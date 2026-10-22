# 8. Gio: Files, Processes, D-Bus, and More

Gio is where "the app does real work" lives. It is also usable without any GTK, which is why PandaManager's engine layer can import it freely.

Docs: https://docs.gtk.org/gio/

## 8.1 Paths and directories

```js
GLib.get_home_dir();             // /home/you
GLib.get_user_data_dir();        // ~/.local/share        (app data, indexes)
GLib.get_user_config_dir();      // ~/.config             (config files)
GLib.get_user_cache_dir();       // ~/.cache              (disposable)
GLib.get_user_state_dir();       // ~/.local/state        (logs, history)
GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES);
GLib.build_filenamev([GLib.get_user_data_dir(), 'pandamanager', 'index.json']);
GLib.mkdir_with_parents(path, 0o755);
```

Always put app files in a **folder named after your app ID or app name** inside these directories.

## 8.2 Gio.File: the file abstraction

`Gio.File` represents a *location* (not the data). It works for local paths, URIs, and remote locations alike.

```js
const f = Gio.File.new_for_path('/home/me/notes.txt');
const child = dir.get_child('notes.txt');
f.get_path();  f.get_basename();  f.get_parent();  f.get_uri();  f.query_exists(null);
```

### Read and write (simple)

```js
// read
const [contents] = f.load_contents(null);                 // sync (small local files only)
const text = new TextDecoder().decode(contents);

// write atomically (writes temp file then renames; safe against crashes)
f.replace_contents(
    new TextEncoder().encode(JSON.stringify(data, null, 2)),
    null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null);
```

For anything slow or large use async versions (Chapter 9): `load_contents_async`, `replace_contents_bytes_async`.

### File info (size, type, times)

```js
const info = f.query_info('standard::name,standard::size,standard::type,time::modified',
                          Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
info.get_size();  info.get_file_type() === Gio.FileType.DIRECTORY;
info.get_modification_date_time();       // GLib.DateTime
```

Ask only for the attributes you need; the list is in the docs ("File Attributes").

### Listing a directory

```js
const e = dir.enumerate_children('standard::name,standard::type',
                                 Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
let info;
while ((info = e.next_file(null)) !== null) {
    const child = e.get_child(info);
    ...
}
e.close(null);
```

Async version:

```js
Gio._promisify(Gio.File.prototype, 'enumerate_children_async', 'enumerate_children_finish');
Gio._promisify(Gio.FileEnumerator.prototype, 'next_files_async', 'next_files_finish');

const en = await dir.enumerate_children_async('standard::name,standard::type',
    Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, GLib.PRIORITY_DEFAULT, null);
while (true) {
    const infos = await en.next_files_async(100, GLib.PRIORITY_DEFAULT, null);
    if (infos.length === 0) break;
    for (const info of infos) { ... }
}
```

### Trash, delete, copy, move, monitor

```js
f.trash(null);                          // move to Trash (PREFER this; recoverable)
f.delete(null);                         // permanent. Avoid for user data
f.copy(dest, Gio.FileCopyFlags.NONE, null, null);
f.move(dest, Gio.FileMoveFlags.NONE, null, null);

const monitor = dir.monitor_directory(Gio.FileMonitorFlags.NONE, null);
monitor.connect('changed', (_m, file, other, eventType) => { ... });
// keep a reference to `monitor` or it is garbage collected and stops
```

### Free disk space

```js
const info = Gio.File.new_for_path('/').query_filesystem_info('filesystem::free,filesystem::size', null);
info.get_attribute_uint64('filesystem::free');
```

### Directory sizes: do NOT walk in JavaScript

Recursing millions of files in JS is slow. Delegate to `du`:

```js
await run(['du', '-sk', '--apparent-size', path]);        // KiB; parse first column
await run(['du', '-d1', '-k', '--exclude=.git', root]);   // children sizes in one pass
```

## 8.3 Running programs: Gio.Subprocess

Your most important tool for a manager-style app.

```js
import Gio from 'gi://Gio';

Gio._promisify(Gio.Subprocess.prototype, 'communicate_utf8_async', 'communicate_utf8_finish');

export async function run(argv, {cwd = null, cancellable = null} = {}) {
    const launcher = new Gio.SubprocessLauncher({
        flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
    });
    if (cwd) launcher.set_cwd(cwd);
    const proc = launcher.spawnv(argv);                         // argv is an ARRAY: no shell, no injection
    const [stdout, stderr] = await proc.communicate_utf8_async(null, cancellable);
    return {ok: proc.get_successful(), status: proc.get_exit_status(), stdout, stderr};
}
```

Notes:

- **Pass an array, never a shell string.** No quoting bugs, no injection. If you truly need shell features use `['sh', '-c', script]` and never interpolate untrusted text.
- Environment: `launcher.setenv('LC_ALL', 'C', true)` to force parseable, English output. Do this for tools whose output you parse.
- Many in parallel: `await Promise.all(repos.map(r => run(['git', '-C', r, 'status', '--porcelain=v2', '--branch'])))`. Limit concurrency (e.g. 8) for big sets, see Section 9.5.
- Stream output line-by-line: use `STDOUT_PIPE` and `Gio.DataInputStream` on `proc.get_stdout_pipe()`, calling `read_line_async`. Needed for long tasks with progress.
- Kill: `proc.force_exit()` or cancel via `Cancellable`.
- A missing program throws at `spawnv` (`G_IO_ERROR_NOT_FOUND`).
- `Gio.Subprocess` does not use a shell, so `~` and `*` are **not** expanded. Expand paths yourself.
- Inside Flatpak, `spawn` runs inside the sandbox. To run host commands you need `flatpak-spawn --host` and permission, which defeats the sandbox (reason PandaManager runs from source).

### Parsing output safely

Prefer machine formats: `--porcelain=v2`, `--json`, `--qf` format strings, `-z` (NUL separated), `--columns=`. Avoid parsing human tables.

## 8.4 Settings: Gio.Settings (GSettings)

Typed, schema-defined preferences stored in dconf.

1. Schema file `data/io.github.you.PandaManager.gschema.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<schemalist>
  <schema id="io.github.you.PandaManager" path="/io/github/you/PandaManager/">
    <key name="scan-roots" type="as">
      <default>[]</default>
      <summary>Folders scanned for repositories</summary>
    </key>
    <key name="window-width" type="i"><default>900</default></key>
    <key name="trash-instead-of-delete" type="b"><default>true</default></key>
  </schema>
</schemalist>
```

2. Compile: `glib-compile-schemas data/`.
3. Use:

```js
const settings = new Gio.Settings({schema_id: 'io.github.you.PandaManager'});
settings.get_strv('scan-roots');
settings.set_strv('scan-roots', ['/home/me/Projects']);
settings.connect('changed::scan-roots', () => rescan());
settings.bind('trash-instead-of-delete', switchRow, 'active', Gio.SettingsBindFlags.DEFAULT);
```

Other getters: `get_boolean`, `get_int`, `get_string`, `get_value` (a Variant). Key types are GVariant type strings (`s`, `i`, `b`, `as`, `a{ss}`).

Schema missing = hard crash. Use `GSETTINGS_SCHEMA_DIR` during development (Chapter 2).

**Use GSettings for small preferences. Use JSON files for caches and indexes.**

## 8.5 D-Bus

D-Bus lets programs expose objects and methods. Most system services (NetworkManager, PackageKit, systemd, UPower, notifications) are D-Bus services. Explore with **D-Spy** or:

```sh
busctl --user list
gdbus introspect --session --dest org.freedesktop.Notifications --object-path /org/freedesktop/Notifications
```

Calling a method:

```js
Gio._promisify(Gio.DBusConnection.prototype, 'call', 'call_finish');

const bus = Gio.bus_get_sync(Gio.BusType.SESSION, null);   // or SYSTEM
const reply = await bus.call(
    'org.freedesktop.Notifications', '/org/freedesktop/Notifications',
    'org.freedesktop.Notifications', 'GetServerInformation',
    null,                              // parameters (GLib.Variant tuple) or null
    null,                              // expected reply type
    Gio.DBusCallFlags.NONE, -1, null);
const [name, vendor, version, spec] = reply.deepUnpack();
```

Proxy helper (generates methods from an XML interface description):

```js
const IFACE = `<node><interface name="org.freedesktop.login1.Manager">
  <method name="Reboot"><arg type="b" direction="in"/></method>
</interface></node>`;
const Proxy = Gio.DBusProxy.makeProxyWrapper(IFACE);
const mgr = new Proxy(Gio.DBus.system, 'org.freedesktop.login1', '/org/freedesktop/login1');
mgr.RebootSync(false);
```

(`makeProxyWrapper` is the classic Shell-extension pattern you already know.)

Your own app already owns a D-Bus name (its application ID); `Gio.Application` uses it for single-instance behaviour.

### Useful services for a manager app

| Service | Use |
|---|---|
| **PackageKit** (`org.freedesktop.PackageKit`) | Install/remove/update packages without running `dnf` as root |
| **polkit** (`pkexec`, `org.freedesktop.PolicyKit1`) | Authentication prompts for privileged operations |
| **systemd** (`org.freedesktop.systemd1`) | Units, timers, services |
| **UDisks2** | Drives, mounts, SMART data |
| **UPower** | Battery |
| **portals** (`org.freedesktop.portal.*`) | Sandbox-safe open file, notification, background |

## 8.6 Notifications

```js
const n = new Gio.Notification();
n.set_title('Scan finished');
n.set_body('3 repositories can be removed');
n.add_button('Review', 'app.show-repos');
app.send_notification('scan-done', n);       // id lets you replace/withdraw it
```

Background-running apps require the Background portal; for a normal foreground app notifications are enough.

## 8.7 Other Gio pieces worth knowing

| Class | Use |
|---|---|
| `Gio.AppInfo` | Installed apps (`Gio.AppInfo.get_all()` lists `.desktop` entries, great for "installed apps" lists); `launch()` |
| `Gio.ContentType` | MIME types and icons for files |
| `Gio.ThemedIcon` / `Gio.FileIcon` | Icon objects for `Gtk.Image.gicon` |
| `Gio.Cancellable` | Cancel async operations |
| `Gio.ListStore` | Writable list model (Chapter 4) |
| `Gio.Menu`, `Gio.SimpleAction` | Menus and actions |
| `Gio.NetworkMonitor` | Online/offline state |
| `Gio.ResourceLoad` / `Gio.Resource` | Compiled resources (Chapter 11) |
| `Gio.UnixInputStream` etc. | Stream plumbing |
| `Soup` (separate lib, `gi://Soup?version=3.0`) | HTTP client/server |

> **Remember:** Gio.File for paths and I/O, `du` for sizes, Subprocess with argv arrays for programs, GSettings for preferences, D-Bus for talking to the system, trash instead of delete.

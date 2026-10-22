# 13. Debugging, Testing, Performance, and Security

## 13.1 Reading errors

GJS prints stack traces like:

```
(gjs:12345): Gjs-CRITICAL **: JS ERROR: TypeError: this._foo is undefined
_onClicked@file:///home/me/app/src/window.js:42:9
```

and GTK/GLib warnings:

```
Gtk-CRITICAL **: gtk_box_append: assertion 'GTK_IS_WIDGET (child)' failed
Gtk-WARNING **: Negative content width -3 ...
Adwaita-WARNING **: ...
```

How to approach:

1. Read the **first** error, later ones are often consequences.
2. `CRITICAL` with "assertion failed" means you passed the wrong type or `null` to a C function. Look at the call named.
3. "Unable to find template / Invalid template" means `GTypeName` or the resource path is wrong.
4. "Unhandled promise rejection" means an `async` function threw and nobody caught it.
5. To turn warnings into crashes with a backtrace: `G_DEBUG=fatal-criticals gjs -m src/main.js` (or `fatal-warnings`).

## 13.2 Tools

| Tool | Use |
|---|---|
| **GTK Inspector** (`GTK_DEBUG=interactive`) | Live widget tree, properties, CSS, layout bounds |
| `console.log`, `logError(e)` | Basic tracing |
| `G_MESSAGES_DEBUG=all` | Verbose GLib/Gio/GTK domain logging |
| `gjs --help` | Debugging flags, e.g. `--debugger`/`-d`, coverage |
| **D-Spy** | Inspect and call D-Bus services |
| `dconf-editor` | See/edit GSettings values |
| **Sysprof** | CPU profiling; find main-loop stalls |
| `strace -f -e trace=file` | See which files an app opens |
| `journalctl --user -f` | Follow logs of GNOME apps launched from the shell |
| `flatpak run --command=sh <id>` | Look inside the sandbox |

Debugging JavaScript: GJS has an experimental command-line debugger (`gjs -d`). In practice most people use logging and the Inspector.

## 13.3 Common bugs and their causes

| Symptom | Likely cause |
|---|---|
| Window never appears | Forgot `win.present()`; error in constructor; no `application:` set |
| UI frozen | Sync call on main thread (Chapter 9) |
| "Namespace Foo not available" | Typelib not installed (`dnf install` the lib or its `-devel`), or wrong version in import |
| Nothing in list | `bind_model` function returns nothing/non-widget; store item type mismatch |
| Template children are `undefined` | Used before `super()`, id mismatch, or missing from `InternalChildren` |
| Rows show raw `&amp;` or empty text | Markup not escaped (Chapter 6.3) |
| Handler runs with wrong `this` | Passed `function` instead of arrow |
| Signal handler stops firing | Object garbage collected (keep a reference), or handler disconnected |
| Setting a property does nothing | Wrong property name; read-only; wrong type |
| Gets "Not a number / NaN" size | `GLib.format_size` given a string, parse numbers first |
| App behaves differently installed vs from source | Missing GResource/schema paths |
| Crash with segfault | Using an object after its widget was destroyed; pass wrong pointer types; report with `coredumpctl` backtrace |

## 13.4 Testing

| Level | Approach |
|---|---|
| Engine logic | Plain gjs scripts or **jasmine-gjs**; feed fixed sample command output into parsers; run against temp directories (`GLib.Dir.make_tmp`/`Gio.File.new_tmp`) |
| Git logic | Create fixture repos in a temp dir with `git init`, then assert on statuses |
| UI | Manual with the Inspector; GTK has no mainstream headless test framework for GJS. Keep UI thin so logic tests suffice |
| Accessibility | Run Orca (screen reader) briefly; check keyboard navigation |
| Visual | Test light/dark, narrow/wide, large text (Settings → Accessibility → Large Text) |

Design for testability: parsers are pure functions `string → object`.

## 13.5 Performance

- Measure first (Sysprof, timestamps).
- Use list **models + ListView** for big lists; avoid creating thousands of widgets.
- Batch updates (`ListStore.splice`) to avoid many redraws.
- Cache expensive scans; refresh in the background.
- Avoid scanning the whole disk: scan configured roots, skip `node_modules`, `.git`, `target`, `build` when walking for repos.
- Debounce search entries (wait 150-250 ms after typing before filtering).
- Prefer system tools (`du`, `find`, `git`) for heavy lifting.

## 13.6 Security and safety

Your app can delete files and run commands as the user, so treat it carefully.

1. **No shell strings.** Use argv arrays (Chapter 8.3). Never build a command by concatenating user or file-derived text.
2. **Validate paths** before destructive operations: absolute, inside allowed roots, not a symlink out of the root, not a system folder.
3. **Don't run as root.** For privileged work:
   - Prefer **PackageKit** over D-Bus for installs/removals (polkit authorises).
   - Otherwise use `pkexec <fixed program> <args>`. For anything frequent, ship a tiny helper script/program with a **polkit policy** file (`/usr/share/polkit-1/actions/*.policy`) so the prompt explains the action; the helper must validate its own arguments.
4. **Don't trust data from disk** (JSON caches, git config, repo hooks). `git` can execute configured hooks/filters in untrusted repos; for read-only scans use `git -c core.fsmonitor=false -c core.hooksPath=/dev/null`-style hardening if scanning repositories you did not create.
5. **Secrets**: never log tokens; store with libsecret (`gi://Secret`) not in JSON.
6. **Network**: validate TLS (default in libsoup 3), do not disable verification.
7. **Flatpak**: request the minimum permissions; use portals.
8. **Downloaded files are data, not code**: never `eval` or `import` content you fetched.
9. Keep dependencies few; pin and review anything you vendor.

## 13.7 Logging

```js
const LOG_DOMAIN = 'PandaManager';
GLib.log_structured(LOG_DOMAIN, GLib.LogLevelFlags.LEVEL_WARNING, {MESSAGE: 'could not read cache'});
console.warn('...');
```

For a persistent action log (cleanup history) append lines to `~/.local/state/pandamanager/actions.log` with timestamps.

> **Remember:** read the first error; GTK_DEBUG=interactive; engine tests in plain gjs; argv arrays; validate paths; PackageKit/polkit instead of root.

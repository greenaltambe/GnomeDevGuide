# 2. Setting Up Your Environment

## 2.1 Install the basics (Fedora)

```sh
# runtime + GJS
sudo dnf install gjs gtk4 libadwaita

# introspection data & headers (devel packages give you .gir files for reference)
sudo dnf install gtk4-devel libadwaita-devel glib2-devel gobject-introspection-devel

# UI & build tools
sudo dnf install blueprint-compiler meson ninja-build desktop-file-utils \
                 appstream libappstream-glib gettext

# packaging
sudo dnf install flatpak flatpak-builder

# inspection tools
sudo dnf install d-spy   # D-Bus explorer (also on Flathub)
```

Flatpak apps worth installing from Flathub:

| App | Why |
|---|---|
| **Workbench** (`re.sonny.Workbench`) | A live playground: write Blueprint + JS/Python/Rust and see the result instantly, with built-in demos. **Best learning tool.** |
| **GNOME Builder** | Full IDE with project templates; useful to *generate a template project* and study its layout |
| **GTK Demo** (`gtk4-demo`, in `gtk4-devel-tools`) | Every GTK widget in action, with source |
| **Libadwaita Demo** (`adwaita-1-demo`) | Every Adw widget in action |
| **Icon Library** | Browse the symbolic icons you can use by name |
| **Sysprof** | Profiler |

> Builder's default Flatpak sandbox cannot see host `dnf`/`rpm`. For apps that manage the host (like PandaManager) develop from source on the host instead (Section 2.4).

## 2.2 Hello window, the smallest possible

Save as `hello.js`, run with `gjs -m hello.js`:

```js
import Adw from 'gi://Adw?version=1';
import System from 'system';

const app = new Adw.Application({application_id: 'org.example.Hello'});

app.connect('activate', () => {
    const win = new Adw.ApplicationWindow({application: app, title: 'Hello'});
    const toolbar = new Adw.ToolbarView();
    toolbar.add_top_bar(new Adw.HeaderBar());
    toolbar.set_content(new Adw.StatusPage({title: 'Hello GNOME'}));
    win.set_content(toolbar);
    win.present();
});

app.run([System.programInvocationName, ...ARGV]);
```

Things to notice:

- `-m` means "treat as an ES module". Required for `import ... from 'gi://...'`. You cannot combine `-m` with `-c`.
- `?version=4.0` pins the library version. Without it GJS may warn or pick the wrong one. Always specify.
- `ARGV` is a global with command line arguments.
- `app.run()` starts the main loop and blocks until the app quits.

## 2.3 Editor setup (Zed, VS Code, anything)

There is no official GJS language server, but you can get autocomplete with **TypeScript type definitions** generated from GIR:

```sh
npm init -y
npm i -D @girs/gjs @girs/gtk-4.0 @girs/adw-1 @girs/gio-2.0 @girs/glib-2.0 @girs/gobject-2.0
```

Add `jsconfig.json`:

```json
{
  "compilerOptions": {
    "module": "ES2022",
    "target": "ES2022",
    "moduleResolution": "bundler",
    "checkJs": false,
    "types": ["@girs/gjs"]
  },
  "include": ["src/**/*.js"]
}
```

Some `gi://` import specifiers may need typing hints depending on the editor; autocomplete for method names is the main win. If it is more trouble than it is worth, rely on Section 16 (reading the docs) instead.

Also useful:

- **ESLint** with GJS-aware globals (`ARGV`, `print`, `log`, `console`, `imports`).
- **Prettier** or a consistent style. The GNOME JS convention is 4 spaces, single quotes, semicolons, `snake_case` for GObject APIs and `camelCase` for your own methods.
- **Blueprint** has an LSP (`blueprint-compiler lsp`) and editor extensions for VS Code. Zed may need a community extension; at worst, treat `.blp` as plain text.

## 2.4 Running from source (the development loop)

For a pure-JS app you can run directly:

```sh
gjs -m src/main.js
```

This is fast and perfect for host-integrating apps. Two things you lose compared with an installed app, and their fixes:

1. **GResource files** (compiled UI/icons) are not found. Fix: compile them in a dev script (Section 11.3), *or* avoid GResource early on and build widgets in code or load `.ui` files from the filesystem.
2. **GSettings schemas** are not found. Fix: compile your schema into a dev folder and point at it:

```sh
glib-compile-schemas data/
GSETTINGS_SCHEMA_DIR=data gjs -m src/main.js
```

Or store settings in JSON in the early stage (Section 10.4).

A tiny `run.sh`:

```sh
#!/bin/sh
cd "$(dirname "$0")"
glib-compile-schemas data/ 2>/dev/null
GSETTINGS_SCHEMA_DIR=data exec gjs -m src/main.js "$@"
```

## 2.5 Handy environment variables while developing

| Variable | Effect |
|---|---|
| `GTK_DEBUG=interactive` | Opens the **GTK Inspector** (live widget tree, CSS editor, properties). Also `Ctrl+Shift+D` in many setups |
| `G_MESSAGES_DEBUG=all` | Show GLib debug messages |
| `GTK_THEME=Adwaita:dark` | Force dark theme to test |
| `ADW_DEBUG_COLOR_SCHEME=prefer-dark` | Force libadwaita colour scheme |
| `GDK_BACKEND=x11` or `wayland` | Choose display backend |
| `GJS_DEBUG_OUTPUT=stderr` | Make sure `log()` output is visible |
| `GSETTINGS_BACKEND=memory` | Ignore real dconf, use throwaway settings |
| `NO_AT_BRIDGE=1` | Silence accessibility bus warnings |

## 2.6 Recommended project layout (JS)

```
myapp/
├─ src/
│  ├─ main.js            # entry: create Application
│  ├─ application.js     # Application subclass, actions, app-level logic
│  ├─ window.js          # main window class
│  ├─ engine/            # NO Gtk imports: logic, data, processes
│  ├─ ui/                # widgets, pages, rows
│  └─ resources/         # .blp / .ui / .css / icons
├─ data/                 # .desktop, metainfo, gschema, icons
├─ po/                   # translations
├─ build-aux/            # flatpak manifest, scripts
├─ meson.build           # build definition (when you package)
└─ README.md
```

Start with only `src/` and grow into the rest. Do not set up meson on day one.

> **Remember:** install gjs/gtk4/libadwaita/blueprint; learn with Workbench; run with `gjs -m`; use `GTK_DEBUG=interactive` constantly.

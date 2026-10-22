# 17. Cheat Sheets, Pitfalls, and Glossary

## 17.1 Starter templates

### Minimal class-based app (JS, no templates)

```js
// main.js
import Adw from 'gi://Adw?version=1';
import Gtk from 'gi://Gtk?version=4.0';
import GObject from 'gi://GObject';
import System from 'system';

const Window = GObject.registerClass(class Window extends Adw.ApplicationWindow {
    constructor(app) {
        super({application: app, title: 'App', default_width: 800, default_height: 600});
        const toolbar = new Adw.ToolbarView();
        toolbar.add_top_bar(new Adw.HeaderBar());
        toolbar.content = new Gtk.Label({label: 'Hello'});
        this.content = toolbar;
    }
});

const App = GObject.registerClass(class App extends Adw.Application {
    constructor() { super({application_id: 'org.example.App'}); }
    vfunc_activate() { (this.active_window ?? new Window(this)).present(); }
});

new App().runAsync([System.programInvocationName, ...ARGV]);
```

### Async scan with progress and cancellation

```js
async scan() {
    this._cancel?.cancel();
    const cancel = this._cancel = new Gio.Cancellable();
    this._stack.visible_child_name = 'loading';
    try {
        const items = await engine.list({cancellable: cancel});
        if (cancel.is_cancelled()) return;
        this._store.splice(0, this._store.get_n_items(), items.map(i => new Item(i)));
        this._stack.visible_child_name = items.length ? 'content' : 'empty';
    } catch (e) {
        if (cancel.is_cancelled()) return;
        this._error.description = e.message;
        this._stack.visible_child_name = 'error';
    }
}
```

## 17.2 "Which widget do I use?"

| I want... | Use |
|---|---|
| App window | `Adw.ApplicationWindow` + `Adw.ToolbarView` + `Adw.HeaderBar` |
| Sidebar navigation | `Adw.NavigationSplitView` |
| Top-level tabs | `Adw.ViewStack` + `Adw.ViewSwitcher` |
| Drill-down screens | `Adw.NavigationView` |
| Settings list | `Adw.PreferencesPage/Group` + `Adw.SwitchRow` etc. |
| List of rows with title/subtitle | `Adw.ActionRow` in a `Gtk.ListBox.boxed-list` |
| Huge list | `Gtk.ListView` + `Gio.ListStore` |
| Table | `Gtk.ColumnView` |
| Empty/error page | `Adw.StatusPage` |
| Notify of success, with Undo | `Adw.Toast` |
| Ask confirmation | `Adw.AlertDialog` |
| Own dialog | `Adw.Dialog` |
| Pick a file/folder | `Gtk.FileDialog` |
| Search | `Gtk.SearchBar` + `Gtk.SearchEntry` |
| Choose from options | `Adw.ComboRow` / `Gtk.DropDown` |
| Progress | `Gtk.ProgressBar` / `Adw.Spinner` |
| Menu | `Gio.Menu` + `Gtk.MenuButton` |
| Responsive layout | `Adw.Breakpoint` + `Adw.Clamp` |

## 17.3 Top pitfalls

1. Forgetting `?version=` on imports.
2. Blocking the main loop with sync calls.
3. Not catching errors inside async signal handlers.
4. `function () {}` instead of arrow in callbacks, wrong `this`.
5. Pango markup in rows with untrusted text (`&`, `<`).
6. Template `GTypeName` mismatch / forgetting `super(params)`.
7. Rows in a ListView treated as permanent instead of recycled.
8. Shell strings for subprocesses instead of argv arrays.
9. Deleting instead of trashing; no preview.
10. Using GTK3 tutorials (`Gtk.main`, `show_all`, `pack_start`).
11. Hard-coded colours; dark mode breaks.
12. Using deprecated widgets that exist in your version but not in the target runtime.
13. Hold-no-reference: a `Gio.FileMonitor` or timer garbage-collected.
14. GSettings schema not found in dev.
15. Walking huge directory trees in JS rather than `du`.

## 17.4 Glossary

| Term | Meaning |
|---|---|
| **Adw / libadwaita** | GNOME's design-language library built on GTK4 |
| **Action** | Named operation that menus/buttons/shortcuts can trigger |
| **App ID** | Reverse-DNS identity of your app |
| **AppStream / metainfo** | XML software description for stores |
| **Blueprint** | Friendly markup that compiles to GTK `.ui` XML |
| **Cancellable** | Object used to cancel async operations |
| **Composite template** | UI description bound to a widget class |
| **D-Bus** | Message bus used to talk between programs |
| **dconf** | The database backing GSettings |
| **GIR / typelib** | API description files enabling language bindings |
| **GJS** | GNOME's JavaScript runtime (SpiderMonkey + bindings) |
| **GLib** | Foundation library: main loop, utilities |
| **GObject** | Object system: classes, properties, signals |
| **Gio** | I/O library: files, processes, D-Bus, settings |
| **GResource** | Compiled bundle of app assets |
| **GSettings** | Typed settings API |
| **GTK** | The widget toolkit |
| **GType** | Runtime type identifier of a GObject class |
| **GVariant** | Typed serialisable value |
| **HIG** | Human Interface Guidelines |
| **Main loop** | Event loop dispatching input, timers, async results |
| **Meson** | Build system used by GNOME |
| **Model (list model)** | Data provider for list widgets |
| **Portal** | Sandbox-safe system service API |
| **polkit** | Authorisation framework for privileged actions |
| **Runtime / SDK (Flatpak)** | Shared base libraries / build tools |
| **Signal** | Named event on an object |
| **Property** | Named, observable state on an object |
| **Typelib** | Binary form of a GIR |
| **vfunc** | Virtual function you can override in a subclass |
| **XDG dirs** | Standard folders (`~/.config`, `~/.local/share`, `~/.cache`) |

## 17.5 Command cheat sheet

```sh
gjs -m main.js                                   # run a JS module
GTK_DEBUG=interactive gjs -m main.js             # with inspector
blueprint-compiler compile in.blp > out.ui       # compile Blueprint
glib-compile-schemas data/                       # compile GSettings schemas
glib-compile-resources app.gresource.xml         # build resources
desktop-file-validate app.desktop                # lint .desktop
appstreamcli validate app.metainfo.xml           # lint metainfo
meson setup build && meson compile -C build      # build
flatpak-builder --user --install --force-clean b manifest.json
flatpak run <app-id>
gdbus introspect --session --dest <name> --object-path <path>
dconf watch /                                    # watch settings changes
```

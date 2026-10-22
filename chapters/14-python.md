# 14. Python (PyGObject) Companion

Everything conceptual in Chapters 1 to 13 (GObject, GTK, Adw, Gio, actions, templates, packaging) applies identically. This chapter gives the **Python spelling** and the places Python differs.

Docs: https://pygobject.gnome.org/ (tutorial and API) and https://pygobject.gnome.org/guide/

## 14.1 Setup

```sh
sudo dnf install python3-gobject gtk4 libadwaita python3-gobject-devel
python3 -c "import gi; print(gi.__version__)"
```

Editor help: `pip install pygobject-stubs --no-binary pygobject-stubs` (type stubs for autocompletion), and use a venv created with `--system-site-packages` so it can see the system `gi` module.

## 14.2 Hello window

```py
import sys
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, GLib, Gio, GObject

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.example.Hello")

    def do_activate(self):
        win = Adw.ApplicationWindow(application=self, title="Hello")
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(Adw.StatusPage(title="Hello GNOME"))
        win.set_content(toolbar)
        win.present()

sys.exit(App().run(sys.argv))
```

Differences from JS:

| Topic | JavaScript | Python |
|---|---|---|
| Import | `import Gtk from 'gi://Gtk?version=4.0'` | `gi.require_version('Gtk','4.0'); from gi.repository import Gtk` |
| Virtual functions | `vfunc_activate()` | `do_activate(self)` |
| Constructor | `new Gtk.Label({label:'x'})` | `Gtk.Label(label='x')` |
| Property names | `icon_name` | `icon_name` (hyphens become underscores) |
| Signals | `w.connect('clicked', cb)` | `w.connect('clicked', self.on_clicked)` |
| Out params | returned as array | returned as tuple |
| Errors | JS exceptions | `GLib.Error` exceptions |
| Enum | `Gtk.Orientation.VERTICAL` | `Gtk.Orientation.VERTICAL` |
| Class registration | `GObject.registerClass` | automatic by inheriting a GObject class |

## 14.3 Defining GObject classes, properties, signals

```py
class Package(GObject.Object):
    __gtype_name__ = "PandaPackage"

    name = GObject.Property(type=str, default="")
    size = GObject.Property(type=float, default=0.0)

    @GObject.Signal(arg_types=(float,))
    def progress(self, fraction):
        pass                     # body runs as the default handler

    def __init__(self, name, size):
        super().__init__()
        self.name = name
        self.size = size

p = Package("git", 1.0)
p.connect("notify::size", lambda obj, pspec: print("size changed"))
p.emit("progress", 0.5)
```

Python object attributes that are not `GObject.Property` are plain Python state and notify nothing.

## 14.4 Templates

```py
@Gtk.Template(resource_path="/io/github/you/PandaManager/window.ui")
class PandaWindow(Adw.ApplicationWindow):
    __gtype_name__ = "PandaWindow"          # must match the template name

    toast_overlay = Gtk.Template.Child()    # attribute name == widget id in the .blp/.ui
    rescan_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @Gtk.Template.Callback()
    def on_rescan_clicked(self, button):    # Blueprint: clicked => $on_rescan_clicked();
        self.toast_overlay.add_toast(Adw.Toast(title="Rescanning…"))
```

Template from file during development: `@Gtk.Template(filename="window.ui")`.

## 14.5 Lists

```py
store = Gio.ListStore(item_type=Package)
store.append(Package("git", 1.0))

factory = Gtk.SignalListItemFactory()
factory.connect("setup", lambda f, li: li.set_child(Gtk.Label(xalign=0)))
factory.connect("bind", lambda f, li: li.get_child().set_label(li.get_item().name))
view = Gtk.ListView(model=Gtk.SingleSelection(model=store), factory=factory)
```

## 14.6 Async in Python: three options

**A. Gio async with callbacks** (works like JS before promisify):

```py
def on_done(proc, res):
    ok, stdout, stderr = proc.communicate_utf8_finish(res)
proc = Gio.Subprocess.new(["flatpak", "list"], Gio.SubprocessFlags.STDOUT_PIPE)
proc.communicate_utf8_async(None, None, on_done)
```

**B. asyncio integrated with the GLib main loop.** Recent PyGObject (3.50 and later) ships `gi.events`:

```py
import asyncio
from gi.events import GLibEventLoopPolicy
asyncio.set_event_loop_policy(GLibEventLoopPolicy())

async def rescan():
    proc = await asyncio.create_subprocess_exec(
        "git", "status", "--porcelain=v2", stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
```

Then `asyncio.create_task(rescan())` from signal handlers. Check the current PyGObject docs for the exact recommended integration; older apps used `gbulb` or `asyncio` in a thread.

**C. Threads + `GLib.idle_add`.** Python threads are fine for blocking work, but **never touch widgets from a thread**:

```py
import threading
def work():
    result = heavy()
    GLib.idle_add(update_ui, result)      # hop back to the main loop
threading.Thread(target=work, daemon=True).start()
```

Python's GIL means threads help I/O-bound, not CPU-bound, work (use `subprocess` or `multiprocessing` for CPU).

## 14.7 Project structure and packaging

Builder's "GNOME Application (Python)" template produces:

```
src/ main.py window.py *.blp  <app-id>.in  meson.build
```

with a launcher script that sets up `pkgdatadir`/`localedir` and loads the GResource. Python package dependencies in Flatpak are declared with generated `python3-<pkg>.json` modules (`flatpak-pip-generator`). Keep third-party deps minimal; the GNOME runtime already includes `gi`.

## 14.8 Python-specific tips

- Use `pathlib` for paths and `subprocess.run` for quick synchronous scripts (not in the UI thread!).
- `dataclasses` for plain data, GObject classes only for list items and observable models.
- Type-check engine code with `mypy`; format with `ruff`/`black`.
- Do not name an attribute the same as a GObject property unless you intend to override it.
- Good example projects to read: Apostrophe, Lollypop, Gaphor (check each repo to confirm language and GTK version).
- The same engine/UI split applies: put logic in a package with no `gi` imports.

> **Remember:** same concepts; `do_` instead of `vfunc_`; `GObject.Property`; `@Gtk.Template`; threads are allowed but hop to the main loop with `GLib.idle_add`.

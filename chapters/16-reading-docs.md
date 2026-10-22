# 16. How to Read the Documentation

Most "I'm stuck" moments in GNOME development are really "I can't find or read the docs". This chapter fixes that.

## 16.1 Where each question is answered

| Question | Go to |
|---|---|
| "What widgets exist and how do they look?" | Libadwaita widget gallery; run `adwaita-1-demo` and `gtk4-demo` |
| "What does this class/method do?" | API reference: GTK https://docs.gtk.org/gtk4/ , Adw https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/ , GLib/Gio/GObject https://docs.gtk.org/ |
| "How do I do this in GJS?" | https://gjs.guide (guides), GJS API docs https://gjs-docs.gnome.org/ , GJS repo `doc/` |
| "What's the right design?" | GNOME HIG https://developer.gnome.org/hig/ |
| "How do I build/package?" | https://developer.gnome.org/documentation/ , Flatpak https://docs.flatpak.org , Meson https://mesonbuild.com |
| "Show me working code" | Workbench demos, Builder templates, and real apps' source on https://gitlab.gnome.org/GNOME |
| "I'm stuck" | https://discourse.gnome.org (tag `gjs`/`development`), Matrix `#gjs:gnome.org` and `#gtk:gnome.org` |

## 16.2 Anatomy of an API page (C docs → what to look for)

Open https://docs.gtk.org/gtk4/class.Button.html . The sections:

1. **Description**: what it is for. Read first.
2. **Hierarchy / Ancestors / Implements**: inherited methods and properties live on those pages too.
3. **Constructors**: `new`, `new_with_label` (JS: `new Gtk.Button(...)` or `Gtk.Button.new_with_label()`).
4. **Instance methods**: `set_label`, `get_label` (JS: same names).
5. **Properties**: names, types, read/write flags. Hyphen names; JS uses underscores for access.
6. **Signals**: names and callback parameters.
7. **Class methods / virtual methods**: `vfunc_*` for subclassers.
8. **CSS nodes / Accessibility / Style classes**: how to style it.
9. **"Since" and "Deprecated"** on each member: check against your version.

## 16.3 The C → GJS translation table

| In the C docs | In GJS |
|---|---|
| `GtkButton`, `AdwActionRow` | `Gtk.Button`, `Adw.ActionRow` |
| `gtk_button_set_label(button, "x")` | `button.set_label('x')` or `button.label = 'x'` |
| `gtk_button_new_with_label("x")` | `Gtk.Button.new_with_label('x')` |
| `GTK_ORIENTATION_VERTICAL` | `Gtk.Orientation.VERTICAL` |
| `G_IO_ERROR_NOT_FOUND` | `Gio.IOErrorEnum.NOT_FOUND` |
| `GFile *`, `GListModel *` | `Gio.File`, `Gio.ListModel` |
| `g_file_load_contents(file, cancellable, &contents, &length, &etag, &error)` | `const [ok, contents, etag] = file.load_contents(null)` (error → exception) |
| `g_object_bind_property(a, "x", b, "y", flags)` | `a.bind_property('x', b, 'y', flags)` |
| `g_signal_connect(btn, "clicked", cb, data)` | `btn.connect('clicked', () => {...})` (no user data) |
| `g_signal_connect_swapped` | use arrow closures |
| `gtk_widget_class_bind_template_child` | `InternalChildren` / `Children` |
| `gtk_widget_class_set_template_from_resource` | `Template:` |
| `GAsyncReadyCallback`, `foo_async/foo_finish` | callback, or `Gio._promisify` then `await` |
| `GError **error` | thrown exception |
| `NULL` | `null` |
| `GList *` of strings | array |
| `gchar **` | array of strings |
| `GVariant *` | `GLib.Variant` |
| "transfer full/none", "nullable", "out", "inout" annotations | memory handled for you; `nullable` = may pass/return `null`; `out` = comes back in the result array |
| Class struct, `*_class_init` | ignore (use `registerClass`) |
| `G_DEFINE_TYPE` | ignore |

Property name check: `AdwActionRow:title-lines` → `row.title_lines`.
Signal name check: `GtkEditable::changed` → `entry.connect('changed', ...)`.
Namespaced static function: `gtk_show_uri` → `Gtk.show_uri(...)`, `g_get_home_dir` → `GLib.get_home_dir()`.

## 16.4 The GJS API docs and GIR

- https://gjs-docs.gnome.org/ is auto-generated from GIR for **JS names** and shows the namespaces (`Gtk-4.0`, `Adw-1`). Use its search box; pick the right version of the library.
- The raw truth is the GIR XML on your machine: `/usr/share/gir-1.0/Adw-1.gir`. `grep` it:

```sh
grep -n 'name="NavigationSplitView"' /usr/share/gir-1.0/Adw-1.gir | head
```

- Fast introspection from a script:

```js
import Adw from 'gi://Adw?version=1';
console.log(Object.getOwnPropertyNames(Adw.ActionRow.prototype));     // methods
console.log(Adw.ActionRow.$gtype.name);                                // GType name
```

- To list properties/signals of a class at runtime:

```js
import GObject from 'gi://GObject';
console.log(GObject.Object.list_properties.call(Adw.ActionRow).map(p => p.name));
console.log(GObject.signal_list_ids(Adw.ActionRow.$gtype).map(id => GObject.signal_name(id)));
```

## 16.5 A method for solving "how do I...?"

1. **Say it in GNOME words.** "A list that updates itself" → *list model + ListView*. "Popup menu" → *Popover / MenuButton / menu model*. "Ask yes/no" → *AlertDialog*.
2. **Find the widget** in the libadwaita gallery or GTK demo.
3. **Open the API page**, check Since/Deprecated, read Description.
4. **Find a working snippet**: Workbench has a Library of examples; also search GitLab: `https://gitlab.gnome.org/search?search=<ClassName>&group_id=8` (GNOME group) or GitHub code search `language:JavaScript Adw.NavigationSplitView`.
5. **Translate** to JS with the table above.
6. **Try in Workbench** or a scratch script; log results.
7. **Inspect** in GTK Inspector if the appearance is wrong.
8. If still stuck, ask on Discourse/Matrix with a minimal example.

## 16.6 Learning from real apps

Read source for patterns (clone and grep). Confirm the current language/GTK version in each repo before copying.

| Language | Apps | Learn |
|---|---|---|
| JS | Workbench, Foliate, GNOME Characters, Sound Recorder, Decibels | templates, async, navigation |
| Python | Apostrophe, Lollypop, Gaphor | Python templates, threads |
| Rust | Loupe, Fractal, Snapshot, Authenticator | subclassing, async, structure |
| C | Nautilus, GNOME Text Editor, Files | the canonical reference; the API docs mirror the C |

Also: https://gitlab.gnome.org/World/ for the broader app ecosystem and https://apps.gnome.org for the circle of apps.

## 16.7 Reading changelogs and migration guides

- libadwaita **NEWS** and the "Migrating" pages in its docs show what is new/deprecated (e.g. Message→Alert dialog migration).
- GTK has https://docs.gtk.org/gtk4/migrating-3to4.html (useful when old tutorials are GTK3).
- For Fedora's versions: `rpm -q gtk4 libadwaita gjs`.

> **Remember:** C docs are the source of truth, GJS is a mechanical translation; check Since/Deprecated; try things in Workbench; read real apps.

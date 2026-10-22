# 7. Blueprint and Composite Templates

Building UI in code (Chapters 5 and 6) works but gets noisy. GTK lets you describe the UI **declaratively** and bind it to a class. The file format is XML (`.ui`); **Blueprint** (`.blp`) is a friendlier syntax that compiles to that XML.

Docs: https://gnome.pages.gitlab.gnome.org/blueprint-compiler/

## 7.1 Blueprint in 10 minutes

```blp
using Gtk 4.0;
using Adw 1;

template $PandaWindow: Adw.ApplicationWindow {
  title: "PandaManager";
  default-width: 900;
  default-height: 640;

  content: Adw.ToastOverlay toast_overlay {
    child: Adw.ToolbarView {
      [top]
      Adw.HeaderBar {
        [end]
        Gtk.MenuButton {
          icon-name: "open-menu-symbolic";
          menu-model: primary_menu;
        }
      }

      content: Gtk.Label greeting {
        label: _("Hello");
        styles ["title-1"]
      };
    };
  };
}

menu primary_menu {
  section {
    item {
      label: _("_About PandaManager");
      action: "app.about";
    }
  }
}
```

Reading it:

| Syntax | Meaning |
|---|---|
| `using Gtk 4.0;` | Declare libraries (required) |
| `template $PandaWindow: Adw.ApplicationWindow` | "This is the UI of my class `PandaWindow`, a subclass of ApplicationWindow." `$Name` refers to a GType name |
| `Gtk.Label greeting { ... }` | Create a Label with the **id** `greeting` |
| `property-name: value;` | Property assignment (use hyphens) |
| `content: Widget {...};` | Assign a widget to a *property* (note the trailing `;`) |
| `[top] Widget {}` | Add as a *child* in a named slot (`top`, `end`, `start`, ...) |
| `styles ["a", "b"]` | CSS classes |
| `_("text")` | Translatable string |
| `clicked => $_on_clicked();` | Connect signal to a method on the template class |
| `bind-property` (see below) | Property binding |
| `menu name { ... }` | A menu model |

Binding examples:

```blp
Gtk.Revealer {
  reveal-child: bind search_button.active;           // one-way
}
Gtk.Entry {
  text: bind template.query bidirectional;           // two-way with a property of your class
}
```

(Binding to properties of your own class works with `template.property-name`; the property must be declared in `Properties`. Check the Blueprint docs for the cast syntax needed when types differ.)

Signals:

```blp
Gtk.Button {
  label: _("Rescan");
  clicked => $_on_rescan_clicked();
  styles ["suggested-action"]
}
```

Compile (manually) with:

```sh
blueprint-compiler compile src/ui/window.blp > src/ui/window.ui
blueprint-compiler batch-compile out/ in/ in/*.blp     # many files
```

In a Meson project this is automated (Section 12.2).

Reading errors: Blueprint's messages are good. If an unknown property is reported, check the property name in the widget's docs (properties use hyphens, e.g. `icon-name`).

## 7.2 Binding the template to a JS class

```js
// src/window.js
import Adw from 'gi://Adw?version=1';
import GObject from 'gi://GObject';

export const PandaWindow = GObject.registerClass({
    GTypeName: 'PandaWindow',                     // must equal the $Name in .blp
    Template: 'resource:///io/github/you/PandaManager/window.ui',
    InternalChildren: ['toast_overlay', 'greeting'],
}, class PandaWindow extends Adw.ApplicationWindow {
    constructor(params) {
        super(params);
        this._greeting.label = 'Loaded!';         // InternalChildren get a leading underscore
    }

    _on_rescan_clicked() {
        this._toast_overlay.add_toast(new Adw.Toast({title: 'Rescanning…'}));
    }
});
```

- `Template:` can be a `resource:///` URI (production) or a `file://` URI/bytes (development).
- `InternalChildren: ['x']` exposes the widget with id `x` as `this._x`. `Children: ['x']` exposes it as `this.x` (public).
- Handler names in `=> $_on_...` become methods on the class.
- The id names in Blueprint are `snake_case` or `kebab`; ids with hyphens become underscores in JS (check by logging). Stick to `snake_case` ids.
- `GTypeName` mismatch is the #1 template error: "Invalid template class".

### Loading a template without GResource (development)

```js
import GLib from 'gi://GLib';
const uri = GLib.uri_resolve_relative(import.meta.url, './window.ui', GLib.UriFlags.NONE);
// Template: uri,
```

Compile the `.blp` to `.ui` in your `run.sh` before launching. Good enough until you set up Meson and GResource.

## 7.3 When to use templates vs code

| Use a template for | Use code for |
|---|---|
| Static structure (windows, pages, rows with fixed layout) | Dynamic lists of rows built from data |
| Menus, breakpoints, bindings | One-off helpers |
| Anything a designer would want to tweak | Logic and branching |

A good split: the template declares **what it looks like**, the class does **what it does**. Make each page its own template class (`ReposPage`, `AppsPage`), each in its own `.blp` + `.js`.

## 7.4 Reusable row/page components

```blp
using Gtk 4.0;
using Adw 1;

template $RepoRow: Adw.ExpanderRow {
  title: bind template.repo-name;
  subtitle: bind template.status-text;
}
```

```js
export const RepoRow = GObject.registerClass({
    GTypeName: 'RepoRow',
    Template: '...repo-row.ui',
    Properties: {
        'repo-name': GObject.ParamSpec.string('repo-name', '', '', GObject.ParamFlags.READWRITE, ''),
        'status-text': GObject.ParamSpec.string('status-text', '', '', GObject.ParamFlags.READWRITE, ''),
    },
}, class RepoRow extends Adw.ExpanderRow { });
```

Now `new RepoRow({repo_name: 'x'})` updates the UI by itself through bindings.

## 7.5 Menus

Menus are separate from widgets. Declare them in Blueprint (above) or in code (`Gio.Menu`) and trigger **actions**. Example in code:

```js
const menu = new Gio.Menu();
const section = new Gio.Menu();
section.append('Preferences', 'app.preferences');
section.append('Keyboard Shortcuts', 'win.show-help-overlay');
section.append('About PandaManager', 'app.about');
menu.append_section(null, section);
menuButton.menu_model = menu;
```

## 7.6 Plain XML `.ui` (what Blueprint becomes)

You will see this in older apps. Know how to read it:

```xml
<interface>
  <template class="PandaWindow" parent="AdwApplicationWindow">
    <property name="title">PandaManager</property>
    <child>
      <object class="GtkButton" id="rescan">
        <property name="label">Rescan</property>
        <signal name="clicked" handler="_on_rescan_clicked" swapped="no"/>
      </object>
    </child>
  </template>
</interface>
```

> **Remember:** Blueprint compiles to XML; `GTypeName` must match `template $Name`; `InternalChildren` gives `this._id`; one template class per page.

# 11. Actions, Shortcuts, Resources, Preferences, and Translations

## 11.1 Actions in depth

Actions let menus, buttons, shortcuts and notifications trigger the same code.

```js
// stateless
const rescan = new Gio.SimpleAction({name: 'rescan'});
rescan.connect('activate', () => this._rescan());
this.add_action(rescan);                              // on a window => 'win.rescan'

// with a parameter (string)
const open = new Gio.SimpleAction({name: 'open-repo', parameter_type: new GLib.VariantType('s')});
open.connect('activate', (_a, param) => this._open(param.get_string()[0]));

// stateful boolean (a toggle)
const showHidden = new Gio.SimpleAction({
    name: 'show-hidden', state: GLib.Variant.new_boolean(false),
});
showHidden.connect('activate', (a) => {
    const next = !a.state.get_boolean();
    a.change_state(GLib.Variant.new_boolean(next));
});
showHidden.connect('notify::state', ...);
```

Convenience: `Gio.PropertyAction` binds an action to an object property:

```js
this.add_action(new Gio.PropertyAction({name: 'sort-desc', object: this, property_name: 'sort-desc'}));
```

Triggering from UI: `button.action_name = 'win.rescan'`, or `button.action_target = new GLib.Variant('s', path)` for parameterised actions. Menu items use `action: "win.rescan"`.

Enable/disable: `action.enabled = false` (buttons using it grey out automatically).

### Namespaces

| Prefix | Added with | Scope |
|---|---|---|
| `app.` | `application.add_action()` | whole application |
| `win.` | `window.add_action()` | one window |
| custom | `widget.insert_action_group('repo', group)` | that widget and children |

## 11.2 Keyboard shortcuts

```js
app.set_accels_for_action('app.quit', ['<Control>q']);
app.set_accels_for_action('win.rescan', ['<Control>r', 'F5']);
app.set_accels_for_action('win.search', ['<Control>f']);
app.set_accels_for_action('win.show-help-overlay', ['<Control>question']);
```

Accelerator syntax: `<Control>`, `<Shift>`, `<Alt>`, `<Super>`; key names from `Gdk` (`Escape`, `F5`, `Return`, `comma` for Ctrl+,).

Conventions: `Ctrl+Q` quit, `Ctrl+W` close, `Ctrl+,` preferences, `Ctrl+F` search, `Ctrl+?` shortcuts, `F5`/`Ctrl+R` refresh, `Ctrl+N` new.

Document them in an `Adw.ShortcutsDialog` (new) or `Gtk.ShortcutsWindow` (older).

## 11.3 GResource: bundling UI and assets

A **GResource** is a compiled bundle of files (UI, CSS, icons) inside the app. Loaded as `resource:///path`.

1. `data/io.github.you.PandaManager.gresource.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/io/github/you/PandaManager">
    <file preprocess="xml-stripblanks">ui/window.ui</file>
    <file>style.css</file>
  </gresource>
  <gresource prefix="/io/github/you/PandaManager/icons/scalable/actions">
    <file>my-symbolic.svg</file>
  </gresource>
</gresources>
```

2. Compile: `glib-compile-resources --sourcedir=build_ui data/app.gresource.xml --target=app.gresource`
3. Load before creating windows:

```js
const res = Gio.Resource.load('/path/to/app.gresource');
res._register();
```

Meson does steps 2 and 3 for installed apps (Chapter 12). During early development you may load `.ui` from files directly (Chapter 7.2).

Load CSS from a resource: `provider.load_from_resource('/io/github/you/PandaManager/style.css')`. Add icon search path for resource icons: `Gtk.IconTheme.get_for_display(display).add_resource_path('/io/github/you/PandaManager/icons')`.

## 11.4 Preferences UI

Use `Adw.PreferencesDialog` (or `Adw.PreferencesWindow` on older libadwaita):

```blp
template $PreferencesDialog: Adw.PreferencesDialog {
  Adw.PreferencesPage {
    title: _("General");
    icon-name: "preferences-system-symbolic";

    Adw.PreferencesGroup {
      title: _("Safety");
      Adw.SwitchRow trash_row {
        title: _("Move to Trash instead of deleting");
      }
      Adw.SpinRow stale_days_row {
        title: _("Mark repositories stale after (days)");
        adjustment: Gtk.Adjustment { lower: 1; upper: 3650; step-increment: 1; value: 90; };
      }
    }
  }
}
```

Bind rows to GSettings in the constructor:

```js
settings.bind('trash-instead-of-delete', this._trash_row, 'active', Gio.SettingsBindFlags.DEFAULT);
settings.bind('stale-days', this._stale_days_row, 'value', Gio.SettingsBindFlags.DEFAULT);
```

Open with `new PreferencesDialog().present(window)`.

For a list of folders (scan roots): an `Adw.PreferencesGroup` whose rows you rebuild on `changed::scan-roots`, each with a remove button, plus an "Add Folder…" `Adw.ButtonRow` that opens `Gtk.FileDialog`.

## 11.5 Internationalisation (i18n)

Even if you only write English, wrap strings early; retrofitting is painful.

```js
import Gettext from 'gettext';
Gettext.bindtextdomain('pandamanager', localeDir);
Gettext.textdomain('pandamanager');
const _ = Gettext.gettext;
const ngettext = Gettext.ngettext;

label.label = _('Rescan');
subtitle = ngettext('%d repository', '%d repositories', n).format(n);
```

Blueprint strings: `_("text")`. Workflow with Meson: `xgettext` collects strings into a `.pot`, translators supply `.po` files. For a personal tool you can skip the infrastructure but keep the `_()` habit.

Locale-aware formatting: `GLib.format_size(bytes)` (SI) or `GLib.format_size_full(bytes, GLib.FormatSizeFlags.IEC_UNITS)`; dates: `GLib.DateTime.new_now_local().format('%x')`, relative times implemented by you.

## 11.6 The primary menu and About

Standard menu:

```
Preferences      app.preferences
Keyboard Shortcuts   win.show-help-overlay
About PandaManager   app.about
```

and an `app.about` action presenting `Adw.AboutDialog` (Chapter 6.9).

## 11.7 Application lifecycle and CLI arguments

```js
vfunc_startup()  // once per process, before first activate. Create actions, load CSS
vfunc_activate() // user launched the app (again): show or present the window
vfunc_open(files, hint)   // when launched with files; requires flags: Gio.ApplicationFlags.HANDLES_OPEN
vfunc_command_line(cl)    // custom args; flags: HANDLES_COMMAND_LINE
vfunc_shutdown()          // clean up (save state, cancel tasks)
```

Window state (size, maximized): store in GSettings and restore at construction, bind with `settings.bind('window-width', this, 'default-width', Gio.SettingsBindFlags.DEFAULT)`.

> **Remember:** actions decouple UI from code; shortcuts attach to actions; GResource bundles UI and icons; preferences are rows bound to GSettings; wrap strings with `_()` from the start.

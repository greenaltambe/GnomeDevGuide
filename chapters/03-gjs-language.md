# 3. GJS: JavaScript for GNOME

GJS is Mozilla's JavaScript engine (SpiderMonkey) embedded with GNOME bindings. It is **not** Node.js and **not** a browser.

## 3.1 What exists and what does not

| Available | Not available |
|---|---|
| Modern ES (classes, `async`/`await`, destructuring, optional chaining, `import`) | `require()`, `process`, `fs`, `path`, `Buffer` |
| `console.log`, `print()`, `log()`, `logError()` | `fetch` (use libsoup via `gi://Soup`) |
| `setTimeout`, `setInterval`, `clearTimeout` | `window`, `document`, DOM |
| `TextEncoder`, `TextDecoder`, `URL` (recent GJS), `structuredClone` | npm packages that assume Node (pure-JS packages may work if bundled) |
| `Promise`, `Symbol`, `Map`, `Set`, `WeakRef` | Real threads (use subprocesses instead) |
| Native `import` of ES modules | JSON import via `import` (read the file instead) |

Check what your GJS supports: https://gjs.guide and the GJS repo docs (`doc/` folder in https://gitlab.gnome.org/GNOME/gjs).

## 3.2 Modules and imports

```js
// A library (GObject Introspection). ALWAYS pin the version for GTK-family libs.
import Gtk from 'gi://Gtk?version=4.0';
import Adw from 'gi://Adw?version=1';

// Libraries without multiple versions need no version
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import GObject from 'gi://GObject';

// Built-in GJS modules
import System from 'system';          // System.exit(), programInvocationName
import Gettext from 'gettext';        // translations

// Your own files: relative paths, WITH the .js extension
import {run} from './engine/run.js';
import * as Git from './engine/git.js';

// Exporting
export function foo() {}
export const BAR = 1;
export default class Thing {}
```

Notes:

- Paths are relative to the *importing* file (like browsers).
- Circular imports work but are a smell. Keep the dependency direction **ui → engine**, never the reverse.
- Modules run once and are cached, so module-level `const state = {}` is effectively a singleton.
- The legacy `imports.gi.Gtk` / `imports.lang` style still appears in old tutorials. **Avoid it in new code** (but `imports.system.programInvocationName` still works).

## 3.3 Globals and output

```js
print('goes to stdout');              // plain
console.log('also stdout', {a: 1});   // modern, formats objects
console.error('stderr');
log('legacy log');                    // stderr via GLib
logError(new Error('boom'));          // prints message + stack
```

Use `console.*` in new code. Use `GLib.log_structured` or `console` for debug output, not `print`, in a shipped app.

## 3.4 GObject types in JavaScript

How C types appear in JS:

| C type | JS value |
|---|---|
| `gint`, `guint`, `gdouble` | number |
| `gint64`, `guint64` | number (precision loss above 2^53) or BigInt in some APIs |
| `gboolean` | boolean |
| `gchar*` / `const char*` | string |
| `char**` (string list) | array of strings |
| `GList`, `GSList`, arrays | JS array |
| `GBytes` | `GLib.Bytes` (convert: `bytes.toArray()` gives `Uint8Array`) |
| `guint8*` + length | `Uint8Array` |
| `GVariant` | `GLib.Variant` (see Section 3.8) |
| enum / flags | `Gtk.Orientation.VERTICAL`, combine flags with `|` |
| `NULL` | `null` |
| out parameters | returned in an **array** alongside the return value |

### Out parameters (important and surprising)

C functions that fill in a pointer return those values to you in an array. If the function also has a return value, it comes **first**:

```js
// C: gboolean g_file_load_contents(file, cancellable, &contents, &length, &etag, &error)
const [ok, contents, etag] = file.load_contents(null);

// C: void gtk_widget_get_preferred_size(widget, &min, &natural)
const [min, natural] = widget.get_preferred_size();
```

If the function returns `void` or the boolean is merely an error indicator, GJS often drops it. When in doubt, `console.log(result)` once and look.

### Errors are exceptions

C functions with a `GError**` argument throw JS exceptions in GJS:

```js
try {
    file.load_contents(null);
} catch (e) {
    if (e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.NOT_FOUND)) {
        // handle missing file
    } else {
        throw e;
    }
}
```

`e.message`, `e.code`, `e.domain` are useful. Cancelled async operations throw `Gio.IOErrorEnum.CANCELLED`, which you usually want to ignore silently.

## 3.5 Calling conventions and naming

- Methods are `snake_case` (`set_margin_top`), matching C. Properties can be set as `widget.margin_top = 12` (snake_case also works for hyphenated properties like `icon_name`).
- Constructor takes an object of properties: `new Gtk.Label({label: 'hi', halign: Gtk.Align.START})`.
- Static functions live on the class: `Gtk.Button.new_with_label('x')`, `GLib.get_home_dir()`.
- Use **one** naming style consistently for properties (this guide uses `snake_case` as the GNOME convention).

## 3.6 Defining your own GObject classes

You need this when your class must have properties, signals, a template, or be used in a list model. For plain helper classes use ordinary JS classes.

```js
import GObject from 'gi://GObject';

export const Package = GObject.registerClass({
    GTypeName: 'PandaPackage',            // unique across the process
    Properties: {
        'name': GObject.ParamSpec.string(
            'name', 'Name', 'Package name',
            GObject.ParamFlags.READWRITE, ''),
        'size': GObject.ParamSpec.double(
            'size', 'Size', 'Size in bytes',
            GObject.ParamFlags.READWRITE, 0, Number.MAX_SAFE_INTEGER, 0),
    },
    Signals: {
        'removed': {},                                     // no args
        'progress': {param_types: [GObject.TYPE_DOUBLE]},  // one double
    },
}, class Package extends GObject.Object {
    constructor(params = {}) {
        super(params);          // sets the properties passed in
    }
});

const p = new Package({name: 'git', size: 123});
p.connect('notify::size', () => console.log('size changed'));
p.size = 456;                   // emits notify::size
p.emit('progress', 0.5);
```

Rules:

- `GTypeName` must be unique and conventionally CamelCase with a prefix.
- Pass **all** property values through `super(params)`. Never forget the call.
- Do not use class fields that clash with GObject property names (property storage is handled for you via the ParamSpec; if you want custom getter/setter, define `get name()`/`set name(v)` and call `this.notify('name')` yourself).
- Inherit from `GObject.Object`, `Gtk.Widget`, `Adw.Bin`, `Gtk.Box`, and so on, depending on need.

Custom getters/setters for validated state:

```js
class Foo extends GObject.Object {
    _count = 0;
    get count() { return this._count; }
    set count(v) {
        if (v === this._count) return;
        this._count = v;
        this.notify('count');
    }
}
```

## 3.7 Closures, `this`, and signal handlers

```js
button.connect('clicked', () => this._onClicked());     // arrow keeps `this`
button.connect('clicked', this._onClicked.bind(this));  // equivalent
button.connect('clicked', function () { /* `this` is NOT your object */ });
```

Always use an arrow function or `bind`. `connect()` returns an id so you can `disconnect(id)`.

## 3.8 GVariant, quickly

`GLib.Variant` is a typed value used by D-Bus, GSettings, and actions.

```js
const v = new GLib.Variant('s', 'hello');            // string
const n = GLib.Variant.new_int32(5);
const d = new GLib.Variant('a{sv}', {a: new GLib.Variant('i', 1)});

v.get_string()[0];          // 'hello'  (returns [string, length])
v.unpack();                 // shallow unpack
v.deepUnpack();             // recursively unpack
```

Type strings: `s` string, `i` int32, `u` uint32, `x` int64, `d` double, `b` boolean, `as` array of strings, `a{sv}` dictionary string to variant, `(si)` tuple. See https://docs.gtk.org/glib/gvariant-format-strings.html .

## 3.9 Memory and lifetimes (just enough)

- GJS has a garbage collector, GObjects are reference counted, and the two cooperate. You rarely free anything manually.
- **Leaks come from**: signal handlers that capture big objects and are never disconnected, `GLib.timeout_add` sources never removed, and long-living lists of widgets.
- Good habits:
  - Disconnect signals you attach to *long-lived* objects from *short-lived* widgets (in `vfunc_unroot` or a `destroy`-like hook).
  - Keep the ID from `GLib.timeout_add` and remove it with `GLib.Source.remove(id)` when the view goes away.
  - Cancel in-flight async operations with a `Gio.Cancellable` when the user navigates away.
- Do not hold on to widget references in global state.

## 3.10 Timers and idle work

```js
// every 2 seconds; return GLib.SOURCE_CONTINUE to repeat, SOURCE_REMOVE to stop
const id = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
    refresh();
    return GLib.SOURCE_CONTINUE;
});
GLib.Source.remove(id);

// run when the loop is idle
GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => { doSmallThing(); return GLib.SOURCE_REMOVE; });

// modern JS timers also work
setTimeout(() => console.log('later'), 500);
```

> **Remember:** `gi://` imports with versions, out-params come back as arrays, errors are exceptions, arrow functions for handlers, `registerClass` only when you need GObject features.

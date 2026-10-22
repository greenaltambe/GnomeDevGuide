# 4. GObject: Properties, Signals, and Models

If you understand this chapter, GTK documentation becomes readable.

## 4.1 Objects, classes, types

- A **class** defines behaviour (`Gtk.Button`). An **instance** is one button.
- Classes **inherit**: `Gtk.Button` is a `Gtk.Widget` is a `GObject.Object`. Methods and properties of parents are available on children.
- Every class has a **GType**, a runtime name (e.g. `GtkButton`). In docs you will see "Hierarchy" diagrams; read them to know what a widget inherits.
- **Interfaces** add capabilities without inheritance (e.g. `Gio.ListModel`, `Gtk.Orientable`, `Gtk.Editable`).

## 4.2 Properties

A property is named, typed, readable/writable data **that notifies when changed**.

```js
const label = new Gtk.Label({label: 'Hello'});   // set at construction
label.label = 'Bye';                              // set later
label.get_label();                                // getter method
label.set_label('Again');                         // setter method
label.connect('notify::label', () => console.log('label changed'));
```

Names in docs are kebab-case (`icon-name`). In JS use `icon_name` for access and `'notify::icon-name'` for the signal string (hyphenated). A frequent bug is writing `notify::icon_name`: GObject does accept both in modern versions, but prefer hyphens in signal names.

### Flags to know

`READABLE`, `WRITABLE`, `READWRITE`, `CONSTRUCT` (set at construction with a default), `CONSTRUCT_ONLY` (settable only once at creation), `EXPLICIT_NOTIFY`.

### Property bindings (very powerful)

Bind one property to another so they stay in sync, no manual signal code:

```js
// entry text drives label text
entry.bind_property('text', label, 'label', GObject.BindingFlags.SYNC_CREATE);

// two-way, e.g. a switch and a settings-backed object
a.bind_property('value', b, 'value',
    GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE);

// invert a boolean
sw.bind_property('active', revealer, 'reveal-child',
    GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN);

// with transform
src.bind_property_full('size', row, 'subtitle',
    GObject.BindingFlags.SYNC_CREATE,
    (binding, bytes) => [true, GLib.format_size(bytes)],  // [success, value]
    null);
```

The binding lives as long as both objects do (or until `binding.unbind()`).

## 4.3 Signals

A signal is a named event. You `connect` a callback.

```js
const id = button.connect('clicked', (btn) => { ... });   // first arg: emitter
button.disconnect(id);
button.connect_after(...)       // run after the default handler
button.block_signal_handler(id) // temporarily mute
GObject.signal_handler_block / unblock
```

- The **first argument** to the callback is always the emitting object, followed by the signal's parameters. Docs list the parameters under "Signals".
- Some signals expect a **return value** (e.g. `close-request` returns `true` to stop closing, `key-pressed` returns `true` if handled). Returning `undefined` counts as "false".
- Emit your own: `this.emit('my-signal', arg)`; declare them in `Signals` (Chapter 3).

### Property-change signals

`notify::<property>` fires after a change. Use it to react to selection changes: `dropdown.connect('notify::selected', ...)`.

## 4.4 Properties versus signals: choosing

| Use a property when... | Use a signal when... |
|---|---|
| it represents **state** you can ask for any time | it is a one-off **event** ("finished", "activated") |
| others may want to bind to it | no persistent value to query |

## 4.5 List models, the heart of GTK lists

Modern GTK builds lists from a **model** (data) and a **view** (widgets), connected by a **factory**.

```
Gio.ListStore  ──►  (optional) Gtk.FilterListModel / SortListModel ──►  Gtk.SelectionModel ──► ListView / ColumnView / GridView
 (your items)            filter + sort without changing data              selection state        creates row widgets
```

- `Gio.ListModel` is the *interface*: "an ordered list of GObjects", with signal `items-changed(position, removed, added)`.
- `Gio.ListStore` is the simplest writable implementation. Items **must be GObjects of one type** (so make your data a `registerClass` class).
- `Gtk.StringList` is a ready model of strings.
- `Gtk.FilterListModel` + `Gtk.CustomFilter` / `Gtk.StringFilter` → search boxes.
- `Gtk.SortListModel` + `Gtk.CustomSorter` / `Gtk.StringSorter` / `Gtk.NumericSorter` → sort by column.
- `Gtk.SingleSelection` / `Gtk.MultiSelection` / `Gtk.NoSelection` → selection state.
- `Gtk.TreeListModel` → hierarchical data (trees).

```js
const store = new Gio.ListStore({item_type: Package});
store.append(new Package({name: 'git', size: 1}));
store.splice(0, store.get_n_items(), newItems);   // replace everything at once (efficient)
store.remove_all();
```

Prefer `splice` over many `append` calls so the UI updates once.

Full example in Section 5.7.

## 4.6 Actions (GAction)

An **action** is a named operation ("quit", "open-file", "repo.delete") that can be triggered from a menu, a button, a keyboard shortcut or a D-Bus call, without those parts knowing each other.

```js
const quit = new Gio.SimpleAction({name: 'quit'});
quit.connect('activate', () => app.quit());
app.add_action(quit);                                 // becomes "app.quit"
app.set_accels_for_action('app.quit', ['<Control>q']);
```

- `app.*` actions are application-wide, `win.*` are per-window, and custom prefixes come from `insert_action_group('repo', group)`.
- A button uses it with `action_name: 'app.quit'`.
- Actions may have a **parameter type** and **state** (checkbox/radio behaviour). See Chapter 11.

## 4.7 Reference counting vs GC (one paragraph)

GObjects are reference-counted in C; GJS wraps each in a JS object and keeps the count in sync. When the last JS reference **and** all C references vanish, the object is freed. Practically: if a signal connection or a parent widget holds the object, it stays alive; otherwise the GC may free it, so keep a reference (`this._timer = ...`) to anything you need to persist.

> **Remember:** properties = notifiable state (bind them), signals = events (first arg is the emitter), list models + factories drive lists, actions decouple UI from behaviour.

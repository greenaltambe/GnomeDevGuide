# 6. libadwaita: The GNOME Look

Docs: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/ . Browse the **Widget Gallery** there, and run `adwaita-1-demo` locally.

Always import as: `import Adw from 'gi://Adw?version=1';`

## 6.1 Window structure (the modern pattern)

```
Adw.ApplicationWindow
└─ Adw.ToastOverlay                    (toasts appear over everything)
   └─ Adw.NavigationSplitView          (sidebar + content, collapses on narrow screens)
      ├─ sidebar: Adw.NavigationPage
      │   └─ Adw.ToolbarView
      │       ├─ top: Adw.HeaderBar
      │       └─ content: sidebar list
      └─ content: Adw.NavigationPage
          └─ Adw.ToolbarView
              ├─ top: Adw.HeaderBar
              └─ content: page content
```

**`Adw.ToolbarView`** puts top and bottom bars around content. Use it instead of old `Gtk.Box` with a header; it supports flat/raised styles when scrolling.

## 6.2 The widget catalogue you actually need

### Application and windows
| Widget | Purpose |
|---|---|
| `Adw.Application` | Replaces `Gtk.Application`; initialises libadwaita, dark mode, etc. |
| `Adw.ApplicationWindow` | Window with adaptive features and breakpoints |
| `Adw.Dialog` | Modal dialog presented inside a window (adaptive, bottom-sheet on narrow) |
| `Adw.AlertDialog` | Simple question/confirm dialog |
| `Adw.PreferencesDialog` | Whole preferences UI (with `Adw.PreferencesPage` inside) |
| `Adw.AboutDialog` | The About window, filled with metadata |
| `Adw.ShortcutsDialog` | Keyboard shortcuts list |

Older names (`Adw.MessageDialog`, `Adw.PreferencesWindow`, `Adw.AboutWindow`) exist but are deprecated in new versions. Check "Since" in the docs for what your libadwaita offers.

### Navigation
| Widget | Purpose |
|---|---|
| `Adw.NavigationSplitView` | Sidebar + content; collapses to a stack on narrow windows |
| `Adw.OverlaySplitView` | Sidebar that overlays content when narrow |
| `Adw.NavigationView` / `Adw.NavigationPage` | Push/pop page stack (drill-down) |
| `Adw.ViewStack` + `Adw.ViewSwitcher` / `ViewSwitcherBar` / `ViewSwitcherTitle` | Tabbed top-level sections |
| `Adw.TabView` / `Adw.TabBar` / `Adw.TabOverview` | Browser-like tabs |
| `Adw.Breakpoint` | Change layout at certain widths |

### Content
| Widget | Purpose |
|---|---|
| `Adw.HeaderBar` | Title bar. `pack_start`, `pack_end`, `title_widget` |
| `Adw.PreferencesPage` / `PreferencesGroup` | Settings-like pages with titled groups |
| `Adw.ActionRow` | Row with title, subtitle, prefix and suffix widgets |
| `Adw.ExpanderRow` | Row that expands to show more rows |
| `Adw.EntryRow`, `PasswordEntryRow`, `SpinRow`, `SwitchRow`, `ComboRow` | Rows containing inputs |
| `Adw.ButtonRow` | A row that is a button |
| `Adw.StatusPage` | Empty/placeholder/error pages with big icon |
| `Adw.Banner` | Thin info bar at the top of content |
| `Adw.ToastOverlay` + `Adw.Toast` | Transient messages with an optional button |
| `Adw.Clamp` / `Adw.ClampScrollable` | Limit content width so it does not stretch on wide screens |
| `Adw.Bin` | A single-child wrapper (handy base class) |
| `Adw.Carousel`, `Adw.Avatar`, `Adw.Spinner` | Specialised (swipe pages, user avatar, loading spinner) |
| `Adw.WrapBox`, `Adw.InlineViewSwitcher` | Newer layout helpers (check availability) |

## 6.3 Lists of rows ("boxed lists")

The bread-and-butter GNOME settings look:

```js
const group = new Adw.PreferencesGroup({
    title: 'Applications',
    description: '14 installed',
});

const row = new Adw.ActionRow({
    title: 'Heroic',
    subtitle: 'Flatpak · 623 MB',
    activatable: true,
});
row.add_prefix(new Gtk.Image({icon_name: 'application-x-executable-symbolic'}));
row.add_suffix(new Gtk.Image({icon_name: 'go-next-symbolic'}));
group.add(row);

const page = new Adw.PreferencesPage();
page.add(group);
```

An `Adw.PreferencesPage` already scrolls and clamps width, so it is also a great container for **non-settings** list pages.

Expanders for details (e.g. "Package details"):

```js
const expander = new Adw.ExpanderRow({title: 'my-repo', subtitle: '2 uncommitted · 1 unpushed'});
expander.add_row(new Adw.ActionRow({title: 'Branch', subtitle: 'main'}));
```

Escaping: `title` and `subtitle` parse **Pango markup**. If text could contain `&` or `<` (package names, paths!) set `use_markup: false` on the row, or escape with `GLib.markup_escape_text(text, -1)`. Forgetting this gives warnings and blank rows.

## 6.4 Sidebar and sections (PandaManager shape)

```js
const split = new Adw.NavigationSplitView({
    min_sidebar_width: 200, max_sidebar_width: 280,
});

// sidebar
const sideList = new Gtk.ListBox({css_classes: ['navigation-sidebar']});
for (const [id, label, icon] of [
    ['apps', 'Apps', 'view-app-grid-symbolic'],
    ['repos', 'Repositories', 'folder-symbolic'],
    ['storage', 'Storage', 'drive-harddisk-symbolic'],
]) {
    const row = new Adw.ActionRow({title: label});
    row.add_prefix(new Gtk.Image({icon_name: icon}));
    row.name = id;                           // widget name carries the page id
    sideList.append(row);
}

const sideToolbar = new Adw.ToolbarView({content: sideList});
sideToolbar.add_top_bar(new Adw.HeaderBar({show_title: false}));
split.sidebar = new Adw.NavigationPage({title: 'PandaManager', child: sideToolbar});

// content
const stack = new Gtk.Stack({transition_type: Gtk.StackTransitionType.CROSSFADE});
stack.add_named(appsPage, 'apps');
stack.add_named(reposPage, 'repos');
const contentToolbar = new Adw.ToolbarView({content: stack});
contentToolbar.add_top_bar(new Adw.HeaderBar());
split.content = new Adw.NavigationPage({title: 'Apps', child: contentToolbar});

sideList.connect('row-selected', (_l, row) => {
    if (row) stack.visible_child_name = row.name;
});
```

Adaptive collapse: attach an `Adw.Breakpoint` to the window:

```js
const bp = new Adw.Breakpoint({condition: Adw.BreakpointCondition.parse('max-width: 600sp')});
bp.add_setter(split, 'collapsed', true);
window.add_breakpoint(bp);
```

(Or via Blueprint, Chapter 7, which is much tidier.) `sp` is a font-scaled pixel so it adapts to text size.

## 6.5 Toasts, banners, status pages

```js
const toast = new Adw.Toast({title: 'Moved "old-repo" to Trash', button_label: 'Undo', timeout: 8});
toast.connect('button-clicked', () => restore());
toastOverlay.add_toast(toast);
```

```js
new Adw.StatusPage({
    icon_name: 'folder-symbolic',
    title: 'No Repositories',
    description: 'Add a folder to scan for git repositories.',
    child: new Gtk.Button({label: 'Add Folder…', css_classes: ['suggested-action', 'pill'], halign: Gtk.Align.CENTER}),
});
```

Use a `StatusPage` for **empty**, **loading error**, and **first-run** states. Every list page needs these three states: loading (spinner), empty, content.

## 6.6 Alert dialogs (confirm destructive actions)

```js
const dialog = new Adw.AlertDialog({
    heading: 'Move repository to Trash?',
    body: `"${name}" has no uncommitted changes and is fully pushed.`,
});
dialog.add_response('cancel', 'Cancel');
dialog.add_response('trash', 'Move to Trash');
dialog.set_response_appearance('trash', Adw.ResponseAppearance.DESTRUCTIVE);
dialog.set_default_response('cancel');     // Enter key picks the safe option
dialog.set_close_response('cancel');       // Esc

dialog.choose(window, null, (d, res) => {
    const response = d.choose_finish(res);
    if (response === 'trash') doIt();
});
```

Or with Promises after promisifying (Chapter 9): `const response = await dialog.choose(window, null);`.

Can add an `extra_child` (e.g. a list of what will be removed). Always make the **non-destructive** answer the default.

## 6.7 Dark mode and accent colour

libadwaita follows the system style automatically. Override only if truly needed:

```js
const sm = Adw.StyleManager.get_default();
sm.color_scheme = Adw.ColorScheme.PREFER_DARK;   // or DEFAULT / FORCE_LIGHT / FORCE_DARK
sm.dark;                                          // is dark currently?
sm.connect('notify::dark', () => ...);
sm.accent_color                                   // 1.6+ ; use @accent_bg_color in CSS
```

Prefer the user's system setting. Provide an override only inside Preferences if at all.

## 6.8 Adaptive layouts

- Width is the main axis: test at ~360px wide (phone) and wide (1400px).
- Use `Adw.Clamp` around forms and text-heavy content.
- Use split views/breakpoints (above) for sidebars.
- `Adw.ViewSwitcherBar` shows at the bottom on narrow windows, `ViewSwitcherTitle` in the header on wide windows.
- Use `Gtk.ScrolledWindow` + `Gtk.FlowBox` for grids that must wrap.

## 6.9 About dialog

```js
const about = new Adw.AboutDialog({
    application_name: 'PandaManager',
    application_icon: 'io.github.you.PandaManager',
    developer_name: 'Your Name',
    version: '0.1.0',
    website: 'https://github.com/you/pandamanager',
    issue_url: 'https://github.com/you/pandamanager/issues',
    license_type: Gtk.License.GPL_3_0,
    copyright: '© 2026 Your Name',
});
about.present(window);
```

## 6.10 HIG patterns to copy

- **Primary action** in the header bar (`pack_end`), styled `suggested-action` only when it is the main thing.
- **Search**: a toggle button in the header bar + `Gtk.SearchBar` + `Gtk.SearchEntry`, enabled by typing (`search_bar.key_capture_widget = window`).
- **Empty states** with a helpful next step.
- **Undo toast** instead of "Are you sure?" for reversible actions. Dialog only for irreversible ones.
- **Don't** put more than ~3 buttons in a header bar; put extras into the primary menu.
- Read https://developer.gnome.org/hig/patterns/ for each pattern you build.

> **Remember:** ToolbarView + HeaderBar, NavigationSplitView for sidebars, PreferencesGroup + ActionRow for lists, StatusPage for empty states, Toast for undo, AlertDialog for destructive confirmation, escape markup in rows.

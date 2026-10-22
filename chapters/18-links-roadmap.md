# 18. Links and a Learning Roadmap

## 18.1 Official documentation

| Topic | URL |
|---|---|
| GNOME developer hub | https://developer.gnome.org/ |
| Documentation index | https://developer.gnome.org/documentation/ |
| Human Interface Guidelines | https://developer.gnome.org/hig/ |
| GTK 4 API | https://docs.gtk.org/gtk4/ |
| GLib / GObject / Gio API | https://docs.gtk.org/glib/ , https://docs.gtk.org/gobject/ , https://docs.gtk.org/gio/ |
| libadwaita docs | https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/ |
| libadwaita style classes | https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/style-classes.html |
| Blueprint | https://gnome.pages.gitlab.gnome.org/blueprint-compiler/ |
| GJS guides | https://gjs.guide/ |
| GJS API browser | https://gjs-docs.gnome.org/ |
| GJS source & docs | https://gitlab.gnome.org/GNOME/gjs |
| PyGObject | https://pygobject.gnome.org/ |
| gtk-rs book | https://gtk-rs.org/gtk4-rs/stable/latest/book/ |
| libadwaita-rs | https://world.pages.gitlab.gnome.org/Rust/libadwaita-rs/ |
| Flatpak docs | https://docs.flatpak.org/ |
| Flathub for app authors | https://docs.flathub.org/ |
| Meson | https://mesonbuild.com/ |
| AppStream spec | https://www.freedesktop.org/software/appstream/docs/ |
| Desktop entry spec | https://specifications.freedesktop.org/desktop-entry-spec/latest/ |
| XDG base directories | https://specifications.freedesktop.org/basedir-spec/latest/ |
| D-Bus tutorial | https://dbus.freedesktop.org/doc/dbus-tutorial.html |
| PackageKit | https://www.freedesktop.org/software/PackageKit/ |
| polkit | https://www.freedesktop.org/software/polkit/docs/latest/ |
| Icon names | https://specifications.freedesktop.org/icon-naming-spec/latest/ |
| GNOME release schedule | https://release.gnome.org/ |

Community: https://discourse.gnome.org/ , Matrix `#gjs:gnome.org`, `#gtk:gnome.org`, `#flatpak:matrix.org`.

Tools on Flathub: Workbench, GNOME Builder, Icon Library, Sysprof, D-Spy.

(URLs change occasionally; if one 404s, search the title or start from developer.gnome.org.)

## 18.2 Suggested learning path

### Stage 1: Foundations (a weekend)
- [ ] Install tools (Chapter 2). Run Workbench; open the **Library** and read 10 demos.
- [ ] Write the hello window by hand. Add a button that changes a label.
- [ ] Read GJS chapter (3) and GObject chapter (4). Make a class with a property and a signal; bind a property.
- [ ] Browse `adwaita-1-demo` and `gtk4-demo`.

### Stage 2: A real shell (a week)
- [ ] Build the main window: ToolbarView, HeaderBar, NavigationSplitView with a sidebar list.
- [ ] Add 3 empty pages with StatusPage.
- [ ] Add an About dialog, a primary menu, and a Preferences dialog.
- [ ] Convert one page to Blueprint + template.

### Stage 3: Real work (2 to 3 weeks)
- [ ] Engine: `run.js`, `flatpak` and `dnf` sources, aggregate with `allSettled`.
- [ ] Model: `PackageItem` + `Gio.ListStore`, page with loading/empty/ready states.
- [ ] Search + sort with `FilterListModel` and `SortListModel`.
- [ ] Persist a cache as JSON; show cached data first.
- [ ] Add async cancellation and a refresh action with `F5`.

### Stage 4: Safe destructive features
- [ ] Git status engine and page.
- [ ] "Safe to remove" logic with unit scripts against fixture repos.
- [ ] Preview dialog, trash, undo toast, action log.
- [ ] Storage page via `du`, with known cache locations.

### Stage 5: Polish and ship
- [ ] Dark mode and narrow-width testing, keyboard navigation.
- [ ] GSettings for preferences.
- [ ] Meson + GResource + `.desktop` + icon; install to `~/.local`.
- [ ] Optional: RPM/COPR or Flatpak with portals.

### Stage 6: Advanced
- [ ] Custom widgets / `DrawingArea` charts.
- [ ] D-Bus integration (PackageKit, UDisks2, systemd).
- [ ] Privileged helper + polkit policy.
- [ ] Background scans, notifications.
- [ ] Rewrite a hot module as a Rust or Python helper process if JS is too slow.
- [ ] Build a second small app in Python or Rust using Chapters 14 and 15.

## 18.3 Mapping to PandaManager milestones

| Milestone | Guide chapters you need |
|---|---|
| 1. Installed-software inventory | 3, 8 (Subprocess), 9, 10.2, 6.3, 5.7 |
| 2. Git dashboard + safe-to-delete | 8, 9.5, 10.7, 10.9, 6.6, 13.6 |
| 3. Storage view + cleanup | 8.2 (`du`), 9, 13.5, 5.9 (drawing), 8.5 (polkit/PackageKit) |
| 4. Rules, gaming, update-all | 8.2 (monitors), 11 (actions, preferences), 8.6 (notifications) |

## 18.4 Habits that keep an app maintainable

- Keep the engine free of UI imports, forever.
- One feature = one branch; commit small; write down decisions in `docs/`.
- Run the Inspector every time a layout looks off, before guessing.
- When something is hard in GTK, you are probably fighting it; find the intended widget or pattern in the HIG and gallery.
- Re-read this guide's Chapter 16 whenever you hit an unfamiliar API.

## 18.5 Updating this guide

This repository is its own project so the guide can evolve. Suggestions:

- Add a section when you learn something that cost you more than an hour.
- Note GNOME/libadwaita version in the heading when you add version-dependent material.
- Rebuild the PDF with `./build.sh`.

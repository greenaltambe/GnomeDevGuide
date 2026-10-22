# 1. The GNOME Platform: What You Are Building On

## 1.1 The stack, bottom to top

```
 Your app (JS / Python / Rust)
 ───────────────────────────────────────────────
 libadwaita   adaptive, modern GNOME widgets & styling
 GTK 4        widgets, layout, input, rendering
 ───────────────────────────────────────────────
 Pango (text)  Cairo (2D)  GdkPixbuf/Glycin (images)  GStreamer (media)
 ───────────────────────────────────────────────
 Gio          files, processes, D-Bus, settings, networking
 GObject      object system: classes, properties, signals
 GLib         data structures, main loop, utilities
 ───────────────────────────────────────────────
 Linux: Wayland/X11, D-Bus, systemd, polkit, portals
```

| Library | Plain-English role | You will use it for |
|---|---|---|
| **GLib** | The standard library of the GNOME world | Main loop, timers, paths (`GLib.get_home_dir()`), string and date helpers |
| **GObject** | The object system | Defining your own classes, properties, signals |
| **Gio** | "Input/Output" | Files, running programs, D-Bus, `GSettings`, `GListStore`, actions |
| **GTK 4** | Toolkit | Windows, buttons, lists, layout, keyboard handling |
| **libadwaita (Adw)** | GNOME's design language | Header bars, preference rows, sidebars, dialogs, toasts, dark mode |
| **Pango** | Text layout | Mostly used indirectly through labels |
| **Cairo / GSK** | Drawing | Custom drawing, charts |
| **GStreamer** | Audio/video | Only if you play media |

## 1.2 GTK versus libadwaita

- **GTK** is generic: it has `Gtk.Button`, `Gtk.Box`, `Gtk.ListView`.
- **libadwaita** is GNOME-specific polish on top: `Adw.HeaderBar`, `Adw.ActionRow`, `Adw.NavigationSplitView`, `Adw.AlertDialog`.

Rule of thumb: **use Adw widgets where one exists, GTK for everything else.** A modern GNOME app always uses both. Only use GTK4 alone if you intentionally want to look non-GNOME.

## 1.3 GObject Introspection (why JS can use C libraries)

C libraries are annotated, and a tool produces a **GIR** (XML) and a **typelib** (binary). Language runtimes load the typelib at runtime.

- In GJS: `import Gtk from 'gi://Gtk?version=4.0'`
- In Python: `gi.require_version('Gtk', '4.0')`
- In Rust: crates (`gtk4`, `libadwaita`) generated from the same GIR files.

Consequences you will notice:

- The JS API mirrors the C API with naming conversions (Chapter 16).
- If a library has no typelib installed, the import fails. On Fedora: `dnf search gir | grep <lib>` or install `<lib>-devel` (devel packages ship `.gir` files; runtime packages ship typelibs).
- Check what is installed: `ls /usr/lib64/girepository-1.0/` (typelibs) and `ls /usr/share/gir-1.0/` (GIR XML).

## 1.4 Versions and what "since" means

- GTK and libadwaita follow **semantic-ish versions**: new widgets arrive in minor releases (e.g. `Adw.AlertDialog` arrived in libadwaita 1.5).
- Every API doc page says **"Since: x.y"** and **"Deprecated: x.y"**. Check these. If you target Fedora (new) only, you are safe; if you package a Flatpak, you are bound by the **GNOME runtime version** you choose.
- GNOME releases twice a year (March, September). Runtimes are named by number (`org.gnome.Platform//49` and so on). Check https://release.gnome.org and https://flathub.org for current ones.
- Check your own versions:

```sh
gjs --version
pkg-config --modversion gtk4 libadwaita-1
```

## 1.5 Desktop integration concepts

These are not libraries but conventions every app takes part in.

| Concept | What it is | Why you care |
|---|---|---|
| **App ID** | Reverse-DNS name, e.g. `io.github.you.PandaManager` | Identifies the app to the whole system; must match the `.desktop` file name, the icon name, the D-Bus name |
| **`.desktop` file** | Launcher metadata (name, icon, exec) | Makes the app appear in the Activities overview |
| **AppStream metainfo** | XML description for software stores | Needed for Flathub / GNOME Software |
| **GSettings** | Typed key/value settings backed by dconf | Storing preferences |
| **XDG directories** | `~/.config`, `~/.local/share`, `~/.cache` | Where to put files (never invent your own dotfolder in `~`) |
| **D-Bus** | System-wide message bus | Talking to other programs and services |
| **Portals** | Sandbox-safe APIs (file chooser, screenshots, notifications) | Required inside Flatpak, good practice outside |
| **polkit** | Privilege escalation prompts | Doing root actions without running as root |

## 1.6 The GNOME Human Interface Guidelines (HIG)

GNOME apps follow design rules: https://developer.gnome.org/hig/ . Skim these ideas now:

- Use a **header bar** with window controls; put the primary action in it.
- **No menu bar**. Use a primary menu (the "hamburger") in the header bar.
- Prefer **preferences windows** and **inline switches** to modal settings dialogs.
- Apps must be **adaptive**: usable at narrow widths (phones, split screens).
- Destructive actions need **confirmation or undo**. Undo toasts are preferred.
- Use **symbolic icons** (e.g. `edit-delete-symbolic`) so they recolour with the theme.

> **Remember:** apps sit on GLib/GObject/Gio/GTK/libadwaita; bindings come from GIR; follow the HIG; check "Since" versions.

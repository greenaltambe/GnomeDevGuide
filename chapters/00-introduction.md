# The GNOME Application Development Guide

**From zero to advanced, in JavaScript (GJS), with Python and Rust companions.**

This guide is a long-lived reference. It is written for someone who can already program, has maybe touched GNOME Shell extensions, and now wants to build real, standalone GNOME applications without feeling lost.

## How this guide is organised

| Part | Chapters | What you get |
|------|----------|--------------|
| **A. Foundations** | 1 to 3 | What GNOME is made of, how to set up, the JavaScript (GJS) language bits you need |
| **B. The toolkit** | 4 to 7 | GObject, GTK4, libadwaita, Blueprint and templates |
| **C. Doing real work** | 8 to 10 | Gio (files, processes, D-Bus), async programming, app architecture |
| **D. Shipping** | 11 to 13 | Actions, settings, resources, packaging, debugging, security |
| **E. Other languages** | 14 and 15 | Python (PyGObject) and Rust (gtk-rs) equivalents |
| **F. Reference** | 16 to 18 | How to read the docs, cheat sheets, glossary, link list |

**How to read it:** if you are new, read Parts A to C in order, building the small examples. After that, jump around. Every chapter ends with a short "Remember" box so you can skim later.

## Conventions

- Code blocks marked `js` are GJS (ES modules). `py` is Python. `rust` is Rust. `blp` is Blueprint. `xml` is XML. `sh` is a shell command.
- "Fedora" commands use `dnf`. Other distros have the same packages under similar names.
- Version numbers go stale. Where it matters, this guide tells you *how to check* instead of just stating a number.
- The running example is **PandaManager**, a Linux manager app (installed software, git repos, storage). You do not need that project to follow along; it is just a realistic target.

## The five-minute mental model

Read this once, and everything else slots into place.

1. A GNOME app is a **normal program** that links against a handful of **C libraries** (GLib, GTK, libadwaita...).
2. Those libraries describe themselves in **GIR files** (a machine-readable API description). That is what lets JavaScript, Python, Rust, and Vala call them. Your language does not reimplement GTK; it *talks to* the C library.
3. Everything is a **GObject**: widgets, files, list models, settings. GObjects have **properties** (data you can read, write, and watch) and **signals** (events you can listen to). Learn these two ideas and GTK stops being mysterious.
4. The UI runs on **one thread with a main loop**. You never block it. Anything slow (disk, network, running programs) is done **asynchronously**, and you `await` the result.
5. **libadwaita** gives you the modern GNOME look and adaptive layouts. **GTK** gives you the raw widgets.
6. To be installed nicely you add a few **metadata files** (a `.desktop` file, an icon, an app ID). To be distributed you usually build a **Flatpak**.

> **Remember:** libraries in C, bindings generated from GIR, everything is a GObject, one main loop, never block it.

## Honest expectations

- GJS is a small community. Documentation has gaps. You will sometimes read C documentation and translate it in your head. Chapter 16 teaches exactly how.
- Your Shell-extension experience helps (same language, same GObject), but note: **extensions use `imports` from Shell, apps use `gi://` and GTK/Adw**. Shell code uses St and Clutter; apps use GTK4.

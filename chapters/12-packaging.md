# 12. Packaging and Distribution

You can use your app forever with `gjs -m src/main.js`. Packaging gives you: a launcher in the Activities overview, an icon, and a way to share it. Do it when the app is useful, not before.

## 12.1 Files every installed app needs

| File | Location when installed | Purpose |
|---|---|---|
| Executable launcher | `/usr/bin/<name>` or `/app/bin/<name>` (Flatpak) | Starts the app |
| `.desktop` | `share/applications/<app-id>.desktop` | Menu entry |
| Icon (SVG) | `share/icons/hicolor/scalable/apps/<app-id>.svg` | App icon (colourful, full size) |
| Symbolic icon | `share/icons/hicolor/symbolic/apps/<app-id>-symbolic.svg` | Monochrome variant |
| Metainfo | `share/metainfo/<app-id>.metainfo.xml` | Store listing (AppStream) |
| GSettings schema | `share/glib-2.0/schemas/<app-id>.gschema.xml` | Preferences |
| GResource | `share/<app-id>/*.gresource` | Compiled UI |
| Translations | `share/locale/*/LC_MESSAGES/*.mo` | i18n |

The **app ID** must be consistent everywhere (`.desktop` filename, icon name, D-Bus name, metainfo `<id>`, GSettings schema id, resource prefix).

Choosing an ID: reverse DNS of something you control: `io.github.<username>.PandaManager` (GitHub Pages domain) or `org.gnome.gitlab.<user>.<App>`. Flathub verifies domains.

### Example `.desktop`

```ini
[Desktop Entry]
Name=PandaManager
Comment=Manage software, repositories and storage
Exec=pandamanager
Icon=io.github.you.PandaManager
Terminal=false
Type=Application
Categories=GNOME;GTK;System;Utility;
StartupNotify=true
```

Validate: `desktop-file-validate data/*.desktop`.

### Example metainfo (minimum)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>io.github.you.PandaManager</id>
  <name>PandaManager</name>
  <summary>Manage software, repositories and storage</summary>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <description><p>One place to see everything installed on your system.</p></description>
  <launchable type="desktop-id">io.github.you.PandaManager.desktop</launchable>
  <releases><release version="0.1.0" date="2026-10-22"/></releases>
  <content_rating type="oars-1.1"/>
</component>
```

Validate: `appstreamcli validate data/*.metainfo.xml`.

## 12.2 Meson: the GNOME build system

Learn just enough Meson to copy and adapt a template. The best way: **generate a "GNOME Application (JavaScript)" project in GNOME Builder** and read it. It gives you `meson.build`, a launcher script, GResource setup, Blueprint compilation, tests, and a Flatpak manifest, all wired correctly.

A map of what you will see:

```
meson.build                     project definition, version, subdirs
src/meson.build                 compile gresource, install JS, configure launcher
src/app-id.in / launcher.in     templates configured with install paths
data/meson.build                installs .desktop, metainfo, icons, schema, validations
po/meson.build, POTFILES        translations
build-aux/*.json                flatpak-builder manifest
```

Key Meson helpers (module `gnome`): `gnome.compile_resources()`, `gnome.compile_schemas()`, `gnome.post_install()`, `i18n.merge_file()`. Blueprint: `custom_target` with `blueprint-compiler` or the `blueprints` helper pattern in templates.

Build and install locally:

```sh
meson setup build --prefix=$HOME/.local
meson compile -C build
meson install -C build
```

(Installing under `~/.local` gives you a menu entry without root. Run `glib-compile-schemas ~/.local/share/glib-2.0/schemas` and `gtk4-update-icon-cache` if needed.)

Reference: https://mesonbuild.com/ and https://mesonbuild.com/Gnome-module.html

## 12.3 Flatpak

Flatpak is the primary way to distribute desktop apps (Flathub).

**Concepts**

- **Runtime**: the shared base (`org.gnome.Platform//<version>` containing GTK, libadwaita, GJS) and **SDK** (`org.gnome.Sdk` for building).
- **Sandbox**: apps see only what you permit (`finish-args`).
- **Portals**: sandbox-safe file pickers, etc.

**Manifest (`build-aux/io.github.you.PandaManager.json`)**

```json
{
  "app-id": "io.github.you.PandaManager",
  "runtime": "org.gnome.Platform",
  "runtime-version": "<current GNOME version>",
  "sdk": "org.gnome.Sdk",
  "command": "pandamanager",
  "finish-args": [
    "--share=ipc",
    "--socket=fallback-x11",
    "--socket=wayland",
    "--device=dri"
  ],
  "modules": [
    {
      "name": "pandamanager",
      "buildsystem": "meson",
      "sources": [{"type": "dir", "path": ".."}]
    }
  ]
}
```

For JavaScript apps with a bundled `blueprint-compiler`, add the blueprint module (look at Builder's template). The `runtime-version` must match an installed runtime: `flatpak install flathub org.gnome.Platform//<ver> org.gnome.Sdk//<ver>`.

Build, install, run:

```sh
flatpak-builder --user --install --force-clean build-dir build-aux/io.github.you.PandaManager.json
flatpak run io.github.you.PandaManager
```

**Permissions** (add to `finish-args` only as needed): `--filesystem=home` (all of home), `--filesystem=xdg-documents`, `--talk-name=org.freedesktop.PackageKit`, `--share=network`. Fewer is better; Flathub reviewers push back on broad access.

**Why PandaManager doesn't use Flatpak (yet)**: it needs the host's `dnf`, `rpm`, home folders, and other package managers. A sandbox fights this. Options later: an RPM/COPR, or a small host helper.

Flathub submission guide: https://docs.flathub.org/docs/for-app-authors/submission

## 12.4 RPM (Fedora-native)

For a host-integrating app, an RPM or COPR repository is a better fit:

- Needs a `.spec` file: `Name`, `Version`, `Requires: gjs gtk4 libadwaita`, `%build` with `%meson`, `%install` with `%meson_install`.
- Build locally: `rpmbuild` or `fedpkg`/`mock`; host on **COPR** (https://copr.fedorainfracloud.org) so users `dnf copr enable you/pandamanager`.
- Docs: https://rpm-packaging-guide.github.io/ and the Fedora Packaging Guidelines.

## 12.5 AppImage / other

Not idiomatic for GNOME apps; mentioned for completeness. Prefer Flatpak or distro packages.

## 12.6 Versioning and releases

- Semantic-ish version in `meson.build` and metainfo `<release>` entries.
- Tag releases in git (`git tag v0.1.0`).
- Keep a `CHANGELOG.md`; the same notes feed the metainfo release description.

> **Remember:** consistent app ID everywhere; copy Builder's template for Meson; validate `.desktop` and metainfo; Flatpak for portable apps, RPM/COPR for host-managing apps.

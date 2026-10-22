# 15. Rust (gtk-rs) Companion

Choose Rust when you want speed, strong typing, long-running reliability, or you plan to share code with a CLI/daemon. The learning curve is steeper than JS or Python: you must also understand Rust ownership, and gtk-rs requires subclassing patterns that feel verbose at first.

Docs:
- The book: https://gtk-rs.org/gtk4-rs/stable/latest/book/ (**start here**)
- API: https://gtk-rs.org/gtk4-rs/stable/latest/docs/gtk4/
- libadwaita crate: https://world.pages.gitlab.gnome.org/Rust/libadwaita-rs/
- Rust language: https://doc.rust-lang.org/book/

## 15.1 Setup

```sh
sudo dnf install rust cargo gtk4-devel libadwaita-devel glib2-devel gcc pkgconf-pkg-config
cargo new --bin pandamanager && cd pandamanager
cargo add gtk4 --rename gtk
cargo add libadwaita --rename adw
```

Crate names: `gtk4`, `libadwaita`, `gio`, `glib` (re-exported through `gtk::gio`, `gtk::glib`). Versions of the crates track GTK/libadwaita releases; use features to enable newer APIs, e.g. `features = ["v1_5"]` for libadwaita 1.5 widgets. Check the crate docs for the feature names.

## 15.2 Hello window

```rust
use adw::prelude::*;

fn main() -> gtk::glib::ExitCode {
    let app = adw::Application::builder()
        .application_id("org.example.Hello")
        .build();

    app.connect_activate(|app| {
        let toolbar = adw::ToolbarView::new();
        toolbar.add_top_bar(&adw::HeaderBar::new());
        toolbar.set_content(Some(&adw::StatusPage::builder().title("Hello GNOME").build()));

        let win = adw::ApplicationWindow::builder()
            .application(app)
            .title("Hello")
            .content(&toolbar)
            .build();
        win.present();
    });

    app.run()
}
```

Key differences:

- `use adw::prelude::*;` (or `gtk::prelude::*`) is mandatory: it brings the trait methods into scope.
- **Builders**: `Widget::builder().prop(value).build()`.
- Methods are `snake_case`, properties get typed setters. Optional values are `Option<&T>`.
- Signals: `connect_clicked`, `connect_activate`, `connect_notify_local(Some("name"), ...)`.

## 15.3 Closures and reference cycles: `glib::clone!`

Rust forbids capturing things carelessly. Widgets are cheap reference-counted handles (`Clone` clones the handle, not the widget):

```rust
let label = gtk::Label::new(None);
button.connect_clicked(glib::clone!(
    #[weak] label,
    move |_| { label.set_label("clicked"); }
));
```

`#[weak]` avoids reference cycles (the closure will not keep `label` alive; if it is gone the closure does nothing). Use `#[strong]` when you want to keep it alive. This is the Rust analogue of "disconnect signals / avoid leaks" from Chapter 3.9.

## 15.4 Subclassing (custom widgets, models, templates)

The pattern is two modules: an `imp` module (private implementation) and a public wrapper.

```rust
mod imp {
    use gtk::{glib, subclass::prelude::*, CompositeTemplate, TemplateChild};
    use adw::subclass::prelude::*;

    #[derive(Debug, Default, CompositeTemplate)]
    #[template(resource = "/io/github/you/PandaManager/window.ui")]
    pub struct PandaWindow {
        #[template_child]
        pub toast_overlay: TemplateChild<adw::ToastOverlay>,
    }

    #[glib::object_subclass]
    impl ObjectSubclass for PandaWindow {
        const NAME: &'static str = "PandaWindow";
        type Type = super::PandaWindow;
        type ParentType = adw::ApplicationWindow;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
            klass.bind_template_callbacks();
        }
        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    #[gtk::template_callbacks]
    impl PandaWindow {
        #[template_callback]
        fn on_rescan_clicked(&self, _button: &gtk::Button) {
            self.toast_overlay.add_toast(adw::Toast::new("Rescanning…"));
        }
    }

    impl ObjectImpl for PandaWindow {}
    impl WidgetImpl for PandaWindow {}
    impl WindowImpl for PandaWindow {}
    impl ApplicationWindowImpl for PandaWindow {}
    impl AdwApplicationWindowImpl for PandaWindow {}
}

glib::wrapper! {
    pub struct PandaWindow(ObjectSubclass<imp::PandaWindow>)
        @extends adw::ApplicationWindow, gtk::ApplicationWindow, gtk::Window, gtk::Widget,
        @implements gio::ActionGroup, gio::ActionMap, gtk::Accessible, gtk::Buildable,
                    gtk::ConstraintTarget, gtk::Native, gtk::Root, gtk::ShortcutManager;
}
```

Reading guide: `imp::X` holds fields (state); `impl ObjectImpl` etc. are the overridable "virtual functions" (our `vfunc_*`); `glib::wrapper!` is the public type. Builder's Rust template generates all of this; copy and adapt.

**Properties** via the `glib::Properties` derive macro:

```rust
#[derive(Properties, Default)]
#[properties(wrapper_type = super::Package)]
pub struct Package {
    #[property(get, set)] name: RefCell<String>,
    #[property(get, set)] size: Cell<u64>,
}
```

Interior mutability (`RefCell`, `Cell`) is used because GObject methods take `&self`.

## 15.5 Async and threads

The GTK main loop is single-threaded; GTK objects are **not `Send`** (cannot cross threads). Patterns:

```rust
// run an async block on the main loop
glib::spawn_future_local(async move {
    let out = run_command("flatpak", &["list"]).await;   // uses gio::Subprocess async, no thread
    label.set_label(&out);
});

// run blocking/CPU code on a thread pool, await the result back on the main loop
glib::spawn_future_local(async move {
    let result = gio::spawn_blocking(move || heavy_scan(path)).await;
    update_ui(result);
});
```

Rust apps can use real threads, `std::thread`, `tokio`, `async-channel` for passing results. Rule: **widgets only on the main thread**; send data (not widgets) between threads. Use `async_channel` + `spawn_future_local` to receive progress messages.

## 15.6 Projects, packaging

- Builder's "GNOME Application (Rust)" template: Cargo + Meson, GResource, Blueprint, Flatpak manifest.
- Flatpak builds are offline: use `flatpak-cargo-generator` (from the flatpak-builder-tools repo) to generate `cargo-sources.json` from `Cargo.lock`.
- Use `cargo clippy` and `cargo fmt`; commit `Cargo.lock` for applications.
- Layout idea for a large app: a workspace with a `core` crate (no GTK, pure logic, testable with `cargo test`) and an `app` crate (GTK UI). This is exactly the "engine without Gtk" idea of Chapter 10.

## 15.7 Reading Rust docs for GTK

- Types mirror C names: `gtk::Button`, `adw::ActionRow`.
- Look at a type's page: the **Implements** and **Trait** sections show where methods live (`ButtonExt`, `WidgetExt`). If a method seems missing you forgot `use gtk::prelude::*`.
- C `Since: 4.10` becomes a cargo feature `v4_10`.
- Real-world Rust GNOME apps to read: Fractal, Loupe, Authenticator, Snapshot (check repos for current state).

## 15.8 When Rust is not the answer

If your app is mostly "run commands and show lists" (like PandaManager), JS or Python is faster to write and fine to run. Reach for Rust when you need performance (parsing huge data), a shared library/daemon, or strong guarantees.

> **Remember:** import the prelude; builders for construction; `glib::clone!` with `#[weak]`; `imp` module + wrapper for subclasses; widgets stay on the main thread; Builder's Rust template is your cheat sheet.

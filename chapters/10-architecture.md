# 10. Application Architecture That Scales

A GNOME app of PandaManager's size goes wrong in predictable ways: logic mixed into widgets, UI freezing, state scattered. This chapter is the plan to avoid that.

## 10.1 Three layers

```
┌───────────────────────────────┐
│ UI layer      (src/ui)        │  widgets, pages, dialogs. Imports Gtk/Adw.
├───────────────────────────────┤
│ Model/State   (src/model)     │  GObject classes + Gio.ListStores the UI binds to.
├───────────────────────────────┤
│ Engine        (src/engine)    │  pure logic: run commands, parse output, scan, cache.
└───────────────────────────────┘     NO Gtk/Adw imports. Testable from plain gjs.
```

Rules:

1. Dependencies point **downward only**. The engine never knows the UI exists.
2. The engine returns **plain data** (objects/arrays) via Promises. A thin model layer wraps it in GObjects (`registerClass`) for lists.
3. UI code reacts to the model through **bindings and signals** and sends user intent to the engine via **actions or methods**.
4. Anything that touches the system (`dnf`, `git`, files) lives in the engine, so you can test it from the terminal.

## 10.2 Plugin ("source") pattern for scanners

PandaManager's package managers all expose the same interface:

```js
// src/engine/sources/flatpak.js
export const id = 'flatpak';
export const label = 'Flatpak';

export async function list() {
    const r = await run(['flatpak', 'list', '--app', '--columns=application,name,version,size']);
    if (!r.ok) throw new Error(r.stderr);
    return r.stdout.trim().split('\n').filter(Boolean).map(line => {
        const [appId, name, version, size] = line.split('\t');
        return {source: id, id: appId, name, version, sizeText: size};
    });
}
export async function uninstall(pkg) { /* ... */ }
```

```js
// src/engine/sources/index.js
import * as dnf from './dnf.js';
import * as flatpak from './flatpak.js';
export const sources = [dnf, flatpak];
```

```js
// aggregate
const lists = await Promise.allSettled(sources.map(s => s.list()));
```

Use `allSettled` so one broken source (e.g. `pipx` not installed) never breaks the others; show a per-source warning instead. Check a tool exists with `GLib.find_program_in_path('pipx')` before calling.

## 10.3 Model objects for the UI

```js
// src/model/package.js
export const PackageItem = GObject.registerClass({
    GTypeName: 'PandaPackageItem',
    Properties: {
        name: GObject.ParamSpec.string('name', '', '', GObject.ParamFlags.READWRITE, ''),
        source: GObject.ParamSpec.string('source', '', '', GObject.ParamFlags.READWRITE, ''),
        size: GObject.ParamSpec.double('size', '', '', GObject.ParamFlags.READWRITE, 0, Number.MAX_SAFE_INTEGER, 0),
    },
}, class PackageItem extends GObject.Object {});
```

The page owns a `Gio.ListStore({item_type: PackageItem})`, fills it from engine results and binds it to the view. Sorting/filtering uses `Gtk.SortListModel` / `Gtk.FilterListModel` (Chapter 4).

## 10.4 Persistence

| Data | Where | How |
|---|---|---|
| User preferences | GSettings | Chapter 8.4 |
| Cached scan results, indexes | `~/.local/share/<app>/*.json` or `~/.cache/<app>` | JSON via `Gio.File.replace_contents` (atomic) |
| Logs | `~/.local/state/<app>/` | append text |
| Secrets | libsecret (Secret Service) | `gi://Secret`; never plain text |

Cache pattern: **show cached data instantly, refresh in the background, update the list when done.** Store a `version` field in JSON so you can migrate the format later.

```js
const CACHE = GLib.build_filenamev([GLib.get_user_data_dir(), 'pandamanager', 'repos.json']);
export function loadCache() { try { return JSON.parse(readText(CACHE)); } catch { return null; } }
export function saveCache(data) { writeTextAtomic(CACHE, JSON.stringify({version: 1, savedAt: Date.now(), data})); }
```

If queries become relational (search across thousands of items with joins), switch to SQLite through the `sqlite3` CLI or libgda; do not adopt it before you need it.

## 10.5 Navigation and state

- One **window** with a split view; each section a **page class** with its own template.
- A page has three states: **loading**, **empty**, **ready** (and often **error**). Model them explicitly with a `Gtk.Stack` or `Adw.ViewStack` whose children are a spinner page, a `StatusPage`, and the content.
- Page lifecycle: load lazily the first time it is shown (`notify::visible-child` or `map` signal), refresh on demand with a button/shortcut, cancel on unmap.
- Shared app state (settings, scan roots) lives in a plain singleton module or on the `Application` object; pass what a page needs through constructor properties rather than reaching into globals.

## 10.6 Error handling you can live with

- Engine functions **throw** `Error` with a clear message; they do not show UI.
- The UI catches at the edge (signal handlers) and shows: a toast for transient errors, a `StatusPage`/banner for page-level errors, a dialog for blocking ones.
- Include the command and its stderr in error details (an expandable "Details" row) so you can debug on user machines.
- Distinguish **expected** failures (tool not installed, permission denied, cancelled) from **bugs**.

## 10.7 Safe destructive operations (design checklist)

For PandaManager-like cleanup features:

1. **Preview first**: compute exactly what would be removed and show it.
2. **Prefer reversible**: `Gio.File.trash()` before delete. Offer "Undo" toasts.
3. **Re-verify at execution time**: state may have changed since the scan (new commit, new file). Run the safety check again immediately before acting.
4. **Never follow symlinks** into deletes (`NOFOLLOW_SYMLINKS`).
5. **Refuse dangerous paths** (`/`, `$HOME`, anything outside configured roots).
6. **Log what was done** to a file the user can read.
7. **Privilege separation**: GUI never runs as root. For root actions use PackageKit or `pkexec` with a fixed, minimal command; never pass unsanitised user input.
8. **Dry-run flag** in the engine (`{dryRun: true}`) so you can test.

## 10.8 Testing the engine

```js
// scratch/test-git.js  (run: gjs -m scratch/test-git.js)
import {repoStatus} from '../src/engine/git.js';
const s = await repoStatus('/home/me/Projects/foo');
console.log(JSON.stringify(s, null, 2));
```

Top-level `await` works in GJS modules. Because the engine has no Gtk imports, you can also write small assertion scripts or use **Jasmine for GJS** (`jasmine-gjs`) if you want a framework. Keep a `scratch/` or `tests/` folder of runnable scripts as you go.

## 10.9 Worked example: git repo status

```js
// src/engine/git.js
import {run} from './run.js';

// Assumes run() accepts an `env` option (loop over it and call launcher.setenv(k, v, true)).
export async function repoStatus(path) {
    const [st, stash] = await Promise.all([
        run(['git', '-C', path, 'status', '--porcelain=v2', '--branch'], {env: {LC_ALL: 'C'}}),
        run(['git', '-C', path, 'stash', 'list']),
    ]);
    if (!st.ok) return {path, error: st.stderr.trim()};

    let branch = null, upstream = null, ahead = 0, behind = 0, dirty = 0, untracked = 0;
    for (const line of st.stdout.split('\n')) {
        if (line.startsWith('# branch.head ')) branch = line.slice(14);
        else if (line.startsWith('# branch.upstream ')) upstream = line.slice(18);
        else if (line.startsWith('# branch.ab ')) {
            const m = line.match(/\+(\d+) -(\d+)/); ahead = +m[1]; behind = +m[2];
        } else if (line.startsWith('?')) untracked++;
        else if (line[0] === '1' || line[0] === '2' || line[0] === 'u') dirty++;
    }
    const stashes = stash.stdout.split('\n').filter(Boolean).length;
    const safeToRemove = dirty === 0 && untracked === 0 && stashes === 0 && upstream !== null && ahead === 0;
    return {path, branch, upstream, ahead, behind, dirty, untracked, stashes, safeToRemove};
}
```

Edge cases to handle later: repos with **no upstream** (never "safe"), **other branches with unpushed commits** (`git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads`), submodules, worktrees, detached HEAD, bare repos.

> **Remember:** engine (no Gtk) → model (GObjects) → UI (templates); plugin interface for sources; `allSettled`; cache then refresh; destructive operations are previewed, re-verified, reversible, and logged.

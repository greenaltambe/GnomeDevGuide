# 9. Async Programming and the Main Loop

## 9.1 The one rule

> **Never block the main loop.** The UI redraws, handles clicks, and runs timers on one thread. A 2-second `load_contents()` on a slow disk, a synchronous `communicate_utf8()`, or a long `for` loop freezes the whole window ("App is not responding").

So: slow things are **asynchronous**. You start them, the loop keeps running, and you are called back when they finish.

## 9.2 Two styles of async in Gio

C-style (callback):

```js
file.load_contents_async(null, (f, res) => {
    const [contents] = f.load_contents_finish(res);
    ...
});
```

Every async function `foo_async` has a matching `foo_finish`. The callback calls `_finish` to get the result (or an exception).

Promise style, enabled with one line per function:

```js
Gio._promisify(Gio.File.prototype, 'load_contents_async', 'load_contents_finish');

const [contents] = await file.load_contents_async(null);
```

`Gio._promisify(prototype, 'x_async', 'x_finish')` rewrites the method so that when you do **not** pass a callback, it returns a Promise. Put these calls once at the top of the module that needs them (or in a shared `promisify.js` imported at startup). You will need them for:

```js
Gio._promisify(Gio.File.prototype, 'load_contents_async', 'load_contents_finish');
Gio._promisify(Gio.File.prototype, 'replace_contents_bytes_async', 'replace_contents_finish');
Gio._promisify(Gio.File.prototype, 'enumerate_children_async', 'enumerate_children_finish');
Gio._promisify(Gio.FileEnumerator.prototype, 'next_files_async', 'next_files_finish');
Gio._promisify(Gio.Subprocess.prototype, 'communicate_utf8_async', 'communicate_utf8_finish');
Gio._promisify(Gio.Subprocess.prototype, 'wait_async', 'wait_finish');
Gio._promisify(Gtk.FileDialog.prototype, 'select_folder', 'select_folder_finish');
Gio._promisify(Gtk.FileDialog.prototype, 'open', 'open_finish');
Gio._promisify(Adw.AlertDialog.prototype, 'choose', 'choose_finish');
```

Recent GJS already promisifies many Gtk/Adw async functions for you. If `await dialog.choose(...)` works without the line, skip it. Calling `_promisify` twice is harmless.

## 9.3 async/await patterns

```js
async function scanAll(roots) {
    const results = [];
    for (const root of roots)
        results.push(...await scanRoot(root));      // sequential
    return results;
}

const all = await Promise.all(roots.map(scanRoot)); // parallel
const settled = await Promise.allSettled(tasks);    // never throws; check .status
```

### Calling async from a signal handler

Signal handlers cannot be awaited. Use an async arrow and **catch errors**, because unhandled rejections are easy to miss:

```js
button.connect('clicked', async () => {
    button.sensitive = false;
    try {
        await this._rescan();
    } catch (e) {
        if (!e.matches?.(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED))
            this._showError(e);
    } finally {
        button.sensitive = true;
    }
});
```

### Fire and forget without losing errors

```js
function spawnTask(promise) {
    promise.catch(e => console.error(e));
}
```

## 9.4 Cancellation

Create a `Gio.Cancellable` per "job". Pass it into every async call. When the user leaves the page or presses Stop, call `cancel()`.

```js
this._cancellable?.cancel();
this._cancellable = new Gio.Cancellable();
const c = this._cancellable;

try {
    const out = await run(['du', '-sk', path], {cancellable: c});
} catch (e) {
    if (c.is_cancelled()) return;          // expected
    throw e;
}
```

Also guard against **stale results**: when an older task finishes after a newer one started, ignore it (compare a job id/token before writing to the UI).

## 9.5 Concurrency limits

Starting 500 `git status` processes at once melts a laptop. Use a small pool:

```js
export async function mapLimit(items, limit, fn) {
    const results = new Array(items.length);
    let next = 0;
    async function worker() {
        while (true) {
            const i = next++;
            if (i >= items.length) return;
            results[i] = await fn(items[i], i);
        }
    }
    await Promise.all(Array.from({length: Math.min(limit, items.length)}, worker));
    return results;
}

const statuses = await mapLimit(repos, 8, repo => gitStatus(repo));
```

Typical limits: 8 for processes, 4 for disk-heavy tasks (`du`).

## 9.6 Progressive UI updates

Do not wait for the entire scan before showing anything:

```js
async function scan() {
    store.remove_all();
    await mapLimit(repos, 8, async (repo) => {
        const status = await gitStatus(repo);
        store.append(new RepoItem(status));     // list grows as results arrive
    });
}
```

Show a spinner/progress bar while loading (`Adw.Spinner` or `Gtk.ProgressBar` with `fraction`), and update a "N of M" subtitle.

## 9.7 Threads?

GJS **does not support JavaScript threads** (no `Worker`). Options for CPU-heavy or blocking work:

1. Use async Gio APIs (usually enough).
2. Run an external helper as a **subprocess** (`du`, `find`, `git`, your own script) and read its output.
3. Break large JS loops into chunks yielding to the loop:

```js
const yieldToLoop = () => new Promise(r => GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => { r(); return GLib.SOURCE_REMOVE; }));
for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 200 === 0) await yieldToLoop();
}
```

4. Write a native helper in Rust/C/Python and call it as a subprocess or over D-Bus (a natural step when you outgrow JS).

(Python and Rust apps *can* use threads; see Chapters 14 and 15.)

## 9.8 Timeouts and retries

```js
function withTimeout(promise, ms) {
    return new Promise((resolve, reject) => {
        const id = GLib.timeout_add(GLib.PRIORITY_DEFAULT, ms, () => {
            reject(new Error('timeout')); return GLib.SOURCE_REMOVE;
        });
        promise.then(v => { GLib.Source.remove(id); resolve(v); },
                     e => { GLib.Source.remove(id); reject(e); });
    });
}
```

Prefer a `Cancellable` plus `proc.force_exit()` over merely abandoning a slow process.

## 9.9 Debugging async

- `console.log` at start and end of each step; log durations with `GLib.get_monotonic_time()` (microseconds).
- A frozen UI = something synchronous on the main thread. The Inspector or Sysprof will show it.
- Silent failure = a Promise rejected with nothing handling it. Wrap handlers as in 9.3.

> **Remember:** promisify, `await`, catch everything in handlers, Cancellable per job, limit concurrency, update the UI progressively, no JS threads (use subprocesses).

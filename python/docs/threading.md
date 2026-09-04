[← API reference](README.md)

# Threading

[`pane.run(builder)`](getting-started.md) builds the window on a dedicated
UI (STA) thread and blocks the calling thread until the window closes.
Build your widget tree inside `builder` - or inside a callback that's
already running on the UI thread (any `on_click`/`on_change`/etc. fires
there automatically).

To touch the UI later from another thread (a timer, a background task, an
API response), marshal back with `pane.invoke(fn)`:

```python
import threading

def build(window):
    label = pane.text("waiting...")
    window.Content = pane.stack(label, margin=20)

    def work():
        result = slow_computation()
        pane.invoke(lambda: setattr(label, "Text", result))

    threading.Thread(target=work, daemon=True).start()

pane.run(build)
```

`pane.invoke()` is safe to call from any thread, including the UI thread
itself (it just runs `fn()` directly in that case) - so code that might run
on either doesn't need to branch on `pane.is_ui_thread()` itself.

← [Events](events.md) · Next: [Value conversion](value-conversion.md) →

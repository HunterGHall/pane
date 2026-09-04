[← API reference](README.md)

# Getting started

```python
import pane

def build(window):
    window.Content = pane.stack(
        pane.text("Hello from Python", size="title", bold=True),
        pane.button("Click me", style="primary", on_click=lambda: print("clicked!")),
        spacing=12, margin=24,
    )

pane.run(build, title="My App")
```

`pane.run(builder, **kwargs)` builds and shows a window, then blocks the
calling thread until it's closed.

| Parameter | Default | |
|---|---|---|
| `builder` | required | `builder(window)` runs on a dedicated UI thread before the window is shown. Build your widget tree there and assign it to `window.Content`. |
| `title` | `"Pane App"` | Window title. |
| `width`, `height` | `1000`, `700` | Initial window size, in device-independent pixels. |
| `theme` | `"dark"` | `"dark"` or `"light"`. |
| `resizable` | `True` | `False` sets `ResizeMode.NoResize`. |

Only call `pane.button(...)`, `pane.stack(...)`, etc. inside `builder`, or
inside a callback that's running on the UI thread (an `on_click`, or a
function passed to `pane.invoke()`) - see [Threading](threading.md).

Other module-level functions:

| Function | |
|---|---|
| `pane.invoke(fn)` | Runs `fn` on the UI thread and returns its result, blocking the caller. Safe from any thread, including the UI thread itself. |
| `pane.close()` | Closes the running window. Safe to call from any thread. |
| `pane.current_window()` | Returns the running `Window` object, or `None`. |
| `pane.is_ui_thread()` | `True` if called from the UI thread. |

Next: [The window](window.md) →

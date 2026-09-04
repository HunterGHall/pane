# pane

Python bindings for [Pane](https://github.com/HunterGHall/pane) — a modern, minimalist
Windows UI engine built on WPF. Build real native Windows app UIs from Python:
buttons, checkboxes, sliders, text input, tabs, live light/dark theming and
accent-color switching, all with a single custom-chrome window.

The engine itself is C#/WPF; this package drives it in-process via
[pythonnet](https://pythonnet.github.io/), so widgets are the real native
controls, not a re-implementation.

**Windows only** (WPF has no cross-platform equivalent). Requires the free
[.NET 8 Desktop Runtime](https://dotnet.microsoft.com/download/dotnet/8.0) —
not the SDK, just the runtime.

## Install

```
pip install pane-ui
```

## Quick start

```python
import pane

def build(window):
    window.Content = pane.stack(
        pane.text("Hello from Python", size="title", bold=True),
        pane.button("Click me", style="primary", on_click=lambda: print("clicked!")),
        pane.checkbox("Enable notifications", checked=True),
        spacing=12,
        margin=24,
    )

pane.run(build, title="My App")
```

Run the full widget gallery from the source repo for a tour of everything
available: `python examples/gallery.py`.

## Documentation

**[Full API reference](docs/README.md)** - every widget, layout helper, the
chat panel, the music player, theming, events, and the threading model:

- [Getting started](docs/getting-started.md) - `pane.run()` and the builder pattern
- [The window](docs/window.md) - the real WPF `Window` object, fullscreen/state
- [Widgets](docs/widgets.md) - buttons, inputs, lists, menus, and every other control
- [Layout](docs/layout.md) - `stack`, `grid`, `card`, `sidebar`, `scroll`
- [Chat](docs/chat.md) - `chat_panel()`, the message-bubble widget
- [Music player](docs/music.md) - `music_player()`, the transport/seek/volume widget
- [Theming](docs/theming.md) - light/dark mode, accent colors
- [Events](docs/events.md) - the `on_*` callback convention
- [Threading](docs/threading.md) - `pane.invoke()` and background work
- [Value conversion](docs/value-conversion.md) - `to_thickness()`, `to_color()`

## License

MIT

# pane-ui API reference

Full reference for the `pane` Python package. For a quick start, see the
[top-level README](../README.md). Every function here returns (or operates
on) a real .NET/WPF object via [pythonnet](https://pythonnet.github.io/) -
not a Python-side abstraction - so anything not covered by this reference is
still reachable directly through the object's own WPF properties/methods.

- [Getting started](getting-started.md) - `pane.run()` and the builder pattern
- [The window](window.md) - the real WPF `Window` object, fullscreen/state
- [Widgets](widgets.md) - buttons, inputs, lists, menus, and every other control
- [Layout](layout.md) - `stack`, `grid`, `card`, `sidebar`, `scroll`
- [Chat](chat.md) - `chat_panel()`, the message-bubble widget
- [Music player](music.md) - `music_player()`, the transport/seek/volume widget
- [Theming](theming.md) - light/dark mode, accent colors
- [Events](events.md) - the `on_*` callback convention
- [Threading](threading.md) - `pane.invoke()` and background work
- [Value conversion](value-conversion.md) - `to_thickness()`, `to_color()`

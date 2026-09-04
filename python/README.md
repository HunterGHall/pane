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

## Widgets

`button`, `checkbox`, `radio_button`, `toggle_switch`, `text_box`,
`password_box`, `progress_bar`, `slider`, `combo_box`, `list_box`, `nav_list`,
`tab_control`, `expander`, `group_box`, `separator`, `text`, `color_swatch`,
`menu_bar`, `chat_panel`, plus `set_tooltip` / `set_context_menu` helpers.

`combo_box`, `list_box` and `nav_list` pass the *selected item itself* to
`on_change`/`on_select` (not its index) - read `.SelectedIndex` off the
returned control if you need that instead:

```python
pane.combo_box(["Newest first", "Oldest first"], on_change=lambda choice: print(choice))
```

`set_context_menu` and `menu_bar` share the same items format: a list of
`(label, on_click)` pairs, `(label, sub_items)` pairs for a nested submenu, or
`None` for a separator:

```python
pane.menu_bar([
    ("File", [("New", on_new), ("Open", on_open), None, ("Exit", on_exit)]),
    ("Edit", [("Cut", on_cut), ("Copy", on_copy), ("Paste", on_paste)]),
])
```

## Chat

`chat_panel()` is a scrollable, bubble-styled message list with an input
row - it's just the UI, with no idea what "AI" means:

```python
chat = pane.chat_panel(
    on_send=lambda text: f"you said: {text}",  # return a string for a quick
                                                # synchronous reply, or None
                                                # and call chat.add_message()
                                                # yourself later (e.g. from a
                                                # background thread via
                                                # pane.invoke(), for an LLM
                                                # call that takes real time)
    placeholder="Message...",
    welcome="Hi! What can I help with?",
)
window.Content = pane.stack(chat.control, margin=16)
```

See `examples/ai_chat.py` for a complete, working chat app wired up to
Claude via the [Anthropic SDK](https://pypi.org/project/anthropic/)
(`pip install anthropic`, set `ANTHROPIC_API_KEY`).

## Layout

`stack(*children, orientation=, spacing=, margin=)`,
`grid(children, rows=, columns=)`, `card(*children)`, `sidebar(*children)`,
`scroll(child)`.

## Theming

```python
pane.set_theme("light")        # or "dark"
pane.toggle_theme()
pane.set_accent("#4C82F7")     # hex string or (r, g, b) tuple
pane.reset_accent()
```

Every widget re-themes live, mid-run, no restart needed.

## Events

Callbacks adapt to whatever you write - zero args or one:

```python
pane.button("Save", on_click=lambda: print("saved"))
pane.slider(on_change=lambda value: print(value))
```

## Threading

`pane.run(builder)` builds the window on a dedicated UI thread and blocks
until it's closed. Build your widget tree inside `builder`. To update the UI
later from another thread (a timer, a background task), use
`pane.invoke(fn)` to marshal back onto the UI thread.

## License

MIT

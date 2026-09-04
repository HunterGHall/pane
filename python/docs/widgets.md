[← API reference](README.md)

# Widgets

Every widget function returns the real WPF control (e.g. `button()` returns
a `System.Windows.Controls.Button`) - store it in a variable if you need to
change it later (`btn.Content = "New label"`, `btn.IsEnabled = False`, ...).

Parameters named `width`, `height`, `margin`, `enabled` are handled by every
widget that has them the same way: `width`/`height` are numbers (device-
independent pixels), `margin` is anything
[`to_thickness()`](value-conversion.md) accepts, `enabled=False` disables
the control.

- [Buttons](#buttons)
- [Selection](#selection)
- [Text input](#text-input)
- [Progress & range](#progress--range)
- [Choices & lists](#choices--lists)
- [Layout & overlays](#layout--overlays)

## Buttons

```python
pane.button(label, *, style="secondary", on_click=None, width=None, height=None, margin=None, enabled=True)
```
`style`: `"secondary"` (default, implicit), `"primary"`, or `"ghost"`.
`on_click`: called with no arguments (or with any signature - see
[Events](events.md)) on click.

## Selection

```python
pane.checkbox(label, *, checked=False, on_change=None, width=None, margin=None, enabled=True)
```
`on_change`, if it takes an argument, receives the new `IsChecked` value
(`True`/`False`/`None` for indeterminate).

```python
pane.radio_button(label, group, *, checked=False, on_change=None, width=None, margin=None, enabled=True)
```
`group`: a string - radio buttons sharing the same `group` are mutually
exclusive. `on_change` fires (with `True`) when this button becomes checked.

```python
pane.toggle_switch(*, checked=False, on_change=None, margin=None, enabled=True)
```
`on_change`, if it takes an argument, receives the new boolean state.

## Text input

```python
pane.text_box(*, text="", placeholder="", on_change=None, width=None, margin=None, enabled=True)
```
`on_change`, if it takes an argument, receives the current text on every
keystroke.

```python
pane.password_box(*, on_change=None, width=None, margin=None, enabled=True)
```
No placeholder support (native `PasswordBox` limitation). `on_change`, if it
takes an argument, receives the current password text.

## Progress & range

```python
pane.progress_bar(*, value=0, minimum=0, maximum=100, indeterminate=False, width=None, margin=None)
pane.slider(*, value=0, minimum=0, maximum=100, on_change=None, width=None, margin=None, enabled=True)
```
`slider`'s `on_change`, if it takes an argument, receives the new numeric
value (a `float`).

## Choices & lists

```python
pane.combo_box(items, *, selected_index=0, on_change=None, width=None, margin=None, enabled=True)
pane.list_box(items, *, selected_index=0, on_select=None, width=None, height=None, margin=None, enabled=True)
pane.nav_list(items, *, selected_index=0, on_select=None)
```
`items`: any iterable; each item is rendered via `str(item)`. **The
callback receives the selected item itself**, not its index - read
`control.SelectedIndex` off the returned control if you need the index:

```python
pane.combo_box(["Newest first", "Oldest first"], on_change=lambda choice: print(choice))
```

`nav_list` is styled as a sidebar navigation list (`Pane.NavigationList`) -
see [`sidebar()`](layout.md#sidebar) for the container it's meant to sit in.

```python
pane.tab_control(tabs, *, width=None, height=None, margin=None)
```
`tabs`: a `dict` of `{header: content_element}`, or a list of `(header,
content)` pairs.

## Layout & overlays

```python
pane.expander(header, content, *, expanded=False, margin=None)
pane.group_box(header, content, *, margin=None)
pane.separator(*, margin=None)
```

```python
pane.text(content, *, size="body", bold=False, color="primary", wrap=False, margin=None)
```
`size`: `"caption"`, `"body"` (default), `"subtitle"`, `"title"`,
`"title-large"`. `color`: `"primary"` (default), `"secondary"`,
`"disabled"`, `"on-accent"` (white-on-accent, for text inside an
accent-colored surface like a `color_swatch` or a user chat bubble).
`content` is converted with `str()`. Re-themes live, same as every other
widget.

```python
pane.color_swatch(color, *, on_click=None, margin=None)
```
A small round, clickable swatch. `color`: anything
[`to_color()`](value-conversion.md) accepts. `on_click`, if it takes an
argument, receives that same `color` value back - handy for building an
accent-color picker:

```python
pane.color_swatch("#4C82F7", on_click=lambda c: pane.set_accent(c))
```

```python
pane.set_tooltip(element, tooltip_text)
```
Sets `element.ToolTip` and returns `element` (so it composes inline:
`pane.set_tooltip(pane.button("Hi"), "A tooltip")`).

```python
pane.set_context_menu(element, items)
pane.menu_bar(items)
```
`set_context_menu` attaches a right-click menu to `element`; `menu_bar`
builds a standalone top menu bar (`System.Windows.Controls.Menu`). Both
share the same `items` format - a list of:

- `(label, on_click)` - a leaf menu item,
- `(label, sub_items)` - `sub_items` a list in this same format, for a
  nested submenu,
- `None` - a separator.

```python
pane.menu_bar([
    ("File", [("New", on_new), ("Open", on_open), None, ("Exit", pane.close)]),
    ("Edit", [("Cut", on_cut), ("Copy", on_copy), ("Paste", on_paste)]),
])
```

← [The window](window.md) · Next: [Layout](layout.md) →

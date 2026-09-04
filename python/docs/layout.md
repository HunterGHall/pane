[← API reference](README.md)

# Layout

Layout functions compose widgets into containers; all return the real WPF
panel/container element.

```python
pane.stack(*children, orientation="vertical", spacing=0, margin=None)
```
A `StackPanel`. `orientation`: `"vertical"` (default) or `"horizontal"`.
`spacing` inserts that much margin between each child (not before the
first).

```python
pane.grid(children, *, rows=None, columns=None, margin=None)
```
A `Grid`. `children`: a list of `(row, col, widget)` or `(row, col, widget,
row_span, col_span)` tuples. `rows`/`columns`: lists of `"auto"`, `"*"`,
`"2*"` (a weighted star size), or a bare number (pixels) - e.g. `rows=["auto",
"*"]` for a header that sizes to its content plus a body that fills the
rest. Default is a single `"auto"` row/column if omitted.

```python
pane.card(*children, padding=20, spacing=12, orientation="vertical", margin=None)
```
A `Border` styled as an elevated surface (`Pane.Card`), containing a
`stack()` of `children`.

## `sidebar()`

```python
pane.sidebar(*children, width=240)
```
A `Border` styled as a sidebar shell (`Pane.Sidebar`) containing a
`DockPanel` of `children` - put a [`nav_list()`](widgets.md#choices--lists)
and other content inside.

```python
pane.scroll(child, *, padding=None)
```
A `ScrollViewer` wrapping a single `child`.

## Gotcha: `ScrollViewer` inside `stack()` won't scroll

A `StackPanel` gives its children unconstrained height, so a `ScrollViewer`
just grows to fit its content instead of clipping/scrolling it. Use
`grid()` with an `"auto"` / `"*"` row split instead when you need a
fixed-size header (or menu bar) above a scrolling body:

```python
window.Content = pane.grid([(0, 0, header), (1, 0, pane.scroll(body))], rows=["auto", "*"])
```

← [Widgets](widgets.md) · Next: [Chat](chat.md) →

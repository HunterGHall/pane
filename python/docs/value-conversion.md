[← API reference](README.md)

# Value conversion

Internal helpers, also useful directly if you're constructing WPF objects
by hand:

```python
from pane._convert import to_thickness, to_color
```

`to_thickness(value)` - accepted by every `margin=`/`padding=` parameter:
- a `System.Windows.Thickness` - passed through,
- a number - uniform on all four sides,
- a 2-tuple `(horizontal, vertical)`,
- a 4-tuple `(left, top, right, bottom)`.

`to_color(value)` - accepted by [`set_accent()`](theming.md),
[`color_swatch()`](widgets.md#layout--overlays):
- a `System.Windows.Media.Color` - passed through,
- a hex string, `"#RRGGBB"` or `"#AARRGGBB"`,
- a 3-tuple `(r, g, b)` or 4-tuple `(a, r, g, b)`.

← [Threading](threading.md) · [Back to API reference](README.md)

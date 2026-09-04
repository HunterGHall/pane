[← API reference](README.md)

# Theming

```python
pane.set_theme(theme)      # "dark" or "light"
pane.toggle_theme()
pane.current_theme()       # -> "dark" or "light"
pane.set_accent(color)     # anything to_color() accepts
pane.reset_accent()        # back to the theme's default accent
```

Every widget re-themes live, mid-run - no restart needed.
[`pane.run(..., theme="light")`](getting-started.md) sets the starting
theme.

← [Music player](music.md) · Next: [Events](events.md) →

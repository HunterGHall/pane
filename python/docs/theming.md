[← API reference](README.md)

# Theming

```python
pane.set_theme(theme)      # "dark", "light", or "system"
pane.toggle_theme()
pane.current_theme()       # -> "dark" or "light" (resolved - never "system")
pane.theme_mode()          # -> "dark", "light", or "system" (what you last asked for)
pane.on_theme_change(fn)   # fn(theme) runs on every switch, live ones included
pane.set_accent(color)     # anything to_color() accepts
pane.reset_accent()        # back to the theme's default accent
```

Every widget re-themes live, mid-run - no restart needed.
[`pane.run(..., theme="light")`](getting-started.md) sets the starting
theme.

## Following the system theme

```python
pane.set_theme("system")
```

Resolves to whatever Windows' light/dark "choose your color" setting
currently is, and keeps tracking it live - if the user flips it in Windows
Settings while your app is open, Pane re-themes immediately, no restart or
polling required. `pane.current_theme()` always tells you what that resolved
to; `pane.theme_mode()` tells you it's `"system"` rather than the resolved
value. Calling `set_theme("dark")`/`set_theme("light")` or `toggle_theme()`
later opts back out of following the system, same as most apps' "use system
setting" toggle being overridden by an explicit choice.

```python
unsubscribe = pane.on_theme_change(lambda theme: print("now", theme))
# ...
unsubscribe()  # stop listening
```

`on_theme_change` fires for that live system switch too, not just explicit
`set_theme()`/`toggle_theme()` calls - use it to keep anything you draw
yourself (a canvas, a loaded image) in sync with the theme.

## Custom colors

`set_accent` only changes the accent; `set_custom_theme` can override any
other slot in the palette too, on top of whichever of "dark"/"light"/"system"
is currently showing:

```python
pane.set_custom_theme(
    surface="#20242B",
    border_default="#343A46",
    accent="#4C82F7",     # equivalent to a separate set_accent() call
)
```

Every parameter is optional and accepts anything `to_color()` does; anything
you don't pass keeps the current theme's default for that slot. The full set:

| Parameter | Default palette slot |
|---|---|
| `window` | window background |
| `surface` | card/panel background |
| `surface_alt` | alternate panel background (e.g. striping) |
| `elevated` | popup/menu/tooltip background |
| `border_default`, `border_subtle`, `border_strong` | borders and dividers |
| `text_primary`, `text_secondary`, `text_disabled`, `text_on_accent` | text colors |
| `accent` | accent + its derived hover/pressed/subtle shades |
| `state_hover`, `state_pressed`, `state_disabled_background` | interaction-state overlays |
| `success`, `warning`, `danger` | semantic colors |

A custom theme persists across `set_theme()` calls - including a live
"system" switch - until `pane.reset_custom_theme()` drops back to the
current theme's defaults. (`reset_custom_theme()` doesn't touch a separately
set accent; call `reset_accent()` too if you want that reset as well.)

← [Playlist](playlist.md) · Next: [Events](events.md) →

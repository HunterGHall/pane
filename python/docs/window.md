[← API reference](README.md)

# The window

`window` (the argument `builder` receives) is a real WPF `Window`
(`Pane.PaneWindow`, a `System.Windows.Window` subclass) - every property and
method on it is available directly, not just `window.Content`. Common ones:

```python
from System.Windows import WindowState, ResizeMode

def build(window):
    window.WindowState = WindowState.Maximized   # start maximized/fullscreen
    window.Title = "Renamed"
    window.MinWidth = 400
    window.MinHeight = 300
    window.Topmost = True                         # always-on-top
    # window.Icon = ...                            # a BitmapImage, if you want one
```

`WindowState` has three values: `Normal`, `Minimized`, `Maximized` - there's
no separate "fullscreen" mode; `Maximized` on Pane's borderless chrome *is*
fullscreen (it fills the monitor's work area, respecting the taskbar).

Import types you need directly from their `System.*` namespace, same as
`WindowState`/`ResizeMode` above - `pane` only wraps the things listed in
this reference, everything else in WPF is one `from System.Windows... import
...` away.

← [Getting started](getting-started.md) · Next: [Widgets](widgets.md) →

[← API reference](README.md)

# Events

Every `on_*` callback adapts to whatever signature you write - zero
arguments, or one:

```python
pane.button("Save", on_click=lambda: print("saved"))
pane.slider(on_change=lambda value: print(value))
```

Internally this is arity-based: a callback that takes 0 positional
parameters is called with none; anything else is called with exactly one
(the widget's associated value - see each widget's own entry in
[Widgets](widgets.md) for what that value is).

← [Theming](theming.md) · Next: [Threading](threading.md) →

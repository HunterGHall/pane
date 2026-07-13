"""Internal: arity-aware callback wiring so `on_click=lambda: ...` and
`on_click=lambda value: ...` both work without the caller having to match a
specific .NET event-handler signature."""

import inspect


def arity(fn):
    try:
        sig = inspect.signature(fn)
        params = [
            p
            for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        return len(params)
    except (TypeError, ValueError):
        return 1


def make_handler(callback, value_fn):
    """Returns a (sender, args) -> None .NET-event-shaped handler that calls
    `callback()` if it takes no arguments, or `callback(value_fn())` otherwise."""
    n = arity(callback)

    def handler(sender, args):
        if n == 0:
            callback()
        else:
            callback(value_fn())

    return handler

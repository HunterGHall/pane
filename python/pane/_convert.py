"""Internal: Python <-> .NET value conversion helpers shared by widgets and layout."""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import Thickness  # noqa: E402
from System.Windows.Media import Color  # noqa: E402


def to_thickness(value):
    if isinstance(value, Thickness):
        return value
    if isinstance(value, (int, float)):
        return Thickness(value)
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            h, v = value
            return Thickness(h, v, h, v)
        if len(value) == 4:
            return Thickness(*value)
    raise ValueError(f"Invalid margin/padding value: {value!r} (expected a number, or a 2/4-tuple)")


def to_color(value):
    if isinstance(value, Color):
        return value
    if isinstance(value, str):
        s = value.lstrip("#")
        if len(s) == 6:
            r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            return Color.FromRgb(r, g, b)
        if len(s) == 8:
            a, r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16)
            return Color.FromArgb(a, r, g, b)
        raise ValueError(f"Invalid hex color: {value!r} (expected '#RRGGBB' or '#AARRGGBB')")
    if isinstance(value, (tuple, list)):
        if len(value) == 3:
            return Color.FromRgb(*value)
        if len(value) == 4:
            return Color.FromArgb(*value)
    raise ValueError(f"Invalid color value: {value!r} (expected a hex string or an (r,g,b) / (a,r,g,b) tuple)")

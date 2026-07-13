"""Theme and accent-color control - thin wrappers over Pane.ThemeManager."""

from . import _bootstrap

_bootstrap.ensure_loaded()

from Pane import PaneTheme, ThemeManager  # noqa: E402

from ._convert import to_color  # noqa: E402


def set_theme(theme):
    """theme: "dark" or "light"."""
    ThemeManager.SetTheme(PaneTheme.Dark if theme == "dark" else PaneTheme.Light)


def toggle_theme():
    ThemeManager.ToggleTheme()


def current_theme():
    return "dark" if ThemeManager.CurrentTheme == PaneTheme.Dark else "light"


def set_accent(color):
    """color: a "#RRGGBB" / "#AARRGGBB" hex string, or an (r,g,b) / (a,r,g,b) tuple."""
    ThemeManager.SetAccentColor(to_color(color))


def reset_accent():
    ThemeManager.ResetAccentColor()

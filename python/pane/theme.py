"""Theme, accent-color, and custom-palette control - thin wrappers over Pane.ThemeManager."""

from . import _bootstrap

_bootstrap.ensure_loaded()

from Pane import PaneTheme, PaneThemeColors, PaneThemeMode, ThemeManager  # noqa: E402

from ._convert import to_color  # noqa: E402
from ._events import make_handler  # noqa: E402

_MODES = {"dark": PaneThemeMode.Dark, "light": PaneThemeMode.Light, "system": PaneThemeMode.System}


def set_theme(theme):
    """theme: "dark", "light", or "system" - "system" follows the Windows
    light/dark setting live, including switching again automatically if the
    user changes it while your app is running. See on_theme_change() to react
    to that (or to an explicit "dark"/"light" switch) yourself."""
    ThemeManager.SetThemeMode(_MODES[theme])


def toggle_theme():
    """Flips between "dark" and "light". Like set_theme("dark"/"light"), this
    opts out of "system" mode if it was active."""
    ThemeManager.ToggleTheme()


def current_theme():
    """The resolved theme actually showing right now: "dark" or "light" -
    even when theme_mode() is "system"."""
    return "dark" if ThemeManager.CurrentTheme == PaneTheme.Dark else "light"


def theme_mode():
    """What was last passed to set_theme(): "dark", "light", or "system".
    Unlike current_theme(), this tells you whether you're following the OS
    setting rather than what it currently resolves to."""
    mode = ThemeManager.Mode
    if mode == PaneThemeMode.System:
        return "system"
    return "dark" if mode == PaneThemeMode.Dark else "light"


def on_theme_change(callback):
    """Registers callback to run every time the resolved theme changes - an
    explicit set_theme()/toggle_theme() call, or (in "system" mode) the
    Windows setting flipping live. callback(theme), if it takes an argument,
    receives the new "dark"/"light" value (same as current_theme()).

    Returns a function that unsubscribes callback when called."""
    handler = make_handler(callback, current_theme)
    ThemeManager.ThemeChanged += handler

    def unsubscribe():
        ThemeManager.ThemeChanged -= handler

    return unsubscribe


def set_accent(color):
    """color: a "#RRGGBB" / "#AARRGGBB" hex string, or an (r,g,b) / (a,r,g,b) tuple."""
    ThemeManager.SetAccentColor(to_color(color))


def reset_accent():
    ThemeManager.ResetAccentColor()


def set_custom_theme(
    *,
    window=None,
    surface=None,
    surface_alt=None,
    elevated=None,
    border_default=None,
    border_subtle=None,
    border_strong=None,
    text_primary=None,
    text_secondary=None,
    text_disabled=None,
    text_on_accent=None,
    accent=None,
    state_hover=None,
    state_pressed=None,
    state_disabled_background=None,
    success=None,
    warning=None,
    danger=None,
):
    """Overrides any subset of Pane's palette on top of the current light/dark
    theme - pass only the slots you want to change; everything else (None)
    keeps that theme's default. Each color: anything to_color() accepts.

    `accent` is a convenience for also calling set_accent() with the same
    value. Persists across set_theme() calls, including live "system" mode
    switches, until reset_custom_theme()."""
    colors = PaneThemeColors()
    overrides = {
        "Window": window,
        "Surface": surface,
        "SurfaceAlt": surface_alt,
        "Elevated": elevated,
        "BorderDefault": border_default,
        "BorderSubtle": border_subtle,
        "BorderStrong": border_strong,
        "TextPrimary": text_primary,
        "TextSecondary": text_secondary,
        "TextDisabled": text_disabled,
        "TextOnAccent": text_on_accent,
        "Accent": accent,
        "StateHover": state_hover,
        "StatePressed": state_pressed,
        "StateDisabledBackground": state_disabled_background,
        "Success": success,
        "Warning": warning,
        "Danger": danger,
    }
    for attr, value in overrides.items():
        if value is not None:
            setattr(colors, attr, to_color(value))
    ThemeManager.SetCustomTheme(colors)


def reset_custom_theme():
    """Drops back to the current theme's default palette. Leaves a
    separately-set accent untouched - call reset_accent() too if you want
    that back to the theme default as well."""
    ThemeManager.ResetCustomTheme()

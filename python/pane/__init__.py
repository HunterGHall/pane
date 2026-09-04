"""
pane - Python bindings for the Pane WPF UI engine.

Builds real Pane-styled WPF windows and widgets from Python, in-process, via
pythonnet. The engine itself (Pane.dll, the XAML control styles) is plain
C#/WPF and untouched by this package - this is a thin, Pythonic layer that
creates and drives the same native controls the WPF gallery app uses.

    import pane

    def build(window):
        window.Content = pane.stack(
            pane.text("Hello from Python", size="title"),
            pane.button("Click me", style="primary", on_click=lambda: print("clicked")),
            spacing=12, margin=24,
        )

    pane.run(build, title="My App")
"""

from .app import close, current_window, invoke, is_ui_thread, run
from .layout import card, grid, scroll, sidebar, stack
from .theme import current_theme, reset_accent, set_accent, set_theme, toggle_theme
from .widgets import (
    button,
    checkbox,
    color_swatch,
    combo_box,
    expander,
    group_box,
    list_box,
    menu_bar,
    nav_list,
    password_box,
    progress_bar,
    radio_button,
    separator,
    set_context_menu,
    set_tooltip,
    slider,
    tab_control,
    text,
    text_box,
    toggle_switch,
)

__all__ = [
    "run",
    "invoke",
    "close",
    "is_ui_thread",
    "current_window",
    "set_theme",
    "toggle_theme",
    "current_theme",
    "set_accent",
    "reset_accent",
    "button",
    "checkbox",
    "radio_button",
    "toggle_switch",
    "text_box",
    "password_box",
    "progress_bar",
    "slider",
    "combo_box",
    "list_box",
    "nav_list",
    "tab_control",
    "expander",
    "group_box",
    "separator",
    "text",
    "set_tooltip",
    "set_context_menu",
    "menu_bar",
    "color_swatch",
    "stack",
    "grid",
    "card",
    "sidebar",
    "scroll",
]

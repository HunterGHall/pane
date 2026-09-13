"""
A Python port of the Pane widget gallery - proves out the whole pythonnet
bridge (theming, layout, every widget type, and event callbacks) end to end.

Run from the python/ directory: python examples/gallery.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pane


def build(window):
    log = pane.text("Click something to see it logged here.", color="secondary")

    def show(message):
        log.Text = message

    buttons_section = pane.card(
        pane.text("Buttons", size="subtitle", bold=True),
        pane.stack(
            pane.button("Secondary", on_click=lambda: show("Secondary clicked")),
            pane.button("Primary", style="primary", on_click=lambda: show("Primary clicked")),
            pane.button("Ghost", style="ghost", on_click=lambda: show("Ghost clicked")),
            pane.button("Disabled", enabled=False),
            orientation="horizontal",
            spacing=10,
            margin=(0, 10, 0, 0),
        ),
    )

    selection_section = pane.card(
        pane.text("Selection", size="subtitle", bold=True),
        pane.stack(
            pane.checkbox("Send weekly summary", checked=True, on_change=lambda v: show(f"Checkbox -> {v}")),
            pane.toggle_switch(checked=False, on_change=lambda v: show(f"Toggle -> {v}")),
            spacing=10,
            margin=(0, 10, 0, 0),
        ),
    )

    text_section = pane.card(
        pane.text("Text input", size="subtitle", bold=True),
        pane.stack(
            pane.text_box(placeholder="Full name", width=280, on_change=lambda v: show(f"Name -> {v!r}")),
            pane.password_box(width=280, on_change=lambda v: show(f"Password length -> {len(v)}")),
            spacing=10,
            margin=(0, 10, 0, 0),
        ),
    )

    progress_section = pane.card(
        pane.text("Progress & sliders", size="subtitle", bold=True),
        pane.stack(
            pane.progress_bar(value=62, width=320),
            pane.slider(value=40, width=320, on_change=lambda v: show(f"Slider -> {v:.0f}")),
            spacing=16,
            margin=(0, 10, 0, 0),
        ),
    )

    choices_section = pane.card(
        pane.text("Choices & lists", size="subtitle", bold=True),
        pane.stack(
            pane.combo_box(["Newest first", "Oldest first", "Alphabetical"], on_change=lambda choice: show(f"Combo -> {choice}")),
            pane.list_box(["Inbox", "Drafts", "Sent", "Archive"], height=110, on_select=lambda item: show(f"List -> {item}")),
            spacing=10,
            margin=(0, 10, 0, 0),
        ),
    )

    # A no-network echo bot - chat_panel() itself doesn't know what "AI" is,
    # it just gives you the widget. See examples/chat_app.py for the same
    # widget with the recommended async-reply (background thread +
    # pane.invoke()) pattern, ready for you to wire up a real backend.
    chat = pane.chat_panel(
        on_send=lambda message: f"echo: {message}",
        welcome="Hi! I just echo whatever you type - see chat_app.py for the async-reply template.",
        height=220,
    )
    chat_section = pane.card(
        pane.text("Chat", size="subtitle", bold=True),
        pane.stack(chat.control, margin=(0, 10, 0, 0)),
    )

    overlays_section = pane.card(
        pane.text("Layout & overlays", size="subtitle", bold=True),
        pane.stack(
            pane.expander("More details", pane.text("Expanded content built from Python.", color="secondary", wrap=True)),
            pane.group_box("Grouped settings", pane.checkbox("Allow desktop notifications")),
            pane.separator(),
            pane.set_tooltip(pane.button("Hover for tooltip"), "This tooltip was set from Python."),
            margin=(0, 10, 0, 0),
        ),
    )

    # Guards against the toggle_switch's own on_change re-entering set_theme() while
    # sync_theme_toggle() is only reflecting a live "system" switch, not a click.
    syncing_theme_toggle = False

    def on_theme_toggle_change(is_dark):
        nonlocal syncing_theme_toggle
        if syncing_theme_toggle:
            return
        pane.set_theme("dark" if is_dark else "light")

    theme_toggle = pane.toggle_switch(checked=True, on_change=on_theme_toggle_change)

    def on_follow_system_change(following):
        theme_toggle.IsEnabled = not following
        pane.set_theme("system" if following else ("dark" if theme_toggle.IsChecked else "light"))

    def sync_theme_toggle(theme):
        nonlocal syncing_theme_toggle
        syncing_theme_toggle = True
        theme_toggle.IsChecked = theme == "dark"
        syncing_theme_toggle = False

    pane.on_theme_change(sync_theme_toggle)

    accent_row = pane.stack(
        pane.color_swatch("#D97757", on_click=lambda color: pane.set_accent(color)),
        pane.color_swatch("#4C82F7", on_click=lambda color: pane.set_accent(color)),
        pane.color_swatch("#4CAF6D", on_click=lambda color: pane.set_accent(color)),
        pane.button("Reset", style="ghost", on_click=pane.reset_accent),
        theme_toggle,
        pane.checkbox("Follow system theme", on_change=on_follow_system_change),
        orientation="horizontal",
        spacing=10,
    )

    menu = pane.menu_bar([
        ("File", [("New", lambda: show("File > New")), ("Open", lambda: show("File > Open")), None, ("Exit", pane.close)]),
        ("Edit", [("Cut", lambda: show("Edit > Cut")), ("Copy", lambda: show("Edit > Copy")), ("Paste", lambda: show("Edit > Paste"))]),
        ("Help", [("About", lambda: show("A Python-built Pane app."))]),
    ])

    body = pane.scroll(
        pane.stack(
            pane.text("Pane widget gallery (built from Python)", size="title-large", bold=True),
            log,
            accent_row,
            buttons_section,
            selection_section,
            text_section,
            progress_section,
            choices_section,
            chat_section,
            overlays_section,
            spacing=20,
            margin=32,
        )
    )

    # A plain stack would give the ScrollViewer unconstrained height and it
    # would never scroll - grid's "auto" / "*" rows size the menu to its
    # content and let the body fill (and clip/scroll within) what's left.
    window.Content = pane.grid([(0, 0, menu), (1, 0, body)], rows=["auto", "*"])


if __name__ == "__main__":
    pane.run(build, title="Pane - Python gallery", width=760, height=820)

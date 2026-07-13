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
            pane.combo_box(["Newest first", "Oldest first", "Alphabetical"], on_change=lambda i: show(f"Combo -> index {i}")),
            pane.list_box(["Inbox", "Drafts", "Sent", "Archive"], height=110, on_select=lambda i: show(f"List -> index {i}")),
            spacing=10,
            margin=(0, 10, 0, 0),
        ),
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

    accent_row = pane.stack(
        pane.button("Terracotta", on_click=lambda: pane.set_accent("#D97757")),
        pane.button("Blue", on_click=lambda: pane.set_accent("#4C82F7")),
        pane.button("Green", on_click=lambda: pane.set_accent("#4CAF6D")),
        pane.button("Reset", style="ghost", on_click=pane.reset_accent),
        pane.toggle_switch(checked=True, on_change=lambda v: pane.set_theme("dark" if v else "light")),
        orientation="horizontal",
        spacing=10,
    )

    window.Content = pane.scroll(
        pane.stack(
            pane.text("Pane widget gallery (built from Python)", size="title-large", bold=True),
            log,
            accent_row,
            buttons_section,
            selection_section,
            text_section,
            progress_section,
            choices_section,
            overlays_section,
            spacing=20,
            margin=32,
        )
    )


if __name__ == "__main__":
    pane.run(build, title="Pane - Python gallery", width=760, height=820)

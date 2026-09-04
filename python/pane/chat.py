"""A scrollable chat message list + input row, styled as chat bubbles
(Pane.ChatBubble.User / Pane.ChatBubble.Assistant).

This module only builds the widget - it has no idea what "AI" means and
makes no network calls. You supply that as an on_send callback; see
examples/chat_app.py for a runnable template with a placeholder callback
marking where a real backend would plug in.
"""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import Thickness  # noqa: E402
from System.Windows.Input import Key  # noqa: E402

from ._events import make_handler  # noqa: E402
from .layout import grid  # noqa: E402
from .widgets import _apply_common, _find_style, text  # noqa: E402

_BUBBLE_STYLES = {
    "user": ("Pane.ChatBubble.User", "on-accent"),
    "assistant": ("Pane.ChatBubble.Assistant", "primary"),
}


class ChatPanel:
    """Returned by chat_panel(). `.control` is the WPF element to add to
    your layout. Build messages with `.add_message(role, content)` - role is
    "user" or "assistant" - which appends a bubble and scrolls it into view.

    Safe to call from a background thread only via pane.invoke(); like every
    other Pane/WPF UI mutation, .add_message() itself must run on the UI
    thread.
    """

    def __init__(self, control, message_stack, scroll_viewer):
        self.control = control
        self._message_stack = message_stack
        self._scroll = scroll_viewer

    def add_message(self, role, content):
        from System.Windows.Controls import Border

        style_key, text_color = _BUBBLE_STYLES.get(role, _BUBBLE_STYLES["assistant"])

        bubble = Border()
        bubble.Style = _find_style(style_key)
        bubble.Child = text(content, wrap=True, color=text_color)
        bubble.Margin = Thickness(0, 0, 0, 10)

        self._message_stack.Children.Add(bubble)
        self._scroll.ScrollToBottom()

    def clear(self):
        self._message_stack.Children.Clear()


def chat_panel(*, on_send=None, placeholder="Message...", welcome=None, width=None, height=None, margin=None):
    """A scrollable message list (styled as chat bubbles) with a text entry
    row beneath it - Enter or the Send button both fire on_send.

    on_send(text), if given, is called with the user's message immediately
    after it's added as a user bubble. If it *returns* a string, that's
    appended as an assistant bubble right away - handy for a quick
    synchronous responder (an echo bot, a local function). For anything
    that takes real time (an HTTP call to an LLM), do that on a background
    thread instead and call the returned ChatPanel's
    `.add_message("assistant", reply)` yourself via pane.invoke() once the
    reply is ready, so the window doesn't freeze - see examples/chat_app.py.

    welcome, if given, is added as an initial assistant message before the
    panel is returned.
    """
    from System.Windows.Controls import Button, ScrollBarVisibility, ScrollViewer, StackPanel, TextBox
    from Pane.Controls import PaneAssist

    message_stack = StackPanel()

    scroll = ScrollViewer()
    scroll.Content = message_stack
    scroll.Padding = Thickness(4, 4, 4, 4)
    scroll.HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled

    panel = ChatPanel(None, message_stack, scroll)

    input_box = TextBox()
    input_box.Margin = Thickness(0, 0, 8, 0)
    if placeholder:
        PaneAssist.SetPlaceholder(input_box, placeholder)

    send_button = Button()
    send_button.Content = "Send"
    send_button.Style = _find_style("Pane.Button.Primary")

    def do_send():
        message = input_box.Text.strip()
        if not message:
            return
        input_box.Text = ""
        panel.add_message("user", message)
        if on_send:
            reply = on_send(message)
            if reply:
                panel.add_message("assistant", reply)

    send_button.Click += make_handler(do_send, lambda: None)

    def on_key_down(sender, args):
        if args.Key == Key.Return:
            do_send()

    input_box.KeyDown += on_key_down

    input_row = grid([(0, 0, input_box), (0, 1, send_button)], columns=["*", "auto"])
    root = grid([(0, 0, scroll), (1, 0, input_row)], rows=["*", "auto"])

    panel.control = root
    _apply_common(root, width=width, height=height, margin=margin)

    if welcome:
        panel.add_message("assistant", welcome)

    return panel

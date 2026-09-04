"""
A template chat app built on pane.chat_panel() - the widget, the input
handling, and the recommended async-reply pattern, with NO backend wired in.

pane.chat_panel() has no idea what "AI" is and makes no network calls - it's
just a scrollable, bubble-styled message list + input row (see pane/chat.py).
get_reply() below is a stand-in: swap its body for a call to whatever you
want - an LLM API, a local model, a script, anything that takes a string and
returns one.

Run it as-is (no API key, no extra dependencies) to see the widget and the
threading pattern working: python examples/chat_app.py
"""

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pane


def get_reply(user_message):
    """Replace this with a real call to your backend of choice - it's the
    only thing in this file that's a placeholder. Whatever you put here can
    take as long as it needs; see on_send() below for why that's safe."""
    time.sleep(0.6)  # stands in for whatever real latency a real call has
    return f"You said: {user_message!r}. Wire get_reply() up to a real backend to make this a real assistant."


def reply_in_background(user_message):
    reply = get_reply(user_message)
    # get_reply() runs on a background thread (started by on_send() below) so
    # a slow call never freezes the window - but touching the UI itself must
    # still happen on the UI thread, which is what pane.invoke() is for.
    pane.invoke(lambda: chat.add_message("assistant", reply))


def on_send(user_message):
    threading.Thread(target=reply_in_background, args=(user_message,), daemon=True).start()
    return None  # the reply is added later, asynchronously - see above


def build(window):
    global chat
    chat = pane.chat_panel(
        on_send=on_send,
        placeholder="Type a message...",
        welcome="Hi! This is a template - see get_reply() in this file to wire up a real backend.",
        width=460,
        height=560,
    )
    window.Content = pane.stack(chat.control, margin=16)


if __name__ == "__main__":
    pane.run(build, title="Pane - chat template", width=500, height=640)

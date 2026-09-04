"""
A real, working AI chat window built on pane.chat_panel(), talking to Claude
via the official Anthropic SDK.

    pip install anthropic
    set ANTHROPIC_API_KEY=sk-ant-...      (or configure any credential source
                                            the SDK supports - see its docs)
    python examples/ai_chat.py

pane.chat_panel() itself has no idea what "AI" means - it's just a styled
message list + input row (see pane/chat.py). This file is the part that
actually calls an LLM: on_send() below hands the user's message to Claude on
a background thread (so the window never freezes waiting on the network),
then uses pane.invoke() to marshal the reply back onto the UI thread, which
is the same pattern pane.run()'s own docs use for any background work.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pane

try:
    import anthropic
except ImportError:
    sys.exit("This example needs the Anthropic SDK: pip install anthropic")

MODEL = "claude-opus-5"
SYSTEM_PROMPT = "You are a helpful, concise assistant chatting inside a small desktop app. Keep replies short."

client = anthropic.Anthropic()  # resolves credentials from the environment
history = []  # [{"role": "user"|"assistant", "content": "..."}, ...]


def ask_claude(user_message):
    """Runs on a background thread - see on_send() below."""
    history.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": "low"},  # chat doesn't need deep reasoning by default
            messages=history,
        )
        reply = next((b.text for b in response.content if b.type == "text"), "")
    except anthropic.AuthenticationError:
        reply = "(Error: invalid or missing ANTHROPIC_API_KEY.)"
    except anthropic.RateLimitError:
        reply = "(Error: rate limited - try again in a moment.)"
    except anthropic.APIConnectionError:
        reply = "(Error: couldn't reach the Anthropic API - check your connection.)"
    except anthropic.APIStatusError as ex:
        reply = f"(Error: Claude API returned {ex.status_code}.)"
    else:
        history.append({"role": "assistant", "content": reply})

    pane.invoke(lambda: chat.add_message("assistant", reply))


def on_send(user_message):
    threading.Thread(target=ask_claude, args=(user_message,), daemon=True).start()
    return None  # reply comes later, asynchronously - see ask_claude()


def build(window):
    global chat
    chat = pane.chat_panel(
        on_send=on_send,
        placeholder="Ask Claude something...",
        welcome="Hi! I'm Claude, running through pane-ui. What's on your mind?",
        width=460,
        height=560,
    )
    window.Content = pane.stack(chat.control, margin=16)


if __name__ == "__main__":
    pane.run(build, title="Pane - AI chat", width=500, height=640)

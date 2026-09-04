[← API reference](README.md)

# Chat

```python
chat = pane.chat_panel(*, on_send=None, placeholder="Message...", welcome=None, width=None, height=None, margin=None)
```
A scrollable, bubble-styled message list with a text entry row (Enter or
the Send button both submit). Returns a `pane.ChatPanel` - `chat.control`
is the WPF element to add to your layout:

```python
chat = pane.chat_panel(welcome="Hi! What can I help with?")
window.Content = pane.stack(chat.control, margin=16)
```

It has no idea what "AI" is and makes no network calls - it's just the
widget. `on_send(text)`:

- if it **returns a string**, that's appended as an assistant bubble right
  away - a quick synchronous responder (an echo bot, a local function):
  ```python
  pane.chat_panel(on_send=lambda text: f"you said: {text}")
  ```
- if it **returns `None`** (or isn't given), you're responsible for adding
  the reply yourself, later - the intended pattern for anything that takes
  real time (an HTTP call to an LLM): do the work on a background thread,
  then call `chat.add_message()` via [`pane.invoke()`](threading.md) so the
  window never freezes:
  ```python
  def on_send(text):
      threading.Thread(target=get_reply_then_add, args=(text,), daemon=True).start()
      return None

  def get_reply_then_add(text):
      reply = call_some_backend(text)  # slow - runs off the UI thread
      pane.invoke(lambda: chat.add_message("assistant", reply))
  ```

`ChatPanel` methods:

| Method | |
|---|---|
| `chat.add_message(role, content)` | Appends a bubble and scrolls it into view. `role`: `"user"` or `"assistant"`. Must run on the UI thread - use `pane.invoke()` from a background thread. |
| `chat.clear()` | Removes every message. |

See `examples/chat_app.py` in the repo for a complete, runnable template.

← [Layout](layout.md) · Next: [Music player](music.md) →

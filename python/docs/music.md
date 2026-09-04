[← API reference](README.md)

# Music player

```python
player = pane.music_player(*, on_play_pause=None, on_previous=None, on_next=None, on_seek=None, on_volume_change=None, on_repeat_change=None, title="No track loaded", artist="", duration=100, previous_restart_threshold=3, width=None, margin=None)
```
An artwork placeholder, track title/artist, previous/play-pause/next/repeat
transport buttons, a seek slider with mm:ss position/duration labels (like
Spotify), and a volume slider. Returns a `pane.MusicPlayer` - `player.control`
is the WPF element to add to your layout:

```python
player = pane.music_player(width=300)
window.Content = pane.stack(player.control, margin=20)
```

It has no idea how to play audio and makes no attempt to - it's the UI
only, same as [`chat_panel()`](chat.md) has no idea what "AI" means. Wire
it up to a real backend of your choice via the `on_*` callbacks and the
returned `MusicPlayer`'s update methods; see `examples/music_player_app.py`
in the repo for a runnable template with a fake, in-memory "backend" (no
audio, no dependencies) demonstrating the intended wiring.

Position/duration values are assumed to be **seconds** - that's what the
mm:ss labels format them as.

## Callbacks

`on_play_pause(is_playing)`, if it takes an argument, receives the new
playing state right after the button toggles - start/stop your real
playback there. `on_seek(value)` / `on_volume_change(value)` fire as those
sliders are dragged.

`on_previous` has Spotify-style logic built in: it only fires on click
**early** in the track - within `previous_restart_threshold` seconds (default
`3`) of position 0. Past that, clicking previous just restarts the current
track instead, which needs no callback of yours - the widget calls
`on_seek(0)` itself, same as if the seek slider had been dragged there. Set
`previous_restart_threshold=0` to always jump to the previous track
instead. `on_next` always fires on click, no such logic.

`on_repeat_change(mode)`, if it takes an argument, fires each time the
repeat button is clicked, cycling `"off"` → `"all"` → `"one"` → `"off"`
(also available as `pane.REPEAT_MODES`). The widget only
tracks/shows which mode is active - it has no playlist of its own, so
acting on the mode (loop the current track, loop the whole playlist, stop
at the end) is up to you, in `on_repeat_change` and/or wherever you decide
what `on_next` does - see `examples/music_player_app.py` for a worked
example (a fake ticker that actually respects all three modes).

## `MusicPlayer` methods

None of these play audio - they only update what's shown, so call them
from wherever your real playback backend reports state (a callback, a
polling timer, ...). Like every other Pane/WPF UI mutation, call them via
[`pane.invoke()`](threading.md) if you're on a background thread.

| Method | |
|---|---|
| `player.set_track(title, artist="", duration=100)` | Updates the title/artist/artwork area and resets position to 0. `duration` is seconds, shown as the mm:ss total and used as the seek slider's max. |
| `player.set_playing(playing)` | Updates the play/pause button's icon and internal state. |
| `player.is_playing()` | Returns the current playing state. |
| `player.set_position(value)` | Updates the seek slider and the mm:ss position label. Does **not** fire `on_seek` - this is for reporting real progress, not simulating a user drag. |
| `player.set_repeat_mode(mode)` | Updates the repeat button's look. `mode`: `"off"`, `"all"`, or `"one"`. |
| `player.repeat_mode()` | Returns the current repeat mode. |

← [Chat](chat.md) · Next: [Theming](theming.md) →

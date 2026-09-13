[← API reference](README.md)

# Playlist

```python
pl = pane.playlist(tracks=None, *, on_select=None, on_remove=None, current_index=-1, empty_message="No tracks", width=None, height=None, margin=None)
```
A scrollable list of tracks - title, artist, and mm:ss duration per row,
a "▶" marker on whichever row is current, and an optional per-row "✕"
remove button. Returns a `pane.Playlist` - `pl.control` is the WPF element
to add to your layout:

```python
pl = pane.playlist(
    [("Sunset Drive", "The Night Owls", 198), ("Coastal Static", "Marigold", 221)],
    on_select=lambda track: print("play", track),
    on_remove=lambda i: print("remove", i),
)
window.Content = pane.stack(pl.control, margin=20)
```

Like [`music_player()`](music.md), it has no idea how to play audio and
makes no attempt to - it's the UI only. `music_player()`'s own docs are
explicit that "it has no playlist of its own"; this widget is the other
half of that pairing, showing a list of tracks and telling you when one is
clicked or removed, but never playing, reordering, or dropping anything
itself. Wire it up to a real backend of your choice via the `on_*`
callbacks and the returned `Playlist`'s update methods; see
`examples/music_player_app.py` in the repo for a runnable template pairing
this with `music_player()`.

A track is a `(title, artist, duration)` tuple, a `(title, artist)` pair,
or a plain title string - `artist`/`duration` default to `""` / `0` for
the shorter forms. `duration` is assumed to be **seconds**, same as
`music_player()`.

## Callbacks

`on_select(track)`, if it takes an argument, receives the clicked row's
track, in whatever form it was given to `.set_tracks()`/`tracks=`. It only
fires on an actual click - never as a side effect of `.set_tracks()` or
`.set_current_index()`.

`on_remove(index)` fires with a row's index when that row's "✕" is
clicked. Pass `on_remove` to enable the button at all - omit it (the
default) and rows get no remove control. Like `on_next` in
`music_player()`, this widget has no playlist of its own to remove from:
it's on your `on_remove` to drop the track from wherever `tracks` came
from and call `.set_tracks()` again with the result.

## `Playlist` methods

None of these touch playback - they only update what's shown, so drive
them from wherever your real backend's state actually lives. Like every
other Pane/WPF UI mutation, call them via [`pane.invoke()`](threading.md)
if you're on a background thread.

| Method | |
|---|---|
| `pl.set_tracks(tracks)` | Replaces the whole list and redraws it. `tracks`: a list of `(title, artist, duration)` tuples, `(title, artist)` pairs, or plain title strings. |
| `pl.set_current_index(index)` | Marks row `index` as "now playing" (`-1` for none). Does **not** fire `on_select`. |
| `pl.current_index()` | Returns the current "now playing" index. |
| `pl.tracks()` | Returns a copy of the current track list. |

← [Music player](music.md) · Next: [Theming](theming.md) →

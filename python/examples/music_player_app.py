"""
A template music player built on pane.music_player() - the UI, the
transport wiring, and a fake in-memory "backend" (a hardcoded playlist and
a timer that pretends to advance playback), with NO real audio anywhere.

pane.music_player() has no idea how to play audio and makes no attempt to -
it's just a styled artwork/title/artist/transport/repeat/seek/volume widget
(see pane/music.py). Everything below that actually looks like a music
player - the playlist, the position ticking forward, auto-advancing at the
end of a track, honoring whichever repeat mode is selected - is this file
simulating one so you can see the wiring, ticker() in particular. Swap
PLAYLIST and the body of ticker() for a real backend (pygame.mixer, VLC,
a media API, ...) and this becomes a real player.

Run: python examples/music_player_app.py
"""

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pane

PLAYLIST = [
    ("Sunset Drive", "The Night Owls", 18),
    ("Coastal Static", "Marigold", 21),
    ("Paper Lanterns", "Halide", 16),
]  # (title, artist, duration) - duration kept short here just so you can
   # see auto-advance happen quickly; use real seconds for a real player.

state = {"index": 0, "position": 0, "playing": False}
player = None  # set in build()


def load_track(index):
    state["index"] = index % len(PLAYLIST)
    state["position"] = 0
    title, artist, duration = PLAYLIST[state["index"]]
    player.set_track(title, artist, duration=duration)


def on_play_pause(is_playing):
    # music_player() already toggled the button glyph itself - this just
    # needs to sync ticker()'s own idea of whether it should advance.
    state["playing"] = is_playing


def on_previous():
    load_track(state["index"] - 1)


def on_next():
    load_track(state["index"] + 1)


def on_seek(value):
    state["position"] = value  # no real audio to actually seek


def on_volume_change(value):
    pass  # no real audio to set the volume of


def on_repeat_change(mode):
    pass  # nothing to do here - ticker() below reads player.repeat_mode()
    # itself, right when a track actually finishes, rather than tracking
    # a separate copy of it here.


def ticker():
    """Fakes playback progress once a second, for as long as the window is
    open, respecting whichever repeat mode is currently selected - the same
    three cases a real backend's end-of-track handling would need to cover.
    Runs on a background thread; touching the UI (player.set_position,
    on_next, player.repeat_mode() is a plain attribute read, not a WPF
    object, so that part's safe from any thread) is marshaled through
    pane.invoke() the same way any real playback-position callback would
    need to be - see docs/threading.md."""
    while True:
        time.sleep(1)
        if not state["playing"]:
            continue
        _, _, duration = PLAYLIST[state["index"]]
        state["position"] += 1
        if state["position"] < duration:
            position = state["position"]
            pane.invoke(lambda: player.set_position(position))
            continue

        # Reached the end of the current track.
        mode = player.repeat_mode()
        if mode == "one":
            state["position"] = 0
            pane.invoke(lambda: player.set_position(0))
        elif mode == "all":
            pane.invoke(on_next)
        elif state["index"] < len(PLAYLIST) - 1:  # "off", but more tracks left
            pane.invoke(on_next)
        else:  # "off" and this was the last track - stop, don't wrap
            state["playing"] = False
            pane.invoke(lambda: player.set_playing(False))


def build(window):
    global player
    player = pane.music_player(
        on_play_pause=on_play_pause,
        on_previous=on_previous,
        on_next=on_next,
        on_seek=on_seek,
        on_volume_change=on_volume_change,
        on_repeat_change=on_repeat_change,
        width=280,
    )
    load_track(0)
    window.Content = pane.stack(player.control, margin=20)

    threading.Thread(target=ticker, daemon=True).start()


if __name__ == "__main__":
    pane.run(build, title="Pane - music player template", width=340, height=340)

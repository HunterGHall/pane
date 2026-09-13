"""
A template music player built on pane.music_player() + pane.playlist() -
the UI, the transport/list wiring, and a fake in-memory "backend" (a
hardcoded playlist and a timer that pretends to advance playback), with NO
real audio anywhere.

Neither widget has any idea how to play audio and neither makes an attempt
to - music_player() is just a styled artwork/title/artist/transport/
repeat/seek/volume widget, and playlist() is just a styled, clickable track
list (see pane/music.py and pane/playlist.py). Everything below that
actually looks like a music player - the playlist data itself, the
position ticking forward, auto-advancing at the end of a track, honoring
whichever repeat mode is selected, removing a track on click - is this
file simulating one so you can see the wiring, ticker() in particular.
Swap PLAYLIST and the body of ticker() for a real backend (pygame.mixer,
VLC, a media API, ...) and this becomes a real player.

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
player_list = None  # set in build()


def load_track(index):
    if not PLAYLIST:  # every track removed via the playlist's "✕" buttons
        return
    state["index"] = index % len(PLAYLIST)
    state["position"] = 0
    title, artist, duration = PLAYLIST[state["index"]]
    player.set_track(title, artist, duration=duration)
    player_list.set_current_index(state["index"])


def on_playlist_select(track):
    # playlist() hands back whatever tracks= gave it - here that's a
    # (title, artist, duration) tuple straight out of PLAYLIST, so its
    # index in PLAYLIST is its index in the (unchanged) list itself.
    load_track(PLAYLIST.index(track))
    state["playing"] = True
    player.set_playing(True)


def on_playlist_remove(index):
    # playlist() has no playlist of its own to remove from (see
    # docs/playlist.md) - it's on this callback to update the real list and
    # push the result back with set_tracks().
    del PLAYLIST[index]
    if not PLAYLIST:
        state["playing"] = False
        player.set_playing(False)
        player_list.set_tracks(PLAYLIST)
        return
    if index < state["index"]:
        state["index"] -= 1
    elif index == state["index"]:
        load_track(state["index"])  # current track removed - load whatever shifted into its slot
    player_list.set_tracks(PLAYLIST)
    player_list.set_current_index(state["index"])


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
    global player, player_list
    player = pane.music_player(
        on_play_pause=on_play_pause,
        on_previous=on_previous,
        on_next=on_next,
        on_seek=on_seek,
        on_volume_change=on_volume_change,
        on_repeat_change=on_repeat_change,
        width=280,
    )
    player_list = pane.playlist(
        PLAYLIST,
        on_select=on_playlist_select,
        on_remove=on_playlist_remove,
        width=280,
    )
    load_track(0)
    window.Content = pane.stack(player.control, player_list.control, spacing=16, margin=20)

    threading.Thread(target=ticker, daemon=True).start()


if __name__ == "__main__":
    pane.run(build, title="Pane - music player template", width=340, height=560)

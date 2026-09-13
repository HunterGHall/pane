"""A playlist UI shell: a scrollable list of tracks with title/artist/
duration, a "now playing" marker on whichever row is current, and an
optional per-row remove button - built entirely from Pane's existing
list/text/button styles (no new engine styles needed).

Like music_player() (see pane/music.py), this has no idea how to play audio
and makes no attempt to. music_player() is explicit that "it has no
playlist of its own" - this widget is the other half: it shows a list of
tracks and tells you when one is clicked or removed, but never plays,
reorders, or drops anything itself. Wire it up to a real backend of your
choice via on_select/on_remove and the returned Playlist's
.set_tracks()/.set_current_index(); see examples/music_player_app.py for a
template pairing this with music_player().
"""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import Thickness, VerticalAlignment  # noqa: E402

from .layout import grid, stack  # noqa: E402
from .widgets import _apply_common, button, text  # noqa: E402


def _format_time(seconds):
    seconds = int(max(0, seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


def _unpack_track(track):
    """A track is (title, artist, duration), (title, artist), or a plain
    title string - artist/duration default to "" / 0 for the shorter forms."""
    if isinstance(track, (tuple, list)):
        title = track[0]
        artist = track[1] if len(track) > 1 else ""
        duration = track[2] if len(track) > 2 else 0
        return title, artist, duration
    return str(track), "", 0


def _swallow_selection(sender, args):
    # A row's remove button still lets the surrounding ListBoxItem select
    # itself first - WPF selects on PreviewMouseLeftButtonDown, before the
    # Button's own Click ever fires - so without this, removing a track
    # would also fire on_select for the row being removed. Marking the
    # preview event handled here stops the ListBoxItem from seeing the
    # click at all, so only on_remove fires.
    args.Handled = True


def _build_row(index, track, current, on_remove):
    from System.Windows.Controls import ListBoxItem

    title, artist, duration = _unpack_track(track)

    title_label = text(("▶ " if current else "") + title, bold=current)  # ▶ now-playing marker
    artist_label = text(artist or " ", size="caption", color="secondary")
    info = stack(title_label, artist_label, spacing=2)
    info.VerticalAlignment = VerticalAlignment.Center

    duration_label = text(_format_time(duration), size="caption", color="secondary")
    duration_label.VerticalAlignment = VerticalAlignment.Center
    duration_label.Margin = Thickness(12, 0, 12 if on_remove else 0, 0)

    cells = [(0, 0, info), (0, 1, duration_label)]
    columns = ["*", "auto"]
    if on_remove:
        remove_button = button("✕", style="ghost", width=28, on_click=lambda: on_remove(index))  # ✕
        remove_button.PreviewMouseLeftButtonDown += _swallow_selection
        remove_button.VerticalAlignment = VerticalAlignment.Center
        cells.append((0, 2, remove_button))
        columns.append("auto")

    row = grid(cells, columns=columns)
    row.Margin = Thickness(4, 6, 4, 6)

    item = ListBoxItem()
    item.Content = row
    return item


class Playlist:
    """Returned by playlist(). `.control` is the WPF element to add to your
    layout. Update what's shown with .set_tracks()/.set_current_index() as
    your real backend reports state - like every other Pane/WPF UI
    mutation, call them via pane.invoke() if you're on a background thread.
    """

    def __init__(self, control, list_box, empty_label, on_remove):
        self.control = control
        self._list_box = list_box
        self._empty_label = empty_label
        self._on_remove = on_remove
        self._tracks = []
        self._current_index = -1
        # See _rebuild(): clearing/repopulating Items fires SelectionChanged
        # with no real user click behind it - this keeps that from reaching
        # on_select, the same trick music.py's MusicPlayer uses for
        # programmatic slider updates (_suppress_seek_callback).
        self._suppress_select_callback = False

    def set_tracks(self, tracks):
        """tracks: a list of (title, artist, duration) tuples, (title, artist)
        pairs, or plain title strings."""
        self._tracks = list(tracks)
        if self._current_index >= len(self._tracks):
            self._current_index = -1
        self._rebuild()

    def set_current_index(self, index):
        """Marks the row at `index` as "now playing" (-1 for none). Does
        not fire on_select - this is for reporting real playback state,
        not simulating a user click."""
        self._current_index = index
        self._rebuild()

    def current_index(self):
        return self._current_index

    def tracks(self):
        return list(self._tracks)

    def _rebuild(self):
        self._suppress_select_callback = True
        self._list_box.Items.Clear()
        for i, track in enumerate(self._tracks):
            self._list_box.Items.Add(_build_row(i, track, i == self._current_index, self._on_remove))
        self._suppress_select_callback = False
        if self._empty_label is not None:
            self._empty_label.Visibility = _visibility(not self._tracks)


def _visibility(visible):
    from System.Windows import Visibility

    return Visibility.Visible if visible else Visibility.Collapsed


def playlist(
    tracks=None,
    *,
    on_select=None,
    on_remove=None,
    current_index=-1,
    empty_message="No tracks",
    width=None,
    height=None,
    margin=None,
):
    """A scrollable playlist: one row per track (title, artist, mm:ss
    duration), a "▶" marker on whichever row is current, and an optional
    per-row "✕" remove button. It has no idea how to play audio and makes
    no attempt to - it's the UI only, same as music_player().

    tracks: initial list of (title, artist, duration) tuples, (title, artist)
    pairs, or plain title strings - see .set_tracks() to replace it later.

    on_select(track), if it takes an argument, receives the clicked row's
    track (in whatever form it was given to set_tracks()/tracks=) - use
    playlist().tracks()[i] yourself if you need the index too, or just
    close over it when building tracks. Not fired by set_current_index()
    or set_tracks(), only by an actual click.

    on_remove(index) fires when a row's "✕" is clicked, with that row's
    index. Pass on_remove to enable the button at all - with it omitted (the
    default), rows have no remove control. Like on_next in music_player(),
    this widget has no playlist of its own to remove from: it's up to your
    on_remove to drop the track from wherever tracks came from and call
    .set_tracks() again with the result.

    Returns a Playlist; update what's shown with its
    .set_tracks()/.set_current_index() as your real backend reports state.
    """
    from System.Windows.Controls import ListBox

    from ._events import make_handler

    list_box = ListBox()
    _apply_common(list_box, width=width, height=height, enabled=True)

    empty_label = text(empty_message, color="secondary")
    empty_label.Margin = Thickness(4, 12, 4, 12)

    panel = Playlist(None, list_box, empty_label, on_remove)

    def selected_track():
        i = list_box.SelectedIndex
        tracks = panel.tracks()
        return tracks[i] if 0 <= i < len(tracks) else None

    if on_select:
        handler = make_handler(on_select, selected_track)

        def selection_changed(sender, args):
            # See Playlist._suppress_select_callback: rebuilding the row
            # list (set_tracks()/set_current_index()) also fires this, with
            # no click behind it - only forward real selections.
            if panel._suppress_select_callback:
                return
            if selected_track() is not None:
                handler(sender, args)

        list_box.SelectionChanged += selection_changed

    root = stack(empty_label, list_box, spacing=0)
    panel.control = root
    panel.set_tracks(tracks or [])
    _apply_common(root, margin=margin)

    return panel

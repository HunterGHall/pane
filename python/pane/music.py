"""A music-player UI shell: artwork placeholder, track title/artist,
transport controls, a Spotify-style position/duration display around the
seek slider, and a volume slider - built entirely from Pane's existing
button/slider/text styles (no new engine styles needed).

This module has no idea how to play audio and makes no attempt to - it's
the UI only, same as chat_panel() has no idea what "AI" means. Wire it up
to a real backend of your choice via the on_* callbacks and the returned
MusicPlayer's .set_track()/.set_playing()/.set_position(); see
examples/music_player_app.py for a template with a fake, in-memory
"backend" (no audio, no dependencies) showing the intended wiring.

Position/duration values are assumed to be in seconds - that's what the
mm:ss time labels format them as.
"""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import HorizontalAlignment, Thickness, VerticalAlignment  # noqa: E402

from .layout import grid, stack  # noqa: E402
from .widgets import _apply_common, _find_style, button, slider, text  # noqa: E402

# Spotify-style skip-back: within this many seconds of the start of a track,
# "previous" jumps to the actual previous track; past that, it restarts the
# current track instead (like clicking back mid-song usually should).
DEFAULT_PREVIOUS_RESTART_THRESHOLD = 3

# Clicking the repeat button cycles through these in order. The widget only
# tracks/displays which one is active and tells you when it changes - it has
# no playlist of its own, so acting on the mode (loop the current track,
# loop the whole playlist, stop at the end) is up to your on_repeat_change
# handler / whatever drives on_next.
REPEAT_MODES = ("off", "all", "one")


def _format_time(seconds):
    seconds = int(max(0, seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


def _pause_icon():
    """Two small bars, built as actual vector shapes rather than a Unicode
    glyph - "⏸" (Miscellaneous Technical block) doesn't render in Segoe UI
    (shows as a tofu box), and two adjacent "▮" block characters render
    edge-to-edge with no visible gap even with a space between them, so
    neither text approach reads as "pause". This always renders correctly,
    independent of font/glyph support."""
    from System.Windows.Controls import Orientation, StackPanel
    from System.Windows.Media import Colors, SolidColorBrush
    from System.Windows.Shapes import Rectangle

    icon = StackPanel()
    icon.Orientation = Orientation.Horizontal
    for i in range(2):
        bar = Rectangle()
        bar.Width = 4
        bar.Height = 14
        bar.Fill = SolidColorBrush(Colors.White)
        if i == 1:
            bar.Margin = Thickness(4, 0, 0, 0)
        icon.Children.Add(bar)
    return icon


class MusicPlayer:
    """Returned by music_player(). `.control` is the WPF element to add to
    your layout. These methods only update what's shown - none of them play
    audio - so call them from wherever your real playback backend reports
    state (a callback, a polling timer, ...). Like every other Pane/WPF UI
    mutation, call them via pane.invoke() if you're on a background thread.
    """

    def __init__(self, control, title_label, artist_label, play_button, position_slider, position_label, duration_label, repeat_button):
        self.control = control
        self._title_label = title_label
        self._artist_label = artist_label
        self._play_button = play_button
        self._position_slider = position_slider
        self._position_label = position_label
        self._duration_label = duration_label
        self._repeat_button = repeat_button
        self._playing = False
        self._repeat_mode = "off"
        # Slider.ValueChanged fires on *any* value change, programmatic sets
        # included - without this, every set_position() call (e.g. a
        # playback-progress ticker) would also fire on_seek, as if the user
        # had dragged the slider there themselves. set_position() sets this
        # around its own Value assignment so seek_changed() below can tell
        # the difference and only call on_seek for real user drags.
        self._suppress_seek_callback = False

    def set_track(self, title, artist="", duration=100):
        """duration: seconds - shown as the mm:ss total next to the seek
        slider, and used as the seek slider's Maximum."""
        self._title_label.Text = title
        self._artist_label.Text = artist or " "
        self._position_slider.Maximum = duration
        self._duration_label.Text = _format_time(duration)
        self.set_position(0)

    def set_playing(self, playing):
        self._playing = bool(playing)
        self._play_button.Content = _pause_icon() if self._playing else "▶"

    def is_playing(self):
        return self._playing

    def set_position(self, value):
        self._suppress_seek_callback = True
        self._position_slider.Value = value
        self._suppress_seek_callback = False
        self._position_label.Text = _format_time(value)

    def set_repeat_mode(self, mode):
        """mode: "off", "all", or "one" - see REPEAT_MODES. Only updates the
        button's own look; it's on you to act on the mode (see the module
        docstring and REPEAT_MODES)."""
        if mode not in REPEAT_MODES:
            raise ValueError(f"invalid repeat mode: {mode!r} (expected one of {REPEAT_MODES})")
        self._repeat_mode = mode
        self._repeat_button.Content = "↻ 1" if mode == "one" else "↻"  # ↻ (repeat), ↻ 1 (repeat one)
        if mode == "off":
            # Button() below never had an explicit Style, only an implicit
            # one from Pane.xaml's resources (the plain "secondary" look) -
            # ClearValue restores exactly that, unlike Style = None, which
            # would strip styling entirely and render a bare native button.
            from System.Windows.Controls import Button

            self._repeat_button.ClearValue(Button.StyleProperty)
        else:
            self._repeat_button.Style = _find_style("Pane.Button.Primary")

    def repeat_mode(self):
        return self._repeat_mode


def music_player(
    *,
    on_play_pause=None,
    on_previous=None,
    on_next=None,
    on_seek=None,
    on_volume_change=None,
    on_repeat_change=None,
    title="No track loaded",
    artist="",
    duration=100,
    previous_restart_threshold=DEFAULT_PREVIOUS_RESTART_THRESHOLD,
    width=None,
    margin=None,
):
    """A music-player UI shell: artwork placeholder, track title/artist,
    previous/play-pause/next/repeat transport buttons, a seek slider with
    mm:ss position/duration labels (like Spotify), and a volume slider. It
    has no idea how to play audio - it's the UI only.

    on_play_pause(is_playing), if it takes an argument, receives the new
    playing state right after the button toggles - start/stop your real
    playback there. on_seek(value)/on_volume_change(value) fire as those
    sliders are dragged.

    on_previous fires on click only early in the track - within
    previous_restart_threshold seconds of position 0 (Spotify-style: skip
    back jumps to the actual previous track only near the start; otherwise
    it just restarts the current one, which needs no callback of yours -
    the widget calls on_seek(0) itself, same as if the seek slider had been
    dragged there). Set previous_restart_threshold=0 to always jump to the
    previous track instead. on_next always fires on click, no such logic.

    on_repeat_change(mode), if it takes an argument, fires each time the
    repeat button is clicked, cycling "off" -> "all" -> "one" -> "off" (see
    REPEAT_MODES). The widget only tracks/shows which mode is active - it
    has no playlist of its own, so acting on the mode (loop the current
    track, loop the whole playlist, stop at the end) is up to you, in
    on_repeat_change and/or wherever you decide what on_next does.

    Returns a MusicPlayer; update what's displayed with its
    .set_track()/.set_playing()/.set_position() as your real backend
    reports state - see examples/music_player_app.py.
    """
    from System.Windows.Controls import Border

    artwork = Border()
    artwork.Width = 88
    artwork.Height = 88
    artwork.Style = _find_style("Pane.Card")
    artwork.Padding = Thickness(0)
    artwork_glyph = text("♪", size="title-large", color="secondary")  # eighth note
    artwork_glyph.HorizontalAlignment = HorizontalAlignment.Center
    artwork_glyph.VerticalAlignment = VerticalAlignment.Center
    artwork.Child = artwork_glyph

    title_label = text(title, size="subtitle", bold=True)
    artist_label = text(artist or " ", color="secondary")
    info = stack(title_label, artist_label, spacing=2)
    info.VerticalAlignment = VerticalAlignment.Center
    info.Margin = Thickness(14, 0, 0, 0)

    header = stack(artwork, info, orientation="horizontal")

    position_label = text(_format_time(0), size="caption", color="secondary")
    duration_label = text(_format_time(duration), size="caption", color="secondary")

    panel = MusicPlayer(None, title_label, artist_label, None, None, position_label, duration_label, None)

    def toggle_play():
        panel.set_playing(not panel.is_playing())
        if on_play_pause:
            on_play_pause(panel.is_playing())

    def prev_clicked():
        if panel._position_slider.Value <= previous_restart_threshold:
            if on_previous:
                on_previous()
        else:
            panel.set_position(0)
            if on_seek:
                on_seek(0)

    def seek_changed(value):
        panel._position_label.Text = _format_time(value)
        if panel._suppress_seek_callback:
            return
        if on_seek:
            on_seek(value)

    def cycle_repeat():
        next_mode = REPEAT_MODES[(REPEAT_MODES.index(panel.repeat_mode()) + 1) % len(REPEAT_MODES)]
        panel.set_repeat_mode(next_mode)
        if on_repeat_change:
            on_repeat_change(next_mode)

    play_button = button("▶", style="primary", on_click=toggle_play, width=44)  # play triangle
    # Media-symbol glyphs (⏮/⏭/⏸, Unicode's Miscellaneous Technical block) don't
    # render in Segoe UI/Segoe UI Variable - they show as tofu boxes. Built from
    # the same Geometric Shapes block as the play triangle above instead, which
    # does render correctly everywhere that font ships (i.e. every Windows box).
    # No fixed width here (unlike play_button) - two glyphs need more room
    # than one, and a too-narrow Button clips its content rather than
    # shrinking it, so auto-sizing is what actually guarantees no clipping.
    prev_button = button("◀◀", on_click=prev_clicked)  # ◀◀ previous track / restart
    next_button = button("▶▶", on_click=on_next)  # ▶▶ next track
    repeat_button = button("↻", on_click=cycle_repeat)

    transport = stack(prev_button, play_button, next_button, repeat_button, orientation="horizontal", spacing=10)
    transport.HorizontalAlignment = HorizontalAlignment.Center

    position_slider = slider(value=0, minimum=0, maximum=duration, on_change=seek_changed)
    panel._play_button = play_button
    panel._prev_button = prev_button
    panel._position_slider = position_slider
    panel._repeat_button = repeat_button

    position_row = grid(
        [(0, 0, position_label), (0, 1, position_slider), (0, 2, duration_label)],
        columns=["auto", "*", "auto"],
    )
    position_label.Margin = Thickness(0, 0, 8, 0)
    duration_label.Margin = Thickness(8, 0, 0, 0)
    position_label.VerticalAlignment = VerticalAlignment.Center
    duration_label.VerticalAlignment = VerticalAlignment.Center

    volume_row = stack(
        text("\U0001f50a", color="secondary"),  # speaker
        slider(value=70, minimum=0, maximum=100, on_change=on_volume_change, width=120),
        orientation="horizontal",
        spacing=8,
    )
    volume_row.HorizontalAlignment = HorizontalAlignment.Center

    root_stack = stack(header, transport, position_row, volume_row, spacing=16)
    root = Border()
    root.Style = _find_style("Pane.Card")
    root.Child = root_stack

    panel.control = root
    _apply_common(root, width=width, margin=margin)

    return panel

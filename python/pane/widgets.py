"""Widget factory functions - each returns a real, Pane-styled WPF control.

Most Pane controls (checkboxes, radio buttons, text boxes, sliders, ...) are
styled implicitly by Pane.xaml, so a plain `CheckBox()` picks up Pane's look
automatically once it's added to a window built by pane.run(). Only the
handful of controls with named styles (Button variants, ToggleSwitch, Card,
ColorSwatch, NavigationList) need an explicit style lookup here.
"""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import Application, FontWeights, TextWrapping  # noqa: E402

from ._convert import to_thickness  # noqa: E402
from ._events import make_handler  # noqa: E402

_FONT_SIZE_KEYS = {
    "caption": "Pane.Font.Size.Caption",
    "body": "Pane.Font.Size.Body",
    "subtitle": "Pane.Font.Size.Subtitle",
    "title": "Pane.Font.Size.Title",
    "title-large": "Pane.Font.Size.TitleLarge",
}

_TEXT_COLOR_KEYS = {
    "primary": "Pane.Brush.Text.Primary",
    "secondary": "Pane.Brush.Text.Secondary",
    "disabled": "Pane.Brush.Text.Disabled",
}


def _find_style(key):
    app = Application.Current
    if app is None:
        raise RuntimeError(
            "No Pane window is running yet - build widgets inside the function "
            "you pass to pane.run(), not before it."
        )
    return app.FindResource(key)


def _apply_common(element, *, width=None, height=None, margin=None, enabled=None):
    if width is not None:
        element.Width = width
    if height is not None:
        element.Height = height
    if margin is not None:
        element.Margin = to_thickness(margin)
    if enabled is not None:
        element.IsEnabled = enabled


# --- Buttons ----------------------------------------------------------------

def button(label, *, style="secondary", on_click=None, width=None, height=None, margin=None, enabled=True):
    from System.Windows.Controls import Button

    btn = Button()
    btn.Content = label
    if style == "primary":
        btn.Style = _find_style("Pane.Button.Primary")
    elif style == "ghost":
        btn.Style = _find_style("Pane.Button.Ghost")
    # else "secondary": leave unset - Pane's implicit Button style applies.
    _apply_common(btn, width=width, height=height, margin=margin, enabled=enabled)
    if on_click:
        btn.Click += make_handler(on_click, lambda: None)
    return btn


# --- Selection ----------------------------------------------------------------

def checkbox(label, *, checked=False, on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import CheckBox

    cb = CheckBox()
    cb.Content = label
    cb.IsChecked = checked
    _apply_common(cb, width=width, margin=margin, enabled=enabled)
    if on_change:
        handler = make_handler(on_change, lambda: cb.IsChecked)
        cb.Checked += handler
        cb.Unchecked += handler
        cb.Indeterminate += handler
    return cb


def radio_button(label, group, *, checked=False, on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import RadioButton

    rb = RadioButton()
    rb.Content = label
    rb.GroupName = group
    rb.IsChecked = checked
    _apply_common(rb, width=width, margin=margin, enabled=enabled)
    if on_change:
        rb.Checked += make_handler(on_change, lambda: True)
    return rb


def toggle_switch(*, checked=False, on_change=None, margin=None, enabled=True):
    from System.Windows.Controls.Primitives import ToggleButton

    tb = ToggleButton()
    tb.Style = _find_style("Pane.ToggleSwitch")
    tb.IsChecked = checked
    _apply_common(tb, margin=margin, enabled=enabled)
    if on_change:
        handler = make_handler(on_change, lambda: bool(tb.IsChecked))
        tb.Checked += handler
        tb.Unchecked += handler
    return tb


# --- Text input ----------------------------------------------------------------

def text_box(*, text="", placeholder="", on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import TextBox
    from Pane.Controls import PaneAssist

    tbx = TextBox()
    tbx.Text = text
    if placeholder:
        PaneAssist.SetPlaceholder(tbx, placeholder)
    _apply_common(tbx, width=width, margin=margin, enabled=enabled)
    if on_change:
        tbx.TextChanged += make_handler(on_change, lambda: tbx.Text)
    return tbx


def password_box(*, on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import PasswordBox

    pwd = PasswordBox()
    _apply_common(pwd, width=width, margin=margin, enabled=enabled)
    if on_change:
        pwd.PasswordChanged += make_handler(on_change, lambda: pwd.Password)
    return pwd


# --- Progress & range ----------------------------------------------------------------

def progress_bar(*, value=0, minimum=0, maximum=100, indeterminate=False, width=None, margin=None):
    from System.Windows.Controls import ProgressBar

    pb = ProgressBar()
    pb.Minimum = minimum
    pb.Maximum = maximum
    pb.Value = value
    pb.IsIndeterminate = indeterminate
    _apply_common(pb, width=width, margin=margin)
    return pb


def slider(*, value=0, minimum=0, maximum=100, on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import Slider

    s = Slider()
    s.Minimum = minimum
    s.Maximum = maximum
    s.Value = value
    _apply_common(s, width=width, margin=margin, enabled=enabled)
    if on_change:
        s.ValueChanged += make_handler(on_change, lambda: s.Value)
    return s


# --- Choices & lists ----------------------------------------------------------------

def combo_box(items, *, selected_index=0, on_change=None, width=None, margin=None, enabled=True):
    from System.Windows.Controls import ComboBox, ComboBoxItem

    cb = ComboBox()
    for item in items:
        cbi = ComboBoxItem()
        cbi.Content = str(item)
        cb.Items.Add(cbi)
    if items:
        cb.SelectedIndex = selected_index
    _apply_common(cb, width=width, margin=margin, enabled=enabled)
    if on_change:
        cb.SelectionChanged += make_handler(on_change, lambda: cb.SelectedIndex)
    return cb


def list_box(items, *, selected_index=0, on_select=None, width=None, height=None, margin=None, enabled=True):
    from System.Windows.Controls import ListBox, ListBoxItem

    lb = ListBox()
    for item in items:
        lbi = ListBoxItem()
        lbi.Content = str(item)
        lb.Items.Add(lbi)
    if items:
        lb.SelectedIndex = selected_index
    _apply_common(lb, width=width, height=height, margin=margin, enabled=enabled)
    if on_select:
        lb.SelectionChanged += make_handler(on_select, lambda: lb.SelectedIndex)
    return lb


def nav_list(items, *, selected_index=0, on_select=None):
    """A Pane-styled sidebar navigation list (see Pane.NavigationList)."""
    from System.Windows.Controls import ListBox, ListBoxItem

    lb = ListBox()
    lb.Style = _find_style("Pane.NavigationList")
    for item in items:
        lbi = ListBoxItem()
        lbi.Content = str(item)
        lb.Items.Add(lbi)
    if items:
        lb.SelectedIndex = selected_index
    if on_select:
        lb.SelectionChanged += make_handler(on_select, lambda: lb.SelectedIndex)
    return lb


def tab_control(tabs, *, width=None, height=None, margin=None):
    """tabs: a dict of {header: content_element}, or a list of (header, content) pairs."""
    from System.Windows.Controls import TabControl, TabItem

    tc = TabControl()
    entries = tabs.items() if isinstance(tabs, dict) else tabs
    for header, content in entries:
        ti = TabItem()
        ti.Header = header
        ti.Content = content
        tc.Items.Add(ti)
    _apply_common(tc, width=width, height=height, margin=margin)
    return tc


# --- Layout & overlays ----------------------------------------------------------------

def expander(header, content, *, expanded=False, margin=None):
    from System.Windows.Controls import Expander

    e = Expander()
    e.Header = header
    e.Content = content
    e.IsExpanded = expanded
    _apply_common(e, margin=margin)
    return e


def group_box(header, content, *, margin=None):
    from System.Windows.Controls import GroupBox

    g = GroupBox()
    g.Header = header
    g.Content = content
    _apply_common(g, margin=margin)
    return g


def separator(*, margin=None):
    from System.Windows.Controls import Separator

    s = Separator()
    _apply_common(s, margin=margin)
    return s


def text(content, *, size="body", bold=False, color="primary", wrap=False, margin=None):
    from System.Windows.Controls import TextBlock

    tb = TextBlock()
    tb.Text = str(content)
    # SetResourceReference (not a direct value assignment) so this text keeps
    # tracking theme/accent changes live, the same way {DynamicResource} does in XAML.
    tb.SetResourceReference(TextBlock.FontFamilyProperty, "Pane.Font.Family")
    tb.SetResourceReference(TextBlock.FontSizeProperty, _FONT_SIZE_KEYS.get(size, _FONT_SIZE_KEYS["body"]))
    tb.SetResourceReference(TextBlock.ForegroundProperty, _TEXT_COLOR_KEYS.get(color, _TEXT_COLOR_KEYS["primary"]))
    if bold:
        tb.FontWeight = FontWeights.SemiBold
    if wrap:
        tb.TextWrapping = TextWrapping.Wrap
    _apply_common(tb, margin=margin)
    return tb


def set_tooltip(element, tooltip_text):
    element.ToolTip = tooltip_text
    return element


def set_context_menu(element, items):
    """items: a list of (label, on_click) pairs; use None for a separator."""
    from System.Windows.Controls import ContextMenu, MenuItem, Separator

    menu = ContextMenu()
    for item in items:
        if item is None:
            menu.Items.Add(Separator())
            continue
        label, on_click = item
        mi = MenuItem()
        mi.Header = label
        if on_click:
            mi.Click += make_handler(on_click, lambda: None)
        menu.Items.Add(mi)
    element.ContextMenu = menu
    return element

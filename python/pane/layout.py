"""Layout container helpers: stack, grid, card, scroll."""

from . import _bootstrap

_bootstrap.ensure_loaded()

from System.Windows import GridLength, GridUnitType, Thickness  # noqa: E402

from ._convert import to_thickness  # noqa: E402
from .widgets import _find_style  # noqa: E402


def stack(*children, orientation="vertical", spacing=0, margin=None):
    from System.Windows.Controls import Orientation, StackPanel

    panel = StackPanel()
    panel.Orientation = Orientation.Vertical if orientation == "vertical" else Orientation.Horizontal
    if margin is not None:
        panel.Margin = to_thickness(margin)

    for i, child in enumerate(children):
        if spacing and i > 0:
            m = child.Margin
            if orientation == "vertical":
                child.Margin = Thickness(m.Left, spacing, m.Right, m.Bottom)
            else:
                child.Margin = Thickness(spacing, m.Top, m.Right, m.Bottom)
        panel.Children.Add(child)
    return panel


def _parse_length(value):
    if value == "auto":
        return GridLength(1, GridUnitType.Auto)
    if isinstance(value, str) and value.endswith("*"):
        factor = 1.0 if value == "*" else float(value[:-1])
        return GridLength(factor, GridUnitType.Star)
    return GridLength(float(value), GridUnitType.Pixel)


def grid(children, *, rows=None, columns=None, margin=None):
    """
    children: a list of (row, col, widget) or (row, col, widget, row_span, col_span) tuples.
    rows / columns: lists of "auto", "*", "2*", or a pixel size, e.g. rows=["auto", "*"].
    """
    from System.Windows.Controls import ColumnDefinition, Grid, RowDefinition

    g = Grid()
    for r in rows or ["auto"]:
        rd = RowDefinition()
        rd.Height = _parse_length(r)
        g.RowDefinitions.Add(rd)
    for c in columns or ["auto"]:
        cd = ColumnDefinition()
        cd.Width = _parse_length(c)
        g.ColumnDefinitions.Add(cd)

    for entry in children:
        row, col, widget = entry[0], entry[1], entry[2]
        row_span = entry[3] if len(entry) > 3 else 1
        col_span = entry[4] if len(entry) > 4 else 1
        Grid.SetRow(widget, row)
        Grid.SetColumn(widget, col)
        if row_span > 1:
            Grid.SetRowSpan(widget, row_span)
        if col_span > 1:
            Grid.SetColumnSpan(widget, col_span)
        g.Children.Add(widget)

    if margin is not None:
        g.Margin = to_thickness(margin)
    return g


def card(*children, padding=20, spacing=12, orientation="vertical", margin=None):
    from System.Windows.Controls import Border

    border = Border()
    border.Style = _find_style("Pane.Card")
    if padding is not None:
        border.Padding = to_thickness(padding)
    if margin is not None:
        border.Margin = to_thickness(margin)
    border.Child = stack(*children, orientation=orientation, spacing=spacing)
    return border


def sidebar(*children, width=240):
    from System.Windows.Controls import DockPanel

    border_style = _find_style("Pane.Sidebar")
    from System.Windows.Controls import Border

    border = Border()
    border.Style = border_style
    border.Width = width

    panel = DockPanel()
    panel.LastChildFill = True
    for child in children:
        panel.Children.Add(child)
    border.Child = panel
    return border


def scroll(child, *, padding=None):
    from System.Windows.Controls import ScrollViewer

    sv = ScrollViewer()
    sv.Content = child
    if padding is not None:
        sv.Padding = to_thickness(padding)
    return sv

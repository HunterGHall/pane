using System.Windows;
using System.Windows.Input;

namespace Pane.Controls;

/// <summary>
/// Marks an element as the window's drag region: click-drag moves the window, double-click
/// toggles maximize/restore. Used instead of WindowChrome.IsHitTestVisibleInChrome, which
/// does not reliably exempt caption-area buttons from the native caption hit-test in all
/// environments - this keeps drag/maximize behavior in ordinary WPF input handling instead,
/// so buttons placed in the title bar just work like buttons anywhere else.
/// </summary>
public static class DragHandle
{
    public static readonly DependencyProperty IsEnabledProperty =
        DependencyProperty.RegisterAttached("IsEnabled", typeof(bool), typeof(DragHandle), new PropertyMetadata(false, OnIsEnabledChanged));

    public static bool GetIsEnabled(DependencyObject obj) => (bool)obj.GetValue(IsEnabledProperty);
    public static void SetIsEnabled(DependencyObject obj, bool value) => obj.SetValue(IsEnabledProperty, value);

    private static void OnIsEnabledChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is not UIElement element)
        {
            return;
        }

        element.PreviewMouseLeftButtonDown -= OnMouseLeftButtonDown;

        if ((bool)e.NewValue)
        {
            element.PreviewMouseLeftButtonDown += OnMouseLeftButtonDown;
        }
    }

    private static void OnMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (sender is not DependencyObject element || Window.GetWindow(element) is not Window window)
        {
            return;
        }

        if (e.ClickCount == 2)
        {
            window.WindowState = window.WindowState == WindowState.Maximized
                ? WindowState.Normal
                : WindowState.Maximized;
            return;
        }

        if (window.WindowState == WindowState.Maximized)
        {
            // Restore-then-drag makes the window follow the cursor immediately, matching
            // the native behavior of dragging a maximized window's title bar.
            var mouseAbsolute = window.PointToScreen(Mouse.GetPosition(window));
            var ratioX = Mouse.GetPosition(window).X / window.ActualWidth;

            window.WindowState = WindowState.Normal;
            window.Left = mouseAbsolute.X - (window.Width * ratioX);
            window.Top = 0;
        }

        window.DragMove();
    }
}

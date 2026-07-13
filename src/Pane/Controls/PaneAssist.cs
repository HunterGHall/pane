using System.Windows;

namespace Pane.Controls;

/// <summary>Attached properties that add small template-level conveniences to stock WPF controls.</summary>
public static class PaneAssist
{
    public static readonly DependencyProperty PlaceholderProperty =
        DependencyProperty.RegisterAttached("Placeholder", typeof(string), typeof(PaneAssist), new PropertyMetadata(string.Empty));

    public static string GetPlaceholder(DependencyObject obj) => (string)obj.GetValue(PlaceholderProperty);
    public static void SetPlaceholder(DependencyObject obj, string value) => obj.SetValue(PlaceholderProperty, value);
}

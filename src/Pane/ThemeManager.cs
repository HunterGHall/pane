using System.Windows;
using System.Windows.Media;

namespace Pane;

public enum PaneTheme
{
    Dark,
    Light
}

/// <summary>
/// Swaps Pane's color resource dictionary at runtime so every DynamicResource-bound
/// brush in the control templates repaints immediately, with no window restart.
/// </summary>
public static class ThemeManager
{
    private static readonly Uri DarkUri = new("pack://application:,,,/Pane;component/Themes/Colors.Dark.xaml");
    private static readonly Uri LightUri = new("pack://application:,,,/Pane;component/Themes/Colors.Light.xaml");

    public static PaneTheme CurrentTheme { get; private set; } = PaneTheme.Dark;

    /// <summary>The last color passed to SetAccentColor, if any - reapplied automatically on theme switches.</summary>
    public static Color? CustomAccent { get; private set; }

    public static event EventHandler<PaneTheme>? ThemeChanged;

    /// <summary>Call once from App startup after merging Themes/Pane.xaml.</summary>
    public static void Initialize(PaneTheme theme = PaneTheme.Dark) => SetTheme(theme);

    public static void SetTheme(PaneTheme theme)
    {
        var app = Application.Current ?? throw new InvalidOperationException("ThemeManager requires an active Application.");
        var newUri = theme == PaneTheme.Dark ? DarkUri : LightUri;
        var themeDict = new ResourceDictionary { Source = newUri };

        // Colors.*.xaml is nested inside Themes/Pane.xaml, and swapping a dictionary that
        // deep in the MergedDictionaries graph doesn't reliably invalidate DynamicResource
        // consumers. Copying its keys directly onto the live, owned Application.Resources
        // dictionary does - local keys always win over merged-dictionary keys, and direct
        // assignment on an owned dictionary is guaranteed to trigger invalidation.
        foreach (object key in themeDict.Keys)
        {
            app.Resources[key] = themeDict[key];
        }

        CurrentTheme = theme;

        // The theme dictionary just overwrote the accent brushes with the theme's default -
        // reapply any user-chosen accent so switching light/dark doesn't silently reset it.
        if (CustomAccent is { } accent)
        {
            ApplyAccentColor(accent);
        }

        ThemeChanged?.Invoke(null, theme);
    }

    public static void ToggleTheme() => SetTheme(CurrentTheme == PaneTheme.Dark ? PaneTheme.Light : PaneTheme.Dark);

    /// <summary>
    /// Overrides the accent color (and its derived hover/pressed/subtle shades) without
    /// touching the light/dark surface palette. Values are written directly onto
    /// Application.Resources so they take precedence over the merged theme dictionaries.
    /// Persists across SetTheme calls until a new accent - or ResetAccentColor - is applied.
    /// </summary>
    public static void SetAccentColor(Color accent)
    {
        CustomAccent = accent;
        ApplyAccentColor(accent);
    }

    /// <summary>Drops back to the current theme's default accent color.</summary>
    public static void ResetAccentColor()
    {
        CustomAccent = null;
        SetTheme(CurrentTheme);
    }

    private static void ApplyAccentColor(Color accent)
    {
        var app = Application.Current ?? throw new InvalidOperationException("ThemeManager requires an active Application.");
        var resources = app.Resources;

        resources["Pane.Brush.Accent.Default"] = Freeze(new SolidColorBrush(accent));
        resources["Pane.Brush.Accent.Hover"] = Freeze(new SolidColorBrush(Blend(accent, Colors.White, 0.15)));
        resources["Pane.Brush.Accent.Pressed"] = Freeze(new SolidColorBrush(Blend(accent, Colors.Black, 0.18)));
        resources["Pane.Brush.Accent.Subtle"] = Freeze(new SolidColorBrush(Color.FromArgb(0x29, accent.R, accent.G, accent.B)));
    }

    private static Color Blend(Color baseColor, Color target, double amount)
    {
        byte R(byte a, byte b) => (byte)(a + (b - a) * amount);
        return Color.FromRgb(R(baseColor.R, target.R), R(baseColor.G, target.G), R(baseColor.B, target.B));
    }

    private static SolidColorBrush Freeze(SolidColorBrush brush)
    {
        brush.Freeze();
        return brush;
    }
}

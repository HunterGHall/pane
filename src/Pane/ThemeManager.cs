using System.Windows;
using System.Windows.Media;
using Microsoft.Win32;

namespace Pane;

public enum PaneTheme
{
    Dark,
    Light
}

/// <summary>
/// What ThemeManager was last told to do: pin to Light/Dark explicitly, or continuously
/// follow the Windows "choose your color" setting. CurrentTheme always holds the resolved
/// Light/Dark value - in System mode that's whatever Windows currently reports, kept live.
/// </summary>
public enum PaneThemeMode
{
    Light,
    Dark,
    System
}

/// <summary>
/// Swaps Pane's color resource dictionary at runtime so every DynamicResource-bound
/// brush in the control templates repaints immediately, with no window restart.
/// </summary>
public static class ThemeManager
{
    private const string PersonalizeKey = @"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize";
    private const string AppsUseLightThemeValue = "AppsUseLightTheme";

    private static readonly Uri DarkUri = new("pack://application:,,,/Pane;component/Themes/Colors.Dark.xaml");
    private static readonly Uri LightUri = new("pack://application:,,,/Pane;component/Themes/Colors.Light.xaml");

    private static bool _followingSystem;

    public static PaneTheme CurrentTheme { get; private set; } = PaneTheme.Dark;

    /// <summary>What was last requested: Light, Dark, or System. Differs from CurrentTheme
    /// only in System mode, where CurrentTheme is whatever that resolves to right now.</summary>
    public static PaneThemeMode Mode { get; private set; } = PaneThemeMode.Dark;

    /// <summary>The last color passed to SetAccentColor, if any - reapplied automatically on theme switches.</summary>
    public static Color? CustomAccent { get; private set; }

    /// <summary>The last palette passed to SetCustomTheme, if any - reapplied automatically on theme switches.</summary>
    public static PaneThemeColors? CustomColors { get; private set; }

    public static event EventHandler<PaneTheme>? ThemeChanged;

    /// <summary>Call once from App startup after merging Themes/Pane.xaml.</summary>
    public static void Initialize(PaneTheme theme = PaneTheme.Dark) => SetTheme(theme);

    /// <summary>Call once from App startup instead of Initialize(PaneTheme) to start out
    /// following the Windows light/dark setting (PaneThemeMode.System) - see SetThemeMode.</summary>
    public static void Initialize(PaneThemeMode mode) => SetThemeMode(mode);

    /// <summary>Sets an explicit theme. Like any explicit choice, this opts out of
    /// PaneThemeMode.System if it was active - see SetThemeMode to go back to following Windows.</summary>
    public static void SetTheme(PaneTheme theme) => SetTheme(theme, preserveMode: false);

    /// <summary>
    /// Light/Dark pins the theme explicitly, same as SetTheme. System continuously follows
    /// the Windows "choose your color" setting: it's applied immediately, and again live
    /// every time that setting changes, until SetThemeMode/SetTheme/ToggleTheme picks
    /// something else.
    /// </summary>
    public static void SetThemeMode(PaneThemeMode mode)
    {
        Mode = mode;
        if (mode == PaneThemeMode.System)
        {
            StartFollowingSystem();
            SetTheme(ReadSystemTheme(), preserveMode: true);
        }
        else
        {
            StopFollowingSystem();
            SetTheme(mode == PaneThemeMode.Dark ? PaneTheme.Dark : PaneTheme.Light, preserveMode: true);
        }
    }

    private static void SetTheme(PaneTheme theme, bool preserveMode)
    {
        if (!preserveMode)
        {
            Mode = theme == PaneTheme.Dark ? PaneThemeMode.Dark : PaneThemeMode.Light;
            StopFollowingSystem();
        }

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

        // The theme dictionary just overwrote the palette/accent brushes with the theme's
        // defaults - reapply any user overrides so switching light/dark (including a live
        // System-mode switch) doesn't silently reset them.
        if (CustomColors is { } colors)
        {
            ApplyCustomColors(colors);
        }
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
    /// Persists across SetTheme/SetThemeMode calls until a new accent - or ResetAccentColor - is applied.
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
        SetTheme(CurrentTheme, preserveMode: true);
    }

    /// <summary>
    /// Overrides any subset of Pane's surface/text/border/state/semantic palette - and,
    /// optionally, the accent color - on top of whatever the current Light/Dark theme
    /// already provides. Fields left null on <paramref name="colors"/> keep the current
    /// theme's default for that slot. Persists across SetTheme/SetThemeMode calls
    /// (including live System-mode switches) until ResetCustomTheme.
    /// </summary>
    public static void SetCustomTheme(PaneThemeColors colors)
    {
        CustomColors = colors;
        ApplyCustomColors(colors);
    }

    /// <summary>Drops back to the current theme's default palette. Leaves a separately-set
    /// accent color (SetAccentColor, or Accent on a previous SetCustomTheme) untouched -
    /// call ResetAccentColor too if you want that back to the theme default as well.</summary>
    public static void ResetCustomTheme()
    {
        CustomColors = null;
        SetTheme(CurrentTheme, preserveMode: true);
    }

    private static void ApplyCustomColors(PaneThemeColors colors)
    {
        var app = Application.Current ?? throw new InvalidOperationException("ThemeManager requires an active Application.");
        var resources = app.Resources;

        void Set(string key, Color? value)
        {
            if (value is { } c)
            {
                resources[key] = Freeze(new SolidColorBrush(c));
            }
        }

        Set("Pane.Brush.Background.Window", colors.Window);
        Set("Pane.Brush.Background.Surface", colors.Surface);
        Set("Pane.Brush.Background.SurfaceAlt", colors.SurfaceAlt);
        Set("Pane.Brush.Background.Elevated", colors.Elevated);

        Set("Pane.Brush.Border.Default", colors.BorderDefault);
        Set("Pane.Brush.Border.Subtle", colors.BorderSubtle);
        Set("Pane.Brush.Border.Strong", colors.BorderStrong);

        Set("Pane.Brush.Text.Primary", colors.TextPrimary);
        Set("Pane.Brush.Text.Secondary", colors.TextSecondary);
        Set("Pane.Brush.Text.Disabled", colors.TextDisabled);
        Set("Pane.Brush.Text.OnAccent", colors.TextOnAccent);

        Set("Pane.Brush.State.Hover", colors.StateHover);
        Set("Pane.Brush.State.Pressed", colors.StatePressed);
        Set("Pane.Brush.State.DisabledBackground", colors.StateDisabledBackground);

        Set("Pane.Brush.Success", colors.Success);
        Set("Pane.Brush.Warning", colors.Warning);
        Set("Pane.Brush.Danger", colors.Danger);

        // Applied last so it always reflects this call's Accent, regardless of whether an
        // older CustomAccent (from a plain SetAccentColor call) was already set.
        if (colors.Accent is { } accent)
        {
            CustomAccent = accent;
            ApplyAccentColor(accent);
        }
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

    // --- System theme tracking ---------------------------------------------------------

    private static void StartFollowingSystem()
    {
        if (_followingSystem)
        {
            return;
        }
        _followingSystem = true;
        SystemEvents.UserPreferenceChanged += OnUserPreferenceChanged;
    }

    private static void StopFollowingSystem()
    {
        if (!_followingSystem)
        {
            return;
        }
        _followingSystem = false;
        SystemEvents.UserPreferenceChanged -= OnUserPreferenceChanged;
    }

    private static void OnUserPreferenceChanged(object? sender, UserPreferenceChangedEventArgs e)
    {
        // The light/dark app-mode setting reports its changes under General, along with a
        // handful of unrelated settings - cheap enough to just re-read the registry value
        // and compare rather than trying to filter more precisely than that.
        if (e.Category != UserPreferenceCategory.General)
        {
            return;
        }

        var resolved = ReadSystemTheme();
        if (resolved == CurrentTheme)
        {
            return;
        }

        // SystemEvents raises this on its own dedicated message-loop thread, not necessarily
        // the WPF UI thread - every Application.Current.Resources write has to happen there.
        var app = Application.Current;
        if (app is null)
        {
            return;
        }
        app.Dispatcher.Invoke(() => SetTheme(resolved, preserveMode: true));
    }

    private static PaneTheme ReadSystemTheme()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(PersonalizeKey);
            if (key?.GetValue(AppsUseLightThemeValue) is int appsUseLightTheme)
            {
                return appsUseLightTheme == 0 ? PaneTheme.Dark : PaneTheme.Light;
            }
        }
        catch (Exception)
        {
            // Registry unavailable/locked down (e.g. a restricted sandbox) - fall back below
            // rather than let a theme lookup take the whole app down.
        }
        return PaneTheme.Dark;
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

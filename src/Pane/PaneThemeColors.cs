using System.Windows.Media;

namespace Pane;

/// <summary>
/// A partial override of Pane's color palette, on top of whatever the current Light/Dark
/// theme already provides. Pass one of these to <see cref="ThemeManager.SetCustomTheme"/>;
/// every property left null keeps the current theme's default for that slot, so you only
/// need to set the handful of colors you actually want to change.
///
/// Plain mutable properties (not init-only) so the type can be built up from Python via
/// pythonnet just as easily as from C# with an object initializer.
/// </summary>
public sealed class PaneThemeColors
{
    public Color? Window { get; set; }
    public Color? Surface { get; set; }
    public Color? SurfaceAlt { get; set; }
    public Color? Elevated { get; set; }

    public Color? BorderDefault { get; set; }
    public Color? BorderSubtle { get; set; }
    public Color? BorderStrong { get; set; }

    public Color? TextPrimary { get; set; }
    public Color? TextSecondary { get; set; }
    public Color? TextDisabled { get; set; }
    public Color? TextOnAccent { get; set; }

    /// <summary>Convenience: setting this also drives SetAccentColor's derived hover/pressed/subtle shades,
    /// same as calling ThemeManager.SetAccentColor(value) separately.</summary>
    public Color? Accent { get; set; }

    public Color? StateHover { get; set; }
    public Color? StatePressed { get; set; }
    public Color? StateDisabledBackground { get; set; }

    public Color? Success { get; set; }
    public Color? Warning { get; set; }
    public Color? Danger { get; set; }
}

using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Pane;

namespace Pane.Template;

public partial class MainWindow : PaneWindow
{
    // Guards against ThemeToggle_Checked/Unchecked re-entering ThemeManager while we're
    // only syncing its visual state to a live system-theme change, not reacting to a click.
    private bool _syncingThemeToggle;

    public MainWindow()
    {
        InitializeComponent();
        ThemeManager.ThemeChanged += OnThemeChanged;
        Closed += (_, _) => ThemeManager.ThemeChanged -= OnThemeChanged;
    }

    private void OnThemeChanged(object? sender, PaneTheme theme)
    {
        _syncingThemeToggle = true;
        ThemeToggle.IsChecked = theme == PaneTheme.Dark;
        _syncingThemeToggle = false;
    }

    private void NavList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (NavList.SelectedItem is ListBoxItem { Tag: FrameworkElement target })
        {
            target.BringIntoView();
        }
    }

    private void SystemThemeToggle_Checked(object sender, RoutedEventArgs e)
    {
        ThemeToggle.IsEnabled = false;
        ThemeManager.SetThemeMode(PaneThemeMode.System);
    }

    private void SystemThemeToggle_Unchecked(object sender, RoutedEventArgs e)
    {
        ThemeToggle.IsEnabled = true;
        ThemeManager.SetThemeMode(ThemeToggle.IsChecked == true ? PaneThemeMode.Dark : PaneThemeMode.Light);
    }

    private void ThemeToggle_Checked(object sender, RoutedEventArgs e)
    {
        if (_syncingThemeToggle)
        {
            return;
        }
        ThemeManager.SetTheme(PaneTheme.Dark);
    }

    private void ThemeToggle_Unchecked(object sender, RoutedEventArgs e)
    {
        if (_syncingThemeToggle)
        {
            return;
        }
        ThemeManager.SetTheme(PaneTheme.Light);
    }

    private void AccentSwatch_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button { Background: SolidColorBrush brush })
        {
            ThemeManager.SetAccentColor(brush.Color);
        }
    }
}

using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Pane;

namespace Pane.Template;

public partial class MainWindow : PaneWindow
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private void NavList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (NavList.SelectedItem is ListBoxItem { Tag: FrameworkElement target })
        {
            target.BringIntoView();
        }
    }

    private void ThemeToggle_Checked(object sender, RoutedEventArgs e) => ThemeManager.SetTheme(PaneTheme.Dark);

    private void ThemeToggle_Unchecked(object sender, RoutedEventArgs e) => ThemeManager.SetTheme(PaneTheme.Light);

    private void AccentSwatch_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button { Background: SolidColorBrush brush })
        {
            ThemeManager.SetAccentColor(brush.Color);
        }
    }
}

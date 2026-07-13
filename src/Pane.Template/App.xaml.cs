using System.Windows;
using Pane;

namespace Pane.Template;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ThemeManager.Initialize(PaneTheme.Dark);
    }
}

# Pane

A modern, minimalist Windows UI engine built on WPF. Pane restyles the
standard WPF controls into a clean, modern look (inspired by the Claude
desktop app), with a custom borderless window chrome, live light/dark
theming, and runtime accent-color switching — as a reusable class library
and a starter template, not a framework you have to fight.



## What's in this repo

- **[`src/Pane`](src/Pane)** — the engine. A WPF class library with themed
  styles for every common control (buttons, checkboxes, sliders, text input,
  tabs, menus, tooltips, chat bubbles, ...), a `ThemeManager` for runtime
  light/dark and accent-color switching, and a `PaneWindow` base class with
  custom chrome (drag, minimize/maximize/restore/close, proper multi-monitor
  maximize).
- **[`src/Pane.Template`](src/Pane.Template)** — a starter WPF app referencing
  the engine, with a full widget gallery you can trim down to what you need.
- **[`python/`](python)** — Python bindings (`pip install pane-ui`) that
  build and drive the same native WPF controls in-process via
  [pythonnet](https://pythonnet.github.io/), no C# required.

## Using it from C#/WPF

```xml
<!-- App.xaml -->
<Application.Resources>
    <ResourceDictionary>
        <ResourceDictionary.MergedDictionaries>
            <ResourceDictionary Source="pack://application:,,,/Pane;component/Themes/Pane.xaml" />
        </ResourceDictionary.MergedDictionaries>
    </ResourceDictionary>
</Application.Resources>
```

```csharp
// App.xaml.cs
protected override void OnStartup(StartupEventArgs e)
{
    base.OnStartup(e);
    ThemeManager.Initialize(PaneTheme.Dark);
}
```

```xml
<!-- MainWindow.xaml -->
<pane:PaneWindow x:Class="MyApp.MainWindow" ...>
    <Button Content="Primary" Style="{StaticResource Pane.Button.Primary}" />
</pane:PaneWindow>
```

See [`src/Pane.Template/MainWindow.xaml`](src/Pane.Template/MainWindow.xaml)
for a complete example covering every widget.

Build and run the template:

```
dotnet build Pane.sln
dotnet run --project src/Pane.Template
```

## Using it from Python

```
pip install pane-ui
```

```python
import pane

def build(window):
    window.Content = pane.stack(
        pane.text("Hello from Python", size="title", bold=True),
        pane.button("Click me", style="primary", on_click=lambda: print("clicked!")),
        spacing=12, margin=24,
    )

pane.run(build, title="My App")
```

See [`python/README.md`](python/README.md) for the full Python API.

## Theming

```csharp
ThemeManager.SetTheme(PaneTheme.Light);
ThemeManager.SetAccentColor(Color.FromRgb(0x4C, 0x82, 0xF7));
```

```python
pane.set_theme("light")
pane.set_accent("#4C82F7")
```

Every widget re-themes live, mid-run — no restart needed either way.

## Requirements

- Windows 10/11
- .NET 8 Desktop Runtime (SDK only needed if building from source)
- For the Python bindings: Python 3.9+

## License

MIT — see [LICENSE](LICENSE).

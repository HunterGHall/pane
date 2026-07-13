using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;

namespace Pane;

/// <summary>
/// Base class for windows using the Pane.Window style. SystemCommands (minimize/maximize/
/// restore/close) require a CommandBinding to actually execute, and CommandBindings isn't a
/// styleable property, so it has to be registered here in code rather than in the Style.
/// It also fixes the classic WindowStyle="None" + maximize bug where the window expands over
/// the taskbar: without this hook, Windows maximizes borderless windows to the full monitor
/// bounds instead of the work area.
/// </summary>
public class PaneWindow : Window
{
    public PaneWindow()
    {
        CommandBindings.Add(new CommandBinding(SystemCommands.MinimizeWindowCommand, (_, _) => SystemCommands.MinimizeWindow(this)));
        CommandBindings.Add(new CommandBinding(SystemCommands.MaximizeWindowCommand, (_, _) => SystemCommands.MaximizeWindow(this)));
        CommandBindings.Add(new CommandBinding(SystemCommands.RestoreWindowCommand, (_, _) => SystemCommands.RestoreWindow(this)));
        CommandBindings.Add(new CommandBinding(SystemCommands.CloseWindowCommand, (_, _) => SystemCommands.CloseWindow(this)));

        Style = (Style)FindResource("Pane.Window");
    }

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);

        if (PresentationSource.FromVisual(this) is HwndSource hwndSource)
        {
            hwndSource.AddHook(WindowProc);
        }
    }

    private static IntPtr WindowProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        const int WM_GETMINMAXINFO = 0x0024;

        if (msg == WM_GETMINMAXINFO)
        {
            ConstrainMaximizedSizeToWorkArea(hwnd, lParam);
            handled = true;
        }

        return IntPtr.Zero;
    }

    private static void ConstrainMaximizedSizeToWorkArea(IntPtr hwnd, IntPtr lParam)
    {
        var mmi = Marshal.PtrToStructure<MINMAXINFO>(lParam);

        const uint MONITOR_DEFAULTTONEAREST = 0x00000002;
        var monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);

        if (monitor != IntPtr.Zero)
        {
            var monitorInfo = new MONITORINFO();
            monitorInfo.cbSize = Marshal.SizeOf<MONITORINFO>();
            GetMonitorInfo(monitor, ref monitorInfo);

            var workArea = monitorInfo.rcWork;
            var monitorArea = monitorInfo.rcMonitor;

            mmi.ptMaxPosition.X = workArea.Left - monitorArea.Left;
            mmi.ptMaxPosition.Y = workArea.Top - monitorArea.Top;
            mmi.ptMaxSize.X = workArea.Right - workArea.Left;
            mmi.ptMaxSize.Y = workArea.Bottom - workArea.Top;
        }

        Marshal.StructureToPtr(mmi, lParam, true);
    }

    [DllImport("user32.dll")]
    private static extern IntPtr MonitorFromWindow(IntPtr handle, uint flags);

    [DllImport("user32.dll")]
    private static extern bool GetMonitorInfo(IntPtr hMonitor, ref MONITORINFO lpmi);

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT
    {
        public int X;
        public int Y;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MINMAXINFO
    {
        public POINT ptReserved;
        public POINT ptMaxSize;
        public POINT ptMaxPosition;
        public POINT ptMinTrackSize;
        public POINT ptMaxTrackSize;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MONITORINFO
    {
        public int cbSize;
        public RECT rcMonitor;
        public RECT rcWork;
        public uint dwFlags;
    }
}

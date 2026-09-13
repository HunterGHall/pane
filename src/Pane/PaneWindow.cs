using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;

namespace Pane;

/// <summary>
/// Base class for windows using the Pane.Window style. SystemCommands (minimize/maximize/
/// restore/close) require a CommandBinding to actually execute, and CommandBindings isn't a
/// styleable property, so it has to be registered here in code rather than in the Style.
/// It also fixes two classic WindowStyle="None" + maximize bugs: without this hook, Windows
/// maximizes borderless windows to the full monitor bounds instead of the work area (covering
/// the taskbar), and separately still reserves its standard resize-frame margin around a
/// maximized borderless window even though nothing is drawn there - leaving the window short
/// of the true screen edges by that margin (~8px at 100% DPI) on every side, so edge-pinned
/// controls like a top-right close button end up unreachable in the actual corner.
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

            // For a WS_THICKFRAME (resizable) window, Windows positions a maximized
            // window itself using its own frame-margin math and ignores whatever
            // ptMaxPosition says here (measured: requesting 0 here still results in
            // an actual position of -frameX/-frameY - Windows' own default, not
            // ours) - but it does honor ptMaxSize exactly as given. Net effect
            // without compensating: the window's top/left sit frameX/frameY off
            // the true screen edges (harmless, off-screen) while its right/bottom
            // edges fall the same amount *short* of the true work-area edges (the
            // classic "8px gap" borderless-WPF-maximize bug - the window looks
            // maximized but doesn't quite reach the screen edges, and edge-pinned
            // controls like a top-right close button end up sitting short of where
            // a user's mouse actually reaches). Adding that same margin once to
            // ptMaxSize (position is left as the plain work-area-relative value -
            // adjusting it further has no effect, per the above) grows the window
            // by exactly enough to cancel the gap back out on the far edges.
            int frameX = GetSystemMetrics(SM_CXSIZEFRAME) + GetSystemMetrics(SM_CXPADDEDBORDER);
            int frameY = GetSystemMetrics(SM_CYSIZEFRAME) + GetSystemMetrics(SM_CXPADDEDBORDER);

            mmi.ptMaxPosition.X = workArea.Left - monitorArea.Left;
            mmi.ptMaxPosition.Y = workArea.Top - monitorArea.Top;
            mmi.ptMaxSize.X = (workArea.Right - workArea.Left) + frameX;
            mmi.ptMaxSize.Y = (workArea.Bottom - workArea.Top) + frameY;
        }

        Marshal.StructureToPtr(mmi, lParam, true);
    }

    private const int SM_CXSIZEFRAME = 32;
    private const int SM_CYSIZEFRAME = 33;
    private const int SM_CXPADDEDBORDER = 92;

    [DllImport("user32.dll")]
    private static extern IntPtr MonitorFromWindow(IntPtr handle, uint flags);

    [DllImport("user32.dll")]
    private static extern bool GetMonitorInfo(IntPtr hMonitor, ref MONITORINFO lpmi);

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int nIndex);

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

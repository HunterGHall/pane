"""The entry point for building and running a Pane UI from Python."""

import threading

from . import _bootstrap

_bootstrap.ensure_loaded()

from Pane import PaneTheme, PaneWindow, ThemeManager  # noqa: E402
from System import Action, Uri  # noqa: E402
from System.Threading import ApartmentState, Thread  # noqa: E402
from System.Threading import ThreadStart  # noqa: E402
from System.Windows import Application, ResizeMode, ResourceDictionary  # noqa: E402

_PANE_XAML_URI = "pack://application:,,,/Pane;component/Themes/Pane.xaml"

_state = {
    "app": None,
    "window": None,
    "dispatcher": None,
    "ui_thread_id": None,
}


def is_ui_thread():
    return threading.get_ident() == _state["ui_thread_id"]


def invoke(fn):
    """Runs fn on the UI thread and returns its result, blocking the caller.
    Safe to call from any thread, including the UI thread itself."""
    if _state["dispatcher"] is None:
        raise RuntimeError("The Pane UI is not running - call pane.run() first")
    if is_ui_thread():
        return fn()

    box = {}

    def wrapper():
        box["result"] = fn()

    _state["dispatcher"].Invoke(Action(wrapper))
    return box.get("result")


def current_window():
    return _state["window"]


def close():
    """Closes the running window. Safe to call from any thread."""
    invoke(lambda: _state["window"].Close())


def run(builder, *, title="Pane App", width=1000, height=700, theme="dark", resizable=True):
    """
    Builds and shows a window, then blocks the calling thread until it's closed.

    `builder(window)` runs on the dedicated UI thread before the window is
    shown - build your widget tree there and assign it to `window.Content`.
    Use pane.button(...), pane.stack(...), etc. only inside `builder` (or
    inside a callback that pane.invoke()s back onto the UI thread).
    """
    ready = threading.Event()
    error_box = {}

    def ui_main():
        try:
            app = Application()
            _state["app"] = app

            # App.xaml normally does this merge declaratively; a bare Application()
            # built from Python has no resources until we merge Pane.xaml ourselves.
            merged = ResourceDictionary()
            merged.Source = Uri(_PANE_XAML_URI)
            app.Resources.MergedDictionaries.Add(merged)

            ThemeManager.Initialize(PaneTheme.Dark if theme == "dark" else PaneTheme.Light)

            window = PaneWindow()
            window.Title = title
            window.Width = width
            window.Height = height
            if not resizable:
                window.ResizeMode = ResizeMode.NoResize

            _state["window"] = window
            _state["dispatcher"] = window.Dispatcher
            _state["ui_thread_id"] = threading.get_ident()

            builder(window)

            ready.set()
            app.Run(window)
        except Exception as ex:  # noqa: BLE001 - surfaced to the caller below
            error_box["error"] = ex
            ready.set()
        finally:
            _state["app"] = None
            _state["window"] = None
            _state["dispatcher"] = None
            _state["ui_thread_id"] = None

    thread = Thread(ThreadStart(ui_main))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()

    ready.wait()
    if "error" in error_box:
        raise error_box["error"]

    thread.Join()

"""
Internal: loads the CLR runtime and the Pane assembly exactly once.

This is the only module that knows about pythonnet/clr - everything else in
the package imports .NET types lazily, after ensure_loaded() has run.
"""

import os
import sys
import threading

_initialized = False
_lock = threading.Lock()


def _find_build_output():
    """Locate Pane.dll plus the runtimeconfig.json CoreCLR needs to host the
    WPF shared framework. Prefers the bundled copy shipped inside this
    installed package; falls back to a locally built dev-repo output so
    `pip install -e .` from a source checkout works without a separate
    packaging step."""
    here = os.path.dirname(os.path.abspath(__file__))

    bundled_dir = os.path.join(here, "_native")
    bundled_config = os.path.join(bundled_dir, "Pane.runtimeconfig.json")
    if os.path.exists(bundled_config):
        return bundled_dir, bundled_config

    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    dev_candidates = [
        os.path.join(repo_root, "src", "Pane.Template", "bin", "Debug", "net8.0-windows"),
        os.path.join(repo_root, "src", "Pane.Template", "bin", "Release", "net8.0-windows"),
    ]
    for candidate in dev_candidates:
        config = os.path.join(candidate, "Pane.Template.runtimeconfig.json")
        if os.path.exists(config):
            return candidate, config

    raise RuntimeError(
        "Could not find Pane.dll. If you're developing from source, run "
        "`dotnet build Pane.sln` in the repo root first. If you installed via "
        "pip, this package build is missing its bundled native files."
    )


def ensure_loaded():
    global _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return

        if sys.platform != "win32":
            raise ImportError(
                "pane only runs on Windows - it's built on WPF, which has no "
                "cross-platform equivalent."
            )

        bin_dir, runtimeconfig = _find_build_output()

        from pythonnet import load
        try:
            load("coreclr", runtime_config=runtimeconfig)
        except Exception as ex:
            raise RuntimeError(
                "pane couldn't start the .NET runtime. This usually means the "
                ".NET 8 Desktop Runtime isn't installed - get it from "
                "https://dotnet.microsoft.com/download/dotnet/8.0 "
                "(the \"Desktop Runtime\" download for your platform, not the SDK) "
                "and try again."
            ) from ex

        import clr
        sys.path.append(bin_dir)
        clr.AddReference("Pane")
        clr.AddReference("PresentationFramework")
        clr.AddReference("PresentationCore")
        clr.AddReference("WindowsBase")

        # WPF's pack:// URI scheme (used everywhere Pane loads its own XAML
        # resource dictionaries) is registered lazily inside PackUriHelper's
        # static constructor. In a normal WPF .exe that happens automatically
        # during app startup; hosted from Python it never runs on its own, so
        # the first pack:// Uri construction throws UriFormatException:
        # "Invalid port specified". Touching PackUriHelper once, up front,
        # forces that registration before any Pane code needs it.
        from System.IO.Packaging import PackUriHelper
        from System import Uri
        PackUriHelper.Create(Uri("http://pane-bootstrap/"))

        _initialized = True

"""PyInstaller runtime hook for pyiec61850.

Executed early during frozen-app startup to configure DLL search paths
so that iec61850.dll (or libiec61850.so) can be found by _pyiec61850.pyd
when the package is imported.
"""

import os
import sys

if sys.platform == "win32":
    # In a frozen app the package files are extracted under sys._MEIPASS.
    _base = getattr(sys, "_MEIPASS", None)
    if _base:
        _pkg_dir = os.path.join(_base, "pyiec61850")
        if os.path.isdir(_pkg_dir):
            # Python >= 3.8 requires add_dll_directory for DLL resolution.
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(_pkg_dir)
            # Also prepend to PATH as a fallback for older Python / ctypes.
            os.environ["PATH"] = _pkg_dir + os.pathsep + os.environ.get("PATH", "")

            # Pre-load the iec61850 DLL so _pyiec61850.pyd can link to it.
            import ctypes

            for _f in sorted(os.listdir(_pkg_dir)):
                if _f.endswith(".dll") and "iec61850" in _f.lower():
                    try:
                        ctypes.WinDLL(os.path.join(_pkg_dir, _f), winmode=0)
                    except Exception:
                        pass

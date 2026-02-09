#!/usr/bin/env python3
"""
pyiec61850-ng - Python bindings for libiec61850.

This package provides Python bindings for the libiec61850 library,
enabling IEC 61850 protocol support for power systems.

Submodules:
    - tase2: TASE.2/ICCP protocol support (IEC 60870-6)
    - mms: Safe MMS protocol wrappers with memory management
    - goose: GOOSE publish/subscribe
    - sv: Sampled Values publish/subscribe
    - server: IEC 61850 server
"""

import os as _os
import sys as _sys
import ctypes as _ctypes

# Load the bundled libiec61850 shared library before importing SWIG bindings.
# When installed from a wheel, the .so/.dll lives inside the package directory.
_package_dir = _os.path.dirname(_os.path.abspath(__file__))

if _sys.platform == 'win32':
    if hasattr(_os, 'add_dll_directory'):
        _os.add_dll_directory(_package_dir)
    _os.environ['PATH'] = _package_dir + _os.pathsep + _os.environ.get('PATH', '')
    for _f in sorted(_os.listdir(_package_dir)):
        if _f.endswith('.dll') and 'iec61850' in _f.lower():
            try:
                _ctypes.WinDLL(_os.path.join(_package_dir, _f), winmode=0)
                break
            except Exception:
                pass
else:
    for _f in _os.listdir(_package_dir):
        if _f.startswith('libiec61850.so'):
            try:
                _ctypes.CDLL(_os.path.join(_package_dir, _f))
                break
            except Exception:
                pass

# Expose submodules (use try/except so the package is importable even if
# individual submodules have unmet dependencies, e.g. missing SWIG extension)
try:
    from . import tase2
except ImportError:
    pass
try:
    from . import mms
except ImportError:
    pass
try:
    from . import goose
except ImportError:
    pass
try:
    from . import sv
except ImportError:
    pass
try:
    from . import server
except ImportError:
    pass

__all__ = ['tase2', 'mms', 'goose', 'sv', 'server']

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

# Load the bundled libiec61850 shared library + SWIG extension. The loader
# captures any failure (wrong glibc / CPython ABI / missing file) instead of
# swallowing it, so LibraryNotFoundError can report the real cause.
from . import _libload  # noqa: F401  (runs the native load on import)

#: The native-lib load error, if any (None on success). Kept for inspection.
_LIB_LOAD_ERROR = _libload.LIB_LOAD_ERROR or _libload.EXT_IMPORT_ERROR

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

__all__ = ["tase2", "mms", "goose", "sv", "server"]

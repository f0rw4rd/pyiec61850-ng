"""Native libiec61850 loader with diagnostics.

Preloads the bundled ``libiec61850`` shared library and tries to import the
SWIG extension, *capturing* any failure instead of swallowing it. The captured
cause is exposed via :func:`load_error_hint` so that ``LibraryNotFoundError``
can tell the user *why* the binary did not load (wrong glibc, wrong CPython
ABI, missing file) rather than the misleading "not found. Install with: pip
install ..." — even when the package clearly is installed (see issue #15).
"""
from __future__ import annotations

import ctypes as _ctypes
import logging as _logging
import os as _os
import platform as _platform
import sys as _sys

_logger = _logging.getLogger("pyiec61850")

_package_dir = _os.path.dirname(_os.path.abspath(__file__))

#: The exception raised while preloading the native lib, or None on success.
LIB_LOAD_ERROR: Exception | None = None
#: The exception raised while importing the SWIG extension, or None on success.
EXT_IMPORT_ERROR: Exception | None = None
#: Absolute path of the native library that was successfully loaded, if any.
LOADED_PATH: str | None = None


def _candidate_dirs() -> list[str]:
    """Directories that may hold the native lib (package dir + auditwheel libs)."""
    dirs = [_package_dir]
    # auditwheel relocates the lib into a sibling <dist>.libs/ directory.
    parent = _os.path.dirname(_package_dir)
    for entry in ("pyiec61850_ng.libs", "pyiec61850.libs"):
        cand = _os.path.join(parent, entry)
        if _os.path.isdir(cand):
            dirs.append(cand)
    return dirs


def _preload() -> None:
    global LIB_LOAD_ERROR, LOADED_PATH

    if _sys.platform == "win32":
        if hasattr(_os, "add_dll_directory"):
            _os.add_dll_directory(_package_dir)
        _os.environ["PATH"] = _package_dir + _os.pathsep + _os.environ.get("PATH", "")
        prefix, loader = "", _ctypes.WinDLL
    else:
        prefix, loader = "libiec61850.so", _ctypes.CDLL

    last_error: Exception | None = None
    for directory in _candidate_dirs():
        try:
            entries = sorted(_os.listdir(directory))
        except OSError:
            continue
        for fname in entries:
            if _sys.platform == "win32":
                match = fname.lower().endswith(".dll") and "iec61850" in fname.lower()
            else:
                match = fname.startswith(prefix)
            if not match:
                continue
            path = _os.path.join(directory, fname)
            try:
                loader(path) if _sys.platform != "win32" else loader(path, winmode=0)
                LOADED_PATH = path
                return
            except Exception as exc:  # noqa: BLE001 - capture, don't swallow
                last_error = exc

    if last_error is not None:
        LIB_LOAD_ERROR = last_error
        _logger.warning("failed to load bundled libiec61850: %s", last_error)


def _import_extension() -> None:
    """Import the SWIG extension, recording (not raising) any failure."""
    global EXT_IMPORT_ERROR
    try:
        import importlib

        importlib.import_module("pyiec61850.pyiec61850")
    except Exception as exc:  # noqa: BLE001
        EXT_IMPORT_ERROR = exc
        _logger.warning("failed to import pyiec61850 SWIG extension: %s", exc)


def _glibc_version() -> str | None:
    try:
        return _os.confstr("CS_GNU_LIBC_VERSION")  # e.g. "glibc 2.31"
    except (ValueError, OSError, AttributeError):
        pass
    try:
        name, ver = _platform.libc_ver()
        return f"{name} {ver}".strip() or None
    except Exception:  # noqa: BLE001
        return None


def have_library() -> bool:
    """True if the SWIG extension imported successfully."""
    return EXT_IMPORT_ERROR is None


def require_library(exc_cls) -> None:
    """Raise ``exc_cls`` (carrying load diagnostics) if the native lib is unusable.

    Single guard for every entry point that needs libiec61850, replacing the
    duplicated ``if not _HAS_IEC61850: raise ...`` blocks. ``exc_cls`` is the
    submodule's own ``LibraryNotFoundError`` so callers keep their exception type;
    instantiating it with no message appends the real cause via
    :func:`library_not_found_message`. Import semantics are unchanged — the
    package stays importable without the native library.
    """
    if not have_library():
        raise exc_cls()


def library_not_found_message(message: str = "pyiec61850 library not found") -> str:
    """``message`` augmented with the real load failure cause, when known.

    Shared by every submodule's ``LibraryNotFoundError`` so the diagnostic
    formatting lives in one place.
    """
    hint = load_error_hint()
    return f"{message}\n{hint}" if hint else message


def load_error_hint() -> str:
    """Human-readable explanation of why the native binary failed to load.

    Returns an empty string when the library loaded successfully.
    """
    cause = LIB_LOAD_ERROR or EXT_IMPORT_ERROR
    if cause is None:
        return ""

    lines = [f"native libiec61850 failed to load: {cause}"]
    text = str(cause)
    build_from_source = (
        "or build from source: pip install --no-binary :all: pyiec61850-ng"
    )
    if "GLIBC_" in text:
        lines.append(
            f"This wheel needs a newer glibc than this system "
            f"(detected: {_glibc_version() or 'unknown'}). Install a wheel "
            f"matching your platform, {build_from_source}"
        )
    elif "GLIBCXX_" in text or "CXXABI_" in text:
        lines.append(
            "This wheel needs a newer libstdc++ (C++ runtime) than this system "
            f"provides. Update libstdc++/gcc, {build_from_source}"
        )
    elif "undefined symbol" in text:
        lines.append(
            f"This looks like a CPython ABI mismatch (running Python "
            f"{_sys.version_info.major}.{_sys.version_info.minor}). Ensure the "
            f"installed wheel matches your interpreter."
        )
    else:
        lines.append(
            f"Install a wheel matching your platform/interpreter "
            f"(Python {_sys.version_info.major}.{_sys.version_info.minor}, "
            f"{_glibc_version() or 'unknown libc'}), {build_from_source}"
        )
    return "\n".join(lines)


_preload()
_import_extension()

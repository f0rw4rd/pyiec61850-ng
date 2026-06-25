"""Shared pytest configuration for the unit-test suite.

Mock-safe native guard (fixes the unit-test/native hang)
--------------------------------------------------------
The unit tests mock the SWIG layer (``patch(... .iec61850)``) inside each
test. When the *real* native extension is also importable (e.g. a dev box or
CI image with a wheel installed), a subtle hang appears:

    with patch("pyiec61850.mms.client.iec61850") as mock_iec:
        client = MMSClient(); client.connect(...)   # uses the mock
    # patch context exits -> client.iec61850 is the REAL module again
    # ... test returns, `client` is garbage-collected ...
    # __del__ -> disconnect() -> real IedConnection_close(<Mock>)

Passing a ``unittest.mock.Mock`` to a real SWIG function makes the typemap
probe the mock for a C pointer, which spawns child mocks ad infinitum and
never returns — the process wedges at GC time.

The fix: wrap every function in the native module so that a call carrying a
Mock argument short-circuits to ``None`` instead of entering the C typemap.
This is **transparent to integration tests** — those call the native layer
with real handles, never mocks, so the guard never fires for them. It only
neutralises the impossible Mock-into-native calls that unit-test GC produces.

The guard is installed once, in place, when this conftest is imported (before
any test runs). If the native extension is absent there is nothing to guard
and no hang is possible, so it is a no-op.
"""

from __future__ import annotations

import functools
import os
import types
import unittest.mock as _mock

import pytest

#: True when this session is the integration suite (real native lib + server).
#: The unit-suite shims below must NOT apply there.
_IS_INTEGRATION = os.environ.get("PYIEC61850_INTEGRATION") == "1"


def _install_mock_safe_native_guard() -> None:
    try:
        import pyiec61850.pyiec61850 as native
    except Exception:
        # No native extension -> the GC-time hang cannot occur.
        return

    if getattr(native, "_mock_safe_guard_installed", False):
        return

    # Common base of Mock / MagicMock / NonCallableMock.
    mock_base = _mock.NonCallableMock

    def _is_mock(value: object) -> bool:
        return isinstance(value, mock_base)

    def _wrap(fn):
        @functools.wraps(fn)
        def guarded(*args, **kwargs):
            if any(_is_mock(a) for a in args) or any(_is_mock(v) for v in kwargs.values()):
                # A mock reached a real native function — only happens for
                # leftover mock handles at GC. Do nothing instead of hanging.
                return None
            return fn(*args, **kwargs)

        return guarded

    for name in dir(native):
        if name.startswith("__"):
            continue
        obj = getattr(native, name)
        if isinstance(obj, types.FunctionType):
            setattr(native, name, _wrap(obj))

    native._mock_safe_guard_installed = True


_install_mock_safe_native_guard()


def _native_extension_importable() -> bool:
    try:
        import pyiec61850.pyiec61850  # noqa: F401
    except Exception:
        return False
    return True


def pytest_collection_modifyitems(config, items):
    """Skip SWIG-director crash-path tests when the real native lib is present.

    Tests like ``TestGooseSubscriberTriggerCrashPaths`` build a
    ``_Py*Handler`` whose base class is ``getattr(iec61850, "...Handler",
    object)`` — resolved at import. Without the extension that base is plain
    ``object`` (the pure-Python fallback these tests are written for); with the
    extension it is a real C++ SWIG director. Feeding such a director the mock
    state these tests use makes its construction/teardown wedge in the SWIG
    typemap (the same class of hang the mock-safe guard above prevents for
    plain functions, but directors route through C++ object machinery the guard
    cannot reach).

    These tests are identified structurally by the ``_make_handler`` helper
    every director crash-path class defines. They run normally on a plain
    checkout; here we only skip them when the extension is importable, so the
    unit and integration environments can coexist without hanging.
    """
    if _IS_INTEGRATION or not _native_extension_importable():
        return
    skip = pytest.mark.skip(
        reason="director crash-path test requires the pure-Python handler "
        "fallback (run without the native extension)"
    )
    for item in items:
        cls = getattr(item, "cls", None)
        if cls is not None and hasattr(cls, "_make_handler"):
            item.add_marker(skip)

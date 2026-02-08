"""PyInstaller hook support for pyiec61850."""

import os


def get_hook_dirs():
    """Return the path to the PyInstaller hooks directory.

    This is registered as a PyInstaller hook entry point so that
    ``pyinstaller --collect-all pyiec61850`` (or a plain import) will
    automatically find our hook.
    """
    return [os.path.dirname(__file__)]


def get_PyInstaller_tests():
    """Return the path to PyInstaller test directory (unused, but expected)."""
    return []

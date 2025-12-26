#!/usr/bin/env python3
"""
pyiec61850-ng - Python bindings for libiec61850.

This package provides Python bindings for the libiec61850 library,
enabling IEC 61850 protocol support for power systems.

Submodules:
    - tase2: TASE.2/ICCP protocol support (IEC 60870-6)
    - mms: Safe MMS protocol wrappers with memory management
"""

# Expose submodules
from . import tase2
from . import mms

__all__ = ['tase2', 'mms']

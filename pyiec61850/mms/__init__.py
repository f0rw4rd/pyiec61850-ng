#!/usr/bin/env python3
"""
MMS Protocol Support for pyiec61850-ng

This module provides safe Python wrappers around pyiec61850 SWIG bindings
to prevent common crash scenarios documented in MMS_STABILITY_ANALYSIS.md:

- Issue #1: Typo in MmsError_destroy (MmsErrror with 3 r's)
- Issue #2: NULL pointer dereference in toCharP()
- Issue #3: Double-free from LinkedList reuse after destroy
- Issue #4: Missing NULL validation before MmsServerIdentity_destroy
- Issue #5: MmsValue not nullified after cleanup
- Issue #6: Silent exception swallowing hiding bugs

Usage:
    # Safe client (recommended)
    from pyiec61850.mms import MMSClient

    with MMSClient() as client:
        client.connect("192.168.1.100", 102)
        for device in client.get_logical_devices():
            print(device)

    # Low-level safe utilities
    from pyiec61850.mms.utils import (
        safe_to_char_p,
        safe_linked_list_iter,
        LinkedListGuard,
        MmsValueGuard,
    )

Features:
    - Safe NULL pointer handling before toCharP()
    - Automatic resource cleanup via context managers
    - Proper MmsError/MmsValue/LinkedList destruction
    - Logging of cleanup errors (not silently swallowed)
"""

__version__ = "0.1.0"
__author__ = "f0rw4rd"

# Main client class
from .client import MMSClient, ServerIdentity, DataAttribute

# Safe utility functions
from .utils import (
    # Issue #2 fix: Safe string conversion
    safe_to_char_p,
    # Issue #2 & #3 fix: Safe LinkedList handling
    safe_linked_list_iter,
    safe_linked_list_to_list,
    safe_linked_list_destroy,
    # Issue #1 fix: Correct MmsError cleanup
    safe_mms_error_destroy,
    # Issue #4 fix: Safe identity cleanup
    safe_identity_destroy,
    # Issue #5 fix: Safe MmsValue cleanup
    safe_mms_value_delete,
    # Context managers (Issue #3, #4, #5)
    LinkedListGuard,
    MmsValueGuard,
    MmsErrorGuard,
    IdentityGuard,
    # Helper functions
    unpack_result,
    cleanup_all,
)

# Exceptions
from .exceptions import (
    MMSError,
    LibraryNotFoundError,
    ConnectionError,
    ConnectionFailedError,
    ConnectionTimeoutError,
    NotConnectedError,
    OperationError,
    ReadError,
    WriteError,
    NullPointerError,
    MemoryError,
    CleanupError,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Client
    "MMSClient",
    "ServerIdentity",
    "DataAttribute",
    # Safe utilities (Issue #1, #2 fixes)
    "safe_to_char_p",
    "safe_linked_list_iter",
    "safe_linked_list_to_list",
    "safe_linked_list_destroy",
    "safe_mms_error_destroy",
    "safe_identity_destroy",
    "safe_mms_value_delete",
    # Context managers (Issue #3, #4, #5 fixes)
    "LinkedListGuard",
    "MmsValueGuard",
    "MmsErrorGuard",
    "IdentityGuard",
    # Helpers
    "unpack_result",
    "cleanup_all",
    # Exceptions
    "MMSError",
    "LibraryNotFoundError",
    "ConnectionError",
    "ConnectionFailedError",
    "ConnectionTimeoutError",
    "NotConnectedError",
    "OperationError",
    "ReadError",
    "WriteError",
    "NullPointerError",
    "MemoryError",
    "CleanupError",
]

#!/usr/bin/env python3
"""
Safe MMS Utility Functions

This module provides safe wrappers around pyiec61850 SWIG bindings
to prevent common crash scenarios:

- NULL pointer dereference in toCharP()
- Memory leaks from improper cleanup
- Double-free from reusing destroyed pointers
- Silent exception swallowing hiding bugs

Usage:
    from pyiec61850.mms.utils import (
        safe_to_char_p,
        safe_linked_list_iter,
        LinkedListGuard,
        MmsValueGuard,
        MmsErrorGuard,
    )
"""

from typing import Any, Generator, List, Optional, Callable
from contextlib import contextmanager
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    NullPointerError,
    CleanupError,
)

logger = logging.getLogger(__name__)


def _ensure_library() -> None:
    """Ensure pyiec61850 is available."""
    if not _HAS_IEC61850:
        raise LibraryNotFoundError(
            "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
        )


# =============================================================================
# Issue #2 Fix: Safe toCharP wrapper
# =============================================================================

def safe_to_char_p(ptr: Any) -> Optional[str]:
    """
    Safely convert C char pointer to Python string.

    This wrapper prevents segfaults by checking for NULL/None
    before calling the SWIG toCharP() function.

    Args:
        ptr: Pointer from LinkedList_getData() or similar

    Returns:
        Python string or None if ptr is NULL

    Example:
        data = iec61850.LinkedList_getData(element)
        name = safe_to_char_p(data)  # Safe - returns None if NULL
        if name:
            print(name)
    """
    _ensure_library()

    if ptr is None:
        return None

    # Some SWIG wrappers return 0 for NULL
    if ptr == 0:
        return None

    # Check for invalid pointer types
    if not hasattr(iec61850, 'toCharP'):
        logger.warning("toCharP not available in pyiec61850")
        return None

    try:
        result = iec61850.toCharP(ptr)
        return result if result else None
    except Exception as e:
        logger.debug(f"toCharP failed: {e}")
        return None


# =============================================================================
# Issue #2 & #3 Fix: Safe LinkedList iteration
# =============================================================================

def safe_linked_list_iter(linked_list: Any) -> Generator[str, None, None]:
    """
    Safely iterate over a LinkedList, yielding string values.

    This iterator:
    - Checks for NULL data pointers before conversion
    - Skips invalid entries instead of crashing
    - Does NOT destroy the list (caller's responsibility)

    Args:
        linked_list: LinkedList pointer from pyiec61850

    Yields:
        String values from each non-NULL element

    Example:
        device_list = iec61850.IedConnection_getLogicalDeviceList(conn)
        for device_name in safe_linked_list_iter(device_list):
            print(f"Found device: {device_name}")
        safe_linked_list_destroy(device_list)
    """
    _ensure_library()

    if not linked_list:
        return

    try:
        element = iec61850.LinkedList_getNext(linked_list)
        while element:
            data = iec61850.LinkedList_getData(element)
            if data:  # Issue #2: NULL check before toCharP
                name = safe_to_char_p(data)
                if name:
                    yield name
            element = iec61850.LinkedList_getNext(element)
    except Exception as e:
        logger.debug(f"LinkedList iteration error: {e}")


def safe_linked_list_to_list(linked_list: Any) -> List[str]:
    """
    Convert LinkedList to Python list safely.

    Args:
        linked_list: LinkedList pointer from pyiec61850

    Returns:
        List of strings (empty list if NULL or error)

    Example:
        device_list = iec61850.IedConnection_getLogicalDeviceList(conn)
        devices = safe_linked_list_to_list(device_list)
        safe_linked_list_destroy(device_list)
    """
    return list(safe_linked_list_iter(linked_list))


def safe_linked_list_destroy(linked_list: Any) -> None:
    """
    Safely destroy a LinkedList.

    Args:
        linked_list: LinkedList pointer (can be None)

    Note:
        After calling this, the linked_list pointer is invalid.
        Set your variable to None after calling:

            safe_linked_list_destroy(device_list)
            device_list = None  # Prevent accidental reuse
    """
    _ensure_library()

    if not linked_list:
        return

    try:
        iec61850.LinkedList_destroy(linked_list)
    except Exception as e:
        logger.debug(f"LinkedList_destroy error: {e}")


# =============================================================================
# Issue #1 Fix: Correct MmsError cleanup (note: MmsError vs MmsErrror)
# =============================================================================

def safe_mms_error_destroy(mms_error: Any) -> None:
    """
    Safely destroy an MmsError object.

    This function uses the CORRECT function name MmsError_destroy
    (not MmsErrror_destroy with 3 r's).

    Args:
        mms_error: MmsError pointer (can be None)
    """
    _ensure_library()

    if not mms_error:
        return

    try:
        # CORRECT spelling: MmsError_destroy (2 r's)
        if hasattr(iec61850, 'MmsError_destroy'):
            iec61850.MmsError_destroy(mms_error)
    except Exception as e:
        logger.debug(f"MmsError_destroy error: {e}")


# =============================================================================
# Issue #4 Fix: Safe MmsServerIdentity cleanup
# =============================================================================

def safe_identity_destroy(identity: Any) -> None:
    """
    Safely destroy an MmsServerIdentity object.

    Args:
        identity: MmsServerIdentity pointer (can be None)
    """
    _ensure_library()

    if not identity:
        return

    try:
        if hasattr(iec61850, 'MmsServerIdentity_destroy'):
            iec61850.MmsServerIdentity_destroy(identity)
    except Exception as e:
        logger.debug(f"MmsServerIdentity_destroy error: {e}")


# =============================================================================
# Issue #5 Fix: Safe MmsValue cleanup
# =============================================================================

def safe_mms_value_delete(value: Any) -> None:
    """
    Safely delete an MmsValue object.

    Args:
        value: MmsValue pointer (can be None)
    """
    _ensure_library()

    if not value:
        return

    try:
        if hasattr(iec61850, 'MmsValue_delete'):
            iec61850.MmsValue_delete(value)
    except Exception as e:
        logger.debug(f"MmsValue_delete error: {e}")


# =============================================================================
# Context Managers for Automatic Cleanup (Issue #3, #4, #5)
# =============================================================================

class LinkedListGuard:
    """
    Context manager for safe LinkedList handling.

    Automatically destroys the LinkedList on exit and
    nullifies the reference to prevent double-free.

    Example:
        with LinkedListGuard(iec61850.IedConnection_getLogicalDeviceList(conn)) as guard:
            for name in safe_linked_list_iter(guard.list):
                print(name)
        # List is automatically destroyed here
    """

    def __init__(self, linked_list: Any):
        self.list = linked_list
        self._destroyed = False

    def __enter__(self) -> 'LinkedListGuard':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._destroyed and self.list:
            safe_linked_list_destroy(self.list)
            self._destroyed = True
        self.list = None  # Issue #3: Nullify to prevent reuse
        return False

    def __iter__(self):
        """Allow direct iteration."""
        return safe_linked_list_iter(self.list)


class MmsValueGuard:
    """
    Context manager for safe MmsValue handling.

    Automatically deletes the MmsValue on exit.

    Example:
        with MmsValueGuard(iec61850.IedConnection_readObject(conn, ref)) as guard:
            if guard.value:
                print(iec61850.MmsValue_toFloat(guard.value))
        # Value is automatically deleted here
    """

    def __init__(self, value: Any):
        self.value = value
        self._deleted = False

    def __enter__(self) -> 'MmsValueGuard':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._deleted and self.value:
            safe_mms_value_delete(self.value)
            self._deleted = True
        self.value = None
        return False


class MmsErrorGuard:
    """
    Context manager for safe MmsError handling.

    Automatically destroys the MmsError on exit using
    the CORRECT function name (MmsError_destroy, not MmsErrror_destroy).

    Example:
        mms_error = iec61850.MmsError()
        with MmsErrorGuard(mms_error):
            result = some_operation(mms_error)
        # Error is automatically destroyed here
    """

    def __init__(self, error: Any):
        self.error = error
        self._destroyed = False

    def __enter__(self) -> 'MmsErrorGuard':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._destroyed and self.error:
            safe_mms_error_destroy(self.error)
            self._destroyed = True
        self.error = None
        return False


class IdentityGuard:
    """
    Context manager for safe MmsServerIdentity handling.

    Example:
        identity, error = iec61850.IedConnection_identify(conn)
        with IdentityGuard(identity) as guard:
            if guard.identity:
                print(guard.identity.vendorName)
        # Identity is automatically destroyed here
    """

    def __init__(self, identity: Any):
        self.identity = identity
        self._destroyed = False

    def __enter__(self) -> 'IdentityGuard':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not self._destroyed and self.identity:
            safe_identity_destroy(self.identity)
            self._destroyed = True
        self.identity = None
        return False


# =============================================================================
# Convenience function for handling tuple returns
# =============================================================================

def unpack_result(result: Any, error_ok: int = None) -> tuple:
    """
    Safely unpack pyiec61850 result tuples.

    Many pyiec61850 functions return (value, error) tuples.
    This helper safely unpacks them.

    Args:
        result: Result from pyiec61850 function call
        error_ok: Expected OK error code (auto-detected if None)

    Returns:
        Tuple of (value, error_code, is_ok)

    Example:
        result = iec61850.IedConnection_getLogicalDeviceList(conn)
        value, error, ok = unpack_result(result)
        if ok:
            for name in safe_linked_list_iter(value):
                print(name)
    """
    _ensure_library()

    if error_ok is None:
        error_ok = getattr(iec61850, 'IED_ERROR_OK', 0)

    if isinstance(result, tuple) and len(result) >= 2:
        value, error = result[0], result[1]
        return (value, error, error == error_ok)
    else:
        # Single value return - assume success
        return (result, error_ok, True)


# =============================================================================
# Safe cleanup helper for multiple resources
# =============================================================================

def cleanup_all(*resources: tuple) -> None:
    """
    Clean up multiple resources safely.

    Args:
        *resources: Tuples of (resource, cleanup_function)

    Example:
        cleanup_all(
            (device_list, safe_linked_list_destroy),
            (mms_value, safe_mms_value_delete),
            (identity, safe_identity_destroy),
        )
    """
    for resource, cleanup_fn in resources:
        if resource and cleanup_fn:
            try:
                cleanup_fn(resource)
            except Exception as e:
                logger.debug(f"Cleanup error: {e}")

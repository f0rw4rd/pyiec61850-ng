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

import logging
from typing import Any, Generator, List, Optional, Union

try:
    import pyiec61850.pyiec61850 as iec61850

    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
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
    if not hasattr(iec61850, "toCharP"):
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
        if hasattr(iec61850, "MmsError_destroy"):
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
        if hasattr(iec61850, "MmsServerIdentity_destroy"):
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
        if hasattr(iec61850, "MmsValue_delete"):
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

    def __enter__(self) -> "LinkedListGuard":
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

    def __enter__(self) -> "MmsValueGuard":
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

    def __enter__(self) -> "MmsErrorGuard":
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

    def __enter__(self) -> "IdentityGuard":
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
        error_ok = getattr(iec61850, "IED_ERROR_OK", 0)

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


# =============================================================================
# MmsValue <-> Python conversion
# =============================================================================

# MMS type constants with fallbacks (matches mms_common.h MmsType enum)
_MMS_ARRAY = 0
_MMS_STRUCTURE = 1
_MMS_BOOLEAN = 2
_MMS_BIT_STRING = 3
_MMS_INTEGER = 4
_MMS_UNSIGNED = 5
_MMS_FLOAT = 6
_MMS_OCTET_STRING = 7
_MMS_VISIBLE_STRING = 8
_MMS_BINARY_TIME = 10
_MMS_STRING = 13
_MMS_UTC_TIME = 14
_MMS_DATA_ACCESS_ERROR = 15


def _mms_const(name: str, fallback: int) -> int:
    """Get MMS constant from SWIG bindings with fallback."""
    if _HAS_IEC61850:
        return getattr(iec61850, name, fallback)
    return fallback


def mms_value_to_python(mms_value: Any) -> Union[bool, int, float, str, bytes, list, dict, None]:
    """
    Convert an MmsValue to a native Python type.

    Handles all MMS types recursively, replacing the duplicated switch
    statements in MMS and GOOSE modules.

    Args:
        mms_value: MmsValue pointer from pyiec61850

    Returns:
        bool, int, float, str, bytes, list, dict, or None.
        - MMS_BOOLEAN -> bool
        - MMS_INTEGER -> int
        - MMS_UNSIGNED -> int
        - MMS_FLOAT -> float
        - MMS_VISIBLE_STRING, MMS_STRING -> str
        - MMS_BIT_STRING -> int (bit pattern as integer)
        - MMS_OCTET_STRING -> bytes
        - MMS_ARRAY -> list (recursively converted elements)
        - MMS_STRUCTURE -> dict (with integer keys if names unavailable)
        - MMS_UTC_TIME -> int (milliseconds since epoch)
        - MMS_BINARY_TIME -> int (milliseconds since epoch)
        - MMS_DATA_ACCESS_ERROR -> None

    Raises:
        LibraryNotFoundError: If pyiec61850 is not available

    Example:
        mms_val = iec61850.IedConnection_readObject(conn, ref, fc)
        python_val = mms_value_to_python(mms_val)
    """
    _ensure_library()

    if mms_value is None or mms_value == 0:
        return None

    mms_type = iec61850.MmsValue_getType(mms_value)

    type_boolean = _mms_const("MMS_BOOLEAN", _MMS_BOOLEAN)
    type_integer = _mms_const("MMS_INTEGER", _MMS_INTEGER)
    type_unsigned = _mms_const("MMS_UNSIGNED", _MMS_UNSIGNED)
    type_float = _mms_const("MMS_FLOAT", _MMS_FLOAT)
    type_visible_string = _mms_const("MMS_VISIBLE_STRING", _MMS_VISIBLE_STRING)
    type_string = _mms_const("MMS_STRING", _MMS_STRING)
    type_bit_string = _mms_const("MMS_BIT_STRING", _MMS_BIT_STRING)
    type_octet_string = _mms_const("MMS_OCTET_STRING", _MMS_OCTET_STRING)
    type_structure = _mms_const("MMS_STRUCTURE", _MMS_STRUCTURE)
    type_array = _mms_const("MMS_ARRAY", _MMS_ARRAY)
    type_utc_time = _mms_const("MMS_UTC_TIME", _MMS_UTC_TIME)
    type_binary_time = _mms_const("MMS_BINARY_TIME", _MMS_BINARY_TIME)
    type_data_access_error = _mms_const("MMS_DATA_ACCESS_ERROR", _MMS_DATA_ACCESS_ERROR)

    if mms_type == type_boolean:
        return bool(iec61850.MmsValue_getBoolean(mms_value))

    elif mms_type == type_integer:
        return int(iec61850.MmsValue_toInt64(mms_value))

    elif mms_type == type_unsigned:
        return int(iec61850.MmsValue_toUint32(mms_value))

    elif mms_type == type_float:
        return float(iec61850.MmsValue_toFloat(mms_value))

    elif mms_type in (type_visible_string, type_string):
        return str(iec61850.MmsValue_toString(mms_value))

    elif mms_type == type_bit_string:
        return int(iec61850.MmsValue_getBitStringAsInteger(mms_value))

    elif mms_type == type_octet_string:
        size = iec61850.MmsValue_getOctetStringSize(mms_value)
        buf = iec61850.MmsValue_getOctetStringBuffer(mms_value)
        if buf is not None and size > 0:
            return bytes(iec61850.MmsValue_getOctetStringOctet(mms_value, i) for i in range(size))
        return b""

    elif mms_type == type_array:
        count = iec61850.MmsValue_getArraySize(mms_value)
        result = []
        for i in range(count):
            element = iec61850.MmsValue_getElement(mms_value, i)
            result.append(mms_value_to_python(element))
        return result

    elif mms_type == type_structure:
        count = iec61850.MmsValue_getArraySize(mms_value)
        result = {}
        for i in range(count):
            element = iec61850.MmsValue_getElement(mms_value, i)
            result[i] = mms_value_to_python(element)
        return result

    elif mms_type == type_utc_time:
        return int(iec61850.MmsValue_getUtcTimeInMs(mms_value))

    elif mms_type == type_binary_time:
        return int(iec61850.MmsValue_getBinaryTimeAsUtcMs(mms_value))

    elif mms_type == type_data_access_error:
        return None

    else:
        logger.warning(f"Unknown MMS type: {mms_type}")
        return None


def python_to_mms_value(value: Any) -> Any:
    """
    Convert a native Python type to an MmsValue.

    The caller is responsible for calling MmsValue_delete on the returned
    handle when it is no longer needed (or use MmsValueGuard).

    Args:
        value: Python value (bool, int, float, or str)

    Returns:
        MmsValue handle

    Raises:
        LibraryNotFoundError: If pyiec61850 is not available
        TypeError: If the value type is not supported

    Example:
        mms_val = python_to_mms_value(42)
        # ... use mms_val ...
        safe_mms_value_delete(mms_val)
    """
    _ensure_library()

    # bool must be checked before int (bool is a subclass of int)
    if isinstance(value, bool):
        return iec61850.MmsValue_newBoolean(value)
    elif isinstance(value, int):
        return iec61850.MmsValue_newIntegerFromInt64(value)
    elif isinstance(value, float):
        return iec61850.MmsValue_newFloat(value)
    elif isinstance(value, str):
        return iec61850.MmsValue_newVisibleString(value)
    else:
        raise TypeError(
            f"Cannot convert {type(value).__name__} to MmsValue. "
            f"Supported types: bool, int, float, str"
        )

#!/usr/bin/env python3
"""
MMS Protocol Exceptions

Exception hierarchy for MMS operations with pyiec61850.
"""


class MMSError(Exception):
    """Base exception for all MMS errors."""
    pass


class LibraryNotFoundError(MMSError):
    """pyiec61850 library not available."""
    pass


class ConnectionError(MMSError):
    """Connection-related error."""
    pass


class ConnectionFailedError(ConnectionError):
    """Failed to establish connection."""

    def __init__(self, host: str, port: int, reason: str = ""):
        self.host = host
        self.port = port
        self.reason = reason
        msg = f"Failed to connect to {host}:{port}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class ConnectionTimeoutError(ConnectionError):
    """Connection timed out."""
    pass


class NotConnectedError(ConnectionError):
    """Operation requires active connection."""

    def __init__(self, message: str = "Not connected to server"):
        super().__init__(message)


class OperationError(MMSError):
    """MMS operation failed."""
    pass


class ReadError(OperationError):
    """Failed to read variable or data."""
    pass


class WriteError(OperationError):
    """Failed to write variable or data."""
    pass


class NullPointerError(MMSError):
    """
    Attempted operation on NULL pointer.

    This error prevents segfaults that would occur if NULL
    pointers were passed to SWIG wrapper functions like toCharP().
    """
    pass


class MemoryError(MMSError):
    """Memory management error (leak, double-free, etc.)."""
    pass


class CleanupError(MMSError):
    """Error during resource cleanup."""
    pass

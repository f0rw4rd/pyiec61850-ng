#!/usr/bin/env python3
"""
Safe MMS Client Implementation

A high-level MMS client that wraps pyiec61850 with proper
memory management to prevent crashes and memory leaks.

Example:
    from pyiec61850.mms import MMSClient

    with MMSClient() as client:
        client.connect("192.168.1.100", 102)

        # Get server info
        info = client.get_server_identity()
        print(f"Vendor: {info.vendor}")

        # List devices
        for device in client.get_logical_devices():
            print(f"Device: {device}")

            # List logical nodes
            for node in client.get_logical_nodes(device):
                print(f"  Node: {node}")
"""

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

try:
    import pyiec61850.pyiec61850 as iec61850

    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

# MMS type constants (fallback values if library not loaded)
MMS_BOOLEAN = getattr(iec61850, "MMS_BOOLEAN", 0) if iec61850 else 0
MMS_INTEGER = getattr(iec61850, "MMS_INTEGER", 1) if iec61850 else 1
MMS_UNSIGNED = getattr(iec61850, "MMS_UNSIGNED", 2) if iec61850 else 2
MMS_FLOAT = getattr(iec61850, "MMS_FLOAT", 3) if iec61850 else 3
MMS_VISIBLE_STRING = getattr(iec61850, "MMS_VISIBLE_STRING", 7) if iec61850 else 7
MMS_BIT_STRING = getattr(iec61850, "MMS_BIT_STRING", 4) if iec61850 else 4

from .exceptions import (
    ConnectionFailedError,
    LibraryNotFoundError,
    MMSError,
    NotConnectedError,
    ReadError,
    WriteError,
)
from .utils import (
    IdentityGuard,
    LinkedListGuard,
    safe_mms_value_delete,
    unpack_result,
)

logger = logging.getLogger(__name__)


@dataclass
class ServerIdentity:
    """MMS Server identity information."""

    vendor: Optional[str] = None
    model: Optional[str] = None
    revision: Optional[str] = None


@dataclass
class DataAttribute:
    """MMS Data attribute with value."""

    name: str
    value: Any
    type_name: str = ""


class MMSClient:
    """
    Safe MMS Client with automatic resource management.

    This client wraps pyiec61850 SWIG bindings with proper
    NULL checks and cleanup to prevent common crashes:

    - NULL pointer checks before toCharP() calls
    - Automatic LinkedList cleanup
    - Proper MmsValue/MmsError destruction
    - Context manager support for connection lifecycle

    Attributes:
        host: Connected server hostname
        port: Connected server port
        is_connected: Whether client is connected

    Example:
        client = MMSClient()
        try:
            client.connect("192.168.1.100", 102)
            devices = client.get_logical_devices()
        finally:
            client.disconnect()

        # Or use context manager:
        with MMSClient() as client:
            client.connect("192.168.1.100", 102)
            devices = client.get_logical_devices()
    """

    DEFAULT_PORT = 102
    DEFAULT_TIMEOUT = 10000  # 10 seconds

    def __init__(self):
        """Initialize MMS client."""
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        self._connection = None
        self._host: Optional[str] = None
        self._port: int = self.DEFAULT_PORT
        self._timeout: int = self.DEFAULT_TIMEOUT

    @property
    def host(self) -> Optional[str]:
        """Return connected host."""
        return self._host

    @property
    def port(self) -> int:
        """Return connected port."""
        return self._port

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connection is not None

    def connect(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """
        Connect to MMS server.

        Args:
            host: Server hostname or IP address
            port: Server port (default 102)
            timeout: Connection timeout in milliseconds

        Returns:
            True if connected successfully

        Raises:
            ConnectionFailedError: If connection fails
        """
        if self.is_connected:
            self.disconnect()

        self._host = host
        self._port = port
        self._timeout = timeout

        try:
            self._connection = iec61850.IedConnection_create()
            if not self._connection:
                raise ConnectionFailedError(host, port, "Failed to create connection")

            iec61850.IedConnection_setConnectTimeout(self._connection, timeout)

            error = iec61850.IedConnection_connect(self._connection, host, port)

            if error != iec61850.IED_ERROR_OK:
                error_msg = self._get_error_string(error)
                self._cleanup()
                raise ConnectionFailedError(host, port, error_msg)

            logger.info(f"Connected to MMS server at {host}:{port}")
            return True

        except ConnectionFailedError:
            raise
        except Exception as e:
            self._cleanup()
            raise ConnectionFailedError(host, port, str(e))

    def disconnect(self) -> None:
        """Disconnect from server."""
        if not self._connection:
            return

        logger.info(f"Disconnecting from {self._host}:{self._port}")

        try:
            iec61850.IedConnection_close(self._connection)
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up connection resources."""
        if self._connection:
            try:
                iec61850.IedConnection_destroy(self._connection)
            except Exception:
                pass
        self._connection = None

    def _ensure_connected(self) -> None:
        """Ensure connection is active."""
        if not self.is_connected:
            raise NotConnectedError()

    def _get_error_string(self, error: int) -> str:
        """Get human-readable error string."""
        try:
            if hasattr(iec61850, "IedClientError_toString"):
                return iec61850.IedClientError_toString(error)
        except Exception:
            pass
        return f"Error code: {error}"

    # =========================================================================
    # Server Information
    # =========================================================================

    def get_server_identity(self) -> ServerIdentity:
        """
        Get server identity information.

        Returns:
            ServerIdentity with vendor, model, revision

        Raises:
            NotConnectedError: If not connected
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_identify(self._connection)
            value, error, ok = unpack_result(result)

            if ok and value:
                # Use IdentityGuard for automatic cleanup (Issue #4)
                with IdentityGuard(value):
                    return ServerIdentity(
                        vendor=getattr(value, "vendorName", None),
                        model=getattr(value, "modelName", None),
                        revision=getattr(value, "revision", None),
                    )

            return ServerIdentity()

        except NotConnectedError:
            raise
        except Exception as e:
            logger.debug(f"Failed to get server identity: {e}")
            return ServerIdentity()

    # =========================================================================
    # Device Discovery
    # =========================================================================

    def get_logical_devices(self) -> List[str]:
        """
        Get list of logical devices on server.

        Returns:
            List of logical device names

        Raises:
            NotConnectedError: If not connected
            MMSError: If operation fails
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_getLogicalDeviceList(self._connection)
            value, error, ok = unpack_result(result)

            if not ok:
                raise MMSError(f"Failed to get devices: {self._get_error_string(error)}")

            # Use LinkedListGuard for automatic cleanup (Issue #3)
            with LinkedListGuard(value) as guard:
                # safe_linked_list_iter handles NULL checks (Issue #2)
                return list(guard)

        except NotConnectedError:
            raise
        except MMSError:
            raise
        except Exception as e:
            raise MMSError(f"Failed to get logical devices: {e}")

    def get_logical_nodes(self, device: str) -> List[str]:
        """
        Get list of logical nodes in a device.

        Args:
            device: Logical device name

        Returns:
            List of logical node names

        Raises:
            NotConnectedError: If not connected
            MMSError: If operation fails
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_getLogicalNodeList(self._connection, device)
            value, error, ok = unpack_result(result)

            if not ok:
                raise MMSError(f"Failed to get nodes: {self._get_error_string(error)}")

            with LinkedListGuard(value) as guard:
                return list(guard)

        except NotConnectedError:
            raise
        except MMSError:
            raise
        except Exception as e:
            raise MMSError(f"Failed to get logical nodes for {device}: {e}")

    def get_data_objects(self, device: str, node: str) -> List[str]:
        """
        Get list of data objects in a logical node.

        Args:
            device: Logical device name
            node: Logical node name

        Returns:
            List of data object names

        Raises:
            NotConnectedError: If not connected
            MMSError: If operation fails
        """
        self._ensure_connected()

        reference = f"{device}/{node}"

        try:
            result = iec61850.IedConnection_getLogicalNodeDirectory(
                self._connection, reference, iec61850.ACSI_CLASS_DATA_OBJECT
            )
            value, error, ok = unpack_result(result)

            if not ok:
                return []  # Data objects may not exist

            with LinkedListGuard(value) as guard:
                return list(guard)

        except Exception as e:
            logger.debug(f"Failed to get data objects for {reference}: {e}")
            return []

    def get_data_attributes(self, device: str, node: str, data_object: str) -> List[str]:
        """
        Get list of data attributes in a data object.

        Args:
            device: Logical device name
            node: Logical node name
            data_object: Data object name

        Returns:
            List of data attribute names
        """
        self._ensure_connected()

        reference = f"{device}/{node}.{data_object}"

        try:
            result = iec61850.IedConnection_getLogicalNodeDirectory(
                self._connection, reference, iec61850.ACSI_CLASS_DATA_ATTRIBUTE
            )
            value, error, ok = unpack_result(result)

            if not ok:
                return []

            with LinkedListGuard(value) as guard:
                return list(guard)

        except Exception as e:
            logger.debug(f"Failed to get attributes for {reference}: {e}")
            return []

    # =========================================================================
    # Variable Operations
    # =========================================================================

    def read_value(self, reference: str) -> Any:
        """
        Read a variable value by reference.

        Args:
            reference: Full object reference (e.g., "device/LN.DO.DA")

        Returns:
            Python value (converted from MmsValue)

        Raises:
            NotConnectedError: If not connected
            ReadError: If read fails
        """
        self._ensure_connected()

        mms_value = None
        try:
            # Parse reference to get functional constraint
            fc = iec61850.IEC61850_FC_ST  # Default to status

            result = iec61850.IedConnection_readObject(self._connection, reference, fc)
            value, error, ok = unpack_result(result)

            if not ok:
                raise ReadError(f"Read failed: {self._get_error_string(error)}")

            mms_value = value
            return self._convert_mms_value(mms_value)

        except NotConnectedError:
            raise
        except ReadError:
            raise
        except Exception as e:
            raise ReadError(f"Failed to read {reference}: {e}")
        finally:
            # Issue #5: Proper MmsValue cleanup
            if mms_value:
                safe_mms_value_delete(mms_value)

    def _convert_mms_value(self, mms_value: Any) -> Any:
        """Convert MmsValue to Python type."""
        if not mms_value:
            return None

        try:
            mms_type = iec61850.MmsValue_getType(mms_value)

            if mms_type == MMS_BOOLEAN:
                return iec61850.MmsValue_getBoolean(mms_value)
            elif mms_type == MMS_INTEGER:
                return iec61850.MmsValue_toInt32(mms_value)
            elif mms_type == MMS_UNSIGNED:
                return iec61850.MmsValue_toUint32(mms_value)
            elif mms_type == MMS_FLOAT:
                return iec61850.MmsValue_toFloat(mms_value)
            elif mms_type == MMS_VISIBLE_STRING:
                return iec61850.MmsValue_toString(mms_value)
            elif mms_type == MMS_BIT_STRING:
                return iec61850.MmsValue_getBitStringAsInteger(mms_value)
            else:
                # Return type info for complex types
                return f"<MmsValue type={mms_type}>"

        except Exception as e:
            logger.debug(f"MmsValue conversion error: {e}")
            return None

    def write_value(self, reference: str, value: Any) -> bool:
        """
        Write a value to a variable.

        Args:
            reference: Full object reference
            value: Python value to write

        Returns:
            True if successful

        Raises:
            NotConnectedError: If not connected
            WriteError: If write fails
        """
        self._ensure_connected()

        mms_value = None
        try:
            mms_value = self._create_mms_value(value)
            if not mms_value:
                raise WriteError(f"Failed to create MmsValue for {type(value)}")

            fc = iec61850.IEC61850_FC_ST

            error = iec61850.IedConnection_writeObject(self._connection, reference, fc, mms_value)

            if error != iec61850.IED_ERROR_OK:
                raise WriteError(f"Write failed: {self._get_error_string(error)}")

            return True

        except NotConnectedError:
            raise
        except WriteError:
            raise
        except Exception as e:
            raise WriteError(f"Failed to write {reference}: {e}")
        finally:
            if mms_value:
                safe_mms_value_delete(mms_value)

    def _create_mms_value(self, value: Any) -> Any:
        """Create MmsValue from Python type."""
        try:
            if isinstance(value, bool):
                return iec61850.MmsValue_newBoolean(value)
            elif isinstance(value, int):
                return iec61850.MmsValue_newIntegerFromInt32(value)
            elif isinstance(value, float):
                return iec61850.MmsValue_newFloat(value)
            elif isinstance(value, str):
                return iec61850.MmsValue_newVisibleString(value)
            else:
                return None
        except Exception as e:
            logger.debug(f"Failed to create MmsValue: {e}")
            return None

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> "MMSClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - ensures disconnect."""
        self.disconnect()
        return False

    def __del__(self):
        """Destructor - ensure cleanup."""
        try:
            self.disconnect()
        except Exception:
            pass

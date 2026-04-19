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
    FileTransferError,
    LibraryNotFoundError,
    MMSError,
    NotConnectedError,
    ReadError,
    WriteError,
)
from .tls import (
    TLSConfig,
    create_tls_configuration,
    create_tls_connection,
    destroy_tls_configuration,
)
from .utils import (
    IdentityGuard,
    LinkedListGuard,
    mms_value_to_python,
    safe_mms_value_delete,
    unpack_result,
)


_FC_NAMES = (
    "ST", "MX", "SP", "SV", "CF", "DC", "SG", "SE",
    "SR", "OR", "BL", "EX", "CO", "US", "MS", "RP",
    "BR", "LG", "GO",
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
    DEFAULT_TLS_PORT = 3782
    DEFAULT_TIMEOUT = 10000  # 10 seconds

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_pdu_size: Optional[int] = None,
        tls: Optional[TLSConfig] = None,
    ):
        """
        Initialize MMS client.

        Connection parameters can be supplied here and reused by later
        calls to ``connect()`` (or by ``__enter__`` auto-connect). They
        can also be overridden per-call.

        Args:
            host: Optional default server hostname. If provided, the
                context-manager form auto-connects on entry.
            port: Default server port.
            timeout: Default connection timeout in milliseconds.
            max_pdu_size: Default max MMS PDU size in bytes, or None to
                use libiec61850's default.
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        self._connection = None
        self._host: Optional[str] = host
        if port is None:
            port = self.DEFAULT_TLS_PORT if tls is not None else self.DEFAULT_PORT
        self._port: int = port
        self._timeout: int = timeout
        self._max_pdu_size: Optional[int] = max_pdu_size
        self._tls_config: Optional[TLSConfig] = tls
        self._native_tls_config: Any = None

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
        host: Optional[str] = None,
        port: Optional[int] = None,
        timeout: Optional[int] = None,
        max_pdu_size: Optional[int] = None,
    ) -> bool:
        """
        Connect to MMS server.

        All arguments default to the values supplied to ``__init__``; any
        given here override those defaults for this connect call (and
        become the new stored defaults).

        Args:
            host: Server hostname or IP address
            port: Server port (default 102)
            timeout: Connection timeout in milliseconds
            max_pdu_size: Optional max MMS PDU size in bytes. Must be set
                before the MMS association is negotiated, so it can only
                be applied here — not via a post-connect setter.
                libiec61850's default is 65000
                (CONFIG_MMS_MAXIMUM_PDU_SIZE); lower it only for servers
                that advertise a smaller PDU.

        Returns:
            True if connected successfully

        Raises:
            ConnectionFailedError: If connection fails
            ValueError: If no host was supplied here or via __init__
        """
        if self.is_connected:
            self.disconnect()

        if host is not None:
            self._host = host
        if port is not None:
            self._port = port
        if timeout is not None:
            self._timeout = timeout
        if max_pdu_size is not None:
            self._max_pdu_size = max_pdu_size

        if self._host is None:
            raise ValueError("connect() requires host (pass to __init__ or connect)")

        host = self._host
        port = self._port
        timeout = self._timeout
        max_pdu_size = self._max_pdu_size

        try:
            if self._tls_config is not None:
                self._native_tls_config = create_tls_configuration(self._tls_config)
                self._connection = create_tls_connection(self._native_tls_config)
            else:
                self._connection = iec61850.IedConnection_create()
            if not self._connection:
                raise ConnectionFailedError(host, port, "Failed to create connection")

            iec61850.IedConnection_setConnectTimeout(self._connection, timeout)

            if max_pdu_size is not None:
                mms_conn = iec61850.IedConnection_getMmsConnection(self._connection)
                if not mms_conn:
                    raise ConnectionFailedError(
                        host, port, "IedConnection has no MmsConnection"
                    )
                iec61850.MmsConnection_setLocalDetail(mms_conn, max_pdu_size)
                logger.debug(f"max PDU size set to {max_pdu_size} bytes")

            # IedConnection_connect returns void in C; the SWIG typemap for
            # IedClientError* turns that into a (None, error_code) tuple.
            result = iec61850.IedConnection_connect(self._connection, host, port)
            if isinstance(result, tuple):
                error = result[1]
            else:
                error = result

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

    def set_request_timeout(self, timeout_ms: int) -> None:
        """
        Set the per-request MMS timeout.

        Controls how long the client waits for a response before giving up
        on an individual Read/Write/etc. libiec61850's default is 5000 ms
        (CONFIG_MMS_CONNECTION_DEFAULT_TIMEOUT). Raise it for slow servers
        that take >5 s to service a request; lower it for tighter SLAs.

        Args:
            timeout_ms: Timeout in milliseconds.

        Raises:
            NotConnectedError: If called before connect().
        """
        self._ensure_connected()
        iec61850.IedConnection_setRequestTimeout(self._connection, timeout_ms)
        logger.debug(f"request timeout set to {timeout_ms} ms")

    def _cleanup(self) -> None:
        """Clean up connection resources."""
        if self._connection:
            try:
                iec61850.IedConnection_destroy(self._connection)
            except Exception:
                pass
        self._connection = None
        # Order matters: the IedConnection may hold a reference to the native
        # TLS configuration, so destroy the connection first, then the TLS
        # config.
        if self._native_tls_config is not None:
            try:
                destroy_tls_configuration(self._native_tls_config)
            except Exception:
                pass
            self._native_tls_config = None

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
            # libiec61850 exports this as getLogicalDeviceDirectory — the
            # "device directory" IS the list of logical nodes under a given
            # logical device. There is no function literally called
            # getLogicalNodeList (an earlier draft of this wrapper assumed
            # one existed; the mocked unit tests hid the typo).
            result = iec61850.IedConnection_getLogicalDeviceDirectory(
                self._connection, device
            )
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

    def read_value(self, reference: str, fc: Any = None) -> Any:
        """
        Read a variable value by reference.

        Args:
            reference: Full object reference (e.g., "device/LN.DO.DA").
                May include a trailing "[FC]" suffix (e.g. "LD0/MMXU1.TotW.mag.f[MX]")
                which will be parsed and stripped.
            fc: Functional constraint. Accepts an int (iec61850.IEC61850_FC_*),
                a two-letter string ("ST", "MX", "CF", ...), or None.
                If None and the reference has no [FC] suffix, defaults to ST.

        Returns:
            Python value (converted from MmsValue)

        Raises:
            NotConnectedError: If not connected
            ReadError: If read fails
        """
        self._ensure_connected()

        # Parse optional [FC] suffix in the reference.
        if reference.endswith("]") and "[" in reference:
            ref_body, suffix = reference.rsplit("[", 1)
            suffix = suffix[:-1]
            if suffix in _FC_NAMES:
                reference = ref_body
                if fc is None:
                    fc = suffix

        if fc is None:
            fc = iec61850.IEC61850_FC_ST
        elif isinstance(fc, str):
            fc = getattr(iec61850, f"IEC61850_FC_{fc.upper()}", iec61850.IEC61850_FC_ST)

        mms_value = None
        try:
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

    def read_dataset(self, dataset_ref: str) -> List[Any]:
        """
        Read all values of a dataset in a single MMS request.

        Much faster than calling read_value() per attribute: one request and
        one response for the whole dataset, so the round-trip cost is paid
        once instead of N times.

        Implementation note: this calls the MMS-layer primitive
        `MmsConnection_readNamedVariableListValues` rather than the
        IedConnection-layer `readDataSetValues`. The latter takes a
        `ClientDataSet` input parameter for which pyiec61850's SWIG wrapper
        applies a NULL-safety typemap that rejects the "allocate a new one"
        sentinel, so it is unusable from Python today.

        Args:
            dataset_ref: Dataset reference, either
                "LDName/LNName.DataSetName" or "LDName/LNName$DataSetName".
                Example: "simpleIOGenericIO/LLN0.Events".

        Returns:
            List of Python values, one per dataset member, in dataset order.
            Uses `mms_value_to_python` semantics: structures become dicts,
            arrays become lists, scalars become bool/int/float/str/bytes.

        Raises:
            NotConnectedError: If not connected
            ReadError: If the read fails or the reference is malformed
        """
        self._ensure_connected()

        slash = dataset_ref.find("/")
        if slash <= 0 or slash == len(dataset_ref) - 1:
            raise ReadError(
                f"Invalid dataset reference '{dataset_ref}': "
                "expected 'LDName/LNName.DataSetName' or "
                "'LDName/LNName$DataSetName'"
            )
        domain_id = dataset_ref[:slash]
        item_id = dataset_ref[slash + 1:].replace(".", "$")

        mms_conn = iec61850.IedConnection_getMmsConnection(self._connection)
        if not mms_conn:
            raise ReadError("IedConnection has no MmsConnection")

        # MmsConnection_readNamedVariableListValues expects a caller-owned
        # MmsError* as its second arg — the %typemap(numinputs=0) in the
        # SWIG bindings only intercepts `IedClientError* error`, not
        # `MmsError* mmsError`, so we allocate one ourselves.
        mms_error = iec61850.MmsError_create()
        values = None
        try:
            values = iec61850.MmsConnection_readNamedVariableListValues(
                mms_conn, mms_error, domain_id, item_id, False
            )
            error_code = iec61850.MmsError_getValue(mms_error)

            if error_code != 0:
                raise ReadError(
                    f"Dataset read failed for {dataset_ref}: "
                    f"MMS error {iec61850.MmsError_toString(mms_error)}"
                )
            if not values:
                raise ReadError(f"Dataset read returned no data for {dataset_ref}")

            size = iec61850.MmsValue_getArraySize(values)
            out: List[Any] = []
            for i in range(size):
                member = iec61850.MmsValue_getElement(values, i)
                out.append(mms_value_to_python(member))
            return out

        except NotConnectedError:
            raise
        except ReadError:
            raise
        except Exception as e:
            raise ReadError(f"Failed to read dataset {dataset_ref}: {e}")
        finally:
            if values:
                safe_mms_value_delete(values)
            # Note: the SWIG wrapper exports the destructor as
            # `MmsErrror_destroy` (triple-r typo in patches/iec61850.i).
            iec61850.MmsErrror_destroy(mms_error)

    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from the MMS server to the local filesystem.

        Args:
            remote_path: Path of the file on the server.
            local_path: Local destination path. The caller is responsible for
                ensuring the parent directory exists. On failure any
                partial file is automatically cleaned up so the caller
                gets either the complete file or nothing.

        Raises:
            NotConnectedError: If not connected.
            FileTransferError: If the download fails.
        """
        self._ensure_connected()

        mms_conn = iec61850.IedConnection_getMmsConnection(self._connection)
        if not mms_conn:
            raise MMSError("IedConnection has no MmsConnection")

        import os

        mms_error = iec61850.MmsError_create()
        succeeded = False
        try:
            ok = iec61850.MmsConnection_downloadFile(
                mms_conn, mms_error, remote_path, local_path
            )
            code = iec61850.MmsError_getValue(mms_error)
            if not ok or code != 0:
                # MmsError_toString takes the enum value (int), not the
                # opaque wrapper returned by MmsError_create. Passing the
                # wrapper raises TypeError from SWIG.
                raise FileTransferError(
                    f"Download of {remote_path!r} failed: "
                    f"{iec61850.MmsError_toString(code)}"
                )
            succeeded = True
        finally:
            # Note: the SWIG wrapper exports the destructor as
            # `MmsErrror_destroy` (triple-r typo in patches/iec61850.i).
            iec61850.MmsErrror_destroy(mms_error)
            # libiec61850 opens the local file before it checks whether
            # the remote file exists, so a failed download leaves a 0-byte
            # turd on disk. Clean it up so the caller gets either the
            # full file or nothing — never a partial artefact.
            if not succeeded and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except OSError as e:
                    logger.debug(f"could not unlink partial {local_path}: {e}")

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
        """Context manager entry — auto-connects if host was given to __init__."""
        if self._host is not None and not self.is_connected:
            self.connect()
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

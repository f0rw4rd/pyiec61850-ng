#!/usr/bin/env python3
"""
TASE.2/ICCP Connection Layer (IEC 60870-6)

This module provides a low-level MMS connection wrapper for TASE.2 operations.
It handles connection management, ISO parameters, and raw MMS function calls.
"""

from typing import Any, List, Optional, Tuple
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .constants import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    STATE_DISCONNECTED,
    STATE_CONNECTING,
    STATE_CONNECTED,
    STATE_CLOSING,
    MMS_ERROR_NONE,
    MAX_DATA_SET_SIZE,
)
from .exceptions import (
    LibraryNotFoundError,
    ConnectionFailedError,
    ConnectionTimeoutError,
    ConnectionClosedError,
    NotConnectedError,
    TASE2Error,
)

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Check if pyiec61850 library is available."""
    return _HAS_IEC61850


class MmsConnectionWrapper:
    """
    Low-level wrapper around pyiec61850 MMS connection.

    Provides connection management and raw MMS operations
    for TASE.2 protocol implementation.
    """

    def __init__(
        self,
        local_ap_title: Optional[str] = None,
        remote_ap_title: Optional[str] = None,
        local_ae_qualifier: int = 12,
        remote_ae_qualifier: int = 12,
    ):
        """
        Initialize MMS connection wrapper.

        Args:
            local_ap_title: Local Application Process title (e.g., "1.1.1.999")
            remote_ap_title: Remote Application Process title
            local_ae_qualifier: Local Application Entity qualifier
            remote_ae_qualifier: Remote Application Entity qualifier
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        self._connection = None
        self._mms_connection = None
        self._state = STATE_DISCONNECTED
        self._host: Optional[str] = None
        self._port: int = DEFAULT_PORT
        self._timeout: int = DEFAULT_TIMEOUT

        # ISO parameters
        self._local_ap_title = local_ap_title
        self._remote_ap_title = remote_ap_title
        self._local_ae_qualifier = local_ae_qualifier
        self._remote_ae_qualifier = remote_ae_qualifier

    @property
    def state(self) -> int:
        """Return current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._state == STATE_CONNECTED and self._connection is not None

    @property
    def host(self) -> Optional[str]:
        """Return connected host."""
        return self._host

    @property
    def port(self) -> int:
        """Return connected port."""
        return self._port

    def connect(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """
        Connect to TASE.2/MMS server.

        Args:
            host: Server hostname or IP address
            port: Server port (default 102)
            timeout: Connection timeout in milliseconds

        Returns:
            True if connected successfully

        Raises:
            ConnectionFailedError: If connection fails
            ConnectionTimeoutError: If connection times out
        """
        if self.is_connected:
            self.disconnect()

        self._host = host
        self._port = port
        self._timeout = timeout
        self._state = STATE_CONNECTING

        try:
            # Create IED connection
            self._connection = iec61850.IedConnection_create()
            if not self._connection:
                raise ConnectionFailedError(host, port, "Failed to create connection object")

            # Set timeout
            iec61850.IedConnection_setConnectTimeout(self._connection, timeout)

            # Configure ISO parameters if provided
            if self._local_ap_title or self._remote_ap_title:
                self._configure_iso_parameters()

            # Connect to server
            error = iec61850.IedConnection_connect(self._connection, host, port)

            if error != iec61850.IED_ERROR_OK:
                error_str = self._get_error_string(error)
                self._cleanup()
                raise ConnectionFailedError(host, port, error_str)

            self._state = STATE_CONNECTED
            logger.info(f"Connected to TASE.2 server at {host}:{port}")
            return True

        except ConnectionFailedError:
            raise
        except Exception as e:
            self._cleanup()
            raise ConnectionFailedError(host, port, str(e))

    def _configure_iso_parameters(self) -> None:
        """Configure ISO connection parameters (AP titles, selectors)."""
        if not self._connection:
            return

        try:
            # Get MMS connection for parameter configuration
            mms_conn = iec61850.IedConnection_getMmsConnection(self._connection)
            if not mms_conn:
                return

            # Get ISO parameters object
            iso_params = iec61850.MmsConnection_getIsoConnectionParameters(mms_conn)
            if not iso_params:
                return

            # Set AP titles if provided
            if self._local_ap_title:
                self._set_ap_title(iso_params, self._local_ap_title, is_local=True)

            if self._remote_ap_title:
                self._set_ap_title(iso_params, self._remote_ap_title, is_local=False)

        except Exception as e:
            logger.warning(f"Failed to configure ISO parameters: {e}")

    def _set_ap_title(self, iso_params: Any, ap_title: str, is_local: bool) -> None:
        """Set Application Process title from dot-separated string."""
        try:
            # Validate AP title format (e.g., "1.1.1.999")
            # Format: dot-separated integers forming an OID
            try:
                [int(p) for p in ap_title.split(".")]
            except ValueError:
                logger.warning(f"Invalid AP title format: {ap_title}")
                return

            # Try to set the AP title using the pyiec61850 API
            if is_local:
                if hasattr(iec61850, 'IsoConnectionParameters_setLocalApTitle'):
                    iec61850.IsoConnectionParameters_setLocalApTitle(
                        iso_params, ap_title, self._local_ae_qualifier
                    )
                    logger.debug(f"Set local AP title: {ap_title}")
                else:
                    logger.debug(f"Local AP title API not available: {ap_title}")
            else:
                if hasattr(iec61850, 'IsoConnectionParameters_setRemoteApTitle'):
                    iec61850.IsoConnectionParameters_setRemoteApTitle(
                        iso_params, ap_title, self._remote_ae_qualifier
                    )
                    logger.debug(f"Set remote AP title: {ap_title}")
                else:
                    logger.debug(f"Remote AP title API not available: {ap_title}")

        except Exception as e:
            logger.warning(f"Failed to set AP title {ap_title}: {e}")

    def disconnect(self) -> None:
        """Disconnect from server."""
        if self._state == STATE_DISCONNECTED:
            return

        self._state = STATE_CLOSING
        logger.info(f"Disconnecting from {self._host}:{self._port}")

        try:
            if self._connection:
                iec61850.IedConnection_close(self._connection)
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
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
        self._mms_connection = None
        self._state = STATE_DISCONNECTED

    def _get_error_string(self, error: int) -> str:
        """Get human-readable error string."""
        try:
            return iec61850.IedClientError_toString(error)
        except Exception:
            return f"Error code: {error}"

    def _ensure_connected(self) -> None:
        """Ensure connection is active."""
        if not self.is_connected:
            raise NotConnectedError()

    # =========================================================================
    # MMS Domain Operations
    # =========================================================================

    def get_domain_names(self) -> List[str]:
        """
        Get list of MMS domain names (VCC/ICC domains).

        Returns:
            List of domain name strings

        Raises:
            NotConnectedError: If not connected
            TASE2Error: If operation fails
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_getLogicalDeviceList(self._connection)

            # Handle tuple return (list, error)
            if isinstance(result, tuple):
                domain_list, error = result
                if error != iec61850.IED_ERROR_OK:
                    raise TASE2Error(f"Failed to get domains: {self._get_error_string(error)}")
            else:
                domain_list = result

            domains = []
            if domain_list:
                element = iec61850.LinkedList_getNext(domain_list)
                while element:
                    data = iec61850.LinkedList_getData(element)
                    if data:
                        domain_name = iec61850.toCharP(data)
                        if domain_name:
                            domains.append(domain_name)
                    element = iec61850.LinkedList_getNext(element)
                iec61850.LinkedList_destroy(domain_list)

            return domains

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to get domain names: {e}")

    def get_domain_variables(self, domain: str) -> List[str]:
        """
        Get list of variable names in a domain.

        Args:
            domain: Domain name

        Returns:
            List of variable name strings
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_getLogicalNodeList(self._connection, domain)

            if isinstance(result, tuple):
                var_list, error = result
                if error != iec61850.IED_ERROR_OK:
                    raise TASE2Error(f"Failed to get variables: {self._get_error_string(error)}")
            else:
                var_list = result

            variables = []
            if var_list:
                element = iec61850.LinkedList_getNext(var_list)
                while element:
                    data = iec61850.LinkedList_getData(element)
                    if data:
                        var_name = iec61850.toCharP(data)
                        if var_name:
                            variables.append(var_name)
                    element = iec61850.LinkedList_getNext(element)
                iec61850.LinkedList_destroy(var_list)

            return variables

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to get domain variables: {e}")

    def get_data_set_names(self, domain: str) -> List[str]:
        """
        Get list of data set names in a domain.

        Args:
            domain: Domain name

        Returns:
            List of data set name strings
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_getLogicalNodeDirectory(
                self._connection, domain, iec61850.ACSI_CLASS_DATA_SET
            )

            if isinstance(result, tuple):
                ds_list, error = result
                if error != iec61850.IED_ERROR_OK:
                    return []  # Data sets may not exist
            else:
                ds_list = result

            data_sets = []
            if ds_list:
                element = iec61850.LinkedList_getNext(ds_list)
                while element:
                    data = iec61850.LinkedList_getData(element)
                    if data:
                        ds_name = iec61850.toCharP(data)
                        if ds_name:
                            data_sets.append(ds_name)
                    element = iec61850.LinkedList_getNext(element)
                iec61850.LinkedList_destroy(ds_list)

            return data_sets

        except Exception as e:
            logger.debug(f"Failed to get data sets for {domain}: {e}")
            return []

    def read_data_set_values(self, domain: str, name: str) -> List[Any]:
        """
        Read all values from a data set.

        Args:
            domain: Domain name
            name: Data set name

        Returns:
            List of MmsValue objects
        """
        self._ensure_connected()

        try:
            # Construct data set reference
            ds_ref = f"{domain}/{name}"

            result = iec61850.IedConnection_readDataSetValues(
                self._connection, ds_ref, None
            )

            if isinstance(result, tuple):
                data_set, error = result
                if error != iec61850.IED_ERROR_OK:
                    raise TASE2Error(f"Read data set failed: {self._get_error_string(error)}")
            else:
                data_set = result

            values = []
            if data_set:
                # Get number of members and values ONCE (fixed bug)
                try:
                    count = iec61850.ClientDataSet_getDataSetSize(data_set)

                    # Check data set size limit per IEC 60870-6
                    if count > MAX_DATA_SET_SIZE:
                        logger.warning(
                            f"Data set {domain}/{name} has {count} members, "
                            f"exceeding TASE.2 limit of {MAX_DATA_SET_SIZE}"
                        )

                    all_values = iec61850.ClientDataSet_getValues(data_set)
                    if all_values:
                        for i in range(count):
                            member = iec61850.MmsValue_getElement(all_values, i)
                            if member:
                                values.append(member)
                except Exception as e:
                    logger.debug(f"Error extracting data set values: {e}")

            return values

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to read data set {domain}/{name}: {e}")

    # =========================================================================
    # MMS Variable Operations
    # =========================================================================

    def read_variable(self, domain: str, variable: str) -> Any:
        """
        Read a variable value.

        Args:
            domain: Domain name
            variable: Variable name

        Returns:
            MmsValue object or Python value
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_readObject(
                self._connection, domain, variable
            )

            if isinstance(result, tuple):
                value, error = result
                if error != iec61850.IED_ERROR_OK:
                    raise TASE2Error(f"Read failed: {self._get_error_string(error)}")
                return value
            return result

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to read {domain}/{variable}: {e}")

    def _create_mms_value(self, value: Any) -> Any:
        """
        Create MmsValue from Python value.

        Args:
            value: Python value (bool, int, float, or str)

        Returns:
            MmsValue object or original value if already MmsValue
        """
        try:
            # Check if it's already an MmsValue (has MMS type info)
            if hasattr(value, '__class__') and 'MmsValue' in str(type(value)):
                return value

            # Create appropriate MmsValue based on Python type
            if isinstance(value, bool):
                if hasattr(iec61850, 'MmsValue_newBoolean'):
                    return iec61850.MmsValue_newBoolean(value)
            elif isinstance(value, int):
                if hasattr(iec61850, 'MmsValue_newIntegerFromInt32'):
                    return iec61850.MmsValue_newIntegerFromInt32(value)
                elif hasattr(iec61850, 'MmsValue_newInteger'):
                    return iec61850.MmsValue_newInteger(value)
            elif isinstance(value, float):
                if hasattr(iec61850, 'MmsValue_newFloat'):
                    return iec61850.MmsValue_newFloat(value)
            elif isinstance(value, str):
                if hasattr(iec61850, 'MmsValue_newVisibleString'):
                    return iec61850.MmsValue_newVisibleString(value)

            # Return original value if no conversion available
            return value

        except Exception as e:
            logger.debug(f"Failed to create MmsValue: {e}")
            return value

    def write_variable(self, domain: str, variable: str, value: Any) -> bool:
        """
        Write a variable value.

        Args:
            domain: Domain name
            variable: Variable name
            value: Value to write (MmsValue or Python value)

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Convert Python value to MmsValue if needed
        mms_value = self._create_mms_value(value)
        created_value = mms_value is not value

        try:
            error = iec61850.IedConnection_writeObject(
                self._connection, domain, variable, mms_value
            )

            if error != iec61850.IED_ERROR_OK:
                raise TASE2Error(f"Write failed: {self._get_error_string(error)}")

            return True

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to write {domain}/{variable}: {e}")
        finally:
            # Clean up if we created the MmsValue
            if created_value and hasattr(iec61850, 'MmsValue_delete'):
                try:
                    iec61850.MmsValue_delete(mms_value)
                except Exception:
                    pass

    # =========================================================================
    # Server Information
    # =========================================================================

    def get_server_identity(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get server identity information.

        Returns:
            Tuple of (vendor, model, revision)
        """
        self._ensure_connected()

        try:
            result = iec61850.IedConnection_identify(self._connection)

            if isinstance(result, tuple) and len(result) >= 2:
                identity, error = result[0], result[1]
                if error == iec61850.IED_ERROR_OK and identity:
                    vendor = getattr(identity, 'vendorName', None)
                    model = getattr(identity, 'modelName', None)
                    revision = getattr(identity, 'revision', None)
                    return (vendor, model, revision)

            return (None, None, None)

        except Exception as e:
            logger.debug(f"Failed to get server identity: {e}")
            return (None, None, None)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False

    def __del__(self):
        """Destructor - ensure cleanup."""
        try:
            self.disconnect()
        except Exception:
            pass

#!/usr/bin/env python3
"""
TASE.2/ICCP Client (IEC 60870-6)

This module provides the main TASE2Client class for TASE.2 protocol
operations including discovery, data access, and control.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

from .connection import MmsConnectionWrapper, is_available
from .types import (
    DataFlags,
    Domain,
    Variable,
    PointValue,
    ControlPoint,
    DataSet,
    TransferSet,
    BilateralTable,
    ServerInfo,
)
from .constants import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    QUALITY_GOOD,
    QUALITY_INVALID,
    BLOCK_1,
    BLOCK_2,
    BLOCK_5,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    SBO_TIMEOUT,
)
from .exceptions import (
    TASE2Error,
    NotConnectedError,
    ConnectionFailedError,
    DomainNotFoundError,
    VariableNotFoundError,
    ReadError,
    WriteError,
    ControlError,
    SelectError,
    OperateError,
)

logger = logging.getLogger(__name__)

# MMS type constants - loaded from libiec61850 at module init
# These are cached to avoid repeated getattr calls and provide consistent fallbacks
_MMS_TYPES = {}


def _init_mms_types():
    """Initialize MMS type constants from libiec61850 library."""
    global _MMS_TYPES
    # Correct MMS type values per libiec61850 src/mms/inc/mms_common.h
    # These fallbacks match the actual libiec61850 MmsType enum values
    FALLBACK_MMS_TYPES = {
        'ARRAY': 0,
        'STRUCTURE': 1,
        'BOOLEAN': 2,
        'BIT_STRING': 3,
        'INTEGER': 4,
        'UNSIGNED': 5,
        'FLOAT': 6,
        'OCTET_STRING': 7,
        'VISIBLE_STRING': 8,
        'GENERALIZED_TIME': 9,
        'BINARY_TIME': 10,
        'BCD': 11,
        'OBJ_ID': 12,
        'STRING': 13,
        'UTC_TIME': 14,
        'DATA_ACCESS_ERROR': 15,
    }
    try:
        import pyiec61850.pyiec61850 as iec61850
        _MMS_TYPES = {
            'ARRAY': getattr(iec61850, 'MMS_ARRAY', FALLBACK_MMS_TYPES['ARRAY']),
            'STRUCTURE': getattr(iec61850, 'MMS_STRUCTURE', FALLBACK_MMS_TYPES['STRUCTURE']),
            'BOOLEAN': getattr(iec61850, 'MMS_BOOLEAN', FALLBACK_MMS_TYPES['BOOLEAN']),
            'BIT_STRING': getattr(iec61850, 'MMS_BIT_STRING', FALLBACK_MMS_TYPES['BIT_STRING']),
            'INTEGER': getattr(iec61850, 'MMS_INTEGER', FALLBACK_MMS_TYPES['INTEGER']),
            'UNSIGNED': getattr(iec61850, 'MMS_UNSIGNED', FALLBACK_MMS_TYPES['UNSIGNED']),
            'FLOAT': getattr(iec61850, 'MMS_FLOAT', FALLBACK_MMS_TYPES['FLOAT']),
            'OCTET_STRING': getattr(iec61850, 'MMS_OCTET_STRING', FALLBACK_MMS_TYPES['OCTET_STRING']),
            'VISIBLE_STRING': getattr(iec61850, 'MMS_VISIBLE_STRING', FALLBACK_MMS_TYPES['VISIBLE_STRING']),
            'STRING': getattr(iec61850, 'MMS_STRING', FALLBACK_MMS_TYPES['STRING']),
            'UTC_TIME': getattr(iec61850, 'MMS_UTC_TIME', FALLBACK_MMS_TYPES['UTC_TIME']),
        }
        logger.debug(f"MMS type constants loaded: {_MMS_TYPES}")
    except ImportError:
        # Use fallback values if library not available
        _MMS_TYPES = FALLBACK_MMS_TYPES.copy()
        logger.warning("Using fallback MMS type constants - library not available")


# Initialize MMS types when module loads
_init_mms_types()


def _validate_point_name(name: str) -> bool:
    """
    Validate TASE.2 data point name per IEC 60870-6-503.

    Rules:
    - Must not be empty
    - Can only contain A-Z, a-z, 0-9, and underscore
    - Cannot start with a digit
    - Maximum length is 32 characters

    Args:
        name: The data point name to validate

    Returns:
        True if valid, False otherwise
    """
    from .constants import MAX_POINT_NAME_LENGTH

    if not name:
        return False
    if len(name) > MAX_POINT_NAME_LENGTH:
        return False
    if name[0].isdigit():
        return False
    return all(c.isalnum() or c == '_' for c in name)


class TASE2Client:
    """
    TASE.2/ICCP Protocol Client.

    Provides high-level API for TASE.2 operations including:
    - Domain (VCC/ICC) discovery
    - Variable enumeration and data access
    - Transfer set management (Block 2)
    - Device control operations (Block 5)
    - Bilateral table queries

    Example:
        >>> from pyiec61850.tase2 import TASE2Client
        >>>
        >>> client = TASE2Client(
        ...     local_ap_title="1.1.1.999",
        ...     remote_ap_title="1.1.1.998"
        ... )
        >>> client.connect("192.168.1.100", port=102)
        >>>
        >>> # Discover domains
        >>> domains = client.get_domains()
        >>> for domain in domains:
        ...     print(f"Domain: {domain.name}")
        >>>
        >>> # Read a data point
        >>> value = client.read_point("ICC1", "Voltage")
        >>> print(f"Value: {value.value}, Quality: {value.quality}")
        >>>
        >>> client.disconnect()
    """

    def __init__(
        self,
        local_ap_title: Optional[str] = None,
        remote_ap_title: Optional[str] = None,
        local_ae_qualifier: int = 12,
        remote_ae_qualifier: int = 12,
    ):
        """
        Initialize TASE.2 client.

        Args:
            local_ap_title: Local Application Process title (e.g., "1.1.1.999")
            remote_ap_title: Remote Application Process title
            local_ae_qualifier: Local Application Entity qualifier
            remote_ae_qualifier: Remote Application Entity qualifier
        """
        self._connection = MmsConnectionWrapper(
            local_ap_title=local_ap_title,
            remote_ap_title=remote_ap_title,
            local_ae_qualifier=local_ae_qualifier,
            remote_ae_qualifier=remote_ae_qualifier,
        )
        self._local_ap_title = local_ap_title
        self._remote_ap_title = remote_ap_title

        # Cached discovery data
        self._domains: Dict[str, Domain] = {}
        self._server_info: Optional[ServerInfo] = None

        # SBO (Select-Before-Operate) tracking
        # Maps device key (domain/device) to select timestamp
        self._sbo_select_times: Dict[str, float] = {}

    # =========================================================================
    # Connection Management
    # =========================================================================

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connection.is_connected

    @property
    def state(self) -> int:
        """Return current client state."""
        return self._connection.state

    @property
    def host(self) -> Optional[str]:
        """Return connected host."""
        return self._connection.host

    @property
    def port(self) -> int:
        """Return connected port."""
        return self._connection.port

    def connect(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """
        Connect to TASE.2 server.

        Args:
            host: Server hostname or IP address
            port: Server port (default 102)
            timeout: Connection timeout in milliseconds

        Returns:
            True if connected successfully

        Raises:
            ConnectionFailedError: If connection fails
        """
        # Clear cached data
        self._domains.clear()
        self._server_info = None

        return self._connection.connect(host, port, timeout)

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._connection.disconnect()
        self._domains.clear()
        self._server_info = None
        self._sbo_select_times.clear()

    def _ensure_connected(self) -> None:
        """Ensure connection is active."""
        if not self.is_connected:
            raise NotConnectedError()

    # =========================================================================
    # Domain Discovery
    # =========================================================================

    def get_domains(self, refresh: bool = False) -> List[Domain]:
        """
        Get list of TASE.2 domains (VCC/ICC).

        Args:
            refresh: Force refresh from server (ignore cache)

        Returns:
            List of Domain objects
        """
        self._ensure_connected()

        if not refresh and self._domains:
            return list(self._domains.values())

        try:
            domain_names = self._connection.get_domain_names()
            self._domains.clear()

            for name in domain_names:
                # Determine if VCC based on naming convention
                is_vcc = name.upper().startswith("VCC") or name.upper() == "VCC"

                # Get variables for this domain
                try:
                    variables = self._connection.get_domain_variables(name)
                except Exception:
                    variables = []

                # Get data sets for this domain
                try:
                    data_sets = self._connection.get_data_set_names(name)
                except Exception:
                    data_sets = []

                domain = Domain(
                    name=name,
                    is_vcc=is_vcc,
                    variables=variables,
                    data_sets=data_sets,
                )
                self._domains[name] = domain

            return list(self._domains.values())

        except NotConnectedError:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to get domains: {e}")

    def get_domain(self, name: str) -> Domain:
        """
        Get a specific domain by name.

        Args:
            name: Domain name

        Returns:
            Domain object

        Raises:
            DomainNotFoundError: If domain not found
        """
        if not self._domains:
            self.get_domains()

        if name not in self._domains:
            raise DomainNotFoundError(name)

        return self._domains[name]

    # =========================================================================
    # Variable Discovery
    # =========================================================================

    def get_vcc_variables(self) -> List[str]:
        """
        Get VCC-scope variables.

        Returns:
            List of variable names
        """
        self._ensure_connected()

        # Find VCC domain
        domains = self.get_domains()
        for domain in domains:
            if domain.is_vcc:
                return domain.variables

        return []

    def get_domain_variables(self, domain: str) -> List[str]:
        """
        Get variables for a specific domain.

        Args:
            domain: Domain name

        Returns:
            List of variable names
        """
        self._ensure_connected()

        try:
            return self._connection.get_domain_variables(domain)
        except Exception as e:
            logger.warning(f"Failed to get variables for {domain}: {e}")
            return []

    # =========================================================================
    # Data Point Access
    # =========================================================================

    def read_point(self, domain: str, name: str) -> PointValue:
        """
        Read a data point value.

        Args:
            domain: Domain name
            name: Variable name

        Returns:
            PointValue with value, quality, and optional timestamp

        Raises:
            ReadError: If read fails
        """
        self._ensure_connected()

        # Validate point name per IEC 60870-6-503 (warn only for backward compat)
        if not _validate_point_name(name):
            logger.warning(
                f"Invalid TASE.2 point name '{name}' - names should contain only "
                "alphanumeric characters and underscores, not start with a digit, "
                "and be max 32 characters"
            )

        raw_value = None
        try:
            raw_value = self._connection.read_variable(domain, name)
            return self._parse_point_value(raw_value, domain, name)

        except NotConnectedError:
            raise
        except TASE2Error as e:
            raise ReadError(f"{domain}/{name}", str(e))
        except Exception as e:
            raise ReadError(f"{domain}/{name}", str(e))
        finally:
            # Clean up MmsValue to prevent memory leaks
            self._cleanup_mms_value(raw_value)

    def read_points(
        self,
        points: List[tuple],
    ) -> List[PointValue]:
        """
        Read multiple data points.

        Args:
            points: List of (domain, name) tuples

        Returns:
            List of PointValue objects
        """
        results = []
        for domain, name in points:
            try:
                value = self.read_point(domain, name)
                results.append(value)
            except Exception as e:
                # Return invalid value on error
                results.append(PointValue(
                    value=None,
                    quality=QUALITY_INVALID,
                    name=name,
                    domain=domain,
                ))
                logger.warning(f"Failed to read {domain}/{name}: {e}")

        return results

    def write_point(self, domain: str, name: str, value: Any) -> bool:
        """
        Write a data point value.

        Args:
            domain: Domain name
            name: Variable name
            value: Value to write

        Returns:
            True if successful

        Raises:
            WriteError: If write fails
        """
        self._ensure_connected()

        # Validate point name per IEC 60870-6-503 (warn only for backward compat)
        if not _validate_point_name(name):
            logger.warning(
                f"Invalid TASE.2 point name '{name}' - names should contain only "
                "alphanumeric characters and underscores, not start with a digit, "
                "and be max 32 characters"
            )

        try:
            return self._connection.write_variable(domain, name, value)

        except NotConnectedError:
            raise
        except TASE2Error as e:
            raise WriteError(f"{domain}/{name}", str(e))
        except Exception as e:
            raise WriteError(f"{domain}/{name}", str(e))

    def _parse_point_value(
        self,
        raw_value: Any,
        domain: str,
        name: str,
    ) -> PointValue:
        """Parse raw MMS value into PointValue."""
        try:
            # Try to extract value from MMS object
            if raw_value is None:
                return PointValue(
                    value=None,
                    quality=QUALITY_INVALID,
                    flags=DataFlags(validity=12),  # NOT_VALID
                    name=name,
                    domain=domain,
                )

            # Handle different value types
            value = self._extract_value(raw_value)
            flags = self._extract_quality(raw_value)
            timestamp = self._extract_timestamp(raw_value)
            cov_counter = self._extract_cov_counter(raw_value)

            return PointValue(
                value=value,
                quality=flags.validity_name if flags else QUALITY_GOOD,
                flags=flags,
                timestamp=timestamp,
                cov_counter=cov_counter,
                name=name,
                domain=domain,
            )

        except Exception as e:
            logger.debug(f"Failed to parse point value: {e}")
            return PointValue(
                value=raw_value,
                quality=QUALITY_GOOD,
                name=name,
                domain=domain,
            )

    def _extract_value(self, raw_value: Any) -> Any:
        """Extract Python value from MMS value (handles structured types)."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            # Check if this is a structured type (TASE.2 compound value)
            mms_type = iec61850.MmsValue_getType(raw_value)

            # Check for structure using cached type constant
            if mms_type == _MMS_TYPES['STRUCTURE']:
                # TASE.2 structured types: [value, flags?, timestamp?, cov?]
                # First element is always the actual value
                try:
                    value_element = iec61850.MmsValue_getElement(raw_value, 0)
                    if value_element:
                        return self._extract_primitive(value_element)
                except Exception:
                    pass

            # Not a structure, extract as primitive
            return self._extract_primitive(raw_value)

        except Exception:
            return raw_value

    def _extract_primitive(self, mms_value: Any) -> Any:
        """Extract primitive Python value from MMS value."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            mms_type = iec61850.MmsValue_getType(mms_value)

            # Use cached MMS type constants for comparisons
            if mms_type == _MMS_TYPES['FLOAT']:
                return iec61850.MmsValue_toFloat(mms_value)

            if mms_type == _MMS_TYPES['INTEGER']:
                return iec61850.MmsValue_toInt32(mms_value)

            if mms_type == _MMS_TYPES['UNSIGNED']:
                return iec61850.MmsValue_toUint32(mms_value)

            if mms_type == _MMS_TYPES['BOOLEAN']:
                return iec61850.MmsValue_getBoolean(mms_value)

            if mms_type in (_MMS_TYPES['VISIBLE_STRING'], _MMS_TYPES['STRING']):
                return iec61850.MmsValue_toString(mms_value)

            # BIT_STRING (for state values)
            if mms_type == _MMS_TYPES['BIT_STRING']:
                return iec61850.MmsValue_getBitStringAsInteger(mms_value)

            # Try generic float extraction
            try:
                return iec61850.MmsValue_toFloat(mms_value)
            except Exception:
                pass

            # Try int extraction
            try:
                return iec61850.MmsValue_toInt32(mms_value)
            except Exception:
                pass

            return mms_value

        except Exception:
            return mms_value

    def _extract_quality(self, raw_value: Any) -> Optional[DataFlags]:
        """Extract quality flags from MMS structured value."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            mms_type = iec61850.MmsValue_getType(raw_value)

            # Only structures have quality fields
            if mms_type == _MMS_TYPES['STRUCTURE']:
                try:
                    element_count = iec61850.MmsValue_getArraySize(raw_value)
                    # Quality is typically 2nd element in structured types
                    if element_count >= 2:
                        flags_element = iec61850.MmsValue_getElement(raw_value, 1)
                        if flags_element:
                            # Extract as integer
                            flags_type = iec61850.MmsValue_getType(flags_element)
                            if flags_type in (_MMS_TYPES['INTEGER'],
                                             _MMS_TYPES['UNSIGNED'],
                                             _MMS_TYPES['BIT_STRING']):
                                flags_raw = iec61850.MmsValue_toInt32(flags_element)
                                return DataFlags.from_raw(flags_raw)
                except Exception as e:
                    logger.debug(f"Failed to extract quality: {e}")

        except Exception:
            pass

        # Default: valid quality
        return DataFlags()

    def _extract_timestamp(self, raw_value: Any) -> Optional[datetime]:
        """Extract timestamp from MMS structured value."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            mms_type = iec61850.MmsValue_getType(raw_value)

            # Only structures have timestamp fields
            if mms_type == _MMS_TYPES['STRUCTURE']:
                try:
                    element_count = iec61850.MmsValue_getArraySize(raw_value)
                    # Timestamp is typically 3rd element
                    if element_count >= 3:
                        ts_element = iec61850.MmsValue_getElement(raw_value, 2)
                        if ts_element:
                            ts_type = iec61850.MmsValue_getType(ts_element)
                            if ts_type == _MMS_TYPES['UTC_TIME']:
                                epoch_ms = iec61850.MmsValue_getUtcTimeInMs(ts_element)
                                # TASE.2 timestamps are UTC per IEC 60870-6
                                return datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
                except Exception as e:
                    logger.debug(f"Failed to extract timestamp: {e}")

        except Exception:
            pass

        return None

    def _extract_cov_counter(self, raw_value: Any) -> Optional[int]:
        """Extract COV (change-of-value) counter from MMS extended value."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            mms_type = iec61850.MmsValue_getType(raw_value)

            # Only structures have COV counter fields
            if mms_type == _MMS_TYPES['STRUCTURE']:
                try:
                    element_count = iec61850.MmsValue_getArraySize(raw_value)
                    # COV counter is typically 4th element in extended types
                    if element_count >= 4:
                        cov_element = iec61850.MmsValue_getElement(raw_value, 3)
                        if cov_element:
                            return iec61850.MmsValue_toInt32(cov_element)
                except Exception as e:
                    logger.debug(f"Failed to extract COV counter: {e}")

        except Exception:
            pass

        return None

    def _cleanup_mms_value(self, mms_value: Any) -> None:
        """
        Clean up MmsValue object to prevent memory leaks.

        Args:
            mms_value: MmsValue object to delete, or None
        """
        if mms_value is None:
            return

        try:
            import pyiec61850.pyiec61850 as iec61850
            if hasattr(iec61850, 'MmsValue_delete'):
                iec61850.MmsValue_delete(mms_value)
        except Exception as e:
            logger.debug(f"Failed to cleanup MmsValue: {e}")

    # =========================================================================
    # Data Sets
    # =========================================================================

    def get_data_sets(self, domain: Optional[str] = None) -> List[DataSet]:
        """
        Get data sets.

        Args:
            domain: Domain name (if None, get from all domains)

        Returns:
            List of DataSet objects
        """
        self._ensure_connected()

        data_sets = []

        if domain:
            domains_to_check = [domain]
        else:
            domains_to_check = [d.name for d in self.get_domains()]

        for dom in domains_to_check:
            try:
                ds_names = self._connection.get_data_set_names(dom)
                for name in ds_names:
                    data_sets.append(DataSet(name=name, domain=dom))
            except Exception as e:
                logger.debug(f"Failed to get data sets for {dom}: {e}")

        return data_sets

    def get_data_set_values(self, domain: str, name: str) -> List[PointValue]:
        """
        Read all values from a data set.

        Args:
            domain: Domain name
            name: Data set name

        Returns:
            List of PointValue objects
        """
        self._ensure_connected()

        try:
            values = self._connection.read_data_set_values(domain, name)
            results = []
            for i, raw_val in enumerate(values):
                pv = self._parse_point_value(raw_val, domain, f"{name}[{i}]")
                results.append(pv)
            return results
        except Exception as e:
            logger.debug(f"Failed to read data set {domain}/{name}: {e}")
            return []

    # =========================================================================
    # Transfer Sets (Block 2)
    # =========================================================================

    # Common transfer set naming patterns
    _TRANSFER_SET_PATTERNS = [
        "DS_TransferSet",
        "Transfer_Set",
        "TransferSet",
        "TS_",
        "DSTS",
    ]

    def get_transfer_sets(self, domain: str) -> List[TransferSet]:
        """
        Get transfer sets for a domain.

        Transfer sets in TASE.2 are typically data sets with specific
        naming conventions. This method discovers them by examining
        data sets and their associated control variables.

        Args:
            domain: Domain name

        Returns:
            List of TransferSet objects
        """
        self._ensure_connected()

        transfer_sets = []

        try:
            # Get data sets for the domain
            data_sets = self._connection.get_data_set_names(domain)

            for ds_name in data_sets:
                # Check if this looks like a transfer set
                is_ts = False
                for pattern in self._TRANSFER_SET_PATTERNS:
                    if pattern.lower() in ds_name.lower():
                        is_ts = True
                        break

                if is_ts:
                    ts = TransferSet(
                        name=ds_name,
                        domain=domain,
                        data_set=ds_name,
                        interval=0,
                        rbe_enabled=False,
                    )

                    # Try to read transfer set status
                    try:
                        status_var = f"{ds_name}_Status"
                        pv = self.read_point(domain, status_var)
                        if pv.value is not None:
                            ts.rbe_enabled = bool(pv.value)
                    except Exception:
                        pass

                    transfer_sets.append(ts)

            # Also check for explicit transfer set variables
            try:
                variables = self._connection.get_domain_variables(domain)
                for var in variables:
                    for pattern in self._TRANSFER_SET_PATTERNS:
                        if pattern.lower() in var.lower() and "enable" not in var.lower():
                            # Check if not already added via data sets
                            if not any(ts.name == var for ts in transfer_sets):
                                ts = TransferSet(
                                    name=var,
                                    domain=domain,
                                )
                                transfer_sets.append(ts)
                            break
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Failed to get transfer sets for {domain}: {e}")

        return transfer_sets

    def get_transfer_set_details(self, domain: str, name: str) -> TransferSet:
        """
        Read full transfer set configuration.

        Attempts to read all DSTS (Data Set Transfer Set) parameters
        per IEC 60870-6 specification.

        Args:
            domain: Domain name
            name: Transfer set name

        Returns:
            TransferSet with populated configuration
        """
        self._ensure_connected()

        ts = TransferSet(name=name, domain=domain, data_set=name)

        # Configuration variable patterns per TASE.2 specification
        config_vars = [
            # Interval configuration
            (f"{name}_Interval", "interval"),
            (f"{name}$Interval", "interval"),
            (f"{name}_IntegrityCheck", "integrity_time"),
            (f"{name}$IntegrityCheck", "integrity_time"),
            # Buffer configuration
            (f"{name}_BufferTime", "buffer_time"),
            (f"{name}$BufferTime", "buffer_time"),
            # RBE configuration
            (f"{name}_RBE", "rbe_enabled"),
            (f"{name}$RBE", "rbe_enabled"),
            (f"{name}_AllChangesReported", "rbe_enabled"),
            # Start time
            (f"{name}_StartTime", "start_time"),
            (f"{name}$StartTime", "start_time"),
        ]

        for var_name, attr in config_vars:
            try:
                pv = self.read_point(domain, var_name)
                if pv.value is not None:
                    current = getattr(ts, attr, None)
                    # Only set if not already set
                    if current is None or current == 0 or current is False:
                        if attr == "rbe_enabled":
                            setattr(ts, attr, bool(pv.value))
                        elif attr in ("interval", "buffer_time", "integrity_time"):
                            setattr(ts, attr, int(pv.value))
                        else:
                            setattr(ts, attr, pv.value)
                        logger.debug(f"Read {var_name} = {pv.value}")
            except Exception:
                pass  # Variable may not exist

        # Try to read DSConditions
        try:
            for var_name in [f"{name}_DSConditions", f"{name}$DSConditions"]:
                try:
                    pv = self.read_point(domain, var_name)
                    if pv.value is not None:
                        # DSConditions is a bitmask
                        from .types import TransferSetConditions
                        ts.conditions = TransferSetConditions.from_raw(int(pv.value))
                        break
                except Exception:
                    pass
        except Exception:
            pass

        return ts

    def enable_transfer_set(self, domain: str, name: str) -> bool:
        """
        Enable a transfer set.

        Writes True to the transfer set enable control variable.

        Args:
            domain: Domain name
            name: Transfer set name

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Try common enable variable patterns
        enable_names = [
            f"{name}_Enable",
            f"{name}_Enabled",
            f"Enable_{name}",
            f"{name}$Enable",
        ]

        for enable_var in enable_names:
            try:
                self._connection.write_variable(domain, enable_var, True)
                logger.info(f"Enabled transfer set {domain}/{name}")
                return True
            except Exception:
                continue

        # Try writing directly to the transfer set
        try:
            self._connection.write_variable(domain, name, True)
            logger.info(f"Enabled transfer set {domain}/{name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to enable transfer set {domain}/{name}: {e}")

        return False

    def disable_transfer_set(self, domain: str, name: str) -> bool:
        """
        Disable a transfer set.

        Writes False to the transfer set enable control variable.

        Args:
            domain: Domain name
            name: Transfer set name

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Try common enable variable patterns
        enable_names = [
            f"{name}_Enable",
            f"{name}_Enabled",
            f"Enable_{name}",
            f"{name}$Enable",
        ]

        for enable_var in enable_names:
            try:
                self._connection.write_variable(domain, enable_var, False)
                logger.info(f"Disabled transfer set {domain}/{name}")
                return True
            except Exception:
                continue

        # Try writing directly to the transfer set
        try:
            self._connection.write_variable(domain, name, False)
            logger.info(f"Disabled transfer set {domain}/{name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to disable transfer set {domain}/{name}: {e}")

        return False

    # =========================================================================
    # Control Operations (Block 5)
    # =========================================================================

    def select_device(self, domain: str, device: str) -> bool:
        """
        Select a device for control (Select-Before-Operate).

        In TASE.2, SBO select is typically done by writing to a
        select variable associated with the control point.

        The select state expires after SBO_TIMEOUT seconds (default 30s).

        Args:
            domain: Domain name
            device: Device/control point name

        Returns:
            True if selection successful

        Raises:
            SelectError: If selection fails
        """
        self._ensure_connected()

        import time
        device_key = f"{domain}/{device}"

        # Try common SBO select variable patterns
        select_names = [
            f"{device}$SBO",
            f"{device}_Select",
            f"{device}$Oper$ctlVal",
            f"{device}$SBOw",
        ]

        for select_var in select_names:
            try:
                # Write select value (typically 1 or True)
                self._connection.write_variable(domain, select_var, 1)
                # Record select timestamp for timeout tracking
                self._sbo_select_times[device_key] = time.time()
                logger.info(f"Selected device {domain}/{device}")
                return True
            except Exception:
                continue

        # Try reading the device first to verify it exists, then assume select works
        try:
            self.read_point(domain, device)
            # Record select timestamp for implicit select
            self._sbo_select_times[device_key] = time.time()
            logger.info(f"Device {domain}/{device} accessible (implicit select)")
            return True
        except Exception as e:
            raise SelectError(f"{domain}/{device}", f"Failed to select device: {e}")

    def operate_device(self, domain: str, device: str, value: Any) -> bool:
        """
        Operate a device (execute control action).

        Note: If select_device was called, the select state must still be valid
        (not expired). The default timeout is SBO_TIMEOUT seconds (30s).

        Args:
            domain: Domain name
            device: Device/control point name
            value: Control value (0=OFF, 1=ON, or numeric)

        Returns:
            True if operation successful

        Raises:
            OperateError: If operation fails or select has timed out
        """
        self._ensure_connected()

        import time
        device_key = f"{domain}/{device}"

        # Check if SBO select has expired
        if device_key in self._sbo_select_times:
            select_time = self._sbo_select_times[device_key]
            elapsed = time.time() - select_time
            if elapsed > SBO_TIMEOUT:
                # Clear expired select
                del self._sbo_select_times[device_key]
                raise OperateError(
                    f"{domain}/{device}",
                    f"SBO select expired after {SBO_TIMEOUT}s (elapsed: {elapsed:.1f}s)"
                )

        try:
            result = self._connection.write_variable(domain, device, value)
            # Clear select after successful operate
            if device_key in self._sbo_select_times:
                del self._sbo_select_times[device_key]
            return result

        except Exception as e:
            raise OperateError(f"{domain}/{device}", str(e))

    def send_command(self, domain: str, device: str, command: int) -> bool:
        """
        Send a command to a device.

        Args:
            domain: Domain name
            device: Device name
            command: Command value (0=OFF, 1=ON)

        Returns:
            True if successful
        """
        return self.operate_device(domain, device, command)

    def send_setpoint_real(self, domain: str, device: str, value: float) -> bool:
        """
        Send a real setpoint value.

        Args:
            domain: Domain name
            device: Device name
            value: Setpoint value

        Returns:
            True if successful
        """
        return self.operate_device(domain, device, value)

    def send_setpoint_discrete(self, domain: str, device: str, value: int) -> bool:
        """
        Send a discrete setpoint value.

        Args:
            domain: Domain name
            device: Device name
            value: Setpoint value

        Returns:
            True if successful
        """
        return self.operate_device(domain, device, value)

    def set_tag(
        self,
        domain: str,
        device: str,
        tag_value: int,
        reason: str = "",
    ) -> bool:
        """
        Set a tag on a device.

        Tags in TASE.2 are used to block control operations:
        - 0: Open and close inhibit (fully blocked)
        - 1: Close only inhibit
        - 2: No tag (remove tag)

        Args:
            domain: Domain name
            device: Device name
            tag_value: Tag value (0=inhibit, 1=close-only, 2=none)
            reason: Reason for tagging

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Try common tag variable patterns
        tag_names = [
            f"{device}$Tag",
            f"{device}_Tag",
            f"{device}$TagValue",
            f"Tag_{device}",
        ]

        for tag_var in tag_names:
            try:
                self._connection.write_variable(domain, tag_var, tag_value)
                logger.info(f"Set tag on {domain}/{device} to {tag_value}")

                # Try to set reason if provided
                if reason:
                    reason_names = [
                        f"{device}$TagReason",
                        f"{device}_TagReason",
                    ]
                    for reason_var in reason_names:
                        try:
                            self._connection.write_variable(domain, reason_var, reason)
                            break
                        except Exception:
                            continue

                return True
            except Exception:
                continue

        logger.warning(f"Failed to set tag on {domain}/{device}")
        return False

    # =========================================================================
    # Bilateral Table
    # =========================================================================

    # Standard TASE.2 bilateral table variable names
    _BLT_ID_NAMES = [
        "Bilateral_Table_ID",
        "BilateralTableId",
        "BLT_ID",
        "BLTID",
    ]
    _BLT_COUNT_NAMES = [
        "Server_Bilateral_Table_Count",
        "ServerBilateralTableCount",
        "BLT_Count",
        "NumBilateralTables",
    ]

    def get_bilateral_table_id(self) -> Optional[str]:
        """
        Get the bilateral table ID from the server.

        Reads the VCC-scope Bilateral_Table_ID variable.

        Returns:
            Bilateral table ID string, or None if not available
        """
        self._ensure_connected()

        # Try to find and read bilateral table ID from VCC domain
        try:
            domains = self.get_domains()
            for domain in domains:
                if domain.is_vcc:
                    # Try common TASE.2 bilateral table variable names
                    for var_name in self._BLT_ID_NAMES:
                        if var_name in domain.variables:
                            try:
                                pv = self.read_point(domain.name, var_name)
                                if pv.value is not None:
                                    return str(pv.value)
                            except Exception:
                                continue
                        # Try case-insensitive match
                        for actual_var in domain.variables:
                            if actual_var.lower() == var_name.lower():
                                try:
                                    pv = self.read_point(domain.name, actual_var)
                                    if pv.value is not None:
                                        return str(pv.value)
                                except Exception:
                                    continue
        except Exception as e:
            logger.debug(f"Failed to get bilateral table ID: {e}")

        return None

    def get_server_bilateral_table_count(self) -> int:
        """
        Get the number of bilateral tables on the server.

        Reads the VCC-scope Server_Bilateral_Table_Count variable.

        Returns:
            Number of bilateral tables (0 if not available)
        """
        self._ensure_connected()

        # Try to find and read bilateral table count from VCC domain
        try:
            domains = self.get_domains()
            for domain in domains:
                if domain.is_vcc:
                    # Try common TASE.2 bilateral table count variable names
                    for var_name in self._BLT_COUNT_NAMES:
                        if var_name in domain.variables:
                            try:
                                pv = self.read_point(domain.name, var_name)
                                if pv.value is not None:
                                    return int(pv.value)
                            except Exception:
                                continue
                        # Try case-insensitive match
                        for actual_var in domain.variables:
                            if actual_var.lower() == var_name.lower():
                                try:
                                    pv = self.read_point(domain.name, actual_var)
                                    if pv.value is not None:
                                        return int(pv.value)
                                except Exception:
                                    continue
        except Exception as e:
            logger.debug(f"Failed to get bilateral table count: {e}")

        return 0

    # =========================================================================
    # Server Information
    # =========================================================================

    def get_server_info(self) -> ServerInfo:
        """
        Get server information.

        Returns:
            ServerInfo object with vendor, model, revision, etc.
        """
        self._ensure_connected()

        if self._server_info:
            return self._server_info

        vendor, model, revision = self._connection.get_server_identity()

        self._server_info = ServerInfo(
            vendor=vendor,
            model=model,
            revision=revision,
            bilateral_table_count=self.get_server_bilateral_table_count(),
            bilateral_table_id=self.get_bilateral_table_id(),
        )

        return self._server_info

    # =========================================================================
    # Discovery and Security Analysis (IEC104 Parity)
    # =========================================================================

    def enumerate_data_points(self, max_points: int = 100) -> List[PointValue]:
        """
        Enumerate all readable data points with their values.

        Similar to IEC104 data point enumeration, this reads values
        from all accessible domains.

        Args:
            max_points: Maximum number of points to enumerate per domain

        Returns:
            List of PointValue objects with values and quality
        """
        self._ensure_connected()

        data_points = []
        domains = self.get_domains()

        for domain in domains:
            points_read = 0
            for var_name in domain.variables:
                if points_read >= max_points:
                    break

                try:
                    pv = self.read_point(domain.name, var_name)
                    data_points.append(pv)
                    points_read += 1
                except Exception as e:
                    logger.debug(f"Failed to read {domain.name}/{var_name}: {e}")
                    # Add placeholder for unreadable points
                    data_points.append(PointValue(
                        value=None,
                        quality=QUALITY_INVALID,
                        name=var_name,
                        domain=domain.name,
                    ))
                    points_read += 1

        return data_points

    def test_control_access(self, domain: str, device: str) -> bool:
        """
        Test if a device is controllable.

        Attempts to verify if the device can be selected for control
        without actually performing any control action.

        Args:
            domain: Domain name
            device: Device name

        Returns:
            True if device appears controllable
        """
        self._ensure_connected()

        try:
            # Try to select the device
            return self.select_device(domain, device)
        except Exception:
            return False

    def test_rbe_capability(self, domain: str) -> bool:
        """
        Test Report-by-Exception (Block 2) capability.

        Checks if the domain supports transfer sets and RBE.

        Args:
            domain: Domain name

        Returns:
            True if RBE is supported
        """
        self._ensure_connected()

        try:
            transfer_sets = self.get_transfer_sets(domain)
            return len(transfer_sets) > 0
        except Exception:
            return False

    def analyze_security(self) -> Dict[str, Any]:
        """
        Analyze security configuration and return findings.

        Performs comprehensive security analysis similar to IEC104 scanner.

        Returns:
            Dictionary with security analysis results including:
            - authentication: Whether authentication is used
            - encryption: Whether encryption is used
            - access_control: Access control mechanisms detected
            - readable_points: Number of readable data points
            - writable_points: Number of potentially writable points
            - control_points: Number of controllable points
            - transfer_sets: Number of transfer sets found
            - concerns: List of security concerns
            - recommendations: List of recommendations
        """
        self._ensure_connected()

        analysis = {
            "authentication": False,
            "encryption": False,
            "access_control": False,
            "readable_points": 0,
            "writable_points": 0,
            "control_points": 0,
            "transfer_sets": 0,
            "conformance_blocks": [],
            "concerns": [],
            "recommendations": [],
        }

        try:
            # Get domains and analyze
            domains = self.get_domains()
            analysis["domain_count"] = len(domains)

            # Check bilateral tables for access control
            blt_id = self.get_bilateral_table_id()
            blt_count = self.get_server_bilateral_table_count()
            if blt_id or blt_count > 0:
                analysis["access_control"] = True
                analysis["bilateral_table_id"] = blt_id
                analysis["bilateral_table_count"] = blt_count

            # Enumerate data points
            all_points = []
            control_keywords = [
                "control", "command", "setpoint", "breaker",
                "switch", "valve", "output", "operate"
            ]

            for domain in domains:
                for var_name in domain.variables[:50]:  # Limit per domain
                    try:
                        pv = self.read_point(domain.name, var_name)
                        if pv.value is not None:
                            analysis["readable_points"] += 1
                            all_points.append((domain.name, var_name, pv))
                    except Exception:
                        pass

                    # Check for control points
                    var_lower = var_name.lower()
                    if any(kw in var_lower for kw in control_keywords):
                        analysis["control_points"] += 1

                # Check transfer sets (Block 2)
                try:
                    ts = self.get_transfer_sets(domain.name)
                    analysis["transfer_sets"] += len(ts)
                except Exception:
                    pass

            # Determine conformance blocks
            analysis["conformance_blocks"].append("Block 1 (Basic)")

            if analysis["transfer_sets"] > 0:
                analysis["conformance_blocks"].append("Block 2 (RBE)")

            if analysis["control_points"] > 0:
                analysis["conformance_blocks"].append("Block 5 (Control)")

            # Security concerns
            analysis["concerns"].append(
                "TASE.2 has no built-in authentication - relies on bilateral tables"
            )
            analysis["concerns"].append(
                "No encryption at application layer - data transmitted in plaintext"
            )

            if analysis["readable_points"] > 0:
                analysis["concerns"].append(
                    f"{analysis['readable_points']} data points accessible without authentication"
                )

            if analysis["control_points"] > 0:
                analysis["concerns"].append(
                    f"{analysis['control_points']} potential control points identified"
                )

            if not analysis["access_control"]:
                analysis["concerns"].append(
                    "No bilateral table detected - access control may be misconfigured"
                )

            # Recommendations
            analysis["recommendations"].append(
                "Implement network segmentation and firewall rules"
            )
            analysis["recommendations"].append(
                "Use TLS wrapper or VPN for transport security"
            )
            analysis["recommendations"].append(
                "Configure bilateral tables to restrict access"
            )

            if analysis["control_points"] > 0:
                analysis["recommendations"].append(
                    "Review control point access permissions"
                )

        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Security analysis failed: {e}")

        return analysis

    # =========================================================================
    # Context Manager
    # =========================================================================

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


# Alias for compatibility with libtase2 API
Client = TASE2Client

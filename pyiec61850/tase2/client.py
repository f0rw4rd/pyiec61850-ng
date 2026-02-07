#!/usr/bin/env python3
"""
TASE.2/ICCP Client

Main TASE2Client class for TASE.2 protocol operations including
discovery, data access, and control.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
import logging
import queue
import time as _time

from .connection import MmsConnectionWrapper, is_available
from .types import (
    DataFlags,
    Domain,
    Variable,
    PointValue,
    ControlPoint,
    DataSet,
    TransferSet,
    DSTransferSetConfig,
    TransferReport,
    SBOState,
    BilateralTable,
    ServerInfo,
    ServerAddress,
    InformationMessage,
    IMTransferSetConfig,
    InformationBuffer,
    TagState,
    ClientStatistics,
)
from .constants import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    QUALITY_GOOD,
    QUALITY_INVALID,
    BLOCK_1,
    BLOCK_2,
    BLOCK_4,
    BLOCK_5,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    SBO_TIMEOUT,
    MAX_DATA_SET_SIZE,
    DSTS_VAR_DATA_SET_NAME,
    DSTS_VAR_INTERVAL,
    DSTS_VAR_INTEGRITY_CHECK,
    DSTS_VAR_BUFFER_TIME,
    DSTS_VAR_DS_CONDITIONS,
    DSTS_VAR_RBE,
    DSTS_VAR_ALL_CHANGES_REPORTED,
    DSTS_VAR_STATUS,
    DSTS_VAR_START_TIME,
    DSTS_VAR_TLE,
    DSTS_VAR_CRITICAL,
    DSTS_VAR_BLOCK_DATA,
    TRANSFER_REPORT_ACK,
    TRANSFER_REPORT_NACK,
    SUPPORTED_FEATURES_BLOCK_1,
    SUPPORTED_FEATURES_BLOCK_2,
    SUPPORTED_FEATURES_BLOCK_4,
    SUPPORTED_FEATURES_BLOCK_5,
    CONFORMANCE_BLOCKS,
    _SUPPORTED_FEATURES_BIT_MAP,
    IMTS_VAR_STATUS,
    INFO_BUFF_VAR_NAME,
    INFO_BUFF_VAR_SIZE,
    INFO_BUFF_VAR_NEXT_ENTRY,
    INFO_BUFF_VAR_ENTRIES,
    INFO_MSG_VAR_INFO_REF,
    INFO_MSG_VAR_LOCAL_REF,
    INFO_MSG_VAR_MSG_ID,
    INFO_MSG_VAR_CONTENT,
    MAX_INFO_MESSAGE_SIZE,
    NEXT_DS_TRANSFER_SET,
    MAX_TRANSFER_SET_CHAIN,
    TAG_VAR_SUFFIX,
    TAG_REASON_VAR_SUFFIX,
    TASE2_EDITION_AUTO,
    TASE2_EDITION_1996,
    TASE2_EDITION_2000,
    MAX_FILE_DOWNLOAD_SIZE,
    DEFAULT_FAILOVER_RETRY_COUNT,
    DEFAULT_FAILOVER_DELAY,
    SERVER_PRIORITY_PRIMARY,
    SERVER_PRIORITY_BACKUP,
    DEFAULT_MAX_CONSECUTIVE_ERRORS,
    TRANSFER_SET_METADATA_MEMBERS,
    TRANSFER_SET_METADATA_OFFSET,
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
    InformationMessageError,
    IMTransferSetError,
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
    Validate TASE.2 data point name.

    Names must be 1-32 characters, alphanumeric plus '$' and '_',
    and must not begin with a digit.
    """
    from .constants import MAX_POINT_NAME_LENGTH

    if not name:
        return False
    if len(name) > MAX_POINT_NAME_LENGTH:
        return False
    if name[0].isdigit():
        return False
    return all(c.isalnum() or c in ('_', '$') for c in name)


class TASE2Client:
    """
    TASE.2/ICCP Protocol Client.

    Provides high-level API for TASE.2 operations including:
    - Domain (VCC/ICC) discovery
    - Variable enumeration and data access
    - Transfer set management (Block 2)
    - Information messages and buffers (Block 4)
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
        max_outstanding_calls: Optional[int] = None,
        max_consecutive_errors: int = DEFAULT_MAX_CONSECUTIVE_ERRORS,
    ):
        """
        Initialize TASE.2 client.

        Args:
            local_ap_title: Local Application Process title (e.g., "1.1.1.999")
            remote_ap_title: Remote Application Process title
            local_ae_qualifier: Local Application Entity qualifier
            remote_ae_qualifier: Remote Application Entity qualifier
            max_outstanding_calls: Max concurrent MMS requests (calling side).
                If set, configures IedConnection_setMaxOutstandingCalls
                after connection creation. Default None (use library default).
            max_consecutive_errors: Maximum consecutive read/write errors
                before declaring connection lost and triggering failover.
                Default 10.
        """
        self._connection = MmsConnectionWrapper(
            local_ap_title=local_ap_title,
            remote_ap_title=remote_ap_title,
            local_ae_qualifier=local_ae_qualifier,
            remote_ae_qualifier=remote_ae_qualifier,
        )
        self._local_ap_title = local_ap_title
        self._remote_ap_title = remote_ap_title
        self._local_ae_qualifier = local_ae_qualifier
        self._remote_ae_qualifier = remote_ae_qualifier

        # Max outstanding calls config (applied at connect time)
        self._max_outstanding_calls = max_outstanding_calls

        # Cached discovery data
        self._domains: Dict[str, Domain] = {}
        self._server_info: Optional[ServerInfo] = None

        # SBO (Select-Before-Operate) tracking
        self._sbo_select_times: Dict[str, float] = {}
        self._sbo_states: Dict[str, SBOState] = {}

        # Connection loss notification
        self._on_connection_lost: Optional[Callable] = None
        self._connection.register_state_callback(self._handle_state_change)

        # Report queue for InformationReports (Phase 3)
        self._report_queue: queue.Queue = queue.Queue()
        self._report_callback: Optional[Callable] = None

        # Block 4: Information Message state
        self._im_transfer_set_enabled: bool = False
        self._im_message_queue: queue.Queue = queue.Queue()
        self._im_message_callback: Optional[Callable] = None

        # Server capabilities (populated post-connect in Phase 4)
        self._server_capabilities: Dict[str, Any] = {}

        # Statistics / diagnostics
        self._statistics = ClientStatistics()

        # TASE.2 edition for timestamp interpretation
        self._tase2_edition: str = TASE2_EDITION_AUTO

        # Local identity (vendor, model, revision)
        self._local_identity: Optional[Tuple[str, str, str]] = None

        # Multi-server failover state
        self._server_list: List[ServerAddress] = []
        self._current_server_index: int = 0
        self._failover_enabled: bool = False
        self._failover_retry_count: int = DEFAULT_FAILOVER_RETRY_COUNT
        self._failover_delay: float = DEFAULT_FAILOVER_DELAY
        self._failover_in_progress: bool = False

        # Consecutive error tracking
        self._max_consecutive_errors: int = max_consecutive_errors
        self._consecutive_errors: int = 0

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
        host: Union[str, List[Tuple[str, int]]],
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
        failover: bool = False,
        retry_count: int = DEFAULT_FAILOVER_RETRY_COUNT,
        retry_delay: float = DEFAULT_FAILOVER_DELAY,
    ) -> bool:
        """
        Connect to TASE.2 server.

        Supports two calling conventions:

        1. Single server: ``client.connect("192.168.1.100", port=102)``
        2. Server list with failover::

            client.connect([
                ("192.168.1.100", 102),  # primary 1
                ("192.168.1.101", 102),  # primary 2
                ("10.0.0.100", 102),     # backup 1
            ], failover=True)

        When failover is enabled, each server is tried in order until one
        succeeds. On connection loss the next server in the list is tried
        automatically.

        Args:
            host: Server hostname/IP, or list of (host, port) tuples
            port: Server port (default 102, ignored when host is a list)
            timeout: Connection timeout in milliseconds
            failover: Enable automatic failover on connection loss
            retry_count: Number of retries per server (default 1)
            retry_delay: Delay in seconds between attempts (default 1.0)

        Returns:
            True if connected successfully

        Raises:
            ConnectionFailedError: If connection fails (all servers exhausted)
        """
        # Clear cached data
        self._domains.clear()
        self._server_info = None
        self._server_capabilities.clear()
        self._statistics = ClientStatistics()
        self._consecutive_errors = 0

        # Handle server list
        if isinstance(host, list):
            self._server_list = [
                ServerAddress(h, p) for h, p in host
            ]
            self._failover_enabled = failover
            self._failover_retry_count = retry_count
            self._failover_delay = retry_delay
            return self._connect_with_failover(timeout)

        # Single server mode
        if failover and self._server_list:
            # Server list was pre-built via add_server()
            self._failover_enabled = True
            self._failover_retry_count = retry_count
            self._failover_delay = retry_delay
            # Add this server to front if not already in list
            if not any(s.host == host and s.port == port for s in self._server_list):
                self._server_list.insert(0, ServerAddress(host, port))
            return self._connect_with_failover(timeout)

        # Simple single server connect
        result = self._connect_single(host, port, timeout)
        return result

    def _connect_single(self, host: str, port: int, timeout: int) -> bool:
        """Connect to a single server and perform post-connect setup."""
        result = self._connection.connect(host, port, timeout)

        if result:
            self._statistics.connect_time = datetime.now(tz=timezone.utc)

            # Apply max outstanding calls if configured
            if self._max_outstanding_calls is not None:
                try:
                    self._connection.set_max_outstanding_calls(
                        self._max_outstanding_calls, self._max_outstanding_calls
                    )
                except Exception as e:
                    logger.warning(f"Failed to set max outstanding calls: {e}")

            # Try to read server capabilities (non-fatal)
            try:
                self._read_bilateral_table_info()
            except Exception as e:
                logger.warning(f"Post-connect capability read failed: {e}")

        return result

    def _connect_with_failover(self, timeout: int) -> bool:
        """
        Try connecting to each server in the list with retries.

        Iterates through all servers starting from _current_server_index,
        trying each server retry_count times before moving to the next.

        Returns:
            True if connected to any server

        Raises:
            ConnectionFailedError: If all servers exhausted
        """
        if not self._server_list:
            raise ConnectionFailedError("(none)", 0, "No servers configured")

        last_error = None
        num_servers = len(self._server_list)

        for offset in range(num_servers):
            idx = (self._current_server_index + offset) % num_servers
            server = self._server_list[idx]

            for attempt in range(self._failover_retry_count + 1):
                try:
                    logger.info(
                        f"Connecting to {server.host}:{server.port} "
                        f"(server {idx + 1}/{num_servers}, "
                        f"attempt {attempt + 1}/{self._failover_retry_count + 1})"
                    )
                    result = self._connect_single(server.host, server.port, timeout)
                    if result:
                        self._current_server_index = idx
                        logger.info(
                            f"Connected to {server.host}:{server.port} "
                            f"({server.priority})"
                        )
                        return True
                except ConnectionFailedError as e:
                    last_error = e
                    logger.warning(
                        f"Connection to {server.host}:{server.port} failed: {e}"
                    )
                except Exception as e:
                    last_error = ConnectionFailedError(
                        server.host, server.port, str(e)
                    )
                    logger.warning(
                        f"Connection to {server.host}:{server.port} failed: {e}"
                    )

                # Delay between retries (not after last attempt)
                if attempt < self._failover_retry_count:
                    _time.sleep(self._failover_delay)

        # All servers exhausted
        if last_error:
            raise last_error
        raise ConnectionFailedError(
            self._server_list[0].host,
            self._server_list[0].port,
            "All servers exhausted",
        )

    def add_server(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        priority: str = SERVER_PRIORITY_PRIMARY,
    ) -> None:
        """
        Add a server address to the failover list.

        Servers are tried in the order they were added. Primary servers
        are tried first, then backup servers.

        Args:
            host: Server hostname or IP address
            port: Server port (default 102)
            priority: Server priority ("primary" or "backup")

        Example:
            >>> client.add_server("192.168.1.100", 102, priority="primary")
            >>> client.add_server("192.168.1.101", 102, priority="primary")
            >>> client.add_server("10.0.0.100", 102, priority="backup")
            >>> client.connect(client._server_list[0].host, failover=True)
        """
        addr = ServerAddress(host, port, priority)
        self._server_list.append(addr)
        # Sort: primaries first, then backups, preserving insertion order within
        self._server_list.sort(key=lambda s: 0 if s.is_primary else 1)
        logger.debug(f"Added server {addr} (total: {len(self._server_list)})")

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._statistics.disconnect_time = datetime.now(tz=timezone.utc)
        self._connection.disconnect()
        self._domains.clear()
        self._server_info = None
        self._sbo_select_times.clear()
        self._sbo_states.clear()
        self._server_capabilities.clear()
        self._im_transfer_set_enabled = False

    def _ensure_connected(self) -> None:
        """Ensure connection is active."""
        if not self.is_connected:
            raise NotConnectedError()

    @property
    def on_connection_lost(self) -> Optional[Callable]:
        """Get the connection lost callback."""
        return self._on_connection_lost

    @on_connection_lost.setter
    def on_connection_lost(self, callback: Optional[Callable]) -> None:
        """Set callback for connection loss notification.

        The callback receives no arguments.
        """
        self._on_connection_lost = callback

    def _handle_state_change(self, old_state: int, new_state: int) -> None:
        """Handle connection state changes from the underlying connection."""
        if old_state == STATE_CONNECTED and new_state == STATE_DISCONNECTED:
            self._handle_connection_lost()

    def _handle_connection_lost(self) -> None:
        """Handle connection loss: attempt failover, then cleanup and notify.

        If failover is enabled and servers are available, attempts to connect
        to the next server in the list before notifying the user callback.
        """
        logger.warning("Connection lost - clearing cached state")
        self._sbo_select_times.clear()
        self._sbo_states.clear()
        self._consecutive_errors = 0

        # Attempt failover if enabled and not already in progress
        if (self._failover_enabled and self._server_list
                and not self._failover_in_progress):
            self._failover_in_progress = True
            try:
                # Move to next server
                self._current_server_index = (
                    (self._current_server_index + 1) % len(self._server_list)
                )
                logger.info(
                    f"Attempting failover to next server "
                    f"(index {self._current_server_index})"
                )
                # Recreate connection wrapper (old one is dead)
                self._connection = MmsConnectionWrapper(
                    local_ap_title=self._local_ap_title,
                    remote_ap_title=self._remote_ap_title,
                    local_ae_qualifier=self._local_ae_qualifier,
                    remote_ae_qualifier=self._remote_ae_qualifier,
                )
                self._connection.register_state_callback(self._handle_state_change)

                # Try failover
                self._connect_with_failover(DEFAULT_TIMEOUT)
                logger.info("Failover successful")
                return  # Connected to new server, skip lost callback
            except Exception as e:
                logger.warning(f"Failover failed: {e}")
            finally:
                self._failover_in_progress = False

        if self._on_connection_lost:
            try:
                self._on_connection_lost()
            except Exception as e:
                logger.warning(f"Connection lost callback error: {e}")

    @property
    def consecutive_errors(self) -> int:
        """Return current consecutive error count for monitoring."""
        return self._consecutive_errors

    @property
    def max_consecutive_errors(self) -> int:
        """Return configured maximum consecutive errors threshold."""
        return self._max_consecutive_errors

    @property
    def server_list(self) -> List[ServerAddress]:
        """Return the configured server list for failover."""
        return list(self._server_list)

    def _record_success(self) -> None:
        """Record a successful operation, resetting consecutive error count."""
        self._consecutive_errors = 0

    def _record_error(self) -> None:
        """Record an operation error, incrementing consecutive count.

        When consecutive errors exceed max_consecutive_errors, declares
        the connection lost and triggers failover/callback.
        """
        self._consecutive_errors += 1
        self._statistics.total_errors += 1
        if self._consecutive_errors >= self._max_consecutive_errors:
            logger.warning(
                f"Consecutive error count ({self._consecutive_errors}) "
                f"reached threshold ({self._max_consecutive_errors}) "
                f"- declaring connection lost"
            )
            self._handle_connection_lost()

    def _read_bilateral_table_info(self) -> None:
        """Post-connect: read bilateral table and server capabilities."""
        try:
            domains = self.get_domains()
            for domain in domains:
                # Read Bilateral_Table_ID
                for var_name in ["Bilateral_Table_ID", "BilateralTableId"]:
                    try:
                        pv = self.read_point(domain.name, var_name)
                        if pv.value is not None:
                            self._server_capabilities["bilateral_table_id"] = str(pv.value)
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read {var_name} from {domain.name}: {e}")
                        continue

                # Read Supported_Features
                for var_name in ["Supported_Features", "SupportedFeatures"]:
                    try:
                        pv = self.read_point(domain.name, var_name)
                        if pv.value is not None:
                            self._parse_supported_features(int(pv.value))
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read {var_name} from {domain.name}: {e}")
                        continue

                # Read TASE.2_Version
                for var_name in ["TASE2_Version", "TASE_2_Version"]:
                    try:
                        pv = self.read_point(domain.name, var_name)
                        if pv.value is not None:
                            self._server_capabilities["tase2_version"] = str(pv.value)
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read {var_name} from {domain.name}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Failed to read bilateral table info: {e}")

    def _parse_supported_features(self, features_bitstring: int) -> None:
        """Parse Supported_Features bitstring into conformance block list.

        Decodes all 9 TASE.2 conformance block bits from the ASN.1 BITSTRING
        value returned by MmsValue_getBitStringAsInteger(). Blocks 1-5 are
        normative; blocks 6-9 are informative (legacy) since the 2014 edition.

        Args:
            features_bitstring: Integer representation of the Supported_Features
                bitstring (MSB-first, as returned by libiec61850).
        """
        blocks = []
        for bitmask, block_num in _SUPPORTED_FEATURES_BIT_MAP:
            if features_bitstring & bitmask:
                blocks.append(block_num)
        self._server_capabilities["supported_blocks"] = blocks

        # Store human-readable summary
        summary_parts = []
        for block_num in blocks:
            name = CONFORMANCE_BLOCKS.get(block_num, (str(block_num),))[0]
            summary_parts.append(f"Block {block_num} ({name})")
        self._server_capabilities["supported_blocks_summary"] = ", ".join(summary_parts) if summary_parts else "none"

    def get_server_blocks(self) -> Dict[int, Dict[str, Any]]:
        """Return conformance block support status for all 9 TASE.2 blocks.

        Returns a dict keyed by block number (1-9) with each value being a dict
        containing:
            - name: Short name of the block (e.g. "BASIC", "RBE")
            - supported: True if the server advertises support, False otherwise,
              or None if Supported_Features has not been read yet.
            - description: Human-readable description of the block.

        Returns:
            Dict mapping block number to block info dict.
        """
        supported_blocks = self._server_capabilities.get("supported_blocks")
        result = {}
        for block_num, (name, description) in CONFORMANCE_BLOCKS.items():
            if supported_blocks is None:
                supported = None
            else:
                supported = block_num in supported_blocks
            result[block_num] = {
                "name": name,
                "supported": supported,
                "description": description,
            }
        return result

    def _check_block_support(self, block: int, operation: str) -> None:
        """Warn if a conformance block is not supported by the server."""
        blocks = self._server_capabilities.get("supported_blocks")
        if blocks is not None and block not in blocks:
            block_name = CONFORMANCE_BLOCKS.get(block, (str(block),))[0]
            logger.warning(
                f"Server may not support Block {block} ({block_name}) "
                f"required for {operation}"
            )

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
                except Exception as e:
                    logger.warning(f"Failed to get variables for domain {name}: {e}")
                    variables = []

                # Get data sets for this domain
                try:
                    data_sets = self._connection.get_data_set_names(name)
                except Exception as e:
                    logger.warning(f"Failed to get data sets for domain {name}: {e}")
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

        Raises:
            TASE2Error: If operation fails
        """
        self._ensure_connected()

        try:
            return self._connection.get_domain_variables(domain)
        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to get variables for {domain}: {e}")

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

        if not _validate_point_name(name):
            logger.warning(
                f"Invalid TASE.2 point name '{name}' - names should be "
                "alphanumeric with underscores, max 32 chars"
            )

        raw_value = None
        try:
            raw_value = self._connection.read_variable(domain, name)
            self._statistics.total_reads += 1
            result = self._parse_point_value(raw_value, domain, name)
            self._record_success()
            return result

        except NotConnectedError:
            raise
        except TASE2Error as e:
            self._record_error()
            raise ReadError(f"{domain}/{name}", str(e))
        except Exception as e:
            self._record_error()
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

        if not _validate_point_name(name):
            logger.warning(
                f"Invalid TASE.2 point name '{name}' - names should be "
                "alphanumeric with underscores, max 32 chars"
            )

        try:
            result = self._connection.write_variable(domain, name, value)
            self._statistics.total_writes += 1
            self._record_success()
            return result

        except NotConnectedError:
            raise
        except TASE2Error as e:
            self._record_error()
            raise WriteError(f"{domain}/{name}", str(e))
        except Exception as e:
            self._record_error()
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
            raise ReadError(f"{domain}/{name}", f"Failed to parse point value: {e}")

    def _extract_value(self, raw_value: Any) -> Any:
        """Extract Python value from MMS value (handles structured types)."""
        try:
            import pyiec61850.pyiec61850 as iec61850

            # Check if this is a structured type (TASE.2 compound value)
            mms_type = iec61850.MmsValue_getType(raw_value)

            # Check for structure using cached type constant
            if mms_type == _MMS_TYPES['STRUCTURE']:
                # TASE.2 structured types vary by point type:
                # 1 element: value only (no quality)
                # 2 elements: value + quality
                # 3 elements: value + quality + timestamp
                # 4 elements: value + quality + timestamp + COV
                try:
                    element_count = iec61850.MmsValue_getArraySize(raw_value)
                    if element_count < 1:
                        logger.debug("Empty structured value")
                        return None
                    if element_count > 4:
                        logger.debug(f"Unexpected structured value size: {element_count}")
                    # First element is always the actual value
                    value_element = iec61850.MmsValue_getElement(raw_value, 0)
                    if value_element:
                        return self._extract_primitive(value_element)
                except Exception as e:
                    logger.warning(f"Failed to extract value from structure: {e}")

            # Not a structure, extract as primitive
            return self._extract_primitive(raw_value)

        except Exception as e:
            logger.warning(f"Failed to extract value, returning raw: {e}")
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
        """Extract quality flags from MMS structured value.

        Per TASE.2 point types:
        - 1 element structures have no quality (value only)
        - 2+ element structures have quality as 2nd element
        """
        try:
            import pyiec61850.pyiec61850 as iec61850

            mms_type = iec61850.MmsValue_getType(raw_value)

            # Only structures have quality fields
            if mms_type == _MMS_TYPES['STRUCTURE']:
                try:
                    element_count = iec61850.MmsValue_getArraySize(raw_value)
                    # 1-element structures have no quality
                    if element_count < 2:
                        return DataFlags()
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
                    logger.warning(f"Failed to extract quality flags: {e}")

        except Exception as e:
            logger.warning(f"Failed to extract quality: {e}")

        # Default: valid quality
        return DataFlags()

    def _extract_timestamp(self, raw_value: Any) -> Optional[datetime]:
        """Extract timestamp from MMS structured value.

        Supports edition-aware interpretation:
        - TASE.2 1996.08 edition: timestamps may be in seconds since epoch
        - TASE.2 2000.08 edition: timestamps in milliseconds since epoch
        - Auto mode: heuristic detection based on value magnitude
        """
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
                                return self._convert_timestamp(epoch_ms)
                except Exception as e:
                    logger.warning(f"Failed to extract timestamp: {e}")

        except Exception as e:
            logger.warning(f"Failed to extract timestamp: {e}")

        return None

    def _convert_timestamp(self, raw_ts: int) -> Optional[datetime]:
        """Convert a raw timestamp value to datetime, respecting edition setting.

        Args:
            raw_ts: Raw timestamp value (seconds or milliseconds since epoch)

        Returns:
            datetime in UTC, or None if conversion fails
        """
        try:
            edition = self._tase2_edition

            if edition == TASE2_EDITION_1996:
                # 1996 edition: value is in seconds
                return datetime.fromtimestamp(raw_ts, tz=timezone.utc)
            elif edition == TASE2_EDITION_2000:
                # 2000 edition: value is in milliseconds
                return datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
            else:
                # Auto-detect: if value > year 3000 in seconds, it's likely ms
                # Threshold: year 3000 ~ 32503680000 seconds
                if raw_ts > 32503680000:
                    return datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
                else:
                    # Could be seconds or small ms value
                    # Heuristic: if > year 2000 in seconds (946684800),
                    # treat as seconds; otherwise treat as ms
                    if raw_ts > 946684800:
                        return datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
                    else:
                        return datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        except (OSError, OverflowError, ValueError) as e:
            logger.debug(f"Timestamp conversion failed for {raw_ts}: {e}")
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
                    logger.warning(f"Failed to extract COV counter: {e}")

        except Exception as e:
            logger.warning(f"Failed to extract COV counter: {e}")

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
            logger.warning(f"Failed to cleanup MmsValue: {e}")

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
                logger.warning(f"Failed to get data sets for {dom}: {e}")

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
        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise ReadError(f"{domain}/{name}", str(e))

    def create_data_set(
        self,
        domain: str,
        name: str,
        members: List[str],
        include_transfer_metadata: bool = False,
    ) -> bool:
        """
        Create a new data set on the server.

        Args:
            domain: Domain name
            name: Data set name
            members: List of member variable names (or domain/name references)
            include_transfer_metadata: When True, prepends the standard
                TASE.2 transfer set metadata members as the first 3 entries:
                Transfer_Set_Name, Transfer_Set_Time_Stamp, and
                DSConditions_Detected. These are required by the standard
                for datasets used with DS Transfer Sets and will appear as
                access-denied in direct reads but are populated in reports.
                (INDEX_OFFSET = 3).

        Returns:
            True if created successfully

        Raises:
            TASE2Error: If creation fails
        """
        self._ensure_connected()

        if not members:
            raise TASE2Error("Data set must have at least one member")

        # Optionally prepend transfer set metadata members
        if include_transfer_metadata:
            full_members = list(TRANSFER_SET_METADATA_MEMBERS) + list(members)
            logger.debug(
                f"Prepending {TRANSFER_SET_METADATA_OFFSET} transfer set "
                f"metadata members to data set {domain}/{name}"
            )
        else:
            full_members = list(members)

        if len(full_members) > MAX_DATA_SET_SIZE:
            raise TASE2Error(
                f"Data set has {len(full_members)} members, exceeding "
                f"TASE.2 limit of {MAX_DATA_SET_SIZE}"
            )

        return self._connection.create_data_set(domain, name, full_members)

    def delete_data_set(self, domain: str, name: str) -> bool:
        """
        Delete a data set from the server.

        Args:
            domain: Domain name
            name: Data set name

        Returns:
            True if deleted successfully

        Raises:
            TASE2Error: If deletion fails
        """
        self._ensure_connected()
        return self._connection.delete_data_set(domain, name)

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

                    # Try to read transfer set status (optional attribute)
                    try:
                        status_var = f"{ds_name}_Status"
                        pv = self.read_point(domain, status_var)
                        if pv.value is not None:
                            ts.rbe_enabled = bool(pv.value)
                    except Exception as e:
                        logger.warning(f"Failed to read transfer set status for {ds_name}: {e}")

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
            except Exception as e:
                logger.warning(f"Failed to enumerate variables for transfer set discovery on {domain}: {e}")

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to get transfer sets for {domain}: {e}")

        return transfer_sets

    def get_transfer_set_details(self, domain: str, name: str) -> TransferSet:
        """
        Read full transfer set configuration.

        Attempts to read all DS Transfer Set parameters.

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
            except Exception as e:
                # Variable may not exist on this server - warn for visibility
                logger.warning(f"Failed to read transfer set attribute {var_name}: {e}")

        # Try to read DSConditions
        for var_name in [f"{name}_DSConditions", f"{name}$DSConditions"]:
            try:
                pv = self.read_point(domain, var_name)
                if pv.value is not None:
                    # DSConditions is a bitmask
                    from .types import TransferSetConditions
                    ts.conditions = TransferSetConditions.from_raw(int(pv.value))
                    break
            except Exception as e:
                logger.warning(f"Failed to read DSConditions variable {var_name}: {e}")

        return ts

    def configure_transfer_set(
        self,
        domain: str,
        name: str,
        config: DSTransferSetConfig,
    ) -> bool:
        """
        Configure a DS Transfer Set by writing standard attribute variables.

        Writes the standard DSTransferSet named variables.

        Args:
            domain: Domain name
            name: Transfer set name
            config: DSTransferSetConfig with desired settings

        Returns:
            True if at least one attribute was written successfully

        Raises:
            TASE2Error: If all writes fail
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_2, "configure_transfer_set")

        writes_succeeded = 0

        # Map config fields to standard TASE.2 variable names
        config_writes = []
        if config.data_set_name:
            config_writes.append((DSTS_VAR_DATA_SET_NAME, config.data_set_name))
        if config.interval is not None:
            config_writes.append((DSTS_VAR_INTERVAL, config.interval))
        if config.integrity_check is not None:
            config_writes.append((DSTS_VAR_INTEGRITY_CHECK, config.integrity_check))
        if config.buffer_time is not None:
            config_writes.append((DSTS_VAR_BUFFER_TIME, config.buffer_time))
        if config.rbe is not None:
            config_writes.append((DSTS_VAR_RBE, config.rbe))
        if config.all_changes_reported is not None:
            config_writes.append((DSTS_VAR_ALL_CHANGES_REPORTED, config.all_changes_reported))
        if config.critical is not None:
            config_writes.append((DSTS_VAR_CRITICAL, config.critical))
        if config.ds_conditions is not None:
            config_writes.append((DSTS_VAR_DS_CONDITIONS, config.ds_conditions.raw_value))
        if config.start_time is not None:
            config_writes.append((DSTS_VAR_START_TIME, config.start_time))
        if config.tle is not None:
            config_writes.append((DSTS_VAR_TLE, config.tle))
        if config.block_data is not None:
            config_writes.append((DSTS_VAR_BLOCK_DATA, config.block_data))

        for var_name, value in config_writes:
            try:
                self._connection.write_variable(domain, var_name, value)
                writes_succeeded += 1
                logger.debug(f"Wrote {domain}/{var_name} = {value}")
            except Exception as e:
                # Try with transfer set name prefix as fallback
                try:
                    prefixed_name = f"{name}_{var_name.split('_', 1)[-1]}"
                    self._connection.write_variable(domain, prefixed_name, value)
                    writes_succeeded += 1
                    logger.debug(f"Wrote {domain}/{prefixed_name} = {value}")
                except Exception:
                    logger.warning(f"Failed to write {var_name}: {e}")

        if writes_succeeded == 0 and config_writes:
            raise TASE2Error(
                f"Failed to configure transfer set {domain}/{name}: "
                "no attributes could be written"
            )

        logger.info(
            f"Configured transfer set {domain}/{name}: "
            f"{writes_succeeded}/{len(config_writes)} attributes written"
        )
        return True

    def send_transfer_report_ack(
        self,
        domain: str,
        transfer_set_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Send Transfer Report ACK to acknowledge a received report.

        Tries two approaches in order:

        1. **InformationReport method** (preferred): Sends an MMS
           InformationReport back to the server using
           ``MmsConnection_sendUnconfirmedPDU()`` with the transfer set
           name and timestamp.

        2. **Write-variable method** (fallback): Writes to the standard
           ``Transfer_Report_ACK`` variable. This is simpler but may
           not be supported by all server implementations.

        Args:
            domain: Domain name
            transfer_set_name: Transfer set name for InformationReport ACK
                (optional, used only for the InformationReport method)
            timestamp: Report timestamp for InformationReport ACK
                (optional, defaults to current UTC time)

        Returns:
            True if ACK sent successfully

        Raises:
            WriteError: If ACK write fails via both methods
        """
        self._ensure_connected()

        # Method 1: Try InformationReport ACK (sendUnconfirmedPDU)
        if transfer_set_name:
            try:
                import pyiec61850.pyiec61850 as iec61850

                if hasattr(iec61850, 'MmsConnection_sendUnconfirmedPDU'):
                    mms_conn = iec61850.IedConnection_getMmsConnection(
                        self._connection._connection
                    )
                    if mms_conn:
                        if timestamp is None:
                            timestamp = datetime.now(tz=timezone.utc)

                        # Construct the ACK MmsValue (timestamp)
                        ts_ms = int(timestamp.timestamp() * 1000)
                        ts_value = None
                        try:
                            if hasattr(iec61850, 'MmsValue_newUtcTimeByMsTime'):
                                ts_value = iec61850.MmsValue_newUtcTimeByMsTime(ts_ms)
                            elif hasattr(iec61850, 'MmsValue_newIntegerFromInt32'):
                                ts_value = iec61850.MmsValue_newIntegerFromInt32(ts_ms)

                            if ts_value:
                                iec61850.MmsConnection_sendUnconfirmedPDU(
                                    mms_conn, None, domain,
                                    transfer_set_name, ts_value
                                )
                                logger.debug(
                                    f"Sent Transfer Report ACK via "
                                    f"InformationReport to {domain}/{transfer_set_name}"
                                )
                                return True
                        finally:
                            if ts_value and hasattr(iec61850, 'MmsValue_delete'):
                                try:
                                    iec61850.MmsValue_delete(ts_value)
                                except Exception:
                                    pass
            except ImportError:
                pass
            except Exception as e:
                logger.debug(
                    f"InformationReport ACK failed, falling back to "
                    f"write-variable: {e}"
                )

        # Method 2: Fallback to write-variable approach
        try:
            self._connection.write_variable(domain, TRANSFER_REPORT_ACK, 1)
            logger.debug(f"Sent Transfer Report ACK to {domain}")
            return True
        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise WriteError(TRANSFER_REPORT_ACK, f"Failed to send ACK to {domain}: {e}")

    def start_receiving_reports(self) -> None:
        """Start receiving InformationReports (installs handler on MMS connection).

        Reports will be queued and can be retrieved via get_next_report().
        If the SWIG InformationReport handler is available, it will be installed
        on the underlying MMS connection. Otherwise, operates in queue-only mode
        where reports must be added manually (e.g. for testing).
        """
        self._ensure_connected()
        # Clear any stale reports
        while not self._report_queue.empty():
            try:
                self._report_queue.get_nowait()
            except queue.Empty:
                break

        # Try to install the native InformationReport handler
        installed = self._connection.install_information_report_handler(
            self._report_queue, self._report_callback
        )
        if installed:
            logger.info("Report receiving started (native handler mode)")
        else:
            logger.info("Report receiving started (queue-only mode)")

    def stop_receiving_reports(self) -> None:
        """Stop receiving InformationReports."""
        self._connection.uninstall_information_report_handler()
        logger.info("Report receiving stopped")

    def get_next_report(self, timeout: Optional[float] = None) -> Optional[TransferReport]:
        """
        Get the next report from the queue.

        Args:
            timeout: Maximum time to wait in seconds, None for non-blocking

        Returns:
            TransferReport if available, None if timeout/empty
        """
        try:
            report = self._report_queue.get(block=timeout is not None, timeout=timeout)
            if report is not None:
                self._statistics.reports_received += 1
            return report
        except queue.Empty:
            return None

    def set_report_callback(self, callback: Optional[Callable]) -> None:
        """
        Set callback for inline report notification.

        The callback receives a TransferReport as its argument.

        Args:
            callback: Callable that takes a TransferReport, or None to clear
        """
        self._report_callback = callback

    def enable_transfer_set(
        self,
        domain: str,
        name: str,
        initial_read: bool = False,
        data_set_name: Optional[str] = None,
    ) -> Union[bool, Tuple[bool, List[PointValue]]]:
        """
        Enable a transfer set.

        Tries standard DSTransferSet_Status first, then common patterns.

        Args:
            domain: Domain name
            name: Transfer set name
            initial_read: When True, performs a full dataset read immediately
                after enabling the transfer set so the client has current
                values before the first report arrives.
            data_set_name: Dataset name for initial read. If None, uses
                the transfer set name as the dataset name.

        Returns:
            True if successful (when initial_read=False), or
            (True, [PointValue, ...]) tuple (when initial_read=True)
        """
        self._ensure_connected()

        # Try standard variable names
        enable_names = [
            DSTS_VAR_STATUS,
            f"{name}_Enable",
            f"{name}_Enabled",
            f"Enable_{name}",
            f"{name}$Enable",
        ]

        last_error = None
        enabled = False
        for enable_var in enable_names:
            try:
                self._connection.write_variable(domain, enable_var, True)
                logger.info(f"Enabled transfer set {domain}/{name}")
                enabled = True
                break
            except Exception as e:
                last_error = e
                continue

        if not enabled:
            # Try writing directly to the transfer set
            try:
                self._connection.write_variable(domain, name, True)
                logger.info(f"Enabled transfer set {domain}/{name}")
                enabled = True
            except Exception as e:
                last_error = e

        if not enabled:
            raise WriteError(
                f"{domain}/{name}",
                f"Failed to enable transfer set: {last_error}"
            )

        # Perform initial dataset read if requested
        if initial_read:
            ds_name = data_set_name or name
            try:
                initial_values = self.get_data_set_values(domain, ds_name)
                logger.info(
                    f"Initial read of {domain}/{ds_name}: "
                    f"{len(initial_values)} values"
                )
                return (True, initial_values)
            except Exception as e:
                logger.warning(
                    f"Initial read of {domain}/{ds_name} failed: {e}"
                )
                return (True, [])

        return True

    def disable_transfer_set(self, domain: str, name: str) -> bool:
        """
        Disable a transfer set.

        Tries standard DSTransferSet_Status first, then common patterns.

        Args:
            domain: Domain name
            name: Transfer set name

        Returns:
            True if successful
        """
        self._ensure_connected()

        # Try standard variable names
        enable_names = [
            DSTS_VAR_STATUS,
            f"{name}_Enable",
            f"{name}_Enabled",
            f"Enable_{name}",
            f"{name}$Enable",
        ]

        last_error = None
        for enable_var in enable_names:
            try:
                self._connection.write_variable(domain, enable_var, False)
                logger.info(f"Disabled transfer set {domain}/{name}")
                return True
            except Exception as e:
                last_error = e
                continue

        # Try writing directly to the transfer set
        try:
            self._connection.write_variable(domain, name, False)
            logger.info(f"Disabled transfer set {domain}/{name}")
            return True
        except Exception as e:
            last_error = e

        raise WriteError(
            f"{domain}/{name}",
            f"Failed to disable transfer set: {last_error}"
        )

    # =========================================================================
    # Control Operations (Block 5)
    # =========================================================================

    def select_device(self, domain: str, device: str) -> bool:
        """
        Select a device for control (Select-Before-Operate).

        In TASE.2, SBO select is typically done by writing to a
        select variable associated with the control point.
        After writing, reads back the CheckBack ID if available.

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
        self._check_block_support(BLOCK_5, "select_device")

        import time
        device_key = f"{domain}/{device}"

        # SBO select variable patterns
        select_names = [
            f"{device}_SBO",
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

                # Try to read back CheckBack ID
                checkback_id = None
                try:
                    pv = self.read_point(domain, select_var)
                    if pv.value is not None:
                        checkback_id = pv.value
                except Exception as e:
                    logger.warning(f"Failed to read back CheckBack ID from {select_var}: {e}")

                self._sbo_states[device_key] = SBOState(
                    checkback_id=checkback_id,
                    select_time=time.time(),
                    domain=domain,
                    device=device,
                )

                logger.info(f"Selected device {domain}/{device}")
                return True
            except Exception as e:
                logger.debug(f"Select via {select_var} failed: {e}")
                continue

        # Try reading the device first to verify it exists, then assume select works
        try:
            self.read_point(domain, device)
            # Record select timestamp for implicit select
            self._sbo_select_times[device_key] = time.time()
            self._sbo_states[device_key] = SBOState(
                select_time=time.time(),
                domain=domain,
                device=device,
            )
            logger.info(f"Device {domain}/{device} accessible (implicit select)")
            return True
        except Exception as e:
            raise SelectError(f"{domain}/{device}", f"Failed to select device: {e}")

    def operate_device(self, domain: str, device: str, value: Any) -> bool:
        """
        Operate a device (execute control action).

        Note: If select_device was called, the select state must still be valid
        (not expired). The default timeout is SBO_TIMEOUT seconds (30s).
        If a CheckBack ID was captured during select, it is included.

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
                self._sbo_states.pop(device_key, None)
                raise OperateError(
                    f"{domain}/{device}",
                    f"SBO select expired after {SBO_TIMEOUT}s (elapsed: {elapsed:.1f}s)"
                )

        try:
            # If we have a CheckBack ID from select, write it first
            sbo_state = self._sbo_states.get(device_key)
            if sbo_state and sbo_state.checkback_id is not None:
                try:
                    self._connection.write_variable(
                        domain, f"{device}_CheckBackID", sbo_state.checkback_id
                    )
                except Exception:
                    logger.warning(f"CheckBack ID write failed for {device_key}")

            result = self._connection.write_variable(domain, device, value)
            self._statistics.control_operations += 1
            # Clear select after successful operate
            self._sbo_select_times.pop(device_key, None)
            self._sbo_states.pop(device_key, None)
            return result

        except Exception as e:
            self._statistics.total_errors += 1
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

        Tags block control operations:
        - 0: No tag (all operations allowed)
        - 1: Open and close inhibit (fully blocked)
        - 2: Close only inhibit
        - 3: Invalid

        Args:
            domain: Domain name
            device: Device name
            tag_value: Tag value (0=none, 1=open-and-close-inhibit, 2=close-only, 3=invalid)
            reason: Reason for tagging

        Returns:
            True if successful
        """
        self._ensure_connected()

        tag_names = [
            f"{device}_TAG",
            f"{device}$Tag",
            f"{device}_Tag",
            f"{device}$TagValue",
            f"Tag_{device}",
        ]

        last_error = None
        for tag_var in tag_names:
            try:
                self._connection.write_variable(domain, tag_var, tag_value)
                logger.info(f"Set tag on {domain}/{device} to {tag_value}")

                # Try to set reason if provided (best-effort, non-critical)
                if reason:
                    reason_names = [
                        f"{device}$TagReason",
                        f"{device}_TagReason",
                    ]
                    for reason_var in reason_names:
                        try:
                            self._connection.write_variable(domain, reason_var, reason)
                            break
                        except Exception as e:
                            logger.warning(f"Failed to write tag reason to {reason_var}: {e}")
                            continue

                return True
            except Exception as e:
                last_error = e
                continue

        from .exceptions import TagError
        raise TagError(f"{domain}/{device}", f"Failed to set tag: {last_error}")

    # =========================================================================
    # Information Messages (Block 4)
    # =========================================================================

    def enable_im_transfer_set(self, domain: Optional[str] = None) -> bool:
        """
        Enable the IM (Information Message) Transfer Set.

        The IM Transfer Set is association-scoped: when enabled, the server
        pushes information messages to this client per the bilateral table.
        This is analogous to enabling a DS Transfer Set for data, but
        operates at the association level rather than domain level.

        Args:
            domain: Optional domain name. If None, tries VCC scope first,
                    then each ICC domain.

        Returns:
            True if successfully enabled

        Raises:
            InformationMessageError: If enabling fails
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "enable_im_transfer_set")

        search_domains = self._get_im_search_domains(domain)

        for dom_name in search_domains:
            # Try standard IM Transfer Set variable names
            enable_names = [
                IMTS_VAR_STATUS,
                "IMTransferSet_Status",
                "IM_Transfer_Set_Enable",
            ]
            for var_name in enable_names:
                try:
                    self._connection.write_variable(dom_name, var_name, True)
                    self._im_transfer_set_enabled = True
                    logger.info(
                        f"Enabled IM Transfer Set on {dom_name}"
                    )
                    return True
                except Exception:
                    continue

        raise IMTransferSetError("Failed to enable IM Transfer Set")

    def disable_im_transfer_set(self, domain: Optional[str] = None) -> bool:
        """
        Disable the IM (Information Message) Transfer Set.

        Stops the server from pushing information messages to this client.

        Args:
            domain: Optional domain name. If None, tries VCC scope first,
                    then each ICC domain.

        Returns:
            True if successfully disabled

        Raises:
            InformationMessageError: If disabling fails
        """
        self._ensure_connected()

        search_domains = self._get_im_search_domains(domain)

        for dom_name in search_domains:
            enable_names = [
                IMTS_VAR_STATUS,
                "IMTransferSet_Status",
                "IM_Transfer_Set_Enable",
            ]
            for var_name in enable_names:
                try:
                    self._connection.write_variable(dom_name, var_name, False)
                    self._im_transfer_set_enabled = False
                    logger.info(
                        f"Disabled IM Transfer Set on {dom_name}"
                    )
                    return True
                except Exception:
                    continue

        raise IMTransferSetError("Failed to disable IM Transfer Set")

    def get_im_transfer_set_status(
        self, domain: Optional[str] = None
    ) -> IMTransferSetConfig:
        """
        Read the IM Transfer Set configuration/status.

        Args:
            domain: Optional domain name. If None, searches all domains.

        Returns:
            IMTransferSetConfig with current status
        """
        self._ensure_connected()

        search_domains = self._get_im_search_domains(domain)

        for dom_name in search_domains:
            status_names = [
                IMTS_VAR_STATUS,
                "IMTransferSet_Status",
                "IM_Transfer_Set_Enable",
            ]
            for var_name in status_names:
                try:
                    pv = self.read_point(dom_name, var_name)
                    if pv.value is not None:
                        return IMTransferSetConfig(
                            enabled=bool(pv.value),
                            name=var_name,
                        )
                except Exception:
                    continue

        # Return default if not readable
        return IMTransferSetConfig(enabled=self._im_transfer_set_enabled)

    def send_info_message(
        self,
        domain: str,
        info_ref: int,
        local_ref: int,
        msg_id: int,
        content: bytes,
    ) -> bool:
        """
        Send an information message to the server.

        In TASE.2, information messages are typically sent from server to
        client. However, a client may write message content to specific
        variables on the server to initiate a message transfer.

        Args:
            domain: Domain name
            info_ref: Information reference number
            local_ref: Local reference number
            msg_id: Message identifier
            content: Message content (text or binary)

        Returns:
            True if message was sent successfully

        Raises:
            InformationMessageError: If sending fails
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "send_info_message")

        if isinstance(content, str):
            content = content.encode("utf-8")

        if len(content) > MAX_INFO_MESSAGE_SIZE:
            raise InformationMessageError(
                f"Message size {len(content)} exceeds maximum {MAX_INFO_MESSAGE_SIZE}"
            )

        writes_succeeded = 0

        # Write message reference fields
        ref_writes = [
            (INFO_MSG_VAR_INFO_REF, info_ref),
            (INFO_MSG_VAR_LOCAL_REF, local_ref),
            (INFO_MSG_VAR_MSG_ID, msg_id),
        ]

        for var_name, value in ref_writes:
            try:
                self._connection.write_variable(domain, var_name, value)
                writes_succeeded += 1
            except Exception as e:
                logger.warning(f"Failed to write {var_name}: {e}")

        # Write content
        try:
            content_str = content.decode("utf-8") if isinstance(content, bytes) else content
            self._connection.write_variable(domain, INFO_MSG_VAR_CONTENT, content_str)
            writes_succeeded += 1
        except Exception as e:
            logger.warning(f"Failed to write message content: {e}")

        if writes_succeeded == 0:
            raise InformationMessageError(
                f"Failed to send information message to {domain}"
            )

        logger.info(
            f"Sent information message to {domain} "
            f"(info_ref={info_ref}, local_ref={local_ref}, msg_id={msg_id}, "
            f"size={len(content)})"
        )
        return True

    def get_info_messages(self, domain: str) -> List[InformationMessage]:
        """
        Read information messages from the server's information buffer.

        Queries the information buffer on the server to retrieve stored
        messages. This reads buffer metadata and attempts to extract
        individual messages.

        Args:
            domain: Domain name

        Returns:
            List of InformationMessage objects
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "get_info_messages")

        messages = []

        # First drain any queued IM messages from the handler
        while not self._im_message_queue.empty():
            try:
                msg = self._im_message_queue.get_nowait()
                messages.append(msg)
            except queue.Empty:
                break

        # Try to read information buffer entries from server
        try:
            entry_count = 0
            for var_name in [INFO_BUFF_VAR_ENTRIES, "Buffer_Entry_Count"]:
                try:
                    pv = self.read_point(domain, var_name)
                    if pv.value is not None:
                        entry_count = int(pv.value)
                        break
                except Exception as e:
                    logger.warning(f"Failed to read {var_name} from {domain}: {e}")
                    continue

            if entry_count > 0:
                logger.debug(
                    f"Information buffer on {domain} has {entry_count} entries"
                )

        except Exception as e:
            logger.warning(f"Failed to read information buffer metadata: {e}")

        return messages

    def get_info_message_by_ref(
        self, domain: str, info_ref: int
    ) -> Optional[InformationMessage]:
        """
        Read a specific information message by its info_ref.

        Attempts to retrieve a message from the server's information
        buffer matching the given information reference number.

        Args:
            domain: Domain name
            info_ref: Information reference number to look for

        Returns:
            InformationMessage if found, None otherwise
        """
        self._ensure_connected()

        # Check queued messages first
        messages = self.get_info_messages(domain)
        for msg in messages:
            if msg.info_ref == info_ref:
                return msg

        # Try direct read of message variables
        try:
            msg_data = {}
            for var_name, key in [
                (INFO_MSG_VAR_INFO_REF, "info_ref"),
                (INFO_MSG_VAR_LOCAL_REF, "local_ref"),
                (INFO_MSG_VAR_MSG_ID, "msg_id"),
                (INFO_MSG_VAR_CONTENT, "content"),
            ]:
                try:
                    pv = self.read_point(domain, var_name)
                    if pv.value is not None:
                        msg_data[key] = pv.value
                except Exception as e:
                    logger.warning(f"Failed to read info message field {var_name}: {e}")
                    continue

            if msg_data.get("info_ref") == info_ref:
                content = msg_data.get("content", "")
                if isinstance(content, str):
                    content = content.encode("utf-8")
                return InformationMessage(
                    info_ref=info_ref,
                    local_ref=int(msg_data.get("local_ref", 0)),
                    msg_id=int(msg_data.get("msg_id", 0)),
                    content=content,
                )
        except Exception as e:
            logger.warning(f"Failed to read info message by ref {info_ref}: {e}")

        return None

    def get_info_buffers(self, domain: str) -> List[InformationBuffer]:
        """
        Discover information buffers in a domain.

        Searches for information buffer objects in the specified domain
        by looking for standard buffer variable names.

        Args:
            domain: Domain name

        Returns:
            List of InformationBuffer objects
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "get_info_buffers")

        buffers = []

        try:
            variables = self._connection.get_domain_variables(domain)

            # Look for information buffer indicators
            buffer_names = set()
            for var in variables:
                var_lower = var.lower()
                if "information_buffer" in var_lower or "infobuffer" in var_lower:
                    # Extract base buffer name
                    buffer_names.add(var.split("_")[0] if "_" in var else var)

            for buf_name in buffer_names:
                buf = InformationBuffer(name=buf_name, domain=domain)

                # Try to read buffer size
                for size_var in [
                    f"{buf_name}_Size",
                    INFO_BUFF_VAR_SIZE,
                ]:
                    try:
                        pv = self.read_point(domain, size_var)
                        if pv.value is not None:
                            buf.max_size = int(pv.value)
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read buffer size from {size_var}: {e}")
                        continue

                # Try to read entry count
                for count_var in [
                    f"{buf_name}_Entry_Count",
                    INFO_BUFF_VAR_ENTRIES,
                ]:
                    try:
                        pv = self.read_point(domain, count_var)
                        if pv.value is not None:
                            buf.entry_count = int(pv.value)
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read buffer entry count from {count_var}: {e}")
                        continue

                buffers.append(buf)

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to discover info buffers in {domain}: {e}")

        return buffers

    def set_im_message_callback(self, callback: Optional[Callable]) -> None:
        """
        Set callback for received information messages.

        The callback receives an InformationMessage as its argument.

        Args:
            callback: Callable that takes an InformationMessage, or None to clear
        """
        self._im_message_callback = callback

    def get_next_info_message(
        self, timeout: Optional[float] = None
    ) -> Optional[InformationMessage]:
        """
        Get the next information message from the queue.

        Messages are queued when the IM Transfer Set is enabled and the
        server pushes information messages.

        Args:
            timeout: Maximum time to wait in seconds, None for non-blocking

        Returns:
            InformationMessage if available, None if timeout/empty
        """
        try:
            return self._im_message_queue.get(
                block=timeout is not None, timeout=timeout
            )
        except queue.Empty:
            return None

    def get_file_directory(self, directory_name: str = "") -> List[Dict[str, Any]]:
        """
        Get file directory listing from the server.

        Uses MMS file services to list files on the server, which in
        TASE.2 Block 4 context supports binary file transfer between
        control centers.

        Args:
            directory_name: Directory path (empty for root)

        Returns:
            List of dicts with file info (name, size, last_modified)
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "get_file_directory")

        return self._connection.get_file_directory(directory_name)

    def delete_file(self, file_name: str) -> bool:
        """
        Delete a file from the server.

        Args:
            file_name: Name of file to delete

        Returns:
            True if deleted successfully
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "delete_file")

        return self._connection.delete_file(file_name)

    def _get_im_search_domains(self, domain: Optional[str] = None) -> List[str]:
        """
        Build ordered domain search list for IM operations.

        The IM Transfer Set is association-scoped, so we try VCC first
        (global scope), then ICC domains.

        Args:
            domain: Specific domain, or None to search all

        Returns:
            Ordered list of domain names to try
        """
        if domain:
            return [domain]

        try:
            domains = self.get_domains()
            # VCC first (global scope), then ICC domains
            vcc = [d.name for d in domains if d.is_vcc]
            icc = [d.name for d in domains if not d.is_vcc]
            return vcc + icc
        except Exception as e:
            logger.warning(f"Failed to get domains for IM search: {e}")
            return []

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

    def get_bilateral_table_id(self, domain: Optional[str] = None) -> Optional[str]:
        """
        Get the bilateral table ID from the server.

        Bilateral_Table_ID is a domain-specific variable. Each ICC domain
        has its own bilateral table ID.

        Args:
            domain: Specific ICC domain to query. If None, searches
                    all ICC domains then falls back to VCC domains.

        Returns:
            Bilateral table ID string, or None if not available
        """
        self._ensure_connected()

        try:
            domains = self.get_domains()

            # Build ordered search list: specified domain first,
            # then ICC domains, then VCC domains as fallback
            search_domains = []
            if domain:
                search_domains = [d for d in domains if d.name == domain]
            else:
                # BLT_ID is domain-specific (ICC scope)
                icc_domains = [d for d in domains if not d.is_vcc]
                vcc_domains = [d for d in domains if d.is_vcc]
                search_domains = icc_domains + vcc_domains

            for dom in search_domains:
                # Try common TASE.2 bilateral table variable names
                for var_name in self._BLT_ID_NAMES:
                    if var_name in dom.variables:
                        try:
                            pv = self.read_point(dom.name, var_name)
                            if pv.value is not None:
                                return str(pv.value)
                        except Exception as e:
                            logger.warning(f"Failed to read {var_name} from {dom.name}: {e}")
                            continue
                    # Try case-insensitive match
                    for actual_var in dom.variables:
                        if actual_var.lower() == var_name.lower():
                            try:
                                pv = self.read_point(dom.name, actual_var)
                                if pv.value is not None:
                                    return str(pv.value)
                            except Exception as e:
                                logger.warning(f"Failed to read {actual_var} from {dom.name}: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Failed to get bilateral table ID: {e}")

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
                            except Exception as e:
                                logger.warning(f"Failed to read {var_name}: {e}")
                                continue
                        # Try case-insensitive match
                        for actual_var in domain.variables:
                            if actual_var.lower() == var_name.lower():
                                try:
                                    pv = self.read_point(domain.name, actual_var)
                                    if pv.value is not None:
                                        return int(pv.value)
                                except Exception as e:
                                    logger.warning(f"Failed to read {actual_var}: {e}")
                                    continue
        except Exception as e:
            logger.warning(f"Failed to get bilateral table count: {e}")

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
                    logger.warning(f"Failed to read {domain.name}/{var_name}: {e}")
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
                    except Exception as e:
                        logger.warning(f"Security analysis: failed to read {domain.name}/{var_name}: {e}")

                    # Check for control points
                    var_lower = var_name.lower()
                    if any(kw in var_lower for kw in control_keywords):
                        analysis["control_points"] += 1

                # Check transfer sets (Block 2)
                try:
                    ts = self.get_transfer_sets(domain.name)
                    analysis["transfer_sets"] += len(ts)
                except Exception as e:
                    logger.warning(f"Security analysis: failed to get transfer sets for {domain.name}: {e}")

            # Determine conformance blocks
            analysis["conformance_blocks"].append("Block 1 (Basic)")

            if analysis["transfer_sets"] > 0:
                analysis["conformance_blocks"].append("Block 2 (RBE)")

            # Check for Block 4 (Information Messages)
            has_block4 = False
            for domain in domains:
                for var_name in domain.variables:
                    var_lower = var_name.lower()
                    if ("im_transfer" in var_lower or
                            "information_buffer" in var_lower or
                            "infobuffer" in var_lower):
                        has_block4 = True
                        break
                if has_block4:
                    break
            if has_block4:
                analysis["conformance_blocks"].append("Block 4 (Info Messages)")

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
    # Get Tag (Block 5) - Read current tag state
    # =========================================================================

    def get_tag(self, domain: str, device: str) -> TagState:
        """
        Read the current tag state for a device.

        Reads the tag value variable ({device}_TAG) and optionally the
        tag reason string ({device}_TagReason) from the server.

        Args:
            domain: Domain name
            device: Device/control point name

        Returns:
            TagState with tag_value and reason

        Raises:
            ReadError: If tag variable cannot be read
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_5, "get_tag")

        tag_value = 0
        reason = ""

        # Read tag value - try standard patterns
        tag_names = [
            f"{device}{TAG_VAR_SUFFIX}",    # Standard: Device_TAG
            f"{device}$Tag",                 # MMS separator
            f"{device}_Tag",                 # Common variant
            f"{device}$TagValue",            # Alternate naming
            f"Tag_{device}",                 # Prefix variant
        ]

        tag_read = False
        for tag_var in tag_names:
            try:
                pv = self.read_point(domain, tag_var)
                if pv.value is not None:
                    tag_value = int(pv.value)
                    tag_read = True
                    break
            except Exception:
                continue

        if not tag_read:
            raise ReadError(
                f"{domain}/{device}{TAG_VAR_SUFFIX}",
                "Could not read tag variable"
            )

        # Try to read reason string (optional)
        reason_names = [
            f"{device}{TAG_REASON_VAR_SUFFIX}",
            f"{device}$TagReason",
            f"{device}_Tag_Reason",
        ]
        for reason_var in reason_names:
            try:
                pv = self.read_point(domain, reason_var)
                if pv.value is not None:
                    reason = str(pv.value)
                    break
            except Exception:
                continue

        return TagState(
            tag_value=tag_value,
            reason=reason,
            device=device,
            domain=domain,
        )

    # =========================================================================
    # Batch Point Reads
    # =========================================================================

    def read_points_batch(
        self,
        domain: str,
        names: List[str],
    ) -> List[PointValue]:
        """
        Read multiple points in a single MMS call using a temporary data set.

        Creates a temporary data set containing the requested variables,
        reads all values in one MMS ReadDataSetValues call, then deletes
        the temporary data set. This is significantly faster than sequential
        reads for large numbers of points.

        Falls back to sequential reads if data set operations fail.

        Args:
            domain: Domain name
            names: List of variable names to read

        Returns:
            List of PointValue objects (same order as names)
        """
        self._ensure_connected()

        if not names:
            return []

        if len(names) == 1:
            # Single point - no benefit from batch
            return [self.read_point(domain, names[0])]

        if len(names) > MAX_DATA_SET_SIZE:
            raise TASE2Error(
                f"Batch read has {len(names)} points, exceeding "
                f"TASE.2 limit of {MAX_DATA_SET_SIZE}"
            )

        # Generate unique temporary data set name
        import time
        temp_ds_name = f"_pyiec_batch_{int(time.time() * 1000) % 100000}"

        try:
            # Create temporary data set with all requested variables
            member_refs = [f"{domain}/{name}" for name in names]
            self._connection.create_data_set(domain, temp_ds_name, member_refs)

            try:
                # Read all values in one MMS call
                raw_values = self._connection.read_data_set_values(
                    domain, temp_ds_name
                )

                results = []
                for i, name in enumerate(names):
                    if i < len(raw_values) and raw_values[i] is not None:
                        pv = self._parse_point_value(
                            raw_values[i], domain, name
                        )
                        results.append(pv)
                    else:
                        results.append(PointValue(
                            value=None,
                            quality=QUALITY_INVALID,
                            name=name,
                            domain=domain,
                        ))

                self._statistics.total_reads += len(names)
                return results

            finally:
                # Always delete the temporary data set
                try:
                    self._connection.delete_data_set(domain, temp_ds_name)
                except Exception as e:
                    logger.warning(f"Failed to delete temp data set: {e}")

        except Exception as e:
            logger.warning(
                f"Batch read via data set failed ({e}), "
                f"falling back to sequential reads"
            )
            # Fall back to sequential reads
            return self.read_points([(domain, name) for name in names])

    # =========================================================================
    # Next_DSTransfer_Set Iteration (Standard discovery)
    # =========================================================================

    def get_transfer_sets_native(self, domain: str) -> List[TransferSet]:
        """
        Discover transfer sets using the Next_DSTransfer_Set linked-list variable.

        Each domain may have a Next_DSTransfer_Set variable pointing to the
        first transfer set, with each set chaining to the next.

        Falls back to the pattern-matching approach if the standard variable
        is not available.

        Args:
            domain: Domain name

        Returns:
            List of TransferSet objects
        """
        self._ensure_connected()

        transfer_sets = []
        visited = set()

        try:
            # Try to read the initial Next_DSTransfer_Set from the domain
            current_name = None
            try:
                pv = self.read_point(domain, NEXT_DS_TRANSFER_SET)
                if pv.value is not None and str(pv.value).strip():
                    current_name = str(pv.value).strip()
            except Exception as e:
                logger.warning(f"Failed to read {NEXT_DS_TRANSFER_SET} from {domain}: {e}")

            if current_name is None:
                # Standard variable not available, fall back to pattern matching
                logger.debug(
                    f"Next_DSTransfer_Set not available on {domain}, "
                    f"falling back to pattern matching"
                )
                return self.get_transfer_sets(domain)

            # Follow the chain
            iteration = 0
            while current_name and iteration < MAX_TRANSFER_SET_CHAIN:
                if current_name in visited:
                    logger.warning(
                        f"Circular reference detected in transfer set chain "
                        f"at {domain}/{current_name}"
                    )
                    break

                visited.add(current_name)

                ts = TransferSet(
                    name=current_name,
                    domain=domain,
                    data_set=current_name,
                )

                # Try to read transfer set status (optional)
                try:
                    status_var = f"{current_name}_Status"
                    status_pv = self.read_point(domain, status_var)
                    if status_pv.value is not None:
                        ts.rbe_enabled = bool(status_pv.value)
                except Exception as e:
                    logger.warning(f"Failed to read transfer set status {status_var}: {e}")

                transfer_sets.append(ts)

                # Read Next_DSTransfer_Set for this transfer set to get next
                next_name = None
                try:
                    next_pv = self.read_point(
                        domain, f"{current_name}_{NEXT_DS_TRANSFER_SET}"
                    )
                    if next_pv.value is not None and str(next_pv.value).strip():
                        next_name = str(next_pv.value).strip()
                except Exception:
                    # Try without prefix
                    try:
                        next_pv = self.read_point(domain, NEXT_DS_TRANSFER_SET)
                        if (next_pv.value is not None and
                                str(next_pv.value).strip() and
                                str(next_pv.value).strip() != current_name):
                            next_name = str(next_pv.value).strip()
                    except Exception:
                        pass

                current_name = next_name
                iteration += 1

            if transfer_sets:
                logger.info(
                    f"Found {len(transfer_sets)} transfer sets on {domain} "
                    f"via Next_DSTransfer_Set chain"
                )

        except Exception as e:
            logger.warning(
                f"Native transfer set discovery failed for {domain}: {e}, "
                f"falling back to pattern matching"
            )
            return self.get_transfer_sets(domain)

        return transfer_sets

    # =========================================================================
    # MMS File Download (Block 4)
    # =========================================================================

    def download_file(self, filename: str, local_path: Optional[str] = None) -> bytes:
        """
        Download a file from the server using MMS file services.

        Uses the underlying MMS file open/read/close sequence.

        Args:
            filename: Name of the file on the server
            local_path: Optional local file path to save to. If provided,
                       the file is written to disk and also returned as bytes.

        Returns:
            File contents as bytes

        Raises:
            TASE2Error: If download fails
        """
        self._ensure_connected()
        self._check_block_support(BLOCK_4, "download_file")

        try:
            data = self._connection.download_file(
                filename, max_size=MAX_FILE_DOWNLOAD_SIZE
            )

            if local_path:
                with open(local_path, 'wb') as f:
                    f.write(data)
                logger.info(
                    f"Downloaded file '{filename}' ({len(data)} bytes) "
                    f"to {local_path}"
                )
            else:
                logger.info(f"Downloaded file '{filename}' ({len(data)} bytes)")

            return data

        except NotConnectedError:
            raise
        except TASE2Error:
            raise
        except Exception as e:
            raise TASE2Error(f"Failed to download file '{filename}': {e}")

    # =========================================================================
    # Statistics / Diagnostics
    # =========================================================================

    def get_statistics(self) -> ClientStatistics:
        """
        Get client statistics and diagnostics.

        Returns a snapshot of operational counters including:
        - Total reads/writes performed
        - Total errors encountered
        - Connection uptime
        - Reports received count
        - Control operations count

        Returns:
            ClientStatistics dataclass with current counters
        """
        return ClientStatistics(
            total_reads=self._statistics.total_reads,
            total_writes=self._statistics.total_writes,
            total_errors=self._statistics.total_errors,
            reports_received=self._statistics.reports_received,
            control_operations=self._statistics.control_operations,
            connect_time=self._statistics.connect_time,
            disconnect_time=self._statistics.disconnect_time,
        )

    # =========================================================================
    # Local Identity (setIdentity)
    # =========================================================================

    def set_local_identity(
        self,
        vendor: str,
        model: str,
        revision: str,
    ) -> None:
        """
        Set the local identity to advertise during association.

        Stores the identity information locally. If the underlying
        libiec61850 binding supports IedConnection_setLocalIdentity
        or similar, it will be applied at connection time.

        Args:
            vendor: Vendor name string
            model: Model name string
            revision: Revision/version string
        """
        self._local_identity = (vendor, model, revision)
        logger.debug(
            f"Local identity set: vendor={vendor}, "
            f"model={model}, revision={revision}"
        )

    def get_local_identity(self) -> Optional[Tuple[str, str, str]]:
        """
        Get the configured local identity.

        Returns:
            Tuple of (vendor, model, revision) or None if not set
        """
        return self._local_identity

    # =========================================================================
    # Edition-Aware Timestamps
    # =========================================================================

    @property
    def tase2_edition(self) -> str:
        """
        Get the TASE.2 edition used for timestamp interpretation.

        Returns:
            Edition string: "1996.08", "2000.08", or "auto"
        """
        return self._tase2_edition

    @tase2_edition.setter
    def tase2_edition(self, edition: str) -> None:
        """
        Set the TASE.2 edition for timestamp interpretation.

        The 1996 edition uses seconds-since-epoch, while the 2000 edition
        uses milliseconds-since-epoch for timestamps. The "auto" setting
        attempts to detect the format heuristically.

        Args:
            edition: One of "1996.08", "2000.08", or "auto"

        Raises:
            ValueError: If edition is not recognized
        """
        valid = {TASE2_EDITION_AUTO, TASE2_EDITION_1996, TASE2_EDITION_2000}
        if edition not in valid:
            raise ValueError(
                f"Invalid TASE.2 edition '{edition}'. "
                f"Must be one of: {', '.join(sorted(valid))}"
            )
        self._tase2_edition = edition
        logger.debug(f"TASE.2 edition set to: {edition}")

    # =========================================================================
    # Max Outstanding Calls Configuration
    # =========================================================================

    @property
    def max_outstanding_calls(self) -> Optional[int]:
        """Get the configured max outstanding MMS calls."""
        return self._max_outstanding_calls

    @max_outstanding_calls.setter
    def max_outstanding_calls(self, value: Optional[int]) -> None:
        """
        Set max outstanding MMS calls.

        If the client is already connected, applies immediately.
        Otherwise, stores for application at next connect().

        Args:
            value: Max number of concurrent MMS requests, or None for default
        """
        self._max_outstanding_calls = value
        if value is not None and self.is_connected:
            try:
                self._connection.set_max_outstanding_calls(value, value)
            except Exception as e:
                logger.warning(f"Failed to apply max outstanding calls: {e}")

    def set_request_timeout(self, timeout_ms: int) -> None:
        """
        Set the MMS request timeout for individual operations.

        Args:
            timeout_ms: Timeout in milliseconds for each MMS request
        """
        if self.is_connected:
            self._connection.set_request_timeout(timeout_ms)
        else:
            logger.warning("Cannot set request timeout: not connected")

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

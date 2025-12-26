#!/usr/bin/env python3
"""
TASE.2/ICCP Protocol Support for pyiec61850-ng (IEC 60870-6)

This module provides Python bindings for TASE.2 (Telecontrol Application
Service Element 2), also known as ICCP (Inter-Control Center Communications
Protocol). TASE.2 is used for real-time data exchange between control
centers in the electric utility industry.

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
    ...     print(f"Domain: {domain.name} (VCC: {domain.is_vcc})")
    >>>
    >>> # Read a data point
    >>> value = client.read_point("ICC1", "Voltage")
    >>> print(f"Voltage: {value.value} (Quality: {value.quality})")
    >>>
    >>> client.disconnect()

Features:
    - Domain (VCC/ICC) discovery
    - Variable enumeration
    - Data point reading with quality
    - Data point writing
    - Transfer set management (Block 2)
    - Device control operations (Block 5)
    - Bilateral table queries
"""

__version__ = "0.1.0"
__author__ = "f0rw4rd"
__license__ = "GPL-3.0"

# Main client class
from .client import TASE2Client, Client

# Connection utilities
from .connection import MmsConnectionWrapper, is_available

# Data types
from .types import (
    DataFlags,
    TransferSetConditions,
    ProtectionEvent,
    Domain,
    Variable,
    PointValue,
    ControlPoint,
    DataSet,
    TransferSet,
    BilateralTable,
    ServerInfo,
    Association,
)

# Constants
from .constants import (
    # Defaults
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    # Point types (IEC 60870-6 compliant)
    POINT_TYPE_STATE,
    POINT_TYPE_STATE_SUPPLEMENTAL,
    POINT_TYPE_DISCRETE,
    POINT_TYPE_REAL,
    POINT_TYPE_STATE_Q,
    POINT_TYPE_STATE_SUPPLEMENTAL_Q,
    POINT_TYPE_DISCRETE_Q,
    POINT_TYPE_REAL_Q,
    POINT_TYPE_STATE_Q_TIMETAG,
    POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG,
    POINT_TYPE_DISCRETE_Q_TIMETAG,
    POINT_TYPE_REAL_Q_TIMETAG,
    POINT_TYPE_STATE_EXTENDED,
    POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED,
    POINT_TYPE_DISCRETE_EXTENDED,
    POINT_TYPE_REAL_EXTENDED,
    POINT_TYPE_SINGLE_PROTECTION_EVENT,
    POINT_TYPE_PACKED_PROTECTION_EVENT,
    # Legacy aliases
    POINT_TYPE_REAL_Q_TIME,
    POINT_TYPE_STATE_Q_TIME,
    POINT_TYPE_DISCRETE_Q_TIME,
    POINT_TYPES,
    # State values
    STATE_BETWEEN,
    STATE_ON,
    STATE_OFF,
    STATE_INVALID,
    STATE_CLOSED,
    STATE_TRIPPED,
    STATE_OPEN,
    # Control types
    CONTROL_TYPE_COMMAND,
    CONTROL_TYPE_SETPOINT_REAL,
    CONTROL_TYPE_SETPOINT_DISCRETE,
    CONTROL_TYPES,
    # Conformance blocks
    BLOCK_1,
    BLOCK_2,
    BLOCK_3,
    BLOCK_4,
    BLOCK_5,
    CONFORMANCE_BLOCKS,
    # Quality flags (bitmask)
    QUALITY_VALIDITY_VALID,
    QUALITY_VALIDITY_SUSPECT,
    QUALITY_VALIDITY_HELD,
    QUALITY_VALIDITY_NOT_VALID,
    QUALITY_SOURCE_TELEMETERED,
    QUALITY_SOURCE_ENTERED,
    QUALITY_SOURCE_CALCULATED,
    QUALITY_SOURCE_ESTIMATED,
    QUALITY_NORMAL_VALUE,
    QUALITY_TIMESTAMP_QUALITY,
    # Legacy quality flags
    QUALITY_GOOD,
    QUALITY_INVALID,
    QUALITY_HELD,
    QUALITY_SUSPECT,
    # DS Conditions
    DS_CONDITIONS_INTERVAL,
    DS_CONDITIONS_CHANGE,
    DS_CONDITIONS_OPERATOR_REQUEST,
    DS_CONDITIONS_EXTERNAL_EVENT,
    DS_CONDITIONS_ALL,
    # Protection event flags
    PROTECTION_EVENT_GENERAL,
    PROTECTION_EVENT_PHASE_A,
    PROTECTION_EVENT_PHASE_B,
    PROTECTION_EVENT_PHASE_C,
    PROTECTION_EVENT_EARTH,
    PROTECTION_EVENT_REVERSE,
    # Report flags
    REPORT_BUFFERED,
    REPORT_INTERVAL_TIMEOUT,
    REPORT_OBJECT_CHANGES,
    REPORT_INTEGRITY_TIMEOUT,
    # Command values
    CMD_OFF,
    CMD_ON,
    # Tag values
    TAG_OPEN_AND_CLOSE_INHIBIT,
    TAG_CLOSE_ONLY_INHIBIT,
    TAG_NONE,
    # Client states
    STATE_DISCONNECTED,
    STATE_CONNECTING,
    STATE_CONNECTED,
    STATE_CLOSING,
    CLIENT_STATES,
    # Domain types
    DOMAIN_VCC,
    DOMAIN_ICC,
    # Protocol limits
    MAX_DATA_SET_SIZE,
    SBO_TIMEOUT,
    MAX_POINT_NAME_LENGTH,
)

# Exceptions
from .exceptions import (
    # Base
    TASE2Error,
    # Library
    LibraryError,
    LibraryNotFoundError,
    # Connection (TASE2ConnectionError is the proper name, ConnectionError is deprecated alias)
    TASE2ConnectionError,
    ConnectionError,  # Deprecated: use TASE2ConnectionError
    ConnectionFailedError,
    ConnectionTimeoutError,
    ConnectionClosedError,
    NotConnectedError,
    AssociationError,
    # Authentication
    AuthenticationError,
    AccessDeniedError,
    BilateralTableError,
    # Operations (TASE2TimeoutError is the proper name, TimeoutError is deprecated alias)
    OperationError,
    TASE2TimeoutError,
    TimeoutError,  # Deprecated: use TASE2TimeoutError
    InvalidParameterError,
    ResourceNotFoundError,
    DomainNotFoundError,
    VariableNotFoundError,
    DataSetNotFoundError,
    TransferSetNotFoundError,
    # Data access
    DataAccessError,
    ReadError,
    WriteError,
    TypeMismatchError,
    # Control
    ControlError,
    ControlNotSupportedError,
    SelectError,
    OperateError,
    TagError,
    DeviceBlockedError,
    # Transfer sets
    TransferSetError,
    RBENotSupportedError,
    TransferSetConfigError,
    # Protocol
    ProtocolError,
    ServiceError,
    RejectError,
    AbortError,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__license__",
    # Main classes
    "TASE2Client",
    "Client",
    "MmsConnectionWrapper",
    "is_available",
    # Data types
    "DataFlags",
    "TransferSetConditions",
    "ProtectionEvent",
    "Domain",
    "Variable",
    "PointValue",
    "ControlPoint",
    "DataSet",
    "TransferSet",
    "BilateralTable",
    "ServerInfo",
    "Association",
    # Constants
    "DEFAULT_PORT",
    "DEFAULT_TIMEOUT",
    "POINT_TYPES",
    "CONTROL_TYPES",
    "CONFORMANCE_BLOCKS",
    # State values
    "STATE_BETWEEN",
    "STATE_ON",
    "STATE_OFF",
    "STATE_INVALID",
    "STATE_CLOSED",
    "STATE_TRIPPED",
    "STATE_OPEN",
    # Quality bitmask
    "QUALITY_VALIDITY_VALID",
    "QUALITY_VALIDITY_SUSPECT",
    "QUALITY_VALIDITY_HELD",
    "QUALITY_VALIDITY_NOT_VALID",
    "QUALITY_SOURCE_TELEMETERED",
    "QUALITY_SOURCE_ENTERED",
    "QUALITY_SOURCE_CALCULATED",
    "QUALITY_SOURCE_ESTIMATED",
    # Legacy quality
    "QUALITY_GOOD",
    "QUALITY_INVALID",
    "QUALITY_HELD",
    "QUALITY_SUSPECT",
    # DS Conditions
    "DS_CONDITIONS_INTERVAL",
    "DS_CONDITIONS_CHANGE",
    "DS_CONDITIONS_OPERATOR_REQUEST",
    "DS_CONDITIONS_EXTERNAL_EVENT",
    "DS_CONDITIONS_ALL",
    # Commands
    "CMD_OFF",
    "CMD_ON",
    # Blocks
    "BLOCK_1",
    "BLOCK_2",
    "BLOCK_3",
    "BLOCK_4",
    "BLOCK_5",
    # Client states
    "STATE_DISCONNECTED",
    "STATE_CONNECTING",
    "STATE_CONNECTED",
    "STATE_CLOSING",
    # Domain types
    "DOMAIN_VCC",
    "DOMAIN_ICC",
    # Protocol limits
    "MAX_DATA_SET_SIZE",
    "SBO_TIMEOUT",
    "MAX_POINT_NAME_LENGTH",
    # Exceptions
    "TASE2Error",
    "LibraryError",
    "LibraryNotFoundError",
    "TASE2ConnectionError",
    "ConnectionError",  # Deprecated alias for TASE2ConnectionError
    "ConnectionFailedError",
    "ConnectionTimeoutError",
    "ConnectionClosedError",
    "NotConnectedError",
    "AssociationError",
    "AuthenticationError",
    "AccessDeniedError",
    "BilateralTableError",
    "OperationError",
    "TASE2TimeoutError",
    "TimeoutError",  # Deprecated alias for TASE2TimeoutError
    "InvalidParameterError",
    "ResourceNotFoundError",
    "DomainNotFoundError",
    "VariableNotFoundError",
    "DataSetNotFoundError",
    "TransferSetNotFoundError",
    "DataAccessError",
    "ReadError",
    "WriteError",
    "TypeMismatchError",
    "ControlError",
    "ControlNotSupportedError",
    "SelectError",
    "OperateError",
    "TagError",
    "DeviceBlockedError",
    "TransferSetError",
    "RBENotSupportedError",
    "TransferSetConfigError",
    "ProtocolError",
    "ServiceError",
    "RejectError",
    "AbortError",
]

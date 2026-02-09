#!/usr/bin/env python3
"""
TASE.2/ICCP Protocol Support for pyiec61850-ng

Python bindings for TASE.2 (ICCP), used for real-time data exchange
between control centers in the electric utility industry.

Example:
    >>> from pyiec61850.tase2 import TASE2Client
    >>> client = TASE2Client(
    ...     local_ap_title="1.1.1.999",
    ...     remote_ap_title="1.1.1.998"
    ... )
    >>> client.connect("192.168.1.100", port=102)
    >>> domains = client.get_domains()
    >>> value = client.read_point("ICC1", "Voltage")
    >>> client.disconnect()
"""

__version__ = "0.4.0"
__author__ = "f0rw4rd"
__license__ = "GPL-3.0"

# Main client class
from .client import Client, TASE2Client

# Connection utilities
from .connection import MmsConnectionWrapper, is_available

# Constants
from .constants import (
    # Standard TASE.2 named variables
    BILATERAL_TABLE_ID_VAR,
    # Conformance blocks
    BLOCK_1,
    BLOCK_2,
    BLOCK_3,
    BLOCK_4,
    BLOCK_5,
    BLOCK_6,
    BLOCK_7,
    BLOCK_8,
    BLOCK_9,
    CLIENT_STATES,
    # Command values
    CMD_OFF,
    CMD_ON,
    CONFORMANCE_BLOCKS,
    # Control types
    CONTROL_TYPE_COMMAND,
    CONTROL_TYPE_SETPOINT_DISCRETE,
    CONTROL_TYPE_SETPOINT_REAL,
    CONTROL_TYPES,
    DEFAULT_FAILOVER_DELAY,
    # Failover configuration
    DEFAULT_FAILOVER_RETRY_COUNT,
    DEFAULT_INFO_BUFFER_SIZE,
    # Consecutive error tracking
    DEFAULT_MAX_CONSECUTIVE_ERRORS,
    # Defaults
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_TLS_PORT,
    DOMAIN_ICC,
    # Domain types
    DOMAIN_VCC,
    DS_CONDITIONS_ALL,
    DS_CONDITIONS_CHANGE,
    DS_CONDITIONS_DETECTED,
    DS_CONDITIONS_EXTERNAL_EVENT,
    DS_CONDITIONS_INTEGRITY,
    # DS Conditions
    DS_CONDITIONS_INTERVAL,
    DS_CONDITIONS_OPERATOR_REQUEST,
    DSTS_VAR_ALL_CHANGES_REPORTED,
    DSTS_VAR_BLOCK_DATA,
    DSTS_VAR_BUFFER_TIME,
    DSTS_VAR_CRITICAL,
    DSTS_VAR_DATA_SET_NAME,
    DSTS_VAR_DS_CONDITIONS,
    DSTS_VAR_EVENT_CODE_REQUESTED,
    DSTS_VAR_INTEGRITY_CHECK,
    DSTS_VAR_INTERVAL,
    DSTS_VAR_RBE,
    DSTS_VAR_START_TIME,
    DSTS_VAR_STATUS,
    DSTS_VAR_TLE,
    # Block 4: Information Messages
    IMTS_VAR_NAME,
    IMTS_VAR_STATUS,
    INFO_BUFF_VAR_ENTRIES,
    INFO_BUFF_VAR_NAME,
    INFO_BUFF_VAR_NEXT_ENTRY,
    INFO_BUFF_VAR_SIZE,
    INFO_MSG_VAR_CONTENT,
    INFO_MSG_VAR_INFO_REF,
    INFO_MSG_VAR_LOCAL_REF,
    INFO_MSG_VAR_MSG_ID,
    # Protocol limits
    MAX_DATA_SET_SIZE,
    # File download limits
    MAX_FILE_DOWNLOAD_SIZE,
    MAX_INFO_MESSAGE_SIZE,
    MAX_POINT_NAME_LENGTH,
    # Transfer set chain limit
    MAX_TRANSFER_SET_CHAIN,
    NEXT_DS_TRANSFER_SET,
    POINT_TYPE_DISCRETE,
    POINT_TYPE_DISCRETE_EXTENDED,
    POINT_TYPE_DISCRETE_Q,
    POINT_TYPE_DISCRETE_Q_TIME,
    POINT_TYPE_DISCRETE_Q_TIMETAG,
    POINT_TYPE_DISCRETE_Q_TIMETAG_EXTENDED,
    POINT_TYPE_PACKED_PROTECTION_EVENT,
    POINT_TYPE_REAL,
    POINT_TYPE_REAL_EXTENDED,
    POINT_TYPE_REAL_Q,
    # Legacy aliases
    POINT_TYPE_REAL_Q_TIME,
    POINT_TYPE_REAL_Q_TIMETAG,
    POINT_TYPE_REAL_Q_TIMETAG_EXTENDED,
    POINT_TYPE_SINGLE_PROTECTION_EVENT,
    # Point types
    POINT_TYPE_STATE,
    POINT_TYPE_STATE_EXTENDED,
    POINT_TYPE_STATE_Q,
    POINT_TYPE_STATE_Q_TIME,
    POINT_TYPE_STATE_Q_TIMETAG,
    POINT_TYPE_STATE_Q_TIMETAG_EXTENDED,
    POINT_TYPE_STATE_SUPPLEMENTAL,
    POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED,
    POINT_TYPE_STATE_SUPPLEMENTAL_Q,
    POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG,
    POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG_EXTENDED,
    POINT_TYPES,
    PROTECTION_EVENT_EARTH,
    # Protection event flags
    PROTECTION_EVENT_GENERAL,
    PROTECTION_EVENT_PHASE_A,
    PROTECTION_EVENT_PHASE_B,
    PROTECTION_EVENT_PHASE_C,
    PROTECTION_EVENT_REVERSE,
    # Legacy quality flags
    QUALITY_GOOD,
    QUALITY_HELD,
    QUALITY_INVALID,
    QUALITY_NORMAL_VALUE,
    QUALITY_SOURCE_CALCULATED,
    QUALITY_SOURCE_ENTERED,
    QUALITY_SOURCE_ESTIMATED,
    QUALITY_SOURCE_TELEMETERED,
    QUALITY_SUSPECT,
    QUALITY_TIMESTAMP_QUALITY,
    QUALITY_VALIDITY_HELD,
    QUALITY_VALIDITY_NOT_VALID,
    QUALITY_VALIDITY_SUSPECT,
    # Quality flags (bitmask)
    QUALITY_VALIDITY_VALID,
    # Report flags
    REPORT_BUFFERED,
    REPORT_INTEGRITY_TIMEOUT,
    REPORT_INTERVAL_TIMEOUT,
    REPORT_OBJECT_CHANGES,
    SBO_TIMEOUT,
    SERVER_PRIORITY_BACKUP,
    SERVER_PRIORITY_PRIMARY,
    # State values
    STATE_BETWEEN,
    # State check interval
    STATE_CHECK_INTERVAL,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_CONNECTED,
    STATE_CONNECTING,
    # Client states
    STATE_DISCONNECTED,
    STATE_INVALID,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
    STATE_TRIPPED,
    # Supported features
    SUPPORTED_FEATURES_BLOCK_1,
    SUPPORTED_FEATURES_BLOCK_2,
    SUPPORTED_FEATURES_BLOCK_3,
    SUPPORTED_FEATURES_BLOCK_4,
    SUPPORTED_FEATURES_BLOCK_5,
    SUPPORTED_FEATURES_BLOCK_6,
    SUPPORTED_FEATURES_BLOCK_7,
    SUPPORTED_FEATURES_BLOCK_8,
    SUPPORTED_FEATURES_BLOCK_9,
    SUPPORTED_FEATURES_VAR,
    TAG_CLOSE_ONLY_INHIBIT,
    TAG_INVALID,
    TAG_NONE,
    # Tag values
    TAG_OPEN_AND_CLOSE_INHIBIT,
    TAG_REASON_VAR_SUFFIX,
    TAG_STATE_ARMED,
    TAG_STATE_IDLE,
    # Tag variable names
    TAG_VAR_SUFFIX,
    # TASE.2 Editions
    TASE2_EDITION_1996,
    TASE2_EDITION_2000,
    TASE2_EDITION_AUTO,
    TASE2_VERSION_VAR,
    TRANSFER_REPORT_ACK,
    TRANSFER_REPORT_NACK,
    # Transfer set metadata
    TRANSFER_SET_METADATA_MEMBERS,
    TRANSFER_SET_METADATA_OFFSET,
    TRANSFER_SET_NAME_VAR,
    TRANSFER_SET_TIMESTAMP,
)

# Exceptions
from .exceptions import (
    AbortError,
    AccessDeniedError,
    AssociationError,
    # Authentication
    AuthenticationError,
    BilateralTableError,
    ConnectionClosedError,
    ConnectionError,  # Deprecated: use TASE2ConnectionError
    ConnectionFailedError,
    ConnectionTimeoutError,
    # Control
    ControlError,
    ControlNotSupportedError,
    # Data access
    DataAccessError,
    DataSetNotFoundError,
    DeviceBlockedError,
    DomainNotFoundError,
    IMNotSupportedError,
    IMTransferSetError,
    # Information messages (Block 4)
    InformationMessageError,
    InvalidParameterError,
    # Library
    LibraryError,
    LibraryNotFoundError,
    NotConnectedError,
    OperateError,
    # Operations (TASE2TimeoutError is the proper name, TimeoutError is deprecated alias)
    OperationError,
    # Protocol
    ProtocolError,
    RBENotSupportedError,
    ReadError,
    RejectError,
    ResourceNotFoundError,
    SelectError,
    ServiceError,
    TagError,
    # Connection (TASE2ConnectionError is the proper name, ConnectionError is deprecated alias)
    TASE2ConnectionError,
    # Base
    TASE2Error,
    TASE2TimeoutError,
    TimeoutError,  # Deprecated: use TASE2TimeoutError
    TransferSetConfigError,
    # Transfer sets
    TransferSetError,
    TransferSetNotFoundError,
    TypeMismatchError,
    VariableNotFoundError,
    WriteError,
    # Error mapping utility
    map_ied_error,
)

# Data types
from .types import (
    Association,
    BilateralTable,
    ClientStatistics,
    ControlPoint,
    DataFlags,
    DataSet,
    Domain,
    DSTransferSetConfig,
    IMTransferSetConfig,
    InformationBuffer,
    InformationMessage,
    PointValue,
    ProtectionEvent,
    SBOState,
    ServerAddress,
    ServerInfo,
    TagState,
    TransferReport,
    TransferSet,
    TransferSetConditions,
    Variable,
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
    "DSTransferSetConfig",
    "TransferReport",
    "SBOState",
    "BilateralTable",
    "ServerInfo",
    "Association",
    "InformationMessage",
    "IMTransferSetConfig",
    "InformationBuffer",
    "TagState",
    "ClientStatistics",
    "ServerAddress",
    # Constants
    "DEFAULT_PORT",
    "DEFAULT_TLS_PORT",
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
    "DS_CONDITIONS_INTEGRITY",
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
    "BLOCK_6",
    "BLOCK_7",
    "BLOCK_8",
    "BLOCK_9",
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
    # State check interval
    "STATE_CHECK_INTERVAL",
    # Standard TASE.2 named variables
    "BILATERAL_TABLE_ID_VAR",
    "SUPPORTED_FEATURES_VAR",
    "TASE2_VERSION_VAR",
    "TRANSFER_SET_NAME_VAR",
    "DSTS_VAR_DATA_SET_NAME",
    "DSTS_VAR_START_TIME",
    "DSTS_VAR_INTERVAL",
    "DSTS_VAR_TLE",
    "DSTS_VAR_BUFFER_TIME",
    "DSTS_VAR_INTEGRITY_CHECK",
    "DSTS_VAR_DS_CONDITIONS",
    "DSTS_VAR_BLOCK_DATA",
    "DSTS_VAR_CRITICAL",
    "DSTS_VAR_RBE",
    "DSTS_VAR_ALL_CHANGES_REPORTED",
    "DSTS_VAR_STATUS",
    "DSTS_VAR_EVENT_CODE_REQUESTED",
    "TRANSFER_REPORT_ACK",
    "TRANSFER_REPORT_NACK",
    "NEXT_DS_TRANSFER_SET",
    "DS_CONDITIONS_DETECTED",
    "TRANSFER_SET_TIMESTAMP",
    # Supported features
    "SUPPORTED_FEATURES_BLOCK_1",
    "SUPPORTED_FEATURES_BLOCK_2",
    "SUPPORTED_FEATURES_BLOCK_3",
    "SUPPORTED_FEATURES_BLOCK_4",
    "SUPPORTED_FEATURES_BLOCK_5",
    "SUPPORTED_FEATURES_BLOCK_6",
    "SUPPORTED_FEATURES_BLOCK_7",
    "SUPPORTED_FEATURES_BLOCK_8",
    "SUPPORTED_FEATURES_BLOCK_9",
    # Block 4: Information Messages
    "IMTS_VAR_NAME",
    "IMTS_VAR_STATUS",
    "INFO_BUFF_VAR_NAME",
    "INFO_BUFF_VAR_SIZE",
    "INFO_BUFF_VAR_NEXT_ENTRY",
    "INFO_BUFF_VAR_ENTRIES",
    "INFO_MSG_VAR_INFO_REF",
    "INFO_MSG_VAR_LOCAL_REF",
    "INFO_MSG_VAR_MSG_ID",
    "INFO_MSG_VAR_CONTENT",
    "MAX_INFO_MESSAGE_SIZE",
    "DEFAULT_INFO_BUFFER_SIZE",
    # TASE.2 Editions
    "TASE2_EDITION_1996",
    "TASE2_EDITION_2000",
    "TASE2_EDITION_AUTO",
    # Tag variable names
    "TAG_STATE_IDLE",
    "TAG_STATE_ARMED",
    "TAG_VAR_SUFFIX",
    "TAG_REASON_VAR_SUFFIX",
    # File download limits
    "MAX_FILE_DOWNLOAD_SIZE",
    # Transfer set chain limit
    "MAX_TRANSFER_SET_CHAIN",
    # Failover configuration
    "DEFAULT_FAILOVER_RETRY_COUNT",
    "DEFAULT_FAILOVER_DELAY",
    "SERVER_PRIORITY_PRIMARY",
    "SERVER_PRIORITY_BACKUP",
    # Consecutive error tracking
    "DEFAULT_MAX_CONSECUTIVE_ERRORS",
    # Transfer set metadata
    "TRANSFER_SET_METADATA_MEMBERS",
    "TRANSFER_SET_METADATA_OFFSET",
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
    "InformationMessageError",
    "IMTransferSetError",
    "IMNotSupportedError",
    "TransferSetError",
    "RBENotSupportedError",
    "TransferSetConfigError",
    "ProtocolError",
    "ServiceError",
    "RejectError",
    "AbortError",
    "map_ied_error",
]

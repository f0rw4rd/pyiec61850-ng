#!/usr/bin/env python3
"""
TASE.2/ICCP Protocol Constants

Protocol constants, point types, and conformance blocks for TASE.2.
"""

DEFAULT_PORT = 102
DEFAULT_TLS_PORT = 3782
DEFAULT_TIMEOUT = 10000  # milliseconds

# Point Types (Indication Points)
# Base types (value only)
POINT_TYPE_STATE = 1
POINT_TYPE_STATE_SUPPLEMENTAL = 2
POINT_TYPE_DISCRETE = 3
POINT_TYPE_REAL = 4

# With Quality flags
POINT_TYPE_STATE_Q = 5
POINT_TYPE_STATE_SUPPLEMENTAL_Q = 6
POINT_TYPE_DISCRETE_Q = 7
POINT_TYPE_REAL_Q = 8

# With Quality + Timestamp
POINT_TYPE_STATE_Q_TIMETAG = 9
POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG = 10
POINT_TYPE_DISCRETE_Q_TIMETAG = 11
POINT_TYPE_REAL_Q_TIMETAG = 12

# With Quality + TimeStampExtended (millisecond resolution, no COV)
POINT_TYPE_STATE_Q_TIMETAG_EXTENDED = 13
POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG_EXTENDED = 14
POINT_TYPE_DISCRETE_Q_TIMETAG_EXTENDED = 15
POINT_TYPE_REAL_Q_TIMETAG_EXTENDED = 16

# Extended (with Quality + TimeStampExtended + COV counter)
POINT_TYPE_STATE_EXTENDED = 17
POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED = 18
POINT_TYPE_DISCRETE_EXTENDED = 19
POINT_TYPE_REAL_EXTENDED = 20

# Protection Events
POINT_TYPE_SINGLE_PROTECTION_EVENT = 21
POINT_TYPE_PACKED_PROTECTION_EVENT = 22

POINT_TYPES = {
    POINT_TYPE_STATE: ("STATE", "2-bit discrete state"),
    POINT_TYPE_STATE_SUPPLEMENTAL: ("STATE_SUPPLEMENTAL", "State with supplemental info"),
    POINT_TYPE_DISCRETE: ("DISCRETE", "32-bit signed integer"),
    POINT_TYPE_REAL: ("REAL", "32-bit floating point"),
    POINT_TYPE_STATE_Q: ("STATE_Q", "State with quality flags"),
    POINT_TYPE_STATE_SUPPLEMENTAL_Q: ("STATE_SUPPLEMENTAL_Q", "State supplemental with quality"),
    POINT_TYPE_DISCRETE_Q: ("DISCRETE_Q", "Discrete with quality flags"),
    POINT_TYPE_REAL_Q: ("REAL_Q", "Real with quality flags"),
    POINT_TYPE_STATE_Q_TIMETAG: ("STATE_Q_TIMETAG", "State with quality and timestamp"),
    POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG: ("STATE_SUPPLEMENTAL_Q_TIMETAG", "State supplemental with quality and timestamp"),
    POINT_TYPE_DISCRETE_Q_TIMETAG: ("DISCRETE_Q_TIMETAG", "Discrete with quality and timestamp"),
    POINT_TYPE_REAL_Q_TIMETAG: ("REAL_Q_TIMETAG", "Real with quality and timestamp"),
    POINT_TYPE_STATE_Q_TIMETAG_EXTENDED: ("STATE_Q_TIMETAG_EXTENDED", "State with quality and extended timestamp (ms)"),
    POINT_TYPE_STATE_SUPPLEMENTAL_Q_TIMETAG_EXTENDED: ("STATE_SUPPLEMENTAL_Q_TIMETAG_EXTENDED", "State supplemental with quality and extended timestamp (ms)"),
    POINT_TYPE_DISCRETE_Q_TIMETAG_EXTENDED: ("DISCRETE_Q_TIMETAG_EXTENDED", "Discrete with quality and extended timestamp (ms)"),
    POINT_TYPE_REAL_Q_TIMETAG_EXTENDED: ("REAL_Q_TIMETAG_EXTENDED", "Real with quality and extended timestamp (ms)"),
    POINT_TYPE_STATE_EXTENDED: ("STATE_EXTENDED", "State with quality, extended timestamp, and COV"),
    POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED: ("STATE_SUPPLEMENTAL_EXTENDED", "State supplemental extended"),
    POINT_TYPE_DISCRETE_EXTENDED: ("DISCRETE_EXTENDED", "Discrete with quality, extended timestamp, and COV"),
    POINT_TYPE_REAL_EXTENDED: ("REAL_EXTENDED", "Real with quality, extended timestamp, and COV"),
    POINT_TYPE_SINGLE_PROTECTION_EVENT: ("SINGLE_PROTECTION_EVENT", "Single protection event"),
    POINT_TYPE_PACKED_PROTECTION_EVENT: ("PACKED_PROTECTION_EVENT", "Packed protection events"),
}

# Legacy aliases
POINT_TYPE_REAL_Q_TIME = POINT_TYPE_REAL_Q_TIMETAG
POINT_TYPE_STATE_Q_TIME = POINT_TYPE_STATE_Q_TIMETAG
POINT_TYPE_DISCRETE_Q_TIME = POINT_TYPE_DISCRETE_Q_TIMETAG

# Control Point Types
CONTROL_TYPE_COMMAND = 1
CONTROL_TYPE_SETPOINT_REAL = 2
CONTROL_TYPE_SETPOINT_DISCRETE = 3

CONTROL_TYPES = {
    CONTROL_TYPE_COMMAND: ("COMMAND", "Binary command (ON/OFF)"),
    CONTROL_TYPE_SETPOINT_REAL: ("SETPOINT_REAL", "Real setpoint value"),
    CONTROL_TYPE_SETPOINT_DISCRETE: ("SETPOINT_DISCRETE", "Discrete setpoint value"),
}

# Conformance Blocks
# Blocks 1-5 are normative (2014 edition), blocks 6-9 are informative (legacy).
BLOCK_1 = 1  # Basic services (mandatory)
BLOCK_2 = 2  # Report-by-Exception (RBE)
BLOCK_3 = 3  # Blocked data transfers
BLOCK_4 = 4  # Information messages
BLOCK_5 = 5  # Device control (commands, SBO)
BLOCK_6 = 6  # Program invocation (informative since 2014)
BLOCK_7 = 7  # Event enrollment and notification (informative since 2014)
BLOCK_8 = 8  # Transfer accounts and energy scheduling (informative since 2014)
BLOCK_9 = 9  # Historical time-series data (informative since 2014)

CONFORMANCE_BLOCKS = {
    BLOCK_1: ("BASIC", "Basic services - association, data values, datasets, transfers"),
    BLOCK_2: ("RBE", "Report-by-Exception - conditional monitoring, event-driven transfer"),
    BLOCK_3: ("BLOCKED_TRANSFERS", "Blocked data transfers (informative since 2014)"),
    BLOCK_4: ("INFO_MSG", "Information messages - ASCII text, binary file transfer"),
    BLOCK_5: ("CONTROL", "Device control - commands, select-before-operate"),
    BLOCK_6: ("PROGRAMS", "Program invocation (informative since 2014)"),
    BLOCK_7: ("EVENTS", "Event enrollment and notification (informative since 2014)"),
    BLOCK_8: ("ACCOUNTS", "Transfer accounts and energy scheduling (informative since 2014)"),
    BLOCK_9: ("TIME_SERIES", "Historical time-series data (informative since 2014)"),
}

# State Values (2-bit discrete)
#   00 = Between/Intermediate
#   01 = Off/Tripped/Open
#   10 = On/Closed
#   11 = Invalid
STATE_BETWEEN = 0
STATE_OFF = 1
STATE_ON = 2
STATE_INVALID = 3

STATE_CLOSED = STATE_ON
STATE_TRIPPED = STATE_OFF
STATE_OPEN = STATE_OFF

# Data Flags (Quality) - 8-bit bitmask
#
# Bit layout:
#   Bits 0-1: Reserved
#   Bits 2-3: Validity (HI=bit2, LO=bit3)
#   Bits 4-5: Current Source (HI=bit4, LO=bit5)
#   Bit 6: Normal Value
#   Bit 7: Timestamp Quality (suspect if set)
#
# Validity (bits 2-3)
QUALITY_VALIDITY_VALID = 0
QUALITY_VALIDITY_SUSPECT = 4
QUALITY_VALIDITY_HELD = 8
QUALITY_VALIDITY_NOT_VALID = 12

# Current Source (bits 4-5)
QUALITY_SOURCE_TELEMETERED = 0
QUALITY_SOURCE_ENTERED = 16
QUALITY_SOURCE_CALCULATED = 32
QUALITY_SOURCE_ESTIMATED = 48

# Additional flags (bits 6-7)
QUALITY_NORMAL_VALUE = 64
QUALITY_TIMESTAMP_QUALITY = 128

# Legacy string-based quality flags
QUALITY_GOOD = "GOOD"
QUALITY_INVALID = "INVALID"
QUALITY_HELD = "HELD"
QUALITY_SUSPECT = "SUSPECT"
QUALITY_OVERFLOW = "OVERFLOW"
QUALITY_OUT_OF_RANGE = "OUT_OF_RANGE"
QUALITY_BAD_REFERENCE = "BAD_REFERENCE"
QUALITY_OSCILLATORY = "OSCILLATORY"
QUALITY_FAILURE = "FAILURE"
QUALITY_OLD_DATA = "OLD_DATA"
QUALITY_INCONSISTENT = "INCONSISTENT"
QUALITY_INACCURATE = "INACCURATE"

# Transfer Set Report Flags (bitmask)
REPORT_BUFFERED = 1
REPORT_INTERVAL_TIMEOUT = 2
REPORT_OBJECT_CHANGES = 4
REPORT_INTEGRITY_TIMEOUT = 8
REPORT_ALL_CHANGES = 16

# DS Transfer Set Conditions (DSConditions) - bitmask
DS_CONDITIONS_INTERVAL = 1           # bit 0: Interval timeout
DS_CONDITIONS_INTEGRITY = 2          # bit 1: Integrity timeout
DS_CONDITIONS_CHANGE = 4             # bit 2: Object change detected
DS_CONDITIONS_OPERATOR_REQUEST = 8   # bit 3: Operator requested
DS_CONDITIONS_EXTERNAL_EVENT = 16    # bit 4: External event
DS_CONDITIONS_ALL = 31               # All conditions (bits 0-4)

# Protection Event Flags
PROTECTION_EVENT_GENERAL = 1
PROTECTION_EVENT_PHASE_A = 2
PROTECTION_EVENT_PHASE_B = 4
PROTECTION_EVENT_PHASE_C = 8
PROTECTION_EVENT_EARTH = 16
PROTECTION_EVENT_REVERSE = 32

# Single Protection Event Quality Flags
SINGLE_EVENT_ELAPSED_TIME_VALIDITY = 1
SINGLE_EVENT_BLOCKED = 2
SINGLE_EVENT_SUBSTITUTED = 4
SINGLE_EVENT_TOPICAL = 8
SINGLE_EVENT_EVENT_VALIDITY = 16
SINGLE_EVENT_EVENT_STATE_HI = 64
SINGLE_EVENT_EVENT_STATE_LO = 128

# Packed Protection Event Quality Flags
PACKED_EVENT_ELAPSED_TIME_VALIDITY = 1
PACKED_EVENT_BLOCKED = 2
PACKED_EVENT_SUBSTITUTED = 4
PACKED_EVENT_TOPICAL = 8
PACKED_EVENT_EVENT_VALIDITY = 16

# Command Values
CMD_OFF = 0
CMD_ON = 1

# Tag Values
TAG_NONE = 0
TAG_OPEN_AND_CLOSE_INHIBIT = 1
TAG_CLOSE_ONLY_INHIBIT = 2
TAG_INVALID = 3

# Tag Device State
TAG_STATE_IDLE = 0
TAG_STATE_ARMED = 1

# Client States
STATE_DISCONNECTED = 0
STATE_CONNECTING = 1
STATE_CONNECTED = 2
STATE_CLOSING = 3

CLIENT_STATES = {
    STATE_DISCONNECTED: "DISCONNECTED",
    STATE_CONNECTING: "CONNECTING",
    STATE_CONNECTED: "CONNECTED",
    STATE_CLOSING: "CLOSING",
}

# Transfer Set States
TS_STATE_DISABLED = 0
TS_STATE_ENABLED = 1

# Domain Types
DOMAIN_VCC = "VCC"
DOMAIN_ICC = "ICC"

# MMS Error Codes (subset relevant to TASE.2)
MMS_ERROR_NONE = 0
MMS_ERROR_CONNECTION_REJECTED = 1
MMS_ERROR_CONNECTION_LOST = 2
MMS_ERROR_TIMEOUT = 3
MMS_ERROR_ACCESS_DENIED = 4
MMS_ERROR_OBJECT_NOT_FOUND = 5
MMS_ERROR_INVALID_ARGUMENT = 6
MMS_ERROR_SERVICE_ERROR = 7
MMS_ERROR_TEMPORARILY_UNAVAILABLE = 8
MMS_ERROR_HARDWARE_FAULT = 9
MMS_ERROR_OBJECT_ATTRIBUTE_INCONSISTENT = 10

# Protocol Limits
MAX_DATA_SET_SIZE = 500
SBO_TIMEOUT = 30  # seconds
MAX_POINT_NAME_LENGTH = 32
STATE_CHECK_INTERVAL = 5.0  # seconds

# Standard TASE.2 Named Variables
BILATERAL_TABLE_ID_VAR = "Bilateral_Table_ID"
SUPPORTED_FEATURES_VAR = "Supported_Features"
TASE2_VERSION_VAR = "TASE.2_Version"
TRANSFER_SET_NAME_VAR = "Transfer_Set_Name"

# DS Transfer Set variables
DSTS_VAR_DATA_SET_NAME = "DSTransferSet_DataSetName"
DSTS_VAR_START_TIME = "DSTransferSet_StartTime"
DSTS_VAR_INTERVAL = "DSTransferSet_Interval"
DSTS_VAR_TLE = "DSTransferSet_TLE"
DSTS_VAR_BUFFER_TIME = "DSTransferSet_BufferTime"
DSTS_VAR_INTEGRITY_CHECK = "DSTransferSet_IntegrityCheck"
DSTS_VAR_DS_CONDITIONS = "DSTransferSet_DSConditionsRequested"
DSTS_VAR_BLOCK_DATA = "DSTransferSet_BlockData"
DSTS_VAR_CRITICAL = "DSTransferSet_Critical"
DSTS_VAR_RBE = "DSTransferSet_RBE"
DSTS_VAR_ALL_CHANGES_REPORTED = "DSTransferSet_AllChangesReported"
DSTS_VAR_STATUS = "DSTransferSet_Status"
DSTS_VAR_EVENT_CODE_REQUESTED = "DSTransferSet_EventCodeRequested"

# Transfer report variables
TRANSFER_REPORT_ACK = "Transfer_Report_ACK"
TRANSFER_REPORT_NACK = "Transfer_Report_NACK"

NEXT_DS_TRANSFER_SET = "Next_DSTransfer_Set"
DS_CONDITIONS_DETECTED = "DSConditions_Detected"
TRANSFER_SET_TIMESTAMP = "Transfer_Set_Time_Stamp"

# Supported Features bitstring positions (conformance blocks)
# Bit 0 is MSB of the first octet (0x80), matching ASN.1 BITSTRING encoding
# and libiec61850 MmsValue_getBitStringAsInteger() output.
SUPPORTED_FEATURES_BLOCK_1 = 0x80
SUPPORTED_FEATURES_BLOCK_2 = 0x40
SUPPORTED_FEATURES_BLOCK_3 = 0x20
SUPPORTED_FEATURES_BLOCK_4 = 0x10
SUPPORTED_FEATURES_BLOCK_5 = 0x08
SUPPORTED_FEATURES_BLOCK_6 = 0x04
SUPPORTED_FEATURES_BLOCK_7 = 0x02
SUPPORTED_FEATURES_BLOCK_8 = 0x01
# Block 9 is bit 8 (MSB of second octet in a 2-octet bitstring)
SUPPORTED_FEATURES_BLOCK_9 = 0x8000

_SUPPORTED_FEATURES_BIT_MAP = [
    (SUPPORTED_FEATURES_BLOCK_1, BLOCK_1),
    (SUPPORTED_FEATURES_BLOCK_2, BLOCK_2),
    (SUPPORTED_FEATURES_BLOCK_3, BLOCK_3),
    (SUPPORTED_FEATURES_BLOCK_4, BLOCK_4),
    (SUPPORTED_FEATURES_BLOCK_5, BLOCK_5),
    (SUPPORTED_FEATURES_BLOCK_6, BLOCK_6),
    (SUPPORTED_FEATURES_BLOCK_7, BLOCK_7),
    (SUPPORTED_FEATURES_BLOCK_8, BLOCK_8),
    (SUPPORTED_FEATURES_BLOCK_9, BLOCK_9),
]

# Block 4: Information Messages
IMTS_VAR_NAME = "IM_Transfer_Set"
IMTS_VAR_STATUS = "IM_Transfer_Set_Status"

INFO_BUFF_VAR_NAME = "Information_Buffer_Name"
INFO_BUFF_VAR_SIZE = "Information_Buffer_Size"
INFO_BUFF_VAR_NEXT_ENTRY = "Next_Buffer_Entry"
INFO_BUFF_VAR_ENTRIES = "Buffer_Entry_Count"

INFO_MSG_VAR_INFO_REF = "InfoRef"
INFO_MSG_VAR_LOCAL_REF = "LocalRef"
INFO_MSG_VAR_MSG_ID = "MsgId"
INFO_MSG_VAR_CONTENT = "InfoContent"

MAX_INFO_MESSAGE_SIZE = 65535
DEFAULT_INFO_BUFFER_SIZE = 64

# TASE.2 Edition identifiers
TASE2_EDITION_1996 = "1996.08"
TASE2_EDITION_2000 = "2000.08"
TASE2_EDITION_AUTO = "auto"

# Tag variable name suffixes (Block 5)
TAG_VAR_SUFFIX = "_TAG"
TAG_REASON_VAR_SUFFIX = "_TagReason"

MAX_FILE_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TRANSFER_SET_CHAIN = 100

# Failover Configuration
DEFAULT_FAILOVER_RETRY_COUNT = 1
DEFAULT_FAILOVER_DELAY = 1.0

SERVER_PRIORITY_PRIMARY = "primary"
SERVER_PRIORITY_BACKUP = "backup"

# Consecutive Error Tracking
DEFAULT_MAX_CONSECUTIVE_ERRORS = 10

# Transfer Set Metadata Members
# Standard mandatory members prepended to datasets for transfer set reports:
#   [0] Transfer_Set_Name
#   [1] Transfer_Set_Time_Stamp
#   [2] DSConditions_Detected
# These are access-denied when read directly but are populated in reports.
TRANSFER_SET_METADATA_MEMBERS = [
    "Transfer_Set_Name",
    "Transfer_Set_Time_Stamp",
    "DSConditions_Detected",
]

TRANSFER_SET_METADATA_OFFSET = 3

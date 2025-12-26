#!/usr/bin/env python3
"""
TASE.2/ICCP Protocol Constants (IEC 60870-6)

This module defines protocol constants, point types, and conformance blocks
for the TASE.2 protocol implementation.
"""

# Default TASE.2/MMS port
DEFAULT_PORT = 102

# Default timeout in milliseconds
DEFAULT_TIMEOUT = 10000

# TASE.2 Point Types (Indication Points) - per IEC 60870-6
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

# Extended (with Quality + Timestamp + COV counter)
POINT_TYPE_STATE_EXTENDED = 13
POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED = 14
POINT_TYPE_DISCRETE_EXTENDED = 15
POINT_TYPE_REAL_EXTENDED = 16

# Protection Events
POINT_TYPE_SINGLE_PROTECTION_EVENT = 17
POINT_TYPE_PACKED_PROTECTION_EVENT = 18

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
    POINT_TYPE_STATE_EXTENDED: ("STATE_EXTENDED", "State with quality, timestamp, and COV"),
    POINT_TYPE_STATE_SUPPLEMENTAL_EXTENDED: ("STATE_SUPPLEMENTAL_EXTENDED", "State supplemental extended"),
    POINT_TYPE_DISCRETE_EXTENDED: ("DISCRETE_EXTENDED", "Discrete with quality, timestamp, and COV"),
    POINT_TYPE_REAL_EXTENDED: ("REAL_EXTENDED", "Real with quality, timestamp, and COV"),
    POINT_TYPE_SINGLE_PROTECTION_EVENT: ("SINGLE_PROTECTION_EVENT", "Single protection event"),
    POINT_TYPE_PACKED_PROTECTION_EVENT: ("PACKED_PROTECTION_EVENT", "Packed protection events"),
}

# Legacy aliases for backward compatibility
POINT_TYPE_REAL_Q_TIME = POINT_TYPE_REAL_Q_TIMETAG
POINT_TYPE_STATE_Q_TIME = POINT_TYPE_STATE_Q_TIMETAG
POINT_TYPE_DISCRETE_Q_TIME = POINT_TYPE_DISCRETE_Q_TIMETAG

# TASE.2 Control Point Types
CONTROL_TYPE_COMMAND = 1
CONTROL_TYPE_SETPOINT_REAL = 2
CONTROL_TYPE_SETPOINT_DISCRETE = 3

CONTROL_TYPES = {
    CONTROL_TYPE_COMMAND: ("COMMAND", "Binary command (ON/OFF)"),
    CONTROL_TYPE_SETPOINT_REAL: ("SETPOINT_REAL", "Real setpoint value"),
    CONTROL_TYPE_SETPOINT_DISCRETE: ("SETPOINT_DISCRETE", "Discrete setpoint value"),
}

# TASE.2 Conformance Blocks
BLOCK_1 = 1  # Basic services (mandatory)
BLOCK_2 = 2  # Report-by-Exception (RBE)
BLOCK_3 = 3  # Reserved (blocked transfers)
BLOCK_4 = 4  # Information messages
BLOCK_5 = 5  # Device control (commands, SBO)

CONFORMANCE_BLOCKS = {
    BLOCK_1: ("BASIC", "Basic services - association, data values, datasets, transfers"),
    BLOCK_2: ("RBE", "Report-by-Exception - conditional monitoring, event-driven transfer"),
    BLOCK_3: ("RESERVED", "Reserved - blocked transfers"),
    BLOCK_4: ("INFO_MSG", "Information messages - ASCII text, binary file transfer"),
    BLOCK_5: ("CONTROL", "Device control - commands, select-before-operate"),
}

# TASE.2 State Values (2-bit discrete)
STATE_BETWEEN = 0      # Intermediate/transitional state
STATE_ON = 1           # Also: CLOSED
STATE_OFF = 2          # Also: TRIPPED
STATE_INVALID = 3      # Invalid/unknown state

# Aliases for common terminology
STATE_CLOSED = STATE_ON
STATE_TRIPPED = STATE_OFF
STATE_OPEN = STATE_OFF

# TASE.2 Data Flags (Quality) - 8-bit bitmask per IEC 60870-6
#
# Bit layout:
#   Bits 0-1: Reserved (unused)
#   Bits 2-3: Validity - indicates data quality
#   Bits 4-5: Current Source - indicates data origin
#   Bit 6: Normal Value - indicates value is within normal operating range
#   Bit 7: Timestamp Quality - indicates timestamp is suspect if set
#
# Note: These values follow libiec61850 conventions which may differ from
# raw IEC 60870-6 specification ordering. The library uses these values
# internally for compatibility with libiec61850.
#
# Validity (bits 2-3, values 0/4/8/12)
# Per fcovatti/iccp reference: 00=Valid, 01=Held, 10=Suspect, 11=Invalid
QUALITY_VALIDITY_VALID = 0       # 0b00xx - Data is good/valid
QUALITY_VALIDITY_HELD = 4        # 0b01xx - Data is held/frozen
QUALITY_VALIDITY_SUSPECT = 8     # 0b10xx - Data quality is suspect
QUALITY_VALIDITY_NOT_VALID = 12  # 0b11xx - Data is invalid

# Current Source (bits 4-5, values 0/16/32/48)
QUALITY_SOURCE_TELEMETERED = 0   # 0bxx00xxxx - Value from field device
QUALITY_SOURCE_ENTERED = 16      # 0bxx01xxxx - Manually entered value
QUALITY_SOURCE_CALCULATED = 32   # 0bxx10xxxx - Calculated/derived value
QUALITY_SOURCE_ESTIMATED = 48    # 0bxx11xxxx - Estimated/substituted value

# Additional flags (bits 6-7)
QUALITY_NORMAL_VALUE = 64        # 0b01xxxxxx - Value is within normal range
QUALITY_TIMESTAMP_QUALITY = 128  # 0b10xxxxxx - Timestamp quality is suspect

# Legacy string-based quality flags (for backward compatibility)
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

# Data Set Transfer Set Conditions (DSConditions) - per IEC 60870-6
DS_CONDITIONS_INTERVAL = 1           # Interval timeout
DS_CONDITIONS_CHANGE = 2             # Object change detected
DS_CONDITIONS_OPERATOR_REQUEST = 4   # Operator requested
DS_CONDITIONS_EXTERNAL_EVENT = 8     # External event
DS_CONDITIONS_ALL = 15               # All conditions

# Protection Event Flags
PROTECTION_EVENT_GENERAL = 1
PROTECTION_EVENT_PHASE_A = 2
PROTECTION_EVENT_PHASE_B = 4
PROTECTION_EVENT_PHASE_C = 8
PROTECTION_EVENT_EARTH = 16
PROTECTION_EVENT_REVERSE = 32

# Control/Command Values
CMD_OFF = 0
CMD_ON = 1

# Tag Values (for device tagging)
TAG_OPEN_AND_CLOSE_INHIBIT = 0
TAG_CLOSE_ONLY_INHIBIT = 1
TAG_NONE = 2

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
DOMAIN_VCC = "VCC"  # Virtual Control Center (global scope)
DOMAIN_ICC = "ICC"  # Intercontrol Center (domain-limited scope)

# MMS Error Codes (subset relevant to TASE.2)
MMS_ERROR_NONE = 0
MMS_ERROR_CONNECTION_REJECTED = 1
MMS_ERROR_CONNECTION_LOST = 2
MMS_ERROR_TIMEOUT = 3
MMS_ERROR_ACCESS_DENIED = 4
MMS_ERROR_OBJECT_NOT_FOUND = 5
MMS_ERROR_INVALID_ARGUMENT = 6
MMS_ERROR_SERVICE_ERROR = 7

# TASE.2 Protocol Limits
# Maximum number of data set members per IEC 60870-6
MAX_DATA_SET_SIZE = 500

# Select-Before-Operate timeout in seconds (per IEC 60870-6)
# The select state expires if operate is not received within this time
SBO_TIMEOUT = 30

# Maximum data point name length per IEC 60870-6-503
MAX_POINT_NAME_LENGTH = 32

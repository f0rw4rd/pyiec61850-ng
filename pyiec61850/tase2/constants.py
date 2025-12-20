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

# TASE.2 Point Types (Indication Points)
POINT_TYPE_REAL = 1
POINT_TYPE_STATE = 2
POINT_TYPE_DISCRETE = 3
POINT_TYPE_REAL_Q = 4
POINT_TYPE_STATE_Q = 5
POINT_TYPE_DISCRETE_Q = 6
POINT_TYPE_REAL_Q_TIME = 7
POINT_TYPE_STATE_Q_TIME = 8
POINT_TYPE_DISCRETE_Q_TIME = 9
POINT_TYPE_STATE_SUPPLEMENTAL = 10

POINT_TYPES = {
    POINT_TYPE_REAL: ("REAL", "Analog measurement (float)"),
    POINT_TYPE_STATE: ("STATE", "Binary state (0/1)"),
    POINT_TYPE_DISCRETE: ("DISCRETE", "Integer counter"),
    POINT_TYPE_REAL_Q: ("REAL_Q", "Analog with quality"),
    POINT_TYPE_STATE_Q: ("STATE_Q", "State with quality"),
    POINT_TYPE_DISCRETE_Q: ("DISCRETE_Q", "Discrete with quality"),
    POINT_TYPE_REAL_Q_TIME: ("REAL_Q_TIME", "Analog with quality and timestamp"),
    POINT_TYPE_STATE_Q_TIME: ("STATE_Q_TIME", "State with quality and timestamp"),
    POINT_TYPE_DISCRETE_Q_TIME: ("DISCRETE_Q_TIME", "Discrete with quality and timestamp"),
    POINT_TYPE_STATE_SUPPLEMENTAL: ("STATE_SUPPLEMENTAL", "State with supplemental info"),
}

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

# Quality flags
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

#!/usr/bin/env python3
"""
MMS Type Enumerations

Clean Python enums for IEC 61850 / MMS constants.
Values match the libiec61850 C library definitions.
"""

from enum import IntEnum

try:
    import pyiec61850.pyiec61850 as _iec
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    _iec = None


def _c(name, fallback):
    """Get constant from SWIG bindings with hardcoded fallback."""
    if _HAS_IEC61850:
        return getattr(_iec, name, fallback)
    return fallback


class MmsType(IntEnum):
    """MMS data type identifiers (from mms_common.h MmsType enum)."""
    ARRAY = _c('MMS_ARRAY', 0)
    STRUCTURE = _c('MMS_STRUCTURE', 1)
    BOOLEAN = _c('MMS_BOOLEAN', 2)
    BIT_STRING = _c('MMS_BIT_STRING', 3)
    INTEGER = _c('MMS_INTEGER', 4)
    UNSIGNED = _c('MMS_UNSIGNED', 5)
    FLOAT = _c('MMS_FLOAT', 6)
    OCTET_STRING = _c('MMS_OCTET_STRING', 7)
    VISIBLE_STRING = _c('MMS_VISIBLE_STRING', 8)
    BINARY_TIME = _c('MMS_BINARY_TIME', 10)
    STRING = _c('MMS_STRING', 13)
    UTC_TIME = _c('MMS_UTC_TIME', 14)
    DATA_ACCESS_ERROR = _c('MMS_DATA_ACCESS_ERROR', 15)


class FC(IntEnum):
    """IEC 61850 Functional Constraints (from iec61850_common.h)."""
    ST = _c('IEC61850_FC_ST', 0)
    MX = _c('IEC61850_FC_MX', 1)
    SP = _c('IEC61850_FC_SP', 2)
    SV = _c('IEC61850_FC_SV', 3)
    CF = _c('IEC61850_FC_CF', 4)
    DC = _c('IEC61850_FC_DC', 5)
    SG = _c('IEC61850_FC_SG', 6)
    SE = _c('IEC61850_FC_SE', 7)
    SR = _c('IEC61850_FC_SR', 8)
    OR = _c('IEC61850_FC_OR', 9)
    BL = _c('IEC61850_FC_BL', 10)
    EX = _c('IEC61850_FC_EX', 11)
    CO = _c('IEC61850_FC_CO', 12)
    US = _c('IEC61850_FC_US', 13)
    MS = _c('IEC61850_FC_MS', 14)
    RP = _c('IEC61850_FC_RP', 15)
    BR = _c('IEC61850_FC_BR', 16)
    LG = _c('IEC61850_FC_LG', 17)
    GO = _c('IEC61850_FC_GO', 18)


class ACSIClass(IntEnum):
    """ACSI service classes (from iec61850_common.h)."""
    DATA_OBJECT = _c('ACSI_CLASS_DATA_OBJECT', 0)
    DATA_SET = _c('ACSI_CLASS_DATA_SET', 1)
    BRCB = _c('ACSI_CLASS_BRCB', 2)
    URCB = _c('ACSI_CLASS_URCB', 3)
    LCB = _c('ACSI_CLASS_LCB', 4)
    LOG = _c('ACSI_CLASS_LOG', 5)
    SGCB = _c('ACSI_CLASS_SGCB', 6)
    GoCB = _c('ACSI_CLASS_GoCB', 7)
    GsCB = _c('ACSI_CLASS_GsCB', 8)
    MSVCB = _c('ACSI_CLASS_MSVCB', 9)
    USVCB = _c('ACSI_CLASS_USVCB', 10)

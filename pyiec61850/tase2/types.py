#!/usr/bin/env python3
"""
TASE.2/ICCP Data Types (IEC 60870-6)

This module defines data classes for TASE.2 protocol objects including
domains, variables, data points, transfer sets, and bilateral tables.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Dict

from .constants import (
    QUALITY_GOOD,
    DOMAIN_VCC,
    POINT_TYPES,
    CONTROL_TYPES,
    CONFORMANCE_BLOCKS,
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
    DS_CONDITIONS_INTERVAL,
    DS_CONDITIONS_CHANGE,
    DS_CONDITIONS_OPERATOR_REQUEST,
    DS_CONDITIONS_EXTERNAL_EVENT,
)


@dataclass
class DataFlags:
    """
    TASE.2 Data Flags (Quality) - 8-bit bitmask per IEC 60870-6.

    The quality flags indicate the validity and source of data values.
    """
    validity: int = QUALITY_VALIDITY_VALID
    source: int = QUALITY_SOURCE_TELEMETERED
    normal_value: bool = False
    timestamp_quality: bool = False

    @property
    def raw_value(self) -> int:
        """Return the raw 8-bit bitmask value."""
        value = self.validity | self.source
        if self.normal_value:
            value |= QUALITY_NORMAL_VALUE
        if self.timestamp_quality:
            value |= QUALITY_TIMESTAMP_QUALITY
        return value

    @classmethod
    def from_raw(cls, value: int) -> 'DataFlags':
        """Create DataFlags from raw 8-bit bitmask."""
        return cls(
            validity=value & 0x0F,  # bits 0-3
            source=value & 0x30,     # bits 4-5
            normal_value=bool(value & QUALITY_NORMAL_VALUE),
            timestamp_quality=bool(value & QUALITY_TIMESTAMP_QUALITY),
        )

    @property
    def is_valid(self) -> bool:
        """Check if data quality indicates valid data."""
        return self.validity == QUALITY_VALIDITY_VALID

    @property
    def is_suspect(self) -> bool:
        """Check if data quality indicates suspect data."""
        return self.validity == QUALITY_VALIDITY_SUSPECT

    @property
    def is_held(self) -> bool:
        """Check if data quality indicates held data."""
        return self.validity == QUALITY_VALIDITY_HELD

    @property
    def is_not_valid(self) -> bool:
        """Check if data quality indicates not valid data."""
        return self.validity == QUALITY_VALIDITY_NOT_VALID

    @property
    def validity_name(self) -> str:
        """Return human-readable validity name."""
        validity_names = {
            QUALITY_VALIDITY_VALID: "VALID",
            QUALITY_VALIDITY_SUSPECT: "SUSPECT",
            QUALITY_VALIDITY_HELD: "HELD",
            QUALITY_VALIDITY_NOT_VALID: "NOT_VALID",
        }
        return validity_names.get(self.validity, "UNKNOWN")

    @property
    def source_name(self) -> str:
        """Return human-readable source name."""
        source_names = {
            QUALITY_SOURCE_TELEMETERED: "TELEMETERED",
            QUALITY_SOURCE_ENTERED: "ENTERED",
            QUALITY_SOURCE_CALCULATED: "CALCULATED",
            QUALITY_SOURCE_ESTIMATED: "ESTIMATED",
        }
        return source_names.get(self.source, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "validity": self.validity_name,
            "source": self.source_name,
            "normal_value": self.normal_value,
            "timestamp_quality": self.timestamp_quality,
            "is_valid": self.is_valid,
            "raw": self.raw_value,
        }

    def __str__(self) -> str:
        return f"DataFlags({self.validity_name}, {self.source_name})"


@dataclass
class TransferSetConditions:
    """
    TASE.2 Transfer Set Conditions (DSConditions).

    Defines when data should be reported from server to client.
    """
    interval_timeout: bool = False
    object_change: bool = False
    operator_request: bool = False
    external_event: bool = False

    @property
    def raw_value(self) -> int:
        """Return the raw bitmask value."""
        value = 0
        if self.interval_timeout:
            value |= DS_CONDITIONS_INTERVAL
        if self.object_change:
            value |= DS_CONDITIONS_CHANGE
        if self.operator_request:
            value |= DS_CONDITIONS_OPERATOR_REQUEST
        if self.external_event:
            value |= DS_CONDITIONS_EXTERNAL_EVENT
        return value

    @classmethod
    def from_raw(cls, value: int) -> 'TransferSetConditions':
        """Create TransferSetConditions from raw bitmask."""
        return cls(
            interval_timeout=bool(value & DS_CONDITIONS_INTERVAL),
            object_change=bool(value & DS_CONDITIONS_CHANGE),
            operator_request=bool(value & DS_CONDITIONS_OPERATOR_REQUEST),
            external_event=bool(value & DS_CONDITIONS_EXTERNAL_EVENT),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "interval_timeout": self.interval_timeout,
            "object_change": self.object_change,
            "operator_request": self.operator_request,
            "external_event": self.external_event,
            "raw": self.raw_value,
        }


@dataclass
class ProtectionEvent:
    """
    TASE.2 Protection Event.

    Represents a protection equipment event with flags, timing, and timestamp.
    """
    event_flags: int = 0
    operating_time: int = 0
    timestamp: Optional[datetime] = None
    elapsed_time_valid: bool = True
    blocked: bool = False
    substituted: bool = False
    topical: bool = True
    event_valid: bool = True

    @property
    def has_general_fault(self) -> bool:
        """Check if general fault flag is set."""
        return bool(self.event_flags & 1)

    @property
    def has_phase_a_fault(self) -> bool:
        """Check if phase A fault flag is set."""
        return bool(self.event_flags & 2)

    @property
    def has_phase_b_fault(self) -> bool:
        """Check if phase B fault flag is set."""
        return bool(self.event_flags & 4)

    @property
    def has_phase_c_fault(self) -> bool:
        """Check if phase C fault flag is set."""
        return bool(self.event_flags & 8)

    @property
    def has_earth_fault(self) -> bool:
        """Check if earth fault flag is set."""
        return bool(self.event_flags & 16)

    @property
    def has_reverse_fault(self) -> bool:
        """Check if reverse fault flag is set."""
        return bool(self.event_flags & 32)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "event_flags": self.event_flags,
            "operating_time": self.operating_time,
            "general": self.has_general_fault,
            "phase_a": self.has_phase_a_fault,
            "phase_b": self.has_phase_b_fault,
            "phase_c": self.has_phase_c_fault,
            "earth": self.has_earth_fault,
            "reverse": self.has_reverse_fault,
            "event_valid": self.event_valid,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class Domain:
    """
    TASE.2 Domain (VCC or ICC).

    In TASE.2, objects are organized within Virtual Control Centers (VCC)
    or Intercontrol Centers (ICC). VCC has global scope while ICC has
    domain-limited scope.
    """
    name: str
    is_vcc: bool = False
    variables: List[str] = field(default_factory=list)
    data_sets: List[str] = field(default_factory=list)

    @property
    def domain_type(self) -> str:
        """Return domain type string."""
        return DOMAIN_VCC if self.is_vcc else "ICC"

    @property
    def variable_count(self) -> int:
        """Return number of variables."""
        return len(self.variables)

    @property
    def data_set_count(self) -> int:
        """Return number of data sets."""
        return len(self.data_sets)


@dataclass
class Variable:
    """
    TASE.2 Variable definition.

    Represents a data point variable within a domain.
    """
    name: str
    domain: str
    point_type: Optional[int] = None
    readable: bool = True
    writable: bool = False

    @property
    def type_name(self) -> str:
        """Return human-readable type name."""
        if self.point_type and self.point_type in POINT_TYPES:
            return POINT_TYPES[self.point_type][0]
        return "UNKNOWN"

    @property
    def full_name(self) -> str:
        """Return fully qualified name (domain/variable)."""
        return f"{self.domain}/{self.name}"


@dataclass
class PointValue:
    """
    TASE.2 Data Point Value with quality and timestamp.

    Represents the current value of a data point including
    quality indicators and optional timestamp.
    """
    value: Any
    quality: str = QUALITY_GOOD  # Legacy string quality (backward compat)
    timestamp: Optional[datetime] = None
    point_type: Optional[int] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    flags: Optional[DataFlags] = None  # New: proper quality flags
    cov_counter: Optional[int] = None  # New: for Extended types

    @property
    def is_valid(self) -> bool:
        """Check if value quality is good."""
        if self.flags is not None:
            return self.flags.is_valid
        return self.quality == QUALITY_GOOD

    @property
    def type_name(self) -> str:
        """Return human-readable type name."""
        if self.point_type and self.point_type in POINT_TYPES:
            return POINT_TYPES[self.point_type][0]
        return "UNKNOWN"

    @property
    def quality_flags(self) -> DataFlags:
        """Return DataFlags (create from legacy quality if needed)."""
        if self.flags is not None:
            return self.flags
        # Convert legacy string quality to DataFlags
        if self.quality == QUALITY_GOOD:
            return DataFlags(validity=QUALITY_VALIDITY_VALID)
        else:
            return DataFlags(validity=QUALITY_VALIDITY_NOT_VALID)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "value": self.value,
        }
        # Include quality in appropriate format
        if self.flags is not None:
            result["flags"] = self.flags.to_dict()
            result["quality"] = self.flags.validity_name
        else:
            result["quality"] = self.quality
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.point_type:
            result["point_type"] = self.type_name
        if self.name:
            result["name"] = self.name
        if self.domain:
            result["domain"] = self.domain
        if self.cov_counter is not None:
            result["cov_counter"] = self.cov_counter
        return result


@dataclass
class ControlPoint:
    """
    TASE.2 Control Point (Block 5).

    Represents a controllable device or setpoint.
    """
    name: str
    domain: str
    control_type: Optional[int] = None
    checkback_name: Optional[str] = None
    tag_value: Optional[int] = None

    @property
    def type_name(self) -> str:
        """Return human-readable control type name."""
        if self.control_type and self.control_type in CONTROL_TYPES:
            return CONTROL_TYPES[self.control_type][0]
        return "UNKNOWN"

    @property
    def full_name(self) -> str:
        """Return fully qualified name (domain/control)."""
        return f"{self.domain}/{self.name}"


@dataclass
class DataSet:
    """
    TASE.2 Data Set (Named Variable List).

    A collection of data points that can be read or transferred together.
    """
    name: str
    domain: str
    members: List[str] = field(default_factory=list)
    deletable: bool = False

    @property
    def member_count(self) -> int:
        """Return number of members."""
        return len(self.members)

    @property
    def full_name(self) -> str:
        """Return fully qualified name (domain/dataset)."""
        return f"{self.domain}/{self.name}"


@dataclass
class TransferSet:
    """
    TASE.2 Data Set Transfer Set (Block 2).

    Defines how and when data set values are reported to the client.
    """
    name: str
    domain: str
    data_set: str = ""
    interval: int = 0  # Interval in seconds
    rbe_enabled: bool = False  # Report-by-exception
    buffer_time: int = 0
    integrity_time: int = 0
    start_time: Optional[datetime] = None
    conditions: Optional[TransferSetConditions] = None  # DSConditions bitmask

    @property
    def is_periodic(self) -> bool:
        """Check if transfer set is periodic."""
        return self.interval > 0

    @property
    def full_name(self) -> str:
        """Return fully qualified name (domain/transferset)."""
        return f"{self.domain}/{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "name": self.name,
            "domain": self.domain,
            "data_set": self.data_set,
            "interval": self.interval,
            "rbe_enabled": self.rbe_enabled,
            "buffer_time": self.buffer_time,
            "integrity_time": self.integrity_time,
        }
        if self.conditions:
            result["conditions"] = self.conditions.to_dict()
        if self.start_time:
            result["start_time"] = self.start_time.isoformat()
        return result


@dataclass
class BilateralTable:
    """
    TASE.2 Bilateral Table.

    Defines the agreement between two TASE.2 implementations including
    which objects can be accessed and what operations are permitted.
    """
    table_id: str
    version: int = 1
    tase2_version: str = "2000-8"
    ap_title: Optional[str] = None
    supported_blocks: List[int] = field(default_factory=list)

    def supports_block(self, block: int) -> bool:
        """Check if a conformance block is supported."""
        return block in self.supported_blocks

    @property
    def supported_block_names(self) -> List[str]:
        """Return list of supported block names."""
        return [
            CONFORMANCE_BLOCKS[b][0]
            for b in self.supported_blocks
            if b in CONFORMANCE_BLOCKS
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "table_id": self.table_id,
            "version": self.version,
            "tase2_version": self.tase2_version,
            "ap_title": self.ap_title,
            "supported_blocks": self.supported_block_names,
        }


@dataclass
class ServerInfo:
    """
    TASE.2 Server Information.

    Contains information about the connected TASE.2 server.
    """
    vendor: Optional[str] = None
    model: Optional[str] = None
    revision: Optional[str] = None
    bilateral_table_count: int = 0
    bilateral_table_id: Optional[str] = None
    conformance_blocks: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        if self.vendor:
            result["vendor"] = self.vendor
        if self.model:
            result["model"] = self.model
        if self.revision:
            result["revision"] = self.revision
        result["bilateral_table_count"] = self.bilateral_table_count
        if self.bilateral_table_id:
            result["bilateral_table_id"] = self.bilateral_table_id
        if self.conformance_blocks:
            result["conformance_blocks"] = [
                CONFORMANCE_BLOCKS[b][0]
                for b in self.conformance_blocks
                if b in CONFORMANCE_BLOCKS
            ]
        return result


@dataclass
class Association:
    """
    TASE.2 Association.

    Represents the connection agreement between client and server.
    """
    association_id: str
    ae_title: Optional[str] = None
    local_ap_title: Optional[str] = None
    remote_ap_title: Optional[str] = None
    supported_features: Optional[str] = None

#!/usr/bin/env python3
"""
TASE.2/ICCP Data Types

Data classes for TASE.2 protocol objects including domains, variables,
data points, transfer sets, and bilateral tables.
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
    DS_CONDITIONS_INTEGRITY,
    DS_CONDITIONS_CHANGE,
    DS_CONDITIONS_OPERATOR_REQUEST,
    DS_CONDITIONS_EXTERNAL_EVENT,
)


@dataclass
class DataFlags:
    """TASE.2 Data Flags (Quality) - 8-bit bitmask."""
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
            validity=value & 0x0C,
            source=value & 0x30,
            normal_value=bool(value & QUALITY_NORMAL_VALUE),
            timestamp_quality=bool(value & QUALITY_TIMESTAMP_QUALITY),
        )

    @property
    def is_valid(self) -> bool:
        return self.validity == QUALITY_VALIDITY_VALID

    @property
    def is_suspect(self) -> bool:
        return self.validity == QUALITY_VALIDITY_SUSPECT

    @property
    def is_held(self) -> bool:
        return self.validity == QUALITY_VALIDITY_HELD

    @property
    def is_not_valid(self) -> bool:
        return self.validity == QUALITY_VALIDITY_NOT_VALID

    @property
    def validity_name(self) -> str:
        validity_names = {
            QUALITY_VALIDITY_VALID: "VALID",
            QUALITY_VALIDITY_SUSPECT: "SUSPECT",
            QUALITY_VALIDITY_HELD: "HELD",
            QUALITY_VALIDITY_NOT_VALID: "NOT_VALID",
        }
        return validity_names.get(self.validity, "UNKNOWN")

    @property
    def source_name(self) -> str:
        source_names = {
            QUALITY_SOURCE_TELEMETERED: "TELEMETERED",
            QUALITY_SOURCE_ENTERED: "ENTERED",
            QUALITY_SOURCE_CALCULATED: "CALCULATED",
            QUALITY_SOURCE_ESTIMATED: "ESTIMATED",
        }
        return source_names.get(self.source, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
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
    """TASE.2 Transfer Set Conditions (DSConditions) bitmask."""
    interval_timeout: bool = False
    integrity_timeout: bool = False
    object_change: bool = False
    operator_request: bool = False
    external_event: bool = False

    @property
    def raw_value(self) -> int:
        value = 0
        if self.interval_timeout:
            value |= DS_CONDITIONS_INTERVAL
        if self.integrity_timeout:
            value |= DS_CONDITIONS_INTEGRITY
        if self.object_change:
            value |= DS_CONDITIONS_CHANGE
        if self.operator_request:
            value |= DS_CONDITIONS_OPERATOR_REQUEST
        if self.external_event:
            value |= DS_CONDITIONS_EXTERNAL_EVENT
        return value

    @classmethod
    def from_raw(cls, value: int) -> 'TransferSetConditions':
        return cls(
            interval_timeout=bool(value & DS_CONDITIONS_INTERVAL),
            integrity_timeout=bool(value & DS_CONDITIONS_INTEGRITY),
            object_change=bool(value & DS_CONDITIONS_CHANGE),
            operator_request=bool(value & DS_CONDITIONS_OPERATOR_REQUEST),
            external_event=bool(value & DS_CONDITIONS_EXTERNAL_EVENT),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interval_timeout": self.interval_timeout,
            "integrity_timeout": self.integrity_timeout,
            "object_change": self.object_change,
            "operator_request": self.operator_request,
            "external_event": self.external_event,
            "raw": self.raw_value,
        }


@dataclass
class ProtectionEvent:
    """TASE.2 Protection Event with flags, timing, and timestamp."""
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
        return bool(self.event_flags & 1)

    @property
    def has_phase_a_fault(self) -> bool:
        return bool(self.event_flags & 2)

    @property
    def has_phase_b_fault(self) -> bool:
        return bool(self.event_flags & 4)

    @property
    def has_phase_c_fault(self) -> bool:
        return bool(self.event_flags & 8)

    @property
    def has_earth_fault(self) -> bool:
        return bool(self.event_flags & 16)

    @property
    def has_reverse_fault(self) -> bool:
        return bool(self.event_flags & 32)

    def to_dict(self) -> Dict[str, Any]:
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
    """TASE.2 Domain (VCC or ICC)."""
    name: str
    is_vcc: bool = False
    variables: List[str] = field(default_factory=list)
    data_sets: List[str] = field(default_factory=list)

    @property
    def domain_type(self) -> str:
        return DOMAIN_VCC if self.is_vcc else "ICC"

    @property
    def variable_count(self) -> int:
        return len(self.variables)

    @property
    def data_set_count(self) -> int:
        return len(self.data_sets)


@dataclass
class Variable:
    """TASE.2 Variable definition within a domain."""
    name: str
    domain: str
    point_type: Optional[int] = None
    readable: bool = True
    writable: bool = False

    @property
    def type_name(self) -> str:
        if self.point_type and self.point_type in POINT_TYPES:
            return POINT_TYPES[self.point_type][0]
        return "UNKNOWN"

    @property
    def full_name(self) -> str:
        return f"{self.domain}/{self.name}"


@dataclass
class PointValue:
    """TASE.2 Data Point Value with quality and timestamp."""
    value: Any
    quality: str = QUALITY_GOOD
    timestamp: Optional[datetime] = None
    point_type: Optional[int] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    flags: Optional[DataFlags] = None
    cov_counter: Optional[int] = None

    @property
    def is_valid(self) -> bool:
        if self.flags is not None:
            return self.flags.is_valid
        return self.quality == QUALITY_GOOD

    @property
    def type_name(self) -> str:
        if self.point_type and self.point_type in POINT_TYPES:
            return POINT_TYPES[self.point_type][0]
        return "UNKNOWN"

    @property
    def quality_flags(self) -> DataFlags:
        """Return DataFlags (create from legacy quality if needed)."""
        if self.flags is not None:
            return self.flags
        if self.quality == QUALITY_GOOD:
            return DataFlags(validity=QUALITY_VALIDITY_VALID)
        else:
            return DataFlags(validity=QUALITY_VALIDITY_NOT_VALID)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "value": self.value,
        }
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
    """TASE.2 Control Point (Block 5)."""
    name: str
    domain: str
    control_type: Optional[int] = None
    checkback_name: Optional[str] = None
    tag_value: Optional[int] = None

    @property
    def type_name(self) -> str:
        if self.control_type and self.control_type in CONTROL_TYPES:
            return CONTROL_TYPES[self.control_type][0]
        return "UNKNOWN"

    @property
    def full_name(self) -> str:
        return f"{self.domain}/{self.name}"


@dataclass
class DataSet:
    """TASE.2 Data Set (Named Variable List)."""
    name: str
    domain: str
    members: List[str] = field(default_factory=list)
    deletable: bool = False

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def full_name(self) -> str:
        return f"{self.domain}/{self.name}"


@dataclass
class TransferSet:
    """TASE.2 Data Set Transfer Set (Block 2)."""
    name: str
    domain: str
    data_set: str = ""
    interval: int = 0
    rbe_enabled: bool = False
    buffer_time: int = 0
    integrity_time: int = 0
    start_time: Optional[datetime] = None
    conditions: Optional[TransferSetConditions] = None

    @property
    def is_periodic(self) -> bool:
        return self.interval > 0

    @property
    def full_name(self) -> str:
        return f"{self.domain}/{self.name}"

    def to_dict(self) -> Dict[str, Any]:
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
    """TASE.2 Bilateral Table defining access agreements."""
    table_id: str
    version: int = 1
    tase2_version: str = "2000-8"
    ap_title: Optional[str] = None
    supported_blocks: List[int] = field(default_factory=list)

    def supports_block(self, block: int) -> bool:
        return block in self.supported_blocks

    @property
    def supported_block_names(self) -> List[str]:
        return [
            CONFORMANCE_BLOCKS[b][0]
            for b in self.supported_blocks
            if b in CONFORMANCE_BLOCKS
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "version": self.version,
            "tase2_version": self.tase2_version,
            "ap_title": self.ap_title,
            "supported_blocks": self.supported_block_names,
        }


@dataclass
class ServerInfo:
    """TASE.2 Server Information."""
    vendor: Optional[str] = None
    model: Optional[str] = None
    revision: Optional[str] = None
    bilateral_table_count: int = 0
    bilateral_table_id: Optional[str] = None
    conformance_blocks: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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
class DSTransferSetConfig:
    """Configuration for a DS Transfer Set."""
    data_set_name: Optional[str] = None
    start_time: Optional[int] = None
    interval: Optional[int] = None
    tle: Optional[int] = None
    buffer_time: Optional[int] = None
    integrity_check: Optional[int] = None
    ds_conditions: Optional[TransferSetConditions] = None
    block_data: Optional[bool] = None
    critical: Optional[bool] = None
    rbe: Optional[bool] = None
    all_changes_reported: Optional[bool] = None
    status: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.data_set_name is not None:
            result["data_set_name"] = self.data_set_name
        if self.interval is not None:
            result["interval"] = self.interval
        if self.integrity_check is not None:
            result["integrity_check"] = self.integrity_check
        if self.buffer_time is not None:
            result["buffer_time"] = self.buffer_time
        if self.rbe is not None:
            result["rbe"] = self.rbe
        if self.ds_conditions is not None:
            result["ds_conditions"] = self.ds_conditions.to_dict()
        if self.critical is not None:
            result["critical"] = self.critical
        if self.block_data is not None:
            result["block_data"] = self.block_data
        return result


@dataclass
class TransferReport:
    """A received TASE.2 InformationReport (transfer report)."""
    domain: str
    transfer_set_name: str
    values: List['PointValue'] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    conditions_detected: Optional[TransferSetConditions] = None
    sequence_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "domain": self.domain,
            "transfer_set_name": self.transfer_set_name,
            "values": [v.to_dict() for v in self.values],
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.conditions_detected:
            result["conditions_detected"] = self.conditions_detected.to_dict()
        if self.sequence_number is not None:
            result["sequence_number"] = self.sequence_number
        return result


@dataclass
class SBOState:
    """Select-Before-Operate state for a control device."""
    select_time: float = 0.0
    domain: str = ""
    device: str = ""
    checkback_id: Optional[Any] = None


@dataclass
class InformationMessage:
    """TASE.2 Information Message (Block 4)."""
    info_ref: int = 0
    local_ref: int = 0
    msg_id: int = 0
    content: bytes = b""
    timestamp: Optional[datetime] = None

    @property
    def text(self) -> str:
        """Return content decoded as UTF-8 text."""
        if isinstance(self.content, str):
            return self.content
        try:
            return self.content.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return repr(self.content)

    @property
    def size(self) -> int:
        if isinstance(self.content, (bytes, bytearray)):
            return len(self.content)
        if isinstance(self.content, str):
            return len(self.content.encode("utf-8"))
        return 0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "info_ref": self.info_ref,
            "local_ref": self.local_ref,
            "msg_id": self.msg_id,
            "size": self.size,
        }
        try:
            if isinstance(self.content, str):
                result["text"] = self.content
            elif isinstance(self.content, bytes):
                result["text"] = self.content.decode("utf-8")
        except UnicodeDecodeError:
            result["binary"] = True
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class IMTransferSetConfig:
    """TASE.2 IM Transfer Set Configuration (Block 4).

    When enabled, the server pushes information messages to the client.
    """
    enabled: bool = False
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "enabled": self.enabled,
        }
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class InformationBuffer:
    """TASE.2 Information Buffer (Block 4).

    Server-side storage for information messages.
    """
    name: str
    domain: str
    max_size: int = 0
    entry_count: int = 0
    messages: List['InformationMessage'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "max_size": self.max_size,
            "entry_count": self.entry_count,
            "messages": [m.to_dict() for m in self.messages],
        }


@dataclass
class TagState:
    """TASE.2 Tag State (Block 5).

    Tag values:
    - 0: No tag, all operations permitted
    - 1: Open and close inhibit (fully blocked)
    - 2: Close only inhibit
    - 3: Invalid/unknown
    """
    tag_value: int = 0
    reason: str = ""
    device: str = ""
    domain: str = ""
    tag_state: int = 0  # 0=IDLE, 1=ARMED

    @property
    def is_tagged(self) -> bool:
        return self.tag_value != 0

    @property
    def is_armed(self) -> bool:
        return self.tag_state == 1

    @property
    def is_idle(self) -> bool:
        return self.tag_state == 0

    @property
    def tag_name(self) -> str:
        tag_names = {
            0: "NO_TAG",
            1: "OPEN_AND_CLOSE_INHIBIT",
            2: "CLOSE_ONLY_INHIBIT",
            3: "INVALID",
        }
        return tag_names.get(self.tag_value, f"UNKNOWN({self.tag_value})")

    @property
    def state_name(self) -> str:
        return "ARMED" if self.tag_state == 1 else "IDLE"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "tag_value": self.tag_value,
            "tag_name": self.tag_name,
            "is_tagged": self.is_tagged,
            "tag_state": self.state_name,
        }
        if self.reason:
            result["reason"] = self.reason
        if self.device:
            result["device"] = self.device
        if self.domain:
            result["domain"] = self.domain
        return result


@dataclass
class ClientStatistics:
    """TASE.2 Client Statistics and Diagnostics."""
    total_reads: int = 0
    total_writes: int = 0
    total_errors: int = 0
    reports_received: int = 0
    control_operations: int = 0
    connect_time: Optional[datetime] = None
    disconnect_time: Optional[datetime] = None

    @property
    def uptime_seconds(self) -> float:
        if self.connect_time is None:
            return 0.0
        end = self.disconnect_time or datetime.now()
        return (end - self.connect_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "total_reads": self.total_reads,
            "total_writes": self.total_writes,
            "total_errors": self.total_errors,
            "reports_received": self.reports_received,
            "control_operations": self.control_operations,
            "uptime_seconds": round(self.uptime_seconds, 2),
        }
        if self.connect_time:
            result["connect_time"] = self.connect_time.isoformat()
        return result


@dataclass
class ServerAddress:
    """TASE.2 Server Address for failover configuration."""
    host: str
    port: int = 102
    priority: str = "primary"

    @property
    def is_primary(self) -> bool:
        return self.priority == "primary"

    @property
    def is_backup(self) -> bool:
        return self.priority == "backup"

    def __str__(self) -> str:
        return f"{self.host}:{self.port} ({self.priority})"


@dataclass
class Association:
    """TASE.2 Association."""
    association_id: str
    ae_title: Optional[str] = None
    local_ap_title: Optional[str] = None
    remote_ap_title: Optional[str] = None
    supported_features: Optional[str] = None

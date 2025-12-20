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
)


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
    quality: str = QUALITY_GOOD
    timestamp: Optional[datetime] = None
    point_type: Optional[int] = None
    name: Optional[str] = None
    domain: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if value quality is good."""
        return self.quality == QUALITY_GOOD

    @property
    def type_name(self) -> str:
        """Return human-readable type name."""
        if self.point_type and self.point_type in POINT_TYPES:
            return POINT_TYPES[self.point_type][0]
        return "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "value": self.value,
            "quality": self.quality,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.point_type:
            result["point_type"] = self.type_name
        if self.name:
            result["name"] = self.name
        if self.domain:
            result["domain"] = self.domain
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
    data_set: str
    interval: int = 0  # Interval in seconds
    rbe_enabled: bool = False  # Report-by-exception
    buffer_time: int = 0
    integrity_time: int = 0
    start_time: Optional[datetime] = None

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
        return {
            "name": self.name,
            "domain": self.domain,
            "data_set": self.data_set,
            "interval": self.interval,
            "rbe_enabled": self.rbe_enabled,
            "buffer_time": self.buffer_time,
            "integrity_time": self.integrity_time,
        }


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

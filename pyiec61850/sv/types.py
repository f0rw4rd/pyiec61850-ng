#!/usr/bin/env python3
"""
Sampled Values Data Types

Data classes for IEC 61850-9-2 Sampled Values protocol.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SVMessage:
    """Received Sampled Values message data."""
    sv_id: str = ""
    app_id: int = 0
    smp_cnt: int = 0
    conf_rev: int = 0
    smp_synch: int = 0
    smp_rate: int = 0
    smp_mod: int = 0
    timestamp: Optional[datetime] = None
    values: List[float] = field(default_factory=list)
    num_asdu: int = 1

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "sv_id": self.sv_id,
            "app_id": self.app_id,
            "smp_cnt": self.smp_cnt,
            "conf_rev": self.conf_rev,
            "smp_synch": self.smp_synch,
            "smp_rate": self.smp_rate,
            "num_asdu": self.num_asdu,
            "value_count": len(self.values),
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class SVPublisherConfig:
    """Configuration for SV publisher."""
    interface: str = "eth0"
    sv_id: str = ""
    app_id: int = 0x4000
    conf_rev: int = 1
    smp_rate: int = 4000
    dst_mac: bytes = b"\x01\x0c\xcd\x04\x00\x00"
    vlan_id: int = 0
    vlan_priority: int = 4
    num_asdu: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface": self.interface,
            "sv_id": self.sv_id,
            "app_id": self.app_id,
            "conf_rev": self.conf_rev,
            "smp_rate": self.smp_rate,
            "vlan_id": self.vlan_id,
            "vlan_priority": self.vlan_priority,
            "num_asdu": self.num_asdu,
        }


@dataclass
class SVSubscriberConfig:
    """Configuration for SV subscriber."""
    interface: str = "eth0"
    sv_id: Optional[str] = None
    app_id: Optional[int] = None
    dst_mac: Optional[bytes] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"interface": self.interface}
        if self.sv_id is not None:
            result["sv_id"] = self.sv_id
        if self.app_id is not None:
            result["app_id"] = self.app_id
        return result

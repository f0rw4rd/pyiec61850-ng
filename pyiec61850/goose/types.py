#!/usr/bin/env python3
"""
GOOSE Data Types

Data classes for GOOSE protocol messages and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class GooseMessage:
    """Received GOOSE message data."""
    go_cb_ref: str = ""
    go_id: str = ""
    data_set: str = ""
    app_id: int = 0
    conf_rev: int = 0
    st_num: int = 0
    sq_num: int = 0
    needs_commissioning: bool = False
    is_valid: bool = True
    time_allowed_to_live: int = 0
    timestamp: Optional[datetime] = None
    values: List[Any] = field(default_factory=list)
    num_data_set_entries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "go_cb_ref": self.go_cb_ref,
            "go_id": self.go_id,
            "data_set": self.data_set,
            "app_id": self.app_id,
            "conf_rev": self.conf_rev,
            "st_num": self.st_num,
            "sq_num": self.sq_num,
            "is_valid": self.is_valid,
            "needs_commissioning": self.needs_commissioning,
            "time_allowed_to_live": self.time_allowed_to_live,
            "num_data_set_entries": self.num_data_set_entries,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class GoosePublisherConfig:
    """Configuration for GOOSE publisher."""
    interface: str = "eth0"
    go_cb_ref: str = ""
    go_id: str = ""
    data_set: str = ""
    app_id: int = 0x1000
    conf_rev: int = 1
    dst_mac: bytes = b"\x01\x0c\xcd\x01\x00\x00"
    vlan_id: int = 0
    vlan_priority: int = 4
    time_allowed_to_live: int = 2000
    needs_commissioning: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface": self.interface,
            "go_cb_ref": self.go_cb_ref,
            "go_id": self.go_id,
            "data_set": self.data_set,
            "app_id": self.app_id,
            "conf_rev": self.conf_rev,
            "vlan_id": self.vlan_id,
            "vlan_priority": self.vlan_priority,
            "time_allowed_to_live": self.time_allowed_to_live,
        }


@dataclass
class GooseSubscriberConfig:
    """Configuration for GOOSE subscriber."""
    interface: str = "eth0"
    go_cb_ref: str = ""
    app_id: Optional[int] = None
    dst_mac: Optional[bytes] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "interface": self.interface,
            "go_cb_ref": self.go_cb_ref,
        }
        if self.app_id is not None:
            result["app_id"] = self.app_id
        if self.dst_mac is not None:
            result["dst_mac"] = self.dst_mac.hex()
        return result

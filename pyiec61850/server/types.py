#!/usr/bin/env python3
"""
IEC 61850 Server Data Types

Data classes for server configuration and runtime data.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ServerConfig:
    """IEC 61850 Server configuration."""
    port: int = 102
    max_connections: int = 5
    file_service_base_path: Optional[str] = None
    edition: int = 2
    enable_dynamic_datasets: bool = True
    enable_file_service: bool = False
    enable_goose_publishing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "max_connections": self.max_connections,
            "edition": self.edition,
            "enable_dynamic_datasets": self.enable_dynamic_datasets,
            "enable_file_service": self.enable_file_service,
            "enable_goose_publishing": self.enable_goose_publishing,
        }


@dataclass
class ClientConnection:
    """Information about a connected client."""
    client_id: int = 0
    peer_address: str = ""
    authenticated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "peer_address": self.peer_address,
            "authenticated": self.authenticated,
        }


@dataclass
class DataAttributeInfo:
    """Information about a data attribute in the model."""
    reference: str = ""
    fc: str = ""
    type_name: str = ""
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "reference": self.reference,
            "fc": self.fc,
        }
        if self.type_name:
            result["type"] = self.type_name
        if self.value is not None:
            result["value"] = self.value
        return result


# Control handler result constants
CONTROL_ACCEPTED = 0
CONTROL_HARDWARE_FAULT = 1
CONTROL_TEMPORARILY_UNAVAILABLE = 2
CONTROL_OBJECT_ACCESS_DENIED = 3
CONTROL_OBJECT_UNDEFINED = 4

# Check handler result constants
CHECK_OK = 0
CHECK_FAILED = 1

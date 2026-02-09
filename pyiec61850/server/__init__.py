#!/usr/bin/env python3
"""
IEC 61850 Server Support for pyiec61850-ng

Provides IEC 61850 MMS server functionality including data model
management, control handlers, and GOOSE publishing.

Example:
    from pyiec61850.server import IedServer, ServerConfig

    config = ServerConfig(port=102, max_connections=10)

    with IedServer("model.cfg", config) as server:
        server.start(102)
        server.update_float("myLD/MMXU1.TotW.mag.f", 1234.5)
"""

__version__ = "0.1.0"
__author__ = "f0rw4rd"

from .exceptions import (
    AlreadyRunningError,
    ConfigurationError,
    ControlHandlerError,
    LibraryNotFoundError,
    ModelError,
    NotRunningError,
    ServerError,
    UpdateError,
)
from .server import IedServer
from .types import (
    CHECK_FAILED,
    CHECK_OK,
    CONTROL_ACCEPTED,
    CONTROL_HARDWARE_FAULT,
    CONTROL_OBJECT_ACCESS_DENIED,
    CONTROL_OBJECT_UNDEFINED,
    CONTROL_TEMPORARILY_UNAVAILABLE,
    ClientConnection,
    DataAttributeInfo,
    ServerConfig,
)

__all__ = [
    "__version__",
    "__author__",
    # Classes
    "IedServer",
    # Types
    "ServerConfig",
    "ClientConnection",
    "DataAttributeInfo",
    # Constants
    "CONTROL_ACCEPTED",
    "CONTROL_HARDWARE_FAULT",
    "CONTROL_TEMPORARILY_UNAVAILABLE",
    "CONTROL_OBJECT_ACCESS_DENIED",
    "CONTROL_OBJECT_UNDEFINED",
    "CHECK_OK",
    "CHECK_FAILED",
    # Exceptions
    "ServerError",
    "LibraryNotFoundError",
    "ModelError",
    "ConfigurationError",
    "NotRunningError",
    "AlreadyRunningError",
    "UpdateError",
    "ControlHandlerError",
]

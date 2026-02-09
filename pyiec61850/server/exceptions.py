#!/usr/bin/env python3
"""
IEC 61850 Server Exceptions

Exception hierarchy for IEC 61850 server operations.
"""


class ServerError(Exception):
    """Base exception for all server errors."""

    def __init__(self, message: str = "Server error"):
        self.message = message
        super().__init__(self.message)


class LibraryNotFoundError(ServerError):
    """pyiec61850 library not available."""

    def __init__(self, message: str = "pyiec61850 library not found"):
        super().__init__(message)


class ModelError(ServerError):
    """Error related to the data model."""

    def __init__(self, reason: str = ""):
        message = "Model error"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ConfigurationError(ServerError):
    """Invalid server configuration."""

    def __init__(self, parameter: str = "", reason: str = ""):
        message = "Configuration error"
        if parameter:
            message = f"Invalid configuration: {parameter}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.parameter = parameter


class NotRunningError(ServerError):
    """Operation requires server to be running."""

    def __init__(self, message: str = "Server not running"):
        super().__init__(message)


class AlreadyRunningError(ServerError):
    """Server is already running."""

    def __init__(self, message: str = "Server already running"):
        super().__init__(message)


class UpdateError(ServerError):
    """Error updating a data attribute value."""

    def __init__(self, reference: str = "", reason: str = ""):
        message = "Update error"
        if reference:
            message = f"Failed to update '{reference}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.reference = reference


class ControlHandlerError(ServerError):
    """Error in control handler."""

    def __init__(self, reason: str = ""):
        message = "Control handler error"
        if reason:
            message += f": {reason}"
        super().__init__(message)

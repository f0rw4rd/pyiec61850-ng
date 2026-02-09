#!/usr/bin/env python3
"""
GOOSE Protocol Exceptions

Exception hierarchy for GOOSE publish/subscribe operations.
"""


class GooseError(Exception):
    """Base exception for all GOOSE errors."""

    def __init__(self, message: str = "GOOSE error"):
        self.message = message
        super().__init__(self.message)


class LibraryNotFoundError(GooseError):
    """pyiec61850 library not available."""

    def __init__(self, message: str = "pyiec61850 library not found"):
        super().__init__(message)


class InterfaceError(GooseError):
    """Network interface error."""

    def __init__(self, interface: str = "", reason: str = ""):
        message = "Interface error"
        if interface:
            message = f"Interface '{interface}' error"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.interface = interface


class SubscriptionError(GooseError):
    """Error subscribing to GOOSE messages."""

    def __init__(self, reason: str = ""):
        message = "Subscription failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class PublishError(GooseError):
    """Error publishing GOOSE messages."""

    def __init__(self, reason: str = ""):
        message = "Publish failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ConfigurationError(GooseError):
    """Invalid GOOSE configuration."""

    def __init__(self, parameter: str = "", reason: str = ""):
        message = "Configuration error"
        if parameter:
            message = f"Invalid configuration: {parameter}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.parameter = parameter


class NotStartedError(GooseError):
    """Operation requires subscriber/publisher to be started."""

    def __init__(self, message: str = "Not started"):
        super().__init__(message)


class AlreadyStartedError(GooseError):
    """Subscriber/publisher is already running."""

    def __init__(self, message: str = "Already started"):
        super().__init__(message)

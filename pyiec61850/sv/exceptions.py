#!/usr/bin/env python3
"""
Sampled Values Protocol Exceptions

Exception hierarchy for SV publish/subscribe operations.
"""


class SVError(Exception):
    """Base exception for all Sampled Values errors."""

    def __init__(self, message: str = "Sampled Values error"):
        self.message = message
        super().__init__(self.message)


class LibraryNotFoundError(SVError):
    """pyiec61850 library not available."""

    def __init__(self, message: str = "pyiec61850 library not found"):
        super().__init__(message)


class InterfaceError(SVError):
    """Network interface error."""

    def __init__(self, interface: str = "", reason: str = ""):
        message = "Interface error"
        if interface:
            message = f"Interface '{interface}' error"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.interface = interface


class SubscriptionError(SVError):
    """Error subscribing to SV streams."""

    def __init__(self, reason: str = ""):
        message = "Subscription failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class PublishError(SVError):
    """Error publishing SV data."""

    def __init__(self, reason: str = ""):
        message = "Publish failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ConfigurationError(SVError):
    """Invalid SV configuration."""

    def __init__(self, parameter: str = "", reason: str = ""):
        message = "Configuration error"
        if parameter:
            message = f"Invalid configuration: {parameter}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.parameter = parameter


class NotStartedError(SVError):
    """Operation requires subscriber/publisher to be started."""

    def __init__(self, message: str = "Not started"):
        super().__init__(message)


class AlreadyStartedError(SVError):
    """Subscriber/publisher is already running."""

    def __init__(self, message: str = "Already started"):
        super().__init__(message)

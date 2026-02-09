#!/usr/bin/env python3
"""
GOOSE Protocol Support for pyiec61850-ng

IEC 61850 GOOSE (Generic Object Oriented Substation Event) messaging
for real-time event distribution in substation automation.

Example:
    # Subscribe to GOOSE messages
    from pyiec61850.goose import GooseSubscriber

    def on_message(msg):
        print(f"stNum={msg.st_num}, values={msg.values}")

    with GooseSubscriber("eth0", "myIED/LLN0$GO$gcb01") as sub:
        sub.set_listener(on_message)
        sub.start()

    # Publish GOOSE messages
    from pyiec61850.goose import GoosePublisher

    with GoosePublisher("eth0") as pub:
        pub.set_go_cb_ref("myIED/LLN0$GO$gcb01")
        pub.start()
        pub.publish([True, 42, 3.14])
"""

__version__ = "0.1.0"
__author__ = "f0rw4rd"

from .subscriber import GooseSubscriber
from .publisher import GoosePublisher
from .types import GooseMessage, GoosePublisherConfig, GooseSubscriberConfig
from .exceptions import (
    GooseError,
    LibraryNotFoundError,
    InterfaceError,
    SubscriptionError,
    PublishError,
    ConfigurationError,
    NotStartedError,
    AlreadyStartedError,
)

__all__ = [
    "__version__",
    "__author__",
    # Classes
    "GooseSubscriber",
    "GoosePublisher",
    # Types
    "GooseMessage",
    "GoosePublisherConfig",
    "GooseSubscriberConfig",
    # Exceptions
    "GooseError",
    "LibraryNotFoundError",
    "InterfaceError",
    "SubscriptionError",
    "PublishError",
    "ConfigurationError",
    "NotStartedError",
    "AlreadyStartedError",
]

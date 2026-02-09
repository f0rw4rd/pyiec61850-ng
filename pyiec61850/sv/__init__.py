#!/usr/bin/env python3
"""
Sampled Values (SV) Protocol Support for pyiec61850-ng

IEC 61850-9-2 Sampled Values for real-time measurement data
distribution in substation automation (merging units).

Example:
    # Subscribe to SV streams
    from pyiec61850.sv import SVSubscriber

    with SVSubscriber("eth0") as sub:
        sub.set_app_id(0x4000)
        sub.set_listener(my_callback)
        sub.start()

    # Publish SV data
    from pyiec61850.sv import SVPublisher

    with SVPublisher("eth0") as pub:
        pub.set_sv_id("myMU/LLN0$SV$MSVCB01")
        pub.start()
        pub.publish_samples([1000, 2000, 3000, 4000, 500, 600, 700, 800])
"""

__version__ = "0.1.0"
__author__ = "f0rw4rd"

from .subscriber import SVSubscriber
from .publisher import SVPublisher
from .types import SVMessage, SVPublisherConfig, SVSubscriberConfig
from .exceptions import (
    SVError,
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
    "SVSubscriber",
    "SVPublisher",
    # Types
    "SVMessage",
    "SVPublisherConfig",
    "SVSubscriberConfig",
    # Exceptions
    "SVError",
    "LibraryNotFoundError",
    "InterfaceError",
    "SubscriptionError",
    "PublishError",
    "ConfigurationError",
    "NotStartedError",
    "AlreadyStartedError",
]

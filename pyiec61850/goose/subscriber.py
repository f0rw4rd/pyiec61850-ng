#!/usr/bin/env python3
"""
GOOSE Subscriber

High-level wrapper for receiving GOOSE messages using libiec61850
GooseSubscriber and GooseReceiver APIs.

Example:
    from pyiec61850.goose import GooseSubscriber

    def on_message(msg):
        print(f"Received: stNum={msg.st_num}, values={msg.values}")

    with GooseSubscriber("eth0", "simpleIOGenericIO/LLN0$GO$gcbAnalogValues") as sub:
        sub.set_app_id(0x1000)
        sub.set_listener(on_message)
        sub.start()
        time.sleep(10)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

try:
    import pyiec61850.pyiec61850 as iec61850

    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    AlreadyStartedError,
    ConfigurationError,
    InterfaceError,
    LibraryNotFoundError,
    SubscriptionError,
)
from .types import GooseMessage

logger = logging.getLogger(__name__)


class GooseSubscriber:
    """
    High-level GOOSE subscriber with automatic resource management.

    Wraps libiec61850 GooseSubscriber/GooseReceiver with proper cleanup
    and Python-friendly callback interface.

    Attributes:
        interface: Network interface name
        go_cb_ref: GOOSE Control Block reference
        is_running: Whether the subscriber is actively receiving

    Example:
        sub = GooseSubscriber("eth0", "simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        sub.set_listener(my_callback)
        sub.start()
        # ... receive messages ...
        sub.stop()
    """

    def __init__(self, interface: str, go_cb_ref: str):
        """
        Initialize GOOSE subscriber.

        Args:
            interface: Network interface name (e.g., "eth0")
            go_cb_ref: GOOSE Control Block reference string

        Raises:
            LibraryNotFoundError: If pyiec61850 is not available
            ConfigurationError: If parameters are invalid
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        if not interface:
            raise ConfigurationError("interface", "must not be empty")
        if not go_cb_ref:
            raise ConfigurationError("go_cb_ref", "must not be empty")

        self._interface = interface
        self._go_cb_ref = go_cb_ref
        self._subscriber = None
        self._receiver = None
        self._running = False
        self._listener: Optional[Callable] = None
        self._app_id: Optional[int] = None
        self._dst_mac: Optional[bytes] = None

        # SWIG director handler (prevent GC)
        self._goose_handler = None
        self._goose_subscriber_py = None

    @property
    def interface(self) -> str:
        """Return network interface name."""
        return self._interface

    @property
    def go_cb_ref(self) -> str:
        """Return GOOSE Control Block reference."""
        return self._go_cb_ref

    @property
    def is_running(self) -> bool:
        """Check if subscriber is actively receiving."""
        return self._running

    def set_app_id(self, app_id: int) -> None:
        """
        Set APPID filter for received messages.

        Args:
            app_id: Application identifier (0-65535)

        Raises:
            ConfigurationError: If app_id is out of range
            AlreadyStartedError: If subscriber is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        if not 0 <= app_id <= 0xFFFF:
            raise ConfigurationError("app_id", "must be 0-65535")
        self._app_id = app_id

    def set_dst_mac(self, mac: bytes) -> None:
        """
        Set destination MAC address filter.

        Args:
            mac: 6-byte MAC address

        Raises:
            ConfigurationError: If MAC address is invalid
            AlreadyStartedError: If subscriber is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        if not isinstance(mac, (bytes, bytearray)) or len(mac) != 6:
            raise ConfigurationError("dst_mac", "must be 6 bytes")
        self._dst_mac = bytes(mac)

    def set_listener(self, callback: Callable) -> None:
        """
        Set callback for received GOOSE messages.

        The callback receives a GooseMessage object with all
        decoded fields from the received GOOSE PDU.

        Args:
            callback: Callable that takes a GooseMessage argument

        Raises:
            ConfigurationError: If callback is not callable
        """
        if callback is not None and not callable(callback):
            raise ConfigurationError("callback", "must be callable")
        self._listener = callback

    def start(self) -> None:
        """
        Start receiving GOOSE messages.

        Creates the GooseReceiver, configures the subscriber,
        and begins listening on the network interface.

        Raises:
            AlreadyStartedError: If already running
            SubscriptionError: If subscription setup fails
            InterfaceError: If network interface is not available
        """
        if self._running:
            raise AlreadyStartedError()

        try:
            # Create GOOSE subscriber
            # v1.6.1.0: dataSetValues must not be NULL, use empty array
            empty_ds = iec61850.MmsValue_createEmptyArray(0)
            self._subscriber = iec61850.GooseSubscriber_create(self._go_cb_ref, empty_ds)
            if not self._subscriber:
                raise SubscriptionError("Failed to create GooseSubscriber")

            # Apply filters
            if self._app_id is not None:
                iec61850.GooseSubscriber_setAppId(self._subscriber, self._app_id)

            if self._dst_mac is not None:
                iec61850.GooseSubscriber_setDstMac(self._subscriber, self._dst_mac)

            # Set up the SWIG director handler for callbacks
            if self._listener and hasattr(iec61850, "GooseHandler"):
                self._goose_handler = _PyGooseHandler(self._listener, self._go_cb_ref)
                self._goose_subscriber_py = iec61850.GooseSubscriberForPython()
                self._goose_subscriber_py.setLibiec61850GooseSubscriber(self._subscriber)
                self._goose_subscriber_py.setEventHandler(self._goose_handler)
                self._goose_subscriber_py.subscribe()

            # Create receiver and add subscriber
            self._receiver = iec61850.GooseReceiver_create()
            if not self._receiver:
                raise SubscriptionError("Failed to create GooseReceiver")

            iec61850.GooseReceiver_addSubscriber(self._receiver, self._subscriber)
            iec61850.GooseReceiver_setInterfaceId(self._receiver, self._interface)

            # Start receiving
            iec61850.GooseReceiver_start(self._receiver)

            if not iec61850.GooseReceiver_isRunning(self._receiver):
                raise InterfaceError(
                    self._interface,
                    "GooseReceiver failed to start (check permissions and interface)",
                )

            self._running = True
            logger.info(f"GOOSE subscriber started on {self._interface} for {self._go_cb_ref}")

        except (AlreadyStartedError, SubscriptionError, InterfaceError):
            raise
        except Exception as e:
            self._cleanup()
            raise SubscriptionError(str(e))

    def stop(self) -> None:
        """
        Stop receiving GOOSE messages.

        Stops the receiver and cleans up all resources.
        Safe to call multiple times.
        """
        if not self._running:
            return

        logger.info(f"Stopping GOOSE subscriber on {self._interface}")
        self._running = False

        try:
            if self._receiver:
                iec61850.GooseReceiver_stop(self._receiver)
        except Exception as e:
            logger.warning(f"Error stopping GooseReceiver: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up all native resources.

        Order matters:
        1. Sever the SWIG director link (deleteEventHandler)
        2. Destroy C++ receiver (which also frees the subscriber)
        3. Disable SWIG destructor on handler (thisown=0) since C++ already freed it
        4. Release Python references
        """
        # Sever director link before destroying C++ objects
        if self._goose_subscriber_py:
            try:
                self._goose_subscriber_py.deleteEventHandler()
            except Exception:
                pass

        if self._receiver:
            try:
                iec61850.GooseReceiver_destroy(self._receiver)
            except Exception as e:
                logger.warning(f"Error destroying GooseReceiver: {e}")
        self._receiver = None
        # Subscriber is destroyed with receiver, do not double-free
        self._subscriber = None

        # Prevent SWIG from calling C++ destructor on handler (already freed)
        if self._goose_handler and hasattr(self._goose_handler, "thisown"):
            self._goose_handler.thisown = 0

        self._goose_subscriber_py = None
        self._goose_handler = None
        self._running = False

    def __enter__(self) -> "GooseSubscriber":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - ensures stop and cleanup."""
        self.stop()
        return False

    def __del__(self):
        """Destructor - ensure cleanup."""
        try:
            self.stop()
        except Exception:
            pass


# Dynamically inherit from GooseHandler so SWIG director vtable is correct.
# Without proper inheritance, C++ callback into trigger() segfaults.
_GooseHandlerBase = (
    iec61850.GooseHandler if _HAS_IEC61850 and hasattr(iec61850, "GooseHandler") else object
)


class _PyGooseHandler(_GooseHandlerBase):
    """
    Python-side GOOSE handler (SWIG director subclass).

    Inherits from GooseHandler so the C++ side can call trigger()
    through the SWIG director vtable without segfaulting.
    """

    def __init__(self, callback: Callable, go_cb_ref: str):
        super().__init__()
        self._callback = callback
        self._go_cb_ref = go_cb_ref

    def trigger(self):
        """Called by C++ subscriber when a GOOSE message arrives."""
        try:
            subscriber = self._libiec61850_goose_subscriber

            msg = GooseMessage(
                go_cb_ref=self._go_cb_ref,
            )

            # Extract fields from the subscriber
            try:
                msg.st_num = iec61850.GooseSubscriber_getStNum(subscriber)
            except Exception:
                pass
            try:
                msg.sq_num = iec61850.GooseSubscriber_getSqNum(subscriber)
            except Exception:
                pass
            try:
                msg.is_valid = iec61850.GooseSubscriber_isValid(subscriber)
            except Exception:
                pass
            try:
                msg.conf_rev = iec61850.GooseSubscriber_getConfRev(subscriber)
            except Exception:
                pass
            try:
                msg.needs_commissioning = iec61850.GooseSubscriber_needsCommissioning(subscriber)
            except Exception:
                pass
            try:
                msg.time_allowed_to_live = iec61850.GooseSubscriber_getTimeAllowedToLive(subscriber)
            except Exception:
                pass
            try:
                msg.num_data_set_entries = iec61850.GooseSubscriber_getNumberOfDataSetEntries(
                    subscriber
                )
            except Exception:
                pass
            try:
                msg.go_id = iec61850.GooseSubscriber_getGoId(subscriber)
            except Exception:
                pass
            try:
                msg.data_set = iec61850.GooseSubscriber_getDataSet(subscriber)
            except Exception:
                pass
            try:
                msg.timestamp = datetime.now(tz=timezone.utc)
            except Exception:
                pass

            # Extract data set values
            try:
                data_set_values = iec61850.GooseSubscriber_getDataSetValues(subscriber)
                if data_set_values:
                    count = msg.num_data_set_entries
                    for i in range(count):
                        element = iec61850.MmsValue_getElement(data_set_values, i)
                        if element:
                            msg.values.append(_extract_mms_value(element))
            except Exception as e:
                logger.warning(f"Failed to extract GOOSE values: {e}")

            if self._callback:
                try:
                    self._callback(msg)
                except Exception as e:
                    logger.warning(f"GOOSE listener callback error: {e}")

        except Exception as e:
            logger.warning(f"GOOSE handler error: {e}")


def _extract_mms_value(mms_value) -> Any:
    """Extract a Python value from an MmsValue element."""
    if not _HAS_IEC61850 or not mms_value:
        return None
    try:
        mms_type = iec61850.MmsValue_getType(mms_value)

        if mms_type == getattr(iec61850, "MMS_BOOLEAN", 2):
            return iec61850.MmsValue_getBoolean(mms_value)
        elif mms_type == getattr(iec61850, "MMS_INTEGER", 4):
            return iec61850.MmsValue_toInt32(mms_value)
        elif mms_type == getattr(iec61850, "MMS_UNSIGNED", 5):
            return iec61850.MmsValue_toUint32(mms_value)
        elif mms_type == getattr(iec61850, "MMS_FLOAT", 6):
            return iec61850.MmsValue_toFloat(mms_value)
        elif mms_type == getattr(iec61850, "MMS_BIT_STRING", 3):
            return iec61850.MmsValue_getBitStringAsInteger(mms_value)
        elif mms_type in (
            getattr(iec61850, "MMS_VISIBLE_STRING", 8),
            getattr(iec61850, "MMS_STRING", 13),
        ):
            return iec61850.MmsValue_toString(mms_value)
        else:
            return None
    except Exception:
        return None

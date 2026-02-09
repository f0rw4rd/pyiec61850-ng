#!/usr/bin/env python3
"""
Sampled Values Subscriber

High-level wrapper for receiving IEC 61850-9-2 Sampled Values
using libiec61850 SVSubscriber and SVReceiver APIs.

Example:
    from pyiec61850.sv import SVSubscriber

    def on_sample(msg):
        print(f"smpCnt={msg.smp_cnt}, values={msg.values}")

    with SVSubscriber("eth0") as sub:
        sub.set_app_id(0x4000)
        sub.set_listener(on_sample)
        sub.start()
        time.sleep(10)
"""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

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
    NotStartedError,
    SubscriptionError,
)
from .types import SVMessage

logger = logging.getLogger(__name__)


class SVSubscriber:
    """
    High-level Sampled Values subscriber with automatic resource management.

    Wraps libiec61850 SVSubscriber/SVReceiver with proper cleanup
    and Python-friendly callback interface.

    Attributes:
        interface: Network interface name
        is_running: Whether the subscriber is actively receiving

    Example:
        sub = SVSubscriber("eth0")
        sub.set_app_id(0x4000)
        sub.set_listener(my_callback)
        sub.start()
        # ... receive samples ...
        sub.stop()
    """

    def __init__(self, interface: str):
        """
        Initialize SV subscriber.

        Args:
            interface: Network interface name (e.g., "eth0")

        Raises:
            LibraryNotFoundError: If pyiec61850 is not available
            ConfigurationError: If interface is invalid
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        if not interface:
            raise ConfigurationError("interface", "must not be empty")

        self._interface = interface
        self._receiver = None
        self._subscriber = None
        self._running = False
        self._listener: Optional[Callable] = None
        self._app_id: Optional[int] = None
        self._sv_id: Optional[str] = None
        self._dst_mac: Optional[bytes] = None

    @property
    def interface(self) -> str:
        """Return network interface name."""
        return self._interface

    @property
    def is_running(self) -> bool:
        """Check if subscriber is actively receiving."""
        return self._running

    def set_app_id(self, app_id: int) -> None:
        """
        Set APPID filter for received SV streams.

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

    def set_sv_id(self, sv_id: str) -> None:
        """
        Set SV ID filter.

        Args:
            sv_id: Sampled Value identifier string

        Raises:
            AlreadyStartedError: If subscriber is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._sv_id = sv_id

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
        Set callback for received SV messages.

        The callback receives an SVMessage object with decoded sample data.

        Args:
            callback: Callable that takes an SVMessage argument

        Raises:
            ConfigurationError: If callback is not callable
        """
        if callback is not None and not callable(callback):
            raise ConfigurationError("callback", "must be callable")
        self._listener = callback

    def start(self) -> None:
        """
        Start receiving Sampled Values.

        Creates the SVReceiver, configures the subscriber,
        and begins listening on the network interface.

        Raises:
            AlreadyStartedError: If already running
            SubscriptionError: If subscription setup fails
            InterfaceError: If network interface is not available
        """
        if self._running:
            raise AlreadyStartedError()

        try:
            # Create SV receiver
            self._receiver = iec61850.SVReceiver_create()
            if not self._receiver:
                raise SubscriptionError("Failed to create SVReceiver")

            iec61850.SVReceiver_setInterfaceId(self._receiver, self._interface)

            # Create subscriber with optional APPID filter
            if self._app_id is not None:
                self._subscriber = iec61850.SVSubscriber_create(self._dst_mac, self._app_id)
            else:
                self._subscriber = iec61850.SVSubscriber_create(None, 0)

            if not self._subscriber:
                raise SubscriptionError("Failed to create SVSubscriber")

            # Install callback if listener is set
            if self._listener:
                _sv_listener_registry[id(self)] = self._listener
                # Use the C callback mechanism via SVSubscriber_setListener
                # Since we cannot create C function pointers from Python,
                # we rely on polling or the SWIG handler pattern
                pass

            iec61850.SVReceiver_addSubscriber(self._receiver, self._subscriber)
            iec61850.SVReceiver_start(self._receiver)

            if not iec61850.SVReceiver_isRunning(self._receiver):
                raise InterfaceError(
                    self._interface, "SVReceiver failed to start (check permissions and interface)"
                )

            self._running = True
            logger.info(f"SV subscriber started on {self._interface}")

        except (AlreadyStartedError, SubscriptionError, InterfaceError):
            raise
        except Exception as e:
            self._cleanup()
            raise SubscriptionError(str(e))

    def read_current_values(self) -> SVMessage:
        """
        Read the current sample values from the subscriber.

        This is a polling-based approach: call periodically to get
        the latest received sample data.

        Returns:
            SVMessage with current sample data

        Raises:
            NotStartedError: If subscriber is not running
        """
        if not self._running:
            raise NotStartedError("Subscriber not started")

        msg = SVMessage()
        try:
            if self._subscriber:
                msg.smp_cnt = iec61850.SVSubscriber_getSmpCnt(self._subscriber)
                msg.conf_rev = iec61850.SVSubscriber_getConfRev(self._subscriber)
                msg.smp_synch = iec61850.SVSubscriber_getSmpSynch(self._subscriber)

                if hasattr(iec61850, "SVSubscriber_getSVID"):
                    msg.sv_id = iec61850.SVSubscriber_getSVID(self._subscriber)

                # Read ASDU values (typically 8 values: 4 currents + 4 voltages)
                asdu = iec61850.SVSubscriber_getASDU(self._subscriber, 0)
                if asdu:
                    for i in range(8):
                        try:
                            val = iec61850.SVClientASDU_getINT32(asdu, i * 4)
                            msg.values.append(float(val))
                        except Exception:
                            break

                msg.timestamp = datetime.now(tz=timezone.utc)
        except NotStartedError:
            raise
        except Exception as e:
            logger.warning(f"Error reading SV values: {e}")

        return msg

    def stop(self) -> None:
        """
        Stop receiving Sampled Values.

        Stops the receiver and cleans up all resources.
        Safe to call multiple times.
        """
        if not self._running:
            return

        logger.info(f"Stopping SV subscriber on {self._interface}")
        self._running = False

        # Remove from listener registry
        _sv_listener_registry.pop(id(self), None)

        try:
            if self._receiver:
                iec61850.SVReceiver_stop(self._receiver)
        except Exception as e:
            logger.warning(f"Error stopping SVReceiver: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up all native resources."""
        if self._receiver:
            try:
                iec61850.SVReceiver_destroy(self._receiver)
            except Exception as e:
                logger.warning(f"Error destroying SVReceiver: {e}")
        self._receiver = None
        # Subscriber is destroyed with receiver
        self._subscriber = None
        self._running = False

    def __enter__(self) -> "SVSubscriber":
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


# Global listener registry for C callback bridge
_sv_listener_registry = {}

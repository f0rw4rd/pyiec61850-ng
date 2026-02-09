#!/usr/bin/env python3
"""
Sampled Values Publisher

High-level wrapper for publishing IEC 61850-9-2 Sampled Values
using libiec61850 SVPublisher API.

Example:
    from pyiec61850.sv import SVPublisher

    with SVPublisher("eth0") as pub:
        pub.set_sv_id("myMU/LLN0$SV$MSVCB01")
        pub.set_app_id(0x4000)
        pub.start()
        pub.publish_samples([1000, 2000, 3000, 4000, 500, 600, 700, 800])
"""

import logging
from typing import List

try:
    import pyiec61850.pyiec61850 as iec61850

    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    AlreadyStartedError,
    ConfigurationError,
    LibraryNotFoundError,
    NotStartedError,
    PublishError,
)

logger = logging.getLogger(__name__)


class SVPublisher:
    """
    High-level Sampled Values publisher with automatic resource management.

    Wraps libiec61850 SVPublisher with proper cleanup and a
    Python-friendly interface for publishing IEC 61850-9-2 sample data.

    Attributes:
        interface: Network interface name
        is_running: Whether the publisher is active

    Example:
        pub = SVPublisher("eth0")
        pub.set_sv_id("myMU/LLN0$SV$MSVCB01")
        pub.set_app_id(0x4000)
        pub.start()
        pub.publish_samples([1000, 2000, 3000, 4000])
        pub.stop()
    """

    def __init__(self, interface: str):
        """
        Initialize SV publisher.

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
        self._publisher = None
        self._asdu = None
        self._running = False
        self._smp_cnt = 0

        # Configuration
        self._sv_id: str = ""
        self._app_id: int = 0x4000
        self._conf_rev: int = 1
        self._smp_rate: int = 4000
        self._dst_mac: bytes = b"\x01\x0c\xcd\x04\x00\x00"
        self._vlan_id: int = 0
        self._vlan_priority: int = 4
        self._num_int32_entries: int = 8
        self._num_asdu: int = 1

    @property
    def interface(self) -> str:
        """Return network interface name."""
        return self._interface

    @property
    def is_running(self) -> bool:
        """Check if publisher is active."""
        return self._running

    def set_sv_id(self, sv_id: str) -> None:
        """
        Set Sampled Value ID.

        Args:
            sv_id: SV identifier string

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._sv_id = sv_id

    def set_app_id(self, app_id: int) -> None:
        """
        Set APPID for published SV messages.

        Args:
            app_id: Application identifier (0-65535)

        Raises:
            ConfigurationError: If app_id is out of range
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        if not 0 <= app_id <= 0xFFFF:
            raise ConfigurationError("app_id", "must be 0-65535")
        self._app_id = app_id

    def set_conf_rev(self, conf_rev: int) -> None:
        """
        Set configuration revision.

        Args:
            conf_rev: Configuration revision number

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._conf_rev = conf_rev

    def set_smp_rate(self, smp_rate: int) -> None:
        """
        Set sample rate (samples per period).

        Args:
            smp_rate: Samples per period (e.g., 4000 for 80 samples/cycle at 50Hz)

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._smp_rate = smp_rate

    def set_dst_mac(self, mac: bytes) -> None:
        """
        Set destination MAC address.

        Args:
            mac: 6-byte MAC address

        Raises:
            ConfigurationError: If MAC address is invalid
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        if not isinstance(mac, (bytes, bytearray)) or len(mac) != 6:
            raise ConfigurationError("dst_mac", "must be 6 bytes")
        self._dst_mac = bytes(mac)

    def set_vlan(self, vlan_id: int, vlan_priority: int = 4) -> None:
        """
        Set VLAN parameters.

        Args:
            vlan_id: VLAN identifier (0-4095)
            vlan_priority: VLAN priority (0-7)

        Raises:
            ConfigurationError: If parameters are out of range
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        if not 0 <= vlan_id <= 4095:
            raise ConfigurationError("vlan_id", "must be 0-4095")
        if not 0 <= vlan_priority <= 7:
            raise ConfigurationError("vlan_priority", "must be 0-7")
        self._vlan_id = vlan_id
        self._vlan_priority = vlan_priority

    def set_num_entries(self, num_int32: int) -> None:
        """
        Set number of INT32 data entries per ASDU.

        Standard IEC 61850-9-2 LE uses 8 entries (4 currents + 4 voltages).

        Args:
            num_int32: Number of INT32 entries per ASDU

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._num_int32_entries = num_int32

    def start(self) -> None:
        """
        Start the SV publisher.

        Creates the SVPublisher and ASDU, and prepares for publishing.

        Raises:
            AlreadyStartedError: If already running
            PublishError: If publisher creation fails
        """
        if self._running:
            raise AlreadyStartedError()

        try:
            # Create SV publisher
            self._publisher = iec61850.SVPublisher_create(None, self._interface)
            if not self._publisher:
                raise PublishError(f"Failed to create SVPublisher on {self._interface}")

            # Create ASDU
            self._asdu = iec61850.SVPublisher_addASDU(
                self._publisher, self._sv_id, None, self._conf_rev
            )
            if not self._asdu:
                raise PublishError("Failed to create SV ASDU")

            # Add INT32 entries for sample data
            for _ in range(self._num_int32_entries):
                iec61850.SVPublisher_ASDU_addINT32(self._asdu)

            # Set sample count entry
            iec61850.SVPublisher_ASDU_setSmpCntWrap(self._asdu, self._smp_rate)

            # Set up ASDU
            iec61850.SVPublisher_setupComplete(self._publisher)

            self._smp_cnt = 0
            self._running = True
            logger.info(f"SV publisher started on {self._interface}")

        except (AlreadyStartedError, PublishError):
            raise
        except Exception as e:
            self._cleanup()
            raise PublishError(str(e))

    def publish_samples(self, values: List[int]) -> None:
        """
        Publish a set of sample values.

        Args:
            values: List of INT32 sample values. Length should match
                    the configured number of entries.

        Raises:
            NotStartedError: If publisher is not started
            PublishError: If publishing fails
        """
        if not self._running:
            raise NotStartedError("Publisher not started")

        try:
            # Set values in ASDU
            for i, val in enumerate(values):
                if i >= self._num_int32_entries:
                    break
                iec61850.SVPublisher_ASDU_setINT32(self._asdu, i, int(val))

            # Set sample count
            iec61850.SVPublisher_ASDU_setSmpCnt(self._asdu, self._smp_cnt)
            self._smp_cnt = (self._smp_cnt + 1) % self._smp_rate

            # Publish
            iec61850.SVPublisher_publish(self._publisher)

        except NotStartedError:
            raise
        except Exception as e:
            raise PublishError(str(e))

    def stop(self) -> None:
        """
        Stop the SV publisher.

        Safe to call multiple times.
        """
        if not self._running:
            return

        logger.info(f"Stopping SV publisher on {self._interface}")
        self._running = False
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up all native resources."""
        if self._publisher:
            try:
                iec61850.SVPublisher_destroy(self._publisher)
            except Exception as e:
                logger.warning(f"Error destroying SVPublisher: {e}")
        self._publisher = None
        self._asdu = None
        self._running = False

    def __enter__(self) -> "SVPublisher":
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

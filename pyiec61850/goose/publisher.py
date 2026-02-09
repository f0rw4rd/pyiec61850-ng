#!/usr/bin/env python3
"""
GOOSE Publisher

High-level wrapper for sending GOOSE messages using libiec61850
GoosePublisher and CommParameters APIs.

Example:
    from pyiec61850.goose import GoosePublisher

    with GoosePublisher("eth0") as pub:
        pub.set_go_cb_ref("simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        pub.set_app_id(0x1000)
        pub.set_conf_rev(1)
        pub.start()
        pub.publish([True, 42, 3.14])
"""

from typing import Any, List, Optional
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    InterfaceError,
    PublishError,
    ConfigurationError,
    NotStartedError,
    AlreadyStartedError,
    GooseError,
)
from .types import GoosePublisherConfig

logger = logging.getLogger(__name__)


class GoosePublisher:
    """
    High-level GOOSE publisher with automatic resource management.

    Wraps libiec61850 GoosePublisher with proper cleanup
    and a Python-friendly interface.

    Attributes:
        interface: Network interface name
        is_running: Whether the publisher is active

    Example:
        pub = GoosePublisher("eth0")
        pub.set_go_cb_ref("myIED/LLN0$GO$gcb01")
        pub.set_conf_rev(1)
        pub.start()
        pub.publish([True, 100.0])
        pub.stop()
    """

    def __init__(self, interface: str):
        """
        Initialize GOOSE publisher.

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
        self._comm_params = None
        self._running = False

        # Configuration
        self._go_cb_ref: str = ""
        self._go_id: str = ""
        self._data_set: str = ""
        self._app_id: int = 0x1000
        self._conf_rev: int = 1
        self._dst_mac: bytes = b"\x01\x0c\xcd\x01\x00\x00"
        self._vlan_id: int = 0
        self._vlan_priority: int = 4
        self._time_allowed_to_live: int = 2000
        self._needs_commissioning: bool = False

    @property
    def interface(self) -> str:
        """Return network interface name."""
        return self._interface

    @property
    def is_running(self) -> bool:
        """Check if publisher is active."""
        return self._running

    def set_go_cb_ref(self, go_cb_ref: str) -> None:
        """
        Set GOOSE Control Block reference.

        Args:
            go_cb_ref: GoCB reference string

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._go_cb_ref = go_cb_ref

    def set_go_id(self, go_id: str) -> None:
        """
        Set GOOSE ID.

        Args:
            go_id: GOOSE identifier string

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._go_id = go_id

    def set_data_set(self, data_set: str) -> None:
        """
        Set data set reference.

        Args:
            data_set: Data set reference string

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._data_set = data_set

    def set_app_id(self, app_id: int) -> None:
        """
        Set APPID for published messages.

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

    def set_time_allowed_to_live(self, time_ms: int) -> None:
        """
        Set time allowed to live (in milliseconds).

        Args:
            time_ms: Time in milliseconds

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._time_allowed_to_live = time_ms

    def set_needs_commissioning(self, needs_commissioning: bool) -> None:
        """
        Set needs commissioning flag.

        Args:
            needs_commissioning: Whether the message needs commissioning

        Raises:
            AlreadyStartedError: If publisher is already running
        """
        if self._running:
            raise AlreadyStartedError("Cannot configure while running")
        self._needs_commissioning = needs_commissioning

    def start(self) -> None:
        """
        Start the GOOSE publisher.

        Creates the publisher and configures it with all set parameters.

        Raises:
            AlreadyStartedError: If already running
            PublishError: If publisher creation fails
            InterfaceError: If network interface is not available
        """
        if self._running:
            raise AlreadyStartedError()

        try:
            # Create CommParameters
            self._comm_params = iec61850.CommParameters()
            if not self._comm_params:
                raise PublishError("Failed to create CommParameters")

            self._comm_params.appId = self._app_id
            self._comm_params.vlanId = self._vlan_id
            self._comm_params.vlanPriority = self._vlan_priority

            # Set destination MAC
            if self._dst_mac:
                for i in range(6):
                    self._comm_params.dstAddress[i] = self._dst_mac[i]

            # Create publisher
            self._publisher = iec61850.GoosePublisher_createEx(
                self._comm_params, self._interface, False
            )

            if not self._publisher:
                raise PublishError(
                    f"Failed to create GoosePublisher on {self._interface}"
                )

            # Configure publisher
            if self._go_cb_ref:
                iec61850.GoosePublisher_setGoCbRef(self._publisher, self._go_cb_ref)
            if self._go_id:
                iec61850.GoosePublisher_setGoID(self._publisher, self._go_id)
            if self._data_set:
                iec61850.GoosePublisher_setDataSetRef(self._publisher, self._data_set)
            iec61850.GoosePublisher_setConfRev(self._publisher, self._conf_rev)
            iec61850.GoosePublisher_setTimeAllowedToLive(
                self._publisher, self._time_allowed_to_live
            )
            iec61850.GoosePublisher_setNeedsCommission(
                self._publisher, self._needs_commissioning
            )

            self._running = True
            logger.info(f"GOOSE publisher started on {self._interface}")

        except (AlreadyStartedError, PublishError, InterfaceError):
            raise
        except Exception as e:
            self._cleanup()
            raise PublishError(str(e))

    def publish(self, values: List[Any]) -> None:
        """
        Publish a GOOSE message with the given data values.

        Args:
            values: List of Python values to encode as MMS data set entries.
                    Supported types: bool, int, float, str.

        Raises:
            NotStartedError: If publisher is not started
            PublishError: If publishing fails
        """
        if not self._running:
            raise NotStartedError("Publisher not started")

        data_set_values = None
        try:
            # Create LinkedList of MmsValue entries
            data_set_values = iec61850.LinkedList_create()
            if not data_set_values:
                raise PublishError("Failed to create value list")

            for val in values:
                mms_val = self._create_mms_value(val)
                if mms_val:
                    iec61850.LinkedList_add(data_set_values, mms_val)

            result = iec61850.GoosePublisher_publish(
                self._publisher, data_set_values
            )

            if result != 0:
                raise PublishError(f"GoosePublisher_publish returned error: {result}")

        except NotStartedError:
            raise
        except PublishError:
            raise
        except Exception as e:
            raise PublishError(str(e))
        finally:
            if data_set_values:
                try:
                    iec61850.LinkedList_destroyDeep(
                        data_set_values, iec61850.MmsValue_delete
                    )
                except Exception:
                    try:
                        iec61850.LinkedList_destroy(data_set_values)
                    except Exception:
                        pass

    def increase_st_num(self) -> None:
        """
        Increase the state number (stNum).

        Call this before publish() when the data set values have changed.

        Raises:
            NotStartedError: If publisher is not started
        """
        if not self._running:
            raise NotStartedError("Publisher not started")
        iec61850.GoosePublisher_increaseStNum(self._publisher)

    def stop(self) -> None:
        """
        Stop the GOOSE publisher.

        Safe to call multiple times.
        """
        if not self._running:
            return

        logger.info(f"Stopping GOOSE publisher on {self._interface}")
        self._running = False
        self._cleanup()

    def _create_mms_value(self, value: Any) -> Any:
        """Create an MmsValue from a Python value."""
        try:
            if isinstance(value, bool):
                return iec61850.MmsValue_newBoolean(value)
            elif isinstance(value, int):
                return iec61850.MmsValue_newIntegerFromInt32(value)
            elif isinstance(value, float):
                return iec61850.MmsValue_newFloat(value)
            elif isinstance(value, str):
                return iec61850.MmsValue_newVisibleString(value)
            else:
                logger.warning(f"Unsupported value type: {type(value)}")
                return None
        except Exception as e:
            logger.warning(f"Failed to create MmsValue: {e}")
            return None

    def _cleanup(self) -> None:
        """Clean up all native resources."""
        if self._publisher:
            try:
                iec61850.GoosePublisher_destroy(self._publisher)
            except Exception as e:
                logger.warning(f"Error destroying GoosePublisher: {e}")
        self._publisher = None
        self._comm_params = None
        self._running = False

    def __enter__(self) -> 'GoosePublisher':
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

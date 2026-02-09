#!/usr/bin/env python3
"""
IEC 61850 Control Operations Client

High-level wrapper for IEC 61850 control operations using
libiec61850 ControlObjectClient API. Supports Direct Operate (DO),
Select-Before-Operate (SBO), and Enhanced SBO patterns.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.control import ControlClient

    with MMSClient() as mms:
        mms.connect("192.168.1.100", 102)
        ctrl = ControlClient(mms)

        # Direct operate
        ctrl.operate("myLD/CSWI1.Pos", True)

        # Select-before-operate
        ctrl.select("myLD/CSWI1.Pos")
        ctrl.operate("myLD/CSWI1.Pos", True)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

try:
    import pyiec61850.pyiec61850 as iec61850

    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    MMSError,
    NotConnectedError,
)

logger = logging.getLogger(__name__)


class ControlError(MMSError):
    """Error during control operations."""

    def __init__(self, message: str = "Control error"):
        super().__init__(message)


class SelectError(ControlError):
    """Select-Before-Operate selection failed."""

    def __init__(self, object_ref: str = "", reason: str = ""):
        message = "Select failed"
        if object_ref:
            message = f"Failed to select '{object_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.object_ref = object_ref


class OperateError(ControlError):
    """Operate command failed."""

    def __init__(self, object_ref: str = "", reason: str = ""):
        message = "Operate failed"
        if object_ref:
            message = f"Failed to operate '{object_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.object_ref = object_ref


class CancelError(ControlError):
    """Cancel command failed."""

    def __init__(self, object_ref: str = "", reason: str = ""):
        message = "Cancel failed"
        if object_ref:
            message = f"Failed to cancel '{object_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.object_ref = object_ref


# Control model constants
CONTROL_MODEL_STATUS_ONLY = 0
CONTROL_MODEL_DIRECT_NORMAL = 1
CONTROL_MODEL_SBO_NORMAL = 2
CONTROL_MODEL_DIRECT_ENHANCED = 3
CONTROL_MODEL_SBO_ENHANCED = 4


@dataclass
class ControlResult:
    """Result of a control operation."""

    success: bool = False
    object_ref: str = ""
    last_error: int = 0
    add_cause: int = 0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "object_ref": self.object_ref,
        }
        if self.last_error:
            result["last_error"] = self.last_error
        if self.add_cause:
            result["add_cause"] = self.add_cause
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


class ControlClient:
    """
    High-level IEC 61850 control operations client.

    Provides Direct Operate, Select-Before-Operate, and Cancel
    operations using ControlObjectClient from libiec61850.

    Attributes:
        is_active: Whether any control objects are created

    Example:
        ctrl = ControlClient(mms_client)

        # Direct operate (no select needed)
        ctrl.operate("myLD/CSWI1.Pos", True)

        # Select-before-operate
        ctrl.select("myLD/CSWI1.Pos")
        ctrl.operate("myLD/CSWI1.Pos", True)

        # Cancel a pending select
        ctrl.cancel("myLD/CSWI1.Pos")
    """

    def __init__(self, mms_client):
        """
        Initialize control client.

        Args:
            mms_client: Connected MMSClient instance

        Raises:
            LibraryNotFoundError: If pyiec61850 is not available
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        self._mms_client = mms_client
        self._control_objects: Dict[str, Any] = {}
        self._command_term_handlers: Dict[str, Any] = {}
        self._command_term_subscribers: Dict[str, Any] = {}

    @property
    def is_active(self) -> bool:
        """Check if any control objects are managed."""
        return len(self._control_objects) > 0

    def _get_connection(self):
        """Get the underlying IedConnection."""
        if not self._mms_client.is_connected:
            raise NotConnectedError()
        return self._mms_client._connection

    def _get_or_create_control(self, object_ref: str) -> Any:
        """Get or create a ControlObjectClient for the given reference."""
        if object_ref in self._control_objects:
            return self._control_objects[object_ref]

        conn = self._get_connection()

        control = iec61850.ControlObjectClient_create(object_ref, conn)
        if not control:
            raise ControlError(f"Failed to create ControlObjectClient for '{object_ref}'")

        self._control_objects[object_ref] = control
        return control

    def select(self, object_ref: str) -> bool:
        """
        Select a controllable object (SBO pattern).

        Args:
            object_ref: Full object reference (e.g., "myLD/CSWI1.Pos")

        Returns:
            True if selection successful

        Raises:
            NotConnectedError: If not connected
            SelectError: If selection fails
        """
        try:
            control = self._get_or_create_control(object_ref)
            result = iec61850.ControlObjectClient_select(control)

            if not result:
                last_error = 0
                try:
                    last_error = iec61850.ControlObjectClient_getLastApplError(control)
                except Exception:
                    pass
                raise SelectError(object_ref, f"server rejected (error {last_error})")

            logger.info(f"Selected control object: {object_ref}")
            return True

        except NotConnectedError:
            raise
        except SelectError:
            raise
        except Exception as e:
            raise SelectError(object_ref, str(e))

    def select_with_value(self, object_ref: str, value: Any) -> bool:
        """
        Select a controllable object with a value (enhanced SBO).

        Args:
            object_ref: Full object reference
            value: Control value (bool, int, or float)

        Returns:
            True if selection successful

        Raises:
            NotConnectedError: If not connected
            SelectError: If selection fails
        """
        try:
            control = self._get_or_create_control(object_ref)
            mms_value = self._create_ctl_value(value)
            if not mms_value:
                raise SelectError(object_ref, f"unsupported value type: {type(value)}")

            result = iec61850.ControlObjectClient_selectWithValue(control, mms_value)

            if not result:
                raise SelectError(object_ref, "server rejected select-with-value")

            logger.info(f"Selected with value: {object_ref} = {value}")
            return True

        except NotConnectedError:
            raise
        except SelectError:
            raise
        except Exception as e:
            raise SelectError(object_ref, str(e))

    def operate(self, object_ref: str, value: Any) -> bool:
        """
        Operate a controllable object.

        For SBO control models, call select() first.
        For direct control models, this can be called directly.

        Args:
            object_ref: Full object reference
            value: Control value (bool for commands, int/float for setpoints)

        Returns:
            True if operation successful

        Raises:
            NotConnectedError: If not connected
            OperateError: If operation fails
        """
        try:
            control = self._get_or_create_control(object_ref)
            mms_value = self._create_ctl_value(value)
            if not mms_value:
                raise OperateError(object_ref, f"unsupported value type: {type(value)}")

            result = iec61850.ControlObjectClient_operate(control, mms_value, 0)

            if not result:
                last_error = 0
                try:
                    last_error = iec61850.ControlObjectClient_getLastApplError(control)
                except Exception:
                    pass
                raise OperateError(object_ref, f"server rejected (error {last_error})")

            logger.info(f"Operated: {object_ref} = {value}")
            return True

        except NotConnectedError:
            raise
        except OperateError:
            raise
        except Exception as e:
            raise OperateError(object_ref, str(e))

    def direct_operate(self, object_ref: str, value: Any) -> bool:
        """
        Directly operate a controllable object (no select).

        Equivalent to operate() but explicitly sets direct control mode.

        Args:
            object_ref: Full object reference
            value: Control value

        Returns:
            True if operation successful

        Raises:
            NotConnectedError: If not connected
            OperateError: If operation fails
        """
        try:
            control = self._get_or_create_control(object_ref)

            # Set control model to direct
            if hasattr(iec61850, "ControlObjectClient_setControlModel"):
                iec61850.ControlObjectClient_setControlModel(control, CONTROL_MODEL_DIRECT_NORMAL)

            return self.operate(object_ref, value)

        except (NotConnectedError, OperateError):
            raise
        except Exception as e:
            raise OperateError(object_ref, str(e))

    def cancel(self, object_ref: str) -> bool:
        """
        Cancel a pending select operation.

        Args:
            object_ref: Full object reference

        Returns:
            True if cancel successful

        Raises:
            NotConnectedError: If not connected
            CancelError: If cancel fails
        """
        try:
            control = self._get_or_create_control(object_ref)
            result = iec61850.ControlObjectClient_cancel(control)

            if not result:
                raise CancelError(object_ref, "server rejected cancel")

            logger.info(f"Cancelled: {object_ref}")
            return True

        except NotConnectedError:
            raise
        except CancelError:
            raise
        except Exception as e:
            raise CancelError(object_ref, str(e))

    def set_command_termination_handler(
        self,
        object_ref: str,
        callback: Callable,
    ) -> None:
        """
        Install a command termination handler.

        For enhanced control models, the server sends a command
        termination message after the operation completes.

        Args:
            object_ref: Full object reference
            callback: Callable that receives a ControlResult

        Raises:
            NotConnectedError: If not connected
            ControlError: If handler installation fails
        """
        if not callable(callback):
            raise ControlError("callback must be callable")

        try:
            control = self._get_or_create_control(object_ref)

            if hasattr(iec61850, "CommandTermHandler") and hasattr(
                iec61850, "CommandTermSubscriber"
            ):
                handler = _PyCommandTermHandler(callback, object_ref)
                subscriber = iec61850.CommandTermSubscriber()
                subscriber.setLibiec61850ControlObjectClient(control)
                subscriber.setEventHandler(handler)
                result = subscriber.subscribe()

                if not result:
                    raise ControlError(
                        f"Failed to subscribe to command termination for {object_ref}"
                    )

                self._command_term_handlers[object_ref] = handler
                self._command_term_subscribers[object_ref] = subscriber
            else:
                # Direct API fallback
                iec61850.ControlObjectClient_setCommandTerminationHandler(control, None, None)

            logger.info(f"Command termination handler installed for {object_ref}")

        except NotConnectedError:
            raise
        except ControlError:
            raise
        except Exception as e:
            raise ControlError(f"Failed to install command term handler for {object_ref}: {e}")

    def get_control_model(self, object_ref: str) -> int:
        """
        Get the control model for a controllable object.

        Args:
            object_ref: Full object reference

        Returns:
            Control model constant (0-4)

        Raises:
            NotConnectedError: If not connected
            ControlError: If query fails
        """
        try:
            control = self._get_or_create_control(object_ref)
            model = iec61850.ControlObjectClient_getControlModel(control)
            return model
        except NotConnectedError:
            raise
        except Exception as e:
            raise ControlError(f"Failed to get control model for {object_ref}: {e}")

    def release(self, object_ref: str) -> None:
        """
        Release a control object and free resources.

        Args:
            object_ref: Full object reference
        """
        control = self._control_objects.pop(object_ref, None)
        self._command_term_handlers.pop(object_ref, None)
        self._command_term_subscribers.pop(object_ref, None)
        if control:
            try:
                iec61850.ControlObjectClient_destroy(control)
            except Exception as e:
                logger.warning(f"Error destroying control object: {e}")

    def release_all(self) -> None:
        """Release all managed control objects."""
        for ref in list(self._control_objects.keys()):
            self.release(ref)

    def _create_ctl_value(self, value: Any) -> Any:
        """Create an MmsValue for a control value."""
        try:
            if isinstance(value, bool):
                return iec61850.MmsValue_newBoolean(value)
            elif isinstance(value, int):
                return iec61850.MmsValue_newIntegerFromInt32(value)
            elif isinstance(value, float):
                return iec61850.MmsValue_newFloat(value)
            else:
                return None
        except Exception as e:
            logger.warning(f"Failed to create control MmsValue: {e}")
            return None

    def __enter__(self) -> "ControlClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - releases all control objects."""
        self.release_all()
        return False


_CommandTermHandlerBase = getattr(iec61850, "CommandTermHandler", object)


class _PyCommandTermHandler(_CommandTermHandlerBase):
    """
    Python-side command termination handler (SWIG director subclass).

    Inherits from CommandTermHandler so the C++ side can call trigger()
    through the SWIG director vtable without segfaulting.
    """

    def __init__(self, callback: Callable, object_ref: str):
        super().__init__()
        self._callback = callback
        self._object_ref = object_ref

    def trigger(self):
        """Called by C++ subscriber when command termination arrives."""
        try:
            result = ControlResult(
                object_ref=self._object_ref,
                timestamp=datetime.now(tz=timezone.utc),
            )

            try:
                control = self._libiec61850_control_object_client
                last_error = iec61850.ControlObjectClient_getLastApplError(control)
                result.last_error = last_error
                result.success = last_error == 0
            except Exception:
                pass

            if self._callback:
                try:
                    self._callback(result)
                except Exception as e:
                    logger.warning(f"Command termination callback error: {e}")

        except Exception as e:
            logger.warning(f"Command termination handler error: {e}")

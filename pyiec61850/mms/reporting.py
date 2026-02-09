#!/usr/bin/env python3
"""
Report Control Block (RCB) Client

High-level wrapper for IEC 61850 reporting services using
libiec61850 RCBHandler/RCBSubscriber director classes.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.reporting import ReportClient

    with MMSClient() as mms:
        mms.connect("192.168.1.100", 102)
        reports = ReportClient(mms)
        reports.install_report_handler("myLD/LLN0$BR$brcb01", "rptId01", my_callback)
        reports.enable_reporting("myLD/LLN0$BR$brcb01")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

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
    ReadError,
)

logger = logging.getLogger(__name__)


class ReportError(MMSError):
    """Error during report operations."""

    def __init__(self, message: str = "Report error"):
        super().__init__(message)


class ReportConfigError(ReportError):
    """Error configuring Report Control Block."""

    def __init__(self, rcb_ref: str = "", reason: str = ""):
        message = "RCB configuration error"
        if rcb_ref:
            message = f"Failed to configure RCB '{rcb_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.rcb_ref = rcb_ref


@dataclass
class ReportEntry:
    """A single data entry within a received report."""

    reference: str = ""
    value: Any = None
    reason_code: int = 0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"reference": self.reference, "value": self.value}
        if self.reason_code:
            result["reason_code"] = self.reason_code
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class Report:
    """Received IEC 61850 Report."""

    rcb_reference: str = ""
    rpt_id: str = ""
    data_set_name: str = ""
    conf_rev: int = 0
    seq_num: int = 0
    sub_seq_num: int = 0
    more_segments_follow: bool = False
    buf_overflow: bool = False
    has_timestamp: bool = False
    timestamp: Optional[datetime] = None
    entries: List[ReportEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "rcb_reference": self.rcb_reference,
            "rpt_id": self.rpt_id,
            "data_set_name": self.data_set_name,
            "seq_num": self.seq_num,
            "entry_count": len(self.entries),
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class RCBConfig:
    """Report Control Block configuration parameters."""

    rpt_id: Optional[str] = None
    data_set: Optional[str] = None
    trigger_options: Optional[int] = None
    option_fields: Optional[int] = None
    buffer_time: Optional[int] = None
    integrity_period: Optional[int] = None
    rpt_ena: Optional[bool] = None
    gi: Optional[bool] = None
    purge_buf: Optional[bool] = None
    entry_id: Optional[bytes] = None
    resv: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.rpt_id is not None:
            result["rpt_id"] = self.rpt_id
        if self.data_set is not None:
            result["data_set"] = self.data_set
        if self.trigger_options is not None:
            result["trigger_options"] = self.trigger_options
        if self.option_fields is not None:
            result["option_fields"] = self.option_fields
        if self.buffer_time is not None:
            result["buffer_time"] = self.buffer_time
        if self.integrity_period is not None:
            result["integrity_period"] = self.integrity_period
        if self.rpt_ena is not None:
            result["rpt_ena"] = self.rpt_ena
        return result


# Trigger option constants
TRG_OPT_DATA_CHANGED = 1
TRG_OPT_QUALITY_CHANGED = 2
TRG_OPT_DATA_UPDATE = 4
TRG_OPT_INTEGRITY = 8
TRG_OPT_GI = 16

# Option field constants
RPT_OPT_SEQ_NUM = 1
RPT_OPT_TIME_STAMP = 2
RPT_OPT_REASON_FOR_INCLUSION = 4
RPT_OPT_DATA_SET = 8
RPT_OPT_DATA_REFERENCE = 16
RPT_OPT_BUFFER_OVERFLOW = 32
RPT_OPT_ENTRY_ID = 64
RPT_OPT_CONF_REV = 128


class ReportClient:
    """
    High-level Report Control Block client.

    Provides report subscription and RCB management for an
    existing MMS connection. Uses SWIG director classes
    (RCBHandler/RCBSubscriber) for asynchronous report delivery.

    Attributes:
        is_active: Whether any report subscriptions are active

    Example:
        reports = ReportClient(mms_client)
        reports.install_report_handler("myLD/LLN0$BR$brcb01", "rptId01", callback)
        reports.enable_reporting("myLD/LLN0$BR$brcb01")
        # ... receive reports via callback ...
        reports.disable_reporting("myLD/LLN0$BR$brcb01")
    """

    def __init__(self, mms_client):
        """
        Initialize report client.

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
        self._handlers: Dict[str, Any] = {}
        self._subscribers: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}

    @property
    def is_active(self) -> bool:
        """Check if any report handlers are installed."""
        return len(self._handlers) > 0

    def _get_connection(self):
        """Get the underlying IedConnection."""
        if not self._mms_client.is_connected:
            raise NotConnectedError()
        return self._mms_client._connection

    def get_rcb_values(self, rcb_reference: str) -> RCBConfig:
        """
        Read Report Control Block configuration from server.

        Args:
            rcb_reference: Full RCB object reference
                           (e.g., "myLD/LLN0$BR$brcb01")

        Returns:
            RCBConfig with current RCB parameters

        Raises:
            NotConnectedError: If not connected
            ReadError: If read fails
        """
        conn = self._get_connection()
        config = RCBConfig()

        try:
            result = iec61850.IedConnection_getRCBValues(conn, rcb_reference, None)

            if isinstance(result, tuple):
                rcb_values, error = result[0], result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise ReadError(f"Failed to read RCB values: error {error}")
            else:
                rcb_values = result

            if rcb_values:
                try:
                    config.rpt_id = iec61850.ClientReportControlBlock_getRptId(rcb_values)
                except Exception:
                    pass
                try:
                    config.data_set = iec61850.ClientReportControlBlock_getDataSetName(rcb_values)
                except Exception:
                    pass
                try:
                    config.trigger_options = iec61850.ClientReportControlBlock_getTrgOps(rcb_values)
                except Exception:
                    pass
                try:
                    config.option_fields = iec61850.ClientReportControlBlock_getOptFlds(rcb_values)
                except Exception:
                    pass
                try:
                    config.buffer_time = iec61850.ClientReportControlBlock_getBufTm(rcb_values)
                except Exception:
                    pass
                try:
                    config.integrity_period = iec61850.ClientReportControlBlock_getIntgPd(
                        rcb_values
                    )
                except Exception:
                    pass
                try:
                    config.rpt_ena = iec61850.ClientReportControlBlock_getRptEna(rcb_values)
                except Exception:
                    pass

            return config

        except NotConnectedError:
            raise
        except ReadError:
            raise
        except Exception as e:
            raise ReadError(f"Failed to read RCB {rcb_reference}: {e}")

    def set_rcb_values(self, rcb_reference: str, config: RCBConfig) -> None:
        """
        Write Report Control Block configuration to server.

        Args:
            rcb_reference: Full RCB object reference
            config: RCBConfig with parameters to set

        Raises:
            NotConnectedError: If not connected
            ReportConfigError: If configuration fails
        """
        conn = self._get_connection()

        try:
            # Read current values first
            result = iec61850.IedConnection_getRCBValues(conn, rcb_reference, None)

            if isinstance(result, tuple):
                rcb_values, error = result[0], result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise ReportConfigError(rcb_reference, f"error {error}")
            else:
                rcb_values = result

            if not rcb_values:
                raise ReportConfigError(rcb_reference, "failed to read RCB")

            # Apply configuration changes
            parametersMask = 0

            if config.rpt_id is not None:
                iec61850.ClientReportControlBlock_setRptId(rcb_values, config.rpt_id)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_RPT_ID", 0x01)

            if config.data_set is not None:
                iec61850.ClientReportControlBlock_setDataSetName(rcb_values, config.data_set)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_DATSET", 0x02)

            if config.trigger_options is not None:
                iec61850.ClientReportControlBlock_setTrgOps(rcb_values, config.trigger_options)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_TRG_OPS", 0x10)

            if config.option_fields is not None:
                iec61850.ClientReportControlBlock_setOptFlds(rcb_values, config.option_fields)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_OPT_FLDS", 0x08)

            if config.buffer_time is not None:
                iec61850.ClientReportControlBlock_setBufTm(rcb_values, config.buffer_time)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_BUF_TM", 0x20)

            if config.integrity_period is not None:
                iec61850.ClientReportControlBlock_setIntgPd(rcb_values, config.integrity_period)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_INTG_PD", 0x80)

            if config.rpt_ena is not None:
                iec61850.ClientReportControlBlock_setRptEna(rcb_values, config.rpt_ena)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_RPT_ENA", 0x04)

            if config.gi is not None:
                iec61850.ClientReportControlBlock_setGI(rcb_values, config.gi)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_GI", 0x40)

            if config.resv is not None:
                iec61850.ClientReportControlBlock_setResv(rcb_values, config.resv)
                parametersMask |= getattr(iec61850, "RCB_ELEMENT_RESV", 0x100)

            # Write back to server
            error = iec61850.IedConnection_setRCBValues(conn, rcb_values, parametersMask, True)

            if isinstance(error, tuple):
                error = error[-1]
            if error != iec61850.IED_ERROR_OK:
                raise ReportConfigError(rcb_reference, f"write error {error}")

            logger.info(f"Configured RCB {rcb_reference}")

        except NotConnectedError:
            raise
        except ReportConfigError:
            raise
        except Exception as e:
            raise ReportConfigError(rcb_reference, str(e))

    def install_report_handler(
        self,
        rcb_reference: str,
        rpt_id: str,
        callback: Callable,
    ) -> None:
        """
        Install a report handler for the given RCB.

        Uses the SWIG director RCBHandler/RCBSubscriber classes
        to receive asynchronous report notifications.

        Args:
            rcb_reference: Full RCB reference (e.g., "myLD/LLN0$BR$brcb01")
            rpt_id: Report ID string
            callback: Callable that receives a Report object

        Raises:
            NotConnectedError: If not connected
            ReportError: If handler installation fails
        """
        conn = self._get_connection()

        if not callable(callback):
            raise ReportError("callback must be callable")

        try:
            if hasattr(iec61850, "RCBHandler") and hasattr(iec61850, "RCBSubscriber"):
                handler = _PyRCBHandler(callback, rcb_reference)
                subscriber = iec61850.RCBSubscriber()
                subscriber.setIedConnection(conn)
                subscriber.setRcbReference(rcb_reference)
                subscriber.setRcbRptId(rpt_id)
                subscriber.setEventHandler(handler)
                result = subscriber.subscribe()

                if not result:
                    raise ReportError(f"Failed to subscribe to RCB {rcb_reference}")

                self._handlers[rcb_reference] = handler
                self._subscribers[rcb_reference] = subscriber
                self._callbacks[rcb_reference] = callback
            else:
                # Fallback: use IedConnection_installReportHandler directly
                iec61850.IedConnection_installReportHandler(conn, rcb_reference, rpt_id, None, None)
                self._callbacks[rcb_reference] = callback

            logger.info(f"Report handler installed for {rcb_reference}")

        except NotConnectedError:
            raise
        except ReportError:
            raise
        except Exception as e:
            raise ReportError(f"Failed to install handler for {rcb_reference}: {e}")

    def enable_reporting(self, rcb_reference: str) -> None:
        """
        Enable reporting on the given RCB.

        Args:
            rcb_reference: Full RCB reference

        Raises:
            NotConnectedError: If not connected
            ReportConfigError: If enable fails
        """
        config = RCBConfig(rpt_ena=True)
        self.set_rcb_values(rcb_reference, config)
        logger.info(f"Reporting enabled for {rcb_reference}")

    def disable_reporting(self, rcb_reference: str) -> None:
        """
        Disable reporting on the given RCB.

        Args:
            rcb_reference: Full RCB reference

        Raises:
            NotConnectedError: If not connected
            ReportConfigError: If disable fails
        """
        config = RCBConfig(rpt_ena=False)
        self.set_rcb_values(rcb_reference, config)
        logger.info(f"Reporting disabled for {rcb_reference}")

    def trigger_gi_report(self, rcb_reference: str) -> None:
        """
        Trigger a General Interrogation (GI) report.

        Args:
            rcb_reference: Full RCB reference

        Raises:
            NotConnectedError: If not connected
            ReportConfigError: If trigger fails
        """
        config = RCBConfig(gi=True)
        self.set_rcb_values(rcb_reference, config)
        logger.info(f"GI report triggered for {rcb_reference}")

    def uninstall_report_handler(self, rcb_reference: str) -> None:
        """
        Uninstall a report handler.

        Args:
            rcb_reference: Full RCB reference
        """
        self._handlers.pop(rcb_reference, None)
        self._subscribers.pop(rcb_reference, None)
        self._callbacks.pop(rcb_reference, None)
        logger.info(f"Report handler uninstalled for {rcb_reference}")

    def uninstall_all_handlers(self) -> None:
        """Uninstall all report handlers."""
        self._handlers.clear()
        self._subscribers.clear()
        self._callbacks.clear()
        logger.info("All report handlers uninstalled")

    def __enter__(self) -> "ReportClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - uninstalls all handlers."""
        self.uninstall_all_handlers()
        return False


class _PyRCBHandler:
    """
    Python-side RCB report handler (SWIG director subclass).

    Receives ClientReport from the C++ layer, parses it into
    a Report object, and delivers it to the Python callback.
    """

    def __init__(self, callback: Callable, rcb_reference: str):
        self._callback = callback
        self._rcb_reference = rcb_reference

        if _HAS_IEC61850 and hasattr(iec61850, "RCBHandler"):
            try:
                iec61850.RCBHandler.__init__(self)
            except Exception:
                pass

    def trigger(self):
        """Called by C++ subscriber when a report arrives."""
        try:
            client_report = self._client_report

            report = Report(rcb_reference=self._rcb_reference)

            try:
                report.rpt_id = iec61850.ClientReport_getRptId(client_report)
            except Exception:
                pass
            try:
                report.data_set_name = iec61850.ClientReport_getDataSetName(client_report)
            except Exception:
                pass
            try:
                report.seq_num = iec61850.ClientReport_getSeqNum(client_report)
            except Exception:
                pass
            try:
                report.sub_seq_num = iec61850.ClientReport_getSubSeqNum(client_report)
            except Exception:
                pass
            try:
                report.more_segments_follow = iec61850.ClientReport_getMoreSegementsFollow(
                    client_report
                )
            except Exception:
                pass
            try:
                report.has_timestamp = iec61850.ClientReport_hasTimestamp(client_report)
            except Exception:
                pass
            try:
                report.buf_overflow = iec61850.ClientReport_hasBufOvfl(client_report)
            except Exception:
                pass
            try:
                report.conf_rev = iec61850.ClientReport_getConfRev(client_report)
            except Exception:
                pass

            # Extract data set values
            try:
                data_set_values = iec61850.ClientReport_getDataSetValues(client_report)
                if data_set_values:
                    count = iec61850.MmsValue_getArraySize(data_set_values)
                    for i in range(count):
                        element = iec61850.MmsValue_getElement(data_set_values, i)
                        if element:
                            entry = ReportEntry(
                                value=_extract_mms_value(element),
                            )
                            try:
                                entry.reason_code = iec61850.ClientReport_getReasonForInclusion(
                                    client_report, i
                                )
                            except Exception:
                                pass
                            report.entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to parse report entries: {e}")

            report.timestamp = datetime.now(tz=timezone.utc)

            if self._callback:
                try:
                    self._callback(report)
                except Exception as e:
                    logger.warning(f"Report callback error: {e}")

        except Exception as e:
            logger.warning(f"RCB handler error: {e}")


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
        elif mms_type in (
            getattr(iec61850, "MMS_VISIBLE_STRING", 8),
            getattr(iec61850, "MMS_STRING", 13),
        ):
            return iec61850.MmsValue_toString(mms_value)
        elif mms_type == getattr(iec61850, "MMS_BIT_STRING", 3):
            return iec61850.MmsValue_getBitStringAsInteger(mms_value)
        else:
            return None
    except Exception:
        return None

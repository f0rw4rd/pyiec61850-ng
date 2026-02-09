#!/usr/bin/env python3
"""
MMS Log/Journal Services Client

High-level wrapper for IEC 61850 log and journal query services
using libiec61850 IedConnection log query APIs.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.logging_service import LogClient

    with MMSClient() as mms:
        mms.connect("192.168.1.100", 102)
        log_client = LogClient(mms)
        entries = log_client.query_log_by_time(
            "myLD/LLN0$log01", start_time, end_time
        )
        for entry in entries:
            print(entry.entry_id, entry.timestamp, entry.values)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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


class LogError(MMSError):
    """Error during log/journal operations."""

    def __init__(self, message: str = "Log error"):
        super().__init__(message)


class LogQueryError(LogError):
    """Error querying log entries."""

    def __init__(self, log_ref: str = "", reason: str = ""):
        message = "Log query failed"
        if log_ref:
            message = f"Failed to query log '{log_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.log_ref = log_ref


@dataclass
class JournalEntryData:
    """A single data value within a journal entry."""

    tag: str = ""
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {"tag": self.tag, "value": self.value}


@dataclass
class JournalEntry:
    """An MMS journal entry (log entry)."""

    entry_id: str = ""
    timestamp: Optional[datetime] = None
    values: List[JournalEntryData] = field(default_factory=list)
    more_follows: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "entry_id": self.entry_id,
            "value_count": len(self.values),
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        if self.values:
            result["values"] = [v.to_dict() for v in self.values]
        return result


@dataclass
class LogQueryResult:
    """Result of a log query operation."""

    entries: List[JournalEntry] = field(default_factory=list)
    more_follows: bool = False
    entry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_count": self.entry_count,
            "more_follows": self.more_follows,
            "entries": [e.to_dict() for e in self.entries],
        }


class LogClient:
    """
    High-level MMS Log/Journal services client.

    Provides log query operations for an existing MMS connection.

    Example:
        log_client = LogClient(mms_client)
        result = log_client.query_log_by_time(
            "myLD/LLN0$log01", start_ms, end_ms
        )
    """

    def __init__(self, mms_client):
        """
        Initialize log client.

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

    def _get_connection(self):
        """Get the underlying IedConnection."""
        if not self._mms_client.is_connected:
            raise NotConnectedError()
        return self._mms_client._connection

    def query_log_after(
        self,
        log_ref: str,
        entry_id: str,
        timestamp_ms: int,
    ) -> LogQueryResult:
        """
        Query log entries after a specific entry.

        Args:
            log_ref: Log reference (e.g., "myLD/LLN0$log01")
            entry_id: Entry ID to query after
            timestamp_ms: Timestamp in milliseconds since epoch

        Returns:
            LogQueryResult with journal entries

        Raises:
            NotConnectedError: If not connected
            LogQueryError: If query fails
        """
        conn = self._get_connection()
        result = LogQueryResult()

        try:
            query_result = iec61850.IedConnection_queryLogAfter(
                conn, log_ref, entry_id, timestamp_ms
            )

            if isinstance(query_result, tuple):
                entries_list, error = query_result[0], query_result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise LogQueryError(log_ref, f"error {error}")
            else:
                entries_list = query_result

            if entries_list:
                result.entries = self._parse_journal_entries(entries_list)
                result.entry_count = len(result.entries)
                try:
                    iec61850.LinkedList_destroy(entries_list)
                except Exception:
                    pass

            return result

        except NotConnectedError:
            raise
        except LogQueryError:
            raise
        except Exception as e:
            raise LogQueryError(log_ref, str(e))

    def query_log_by_time(
        self,
        log_ref: str,
        start_time_ms: int,
        end_time_ms: int,
    ) -> LogQueryResult:
        """
        Query log entries within a time range.

        Args:
            log_ref: Log reference (e.g., "myLD/LLN0$log01")
            start_time_ms: Start timestamp in milliseconds since epoch
            end_time_ms: End timestamp in milliseconds since epoch

        Returns:
            LogQueryResult with journal entries

        Raises:
            NotConnectedError: If not connected
            LogQueryError: If query fails
        """
        conn = self._get_connection()
        result = LogQueryResult()

        try:
            query_result = iec61850.IedConnection_queryLogByTime(
                conn, log_ref, start_time_ms, end_time_ms
            )

            if isinstance(query_result, tuple):
                entries_list, error = query_result[0], query_result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise LogQueryError(log_ref, f"error {error}")
            else:
                entries_list = query_result

            if entries_list:
                result.entries = self._parse_journal_entries(entries_list)
                result.entry_count = len(result.entries)
                try:
                    iec61850.LinkedList_destroy(entries_list)
                except Exception:
                    pass

            return result

        except NotConnectedError:
            raise
        except LogQueryError:
            raise
        except Exception as e:
            raise LogQueryError(log_ref, str(e))

    def _parse_journal_entries(self, entries_list) -> List[JournalEntry]:
        """Parse a LinkedList of MmsJournalEntry objects."""
        entries = []

        try:
            element = iec61850.LinkedList_getNext(entries_list)
            while element:
                data = iec61850.LinkedList_getData(element)
                if data:
                    entry = JournalEntry()

                    try:
                        entry.entry_id = iec61850.MmsJournalEntry_getEntryID(data)
                    except Exception:
                        pass

                    try:
                        occur_time = iec61850.MmsJournalEntry_getOccurenceTime(data)
                        if occur_time:
                            entry.timestamp = datetime.fromtimestamp(
                                occur_time / 1000.0, tz=timezone.utc
                            )
                    except Exception:
                        pass

                    # Parse journal variables
                    try:
                        var_list = iec61850.MmsJournalEntry_getJournalVariables(data)
                        if var_list:
                            var_elem = iec61850.LinkedList_getNext(var_list)
                            while var_elem:
                                var_data = iec61850.LinkedList_getData(var_elem)
                                if var_data:
                                    jv = JournalEntryData()
                                    try:
                                        jv.tag = iec61850.MmsJournalVariable_getTag(var_data)
                                    except Exception:
                                        pass
                                    try:
                                        mms_val = iec61850.MmsJournalVariable_getValue(var_data)
                                        if mms_val:
                                            jv.value = _extract_mms_value(mms_val)
                                    except Exception:
                                        pass
                                    entry.values.append(jv)
                                var_elem = iec61850.LinkedList_getNext(var_elem)
                    except Exception as e:
                        logger.warning(f"Error parsing journal variables: {e}")

                    entries.append(entry)

                element = iec61850.LinkedList_getNext(element)

        except Exception as e:
            logger.warning(f"Error parsing journal entries: {e}")

        return entries

    def __enter__(self) -> "LogClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False


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
        else:
            return None
    except Exception:
        return None

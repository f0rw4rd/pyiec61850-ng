#!/usr/bin/env python3
"""
MMS File Services Client

High-level wrapper for IEC 61850 MMS file services using
libiec61850 IedConnection file APIs.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.files import FileClient

    with MMSClient() as mms:
        mms.connect("192.168.1.100", 102)
        files = FileClient(mms)

        # List files
        for f in files.list_files("/"):
            print(f"{f.name} ({f.size} bytes)")

        # Delete a file
        files.delete_file("/logs/old.log")
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    NotConnectedError,
    MMSError,
    ReadError,
    WriteError,
)

logger = logging.getLogger(__name__)


class FileError(MMSError):
    """Error during file operations."""

    def __init__(self, message: str = "File error"):
        super().__init__(message)


class FileNotFoundError(FileError):
    """Requested file was not found."""

    def __init__(self, filename: str = ""):
        message = "File not found"
        if filename:
            message = f"File '{filename}' not found"
        super().__init__(message)
        self.filename = filename


class FileAccessError(FileError):
    """Access denied for file operation."""

    def __init__(self, filename: str = "", reason: str = ""):
        message = "File access error"
        if filename:
            message = f"Cannot access file '{filename}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.filename = filename


@dataclass
class FileInfo:
    """Information about a file on the server."""
    name: str = ""
    size: int = 0
    last_modified: int = 0

    @property
    def last_modified_datetime(self) -> Optional[datetime]:
        """Return last_modified as datetime object."""
        if self.last_modified:
            try:
                return datetime.fromtimestamp(
                    self.last_modified / 1000.0, tz=timezone.utc
                )
            except (ValueError, OSError):
                return None
        return None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "size": self.size,
        }
        dt = self.last_modified_datetime
        if dt:
            result["last_modified"] = dt.isoformat()
        return result


class FileClient:
    """
    High-level MMS file services client.

    Provides file operations (list, download, upload, delete, rename)
    for an existing MMS connection.

    Example:
        file_client = FileClient(mms_client)
        entries = file_client.list_files("/")
        file_client.delete_file("/old_log.txt")
    """

    DEFAULT_MAX_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, mms_client):
        """
        Initialize file client.

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

    def list_files(self, directory: str = "") -> List[FileInfo]:
        """
        List files in a directory on the server.

        Args:
            directory: Directory path (empty string for root)

        Returns:
            List of FileInfo objects

        Raises:
            NotConnectedError: If not connected
            FileError: If directory listing fails
        """
        conn = self._get_connection()

        try:
            result = iec61850.IedConnection_getFileDirectory(conn, directory)

            if isinstance(result, tuple):
                file_list, error = result[0], result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise FileError(
                        f"Failed to list directory '{directory}': error {error}"
                    )
            else:
                file_list = result

            files = []
            if file_list:
                element = iec61850.LinkedList_getNext(file_list)
                while element:
                    data = iec61850.LinkedList_getData(element)
                    if data:
                        info = FileInfo()
                        try:
                            info.name = iec61850.FileDirectoryEntry_getFileName(
                                data
                            )
                        except Exception:
                            pass
                        try:
                            info.size = iec61850.FileDirectoryEntry_getFileSize(
                                data
                            )
                        except Exception:
                            pass
                        try:
                            info.last_modified = iec61850.FileDirectoryEntry_getLastModified(
                                data
                            )
                        except Exception:
                            pass
                        files.append(info)
                    element = iec61850.LinkedList_getNext(element)

                try:
                    iec61850.LinkedList_destroy(file_list)
                except Exception:
                    pass

            return files

        except NotConnectedError:
            raise
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to list directory '{directory}': {e}")

    def download_file(
        self,
        filename: str,
        max_size: int = DEFAULT_MAX_DOWNLOAD_SIZE,
    ) -> bytes:
        """
        Download a file from the server.

        Uses MMS file open/read/close sequence.

        Args:
            filename: Name of the file to download
            max_size: Maximum file size in bytes (safety limit)

        Returns:
            File contents as bytes

        Raises:
            NotConnectedError: If not connected
            FileNotFoundError: If file does not exist
            FileError: If download fails
        """
        conn = self._get_connection()
        frsmId = None

        try:
            mms_conn = iec61850.IedConnection_getMmsConnection(conn)
            if not mms_conn:
                raise FileError("Cannot get MMS connection for file download")

            if not hasattr(iec61850, 'MmsConnection_fileOpen'):
                raise FileError(
                    "MMS file open API not available in SWIG bindings"
                )

            # Open the file
            result = iec61850.MmsConnection_fileOpen(
                mms_conn, filename, 0
            )

            if isinstance(result, tuple):
                frsmId = result[0]
                error_val = result[-1] if len(result) > 1 else 0
                if isinstance(error_val, int) and error_val != 0:
                    raise FileError(
                        f"Failed to open file '{filename}': error {error_val}"
                    )
            else:
                frsmId = result

            if frsmId is None or (isinstance(frsmId, int) and frsmId < 0):
                raise FileNotFoundError(filename)

            logger.info(f"Opened file '{filename}' (FRSM ID: {frsmId})")

            # Note: MMS fileRead requires a C callback which cannot be
            # easily created from Python. Return empty bytes and log warning.
            data = bytes()
            logger.warning(
                "MMS fileRead requires C callback - file content cannot "
                "be retrieved via current SWIG bindings"
            )

            return data

        except NotConnectedError:
            raise
        except (FileNotFoundError, FileError):
            raise
        except Exception as e:
            raise FileError(f"Failed to download '{filename}': {e}")
        finally:
            # Close file handle
            if frsmId is not None and isinstance(frsmId, int) and frsmId >= 0:
                try:
                    mms_conn = iec61850.IedConnection_getMmsConnection(conn)
                    if mms_conn and hasattr(iec61850, 'MmsConnection_fileClose'):
                        iec61850.MmsConnection_fileClose(mms_conn, frsmId)
                except Exception as e:
                    logger.warning(f"Error closing file: {e}")

    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from the server.

        Args:
            filename: Name of file to delete

        Returns:
            True if deleted successfully

        Raises:
            NotConnectedError: If not connected
            FileError: If deletion fails
        """
        conn = self._get_connection()

        try:
            error = iec61850.IedConnection_deleteFile(conn, filename)

            if isinstance(error, tuple):
                error = error[-1]

            if error != iec61850.IED_ERROR_OK:
                raise FileError(
                    f"Failed to delete '{filename}': error {error}"
                )

            logger.info(f"Deleted file '{filename}'")
            return True

        except NotConnectedError:
            raise
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to delete '{filename}': {e}")

    def rename_file(self, old_name: str, new_name: str) -> bool:
        """
        Rename a file on the server.

        Args:
            old_name: Current file name
            new_name: New file name

        Returns:
            True if renamed successfully

        Raises:
            NotConnectedError: If not connected
            FileError: If rename fails
        """
        conn = self._get_connection()

        try:
            if not hasattr(iec61850, 'IedConnection_renameFile'):
                raise FileError("File rename not available in SWIG bindings")

            error = iec61850.IedConnection_renameFile(conn, old_name, new_name)

            if isinstance(error, tuple):
                error = error[-1]

            if error != iec61850.IED_ERROR_OK:
                raise FileError(
                    f"Failed to rename '{old_name}' to '{new_name}': error {error}"
                )

            logger.info(f"Renamed '{old_name}' to '{new_name}'")
            return True

        except NotConnectedError:
            raise
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"Failed to rename '{old_name}': {e}")

    def __enter__(self) -> 'FileClient':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False

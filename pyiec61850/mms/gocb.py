#!/usr/bin/env python3
"""
GOOSE Control Block (GoCB) Client

High-level wrapper for reading GOOSE Control Block configuration
from IEC 61850 servers over MMS.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.gocb import GoCBClient

    with MMSClient() as mms:
        mms.connect("192.168.1.100", 102)
        gocb = GoCBClient(mms)
        info = gocb.read("simpleIOGenericIO/LLN0$GO$gcbAnalogValues")
        print(f"GOOSE ID: {info.goose_id}, Dataset: {info.dataset}")
"""

import logging
from dataclasses import dataclass
from typing import List

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
from .utils import (
    LinkedListGuard,
    unpack_result,
)

logger = logging.getLogger(__name__)


class GoCBError(MMSError):
    """Error during GoCB operations."""

    def __init__(self, message: str = "GoCB error"):
        super().__init__(message)


def _format_mac(mms_mac_value) -> str:
    """Format an MMS octet-string MAC address as a colon-separated hex string."""
    if not _HAS_IEC61850 or mms_mac_value is None:
        return ""
    try:
        size = iec61850.MmsValue_getOctetStringSize(mms_mac_value)
        if size < 6:
            return ""
        octets = []
        for i in range(6):
            octets.append(format(iec61850.MmsValue_getOctetStringOctet(mms_mac_value, i), "02x"))
        return ":".join(octets)
    except Exception:
        return ""


@dataclass
class GoCBInfo:
    """GOOSE Control Block configuration read from a server."""

    gocb_ref: str = ""
    goose_id: str = ""
    dataset: str = ""
    enabled: bool = False
    conf_rev: int = 0
    min_time: int = 0
    max_time: int = 0
    fixed_offs: bool = False
    nds_comm: bool = False
    appid: int = 0
    vlan_id: int = 0
    vlan_priority: int = 0
    dst_mac: str = ""


class GoCBClient:
    """
    High-level client for reading GOOSE Control Blocks over MMS.

    Wraps the ClientGooseControlBlock C API with proper resource
    management and a Python-friendly interface.

    Args:
        mms_client: Connected MMSClient instance

    Example:
        gocb = GoCBClient(mms_client)
        info = gocb.read("myLD/LLN0$GO$gcb01")
        print(info.goose_id, info.dataset)
    """

    def __init__(self, mms_client):
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )
        self._mms_client = mms_client

    def _get_connection(self):
        """Get the underlying IedConnection handle."""
        if not self._mms_client.is_connected:
            raise NotConnectedError()
        return self._mms_client._connection

    def read(self, gocb_ref: str) -> GoCBInfo:
        """
        Read a GOOSE Control Block's configuration from the server.

        Args:
            gocb_ref: Full GoCB object reference
                      (e.g., "simpleIOGenericIO/LLN0$GO$gcbAnalogValues")

        Returns:
            GoCBInfo with current GoCB parameters

        Raises:
            NotConnectedError: If not connected
            ReadError: If read fails
        """
        conn = self._get_connection()

        gocb = None
        try:
            result = iec61850.IedConnection_getGoCBValues(conn, gocb_ref, None)

            if isinstance(result, tuple):
                gocb_handle, error = result[0], result[-1]
                if error != iec61850.IED_ERROR_OK:
                    raise ReadError(f"Failed to read GoCB '{gocb_ref}': error {error}")
            else:
                gocb_handle = result

            if not gocb_handle:
                raise ReadError(f"Failed to read GoCB '{gocb_ref}': null response")

            gocb = gocb_handle
            return self._parse_gocb(gocb_ref, gocb)

        except (NotConnectedError, ReadError):
            raise
        except Exception as e:
            raise ReadError(f"Failed to read GoCB '{gocb_ref}': {e}")
        finally:
            if gocb is not None:
                try:
                    iec61850.ClientGooseControlBlock_destroy(gocb)
                except Exception as e:
                    logger.debug(f"GoCB destroy error: {e}")

    def _parse_gocb(self, gocb_ref: str, gocb) -> GoCBInfo:
        """Extract all fields from a ClientGooseControlBlock handle."""
        info = GoCBInfo(gocb_ref=gocb_ref)

        try:
            info.goose_id = iec61850.ClientGooseControlBlock_getGoID(gocb) or ""
        except Exception:
            pass
        try:
            info.dataset = iec61850.ClientGooseControlBlock_getDatSet(gocb) or ""
        except Exception:
            pass
        try:
            info.enabled = bool(iec61850.ClientGooseControlBlock_getGoEna(gocb))
        except Exception:
            pass
        try:
            info.conf_rev = int(iec61850.ClientGooseControlBlock_getConfRev(gocb))
        except Exception:
            pass
        try:
            info.min_time = int(iec61850.ClientGooseControlBlock_getMinTime(gocb))
        except Exception:
            pass
        try:
            info.max_time = int(iec61850.ClientGooseControlBlock_getMaxTime(gocb))
        except Exception:
            pass
        try:
            info.fixed_offs = bool(iec61850.ClientGooseControlBlock_getFixedOffs(gocb))
        except Exception:
            pass
        try:
            info.nds_comm = bool(iec61850.ClientGooseControlBlock_getNdsComm(gocb))
        except Exception:
            pass
        try:
            info.appid = int(iec61850.ClientGooseControlBlock_getDstAddress_appid(gocb))
        except Exception:
            pass
        try:
            info.vlan_id = int(iec61850.ClientGooseControlBlock_getDstAddress_vid(gocb))
        except Exception:
            pass
        try:
            info.vlan_priority = int(iec61850.ClientGooseControlBlock_getDstAddress_priority(gocb))
        except Exception:
            pass
        try:
            mac_value = iec61850.ClientGooseControlBlock_getDstAddress_addr(gocb)
            info.dst_mac = _format_mac(mac_value)
        except Exception:
            pass

        return info

    def enumerate(self) -> List[GoCBInfo]:
        """
        Discover and read all GOOSE Control Blocks on the server.

        Walks the data model: logical devices -> logical nodes -> GoCB directory,
        then reads each discovered GoCB.

        Returns:
            List of GoCBInfo for all GoCBs on the server

        Raises:
            NotConnectedError: If not connected
            MMSError: If discovery fails
        """
        conn = self._get_connection()
        results = []

        # Get logical devices
        ld_result = iec61850.IedConnection_getLogicalDeviceList(conn)
        ld_value, ld_error, ld_ok = unpack_result(ld_result)
        if not ld_ok:
            raise MMSError(f"Failed to enumerate logical devices: error {ld_error}")

        with LinkedListGuard(ld_value) as ld_guard:
            devices = list(ld_guard)

        for device in devices:
            # Get logical nodes
            ln_result = iec61850.IedConnection_getLogicalNodeList(conn, device)
            ln_value, ln_error, ln_ok = unpack_result(ln_result)
            if not ln_ok:
                continue

            with LinkedListGuard(ln_value) as ln_guard:
                nodes = list(ln_guard)

            for node in nodes:
                reference = f"{device}/{node}"
                acsi_class_gocb = getattr(iec61850, "ACSI_CLASS_GoCB", 7)

                try:
                    dir_result = iec61850.IedConnection_getLogicalNodeDirectory(
                        conn, reference, acsi_class_gocb
                    )
                    dir_value, dir_error, dir_ok = unpack_result(dir_result)
                    if not dir_ok or not dir_value:
                        continue

                    with LinkedListGuard(dir_value) as dir_guard:
                        gocb_names = list(dir_guard)

                    for name in gocb_names:
                        gocb_ref = f"{reference}$GO${name}"
                        try:
                            info = self.read(gocb_ref)
                            results.append(info)
                        except Exception as e:
                            logger.warning(f"Failed to read GoCB {gocb_ref}: {e}")

                except Exception as e:
                    logger.debug(f"Failed to list GoCBs for {reference}: {e}")

        return results

    def __enter__(self) -> "GoCBClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False

#!/usr/bin/env python3
"""
TLS Configuration for IEC 61850 MMS Connections

Provides TLS support for MMSClient and TASE2Client connections
using libiec61850 TLSConfiguration API.

Example:
    from pyiec61850.mms import MMSClient
    from pyiec61850.mms.tls import TLSConfig

    tls = TLSConfig(
        own_cert="client.pem",
        own_key="client-key.pem",
        ca_certs=["ca.pem"],
    )

    with MMSClient() as client:
        client.connect_tls("192.168.1.100", 3782, tls)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    MMSError,
)

logger = logging.getLogger(__name__)


class TLSError(MMSError):
    """Error related to TLS configuration or connection."""

    def __init__(self, message: str = "TLS error"):
        super().__init__(message)


class TLSConfigError(TLSError):
    """Invalid TLS configuration."""

    def __init__(self, reason: str = ""):
        message = "TLS configuration error"
        if reason:
            message += f": {reason}"
        super().__init__(message)


@dataclass
class TLSConfig:
    """
    TLS connection configuration.

    Wraps libiec61850 TLSConfiguration with certificate and key paths.

    Attributes:
        own_cert: Path to own certificate (PEM format)
        own_key: Path to own private key (PEM format)
        ca_certs: List of paths to CA certificate files
        chain_validation: Whether to validate certificate chain
        allow_only_known_certs: Only allow connections to known certificates
    """
    own_cert: str = ""
    own_key: str = ""
    ca_certs: List[str] = field(default_factory=list)
    chain_validation: bool = True
    allow_only_known_certs: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "own_cert": self.own_cert,
            "own_key": self.own_key,
            "ca_certs": self.ca_certs,
            "chain_validation": self.chain_validation,
            "allow_only_known_certs": self.allow_only_known_certs,
        }


def create_tls_configuration(config: TLSConfig) -> Any:
    """
    Create a libiec61850 TLSConfiguration from a TLSConfig.

    Args:
        config: TLSConfig with certificate paths

    Returns:
        Native TLSConfiguration object

    Raises:
        LibraryNotFoundError: If pyiec61850 is not available
        TLSConfigError: If configuration is invalid
        TLSError: If TLS configuration creation fails
    """
    if not _HAS_IEC61850:
        raise LibraryNotFoundError(
            "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
        )

    if not hasattr(iec61850, 'TLSConfiguration_create'):
        raise TLSError("TLS not available in SWIG bindings (requires libiec61850 with TLS)")

    if not config.own_cert:
        raise TLSConfigError("own_cert is required")
    if not config.own_key:
        raise TLSConfigError("own_key is required")

    try:
        tls_config = iec61850.TLSConfiguration_create()
        if not tls_config:
            raise TLSError("Failed to create TLSConfiguration")

        # Set own certificate and key
        iec61850.TLSConfiguration_setOwnCertificateFromFile(
            tls_config, config.own_cert
        )
        iec61850.TLSConfiguration_setOwnKeyFromFile(
            tls_config, config.own_key, None
        )

        # Add CA certificates
        for ca_cert in config.ca_certs:
            iec61850.TLSConfiguration_addCACertificateFromFile(
                tls_config, ca_cert
            )

        # Configure chain validation
        iec61850.TLSConfiguration_setChainValidation(
            tls_config, config.chain_validation
        )
        iec61850.TLSConfiguration_setAllowOnlyKnownCertificates(
            tls_config, config.allow_only_known_certs
        )

        logger.info("TLS configuration created successfully")
        return tls_config

    except (TLSError, TLSConfigError):
        raise
    except Exception as e:
        raise TLSError(f"Failed to create TLS configuration: {e}")


def destroy_tls_configuration(tls_config: Any) -> None:
    """
    Destroy a TLS configuration object.

    Args:
        tls_config: Native TLSConfiguration object
    """
    if not tls_config:
        return

    try:
        if _HAS_IEC61850 and hasattr(iec61850, 'TLSConfiguration_destroy'):
            iec61850.TLSConfiguration_destroy(tls_config)
    except Exception as e:
        logger.warning(f"Error destroying TLS configuration: {e}")


def create_tls_connection(tls_config: Any) -> Any:
    """
    Create an IedConnection with TLS support.

    Args:
        tls_config: Native TLSConfiguration object

    Returns:
        IedConnection with TLS configured

    Raises:
        TLSError: If connection creation fails
    """
    if not _HAS_IEC61850:
        raise LibraryNotFoundError()

    if not hasattr(iec61850, 'IedConnection_createWithTlsSupport'):
        raise TLSError(
            "IedConnection_createWithTlsSupport not available - "
            "rebuild with TLS support"
        )

    try:
        conn = iec61850.IedConnection_createWithTlsSupport(tls_config)
        if not conn:
            raise TLSError("Failed to create TLS-enabled IedConnection")
        return conn
    except TLSError:
        raise
    except Exception as e:
        raise TLSError(f"Failed to create TLS connection: {e}")

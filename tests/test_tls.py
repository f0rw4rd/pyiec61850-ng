#!/usr/bin/env python3
"""
Tests for pyiec61850.mms.tls module - TLS configuration and connections.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestTLSImports(unittest.TestCase):
    """Test TLS module imports."""

    def test_import_tls_config(self):
        from pyiec61850.mms.tls import TLSConfig

        self.assertIsNotNone(TLSConfig)

    def test_import_functions(self):
        from pyiec61850.mms.tls import (
            create_tls_configuration,
            create_tls_connection,
            destroy_tls_configuration,
        )

        self.assertIsNotNone(create_tls_configuration)
        self.assertIsNotNone(destroy_tls_configuration)
        self.assertIsNotNone(create_tls_connection)

    def test_import_exceptions(self):
        from pyiec61850.mms.exceptions import MMSError
        from pyiec61850.mms.tls import TLSConfigError, TLSError

        self.assertTrue(issubclass(TLSError, MMSError))
        self.assertTrue(issubclass(TLSConfigError, TLSError))


class TestTLSConfig(unittest.TestCase):
    """Test TLSConfig dataclass."""

    def test_default_values(self):
        from pyiec61850.mms.tls import TLSConfig

        cfg = TLSConfig()
        self.assertEqual(cfg.own_cert, "")
        self.assertEqual(cfg.own_key, "")
        self.assertEqual(cfg.ca_certs, [])
        self.assertTrue(cfg.chain_validation)
        self.assertFalse(cfg.allow_only_known_certs)

    def test_custom_values(self):
        from pyiec61850.mms.tls import TLSConfig

        cfg = TLSConfig(
            own_cert="client.pem",
            own_key="client-key.pem",
            ca_certs=["ca.pem", "intermediate.pem"],
            chain_validation=False,
            allow_only_known_certs=True,
        )
        self.assertEqual(cfg.own_cert, "client.pem")
        self.assertEqual(cfg.own_key, "client-key.pem")
        self.assertEqual(len(cfg.ca_certs), 2)
        self.assertFalse(cfg.chain_validation)
        self.assertTrue(cfg.allow_only_known_certs)

    def test_to_dict(self):
        from pyiec61850.mms.tls import TLSConfig

        cfg = TLSConfig(own_cert="cert.pem", own_key="key.pem")
        d = cfg.to_dict()
        self.assertEqual(d["own_cert"], "cert.pem")
        self.assertEqual(d["own_key"], "key.pem")
        self.assertIn("chain_validation", d)
        self.assertIn("allow_only_known_certs", d)
        self.assertIn("ca_certs", d)

    def test_ca_certs_independent_instances(self):
        from pyiec61850.mms.tls import TLSConfig

        cfg1 = TLSConfig()
        cfg2 = TLSConfig()
        cfg1.ca_certs.append("test.pem")
        self.assertEqual(len(cfg2.ca_certs), 0)


class TestCreateTLSConfiguration(unittest.TestCase):
    """Test create_tls_configuration function."""

    def test_raises_without_library(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", False):
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            from pyiec61850.mms.tls import TLSConfig, create_tls_configuration

            with self.assertRaises(LibraryNotFoundError):
                create_tls_configuration(TLSConfig(own_cert="cert.pem", own_key="key.pem"))

    def test_raises_without_tls_support(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            mock_iec = Mock(spec=[])  # Empty spec = no attributes
            with patch("pyiec61850.mms.tls.iec61850", mock_iec):
                from pyiec61850.mms.tls import (
                    TLSConfig,
                    TLSError,
                    create_tls_configuration,
                )

                with self.assertRaises(TLSError):
                    create_tls_configuration(TLSConfig(own_cert="cert.pem", own_key="key.pem"))

    def test_raises_without_own_cert(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.TLSConfiguration_create = Mock()
                from pyiec61850.mms.tls import (
                    TLSConfig,
                    TLSConfigError,
                    create_tls_configuration,
                )

                with self.assertRaises(TLSConfigError):
                    create_tls_configuration(TLSConfig(own_key="key.pem"))

    def test_raises_without_own_key(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.TLSConfiguration_create = Mock()
                from pyiec61850.mms.tls import (
                    TLSConfig,
                    TLSConfigError,
                    create_tls_configuration,
                )

                with self.assertRaises(TLSConfigError):
                    create_tls_configuration(TLSConfig(own_cert="cert.pem"))

    def test_success(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_tls = Mock()
                mock_iec.TLSConfiguration_create.return_value = mock_tls

                from pyiec61850.mms.tls import TLSConfig, create_tls_configuration

                config = TLSConfig(
                    own_cert="cert.pem",
                    own_key="key.pem",
                    ca_certs=["ca.pem"],
                )
                result = create_tls_configuration(config)

                self.assertEqual(result, mock_tls)
                mock_iec.TLSConfiguration_create.assert_called_once()
                mock_iec.TLSConfiguration_setOwnCertificateFromFile.assert_called_once_with(
                    mock_tls, "cert.pem"
                )
                mock_iec.TLSConfiguration_setOwnKeyFromFile.assert_called_once_with(
                    mock_tls, "key.pem", None
                )
                mock_iec.TLSConfiguration_addCACertificateFromFile.assert_called_once_with(
                    mock_tls, "ca.pem"
                )
                mock_iec.TLSConfiguration_setChainValidation.assert_called_once_with(mock_tls, True)
                mock_iec.TLSConfiguration_setAllowOnlyKnownCertificates.assert_called_once_with(
                    mock_tls, False
                )

    def test_success_multiple_ca_certs(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_tls = Mock()
                mock_iec.TLSConfiguration_create.return_value = mock_tls

                from pyiec61850.mms.tls import TLSConfig, create_tls_configuration

                config = TLSConfig(
                    own_cert="cert.pem",
                    own_key="key.pem",
                    ca_certs=["ca1.pem", "ca2.pem", "ca3.pem"],
                )
                create_tls_configuration(config)

                self.assertEqual(mock_iec.TLSConfiguration_addCACertificateFromFile.call_count, 3)

    def test_create_returns_none_raises(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.TLSConfiguration_create.return_value = None

                from pyiec61850.mms.tls import (
                    TLSConfig,
                    TLSError,
                    create_tls_configuration,
                )

                with self.assertRaises(TLSError):
                    create_tls_configuration(TLSConfig(own_cert="cert.pem", own_key="key.pem"))

    def test_create_exception_wraps_in_tls_error(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.TLSConfiguration_create.side_effect = RuntimeError("boom")

                from pyiec61850.mms.tls import (
                    TLSConfig,
                    TLSError,
                    create_tls_configuration,
                )

                with self.assertRaises(TLSError):
                    create_tls_configuration(TLSConfig(own_cert="cert.pem", own_key="key.pem"))


class TestDestroyTLSConfiguration(unittest.TestCase):
    """Test destroy_tls_configuration function."""

    def test_destroy_none(self):
        from pyiec61850.mms.tls import destroy_tls_configuration

        # Should not raise
        destroy_tls_configuration(None)

    def test_destroy_success(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                from pyiec61850.mms.tls import destroy_tls_configuration

                mock_tls = Mock()
                destroy_tls_configuration(mock_tls)
                mock_iec.TLSConfiguration_destroy.assert_called_once_with(mock_tls)

    def test_destroy_no_library(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", False):
            from pyiec61850.mms.tls import destroy_tls_configuration

            # Should not raise even without library
            destroy_tls_configuration(Mock())

    def test_destroy_exception_suppressed(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.TLSConfiguration_destroy.side_effect = RuntimeError("boom")
                from pyiec61850.mms.tls import destroy_tls_configuration

                # Should not raise - exceptions suppressed in cleanup
                destroy_tls_configuration(Mock())


class TestCreateTLSConnection(unittest.TestCase):
    """Test create_tls_connection function."""

    def test_raises_without_library(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", False):
            from pyiec61850.mms.exceptions import LibraryNotFoundError
            from pyiec61850.mms.tls import create_tls_connection

            with self.assertRaises(LibraryNotFoundError):
                create_tls_connection(Mock())

    def test_raises_without_tls_support(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            mock_iec = Mock(spec=[])  # No attributes
            with patch("pyiec61850.mms.tls.iec61850", mock_iec):
                from pyiec61850.mms.tls import TLSError, create_tls_connection

                with self.assertRaises(TLSError):
                    create_tls_connection(Mock())

    def test_success(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_conn = Mock()
                mock_iec.IedConnection_createWithTlsSupport.return_value = mock_conn

                from pyiec61850.mms.tls import create_tls_connection

                mock_tls = Mock()
                result = create_tls_connection(mock_tls)

                self.assertEqual(result, mock_conn)
                mock_iec.IedConnection_createWithTlsSupport.assert_called_once_with(mock_tls)

    def test_returns_none_raises(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.IedConnection_createWithTlsSupport.return_value = None

                from pyiec61850.mms.tls import TLSError, create_tls_connection

                with self.assertRaises(TLSError):
                    create_tls_connection(Mock())

    def test_exception_wraps_in_tls_error(self):
        with patch("pyiec61850.mms.tls._HAS_IEC61850", True):
            with patch("pyiec61850.mms.tls.iec61850") as mock_iec:
                mock_iec.IedConnection_createWithTlsSupport.side_effect = RuntimeError("boom")

                from pyiec61850.mms.tls import TLSError, create_tls_connection

                with self.assertRaises(TLSError):
                    create_tls_connection(Mock())


if __name__ == "__main__":
    unittest.main()

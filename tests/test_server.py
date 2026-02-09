#!/usr/bin/env python3
"""
Tests for pyiec61850.server module - IEC 61850 server.

All tests use mocks since the C library isn't available in dev.
"""

import logging
import unittest
from unittest.mock import Mock, patch

logging.disable(logging.CRITICAL)


class TestServerImports(unittest.TestCase):
    """Test server module imports."""

    def test_import_module(self):
        from pyiec61850 import server

        self.assertIsNotNone(server)

    def test_import_server(self):
        from pyiec61850.server import IedServer

        self.assertIsNotNone(IedServer)

    def test_import_types(self):
        from pyiec61850.server import ServerConfig

        self.assertIsNotNone(ServerConfig)

    def test_import_exceptions(self):
        from pyiec61850.server import (
            ModelError,
            ServerError,
            UpdateError,
        )

        self.assertTrue(issubclass(ModelError, ServerError))
        self.assertTrue(issubclass(UpdateError, ServerError))

    def test_import_constants(self):
        from pyiec61850.server import (
            CONTROL_ACCEPTED,
        )

        self.assertEqual(CONTROL_ACCEPTED, 0)


class TestServerConfig(unittest.TestCase):
    """Test ServerConfig dataclass."""

    def test_default_values(self):
        from pyiec61850.server import ServerConfig

        cfg = ServerConfig()
        self.assertEqual(cfg.port, 102)
        self.assertEqual(cfg.max_connections, 5)
        self.assertFalse(cfg.enable_goose_publishing)

    def test_custom_values(self):
        from pyiec61850.server import ServerConfig

        cfg = ServerConfig(port=8102, max_connections=20, enable_goose_publishing=True)
        self.assertEqual(cfg.port, 8102)
        self.assertEqual(cfg.max_connections, 20)
        self.assertTrue(cfg.enable_goose_publishing)

    def test_to_dict(self):
        from pyiec61850.server import ServerConfig

        cfg = ServerConfig(port=102)
        d = cfg.to_dict()
        self.assertEqual(d["port"], 102)
        self.assertIn("max_connections", d)


class TestIedServer(unittest.TestCase):
    """Test IedServer class."""

    def test_raises_without_library(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", False):
            from pyiec61850.server import IedServer, LibraryNotFoundError

            with self.assertRaises(LibraryNotFoundError):
                IedServer()

    def test_creation_without_model(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer

                srv = IedServer()
                self.assertFalse(srv.is_running)
                self.assertEqual(srv.port, 102)

    def test_creation_with_model(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_model = Mock()
                mock_iec.IedModel_createFromConfigFile.return_value = mock_model

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                self.assertEqual(srv._model, mock_model)

    def test_creation_with_bad_model(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = None

                from pyiec61850.server import IedServer, ModelError

                with self.assertRaises(ModelError):
                    IedServer("bad_model.cfg")

    def test_start_success(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_model = Mock()
                mock_iec.IedModel_createFromConfigFile.return_value = mock_model
                mock_server = Mock()
                # MagicMock has IedServerConfig_create, so createWithConfig path is taken
                mock_iec.IedServer_createWithConfig.return_value = mock_server
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start(8102)

                self.assertTrue(srv.is_running)
                self.assertEqual(srv.port, 8102)
                mock_iec.IedServer_start.assert_called_once_with(mock_server, 8102)

    def test_start_already_running(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import AlreadyRunningError, IedServer

                srv = IedServer("model.cfg")
                srv.start()
                with self.assertRaises(AlreadyRunningError):
                    srv.start()

    def test_start_no_model(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, ModelError

                srv = IedServer()
                with self.assertRaises(ModelError):
                    srv.start()

    def test_start_failed(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = False

                from pyiec61850.server import IedServer, ServerError

                srv = IedServer("model.cfg")
                with self.assertRaises(ServerError):
                    srv.start()

    def test_stop(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_server = Mock()
                mock_iec.IedServer_create.return_value = mock_server
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.stop()

                self.assertFalse(srv.is_running)
                mock_iec.IedServer_stop.assert_called_once()
                mock_iec.IedServer_destroy.assert_called_once()

    def test_stop_when_not_running(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer

                srv = IedServer()
                srv.stop()  # Should not raise

    def test_update_boolean(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_node = Mock()
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = mock_node

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_boolean("myLD/GGIO1.Ind1.stVal", True)

                mock_iec.IedServer_updateBooleanAttributeValue.assert_called_once()

    def test_update_boolean_not_running(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, NotRunningError

                srv = IedServer()
                with self.assertRaises(NotRunningError):
                    srv.update_boolean("test", True)

    def test_update_boolean_node_not_found(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = None

                from pyiec61850.server import IedServer, UpdateError

                srv = IedServer("model.cfg")
                srv.start()
                with self.assertRaises(UpdateError):
                    srv.update_boolean("nonexistent", True)

    def test_update_float(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_float("myLD/MMXU1.TotW.mag.f", 1234.5)

                mock_iec.IedServer_updateFloatAttributeValue.assert_called_once()

    def test_update_int32(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_int32("myLD/GGIO1.SPCSO1.stVal", 42)

                mock_iec.IedServer_updateInt32AttributeValue.assert_called_once()

    def test_context_manager(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_create.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer

                with IedServer("model.cfg") as srv:
                    srv.start()
                    self.assertTrue(srv.is_running)

                self.assertFalse(srv.is_running)
                mock_iec.IedServer_stop.assert_called()

    def test_lock_unlock_data_model(self):
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_server = Mock()
                mock_iec.IedServer_create.return_value = mock_server
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.lock_data_model()
                srv.unlock_data_model()

                mock_iec.IedServer_lockDataModel.assert_called_once()
                mock_iec.IedServer_unlockDataModel.assert_called_once()


if __name__ == "__main__":
    unittest.main()

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


class TestIedServerCrashPaths(unittest.TestCase):
    """Test IedServer crash paths: start/stop, cleanup ordering, model loading."""

    def test_load_model_fallback_api(self):
        """_load_model must fall back to ConfigFileParser if IedModel not available."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                del mock_iec.IedModel_createFromConfigFile
                mock_iec.ConfigFileParser_createModelFromConfigFile.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                self.assertIsNotNone(srv._model)

    def test_load_model_no_api_available(self):
        """_load_model with no loading API must raise ModelError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                del mock_iec.IedModel_createFromConfigFile
                del mock_iec.ConfigFileParser_createModelFromConfigFile

                from pyiec61850.server import IedServer, ModelError

                with self.assertRaises(ModelError):
                    IedServer("model.cfg")

    def test_load_model_exception_wraps(self):
        """_load_model must wrap unexpected exceptions in ModelError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.side_effect = RuntimeError("disk fail")

                from pyiec61850.server import IedServer, ModelError

                with self.assertRaises(ModelError):
                    IedServer("model.cfg")

    def test_start_server_create_null(self):
        """IedServer_create returning NULL must raise ServerError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                # Remove config API so it falls through to IedServer_create
                del mock_iec.IedServerConfig_create
                mock_iec.IedServer_create.return_value = None

                from pyiec61850.server import IedServer, ServerError

                srv = IedServer("model.cfg")
                with self.assertRaises(ServerError):
                    srv.start()

    def test_start_unexpected_exception_triggers_cleanup(self):
        """Unexpected exception during start must trigger _cleanup."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_start.side_effect = RuntimeError("bind failed")

                from pyiec61850.server import IedServer, ServerError

                srv = IedServer("model.cfg")
                with self.assertRaises(ServerError):
                    srv.start()

                self.assertIsNone(srv._server)

    def test_start_with_goose_publishing(self):
        """start() with enable_goose_publishing must call enableGoosePublishing."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer, ServerConfig

                cfg = ServerConfig(enable_goose_publishing=True)
                srv = IedServer("model.cfg", config=cfg)
                srv.start()

                mock_iec.IedServer_enableGoosePublishing.assert_called()

    def test_start_goose_publishing_failure_no_crash(self):
        """If enableGoosePublishing fails, start() must continue."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedServer_enableGoosePublishing.side_effect = RuntimeError("fail")

                from pyiec61850.server import IedServer, ServerConfig

                cfg = ServerConfig(enable_goose_publishing=True)
                srv = IedServer("model.cfg", config=cfg)
                srv.start()  # Must not raise

                self.assertTrue(srv.is_running)

    def test_cleanup_destroy_exception_still_clears(self):
        """If IedServer_destroy throws, references must still be cleared."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedServer_destroy.side_effect = RuntimeError("destroy failed")

                from pyiec61850.server import IedServer

                srv = IedServer()
                srv._running = True
                srv._server = Mock()
                srv._model = Mock()

                srv.stop()  # Must not raise

                self.assertIsNone(srv._server)
                self.assertIsNone(srv._model)
                self.assertFalse(srv.is_running)

    def test_cleanup_config_destroy_exception_no_crash(self):
        """If IedServerConfig_destroy throws, cleanup must continue."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedServerConfig_destroy.side_effect = RuntimeError("fail")

                from pyiec61850.server import IedServer

                srv = IedServer()
                srv._running = True
                srv._server = Mock()
                srv._ied_server_config = Mock()
                srv._model = Mock()

                srv.stop()  # Must not raise

                self.assertIsNone(srv._ied_server_config)

    def test_stop_server_stop_exception_still_cleans_up(self):
        """If IedServer_stop throws, cleanup must still happen."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedServer_stop.side_effect = RuntimeError("stop failed")

                from pyiec61850.server import IedServer

                srv = IedServer()
                srv._running = True
                srv._server = Mock()
                srv._model = Mock()

                srv.stop()  # Must not raise

                self.assertFalse(srv.is_running)
                mock_iec.IedServer_destroy.assert_called_once()

    def test_double_stop_no_crash(self):
        """Calling stop() twice must not crash."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.stop()
                srv.stop()  # Must be no-op
                self.assertFalse(srv.is_running)

    def test_update_visible_string(self):
        """update_visible_string must call the correct C function."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_visible_string("myLD/LLN0.NamPlt.vendor", "test")

                mock_iec.IedServer_updateVisibleStringAttributeValue.assert_called_once()

    def test_update_quality(self):
        """update_quality must call the correct C function."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_quality("myLD/MMXU1.TotW.q", 0)

                mock_iec.IedServer_updateQuality.assert_called_once()

    def test_update_timestamp(self):
        """update_timestamp must call the correct C function."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = Mock()

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                srv.update_timestamp("myLD/MMXU1.TotW.t", 1704067200000)

                mock_iec.IedServer_updateUTCTimeAttributeValue.assert_called_once()

    def test_update_functions_node_not_found(self):
        """All update functions must raise UpdateError when node not found."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = None

                from pyiec61850.server import IedServer, UpdateError

                srv = IedServer("model.cfg")
                srv.start()

                with self.assertRaises(UpdateError):
                    srv.update_visible_string("bad", "val")
                with self.assertRaises(UpdateError):
                    srv.update_quality("bad", 0)
                with self.assertRaises(UpdateError):
                    srv.update_timestamp("bad", 0)

    def test_set_control_handler_not_running(self):
        """set_control_handler when not running must raise NotRunningError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, NotRunningError

                srv = IedServer()
                with self.assertRaises(NotRunningError):
                    srv.set_control_handler("test", Mock())

    def test_set_control_handler_not_callable(self):
        """set_control_handler with non-callable must raise ControlHandlerError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True

                from pyiec61850.server import ControlHandlerError, IedServer

                srv = IedServer("model.cfg")
                srv.start()
                with self.assertRaises(ControlHandlerError):
                    srv.set_control_handler("test", "not_callable")

    def test_set_control_handler_node_not_found(self):
        """set_control_handler with missing node must raise ControlHandlerError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedModel_getModelNodeByObjectReference.return_value = None

                from pyiec61850.server import ControlHandlerError, IedServer

                srv = IedServer("model.cfg")
                srv.start()
                with self.assertRaises(ControlHandlerError):
                    srv.set_control_handler("nonexistent", Mock())

    def test_enable_goose_publishing_not_running(self):
        """enable_goose_publishing when not running must raise NotRunningError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, NotRunningError

                srv = IedServer()
                with self.assertRaises(NotRunningError):
                    srv.enable_goose_publishing()

    def test_disable_goose_publishing_not_running(self):
        """disable_goose_publishing when not running must raise NotRunningError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, NotRunningError

                srv = IedServer()
                with self.assertRaises(NotRunningError):
                    srv.disable_goose_publishing()

    def test_get_number_of_open_connections_not_running(self):
        """get_number_of_open_connections when not running must raise NotRunningError."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850"):
                from pyiec61850.server import IedServer, NotRunningError

                srv = IedServer()
                with self.assertRaises(NotRunningError):
                    srv.get_number_of_open_connections()

    def test_get_number_of_open_connections_exception_returns_zero(self):
        """get_number_of_open_connections exception must return 0."""
        with patch("pyiec61850.server.server._HAS_IEC61850", True):
            with patch("pyiec61850.server.server.iec61850") as mock_iec:
                mock_iec.IedModel_createFromConfigFile.return_value = Mock()
                mock_iec.IedServer_createWithConfig.return_value = Mock()
                mock_iec.IedServer_isRunning.return_value = True
                mock_iec.IedServer_getNumberOfOpenConnections.side_effect = RuntimeError("fail")

                from pyiec61850.server import IedServer

                srv = IedServer("model.cfg")
                srv.start()
                count = srv.get_number_of_open_connections()
                self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

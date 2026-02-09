#!/usr/bin/env python3
"""
IEC 61850 Server

High-level wrapper for libiec61850 IedServer providing
IEC 61850 MMS server functionality with data model management,
control handlers, and GOOSE publishing.

Example:
    from pyiec61850.server import IedServer

    with IedServer("model.cfg") as server:
        server.start(102)
        server.update_boolean("myLD/GGIO1.Ind1.stVal", True)
        # ... serve clients ...
        server.stop()
"""

from typing import Any, Callable, Dict, List, Optional
import logging

try:
    import pyiec61850.pyiec61850 as iec61850
    _HAS_IEC61850 = True
except ImportError:
    _HAS_IEC61850 = False
    iec61850 = None

from .exceptions import (
    LibraryNotFoundError,
    ModelError,
    ConfigurationError,
    NotRunningError,
    AlreadyRunningError,
    UpdateError,
    ControlHandlerError,
    ServerError,
)
from .types import ServerConfig, ClientConnection

logger = logging.getLogger(__name__)


class IedServer:
    """
    High-level IEC 61850 MMS Server.

    Wraps libiec61850 IedServer with proper resource management
    and a Python-friendly interface for serving IEC 61850 data.

    Attributes:
        is_running: Whether the server is currently running
        port: Port the server is listening on

    Example:
        server = IedServer("model.cfg")
        server.start(102)
        server.update_float("myLD/MMXU1.TotW.mag.f", 1234.5)
        server.stop()
    """

    def __init__(self, model_path: Optional[str] = None, config: Optional[ServerConfig] = None):
        """
        Initialize IEC 61850 server.

        Args:
            model_path: Path to ICD/SCL model file, or None for runtime model
            config: Server configuration (uses defaults if None)

        Raises:
            LibraryNotFoundError: If pyiec61850 is not available
            ModelError: If model file cannot be loaded
        """
        if not _HAS_IEC61850:
            raise LibraryNotFoundError(
                "pyiec61850 library not found. Install with: pip install pyiec61850-ng"
            )

        self._config = config or ServerConfig()
        self._model = None
        self._server = None
        self._ied_server_config = None
        self._running = False
        self._port = self._config.port

        # Control handler references (prevent GC)
        self._control_subscribers: Dict[str, Any] = {}
        self._control_handlers: Dict[str, Any] = {}

        # Load model if path provided
        if model_path:
            self._load_model(model_path)

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def port(self) -> int:
        """Return the configured port."""
        return self._port

    def _load_model(self, model_path: str) -> None:
        """Load the IEC 61850 data model from file."""
        try:
            if hasattr(iec61850, 'IedModel_createFromConfigFile'):
                self._model = iec61850.IedModel_createFromConfigFile(model_path)
            elif hasattr(iec61850, 'ConfigFileParser_createModelFromConfigFile'):
                self._model = iec61850.ConfigFileParser_createModelFromConfigFile(
                    model_path
                )
            else:
                raise ModelError("No model loading API available in bindings")

            if not self._model:
                raise ModelError(f"Failed to load model from '{model_path}'")

            logger.info(f"Loaded IEC 61850 model from {model_path}")

        except ModelError:
            raise
        except Exception as e:
            raise ModelError(f"Failed to load model from '{model_path}': {e}")

    def start(self, port: int = 102) -> None:
        """
        Start the IEC 61850 server.

        Args:
            port: TCP port to listen on (default 102)

        Raises:
            AlreadyRunningError: If server is already running
            ServerError: If server fails to start
            ModelError: If no model is loaded
        """
        if self._running:
            raise AlreadyRunningError()

        if not self._model:
            raise ModelError("No data model loaded")

        try:
            self._port = port

            # Create server configuration
            if hasattr(iec61850, 'IedServerConfig_create'):
                self._ied_server_config = iec61850.IedServerConfig_create()
                if self._ied_server_config:
                    if hasattr(iec61850, 'IedServerConfig_setMaxMmsConnections'):
                        iec61850.IedServerConfig_setMaxMmsConnections(
                            self._ied_server_config, self._config.max_connections
                        )
                    if self._config.file_service_base_path and hasattr(
                        iec61850, 'IedServerConfig_setFileServiceBasePath'
                    ):
                        iec61850.IedServerConfig_setFileServiceBasePath(
                            self._ied_server_config,
                            self._config.file_service_base_path,
                        )
                    if hasattr(iec61850, 'IedServerConfig_setEdition'):
                        iec61850.IedServerConfig_setEdition(
                            self._ied_server_config, self._config.edition
                        )
                    if hasattr(iec61850, 'IedServerConfig_enableDynamicDataSetService'):
                        iec61850.IedServerConfig_enableDynamicDataSetService(
                            self._ied_server_config,
                            self._config.enable_dynamic_datasets,
                        )
                    if hasattr(iec61850, 'IedServerConfig_enableFileService'):
                        iec61850.IedServerConfig_enableFileService(
                            self._ied_server_config,
                            self._config.enable_file_service,
                        )

            # Create IED server
            if self._ied_server_config and hasattr(iec61850, 'IedServer_createWithConfig'):
                self._server = iec61850.IedServer_createWithConfig(
                    self._model, None, self._ied_server_config
                )
            else:
                self._server = iec61850.IedServer_create(self._model)

            if not self._server:
                raise ServerError("Failed to create IedServer")

            # Start server
            iec61850.IedServer_start(self._server, port)

            if not iec61850.IedServer_isRunning(self._server):
                raise ServerError(
                    f"Server failed to start on port {port} "
                    "(port may be in use or insufficient permissions)"
                )

            # Enable GOOSE publishing if configured
            if self._config.enable_goose_publishing:
                try:
                    iec61850.IedServer_enableGoosePublishing(self._server)
                    logger.info("GOOSE publishing enabled")
                except Exception as e:
                    logger.warning(f"Failed to enable GOOSE publishing: {e}")

            self._running = True
            logger.info(f"IEC 61850 server started on port {port}")

        except (AlreadyRunningError, ModelError, ServerError):
            raise
        except Exception as e:
            self._cleanup()
            raise ServerError(f"Failed to start server: {e}")

    def stop(self) -> None:
        """
        Stop the IEC 61850 server.

        Safe to call multiple times.
        """
        if not self._running:
            return

        logger.info("Stopping IEC 61850 server")
        self._running = False

        try:
            if self._server:
                iec61850.IedServer_stop(self._server)
        except Exception as e:
            logger.warning(f"Error stopping server: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up all native resources."""
        self._control_subscribers.clear()
        self._control_handlers.clear()

        if self._server:
            try:
                iec61850.IedServer_destroy(self._server)
            except Exception as e:
                logger.warning(f"Error destroying IedServer: {e}")
        self._server = None

        if self._ied_server_config:
            try:
                if hasattr(iec61850, 'IedServerConfig_destroy'):
                    iec61850.IedServerConfig_destroy(self._ied_server_config)
            except Exception:
                pass
        self._ied_server_config = None

        if self._model:
            try:
                iec61850.IedModel_destroy(self._model)
            except Exception as e:
                logger.warning(f"Error destroying model: {e}")
        self._model = None
        self._running = False

    def update_boolean(self, reference: str, value: bool) -> None:
        """
        Update a boolean data attribute value.

        Args:
            reference: Full data attribute reference (e.g., "myLD/GGIO1.Ind1.stVal")
            value: Boolean value

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateBooleanAttributeValue(
                self._server, node, value
            )
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def update_int32(self, reference: str, value: int) -> None:
        """
        Update an INT32 data attribute value.

        Args:
            reference: Full data attribute reference
            value: Integer value

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateInt32AttributeValue(
                self._server, node, value
            )
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def update_float(self, reference: str, value: float) -> None:
        """
        Update a float data attribute value.

        Args:
            reference: Full data attribute reference
            value: Float value

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateFloatAttributeValue(
                self._server, node, value
            )
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def update_visible_string(self, reference: str, value: str) -> None:
        """
        Update a visible string data attribute value.

        Args:
            reference: Full data attribute reference
            value: String value

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateVisibleStringAttributeValue(
                self._server, node, value
            )
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def update_quality(self, reference: str, quality: int) -> None:
        """
        Update a quality data attribute value.

        Args:
            reference: Full data attribute reference (typically ending in ".q")
            quality: Quality bitstring value

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateQuality(self._server, node, quality)
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def update_timestamp(self, reference: str, timestamp_ms: int) -> None:
        """
        Update a UTC timestamp data attribute value.

        Args:
            reference: Full data attribute reference (typically ending in ".t")
            timestamp_ms: Timestamp in milliseconds since epoch

        Raises:
            NotRunningError: If server is not running
            UpdateError: If update fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, reference
            )
            if not node:
                raise UpdateError(reference, "node not found in model")

            iec61850.IedServer_updateUTCTimeAttributeValue(
                self._server, node, timestamp_ms
            )
        except NotRunningError:
            raise
        except UpdateError:
            raise
        except Exception as e:
            raise UpdateError(reference, str(e))

    def set_control_handler(
        self,
        object_ref: str,
        handler: Callable,
    ) -> None:
        """
        Set a control handler for a controllable data object.

        The handler callback will be invoked by the server when a client
        issues a control command on the specified object.

        Args:
            object_ref: Full data object reference (e.g., "myLD/CSWI1.Pos")
            handler: Callable that receives (control_action, value, test)
                     and returns a ControlHandlerResult

        Raises:
            NotRunningError: If server is not running
            ControlHandlerError: If handler setup fails
        """
        if not self._running:
            raise NotRunningError()

        if not callable(handler):
            raise ControlHandlerError("handler must be callable")

        try:
            node = iec61850.IedModel_getModelNodeByObjectReference(
                self._model, object_ref
            )
            if not node:
                raise ControlHandlerError(
                    f"control object '{object_ref}' not found in model"
                )

            if hasattr(iec61850, 'ControlSubscriberForPython'):
                ctrl_sub = iec61850.ControlSubscriberForPython()
                ctrl_sub.setIedServer(self._server)
                ctrl_sub.setControlObject(node)

                ctrl_handler = _PyControlHandler(handler, object_ref)
                ctrl_sub.setControlHandler(ctrl_handler)
                ctrl_sub.subscribe()

                self._control_subscribers[object_ref] = ctrl_sub
                self._control_handlers[object_ref] = ctrl_handler
            else:
                logger.warning(
                    "ControlSubscriberForPython not available in SWIG bindings"
                )

            logger.info(f"Control handler installed for {object_ref}")

        except NotRunningError:
            raise
        except ControlHandlerError:
            raise
        except Exception as e:
            raise ControlHandlerError(str(e))

    def enable_goose_publishing(self) -> None:
        """
        Enable GOOSE publishing on the server.

        Raises:
            NotRunningError: If server is not running
            ServerError: If enable fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            iec61850.IedServer_enableGoosePublishing(self._server)
            logger.info("GOOSE publishing enabled")
        except Exception as e:
            raise ServerError(f"Failed to enable GOOSE publishing: {e}")

    def disable_goose_publishing(self) -> None:
        """
        Disable GOOSE publishing on the server.

        Raises:
            NotRunningError: If server is not running
            ServerError: If disable fails
        """
        if not self._running:
            raise NotRunningError()

        try:
            iec61850.IedServer_disableGoosePublishing(self._server)
            logger.info("GOOSE publishing disabled")
        except Exception as e:
            raise ServerError(f"Failed to disable GOOSE publishing: {e}")

    def get_number_of_open_connections(self) -> int:
        """
        Get the number of currently open client connections.

        Returns:
            Number of connected clients

        Raises:
            NotRunningError: If server is not running
        """
        if not self._running:
            raise NotRunningError()

        try:
            return iec61850.IedServer_getNumberOfOpenConnections(self._server)
        except Exception:
            return 0

    def lock_data_model(self) -> None:
        """
        Lock the data model for atomic updates.

        Call this before updating multiple values that should be
        consistent, then call unlock_data_model() when done.

        Raises:
            NotRunningError: If server is not running
        """
        if not self._running:
            raise NotRunningError()
        iec61850.IedServer_lockDataModel(self._server)

    def unlock_data_model(self) -> None:
        """
        Unlock the data model after atomic updates.

        Raises:
            NotRunningError: If server is not running
        """
        if not self._running:
            raise NotRunningError()
        iec61850.IedServer_unlockDataModel(self._server)

    def __enter__(self) -> 'IedServer':
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


class _PyControlHandler:
    """
    Python-side control handler (SWIG director subclass).

    Receives control actions from the C++ layer and delivers
    them to the Python callback.
    """

    def __init__(self, callback: Callable, object_ref: str):
        self._callback = callback
        self._object_ref = object_ref

        if _HAS_IEC61850 and hasattr(iec61850, 'ControlHandlerForPython'):
            try:
                iec61850.ControlHandlerForPython.__init__(self)
            except Exception:
                pass

    def trigger(self):
        """Called by C++ subscriber when a control action arrives."""
        try:
            value = None
            test = False

            try:
                value = self._libiec61850_mms_value
            except Exception:
                pass
            try:
                test = self._libiec61850_test
            except Exception:
                pass

            if self._callback:
                try:
                    result = self._callback(self._object_ref, value, test)
                    if result is not None:
                        self._libiec61850_control_handler_result = result
                except Exception as e:
                    logger.warning(f"Control handler callback error: {e}")

        except Exception as e:
            logger.warning(f"Control handler error: {e}")

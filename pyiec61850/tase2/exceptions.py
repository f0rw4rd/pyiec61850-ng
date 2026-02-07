#!/usr/bin/env python3
"""
TASE.2/ICCP Exceptions

Exception hierarchy for TASE.2 protocol errors.
"""


class TASE2Error(Exception):
    """Base exception for all TASE.2 errors."""

    def __init__(self, message: str = "TASE.2 error", code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)


# Library Errors
class LibraryError(TASE2Error):
    """Error related to the underlying library."""
    pass


class LibraryNotFoundError(LibraryError):
    """pyiec61850 library not available."""

    def __init__(self, message: str = "pyiec61850 library not found"):
        super().__init__(message)


# Connection Errors
class TASE2ConnectionError(TASE2Error):
    """Base class for connection-related errors."""
    pass


# Backward compatibility alias (deprecated - shadows builtins.ConnectionError)
ConnectionError = TASE2ConnectionError


class ConnectionFailedError(ConnectionError):
    """Failed to establish connection."""

    def __init__(self, host: str = "", port: int = 102, reason: str = ""):
        message = f"Failed to connect to {host}:{port}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.host = host
        self.port = port


class ConnectionTimeoutError(ConnectionError):
    """Connection timed out."""

    def __init__(self, timeout: int = 0):
        message = f"Connection timed out after {timeout}ms"
        super().__init__(message)
        self.timeout = timeout


class ConnectionClosedError(ConnectionError):
    """Connection was closed unexpectedly."""

    def __init__(self, reason: str = ""):
        message = "Connection closed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class NotConnectedError(ConnectionError):
    """Operation attempted while not connected."""

    def __init__(self, operation: str = ""):
        message = "Not connected to server"
        if operation:
            message = f"Cannot {operation}: not connected"
        super().__init__(message)


class AssociationError(ConnectionError):
    """Error establishing TASE.2 association."""

    def __init__(self, reason: str = ""):
        message = "Association failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


# Authentication Errors
class AuthenticationError(TASE2Error):
    """Base class for authentication-related errors."""
    pass


class AccessDeniedError(AuthenticationError):
    """Access to resource was denied."""

    def __init__(self, resource: str = ""):
        message = "Access denied"
        if resource:
            message += f" to {resource}"
        super().__init__(message)
        self.resource = resource


class BilateralTableError(AuthenticationError):
    """Error related to bilateral table validation."""

    def __init__(self, reason: str = ""):
        message = "Bilateral table error"
        if reason:
            message += f": {reason}"
        super().__init__(message)


# Operation Errors
class OperationError(TASE2Error):
    """Base class for operation-related errors."""
    pass


class TASE2TimeoutError(OperationError):
    """Operation timed out."""

    def __init__(self, operation: str = "", timeout: int = 0):
        message = "Operation timed out"
        if operation:
            message = f"{operation} timed out"
        if timeout:
            message += f" after {timeout}ms"
        super().__init__(message)
        self.timeout = timeout


# Backward compatibility alias (deprecated - shadows builtins.TimeoutError)
TimeoutError = TASE2TimeoutError


class InvalidParameterError(OperationError):
    """Invalid parameter provided."""

    def __init__(self, parameter: str = "", reason: str = ""):
        message = "Invalid parameter"
        if parameter:
            message = f"Invalid parameter: {parameter}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.parameter = parameter


class ResourceNotFoundError(OperationError):
    """Requested resource not found."""

    def __init__(self, resource_type: str = "resource", name: str = ""):
        message = f"{resource_type} not found"
        if name:
            message = f"{resource_type} '{name}' not found"
        super().__init__(message)
        self.resource_type = resource_type
        self.name = name


class DomainNotFoundError(ResourceNotFoundError):
    """Domain not found."""

    def __init__(self, domain: str = ""):
        super().__init__("Domain", domain)


class VariableNotFoundError(ResourceNotFoundError):
    """Variable not found."""

    def __init__(self, variable: str = "", domain: str = ""):
        name = f"{domain}/{variable}" if domain else variable
        super().__init__("Variable", name)


class DataSetNotFoundError(ResourceNotFoundError):
    """Data set not found."""

    def __init__(self, data_set: str = "", domain: str = ""):
        name = f"{domain}/{data_set}" if domain else data_set
        super().__init__("Data set", name)


class TransferSetNotFoundError(ResourceNotFoundError):
    """Transfer set not found."""

    def __init__(self, transfer_set: str = "", domain: str = ""):
        name = f"{domain}/{transfer_set}" if domain else transfer_set
        super().__init__("Transfer set", name)


# Data Access Errors
class DataAccessError(TASE2Error):
    """Base class for data access errors."""
    pass


class ReadError(DataAccessError):
    """Error reading data point."""

    def __init__(self, variable: str = "", reason: str = ""):
        message = "Read failed"
        if variable:
            message = f"Failed to read '{variable}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.variable = variable


class WriteError(DataAccessError):
    """Error writing data point."""

    def __init__(self, variable: str = "", reason: str = ""):
        message = "Write failed"
        if variable:
            message = f"Failed to write '{variable}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.variable = variable


class TypeMismatchError(DataAccessError):
    """Type mismatch between expected and actual value."""

    def __init__(self, expected: str = "", actual: str = ""):
        message = "Type mismatch"
        if expected and actual:
            message = f"Type mismatch: expected {expected}, got {actual}"
        super().__init__(message)
        self.expected = expected
        self.actual = actual


# Control Errors (Block 5)
class ControlError(TASE2Error):
    """Base class for control operation errors."""
    pass


class ControlNotSupportedError(ControlError):
    """Control operations not supported (Block 5 not available)."""

    def __init__(self):
        super().__init__("Control operations not supported (Block 5 not available)")


class SelectError(ControlError):
    """Select-before-operate selection failed."""

    def __init__(self, device: str = "", reason: str = ""):
        message = "Select failed"
        if device:
            message = f"Failed to select '{device}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.device = device


class OperateError(ControlError):
    """Operate command failed."""

    def __init__(self, device: str = "", reason: str = ""):
        message = "Operate failed"
        if device:
            message = f"Failed to operate '{device}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.device = device


class TagError(ControlError):
    """Tag operation failed."""

    def __init__(self, device: str = "", reason: str = ""):
        message = "Tag operation failed"
        if device:
            message = f"Tag operation failed for '{device}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.device = device


class DeviceBlockedError(ControlError):
    """Device is blocked/tagged and cannot be operated."""

    def __init__(self, device: str = ""):
        message = "Device is blocked"
        if device:
            message = f"Device '{device}' is blocked"
        super().__init__(message)
        self.device = device


# Information Message Errors (Block 4)
class InformationMessageError(TASE2Error):
    """Base class for information message errors (Block 4)."""
    pass


class IMTransferSetError(InformationMessageError):
    """Error related to IM Transfer Set operations."""

    def __init__(self, reason: str = ""):
        message = "IM Transfer Set error"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class IMNotSupportedError(InformationMessageError):
    """Information messages not supported (Block 4 not available)."""

    def __init__(self):
        super().__init__("Information messages not supported (Block 4 not available)")


# Transfer Set Errors (Block 2)
class TransferSetError(TASE2Error):
    """Base class for transfer set errors."""
    pass


class RBENotSupportedError(TransferSetError):
    """Report-by-exception not supported (Block 2 not available)."""

    def __init__(self):
        super().__init__("Report-by-exception not supported (Block 2 not available)")


class TransferSetConfigError(TransferSetError):
    """Transfer set configuration error."""

    def __init__(self, transfer_set: str = "", reason: str = ""):
        message = "Transfer set configuration error"
        if transfer_set:
            message = f"Failed to configure transfer set '{transfer_set}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.transfer_set = transfer_set


# Protocol Errors
class ProtocolError(TASE2Error):
    """Base class for protocol-level errors."""
    pass


class ServiceError(ProtocolError):
    """MMS service error."""

    def __init__(self, service: str = "", code: int = 0):
        message = "Service error"
        if service:
            message = f"Service '{service}' error"
        if code:
            message += f" (code: {code})"
        super().__init__(message, code)
        self.service = service


class RejectError(ProtocolError):
    """Request was rejected by server."""

    def __init__(self, reason: str = ""):
        message = "Request rejected"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class AbortError(ProtocolError):
    """Connection was aborted."""

    def __init__(self, reason: str = ""):
        message = "Connection aborted"
        if reason:
            message += f": {reason}"
        super().__init__(message)


def map_ied_error(error_code: int, context: str = "") -> TASE2Error:
    """
    Map libiec61850 IedClientError code to appropriate TASE2 exception.

    Args:
        error_code: IED error code from libiec61850
        context: Optional context string describing the operation

    Returns:
        Appropriate TASE2Error subclass instance
    """
    # Get error code values from library, with fallbacks matching
    # libiec61850's IedClientError enum
    try:
        import pyiec61850.pyiec61850 as iec61850
        _get = lambda name, default: getattr(iec61850, name, default)
    except ImportError:
        _get = lambda name, default: default

    error_map = {
        _get('IED_ERROR_ALREADY_CONNECTED', 1): lambda: TASE2Error(f"Already connected: {context}"),
        _get('IED_ERROR_NOT_CONNECTED', 2): lambda: NotConnectedError(context),
        _get('IED_ERROR_ACCESS_DENIED', 3): lambda: AccessDeniedError(context),
        _get('IED_ERROR_OBJECT_REFERENCE_INVALID', 4): lambda: InvalidParameterError(context, "invalid object reference"),
        _get('IED_ERROR_OBJECT_DOES_NOT_EXIST', 5): lambda: VariableNotFoundError(context),
        _get('IED_ERROR_OBJECT_EXISTS', 6): lambda: TASE2Error(f"Object already exists: {context}"),
        _get('IED_ERROR_TIMEOUT', 7): lambda: TASE2TimeoutError(context),
        _get('IED_ERROR_ENABLE_REPORT_FAILED_DATASET_MISMATCH', 8): lambda: TransferSetConfigError(context, "dataset mismatch"),
        _get('IED_ERROR_TYPE_INCONSISTENT', 9): lambda: TypeMismatchError("", context),
        _get('IED_ERROR_CONNECTION_LOST', 10): lambda: ConnectionClosedError(context),
        _get('IED_ERROR_SERVICE_NOT_SUPPORTED', 11): lambda: ServiceError(context),
    }

    if error_code in error_map:
        return error_map[error_code]()

    return TASE2Error(f"IED error {error_code}: {context}" if context else f"IED error {error_code}")

class JBLControllerError(Exception):
    """Base exception for all JBL Controller errors."""
    pass

class ConnectionError(JBLControllerError):
    """Raised when BLE connection fails or drops."""
    pass

class ProtocolError(JBLControllerError):
    """Raised when there is an issue building or parsing BLE packets."""
    pass

class UnsupportedFeatureError(JBLControllerError):
    """Raised when trying to use a feature or pattern not supported by the physical device."""
    pass

class InvalidValueError(JBLControllerError):
    """Raised when a parameter value is out of the accepted bounds."""
    pass


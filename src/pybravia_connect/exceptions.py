"""Exception hierarchy for pybravia-connect."""


class BraviaConnectError(Exception):
    """Base error for BRAVIA Connect protocol operations."""


class AuthError(BraviaConnectError):
    """Local gRPC session handshake failed."""


class ConnectionError(BraviaConnectError):
    """Could not establish a connection to the device."""


class CredentialsError(BraviaConnectError):
    """Sony Seeds credentials are missing, invalid, or expired."""

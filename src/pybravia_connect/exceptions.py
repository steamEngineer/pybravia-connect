"""Exception hierarchy for pybravia-connect."""


class BraviaConnectError(Exception):
    """Base error for BRAVIA Connect protocol operations."""


class AuthError(BraviaConnectError):
    """Local gRPC session handshake failed."""


class ConnectionError(BraviaConnectError):
    """Could not establish a connection to the device."""


class CredentialsError(BraviaConnectError, ValueError):
    """Sony Seeds credentials are missing, invalid, or expired."""


class CredentialsRefreshError(BraviaConnectError, OSError):
    """OAuth or session-key refresh failed.

    ``status`` carries the HTTP status when the failure was an error response
    from Sony's cloud, so callers can tell a rejected refresh token (400/401 —
    re-authenticate) from a transient/server error (retry).
    """

    def __init__(self, *args: object, status: int | None = None) -> None:
        super().__init__(*args)
        self.status = status


class OAuthError(BraviaConnectError, ValueError):
    """Sony Seeds OAuth redirect or token exchange failed."""


class DeviceSelectError(OAuthError):
    """Could not select a unique device from the Sony account device list."""

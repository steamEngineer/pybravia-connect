"""Sony BRAVIA Connect local gRPC protocol client (HA-agnostic)."""

from .client import BraviaConnectClient
from .credentials import (
    async_complete_oauth_flow,
    async_refresh_credentials,
    build_authorization_url,
    build_credentials_bundle,
    credentials_to_json,
    device_hardware_info,
    generate_pkce_pair,
    keys_need_refresh,
    parse_authorization_code,
    parse_credentials_json,
    parse_oauth_redirect_state,
    select_device,
    select_speaker_device,
    select_tv_device,
    start_oauth_login,
)
from .discovery import (
    DEFAULT_THEATRE_PORT,
    discover_grpc_port,
    is_control_device_service,
    scan_open_ports,
)
from .exceptions import (
    AuthError,
    BraviaConnectError,
    ConnectionError,
    CredentialsError,
    CredentialsRefreshError,
    DeviceSelectError,
    OAuthError,
)
from .wire.capabilities import CapabilityMeta

__version__ = "0.1.0a1"

__all__ = [
    "DEFAULT_THEATRE_PORT",
    "AuthError",
    "BraviaConnectClient",
    "BraviaConnectError",
    "CapabilityMeta",
    "ConnectionError",
    "CredentialsError",
    "CredentialsRefreshError",
    "DeviceSelectError",
    "OAuthError",
    "__version__",
    "async_complete_oauth_flow",
    "async_refresh_credentials",
    "build_authorization_url",
    "build_credentials_bundle",
    "credentials_to_json",
    "device_hardware_info",
    "discover_grpc_port",
    "generate_pkce_pair",
    "is_control_device_service",
    "keys_need_refresh",
    "parse_authorization_code",
    "parse_credentials_json",
    "parse_oauth_redirect_state",
    "scan_open_ports",
    "select_device",
    "select_speaker_device",
    "select_tv_device",
    "start_oauth_login",
]

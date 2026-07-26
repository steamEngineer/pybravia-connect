"""Smoke tests for the package shell."""

import pybravia_connect

_EXPECTED_EXPORTS = (
    "APPLICATION_LIST_PATH",
    "ZEROCONF_TYPE",
    "async_credentials_from_oauth",
    "async_exchange_oauth_redirect",
    "async_get_device_states",
    "async_get_devices",
    "async_list_oauth_devices",
    "async_refresh_access_token",
    "complete_oauth_flow",
    "credentials_from_oauth",
    "enum_values_from_capability",
    "exchange_authorization_code",
    "exchange_oauth_redirect",
    "get_device_states",
    "get_devices",
    "get_session_keys",
    "image_content_type",
    "int_range_from_capability",
    "is_int_capability",
    "load_credentials",
    "refresh_access_token",
    "refresh_credentials",
    "write_credentials",
)


def test_version() -> None:
    assert isinstance(pybravia_connect.__version__, str)
    assert pybravia_connect.__version__ == "0.1.0a8"


def test_public_exports() -> None:
    assert pybravia_connect.BraviaConnectClient is not None
    assert pybravia_connect.DEFAULT_THEATRE_PORT == 55051
    for name in _EXPECTED_EXPORTS:
        assert getattr(pybravia_connect, name) is not None
        assert name in pybravia_connect.__all__

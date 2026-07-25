"""Unit tests for credentials helpers."""

from __future__ import annotations

import pytest

from pybravia_connect import credentials
from pybravia_connect.exceptions import (
    CredentialsRefreshError,
    DeviceSelectError,
)

_TV = {
    "device_id": "tv-id",
    "device_type": "TV",
    "attributes": {"device_unique_id": "51b397cf"},
    "device_infos": {"model_name": "BRAVIA 8 II"},
}
_SPEAKER = {
    "device_id": "spk-id",
    "device_type": "Speaker",
    "attributes": {"device_unique_id": "bac76409"},
    "device_infos": {"model_name": "BRAVIA Theatre Quad"},
}


def test_select_tv_by_unique_id() -> None:
    got = credentials.select_tv_device([_TV, _SPEAKER], device_unique_id="51b397cf")
    assert got["device_id"] == "tv-id"


def test_select_unique_id_is_case_insensitive() -> None:
    got = credentials.select_tv_device([_TV, _SPEAKER], device_unique_id="51B397CF")
    assert got["device_id"] == "tv-id"


def test_select_soundbar_unique_id_rejected() -> None:
    with pytest.raises(DeviceSelectError):
        credentials.select_tv_device([_TV, _SPEAKER], device_unique_id="bac76409")


def test_select_falls_back_to_single_tv() -> None:
    assert credentials.select_tv_device([_TV, _SPEAKER])["device_id"] == "tv-id"


def test_select_by_explicit_device_id() -> None:
    assert credentials.select_device([_TV, _SPEAKER], device_id="spk-id") is _SPEAKER


def test_select_tv_rejects_speaker_device_id() -> None:
    with pytest.raises(DeviceSelectError):
        credentials.select_tv_device([_TV, _SPEAKER], device_id="spk-id")


def test_select_unknown_unique_id_raises() -> None:
    with pytest.raises(DeviceSelectError):
        credentials.select_tv_device([_TV, _SPEAKER], device_unique_id="ffff")


def test_select_no_tv_raises() -> None:
    with pytest.raises(DeviceSelectError):
        credentials.select_tv_device([_SPEAKER])


def test_select_speaker() -> None:
    assert credentials.select_speaker_device([_TV, _SPEAKER])["device_id"] == "spk-id"


def test_device_hardware_info() -> None:
    device = {
        "device_id": "x",
        "device_infos": {
            "model_name": "BRAVIA 8 II",
            "firmware_version": "114.602.080.1EUA",
        },
        "attributes": {"identified_model_name": "K-65XR8M2"},
    }
    assert credentials.device_hardware_info(device) == {
        "model": "BRAVIA 8 II",
        "model_id": "K-65XR8M2",
        "sw_version": "114.602.080.1EUA",
    }


def test_device_hardware_info_missing() -> None:
    assert credentials.device_hardware_info({}) == {
        "model": None,
        "model_id": None,
        "sw_version": None,
    }


def test_refresh_error_carries_http_status() -> None:
    err = CredentialsRefreshError("HTTP 401", status=401)
    assert err.status == 401
    assert str(err) == "HTTP 401"


def test_refresh_error_status_defaults_none() -> None:
    err = CredentialsRefreshError("connection reset")
    assert err.status is None


def test_start_oauth_login_shape() -> None:
    url, verifier, state = credentials.start_oauth_login()
    assert "authorize" in url
    assert verifier
    assert state


def test_parse_authorization_code_from_redirect() -> None:
    code = credentials.parse_authorization_code(
        "ssh-app://signin?code=abc123&state=xyz"
    )
    assert code == "abc123"


def test_keys_need_refresh_missing_expiry() -> None:
    assert credentials.keys_need_refresh({}) is False

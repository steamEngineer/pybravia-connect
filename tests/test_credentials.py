"""Unit tests for credentials helpers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pybravia_connect import credentials
from pybravia_connect.exceptions import (
    CredentialsRefreshError,
    DeviceSelectError,
    OAuthError,
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


def test_load_write_credentials_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "keys.json"
    payload = {"device_id": "dev", "session_key": "sk", "hmac_key": "hk"}
    credentials.write_credentials(path, payload)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == payload
    assert credentials.load_credentials(path) == payload


def test_load_credentials_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(TypeError, match="object"):
        credentials.load_credentials(path)


def test_exchange_oauth_redirect_state_mismatch() -> None:
    with pytest.raises(OAuthError, match="state"):
        credentials.exchange_oauth_redirect(
            "ssh-app://signin?code=abc&state=other",
            "verifier",
            expected_state="expected",
        )


def test_complete_oauth_flow_sync() -> None:
    token = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
    session_keys = {
        "device_id": "dev-1",
        "key_id": "kid",
        "session_key": "sk",
        "hmac_key": "hk",
        "expires_in": 86400,
    }
    with (
        patch.object(
            credentials, "exchange_authorization_code", return_value=token
        ) as exchange,
        patch.object(
            credentials,
            "get_devices",
            return_value={"devices": [{"device_id": "dev-1"}]},
        ),
        patch.object(credentials, "get_session_keys", return_value=session_keys),
    ):
        bundle = credentials.complete_oauth_flow(
            "ssh-app://signin?code=abc123&state=st",
            "verifier",
            expected_state="st",
        )
    exchange.assert_called_once_with("abc123", "verifier")
    assert bundle["access_token"] == "at"
    assert bundle["refresh_token"] == "rt"
    assert bundle["session_key"] == "sk"
    assert bundle["device_id"] == "dev-1"


def test_credentials_from_oauth_explicit_device_id() -> None:
    token = {"access_token": "at"}
    session_keys = {
        "key_id": "kid",
        "session_key": "sk",
        "hmac_key": "hk",
        "expires_in": 86400,
    }
    with (
        patch.object(credentials, "get_devices") as get_devices,
        patch.object(
            credentials, "get_session_keys", return_value=dict(session_keys)
        ) as get_keys,
    ):
        bundle = credentials.credentials_from_oauth(token, device_id="explicit")
    get_devices.assert_not_called()
    get_keys.assert_called_once_with("explicit", "at")
    assert bundle["device_id"] == "explicit"
    assert bundle["session_key"] == "sk"

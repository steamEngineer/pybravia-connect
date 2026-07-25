"""Unit tests for ExecCommandWithAuth wire builders."""

from __future__ import annotations

from pybravia_connect.wire.exec_command import (
    build_exec_command_signing_preimage,
    build_exec_command_with_auth_request,
    parse_exec_response,
    sign_exec_auth_token,
)

# Live-device capture (volume=60): validates Theatre-shaped 8-byte session embed.
_VOLUME_CAPTURE = bytes.fromhex(
    "0a680a440a100a0e0a06766f6c756d6510012202083c12300a0892f127335ad9a5171"
    "a2465336330666232372d613133612d343934632d623734342d383834356230336439666632"
    "122035006fd9f72a88a35ea7caf42fb03e6b35763dbca013e1cc83faad0902a1ec77"
)
_VOLUME_SESSION_RANDOM = bytes.fromhex("92f127335ad9a517")
_VOLUME_SESSION_ID = "e3c0fb27-a13a-494c-b744-8845b03d9ff2"
_VOLUME_AUTH_TOKEN = bytes.fromhex(
    "35006fd9f72a88a35ea7caf42fb03e6b35763dbca013e1cc83faad0902a1ec77"
)


def test_parse_exec_response_success() -> None:
    assert parse_exec_response(b"\x08\x01") is True
    assert parse_exec_response(b"") is False


def test_signing_preimage_deterministic() -> None:
    a = build_exec_command_signing_preimage(
        "mute",
        session_random=b"\x01" * 8,
        session_id="sess",
        bool_value=True,
    )
    b = build_exec_command_signing_preimage(
        "mute",
        session_random=b"\x01" * 8,
        session_id="sess",
        bool_value=True,
    )
    assert a == b
    assert len(a) > 20


def test_sign_exec_auth_token_length() -> None:
    token = sign_exec_auth_token(
        "00" * 32,
        "volume",
        session_random=b"\x02" * 8,
        session_id="sess",
        int_value=10,
    )
    assert len(token) == 32


def test_build_matches_volume_capture() -> None:
    built = build_exec_command_with_auth_request(
        "volume",
        session_random=_VOLUME_SESSION_RANDOM,
        session_id=_VOLUME_SESSION_ID,
        auth_token=_VOLUME_AUTH_TOKEN,
        int_value=60,
    )
    assert built == _VOLUME_CAPTURE

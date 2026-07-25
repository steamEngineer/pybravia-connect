"""Hand-parse GetStates response session_random / auth_token rotation."""

from __future__ import annotations

from pybravia_connect.wire.codec import encode_varint, length_delimited
from pybravia_connect.wire.get_states_request import (
    extract_auth_token_from_states_response,
    extract_session_tokens_from_states_response,
)


def test_extract_session_tokens_field2_and_field4() -> None:
    session_random = b"\x11" * 8
    auth_token = b"\x22" * 32
    session_id = "key-abc"
    raw = (
        length_delimited(1, b"\x00")  # states blob (ignored)
        + length_delimited(2, session_random)
        + length_delimited(3, session_id.encode())
        + length_delimited(4, auth_token)
    )
    got_random, got_auth, got_sid = extract_session_tokens_from_states_response(raw)
    assert got_random == session_random
    assert got_auth == auth_token
    assert got_sid == session_id


def test_extract_ignores_non_eight_byte_session_random() -> None:
    # Theatre overloads field 2 with notify-sized blobs; must not poison signing.
    blob = b"\x33" * 32
    auth = b"\x44" * 32
    raw = length_delimited(2, blob) + length_delimited(4, auth)
    got_random, got_auth, _ = extract_session_tokens_from_states_response(raw)
    assert got_random is None
    assert got_auth == auth


def test_extract_auth_fallback_trailing_field2() -> None:
    auth = b"\x55" * 32
    raw = b"\x0a\x01\x00" + b"\x12\x20" + auth
    assert extract_auth_token_from_states_response(raw) == auth
    got_random, got_auth, _ = extract_session_tokens_from_states_response(raw)
    assert got_random is None
    assert got_auth == auth


def test_field4_overwrites_trailing_auth_fallback() -> None:
    trailing = b"\x66" * 32
    field4 = b"\x77" * 32
    session_random = b"\x88" * 8
    # states + 8-byte field2 + trailing-shaped field2 auth + field4 auth
    raw = (
        length_delimited(1, b"\x00")
        + length_delimited(2, session_random)
        + b"\x12"
        + encode_varint(32)
        + trailing
        + length_delimited(4, field4)
    )
    got_random, got_auth, _ = extract_session_tokens_from_states_response(raw)
    assert got_random == session_random
    assert got_auth == field4

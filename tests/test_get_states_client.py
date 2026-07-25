"""BraviaConnectClient.get_states under the session lock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pybravia_connect.client import BraviaConnectClient
from pybravia_connect.exceptions import ConnectionError
from pybravia_connect.wire.codec import length_delimited


def test_get_states_signs_applies_tokens_and_parses() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    client._stub = MagicMock()
    client._channel = MagicMock()
    client._session_random = b"\x01" * 8
    client._safe_get_states_paths = ["volume"]

    # Minimal response: field2 session_random + field4 auth (no states entries).
    new_random = b"\xaa" * 8
    new_auth = b"\xbb" * 32
    raw = length_delimited(2, new_random) + length_delimited(4, new_auth)

    unary = MagicMock(return_value=raw)
    with patch.object(client, "_raw_unary", return_value=unary):
        result = client.get_states(["volume"])

    assert result == {}
    assert client._session_random == new_random
    assert client._auth_token == new_auth
    unary.assert_called_once()
    req = unary.call_args.args[0]
    assert isinstance(req, bytes) and len(req) > 40
    # Auth tail: field 2, length 32.
    assert req[-34:-32] == b"\x12\x20"


def test_get_states_requires_paths() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    client._stub = MagicMock()
    client._channel = MagicMock()
    client._session_random = b"\x01" * 8
    with pytest.raises(ConnectionError, match="no GetStates paths"):
        client.get_states()

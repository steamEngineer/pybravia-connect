"""BraviaConnectClient get_capabilities_json and session_snapshot."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pb_helpers import ld
import pytest

from pybravia_connect.client import BraviaConnectClient
from pybravia_connect.exceptions import ConnectionError
from pybravia_connect.wire.capabilities import CapabilityMeta


def _capabilities_wire(payload: dict) -> bytes:
    return ld(1, ld(1, json.dumps(payload).encode()))


def test_get_capabilities_json_parses_and_caches() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    client._channel = MagicMock()
    payload = {
        "capabilities": [
            {
                "name": "volume",
                "type": "int",
                "props": {"get": True, "min": 0, "max": 100},
            },
        ]
    }
    raw = _capabilities_wire(payload)
    unary = MagicMock(return_value=raw)

    with patch.object(client, "_raw_unary", return_value=unary) as raw_unary:
        index = client.get_capabilities()
        assert "volume" in index
        assert client._capabilities_json is not None
        assert client._capabilities_json["capabilities"][0]["name"] == "volume"

        again = client.get_capabilities_json()
        assert again == client._capabilities_json
        assert again is not None
        assert again["capabilities"][0]["name"] == "volume"
        # Cache hit: no second RPC.
        assert raw_unary.call_count == 1
        assert unary.call_count == 1


def test_get_capabilities_json_fetches_when_uncached() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    client._channel = MagicMock()
    payload = {"capabilities": [{"name": "power", "type": "bool"}]}
    raw = _capabilities_wire(payload)
    unary = MagicMock(return_value=raw)

    with patch.object(client, "_raw_unary", return_value=unary):
        result = client.get_capabilities_json()

    assert result is not None
    assert result["capabilities"][0]["name"] == "power"
    assert client._safe_get_states_paths == []  # no props.get


def test_get_capabilities_json_requires_connection() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    with pytest.raises(ConnectionError, match="not connected"):
        client.get_capabilities_json()


def test_session_snapshot_flags() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    snap = client.session_snapshot()
    assert snap["connected"] is False
    assert isinstance(snap["session_id"], str) and snap["session_id"]
    assert snap["has_session_random"] is False
    assert snap["has_auth_token"] is False
    assert snap["has_capabilities"] is False

    client._channel = MagicMock()
    client._session_random = b"\x01" * 8
    client._auth_token = b"\x02" * 32
    client._capabilities = {
        "volume": CapabilityMeta(name="volume", type="int", min=0, max=100)
    }
    snap = client.session_snapshot()
    assert snap["connected"] is True
    assert snap["has_session_random"] is True
    assert snap["has_auth_token"] is True
    assert snap["has_capabilities"] is True
    assert set(snap) == {
        "connected",
        "session_id",
        "has_session_random",
        "has_auth_token",
        "has_capabilities",
    }

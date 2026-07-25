"""Unit tests for GetCapabilities decoding helpers."""

from __future__ import annotations

import json

from pb_helpers import encode_varint, ld

from pybravia_connect.wire.capabilities import (
    CapabilityMeta,
    capability_index_from_json,
    decode_capabilities_json_text,
    paths_for_safe_get_states,
)


def test_capability_index_from_json() -> None:
    cap = {
        "capabilities": [
            {
                "name": "volume",
                "type": "int",
                "props": {"min": 0, "max": 100, "get": True},
            },
            {
                "name": "mute",
                "type": "bool",
                "props": {"get": True},
            },
        ]
    }
    index = capability_index_from_json(cap)
    assert index["volume"] == CapabilityMeta(
        name="volume", type="int", min=0, max=100, values=None
    )
    assert index["mute"].type == "bool"


def test_paths_for_safe_get_states_skips_security() -> None:
    cap = {
        "capabilities": [
            {"name": "volume", "type": "int", "props": {"get": True}},
            {
                "name": "system_setting.application_list",
                "type": "any",
                "props": {"get": True, "security": {"getstates_request": True}},
            },
        ]
    }
    assert paths_for_safe_get_states(cap) == ["volume"]


def test_decode_capabilities_json_text_from_wire() -> None:
    payload = json.dumps({"capabilities": [{"name": "power", "type": "bool"}]}).encode()
    # outer field1 -> inner field1 string
    raw = ld(1, ld(1, payload))
    text = decode_capabilities_json_text(raw)
    assert text is not None
    assert "power" in text
    # sanity: varint helper used by ld
    assert encode_varint(150) == b"\x96\x01"

"""Unit tests for the StartNotifyStates delta decoder."""

from __future__ import annotations

from pb_helpers import ld, vint

from pybravia_connect.wire import notify as nd
from pybravia_connect.wire.notify import APPLICATION_LIST_PATH


def _delta(path: str, value_field: bytes) -> bytes:
    """A notify delta payload: field1 -> field1 -> {field1=path, <value>}."""
    inner = ld(1, path.encode()) + value_field
    return ld(1, ld(1, inner))


def test_int_value() -> None:
    payload = _delta("volume", ld(2, vint(1, 18)))
    assert nd.decode_notify_delta(payload) == ("volume", 18)


def test_omitted_zero_int_is_zero_not_none() -> None:
    payload = _delta("display_setting.brightness", ld(2, b""))
    assert nd.decode_notify_delta(payload) == ("display_setting.brightness", 0)


def test_bool_true_and_omitted_false() -> None:
    assert nd.decode_notify_delta(_delta("power", ld(3, vint(1, 1)))) == ("power", True)
    assert nd.decode_notify_delta(_delta("mute", ld(3, b""))) == ("mute", False)


def test_string_value() -> None:
    value = ld(4, ld(1, b"video"))
    assert nd.decode_notify_delta(
        _delta("display_and_sound_setting.content_mode", value)
    ) == ("display_and_sound_setting.content_mode", "video")


def test_sound_field_int_coerced_to_bool() -> None:
    assert nd.decode_notify_delta(_delta("sound_field", ld(2, vint(1, 1)))) == (
        "sound_field",
        True,
    )


def test_maybe_signed_int_roundtrip() -> None:
    assert nd._maybe_signed_int(0) == 0
    assert nd._maybe_signed_int(6) == 6
    assert nd._maybe_signed_int((1 << 64) - 6) == -6


def test_parse_notify_message_dispatches_normal_delta() -> None:
    raw = ld(2, _delta("volume", ld(2, vint(1, 7))))
    assert nd.parse_notify_message(raw) == ("volume", 7)


def test_parse_notify_message_large_field3_is_app_list_trigger() -> None:
    raw = ld(3, b"\x00" * 300)
    assert nd.parse_notify_message(raw) == (APPLICATION_LIST_PATH, None)


def test_parse_notify_message_small_field3_ignored() -> None:
    raw = ld(3, b"session-id")
    assert nd.parse_notify_message(raw) == (None, None)

"""Tiny protobuf wire builders for unit tests."""

from __future__ import annotations


def encode_varint(value: int) -> bytes:
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def ld(field: int, body: bytes) -> bytes:
    """Length-delimited field."""
    return bytes([(field << 3) | 2]) + encode_varint(len(body)) + body


def vint(field: int, value: int) -> bytes:
    """Varint field."""
    return bytes([(field << 3) | 0]) + encode_varint(value)

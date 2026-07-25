"""Build GetStatesWithAuth request bytes (wire format differs from .proto)."""

from __future__ import annotations

from .codec import decode_field, encode_varint


def build_get_states_with_auth_request(
    field_paths: list[str],
    *,
    session_random: bytes,
    session_id: str,
    auth_token: bytes,
) -> bytes:
    """
    Return serialized GetStatesWithAuth request matching BRAVIA Connect captures.

    Top-level layout (6558 bytes with 177 paths on fw 001.454):
      field 1 (6521 B): nested path list + embedded session block (field 2 / 0x12)
      field 2 (34 B): auth_token (32 B HMAC-SHA256)
    """
    # BRAVIA TVs return a 64-byte session_random. Emit the field length-prefixed
    # rather than assuming a fixed size.
    if len(auth_token) != 32:
        msg = f"auth_token must be 32 bytes, got {len(auth_token)}"
        raise ValueError(msg)

    inner_parts = b""
    for path in field_paths:
        path_bytes = path.encode("utf-8")
        inner_parts += b"\x0a" + encode_varint(len(path_bytes)) + path_bytes

    nested_field = b"\x0a" + encode_varint(len(inner_parts)) + inner_parts

    session_id_bytes = session_id.encode("utf-8")
    embedded_data = (
        b"\x0a"
        + encode_varint(len(session_random))
        + session_random
        + b"\x1a"
        + encode_varint(len(session_id_bytes))
        + session_id_bytes
    )
    embedded_field = b"\x12" + encode_varint(len(embedded_data)) + embedded_data

    field1_content = nested_field + embedded_field
    field_list_bytes = b"\x0a" + encode_varint(len(field1_content)) + field1_content
    auth_token_bytes = b"\x12" + encode_varint(len(auth_token)) + auth_token
    return field_list_bytes + auth_token_bytes


def build_small_get_states_with_auth_request(
    field_path: str,
    *,
    session_random: bytes,
    session_id: str,
    auth_token: bytes,
) -> bytes:
    """
    Return a single-path GetStatesWithAuth request (app mutex preflight).

    Used before ExecCommandWithAuth to obtain a rolling ``auth_token`` for the
    command body (single-path mutex-style preflight).
    """
    if len(session_random) != 8:
        msg = f"session_random must be 8 bytes, got {len(session_random)}"
        raise ValueError(msg)
    if len(auth_token) != 32:
        msg = f"auth_token must be 32 bytes, got {len(auth_token)}"
        raise ValueError(msg)

    path_bytes = field_path.encode("utf-8")
    depth2 = b"\x0a" + encode_varint(len(path_bytes)) + path_bytes
    depth1 = b"\x0a" + encode_varint(len(depth2)) + depth2

    session_id_bytes = session_id.encode("utf-8")
    embedded_data = (
        b"\x0a\x08"
        + session_random
        + b"\x1a"
        + encode_varint(len(session_id_bytes))
        + session_id_bytes
    )
    embedded_field = b"\x12" + encode_varint(len(embedded_data)) + embedded_data

    inner = depth1 + embedded_field
    field_list_bytes = b"\x0a" + encode_varint(len(inner)) + inner
    auth_token_bytes = b"\x12" + encode_varint(len(auth_token)) + auth_token
    return field_list_bytes + auth_token_bytes


def extract_auth_token_from_states_response(raw: bytes) -> bytes | None:
    """Return trailing 32-byte auth token from a GetStatesWithAuth response body."""
    marker = b"\x12\x20"
    idx = raw.rfind(marker)
    if idx < 0 or idx + 34 > len(raw):
        return None
    return raw[idx + 2 : idx + 34]


def extract_session_tokens_from_states_response(
    raw: bytes,
) -> tuple[bytes | None, bytes | None, str | None]:
    """
    Hand-parse GetStatesWithAuth response tokens (no fat response pb2).

    Top-level fields (nominal schema):
      1 states blob (ignored here)
      2 session_random — only meaningful when exactly 8 bytes
      3 session_id
      4 auth_token (32 B)

    Also accepts a trailing field-2 ``\\x12\\x20`` + 32 B auth fallback used by
    some Theatre response shapes. Field 4 overwrites that fallback when present.
    """
    session_random: bytes | None = None
    auth_token = extract_auth_token_from_states_response(raw)
    session_id: str | None = None

    offset = 0
    while offset < len(raw):
        field, offset = decode_field(raw, offset)
        if not field:
            break
        field_num, wire_type, payload = field
        if wire_type != 2 or not isinstance(payload, bytes):
            continue
        if field_num == 2 and len(payload) == 8:
            session_random = payload
        elif field_num == 3:
            session_id = payload.decode("utf-8", errors="replace")
        elif field_num == 4 and len(payload) == 32:
            auth_token = payload

    return session_random, auth_token, session_id

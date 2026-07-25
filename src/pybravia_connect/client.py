"""Synchronous ControlDeviceService client (HA-agnostic).

Run blocking calls from Home Assistant in an executor. Session-authenticated
RPCs (GetSessionRandom + ExecCommandWithAuth) are serialized with a lock —
concurrent GetSessionRandom can crash device firmware.
"""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import hmac
import logging
import threading
from typing import Any
import uuid

import grpc

from .exceptions import AuthError, ConnectionError
from .proto.bravia_control_pb2 import (
    ConfirmKeysRequest,
    ConfirmSigninRequest,
    GetSessionRandomRequest,
    StartNotifyStatesRequest,
)
from .proto.bravia_control_pb2_grpc import ControlDeviceServiceStub
from .wire.capabilities import (
    CapabilityMeta,
    decode_capabilities_json_text,
    get_capabilities_method,
    parse_capability_index,
    paths_for_safe_get_states,
)
from .wire.exec_command import (
    build_exec_command_with_auth_request,
    parse_exec_response,
    sign_exec_auth_token,
)
from .wire.get_states_auth import sign_get_states_request_body
from .wire.get_states_request import (
    build_small_get_states_with_auth_request,
    extract_auth_token_from_states_response,
)
from .wire.notify import parse_notify_message

_LOGGER = logging.getLogger(__name__)

_SERVICE = "jp.co.sony.hes.ssh.controldevice.v1.ControlDeviceService"
_EXEC_METHOD = f"/{_SERVICE}/ExecCommandWithAuth"
_GET_STATES_METHOD = f"/{_SERVICE}/GetStatesWithAuth"
_NOTIFY_METHOD = f"/{_SERVICE}/StartNotifyStates"
_MUTEX_PATH = "client_control.mutex.any"

_CHANNEL_OPTIONS = (
    ("grpc.keepalive_time_ms", 2147483647),  # effectively off
    ("grpc.keepalive_timeout_ms", 20000),
    ("grpc.keepalive_permit_without_calls", False),
    ("grpc.http2.max_pings_without_data", 2),
    ("grpc.http2.write_buffer_size", 65536),
)

DeltaCallback = Callable[[str, Any], None]


def _hmac_key_bytes(hmac_key_hex: str) -> bytes:
    if len(hmac_key_hex) == 64:
        return bytes.fromhex(hmac_key_hex)
    return hmac_key_hex.encode("utf-8")[:32].ljust(32, b"\x00")


class BraviaConnectClient:
    """Synchronous gRPC client for BRAVIA Connect devices."""

    def __init__(
        self,
        host: str,
        port: int,
        device_id: str,
        hmac_key: str,
        *,
        key_id: str | None = None,
        session_key: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._device_id = device_id
        self._hmac_key = hmac_key
        self._session_key = session_key
        self._session_id = key_id or str(uuid.uuid4())
        self._channel: grpc.Channel | None = None
        self._stub: ControlDeviceServiceStub | None = None
        self._session_random: bytes | None = None
        self._auth_token: bytes | None = None
        self._capabilities: dict[str, CapabilityMeta] = {}
        self._safe_get_states_paths: list[str] = []
        self._session_lock = threading.Lock()
        self._notify_cache: dict[str, Any] = {}

        self._notify_thread: threading.Thread | None = None
        self._notify_stop = threading.Event()
        self._on_delta: DeltaCallback | None = None
        self._on_connection_lost: Callable[[], None] | None = None
        self._on_reconnect: Callable[[], None] | None = None

    def connect(self, timeout: float = 5.0) -> None:
        """Open the channel and run the auth handshake."""
        self._channel = grpc.insecure_channel(
            f"{self.host}:{self.port}", options=list(_CHANNEL_OPTIONS)
        )
        try:
            grpc.channel_ready_future(self._channel).result(timeout=timeout)
        except grpc.FutureTimeoutError as err:
            raise ConnectionError(
                f"gRPC channel to {self.host}:{self.port} not ready"
            ) from err
        self._stub = ControlDeviceServiceStub(self._channel)
        with self._session_lock:
            self._authenticate(timeout=timeout)

    def _authenticate(self, timeout: float = 5.0) -> None:
        assert self._stub is not None
        signin = ConfirmSigninRequest()
        signin.auth_data = hashlib.sha256(self._device_id.encode()).digest()
        try:
            self._stub.ConfirmSignin(signin, timeout=timeout)
            keys = ConfirmKeysRequest()
            keys.session_id = self._session_id
            keys.key_data = hmac.new(
                _hmac_key_bytes(self._hmac_key),
                self._session_id.encode(),
                hashlib.sha256,
            ).digest()
            self._stub.ConfirmKeys(keys, timeout=timeout)
            self._refresh_session_random(timeout=timeout)
        except grpc.RpcError as err:
            raise AuthError(f"handshake failed: {err.code()}") from err

    def _refresh_session_random(self, timeout: float = 5.0) -> None:
        assert self._stub is not None
        resp = self._stub.GetSessionRandom(
            GetSessionRandomRequest(session_id=self._session_id), timeout=timeout
        )
        self._session_random = resp.session_random
        if resp.auth_token:
            self._auth_token = resp.auth_token
        if not self._session_random:
            raise AuthError("GetSessionRandom returned no session_random")

    def _apply_get_states_tokens(self, raw: bytes) -> None:
        token = extract_auth_token_from_states_response(raw)
        if token:
            self._auth_token = token

    def _mutex_preflight(self, timeout: float = 8.0) -> bool:
        """HMAC-signed mutex GetStates (Theatre firmware requires this before exec)."""
        if self._channel is None or self._session_random is None:
            return False
        if len(self._session_random) != 8:
            # TV session_random is longer; mutex small-request is Theatre-shaped.
            return True
        preview = build_small_get_states_with_auth_request(
            _MUTEX_PATH,
            session_random=self._session_random,
            session_id=self._session_id,
            auth_token=b"\x00" * 32,
        )
        token = sign_get_states_request_body(self._hmac_key, preview)
        req = build_small_get_states_with_auth_request(
            _MUTEX_PATH,
            session_random=self._session_random,
            session_id=self._session_id,
            auth_token=token,
        )
        try:
            raw = self._raw_unary(_GET_STATES_METHOD)(req, timeout=timeout)
        except grpc.RpcError as err:
            _LOGGER.debug("mutex preflight failed: %s", err.code())
            return False
        if not raw:
            return False
        self._apply_get_states_tokens(raw)
        return True

    def close(self) -> None:
        """Stop notify and close the channel."""
        self.stop_notify()
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None

    def _raw_unary(self, method: str) -> Any:
        return self._channel.unary_unary(  # type: ignore[union-attr]
            method, request_serializer=lambda p: p, response_deserializer=lambda p: p
        )

    def _raw_stream(self, method: str) -> Any:
        return self._channel.unary_stream(  # type: ignore[union-attr]
            method, request_serializer=lambda p: p, response_deserializer=lambda p: p
        )

    def get_capabilities(self, timeout: float = 10.0) -> dict[str, CapabilityMeta]:
        """Fetch and cache the device field-path schema (unauthenticated)."""
        if self._channel is None:
            raise ConnectionError("not connected")
        call = self._raw_unary(get_capabilities_method())
        raw = call(b"", timeout=timeout)
        index = parse_capability_index(raw) or {}
        self._capabilities = index
        cap_json = decode_capabilities_json_text(raw)
        self._safe_get_states_paths = (
            paths_for_safe_get_states(cap_json) if cap_json else []
        )
        return index

    @property
    def capabilities(self) -> dict[str, CapabilityMeta]:
        return self._capabilities

    def exec_command(
        self,
        path: str,
        value: Any,
        *,
        confirm_prerequisite: str | None = None,
        timeout: float = 8.0,
    ) -> bool:
        """Set *path* to *value*, choosing the wire type from the capability."""
        if self._stub is None:
            raise ConnectionError("not connected")
        with self._session_lock:
            self._refresh_session_random(timeout=timeout)
            # Theatre (8-byte session_random): mutex×2 before exec, like BRAVIA Connect.
            if len(self._session_random or b"") == 8:
                for _ in range(2):
                    if not self._mutex_preflight(timeout=timeout):
                        _LOGGER.debug("mutex preflight incomplete for %s", path)
            if confirm_prerequisite is not None:
                self._exec(
                    f"{path}.confirm_prerequisite",
                    timeout,
                    string_value=confirm_prerequisite,
                )
            else:
                self._confirm_prerequisites(path, timeout)
            return self._exec(path, timeout, **self._value_kwargs(path, value))

    def _exec(self, path: str, timeout: float, **value_kwargs: Any) -> bool:
        assert self._session_random is not None
        token = sign_exec_auth_token(
            self._hmac_key,
            path,
            session_random=self._session_random,
            session_id=self._session_id,
            **value_kwargs,
        )
        req = build_exec_command_with_auth_request(
            path,
            session_random=self._session_random,
            session_id=self._session_id,
            auth_token=token,
            **value_kwargs,
        )
        call = self._raw_unary(_EXEC_METHOD)
        raw = call(req, timeout=timeout)
        if parse_exec_response(raw):
            return True
        # Some paths return an empty body; confirm via notify cache when present.
        if not raw and path in self._notify_cache:
            expected = value_kwargs.get("bool_value")
            if expected is None:
                expected = value_kwargs.get("int_value")
            if expected is None:
                expected = value_kwargs.get("string_value") or value_kwargs.get(
                    "any_value"
                )
            if self._notify_cache.get(path) == expected:
                return True
        return False

    def _confirm_prerequisites(self, path: str, timeout: float) -> None:
        meta = self._capabilities.get(f"{path}.confirm_prerequisite")
        if meta is None or not meta.values:
            return
        for prerequisite in meta.values:
            try:
                self._exec(
                    f"{path}.confirm_prerequisite", timeout, string_value=prerequisite
                )
            except grpc.RpcError as err:
                _LOGGER.debug(
                    "confirm_prerequisite %s for %s failed: %s",
                    prerequisite,
                    path,
                    err.code(),
                )

    def _value_kwargs(self, path: str, value: Any) -> dict[str, Any]:
        meta = self._capabilities.get(path)
        cap_type = meta.type if meta else None
        if cap_type == "bool" or isinstance(value, bool):
            return {"bool_value": bool(value)}
        if cap_type == "int" or isinstance(value, int):
            return {"int_value": int(value)}
        if cap_type == "any":
            return {"any_value": str(value)}
        return {"string_value": str(value)}

    def start_notify(
        self,
        on_delta: DeltaCallback,
        on_connection_lost: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> None:
        """Start (or restart) the StartNotifyStates worker thread."""
        self._on_delta = on_delta
        self._on_connection_lost = on_connection_lost
        self._on_reconnect = on_reconnect
        self._notify_stop.clear()
        self._notify_thread = threading.Thread(
            target=self._notify_worker, name="bravia_connect_notify", daemon=True
        )
        self._notify_thread.start()

    def stop_notify(self) -> None:
        """Stop the notify worker thread."""
        self._notify_stop.set()
        thread = self._notify_thread
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        self._notify_thread = None

    def _notify_worker(self) -> None:
        backoff = 1.0
        failures = 0
        had_drop = False
        while not self._notify_stop.is_set():
            if self._stub is None:
                break
            try:
                notify = self._raw_stream(_NOTIFY_METHOD)
                stream = notify(
                    StartNotifyStatesRequest(
                        session_id=self._session_id
                    ).SerializeToString()
                )
                for raw in stream:
                    if self._notify_stop.is_set():
                        stream.cancel()
                        break
                    if had_drop:
                        had_drop = False
                        if self._on_reconnect is not None:
                            try:
                                self._on_reconnect()
                            except Exception:  # noqa: BLE001
                                _LOGGER.exception("notify reconnect handler failed")
                    failures = 0
                    path, value = parse_notify_message(raw)
                    if path:
                        self._notify_cache[path] = value
                        if self._on_delta is not None:
                            try:
                                self._on_delta(path, value)
                            except Exception:  # noqa: BLE001
                                _LOGGER.exception("notify callback failed for %s", path)
                failures = 0
                backoff = 1.0
                had_drop = True
            except grpc.RpcError as err:
                if self._notify_stop.is_set():
                    break
                had_drop = True
                failures += 1
                _LOGGER.debug(
                    "notify stream ended (%s); reconnect attempt %d",
                    err.code(),
                    failures,
                )
                if failures >= 3 and self._on_connection_lost is not None:
                    _LOGGER.warning(
                        "Notify connection lost after %d attempts",
                        failures,
                    )
                    self._on_connection_lost()
                    break
            self._notify_stop.wait(backoff)
            backoff = min(backoff * 2, 5.0)

"""Unit tests for TCP discovery helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import grpc

from pybravia_connect import discovery


def test_default_theatre_port() -> None:
    assert discovery.DEFAULT_THEATRE_PORT == 55051


@patch("pybravia_connect.discovery._port_open", return_value=False)
def test_discover_grpc_port_none_when_closed(mock_open: MagicMock) -> None:
    assert discovery.discover_grpc_port("127.0.0.1", candidate_ports=(55051,)) is None
    mock_open.assert_called()


@patch("pybravia_connect.discovery.is_control_device_service", return_value=True)
@patch("pybravia_connect.discovery._port_open", return_value=True)
def test_discover_grpc_port_candidate(
    mock_open: MagicMock, mock_svc: MagicMock
) -> None:
    assert discovery.discover_grpc_port("192.0.2.1", candidate_ports=(55051,)) == 55051
    mock_svc.assert_called_once()


@patch("pybravia_connect.discovery.grpc.insecure_channel")
def test_is_control_device_service_invalid_argument(mock_channel_fn: MagicMock) -> None:
    channel = MagicMock()
    mock_channel_fn.return_value = channel
    future = MagicMock()
    future.result.return_value = None
    with patch(
        "pybravia_connect.discovery.grpc.channel_ready_future", return_value=future
    ):
        call = MagicMock()
        err = grpc.RpcError()
        err.code = lambda: grpc.StatusCode.INVALID_ARGUMENT  # type: ignore[method-assign]
        call.side_effect = err
        channel.unary_unary.return_value = call
        assert discovery.is_control_device_service("192.0.2.1", 55051) is True


@patch("pybravia_connect.discovery.grpc.insecure_channel")
def test_is_control_device_service_unimplemented(mock_channel_fn: MagicMock) -> None:
    channel = MagicMock()
    mock_channel_fn.return_value = channel
    future = MagicMock()
    future.result.return_value = None
    with patch(
        "pybravia_connect.discovery.grpc.channel_ready_future", return_value=future
    ):
        call = MagicMock()
        err = grpc.RpcError()
        err.code = lambda: grpc.StatusCode.UNIMPLEMENTED  # type: ignore[method-assign]
        call.side_effect = err
        channel.unary_unary.return_value = call
        assert discovery.is_control_device_service("192.0.2.1", 12345) is False

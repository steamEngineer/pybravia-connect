"""Discover the ControlDeviceService gRPC port (HA-free TCP probes).

Theatre devices typically use fixed port 55051. BRAVIA TVs serve the service on
a dynamic port that changes across reboots — locate it by probing candidate
TCP ports and confirming the service by RPC behaviour.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
import socket

import grpc

_LOGGER = logging.getLogger(__name__)

DEFAULT_THEATRE_PORT = 55051
ZEROCONF_TYPE = "_sonysmarthome._tcp.local."

_SERVICE = "jp.co.sony.hes.ssh.controldevice.v1.ControlDeviceService"
_PROBE_METHOD = f"/{_SERVICE}/GetSessionRandom"


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def scan_open_ports(
    host: str, ports: range, timeout: float = 0.3, workers: int = 500
) -> list[int]:
    """Return the subset of ``ports`` accepting TCP connections on ``host``."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda p: (p, _port_open(host, p, timeout)), ports)
        return [p for p, is_open in results if is_open]


def is_control_device_service(host: str, port: int, timeout: float = 3.0) -> bool:
    """Return True if ``host:port`` hosts the Sony ControlDeviceService.

    Distinguishes the real service (registered method → INVALID_ARGUMENT on an
    empty request) from an unrelated HTTP/2 server (→ UNIMPLEMENTED).
    """
    channel = grpc.insecure_channel(f"{host}:{port}")
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout)
        call = channel.unary_unary(_PROBE_METHOD)
        try:
            call(b"", timeout=timeout)
        except grpc.RpcError as err:
            code = err.code()
            if code == grpc.StatusCode.INVALID_ARGUMENT:
                return True
            _LOGGER.debug("Port %s not the service: %s", port, code)
            return False
        return True
    except (grpc.FutureTimeoutError, grpc.RpcError):
        return False
    finally:
        channel.close()


def discover_grpc_port(
    host: str,
    candidate_ports: tuple[int, ...] = (),
    scan_range: range | None = None,
) -> int | None:
    """Locate the gRPC control port on ``host``.

    Tries ``candidate_ports`` first, then optionally probes open ports in
    ``scan_range``. For Theatre, pass ``candidate_ports=(DEFAULT_THEATRE_PORT,)``.
    """
    for port in candidate_ports:
        if _port_open(host, port) and is_control_device_service(host, port):
            _LOGGER.info("Found ControlDeviceService on %s:%s", host, port)
            return port

    if scan_range is None:
        return None

    for port in scan_open_ports(host, scan_range):
        if port in candidate_ports:
            continue
        if is_control_device_service(host, port):
            _LOGGER.info("Discovered ControlDeviceService on %s:%s", host, port)
            return port
    return None

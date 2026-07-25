"""Session lock serializes exec / GetSessionRandom on the sync client."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

from pybravia_connect.client import BraviaConnectClient


def test_exec_command_is_serialized() -> None:
    client = BraviaConnectClient("192.0.2.1", 55051, "dev", "00" * 32)
    client._stub = MagicMock()
    client._channel = MagicMock()
    client._session_random = b"\x01" * 8
    client._capabilities = {}

    order: list[str] = []

    def slow_refresh(timeout: float = 5.0) -> None:
        order.append("start")
        time.sleep(0.08)
        order.append("end")
        client._session_random = b"\x02" * 8

    results: list[bool] = []

    def worker() -> None:
        results.append(client.exec_command("mute", True, timeout=1.0))

    with (
        patch.object(client, "_refresh_session_random", side_effect=slow_refresh),
        patch.object(client, "_exec", return_value=True),
    ):
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)

    assert results == [True, True]
    # Serialized: start/end pairs, not interleaved starts.
    assert order == ["start", "end", "start", "end"]

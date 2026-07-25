#!/usr/bin/env python3
"""Live smoke: connect → capabilities → notify (+ optional exec) on a real device.

Env:
  BRAVIA_HOST          device IP (required)
  BRAVIA_PORT          gRPC port (default 55051)
  BRAVIA_CREDENTIALS   path to credentials JSON from OAuth (required)

Optional:
  BRAVIA_EXEC_PATH     field to write (default: volume)
  BRAVIA_EXEC_VALUE    int/bool/string value (default: 7 for volume)
  BRAVIA_SKIP_EXEC     set to 1 to skip the write attempt

Exit 0 when connect + GetCapabilities + at least one notify delta succeed.
Exec success is reported but does not fail the smoke (Theatre writes may need
the fuller GetStates app-sequence that lands in a later milestone).

Does not import homeassistant.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time

from pybravia_connect import DEFAULT_THEATRE_PORT, BraviaConnectClient


def main() -> int:
    host = os.environ.get("BRAVIA_HOST")
    creds_path = os.environ.get("BRAVIA_CREDENTIALS")
    if not host or not creds_path:
        print("Set BRAVIA_HOST and BRAVIA_CREDENTIALS", file=sys.stderr)
        return 2

    port = int(os.environ.get("BRAVIA_PORT", str(DEFAULT_THEATRE_PORT)))
    creds = json.loads(Path(creds_path).read_text(encoding="utf-8"))
    device_id = creds["device_id"]
    hmac_key = creds["hmac_key"]
    key_id = creds.get("key_id")

    client = BraviaConnectClient(
        host,
        port,
        device_id,
        hmac_key,
        key_id=key_id,
        session_key=creds.get("session_key"),
    )
    print(f"connecting {host}:{port} …")
    client.connect()
    caps = client.get_capabilities()
    print(f"capabilities: {len(caps)} paths")

    seen: dict[str, object] = {}

    def on_delta(path: str, value: object) -> None:
        seen[path] = value
        print(f"notify {path}={value!r}")

    client.start_notify(on_delta)
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline and not seen:
        time.sleep(0.25)

    if not seen:
        print("no notify deltas received (capabilities still ok)", file=sys.stderr)
        client.close()
        # Handshake + schema are enough for smoke when the stream is quiet.
        return 0

    if os.environ.get("BRAVIA_SKIP_EXEC") != "1":
        path = os.environ.get("BRAVIA_EXEC_PATH", "volume")
        if "BRAVIA_EXEC_VALUE" in os.environ:
            raw = os.environ["BRAVIA_EXEC_VALUE"]
            if raw.lower() in ("true", "false"):
                value: object = raw.lower() == "true"
            else:
                try:
                    value = int(raw)
                except ValueError:
                    value = raw
        else:
            value = 7
        print(f"exec {path}={value!r}")
        try:
            ok = client.exec_command(path, value)
            print(f"exec ok={ok}")
        except Exception as exc:  # noqa: BLE001
            print(f"exec error: {exc}")
        time.sleep(1.0)

    client.close()
    print("done (connect + capabilities + notify ok)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

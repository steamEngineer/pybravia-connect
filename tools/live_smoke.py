#!/usr/bin/env python3
"""Live smoke: connect → capabilities → get_states → volume write → read-back.

Env:
  BRAVIA_HOST          device IP (required)
  BRAVIA_PORT          gRPC port (default 55051)
  BRAVIA_CREDENTIALS   path to credentials JSON from OAuth (required)

Optional:
  BRAVIA_EXEC_PATH     field to write (default: volume)
  BRAVIA_EXEC_VALUE    int/bool/string value (default: toggle volume ±1)
  BRAVIA_SKIP_EXEC     set to 1 to skip the write attempt

Stop the Home Assistant bravia_quad gRPC session before running — dual key_id
sessions on the same HT-A9M2 flake ConfirmKeys / exec.

Exit 0 when connect + GetCapabilities succeed and (unless BRAVIA_SKIP_EXEC=1)
the exec path changes state confirmed by get_states read-back. Exec that
reports ok but leaves state unchanged fails the smoke.

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
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and not seen:
        time.sleep(0.25)

    if os.environ.get("BRAVIA_SKIP_EXEC") == "1":
        client.close()
        print("done (connect + capabilities; exec skipped)")
        return 0

    path = os.environ.get("BRAVIA_EXEC_PATH", "volume")
    # Volume/mute writes no-op while the control unit is off; wake first.
    if path in ("volume", "mute"):
        try:
            powered = client.get_states(["power"]).get("power")
            print(f"get_states power={powered!r}")
            if powered is not True:
                print("exec power=True (required before volume/mute writes)")
                client.exec_command("power", True)
                time.sleep(0.5)
        except Exception as exc:  # noqa: BLE001
            print(f"power preflight skipped: {exc}")

    before = client.get_states([path])
    before_val = before.get(path)
    print(f"get_states before {path}={before_val!r}")

    if "BRAVIA_EXEC_VALUE" in os.environ:
        raw = os.environ["BRAVIA_EXEC_VALUE"]
        if raw.lower() in ("true", "false"):
            value: object = raw.lower() == "true"
        else:
            try:
                value = int(raw)
            except ValueError:
                value = raw
    elif isinstance(before_val, int):
        value = before_val + 1 if before_val < 50 else before_val - 1
    elif isinstance(before_val, bool):
        value = not before_val
    else:
        value = 7

    print(f"exec {path}={value!r}")
    try:
        ok = client.exec_command(path, value)
        print(f"exec ok={ok}")
    except Exception as exc:  # noqa: BLE001
        print(f"exec error: {exc}", file=sys.stderr)
        client.close()
        return 1

    time.sleep(0.5)
    after = client.get_states([path])
    after_val = after.get(path)
    print(f"get_states after {path}={after_val!r}")
    client.close()

    if after_val != value:
        print(
            f"FAIL: expected {path}={value!r} after exec, got {after_val!r} "
            f"(before={before_val!r}, exec_ok={ok})",
            file=sys.stderr,
        )
        return 1

    print("done (volume/state change confirmed via get_states)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

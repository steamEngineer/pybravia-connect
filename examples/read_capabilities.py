#!/usr/bin/env python3
"""Read-only: connect and print GetCapabilities JSON.

Env:
  BRAVIA_HOST          device IP (required)
  BRAVIA_CREDENTIALS   path to credentials JSON (required)
  BRAVIA_PORT          gRPC port (default 55051)

Stop any Home Assistant bravia_quad gRPC session on the same device first —
dual key_id sessions flake. Never commit credentials JSON.
"""

from __future__ import annotations

import os
import sys

from pybravia_connect import (
    DEFAULT_THEATRE_PORT,
    BraviaConnectClient,
    load_credentials,
)


def main() -> int:
    host = os.environ.get("BRAVIA_HOST")
    creds_path = os.environ.get("BRAVIA_CREDENTIALS")
    if not host or not creds_path:
        print("Set BRAVIA_HOST and BRAVIA_CREDENTIALS", file=sys.stderr)
        return 2

    port = int(os.environ.get("BRAVIA_PORT", str(DEFAULT_THEATRE_PORT)))
    creds = load_credentials(creds_path)
    client = BraviaConnectClient(
        host,
        port,
        creds["device_id"],
        creds["hmac_key"],
        key_id=creds.get("key_id"),
        session_key=creds.get("session_key"),
    )
    try:
        client.connect()
        print(client.get_capabilities_json())
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

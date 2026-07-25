# pybravia-connect

HA-agnostic Python client for Sony BRAVIA Connect local gRPC
(`ControlDeviceService`).

This is a **protocol library**, not a Home Assistant integration. Integrations
that speak BRAVIA Connect (for example
[bravia-quad-homeassistant](https://github.com/steamEngineer/bravia-quad-homeassistant)
and
[bravia-tv-grpc-homeassistant](https://github.com/braviafanboy/bravia-tv-grpc-homeassistant))
can depend on this package once cut over.

Protocol code was extracted from those integrations (MIT). Thanks to
@steamEngineer and @braviafanboy.

## Status

`0.1.0a3` — connect/handshake, `StartNotifyStates`, `GetCapabilities`,
`get_states`, `ExecCommandWithAuth` (fresh `GetSessionRandom` per write), and
nonce-gated TV `read_application_list` / `read_resource` (AES-GCM; needs
`session_key` + `[crypto]`).

## Install

```bash
pip install pybravia-connect==0.1.0a3
```

For local development:

```bash
pip install -e ".[dev]"
```

For TV app-list and icon reads (AES-GCM decrypt):

```bash
pip install "pybravia-connect[crypto]"
```

## Public API (sketch)

```python
from pybravia_connect import (
    BraviaConnectClient,
    DEFAULT_THEATRE_PORT,
    async_complete_oauth_flow,
    start_oauth_login,
    select_device,
    discover_grpc_port,
)
```

Sync gRPC client (run in an executor from asyncio). Async credentials use
`aiohttp.ClientSession`.

## Live smoke

```bash
export BRAVIA_HOST=192.168.x.x
export BRAVIA_PORT=55051          # Theatre default; TVs may need discovery
export BRAVIA_CREDENTIALS=/path/to/keys.json
python tools/live_smoke.py
```

Validated on HT-A9M2: connect/handshake, GetCapabilities, StartNotifyStates,
`get_states`, and volume writes via `exec_command` while powered on. Volume/mute
writes are no-ops when the control unit is off — live smoke wakes `power` first.
Stop any Home Assistant `bravia_quad` session on the same device before smoke
(dual `key_id` sessions flake).

## Regenerating protobuf stubs

```bash
python -m grpc_tools.protoc -Isrc/pybravia_connect/proto \
  --python_out=src/pybravia_connect/proto \
  --grpc_python_out=src/pybravia_connect/proto \
  src/pybravia_connect/proto/bravia_control.proto
```

Then re-apply two manual patches:

1. Make the `pb2_grpc` import relative: `from . import bravia_control_pb2`.
2. Register the descriptor in a **private** pool, not the global `Default()` one
   (`_pool = DescriptorPool()` / `DESCRIPTOR = _pool.AddSerializedFile(...)`).
   This avoids symbol collisions when co-installed with integrations that still
   vendor their own stubs.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest -q
```

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

`0.1.0a8` — connect/handshake, `StartNotifyStates`, `GetCapabilities`,
`get_capabilities_json`, `session_snapshot`, `get_states`,
`ExecCommandWithAuth` (fresh `GetSessionRandom` per write), and nonce-gated TV
`read_application_list` / `read_resource` (AES-GCM; needs `session_key` +
`[crypto]`). Public root also re-exports OAuth/Seeds helpers (including sync
`complete_oauth_flow` / `load_credentials` / `write_credentials`), capability
helpers, and TV constants used by HA consumers.

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Install

```bash
pip install pybravia-connect==0.1.0a8
```

For local development:

```bash
pip install -e ".[dev]"
pre-commit install  # optional local hooks; CI is the source of truth
```

For TV app-list and icon reads (AES-GCM decrypt):

```bash
pip install "pybravia-connect[crypto]"
```

## Public API (sketch)

```python
from pybravia_connect import (
    APPLICATION_LIST_PATH,
    BraviaConnectClient,
    DEFAULT_THEATRE_PORT,
    ZEROCONF_TYPE,
    async_complete_oauth_flow,
    async_credentials_from_oauth,
    async_exchange_oauth_redirect,
    async_get_device_states,
    async_get_devices,
    async_list_oauth_devices,
    async_refresh_access_token,
    complete_oauth_flow,
    discover_grpc_port,
    enum_values_from_capability,
    get_device_states,
    get_devices,
    get_session_keys,
    image_content_type,
    int_range_from_capability,
    is_int_capability,
    load_credentials,
    refresh_access_token,
    refresh_credentials,
    select_device,
    start_oauth_login,
    write_credentials,
)

client.get_capabilities_json()  # parsed GetCapabilities JSON (or None)
client.session_snapshot()  # connected + handshake flags for debug
```

Sync gRPC client (run in an executor from asyncio). Async credentials use
`aiohttp.ClientSession`. Sync Seeds helpers (`complete_oauth_flow`,
`refresh_credentials`, `get_devices`, …) are for scripts; prefer the
`async_*` variants from HA.

## CLI session keys

OAuth login and write a credentials JSON for local gRPC (never commit the
output):

```bash
python tools/get_session_keys.py --login --open -o /tmp/session_keys.json
```

Also supports `--code`, `--token`, `--refresh -i …`, and `--from-har` (Chrome
HAR + `--code-verifier`).

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

## Security

Local gRPC control assumes a **trusted private LAN**. Do not expose the device’s
gRPC port to the internet. Never commit session-key JSON, OAuth tokens, or HAR
files from the CLI tools.

See [SECURITY.md](SECURITY.md) for reporting and operator guidance, and
[THREAT_MODEL.md](THREAT_MODEL.md) for what is in scope for private advisories.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy
pytest -q
python -m build && twine check dist/*
```

## Releasing

1. Bump `__version__` in `src/pybravia_connect/__init__.py` (single source of truth).
2. Move `[Unreleased]` notes into a new `CHANGELOG.md` section for that version.
3. Commit, push to `main`, then tag and push:
   ```bash
   git tag vX.Y.ZaN
   git push origin vX.Y.ZaN
   ```
4. The Publish workflow builds, checks that the tag matches the wheel version,
   uploads to PyPI via Trusted Publishing, and creates a GitHub Release from the
   changelog section.
5. Bump the pin in consumer integrations (for example
   `bravia-quad-homeassistant` `custom_components/bravia_quad/manifest.json` and
   lockfile) in a separate change.

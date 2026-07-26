# pybravia-connect

[![PyPI](https://img.shields.io/pypi/v/pybravia-connect.svg)](https://pypi.org/project/pybravia-connect/)
[![Python versions](https://img.shields.io/pypi/pyversions/pybravia-connect.svg)](https://pypi.org/project/pybravia-connect/)
[![CI](https://github.com/steamEngineer/pybravia-connect/actions/workflows/ci.yml/badge.svg)](https://github.com/steamEngineer/pybravia-connect/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/pybravia-connect.svg)](LICENSE)

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

**Alpha** (`0.1.x` on PyPI). APIs may change before 1.0. See
[CHANGELOG.md](CHANGELOG.md) for release history. Apps that need a fixed
surface can pin a specific version in their own lockfile.

## Install

Requires Python 3.12+.

```bash
pip install pybravia-connect
```

`bravia-connect` is a reserved PyPI alias for the same release
(`pip install bravia-connect` installs `pybravia-connect` at the matching
version). Prefer the canonical name above; the import package is always
`pybravia_connect`.

For TV app-list and icon reads (AES-GCM decrypt):

```bash
pip install "pybravia-connect[crypto]"
```

For local development:

```bash
pip install -e ".[dev]"
```

## Quickstart

Obtain credentials JSON first (see [Credentials CLI](#credentials-cli)), then:

```python
from pybravia_connect import (
    BraviaConnectClient,
    DEFAULT_THEATRE_PORT,
    load_credentials,
)

HOST = "192.168.x.x"
CREDS_PATH = "/path/to/session_keys.json"  # never commit

creds = load_credentials(CREDS_PATH)
client = BraviaConnectClient(
    HOST,
    DEFAULT_THEATRE_PORT,  # or discover_grpc_port(HOST) for TVs
    creds["device_id"],
    creds["hmac_key"],
    key_id=creds.get("key_id"),
    session_key=creds.get("session_key"),
)
client.connect()
print(client.get_capabilities_json())
client.start_notify(lambda path, value: print(path, value))
# optional: client.get_states(["power", "volume"])
# optional write: client.exec_command("volume", 10)  # power on first
client.close()
```

`BraviaConnectClient` is synchronous — run it in an executor from asyncio.
The example is read-mostly; volume/mute writes no-op while the control unit is
off. Public exports are listed in `pybravia_connect.__all__`.

## Features

- Connect and auth handshake for local `ControlDeviceService` gRPC
- `GetCapabilities` / `get_capabilities_json` and capability helpers
- `StartNotifyStates` delta stream and `get_states`
- `ExecCommandWithAuth` (fresh session random per write)
- OAuth / Seeds credential helpers (sync for scripts; `async_*` for HA)
- TCP port discovery for non-Theatre devices (`discover_grpc_port`)
- Optional TV AES-GCM app-list / icon reads (`session_key` + `[crypto]`)

Validated on HT-A9M2 for connect/handshake, capabilities, notify, `get_states`,
and volume writes while powered on.

## Requirements

- Device on a **trusted private LAN** (do not expose the gRPC port)
- Credentials JSON with at least `device_id` and `hmac_key` (optional
  `key_id`, `session_key`)
- Theatre systems default to port `55051` (`DEFAULT_THEATRE_PORT`); TVs often
  need `discover_grpc_port`
- Stop any Home Assistant `bravia_quad` gRPC session on the same device before
  experimenting — dual `key_id` sessions flake

## Credentials CLI

OAuth login and write credentials for local gRPC (never commit the output):

```bash
python tools/get_session_keys.py --login --open -o /tmp/session_keys.json
```

See `python tools/get_session_keys.py --help` for `--code`, `--token`,
`--refresh`, and `--from-har`.

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — release history
- [SECURITY.md](SECURITY.md) — reporting and operator guidance
- [THREAT_MODEL.md](THREAT_MODEL.md) — advisory scope
- [Issues](https://github.com/steamEngineer/pybravia-connect/issues)
- [AGENTS.md](AGENTS.md) — contributor / agent conventions
- [docs/development.md](docs/development.md) — protobuf stub regeneration
- [docs/releasing.md](docs/releasing.md) — tagging and PyPI publish

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
```

Live device smoke (env details in the script docstring):

```bash
export BRAVIA_HOST=192.168.x.x
export BRAVIA_CREDENTIALS=/path/to/keys.json
python tools/live_smoke.py
```

Open PRs against `main` and complete
[`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)
(tick exactly one change type so CI can label the PR for release notes).
See [AGENTS.md](AGENTS.md) for agent/contributor conventions.

Protobuf regeneration and release steps:
[docs/development.md](docs/development.md),
[docs/releasing.md](docs/releasing.md).

## License

MIT. Protocol code was extracted from the integrations listed above; thanks to
@steamEngineer and @braviafanboy.

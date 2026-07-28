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

`bravia-connect` and `bravaconnect` are reserved PyPI aliases for the same
release (`pip install bravia-connect` or `pip install bravaconnect` installs
`pybravia-connect` at the matching version). Prefer the canonical name above;
the import package is always `pybravia_connect`.

For TV app-list and icon reads (AES-GCM decrypt):

```bash
pip install "pybravia-connect[crypto]"
```

For local development:

```bash
pip install -e ".[dev]"
```

## Quickstart

Obtain credentials JSON first (see [Credentials CLI](#credentials-cli)).
Stop any Home Assistant `bravia_quad` gRPC session on the same device before
experimenting — dual `key_id` sessions flake.

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

Or run the read-only example (clone of this repo):

```bash
export BRAVIA_HOST=192.168.x.x
export BRAVIA_CREDENTIALS=/path/to/session_keys.json
python examples/read_capabilities.py
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

OAuth login writes a credentials JSON file for local gRPC. Never commit the
output. After `pip install pybravia-connect` (from a release that includes the
console script):

```bash
bravia-connect-keys --login --open -o /tmp/session_keys.json
```

### Desktop OAuth walkthrough

1. Run the command above. It prints an authorize URL (and opens it with
   `--open`). Use an incognito/private window if the page is blank.
2. Sign in with your Sony account for **Home Entertainment & Sound Service**.
3. After login, the browser tries to open `ssh-app://signin?code=…`. On desktop
   that fails — the redirect is **not** in the address bar.
4. In Chrome DevTools (F12) → **Network** → filter `signin` → copy the
   `ssh-app://signin?…` Request URL or Location header, or just the `code=`
   value.
5. Paste that into the CLI prompt. With `-o`, the CLI writes the credentials
   JSON.

See `bravia-connect-keys --help` for `--code`, `--token`, `--refresh`, and
`--from-har`. From a git checkout, `python tools/get_session_keys.py` remains a
thin shim to the same entry point (useful before the console script is on PyPI,
or for local muscle memory).

### Credentials JSON shape

Required for local gRPC connect:

| Field | Role |
|-------|------|
| `device_id` | Seeds device id |
| `hmac_key` | Local gRPC auth material |

Often also present (optional for basic connect; used by some helpers):

| Field | Role |
|-------|------|
| `key_id` | Session key id |
| `session_key` | Session key (e.g. TV AES-GCM paths with `[crypto]`) |

The CLI also writes OAuth fields (`access_token`, `refresh_token`, and related
expiry helpers) so `--refresh` can mint new gRPC keys without a browser. Treat
the whole file as a secret — see [SECURITY.md](SECURITY.md).

Redacted example (placeholders only):

```json
{
  "device_id": "<device-id>",
  "hmac_key": "<redacted>",
  "key_id": "<redacted>",
  "session_key": "<redacted>",
  "access_token": "<redacted>",
  "refresh_token": "<redacted>"
}
```

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — release history
- [SECURITY.md](SECURITY.md) — reporting and operator guidance
- [THREAT_MODEL.md](THREAT_MODEL.md) — advisory scope
- [Issues](https://github.com/steamEngineer/pybravia-connect/issues)
- [CONTRIBUTING.md](CONTRIBUTING.md) — clone, lint, test, PRs
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

See [CONTRIBUTING.md](CONTRIBUTING.md) for the short contributor path.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy
pytest -q
```

Live device smoke (`tools/live_smoke.py`; stop HA gRPC on the same device first):

| Env | Required | Notes |
|-----|----------|-------|
| `BRAVIA_HOST` | yes | Device IP |
| `BRAVIA_CREDENTIALS` | yes | Path to credentials JSON |
| `BRAVIA_PORT` | no | Default `55051` |
| `BRAVIA_SKIP_EXEC` | no | Set `1` to skip writes |
| `BRAVIA_EXEC_PATH` | no | Field to write (default `volume`) |
| `BRAVIA_EXEC_VALUE` | no | Value to write (default toggles volume ±1) |

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

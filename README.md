# pybravia-connect

HA-agnostic Python client for Sony BRAVIA Connect local gRPC
(`ControlDeviceService`).

This is a **protocol library**, not a Home Assistant integration. Integrations
that speak BRAVIA Connect (for example
[bravia-quad-homeassistant](https://github.com/steamEngineer/bravia-quad-homeassistant)
and
[bravia-tv-grpc-homeassistant](https://github.com/braviafanboy/bravia-tv-grpc-homeassistant))
are expected to depend on this package once the protocol layer is extracted
here.

## Status

Scaffold only (`0.0.0`). Protocol extraction is in progress.

## Development

Requires Python 3.12+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest -q
```

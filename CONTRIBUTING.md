# Contributing

## Setup

```bash
git clone https://github.com/steamEngineer/pybravia-connect.git
cd pybravia-connect
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Lint, type check, tests

```bash
ruff check . && ruff format --check .
mypy
pytest -q
```

## Live device smoke

Needs `BRAVIA_HOST` and `BRAVIA_CREDENTIALS` (see README Development for the full
env list). Stop Home Assistant gRPC on the same device first.

```bash
python tools/live_smoke.py
```

## Pull requests

Open PRs against `main`. Fill in
[`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) and tick
exactly one change type.

## Further reading

- [README.md](README.md) — install, credentials CLI, Development
- [AGENTS.md](AGENTS.md) — agent / contributor conventions
- [docs/development.md](docs/development.md) — protobuf stub regeneration
- [docs/releasing.md](docs/releasing.md) — tagging and PyPI publish
- [SECURITY.md](SECURITY.md) — secrets hygiene and reporting

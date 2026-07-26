# AGENTS.md

## Behaviour

- Do not post GitHub PR or issue comments without explicit user consent.

## Branching and PRs

- All PRs target `main`.
- Fill in [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md); tick exactly one change type (CI applies the matching label automatically).
- PR title: functional description of the change. Do not use conventional commit prefixes such as `feat:`, `fix:`, or `chore:` — labels categorize PRs, not the title.
- PR body: include a test plan; device-facing protocol changes should note live smoke when applicable.

## Development

- `pip install -e ".[dev]"` — editable install + tools
- `ruff check . && ruff format --check .` — lint/format
- `mypy` — type check
- `pytest -q` — unit tests
- `python tools/live_smoke.py` — live device smoke (needs `BRAVIA_*` env; see README Development and the script docstring)
- `python -m build && twine check dist/*` — packaging check when metadata/build changes

Run ruff, mypy, and pytest after code changes.

## Code standards

- Match existing package layout under `src/pybravia_connect/`.
- Never commit session-key JSON, OAuth tokens, or HAR files.
- See README (Development / Security) and [SECURITY.md](SECURITY.md).

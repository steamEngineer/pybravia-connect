## Summary

<!-- What changed and why -->

## Test plan

- [ ] `ruff check . && ruff format --check .`
- [ ] `mypy`
- [ ] `pytest -q`
- [ ] `python -m build && twine check dist/*` (if packaging/metadata changed)

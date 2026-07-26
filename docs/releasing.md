# Releasing

1. Bump `__version__` in `src/pybravia_connect/__init__.py` (single source of truth)
   and the pin in `tests/test_smoke.py` (`test_version`).
2. Move `[Unreleased]` notes into a new `CHANGELOG.md` section for that version
   (and update the compare links at the bottom of the file).
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

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
   builds the PyPI aliases (dependency-only pins of this version), uploads the
   canonical package and aliases to PyPI via Trusted Publishing, and creates a
   GitHub Release from the changelog section.
5. Bump the pin in consumer integrations (for example
   `bravia-quad-homeassistant` `custom_components/bravia_quad/manifest.json` and
   lockfile) in a separate change.

## PyPI aliases (`bravia-connect`, `bravaconnect`)

The Publish workflow also uploads version-locked aliases named `bravia-connect`
and `bravaconnect` (`pip install <alias>` → depends on
`pybravia-connect==<same version>`). Import remains `pybravia_connect`. No
separate version bump or tag is required.

One-time setup per alias project: add a **pending** Trusted Publisher on PyPI
for that project name, same owner/repo (`steamEngineer` / `pybravia-connect`),
workflow `publish.yml`, environment `pypi`. The first tagged release after that
creates the project. `bravia-connect` is already claimed; add `bravaconnect`
before the release that first publishes it.

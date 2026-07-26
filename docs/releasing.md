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
   builds the `bravia-connect` PyPI alias (dependency-only pin of this version),
   uploads both to PyPI via Trusted Publishing, and creates a GitHub Release from
   the changelog section.
5. Bump the pin in consumer integrations (for example
   `bravia-quad-homeassistant` `custom_components/bravia_quad/manifest.json` and
   lockfile) in a separate change.

## PyPI alias (`bravia-connect`)

The Publish workflow also uploads a version-locked alias named `bravia-connect`
(`pip install bravia-connect` → depends on `pybravia-connect==<same version>`).
Import remains `pybravia_connect`. No separate version bump or tag is required.

One-time setup (already done for `pybravia-connect`): add a **pending** Trusted
Publisher on PyPI for project `bravia-connect`, same owner/repo
(`steamEngineer` / `pybravia-connect`), workflow `publish.yml`, environment
`pypi`. The first tagged release after that creates the project.

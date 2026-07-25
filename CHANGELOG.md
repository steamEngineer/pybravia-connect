# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- PyPI metadata (classifiers, project URLs, PEP 639 license) and hatch path
  versioning from `__version__`.
- CI matrix for Python 3.12–3.14, mypy, coverage reporting, and
  `build`/`twine check`.
- Tag publish workflow asserts tag==wheel version, creates a GitHub Release from
  the changelog, and drops ad-hoc `workflow_dispatch` publishes.

### Added

- `CHANGELOG.md`, `SECURITY.md`, Dependabot, PR template, release-drafter, and
  pre-commit hooks.

## [0.1.0a3] - 2026-07-25

### Added

- Nonce-gated TV `read_application_list` / `read_resource` with optional AES-GCM
  decrypt via the `[crypto]` extra.
- PyPI Trusted Publisher workflow for tagged releases.

## [0.1.0a2] - 2026-07-25

### Added

- `get_states` request/response helpers.
- Live volume smoke hardening for powered devices.

## [0.1.0a1] - 2026-07-25

### Added

- Initial public alpha: OAuth credentials helpers, connect/handshake,
  `StartNotifyStates`, `GetCapabilities`, and `ExecCommandWithAuth`.

[Unreleased]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a3...HEAD
[0.1.0a3]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/steamEngineer/pybravia-connect/releases/tag/v0.1.0a1

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0a5] - 2026-07-25

### Added

- Public re-exports on the package root for HA consumers: OAuth/Seeds helpers
  (`async_credentials_from_oauth`, `async_exchange_oauth_redirect`,
  `async_list_oauth_devices`, `async_get_device_states`, `async_get_devices`,
  `async_refresh_access_token`, plus sync `refresh_credentials` /
  `get_devices` / `get_device_states` / `get_session_keys`), capability helpers
  (`is_int_capability`, `int_range_from_capability`,
  `enum_values_from_capability`), TV constants (`APPLICATION_LIST_PATH`,
  `image_content_type`), and `ZEROCONF_TYPE`.

## [0.1.0a4] - 2026-07-25

### Changed

- PyPI metadata (classifiers, project URLs, PEP 639 license) and hatch path
  versioning from `__version__`.
- CI matrix for Python 3.12–3.14, mypy, coverage reporting, and
  `build`/`twine check`.
- Tag publish workflow asserts tag==wheel version, creates a GitHub Release from
  the changelog, and drops ad-hoc `workflow_dispatch` publishes.
- Allow `protobuf` `>=5,<8` (was `<7`).
- Bump GitHub Actions: `actions/checkout` v7.0.1, `actions/setup-python` v7.0.0,
  `softprops/action-gh-release` v3.0.2, `release-drafter/release-drafter` v7.6.0.

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

[Unreleased]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a5...HEAD
[0.1.0a5]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a4...v0.1.0a5
[0.1.0a4]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a3...v0.1.0a4
[0.1.0a3]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a2...v0.1.0a3
[0.1.0a2]: https://github.com/steamEngineer/pybravia-connect/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/steamEngineer/pybravia-connect/releases/tag/v0.1.0a1

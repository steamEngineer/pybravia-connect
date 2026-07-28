# Security Policy

## Supported versions

Security fixes are applied to the latest published release on PyPI.

## Threat model

Before reporting, read [THREAT_MODEL.md](THREAT_MODEL.md). It defines what is
in scope for a private advisory versus issues that are out of scope by design
(for example, cleartext local gRPC on a trusted LAN).

## Reporting a vulnerability

Please report security issues privately via
[GitHub Security Advisories](https://github.com/steamEngineer/pybravia-connect/security/advisories/new)
for this repository.

Do not open a public issue for vulnerabilities that could affect device
credentials or local-network control of BRAVIA Connect hardware.

## Secrets vs public client material

Treat these as **secrets** (never commit, never share in issues or logs):

- Session-key bundle fields: `hmac_key`, `session_key`, and related key material
- OAuth `access_token` and `refresh_token`
- Credential JSON files produced by `bravia-connect-keys` (or
  `tools/get_session_keys.py`) (for example `session_keys.json`)
- Browser HAR files that may contain redirect URLs or tokens (`*.har`)

These are **public client identifiers** embedded in the library (not user
secrets): Seeds `CLIENT_ID` and the Seeds `API_KEY` used as an app API key for
the official-style OAuth client.

## Operator guidance

- Run local control on a **trusted private network**. Do not expose the device’s
  local gRPC port (Theatre default `55051`) or other local control ports to the
  internet.
- Store credentials outside the git tree; prefer a restricted path used only by
  the controller (Home Assistant config entry, secrets file ignored by VCS).
- If credentials leak: discard the file, re-run OAuth / session-key minting, and
  update any host that stored the old bundle. Treat a leaked `refresh_token` or
  `hmac_key` as full control of that device until rotated.

## Contributor hygiene

- Never commit `session_keys.json`, `credentials*.json`, or HAR captures. The
  repository `.gitignore` covers common names; do not force-add them.
- Do not paste session keys, OAuth tokens, or full credentials JSON into issues,
  PRs, or CI logs.

## Repository security features

Maintainers should keep these enabled in GitHub repository settings:

**Code security / Secrets**

- **Dependabot alerts** and **Dependabot security updates** (version updates
  are already configured in `.github/dependabot.yml`)
- **Secret scanning**
- **Push protection** for secret scanning

**Branches / rules**

- **Branch protection** (or a repository ruleset) on `main`:
  - Require a pull request before merging
  - Require status checks to pass: `CI` jobs (`lint`, `test`, `package`) and
    `Dependency security` / `pip-audit`
  - Block force pushes and branch deletion
  - Prefer “do not allow bypassing the above settings” so admins cannot
    silently skip checks

CI also runs a lean `pip-audit` job on dependencies; remediate findings via
Dependabot or a manual pin bump.

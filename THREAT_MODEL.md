# Threat model

This document defines the trust boundary for **pybravia-connect** — a Python
client library for Sony BRAVIA Connect local gRPC — so real security bugs can be
told apart from defense-in-depth or deployment issues.

Related: [SECURITY.md](SECURITY.md) (how to report).

## Trust boundary

Trusted inputs by design:

1. **Credential holders** — anyone with a valid session-key bundle
   (`hmac_key`, `key_id` / session id, `device_id`, and optionally `session_key`
   plus OAuth tokens) minted via Sony Seeds for that device.
2. **Host operators** — anyone who can run this library or edit its credentials
   file / host config (shell on the controller, Home Assistant config entry
   access, and so on).

The security boundary is therefore **unauthenticated network traffic vs. those
trusted inputs**. A bug that lets an unauthenticated attacker cross it is a
security bug.

## What we do defend

These *are* in scope for a private report:

- Authentication bypass that allows local gRPC control **without** valid session
  keys or equivalent proof from the documented handshake.
- Bugs in this library that exfiltrate or log credentials (session keys, OAuth
  tokens) to unintended parties.
- Issues in this repository’s publish path that could compromise the PyPI
  package (for example, workflow privilege mistakes that allow unauthorized
  release).

## What is not a security vulnerability

- **Cleartext local gRPC** — the device speaks unencrypted h2c on the LAN; the
  library uses an insecure channel because that is the device protocol. App-layer
  HMAC (and AES-GCM where the device requires it) is the documented auth model,
  not transport TLS.
- **Attacks by someone who already holds valid session keys or OAuth tokens** —
  possession of those credentials is full local (and cloud key-refresh) control
  by design.
- **Exposing the device’s gRPC (or other local control) ports to the internet** —
  operator deployment choice; see operator guidance in [SECURITY.md](SECURITY.md).
- **Sony Seeds / cloud API issues** — report those to Sony, not this repository.
- **Local attackers with shell access** on the host that stores credentials or
  runs the client.
- **Supply-chain attacks against third-party dependencies** — tracked via
  Dependabot and CI audit; not private advisories unless they are specific to
  how *this* package publishes or vendors code.

## Reporting

If you believe you have found an issue that crosses the unauthenticated boundary
above, report it privately via GitHub Security Advisories as described in
[SECURITY.md](SECURITY.md). Read this document first for likely out-of-scope
cases.

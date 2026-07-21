# Security Policy

## Reporting a vulnerability

Report security issues through the private project communication channel.

Do not open a public issue for a suspected vulnerability.

## Rules

- Do not publish secrets (API keys, tokens, credentials, private keys) in
  this repository, in commits, in issues, or in pull requests.
- Do not use real personal data anywhere in this repository — no real names,
  emails, government identifiers, or identity documents. Use synthetic
  fixtures only.
- Do not disclose suspected vulnerabilities publicly before they have been
  triaged through the private project communication channel.
- There is currently no production deployment of this platform. This
  infrastructure skeleton (CLAUDE-PACK-01) does not expose any running
  service, API, or database.
- Any security-critical change (authentication, credential handling,
  cryptography, anonymity guarantees, audit integrity) requires a separate,
  dedicated review in addition to normal code review, and — where it touches
  the canon — an accepted ADR.

## Scope

This policy applies to the `epd2-civic-os` repository as a whole. As
individual services are introduced in later packages, they may define
additional, more specific security requirements.

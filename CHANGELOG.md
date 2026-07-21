# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - initial repository skeleton

### Added

- Repository skeleton for EPD² Civic OS (CLAUDE-PACK-01).
- Canonical domain and event model (TZ-00, canon version 0.1.0) placed at
  `docs/canonical/TZ-00-domain-event-canon.md`.
- Architecture documentation (`docs/architecture/`) and initial ADRs
  (`docs/adr/`).
- Root Python workspace managed with `uv`, and the `epd2-core` shared
  package (version constants, UUID identifier helpers).
- Shared TypeScript package `epd2-types` (version constants).
- Minimal Next.js frontend skeleton (`frontend/web-shell`).
- Repository structure checks and top-level tests
  (`scripts/`, `tests/repository/`).
- `Makefile` with a unified command interface (`setup`, `format`, `lint`,
  `typecheck`, `test`, `check-repository`, `verify`, `clean`).
- Pre-commit configuration and GitHub Actions CI workflow.
- Contribution, security, and CODEOWNERS documentation.

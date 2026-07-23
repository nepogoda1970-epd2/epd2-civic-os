# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - participation and decision kernel

### Added

- Six independent, in-memory-backed services (CLAUDE-PACK-03,
  "Participation and Decision Kernel"): `initiative-service`,
  `deliberation-service`, `moderation-service`, `voting-service`,
  `tally-service`, `delegation-service`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter, following ADR-005's service decomposition.
- All 18 canon-scoped entities across the six new services: `Initiative`,
  `InitiativeVersion`, `SupportRecord`, `Amendment`, `SourceRecord`
  (initiative-service); `Discussion`, `Contribution`
  (deliberation-service); `ModerationCase`, `ModerationDecision`, `Appeal`
  (moderation-service); `Ballot`, `BallotOption`, `VoteEnvelope`,
  `VoteReceipt` (voting-service); `Tally`, `ResultPublication`
  (tally-service); `Delegation`, `DelegationSnapshot`
  (delegation-service) - each with its explicit `ALLOWED_TRANSITIONS`
  state machine (where canon defines a status enum), application-layer
  commands, canonical event construction, and `epd2_audit_core` audit
  entries for every state-changing action.
- `docs/adr/ADR-005` through `ADR-006`, `ADR-008` through `ADR-010`
  (service decomposition, reason-code additions, PACK-02 integration
  boundary, voting/delegation/quorum/tie/challenge/finality defaults, and
  the canon minor-version addition those defaults required), all accepted
  (ADR-009/ADR-010 with owner amendments) prior to this implementation.
- Structural, fail-closed enforcement of every accepted ADR-009 voting
  default: vote changes allowed until close with only the latest valid
  envelope counted (items 1-2); abstention modeled as an explicit
  `BallotOption` (item 3); `Ballot.ballot_method` restricted to
  `single_choice`/`yes_no` for this pilot (item 4); quorum optional per
  ballot (item 5); a second, distinct actor required to approve final
  ballot configuration (item 7, INV-08); `Delegation`/`DelegationSnapshot`
  implemented fully but disabled by default per ballot, maximum
  delegation depth 1 (items 8-9); a delegator's own direct vote overrides
  their delegate's (item 10); ties recorded as an explicit
  `tie_no_decision` outcome, never silently broken (item 11); and
  `Ballot.challenge_window_hours`/`ResultPublication.challenge_deadline_at`
  (canon 0.2.0, ADR-010) implemented with a 72-hour repository default,
  configurable per ballot, and a `compute_finality_state` function that
  can only ever return a provisional value - no PACK-03 code path may
  declare a `ResultPublication` final (items 12-13).
- ADR-009 item 14 (accepted with amendment): the canonical `invalidated`
  `Ballot` status and its transition structure are implemented, but no
  PACK-03 application-layer command can reach it - ballot invalidation
  authorization belongs entirely to the future Governance service.
- Structural identity-separation and vote-linkability guarantees
  (CT-00-08/CT-00-09) extended to `VoteEnvelope`, `VoteReceipt`, `Tally`,
  `ResultPublication`, `SupportRecord`, and `Delegation`: none may contain
  `account_id`, `person_id`, or `identity_record_id`, enforced via
  `additionalProperties: false` JSON Schemas and per-entity
  `FORBIDDEN_FIELD_NAMES` structural tests, plus a positive-space
  regression test proving no code path resolves a `VoteEnvelope` to an
  `Account`.
- The narrow, ADR-008-governed PACK-03 -> PACK-02 read boundary:
  `initiative-service` and `voting-service` call
  `epd2_credential_service.application.validate_participation_credential`
  and two new, additive, read-only `epd2_eligibility_service.application`
  query functions (`get_eligibility_decision`, `get_eligibility_snapshot`)
  - never either service's `storage`/`domain` modules. No other PACK-03
    service depends on PACK-02, no PACK-02 service depends on PACK-03, and
    no PACK-03 service imports another PACK-03 service's package.
- `contracts/reason-codes/pack-03.yml` (70 entries: 9 PACK-03-relevant
  canon section-24 codes, 5 reused generic canon codes, and PACK-03's own
  additive codes per ADR-006), 18 entity JSON Schemas and 18 event-payload
  JSON Schemas (`contracts/schemas/`, `contracts/events/`), and
  `contracts/openapi/pack-03.yaml` (71 paths, one per real application
  command, tagged per service).
- CT-00-01 through CT-00-10 extended to cover all six new services
  (`tests/contract/`); CT-00-11/12 remain explicitly not-applicable for
  PACK-03 (no `AIProcessingRecord`/`EmergencyAction` in scope), the same
  treatment PACK-02 gave them.
- `tests/repository/test_service_boundaries.py` extended with the PACK-03
  service matrix, the ADR-008 `.application`-only PACK-03->PACK-02 edges,
  and the one-way PACK-02/PACK-03 dependency direction, as their own
  dedicated, AST-based structural tests (not merely re-running the
  existing PACK-02-only check).
- `docs/handover/PACK-03-REPORT.md`.

### Changed

- `scripts/check_repository.py` `REQUIRED_PATHS` extended for every new
  PACK-03 path (six services, contracts, and the report).
- Root `pyproject.toml` / `package.json` workspace membership, `ruff`,
  `mypy`, and `pytest` configuration extended to cover the six new
  services; `Makefile`'s `typecheck` target gained six new scoped mypy
  invocations.
- `docs/canonical/canon-version.json`'s `repository_compatibility` range
  widened from `>=0.1.0 <0.3.0` to `>=0.1.0 <0.4.0` to admit
  `REPOSITORY_VERSION 0.3.0` - this is repository-side bookkeeping, not
  canon-immutable content; the canon document's own text and checksum are
  unchanged by this pack (still `0.2.0`,
  `5ed52c3a6a94e821323616ac369595fd364a71115cf5c1c6763d8edb51a6044a`).

## [Unreleased] - canon minor version 0.2.0

### Changed

- `docs/canonical/TZ-00-domain-event-canon.md`: canon version `0.1.0 →
0.2.0` (ADR-010, accepted with amendment) — the first edit to this
  document's own text since its original acceptance. Adds two
  backward-compatible fields: `Ballot.challenge_window_hours` (optional,
  repository default 72 hours, configurable per ballot) and
  `ResultPublication.challenge_deadline_at` (computed as `published_at +
challenge_window_hours`), plus a clarifying note that reaching
  `challenge_deadline_at` is necessary but not sufficient for finality —
  a canonical or explicitly approved technical-challenge registration and
  adjudication mechanism must exist first (its own future ADR).
  `docs/canonical/canon-version.json`, `packages/python/epd2-core/src/epd2_core/version.py`,
  and `packages/typescript/epd2-types/src/version.ts` updated to match;
  `REPOSITORY_VERSION` is unchanged (`0.2.0`) since no PACK-03 service
  code exists yet.

## [0.2.0] - identity separation and audit kernel

### Added

- Five independent, in-memory-backed services (CLAUDE-PACK-02):
  `account-service`, `identity-service`, `eligibility-service`,
  `credential-service`, `audit-core`, each with its own `README.md`,
  `pyproject.toml`, `src/`, `tests/`, storage interface, and in-memory
  reference adapter.
- `epd2-audit-core`: append-only, hash-chained `AuditEvent` store
  (canon 18.1, INV-04/INV-05) with idempotent append by `audit_event_id`
  and fail-closed conflict detection on a duplicate id with different
  content.
- Identity/participation separation (INV-01): `Account` -> `IdentityRecord`
  -> `EligibilityRule`/`EligibilityDecision`/`EligibilitySnapshot` ->
  `ParticipationCredential`, with no identity-linking field on the
  credential, enforced by an automated identity-leakage test suite.
- Centralized, executable reason-code registry
  (`contracts/reason-codes/pack-02.yml`), JSON Schemas
  (`contracts/schemas/`), event payload schemas (`contracts/events/`), and
  a transport-neutral OpenAPI contract (`contracts/openapi/pack-02.yaml`).
- Contract test suite (`tests/contract/`): CT-00-01 through CT-00-10,
  CT-00-11/12 explicitly marked not-applicable; identity-leakage,
  state-transition, audit, and Hypothesis property-based tests.
- ADR-002 (identity/participation separation and canonical event/name
  resolution), ADR-003 (append-only audit hash chain), ADR-004
  (centralized reason-code registry), plus new architecture docs
  (`docs/architecture/identity-participation-separation.md`,
  `docs/architecture/audit-kernel.md`) and
  `docs/review/PACK-02-THREAT-MODEL.md`.
- `docs/handover/PACK-02-REPORT.md`.

### Changed

- `scripts/check_repository.py` and `scripts/check_forbidden_files.py`
  updated for PACK-02 (new required paths; a filename-based check for a
  forbidden central identity-participation mapping table/file, pack
  section 15).
- Root `pyproject.toml` / `package.json` workspace membership, `mypy`,
  and `pytest` configuration extended to cover the five new services and
  `tests/contract/`.

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

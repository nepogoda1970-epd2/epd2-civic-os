# Contracts

Versioned contracts between EPD² Civic OS modules. As of `CLAUDE-PACK-02`
this directory contains real, executable content for the five services'
canonical entities and events - `CLAUDE-PACK-01` shipped only the
directory structure and a documentary reason-code list.

## Directories

- `openapi/` — `pack-02.yaml`: transport-neutral API contracts for the five
  PACK-02 services (pack section 11). No production HTTP server ships in
  this pack.
- `events/` — versioned JSON Schemas for each canonical event's `payload`
  (canon sections 20–21). One schema per payload shape actually emitted by
  a PACK-02 service; wraps into `schemas/event-envelope.schema.json`'s
  `payload` field.
- `schemas/` — JSON Schema descriptions of the canonical entities in scope
  (`Account`, `IdentityRecord`, `EligibilityRule`, `EligibilityDecision`,
  `EligibilitySnapshot`, `ParticipationCredential`, `AuditEvent`) plus the
  canonical event envelope itself.
- `reason-codes/` — `pack-02.yml`: the executable, centralized reason-code
  registry (pack section 10). See `reason-codes/README.md` and
  `docs/adr/ADR-004-reason-code-registry.md`.
- `fixtures/` — test fixtures for contract tests (canon section 27),
  populated under Task 20's `tests/contract/` suite.

## Validation

Every schema here is standard JSON Schema (draft 2020-12) and is validated
two ways:

- In CI (`.github/workflows/verify-and-package.yml`), with the real
  `jsonschema` package (network access available there).
- Locally in this sandbox (no network access to install `jsonschema`),
  with `epd2_core.minimal_json_schema` - a small, dependency-free
  validator supporting a documented subset of JSON Schema keywords
  (`type`, `required`, `properties`, `additionalProperties`, `enum`,
  `items`, `minLength`, `format: uuid|date-time`). Every schema in this
  directory is written to validate correctly under both.

`additionalProperties: false` on `participation-credential.schema.json`
and the `credential.issued`/`credential.revoked` event payload schemas is
a load-bearing identity-leakage control (CT-00-08): no identity field
(`identity_record_id`, `person_id`, `account_id`, `full_name`,
`date_of_birth`, `address`, `email`, `eid_subject`) can appear on any
instance that validates against them.

## Versioning rule

Any change to a contract in these directories is versioned. A backward
incompatible change requires a new major version, not a silent
replacement of an existing version's meaning (see `CONTRIBUTING.md` and
canon section 25).

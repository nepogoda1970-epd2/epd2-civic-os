# PACK-11 — implementation report

**Round:** CLAUDE-PACK-11 — Governed Documents & Evidence
**Artifact:** `EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_CANDIDATE.zip`
**Status:** CANDIDATE. **Not** a FINAL PASS. **Not** a PACK-11 PASS.
**Baseline:** `EPD2_PACK-10_PARTY_FINANCE_0.10.0_FINAL_PASS.zip`

## Version state

| Constant                                 | Value                                      | Source of truth                                                                                                       |
| ---------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `REPOSITORY_VERSION`                     | `0.11.0`                                   | `packages/python/epd2-core/src/epd2_core/version.py`, `packages/typescript/epd2-types/src/version.ts`, `CHANGELOG.md` |
| `CANON_VERSION`                          | `0.8.0` (unchanged)                        | `docs/canonical/canon-version.json` and both version files                                                            |
| `document_context_implementation_status` | `reference_implementation`                 | `docs/canonical/canon-version.json`                                                                                   |
| `finance_context_implementation_status`  | `reference_implementation` (unchanged)     | `docs/canonical/canon-version.json`                                                                                   |
| `repository_compatibility`               | `>=0.1.0 <0.12.0` (widened from `<0.11.0`) | `docs/canonical/canon-version.json`                                                                                   |

`docs/canonical/TZ-00-domain-event-canon.md` is **byte-for-byte untouched**.
This round amends no canon; it implements a context canon 19f.22 already
assigned to PACK-11.

Why `reference_implementation` and not `implemented`: the governed
workflow, the integrity model, the authorization model and the consumer
interface are real and tested; the production data plane, durable content
storage and an external anchor for the chain head are not. `implemented`
would be a false production claim of exactly the kind `FIR-INV-015`
forbids. `not_implemented` was true before this round and is now false.

## What shipped

`services/document-service` — thirteen modules, 358 tests. See
`docs/packs/PACK-11-IMPLEMENTATION.md` for the module map and the design
decisions, `docs/packs/PACK-11-SPECIFICATION.md` for the model, and
`docs/packs/PACK-11-ACCEPTANCE-MATRIX.md` for criterion-to-test evidence.

Six proposed ADRs: ADR-055 (decomposition and reason codes), ADR-056
(authority separation and access), ADR-057 (immutable versions and the
hash-linked chain), ADR-058 (evidence, custody and bundles), ADR-059
(governed determinations), ADR-060 (publication separation and the
projection surface).

`contracts/reason-codes/pack-11.yml` — 71 entries, none canon-owned,
because canon section 24 registers no document or evidence code at all.

Four JSON Schemas in `contracts/schemas/`.

`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` — placed at
its canonical repository path and updated with exact PACK-11 status,
evidence paths and remaining work.

## FIR traceability

**Fully implemented:** `FIR-ROADMAP-001`, `FIR-INV-010`.

**Foundation only, explicitly not implemented:** `FIR-DEC-001`,
`FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`, `FIR-PROG-002`,
`FIR-INIT-021`, `FIR-PAY-003`, `FIR-DATA-003`.

No foundation-only entry is marked `implemented` in the register, and
`epd2_document_service.IMPLEMENTED_FIR_ENTRIES` names only the two —
asserted by `test_privacy_boundary.py`, so the claim is executable.

**New FIR entries created by implementation discovery:** none. Full detail
in `docs/packs/PACK-11-FIR-TRACEABILITY.md`.

## Verification performed

| Check                                                               | Result                                                                                                                                                                                                    |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/document-service/tests` (13 modules)                      | **358 passed, 0 failed**                                                                                                                                                                                  |
| `scripts/check_canon_0_8_0.py`                                      | **18/18 checks pass** (17 pre-existing + 1 new)                                                                                                                                                           |
| `scripts/verify_versions.py`                                        | **consistent**                                                                                                                                                                                            |
| `scripts/check_repository.py`                                       | **all required paths present**                                                                                                                                                                            |
| `scripts/check_forbidden_files.py`                                  | **clean** (git-trackable paths)                                                                                                                                                                           |
| Reason-code registry                                                | 71 unique entries; every literal in `services/document-service/src` registered                                                                                                                            |
| Line length ≤ 100, trailing whitespace, EOF newline, unused imports | clean across `services/document-service`                                                                                                                                                                  |
| Full end-to-end lifecycle smoke run                                 | register → version → review → approve → authorize → publish → rendition → determinations → evidence → bundle → retention → hold → integrity → read → projections → resolution, with an intact audit chain |

## Verification **not** performed, and why

This sandbox has no package-index access, so `pytest`, `ruff`, `mypy`,
`uv lock`/`uv sync`, `npm install` and `next build` could not run. The test
suite above was executed with a local runner over the same pytest-style
test modules, and the lint checks named above are approximations of the
repository's ruff configuration.

This is the same limitation every prior pack recorded in
`LOCAL_VERIFICATION.md`, and CI is where it is resolved. Before this
candidate is considered for PASS, `make verify` must run green on a runner
with network access.

## Boundary state

`document-service` imports `epd2-core` and `epd2-audit-core` and nothing
else. No other service imports it. PACK-09's and PACK-10's placeholder
reference types are **deliberately unchanged** — see
`docs/packs/PACK-11-CROSS-PACK-BOUNDARIES.md` and OD-21.

Four repository-level boundary tests enforce this in
`tests/repository/test_service_boundaries.py`.

## What this round does not claim

No legal validity. No evidential admissibility. No signature verification.
No qualified-electronic-signature conformance. No tamper _resistance_ —
the chain is tamper evidence and the limitations document says so. No
production readiness. No assertion about German party law.

See `docs/handover/PACK-11-KNOWN-LIMITATIONS.md` and
`docs/packs/PACK-11-OPEN-DECISIONS.md` (OD-20 through OD-26).

# PACK-13 — FIR Coverage Matrix

**The treatment columns below come from the PACK-13 specification round
and are unchanged.** The implementation-coverage appendix at the end is
added by the PACK-13 Implementation Candidate (`0.13.0`).

> **Status, as of the PACK-13 FINAL PASS round (2026-07-30):**
> **PACK-13 EXTERNAL CI PASS · FINAL PASS ARCHIVE PREPARED ·
> `REPOSITORY_VERSION` `0.13.0` · `CANON_VERSION` `0.8.0` ·
> NOT PRODUCTION READY · NOT LEGALLY ACTIVATED.** See
> `docs/handover/PACK-13-FINAL-PASS-REPORT.md`.
>
> The treatment columns below are **unchanged by the PASS**, and this
> document still records **zero** `implemented` treatments — asserted
> structurally by `tests/repository/test_pack13_fir_matrix.py`
> (`AC-P13-155`), which the passing pipeline itself ran. Where a status
> moved, it moved in the **Master Future Implementation Register**, which
> is where FIR status lives: `FIR-ROADMAP-003` is now
> `implemented in reference form` there. This matrix records what the
> PACK-13 rounds _did with each entry_, and that record does not change
> because a pipeline went green.

**No FIR entry is marked `implemented` by this round, and none may be.**
That was true of the specification round because a specification round
produces requirements rather than implementations. It remains true after
the external GitHub Actions PASS for a different and equally binding
reason: **every storage adapter in this pack is in memory**. A green
pipeline verifies the tree and deploys nothing, so `implemented` claimed
on its strength would be a claim the evidence does not support.

The `PACK-13 treatment` column records what the specification round did
with each entry; the `Implementation-stage obligation` column records what
the implementation round must do before any status change is even
arguable; and the appendix records what the candidate actually built
against each obligation.

Treatment values: **addressed** (fully specified), **partially addressed**
(specified in part, remainder named), **deferred** (recorded as a
dependency owned by a later pack), **unchanged** (untouched by PACK-13).

---

## 1. Roadmap

| FIR               | Status before | Treatment | References                               | Implementation-stage obligation                                                                                         | Reason for deferral |
| ----------------- | ------------- | --------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `FIR-ROADMAP-003` | `approved`    | addressed | whole package; spec §1–§35; ADR-069..078 | Build the data plane; satisfy every PASS-blocking criterion in the acceptance matrix; only then propose a status change | —                   |

`FIR-ROADMAP-003` MUST NOT move past `scheduled` or `under_review` on the
strength of this round.

**Where that stands after the PASS (added 2026-07-30).** "This round" in
the sentence above is the **specification** round, which produced
requirements and no code — its restriction is satisfied and remains
historically accurate. The implementation round then built the package and
an external GitHub Actions run passed every stage, and on that strength the
Master Register moved the entry to **`implemented in reference form`** —
not to `implemented`, because every storage adapter is still in memory. The
restriction this line records was never a bar on a verified implementation
round; it was a bar on claiming one from a document.

---

## 2. Hard invariants

| FIR                                               | Status before                   | Treatment           | References                                                                                               | Implementation-stage obligation                                                                                                                                                                                   | Reason for deferral                                                                                                                                                                                                                                                                         |
| ------------------------------------------------- | ------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-INV-001` — no global user ID                 | `approved`                      | addressed           | `P13-DP-008`, `P13-DP-016`, `P13-IDEM-003`, `P13-ID-001`..`005`, `P13-MIG-015`, `P13-PROJ-006`; T-P13-03 | Structural tests: no cross-domain identity key in any schema, projection, index or idempotency key; a migration gate that fails on one                                                                            | Behavioural correlation is not closed by any pack                                                                                                                                                                                                                                           |
| `FIR-INV-002` — identity/ballot unlinkability     | `approved`                      | partially addressed | `P13-DP-017`, `P13-VOTE-001`..`011`, `P13-MIG-016`, `P13-OBS-003`; T-P13-27                              | Structural absence tests for the general plane: no ballot content or secret, no identity-to-ballot join, no identity-linked ballot payload on the general bus, no global identifier as a Voting Client identifier | **The voting architecture and its topology are PACK-15/16's**, which must demonstrate isolation and unlinkability against their own threat model (`P13-VOTE-009`). PACK-13 supplies general data-plane constraints only and prescribes no broker, connection, credential or naming topology |
| `FIR-INV-004` — eligibility/credential separation | `approved`                      | partially addressed | ownership matrix §3.2, `P13-OWN-004`, `P13-OWN-012`                                                      | Prove no shared key, schema or join path — for the baseline reference implementations now, and for whatever owners PACK-15 establishes later                                                                      | **Both boundaries are reserved future ownership**; final owners and topology are PACK-15's                                                                                                                                                                                                  |
| `FIR-INV-005` — no intermediate tally             | `approved`                      | partially addressed | `P13-VOTE-004`, `P13-VOTE-005`                                                                           | Structural absence of any tally-shaped projection or analytics copy                                                                                                                                               | Tally semantics owned by PACK-15/16                                                                                                                                                                                                                                                         |
| `FIR-INV-006` — safe feature flags                | `approved`                      | addressed           | `P13-GOV-004`, `P13-SEC-006`; T-P13-28                                                                   | Prove no flag, environment switch or emergency path skips a compatibility gate, a migration gate, an audit append or an invariant                                                                                 | —                                                                                                                                                                                                                                                                                           |
| `FIR-INV-007` — DLP and controlled export         | `approved`                      | partially addressed | `P13-EXPORT-001`..`004`, `P13-SRCH-001`..`007`, `P13-SEC-007`; T-P13-18, T-P13-19                        | Prove no raw-export bypass exists via dump, replica, backup or analytics copy                                                                                                                                     | **Export and DLP policy remain PACK-12's**; PACK-13 supplies contracts only                                                                                                                                                                                                                 |
| `FIR-INV-010` — document version integrity        | `implemented in reference form` | unchanged           | `P13-DP-010`, `P13-MIG-014`, `P13-DOC-004`; T-P13-22                                                     | Preserve, do not reimplement: no migration or rollback may rewrite a hash-linked history                                                                                                                          | Implemented by PACK-11                                                                                                                                                                                                                                                                      |
| `FIR-INV-011` — statistical disclosure control    | `approved`                      | partially addressed | `P13-PROJ-005`, `P13-VOTE-004`                                                                           | Provide release-history persistence for PACK-12's cumulative model; ensure no projection becomes an uncontrolled aggregate source                                                                                 | **The SDC rules are PACK-12's**; the analytics engine is a later pack's                                                                                                                                                                                                                     |
| `FIR-INV-013` — Bund/Land/Kreis isolation         | `approved`                      | addressed           | `P13-DP-005`, `P13-CTX-002`, `P13-PROJ-011`, `P13-MIG-012`; T-P13-04                                     | Conformance test: every scoped table has the column; every projection carries it; a migration gate fails on loss                                                                                                  | —                                                                                                                                                                                                                                                                                           |
| `FIR-INV-015` — no false production claims        | `approved`                      | addressed           | §34, `P13-FE-008`, `P13-BAK-011`                                                                         | Forbidden-phrase scans across code, docs and operator surfaces; no production-readiness or legal-activation claim anywhere                                                                                        | —                                                                                                                                                                                                                                                                                           |
| `FIR-INV-003` — Voting Client isolation           | `approved`                      | unchanged           | `P13-VOTE-007` referenced only                                                                           | Structural absence of a global member ID in that plane                                                                                                                                                            | Owned by PACK-15/16                                                                                                                                                                                                                                                                         |
| `FIR-INV-008` — institutional role separation     | `approved`                      | unchanged           | `P13-SEC-005` references PACK-12's matrix                                                                | Database roles must not reconstitute a forbidden pair                                                                                                                                                             | Implemented by PACK-08/PACK-12                                                                                                                                                                                                                                                              |
| `FIR-INV-012` — accessibility                     | `approved`                      | unchanged           | `P13-FE-007` referenced only                                                                             | Administrative surfaces meet the existing obligation                                                                                                                                                              | Owned by FRONT-PACK                                                                                                                                                                                                                                                                         |
| `FIR-INV-014` — no universal administration       | `approved`                      | addressed           | `P13-SEC-001`, `P13-SEC-005`; T-P13-17                                                                   | Prove no database role combines cluster operation with domain-content read                                                                                                                                        | Residual: a superuser can read what the engine decrypts — PACK-14/17                                                                                                                                                                                                                        |

---

## 3. Data governance

| FIR                                                 | Status before                   | Treatment           | References                                                    | Implementation-stage obligation                                                                                                  | Reason for deferral                                                 |
| --------------------------------------------------- | ------------------------------- | ------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `FIR-DATA-001` — data catalog & processing registry | `approved`                      | partially addressed | `P13-DP-006`, `P13-RET-001`, `P13-RET-002`; ownership matrix  | Bind every persistent class to a record class and a processing purpose; make the binding queryable                               | **The catalog and processing registry themselves remain PACK-09's** |
| `FIR-DATA-003` — legal hold                         | `approved` (PACK-11 foundation) | partially addressed | `P13-RET-002`..`006`, `P13-MIG-013`, `P13-PROJ-010`; T-P13-16 | Observe hold state before every deletion, migration and propagation; fail closed when unknown; never treat hold as authorization | **Hold semantics remain PACK-09's**; PACK-13 observes and preserves |
| `FIR-DATA-002` — deadline management                | `approved`                      | unchanged           | referenced only                                               | Deadline jobs are idempotent (§11)                                                                                               | Owned by PACK-09                                                    |

---

## 4. Requirements inherited from PACK-09, PACK-11 and PACK-12

| Source  | Requirement                                                                 | Treatment           | Implementation-stage obligation                                                                                                    |
| ------- | --------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| PACK-09 | Retention schedules, deletion eligibility, destruction evidence, tombstones | partially addressed | Persist and propagate; decide nothing                                                                                              |
| PACK-09 | Records governance asked, never bypassed                                    | addressed           | `P13-OWN-005`; no domain reads the hold table directly                                                                             |
| PACK-02 | Append-only hash-chained audit                                              | addressed           | `P13-DP-014a`, `P13-OWN-014`: all domains **submit** through the governed audit-ingestion contract; only `audit-core` **persists** |
| PACK-11 | Immutable hash-linked versions, sealed evidence bundles                     | addressed           | `P13-DP-010`; no `UPDATE`/`DELETE` in the persistence contract                                                                     |
| PACK-11 | Evidence references for governed artifacts                                  | addressed           | Migration plans and verification reports use them (`P13-DOC-002`)                                                                  |
| PACK-12 | Privileged grants for migration and direct SQL                              | addressed           | `P13-SEC-002`, `P13-SEC-003`                                                                                                       |
| PACK-12 | Search policy, index policy, suppression                                    | partially addressed | Contracts only; policy untouched (`P13-SRCH-001`)                                                                                  |
| PACK-12 | Governed export, DLP, disclosure control                                    | partially addressed | Contracts only; `P13-EXPORT-004` closes the database bypass                                                                        |
| PACK-12 | Session evidence, no secrets in records                                     | addressed           | `P13-OBX-008`, `P13-OBS-002`                                                                                                       |

---

## 5. Architecture Framework schema and contract evolution requirements

| Requirement                             | Treatment | References                |
| --------------------------------------- | --------- | ------------------------- |
| Canonical schema registry               | addressed | §12, ADR-073              |
| API contract versioning and deprecation | addressed | §15, ADR-074              |
| Event schema evolution and upcasting    | addressed | §16, ADR-074              |
| Compatibility classification            | addressed | §14, compatibility matrix |
| Migration discipline                    | addressed | §18–§20, ADR-075          |
| Idempotency                             | addressed | §11, ADR-077              |
| Outbox and delivery semantics           | addressed | §8–§10, ADR-071, ADR-072  |
| Projection governance                   | addressed | §21, ADR-076              |

---

## 6. Production-blocked items depending on the data plane

| Item                             | PACK-13 treatment                                                                                 | Still blocked by                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Production database              | **deferred to implementation** — architecture and acceptance criteria specified, nothing deployed | the implementation round; provider procurement (§34)                         |
| Production event bus             | deferred                                                                                          | implementation; PACK-17 operations                                           |
| Production search engine         | deferred                                                                                          | implementation; PACK-12 policy remains                                       |
| Real payment/banking integration | unchanged                                                                                         | PACK-14 and external agreements                                              |
| Production identity              | unchanged                                                                                         | PACK-14                                                                      |
| Real external gateway activation | unchanged                                                                                         | PACK-14                                                                      |
| Operational finance UI           | unchanged                                                                                         | FRONT-PACK                                                                   |
| Backup and restore capability    | deferred                                                                                          | **PACK-17**; `P13-BAK-011` forbids claiming readiness without a restore test |

---

## 6a. Reserved future ownership boundaries and FIR treatment

PACK-13 assigns no owner to the identity, eligibility, credential, voting or
tally/result-certification boundaries. The FIR entries those boundaries
carry are therefore **partially addressed at best**, and the remainder is
owned by the pack that establishes the owner.

| Reserved boundary                        | Owner established by | FIR entries whose remainder that pack owns                                |
| ---------------------------------------- | -------------------- | ------------------------------------------------------------------------- |
| future identity domain                   | **PACK-14**          | `FIR-INV-001` (residual: behavioural correlation), `FIR-ID-*` obligations |
| future eligibility domain                | **PACK-15**          | `FIR-INV-004`                                                             |
| future credential domain                 | **PACK-15**          | `FIR-INV-004`                                                             |
| future voting domain                     | **PACK-15/16**       | `FIR-INV-002`, `FIR-INV-003`, `FIR-INV-005`                               |
| future tally/result-certification domain | **PACK-15/16**       | `FIR-INV-005`                                                             |

`P13-OWN-012` binds each future owner to the PACK-13 data-plane contracts,
so the constraints in this matrix apply to them when they are established —
but PACK-13 cannot mark any of these entries fully addressed, because the
component that would satisfy them does not yet have an owner.

---

## 7. Summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 13    |
| partially addressed | 9     |
| deferred            | 2     |
| unchanged           | 6     |
| **implemented**     | **0** |

Zero is the only correct value in the last row for a specification-only
round, and the acceptance matrix makes it structurally testable: the
implementation round must be able to assert that this matrix contains no
`implemented` value.

---

## Implementation coverage — PACK-13 Implementation Candidate (`0.13.0`)

Added by the implementation round. `Reference coverage` says what the
candidate built against the obligation; `Remains open` says what it did
not, and why.

| FIR                                | Reference coverage in `services/data-plane-service`                                                                                                                                                                                  | Remains open                                                                                                                                                                                      |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIR-ROADMAP-003`                  | The whole package, plus `contracts/reason-codes/pack-13.yml` and the accepted ADR-069..078                                                                                                                                           | An external CI PASS; the production data plane itself. The entry moves to `scheduled`, not `implemented`                                                                                          |
| `FIR-INV-001`                      | `domain.GLOBAL_IDENTITY_KEYS`; `boundaries.reject_global_identifier_column`, `reject_cross_domain_identity_join`, `ScopedSubjectReference`; `idempotency.reject_identity_derived_key`; `migrations` gate; `projections.ProjectedRow` | The guards are name-based and structural. An opaque hash of a person identifier is not detectable by them, and behavioural correlation is closed by no pack                                       |
| `FIR-INV-002`                      | `domain.VOTING_MATERIAL_KEYS`; `boundaries.reject_ballot_linkage`, `reject_tally_projection`, `reject_voting_client_identifier`; the `migrations` unlinkability gate                                                                 | The voting architecture and its topology are **PACK-15/16's**, which must demonstrate isolation and unlinkability against their own threat model. PACK-13 supplies general-plane constraints only |
| `FIR-INV-003`                      | Unchanged. `boundaries.reject_voting_client_identifier` only                                                                                                                                                                         | **PACK-15/16**                                                                                                                                                                                    |
| `FIR-INV-004`                      | Unchanged. `domain.ReservedBoundary` records both boundaries as reserved with no schema                                                                                                                                              | **PACK-15** establishes both owners                                                                                                                                                               |
| `FIR-INV-005`                      | `boundaries.reject_tally_projection`; no tally type exists                                                                                                                                                                           | **PACK-15/16** owns tally semantics                                                                                                                                                               |
| `FIR-INV-006`                      | `contracts.reject_flag_bypassing_gate`; `privileged.BreakGlassContext`, which has no field that could disable an obligation                                                                                                          | Nothing structural; the remainder is that a production deployment must have no environment switch the code cannot see                                                                             |
| `FIR-INV-007`                      | `integration.ExportRoute` and `reject_raw_export_route`; `SearchProjectionState`                                                                                                                                                     | Export and DLP policy remain **PACK-12's**. The infrastructure-level egress control the requirement actually turns on is **deferred to production infrastructure**                                |
| `FIR-INV-010`                      | Unchanged and deliberately not reimplemented. `retention.GovernedArtifactEvidence` references PACK-11's bundles; the migration evidence-linkage gate refuses a break                                                                 | Implemented by **PACK-11**                                                                                                                                                                        |
| `FIR-INV-011`                      | `integration.CumulativeReleaseHistoryEntry` persistence contract; `projections` governance keeps no uncontrolled aggregate source                                                                                                    | The SDC rules are **PACK-12's**; the analytics engine is a later pack's                                                                                                                           |
| `FIR-INV-012`                      | Unchanged. No rendered surface is introduced                                                                                                                                                                                         | **FRONT-PACK**                                                                                                                                                                                    |
| `FIR-INV-013`                      | `domain.require_organization_scope`; scope as a required field on every scoped model; `projections.ProjectedRow`; the migration scope gate                                                                                           | A live catalog conformance report is **deferred to production infrastructure**                                                                                                                    |
| `FIR-INV-014`                      | `privileged.INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS`, `reject_incompatible_roles`, `require_domain_content_authority`                                                                                                                     | A superuser can read what the engine decrypts — **PACK-14/17**. A real role inventory is **deferred to production infrastructure**                                                                |
| `FIR-INV-015`                      | `domain.DATA_PLANE_IMPLEMENTATION_STATUS`; `administration.OperationalStatus`; the negation scan in `tests/test_boundaries.py`                                                                                                       | Nothing. The scan is the control, and it runs                                                                                                                                                     |
| `FIR-DATA-001`                     | `retention.RetentionBinding` binds every infrastructure persistent class to a record class and a schedule                                                                                                                            | The catalog and processing registry themselves remain **PACK-09's**                                                                                                                               |
| `FIR-DATA-002`                     | Unchanged. `idempotency.OperationClass.DEADLINE_JOB` exists so a deadline job is idempotent                                                                                                                                          | Owned by **PACK-09**                                                                                                                                                                              |
| `FIR-DATA-003`                     | `retention.LegalHoldObservation`, `DeletionDecision`; fail-closed on unknown hold state; `projections.DeletionPropagation`                                                                                                           | Hold semantics remain **PACK-09's**; PACK-13 observes and preserves                                                                                                                               |
| PACK-02 append-only audit          | `boundaries.AuditIngestionPort`, `AuditSubmission`, `ApplicationCredential`, `reject_direct_audit_write`; `storage.DataPlaneAuditEventStore` names PACK-02's port rather than redeclaring it                                         | A real per-role database grant inventory is **deferred to production infrastructure**                                                                                                             |
| PACK-09 retention and evidence     | `retention` module in full                                                                                                                                                                                                           | PACK-09 decides; PACK-13 binds and observes                                                                                                                                                       |
| PACK-11 evidence references        | `retention.GovernedArtifactEvidence`, `require_evidence_for`; evidence required on publication decisions, migration plans and verifications                                                                                          | PACK-11 owns the bundles                                                                                                                                                                          |
| PACK-12 privileged, search, export | `privileged` and `integration` modules in full                                                                                                                                                                                       | PACK-12 owns every policy question; PACK-13 supplies contracts                                                                                                                                    |

### Summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 13    |
| partially addressed | 9     |
| deferred            | 2     |
| unchanged           | 6     |
| **implemented**     | **0** |

Zero remains the only correct value in the last row, and
`AC-P13-155` makes it structurally testable:
`tests/repository/test_pack13_fir_matrix.py` asserts that no table cell in
this file carries `implemented` as a treatment value.

# PACK-13 — Specification + ADR Report

```text
PACK-13 SPECIFICATION + ADR CORRECTED
NOT IMPLEMENTED
NOT PASS
```

**Round type:** specification and ADR only. **No code changed. No test
changed. No CI changed. No version changed. No canon changed.**

|                    |                                                                     |
| ------------------ | ------------------------------------------------------------------- |
| Round              | PACK-13 — Production Data Plane & Contract Evolution                |
| Date               | 2026-07-29                                                          |
| Input baseline     | `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip` |
| Repository version | **unchanged at `0.12.0`**                                           |
| Canon version      | **unchanged at `0.8.0`**                                            |
| Register entry     | `FIR-ROADMAP-003` — remains `approved`, **not** advanced            |
| Documents produced | 22 (11 pack documents, 10 ADRs, this report)                        |

---

## 1. Input baseline

PACK-01 through PACK-12 at FINAL PASS. Twenty-one services whose every
storage adapter is in memory — deliberately, and stated as such throughout.
Architecture Domain Framework 0.8.2 CORRECTED, Target Frontend Architecture
0.8.2 CORRECTED, canon 0.8.0, ADR-001 through ADR-068, and the Master
Future Implementation Register.

The hard invariants and public contracts of PACK-09 (records governance),
PACK-10 (finance), PACK-11 (governed documents and evidence) and PACK-12
(privileged administration, search, export) are inherited unchanged. §2 of
the specification tabulates what each contributes and what PACK-13 may not
do to it.

## 2. What was created

### Pack documents (11)

| Document                                 | What it fixes                                                                                                   |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `PACK-13-SPECIFICATION.md`               | 35 sections; ~230 normative requirements across 29 prefixes                                                     |
| `PACK-13-ACCEPTANCE-MATRIX.md`           | **176 criteria, 168 PASS blockers**, in 25 groups                                                               |
| `PACK-13-THREAT-MODEL.md`                | **30 threats**, each with preventive/detective controls, evidence, residual risk and pack dependency            |
| `PACK-13-DATA-OWNERSHIP-MATRIX.md`       | Ownership for 25 data areas; the four admissible integration mechanisms; the closed cross-domain reference list |
| `PACK-13-SCHEMA-COMPATIBILITY-MATRIX.md` | 5 modes; 27 change classes; the 6 structurally invisible classes; per-format checker capability stated honestly |
| `PACK-13-MIGRATION-CONTROL-MATRIX.md`    | 6 migration classes; a 17-row gate matrix; failure handling; expand/contract step controls                      |
| `PACK-13-EVENT-DELIVERY-MATRIX.md`       | 14 delivery situations; ordering scopes per family; 10 idempotency scopes                                       |
| `PACK-13-EVENT-CATALOG.md`               | **37 events** in 4 families, on the existing envelope                                                           |
| `PACK-13-REASON-CODE-CATALOG.md`         | **88 codes** in 8 families plus 10 reused; no generic `DATA_ERROR` or `CONFLICT`                                |
| `PACK-13-FIR-COVERAGE-MATRIX.md`         | 30 entries; **zero marked implemented**                                                                         |
| `PACK-13-CANON-ASSESSMENT.md`            | Verdict with the reasoning, and the triggers that would reverse it                                              |

### ADRs (10)

ADR-069 through ADR-078 — listed in §4.

## 3. Gaps closed

| Gap before this round                                                | Closed by                         |
| -------------------------------------------------------------------- | --------------------------------- |
| No specified persistence architecture; every adapter in memory       | ADR-069, spec §4–§5               |
| No rule preventing cross-domain database access                      | ADR-070, ownership matrix         |
| No specified relationship between state change and event publication | ADR-071, `P13-TX-003`             |
| Delivery semantics unstated; "exactly-once" available to be assumed  | ADR-072, `P13-DEL-015`            |
| No registry of schemas, versions, owners or consumers                | ADR-073                           |
| No compatibility classification; no deprecation discipline           | ADR-074, compatibility matrix     |
| No migration discipline; no checksum, ordering or approval rules     | ADR-075, migration control matrix |
| Projections ungoverned; authorization widening possible              | ADR-076                           |
| Concurrency and idempotency unspecified beyond per-pack practice     | ADR-077                           |
| Retention and hold unenforced across derived stores                  | ADR-078                           |
| No path from reference implementation to production                  | spec §33                          |

## 4. ADRs accepted (all `proposed`)

| ADR         | Decision                                                                                                                                                                            |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ADR-069** | PostgreSQL-compatible relational data plane, domain-owned schemas, scope from the first migration, no global person table, no authoritative JSON dump                               |
| **ADR-070** | One owning domain per table; four admissible integration mechanisms; outbox co-located with its domain; no reserved tables for future domains                                       |
| **ADR-071** | Transactional outbox mandatory; stable event ID; published state and delivery evidence distinct; **transport metadata stays out of the envelope**                                   |
| **ADR-072** | At-least-once delivery; effectively-once consumer effect; exactly-once claimed nowhere; permanent business-fact guards where expiry is unacceptable                                 |
| **ADR-073** | Canonical schema registry; **canon governs over registry**; retired versions retained; fixtures mandatory; domain owns the schema                                                   |
| **ADR-074** | Five compatibility modes with `unknown` first-class; six structurally invisible classes always reviewed; upcasters invent no legal facts; unknown enums never default               |
| **ADR-075** | Immutable applied migrations; mandatory checksums that never auto-repair; class-based controls; five automated invariant gates; expand/contract; rollback tested or declared absent |
| **ADR-076** | Projections owned, declared, non-authoritative; never widen authorization; staleness visible; deletion propagates with evidence                                                     |
| **ADR-077** | Optimistic concurrency; last-write-wins forbidden for consequential records; approval refused on a changed version; scoped idempotency keys never derived from identity             |
| **ADR-078** | Retention applies to infrastructure; hold preserves and authorizes nothing; evidence uses PACK-11's mechanisms; the backup gap left open and visible                                |

## 5. Bounded contexts

Five, logical rather than deployable: Transactional Data Plane; Event
Transport; Canonical Schema Registry; Contract Evolution; Projection and
Read Models. None may become a general-purpose platform bypassing a domain
owner (`P13-CTX-001`).

## 6. FIR coverage

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 14    |
| partially addressed | 8     |
| deferred            | 2     |
| unchanged           | 6     |
| **implemented**     | **0** |

`FIR-ROADMAP-003` is **addressed** and stays `approved`. It must not move
past `scheduled` or `under_review` on the strength of this round.

Fully addressed: `FIR-INV-001`, `FIR-INV-006`, `FIR-INV-013`,
`FIR-INV-014`, `FIR-INV-015`. Partially addressed, with the remainder named
and owned: `FIR-INV-002`, `FIR-INV-004`, `FIR-INV-005`, `FIR-INV-007`,
`FIR-INV-011`, `FIR-DATA-001`, `FIR-DATA-003`. `FIR-INV-004` moved from
addressed to partially addressed in this correction round: both the
eligibility and credential boundaries are reserved future ownership, so the
separation binds the baseline reference implementations now and whatever
owners PACK-15 establishes later.

## 7. Canon assessment

```text
CANON AMENDMENT NOT REQUIRED
```

Every PACK-13 concept was tested against four questions: does it change the
domain model, the envelope, event naming, or a registered code's meaning?
All four answers are no. The registry records artifacts, not meaning, and
`P13-REG-002` makes the canon govern where they disagree. Transport
metadata deliberately stays **out** of the envelope (ADR-071) — that single
decision is what keeps this round canon-neutral. The canon file is not
modified, and no document proposes an edit to it.

The assessment also records the triggers that **would** require an
amendment, so a future round recognises them rather than rediscovering the
question.

## 8. Open implementation decisions

| ID            | Decision                                                                    | Why it is open                                                                                                          |
| ------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **OD-P13-01** | Database engine and deployment topology                                     | An architectural direction is fixed; the engine, version and topology are the implementation round's, under its own ADR |
| **OD-P13-02** | Schema-per-domain vs database-per-domain                                    | Both satisfy the isolation requirement; the trade-off is operational and belongs with the operator                      |
| **OD-P13-03** | Numeric coexistence and deprecation windows                                 | The specification fixes that they exist and are per-class; the values are policy                                        |
| **OD-P13-04** | Minimum observation period before a contract step                           | Same reasoning                                                                                                          |
| **OD-P13-05** | Broker technology and partitioning strategy                                 | Ordering scopes are fixed; the mechanism is not                                                                         |
| **OD-P13-06** | Retry counts, backoff curves, dead-letter thresholds                        | Operational tuning, not architecture                                                                                    |
| **OD-P13-07** | Idempotency and dedup retention windows per operation class                 | Depends on PACK-09 retention schedules not yet set                                                                      |
| **OD-P13-08** | Projection lag thresholds and staleness bands per consumer                  | Depends on which decisions turn out to be freshness-sensitive                                                           |
| **OD-P13-09** | Whether the schema registry is a service or a governed repository structure | Both satisfy the requirements; the choice affects operational surface                                                   |
| **OD-P13-10** | Migration tooling                                                           | Must satisfy immutability, checksums and deterministic ordering; the tool is free                                       |
| **OD-P13-11** | Backfill batch sizes and rate limits                                        | Depends on production data volumes, unknown here                                                                        |
| **OD-P13-12** | Whether outbox dispatch is polling or log-based                             | ADR-071 rejects CDC as the event contract; it does not forbid it as dispatch transport                                  |

**Numeric and configuration values not yet approved:** every window,
threshold, limit, batch size, retry count and retention period above. The
specification fixes that they exist, that they are versioned policy, and
that no hard invariant may be disabled by configuring one — never their
values.

## 9. Future tests the implementation round must write

Structural: catalog conformance against the ownership matrix; scope-column
presence; absence of cross-domain identity keys; absence of voting-shaped
tables, topics and reference types; migration gates for scope loss, global
identifiers and unlinkability.

Behavioural: atomic state-plus-outbox under injected failure; duplicate
delivery producing one effect; kill-and-resume backfill; double-run
backfill; conflict on stale expected version; approval refused on a changed
version; unknown enum refused rather than defaulted; upcaster determinism
over recorded historical payloads; rebuild-and-compare for every projection
declared rebuildable.

Scans: forbidden-phrase scan for "exactly-once", production-readiness and
legal-activation claims; telemetry content scan; backfill log scan.

## 10. Dependencies on later packs

| Pack           | What PACK-13 depends on it for                                                                                                                                  |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PACK-14**    | External IAM, authentication, MFA, HSM/PKI key custody. Reduces the residual risk in T-P13-17 (privileged operator reading content), which PACK-13 cannot close |
| **PACK-15/16** | The voting architecture and its isolated data plane. PACK-13 guarantees only that unlinkability is not defeated **from the data-plane side**                    |
| **PACK-17**    | Incident response, operational monitoring, backup and **restore testing**. The backup-retention gap in T-P13-15 and the egress risk in T-P13-18 are theirs      |
| **FRONT-PACK** | Workspace architecture for the ten administrative surfaces                                                                                                      |
| **PACK-09**    | Retention schedules and hold decisions, which PACK-13 observes and never makes                                                                                  |
| **PACK-12**    | Privileged grants for migrations and SQL; search and export policy, which PACK-13 supplies contracts for and never rewrites                                     |

## 11. Frontend boundary

Ten administrative surfaces only. **No universal admin console.** The
frontend is not a security boundary; no surface executes arbitrary SQL; no
surface bypasses a PACK-12 grant; no surface claims production
infrastructure is active. Accessibility obligations are preserved.

## 11a. Corrections applied in this round

Four substantive corrections. **No code, no test, no CI, no version, no
canon change, and no document added or removed.** Twelve files changed.

### 1. Future ownership boundaries are no longer presented as settled

The ownership matrix listed `account-service`, `identity-service`,
`eligibility-service`, `credential-service`, `voting-service` and
`tally-service` alongside genuinely settled owners, which read as though
PACK-13 had assigned production data-plane ownership for identity,
eligibility, credential, voting and tally. It had not, and it may not.

The matrix is now split into **§3.1 Existing implemented owners** — the
eighteen areas whose ownership PACK-13 does settle — and **§3.2 Reserved
future ownership boundaries**, using the required wording:

```text
future identity domain — owner to be established by PACK-14
future eligibility domain — owner to be established by PACK-15
future credential domain — owner to be established by PACK-15
future voting domain — owner to be established by PACK-15/16
future tally/result-certification domain — owner to be established by PACK-15/16
```

Five new rules (`P13-OWN-009`..`013`) fix that a reserved boundary is a
conceptual boundary and not an existing deployable service; that PACK-13
assigns no final service name; that PACK-13 creates no schema ownership on
behalf of a future PACK; that whatever owner is established must comply
with the PACK-13 data-plane contracts; and that final topology and
ownership are approved by the corresponding PACK.

Stated plainly in §3.2, because it would otherwise look like an
inconsistency: **several of these boundaries do have reference-
implementation services in the baseline, from PACK-02 and PACK-03. Their
existence does not settle production data-plane ownership**, and PACK-13
does not settle it either.

### 2. The audit-core write boundary no longer contradicts itself

The package asserted both "only the owner writes" and "every domain may
append to audit-core". Read together they licensed exactly what the first
forbids.

Resolved with the normative sentence, now in the specification
(`P13-DP-014a`), the ownership matrix (§3.3, `P13-OWN-014`) and ADR-070:

> All domains may submit typed audit records through the governed
> audit-ingestion contract; only `audit-core` persists authoritative audit
> records.

Both statements are true because they describe different acts: every domain
**submits**, exactly one domain **persists**. Fixed with it: no direct
`INSERT`/`UPDATE`/`DELETE` by a non-owner; submission through the ingestion
port/API or a versioned audit command or event; append-only describes
ingestion semantics _and_ authoritative storage; other domains'
application credentials carry no write grant on the audit schema; bulk
loading and emergency SQL are not ordinary integration paths; privileged
maintenance obeys PACK-12 and does not transfer ownership.

New threat **T-P13-02a** covers direct write by a non-owner. New reason
codes `DATAPLANE_AUDIT_DIRECT_WRITE_DENIED` and
`DATAPLANE_AUDIT_INGESTION_CONTRACT_REQUIRED`. And the acceptance criterion
the correction asked for explicitly:

> **AC-P13-156 — No non-owner domain credential can write directly to
> audit-core persistence.**

### 3. Voting topology is no longer decided by PACK-13

`P13-OWN-007` had fixed that the voting data plane is "physically separate"
and shares no connection pool identity and no broker topic. Those are
PACK-15/16 decisions, and taking them here would have settled a security
architecture from outside the pack that owns it, against a threat model not
yet written.

Specification §28 is now split. **§28.1 — what PACK-13 fixes:** ballot
content and voting secrets never in the general plane; no identity-to-ballot
join in any general schema; no identity-linked ballot payload on the general
event bus; no global member or account identifier as a Voting Client
identifier. **§28.2 — what PACK-13 does not prescribe:** broker topics,
separate or shared broker deployment, connection-pool topology, service
names, credential topology, transport provider.

`P13-VOTE-009` obliges the future voting architecture to demonstrate
isolation and unlinkability against **its own** threat model. `P13-VOTE-010`
keeps the retained formulation — _separate infrastructure is the preferred
reference direction where required by the PACK-15/16 threat model_ — as a
direction, not a decision already taken.

### 4. Content digest and schema-version identity are separated

`P13-REG-005` had said that two byte-different but semantically identical
documents must not produce two schema versions. That was wrong twice: it
made the registry claim a **semantic-equivalence proof** no
canonicalization can perform, and it conflated a content fact with a
governance fact — silently merging a deliberate governed re-issue into the
existing version and erasing the decision behind it.

Replaced with:

> Content that is identical after the registry's format-specific
> canonicalization produces the same content digest. Digest equality does
> not itself define schema-version identity.

The registry model now carries `content_digest`, `schema_version_id`,
`publication_decision_id`, `effective_at`, `deprecated_at`,
`supersession_reference` and `governance_justification` as separate fields.
Seven sub-requirements (`P13-REG-005a`..`005g`) fix that canonicalization
removes only enumerated serialization differences; that the registry claims
no universal semantic-equivalence proof; that accidental republication is
blocked or reason-coded; that identical content may be bound to a new
governed version only with explicit justification; and that historical
version identity is never rewritten because of digest equality.

New reason codes: `SCHEMA_DUPLICATE_CONTENT`,
`SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`,
`SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED`,
`SCHEMA_VERSION_IDENTITY_IMMUTABLE`,
`SCHEMA_GOVERNANCE_JUSTIFICATION_MISSING`. `SCHEMA_ALREADY_PUBLISHED` was
removed as superseded by that taxonomy. New threat **T-P13-27a**. Seven new
acceptance criteria (AC-P13-170..176), and AC-P13-061 rewritten.

---

## 12. Consistency checks performed

All 29 checks passed, including the four this correction round added —
future domains are not presented as existing services; `audit-core` retains
exclusive persistence ownership; voting topology does not pre-empt
PACK-15/16; canonicalization claims no semantic equivalence and digest is
separated from version identity — and: no code; no version change; canon
absent from this package; PACK-09, PACK-11 and PACK-12 not duplicated or rewritten;
PACK-14, PACK-15/16 and PACK-17 not absorbed; no global user ID; Bund/Land/
Kreis isolation and voting unlinkability preserved; the registry does not
become a new canon; events use the existing envelope; no universal
exactly-once claim; no provider lock-in claim; no legal-compliance,
production-readiness or PASS claim; the FIR matrix contains no `implemented`
value.

Every occurrence of "exactly-once" in this package is a **prohibition**.
Likewise, the only surviving occurrences of "physically separate" and
"byte-different" are in §11a and ADR-073, where they quote the **superseded**
wording in order to record what was corrected.

One reference resolves outside this package by design:
`docs/canonical/TZ-00-domain-event-canon.md`, cited by the canon assessment.
It is a repository file, deliberately **not** included here — this is a
documentation-only package and the canon is not modified by this round.

## 13. Confirmations

```text
NO CODE CHANGED
NO TESTS CHANGED
NO CI CHANGED
NO VERSIONS CHANGED
NO CANON CHANGED
NOT IMPLEMENTED
NOT PASS
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This package contains **only Markdown documentation**. It adds no file to
`services/`, `packages/`, `contracts/`, `scripts/`, `tests/`, `frontend/`
or `.github/`, and modifies no existing repository file.

## 14. SHA-256 of every file

| File                                                                  | SHA-256                                                                                          |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `docs/adr/ADR-069-PRODUCTION-RELATIONAL-DATA-PLANE.md`                | `0b8720f0353b0b8edf446d81a06bccb7204f58febe5594872411a2d60f42d9cb`                               |
| `docs/adr/ADR-070-DOMAIN-DATA-OWNERSHIP.md`                           | `d2b75bc5b2eca65f61b9c9d8864c68f60d4bb9c77388ba29b3ab08f30e404c72`                               |
| `docs/adr/ADR-071-TRANSACTIONAL-OUTBOX.md`                            | `caecad636d1b36c7f58ac114f79ebd7b99f6d68efaa223a2cf02a4f6c27e1d4e`                               |
| `docs/adr/ADR-072-AT-LEAST-ONCE-DELIVERY-AND-IDEMPOTENT-CONSUMERS.md` | `30174caa71135330a66cfdbec17ef0cbf268b0f12be74d8afc14dc0c8d2ed9c1`                               |
| `docs/adr/ADR-073-CANONICAL-SCHEMA-REGISTRY.md`                       | `80abb5026cc5dc2e2fcbedc03cfa95f866678fe6788f8c3d9558fa32bc3e51b2`                               |
| `docs/adr/ADR-074-API-AND-EVENT-CONTRACT-EVOLUTION.md`                | `5379be64977e2496e9bdf0e0fd2ded6041dc0ca73d830f1466271c82a5564cba`                               |
| `docs/adr/ADR-075-DATABASE-MIGRATION-DISCIPLINE.md`                   | `701740f66fccabace1b88b6c222547084dd0e6b765de22eaeb9a31089bfdd7ab`                               |
| `docs/adr/ADR-076-PROJECTION-AND-READ-MODEL-GOVERNANCE.md`            | `cef2a7e39a14586e4e770abd9b4fb9cf642a0e58d3a5c13850c425570060150c`                               |
| `docs/adr/ADR-077-CONCURRENCY-AND-IDEMPOTENCY.md`                     | `0d512ddf78068782629b752c0355852cb50ccba9daefabcd06d6b9cb8bfe3762`                               |
| `docs/adr/ADR-078-DATA-PLANE-RETENTION-LEGAL-HOLD-AND-EVIDENCE.md`    | `d3325515eb3f52d0da50776e10efc8c30b0bfdd697a7ed4fe402571143bedf4c`                               |
| `docs/handover/PACK-13-SPEC-ADR-REPORT.md`                            | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |
| `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md`                     | `7131cdd6f002d2b622b1684911e1818ff16a1be1af34aa684596a8cc485eb9ce`                               |
| `docs/packs/PACK-13/PACK-13-CANON-ASSESSMENT.md`                      | `3e72cfa1966d6ab807bc6aae225f16ad9710c8e0379f47da7570395006a553a3`                               |
| `docs/packs/PACK-13/PACK-13-DATA-OWNERSHIP-MATRIX.md`                 | `decd441b2189c1896ed3ceb8f12b8ad15bf6c9bfc34b21ef50ee36c0fd35485f`                               |
| `docs/packs/PACK-13/PACK-13-EVENT-CATALOG.md`                         | `7e7038b402c9ce8db1a774ce8a29117e0afe51c174d494e8f77d51369ba7bfc3`                               |
| `docs/packs/PACK-13/PACK-13-EVENT-DELIVERY-MATRIX.md`                 | `44e3e1b429a4a3bff21f2e5afde3f1120514f8aecd25f11e8cd450753ae59bcd`                               |
| `docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md`                   | `be20636d642223cc8ded28d839e87ef6b7b8aa77286bb339234e0cf27dffa20e`                               |
| `docs/packs/PACK-13/PACK-13-MIGRATION-CONTROL-MATRIX.md`              | `09d3a716171dbfde49531c1274348291d1e4a9755668da8613ff3b18a1383fa3`                               |
| `docs/packs/PACK-13/PACK-13-REASON-CODE-CATALOG.md`                   | `e6e85712de7ab7999ac655dd9bdc8ebb35c32ff332f3128b5e1edd56bba47242`                               |
| `docs/packs/PACK-13/PACK-13-SCHEMA-COMPATIBILITY-MATRIX.md`           | `29bcfb215b35228bc30b0130779799dae4a2190b9e1092dfa2081247b5162cb1`                               |
| `docs/packs/PACK-13/PACK-13-SPECIFICATION.md`                         | `804f707c01b74a153d9331e3ff94ef3fce0643a1fba5c68a83971851152e2777`                               |
| `docs/packs/PACK-13/PACK-13-THREAT-MODEL.md`                          | `a6e1651a0b941fe1a4fe3b8ebd8bb21984035ecc02b59479193222ae029d8166`                               |

## 15. SHA-256 of the archive

Reported in the delivery message accompanying
`EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_SPEC_ADR.zip`.
A file cannot contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_SPEC_ADR.zip
```

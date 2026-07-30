# EPD² Master Future Implementation Register

**Status:** Living master register  
**Purpose:** Single authoritative repository document for all captured future requirements, proposed normative profiles, roadmap items, hard invariants, frontend obligations, institutional roles, trust boundaries and implementation conditions that are not yet fully completed.

## Canonical repository location

```text
docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md
```

This file replaces separate idea notes, ad-hoc reminders, standalone future-feature lists and duplicate roadmap addenda.

---

# 1. Governance of this register

## 1.1 Entry lifecycle

Allowed statuses:

- `captured`
- `proposed_normative`
- `under_review`
- `approved`
- `scheduled`
- `implemented`
- `deferred`
- `legally_blocked`
- `production_blocked`
- `rejected`
- `superseded`

## 1.2 Change discipline

Every requirement or idea must:

- have a stable identifier;
- preserve its history;
- never be silently deleted;
- state domain ownership;
- state target package or frontend placement where known;
- state dependencies;
- state acceptance criteria;
- reference the implementing PACK, ADR, audit or handover report once implemented.

## 1.3 Package discipline

Every future PACK task must list:

- FIR IDs implemented;
- FIR IDs deferred;
- FIR IDs intentionally left unchanged;
- any new FIR IDs created by implementation discovery.

## 1.4 Baseline discipline

This file must be included in every cumulative FINAL PASS archive, at
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`. The PACK-11
round added that path to `scripts/check_repository.py`'s required paths, so
an archive that drops it now fails a check rather than passing quietly.

## 1.5 Round record — PACK-11 (2026-07-28)

Per section 1.3, every PACK task lists what it did to this register.

**FIR IDs implemented:** `FIR-ROADMAP-001`, `FIR-INV-010` — both to
`implemented in reference form`, both with evidence paths and named
remaining work.

**FIR IDs given a foundation but explicitly NOT implemented:**
`FIR-DEC-001`, `FIR-DEC-002`, `FIR-CAND-001`, `FIR-COMM-001`,
`FIR-PROG-002`, `FIR-INIT-021`, `FIR-PAY-003`, `FIR-DATA-003`. Each carries
"**PACK-11 foundation provided — this entry is NOT implemented.**", what
PACK-11 supplies, what it deliberately does not, and what remains.

**FIR IDs intentionally left unchanged:** every other entry. In particular
`FIR-AI-001` and `FIR-AI-002` are untouched — PACK-11 exposes
`Provenance.analysis_provenance_reference` as a hook and deliberately does
not restate an AI provenance contract, because a restated contract can
disagree with the original. All `FIR-FIN-*` and PACK-10 entries are
untouched, and PACK-09's and PACK-10's placeholder reference types were
deliberately not rewritten (see OD-21).

**New FIR IDs created by implementation discovery:** none. The two
limitations this round found — `FIR-INV-010` being satisfiable only as
tamper evidence without an external anchor, and PACK-09's hold state being
read-through rather than cached — are the known boundary of existing
requirements, not new ones, and are recorded as **OD-20** and limitation 6
in `docs/handover/PACK-11-KNOWN-LIMITATIONS.md`.

**Register updates only.** No entry was deleted, no identifier reused, and
no status downgraded.

## 1.6 Round record — PACK-12 (2026-07-29)

Per section 1.3, every PACK task lists what it did to this register.

**FIR IDs implemented:** none. `FIR-ROADMAP-002` moves from `approved` to
`scheduled` and no further. PACK-12 is an **implementation candidate that
has not passed external CI**, and a status of `implemented` claimed on the
strength of a locally-run pipeline would be a claim the evidence does not
support.

**FIR IDs given a foundation but explicitly NOT implemented:**
`FIR-SEARCH-001`, `FIR-SEARCH-002`, `FIR-SEARCH-003`, `FIR-METRIC-002`,
`FIR-ID-002`, `FIR-COMM-004`, `FIR-SEC-001`, `FIR-SEC-003`,
`FIR-ROLE-001`, `FIR-ROLE-003`, `FIR-DATA-001`, `FIR-DATA-003`,
`FIR-FRONT-001`, `FIR-FRONT-002`, `FIR-FRONT-003`, `FIR-INV-011`. Each
carries "**PACK-12 foundation provided — this entry is NOT implemented.**"
where PACK-12 touches it, together with what PACK-12 supplies, what it
deliberately does not, and what remains.

**FIR IDs intentionally left unchanged:** every other entry. In
particular `FIR-INV-002`, `FIR-INV-003` and `FIR-INV-005` are untouched —
PACK-12 establishes the _structural absence_ of any voting reference type
and adds no voting semantics, because a restated voting contract can
disagree with the original. `FIR-INV-010` is untouched: PACK-12 reuses
PACK-11's evidence bundles rather than reimplementing them. All
`FIR-UX-*` and `FIR-SUPPORT-*` entries added by section 24 this round are
untouched by the implementation.

**New FIR IDs created by implementation discovery:** none. Two facts this
round established are the known boundary of existing requirements rather
than new ones, and are recorded in
`docs/handover/PACK-12-KNOWN-LIMITATIONS.md`: session evidence is tamper
_evidence_ without an external anchor (the same boundary `OD-20` records
for PACK-11), and the cumulative-release model is bounded by a policy
window rather than being an all-releases-ever model (`OD-P12-08`).

**Register updates this round.** Sections 24 and 25 were merged in from
the user-supplied updated register, adding thirteen new entries
(`FIR-UX-001`, `FIR-UX-002`, `FIR-ID-001`, `FIR-ID-002`, `FIR-COMM-004`,
`FIR-SEARCH-001`..`003`, `FIR-SUPPORT-001`..`003`, `FIR-METRIC-001`,
`FIR-METRIC-002`). The merge took **this repository file as the base** and
appended only the genuinely new sections: the supplied file was derived
from a pre-PACK-11 baseline, so adopting it wholesale would have silently
reverted the PACK-11 round record, the PACK-11 status changes and the
current baseline pointer. No entry was deleted, no identifier reused, no
status downgraded, and no second register was created.

## 1.7 Round record — PACK-12 FINAL PASS (2026-07-29)

**PACK-12 EXTERNAL CI PASS. PACK-12 FINAL PASS ARCHIVE PREPARED.**
`REPOSITORY_VERSION` `0.12.0`; `CANON_VERSION` `0.8.0`.
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

A packaging round, not an implementation round. No service module, test,
reason code, ADR, contract or frontend file was changed.

**FIR IDs implemented:** `FIR-ROADMAP-002`, moved from `scheduled` to
`implemented` on the strength of an external GitHub Actions run that
passed every stage — 728/728 repository paths, no forbidden paths, Ruff
format, Prettier, Ruff lint, mypy and TypeScript typecheck all PASS,
4062 Python tests passed with 4 skipped, 108 browser tests passed, and
accessibility and visual checks PASS. Evidence:
`docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md` and
`docs/handover/PACK-12-FINAL-PASS-REPORT.md`.

**FIR IDs whose foundation-only status is unchanged by this round:** all
sixteen recorded in §1.6. A green pipeline does not implement a
requirement that the round never set out to implement, and none of them
is promoted here.

**FIR IDs intentionally left unchanged:** every other entry, including
every `FIR-UX-*`, `FIR-ID-*`, `FIR-COMM-*`, `FIR-SEARCH-*`,
`FIR-SUPPORT-*` and `FIR-METRIC-*` entry added by sections 24 and 25.
Those remain **future requirements**: PACK-12 supplies enforcement
foundations for search and small-cohort disclosure control, and
implements no cabinet, identity, communication-persona, support or
metrics surface.

**New FIR IDs created:** none.

**`AC-P12-090` remains deferred** and is not closed by this round.

**Register updates only.** No entry was deleted, no identifier reused, no
status downgraded, and no second register was created. The candidate
round records in §1.6 are preserved unmodified: the round genuinely was a
candidate at the time, and rewriting that history to read as though it
had always been FINAL PASS would destroy the audit trail this register
exists to keep.

## 1.8 Round record — PACK-13 Implementation Candidate (2026-07-30)

Per section 1.3, every PACK task lists what it did to this register.

**Baseline:** PACK-12 FINAL PASS (`0.12.0`). **Repository version after
this round:** `0.13.0`. **Canon version:** unchanged at `0.8.0`.

**FIR IDs implemented:** none. `FIR-ROADMAP-003` moves from `approved` to
`scheduled` and no further. PACK-13 is an **implementation candidate that
has not passed external CI**, and `implemented` claimed on the strength of
a locally-run, partially-runnable pipeline would be a claim the evidence
does not support. The same reasoning PACK-12's round record recorded
applies unchanged.

**FIR IDs given a foundation but explicitly NOT implemented:**
`FIR-INV-001`, `FIR-INV-006`, `FIR-INV-013`, `FIR-INV-014`, `FIR-INV-015`,
`FIR-DATA-001`, `FIR-DATA-003`, `FIR-INV-007`, `FIR-INV-011`. Each is
addressed in **reference form** by `services/data-plane-service` — the
contracts, the gates and the refusals are real and tested — and none is
closed, because the production data plane those invariants would finally be
enforced in is not deployed.

**FIR IDs intentionally left unchanged:** every other entry. In particular
`FIR-INV-002`, `FIR-INV-003`, `FIR-INV-004` and `FIR-INV-005` are
untouched. PACK-13 establishes the _structural absence_ of ballot,
credential and tally material in the general data plane and prescribes no
broker topic, broker deployment arrangement, connection-pool topology,
service name, credential topology or transport provider for the voting
domain — those are PACK-15/16's, taken with that pack's own threat model
(`P13-VOTE-008`). Deciding them here would be settling a security
architecture from outside the pack that owns it.

**New FIR IDs created by implementation discovery:** none. The limitations
this round found are the known boundary of existing requirements rather
than new ones, and are recorded in
`docs/handover/PACK-13-KNOWN-LIMITATIONS.md`.

**Documentation correction (2026-07-30), after the first candidate
archive.** One approved requirement was found to be missing from this
register: the public presentation of the adopted programme and its
projects. It had been approved before the candidate was built but had
never been written here, so the round that was told not to delete it was
working from a baseline that did not contain it. It is now recorded as
**`FIR-PROG-003` — Public Presentation of Adopted Programme and Projects**
in section 17, status `approved`, as a **future frontend obligation**.

The correction is documentation-only. No code, test, CI configuration,
ADR, PACK-13 architecture decision, repository version or canon version
changed, and `FIR-PROG-003` is **not** a PACK-13 implementation item — it
is recorded here, and it stays outside this round's scope.

**Production infrastructure items remain future.** No production
PostgreSQL, no cloud database, no real broker, no external schema-registry
product, no production search engine, no production IAM and no
multi-region topology is deployed or claimed by this round. The identity
(PACK-14), eligibility/credential/voting/tally (PACK-15/16) and backup
recovery (PACK-17) items remain future in exactly the state they were.

**Register updates only.** No entry was deleted, no identifier reused, no
status downgraded, and no second register was created.

---

# 2. Current confirmed baseline

## FIR-BASE-001 — Current repository baseline

**Status:** implemented  
**Last updated:** PACK-13 Implementation Candidate round (2026-07-30)

**Current authoritative cumulative baseline (PASS):**

```text
EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip
```

**Current working head — a CANDIDATE, not a baseline:**

```text
EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_CANDIDATE.zip
```

Repository version `0.13.0`; canon version `0.8.0` (unchanged — this
round amends no canon). **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY
ACTIVATED.** The PASS baseline above is unchanged and remains the
authoritative one until an external GitHub Actions run passes over the
candidate. Added by the candidate:

- `services/data-plane-service`: 22 source modules, 20 test modules
- Data-plane implementation status: `reference_implementation`
- `contracts/reason-codes/pack-13.yml` (125 entries: 88 from the PACK-13
  reason-code catalog, 37 `*_RECORDED` audit classifications)
- ADR-069 through ADR-078, accepted
- still no production database, no production event bus, no external
  schema-registry product, no production search engine, no production
  IAM, no backup or restore capability

Repository version `0.12.0`; canon version `0.8.0`. Verified by an
external GitHub Actions run — see
`docs/handover/PACK-12-FINAL-PASS-REPORT.md` and
`docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`.
**Not production ready. Not legally activated.**

**Previous PASS baseline, superseded by the line above:**

```text
EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip
```

**Earlier PASS baseline:**

```text
EPD2_PACK-10_PARTY_FINANCE_0.10.0_FINAL_PASS.zip
```

Confirmed at the previous PASS baseline:

- Repository version: `0.10.0`
- Canon version: `0.8.0`
- PACK-01 through PACK-10: PASS
- FRONT-00 Foundation: PASS
- FRONT-01 Public Website: PASS
- Finance implementation status: `reference_implementation`
- 45 committed visual snapshots
- no production DB
- no production event bus
- no banking/payment-provider integration
- no operational finance UI

Added by PACK-11, now confirmed at the current PASS baseline by an
external GitHub Actions run
(`docs/handover/PACK-11-GOVERNED-DOCUMENTS-EVIDENCE-0.11.0-FINAL-PASS-REPORT.md`,
`docs/handover/PACK-11-EXTERNAL-CI-VERIFICATION.log`):

- Repository version: `0.11.0`
- Canon version: `0.8.0` (unchanged — this round amends no canon)
- `services/document-service`: 13 modules, 358 tests
- Document/evidence implementation status: `reference_implementation`
- `contracts/reason-codes/pack-11.yml` (71 entries)
- proposed ADR-055 through ADR-060
- this register, now at its canonical repository path
- still no production DB, no production event bus, no external anchor for
  the document version-chain head, no signature verification, no
  document/evidence UI

---

# 3. Master roadmap

---

## FIR-ROADMAP-001 — PACK-11 Governed Documents & Evidence

**Status:** implemented in reference form  
**Target version:** `0.11.0` — delivered by PACK-11, FINAL PASS  
**Implementing round:** PACK-11 implementation round (2026-07-28)

Scope, with delivery state per item:

| Scope item                               | State                    | Evidence                                                                                                                                                 |
| ---------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| governed documents                       | implemented              | `document-service/documents.py` (`GovernedDocument`)                                                                                                     |
| document lifecycle                       | implemented              | `documents.py` (`DocumentState`), `versions.py` (`VersionState`, `_ALLOWED_VERSION_TRANSITIONS`)                                                         |
| immutable versions                       | implemented              | `versions.py`, `storage.py` (`append`, `record_state_change`)                                                                                            |
| typed evidence references                | implemented              | `references.py` (7 outward, 6 inward types)                                                                                                              |
| cryptographically linked version history | implemented              | `versions.py` (`compute_version_hash`, `verify_version_chain`), ADR-057                                                                                  |
| access and publication profiles          | implemented              | `domain.AccessProfile`, `authorization.assert_access_permitted`, `documents.PublicationAudience`, `documents.PublicationAuthorization`                   |
| correction and supersession              | implemented              | `versions.DocumentVersion.corrects_version_number`, `documents.SupersessionRecord`, `documents.RevocationRecord`                                         |
| retention integration                    | implemented as a binding | `domain.RetentionBinding`, `domain.LegalHoldBinding`, `documents.assert_disposition_authorized`. PACK-09 remains owner of the schedule and the decision. |
| evidence integrity                       | implemented              | `evidence.py` (custody chain verification, sealed bundles), `application.verify_document_integrity`                                                      |

**Evidence paths:**

- `services/document-service/` (13 source modules, 13 test modules, 358 tests)
- `contracts/reason-codes/pack-11.yml`
- `contracts/schemas/{governed-document,document-version,evidence-bundle,publication-rendition}.schema.json`
- `docs/adr/ADR-055` … `ADR-060`
- `docs/packs/PACK-11-{SPECIFICATION,IMPLEMENTATION,FIR-TRACEABILITY,ACCEPTANCE-MATRIX,CROSS-PACK-BOUNDARIES,THREAT-MODEL,OPEN-DECISIONS}.md`
- `docs/architecture/document-service.md`, `docs/architecture/document-version-integrity.md`
- `docs/contracts/document-command-query-contracts.md`
- `docs/handover/PACK-11-IMPLEMENTATION-REPORT.md`, `docs/handover/PACK-11-KNOWN-LIMITATIONS.md`

**Remaining work before this entry may be marked `implemented` outright:**

1. `make verify` green on a networked CI runner (`pytest`, `ruff`, `mypy`,
   `uv lock`, `npm`) — not executable in the build sandbox;
2. production persistence and the event bus (PACK-13);
3. an external anchor or countersignature for `head_version_hash` (OD-20)
   — without it, `FIR-INV-010` is satisfied as tamper _evidence_ only;
4. a PACK-11 PASS round.

## FIR-ROADMAP-002 — PACK-12 Privileged Admin, Search & Data Export Security

**Status:** implemented in reference form  
**Target version:** `0.12.0` — delivered by PACK-12, FINAL PASS  
**Implementing round:** PACK-12 implementation round (2026-07-29),
candidate → two CI corrections → FINAL PASS

**External GitHub Actions passed every stage:** 728/728 repository paths,
no forbidden paths, Ruff format, Prettier, Ruff lint, mypy and TypeScript
typecheck all PASS, 4062 Python tests passed with 4 skipped, 108 browser
tests passed, accessibility and visual checks PASS.

**`implemented in reference form`, not `implemented` outright**, and the
distinction is load-bearing. The governed workflows, the separation model
and the refusal surface are real and externally verified. The production
data plane is not: every storage adapter is in-memory, there is no
external IAM, no MFA, no HSM/PKI, no production search engine, no real
DLP provider, no real notification transport, and no administrative
frontend. Those belong to PACK-13, PACK-14, PACK-17 and FRONT-PACK, and
are listed as remaining work below.

**Not production ready. Not legally activated.**

Scope, with delivery state per item:

| Scope item                               | State                    | Evidence                                                                                                           |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| privileged access                        | reference implementation | `privileged-access-service/access.py` (`PrivilegedAccessGrant`), `application.py` (request → approve → activate)   |
| JIT access                               | reference implementation | `EffectiveWindow` has no unbounded option; `policy.MAX_ALLOWED_GRANT_DURATION`; no `renew` method exists           |
| break-glass                              | reference implementation | `breakglass.py` — dual control, notification obligation, escalation on failure, independent review                 |
| Security Admin / System Admin separation | reference implementation | `roles.PRESERVED_INSTITUTIONAL_PAIRS` + 14 added pairs; re-checked at the act inside `application._guard`          |
| controlled search                        | reference implementation | `search.py` — two modes only, purpose admission, result-time source re-resolution, suppression bands, cache keying |
| data export control                      | reference implementation | `export.py` — five distinct permissions, closed recipient taxonomy, field selection before generation              |
| DLP guardrails                           | reference implementation | `dlp.py` — 18 controls, fail-closed subset, volume/frequency/repetition rules, transforms                          |
| reason-coded privileged actions          | implemented              | `contracts/reason-codes/pack-12.yml`; no free-text refusal anywhere in the service                                 |
| out-of-band notification for break-glass | contract only            | `breakglass.NotificationPort` is the seam; the transport itself is PACK-17's                                       |

**Evidence paths:**

- `services/privileged-access-service/` (17 source modules, 16 test modules, 327 tests)
- `contracts/reason-codes/pack-12.yml`
- `docs/adr/ADR-061` … `ADR-068`
- `docs/packs/PACK-12/` (nine specification documents)
- `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md`,
  `docs/handover/PACK-12-KNOWN-LIMITATIONS.md`
- `docs/handover/PACK-12-FINAL-PASS-REPORT.md`,
  `docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`
- `docs/handover/PACK-12-SPEC-ADR-REPORT.md`

**Remaining work before this entry could ever be marked `implemented`
outright:**

1. production persistence, the event bus and a production search index
   (PACK-13);
2. an external IAM/IdP, MFA and HSM/PKI (PACK-14);
3. real out-of-band notification delivery and the incident-response
   platform (PACK-17);
4. a production DLP provider performing real content inspection;
5. the twelve administrative frontend surfaces (FRONT-PACK);
6. `AC-P12-090`, which remains **deferred** and is not closed by this
   round.

## FIR-ROADMAP-003 — PACK-13 Production Data Plane & Contract Evolution

**Status:** scheduled  
**Target version:** `0.13.0`  
**Repository version carrying the candidate:** `0.13.0`

Scope:

- production database;
- event bus;
- canonical schema registry;
- API evolution;
- event evolution;
- idempotency;
- compatibility policy;
- migration discipline;
- contract versioning.

**PACK-13 specification and ADR round: ACCEPTED.** `PACK-13-SPECIFICATION.md`
and ADR-069 through ADR-078 were accepted as the normative basis. That
round set no version and implemented nothing.

**PACK-13 implementation round: CANDIDATE. This entry is NOT
implemented.** `services/data-plane-service` implements the specification
in **reference form**: the transactional persistence contracts, the
canonical schema registry, the deterministic compatibility checker, the
API and event contract-evolution model, the migration framework and its
five automated gates, the backfill runner, the transactional outbox, the
at-least-once delivery semantics with effectively-once consumer effect,
projection governance, the search and export persistence contracts, the
retention and legal-hold bindings, the PACK-12 privileged gates and the
structural boundary guards — twenty-two source modules and twenty test
modules, with `contracts/reason-codes/pack-13.yml` carrying 125 entries.

**Why the status is `scheduled` and not `implemented`:**

1. this round produced an **implementation candidate**, not a PASS, and
   the external GitHub Actions pipeline has not run against it;
2. every storage adapter is **in memory**. No production PostgreSQL,
   cloud database, real broker, external schema-registry product,
   production search engine or production IAM is deployed. The
   requirements a production data plane must satisfy are implemented as
   contracts and refusals, which is a different and lesser claim than
   satisfying them in production;
3. the criteria whose evidence is a database grant inventory, a live
   catalog snapshot or an egress-control review are recorded as
   `deferred to production infrastructure` in the acceptance matrix's
   implementation-status appendix, not as met.

**Evidence:**

- `services/data-plane-service/` (source and tests);
- `contracts/reason-codes/pack-13.yml`;
- `docs/adr/ADR-069-*` through `docs/adr/ADR-078-*` (accepted);
- `docs/packs/PACK-13/` (specification and matrices, including the
  acceptance matrix's implementation-status appendix);
- `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`;
- `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`;
- `docs/handover/PACK-13-SPEC-ADR-REPORT.md` (the specification round's
  own report, retained unchanged).

**Remaining work before this entry could ever be marked `implemented`
outright:**

1. an external GitHub Actions PASS over this candidate;
2. a production PostgreSQL-compatible deployment with domain-owned
   schemas, per-domain grants and the immutable-history tables enforced at
   the privilege level;
3. a production event broker, and the dispatcher and consumer adapters
   that talk to it;
4. a production schema-registry deployment and a real search index;
5. domain-by-domain adapter migration behind the unchanged ports
   (`P13-PATH-004`), each with its own acceptance evidence;
6. backup and restore capability, which is **PACK-17's** and which
   `P13-BAK-011` forbids claiming without a restore test.

## FIR-ROADMAP-004 — PACK-14 Identity/Auth & External Gateway Security

**Status:** approved  
**Target version:** `0.14.0`

Scope:

- identity and authentication;
- external trust providers;
- gateway hardening;
- scoped sessions;
- no global user ID;
- external identity minimization;
- eID/KYC integration boundary.

## FIR-ROADMAP-005 — PACK-15 Voting Trust Boundary & Unlinkability Threat Model

**Status:** approved  
**Target version:** `0.15.0`

Scope:

- voting threat model;
- Voting Client Isolation Profile;
- eligibility / credential separation;
- unlinkability;
- origin isolation;
- no shared identity session;
- no shared analytics or telemetry;
- no persistent member identifier in Voting Client.

## FIR-ROADMAP-006 — PACK-16 Verifiable Voting Implementation

**Status:** approved  
**Target version:** `0.16.0`

Scope:

- verifiable voting;
- audited cryptographic protocol integration;
- ballot casting;
- vote verification;
- tally controls;
- no intermediate tally;
- eligibility without identity-vote linkage.

## FIR-ROADMAP-007 — PACK-17 Independent Verification, Resilience & Incident Readiness

**Status:** approved  
**Target version:** `0.17.0`

Scope:

- independent verification;
- security incident response;
- breach response;
- backup verification;
- recovery testing;
- resilience;
- operational readiness;
- external audit readiness.

## FIR-ROADMAP-008 — PACK-18 User Apps, Communication & AI Accountability Addendum

**Status:** approved  
**Target version:** `0.18.0`

Scope:

- user apps;
- member-facing communication;
- AI accountability;
- communication identity minimization;
- notifications;
- human review;
- AI traceability;
- accessibility.

## FIR-ROADMAP-009 — Later roadmap domains

**Status:** captured

Includes:

- Open Representative Desk;
- Emergency Governance & Crisis Override;
- Constitutional & Ethics Oversight;
- Delegation Reputation;
- Program Formation Lifecycle;
- Citizen Office Routing;
- Lobbying & Meeting Disclosure;
- parliamentary interface;
- public accountability;
- representative progress obligations.

---

# 4. Global hard invariants

## FIR-INV-001 — No global user ID

**Status:** approved

No universal identifier may correlate a person across all domains.

## FIR-INV-002 — Identity / ballot unlinkability

**Status:** approved

Identity verification and ballot handling must remain separated.

## FIR-INV-003 — Voting Client isolation

**Status:** approved

Voting Client must have:

- separate origin;
- no shared cookies;
- no shared localStorage;
- no shared IndexedDB;
- no shared identity session;
- no analytics;
- no fingerprinting;
- no shared telemetry;
- one-time purpose-scoped handoff artifact;
- no persistent member identifier.

## FIR-INV-004 — Eligibility / Credential separation

**Status:** approved

Eligibility authority and credential issuance authority must be separated.

## FIR-INV-005 — No intermediate tally

**Status:** approved

No intermediate tally or partial distribution may be shown before closure.

## FIR-INV-006 — Safe feature flags

**Status:** approved

Feature flags must never disable hard invariants, audit obligations, separation of duties or security gates.

## FIR-INV-007 — DLP and controlled export

**Status:** approved

Search and export must use:

- scoped access;
- reason codes;
- export purpose;
- DLP checks;
- rate limits;
- approval where required;
- audit evidence.

## FIR-INV-008 — Security Admin / System Admin separation

**Status:** approved

Security administration and system administration must remain distinct.

## FIR-INV-009 — JIT and break-glass governance

**Status:** approved

Privileged access must be:

- time-limited;
- purpose-bound;
- approved where required;
- fully audited;
- followed by out-of-band notification for break-glass.

## FIR-INV-010 — Document version integrity

**Status:** implemented in reference form  
**Implementing round:** PACK-11 implementation round (2026-07-28)

Historical versions must never be rewritten. Documents must preserve cryptographically linked history.

**How it is enforced.** `version_hash = sha256(canonical_dumps(hashable_fields(v)) + previous_version_hash)`,
the same rule `audit-core` uses for the audit log (ADR-003), so one
verification procedure covers both chains. Three independent defences:
`versions.verify_version_chain` _detects_ a rewrite;
`storage.InMemoryDocumentVersionStore` _refuses to perform_ one (no
replacement, no version number that is not head+1, no re-parenting, and
`record_state_change` compares `hashable_fields` rather than only the
stored hash); and `application._load_chain` re-verifies before every
governed act, so nothing is recorded against a history that no longer
verifies. At the workflow level, `returned_for_revision` is terminal for
that version and a correction is a new version, so immutability holds in
the process and not only in the store.

**Evidence paths:** `services/document-service/src/epd2_document_service/versions.py`;
`storage.py`; `application.py` (`_load_chain`, `verify_document_integrity`);
`services/document-service/tests/test_versions.py` (34 tests written against
the attacks: rewritten field, removed version, re-parented chain, swapped
content blob, resealed forgery); `docs/architecture/document-version-integrity.md`;
ADR-057.

**Remaining work.** The chain is tamper **evidence**, not tamper
**resistance**: an actor with write access to the whole store could rewrite
every version and recompute every hash. Closing that requires anchoring the
head hash outside this repository, or countersigning by a party that is not
the store operator — recorded as **OD-20** in
`docs/packs/PACK-11-OPEN-DECISIONS.md` and as limitation 1 in
`docs/handover/PACK-11-KNOWN-LIMITATIONS.md`. Until then this entry stays
`implemented in reference form`.

## FIR-INV-011 — Statistical Disclosure Control

**Status:** approved

Small samples and sensitive aggregates must use disclosure controls.

## FIR-INV-012 — Accessibility as Definition of Done

**Status:** approved

Accessibility is mandatory from the first frontend commit.

## FIR-INV-013 — Bund / Land / Kreis isolation

**Status:** approved

Organizational scope isolation must exist from the beginning of the data model.

## FIR-INV-014 — No universal administration

**Status:** approved

There must be no unrestricted universal admin panel spanning all domains.

## FIR-INV-015 — No false production claims

**Status:** approved

No feature may claim production, legal validity, anonymity, security certification or real-payment readiness until activation gates pass.

---

# 5. Institutional roles and separation of duties

## FIR-ROLE-001 — DPO

**Status:** approved

Institutional role for data protection governance.

## FIR-ROLE-002 — Election board / election officer

**Status:** approved

Election administration role separated from ordinary system administration.

## FIR-ROLE-003 — Independent auditor

**Status:** approved

Independent audit role with governed read-only or narrowly scoped access.

## FIR-ROLE-004 — Finance auditor

**Status:** approved

Independent finance-audit role separated from finance operations.

## FIR-ROLE-005 — Election Administration Separation Matrix

**Status:** approved

Must define incompatible and separated election roles.

## FIR-ROLE-006 — Finance separation of duties

**Status:** implemented in reference form

Includes separation of:

- payment authorization;
- payment execution;
- review;
- correction;
- reporting;
- independent audit.

---

# 6. Communication and correspondence

## FIR-COMM-001 — Communications & Official Correspondence

**Status:** captured — PACK-11 foundation available  
**Target:** future backend and frontend packages  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.OFFICIAL_CORRESPONDENCE` and
`OFFICIAL_NOTICE_PROOF`; governed attachments as versioned documents;
retention and legal-hold bindings; and the immutable, attributable record a
notice-proof package needs (PACK-09's `NoticeProofPackageRef` placeholder
pointed here).

PACK-11 does **not** provide messages, group or member-to-body
communication, delivery status, read status, moderation, channels or
governed templates. PACK-09 owns notice legal effect (ADR-043) and PACK-22
will own channels; delivery telemetry never establishes legal notice, and
nothing in PACK-11 changes that.

**Evidence:** `domain.DocumentKind`, `domain.RetentionBinding`,
`domain.LegalHoldBinding`.

**Remaining work:** everything in the scope list below except attachments,
retention and legal hold.

Scope:

- personal messages;
- group messages;
- member-to-body communication;
- official notices;
- attachments;
- delivery status;
- read status;
- moderation;
- retention;
- legal hold;
- governed templates.

## FIR-COMM-002 — Neutral sensitive notifications

**Status:** approved

Sensitive notifications must remain neutral and avoid exposing political or personal content in ordinary email or push notifications.

## FIR-COMM-003 — Communication Identity-Minimization Profile

**Status:** approved

Communication services must avoid unnecessary cross-domain identity correlation.

---

# 7. Candidacy and nominations

## FIR-CAND-001 — Candidacy & Nomination

**Status:** captured — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.CANDIDACY_DOCUMENT`,
`NOMINATION_PACKAGE` and `APPEAL_RECORD`; versioned candidate documents
with immutable history — the "versioned candidate documents" item of this
entry's own scope list; controlled review and approval; and sealed evidence
bundles for an admission or appeal file.

PACK-11 does **not** provide eligibility, deadlines, admission, rejection,
appeal procedure, election-process linkage or conflict checks. ADR-053
already reserves `AdmissionDecisionRef` for PACK-19, and PACK-09 owns the
procedural-case and deadline infrastructure.

**Evidence:** `domain.DocumentKind`, `evidence.EvidenceBundle`,
`docs/packs/PACK-11-CROSS-PACK-BOUNDARIES.md`.

**Remaining work:** everything in the scope list below except versioned
candidate documents.

Scope:

- internal roles and candidates;
- nomination package;
- eligibility;
- deadlines;
- review;
- admission;
- rejection;
- appeal;
- election-process linkage;
- versioned candidate documents;
- conflict checks.

---

# 8. Assemblies & Online Meetings

## FIR-ASM-001 — Meeting lifecycle

**Status:** captured  
**Priority:** high

Normal lifecycle:

```text
draft
→ internal_review
→ approved
→ published
→ delivered
→ active
→ closed
→ minutes_under_review
→ minutes_approved
→ archived
```

Meeting is created by an authorized person acting for the competent body.

## FIR-ASM-002 — Mandatory meeting card

Must show:

- convening body;
- organizational scope;
- meeting type;
- legal basis;
- date;
- time;
- time zone;
- location;
- room;
- accessibility;
- participation mode;
- registration deadline;
- motion and amendment deadlines;
- agenda version;
- documents;
- member participation status.

## FIR-ASM-003 — Meeting leadership and secretary

Must explicitly show:

- Versammlungsleitung;
- Protokollführung / Schriftführung;
- appointing authority;
- status;
- effective start and end;
- replacements;
- replacement reasons.

## FIR-ASM-004 — Agenda and documents

Agenda must be versioned and linked to:

- motions;
- amendments;
- documents;
- candidates;
- speakers;
- voting;
- AI analysis.

## FIR-ASM-005 — Online and hybrid participation

Must support:

- in-person;
- online;
- hybrid;
- controlled temporary meeting access;
- no permanent public meeting link;
- manual prototype attendance;
- later governed attendance and quorum.

## FIR-ASM-006 — Advance voting

Options:

```text
Ja
Nein
Enthaltung
```

Must show:

- exact proposal version;
- opening and closing;
- binding or advisory;
- majority rule;
- abstention handling;
- changeability;
- result publication rule.

No intermediate tally.

## FIR-ASM-007 — Closed confidential poll

For admitted participants only.

Properties:

- one response per participant;
- Ja / Nein / Enthaltung;
- no intermediate distribution;
- aggregated result after closure;
- no ordinary UI mapping person to answer;
- explicitly non-binding;
- no claim of cryptographic anonymity.

## FIR-ASM-008 — Prototype video meetings

Prototype may use external video service.

Must clearly state:

- external provider;
- manual attendance;
- manual quorum;
- manual minutes;
- no legal-completeness claim;
- no official secret voting through provider polls.

---

# 9. Minutes and Decision Register

## FIR-DEC-001 — Governed minutes

**Status:** captured — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.MEETING_MINUTES`; membership of
`domain.OFFICIAL_RECORD_KINDS`, which makes a substantive review mandatory
before approval and forbids publication without a named disclosure
obligation; immutable hash-linked versions; controlled review and approval
with three-actor separation; publication and citable renditions;
correction, supersession and revocation.

PACK-11 does **not** provide the minutes _content model_: leadership,
secretary, attendance, quorum, agenda version, motions, amendments,
results, decisions, objections, role changes, start and end. PACK-11 stores
a minutes document and does not know what is inside one.

**Evidence:** `services/document-service/src/epd2_document_service/domain.py`
(`DocumentKind`, `OFFICIAL_RECORD_KINDS`), `documents.py`
(`default_review_requirement`), `docs/packs/PACK-11-FIR-TRACEABILITY.md`.

**Remaining work:** the whole minutes content model and the assemblies
lifecycle (`FIR-ASM-001` … `FIR-ASM-008`), in a later package.

Approved minutes are the official record.

They must contain:

- leadership;
- secretary;
- attendance;
- quorum;
- agenda version;
- motions;
- amendments;
- results;
- decisions;
- objections;
- role changes;
- start and end.

## FIR-DEC-002 — Separate Decision Register

**Status:** captured — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.DECISION_RECORD`; stable identifiers;
exact, immutable versioned text; a minutes reference through
`GovernedDocument.subject_reference`; and supersession history through
`documents.SupersessionRecord`.

PACK-11 does **not** provide the register itself: outcome, vote result,
responsible person or body, due date, execution status
(`FIR-DEC-003`) and completion evidence. A decision register is a workflow
over decisions, not a store of documents about them.

**Evidence:** `domain.DocumentKind`, `documents.SupersessionRecord`,
`versions.DocumentVersion`.

**Remaining work:** the register entity, its status model and its execution
tracking, in a later package. Note that a decision's _vote result_ must
arrive as an aggregate: PACK-11 forbids any ballot, vote or tally reference
(`PROHIBITED_VOTING_KEYS`), so the register may not carry one either.

Required fields:

- stable ID;
- exact text;
- version;
- meeting;
- agenda item;
- minutes reference;
- outcome;
- vote result;
- responsible person or body;
- due date;
- status;
- completion evidence;
- supersession history.

## FIR-DEC-003 — Decision execution tracking

Statuses:

- open;
- in progress;
- blocked;
- completed;
- overdue;
- superseded;
- revoked.

---

# 10. Membership dues, payments and donations

## FIR-PAY-001 — Member financial self-service

Navigation:

```text
Meine Mitgliedschaft
→ Beiträge & Zahlungen
```

Must show:

- contribution rate;
- frequency;
- next due date;
- planned debit date;
- open amount;
- arrears;
- credit balance;
- payment method;
- mandate status;
- payment history;
- donations;
- refunds;
- receipts;
- certificates.

## FIR-PAY-002 — Contribution states

Statuses:

- announced;
- due;
- payment initiated;
- paid;
- overdue;
- failed;
- under clarification;
- waived;
- corrected;
- refunded.

## FIR-PAY-003 — SEPA mandate

**Status:** captured — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.SEPA_MANDATE_EVIDENCE`; an immutable,
hash-linked mandate evidence document; provenance recording how the
evidence entered the system; `SignatureDetermination` for a governed answer
to "is this a signed original?" (including the honest
`SIGNED_UNVERIFIED`); chain of custody; and the downloadable evidence a
member is entitled to, through the authority- and profile-checked
`read_document_content`.

PACK-11 deliberately **cannot** hold the mandate record itself. `iban`,
`bank_account`, `national_id` and `full_name` are all in
`domain.PROHIBITED_IDENTITY_KEYS`, so a creditor ID, an account holder or
an IBAN cannot be stored, emitted or projected by this service at all.
PACK-11 holds the _evidence document_; the mandate record — creditor,
creditor ID, mandate reference, scope, account holder, IBAN, consent
version, revocation, replacement reference — belongs to the payments
package.

This is a boundary, not a gap: "finance staff may not fabricate consent" is
enforceable precisely because the consent evidence lives in an immutable,
attributable store that finance does not own.

**Evidence:** `domain.DocumentKind`, `domain.PROHIBITED_IDENTITY_KEYS`,
`determinations.SignatureDetermination`, `evidence.CustodyEvent`.

**Remaining work:** the mandate record and its lifecycle, in the payments
package.

Member can:

- create;
- view;
- replace;
- revoke;
- download evidence.

Mandate must preserve:

- creditor;
- creditor ID;
- mandate reference;
- scope;
- account holder;
- IBAN;
- consent version;
- timestamp;
- revocation;
- replacement reference.

Finance staff may not fabricate consent.

## FIR-PAY-004 — Payment initiation

Supported future methods may include:

- SEPA direct debit;
- bank transfer;
- payment QR;
- card provider;
- approved payment provider.

Payment must not become `paid` before trusted confirmation or reconciliation.

## FIR-PAY-005 — Donations

Must support:

- one-time;
- recurring;
- amount;
- recipient;
- allowed purpose;
- declarations;
- compliance;
- receipt;
- separate accounting.

Membership contribution and donation remain separate.

Overpayment must not become donation without explicit consent.

## FIR-PAY-006 — Prototype financial journey

Prototype may show:

- history;
- next due;
- arrears;
- mock mandate;
- mock payment;
- mock donation;
- sample receipt.

Mandatory label:

```text
Prototype — keine echte Zahlung oder Abbuchung
```

---

# 11. Initiative Automated Pre-Publication Review Profile

## FIR-INIT-001 — Purpose

**Status:** proposed_normative

The profile defines mandatory pre-publication review for initiatives.

Goals:

- detect formal, technical, procedural and security issues;
- allow low-risk automatic publication eligibility;
- route ambiguous cases to humans;
- prevent hidden political censorship;
- preserve reason-coded, versioned and auditable decisions;
- provide correction and appeal.

AI may not make final political or legal decisions.

## FIR-INIT-002 — Review sequence

```text
draft
→ submitted
→ automated_prepublication_review
```

Possible outcomes:

- auto_publish_eligible;
- revision_required;
- manual_review_required;
- duplicate_candidate;
- scope_unresolved;
- procedural_type_uncertain;
- blocked_for_security.

An initiative must never be silently discarded.

## FIR-INIT-003 — Completeness filter

Checks:

- title;
- summary;
- full proposal;
- category;
- scope;
- intended outcome;
- declarations;
- sources;
- attachments;
- publication-rule acceptance.

## FIR-INIT-004 — Technical filter

Checks:

- length;
- encoding;
- meaningful content;
- executable attachments;
- supported file types;
- markup;
- script injection;
- malicious links;
- malware;
- broken attachments.

## FIR-INIT-005 — Scope resolution

Possible scopes:

- Bund;
- Land;
- Kreis;
- local;
- internal party procedure;
- Citizen Office;
- another governed procedure.

Low confidence produces `scope_unresolved`.

No silent legally significant scope assignment.

## FIR-INIT-006 — Duplicate and similarity detection

Checks:

- exact duplicate;
- near duplicate;
- active similar initiative;
- unchanged resubmission;
- coordinated mass submissions;
- repeated automated submissions.

Author can:

- view similar initiatives;
- join or support;
- explain differences;
- request manual review.

## FIR-INIT-007 — Sensitive data detection

Detect:

- uninvolved third-party names;
- addresses;
- phone numbers;
- emails;
- identity numbers;
- bank data;
- medical data;
- minors;
- sensitive membership data;
- voting data;
- credentials;
- secrets;
- tokens.

Sensitive findings must not enter ordinary logs or analytics.

## FIR-INIT-008 — Security and prohibited content

Flag:

- threats;
- incitement;
- doxxing;
- malicious instructions;
- malware;
- phishing;
- unlawful trade;
- sexual exploitation;
- immediate security risk.

Complex legal or political content goes to human review.

## FIR-INIT-009 — Toxicity boundary

Toxicity is advisory only.

It must not automatically reject:

- sharp criticism;
- criticism of party organs;
- unpopular opinion;
- emotional disagreement;
- controversial proposals.

## FIR-INIT-010 — Spam and automation abuse

Checks:

- frequency;
- repetition;
- generated noise;
- mass links;
- meaningless text;
- unchanged resubmission;
- suspicious automation.

Controls:

- rate limit;
- verification;
- manual review;
- reason-coded abuse decision.

## FIR-INIT-011 — Procedural classification

Possible classifications:

- initiative;
- amendment;
- complaint;
- appeal;
- Citizen Office request;
- message;
- programme proposal;
- candidacy submission;
- legal dispute.

No silent legally significant conversion.

## FIR-INIT-012 — Competence and routing

Detect:

- wrong level;
- outside competence;
- assembly decision required;
- constitutional/statutory change;
- candidacy procedure;
- legal review;
- Citizen Office routing.

Final material competence decisions require a human.

## FIR-INIT-013 — Sources and links

Check:

- accessibility;
- protocol safety;
- phishing;
- malware;
- source type;
- metadata;
- fabricated or malformed citations.

Reachability does not equal truth.

## FIR-INIT-014 — AI-generated content signals

AI use is not itself a rejection reason.

May flag:

- meaningless generated text;
- mass templates;
- fabricated sources;
- nonexistent quotations;
- contradictions;
- no concrete proposal.

## FIR-INIT-015 — Automatic publication conditions

`auto_publish_eligible` only when:

- mandatory fields complete;
- scope confidence sufficient;
- procedure clear;
- no sensitive-data blocker;
- no security blocker;
- no material abuse indicator;
- attachments pass;
- no unresolved critical duplicate;
- policy version known;
- no mandatory human-review trigger.

## FIR-INIT-016 — Mandatory human review

Required for:

- competence uncertainty;
- legal ambiguity;
- constitutional/statutory implication;
- defamation risk;
- privacy/public-interest conflict;
- disputed duplicate similarity;
- threats or severe harassment;
- uncertain procedure;
- Bund/Land/Kreis conflict;
- election-related initiative;
- finance-related initiative;
- emergency-governance initiative;
- unclear policy version;
- low confidence;
- contested automated classification.

## FIR-INIT-017 — Reviewer authority

Reviewer acts through scoped, effective-dated authority.

Reviewer may decide:

- publish;
- revision_required;
- formally_inadmissible.

Must not decide based on:

- political agreement;
- popularity;
- leadership alignment;
- electoral success;
- criticism of party organs;
- personal disagreement.

Negative decisions require:

- reason code;
- policy version;
- explanation;
- correction path;
- appeal path;
- timestamp;
- authority reference;
- immutable audit record.

## FIR-INIT-018 — Separation of duties

Separate where applicable:

- author;
- policy owner;
- initial reviewer;
- moderator;
- legal reviewer;
- appeal reviewer;
- system administrator.

Original decision-maker must not decide their own appeal.

## FIR-INIT-019 — Filter-result contract

Required fields:

- filter_id;
- policy_version;
- result;
- confidence;
- reason_code;
- recommended_action;
- evidence_reference;
- evaluated_at.

No unnecessary personal data.

## FIR-INIT-020 — Reason-code groups

At minimum:

- missing data;
- unsupported attachment;
- unsafe attachment;
- malicious link;
- scope unresolved;
- procedure uncertain;
- possible duplicate;
- confirmed spam;
- sensitive personal data;
- credential detected;
- security threat;
- abusive-content review;
- competence review;
- legal review;
- policy unavailable;
- manual review;
- correction required;
- formally inadmissible;
- reviewer conflict;
- appeal available.

## FIR-INIT-021 — Audit and versioning

**Status:** proposed_normative — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides: `DocumentKind.INITIATIVE_ATTACHMENT`; an immutable
submitted snapshot as a sealed version with a content digest; append-only
review records carrying a registered reason code, the deciding authority
and a timestamp; supersession and correction history; and the structural
guarantee this entry's closing sentence demands — **"later policy changes
must not rewrite historical decisions"** — because a `ReviewRequirement`
is stored on the document with its own policy version and a stored version
cannot be rewritten at all.

PACK-11 does **not** provide the initiative review pipeline: filter set,
filter results, policy versions, automated classification, reviewer
decisions on initiatives, corrections or appeals
(`FIR-INIT-001` … `FIR-INIT-024`).

**Evidence:** `documents.ReviewRequirement`, `documents.ReviewRecord`,
`versions.py`, `services/document-service/tests/test_versions.py`.

**Remaining work:** the review pipeline itself, in the initiative package.

Preserve:

- initiative ID;
- version;
- submitted snapshot;
- filter-set version;
- policy version;
- results;
- reviewer decisions;
- reasons;
- timestamps;
- authority references;
- corrections;
- appeals.

Later policy changes must not rewrite historical decisions.

## FIR-INIT-022 — Privacy and logging

Must not:

- log full initiative text in ordinary telemetry;
- expose sensitive findings;
- send political content to third parties without approved processing profile;
- create global author ID;
- create voting correlation bridge;
- include personal data in general events.

## FIR-INIT-023 — AI boundary

AI may:

- detect missing information;
- suggest classification;
- detect similarity;
- flag sensitive data;
- identify contradictions;
- recommend human review.

AI may not:

- make final political decision;
- make final legal decision;
- hide or delete initiative;
- change support counts;
- alter text;
- approve ballot readiness;
- determine voting eligibility;
- suppress criticism.

## FIR-INIT-024 — FRONT-02 requirements

Author-facing UI must provide:

- visible review status;
- understandable findings;
- correction guidance;
- similar-initiative suggestions;
- difference explanation;
- manual-review status;
- reason codes;
- appeal;
- initiative version;
- policy version;
- no hidden rejection.

Reviewer UI must provide:

- scoped queue;
- conflict declaration;
- filter results;
- immutable submitted version;
- reason codes;
- structured explanation;
- correction request;
- history;
- appeal handoff.

---

# 12. One-click AI deliberation analysis

## FIR-AI-001 — Mandatory one-click analysis

**Status:** approved  
**Priority:** high

Every initiative or project must provide a one-step AI analysis button.

Analysis must use an immutable snapshot of:

- initiative/project version;
- comments;
- arguments;
- amendments;
- sources.

Output must include:

- structured summary;
- arguments for;
- arguments against;
- contradictions;
- unresolved questions;
- sources;
- snapshot/version reference.

AI output must remain advisory and reproducible against the referenced snapshot.

---

# 13. Data governance and compliance

## FIR-DATA-001 — Data Catalog & Processing Registry

**Status:** approved

Must inventory:

- data categories;
- processing purposes;
- controllers/processors;
- retention;
- legal basis;
- data flows;
- access roles;
- transfers.

## FIR-DATA-002 — Legal Workflow & Deadline Management

**Status:** approved

Must support:

- legally governed deadlines;
- escalation;
- reminders;
- evidence of delivery;
- missed-deadline handling;
- appeal windows;
- authority assignment.

## FIR-DATA-003 — Legal Hold

**Status:** approved — PACK-11 foundation available  
**Last updated:** PACK-11 implementation round (2026-07-28)

Retention must support legal hold without silent deletion.

**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides the _document-side_ half: `domain.LegalHoldBinding` with a
three-valued state (`active` / `released` / `indeterminate`);
`documents.assert_no_destruction_under_hold`, which refuses under an active
hold with `RECORD_UNDER_LEGAL_HOLD` and fails closed under an
indeterminate one with the distinct `LEGAL_HOLD_STATE_UNKNOWN` — the two
are never collapsed, because "we could not confirm the hold" must not later
read as "there was a hold"; **no delete method on any storage port**, with
the single module-level `delete_document_record` existing only to refuse;
and a disposition path that requires a current PACK-09 destruction
authorization and treats one issued against a smaller version count as
stale.

PACK-11 does **not** own legal hold. PACK-09 issues, scopes and releases
holds and authorizes destruction. PACK-11 records PACK-09's answer with the
moment it was observed, re-reads rather than caches it across acts, and
refuses without it.

**Evidence:** `domain.LegalHoldBinding`, `documents.assert_no_destruction_under_hold`,
`documents.assert_disposition_authorized`, `storage.delete_document_record`,
`services/document-service/tests/test_documents.py`,
`tests/repository/test_service_boundaries.py::test_document_service_storage_exposes_no_delete_operation`.

**Remaining work:** hold propagation to replicas, indexes and exports
(PACK-12/PACK-13); what a completed disposition leaves behind (OD-25); and
PACK-09's own production-side implementation.

---

# 14. Party finance and external influence

## FIR-FIN-001 — Party Finance Reporting

**Status:** implemented in reference form / further production work required

Includes:

- ledger;
- contribution records;
- donation records;
- sponsorship;
- expenses;
- obligations;
- reporting lifecycle;
- Rechenschaftsbericht;
- audit handoff.

## FIR-FIN-002 — External influence and sponsorship

**Status:** captured

Must cover:

- sponsorship;
- benefits;
- external influence;
- meeting disclosure;
- lobbying disclosure;
- donor/source checks;
- conflicts of interest.

## FIR-FIN-003 — Operational finance activation

**Status:** production_blocked

Requires:

- production DB;
- banking/payment integration;
- reconciliation;
- provider contracts;
- legal review;
- finance UI;
- operational controls.

---

# 15. Emergency, ethics and oversight

## FIR-GOV-001 — Emergency Governance

**Status:** captured

Must define:

- emergency trigger;
- scope;
- duration;
- override limits;
- review;
- expiry;
- audit;
- restoration of normal governance.

## FIR-GOV-002 — Constitutional & Ethics Oversight

**Status:** captured

Must provide:

- constitutional review;
- ethics review;
- conflict handling;
- independent authority;
- published or controlled findings.

## FIR-GOV-003 — Independent oversight workspace

**Status:** captured

Must provide narrow, governed access for:

- independent auditor;
- finance auditor;
- election oversight;
- DPO;
- ethics oversight.

---

# 16. Representative and public interface

## FIR-REP-001 — Open Representative Desk

**Status:** captured

Must provide:

- representative office;
- requests;
- progress;
- obligations;
- responses;
- transparency.

## FIR-REP-002 — Parliamentary Interface

**Status:** captured

Must connect internal initiatives, mandates and representative activity.

## FIR-REP-003 — Lobbying & Meeting Disclosure

**Status:** captured

Must disclose governed lobbying and external meetings.

## FIR-REP-004 — Citizen Office Routing

**Status:** captured

Must route citizen requests to competent body without converting them silently into another procedure.

---

# 17. Program formation and delegation

## FIR-PROG-001 — Program Formation Lifecycle

**Status:** captured

Must cover:

- proposal;
- deliberation;
- amendment;
- consolidation;
- conflict resolution;
- approval;
- publication;
- version history.

## FIR-PROG-002 — Mandatory Pre-Adoption AI, Expert and Legal Review

**Status:** approved  
**Priority:** high  
**Domain:** program formation / legal / expert review  
**Target:** Program Formation Lifecycle package and member-facing adoption workflow

Before any programme provision may proceed to final adoption, the system must enforce a mandatory pre-adoption review gate.

### Mandatory AI analysis

A separate AI analysis must be generated for the exact immutable version of the programme provision that is intended for adoption.

The AI analysis must examine at least:

- internal contradictions;
- contradictions with other programme provisions;
- foreseeable consequences;
- implementation risks;
- affected institutional and organizational domains;
- relation to existing law and regulation;
- relation to party statutes and internal rules;
- unresolved questions;
- assumptions requiring human verification;
- source and evidence gaps.

The AI analysis must remain:

- advisory;
- contestable;
- versioned;
- reproducible against the referenced snapshot;
- clearly separated from human expert conclusions.

AI must not:

- make the final adoption decision;
- replace legal review;
- certify legal admissibility;
- suppress a proposal because of political disagreement;
- silently alter the programme provision.

### Mandatory expert opinions

Separate expert opinions must be obtained where relevant from competent subject-matter specialists.

At minimum, the workflow must support:

- legal opinion;
- financial/economic opinion;
- technical opinion;
- social-policy opinion;
- constitutional opinion;
- data-protection opinion;
- security opinion;
- implementation/operations opinion;
- other domain-specific opinion.

### Mandatory legal opinion

A legal opinion is mandatory before final adoption.

It must assess at least:

- legal admissibility;
- competence of the party or relevant party body;
- conformity with the Grundgesetz;
- conformity with the Parteiengesetz;
- conformity with party statutes;
- relation to applicable federal, state and EU law;
- implementation constraints;
- legal risks;
- need for statutory, constitutional or procedural changes.

### Versioning and attribution

Every AI analysis and expert opinion must be:

- linked to the exact immutable version of the programme provision;
- versioned;
- signed or otherwise attributable;
- dated;
- assigned to a qualified author or responsible institution;
- preserved in immutable history;
- available to eligible participants before voting;
- replaced only through an explicit supersession record.

A later change to the programme provision invalidates the adoption readiness of prior analyses and opinions unless they are explicitly confirmed for the new version.

### Adoption gate

A programme provision must not enter final adoption voting unless:

- mandatory AI analysis exists;
- mandatory legal opinion exists;
- required subject-matter opinions exist;
- all materials refer to the exact adoption version;
- all materials are available to eligible participants;
- required review periods have elapsed;
- unresolved blocking findings have been formally addressed or reason-coded;
- the competent authority confirms adoption readiness.

### User-facing requirements

Participants must be able to see:

- programme provision version;
- AI analysis status;
- legal opinion status;
- expert-opinion status;
- authors and attribution;
- publication timestamps;
- open findings;
- blocking findings;
- superseded opinions;
- adoption-readiness status.

Suggested status model:

```text
draft
→ deliberation
→ expert_review_required
→ expert_review_in_progress
→ legal_review_required
→ legal_review_in_progress
→ review_complete
→ adoption_ready
→ adopted / rejected / returned_for_revision
```

### Separation of duties

Where applicable, the following roles must remain distinct:

- programme author;
- AI policy owner;
- subject-matter expert;
- legal reviewer;
- adoption-readiness confirmer;
- voting administrator;
- final voting participants.

A person must not approve their own expert or legal opinion without an independent review path where required.

### PACK-11 foundation (2026-07-28)

**Status:** approved — PACK-11 foundation available.
**PACK-11 foundation provided — this entry is NOT implemented.**

PACK-11 provides the governed shape every AI analysis and expert or legal
opinion in this entry needs: `DocumentKind.PROGRAMME_PROVISION`,
`LEGAL_OPINION`, `EXPERT_OPINION` and `AI_ANALYSIS_RECORD`;
`ReviewKind.LEGAL` plus `authorization.assert_reviewer_qualified`, so a
general reviewer cannot sign off a legal opinion; opinions linked to the
**exact immutable version** they examined; versioning, dating and
attribution to a qualified authority; preservation in immutable history;
replacement only through an explicit `SupersessionRecord`; and
`Provenance.analysis_provenance_reference`, through which an AI analysis
points at the AI accountability context's own provenance contract
(`FIR-AI-002`) rather than restating it.

The requirement that "a later change to the programme provision invalidates
the adoption readiness of prior analyses and opinions unless explicitly
confirmed for the new version" has its structural half here: a
determination or approval is bound to a version hash and does not carry
forward.

PACK-11 does **not** provide **the adoption gate**. Nothing in PACK-11
enforces that a programme provision cannot enter final adoption voting
without the mandatory AI analysis, legal opinion and applicable expert
opinions. That gate — the acceptance criterion of this entry — belongs to
the programme-formation package and remains unimplemented.

**Evidence:** `domain.DocumentKind`, `documents.ReviewKind`,
`authorization.assert_reviewer_qualified`, `determinations.py`,
`documents.SupersessionRecord`, `domain.Provenance`.

**Remaining work:** the adoption-readiness state model, the gate itself,
participant availability evidence, and the user-facing status surface.

### Audit and evidence

The system must preserve:

- programme provision ID;
- exact version;
- analysis and opinion IDs;
- authorship and qualifications;
- timestamps;
- review scope;
- findings;
- blocking status;
- resolution references;
- supersession history;
- participant availability evidence;
- adoption-readiness decision;
- final voting reference.

### Acceptance criteria

The implementation is complete only when no programme provision can reach final adoption voting without the required AI analysis, legal opinion and applicable expert opinions linked to the exact version and made available to participants in advance.

## FIR-PROG-003 — Public Presentation of Adopted Programme and Projects

**Status:** approved
**Priority:** high
**Domain:** public website / program formation / governed publication
**Target:** future Public Website and Program Formation frontend packages
**Recorded by:** PACK-13 candidate documentation correction (2026-07-30).
This entry was approved before the PACK-13 implementation candidate was
built but had not yet been written into this register; the correction adds
it and changes nothing else.

### Why this entry exists

A party's public `Programm` page has one job: say what the party has
actually decided. The failure mode is specific and common — the page fills
up with proposals, drafts and things "in discussion", a reader cannot tell
which sentences are binding, and the adopted programme becomes one voice
among many on its own page. Every requirement below exists to prevent
that, and the distinction it protects is **adopted versus not adopted**,
not "new versus old".

### Normative requirement

**The adopted programme is the primary content of the public `Programm`
page.** It is what a reader sees first, and it dominates the page both
visually and in substance.

For the programme as a whole, and where applicable for each thematic
section, the following must be directly available:

- the exact text currently in force;
- the version number;
- the date of adoption;
- the competent body that adopted it;
- the manner of adoption — for example a `Parteitag` or a
  `Mitgliederentscheid`;
- the date it entered into force;
- a reference to the adopting decision;
- the change history;
- previous versions, reachable through a separate archive path.

**Public projects and proposals must not be rendered as a full list beside
the adopted programme**, and must not crowd the main page.

After the corresponding thematic section, exactly **one** compact,
secondary card is permitted:

```text
Projekte in Beratung
```

That card must:

- show the number of active projects;
- carry the explicit marking `Noch nicht beschlossen`;
- link to a separate projects page for that thematic section;
- not read as part of the adopted programme.

A **separate page listing all public projects** must exist in addition.

### The status distinction must not rest on colour alone

The difference between the adopted programme and projects must be carried
**simultaneously** by:

- a textual status;
- the page structure;
- the shape of the card;
- an icon or another accessible visual marker;
- different actions and links.

Colour alone is not an accessible status signal, and it is not a
sufficient one here for the same reason `FIR-INV-012` exists: a reader who
cannot distinguish the two by colour must still be able to tell what the
party has decided from what it is merely discussing.

### Boundaries

This entry is:

- a **future frontend obligation**;
- **not** a PACK-13 implementation item, and not implemented by it;
- **not** a canon change;
- **not** a basis for treating Program Formation as implemented;
- **not** a basis for treating the Public Website as complete.

PACK-13 records this requirement and touches nothing it governs. No
data-plane model, event, reason code or contract in
`services/data-plane-service` presents, orders or renders programme
content.

### Dependencies

`FIR-PROG-001` (the programme formation lifecycle that produces an adopted
version at all), `FIR-PROG-002` (the pre-adoption review gate whose
decision reference this page cites), `FIR-INV-012` (accessibility), and
the governed-publication semantics PACK-11 owns — an adopted version is an
immutable governed version, and previous versions are superseded rather
than overwritten.

### Acceptance criteria

The requirement is implemented only when:

1. the main page does not mix a full list of projects into the text in
   force;
2. the adopted text and the facts of its adoption — version, date, body,
   manner, entry into force, decision reference — are directly available;
3. the projects card states explicitly that the material is not yet
   adopted;
4. projects open on a separate page;
5. the status is distinguishable without relying on colour alone;
6. historical versions are not overwritten.

## FIR-DEL-001 — Delegation Reputation

**Status:** captured

Must avoid opaque scoring and preserve contestability, context and disclosure control.

---

# 18. Security, resilience and operations

## FIR-SEC-001 — Security Incident & Breach Response

**Status:** approved

Must include:

- detection;
- classification;
- containment;
- evidence preservation;
- notification;
- recovery;
- post-incident review.

## FIR-SEC-002 — Backup Verification & Recovery Testing

**Status:** approved

Backups are not accepted merely because they exist; restoration must be tested.

## FIR-SEC-003 — External gateway security

**Status:** approved

All external providers require:

- minimized data;
- purpose limitation;
- typed contracts;
- failure handling;
- audit;
- provider replacement strategy.

---

# 19. Frontend workspace model

## FIR-FRONT-001 — Multi-workspace architecture

**Status:** approved

No single universal admin panel.

Workspaces include:

- public website;
- member core;
- Voting Client;
- mandate holder;
- Citizen Office;
- institutional administration;
- compliance/legal;
- finance;
- independent oversight;
- transparency/publication.

## FIR-FRONT-002 — Institutional minimalism

**Status:** approved

Shared visual language:

- calm civic design;
- white/light-gray;
- clear status;
- no manipulative UI;
- accessibility;
- predictable navigation;
- visible audit and version references where relevant.

## FIR-FRONT-003 — Mobile App Scope and Workspace Boundaries

**Status:** approved  
**Priority:** high  
**Domain:** mobile frontend / workspace architecture  
**Target:** future EPD² Mobile App package

The EPD² Mobile App is not an eleventh workspace and must not become an additional universal origin.

Primary scope:

- WS-02 Member Core;
- selected low-risk functions of WS-05 Citizen Office;
- neutral notifications;
- personal tasks;
- meeting participation preparation;
- contribution and payment self-service where activation gates pass.

The ordinary Mobile App must not directly include:

- WS-06 Institutional Administration;
- WS-07 Compliance & Legal;
- WS-08 Finance Operations;
- WS-09 Independent Oversight;
- privileged administration;
- security administration;
- system administration;
- operational election administration.

The Mobile App must preserve the same trust boundaries as the web architecture.

It must not:

- collapse all workspaces into one universal session;
- expose privileged functions through ordinary member authentication;
- share ordinary member session state with the Voting Client;
- treat native-app presence as authorization for sensitive workspaces.

Offline support may be used only for safe, non-consequential functions.

Consequential offline actions are prohibited, including:

- voting;
- consent creation;
- payment confirmation;
- legal submission;
- deadline-sensitive appeal submission;
- privileged approval;
- publication approval;
- destructive changes.

Acceptance criteria:

- app scope is explicitly limited;
- privileged workspaces are absent from the ordinary app;
- workspace isolation remains enforceable;
- offline mode cannot create consequential state changes.

## FIR-FRONT-004 — Mobile Voting System-Browser Handoff

**Status:** approved  
**Priority:** high  
**Domain:** mobile frontend / voting isolation  
**Target:** Mobile App package + Voting Client integration

Required flow:

```text
EPD² Mobile App
→ one-time purpose-scoped handoff
→ system browser
→ separate WS-03 Voting Client
→ return without ballot data
```

Mandatory rules:

- voting must open in the operating system's external system browser;
- embedded WebView is prohibited for voting;
- the Mobile App does not host WS-03;
- the Mobile App does not become a voting origin;
- no ordinary member session is transferred to WS-03;
- no shared cookies;
- no shared localStorage;
- no shared IndexedDB;
- no shared analytics;
- no shared telemetry;
- no persistent member identifier;
- only one-time, purpose-scoped handoff material may be transferred.

Permitted return statuses:

```text
completed
cancelled
expired
failed
```

Return path requirements:

- signed or one-time return deep link;
- no ballot reference;
- no vote content;
- no candidate selection;
- no tally information;
- no linkable voting identifier;
- no persistent cross-origin correlation token.

After return, the Mobile App must:

- clear its temporary voting handoff context;
- preserve only the permitted terminal status;
- avoid caching sensitive handoff data;
- avoid exposing voting details in logs, notifications or recent-task previews.

Acceptance criteria:

- voting always leaves the app for the system browser;
- no embedded WebView path exists;
- return carries only a permitted terminal status;
- no ballot or vote data reaches the Mobile App.

## FIR-FRONT-005 — Mobile Security and Notification Profile

**Status:** approved  
**Priority:** high  
**Domain:** mobile security / notifications  
**Target:** Mobile App package

### Notifications

Push payloads must be neutral.

They must not include:

- political content;
- initiative title where sensitive;
- vote topic;
- membership status detail;
- legal-case detail;
- finance detail;
- confidential message content;
- candidate preference;
- ballot status beyond neutral action availability.

Preferred pattern:

```text
Eine neue Mitteilung ist in EPD² verfügbar.
```

### Device and session controls

The user must be able to:

- view active mobile sessions;
- identify registered devices;
- revoke a device;
- terminate one session;
- perform remote logout;
- revoke all sessions;
- see last activity and session creation time where appropriate.

### Crash logs and telemetry

Crash and diagnostic logs must:

- exclude message content;
- exclude initiative text;
- exclude voting context;
- exclude financial details;
- exclude attachments;
- exclude access tokens;
- minimize identifiers;
- use approved retention;
- remain purpose-limited.

### Clipboard

Sensitive values must not be copied automatically.

Where copying is permitted:

- explicit user action is required;
- warning may be shown;
- clipboard clearing should be used where platform support is reliable;
- secrets, credentials and voting artifacts must never be copied.

### Screenshots and screen recording

Sensitive screens must define screenshot policy.

High-risk screens may require:

- screenshot blocking where supported;
- recent-app preview obfuscation;
- warning when screen recording is detected where supported;
- no hidden reliance on screenshot blocking as sole protection.

### OS sharing

OS share sheets must be restricted to explicitly shareable content.

The app must not expose through sharing:

- confidential attachments;
- voting material;
- legal case files;
- identity evidence;
- privileged reports;
- financial records;
- internal moderation findings.

### Local storage

Local mobile storage must be:

- minimized;
- encrypted using platform protections;
- scoped by function;
- cleared on logout where required;
- protected from backup where data sensitivity requires it.

Acceptance criteria:

- neutral push payloads are enforced;
- device revocation and session inventory exist;
- crash logs, clipboard, screenshots, sharing and local storage follow explicit security rules.

## FIR-MEM-001 — Membership Appeal Pending UI Contract

**Status:** approved  
**Priority:** high  
**Domain:** membership / legal-compliance / frontend  
**Target:** WS-02 Member Core + WS-07 Compliance & Legal

A membership appeal must have a split frontend model.

### Applicant-facing placement

The applicant sees the appeal in WS-02 Member Core.

Required state:

```text
membership_appeal_pending
```

Applicant-facing UI must show:

- appeal ID;
- related decision;
- submission timestamp;
- current status;
- applicable deadline;
- documents submitted;
- requests for additional information;
- reason-coded updates;
- decision when issued;
- next available remedy;
- no hidden rejection or silent closure.

The applicant must not see:

- internal reviewer deliberation;
- privileged notes;
- conflict declarations of unrelated staff;
- legal strategy;
- internal risk scoring;
- restricted evidence.

### Staff-facing placement

Authorized staff process the appeal in WS-07 Compliance & Legal.

Staff UI must provide:

- scoped queue;
- authority verification;
- conflict-of-interest declaration;
- immutable appealed decision;
- evidence bundle;
- deadlines;
- reason codes;
- request-for-information workflow;
- decision drafting;
- independent reviewer assignment;
- audit history;
- handoff to further remedy where applicable.

### Separation of duties

The original decision-maker must not make the final decision on the appeal against their own decision.

### Acceptance criteria

The applicant can track the appeal transparently in WS-02 while authorized staff process it in WS-07 with full separation of duties and audit history.

## FIR-AI-002 — AI Analysis Provenance and Staleness Contract

**Status:** approved  
**Priority:** high  
**Domain:** AI accountability / initiatives / deliberation / programme formation  
**Target:** AI analysis services and all frontend surfaces showing AI analysis

Every generated AI analysis must preserve a complete provenance contract.

Required fields:

- analysis_id;
- subject_type;
- subject_id;
- subject_version;
- DiscussionSnapshot reference;
- immutable snapshot digest;
- model provider;
- model family;
- exact model version;
- prompt-template ID;
- prompt-template version;
- system-instruction version;
- tool-policy version where applicable;
- retrieval profile version;
- source set references;
- generation timestamp;
- generation parameters where policy permits;
- safety or policy profile version;
- output digest;
- human-review status;
- stale flag;
- stale reason.

### DiscussionSnapshot

The analysis must be generated from an immutable DiscussionSnapshot containing the exact referenced state of:

- initiative or project version;
- comments;
- arguments;
- amendments;
- sources;
- relevant decisions;
- applicable policy or programme text.

The snapshot must be reproducible and content-addressed or otherwise protected by an immutable digest.

### Staleness

An analysis becomes stale when any material input changes, including:

- initiative text;
- project text;
- comment set;
- argument set;
- amendment set;
- source set;
- relevant decision;
- policy context;
- programme provision;
- prompt-template version where policy requires regeneration;
- model version where policy requires regeneration.

Frontend must clearly show:

```text
Aktuell
Veraltet
Neue Analyse erforderlich
```

A stale analysis must not be presented as current.

### User-facing provenance

Users must be able to see at least:

- analysis timestamp;
- referenced subject version;
- snapshot reference;
- model version;
- prompt-template version;
- whether the analysis is stale;
- why it is stale;
- whether a newer analysis exists.

### AI boundary

Provenance does not convert AI output into authority.

AI analysis remains:

- advisory;
- contestable;
- reproducible;
- attributable to a specific model and prompt configuration;
- distinct from legal, expert or political decisions.

### Acceptance criteria

No AI analysis is displayed without provenance, immutable snapshot reference, digest and staleness status.

---

# 20. Activation gates

No domain may be called production-ready until relevant gates pass.

Required gate families:

- architecture approval;
- legal review;
- security review;
- privacy review;
- accessibility review;
- provider readiness;
- incident readiness;
- backup recovery test;
- independent audit;
- CI verification;
- operational ownership;
- documentation;
- training;
- rollback readiness.

---

# 21. Current implementation status summary

## Implemented

- PACK-01 through PACK-10 (PASS);
- PACK-11 (PASS — external GitHub Actions verification complete);
- **PACK-12 (PASS — external GitHub Actions verification complete);**
- FRONT-00;
- FRONT-01;
- finance reference implementation;
- **governed documents and evidence reference implementation** (PACK-11);
- **privileged administration, authorization-aware search and governed
  export reference implementation** (PACK-12);
- cumulative architecture baseline;
- 45 visual snapshots.

"Reference implementation" is the operative qualifier for PACK-10,
PACK-11 and PACK-12 alike: the governed workflows are real and externally
verified; the production data plane is not. Nothing in this list is
production ready or legally activated.

## Specified but not implemented

- most domains in this register;
- FRONT-02 Member Core;
- assemblies;
- decision register (PACK-11 provides the document foundation only);
- member payments;
- SEPA mandate record (PACK-11 provides the mandate _evidence_ foundation only);
- full voting implementation;
- production data plane;
- identity/auth;
- communications (PACK-11 provides the correspondence-document foundation only);
- candidacy (PACK-11 provides the candidacy-document foundation only);
- the FIR-PROG-002 pre-adoption gate (PACK-11 provides the opinion-document
  foundation only);
- emergency governance;
- representative desk;
- lobbying disclosure;
- applicant and member cabinets, identity and session model, communication
  persona and scoped directory, person/document search surfaces, layered
  user assistance, and membership metrics (sections 24 and 25) — PACK-12
  supplies enforcement foundations for authorization-aware search and
  small-cohort disclosure control only, and implements none of these
  surfaces.

## Production-blocked

- real banking/payment integration;
- production voting;
- production identity;
- production DB/event bus;
- real external gateway activation;
- operational finance UI.

## Legally blocked pending review

- legally binding online assemblies;
- legally binding advance voting;
- election activation;
- donation processing details;
- public disclosure rules;
- emergency override activation.

---

# 22. Repository checks to add

Future repository checks should verify:

- FIR IDs are unique;
- no implemented FIR lacks package/handover reference;
- no scheduled FIR lacks acceptance criteria;
- no FIR disappears silently;
- all future PACK tasks reference FIR IDs;
- baseline archives contain this file;
- status transitions preserve reason and date;
- no duplicate standalone future-register file exists;
- this file is present at `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`
  (added to `scripts/check_repository.py`'s required paths by the PACK-11
  round, so a cumulative archive that dropped it now fails a check rather
  than passing quietly);
- no entry marked `implemented` where only a foundation exists — the
  PACK-11 round's own discipline, recorded here so a later round inherits
  it: eight entries in this register carry
  "**PACK-11 foundation provided — this entry is NOT implemented.**" and
  must keep it until the domain itself is built.

---

# 23. Single-file policy

This document is the only future-implementation register.

Do not create additional standalone files for:

- idea capture;
- future feature lists;
- separate reminders;
- separate roadmap addenda;
- duplicate normative intake notes.

Implementation-specific artifacts may still be created inside the relevant PACK when needed, but the master capture and status remain here.

---

# 24. User accounts, identity, communication, search and support

## FIR-UX-001 — Applicant Account Scope

**Status:** approved  
**Priority:** high  
**Domain:** membership / frontend / identity  
**Target:** FRONT-02 Member Core + membership backend + PACK-14

An applicant must receive a restricted personal account for their own membership procedure.

The applicant-facing account must show at least:

- application ID;
- submission timestamp;
- current status;
- competent organizational unit;
- current procedural stage;
- applicable deadlines;
- requested supplementary information;
- submitted documents and their verification state;
- applicant-visible timeline;
- official messages and notices;
- final decision;
- reasons and reason codes where applicable;
- correction, remedy and appeal path;
- security/session information.

The applicant must not automatically receive access to member-only functions.

The applicant must not see:

- internal reviewer deliberation;
- privileged notes;
- protected evidence;
- unrelated conflict declarations;
- legal strategy;
- other applicants' data;
- member directory;
- internal initiatives, assemblies or voting.

A membership decision must be a governed state transition. Account creation alone must not establish membership.

### Acceptance criteria

- the applicant can track the complete applicant-visible procedure;
- every request for additional information shows a deadline and response path;
- rejection is never shown without an explanation and available remedy where applicable;
- applicant access remains restricted until an authoritative membership decision activates member status.

## FIR-UX-002 — Member Core Personal Workspace

**Status:** approved  
**Priority:** high  
**Domain:** membership / frontend  
**Target:** FRONT-02 Member Core and dependent domain packages

A member must receive a personal Member Core workspace showing only functions available through the member's current status, organizational scope, authority and procedure participation.

The workspace should provide governed access to:

- membership record and status;
- Bund/Land/Kreis affiliation;
- personal tasks and deadlines;
- messages and official notices;
- initiatives and deliberation;
- assemblies and documents;
- eligibility status and voting handoff;
- candidacy and nomination procedures;
- delegation where implemented;
- contributions, payments, donations and receipts where activated;
- personal governed documents;
- decisions relevant to the member;
- account, device and session security.

The ordinary member workspace must not expose:

- other members' protected data;
- administrative workspaces;
- legal/compliance investigations;
- whistleblower submissions;
- raw finance operations;
- privileged audit evidence;
- ballot content;
- intermediate tally;
- closed materials outside the member's authority or participation scope.

The Voting Client remains a separate workspace and origin. Member Core may show only permitted voting availability and terminal handoff status.

## FIR-ID-001 — No Universal User Identifier

**Status:** approved  
**Priority:** critical  
**Domain:** identity / privacy / all domains  
**Target:** PACK-14 + all domain implementations

No single identifier may represent a person across all EPD² domains, workspaces and procedures.

The architecture must distinguish at least:

- protected identity/person record;
- IAM account identifier;
- domain-specific subject identifier;
- membership identifier;
- visible membership number where used;
- case/procedure identifier;
- scoped actor reference;
- one-time voting credential.

A visible membership number:

- belongs only to the membership record;
- is not a login credential;
- is not a global user ID;
- must not be used by the Voting Client;
- must not be a system-wide lookup key;
- must not be exposed to ordinary members as a directory identifier.

Cross-domain mappings must be explicit, purpose-bound, access-controlled, auditable and limited to the minimum necessary relationship.

### Acceptance criteria

- no API, event, index or UI introduces a global person key;
- domain identifiers are not interchangeable;
- voting receives no persistent member or account identifier;
- account identifiers are not exposed as public or user-facing identifiers;
- cross-domain correlation requires a governed mapping boundary.

## FIR-ID-002 — Workspace-Specific Account and Session Model

**Status:** approved  
**Priority:** high  
**Domain:** identity / sessions / frontend architecture  
**Target:** PACK-14

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12 supplies the privileged-session model that a workspace-scoped
session would have to satisfy: a session is bound to one grant, one
purpose, one target domain and one organizational scope, and it seals
into tamper-evident evidence. It supplies no authentication, no session
issuance and no identity of any kind — all of that remains PACK-14's.

Authentication must not create a universal session spanning all workspaces.

The identity architecture must support at least:

- restricted applicant account;
- Member Core account/session;
- Citizen Office case-scoped account or secure case token;
- separate privileged/admin assurance context;
- separate Voting Client session created through one-time purpose-scoped handoff.

Target authentication options may include:

- passkeys/WebAuthn;
- controlled fallback credential;
- MFA and step-up authentication;
- email magic link for limited activation or recovery purposes;
- external identity/eID verification only where needed;
- governed account recovery;
- device and session management.

Final provider and credential choices remain PACK-14 decisions.

## FIR-COMM-004 — Member Communication Persona and Scoped Directory

**Status:** approved  
**Priority:** high  
**Domain:** communications / membership / privacy  
**Target:** Communications package + FRONT-02

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12 supplies only the negative half: its records carry opaque actor
_references_ and never a person identifier, and `ActorRef` on every event
names the acting authority rather than the human behind it
(`FIR-INV-001`). The communication persona, the scoped directory and the
messaging surfaces remain the Communications package's and FRONT-02's.

Communication between members must use a separate scoped communication persona, not a membership number, IAM account ID or global person ID.

The communication persona may contain only policy-permitted fields such as:

- `communication_persona_id`;
- display name;
- permitted organizational affiliation;
- visible role or working-group function;
- contact permissions;
- visibility policy;
- relevant shared context.

Ordinary member discovery must not expose:

- membership ID;
- membership number;
- IAM identifier;
- private email;
- telephone number;
- home address;
- date of birth;
- identity evidence;
- hidden administrative attributes.

Member-to-member discovery and messaging must be restricted by:

- organization scope;
- shared group, initiative, assembly or procedure context;
- contact permissions;
- privacy settings;
- sender authority;
- anti-bulk-extraction controls.

Official communication from a competent party body may use a governed official channel even when ordinary direct messaging is restricted.

## FIR-SEARCH-001 — Authorization-Aware Domain-Scoped Search

**Status:** approved  
**Priority:** critical  
**Domain:** search / security / all workspaces  
**Target:** PACK-12 + PACK-13 + frontend packages

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12's `privileged-access-service/search.py` supplies the enforcement
core: exactly two governed modes with no third, the mode→purpose
admission table, the absolutely-excluded domain set, result-time
re-resolution of source authorization through `SourceAuthorizationPort`
(so nothing is trusted from the index but the pointer), snippet
suppression at restricted tiers, suppression _bands_ rather than counts,
and an authorization-context-keyed result cache. `Purpose.INVESTIGATION`
is the resolution of `OD-P12-02`: investigation is a purpose that narrows
the ordinary scoped search and requires an explicit grant, not an
unrestricted investigative mode.

It deliberately does not supply the production search engine, the index
pipeline, or any frontend search surface, and its adapters are in-memory.
Remaining: PACK-13's production index and PACK-14/FRONT's search UI.

EPD² must not provide one unrestricted global search across all domains.

Supported search patterns must include:

- public search over approved publication renditions;
- general authorized search within a workspace;
- domain-scoped search;
- privileged scoped search with explicit grant, purpose, scope, reason code and audit.

Core rule:

```text
findable subset of openable
```

Search must never expand source authorization.

Authorization must be checked at least at:

- index eligibility;
- query authorization;
- per-result source authorization;
- result rendering;
- snippet/highlight generation;
- count/facet/autocomplete generation;
- cache retrieval.

The index is not authoritative and must not create legal effect.

### Required protections

- stale index ACL must not preserve access;
- unauthorized matches must not affect visible counts;
- facets and suggestions must not reveal restricted values;
- cache must be partitioned by security context, organization, purpose and policy version;
- unknown classification must fail closed;
- deleted, expired or access-revoked records must become non-retrievable;
- legal hold must not expand search access;
- small cohorts must use disclosure controls.

## FIR-SEARCH-002 — Search for Persons

**Status:** approved  
**Priority:** high  
**Domain:** search / membership / communications / case management  
**Target:** PACK-12 + FRONT-02 + Communications package

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12 supplies the purpose-binding and grant requirement that make
person search purpose-specific rather than open, and the organizational
scope check that stops it crossing a boundary. It supplies no person
model, no directory and no membership data: identity remains PACK-14's
and the member workspace remains FRONT-02's.

Person search must be purpose-specific.

Ordinary members may search only communication personas visible in their permitted scope.

Staff may search applicants, case parties or procedure participants only within an authorized case, queue or organizational scope.

Permitted search keys may include, depending on role and purpose:

- display name;
- application ID;
- case ID;
- procedure status;
- organizational scope;
- authorized role or group context.

A person search result must not become a universal profile joining membership, finance, Citizen Office, legal, communication and voting identities.

## FIR-SEARCH-003 — Search for Documents and Information

**Status:** approved  
**Priority:** high  
**Domain:** documents / search / publication  
**Target:** PACK-11 + PACK-12 + PACK-13 + frontend packages

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12 supplies the index policy that decides what may be indexed at
all, the classification→tier mapping that decides what a query may
surface, and `PublicationRenditionRef` as the only path by which a
certified result reaches a reader. The governed document records and
publication renditions themselves remain PACK-11's and PACK-04's.

Document search must use governed search projections linked to authoritative document records or approved publication renditions.

Searchable fields must be explicitly allowed by:

- canonical classification;
- record class;
- document access profile;
- publication state;
- organization scope;
- retention and deletion state;
- domain-specific index policy.

Historical versions, correction records and supersession history may be shown only where the user has corresponding access.

Highly confidential and absolute-exclusion data must not enter general indexes, including:

- ballot content and voting linkage data;
- whistleblower identity and protected submissions;
- credentials, tokens and keys;
- sealed evidence;
- protected identity evidence;
- raw privileged-session secrets;
- records excluded by authoritative domain policy.

A final certified voting result may be discoverable only as an approved authoritative publication, never as raw tally material or administrative search data.

## FIR-SUPPORT-001 — Layered User Assistance Model

**Status:** approved  
**Priority:** high  
**Domain:** frontend / communications / support / AI accountability  
**Target:** FRONT-02 + Communications package + PACK-18

User assistance must be layered and must not depend on a single chatbot.

Required assistance levels:

1. contextual help on the current screen;
2. versioned help center and instructions;
3. case-specific secure question linked to the relevant procedure;
4. human support through secure message, callback, video or appointment;
5. technical support with minimum necessary access;
6. AI assistance with explicit advisory status;
7. complaint, review and appeal paths.

Contextual assistance must explain:

- current status;
- required action;
- missing information;
- deadline;
- consequence of inaction;
- next procedural step;
- available human contact or remedy.

Material outcomes of calls or appointments must be recorded in the governed case history without allowing support personnel to impersonate the user or silently alter submissions.

## FIR-SUPPORT-002 — AI Assistance Boundary

**Status:** approved  
**Priority:** high  
**Domain:** AI accountability / user assistance  
**Target:** PACK-18 and relevant frontend packages

AI may:

- explain interface elements;
- locate the correct section;
- summarize rules in plain language;
- check form completeness;
- identify missing fields;
- propose draft structure;
- explain status and next steps;
- locate permitted public or internal materials;
- prepare a draft message for user approval.

AI must not:

- make final membership, legal, political or eligibility decisions;
- vote for a user;
- alter or submit user content without explicit confirmation;
- hide or delete initiatives;
- impersonate staff;
- guarantee legal correctness;
- access data outside the current authorized context;
- trap the user in an automated support path without access to a human remedy.

Every legally or procedurally consequential action must remain explicitly confirmed by the user or decided by the competent human authority.

## FIR-SUPPORT-003 — Accessible Form Assistance

**Status:** approved  
**Priority:** high  
**Domain:** accessibility / frontend  
**Target:** all frontend packages

Forms must provide a transparent sequence:

```text
draft
→ completeness check
→ understandable findings
→ user correction
→ preview
→ explicit confirmation
→ submission
```

The interface must distinguish:

- mandatory field;
- recommendation;
- warning;
- blocking error;
- legally significant confirmation.

AI recommendations must never be presented as mandatory legal requirements unless the requirement is independently defined by authoritative policy.

Assistance must support keyboard navigation, screen readers, clear focus, zoom, sufficient contrast, text explanations, plain language and an alternative channel where a digital-only path would exclude the user.

## FIR-METRIC-001 — Membership and User Counts

**Status:** approved  
**Priority:** high  
**Domain:** membership / analytics / transparency / disclosure control  
**Target:** FRONT-02 + transparency/publication + PACK-12/13

The system must distinguish membership counts from account and user counts.

Separate metrics may include:

- applicants;
- active memberships;
- suspended memberships;
- former memberships;
- registered accounts;
- active member accounts;
- Citizen Office users;
- privileged users;
- eligible participants;
- group or assembly participants.

A generic metric labelled only `users` must not be shown without an explicit definition.

### Member-facing visibility

An ordinary member may see policy-approved aggregates such as:

- total members in their organization;
- participants in an accessible working group;
- registrations for an accessible assembly;
- published support counts for an initiative;
- published membership development.

Member-facing counts must not provide a hidden full membership directory.

### Public visibility

Public membership statistics may include:

- total party membership;
- approved Land/Kreis aggregates;
- time-series development;
- aggregated entries and departures.

Public values require:

- approved publication workflow;
- authoritative metric definition;
- version and reporting period;
- statistical disclosure control;
- suppression or aggregation of small cohorts.

### Administrative visibility

Administrative users may see only metrics required by their function and organizational scope.

Examples:

- membership administration: active, pending and suspended records;
- finance: contribution and arrears aggregates;
- election administration: eligible participant counts;
- system administration: technical account/service metrics without automatic access to membership content;
- security administration: security metrics without automatic access to the member registry.

No count may reveal ballot status, intermediate tally, whistleblower cases, protected legal matters or other sensitive small cohorts.

## FIR-METRIC-002 — Count, Facet and Small-Cohort Disclosure Controls

**Status:** approved  
**Priority:** critical  
**Domain:** statistical disclosure control / search / publication  
**Target:** PACK-12 + PACK-13

**PACK-12 foundation provided — this entry is NOT implemented.**

PACK-12's `disclosure.py` supplies the rule engine: a cohort policy that
refuses fewer than two active rule families, and four evaluators — cohort
threshold, complement protection, differencing across a requester's
recent query digests, and a bounded cumulative-release check. The
cumulative model is the resolution of `OD-P12-08`: a policy window, a
policy limit, and a release history that must be _available_, failing
closed when it is not. A per-release-class cohort policy may make the
threshold stricter and never weaker than the repository-wide floor.

It supplies no analytics engine, no dashboard and no production release
history store. Remaining: PACK-13's release-history persistence and the
publication surfaces that would consume these decisions.

Counts, facets, dashboards and published aggregates must be generated only from the already authorized and releasable data subset.

The system must prevent inference through:

- small groups;
- neighbouring cohorts;
- totals and subtraction;
- repeated queries;
- differential queries;
- overlapping releases;
- time-series changes;
- cross-scope comparison.

Thresholds must not be the only protection. Release history and cumulative disclosure risk must be considered.

---

# 25. Implementation placement summary for Section 24

The entries in Section 24 are cross-package requirements.

Primary placement:

- applicant/member workspace: FRONT-02 and membership domain;
- identity, sessions and credentials: PACK-14;
- Voting Client handoff and unlinkability: PACK-15/16;
- search, count protection and disclosure control: PACK-12 with production persistence in PACK-13;
- governed documents and versions: PACK-11;
- communications and official correspondence: future communications package;
- AI assistance and accountability: PACK-18;
- public aggregates and transparency: future publication/transparency packages.

No entry in this section is considered implemented merely by inclusion in this register.

# EPD² Master Future Implementation Register

**Status:** Living master register
**Maintenance copy:** V26 — BSI CC PP-0121 certification-readiness governance refinement (2026-08-30), layered losslessly on the V25 canonical reconciliation. V25 lineage and all existing FIRs remain preserved; V26 adds/refines only `FIR-VOTE-BSI-001` and its governed certification-readiness references.
**Repository filename remains canonical and unversioned:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`.

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

## 1.4.1 Cumulative register freshness gate — added 2026-08-09

Starting with PACK-25, preservation of this file is not sufficient: the
canonical register must also be **current**.

A cumulative candidate must fail repository governance checks when any of
the following is true:

- `FIR-BASE-001` does not identify the latest accepted cumulative baseline;
- a completed or accepted PACK in the repository lineage has no corresponding
  round record or explicit historical catch-up record in this file;
- a PACK task does not list FIR IDs implemented, deferred, intentionally
  unchanged, and newly created;
- a newer cumulative archive carries an older copy of this register without a
  governed explanation;
- another standalone future-implementation register is introduced.

The repository check should validate at least the current repository version,
the latest PACK number represented by the register, and the baseline pointer.
A stale register is a governance defect, not a documentation-only warning.

## 1.39 Round record — SEC-01 pre-pilot runtime security closure (repository 0.42.0)

SEC-01 is an implementation round, not a business PACK. It hardens the
reachable non-voting runtime surface that PROD-02 C1 created: Argon2id
password verification with in-place legacy migration, PostgreSQL-backed
abuse control, a centralized response security header layer with a
ten-directive CSP, a trusted-proxy boundary, request limits, durable
security-event evidence, and a runnable dependency / SAST / secret /
SBOM scanning pipeline. No bounded context was added, no business scope
expanded, no architecture reopened, and WS-03 / PB01 / TFCAR / PRDCI
were not touched. PACK-36 is not begun.

FIR IDs implemented: none.
FIR IDs deferred: none.
FIR IDs intentionally left unchanged: all. SEC-01 changed no FIR status
and rewrote no historical entry.
New FIR IDs created: none. The round's open items are recorded in
`docs/packs/SEC-01/SEC-01-OPEN-GAP-DELTA.csv` rather than as FIR
entries; two previously-merged items were split out of `OG-09` and one
new gap (`OG-20`) was created there, so that a partially-closed gap does
not hide the part that remains blocked.

Outcome: **B — SEC-01 PARTIAL**. Readiness is unchanged: PR-2 remains
conditionally established, and PR-2 criterion 11's external Docker smoke
must now be rerun against the SEC-01 candidate because the runtime
image's dependency set changed.

## 1.38 Round record — PROD-02 C1 transport completion (repository 0.41.0 C1)

A completion tranche of PROD-02: transport for the already-composed
account, membership and deliberation contexts, a provider-neutral
staging deployment artifact, and a real client journey over HTTP. No new
bounded context, no business scope expansion, PACK-36 not begun.

FIR IDs implemented: none.
FIR IDs deferred: none.
FIR IDs intentionally left unchanged: all.
New FIR IDs created: none. Open items remain in
`docs/packs/PROD-02/PROD-02-C1-OPEN-GAPS.md`.

## 1.37 Round record — PACK-33/PACK-06/PACK-02 productization (PROD-02, repository 0.41.0)

PROD-02 is an implementation round, not a business PACK. It composes
`account-service`, `membership-service` and `deliberation-service` onto
the PROD-01 runtime spine beside `citizen-office-routing-service`.
PACK-36 is not begun.

FIR IDs implemented: none.
FIR IDs deferred: none.
FIR IDs intentionally left unchanged: all. PROD-02 changed no FIR status
and rewrote no historical entry.
New FIR IDs created: none. The round's open items are recorded in
`docs/packs/PROD-02/PROD-02-OPEN-GAPS.md` rather than as FIR entries.

## 1.36 Round record — PACK-33 productization (PROD-01, repository 0.40.0)

PROD-01 is an implementation round, not a business PACK. It adds a
production runtime spine (`packages/python/epd2-runtime`) and binds
`citizen-office-routing-service` (PACK-33) to it. PACK-36 is not begun.

FIR IDs implemented: none.
FIR IDs deferred: none.
FIR IDs intentionally left unchanged: all. PROD-01 changed no FIR status
and rewrote no historical entry.
New FIR IDs created: none. The round's open items are recorded in
`docs/packs/PROD-01/PROD-01-OPEN-GAPS.md` (OG-01 … OG-17) rather than as
FIR entries, so that a productization gap is not confused with a design
obligation.

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

**New FIR IDs created by implementation discovery:** none.

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

## 1.9 Documentation-only register update — Canonical Forms (2026-07-30)

This is a documentation-only register update discovered after PACK-13's
implementation candidate and external CI run. It does not extend PACK-13's
implementation scope and it is not evidence that a forms framework exists.

**New FIR IDs created:** `FIR-FORM-001` through `FIR-FORM-005`, all with
status `approved`. Together they establish the future cross-cutting layer
for canonical form definitions, domain form inventories, governed German
content, submissions and official multi-channel renditions.

**FIR IDs implemented:** none. The five entries remain approved future
obligations. Their inclusion in this register does not make any form,
submission workflow, official text, PDF rendition or frontend surface
implemented.

**FIR IDs intentionally left unchanged:** every pre-existing entry.
No identifier was reused, no status was downgraded and no second register
was created.

The updated register contained in the next cumulative FINAL PASS archive
becomes the authoritative register for PACK-14 and every subsequent PACK.
Later PACKs must preserve these entries unless a governed change updates
their status or scope.

---

## 1.10 Documentation-only register update — Cross-cutting procedural layers (2026-07-30)

This is a documentation-only register update identified before PACK-13 FINAL
PASS. It does not extend PACK-13 implementation scope and it does not alter
the external CI result for the PACK-13 implementation candidate.

**New FIR IDs created:** `FIR-RULE-001`, `FIR-REF-001`,
`FIR-DELIVERY-001`, `FIR-TRUST-001`, `FIR-REPRESENT-001`,
`FIR-INCLUSION-001`, `FIR-QUALITY-001`, `FIR-CONFIG-001`,
`FIR-IMPORT-001` and `FIR-SERVICE-001`, all with status `approved`.

**FIR IDs implemented:** none. These entries remain future obligations.
They establish cross-cutting requirements for governed procedural rules,
reference data, official delivery evidence, signatures and trusted
timestamps, representation, alternative-channel procedures, reconciliation,
operational configuration, legacy import and a service-responsibility
catalogue.

This update must be preserved in the PACK-13 FINAL PASS archive and becomes
part of the authoritative cumulative baseline for PACK-14 and subsequent
PACKs. A later PACK may change an entry's status or scope only through a
governed register update that preserves history.

## 1.11 Documentation-only register update — Frontend design and interaction governance (2026-07-30)

This documentation-only update preserves the established minimalist EPD²
visual direction and adds cross-cutting frontend governance requirements
before PACK-13 FINAL PASS.

**New FIR IDs created:** `FIR-UX-003` through `FIR-UX-010`, all with status
`approved`.

**FIR IDs implemented:** none. Existing FRONT-00/FRONT-01 assets and pages
provide the current visual baseline, but they do not make the future design
system, navigation governance or workspace interaction patterns complete.

The updated register must be preserved in the PACK-13 FINAL PASS archive and
carried into PACK-14 and subsequent PACKs.

## 1.12 Documentation-only register update — Exact frontend baseline continuity (2026-07-30)

This update clarifies that the approved FRONT-00 and FRONT-01 implementation,
including the existing public pages, shared components, actual design tokens,
layouts and accepted reference screenshots, is the authoritative visual
baseline for future frontend work.

“Minimalist EPD² design” must not be interpreted as permission to create a
new unrelated minimalist design from scratch.

No FIR is implemented by this clarification. It remains a future frontend
governance obligation and must be carried into PACK-14 and subsequent
FRONT-PACKs.

## 1.13 Round record — PACK-13 FINAL PASS (2026-07-30)

**PACK-13 EXTERNAL CI PASS. PACK-13 FINAL PASS ARCHIVE PREPARED.**
`REPOSITORY_VERSION` `0.13.0`; `CANON_VERSION` `0.8.0`.
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

A packaging round, not an implementation round. No service module, test,
reason code, ADR, contract, frontend file, route or visual snapshot was
changed, and neither the repository version nor the canon version moved.

**FIR IDs implemented:** `FIR-ROADMAP-003`, moved from `scheduled` to
**`implemented in reference form`** on the strength of an external GitHub
Actions run that passed every stage — 800/800 repository paths, no
forbidden paths, version consistency, Ruff format over 520 files, Prettier,
Ruff lint, ESLint, mypy across all 23 groups, both TypeScript typechecks,
4625 Python tests passed with 4 skipped, 34 Node tests, 16 frontend unit
and render tests, a successful Next.js production build, and 108 browser,
accessibility and visual tests. Evidence:
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md`,
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` and
`docs/handover/PACK-13-FINAL-PASS-REPORT.md`.

**`implemented in reference form`, not `implemented` outright.** The
distinction is the whole content of the status. The contracts, the gates
and the refusals are real and externally verified; the production data
plane is not deployed. Every storage adapter in
`services/data-plane-service` is in memory, and the criteria whose evidence
is a database grant inventory, a live catalog snapshot, a role inventory or
an egress-control review remain `deferred to production infrastructure` in
the acceptance matrix's implementation-status appendix. A green pipeline
verifies the tree; it does not deploy a database.

**FIR IDs whose foundation-only status is unchanged by this round:** all
nine recorded in §1.8. A green pipeline does not implement a requirement
the round never set out to implement, and none is promoted here.

**FIR IDs intentionally left unchanged:** every other entry, including
`FIR-INV-002` … `FIR-INV-005`, `FIR-PROG-003`, all five `FIR-FORM-*`, all
ten cross-cutting entries of §1.10 and all eight `FIR-UX-003` … `FIR-UX-010`
frontend-governance entries. Every one of them remains `approved` and
**none is implemented by PACK-13**.

**New FIR IDs created by implementation discovery:** none.

**Order of events, stated plainly because it matters for what the PASS
covers.** The external GitHub Actions run verified the **implementation
candidate**. The register updates recorded in §1.9 through §1.12 —
`FIR-FORM-001` … `FIR-FORM-005`, the ten cross-cutting procedural entries,
`FIR-UX-003` … `FIR-UX-010` and the frontend-baseline-continuity
clarification — were written **after** that run and are therefore **not
covered by it**. They are documentation-only, they change no code, test, CI
configuration, ADR, canon or version, and they were re-verified here only
by the deterministic repository and formatting checks this environment can
run. `docs/handover/PACK-13-FINAL-PASS-REPORT.md` §11 states that split in
full.

**Production infrastructure and later-pack items remain future.** No
production PostgreSQL, cloud database, real broker, external
schema-registry product, production search engine, production IAM,
multi-region topology, backup or restore capability is deployed or claimed.
Identity (PACK-14), eligibility/credential/voting/tally (PACK-15/16) and
backup recovery (PACK-17) remain future in exactly the state they were.

**Register updates only.** No entry was deleted, no identifier reused, no
status downgraded, and no second register was created. This file is the
consolidated register supplied for this round, adopted at its canonical
path with only the four status changes this FINAL PASS round is itself
required to make: this round record, the `FIR-BASE-001` baseline pointer,
`FIR-ROADMAP-003`'s status, and section 21's implementation summary. The
candidate round record in §1.8 is preserved unmodified — the round genuinely
was a candidate at the time, and rewriting that history to read as though it
had always been FINAL PASS would destroy the audit trail this register
exists to keep.

## 1.14 Documentation-only register update — Page specification and screen content governance (2026-07-30)

This update adds `FIR-UX-011 — Page Specification and Screen Content
Governance`.

It establishes that every user-facing domain must define a complete page and
screen catalogue before frontend implementation, including page order,
navigation sequence, content blocks, actions, states, exact governed content
references and acceptance evidence.

No implementation status changes. No code, test, CI, repository version or
canon version changes are implied.

_Numbering note: supplied as §1.13 in the standalone V5 register. It is
recorded here as §1.14 because §1.13 in this cumulative register is already
the PACK-13 FINAL PASS round record, which predates it. No word of its
content changed, and nothing existing was renumbered._

## 1.15 Round record — PACK-14 implementation candidate (2026-07-30)

**Round:** PACK-14 — Identity, Authentication & Account Security,
implementation candidate. **NOT PASS.** External GitHub Actions has not
run against this round.

**Repository version:** `0.13.0` → `0.14.0`.
**Canon version:** unchanged at `0.8.0` — the round amends no canon.

**What was built.** `services/identity-service` gains, in place, the six
bounded contexts specification §4.1 assigns to it: Account Registry,
Credential Registry, Authentication, Session Security, Recovery
coordination and Identity-Proofing references — as internally separated
modules with separate storage boundaries. 34 new source modules, 8 new
test modules, 288 service tests plus 28 repository-level tests.
`contracts/reason-codes/pack-14.yml` registers 213 entries. 59 event
types use PACK-13's canonical envelope unchanged.

**Correction round, before external CI, same repository version.** The
first candidate archive was reviewed and three findings were returned and
fixed. (1) The persistence was metadata rather than persistence: ten real
SQL migration artefacts, a transactional checksum-guarded migration
runner, eleven durable adapters, a transaction boundary, an
optimistic-concurrency guard and a safe serializer were added, and the
in-memory adapters were demoted to explicit test adapters that are no
longer any runtime's default binding. It is a **reference** persistence
path on SQLite through the standard library: **no production database is
deployed and no production durability is claimed.** (2) The
breached-password default was permissive and now **refuses**: no password
may be enrolled or replaced without a bound checker, and the one governed
exception permits authentication against an already stored hash only.
(3) `api.py` was an endpoint catalogue and a runnable, transport-agnostic
reference boundary was added, routing 12 of the 42 catalogued
operations. No functional scope was expanded, no frontend was built, no
dependency was added, no CI gate was weakened, no existing test was
removed, and neither the repository nor the canon version changed.

**FIR IDs implemented:** none. `FIR-ROADMAP-004` moves from `approved` to
`candidate` — not to `implemented` and not to `implemented in reference
form`, because no external pipeline has verified this round.

**FIR IDs whose status is otherwise unchanged:** every other entry in this
register. In particular `FIR-UX-011` stays **future**: no FRONT-PACK was
built, no page catalogue or screen-state matrix exists, and the identity
journey is explicitly not claimed as designed. `FIR-TRUST-001`,
`FIR-REPRESENT-001` and `FIR-INCLUSION-001` stay future.
`FIR-CONFIG-001` gains a consumer — PACK-14's governed timeout and
freshness defaults — but is not itself implemented by this round.

**What remains deferred, unchanged.** Production IAM, real eID, real
email and SMS delivery, production HSM or KMS, the Voting Client, voting
credential issuance, ballots, tallies, a full legal electronic signature,
and the complete Account & Security FRONT-PACK.

**`OD-P14-07` remains open**, pending legal confirmation of retention
durations. It does not block the reference implementation: provisional
schedules exist, every destructive disposition refuses while the schedule
is unconfirmed, deletion under a legal hold refuses, and an unknown hold
state fails closed.

**No PACK-13 record was reopened, reverted or rewritten by this round**,
and no future obligation was removed. The four changes this round makes
to this register are: this round record, the `FIR-BASE-001` candidate
pointer, `FIR-ROADMAP-004`'s status, and section 21's implementation
summary line. The correction round adds no fifth change of kind: it
updates the text of those same four places and the candidate archive
name, and it moves no entry's status.

## 1.16 Round record — PACK-14 FINAL PASS (2026-07-30)

**Round:** PACK-14 — Identity, Authentication & Account Security, **FINAL
PASS**. External GitHub Actions has run against the candidate tree and
**passed every stage**.

**Repository version:** unchanged at `0.14.0`.
**Canon version:** unchanged at `0.8.0`.

**This is a packaging round.** No implementation was rebuilt. No
`identity-service` module, migration artefact, test, reason code, ADR,
contract, frontend file, route, visual snapshot or CI definition changed.
The archive is the externally verified tree plus the status, register and
handover documents that close the round.

**External CI results, read from the committed transcript**
(`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`):

| Stage                            | Result                        |
| -------------------------------- | ----------------------------- |
| Repository path manifest         | PASS — 867 / 867              |
| Forbidden paths                  | PASS — none present           |
| Version consistency              | PASS                          |
| Ruff format                      | PASS — 566 files              |
| Prettier                         | PASS                          |
| Ruff lint                        | PASS                          |
| ESLint                           | PASS                          |
| mypy, 23 targets                 | PASS — no issues in any group |
| TypeScript typecheck, 2 packages | PASS                          |
| Python test suite                | PASS — 4905 passed, 4 skipped |
| TypeScript package tests         | PASS — 3 passed               |
| Node tests                       | PASS — 34 passed              |
| Frontend unit / render tests     | PASS — 16 passed              |
| Next.js production build         | PASS — 46 / 46 static pages   |
| Browser / visual / accessibility | PASS — 108 passed             |

Evidence archive SHA-256:
`c80b2f1a05f97423c782f7b0e42f78502a802bd47432a43caee207321dff515d`;
the verification ZIP it contains:
`df6981227d80f4a01d406bcf882f7dea3cfd31400d3c262eb93009c1eb1b6054`.
Both were recomputed in the environment that assembled this archive.

**FIR IDs implemented by this round: none.** `FIR-ROADMAP-004` moves from
`candidate` to `implemented in reference form` — not to `implemented`,
because no provider is bound and nothing is deployed.

**FIR IDs whose status is otherwise unchanged:** every other entry in this
register. 141 FIR entries before this round and 141 after. In particular
`FIR-UX-011` stays **future**: no FRONT-PACK was built, no page catalogue
or screen-state matrix exists, and the identity journey is explicitly not
claimed as designed. `FIR-TRUST-001`, `FIR-REPRESENT-001` and
`FIR-INCLUSION-001` stay future. `FIR-CONFIG-001` remains a consumer
relationship, not an implementation. **No future obligation was removed
and no entry was rolled back.**

**`OD-P14-07` remains open**, pending legal confirmation of retention
durations. The PASS does not close it: every `duration_confirmed` flag is
still `False`, every destructive disposition still refuses, deletion under
a legal hold still refuses and an unknown hold state still fails closed.

**One factual correction.** The PACK-14 candidate round's entry in
`FIR-BASE-001` described ADR-079 — ADR-088 as "accepted in the
specification round". `docs/handover/PACK-14-SPEC-ADR-REPORT.md` §2 records
them as `proposed`, and the ADR files themselves say `proposed`. The
register now says `proposed` too. No ADR file was edited: their governance
status is for the body that owns them, and a green pipeline does not move
it — the same treatment ADR-061 — ADR-068 received through PACK-11's and
PACK-12's FINAL PASS rounds.

**The three changes this round makes to this register** are: this round
record, `FIR-BASE-001`'s baseline pointer (PACK-14 becomes the
authoritative cumulative PASS baseline; PACK-13 becomes the previous one),
and `FIR-ROADMAP-004`'s status. Section 21's implementation summary is
updated to move PACK-14 out of the "candidate, not yet externally
verified" subsection, which that subsection existed to hold.

## 1.17 Documentation-only register update — Open-source licensing and reuse governance (2026-07-31)

This documentation-only update selects the **European Union Public Licence
Version 1.2 (`EUPL-1.2`)** as the intended project licence for original EPD²
software, subject to final legal review before public release.

The choice is fixed to Version 1.2 rather than “or later”. Adoption of any
later EUPL version requires a separate governed decision.

**New FIR IDs created:** `FIR-OSS-001` through `FIR-OSS-006`, all with status
`approved`.

No implementation status changes. No code, test, CI, repository version or
canon version changes are implied by this register update.

## 1.18 Round record — PACK-15 implementation candidate (2026-07-31)

**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential
Separation, **implementation candidate**.

**Repository version:** `0.14.0` -> `0.15.0`.
**Canon version:** unchanged at `0.8.0`. PACK-15 makes no canon amendment,
which its own canon assessment records: no canon entity, no canon status
value and no canon event was added. `canon-version.json` changed only its
non-canonical bookkeeping - `repository_compatibility` widened to
`<0.16.0`.

**What was built.** The separation between knowing who someone is and
knowing that a vote was cast, implemented rather than specified. The
design turns on ADR-093's structural cut: the spent-nonce record is a
**set** with three columns and no value column, so no store, log, event,
trace, backup or export contains both an assertion reference and a
credential reference for the same participation. Seven separate SQLite
database files - one per trust boundary - make a cross-boundary foreign
key inexpressible rather than merely unwritten. Exactly-once is enforced
on both sides differently, each by an INSERT that is itself the check.
Twenty-two versioned API endpoints sit over a shared contract layer in
`epd2-core`. Ten roles and eight structural separation rules are validated
at import time.

**Deliberately not a new workspace member.** PACK-15 extends
`eligibility-service`, `credential-service`, `governance-service` and
`audit-core` in place. A new member would have required regenerating
`uv.lock`, which CI installs `--frozen`; in an environment where the
package registries return HTTP 403 that could not have been done honestly.
**Neither lock file was modified.**

**Verification, stated exactly.**

| Check                                                | Result                                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `pytest`, full repository                            | PASS - 5335 passed, 5 skipped                                                        |
| `mypy`, every Python group of the `typecheck` target | PASS                                                                                 |
| `ruff check` / `ruff format --check`                 | PASS                                                                                 |
| `scripts/check_repository.py`                        | PASS - 983 paths                                                                     |
| `scripts/check_forbidden_files.py`                   | PASS                                                                                 |
| `scripts/verify_versions.py`                         | PASS                                                                                 |
| `scripts/check_canon_0_8_0.py`                       | PASS - 18 checks                                                                     |
| `uv sync --frozen`                                   | NOT EXECUTED - ENVIRONMENT BLOCKED (PyPI HTTP 403)                                   |
| Every npm-dependent check                            | NOT EXECUTED - ENVIRONMENT BLOCKED (registry HTTP 403; `node_modules` uninstallable) |
| Property-based tests                                 | NOT EXECUTED - ENVIRONMENT BLOCKED (`hypothesis` unavailable)                        |
| Visual regression                                    | NOT APPLICABLE - no PACK-15 baselines were added                                     |

This corrects the two preceding PACK-15 rounds, which recorded that no
Python tooling could run at all. `pytest`, `mypy` and `ruff` are present
in this environment and were really executed - but from outside the
project environment, so the versions they resolve to are not the versions
`uv.lock` pins. **External CI remains the authoritative run.** No CI check
was weakened and no test result was fabricated.

**FIR IDs implemented by this round: none.** `FIR-ROADMAP-005` moves from
`approved` to `candidate` - not to `implemented in reference form`, which
is what PACK-14 reached only after external CI passed. No FIR entry may
move on the strength of a locally verified candidate whose entire frontend
has never been executed.

**FIR IDs whose status is otherwise unchanged:** every other entry in this
register, including all six `FIR-OSS-001` through `FIR-OSS-006` and
`FIR-UX-011`, which stays **future**: no FRONT-PACK was built, no page
catalogue or screen-state matrix exists, and the five PACK-15 frontend
files are unverified source rather than a designed journey.
`FIR-INV-002` (identity / ballot unlinkability) is **partially addressed
and stays future**: PACK-15 closes the identity-to-credential half, the
credential-to-ballot half is PACK-16's, and neither half alone closes the
invariant. **No future obligation was removed and no entry was rolled
back.**

**One defect found and closed while assembling the evidence.** The
assurance flag `required_assurance_satisfied` was carried across the trust
boundary, persisted, and never read - a fail-open in a control the
specification marks fail-closed. It was found by building the traceability
matrix, which is the argument for building one, and is now refused with
`ELIGIBILITY_ASSURANCE_INSUFFICIENT`. Three further defects found by
adversarial review of the API layer are recorded in
`docs/handover/PACK-15-IMPLEMENTATION-REPORT.md` section 5.

**One numbering correction.** The open-source licensing update above was
filed as `1.15`, a number `1.15 Round record — PACK-14 implementation
candidate` already held; it is renumbered `1.17`. No content, no entry and
no status changed - two sections with one number is a filing error, and
leaving it would have made this round's record the third `1.16`.

**The four changes this round makes to this register** are: this round
record, that renumbering, `FIR-BASE-001`'s candidate pointer, and
`FIR-ROADMAP-005`'s status. Nothing else in this file was edited.

## 1.19 Round record — PACK-15 FINAL PASS (2026-07-31)

**Round:** PACK-15 — Voting Trust Boundary, Eligibility & Credential
Separation, **FINAL PASS**. External GitHub Actions has run against the
cleaned candidate tree and **passed every stage**.

**Repository version:** unchanged at `0.15.0`.
**Canon version:** unchanged at `0.8.0`.

**This is a packaging round.** No implementation was rebuilt. No service
module, migration artefact, API catalogue, event schema, reason code,
test, contract, frontend file or CI definition changed. The archive is
the externally verified tree plus the status, register and handover
documents that close the round.

**External CI results, read from the committed run log:**

| Stage                            | Result                        |
| -------------------------------- | ----------------------------- |
| Required paths                   | PASS — 983 / 983              |
| Forbidden paths                  | PASS                          |
| Version consistency              | PASS                          |
| Ruff format                      | PASS — 436 files              |
| Prettier                         | PASS                          |
| Ruff lint                        | PASS                          |
| ESLint                           | PASS                          |
| mypy                             | PASS                          |
| Python tests                     | PASS — 5343 passed, 4 skipped |
| TypeScript package tests         | PASS — 3 passed               |
| Node tests                       | PASS — 41 passed              |
| Frontend tests                   | PASS — 23 passed              |
| Next.js production build         | PASS                          |
| Static pages                     | 48 / 48                       |
| Browser / visual / accessibility | PASS — 135 passed             |

Verification artifact SHA-256:
`e8fd5b2a14e61be95be49afd461467a9ddbaab8f5dc70db68a9ab5f0bb9cd1b4`;
the internal verification ZIP it contains:
`7ea70c5b9ba3c7350e1d0831148c2be560512e17f78392031c1b0e5e7ea3df8c`.
Both were recomputed in the environment that assembled this archive and
both matched.

**A hygiene correction preceded this run, and it is why the run was
repeated.** An earlier external run passed against a tree that also
contained `epd2-civic-os/`, a complete stale copy of the repository at
`REPOSITORY_VERSION 0.6.0` / `CANON_VERSION 0.6.0`. That run reported
`Ruff format: 609 files`, which is 436 root files plus the nested copy's 173. The directory was removed — PACK-08, PACK-10, PACK-11 and PACK-14
had each already recommended it — and the tree was re-verified from
scratch. This run reports **436 files**. **Every verification artifact
for a tree containing that directory is superseded and is not FINAL PASS
evidence.** The archive shipped here was compared file by file against
the newly verified tree: 1171 source files, zero differences.

**FIR IDs implemented by this round: none.** `FIR-ROADMAP-005` moves from
`candidate` to `implemented in reference form` — not to `implemented`,
because no provider is bound and nothing is deployed.

**FIR IDs whose status is otherwise unchanged:** every other entry in this
register, including all six `FIR-OSS-001` through `FIR-OSS-006` and
`FIR-UX-011`, which stays **future**: no FRONT-PACK was built, no page
catalogue or screen-state matrix exists. `FIR-ROADMAP-006` (PACK-16),
`FIR-ROADMAP-007` and `FIR-ROADMAP-008` stay future and unchanged.
`FIR-INV-002` remains **partially addressed and future**: PACK-15 closes
the identity-to-credential half, the credential-to-ballot half is
PACK-16's, and neither half alone closes the invariant. **No future
obligation was removed and no entry was rolled back.**

**No production-readiness and no legal-activation claim is made by this
round.** The pipeline verifies the repository; it binds no provider and
deploys nothing. Key custody is unbound and refuses, there is no
transport layer, and SQLite remains the reference persistence.

**The four changes this round makes to this register** are: this round
record, `FIR-BASE-001`'s baseline pointer (PACK-15 becomes the
authoritative cumulative PASS baseline; PACK-14 becomes the previous
one), `FIR-ROADMAP-005`'s status, and section 21's implementation summary,
where PACK-15 joins the externally verified packs and the reference-
implementation qualifier is extended to cover it.

## 1.20 Round record — PACK-16A specification and ADR (2026-08-01)

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model
Selection. **Specification and ADR only. No code. Not implemented. Not an
implementation candidate. Not a PASS.**

**Repository version:** unchanged at `0.15.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip`,
SHA-256 `38697c0a0bca9d211bf9f44ec5c2f7b475d86bd38eb1ccc10bc9521c3f2f087a`,
1172 files, one repository root, one `uv.lock`, one `package-lock.json`,
one canonical Master Register, no duplicate archive paths and no nested
ZIP files. The baseline was read in full — specification, matrices, threat
model, catalogues, `ADR-088` … `ADR-098`, the canonical domain and event
model and this register — rather than quoted from a handover.

**What this round did.** Nine mature verifiable-voting protocol families
were assessed against primary sources — official specifications,
peer-reviewed papers, official caveat documents, official repositories, a
binding regulatory ordinance, a constitutional judgment, current national
technical guidance and party law. Fifty-six evidence entries were recorded
with document, version, date, section, URL and a classification as
protocol property, implementation property, legal or inference;
unverifiable items were marked as such and support no conclusion. One
family was selected, bounded into one profile, and recorded as a
**proposed** ADR.

```text
SELECTED   homomorphic exponential-ElGamal ballots with threshold
           distributed key generation and decryption, NIZK well-formedness
           proofs and Benaloh cast-or-challenge, in the lineage of the
           ElectionGuard Design Specification 2.1.0
PROFILE    EPD2-HOM-1 — cardinal ballots, homomorphic tally
DEFERRED   EPD2-MIX-1 — ordinal ballots, mixnet tally; defined, not
           selected, prohibited pending research
REVOTING   none — explicitly decided, not deferred
ADR        ADR-099, status `proposed`
```

**Documents added.** Twenty-two documents under `docs/packs/PACK-16/` and
`docs/adr/ADR-099-VERIFIABLE-VOTING-PROTOCOL-AND-BALLOT-MODEL.md`. Nothing
else in the repository was created, modified or deleted apart from this
register entry and `FIR-ROADMAP-006`'s cross-reference note.

**FIR IDs implemented by this round:** none, and none may be. **FIR IDs
deferred:** `FIR-ROADMAP-007` (network and infrastructure metadata,
backup topology, resilience, incident readiness, independent-verification
operations); `FIR-ASM-006`; `FIR-ASM-007`; `FIR-SEC-001`; `FIR-SEC-002`;
`FIR-TRUST-001`; `FIR-OSS-006` (delivery); `FIR-DATA-003` (assessed).
**FIR IDs blocked pending legal assessment:** `FIR-CAND-001` — statutory
candidate nomination requires simultaneous physical presence and written
secret paper ballots under § 17 PartG in conjunction with § 21 Abs. 3 and
§ 27 Abs. 5 BWahlG and the Bundeswahlleiterin's operative guidance.
**FIR IDs intentionally left unchanged:** `FIR-ROADMAP-005`,
`FIR-ROADMAP-008`, `FIR-ROADMAP-009`, `FIR-INV-004`, `FIR-INV-010`,
`FIR-INV-013`, `FIR-ROLE-004`, `FIR-ROLE-006`, `FIR-UX-011`,
`FIR-OSS-001` … `FIR-OSS-006`, and every entry not named in
`docs/packs/PACK-16/PACK-16A-FIR-COVERAGE-MATRIX.md`. **New FIR IDs
created by this round: none.**

`FIR-INV-002` remains **partially addressed and future**. PACK-15 closed
the identity→credential half; PACK-16A **specifies the architecture** of
the credential→ballot half and does not implement or demonstrate it.
Specification is not closure, neither half alone closes the invariant, and
the strongest residual — redemption-to-casting timing correlation — is
**reduced and bounded, not eliminated**.

`FIR-ROADMAP-006` **keeps its status `approved` and its target version
`0.16.0`.** PACK-16A performs the research and selection stage only. Ballot
casting, vote verification and tally controls remain unimplemented, and
the version bump belongs to the implementation candidate, not to a
specification stage.

**Canon.** `CANON CLARIFICATION REQUIRED`; six clarifications recorded;
**no amendment proposed**; three amendment candidates recorded for
PACK-16B/16C — a bulletin-board publication aggregate (canon 19a.1 forbids
`PublicLedgerEntry → VoteEnvelope`, and that prohibition stands), a
trustee/key-ceremony evidence aggregate, and a mirror registry.
`CANON_VERSION` unchanged at `0.8.0` and the canon files are untouched.

**No production-readiness, external-CI, FINAL PASS or legal-activation
claim is made by this round.** `PUBLIC-ELECTION ACTIVATION PROHIBITED BY
DEFAULT`. PACK-16B must not start before architectural acceptance of
PACK-16A.

**The two changes this round makes to this register** are: this round
record, and a cross-reference note under `FIR-ROADMAP-006`. No entry was
deleted, no identifier reused, no status changed, no status downgraded and
no second register created.

## 1.21 Round record — PACK-16B specification and ADR (2026-08-01)

**Round:** PACK-16B — Cryptographic Parameters, Key Ceremony and Trustee
Architecture. **Specification and ADR only. No code. No cryptographic code.
Not implemented. Not an implementation candidate. Not a PASS.**

**Repository version:** unchanged at `0.15.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-16A_VERIFIABLE_VOTING_PROTOCOL_AND_BALLOT_MODEL_SPEC_ADR_CORRECTED_CANDIDATE.zip`,
SHA-256 `14b65dae696eeb80e237fbb33a14f7bad55e8ca043672ba0fa2e86a90b011f9e`,
1195 files, one repository root, one `uv.lock`, one `package-lock.json`,
one canonical Master Register, no duplicate archive paths and no nested ZIP
files. The corrected PACK-16A candidate — the one whose acceptance matrix
and single consolidated evidence registry passed narrow correction — is the
authoritative input; no earlier PACK-16A tree was used.

**What this round did.** The pinned specification was read directly and its
parameters were **independently regenerated and confirmed byte for byte**.
Current German and international guidance — BSI TR-02102-1 (2026-01), BSI
AIS 20/31 v3.0, NIST SP 800-56A Rev 3 and the SP 800-90 series — was
assessed against the parameters from primary sources, with one sentence
recorded as **unread and unverified** rather than assumed. Thirty-two
evidence entries were recorded in a **single canonical registry** with
twelve fields each, classified as protocol, analysis, normative, governance
or EPD²-generated; four are EPD²'s own findings and are marked as such and
never presented as external corroboration.

```text
PARAMETER PROFILE   EPD2-CRYPTO-1 — the specification's fixed 4096-bit
                    finite-field parameters, adopted UNMODIFIED (Option A)
EG COMPATIBILITY    full — every conforming 2.1 verifier accepts the record
BSI ASSESSMENT      meets every figure verified first-hand; one sentence
                    UNVERIFIED and carried as a blocking obligation
GUARDIANS/QUORUM    k=3 of n=5 default; k=4 of n=7 high assurance;
                    k >= 3 always; k may never be reduced
CEREMONY            twenty phases; controlled hybrid or in person;
                    FULLY REMOTE PROHIBITED
BACKUP              per-guardian, own share, own custody, only
COMPENSATION        DOES NOT EXIST in the pinned version — factual
                    correction to PACK-16A KC-11's described mechanism;
                    the requirement itself is unchanged
BREAK-GLASS         none. PRE-CLOSURE DECRYPTION PROHIBITED
ADR                 ADR-100, status `proposed`
```

**Documents added.** Twenty-nine documents under `docs/packs/PACK-16/` and
`docs/adr/ADR-100-CRYPTOGRAPHIC-PARAMETERS-KEY-CEREMONY-AND-TRUSTEE-ARCHITECTURE.md`.
Nothing else in the repository was created, modified or deleted apart from
this register entry and `FIR-ROADMAP-006`'s cross-reference note. No source
file, test, migration, API or event implementation, frontend file, CI
workflow, `uv.lock`, `package-lock.json` or dependency was touched.

**FIR IDs implemented by this round:** none, and none may be. **FIR IDs
deferred:** `FIR-ROADMAP-007` (ceremony resilience, incident readiness,
archive re-verification, independent-verification operations);
`FIR-SEC-001` and `FIR-SEC-002` (runbooks and recovery testing);
`FIR-TRUST-001` (the signature and timestamp framework itself);
`FIR-OSS-006` (delivery). **FIR IDs assessed:** `FIR-DATA-003` — a legal
hold may not extend the life of secret material, compel a guardian or
produce a decryption. **FIR IDs intentionally left unchanged:**
`FIR-ROADMAP-005`, `FIR-ROADMAP-008`, `FIR-ROADMAP-009`, `FIR-INV-011`,
`FIR-ROLE-004`, `FIR-ROLE-006`, `FIR-UX-011`, `FIR-OSS-001` …
`FIR-OSS-006`, `FIR-CAND-001`, `FIR-ASM-006`, `FIR-ASM-007`,
`FIR-PROG-001`, and every entry not named in
`docs/packs/PACK-16/PACK-16B-FIR-COVERAGE-MATRIX.md`. **New FIR IDs created
by this round: none. FIR statuses changed by this round: none.**

`FIR-INV-002` remains **partially addressed and future**, exactly as
PACK-15 and PACK-16A left it. This round separates guardians structurally
from eligibility, issuance and casting, and **does not advance the
invariant**: it cannot be closed without a built system to demonstrate
against.

`FIR-ROADMAP-006` **keeps its status `approved` and its target version
`0.16.0`.** PACK-16B performs the parameter, ceremony and trustee stage
only.

**Canon.** `CANON CLARIFICATION REQUIRED`; five clarifications recorded
(`CQ-P16B-01` … `CQ-P16B-05`); **no amendment proposed**; three amendment
candidates recorded (`CAM-P16B-01` … `CAM-P16B-03`). The ceremony
transcript is found **not** to be a canonical aggregate and **not** a
`PublicLedgerEntry`, and PACK-16A's `CA-02` candidate is therefore
**narrowed rather than discharged**. The `PublicLedgerEntry →
VoteEnvelope` prohibition stands untouched. `CANON_VERSION` unchanged at
`0.8.0` and the canon files are untouched.

**Open decisions.** Closed: `OD-P16A-03`, `OD-P16A-05`, and the
cryptographic boundary of `OD-P15-05` (whose construction question is
reassigned to PACK-16C). Opened: `OD-P16B-01` … `OD-P16B-06`. **Four
independent activation blocks remain open and none is closed by
assertion**, the gravest being that **no peer-reviewed security analysis of
the selected specification's key ceremony exists, in any version, and no
peer-reviewed analysis of version 2.1 exists at all** — recorded as
`blocked pending cryptographic review`, not as satisfied.

**No production-readiness, external-CI, FINAL PASS, certification or
legal-activation claim is made by this round.** `PUBLIC-ELECTION ACTIVATION
PROHIBITED BY DEFAULT`. PACK-16C must not start before architectural
acceptance of PACK-16B, and PACK-16D is not begun.

**The two changes this round makes to this register** are: this round
record, and a cross-reference note under `FIR-ROADMAP-006`. No entry was
deleted, no identifier reused, no status changed, no status downgraded and
no second register created.

## 1.36 Register recovery and cumulative catch-up — PACK-18 through PACK-24 (2026-08-09)

This record repairs a continuity defect in the living register. The canonical
file continued to be carried inside cumulative archives, but its baseline
pointer and round history stopped being updated after the PACK-15/17 era.
This catch-up **does not rewrite the contemporaneous PACK records** and does
not invent missing evidence. It records the lineage already present in the
accepted cumulative repository and makes the register usable again as the
single future-implementation source for PACK-25 and later rounds.

Current cumulative lineage represented by the repository:

| Round    | Repository version | Domain / architecture increment                                     |
| -------- | ------------------ | ------------------------------------------------------------------- |
| PACK-17D | `0.19.0`           | incident lifecycle and publication-failure response                 |
| PACK-18  | `0.20.0`           | integrated frontend workspaces, access boundaries and accessibility |
| PACK-19  | `0.21.0`           | candidacy, nomination and ballot admission                          |
| PACK-20  | `0.22.0`           | party offices, appointments, terms and mandates                     |
| PACK-21  | `0.23.0`           | assemblies, motions and minutes                                     |
| PACK-22  | `0.24.0`           | communications and official correspondence                          |
| PACK-23  | `0.25.0`           | complaints, petitions and ombuds casework                           |
| PACK-24  | `0.26.0`           | protected reporting and investigations                              |

**Latest accepted cumulative baseline:** PACK-24, repository `0.26.0`,
Canon `0.8.0`.

Accepted PACK-24 candidate SHA-256:

```text
1da174681759a9925e2d5a8dc95b04ea383ba55f62bb502e18dd6e7a6fc29cf7
```

Authoritative Windows CI for that exact corrected candidate finished
`RESULT: PASSED` with the ordinary suite at **9064 passed, 4 skipped,
15 deselected**, all **29 mypy groups** passing, frontend Node
**397/397**, Vitest **264/264**, Prettier PASS, Pack-17b suites PASS,
adversarial corpus **93/93**, comparison gate
**186 BOTH_ACCEPT / 94 BOTH_REJECT_SAME_REASON**, and seven frozen artefacts
verified unchanged.

PACK-24 was then accepted with AVH 0.1.3 integration. The AVH integration
reported no findings or ordering violations; the two remaining LIMITED
idempotency-ordering paths are inherited candidacy-service limitations,
not PACK-24 defects.

**FIR IDs implemented by this recovery record:** none. This is a register
continuity repair, not a domain implementation.

**FIR IDs whose status is changed by this recovery record:** only baseline
and roadmap status metadata needed to make the register consistent with the
accepted cumulative lineage. No substantive future requirement is silently
removed or downgraded.

**New FIR IDs created by this recovery:** `FIR-CTRL-001` and
`FIR-ROADMAP-010`, defining the mandatory Unified Control Plane closure
before Architecture Baseline 1.0 / Freeze.

**Future PACK discipline restored:** PACK-25 and every later cumulative
candidate must update this register in the same round and must fail its
repository governance checks if the register is stale.

## 1.37 Documentation-only register update — Cross-cutting operational assurance foundations (2026-08-09)

This documentation-only update was made during the PACK-25 implementation
window after the V7 register-recovery round. It does not expand PACK-25's
business-domain implementation scope and does not change the accepted PACK-24
baseline, `REPOSITORY_VERSION`, `CANON_VERSION`, or the status of any accepted
PACK.

**New FIR IDs created:**

- `FIR-CRYPTO-001` — Cryptographic Key, Secret & Trust-Anchor Lifecycle;
- `FIR-TIME-001` — Authoritative Time, Clock & Temporal Evidence;
- `FIR-OPS-001` — Privacy-Safe Observability, SLO & Operational Health;
- `FIR-REL-001` — Release, Deployment & Environment Integrity;
- `FIR-DATA-004` — Data Disposition Propagation & Derived-Copy Governance;
- `FIR-RES-001` — Capacity, Overload & Graceful Degradation;
- `FIR-LIFE-001` — Service, Contract & Provider Decommissioning;
- `FIR-TEST-001` — System-Level Failure & Adversarial Assurance.

All eight entries have status `approved`. None is implemented merely by this
register update.

These requirements close a class of system-level gaps that are not ordinary
party/business domains: key lifecycle, trustworthy time, privacy-safe
observability, source-to-deployment integrity, propagation of disposition to
derived copies, overload behaviour, controlled decommissioning, and
system-wide adversarial/failure assurance.

**FIR IDs implemented:** none.

**Existing FIR IDs intentionally left unchanged:** all pre-existing entries.
The additions refine future cross-cutting obligations without weakening or
reinterpreting existing security, privacy, voting, retention, incident,
backup, configuration, deployment, provider or Control Plane boundaries.

**Placement:** these obligations must be carried through PACK-25 and every
later cumulative PACK. Their implementation may be distributed across the
later INFRA, SEC, OPS, DATA, release-engineering and architecture-closure
workstreams. `FIR-TEST-001` must additionally be exercised in the system-wide
challenge after PACK-35 and before Architecture Baseline 1.0 / Freeze.

## 1.38 Documentation-only register update — Voting infrastructure unlinkability and legal-effect activation (2026-08-09)

This documentation-only update was made after review of the auditor structural
skeleton and the resulting independent risk analysis. It does not expand
PACK-25's procurement/vendor implementation scope, does not alter the accepted
PACK-24 baseline, and does not change `REPOSITORY_VERSION` or `CANON_VERSION`.

**New FIR IDs created:**

- `FIR-VOTE-NET-001` — Network & Infrastructure Unlinkability for Voting;
- `FIR-LEGAL-001` — Procedural Legal-Effect Activation Gate.

Both entries have status `approved`. Neither is implemented merely by this
register update.

The first closes an architectural gap between application-layer Voting Client
isolation and lower-layer infrastructure metadata such as ingress, CDN/WAF,
reverse-proxy, network and tracing data. The second formalizes the already
established distinction between technical implementation and legal/procedural
activation.

**FIR IDs implemented:** none.

**Existing FIR IDs intentionally left unchanged:** all pre-existing entries.
In particular, no voting cryptographic mechanism such as a mixnet is selected
by this update, and no legal conclusion is hard-coded for a class of online
procedures. Those remain subject to the relevant threat model, architecture
review and legally governed activation evidence.

**Placement:** both requirements must be carried through PACK-25 and every
later cumulative PACK. `FIR-VOTE-NET-001` must be included in the voting
system-wide adversarial challenge before Architecture Baseline 1.0 / Freeze.
`FIR-LEGAL-001` applies to every domain capable of producing a legally or
procedurally consequential outcome.

## 1.39 Documentation-only register update — Authority revalidation, FIR placement governance and incremental failure fixtures (2026-08-09)

This documentation-only update was made after a further omission review of the
auditor structural skeleton. It does not expand PACK-25's procurement/vendor
business scope, does not alter the accepted PACK-24 baseline, and does not
change `REPOSITORY_VERSION` or `CANON_VERSION`.

**New FIR IDs created:**

- `FIR-AUTH-001` — Consequential Commit Reauthorization & TOCTOU Protection;
- `FIR-ROADMAP-011` — FIR Ownership, Placement & Verification Map;
- `FIR-TEST-002` — Incremental Cross-Service Failure Fixtures.

All three entries have status `approved`. None is implemented merely by this
register update.

**FIR IDs implemented:** none.

**Existing FIR IDs intentionally left unchanged:** all pre-existing entries.

These additions close three specific governance gaps:

1. authority, scope, assurance and object state may change after an initial
   authorization check but before a consequential commit;
2. an approved/deferred FIR can become an orphan requirement unless a future
   owner/workstream and verification gate are explicit;
3. cross-service failure assurance must accumulate during PACK delivery rather
   than being postponed entirely until the post-PACK-35 system-wide challenge.

These requirements must be carried through PACK-25 and every later cumulative
PACK. `FIR-TEST-002` complements, but does not replace, `FIR-TEST-001`.

## 1.40 Documentation-only register update — Cross-domain identifier and correlation governance (2026-08-09)

This documentation-only update adds one critical privacy/security requirement
identified during further structural review. It does not expand PACK-25's
business-domain scope, does not alter the accepted PACK-24 baseline, and does
not change `REPOSITORY_VERSION` or `CANON_VERSION`.

**New FIR ID created:**

- `FIR-ID-001` — Cross-Domain Identifier & Correlation Governance.

**Status:** `approved`.

**FIR IDs implemented:** none.

The new requirement addresses the risk that otherwise well-isolated services
can become linkable through a stable technical identifier reused in schemas,
events, logs, traces, analytics, search indexes, exports, support tooling or
external-provider references.

The requirement must be carried through PACK-25 and every later cumulative
PACK. Repository/AVH assurance should progressively add machine-readable
checks for prohibited stable identifier propagation across trust domains.

## 1.41 Documentation-only register update — Ingress/routing governance, runtime readiness and launch-control hardening (2026-08-09)

This documentation-only update adds the remaining pre-production structural
controls identified during deployment/startup omission review. It does not
expand PACK-25's procurement/vendor business scope, does not alter the accepted
PACK-24 baseline, and does not change `REPOSITORY_VERSION` or `CANON_VERSION`.

**New FIR IDs created:**

- `FIR-EDGE-001` — Origin, Ingress & Routing Policy Governance;
- `FIR-READY-001` — Runtime Readiness, Compatibility & Stale-State Protection.

**Existing FIRs strengthened:**

- `FIR-REL-001` — explicit rolling-deployment compatibility and signed
  deployment-manifest requirements;
- `FIR-DATA-004` — explicit restore activation gate before consequential
  traffic is reopened.

**FIR IDs implemented:** none.

This update also establishes a future **Launch Control Gate**: production or
other consequential traffic must not be activated merely because processes are
alive. Artifact provenance, configuration/schema compatibility, trusted-time
condition, projection/read-model freshness, key readiness, dependency readiness
and origin/routing policy must all be demonstrably acceptable for the relevant
service/workspace.

The update does not require all services to run the same Git commit, does not
mandate one fixed startup order, and does not require separate source
repositories or toolchains for every frontend origin. Compatibility and trust
must be proven at the deployed-artifact and runtime-boundary level.

## 1.42 Round record — PACK-25 implementation candidate (2026-08-09)

Per section 1.3, every PACK task lists what it did to this register.

**Baseline:** PACK-24 FINAL PASS (`0.26.0`, SHA-256
`1da174681759a9925e2d5a8dc95b04ea383ba55f62bb502e18dd6e7a6fc29cf7`).
**Repository version after this round:** `0.27.0`. **Canon version:**
unchanged at `0.8.0` — no canon amendment was required and none was made.
**Round status:** implementation candidate. **Not a FINAL PASS.**

**Lineage.** Section 1.36 already carries the PACK-18 through PACK-24
cumulative catch-up supplied with the recovered register; section 1.37
carries the documentation-only update that introduced the cross-cutting
operational assurance foundations; and sections 1.38 through 1.41 carry
the documentation-only updates that introduced, in turn, voting
infrastructure unlinkability and the procedural legal-effect activation
gate; authority revalidation, FIR placement governance and incremental
failure fixtures; cross-domain identifier and correlation governance; and
ingress/routing governance, runtime readiness and launch-control
hardening. This round adds no second catch-up record and renumbers
nothing: the lineage is represented once, by the records that were written
for it, and this record takes the next free number after them — which has
moved as each maintenance copy arrived, rather than any copy's record
being displaced to make room.

**Register recovery.** This round replaced the stale repository copy of
this register with the supplied maintenance copy
`EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V12.md`, installed at
the single canonical path
`docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md`. Six
maintenance copies were supplied over the course of this round — V7
through V12 — and each superseded the one before it. The repository holds
the content of the last, under the canonical name only: no second register
was created, no V7- through V12-named file exists in the repository, no
FIR entry was deleted, no identifier was reused and no historical wording
was rewritten. A mechanical check backs that claim rather than the
sentence: every one of the 163 distinct FIR identifiers in the supplied
V12 copy is present in the installed register, which adds exactly the
entries listed below and nothing else. Carrying the intermediate copies
forward would have left six registers disagreeing about which was
authoritative, which is the condition the recovery exists to end.

The PACK-25 content merged into this copy is this round record, the
`FIR-BASE-001` baseline/candidate distinction, the section 22 note
recording which of its bullets the freshness gate now implements, and
section 33. Nothing else in the supplied copy was altered. The only formatting change applied to the supplied copy was
Prettier's whitespace and table-alignment normalisation, applied through
the governed single-file allowlist mechanism the `Makefile` sanctions; a
whitespace-insensitive comparison of before and after differs only in the
padding of one table's separator row.

**FIR IDs implemented:** none.

PACK-25 is an implementation candidate that has not passed independent
acceptance, authoritative Windows CI or an independent AVH run. Promoting
any entry to `implemented` on the strength of a locally-run pipeline would
be a claim the evidence does not support, and it is the same reasoning
PACK-12's and PACK-13's candidate round records recorded. Two of the new
entries created below are recorded as `implemented in reference form`,
which is the qualifier this repository uses for a governed workflow that
is real, tested and not deployed; it is a weaker claim than `implemented`
and it is stated as such in the entries themselves.

**New FIR IDs created by implementation discovery:**

- `FIR-PROC-001 — Procurement Requisition, Procedure and Selection
Governance`;
- `FIR-PROC-002 — Commitment Chain: Contract Reference, Purchase Order,
Acceptance and Invoice Control`;
- `FIR-PROC-003 — Procurement Separation of Duties and Maker-Checker`;
- `FIR-VENDOR-001 — Vendor Lifecycle and Activation Gate`;
- `FIR-VENDOR-002 — Third-Party Assurance: Versioned Evidence-Backed
Assessment and Governed Reviews`;
- `FIR-VENDOR-003 — External Provider and Gateway Lifecycle Governance`;
- `FIR-VENDOR-004 — Vendor Renewal, Exit and Evidence of Disengagement`;
- `FIR-VENDOR-005 — Event-Triggered Vendor Reassessment`;
- `FIR-REG-001 — Master Future Implementation Register Freshness Gate`.

Each is created because the complete existing register was inspected first
and found to carry no entry with the same semantics. Section 26's forms
catalogue mentions a _procurement request_, a _vendor declaration_, a _bid
submission_, an _evaluation declaration_ and an _invoice approval_ as
**form types**; section 32 lists _procurement and vendor governance_ as a
**control-plane domain**. Neither is a lifecycle, authorization or
assurance requirement, and neither could have been satisfied or
contradicted by this round without being stretched past what it says. The
new entries reference both rather than duplicating them.

**FIR IDs given a foundation but explicitly NOT implemented:**

- `FIR-FORM-003 — Initial EPD² Forms and Documents Catalogue`. **PACK-25
  foundation provided — this entry is NOT implemented.** The "Personnel,
  procurement and contractors" catalogue names procurement request, vendor
  declaration, bid submission, evaluation declaration and reimbursement
  and invoice approval. PACK-25 supplies the _records_ those forms would
  produce and the governed vocabularies they would draw on. It supplies no
  form definition, no field catalogue, no rendition and no submission
  channel, and `FIR-FORM-001`'s framework remains unbuilt.
- `FIR-FORM-002 — Domain Forms and Official Documents Inventory`.
  **PACK-25 foundation provided — this entry is NOT implemented.** The
  procurement domain now has an inventory of governed documents it
  _references_ (`GovernedDocumentKind`: contract, framework agreement,
  tender, bid, invoice, DPA, security report, penetration test, audit
  report, certificate, acceptance evidence, exit evidence, export test
  evidence, incident evidence). That is an inventory of reference kinds,
  not of forms and official renditions.
- `FIR-ROLE-006 — Finance separation of duties`. **PACK-25 foundation
  provided — this entry is NOT implemented.** PACK-25 separates requester,
  buyer, budget owner, approver, receiver and payment authority on the
  _procurement_ side, and holds `PAYMENT_AUTHORITY_ACTIONS` empty so that
  no action in this service releases money. The finance side of the
  boundary is PACK-10's and is untouched.
- `FIR-SEC-003 — External gateway security`. **PACK-25 foundation provided
  — this entry is NOT implemented.** PACK-25 closes the _vendor-lifecycle_
  half of AGR-30: provider registration, activation gating, purpose
  binding, replay-safe signed callbacks, provider-local identifiers that
  cannot become global identifiers, and exit/export evidence. It supplies
  no transport security, no key management, no rotation and no runtime
  gateway hardening.
- `FIR-DATA-001 — Data Catalog & Processing Registry`. **PACK-25
  foundation provided — this entry is NOT implemented.** A vendor record
  carries a `ProcessorRoleStatement` recording _who stated what_, with
  evidence and a date. It makes no controller/processor classification,
  and `OD-P25-10` records that the classification rule is unresolved.
- `FIR-DATA-003 — Legal Hold`. **PACK-25 foundation provided — this entry
  is NOT implemented.** Procurement records carry a legal-hold state and a
  reference to PACK-09's hold, and destructive acts are refused while a
  hold is active. The hold itself is PACK-09's and is not reimplemented.
- `FIR-SEARCH-001 — Authorization-Aware Domain-Scoped Search`. **PACK-25
  foundation provided — this entry is NOT implemented.** The procurement
  context answers a closed list of nine governed, scoped, purpose-bound
  reads and refuses every other query kind as a generic administrative
  search. That is a refusal surface, not the cross-domain search facility
  the entry describes.
- `FIR-INV-007 — DLP and controlled export`. **PACK-25 foundation provided
  — this entry is NOT implemented.** Export from this context requires the
  governed export action specifically, an organizational scope, a stated
  purpose and a permitted destination, and every exported record passes
  the same seven walks the event boundary runs. No repository-wide DLP
  capability follows.
- `FIR-CONFIG-001 — Governed Operational Configuration`. **PACK-25
  foundation provided — this entry is NOT implemented.** Every
  procurement policy input arrives through one frozen bundle carrying the
  policy version that each act records. The bundle is a port; nothing
  configures it.
- `FIR-SERVICE-001 — Service Catalogue and Responsibility Directory`.
  **PACK-25 foundation provided — this entry is NOT implemented.** A
  provider registration names its `owning_service`, because an integration
  nobody owns is an integration nobody turns off. That is one edge of the
  directory, recorded per integration rather than centrally.
- `FIR-OSS-003 — Third-Party Licence and Dependency Compliance`. **PACK-25
  foundation provided — this entry is NOT implemented.** The vendor
  assessment model is general enough to hold a supplier of software, and
  `AssessmentDimension` includes subcontractor exposure and audit-evidence
  availability. No dependency inventory, SBOM, licence scan or
  vendored-component governance is provided, and the _dependency_ sense of
  "vendor" in `FIR-OSS-003` is deliberately not conflated with the
  _counterparty_ sense in `FIR-VENDOR-001`.
- `FIR-UX-011 — Page Specification and Screen Content Governance`.
  **PACK-25 foundation provided — this entry is NOT implemented.** Seven
  activation-gated route classes are declared with owners and backend
  dependencies. No page specification, screen content catalogue or
  navigation sequence is supplied.
- `FIR-CTRL-001 — Unified Control Plane & Administrative Workspace
Architecture` and `FIR-ROADMAP-010 — CTRL-01`. **PACK-25 foundation
  provided — these entries are NOT implemented and CTRL-01 was NOT
  started.** PACK-25 contributes the procurement/vendor domain's role
  vocabulary, incompatible-role matrix and desk-shaped route classes to
  the eventual Control Plane Registry, and holds
  `technical administration != procurement authority` structurally. Both
  entries keep their scheduled placement after PACK-35 and before
  Architecture Baseline 1.0 / Freeze, unchanged.

**FIR IDs intentionally left unchanged:** every other entry in this
register. In particular:

- all `FIR-INIT-*`, `FIR-ASM-*`, `FIR-DEC-*`, `FIR-CAND-*`, `FIR-PAY-*`,
  `FIR-FIN-*`, `FIR-PROG-*` and `FIR-AI-*` entries are untouched — PACK-25
  reaches none of those domains;
- `FIR-INV-013 — Bund / Land / Kreis isolation` is untouched as a
  _requirement_: PACK-25 enforces scope isolation inside its own stores
  and adds no repository-wide capability, so restating the invariant here
  would risk a restatement disagreeing with the original;
- `FIR-INV-003 — Voting Client isolation` and `FIR-FRONT-004` are
  untouched. PACK-25 adds refusals that keep procurement material out of
  WS-03 and keep voting identifiers out of procurement references; it
  narrows nothing and restates nothing;
- `FIR-INV-012 — Accessibility as Definition of Done` is untouched. The
  repository's existing accessibility baseline applies to the PACK-25
  routes and no procurement-specific exemption is claimed; `OD-P25-27`
  records that no procurement-specific accessibility requirement has been
  stated;
- `FIR-INV-015 — No false production claims` is untouched and is the
  entry this round most deliberately complies with: every PACK-25
  artefact carries **NOT PRODUCTION READY** and **NOT LEGALLY ACTIVATED**,
  and no FIR is promoted to `implemented`.
- `FIR-VOTE-NET-001 — Network & Infrastructure Unlinkability for Voting`
  is untouched and **was not implemented**. It arrived with the V9
  maintenance copy during this round. PACK-25 neither advances nor
  contradicts it: this pack adds no ingress, CDN/WAF, reverse-proxy,
  network or tracing capability, and its five procurement-specific Voting
  Client controls are application-layer refusals that keep procurement
  material out of WS-03 — which is precisely the layer `FIR-VOTE-NET-001`
  observes is _not_ sufficient on its own. Recording it as advanced would
  be the misreading the entry exists to prevent.
- `FIR-LEGAL-001 — Procedural Legal-Effect Activation Gate` is untouched
  and **was not implemented**. It also arrived with V9. PACK-25 is
  consistent with it — every artefact is marked **NOT LEGALLY
  ACTIVATED**, no vocabulary member or reason code concludes anything
  about legality, and twenty-eight legal applicability questions are held
  open rather than answered — but consistency is not implementation. The
  entry asks for a governed activation gate with evidence, and this pack
  supplies none.
- `FIR-AUTH-001 — Consequential Commit Reauthorization & TOCTOU
Protection` is untouched and **was not implemented**. It arrived with
  the V10 maintenance copy. PACK-25's guard resolves authority once per
  command, before the body runs, which is the shape the entry identifies
  as insufficient — authority, scope, assurance and object state may all
  change between that check and the commit. No revalidation-at-commit
  mechanism is provided here, and recording one would misdescribe what
  the guard does.
- `FIR-ROADMAP-011 — FIR Ownership, Placement & Verification Map` is
  untouched and **was not implemented**. It also arrived with V10. The
  eight entries this round creates each name an owner and a verification
  route in their own text, which is a contribution to the eventual map
  and is not the map.
- `FIR-TEST-002 — Incremental Cross-Service Failure Fixtures` is
  untouched and **was not implemented**. It also arrived with V10.
  PACK-25's suites exercise this service's own failure paths against
  fakes; no cross-service failure fixture is supplied, and the
  distinction is the entry's whole point.
- `FIR-ID-001 — Cross-Domain Identifier & Correlation Governance` is
  untouched and **was not implemented**. It arrived with the V11
  maintenance copy, and PACK-25's obligation under it is negative rather
  than constructive: **do not introduce** a prohibited cross-domain
  stable identifier. That obligation is met and is checked
  (`NC-P25-48`) — a `CROSS_DOMAIN_IDENTIFIER_MARKERS` walk runs at both
  the command boundary and the emission chokepoint, no governed contract
  declares such a property, `ProviderLocalIdentifier` cannot be promoted
  to a global identity, the stores are scope-partitioned, and correlation
  identifiers are request-scoped rather than person-scoped. None of that
  is the identifier inventory, semantic registry or repository-wide
  correlation checker the entry requires, and this round does not claim
  otherwise.
- `FIR-EDGE-001 — Origin, Ingress & Routing Policy Governance` is
  untouched and **was not implemented**. It arrived with the V12
  maintenance copy. PACK-25 declares seven activation-gated route classes
  with owners and backend dependencies and adds no ingress, origin,
  routing, CDN or edge configuration of any kind — which is the layer the
  entry governs. A route registry is not a routing policy, and recording
  one as progress against the other would be the conflation the entry
  exists to prevent.
- `FIR-READY-001 — Runtime Readiness, Compatibility & Stale-State
Protection` is untouched and **was not implemented**. It also arrived
  with V12. Every PACK-25 frontend route is `BACKEND_UNAVAILABLE` and no
  procurement service is deployed, so there is no runtime whose readiness
  could be gated. The entry's Launch Control Gate — that consequential
  traffic must not be activated merely because processes are alive — is a
  repository-wide control this pack neither implements nor weakens.
- `FIR-REL-001`, as **strengthened by V12** with explicit
  rolling-deployment compatibility and signed deployment-manifest
  requirements, is untouched and **was not implemented**. PACK-25 supplies
  no deployment manifest, signed or otherwise, and no rolling-compatibility
  statement. The strengthened wording is carried forward verbatim.
- `FIR-DATA-004`, as **strengthened by V12** with an explicit restore
  activation gate before consequential traffic is reopened, is untouched
  and **was not implemented**. PACK-25's stores are in-memory reference
  adapters; there is no backup, no restore path and therefore no restore
  gate. The strengthened wording is carried forward verbatim.

**FIR IDs deferred:** none. PACK-25 defers no entry: an entry it did not
reach is left unchanged rather than moved to `deferred`, because
`deferred` is a governed decision about scheduling and this round has no
authority to make one.

**Limitations this round found.** Twenty-eight open decisions
(`OD-P25-01` through `OD-P25-28`) are recorded in
`contracts/procurement/pack-25-open-decisions.json` and every one of them
fails closed. None of them is a new _requirement_: each is a question the
domain cannot answer without a governed legal decision, and recording them
as open decisions rather than as FIR entries is deliberate — a FIR is
something this repository intends to build, and a legal applicability
question is not.

## 1.43 Correction round — PACK-16D verification-harness integrity (2026-08-09)

This is a **governed correction round**, not a new business PACK. PACK-26 was
not started. The repository version remains `0.27.0` and Canon remains `0.8.0`;
the correction changes verification mechanics and evidence-chain enforcement
only.

**Accepted baseline entering the correction:** PACK-25 FINAL PASS, exact
candidate SHA-256
`962aa8b554995664f7fedb091b6955139edf41f757da3a56834a865e728f49ca`.
Acceptance followed the authoritative Windows local-CI PASS and the independent
AVH 0.1.3 run accepted for the round. The accepted PACK-25 archive is immutable;
all correction work is performed in a separate cumulative copy.

**Correction finding.** The inherited target-conformance module used two
PACK-16D frozen reference artefacts as writable outputs. The local-CI driver
restored them after its dedicated stage, which protected that one driver path,
but direct pytest execution could leave the repository dirty. That is an
evidence-chain defect: verification must not make accepted reference bytes depend
on which tests happened to run before packaging.

**Correction invariants.**

- frozen PACK-16D reference artefacts are read-only test inputs; generated
  fixtures and host timings are emitted only below pytest-managed temporary
  storage;
- the five immutable PACK-16D voting artefacts have exact SHA-256 identities
  enforced before testing, after the target-conformance stage, after the whole
  pipeline, immediately before packaging, and again from the bytes inside the
  produced archive;
- a deliberate one-byte mutation is detected by the actual packaging gate and
  causes packaging to fail closed before a ZIP is created;
- legacy restore remains defence-in-depth but is no longer the mechanism that
  makes ordinary target-conformance safe;
- no PACK-26 domain, service, route, contract or document is introduced.

**FIR disposition:** no FIR is promoted, deferred or newly created by this
correction. It supplies concrete evidence-chain hardening relevant to
`FIR-REL-001` and the pre-Freeze verification gate, while leaving those broader
future requirements at their existing status.

## 1.44 Acceptance continuity record — PACK-25 and PACK-25C6 FINAL PASS (2026-08-09)

This maintenance record repairs the canonical baseline pointer after the
independent acceptance sequence completed. It is a register-continuity update,
not a new business PACK and not a repository-version bump.

**Accepted PACK-25 business baseline:** repository `0.27.0`, Canon `0.8.0`,
SHA-256 `962aa8b554995664f7fedb091b6955139edf41f757da3a56834a865e728f49ca`.

**Accepted PACK-25C6 correction baseline:** repository `0.27.0`, Canon `0.8.0`,
SHA-256 `900f955762fbad14d82d24da315a28b5f268318d3bb278223f8d05eaf4037d2f`.
The correction is now the sole entering baseline for PACK-26.

Authoritative Windows local CI for PACK-25C6 passed every stage, including the
isolated target-conformance suite, Ruff lint and format check, ordinary pytest,
all mypy groups, repository governance, verifier/adversarial/comparison suites,
wheel isolation, frontend checks, Prettier, final frozen verification and
packaging eligibility. AVH 0.1.3 then returned its expected `CONDITIONAL
(AVH-L1)` result with zero findings. The five frozen PACK-16D artifacts retained
their accepted exact SHA-256 values.

**FIR IDs implemented by this record:** none. Acceptance evidence does not
silently implement future requirements.

**FIR IDs intentionally left unchanged:** every substantive FIR entry except
`FIR-BASE-001`, whose baseline pointer is updated to the accepted correction.

**New FIR IDs created:** none.

## 1.45 Documentation-only V13 update — voting cryptographic closure, gateway non-ownership and deployment compatibility (2026-08-09)

This V13 maintenance update records three pre-production controls that must be
closed before Architecture Baseline 1.0 / Freeze. It does not start PACK-26,
does not change repository version `0.27.0`, does not change Canon `0.8.0`, and
does not alter the accepted PACK-25C6 archive.

**New FIR IDs created:**

- `FIR-VOTE-CRYPTO-001` — Production Secret-Ballot Cryptographic Protocol Selection & Verification;
- `FIR-API-001` — API Gateway / BFF Non-Ownership & Domain-Logic Prohibition.

**Existing FIRs strengthened:**

- `FIR-REL-001` — deployment manifests now explicitly constitute the approved
  integrated build identity; accidental heterogeneous service combinations are
  fail-closed, while deliberately mixed rolling versions are allowed only by a
  declared compatibility matrix;
- `FIR-EDGE-001` — ingress/gateway routing policy is explicitly separated from
  domain authority and domain truth;
- `FIR-READY-001` — runtime readiness must validate deployment-manifest and
  compatibility evidence before consequential traffic is activated.

**FIR IDs implemented:** none. These are future hard gates.

The update deliberately does **not** require every service to have the same Git
hash. The stronger invariant is that every staging/production integrated
contour must match one approved, immutable deployment manifest containing the
exact artifact identities and compatibility evidence for the combination that
is actually running.

## 1.46 Round record — Dedicated Correction Round: PACK-16D Verification-Harness Integrity (2026-08-09)

**Round:** Special Technology Correction Round (Harness & Evidence-Chain Hardening).  
**Business Scope:** Explicitly NONE. PACK-26 (Volunteer, Staff & Contractor Administration) was NOT started.  
**Repository Version:** Unchanged at `0.27.0`.  
**Canon Version:** Unchanged at `0.8.0` — no canon entities or aggregates were altered.  
**Baseline:** Accepted cumulative PACK-25 / PACK-25C6 Final Pass (`0.27.0`, SHA-256: `900f955762fbad14d82d24da315a28b5f268318d3bb278223f8d05eaf4037d2f`).

### 1.46.1 Context and Technical Finding

An independent architectural audit identified a critical weakness in the inherited target-conformance testing layout for the voting domain. Two frozen cryptographic reference artefacts were being used as writable test outputs by the target-conformance module. Although the local-CI driver preserved and restored the accepted bytes around that stage, direct execution of the test module could mutate the working tree and make verification results depend on execution order and host conditions.

This correction round isolates generated target-conformance outputs from the frozen reference catalogue without altering the accepted PACK-25 business/domain implementation.

### 1.46.2 Implemented Invariants & Safeguards

- **Test-output isolation:** Frozen PACK-16D reference artefacts are no longer used as runtime output destinations. Target-conformance-generated fixtures, timings and related execution artefacts are written only to isolated temporary locations.
- **Frozen-evidence integrity gates:** The accepted SHA-256 identities of the five governed PACK-16D artefacts are checked at multiple lifecycle boundaries, including:
  1. before test execution;
  2. after the isolated target-conformance stage;
  3. before packaging;
  4. during archive creation;
  5. against the corresponding bytes contained inside the generated archive.
- **Fail-closed mutation coverage:** Dedicated repository tests deliberately mutate frozen artefact bytes in isolated test fixtures and verify that packaging is refused on any accepted-hash mismatch.
- **Defence-in-depth restoration:** Legacy restoration logic remains only as a secondary safety mechanism. Correctness no longer depends on writing frozen reference artefacts and subsequently restoring them.
- **Direct-test safety:** The target-conformance module itself now uses temporary output paths, so direct execution no longer requires mutation of the governed frozen catalogue.

### 1.46.3 FIR Disposition

- **FIR IDs implemented:** None. This round hardens verification/release-integrity mechanisms associated with `FIR-REL-001` and the pre-Freeze assurance path, but does not close a functional FIR requirement.
- **FIR IDs deferred or newly created:** None.
- **FIR IDs intentionally left unchanged:** All substantive future requirements. In particular, `FIR-VOTE-NET-001` and `FIR-CTRL-001` remain in their planned future closure windows.

### 1.46.4 Verification Evidence

Authoritative Windows Local-CI passed all integrated stages on the corrected PACK-25C6 tree, including isolated target conformance, Ruff, full pytest, all mypy groups, repository governance checks, Pack-17b verification suites, frontend checks, packaging controls and final frozen-artefact verification.

Independent AVH 0.1.3 verification of the exact accepted PACK-25C6 archive completed with the expected `CONDITIONAL (AVH-L1)` result and zero findings.

The five governed PACK-16D frozen artefacts retained their accepted SHA-256 identities throughout verification and packaging.

The canonical baseline pointer `FIR-BASE-001` is updated to identify PACK-25C6 as the sole authoritative entering baseline for PACK-26.

## 1.47 Round record — Documentation-only register update: Repository Secret Leakage Prevention & Public-Release Sanitization (2026-08-09)

**Round:** Post-PACK-25C6 Governance Update.  
**Business Scope:** Explicitly NONE. PACK-26 was NOT started.  
**Repository Version:** Unchanged at `0.27.0`.  
**Canon Version:** Unchanged at `0.8.0`.  
**Baseline:** Accepted cumulative PACK-25C6 correction baseline (`0.27.0`, SHA-256: `900f955762fbad14d82d24da315a28b5f268318d3bb278223f8d05eaf4037d2f`).

**New FIR ID created:**

- `FIR-SEC-SECRET-001` — Repository Secret Leakage Prevention & Public-Release Sanitization.  
  **Status:** `approved`.  
  **Implementation Target:** Distributed; INFRA/CI phase for automated enforcement.  
  **Hard Blocker:** Public Repository Release + Production Readiness.

### 1.47.1 Requirement Specification: FIR-SEC-SECRET-001

Ни один действующий пароль, токен, закрытый ключ, секрет подписи, API-ключ, персональный токен доступа (PAT), продукционная строка подключения, учетные данные облачного провайдера или иной действующий операционный секрет не может находиться в исходном дереве репозитория, фикстурах, документации, сохранённых логах, сгенерированных артефактах, дистрибутивах, release-архивах либо в Git-истории, предназначенной для публикации.

Все тестовые credentials, connection mocks, cryptographic secrets и identity assertions должны быть явно синтетическими, детерминированными, non-live и неспособными предоставить доступ к реальной среде.

### 1.47.2 Multi-Stage Fail-Closed Enforcement Cascade

Защита должна состоять из независимых рубежей:

1. **Developer-side pre-commit protection:** локальный secret scanner должен обнаруживать подозрительные credentials до commit. Этот механизм является ранним предупреждением и defence-in-depth и **не считается авторитетным security gate**, поскольку локальный hook может быть отключён или обойдён.
2. **Authoritative CI gate:** CI должен fail closed при обнаружении неразрешённого secret candidate в изменённых файлах, generated outputs либо иных artefacts, входящих в проверяемую сборку. Успешный merge/release не может зависеть исключительно от локального pre-commit контроля.
3. **Repository/history gate:** перед публичным release должна сканироваться текущая repository tree и вся Git-history/refs, которые будут доступны в публикуемом репозитории. Удаление секрета только из текущей версии файла не считается remediation.
4. **Packaging integrity gate:** до упаковки проверяется staging/source set, предназначенный для distribution; после создания ZIP/wheel/другого distributable artefact выполняется повторная проверка фактического содержимого созданного контейнера. Packaging/release must fail closed on an unresolved secret finding.
5. **Public-release gate:** непосредственно перед первым публичным открытием репозитория выполняется отдельный полный secret-leakage scan целевого public state, включая публикуемую Git history и release artefacts.

Detection may combine known-secret signatures, provider-specific formats, structured detectors, entropy analysis and additional governed mechanisms. Конкретный scanner implementation не фиксируется данным FIR заранее.

### 1.47.3 Cryptographic Material Separation & Allowlist Governance

- **Public cryptographic material != secret.** Governed reference public keys, public verification parameters, deterministic hashes, public test vectors, NIZK verification material и иные намеренно публикуемые криптографические данные не должны автоматически классифицироваться как live secrets.
- **Private/signing material remains prohibited.** Реальные private keys, signing secrets, recovery secrets и operational credentials не могут использовать reference-material exception.
- **Central governed allowlist only.** Произвольные inline bypasses (`# ignore-secret`, аналогичные comments/directives) запрещены. Исключение допускается только через централизованно управляемый allowlist с машинно-проверяемым идентификатором, ограниченной областью действия и документированным доказательством synthetic/non-live nature.
- Allowlist не должен разрешать broad path/pattern exemptions, способные скрыть настоящий секрет.

### 1.47.4 Compromise, Revocation & Remediation

При подтверждённом обнаружении live secret:

1. credential/secret считается скомпрометированным независимо от того, был ли репозиторий публичным;
2. секрет должен быть revoked/rotated у соответствующего authority/provider;
3. удаление строки из HEAD не считается достаточным;
4. если секрет присутствует в публикуемой Git history, history должна быть очищена либо соответствующая история исключена из public release;
5. после remediation выполняется полный повторный scan;
6. release запрещён до получения PASS.

History rewriting не отменяет необходимость rotation: секрет, однажды раскрытый за пределами контролируемой границы, больше не считается доверенным.

### 1.47.5 Environment & Machine-Specific Configuration Boundary

Репозиторий может содержать шаблоны вроде `.env.example` только с явно несекретными placeholders.

Реальные `.env`, developer tokens, production credentials, machine-local connection data и иная локальная secret-bearing configuration должны:

- находиться вне version control;
- быть исключены правилами repository hygiene / `.gitignore`;
- не попадать в source archives, release archives и CI evidence;
- не использоваться как committed test fixtures.

`.gitignore` является defence-in-depth и **не является доказательством отсутствия секретов**.

### 1.47.6 Log & Evidence Sanitization

Persistent CI logs, diagnostic traces, verification bundles и WORM evidence должны проходить sanitization до сохранения или публикации.

В частности, запрещено сохранять в открытом виде:

- `Authorization` credentials;
- session/access/refresh tokens;
- cookies и authentication session identifiers;
- private keys;
- password/credential values;
- secret-bearing environment variables;
- provider access credentials.

Redaction itself must be testable. Security evidence must prove the execution result without reproducing the secret it is intended to protect.

### 1.47.7 Acceptance Criteria for System Freeze / Public Release

`clean working tree` не является достаточным доказательством.

Для прохождения Public Repository Release Gate и Architecture Baseline / Freeze должны одновременно получить PASS:

- current repository tree;
- Git history and refs included in the public repository;
- generated/build outputs selected for distribution;
- compiled wheels/packages;
- final public-release ZIP/archive;
- persisted CI/release evidence subject to publication.

Any unresolved confirmed live-secret finding is a **hard release blocker**.

### 1.47.8 FIR Disposition

`FIR-SEC-SECRET-001` создаётся как cross-cutting security/release-integrity requirement. Его enforcement распределён по repository governance, CI/CD, packaging и public-release controls.

Он не считается реализованным данным documentation-only round и не должен быть закрыт до появления machine-enforced verification evidence.

## 1.48 Round record — Documentation-only register update: Sovereign Infrastructure Assurance and Governed Native Mobile Client (2026-08-10)

- **Round:** Post-PACK-26C1 Governance Update
- **Business Scope:** `NONE`
- **PACK-27:** `NOT started by this documentation-only round`
- **Entering accepted code baseline:** `EPD2_PACK-26C1_CANDIDATE_0.28.0.zip`
- **Repository version:** `0.28.0`
- **Canon version:** `0.8.0`
- **Nature of change:** future-governance requirements only; no implementation claim and no production-activation claim

This maintenance round records two approved future requirements without selecting a commercial provider or prematurely implementing a mobile product:

1. `FIR-INFRA-SOV-001` — Sovereign Hosting, Infrastructure Isolation & Data-Residency Assurance;
2. `FIR-MOBILE-001` — Governed Native Mobile Client & Release Assurance.

The infrastructure requirement deliberately separates legal obligations from EPD²'s chosen assurance posture. It does **not** state that DSGVO, PartG, BSI or BVA categorically require bare metal, dedicated hosts or a particular provider. Provider, tenancy, physical-isolation and key-custody choices must be justified by the current threat model, DPIA/data-protection assessment where applicable, legal evidence, service criticality and independent assurance. Unknown or unsupported legal applicability remains `OPEN`.

The mobile requirement preserves the accepted ten-workspace/ten-origin architecture. A native mobile application is a client channel, not an eleventh workspace or origin and not a second source of domain authority. Voting from mobile must continue through the separately isolated Voting Client boundary using the governed system-browser/one-time-handoff pattern; mobile application state must not absorb voting identity, ballot, credential or persistent Voting Client state.

Neither FIR is closed by this documentation-only round. Both require machine-enforced implementation evidence before their respective production-readiness gates can pass.

## 1.49 Round record — PACK-26 implementation candidate (2026-08-09)

Volunteer, staff and contractor administration. The first normal functional
PACK after the governed PACK-25C6 verification-harness correction, entered from
that correction as the sole baseline. Repository version `0.27.0` → `0.28.0`;
Canon unchanged at `0.8.0`.

The pack adds `services/people-administration-service` as a leaf service
depending only on `epd2-core` and `epd2-audit-core`, with governed contracts,
reserved/enforced deadline partitioning, an open-decision register of sixteen
entries, governed frontend surfaces inside the existing ten workspaces, and
adversarial test coverage.

The central invariant is that an engagement is a relationship recorded for
administration and is **not** a membership, an office, a mandate, an
authorization grant, a procurement act or a legal determination of employment
status. Every one of those separations is encoded as a refusal with its own
exception type rather than as a documented expectation, so a test asserting a
conflation refusal cannot be satisfied by a service that merely rejected the
payload for being malformed.

**FIR IDs implemented:** none. PACK-26 closes no repository-wide
future requirement outright, and this record claims none.

**FIR IDs partially advanced:**

- `FIR-ID-001` — incremental, PACK-26-local enforcement only. Engagement
  identifiers are domain-scoped (`EngagementLocalIdentifier`, which binds the
  engagement into the type and whose promotion helper always raises); the
  cross-domain identifier walk refuses a stable person identifier at every
  command and event boundary; `assert_engagements_not_correlated` refuses an
  assertion that two engagements concern one human; no projection reconstructs
  the correlation. This does **not** close `FIR-ID-001`, which remains a
  repository-wide requirement across all contexts.
- `FIR-AUTH-001` — advanced within this context only: an exhaustive action
  registry where absence denies, maker/checker on the four consequential acts,
  nineteen declared incompatible role pairs, and six roles declared solely so
  that holding one can be refused. No repository-wide authorization model is
  established.
- `FIR-LEGAL-001` — advanced by adding a further context that carries
  `NO_LEGAL_EFFECT_ESTABLISHED` on every record and refuses employment, tax and
  social-security conclusions at the boundary. The repository-wide requirement
  is unchanged.
- `FIR-TEST-002` — advanced by adversarial and mutation-style coverage for this
  service's idempotency, replay-before-version ordering, scope isolation and
  separation controls. The repository-wide coverage requirement is unchanged.
- `FIR-DATA-004` — advanced by refusing special categories, judgement fields and
  unstructured narrative at every boundary, and by holding references rather
  than content throughout.

**FIR IDs intentionally left unchanged:**

- `FIR-ROADMAP-011`, `FIR-READY-001`, `FIR-REL-001`, `FIR-CTRL-001` — untouched.
  PACK-26 deploys nothing, activates nothing and establishes no runtime
  readiness or release-identity evidence, so nothing in it may advance them.
- `FIR-API-001` and `FIR-VOTE-CRYPTO-001` — carried forward from the V13
  register merge, untouched by this pack.
- every other substantive FIR entry.

**FIR IDs deferred:** none deferred _by_ this pack. The work PACK-26 declined to
do is recorded as new FIR entries below rather than as deferrals, because none
of it was previously scheduled into this round.

**New FIR IDs created:** `FIR-PEOPLE-001`, `FIR-PEOPLE-002`, `FIR-PEOPLE-003`.

Explicit non-goals honoured: no payroll, salary, tax or social-security
calculation; no banking or payment; no invoice approval; no timesheets or
working-time records; no leave, sickness or medical records; no recruitment or
applicant tracking; no performance scoring; no disciplinary dossier; no
procurement award or vendor activation; no universal IAM or RBAC redesign; no
conflict-of-interest system (PACK-27); no transparency publication (PACK-28);
no deployment, container or database implementation.

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent party
for this pack, and this record does not claim a PASS.

## 1.50 Round record — PACK-27 implementation candidate (2026-08-10)

Conflicts, declarations and recusal. Entered from the accepted PACK-26C1
candidate as the sole authoritative code baseline
(`EPD2_PACK-26C1_CANDIDATE_0.28.0.zip`, SHA-256
`760b1c9afa456547202eca2332445164914ba489631ad3134d67ca3641d9aa28`).
Repository version `0.28.0` → `0.29.0`; Canon unchanged at `0.8.0`.

The pack adds `services/conflict-recusal-service` as a leaf service depending
only on `epd2-core` and `epd2-audit-core`, with governed contracts, three state
machines, an enforced/reserved deadline partition, an open-decision register of
sixteen entries, governed frontend surfaces inside the existing ten workspaces,
and adversarial test coverage.

This round also reconciles the external `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V13.md`
into this single canonical register, in two passes as the governing reference was
updated mid-round. Carried in verbatim: rounds 1.46 (PACK-16D verification-harness
integrity), 1.47 (`FIR-SEC-SECRET-001`) and 1.48 (sovereign infrastructure
assurance and governed native mobile client), and sections 34, 35 and 36
(`FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`, `FIR-MOBILE-001`).

Two numbering collisions were resolved in favour of the governing reference. The
PACK-26 round record moves 1.46 → 1.49 and the PACK-27 round record is 1.50; the
section this pack created for its own discoveries moves 35 → 37. Both are
renumberings, not rewrites: no FIR entry, disposition, acceptance record or round
content was deleted, renamed, downgraded or closed by the reconciliation. After
this round there is no external governing register: the canonical file is the
only one.

The central invariant is a chain of separations, each encoded as a named
refusal rather than as a documented expectation:

```text
declaration != conflict finding != recusal != role removal
             != office termination != disciplinary sanction
             != procurement exclusion != authorization revocation
```

with `technical access state != conflict status` running sideways in both
directions. The first link carries the most weight and is the least technical:
a register in which declaring is itself the finding punishes candour, and the
rational response to such a register is to declare nothing.

Two further structural refusals: there is no universal `conflicted` flag
(`assert_no_universal_conflict_flag` refuses the field at every boundary,
because one bit collapses five separately-decided facts and answers none of
them), and there is no universal ethics administrator
(`assert_no_universal_role` proves that no role is permitted for every governed
action).

**FIR IDs implemented:** none. PACK-27 closes no repository-wide future
requirement outright, and this record claims none.

**FIR IDs partially advanced:**

- `FIR-ID-001` — incremental, PACK-27-local enforcement only. Declaration
  identifiers are domain-scoped (`DeclarationLocalIdentifier`, whose promotion
  helper always raises); the cross-domain identifier walk refuses a stable
  person identifier at every command and event boundary;
  `assert_declarations_not_correlated` refuses an assertion that two
  declarations concern one human; no projection reconstructs the correlation
  and `refuse_person_centric_view` refuses the query by name. This does **not**
  close `FIR-ID-001`, which remains a repository-wide requirement across all
  contexts. Future owner: a repository-wide identity round.
- `FIR-AUTH-001` — advanced within this context only: an exhaustive action
  registry of twenty-three actions where absence denies, maker/checker on the
  five consequential acts at `HIGH` assurance, twenty-six declared incompatible
  role pairs, and five roles declared solely so that holding one can be
  refused. No repository-wide authorization model is established.
- `FIR-DATA-004` — advanced by refusing special categories, judgement fields,
  interest amounts, third-party personal data and unstructured narrative at
  every boundary, and by holding references rather than content throughout.
  Disposition propagation across derived copies is untouched.
- `FIR-REL-001`, `FIR-EDGE-001`, `FIR-READY-001` — carried forward in their
  strengthened V13 form, untouched. PACK-27 deploys nothing and establishes no
  runtime readiness, ingress or release-identity evidence.
- `FIR-TEST-002` — advanced by adversarial coverage for this service's
  idempotency, replay-before-version ordering, scope isolation, deadline
  boundary behaviour and separation controls. The repository-wide coverage
  requirement is unchanged.
- `FIR-CTRL-001` — advanced only to the extent that four governed surfaces were
  registered inside the existing ten workspaces with one owner, one backend
  dependency, an explicit activation state and declared assurance each. No
  control-plane architecture is established.
- `FIR-LEGAL-001` — advanced by adding a further context that carries
  `NO_LEGAL_EFFECT_ESTABLISHED` on every record, refuses statutory periods by
  name, and refuses to claim that a decision taken by a participant this
  register shows as recused is void, challengeable or valid (`OD-P27-11`). The
  repository-wide requirement is unchanged.

**FIR IDs intentionally left unchanged:**

- `FIR-SEC-SECRET-001` — preserved exactly as carried in from V13 and **not**
  advanced. PACK-27 builds no secret-scanning or CI infrastructure; that
  remains an INFRA/CI responsibility and a hard blocker for Public Repository
  Release and Production Readiness. PACK-27 introduced no secret-bearing
  committed material.
- `FIR-VOTE-CRYPTO-001` — untouched. No voting protocol and no cryptographic
  implementation in this pack. `RestrictedActivity.VOTING_IN_MATTER` is a
  governance restriction on participating in a decision and is not a Voting
  Client operation.
- `FIR-API-001` — untouched. This service exposes no gateway or BFF and owns no
  domain logic outside its bounded context.
- `FIR-INFRA-SOV-001` — preserved exactly as carried in from V13 and **not**
  advanced. PACK-27 selects no provider, chooses no tenancy or physical-isolation
  model, defines no residency or key-custody control and deploys nothing. What it
  does do is not violate the requirement: the service is a leaf domain module with
  no infrastructure, no deployment manifest, no operator-access model and no
  persistence beyond in-memory adapters, so it introduces no placement decision
  for a future profile to undo. `hosting provider != trust assumption` is not a
  proposition this pack tests, because this pack has no hosting.
- `FIR-MOBILE-001` — preserved exactly as carried in from V13 and **not**
  advanced. PACK-27 adds no mobile client and no channel of any kind. It also does
  not obstruct the requirement: the four surfaces it registers sit inside the
  accepted ten-workspace/ten-origin model, add no eleventh workspace or origin, add
  no route to WS-03, hold no voting identity, ballot, credential or persistent
  Voting Client state, and make no client a source of domain authority. A future
  native client is a channel onto these same governed routes, and nothing here
  makes that harder.
- `FIR-ROADMAP-011` — untouched.
- `FIR-PEOPLE-001` and `FIR-PEOPLE-003` name PACK-27 in their target windows
  and are **not** closed by this pack. PACK-27's engagement boundary is a
  citation type (`EngagementFactRef`) plus a refusal that always raises; it is
  one context's share of each requirement, not either requirement's closure. A
  reader who assumed otherwise from the target window would be assuming what
  this record declines to say.
- every other substantive FIR entry.

**FIR IDs deferred:** none deferred _by_ this pack. The work PACK-27 declined
to do is recorded as new FIR entries below rather than as deferrals, because
none of it was previously scheduled into this round.

**New FIR IDs created by implementation discovery:** `FIR-CONFLICT-001`,
`FIR-CONFLICT-002`.

Explicit non-goals honoured: no sanction, warning, exclusion or disciplinary
measure; no removal from any role, office, mandate, engagement or membership;
no technical access grant or revocation; no vendor selection, approval,
rejection, activation, order, invoice approval or payment; no voiding,
reopening or validating of any governed decision; no universal IAM or RBAC
redesign; no people administration; no protected-reporting channel; no
transparency publication beyond the approved projection this service builds; no
change to Voting Client architecture; no new voting protocol or cryptography;
no deployment, container or database implementation.

German legal applicability remains **OPEN** (`OD-P27-01`). No provision of the
VwVfG, of any Gemeindeordnung, of the Parteiengesetz or of the
Abgeordnetengesetz is encoded, applied or concluded, and no statutory period is
computed. `implemented != legally activated`;
`technical conflict finding != legal consequence`;
`recusal record != legally effective removal`.

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent party
for this pack, and this record does not claim a PASS.

## 1.51 Round record — PACK-27C1 governance and enforcement correction (2026-08-10)

**Round:** surgical correction. **Business scope: NONE.** No domain was
redesigned and no domain logic was reimplemented. Repository version
unchanged at `0.29.0`; canon unchanged at `0.8.0`. Entering baseline:
`EPD2_PACK-27_CANDIDATE_0.29.0.zip`, SHA-256
`1970169629770c921ff0ec385351d3d4aca70ede1029f664bc1878b47346d256`.

Independent inspection of the PACK-27 candidate found three defects, all
of them governance rather than domain. This round fixes each and nothing
else.

**1. The duplicate `FIR-ID-001` heading is resolved.** The merged register
carried 184 `## FIR-…` headings and 183 distinct IDs, because
`FIR-ID-001` appeared twice with different titles. The governing V13
reference had already resolved this: it carries the later passage as
`### V12 strengthening of FIR-ID-001 — Cross-Domain Identifier &
Correlation Governance`, a subsection, not a second entry. The PACK-26
round had promoted it to a top-level entry and PACK-27's reconciliation
preserved the promotion rather than the reference.

The heading is restored to the governing reference's own form. **No
substantive content moved, was reworded or was lost** — the passage keeps
every line it had, in place, under section 29B — and no new FIR ID was
invented for it. A cross-reference was added to the canonical entry so
that demoting the heading costs nothing in discoverability. Result: 183
headings, 183 distinct IDs, `FIR-ID-001` exactly once.

**2. Registered-but-unwired controls are now classified, and the
classification is enforced.** PACK-27's own report listed four actions,
three refusal helpers and one event builder as having no call site. Each
has been audited and placed in exactly one of two classes.

Three actions were **wired** with real call sites and tests:
`conflict.declaration.amend` (a new `amend_declaration` command that
supersedes a declaration with a more accurate one, preserving every prior
version), `conflict.evidence.read_protected` and
`conflict.disclosure.read_public` (two authorized read paths). Wiring the
protected-evidence read also gave `assert_document_access_permitted` its
first call site, so PACK-11 is now actually asked, per document, per
principal, per purpose.

One action — `conflict.applicability.review` — was **reserved**, because
applicability is reviewed inside `conflict.assessment.open` and whether it
becomes a separately authorized act depends on `OD-P27-06`. Two event
types — `conflict.applicability.reviewed` and `conflict.deadline.missed` —
were **reserved** for stated reasons.

Reserved is now a machine-checked state rather than a sentence in a
report. `RESERVED_UNWIRED_ACTIONS`, `RESERVED_ACTION_REASONS`,
`RESERVED_UNEMITTED_EVENT_TYPES` and `RESERVED_EVENT_REASONS` mirror the
shape `RESERVED_UNENFORCED_DEADLINE_KINDS` already had: a closed set, a
reason table, a partition assertion in process, a runtime refusal, and a
repository test that scans for call sites in **both** directions — because
set membership proves classification and only a scan proves wiring. The
command guard refuses a reserved action before it resolves any authority.

The three refusal helpers were **reclassified rather than wired**. A
function whose only behaviour is to raise has no call site by design; that
is what it is for. Counting them as unwired controls was the wrong
classification. What they needed was proof of exercise, and a repository
test now asserts that every one of the twenty-five always-raising refusals
in this service is exercised by a test.

**No deadline changed class.** All three enforced deadline kinds keep real
`assert_within_deadline` call sites, and no declared or enforced deadline
lacks an enforcement site. No fake call site was created to satisfy a
structural checker.

**3. A harness defect in the archive-hygiene suite is fixed.**
`test_the_root_allowlist_matches_the_repository` re-derived its own
exclusion rule inline — "ignore anything starting with a dot" — instead of
consulting `GENERATED_CACHE_DIRECTORIES`, the closed list the working
phase already uses. It therefore disagreed with `find_tree_defects` about
`__pycache__` and `node_modules`, and its dot rule was _weaker_ than the
allowlist it guarded: an unlisted `.cache` or `.idea` at the repository
root would have passed. The test now consults the closed list, so an
unlisted directory is a defect again, dotted or not. The candidate phase
is untouched and stays strict; `find_zip_defects` grants no generated-cache
exemption and a new test pins that.

**FIR IDs implemented:** none. This is a correction round and closes no
future requirement.

**FIR IDs partially advanced:** `FIR-AUTH-001` — marginally, within this
context: the action registry now distinguishes enforced from reserved
authority and refuses the latter at runtime. `FIR-TEST-002` — marginally:
two-direction call-site scans and a refusal-exercise check. Neither
repository-wide requirement is closed.

**FIR IDs intentionally left unchanged:** `FIR-ID-001` — the duplicate
heading was a structural defect in the register, not a change to the
requirement, which is unchanged in scope, status and content.
`FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`, `FIR-MOBILE-001`,
`FIR-VOTE-CRYPTO-001`, `FIR-API-001`, `FIR-REL-001`, `FIR-EDGE-001`,
`FIR-READY-001`, `FIR-ROADMAP-011`, `FIR-PEOPLE-001`, `FIR-PEOPLE-002`,
`FIR-PEOPLE-003` and every other substantive entry.

**`FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open and are explicitly
not closed.** Participation-time enforcement of recorded recusals is still
not implemented, and no consuming context consumes a conflict outcome.
Wiring three actions inside this bounded context advances neither, and
this record claims neither.

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** none. The three
defects this round fixes are corrections to PACK-27's own delivery, not
newly discovered future requirements.

**Round status:** correction candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent
party for this correction, and this record does not claim a PASS.

## 1.52 Round record — PACK-28 governed transparency publication (2026-08-10)

**Round:** business scope. Repository version `0.29.0` -> `0.30.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.30.0` -> `<0.31.0`.
Entering baseline: `EPD2_PACK-27C1_CANDIDATE_0.29.0.zip`, SHA-256
`38454b8b2a1c4c6a21c0478ec5ae752cd674c24d49161ddd34822e98ca764c1d`. No code
was merged from the initial PACK-27 candidate, from PACK-26, or from any
other repository archive.

**No new bounded context.** The existing `services/transparency-service`
was extended with a governed publication layer of twelve `publication_*`
modules. A second transparency or publication service would have had to
hold the same classification vocabulary, the same forbidden-field walks and
the same legal-effect statement as the first, and the two would have
disagreed the first time either changed. PACK-04's `PublicLedgerEntry`,
`AuditExportPackage`, `DisclosurePolicy` and `LobbyLogEntry` are untouched.

**The central invariant is structural.**

```text
source-domain fact != publication decision != publication projection
                  != public legal effect
```

A record existing inside EPD² never means it is publishable. Nine
separately-decided things — candidate, classification, minimisation,
approval, projection, publication, suspension, correction, withdrawal —
are held by five different roles, and there is no `is_public` boolean
anywhere: `assert_no_universal_publication_flag` refuses it by name at
both boundaries and an AST scan refuses it as a field.

**Built by inclusion, not by exclusion.** The projection starts from
nothing and adds only what a recorded minimisation decision authorized.
The obvious implementation — take the source record, strip the redacted
fields — publishes every field somebody adds to the source record later,
because nobody redacted a field that did not exist when the decisions were
taken.

**The redacted value has nowhere to live.** `MinimisationDecision` has no
field for it, `REDACTED_VALUE_KEYS` names sixteen keys it arrives under,
and a repository test asserts the absence by AST. The mistake this
prevents is well-meant: storing what was removed "for the audit trail"
writes the disclosure the redaction refused into an append-only store.

**Corrections add versions.** A correcting publication is a separate
candidate carrying a link that names the earlier one by receipt digest,
checked against the earlier receipt's own recomputed digest.
`assert_receipt_not_rewritten` refuses a second receipt for the same
version — the shape "implement correction as a re-issue" takes.

**Protected reporting is refused structurally.** `SourceDomain` names no
protected-reporting, voting or tally context at all, so a candidate citing
one cannot be constructed. That is not a classification that could be set
wrongly; it is a missing enumeration member.

**Integrity evidence is a digest and is called one.** The receipt carries a
deterministic, publicly recomputable SHA-256. It is not a signature, it
identifies no signer, and `refuse_production_signing_claim` refuses the
claim by name. No key ceremony, HSM or trust anchor exists in this pack.

**One reserved action, two reserved event types, five reserved deadline
kinds**, each with a stated reason, a runtime refusal and a two-direction
call-site scan — because set membership proves classification and only a
scan proves wiring.

**Frontend:** four routes (`P28-R-069` … `P28-R-072`) inside the existing
ten workspaces. Two public in WS-10, two protected in WS-06 and WS-07. No
eleventh workspace, no eleventh origin, nothing in WS-03, and no panel
renders a `button`, a `form` or an `input`.

**FIR IDs implemented:** none. No future requirement in this register is
closed by this round.

**FIR IDs partially advanced:** `FIR-ID-001` — enforced at one more
boundary; no universal or pseudonymous person key reaches a projection and
correlation is refused by name. `FIR-AUTH-001` — a twenty-one-action
registry with an enforced wired/reserved partition. `FIR-DATA-004` —
minimisation as a governed per-field decision carrying no removed value.
`FIR-TEST-002` — two-direction call-site scans, a refusal-exercise scan and
an exhaustive state-machine complement test. None of the four is closed.

**FIR IDs intentionally left unchanged:** `FIR-REL-001`, `FIR-READY-001`,
`FIR-LEGAL-001`, `FIR-CTRL-001`, `FIR-ROADMAP-011`, `FIR-SEC-SECRET-001`,
`FIR-INFRA-SOV-001`, `FIR-MOBILE-001`, `FIR-API-001`,
`FIR-VOTE-CRYPTO-001`, and every other substantive entry.

**`FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open and are explicitly
not closed.** Rendering an approved conflict-disclosure projection is
publication, not participation-time recusal enforcement, and it is not
governed consumption of a conflict outcome by an owning context. PACK-28
has neither the authority nor the source-domain reach to advance either,
and this record claims neither.

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** `FIR-PUB-001`
(governed publication channels and the reach of a withdrawal),
`FIR-PUB-002` (publication integrity signing and independent
verification), `FIR-PUB-003` (governed consumption of published
projections by parliamentary and reporting interfaces) and `FIR-PUB-004`
(removal of the four inherited, unused PACK-04 upstream dependency
declarations from `transparency-service`'s manifest).

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent
party for this candidate, and this record does not claim a PASS.

## 1.53 Round record — PACK-28C1 dependency-boundary and report correction (2026-08-10)

**Round:** surgical correction. **Business scope: NONE.** No domain was
redesigned and no domain logic was reimplemented. Repository version
unchanged at `0.30.0`; canon unchanged at `0.8.0`; compatibility ceiling
unchanged at `<0.31.0`. Entering baseline:
`EPD2_PACK-28_CANDIDATE_0.30.0.zip`, SHA-256
`4862c78a2b8d98dd6f8fd3ae6802bf22484d40e33d9d2f22621783e2266b387d`.

Independent inspection of the PACK-28 candidate returned two findings, one
architectural and one factual. This round fixes both and nothing else.

**1. The transparency-service dependency boundary is now true, not
scoped.** PACK-28's central architectural claim is that the transparency
publication bounded context does not directly depend on source-domain
services. That was enforced on the twelve `publication_*` modules and
contradicted by the manifest, which still declared
`epd2-initiative-service`, `epd2-moderation-service`,
`epd2-voting-service` and `epd2-tally-service` — four ADR-012 edges
granted in July 2026 and **never taken**, as PACK-04's own README recorded
from the start.

The four declarations are removed. `services/transparency-service` now
declares `epd2-core` and `epd2-audit-core`, both verified by inspection to
be genuinely required rather than assumed: `epd2_audit_core.application`,
`.domain` and `.storage`, and `epd2_core.clock`, `.event_envelope` and
`.identifiers`, are imported by both layers of the service.

Nothing compensates for the removal. There is no adapter module, no
dynamic import, no optional import, no `TYPE_CHECKING`-only import, no
`importlib.import_module`, no `__import__` and no module-path string. A
repository test scans the whole service for every one of those shapes
rather than for static imports alone, because a static-import scan is
exactly what an indirection defeats.

**ADR-113 records the narrowing and supersedes ADR-012 in part.** Items
1–3 of ADR-012's Decision — the four upstream edges — are withdrawn. Item
4 (`epd2_audit_core`), every named exclusion
(`epd2_deliberation_service`, `epd2_delegation_service`,
`epd2_account_service`, `epd2_identity_service`,
`epd2_eligibility_service`, `epd2_credential_service`), the requirement
that each exclusion be tested as an affirmative forbidden pair, and the
one-way dependency rule are re-affirmed unchanged. **ADR-012 keeps its
full accepted text** and gains a superseded-in-part note at its head: a
later round that narrows a permission does not get to edit the record of
the permission.

`ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES` and
`PACK04_ALLOWED_PACK03_ROOTS` in
`tests/repository/test_service_boundaries.py` are now empty. An empty
allowlist is a **stricter** check than a populated one, not a weaker one:
the existing boundary test compares every import against it, so any
PACK-02 or PACK-03 import from this service is now a violation where four
were permitted.

Because a Python dependency declaration changed, `uv.lock` was regenerated
with `uv lock` and **not** hand-edited. The diff is exactly the eight lines
that named the four withdrawn packages. `package-lock.json` is byte-identical:
no frontend dependency changed.

The four upstream read wrappers remain public in their owning services,
unchanged, and now have no declared consumer in this repository. Removing
them would be a change to four other bounded contexts made under cover of
a correction, and this round does not make it.

**2. The PACK-28 implementation report's inventory figure is corrected.**
The report stated `63 added / 25 changed / 0 removed` for PACK-27C1 →
PACK-28. Independent byte comparison found `63 / 24 / 0`, and the
independent figure is right. The cause is recorded rather than glossed:
the inventory was computed before `frontend/web-shell/tsconfig.tsbuildinfo`
— a `.gitignore`d incremental build cache regenerated by running the
frontend build — was restored to its entering bytes, and the stale count
was never recomputed afterwards. The delivered archive was correct; the
number describing it was not.

PACK-28C1 recomputes the complete inventory from exact bytes and reports
actual files, directory entries and total ZIP entries as three distinct
figures, because an inspection comparing a file count against an entry
count without distinguishing them finds a discrepancy that is not one.

**FIR IDs implemented:** none. This is a correction round and closes no
future requirement.

**FIR IDs superseded:** `FIR-PUB-004`, by ADR-113. It recorded the removal
of the four unused declarations as future work; the removal happened here,
so it is no longer outstanding work. The entry is demoted to `superseded`
rather than deleted — section 1.2 forbids silent deletion — and the
identifier is retired rather than reused.

**FIR IDs partially advanced:** none beyond what PACK-28 already recorded.

**FIR IDs intentionally left unchanged:** `FIR-PUB-001`, `FIR-PUB-002`,
`FIR-PUB-003`, `FIR-CONFLICT-001`, `FIR-CONFLICT-002`, `FIR-ID-001`,
`FIR-AUTH-001`, `FIR-DATA-004`, `FIR-REL-001`, `FIR-TEST-002`,
`FIR-READY-001`, `FIR-LEGAL-001`, `FIR-CTRL-001`, `FIR-ROADMAP-011`,
`FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`, `FIR-MOBILE-001`,
`FIR-API-001`, `FIR-VOTE-CRYPTO-001`, and every other substantive entry.

**`FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open and are explicitly
not closed**, exactly as PACK-28 recorded.

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** none. Neither finding
is future work: both were fixed in this round.

**Preserved unchanged:** the publication lifecycle and domain semantics,
the minimisation and redaction design, the authorization and separation-of-duties
semantics, the event and deadline registries, all four frontend routes,
the Voting Client architecture, exactly ten workspaces and ten origins, the
twelve open decisions, and the five frozen PACK-16D artefacts.

**Round status:** correction candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent
party for this correction, and this record does not claim a PASS.

## 1.54 Round record — PACK-28C2 independent verifier runtime dependency correction (2026-08-10)

**Round:** surgical correction. **Business scope: NONE.** PACK-28 was not
redesigned and no publication-domain logic was reimplemented. Repository
version unchanged at `0.30.0`; canon unchanged at `0.8.0`; compatibility
ceiling unchanged at `<0.31.0`. Entering baseline:
`EPD2_PACK-28C1_CANDIDATE_0.30.0.zip`, SHA-256
`f5f570322868f500d6aa674c60456d9b44643f2eb47887caa446a7c5a5d34dc9`.

Authoritative Windows CI, run against the PACK-28C1 candidate, exposed one
real inherited dependency defect. `uv sync --all-groups --frozen` passed;
verifier-runtime preflight then failed with `VERIFIER_RUNTIME_UNAVAILABLE`
because the dedicated verifier environment could not import
`cryptography.hazmat.primitives.asymmetric.ed25519`. Twenty-nine ordinary
pytest failures and two PACK-17C suites followed from that one preflight
failure. The publication-domain tests were never the cause.

**The root cause is ownership, not the publication domain.**
`packages/python/epd2-independent-verifier` declares
`cryptography>=46.0.0` in its own manifest, but it was not a member of the
uv workspace. uv locks members; a directory that is not a member is
invisible to `uv lock`. `uv.lock` therefore carried no record of the
verifier's requirement, and an inventory of the shipped PACK-28C1 lock
shows exactly one package declaring `cryptography`:
`epd2-voting-service`. The verification toolchain's pin was a side effect
of a source-domain service's dependency list — the same class of accident
PACK-28C1 had just removed from `transparency-service`, in a place nobody
had looked.

**ADR-114 resolves `OD-P17CC1-01` and takes both halves of it.**
PACK-17C-C1 recorded workspace membership and the managed dedicated
environment as alternatives and deferred the choice to a networked round.
They are not alternatives. The verifier is now a workspace member **and**
keeps its managed dedicated environment: membership is what puts the
verifier's own `cryptography` edge into `uv.lock`, and the managed
environment is what keeps the verifier out of the project environment.

- Added to `[tool.uv.workspace].members` and to nothing else.
- **Not** added to the root `[project].dependencies`, and no package in
  this repository declares a dependency on it — a repository test refuses
  the edge. `uv sync --all-groups --frozen` installs no part of the
  verifier into the project environment, which was verified rather than
  assumed.
- **No `[tool.uv.sources]` entry.** That table maps declared dependencies
  onto workspace packages; nothing declares this one.
- `uv.lock` regenerated with `uv lock`, never edited. The diff is exactly
  one added package block of twelve lines plus one added name in the
  workspace member list; no existing resolution moved.
- `scripts/verifier_runtime.py` now resolves the pin **through the
  verifier's own edge** — the verifier's `requires-dist` must name
  `cryptography`, the dependency must have a resolved block, and the
  resolved version must satisfy the declared specifier — instead of taking
  the first `cryptography` block it finds in the file.
- The dedicated environment is built from locked state with
  `uv sync --package epd2-independent-verifier --frozen --no-editable --no-dev`,
  which needs no index access once the project has been synced.
  That is the whole of the Windows fix. The pre-existing
  venv-plus-wheelhouse path is preserved as a fallback for hosts without
  uv, and still fails closed.

**Nothing about verifier isolation was weakened**, and each guarantee is
re-asserted by test: exact absolute executable path; dedicated environment
outside the repository; no ambient `PYTHONPATH` or `PYTHONHOME` in the
build child; no `--system-site-packages`; `--no-editable`, so no source
directory reaches the environment; the exact `0.1.2` version gate; the
locked-version comparison with deviations recorded; the Ed25519 smoke test
that verifies a real signed archive; and no failure path that degrades to a
skip. The verifier is not mocked on the authoritative path.

**A second, latent defect was found and fixed while proving the first.**
The verifier's `[tool.hatch.build.targets.wheel] force-include` table
re-added `corpus_data` at archive paths the declared `packages` root
already occupied, which hatchling refuses outright — so the declared build
backend could not build the package at all. Nothing noticed for three
rounds because every build went through the offline wheel builder, whose
own docstring states that the declared backend is authoritative where the
two disagree. The redundant table is removed and the two wheels now have
identical payloads, twenty-four files, name for name. The verifier's
package version stays `0.1.2`: its behaviour did not change.

**FIR IDs implemented:** none. This is a correction round and closes no
future requirement.

**FIR IDs superseded:** none. `FIR-PUB-004` stays `superseded` by ADR-113,
untouched by this round.

**FIR IDs partially advanced:** none.

**FIR IDs intentionally left unchanged:** `FIR-PUB-001`, `FIR-PUB-002`,
`FIR-PUB-003`, `FIR-CONFLICT-001`, `FIR-CONFLICT-002`, `FIR-ID-001`,
`FIR-AUTH-001`, `FIR-DATA-004`, `FIR-REL-001`, `FIR-TEST-002`,
`FIR-READY-001`, `FIR-LEGAL-001`, `FIR-CTRL-001`, `FIR-ROADMAP-011`,
`FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`, `FIR-MOBILE-001`,
`FIR-API-001`, `FIR-VOTE-CRYPTO-001`, and every other substantive entry.

**`FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open and are explicitly
not closed.**

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** none. Both findings
were fixed in this round rather than recorded as future work — the same
disposition rule PACK-28C1 applied to `FIR-PUB-004`.

**Open decisions:** `OD-P17CC1-01` **closed** by ADR-114. Its record in
`docs/packs/PACK-17/PACK-17C-C1-OPEN-DECISIONS.md` is annotated in place
and not rewritten. No other open decision moved; the twelve PACK-28 legal
decisions are all still `OPEN`.

**Preserved unchanged:** ADR-113 and the two-dependency
`transparency-service` boundary; the publication lifecycle and domain
semantics; minimisation and redaction; authorization and
separation-of-duties; the event and deadline registries; all four frontend
routes; the Voting Client architecture; exactly ten workspaces and ten
origins; the five frozen PACK-16D artefacts; `package-lock.json`.

**Round status:** correction candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** This round was prompted by an
authoritative Windows CI result, but no Windows CI run, no AVH run and no
independent inspection was performed **by this round**, and none is claimed.

## 1.55 Round record — PACK-29 parliamentary interface and open representative desk (2026-08-11)

**Round:** business scope. Repository version `0.30.0` -> `0.31.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.31.0` -> `<0.32.0`.
Entering baseline: `EPD2_PACK-28C2_CANDIDATE_0.30.0.zip`, SHA-256
`c8b6b26c2fc9a261a4403875fce02ccd8217bb60f00769d653ae0b03ea035386`. No
code was merged from the PACK-28 or PACK-28C1 candidates, from PACK-27, or
from any other repository archive.

**One new bounded context**, `services/representative-desk-service`, and a
leaf in both directions: its manifest declares exactly `epd2-core` and
`epd2-audit-core`, no module imports another service's package, and
nothing in the repository imports it. It was not placed inside
`office-mandate-service`, `casework-service`, `transparency-service`,
`correspondence-service`, `governance-service` or `assembly-service`,
because a desk that lived inside any of them would inherit that context's
authority — and the whole difficulty of a representative desk is that it
has almost none.

**The central invariant is a shape, not a rule.**

```text
governed democratic decision -> representative response / alignment /
                                divergence / explanation
```

Never `-> mandatory state transition`. No command in this service takes a
governed decision reference except the three that record a
representative's own statement about one; there is no port to a chamber,
no parliamentary credential anywhere, and
`assert_no_automated_parliamentary_execution`,
`assert_decision_reference_is_not_instruction` and
`assert_alignment_not_computed` are **unconditional** refusals rather than
conditional checks. A repository test asserts the unconditionality from
the AST, because a refusal that grew a permitting branch would still be
named, still be imported and still be documented.

**Divergence is a governed value and not an offence.** No dataclass in
this service carries a field named for a sanction, penalty, misconduct
finding, breach or disciplinary consequence — asserted by an AST scan
across every class in the package, not by convention. The divergence event
carries `constitutes_misconduct_finding: false`, and `record_divergence`
deliberately takes **one** principal where every other consequential act
takes two: a second signature on a divergence record is a second person
who can decline to give it, and the record they would be suppressing is
the record of a representative acting against an internal majority.

**Desk activation is not a mandate.** A desk is activated only against an
`ACTIVE` office-mandate authority obtained through a port, and the
activation confers no seat, verifies no election, extends no term and ends
nothing. `assert_desk_is_not_parliamentary_mandate` and
`assert_office_reference_is_not_desk_activation` refuse both readings by
name, and `assert_no_office_lifecycle_duplication` refuses a field that
would let PACK-20's lifecycle be re-implemented here.

**There is no `VERIFIED` parliamentary status.** The strongest
`VerificationStatus` offers is `SOURCE_ATTESTED`, which means only that
the publisher said so, and `ExternalParliamentaryRecordRef` has no
`content`, `title`, `text` or `result` field. This repository points at a
chamber's record; it does not hold one, and it does not certify one.
`FIR-DESK-001` records the authenticity work that would be needed before it
could.

**One way out.** Everything public leaves through the PACK-28 publication
boundary. `PublicationBoundaryPort` has a single method
`submit_candidate`; there is no `publish` and no `approve` anywhere in
this service; and the seven `NEVER_PUBLISHABLE_SUBJECTS` — an intake, a
response draft, an internal note, private correspondence, a protected
report, conflict evidence and a staff assignment — have no candidate
builder at all. An internal answer, commitment or explanation is not a
public record until it has passed that boundary.

**Referral is not routing.** A desk may record that an inquiry is not its
business and that it asked somebody else to take it, with a disposition
and a status. Resolving a competent authority and tracking onward handling
is PACK-33 and stays a separate bounded context;
`assert_referral_is_not_routing` refuses an attempt to build it here, and
`NoWrongDoorRoutingNotImplementedError` raises rather than degrading into
a partial implementation nobody would replace.

**No intake carries a `handled` flag.** An inbound item ends in a named
governed state with a governed reason, or it is still open. A boolean
would let a desk close a constituent's question without saying what became
of it, and the constituent is the person least able to find out.

**Counts, never scores.** `DeskActivitySummary` computes no rate, ratio,
index or percentage, and `projections.py` contains no division at all. A
responsiveness rate would be the most-read number on a public
representative surface and would be a number this repository computed
about a named person from data it knows to be incomplete. `FIR-DESK-005`
and `OD-P29-12` hold the question.

**One reserved action, two reserved event types, seven reserved deadline
kinds**, each with a stated reason naming an open decision, a runtime
refusal and a two-direction call-site scan — because set membership proves
classification and only a scan proves wiring. Nineteen statutory-sounding
answering periods are refused by name.

**German applicability stays OPEN.** No constitutional article, no
Fraktionsdisziplin rule, no chamber rule of procedure and no disclosure
statute is encoded as an implementation fact.
`assert_constitutional_rule_not_encoded` refuses the attempt and names the
decision, and `OD-P29-02` is unresolved **in both directions**: this
repository asserts neither that a representative is bound by an internal
majority nor that they are free of it.

**Frontend:** seven routes (`P29-R-073` … `P29-R-079`) inside the existing
ten workspaces — five public in WS-10, one protected in WS-06, one in
WS-07. No eleventh workspace, no eleventh origin, nothing in WS-03, and no
path into the Voting Client.

**FIR IDs implemented:** none. No future requirement in this register is
closed by this round. In particular section 16's `FIR-REP-001` (Open
Representative Desk) and `FIR-REP-002` (Parliamentary Interface) are the
captured requirements this round works towards and **neither is closed**: a
desk that is `NOT LEGALLY ACTIVATED`, whose periods are four enforced
windows and seven reserved ones, and whose parliamentary interface is a set
of unverified pointers, is a reference implementation of the shape rather
than the capability.

**`FIR-REP-003` and `FIR-REP-004` are explicitly not advanced.** Lobbying
and external-meeting disclosure belongs to PACK-35, and this pack declares
`LobbyingDisclosureRef` for the sole purpose of letting
`assert_lobbying_disclosure_unavailable` name it. Citizen-office routing
belongs to PACK-33; recording that a desk asked another body to take a
matter is not routing it, and `assert_referral_is_not_routing` refuses the
conflation by name. Neither entry moves, and this record claims neither.

**FIR IDs partially advanced:** `FIR-REP-001` and `FIR-REP-002` — a
governed desk, its intake, its commitments, its positions and its
parliamentary references exist as a reference implementation; neither is
closed. `FIR-ID-001` — enforced at one more
boundary; desk identifiers are derived locally, `assert_not_person_identity`
always raises, and two desks cannot be correlated. `FIR-AUTH-001` — a
thirty-six-action registry with an enforced wired/reserved partition, six
never-granted roles and an incompatible-role matrix. `FIR-DATA-004` —
nineteen governed payload walks run at both the command and the emission
boundary. `FIR-TEST-002` — two-direction call-site scans, an
unconditionality scan over every always-raising refusal, and exhaustive
state-machine totality tests. None of the four is closed.

**FIR IDs intentionally left unchanged:** `FIR-REL-001`, `FIR-READY-001`,
`FIR-LEGAL-001`, `FIR-CTRL-001`, `FIR-ROADMAP-011`, `FIR-SEC-SECRET-001`,
`FIR-INFRA-SOV-001`, `FIR-MOBILE-001`, `FIR-API-001`,
`FIR-VOTE-CRYPTO-001`, `FIR-PUB-001` through `FIR-PUB-003`, and every
other substantive entry.

**`FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open and are explicitly
not closed.** Consuming a conflict outcome as a governed reference — which
is what this pack does before a desk may act on a matter — is not
participation-time recusal enforcement, and it is not a governed decision
by an owning context that cites a conflict outcome. PACK-29 has neither
the authority nor the source-domain reach to advance either, and this
record claims neither.

**PACK-33, PACK-34 and PACK-35 are explicitly not started.** No-wrong-door
routing, delegation reputation and lobbying disclosure are each named,
each refused by an exception that exists only to be raised, and each left
to the bounded context that will own it. `LobbyingDisclosureRef` is
declared so that `assert_lobbying_disclosure_unavailable` can name it, and
for no other reason.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**New FIR IDs created by implementation discovery:** `FIR-DESK-001`
(external parliamentary source authenticity and provenance verification),
`FIR-DESK-002` (governed answering periods and representative desk service
targets), `FIR-DESK-003` (governed staff worklist and intake assignment),
`FIR-DESK-004` (governed evidence path for material arriving from the
public) and `FIR-DESK-005` (public representative activity measures). A new
prefix rather than the next free `FIR-REP-nnn`: section 16's `FIR-REP-001`
through `FIR-REP-004` are the _captured business requirements_ this pack
works towards, and numbering discoveries into the same series would make
the register's own identifiers ambiguous about which is which. One
further entry, `FIR-LIC-OPS-001` (open-core licensing, managed operations
and deployment boundary), is created by **specification** rather than by
implementation discovery and is **not** implemented, prepared or partially
built by this round.

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent
party for this candidate, and this record does not claim a PASS.

## 1.56 Round record — PACK-29C1 PACK-28 publication-consumption boundary correction (2026-08-11)

**Round:** correction. Repository version unchanged at `0.31.0`; canon
unchanged at `0.8.0`; compatibility ceiling unchanged at `<0.32.0`.
Entering baseline: `EPD2_PACK-29_CANDIDATE_0.31.0.zip`, SHA-256
`99193be36cd180fb2af455ccd302ceff871b30335bb124a10e5f45aaa08dc6c5`. No code
was merged from any other archive.

**What was wrong.** PACK-29 inherited PACK-28's invariant
`publication candidate != publication decision != published projection` and
broke it in four places. `PublicationClassification.PUBLIC_CANDIDATE` — a
statement by the desk that it would _like_ something published — was used
as the filter deciding what a public surface rendered.
`read_public_projection` built that rendering directly from the desk's own
positions, commitments, alignments, activity references and open tables,
with no PACK-28 decision, no minimisation, no approval and no version
anywhere in the path. `PublishedProjectionRef` was declared and nothing
produced or consumed one, so the documented chain stopped at the candidate.
And all seven frontend routes, including the five public ones, named
`representative-desk-service` as their backend, which made every public
representative surface structurally capable of bypassing PACK-28.

**The correction, and what it deliberately is not.** `PUBLIC_CANDIDATE` now
gates _offering_ and nothing else: the predicate is `_is_offerable`, the
object it builds is `DeskCandidateMaterial` carrying
`is_published_projection = False` and no projection reference or version,
and it feeds `offer_candidate`. `read_public_projection` is removed;
`refuse_public_projection_from_internal_state` and
`refuse_candidate_material_as_public_projection` raise unconditionally
where it was.

A new module `published.py` completes the chain. `PublishedDeskProjectionLink`
holds the projection reference, the version PACK-28 assigned and the
candidate it came from — and **no rendered content at all**, because a
second copy of a published projection maintained in this service is the
copy that goes stale and the copy the public reads. A new read-only port
`PublishedProjectionPort` resolves what PACK-28 published; it is separate
from `PublicationBoundaryPort` so that the outbound port keeps exactly one
method and "this service cannot publish" stays checkable by counting. A new
command `record_published_projection` — two principals, `HIGH` assurance —
records the link, and refuses rather than storing a placeholder when nothing
was published.

The correction was **not** made by importing `transparency-service`. That
would end the leaf property ADR-115 established, and a leaf that imports one
service imports the next one the same way. The manifest still declares
exactly `epd2-core` and `epd2-audit-core`, and NC-P29-48 asserts it.

**A published version does not move when an internal record does.**
`assert_publication_not_rewritten` refuses re-pointing an existing version
at different material and refuses a chain that moves backwards;
`assert_projection_version_known` fails closed on an absent or defaulted
version. NC-P29-39 drives the whole shape: a position published as `V1`, then
superseded internally with a commitment added, still reads `V1` at the same
reference — and moves only when PACK-28 publishes `V2`.

**Frontend ownership corrected.** The five public routes name
`transparency-service`; the two protected ones — intake worklist and
oversight — still name `representative-desk-service`, which is correct.
Every public view type carries a required `publishedProjection` block; the
protected worklist carries none, and a test asserts its absence. No eleventh
workspace, no eleventh origin, no second transparency service, and frontend
authorization is not used as the boundary.

**Twelve negative controls added**, six behavioural and six structural, and
the structural ones are AST walks and file scans rather than
documentation-string assertions. Two existing tests that encoded the defect
were corrected rather than deleted, and both now assert strictly more than
before.

**Documentation corrected, without changing behaviour to suit it.**
`PACK-29-FRONTEND.md` claimed both "no input, no form, no button that
writes" and "public intake is a bounded, markup-free text field". The first
was accurate: **this round exposes no public intake form**, and the second
described the backend control as though a surface existed for it.
`FIR-DESK-004` carried the same error and is reworded. **No form was added
to make either document true**, and the backend `submit_intake` capability
with its bounded-input controls is unchanged.

**FIR IDs implemented:** none. `FIR-REP-001` and `FIR-REP-002` remain
partially advanced and open; `FIR-REP-003` and `FIR-REP-004` remain
explicitly not advanced; `FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain
open.

**FIR IDs partially advanced:** `FIR-PUB-003` — governed consumption of
published projections by a parliamentary interface now has one real
consumer, by reference, with the version carried. It is **not** closed:
one consuming context is not the governed consumption model that entry
describes.

**FIR IDs intentionally left unchanged:** `FIR-DESK-001`, `FIR-DESK-002`,
`FIR-DESK-003`, `FIR-DESK-005`, `FIR-LIC-OPS-001`, `FIR-ID-001`,
`FIR-AUTH-001`, `FIR-DATA-004`, `FIR-TEST-002`, `FIR-REL-001`,
`FIR-READY-001`, `FIR-LEGAL-001`, `FIR-CTRL-001`, `FIR-SEC-SECRET-001`,
`FIR-INFRA-SOV-001`, `FIR-MOBILE-001`, `FIR-API-001`,
`FIR-VOTE-CRYPTO-001`, and every other substantive entry.
`FIR-DESK-004`'s **wording** is corrected; its status, priority, scope,
target and dependencies are untouched.

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** none. The four defects
this round fixes are corrections to PACK-29's own delivery, not newly
discovered future requirements.

**Preserved unchanged:** ADR-115 and ADR-116; the desk lifecycle;
commitments; positions; alignment, divergence and explanation; Open Table;
parliamentary references; the intake lifecycle; the PACK-33 and PACK-35
boundaries; authorization and separation of duties; identity minimisation;
deadlines; repository `0.31.0`; canon `0.8.0`; exactly ten workspaces and
ten origins; the Voting Client; the leaf property; the PACK-28C2
verifier-runtime architecture; the five frozen PACK-16D artefacts;
`uv.lock` and `package-lock.json`, both byte-identical.

**Round status:** correction candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent party
for this correction, and this record does not claim a PASS.

## 1.58 Round record — PACK-31 constitutional and ethics oversight (2026-08-11)

**Round:** business scope. Repository version `0.32.0` -> `0.33.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.33.0` -> `<0.34.0`.
Entering baseline: `EPD2_PACK-30_CANDIDATE_0.32.0.zip`, SHA-256
`6c09508b1cb4573e8a002a6160d369d9cc1f9c1cd4fa5ca494eef7dc1bac88a2`. No code
was merged from any other archive.

**What this round adds.** One new leaf bounded context,
`services/oversight-service`, declaring exactly `epd2-core` and
`epd2-audit-core` and imported by nothing. Twenty-two modules covering
intake, admissibility, competence, assignment, reviewer independence,
evidence, panels, findings, dissent, recommendations, corrective action,
reopening, supersession, closure and publication candidacy.

**The central invariant.** `oversight != authority over every domain`. A
body that reviews everything and may change nothing is an oversight body. A
body that reviews everything and may change anything is the organization.
There is no third position, and this round is arranged around keeping the
first one expressible after the eighteenth month — when the review that
matters lands and somebody points out that the finding would be much more
useful if it just took effect.

**Four properties carry the round.**

_Competence is a profile, not a status._ `assert_competent` checks six
dimensions positively — organization, level, subject domain, review
category, establishing basis, effective period — and refuses a case no
profile covers. A body constituted to review ethics conduct in one
Kreisverband is not thereby competent over a Bund-level constitutional
question. `assert_not_competent_for_everything` refuses a profile reaching
every domain and every category, which is how a supreme organ gets
assembled: one reasonable extension at a time, by nobody objecting. There
is deliberately **no containment rule between organizational levels** — a
Bund profile covers Bund cases and the absence is `OD-P31-06` rather than
an omission, because whether a national body may review a regional one's
decision is a question about how an organization is constituted and not a
fact about hierarchy. ADR-122.

_Ethics and law are two fields._ `LegalAssessment` and `EthicsAssessment`
are separate enumerations sharing no member, both mandatory on every
finding, both defaulting to `NOT_ASSESSED`. Neither contains `VIOLATION`,
`GUILTY`, `CRIMINAL`, `SANCTION`, `INVALID`, `ANNUL`, `UNLAWFUL`,
`UNCONSTITUTIONAL` or `REMOVAL`. A single `status` field would be smaller
and it is the exact shape of this domain's central failure: a body that was
uncomfortable with how something was handled writes the only word
available, and eighteen months later the record says it found a violation.
The merge happens in the data model rather than in anybody's reasoning,
which is why no amount of care in drafting prevents it. ADR-123.

_Finalisation is not activation._
`assert_finding_status_is_not_legal_effect` runs at the exact point a
finding is finalised and refuses any legal effect other than `OPEN`. Every
record this pack produces carries `OPEN`.
`oversight.binding_determination.issue` and
`oversight.legal_effect.activate` are registered, reserved and permitted to
nobody. `legal activation != technical completion`, and a system where
completing a workflow produces a legal event has made that decision without
anybody taking it.

_Nothing here writes to another domain._ `OversightPorts` declares no port
with a write method into any reviewed context. There is no
`apply_corrective_action_to_source_domain`, and `assert_no_direct_execution`
is the named refusal for anybody building one. The failure this prevents is
not malice: it is a body that has identified something obviously wrong, in a
domain whose owner will take weeks, with a function one call away.

**Separation of duties, and independence on top of it.** Intake screener,
admissibility decider, case assigner, reviewer, rapporteur, finding checker,
panel chair, corrective-action verifier, publication liaison and auditor are
ten distinct roles across thirty-one, eighteen of which the table grants
nothing to and which exist so that holding one can be refused. Forty-one
incompatible pairs. `assert_reviewer_independence` is a separate control
from all of it: four principals are compared against the reviewer — the
subject, the original decision-maker, the original approver and the
technical operator of the reviewed act — and each is a fact about the
decision under review rather than about the reviewer, which is why they are
presented per case. Independence is established, never inferred from a
title.

**Attendance is not entitlement.** `PanelComposition` distinguishes members
who carry a vote from participants who do not, and `assert_quorum` counts
only distinct, entitled, participating members. The ordinary failure is not
a forged panel: it is a real meeting, short a member, with the secretary and
an external expert in the room and minutes recording five people present.
`OVERSIGHT_SECRETARY`, `OVERSIGHT_OBSERVER` and `EXTERNAL_EXPERT` are
granted nothing and refused from every count.

**Conflicts are consumed, never determined.** PACK-27 owns conflict and
recusal truth. This service reads an applicability result and refuses on
absent, undetermined or unreadable — and takes no urgency parameter, no
override and no default, because every real argument for skipping the check
is an argument about time. `assert_conflict_not_determined_here` refuses
making a second determination by name.

**Corrective action cannot be short-circuited.** No edge from `ISSUED` to
`VERIFIED`, none from `ACKNOWLEDGED`, none from
`IMPLEMENTATION_REPORTED`. Verification passes through
`VERIFICATION_PENDING`, which is a state somebody moves a record into.
`assert_sequence_not_skipped` checks the same property against the required
sequence rather than against the transition table, so the guarantee does not
rest on one table being read correctly.

**Boundaries kept.** PACK-12 owns privileged access and break-glass; this
service reviews its use and owns none of it. PACK-20 owns offices and
mandates, PACK-21 assemblies, PACK-22 delivery, PACK-23 casework and
protected reporting, PACK-25 procurement, PACK-26 people administration,
PACK-27 conflicts, PACK-28 publication, PACK-29 the representative desk and
PACK-30 emergency governance. No command here mutates any of them; a
repository test drives every one of the fourteen source-domain refusals by
name. PACK-32 and PACK-33 are not implemented and this round creates no
dependency towards them.

**Frontend.** Six routes, `P31-R-087` through `P31-R-092`, inside the
existing ten workspaces and ten origins. No eleventh workspace, no eleventh
origin, no route in WS-03 and no `/vote` path. The public route names
`transparency-service`, not the owning service.

**FIR IDs implemented:** none. No future requirement in this register is
closed by this round. In particular `FIR-CONFLICT-001` and
`FIR-CONFLICT-002` are **not** closed: this service refuses to act without a
PACK-27 result, which is a governed consumption, and the enforcement point
for a recorded recusal is in the domain where the person would otherwise
participate. `FIR-CTRL-001` is not closed either: every oversight action
carries authority, competence, scope, assurance, maker/checker, independence
and evidence so that a later Control Plane does not have to redo the
architecture, and preparing for a control plane is not building one.

**FIR IDs partially advanced:** `FIR-OPS-001` and `FIR-TIME-001` — governed
operational windows and a single comparison site for instants now exist in
one more context. `FIR-PUB-003` — one more consumer reads published
projections through the PACK-28 boundary rather than an internal store.
None is closed.

**FIR IDs intentionally left unchanged:** `FIR-ID-001`, `FIR-AUTH-001`,
`FIR-REL-001`, `FIR-RES-001`, `FIR-DATA-004`, `FIR-TEST-001`,
`FIR-TEST-002`, `FIR-READY-001`, `FIR-LEGAL-001`, `FIR-CTRL-001`,
`FIR-ROADMAP-011`, `FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`,
`FIR-MOBILE-001`, `FIR-API-001`, `FIR-VOTE-CRYPTO-001`, `FIR-CONFLICT-001`,
`FIR-CONFLICT-002`, `FIR-PUB-001`, `FIR-PUB-002`, `FIR-PUB-003`,
`FIR-DESK-001` through `FIR-DESK-005`, `FIR-LIC-OPS-001`, `FIR-EMERG-001`
through `FIR-EMERG-004`, and every other substantive entry.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**New FIR IDs created by implementation discovery:** `FIR-OVERSIGHT-001`
(subject procedural rights and the review of a finding), `FIR-OVERSIGHT-002`
(public oversight measures and the method that would govern them),
`FIR-OVERSIGHT-003` (external authority interaction and the referral
channel), `FIR-OVERSIGHT-004` (oversight legal activation profiles) and
`FIR-OVERSIGHT-005` (machine-assisted analysis as governed oversight
evidence).

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins; the Voting Client; the PACK-28C2 verifier-runtime architecture and
the independent verifier's dependency ownership; the five frozen PACK-16D
artefacts, byte-identical; `package-lock.json`, byte-identical; every
existing FIR identifier and its history; ADR-000 through ADR-120.

**Re-aimed rather than deleted:** the next-pack scope guards in
`test_pack23_casework_governance.py`,
`test_pack24_protected_reporting_governance.py`,
`test_pack25_procurement_governance.py`,
`test_pack25c1_harness_integrity.py` and
`test_pack26_people_administration_governance.py` now name PACK-32, which is
the treatment every round since PACK-24 has given them.

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent party
for this candidate, and this record does not claim a PASS.

## 1.57 Round record — PACK-30 emergency governance and crisis controls (2026-08-11)

**Round:** business scope. Repository version `0.31.0` -> `0.32.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.32.0` -> `<0.33.0`.
Entering baseline: `EPD2_PACK-29C1_CANDIDATE_0.31.0.zip`, SHA-256
`4371ffe99f3e0894266b3d62ff07225b39b15e9919901f2ad60d476a6aee7bdd`. No code
was merged from any other archive.

**What this round adds.** One new leaf bounded context,
`services/emergency-governance-service`, declaring exactly `epd2-core` and
`epd2-audit-core` and imported by nothing. It implements canon section
19.1's `EmergencyAction` — the entity `docs/architecture/data-ownership.md`
has carried as "Not implemented" against a "Governance / Crisis Service"
since PACK-02, and which no previous pack owned. Canon's eight measure
types and seven statuses are carried exactly, extended by two operational
modes this repository needs.

**The central invariant.** `emergency governance != emergency override of
architecture`. A crisis may change which organizational procedures apply,
which routes are open, which of this repository's own deadlines are in
force and which additional controls are required. It does not change what
the architecture permits, and this round is arranged entirely around making
that difference structural rather than stated.

**Three properties carry the round.**

_Expiry is a type signature, not a validation step._ `EmergencyDeclaration`,
`EmergencyMeasure` and `ExceptionalGrant` have no representation without an
expiry: a required field, no default, no `None` meaning indefinite, no `0`
meaning unlimited, refused at construction if naive or not after the start,
and bounded again by a governed maximum from the policy bundle.
`assert_expiry_within_policy` is the second half, because a mandatory expiry
that accepted any value is satisfied by a date nobody expects to reach.
Expiry is _computed_ on read — `is_expired`, `is_active` — rather than
stored as a flag, because a stored flag goes stale in one direction only and
the job that would correct it is the job that does not run during an
incident. ADR-119.

_There is no generic override._ No `override(action)` API, no `force`
parameter, no `EMERGENCY_ADMIN`. `assert_no_universal_role` computes each
role's reachable action set and refuses any role reaching all of them, so
renaming does not defeat it. Sixteen acts are prohibited outright by a
`frozenset` built at import from its own enumeration, reachable by no
feature flag, policy bundle, emergency category or system state, and held in
a module separate from `authorization.py` because a prohibition living
beside permissions drifts into being a permission with a very restrictive
role list. ADR-120.

_Voting has no emergency exception._ No category, measure kind, authority,
break-glass session, administrator role or state of this service identifies
a voter, reaches ballot-level identity linkage, produces an intermediate
tally, disables Voting Client isolation or merges eligibility determination
with credential issuance. Canon's `ballot_cancel` is declared and
**reserved** (`OD-P30-07`): pausing a ballot freezes activity and determines
nothing, and determining that a democratic act did not validly happen is
standing this repository does not have. `CREDENTIAL_REVOCATION`
(`OD-P30-08`) and `FORCE_LOGOUT` (`OD-P30-09`) are reserved for the same
kind of reason.

**Separation of duties is stronger under emergency, not weaker.** Declarer,
assessor, approver, executor, reviewer and technical operator are six
distinct roles across nineteen, ten of which the table grants nothing to and
which exist so that holding one can be refused. Twenty-two incompatible
pairs. `assert_declarer_is_not_proposer` catches what the maker/checker
field cannot, because the proposer acted on an earlier record.
`assert_distinct_principals` refuses a duplicate counted twice — one person
presenting two authorities is the cheapest possible forged quorum and from
the outside it looks exactly like two people agreeing.

**Recovery is evidenced.** `emergency ended != system automatically normal`.
`verify_recovery` refuses while any reconciliation task is outstanding and
refuses while any exceptional grant is still active, which is the check that
stops a crisis becoming a standing privilege escalation nobody remembers
approving. `INCOMPLETE_RECORDED` is a real terminal ending, because the
alternative is a recovery marked complete because the review meeting was the
last chance to close it.

**Deadline extension is modelled narrowly.** Two of eleven kinds are
extendable, both operational, and no statutory period is extendable at all.
An extension requires the kind's own policy, an authorized approver with a
second principal, a reason and evidence, a bound from the policy bundle, and
the original retained in history —
`assert_original_retained` and the append-only `extensions` tuple. The
record this prevents is "the deadline was met".

**Boundaries kept.** PACK-12 owns privileged access and break-glass and
nothing here weakens its evidence, expiry, scope, out-of-band notification,
maker/checker or post-use review. PACK-17D owns security incidents;
`security incident != governance emergency` in both directions. PACK-21 owns
assemblies. PACK-22 owns delivery. PACK-27 owns conflicts and recusal.
PACK-28 is the single path outward and its minimisation, redaction and
approval are identical during an emergency —
`assert_minimisation_unchanged_in_crisis` refuses the faster path by name.
PACK-29's representative desk stays separate. PACK-31 is not implemented and
this round creates no dependency towards it.

**Frontend.** Seven routes, `P30-R-080` through `P30-R-086`, inside the
existing ten workspaces and ten origins. No eleventh workspace, no eleventh
origin, no route in WS-03 and no `/vote` path. The two public routes name
`transparency-service`, not the owning service — PACK-29C1's correction
adopted from the first line rather than learned again.

**Hardened after an adversarial pass against this round's own claims.**
Four claims were put to an independent reviewer instructed to break them
rather than confirm them: no generic override, mandatory expiry, no
voting exception, and CTRL-01 readiness. Two held; two broke. Nine
findings were fixed, each by making the service stricter — a capability
suspension that could outlive its emergency; a confirmation accepted
after the emergency had ended; a recovery verification that cleared
grants and ignored capabilities; a deadline extension chain uncapped in
count and permitted after the emergency had ended; an unnormalised
principal handle, so `anna` and `Anna` satisfied a two-principal act and
a three-person quorum; four reads that never reached the authorization
port, leaving the `HIGH` assurance on the two evidence reads enforced by
no code path at all; high-impact measures requiring no evidence; a policy
ceiling with no ceiling of its own; and sixteen registry mappings that
were mutable `dict`s. Each is pinned by a test. Two fragilities were
reported and deliberately **not** fixed, and are recorded as limitations
rather than closed: the governed payload walks match key names rather
than payload shape, and `epd2_core.build_event_envelope` is public and
runs no walk.

**FIR IDs implemented:** none. No future requirement in this register is
closed by this round. In particular `FIR-CTRL-001` is **not** closed: every
emergency action already carries authority, scope, assurance, maker/checker
and evidence so that a later Control Plane does not have to redo the
architecture, but preparing for a control plane is not building one.

**FIR IDs partially advanced:** `FIR-OPS-001` and `FIR-TIME-001` — governed
operational windows and a single comparison site for instants now exist in
one more context. Neither is closed: one context is not the operational
model either entry describes.

**FIR IDs intentionally left unchanged:** `FIR-ID-001`, `FIR-AUTH-001`,
`FIR-REL-001`, `FIR-RES-001`, `FIR-DATA-004`, `FIR-TEST-001`,
`FIR-TEST-002`, `FIR-READY-001`, `FIR-LEGAL-001`, `FIR-CTRL-001`,
`FIR-ROADMAP-011`, `FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`,
`FIR-MOBILE-001`, `FIR-API-001`, `FIR-VOTE-CRYPTO-001`, `FIR-CONFLICT-001`,
`FIR-CONFLICT-002`, `FIR-PUB-001`, `FIR-PUB-002`, `FIR-PUB-003`,
`FIR-DESK-001` through `FIR-DESK-005`, `FIR-LIC-OPS-001`, and every other
substantive entry.

**FIR IDs deferred:** none.

**New FIR IDs created by implementation discovery:** `FIR-EMERG-001`
(organizational emergency exercise and drill assurance), `FIR-EMERG-002`
(public emergency measures and the method that would govern them),
`FIR-EMERG-003` (external civil-protection and public-authority emergency
integration) and `FIR-EMERG-004` (emergency legal activation profiles).

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins; the Voting Client; the PACK-28C2 verifier-runtime architecture and
the independent verifier's dependency ownership; the five frozen PACK-16D
artefacts, byte-identical; `package-lock.json`, byte-identical; every
existing FIR identifier and its history; ADR-000 through ADR-117.

**Re-aimed rather than deleted:** the next-pack scope guards in
`test_pack23_casework_governance.py`,
`test_pack24_protected_reporting_governance.py`,
`test_pack25_procurement_governance.py`,
`test_pack25c1_harness_integrity.py` and
`test_pack26_people_administration_governance.py` now name PACK-31, which is
the treatment every round since PACK-24 has given them.

**Round status:** implementation candidate. **Not a FINAL PASS.**

Acceptance status: **candidate only.** Authoritative Windows local CI and
independent AVH 0.1.3 verification have not been run by an independent party
for this candidate, and this record does not claim a PASS.

## 1.59 Documentation-only V14 update — VCRYPTO-01 Entry Gate & Adversarial Security Model (2026-08-11)

**Round:** documentation/governance only. No business PACK is started by this
update. Repository version remains `0.33.0`; Canon remains `0.8.0`; the
accepted PACK-31 code baseline and its SHA-256 remain unchanged.

**Purpose:** strengthen the already existing `FIR-VOTE-CRYPTO-001` without
creating a duplicate FIR. V13 is preserved. This V14 update adds a mandatory
protocol-selection entry gate that must be passed before VCRYPTO-01 may select
or advance a production secret-ballot cryptographic construction to
implementation evaluation.

**FIR IDs implemented:** none.

**FIR IDs intentionally left unchanged:** all FIR IDs except that
`FIR-VOTE-CRYPTO-001` is strengthened by the mandatory gate below; its status
remains `approved` and it remains a future production blocker.

**New FIR IDs created:** none.

### 1.59.1 Core Architectural Filter for VCRYPTO-01 Protocol Selection

VCRYPTO-01 **MUST NOT** select, freeze, recommend for implementation or assume
a concrete cryptographic primitive or hybrid protocol until the candidate has
an explicit formal security model and a proof or rigorous security argument
showing that it satisfies all hard invariants `VCR-HI-01`–`VCR-HI-09` under an
explicitly defined:

- adversary model;
- collusion model;
- trust model;
- key-compromise model;
- time/release model;
- network model;
- cryptographic hardness assumptions.

The evaluation must state the **minimal honest / uncompromised assumption**
that must remain true for every claimed security property. A proof may not
silently assume honesty of the EPD² backend, databases, System Admin, Election
Admin or application clocks.

The following are candidate components only, never predetermined architecture:

- Ciphertext-Policy Attribute-Based Encryption (CP-ABE);
- timed-release / delay encryption;
- Verifiable Delay Functions (VDF);
- threshold beacons / distributed randomness;
- externally released cryptographic secrets;
- hardware-sealed HSM/TEE release keys;
- threshold encryption;
- Distributed Key Generation;
- verifiable mixnets;
- homomorphic tally;
- Zero-Knowledge Proof systems;
- anonymous credentials / blind credentials;
- hybrids built from such mechanisms.

E2E verifiability alone is insufficient. A candidate fails this gate if an
authorized Guardian quorum before the governed release condition can obtain a
plaintext tally, meaningful partial tally, option/candidate trend, tally of an
intermediate ballot-set snapshot, or plaintext contents of an individual cast
ballot.

The candidate also fails if early-tally prevention depends only on application
policy, backend state, a database flag, system clock, feature flag, operator
procedure, organizational promise, or ordinary `k-of-n` threshold possession
where Guardian shares are already usable before release.

```text
intermediate tally prevention must be a property of the cryptographic construction,
not of cooperative application behaviour
```

### 1.59.2 Mandatory Adversarial Entry-Gate Test A — Infrastructure Total Compromise

Before implementation evaluation, every candidate must analyse a threat state
in which **100% of EPD² infrastructure is actively malicious**:

- bare-metal and cloud servers;
- ingress, reverse proxies and load balancers;
- application nodes;
- databases, queues, caches and storage;
- monitoring and deployment systems.

The model also treats System Administrators, technical Security Administrators
within their technical capability, Network Administrators, Database
Administrators, application operators and deployment operators as malicious or
fully compromised.

The adversary may alter server clocks, database records, backend executables,
feature flags and lifecycle state; initiate arbitrary backend requests; replay
old messages; present alternative ballot-set snapshots or election states to
Guardians; and attempt tally before closure.

The candidate must show that infrastructure compromise alone does not provide
the capability to:

1. decrypt cast ballots;
2. obtain an intermediate tally;
3. obtain a politically meaningful partial trend;
4. create usable Guardian decryption material;
5. unlock the governed release condition.

```text
backend total compromise != ballot secrecy compromise
backend total compromise != early tally capability
```

### 1.59.3 Mandatory Adversarial Entry-Gate Test B — Pre-Release Guardian Quorum Collusion

This test is intentionally stronger than the classic `k-1` threshold test.
Before `T_release`, assume collusion by **at least the ordinary election
threshold `k` of Guardians**, while the attacker simultaneously controls all
infrastructure from section `1.59.2`.

Despite possession/control of the ordinary Guardian quorum, the coalition must
remain cryptographically unable to obtain a meaningful plaintext tally before
the governed release condition.

```text
ordinary possession of k Guardian shares before release MUST NOT be sufficient for decryption
Guardian quorum before release != usable decryption authority
```

If a classic threshold primitive is part of the construction, usable
decryption must depend on an additional independent cryptographic release
condition.

### 1.59.4 Independent Release-Domain Requirement

If the protocol uses a time/release mechanism, that mechanism forms a separate
trust domain. It must not be equivalent to:

- the EPD² backend;
- Election Administration;
- System Administration;
- the same Guardian quorum that performs election decryption.

VCRYPTO-01 must state who or what creates release capability, its compromise
threshold, hardness/trust assumptions, whether premature release is possible,
and how premature release can be independently detected.

The design must not claim security against simultaneous compromise of every
trust root unless the selected construction actually proves such a property.
Every candidate must state its **Minimal Honest / Uncompromised Assumption**.

### 1.59.5 Final Ballot-Set Commitment Gate

`T_release` alone is not sufficient for decryption. Before usable decryption
capability exists, the system must have an immutable cryptographic commitment
to the final accepted ballot set.

The `Final Ballot-Set Commitment` must bind at least:

- election identifier;
- election context/version;
- final ballot-set root;
- final ballot count;
- cryptographic profile;
- closure state;
- relevant key epoch/version.

```text
T_release without final commitment != decryption capability
final commitment before T_release != decryption capability
```

Only the permitted combination of both conditions may enable the governed tally
ceremony.

### 1.59.6 Alternative-Snapshot Attack

After authentic final release material becomes available, an adversary may try
to apply it to an earlier ballot-set root, incomplete snapshot, alternative
root, different election, different key epoch or different cryptographic
profile.

Every such attempt must fail cryptographically.

```text
release for final root A cannot authorize decryption of root B
```

The release mechanism therefore must not enable retrospective calculation of
intermediate results from stored pre-closure snapshots.

### 1.59.7 No Individual Cast-Ballot Decryption

The production protocol must expose no normal operation equivalent to:

```text
decrypt individual cast ballot
```

for a Guardian, Guardian quorum, administrator, backend, auditor or verifier.
The key architecture may reveal only plaintext outputs explicitly defined by
the governed final tally protocol.

For homomorphic aggregation, the permitted target is the governed final
aggregate. For a mixnet, plaintext outputs must not enable reversal to the
individual voter. Challenge/spoiled-ballot mechanisms, if required by the
chosen scheme, must be a separate protocol class and must not apply to cast
ballots.

### 1.59.8 Context-Bound Decryption Contributions

Every Guardian/release contribution must be cryptographically domain-separated
and bound, where applicable, to:

- `election_id`;
- `final_ballot_set_root`;
- `crypto_profile`;
- `key_epoch`;
- Guardian/release identity or role context;
- `decryption_purpose`.

Shares/contributions from another election, root, key epoch, cryptographic
profile or purpose, and replayed contributions outside the permitted context,
must be rejected cryptographically rather than merely by application-level
validation.

### 1.59.9 Public Verification Requirement

The transition:

```text
CLOSED
-> RELEASE-ELIGIBLE
-> DECRYPTION CEREMONY
-> FINAL TALLY
```

must produce independently verifiable cryptographic evidence. An independent
verifier must be able to check, without trusting the backend:

- election context;
- final ballot-set commitment;
- that the tally corresponds to that commitment;
- cryptographic profile;
- key epoch;
- correctness of Guardian/release contributions;
- shuffle/aggregation/decryption proofs where applicable;
- absence of an alternative accepted root in the presented evidence;
- correctness of final tally derivation.

```text
provider success != verification evidence
server success != verification evidence
guardian UI success != verification evidence
```

### 1.59.10 Voter-Secrecy and Network-Unlinkability Boundary

VCRYPTO-01 must distinguish:

**A. Ballot Content Secrecy** — the adversary cannot learn plaintext contents
of a cast ballot.

**B. Voter-to-Ballot Unlinkability** — the adversary cannot link a concrete
voter to a concrete cast-ballot record with an impermissible advantage.

Ballot content secrecy is a mandatory cryptographic VCRYPTO entry gate.
Voter-to-ballot unlinkability additionally depends on transport/network
metadata and must be challenged together with the separate Network
Unlinkability work. Encrypted ballots alone do not prove network unlinkability.

### 1.59.11 Formal Failure Criterion

A candidate receives:

```text
VCRYPTO-01 ENTRY GATE — FAIL
```

if any `VCR-HI-01`–`VCR-HI-09` security property lacks a security argument;
its assumptions are undefined; a material threat actor is excluded without
justification; protection exists only in the application layer; a Guardian
quorum can produce an early plaintext tally; an earlier snapshot can be
decrypted after release; an individual cast ballot can be normally decrypted;
context replay is not cryptographically blocked; backend compromise can create
release/decryption capability; or a claimed property silently depends on
honesty of a technical administrator.

No waiver, administrative exception or feature flag may bypass this Entry
Gate.

### 1.59.12 Mandatory VCRYPTO-01 Research Output

Every candidate protocol must produce a decision matrix:

```text
Invariant
-> Threat
-> Primitive
-> Security Assumption
-> Trust Assumption
-> Collusion Threshold
-> Formal Argument / Proof
-> Failure Mode
-> Independent Verification Method
-> PASS / FAIL / UNRESOLVED
```

No `UNRESOLVED` result for `VCR-HI-01`–`VCR-HI-09` permits the candidate to
advance to implementation evaluation.

The governing criterion is:

> Before election closure, the political result must be protected by the
> construction of the cryptographic protocol rather than by operator good
> behaviour. Compromise of EPD² infrastructure and possession of the ordinary
> Guardian quorum before the permitted release condition must not create an
> early-tally capability. Time/release, the final ballot-set commitment and the
> decryption context must be cryptographically bound and independently
> verifiable.

## 1.60 Round record — PACK-32 program formation and deliberation intelligence (2026-08-11)

**Round:** business scope. Repository version `0.33.0` -> `0.34.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.34.0` -> `<0.35.0`.
Entering baseline: `EPD2_PACK-31_CANDIDATE_0.33.0.zip`, SHA-256
`efe5fc4a3b31e09caff88b820b78d02968df0af8c04416bc444724830b595763`. No code
was merged from any other archive.

**What this round adds.** One new leaf bounded context,
`services/program-service`, declaring exactly `epd2-core` and
`epd2-audit-core` and imported by nothing. Twenty-seven modules covering the
programme container and its sections, ideas, proposals, procedural
admissibility, amendments, governed deliberation links, machine-assistance
artefacts, syntheses, similarity suggestions, support signals, candidate
programme versions, adoption, supersession, reopening and publication
candidacy.

**The central invariant.** `deliberation intelligence != political
authority`. Technology can make large-scale political deliberation legible,
and that is worth building. What it must never become is the thing that
decides. The failure this round is arranged against is not a rogue model; it
is a helpful one — a summary that reads well, a duplicate detector that is
usually right, a relevance ordering that surfaces the good proposals. Each
is an improvement, each removes one more human judgement, and the last one
to go is the judgement about what the party stands for.

**Five properties carry the round.**

_Adoption has exactly one route._ `adopt_program_version` is the only
function that produces `ProgramVersionState.ADOPTED`, and it takes a
resolved `AdoptionDecisionRef` as a parameter, so a call site without one
cannot be written. `PROGRAM_VERSION_TRANSITIONS` has no `DRAFT -> ADOPTED`
and no `CANDIDATE -> ADOPTED` edge. `OfferedAdoptionEvidence` enumerates the
six things regularly offered instead — a machine output, a support count, an
argument count, a staff action, an administrator action, and a deadline
expiring with nobody objecting — and `assert_adoption_evidence_is_governed`
raises on every member with no permitted branch. The sixth is the one that
gets built: it is proposed in good faith to keep a congress moving, it looks
like efficiency, and in the record it is indistinguishable from a decision
people made. ADR-124.

_A machine output is an artefact, not an answer._ `AssistanceArtefact`
carries the model reference, the model version, the policy reference, the
output version, the processing record, the sources it was given and a
three-valued review state. An unknown model, policy or output version fails
closed. `SYNTHESIS_TRANSITIONS` has no edge from `GENERATED` to `ACCEPTED`,
and `assert_review_separation` refuses the principal who requested a
generation from accepting it — one person asking a machine to summarise a
discussion and then accepting their own request's output is the whole
failure mode of assisted deliberation, performed by somebody with no bad
intent at all. `AUTOMATED_AGENT_PERMITTED_ACTIONS` is empty. ADR-125.

_The minority survives the summary._ A `DeliberationSynthesis` carrying
opposing arguments must carry the minority positions they represent, and
`assert_minority_positions_retained` checks the synthesis against the
_discussion_ rather than against itself: a summary can be internally
consistent and silent about the people who disagreed. A summary that drops
the three dissenters reads better by every measure, and it is how a party
stops noticing that part of it disagrees.

_Nothing here is deleted._ Withdrawal, closure, supersession and archival
are the four available endings and all four retain the record. An adopted
programme version is immutable from `ADOPTED` onwards — a correction is a
new version with its own decision reference and a predecessor link — and no
store in the service has a delete method or a protocol that could declare
one.

_Publication belongs to PACK-28._ One outbound method offers a candidate;
one read method learns that a publication happened. Only adopted material is
offerable: publishing a candidate version would produce a public page
showing text nobody adopted, indistinguishable on the page from text that
was.

**FIR IDs implemented:** none. PACK-32 closes no future-implementation
requirement. `FIR-CONFLICT-001` and `FIR-CONFLICT-002` are the two a reader
is most likely to think this round closed, because the service refuses to
take a governed programme decision without a PACK-27 result. They are
**not** closed: consuming the outcome in one more domain is not system-wide
enforcement, and the enforcement point for a recorded recusal is in every
domain where the person would otherwise participate. `FIR-VOTE-CRYPTO-001`
remains open and is untouched by this round.

**Master Register V14 carry-forward.** This round incorporates the accepted
Master Future Implementation Register V14, which adds the VCRYPTO-01 entry
gate and adversarial security model at section `1.59` with subsections
`1.59.1`–`1.59.12` and the normative linkage from `FIR-VOTE-CRYPTO-001` to
that gate. The carry-forward is governance only: PACK-32 selects no
production voting cryptographic primitive, implements no Guardian or
time-release mechanism, changes no voting, credential, tally or Voting
Client code, and claims no closure of production voting cryptography.
`services/program-service` was not redesigned because of it.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**FIR IDs intentionally left unchanged:** every other entry in this
register, and three of them deliberately. `FIR-CONFLICT-001` and
`FIR-CONFLICT-002` stay open for the reason stated above.
`FIR-VOTE-CRYPTO-001` stays **OPEN** and its status is not moved by the V14
carry-forward: carrying an entry gate forward is not implementing it, and
recording production voting cryptography as advanced because its
requirements are now written down would be exactly the false closure the
gate exists to prevent. No entry in this register was renamed, deleted or
closed by this round.

**New FIR IDs created by implementation discovery:** `FIR-PROGRAM-001`
(the governed programme adoption decision and the body competent to take
it), `FIR-PROGRAM-002` (machine-assistance model governance and the policy
that would authorise a model), `FIR-PROGRAM-003` (programme publication as
a governed public projection), `FIR-PROGRAM-004` (programme legal
activation profiles) and `FIR-PROGRAM-005` (cross-organizational programme
coordination). All five are in section 40 and none is implemented.

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins; the Voting Client, which gains no PACK-32 route; the PACK-28C2
verifier-runtime architecture and the independent verifier's dependency
ownership; the five frozen PACK-16D artefacts, byte-identical; every
pre-existing FIR identifier, historical entry and round record in this
file, including §1.59 and all twelve of its subsections.

## 1.65 Round record — system-wide corrective closure (2026-08-14)

**Round:** corrective scope. Repository version `0.38.0` -> `0.40.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.39.0` -> `<0.40.0`. Entered
from `EPD2_CTRL-01_CANDIDATE_0.38.0.zip`
(`f39fd60faf79892edf9617d391557ce29ddcfd73fc5d23f7447e380f9eb6e434`) as the
sole authoritative code baseline, against the evidence in
`EPD2_SYSTEM-WIDE_ARCHITECTURE_CHALLENGE_0.38.0.zip`
(`4377b0ccbe2a41273e6dde709111409cb76879441c95519d7b48a43bcc7f4d7c`). No new
bounded context, no new workspace, no new frontend surface, no new authority
and no activated governance decision. PACK-36 is not begun.

**What it closed.** Eight checker rules that could not produce a finding
because the generator wrote their inputs as literal `[]`; a break-glass
prohibition matched on prose, which permitted `suspend a mandate` and refused
`castle defence`; a `CONDITIONAL` separation verdict with no branch in
`assert_roles_compatible`; a console cross product that gave
`FINANCE_OPERATOR` both `finance.entry.record` and `finance.approve` and so
defeated `SOD-CTRL-007` without anybody holding two roles; a
`RoleAssignment.is_active` that never consulted `valid_until`; eleven checker
rules that matched a name, a substring or a self-declaration rather than
verifying a property; and a public read path in `assembly-service` that
returned an `INTERNAL_ONLY` assembly's minutes to a caller presenting
nothing.

**What it did not close, and why.** The caller-asserted authorization
dialect (153 functions across 15 services) is an architectural split, not a
defect this round may correct without redesigning a bounded context.
Cross-context accumulation of roles by one person remains unobservable while
`FIR-ID-001` holds and no assignment mechanism exists. The harvest partition
gaps (183 role members in 15 contexts, 282 actions in 13) are reported per
context with dispositions rather than mechanically eliminated: an
unclassified item grants nothing and is never read as `WIRED`.

**FIR:** no FIR identifier was created, renamed or removed. `FIR-ID-001`
remains `approved` with its negative obligation met. `FIR-VOTE-CRYPTO-001`
is unchanged and untouched: this round selects no production voting
cryptographic primitive, implements no Guardian or time-release mechanism,
changes no voting, credential, eligibility or tally code, and neither begins
nor passes the VCRYPTO-01 entry gate. Sections `1.59.1`–`1.59.12` are
unchanged. PB01 and TFCAR are unchanged.

**Status:** candidate only. No FINAL PASS, no Architecture Baseline 1.0, no
authoritative Windows CI result and no AVH 0.1.3 result is claimed.

## 1.66 Documentation-only V15 update — Public Transparency Information Architecture & Verification Surface (2026-08-24)

_Reconciliation note (API-01 C3, 2026-08-25): this record is section 1.60 of the standalone V16 maintenance copy; it is carried here verbatim as section 1.66 because 1.60 is already a repository round record._

**Round:** documentation/governance only. No business PACK, DATA stage,
INTEGRATION stage or FRONT implementation round is started by this update.

**Entering register:** V14, including the VCRYPTO-01 Entry Gate & Adversarial
Security Model. V14 is preserved in full.

**Purpose:** record the approved public `/transparenz` information
architecture and bind it to the already-existing frontend, publication,
release-integrity and VCRYPTO governance without creating a duplicate
transparency/publication architecture.

**New FIR ID created:**

- `FIR-UX-012 — Public Transparency Information Architecture & Verification Surface`.

**FIR IDs implemented:** none.

**FIR IDs intentionally left unchanged:** every pre-existing FIR ID,
including `FIR-PUB-001`, `FIR-PUB-002`, `FIR-PUB-003`, `FIR-REL-001`,
`FIR-READY-001`, `FIR-SEC-SECRET-001`, `FIR-VOTE-CRYPTO-001`,
`FIR-FRONT-001`, `FIR-FRONT-002` and `FIR-UX-003` through `FIR-UX-011`.

This update deliberately does **not** create `FIR-TRANS-001`: the register
already has a transparency/publication workspace, PACK-28 publication
governance, publication integrity requirements and downstream-consumption
requirements. A second broad transparency FIR would duplicate authority and
would make later closure ambiguous.

**Frontend reference handoff:**
`EPD2_FRONTEND_TRANSPARENZ_HANDOFF_0.1.zip`,
SHA-256 `45abc68598426d0d513e0ee1a622a453b1906f7177bc3d6236b8417b45bf076a`.

The handoff fixes content direction and semantic grouping only. It does not
authorize redesign of the accepted frontend baseline and is not evidence of
implementation.

**No production-readiness, legal-activation or voting-readiness claim is made
by this documentation-only update.**

## 1.67 Documentation-only V16 update — Global EPD² Identity Line (2026-08-24)

_Reconciliation note (API-01 C3, 2026-08-25): this record is section 1.61 of the standalone V16 maintenance copy; it is carried here verbatim as section 1.67 because 1.61 is already a repository round record._

**Round:** documentation/governance only. No business PACK, DATA stage,
INTEGRATION stage or FRONT implementation round is started by this update.

**Entering register:** V15. V15 is preserved in full.

**Purpose:** record one global public-site identity requirement: the official
expansion of `EPD²` must be visible directly beneath the standard upper-left
logo on every public page using the shared EPD² header.

**New FIR ID created:**

- `FIR-UX-013 — Global EPD² Identity Line`.

**Exact public wording:**

`Erste Partei Direkte Demokratie`

**FIR IDs implemented:** none.

**FIR IDs intentionally left unchanged:** every pre-existing FIR ID, including
`FIR-UX-012`. The transparency-page requirement remains scoped to
`/transparenz`; this new FIR is cross-site and belongs to the shared public
header/page shell.

This update does not authorize a redesign and does not alter the EPD² logo.

## 1.64 Round record — CTRL-01 unified control plane and administration architecture (2026-08-14)

**Round:** consolidation scope. Repository version `0.37.0` -> `0.38.0`;
canon unchanged at `0.8.0`; compatibility ceiling `<0.38.0` -> `<0.39.0`.
Entering baseline: `EPD2_PACK-35_CANDIDATE_0.37.0.zip`. No code was merged
from any other archive. CTRL-01 is not a new business domain and PACK-36 is
not begun.

**What this round adds.** One new leaf control-plane context,
`services/control-plane-service`, declaring exactly `epd2-core` and imported
by nothing. Sixteen modules covering the authority model, the role model,
organizational scope, workspaces, consoles and desks, assurance profiles,
separation of duties, maker/checker, the role-assignment and
authority-activation lifecycles, temporary elevation, break-glass,
sensitive-data access, source-of-truth ownership, the control-plane matrix
and the consistency checker.

**The five invariants.** `technical capability != legal authority`,
`control plane != sovereign authority`,
`technical admin != political/legal decision-maker`, `console != authority`
and `break-glass != authority expansion`. Twenty preserved distinctions in
all, each with a named refusal.

**Consolidation, not redesign.** No service was rewritten, no role renamed,
no bounded context merged, no authorization runtime centralized. The
registries are harvested by parsing the repository — 393 role members and
624 actions across thirty-eight services — so the control plane consumes
generated contracts and no business service imports it. Hard invariants stay
locally enforceable: an unavailable control plane degrades visibility and
never degrades safety.

**No universal administrator.** No role in this repository is a super-,
global-, root- or master-administrator by any spelling, and the checker
scans every role enumeration in every service to say so rather than
asserting it. `SYSTEM_ADMINISTRATOR` and `SECURITY_ADMINISTRATOR` are
structurally separate, as are eligibility and credential, and voting and
tally; each collapse raises its own error type.

**Nothing is activated.** All eleven authority records ship `DEFINED`.
`OD-CTRL-13` has not decided which body activates an authority, and a
repository that activated one would have created the competence it exists
to record. As shipped, the control plane records competences and confers
none.

**System-wide findings.** Two observations, neither a defect and both
reported rather than silently fixed: 183 role members in fifteen bounded
contexts declare no grant partition, and 282 actions in thirteen declare no
wiring partition. Each may be classified inside its own service; none is
readable from the registries, and what the control plane cannot see it
reports rather than assumes.

**FIR IDs implemented:** none. CTRL-01 closes no future-implementation
requirement.

**FIR IDs partially advanced:** none. Every administration, role, authority,
workspace-isolation, break-glass, export and incident-response entry is
assessed in `CTRL-01-FIR-TRACEABILITY.md` and none is advanced, because
CTRL-01 documents and validates the separations rather than staffing or
activating them.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**FIR IDs intentionally left unchanged:** every entry in this register,
including `FIR-VOTE-CRYPTO-001`, which remains OPEN. CTRL-01 selects no
production voting cryptographic primitive, changes no voting, credential,
eligibility, tally or Voting Client code, and neither begins nor passes the
VCRYPTO-01 entry gate. TFCAR and PRDCI research entries are unchanged and
non-blocking.

**New FIR IDs created by implementation discovery:** `FIR-CTRL-101`
(competent role-assignment authorities per scope), `FIR-CTRL-102` (the
production assurance requirement for each profile), `FIR-CTRL-103` (which
acts require maker/checker in production), `FIR-CTRL-104` (physical or
logical separation for high-risk roles), `FIR-CTRL-105` (the break-glass
approval chain and its out-of-band recipient), `FIR-CTRL-106` (the maximum
duration of a temporary elevation) and `FIR-CTRL-107` (which body activates
an authority). Section 44 holds them.

The numbering starts at 101 rather than 001 deliberately. `FIR-CTRL-001`
through `FIR-CTRL-00n` already exist in section 1.36 under a different
meaning, and reusing the identifiers would have produced two entries with
one name — the exact defect this register's uniqueness rule exists to
prevent. Nothing historical is renamed. None is implemented and none is
scheduled by this round.

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins, with no frontend surface added at all; every pre-existing FIR
identifier; §1.59 and all twelve of its subsections; the five frozen
PACK-16D artefacts; `package-lock.json`.

## 1.63 Round record — PACK-35 lobbying disclosure and external influence transparency (2026-08-14)

**Round:** business scope. Repository version `0.36.0` -> `0.37.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.37.0` -> `<0.38.0`. Entering
baseline: `EPD2_PACK-34_CANDIDATE_0.36.0.zip`. No code was merged from any
other archive.

**What this round adds.** One new recording context,
`services/lobbying-disclosure-service`, declaring exactly `epd2-core` and
`epd2-audit-core`, and imported by nothing. Twenty-seven modules covering
the subject and external-actor vocabularies, the interaction record, source
provenance and verification as two independent axes, the mandatory
classification boundary, the materiality rule registry and its lifecycle,
the disclosure aggregate, review, correction, contest and subject response,
third-party allegations, the influence-context relation, disclosure-to-
disclosure relations, privacy and access classes, bounded search, the
publication candidate boundary, authorization with separation of duties,
append-only storage, events and the command layer.

**The four invariants.** `disclosure != guilt`, `contact != influence`,
`influence evidence != authority` and `transparency != surveillance`. All
four are module constants asserted as exact literals, each with a refusal
function behind it. Sixteen further distinctions travel with them in
`PRESERVED_DISTINCTIONS`, each with a named exception type.

**What the register cannot answer.** Not "who is compromised". There is no
influence score and no ranking: `SCORING_ACTIONS` and `RANKING_ACTIONS` are
empty sets, the scoring walk refuses the marker vocabulary and the
evaluative-ordering compound at both payload boundaries, and no state a
disclosure can reach is a verdict. `ReviewDetermination` has seven members
and none of them says a person did something wrong. An allegation is a
separate type in a separate store with no join to any disclosure and no
`verified`, `substantiated`, `credible` or `severity` field.

**The line this round had to hold.** A lobbying register is a list of who
met whom. Read carelessly it is a list of who is compromised, and the
distance between the two is one column somebody adds because a journalist
asked a reasonable question. Every failure mode has the same shape: a fact
is recorded accurately, a second fact is recorded accurately, software puts
them next to each other, and the arrangement asserts something neither fact
contains. Nobody writes that sentence. The layout writes it.

**The citizen-contact boundary.** `classify()` runs before anything is
stored and the outcome decides what kind of record exists. A constituent
writing to their representative is `CONSTITUENCY_CONTACT` and the command
refuses it — not stored and marked, refused — because the moment ordinary
contact enters a lobbying register, being in touch with your representative
is a thing that goes on a list. A party member raising a motion and a
citizen using an ordinary channel are refused on the same ground. Where the
facts run out the answer is `UNRESOLVED` and a human decides, rather than
the more useful of the two answers.

**The PACK-34 boundary.** No cross-pack inference chain. There is no port in
this service that reads a delegation anti-gaming signal — not one that
refuses, one that does not exist — so the chain of delegation concentration
plus a donation plus a meeting arriving at a conclusion about a person has
no first step. `assert_no_delegation_signal_as_proof` and
`assert_no_cross_pack_inference_chain` cover a caller who reaches for the
idea anyway.

**Source is not verification.** Two enumerations with no member in common.
`SELF_DECLARED` is where a fact came from and stays true forever;
`VERIFIED` is what somebody established about it. Collapsing them would
produce a register in which a representative's own account of a meeting is
marked verified because the representative is a reliable source. The person
who recorded a disclosure cannot verify it, and the separation is required
by the guard rather than looked up, because a lookup that fails open is a
separation that disappears exactly when the data is missing.

**FIR IDs implemented:** none. PACK-35 closes no future-implementation
requirement.

**FIR IDs partially advanced:** none. `FIR-DEL-001` is unchanged at
`partial`; this round touches no delegation code. `FIR-PROGRAM-004` is
unchanged and explicitly not closed.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**FIR IDs intentionally left unchanged:** every other entry in this
register, including `FIR-VOTE-CRYPTO-001`, which remains OPEN. PACK-35
selects no production voting cryptographic primitive, implements no Guardian
or time-release mechanism, changes no voting, credential, eligibility, tally
or Voting Client code, and neither begins nor passes the VCRYPTO-01 entry
gate. `VOTING_ACTIONS` is an empty set and `assert_no_voting_act` refuses.

**New FIR IDs created by implementation discovery:** `FIR-LOBBY-001` (which
roles carry a disclosure obligation at all), `FIR-LOBBY-002` (the monetary
and material thresholds, and which body sets them), `FIR-LOBBY-003`
(competence to activate, suspend or retire a disclosure rule),
`FIR-LOBBY-004` (whether an individual subject may be named in a public
register), `FIR-LOBBY-005` (what makes a disclosure eligible to be offered
for publication), `FIR-LOBBY-006` (handling of third-party allegations and
who may read one before it is referred) and `FIR-LOBBY-007` (retention for
each class of record, including how long an entry about a former
office-holder stays visible). Section 43 holds them. None is implemented and
none is scheduled by this round.

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins, with no frontend surface added at all; every pre-existing FIR
identifier; §1.59 and all twelve of its subsections; the five frozen
PACK-16D artefacts; `package-lock.json`.

## 1.62 Round record — PACK-34 delegation reputation and anti-gaming (2026-08-13)

**Round:** business scope. Repository version `0.35.0` -> `0.36.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.36.0` -> `<0.37.0`. Entering
baseline: `EPD2_PACK-33_CANDIDATE_0.35.0.zip`. No code was merged from any
other archive.

**What this round adds.** One new analytical context,
`services/delegation-reputation-service`, declaring exactly `epd2-core`,
`epd2-audit-core` and `epd2-delegation-service`, and imported by nothing.
Twenty-five modules covering context and temporal binding, the source
evidence boundary, a bounded metric registry, factual computation, a
versioned anti-gaming rule registry with a lifecycle, deterministic
detection, the analysis and signal records, contestability and review,
participant explanations, statistical disclosure control, the publication
candidate boundary, authorization with separation of duties, append-only
storage, events and the command layer.

**The two invariants.** `reputation != authority` and `anti-gaming !=
participant scoring`. What this pack calls reputation is transparent,
contestable, context-bound evidence about delegation behaviour and
delegation-system conditions — never a judgement about a person collapsed
into a value. Eighteen further distinctions travel with them, each with a
named refusal.

**The refusal this round did not reverse.** PACK-32 refused a per-participant
political score, and PACK-34 is the round that had the data to build one. It
does not. There is no scalar or composite value ranking a participant under
any name: the scoring walk refuses by exact key and by suffix, at every
nesting depth, inbound at the command chokepoint and outbound at the single
event construction point, so `trust_score` and `member_trust_index` are
refused alike. `AntiGamingSignal` has no verdict, sanction, confidence or
score field — asserted by parsing the dataclass, not by reading its
docstring — and `MEMBER_RATING_ADMINISTRATOR` is a registered role that is
never granted, so that the absence is a decision somebody would have to
reverse in writing.

**Facts and signals are two modules.** `computation.py` produces nine
scope-level factual metrics and constructs no signal; `detection.py`
evaluates six rules and computes no metric. Not one of the nine metrics
names a participant. A per-delegate figure exists only inside a rule
evaluation, as the factual basis of a signal a human reviews, and the
subject of a subject-bound signal is always the delegate — never a
delegator, because recording who somebody chose to follow is recording
their political behaviour.

**Nothing is activated, and not by omission.** All six rules ship in
`DEFINED`. Activation requires a governed authority reference and
`ActivationAuthorityPort` has no implementation, because no body in this
repository is recorded as competent to hold it. The only threshold profile
shipped is named `EPD2-TESTONLY-NOTGOVERNED-P34-THRESHOLDS-1` and is refused
wherever a governed evaluation is claimed. There is no disclosure floor at
all. As shipped, this service computes factual metrics and raises no signal,
and the round reports that rather than working around it.

**Arithmetic that reproduces.** Every metric value is an integer numerator
over an integer denominator and every threshold comparison is a
cross-multiplication. An independent verifier holding the same source
evidence, rule-set version, calculation version, threshold profile, scope
and window reaches the same values and the same deterministic signals, and
`reproduction.py` states the canonical form of exactly those bindings.

**Detection is not enforcement.** No path exists from a signal to a
delegation change, a weight change, a suspension, a publication, a complaint
or a case. Review confirms a calculation and confers nothing: seven review
outcomes describe the calculation and none can express guilt, and
`REVIEWER_ACQUIRES_NOTHING` enumerates the seven authorities a reviewer does
not acquire by reviewing.

**FIR IDs implemented:** none. PACK-34 closes no future-implementation
requirement. `FIR-DEL-001` moves from `captured` to `partial` — its
contestability, context-binding and method-disclosure requirements are
implemented and its disclosure-control requirement is not, because the
disclosure floor it depends on has not been agreed.

**FIR IDs partially advanced:** `FIR-DEL-001`, as above.
`FIR-PROGRAM-004` is **not** advanced and explicitly not closed: PACK-34
demonstrates bounded-input, non-profiling, disclosed-method anti-gaming in
one domain, and programme ordering is a different domain with its own
acceptance criteria, none of which this round meets.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**FIR IDs intentionally left unchanged:** every other entry in this
register, including `FIR-VOTE-CRYPTO-001`, which remains OPEN. PACK-34
selects no production voting cryptographic primitive, implements no Guardian
or time-release mechanism, changes no voting, credential, eligibility, tally
or Voting Client code, and neither begins nor passes the VCRYPTO-01 entry
gate.

**New FIR IDs created by implementation discovery:** `FIR-DELREP-001`
(competence to activate an anti-gaming rule), `FIR-DELREP-002` (governed
thresholds and the minimum population for disclosure), `FIR-DELREP-003`
(whether and how a participant learns a signal names them, and who reviews
it), `FIR-DELREP-004` (retention of derived political-behaviour data),
`FIR-DELREP-005` (when, if ever, a signal may trigger another domain's
governed review) and `FIR-DELREP-006` (repository-wide governance of the
payload marker sets each service maintains by hand). Section 42 holds them.
None is implemented and none is scheduled by this round.

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins, with no frontend surface added at all; every pre-existing FIR
identifier; §1.59 and all twelve of its subsections; the five frozen
PACK-16D artefacts; `package-lock.json`.

## 1.61 Round record — PACK-33 citizen office routing and no-wrong-door caseflow (2026-08-13)

**Round:** business scope. Repository version `0.34.0` -> `0.35.0`; canon
unchanged at `0.8.0`; compatibility ceiling `<0.35.0` -> `<0.36.0`.
Entering baseline: `EPD2_PACK-32_CANDIDATE_0.34.0.zip`, SHA-256
`5458d45ef02577d9eefa5a78fad7c8420857db26f4c486f5b6c6c334246ba828`. No code
was merged from any other archive.

**What this round adds.** One new leaf bounded context,
`services/citizen-office-routing-service`, declaring exactly `epd2-core` and
`epd2-audit-core` and imported by nothing. Thirty modules covering citizen
submission, acknowledgement, routing classification, typed routing targets,
routing decisions, responsible and representative assignment, handoff with
purpose and confidentiality preservation, escalation, information requests,
response coordination, governed conversion requests, duplicate relations,
closure and the citizen-facing status projection.

**The product principle.** A citizen must not be required to understand the
internal organization of EPD² in order to reach the competent body. A valid
submission received by any citizen-facing office is not refused merely
because the sender chose the wrong internal door: the system, not the
sender, carries the cost of finding the right one. Where routing can be
resolved safely the matter is received, acknowledged, classified, routed and
tracked. Where it cannot, nothing is silently discarded, nothing is falsely
assigned and no competence is fabricated — the matter reaches `UNRESOLVED`,
a visible governed state with a reason the sender can be told.

**The central invariant.** `routing != authority`. A routing decision
determines _where_ a matter is handled. It does not decide the political,
legal, disciplinary, complaint, programmatic or representative outcome of
that matter. And the half of the product principle that gets dropped in
retelling is written down beside it: `no wrong door != every door has every
authority`. Routing solves discoverability and coordination; it does not
dissolve institutional boundaries.

**Five properties carry the round.**

_There is no field an outcome could occupy._ `RoutingDecision` has no
`outcome`, no `finding`, no `result` and no `disposition`, and neither does
`CitizenSubmission`. The absence is structural rather than documented: there
is no value for a code path to set, and the repository suite asserts it by
parsing the dataclass rather than by reading the docstring. Ten governed
payload walks run inbound at the single `_guard` and outbound at the single
private `_envelope`, and three of the ten are specific to this pack —
`assert_no_case_content`, `assert_no_universal_person_identifier` and
`assert_no_outcome_claim`. ADR-127.

_Requested is not accepted, twice over._ A handoff is a request and then,
separately, the target's answer; a conversion is a request and then,
separately, the destination domain's answer read through a port with one
read method. `ConversionState.REQUESTED` has no edge this service can
traverse alone, and `record_conversion_result` takes no parameter by which a
caller could supply an acceptance. The gap between requested and accepted is
where a matter goes missing, and a system that cannot represent the gap
cannot show it to anybody. ADR-128.

_No-wrong-door does not become infinite-wrong-door._ A destination already
in a matter's history may receive it again only when the routing carries a
governed basis recorded elsewhere — a reclassification, a refusal that named
this office, a reviewer's direction. "The officer thinks so this time" is
not such a basis, because it is not in the record. A matter that four
offices have disclaimed has found a competence question, and it escalates
rather than moving again. Every individual step in a routing loop is
reasonable and correctly recorded, which is exactly why the loop is
invisible from inside it.

_Purpose and confidentiality survive the transfer._ Purposes are intersected
rather than unioned; a proposed purpose the source did not hold is refused
rather than trimmed; minimum-necessary is enforced against the
_destination's_ declaration rather than the sender's judgement; retention
references, legal holds and access restrictions travel; and confidentiality
moves in one direction only. There is no role that may lower a class and no
policy field that permits it, because the failure this refuses is not malice
— it is an officer who cannot route a matter to the office they believe is
right, and who finds that relabelling it makes the rule accept the
destination.

_Nothing is merged, and nothing is published._ A duplicate relation is
recordable; a merge is not implemented, is a prohibited act, and has no
member in the relation enumeration. One person's letter ceasing to exist as
something anybody can answer is the thing that must never happen without a
trace. Publication belongs to PACK-28: this service offers a candidate and
performs nothing, and no case becomes public because it closed.

**FIR IDs implemented:** none. PACK-33 closes no future-implementation
requirement. The two a reader is most likely to think this round closed are
PACK-29's, because this service consumes a representative referral, and the
complaint-domain entries, because this service classifies towards a
complaint context. Neither is closed: consuming a referral is not
implementing the desk, and routing _to_ an unbuilt domain is not building
it. `FIR-CONFLICT-001` and `FIR-CONFLICT-002` remain open.
`FIR-VOTE-CRYPTO-001` remains **OPEN** and is untouched by this round; the
VCRYPTO-01 entry gate at `1.59.1`–`1.59.12`, carried forward under PACK-32's
addendum, is unchanged in every particular and no production voting
cryptographic primitive is selected.

**FIR IDs partially advanced:** none. Preparing for a domain is not
advancing a requirement that domain owns.

**FIR IDs deferred:** none deferred from an earlier round by this one.

**FIR IDs intentionally left unchanged:** every other entry in this
register. In particular `FIR-CTRL-001` is not closed: every routing act
carries authority, scope, assurance, maker/checker where required, audit
evidence and a governed ground, so that a later Control Plane does not have
to redo the architecture — but preparing for a control plane is not building
one. No entry in this register was renamed, deleted or closed by this round.

**New FIR IDs created by implementation discovery:** `FIR-ROUTING-001` (the
authoritative competence directory and who maintains it), `FIR-ROUTING-002`
(the complaint and petition owning domain), `FIR-ROUTING-003` (cross-scope
routing policy and organizational containment), `FIR-ROUTING-004` (the legal
basis for transfer between offices of a political party) and
`FIR-ROUTING-005` (citizen remedy against a routing decision). All five are
in section 41 and none is implemented.

**Preserved unchanged:** canon `0.8.0`; exactly ten workspaces and ten
origins; the Voting Client, which gains no PACK-33 route; the PACK-28C2
verifier-runtime architecture and the independent verifier's dependency
ownership; the five frozen PACK-16D artefacts, byte-identical; §1.59 and all
twelve of its subsections; and every pre-existing FIR identifier, historical
entry and round record in this file.

# 2. Current confirmed baseline

## 1.22 Round record — PACK-16C specification and ADR (2026-08-01)

**Round:** PACK-16C — Casting, Receipt, Verification Client, Bulletin Board
and Election Record. **Specification and ADR only. No code. No
cryptographic implementation. Not implemented. Not an implementation
candidate. Not a PASS.**

**Repository version:** unchanged at `0.15.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-16B_CRYPTOGRAPHIC_PARAMETERS_KEY_CEREMONY_AND_TRUSTEE_ARCHITECTURE_SPEC_ADR_FINAL_REVIEW_CANDIDATE.zip`,
SHA-256 `7074feedd7b5d97dd8b44bc2017dd5170fda6390766d5a41566e73283d688d9b`,
one repository root, one `uv.lock`, one `package-lock.json`, one canonical
Master Register, no duplicate archive paths and no nested ZIP files. The
final-review PACK-16B candidate — the one whose `VO-08` ownership and
Acceptance Matrix wording passed correction — is the authoritative input;
no earlier PACK-16B tree was used.

**What this round did.** It answered the three questions PACK-16A and
PACK-16B left for it: when the continuation capability is consumed, what a
voter may be given afterwards, and what must be published so that a stranger
can check the outcome. The consumption point is fixed **inside an atomic
acceptance boundary, after every cryptographic check and immediately before
durable acceptance**, so that a ballot failing any check costs the voter
nothing. The receipt proves **publication only**. The election record is
fixed at **thirty-two mandatory artefacts**, sufficient for the sixteen
checks an independent verifier must perform, plus a mandatory statement of
the six things the record cannot show.

```text
CONSUMPTION      atomic validation + consumption + acceptance;
                 exactly-once; mechanism deferred as OD-P16C-01 and
                 an ARCHITECTURAL BLOCKER if undemonstrable
BALLOT IDENTITY  four separated values; ballot_id client-random
CHALLENGE        commitment before choice; unlimited, voter-manual;
                 a challenged ballot is NEVER counted
PIPELINE         23 ordered stages, fail closed, distinct reason code
                 per stage; every cryptographic check before the boundary
LIFECYCLE        16 states; PACK-16A's 14 extended, none redefined;
                 superseded_if_permitted remains UNREACHABLE
RECEIPT          proves publication only; re-derivable; proves
                 PARTICIPATION, which is accepted and not solved
BOARD            Merkle transparency log, chained signed checkpoints,
                 mirror co-signing; TAMPER-EVIDENT, not tamper-proof
PUBLICATION      durable acceptance + signed commitment + published
                 deadline; no state "accepted but never published"
RECORD           32 artefacts; 16 verifier checks; 0 checks unserved;
                 4 artefacts retained for honesty, serving no check
TURNOUT          fixed-size batches with padding; below a minimum
                 electorate size a context is NOT activated electronically
ADR              ADR-101, status `proposed`, CONDITIONAL on ADR-100
```

**Documents added.** Thirty-three documents under `docs/packs/PACK-16/` and
`docs/adr/ADR-101-CASTING-RECEIPT-VERIFICATION-BULLETIN-BOARD-AND-ELECTION-RECORD.md`.
Nothing else in the repository was created, modified or deleted apart from
this register entry and `FIR-ROADMAP-006`'s cross-reference note. No source
file, test, migration, API or event implementation, frontend file, CI
workflow, `uv.lock`, `package-lock.json` or dependency was touched.

**FIR IDs implemented by this round:** none, and none may be. **FIR IDs
deferred:** `FIR-ROADMAP-007` (independent-verification operations, board
resilience, archive re-verification, witness ecosystem); `FIR-SEC-001`
(runbooks and rehearsal); `FIR-TRUST-001` (the signature and timestamp
framework itself); `FIR-OSS-006` (delivery); and the remainders of
`FIR-ASM-006` and `FIR-ASM-007`. **FIR IDs taken up as deferred to PACK-16C
by PACK-16B:** `FIR-ASM-006` and `FIR-ASM-007`, both **specified,
partially**. **FIR IDs assessed:** `FIR-SEC-002` and `FIR-DATA-003`. **FIR
IDs intentionally left unchanged:** `FIR-ROADMAP-005`, `FIR-ROADMAP-008`,
`FIR-ROADMAP-009`, `FIR-ROLE-004`, `FIR-ROLE-006`, `FIR-CAND-001`,
`FIR-PROG-001`, `FIR-ASM-008`, `FIR-OSS-001` … `FIR-OSS-006`, and every
entry not named in
`docs/packs/PACK-16/PACK-16C-FIR-COVERAGE-MATRIX.md`. **New FIR IDs created
by this round: none. FIR statuses changed by this round: none.**

`FIR-INV-002` remains **partially addressed and future**, exactly as
PACK-15, PACK-16A and PACK-16B left it. This round specifies the ballot side
of `credential → ballot` in full — separate stores with no join key, no
trace spanning the atomic boundary, the retry token stripped before
publication, and no correlating field published — and **does not close the
invariant**: it cannot be closed without a built system to demonstrate
against, and an operator with database access to both stores plus precise
timing remains a stated residual.

`FIR-ROADMAP-006` **keeps its status `approved` and its target version
`0.16.0`.** PACK-16C performs the casting, receipt, verification, board and
record specification stage only.

**Canon.** `CANON CLARIFICATION REQUIRED`; six clarifications recorded
(`CQ-P16C-01` … `CQ-P16C-06`); **no amendment proposed**; three amendment
candidates recorded (`CAM-P16C-01` … `CAM-P16C-03`). The finding is that the
canon has **no publication primitive for a public ballot-bearing board**,
because its only append-only public primitive — `PublicLedgerEntry` (19a.1)
— correctly prohibits a link to `VoteEnvelope`. The board is therefore
specified on its own terms and the gap is recorded rather than filled by
analogy. The `PublicLedgerEntry → VoteEnvelope` prohibition stands
untouched and is reinforced at the data-model level. `CANON_VERSION`
unchanged at `0.8.0` and the canon files are untouched.

**Open decisions.** Closed: **none**. Opened: `OD-P16C-01` … `OD-P16C-13`.
`VO-08` is **not closed, not narrowed and not re-owned** by this round; it
remains owned by PACK-16B external cryptographic review and confirmed by
PACK-17. Three acceptance rows are `BLOCKED` and none is dressed as
progress: challenge take-up is an empirical fact no specification act
changes; independent verification of a real context requires a party that
has not been engaged; and split-view resistance rests on organisational
mirror independence because the mechanism is unstandardised — the IETF's own
gossip draft for Certificate Transparency expired in 2020 without becoming
an RFC.

**Evidence.** Five entries in a single canonical registry. **Four new
primary sources were read first-hand on 2026-08-01** — RFC 9162, RFC 6962,
`draft-ietf-trans-gossip-05` and the C2SP `tlog-witness` specification — and
quoted with section numbers; one entry is an inference and is marked as
such. Fourteen inherited entries are cited **as inherited**, with no
re-attestation of a reading this round did not perform. **All four new
sources are from the certificate and software-supply-chain domain; none
concerns elections**, and that limitation is stated rather than glossed.
**Six of this round's central decisions rest on no external source at all**
and are recorded as reasoned rather than evidenced.

**Acceptance.** 166 rows: 134 `SATISFIED`, 9 `PARTIALLY SATISFIED`, 11
`DEFERRED`, 3 `BLOCKED`, 9 `NOT APPLICABLE`. No row claims implementation,
external review, production readiness or legal activation. **Lines of code
written: 0.**

**PACK-16D is not started.**

## 1.23 Round record — PACK-16D reference implementation candidate (2026-08-02)

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation candidate. Not production code. Not certified.
Not a PASS.**

**Repository version:** `0.15.0` → `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-16C_CASTING_RECEIPT_VERIFICATION_BULLETIN_BOARD_AND_ELECTION_RECORD_SPEC_ADR_FINAL_CORRECTED_CANDIDATE.zip`,
SHA-256 `60297babbcab02ea51db66db97ac50823a37d2373da735b88c5e5fd80a56ed83`,
one repository root, one `uv.lock`, one `package-lock.json`, one canonical
Master Register, no duplicate archive paths and no nested ZIP files. The
final corrected PACK-16C candidate — the one whose event-privacy and
open-decision corrections passed — is the authoritative input; no earlier
PACK-16C tree was used.

**What this round did.** It is the first PACK-16 round that ships code. It
implements a _reference_ form of the model PACK-16A, PACK-16B and PACK-16C
specified: cryptography, canonical encoding, domain separation, randomness,
ballot preparation, the NIZK proof family, the two atomic transactions,
sealed fixed-capacity batches, the bulletin board, the election record and
an independent verifier — 39 Python modules under
`services/voting-service/src/epd2_voting_service/reference/`, with 361 tests
under `services/voting-service/tests/reference/`.

```text
PLACEMENT        inside epd2-voting-service; NO new workspace member, so
                 uv.lock and package-lock.json are byte-identical
DEPENDENCIES     ZERO added; hashlib, hmac, secrets and Python integers
PARAMETERS       EPD2-CRYPTO-1 REGISTERED BUT UNAVAILABLE and failing
                 closed (OD-P16D-01); two banner-marked TEST profiles
                 carry the tests; q = 2**256 - 189 confirmed first-hand
ENCODING         EPD2-ENC-1 canonical binary tuples; order normative
DOMAIN SEP       EPD2-DS-1, 25 labels, one registry, fail closed
TRANSACTIONS     both atomic; a capability is never spent by a submission
                 that does not commit; 11 fault points prove it
CAPACITY         L_max = E x (K + A) from capabilities, never turnout;
                 slot partition must cover the batch exactly
BATCHES          constant-shaped; cover leaves are uniform random
BOARD            RFC 6962 tree; inclusion, consistency, rollback and
                 equivocation detected within one exported view
RECORD           no tally artefact can be constructed before closure
VERIFIER         public artefacts only; boundary enforced by ast tests
VECTORS          23, ALL self-generated; stability only, NOT conformance
GUARDIANS        SINGLE guardian; threshold DKG NOT implemented
VO-08            OPEN; no BSI conformity claimed
ADR              ADR-102, status `proposed`
```

**Documents added.** Thirty-three documents under `docs/packs/PACK-16/` and
`docs/adr/ADR-102-CRYPTOGRAPHIC-REFERENCE-IMPLEMENTATION-ATOMIC-PERSISTENCE-AND-VERIFICATION-HARNESS.md`.

**Source added.** 39 Python modules and 2 parameter files under
`services/voting-service/src/epd2_voting_service/reference/`; 10 test
modules and 1 test-vector catalogue under
`services/voting-service/tests/reference/`. **Modified:** eight files, all
of them version bookkeeping bound together by `scripts/verify_versions.py`
and `scripts/check_canon_0_8_0.py`, plus `CHANGELOG.md` and `README.md`.
**Deleted:** none. **No dependency, `uv.lock`, `package-lock.json`,
migration, frontend file or CI workflow was touched.**

**FIR IDs implemented by this round:** none in full. `FIR-ROADMAP-006` moves
to **`implemented in reference form`** for the casting, publication, record
and verification path and stays `approved` overall — see its entry. **FIR
IDs deferred to PACK-17:** `FIR-ROADMAP-007` (independent verification,
board resilience, archive re-verification, witness ecosystem); `FIR-SEC-001`
(runbooks and rehearsal); `FIR-TRUST-001`; `FIR-OSS-006`. **FIR IDs
intentionally left unchanged:** every entry not named in
`docs/packs/PACK-16/PACK-16D-FIR-COVERAGE-MATRIX.md`. **New FIR IDs created
by this round: none. FIR statuses changed by this round: none.**

`FIR-INV-002` remains **partially addressed and future**, exactly as
PACK-15, PACK-16A, PACK-16B and PACK-16C left it. This round _implements_
the ballot side of `credential → ballot` — separate maps with no shared key,
a leaf reservation that names a submission and never a capability, an outbox
row scanned for forbidden fields, and tests that assert no persisted row
pairs the two — and **does not close the invariant**: an in-memory reference
store is not a production data plane, and the operator-with-database-access
residual is unchanged.

**Canon.** `NO CANON CHANGE REQUIRED`. All eight entities §54 names map onto
aggregates PACK-16A/16B/16C already specified; five implementation types
(`AuditRecord`, `FeatureFlags`, `LogRecord`, `SchemaDescriptor`,
`FaultPoint`) are held at service level on the precedent PACK-12's
`PrivilegedSession`, PACK-14's `SessionRecord` and PACK-15's voting context
registry set.

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata was updated to include
repository version 0.16.x.
```

Concretely: `canon-version.json` had its non-canonical
`repository_compatibility` widened from `>=0.1.0 <0.16.0` to
`>=0.1.0 <0.17.0` because the repository moved to `0.16.0`. That is
bookkeeping rather than semantics, it is correct under the repository's
versioning rules, and it is not reverted — but the file **was** modified,
so this round is not described as leaving the canon files untouched.

**Open decisions.** Closed: **none**. Opened: `OD-P16D-01` … `OD-P16D-10`.
`VO-08` is **not closed, not narrowed and not re-owned**; it remains owned by
PACK-16B external cryptographic review with independent confirmation in
PACK-17, and is named in the verifier's `NOT_CHECKED` list so that every
verification result carries it. Two of this round's open decisions are
**production blockers**: `OD-P16D-05` (no constant-time guarantee — Python
big-integer arithmetic is not constant-time) and `OD-P16D-09` (checkpoint
signatures are carried but never verified, because the reference board signs
with a symmetric key a third-party verifier does not hold).

**Verification.** 5513 Python tests passed, 17 skipped; mypy clean across
every Makefile group; `ruff check` and `ruff format --check` clean; all four
repository scripts pass. Line coverage of the reference package is 91.8 %,
measured with the standard library's `trace` module. **`uv sync --frozen`
and the entire npm side were NOT executed** — both registries return HTTP
403 in this environment, exactly as `LOCAL_VERIFICATION.md` records — and
**branch coverage was NOT measured**, because no coverage tool is
installable here. Property tests run as deterministic seeded loops rather
than `hypothesis` strategies, for the same reason.

**Defects found by this round's own harness and fixed in the
implementation.** Recorded because a round that reports none has usually not
looked: the idempotency check ran outside the transaction, so two concurrent
requests sharing a key could both proceed; the shared reserve was inferred
from leftover batch capacity, which silently reintroduced adaptive overflow;
the Merkle construction duplicated the last node on odd levels, which lets
two leaf sequences share a root, and was replaced with the RFC 6962 shape;
the election-record digest omitted the batch openings and the decryption
shares; decryption-share proofs were not bound to the contest and option
they decrypt; two proof verifiers did not subgroup-check the public key;
`load_profile` and `verify_record` compared a parameter's bit length against
itself; and a concurrency test asserted an outcome that was wrong about one
run in thirty. Every one was fixed in the implementation, not in the test.

**PACK-17 is not started.**

## 1.24 Round record — PACK-16D correction: cryptographic profile, threshold guardians, checkpoint authenticity and conformance (2026-08-02)

**Round:** PACK-16D — Cryptographic Profile, Threshold Guardians, Checkpoint
Authenticity and Conformance Correction. **A correction of the section 1.23
candidate, not a new round.**
**Reference implementation candidate. Not production code. Not certified.
Not a PASS.**

**Repository version:** unchanged at `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-16D_CRYPTOGRAPHIC_IMPLEMENTATION_ATOMIC_PERSISTENCE_TEST_VECTORS_AND_VERIFICATION_HARNESS_CANDIDATE.zip`,
SHA-256 `9ff64a5b97f0d9b237c25991f602d404304c0d13cdb08276ba3675ad7d54d4b0`.

**Why there is a correction.** An independent audit of that archive returned
**NOT ACCEPTED**:

```text
ARCHIVE HYGIENE:                    PASS
REFERENCE TEST SUITE:               PASS
REFERENCE IMPLEMENTATION SCAFFOLD:  PASS
ATOMIC PERSISTENCE MODEL:           PASS FOR REFERENCE STORE
ACTUAL EPD2-CRYPTO-1 PROFILE:       FAIL
THRESHOLD GUARDIAN MODEL:           FAIL
CHECKPOINT AUTHENTICITY:            FAIL
EXTERNAL CONFORMANCE:               FAIL
PACK-16D:                           NOT ACCEPTED
PACK-17:                            DO NOT START
```

The four failures shared one shape: a central mechanism was missing, the
absence was described carefully, and the description was filed under a
heading — an open decision, a `BLOCKED` acceptance row, an external-party
dependency — that made it read as somebody else's work. All four are now
implemented. Everything the audit passed was preserved rather than rebuilt.

```text
PLACEMENT        unchanged; inside epd2-voting-service, NO new workspace
                 member, uv.lock and package-lock.json unchanged
DEPENDENCIES     still ZERO added; Ed25519 implemented from RFC 8032 in
                 the standard library precisely so no lock change was
                 needed; cryptography and Node.js are TEST ORACLES ONLY
PARAMETERS       EPD2-CRYPTO-1 REAL AND LOADABLE. ElectionGuard 2.1
                 §3.1.1 standard baseline, primary-sourced, verified by
                 arithmetic no transcription error survives. NO FALLBACK
                 of any kind. Test profiles renamed
                 EPD2-TESTONLY-NOTCONFORMANT-*        (OD-P16D-01 CLOSED)
ENCODING         EPD2-ENC-1; SEQ and STRUCT now length-prefix every
                 member — the previous form was AMBIGUOUS and was found
                 by the independent oracle, not by any internal vector
DOMAIN SEP       EPD2-DS-1, 27 labels, one registry, fail closed
GUARDIANS        Feldman VSS DKG; generic k-of-n; 3-of-5 default and
                 4-of-7 high assurance; 2k <= n refused; threshold
                 reduction impossible; compensated decryption refuses
                                                      (OD-P16D-07 CLOSED)
CHECKPOINTS      Ed25519 RFC 8032; canonical domain-separated payload;
                 SignerRegistry trust anchor supplied ALONGSIDE the
                 export, never read from the artefact; declared rotation
                 windows; five distinct fail-closed outcomes
                                                      (OD-P16D-09 CLOSED)
CONFORMANCE      three named evidence classes; 23 internal-stability
                 vectors UNCHANGED in status, plus 2 primary-source and
                 11 cross-implementation entries from TWO oracles that
                 share no code with the producer
VERIFIER         26 result codes, 26 exit codes; NOT_CHECKED now 9
                 entries — one removed because it became FALSE
VO-08            OPEN; no BSI conformity claimed; obtaining the
                 parameters did not narrow it by one word
ADR              ADR-102, status `proposed`, unchanged
```

**Documents.** Three added
(`PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md`,
`PACK-16D-CHECKPOINT-SIGNATURE-AND-SIGNER-TRUST-MODEL.md`,
`PACK-16D-EXTERNAL-CONFORMANCE-REPORT.md`), bringing the round to 36
documents under `docs/packs/PACK-16/` plus `ADR-102`. The rest were revised.

**Source.** 14 files added (7 under `reference/`, 7 under
`tests/reference/`), 2 renamed, 0 deleted. The reference package is now 45
modules and 7 392 lines; the tests are 14 modules plus 2 oracles and 6 676
lines. **No dependency, `uv.lock`, `package-lock.json`, migration, frontend
file, CI workflow or version constant was touched, and no file under
`docs/canonical/` was modified by this pass.**

**FIR.** **New FIR IDs: none. FIR statuses changed: none.**
`FIR-ROADMAP-006` stays `approved` and `implemented in reference form`,
partially, with a materially stronger delivery. `FIR-TRUST-001` moves from
_deferred to PACK-17_ to **partially implemented**: the signature half of
the signature-and-timestamp framework now exists; the timestamp half does
not. `FIR-SEC-002` **stays** _blocked pending external review_ — the
parameters arrived, the assurance did not, and assurance is what the entry
is about. `FIR-INV-002` remains partially addressed and is not closed.
**None of the eight items that may not be closed was closed.**

**Canon.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata was updated to include
repository version 0.16.x.
```

`NO CANON CHANGE REQUIRED`. The correction's new implementation types —
guardian records, threshold shares, checkpoint signer records — are held at
service level on the same PACK-12 / PACK-14 / PACK-15 precedent, bringing
that list to nine. The closest call is `SignerRegistry`: a _published,
governance-issued_ signer set would be canon-visible, and it is not canon
yet only because no governance act issues one. If `OD-P16D-12` closes with a
published registry, the amendment question must be re-asked.

**Open decisions.** **Closed: three** — `OD-P16D-01` (the profile loads),
`OD-P16D-07` (threshold path implemented), `OD-P16D-09` (signatures
verified). **Opened: two** — `OD-P16D-11` (the reference ceremony has no
custody model: one process, no authenticated channel, no HSM, no air gap)
and `OD-P16D-12` (the signer registry's own authorisation is outside the
verifier's reach). `OD-P16D-02` is **narrowed but not closed**: two
independent oracles and primary-source parameters now exist, but no
comparison against a _complete_ independent implementation. **No inherited
decision was closed**, and `VO-08` remains open. **One production blocker
remains**: `OD-P16D-05`, now across four distinguished surfaces — public
verification carries no secret, while guardian secret operations,
secret-nonce use and Ed25519 private-key signing are all secret-bearing and
none is constant-time. `OD-P16D-09`'s blocker status is discharged.

**Acceptance matrix.** 85 rows: 72 `SATISFIED`, 6 `PARTIALLY SATISFIED`,
2 `DEFERRED`, 4 `BLOCKED`, 1 `NOT APPLICABLE`. Four rows left `BLOCKED`;
three because the work was done, and one (`AM-77`, a fully independent
verifier) because calling it blocked misdescribed this round's own omission
as an external party's inaction. `CORRECTED` is not used as a status.

**Verification.** 5 616 Python tests passed, 17 skipped, 464 of them in the
reference suite; `ruff check` and `ruff format --check` (496 files) clean;
`mypy services/voting-service` clean over 69 source files; all four
repository scripts pass. Line coverage of the reference package is 90.9 %
(3 816 / 4 200) with the standard library's `trace` module — a lower
percentage than the first candidate's 91.8 % over a package a third larger.
**`uv sync --frozen`, the entire npm side, hypothesis and branch coverage
were NOT executed** and none is claimed as a PASS.

**The defect that justifies the audit's judgement.** `encode_seq`
concatenated its items raw after a count, so `SEQ([b"ab", b"c"])` and
`SEQ([b"a", b"bc"])` produced identical bytes — two different sequences
sharing a digest, in a function every protocol digest runs through.
`encode_struct` had the same flaw. It was found by the independent Node.js
oracle, which was written from the documented grammar rather than from the
code and therefore disagreed with it. **No self-generated stability vector
could have found this**, which is precisely why `EXTERNAL CONFORMANCE: FAIL`
was the right call.

**PACK-17 is not started and must not start before independent acceptance of
PACK-16D.**

## 1.25 Round record — PACK-16D final correction: vetted cryptographic provider, immutable parameter provenance, target-profile conformance (2026-08-02)

**Round:** PACK-16D — Final Cryptographic Provider, Immutable Parameter
Provenance and Target-Profile Conformance Correction. **A correction of the
section 1.24 candidate, not a new round.**
**Reference implementation candidate. Not production code. Not certified.
Not a PASS.**

**Repository version:** unchanged at `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:**
`EPD2_PACK-16D_..._CORRECTED_CANDIDATE.zip`,
SHA-256 `bd543264f04a98d962aa6cde4a8bff6405e790962a14f657cdb40ea3160ab891`.

**Why there is a second correction.** The audit of that archive returned:

```text
ARCHIVE HYGIENE:                          PASS
REAL EPD2-CRYPTO-1:                       PASS
TARGET-PROFILE CRYPTO TESTS:              PASS
3-OF-5 THRESHOLD REFERENCE PATH:          PASS
4-OF-7 GENERIC PATH:                      PASS
CHECKPOINT SIGNATURE SEMANTICS:           PASS
CHECKPOINT SIGNATURE PRIMITIVE POLICY:    FAIL - HANDWRITTEN ED25519
PARAMETER SOURCE REPRODUCIBILITY:         PARTIAL - MUTABLE URL / DIGEST NOT IN ARTIFACT
CROSS-IMPLEMENTATION ON TARGET PROFILE:   PARTIAL
PACK-16D:                                 NOT YET ACCEPTED
PACK-17:                                  DO NOT START
```

The first finding is the instructive one. The previous round had implemented
Ed25519 from RFC 8032 in the standard library and defended it carefully:
published standard, implemented as written, cross-checked against OpenSSL on
25 vectors. Every fact was true and the conclusion was wrong. The round had
optimised for **"add no dependency"** when the property that mattered was
**"implement no cryptographic primitive"** — two goals that pointed in
opposite directions, with the weaker one chosen unnoticed.

```text
SIGNATURE          crypto/ed25519.py DELETED. crypto/signature_provider.py
                   is a port over cryptography 46.0.7 / OpenSSL 3.5.6: a
                   Protocol with six operations, one implementation, strict
                   raw canonical encodings, fail-closed verify, NO FALLBACK.
                   An ast test forbids re-adding curve arithmetic anywhere.
                                                      (OD-P16D-13 CLOSED)
PROVENANCE         authoritative reference moved from a mutable /main/ URL
                   to the SPECIFICATION at a versioned release asset, digest
                   recorded IN the artefact. Plus offline reconstruction: p
                   from the published ln 2 rule (3305 bits, computed as
                   2*atanh(1/3)) and a recorded 279-bit offset; q, r, g in
                   closed form. The previous round's source digest was
                   WITHDRAWN - it was computed over a markdown rendering.
                                                      (OD-P16D-14 CLOSED)
CONFORMANCE        all TWELVE core operations cross-checked on EPD2-CRYPTO-1
                   itself, with fixed nonces, exported fixtures, a
                   machine-readable oracle envelope, and two invalid
                   fixtures that stay INSIDE the subgroup.
                                                      (OD-P16D-15 CLOSED)
CLASSIFICATIONS    five, not three: internal-stability, primary-source,
                   rfc-conformance, cross-implementation-test-profile,
                   cross-implementation-target-profile
LOCK               NOT REGENERATED at the time. SUPERSEDED by section 1.27:
                   uv.lock now resolves cryptography 46.0.7.
                                              (OD-P16D-16 OPENED HERE, CLOSED)
UPSTREAM PIN       no commit SHA or digest obtainable at the time. SUPERSEDED
                   by section 1.27: pinned at 5206511...ceac.
                                              (OD-P16D-17 OPENED HERE, CLOSED)
CONSTANT-TIME      NARROWED, not closed. Signing is OpenSSL's; the guardian
                   secret operations and nonce use remain pure Python.
                   OD-P16D-05 is still the production blocker
VO-08              OPEN. ADR-102 proposed. PACK-17 not started
```

**A pre-existing repository defect, found and fixed.**
`tests/contract/test_reason_codes_registry.py` had been **skipping** rather
than passing since PACK-16D first landed, because PyYAML was not importable
— hiding roughly sixty-five reference-package reason-code literals that had
never been checked against `contracts/reason-codes/pack-03.yml`, through two
candidate rounds and two independent audits. Verified pre-existing by
running it against the untouched source tree, then fixed by excluding the
`reference/` subtree by path with the reason recorded in code. **A skipped
test is not a passing test**, and a suite reporting "17 skipped" that nobody
reads is a suite with unknown coverage.

**Source.** 6 files added, 2 deleted, 12 modified. The reference package
stays at 45 modules — one deleted, one added — and is now 7 534 lines; the
tests are 15 modules plus 2 oracles and 7 977 lines. **`uv.lock`,
`package-lock.json`, migrations, frontend files, CI workflows and every
version constant are unchanged, and no file under `docs/canonical/` was
modified.** `services/voting-service/pyproject.toml` gained one dependency
and the root `pyproject.toml` gained one pytest marker.

**FIR.** **No FIR outcome moved.** The correction improved the evidence
behind `FIR-ROADMAP-006`, `FIR-SEC-002` and `FIR-TRUST-001` without changing
any state. `FIR-SEC-002` in particular stays **blocked pending external
review**: using a well-reviewed library means somebody else's code was
reviewed, which is a different sentence from an external cryptographer
reviewing this system. **New FIR IDs: none. Statuses changed: none. None of
the eight unclosable items was closed.**

**Canon.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

`NO CANON CHANGE REQUIRED`. Swapping an implementation for a library is the
clearest possible case of a change invisible to canon: a signature that
verifies under the same key over the same bytes is the same signature
whoever's arithmetic produced it. The provider joins the service-level types
held on the PACK-12 / PACK-14 / PACK-15 precedent, bringing that list to ten.

**Acceptance matrix.** 90 rows: 75 `SATISFIED`, 7 `PARTIALLY SATISFIED`,
3 `DEFERRED`, 4 `BLOCKED`, 1 `NOT APPLICABLE`. Row 89 — the dependency lock
— is the only row that is unfinished rather than deferred.

**Verification.** **5 847 Python tests passed, 5 skipped, 0 failed, with no
`--ignore`** (the previous round: 5 616 passed, 17 skipped, _with_ one);
499 in the reference suite; `ruff check`, `ruff format --check` (497 files)
and `mypy services/voting-service` (70 source files) clean; all four
repository scripts pass. Line coverage 90.9 %. `uv sync --all-groups
--frozen` **was run** and failed on a third-party wheel with HTTP 403 after
building every workspace member — a network failure, not a lock
inconsistency, and **not a PASS**. **`uv lock`, `uv lock --check`, the
entire npm side, hypothesis and branch coverage were NOT executed.**

**PACK-17 is not started and must not start before independent acceptance of
PACK-16D.**

## 1.26 Round record — PACK-16D lockfile, provenance and acceptance-matrix correction (2026-08-02)

**Round:** PACK-16D — Final Lockfile, Immutable Provenance and
Acceptance-Matrix Correction. **A correction of the section 1.25 candidate,
not a new round.**
**Reference implementation candidate. Not production code. Not certified.
Not a PASS.**

**Repository version:** unchanged at `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:** `EPD2_PACK-16D_..._FINAL_REVIEW_CANDIDATE.zip`,
SHA-256 `ff3909bb1b8d195cfcb6c5c19ab2f63f7238daaa84c31a3bc573de0044b86de5`.

**The audit of that archive passed every cryptographic finding:**

```text
ARCHIVE HYGIENE:                          PASS
VETTED ED25519 PROVIDER:                  PASS
HANDWRITTEN ED25519 REMOVAL:              PASS
CHECKPOINT AUTHENTICITY:                  PASS
REAL EPD2-CRYPTO-1:                       PASS
3-OF-5 THRESHOLD PATH:                    PASS
4-OF-7 CONFIGURATION:                     PASS
TARGET-PROFILE CROSS-IMPLEMENTATION CORE: PASS
DEPENDENCY LOCK / FROZEN INSTALL:         FAIL
IMMUTABLE PARAMETER PROVENANCE:           FAIL
ACCEPTANCE MATRIX:                        NARROW CORRECTION REQUIRED
PACK-16D:                                 NOT YET ACCEPTED
PACK-17:                                  DO NOT START
```

```text
STATUS AFTER THIS ROUND - SUPERSEDED BY SECTION 1.27

DEPENDENCY LOCK:                          BLOCKED BY ENVIRONMENT
FROZEN CLEAN INSTALL:                     NOT EXECUTED
IMMUTABLE UPSTREAM IMPLEMENTATION
  PROVENANCE:                             PARTIALLY SATISFIED
CRYPTOGRAPHIC AND TARGET-PROFILE
  IMPLEMENTATION:                         UNCHANGED
PACK-16D:                                 NOT ACCEPTED
PACK-17:                                  DO NOT START
```

_The three findings above were environmental and were cleared on a
network-enabled host. Section 1.27 records the resolving evidence; this block
describes the state as of 2026-08-02 and must not be quoted as current._

**The matrix defect is the one worth recording for its own sake.** `AM-79`
asserted the parameter set was _immutably provenanced_ and carried status
`SATISFIED`, while the same row's evidence column recorded that the upstream
commit, the pinned URL and the source digest were all absent. **Nothing new
was learned to force the downgrade** — those facts were already in the
parameter artefact, in the evidence registry, and in the previous handover.
What was wrong was the status placed on top of them. An evidence column that
stays honest while a status column drifts optimistic is invisible to anyone
who reads only the status, and it is precisely what an audit that reads both
will find. `AM-79` is now `PARTIALLY SATISFIED`.

**Both blockers were re-attempted, not carried forward.** `uv lock`,
`uv sync --all-groups --frozen`, a clean-environment retry, and three
distinct GitHub access paths were all re-run and all refused. Every command
and every error string is reproduced verbatim in the new
`PACK-16D-ENVIRONMENT-BLOCKED-EVIDENCE.md`, because a blocker quoted from a
previous round's notes is indistinguishable from an excuse. Two distinct
refusal mechanisms are involved on the GitHub side — a per-repository access
broker and an egress allowlist — so this is not one misconfiguration.

**Nothing was invented to close a gap.** No commit SHA, no source digest, no
hand-edited `uv.lock`. An earlier round's `source_sha256`, computed over a
markdown rendering rather than raw bytes, stays withdrawn.

**Source.** 1 file added, 0 deleted, 11 modified. **No cryptographic,
guardian, checkpoint, conformance, transaction or sealed-batch code was
touched.** `uv.lock`, `package-lock.json`, migrations, frontend files, CI
workflows and every version constant are unchanged, and no file under
`docs/canonical/` was modified. `services/voting-service/pyproject.toml` is
unchanged from the source candidate.

**Acceptance matrix.** 90 rows: **74 `SATISFIED`, 8 `PARTIALLY SATISFIED`,
3 `DEFERRED`, 4 `BLOCKED`, 1 `NOT APPLICABLE`.** Requirement IDs `AM-01` …
`AM-90`, unique and contiguous; counts sum to the row count; `CORRECTED`
appears nowhere as a status.

**FIR.** **No FIR outcome moved.** A round that corrected a status and
recorded two blockers changed no delivery. `FIR-SEC-002` stays _blocked
pending external review_.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

**Verification.** **5 847 Python tests passed, 5 skipped, 0 failed, with no
`--ignore`**; 504 in the reference suite; `ruff check`,
`ruff format --check` (498 files) and `mypy services/voting-service` (70
source files) clean; all four repository scripts pass. The dependency guard
grew from 3 to 7 tests and now parses `uv.lock` as TOML rather than
searching it as text; five provenance tests were added.

**PACK-17 is not started and must not start before independent acceptance of
PACK-16D.**

## 1.27 Round record — PACK-16D network-enabled finalization (2026-08-03)

**Round:** PACK-16D — Network-Enabled Finalization: Lockfile Regeneration,
Immutable ElectionGuard Provenance and Final Acceptance Alignment. **A
narrow finalization of the section 1.26 candidate, not a new round.**
**Reference implementation candidate. Not production code. Not certified.
Not a PASS.**

**Repository version:** unchanged at `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:** `EPD2_PACK-16D_..._ENVIRONMENT_BLOCKED_CANDIDATE.zip`,
SHA-256 `a6fc8b670991d51a9a3f4d6ce1db5306166506513b43c85662ab3317c48b947c`.

**What this round did.** Nothing cryptographic. The two blockers section 1.26
recorded as environmental were cleared on a host with the network access they
needed, and the repository was aligned to that evidence.

```text
STATUS AFTER THIS ROUND

DEPENDENCY LOCK:                          REGENERATED
                                          cryptography 46.0.7 from
                                          https://pypi.org/simple, hashes on
                                          43 artefacts, cffi 2.1.0 +
                                          pycparser 3.0, inside the
                                          epd2-voting-service graph
                                                      (OD-P16D-16 CLOSED)
FROZEN CLEAN INSTALL:                     EXECUTED ON A NETWORK-ENABLED HOST
                                          uv sync --all-groups --frozen,
                                          Checked 61 packages; NOT re-run in
                                          the build session, which has no
                                          package index
IMMUTABLE UPSTREAM IMPLEMENTATION
  PROVENANCE:                             RECORDED
                                          microsoft/electionguard-rust at
                                          520651138110a13f777409e96606454df928ceac
                                          (2025-02-02),
                                          src/eg/src/standard_parameters.rs,
                                          sha256 ad38bfa6...5770,
                                          retrieved 2026-08-03
                                                      (OD-P16D-17 CLOSED)
CRYPTOGRAPHIC AND TARGET-PROFILE
  IMPLEMENTATION:                         UNCHANGED
VO-08:                                    OPEN
ADR-102:                                  proposed
PACK-16D:                                 REQUIRES INDEPENDENT AUDIT
PACK-17:                                  DO NOT START
```

**One discrepancy is recorded rather than silently corrected.** The
finalization brief quoted the new `uv.lock` digest as `02d0775458…`; the digest
computed over the delivered file's actual bytes is `b2d0775458…`. The two agree
in 63 of 64 hex characters, which no byte-level corruption produces — SHA-256
avalanche makes a one-nibble difference about as likely as guessing the digest
outright — so this is a transcription slip in the brief. The computed value
governs, because it is the one anybody can reproduce from the file.

**What was verified rather than accepted.** The supplied lock was parsed as
TOML, not searched as text: `cryptography` resolves at `46.0.7` from a registry
with `sha256:`-prefixed hashes on every artefact, both transitives are locked,
the entry sits in `epd2-voting-service`'s own dependency list rather than at the
workspace root, `requires-dist` echoes the manifest specifier, and the lock delta
is purely additive — 149 lines added, none removed, no existing package's version
changed. The imported library's version is asserted equal to the locked one, so
a green suite against some other build cannot pass as evidence about this one.

**What was not done here, and is recorded as not done here.** The frozen install
and the upstream byte fetch both happened on the network-enabled host. The build
session verified the lock's contents and the pin's internal consistency and
re-derived every parameter offline; it did not re-run `uv sync` and did not
re-fetch the upstream file. `source_sha256_verification_scope` in the parameter
artefact states this where a verifier will look, and names the one command that
closes it: `curl -sL <pinned-url> | sha256sum`.

**Two matrix rows were promoted, and neither on the blocker's disappearance.**
`AM-79` and `AM-89` moved to `SATISFIED` against the five conditions each row
requires, every one of which is asserted by a named offline test. The previous
correction's defect was a status drifting ahead of its evidence; promoting on
"the obstacle went away" would be the same error pointed the other way.

**Source.** 0 files added, 0 deleted; `uv.lock` plus the parameter artefact,
two test modules and the documentation set. **No cryptographic, guardian,
checkpoint, conformance, transaction or sealed-batch logic was touched.**
`package-lock.json`, migrations, frontend files, CI workflows and every version
constant are unchanged, and no file under `docs/canonical/` was modified.

**Acceptance matrix.** 90 rows: **76 `SATISFIED`, 6 `PARTIALLY SATISFIED`,
3 `DEFERRED`, 4 `BLOCKED`, 1 `NOT APPLICABLE`.** Requirement IDs `AM-01` …
`AM-90`, unique and contiguous; counts sum to the row count; `CORRECTED`
appears nowhere as a status.

**Open decisions.** `OD-P16D-16` and `OD-P16D-17` closed on recorded command
output; nothing else moved. `VO-08`, external cryptographic review, a fully
independent verifier, full ElectionGuard ecosystem interoperability,
constant-time production assurance, production HSM and key custody, the
production guardian ceremony and legal certification all remain **OPEN**.

**FIR.** **No FIR outcome moved.** `FIR-SEC-002` stays _blocked pending
external review_: a hash-pinned lock and a commit-pinned source are supply-chain
and traceability properties, and assurance remains a statement an external
cryptographer makes about this system.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

No Canon domain, aggregate, event or invariant semantics changed.

Canon compatibility metadata continues to support
repository version 0.16.x.
```

**Verification.** **5 851 Python tests passed, 5 skipped, 0 failed, with no
`--ignore`**; 506 in the reference suite; `ruff check`,
`ruff format --check` (498 files) and `mypy services/voting-service` (70
source files) clean; all four repository scripts pass. The dependency guard
grew from 7 to 9 tests and the provenance tests from 30 to 32; **every
dual-state branch in both was removed**, so a `null` commit or a missing lock
entry now fails rather than being tolerated.

**Source.** 0 files added, 0 deleted, 24 modified.

**PACK-17 is not started and must not start before independent acceptance of
PACK-16D.**

## 1.28 Round record — PACK-17A specification and ADR (2026-08-04)

**Round:** PACK-17A — Independent Verification, Resilience and Incident
Readiness. **Specification and ADR candidate. No implementation. Not a PASS.**

**Repository version:** unchanged at `0.16.0`.
**Canon version:** unchanged at `0.8.0`.

**Baseline:** `EPD2_PACK-16D_FINAL_ACCEPTANCE_CANDIDATE.zip`, SHA-256
`97f0cf950825bacd4c64cf7b66c9e5ebc27c332a1c2684b71cdd5efebfbb9577`, verified
on receipt.

**The start gate recorded in section 1.27 was not met.** No independent
acceptance of PACK-16D exists in this repository: `docs/handover/` carries no
PACK-16D external verification result, and the last recorded external CI
verification is PACK-15's. This round was directed to start regardless. The
gate is recorded as unmet rather than deleted or declared satisfied, and is
carried as `OD-P17A-01`, which blocks **PACK-17A's own acceptance** and
nothing technical — PACK-17A is specification only, so nothing it produces
depends on PACK-16D's implementation being correct.

**What this round did.** Closed `AGR-26` in specification form. Twenty
documents under `docs/packs/PACK-17/`, six ADRs (`ADR-103` … `ADR-108`, all
`proposed`), one single-entry local CI driver with two wrappers, and one
repository test.

```text
STATUS AFTER THIS ROUND

SPECIFICATION:                            WRITTEN
IMPLEMENTATION:                           NONE
INDEPENDENT VERIFICATION:                 NOT PERFORMED
EXTERNAL CRYPTOGRAPHIC REVIEW:            NOT PERFORMED
EXERCISES:                                NONE PERFORMED
BACKUP RESTORES:                          NONE PERFORMED
PRODUCTION READINESS:                     NOT CLAIMED
LEGAL ACTIVATION:                         NOT CLAIMED
```

**Source.** 30 files added, 0 deleted, 3 modified (`CHANGELOG.md`, this
register, `LOCAL_VERIFICATION.md`). No service module, migration, contract,
reason code, event schema or frontend file was added or changed. No file under
`docs/canonical/` was modified. `uv.lock` and `package-lock.json` are
unchanged, and every frozen PACK-16D cryptographic artefact is byte-identical
with its digest recorded in `docs/packs/PACK-17/PACK-17A-EVIDENCE-REGISTRY.md`
§2.

**Acceptance matrix.** 90 rows, `AM17-01` … `AM17-90`: **70 `SATISFIED`,
8 `PARTIALLY SATISFIED`, 8 `DEFERRED`, 3 `BLOCKED`, 1 `NOT APPLICABLE`.**
`SATISFIED` means _specified_ and never implemented, tested, verified or
activated; `PASS` appears nowhere as a status.

**Open decisions.** **14 opened (`OD-P17A-01` … `OD-P17A-14`), 0 closed.**
`VO-08`, `VO-02`, `VO-03`, `OD-P16B-02/03`, `OD-P16C-08/09/10/11/12/18/19` and
`OD-P16D-02/04/05/06/11/12` are all carried forward **unchanged**.

**FIR.** **No FIR outcome moved and no new FIR ID was created.**
`FIR-ROADMAP-007`, `FIR-SEC-001`, `FIR-SEC-002` and `FIR-SEC-003` are
addressed in specification form only. `FIR-ROADMAP-007`'s target version of
`0.17.0` is unchanged and **not reached**: this round adds no runtime code, and
the three PACK-16 specification rounds each left the repository version alone.

**Verification.** `check_repository.py`, `check_forbidden_files.py`,
`check_archive_hygiene.py` and `verify_versions.py` all executed and passed.
**`uv sync`, Ruff, Mypy, pytest, `npm ci`, the npm workspace scripts and
Prettier 3.9.6 were NOT EXECUTED** — the round ran on a host without network
access, and no unavailable check was converted into a pass. Repository-wide
Prettier verification is an unresolved validation item for the next
network-enabled run; the PACK-16D Prettier allowlist was **not** modified and
stands at 130 entries with no PACK-17 path.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

Eleven candidate concepts assessed; all eleven held at service level on the
PACK-12, PACK-14, PACK-15 and PACK-16D precedent.

One close case recorded: a ContinuityDecision's effect on a legal deadline.
Resolved as a governed decision in PACK-09's owning context referencing the
operational record as evidence. If PACK-17B finds that inexpressible, it is a
CANON AMENDMENT REQUIRED finding and must be raised as its own amendment.
```

**PACK-17B must not start before independent review of PACK-17A**, and must
resolve `OD-P17A-13` — the placement of the operational domain — before
writing any service code.

### 1.28.1 Local CI runtime correction (2026-08-04)

**A narrow correction of the section 1.28 candidate, not a new round.** Three
runtime defects in `scripts/run_epd2_local_ci.py`, found by running it on a
real Windows host: OpenSSL was discovered and then discarded rather than
propagated to child processes; `pytest` ran on Windows without an IANA timezone
database and failed finance-service collection on `Europe/Berlin`; and the
target-conformance benchmark rewrote the accepted timing artefact, so a
successful run failed the frozen-artefact check afterwards.

**Repository version:** unchanged at `0.16.0`. **Canon version:** unchanged at
`0.8.0`. **No dependency changed** — `uv.lock` and `package-lock.json` are
byte-identical, and the Windows timezone database is supplied ephemerally as
`tzdata==2025.2` rather than added to the lock. **No PACK-16D artefact changed.**

**Source.** 1 file added (`tests/repository/test_pack17a_local_ci_driver.py`,
30 executed regression checks), 0 deleted, 6 modified: the driver, the
handover, the acceptance matrix, the evidence registry, `LOCAL_VERIFICATION.md`
and `CHANGELOG.md`. **No PACK-17A architecture, ADR decision, Canon decision,
open decision or `VO-08` status changed.**

**Acceptance matrix.** 94 rows, `AM17-01` … `AM17-94`: **73 `SATISFIED`,
9 `PARTIALLY SATISFIED`, 8 `DEFERRED`, 3 `BLOCKED`, 1 `NOT APPLICABLE`.** Rows
91–94 were added for the correction and are the only rows in the matrix whose
evidence is an executed test rather than a document section.

**Not executed.** `uv sync`, Ruff, Mypy, pytest, `npm ci`, the npm workspace
scripts and Prettier 3.9.6 remain **NOT EXECUTED** — still no network access.
The corrected paths were verified structurally and by the regression suite; the
driver's full pass is still not claimed. `tzdata==2025.2` could not be resolved
against a package index here and is recorded as `PARTIALLY SATISFIED` at
`AM17-92`.

## 1.29 Round record — PACK-17B implementation and executable evidence (2026-08-04)

**Round:** PACK-17B — Independent Election-Record Verification, Archive
Integrity and Adversarial Corpus. **Implementation and executable-evidence
candidate. Not externally certified. Not production ready. Not legally
activated.**

**Repository version:** `0.16.0` → **`0.17.0`**. This round ships executable
implementation, which is the condition the three PACK-16 specification rounds
and PACK-17A did not meet. **Canon version:** unchanged at `0.8.0`.

**Baseline:** `EPD2_PACK-17A_LOCAL_CI_RUNTIME_CORRECTED_CANDIDATE.zip`,
SHA-256 `08ea15f487df2ab5280299374750833d9f510c47d926683daeb4a5fa7ed71caa`,
verified on receipt.

**What this round did.** Implemented the independent-verification portion of
PACK-17A as a separate package: `EPD2-ARCHIVE-1` container reader, strict
byte-level JSON parser, a reimplementation of the canonical grammar,
signature and signer-authorization verification, checkpoint chain, rollback
and split-view detection, a 44-case adversarial corpus, a comparison harness
against the PACK-16D reference implementation, and installed-wheel evidence.

```text
STATUS AFTER THIS ROUND

INDEPENDENTLY STRUCTURED IMPLEMENTATION:  BUILT
EXECUTABLE EVIDENCE:                      147 first-party checks passed
INTERNAL COMPARISON:                      0 acceptance disagreements
EXTERNAL INDEPENDENT VERIFICATION:        NOT ACHIEVED, NOT ACHIEVABLE HERE
EXTERNAL CRYPTOGRAPHIC REVIEW:            NOT PERFORMED
INTEROPERABILITY:                         NOT DEMONSTRATED
TRUSTED TIME:                             NOT AVAILABLE
PRODUCTION READINESS:                     NOT CLAIMED
LEGAL ACTIVATION:                         NOT CLAIMED
```

**Finding F-17B-01.** `revoked` and `roles` fall outside the PACK-16D
signer-record canonical encoding and therefore outside `registry_digest`, so
a substituted registry can un-revoke a signer or grant it a role without
changing the published digest. Classified as an **architectural ambiguity
with a security consequence**, not an implementation defect: the accepted
code matches its own specification, and the specification does not say what
the digest must cover. The verifier now fails closed with
`SIGNER_AUTHORIZATION_UNBOUND`; the accepted construction is byte-identical
and untouched. Format evolution on the producing side is `OD-P17B-01` and is
an **activation blocker**.

**Acceptance matrix.** 44 rows, `AM17B-01` … `AM17B-44`: **27 `EXECUTABLE
EVIDENCE PASSED`, 6 `BLOCKED`, 5 `DEFERRED`, 3 `IMPLEMENTED`, 2 `INTERNALLY
COMPARED`, 1 `PARTIALLY SATISFIED`.** `EXTERNALLY INDEPENDENTLY VERIFIED`
appears in zero rows.

**Open decisions.** 8 opened (`OD-P17B-01` … `OD-P17B-08`), **2 closed** —
both implementation-specific, with executed evidence — and `OD-P17A-13`
narrowed but not closed. `VO-08`, `VO-02`, `VO-03`, every `OD-P16*` entry and
`OD-P17A-01` … `OD-P17A-14` are carried forward **unchanged**.

**FIR.** `FIR-ROADMAP-007` remains `approved`; its verification portion now
has a reference implementation, and its resilience, continuity and
incident-response portions are untouched. **No FIR outcome moved to
`implemented`** and no new FIR ID was created.

**Verification.** Executed: five test suites (147 checks), the adversarial
corpus, the comparison harness, the wheel build, a clean external
installation, the installed CLI, and the four repository scripts.
**NOT EXECUTED:** `uv sync`, Ruff, Mypy, full pytest, `npm ci`, the npm
workspace scripts and Prettier 3.9.6 — no network access, and no unavailable
check was converted into a pass.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

The verifier reads published record formats and tool-level contracts. It
introduces no cross-domain semantic that canon must express.

Only canon compatibility metadata moved: repository_compatibility now
supports repository version 0.17.x.
```

**PACK-17C must not start before independent review of PACK-17B**, and must
resolve `OD-P17B-01` — the signer-registry authorization binding — as a
compatible format evolution on the producing side.

## 1.30 Round record — PACK-17B-C1 signer-registry authorization binding correction (2026-08-04)

**A narrow correction of the section 1.29 candidate, not a new round.**
Resolves the format half of finding **F-17B-01**: `roles` and `revoked` were
outside the signer-registry digest inherited from PACK-16D, so a substituted
registry could grant a role or un-revoke a signer without changing it.

**Repository version:** `0.17.0` → **`0.17.1`**. **Verifier package:**
`0.1.0` → **`0.1.1`**. **Canon version:** unchanged at `0.8.0`; no canon-owned
file changed, including `canon-version.json`.

**Baseline:** `EPD2_PACK-17B_..._IMPLEMENTATION_CANDIDATE.zip`, SHA-256
`161bc7014c293556c70aa6671bb561b7c5c562698f540b269df7da1cf0b2520c`.

**What this round did.** Introduced `EPD2-SIGNER-REGISTRY-2` under three new
domain labels, with the version carried inside the digested bytes so v1 can
never be read as v2. Sixteen authorization-relevant fields are bound. The
producing side emits it; the independent verifier derives it from the format
specification without importing the producing side.

```text
STATUS AFTER THIS ROUND

AUTHORIZATION BINDING:                    DELIVERED (v2)
PRODUCING SIDE:                           EMITS v2
INDEPENDENT VERIFIER:                     DERIVES v2 INDEPENDENTLY
LEGACY v1:                                READABLE, FAIL-CLOSED, NO
                                          AUTHORIZATION CLAIM
v1 -> v2 MIGRATION:                       BLOCKED (OD-P17BC1-02)
F-17B-01:                                 PARTIALLY RESOLVED, NOT CLOSED
EXTERNAL INDEPENDENT VERIFICATION:        NOT ACHIEVED
```

**Source.** 12 files added, 0 deleted, 20 modified. No vote, tally, credential
or eligibility logic changed. Three domain labels were added to the PACK-16D
registry; **no existing label, encoding or digest changed**, and every frozen
PACK-16D artefact is byte-identical.

**Acceptance matrix.** 39 rows, `AMC1-01` … `AMC1-39`: **28 `EXECUTABLE
EVIDENCE PASSED`, 4 `BLOCKED`, 3 `INTERNALLY COMPARED`, 2 `DEFERRED`, 1
`IMPLEMENTED`, 1 `PARTIALLY SATISFIED`.** `EXTERNALLY INDEPENDENTLY VERIFIED`
appears in zero rows.

**Open decisions.** 4 opened (`OD-P17BC1-01` … `-04`), **1 closed**
(`OD-P17B-01`, the format decision this round existed to make). Everything
else carried forward unchanged, including `VO-08`.

**Evidence.** 200 first-party checks passed across six suites; adversarial
corpus 72/72 at declared code and stage; comparison harness 99 `BOTH_ACCEPT`
and 73 `BOTH_REJECT_SAME_REASON` with **0 acceptance disagreements**; 28
governed vectors re-derived clean; wheel built and installed into a clean
environment, verifying a v2 archive with the source tree unavailable.

**Not executed.** `uv sync`, Ruff, Mypy, full pytest, `npm ci`, npm workspace
scripts, Prettier 3.9.6 and the hatchling wheel build — no network access, and
no unavailable check was converted into a pass.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

Signer-registry encoding is a cryptographic publication format and a
service/tool-level contract. No canon-owned file was modified.
```

**PACK-17C must not start before independent review of PACK-17B-C1**, and
must answer `OD-P17BC1-02` — who may authorise a v1 to v2 registry transition
— before any migration is attempted.

## 1.31 Round record — PACK-17B-C2 checkpoint-to-signer-registry binding correction (2026-08-04)

**A narrow follow-up correction to section 1.30, not a new round.** Closes
`OD-P17BC1-03`: the signer-registry version and digest were not
cryptographically bound into the signed checkpoint payload, so a correctly
signed checkpoint could be repackaged beside a different registry — one
granting a role, restoring a revoked signer, or simply older — and every
individual check would still pass.

**Repository version:** `0.17.1` → **`0.17.2`**. **Verifier package:**
`0.1.1` → **`0.1.2`**. **Canon version:** unchanged at `0.8.0`; no canon-owned
file changed.

**Baseline:** `EPD2_PACK-17B_C1_..._CORRECTED_CANDIDATE.zip`, SHA-256
`24b97efd99e74693ef30b8b20f5b7cd6799460b439f78338d1c8de7251a69aeb`.

**What this round did.** Introduced checkpoint payload `EPD2-CHECKPOINT-3`
under the new domain label `EPD2/v3/board_checkpoint`, carrying the signer
registry's format version, aggregate digest, sequence and predecessor link —
plus organization scope and checkpoint purpose — inside the signed bytes. The
producing side derives the binding from the registry object used for
authorisation and refuses to sign for an unauthorised signer; the independent
verifier re-derives the registry digest from archive bytes and compares it
with the value inside the signed payload before authorising anything.

```text
STATUS AFTER THIS ROUND

CHECKPOINT-TO-REGISTRY BINDING:           DELIVERED (EPD2-CHECKPOINT-3)
PRODUCING SIDE:                           REFERENCE IMPLEMENTATION ONLY
INDEPENDENT VERIFIER:                     DERIVES AND CHECKS IT
LEGACY CHECKPOINTS:                       READABLE, FAIL-CLOSED, NO
                                          AUTHORIZATION CLAIM
CHECKPOINT CHAIN MIGRATION:               OPEN (OD-P17BC2-01)
OD-P17BC1-03:                             CLOSED
F-17B-01:                                 TECHNICALLY CLOSED
OD-P17B-02:                               OPEN
EXTERNAL INDEPENDENT VERIFICATION:        NOT ACHIEVED
```

**Source.** 12 files added, 0 deleted, 24 modified. No election-record, tally,
credential, eligibility or voting-client logic changed. One domain label was
added; **no existing label, encoding or digest changed**, and every frozen
PACK-16D artefact and the PACK-17B-C1 governed vector set are byte-identical.

**Acceptance matrix.** 46 rows, `AMC2-01` … `AMC2-46`: **37 `EXECUTABLE
EVIDENCE PASSED`, 4 `BLOCKED`, 2 `INTERNALLY COMPARED`, 2 `DEFERRED`, 1
`IMPLEMENTED`.** `EXTERNALLY INDEPENDENTLY VERIFIED` appears in zero rows.

**Open decisions.** 3 opened (`OD-P17BC2-01` … `-03`), **1 closed**
(`OD-P17BC1-03`). Everything else carried forward unchanged, including
`VO-08` and `OD-P17BC1-02`.

**Evidence.** 244 first-party checks passed across seven suites; adversarial
corpus 93/93 at declared code and stage; comparison harness 177 `BOTH_ACCEPT`
and 94 `BOTH_REJECT_SAME_REASON` with **0 acceptance disagreements**; 23 new
governed vectors re-derived clean; wheel built and installed into a clean
environment, verifying a corrected archive with the source tree unavailable.

**Not executed.** `uv sync`, Ruff, Mypy, full pytest, `npm ci`, npm workspace
scripts, Prettier 3.9.6 and the hatchling wheel build — no network access, and
no unavailable check was converted into a pass.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

The checkpoint payload is a cryptographic publication format and a
service/tool-level contract. No canon-owned file was modified.
```

**PACK-17C must not start before independent review of PACK-17B-C2**, and its
first task is `OD-P17B-02` — a real producing side. Two consecutive
first-party corrections to the same area, with no archive from outside this
repository's test builder ever verified, is the signal that the next defect
will be found there rather than here.

## 1.32 Round record — PACK-17C production-facing election-record producer (2026-08-04)

**Round:** PACK-17C — Production-Facing Election Record Producer, Checkpoint
Publication and Immutable Archive Pipeline. **Implementation and
executable-evidence candidate. NOT deployed to production.**

**Repository version:** `0.17.2` → **`0.18.0`** — a minor bump, because this
round adds a capability rather than correcting shipped behaviour. **Canon
version:** unchanged at `0.8.0`; only the compatibility ceiling moved, to
`<0.19.0`.

**Baseline:** `EPD2_PACK-17B_C2_..._CORRECTED_CANDIDATE.zip`, SHA-256
`c9f1977a44602b549c2be0eba0981351faa3b4605a1238b2d7f5c155498304ec`.

**What this round did.** Closed the **implementation half** of `OD-P17B-02`.
Until now the only thing emitting the governed archive format was the
independent verifier's own test builder. There is now a service-facing
producer at `epd2_voting_service.publication`, reachable from
`epd2-publish-record`, with a 14-state governed lifecycle, strict versioned
input contracts, a disclosure allowlist, deterministic archive assembly, a
byte-level self-verification gate that invokes the independent verifier
**across a process boundary**, maker-checker publication authorization, an
idempotent append-only publication protocol, mandatory read-back
verification, an append-only ledger and twelve governed failure events for
PACK-17D.

```text
STATUS AFTER THIS ROUND

SERVICE-FACING PRODUCER:                  BUILT
RUNS FROM AN INSTALLED PACKAGE:           YES
ARCHIVES ACCEPTED BY THE VERIFIER:        YES (process boundary)
DEPLOYED TO PRODUCTION:                   NO
PROVIDER ADAPTER:                         NO (reference adapter only)
PUBLISHED TO A REAL DESTINATION:          NO
OD-P17B-02:                               PARTIALLY CLOSED
EXTERNAL INDEPENDENT VERIFICATION:        NOT ACHIEVED
```

**Source.** 11 files added, 0 deleted, 12 modified. No voting cryptography,
tally, credential, eligibility or voting-client logic changed. Every frozen
PACK-16D artefact and both PACK-17B vector sets are byte-identical, and no
dependency lock moved.

**Acceptance matrix.** 52 rows, `AMC3-01` … `AMC3-52`: **42 `EXECUTABLE
EVIDENCE PASSED`, 5 `BLOCKED`, 3 `DEFERRED`, 1 `INTERNALLY COMPARED`, 1
`IMPLEMENTED`.** `EXTERNALLY INDEPENDENTLY VERIFIED` appears in zero rows.
Rows 44 and 45 keep `OD-P17B-02`'s two halves apart.

**Open decisions.** 6 opened (`OD-P17C-01` … `-06`), **1 closed**
(`OD-P17B-02`, implementation half only). Everything else carried forward
unchanged.

**Evidence.** 301 first-party checks passed across nine suites; corpus 93/93;
comparison harness 186 `BOTH_ACCEPT` and 94 `BOTH_REJECT_SAME_REASON` with
**0 acceptance disagreements**, now including eight rows over the producer's
own archives; two wheels built and installed into a clean environment, with a
complete publication run from site-packages and the source tree absent.

**Not executed.** `uv sync`, Ruff, Mypy, full pytest, `npm ci`, npm workspace
scripts, Prettier 3.9.6 and the hatchling wheel build — no network access —
and **no publication to a real destination**, because nothing is deployed.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

The publication pipeline is a service-level application path over existing
cryptographic publication formats. No canon-owned semantic changed.
```

**PACK-17D must not start before independent review of PACK-17C**, and its
first task is the incident lifecycle over the twelve governed failure events
this round emits and nothing yet consumes.

## 1.33 Round record — PACK-17C-C1 verifier runtime and executable contract correction (2026-08-04)

**A narrow runtime-integration correction to section 1.32, not a new round.**
Closes finding **F-17C-01**: the production-facing `VerificationGate`
launched `sys.executable -m epd2_independent_verifier.cli`, but the
independent verifier is not a uv workspace member, so a standard
`uv sync --all-groups --frozen` does not install it. Ordinary repository
pytest failed (**16 failed, 111 passed**) before any specialised stage ran,
and the only thing that made the relevant suite pass was a manual
`PYTHONPATH` in the PACK-17C test module.

**Repository version:** `0.18.0` → **`0.18.1`**. **Voting service:** `0.1.0`
→ **`0.1.1`**. **Independent verifier:** unchanged at `0.1.2`. **Canon:**
unchanged at `0.8.0`.

**Baseline:** `EPD2_PACK-17C_..._CANDIDATE.zip`, SHA-256
`0cff1c2091616883813cbca18c5cbba7b6095c467da55b184999878e50aa5017`.

**Runtime model chosen: a managed dedicated verifier environment.**
`scripts/verifier_runtime.py` builds the verifier from the repository,
installs it outside the repository, version-gates and smoke-tests it, and
returns an exact console-script path. The repository `conftest.py` and the
local CI preflight call the same function, so there is one runtime model
rather than two. Workspace membership is recorded as `OD-P17CC1-01` for a
networked round: it alters the resolved graph and `uv.lock`, which this
environment cannot regenerate reproducibly.

```text
STATUS AFTER THIS ROUND

VERIFIER RUNTIME:                         PREPARED BEFORE PYTEST
EXECUTABLE CONTRACT:                      EXACT ABSOLUTE PATH
ENVIRONMENT ISOLATION:                    ALLOWLIST; PYTHONPATH REMOVED
MANUAL PYTHONPATH:                        REMOVED, AND GUARDED BY TEST
PROCESS/PACKAGE BOUNDARY:                 PRESERVED
F-17C-01:                                 CLOSED
OD-P17B-02 implementation half:           CLOSED
OD-P17B-02 deployment half:               OPEN
EXTERNAL INDEPENDENT VERIFICATION:        NOT ACHIEVED
```

**Source.** 12 files added, 0 deleted, 11 modified. No producer state machine,
publication semantic, archive format, cryptographic encoding or domain label
changed. **No dependency changed and no lock file moved.**

**Acceptance matrix.** 42 rows, `AMCC1-01` … `AMCC1-42`: **33 `EXECUTABLE
EVIDENCE PASSED`, 3 `DEFERRED`, 3 `BLOCKED`, 2 `IMPLEMENTED`, 1 `INTERNALLY
COMPARED`.** `EXTERNALLY INDEPENDENTLY VERIFIED` appears in zero rows.

**Open decisions.** 2 opened (`OD-P17CC1-01`, `-02`), **1 finding closed**
(`F-17C-01`). Everything else carried forward unchanged.

**Evidence.** 331 first-party checks across ten suites, with **no manual
`PYTHONPATH`**; corpus 93/93; harness 0 acceptance disagreements; both wheels
built and installed into a clean external environment; producer and verifier
loaded from `site-packages` and exercised from a non-repository directory;
publication blocked when the verifier is unavailable.

**Not executed.** `uv sync --all-groups --frozen`, `uv run pytest`, Ruff,
Mypy, the target-conformance benchmark, `npm ci`, npm workspace scripts,
Prettier 3.9.6 and the hatchling wheel build — no network access, and no
unavailable check was converted into a pass.

**Canon.**

```text
CANON_VERSION remains 0.8.0.

NO CANON CHANGE REQUIRED.

Runtime integration and packaging are tool-level concerns. No canon-owned
file was modified.
```

**PACK-17D must not start before independent review of PACK-17C-C1**, and its
first action should be a networked run: `uv sync`, `uv run pytest`, Ruff,
Mypy, npm, Prettier, hatchling and `OD-P17CC1-01` are one session's work with
a package index, and the cheapest remaining evidence in the programme.

## 1.34 Round record — PACK-17C-C2 Windows full-CI corrections (2026-08-04)

**A correction round driven by external execution evidence: two Windows CI
runs on the operator's own host.** The first, extracted to a long path, was
**invalidated** — Windows dropped ~180 files above `MAX_PATH`. The second,
from `C:\e`, is authoritative and established that `uv sync` passes on
Python 3.12.13, target conformance is 15/15, the timing artefact restores
byte-for-byte, and ordinary pytest reaches 6000 passed / 28 failed.

**Repository version:** `0.18.1` → **`0.18.2`**. `epd2-voting-service`
reverted `0.1.1` → `0.1.0`. **Canon unchanged at `0.8.0`.** `uv.lock` and
`package-lock.json` byte-identical.

**Eight findings closed** — `F-17C-02` through `F-17C-09` — each recorded
separately rather than as a generic CI issue: Windows extraction path length,
stale governed version assertions, a verifier runtime installed without its
cryptographic dependency, global-Python misuse in dependency-bearing stages,
Unix-only test fixtures, a reason-code scanner that classified `PATH` and
`VERIFIED` as reason codes, a missing `mypy_path` entry, and hygiene that
expected a pristine tree after the tools had run. `F-17C-01` remains closed.

**Acceptance matrix.** 47 rows: 36 `EXECUTABLE EVIDENCE PASSED`, 4
`IMPLEMENTED`, 3 `DEFERRED`, 3 `BLOCKED`, 1 `INTERNALLY COMPARED`.

**Evidence.** 349 first-party checks across eleven suites; corpus 93/93;
harness 0 acceptance disagreements; verifier runtime built without system
site packages and passing a real Ed25519 smoke test.

**Not executed.** Ruff, Ruff-format, Mypy, `uv sync`, `uv run pytest`, npm and
**Prettier 3.9.6** — no network. The Ruff and Mypy corrections are made
against the log's exact findings and are claims until a networked host
confirms them. **Prettier had no change made at all**, because approximating
it is what created the sixty-nine failing files in the first place.

**Canon.**

```text
CANON_VERSION remains 0.8.0.
NO CANON CHANGE REQUIRED.
```

**PACK-17D must not start before a networked verification session and a
short-path Windows rerun.**

## 1.35 Round record — PACK-17D incident lifecycle and publication failure response (2026-08-05)

**A new implementation pack.** Repository `0.18.2` -> **`0.19.0`**; Canon
unchanged at `0.8.0`; independent verifier `0.1.2`; voting service `0.1.0`.
All nine frozen artefacts byte-identical.

**Governed failure events: exactly twelve**, counted from `FailureEventType`
in the producer rather than from the review report. No event was invented.

**Delivered.** Ten incident states with an explicit transition matrix
(`CLOSED`/`ANNULLED` terminal, `RECOVERED` not terminal, no `DETECTED` ->
`CLOSED`, failed recovery moves backwards, no reopening by mutation); four
deterministic severities; twelve response policies with no wildcard; fourteen
bounded containment actions and nine permanently forbidden ones; maker-checker
on eight sensitive actions with the publication producer barred from approving
its own failure; append-only hash-linked evidence under the new domain label
`EPD2/v1/incident_history`; six deadline classes that escalate but never
close or downgrade; and an evidence-driven recovery protocol that refuses to
infer freshness without trusted prior state.

**Boundary.** Inside the voting service, beside the producer. No new
microservice; `ADR-112` records the decision and what would reverse it.

**Acceptance matrix.** 50 rows: 39 `EXECUTABLE EVIDENCE PASSED`, 4
`DEFERRED`, 3 `BLOCKED`, 3 `IMPLEMENTED`, 1 `INTERNALLY COMPARED`.
`EXTERNALLY INDEPENDENTLY VERIFIED` appears in zero rows.

**Evidence.** 65 new tests; 414 first-party checks total, 0 failed; corpus
93/93; harness 0 acceptance disagreements; canon 18/18.

**Not executed.** Ruff, Ruff-format, Mypy, `uv sync`, `uv run pytest`, target
conformance, npm and Prettier — no network. **The new code has not been read
by a linter, a type checker or a formatter.**

**Open decisions.** `OD-P17A-02` and `OD-P16D-02` remain **OPEN** and are not
marked satisfied anywhere. Six new decisions opened, `OD-P17D-01` .. `-06`,
of which `OD-P17D-03` (who resolves a split view) is a limit of the evidence
rather than a gap in the implementation.

**Canon.**

```text
CANON_VERSION remains 0.8.0.
NO CANON CHANGE REQUIRED.
Only the repository_compatibility ceiling moved, to <0.20.0.
```

## 1.68 Documentation-only correction — Canonical frontend visual baseline lock (2026-08-25)

**Round:** documentation/governance correction only. No frontend code, token, component or accepted reference screenshot is changed by this round.

**Reason:** `FIR-UX-003` and `FIR-UX-010` previously described FRONT-00/FRONT-01 as an authoritative reference while still permitting ordinary frontend work to “evolve”, “replace” or improve it. That ambiguity is removed.

**Governed rule:** accepted FRONT-00/FRONT-01 visual implementation is the **canonical immutable visual baseline**. Existing typography, spacing, colors, borders, radii, layout/grid geometry, header/footer/navigation treatment, component styling, responsive behavior, interaction states and accepted reference screenshots must be reused exactly where they already exist. New functionality may extend pages and compose existing primitives, but it may not restyle existing blocks.

The only exception is a separate explicit governed **Design Change Decision** approved before implementation and naming the exact affected baseline element, with rationale, before/after screenshots, accessibility evidence and visual-regression impact. A feature requirement, implementation convenience, developer preference, mockup or “modernization” is not such approval.

**FIR IDs changed:** requirement wording of `FIR-UX-003` and the directly conflicting acceptance wording in `FIR-UX-010`; both statuses remain `approved`. No FIR status changes.

**FIR IDs implemented:** none. **New FIR IDs:** none.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`; final FRONT closure remains future.

## 1.69 Documentation-only refinement — Regional/local frontend operating model (2026-08-25)

**Round:** documentation/governance refinement only. No runtime, organization, membership, voting or administrative authority is activated by this round.

**Governed decision:** Landes-, Kreis-, Orts- and other regional party bodies use one EPD² platform with organization-scoped public and authenticated views. They do not receive separate independently designed local products, separate identity systems or separate voting engines.

Public regional hubs use `/regionen` and `/regionen/[slug]` and aggregate only approved public organization projections/renditions from centrally governed content families. Authenticated scope switching is limited to authorized Bund/Land/Kreis/Orts/body scopes and must re-evaluate authorization and invalidate incompatible stale context. Regional binding votes use the same isolated WS-03 Voting Client with one-time purpose- and organization-scoped handoff. Regional administration remains scoped; no universal admin is introduced.

**FIR IDs refined:** `FIR-UX-004` and existing FRONT/organization-scope/voting-isolation obligations. **Status changes:** none. **New FIR IDs:** none.

**Frontend evidence/specification:** `docs/frontend/FRONT-02-REGIONAL-OPERATING-MODEL.md` and the Regionen section of `docs/frontend/FRONT-02-SPECIFICATION.md`.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`.

## 1.70 Documentation-only refinement — DE/EN frontend language model (2026-08-26)

**Round:** documentation/governance refinement only. No runtime, legal, publication, membership, voting or administrative capability is activated by this round.

**Governed decision:** EPD² frontend surfaces use a DE/EN localization model. German is the default interface language and authoritative reference for legally, procedurally and institutionally material German party content unless an exact later governed decision states otherwise. English is a governed translation rendition. German canonical route paths remain canonical; language selection changes rendition state and does not create a second English route authority.

Shared shells expose a canonical-style accessible `DE | EN` selector where both languages are offered. Language preference is minimal non-authoritative display state and must not encode or correlate identity, authorization, political interest, organization scope, case identity or voting eligibility. Material English content is version-linked to its German source, carries governed translation status/approval evidence, and fails explicitly to the current German authoritative rendition when missing, stale or unapproved.

**FIR IDs refined:** `FIR-FORM-004`, `FIR-UX-004`, `FIR-UX-007`, `FIR-UX-008`, `FIR-UX-011` and existing privacy/session/accessibility obligations. **Status changes:** none. **New FIR IDs:** none.

**Frontend evidence/specification:** `docs/frontend/FRONT-02-LANGUAGE-AND-LOCALIZATION-MODEL.md` and §5.3 of `docs/frontend/FRONT-02-SPECIFICATION.md`.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`.

## 1.71 Documentation-only update — Governed AI Correspondence Analysis & Reply Drafting (2026-08-27)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is started or closed by this update.

**Purpose:** record the approved EPD² requirement for governed AI-assisted analysis of incoming correspondence and preparation of reply drafts across authorized correspondence, casework, member-support and representative-desk workflows.

**New FIR ID created:**

- `FIR-AI-003 — Governed Correspondence Analysis & Reply Drafting` — status `approved`, priority `high`.

**FIR IDs implemented:** none. The existing `ai-processing-service` already provides reference-level use classes including summarization, classification, recommendation and drafting, together with provenance/redaction/human-review boundaries. This update does not claim an end-to-end correspondence copilot, a live AI provider, automatic sending, production readiness or legal activation.

**Human-authority boundary:** AI output remains advisory. The AI layer may analyze authorized correspondence and prepare drafts, but may not establish the organization's political/legal position, issue a consequential decision, finalize or close a governed case, or send an official consequential response without the owning workflow's required human authorization. Automated transmission is prohibited by default; any future narrowly defined non-substantive acknowledgement requires a separate governed decision.

**Execution state:** unchanged. `API-02 = NEXT` remains the primary implementation position. No current stage status is promoted or reopened.

## 1.72 Documentation-only refinement — FIR-AI-003 Implementation Placement Matrix (2026-08-27)

**Round:** documentation/governance refinement only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is started, accepted or closed by this update.

**Purpose:** remove implementation-placement ambiguity for `FIR-AI-003` by assigning mandatory responsibility across authoritative correspondence/casework ownership, `ai-processing-service`, document/evidence ownership, API, INFRA, OPS, CTRL, FRONT, FINAL INTEGRATION and SEC.

**FIR IDs refined:** `FIR-AI-003`. **Status changes:** none. **New FIR IDs:** none.

**Governed rule:** no single service, layer, generic chatbot, provider integration or frontend surface may claim `FIR-AI-003` complete in isolation. Each stage owns only its scoped obligations; whole-FIR completion requires the governed end-to-end path and acceptance evidence.

**Execution state:** unchanged. `API-02 = NEXT` remains the primary implementation position. Exact allocation among API-02…API-06 remains governed by their stage contracts; this refinement does not pre-assign or pre-accept a specific API stage.

## 1.73 Documentation-only update — Regional Authority Suspension & Intervention Control (2026-08-27)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is accepted or closed by this update, and no regional intervention capability is activated merely by recording it.

**Purpose:** establish the mandatory technical control model for containing misuse of regional administrative authority without disabling the regional organization, ordinary member participation or the voting trust boundary.

**New FIR ID created:** `FIR-GOV-004 — Regional Authority Suspension & Intervention Control` — status `approved`, priority `critical`.

**Governed rule:** intervention acts on exact privileged sessions, exact `OrganizationalAuthority` assignments, exact administrative `action_code` classes and, where necessary, narrow time-bounded `temporary_supervision_by` authority. There is no unrestricted `region_disabled` switch, no implicit Bund takeover and no universal regional super-administrator.

**Legal/governance boundary:** this round fixes the technical mechanism and safety invariants. The exact statutory/legal body competent to initiate, approve, review or overturn each intervention remains subject to later legal/Satzung refinement and must be supplied through governed authority/rule configuration; technical hierarchy position alone never supplies that competence.

**FIR IDs implemented:** none. Existing ADR-034/ADR-036 regional-scope and authority foundations, PACK-12 privileged-access controls and audit/evidence mechanisms are dependencies, not evidence that the end-to-end intervention workflow already exists.

**Execution state:** the FIR addition itself changes no implementation-stage acceptance state. API-02 execution-state reconciliation is recorded separately in Program Control; no API-02 PASS/ACCEPTED claim follows from this round.

## 1.74 Documentation-only update — Governed Access, Credential & Key Authority Lifecycle Control (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is accepted or closed by this update, and no credential/key-management capability is activated merely by recording it.

**Purpose:** establish the mandatory end-to-end authority model for blocking access, recovering or replacing human credentials, issuing service credentials, generating/activating/rotating/revoking cryptographic keys, emergency compromise handling and independent evidence/review.

**New FIR ID created:** `FIR-SEC-004 — Governed Access, Credential & Key Authority Lifecycle Control` — status `approved`, priority `critical`.

**Governed rule:** authentication credential, session, organizational authority, privileged grant, service credential and cryptographic key are different control objects. The rights to request, approve, execute/generate, see secret material, activate, revoke, restore, rotate, destroy and audit are separate authorities and must not collapse into a universal administrator.

**Dependencies preserved:** PACK-14 authentication/recovery controls, PACK-12 JIT/break-glass separation, FIR-GOV-004 regional authority intervention controls, voting trust-domain isolation and audit/evidence rules remain controlling boundaries. This round does not reopen any closed architecture PACK.

**FIR IDs implemented:** none. Exact allocation among API-02…API-06 and later INFRA/OPS/CTRL/FRONT/SEC stages remains governed by their stage contracts and acceptance gates.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. No API-02 PASS/ACCEPTED/CLOSED claim follows from this round.

## 1.75 Round record — INFRA-01 CI Acceptance Harness & Release-Integrity Foundation (2026-08-31)

**Round:** infrastructure implementation, developed in parallel as `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED` under Entering Baseline Identity v1.1 (`nepogoda1970-epd2/epd2-civic-os` commit `8ff32c3e9ed654768ae86ac569a9c498f78c5aa2`, tree `13e1c439f8f5b0bd37cb6519f109d9f4c02f1ef9`). No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT stage is accepted or closed by this round; INFRA closure remains blocked on the governed predecessor sequence. Repository version unchanged at `0.16.0`; Canon unchanged at `0.8.0`.

**Purpose:** turn repository verification from individual scripts/workflows into one deterministic, fail-closed, evidence-producing canonical acceptance system: `uv run python -m scripts.acceptance run` (`make acceptance`), with a machine-readable governed check registry (`scripts/acceptance/check_registry.json`), exact candidate identity binding, tested-bytes==packaged-bytes freeze/package proof, frozen-artifact integrity at five lifecycle boundaries, a secret-leakage hard gate with a line-pinned governed allowlist, archive hygiene under one canonical packaging allowlist, an adversarially tested evidence validator (16 mutation classes, 16 distinct detectors), a sealed canonical execution manifest, an evidence bundle sufficient for independent review, and a GitHub Actions workflow (`.github/workflows/infra01-acceptance.yml`) that invokes the same harness rather than reimplementing acceptance.

**Foundations established (machine-readable):** deployment-manifest schema/validator enforcing `running combination == one approved deployment manifest` with mixed versions only via a declared compatibility matrix (`FIR-REL-001` foundation); runtime readiness contract with fail-closed `process alive != safe for consequential traffic` semantics (`FIR-READY-001` foundation); mandatory sovereignty-profile fields with no provider selected and `provider != trust assumption` (`FIR-INFRA-SOV-001` foundation); structural gateway/infrastructure non-ownership checks (`FIR-EDGE-001`/`FIR-API-001` preserved).

**Corrections carried on this source lineage:** PACK-25C6-equivalent test-output isolation for the two frozen PACK-16D target-profile artifacts (tests write only to isolated temporary locations; accepted digests pinned in `scripts/acceptance/frozen_artifacts.json` and verified at five boundaries); pre-existing red `ruff check .` (2 errors) and `make typecheck` (10 errors) fixed forward in verification-infrastructure files with no behavioural change; `test_property_limitation_is_recorded` rewritten to pass in both the blocked and the resolved hypothesis-availability state. No existing check was weakened.

**FIR IDs implemented:** none.

**FIR IDs deferred:** none newly deferred.

**FIR IDs intentionally left unchanged:** all requirements outside INFRA-01 scope, including every voting, identity, UX, AI, OPS, CTRL, SEC, legal-activation and BSI-readiness FIR; `FIR-BASE-001` continues to identify the latest accepted cumulative baseline because this candidate is not accepted.

**New FIR IDs created:** none.

**FIRs materially advanced (status unchanged, evidence in `docs/infra/INFRA-01/INFRA-01-FIR-COVERAGE-MATRIX.md`):** `FIR-REL-001`, `FIR-READY-001`, `FIR-EDGE-001`, `FIR-SEC-SECRET-001`, `FIR-INFRA-SOV-001`, `FIR-TEST-001`, `FIR-TEST-002`, `FIR-API-001`.

**Execution state:** governed by the Program Control Register. `INFRA-01 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; the delivered candidate carries `LOCAL CANONICAL HARNESS: PASS / EXTERNAL GOVERNED ACCEPTANCE: NOT YET PERFORMED / NOT PRODUCTION READY / NOT LEGALLY ACTIVATED`.

## FIR-BASE-001 — Current repository baseline

**Status:** implemented  
**Last updated:** PACK-31 constitutional and ethics oversight (2026-08-11)

### Baseline pointer and candidate pointer are two different things

The distinction below is the one the PACK-25 register addendum requires, and
the freshness checker (`scripts/check_register_freshness.py`) reads both halves
of it:

```text
latest accepted cumulative baseline = PACK-26C1, repository 0.28.0, accepted
current implementation candidate    = PACK-33, repository 0.35.0, NOT a PASS
```

**Current authoritative cumulative baseline (accepted cumulative baseline,
PASS):**

```text
EPD2_PACK-25C6_VERIFICATION-HARNESS-CORRECTION_CANDIDATE_0.27.0.zip
```

Accepted immutable SHA-256:

```text
900f955762fbad14d82d24da315a28b5f268318d3bb278223f8d05eaf4037d2f
```

Repository version `0.27.0`; Canon version `0.8.0`.

Acceptance status:

```text
EPD² PACK-25C6 FINAL PASS
VERIFICATION-HARNESS CORRECTION ACCEPTED
AVH 0.1.3 INTEGRATION ACCEPTED
```

PACK-25C6 is the sole authoritative entering baseline for PACK-26. The earlier
accepted PACK-25 archive remains historical evidence of the business-domain
increment, but must not be used as the working source for PACK-26 and must not
be merged with PACK-25C6.

The accepted PACK-25 business baseline immediately beneath the correction is:

```text
EPD2_PACK-25_CANDIDATE_0.27.0.zip
SHA-256 962aa8b554995664f7fedb091b6955139edf41f757da3a56834a865e728f49ca
```

The PACK-25C6 correction changed verification-harness behaviour and its
regression evidence, not PACK-25 business scope. It removed writable frozen
PACK-16D target-conformance outputs from the test path, retained exact
pre/post immutable SHA checks and packaging fail-closed checks, and was
accepted only after authoritative Windows CI returned `RESULT: PASSED` and an
independent AVH 0.1.3 run returned the expected `CONDITIONAL (AVH-L1)` with
zero findings.

The accepted PACK-26C1 candidate entered PACK-27 as the sole authoritative
code baseline:

```text
EPD2_PACK-26C1_CANDIDATE_0.28.0.zip
SHA-256 760b1c9afa456547202eca2332445164914ba489631ad3134d67ca3641d9aa28
```

It carried an authoritative Windows local CI PASS, the expected AVH 0.1.3
`CONDITIONAL (AVH-L1)` with zero findings, no new ordering violations, and the
accepted frozen PACK-16D artefacts unchanged. PACK-27 merged no code from
PACK-25, from the initial PACK-26 candidate, or from any other repository
archive.

**Current implementation candidate (NOT accepted, NOT a PASS):**

```text
EPD2_SYSTEM-WIDE_CORRECTIVE_CLOSURE_CANDIDATE_0.39.0.zip
```

Repository version `0.38.0` -> `0.39.0`; Canon version unchanged at `0.8.0`;
compatibility ceiling `<0.39.0` -> `<0.40.0`. It entered from
`EPD2_CTRL-01_CANDIDATE_0.38.0.zip`
(`f39fd60faf79892edf9617d391557ce29ddcfd73fc5d23f7447e380f9eb6e434`) as the
sole authoritative code baseline, and closes the reproducible architecture
defects the system-wide challenge
(`4377b0ccbe2a41273e6dde709111409cb76879441c95519d7b48a43bcc7f4d7c`)
demonstrated: the three checker inputs that shipped as literal `[]`, the
free-text break-glass matcher, the unevaluated `CONDITIONAL` separation
verdict, the console cross product that gave one role both halves of a
maker/checker rule, role-assignment expiry that no computation consulted,
and eleven checker rules that recognised a spelling rather than verifying a
property. It adds no bounded context, no frontend surface and no authority,
activates no governance decision, and redesigns no business domain. It is
not accepted, and it is **partial** by its own report: the caller-asserted
authorization dialect, the cross-context accumulation blind spot and the
harvest-partition gaps are carried forward with explicit dispositions rather
than closed. Section 1.65 carries the round record.

The superseded CTRL-01 candidate record follows.

```text
EPD2_CTRL-01_CANDIDATE_0.38.0.zip
```

Repository version `0.37.0` -> `0.38.0`; Canon version unchanged at `0.8.0`;
compatibility ceiling `<0.38.0` -> `<0.39.0`. It entered from
`EPD2_PACK-35_CANDIDATE_0.37.0.zip` as the sole authoritative code baseline,
and adds one leaf control-plane context —
`services/control-plane-service` — consolidating the administration,
authority, workspace, console, separation-of-duty, assurance,
sensitive-data, audit and break-glass architecture into one machine-readable
model (section 1.64). It creates no authority, activates nothing, adds no
frontend surface and redesigns no business domain. It is not accepted, and
it is **partial** by its own report: no authority is activated, no assurance
profile binds anybody, and no role-assignment or break-glass approval body
is named.

The superseded PACK-35 candidate record follows.

```text
EPD2_PACK-35_CANDIDATE_0.37.0.zip
```

Repository version `0.36.0` -> `0.37.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.37.0` -> `<0.38.0`. It entered from
`EPD2_PACK-34_CANDIDATE_0.36.0.zip` as the sole authoritative code baseline,
and adds one recording context — `services/lobbying-disclosure-service` —
for lobbying disclosure and external influence transparency (section 1.63,
ADR-133, ADR-134, ADR-135). It selects no production voting cryptographic
primitive and leaves the VCRYPTO-01 entry gate and all twelve of its
subsections unchanged. It is not accepted, and it is **partial** by its own
report: no materiality rule is activated, no governed threshold profile
exists, nothing is publishable, and which roles carry a disclosure
obligation at all is undecided.

The superseded PACK-34 candidate record follows.

```text
EPD2_PACK-34_CANDIDATE_0.36.0.zip
```

Repository version `0.35.0` -> `0.36.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.36.0` -> `<0.37.0`. It entered from
`EPD2_PACK-33_CANDIDATE_0.35.0.zip` as the sole authoritative code baseline,
and adds one analytical context — `services/delegation-reputation-service` —
for delegation reputation and anti-gaming (section 1.62, ADR-130, ADR-131,
ADR-132). It selects no production voting cryptographic primitive and leaves
the VCRYPTO-01 entry gate and all twelve of its subsections unchanged. It is
not accepted, and it is **partial** by its own report: no anti-gaming rule is
activated, no governed threshold exists and no disclosure floor has been
agreed.

The superseded PACK-33 candidate record follows.

```text
EPD2_PACK-33_CANDIDATE_0.35.0.zip
```

Repository version `0.34.0` -> `0.35.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.35.0` -> `<0.36.0`. It entered from
`EPD2_PACK-32_CANDIDATE_0.34.0.zip`, SHA-256
`5458d45ef02577d9eefa5a78fad7c8420857db26f4c486f5b6c6c334246ba828`, as the
sole authoritative code baseline, and adds one leaf bounded context —
`services/citizen-office-routing-service` — for citizen office routing and
no-wrong-door caseflow (section 1.61, ADR-127, ADR-128, ADR-129). It selects
no production voting cryptographic primitive and leaves the VCRYPTO-01 entry
gate and all twelve of its subsections unchanged. (The subsection numbers are
written out here rather than backticked: the freshness gate reads every
backticked three-part number in this section as a repository version, and a
section number is not one.) It is not accepted.

The superseded PACK-32 candidate record follows.

```text
EPD2_PACK-32_CANDIDATE_0.34.0.zip
```

Repository version `0.33.0` -> `0.34.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.34.0` -> `<0.35.0`. It entered from
`EPD2_PACK-31_CANDIDATE_0.33.0.zip`, SHA-256
`efe5fc4a3b31e09caff88b820b78d02968df0af8c04416bc444724830b595763`, as the
sole authoritative code baseline, and adds one leaf bounded context —
`services/program-service` — for programme formation and deliberation
intelligence (section 1.60, ADR-124, ADR-125, ADR-126). It also carries
the accepted Master Register **V14** content forward, preserving every
pre-existing FIR identifier, §1.59 and all twelve subsections
§1.59.1 — §1.59.12, and `FIR-VOTE-CRYPTO-001`'s normative linkage to the
VCRYPTO-01 Entry Gate. `FIR-VOTE-CRYPTO-001` remains OPEN and no
production voting cryptographic primitive is selected. It is not
accepted.

The superseded PACK-31 candidate record follows.

```text
EPD2_PACK-31_CANDIDATE_0.33.0.zip
```

Repository version `0.32.0` -> `0.33.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.33.0` -> `<0.34.0`. It entered from
`EPD2_PACK-30_CANDIDATE_0.32.0.zip`, SHA-256
`6c09508b1cb4573e8a002a6160d369d9cc1f9c1cd4fa5ca494eef7dc1bac88a2`, as the
sole authoritative code baseline, and adds one leaf bounded context —
`services/oversight-service` — for constitutional and ethics oversight
(section 1.58, ADR-121, ADR-122, ADR-123). It is not accepted.

The superseded PACK-30 candidate record follows.

```text
EPD2_PACK-30_CANDIDATE_0.32.0.zip
```

Repository version `0.31.0` -> `0.32.0`; Canon version unchanged at
`0.8.0`; compatibility ceiling `<0.32.0` -> `<0.33.0`. It entered from
`EPD2_PACK-29C1_CANDIDATE_0.31.0.zip`, SHA-256
`4371ffe99f3e0894266b3d62ff07225b39b15e9919901f2ad60d476a6aee7bdd`, as the
sole authoritative code baseline, and adds one leaf bounded context —
`services/emergency-governance-service` — implementing canon section 19.1's
`EmergencyAction` (section 1.57, ADR-118, ADR-119, ADR-120). It is not
accepted.

The superseded PACK-29C1 candidate record follows.

```text
EPD2_PACK-29C1_CANDIDATE_0.31.0.zip
```

Repository version unchanged at `0.31.0`; Canon version unchanged at
`0.8.0`. It entered from `EPD2_PACK-29_CANDIDATE_0.31.0.zip`, SHA-256
`99193be36cd180fb2af455ccd302ceff871b30335bb124a10e5f45aaa08dc6c5`, which
independent inspection returned for a publication-consumption boundary
correction: `PUBLIC_CANDIDATE` fed a public projection built from
representative-desk internal stores, `PublishedProjectionRef` was declared
and never consumed, and the five public frontend routes named
`representative-desk-service` as their backend (section 1.56, ADR-117).
Neither candidate is accepted.

The superseded PACK-29 candidate record follows.

```text
EPD2_PACK-29_CANDIDATE_0.31.0.zip
```

Repository version `0.31.0`; Canon version unchanged at `0.8.0`. It entered
from `EPD2_PACK-28C2_CANDIDATE_0.30.0.zip`, SHA-256
`c8b6b26c2fc9a261a4403875fce02ccd8217bb60f00769d653ae0b03ea035386`, which is
the sole authoritative code baseline for the PACK-29 round and which is itself
**not accepted**. PACK-29 merged no code from the PACK-28 or PACK-28C1
candidates, from PACK-27, or from any other repository archive. It adds one
new bounded context, `services/representative-desk-service`, a leaf declaring
exactly `epd2-core` and `epd2-audit-core` (section 1.55).

The superseded PACK-28C2 candidate record follows.

```text
EPD2_PACK-28C2_CANDIDATE_0.30.0.zip
```

Repository version `0.30.0`; Canon version unchanged at `0.8.0`. It entered
from `EPD2_PACK-28C1_CANDIDATE_0.30.0.zip`, SHA-256
`f5f570322868f500d6aa674c60456d9b44643f2eb47887caa446a7c5a5d34dc9`, which
authoritative Windows CI returned for one real inherited dependency defect:
the independent verifier's `cryptography` runtime dependency was owned by
`voting-service` rather than by the verifier, so verifier-runtime preflight
failed with `VERIFIER_RUNTIME_UNAVAILABLE` and 29 ordinary tests plus two
PACK-17C suites failed behind it (section 1.54, ADR-114). No candidate
in this chain is accepted.

The superseded PACK-28C1 candidate record follows.

```text
EPD2_PACK-28C1_CANDIDATE_0.30.0.zip
```

Repository version `0.30.0`; Canon version unchanged at `0.8.0`. It
superseded `EPD2_PACK-28_CANDIDATE_0.30.0.zip` (SHA-256
`4862c78a2b8d98dd6f8fd3ae6802bf22484d40e33d9d2f22621783e2266b387d`), which
independent inspection returned for a dependency-boundary and report
correction (section 1.53). Its own dependency-boundary correction — ADR-113,
`transparency-service` reduced to `epd2-core` and `epd2-audit-core` — is
carried forward unchanged by PACK-28C2 and is **not** reverted by it.

The superseded PACK-28 candidate record follows.

```text
EPD2_PACK-28_CANDIDATE_0.30.0.zip
```

Repository version `0.30.0`; Canon version unchanged at `0.8.0`. It entered
from `EPD2_PACK-27C1_CANDIDATE_0.29.0.zip`, SHA-256
`38454b8b2a1c4c6a21c0478ec5ae752cd674c24d49161ddd34822e98ca764c1d`, which
was the sole authoritative code baseline for the PACK-28 round and which is
itself **not accepted**: it carried an authoritative Windows local CI
`RESULT: PASSED`, 9920 pytest passed, 32/32 mypy groups, the expected AVH
0.1.3 `CONDITIONAL (AVH-L1)` with zero findings, and no independent
acceptance round.

The immediately preceding candidate record follows.

```text
EPD2_PACK-27C1_CANDIDATE_0.29.0.zip
```

Repository version `0.29.0`; Canon version unchanged at `0.8.0`. This
supersedes `EPD2_PACK-27_CANDIDATE_0.29.0.zip` (SHA-256
`1970169629770c921ff0ec385351d3d4aca70ede1029f664bc1878b47346d256`), which
independent inspection returned for a governance and enforcement
correction. Neither is accepted.

PACK-27C1 (conflicts, declarations and recusal, plus the governance and
enforcement correction at section 1.51) is an **implementation candidate**. It has not been independently accepted, it has not been run
against authoritative Windows CI or AVH by an independent party, and nothing in
this register promotes it. Only a later independent acceptance round may make
PACK-27 the authoritative baseline; until it does, the accepted cumulative
baseline above remains PACK-26C1 and the PACK-25/PACK-25C6/PACK-26C1 acceptance
history is untouched.

PACK-27 did not modify the PACK-26C1 archive, did not recompute its hash and
did not reopen its acceptance.

Current cumulative architecture includes PACK-01 through PACK-26C1 as accepted,
plus the accepted PACK-25C6 verification-harness correction, plus the PACK-26
candidate increment (volunteer, staff and contractor administration) which is
**not** accepted, plus the accepted FRONT foundation already carried by the
repository. This remains **NOT PRODUCTION READY** and **NOT LEGALLY
ACTIVATED**.

The canonical register path remains:

```text
docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md
```

Starting with PACK-25, repository governance rejects a cumulative candidate
when this baseline pointer or the represented PACK history is stale. That
requirement is not prose only: it is `scripts/check_register_freshness.py`,
wired into `make check-repository` and into the local-CI driver's
repository-scripts stage, with mutation tests in
`tests/repository/test_pack25_register_freshness.py` that prove the checker
fails on deliberately stale temporary fixtures rather than merely passing on
the real one. A later PACK must update this pointer only after its own
independent acceptance round.

**Immediately previous accepted baselines with independently recorded hashes:**

- PACK-23 — repository `0.25.0`, SHA-256
  `14c0f04a979239faf69e5a653d6d3e72ee0e9fb4066c8d8ce517d4bf1c9b6810`;
- PACK-22 — repository `0.24.0`, SHA-256
  `ffdd763b3f496ba58632e03cdeae34e7a7ee21cb0f69afb5aa8f90720fb67caa`;
- PACK-21 — repository `0.23.0`, SHA-256
  `4d517d7ba420382a7be83ca66f06e71e87914d19ff11e03623e3815fb303afd4`.

The older detailed baseline history below is preserved as historical
evidence. Where it calls PACK-14 or PACK-15 “current”, that wording is a
historical snapshot from the round in which it was written and is
superseded by the current pointer above.

**Previous authoritative cumulative baseline (PASS):**

```text
EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip
```

Repository version `0.14.0`; canon version `0.8.0` (unchanged — this round
amends no canon). Verified by an external GitHub Actions run that passed
every stage — see `docs/handover/PACK-14-FINAL-PASS-REPORT.md`,
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION-RESULT.md` and
`docs/handover/PACK-14-EXTERNAL-CI-VERIFICATION.log`.
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

The verified candidate was
`EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_CANDIDATE_CORRECTED_PRETTIER.zip`.
This FINAL PASS archive is that externally verified tree plus the status,
register and handover documents that close the round; no service module,
test, migration artefact, reason code, ADR, contract, frontend file, route,
visual snapshot or CI definition changed, and neither version moved.

Confirmed at this baseline:

- Repository version: `0.14.0`
- Canon version: `0.8.0`
- PACK-01 through PACK-14: PASS
- FRONT-00 Foundation: PASS
- FRONT-01 Public Website: PASS
- `services/identity-service`: 40 source modules (34 new), 12 test modules
- Identity implementation status: `reference_implementation`
- `contracts/reason-codes/pack-14.yml` (213 entries: 131 additive, 22
  redeclared from earlier packs, 60 `*_RECORDED` audit classifications)
- ADR-079 through ADR-088. **These ten records carry `proposed` status**,
  which `docs/handover/PACK-14-SPEC-ADR-REPORT.md` §2 already stated and
  which the FINAL PASS round did not change: a green pipeline verifies an
  implementation, not the governance status of a decision record — the
  same treatment ADR-061—ADR-068 received. An earlier draft of this bullet
  said "accepted"; that was wrong and is corrected here.
- A **reference persistence path**: ten SQL migration artefacts applied in
  order in a transaction with a recorded checksum, producing 29 tables and
  35 indexes; eleven durable adapters; a transaction boundary and an
  optimistic-concurrency guard. It runs on SQLite through the standard
  library. **No production database is deployed and no production
  durability is claimed.** The in-memory adapters are retained as test
  adapters and are not the default runtime binding.
- A **runnable reference service boundary** routing 12 of the 42
  catalogued operations, transport-agnostic, with reason-coded responses
  and no secret or raw identifier in any response body
- All four security ports **refuse** when unbound; in particular no
  password may be enrolled or replaced without a bound breached-password
  checker
- still no production IAM, no eID scheme, no email or SMS provider, no
  HSM or KMS, no Voting Client, no HTTP surface or production gateway,
  and no frontend

The last line is why `FIR-ROADMAP-004` is `implemented in reference form`
rather than `implemented`. A green pipeline verifies the tree; it binds no
provider and deploys nothing.

**Lineage of this baseline.** The round shipped a first candidate,
`EPD2_PACK-14_..._0.14.0_CANDIDATE.zip`; a correction round before
external CI returned and fixed three findings — persistence that was
metadata rather than persistence, a permissive breached-password default,
and an API module that was a catalogue rather than a boundary — producing
`..._CANDIDATE_CORRECTED.zip`; the first external run then failed on one
Prettier-unformatted file, and the whitespace-only fix produced
`..._CANDIDATE_CORRECTED_PRETTIER.zip`, which is the archive the passing
run verified. No functional scope was expanded, no frontend was built, no
dependency was added and no CI gate was weakened at any step.

**Previous PASS baseline, superseded by the line above:**

```text
EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip
```

Repository version `0.13.0`; canon version `0.8.0`. Verified by an
external GitHub Actions run that passed every stage — see
`docs/handover/PACK-13-FINAL-PASS-REPORT.md`,
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` and
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`.
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

Confirmed at that baseline:

- Repository version: `0.13.0`
- Canon version: `0.8.0`
- PACK-01 through PACK-13: PASS
- `services/data-plane-service`: 22 source modules, 20 test modules
- Data-plane implementation status: `reference_implementation`
- `contracts/reason-codes/pack-13.yml` (125 entries: 88 from the PACK-13
  reason-code catalog, 37 `*_RECORDED` audit classifications)
- ADR-069 through ADR-078, accepted
- still no production database, no production event bus, no external
  schema-registry product, no production search engine, no production
  IAM, no backup or restore capability, no multi-region topology

The last line is why `FIR-ROADMAP-003` is `implemented in reference form`
rather than `implemented`. A green pipeline verifies the tree; it deploys
nothing.

**Earlier PASS baseline:**

```text
EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip
```

Repository version `0.12.0`; canon version `0.8.0`. Verified by an
external GitHub Actions run — see
`docs/handover/PACK-12-FINAL-PASS-REPORT.md` and
`docs/handover/PACK-12-EXTERNAL-CI-VERIFICATION-RESULT.md`.
**Not production ready. Not legally activated.**

**Earlier PASS baselines, in order:**

```text
EPD2_PACK-11_GOVERNED_DOCUMENTS_EVIDENCE_0.11.0_FINAL_PASS.zip
EPD2_PACK-10_PARTY_FINANCE_0.10.0_FINAL_PASS.zip
```

Confirmed at the `0.10.0` PASS baseline:

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

Added by PACK-11 and confirmed at the `0.11.0` PASS baseline by an
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

PROD-01 raises the accepted cumulative baseline to `0.40.0`. That
implementation candidate adds a production runtime spine and binds one
non-voting bounded context to it; it reopens no architecture and
activates no governance.

PROD-02 raises the accepted cumulative baseline to `0.41.0`. That
implementation candidate scales the PROD-01 runtime pattern across the
selected PILOT-MUST contexts; it reopens no architecture and activates
no governance.

SEC-01 raises the accepted cumulative baseline to `0.42.0`. That
implementation candidate hardens the reachable non-voting runtime
surface — password verification, abuse control, session and transport
security, and a security scanning pipeline. It reopens no architecture,
activates no governance, grants no new authority, and is neither a
penetration test nor a security certification.

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

**Status:** implemented in reference form  
**Target version:** `0.13.0` — delivered by PACK-13, FINAL PASS  
**Implementing round:** PACK-13 implementation round (2026-07-30),
candidate → documentation correction → external CI PASS → FINAL PASS

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

**PACK-13 implementation round: EXTERNAL CI PASS, FINAL PASS archive
prepared.** `services/data-plane-service` implements the specification
in **reference form**: the transactional persistence contracts, the
canonical schema registry, the deterministic compatibility checker, the
API and event contract-evolution model, the migration framework and its
five automated gates, the backfill runner, the transactional outbox, the
at-least-once delivery semantics with effectively-once consumer effect,
projection governance, the search and export persistence contracts, the
retention and legal-hold bindings, the PACK-12 privileged gates and the
structural boundary guards — twenty-two source modules and twenty test
modules, with `contracts/reason-codes/pack-13.yml` carrying 125 entries.

**External GitHub Actions passed every stage:** 800/800 repository paths,
no forbidden paths, version consistency, Ruff format over 520 files,
Prettier, Ruff lint, ESLint, mypy across all 23 groups, both TypeScript
typechecks, 4625 Python tests passed with 4 skipped, 34 Node tests, 16
frontend unit and render tests, a successful Next.js production build, and
108 browser, accessibility and visual tests.

**Why the status is `implemented in reference form` and not `implemented`
outright:**

1. every storage adapter is **in memory**. No production PostgreSQL,
   cloud database, real broker, external schema-registry product,
   production search engine or production IAM is deployed. The
   requirements a production data plane must satisfy are implemented as
   contracts and refusals, which is a different and lesser claim than
   satisfying them in production;
2. the criteria whose evidence is a database grant inventory, a live
   catalog snapshot, a role inventory or an egress-control review are
   recorded as `deferred to production infrastructure` in the acceptance
   matrix's implementation-status appendix, not as met;
3. the external pipeline verifies the repository. It builds, type-checks,
   lints, formats and tests the tree — and it deploys no database, starts
   no broker and grants no role, so it cannot close a criterion whose
   evidence lives in an environment that does not exist yet.

**Not production ready. Not legally activated.**

**Evidence:**

- `services/data-plane-service/` (source and tests);
- `contracts/reason-codes/pack-13.yml`;
- `docs/adr/ADR-069-*` through `docs/adr/ADR-078-*` (accepted);
- `docs/packs/PACK-13/` (specification and matrices, including the
  acceptance matrix's implementation-status appendix);
- `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`;
- `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`;
- `docs/handover/PACK-13-SPEC-ADR-REPORT.md` (the specification round's
  own report, retained unchanged);
- `docs/handover/PACK-13-FINAL-PASS-REPORT.md`,
  `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` and
  `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`.

**Remaining work before this entry could ever be marked `implemented`
outright:**

1. ~~an external GitHub Actions PASS over this candidate~~ — **done**
   (2026-07-30), and it is what moved this entry to `implemented in
reference form`. Retained rather than deleted, because the register
   preserves history;
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

**Status:** implemented in reference form  
**Target version:** `0.14.0`

Moved from `approved` to `candidate` by the PACK-14 implementation
candidate round (§1.15), and from `candidate` to `implemented in reference
form` by the PACK-14 FINAL PASS round (§1.16), on the evidence of an
external GitHub Actions run that passed every stage.

Deliberately **not** `implemented` outright. Reference form means the
aggregates, the governed workflows, the refusals, the reference
persistence path and the runnable service boundary are real and tested.
It does not mean any of the following, none of which exists:

- a bound WebAuthn verifier, password hasher, breached-password checker or
  assertion-signature verifier — all four ports **refuse** by default, and
  no password can be enrolled or replaced without the third;
- a production database. The persistence path runs on SQLite through the
  standard library; no replication, backup, failover or restore exists;
- an HTTP surface, TLS termination or production gateway. **The
  gateway-hardening half of the scope below is untouched.**
- a selected identity provider, eID scheme or KYC integration. **The
  external-trust-provider half of the scope below is untouched** — this
  round defines a provider _adapter boundary_ and selects no provider.

Scope:

- identity and authentication;
- external trust providers;
- gateway hardening;
- scoped sessions;
- no global user ID;
- external identity minimization;
- eID/KYC integration boundary.

## FIR-ROADMAP-005 — PACK-15 Voting Trust Boundary & Unlinkability Threat Model

**Status:** implemented in reference form  
**Target version:** `0.15.0`

Moved from `approved` to `candidate` by the PACK-15 implementation
candidate round, and from `candidate` to `implemented in reference form`
by the PACK-15 FINAL PASS round (2026-07-31), on the strength of an
external GitHub Actions run that passed every stage against the cleaned
tree. It does **not** move to `implemented`: no provider is bound and
nothing is deployed. Key custody refuses every call, there is no
transport layer, and SQLite remains the reference persistence.

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

**Sequencing note added by PACK-16A (2026-08-01).** PACK-16 is delivered in
four stages, and this entry is satisfied by none of them until the last:

```text
PACK-16A  protocol and ballot model selection      — specification + ADR
PACK-16B  cryptographic parameters, key ceremony, trustee architecture
PACK-16C  casting, verification, receipt, bulletin-board specification
PACK-16D  implementation candidate
```

PACK-16A is complete as a **specification and ADR round only** and is
recorded in section 1.20. It selects a protocol family and a bounded EPD²
profile (`ADR-099`, status `proposed`; documents under
`docs/packs/PACK-16/`) and **implements nothing in this entry's scope**.
**Status stays `approved` and the target version stays `0.16.0`;** the
version bump belongs to PACK-16D. PACK-16B must not start before
architectural acceptance of PACK-16A.

PACK-16B is complete as a **specification and ADR round only** and is
recorded in section 1.21. It fixes the cryptographic parameter profile, the
guardian count and quorum, the key ceremony, the trustee architecture and
the recovery limits (`ADR-100`, status `proposed`; documents under
`docs/packs/PACK-16/`) and **implements nothing in this entry's scope**.
**Status stays `approved` and the target version stays `0.16.0`.** PACK-16C
must not start before architectural acceptance of PACK-16B.

PACK-16C is complete as a **specification and ADR round only** and is
recorded in section 1.22. It fixes the casting flow, the continuation
consumption boundary, the ballot envelope, the cast-or-challenge policy, the
validation pipeline, the ballot lifecycle, the receipt, the Verification
Client, the independent-verifier requirements, the bulletin board, the
publication model and the election record (`ADR-101`, status `proposed`;
documents under `docs/packs/PACK-16/`) and **implements nothing in this
entry's scope**. **Status stays `approved` and the target version stays
`0.16.0`.** PACK-16D must not start before architectural acceptance of
PACK-16C.

PACK-16D is complete as a **reference implementation candidate** and is
recorded in section 1.23. It is the first stage that ships code, and it
delivers the casting, publication, election-record and verification path in
reference form (`ADR-102`, status `proposed`; documents under
`docs/packs/PACK-16/`; source under
`services/voting-service/src/epd2_voting_service/reference/`).

**Outcome for this entry: `implemented in reference form`, partially.**
The status stays **`approved`** and is NOT moved to `implemented`, because
four items in this entry's scope are not delivered by a reference
implementation:

```text
audited cryptographic protocol integration  -> VO-08 OPEN; EPD2-CRYPTO-1
                                               constants absent
                                               (OD-P16D-01); no external
                                               conformance vectors
                                               (OD-P16D-02)
tally controls                              -> single guardian only;
                                               threshold DKG and the
                                               3-of-5 / 4-of-7 quorum NOT
                                               implemented (OD-P16D-07)
eligibility without identity-vote linkage   -> implemented against an
                                               in-memory reference store,
                                               not a production data plane;
                                               no production authentication
                                               (OD-P16D-08)
verifiable voting end to end                -> checkpoint signatures are
                                               never verified (OD-P16D-09);
                                               no constant-time guarantee
                                               (OD-P16D-05)
```

**The target version stays `0.16.0`, and `REPOSITORY_VERSION` reached
`0.16.0` in this round** — the version bump this entry anticipated has now
happened. Reaching the target version does not close the entry: production
acceptance requires the external cryptographic review, the independent
implementation and the PACK-17 verification that `FIR-ROADMAP-007` owns.

**Correction note added by the PACK-16D correction round (2026-08-02),
recorded in section 1.24.** The candidate above was audited and returned
**NOT ACCEPTED** on four findings. The correction implements all four, and
three of the four gaps named in the block above no longer hold:

```text
audited cryptographic protocol integration  -> EPD2-CRYPTO-1 is PRESENT
                                               and loadable, primary-
                                               sourced and arithmetically
                                               verified (OD-P16D-01
                                               CLOSED); conformance
                                               evidence now spans three
                                               named classes with two
                                               independent oracles. STILL
                                               NOT DELIVERED: VO-08 is
                                               OPEN, and no complete
                                               independent implementation
                                               has checked this one
                                               (OD-P16D-02)
tally controls                              -> Feldman VSS DKG, generic
                                               k-of-n, 3-of-5 default and
                                               4-of-7 high assurance, all
                                               running (OD-P16D-07
                                               CLOSED). STILL NOT
                                               DELIVERED: a key ceremony
                                               with custody, authenticated
                                               channels and an HSM
                                               (OD-P16D-11)
verifiable voting end to end                -> checkpoint signatures are
                                               generated AND verified
                                               against a declared signer
                                               registry (OD-P16D-09
                                               CLOSED). STILL NOT
                                               DELIVERED: no constant-time
                                               guarantee (OD-P16D-05,
                                               the remaining production
                                               blocker); the registry's
                                               own authorisation is
                                               outside the verifier's
                                               reach (OD-P16D-12)
eligibility without identity-vote linkage   -> UNCHANGED. Still an
                                               in-memory reference store,
                                               still no production
                                               authentication
                                               (OD-P16D-08)
```

**The status stays `approved` and the outcome stays `implemented in
reference form`, partially.** A materially stronger delivery is still a
reference delivery. `REPOSITORY_VERSION` stays `0.16.0`: a correction of a
candidate that was never accepted does not consume a new version.

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

## FIR-ROADMAP-010 — CTRL-01 Unified Control Plane & Administration Architecture

**Status:** approved  
**Priority:** critical  
**Target:** after PACK-35 and before system-wide architecture freeze  
**Dependencies:** PACK-12, PACK-18, PACK-19 through PACK-35

CTRL-01 is an architecture-closure workstream, not a new business domain.

It must consolidate all administrative, operational, oversight, security,
emergency and domain-specific work surfaces into one authoritative
Control Plane Registry before Architecture Baseline 1.0 / Freeze.

Required output:

```text
role
→ authority
→ organization scope
→ workspace
→ physical console
→ desk
→ route
→ backend service
→ action set
→ assurance requirement
→ maker/checker rule
→ incompatible roles
→ sensitive-data boundary
→ audit/evidence obligation
→ break-glass rule
```

The final physical-console count must be derived from the completed domain
architecture rather than fixed prematurely.

Required closure sequence:

```text
PACK-35
→ CTRL-01
→ system-wide AVH challenge
→ corrective closure
→ Architecture Baseline 1.0 / Freeze
```

CTRL-01 must not create a universal administrator or collapse independent
authorities merely because multiple desks share one frontend shell.

## FIR-ROADMAP-011 — FIR Ownership, Placement & Verification Map

**Status:** approved  
**Priority:** critical  
**Target:** establish no later than PACK-30; begin populating immediately  
**Dependencies:** canonical Master Future Implementation Register, repository governance, AVH

Every approved, deferred or partially founded FIR must resolve to an explicit
future implementation owner and verification path.

Required machine-readable mapping:

```text
FIR
→ owner workstream
→ target PACK / closure
→ dependencies
→ current status
→ implementation evidence
→ verification gate
→ blocker / limitation state
```

The architecture must detect **orphan requirements**: FIR entries that exist in
the canonical register but have no responsible future workstream or no planned
verification gate.

At minimum:

- every non-implemented FIR has an owner workstream;
- every FIR has a target PACK, architecture closure, legal-activation gate or
  explicit `UNSCHEDULED_BLOCKER` state;
- every implemented FIR points to evidence sufficient to support the status;
- every critical FIR has an explicit verification gate;
- placement changes are versioned and do not silently erase earlier ownership;
- no parallel roadmap may replace the canonical register.

Repository governance should be able to fail on orphan critical FIRs once the
placement map becomes normative.

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

## FIR-GOV-004 — Regional Authority Suspension & Intervention Control

**Status:** approved
**Priority:** critical
**Domain:** organization governance / regional authority / oversight / privileged security
**Target:** `organization-service` + governance/privileged-access integration + API + CTRL + FRONT + OPS + SEC

EPD² must provide a governed mechanism for containing misuse, compromise or operational failure of regional administrative authority without turning the upper organizational level into a permanent universal administrator.

Core rule:

```text
contain authority, not the region
```

A regional intervention must target the minimum necessary authority or action surface. The platform must not implement an unrestricted `region_disabled` switch, implicit Bund takeover, hierarchy-derived superuser or blanket cross-Land administration path.

### Intervention levels

The technical intervention model has four distinct levels. Permanent revocation is a possible final authority-lifecycle outcome after review, not a temporary intervention level.

1. **`SESSION_QUARANTINE` — immediate technical containment.** Security operations may terminate or quarantine the affected actor's privileged sessions and prevent new privileged sessions where the security policy authorizes it. This does not itself remove party membership, remove a person from office, decide a disciplinary matter or grant the security operator domain authority.
2. **`AUTHORITY_SUSPENSION` — temporary suspension of an exact `OrganizationalAuthority`.** The future authority lifecycle must support `ACTIVE -> SUSPENDED -> ACTIVE | REVOKED`, with normal expiry remaining possible. A suspended authority fails authorization at the moment of every affected act, including requests made from a browser page, token or session established before suspension.
3. **`REGIONAL_ACTION_RESTRICTION` — temporary freeze of exact administrative action classes in an exact organizational scope.** A governed `RegionalAdministrationRestriction` (or an explicitly equivalent later canonical contract) blocks only named state-changing `action_code` values for the target scope. It must not disable the regional organization as a whole.
4. **`TEMPORARY_SUPERVISION` — narrow external operational substitution when containment alone would leave the organization unable to function.** It reuses the governed `temporary_supervision_by` model and may grant only the specific functions required for restoration. Open-ended supervision remains forbidden; the existing 90-day default maximum and new-decision-on-extension rule remain binding unless a later governed legal rule narrows them.

A final `REVOKED` authority state uses the ordinary governed authority-revocation lifecycle and preserves the complete prior record.

### `RegionalAdministrationRestriction` minimum contract

The governed restriction record must preserve at least:

- stable restriction ID;
- exact `target_scope`;
- exact affected authority IDs where the restriction is authority-specific;
- closed/registered affected `action_code` set;
- intervention type;
- `valid_from`;
- mandatory `valid_until` for every temporary Level 2–4 intervention;
- reason code;
- evidence references;
- governing rule/policy version;
- initiating authority reference;
- approving authority reference where dual control applies;
- decision reference;
- notification evidence;
- review deadline;
- restoration, revocation or supersession reference;
- immutable audit/evidence references.

Free-text action classes, indefinite temporary restrictions and silent extension of an existing restriction are prohibited. Extension requires a new governed decision and new audit evidence.

### What may be restricted

Subject to the owning domain's own stricter rules, Level 3 may restrict exact regional administrative actions such as:

- assignment, activation, suspension or revocation of organizational authorities;
- membership-administration mutations;
- scoped finance-administration mutations;
- official correspondence/send actions;
- official document publication, supersession or revocation actions;
- governed data exports;
- organization configuration and relationship mutations;
- candidacy/election-administration actions only where the election domain separately permits that intervention.

A consuming domain may narrow or refuse an intervention capability. It may never broaden the regional intervention into data or actions that the actor could not otherwise govern.

### Regional continuity and ordinary member rights

An intervention against regional administration must not automatically suspend the regional body, its public presence or the ordinary rights of unaffected members.

Absent a separate, independently authorized domain/legal decision, the intervention must preserve:

- ordinary public read access to approved public material;
- ordinary member access within their existing lawful scope;
- discussion and initiative participation not implicated by the restriction;
- existing meetings, documents and decisions as historical records;
- audit and evidence visibility according to their existing access rules;
- case/correspondence history;
- the ability to restore lawful regional self-administration.

A broader restriction of member rights requires its own competent legal/procedural authority and is not granted by `FIR-GOV-004`.

### Voting and election trust-boundary carve-out

`FIR-GOV-004` must not become a generic path into WS-03 or the voting trust domain.

Regional intervention must not by itself:

- read ballot content;
- reveal identity-vote linkage;
- reveal or compute an intermediate tally;
- alter or delete accepted ballots;
- cancel or finalize a voting process;
- mass-revoke voting credentials;
- bypass election-specific governance, trustee, credential or challenge controls;
- transfer the ordinary member/admin session into the Voting Client.

Any intervention affecting a voting/election process must be separately authorized by that domain's own governed rules and trust boundaries. A generic regional action restriction is insufficient.

### Authorization and upper-level intervention

Upper organizational levels may intervene only through explicit governed authority. Being Bund-level, being an ancestor in the organization graph, holding a familiar title or operating the platform is never sufficient.

Mandatory rules:

- exact actor, purpose, target scope and action are evaluated at execution time;
- Levels 2–4 require two distinct authorized human actors unless a later stricter domain rule requires more;
- proposer and approver must differ;
- the affected actor cannot approve their own suspension, restoration or revocation;
- hierarchy-derived implicit intervention authority is prohibited;
- data access is never implied by procedural oversight or supervision title;
- temporary intervention has a hard expiry and review deadline;
- unknown, unavailable, expired or unverifiable intervention/authority state fails closed for the affected privileged mutation;
- ordinary break-glass is not a substitute for this workflow.

`temporary_supervision_by` is an organizational intervention mechanism. PACK-12 break-glass remains a separate emergency privileged-access mechanism with its own dual control, notification and independent post-hoc review obligations.

### Enforcement order

Every affected privileged state-changing request must be evaluated server-side at the moment of the act. Frontend state, an old role claim, an already-open page or a token issued before suspension must never be treated as sufficient authorization.

Minimum decision chain:

```text
REQUEST
-> authentication and current session state
-> current actor authority state
-> regional scope authorization
-> active authority suspension / RegionalAdministrationRestriction
-> owning-domain rule and purpose
-> separation of duties / required approvals / assurance
-> ALLOW or reason-coded DENY
```

The frontend may display the result but is never the security boundary.

### Evidence, review and restoration

Every Level 1–4 action must create durable reason-coded evidence appropriate to its class. Levels 2–4 must preserve the exact governing decision, scope, affected authority/action set, proposer, approver, evidence basis, start/end time, notification state and review deadline.

Historical records must not be rewritten or hidden because an intervention occurred. In particular, intervention authority must not delete or alter prior decisions, correspondence, documents, audit events or evidence. Corrections and reversals use new restoration/revocation/superseding records.

The implementation must support a governed path to:

```text
SUSPEND / RESTRICT
-> REVIEW
-> RESTORE | REVOKE | SUPERSEDE
```

A contested intervention must have a review/appeal path supplied by the competent later legal/governance rule. The technical system must preserve the records needed for that review even before the final legal role allocation is fixed.

### Implementation placement

| Layer / owner                           | Mandatory responsibility                                                                                                                                                                                    | Must not do                                                                                                                                      |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `organization-service`                  | Own current organizational scope, `OrganizationalAuthority` suspension state, regional restriction state and `temporary_supervision_by` relationship/effective dates.                                       | Must not infer intervention authority from hierarchy position or become a universal admin service.                                               |
| Identity / Security / privileged access | Terminate/quarantine privileged sessions and enforce privileged-session/JIT/break-glass controls.                                                                                                           | Must not decide membership, office removal, regional policy or substantive domain outcomes.                                                      |
| Governance / oversight                  | Own the governed human decision and rule references authorizing suspension, restriction, restoration, revocation or supervision.                                                                            | Must not gain implicit data access from an oversight title.                                                                                      |
| API                                     | Re-evaluate current session, authority, scope, restriction and domain authorization on every affected mutation and expose reason-coded outcomes.                                                            | Must not trust stale frontend/token scope or provide an upper-level bypass endpoint. Exact API-stage allocation remains stage-contract governed. |
| CTRL                                    | Provide scoped proposal, approval, review, restoration/revocation and supervision control surfaces with separation of duties.                                                                               | Must not expose a one-click universal `disable region` / `take over region` control.                                                             |
| FRONT                                   | Show the exact restriction/suspension state, affected scope/actions, reason/reference, review/expiry state and available remedy to authorized users. Preserve ordinary unaffected regional/member journeys. | Must not present the entire region or all members as suspended when only administrative authority is contained.                                  |
| OPS                                     | Provide incident containment, monitoring, expiry/review alerts, recovery and evidence handling.                                                                                                             | Must not silently extend intervention or convert an outage into permanent governance state.                                                      |
| SEC / FINAL INTEGRATION                 | Prove that stale sessions/tokens, cross-Land calls, hierarchy tricks, approval bypass, expired restrictions, supervision overreach and voting-boundary attacks fail on the exact integrated baseline.       | Must not infer safety from isolated service tests only.                                                                                          |

### Dependencies

At minimum:

- `FIR-INV-013` — Bund/Land/Kreis isolation;
- `FIR-INV-014` — no universal administration;
- `FIR-INV-009` — JIT and break-glass governance;
- `FIR-GOV-001` — Emergency Governance;
- `FIR-RULE-001` — governed rules and competent authority;
- ADR-034 regional scope authorization/inheritance;
- ADR-036 institutional authority lifecycle and separation of duties;
- PACK-12 privileged-access/break-glass controls;
- applicable audit, evidence, retention, notification and domain-specific voting/finance/communications controls.

### Acceptance criteria

The requirement is not complete until the integrated system demonstrates at least that:

1. suspending an exact authority immediately prevents its affected mutations even through a session/token/page opened before suspension;
2. an unrelated actor, authority, organization and Land remain unaffected;
3. ordinary unaffected member participation remains available during an administrative restriction;
4. Level 3 blocks only registered exact `action_code` values in the target scope and cannot become a blanket `region_disabled` state;
5. Bund/ancestor hierarchy position or role-name reuse alone cannot initiate, approve or execute an intervention;
6. Levels 2–4 enforce two-distinct-actor approval and reject self-approval;
7. temporary suspension/restriction/supervision expires and cannot be silently extended;
8. `temporary_supervision_by` grants only explicitly permitted functions and no blanket read/export access;
9. restriction/authority state that cannot be verified fails closed for the affected privileged mutation;
10. every intervention, restoration, revocation and supersession preserves immutable reason-coded audit/evidence history;
11. intervention cannot rewrite or erase prior decisions, correspondence, documents, audit events or evidence;
12. generic regional intervention cannot access ballots, identity-vote linkage, intermediate tally or bypass WS-03/election governance;
13. no universal administrator or cross-Land bypass path is introduced;
14. the exact integrated CTRL/FRONT flow can suspend, review and restore or revoke authority while preserving the regional body's unaffected operation.

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

**Status:** partial

Must avoid opaque scoring and preserve contestability, context and disclosure control.

The sentence above is the entry as it was captured and is unchanged. PACK-34
(repository `0.36.0`) implements against it and expands what it would take
to satisfy it, without altering what it originally meant.

The requirement is satisfied only when all five hold:

1. **No opaque scoring.** No scalar or composite value ranks a participant
   politically, under any name, and no method is undisclosed. — _implemented_
   in PACK-34: refused by exact key and by suffix at both payload boundaries,
   absent from the signal record by construction, and every rule's method is
   generated from the rule definition rather than written beside it.
2. **Contestability.** The participant a signal concerns can have it
   reviewed, the review is recorded, a correction creates a new version and
   the original is never silently removed. — _mechanism implemented_ in
   PACK-34; the notification that would let a participant know a signal names
   them is not, and is `FIR-DELREP-003`.
3. **Context binding.** No indicator without organizational scope,
   delegation scope, observation window, calculation version, source
   reference and a disclosure sentence; no indicator that follows a
   participant into another scope. — _implemented_ in PACK-34.
4. **Disclosure control.** No figure is stated where the population it was
   computed over is small enough that the arithmetic identifies an
   individual. — _not satisfied_: the mechanism exists and no governed
   minimum population does, so every figure that needs one is withheld.
   `FIR-DELREP-002`.
5. **Governed operation.** Whatever is computed in production is computed
   under rules a competent body activated, against thresholds it set. —
   _not satisfied_: no body is recorded as competent. `FIR-DELREP-001`.

`FIR-DEL-001` moves to `implemented` only when 4 and 5 are met as well.

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

## V21 governance maintenance record — Party-organ competence and digital authority binding (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is accepted or closed by this update. No Satzung provision or party-organ competence becomes legally effective merely because this project requirement is recorded.

**New FIR ID created:** `FIR-GOV-005 — Statutory Party-Organ Competence & Digital Authority Binding` — status `approved`, priority `critical`.

**Governed proposal artifacts:**

- `docs/governance/EPD2_PARTY_ORGAN_COMPETENCE_AND_DIGITAL_AUTHORITY_MODEL_0.1.md`;
- `docs/governance/EPD2_SATZUNG_AMENDMENT_PROPOSAL_REGIONAL_COMPETENCE_0.3.md`.

**Boundary:** the Civic OS target model is approved as a future implementation/governance requirement. The accompanying Satzung text remains a non-adopted legal draft until the competent party founding/party congress process adopts it after legal review. Software must not treat the draft as a legally active RuleVersion before that event.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. Exact allocation among API-02…API-06 and later INFRA/OPS/CTRL/FRONT/SEC remains stage-contract governed.

## FIR-GOV-005 — Statutory Party-Organ Competence & Digital Authority Binding

**Status:** approved
**Priority:** critical
**Domain:** party governance / organizational competence / rules / authorization / regional autonomy
**Target:** Satzung and governed Nebenordnung proposals + rules registry + `organization-service` + API + CTRL + FRONT + OPS + SEC + FINAL INTEGRATION

### Purpose

EPD² must bind every consequential digital organizational authority to the exact lawful and satzungsmäßige competence of the party organ that created or controls it. Civic OS must represent the federated party structure without converting organizational hierarchy into inherited access or universal administration.

Core invariant:

```text
organizational hierarchy
!= legal/political competence
!= OrganizationalAuthority
!= data access
!= technical administration
!= security authority
!= voting authority
```

### Required organizational competence model

The target model must support at least:

- Bundesverband;
- Landesverbände;
- Kreis-/Bezirksverbände;
- Ortsverbände;
- non-Gebietsverband local working groups where adopted.

Every formal Gebietsverband must have the democratically required assembly and Vorstand according to the adopted Satzung and mandatory law. Land-level and other required party courts/review bodies must remain independent from the boards they review.

The highest assembly of each Gebietsverband owns the matters reserved to that level by law/Satzung. Its Vorstand executes lawful decisions and conducts ordinary business within the exact scope assigned to that Verband. A higher Verband receives no lower-scope office, data access, finance authority or technical permission from hierarchy alone.

### Competence provenance

Every consequential `OrganizationalAuthority` must be resolvable to:

- exact subject/office holder;
- exact role/office code;
- exact organization and territorial/institutional scope;
- exact capability set;
- exact governing Satzung/Ordnung/RuleVersion;
- exact source election, appointment or governed decision;
- appointing/deciding organ;
- validity interval and current lifecycle state;
- applicable SoD/approval requirement;
- audit/evidence references;
- review/appeal route where applicable.

Role display text, hierarchy position or possession of a login/credential is never sufficient proof of organizational competence.

### Bund / Land / Kreis / Ort boundary

At minimum the future rules must distinguish:

- Bundessatzung and Bund-wide programme decisions from Land/Kreis/Ort positions;
- Land programme/budget/organization from Bund and other Länder;
- Kreis/Bezirks and Orts matters from higher-level reserved matters;
- the right to propose to a higher organ from the right to decide the higher organ's matter;
- candidate nomination/Aufstellung from Wahlvorschlag filing/signature authority;
- party office from public mandate;
- political/organizational authority from technical/security/key authority.

### Membership territorial assignment

Membership is membership in EPD² as one party. Territorial organizational assignment may determine the competent Land/Kreis/Ort participation scope but must not create separate memberships or duplicate voting rights.

Assignment changes are effective-dated and may not rewrite historical participation, decisions, candidacies or audit evidence. A territorial assignment alone never grants administrative authority.

### Financial competence

Financial authority is scope-bound. The Beitrags- und Finanzordnung must remain the governing place for contribution allocation and detailed Bund/Land/Kreis/Ort financial rules.

The digital model must support separation at least between preparation/request, approval, execution, booking/reconciliation and independent review. A finance role in one scope does not inherit another scope.

### Intervention chain

`FIR-GOV-004` remains the technical intervention contract. `FIR-GOV-005` requires the adopted Satzung/Ordnung to supply the competent political-organ chain that authorizes Levels 2–4.

The target normative proposal is:

- Land target: Bundesvorstand temporary measure where authorized -> confirmation by next Bundesparteitag -> Bundesschiedsgericht remedy;
- Kreis/Bezirk target: Landesvorstand temporary measure where authorized -> confirmation by next Landesparteitag -> competent Land/Bund court route;
- Orts target: competent Kreis-/Bezirksvorstand, or Landesvorstand where no competent Kreis exists -> confirmation by next competent higher Parteitag -> competent court route.

No such mapping is legally activated by this FIR alone. Until an adopted RuleVersion exists, runtime must fail closed rather than infer competence from hierarchy.

Technical security containment of a compromised session/credential remains distinct from political/organizational intervention and does not remove an office by itself.

### Digital-permission constitutional rule

The adopted Satzung/Ordnung and the implementation must preserve:

```text
technical permission does not create legal competence
recovery of authentication does not restore suspended office
security containment does not create disciplinary authority
party office does not create credential/key authority
platform operation does not create party-organ authority
oversight does not automatically create data access
```

No universal `Bund admin`, `regional superadmin`, `root party admin` or equivalent may be introduced as a shortcut around this rule.

### Voting carve-out

Ordinary political, organizational, identity, platform, security, key-custody and temporary-supervision roles must not obtain voting trust-domain authority from this FIR. Voting/election credentials, trustee keys, ballot secrecy and identity-vote unlinkability remain governed by the isolated voting domain and its own lawful roles.

### EPD Plattform e.V. boundary

Technical operation by EPD Plattform e.V. must remain contractually and technically separate from party-organ competence. Technical capability does not create membership, candidacy, programme, finance, disciplinary, publication or voting authority.

### Required companion normative documents

Before legal activation of the target model, EPD² must establish and legally review at least:

- consolidated Satzung provisions for regional structure, organs, competence, member assignment and intervention;
- `Organisations-, Zuständigkeits- und Kompetenzordnung (OZKO)`;
- reconciled Schiedsgerichtsordnung;
- reconciled Beitrags- und Finanzordnung;
- reconciled Wahl- und Kandidaturenordnung;
- machine-readable RuleVersion mapping compatible with those adopted texts.

The governed proposal artifacts for this FIR are:

- `docs/governance/EPD2_PARTY_ORGAN_COMPETENCE_AND_DIGITAL_AUTHORITY_MODEL_0.1.md`;
- `docs/governance/EPD2_SATZUNG_AMENDMENT_PROPOSAL_REGIONAL_COMPETENCE_0.3.md`.

### Implementation placement

| Layer / owner                     | Mandatory responsibility                                                                                                                       | Must not do                                                                   |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Satzung / OZKO / rules governance | Define legally competent organs, scope, delegation, intervention, review and exact RuleVersions.                                               | Must not be replaced by software defaults or hierarchy inference.             |
| `organization-service`            | Represent organizations, relations, scopes and `OrganizationalAuthority` lifecycle bound to source decisions/rules.                            | Must not create competence from role labels or parent relation alone.         |
| API/runtime                       | Re-evaluate current actor + scope + capability + active restrictions + assurance at action time.                                               | Must not trust stale token/profile role claims as final authority.            |
| CTRL                              | Provide governed request/approval/intervention/review queues, SoD and evidence.                                                                | Must not expose universal takeover/admin controls.                            |
| FRONT                             | Show office, scope, source authority, restrictions and remedy accurately.                                                                      | Must not imply a technical role is a political office or vice versa.          |
| OPS                               | Operate lawful administrative/security procedures and escalation.                                                                              | Must not convert emergency containment into permanent political intervention. |
| SEC                               | Test cross-scope escalation, self-grant, stale authority, approval bypass, court/audit tampering and voting escape.                            | Must not accept hierarchy-based authorization as a shortcut.                  |
| FINAL INTEGRATION                 | Prove exact adopted rule -> organ decision/election -> OrganizationalAuthority -> allowed/denied action -> immutable evidence -> review chain. | Must not infer completion from documentation or isolated service tests.       |

### Dependencies

At minimum:

- `FIR-GOV-004` — Regional Authority Suspension & Intervention Control;
- `FIR-SEC-004` — Governed Access, Credential & Key Authority Lifecycle Control;
- `FIR-RULE-001` — governed procedural rules / RuleVersion semantics;
- `FIR-INV-013` — Bund/Land/Kreis isolation;
- `FIR-INV-014` — no universal administration;
- applicable party-court, finance, candidacy, membership, audit, privacy and voting requirements.

### Acceptance criteria

This FIR is not implemented merely because the proposal documents exist.

Acceptance requires an adopted legally reviewed competence baseline and integrated proof that:

1. hierarchy alone cannot grant lower-scope access;
2. every consequential `OrganizationalAuthority` resolves to exact adopted rule + competent source decision/election + scope;
3. Bund, Land, Kreis/Bezirk and Ort reserved competences cannot be silently substituted by another level;
4. regional programme authority cannot mutate the Bund programme outside the Bund procedure;
5. member territorial reassignment does not create duplicate rights or rewrite history;
6. nomination and filing/signature authority are separate where law requires;
7. public mandate and party office remain separate;
8. finance authority and audit can be separated by scope and act;
9. Levels 2–4 regional intervention can execute only from the adopted competent-organ chain and remains reviewable;
10. identity/security/key operators cannot grant or restore party-organ competence;
11. party officers cannot self-mint privileged technical/key authority;
12. EPD Plattform e.V. technical control cannot become party-organ authority;
13. voting trust-domain authority cannot be obtained through ordinary organization/platform roles;
14. invalid, stale, expired, suspended or legally unactivated competence fails closed;
15. immutable decision/audit/court evidence survives intervention, reorganization and restoration.

## FIR-SEC-004 — Governed Access, Credential & Key Authority Lifecycle Control

**Status:** approved  
**Priority:** critical  
**Domain:** authentication / authorization / privileged access / credential lifecycle / cryptographic key management / security operations  
**Target:** identity and credential services + privileged-access service + organization/governance integration + service identity + API + INFRA + OPS + CTRL + FRONT + SEC, with a separate voting trust-domain boundary

EPD² must implement one governed authority model for access blocking, credential recovery/replacement, service credential issuance and cryptographic key lifecycle management without turning any human, organizational level, infrastructure operator or security function into a universal administrator.

Core rule:

```text
authentication credential != session != organizational authority != privileged grant != service credential != cryptographic key
```

A second mandatory rule is:

```text
request != approve != execute/custody != audit
```

The implementation may automate low-risk mechanical steps after an authorized decision, but it must preserve the authority split, purpose, scope and evidence of the decision. A technical ability to generate, store, revoke or rotate a credential/key does not itself grant legal, political, organizational or business authority.

### Control-object classes

The system must distinguish at least the following classes. A later accepted implementation may refine names and schemas but must not collapse their authority semantics.

1. **Human authentication credentials.** Passkey/WebAuthn credentials are the preferred target where supported. Any governed fallback authentication factor is a separate credential class. A server/operator must not manufacture and hand a user a passkey private key; the authenticator/device generates the key pair and the platform registers the public credential after the governed enrollment/recovery gate.
2. **Recovery factors and recovery decisions.** Recovery is proof-and-approval workflow, not an ordinary login method and not a universal administrator override. Recovery may restore the ability to authenticate; it does not prove membership/eligibility and does not grant or reactivate an `OrganizationalAuthority`.
3. **Sessions and session-renewal artifacts.** Browser/session state, refresh/renewal artifacts and equivalent runtime sessions are independently quarantinable/revocable. Session invalidation is not the same act as credential revocation.
4. **`OrganizationalAuthority`.** This is an authorization/governance object, not a cryptographic key. Assignment, activation, suspension, restoration, expiry and revocation remain governed by organization/governance rules and `FIR-GOV-004` where regional intervention applies.
5. **Privileged JIT and break-glass grants.** These are short-lived, purpose/scoped privilege elevations controlled by the privileged-access plane. They are neither permanent roles nor substitute authentication credentials.
6. **Service-to-service / workload credentials.** Workload identity, mTLS/certificate credentials, signed service assertions or an accepted equivalent must be scoped to a service/workload and purpose. Static long-lived shared secrets are disfavoured and may exist only where a later accepted design explicitly governs them.
7. **Platform cryptographic keys and certificates.** This includes signing keys, encryption/wrapping keys, TLS/certificate private keys and equivalent key material selected by accepted INFRA/runtime architecture. Root/master/KEK/HSM-backed classes are governed only if the accepted architecture actually adopts them.
8. **Provider/API/client secrets where unavoidable.** Human-shared long-lived API keys are prohibited as a normal access model. Any unavoidable client/provider secret must have an owning service, exact scope, lifecycle, expiry/rotation policy, secret-storage boundary and revocation evidence.
9. **Voting/election credentials and keys.** These remain in the voting trust domain. Generic identity administrators, regional administrators, platform operators, security operators and ordinary key custodians do not obtain voting-key authority from this FIR.

### Authority roles

The implementation must represent responsibilities explicitly. One natural person may hold more than one organizational role only where the applicable risk/SoD policy permits it; a single consequential operation must still satisfy its required separation.

- **Subject / principal:** person or workload whose credential/access is affected.
- **Requester:** initiates the governed change and states purpose/scope.
- **Identity/Credential operator:** executes allowed human-credential lifecycle operations after the required proof/decision; cannot grant organizational authority merely because they can manage credentials.
- **Security operator:** performs incident containment such as session quarantine and emergency credential/key revocation within explicit incident authority; cannot silently issue replacement authority or close substantive governance cases.
- **Privileged-access operator/control plane:** administers JIT and break-glass mechanics; cannot become a universal business/data administrator.
- **Service owner:** owns the operational need for a workload credential/key and requests changes for that service; does not obtain unilateral cryptographic custody by ownership alone.
- **Key custodian / KMS-HSM or certificate operator:** generates/stages/rotates/destroys cryptographic material within authorized policy; possession/custody does not grant business authority.
- **Governance/domain approver:** confirms competent purpose, scope and authorization for consequential changes; approval does not require access to plaintext private material.
- **Recovery approver:** evaluates recovery evidence at the assurance required for the affected account/workspace; privileged recovery requires stronger controls than ordinary self-service recovery.
- **Independent reviewer/auditor:** verifies evidence, SoD, timing and outcome; must not need plaintext private keys/secrets to perform review.
- **Voting trustee/quorum:** separate domain-specific key authority where the voting architecture requires it; not inherited from other roles.

### Rights are separate capabilities

For every managed credential/key class, the authorization model must be able to distinguish:

- `REQUEST`;
- `APPROVE`;
- `GENERATE_OR_ENROLL`;
- `READ_METADATA`;
- `VIEW_OR_EXPORT_SECRET` where technically possible and explicitly allowed;
- `ACTIVATE`;
- `SUSPEND_OR_QUARANTINE`;
- `REVOKE`;
- `RESTORE` where restoration is legally/technically permitted;
- `ROTATE_OR_REPLACE`;
- `DESTROY`;
- `REVIEW_OR_AUDIT`.

No broad role label such as `admin`, `security`, `Bund`, `platform operator` or `key manager` implicitly grants all of those capabilities.

### Canonical authority matrix

The following is the minimum planning matrix. A later domain policy may require stronger controls but must not weaken the listed separation for consequential operations.

| Operation                                                | Request / initiate                                                               | Approve                                                                                                                                                   | Execute / custody                                                                                        | Secret/private-material visibility                                                                                 | Independent evidence/review                                              |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Enrol ordinary passkey                                   | subject after authenticated/enrollment gate                                      | policy/self-service gate; additional approval only where risk requires                                                                                    | authenticator generates private key; credential service registers public credential                      | subject authenticator only; operator never receives private key                                                    | automated immutable audit; anomaly review as governed                    |
| High-assurance lost-device/account recovery              | subject or authorized support intake                                             | recovery approver; privileged accounts require distinct stronger approval/dual control                                                                    | credential service enables bounded re-enrollment; subject creates replacement credential                 | no operator-created passkey private key; recovery evidence is separately protected                                 | mandatory reason/evidence; privileged recovery independently reviewed    |
| Quarantine/revoke active sessions                        | subject self-service where applicable or security operator under incident policy | immediate containment may be pre-authorized by policy; broader/continued intervention follows governed approval                                           | session/security service                                                                                 | no credential private-key access implied                                                                           | reason-coded incident/audit record; review proportional to impact        |
| Revoke compromised human authenticator                   | subject or security/credential operator under explicit scope                     | ordinary self-revoke may be self-service; administrative/high-impact revoke follows governed approval                                                     | credential service                                                                                       | operator sees credential metadata/public material only                                                             | revocation and replacement linkage preserved                             |
| Suspend/restore/revoke `OrganizationalAuthority`         | competent governance/security process                                            | `FIR-GOV-004`/owning governance rule; Levels 2–4 require two distinct authorized humans                                                                   | organization/governance service enforces state                                                           | no credential/key secret access implied                                                                            | immutable decision/evidence/review/appeal chain                          |
| Grant JIT privileged access                              | authorized requester                                                             | separate authorized approver                                                                                                                              | privileged-access service activates scope + TTL                                                          | only task-required data/secret access; no generic secret export                                                    | mandatory grant/use/expiry evidence; post-review by risk class           |
| Activate break-glass                                     | authorized emergency requester                                                   | distinct controller under PACK-12 policy unless a stricter emergency rule applies                                                                         | privileged-access service activates bounded emergency grant                                              | only explicitly approved emergency scope                                                                           | auto-expiry/revoke + mandatory independent post-use review               |
| Issue/replace service credential                         | service owner/requester                                                          | service/security/platform authority according to risk class                                                                                               | workload identity/certificate/key platform generates or enrols; delivery is machine-bound where possible | service receives only what its protocol requires; custodians should use handles/non-exportable keys where possible | issuance, scope, expiry and consumer evidence reviewed                   |
| Generate platform cryptographic key                      | service/domain owner requests purpose                                            | governance/security/platform approver according to key class; high-impact/root classes require dual control or stronger quorum                            | KMS/HSM/certificate/key custodian                                                                        | private material non-exportable where supported; approver/auditor need no plaintext                                | generation attestation/metadata and policy version preserved             |
| Activate/scheduled-rotate signing, encryption or TLS key | service owner/key lifecycle controller                                           | class-specific approval; high-impact rotation requires distinct approver                                                                                  | key platform/custodian stages and activates                                                              | no broader plaintext visibility than technically unavoidable                                                       | cutover, verifier convergence and old-key retirement evidence            |
| Emergency revoke compromised service/platform key        | security incident authority                                                      | immediate containment may be pre-authorized; replacement activation follows required SoD; root/high-impact exceptions require governed break-glass/quorum | key/cert/workload platform revokes and propagates new trust state                                        | containment does not grant right to inspect unrelated secrets                                                      | incident evidence + mandatory post-action review and replacement linkage |
| Destroy retired cryptographic key                        | lifecycle controller/service owner after retention/decryption dependency check   | class-specific approver; high-impact classes require dual control/quorum                                                                                  | KMS/HSM/key custodian destroys or cryptographically erases                                               | no export before destruction                                                                                       | destruction attestation/evidence retained without secret material        |
| Root/master/KEK ceremony, if adopted                     | designated key-governance authority                                              | governed quorum stronger than a single operator; exact threshold defined by accepted INFRA/SEC policy                                                     | HSM/KMS custodians under ceremony                                                                        | split/quorum/non-exportable handling; no single plaintext custodian                                                | independent witness/evidence mandatory                                   |
| Voting-domain key change                                 | voting-domain governed actor/trustee                                             | voting-specific trustee/quorum/governance only                                                                                                            | voting trust-domain components                                                                           | generic platform/regional/security admins excluded                                                                 | voting-domain evidence/challenge rules only                              |

### Human credential lifecycle

Minimum lifecycle semantics:

```text
PENDING_ENROLLMENT
-> ACTIVE
-> SUSPENDED | RECOVERY_REQUIRED
-> ACTIVE (only through a valid recovery/restoration decision where allowed)
   | REVOKED
   | REPLACED
```

Exact database enum names remain implementation-stage governed. Required semantics are:

- credential IDs/versions are stable and audit referenced;
- a revoked/replaced credential is never silently resurrected under the same credential ID/version;
- replacement creates new credential identity and links to the superseded/revoked credential;
- recovery status does not restore a separately suspended `OrganizationalAuthority`;
- an administrative authority suspension does not automatically revoke an ordinary member's authentication credential unless a separate security/recovery decision requires that containment.

### Session lifecycle

Minimum semantics:

```text
ACTIVE
-> QUARANTINED | REVOKED | EXPIRED
```

A credential or authority change that requires runtime invalidation must define which existing sessions/tokens are invalidated, quarantined or allowed to expire. Every privileged mutation re-evaluates current session/credential/authority/restriction state at use time; an old token or open page is never an authorization guarantee.

### Organizational-authority lifecycle

The existing governed semantics remain controlling:

```text
ACTIVE
-> SUSPENDED
-> ACTIVE | REVOKED
```

with expiry where applicable. Authentication recovery, passkey replacement, service-key rotation and break-glass do not themselves assign/reactivate organizational authority.

### JIT and break-glass lifecycle

Minimum JIT semantics:

```text
REQUESTED
-> APPROVED
-> ACTIVE (exact scope + purpose + TTL)
-> EXPIRED | REVOKED
-> REVIEWED where required
```

Minimum break-glass semantics:

```text
DECLARED
-> DUAL-CONTROLLED / GOVERNED ACTIVATION
-> BOUNDED EMERGENCY USE
-> AUTO-EXPIRE OR REVOKE
-> MANDATORY POST-USE REVIEW
```

Break-glass must not become the routine path for credential recovery, key replacement, region takeover or voting-domain access.

### Service credential / cryptographic key lifecycle

Minimum semantics:

```text
REQUESTED
-> APPROVED
-> GENERATED
-> STAGED
-> ACTIVE
-> RETIRING
-> REVOKED
-> DESTROYED when retention/decryption obligations permit
```

Compromise path:

```text
ACTIVE
-> COMPROMISED
-> REVOKED
-> NEW KEY/CREDENTIAL ID + governed replacement
```

A compromised or revoked key version is never returned to `ACTIVE`. Planned rollovers use a new version/ID.

### Key generation and custody rules

- Private key material must be generated in the endpoint authenticator, workload identity boundary, KMS/HSM/certificate system or other accepted protected execution boundary appropriate to its class.
- Passkey private keys remain in the user's authenticator/device boundary; support staff do not issue or email them.
- Platform signing/encryption/private certificate keys should be non-exportable when the accepted KMS/HSM/runtime technology supports it.
- Private keys, API secrets and recovery secrets must not be distributed through email, chat, tickets, ordinary document stores or ad-hoc downloadable bundles.
- Approvers and auditors receive metadata, policy/evidence and public material, not plaintext private keys merely because they approve/review.
- Backup/escrow is class-specific. The system must not assume every private key is escrowed or recoverable. Any escrow capability requires its own access, quorum, retention and restore evidence.
- Where secret export is technically unavoidable, it must be an explicit capability with reason, target, one-time/short-lived delivery, recipient binding and audit; export must not be the default key-management path.

### Planned rotation protocol

Every key/credential class that supports rotation must have a governed class policy defining its maximum age or renewal condition, `rotate_before` window where applicable, overlap rules, verifier/consumer convergence target, revocation cutoff and retention/destruction rule. This FIR intentionally does not invent one universal number of days for all key classes.

Minimum planned rollover:

```text
1. INVENTORY / OWNERSHIP CHECK
2. REQUEST ROTATION with reason, class, scope, consumers and target time
3. REQUIRED APPROVAL / SoD CHECK
4. GENERATE NEW key/credential version in protected boundary
5. STAGE NEW PUBLIC/TRUST/CONSUMER MATERIAL
6. VALIDATE consumers/verifiers before cutover
7. ACTIVATE NEW version
8. BOUNDED OVERLAP only where protocol requires it
9. OBSERVE convergence and failures
10. RETIRE OLD version
11. REVOKE OLD version at governed cutoff
12. DESTROY/ARCHIVE only according to retention/decryption obligations
13. CLOSE with exact evidence and independent review where required
```

Overlap is permitted only for a bounded planned rollover or explicitly governed compatibility window. It must not become indefinite dual validity.

### Emergency compromise protocol

A suspected/confirmed credential/key compromise must support rapid containment without allowing the incident responder to self-grant replacement business authority.

Minimum sequence:

```text
DETECT / REPORT
-> CLASSIFY affected credential/key + consumers + scope
-> CONTAIN sessions/workloads/key use
-> REVOKE or disable compromised material as quickly as the protocol safely permits
-> GENERATE a new ID/version through the governed replacement path
-> UPDATE trust sets/consumers
-> INVALIDATE dependent sessions/tokens where required by the affected signing/authentication key
-> VERIFY old material is rejected
-> RESTORE only required service/user capability
-> PRESERVE evidence
-> INDEPENDENT POST-INCIDENT REVIEW
```

Emergency policy may pre-authorize one qualified security actor to perform immediate containment/revocation when delay would worsen exposure. It must not thereby authorize that actor alone to approve and grant a new high-impact organizational authority, root/master key or voting key. Any emergency bypass must be the separately governed break-glass path and must receive mandatory post-use review.

### Signing-key / verifier trust-set rollover

Where the accepted runtime uses token/document signing keys and a JWKS or equivalent trust-set publication mechanism:

1. generate a new signing key/version in the approved protected boundary;
2. publish/stage its public verification material before first use where the protocol permits;
3. confirm verifier discovery/cache health;
4. begin signing with the new active version;
5. keep the old public verification material only for the bounded lifetime/cache window needed to verify already-issued artifacts;
6. stop new signing with the old key;
7. after governed verifier convergence/artifact lifetime, mark old key revoked/retired and remove it from active trust according to protocol;
8. prove that new artifacts use the new version and old material can no longer create accepted new artifacts.

A key compromise may require accelerated removal and explicit revocation/deny handling instead of normal overlap.

### Encryption-key rotation / rewrap protocol

Where the accepted architecture uses versioned encryption or envelope keys:

- new writes use the new active key/version after cutover;
- retained ciphertext must remain decryptable only for as long as its retention/legal purpose requires;
- rewrap/re-encryption is performed according to the accepted data/key architecture, not by silently deleting an old key before dependent data is migrated or expired;
- migration progress and decryptability verification are observable;
- old decrypt authority is retired only after dependency and retention checks;
- destruction produces evidence and must not erase required audit/history.

No key-management operator gains a general right to browse decrypted business data merely because the platform can decrypt it.

### TLS/certificate rotation protocol

For service/server/client certificates where adopted:

```text
REQUEST/RENEW
-> ISSUE new certificate/key under approved identity
-> STAGE
-> VALIDATE chain, SAN/identity, expiry and consumer trust
-> DEPLOY/CUT OVER
-> MONITOR handshake/authentication health
-> REMOVE/REVOKE old certificate/key
-> VERIFY no stale endpoint/consumer depends on old identity
```

Private key reuse across renewal is prohibited by default unless a later accepted certificate policy explicitly justifies an exception.

### Service credential protocol

Service credentials must bind at minimum:

- workload/service identity;
- environment;
- audience/peer or permitted consumer where protocol supports it;
- purpose/scope;
- issuer;
- issuance time;
- expiry/renewal condition;
- credential/key version;
- revocation status;
- owning service/team/function;
- audit/correlation reference.

Prefer automatically renewed short-lived workload identity or certificates over manually distributed long-lived static secrets where the accepted architecture supports it. Automated renewal is not automated expansion of business authority: the renewed credential inherits only the already-approved service identity/scope and must fail if that authority has been revoked.

### Human recovery and replacement protocol

A lost device/passkey does not allow support staff to create a replacement private key for the user.

Minimum path:

```text
RECOVERY REQUEST
-> identify account/workspace and risk class
-> verify governed recovery evidence at required assurance
-> check account/authority/security restrictions
-> approve recovery according to risk/SoD
-> invalidate/quarantine affected old sessions/credentials as required
-> create a bounded re-enrollment window
-> subject enrolls a NEW authenticator/passkey
-> credential service records new credential ID and supersession link
-> re-establish only the assurance/access actually proved
-> notify subject through governed channel
-> preserve evidence and review privileged recoveries
```

Recovery must not silently restore a suspended office, privileged role, candidacy, voting eligibility or other separately governed authorization.

### Blocking and restoration rules

Blocking actions are scoped to the affected control object:

- session quarantine blocks sessions, not membership;
- credential revocation blocks that authenticator/credential, not automatically organizational membership;
- authority suspension blocks governed administrative/political authority, not automatically ordinary login;
- service credential revocation blocks that workload credential, not all services in the organization;
- key revocation blocks that key version/cryptographic use, not unrelated business authority;
- regional intervention follows `FIR-GOV-004` and must contain authority rather than disable the region;
- voting-domain suspension/revocation requires its own voting-specific governance.

Restoration must re-evaluate the current state. A previous grant or credential does not automatically spring back merely because an incident ticket is closed.

### Root/master/KEK ceremony, if later adopted

If accepted INFRA architecture introduces HSM/KMS root, master or key-encryption-key classes with material organizational impact, their lifecycle must use a separately defined ceremony/profile that includes at least:

- named key class/purpose;
- governed quorum stronger than a single actor;
- separate proposer/approver/custodian responsibilities;
- protected generation inside the approved HSM/KMS boundary where supported;
- non-exportability or explicitly governed split/backup handling;
- witness/attestation evidence;
- activation/cutover plan;
- recovery/backup test where recoverability is intended;
- emergency revocation/rotation plan;
- destruction/retirement evidence.

The exact quorum threshold and cryptoperiod are deliberately left to the accepted INFRA/SEC key-class profile; recording this FIR does not prematurely choose a cloud KMS/HSM vendor or root-key topology.

### Voting-domain isolation

Generic access/key governance must not create a back door into WS-03 or voting cryptography.

In particular, generic identity/credential/security/key administrators must not by this authority:

- mint voting credentials;
- recover or export voting private/trustee key material;
- reveal identity-vote linkage;
- decrypt ballots;
- reveal an intermediate tally;
- rotate voting keys outside the election/trustee ceremony;
- revoke voting credentials in bulk;
- bypass trustee/quorum/challenge controls;
- convert an ordinary member/admin session into Voting Client authority.

Voting key/credential lifecycle is governed by the voting domain's own accepted contracts, trustees/quorum and evidence rules.

### Common operation record

Every consequential credential/key lifecycle action must preserve enough structured evidence to reconstruct what was authorized and what actually occurred, including as applicable:

- operation ID;
- control-object class;
- credential/key ID and version without storing unnecessary secret material;
- subject/workload/service;
- requester;
- approver(s);
- executor/custodian;
- reviewer where required;
- exact scope/purpose/action;
- reason code;
- governing policy/rule version;
- assurance level/evidence references;
- source incident/recovery/decision reference;
- generation/enrollment method;
- `valid_from`, expiry/TTL/rotation target;
- activation time;
- old/new version linkage;
- overlap window if any;
- trust-set/consumer propagation evidence;
- session/token invalidation consequence where applicable;
- revoke/retire/destroy time and reason;
- notifications;
- rollback/failback reference where used;
- immutable audit/evidence correlation.

Audit records contain metadata/evidence, not plaintext private keys or recovery secrets.

### Failure and fail-closed rules

For privileged or consequential mutations:

- unverifiable current session/credential status fails closed;
- unverifiable `OrganizationalAuthority` or active restriction state fails closed;
- unverifiable service credential/key revocation state fails closed where accepting the request would create privileged/consequential effect;
- expired credentials/keys/grants are not accepted because a cache or frontend still shows them;
- key/trust-set propagation failures surface as operational incidents and may block cutover rather than silently extending unsafe validity;
- an inability to perform rotation does not authorize ad-hoc secret sharing;
- a failed recovery does not authorize manual role assignment;
- a revoked key/credential version must be rejected after its governed cutoff.

### Implementation placement

| Layer / owner                       | Mandatory responsibility                                                                                                                                                                         | Must not do                                                                                                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Identity / credential services      | Human credential enrollment, public-credential metadata, revocation/replacement, governed recovery state/evidence and assurance outcome.                                                         | Must not manufacture passkey private keys, grant organizational authority or use recovery as universal bypass.                                           |
| Session/authentication runtime      | Issue, validate, quarantine, revoke and expire sessions/tokens according to current credential/security state.                                                                                   | Must not trust stale authority claims after governing state has changed.                                                                                 |
| `organization-service` + governance | Own `OrganizationalAuthority` assignment/suspension/restoration/revocation and FIR-GOV-004 relationships.                                                                                        | Must not equate possession of a login/key with office or organizational authority.                                                                       |
| `privileged-access-service`         | JIT and break-glass grants, exact purpose/scope/TTL, dual control and post-use evidence.                                                                                                         | Must not become permanent superadmin or routine credential-recovery path.                                                                                |
| Service identity / API runtime      | Bind workload credentials to exact service/environment/audience/purpose and re-evaluate current credential/authority state at use time.                                                          | Must not turn a valid machine credential into unrestricted cross-service business authority. Exact API-stage allocation remains stage-contract governed. |
| INFRA                               | Provide accepted KMS/HSM/certificate/secret/workload-identity substrate, protected generation/storage, non-exportability where supported, trust-set publication and key-version mechanics.       | Must not select/activate a provider or expose secret material outside accepted region/policy merely because the FIR exists.                              |
| OPS                                 | Inventory/ownership, rotation/expiry monitoring, compromise response, convergence monitoring, recovery runbooks, notification and destruction/retirement operations.                             | Must not silently extend expired keys, bypass approval or distribute secrets through ad-hoc channels.                                                    |
| CTRL                                | Request/approval/custody/review workflows, SoD enforcement, key/credential status, expiry/rotation queues, evidence inspection and ceremony controls.                                            | Must not expose one-click universal `reset all access`, `mint admin key` or cross-domain bypass controls.                                                |
| FRONT                               | Safe enrollment/recovery/status UX; show blocked/recovery/expiry state and available remedy to authorized users.                                                                                 | Must not display private key material unnecessarily, claim a blocked authority is restored from login alone or become the authorization boundary.        |
| SEC / FINAL INTEGRATION             | Adversarially prove stale credential/session/key rejection, rotation correctness, compromise containment, secret non-disclosure, SoD, cross-scope isolation and exact integrated recovery paths. | Must not infer safety from the existence of KMS/HSM or isolated unit tests.                                                                              |
| Voting trust domain                 | Own voting-specific credentials/keys, trustee/quorum ceremonies and election-specific revocation/rotation.                                                                                       | Must not inherit generic platform/regional/security key-admin authority.                                                                                 |

### Dependencies

At minimum:

- PACK-14 authentication-method and recovery-control matrices;
- PACK-12 privileged-access / JIT / break-glass controls;
- `FIR-GOV-004` Regional Authority Suspension & Intervention Control;
- `FIR-INV-009` JIT and break-glass governance;
- `FIR-INV-013` Bund/Land/Kreis isolation;
- `FIR-INV-014` no universal administration;
- applicable identity/session/authorization and service-to-service API stage contracts;
- audit, evidence, retention, legal-hold, notification and DLP controls;
- voting-domain trust-boundary, credential and trustee/quorum rules;
- accepted INFRA key/secret/certificate technology decisions when those stages are opened.

### Acceptance criteria

This requirement is not complete until the exact integrated baseline demonstrates at least that:

1. a user can enrol a new passkey without any operator receiving or generating the passkey private key;
2. lost-device recovery proves/approves recovery and creates a new credential ID without silently restoring separately suspended organizational authority;
3. session quarantine immediately prevents affected privileged use while leaving unrelated credentials/ordinary rights unchanged unless separately governed;
4. revoking a human credential does not itself grant a replacement credential or organizational authority;
5. `OrganizationalAuthority` suspension remains separately governed under `FIR-GOV-004` and survives login/passkey recovery until explicitly restored;
6. JIT access is exact-purpose/scope/TTL and cannot become a permanent role;
7. break-glass requires its governed control path, automatically expires/revokes and receives mandatory post-use review;
8. a service owner can request but cannot unilaterally mint/activate an unrestricted production credential outside the accepted risk/approval policy;
9. platform private key material is non-exportable where the selected technology supports it, and approvers/auditors can perform their jobs without plaintext secret access;
10. a planned rotation stages a new version, performs bounded cutover/overlap where required, proves consumer/verifier convergence and rejects the retired version after cutoff;
11. a compromised key/credential can be rapidly revoked and replaced under a new ID/version without resurrecting the compromised version;
12. signing/trust-set rollover does not create an indefinite window in which both old and new keys can mint accepted new artifacts;
13. encryption-key retirement does not destroy decryptability before governed migration/retention dependencies are satisfied;
14. certificate rotation validates identity/chain and removes stale certificate dependence after cutover;
15. expired/revoked credentials, sessions, grants and keys are rejected despite stale frontend state, cache state or old tokens;
16. no actor can perform request + consequential approval + unrestricted secret custody/export + evidence deletion as one universal-admin path;
17. every consequential issue/recovery/activation/rotation/revocation/destruction action has durable reason-coded evidence linking requester, approver, executor/custodian, scope, policy, old/new version and outcome;
18. audit/review can be completed without storing plaintext private keys/recovery secrets in audit records;
19. no generic key-management capability creates cross-Land, cross-service or universal business authority;
20. generic credential/security/key administrators cannot mint, recover, decrypt, rotate or bulk-revoke voting-domain credentials/keys outside the voting domain's own trustee/quorum governance;
21. any root/master/KEK class actually adopted by INFRA is operated under a separately accepted quorum ceremony/profile rather than single-operator control;
22. exact CTRL/FRONT workflows clearly distinguish blocking, recovery, replacement, authority restoration and key rotation instead of presenting them as one generic administrator action.

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

## FIR-AI-003 — Governed Correspondence Analysis & Reply Drafting

**Status:** approved  
**Priority:** high  
**Domain:** AI accountability / correspondence / casework / member support / representative desk  
**Target:** AI processing services, owning correspondence/casework services and all relevant staff-facing frontend surfaces

EPD² must provide governed AI assistance for the analysis of incoming written correspondence and the preparation of reply drafts where the acting user is authorized to access the underlying material.

The capability applies, as permitted by the owning domain, to e-mail, contact-form submissions, member and citizen inquiries, complaints and petitions, representative-desk intake, routed internal correspondence and governed document/attachment references.

### Required analysis capabilities

For an authorized correspondence item or thread, the AI assistance layer must be able to:

- produce a concise structured summary without dropping material requests or qualifications;
- identify the sender context available to the authorized workflow without creating a new global person identifier;
- classify the subject, intent and owning procedural/domain context as an advisory classification;
- extract explicit questions, requests, allegations, commitments, deadlines, dates, references and attachment dependencies;
- distinguish answered, partially answered and still-open points;
- identify contradictions or material changes against prior authorized correspondence and case history;
- retrieve and cite only authorized relevant context from the same thread/case and, where permitted, governed decisions, programme provisions, Satzung/internal rules, published material and other approved sources;
- flag factual assertions that require verification rather than presenting them as established truth;
- flag possible legal, procedural, privacy, security or political-risk questions for human review without making the final determination;
- identify missing information required for a complete answer;
- prepare a complete reply draft addressing the open points;
- offer alternative drafting modes where useful, including concise, detailed, formal and plain-language variants;
- revise the draft after human edits or instructions while preserving the source/provenance boundary.

### Authorization and context boundary

AI assistance must never expand access.

Every source supplied to the analysis must already be accessible to the acting principal for the stated purpose and organizational scope. Context assembly and retrieval must enforce the same authorization, purpose, classification, retention, legal-hold, DLP and cross-domain correlation rules as direct access to the source.

The correspondence AI path must not receive prohibited material merely because it could improve a draft. In particular, secret-ballot content, voting-linkability data, credential secrets, unrestricted identity records, protected evidence outside the actor's scope, live operational secrets and unrestricted audit exports remain outside the AI input boundary.

Attachments and source documents remain owned by their source/document domains. AI processing may reference or process an authorized rendition according to policy; it does not become a second authoritative document store.

### Grounding and provenance

Every analysis and reply draft must use the `FIR-AI-002` provenance and staleness contract and the AI accountability context's governed processing record.

The record must bind the output to the exact correspondence/thread/case snapshot and relevant source-set versions used to generate it. A material change to the incoming item, thread, attachments, cited decision, policy, programme provision or other relied-upon source must make the prior analysis/draft stale where the governed staleness policy so requires.

User-facing/staff-facing presentation must distinguish:

- source-supported facts;
- extracted requests/questions;
- AI inference or recommendation;
- unresolved or unverifiable claims;
- missing sources/evidence;
- the current draft version and its provenance/staleness state.

Hidden chain-of-thought is not a governed evidence artifact and must not be stored or exposed. The durable accountability record consists of the permitted structured analysis, source/provenance references, model/configuration identity, output digest, human-review state and audit evidence.

### Human authority and sending boundary

Core rule:

```text
AI analysis / draft != organizational decision != authorized send
```

AI may analyze, summarize, recommend and draft. It must not autonomously:

- establish or change an official political, legal, disciplinary, financial, membership, candidacy, voting or procedural position;
- approve its own consequential output;
- finalize a governed decision or close a case;
- alter the source correspondence or authoritative case record;
- impersonate the sender, member, representative or staff actor;
- send an official consequential reply;
- invoke a provider callback/tool/command path that mutates EPD² state.

A consequential or official reply must pass the owning domain's required human review/approval, authority, scope, assurance and separation-of-duties controls before the normal correspondence/delivery path sends it. The final send action and its authoritative content/version must be separately auditable from the AI draft.

Automated transmission is prohibited by default. A future narrowly defined non-substantive acknowledgement may be enabled only by a separate governed decision with explicit template/content limits, routing, audit and opt-out/error handling; it must not silently become a substantive AI-generated answer.

### Audit and correction

The system must preserve, according to policy:

- the incoming correspondence reference and governed snapshot/version;
- AI processing/provenance reference;
- structured analysis result;
- draft version and digest;
- human edits or superseding draft references where retained by policy;
- reviewer/approver outcome for consequential use;
- the final authorized reply version;
- delivery/send evidence from the owning communication/delivery domain;
- reason-coded failure, rejection and escalation states.

Corrections create a new governed version or superseding AI processing record; they do not rewrite historical analysis or a previously sent official reply.

### Required staff interaction model

Relevant workspaces must support the governed flow:

```text
Original correspondence
-> AI analysis
-> authorized history/context
-> open questions and verification flags
-> recommended response structure
-> reply draft
-> human review/edit/approval
-> authorized send
-> governed case/correspondence history
```

The UI must make clear which content is original source material, which is AI-generated, which was changed/approved by a human and which exact version was actually sent.

### Implementation placement matrix

`FIR-AI-003` is a cross-layer capability. No single implementation stage, service, generic chatbot, frontend component or AI-provider integration may claim this FIR complete in isolation.

The following placement is mandatory unless a later governed architecture decision explicitly reallocates ownership without weakening the boundaries below.

| Layer / owner                                                    | Mandatory responsibility for `FIR-AI-003`                                                                                                                                                                                                                                                                                                                              | Must not own / claim                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Existing domain services / Communications and Casework ownership | Own the authoritative incoming correspondence/thread/case state, sender/recipient routing context, attachment references, procedural status, final authorized reply and delivery linkage. Assemble only the case/domain context the acting principal is already authorized to access.                                                                                  | Must not delegate authoritative correspondence/case ownership to the AI service or treat AI output as the case decision.                                                                                                                              |
| `ai-processing-service`                                          | Perform governed summarization, classification, recommendation, drafting, verification flags and structured correspondence analysis; enforce redaction/provenance, model/configuration identity, staleness, human-review state and fail-closed prohibited-input controls.                                                                                              | Must not become the authoritative message/document store, widen authorization, close a case, establish organizational position or send/mutate Civic OS state.                                                                                         |
| Document / evidence ownership                                    | Preserve immutable/versioned attachment and document references, governed renditions, exact sent-response versions and applicable retention/legal-hold evidence.                                                                                                                                                                                                       | Must not duplicate source ownership inside the AI-processing record.                                                                                                                                                                                  |
| API                                                              | Expose governed production contracts/BFF composition for requesting analysis, reading structured results and provenance, generating/revising drafts, submitting required human review/approval state and invoking the owning correspondence delivery path after authorization. API contracts must preserve actor, purpose, scope, correlation and version identifiers. | Must not introduce a direct AI-provider-to-send shortcut or an endpoint that bypasses owning-domain authorization/human approval. Exact allocation among API stages is governed by their stage contracts; this FIR does not pre-accept any API stage. |
| INFRA                                                            | Provide the deployable AI runtime/provider path, credentials and secret handling, network and region isolation, queue/execution substrate, approved retention modes, model endpoint configuration and provider availability controls required by the accepted API/runtime design.                                                                                      | Must not activate a provider or data route outside approved region/retention/policy boundaries or claim application-level completion.                                                                                                                 |
| OPS                                                              | Define and operate monitoring, timeout/retry/cancellation policy, degraded-mode behavior, escalation to humans, provider outage handling, incident response, recovery and operational evidence for correspondence AI processing.                                                                                                                                       | Must not silently auto-send when AI/provider processing fails or substitute retries for human review.                                                                                                                                                 |
| CTRL                                                             | Provide governed control-plane surfaces for reviewer queues, reviewer authority/scope, model/prompt/policy version visibility, approval/rejection/supersession, audit inspection, configuration controls and separation-of-duties enforcement for consequential outputs.                                                                                               | Must not allow AI self-approval, universal admin access or configuration that bypasses the owning workflow's authority model.                                                                                                                         |
| FRONT                                                            | Provide the staff-facing workflow `Original correspondence -> AI analysis -> authorized context -> open questions/verification flags -> reply draft -> human edit/review/approval -> authorized send -> history`, with clear provenance/staleness and source-vs-AI-vs-human distinctions.                                                                              | Must not present AI output as already approved, hide stale/ungrounded state, or simulate unsupported backend capability as complete.                                                                                                                  |
| SEC                                                              | Adversarially verify prompt-injection resistance, poisoned attachments/context, prohibited-input handling, authorization/correlation boundaries, data exfiltration attempts, provider/tool escape attempts, human-approval bypasses and exact-send integrity on the integrated baseline.                                                                               | Must not test only the model in isolation; the target is the complete accepted cross-layer path.                                                                                                                                                      |
| FINAL INTEGRATION                                                | Prove the exact end-to-end path from authorized intake through AI processing/context grounding and human approval to the exact delivered version and durable audit/evidence history on the accepted integrated baseline.                                                                                                                                               | Must not infer completion from isolated unit/service tests or from the existence of `ai-processing-service`.                                                                                                                                          |

### Stage-completion rule

Implementation is cumulative across the canonical execution sequence:

```text
API contracts and runtime boundaries
-> INFRA provider/runtime substrate
-> OPS operational behavior
-> CTRL review/control surfaces
-> FRONT staff workflow
-> FINAL INTEGRATION proof
-> SEC adversarial verification of the exact integrated baseline
```

A stage may satisfy its own scoped obligations without satisfying `FIR-AI-003` as a whole. The FIR remains unimplemented until the end-to-end acceptance criteria below are demonstrated against the governed integrated baseline.

### Dependencies

At minimum:

- `FIR-AI-002` — AI Analysis Provenance and Staleness Contract;
- `FIR-SUPPORT-002` — AI Assistance Boundary;
- applicable correspondence/document/delivery governance;
- `FIR-AUTH-001` — consequential commit reauthorization where applicable;
- `FIR-ID-001` — cross-domain identifier and correlation governance;
- applicable privacy, retention, legal-hold, DLP and audit requirements.

### Acceptance criteria

The requirement is not satisfied merely because a generic chatbot or text-generation endpoint exists.

Acceptance requires an end-to-end governed correspondence workflow demonstrating that:

1. an authorized incoming item/thread can be analyzed into the required structured result;
2. relevant prior context is retrieved without expanding source authorization;
3. unanswered points, deadlines, verification needs and source gaps are visible;
4. a grounded reply draft can be generated and revised;
5. provenance, exact source snapshot/version and staleness are visible and auditable;
6. consequential output cannot be approved or sent by the AI itself;
7. the exact human-authorized version sent through the owning delivery path is recorded separately from the AI draft;
8. prohibited inputs and cross-domain correlation attempts fail closed;
9. correction/supersession preserves history rather than rewriting it;
10. no production, legal-effect or autonomous-authority claim is made without the corresponding governed activation evidence.

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

> **Authoritative status overlay — register recovery 2026-08-09:** the
> accepted cumulative baseline is PACK-24 / repository `0.26.0`, not
> PACK-14 or PACK-15. Detailed older subsections below are retained as
> historical round snapshots.

## Current accepted cumulative reference baseline

- PACK-01 through PACK-24 are carried in the accepted cumulative baseline;
- repository version: `0.26.0`;
- Canon version: `0.8.0`;
- latest accepted immutable candidate SHA-256:
  `1da174681759a9925e2d5a8dc95b04ea383ba55f62bb502e18dd6e7a6fc29cf7`;
- PACK-21: assemblies, motions and minutes;
- PACK-22: communications and official correspondence;
- PACK-23: complaints, petitions and ombuds casework;
- PACK-24: protected reporting and investigations;
- PACK-24 authoritative Windows CI: PASS;
- PACK-24 AVH 0.1.3 integration: accepted;
- no production-readiness or legal-activation claim follows from this
  cumulative acceptance.

The older “Implemented” and PACK-14-specific paragraphs below are preserved
for historical traceability. They must not be read as the current baseline
pointer.

## Implemented

- PACK-01 through PACK-10 (PASS);
- PACK-11 (PASS — external GitHub Actions verification complete);
- PACK-12 (PASS — external GitHub Actions verification complete);
- PACK-13 (PASS — external GitHub Actions verification complete);
- PACK-14 (PASS — external GitHub Actions verification complete);
- **PACK-15 (PASS — external GitHub Actions verification complete);**
- FRONT-00;
- FRONT-01;
- finance reference implementation;
- governed documents and evidence reference implementation (PACK-11);
- privileged administration, authorization-aware search and governed
  export reference implementation (PACK-12);
- production data plane and contract evolution reference implementation
  (PACK-13);
- identity, authentication and account security reference
  implementation (PACK-14);
- **voting trust boundary, eligibility and credential separation
  reference implementation** (PACK-15);
- cumulative architecture baseline;
- 45 visual snapshots.

"Reference implementation" is the operative qualifier for PACK-10 through
PACK-15 alike: the governed workflows are real and externally verified;
the production infrastructure is not. PACK-13 is the sharpest case of the
distinction, because it is the pack _named_ for the production data plane
and every storage adapter in it is a Python dictionary. PACK-14 is the
second sharpest, and in a different way: its persistence really is
migrated, transactional and durable across a restart — on SQLite through
the standard library — while all four of its security ports refuse
because no WebAuthn library, password hasher, breached-password corpus or
signature verifier is bound, and no identity provider is selected.
Nothing in this list is production ready or legally activated.

## What PACK-14's PASS does and does not cover

The six bounded contexts specification §4.1 assigns to `identity-service`
exist in reference form and are externally verified: the account lifecycle
that represents locks, restrictions and closure requests without extending
canon 7.2's six statuses, passkey-first authentication behind a
verification port, the fenced password fallback, MFA with SMS OTP
deliberately absent as a factor class, the fail-closed assurance
conjunction, the session aggregate with two mandatory deadlines, action-
and object-version-bound step-up, the per-workspace authentication
bootstrap that is explicitly not SSO, the identity-free WS-03 voting
handoff boundary, the governed recovery workflow, the proofing boundary
and the scoped identity mappings. Behind them is a reference persistence
path that really runs — ten applied SQL migration artefacts, 29 tables, 35
indexes, eleven durable adapters, transaction boundaries and an
optimistic-concurrency guard — and a runnable reference service boundary
for 12 of the 42 catalogued operations.

The PASS covers exactly that and nothing beyond it. PACK-14 integrates no
production IAM, no eID scheme, no email or SMS provider and no HSM or KMS;
it implements no WebAuthn cryptography and no password-hashing algorithm,
and **all four security ports refuse when unbound**, so an unconfigured
deployment cannot enroll or replace a password at all; it deploys no
production database and claims no operational durability; it exposes no
HTTP surface and no production gateway; and it builds no frontend, so
`FIR-UX-011` stays **future**. `FIR-ROADMAP-004` is therefore
`implemented in reference form`, not `implemented`.

## Specified but not implemented

- most domains in this register;
- FRONT-02 Member Core;
- assemblies;
- decision register (PACK-11 provides the document foundation only);
- member payments;
- SEPA mandate record (PACK-11 provides the mandate _evidence_ foundation only);
- full voting implementation;
- the **production** data plane — PACK-13 delivers the contracts, gates and
  refusals in reference form and deploys no database, broker, schema
  registry or search engine;
- canonical forms, submissions and official renditions (section 26);
- the cross-cutting procedural, trust and operational foundations
  (section 27);
- the frontend design, visualization and interaction governance layer
  (section 28), including `FIR-UX-011`'s page and screen catalogue —
  FRONT-00 and FRONT-01 are the approved visual baseline, not a completed
  design system, and no page sequence is yet specified;
- identity/auth **beyond PACK-14's reference implementation** — no
  production IAM, no eID scheme, no provider integration of any kind, no
  production database or operational durability behind the reference
  persistence path, no HTTP surface or production gateway in front of the
  reference service boundary, and no Account & Security FRONT-PACK;
- communications (PACK-11 provides the correspondence-document foundation only);
- candidacy (PACK-11 provides the candidacy-document foundation only);
- the FIR-PROG-002 pre-adoption gate (PACK-11 provides the opinion-document
  foundation only);
- emergency governance;
- regional authority suspension and intervention control;
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

**Implemented by PACK-25 (`scripts/check_register_freshness.py`, wired into
`make check-repository` and into the local-CI driver):** the canonical
register exists at the path above; no second standalone future-register
file exists anywhere in the tree; the register's repository-version
expectation is not behind the repository's own `REPOSITORY_VERSION`; the
latest implementation round is represented; `FIR-BASE-001` distinguishes
the accepted baseline from the current candidate; and every governed PACK
round record carries the four FIR disposition categories section 1.3
requires. See `FIR-REG-001`.

The remaining bullets above are still unimplemented, and the PACK-25
checker deliberately does not pretend to cover them: it reads structure,
not meaning, and cannot tell a truthful round record from a plausible one.

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

> **This entry is strengthened later in this register.** Section 29B
> carries "V12 strengthening of FIR-ID-001 — Cross-Domain Identifier &
> Correlation Governance", which extends this requirement to schemas,
> events, logs, traces, analytics, search, exports, support tooling and
> cross-domain data mappings. It is a subsection of this entry rather than
> a second entry: `FIR-ID-001` is one requirement with one identifier, and
> the strengthening is part of it. Read both.

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

# 26. Canonical Forms, Submissions & Official Renditions

This section establishes forms, applications, declarations, submissions,
decisions and official documents as an independent mandatory layer of
EPD². They are not a cosmetic frontend afterthought. A domain is not
considered to cover its user journey merely because backend records and
workflow states exist while the actual form, official wording and
renditions remain undefined.

## FIR-FORM-001 — Canonical Forms and Submissions Framework

**Status:** approved  
**Priority:** critical  
**Domain:** cross-cutting forms / submissions / governed content / records / frontend  
**Target:** dedicated future foundation PACK or the next suitable core and frontend PACK  
**Dependencies:** PACK-09, PACK-11, PACK-12, PACK-13, PACK-14

Create one governed mechanism for defining forms and submissions.

The minimum normative model includes:

- `FormDefinition`;
- `FormVersion`;
- `FormSection`;
- `FormField`;
- `FieldOption`;
- `ConditionalVisibilityRule`;
- `ValidationRule`;
- `AttachmentRule`;
- `RequiredDeclaration`;
- `ConsentRequirement`;
- `SignatureRequirement`;
- `SubmissionDefinition`;
- `SubmissionDraft`;
- `SubmissionSnapshot`;
- `SubmissionCorrection`;
- `SubmissionWithdrawal`;
- `SubmissionDecision`;
- `SubmissionAppealReference`;
- `RenditionDefinition`.

Every form must define at least:

- a stable form ID;
- a domain owner;
- a version and lifecycle state;
- effective-from and retired-from dates;
- the legal, statutory or procedural basis;
- organization scope;
- eligible submitter categories;
- competent recipient or authority;
- mandatory and optional fields;
- conditional fields and visibility rules;
- validation rules;
- attachment requirements;
- exact declaration and consent texts;
- required confirmation, authentication or signature class;
- draft, submission, correction and withdrawal rules;
- submission and decision deadlines;
- confidentiality classification;
- retention schedule and legal-hold integration;
- accessibility and localization requirements;
- web, mobile, print and PDF renditions;
- an immutable submitted snapshot;
- audit and evidence references.

Changing a form must never alter an already submitted application. Every
submission keeps a durable reference to the exact form version, content
version, declarations and attachment rules in force at submission time.

Existing records, documents or workflow models do not by themselves
satisfy this requirement.

### Acceptance criteria

- A versioned form definition can be approved, activated, superseded and
  retired without changing prior submission snapshots.
- Required declarations, attachment rules and validation rules are bound
  to the same form version.
- A submission can be rendered consistently for digital review, printing
  and archival evidence.
- Retention, confidentiality, organization scope and legal hold are
  enforced without turning preservation into authorization.
- No consequential submission is accepted without explicit confirmation
  of the exact version presented to the submitter.

## FIR-FORM-002 — Domain Forms and Official Documents Inventory

**Status:** approved  
**Priority:** critical  
**Domain:** all business domains  
**Target:** every relevant domain PACK  
**Dependencies:** FIR-FORM-001

Every domain PACK must publish the complete set of user-facing and
administrative forms and official documents needed to complete the user
journeys claimed by that PACK.

Every relevant PACK must produce:

1. `FORM-INVENTORY.md` — all forms and official documents;
2. `FIELD-CATALOGUE.md` — fields, types, requiredness, dependencies and
   validation;
3. `CONTENT-CATALOGUE-DE.md` — exact German questions, explanations,
   declarations, warnings and confirmations;
4. `WORKFLOW-MATRIX.md` — submission, intake, review, correction,
   withdrawal, decision and appeal;
5. `ATTACHMENT-MATRIX.md` — permitted and required attachments;
6. `RENDITION-SPECIFICATION.md` — web, mobile, accessible, print and PDF;
7. `PRIVACY-RETENTION-MATRIX.md`;
8. acceptance fixtures covering a valid submission, incomplete
   submission, inadmissible submission, correction, withdrawal, approval,
   rejection and appeal where applicable.

A domain must not be described as fully covering its user process when it
only defines backend entities and state transitions but omits the actual
forms, fields, official wording and user-confirmed submission artifact.

### Mandatory PACK reporting rule

Starting with the next relevant domain PACK, its Specification, Acceptance
Matrix and Final Report must contain a section titled:

```text
Forms and Official Documents Coverage
```

That section must state:

- which forms are fully defined;
- which exist only as system models;
- which official texts are still missing;
- which web, mobile, accessible, print and PDF renditions exist;
- which forms are deferred;
- which FIR entries are addressed;
- whether a missing form blocks PASS and why.

Absence of a form is a PASS blocker when the primary user journey claimed
by the PACK cannot be completed without it.

## FIR-FORM-003 — Initial EPD² Forms and Documents Catalogue

**Status:** approved  
**Priority:** high  
**Domain:** cross-domain inventory  
**Target:** complete before the main PACK-19 through PACK-35 implementation sequence  
**Dependencies:** FIR-FORM-001

Prepare one preliminary catalogue of all anticipated EPD² forms,
applications, declarations, notifications, confirmations, decisions and
official records.

The catalogue must cover at least the following groups.

### Membership

- membership application;
- acknowledgement of receipt;
- request for missing information;
- correction of personal data;
- change of address and contact details;
- change of payment details;
- membership confirmation;
- suspension and termination notices;
- resignation from membership;
- rejection decision;
- objection and appeal.

### Candidacy and nomination

- candidacy application;
- nomination proposal;
- candidate consent;
- withdrawal;
- eligibility declaration;
- conflict-of-interest disclosure;
- supporting-document confirmation;
- admission or exclusion decision;
- objection and appeal.

### Party offices and mandates

- application for party office;
- consent to nomination;
- duty declaration;
- interest disclosure;
- resignation from office or mandate;
- office-holder report;
- documents for the open representative's table.

### Programme and initiatives

- programme proposal;
- initiative;
- amendment;
- withdrawal of proposal;
- request for AI analysis;
- expert opinion;
- legal opinion;
- readiness declaration;
- decision on admission to voting.

### Assemblies and meetings

- request to convene;
- participation registration;
- request for online participation;
- agenda-item proposal;
- amendment;
- procedural motion;
- proxy where legally and procedurally permitted;
- conflict-of-interest declaration;
- objection to minutes;
- request to correct minutes.

### Complaints and oversight

- complaint;
- Ombuds submission;
- ethics complaint;
- confidentiality request;
- protected disclosure;
- whistleblowing submission;
- recusal request;
- objection;
- appeal;
- decision notice.

### Finance

- donation declaration;
- donation receipt or confirmation;
- expense reimbursement request;
- advance request;
- expense report;
- financial disclosure;
- source-of-funds confirmation;
- suspicious-transaction notification;
- receipt and review confirmation.

### Data and documents

- access request;
- correction request;
- deletion request;
- objection to processing;
- export request;
- document request;
- request for an official copy;
- receipt confirmation;
- confidentiality request;
- access-restriction decision.

### Citizen Office

- citizen submission;
- consultation request;
- petition;
- complaint;
- problem report;
- consent to referral to a competent authority;
- status request;
- case closure;
- appeal or review request.

### Personnel, procurement and contractors

- candidate application;
- onboarding declarations;
- confidentiality declaration;
- conflict-of-interest disclosure;
- procurement request;
- vendor declaration;
- bid submission;
- evaluation declaration;
- reimbursement and invoice approval;
- offboarding confirmation.

### Lobbying and parliamentary transparency

- lobbying-contact disclosure;
- meeting disclosure;
- gift or benefit disclosure;
- external-interest declaration;
- parliamentary initiative submission;
- explanation of deviation from the member mandate;
- public representative report.

For every catalogue item, record at least:

- provisional form ID;
- domain owner;
- intended submitter;
- receiving authority;
- legal, statutory or procedural basis;
- confidentiality class;
- expected attachments;
- signature or authentication class;
- workflow;
- retention class;
- responsible future PACK.

## FIR-FORM-004 — Governed Form Content and Language Catalogue

**Status:** approved  
**Priority:** high  
**Domain:** governed content / documents / localization / accessibility  
**Target:** Canonical Forms foundation and every later domain PACK  
**Dependencies:** FIR-FORM-001, PACK-11

The actual wording of a form must be governed, versioned content rather
than text embedded only in frontend source code.

Governed content includes:

- German form names;
- questions and instructions;
- help text and tooltips;
- declarations and consent wording;
- legal and procedural notices;
- warnings;
- confirmation text;
- correction and rejection messages;
- accessibility labels;
- print and PDF labels.

Every content version must have:

- an owner;
- a version ID;
- language;
- effective date;
- approval evidence;
- a reference to the form version;
- supersession history;
- content digest;
- immutable historical availability.

A translation must not silently alter legal or procedural meaning. Where
multiple languages are offered, the authoritative language and the
relationship between versions must be explicit.

For the frontend DE/EN baseline, German is the default and authoritative
language for legally, procedurally and institutionally material German party
content unless an exact later governed decision states otherwise. English is a
governed translation rendition. Material EN content must be linked to the exact
DE source/version and carry translation status and approval evidence. Missing,
stale or unapproved English material must not be silently presented as current
authoritative content; the current German authoritative rendition remains
available with an explicit translation-status/fallback notice.

## FIR-FORM-005 — Multi-Channel Official Renditions

**Status:** approved  
**Priority:** high  
**Domain:** frontend / governed documents / accessibility / evidence  
**Target:** future Public Website, Member Core and administrative frontend PACKs  
**Dependencies:** FIR-FORM-001, PACK-11

One approved form version must produce consistent official renditions for:

- desktop web;
- mobile web;
- an accessible representation;
- printable form;
- archival PDF;
- immutable submission receipt;
- administrative review view.

All renditions must derive from the same governed `FormDefinition` and the
same content-catalogue version. A print or PDF rendition must not differ
from the digital form in mandatory questions, declarations, warnings or
confirmation requirements.

The immutable submission receipt must contain at least:

- form ID and form version;
- submission ID;
- submission date and time;
- submitting party in the permitted identity form;
- organization scope;
- attachment inventory;
- declarations explicitly confirmed;
- digest or equivalent integrity reference;
- submission channel;
- next procedural step and applicable deadlines.

### Boundaries for FIR-FORM-001 through FIR-FORM-005

These entries:

- do not make the forms framework implemented;
- do not change `CANON_VERSION`;
- do not expand PACK-13 implementation scope;
- are approved future obligations;
- must be carried forward in the authoritative cumulative Master Future
  Implementation Register;
- may be marked implemented only by a later governed PACK with concrete
  forms, content, workflows, renditions, tests and evidence.

# 27. Cross-cutting procedural, trust and operational foundations

The entries in this section complete the end-to-end path of an official
party action:

```text
applicable rule
→ form or request
→ identity or representation
→ submission
→ signature or confirmation
→ delivery
→ review
→ decision
→ service of decision
→ correction or appeal
→ evidence and archive
```

These entries are approved future obligations. They do not expand PACK-13
implementation scope and are not implemented merely because supporting
records, documents, events or workflow primitives already exist.

## FIR-RULE-001 — Governed Policy and Decision Rules Registry

- **Status:** `approved`
- **Scope:** cross-cutting governance and decision logic
- **Target:** future governance/rules foundation and every consequential
  domain PACK
- **Dependencies:** PACK-09, PACK-11, PACK-13 and the relevant domain PACK

EPD² must maintain a governed registry of the procedural and normative rules
used to make consequential decisions. Important rules must not exist only in
frontend code, service conditionals, configuration fragments or human
instructions.

The registry must cover, where applicable:

- source rule, including Satzung, Geschäftsordnung, programme procedure,
  finance rule, election rule or approved policy;
- stable rule ID and version;
- domain owner;
- organizational scope, including Bund/Land/Kreis;
- competent authority;
- eligible actor;
- permitted and prohibited actions;
- quorum and majority requirements;
- thresholds;
- deadlines and time-computation rules;
- delegation and substitution limits;
- eligibility and admissibility rules;
- mandatory review and separation-of-duties requirements;
- effective date, expiry and supersession;
- exception and waiver rules;
- reason-code mapping;
- evidence and approval references.

Every consequential decision must preserve a reference to the exact rule
version applied, the competent authority, organization scope, material input
facts, result, reason codes, exceptions and evidence.

A rule change must not silently reinterpret historical decisions. Historical
rule versions remain immutable and available for audit.

### Acceptance criteria

- no consequential decision depends only on an unversioned code branch;
- rule version and authority are recorded with the decision;
- organizational competence is validated at execution time;
- superseded rules remain historically retrievable;
- rule exceptions are explicit, authorized and reason-coded.

## FIR-REF-001 — Governed Reference Data and Taxonomy Registry

- **Status:** `approved`
- **Scope:** cross-cutting reference data
- **Target:** future reference-data foundation and all domain PACKs
- **Dependencies:** PACK-11, PACK-13

Create a governed registry for controlled classifications and reusable codes,
including organization types, body types, meeting types, document classes,
procedure types, decision reasons, office types, attachment classes, expense
categories, communication channels and other shared taxonomies.

Each value must have:

- stable code;
- domain owner;
- German display name;
- description and intended meaning;
- version and lifecycle state;
- organizational or domain scope;
- effective and deprecation dates;
- replacement mapping;
- translation rules where applicable;
- evidence of approval.

A deprecated code must never be reused with a new meaning. Display labels may
change only through a governed version update, while stable codes preserve
contract compatibility.

### Acceptance criteria

- duplicate or semantically conflicting codes are detected;
- historical records retain the code meaning in force at the time;
- unknown values fail safely or enter controlled review;
- frontend labels are not the authoritative taxonomy source.

## FIR-DELIVERY-001 — Official Delivery, Receipt and Service Evidence

- **Status:** `approved`
- **Scope:** communications, decisions, deadlines and remedies
- **Target:** future communications/correspondence and domain PACKs
- **Dependencies:** PACK-09, PACK-11, PACK-13, future communications PACK

EPD² must distinguish ordinary communication from legally or procedurally
significant delivery.

The framework must support:

- ordinary message;
- notification;
- official notice;
- request for action;
- decision;
- deadline-triggering document;
- repeated service attempt;
- failed delivery;
- fallback channel;
- dispute about service.

Required evidence includes:

- recipient and capacity;
- content and document version;
- delivery channel;
- dispatch time;
- technical delivery result;
- opening or acknowledgement where relevant;
- explicit receipt confirmation where required;
- failure reason;
- fallback action;
- service date and deadline-start date;
- evidence bundle;
- re-service and dispute history.

A read/open status alone must not automatically be treated as legally or
procedurally sufficient service.

### Acceptance criteria

- deadline-triggering service uses an approved service rule;
- failed delivery cannot silently start a deadline;
- the exact served content version is preserved;
- fallback and re-service are reason-coded and auditable;
- notification policy remains neutral and identity-minimizing.

## FIR-TRUST-001 — Electronic Signature, Seal and Trusted Timestamp Framework

- **Status:** `approved`
- **Scope:** trust, submissions, decisions and official documents
- **Target:** future trust foundation with PACK-14 integration
- **Dependencies:** PACK-11, PACK-13, PACK-14

Define assurance classes for electronic confirmation and signature rather
than using a generic boolean such as `signed=true`.

The framework must distinguish:

- authenticated account confirmation;
- step-up authentication;
- typed electronic consent;
- simple electronic signature;
- advanced electronic signature where required;
- qualified electronic signature where required;
- organizational electronic seal;
- trusted timestamp;
- witness or dual approval;
- handwritten/offline fallback.

Each signed or sealed act must bind:

- signer;
- represented capacity;
- exact object and version;
- digest;
- signing method and assurance class;
- timestamp;
- certificate/provider reference where applicable;
- verification result;
- revocation or invalidation state;
- long-term validation evidence;
- fallback evidence.

PACK-14 may establish identity and authentication boundaries but must not
silently redefine the procedural meaning of signatures, seals or timestamps.

### Acceptance criteria

- each procedure declares the required assurance class;
- the signed object version is immutable;
- verification failure blocks consequential use;
- revocation and long-term evidence are preserved;
- provider outage has a governed fallback rather than an unsafe downgrade.

**Note added by the PACK-16D correction round (2026-08-02), recorded in
section 1.24. Outcome: `partially implemented`. Status stays `approved`.**

The correction delivers the **signature half** of this entry, for one
object class only — bulletin-board checkpoints. Ed25519 (RFC 8032
PureEdDSA) signing and verification over a canonical, domain-separated
payload that binds the signer's key identifier, the exact object and its
sequence, its digest and its publication phase; an authorised-signer
registry that is part of the election context rather than carried by the
artefact; declared-in-advance key rotation windows; and five distinct
fail-closed verification outcomes, so that verification failure blocks
consequential use rather than degrading.

**What this entry still does not have:**

```text
the timestamp half entirely   no trusted timestamp, no RFC 3161, no time
                              authority, no long-term validation evidence
assurance classes             one method for one object class is not a
                              framework distinguishing ten classes
revocation                    no revocation or invalidation state exists;
                              rotation windows are not revocation
certificates and providers    no certificate, no provider reference, no
                              governed fallback for provider outage
key custody                   no HSM, no issuance procedure, no custody
                              (OD-P16D-11)
registry authorisation        the verifier cannot confirm the signer
                              registry it was given was authorised
                              (OD-P16D-12)
```

**Owner of the remainder:** PACK-17 and later trust-foundation work. This
entry is **not closed** and the eight-item prohibition on closing external
review, independent implementation, production HSM and production key
ceremony is untouched by it.

## FIR-REPRESENT-001 — Representation, Mandate and Assisted Action

- **Status:** `approved`
- **Scope:** representation and delegated action
- **Target:** future representation foundation and all relevant domain PACKs
- **Dependencies:** PACK-11, PACK-13, PACK-14

EPD² must distinguish the person operating the system from the person or
organization on whose behalf an action is taken.

The model must preserve separately:

```text
actor
principal
beneficiary
authorizing authority
```

It must support, where legally or procedurally permitted:

- legal representative;
- authorized representative;
- organizational representative;
- assistant without decision authority;
- temporary substitute;
- guardian or comparable protected representation;
- submission on behalf of another person;
- withdrawal or expiry of mandate.

Each mandate must define:

- basis and evidence;
- scope;
- permitted and prohibited actions;
- organizational and domain scope;
- start and end;
- delegation/substitution rules;
- notification of the principal;
- revocation;
- attribution in audit and receipts.

Technical assistance must not silently become authority to make a
consequential decision.

### Acceptance criteria

- every represented action records actor and principal separately;
- an expired or revoked mandate blocks action;
- the representative cannot exceed the mandate scope;
- receipts and decisions clearly identify the represented capacity;
- representation does not create a global person identifier.

## FIR-INCLUSION-001 — Assisted, Offline and Alternative-Channel Procedure

- **Status:** `approved`
- **Scope:** accessibility, inclusion and procedural continuity
- **Target:** future forms/frontend and every citizen/member-facing PACK
- **Dependencies:** FIR-FORM-001, PACK-09, PACK-11, PACK-14

Accessibility must cover the whole procedure, not only the web interface.

Where the procedure permits, EPD² must support:

- postal submission;
- in-person submission;
- assisted digital submission;
- telephone assistance without hidden operator decision-making;
- accessible documents and alternative formats;
- plain-language explanation where procedurally permissible;
- interpretation or communication assistance;
- barrier-related accommodation;
- governed deadline relief where authorized;
- conversion of offline material into an immutable digital snapshot;
- operator verification;
- receipt to the submitting person;
- preservation of the original source.

A person must not lose procedural rights solely because of disability,
temporary technical failure, lack of a device or inability to use the
preferred digital channel.

### Acceptance criteria

- equivalent substantive requirements apply across channels;
- channel choice does not silently reduce rights;
- operator assistance is attributed and auditable;
- the original offline submission remains linked to the digital snapshot;
- inaccessible delivery or form design is a PASS blocker for the affected
  user journey.

## FIR-QUALITY-001 — Data Quality, Reconciliation and Discrepancy Management

- **Status:** `approved`
- **Scope:** cross-domain data quality and operational review
- **Target:** future data-quality foundation and all domain PACKs
- **Dependencies:** PACK-09, PACK-11, PACK-13

Create a governed mechanism for detecting and resolving:

- missing or incomplete data;
- conflicting records;
- stale references;
- suspected duplicate entities without automatic merge;
- source/projection divergence;
- payment and ledger discrepancies;
- organization-scope inconsistencies;
- invalid references;
- failed propagation;
- unresolved import records;
- backfill and migration discrepancies.

The mechanism must support:

- detection;
- severity and domain ownership;
- manual review queue;
- correction proposal;
- approval;
- evidence;
- affected-person notification where required;
- reconciliation result;
- residual-risk record.

Silent overwrite is prohibited. Historical corrections use correction,
supersession or reason-coded reconciliation rather than rewriting the past.

Identity reconciliation must not create a universal person ID. Voting data
must not participate in general identity reconciliation.

### Acceptance criteria

- source records are not silently changed from a projection;
- duplicate candidates are reviewed before merge;
- corrections preserve provenance and evidence;
- unresolved discrepancies remain visible and owned;
- financial and membership reconciliation remain separated by domain
  ownership.

## FIR-CONFIG-001 — Governed Operational Configuration

- **Status:** `approved`
- **Scope:** operational configuration and safe change
- **Target:** future configuration foundation
- **Dependencies:** PACK-11, PACK-12, PACK-13

Operational parameters that affect rights, deadlines, notifications,
thresholds, retention, workflow routing or safety must be governed,
versioned and auditable rather than hidden in mutable environment settings.

The framework must cover:

- stable configuration ID;
- owner;
- scope;
- type and validation;
- effective date;
- approval;
- change reason;
- rollback or supersession;
- environment placement;
- secret/non-secret classification;
- evidence;
- impact assessment.

Feature flags must not disable hard invariants, bypass compatibility gates,
change historical meaning or create a hidden legal rule.

### Acceptance criteria

- consequential configuration changes require approval and evidence;
- configuration history is immutable;
- invalid values fail closed;
- secrets are not stored in public configuration records;
- rollback does not rewrite history.

## FIR-IMPORT-001 — Legacy Import and Controlled Data Onboarding

- **Status:** `approved`
- **Scope:** migration from legacy or offline sources
- **Target:** future onboarding/import foundation and relevant domain PACKs
- **Dependencies:** PACK-09, PACK-11, PACK-13, FIR-QUALITY-001

Define governed import of members, documents, decisions, finance records,
organizational structures and archives.

Every import must specify:

- source and provenance;
- legal/procedural authority;
- source format and schema;
- mapping version;
- organization scope;
- validation;
- duplicate detection;
- rejection and review handling;
- idempotency;
- checkpoint and restart;
- reconciliation;
- evidence;
- retention and legal hold;
- final import report.

Imports must not invent missing facts, silently coerce ambiguous values,
create a global person identifier, or bypass domain invariants.

### Acceptance criteria

- every imported record retains provenance;
- rejected and ambiguous records are reported, not silently dropped;
- rerun is idempotent;
- imported decisions preserve original effective dates and evidence;
- voting secrets and identity-linked ballot data are excluded from general
  import.

## FIR-SERVICE-001 — Service Catalogue and Responsibility Directory

- **Status:** `approved`
- **Scope:** public/internal service discovery and routing
- **Target:** future Help Center, Public Website, Member Core and admin
  workspaces
- **Dependencies:** FIR-FORM-001, FIR-RULE-001, FIR-DELIVERY-001,
  FIR-INCLUSION-001

Create a governed catalogue of available party procedures and services.

For each service or procedure, publish or internally expose as appropriate:

- stable service ID;
- name and plain-language description;
- competent organization and role;
- eligible user;
- required form;
- required evidence;
- channels;
- expected processing time;
- legal or procedural deadline;
- delivery method;
- available remedies;
- accessibility and alternative-channel options;
- privacy/classification;
- escalation path;
- current availability and version.

The catalogue must be the shared source for Help Center routing, contextual
assistance and responsibility discovery. It must not expose protected
internal details or create an unauthorized directory of persons.

### Acceptance criteria

- users can identify the competent route without guessing;
- every listed form links to the governing service version;
- service ownership and escalation are explicit;
- outdated procedures are deprecated rather than silently replaced;
- public and internal views respect classification and organization scope.

## Section 27 boundaries

The entries in this section:

- are approved future obligations;
- do not change `CANON_VERSION`;
- do not expand PACK-13 implementation scope;
- are not covered by the external CI run for the PACK-13 implementation
  candidate;
- require their own future Specification/ADR, implementation candidate,
  external CI and FINAL PASS treatment;
- must be carried forward unchanged in cumulative archives until a governed
  later PACK updates their status or scope.

# 28. Frontend design, visualization and interaction governance

EPD² must preserve the restrained minimalist design already established in
the existing public pages and frontend foundation. Future workspaces must
evolve from that baseline rather than replacing it with unrelated visual
systems.
EPD² must preserve the exact visual implementation already established in
the accepted FRONT-00/FRONT-01 public pages and frontend foundation. That
implementation is the **canonical immutable visual baseline** for later
frontend work; ordinary FRONT-PACK scope does not include visual evolution,
modernization, refresh or restyling.

The preserved direction includes:
The canonical baseline includes:

- clear, calm and institutional presentation;
- Inter or the approved successor typeface;
- the exact accepted FRONT-00/FRONT-01 typeface configuration;
- restrained color usage;
- generous spacing;
- simple grids;
- strong hierarchy;
- limited decorative elements;
- accessible contrast;
- content-first layouts;
- clear status and decision semantics;
- no advertising-style visual noise;
- no gamification of consequential civic procedures.

This is a governed direction, not a freeze of every current pixel. Future
FRONT-PACKs may refine components and layouts where usability, accessibility
or domain risk requires it, while preserving the common visual character.
This is a governed visual freeze of the accepted implementation baseline.
Functional, usability, accessibility or domain-risk needs must first be
solved through existing canonical components and tokens. If a need genuinely
requires changing an established visual-baseline element, that change requires
a separate approved **Design Change Decision** before implementation, with the
exact affected element, rationale, before/after screenshots, accessibility
evidence and visual-regression impact.

## FIR-UX-003 — EPD² Design System and Component Governance

- **Status:** `approved`
- **Scope:** all public and authenticated frontend surfaces
- **Target:** future frontend foundation and every FRONT-PACK
- **Dependencies:** FRONT-00, FRONT-01, PACK-11, FIR-FORM-001

Create and govern the shared EPD² design system from the **canonical, immutable
FRONT-00/FRONT-01 visual implementation baseline**.

The approved FRONT-00 and FRONT-01 implementation is not merely a visual
reference. It is the canonical frontend design baseline. This includes the
current public pages, shared components, actual typography, spacing, color,
border, radius and layout tokens, header/footer and navigation geometry,
responsive behavior, interaction states and the accepted FRONT-00/FRONT-01
reference screenshots.

“Minimalist EPD² design” must not be interpreted as permission to produce a
new minimalist design, a visual refresh or an independently reinterpreted
version of the current pages. Future frontend work MUST reuse the existing
visual implementation. It MUST NOT evolve, modernize, restyle, reinterpret or
replace existing tokens, component styling, geometry or page composition for
aesthetic reasons.

New functionality may add content and components only by composing the
existing primitives and tokens. Where no existing component can express a
required function, the new component must be derived from the nearest
canonical component pattern without introducing a new visual language.

A change to any established visual-baseline element is permitted only through
a **separate explicit governed Design Change Decision** naming the exact
token/component/page affected and carrying before/after screenshots,
accessibility evidence and visual-regression impact. A feature requirement,
implementation convenience, developer preference, mockup or general claim of
“modernization” is not design-change approval.

Any frontend candidate that changes the canonical visual baseline without such
a Design Change Decision fails acceptance.

It must cover:

- typography;
- spacing and grid;
- layout widths;
- buttons and links;
- inputs and form sections;
- cards;
- tables and lists;
- tabs and navigation;
- status badges;
- alerts and notifications;
- dialogs;
- document upload;
- timelines;
- decision and evidence presentation;
- loading, empty and error states;
- responsive behavior;
- accessibility states;
- focus, hover and disabled states;
- component versioning;
- visual regression fixtures.

The design system must not hide domain differences behind overly generic
components. Voting, finance, membership and protected reporting may share
visual primitives but must preserve their distinct risk and interaction
semantics.

### Minimalist baseline requirements

- content and task hierarchy dominate decoration;
- no unnecessary gradients, animation, shadows or visual effects;
- color is used sparingly and never as the sole status indicator;
- whitespace and typography provide primary structure;
- institutional trust must not be simulated through ornamental complexity;
- public and internal surfaces remain visibly related without becoming
  indistinguishable;
- changes to any established visual-baseline element require a separate approved
  Design Change Decision; ordinary design review, accessibility evidence,
  implementation convenience or a mockup does not authorize such a change.

## FIR-UX-004 — Information Architecture and Navigation Governance

- **Status:** `approved`
- **Scope:** public site and ten-workspace frontend architecture
- **Target:** future Public Website and workspace FRONT-PACKs
- **Dependencies:** Target Frontend Architecture 0.8.2 CORRECTED

Define governed information architecture for:

- public versus authenticated navigation;
- the ten workspaces and ten origins;
- personal, organizational and administrative contexts;
- Bund/Land/Kreis scope;
- breadcrumbs;
- task entry points;
- deep links;
- mobile navigation;
- return to unfinished work;
- safe cross-workspace handoff;
- isolated Voting Client navigation;
- session and identity boundary visibility.

### Regional and local organization operating model

The frontend must implement one EPD² platform with organization-scoped views,
not separate local products or independently designed mini-sites for Landes-,
Kreis-, Orts- or other governed party bodies.

Public regional discovery uses `/regionen` and `/regionen/[slug]`. A regional
detail page is a hub within the common public site and, where approved public
content exists, must be able to present `Übersicht`, `Aktuelles`, `Termine`,
`Initiativen`, approved public `Personen`, public `Wahlen`, `Dokumente &
Transparenz` and `Kontakt`. Only approved public organization projections and
public renditions may appear. Internal member directories and protected
operational data remain excluded.

Regional public content must reuse centrally governed content families and be
filtered/projected by authoritative organization scope. The frontend must not
create independent regional copies of authoritative `Aktuelles`, `Termine`,
initiative, election, person or document data merely to construct a local page.

Authenticated member and administrative surfaces must make the active
organization scope visible whenever it materially changes authority, dataset or
procedural meaning. A scope selector may expose only authorized Bund/Land/Kreis/
Orts/body scopes. Changing scope must re-evaluate authorization and purpose and
clear or invalidate incompatible stale context. Workspace access does not create
party-wide or cross-regional authority, and no universal regional administrator
may be introduced.

Binding regional votes use the same isolated Voting Client and the same voting
trust boundary as Bund-level votes. The handoff is one-time, purpose-scoped and
organization-scoped; the member session is not transferred into the Voting
Client. Frontend scope selection alone never establishes eligibility.

FRONT-02 may present and navigate approved existing organization projections but
must not claim that frontend implementation itself establishes, dissolves,
merges, reassigns members between, or changes the territorial/legal competence
of party bodies. Those are governed organization-lifecycle actions owned by the
relevant domain rules and authority.

Navigation must not imply a shared session or shared identity where the
architecture prohibits it. Critical functions must not become inaccessible
through hidden or inconsistent navigation.

## FIR-UX-005 — Interaction Patterns for Consequential Actions

- **Status:** `approved`
- **Scope:** submissions, decisions, approvals and other consequential acts
- **Target:** every relevant frontend and domain PACK
- **Dependencies:** FIR-FORM-001, FIR-RULE-001, FIR-TRUST-001

Establish common patterns for:

- preview before submission;
- explicit confirmation;
- step-up authentication where required;
- warning about consequences;
- immutable receipt;
- cancellation before final commit;
- stale-version and conflict handling;
- re-confirmation after object changes;
- clear distinction between `Speichern`, `Einreichen`, `Bestätigen`,
  `Freigeben` and `Abstimmen`;
- prevention of double submission;
- protection against misleading controls and dark patterns.

A frontend action must not imply completion before the authoritative backend
commit has succeeded.

## FIR-UX-006 — System States and Recovery Experience

- **Status:** `approved`
- **Scope:** all frontend journeys
- **Target:** every FRONT-PACK
- **Dependencies:** PACK-13, FIR-INCLUSION-001

Each user journey must explicitly design and test:

- loading;
- empty state;
- validation error;
- permission denied;
- expired session;
- stale data;
- partial outage;
- unavailable dependency;
- failed upload;
- interrupted submission;
- duplicate action;
- conflict;
- maintenance;
- retry;
- safe degraded mode;
- offline or alternative-channel fallback where applicable.

The interface must clearly state whether data was saved, submitted, rejected
or left unchanged, and what the user can do next.

## FIR-UX-007 — Content Design and Terminology Governance

- **Status:** `approved`
- **Scope:** German interface language and official terminology
- **Target:** content system, design system and all FRONT-PACKs
- **Dependencies:** FIR-FORM-004, FIR-REF-001

Maintain a governed terminology catalogue for recurring interface concepts,
including distinctions such as:

- Mitglied / Antragsteller / Nutzer;
- Antrag / Entwurf / Einreichung;
- Entscheidung / Beschluss;
- Einspruch / Widerspruch / Beschwerde / Berufung;
- Speichern / Absenden / Einreichen;
- gültig / beschlossen / in Beratung;
- Frist / Termin;
- Vertretung / Delegation.

Button labels, warnings, errors and status text must not contradict official
forms, rule sources or decision semantics. Important wording must not exist
only as hard-coded frontend copy.

### DE/EN frontend language presentation

All FRONT-PACKs must preserve DE/EN readiness. German (`de`) is the default
interface language and the semantic/authoritative reference for governed German
terminology. English (`en`) is a supported translation layer, not an independent
action taxonomy, route authority, identity context or legal/procedural authority.

The shared frontend shell must support a visible accessible `DE | EN` language
selector where both languages are offered. German canonical route paths remain
canonical; language selection changes the rendition only. Language preference
is non-authoritative host-local display state and must not be used for identity,
authorization, organization scope, eligibility or cross-workspace correlation.

Material English translations must be version-linked to the authoritative German
source and fail visibly to the current German rendition when translation is
missing, stale or unapproved. Consequential-action semantics, deadlines, consent
scope and legal effect must remain identical across language renditions.

## FIR-UX-008 — Responsive and Multi-Device Experience

- **Status:** `approved`
- **Scope:** all supported frontend surfaces
- **Target:** every FRONT-PACK
- **Dependencies:** FRONT-00 accessibility and visual baseline

Design and verify complete workflows for:

- mobile;
- tablet;
- desktop;
- wide desktop;
- keyboard-only use;
- screen readers;
- zoom and reflow;
- touch input;
- print where required.

Responsive implementation must preserve the whole task, not merely resize the
desktop layout. No required action, evidence or status may disappear on a
supported viewport.

## FIR-UX-009 — Visual Status and Decision Semantics

- **Status:** `approved`
- **Scope:** all public and authenticated status presentation
- **Target:** design system and all domain FRONT-PACKs
- **Dependencies:** FIR-REF-001, FIR-UX-003

Create common visual and textual semantics for:

- adopted;
- active;
- draft;
- in discussion;
- awaiting action;
- overdue;
- rejected;
- replaced;
- archived;
- confidential;
- restricted;
- under review;
- failed;
- unavailable.

Status must never be communicated by color alone. Text, iconography, shape,
placement and accessible description must work together.

For public programme presentation specifically:

- the adopted programme remains the dominant content;
- decision, version, authority, adoption method and effective date are shown;
- proposals are represented only through a secondary
  `Projekte in Beratung` card per thematic section;
- the card states `Noch nicht beschlossen`;
- full proposals open on separate pages;
- proposals must not visually resemble adopted programme text.

## FIR-UX-010 — Design Evidence and Frontend Acceptance

- **Status:** `approved`
- **Scope:** frontend delivery governance
- **Target:** every FRONT-PACK
- **Dependencies:** FRONT-00 acceptance baseline

Every FRONT-PACK must first assess the existing visual baseline and provide,
as applicable:

- inventory of existing FRONT-00/FRONT-01 components and page patterns;
- extraction of actual typography, spacing, color, border, radius and layout
  tokens;
- `reuse` classification for every existing affected pattern, and
  `extend-with-canonical-tokens` only where no existing component can express
  required new functionality;
- reference to an already approved Design Change Decision for any proposed
  replacement or visual-baseline modification; without that decision the
  replacement is prohibited;
- screenshot comparison against the approved FRONT-00/FRONT-01 baseline;
- user-flow map;
- information architecture;
- screen inventory;
- mobile, desktop and wide layouts;
- consequential-action states;
- loading, empty, failure and recovery states;
- keyboard-flow review;
- accessibility review;
- content and terminology review;
- visual regression fixtures;
- browser tests;
- acceptance screenshots;
- confirmation that frontend is not the security boundary.

A FRONT-PACK cannot claim full journey completion if it implements only the
successful desktop state.

### Canonical visual-baseline rule

Existing accepted FRONT-00/FRONT-01 pages, tokens, components and reference
screenshots are the **immutable visual baseline**, not merely a reference.
Ordinary FRONT-PACK work may add governed functionality and content but may not
visually improve, evolve, modernize or reinterpret the existing baseline.

A future FRONT-PACK must preserve exactly, where already established:

- typography hierarchy;
- spacing rhythm;
- page width and grid logic;
- navigation character;
- card and section treatment;
- restrained use of color;
- border and radius language;
- density and whitespace;
- status presentation;
- interaction tone.

Any departure from an established baseline element requires a separate
approved **Design Change Decision** before implementation. Documentation inside
the same implementation task, accessibility evidence alone, usability claims,
developer preference or a mockup do not authorize the departure. A candidate
with an unapproved visual-baseline change fails acceptance.

## FIR-UX-011 — Page Specification and Screen Content Governance

- **Status:** `approved`
- **Scope:** every user-facing public and authenticated domain
- **Target:** every relevant FRONT-PACK specification and UX/IA phase
- **Dependencies:** FIR-UX-003—010, FIR-FORM-001—005, FIR-RULE-001,
  FIR-REF-001

No user-facing domain may be considered fully designed until an approved Page
Specification Catalogue and Screen-State Matrix exist.

Before frontend implementation, each relevant FRONT-PACK must define the full
page sequence and navigation model, including:

- first page or entry screen;
- subsequent pages and decision points;
- branch conditions;
- return paths;
- cancellation paths;
- interrupted-process recovery;
- completion page;
- receipt or evidence page where applicable;
- links to related documents and decisions.

For every page or screen, the specification must include:

- stable page ID;
- route or route pattern;
- workspace and origin;
- purpose;
- target audience;
- source domain and authoritative data source;
- required permissions;
- authentication and assurance requirement;
- page position in the user journey;
- predecessor and successor pages;
- content blocks in display order;
- fields and source definitions;
- primary action;
- secondary actions;
- destructive or consequential actions;
- status and decision presentation;
- warnings and confirmations;
- evidence and receipt presentation;
- related forms and official documents;
- loading state;
- empty state;
- validation state;
- permission-denied state;
- stale-data state;
- partial-failure state;
- recovery state;
- completed state;
- mobile, tablet, desktop and wide-layout structure;
- keyboard and screen-reader behavior;
- governed terminology and exact content references;
- telemetry prohibition or approved minimized telemetry;
- acceptance screenshots and browser-test obligations.

### Required frontend specification artefacts

Each relevant FRONT-PACK must produce, as applicable:

- `PAGE-CATALOGUE.md`;
- `PAGE-SEQUENCE-MAP.md`;
- `NAVIGATION-MAP.md`;
- `CONTENT-MAP.md`;
- `ACTION-MAP.md`;
- `SCREEN-STATE-MATRIX.md`;
- `PERMISSION-AND-ASSURANCE-MATRIX.md`;
- `RESPONSIVE-LAYOUT-SPECIFICATION.md`;
- `ACCESSIBILITY-FLOW.md`;
- `ACCEPTANCE-SCREENSHOT-INVENTORY.md`.

### Responsibility split

- The domain PACK defines the process, authoritative data, permissions,
  forms, decisions and mandatory content.
- The corresponding FRONT-PACK defines the page order, screen structure,
  navigation, content hierarchy, responsive layout and interaction states.
- Governed content catalogues define exact wording for consequential labels,
  warnings, confirmations, errors and official notices.
- Frontend developers implement the approved specifications and must not
  invent missing process logic or consequential content.

### Timing rule

The complete first-page-to-final-page structure becomes visible during the
`FRONT-PACK Specification + UX/IA` stage, before frontend implementation.

A FRONT-PACK implementation candidate must not start until the page catalogue,
page sequence, wireframes, content map and state matrix are accepted.

### PASS blocking rule

A claimed complete user journey is a PASS blocker when:

- the first page is undefined;
- one or more subsequent pages are missing;
- navigation or branching is ambiguous;
- consequential content is invented in code;
- failure and recovery pages are absent;
- mobile or accessibility flows are incomplete;
- screenshots do not cover the approved page sequence.

## FIR-UX-012 — Public Transparency Information Architecture & Verification Surface

- **Status:** `approved`
- **Scope:** public `/transparenz` information architecture and its governed links into WS-10 transparency/publication
- **Target:** next governed FRONT-PACK that changes `/transparenz`; dynamic publication remains owned by WS-10 / the applicable publication and infrastructure rounds
- **Dependencies:** FIR-UX-003, FIR-UX-004, FIR-UX-007, FIR-UX-008,
  FIR-UX-009, FIR-UX-010, FIR-UX-011, FIR-FRONT-001, FIR-FRONT-002,
  FIR-PUB-001, FIR-PUB-002, FIR-PUB-003, FIR-REL-001, FIR-READY-001,
  FIR-INV-015, FIR-SEC-SECRET-001, FIR-VOTE-CRYPTO-001

### Purpose

The public EPD² transparency page must function as an intelligible verification
hub rather than as a flat list of unrelated links.

An ordinary visitor must be able to understand:

- what political and organizational information is published;
- what financial and governed-document information is available;
- which technical areas are implemented, verified, still under verification,
  or not released;
- where deeper technical evidence can be inspected;
- what Open Source means in practice;
- how technically qualified contributors can inspect or improve the public
  codebase.

The page is an explanatory and navigational public surface. It is **not** a
second source of domain truth and it is **not** a bypass around PACK-28 / WS-10
publication governance.

### Exact visual-baseline continuity

This requirement does **not** authorize a redesign.

The accepted FRONT-00 / FRONT-01 visual baseline and the existing public-site
template remain controlling under `FIR-UX-003`, `FIR-UX-010` and the
documentation-only exact frontend-baseline-continuity clarification.

For this page change:

- preserve the existing EPD² page template, header, footer, card language,
  spacing system, typography, button language and established visual character;
- do not introduce a new color system, dashboard aesthetic, gamification,
  ornamental status widgets, unrelated icon system, accordion system or a new
  card vocabulary merely for this page;
- semantic hierarchy may be improved with the existing visual primitives;
- any later visual replacement requires its own governed FRONT-PACK evidence
  and must not be inferred from this FIR.

### Required public information architecture

The public `/transparenz` page must group the existing subject matter into
three principal semantic sections:

1. `Politik & Entscheidungen`
   - Öffentliche Entscheidungsdokumentation;
   - Entscheidungsprotokolle;
   - Lobbying-Log;
   - Offener Abgeordnetentisch;
   - Mitglieder & Beteiligung.

2. `Finanzen & Dokumente`
   - Finanzen;
   - Dokumente & Versionen.

3. `Technologie & Civic OS`
   - KI-Protokolle;
   - EPD² Civic OS — Systemstatus;
   - Technische Prüfberichte;
   - Open Source & Code.

A final explanatory block, `So kannst du selbst prüfen`, must explain in
plain German what a non-technical visitor can verify and where a technically
qualified visitor may inspect deeper evidence.

### Consolidation and semantic distinctions

`Offener Quellcode`, `Was bedeutet Open Source?` and `Am Code mitarbeiten`
must be presented as one `Open Source & Code` area with subordinate actions,
rather than as three equal top-level topics.

`Öffentliche Entscheidungsdokumentation` and `Entscheidungsprotokolle` remain
distinct:

- the former concerns public decisions, votes, outcomes and published reasons;
- the latter concerns internal board/body decision records and their reasons.

The UI must not blur those two evidentiary classes.

### Plain-language first, evidence underneath

A visitor must not need software-engineering knowledge to understand the
meaning of a technical status.

Where technical evidence is exposed, the public presentation should provide:

1. a plain-language explanation of what was checked and why it matters;
2. the current governed status;
3. a link to the relevant report or evidence;
4. deeper technical identity/provenance information only as an additional
   layer.

Technical terms such as `SHA-256`, canonical baseline, release identity,
prompt hash or deployment attestation must not be presented without a
plain-language explanation where they are material to the public claim.

### System-status hard rule

The page must not convert implementation progress into a production-readiness
claim.

`FIR-INV-015 — No false production claims` remains controlling.

In particular, until the governed VCRYPTO-01 production selection,
independent-verification, legal/procedural and activation gates have passed,
the public system-status wording for secret electronic voting must remain
equivalent to:

`IN ENTWICKLUNG / NICHT FREIGEGEBEN FÜR GEHEIME WAHLEN`

A frontend-only state, CMS value, feature flag, administrative convenience or
ordinary CI result must not upgrade that claim.

### Publication boundary and approved renditions

Public transparency data must obey the existing PACK-28 / WS-10 publication
boundary.

The frontend must not directly render raw internal operational tables, raw
external submissions, confidential notes or unreviewed source-domain records.

Where dynamic data is used, the public surface must consume only governed
published projections / approved renditions produced through the applicable
review, minimisation, redaction, approval, versioning, correction and
withdrawal process.

For the Lobbying-Log specifically, raw intake or internal working material must
never be treated as public display data.

This FIR does not replace `FIR-PUB-001` through `FIR-PUB-003`; those entries
remain authoritative for publication-channel governance, integrity
verification and governed downstream consumption.

### Technical integrity claims

A public SHA-256 may be shown as an integrity identifier only for the object it
actually identifies.

A bare digest must not be described as proof that public GitHub source is
bit-for-bit identical to the software currently running in production.

Where a stronger source-to-runtime claim is made, it must be supported by the
existing release/deployment governance chain, including as applicable:

`source commit`
→ `controlled/verifiable build`
→ `artifact digest`
→ `approved deployment manifest / attestation`
→ `running release identity`

`FIR-REL-001`, `FIR-READY-001` and the existing publication-integrity
requirements remain controlling.

### AI-governance presentation

The KI-Protokolle area must prominently preserve the principle:

`Politische Verantwortung bleibt beim Menschen.`

Where an AI-generated summary or analysis is publicly exposed, its governed
provenance should identify, where applicable and available:

- prompt/system-prompt version;
- prompt/system-prompt hash;
- model/provider identity;
- model/configuration version;
- material parameters;
- referenced snapshot/context/source set;
- timestamp;
- review/audit status.

A prompt hash alone must not be described as guaranteeing deterministic
reproduction of an AI output.

### Finance presentation

The public financial area should identify the actual publication/update date of
the governed financial rendition/report.

No monthly, quarterly or other publication cadence may be invented in frontend
copy unless that cadence has been separately governed and is actually
operational.

### Open Source & Code

The combined Open Source area must provide, as applicable:

- the governed public source-repository link;
- a plain-language explanation of Open Source;
- a contribution path for developers and security researchers;
- a responsible security-reporting route.

Open Source must not be presented as synonymous with security, audit or
production readiness.

### Reference frontend handoff

The approved content/structure reference prepared on 2026-08-24 is:

`EPD2_FRONTEND_TRANSPARENZ_HANDOFF_0.1.zip`

SHA-256:

`45abc68598426d0d513e0ee1a622a453b1906f7177bc3d6236b8417b45bf076a`

This handoff is a frontend content/IA reference. It is not production
deployment evidence and does not itself move this FIR to `implemented`.

A later governed handoff may supersede it only by preserving history and
recording the superseding identity.

### Acceptance criteria

`FIR-UX-012` may move to `implemented` only when a governed frontend round
provides evidence that:

1. the requirement is present in the single canonical Master Future
   Implementation Register;
2. `/transparenz` uses the required semantic grouping or a formally governed
   superseding information architecture;
3. the accepted EPD² visual baseline is preserved unless a separately governed
   design change explicitly supersedes it;
4. Open Source subtopics are consolidated as required;
5. decision-documentation and internal-protocol semantics remain distinct;
6. plain-language explanations are available for material technical claims;
7. public system status does not make false production or legal-activation
   claims;
8. secret electronic voting remains fail-closed as not released until the
   applicable VCRYPTO and activation evidence exists;
9. dynamic transparency content reaches the UI only through governed public
   projections / approved renditions;
10. Lobbying-Log presentation cannot consume raw internal or raw external
    records directly;
11. AI-governance presentation preserves human political responsibility and
    does not overstate reproducibility;
12. release-integrity wording does not exceed the actual cryptographic and
    deployment evidence;
13. financial update wording reflects actual governed publication evidence;
14. external source-code links are identifiable as external while remaining
    within the accepted visual language;
15. responsive, accessibility, browser and screenshot evidence passes the
    applicable FRONT-PACK gates;
16. the implementation records the exact frontend handoff it used, or the
    governed superseding handoff;
17. canonical/external verification for the implementing frontend round passes.

## FIR-UX-013 — Global EPD² Identity Line

- **Status:** `approved`
- **Scope:** all public EPD² website pages
- **Target:** next governed FRONT-PACK touching the shared public header / public page shell
- **Dependencies:** FIR-UX-003, FIR-UX-010, FIR-UX-011, FIR-FRONT-001, FIR-FRONT-002

### Requirement

Every public EPD² webpage that displays the standard EPD² logo in the upper-left
header area must display the following permanent identity line directly beneath
that logo:

`Erste Partei Direkte Demokratie`

This is the official expansion of `EPD²` for the public website.

The line is a global identity element, not page-specific content.

### Placement

- directly beneath the `EPD²` logo;
- upper-left header area;
- present consistently on all public pages that use the shared public header;
- implemented through the shared header/page-shell component where technically
  applicable, rather than copied independently into every page.

### Visual continuity

This requirement does not authorize a redesign.

The identity line must use the existing EPD² visual language and must not:

- create a new logo;
- alter the existing EPD² mark;
- introduce a new color system;
- introduce a badge, ribbon, card or promotional device;
- materially increase header height beyond what is required for the short line;
- change unrelated header navigation, spacing, controls or responsive behaviour.

The text should remain visually subordinate to the logo while remaining legible.

### Consistency rule

The wording is fixed:

`Erste Partei Direkte Demokratie`

Alternative expansions, slogans or paraphrases must not replace it.

`Digitale Demokratie für Deutschland` or any other campaign/slogan text may
exist separately where otherwise governed, but it is not the expansion of
`EPD²`.

### Accessibility and responsive behaviour

The identity line must:

- remain readable at the supported responsive breakpoints;
- not overlap navigation or logo content;
- preserve keyboard/navigation behaviour of the existing header;
- satisfy the applicable contrast, zoom, reflow and screenshot/browser gates.

### Acceptance criteria

`FIR-UX-013` may move to `implemented` only when a governed frontend round
provides evidence that:

1. the shared public header/page shell contains the identity line;
2. the exact wording is `Erste Partei Direkte Demokratie`;
3. all public pages using the standard EPD² header inherit it consistently;
4. no page carries a conflicting EPD² expansion;
5. the existing logo and public visual baseline are preserved;
6. desktop and mobile layouts pass the applicable browser, visual and
   accessibility checks;
7. the implementation is covered by the applicable shared-header regression
   tests;
8. canonical/external verification for the implementing frontend round passes.

## Section 28 boundaries

These entries:

- preserve the established minimalist EPD² design direction;
- do not freeze every current component or pixel;
- preserve the accepted FRONT-00/FRONT-01 visual implementation as the
  canonical immutable baseline;
- freeze established visual tokens, component styling, geometry and page
  treatment by default; only a separate approved Design Change Decision may
  authorize a specific change;
- do not require implementation in PACK-13;
- do not change `CANON_VERSION`;
- are not covered by the external CI run for the PACK-13 implementation
  candidate;
- remain approved future obligations;
- require explicit treatment in later FRONT-PACK specifications, acceptance
  matrices, implementation candidates and FINAL PASS reports.

# 29. Open-source licensing, reuse and official-instance governance

EPD² is intended to be open-source civic infrastructure.

The intended licence for original EPD² software is:

```text
European Union Public Licence Version 1.2
SPDX-License-Identifier: EUPL-1.2
```

The selection is `EUPL-1.2` only. A future change to another version or
licence requires an explicit governed decision and legal compatibility review.

This licence choice is subject to final review by qualified legal counsel
before the first public source release. Until the repository contains the
approved licence text, notices and provenance records, no incomplete licence
statement may be presented as final legal activation.

## FIR-OSS-001 — EUPL-1.2 Project Licensing Baseline

- **Status:** `approved`
- **Scope:** original EPD² software and source-controlled software assets
- **Target:** repository licensing and first public source release
- **Dependencies:** legal review, copyright ownership verification,
  third-party dependency review

License original EPD² software under `EUPL-1.2`.

The implementation must include:

- the official EUPL-1.2 licence text in the repository root;
- `SPDX-License-Identifier: EUPL-1.2` in supported source-file headers or
  repository-standard SPDX metadata;
- copyright and contributor notices;
- a machine-readable licence declaration;
- package metadata aligned with `EUPL-1.2`;
- a `NOTICE` or equivalent attribution file;
- a public licensing policy;
- a release checklist preventing unlicensed publication;
- confirmation that all original code can legally be licensed by the project.

The project must not use an ambiguous statement such as “open source” without
identifying the applicable licence.

### Rights granted to downstream users

Subject to compliance with the EUPL-1.2, recipients may:

- use the software for any lawful purpose;
- study and inspect the source code;
- copy the software;
- modify it;
- run modified deployments;
- redistribute original or modified versions;
- use it commercially;
- provide services based on it.

These rights do not imply endorsement, certification, official EPD status,
access to EPD data, access to infrastructure secrets or authority to act on
behalf of EPD.

## FIR-OSS-002 — Source Availability for Network-Provided Modified Versions

- **Status:** `approved`
- **Scope:** EPD² deployments communicated or provided over a network
- **Target:** public release, deployment and distribution governance
- **Dependencies:** FIR-OSS-001

Document and enforce EUPL obligations applicable when the work or a derivative
work is distributed or communicated to the public, including network-provided
services.

A compliant deployment process must provide, as applicable:

- access to the corresponding source of the deployed derivative work;
- the applicable licence text;
- copyright and attribution notices;
- identification of modifications;
- build and installation information needed to exercise the licensed rights;
- source for project-controlled frontend, backend and protocol changes;
- a visible source-code notice from user-facing network services where legally
  required.

No deployment may falsely claim compliance while withholding modified
project-controlled source that must be provided under the licence.

## FIR-OSS-003 — Third-Party Licence and Dependency Compliance

- **Status:** `approved`
- **Scope:** all direct, transitive, vendored and generated dependencies
- **Target:** build, CI, release and SBOM governance
- **Dependencies:** PACK-13 contract evolution and dependency governance

Create a governed third-party licence compliance process covering:

- direct and transitive dependencies;
- frontend and backend packages;
- containers and base images;
- fonts, icons, media and datasets;
- generated code;
- vendored components;
- cryptographic libraries;
- build tools included in distributed artefacts.

Required controls:

- SBOM generation;
- licence inventory;
- compatibility review against `EUPL-1.2`;
- attribution generation;
- prohibited or review-required licence policy;
- dependency provenance;
- release blocking on unresolved licence conflicts;
- documented treatment of permissive, weak-copyleft and strong-copyleft
  dependencies;
- no assumption that a dependency is compatible merely because it is publicly
  available.

## FIR-OSS-004 — Contribution, Copyright and Provenance Governance

- **Status:** `approved`
- **Scope:** internal and external contributions
- **Target:** contribution workflow before accepting public contributions
- **Dependencies:** FIR-OSS-001

Define who owns or is authorised to license every contribution.

The contribution model must include:

- contributor sign-off through a Developer Certificate of Origin or another
  explicitly approved mechanism;
- contributor identity and provenance records;
- confirmation that contributions are original or properly licensed;
- no copying from incompatible or unknown sources;
- AI-assisted contribution disclosure and provenance policy;
- copyright notice rules;
- contribution review;
- retention of sign-off evidence;
- a process for removing or replacing code with defective provenance.

A Contributor Licence Agreement may be adopted only through a separate
governed decision. No CLA may silently grant broader relicensing rights than
contributors were clearly informed about.

## FIR-OSS-005 — Trademark, Name and Official Instance Separation

- **Status:** `approved`
- **Scope:** EPD² names, logos, visual identity and official-service claims
- **Target:** public release and deployment governance
- **Dependencies:** trademark and organizational governance

Open-source rights to the software do not automatically grant rights to:

- the EPD² name;
- EPD Plattform e.V. names;
- logos;
- official seals;
- official domains;
- certification marks;
- claims of endorsement;
- claims that a deployment is an official EPD service.

Define a separate trademark and naming policy.

Third parties may operate forks and modified deployments under the software
licence, but must not misrepresent them as official EPD² instances.

An official-instance policy must define:

- authorised domains;
- release provenance;
- signed release manifests;
- operator identity;
- certification or conformance status;
- security and legal activation status;
- rules for describing forks;
- mandatory removal or alteration of protected branding where required.

## FIR-OSS-006 — Open Verification, Reproducible Builds and Public Security Process

- **Status:** `approved`
- **Scope:** public trust and independently verifiable releases
- **Target:** future public releases
- **Dependencies:** CI, supply-chain security, incident response

Open-source publication must support meaningful independent verification, not
only source visibility.

Future public releases must provide, as applicable:

- reproducible or independently verifiable build instructions;
- signed release tags and manifests;
- source-to-binary provenance;
- public protocol and schema documentation;
- public test suites;
- public verification tools;
- vulnerability reporting instructions;
- coordinated disclosure policy;
- security advisories;
- release history and change logs;
- clear separation between public source and protected operational secrets.

Security through obscurity must not be treated as a primary control.
Publication must nevertheless exclude credentials, private keys, personal
data, protected evidence, live configuration secrets and exploit-sensitive
incident details whose temporary restriction is justified.

## Section 29 boundaries

These entries:

- select an intended open-source licence but do not themselves complete legal
  licensing;
- do not grant access to personal data, ballots, membership records or
  operational secrets;
- do not certify any fork as an official EPD² service;
- do not require publication of private keys or confidential records;
- do not change `REPOSITORY_VERSION`;
- do not change `CANON_VERSION`;
- require implementation, legal review and release evidence before a public
  source release may claim full compliance.

---

## PACK-18 — Integrated frontend workspaces, access boundaries and accessibility

**Repository `0.20.0`. Canon `0.8.0` unchanged. Implementation candidate.**

Ten workspaces and ten origins made checkable rather than documented: an
authoritative registry cross-checked against FRONT-00 at module load, complete
route ownership that fails closed on an unowned path, nine governed shell
classes, nine identity profiles, a seven-state default-deny authorization
boundary, an eleven-state activation model, a fail-closed voting handoff, a
separated frontend state model and a governed error catalogue.

**Evidence.** 193 first-party frontend checks (135 Node, 58 Vitest) including
56 accessibility checks, plus 30 Python repository governance checks that
assert the same invariants from outside the module graph. No workspace is
`ACTIVE`; WS-03 is `LEGALLY_INACTIVE`.

**Not evidenced.** Runtime origin isolation, real credential issuance, backend
availability, accessibility conformance, and any legal activation of digital
voting under German law. Fourteen open decisions were opened and none closed.

## PACK-20 — Party offices, appointments, terms and mandates

**Repository `0.22.0`. Canon `0.8.0` unchanged. Implementation candidate.**

Five separations made structural rather than documented: office designation
is not appointment, appointment is not acceptance, acceptance is not an
active term, an active term is not an unrestricted authority grant, and a
system role is not a legal or political mandate. Twenty-four governed record
types with no conversion between them, thirteen state machines with explicit
forbidden-transition fixtures, a ten-condition activation gate that returns
`None`, an authority derivation that stores nothing and is recomputed on
every ask, and an AST scan that fails the suite if any universal
office-holder boolean appears.

**Evidence.** One new leaf service (`services/office-mandate-service`,
461 tests), 124 repository governance checks, 55 frontend checks over four
routes on four existing workspaces, 125 governed reason codes, seventeen
contract schemas, and 24 carry-forward tests for the two PACK-19
corrections (`F-19-01` finality guard; three reserved candidacy deadline
kinds). Ten workspaces and ten origins unchanged; no route in the isolated
Voting Client workspace or origin.

**Not evidenced.** Not one rule of German party law is encoded: every legal
quantity — term length, re-election limit, quorum, threshold, cooling-off
period, acting-capacity maximum — is `None` or empty. No identity evidence
binds a handle to a person, no institutional body separation is modelled, no
production persistence exists, and four PACK-20 deadline kinds resolve while
being enforced nowhere. Twenty-four open decisions were opened and none
closed. No external legal, security or accessibility review has been
performed, and no conformance or certification claim is made.

## V22 governance maintenance record — Resilient trust, delegated regional issuance, recovery and immutable audit (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT stage is accepted or closed by this update. No provider, HSM/KMS, DID framework, distributed ledger or production trust topology is selected or activated.

**New FIR ID created:** `FIR-TRUST-002 — Resilient Trust, Delegated Regional Issuance, Recovery & Immutable Audit` — status `approved`, priority `critical`.

**Governed proposal artifact:**

- `docs/governance/EPD2_RESILIENT_TRUST_DELEGATED_REGIONAL_RECOVERY_AUDIT_MODEL_0.1.md`.

**Scope:** this update establishes a technology-neutral trust and resilience contract: central root/master keys remain protected and outside political/regional administration; bounded regional issuers may support continuity without receiving master keys or authority to escape scope; `OrganizationalAuthority` remains the authoritative source while signed runtime projections are short-lived derivatives; Security containment remains technical and cannot decide political office; quorum-loss/root recovery uses separate governance authorization, recovery custody, execution and independent review; immutable/WORM audit is externally anchored for high-impact evidence; RTO/RPO and regional autonomy windows must be explicitly adopted and rehearsed later rather than guessed now.

**Dependencies preserved:** `FIR-GOV-004`, `FIR-GOV-005`, `FIR-SEC-004`, `FIR-TRUST-001`, `FIR-INV-010`/OD-20 and `FIR-ROADMAP-007` remain in force and are not closed or superseded.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. Exact allocation among API-02…API-06 and later INFRA/OPS/CTRL/FRONT/SEC remains stage-contract governed.

## FIR-TRUST-002 — Resilient Trust, Delegated Regional Issuance, Recovery & Immutable Audit

**Status:** approved
**Priority:** critical
**Domain:** trust / authorization / regional resilience / key custody / recovery / audit
**Target:** organization/governance + API + service identity + INFRA + OPS + CTRL + FRONT + SEC + FINAL INTEGRATION

EPD² must provide a resilient trust architecture in which central root/master material is strongly protected without becoming the hot-path dependency for every ordinary regional action, while regional continuity cannot turn into autonomous privilege escalation.

### Hard invariants

- no political office, Bund role, Land role, regional admin or generic platform admin receives the central root/master key by organizational status;
- regional delegated trust is bounded by exact scope, purpose/audience, credential/assertion class, TTL, delegation depth and policy version;
- a Land/Kreis/Ort trust component cannot mint Bund, cross-Land, platform-root or voting authority;
- `OrganizationalAuthority` remains authoritative; a signed token/assertion is a short-lived runtime projection and cannot resurrect suspended/revoked authority;
- Security containment is technically capable of rapid quarantine/revoke but cannot appoint/remove political office, create organizational authority or take over a region;
- Identity/recovery cannot silently undo active security containment or restore separately suspended organizational authority;
- root/critical key custody uses key-class-specific threshold policy, not a universal superadmin and not a single hard-coded quorum for every key class;
- loss of ordinary key-custodian quorum has a separate governed recovery ceremony with post-recovery rotation and independent review;
- a Parteischiedsgericht may authorize/review recovery only where legally competent; it does not become a platform key custodian or HSM operator;
- high-impact audit/evidence is append-only/immutable and independently verifiable against an external anchor/trusted timestamp/countersignature; blockchain is not required;
- regional disconnected operation is time/freshness bounded and cannot silently become indefinite trust;
- RTO, RPO, autonomy and revocation/recovery objectives are required before production readiness but are not numerically invented by this FIR;
- voting-domain credentials/keys/trustees remain outside generic regional delegation and generic recovery.

### Required failure/recovery coverage

At minimum cover central HSM/KMS outage, network isolation/DDoS, key-custodian quorum loss, root/intermediate/regional issuer compromise, mass human-credential compromise, compromised Security operator, Identity outage, regional isolation, audit-pipeline/storage outage, trust-store corruption/rollback and stale distributed authority state.

Each runbook must identify detection, containment, permitted degraded operations, prohibited operations, recovery authority, technical recovery execution/ceremony, convergence, rotation/invalidation, evidence and independent post-review.

### Implementation placement

The detailed governed placement and acceptance matrix is defined by `docs/governance/EPD2_RESILIENT_TRUST_DELEGATED_REGIONAL_RECOVERY_AUDIT_MODEL_0.1.md`. Exact API-stage allocation remains stage-contract governed and this FIR does not pre-accept any API stage or select a production provider.

### Acceptance criteria

The FIR is complete only when the exact integrated accepted baseline proves bounded regional issuance without scope escape; safe degraded regional operation with tested autonomy/freshness limits; current-state refusal of stale/suspended authority; rapid technical containment without political takeover; threshold custody and rehearsed quorum-loss recovery; key/issuer compromise rotation with old-material rejection; independently anchored immutable audit; durable recovery evidence and post-review; and continued voting-domain isolation.

---

## V23 governance maintenance record — Cryptographic key classes, algorithm profiles and crypto-agility (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT stage is accepted or closed by this update. No HSM/KMS/PKI provider is selected or activated and no voting cryptographic profile is changed.

**New FIR ID created:** `FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility` — status `approved`, priority `critical`.

**Governed profile artifacts:**

- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.md`;
- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json`.

**Scope:** the generic EPD² platform now has a governed target crypto profile before API-02/API-03 closure: ES384/P-384 for generic root/intermediate/regional trust and high-impact audit signing; ES256/P-256 for short-lived authority and service JWS assertions; X.509/mTLS for workload identity; WebAuthn ES256 as the mandatory offered passkey baseline with scoped compatibility options; AES-256-GCM for EPD²-owned application/envelope data encryption; strict JOSE/JWKS typing/allow-list/key-ID/trust-location rules; explicit crypto-agility; and ML-KEM-768/ML-DSA-65 as inactive migration candidates rather than current defaults. Provider selection remains INFRA-owned.

**API sequencing refinement:** API-02 is already active and must reconcile the final accepted candidate with this profile before acceptance. API-03 PRE-SEAL development may continue, but API-03 C1 seal is blocked until its exact service-to-service credential/trust mechanism is reconciled with this V23 profile and onto the exact independently accepted API-02 bytes required by Program Control.

**Voting boundary:** PACK-16 voting cryptography, trustee/quorum rules and voting key ceremonies remain governed by the isolated voting domain and are not replaced by this generic profile.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

## FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility

**Status:** approved
**Priority:** critical
**Domain:** cryptographic trust / key classes / algorithm policy / runtime assertions / workload identity / data encryption / crypto-agility
**Target:** API + identity/session runtime + service identity + organization/governance + INFRA + OPS + CTRL + SEC + FINAL INTEGRATION; voting remains a separate domain profile

EPD² must use an explicit cryptographic class/profile registry rather than allowing each service, token, certificate or operator to choose algorithms ad hoc.

Core invariant:

```text
key class -> one purpose family -> one approved algorithm profile -> one custody profile
```

A key or valid cryptographic signature proves only the cryptographic statement defined by its profile. It never creates political, legal or organizational competence by itself.

### Generic platform baseline

- generic root/intermediate/regional trust: ECDSA P-384 + SHA-384 / `ES384`, X.509 v3 where PKI applies;
- short-lived `OrganizationalAuthority` runtime projections: JWS `ES256`, explicit `typ`, `iss`, `aud`, `exp`, `jti`, `kid`, authority/state freshness and exact scope/capability binding;
- short-lived service assertions where used: JWS `ES256` with exact service issuer/audience/environment/purpose and replay controls;
- workload identity: short-lived X.509 v3 mTLS leaf credentials, ECDSA P-256 baseline, TLS 1.3 preferred;
- human authentication: WebAuthn/passkey with ES256 as the mandatory offered baseline; EdDSA allowed where explicitly supported; RS256 compatibility-only;
- EPD²-owned data encryption: AES-256-GCM with unique nonce per key and versioned envelope keys; KEK held in HSM/KMS;
- high-impact audit/evidence signing: P-384/SHA-384 plus the V22 external anchor/timestamp/countersignature requirement;
- legal advanced/qualified signatures, seals and trusted timestamps: separately governed provider/eIDAS profile, not silently equated to the internal platform root;
- voting cryptography: excluded and unchanged under PACK-16/voting governance.

### Algorithm controls

Implementations must classify algorithms as `MANDATORY_BASELINE`, `ALLOWED_SCOPED`, `COMPATIBILITY_ONLY`, `MIGRATION_CANDIDATE` or `PROHIBITED` per use class.

At minimum:

- `alg=none` is prohibited for EPD² authorization/service/security assertions;
- generic HS* JWT authorization is prohibited;
- SHA-1/MD5, DSA, DES/3DES, RC4, ECB and new unauthenticated application CBC are prohibited;
- RSA-PKCS1-v1_5 signature profiles are compatibility/verify-only, not new generic issuer defaults;
- a key is bound to one algorithm and one purpose family;
- verifiers use exact allow-lists and never accept an algorithm because the untrusted artifact requested it;
- untrusted `jku`/`x5u` cannot select verifier trust locations;
- unknown `kid` fails closed after at most one refresh from the configured trusted issuer location.

### Key identifiers and lifecycle

Every new key version gets a new opaque `kid` with at least 128 bits of CSPRNG entropy. `kid` is never reused after rotation/revocation. RFC 7638 SHA-256 JWK thumbprint is stored separately as public-key fingerprint where JWK is used.

The registry must represent at least `GENERATED`, `STAGED`, `ACTIVE_SIGNING`, `VERIFY_ONLY`, `COMPROMISED`, `REVOKED`, `RETIRED` and `DESTROYED`. A compromised/revoked/retired/destroyed key never returns to signing-active state under the same ID.

### Initial generic cryptoperiod constraints

The governed profile artifact sets initial ceilings/targets by key class, including root <= 5 years, platform intermediate <= 12 months, regional issuer <= 90 days, runtime authority/service signer <= 30 days, authority assertion default 5 minutes/hard max 10 minutes, service assertion default 5 minutes/hard max 15 minutes, workload mTLS target <= 24 hours, audit signer <= 90 days and data KEK target <= 180 days. INFRA/SEC may shorten these. Lengthening a stated ceiling requires a governed profile revision/exception with security review.

Human passkeys are not force-rotated solely because of age; compromise, loss, assurance or policy events drive replacement.

### Crypto-agility and PQC

Consumers must support the governed migration sequence:

```text
CURRENT -> STAGED_NEXT -> DUAL_VERIFY -> NEW_ACTIVE -> OLD_VERIFY_ONLY -> RETIRED
```

Dual verification is bounded. Dual signing is prohibited by default unless a migration profile explicitly requires it. Downgrade to compatibility/prohibited algorithms fails closed.

`ML-KEM-768` and `ML-DSA-65` are recorded as `MIGRATION_CANDIDATE` only. No pure-PQ or hybrid activation is authorized by this FIR. The data model/trust registry must nevertheless be able to represent successor/hybrid profiles without architectural redesign.

### API gates

Before API-02 acceptance, its final candidate must reconcile passkey algorithm negotiation, any JWT/JWS helper/runtime artifacts, key ID handling, issuer/audience/expiry validation and current-state authorization with the V23 profile.

API-03 PRE-SEAL work may continue. API-03 C1 seal MUST NOT occur until:

1. authoritative API-02 is independently accepted;
2. API-03 is reconciled onto those exact accepted API-02 bytes;
3. the exact S2S mechanism selects only V23-approved workload mTLS and/or short-lived ES256 service assertion profiles;
4. trust generation, audience, replay, expiry, revocation and key-rotation behavior are demonstrated against the V23 profile.

### Provider boundary

V23 selects algorithms, formats and class semantics. INFRA selects concrete HSM/KMS/PKI/secret-manager/timestamp providers later and must prove non-exportability, generation, attestation, regional isolation, automation, revocation and recovery properties. Product branding is not acceptance evidence.

### Governing artifacts and acceptance

Detailed requirements, class table, format rules, JOSE/JWKS/X.509 profile, cryptoperiods, prohibited patterns, PQ migration boundary and acceptance criteria are governed by:

- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.md`;
- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json`.

This FIR is not complete until the integrated baseline proves class registration, algorithm allow-listing, custody/non-exportability, bounded cryptoperiod and rotation, stale/revoked rejection, regional scope confinement, data-encryption nonce/key safety, crypto-agile migration, audit independence and the API-02/API-03 gates without weakening the isolated voting domain.

# 29A. Authority Revalidation and Incremental Failure Assurance

## FIR-AUTH-001 — Consequential Commit Reauthorization & TOCTOU Protection

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** all consequential actions, especially asynchronous, queued,
  multi-step or long-running workflows
- **Target:** AUTH / domain services / AVH
- **Dependencies:** SoD rules, assurance model, scope isolation, state machines,
  FIR-TIME-001, idempotency/replay guarantees

An authorization decision is not automatically valid forever.

Hard invariants:

```text
authorization at request != authorization at consequential commit
queued authority != permanent authority
role visibility != current authority
```

Where authority, organization scope, assurance, policy version, legal-effect
profile or relevant object state can change between initial request and final
commit, the owning backend must revalidate at the consequential commit point.

Typical protected sequence:

```text
authorize
→ prepare
→ perform external/non-authoritative work if needed
→ revalidate authority + scope + assurance + policy + object state
→ commit authoritative effect
```

This applies especially to:

- voting/election administration;
- finance and payment approval;
- procurement/vendor activation and award decisions;
- appointments, mandates and office powers;
- publication;
- complaints/investigations;
- access grants;
- break-glass;
- queued jobs and delayed callbacks;
- deadline-sensitive actions.

The system must define when the original authorization may be bound into a
short-lived capability/transaction token and when fresh reauthorization is
mandatory. Such a token must be narrowly scoped, time-bounded and incapable of
outliving the authority it represents unless an explicitly governed rule says
otherwise.

### Required failure cases

Tests must cover at least:

- role revoked after request but before commit;
- authority term expired before commit;
- organization scope changed before commit;
- assurance downgraded or session invalidated;
- object state changed by a concurrent actor;
- legal/policy version changed before commit;
- queue delay crosses a deadline;
- break-glass window expires before side effect completion.

### Acceptance criteria

`FIR-AUTH-001` is complete only when:

1. consequential commit points are explicitly identified;
2. mutable authority/scope/state is revalidated where required;
3. stale queued work fails closed rather than inheriting old authority;
4. idempotent replay cannot bypass reauthorization rules;
5. tests prove revoke/expiry/change-between-check-and-commit behavior;
6. audit evidence records the authority basis actually used at commit.

## FIR-TEST-002 — Incremental Cross-Service Failure Fixtures

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** PACK-local and cross-service failure assurance during ongoing
  architecture construction
- **Target:** begin with current/future PACKs; accumulate into pre-Freeze
  system-wide challenge
- **Dependencies:** AVH, FIR-TEST-001, idempotency/replay guarantees,
  service contracts, deadline model

The system-wide adversarial challenge after PACK-35 must not be the first time
cross-service failure behavior is exercised.

Each new PACK that introduces a consequential external or cross-service
boundary should add realistic failure fixtures proportionate to its scope.

Representative patterns include:

- duplicate callback/event;
- delayed callback/event;
- out-of-order event;
- provider returns success after local state became invalid;
- local commit succeeds but external side effect fails;
- external side effect succeeds but acknowledgement is lost;
- retry after lost response;
- authority revoked while work is queued;
- deadline expires during processing;
- dependency unavailable;
- partial disposition/deletion failure;
- stale schema/policy/configuration at one side of a boundary;
- restore/replay after prior revocation or hold.

For PACK-25 specifically, suitable fixtures include:

- duplicate vendor/provider callback;
- callback after vendor suspension;
- external `SUCCESS` when internal state transition is not permitted;
- assessment revoked between approval and activation;
- contract expired while an activation/payment-related job is queued;
- provider unreachable after local commit;
- third-party deletion/disposition only partially completed.

These fixtures must use actual service/checker logic where practical rather
than only a separate oracle.

### Acceptance criteria

- every consequential new cross-service boundary has at least one negative or
  failure-path fixture;
- failure fixtures are deterministic and isolated;
- expected fail-closed/retry/reconcile behavior is explicit;
- new fixtures become part of cumulative assurance rather than being discarded
  after a PACK;
- `FIR-TEST-001` later reuses/extends this corpus for the system-wide challenge.

## Section 29A boundaries

These requirements:

- add no new business domain;
- do not require distributed transactions everywhere;
- do not force synchronous reauthorization where immutable capability semantics
  are explicitly governed and proven safe;
- do not expand PACK-25 scope beyond failure testing of boundaries it already
  introduces;
- do not replace the final system-wide adversarial campaign.

# 29B. Cross-Domain Identifier & Correlation Governance

### V12 strengthening of FIR-ID-001 — Cross-Domain Identifier & Correlation Governance

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** schemas, events, logs, traces, analytics, search, exports,
  support tooling, provider references and cross-domain data mappings
- **Target:** DATA / PRIVACY / SEC / AVH and all domain implementations
- **Dependencies:** trust-boundary registry, FIR-OPS-001, FIR-DATA-004,
  FIR-VOTE-NET-001, scope isolation and identity architecture

A natural person must not silently acquire one universal technical identifier
that is reusable across otherwise separated trust domains.

Hard invariants:

```text
same natural person != same technical identifier everywhere
technical join capability != authorized correlation
stable identifier reuse != legitimate purpose
```

### Required identifier classes

The architecture must distinguish at least:

- authoritative identity identifiers;
- domain-local subject identifiers;
- organization/scope identifiers;
- case/procedure identifiers;
- request/session correlation identifiers;
- audit/evidence identifiers;
- provider/external identifiers;
- anonymous/pseudonymous identifiers;
- voting/credential identifiers;
- export/search/index identifiers.

An identifier must have an explicit owner, purpose, scope and permitted
propagation path.

### Cross-domain rules

At minimum:

- prefer domain-local identifiers over universal person/member IDs;
- cross-domain identity mapping must occur only through an explicit governed
  mapping boundary;
- logs, traces and metrics must not become an alternate global identity
  registry;
- correlation IDs must normally be request/session scoped, not person scoped;
- analytics identifiers must not bridge otherwise isolated domains;
- search indexes must not join records across authority domains merely because
  the same person can technically be recognized;
- export formats must not introduce reusable universal identifiers unless the
  governed purpose explicitly requires them;
- support tooling must not gain cross-domain correlation powers absent domain
  authority;
- external provider IDs must not become internal master identity keys;
- any stable cross-domain join requires explicit purpose, authority, scope,
  retention and audit;
- identifier mapping tables are sensitive assets and require their own access,
  retention, export and disposition controls;
- identifier lifecycle must account for rotation, revocation, merge/split,
  correction and disposition where applicable.

### Voting boundary

Voting remains stricter than the ordinary domain model:

- no member/account/person identifier may accompany ballot submission;
- Voting Client identifiers must not be reversibly mapped to member identity
  through ordinary application or infrastructure data;
- any one-time eligibility/credential handoff must preserve the established
  Eligibility/Credential separation;
- no log, trace, analytics, provider or support identifier may create a
  backdoor identity-to-ballot join.

### Machine-readable identifier inventory

Before Architecture Freeze 1.0, EPD² must maintain or derive a machine-readable
inventory sufficient to answer:

```text
identifier
→ owning domain
→ semantic type
→ stability
→ person-linkability
→ organization scope
→ storage locations
→ event/API propagation
→ log/trace usage
→ search/index usage
→ export usage
→ provider exposure
→ allowed cross-domain mappings
→ retention/disposition
```

### Automated assurance requirement

Repository governance / AVH should include an automated
**Cross-Domain Identifier Correlation Check**.

The check should inspect, where machine-readable:

- canonical schemas;
- API/OpenAPI/JSON-schema contracts;
- event contracts;
- persistence models;
- logging/telemetry field registries;
- search/index mappings;
- export schemas;
- provider/gateway contracts;
- frontend/shared-client contracts where identifiers cross origins.

It should detect at least:

- the same stable person identifier appearing in multiple prohibited trust
  domains;
- identifier propagation into Voting Client or ballot contracts;
- persistent identifiers in logs/traces where only request-scoped correlation
  is allowed;
- provider IDs reused as internal master IDs;
- cross-domain mappings with no registered purpose/authority;
- new identifier-like fields absent from the identifier inventory;
- identifier aliases that bypass naming-only checks.

The checker must not rely only on field names such as `member_id`; it should
support a governed semantic annotation/registry so renaming an identifier does
not evade the control.

### Acceptance criteria

`FIR-ID-001` is complete only when:

1. identifier classes and owners are explicit;
2. prohibited cross-domain stable-ID reuse is machine-detectable;
3. permitted mappings are registered and auditable;
4. logs/search/analytics/exports/providers are included, not only primary
   databases;
5. Voting has no reversible identity/ballot identifier path;
6. AVH includes real positive and mutation/negative fixtures;
7. disposition/revocation covers mapping tables and derived copies;
8. every critical exception has explicit authority and purpose.

## Section 29B boundaries

This requirement:

- does not prohibit all cross-domain joins;
- does not require a single global identity service to disappear;
- prohibits silent/unregistered correlation power;
- adds no new business domain;
- does not expand PACK-25 beyond carry-forward governance and relevant vendor
  identifier discipline;
- must be enforced progressively and included in the pre-Freeze system-wide
  assurance challenge.

# 29C. Edge Governance, Runtime Readiness & Launch Control

## FIR-EDGE-001 — Origin, Ingress & Routing Policy Governance

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** frontend origins, ingress, API gateway, reverse proxy, CDN/WAF,
  security headers, cookies/storage, telemetry, logging and route policy
- **Target:** FRONT / INFRA / SEC / OPS / AVH
- **Dependencies:** FIR-FRONT-001, FIR-VOTE-NET-001, FIR-ID-001,
  FIR-OPS-001, FIR-REL-001

The multi-origin architecture must be enforced below the application UI layer.

Hard invariant:

```text
declared origin isolation != enforced ingress isolation
```

EPD² must maintain a versioned, machine-readable policy mapping at least:

```text
origin
→ allowed backend/service routes
→ authentication mode
→ assurance requirements
→ cookie/storage policy
→ CSP/CORS/security-header policy
→ telemetry/logging profile
→ identifier policy
→ WAF/DDoS profile
→ cache policy
→ allowed cross-origin handoffs
```

At minimum:

- no route may be exposed to an origin unless explicitly permitted;
- security headers must be generated/validated from governed policy rather than
  ad-hoc per deployment;
- cookies must not be widened across origins in ways that collapse trust
  boundaries;
- critical origins must not inherit shared telemetry or correlation identities;
- Voting Client routing must preserve FIR-VOTE-NET-001;
- gateway/reverse-proxy configuration must be versioned and reviewed;
- infrastructure routing changes must be traceable to a reviewed change;
- a configuration error must fail closed for protected routes;
- WAF/CDN policy must not create a hidden identity bridge between isolated
  origins;
- support/incident tooling must not bypass origin policy.

A shared monorepo, build toolchain or dependency package is not by itself a
violation. The violation is shared runtime state, authority, identifier,
telemetry or routing that crosses a prohibited trust boundary.

### Automated assurance

Repository governance / AVH should validate at least:

- unknown/unregistered origins;
- route exposure not declared in policy;
- shared cookie-domain expansion;
- forbidden CORS/CSP relaxation;
- forbidden telemetry/analytics on critical origins;
- Voting Client route to unauthorized backend;
- cross-origin identifier propagation;
- missing or stale gateway policy relative to deployed services.

### Gateway non-ownership boundary — V13 strengthening

See `FIR-API-001`; gateway/edge components may route and minimize metadata but may not own domain truth or execute domain decisions.

## FIR-READY-001 — Runtime Readiness, Compatibility & Stale-State Protection

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** service startup, rolling deployment, recovery, projections,
  migrations, key/policy/config readiness and traffic activation
- **Target:** INFRA / OPS / DATA / AUTH / AVH
- **Dependencies:** FIR-REL-001, FIR-DATA-004, FIR-TIME-001,
  FIR-CRYPTO-001, FIR-OPS-001, schema/event evolution rules

Hard invariants:

```text
process alive != service ready
service ready != authoritatively ready
port open != safe for consequential traffic
```

A component may start in any order, but it must not accept consequential work
until the dependencies and local state required for that work are ready.

Readiness must account, where applicable, for:

- database/schema migration completion;
- producer/consumer contract compatibility;
- loaded and valid policy/configuration versions;
- required key/certificate availability;
- trusted-time condition;
- dependency compatibility;
- read-model/projection generation and freshness watermark;
- event/broker position required for authoritative decisions;
- provider/gateway readiness where the operation depends on them;
- restore/recovery reconciliation completion;
- legal-effect profile availability where relevant.

Stale projections must not be treated as current authority merely because the
read-model process is running.

For consequential reads/actions:

```text
projection behind required authoritative position
→ NOT_READY / fail closed / explicit degraded mode
```

where the domain requires freshness.

### Launch Control Gate

Before production or other legally/operationally consequential traffic is
activated, the relevant deployment must establish evidence for:

```text
artifact provenance
+ deployment manifest
+ config/schema compatibility
+ trusted time
+ key readiness
+ dependency readiness
+ projection/read-model freshness
+ restore/reconciliation state
+ origin/ingress/routing policy
= LAUNCH GATE PASS
```

The gate may be scoped per service/workspace rather than requiring the entire
platform to start atomically.

### Acceptance criteria

- startup ordering is not relied upon as the sole safety mechanism;
- stale authority/read models cannot silently serve consequential decisions;
- readiness state is observable and machine-checkable;
- rolling deployment can distinguish compatible from incompatible mixtures;
- recovery does not reopen traffic before reconciliation is complete;
- launch activation has an auditable evidence record.

## Section 29C boundaries

These requirements:

- do not mandate one API gateway product;
- do not mandate all services share one release version or Git hash;
- do not require one rigid startup sequence;
- do not require separate source repositories for each origin;
- do require machine-enforced runtime boundaries and compatibility evidence;
- are mandatory preconditions for relevant production activation.

# 30. Cross-cutting Operational Assurance Foundations

These requirements cover the system properties that must remain true while
EPD² is built, released, operated, degraded, recovered, migrated and finally
decommissioned. They are not new business domains and must not be implemented
by weakening domain boundaries.

## FIR-CRYPTO-001 — Cryptographic Key, Secret & Trust-Anchor Lifecycle

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** cryptographic keys, secrets, signing roots, certificates,
  callback-verification keys, recovery material and trust anchors
- **Target:** SEC / INFRA / OPS workstreams, Voting integration and every
  provider-facing domain
- **Dependencies:** PACK-12, PACK-14, PACK-15/16, FIR-TRUST-001,
  FIR-SEC-003, FIR-REL-001

EPD² must govern the complete lifecycle of cryptographic keys and secrets:

```text
generate
→ approve
→ activate
→ use
→ rotate
→ suspend
→ revoke
→ compromise-response
→ recover
→ retire
→ destroy
```

At minimum:

- key ownership, purpose and permitted algorithms are explicit;
- key version is preserved with every consequential cryptographic act;
- highly privileged trust anchors use separation of duties / dual control;
- plaintext secrets are prohibited from source control, ordinary logs,
  analytics, exports and unprotected backups;
- production, test and development secrets remain separated;
- provider signing keys are provider-scoped and do not become universal EPD²
  trust anchors;
- Voting keys and credential material remain isolated from ordinary
  infrastructure keys;
- rotation must preserve verification of historical signatures where the
  procedure requires it;
- compromise of one key must not imply unrestricted compromise of unrelated
  domains;
- recovery keys and ordinary operational keys remain separated;
- revocation, compromise and destruction events are auditable;
- cryptographic agility permits governed replacement of algorithms without
  rewriting historical evidence.

A boolean such as `trusted_key=true` is not sufficient governance.

### Acceptance criteria

- every active key/secret has an owner, purpose, lifecycle state and version;
- revoked or expired material cannot authorize new consequential actions;
- historical evidence remains verifiable according to its recorded trust
  context;
- no universal secret spans otherwise isolated trust domains;
- key compromise has a tested containment and recovery path.

## FIR-TIME-001 — Authoritative Time, Clock & Temporal Evidence

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** deadlines, elections, sessions, mandates, contracts, retention,
  signatures, audit and time-dependent authorization
- **Target:** INFRA / OPS / trust foundation and all consequential domains
- **Dependencies:** FIR-DATA-002, FIR-TRUST-001, FIR-CONFIG-001

EPD² must distinguish machine clock readings from authoritative procedural or
legal temporal evidence.

Hard invariant:

```text
system clock != legal/procedural time evidence
```

The architecture must define:

- authoritative clock sources;
- UTC handling and explicit local time zone;
- daylight-saving-time transitions;
- maximum tolerated clock skew;
- monotonic time for elapsed-duration logic where wall-clock rollback would
  be unsafe;
- timestamp provenance;
- trusted timestamp use where a procedure requires it;
- behaviour when clock trust is lost;
- detection of backward jumps and material forward jumps;
- reconciliation after time-service restoration;
- exact time basis used for deadline calculations.

Unknown or materially unreliable time must fail closed for actions whose
validity depends on exact time, rather than silently using a local clock.

### Acceptance criteria

- consequential timestamps identify their time basis/provenance;
- deadline computation is deterministic and testable around DST and clock
  changes;
- clock rollback cannot reopen an expired privilege or closed procedure;
- loss of trusted time has a governed degraded/fail-closed behaviour;
- audit chronology can distinguish event order from wall-clock assertions.

## FIR-OPS-001 — Privacy-Safe Observability, SLO & Operational Health

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** health, metrics, tracing, alerts, service dependencies, queues,
  capacity and operational ownership
- **Target:** OPS / INFRA workstreams and all deployed services
- **Dependencies:** FIR-SEC-001, FIR-DATA-001, FIR-METRIC-002,
  FIR-FRONT-003/005 where mobile telemetry is involved

EPD² must be observable enough to detect failure without turning observability
into surveillance.

Hard invariant:

```text
observability != surveillance
debugging != authorization to read domain data
```

The operational model must define:

- service health and dependency health;
- SLI/SLO and error-budget policy where appropriate;
- queue lag and backpressure indicators;
- alert ownership and escalation;
- on-call responsibility;
- capacity and saturation indicators;
- trace and correlation identifiers that do not become global person IDs;
- privacy-safe diagnostic events;
- controlled diagnostic elevation for incidents;
- retention and access policy for operational telemetry.

Ordinary observability must exclude, unless a narrowly governed exception is
explicitly approved:

- ballot/vote content or linkable voting identifiers;
- protected reporter identity or submission content;
- message/document bodies;
- credentials, tokens, keys and secrets;
- detailed finance data;
- protected identity evidence;
- unnecessary member/person identifiers.

The Voting Client requires its own minimized observability profile consistent
with its isolation requirements.

### Acceptance criteria

- important outages and degradation are detectable from permitted telemetry;
- telemetry fields have a governed purpose and retention;
- an operator cannot gain domain-content access merely by enabling tracing;
- no global correlation key emerges from monitoring;
- incident diagnostics have an auditable escalation path.

## FIR-REL-001 — Release, Deployment & Environment Integrity

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** source-to-build-to-artifact-to-deployment provenance
- **Target:** release engineering / INFRA / OPS
- **Dependencies:** FIR-OSS-003, FIR-OSS-006, FIR-CONFIG-001,
  FIR-SEC-002, PACK-13

EPD² must preserve the identity of an independently verified source state
through build, release and deployment.

Required separation:

```text
development != test != staging != production
```

At minimum:

- production secrets and authority are unavailable to ordinary development and
  test environments;
- a verified artefact is promoted between environments rather than silently
  rebuilt with different inputs;
- source commit, dependency lock state, build provenance, artifact digest,
  configuration version, database/schema migration set and deployed release
  are traceable;
- releases and manifests are signed or otherwise independently verifiable;
- production deployment requires governed authorization;
- rollback and roll-forward paths are defined and tested;
- incompatible schema/configuration deployment fails closed;
- production hotfixes must return to repository history and normal review;
- configuration drift and unauthorized binary drift are detectable;
- emergency deployment has its own constrained, audited workflow;
- deployed version and activation state are always discoverable.

A green repository CI run does not by itself prove the deployed environment
matches the verified artifact.

### Rolling compatibility and deployment manifest

EPD² must support controlled mixed-version windows during rolling deployment.

The required rule is not “all services must run the same Git hash”. Instead,
every deployed component must have an exact artifact identity and participate
only in a declared compatible combination.

A governed deployment manifest should bind, at minimum:

```text
service/component
→ artifact digest
→ source revision
→ dependency lock/provenance
→ schema/event contract version
→ configuration version
→ environment
→ activation state
```

Schema/event evolution must follow an explicitly compatible migration pattern,
for example:

```text
expand
→ deploy compatible writers
→ deploy compatible readers
→ switch behavior
→ contract/deprecate
```

A deployment must fail closed when a producer/consumer, schema, configuration
or migration combination is outside the declared compatibility matrix.

### Integrated deployment identity hard gate — V13 strengthening

For every staging or production integrated contour:

```text
running component set == one approved immutable deployment manifest
```

The manifest must bind, as applicable:

```text
component/service
→ exact artifact digest
→ source revision
→ dependency-lock/provenance identity
→ schema/event/API contract versions
→ migration set
→ configuration version
→ frontend artifact digest
→ infrastructure/runtime profile
→ activation state
```

CI/CD and launch control must fail closed when the actual deployed set does not
match the approved manifest.

Accidental heterogeneous versions are prohibited. Deliberate rolling or
mixed-version operation is permitted only when an explicit compatibility
matrix has been declared and tested beforehand. Absence of compatibility
evidence means the mixed-version combination is not deployable.

This is intentionally stronger and more accurate than requiring one Git hash
for every service: independently versioned artifacts may coexist only as an
approved compatible set, never as an accidental mixture.

### Acceptance criteria

- every production deployment resolves to an exact verified artifact digest;
- no environment can silently use a different dependency/configuration set;
- rollback preserves history and evidence;
- emergency release cannot bypass audit and subsequent reconciliation;
- source-to-running-instance provenance is independently checkable.

## FIR-DATA-004 — Data Disposition Propagation & Derived-Copy Governance

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** authoritative records, replicas, projections, indexes, caches,
  exports, backups, analytics copies and third-party copies
- **Target:** DATA / OPS / domain implementations
- **Dependencies:** FIR-DATA-003, FIR-QUALITY-001, PACK-11, PACK-12,
  PACK-13, FIR-SEC-003

Hard invariant:

```text
deleted from source != deleted everywhere
```

Every governed correction, access revocation, retention disposition or
deletion must account for derived and external copies.

The architecture must inventory, where applicable:

- authoritative source;
- replicas;
- read models/projections;
- search indexes;
- caches;
- exports;
- analytical copies;
- backups;
- provider-held copies;
- offline/printed evidence where governed.

Disposition workflows must define:

- propagation targets;
- invalidation and purge behaviour;
- legal-hold blocking;
- backup treatment;
- provider notification and confirmation;
- evidence of completed or incomplete propagation;
- minimum tombstone/audit evidence that remains after disposition;
- reconciliation of failed propagation;
- treatment of restored backups so disposed data does not silently reappear.

Deletion confirmation by an external provider is evidence, not automatic proof
of every legal or technical disposition obligation.

### Restore activation gate

A successful source-database restore does not by itself make the system safe
to reopen.

Before authoritative traffic is re-enabled after restore, the recovery process
must establish, where applicable:

```text
restore authoritative source
→ replay/reconcile authoritative events
→ reapply revocations
→ reapply legal holds
→ reapply dispositions/deletions
→ restore current key/trust state
→ rebuild projections/read models
→ rebuild or invalidate search indexes/caches
→ verify freshness and consistency
→ readiness proof
→ traffic activation
```

The exact implementation may vary by domain, but stale derived state must not
be exposed merely because infrastructure is reachable.

### Acceptance criteria

- the system can identify known derived-copy locations for governed data;
- access revocation propagates to indexes/caches and does not wait for ordinary
  expiry when immediate withdrawal is required;
- legal hold prevents destructive propagation;
- restored backups reapply disposition history before serving data;
- incomplete third-party disposition remains visible and owned.

## FIR-RES-001 — Capacity, Overload & Graceful Degradation

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** overload, denial-of-service resilience, peak-event capacity and
  degraded operation
- **Target:** INFRA / OPS / SEC and high-load domain workstreams
- **Dependencies:** FIR-INV-006, FIR-SEC-001, FIR-OPS-001,
  FIR-SEC-002

Hard invariant:

```text
degraded mode != weakened invariant
```

The system must define overload behaviour before production activation,
including:

- rate limits;
- admission control;
- queue bounds and backpressure;
- dependency timeouts;
- circuit breakers;
- retry budgets;
- load shedding;
- capacity targets;
- peak-event testing;
- fair-use protections;
- prioritization of critical operations;
- safe read-only or unavailable modes where appropriate.

Overload must never justify disabling:

- authorization;
- separation of duties;
- Voting Client isolation;
- audit requirements;
- idempotency/replay safety;
- legal hold;
- sensitive-data protections;
- no-intermediate-tally guarantees.

### Acceptance criteria

- critical services have measured peak-capacity and saturation tests;
- dependency failure cannot trigger unbounded retry storms;
- overload cannot create duplicate consequential actions;
- degraded mode has explicit user-visible semantics;
- recovery from overload does not lose or silently reorder authoritative work.

## FIR-LIFE-001 — Service, Contract & Provider Decommissioning

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** internal services, APIs, schemas, algorithms, providers,
  integrations and frontend surfaces
- **Target:** architecture / DATA / INFRA / OPS / provider governance
- **Dependencies:** PACK-13 contract evolution, FIR-SEC-003,
  FIR-DATA-004, FIR-REL-001, PACK-25 vendor-exit lifecycle

EPD² must govern end-of-life as a lifecycle rather than deleting a service or
provider when it is no longer wanted.

Minimum lifecycle:

```text
inventory
→ dependency analysis
→ migration plan
→ compatibility window
→ data/evidence preservation
→ consumer migration
→ access and credential revocation
→ data disposition
→ shutdown
→ post-shutdown verification
```

The process must address:

- APIs and event contracts;
- data ownership and migration;
- retention/legal hold;
- provider/export obligations;
- certificates, secrets and credentials;
- frontend routes and deep links;
- monitoring and alerts;
- outstanding jobs and messages;
- historical verification;
- documentation and service catalogue;
- rollback during the migration window.

Deprecated identifiers, reason codes or schema meanings must not be silently
reused.

### Acceptance criteria

- no service/provider is shut down without dependency evidence;
- historical records remain interpretable after implementation removal;
- credentials and external access are revoked;
- data disposition and legal hold are reconciled;
- obsolete routes/contracts fail explicitly rather than being silently
  repurposed.

## FIR-TEST-001 — System-Level Failure & Adversarial Assurance

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** cross-service failure injection, adversarial scenarios,
  recovery and system-wide invariant verification
- **Target:** continuous assurance plus mandatory system-wide challenge after
  PACK-35
- **Dependencies:** AVH, FIR-SEC-001, FIR-SEC-002, FIR-REL-001,
  FIR-OPS-001, FIR-RES-001, FIR-CTRL-001

Component and PACK-level tests are necessary but are not sufficient evidence
for system safety.

The system-wide assurance programme must exercise realistic cross-boundary
failures, including at least:

- identity service unavailable during a consequential procedure;
- stale authorization or scope information;
- duplicated/delayed/out-of-order events;
- lost response followed by idempotent retry;
- database failover between authorization/check and commit;
- network partition;
- external provider compromise or false-success signal;
- cryptographic key compromise and rotation;
- trusted-clock loss or rollback;
- corrupted or incomplete backup and restore;
- failed disposition propagation;
- overloaded queue / retry storm;
- schema migration rollback;
- partial deployment/configuration drift;
- incompatible-role collusion attempts;
- Bund/Land/Kreis scope confusion;
- Voting isolation crossover attempts;
- emergency/break-glass misuse;
- restoration from a stale environment snapshot.

Tests must verify system properties and invariants, not only availability.

### Mandatory architecture-closure placement

After PACK-35 and CTRL-01:

```text
completed domain architecture
→ CTRL-01
→ system-wide adversarial/failure challenge
→ corrective closure
→ Architecture Baseline 1.0 / Freeze
```

The challenge must produce machine-readable findings, reproducible fixtures
where practicable, independent verification evidence and a clear distinction
between:

- verified;
- limited/unproven;
- failed;
- not applicable.

### Acceptance criteria

- critical cross-service invariants are exercised under failure, not only
  happy-path operation;
- discovered failures result in corrective closure rather than waivers hidden
  in documentation;
- accepted limitations are explicit and owned;
- Architecture Baseline 1.0 / Freeze is blocked by unresolved critical
  system-level findings.

## Section 30 boundaries

These entries:

- are cross-cutting future obligations, not new party/business domains;
- do not change the accepted PACK-24 baseline;
- do not require PACK-25 to implement production infrastructure;
- do not change `CANON_VERSION`;
- must be preserved in every cumulative candidate beginning with PACK-25;
- may be implemented incrementally by later SEC, DATA, INFRA, OPS and
  architecture-closure workstreams;
- must not be marked implemented merely because a reference interface or test
  seam exists.

# 31. Voting Infrastructure Unlinkability and Legal-Effect Activation

## FIR-VOTE-NET-001 — Network & Infrastructure Unlinkability for Voting

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** WS-03 Voting Client, ingress, reverse proxy, CDN/WAF, TLS,
  network telemetry, tracing, timing metadata and operational observability
- **Target:** Voting architecture, SEC / INFRA / OPS workstreams, pre-Freeze
  system-wide adversarial challenge
- **Dependencies:** FIR-INV-002, FIR-INV-003, FIR-INV-004, FIR-OPS-001,
  FIR-CRYPTO-001, PACK-15/16

Application-layer origin isolation is necessary but not sufficient for
identity/ballot unlinkability.

Hard invariant:

```text
application-layer unlinkability != infrastructure-layer unlinkability
```

EPD² must model and mitigate correlation risks created by infrastructure
metadata, including where applicable:

- client IP address;
- source network / ASN information;
- TLS/session metadata;
- reverse-proxy or load-balancer identifiers;
- CDN/WAF request identifiers;
- precise request timestamps;
- request sizes and timing patterns;
- browser/network metadata available to infrastructure;
- shared trace or correlation IDs;
- shared operational logs;
- shared anti-abuse identifiers;
- provider-side telemetry.

### Mandatory boundaries

The Voting Client and its ballot-submission path must have an infrastructure
profile that is independently reviewed from ordinary authenticated traffic.

At minimum:

- Voting ingress must not inherit a reusable member/account/session identifier;
- no ordinary application correlation ID may cross into or out of WS-03;
- no person/member/account identifier may be written into voting proxy,
  CDN/WAF, network or tracing logs;
- infrastructure observability for voting must be purpose-minimized and
  separately governed;
- shared tracing across Member Core and Voting Client is prohibited;
- IP-address retention must be minimized or eliminated to the extent required
  by the approved threat model and operational/security obligations;
- timestamps and request metadata must be assessed for practical
  re-identification risk;
- infrastructure operators must not gain a trivial ability to correlate a
  one-time voting handoff with a specific ballot submission;
- DDoS/WAF controls must preserve unlinkability and must not introduce a
  persistent cross-origin user identifier;
- return from Voting Client must carry only the already permitted terminal
  status and must not expose ballot identifiers or correlation tokens.

### Traffic-correlation threat model

The voting threat model must explicitly analyse an adversary who can observe
one or more of:

- ordinary authenticated ingress;
- voting ingress;
- reverse-proxy/CDN/WAF logs;
- network timing;
- infrastructure traces;
- provider telemetry.

The model must distinguish:

```text
possible correlation
practical correlation
high-confidence correlation
proven unlinkability property
```

Claims of anonymity or unlinkability must not exceed the evidence.

### Mitigation selection

This requirement deliberately does **not** mandate one specific mechanism.

The approved architecture may consider, as justified by the threat model:

- ingress separation;
- privacy-preserving relays;
- batching;
- timing decoupling;
- traffic shaping;
- queueing;
- metadata reduction;
- log suppression;
- cryptographic mix networks;
- other independently reviewed techniques.

A mechanism such as a mixnet, batching layer or browser `Clear-Site-Data`
policy must be adopted only when the threat model and implementation review
justify it. No single browser header is sufficient evidence of
infrastructure-level unlinkability.

### Browser/storage hygiene

Existing Voting Client isolation remains mandatory:

- separate origin;
- no shared cookies;
- no shared localStorage;
- no shared IndexedDB;
- no shared Service Worker;
- no shared analytics;
- no shared telemetry;
- no persistent member identifier;
- one-time purpose-scoped handoff only.

Additional browser cache/storage-clearing controls may be used as defence in
depth, but they must not be presented as a substitute for network-layer
unlinkability.

### Acceptance criteria

`FIR-VOTE-NET-001` is complete only when:

1. the voting infrastructure threat model includes network/metadata
   correlation;
2. Member Core and Voting ingress have no shared persistent identity or trace
   identifier;
3. infrastructure logging fields are explicitly governed and tested;
4. no ballot submission carries a member/account identifier;
5. practical temporal-correlation attacks are independently tested;
6. DDoS/WAF/CDN protections do not create a cross-origin identity bridge;
7. any remaining correlation risk is explicitly classified and accepted or
   corrected;
8. production activation of voting is blocked until independent evidence
   supports the claimed unlinkability level.

## FIR-LEGAL-001 — Procedural Legal-Effect Activation Gate

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** every legally or procedurally consequential domain
- **Target:** cross-cutting governance/rules foundation and all domain
  activation gates
- **Dependencies:** FIR-RULE-001, FIR-TRUST-001, FIR-DATA-002,
  FIR-INV-015, FIR-CONFIG-001

EPD² must represent technical implementation and legal/procedural effect as
separate states.

Hard invariants:

```text
implemented != legally activated
online capability != legally permissible procedure
technical result != legal effect
provider/evidence success != legal effect
vote result != legally effective decision
```

No backend state transition may create legal or procedural effect merely
because a technical workflow completed successfully.

### Legal Effect Profile

Every domain capable of producing a consequential outcome must reference an
explicit governed Legal Effect Profile for the exact procedure.

The profile must be versioned and contain, at minimum:

- procedure type;
- jurisdiction / applicable organizational level;
- competent authority;
- organization scope;
- rule/policy version;
- legal or procedural basis reference;
- permitted channel(s);
- required identity/authentication/signature assurance;
- required quorum/majority or equivalent decision rule where applicable;
- required evidence;
- effective-from / effective-until;
- activation decision and authority;
- limitations / exceptions;
- fallback procedure;
- review date;
- status.

Minimum status model:

```text
OPEN
NOT_ACTIVATED
ACTIVATED
SUSPENDED
EXPIRED
```

Unknown, missing, expired or contradictory activation evidence must fail
closed for automatic legal/procedural effect.

### Separation of facts

The implementation must preserve the distinction between:

- technical completion;
- evidence collection;
- internal decision;
- publication;
- service/delivery;
- entry into force;
- legal/procedural effectiveness.

For example:

```text
ballot closed != legally effective election
provider callback succeeded != legal settlement
document signed != competent-authority approval
message delivered != legally sufficient service
selection recorded != legally binding procurement award
```

### No hard-coded broad legal conclusions

The system must not encode unsupported universal propositions such as:

```text
all online party elections are valid
all online party elections are invalid
all electronic signatures create the same legal effect
all provider confirmations are legally sufficient
```

Legal/procedural applicability must be attached to the exact governed profile,
time, jurisdiction, procedure and evidence set.

### Change and suspension

A Legal Effect Profile change:

- must be versioned;
- must not rewrite historical outcomes;
- must identify its competent approving authority;
- may suspend future legal-effect generation without deleting technical
  capability;
- must define treatment of in-flight procedures;
- must be auditable.

Feature flags or ordinary configuration must not activate legal effect unless
the corresponding governed profile is valid and active.

### Acceptance criteria

`FIR-LEGAL-001` is complete only when:

1. every consequential domain has either an active Legal Effect Profile or an
   explicit `NOT_ACTIVATED/OPEN` state;
2. technical success alone cannot create legal effect;
3. legal-effect generation fails closed on missing/expired/unknown profile;
4. historical decisions retain the exact profile version applied;
5. activation and suspension require competent governed authority;
6. tests prove that provider success, technical completion and frontend state
   cannot bypass the gate;
7. user-facing status distinguishes technical completion from legal or
   procedural effectiveness where the distinction matters.

## FIR-VOTE-CRYPTO-001 — Production Secret-Ballot Cryptographic Protocol Selection & Verification

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** production secret-ballot protocol, credential-to-ballot boundary,
  tally/publication verification, privacy and coercion/correlation threat model
- **Target:** Voting architecture evaluation before PACK-30; implementation and
  closure during PACK-30–35; mandatory blocker before Architecture Baseline 1.0 / Freeze
- **Dependencies:** PACK-15/16, FIR-VOTE-NET-001, FIR-CRYPTO-001,
  FIR-TIME-001, FIR-TEST-001, FIR-TEST-002, FIR-LEGAL-001

PACK-15/16 establish the application-level voting trust boundaries and
unlinkability invariants, but do not by themselves constitute final production
selection of a secret-ballot cryptographic protocol.

Hard requirement:

```text
reference voting architecture != production cryptographic protocol acceptance
```

Before production activation, EPD² must perform a governed protocol-selection
and verification programme grounded in an explicit threat model. It must not
select a mechanism merely because it is fashionable or easy to integrate.

The evaluation must demonstrate, at minimum:

- eligibility without identity-to-ballot linkage;
- uniqueness / resistance to duplicate valid voting;
- ballot secrecy and practical unlinkability;
- end-to-end or independently checkable verifiability appropriate to the chosen
  protocol;
- no intermediate tally disclosure;
- clear credential issuance/use/revocation semantics;
- failure, recovery and disputed-publication behaviour;
- infrastructure-correlation analysis together with `FIR-VOTE-NET-001`;
- compatibility with the separate Voting Client origin and one-time handoff;
- independent cryptographic review and adversarial test evidence.

The governed shortlist may consider families such as blind signatures,
anonymous credentials, mixnets, homomorphic tally, zero-knowledge proofs or
hybrid constructions, but this FIR deliberately prescribes none of them in
advance.

**Mandatory VCRYPTO-01 Entry Gate (V14):** Before any candidate primitive or
hybrid protocol may enter implementation evaluation, it must satisfy the
formal protocol-selection and adversarial-security gate in sections
`1.59.1`–`1.59.12`. Those sections are normative for this FIR. In particular,
ordinary possession of an election Guardian threshold before the governed
release condition must not itself create usable decryption authority, and
intermediate-tally prevention must be a property of the cryptographic
construction rather than cooperative application behaviour.

### Required decision artifacts

At minimum:

1. formal threat model;
2. comparison of at least two plausible protocol families unless only one
   remains defensible after documented elimination;
3. ADR selecting or rejecting the production profile;
4. proof/evidence mapping for Eligibility, Uniqueness, Secrecy/Unlinkability
   and Verifiability;
5. network/infrastructure correlation analysis;
6. independent review record;
7. failure/recovery/adversarial fixtures;
8. production activation blocker until the verification gate passes.

### Acceptance criteria

`FIR-VOTE-CRYPTO-001` is complete only when the selected production profile is
versioned, independently reviewed, implemented without persistent identity in
the ballot path, exercised against the approved threat model, and its remaining
limitations are explicit. A green repository CI run alone is insufficient.

## FIR-API-001 — API Gateway / BFF Non-Ownership & Domain-Logic Prohibition

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** future Production API Gateway / BFF, ingress composition layer and
  frontend-facing integration boundary
- **Target:** API-01 / EDGE / FRONT integration workstream before production
- **Dependencies:** FIR-EDGE-001, FIR-AUTH-001, FIR-REL-001,
  FIR-READY-001, bounded-context ownership established by PACK-01+

The Production API Gateway / BFF must remain a transport/integration boundary.
It must never become a convenience monolith that silently re-implements the
business system.

Hard invariants:

```text
API Gateway / BFF != bounded context
API Gateway / BFF != domain source of truth
transport authorization enforcement != ownership of authorization truth
frontend convenience != permission to duplicate domain logic
```

Permitted responsibilities include:

- routing and origin enforcement;
- protocol adaptation;
- request/response shaping;
- transport-level rate/size/format controls;
- metadata/identity minimization and redaction;
- composition of already-authorized read models;
- forwarding governed authentication/authorization context without becoming
  its source of truth.

Prohibited responsibilities include:

- owning authoritative domain state;
- implementing domain state machines or transitions;
- deciding domain eligibility or policy outcomes;
- recreating service authorization logic as an alternative authority;
- calculating or persisting voting/tally/finance/procurement/casework or other
  domain outcomes;
- shadow persistence that can diverge from a domain service;
- bypassing a service-owned hard invariant because a frontend flow is easier
  to implement in the gateway.

### Mechanical enforcement target

API-01 must add checker/test coverage that can detect at least:

- forbidden gateway dependencies on domain implementation modules;
- state-machine/domain-decision code located in the gateway package;
- persistence owned by the gateway for domain truth;
- action mappings that terminate in the gateway instead of the owning service;
- protected-read or consequential-write bypass through the BFF.

### Acceptance criteria

`FIR-API-001` is complete only when gateway responsibilities are explicitly
catalogued, forbidden domain ownership is mechanically checked, representative
negative mutations are detected by the checker, and consequential operations
remain service-owned end to end.

## FIR-PEOPLE-001 — Cross-Register Person Correlation Hard Gate

- **Status:** `approved`
- **Priority:** `critical`
- **Owner workstream:** Identity & People Administration (ID / PEOPLE)
- **Scope:** mechanical, repository-wide prevention of a person-level join
  between the engagement, membership, identity, payroll and voting registers
- **Target PACK / closure:** PACK-27–PACK-29 for repository-wide mechanical
  enforcement; mandatory blocker before Architecture Baseline 1.0 / Freeze
- **Dependencies:** `FIR-ID-001`, `FIR-AUTH-001`, `FIR-DATA-004`, PACK-08
  membership context, PACK-14 identity context, PACK-26 people administration

PACK-26 enforces non-correlation **inside its own context**: engagement
identifiers are engagement-local by type, the boundary walks refuse cross-domain
identifier names, and no projection joins across an authority domain.

That is not sufficient repository-wide. Nothing today mechanically prevents two
_different_ contexts from independently adopting the same external handle for
the same human and thereby reconstituting the join outside any single service's
boundary. Field-name lists do not catch it, because neither context has to name
the identifier in a prohibited way for the correlation to exist.

Hard invariant to be mechanically enforced:

```text
same natural person != same technical identifier across bounded contexts
per-context handles must not be derivable from one another
```

**Implementation evidence required:** a repository-level checker that inspects
declared reference types across services and fails when two contexts declare a
handle drawn from the same issuing authority or derivable namespace; adversarial
fixtures that attempt the join through a shared external register identifier.

**Verification gate:** the checker detects representative negative mutations —
a shared issuer, a derived handle, and a join performed in a read model —
rather than merely passing on the current tree.

**Blocker / limitation:** the general problem is not decidable from field names
alone. The gate is therefore scoped to _declared_ reference types and issuing
authorities, and the residual risk of an undeclared out-of-band correlation is
explicitly not closed by this entry.

## FIR-PEOPLE-002 — Employment Legal Classification Determination Boundary

- **Status:** `approved`
- **Priority:** `high`
- **Owner workstream:** Legal & People Administration (LEGAL / PEOPLE)
- **Scope:** the boundary between what this repository records about a working
  relationship and what German law determines about it
- **Target PACK / closure:** governed legal review before any production
  activation of people administration; not closable by an implementation round
- **Dependencies:** `FIR-LEGAL-001`, `OD-P26-01`, `OD-P26-05`, `OD-P26-04`

PACK-26 records `EngagementType.STAFF` as an administrative fact and offers no
`EMPLOYEE` member, carries `LEGAL_CLASSIFICATION_NOT_DETERMINED` on every
record, and refuses employment, tax and social-security conclusion fields at
every boundary. Notice, probation, fixed-term and social-security registration
periods are refused by name rather than computed.

What remains open is the governed question itself: whether any relationship any
organization operating this repository administers is an employment
relationship, who determines it, and what the system is permitted to display
once somebody has.

```text
administrative classification != legal employment determination
technical termination record != legally effective termination
contractor engagement record != tax or social-security classification
```

**Implementation evidence required:** a governed legal determination recorded as
repository evidence, per organization type, before any surface displays a
classification as settled.

**Verification gate:** no code path may set a classification other than
`NOT_DETERMINED_IN_THIS_SYSTEM` without a cited external determination
reference, and a test asserts that the permissive branch does not exist.

**Blocker / limitation:** this entry cannot be closed by implementation. It is
closed by a legal determination this repository does not make, and until then
the fail-closed behaviour is the whole control.

## FIR-PEOPLE-003 — Contractor Engagement / Procurement Boundary Enforcement

- **Status:** `approved`
- **Priority:** `high`
- **Owner workstream:** Procurement & People Administration (PROC / PEOPLE)
- **Scope:** mechanical enforcement that a contractor engagement and a
  procurement act remain separate decisions by separate principals
- **Target PACK / closure:** PACK-27–PACK-30 cross-context checker work
- **Dependencies:** `FIR-AUTH-001`, `OD-P25-01`, `OD-P26-12`, PACK-25
  procurement context, PACK-26 people administration

PACK-26 keeps the boundary structurally within its own context: the only link is
`VendorEngagementRef`, `assert_vendor_reference_is_not_award` always raises, and
`PROCUREMENT_AUTHORITY` is granted no people-administration action.

What is not yet enforced is the _cross-context_ direction. Nothing mechanically
prevents a consumer of both event streams from treating a contractor engagement
activation as evidence of vendor approval, or from ordering against a vendor
whose PACK-25 security and privacy reviews were never recorded.

```text
approved vendor != engaged contractor
contractor engagement activation != vendor activation
procurement approval != people-administration approval
```

**Implementation evidence required:** a cross-context checker asserting that no
consumer derives a procurement state transition from a people-administration
event, and that no principal holds an approving role in both contexts for the
same arrangement.

**Verification gate:** negative fixtures in which a consumer attempts the
derivation are detected; a same-principal-both-sides fixture is refused.

**Blocker / limitation:** depends on `OD-P25-01` and `OD-P26-12`, both open. The
fail-closed direction meanwhile is that no precondition is required, checked or
implied in either direction.

## Section 31 boundaries

These entries:

- add no new business domain;
- do not select a mixnet or other specific privacy mechanism today;
- do not make a universal legal conclusion about online procedures;
- do not change the accepted PACK-24 baseline;
- do not expand PACK-25 scope beyond carry-forward governance;
- do not change `CANON_VERSION`;
- must be preserved in every cumulative candidate beginning with PACK-25;
- are mandatory blockers for relevant production/legal activation;
- must be exercised in the system-wide pre-Freeze assurance programme where
  applicable.

# 32. Unified Control Plane and Administrative Workspace Architecture

## FIR-CTRL-001 — Unified Control Plane & Administrative Workspace Architecture

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** cross-cutting administration, operations, oversight, security,
  emergency access and domain work desks
- **Target:** `CTRL-01` after PACK-35 and before Architecture Baseline 1.0 / Freeze
- **Dependencies:** PACK-12, PACK-18, all domain PACKs through PACK-35,
  FIR-FRONT-001, FIR-INV-008, FIR-INV-009, FIR-INV-013 and FIR-INV-014

EPD² must define one authoritative system-wide map of administrative and
oversight surfaces after the domain architecture is complete.

The architecture must distinguish a **physical console** from the
**authority** exercised inside it. Several desks may share a shell or origin
only where trust boundaries permit it; sharing a shell must never merge
permissions.

### Hard invariants

```text
physical console != authority
workspace membership != domain authority
technical administrator != domain decision-maker
one UI shell != shared permissions
role visibility != authorization
break-glass != ordinary administration
security administration != system administration
oversight access != operational mutation authority
```

No physical console, role, workspace membership, technical account or
frontend route may create authority that is absent from the governed backend
authorization model.

### Mandatory Control Plane Registry

CTRL-01 must produce a machine-readable registry covering every
administrative or oversight desk with at least:

- `console_id`;
- `desk_id`;
- workspace;
- origin;
- role;
- authority / governed action set;
- Bund/Land/Kreis organization scope;
- backend service;
- routes;
- authentication and assurance level;
- step-up requirement;
- maker/checker and dual-control requirement;
- incompatible roles;
- sensitive-data classes;
- search/export restrictions;
- audit/evidence obligations;
- break-glass eligibility and notification;
- activation state.

A suitable repository artefact is:

```text
docs/architecture/control-plane/EPD2_Control_Plane_Registry.csv
```

or an equivalent governed machine-readable format.

### Required desk coverage

The registry must account for, at minimum, the domains and institutional
roles already defined or reserved in the architecture, including:

- system administration;
- security administration;
- privileged access and DLP/export review;
- operations;
- independent audit and oversight;
- DPO/privacy oversight;
- election administration;
- membership and organization administration;
- offices and mandates;
- assemblies, motions and minutes;
- correspondence;
- complaints, petitions and ombuds casework;
- protected reporting and investigations, including separately protected
  reporter-identity custody;
- finance;
- procurement and vendor governance;
- records/documents/retention;
- transparency/publication;
- representative/open-desk functions;
- Citizen Office routing;
- moderation;
- AI/human-review oversight;
- emergency and break-glass administration.

This list is a minimum inventory, not a requirement for one physical
application per desk.

### Physical-console decision

The final number of physical administrative applications, origins and shells
must be decided only after PACK-35, using:

- trust-boundary analysis;
- role incompatibility;
- data-classification boundaries;
- authentication/assurance requirements;
- emergency isolation;
- operational usability;
- accessibility;
- failure containment;
- independent oversight requirements.

A preliminary design may group multiple desks, but CTRL-01 must prove that
such grouping does not create shared authority or an unintended universal
administration surface.

### Frontend and backend rule

Frontend visibility is not an authorization boundary.

Every consequential action exposed by a desk must be authorized again at the
owning backend service using the current authority, scope, action, assurance
and object state.

A person who can deploy, restart, observe or secure a service does not thereby
gain the political, legal, financial, electoral, investigative or
administrative authority represented by that service.

### Break-glass boundary

Emergency access must remain a separately governed path. CTRL-01 must specify:

- eligible principals;
- permitted emergency actions;
- purpose and reason requirements;
- time limits;
- dual control where required;
- immutable audit evidence;
- out-of-band notification;
- post-event independent review;
- actions that remain prohibited even under break-glass.

### Acceptance criteria

FIR-CTRL-001 is complete only when:

1. every administrative/oversight role in the architecture resolves to an
   explicit desk or to an explicit `NO_UI` decision;
2. every desk resolves to exactly one owned route set and backend authority
   boundary;
3. every consequential action is mapped to an explicit authorization rule;
4. incompatible-role and maker/checker rules are machine-readable and tested;
5. no technical role gains domain authority by implication;
6. no shell/origin grouping creates shared permissions;
7. the Voting Client remains outside all administrative control-plane
   surfaces;
8. emergency access is independently governed and auditable;
9. system-wide architecture tests prove there is no unrestricted universal
   admin panel;
10. the Control Plane Registry is reviewed before Architecture Baseline 1.0 /
    Freeze.

### PASS / freeze rule

Architecture Baseline 1.0 / Freeze must not be declared until `CTRL-01` has
closed FIR-CTRL-001 or explicitly recorded a governed blocker accepted by the
architecture authority.

## Section 32 boundaries

This entry:

- does not fix the final number of physical consoles today;
- does not merge roles or domains;
- does not create a new business service;
- does not change `CANON_VERSION`;
- does not reopen accepted domain PACKs;
- requires a dedicated architecture-closure review after PACK-35;
- must be carried in every cumulative PACK beginning with PACK-25.

# 33. Procurement, vendors and third-party assurance

Added by the PACK-25 implementation candidate (2026-08-09).

The complete existing register was inspected before these entries were
created. Section 26's forms catalogue names a procurement request, a vendor
declaration, a bid submission, an evaluation declaration and an invoice
approval as **form types**; section 32 names procurement and vendor
governance as a **control-plane domain**. Neither states a lifecycle, an
authorization model or an assurance requirement, so neither is duplicated
here — both are referenced instead.

The `FIR-VENDOR-*` entries use "vendor" in the **counterparty** sense: a
third party this organization commits to. `FIR-OSS-003` uses "vendored" in
the **dependency** sense. The two are deliberately not conflated, and no
entry here supersedes `FIR-OSS-003`.

## FIR-PROC-001 — Procurement Requisition, Procedure and Selection Governance

**Status:** implemented in reference form
**Domain owner:** procurement office
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `docs/packs/PACK-25/PACK-25-PROCUREMENT-PROCESS.md`,
`contracts/procurement/procurement-requisition.schema.json`,
`contracts/procurement/procurement-procedure.schema.json`,
`contracts/procurement/bid.schema.json`,
`contracts/procurement/selection-decision.schema.json`

A requisition, a procedure, a bid and a selection decision are four
separate versioned records with four separate lifecycles. The separations
are held as absent transition edges rather than as validation rules:

```text
requisition != approval
approval    != procurement selection
bid         != contract
selection   != contract execution
```

A selection decision cannot be constructed without the evaluation-criteria
version that applied **at decision time**, because a decision whose
criteria are unrecorded cannot be reviewed.

**Remaining work.** Whether public-procurement law applies at all is
`OD-P25-01`; thresholds are `OD-P25-02`; publication duties `OD-P25-03`;
permitted methods `OD-P25-04`; award requirements `OD-P25-05`; challenge
and remedy `OD-P25-06`. No entry here may be read as claiming any of them
resolved. "Reference form" is the operative qualifier: the workflow is
real and tested, the deployment is not.

## FIR-PROC-002 — Commitment Chain: Contract Reference, Purchase Order, Acceptance and Invoice Control

**Status:** implemented in reference form
**Domain owner:** procurement office; finance for the payment boundary
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `docs/packs/PACK-25/PACK-25-STATE-MACHINES.md`,
`contracts/procurement/contract-reference.schema.json`,
`contracts/procurement/purchase-order.schema.json`,
`contracts/procurement/delivery-acceptance.schema.json`,
`contracts/procurement/invoice-reference.schema.json`

Four links, four separations:

```text
contract            != purchase order
purchase order      != delivery acceptance
delivery acceptance != invoice approval
invoice approval    != payment
```

The chain stops structurally at the invoice-approval control. There is no
payment record, no payment state, no payment port and no payment command
in the package; `PAYMENT_AUTHORITY_ACTIONS` is empty and a test asserts
that it is. The three-way match is an operational control whose outcome
proves nothing about invoice legality, tax correctness, payment
entitlement or accounting correctness, and a missing leg fails closed for
approval rather than producing a partial match.

**Remaining work.** The interface between an approval control and actual
payment is `OD-P25-21`. Retention periods are `OD-P25-24`. Neither is
resolved and neither may be inferred from the existence of this chain.

## FIR-PROC-003 — Procurement Separation of Duties and Maker-Checker

**Status:** implemented in reference form
**Domain owner:** procurement office; independent oversight
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `docs/packs/PACK-25/PACK-25-SEPARATION-OF-DUTIES.md`,
`contracts/procurement/pack-25-procurement-vocabulary.json`

Ten separation-of-duties controls, each checked against a recorded fact
rather than against a role where a role check would miss the case:

```text
requester                != approver
buyer                    != sole final approver
receiver                 != supplier side
receiver                 != payer
budget approval          != payment authority
security review          != procurement approval
privacy review           != procurement approval
contract owner           != override of a review refusal
technical administration != procurement authority
subject vendor           != its own assessor
```

The requester check is keyed on the requisition's recorded requester, not
on roles, because the requester frequently holds a valid approver
authority for every _other_ requisition and every role-keyed check would
pass them. The vendor-side exclusion is keyed on the presence of a
vendor-side principal in the request context, so a supplier's
representative who also holds an internal account is still refused.

**Relationship to `FIR-ROLE-006`.** That entry owns finance separation of
duties and is untouched. This entry owns the procurement side and stops at
the payment boundary.

**Remaining work.** Monetary thresholds for maker-checker are `OD-P25-22`.
While that is open, the buyer is refused as sole approver outright rather
than above a figure nobody has stated. Contract-signing authority is
`OD-P25-23`.

## FIR-VENDOR-001 — Vendor Lifecycle and Activation Gate

**Status:** implemented in reference form
**Domain owner:** vendor management; security review; DPO
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `docs/packs/PACK-25/PACK-25-SPECIFICATION.md`,
`contracts/procurement/vendor.schema.json`

The proposition this entry exists for:

```text
a third party is never trusted merely because it exists in the vendor
registry
```

Held by four mechanisms, because each survives a different mistake: a
transition table with no edge into `ACTIVE` except from
`APPROVED_FOR_CONTRACTING`; an activation gate that runs the governed
review set independently of that table; `VendorClass.UNSPECIFIED` as the
default, refusing activation rather than treating an unclassified vendor
as low risk; and no edge from `SUSPENDED` back to `ACTIVE`, so a suspended
vendor returns through review or not at all.

Also held here:

```text
vendor registration != vendor activation
suspension          != deletion
termination         != data erasure
contract expiry     != vendor deletion
renewal             != automatic reactivation
vendor              != external gateway != internal service
```

**Remaining work.** Which reviews a vendor class requires beyond the stated
security/privacy minimum is `OD-P25-14` and `OD-P25-17`; how long a review
stays valid is `OD-P25-16`. Both fail closed. Sanctions screening
(`OD-P25-07`) and beneficial-ownership checks (`OD-P25-08`) are not
performed and their absence is not a clearance.

## FIR-VENDOR-002 — Third-Party Assurance: Versioned Evidence-Backed Assessment and Governed Reviews

**Status:** implemented in reference form
**Domain owner:** vendor management; security review; DPO
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `docs/packs/PACK-25/PACK-25-ASSESSMENT-AND-REVIEW-MODEL.md`,
`contracts/procurement/vendor-assessment.schema.json`,
`contracts/procurement/governed-review.schema.json`

Assurance is an evidence-backed, versioned, purpose-bounded assessment and
never a boolean. There is no `trusted`, `safe_vendor`, `legal_vendor`,
`gdpr_compliant` or `approved_by_law` field anywhere, and the walk that
refuses them runs on every inbound command, every event and every
projection. The strongest positive outcome is
`ACCEPTABLE_FOR_STATED_PURPOSE`, and the three words after "acceptable"
are the whole of it.

```text
assessment        != certification
vendor risk score != legal/compliance determination
processor status  != GDPR legal conclusion
security review   != privacy review
```

The two reviews are separately authorized, separately auditable and
separately typed. A review record cannot be constructed without a stated
scope, a stated purpose and stated **limitations**, because a review with
no stated limitations has not said what it did not look at.

**Relationship to `FIR-DATA-001`.** The processor-role statement records
who stated what, with evidence and a date. It makes no classification, and
`FIR-DATA-001` keeps the classification requirement.

**Remaining work.** Mandatory security standards `OD-P25-14`; audit and
penetration-test evidence requirements `OD-P25-15`; DPA workflow
`OD-P25-11`; international transfers `OD-P25-12`; subprocessors
`OD-P25-13`.

## FIR-VENDOR-005 — Event-Triggered Vendor Reassessment

**Status:** implemented in reference form
**Domain owner:** vendor management (decision); security review and DPO
(trigger and reassessment)
**Package:** PACK-25 (`services/procurement-service/reassessment.py`)
**Evidence:** `docs/packs/PACK-25/PACK-25-REASSESSMENT.md`,
`contracts/procurement/vendor-reassessment-trigger.schema.json`,
`contracts/procurement/vendor-reassessment.schema.json`,
`NC-P25-44` … `NC-P25-47`

Periodic review answers "is this still fine, a year later" and cannot
answer "this vendor was breached on Tuesday". A relationship reviewed only
on a schedule is unassessed for the whole interval between the event and
the next scheduled review, and that interval is when the answer matters.

```text
periodic review     != reassessment
trigger recorded    != decision made
decision recorded   != act performed
vendor's account    != established fact
```

Ten governed trigger kinds — security incident or breach, privacy breach,
subprocessor change, hosting or processing region change, ownership or
control change, certificate or assurance expiry, material product or API
change, material contract amendment, signing key or certificate
compromise, and critical vulnerability materially affecting the supplied
service. An unknown kind is refused rather than bucketed as "other", and
`UNSPECIFIED` cannot open a reassessment.

Five governed outcomes — continue unchanged, continue with restrictions,
suspend required, remediation required, exit required — each recorded with
evidence and a named deciding authority, at `HIGH` assurance and with two
principals. **None of the five is self-executing.** The decision names the
separate governed act it calls for; performing that act belongs to the
authority that holds the vendor lifecycle, with its own authorization and
its own second principal.

Both reviewers may open a reassessment and neither may close one, which is
the same separation the two governed reviews already carry.

**Remaining work.** No trigger is detected by this service — something
outside it observes the incident. No review interval is encoded
(`OD-P25-28`), nothing expires a review, and no severity is rated. The
restriction and remediation follow-up acts named by the decision table are
references, not commands: `vendor.restriction.record` and
`vendor.remediation.record` do not exist yet, and a later pack that adds
them must keep them separate from the decision that calls for them.

## FIR-VENDOR-003 — External Provider and Gateway Lifecycle Governance

**Status:** implemented in reference form
**Domain owner:** vendor management; owning internal service
**Package:** PACK-25 (`services/procurement-service`); closes the
vendor-lifecycle half of AGR-30
**Evidence:**
`docs/packs/PACK-25/PACK-25-PROVIDER-GATEWAY-GOVERNANCE.md`,
`contracts/procurement/provider-registration.schema.json`,
`contracts/procurement/provider-signal.schema.json`

AGR-30's rule, made structural:

```text
external provider success signal != internal legal/procedural truth
provider IDs                     != global IDs
signed callbacks                  are replay-safe and purpose-bound
exit/export                       is evidenced, not claimed
```

Every provider signal kind is phrased as a claim — `DELIVERY_CLAIMED`,
`PAYMENT_SUCCESS_CLAIMED`, `SIGNATURE_CLAIMED` — because a field named
`delivered` is read as delivery by everybody who sees it. A
provider-local identifier is a distinct type bound to one registration and
the function that would promote it always raises. Callback validation runs
**before** the replay ledger is consulted or written, so an unsigned
callback cannot claim a genuine callback's reference.

A provider registration is separate from the vendor record and never
derived from it: the same company can be an active vendor with a suspended
gateway.

**Relationship to `FIR-SEC-003`.** That entry owns external gateway
_security_ — transport, keys, rotation, runtime hardening — and is
untouched. This entry owns the gateway's _lifecycle and governance_.

**Remaining work.** Signature and callback standards are `OD-P25-28`; the
absence of an agreed standard is not permission to skip validation, and
the fail-closed direction is refusal.

## FIR-VENDOR-004 — Vendor Renewal, Exit and Evidence of Disengagement

**Status:** implemented in reference form
**Domain owner:** vendor management; contract owner; records officer
**Package:** PACK-25 (`services/procurement-service`)
**Evidence:** `contracts/procurement/vendor-exit.schema.json`,
`contracts/procurement/renewal-review.schema.json`

An exit records evidence of ten things and cannot record a step without an
evidence reference, because a tick answers nothing six months later when
somebody asks whether the data actually came back. Two of the ten are
separate kinds on purpose:

```text
DATA_RETURN_OR_DELETION_REQUESTED        — what we did
PROVIDER_DELETION_CONFIRMATION_RECEIVED  — what they said
```

Neither is deletion, and each has its own refusal, because the two
mistakes are made by different people: the first by whoever builds the
exit workflow, the second by whoever integrates the provider's API. The
terminal state is `EXIT_COMPLETED_OPERATIONALLY` rather than
`EXIT_COMPLETED`, because what this repository can observe is that the
internal steps were performed.

A renewal is a new governed review and a new decision. There is no
`AUTO_RENEWED` outcome, `NOT_REVIEWED` and `UNSPECIFIED` both refuse, and
the vendor state machine has no `SUSPENDED -> ACTIVE` edge for a renewal
to travel along.

**Remaining work.** Exit and export testing requirements `OD-P25-19`;
deletion and return evidence requirements `OD-P25-20`; continuity, RTO and
RPO by vendor class `OD-P25-18`.

## FIR-REG-001 — Master Future Implementation Register Freshness Gate

**Status:** implemented in reference form
**Domain owner:** repository governance
**Package:** PACK-25 (`scripts/check_register_freshness.py`)
**Evidence:** `tests/repository/test_pack25_register_freshness.py`,
`Makefile` `check-repository` target

Section 1.4.1 states the freshness rule. Until PACK-25 it was prose, and a
prose rule about staleness is exactly the kind of rule that goes stale.

The checker refuses a cumulative candidate when:

1. the canonical register is missing;
2. a second or duplicate future-implementation register exists anywhere in
   the tree;
3. the register's repository-version expectation is behind the repository's
   own `REPOSITORY_VERSION`;
4. the latest implementation round is absent from the register;
5. `FIR-BASE-001` does not structurally distinguish the latest accepted
   cumulative baseline from the current implementation candidate;
6. a PACK round record omits any of the four FIR disposition categories
   section 1.3 requires.

The current repository version and the current pack number are **derived**
from existing canonical metadata — `epd2_core.version.REPOSITORY_VERSION`
and the `docs/packs/PACK-nn` directories — rather than hardcoded, so the
checker cannot itself become the stale list it exists to prevent.

`tests/repository/test_pack25_register_freshness.py` proves each of the
six detections by building a deliberately broken temporary fixture and
asserting the checker fails on it. A checker tested only against the real,
passing register would pass equally well if it did nothing.

**Remaining work.** The checker reads structure, not meaning: it cannot
tell a truthful round record from a plausible one. That remains a human
review obligation, and the register says so rather than implying the check
is sufficient.

# 34. Repository Secret Leakage Prevention & Public-Release Sanitization

## FIR-SEC-SECRET-001 — Repository Secret Leakage Prevention & Public-Release Sanitization

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** repository governance, developer workflows, CI/CD, packaging, release evidence and public-repository publication
- **Target:** distributed implementation; automation in INFRA/CI phase; mandatory closure before Public Repository Release and Production Readiness
- **Dependencies:** FIR-CRYPTO-001, FIR-REL-001, FIR-READY-001, FIR-SEC-003, FIR-TEST-001, FIR-TEST-002

EPD² must maintain a fail-closed repository and release boundary against accidental disclosure of live secrets.

Hard invariant:

```text
live operational secret ∉ source tree
live operational secret ∉ committed fixtures/docs
live operational secret ∉ persisted logs/evidence
live operational secret ∉ distributable artifacts
live operational secret ∉ published Git history
```

Test credentials and cryptographic material that must be committed for verification are allowed only when they are explicitly synthetic/non-live or intentionally public reference material. A public key, deterministic hash, governed test vector or NIZK verification artefact is not a secret merely because it is cryptographic; real private/signing/recovery material remains prohibited.

### Required enforcement layers

The final implementation must provide independent controls at least at these boundaries:

1. developer-side pre-commit detection as early-warning/defence-in-depth, never as the sole authoritative control;
2. authoritative CI scanning of changed content and generated outputs entering the build;
3. full current-tree and publishable Git-history/ref scanning before public release;
4. pre-packaging source/staging scan plus post-packaging inspection of the actual ZIP/wheel/distributable bytes;
5. a dedicated Public Repository Release Gate immediately before public visibility is enabled.

Detection may use provider-specific signatures, structured detectors, known-secret formats, entropy analysis and other governed mechanisms. The scanner product/implementation is intentionally not selected by this FIR.

### Allowlist governance

Inline developer bypasses such as `# ignore-secret` are prohibited as a general mechanism. Any necessary exception must be declared centrally, narrowly scoped and evidence-backed as synthetic/non-live or intentionally public. Broad path or pattern exemptions capable of concealing a genuine live secret are not acceptable.

### Environment and evidence boundary

Only non-secret templates such as `.env.example` may be committed. Real `.env` files, production credentials, developer tokens and machine-local secret-bearing configuration remain outside version control and release artifacts. `.gitignore` is defence-in-depth, not evidence that the repository is clean.

Persistent CI logs, diagnostic traces, verification bundles and WORM evidence must redact secret-bearing authorization headers, cookies, session/access/refresh tokens, credentials, private keys and secret-valued environment variables before persistence or publication. Redaction itself must be mechanically testable.

### Confirmed-secret response

A confirmed live secret is considered compromised regardless of whether the repository was already public. Remediation requires revocation/rotation at the owning authority/provider, removal from the publishable state/history as required, and a complete rescan. Rewriting history does not substitute for credential rotation.

### Acceptance criteria

`FIR-SEC-SECRET-001` may move to `implemented` only when machine-enforced evidence proves PASS across the relevant repository/CI/history/packaging/public-release boundaries. Before Architecture Baseline 1.0 / Freeze and before the first public repository release, all of the following must pass simultaneously:

```text
current repository tree
+ publishable Git history and refs
+ generated/build outputs selected for distribution
+ compiled packages/wheels
+ final public-release archive
+ persisted release evidence intended for publication
```

Any unresolved confirmed live-secret finding is a hard release blocker.

## Section 34 boundaries

This entry does not select a secret-scanning vendor or tool, does not require PACK-26 to implement INFRA/CI automation, does not alter PACK-25C6, and does not classify intentionally public PACK-16D reference cryptographic material as secret. PACK-26 and later cumulative candidates must preserve this requirement and must not introduce secret-bearing committed material while the full automated enforcement remains future work.

# 35. Sovereign Hosting, Infrastructure Isolation & Data-Residency Assurance

## FIR-INFRA-SOV-001 — Sovereign Hosting, Infrastructure Isolation & Data-Residency Assurance

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** production hosting, cloud/provider governance, tenancy/isolation, data residency, operator access, cryptographic key custody, deployment assurance and high-criticality workload placement
- **Target:** provider-neutral architecture and assurance profile before real-user Public Pilot; production profile must pass before Production Readiness / Freeze
- **Dependencies:** FIR-REL-001, FIR-READY-001, FIR-DATA-004, FIR-TEST-002, FIR-LEGAL-001, FIR-SEC-003, FIR-SEC-SECRET-001, FIR-VOTE-NET-001, FIR-VOTE-CRYPTO-001, FIR-API-001

EPD² must define and enforce a provider-neutral infrastructure assurance profile appropriate to the sensitivity and consequence of each workload. Provider selection is an implementation/procurement decision, not a domain invariant.

### Core invariant

```text
hosting provider ≠ trust assumption
EU/EEA location ≠ sufficient assurance by itself
dedicated hardware ≠ automatically required by law
shared tenancy ≠ automatically acceptable for every workload
provider certification ≠ EPD² production readiness
```

A deployment may use public cloud, private cloud, dedicated/bare-metal infrastructure or a hybrid model only when the chosen placement is supported by the threat model, data-protection/legal assessment, tenant-isolation evidence, operator-access model, key-custody model, resilience requirements and deployment-manifest controls.

### Required assurance dimensions

The implementation phase must define machine-reviewable or evidence-backed controls for at least:

- processing/data residency and backup residency;
- controller/processor/subprocessor chain and relevant cross-border access exposure;
- tenant isolation and hypervisor/shared-memory risk appropriate to workload criticality;
- network segmentation and ingress/egress boundaries;
- privileged operator access and separation of duties;
- encryption in transit and at rest;
- key custody, HSM/KMS assurance and break-glass controls;
- immutable deployment identity and artefact digests under `FIR-REL-001`;
- backup/recovery verification and incident-response integration;
- audit/evidence retention and secret-redaction requirements;
- provider exit, migration and portability;
- DDoS/availability controls appropriate to public and voting-facing services;
- mixed-version compatibility and fail-closed rollout constraints.

### Criticality profiles

At minimum, the future deployment model must distinguish lower- and higher-criticality workloads instead of treating all ten workspaces as requiring identical physical infrastructure.

The isolated Voting Client, voting/eligibility/credential trust boundaries, privileged administration, legal/oversight functions, signing/key material and other high-consequence data paths require a stronger assurance profile than ordinary public read surfaces. Dedicated or otherwise demonstrably isolated compute may be required where the threat model and independent assurance justify it, but the register does not prescribe bare metal as a universal legal requirement.

The accepted ten-workspace/ten-origin architecture is a logical/security-origin invariant. It does **not** by itself mandate ten physical hosts or ten physical security zones.

### Provider neutrality

No commercial provider is canonically selected by this FIR. Hetzner, OVHcloud, European sovereign-cloud offerings, hyperscalers with suitable controls, colocation or another provider may be evaluated later against the same evidence-based profile.

No provider may become a hidden source of domain truth, authorization, voting truth or legal effect. Provider-specific KMS/HSM, IAM, queue, database or networking facilities are infrastructure adapters and must remain behind governed service boundaries.

### Legal/regulatory evidence boundary

Any assertion that a German or EU rule, regulator, authority, eID integration or certification scheme requires or prohibits a specific hosting/tenancy model must be backed by current governed legal/official evidence. In the absence of such evidence the state is `OPEN`; architecture may still voluntarily choose a stronger assurance posture.

In particular:

```text
implemented infrastructure ≠ legally approved infrastructure
EU-hosted ≠ automatically compliant
provider certification ≠ BVA/eID approval
technical isolation ≠ legal activation
```

### Public-pilot and production gates

Before processing real-user high-sensitivity data in a Public Pilot, EPD² must have an approved hosting assurance profile, provider assessment, deployment topology, key-custody design, backup/recovery evidence, incident boundary and data-protection/legal disposition appropriate to the planned use.

Before Production Readiness / Freeze, the deployed set must additionally be bound to the immutable deployment manifest required by `FIR-REL-001`, with tested compatibility, recovery, rollback, provider-exit and independent assurance evidence. Unknown critical infrastructure state fails closed.

### Current implementation boundary

This FIR does not require PACK-27 to deploy cloud resources, choose a vendor, configure databases, create HSM/KMS infrastructure or make a legal claim about eID hosting. PACK-27 and later packs must preserve the requirement and must not introduce provider lock-in into domain logic.

# 36. Governed Native Mobile Client & Release Assurance

## FIR-MOBILE-001 — Governed Native Mobile Client & Release Assurance

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** native/cross-platform mobile client, mobile authentication/session handling, deep links, notifications, secure local state, app-store release, build provenance and Voting Client handoff
- **Target:** architecture preparation during PACK-27–30; first installable mobile client after platform/API boundaries stabilize (target MOBILE-01 after approximately PACK-30/31); full hardening and release assurance before Public Pilot / Production Readiness
- **Dependencies:** FIR-API-001, FIR-AUTH-001, FIR-ID-001, FIR-REL-001, FIR-READY-001, FIR-TEST-002, FIR-SEC-SECRET-001, FIR-VOTE-NET-001, FIR-VOTE-CRYPTO-001, FIR-CTRL-001

EPD² shall support a governed native or cross-platform mobile application as a presentation/client channel over the same service-owned domain rules as the web clients.

### Core invariant

```text
Mobile App ≠ new bounded context
Mobile App ≠ new workspace
Mobile App ≠ new domain authority
Mobile App ≠ Voting Client
web rules = mobile rules = service-owned domain rules
```

The mobile application must not duplicate or fork consequential business rules, authorization truth, legal-effect decisions, voting truth or workflow state machines. It consumes governed APIs/BFF projections and commands while backend services remain authoritative.

### Workspace/origin continuity

The existing architecture remains exactly ten workspaces/origins. Mobile is a client channel mapped onto governed capabilities; it does not create `WS-11` and does not collapse existing origin boundaries.

A mobile capability must resolve to an existing workspace owner, backend service and action/assurance policy. Unknown route/capability/action fails closed.

### Voting from mobile

Voting remains isolated. The app must not embed ordinary member-session continuity into the Voting Client and must not persist voting identity, ballot, credential or voter-linked telemetry.

The governed model is:

```text
Mobile/member context
    -> explicit one-time scoped handoff
    -> isolated system-browser / Voting Client origin
    -> no shared cookies/storage/session/analytics
```

Returning from Voting Client must not create a covert identity↔ballot correlation channel. No mobile SDK, analytics, crash-reporting, push system, deep-link payload or shared storage may weaken `FIR-VOTE-NET-001` or the accepted Voting Client isolation profile.

### MOBILE-01 scope

The first installable mobile client should remain deliberately narrow and may expose low-/medium-risk member-facing capabilities such as:

- authentication/account entry through governed identity flows;
- member dashboard/read models;
- announcements and documents;
- own case/correspondence/status views;
- assembly/agenda information;
- neutral notifications;
- explicit handoff to isolated voting.

MOBILE-01 must not become a privileged universal administration console. High-privilege Legal, Security Admin, System Admin, election administration and other sensitive control-desk functions remain excluded unless a later explicit assurance decision authorizes a narrowly scoped mobile surface.

### MOBILE-02 / later capability expansion

After PACK-33–35 domain surfaces stabilize, a later round may add governed mobile access to Citizen Office, Representative Desk, deliberation/program, delegation and transparency capabilities. Each capability remains subject to its existing workspace, authorization, privacy and legal-effect boundaries.

### Mobile security profile

Before any real-user pilot, mobile implementation must define and test at least:

- secure token/session storage with explicit lifetime/revocation behaviour;
- prohibition of sensitive material in ordinary logs, crash reports, clipboard and screenshots where justified;
- deep-link and universal/app-link validation;
- push-notification identity/content minimization and neutral sensitive notifications;
- rooted/jailbroken-device risk policy where justified by threat model;
- local-cache classification, encryption and expiry;
- offline behaviour that cannot manufacture authority or stale consequential state;
- TLS and endpoint trust policy; certificate pinning only if justified and operationally supportable;
- no uncontrolled third-party analytics/fingerprinting for sensitive flows;
- no persistent Voting Client identifier or shared voting state;
- dependency provenance and mobile SBOM/release inventory;
- signing-key custody and release separation of duties;
- update, rollback, minimum-supported-version and forced-security-update policy;
- accessibility as Definition of Done.

### Build and store-release assurance

Before store-ready Beta and Production Readiness, every mobile release must be bound to an immutable machine-readable release/deployment manifest identifying at least source/repository release, exact mobile artefact digest, dependencies, API/contract compatibility, signing identity, build environment/provenance and required backend compatibility.

Release gates must cover secret scanning, package/dependency provenance, app signing, reproducible/verifiable build evidence where feasible, malware/static analysis as governed, store-distribution configuration and rollback/revocation procedures.

A successful App Store / Play Store review is distribution evidence, not EPD² security or legal approval.

### Privacy and identity minimization

Mobile convenience features must not create a universal cross-domain person identifier. Device identifiers, push tokens, installation IDs and analytics IDs are not allowed to become hidden identity-correlation keys across bounded contexts.

Push infrastructure must carry the minimum information necessary to route a neutral notification. Sensitive domain content should be fetched only after authenticated/authorized application access where the governing domain allows it.

### API/BFF boundary

Mobile-specific BFF/adaptation may perform routing, protocol adaptation, request shaping and aggregation of already-authorized read models, but must obey `FIR-API-001`: it may not own domain state, execute domain decisions, become authorization truth or bypass service invariants.

### Current implementation boundary

PACK-27–30 should prepare stable mobile-safe contracts, authentication/session semantics, notification policy, deep-link policy and Voting Client handoff constraints, but should not prematurely build a second business-logic stack.

A later dedicated `MOBILE-01` round should produce the first installable application. Subsequent `MOBILE-02` and security/release-hardening work completes the client before Public Pilot / Production Readiness.

This FIR remains open until an actual independently verified mobile release satisfies the required functional, privacy, security, accessibility, voting-isolation and release-assurance gates.

# 37. Conflict of Interest and Recusal Enforcement

## FIR-PUB-001 — Governed Publication Channels and the Reach of a Withdrawal

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** transparency publication (PACK-28), infrastructure, communications
- **Target:** a later governed round
- **Dependencies:** FIR-INFRA-SOV-001, FIR-COMM-001

PACK-28 renders an approved projection on one governed surface in this
repository and takes no position on any other channel. Syndication, feeds,
mirrors, third-party archives and search-engine indexes are all outside it,
and `channel_policy` is `UNSPECIFIED` because no body has decided them.

The gap this entry records is not the absence of a feed. It is that
**withdrawal does not reach a copy somebody already holds.** PACK-28's
withdrawal changes what this repository renders; it does nothing about a
page already archived, quoted or indexed. A body that withdrew a
publication and believed the matter closed would be wrong in a way nobody
in the system would tell them.

`FIR-PUB-001` may move to `implemented` only when the channels an approved
projection may reach are governed, when a withdrawal produces a governed
notification to each of them, and when the surface states plainly what a
withdrawal cannot undo. `OD-P28-08` is the open decision.

## FIR-PUB-002 — Publication Integrity Signing and Independent Verification

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** transparency publication (PACK-28), infrastructure, verification
- **Target:** a later infrastructure round
- **Dependencies:** FIR-INFRA-SOV-001, FIR-ROADMAP-007

PACK-28's `PublicationReceipt` carries a deterministic, publicly
recomputable SHA-256 over the projection, its source-reference set, its
policy version and its publication version. It proves that a projection in
hand is the one the receipt was issued over. It proves nothing about who
issued it.

That distinction is stated in three places — `verify_receipt`'s docstring,
the `INTEGRITY_STATEMENT` rendered on the protected evidence surface, and
`refuse_production_signing_claim`, which refuses the stronger claim by
name — precisely because a reader looking at a hash will otherwise assume
the stronger thing.

What is missing is a signature over a key somebody accountable holds, a key
custody arrangement, a signer registry, and an independent verifier that
can check a published projection without trusting the publisher. Each of
those is infrastructure this repository has deliberately not chosen
(`FIR-INFRA-SOV-001`), and inventing a signing scheme without them would
produce evidence that looks stronger than it is — which is worse than the
honest digest.

`FIR-PUB-002` may move to `implemented` only when publication evidence is
signed under governed key custody and an independent verifier reproduces
the check without the publisher's cooperation. `OD-P28-10` is the open
decision.

## FIR-PUB-003 — Governed Consumption of Published Projections by Reporting and Parliamentary Interfaces

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** transparency publication (PACK-28), PACK-29 parliamentary interface, finance reporting
- **Target:** PACK-29 and later reporting rounds
- **Dependencies:** FIR-PUB-001, FIR-PUB-002

PACK-28 produces governed publication decisions, projections and evidence,
and owns none of the consequences. A parliamentary interface, a finance
reporting surface or an open-representative desk _may_ consume a published
projection through a stable interface, and none of them currently does.

The interface has to be built from the consuming side, and it has to
preserve the separations in both directions:

```text
published projection != source-domain truth
published projection != legal effect
absence of a publication != absence of the underlying fact
```

The failure this entry exists to prevent is the convenient shortcut: a
consumer reads the public index because it is convenient, treats it as the
register, and acts on a snapshot that has since been corrected —
`refuse_projection_as_source_truth` and
`assert_projection_is_not_authority` exist for exactly that reader, and
neither binds a consumer that never calls them.

`FIR-PUB-003` may move to `implemented` only when a consuming context takes
a governed decision of its own that _cites_ a published projection, with
the citation recorded, the projection version pinned, and the consuming
decision separately authorised — never when a surface simply reads the
index.

## FIR-PUB-004 — Removal of the Inherited PACK-04 Upstream Dependency Declarations

- **Status:** `superseded`
- **Superseded by:** ADR-113, performed in the PACK-28C1 correction round (2026-08-10)
- **Priority:** —
- **Scope:** transparency publication (PACK-28), PACK-04 ADR-012, repository dependency governance
- **Target:** none — the work is done
- **Dependencies:** none

**This entry no longer represents outstanding future work, and the
identifier is retired rather than reused.** Section 1.2 forbids silent
deletion, so the entry stays where it was written, says what it recorded,
and says what happened to it.

**What it recorded.** PACK-28 found that
`services/transparency-service/pyproject.toml` still declared four
upstream PACK-04 dependencies — `epd2-initiative-service`,
`epd2-moderation-service`, `epd2-voting-service`,
`epd2-tally-service` — that no module in the service imported, and
deferred their removal to a later round on the reasoning that removing an
ADR-sanctioned declaration is an amendment to that ADR.

**Why that was the wrong disposition.** The reasoning was sound about
_what_ the change is and wrong about _when_ it belongs. Amending an ADR,
deleting four manifest lines, narrowing two allowlists and regenerating a
lock file is the work of a correction round, not of a future domain round.
A register entry that defers something already doable teaches this
register's readers that entries are aspirational — which is the one thing
this file cannot afford to be.

Independent inspection of the PACK-28 candidate made the same point from
the other side: the pack claimed a transparency publication context with
no direct dependency on any source-domain service while its manifest still
declared four of them. The claim was true of the publication _layer_ and
false of the _manifest_, and a reader had no way to know the sentence was
scoped.

**What happened.** PACK-28C1 removed the four declarations, recorded
ADR-113 superseding ADR-012's items 1–3 in part while re-affirming its
item 4 and every one of its exclusions, emptied
`ALLOWED_PACK04_TO_UPSTREAM_APPLICATION_MODULES` and
`PACK04_ALLOWED_PACK03_ROOTS`, regenerated `uv.lock` with `uv lock`, and
added repository tests that refuse the four packages in every form — static
import, `from` import, `TYPE_CHECKING`-guarded import, dynamic import
machinery and bare module-path string.

`services/transparency-service` now declares `epd2-core` and
`epd2-audit-core`, and nothing else.

**The identifier is not reused.** `FIR-PUB-004` names this subject and no
other, permanently. A future dependency-governance requirement gets its
own identifier.

## FIR-DESK-001 — External Parliamentary Source Authenticity and Provenance Verification

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** representative desk (PACK-29), infrastructure, integration
- **Target:** a later governed round
- **Dependencies:** FIR-INFRA-SOV-001, FIR-SEC-SECRET-001, FIR-PUB-002

PACK-29 records pointers at parliamentary records — a written question, a
motion, a speech, a committee item — and records for each of them what kind
of record it is, its stable external identifier, which authority published
it, when this repository observed it, and how far that observation was
verified. It holds no copy: `ExternalParliamentaryRecordRef` has no
`content`, `title`, `text` or `result` field, because a mirror of a
chamber's proceedings becomes the version people read and this repository
has no authority to be that.

What is missing is the verification itself. There is **no authenticated
channel to any parliament** in this repository, so the strongest status
`VerificationStatus` offers is `SOURCE_ATTESTED`, which means only that the
publisher said so, and there is deliberately no `VERIFIED` member at all —
a status that implied verification without one would be the most
load-bearing lie on a public representative surface. The reserved deadline
kind `ACTIVITY_REFERENCE_REFRESH_WINDOW` is reserved for the same reason:
a refresh cadence without a source to refresh from is a cadence that
measures nothing.

`FIR-DESK-001` may move to `implemented` only when a governed retrieval path
to a named source authority exists, when its authenticity evidence is
recorded per reference rather than asserted per source, and when the public
surface states which references carry that evidence and which do not.
`OD-P29-11` is the open decision.

## FIR-DESK-002 — Governed Answering Periods and Representative Desk Service Targets

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** representative desk (PACK-29), governance, legal
- **Target:** a later governed round
- **Dependencies:** FIR-LEGAL-001, FIR-CASEWORK-001

Four of PACK-29's eleven deadline kinds are enforced; seven are reserved
with a stated reason, and four of those seven —
`INTAKE_RESPONSE_TARGET_WINDOW`, `INTAKE_CLASSIFICATION_WINDOW`,
`COMMITMENT_DUE_WINDOW` and `DESK_REVIEW_WINDOW` — are reserved because
nobody has decided how long a representative has to answer a constituent,
who sets that period, and what follows from missing it. The reserved event
type `representative.deadline.missed` is the same gap seen from the event
side.

Nineteen statutory-sounding period names are refused outright by
`REFUSED_STATUTORY_DEADLINE_NAMES`. That refusal is the point: a service
target a party set for itself and a statutory period a legislature set are
different objects with different consequences, and a system that let the
first be named as the second would let an internal courtesy be read as a
legal duty — including by the constituent waiting on it.

`FIR-DESK-002` may move to `implemented` only when the answering periods are
decided by a body with the authority to decide them, when each is declared
with its policy version and its enforcement call site, and when the surface
distinguishes a target the organisation set from an obligation somebody
else imposed. `OD-P29-05` and `OD-P29-06` are the open decisions.

## FIR-DESK-003 — Governed Staff Worklist and Intake Assignment at a Representative Desk

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** representative desk (PACK-29), people administration (PACK-26), privacy
- **Target:** a later governed round
- **Dependencies:** FIR-ID-001, FIR-DATA-004, FIR-PEOPLE-001

PACK-29's one reserved action is `representative.intake.assign`, and its
matching reserved event is `representative.intake.assigned`. Assigning an
inbound item to a named member of office staff records a person-level fact
about an employee — which member of staff handled which constituent's
matter — and whether this service may hold such a fact at all is
`OD-P29-08`, which is open.

Meanwhile the item reaches staff through the desk's own worklist, which
needs no assignment record and creates no such fact. That is a real
capability gap rather than a cosmetic one: a desk with several assistants
has no governed way to say who is dealing with what, and the obvious
workaround — a free-text note naming a person — is refused by the governed
payload walks.

`FIR-DESK-003` may move to `implemented` only when the lawful basis for
holding a staff-level handling record is decided, when its retention is
decided with it, and when the record is unreachable from every public
projection by construction rather than by classification. `OD-P29-08` is
the open decision.

## FIR-DESK-004 — Governed Evidence Path for Material Arriving from the Public

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** representative desk (PACK-29), documents and evidence (PACK-11), security
- **Target:** a later governed round
- **Dependencies:** FIR-DOC-001, FIR-SEC-SECRET-001, FIR-CASEWORK-001

**Corrected by PACK-29C1.** The original wording of this entry described
PACK-29 as _exposing_ a public intake form. It does not, and did not: the
pack ships the backend capability and no frontend surface for it. There is
no `input`, no `textarea`, no `form` and no writing button on any of the
seven PACK-29 routes, and no client path from any of them to
`submit_intake`. No form was added to make this entry true.

What PACK-29 ships is the **backend** intake capability and its
bounded-input controls, which is the smallest correct thing to build first
because a public intake surface is the one surface an unauthenticated
stranger can reach: `submit_intake` accepts a payload of at most 4096
characters under one of three governed schemas, refuses markup rather than
sanitising it, refuses oversized input rather than truncating it, and has
**no attachment path of any kind**. There is no upload parameter, no
content type, no byte field and no storage for one anywhere in this
service.

That is correct as far as it goes and it is not sufficient for the work.
When a public intake surface is eventually built, a constituent whose case
turns on a letter, a photograph or a decision notice will have nowhere to
put it, and the workaround — pasting a link, or sending it by some other
channel and mentioning it in the text — moves the evidence outside every
governed control this pack has.

`FIR-DESK-004` may move to `implemented` only when material arriving from an
unauthenticated member of the public has a governed evidence path with
declared handling, scanning and retention, when the path is separate from
the published projection by construction, and when the surface — once one
exists — tells the sender what happens to what they sent. `OD-P29-09` holds
the retention half.

## FIR-DESK-005 — Public Representative Activity Measures

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** representative desk (PACK-29), transparency publication (PACK-28), governance
- **Target:** a later governed round
- **Dependencies:** FIR-PUB-001, FIR-LEGAL-001

`DeskActivitySummary` carries counts of governed facts and computes no
rate, ratio, index, percentage or score. The absence is deliberate and is
asserted structurally: no field in `projections.py` is named for one, and
the module contains no division at all.

The reason is that a responsiveness rate, an alignment percentage or an
attendance rate would each become the most-read number on a public
representative surface, and each would be a number this repository computed
about a named person, from data it knows to be incomplete, under a method
nobody agreed to. A desk that received two questions and answered one is
not "50% responsive"; it is a desk with two questions and one answer, and
the difference matters most to the representative whose reputation the
number would carry.

`FIR-DESK-005` may move to `implemented` only when a body with the authority
to set the method has set it, when the method is published alongside every
figure derived under it, when the incompleteness of the underlying data is
stated on the same surface, and when a representative can see and contest
the figure before it is public. `OD-P29-12` is the open decision.

## FIR-LIC-OPS-001 — Open-Core Licensing, Managed Operations and Deployment Boundary

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** repository-wide, licensing, operations, infrastructure, release
- **Target:** a later governed round, before any managed offering exists
- **Dependencies:** FIR-INFRA-SOV-001, FIR-SEC-SECRET-001, FIR-REL-001, FIR-READY-001

This entry is created by **specification** rather than by implementation
discovery, and **nothing in PACK-29 implements any part of it.** No
licence file, no edition flag, no tenancy concept, no billing surface, no
entitlement check and no deployment profile is added by this round, and no
module in `services/representative-desk-service` names one.

What it records is that the repository has begun to look like something an
organisation would want operated for them, and that the questions this
raises have not been asked, let alone answered:

```text
open source code            != freely operable service
managed operation           != product edition
deployment profile          != licence grant
paid support                != governed authority
tenant isolation            != organizational scope isolation
```

The last line is the one most likely to be got wrong quietly. This
repository already has an organizational scope model, and a managed
offering will be tempted to reuse it as a tenancy boundary. They are not
the same thing: a scope is a governance concept describing whose decisions
bind whom, and a tenant is an operational concept describing whose data
shares a process. Conflating them makes every future isolation question
answerable in two incompatible ways.

Four constraints hold in the meantime, and each is already enforced
elsewhere:

- production and customer secrets and configuration stay outside public
  source repositories (`FIR-SEC-SECRET-001`);
- no infrastructure provider is chosen or named in source
  (`FIR-INFRA-SOV-001`), and PACK-29's own governance suite scans for
  provider names on word boundaries;
- release and readiness statements stay honest about what has not been
  independently verified (`FIR-REL-001`, `FIR-READY-001`);
- nothing in this repository may condition a **governed** capability —
  a vote, a publication, an audit read, a right of appeal — on a
  commercial term.

`FIR-LIC-OPS-001` may move to `implemented` only when the licensing model
is decided by the body entitled to decide it, when the boundary between
the open core and any managed operation is stated in the repository rather
than in a sales document, when a deployment profile carries no implied
licence grant, and when the fourth constraint above is enforced by a check
rather than by intention.

## FIR-CONFLICT-001 — Participation-Time Enforcement of Recorded Recusals

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** assembly, deliberation, voting, governance decision, procurement and finance contexts
- **Target:** a later cross-context round; mandatory before any governed decision process is treated as conflict-controlled
- **Dependencies:** FIR-AUTH-001, FIR-CTRL-001, FIR-ID-001, FIR-LEGAL-001

PACK-27 records that a person is restricted from participating in a named
matter. Nothing in this repository consults that record at the moment
participation actually happens.

That gap is the difference between a conflicts register and a conflicts
control. A body may hold an `ACTIVE` recusal, correctly decided by two
principals on cited evidence, and still let the restricted participant
deliberate, chair, prepare the decision or vote — because the context running
the matter never asks.

Hard invariant for the closing round:

```text
active recusal in matter M restricting activity A
  => every context that admits participation in M must refuse A for that subject
```

The enforcement must read the recusal **record** and call
`evaluate_participation`, never a projection: read models lag, and the act most
likely to be decided on a stale one is precisely the act that lets a recused
person take part because a worklist had not caught up.
`assert_projection_is_not_authority` exists so that the attempt is refused by
name rather than quietly satisfied.

Two things this requirement does **not** authorise. It does not permit a
cross-domain person identifier to be introduced in order to match subjects
across contexts — the matching must run through explicitly governed references
for the authorised purpose, and `FIR-ID-001` continues to apply. And it does not
extend to the Voting Client: WS-03 is isolated, holds no persistent member
identity, and receives no conflict record. Whether and how a governed decision
process that runs partly through WS-03 can honour a recusal without breaking
that isolation is part of what the closing round must answer, not something
this entry presumes.

`FIR-CONFLICT-001` may move to `implemented` only when at least one governed
decision context refuses a restricted activity on the strength of a recorded
active recusal, with adversarial tests proving the refusal and proving that a
stale projection cannot satisfy it.

## FIR-CONFLICT-002 — Governed Consumption of Conflict Outcomes by Owning Contexts

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** procurement (PACK-25), office and mandate (PACK-20), people administration (PACK-26), finance
- **Target:** a later cross-context round
- **Dependencies:** FIR-CONFLICT-001, FIR-PROC-003, FIR-VENDOR-001

PACK-27 produces governed conflict and recusal outcomes and owns none of the
consequences. Procurement-service remains the source of truth for procurement
state; PACK-20 holds offices and ends them; PACK-26 administers engagements.
Each of those contexts _may_ consume a conflict outcome through a stable
interface, and none of them currently does.

The interface has to be built from the consuming side, and it has to preserve
the separations in both directions:

```text
conflict finding != vendor rejection
recusal          != procurement decision
recusal          != loss of mandate
conflict finding != office vacancy
recusal          != engagement change
```

The failure this entry exists to prevent is the convenient shortcut: a
consumer subscribes to `conflict.assessment.recorded`, reads `CONFLICT_FOUND`,
and excludes the vendor, vacates the seat or ends the engagement — a
consequence imposed by an inference nobody reviewed, by a register that has no
authority over any of the three. Every event PACK-27 emits already carries
`constitutes_procurement_decision: false`, `constitutes_office_effect: false`
and `constitutes_engagement_effect: false` for exactly this reader.

`FIR-CONFLICT-002` may move to `implemented` only when a consuming context
takes a governed decision of its own that _cites_ a conflict outcome, with the
citation recorded and the consuming decision separately authorised — never when
a subscriber acts on an event.

## Section 37 boundaries

This section does not select an enforcement mechanism, does not require PACK-27
to build one, does not grant PACK-27 authority over any consuming context, and
does not resolve `OD-P27-07`, `OD-P27-08` or `OD-P27-11`. It records that
recording a restriction and enforcing one are different things, and that this
repository currently does only the first.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 38. Emergency Governance and Crisis Controls

Added by PACK-30 (repository `0.32.0`). Every entry below was discovered by
implementing emergency governance rather than anticipated before it, which is
the criterion this register applies: a requirement nobody hit is a guess.

None of these is closed by PACK-30.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

## FIR-EMERG-001 — Organizational Emergency Exercise and Drill Assurance

- **Status:** `approved`
- **Priority:** `high`
- **Scope:** emergency governance (PACK-30), operations, assurance
- **Target:** a later governed round
- **Dependencies:** FIR-OPS-001, FIR-READY-001, FIR-TEST-002

PACK-30 has a complete set of unit tests over its command paths and proves
nothing whatsoever about whether an organization could actually run an
emergency through it. Those are different claims, and the gap between them is
the whole of this entry.

The action `emergency.drill.schedule` and the event
`emergency.drill.scheduled` are both registered and both reserved, and the
reason is a genuine dilemma rather than an omission. A drill that ran through
the real command paths would produce real emergency records — a real
declaration, real measures, real grants, real audit rows — which afterwards
nobody could distinguish from a real crisis, and which would sit in the same
append-only history that has no deletion path. A drill that used a separate
path would exercise the separate path and prove nothing about the one that
matters.

What is missing is the governed distinction: a way to mark a declaration as an
exercise that is trustworthy at read time, that cannot be applied to a real
declaration retroactively, that no public projection can be fooled by, and
that a later audit can rely on. Neither `RecordSensitivity` nor
`LegalEffectStatement` is that field, and adding a boolean would be adding the
weakest possible version of it.

`FIR-EMERG-001` may move to `implemented` only when an exercise is
distinguishable from a real emergency by construction rather than by
classification, when the distinction survives the append-only history, and
when a real organizational exercise has been run and its evidence recorded.
Passing unit tests is not that evidence. `OD-P30-12` is the related open
decision.

## FIR-EMERG-002 — Public Emergency Measures and the Method That Would Govern Them

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** emergency governance (PACK-30), transparency publication (PACK-28), governance
- **Target:** a later governed round
- **Dependencies:** FIR-PUB-001, FIR-LEGAL-001, FIR-DESK-005

`projections.py` computes counts and nothing else. There is no rate, no ratio,
no percentage, no index and no score anywhere in the module, and no division
operator at all; a repository test asserts the absence by parsing for
`ast.Div` rather than by reading the docstring.

The absence is deliberate and it is the same reasoning as `FIR-DESK-005`,
arriving in a domain where it bites harder. A "mean time to recovery", an
"emergency frequency by organizational unit" or a "measure compliance
percentage" would each become the most-read number about a body's handling of
a crisis. Each would be computed by this repository, from data it knows to be
incomplete, under a method nobody agreed to, about a named organizational
unit — and it would be read as an assessment of the volunteers who were there
at three in the morning. A Kreisverband that declared three emergencies in a
year is a Kreisverband that declared three emergencies; it is not "three times
the party average".

The gap is real rather than cosmetic. Oversight legitimately wants to know
whether emergency powers are being used more in some places than others, and
this pack gives them counts per scope and no way to compare across scopes at
all — `refuse_cross_scope_projection` refuses the query by name.

`FIR-EMERG-002` may move to `implemented` only when a body with the authority
to set the method has set it, when the method is published alongside every
figure derived under it, when the incompleteness of the underlying data is
stated on the same surface, and when the organizational unit concerned can see
and contest the figure before it is public. `OD-P30-10` is the open decision.

## FIR-EMERG-003 — External Civil-Protection and Public-Authority Emergency Integration

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** emergency governance (PACK-30), correspondence (PACK-22), integration, legal
- **Target:** a later governed round
- **Dependencies:** FIR-INFRA-SOV-001, FIR-LEGAL-001, FIR-API-001

`emergency.external.authority_notify` is registered and reserved, and so is
`emergency.federation.coordinate`. Neither reaches a command.

Two separate things are missing behind them. The first is legal: whether a
body operating this repository must notify any external authority of an
emergency, which authority, within what period and with what content, is
`OD-P30-10` and is unresolved — and a window encoded for it would imply an
obligation exists. `EXTERNAL_NOTIFICATION_WINDOW` is a reserved, unenforced
deadline kind for exactly that reason.

The second is architectural. There is no authenticated channel to any
Katastrophenschutz authority, any Ordnungsamt or any other public body in this
repository, so a notification act would record that something was sent without
any evidence that it arrived — and `emergency notice created != delivered`,
`delivered != legally served` are the distinctions PACK-22 exists to keep.

Cross-organization coordination is deferred for a third reason, which is not
technical: the first thing such a channel would share is which bodies are
currently in crisis, and that is a map of where the organization is weakest.
Building it before deciding who may read it would be building the map first.

`FIR-EMERG-003` may move to `implemented` only when the notification
obligation is decided, when a governed authenticated channel to a named
authority exists with per-message delivery evidence, and when the read model
for any cross-organization view is decided before the channel is built.

## FIR-EMERG-004 — Emergency Legal Activation Profiles

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** emergency governance (PACK-30), legal, governance
- **Target:** a later governed round
- **Dependencies:** FIR-LEGAL-001, FIR-ROADMAP-011

Every record PACK-30 produces carries `LegalEffectStatement.OPEN`. The other
four members — `NOT_ACTIVATED`, `ACTIVATED`, `SUSPENDED`, `EXPIRED` — exist so
that a future activation has somewhere to put an answer, and
`assert_legal_effect_not_activated` refuses all four today.

This is the entry a reader should be most careful with, because the
implemented behaviour looks the most like the real thing. The service declares
emergencies, records who declared them on what authority, imposes measures,
bounds them in time and reviews them afterwards — and none of it establishes
anything about anybody's legal position. Nothing here is a legally recognised
state of emergency. No measure discharges a duty or creates a power. No
decision recorded here has been reviewed for constitutional legality by
anybody. `emergency measure != legal authority`; `emergency decision !=
constitutional legality`; `implemented != legally activated`.

Four questions have to be answered before any of that changes, and none is a
software question: whether German constitutional, party, parliamentary and
administrative emergency rules apply to a body operating this repository at
all (`OD-P30-01`); which office or organ may lawfully declare which emergency
at which level (`OD-P30-02`); what maximum duration and renewal limits bind it
(`OD-P30-03`); and whether a party-internal declaration has any legal effect
in either direction (`OD-P30-04`, which this repository leaves unresolved in
both directions on purpose, because answering either way would state law it
has no standing to state).

`FIR-EMERG-004` may move to `implemented` only when a competent legal
determination exists per organizational level and per emergency category, when
it is recorded as a governed, versioned activation profile rather than as a
configuration value, when the evidence behind it is referenced from every
record produced under it, and when a record produced before activation is
still readable as having been produced before it. Software configuration does
not create legal authority, and the gap between an activation profile and a
switch is the entire content of this entry.

## Section 38 boundaries

This section does not resolve any of `OD-P30-01` through `OD-P30-12`, does not
require PACK-30 to build any of the four capabilities above, does not grant
PACK-30 authority over any other bounded context, and does not claim that
PACK-30's controls have been exercised in an organization. It records four
things that implementing emergency governance made visible and that this round
deliberately did not do.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 39. Constitutional and Ethics Oversight

Added by PACK-31 (repository `0.33.0`). Every entry below was discovered by
implementing oversight rather than anticipated before it, which is the
criterion this register applies: a requirement nobody hit is a guess.

None of these is closed by PACK-31.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

## FIR-OVERSIGHT-001 — Subject Procedural Rights and the Review of a Finding

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** constitutional and ethics oversight (PACK-31), legal, governance
- **Target:** a later governed round
- **Dependencies:** FIR-LEGAL-001, FIR-CONFLICT-001

PACK-31 can open a case about a person, admit it, assign reviewers, take
evidence, deliberate, finalise a finding and issue a corrective action
without the subject of the review being told that any of it happened. That
is not an oversight. It is the honest consequence of two unresolved
questions, and the pack refuses to answer either by implementing one answer
to it.

`SUBJECT_NOTIFICATION_WINDOW` is a declared, reserved, unenforced deadline
kind (`OD-P31-08`). `APPEAL_WINDOW` is another (`OD-P31-11`).
`oversight.appeal.register` is a registered, reserved action permitted to
nobody, and `oversight.appeal.registered` is a declared, unemitted event
type. `assert_read_authorized` refuses the subject of a review a read of the
case record _by virtue of being its subject_, and names `OD-P31-11` in the
refusal.

Every one of those is a placeholder for the same missing decision: what a
person under review is entitled to. Whether they must be told a case exists,
when, and in what words. Whether they may see the evidence, and which
classes of it. Whether they may see a draft finding before it is final.
Whether they may have a finalised finding reviewed, by whom, on what grounds
and within what period, and what happens to the finding meanwhile.

The gap is real rather than theoretical, and it bites hardest in the case
the pack handles most carefully elsewhere. Supersession exists and is a
governed act _by the body itself_: the subject of a finding has no remedy in
this repository at all. A body that can revisit its own findings and a
subject who cannot ask it to is a body whose corrections happen when it
notices.

Building an appeal path now would answer the question by implementing one
answer to it, and the answer chosen would be the one that was convenient to
build. `FIR-OVERSIGHT-001` may move to `implemented` only when a competent
body has decided what procedural rights attach to being the subject of an
internal review, when the decision is recorded as a governed, versioned
profile rather than as a configuration value, when the notification
obligation and the review right are separable (they are different
decisions), and when a finding produced before the decision is still
readable as having been produced before it. `OD-P31-08` and `OD-P31-11` are
the open decisions.

## FIR-OVERSIGHT-002 — Public Oversight Measures and the Method That Would Govern Them

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** constitutional and ethics oversight (PACK-31), transparency publication (PACK-28), governance
- **Target:** a later governed round
- **Dependencies:** FIR-PUB-001, FIR-DESK-005, FIR-EMERG-002

`projections.py` computes counts and nothing else. There is no rate, no
ratio, no percentage, no index and no score anywhere in the module, and no
division operator at all; a repository test asserts the absence by parsing
for `ast.Div` rather than by reading the docstring.

The absence is deliberate and it is `FIR-DESK-005`'s and `FIR-EMERG-002`'s
reasoning arriving in the domain where it bites hardest. An "Aufhebungsquote",
a "findings per Gliederung" figure or an "ethics compliance score" would each
become the most-read number about a named organizational unit's _conduct_.
Each would be computed by this repository, from data it knows to be
incomplete — a body with three oversight cases may be a body under scrutiny
or a body where people feel able to raise things — under a method nobody
agreed to, about volunteers, and it would be read as a verdict on them.

The gap is real rather than cosmetic. Oversight legitimately wants to know
whether concerns cluster somewhere, and this pack gives counts per scope and
no way to compare across scopes at all: `refuse_cross_scope_projection`
refuses the query by name, and the store offers no unscoped list to build
one from.

`FIR-OVERSIGHT-002` may move to `implemented` only when a body with the
authority to set the method has set it, when the method is published
alongside every figure derived under it, when the incompleteness of the
underlying data is stated on the same surface, and when the organizational
unit concerned can see and contest the figure before it is public.
`OD-P31-17` is the related open decision.

## FIR-OVERSIGHT-003 — External Authority Interaction and the Referral Channel

- **Status:** `approved`
- **Priority:** `medium`
- **Scope:** constitutional and ethics oversight (PACK-31), correspondence (PACK-22), integration, legal
- **Target:** a later governed round
- **Dependencies:** FIR-INFRA-SOV-001, FIR-LEGAL-001, FIR-API-001

`oversight.external.authority_refer` is registered and reserved, and so is
`oversight.federation.coordinate`. `EXTERNAL_REFERRAL_WINDOW` is a declared,
unenforced deadline kind. `AuthorityKind.EXTERNAL_PUBLIC_AUTHORITY` is
declared and refused by `assert_kind_may_carry_authority`, and
`assert_external_authority_not_assumed` refuses borrowing an external
competence by name.

Three separate things are missing behind them. The first is legal: whether a
body operating this repository may refer a matter to a court, a supervisory
authority, a Wahlprüfungsausschuss or a public prosecutor — and whether it
_must_ — is `OD-P31-12` and is unresolved, and a window encoded for it would
imply an obligation exists.

The second is architectural. There is no authenticated channel to any
external authority in this repository, so a referral act would record that
something was sent with no evidence that it arrived. `oversight notice
created != delivered`; `delivered != legally served`. PACK-22 owns the
distinction and this pack does not weaken it.

The third is the one that would be decided by accident. What an external
determination does to an internal finding — whether it supersedes it,
suspends it, or does nothing to it — is a question about the standing of the
internal body, and building the inbound half of the channel before answering
it would answer it.

Cross-organization coordination is deferred for a fourth reason, which is
not technical: the first thing such a channel would share is which bodies
are currently under review, and that is a map of where an organization is
most exposed. Deciding who may read it comes before building it.

`FIR-OVERSIGHT-003` may move to `implemented` only when the referral
question is decided, when a governed authenticated channel to a named
authority exists with per-message delivery evidence, when the effect of an
external determination on an internal finding is decided, and when the read
model for any cross-organization view is decided before the channel is
built.

## FIR-OVERSIGHT-004 — Oversight Legal Activation Profiles

- **Status:** `approved`
- **Priority:** `critical`
- **Scope:** constitutional and ethics oversight (PACK-31), legal, governance
- **Target:** a later governed round
- **Dependencies:** FIR-LEGAL-001, FIR-ROADMAP-011, FIR-EMERG-004

Every record PACK-31 produces carries `LegalEffectStatement.OPEN`. The other
four members exist so that a future activation has somewhere to put an
answer, and `assert_legal_effect_not_activated` refuses all four today.

This is the entry a reader should be most careful with, because the
implemented behaviour looks the most like the real thing. The service takes
review requests, decides admissibility against a governed competence,
assigns independent reviewers, consumes conflict outcomes, takes evidence,
deliberates under a quorum, records findings with dissenting opinions,
issues corrective actions and verifies them independently — and none of it
establishes anything about anybody's legal position. Nothing here is a
constitutional review in any sense a court would recognise. No finding
suspends, invalidates or requires the reconsideration of anything. No
recommendation obliges anybody. `finding != binding determination`;
`software finding != court judgment`; `implemented != legally activated`.

Five questions have to be answered before any of that changes, and none is a
software question: whether German constitutional, party, parliamentary and
administrative rules apply to compatibility review by a body operating this
repository at all (`OD-P31-01`); who is legally competent to perform which
review (`OD-P31-02`); whether an internal finding has any legal effect
(`OD-P31-03`, which this repository leaves unresolved in _both_ directions
on purpose, because answering either way would state law it has no standing
to state); whether a finding may suspend or invalidate a decision
(`OD-P31-04`); and what authority, if any, would permit a finding to produce
a consequence for a person's office, mandate, employment or contract
(`OD-P31-05`).

`FIR-OVERSIGHT-004` may move to `implemented` only when a competent legal
determination exists per organizational level and per review category, when
it is recorded as a governed, versioned, evidence-backed activation profile
rather than as a configuration value, when the evidence behind it is
referenced from every record produced under it, and when a record produced
before activation is still readable as having been produced before it.
Binding effect would additionally have to be action-specific,
policy-specific, organization-scoped and authority-backed: the gap between
an activation profile and a switch is the entire content of this entry.

## FIR-OVERSIGHT-005 — Machine-Assisted Analysis as Governed Oversight Evidence

- **Status:** `approved`
- **Priority:** `low`
- **Scope:** constitutional and ethics oversight (PACK-31), AI processing (PACK-06), governance
- **Target:** a later governed round
- **Dependencies:** FIR-DATA-004, FIR-LEGAL-001

`oversight.ai.assisted_analysis_attach` is a registered, reserved action
permitted to nobody. Every determining act in this service is in
`HUMAN_ONLY_ACTIONS`, and an automated agent is refused before any authority
is resolved.

`AI analysis != oversight finding`; `AI recommendation != constitutional
determination`. The reservation is not a position on whether machine
analysis is useful — sifting a large body of governed records is exactly
what it is good at, and an oversight body reviewing a year of decisions has
a large body of governed records. The reservation is that attaching it as
evidence needs three things this repository does not have: a provenance
model that records which model, which version and which inputs produced an
output; a versioning model that survives the model being retrained; and a
contestability model that lets the subject of a finding challenge an input
they cannot read.

Without the third, a finding partly resting on machine analysis is a finding
its subject cannot argue with, which is a worse position than one they
disagree with.

`FIR-OVERSIGHT-005` may move to `implemented` only when machine-assisted
analysis is a governed, versioned, provenance-carrying evidence class with
its own authenticity semantics, when it is distinguishable from human
analysis at read time and in every projection, when a human authorised
reviewer's determination is required and recorded separately from it, and
when the subject of a finding can contest it. `OD-P31-14` is the open
decision.

## Section 39 boundaries

This section does not resolve any of `OD-P31-01` through `OD-P31-18`, does
not require PACK-31 to build any of the five capabilities above, does not
grant PACK-31 authority over any other bounded context, and does not claim
that PACK-31's controls have been exercised by an organization. It records
five things that implementing constitutional and ethics oversight made
visible and that this round deliberately did not do.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 40. Program Formation and Deliberation Intelligence

PACK-32 implements governed programme formation and assistive deliberation
intelligence: the programme container and its sections, ideas, proposals,
procedural admissibility, amendments, governed links into the deliberation
context, machine-assistance artefacts with provenance and human review,
syntheses that must carry their minority positions, similarity suggestions
that merge nothing, support signals that are structurally not ballots,
candidate programme versions, adoption bound to a governed external decision
reference, immutable adopted versions, supersession, reopening and
publication candidacy through PACK-28.

The five entries below are what implementing that made visible and what this
round deliberately did not do. None is implemented. Each names the open
decision it depends on where there is one.

## FIR-PROGRAM-001 — Production Model Provenance and Attestation for Political Assistance

- **Status:** `captured`
- **Priority:** `critical`
- **Scope:** model identity, model version, hosting location, weights
  provenance, inference-time attestation for any machine assistance used in a
  consequential programme step
- **Target:** before any production activation of assisted deliberation
- **Dependencies:** PACK-06, FIR-INFRA-SOV-001, FIR-SEC-SECRET-001, PACK-32

PACK-32 requires an `AssistanceProvenance` on every artefact — model
reference, model version, policy reference, output version and processing
record — and fails closed when any is unknown. That is a _structural_
requirement satisfied by a string.

What it does not establish is that the string is true. Nothing in this
repository verifies that the model named is the model that ran, that its
weights are the weights that were reviewed, that inference happened in the
jurisdiction the organization believes, or that the output was not altered
between generation and recording.

For a summariser of political discussion, the gap matters more than for most
workloads: a substituted model that summarises slightly differently is
indistinguishable from a correct one at read time, its output is reviewed by
somebody who cannot compare it to what the reviewed model would have said,
and the artefact records the name of a model that never ran.

`FIR-PROGRAM-001` may move to `implemented` only when model identity and
version are attested rather than asserted, when weights provenance is
verifiable, when inference location is established, and when an
independently checkable binding exists between an artefact and the inference
that produced it. `OD-P32-11` is the open decision.

## FIR-PROGRAM-002 — Political Bias Evaluation for Assisted Summarisation

- **Status:** `captured`
- **Priority:** `critical`
- **Scope:** systematic evaluation of whether machine summarisation of
  political deliberation treats positions, factions, registers and dialects
  evenly
- **Target:** before any production activation of assisted deliberation
- **Dependencies:** PACK-06, PACK-32, FIR-PROGRAM-001

PACK-32 requires a synthesis carrying opposing arguments to carry the
minority positions they represent, and checks it against the discussion
rather than against itself. That catches a summary which omits the minority
entirely. It does not catch the failure that actually occurs.

A summariser can include every minority position and still systematically
render one side's arguments in weaker language, compress the more
technically-worded contributions, favour the register of whoever writes most
like the training distribution, or reliably place one faction's points last.
Every individual output is defensible. The aggregate is a thumb on the scale
that nobody can point to, applied to a party's internal argument, by a
component the participants were told is neutral.

The evaluation cannot be a checklist. It requires a corpus of real
deliberation with known positions, a measurement method agreed before the
results are seen, evaluators who are not the operators, and a published
result — including when the result is that a difference was found and not
explained.

`FIR-PROGRAM-002` may move to `implemented` only when such an evaluation
exists, has been repeated on the model version actually in production, and
has an accepted threshold below which assistance is withdrawn rather than
disclosed. `OD-P32-11` is the open decision.

## FIR-PROGRAM-003 — Independent Deliberation Fairness Assessment

- **Status:** `captured`
- **Priority:** `high`
- **Scope:** independent assessment of whether the programme process as
  operated gives comparable access to members regardless of time, fluency,
  digital confidence, seniority and organizational position
- **Target:** before Architecture Baseline 1.0
- **Dependencies:** PACK-32, PACK-03, FIR-MOBILE-001

Every control in PACK-32 is about what the _software_ may do. None of them
measures what the process does to people.

A programme process can satisfy every invariant in this pack and still be one
in which proposals from members who write well, have evenings free and know
the procedure reach deliberation, and proposals from everybody else do not.
The software would record that outcome as a series of correct procedural
acts, and the register of admitted proposals would look like a record of what
the membership thinks.

This requires assessment by somebody who is not the organization operating
it, of the process as actually run rather than as designed, with attention to
who did not participate.

`FIR-PROGRAM-003` may move to `implemented` only when such an assessment has
been performed on a real programme cycle, its method is published, and the
organization has recorded what it changed in response.

## FIR-PROGRAM-004 — Manipulation Resistance for Any Programme Ordering

- **Status:** `captured`
- **Priority:** `high`
- **Scope:** disclosure, bounded inputs, gaming resistance and non-profiling
  assurance for any ordering applied to a list of political proposals
- **Target:** before any relevance ordering is offered in production
- **Dependencies:** PACK-32, PACK-34, FIR-CTRL-001

PACK-32 offers four orderings — chronological, recently active, structurally
related and participant-selected — each with a disclosure sentence, and a
neutral view a participant can always reach. It offers no relevance ordering
and `program.ranking.algorithmic_relevance` is registered and unwired.

That is the safe position and it is not a permanent one: at scale, a
chronological list of thirty thousand proposals is not navigable, and the
pressure to order by something will be real and reasonable.

Ordering decides what gets read. An ordering that can be influenced by
coordinated support signals, by resubmission timing, by contribution volume
or by any per-participant attribute is a mechanism for deciding what the
party discusses, operated by whoever understands it best. The assurance
required is not "the algorithm is disclosed": it is that the inputs are
bounded and enumerable, that no per-person attribute is among them, that
coordinated behaviour cannot move an item materially, and that the unordered
view remains reachable in one action.

`FIR-PROGRAM-004` may move to `implemented` only when an ordering has been
specified with enumerated bounded inputs, adversarially tested against
coordinated manipulation, and shown to use no participant profile. PACK-34
remains the owner of delegation anti-gaming; this entry is about programme
ordering specifically. `OD-P32-04` is the open decision.

## FIR-PROGRAM-005 — Multilingual Programme Equivalence

- **Status:** `captured`
- **Priority:** `medium`
- **Scope:** the relationship between language versions of an adopted
  programme text, and who is competent to establish it
- **Target:** before any multilingual programme publication
- **Dependencies:** PACK-32, PACK-28, PACK-11

PACK-32 permits machine translation as an assistance purpose, for reading.
It does not permit a translated text to be adopted text, and
`program.multilingual_equivalence.certify` is registered and unwired.

The question this defers is not technical. Two language versions of a
political programme are two texts, and whether they say the same thing is a
political judgement about wording that people argued over — often about the
exact word that does not translate. If both are published, a reader in each
language takes theirs to be the programme. If a discrepancy is later found,
which one the organization adopted is a question nobody prepared for.

`FIR-PROGRAM-005` may move to `implemented` only when the organization has
determined which language version is authoritative, who establishes
equivalence, what happens when a discrepancy is found in an adopted version,
and how a published translation is labelled so that a reader knows which they
are reading. `OD-P32-06` is the open decision.

## Section 40 boundaries

This section does not resolve any of `OD-P32-01` through `OD-P32-12`, does
not require PACK-32 to build any of the five capabilities above, does not
grant PACK-32 authority over any other bounded context, and does not claim
that PACK-32's controls have been exercised by an organization. It records
five things that implementing programme formation and assistive deliberation
made visible and that this round deliberately did not do.

It closes no entry in section 39, no entry under `FIR-CONFLICT-001` or
`FIR-CONFLICT-002`, and nothing under `FIR-VOTE-CRYPTO-001`, whose VCRYPTO-01
entry gate at sections `1.59.1`–`1.59.12` remains future scope.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 41. Citizen Office Routing and No-Wrong-Door Caseflow

Added by PACK-33 (repository `0.35.0`). Every entry below was discovered by
implementing the routing context and finding a question the implementation
could not answer for itself. None is implemented, and none is scheduled by
this round.

## FIR-ROUTING-001

**Title:** Authoritative competence directory for citizen matters
**Status:** `open`
**Origin:** PACK-33 implementation discovery
**Relates to:** `OD-P33-02`

There is no authoritative statement anywhere in this repository of which
office is competent for which subject in which Gliederung. PACK-33 routes
against a typed target chosen by a named human, and
`RESOLVE_COMPETENCE_FROM_DIRECTORY` is registered and unwired precisely
because resolving competence against a list somebody maintained locally
would make a guess look like a determination. What a competence directory
is, who maintains it, how it is versioned and what happens to matters routed
under a superseded version are all unresolved.

## FIR-ROUTING-002

**Title:** The complaint and petition owning domain
**Status:** `open`
**Origin:** PACK-33 implementation discovery
**Relates to:** `FIR-CONFLICT-001`, `FIR-CONFLICT-002`

PACK-33 can classify a matter as a complaint or petition _candidate_ and can
request a conversion towards a complaint domain. That domain does not exist.
`FUTURE_COMPLAINT_OR_PETITION_CONTEXT` is an unreachable target kind and a
conversion request towards it has no acceptance to read, so it sits visibly
in `REQUESTED`. This is the honest state and it is not a design: what a
complaint case is, who adjudicates it, what rights a complainant has and how
`complaint != appeal != initiative != whistleblowing` is enforced across
them all remain future scope.

## FIR-ROUTING-003

**Title:** Cross-scope routing policy and organizational containment
**Status:** `open`
**Origin:** PACK-33 implementation discovery
**Relates to:** `OD-P33-03`

Bund, Land and Kreis are isolated in the data model and PACK-33 keeps them
so: ordinary routing refuses a target in another scope, and cross-scope
movement is a two-principal act at high assurance with its own purpose
basis. What is unresolved is whether a containing level ever acquires a
contained level's matters, under what conditions, and what a sender is told
when their matter leaves the Gliederung they wrote to.

## FIR-ROUTING-004

**Title:** Legal basis for transfer of citizen data between party offices
**Status:** `open`
**Origin:** PACK-33 implementation discovery
**Relates to:** `OD-P33-04`, `OD-P33-01`

Three transfer bases are activated in this repository — sender request,
explicit sender consent, organizational internal coordination.
`STATUTORY_OBLIGATION` and `PUBLIC_TASK` are recordable and are refused as
not activated, because whether a political party's citizen office performs a
public task in the sense a transfer basis requires is a legal question this
service has no standing to answer. The same gap covers statutory response
periods: none is encoded, named German periods are refused by name, and the
absence of one here is not a finding that none applies.

## FIR-ROUTING-005

**Title:** Citizen remedy against a routing decision
**Status:** `open`
**Origin:** PACK-33 implementation discovery
**Relates to:** `OD-P33-11`, `OD-P33-05`

A citizen whose matter was sent somewhere they think is wrong has, in this
round, no recorded way to say so. `RECORD_CITIZEN_ROUTING_APPEAL` and
`CITIZEN_APPEAL_PERIOD` are both registered and unwired, and building either
before the remedy exists would create an appeal nobody has to answer. What
remedy exists, who hears it, within what period and what the sender may be
told about the internal reasoning are unresolved together.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 42. Delegation Reputation and Anti-Gaming

Added by PACK-34 (repository `0.36.0`). Every entry below was discovered by
implementing the delegation reputation context and finding a question the
implementation could not answer for itself. None is implemented, and none is
scheduled by this round.

## FIR-DELREP-001

**Title:** Competence to activate an anti-gaming rule
**Status:** `open`
**Origin:** PACK-34 implementation discovery
**Relates to:** `OD-P34-02`, `OD-P34-03`, `FIR-DEL-001`

PACK-34 defines six anti-gaming rules and activates none. Activation
requires a governed authority reference and no organ in this repository is
recorded as competent to give one, so `ActivationAuthorityPort` has no
implementation and every activation attempt is refused. Activating a rule
decides what the party watches for in its own members' behaviour, which is
not a configuration value. Which body holds that competence, whether it is
the same body in every Gliederung, and what a member may be told about which
rules are running are unresolved together.

## FIR-DELREP-002

**Title:** Governed thresholds and the minimum population for disclosure
**Status:** `open`
**Origin:** PACK-34 implementation discovery
**Relates to:** `OD-P34-04`, `OD-P34-05`, `OD-P34-07`, `FIR-DEL-001`

Two numbers are missing and both are load-bearing. No threshold profile
exists that a governed evaluation would accept — the only one shipped is
named `EPD2-TESTONLY-NOTGOVERNED-P34-THRESHOLDS-1` and is refused — and
`GOVERNED_DISCLOSURE_FLOOR` is `None`, so every figure classed
`SUPPRESSED_PENDING_FLOOR`, including the central concentration share, is
withheld rather than shown against a guessed number. "More than a third of a
Gliederung's delegations with one person is worth a look" and "suppress below
five participants" are both plausible sentences and both party-constitutional
or data-protection judgements. A default in either place would have become
the policy because somebody typed it.

## FIR-DELREP-003

**Title:** Telling a participant that a signal names them, and who reviews it
**Status:** `open`
**Origin:** PACK-34 implementation discovery
**Relates to:** `OD-P34-08`, `OD-P34-10`, `OD-P34-11`, `FIR-DEL-001`

Contestability is a complete mechanism in PACK-34 and is unreachable in
practice by the person it is for. A signal nobody may see cannot be contested
by its subject; telling somebody a rule flagged them is a serious act with no
procedure behind it. `PARTICIPANT_NOTIFY_OF_SIGNAL` is registered and
unwired for exactly that reason. Who is competent to review a contested
signal is separately unresolved — the service refuses the one obvious
answer, the operator who produced the analysis, and names no other.

## FIR-DELREP-004

**Title:** Retention of derived political-behaviour data
**Status:** `open`
**Origin:** PACK-34 implementation discovery
**Relates to:** `OD-P34-12`

Storage is append-only and nothing expires. Source references, factual
metrics, analytical signals, reviews, participant explanations and public
projections each have a different retention argument and no round has made
any of them. A running deployment accumulates a permanent record of how
delegation moved in every scope, and a lawful erasure request has nowhere to
happen. `ANALYSIS_EXPORT` is registered and unwired for the same reason: with
no retention policy and no export classification, an export is a political
profile in a file.

## FIR-DELREP-005

**Title:** When a signal may trigger another domain's governed review
**Status:** `open`
**Origin:** PACK-34 implementation discovery
**Relates to:** `OD-P34-13`

`SIGNAL_ESCALATE_TO_GOVERNED_REVIEW` is registered and unwired. The moment a
signal can open a case in another domain, detection has become enforcement
through a referral — and the referral is the step nobody would review,
because each end can point at the other. Whether such a path should exist,
what threshold of human judgement it requires, and what the receiving domain
is told and not told are unresolved.

## FIR-DELREP-006

**Title:** Repository-wide governance of payload marker sets
**Status:** `open`
**Origin:** PACK-34 implementation discovery, from a defect found in PACK-33
**Relates to:** `FIR-CTRL-001`

Nine services now maintain a list of payload key names their governed walks
refuse — ballot and voting material, secrets, special categories, universal
person identifiers. Each list is written and maintained by hand, per service,
and nothing checks that one is a superset of the repository-wide vocabulary.
The gap was found rather than reasoned about: `citizen-office-routing-service`
was missing `ballot_content`, a marker eight other services already refused,
and no control noticed. What the shared vocabulary is, where it lives, and
how a service declares a justified departure from it are unresolved.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 43. Lobbying Disclosure and External Influence Transparency

Added by PACK-35 (repository `0.37.0`). Every entry below was discovered by
implementing the lobbying disclosure context and finding a question the
implementation could not answer for itself. None is implemented, and none is
scheduled by this round.

More of these are legal questions than in any earlier section. Who must
disclose, above what value, within what period and with what exemptions are
questions German party and parliamentary law has views about, and a
developer's default in any of them would be a legal position taken by
typing.

## FIR-LOBBY-001

**Title:** Which roles carry a disclosure obligation
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-01`

Nine subject kinds are enumerated and none of them is declared obliged.
Representatives and office-holders are the obvious answer and the obvious
answer is incomplete: party staff, advisers, candidates and committee
members all have plausible claims to be in or out, and each is a governance
decision rather than a modelling one. `subject_obligation.determine` is
registered and unwired for this reason, and every determination that
somebody was obliged to declare something is blocked behind it.

`FIR-LOBBY-001` may move to `implemented` only when the party's own
constitutional documents state which roles are subject to a disclosure
obligation, and the enumeration in `subjects.py` can be checked against
them.

## FIR-LOBBY-002

**Title:** Monetary and material disclosure thresholds
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-02`, `OD-P35-03`

"A gift above thirty-five euro must be declared" is a plausible sentence and
a live question in German party law. The only materiality profile PACK-35
ships is named `EPD2-TESTONLY-NOTGOVERNED-P35-MATERIALITY-1`, carries
`is_governed=False`, and is refused in any governed determination. Every
benefit value band therefore reads `BAND_UNRESOLVED`, and the value rule
`DR-P35-003` is defined and never evaluated.

Setting the thresholds too broadly turns every constituent letter into a
register entry; too narrowly and organized influence stays invisible. Both
failures are governance failures, which is why neither is a default.

`FIR-LOBBY-002` may move to `implemented` only when a competent body has set
the thresholds and a governed profile exists to carry them.

## FIR-LOBBY-003

**Title:** Competence to activate, suspend or retire a disclosure rule
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-04`, `FIR-LOBBY-002`

All six materiality rules ship `DEFINED`. Activation requires a governed
authority reference and no organ in this repository is recorded as competent
to give one, so `ActivationAuthorityPort` has no implementation and
`UnresolvedActivationAuthority` refuses. Activating a rule sets the party's
transparency obligations, and a default implementation returning a plausible
authority would put that competence wherever the first deployment left it.

This is the same shape as `FIR-DELREP-001` and it is a separate entry
because the competence is a different one: setting what must be disclosed is
not the same act as setting what may be detected.

`FIR-LOBBY-003` may move to `implemented` only when the party's own
constitutional documents record who holds it.

## FIR-LOBBY-004

**Title:** Whether an individual subject may be named in a public register
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-15`, `OD-P35-06`

The single most consequential question in the pack. A register of
organizations that sought influence is useful; a register naming the people
they met is more useful and is a public statement about individuals. The
public projection names every field it includes, and the choice of that list
is a policy this round did not make.

`INDIVIDUAL_SUBJECT_KINDS` exists so that "the Kreisverband met a trade
association" is not treated with the caution "a named member met one"
requires, and the distinction is available to whoever decides.

`FIR-LOBBY-004` may move to `implemented` only when the members' assembly
and the data protection function have decided, and the projection's field
list can be checked against that decision.

## FIR-LOBBY-005

**Title:** What makes a disclosure eligible to be offered for publication
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-07`, `FIR-LOBBY-004`

Verification is necessary and plainly not sufficient. Whether this class of
fact about this class of person belongs in a public register is the
question, and it has a different answer for a minister and for a local
treasurer. `PublicationEligibility` starts `UNRESOLVED`, no command in this
repository moves it, and so nothing reaches `ELIGIBLE_AS_CANDIDATE`. The
offer mechanism is complete and the gate is shut.

`FIR-LOBBY-005` may move to `implemented` only when the publication
authority under PACK-28 has stated the criteria.

## FIR-LOBBY-006

**Title:** Handling of third-party allegations and who may read one
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-08`, `OD-P35-16`

An allegation is recorded, referred or closed without referral, and who may
read one before it is referred is unresolved. Too open and the register
becomes a rumour store; too closed and nobody can act on a real report.
`allegation.refer` and the `ALLEGATION_REFERRED` event are both reserved,
because a referral path that is too easy turns a register into an accusation
pipeline and one that is too hard leaves a reviewer with nowhere to send
something serious.

`FIR-LOBBY-006` may move to `implemented` only when the data protection
function and the complaint domain have agreed the access model and the
receiving domain has agreed the referral contract.

## FIR-LOBBY-007

**Title:** Retention for each class of disclosure record
**Status:** `open`
**Origin:** PACK-35 implementation discovery
**Relates to:** `OD-P35-12`

Source references, disclosures, allegations, reviews, corrections, responses
and public projections each have a different retention argument, and a
public register has an additional one: how long an entry about a former
office-holder stays visible. Storage is append-only and nothing expires,
which is a property this round records as a problem rather than a feature.
`disclosure.export` is reserved for the same reason: with no retention
policy, an export of a lobbying register is a set of contact histories about
named people in a file.

`FIR-LOBBY-007` may move to `implemented` only when the data protection
function has set a retention policy per record class and a mechanism exists
to apply it without making the register editable.

## Section 43 boundaries

This section does not resolve any of `OD-P35-01` through `OD-P35-16`, does
not require PACK-35 to build any of the seven capabilities above, does not
grant PACK-35 authority over any other bounded context, and does not claim
that PACK-35's controls have been exercised by an organization. It records
seven things that implementing lobbying disclosure made visible and that
this round deliberately did not do.

It closes no entry in any earlier section, advances no entry under
`FIR-DEL-001`, `FIR-PROGRAM-004` or `FIR-DELREP-001` through
`FIR-DELREP-006`, and nothing under `FIR-VOTE-CRYPTO-001`, whose VCRYPTO-01
entry gate at sections `1.59.1`–`1.59.12` remains future scope.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

# 44. Unified Control Plane and Administration Architecture

Added by CTRL-01 (repository `0.38.0`). Every entry below was discovered by
consolidating the administration and authority architecture and finding a
question the consolidation could not answer for itself. None is implemented,
and none is scheduled by this round.

Numbering starts at 101 because `FIR-CTRL-001` and its neighbours already
exist in section 1.36 with a different meaning. Nothing historical is
renamed or deleted.

More of these are staffing and governance questions than in any service
section. Who may hand out administrative access, how many people a
Kreisverband can put on a two-principal act, and whether a privileged
workstation is affordable are questions about how the party is run, and a
developer's default in any of them would become policy by shipping.

## FIR-CTRL-101

**Title:** Competent role-assignment authorities, per organizational scope
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-01`, `OD-CTRL-09`

CTRL-01 refuses the answers that cannot be right — the subject, the
proposer, and anybody holding an incompatible role — and names no body that
is right. No role assignment can reach `APPROVED` without a named approving
body, so the lifecycle is complete and nothing moves through it.

`FIR-CTRL-101` may move to `implemented` only when the party's
constitutional documents record which body approves an assignment at each
organizational level.

## FIR-CTRL-102

**Title:** The production assurance requirement for each profile
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-02`, `OD-CTRL-05`

Nine assurance profiles are designed and none is legally required of
anybody; all ship `DEFINED`. Requiring a hardware token or a privileged
workstation is a purchasing and staffing decision before it is a security
one, and a repository that required one would have made both.

## FIR-CTRL-103

**Title:** Which acts require maker/checker in production
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-03`

Twelve rules are written from the shape of the act. Whether a Kreisverband
with four active members can staff two principals for each of them is a
question about the party rather than about the software, and a rule that
cannot be staffed is one that gets bypassed.

## FIR-CTRL-104

**Title:** Physical or logical separation for high-risk roles
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-04`, `OD-CTRL-05`

Separate account, separate browser profile, separate workstation, privileged
access workstation and dedicated offline device are five different costs and
five different guarantees. CTRL-01 models the separation as logical and says
so, rather than inventing a hardware requirement.

## FIR-CTRL-105

**Title:** The break-glass approval chain and its out-of-band recipient
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-06`, `OD-CTRL-07`, `OD-CTRL-15`

`SOD-CTRL-015` is the only `CONDITIONAL` rule in the separation matrix, and
it is conditional because a rule that cannot be satisfied at three in the
morning is a rule that gets bypassed, while one that can always be satisfied
by one person is not a rule. `assert_out_of_band_recipient` fails closed
until a recipient is configured.

## FIR-CTRL-106

**Title:** The maximum duration of a temporary elevation
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-08`

Eight hours is a developer's number and is enforced as a refusal rather than
offered as a policy. The governed one depends on shift patterns nobody has
told this repository about.

## FIR-CTRL-107

**Title:** Which body activates an authority, and on what evidence
**Status:** `open`
**Origin:** CTRL-01 consolidation discovery
**Relates to:** `OD-CTRL-13`

The most consequential entry in this section. An authority is what makes an
act legitimate, and all eleven records ship `DEFINED` because a repository
that activated one would have created the competence it exists to record.
As shipped, the control plane records competences and confers none.

## Section 44 boundaries

This section does not resolve any of `OD-CTRL-01` through `OD-CTRL-16`, does
not require CTRL-01 to build any of the seven capabilities above, does not
grant CTRL-01 authority over any bounded context, and does not claim that
CTRL-01's controls have been exercised by an organization.

It closes no entry in any earlier section, advances nothing, and touches
nothing under `FIR-VOTE-CRYPTO-001`, whose VCRYPTO-01 entry gate at sections
`1.59.1`–`1.59.12` remains future scope. TFCAR and PRDCI research entries
are unchanged and non-blocking.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

---

## V24 governance maintenance record — Reconciliation of the canonical V23 register onto the accepted maintenance line (2026-08-29)

**Why this level exists.** The canonical V23 register and the register packaged in the accepted API-01 C5 baseline were two lines, not one. V23 carried the V17–V23 governance additions; the accepted line carried the API-01 C3 reconciliation and everything after it. Neither contained the other. Measured against each other, V23 was missing 81 FIR headings and 59 numbered sections, including `FIR-AUTH-001` — the requirement API-02 implements — and including `FIR-UX-012` and `FIR-UX-013`, which the V23 Program Control Register's own maintenance-level sentence states its Master includes. A register that does not contain what its control register says it contains cannot be the authority a candidate seals against, and API-02 C5 stopped rather than seal against it.

**What this level is.** The accepted line, whole, with every legitimate V23 addition and refinement merged into it. It is a superset of both inputs by construction and by measurement: the verification below is regenerable and is what this record rests on.

### How each part was decided

| Decision                                | Count | What it means                                                                                                                       |
| --------------------------------------- | ----: | ----------------------------------------------------------------------------------------------------------------------------------- |
| Carried from the accepted line verbatim |    18 | Top-level sections the V23 register did not contain at all: 29A, 29B, 29C and 30–44. Restored whole, with their FIR entries.        |
| Added from the canonical V23 register   |    16 | Blocks present only in V23: the V21, V22 and V23 governance maintenance records and the new FIR entries they introduce.             |
| Union of both                           |     6 | Blocks where V23 adds material and removes none; the result carries every line of both.                                             |
| V23 text taken as the newer requirement |     2 | Genuine V17–V23 strengthenings that rewrite a requirement's text. Named individually below, because rule 4 forbids a silent change. |
| Accepted text kept over V23             |    11 | Blocks where the V23 text is older or is a restyle. Named individually below.                                                       |

### The two requirements whose text V23 strengthened

- **FIR-UX-003 — EPD² Design System and Component Governance** (section 28): V23 strengthens the design-system baseline from 'authoritative visual reference' to 'canonical, immutable FRONT-00/FRONT-01 implementation baseline' and widens what it covers.
- **FIR-UX-010 — Design Evidence and Frontend Acceptance** (section 28): V23 tightens the acceptance classification: reuse, or extend-with-canonical-tokens only where no existing component suffices, and a replacement needs an approved Design Change Decision.

One subsection is superseded by that second change and is named here rather than left to be noticed: `FIR-UX-010`'s **Visual continuity rule** — "Existing pages are a reference baseline, not an immutable pixel freeze. Improvements are permitted where justified, but an unrelated redesign is not." — is replaced by the V23 requirement that any visual-baseline modification reference an already approved Design Change Decision. The two cannot both stand: one permits a justified improvement without a prior decision and the other requires one. The stricter V23 rule is taken, and the superseded sentence is recorded here so the change is a governed one rather than a heading that quietly stopped existing.

### The blocks where the accepted text was kept

Six of these are markdown emphasis restyles (`_x_` to `*x*`) and two are a dropped horizontal rule. The three that matter are substantive, and each is a case of the V23 line never having received a later governed round:

- **FIR-BASE-001 — Current repository baseline** (section 2): V23 baseline pointer is PACK-15 / 0.15.0, six rounds behind the accepted PACK-31 / 0.28.0 pointer.
- **FIR-DEL-001 — Delegation Reputation** (section 17): V23 downgrades status partial -> captured and drops the 31 lines recording PACK-34's implementation and its three FIR-DELREP cross-references.
- **FIR-ID-001 — No Universal User Identifier** (section 24): V23 drops the cross-reference to section 29B, a section V23 does not carry.

### The round records that were renumbered, and why

The V23 line numbered its documentation-only records `1.28`–`1.34` while the accepted line was already using those numbers for the PACK-17 round records. Rule 4 protects the numbers that already exist, so the incoming records move to the next free values after `1.67`. This register has done exactly this before and recorded it: the V15/V16 additions were "numbered 1.60 and 1.61 in the standalone V16 copy, renumbered here because those numbers were already taken by repository round records".

| V23 number | number in this register                                                                                         |
| ---------- | --------------------------------------------------------------------------------------------------------------- |
| `1.28`     | `1.68` — Documentation-only correction — Canonical frontend visual baseline lock (2026-08-25)                   |
| `1.29`     | `1.69` — Documentation-only refinement — Regional/local frontend operating model (2026-08-25)                   |
| `1.30`     | `1.70` — Documentation-only refinement — DE/EN frontend language model (2026-08-26)                             |
| `1.31`     | `1.71` — Documentation-only update — Governed AI Correspondence Analysis & Reply Drafting (2026-08-27)          |
| `1.32`     | `1.72` — Documentation-only refinement — FIR-AI-003 Implementation Placement Matrix (2026-08-27)                |
| `1.33`     | `1.73` — Documentation-only update — Regional Authority Suspension & Intervention Control (2026-08-27)          |
| `1.34`     | `1.74` — Documentation-only update — Governed Access, Credential & Key Authority Lifecycle Control (2026-08-28) |

They are placed before `FIR-BASE-001` rather than after it. `FIR-BASE-001` is the register's current-state block and belongs last; `check_register_freshness` reads the baseline pointer as everything from that heading onwards, and a round record inserted after it would cut that window short and make a current register read as stale.

### What this record does not do

It closes no requirement, moves no status forward and accepts no candidate. It reconciles two governance lines into one and says exactly how. `FIR-DEL-001` keeps the `partial` status the accepted line records; the V23 register's `captured` is treated as the regression it is rather than as a governed downgrade. Any deliberate downgrade remains available to governance as its own decision, recorded as one.

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. NOT A BINDING VOTE.**

---

## V24 governance maintenance record — Open Trust Core & Commercial Operations Boundary (2026-08-29)

**Round:** documentation/governance only. No software is relicensed, published, privatized, deployed, certified or legally activated by this update. No API, INFRA, OPS, CTRL, FRONT, SEC, PILOT, PACK-16 or PACK-17 status is accepted or closed.

**New FIR ID created:** `FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary` — status `approved`, priority `critical`.

**Governed model artifact:** `docs/governance/EPD2_OPEN_TRUST_CORE_COMMERCIAL_OPERATIONS_BOUNDARY_0.1.md`.

**Core decision:** EPD² adopts an Open Trust Core boundary. Protocol specifications, verification-relevant cryptography/reference code, canonical encoding/test vectors, minimal reference voting client, independent verifier, key/guardian ceremony protocol and reference tooling, election-record/finalization semantics, public audit-evidence integrity semantics and reproducible verification remain publicly inspectable. Commercial value may be created around managed deployment, orchestration, enterprise/admin/guardian UX, HA/resilience, HSM/KMS and government integrations, observability, compliance operations, hardened/certified distributions, SLA and professional services only where those components are not required to establish cryptographic truth or independent verification.

**Licensing:** `FIR-OSS-001` remains controlling: the intended original-project software licence baseline is `EUPL-1.2`, subject to the existing legal-review gate. This update does not select Apache-2.0, does not relicense existing source and does not declare any EUPL-covered code proprietary. Any future proprietary/separately licensed enterprise component or dual-licensing model requires a separate governed decision plus legal/copyright/derivative-work/network-communication review and may not evade applicable EUPL source-availability obligations.

**Voting boundary:** PACK-15/16 isolation and PACK-16 cryptography/guardian/quorum/ceremony governance remain unchanged. Generic `FIR-TRUST-003` crypto profiles do not replace voting-domain cryptography. This update adds an openness/verification boundary, not a new voting protocol.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. Existing API-02 V23 reconciliation and API-03 C1 gate remain unchanged.

## FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary

- **Status:** `approved`
- **Priority:** `critical`
- **Domain:** open source / voting trust / independent verification / audit transparency / commercial operations
- **Target:** PACK-15/16 lineage + API + INFRA + OPS + CTRL + FRONT + SEC + FINAL INTEGRATION + release/licensing governance
- **Dependencies:** `FIR-OSS-001` through `FIR-OSS-006`, `FIR-INV-002`, `FIR-INV-010`, `FIR-SEC-002`, `FIR-TRUST-001`, `FIR-TRUST-002`, PACK-15/16 voting isolation and verifier/election-record lineage

EPD² must preserve a public trust boundary in which no proprietary or operator-only component is necessary to independently establish whether a published election result and its verification-relevant evidence conform to the governed protocol.

### Mandatory public trust surface

At minimum, where applicable to the implemented profile, keep public and independently reviewable:

- protocol specifications, threat model, formal/security claims, limitations and residual risks;
- verification-relevant cryptographic core/reference implementation, canonical encoding and test vectors;
- client crypto/core SDK plus a minimal reference voting client sufficient to exercise the public protocol;
- an independent verifier using public election artefacts only, with reproducible/independently verifiable build/run instructions;
- key/guardian ceremony specification, transcript/evidence format and reference ceremony tooling;
- ballot acceptance, election lifecycle, tally/finalization, publication commitment and election-record semantics needed for independent verification;
- public audit-evidence integrity format, chain/anchor verification semantics and independent verification tooling;
- public protocol/schema versioning and vulnerability/security disclosure process.

### Permitted commercial operations surface

Subject to all applicable licence/copyright/dependency obligations, commercial value may be delivered through managed hosting/SaaS, deployment/orchestration, HA/multi-region resilience, enterprise administration UX, guardian operational UX, HSM/KMS integrations, government/enterprise connectors, observability, WORM/audit storage infrastructure, compliance workflow tooling, hardened/certified distributions, SLA/support/maintenance and professional services.

### Hard boundary

A commercial/closed component must not be required for independent verification and must not be able to introduce an undetectable alternate ballot-acceptance, tally, finalization, decrypt, quorum-bypass, result-signing or audit-integrity path.

If removal or malicious behavior of a proposed closed component would make a false result indistinguishable from a conforming result to an independent verifier using the public trust artefacts, the trust-critical portion of that component belongs in the Public Trust Core.

### Licence compatibility

This FIR does not alter `FIR-OSS-001`: EUPL-1.2 remains the intended baseline for original EPD² software subject to final legal review. It does not itself authorize dual licensing or proprietary relicensing. Separate commercial code/services are allowed only where the legal/licence boundary permits them; applicable EUPL source-availability, derivative-work and network-communication obligations must be honored rather than bypassed.

### Acceptance

This FIR is not complete until an exact release/deployment proves that an independent party can rebuild/run the public verification path, verify the governed election record and verification-relevant audit evidence without private EPD² infrastructure, while every commercial component is shown non-authoritative for cryptographic truth and unable to create an undetectable alternate outcome path. Official-instance status, certification, legal activation and production readiness remain separate claims.

---

## V25 governance maintenance record — Lossless reconciliation of the accepted maintenance lineage with current canonical V24 (2026-08-29)

**Why V25 exists.** API-02 C5 independent review established that the current V23/V24 Master line and the fuller accepted maintenance lineage were divergent. The candidate-local C5 merge was not sufficient authority. V25 makes the lossless reconciliation upstream and canonical.

**Measured inputs:** current `main@007b5d71cf5a54e417cbd5647a35a57098ead186` (parent `5d427eba903999f15b6f6a0d9a3de915a30cf666`), current-main Master SHA-256 `ac212cdd32c843a1403b069b51ea6e68a1f120ddadad414a50a0cbad35990e33`, current-main PCR SHA-256 `73b79b356617b7d2f65081bb409fd4b57d4565b83c7a933ac613de0d1e2de735`, pristine V23 Master SHA-256 `502ddd3ed8c3bf55e3847145772b0863ded01fdcd8521f4c3debf857d0cc0503`, independently reviewed C5 merged-Master SHA-256 `128c1bf2c060cfe1833bd6c211e9c74823137a3c27e53a37813b7b3f1f1bdd90`, API-02 C5 archive SHA-256 `c9cd83116b6045bc12a5104bf85270cb0fb29883166628924314394ca0e8e978`, accepted API-01 C5 archive SHA-256 `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27`.

**Lossless result.** C5 merged input contains `240` unique FIR headings; current-main V24 contains `154`; their union contains `241`. V25 contains the entire union with `missing_after_merge = []`, `duplicate_active_ids = []`, and carries the exact current-main `FIR-OSS-007` block rather than reconstructing it from task text.

**Conflict rule.** The independently reviewed C5 merge remains the governed resolution for accepted-line versus V23 content conflicts; V25 adds the exact later current-main V24 material and does not reopen those resolved choices. No FIR is intentionally deleted, downgraded or renumbered.

**Execution state:** unchanged. `API-01 = ACCEPTED / CLOSED`; `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. This repair accepts or closes no implementation stage and is **NOT PRODUCTION READY / NOT LEGALLY ACTIVATED**.

## Governance maintenance record — BSI voting certification readiness (2026-08-30)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT,
SEC, PACK-15, PACK-16, PACK-17 or other implementation stage is accepted,
closed, reopened, certified or legally activated by this update.

**New FIR ID created:** `FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness`
— status `approved`, priority `critical`.

**Governed readiness artifacts:**

- `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`;
- `docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md`.

**Core decision:** EPD² Voting is to be developed with future certification
against the applicable `BSI-CC-PP-0121` target in mind, presently targeting
`EAL4 + ALC_FLR.2`, while preserving stronger EPD² privacy,
no-intermediate-tally and independent-verification invariants. This is a
certification-readiness obligation, not a certification or conformance claim.

**Execution state:** unchanged. The Program Control Register remains the sole
authority for current stage state.

## FIR-VOTE-BSI-001 — BSI CC PP-0121 Certification Readiness

- **Status:** `approved`
- **Priority:** `critical`
- **Domain:** voting security / Common Criteria / BSI certification readiness / assurance evidence
- **Target:** bounded EPD² Voting TOE and every future Voting-affecting API, INFRA, OPS, CTRL, FRONT and SEC change
- **Governed matrix:** `docs/security/bsi/EPD2_BSI_CC_PP_0121_CERTIFICATION_READINESS_GAP_MATRIX_0.1.md`
- **P0 questionnaire:** `docs/security/bsi/EPD2_BSI_CC_PP_0121_P0_PRE_EVALUATION_QUESTIONNAIRE_0.1.md`

### Normative requirement

EPD² Voting must preserve an architecture capable of becoming a bounded Common Criteria TOE conformant to the then-current applicable BSI online-voting Protection Profile, presently BSI-CC-PP-0121, without weakening existing voting privacy, unlinkability or WS-03 isolation invariants.

This FIR is a certification-readiness obligation, not a certification or conformance claim. It does not make EPD² Voting `BSI-certified`, `BSI compliant`, `CC compliant`, `EAL4`, production ready or legally activated.

### Hard P0 architectural freeze

Until a recognised Common Criteria evaluation facility provides a written P0 position on the PP-0121 identity model, EPD² must not weaken the invariant `no persistent member/person identifier inside voting domain` merely to match PP terminology. In particular, civil identity, member identity, account identity, persistent member/person identifiers and reverse-resolvable identity references remain prohibited inside the voting domain.

A negative evaluator answer does not itself authorize weakening that invariant. It triggers a governed TOE/certification-strategy decision.

EPD² must not assume that internal party elections are either in-scope or out-of-scope without written BSI/ITSEF classification.

### Mandatory certification-readiness gates

```text
ITSEF P0 feasibility
→ TOE boundary
→ Security Target
→ P1 closure
→ EAL4 + ALC_FLR.2 evidence
→ independent evaluation
→ BSI decision
```

The gates are ordered. Preparatory work may proceed in parallel where it does not pre-judge an unresolved earlier gate, but no later gate may be claimed complete on internal evidence alone where external evaluation is required.

### Required P0 questions

1. Can PP-0121 `User Identity`, `voters' register` and individual `voting record` be represented by a non-identifying, election-scoped, single-use eligibility representation that cannot be correlated to the ballot or to civil/member identity while preserving strict conformance?
2. For EPD², should the evaluation target be a central/single-component Voting TOE or a multi-component Voting TOE using the PP multi-component package?
3. How should internal party election use cases be classified against the stated `non-political elections` scope before any product-scope claim is made?

### Acceptance criteria

`FIR-VOTE-BSI-001` is not implemented merely because this FIR, the readiness matrix or the questionnaire exists. It may advance only on explicit evidence that:

- the written P0 evaluator position is recorded;
- the exact TOE boundary is frozen;
- a Security Target maps the applicable PP requirements under strict conformance;
- every claimed SFR/SAR has maintained design/implementation/test/evidence traceability;
- P1 production gaps are closed for the candidate TOE;
- the required EAL4 + ALC_FLR.2 assurance evidence exists;
- independent testing/vulnerability analysis findings are closed as required; and
- a BSI certification decision exists for a fixed product/version/configuration before any certification claim is made.

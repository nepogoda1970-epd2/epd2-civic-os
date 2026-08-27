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
implements a *reference* form of the model PACK-16A, PACK-16B and PACK-16C
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
PACK-15, PACK-16A, PACK-16B and PACK-16C left it. This round *implements*
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
*deferred to PACK-17* to **partially implemented**: the signature half of
the signature-and-timestamp framework now exists; the timestamp half does
not. `FIR-SEC-002` **stays** *blocked pending external review* — the
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
that list to nine. The closest call is `SignerRegistry`: a *published,
governance-issued* signer set would be canon-visible, and it is not canon
yet only because no governance act issues one. If `OD-P16D-12` closes with a
published registry, the amendment question must be re-asked.

**Open decisions.** **Closed: three** — `OD-P16D-01` (the profile loads),
`OD-P16D-07` (threshold path implemented), `OD-P16D-09` (signatures
verified). **Opened: two** — `OD-P16D-11` (the reference ceremony has no
custody model: one process, no authenticated channel, no HSM, no air gap)
and `OD-P16D-12` (the signer registry's own authorisation is outside the
verifier's reach). `OD-P16D-02` is **narrowed but not closed**: two
independent oracles and primary-source parameters now exist, but no
comparison against a *complete* independent implementation. **No inherited
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
`--ignore`** (the previous round: 5 616 passed, 17 skipped, *with* one);
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

*The three findings above were environmental and were cleared on a
network-enabled host. Section 1.27 records the resolving evidence; this block
describes the state as of 2026-08-02 and must not be quoted as current.*

**The matrix defect is the one worth recording for its own sake.** `AM-79`
asserted the parameter set was *immutably provenanced* and carried status
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
recorded two blockers changed no delivery. `FIR-SEC-002` stays *blocked
pending external review*.

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

**FIR.** **No FIR outcome moved.** `FIR-SEC-002` stays *blocked pending
external review*: a hash-pinned lock and a commit-pinned source are supply-chain
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

## 1.28 Documentation-only correction — Canonical frontend visual baseline lock (2026-08-25)

**Round:** documentation/governance correction only. No frontend code, token, component or accepted reference screenshot is changed by this round.

**Reason:** `FIR-UX-003` and `FIR-UX-010` previously described FRONT-00/FRONT-01 as an authoritative reference while still permitting ordinary frontend work to “evolve”, “replace” or improve it. That ambiguity is removed.

**Governed rule:** accepted FRONT-00/FRONT-01 visual implementation is the **canonical immutable visual baseline**. Existing typography, spacing, colors, borders, radii, layout/grid geometry, header/footer/navigation treatment, component styling, responsive behavior, interaction states and accepted reference screenshots must be reused exactly where they already exist. New functionality may extend pages and compose existing primitives, but it may not restyle existing blocks.

The only exception is a separate explicit governed **Design Change Decision** approved before implementation and naming the exact affected baseline element, with rationale, before/after screenshots, accessibility evidence and visual-regression impact. A feature requirement, implementation convenience, developer preference, mockup or “modernization” is not such approval.

**FIR IDs changed:** requirement wording of `FIR-UX-003` and the directly conflicting acceptance wording in `FIR-UX-010`; both statuses remain `approved`. No FIR status changes.

**FIR IDs implemented:** none. **New FIR IDs:** none.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`; final FRONT closure remains future.

## 1.29 Documentation-only refinement — Regional/local frontend operating model (2026-08-25)

**Round:** documentation/governance refinement only. No runtime, organization, membership, voting or administrative authority is activated by this round.

**Governed decision:** Landes-, Kreis-, Orts- and other regional party bodies use one EPD² platform with organization-scoped public and authenticated views. They do not receive separate independently designed local products, separate identity systems or separate voting engines.

Public regional hubs use `/regionen` and `/regionen/[slug]` and aggregate only approved public organization projections/renditions from centrally governed content families. Authenticated scope switching is limited to authorized Bund/Land/Kreis/Orts/body scopes and must re-evaluate authorization and invalidate incompatible stale context. Regional binding votes use the same isolated WS-03 Voting Client with one-time purpose- and organization-scoped handoff. Regional administration remains scoped; no universal admin is introduced.

**FIR IDs refined:** `FIR-UX-004` and existing FRONT/organization-scope/voting-isolation obligations. **Status changes:** none. **New FIR IDs:** none.

**Frontend evidence/specification:** `docs/frontend/FRONT-02-REGIONAL-OPERATING-MODEL.md` and the Regionen section of `docs/frontend/FRONT-02-SPECIFICATION.md`.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`.

## 1.30 Documentation-only refinement — DE/EN frontend language model (2026-08-26)

**Round:** documentation/governance refinement only. No runtime, legal, publication, membership, voting or administrative capability is activated by this round.

**Governed decision:** EPD² frontend surfaces use a DE/EN localization model. German is the default interface language and authoritative reference for legally, procedurally and institutionally material German party content unless an exact later governed decision states otherwise. English is a governed translation rendition. German canonical route paths remain canonical; language selection changes rendition state and does not create a second English route authority.

Shared shells expose a canonical-style accessible `DE | EN` selector where both languages are offered. Language preference is minimal non-authoritative display state and must not encode or correlate identity, authorization, political interest, organization scope, case identity or voting eligibility. Material English content is version-linked to its German source, carries governed translation status/approval evidence, and fails explicitly to the current German authoritative rendition when missing, stale or unapproved.

**FIR IDs refined:** `FIR-FORM-004`, `FIR-UX-004`, `FIR-UX-007`, `FIR-UX-008`, `FIR-UX-011` and existing privacy/session/accessibility obligations. **Status changes:** none. **New FIR IDs:** none.

**Frontend evidence/specification:** `docs/frontend/FRONT-02-LANGUAGE-AND-LOCALIZATION-MODEL.md` and §5.3 of `docs/frontend/FRONT-02-SPECIFICATION.md`.

**Execution state:** unchanged. `API = NEXT`; `FRONT-02 = SPECIFICATION ESTABLISHED / IMPLEMENTATION NOT STARTED`.

## 1.31 Documentation-only update — Governed AI Correspondence Analysis & Reply Drafting (2026-08-27)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is started or closed by this update.

**Purpose:** record the approved EPD² requirement for governed AI-assisted analysis of incoming correspondence and preparation of reply drafts across authorized correspondence, casework, member-support and representative-desk workflows.

**New FIR ID created:**

- `FIR-AI-003 — Governed Correspondence Analysis & Reply Drafting` — status `approved`, priority `high`.

**FIR IDs implemented:** none. The existing `ai-processing-service` already provides reference-level use classes including summarization, classification, recommendation and drafting, together with provenance/redaction/human-review boundaries. This update does not claim an end-to-end correspondence copilot, a live AI provider, automatic sending, production readiness or legal activation.

**Human-authority boundary:** AI output remains advisory. The AI layer may analyze authorized correspondence and prepare drafts, but may not establish the organization's political/legal position, issue a consequential decision, finalize or close a governed case, or send an official consequential response without the owning workflow's required human authorization. Automated transmission is prohibited by default; any future narrowly defined non-substantive acknowledgement requires a separate governed decision.

**Execution state:** unchanged. `API-02 = NEXT` remains the primary implementation position. No current stage status is promoted or reopened.

## 1.32 Documentation-only refinement — FIR-AI-003 Implementation Placement Matrix (2026-08-27)

**Round:** documentation/governance refinement only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is started, accepted or closed by this update.

**Purpose:** remove implementation-placement ambiguity for `FIR-AI-003` by assigning mandatory responsibility across authoritative correspondence/casework ownership, `ai-processing-service`, document/evidence ownership, API, INFRA, OPS, CTRL, FRONT, FINAL INTEGRATION and SEC.

**FIR IDs refined:** `FIR-AI-003`. **Status changes:** none. **New FIR IDs:** none.

**Governed rule:** no single service, layer, generic chatbot, provider integration or frontend surface may claim `FIR-AI-003` complete in isolation. Each stage owns only its scoped obligations; whole-FIR completion requires the governed end-to-end path and acceptance evidence.

**Execution state:** unchanged. `API-02 = NEXT` remains the primary implementation position. Exact allocation among API-02…API-06 remains governed by their stage contracts; this refinement does not pre-assign or pre-accept a specific API stage.

## 1.33 Documentation-only update — Regional Authority Suspension & Intervention Control (2026-08-27)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is accepted or closed by this update, and no regional intervention capability is activated merely by recording it.

**Purpose:** establish the mandatory technical control model for containing misuse of regional administrative authority without disabling the regional organization, ordinary member participation or the voting trust boundary.

**New FIR ID created:** `FIR-GOV-004 — Regional Authority Suspension & Intervention Control` — status `approved`, priority `critical`.

**Governed rule:** intervention acts on exact privileged sessions, exact `OrganizationalAuthority` assignments, exact administrative `action_code` classes and, where necessary, narrow time-bounded `temporary_supervision_by` authority. There is no unrestricted `region_disabled` switch, no implicit Bund takeover and no universal regional super-administrator.

**Legal/governance boundary:** this round fixes the technical mechanism and safety invariants. The exact statutory/legal body competent to initiate, approve, review or overturn each intervention remains subject to later legal/Satzung refinement and must be supplied through governed authority/rule configuration; technical hierarchy position alone never supplies that competence.

**FIR IDs implemented:** none. Existing ADR-034/ADR-036 regional-scope and authority foundations, PACK-12 privileged-access controls and audit/evidence mechanisms are dependencies, not evidence that the end-to-end intervention workflow already exists.

**Execution state:** the FIR addition itself changes no implementation-stage acceptance state. API-02 execution-state reconciliation is recorded separately in Program Control; no API-02 PASS/ACCEPTED claim follows from this round.

## 1.34 Documentation-only update — Governed Access, Credential & Key Authority Lifecycle Control (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT implementation stage is accepted or closed by this update, and no credential/key-management capability is activated merely by recording it.

**Purpose:** establish the mandatory end-to-end authority model for blocking access, recovering or replacing human credentials, issuing service credentials, generating/activating/rotating/revoking cryptographic keys, emergency compromise handling and independent evidence/review.

**New FIR ID created:** `FIR-SEC-004 — Governed Access, Credential & Key Authority Lifecycle Control` — status `approved`, priority `critical`.

**Governed rule:** authentication credential, session, organizational authority, privileged grant, service credential and cryptographic key are different control objects. The rights to request, approve, execute/generate, see secret material, activate, revoke, restore, rotate, destroy and audit are separate authorities and must not collapse into a universal administrator.

**Dependencies preserved:** PACK-14 authentication/recovery controls, PACK-12 JIT/break-glass separation, FIR-GOV-004 regional authority intervention controls, voting trust-domain isolation and audit/evidence rules remain controlling boundaries. This round does not reopen any closed architecture PACK.

**FIR IDs implemented:** none. Exact allocation among API-02…API-06 and later INFRA/OPS/CTRL/FRONT/SEC stages remains governed by their stage contracts and acceptance gates.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. No API-02 PASS/ACCEPTED/CLOSED claim follows from this round.

## FIR-BASE-001 — Current repository baseline

**Status:** implemented  
**Last updated:** PACK-15 FINAL PASS round (2026-07-31)

**Current authoritative cumulative baseline (PASS):**

```text
EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_FINAL_PASS.zip
```

Repository version `0.15.0`; canon version `0.8.0` (unchanged — PACK-15
amends no canon). Verified by an external GitHub Actions run that passed
every stage — 983/983 required paths, Ruff format over **436 files**,
5343 Python tests passed with 4 skipped, a Next.js production build with
48/48 static pages and 135 browser, visual and accessibility tests. See
`docs/handover/PACK-15-FINAL-PASS-REPORT.md`.
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

The verified candidate was
`EPD2_PACK-15_VOTING_TRUST_BOUNDARY_ELIGIBILITY_CREDENTIAL_SEPARATION_0.15.0_CANDIDATE_HYGIENE_CORRECTED.zip`.
This FINAL PASS archive is that externally verified tree plus the status,
register and handover documents that close the round; no service module,
migration artefact, test, reason code, contract, frontend file or CI
definition changed, and neither version moved.

An earlier external run passed against a tree that also contained
`epd2-civic-os/`, a stale copy of the repository at `0.6.0`. That
directory was removed and the tree re-verified from scratch; **the
artifacts for the earlier run are superseded and are not FINAL PASS
evidence.**

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

| Layer / owner | Mandatory responsibility | Must not do |
| --- | --- | --- |
| `organization-service` | Own current organizational scope, `OrganizationalAuthority` suspension state, regional restriction state and `temporary_supervision_by` relationship/effective dates. | Must not infer intervention authority from hierarchy position or become a universal admin service. |
| Identity / Security / privileged access | Terminate/quarantine privileged sessions and enforce privileged-session/JIT/break-glass controls. | Must not decide membership, office removal, regional policy or substantive domain outcomes. |
| Governance / oversight | Own the governed human decision and rule references authorizing suspension, restriction, restoration, revocation or supervision. | Must not gain implicit data access from an oversight title. |
| API | Re-evaluate current session, authority, scope, restriction and domain authorization on every affected mutation and expose reason-coded outcomes. | Must not trust stale frontend/token scope or provide an upper-level bypass endpoint. Exact API-stage allocation remains stage-contract governed. |
| CTRL | Provide scoped proposal, approval, review, restoration/revocation and supervision control surfaces with separation of duties. | Must not expose a one-click universal `disable region` / `take over region` control. |
| FRONT | Show the exact restriction/suspension state, affected scope/actions, reason/reference, review/expiry state and available remedy to authorized users. Preserve ordinary unaffected regional/member journeys. | Must not present the entire region or all members as suspended when only administrative authority is contained. |
| OPS | Provide incident containment, monitoring, expiry/review alerts, recovery and evidence handling. | Must not silently extend intervention or convert an outage into permanent governance state. |
| SEC / FINAL INTEGRATION | Prove that stale sessions/tokens, cross-Land calls, hierarchy tricks, approval bypass, expired restrictions, supervision overreach and voting-boundary attacks fail on the exact integrated baseline. | Must not infer safety from isolated service tests only. |

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

| Layer / owner | Mandatory responsibility | Must not do |
| --- | --- | --- |
| Satzung / OZKO / rules governance | Define legally competent organs, scope, delegation, intervention, review and exact RuleVersions. | Must not be replaced by software defaults or hierarchy inference. |
| `organization-service` | Represent organizations, relations, scopes and `OrganizationalAuthority` lifecycle bound to source decisions/rules. | Must not create competence from role labels or parent relation alone. |
| API/runtime | Re-evaluate current actor + scope + capability + active restrictions + assurance at action time. | Must not trust stale token/profile role claims as final authority. |
| CTRL | Provide governed request/approval/intervention/review queues, SoD and evidence. | Must not expose universal takeover/admin controls. |
| FRONT | Show office, scope, source authority, restrictions and remedy accurately. | Must not imply a technical role is a political office or vice versa. |
| OPS | Operate lawful administrative/security procedures and escalation. | Must not convert emergency containment into permanent political intervention. |
| SEC | Test cross-scope escalation, self-grant, stale authority, approval bypass, court/audit tampering and voting escape. | Must not accept hierarchy-based authorization as a shortcut. |
| FINAL INTEGRATION | Prove exact adopted rule -> organ decision/election -> OrganizationalAuthority -> allowed/denied action -> immutable evidence -> review chain. | Must not infer completion from documentation or isolated service tests. |

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

| Operation | Request / initiate | Approve | Execute / custody | Secret/private-material visibility | Independent evidence/review |
| --- | --- | --- | --- | --- | --- |
| Enrol ordinary passkey | subject after authenticated/enrollment gate | policy/self-service gate; additional approval only where risk requires | authenticator generates private key; credential service registers public credential | subject authenticator only; operator never receives private key | automated immutable audit; anomaly review as governed |
| High-assurance lost-device/account recovery | subject or authorized support intake | recovery approver; privileged accounts require distinct stronger approval/dual control | credential service enables bounded re-enrollment; subject creates replacement credential | no operator-created passkey private key; recovery evidence is separately protected | mandatory reason/evidence; privileged recovery independently reviewed |
| Quarantine/revoke active sessions | subject self-service where applicable or security operator under incident policy | immediate containment may be pre-authorized by policy; broader/continued intervention follows governed approval | session/security service | no credential private-key access implied | reason-coded incident/audit record; review proportional to impact |
| Revoke compromised human authenticator | subject or security/credential operator under explicit scope | ordinary self-revoke may be self-service; administrative/high-impact revoke follows governed approval | credential service | operator sees credential metadata/public material only | revocation and replacement linkage preserved |
| Suspend/restore/revoke `OrganizationalAuthority` | competent governance/security process | `FIR-GOV-004`/owning governance rule; Levels 2–4 require two distinct authorized humans | organization/governance service enforces state | no credential/key secret access implied | immutable decision/evidence/review/appeal chain |
| Grant JIT privileged access | authorized requester | separate authorized approver | privileged-access service activates scope + TTL | only task-required data/secret access; no generic secret export | mandatory grant/use/expiry evidence; post-review by risk class |
| Activate break-glass | authorized emergency requester | distinct controller under PACK-12 policy unless a stricter emergency rule applies | privileged-access service activates bounded emergency grant | only explicitly approved emergency scope | auto-expiry/revoke + mandatory independent post-use review |
| Issue/replace service credential | service owner/requester | service/security/platform authority according to risk class | workload identity/certificate/key platform generates or enrols; delivery is machine-bound where possible | service receives only what its protocol requires; custodians should use handles/non-exportable keys where possible | issuance, scope, expiry and consumer evidence reviewed |
| Generate platform cryptographic key | service/domain owner requests purpose | governance/security/platform approver according to key class; high-impact/root classes require dual control or stronger quorum | KMS/HSM/certificate/key custodian | private material non-exportable where supported; approver/auditor need no plaintext | generation attestation/metadata and policy version preserved |
| Activate/scheduled-rotate signing, encryption or TLS key | service owner/key lifecycle controller | class-specific approval; high-impact rotation requires distinct approver | key platform/custodian stages and activates | no broader plaintext visibility than technically unavoidable | cutover, verifier convergence and old-key retirement evidence |
| Emergency revoke compromised service/platform key | security incident authority | immediate containment may be pre-authorized; replacement activation follows required SoD; root/high-impact exceptions require governed break-glass/quorum | key/cert/workload platform revokes and propagates new trust state | containment does not grant right to inspect unrelated secrets | incident evidence + mandatory post-action review and replacement linkage |
| Destroy retired cryptographic key | lifecycle controller/service owner after retention/decryption dependency check | class-specific approver; high-impact classes require dual control/quorum | KMS/HSM/key custodian destroys or cryptographically erases | no export before destruction | destruction attestation/evidence retained without secret material |
| Root/master/KEK ceremony, if adopted | designated key-governance authority | governed quorum stronger than a single operator; exact threshold defined by accepted INFRA/SEC policy | HSM/KMS custodians under ceremony | split/quorum/non-exportable handling; no single plaintext custodian | independent witness/evidence mandatory |
| Voting-domain key change | voting-domain governed actor/trustee | voting-specific trustee/quorum/governance only | voting trust-domain components | generic platform/regional/security admins excluded | voting-domain evidence/challenge rules only |

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

| Layer / owner | Mandatory responsibility | Must not do |
| --- | --- | --- |
| Identity / credential services | Human credential enrollment, public-credential metadata, revocation/replacement, governed recovery state/evidence and assurance outcome. | Must not manufacture passkey private keys, grant organizational authority or use recovery as universal bypass. |
| Session/authentication runtime | Issue, validate, quarantine, revoke and expire sessions/tokens according to current credential/security state. | Must not trust stale authority claims after governing state has changed. |
| `organization-service` + governance | Own `OrganizationalAuthority` assignment/suspension/restoration/revocation and FIR-GOV-004 relationships. | Must not equate possession of a login/key with office or organizational authority. |
| `privileged-access-service` | JIT and break-glass grants, exact purpose/scope/TTL, dual control and post-use evidence. | Must not become permanent superadmin or routine credential-recovery path. |
| Service identity / API runtime | Bind workload credentials to exact service/environment/audience/purpose and re-evaluate current credential/authority state at use time. | Must not turn a valid machine credential into unrestricted cross-service business authority. Exact API-stage allocation remains stage-contract governed. |
| INFRA | Provide accepted KMS/HSM/certificate/secret/workload-identity substrate, protected generation/storage, non-exportability where supported, trust-set publication and key-version mechanics. | Must not select/activate a provider or expose secret material outside accepted region/policy merely because the FIR exists. |
| OPS | Inventory/ownership, rotation/expiry monitoring, compromise response, convergence monitoring, recovery runbooks, notification and destruction/retirement operations. | Must not silently extend expired keys, bypass approval or distribute secrets through ad-hoc channels. |
| CTRL | Request/approval/custody/review workflows, SoD enforcement, key/credential status, expiry/rotation queues, evidence inspection and ceremony controls. | Must not expose one-click universal `reset all access`, `mint admin key` or cross-domain bypass controls. |
| FRONT | Safe enrollment/recovery/status UX; show blocked/recovery/expiry state and available remedy to authorized users. | Must not display private key material unnecessarily, claim a blocked authority is restored from login alone or become the authorization boundary. |
| SEC / FINAL INTEGRATION | Adversarially prove stale credential/session/key rejection, rotation correctness, compromise containment, secret non-disclosure, SoD, cross-scope isolation and exact integrated recovery paths. | Must not infer safety from the existence of KMS/HSM or isolated unit tests. |
| Voting trust domain | Own voting-specific credentials/keys, trustee/quorum ceremonies and election-specific revocation/rotation. | Must not inherit generic platform/regional/security key-admin authority. |

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

| Layer / owner | Mandatory responsibility for `FIR-AI-003` | Must not own / claim |
| --- | --- | --- |
| Existing domain services / Communications and Casework ownership | Own the authoritative incoming correspondence/thread/case state, sender/recipient routing context, attachment references, procedural status, final authorized reply and delivery linkage. Assemble only the case/domain context the acting principal is already authorized to access. | Must not delegate authoritative correspondence/case ownership to the AI service or treat AI output as the case decision. |
| `ai-processing-service` | Perform governed summarization, classification, recommendation, drafting, verification flags and structured correspondence analysis; enforce redaction/provenance, model/configuration identity, staleness, human-review state and fail-closed prohibited-input controls. | Must not become the authoritative message/document store, widen authorization, close a case, establish organizational position or send/mutate Civic OS state. |
| Document / evidence ownership | Preserve immutable/versioned attachment and document references, governed renditions, exact sent-response versions and applicable retention/legal-hold evidence. | Must not duplicate source ownership inside the AI-processing record. |
| API | Expose governed production contracts/BFF composition for requesting analysis, reading structured results and provenance, generating/revising drafts, submitting required human review/approval state and invoking the owning correspondence delivery path after authorization. API contracts must preserve actor, purpose, scope, correlation and version identifiers. | Must not introduce a direct AI-provider-to-send shortcut or an endpoint that bypasses owning-domain authorization/human approval. Exact allocation among API stages is governed by their stage contracts; this FIR does not pre-accept any API stage. |
| INFRA | Provide the deployable AI runtime/provider path, credentials and secret handling, network and region isolation, queue/execution substrate, approved retention modes, model endpoint configuration and provider availability controls required by the accepted API/runtime design. | Must not activate a provider or data route outside approved region/retention/policy boundaries or claim application-level completion. |
| OPS | Define and operate monitoring, timeout/retry/cancellation policy, degraded-mode behavior, escalation to humans, provider outage handling, incident response, recovery and operational evidence for correspondence AI processing. | Must not silently auto-send when AI/provider processing fails or substitute retries for human review. |
| CTRL | Provide governed control-plane surfaces for reviewer queues, reviewer authority/scope, model/prompt/policy version visibility, approval/rejection/supersession, audit inspection, configuration controls and separation-of-duties enforcement for consequential outputs. | Must not allow AI self-approval, universal admin access or configuration that bypasses the owning workflow's authority model. |
| FRONT | Provide the staff-facing workflow `Original correspondence -> AI analysis -> authorized context -> open questions/verification flags -> reply draft -> human edit/review/approval -> authorized send -> history`, with clear provenance/staleness and source-vs-AI-vs-human distinctions. | Must not present AI output as already approved, hide stale/ungrounded state, or simulate unsupported backend capability as complete. |
| SEC | Adversarially verify prompt-injection resistance, poisoned attachments/context, prohibited-input handling, authorization/correlation boundaries, data exfiltration attempts, provider/tool escape attempts, human-approval bypasses and exact-send integrity on the integrated baseline. | Must not test only the model in isolation; the target is the complete accepted cross-layer path. |
| FINAL INTEGRATION | Prove the exact end-to-end path from authorized intake through AI processing/context grounding and human approval to the exact delivered version and durable audit/evidence history on the accepted integrated baseline. | Must not infer completion from isolated unit/service tests or from the existence of `ai-processing-service`. |

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

EPD² must preserve the exact visual implementation already established in
the accepted FRONT-00/FRONT-01 public pages and frontend foundation. That
implementation is the **canonical immutable visual baseline** for later
frontend work; ordinary FRONT-PACK scope does not include visual evolution,
modernization, refresh or restyling.

The canonical baseline includes:

- clear, calm and institutional presentation;
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

## Section 28 boundaries

These entries:

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

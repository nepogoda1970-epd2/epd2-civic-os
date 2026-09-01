# PACK-13 Production Data Plane & Contract Evolution 0.13.0 — Final PASS Report

Status: **PACK-13 PRODUCTION DATA PLANE & CONTRACT EVOLUTION 0.13.0 — FINAL PASS.**

```text
PACK-13 FINAL PASS
EXTERNAL GITHUB ACTIONS PASS
REPOSITORY_VERSION 0.13.0
CANON_VERSION 0.8.0
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
```

This is a **packaging round**. No implementation was rebuilt. No
`data-plane-service` module was changed, no test was changed, no reason
code, ADR, contract, frontend file, route or visual snapshot was touched,
and neither the repository nor the canon version moved. The archive is the
externally verified tree plus the status, register and handover documents
that close the round.

The PASS rests on an **external GitHub Actions run**. Section 10 records its
figures; section 11 states exactly which checks were re-run locally after
the documentation edits, and which are accepted from that run. Nothing
network-dependent is claimed as locally verified, and — this matters for a
pack named after the production data plane — nothing about production
infrastructure is claimed at all.

---

## 1. Input baseline — PACK-12

|                             |                                                                     |
| --------------------------- | ------------------------------------------------------------------- |
| Baseline archive            | `EPD2_PACK-12_PRIVILEGED_ADMIN_SEARCH_EXPORT_0.12.0_FINAL_PASS.zip` |
| Baseline repository version | `0.12.0`                                                            |
| Canon version               | `0.8.0` — unchanged by this round                                   |
| Baseline status             | FINAL PASS, external GitHub Actions verified                        |

PACK-12 is now the previous PASS baseline. Nothing in PACK-01—PACK-12 was
rewritten to reach this one: `privileged-access-service`,
`document-service` and every earlier service are untouched, and PACK-13
adds a bounded context beside them rather than a layer beneath them.

## 2. Accepted specification and ADR basis

The normative basis is the **corrected PACK-13 Specification + ADR round**,
accepted before any code existed:

- `docs/packs/PACK-13/PACK-13-SPECIFICATION.md` and the ten companion
  documents under `docs/packs/PACK-13/`;
- `docs/adr/ADR-069-*` through `docs/adr/ADR-078-*`;
- `docs/handover/PACK-13-SPEC-ADR-REPORT.md`, **retained unchanged** as
  that round's own record and deliberately never rewritten as an
  implementation report.

That round set no version and implemented nothing. The specification
carries one superseding status note added by this round, because its
"Not implemented. Not a candidate. Not a PASS." header describes the
specification round and had become misleading on its own terms; the header
itself is preserved.

## 3. Scope of PACK-13

`FIR-ROADMAP-003`: production database, event bus, canonical schema
registry, API evolution, event evolution, idempotency, compatibility
policy, migration discipline, contract versioning.

The governing rule is the specification's first sentence, and it is the
reason this pack has no authority surface:

> **The data plane is infrastructure. It is not an authority.**
> Persistence must not create a capability that the domain layer refuses.

## 4. Bounded contexts implemented

One new service, `services/data-plane-service`: **22 source modules, 22
test modules (20 test suites plus `conftest.py` and a builder module), 555
tests of its own**, ~10.5k lines of source and ~7.5k lines of tests.

It is deliberately not a god service. It owns the five logical contexts
§3 of the specification assigns to PACK-13 itself and owns no other
domain's data:

| Context                             | Modules                                                                                                                   |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Transactional persistence contracts | `concurrency`, `idempotency`, `storage`                                                                                   |
| Canonical schema registry           | `registry`, `canonicalization`, `compatibility`                                                                           |
| Contract evolution                  | `contracts`                                                                                                               |
| Migration control                   | `migrations`, `backfill`                                                                                                  |
| Delivery and projection governance  | `outbox`, `delivery`, `projections`                                                                                       |
| Supporting                          | `exceptions`, `domain`, `integration`, `retention`, `privileged`, `boundaries`, `events`, `application`, `administration` |

## 5. ADR-069 — ADR-078

All ten are `accepted`. This round amends **no** canon: `CANON_VERSION`
stays `0.8.0` and `docs/canonical/TZ-00-domain-event-canon.md` is
untouched. The canon §21 event envelope is unchanged, which is what keeps
the pack canon-neutral — transport metadata never reaches it.

| ADR     | Decision                                                                                                                         | Where it lives                          |
| ------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| ADR-069 | A PostgreSQL-compatible relational data plane of domain-owned schemas, organizational scope first-class from the first migration | `domain`, `storage`, `boundaries`       |
| ADR-070 | One owning domain per table; exactly four admissible integration mechanisms; audit ingestion is submission, not persistence      | `boundaries`, `storage`                 |
| ADR-071 | The transactional outbox is mandatory; transport metadata stays off the canonical envelope                                       | `outbox`, `storage.ReferenceUnitOfWork` |
| ADR-072 | At-least-once delivery with effectively-once consumer effect through mandatory consumer idempotency                              | `delivery`, `idempotency`               |
| ADR-073 | A canonical schema registry in which content digest and schema-version identity are separate fields                              | `registry`, `canonicalization`          |
| ADR-074 | Five compatibility modes with `unknown` first-class; structurally invisible change classes always require semantic review        | `compatibility`, `contracts`            |
| ADR-075 | A migration is immutable once applied; five checks are automated gates rather than reviewer vigilance                            | `migrations`, `backfill`                |
| ADR-076 | A read model is never authoritative, never widens source authorization, and is not a hidden cross-domain database                | `projections`                           |
| ADR-077 | Optimistic concurrency everywhere it matters; idempotency keys scoped to domain and operation, never derived from a person       | `concurrency`, `idempotency`            |
| ADR-078 | Retention applies to infrastructure; a legal hold preserves data and authorizes nothing; evidence reuses PACK-11                 | `retention`                             |

## 6. Models, adapters, services and tests

**Typed models.** Every value object in `domain.py` is a frozen dataclass
with a timezone-aware timestamp requirement and a payload guard:
`PROHIBITED_PAYLOAD_KEYS` unions secret material, global identity keys,
voting material and bulk content, so a payload carrying `password`,
`person_id` or `ballot_id` is refused at construction rather than
inspected later.

**Reference persistence adapters.** `storage.py` defines the ports as
`Protocol`s and implements each with an in-memory adapter. **No storage
port defines a delete-shaped method.** A production adapter implements the
same `Protocol` and the domain layer does not change (`P13-PATH-001`).

**Tests.** 555 in the service, run as part of the repository's 4625.
They are written against the refusals, not the happy paths: a stale
expected version conflicts, a grant-less migration is refused, a
cross-domain write is refused, a checksum mismatch halts with no repair
path.

The audit-core boundary test is the load-bearing one: **no non-owner
domain credential can write directly to audit-core persistence.** The
guard sits on `ApplicationCredential`'s constructor, so the violation is
not merely detected — it is not expressible.

## 7. The load-bearing mechanisms

**Transactional outbox (`P13-TX-003`, ADR-071).** A state change and its
outbox record commit atomically or not at all; a rollback leaves no event
behind; a retry reuses the same stable logical event ID. "Published" and
"acknowledged by the broker" are separate fields, because collapsing them
is how a system comes to believe it delivered something it did not.

**At-least-once delivery (ADR-072, `P13-DEL-002`).** The guarantee is
**at-least-once delivery with effectively-once consumer effect through
idempotency**. Duplicates are expected, counted and absorbed; they are not
incidents. The stronger phrase is claimed nowhere in the package, its
documents, its comments or any surface it exposes, and
`tests/test_boundaries.py` scans the source to keep it that way rather
than trusting a convention.

**Idempotent consumers (ADR-077).** Keys are scoped to a domain and an
operation and are **never derived from a person identifier**. Consequential
operation classes carry a permanent `BusinessFactGuard`, so an
idempotency window expiring never becomes permission to perform a
consequential act twice.

**Canonical schema registry (ADR-073, `P13-REG-005`).** Format-specific
canonicalization yields a `content_digest`; digest equality **never**
defines `schema_version_id`. Two documents with the same digest are
byte-identical after canonicalization and nothing more. Duplicate content
resolves to one of three reason-coded dispositions —
`SCHEMA_DUPLICATE_CONTENT`, `SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`,
`SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED` — never to a silent
merge.

**API and event contract evolution (ADR-074).** Five compatibility modes
with `UNKNOWN` as a first-class outcome rather than a euphemism for
"probably fine"; thirteen mandatory fields on a breaking change;
coexistence windows; consumer-readiness tracking; and deterministic
upcasters that **invent no legal fact**. Eight `SemanticRiskClass` values
always escalate to human review, and automated and human verdicts are
stored separately so neither can be mistaken for the other.

**Migration framework (ADR-075).** An applied migration is immutable. Five
**automated** gates run before execution — organization scope, legal-hold
state, evidence linkage, global identifier, voting unlinkability — and a
checksum mismatch halts with **no repair path**. Expand/contract is the
required shape, and the backfill runner is deterministic, restartable,
checkpointed and idempotent, with a review queue for what it will not
guess.

**Projection governance (ADR-076).** A read model is never authoritative,
never widens the authorization of its source, exposes its staleness rather
than hiding it, and propagates deletion with evidence and tombstones.

## 8. Boundaries: audit-core ownership and the voting domain

**Audit-core ownership.** Audit ingestion is **submission, not
persistence**. A domain submits; audit-core persists. `boundaries.py`
makes any other arrangement unrepresentable, and the constructor-level
credential guard is the test named in section 6.

**The voting boundary.** Seven prohibitions exist as **structural
absences** rather than checks: no ballot, credential or tally material in
the general data plane, and no global user ID anywhere. PACK-13
deliberately decides **nothing** about the voting domain's broker topics,
broker deployment arrangement, connection-pool topology, service names,
credential topology or transport provider (`P13-VOTE-008`). Those belong
to PACK-15/16 together with that pack's own threat model; settling them
here would fix a security architecture from outside the pack that owns it.

`services/identity-service`, `eligibility-service`, `credential-service`,
`voting-service` and `tally-service` exist in the baseline as earlier
reference implementations. Their existence settles nothing about
production data-plane ownership, and this round settles nothing either
(`P13-OWN-009`…`013`).

## 9. FIR treatment

`FIR-ROADMAP-003` → **`implemented in reference form`**, on the strength of
the external GitHub Actions PASS in section 10. Not `implemented` outright,
and the distinction is the whole content of the status: the contracts, the
gates and the refusals are real and externally verified; the production
data plane is not deployed.

Entries given a **foundation only** — each explicitly NOT implemented, each
carrying that statement in the register: `FIR-INV-001`, `FIR-INV-006`,
`FIR-INV-007`, `FIR-INV-011`, `FIR-INV-013`, `FIR-INV-014`, `FIR-INV-015`,
`FIR-DATA-001`, `FIR-DATA-003`. A green pipeline promotes none of them.

Entries deliberately left **unchanged**: every other entry. In particular
`FIR-INV-002`, `FIR-INV-003`, `FIR-INV-004` and `FIR-INV-005` are
untouched — PACK-13 establishes the structural absence of voting material
and adds no voting semantics.

New FIR identifiers created by implementation discovery: **none.**

The PACK-13 FIR coverage matrix has exactly one location,
`docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md`, and still records
**zero** `implemented` treatments — asserted structurally by
`tests/repository/test_pack13_fir_matrix.py` (`AC-P13-155`), which the
passing pipeline itself ran. FIR _status_ lives in the Master Register;
the matrix records what the PACK-13 rounds did with each entry, and that
record does not change because a pipeline went green.

### `FIR-PROG-003` — a future frontend obligation

`FIR-PROG-003 — Public Presentation of Adopted Programme and Projects`
remains **`approved`** and remains **outside PACK-13's scope**. It requires
the public `Programm` page to lead with the adopted programme in force
(exact text, version, adoption date, competent body, manner of adoption,
entry into force, decision reference, change history, archived previous
versions), to show projects only as one compact `Projekte in Beratung`
card per thematic section carrying the active count and the marker
`Noch nicht beschlossen` with a link to a separate all-projects page, and
to carry the adopted/not-adopted distinction simultaneously through
textual status, page structure, card shape, an accessible visual marker
and different actions — **never colour alone** (`FIR-INV-012`).

It is a future frontend obligation. A PACK-13 PASS says nothing about it,
and it is **not** recorded as an implemented PACK-13 FIR.

### Register addenda recorded in this round — future implementation debt

The Master Register in this archive is the consolidated version supplied
for this round, adopted verbatim at its canonical path. Beyond
`FIR-PROG-003` it carries three cross-cutting sections written **after**
the external CI run and therefore **not covered by it**:

| Section | Entries                                                                                                                                                                                | Subject                                                                                                                                                                                                                                                                                |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 26      | `FIR-FORM-001` … `FIR-FORM-005`                                                                                                                                                        | Canonical forms, submissions and official renditions: the governed form model, per-domain form inventories, governed German content, multi-channel renditions                                                                                                                          |
| 27      | `FIR-RULE-001`, `FIR-REF-001`, `FIR-DELIVERY-001`, `FIR-TRUST-001`, `FIR-REPRESENT-001`, `FIR-INCLUSION-001`, `FIR-QUALITY-001`, `FIR-CONFIG-001`, `FIR-IMPORT-001`, `FIR-SERVICE-001` | Cross-cutting procedural, trust and operational foundations: governed rules registry, reference data, official delivery evidence, signatures and trusted timestamps, representation, alternative channels, reconciliation, operational configuration, legacy import, service catalogue |
| 28      | `FIR-UX-003` … `FIR-UX-010`                                                                                                                                                            | Frontend design, visualization and interaction governance, with the approved FRONT-00/FRONT-01 implementation as the authoritative visual baseline                                                                                                                                     |

All twenty-three are `approved` future obligations. **None is implemented,
none changes `CANON_VERSION`, none extends PACK-13's implementation scope,
and none is a reason to modify code, tests or CI.** They are recorded as
discovered cross-cutting **future implementation debt** — which is the
honest thing to do with a gap you have found and not closed.

Section 28 is worth restating because it constrains future work rather
than describing it: the existing FRONT-00 and FRONT-01 implementation —
current public pages, shared components, actual typography, spacing
rhythm, colours, borders, radii, page widths, grid and layout logic,
navigation character and the accepted reference screenshots — is the
**authoritative visual baseline**. "Minimalist EPD² design" is not
permission to draw an unrelated new minimalism from scratch. A future
FRONT-PACK must inventory the existing components and page patterns,
extract the real design tokens, classify each affected pattern as
`reuse` / `extend` / `replace`, justify every replacement on usability,
accessibility, security or domain grounds, compare new screenshots against
the accepted baseline, and preserve recognisable continuity. The baseline
is a reference, not a pixel freeze: justified improvement is allowed, an
unrelated redesign is not.

## 10. External GitHub Actions results

| Stage                            | Result                               |
| -------------------------------- | ------------------------------------ |
| Repository path manifest         | **PASS** — 800 / 800                 |
| Forbidden paths                  | **PASS** — none present              |
| Version consistency              | **PASS**                             |
| Ruff format                      | **PASS** — 520 files                 |
| Prettier                         | **PASS**                             |
| Ruff lint                        | **PASS**                             |
| ESLint                           | **PASS**                             |
| mypy                             | **PASS** — all 23 groups             |
| TypeScript typecheck             | **PASS** — `epd2-types`, `web-shell` |
| Python tests                     | **PASS** — 4625 passed, 4 skipped    |
| Node tests                       | **PASS** — 34 passed                 |
| Frontend unit / render tests     | **PASS** — 16 passed                 |
| Next.js production build         | **PASS**                             |
| Browser / visual / accessibility | **PASS** — 108 passed                |

Runner: GitHub Actions / ubuntu-latest, Python 3.12, Node.js 22.

Evidence archive: `epd2-civic-os-verification-result(15).zip`, SHA-256
`e3aa070f594e7366bd40f25f8d46dab8fda7d820428fc600020b2d8adcc9667b`,
retained **outside** this repository. No nested ZIP is placed inside the
FINAL PASS archive.

Unlike PACK-12's round, these figures were **not accepted on report**. The
evidence archive was present in the environment that assembled this
archive; its SHA-256 was recomputed and matches; and every figure above was
read out of the run's own transcript, which is committed at
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` (780 lines).
`docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` records the
provenance in full.

The verified checkout was also compared **file by file** against the
packaged tree: all 948 files tracked at candidate time matched by SHA-256,
except CI-generated artifacts, PACK-12's superseded correction notes, and
two files adopted _from_ the CI tree because the packaging sandbox's copies
were stale — `uv.lock` (the CI tree's lock registers
`epd2-data-plane-service` as a workspace member) and
`docs/frontend/FRONT-00-PAGE-INVENTORY.csv` (identical content, LF instead
of CRLF).

## 11. What the PASS covers, and what came after it

Three things must not be conflated, so they are stated separately.

**1. The implementation candidate that passed external GitHub Actions.**
The tree containing `services/data-plane-service`, its 555 tests, the
reason-code registry, ADR-069—078, the PACK-13 specification documents and
the register as it stood then — with `FIR-PROG-003` already recorded. This
is what section 10's figures verify.

**2. Documentation-only Master Register updates made after that run.**
Sections 26, 27 and 28 (`FIR-FORM-*`, the ten cross-cutting entries,
`FIR-UX-003` … `FIR-UX-010`) and their round records §1.9—§1.12 were
written after the pipeline was green. **They are not covered by it.** They
change no code, no test, no CI configuration, no ADR, no canon and no
version. The register also received the four status changes this round is
required to make — the FINAL PASS round record §1.13, the `FIR-BASE-001`
baseline pointer, `FIR-ROADMAP-003`'s status, and section 21's
implementation summary — plus the status and index updates listed in
section 17.

**3. Local checks re-run after those updates.** Everything the sandbox can
run without network access was re-run against the final tree:

| Check                    | Command                                     | Result                                                                                                                                          |
| ------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Repository path manifest | `scripts/check_repository.py`               | **PASS** — 803 / 803                                                                                                                            |
| Forbidden paths          | `scripts/check_forbidden_files.py`          | **PASS**                                                                                                                                        |
| Version consistency      | `scripts/verify_versions.py`                | **PASS** — `0.13.0` across Python, TypeScript and `CHANGELOG.md`                                                                                |
| Canon amendment state    | `scripts/check_canon_0_8_0.py`              | **PASS** — 18 / 18, canon `0.8.0` unchanged                                                                                                     |
| Ruff format              | `ruff format --check .`                     | **PASS** — 347 files                                                                                                                            |
| Ruff lint                | `ruff check .`                              | **PASS**                                                                                                                                        |
| mypy                     | every target in `Makefile`                  | **PASS** — 23 groups, no issues                                                                                                                 |
| Python tests             | `pytest`                                    | **4618 passed, 5 skipped** — reconciles exactly to CI's 4625 / 4                                                                                |
| Prettier                 | local 3.8.1 binary                          | **PASS** on every file this round touched                                                                                                       |
| Duplicate files          | content and path scan over the archive      | **PASS** — one Master Register, one PACK-13 FIR coverage matrix, no duplicate ADR filename, no candidate or verification ZIP, no nested archive |
| Register integrity       | FIR identifier scan                         | **PASS** — 140 entries, no duplicate identifier, none missing relative to the supplied consolidated register                                    |
| SHA-256                  | recomputed for every added and changed file | sections 18 and 19                                                                                                                              |

The manifest is 803 rather than CI's 800 because this round adds three
required paths: the FINAL PASS report, the external-CI result document and
the CI transcript. That difference is expected and is itself the reason
the next pipeline run must re-verify the archive.

### What could not be run here, and why

`make verify` cannot complete in this environment: the package registries
are unreachable (`403 Forbidden` on PyPI and npm), so
`uv sync --all-groups --frozen`, `uv lock` and `npm ci` all fail. ESLint,
`tsc`, the TypeScript and frontend tests, the Next.js build and Playwright
therefore **did not run locally**, and their results are taken from the
external run rather than claimed here.

The seven-test difference between the local and CI Python figures is fully
accounted for: `tests/contract/test_property_based.py` calls
`pytest.importorskip("hypothesis")` and `hypothesis` cannot be installed
here, so its seven tests are not collected and the module counts as one
skip. 4618 + 7 = 4625; 5 − 1 = 4.

Prettier ran at 3.8.1 rather than the version CI pins. Three pre-existing
baseline files that only 3.8.1 would reformat were left at their baseline
bytes rather than rewritten: `docs/adr/ADR-051-*.md`,
`frontend/web-shell/foundation/storage-policy.ts` and
`frontend/web-shell/foundation/types.ts`. They are exactly the three the
externally verified tree contained, and CI's own Prettier passed on them.

## 12. Deferred to production infrastructure

The acceptance matrix's implementation-status appendix covers all **176**
criteria: 120 implemented and tested, 50 reference implementation, 4
deferred to production infrastructure, 2 blocked by PACK-14/15/16.
**Recorded as met: 0** — unchanged by the PASS.

That last figure is not modesty. Every criterion whose stated evidence is
a database grant inventory, a live catalog snapshot, a role inventory or
an egress-control review describes an environment that does not exist yet.
A pipeline that lints, type-checks and tests a repository cannot produce a
grant inventory, because it grants nothing.

## 13. Dependencies on later packages, and the frontend boundary

| Owner       | What PACK-13 depends on and does **not** provide                                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PACK-14** | Identity, authentication, external IAM/IdP, MFA, HSM/PKI, scoped sessions. `AuthorizationPort` is the seam; PACK-13 mints no identity and reserves the identity boundary without assigning an owner. |
| **PACK-15** | The voting threat model, Voting Client isolation, eligibility/credential separation. PACK-13 chooses no broker topic, topology, service name, credential arrangement or transport for that domain.   |
| **PACK-16** | Verifiable voting, ballot casting, tally controls. PACK-13 declares no voting reference type at all.                                                                                                 |
| **PACK-17** | Backup, restore and recovery testing, the incident-response platform. `P13-BAK-011` forbids claiming backup readiness without a restore test, and no backup exists here.                             |

**Frontend boundary.** PACK-13 is not FRONT-PACK (`P13-FE-001`).
`administration.py` holds contract-level typed view models with a payload
guard: no route, no rendered surface, no component, no accessibility work.
`AC-P13-149` is `deferred to production infrastructure` with FRONT-PACK
named as owner. The frontend obligations this round records —
`FIR-PROG-003` and section 28's `FIR-UX-003` … `FIR-UX-010` — are future
work, and recording them is not doing them.

## 14. Known limitations

`docs/handover/PACK-13-KNOWN-LIMITATIONS.md` states fourteen in full, all
of which survive the PASS unchanged. The load-bearing ones:

- **Every storage adapter is in memory. This is not a data plane.** The
  contracts are real, the refusals are real and tested; the enforcement is
  not. A test proving the code refuses a cross-domain write proves the code
  refuses it — not that a database grant would.
- **`ReferenceUnitOfWork` is not a transaction.** No isolation, no
  durability, no recovery. It makes the atomicity contract testable and
  nothing more.
- **The identity guards are name-based, and a hash defeats them.** A column
  called `ref_7` holding an opaque hash of a person identifier passes. The
  control is the architecture; the name check is a backstop.
- **The compatibility checker is necessary and not sufficient.** A
  submitter who does not declare a semantic-risk class gets a clean
  structural verdict, because nothing automated can tell that a meaning
  changed. The declaration is the control, and it is human.
- **No migration is ever executed.** `MigrationDefinition.statements` is an
  opaque tuple of strings that nothing parses.
- **Backup and restore do not exist, and the deletion gap stays open.** A
  record deleted from a live database but present in backups is not
  deleted. Closing that is PACK-17's.

## 15. Production and legal disclaimers

**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**

PACK-13 does **not** close, provide or activate any of the following, and
no document in this round may be read as claiming otherwise:

- a production PostgreSQL deployment or any real database;
- a real event broker — Kafka, RabbitMQ, NATS or otherwise — or any
  transport, topic-naming or partitioning decision;
- an external schema-registry product;
- a production search engine or search index;
- a production IAM or identity provider;
- identity implementation (PACK-14);
- voting or tally implementation (PACK-15/16);
- backup or restore readiness (PACK-17);
- multi-region deployment;
- legal activation of any workflow.

"PostgreSQL-compatible" is an architectural direction recorded in ADR-069,
not a vendor choice, and no engine dependency exists anywhere in the
repository to make it one. Nothing here establishes that a persisted
record is admissible, that a migration was lawful, or that a retention
decision satisfied a legal basis. Each remains a human legal judgement made
outside this system.

## 16. Archive hygiene

Built from `git ls-files`, so nothing untracked could enter, then verified
by extracting the result and scanning it. The archive contains **no**
`.git`, `.venv`, `node_modules`, `.next`, `dist`, `build`, `__pycache__`,
`.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.hypothesis`, coverage
artifact, temporary file, OS metadata file, secret, credential, local
environment file or nested archive of any kind. There is no candidate ZIP
and no verification ZIP inside it, no duplicate Master Register, no
duplicate PACK-13 FIR coverage matrix, no duplicate ADR filename and no
obsolete duplicate documentation path.

Two hygiene decisions are worth recording rather than leaving to be
noticed:

1. **PACK-12's temporary correction notes are absent.** `DELETE.txt`,
   `PACK-12-CI-FORMAT-CORRECTION.md` and `PACK-12-CI-FORMAT-CORRECTION-2.md`
   exist in the verified CI checkout but are superseded by
   `docs/handover/PACK-12-FINAL-PASS-REPORT.md` §7 and have no place in a
   cumulative archive.
2. **The external-CI transcripts are now tracked.** `.gitignore` excluded
   `*.log`, which silently kept `docs/handover/PACK-09-EXTERNAL-CI-VERIFICATION.log`
   and `PACK-11-EXTERNAL-CI-VERIFICATION.log` out of `git ls-files` even
   though the PACK-12 baseline archive contained both. Since this round
   makes PACK-13's transcript a required path, a gitignored required path
   would fail the manifest on any fresh clone. `.gitignore` now carries
   `!docs/handover/*.log`, and all three transcripts are tracked and
   present.

## 17. Documentation changed by this packaging round

- `docs/handover/PACK-13-FINAL-PASS-REPORT.md` — **new**, this document.
- `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md` — **new**.
- `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log` — **new**, the raw
  transcript.
- `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` — the
  consolidated register adopted at its canonical path, plus this round's
  four required status changes.
- `README.md`, `CHANGELOG.md`, `docs/adr/README.md`, `services/README.md`,
  `services/data-plane-service/README.md` — status and index updates.
- `docs/handover/PACK-13-KNOWN-LIMITATIONS.md` — status block, limitation
  13 (local verification, now complemented by the external run) and
  limitation 14.
- `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md` and
  `PACK-13-FIR-COVERAGE-MATRIX.md` — status blocks only; no criterion,
  treatment or appendix row changed.
- `docs/packs/PACK-13/PACK-13-SPECIFICATION.md` — one superseding status
  note; the original header is preserved.
- `scripts/check_repository.py` — three required paths added.
- `.gitignore` — the `!docs/handover/*.log` exception explained in
  section 16.
- `uv.lock` and `docs/frontend/FRONT-00-PAGE-INVENTORY.csv` — adopted from
  the externally verified tree, as recorded in section 10.

**`docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md` and
`docs/handover/PACK-13-SPEC-ADR-REPORT.md` are retained unmodified.** Each
round genuinely was what it said it was at the time, and rewriting either
to read as though it had always been a FINAL PASS would destroy the record
this handover chain exists to keep.

---

## 18. Files added since the PACK-12 FINAL PASS baseline (75)

| File                                                                          | SHA-256                                                                                          |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `contracts/reason-codes/pack-13.yml`                                          | `0008f5ddafff420305cc291ac2a2e0085f574f056145c00c7c651376093b6417`                               |
| `docs/adr/ADR-069-PRODUCTION-RELATIONAL-DATA-PLANE.md`                        | `b55c6bf7f281ccf58cac54e361a24e16849c73e3d5674a429691a1aa65f6c017`                               |
| `docs/adr/ADR-070-DOMAIN-DATA-OWNERSHIP.md`                                   | `01ced126402f54ef238a0ffa95bde43c5adb4c475db3ac3a175598066696ad92`                               |
| `docs/adr/ADR-071-TRANSACTIONAL-OUTBOX.md`                                    | `27ecec8ef96a9e65f89abf00ec1cb4e050d8e9f8ad11f15b61656ffc98972a27`                               |
| `docs/adr/ADR-072-AT-LEAST-ONCE-DELIVERY-AND-IDEMPOTENT-CONSUMERS.md`         | `68dc00f1a257fc0ae7d1fbb7413b4e942f1c62a200d8e11e730527a9147d8254`                               |
| `docs/adr/ADR-073-CANONICAL-SCHEMA-REGISTRY.md`                               | `bb688fdb6eaa3ab4c93457926a1309524e98cf20c21244b5f9a2763e73d92d13`                               |
| `docs/adr/ADR-074-API-AND-EVENT-CONTRACT-EVOLUTION.md`                        | `a8b629fbf6afee85cbcf7bc35260860d6e517936f15af7ab496bcd1d4b8ea6a1`                               |
| `docs/adr/ADR-075-DATABASE-MIGRATION-DISCIPLINE.md`                           | `c1ede51f2b6e44e3e428fd0e51b50f9be79ccb1962bcb4c92d924d981447e9e5`                               |
| `docs/adr/ADR-076-PROJECTION-AND-READ-MODEL-GOVERNANCE.md`                    | `8e4522a5664052e468aed4bdd278fd07d0e4964d8f64a5720c2294485b4bb68b`                               |
| `docs/adr/ADR-077-CONCURRENCY-AND-IDEMPOTENCY.md`                             | `b9803bd5df636ccc8616fed0bbd8defaa669bc65a2a588a1417f638b6a138ae4`                               |
| `docs/adr/ADR-078-DATA-PLANE-RETENTION-LEGAL-HOLD-AND-EVIDENCE.md`            | `ec1205bcf0578a010bab689f16ccdcf36a63ed48c3f9fdb6259d5f486fa8499b`                               |
| `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION-RESULT.md`                    | `bb7e3dd1a3d240e3d124bced5248f1747b056bf9d0efa8311f625493b37e76b0`                               |
| `docs/handover/PACK-13-EXTERNAL-CI-VERIFICATION.log`                          | `5a913b0250b7a9dc94eebdfa19d339c8dbeb0ce963cd3145bfedecf5f8319caa`                               |
| `docs/handover/PACK-13-FINAL-PASS-REPORT.md`                                  | _self-referential — a file cannot contain its own digest; compute it from the delivered archive_ |
| `docs/handover/PACK-13-IMPLEMENTATION-CANDIDATE-REPORT.md`                    | `0ee3b20e0f863903235150c2727c369b7790767c5300bd53e438fcf08cc925c1`                               |
| `docs/handover/PACK-13-KNOWN-LIMITATIONS.md`                                  | `fe16f016593f5fd1e71b586c98f8e22d08dea252bab4a1f3909a824cfc16bbf6`                               |
| `docs/handover/PACK-13-SPEC-ADR-REPORT.md`                                    | `a9f29182a6c8ce1dbe6c2a2db732f1b2010d6892f052647a115bdad8921904bf`                               |
| `docs/packs/PACK-13/PACK-13-ACCEPTANCE-MATRIX.md`                             | `a791843fb07f3bd4af6df8862701bbd150154f68d87eb6b5a812c7c9e03723f3`                               |
| `docs/packs/PACK-13/PACK-13-CANON-ASSESSMENT.md`                              | `3e72cfa1966d6ab807bc6aae225f16ad9710c8e0379f47da7570395006a553a3`                               |
| `docs/packs/PACK-13/PACK-13-DATA-OWNERSHIP-MATRIX.md`                         | `decd441b2189c1896ed3ceb8f12b8ad15bf6c9bfc34b21ef50ee36c0fd35485f`                               |
| `docs/packs/PACK-13/PACK-13-EVENT-CATALOG.md`                                 | `7e7038b402c9ce8db1a774ce8a29117e0afe51c174d494e8f77d51369ba7bfc3`                               |
| `docs/packs/PACK-13/PACK-13-EVENT-DELIVERY-MATRIX.md`                         | `44e3e1b429a4a3bff21f2e5afde3f1120514f8aecd25f11e8cd450753ae59bcd`                               |
| `docs/packs/PACK-13/PACK-13-FIR-COVERAGE-MATRIX.md`                           | `3528a32716c5634640b85e04b4c8db85f990fb5e3e3920031f98b8c283574fb6`                               |
| `docs/packs/PACK-13/PACK-13-MIGRATION-CONTROL-MATRIX.md`                      | `09d3a716171dbfde49531c1274348291d1e4a9755668da8613ff3b18a1383fa3`                               |
| `docs/packs/PACK-13/PACK-13-REASON-CODE-CATALOG.md`                           | `e6e85712de7ab7999ac655dd9bdc8ebb35c32ff332f3128b5e1edd56bba47242`                               |
| `docs/packs/PACK-13/PACK-13-SCHEMA-COMPATIBILITY-MATRIX.md`                   | `29bcfb215b35228bc30b0130779799dae4a2190b9e1092dfa2081247b5162cb1`                               |
| `docs/packs/PACK-13/PACK-13-SPECIFICATION.md`                                 | `8f7a596e15100172d13d37eca873763a2aada59b955330b5a71920105b7c7723`                               |
| `docs/packs/PACK-13/PACK-13-THREAT-MODEL.md`                                  | `a6e1651a0b941fe1a4fe3b8ebd8bb21984035ecc02b59479193222ae029d8166`                               |
| `services/data-plane-service/README.md`                                       | `e8e3d36d2d9f83420caf8e57760cf5a5e3ed12ec98cfa19858a5724dc1eb5c5b`                               |
| `services/data-plane-service/pyproject.toml`                                  | `b7da5ad1a3f9f3f1e2ccc4e8282d262fca2e52e53744c5640875af440a3ffb46`                               |
| `services/data-plane-service/src/epd2_data_plane_service/__init__.py`         | `3e9ecf5621f6f15fe70abbadb5da78823e40903aea7776234235769ec9defbe3`                               |
| `services/data-plane-service/src/epd2_data_plane_service/administration.py`   | `1c414eeeab15530ed427541cc97164186f624d66605e19535296a1c42a3fc14b`                               |
| `services/data-plane-service/src/epd2_data_plane_service/application.py`      | `ee3dbf88735a0c498caed77d4fbed03f955e9751e35f0dcf9bc45b9a8646ea7a`                               |
| `services/data-plane-service/src/epd2_data_plane_service/backfill.py`         | `bcbc32bfa1dbcbc2b3af7046ec52ad9a2bf8d71a7d209b16dfb96dd7e3e0ba80`                               |
| `services/data-plane-service/src/epd2_data_plane_service/boundaries.py`       | `1f91e26bf65b6b10bf61c32e7cf58e66120f11038e2eb2e2ca69f7a05b057ab2`                               |
| `services/data-plane-service/src/epd2_data_plane_service/canonicalization.py` | `55b66746c6d38b5e07f0fac4d657f1502c68a60647b96a0dd3413c8ba80a9f5a`                               |
| `services/data-plane-service/src/epd2_data_plane_service/compatibility.py`    | `06e0f5ac987b60e0fd79405ef0ee85a2b1cf54c53678ec6f96f41c9e28e8483c`                               |
| `services/data-plane-service/src/epd2_data_plane_service/concurrency.py`      | `19e11fed42fe0a607f861d507478de45bf2bcb4ece58701f9a105327c09c16cf`                               |
| `services/data-plane-service/src/epd2_data_plane_service/contracts.py`        | `bd63b39711c62c12ee6d7e7dbcfbb9f4b090552c2dc96a88523ee806127177bd`                               |
| `services/data-plane-service/src/epd2_data_plane_service/delivery.py`         | `a85c6aa4a24cc8c840d204513b02df630f6c005207ad0e90d2219a2936debec9`                               |
| `services/data-plane-service/src/epd2_data_plane_service/domain.py`           | `435ce8074ac6b811b6b4a084084d21d757ca60025a7b3bed527a453bca6a7a86`                               |
| `services/data-plane-service/src/epd2_data_plane_service/events.py`           | `a967def5a8c35ac6847d0b8cfe50d4c9b52751fc25942d92601b939f2a96d7d2`                               |
| `services/data-plane-service/src/epd2_data_plane_service/exceptions.py`       | `fcf66f34481bb1540684d3cd364ec53db8eac2956656d54a3d5b36dce4224c66`                               |
| `services/data-plane-service/src/epd2_data_plane_service/idempotency.py`      | `4e451b539893d5b2b5b16d7dd27af6f7c353730790ac275142182555e2118472`                               |
| `services/data-plane-service/src/epd2_data_plane_service/integration.py`      | `b96e86fbe6309c8e2b84f3511ebe7e7dc51e8c8d655bfb8d098afeeeabcbe6ec`                               |
| `services/data-plane-service/src/epd2_data_plane_service/migrations.py`       | `a542be10366e030b609338a5653c0ab587721607002afd10ef00f6f64161bf08`                               |
| `services/data-plane-service/src/epd2_data_plane_service/outbox.py`           | `04ae768586975ef6b252c1cf6684e85a3d7484614a7e9bcb02a4adcd6ce56886`                               |
| `services/data-plane-service/src/epd2_data_plane_service/privileged.py`       | `bfcaa224d4c58f2c77990e37530c89d9e2cb7efa5dec91a93185de5628ffae70`                               |
| `services/data-plane-service/src/epd2_data_plane_service/projections.py`      | `3ca66a63d67bd394c65d81775c502d3ba11ba4df4c6bba4fd2fd797381ea4f03`                               |
| `services/data-plane-service/src/epd2_data_plane_service/registry.py`         | `0a44598faed5d8ba2ccd0871a57dda1ebfb62fe880fd1b793c2db612fbcc83f0`                               |
| `services/data-plane-service/src/epd2_data_plane_service/retention.py`        | `dcecd4d629ceed3806a3142ae927cb370010346adac23b04be263b6f18dac2a4`                               |
| `services/data-plane-service/src/epd2_data_plane_service/storage.py`          | `21071126e7fb3cef518eadea311041eeb2defe395a8b959ff14bb01100482bc4`                               |
| `services/data-plane-service/tests/_data_plane_builders.py`                   | `3076c7d3b61100a1e686bdb92c8d0b20329a7d3f1cafc53bc26c1d44093ed1f8`                               |
| `services/data-plane-service/tests/conftest.py`                               | `777744cfcd6962efd718e5779c49af5bec908d1d0617d14f183fa2f7fb989869`                               |
| `services/data-plane-service/tests/test_administration.py`                    | `57910225e52227f3e08e855b05b748ccbb9da812446b06097bb31910c6f2e1f6`                               |
| `services/data-plane-service/tests/test_backfill.py`                          | `1c528f736398558d968d3e5c42d5d89331fbc32c26c37cc3671381a6e696e663`                               |
| `services/data-plane-service/tests/test_boundaries.py`                        | `c386a20c6951032ed95b412e585a71c1bbe01d4b00b1c0e35ed1d0af3a0a22d7`                               |
| `services/data-plane-service/tests/test_canonicalization.py`                  | `c79fa531554c0c69d9b59bd94afea56c71e3a01a652e2f33c844f93ebf7bfc3d`                               |
| `services/data-plane-service/tests/test_compatibility.py`                     | `43aec17119c6336e05954947383d7b7e2fa4a9729f822938d29dfa41393ae5fd`                               |
| `services/data-plane-service/tests/test_concurrency.py`                       | `d9696b734e36cd8db81b619dfdc0b51f3cd67aee894f1e750648c8472abc81eb`                               |
| `services/data-plane-service/tests/test_contracts.py`                         | `79b9f6d50d0d7864d5ff6920a1fa784490dfb575a04770daa9266a08faaf9b33`                               |
| `services/data-plane-service/tests/test_data_plane_application.py`            | `bdf6c6d65a150bfe27e1278e77a17fd1d57a32f65219b3ac2e04d3562003bf0f`                               |
| `services/data-plane-service/tests/test_delivery.py`                          | `d17aaef86be739bc9844b7537e6674edf87b3ab5b4e1c07e9427bda2024146fa`                               |
| `services/data-plane-service/tests/test_domain.py`                            | `6a51f9119ae289962039645821c84f2bbef5390c992dffad247dbcccf7bd498e`                               |
| `services/data-plane-service/tests/test_events.py`                            | `55b5db5d03323404f86036be9f5a691f01f5bc64acb5ab8f3308bcbdb7ddfae8`                               |
| `services/data-plane-service/tests/test_idempotency.py`                       | `b91910f7f2741ead5edf1ac2e4eb2c80eefbb638149a788c29ce4f2783ea57a7`                               |
| `services/data-plane-service/tests/test_integration.py`                       | `00f037e672d17b772204a1faceac85542e6c9ea63a7c765c869dae5afa614aa7`                               |
| `services/data-plane-service/tests/test_migrations.py`                        | `5d297427a28617b8516887bfd82bf72d7e446ffd6f1c7aa7436829caa4df2ed8`                               |
| `services/data-plane-service/tests/test_outbox.py`                            | `61960492df6ef57d3e2854309977f0b8c552d982bf6f9ee1fb39887c39d7d261`                               |
| `services/data-plane-service/tests/test_privileged.py`                        | `c66cc9ec52a9e2536a60d3c8b70f6599c942d9d73695c99547b28086ff6dbe72`                               |
| `services/data-plane-service/tests/test_projections.py`                       | `3465420e1b349d2b927c831cd678acb16a0518a902ddc46ff55f6b6b26fbaf27`                               |
| `services/data-plane-service/tests/test_registry.py`                          | `66fcbc3c0165b45dbfb681c899858bb8232bb4bc65897729ce2001846d5b0cf6`                               |
| `services/data-plane-service/tests/test_retention.py`                         | `1e9026b2c601ec07b9cec552dabe199f8d4ae39cfb2d82f2539e8eed2e230b6d`                               |
| `services/data-plane-service/tests/test_storage.py`                           | `cc2bc8e7723cee4533534619b316b5e40f360bf18a32e7f0ae9b2cfbda1efa73`                               |
| `tests/repository/test_pack13_fir_matrix.py`                                  | `26872bc04bb7dd0c68eb6629abb82bbf89d311f3e23469e61d4f65bf52c822d7`                               |

---

## 19. Files changed since the PACK-12 FINAL PASS baseline (19)

| File                                                         | SHA-256                                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| `.gitignore`                                                 | `063ea13f8ff2eda2f576b5afe302f207435f06a58e86c9492e9d5d9669186862` |
| `CHANGELOG.md`                                               | `e567c87d209b18144a3affbf34639f576f9d7b273a01284e1f491cf0925b93fb` |
| `Makefile`                                                   | `6bb0041505f21866b906c5e000bd72b6a0dd66663668962ad9c9213aa845adb9` |
| `README.md`                                                  | `97bf3d5fdcac2423f9842c34835032e9bc23688ca036abb8a76fadae5ae50f46` |
| `docs/adr/README.md`                                         | `793284adbeb5d20a47e3a7bbeba8274e9f4c3d622c03035d34ea4aa7bb3568c2` |
| `docs/canonical/canon-version.json`                          | `d782700476e47015c7bd1c49d102b8f4ec1f6c3ee71588e0de7e9aa9529287f1` |
| `docs/frontend/FRONT-00-PAGE-INVENTORY.csv`                  | `7dc3cc97e43a8527faeb4417de88d0b9b7413535bd4402a0259dcb0fcfdf95a0` |
| `docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md` | `8d35a7551a28d1156fd8f2c66e37c4db4659589cf46e4f7e2ee83a161115c278` |
| `packages/python/epd2-core/src/epd2_core/version.py`         | `2d567710a30c671b17dabf63a5c23cd09fc962ad1e7420bbdf74ff8c720a7e81` |
| `packages/python/epd2-core/tests/test_version.py`            | `4836562710ea602da4ea921053b17eea398dffe8897002feb633b5b414354ce4` |
| `packages/typescript/epd2-types/src/version.ts`              | `73f02d60fe673e86d6801fb7a3c914f1cdccfdac1bf93b481145bc18746671f6` |
| `packages/typescript/epd2-types/tests/version.test.ts`       | `b9bc46f68c9d2c644b39d86b87c79d889ae61fb908f3c24d76a289c6c6566936` |
| `pyproject.toml`                                             | `12595bdb6b0bbfc91f83b55091b63d9f6ab41f183aac2b36c33480d1625389f3` |
| `scripts/check_canon_0_8_0.py`                               | `b5affc4c0d7cb768f2dee453b366114c06e8400fa7702dc28e3dc66846791494` |
| `scripts/check_repository.py`                                | `fe0eff7a980b21a56fbbb12d57f06a4bdac3ebd97fb521cf8c6caf137753cd62` |
| `services/README.md`                                         | `fc97cb909e882ea5f53f9c74aad93a0784da7c5b1ec140d6dc8706197392cd0e` |
| `tests/contract/_schema_helpers.py`                          | `3562b3aefaf61910595dc0f009cc781eaf0916aff54cb5ef08a233665ae1bf77` |
| `tests/contract/test_reason_codes_registry.py`               | `fa78a628d7394d23b24042abbc3e082c40f44206b52f2168b7098bf57af79edf` |
| `uv.lock`                                                    | `1a1e5a72b67b92a53b189e6eb9c9f4305f236a0aa76f7d55887f24ad2a76d543` |

---

## 20. Files removed

None. The two external-CI transcripts that the PACK-12 baseline carried
and that `git ls-files` had been silently dropping are restored and
tracked — see section 16.

---

## 21. Archive digest

The SHA-256 of the delivered archive is reported in the delivery message
accompanying it, and is deliberately not printed here: a file cannot
contain the digest of the archive that contains it.

```bash
sha256sum EPD2_PACK-13_PRODUCTION_DATA_PLANE_CONTRACT_EVOLUTION_0.13.0_FINAL_PASS.zip
```

# CLAUDE-PACK-08 — Organization & Regional Scope Foundation: Specification/ADR Round Handover Report

Status: **specification and ADR round complete, documentation only —
including a subsequent targeted correction round (2026-07-25, "PACK-08
SPEC CORRECTION + OWNER DECISIONS").** No service code, database,
migration, infrastructure, or production integration is authorized or
delivered by this round or its correction. **No external GitHub
Actions run has ever been performed for PACK-08, and none is claimed
by this report.** This report covers exactly what was produced and
what was locally verified before packaging, honestly distinguishing
this round's own local results from PACK-07's separately-confirmed
external result (section 6).

## 0. What this round adds

- `docs/packs/PACK-08-SPECIFICATION.md` — the complete PACK-08
  specification: organization model, concept separation, organizational
  relationships, effective dating, reorganization workflows, regional
  authorization, institutional authority assignments, role lifecycle,
  cross-domain migration summary, privacy/minimization, events, reason
  codes, frontend slice, hard invariants, exclusions, and a version/
  verification/deliverables closing section. **Corrected in place**
  (section 9) with owner decisions on the organizational graph model,
  inheritance-policy ownership, temporary-supervision duration, the
  non-combinable-role baseline, `RoleAssignment.scope_id` classification,
  `parent_reference`'s non-authoritative status, and the mandatory
  canon-amendment gate.
- Five ADRs, now all `accepted` (moved from `proposed` in the
  correction round, section 9), all authored against canon `0.6.0`
  with **no canon edit performed** — but each now stating explicitly
  that a canon amendment is **required, not conditional**, before
  implementation:
  - `docs/adr/ADR-032-organization-and-civic-space-ownership.md`
  - `docs/adr/ADR-033-organizational-relationships-effective-dating-and-reorganization.md`
  - `docs/adr/ADR-034-regional-scope-authorization-and-inheritance.md`
  - `docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md`
  - `docs/adr/ADR-036-institutional-authority-assignments-and-non-combinable-roles.md`
- `docs/packs/PACK-08-MIGRATION-MATRIX.md` — the complete field-by-field
  classification of every current `organization_id`/`region_code`/
  `jurisdiction`/`scope_type`/`scope_id`/`civic_space_id`-shaped/
  `role_scope`-shaped reference found in the repository, each traced to
  its actual current source and behavior. **Corrected** (section 9)
  with the six-category `RoleAssignment.scope_id` classification
  scheme.
- `docs/packs/PACK-08-OPEN-DECISIONS.md` — eighteen consolidated,
  unresolved questions (OD-1 through OD-18) surfaced by the
  specification and the five ADRs, for owner/legal/security review.
  **Corrected** (section 9): OD-5, OD-8, OD-10 closed; OD-7 and OD-11
  partially closed / closed at policy level; OD-18 closed definitively.
- This report. **Corrected** (section 9) to state exact, honest local
  verification results for this round, distinct from PACK-07's own
  confirmed external result.
- `docs/adr/README.md` — updated with five new index rows (ADR-032
  through ADR-036) and a short narrative entry for this round,
  **corrected** (section 9) to show status `accepted` rather than
  `proposed`.

## 1. Baseline this round was authored against

- `REPOSITORY_VERSION = 0.7.0`, `CANON_VERSION = 0.6.0` (both
  unchanged by this round — see section 5).
- CLAUDE-PACK-01 through CLAUDE-PACK-07 — PASS; PACK-07 implementation
  externally verified (`docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`
  section 6a).
- ADR-026 through ADR-031 — accepted.
- The user-supplied master planning baseline (`MASTER-ARCHITECTURE-0.8.md`,
  `MASTER-ROADMAP-0.8.md`, `HARD-INVARIANTS-0.8.md`,
  `ARCHITECTURE-GAP-REGISTER.md`, `PACK-08-PROPOSAL.md`) — the "master
  review revision," confirmed approved before this specification round
  began, naming PACK-08 as the next recommended step and requiring
  exactly a specification/ADR round, not implementation, as the
  immediate next action (`ARCHITECTURE-GAP-REGISTER.md` section 7,
  "Recommended immediate action").
- Existing canon 0.6.0 content directly engaged: sections 5.4
  (Organization Context, responsibility only), 8.1 (`Organization`), 8.2
  (`CivicSpace`), 8.3 (`Membership`, carrying `organization_id`/
  `region_code`), 8.4 (`RoleAssignment`, carrying `scope_id`) — all read
  and classified, none amended.
- `docs/handover/PACK-07-SPEC-FINAL.md` section 11 — the explicit,
  already-on-record deferral of all real organizational-hierarchy work
  to "PACK-08," confirmed and now acted on by this round's specification
  and ADRs.

## 2. Research performed before drafting

Before drafting any specification or ADR content, the repository was
searched for every field name the governing request asked to be
classified, to ensure the migration matrix (section 0 above) reflects
actual current behavior rather than assumption:

```bash
grep -rln "organization_id" services/ contracts/ docs/canonical/*.md
grep -rln "region_code" --include="*.py" --include="*.md" \
  --include="*.json" --include="*.yaml" --include="*.yml" .
grep -rln "jurisdiction" ...
grep -rln "scope_id" ...
grep -rln "scope_type" ...
grep -rln "civic_space_id" ...
grep -rln "role_scope" ...
```

Findings (full detail in `docs/packs/PACK-08-MIGRATION-MATRIX.md`):
`organization_id` is used only inside `membership-service` (canon 8.3's
`Membership.organization_id`), never dereferenced by any other service;
`region_code` is likewise `membership-service`-only; `jurisdiction`
appears only on `eligibility-service`'s `ProcessEligibilityPolicy`
(ADR-028), explicitly "structure only"; `scope_type`/`scope_id` appear,
heterogeneously, across `governance-service`, `credential-service`,
`delegation-service`, `voting-service`, `initiative-service`,
`eligibility-service`, and `membership-service`, with at least three
genuinely different meanings depending on service; `civic_space_id`
does not exist anywhere in the repository today (`CivicSpace`'s own
primary key is `space_id`); `role_scope` exists only as
`transparency-service`'s unrelated `GENERALIZE_TO_ROLE_SCOPE`
redaction-transformation enum value, a false cognate flagged explicitly
rather than silently conflated.

## 3. Canon integrity

No canon edit was made or proposed at this stage, in either the
original specification/ADR round or this correction round.
`docs/canonical/TZ-00-domain-event-canon.md` is untouched; its checksum
is unchanged; `CANON_VERSION` remains `0.6.0`.

**Owner decision, correction round (closes OD-18 definitively):** PACK-08
introduces canon-relevant concepts — `Organization`, `CivicSpace`,
`OrganizationalRelation`, `OrganizationalAuthority`,
`OrganizationalScope`, regional scope authorization, institutional
authority lifecycle, and reorganization/successor invariants — that do
not exist in canon 0.6.0 today. Therefore PACK-08 implementation must
not start before a separate canon amendment round; `CANON_VERSION` and
the canon checksum remain unchanged in this correction round; a future
canon ADR must be prepared and accepted before implementation. This
**supersedes** this document's original framing (a conditional canon
ADR needed "only if the accepted implementation adds/changes canonical
fields") — the canon amendment is now a **mandatory precondition**, not
a contingency. All five ADRs (now `accepted`, section 9) restate this
identically in their own "Related canon version" sections.

## 4. Scope discipline

Per the governing request's explicit instruction, this round contains
**no** service code, database schema, migration script, infrastructure
configuration, or production integration. No file under `services/`,
`packages/`, or `contracts/` was created or modified. No
`contracts/reason-codes/pack-08.yml`, JSON Schema, event-payload schema,
or OpenAPI file was created — the reason codes (specification section
14), events (section 13), and API surface these will eventually need
are specified in prose within the specification and ADR documents
themselves, deferred to a future implementation round's own contract
deliverables, consistent with the nine deliverables actually listed by
the governing request's item 17.

Documentation supersession for the four stale documents named by
`PACK-08-PROPOSAL.md` section 10 and `ARCHITECTURE-GAP-REGISTER.md`
GAP-052 through GAP-055 (`docs/review/KNOWN_LIMITATIONS.md`,
`docs/architecture/data-ownership.md`,
`docs/architecture/system-context.md`,
`docs/review/PACK-07-OWNER-DECISIONS.md`) was **not** performed this
round — tracked as `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-17,
since the master baseline itself frames that supersession as a PACK-08
_implementation_-round action, not a specification-round action.

## 5. Versions

**Unchanged by this round, confirmed:**

```bash
python3 scripts/verify_versions.py
# OK: all version sources are consistent.
```

`REPOSITORY_VERSION` remains `0.7.0`
(`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`). `CANON_VERSION`
remains `0.6.0` (`docs/canonical/canon-version.json`). No file under
either version-declaration path was edited.

## 6. Verification performed this round

Since this round changed no service/contract/test code, verification
focused on confirming no regression and on repository-structural
honesty:

```bash
python3 scripts/check_repository.py
# OK: all 402 required paths are present.

python3 scripts/verify_versions.py
# OK: all version sources are consistent.
```

`scripts/check_repository.py`'s `REQUIRED_PATHS` was **not** extended
with the nine new documents this round produces. This mirrors the
repository's own existing, established pattern: ADR-026 through
ADR-031 and PACK-07's own `SPEC`/`SPEC-FINAL`/`CANON-AMENDMENT-REPORT`/
`OWNER-DECISIONS` documents were likewise never added to
`REQUIRED_PATHS` during the PACK-07 specification/canon round (only
contract/service paths were added, during PACK-07's later
_implementation_ round) — confirmed by inspecting
`scripts/check_repository.py`'s own current content before drafting
this report. This round follows the same precedent rather than
introducing a new one; extending `REQUIRED_PATHS` to track every
historical spec/ADR document remains an open repository-maintenance
question, not specific to PACK-08.

The full existing Python test suite was re-run to confirm this round's
documentation-only changes introduced no regression (using the
established `PYTHONPATH` workaround from `LOCAL_VERIFICATION.md`):

```bash
export PYTHONPATH=$(python3 -c "
import glob
paths = glob.glob('services/*/src') + glob.glob('packages/python/*/src')
print(':'.join(paths))
"):/usr/local/lib/python3.11/dist-packages

/root/.local/bin/ruff check .
/root/.local/bin/ruff format --check .
/root/.local/bin/mypy packages/python/epd2-core scripts tests/repository conftest.py
/root/.local/bin/mypy tests/contract
/root/.local/bin/mypy services/<each-service>
/root/.local/bin/pytest packages/python/epd2-core tests/repository -q
/root/.local/bin/pytest tests/contract -q
/root/.local/bin/pytest services -q
```

**Exact results, this correction round's own fresh local re-run
(2026-07-25), not copied from any prior round:**

```text
ruff check .                    -> All checks passed!
ruff format --check .           -> 186 files already formatted
mypy (core/scripts/repository)  -> Success: no issues found in 25 source files
mypy (contract)                 -> Success: no issues found in 20 source files
mypy (all 15 services)          -> Success: no issues found, each service
pytest packages/python/epd2-core tests/repository -q
                                 -> 94 passed, 1 failed
pytest tests/contract -q        -> 915 passed, 5 skipped
pytest services -q              -> 1011 passed
scripts/check_repository.py     -> OK: all 402 required paths are present.
scripts/verify_versions.py      -> OK: all version sources are consistent.
```

**Total: 2020 passed, 5 skipped, 1 failed.** The single failure is
`tests/repository/test_no_forbidden_paths_present`, an expected,
self-resolving cache-artifact detection (`.mypy_cache/`,
`.pytest_cache/`, `.ruff_cache/`, and per-service `__pycache__/`
directories created by the verification commands themselves, mid-run,
before cache cleanup) — not a real code or documentation defect. This
is **0 real failures**, restated explicitly.

**This is NOT the same measurement as PACK-07's confirmed external
result, and this report does not claim it is.** PACK-07's own,
separately confirmed result was an **external GitHub Actions run**:
2028 passed, 4 skipped, 0 failed. This round's numbers above are an
**entirely different measurement** — a local sandbox re-run, in this
environment, without the network access, CI runner configuration, or
independent verification an external GitHub Actions run provides. The
totals differ (2020 vs. 2028 passed; 5 vs. 4 skipped) because this is
a different suite invocation on different infrastructure, not because
of any regression, and this report does not assert the two are
equivalent, comparable line-for-line, or "unchanged" from one another.
An earlier draft of this report used exactly that kind of comparison
language ("unchanged from the PACK-07 closeout baseline") — this was
flagged as misleading and is corrected here: no such equivalence claim
is made.

**No external GitHub Actions run has ever been performed for PACK-08,
and none is claimed by this report or by any PACK-08 document.** Every
number in this section is this sandbox's own local, honest self-report,
run fresh in this correction round, not reused from a prior session or
assumed unchanged.

A manual cross-reference pass was performed across all five ADRs and
the specification, confirming: entity names, field names, and
`role_code` values match exactly across every document; every
"Unresolved question"/OD- cross-reference in the ADRs resolves to an
actual entry in `docs/packs/PACK-08-OPEN-DECISIONS.md`; no ADR claims
an ownership, ordering, or classification decision that contradicts
another ADR or the specification; and every field cited in
`docs/packs/PACK-08-MIGRATION-MATRIX.md` was independently re-verified
against its actual source location (section 2, this report) rather than
copied from the master baseline documents without confirmation.

This is a **local, honest self-report** for a documentation-only round.
No external GitHub Actions run is claimed or implied.

## 7. Before archiving

No Python bytecode or tool caches were introduced by this round's own
work (no Python code was executed to produce these documents); any
caches present from the verification commands in section 6 are cleaned
immediately before the delivery archive is built, mirroring every
prior round's own documented practice
(`docs/handover/PACK-07-IMPLEMENTATION-REPORT.md` section 7).

## 8. Deliverables

- `docs/packs/PACK-08-SPECIFICATION.md` (corrected, section 9)
- `docs/adr/ADR-032-organization-and-civic-space-ownership.md` (corrected, `accepted`)
- `docs/adr/ADR-033-organizational-relationships-effective-dating-and-reorganization.md` (corrected, `accepted`)
- `docs/adr/ADR-034-regional-scope-authorization-and-inheritance.md` (corrected, `accepted`)
- `docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md` (corrected, `accepted`)
- `docs/adr/ADR-036-institutional-authority-assignments-and-non-combinable-roles.md` (corrected, `accepted`)
- `docs/packs/PACK-08-MIGRATION-MATRIX.md` (corrected, section 9)
- `docs/packs/PACK-08-OPEN-DECISIONS.md` (corrected, section 9)
- `docs/handover/PACK-08-SPEC-REPORT.md` (this file, corrected)
- `docs/adr/README.md` (updated index — status `accepted` — and narrative entry)
- `epd2-civic-os-PACK-08-SPEC-ADR-CORRECTED.zip` — one complete, clean
  archive (excludes `.git/`, `node_modules/`, `.venv/`, all caches,
  build output, nested ZIPs, and verification-result archives),
  superseding the original `epd2-civic-os-PACK-08-SPEC-ADR-CANDIDATE.zip`.

## 9. Correction round (2026-07-25) — "PACK-08 SPEC CORRECTION + OWNER DECISIONS"

Applied to the original PACK-08 specification/ADR candidate, per an
explicit, targeted correction request. **Owner decisions only; no new
implementation scope, no schema, no service code.**

### 9.1 Exact files changed

- `docs/handover/PACK-08-SPEC-REPORT.md` — this file: section 3 (canon
  integrity, REQUIRED framing), section 6 (honest fresh verification
  numbers, PACK-07-external vs. this-round-local distinction), section
  8 (archive name), this section 9 (new).
- `docs/packs/PACK-08-OPEN-DECISIONS.md` — OD-5, OD-8, OD-10 closed;
  OD-7 partially closed (minimum baseline adopted); OD-11 closed at
  policy level (enumeration still open); OD-18 closed definitively;
  summary table gained a Status column.
- `docs/packs/PACK-08-SPECIFICATION.md` — new section 0.1 (correction
  round summary); section 3.1 (`parent_reference` non-authoritative
  clarification; `OrganizationalHierarchyOverlapPolicy` and
  `OrganizationalInheritancePolicy` added to the entity list); section
  5.1 (multiple-typed-graph owner decision, replacing "reviewed
  exception" language); section 6 (overlap-validation cross-reference
  update); section 8.1 (modes 2/3/5 — inheritance-policy and 90-day
  temporary-supervision rules); section 8.2 (implicit-inheritance
  anti-pattern update); section 9.3 (eight-bullet non-combinable-role
  baseline); section 18 (REQUIRED canon-amendment framing); section 20
  (archive name).
- `docs/packs/PACK-08-MIGRATION-MATRIX.md` — section 1 (six-category
  exception noted for `RoleAssignment.scope_id`); section 2.3
  (rewritten with the six-category classification scheme,
  migration-blocked category-6 treatment, pre-migration table
  requirement); section 3 summary table row updated.
- `docs/adr/ADR-032-organization-and-civic-space-ownership.md` —
  status → `accepted`; new "Owner decision" section; testing
  requirements addition; unresolved-questions rewording; "Related canon
  version" rewritten to REQUIRED framing.
- `docs/adr/ADR-033-organizational-relationships-effective-dating-and-reorganization.md`
  — status → `accepted`; new "Owner decision" sections (graph model,
  `parent_reference`); hierarchy-category decision text rewritten;
  testing requirements additions; unresolved questions updated;
  "Related canon version" rewritten.
- `docs/adr/ADR-034-regional-scope-authorization-and-inheritance.md` —
  status → `accepted`; new "Owner decision" section (inheritance-policy
  ownership, temporary-supervision duration); decision modes 2/3/5 and
  anti-patterns updated; testing requirements additions; unresolved
  questions updated; "Related canon version" rewritten.
- `docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md`
  — status → `accepted`; new "Owner decision" section (six-category
  scheme); Decision section's `RoleAssignment.scope_id` paragraph
  rewritten to reconcile the six-category scheme with the ADR's own
  four-category top-level scheme; testing requirements additions;
  unresolved questions (OD-11) reworded; "Related canon version"
  rewritten.
- `docs/adr/ADR-036-institutional-authority-assignments-and-non-combinable-roles.md`
  — status → `accepted`; new "Owner decision" section (eight-bullet
  minimum-baseline matrix); "Non-combinable roles" subsection rewritten;
  testing requirements additions; unresolved questions (OD-7) reworded;
  "Related canon version" rewritten.
- `docs/adr/README.md` — status column for ADR-032 through ADR-036
  changed from `proposed` to `accepted`; narrative paragraph updated to
  describe the correction round and the canon-amendment-blocking
  caveat.

### 9.2 Owner decisions closed

OD-5 (organizational graph model — multiple typed directed graphs);
OD-8 (inheritance-policy ownership); OD-10 (temporary-supervision
maximum duration, 90 days default); OD-18 (canon amendment mandatory,
not conditional).

### 9.3 Owner decisions partially closed / closed at policy level

OD-7 (non-combinable-role matrix — minimum eight-bullet baseline
adopted; full legally-refined matrix remains open); OD-11
(`RoleAssignment.scope_id` classification — six-category scheme and
migration-blocked rule settled; concrete per-`role_code` enumeration
remains open).

### 9.4 Owner decisions still open

OD-1, OD-2, OD-3, OD-4, OD-6, OD-9, OD-12, OD-13, OD-14, OD-15, OD-16,
OD-17 — unchanged by this correction round; see
`docs/packs/PACK-08-OPEN-DECISIONS.md` for full detail on each.

### 9.5 ADR acceptance status

**ADR-032 through ADR-036 are all now `accepted`** — moved from
`proposed` because this correction round's owner decisions settle every
core architectural semantic question each ADR raised, leaving only
non-blocking legal-refinement details open (per the governing request's
own allowance). **Every one of the five ADRs' own acceptance is
explicitly qualified: acceptance does not authorize implementation.**

### 9.6 Canon amendment / implementation blocking status

**PACK-08 implementation remains blocked, explicitly and by design,
pending a separate canon amendment round.** This is stated identically
in the specification (section 18), in `PACK-08-OPEN-DECISIONS.md`
(OD-18, closed definitively), and in every one of ADR-032 through
ADR-036's own "Related canon version" and "Owner decision" sections.
`CANON_VERSION` (`0.6.0`) and the canon checksum are unchanged by this
correction round. No implementation code, schema, service, database, or
infrastructure change is authorized by this round or by the correction
round — this remains a specification/ADR-only deliverable throughout.

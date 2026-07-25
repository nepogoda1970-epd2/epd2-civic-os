# PACK-08 — Canon Amendment Report (ADR-037 Acceptance + Canon 0.6.0 → 0.7.0)

**Status: canon/documentation-only amendment round.** This report
covers the formal preparation and application of the canon amendment
PACK-08 required — ADR-037's acceptance and the resulting canon edit
(`CANON_VERSION 0.6.0 → 0.7.0`), performed 2026-07-25 following the
already-accepted `docs/packs/PACK-08-SPECIFICATION.md` and ADR-032
through ADR-036 (accepted in the prior PACK-08 spec/ADR round and its
subsequent spec-correction round). **No service logic was implemented.**
`services/organization-service` does not exist; no PACK-08 OpenAPI
file, JSON Schema, or executable reason-code registry was created. This
report distinguishes exactly what changed from what remains deferred,
reports local verification results honestly, and states plainly that
**no external GitHub Actions PASS is claimed** for this round.

**Updated 2026-07-25 during the PACK-08 CANON FINAL CLEANUP round**
(documentation and verification-language corrections only, no canon
substance changed): section 6 was rewritten to remove "0 real
failures"-style wording and report a genuine clean local rerun; section
9 was updated to match; sections 7–8 note the additional files changed
and the new `epd2-civic-os-PACK-08-CANON-0.7.0-PASS.zip` archive. See
each section for detail.

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072
CANON_VERSION = 0.7.0   (was 0.6.0)
REPOSITORY_VERSION = 0.7.0   (unchanged — see section 3)
```

## 1. Accepted ADR

ADR-037 is now `accepted`:

| ADR     | Subject                                         | Status                 |
| ------- | ----------------------------------------------- | ---------------------- |
| ADR-037 | Organization and Regional Scope Canon Amendment | `accepted`, 2026-07-25 |

ADR-032 through ADR-036 remain `accepted` (unchanged by this round —
they were accepted in the prior PACK-08 spec-correction round). ADR-037
is this round's own governing ADR: its acceptance directly authorizes,
and this same round performs, the canon-text edit — unlike ADR-032
through ADR-036, whose acceptance explicitly deferred the edit to this
dedicated later task (the same acceptance-then-canon-edit pattern
ADR-010/013/018/020/023/025/028 each already established for this
project).

## 2. Canon changes (`docs/canonical/TZ-00-domain-event-canon.md`)

`CANON_VERSION` moved `0.6.0 → 0.7.0` (minor, additive-only, per canon
section 25). Top-of-document version banner updated to `0.7.0`. No
existing field, event name/meaning, entity owner, status enum value, or
architectural invariant is removed, redefined, or reassigned.

**New section 19e — "Организация и региональная авторизация —
расширение" (Organization & Regional Scope Context)**, inserted between
existing sections 19d and 20 (the established non-renumbering technique
used for 19a/19b/19c/19d), with:

- **`Organization` (8.1) extended** with six additive fields:
  `organization_profile`, `parent_reference`, `effective_from`,
  `effective_until`, `dissolved_at`, `successor_reference` (19e.3). All
  six existing fields, four statuses, and the owner (Organization
  Service) are unchanged.
- **`CivicSpace` (8.2) confirmed unchanged** — all seven fields, five
  statuses, and owner (19e.6).
- **Four new canonical entities**, all owned by `organization-service`:
  `OrganizationalUnit` (19e.5), `OrganizationalRelation` (19e.7, the
  typed, versioned, effective-dated relationship edge —
  hierarchy/continuity/cooperation categories, multiple typed directed
  graphs, relation-type-specific cycle and overlap rules),
  `OrganizationalHierarchyOverlapPolicy` (19e.8, closes the former OD-5),
  `OrganizationalInheritancePolicy` (19e.13, closes the former OD-8).
- **`OrganizationalAuthority`** (19e.15), also owned by
  `organization-service`, distinct from and cross-referenced only by
  opaque reference with the existing `RoleAssignment` (8.4, Governance
  Context, unchanged in every field, status, and owner).
- **`OrganizationalScope`** (19e.11), a reusable value shape — not a
  separately owned entity, the same status already given to
  `RedactionManifest` (19c.4) and `AIDisclosurePackage` (19c.6).
- **Concept separation** (19e.2): Organization, Jurisdiction, CivicSpace,
  and process-local Scope fixed as four non-interchangeable concepts;
  `organization_id`/`jurisdiction`/`region_code`/`scope_id`/
  `civic_space_id` may never be silently reinterpreted across domains.
- **`parent_reference` non-authoritative rule** (19e.4): derived
  read-model/compatibility projection only; `OrganizationalRelation` is
  the sole authoritative source; never independently mutated; may be
  omitted entirely where it risks becoming a second source of truth.
- **Effective dating** (19e.9): `valid_from`/`valid_until`/`recorded_at`/
  `supersedes_*_id`, historical queryability, future-dated changes,
  relation-type-specific overlap validation, and the hard rule that
  current state never overwrites historical organizational truth —
  applied uniformly across `Organization`, `OrganizationalUnit`,
  `OrganizationalRelation`, and `OrganizationalAuthority`.
- **Reorganization** (19e.10): canonical rules for creation, activation,
  suspension, dissolution, merger, split, successor organization,
  renaming, and territorial reassignment, plus the hard rule that no
  authority, role, entitlement, access right, or institutional
  appointment transfers automatically to a merged, split, or successor
  organization — transfer always requires an explicit governed
  decision, effective date, and audit record.
- **Regional scope authorization** (19e.12): default-deny; six explicit
  access modes (exact, ancestor, descendant, delegated, temporary
  supervision, institutional oversight without implicit data access);
  hard rules that role names and hierarchy position are never proof of
  authority, frontend is never the source of authorization, consuming
  domains may restrict but never broaden inherited authority, no
  universal administrator may emerge through scope inheritance, and
  cross-scope access always requires explicit policy and audit.
- **Inheritance policy ownership** (19e.13) and **temporary supervision**
  (19e.14: mandatory `valid_from`/`valid_until`, 90-day default maximum,
  governed-decision-plus-audit-record extension, narrower-only future
  legal limits).
- **`OrganizationalAuthority`'s canonical fields** (19e.15):
  `authority_id`, `authority_version`, `role_code`, `scope`
  (`OrganizationalScope`), `appointing_authority_reference`,
  `assigned_subject_reference`, `valid_from`, `valid_until`, `status`,
  `revocation_reason_reference`, `policy_version`, `decision_reference`,
  `audit_reference` — independent `grants_procedural_authority`/
  `grants_data_access` booleans, never inferred from title alone.
- **Institutional roles and the minimum non-combinable-role baseline**
  (19e.16): seven named roles (DPO, election board member, election
  officer, independent auditor, finance auditor, party arbitrator,
  organizational administrator); the eight-bullet minimum baseline,
  marked as subject to legal refinement.
- **Role/authority lifecycle rules** (19e.17, eight rules) and **extended
  identity minimization** (19e.18, eight rules).
- **`RoleAssignment.scope_id` classification** (19e.19): six categories
  (organization/jurisdiction/CivicSpace/process-local/global-system/
  invalid-legacy-ambiguous scope); no silent reinterpretation; category-6
  values migration-blocked; global/system scope never implies universal
  administrative access. `RoleAssignment` (8.4) itself — fields,
  statuses, owner — is unchanged; only this classification rule for its
  `scope_id` field is newly canonical.
- **Structural separation with other contexts** (19e.22) and an explicit
  **implementation gate** (19e.23): canon defines the model only; no
  `organization-service` code, database, migration, event bus, frontend,
  or production integration is authorized by this section alone.

**Section 20.5 (Organization events)** gains thirteen entries:
`organization.activated`, `.suspended`, `.dissolved`, `.merged`,
`.split`, `.successor_declared`, `organizational_relation.created`,
`.ended`, `organizational_authority.assigned`, `.revoked`,
`regional_scope_access.granted`, `.revoked`, plus documentation of each
event's canonical owner, minimum/prohibited payload, effective/recorded
time, policy-version reference, audit linkage, idempotency expectation,
and privacy constraint (19e.20).

**Section 22 (ownership matrix)** gains five new rows:
`OrganizationalUnit`, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
`OrganizationalAuthority` — all "Organization Service." `Organization`
and `CivicSpace`'s existing rows are unchanged; `OrganizationalScope`
gains no row (reusable value shape, not a separately owned entity).

**Section 23 (forbidden links)** gains new entries: no read/write edge
from any of the seven new/extended entities to `VoteEnvelope`/`Tally`/
`Ballot`; role-name-is-not-proof-of-authority; hierarchy-position-is-
not-proof-of-authority; frontend-is-never-the-source-of-authorization;
no silent field reinterpretation for `organization_id`/`jurisdiction`/
`region_code`/`scope_id`/`civic_space_id`; `parent_reference` cannot be
independently mutated; hierarchy-category cycles forbidden without
exception; no automatic authority transfer on merge/split/succession;
category-6 `role_code` values migration-blocked; global/system scope
does not imply universal administration; `temporary_supervision_by`
without `valid_until` forbidden.

**Section 24 (reason codes)** gains ten codes:
`ORGANIZATION_NOT_ACTIVE`, `ORGANIZATION_SCOPE_MISMATCH`,
`CROSS_SCOPE_ACCESS_DENIED`, `AUTHORITY_ASSIGNMENT_INVALID`,
`AUTHORITY_ROLE_INCOMPATIBLE`, `AUTHORITY_SCOPE_INVALID`,
`SUCCESSOR_TRANSFER_REQUIRES_DECISION`, `ORGANIZATIONAL_RELATION_OVERLAP`,
`ORGANIZATIONAL_CYCLE_FORBIDDEN`, `HISTORICAL_SCOPE_NOT_EFFECTIVE` —
exactly the ten named by the governing request's item 14, verbatim, no
renaming of any existing code.

**No naming conflict found.** A repository-wide search performed as
part of this round (`grep -rn` across `docs/canonical/TZ-00-domain-event-canon.md`
section 24 and every `contracts/reason-codes/pack-0N.yml` file, section 3
below) confirmed none of the ten new codes, and none of the thirteen new
event names, collide with any existing registered code or event name.
No compatibility decision was required.

## 3. Repository version decision

**`REPOSITORY_VERSION` is unchanged, remaining `0.7.0`.** Per the
governing request's item 18 ("do not change `REPOSITORY_VERSION` in
this canon-only round unless repository policy strictly requires a
documentation release increment"): this repository's own established
policy (`scripts/verify_versions.py`) requires `REPOSITORY_VERSION` to
match the latest numbered `CHANGELOG.md` heading, not `CANON_VERSION` —
those two version numbers are tracked independently throughout this
project's history (see, e.g., `CANON_VERSION 0.3.0`/`REPOSITORY_VERSION
0.2.0` coexisting after the PACK-04 canon-only round, or the current
`CANON_VERSION 0.7.0`/`REPOSITORY_VERSION 0.7.0` coincidental match after
this one). This round adds a new `## [Unreleased] - canon minor version
0.7.0 (Organization & Regional Scope Context)` entry to `CHANGELOG.md`
(mirroring every prior canon-only round's own `[Unreleased]` entry
convention) rather than a new numbered heading, so the existing `##
[0.7.0]` heading (CLAUDE-PACK-07 implementation) remains the latest
numbered entry `scripts/verify_versions.py` matches against —
`REPOSITORY_VERSION` and that heading both correctly stay `0.7.0`, with
no increment needed or performed.

## 4. Generated-contract changes

**None.** No `contracts/reason-codes/pack-08.yml`, JSON Schema,
event-payload schema, or OpenAPI file was created or modified by this
round — consistent with every prior canon-only round's own precedent
(ADR-010, ADR-013, ADR-018/020, ADR-023/025, ADR-026 through ADR-031):
canon fixes the stable, canon-owned reason-code and event names
(sections 20, 24); the executable per-pack contract registry remains a
future implementation-round deliverable.

## 5. Implementation explicitly deferred (not performed by this round)

- `services/organization-service` — not created.
- Any database, migration script, or event-bus/transport implementation
  for the thirteen new events.
- `contracts/openapi/pack-08.yaml`, `contracts/reason-codes/pack-08.yml`,
  and every entity/event JSON Schema for the seven new/extended
  entities.
- Any frontend code (the minimal read-only slice named by
  `docs/packs/PACK-08-SPECIFICATION.md` section 15 remains
  unimplemented).
- Production IAM, eID integration, secrets/key management, deployment
  configuration.
- The concrete `RoleAssignment.scope_id` per-`role_code` migration table
  (19e.19; `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-11, closed at
  policy level only — the enumeration itself remains open).
- The complete, legally-refined non-combinable-role matrix beyond the
  eight-bullet minimum baseline (19e.16; OD-7, partially closed).
- `docs/architecture/data-ownership.md`, `docs/architecture/system-context.md`,
  and the other stale documents named by OD-17 — sequencing to a future
  implementation round unchanged by this canon-only round.

## 6. Verification performed this round

**This section was corrected during the PACK-08 CANON FINAL CLEANUP
round (2026-07-25) and replaces the original version's verification
text in full.** The original text below is superseded, not because the
underlying test suite changed, but because its "0 real failures"
framing converted a failed run into an implied PASS — flagged as
unacceptable and corrected per that round's explicit instruction not to
use that phrase or any wording that converts a failed test run into a
claimed PASS.

**Root cause identified.** This sandbox's copy of the repository has no
`.git` directory (`git rev-parse --is-inside-work-tree` fails with
`fatal: not a git repository`). `scripts/check_forbidden_files.py`'s
`find_forbidden_paths()` is git-aware: when `.git` exists it lists only
git-tracked/untracked-but-not-ignored paths via `git ls-files --cached
--others --exclude-standard`; when `.git` is absent — as here — it
falls back to a full, `.gitignore`-blind filesystem walk
(`_walk_all_paths()`), which flags _any_ cache directory present on
disk as forbidden, regardless of whether it would ever actually be
committed. This is why `tests/repository/test_no_forbidden_paths_present`
failed in the original run below, and in every prior verification round
in this project's history in this sandbox: verification commands
(`mypy`, `pytest`, `ruff`) were creating `.mypy_cache/`, `.pytest_cache/`,
`.ruff_cache/`, and `__pycache__/` directories mid-run, and the
non-git fallback walk was detecting them before any post-run cleanup
occurred. This was a real, avoidable side effect of how verification
was invoked, not an inherent defect in the repository.

**Fix applied: suppress cache-artifact creation for the entire
verification pass**, rather than clean up after the fact:

- `ruff check --no-cache .` / `ruff format --no-cache --check .` — no
  `.ruff_cache/` directory is ever created.
- `mypy --cache-dir=/dev/null <paths>` (for every group, including each
  of the 15 services individually) — no `.mypy_cache/` directory is
  ever created.
- `export PYTHONDONTWRITEBYTECODE=1` — no `.pyc` file or `__pycache__/`
  directory is ever created by any Python import during the run.
- `pytest -p no:cacheprovider <paths> -q` (for every group) — no
  `.pytest_cache/` directory is ever created.

```bash
cd /home/claude/epd2-civic-os

find . -type d \( -name "__pycache__" -o -name ".pytest_cache" \
  -o -name ".mypy_cache" -o -name ".ruff_cache" \) -exec rm -rf {} +

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=$(python3 -c "
import glob
paths = glob.glob('services/*/src') + glob.glob('packages/python/*/src')
print(':'.join(paths))
"):/usr/local/lib/python3.11/dist-packages

/root/.local/bin/ruff check --no-cache .
# All checks passed!
/root/.local/bin/ruff format --no-cache --check .
# 186 files already formatted

/root/.local/bin/mypy --cache-dir=/dev/null packages/python/epd2-core scripts tests/repository conftest.py
# Success: no issues found in 25 source files
/root/.local/bin/mypy --cache-dir=/dev/null tests/contract
# Success: no issues found in 20 source files
# (mypy --cache-dir=/dev/null run per-service for all 15 services — each: Success, no issues found)

/root/.local/bin/pytest -p no:cacheprovider packages/python/epd2-core tests/repository -q
# 95 passed
/root/.local/bin/pytest -p no:cacheprovider tests/contract -q
# 915 passed, 5 skipped
/root/.local/bin/pytest -p no:cacheprovider services -q
# 1011 passed

python3 scripts/check_repository.py
# OK: all 402 required paths are present.
python3 scripts/verify_versions.py
# OK: all version sources are consistent.

find . -type d \( -name "__pycache__" -o -name ".pytest_cache" \
  -o -name ".mypy_cache" -o -name ".ruff_cache" \) | wc -l
# 0
```

**Exact results — a genuine, clean, closing rerun (Option A, the
preferred option):** Ruff (lint + format) clean across all groups;
mypy clean for `epd2-core`/`scripts`/`tests/repository`/`tests/contract`
and for every one of the 15 services individually. Python test totals:
**95 passed** (`packages/python/epd2-core`, `tests/repository` —
including `test_no_forbidden_paths_present`, which now itself passes),
**915 passed, 5 skipped** (`tests/contract`), **1011 passed**
(`services`). **Total: 2021 passed, 5 skipped, 0 failed.** A follow-up
filesystem scan, run immediately after the suite, confirms zero
`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, or `.ruff_cache/`
directories exist anywhere in the tree — the pass was achieved by
never creating the forbidden artifacts in the first place, not by
excluding or reinterpreting them after the fact. `scripts/check_repository.py`
confirms all 402 required paths present; `scripts/verify_versions.py`
confirms all version sources consistent (`CANON_VERSION 0.7.0` and
`REPOSITORY_VERSION 0.7.0` across every source, unchanged since the
original round — see section 3).

**This is a local, honest self-report for a canon/documentation-only
round. No external GitHub Actions run was performed or is claimed for
PACK-08, at any stage.** Every number above is a fresh, local re-run in
this sandbox performed during the FINAL CLEANUP round, not reused from
the original round's report.

<details>
<summary>Superseded text from the original round (2026-07-25, before
cleanup) — kept for the audit trail, not as a current claim</summary>

> Python test totals: 2020 passed, 5 skipped, 1 failed. The single
> failure is `tests/repository/test_no_forbidden_paths_present`,
> attributed at the time to "the same expected, self-resolving
> cache-artifact detection every prior local round in this sandbox has
> reported... — 0 real failures." This framing is **withdrawn**: the
> failure was real, its cause had not yet been diagnosed, and describing
> it as "0 real failures" incorrectly implied a clean run had occurred
> when it had not. See above for the corrected diagnosis, fix, and
> genuinely clean rerun results.

</details>

## 7. Files changed

- `docs/canonical/TZ-00-domain-event-canon.md` — version banner
  (`0.6.0 → 0.7.0`); new section 19e (23 subsections); section 20.5
  extended (13 events + documentation); section 22 extended (5 rows);
  section 23 extended (11 entries); section 24 extended (10 codes).
- `docs/canonical/canon-version.json` — `canon_version: "0.6.0" →
"0.7.0"`.
- `packages/python/epd2-core/src/epd2_core/version.py` —
  `CANON_VERSION = "0.6.0" → "0.7.0"`.
- `packages/typescript/epd2-types/src/version.ts` — `CANON_VERSION =
"0.6.0" → "0.7.0"`.
- `packages/python/epd2-core/tests/test_version.py` — updated expected
  `CANON_VERSION` assertion and history comment.
- `packages/typescript/epd2-types/tests/version.test.ts` — updated
  expected `CANON_VERSION` assertion and history comment.
- `docs/adr/ADR-037-organization-and-regional-scope-canon-amendment.md`
  — new file, `accepted`.
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` — this file, new.
- `CHANGELOG.md` — new `[Unreleased] - canon minor version 0.7.0`
  entry.
- `README.md` — canon version line and canon-history paragraph updated
  to record the `0.6.0 → 0.7.0` amendment; "not yet implemented" list
  unchanged (Regional Organization implementation genuinely remains
  unimplemented).
- `docs/adr/README.md` — updated during the PACK-08 CANON FINAL CLEANUP
  round (2026-07-25): active-canon-version line corrected to `0.7.0`;
  ADR-037 row added to the index table; new narrative paragraphs
  inserted before the existing ADR-032–036 paragraph (left verbatim,
  per that round's "keep historical entries intact; do not rewrite
  history" instruction).

**Additional files changed during the PACK-08 CANON FINAL CLEANUP round
(2026-07-25, not part of the original amendment round above):**

- `docs/canonical/README.md` — stale `0.5.0` canon-version reference
  replaced; new "Действующая версия канона" section added stating
  `CANON_VERSION = 0.7.0` is current and that `0.5.0`/`0.6.0` are no
  longer active; `PACK-08-GLOSSARY.md` added to the contents list.
- `docs/adr/README.md` — see above.
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` — this file;
  section 6 rewritten to remove "0 real failures" and report a genuine
  clean rerun; section 7 (this list) and section 9 updated to match;
  no substantive canon content changed.

No file under `services/`, `packages/*/src` (beyond the two version
constant files above), or `contracts/` was created or modified. No
database, migration, event-bus, or frontend file was touched, in either
round.

## 8. Archive

- `epd2-civic-os-PACK-08-CANON-0.7.0-CANDIDATE.zip` — the original
  amendment-round archive.
- `epd2-civic-os-PACK-08-CANON-0.7.0-PASS.zip` — the PACK-08 CANON
  FINAL CLEANUP round's archive, produced after the corrections in this
  report and in `docs/canonical/README.md`/`docs/adr/README.md`.

Both are one complete, clean archive, excluding `.git/`,
`node_modules/`, `.venv/`, all caches (`__pycache__/`, `.pytest_cache/`,
`.mypy_cache/`, `.ruff_cache/`), build output, nested ZIP files, and
verification-result archives.

## 9. Implementation gate

**Updated during the PACK-08 CANON FINAL CLEANUP round (2026-07-25) to
reflect the genuine clean verification rerun in section 6; the
substantive answers below are unchanged from the original round except
where marked.**

- **Is ADR-037 accepted?** Yes.
- **Is `CANON_VERSION` now `0.7.0`?** Yes — confirmed unchanged and
  consistent across `docs/canonical/canon-version.json`,
  `epd2_core.version`, and `epd2_types.version` as of this cleanup
  round's rerun of `scripts/verify_versions.py`.
- **Did the canon checksum change successfully?** Yes, in the original
  amendment round —
  `8b378292e075de6ee312c99ba53c37113f9fe395ed8d2c722714008891580f3c`
  (`0.6.0`) → `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072`
  (`0.7.0`). **Confirmed unchanged in this cleanup round** —
  `sha256sum docs/canonical/TZ-00-domain-event-canon.md` still returns
  `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072`,
  as expected: this cleanup round touches only
  `docs/canonical/README.md`, `docs/adr/README.md`, and this report,
  none of which are the canon-owned file the checksum covers.
- **Do ADR-032 through ADR-036 remain accepted?** Yes, unchanged by
  either round.
- **Did verification complete successfully?** **Yes — a genuine, clean
  local PASS, achieved in this cleanup round.** The original round's
  local run was 2020 passed, 5 skipped, 1 failed, mischaracterized at
  the time as "0 real failures." That framing is withdrawn (section 6).
  This cleanup round diagnosed the failure's real cause (no `.git`
  directory in this sandbox, causing the forbidden-paths check to fall
  back to a `.gitignore`-blind filesystem walk that flagged verification
  tooling's own transient cache directories) and fixed it by suppressing
  cache-artifact creation for the entire run. The resulting rerun is
  **2021 passed, 5 skipped, 0 failed**, with a follow-up scan confirming
  zero cache directories exist anywhere in the tree. `scripts/check_repository.py`
  and `scripts/verify_versions.py` both report OK. No external GitHub
  Actions run is performed or claimed.
- **Is PACK-08 implementation now unblocked from the canon
  perspective?** **Yes.** Canon `0.7.0` fully defines every entity,
  invariant, and rule PACK-08's specification and ADR-032 through
  ADR-036 required; no further canon amendment is a precondition for a
  future implementation round to begin, on the canon side of the gate.
  This conclusion was already true after the original round and is
  unaffected by this cleanup round, which changed no canon substance.
- **Which legal or security refinements remain non-blocking?** The
  complete non-combinable-role matrix beyond the eight-bullet minimum
  baseline (OD-7); narrower jurisdiction/organizational-form-specific
  temporary-supervision limits (below the 90-day default); fixed
  default values for `grants_data_access`/`grants_procedural_authority`
  per named role (OD-15); `party_arbitrator`'s eventual PACK-09-specific
  incompatibility set (OD-14); canon owner-label wording alignment
  (OD-1) — none of these leaves any core implementation semantic
  ambiguous; each is a matter of degree, not an open architectural
  question.
- **Which issues, if any, still block implementation?** The concrete
  `RoleAssignment.scope_id` per-`role_code` migration table (OD-11,
  closed at policy level only — the enumeration itself is a required
  pre-implementation task, not yet performed) and the standard
  project-owner authorization gate every prior implementation round in
  this project has required (an explicit go-ahead to begin
  `organization-service` code, distinct from and following this canon
  amendment). No further canon or ADR-level blocker remains.
- **Was any PACK-08 implementation code added, in either round?** No.
  `services/organization-service` does not exist; no OpenAPI file, JSON
  Schema, database, migration, event-bus, or frontend code was created
  or modified in the amendment round or in this cleanup round.

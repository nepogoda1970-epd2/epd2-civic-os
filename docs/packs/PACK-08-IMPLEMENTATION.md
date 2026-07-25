# CLAUDE-PACK-08 — Organization & Regional Scope Foundation: Implementation

## 0. Status and baseline

This document records what the **PACK-08 IMPLEMENTATION ROUND** actually
built, as distinct from the specification/ADR rounds that preceded it:

- `docs/packs/PACK-08-SPECIFICATION.md` — the specification, corrected in
  place, that this round implements without further scope change.
- `docs/adr/ADR-032-*.md` through `docs/adr/ADR-037-*.md` — the six
  accepted ADRs this round implements (ADR-032–036 accepted in the
  spec-correction round; ADR-037 accepted in the canon-amendment round).
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` — records
  `CANON_VERSION` moving `0.6.0 -> 0.7.0` for ADR-037's new canon section
  19e text. **No further canon edit was made this round.** `CANON_VERSION`
  stays `0.7.0`; `REPOSITORY_VERSION` moves `0.7.0 -> 0.8.0`.
- Canon checksum (`sha256sum docs/canonical/TZ-00-domain-event-canon.md`):
  `a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072` —
  unchanged from the canon-amendment round, confirming no canon-owned file
  was touched this round.

For the full handover narrative (environment, verification results,
deliverables), see `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`. This
document is the technical reference: what was built, where, and how it
maps to canon 19e / ADR-032 through ADR-037.

## 1. New service: `organization-service`

A wholly new, independent, in-memory-backed service —
`services/organization-service/` — the sole authoritative owner of every
canon 19e entity. It imports only `epd2_core`/`epd2_audit_core`; no other
service imports it and it imports no other service (enforced structurally
in `tests/repository/test_service_boundaries.py`).

### 1.1 Domain model (`src/epd2_organization_service/domain.py`)

| Entity / value | Canon reference | Key fields (canon-exact names) |
| --- | --- | --- |
| `Organization` | 8.1 (extended) | `organization_id`, `name`, `legal_operator`, `organization_type`, `status`, `default_policy_version`, `organization_profile`, `effective_from`, `effective_until`, `dissolved_at`, `successor_reference`, `parent_reference` |
| `OrganizationalUnit` | 19e.4 | `organizational_unit_id`, `owning_organization_id`, `unit_type`, `status`, `valid_from`, `valid_until`, `recorded_at` |
| `CivicSpace` | 8.2 (confirmed unchanged) | `space_id`, `organization_id`, `name`, `space_type`, `visibility`, `participation_policy_id`, `status` |
| `OrganizationalRelation` | 19e.7 | `relation_id`, `relation_version`, `relation_type`, `source_organization_id`, `target_organization_id`, `status`, `valid_from`, `valid_until`, `recorded_at`, `supersedes_relation_id`, `authorizing_decision_reference` |
| `OrganizationalHierarchyOverlapPolicy` | 19e.8 | `policy_id`, `policy_version`, `applicable_relation_types`, `overlap_permitted`, `authorizing_decision_reference`, `status`, `valid_from`, `valid_until` |
| `OrganizationalInheritancePolicy` | 19e.9 | `policy_id`, `policy_version`, `role_code`, `inheritance_mode`, `authorizing_decision_reference`, `status`, `valid_from`, `valid_until` |
| `OrganizationalScope` (value shape) | 19e.11 | `scope_type`, `scope_reference`, `owning_domain`, `valid_from`, `valid_until`, `policy_version` |
| `OrganizationalAuthority` | 19e.15 | `authority_id`, `authority_version`, `role_code`, `scope`, `appointing_authority_reference`, `assigned_subject_reference`, `valid_from`, `status`, `policy_version`, `decision_reference`, `audit_reference`, `valid_until`, `revocation_reason_reference`, `grants_procedural_authority`, `grants_data_access` |
| `RegionalScopeAccessDecision` (value, not stored) | 19e.12 | `allowed`, `reason_code`, `evaluated_scope`, `policy_version`, `effective_time`, `mode`, `audit_reference` |
| `ScopeDelegationGrant` | 19e.12 mode 4 | `grant_id`, `delegate_scope`, `target_scope`, `action_code`, `authorizing_decision_reference`, `policy_version`, `valid_from`, `valid_until`, `status` |

Four-value `OrganizationStatus` (`draft`/`active`/`restricted`/`archived`)
and its allowed-transition set are canon 8.1/19e.10-exact. Nine-value
`RelationType`, its derived (never independently set) `RelationCategory`,
and four-value `RelationStatus` are canon 19e.7-exact. Six-value
`AccessMode` and the seven-role `InstitutionalRole` baseline (with the
eight-rule `PAIRWISE_INCOMPATIBLE_ROLES` matrix, `ROLE_INCOMPATIBILITY_BASELINE_VERSION
= "1.0"`) are canon 19e.12/19e.16-exact, including the two documented
reconciliation notes (`independent_auditor` for "election auditor",
`organizational_administrator` for "finance administrator" — the same
kind of implementation-level naming reconciliation ADR-037 itself
performed).

### 1.2 Business rules implemented

- **Effective dating and reorganization** — `Organization`/`CivicSpace`
  status transitions follow canon 8.1/19e.10's exact allowed-transition
  sets; `effective_from`/`effective_until`/`dissolved_at` are enforced
  tz-aware and internally consistent (`_require_tz_aware`,
  window-overlap helpers).
- **Multiple-typed-directed-graph relationships** — `RelationType` is
  open-extensible within three fixed categories (hierarchy/continuity/
  cooperation); `parent_of`/`subordinate_to` and, additionally,
  `temporary_supervision_by` are cycle-checked.
- **Hierarchy cycle detection** — `would_create_hierarchy_cycle` (fixed
  this round; see section 3) and `would_create_supervision_cycle` (already
  correct) both walk from the *candidate parent/supervisor* up through
  existing edges looking for the *candidate child/supervisee* — the
  correct direction for detecting that the new edge would close a loop.
- **Overlap policy resolution** — `resolve_for_relation_type` picks the
  highest-version active, in-window, applicable-type policy; unresolved
  falls back to a documented default.
- **Temporary supervision** — `assert_temporary_supervision_window_valid`
  enforces a mandatory `valid_until` and the `TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS
  = 90` default ceiling (ADR-034), overridable only via an explicit,
  audited decision reference.
- **Regional scope authorization (default-deny, six access modes)** —
  `check_regional_scope_access`-shaped logic in `application.py` returns a
  `RegionalScopeAccessDecision` that is `allowed=False` unless an
  `exact_scope`, `ancestor_scope`, `descendant_scope`,
  `delegated_cross_scope` (via `ScopeDelegationGrant.find_usable`),
  `temporary_supervision`, or `institutional_oversight_without_data_access`
  match is found — never inferred beyond an explicit grant/relation.
- **Institutional authority and role incompatibility** —
  `find_role_incompatibility` returns the conflicting existing `role_code`
  for any candidate that matches `PAIRWISE_INCOMPATIBLE_ROLES`, scoped by
  the caller to the same subject + same `OrganizationalScope` + all
  currently active (never combined; canon 19e.16).
- **Role/authority lifecycle** — `AuthorityStatus`
  (`proposed`/`active`/`revoked`/`expired`) with `PROPOSED` supporting
  19e.17 rule 6 (activation requires an explicit decision), plus
  revocation-reason-reference tracking.

### 1.3 Application layer, events, exceptions, storage

`application.py` exposes the command/read functions backing
`contracts/openapi/pack-08.yaml`'s nine operations plus internal-only
functions with no HTTP-shaped path (matching PACK-07's own
`verify_role_assignment_for_action` precedent). `events.py` builds all 13
canonical event payloads (section 4 below). `exceptions.py` declares one
exception per forbidden-transition/invalid-input case, each carrying the
matching reason code from `contracts/reason-codes/pack-08.yml`. `storage.py`
implements the repository pattern via seven in-memory store classes
(`InMemoryOrganizationStore`, `InMemoryOrganizationalRelationStore`,
`InMemoryOrganizationalHierarchyOverlapPolicyStore`,
`InMemoryOrganizationalInheritancePolicyStore`,
`InMemoryOrganizationalAuthorityStore`, `InMemoryScopeDelegationGrantStore`,
plus the shared `InMemoryAuditEventStore` from `epd2_audit_core`), each
tested independently in `tests/test_storage.py` (23 tests).

## 2. Mandatory `RoleAssignment.scope_id` migration table

Per the governing task's explicit prerequisite ("inspect ALL existing
`role_code` values BEFORE implementing migration behavior"), every real
`role_code` value in the repository was traced to its owning service and
classified. Full detail, methodology, and per-code reasoning:
`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`.

**Summary: 12 `role_code` values found (8 in `governance-service`, 4 in
`ai-processing-service`), all against the same `RoleAssignment.scope_id`
field. Zero are migration-blocked. Zero are category-6
(invalid/ambiguous).** One (`oversight_reviewer`) is context-dependent:
its scope class is category-4 or category-5 depending on which
`GovernanceDecision.decision_type` the specific grant is being exercised
for, so it is represented as two context-specific rows keyed explicitly
by `decision_type` (corrected in place during the "PACK-08 MIGRATION
TABLE CORRECTION" round — a `role_code` alone is insufficient to
determine scope, and no downstream service may infer scope from the
role_code name alone), fully pinned down by existing dispatch logic —
not ambiguous. One (`observer`) is category-5 by 100%-consistent usage
but flagged as not yet load-bearing (no application command currently
requires it). This closes OD-11 in `docs/packs/PACK-08-OPEN-DECISIONS.md`.

## 3. Bug found and fixed during implementation

`would_create_hierarchy_cycle` originally searched in the wrong direction
(started from the candidate *child* looking for the candidate *parent*
among the child's own ancestors — the inverse of the correct check).
Fixed to start from the candidate *parent* and walk up existing
`parent_of` edges looking for the candidate *child* — detecting that the
candidate child is already a transitive parent of the candidate parent,
which is exactly the condition under which adding `parent -> child` would
close a cycle. See the inline comment in `domain.py` for the full
reasoning, and `test_forbidden_hierarchical_cycle_detected` /
`test_forbidden_hierarchical_cycle_rejected_end_to_end` for the regression
tests that caught it. `would_create_supervision_cycle` needed no fix — it
was already implemented in the equivalent, correct direction.

## 4. Thirteen canon 20.5 events, minimum-necessary payload

Seven organization-status events share one payload shape
(`organization-status-payload.v1.schema.json`: `organization_id`,
`status`, `effective_time`, `recorded_at`, optional
`decision_reference`) — `organization.created`, `.activated`,
`.suspended`, `.dissolved`, `.merged`, `.split`, `.successor_declared`.
The remaining six each have a dedicated, minimal payload schema under
`contracts/events/`: relation created/ended, authority assigned/revoked,
regional-scope-access granted/revoked. None carries more than the
canon-required minimum (no PII, no derived-authority inference in the
payload itself).

## 5. Reason codes, schemas, OpenAPI (contract parity)

- **Reason codes** (`contracts/reason-codes/pack-08.yml`, 32 entries):
  10 canon-fixed (`source: canon-24`), 18 additive service-owned
  (`source: pack-08-service`), 4 reused from PACK-02
  (`source: pack-02-reused`). Verified to exactly match the 32 all-caps
  literals scanned from `services/organization-service/src` — zero
  missing, zero extra (`test_reason_codes_registry.py`).
- **Entity schemas** (`contracts/schemas/`, 5 new files):
  `organization`, `organizational-unit`, `civic-space`,
  `organizational-relation`, `organizational-authority`.
- **Event schemas** (`contracts/events/`, 6 new files, covering 13 event
  types as described in section 4).
- **OpenAPI** (`contracts/openapi/pack-08.yaml`, 9 operations, tag
  `organization-service`): `createOrganization`, `getOrganization`,
  `getCivicSpace`, `createOrganizationalRelation`,
  `endOrganizationalRelation`, `queryRelationshipGraph`,
  `assignOrganizationalAuthority`, `revokeOrganizationalAuthority`,
  `listScopedAuthorityAssignments`, `checkRegionalCapability`,
  `inspectEffectiveScope`. **Deliberately excluded, by design, per this
  round's own scope decision:** a bulk cross-regional directory endpoint,
  a public member directory endpoint, and any lifecycle-transition
  command as a public HTTP-shaped path (activation/suspension/dissolution
  remain internal-application-layer-only, mirroring PACK-07's internal-read
  precedent).

All 12 tests in `tests/contract/test_ct00_01_pack08_schema_validation.py`
validate every schema above against a real, directly-constructed domain
instance (not a hand-typed fixture dict).

## 6. Frontend vertical slice: `frontend/web-shell/app/organizations/*`

A minimal, read-only, accessible frontend slice — static sample data only
(`app/organizations/data.ts`), no fetch/HTTP call anywhere in the slice
(there is no running `organization-service` HTTP server in this
repository; see section 5's OpenAPI scope note).

- **Organization browser** (`page.tsx`) — table of sample organizations;
  explicitly no bulk cross-regional directory, no public member
  directory.
- **Organization detail** (`[id]/page.tsx`) — current/historical state
  selector (`AsOfSelector.tsx`, a client component resolving purely
  against static `status_history` sample data, `aria-live` region, no
  network call), typed relationship viewer (grouped by canon 19e.7
  relation type/category), institutional authority viewer (only
  explicitly-assigned roles are ever shown — no inferred authority).
- **Development authorization test console**
  (`dev-authorization-console/page.tsx`) — clearly, visibly labeled as
  development/testing-only (`role="alert"` banner); demonstrates the
  default-deny, six-access-mode shape of canon 19e.12 against a small,
  explicit set of sample grants (`authorization.ts`,
  `checkSampleRegionalScopeAccess`) — not a real authorization decision,
  no backend connection.
- **Language**: German-authoritative, English-informational throughout
  (`labels.ts`; every `<main>` marked `lang="de"`, every English gloss
  marked `lang="en"` and visually secondary).
- **Accessibility**: semantic `<table>`/`<caption>`/`<th scope="col">`,
  `<section aria-labelledby>` landmarks, `role="group"` control groups,
  `aria-live="polite"` result/status regions, visible `:focus-visible`
  outlines (`globals.css`).
- **No administration portal** — no create/edit/delete UI, no login, no
  form submission of any kind (verified by
  `tests/organizations.test.ts`'s own `<form`/`fetch(` absence checks,
  mirroring `tests/smoke.test.ts`'s established style).

Full detail and the exact local verification limitation (no
`node_modules`, no network — see `docs/handover/PACK-08-IMPLEMENTATION-REPORT.md`
section 6) is in `frontend/web-shell/README.md`.

## 7. Version and documentation bookkeeping

`REPOSITORY_VERSION` moved `0.7.0 -> 0.8.0` in
`packages/python/epd2-core/src/epd2_core/version.py`,
`packages/typescript/epd2-types/src/version.ts`, and `CHANGELOG.md`
(new `[0.8.0]` entry); `CANON_VERSION` unchanged at `0.7.0` everywhere.
`docs/canonical/canon-version.json`'s `repository_compatibility` widened
`<0.8.0 -> <0.9.0`. `docs/architecture/data-ownership.md` updated:
`Organization`/`CivicSpace` marked "Implemented (PACK-08)"; five new rows
added for `OrganizationalUnit`/`OrganizationalRelation`/
`OrganizationalHierarchyOverlapPolicy`/`OrganizationalInheritancePolicy`/
`OrganizationalAuthority` — with an honest note that pre-PACK-08 rows for
entities implemented in PACK-03 through PACK-07 remain unmarked (a
pre-existing gap this round did not retroactively fix; see that
document's own note and section 8 below).

## 8. Explicitly out of scope / honestly deferred

- Lifecycle-transition commands (activate/suspend/dissolve/merge/split)
  have no public OpenAPI path — internal application-layer functions only
  (section 5).
- No bulk cross-regional directory, no public member directory (explicit
  scope decision, tested for in `test_openapi_contract.py`).
- Cross-cutting aggregator test files from earlier packs
  (`test_state_transitions.py`, `test_audit.py`, etc.) were **not**
  extended with a PACK-08 section this round — this pack's own
  transition/audit behavior is covered by its own `tests/test_domain.py` /
  `tests/test_application.py` instead, matching the precedent that not
  every pack must extend every earlier cross-cutting file (e.g. PACK-06's
  own not-applicable markers in `test_ct00_10_rule_freeze.py`).
- The pre-existing gap in `scripts/check_repository.py`'s `REQUIRED_PATHS`
  (PACK-07's own handover/review/ADR docs were never added in PACK-07's
  own round) was documented, not backfilled — only this round's own new
  paths were added.
- `docs/architecture/system-context.md` and
  `docs/architecture/service-boundaries.md` were reviewed and left
  unchanged: `system-context.md`'s "Organization" bounded-context
  description was already accurate at the conceptual level this document
  operates at, and `service-boundaries.md`'s "Реализация в CLAUDE-PACK-02"
  section was never extended by PACK-03 through PACK-07 either — adding a
  PACK-08-only update there would have been inconsistent with how every
  prior implementation pack treated that file.

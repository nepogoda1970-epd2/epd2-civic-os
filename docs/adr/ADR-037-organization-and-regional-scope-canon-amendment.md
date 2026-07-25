# ADR-037: Organization and Regional Scope Canon Amendment

## Status

`accepted`

## Date

2026-07-25

## Context

`docs/packs/PACK-08-SPECIFICATION.md` (accepted) and ADR-032 through
ADR-036 (accepted, in the PACK-08 spec/ADR round and its subsequent
spec-correction round) fully specified the Organization & Regional
Scope domain — `Organization` extensions, `OrganizationalUnit`,
`CivicSpace` ownership confirmation, `OrganizationalRelation`,
`OrganizationalHierarchyOverlapPolicy`, `OrganizationalInheritancePolicy`,
`OrganizationalAuthority`, `OrganizationalScope`, regional scope
authorization, institutional authority lifecycle, effective dating,
reorganization, successor handling, scope isolation, and institutional
role incompatibility — but every one of those five ADRs explicitly
qualified its own acceptance with "this acceptance does not authorize
implementation" and "a canon amendment is required, not conditional,
before implementation." `docs/packs/PACK-08-OPEN-DECISIONS.md` item
OD-18 closed definitively on exactly this point: PACK-08 introduces
canon-relevant concepts that do not exist in canon `0.6.0` today, so
implementation must not start before a separate canon amendment round.
This ADR is that round's own governing ADR — the "PACK-08 CANON
AMENDMENT ROUND" governing request confirms the baseline (PACK-01
through PACK-07 PASS, `REPOSITORY_VERSION = 0.7.0`, `CANON_VERSION =
0.6.0`, PACK-08 specification and ADR-032 through ADR-036 accepted,
PACK-08 implementation blocked pending canon amendment) and instructs
exactly this: prepare and apply the canon amendment PACK-08 requires,
as a canon/documentation round only — no service code, database,
migration, frontend, or production integration.

## Decision

**Amend canon to `0.7.0`, adding new section 19e ("Организация и
региональная авторизация — расширение / Organization & Regional Scope
Context"), inserted between sections 19d and 20 without renumbering any
existing section** — the same non-renumbering technique already used
for sections 19a, 19b, 19c, and 19d. This ADR's acceptance directly
authorizes, and this same round performs, the canon edit itself (unlike
ADR-032 through ADR-036, whose acceptance deliberately deferred canon
implementation to this later, dedicated task — the same pattern
ADR-010/013/018/020/023/025/028 each already established: acceptance
first, canon-text edit as a following, explicitly authorized step,
sometimes in the same round as here and sometimes in a distinct later
one).

The canon edit performed:

- Extends `Organization` (8.1) with six additive fields:
  `organization_profile`, `parent_reference`, `effective_from`,
  `effective_until`, `dissolved_at`, `successor_reference` (19e.3). All
  six existing fields, statuses, and the owner (Organization Service)
  are unchanged.
- Confirms `CivicSpace` (8.2) unchanged in every field, status, and
  owner (19e.6).
- Defines four wholly new canonical entities, all owned by
  `organization-service` (ADR-032): `OrganizationalUnit` (19e.5),
  `OrganizationalRelation` (19e.7), `OrganizationalHierarchyOverlapPolicy`
  (19e.8), `OrganizationalInheritancePolicy` (19e.13).
- Defines `OrganizationalAuthority` (19e.15), also owned by
  `organization-service`, distinct from and never merged with the
  existing `RoleAssignment` (8.4, Governance Context, unchanged in
  every field, status, and owner).
- Defines `OrganizationalScope` (19e.11) as a reusable value shape, not
  a separately owned entity — the same status already given to
  `RedactionManifest` (19c.4) and `AIDisclosurePackage` (19c.6).
- Canonizes the accepted multiple-typed-directed-graph relationship
  model, relation-type-specific cycle/overlap rules, effective dating,
  reorganization rules (including the hard no-automatic-authority-
  transfer rule), default-deny regional scope authorization (six access
  modes), inheritance-policy ownership, the 90-day temporary-supervision
  default, the institutional-role minimum non-combinable-role baseline,
  role/authority lifecycle rules, extended identity-minimization rules,
  and the `RoleAssignment.scope_id` six-category classification
  requirement (19e.2, 19e.4, 19e.7–19e.19).
- Extends section 20.5 (Organization events) with thirteen new events
  and their minimum/prohibited payload, effective/recorded time, policy-
  version reference, audit linkage, idempotency, and privacy-constraint
  documentation (19e.20).
- Extends section 22 (ownership matrix) with five new rows.
- Extends section 23 (forbidden links) with new entries.
- Extends section 24 (reason codes) with ten new codes.
- Moves `canon_version` `0.6.0 → 0.7.0` (canon section 25: a
  backward-compatible, additive, minor change — no existing required
  field, event meaning, entity owner, architectural invariant, anonymity
  rule, or critical-object lifecycle is altered).

## Canon impact

Minor-version, additive canon change (canon section 25). No existing
canonical field, event name/meaning, entity owner, status enum value,
or architectural invariant (INV-01 through INV-10) is altered, renamed,
or removed. `Organization` (8.1) and `RoleAssignment` (8.4) each gain
new, additive fields/constraints only; `CivicSpace` (8.2) and
`Membership` (8.3) are confirmed unchanged. See canon section 19e for
the complete text; see the Decision section above for the itemized
summary.

## Affected domains

- **Organization & Regional Scope** (new, canon 5.4 now fully defined;
  physical service `organization-service`, not created by this round).
- **Governance Context** (19b) — `RoleAssignment` (8.4) unaffected in
  field/status/owner; only its `scope_id`'s per-`role_code`
  classification is now canonically constrained (19e.19), a
  classification rule, not a field change.
- **Participation & Membership Context** (19d) — `Membership` (8.3)
  unaffected in field/status/owner; `Membership.organization_id`'s
  eventual real-referent behavior (already anticipated by 19d and the
  PACK-08 migration matrix) is unaffected in canon text by this round.
- Transparency Context (19a), AI Processing Context (17, 19c), and
  Emergency/Crisis Override (19) are untouched.

## Affected schemas

None. No JSON Schema, OpenAPI file, or database schema is created,
modified, or authorized by this ADR or this round — canon defines the
domain model only (19e.23); schemas remain a future implementation-round
deliverable, consistent with every prior canon-only round's own
precedent (ADR-010, ADR-013, ADR-018/020, ADR-023/025, ADR-026 through
ADR-031).

## Affected events

Thirteen new canonical events added to section 20.5: `organization.activated`,
`organization.suspended`, `organization.dissolved`, `organization.merged`,
`organization.split`, `organization.successor_declared`,
`organizational_relation.created`, `organizational_relation.ended`,
`organizational_authority.assigned`, `organizational_authority.revoked`,
`regional_scope_access.granted`, `regional_scope_access.revoked` — twelve
event names, matching exactly the twelve named by the governing request's
item 13 plus the pre-existing `organization.created` (already canon since
0.1.0, unchanged). No existing event name or meaning is altered. No event
transport, payload schema, or queue is implemented by this round (19e.23).

## Affected reason codes

Ten new canon-level reason codes added to section 24:
`ORGANIZATION_NOT_ACTIVE`, `ORGANIZATION_SCOPE_MISMATCH`,
`CROSS_SCOPE_ACCESS_DENIED`, `AUTHORITY_ASSIGNMENT_INVALID`,
`AUTHORITY_ROLE_INCOMPATIBLE`, `AUTHORITY_SCOPE_INVALID`,
`SUCCESSOR_TRANSFER_REQUIRES_DECISION`, `ORGANIZATIONAL_RELATION_OVERLAP`,
`ORGANIZATIONAL_CYCLE_FORBIDDEN`, `HISTORICAL_SCOPE_NOT_EFFECTIVE`. No
existing reason code is renamed or repurposed; a repository-wide check
performed as part of this round (`docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md`
section 3) found no naming conflict between these ten and any code
already registered in canon section 24 or in any `contracts/reason-codes/pack-0N.yml`
file. A future implementation round's own `contracts/reason-codes/pack-08.yml`
remains a separate, later deliverable, per the same precedent every
prior canon-only round already established (canon section 24 fixes the
stable, canon-owned subset; the executable per-pack registry is an
implementation-round artifact).

## Identity and privacy impact

Extends, without weakening, the existing identity-separation invariant
(INV-01) and `DomainPseudonymReference`/`AntiCorrelationInvariant`
(19d.17): no global user identifier is introduced; institutional
authority references (`OrganizationalAuthority.appointing_authority_reference`,
`.assigned_subject_reference`) use the same opaque, domain-scoped
reference convention already established project-wide; no public or
cross-regional membership/participant directory is introduced by
default (19e.18); events carry no unnecessary identity data (19e.20);
scope authorization returns only a boolean and, where useful, a reason
code — never a membership list, role-holder list, or `Organization`
graph (mirrors `check_regional_scope_access`'s minimum-necessary-claims
design, 19e.12).

## Security impact

Canonizes default-deny regional scope authorization (19e.12) and closes,
at the canon level, three named failure modes the governing baseline
identified: cross-Land data leakage (no mode grants cross-scope access
without an explicit policy or delegation record), confused-deputy access
(every mode re-validates the actor's scope against the target's scope at
evaluation time), and role-name-as-proof-of-authority (a `role_code`
string is never itself sufficient; an active, scope-matched
`RoleAssignment`/`OrganizationalAuthority` record is always required).
The minimum non-combinable-role baseline (19e.16) and the self-
assignment/dual-control prohibitions (19e.17, rules 4–6) directly
implement HI-12-equivalent separation-of-duties protection. The
`RoleAssignment.scope_id` migration-blocked rule for ambiguous
`role_code` values (19e.19) prevents a future implementation from
silently wiring an unclassified role into scope-authorization logic.

## Migration impact

None at the canon level — no existing field is renamed, removed, or
reinterpreted; `Organization`/`RoleAssignment`/`CivicSpace`/`Membership`
all gain, at most, additive fields or classification constraints, never
in-place changes to existing data semantics. The concrete
`RoleAssignment.scope_id` per-`role_code` migration table (19e.19)
remains a required **pre-implementation** task
(`docs/packs/PACK-08-MIGRATION-MATRIX.md` section 2.3,
`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-11), not performed by
this canon amendment itself. No database, migration script, or existing
service's stored data is touched by this round.

## Compatibility impact

Backward compatible in every respect canon section 25's "minor" category
requires: every existing required field, event meaning, entity owner,
and status enum value is unchanged; every new field on `Organization`
is additive and nullable/optional where applicable
(`organization_profile`, `parent_reference`, `effective_until`,
`dissolved_at`, `successor_reference` are all nullable or defaultable;
`effective_from` is the sole new mandatory field, consistent with every
prior canon round's own precedent of adding at least one mandatory
field where the new concept structurally requires it — e.g.
`AIProcessingRecord.redaction_manifest`, ADR-023 D4a). `repository_compatibility`
in `docs/canonical/canon-version.json` already admits `REPOSITORY_VERSION
0.7.0` (`>=0.1.0 <0.8.0`), unchanged by this round.

## Testing requirements

A future implementation pack must add: a test proving `Organization`'s
six existing fields and status enum validate unchanged after the six
new additive fields are introduced; a `parent_reference` projection-
correctness test proving it always matches the current active
hierarchy-category `OrganizationalRelation` set, per 19e.4 (already
required by ADR-033's own testing-requirements section); a
relation-type-specific cycle-rejection test for `parent_of`/
`subordinate_to` and a cycle-permission test for cooperation-category
relation types explicitly declared non-hierarchical (19e.7); an overlap-
policy enforcement test proving a hierarchy-category overlap is rejected
absent an `OrganizationalHierarchyOverlapPolicy` record (19e.7, 19e.8);
a `check_regional_scope_access` default-deny test proving all six modes
individually and proving no seventh implicit mode exists (19e.12); a
restrict-never-broaden test for `OrganizationalInheritancePolicy`
(19e.13); a `valid_until`-required rejection test and a 90-day-default
test for `temporary_supervision_by` (19e.14); a non-combinable-role
test for each of the eight minimum-baseline bullets (19e.16); a
lifecycle test per each of the eight rules in 19e.17; a test proving a
`RoleAssignment.scope_id` classified as category 6 (invalid/legacy
ambiguous) is rejected by any code path that attempts to wire it into
`check_regional_scope_access` (19e.19); and a static/AST-based test
(mirroring `tests/repository/test_pack07_duplicated_logic_parity.py`'s
established style) confirming no source file in this canon-only round
introduces service code, a database migration, or an event-transport
implementation. This canon-only round itself adds no new test file —
these are pre-implementation requirements for the future, separate
implementation round (19e.23).

## Implementation blockers

**None remaining from the canon perspective as of this ADR's
acceptance.** Canon `0.7.0` now fully defines the Organization &
Regional Scope domain model; `docs/packs/PACK-08-SPECIFICATION.md` and
ADR-032 through ADR-036 remain accepted and are now consistent with
canon text. What remains open and **does** block a real implementation
round, but is not a canon blocker:

- The concrete `RoleAssignment.scope_id` per-`role_code` migration table
  (19e.19; OD-11, closed at policy level only) must be populated and
  reviewed before any data migration touching that field.
- The complete, legally-refined non-combinable-role matrix beyond the
  eight-bullet minimum baseline (19e.16; OD-7, partially closed) remains
  a legal-review matter.
- `docs/handover/PACK-08-CANON-AMENDMENT-REPORT.md` section 8 records
  the full implementation-gate answer this ADR's acceptance requires.

## Rejected alternatives

- **Defer the canon edit to a later, separate task (ADR-032 through
  ADR-036's own original pattern).** Rejected for this specific round:
  the governing "PACK-08 CANON AMENDMENT ROUND" request explicitly asks
  to "prepare **and apply**" the canon amendment now, unlike the
  original PACK-08 spec/ADR round, which explicitly deferred the edit.
  Splitting further would only re-create the same two-step pattern this
  round exists to complete.
- **Treat the six new `Organization` fields, or any of the four new
  entities, as non-canonical, pack-level contract entities** (mirroring
  how `AssuranceRequirement`/`AttributeFreshnessRequirement`, ADR-028,
  remain reusable value shapes without full canon-entity status).
  Rejected: `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18 already
  closed this question definitively — these concepts are canon-relevant
  precisely because regional scope authorization, institutional
  authority, and reorganization are cross-cutting, multi-domain
  invariants (default-deny, no-universal-administrator,
  no-automatic-rights-transfer) of the same kind canon already fixes for
  every other domain (INV-08, INV-09, INV-10), not domain-internal
  implementation detail.
- **A major, not minor, canon version bump.** Rejected: no existing
  required field, event meaning, entity owner, architectural invariant,
  anonymity rule, or critical-object lifecycle is changed — every
  change is purely additive, satisfying canon section 25's own "minor"
  criteria exactly, the same standard every prior canon addition
  (0.2.0 through 0.6.0) was held to.
- **Rename `RoleAssignment.scope_id` or split it into multiple fields
  now**, to make the six-category classification structurally explicit
  in the schema itself. Rejected as premature: `docs/packs/PACK-08-OPEN-DECISIONS.md`
  item OD-13 already tracks this as a possible future canon edit, only
  once the concrete per-`role_code` enumeration (OD-11) is complete —
  renaming the field now, before that enumeration exists, would risk
  exactly the kind of unreviewed reinterpretation ADR-035 exists to
  prevent.

## Unresolved legal refinements

The following remain **explicitly non-blocking** for canon or for a
future implementation round's core semantics, per the governing
request's own item 9 allowance ("unresolved legal details may remain
explicitly marked as legal refinement, but must not leave core
implementation semantics ambiguous") — every item below is a matter of
degree (narrower, stricter, more specific), never a question the canon
text above leaves ambiguous:

- The complete non-combinable-role matrix beyond the eight-bullet
  minimum baseline (19e.16; OD-7).
- Narrower legal limits on temporary-supervision maximum duration for
  specific organizational forms or jurisdictions, below the 90-day
  canon default (19e.14).
- Fixed, canon-recommended default values for `grants_data_access`/
  `grants_procedural_authority` per named institutional role, versus
  entirely open per-deployment configuration (`docs/packs/PACK-08-OPEN-DECISIONS.md`
  item OD-15).
- Whether `party_arbitrator` needs its own distinct incompatibility set
  once PACK-09's arbitration workflow is specified (OD-14).
- Canon owner-label alignment between canon 8.1's prose ("Organization
  Service") and the repository's own `organization-service` naming
  convention (OD-1) — a documentation/naming question, not a semantic
  one.

## Reversibility

Reversible with cost once real `organization-service` data exists under
this canon text — narrowing or restructuring any of the four new
entities, `Organization`'s six new fields, or the six-category
`RoleAssignment.scope_id` classification, becomes a major-version-
equivalent change under canon section 25, exactly as every prior
canon addition (17.1's `AIProcessingRecord` extension, 19b's
`GovernanceDecision`, etc.) already established. Today, before any
implementation exists, reverting this ADR's canon edit remains a
documentation-only, non-major change.

## Related canon version

Authored against, and directly amends, canon version `0.6.0 → 0.7.0`.
This ADR's acceptance **is** the authorization for, and this same round
performs, the canon-text edit — unlike ADR-032 through ADR-036, whose
acceptance explicitly deferred the edit to this dedicated task. See
`docs/canonical/TZ-00-domain-event-canon.md` section 19e for the
complete canonical text this ADR authorizes and records:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  a16341a66ce39514e6d8cd6d7a6dde8fc37b0430e3e9ddd7bfd284b116cb9072
CANON_VERSION = 0.7.0
```

Previous checksum and version, for reference:

```text
sha256(docs/canonical/TZ-00-domain-event-canon.md) =
  8b378292e075de6ee312c99ba53c37113f9fe395ed8d2c722714008891580f3c
CANON_VERSION = 0.6.0
```

This is a canon-only change: no `services/organization-service`
directory, JSON Schema, OpenAPI file, or reason-code registry was
created, and no PACK-01 through PACK-07 source code was touched.
`organization-service` implementation remains a separate, later task,
gated on this canon content and on ADR-032 through ADR-036, but not
authorized by any of them alone.

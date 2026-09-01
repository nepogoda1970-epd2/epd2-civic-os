# ADR-036: Institutional authority assignments and non-combinable roles

## Status

`accepted`

## Date

2026-07-25

## Owner decision

Accepted 2026-07-25, in the PACK-08 spec-correction round.

**Institutional role incompatibility baseline (closes OD-7 only to the
extent necessary for implementation readiness):** the following
minimum non-combinable-role matrix is adopted, superseding and
extending this ADR's original four-pair starting set:

1. An `election officer` cannot simultaneously act as `election
auditor` for the same process/scope.
2. An `election board member` cannot independently approve their own
   appointment or removal.
3. A `finance auditor` cannot simultaneously be `finance administrator`
   for the same organization/scope.
4. An `independent auditor` cannot audit actions they themselves
   performed or approved.
5. A `party arbitrator` cannot participate in a case where they hold an
   operational role in the affected organization.
6. An `organizational administrator` cannot self-assign institutional
   authority.
7. `DPO` procedural independence must be preserved (a DPO's own
   procedural role cannot be overridden or directed by the organization
   or role it oversees).
8. No person may satisfy both sides of a dual-control action (the
   proposer and the activator/approver of the same controlled action
   must always be different people).

**This matrix is a minimum baseline, subject to legal refinement** —
it does not foreclose a stricter or more detailed matrix once legal
review of specific organizational forms and role definitions is
complete (`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-7, updated).
It supersedes this ADR's original four-pair set as the binding starting
point: `election officer`/`election auditor`, `election board member`
self-approval, `finance_auditor`/`finance administrator`,
`independent_auditor` self-audit, and `party_arbitrator` operational-
role participation are now covered explicitly above (bullets 1, 2, 3,
4, 5); the two remaining original pairs
(`finance_auditor` × `organizational_administrator` and
`independent_auditor` × `organizational_administrator`) remain in force
as specific instances of the general dual-control and self-assignment
principles (bullets 6 and 8) and are restated, not dropped, in the
"Non-combinable roles" section below.

**This closes OD-7 "only to the extent necessary for implementation
readiness"**: the eight-bullet minimum baseline is settled and binding
as the floor every future implementation must enforce. It is a partial,
not a full, closure — the complete, legally-refined matrix (exact role
pairs beyond this baseline, organizational-form-specific narrowing)
remains open, tracked in OD-7.

**This acceptance does not authorize implementation.** `OrganizationalAuthority`
depends on canon concepts (`Organization`, institutional authority
lifecycle) that are canon-relevant per the Owner decision recorded in
ADR-032's own "Owner decision" section and in
`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18: PACK-08 implementation
must not start before a separate canon amendment round is prepared and
accepted. `CANON_VERSION` and the canon checksum are unchanged by this
correction round.

## Context

`PACK-08-PROPOSAL.md` section 3.3 requires "role assignability/authority
references for: DPO; election board/officer; independent auditor;
finance auditor" without implementing their later institutional
workflows, and section 5's ADR-036 summary requires deciding
"appointment authority, effective period, organizational scope,
non-combinable roles, revocation and whether an institutional role
grants process authority, data access, or both," plus the rule that
"a role cannot be active outside the effective lifetime of its
organization" and that "dissolution, suspension, merge, split or
successor designation never transfers authority implicitly."
`HARD-INVARIANTS-0.8.md` HI-11 (no universal administrator), HI-12
(separation of duties), and HI-13 (scoped institutional authority) are
the governing constraints. Canon 8.4 already defines `RoleAssignment`
(owned by `governance-service`, per ADR-016) for system/governance
roles; this ADR must decide whether the seven named institutional roles
(DPO, election board member, election officer, independent auditor,
finance auditor, party arbitrator, organizational administrator) extend
that existing entity or become a new one.

## Problem

`RoleAssignment` (canon 8.4) already carries `role_code`, `scope_id`,
`valid_from`/`valid_until`, `assigned_by`, `approval_reference` — a
shape that, at first glance, looks sufficient for the seven
institutional roles too. But `RoleAssignment` is owned by
`governance-service` (canon's own table, ADR-016) and was designed for
system/governance-policy roles (e.g. a `GovernanceDecision` reviewer),
not for organizationally-scoped institutional appointments that also
need to record whether the role grants data access, procedural
authority, or both, and that participate in the reorganization
lifecycle (ADR-033 section 7) in ways `RoleAssignment` was never
designed to. Reusing `RoleAssignment` outright risks quietly expanding
`governance-service`'s ownership to include organizational-institutional
concerns it was not designed for (an INV-02 boundary concern,
mirroring ADR-032's own reasoning); introducing a wholly separate,
unrelated entity risks needless duplication if the two are, in
substance, the same shape with different owners.

## Considered options

- **Option A — extend `RoleAssignment` (canon 8.4) in place** with
  `grants_data_access`/`grants_procedural_authority`/`incompatibilities`
  fields, keeping ownership in `governance-service`.
- **Option B — a new, distinct entity, `OrganizationalAuthority`,**
  owned by `organization-service` (ADR-032), structurally similar to
  `RoleAssignment` but independently defined, with `governance-service`'s
  own `RoleAssignment.assigned_by`/`approval_reference` able to
  reference an `OrganizationalAuthority` record as an opaque input
  where relevant, never the reverse.
- **Option C — a fully generic "authority" abstraction** shared by both
  services, refactoring `RoleAssignment` itself into a shared base
  entity both `governance-service` and `organization-service` extend.

## Decision

**Option B.** `OrganizationalAuthority` (fields: specification section
9.1) is a new entity, owned exclusively by `organization-service`
(ADR-032), distinct from canon 8.4 `RoleAssignment`. The two remain
separately owned and separately evolvable: `RoleAssignment` continues
to mean "a system/governance-policy role, owned by `governance-service`";
`OrganizationalAuthority` means "an institutional, organizationally-
scoped appointment, owned by `organization-service`." Where a future
workflow needs both (e.g. a `GovernanceDecision` approval that must
verify the approver also holds a specific `OrganizationalAuthority`),
the two are cross-referenced by opaque reference, exactly like every
other existing narrow-read pattern in this project (ADR-027) — never
merged into one entity or one service.

## Rejected options

**Rejected: Option A (extend `RoleAssignment` in place).** Would repeat,
at the entity level, the exact ownership-blurring ADR-032 already
rejected at the service level (folding `Organization` into
`governance-service`): `governance-service` would end up owning both
"system/policy roles" and "organizationally-scoped institutional
appointments" — two conceptually distinct authority domains — merely
because they share a superficially similar field shape. It would also
force every future organizational-authority change (e.g. adding a new
institutional role type, section 9.2) through `governance-service`'s
own release/review process, coupling two domains that the governing
request treats as distinct (`RoleAssignment` is never named among the
entities PACK-08 is asked to define).

**Rejected: Option C (generic shared base entity).** A retroactive
refactor of `RoleAssignment` (an already-`accepted`, already-implemented,
already-tested canon 8.4 entity, in production use since PACK-05) is
out of scope for a specification/ADR round that is explicitly barred
from implementing any code, and would be a disproportionate, high-risk
change merely to save the small amount of field duplication between
two structurally-similar-but-substantively-different entities. The
narrow-reference pattern (Option B) achieves the practical benefit
(no double-entry of the same appointment) without touching existing,
working canon/service code.

## Consequences

A future implementation pack adds `OrganizationalAuthority` to
`organization-service` alongside `Organization`/`CivicSpace`/
`OrganizationalRelation` (ADR-032); `governance-service` gains, at
most, a narrow read edge into `organization-service` to verify an
`OrganizationalAuthority` reference where a governance workflow needs
to (symmetrical to the reverse edge ADR-032's Unresolved Question
OD-3 already flags). The seven named institutional roles (DPO, election
board member, election officer, independent auditor, finance auditor,
party arbitrator, organizational administrator) are `role_code` values
on `OrganizationalAuthority`, not on `RoleAssignment` — restated from
specification section 9.1.

### Role lifecycle invariants (binding on `OrganizationalAuthority`)

Restated in full from `docs/packs/PACK-08-SPECIFICATION.md` section 10,
fixed by this ADR as binding:

1. Cannot begin before the organization exists (`valid_from` on or
   after the scope's own `Organization.effective_from`).
2. Cannot remain valid after dissolution without explicit migration —
   dissolution suspends every scoped authority assignment by default
   (fail-closed); only a separately authorized migration decision may
   redirect one toward a successor scope.
3. Does not automatically move after merge or split.
4. Does not automatically transfer to a successor.
5. Cannot be self-assigned (`appointing_authority_reference` must
   differ from the assignment's own subject).
6. Cannot be activated by the same person who proposed it where dual
   control is required — restated as mandatory for all seven named
   institutional roles at minimum.

### Non-combinable roles

**Binding minimum baseline (per the "Owner decision" section above,
supersedes and extends this ADR's original four-pair starting set;
non-exhaustive — the full matrix is a legal-review matter, tracked as
OD-7, "Unresolved questions" below):**

1. `election_officer` × `election_auditor` — incompatible, for the same
   process/scope.
2. `election_board_member` — cannot independently approve their own
   appointment or removal.
3. `finance_auditor` × `finance_administrator` — incompatible, for the
   same organization/scope.
4. `independent_auditor` — cannot audit actions they themselves
   performed or approved.
5. `party_arbitrator` — cannot participate in a case where they hold an
   operational role in the affected organization.
6. `organizational_administrator` — cannot self-assign institutional
   authority (restates lifecycle rule 5 as a role-specific instance).
7. `DPO` — procedural independence must be preserved; a DPO's own
   procedural role cannot be overridden or directed by the organization
   or role it oversees.
8. No person may satisfy both sides of a dual-control action (restates
   lifecycle rule 6 as a general cross-role rule, not limited to the
   seven named institutional roles).

**Retained from the original starting set, as specific instances of
bullets 3 and 6 above:**

- `finance_auditor` × `organizational_administrator` — incompatible, in
  the same scope.
- `finance_auditor` × any future finance-preparation/approval role —
  incompatible, in the same scope (rule reserved now; roles do not yet
  exist).
- `independent_auditor` × `organizational_administrator` — incompatible,
  in the same scope.
- `election_board_member`/`election_officer` × declared candidacy in
  the election they administer — incompatible (exact detection
  mechanism deferred to `ConflictAssessment`, canon 19d.11).

This eight-bullet set is a **minimum baseline, subject to legal
refinement** — it is the floor, not the ceiling, of what a future
implementation must enforce.

### Data access vs. procedural authority

`grants_data_access` and `grants_procedural_authority` are independent
booleans (specification section 9.1) — restated as binding: **no role**
in the seven-role starting set is assumed to carry both by default. A
future implementation pack's own configuration explicitly sets both
flags per role/scope combination; this ADR does not fix their values
for any specific role (that is itself a legal/security-review matter,
tracked below), only the rule that the two are independent and neither
is inferred from the other or from the role's title.

## Privacy impact

`OrganizationalAuthority` records reference actors only through the
project's existing opaque, domain-scoped reference convention
(mirroring ADR-031's anti-correlation principle) — never a raw name.
Institutional titles (e.g. "independent auditor") never imply data
access by themselves (mode 6 of ADR-034); an auditor's actual read
access to specific records requires its own separate grant, keeping the
audit-log/appointment-record layer separated from the data-access layer
even for oversight roles.

## Security impact

This ADR directly implements HI-12 (separation of duties) and HI-13
(scoped institutional authority): the non-combinable-role set prevents
a single actor from holding both operational and oversight authority
over the same scope (e.g. `finance_auditor` and
`organizational_administrator` together, which would let one person
both create and audit the same records). The self-assignment and
dual-control prohibitions (lifecycle rules 5–6) close the most direct
"appoint yourself, then act unilaterally" attack a scoped-authority
system would otherwise be vulnerable to.

## Migration impact

None — `OrganizationalAuthority` is a wholly new entity; no existing
`RoleAssignment` record or consumer is affected by this ADR. Any future
implementation that surfaces an existing `RoleAssignment`-based
institutional-role convention (should one exist informally in a future
pack before this ADR's own implementation) would require its own
explicit, reviewed migration — not addressed by this ADR, since no such
convention currently exists in the repository.

## Testing requirements

A future implementation pack must add: a lifecycle test per rule 1–6
above (organization-does-not-exist-yet rejection, dissolution-suspends-
authority, merge/split-does-not-transfer, successor-does-not-transfer,
self-assignment rejection, dual-control violation rejection); a
non-combinable-role test for each of the eight minimum-baseline bullets
in the Owner decision above, plus each pair in the retained original
starting set; a test proving `grants_data_access`/`grants_procedural_authority`
are independently settable and that neither is inferred from the other
or from `role_code` alone; an audit-creation test proving every
assignment and revocation produces an `AuditEvent` via
`epd2_audit_core`, mirroring existing PACK-05/07 coverage patterns
(`tests/contract/test_ct00_07_audit_creation.py`'s established style);
and a specific test proving an `election_board_member` cannot approve
or reject their own appointment/removal record (bullet 2), and a
specific test proving a `DPO`'s procedural determinations cannot be
overridden through any code path owned by the organization or role the
DPO oversees (bullet 7).

## Unresolved questions

- **OD-7 is closed at the minimum-baseline level by the Owner decision,
  above** (the eight-bullet matrix is settled and binding). The
  complete, legally-refined non-combinable-role matrix beyond this
  baseline remains a legal-review matter (`PACK-08-PROPOSAL.md`
  section 6); tracked as `docs/packs/PACK-08-OPEN-DECISIONS.md` item
  OD-7 (updated, partial closure only).
- Whether `party_arbitrator` needs its own distinct incompatibility set
  once PACK-09's arbitration workflow is specified (this ADR only seeds
  the role's assignment shape, not its workflow) — tracked as OD-14.
- Whether `grants_data_access`/`grants_procedural_authority` should have
  fixed, canon-recommended default values per named role (e.g.
  `independent_auditor` typically `grants_data_access = true` for read-
  only export access), or remain entirely open, per-deployment
  configuration with no recommended defaults at all — tracked as OD-15.
- Whether `OrganizationalAuthority` needs its own `Appeal`-style review
  path for a contested revocation, mirroring `membership-service`'s
  reused polymorphic `Appeal` model (ADR-030), or whether that is
  entirely a PACK-09 arbitration-workflow concern — tracked as OD-16.

## Reversibility

Reversible with cost before code exists. Once real `OrganizationalAuthority`
appointment data exists (especially given the non-combinable-role and
dual-control dependencies), narrowing or restructuring this entity
becomes a major-version-equivalent change under canon section 25, were
canon ever amended to include it.

## Related canon version

Authored against canon version `0.6.0`. `CANON_VERSION` and the canon
checksum are unchanged by this ADR and by the PACK-08 spec-correction
round that accepted it.

**A canon amendment is now REQUIRED — not conditional — before any
implementation of `OrganizationalAuthority`.** `OrganizationalAuthority`
is a new, proposed entity, not a canon 8.4 `RoleAssignment` amendment,
and this ADR itself edits no canon text. However, `OrganizationalAuthority`
and institutional authority lifecycle are named explicitly among the
canon-relevant concepts PACK-08 introduces, per the Owner decision
recorded in `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18 and
restated identically in ADR-032/033/034/035's own "Related canon
version" sections: implementation must not begin before a separate,
dedicated canon amendment round proposes the actual canon addition (its
owner label, its relationship to canon 8.4 `RoleAssignment`, and its
place in the canon's own entity index) and that canon ADR is prepared
and accepted, with `CANON_VERSION` bumped accordingly. This is a firm
precondition, not a possibility left open for a future ADR to decide
whether to require.

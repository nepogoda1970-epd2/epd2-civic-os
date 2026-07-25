# CLAUDE-PACK-08 — Open decisions

Consolidates every unresolved question raised by
`docs/packs/PACK-08-SPECIFICATION.md` and ADR-032 through ADR-036, in
one place, for owner/legal/security review before any PACK-08
implementation round is authorized. Mirrors the role
`docs/review/PACK-07-OWNER-DECISIONS.md` played for PACK-07.

**Status of this document:** nothing below is decided. Each item names
the question, why it is open, and which document(s) depend on its
resolution. Resolving an item does not, by itself, authorize
implementation — per the governing baseline
(`ARCHITECTURE-GAP-REGISTER.md` section 7), only an explicit
owner/legal/security-reviewed authorization does that.

## OD-1 — Canon owner-label alignment for `Organization`

Canon 8.1 already names the owner of `Organization` as "Organization
Service" in its own table. Does a future canon-alignment edit rename
this to `organization-service` (matching this project's
`epd2_<domain>_service` naming convention), or does the canon prose
label stay as-is with the real service simply matching it? Depends on:
ADR-032. Affects: any future conditional canon ADR.

## OD-2 — `OrganizationalUnit` as specialization vs. distinct entity

Should `OrganizationalUnit` be its own canonical entity distinct from
`Organization`, or a `organization_profile`-driven specialization of
`Organization` itself? The specification currently proposes the
latter. Pending: legal review of which organizational forms (working
groups, temporary bodies) genuinely need distinct legal/statutory
treatment versus a shared entity with a different profile value.
Depends on: `docs/packs/PACK-08-SPECIFICATION.md` section 3.1,
ADR-032.

## OD-3 — Reverse read edge, `organization-service` → `governance-service`

Does `organization-service` need its own narrow read into
`governance-service` (e.g. to verify an `authorizing_decision_reference`
used in reorganization workflows actually resolves to an approved
`GovernanceDecision`), mirroring the existing
`eligibility-service → governance-service` edge (ADR-027)? Or is that
verification the caller's own responsibility? Depends on: ADR-032,
ADR-033 section 7.

## OD-4 — Extensibility of `relation_type` within a category

Should new `relation_type` values beyond the nine named by the
governing request be addable within an existing relation category by
repository configuration alone (the specification's current proposal),
or does every new `relation_type` value require its own ADR regardless
of category? Depends on: ADR-033.

## OD-5 — CLOSED (correction round, 2026-07-25): organizational graph model

**Owner decision adopted:** Organization relationships use multiple
typed directed graphs; a simple tree is not authoritative. Multiple
simultaneous parent-like relationships are allowed only when relation
types differ, or where an explicit, versioned
`OrganizationalHierarchyOverlapPolicy` (new proposed entity, owned by
`organization-service`) permits overlap for the relation types
involved — replacing the original "reviewed exception... recorded"
framing with a concrete, named policy entity rather than an ad hoc
decision reference. Cycles are forbidden, without exception, for
containment and subordination (`parent_of`/`subordinate_to`) relations;
cycles may be allowed only for relation types explicitly declared
non-hierarchical (the cooperation category, section 5.1). Conflict and
overlap validation is relation-type-specific, never a single blanket
rule across all relation types. See
`docs/packs/PACK-08-SPECIFICATION.md` sections 3.1/5.1/6 and ADR-033's
own "Owner decision" section for full detail. Closed — no further
architectural decision needed on this point; the exact field shape of
`OrganizationalHierarchyOverlapPolicy` remains a pre-implementation
detail, not an open architecture question.

## OD-6 — Cardinality of `operates_within` / `participates_in`

Can a node `operate_within` more than one other node concurrently?
Currently left unconstrained pending legal review of real
cross-regional working-body practice. Depends on: ADR-033.

## OD-7 — PARTIALLY CLOSED (correction round, 2026-07-25): non-combinable-role matrix

**Owner decision adopted, closing this item "only to the extent
necessary for implementation readiness":** a minimum, eight-bullet
non-combinable-role baseline is now settled and binding (specification
section 9.3, ADR-036's own "Owner decision" section): (1) election
officer ≠ election auditor, same process/scope; (2) election board
member cannot approve their own appointment/removal; (3) finance
auditor ≠ finance administrator, same organization/scope; (4)
independent auditor cannot audit their own actions/approvals; (5) party
arbitrator cannot participate in a case where they hold an operational
role in the affected organization; (6) organizational administrator
cannot self-assign institutional authority; (7) DPO procedural
independence must be preserved; (8) no person may satisfy both sides of
a dual-control action. This baseline is explicitly marked **minimum,
subject to legal refinement** — it is the floor a future implementation
must enforce, not the ceiling.

**Still open:** the complete, legally-refined matrix beyond this
baseline — every additional pairwise incompatibility among the seven
named institutional roles (and any future ones), in every scope
combination — remains a legal-review matter
(`PACK-08-PROPOSAL.md` section 6). Depends on: ADR-036. **Priority:
required before any full implementation of institutional-authority
enforcement; the eight-bullet baseline itself is required before any
partial implementation.**

## OD-8 — CLOSED (correction round, 2026-07-25): inheritance-policy ownership

**Owner decision adopted:** the ancestor/descendant inheritance policy
(ADR-034 modes 2–3) is a canonical, versioned, auditable entity —
`OrganizationalInheritancePolicy` — owned exclusively by the
Organization & Regional Scope domain (`organization-service`), not mere
repository/deployment configuration outside canon's scope. Consuming
domains may apply stricter rules on top of it but may never broaden the
authority it grants; inheritance rules are versioned and auditable;
frontend and downstream services can never infer inheritance
independently of an actual policy evaluation. See
`docs/packs/PACK-08-SPECIFICATION.md` section 8.1 and ADR-034's own
"Owner decision" section for full detail. Closed.

## OD-9 — Denial reason-code granularity

Should `check_regional_scope_access`'s denial explanation use a single
`CROSS_SCOPE_ACCESS_DENIED` code regardless of which mode was
attempted, or a more granular code per attempted mode (e.g. distinct
codes for a failed ancestor-inheritance attempt versus a failed
delegation lookup)? Depends on: ADR-034, specification section 14.

## OD-10 — CLOSED (correction round, 2026-07-25): temporary-supervision maximum duration

**Owner decision adopted:** `temporary_supervision_by` must always
carry both `valid_from` and `valid_until` — open-ended temporary
supervision is forbidden. The default maximum duration is 90 days from
`valid_from` (mirroring the
`StepUpAuthenticationRequirement.maximum_authentication_age` ceiling
pattern, ADR-028 item 7). Extending a temporary-supervision window
beyond its current `valid_until` requires a new, separately governed
decision and its own audit record — never a silent extension of the
existing record. A future, dedicated legal review may define narrower
(never wider) maximum durations for specific organizational forms. See
`docs/packs/PACK-08-SPECIFICATION.md` section 8.1 mode 5 and ADR-034's
own "Owner decision" section for full detail. Closed.

## OD-11 — CLOSED (implementation round, 2026-07-25): `RoleAssignment.scope_id` classification and enumeration

**Owner decision adopted:** every existing and future `role_code` on
`RoleAssignment.scope_id` must be classified into exactly one of six
categories — organization scope, jurisdiction scope, CivicSpace scope,
process-local scope, global/system scope, or invalid/legacy ambiguous
— superseding ADR-035's original two-way (organization-reference /
process-local) simplification for this field. No silent
reinterpretation is allowed for any `role_code`, in any category.
Ambiguous (category-6) roles are migration-blocked: no implementation
may wire them into `check_regional_scope_access` or any
organization-scope-aware logic until reclassified. Implementation must
include a complete `role_code`-keyed migration table, populated and
reviewed, before any data migration touching this field begins.
Global/system-scoped roles never imply universal administrative access
(HI-11 still applies). See ADR-035's own "Owner decision" section for
full detail.

**Fully closed as of the PACK-08 implementation round.** The concrete,
per-`role_code` enumeration this decision required before any migration
touching `RoleAssignment.scope_id` could begin is now complete:
`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md` classifies all 12
`role_code` values found in the repository (8 defined by
`governance-service`'s `PILOT_ROLE_CODES`, 4 defined by
`ai-processing-service`'s `REVIEWER_ROLE_CODES` and granted against the
same field) against the six categories above. None is classified into
category 6 (invalid/legacy ambiguous) and none is migration-blocked;
`oversight_reviewer` is represented as two context-specific rows
(keyed explicitly by `GovernanceDecision.decision_type`, corrected in
place during the "PACK-08 MIGRATION TABLE CORRECTION" round —
`role_code` alone is insufficient to determine scope, so this role_code
is never asserted as a single row with two scope classes) and `observer`
carries a documented "classified but not yet load-bearing" note — both
are fully pinned down, not open questions. This implementation round's
own new field, `OrganizationalAuthority.role_code` (canon 19e.15,
`organization-service`), is a structurally separate namespace and does
not touch `RoleAssignment.scope_id` at all — no migration of that field
was performed or was in scope this round. Depends on: ADR-035,
`docs/packs/PACK-08-MIGRATION-MATRIX.md` section 2.3,
`docs/packs/PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`.

## OD-12 — `Membership.region_code` deprecation window

Does the additive-companion-field compatibility strategy for
`Membership.region_code` (migration matrix section 2.2) have a fixed
end date/version after which `region_code` is formally deprecated, or
does it remain indefinitely dual-written pending a separate future
ADR? Depends on: ADR-035, migration matrix section 2.2.

## OD-13 — Possible future rename of `RoleAssignment.scope_id`

Once the per-`role_code` split (OD-11) is fully resolved, should a
future canon edit rename `RoleAssignment.scope_id` to something more
specific (e.g. splitting into two differently-named fields by
category), or does the single field name persist with category-specific
documentation only? Depends on: ADR-035.

## OD-14 — `party_arbitrator` incompatibility set

`party_arbitrator`'s own workflow is PACK-09 scope
(`MASTER-ROADMAP-0.8.md`); this pack seeds only the role's assignment
shape. Does `party_arbitrator` need its own distinct non-combinable-role
set once PACK-09's arbitration workflow is specified? Depends on:
ADR-036; deferred to PACK-09.

## OD-15 — Default values for `grants_data_access` / `grants_procedural_authority`

Should the seven named institutional roles have fixed, canon-recommended
default values for `grants_data_access`/`grants_procedural_authority`
(e.g. `independent_auditor` typically read-only data access), or remain
entirely open, per-deployment configuration with no recommended
defaults at all? Depends on: ADR-036.

## OD-16 — Appeal path for contested `OrganizationalAuthority` revocation

Does `OrganizationalAuthority` need its own `Appeal`-style review path
for a contested revocation, mirroring `membership-service`'s reused
polymorphic `Appeal` model (ADR-030), or is that entirely a PACK-09
arbitration-workflow concern? Depends on: ADR-036; overlaps with OD-14.

## OD-17 — Documentation supersession for stale architecture documents

`PACK-08-PROPOSAL.md` section 10 and `ARCHITECTURE-GAP-REGISTER.md`
GAP-052 through GAP-055 name four documents whose stale content should
gain an explicit `superseded-by` reference once PACK-08 is implemented:
`docs/review/KNOWN_LIMITATIONS.md`, `docs/architecture/data-ownership.md`,
`docs/architecture/system-context.md`, and
`docs/review/PACK-07-OWNER-DECISIONS.md`'s canon-only snapshot
statement. **This specification round does not edit any of the four** —
per the governing request's scope (specification and ADRs only, no
implementation), and because the master baseline itself frames this as
a PACK-08 *implementation* action, not a specification-round action.
Confirm this sequencing (defer to implementation) is correct, or
whether the specification round should perform these edits now, before
implementation is authorized.

## OD-18 — CLOSED DEFINITIVELY (correction round, 2026-07-25): canon amendment is mandatory, not conditional

**Owner decision adopted:** PACK-08 introduces canon-relevant concepts
— `Organization`, `CivicSpace`, `OrganizationalRelation`,
`OrganizationalAuthority`, `OrganizationalScope`, regional scope
authorization, institutional authority lifecycle, and reorganization/
successor invariants — that do not exist in canon 0.6.0 today (beyond
`Organization`/`CivicSpace`'s own unfilled-owner stubs). Therefore:

- **PACK-08 implementation must not start before a separate canon
  amendment round.**
- `CANON_VERSION` and the canon checksum remain unchanged in this
  correction round.
- A future canon ADR must be prepared and accepted before
  implementation.

This closes OD-18 definitively: the question is no longer "whether" a
conditional canon ADR is needed — it is now settled that canon
amendment is a **mandatory precondition** for implementation, not a
possibility contingent on how implementation later turns out. What
remains open is only the future canon ADR's own exact content and
timing, which is out of scope for this specification/ADR-correction
round. See `docs/packs/PACK-08-SPECIFICATION.md` section 18 and every
one of ADR-032 through ADR-036's own "Related canon version" sections
for the identical restatement of this gate.

## Summary table

**Updated in the correction round (2026-07-25)** — status column added.

| ID | Topic | Depends on | Priority | Status |
|---|---|---|---|---|
| OD-1 | Canon owner-label alignment | ADR-032 | Low | Open |
| OD-2 | `OrganizationalUnit` specialization | ADR-032 | Medium | Open |
| OD-3 | Reverse read edge to governance-service | ADR-032 | Medium | Open |
| OD-4 | `relation_type` extensibility | ADR-033 | Low | Open |
| OD-5 | Organizational graph model / multiple-parent overlap | ADR-033 | Medium | **Closed** |
| OD-6 | `operates_within`/`participates_in` cardinality | ADR-033 | Low | Open |
| OD-7 | Complete non-combinable-role matrix | ADR-036 | **High** | **Partially closed** (minimum baseline adopted) |
| OD-8 | Inheritance-policy ownership | ADR-034 | Medium | **Closed** |
| OD-9 | Denial reason-code granularity | ADR-034 | Low | Open |
| OD-10 | Temporary-supervision max duration | ADR-034 | Medium | **Closed** |
| OD-11 | `RoleAssignment.scope_id` decision table | ADR-035 | **High** | **Closed** (enumeration complete, see `PACK-08-ROLE-SCOPE-MIGRATION-TABLE.md`) |
| OD-12 | `region_code` deprecation window | ADR-035 | Medium | Open |
| OD-13 | Possible `scope_id` rename | ADR-035 | Low | Open |
| OD-14 | `party_arbitrator` incompatibility set | ADR-036 | Deferred (PACK-09) | Open |
| OD-15 | Data-access/procedural-authority defaults | ADR-036 | Medium | Open |
| OD-16 | Authority-revocation appeal path | ADR-036 | Deferred (PACK-09) | Open |
| OD-17 | Stale-document supersession sequencing | Master baseline | Medium | Open |
| OD-18 | Whether canon amendment is mandatory | All five ADRs | **High** | **Closed definitively** (mandatory, not conditional) |

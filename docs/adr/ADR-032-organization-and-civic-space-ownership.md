# ADR-032: Organization and CivicSpace ownership

## Status

`accepted`

## Date

2026-07-25

## Owner decision

Accepted 2026-07-25, in the PACK-08 spec-correction round following
`PACK-08 SPEC CORRECTION + OWNER DECISIONS`. The ownership decision
below (Option C, a new `organization-service`) is confirmed as
architecturally settled — no blocking architectural question remains
against this ADR's own scope. **This acceptance does not authorize
implementation.** Per the owner's explicit canon-amendment decision
(recorded in full in `docs/packs/PACK-08-SPECIFICATION.md` section 18
and `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18, both updated by
this correction round): PACK-08 introduces canon-relevant concepts
(`Organization` ownership completion, `CivicSpace`, and, via the
sibling ADRs, `OrganizationalRelation`, `OrganizationalAuthority`,
`OrganizationalScope`, regional scope authorization, institutional
authority lifecycle, and reorganization/successor invariants) that
require a separate, dedicated canon amendment round before any
implementation begins. `CANON_VERSION` and the canon checksum remain
unchanged by this correction round; a future canon ADR must be
drafted and accepted before `services/organization-service/` or any
other PACK-08 code may be written.

## Context

Canon `0.6.0` already defines `Organization` (8.1) and `CivicSpace`
(8.2) as canonical entities, with `Organization`'s owner named as
"Organization Service" in canon's own table — but no such service has
ever existed. Canon section 5.4 ("Organization Context") describes the
responsibility area (организация, подразделения, Civic Spaces, рабочие
группы, роли, членство, организационная структура) without a service
behind it. `docs/handover/PACK-07-SPEC-FINAL.md` section 11 explicitly
defers all real hierarchy work: "Neither service may assume a live
`Organization` or `CivicSpace` entity exists until PACK-08 defines
one." `membership-service` (PACK-07) already writes an opaque
`Membership.organization_id` (canon 8.3) with no service on the other
end to validate it against. `governance-service`'s `RoleAssignment.scope_id`
(canon 8.4) is similarly opaque. `MASTER-ARCHITECTURE-0.8.md` section 14
and `PACK-08-PROPOSAL.md` section 3.1 both name this as the first gap
PACK-08 must close: "Create one authoritative organization domain ...
Unique ownership; no other service writes organization state."

`docs/packs/PACK-08-SPECIFICATION.md` section 3 proposes five new or
extended entities in this domain: `Organization` (extended),
`OrganizationalUnit` (new), `CivicSpace` (unchanged), `OrganizationalRelation`
(new), `OrganizationalStatus` (new, derived read model), plus two
entities this ADR explicitly places elsewhere (`OrganizationalAuthority`,
still owned in this domain but decided in detail by ADR-036;
`OrganizationalScope`, a reusable value shape decided by ADR-034). This
ADR fixes who owns all of them, and the boundary of what other services
may read.

## Problem

Without a single named owner, `Organization`/`CivicSpace` risk repeating
the exact anti-pattern canon's own INV-02 ("один владелец каждой
сущности") exists to prevent: multiple services each maintaining their
own partial, inconsistent copy of organizational state (one plausible
failure mode already visible today — `Membership.organization_id`,
`RoleAssignment.scope_id`, and `ProcessEligibilityPolicy`'s `scope_type`/
`scope_id` are three different services' three different opaque
references to what should be the same underlying concept, with no
single service actually owning the referent). A decision is also needed
on whether the new domain folds into an existing service
(`governance-service`, which already owns `RoleAssignment`, or
`membership-service`, which already writes `organization_id`) or becomes
its own new service, before any of ADR-033 through ADR-036 can assume a
concrete ownership boundary.

## Considered options

- **Option A — fold `Organization`/`CivicSpace` into `governance-service`.**
  `governance-service` already owns `RoleAssignment` (canon 8.4, the
  entity most directly needing an `Organization` referent) and
  `GovernancePolicy`/`GovernanceDecision`, which already authorize
  critical-policy activation project-wide.
- **Option B — fold `Organization`/`CivicSpace` into `membership-service`.**
  `membership-service` already writes `Membership.organization_id`
  (canon 8.3) and is the service most directly downstream of
  organizational structure today.
- **Option C — a new, independent `organization-service`,** owning
  `Organization`, `OrganizationalUnit`, `CivicSpace`,
  `OrganizationalRelation`, `OrganizationalStatus`, and
  `OrganizationalAuthority`, with every other service (including
  `governance-service` and `membership-service`) reading it only
  through narrow, boolean/opaque-reference reads mirroring ADR-027's
  established pattern.
- **Option D — split `Organization` and `CivicSpace` across two
  different services** (e.g. `organization-service` for the hierarchy,
  a separate `civic-space-service` for participation areas).

## Decision

**Option C.** A new service, `organization-service`, is the exclusive
owner of `Organization`, `OrganizationalUnit`, `CivicSpace`,
`OrganizationalRelation`, `OrganizationalStatus`, and
`OrganizationalAuthority` (the last also governed in detail by
ADR-036). `OrganizationalScope` (ADR-034) is a reusable value shape
this service's own reads return; it is not an independently owned
entity, and no other service constructs one from raw fields itself.

**No other service may write `Organization`, `OrganizationalUnit`,
`CivicSpace`, `OrganizationalRelation`, or `OrganizationalAuthority`
state.** `eligibility-service`, `membership-service`,
`governance-service`, `credential-service`, `identity-service`,
`transparency-service`, `voting-service`, `delegation-service`, and
`ai-processing-service` may each hold a **narrow read edge** into
`organization-service`, returning only:

- scope existence/active status (`OrganizationalStatus`, section 3.1 of
  the specification);
- ancestor/descendant relationship between two scopes (section 5/8 of
  the specification);
- exact-scope match;
- a permitted-inheritance/delegation result (ADR-034).

No broad `Organization` graph, member list, or role-holder list is ever
returned across this boundary — mirroring ADR-027's own narrow-read
philosophy, generalized to a sixth (regional) dimension alongside the
five ADR-027 already covers (identity, eligibility, credential,
governance, membership).

**Rejected: Option A.** Folding organizational structure into
`governance-service` would blur canon 5.12 (Governance Context: system
roles, policy authority, rule versions) against canon 5.4 (Organization
Context: organization, subdivisions, Civic Spaces) — two responsibility
areas canon itself already separates. It would also make
`governance-service` a second, larger single point of failure for both
"who is authorized to do X" (its existing job) and "what does the
organizational world look like" (a materially different, much larger
job), working against INV-02's one-owner discipline by concentrating
two genuinely separate ownership domains in one service merely because
they are both consumed by authorization logic.

**Rejected: Option B.** `membership-service` is already the newest,
most recently stabilized service (PACK-07); adding the organization
domain to it would repeat Option A's blurring in the opposite
direction — party membership is a _consumer_ of organizational
structure (a member's `Membership.organization_id` names which
organization they belong to), not the natural owner of that structure
itself. Every other domain that will eventually need organizational
scope (governance, eligibility, transparency, voting, future finance
and documents) would then depend on `membership-service` for a concept
that has nothing to do with membership per se — the exact "narrow read
into an unrelated domain" smell ADR-026/027 were themselves written to
avoid for `eligibility-service`/`membership-service`'s own split.

**Rejected: Option D.** Canon 8.2 already models `CivicSpace` as
nesting directly under `organization_id` — the two are one coherent
aggregate, not two independently evolving domains. Splitting them would
force every consumer needing "is this Civic Space active, and under
which organization" to make two service calls where one suffices today,
with no compensating boundary benefit (unlike, say, Identity vs.
Eligibility vs. Credential, which genuinely encode different trust
levels, canon 5.1–5.3).

## Rejected options

See "Considered options" / "Decision" above for the full analysis of
Options A, B, and D.

## Consequences

A new service directory, `services/organization-service/`, would be
created by a future implementation pack (not by this ADR), mirroring
the existing fifteen services' own `README.md`/`pyproject.toml`/`src/`/
`tests/` shape. `docs/architecture/service-boundaries.md` and
`docs/architecture/data-ownership.md` would gain a new row/section for
this service — the master baseline's own documentation-supersession
rule (`PACK-08-PROPOSAL.md` section 10, `ARCHITECTURE-GAP-REGISTER.md`
GAP-052 through GAP-055) applies to this update, which this ADR notes
as required of a future implementation round, not performed here.
Every future PACK depending on organizational scope (PACK-09 through
PACK-12 and beyond, per `MASTER-ROADMAP-0.8.md`) depends on this
ownership decision being settled first, consistent with the
roadmap's own sequencing principle 1.

## Privacy impact

Centralizing ownership in one service, rather than letting every
consumer hold its own partial copy, reduces the number of places
personally-linked organizational facts (which member belongs to which
Civic Space, who holds which authority) could otherwise leak through
inconsistent partial replication. The narrow-read boundary (this ADR)
combined with `docs/packs/PACK-08-SPECIFICATION.md` section 12 ensures
no cross-service read ever returns a member or role-holder list, only
booleans/opaque references.

## Security impact

A single write owner closes the "which of N services' copies is
authoritative" ambiguity that would otherwise be exploitable as a
confused-deputy vector (a stale or maliciously diverged copy in one
service being trusted over the real `organization-service` state).
Restricting every other service to read-only narrow edges means a
compromised downstream service (e.g. `voting-service`) cannot itself
mutate organizational structure, satisfying HI-11 (no universal
administrator) and INV-03 (no direct access to another service's
database) by construction rather than by convention alone.

## Migration impact

None performed by this ADR. `Membership.organization_id` (canon 8.3)
and `RoleAssignment.scope_id` (canon 8.4) remain exactly as they are
today — opaque, undereferenced fields — until a future implementation
pack both creates `organization-service` and wires the narrow reads
this ADR authorizes. No existing schema, event, or API changes as a
result of this ADR alone. The full field-by-field migration decision is
ADR-035's own scope, not this ADR's.

## Testing requirements

A future implementation pack must add, mirroring
`tests/repository/test_service_boundaries.py`'s existing AST-based
approach: a static test confirming no service other than
`organization-service` imports or writes `Organization`/
`OrganizationalUnit`/`CivicSpace`/`OrganizationalRelation`/
`OrganizationalAuthority` domain state; a static test confirming every
narrow read edge this ADR authorizes is `.application`-only (mirroring
ADR-027's own edge-matrix test); an ownership-uniqueness test (one
service per entity, mirroring existing `test_service_boundaries.py`
coverage for the other fourteen services); and a **projection-correctness
test for `Organization.parent_reference`** — per the owner decision
recorded in ADR-033 (section "Owner decision — `parent_reference` is a
non-authoritative projection"), `parent_reference` is never
independently mutated and must always equal whatever the current
hierarchy-category `OrganizationalRelation` set for that node resolves
to; this test asserts the two never diverge, and that no code path
writes `parent_reference` directly.

## Unresolved questions

Non-blocking legal/naming refinements only — none leaves this ADR's own
core semantics (ownership, write exclusivity, narrow-read boundary)
ambiguous:

- Does canon 8.1's existing "Organization Service" owner label get
  renamed to `organization-service` (matching this project's
  `epd2_<domain>_service` naming convention) as part of the required
  future canon amendment (see Owner decision, above)? Tracked as
  `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-1.
- Should `OrganizationalUnit` be its own canonical entity distinct from
  `Organization`, or a `organization_profile`-driven specialization of
  `Organization` itself (`docs/packs/PACK-08-SPECIFICATION.md` section
  3.1 currently proposes the latter, but this remains open pending
  legal review of which organizational forms genuinely need distinct
  legal/statutory treatment)? Tracked as OD-2.
- Whether `organization-service` needs its own narrow read into
  `governance-service` (e.g. to verify an `authorizing_decision_reference`
  used in section 7 of the specification actually resolves to an
  approved `GovernanceDecision`), mirroring the existing
  `eligibility-service → governance-service` edge (ADR-027) — or
  whether that verification is instead the caller's own responsibility.
  Tracked as OD-3.

## Reversibility

Reversible with cost before code exists (this stage — no
`organization-service` directory, no schema, no test exists yet).
Once real `Organization`/`CivicSpace` data and cross-service read edges
exist, re-splitting ownership becomes a major-version-equivalent change
under canon section 25, once canon itself is amended to reflect it (see
Related canon version, below).

## Related canon version

Authored against canon version `0.6.0`. **This ADR performs no canon
edit; `CANON_VERSION` and the canon checksum are unchanged.** Per the
owner decision recorded above, a canon amendment is a **required**
prerequisite — not merely conditional — before any PACK-08
implementation begins: canon 8.1/8.2 already name `Organization`/
`CivicSpace` with an owner this ADR fills in for the first time, and
this ADR's sibling ADRs (033/034/036) introduce further canon-relevant
concepts. A dedicated, separate canon ADR must be drafted and accepted,
covering at minimum the owner-label question (OD-1) and the new
entities named by ADR-033/034/036, before `services/organization-service/`
or any other implementation artifact is created.

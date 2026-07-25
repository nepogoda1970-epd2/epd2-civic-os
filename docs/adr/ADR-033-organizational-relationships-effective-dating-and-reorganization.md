# ADR-033: Organizational relationships, effective dating, and reorganization

## Status

`accepted`

## Date

2026-07-25

## Owner decision

Accepted 2026-07-25, in the PACK-08 spec-correction round, with two
architectural decisions now closed and binding:

**Organizational graph model (closes OD-5):** organization relationships
use multiple typed directed graphs (restated, unchanged from the
original Decision, below). A simple tree is not authoritative. Multiple
simultaneous parent-like (hierarchy-category) relationships are allowed
**only** when (a) the relation types differ (e.g. one `parent_of` edge
and one `subordinate_to` edge naming different target nodes are not
"the same kind of overlap" and are each evaluated independently), or (b)
an explicit, versioned **`OrganizationalHierarchyOverlapPolicy`**
(new, proposed entity, owned by `organization-service`, alongside
`OrganizationalRelation`) permits the specific overlap for the
node's/edge's own relation type and organizational profile — never a
one-off `authorizing_decision_reference` alone, and never an implicit
allowance. Cycles remain **forbidden, without exception, for containment
and subordination relations** (`parent_of`, `subordinate_to` — the
hierarchy category). Cycles **may** be allowed only for relation types
**explicitly declared non-hierarchical** — restated from the original
Decision: every cooperation-category relation type is individually
declared cycle-permitting or not (`affiliated_with`, `operates_within`,
`participates_in` permit cycles; `temporary_supervision_by` does not,
by its own declared semantics, even though it shares the cooperation
category) — no relation type's cycle behavior is inferred from its
category membership alone. Conflict and overlap validation (canon —
`docs/packs/PACK-08-SPECIFICATION.md` section 6) is **relation-type-specific**,
never a single blanket rule applied across every `relation_type`.

**`parent_reference` is a non-authoritative projection (see the new
section below), never a second source of truth.**

**This acceptance does not authorize implementation.** As with ADR-032,
a separate, dedicated canon amendment round — covering
`OrganizationalRelation`, the new `OrganizationalHierarchyOverlapPolicy`,
and the reorganization/successor invariants this ADR fixes — is required
before any implementation begins (`docs/packs/PACK-08-OPEN-DECISIONS.md`
item OD-18, closed in favor of "mandatory"). `CANON_VERSION` and the
canon checksum are unchanged by this correction round.

## Context

ADR-032 gives `organization-service` exclusive ownership of
`Organization`/`OrganizationalUnit`/`CivicSpace`, but says nothing about
how nodes relate to each other, over time, through change. The
governing request is explicit that "the hierarchy is [not] always a
simple tree," and requires typed relationships (`parent_of`,
`subordinate_to`, `affiliated_with`, `successor_of`, `merged_into`,
`split_from`, `temporary_supervision_by`, `operates_within`,
`participates_in`), a decision between tree/DAG/multiple typed graphs,
full effective-dating support, and a complete reorganization workflow
set with a hard no-implicit-rights-transfer rule.
`PACK-08-PROPOSAL.md` section 3.1 states relationship topology "is
decided by ADR-033 and must not assume a simple tree before review."
`MASTER-ROADMAP-0.8.md`'s PACK-08 required-tests list separately calls
for hierarchy-cycle property tests, effective-date/reorganization
tests, and "overlapping, typed, and non-territorial relationship
tests" — implying the model must support genuinely non-tree shapes,
not merely tolerate them as an edge case.

## Problem

A single, undifferentiated graph of "organization relates to
organization" would either (a) force every relation type into
tree-shaped assumptions that special/cross-regional/non-territorial
units already violate, or (b) permit meaningless combinations (e.g. a
`successor_of` edge participating in a cycle-detection algorithm
designed for `parent_of`, or a `parent_of` edge being treated as
mutable history the way `merged_into` legitimately is). Three
genuinely different kinds of fact are being asked to share one
relationship concept: current structural position (hierarchy),
historical continuity (succession/merger/split), and ongoing
cooperation that is neither (affiliation, supervision, participation).
Conflating them risks exactly the kind of "one boolean for several
distinct questions" error ADR-028 item 1 already had to correct
elsewhere in this project (the four separated electoral-eligibility
claims replacing one `electoral_eligibility_met`).

## Considered options

- **Option A — a strict single tree.** Every `Organization` node has at
  most one `parent_of` edge into it; hierarchy is enforced as literally
  tree-shaped at the schema level.
- **Option B — one undifferentiated directed graph,** with all nine
  relation types stored as untyped edges and no per-type invariant
  distinction.
- **Option C — multiple typed relationship graphs, modeled as one
  canonical `OrganizationalRelation` entity with a `relation_type` field
  and a derived `relation_category` (hierarchy | continuity |
  cooperation), each category carrying its own invariants** (cycle
  rules, mutability rules, cardinality rules).
- **Option D — three fully separate canonical entities** (e.g.
  `HierarchyEdge`, `ContinuityRecord`, `CooperationRelation`), each with
  its own schema, instead of one entity with a discriminator.

## Decision

**Option C.** `OrganizationalRelation` is one canonical entity
(`docs/packs/PACK-08-SPECIFICATION.md` section 5.2 for the full field
list), whose `relation_type` value determines its `relation_category`:

- **Hierarchy** (`parent_of`, `subordinate_to`) — expected tree-shaped
  for most territorial nodes, but **not enforced as a strict tree**: a
  node may have zero parent-category edges (a Bund-level, special, or
  cross-regional node), and may have more than one **only** where the
  relation types differ or an explicit, versioned
  `OrganizationalHierarchyOverlapPolicy` permits the specific overlap
  (Owner decision, above) — never merely because an
  `authorizing_decision_reference` was recorded on the second edge.
  Cycles are structurally forbidden within this category, without
  exception.
- **Continuity** (`successor_of`, `merged_into`, `split_from`) — a
  directed, append-only historical record. Never mutated in place;
  never fed into the hierarchy category's cycle check; never implies
  rights/role transfer by itself (section 7 of the specification).
- **Cooperation** (`affiliated_with`, `temporary_supervision_by`,
  `operates_within`, `participates_in`) — a general directed graph.
  Mutual edges are permitted (two nodes may each hold an
  `affiliated_with` edge toward the other); cycle-freedom is enforced
  only for `temporary_supervision_by` specifically (a node may not
  supervise itself, directly or transitively, at the same time), not
  for the category as a whole.

This is the explicitly justified "another model" the governing request
allows for: not a tree, not a single undifferentiated DAG, but multiple
typed graphs sharing one contract with per-category rules — the
narrowest model that (a) tolerates non-tree hierarchy shapes without
weakening cycle protection where it matters, (b) keeps historical
continuity immutable and separate from current structure, and (c)
keeps cooperative relationships free to form cycles where that is
actually meaningful (mutual affiliation).

## Rejected options

**Rejected: Option A (strict single tree).** Explicitly excluded by the
governing request ("Do not assume that the hierarchy is always a simple
tree") and contradicted by the special/cross-regional/non-territorial
unit requirement — a cross-regional working body reporting into two
Landesverbände cannot be represented under a strict single-parent
constraint without an artificial workaround (e.g. a fake intermediate
node), which would itself misrepresent the real organizational fact.

**Rejected: Option B (one undifferentiated graph).** Would either
under-protect the hierarchy category (permitting cycles that make no
organizational sense — an organization cannot be its own ancestor) or
over-protect the cooperation category (forbidding legitimate mutual
affiliation because a generic cycle check does not distinguish
category), and would let a continuity edge (`merged_into`) be
misread as a structural hierarchy edge by any consumer that does not
separately track relation semantics out-of-band.

**Rejected: Option D (three separate entities).** Three schemas for
what is, in every case, "an edge between two organizational nodes with
effective dating and a governing decision reference" duplicates the
common fields (section 6 of the specification: `valid_from`,
`valid_until`, `recorded_at`, `supersedes_*_id`,
`authorizing_decision_reference`) three times, multiplies the contract
surface (three JSON Schemas, three OpenAPI path groups, three sets of
tests) for no boundary benefit — unlike ADR-032's rejection of
splitting `Organization`/`CivicSpace` (a genuine, evolvable-independently
split), here the three categories are three _interpretations of the
same underlying fact shape_ (node A relates to node B, this way, during
this period), not three independently evolving domains.

## Owner decision — `parent_reference` is a non-authoritative projection

`Organization.parent_reference` (`docs/packs/PACK-08-SPECIFICATION.md`
section 3.1) is, and remains, **not authoritative**. It is a derived
read-model / compatibility projection only, provided purely as a
read-optimization convenience for the common single-parent case.
**`OrganizationalRelation` (this ADR) is the sole authoritative source**
of organizational structure. Binding rules:

- `parent_reference` **cannot be independently mutated** — there is no
  write path that sets it directly; it is always computed from the
  node's own current, active hierarchy-category `OrganizationalRelation`
  set.
- Where a node's hierarchy-category relations are ambiguous for
  projection purposes (zero parents, or more than one under an accepted
  `OrganizationalHierarchyOverlapPolicy`), `parent_reference` is either
  left null (zero parents) or, for the multiple-parent case, a future
  implementation pack **may omit `parent_reference` from that node's
  record entirely** rather than arbitrarily picking one parent to
  project — omission is preferred over a misleading single value,
  per the owner's explicit "may be omitted entirely if it risks
  becoming a second source of truth" instruction.
- **Consistency tests must prove projection correctness**: a future
  implementation pack adds a test asserting `parent_reference`, whenever
  present, always equals the unique result of resolving the node's own
  active hierarchy-category relations, and a second test asserting no
  code path writes `parent_reference` other than the projection
  mechanism itself (cross-referenced from ADR-032's own Testing
  requirements, updated by this correction round).

## Consequences

`organization-service` (ADR-032) implements exactly one relation write
path, parameterized by `relation_type`, with category-derived validation
branching internally — never three separate write paths. A future
implementation's cycle-detection logic must be written per-category,
not applied uniformly, and every test asserting "no cycles" must
specify which category it is asserting about, per
`docs/packs/PACK-08-SPECIFICATION.md` section 5.1's explicit
distinction. Renaming/territorial-reassignment (specification section
7.1) is modeled as a hierarchy-category relation _version_ change
(the old edge's `valid_until` is set; a new edge is created), never an
in-place field edit — mirroring the immutable-correction discipline
already established for `ProcessEligibilityPolicy` (ADR-028/30).

## Privacy impact

`OrganizationalRelation` carries only opaque node references and an
`authorizing_decision_reference` — never a person's identity. The
cooperation category's `participates_in` relation type could, if misused,
be extended to mean "person participates in organization" — this ADR
restates that `OrganizationalRelation` connects two `Organization`/
`OrganizationalUnit` nodes only; person-to-organization participation
remains `Membership`'s own domain (canon 8.3), never duplicated here.

## Security impact

Immutability of the continuity category (never edited in place) and
the append-only nature of every relation version prevents a
compromised or mistaken actor from silently rewriting organizational
history to fabricate a false succession chain — any correction is a
new, separately authorized version, auditable against the one it
supersedes. Category-specific cycle enforcement prevents a
maliciously or accidentally constructed hierarchy cycle from being used
to defeat ancestor/descendant scope-authorization logic (ADR-034),
which depends on the hierarchy category being genuinely acyclic to
terminate correctly.

## Migration impact

None — `OrganizationalRelation` is a wholly new entity; no existing
canon entity or service field is altered by this ADR. Future
implementation must ensure `organization-service`'s own relation-write
path is the _only_ writer, per ADR-032, so no existing service's own
ad hoc "parent" or "region" field is retroactively treated as
equivalent to a real `OrganizationalRelation` record without the
explicit per-field decision ADR-035 makes.

## Testing requirements

A future implementation pack must add: a property-based test asserting
no cycle is constructible within the hierarchy category regardless of
insertion order; a property-based test asserting mutual `affiliated_with`
edges are accepted without error; a test asserting `temporary_supervision_by`
rejects a self-supervision or transitive-self-supervision cycle; an
effective-dating overlap-validation test per specification section 6;
a test asserting a continuity-category record, once created, is never
subject to an update operation (only `supersedes_relation_id`-chained
new versions); non-territorial/cross-regional/special-unit fixture
cases exercising zero-parent and multiple-parent hierarchy nodes; a
test asserting a same-type multiple-parent hierarchy edge is rejected
absent an applicable, active `OrganizationalHierarchyOverlapPolicy`, and
accepted once one applies; and the `parent_reference` projection-
correctness tests named in the Owner decision section above.

## Unresolved questions

**OD-5 is closed by the Owner decision, above** (an explicit, versioned
`OrganizationalHierarchyOverlapPolicy` — not a bare decision reference,
and not a separate named workflow/entity beyond the policy itself).
Remaining, non-blocking:

- Whether `relation_type` values beyond the nine named in the governing
  request should be open to repository-configuration extension within
  an existing category (the specification currently proposes yes, new
  categories require a new ADR) — tracked as
  `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-4.
- Whether `operates_within`/`participates_in` need their own distinct
  cardinality rules (e.g. can a node `operate_within` more than one
  other node concurrently) — currently left unconstrained pending legal
  review of real cross-regional working-body practice. Tracked as OD-6.
- The exact field shape of `OrganizationalHierarchyOverlapPolicy`
  beyond "versioned, scoped by relation type and organizational
  profile, adopted by a `GovernanceDecision` reference" (mirroring
  every other versioned policy entity in this project) is not fully
  enumerated by this ADR and is left to the future implementation
  pack's own contract work, gated on the required canon amendment.

## Reversibility

Reversible with cost before code exists. Once real relation data
accumulates (especially continuity-category records, which are
explicitly append-only and historically significant), narrowing the
three-category model to something stricter becomes a major-version-
equivalent change; widening it (adding a fourth category) remains a
minor, additive change under canon section 25 if canon is ever amended
to include this entity.

## Related canon version

Authored against canon version `0.6.0`. **This ADR performs no canon
edit; `CANON_VERSION` and the canon checksum are unchanged.**
`OrganizationalRelation` and `OrganizationalHierarchyOverlapPolicy` are
new, proposed entities not yet in canon. Per the owner decision recorded
above, adding them to canon is a **required** step of a future,
mandatory canon amendment round — not an optional, conditional one —
that must be drafted and accepted before any PACK-08 implementation
begins.

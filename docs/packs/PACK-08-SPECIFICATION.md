# CLAUDE-PACK-08 — Organization & Regional Scope Foundation: Specification

## 0. Status and baseline

**This document is a specification and ADR-round deliverable only. It
does not authorize, and is not accompanied by, any service code,
database, migration, infrastructure, or production integration.** No
line of `services/`, `packages/`, or `contracts/` code changes as a
result of this document. `REPOSITORY_VERSION` and `CANON_VERSION` are
unchanged by this round (section 18).

**Confirmed baseline this specification is authored against:**

- `MASTER-ARCHITECTURE-0.8.md`, `MASTER-ROADMAP-0.8.md`,
  `HARD-INVARIANTS-0.8.md`, and `ARCHITECTURE-GAP-REGISTER.md` — the
  "master review revision" planning baseline, approved prior to this
  specification round, naming PACK-08 as "Organization & Regional Scope
  Foundation" and requiring exactly a specification/ADR round (not
  implementation) as the immediate next action.
- `PACK-08-PROPOSAL.md` — the accepted proposal this specification
  operationalizes into concrete entities, fields, workflows, and ADRs.
- `REPOSITORY_VERSION = 0.7.0`, `CANON_VERSION = 0.6.0`.
- CLAUDE-PACK-01 through CLAUDE-PACK-07 — **PASS**, PACK-07 implementation
  externally verified (`docs/handover/PACK-07-IMPLEMENTATION-REPORT.md`,
  section 6a).
- ADR-026 through ADR-031 — accepted (canon 0.6.0, Participation &
  Membership Context).
- `docs/canonical/TZ-00-domain-event-canon.md` sections 5.4 (Organization
  Context, responsibility only, no service), 8.1 (`Organization`), 8.2
  (`CivicSpace`), 8.3 (`Membership`, carrying `organization_id` and
  `region_code`), 8.4 (`RoleAssignment`, carrying `scope_id`) — all
  already present in canon 0.6.0, unimplemented by any service, and
  explicitly deferred to "PACK-08" by `docs/handover/PACK-07-SPEC-FINAL.md`
  section 11 ("Neither service may assume a live `Organization` or
  `CivicSpace` entity exists until PACK-08 defines one").

This specification, together with ADR-032 through ADR-036, is the
governed input the project owner, legal reviewers, and security
reviewers evaluate before any PACK-08 implementation round is
authorized. Nothing in this document is self-executing.

### 0.1 Correction round (2026-07-25)

This document was corrected, in place, in a targeted "PACK-08 SPEC
CORRECTION + OWNER DECISIONS" round following the original
specification candidate. That round applied **owner decisions only**
— no new implementation scope, no schema, no service code — and
settled several previously open questions:

- The organizational relationship graph model is fixed as **multiple
  typed directed graphs**, not a simple tree (sections 3.3, 5.1, 5.3).
- Inheritance policy ownership, versioning, and the
  restrict-never-broaden rule are fixed (section 8, ADR-034).
- Temporary supervision's mandatory `valid_until` and 90-day default
  maximum duration are fixed (section 8.1 mode 5, ADR-034).
- A minimum, eight-bullet institutional-role non-combinable-role
  baseline is fixed (section 9.3, ADR-036).
- `RoleAssignment.scope_id`'s six-category classification scheme is
  fixed at the policy level (section 11, ADR-035).
- `Organization.parent_reference`'s non-authoritative, derived-
  projection status is fixed (section 3.1).
- **A canon amendment is now confirmed as REQUIRED — not
  conditional — before any PACK-08 implementation begins** (section
  18, superseding this document's original "conditional canon ADR"
  framing).

ADR-032 through ADR-036 moved from `proposed` to `accepted` as a
direct consequence of this correction round settling the architectural
questions those ADRs raised; every one of the five ADRs' own
acceptance is explicitly qualified as **not** authorizing
implementation. See `docs/handover/PACK-08-SPEC-REPORT.md` for the
exact list of files changed in this round and
`docs/packs/PACK-08-OPEN-DECISIONS.md` for which owner decisions this
round closed, partially closed, or left open.

## 1. Goals and non-goals

**Goals:**

1. Give `Organization` and `CivicSpace` (canon 8.1/8.2, currently
   unowned stubs) a real service owner and a complete, extensible
   entity model supporting Bund/Landesverband/Kreisverband or
   Bezirksverband/Ortsverband or Ortsgruppe, non-territorial units,
   special and cross-regional units, and future extension — without
   freezing German administrative categories as permanent platform
   enums (section 3).
2. Explicitly separate `Organization`, geographic/legal jurisdiction,
   `CivicSpace`, and process-local scope as four non-interchangeable
   concepts (section 4).
3. Define typed, versioned, effective-dated organizational relationships
   and settle the tree/DAG/multiple-typed-graph question with an
   explicit, justified model (sections 5–6, ADR-033).
4. Define reorganization workflows (creation, activation, suspension,
   dissolution, merger, split, successor, renaming, territorial
   reassignment) with a hard no-implicit-rights-transfer invariant
   (section 7).
5. Define default-deny regional scope authorization with exact/ancestor/
   descendant/delegated/temporary-supervision/oversight-without-access
   modes, closing the cross-Land-leakage, confused-deputy, and
   role-name-as-proof-of-authority failure modes named by the baseline
   (section 8, ADR-034).
6. Define institutional authority assignments (DPO, election board
   member, election officer, independent auditor, finance auditor,
   party arbitrator, organizational administrator) and role-lifecycle
   invariants tying authority strictly to organization lifecycle and
   human decision (sections 9–10, ADR-036).
7. Classify every current use of `organization_id`, `region_code`,
   jurisdiction, `scope_type`/`scope_id`, `civic_space_id`-shaped
   references, and `role_scope` across the repository, and decide,
   field by field, whether each becomes an organization reference,
   stays process-local, represents legal jurisdiction, or needs a
   compatibility strategy (section 11, ADR-035,
   `docs/packs/PACK-08-MIGRATION-MATRIX.md`).
8. Specify canonical events, a complete reason-code set, a minimal
   read-only frontend slice, and privacy/minimization defaults for the
   organization domain (sections 12–15).
9. Preserve every applicable hard invariant from `HARD-INVARIANTS-0.8.md`
   and canon's own INV-01 through INV-10, with no exception carved out
   for organizational or regional data (section 16).

**Non-goals (this round):** no `organization-service` code, no
database, no migration script, no production IAM, no full
administration portal, no legal or accounting rule encoded as fact, no
canon edit unless a conditional canon ADR is later separately drafted
and accepted (section 17, section 18).

## 2. Terminology — four non-interchangeable concepts

Per `PACK-08-PROPOSAL.md` section 3.1 and the master architecture's
regional-scope framing, this specification fixes four concepts that
must never be treated as interchangeable identifiers, substituted for
one another, or collapsed into a single generic "scope" field:

- **Organization** — a governed, real-world organizational node in this
  platform's own organizational domain (a Bund-level party, a
  Landesverband, a Kreisverband, a non-territorial working body, a
  special or cross-regional unit). Owned exclusively by
  `organization-service` (ADR-032). Identified by `organization_id`
  (canon 8.1, unchanged field name).
- **Jurisdiction** — a geographic or legal jurisdiction fact (e.g. "DE",
  "Berlin", a supranational body), external to this platform's own
  organizational structure, already modeled as an open string on
  `ProcessEligibilityPolicy.jurisdiction` (canon 19d, ADR-028). A
  jurisdiction is a legal/geographic fact a process is evaluated
  against; it is never itself an `Organization` node, and no
  `Organization` node is ever assumed to "be" a jurisdiction merely
  because its name resembles one (a `Land`-level `Organization` is the
  party's own Landesverband, not the `Land` as a state entity).
- **CivicSpace** — a process-local area of participation nested under an
  `Organization` (canon 8.2: a federal programme, a Landesverband's own
  space, a local group, a topical workshop, a closed pilot). Owned by
  `organization-service` alongside `Organization` (ADR-032), referencing
  its parent via `organization_id` (canon 8.2, unchanged), identified by
  its own `space_id` (canon 8.2, unchanged — this specification does
  **not** rename `space_id` to `civic_space_id`; see section 11 and
  `PACK-08-MIGRATION-MATRIX.md` for why the shorthand `civic_space_id`
  used elsewhere is a reference-naming convention, not a field rename).
- **Scope** (process-local) — an opaque `scope_type`/`scope_id` pair
  already used, heterogeneously, by `credential-service`,
  `delegation-service`, `voting-service`, `initiative-service`,
  `eligibility-service`, and `membership-service` to mean "the specific
  object instance this capability check or policy applies to" — which,
  today, is _not_ an organizational reference in most of those services
  (section 11). A process-local scope reference may, going forward,
  _also_ carry an `OrganizationalScope` reference where the process is
  organization-bound (ADR-034/ADR-035), but it never becomes
  synonymous with `Organization` or `Jurisdiction`.

**Binding rule:** `Organization`, `Jurisdiction`, `CivicSpace`, and
process-local `Scope` may reference each other (an `OrganizationalScope`
value may point at an `Organization`; a `ProcessEligibilityPolicy` may
carry both a `jurisdiction` and, additively, an `OrganizationalScope`),
but no consumer may treat any one of the four as a substitute for
another, and no field is silently reinterpreted from one concept to
another (section 11).

## 3. Organization model

### 3.1 New and extended entities

Per `PACK-08-PROPOSAL.md` section 3.1 and ADR-032, this specification
proposes:

- **`Organization`** (canon 8.1, extended) — the governed organizational
  node itself. Existing fields (`organization_id`, `name`,
  `legal_operator`, `organization_type`, `status`,
  `default_policy_version`) are retained unchanged. Proposed additive
  fields: `organization_profile` (an extensible type/profile reference,
  see 3.2, replacing any assumption that `organization_type` alone
  carries the full territorial-level semantics), `parent_reference`
  (nullable — **owner decision, correction round: `parent_reference`
  is not authoritative.** It is a derived read-model / compatibility
  projection only, computed from the current, active hierarchy-category
  `OrganizationalRelation` set (section 5) — `OrganizationalRelation` is
  the sole authoritative source. `parent_reference` cannot be
  independently mutated (no write path sets it directly; it is always
  recomputed from relations). Where the underlying relation set has
  zero parents, `parent_reference` is null; where it has more than one
  concurrent parent-shaped edge (permitted per section 3.3/5.1's
  multiple-typed-graph model), `parent_reference` **may be omitted
  entirely** rather than arbitrarily picking one — a future
  implementation pack may choose to omit the field altogether if
  maintaining it risks becoming a second source of truth. Consistency
  tests must prove the projection is always correct relative to the
  authoritative relation set, never merely eventually consistent),
  `effective_from`, `effective_until` (nullable), `dissolved_at`
  (nullable), `successor_reference` (nullable, opaque; never implies
  rights transfer by itself — section 7).
- **`OrganizationalUnit`** (new, proposed) — a lighter-weight node type
  for subordinate structures that are not themselves a full
  `Organization` in the legal/statutory sense (e.g. a thematic working
  group, a task force, a temporary regional working body) but still
  need scope, effective dating, and relationship participation.
  Distinguishing an `OrganizationalUnit` from an `Organization` is a
  matter of the accepted `organization_profile`/type taxonomy (3.2),
  not a hard structural split — both share the same relationship
  (section 5) and scope (section 8) machinery, and `OrganizationalUnit`
  is deliberately modeled as an `Organization` specialization (same
  owning service, same table family conceptually), not a parallel
  hierarchy.
- **`CivicSpace`** (canon 8.2, unchanged fields) — retained exactly as
  canon already defines it; no field changes proposed.
- **`OrganizationalRelation`** (new, proposed) — the typed, versioned,
  effective-dated edge entity connecting two `Organization`/
  `OrganizationalUnit` nodes (section 5).
- **`OrganizationalStatus`** (new, proposed — a derived read model, not
  a stored duplicate of `Organization.status`) — resolves "is this
  organization/unit currently active, as of a given date" by combining
  `Organization.status`, `effective_from`/`effective_until`, and any
  in-flight reorganization workflow state (section 7), so that
  consumers never have to reimplement that combination themselves.
- **`OrganizationalAuthority`** (new, proposed) — the institutional
  authority assignment entity (DPO, election board member, election
  officer, independent auditor, finance auditor, party arbitrator,
  organizational administrator), distinct from canon 8.4
  `RoleAssignment` (section 9, ADR-036).
- **`OrganizationalScope`** (new, proposed reusable value shape, not an
  independently owned entity) — the narrow, opaque scope-reference
  contract other services receive when they need to ask "is this
  action/record inside this organizational scope" without receiving an
  `Organization` graph (section 8, ADR-034).
- **`OrganizationalHierarchyOverlapPolicy`** (new, proposed — owner
  decision, correction round) — a versioned, canonical policy entity,
  owned by `organization-service`, governing when more than one
  same-relation-category, hierarchy-shaped parent edge may concurrently
  exist for the same node (section 5.1, ADR-033). Closes OD-5: a simple
  tree is not authoritative, and multiple simultaneous parent-like
  relationships are permitted only when the relation types genuinely
  differ, or where this policy explicitly permits overlap for a given
  relation type — never as an ad hoc, undocumented exception.
- **`OrganizationalInheritancePolicy`** (new, proposed — owner decision,
  correction round) — a versioned, auditable, canonical policy entity,
  owned by `organization-service`, governing ancestor/descendant scope
  access (section 8.1 modes 2–3, ADR-034). Closes OD-8: inheritance
  policy ownership belongs to the Organization & Regional Scope domain;
  consuming domains may apply stricter rules but may never broaden
  inherited authority; frontend and downstream services can never infer
  inheritance independently of this policy.

### 3.2 Extensible type/profile model

`Organization.organization_type` (canon 8.1, currently an unconstrained
field with no documented enumeration) is proposed to be governed by an
**open, extensible `organization_profile` taxonomy**, never a canon-fixed
closed enum, satisfying the explicit "future extension without schema
redesign" requirement:

- **At least these named profiles are supported at launch** (open list,
  illustrative, extended by repository-level configuration, never by a
  canon edit, mirroring `identity_scheme`'s and `action_code`'s own
  established open-string-extensible pattern, ADR-028 item 5):
  `bund`, `landesverband`, `kreisverband`, `bezirksverband`,
  `ortsverband`, `ortsgruppe`, `non_territorial_unit`, `special_unit`,
  `cross_regional_unit`, `working_group`.
- **No profile is assumed to occupy a fixed level of a fixed-depth
  tree.** `bund`/`landesverband`/`kreisverband` commonly nest in that
  order, but this specification does not encode "exactly four levels"
  or any other fixed depth — a `bezirksverband` may exist between
  `landesverband` and `kreisverband` in some Länder and not others; a
  `special_unit` or `cross_regional_unit` may have no single
  territorial parent at all (section 5).
- **Non-territorial organizational units** (e.g. a party's youth
  organization, a professional or thematic association acting as an
  affiliated organizational unit) are first-class `Organization`/
  `OrganizationalUnit` nodes with `organization_profile` values of their
  own (e.g. `non_territorial_unit`), not a special case bolted onto the
  territorial hierarchy.
- **Special and cross-regional organizational units** (e.g. a joint
  Land/Bezirk working body, a cross-Land co-operation committee) are
  modeled the same way, with `OrganizationalRelation` edges (section 5)
  expressing however many parent/cooperation relationships actually
  apply — never forced into a single-parent slot.

### 3.3 Explicit non-tree assumption

**This specification does not assume the organizational hierarchy is
always a simple tree.** Sections 5–6 and ADR-033 fix the exact graph
model; the summary carried forward here: the _common_ Bund →
Landesverband → Kreisverband/Bezirksverband → Ortsverband/Ortsgruppe
chain is expected to be tree-shaped for most nodes, but
`OrganizationalRelation` itself supports multiple parent-shaped edges,
non-territorial nodes with no territorial parent, and cross-regional
nodes with edges into more than one branch — the data model must not
reject these as invalid merely because they do not fit a strict tree.

## 4. Concept separation (detail)

Extending section 2's binding rule with the concrete mechanism ADR-034/
ADR-035 rely on:

- An `OrganizationalScope` value always names exactly which of the four
  concepts (section 2) it is referencing — it is never a bare UUID with
  implied meaning. A consumer holding an `OrganizationalScope` can
  always answer "is this an Organization-scope reference, and if so,
  which organization" without needing to guess from field name alone.
- `ProcessEligibilityPolicy` (canon 19d, ADR-028) is the clearest
  existing example of the failure mode this separation prevents: it
  already carries `jurisdiction` (legal/geographic), `scope_type`/
  `scope_id` (process-local, structure-only per ADR-028), and, once
  PACK-08 is implemented, may additionally carry an
  `OrganizationalScope` reference (e.g. "this `epd_member_vote` process
  belongs to Kreisverband X") — three genuinely different facts about
  the same policy record, never collapsed into one field.
- `Membership.organization_id` (canon 8.3) is the clearest existing
  example of a field that _already looks like_ an `Organization`
  reference but, today, is never dereferenced or validated by any
  service (`docs/handover/PACK-07-SPEC-FINAL.md` section 11) — PACK-08
  is what gives that field a real referent for the first time (section
  11, ADR-035).

## 5. Organizational relationships

### 5.1 `OrganizationalRelation` — one entity, three relation categories

Per ADR-033 (full reasoning there), this specification proposes a
single canonical entity, `OrganizationalRelation`, with a
`relation_type` field whose value determines which of three
**relation categories** the edge belongs to — modeling "multiple typed
graphs" as one contract with per-category invariants, rather than three
separate schemas or one undifferentiated graph:

**Owner decision (correction round): Organization relationships use
multiple typed directed graphs. A simple tree is not authoritative.**
Multiple simultaneous parent-like relationships are allowed only when
relation types differ, or where an explicit
`OrganizationalHierarchyOverlapPolicy` (section 3.1) permits overlap for
a given relation type. Cycles are forbidden for containment and
subordination relations; cycles may be allowed only for relation types
explicitly declared non-hierarchical. Conflict and overlap validation
is relation-type-specific, never a single blanket rule. This closes
OD-5.

1. **Hierarchy category** — `parent_of`, `subordinate_to`. Expected to
   be tree-shaped for most territorial nodes, but **not enforced as a
   strict tree**: a node may have zero parents (a Bund-level or
   special/cross-regional node), and may have more than one
   concurrent parent-shaped edge only where an
   `OrganizationalHierarchyOverlapPolicy` record (section 3.1)
   explicitly permits it for the relation types involved (e.g. a
   cross-regional unit reporting into two Landesverbände under an
   overlap policy that names that case) — never as an undocumented,
   ad hoc exception. Cycles are structurally forbidden in this category,
   without exception (a node may never be its own ancestor, directly or
   transitively, for `parent_of`/`subordinate_to`).
2. **Continuity category** — `successor_of`, `merged_into`,
   `split_from`. A directed, append-only, historical record of
   organizational continuity events (section 7). Never mutated in
   place; never interpreted as a hierarchy edge; never implies rights
   or role transfer by itself (section 7, ADR-036).
3. **Cooperation category** — `affiliated_with`, `temporary_supervision_by`,
   `operates_within`, `participates_in`. A general directed graph.
   Mutual `affiliated_with` edges (A affiliated with B and B affiliated
   with A) are permitted — cycle-freedom is **not** a blanket rule
   across all relation types, only within the hierarchy category
   (bullet 1, no exception) and within `temporary_supervision_by`
   specifically (a node may not supervise itself, directly or
   transitively, at the same time). Relation types in this category are
   the ones this specification treats as explicitly declared
   non-hierarchical, for the purpose of the cycle rule above; a future
   new relation type added to this category by repository configuration
   must be reviewed against the same non-hierarchical/cycle-permitting
   classification before being added.

### 5.2 Fields

```text
OrganizationalRelation (proposed):
  relation_id
  relation_version
  relation_type          — parent_of | subordinate_to | affiliated_with
                            | successor_of | merged_into | split_from
                            | temporary_supervision_by | operates_within
                            | participates_in  (open, extensible per
                            category — new relation_type values may be
                            added within an existing category by
                            repository configuration; a new category
                            requires an ADR)
  relation_category      — hierarchy | continuity | cooperation
                            (derived from relation_type, never set
                            independently)
  source_organization_id
  target_organization_id
  status                 — draft | active | superseded | ended
  valid_from
  valid_until            — nullable
  recorded_at
  supersedes_relation_id — nullable; corrections are always a new
                            version, never a rewrite (mirrors
                            `ProcessEligibilityPolicy`'s own
                            versioning discipline, ADR-028/30)
  authorizing_decision_reference — opaque reference to the governed
                            decision that created this relation (never
                            self-created by automated inference)
```

### 5.3 Graph-model decision, restated

**Decision (ADR-033): multiple typed relationship graphs over one
`OrganizationalRelation` entity**, not a single tree and not one
undifferentiated DAG. This is the explicitly justified model required
by the task; see ADR-033 section "Decision" for the full alternatives
analysis.

## 6. Effective dating

All organizational structures (`Organization`, `OrganizationalUnit`,
`OrganizationalRelation`) and authority assignments
(`OrganizationalAuthority`) support, uniformly:

- `valid_from` — mandatory.
- `valid_until` — nullable; absent means "still in effect."
- `recorded_at` — when the record was actually written (distinct from
  `valid_from`, which may be future-dated — see below).
- `supersedes_*_id` — the correction/versioning mechanism; a correction
  is always a new version, never an in-place edit (mirrors
  `ProcessEligibilityPolicy`/`PartyMembershipEligibilityPolicy`'s own
  established pattern, ADR-028 item 6, ADR-030).
- **Historical queries** — "what was the organizational structure/scope/
  authority as of date X" is always answerable by filtering every
  relevant record (relation, status, authority) to those whose
  `[valid_from, valid_until)` window covers X, never by mutating or
  deleting a past record.
- **Future-dated changes** — `valid_from` may be set in the future
  (e.g. a reorganization decided today, effective at the start of next
  term); until `valid_from` is reached, the change is not yet in
  effect for scope-authorization purposes (section 8), even though the
  record already exists and is queryable as a planned future state.
- **Overlap validation** — for relation types where more than one
  concurrently active edge would be contradictory (e.g. two different
  `parent_of` edges asserting two different parents for the same node
  at the same date, where no `OrganizationalHierarchyOverlapPolicy`
  record, section 3.1/5.1, explicitly permits that overlap for the
  relation types involved), the write path must reject an overlapping
  `[valid_from, valid_until)` window against an existing active record
  of the same conflicting shape. **Conflict and overlap validation is
  relation-type-specific, not a single blanket rule** (owner decision,
  correction round, section 5.1): relation types that legitimately
  permit concurrency (e.g. multiple simultaneous `affiliated_with`
  edges, or a hierarchy-category edge pair explicitly covered by an
  `OrganizationalHierarchyOverlapPolicy` record) are exempt from this
  check for that specific relation-type combination only, never
  category-wide by default.

## 7. Reorganization

### 7.1 Workflows

Each of the following is a distinct, auditable, explicitly governed
event/decision — never inferred automatically from a status change
elsewhere:

- **Creation** — a new `Organization`/`OrganizationalUnit` node, status
  `draft` initially (mirroring canon 8.1's existing `draft` status),
  requiring an `authorizing_decision_reference`.
- **Activation** — `draft → active`; requires the same authorized
  human-decision discipline as every other consequential PACK-07
  transition (mirroring `MembershipApplication`'s Stage A/Stage B
  pattern, ADR-028 item 2) — never automatic on creation.
- **Suspension** — `active → restricted` (canon 8.1's existing status);
  reversible, requires a decision reference and reason code (section
  13).
- **Dissolution** — `active`/`restricted → archived` (canon 8.1's
  existing terminal status); `dissolved_at` recorded; irreversible
  through this workflow (a dissolved organization is never silently
  reactivated — only a new node, optionally linked via `successor_of`,
  may continue its work).
- **Merger** — two or more source `Organization` nodes each gain a
  `merged_into` continuity-category relation targeting one resulting
  node; each source node is dissolved as part of the same governed
  decision, never left ambiguously active.
- **Split** — one source `Organization` node gains one or more
  `split_from` continuity-category relations from the resulting nodes;
  the source node's own continuation status (dissolved vs. continuing
  as one of the resulting nodes) is an explicit decision field, never
  inferred from which resulting node "looks like" the original.
- **Successor organization** — `successor_of` relation recorded, always
  as its own explicit governed decision, carrying an
  `authorizing_decision_reference`; the predecessor node's own
  `successor_reference` (3.1) is populated at the same time as a
  read-optimization convenience, never as the sole record of the fact.
- **Renaming** — an additive, versioned `name` change; the prior name
  remains queryable historically (mirrors the general effective-dating
  discipline, section 6); renaming alone never changes
  `organization_id`, hierarchy relations, or authority assignments.
- **Territorial reassignment** — a change to which parent node an
  `Organization`/`OrganizationalUnit` reports into; recorded as a new
  hierarchy-category `OrganizationalRelation` version (the old parent
  relation's `valid_until` is set, a new one is created with its own
  `valid_from`) — never an in-place edit of the existing relation
  record.

### 7.2 Hard invariant — no automatic rights transfer

**No rights, roles, or access may automatically transfer to a successor
organization, or to any resulting node of a merger or split, without an
explicit governed decision.** This is a hard, structural invariant,
proposed for canon alongside INV-08/INV-09/INV-10 and mirroring
`HARD-INVARIANTS-0.8.md`'s HI-09 (no automated final deprivation of
rights) applied to the _positive_ direction (no automated final
_grant_ of rights either):

- A `merged_into`/`split_from`/`successor_of` relation, by itself, never
  activates, transfers, or extends any `OrganizationalAuthority` or
  `RoleAssignment` scoped to the predecessor node(s).
- Every such transfer requires its own explicit
  `authorizing_decision_reference`, distinct from the reorganization
  decision itself (though both may be recorded as part of the same
  governed session, they remain two separately auditable decisions).
- Absent an explicit transfer decision, authority scoped to a
  dissolved, merged-away, or split-away node simply lapses at
  dissolution (section 9.3) — never silently continues, and never
  silently voids without record (the lapse itself is an audited state
  change, not a deletion).

## 8. Regional authorization

### 8.1 Default-deny model

**Every regional-scope authorization decision defaults to deny.**
Access is granted only by one of the following explicit modes,
evaluated by a narrow, atomic, server-side read
(`check_regional_scope_access`, mirroring the atomic-capability-check
pattern already established by ADR-027/canon 19d.14):

1. **Exact-scope access** — the actor's own `OrganizationalScope`
   reference matches the target record's scope exactly.
2. **Ancestor-scope access** — the actor's scope is a hierarchy-category
   ancestor of the target's scope, **and** the canonical, versioned
   `OrganizationalInheritancePolicy` (section 3.1, owner decision,
   correction round) for the relevant role/action grants this (never
   assumed merely from hierarchy position — see 8.2). Inheritance
   policy is owned exclusively by the Organization & Regional Scope
   domain (`organization-service`); consuming domains may apply
   stricter rules on top of it but may never broaden the authority it
   grants; the policy itself is versioned and every grant it produces is
   auditable; frontend and downstream services may never infer
   ancestor-scope access independently of an actual policy evaluation.
   Closes OD-8.
3. **Descendant-scope access** — symmetric to 2, for the (rarer) case
   where a descendant-scoped actor needs a narrow read into an ancestor
   record; likewise never assumed by default, and governed by the same
   `OrganizationalInheritancePolicy` and its restrict-never-broaden rule.
4. **Explicitly delegated cross-scope access** — a time-bounded,
   purpose-recorded delegation record (distinct from ancestor/descendant
   inheritance) granting a named actor or role a specific cross-scope
   permission.
5. **Temporary supervision** — the `temporary_supervision_by`
   cooperation-category relation (section 5.1), itself effective-dated
   and revocable, granting the supervising node's authorized actors a
   narrow, purpose-bound access window into the supervised node's
   scope. **Owner decision (correction round), closes OD-10:**
   temporary supervision must always carry both `valid_from` and
   `valid_until` — open-ended temporary supervision is forbidden. The
   default maximum duration is 90 days from `valid_from`. Extending a
   temporary-supervision window beyond its current `valid_until`
   requires a new, separately governed decision and its own audit
   record — never a silent extension of the existing record. A future,
   dedicated legal review may define narrower (never wider) maximum
   durations for specific organizational forms.
6. **Institutional oversight without implicit data access** — an
   `OrganizationalAuthority` assignment (section 9) whose
   `grants_procedural_authority` is true but whose `grants_data_access`
   is false grants no read access at all by virtue of the title; any
   data access an oversight role needs must be granted through one of
   modes 1–4 explicitly, never inferred from the oversight title
   itself.

### 8.2 Explicitly prevented anti-patterns

- **Cross-Land data leakage** — a Landesverband-scoped actor never
  receives another Land's data through any of the six modes above
  unless mode 4 (explicit delegation) or mode 5 (temporary supervision)
  names that specific cross-Land grant.
- **Confused-deputy access** — an action authorized "for scope A" is
  never honored against scope B merely because the same
  `RoleAssignment`/`OrganizationalAuthority` record happens to be
  presented; every check re-validates the actor's scope against the
  target's scope at evaluation time (mirrors HI-08's atomic,
  bound-to-current-state check).
- **Role name reuse as proof of authority** — a `role_code` string
  (e.g. `"kreisvorsitzender"`) is **never**, by itself, proof of
  authority. Every check resolves through an actual, currently `active`
  `RoleAssignment`/`OrganizationalAuthority` record with a matching
  scope and validity window — never through string comparison against
  a role name alone.
- **Implicit inheritance from organization names or hierarchy
  position** — being the Landesverband's own `Organization` node's
  administrator does not, by itself, grant any Kreisverband-level
  authority; ancestor/descendant inheritance (modes 2–3) is opt-in per
  role/action via the explicit, canonical `OrganizationalInheritancePolicy`
  (section 8.1, ADR-034), never a default consequence of hierarchy
  position, and never inferred by the frontend or a downstream service
  independently of an actual policy evaluation.

## 9. Institutional authority assignments

### 9.1 `OrganizationalAuthority` — fields

```text
OrganizationalAuthority (proposed):
  authority_id
  authority_version
  role_code                     — dpo | election_board_member |
                                   election_officer | independent_auditor
                                   | finance_auditor | party_arbitrator |
                                   organizational_administrator (open,
                                   extensible — new institutional roles
                                   are added by configuration + ADR
                                   review, never silently)
  appointing_authority_reference — opaque reference to the authorized
                                   body/decision that made the
                                   appointment; never the same actor
                                   being appointed (section 10)
  scope                         — an OrganizationalScope reference
                                   (section 4/8)
  valid_from
  valid_until                  — nullable
  revoked_at                   — nullable
  revocation_reason_reference   — mandatory if revoked_at is set
  incompatibilities             — set of role_code values this
                                   assignment may never be combined with
                                   in the same scope, for the same
                                   actor, at the same time (section 9.3)
  grants_data_access           — boolean, independent of...
  grants_procedural_authority   — ...this boolean; a role may hold
                                   either, both, or neither, and neither
                                   implies the other (8.1 mode 6)
  audit_reference               — every assignment and revocation
                                   creates an AuditEvent via
                                   epd2_audit_core, unchanged
                                   project-wide convention
```

### 9.2 Named institutional roles — non-exhaustive description

- **Data protection officer (DPO)** — procedural authority over
  processing-registry and privacy-review matters within scope; data
  access only where an explicit, separate grant names it (this pack
  seeds the role definition; the DPO's operational workflow is PACK-09
  scope per `MASTER-ROADMAP-0.8.md`).
- **Election board member / election officer** — procedural authority
  over election operations within scope; distinct roles (a board acts
  collectively, an officer individually), never conflated.
- **Independent auditor** — read/verification authority, explicitly
  never write authority over the records being audited.
- **Finance auditor** — independent review authority over finance
  records within scope, structurally separated from finance
  preparation/approval authority (a future PACK-10 concern; this pack
  seeds the role and its non-combinable-role rule, section 9.3).
- **Party arbitrator** — procedural authority within the (deferred)
  arbitration workflow (PACK-09); this pack defines only the
  authority-assignment shape, never the arbitration procedure itself.
- **Organizational administrator** — scoped administrative authority
  over one `Organization`/`OrganizationalUnit` node's own records;
  **never** a platform-wide administrator (HI-11) — an
  `organizational_administrator` assignment's `scope` is always a
  single `OrganizationalScope`, never "all scopes."

### 9.3 Non-combinable roles

**Owner decision (correction round), closes OD-7 only to the extent
necessary for implementation readiness:** the following minimum
non-combinable-role baseline is adopted, superseding this
specification's original four-pair starting set. It is marked as a
**minimum baseline, subject to legal refinement** — not a full or final
matrix.

1. An `election_officer` cannot simultaneously act as `election_auditor`
   for the same process/scope.
2. An `election_board_member` cannot independently approve their own
   appointment or removal.
3. A `finance_auditor` cannot simultaneously be `finance_administrator`
   for the same organization/scope.
4. An `independent_auditor` cannot audit actions they themselves
   performed or approved.
5. A `party_arbitrator` cannot participate in a case where they hold an
   operational role in the affected organization.
6. An `organizational_administrator` cannot self-assign institutional
   authority (restates section 10 rule 5 as a role-specific instance).
7. `DPO` procedural independence must be preserved — a DPO's own
   procedural determinations cannot be overridden or directed by the
   organization or role it oversees.
8. No person may satisfy both sides of a dual-control action (restates
   section 10 rule 6 as a general cross-role rule).

**Retained from the original starting set, as specific instances of
bullets 3 and 6 above:**

- `finance_auditor` is incompatible with `organizational_administrator`
  in the same scope (auditor independence).
- `finance_auditor` is incompatible with any future finance-preparation/
  approval role in the same scope (PACK-10 will need to extend this set
  once such roles exist; this pack reserves the rule, not the roles).
- `independent_auditor` is incompatible with `organizational_administrator`
  in the same scope, for the same reason.
- `election_board_member`/`election_officer` are incompatible with
  being a declared candidate in the election they administer (exact
  mechanism deferred to the eligibility/membership domain's own
  conflict-of-interest machinery, `ConflictAssessment`, canon 19d.11 —
  this pack records the incompatibility rule, not a new detection
  mechanism).

The complete, legally-refined matrix beyond this baseline remains open
(`PACK-08-PROPOSAL.md` section 6, tracked as
`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-7, partially closed).

## 10. Role lifecycle

An `OrganizationalAuthority` (and, by the same rule, a `RoleAssignment`
scoped to an `Organization`):

1. **Cannot begin before the organization exists** — `valid_from` must
   be on or after the scope's own `Organization.effective_from`
   (section 6); the write path rejects a record whose validity window
   starts before its own scope's existence window.
2. **Cannot remain valid after dissolution without explicit migration**
   — dissolution (section 7.1) suspends every authority assignment
   scoped to the dissolved node by default (fail-closed); only an
   explicit, separately authorized migration decision may reactivate or
   redirect any of them toward a successor scope (section 7.2).
3. **Does not automatically move after merge or split** — restated from
   section 7.2; a merge/split relation record never carries an implicit
   authority-transfer effect.
4. **Does not automatically transfer to a successor** — restated from
   section 7.2.
5. **Cannot be self-assigned** — `appointing_authority_reference` must
   resolve to an actor/body distinct from the assignment's own subject.
6. **Cannot be activated by the same person who proposed it where dual
   control is required** — mirrors `MembershipApplication`'s Stage A/
   Stage B separation (ADR-028 item 2) and
   `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`'s existing self-review
   prohibition (PACK-07); the proposing actor and the activating actor
   must differ for every role this specification or a future
   legal-review round designates as dual-control (starting set: all
   seven named institutional roles, section 9.2).

## 11. Cross-domain migration (summary — full matrix is its own deliverable)

The complete field-by-field classification is
`docs/packs/PACK-08-MIGRATION-MATRIX.md`, decided by ADR-035. Summary of
the classification categories applied:

- **Becomes an organization reference:** `Membership.organization_id`
  (canon 8.3) — currently an opaque, never-dereferenced field
  (`docs/handover/PACK-07-SPEC-FINAL.md` section 11); PACK-08 gives it,
  for the first time, a real `Organization` node to resolve against,
  additively, with no schema break (the field itself is unchanged; only
  a future implementation pack's _behavior_ around it changes).
- **Remains process-local, opaque scope:** the `scope_type`/`scope_id`
  pairs on `credential-service`, `delegation-service`,
  `voting-service`/`initiative-service` (used as `required_scope_type`/
  `required_scope_id` in atomic capability checks), and
  `PartyMembershipEligibilityPolicy` (membership-service) — none of
  these are reclassified as `Organization` references by this round;
  they continue to mean "the specific object instance a capability
  check applies to."
- **Represents legal jurisdiction, not organization:**
  `ProcessEligibilityPolicy.jurisdiction` (eligibility-service, canon
  19d, ADR-028) — explicitly retained as a distinct legal/geographic
  concept, never reinterpreted as an `Organization` reference (section
  2/4).
- **Requires a compatibility strategy:** `Membership.region_code`
  (canon 8.3) — recommended to remain, additively, as a legacy free-form
  field through a deprecation window, alongside (never replaced by) a
  new, additive `OrganizationalScope` reference field, per ADR-035's
  no-silent-reinterpretation rule.
- **False cognate, no migration needed:** `transparency-service`'s
  `GENERALIZE_TO_ROLE_SCOPE` redaction-transformation enum value (a
  statistical-disclosure-control generalization strategy name, unrelated
  to any organizational scope concept) — flagged explicitly so a future
  implementer does not conflate the two merely because both contain the
  substring "scope."
- **Naming clarification, no field exists yet:** `civic_space_id` — no
  such field exists anywhere in the repository today; canon 8.2's own
  primary key is `space_id`. This specification recommends that any
  future foreign-key field referencing a `CivicSpace` be named
  `civic_space_id` explicitly (for clarity against the generic
  `scope_id` pattern), while `CivicSpace`'s own primary key remains
  `space_id`, unchanged — a naming convention decision, not a migration.

**No automated bulk rewrite occurs inside this specification or its
ADRs.** Every reinterpretation above is a decision, not a script; a
future implementation pack executes it, additively, under its own
review.

## 12. Privacy and minimization

- **No new global identity graph.** `Organization`/`OrganizationalUnit`/
  `OrganizationalRelation`/`OrganizationalAuthority` never introduce a
  cross-domain person identifier; `Membership`'s own existing
  `account_reference` (canon 8.3, unchanged) remains the only link
  between a person and an organization, and it is never exposed as part
  of an organization or scope read (mirrors HI-01/HI-04).
- **Domain-specific pseudonymous references.** Where an
  `OrganizationalAuthority`'s `appointing_authority_reference` or a
  `RoleAssignment`'s `assigned_by` needs to name a person, it does so
  through the same opaque, domain-scoped reference convention already
  established project-wide (ADR-031's anti-correlation principle),
  never a raw name or a cross-domain identifier.
- **Minimum necessary claims.** `check_regional_scope_access` (section 8) returns a boolean and, where useful, a reason code — never an
  `Organization` graph, a member list, or a role-holder list.
- **Scoped read models.** `OrganizationalStatus` (section 3.1) and any
  future organization-browser read model (section 14) return only the
  fields relevant to the requesting scope's own authorization level —
  never the full internal record.
- **No public membership exposure.** Restated from
  `Membership`'s existing restricted-by-default rule (ADR-028 item 3):
  which `account_reference`s hold `Membership` in which `Organization`
  is never exposed by any organization-domain read, public or
  cross-service.
- **No cross-regional member directory by default.** No API or read
  model this specification proposes returns "all members/role-holders
  across scopes" — every read is scope-bound per section 8, and a
  cross-scope aggregate view, if ever needed, requires its own
  separately reviewed, purpose-bound export path (mirroring HI-27's
  export-control discipline), never a default capability of the
  organization domain.

## 13. Events

Canonical events proposed (owner: `organization-service`, except where
noted), carrying no unnecessary identity data (only opaque references
and reason codes, per section 12):

- `OrganizationCreated`
- `OrganizationActivated`
- `OrganizationSuspended`
- `OrganizationDissolved`
- `OrganizationMerged`
- `OrganizationSplit`
- `OrganizationSuccessorDeclared`
- `OrganizationalRelationCreated`
- `OrganizationalRelationEnded`
- `OrganizationalAuthorityAssigned`
- `OrganizationalAuthorityRevoked`
- `RegionalScopeAccessGranted` (emitted for modes 3–5 of section 8.1 —
  exact-scope access, being the default, does not itself emit a grant
  event; only ancestor/descendant/delegated/temporary-supervision
  grants, being the exceptions to default-deny, are individually
  audited this way)
- `RegionalScopeAccessRevoked`

No event payload schema is created by this round (section 18/20 —
contracts are a future implementation-pack deliverable); the event
names, owning service, and no-unnecessary-identity-data rule are fixed
here so a future implementation pack does not have to re-derive them.

## 14. Reason codes

The following PACK-08 reason codes are defined (full registry file
creation deferred to implementation, per section 18/20):

- `ORGANIZATION_NOT_ACTIVE`
- `ORGANIZATION_SCOPE_MISMATCH`
- `CROSS_SCOPE_ACCESS_DENIED`
- `AUTHORITY_ASSIGNMENT_INVALID`
- `AUTHORITY_ROLE_INCOMPATIBLE`
- `AUTHORITY_SCOPE_INVALID`
- `SUCCESSOR_TRANSFER_REQUIRES_DECISION`
- `ORGANIZATIONAL_RELATION_OVERLAP`
- `ORGANIZATIONAL_CYCLE_FORBIDDEN`
- `HISTORICAL_SCOPE_NOT_EFFECTIVE`
- `ORGANIZATION_DISSOLVED` — authority/scope check against a dissolved
  node with no migration decision on record.
- `ORGANIZATION_ALREADY_ACTIVE` — activation attempted on a node not in
  `draft`/`restricted`.
- `AUTHORITY_SELF_ASSIGNMENT_PROHIBITED` — section 10 rule 5.
- `AUTHORITY_DUAL_CONTROL_VIOLATION` — section 10 rule 6.
- `ORGANIZATIONAL_RELATION_CYCLE_TYPE_NOT_APPLICABLE` — a cycle-check
  attempted against a relation category that permits cycles (section
  5.1) is a caller error, not a domain violation; this code
  distinguishes that from `ORGANIZATIONAL_CYCLE_FORBIDDEN` itself.

## 15. Frontend slice

Per `PACK-08-PROPOSAL.md` section 3.7 and `MASTER-ROADMAP-0.8.md`
sequencing principle 8, a **minimal, read-only vertical slice**,
against real future PACK-08 APIs, non-authoritative, unable to mutate
organizational state:

- **Organization browser** — list/search/detail view of
  `Organization`/`OrganizationalUnit` nodes within the viewer's own
  authorized scope.
- **Hierarchy/relationship viewer** — renders the `OrganizationalRelation`
  graph (section 5) for a selected node, across all three relation
  categories, clearly distinguishing them.
- **Current and historical scope view** — renders `OrganizationalStatus`
  and relation validity as of "now" or as of a selected historical
  date (section 6).
- **Institutional role view** — read-only list of `OrganizationalAuthority`
  assignments within the viewer's authorized scope, showing role,
  scope, validity, and whether it grants data access or only
  procedural authority (section 8.1 mode 6) — never showing the
  assigned actor's identity beyond the same opaque reference the
  backend itself uses.
- **Authorization test console** — a development/review tool letting a
  reviewer submit a hypothetical `(actor scope, target scope, action)`
  triple and see which of section 8.1's six modes, if any, would grant
  access, and why — for verifying default-deny behavior, never for
  granting real access itself.

**Not built this round, and not built even in the eventual
implementation pack without a separate decision:** a full regional
administration portal (create/edit/dissolve through the UI), any
mutation path, or any cross-scope aggregate view (section 12).

## 16. Hard invariants preserved

Every applicable hard invariant from `HARD-INVARIANTS-0.8.md` and canon's
own INV-01 through INV-10 is preserved without exception for
organizational or regional data. Most directly engaged by this
specification:

- **HI-01 (no global user ID)** — section 12.
- **HI-04 (data minimization at every boundary)** — sections 8, 12.
- **HI-07 (frontend is never a source of authority)** — section 15; the
  authorization test console evaluates against the same backend logic
  a real check would use, never a client-side approximation.
- **HI-08 (atomic capability enforcement)** — section 8.1.
- **HI-09 (no automated final deprivation/grant of rights)** — section
  7.2, extended to organizational continuity events.
- **HI-11 (no universal administrator)** — sections 9.2, 8.2.
- **HI-12 (separation of duties)** — sections 9.3, 10.
- **HI-13 (scoped institutional authority)** — section 9.
- **HI-24 (regional scope isolation)** — sections 8, 11.
- **INV-02 (one owner per entity)** — section 3 (ADR-032): every
  proposed entity has exactly one owning service.
- **INV-04/INV-05 (political actions leave a trace; history is never
  silently rewritten)** — sections 6, 13: every reorganization and
  authority change is an audited event, and every correction is a new
  version, never an edit.
- **INV-10 (fail-closed)** — section 8.1: default deny.

## 17. Explicitly out of scope

Per the governing request and `PACK-08-PROPOSAL.md` section 4, this
round (specification and its eventual implementation) does not include:

databases; migrations; production IAM; eID; payments; Party Finance;
Document Service; Search; DLP; Party Arbitration workflows; Legal Hold;
voting cryptography; deployment; HSM/KMS; a full frontend beyond section
15's minimal slice; a mobile client; restructuring the monorepo;
additional languages beyond German/English (`PACK-08-PROPOSAL.md`
section 3.6); real authentication/MFA; privileged/JIT access or
break-glass implementation; a full administration portal.

## 18. Versions

**Unchanged by this round:**

- `REPOSITORY_VERSION` remains `0.7.0`.
- `CANON_VERSION` remains `0.6.0`.
- `docs/canonical/TZ-00-domain-event-canon.md` is not edited; its
  checksum is unchanged (this document performs no edit to that file).

A conditional canon ADR is explicitly **not** drafted as one of the five
required ADRs (section 16 of the governing request), consistent with
`PACK-08-PROPOSAL.md`'s own "Conditional canon ADR ... required only if
the accepted implementation adds/changes canonical fields, ownership,
events, or hard invariants" framing.

**Owner decision (correction round), closes OD-1/OD-18 — canon
amendment is REQUIRED, not conditional:** PACK-08 introduces
canon-relevant concepts not present in canon 0.6.0 today —
`Organization` extensions (`parent_reference`, `organization_profile`,
effective dating, successor reference), `CivicSpace` ownership,
`OrganizationalRelation`, `OrganizationalAuthority`,
`OrganizationalScope`, regional scope authorization, institutional
authority lifecycle, and reorganization/successor invariants. Because
of this:

- **PACK-08 implementation must not start before a separate canon
  amendment round** is prepared and accepted.
- `CANON_VERSION` and the canon checksum **remain unchanged in this
  correction round** — this document performs no canon edit itself.
- A future, dedicated canon ADR must be drafted, reviewed, and accepted
  — proposing the actual canon 8.x additions/amendments this
  specification's entities require — **before** any PACK-08
  implementation pack begins. This is a firm precondition, not a
  possibility left open for later discretion.

This supersedes this document's original "whether canon needs amendment
is an open decision" framing (formerly tracked as OD-1): the question is
now closed — canon amendment is mandatory before implementation, only
its exact content and timing remain to be drafted in that future round.

## 19. Verification performed this round

This is a documentation-only round: no service, schema, contract, or
test code changes. Verification honestly performed and reported in
`docs/handover/PACK-08-SPEC-REPORT.md` covers: `scripts/check_repository.py`,
`scripts/verify_versions.py`, the full existing Python test suite (Ruff,
mypy, pytest) to confirm this round introduced no regression, and a
manual cross-reference check of every new document against the other
four (no contradictory field names, statuses, or ownership claims). No
external GitHub Actions run is claimed by this round.

## 20. Deliverables

- `docs/packs/PACK-08-SPECIFICATION.md` (this file).
- `docs/adr/ADR-032-organization-and-civic-space-ownership.md`
- `docs/adr/ADR-033-organizational-relationships-effective-dating-and-reorganization.md`
- `docs/adr/ADR-034-regional-scope-authorization-and-inheritance.md`
- `docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md`
- `docs/adr/ADR-036-institutional-authority-assignments-and-non-combinable-roles.md`
- `docs/handover/PACK-08-SPEC-REPORT.md`
- `docs/packs/PACK-08-MIGRATION-MATRIX.md`
- `docs/packs/PACK-08-OPEN-DECISIONS.md`
- One clean archive: `epd2-civic-os-PACK-08-SPEC-ADR-CORRECTED.zip`
  (this correction round; supersedes the original
  `epd2-civic-os-PACK-08-SPEC-ADR-CANDIDATE.zip`).

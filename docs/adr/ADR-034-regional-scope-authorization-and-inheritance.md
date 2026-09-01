# ADR-034: Regional scope authorization and inheritance

## Status

`accepted`

## Date

2026-07-25

## Owner decision

Accepted 2026-07-25, in the PACK-08 spec-correction round, with two
architectural decisions now closed and binding:

**Inheritance policy ownership (closes OD-8):** the per-role/per-action
inheritance policy (modes 2–3, below) is a canonical, versioned,
auditable entity — **`OrganizationalInheritancePolicy`** (new, proposed,
owned by `organization-service`) — not merely repository/deployment
configuration. Binding rules: it is owned by the Organization & Regional
Scope domain (`organization-service`) exclusively; **consuming domains
may apply stricter rules on top of it** (e.g. `governance-service` may
refuse to honor an ancestor-scope grant this policy would otherwise
permit, for its own additional reasons) but **may never broaden** what
the policy grants; every version is auditable and effective-dated
(section 6 of the specification); and **frontend and downstream
services cannot infer inheritance independently** — every ancestor/
descendant access decision is still evaluated by
`check_regional_scope_access` itself, never precomputed or cached by a
consumer and applied without re-checking.

**Temporary supervision bounds (closes OD-10):** `temporary_supervision_by`
(mode 5) **must always have both `valid_from` and `valid_until`** —
**open-ended temporary supervision is forbidden**. Absent an explicit,
shorter duration, the **default maximum duration is 90 days**.
Extending a temporary-supervision grant past its `valid_until` **requires
a new governed decision and its own audit record** — never a silent
`valid_until` extension on the existing record. A future legal-review
round may define a narrower maximum for specific organizational forms;
it may only narrow, never widen, the 90-day default fixed here.

**This acceptance does not authorize implementation.** A separate,
dedicated canon amendment round — covering `check_regional_scope_access`,
its six access modes, and `OrganizationalInheritancePolicy` — is
required before any implementation begins
(`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18, closed in favor of
"mandatory"). `CANON_VERSION` and the canon checksum are unchanged by
this correction round.

## Context

`HARD-INVARIANTS-0.8.md` HI-24 ("Regional scope isolation") requires
every organization-bound record, role, policy, workflow, query, and
export to be explicitly scoped, with Bund/Land/Kreis and subordinate
scopes isolated by default and inheritance or cross-scope access
explicit, narrow, and audited. `PACK-08-PROPOSAL.md` section 3.2
requires a minimal `OrganizationScopeReference`-equivalent contract
with narrow reads for scope existence/active status,
ancestor/descendant relationship, exact-scope match, and
permitted-inheritance/delegation result — explicitly "no broad
organization graph returned to domains that need only a boolean
decision." The governing request additionally names six required
access modes (exact-scope, ancestor-scope, descendant-scope, explicitly
delegated cross-scope, temporary supervision, institutional oversight
without implicit data access) and four anti-patterns to prevent
(cross-Land leakage, confused-deputy access, role-name-reuse-as-proof,
implicit hierarchy-position inheritance). ADR-032 places
`Organization`/`OrganizationalRelation` ownership in
`organization-service`; ADR-033 fixes the relationship graph model this
ADR's ancestor/descendant modes rely on.

## Problem

Every trust-boundary precedent this project has established so far
(ADR-027's narrow reads, ADR-031's atomic capability checks, canon
19d.14's `check_atomic_capability`) evaluates a single-service, mostly
non-hierarchical authorization question. Regional scope introduces a
new kind of question — "is scope A permitted to act on/read scope B,"
where A and B may be unrelated, may be in an ancestor/descendant
relationship, or may be connected only by an explicit delegation or
supervision grant — that none of the existing mechanisms answer
directly. Without an explicit default-deny model and a closed,
enumerated set of access modes, a future implementation could plausibly
default to "if it's the same overall platform, scope doesn't matter"
(cross-Land leakage), "if the role name sounds authoritative, trust it"
(role-name-as-proof), or "if I'm the parent, I can obviously see the
child" (implicit inheritance) — each a real, named failure mode the
governing request and HI-24 both require this ADR to close.

## Considered options

- **Option A — implicit inheritance by default:** any ancestor scope
  automatically has full access to every descendant scope's data,
  mirroring a naive "management chain" mental model.
- **Option B — no inheritance at all:** every cross-scope access
  requires an explicit delegation record, with no ancestor/descendant
  shortcut of any kind, even for legitimate oversight needs.
- **Option C — default-deny with six explicit, independently evaluated
  access modes** (exact-scope, ancestor-scope, descendant-scope,
  explicitly delegated cross-scope, temporary supervision, institutional
  oversight without implicit data access), each requiring its own
  explicit grant/policy, evaluated by one atomic, server-side read.

## Decision

**Option C.** `check_regional_scope_access(actor_scope, target_scope,
action_code) -> AccessResult` (owned by `organization-service`, per
ADR-032) is the single, atomic, server-side evaluation point — no
consumer implements its own scope-comparison logic. It defaults to
deny, and grants access only through one of:

1. **Exact-scope access** — `actor_scope == target_scope`.
2. **Ancestor-scope access** — `actor_scope` is a hierarchy-category
   ancestor of `target_scope` (ADR-033) **and** an active
   `OrganizationalInheritancePolicy` (Owner decision, above) grants
   downward access for this specific role/`action_code` — never assumed
   from hierarchy position alone.
3. **Descendant-scope access** — symmetric to 2, likewise never
   assumed by default and likewise gated by an active
   `OrganizationalInheritancePolicy`.
4. **Explicitly delegated cross-scope access** — a distinct,
   time-bounded, purpose-recorded delegation record naming the actor
   or role and the specific permission, independent of hierarchy
   position entirely (a Landesverband may delegate a specific action to
   a named actor in an unrelated Kreisverband, if the delegation record
   says so).
5. **Temporary supervision** — the `temporary_supervision_by`
   cooperation-category relation (ADR-033), always carrying both
   `valid_from` and `valid_until` (open-ended supervision is forbidden;
   default maximum duration 90 days; extension requires a new governed
   decision and its own audit record — Owner decision, above), granting
   the supervising node's authorized actors a narrow, purpose-bound
   window.
6. **Institutional oversight without implicit data access** — an
   `OrganizationalAuthority` (ADR-036) whose `grants_procedural_authority`
   is true grants no read access by title alone; any data access must
   separately satisfy one of modes 1–4.

**All four named anti-patterns are structurally prevented:**

- **Cross-Land data leakage** — closed by default-deny itself: absent
  an explicit mode-2/3/4/5 grant naming the specific cross-Land
  relationship, no access exists.
- **Confused-deputy access** — closed by evaluating `actor_scope`
  against `target_scope` atomically, at the moment of the action,
  every time (mirroring HI-08); a token or role valid for scope A is
  never silently honored against scope B.
- **Role name reuse as proof of authority** — closed by requiring every
  check to resolve through an actual `active` `RoleAssignment`/
  `OrganizationalAuthority` record with a matching scope and validity
  window; a `role_code` string alone never satisfies any of the six
  modes.
- **Implicit inheritance from organization names or hierarchy
  position** — closed by modes 2/3 requiring an active, explicit
  `OrganizationalInheritancePolicy` per role/action; hierarchy position
  alone (being "the parent") is necessary but never sufficient, and no
  consumer may infer an inheritance grant independently of that policy
  (Owner decision, above).

## Rejected options

**Rejected: Option A (implicit inheritance by default).** Directly
contradicts HI-24 and the governing request's explicit
"implicit inheritance from organization names or hierarchy position"
prohibition. It would also recreate, at the regional level, exactly
the "universal admin by virtue of position" pattern HI-11 forbids at
the platform level — a Bund-level actor would trivially become a
de facto universal administrator over every Land/Kreis, merely by
being highest in the hierarchy.

**Rejected: Option B (no inheritance at all).** While maximally safe,
this would make legitimate, narrow oversight functions (e.g. a Land
verifying its own Kreisverbände are correctly configured, an
institutional auditor's scoped review) impossible without an
unreasonably large number of individually-issued delegation records
for entirely routine, foreseeable oversight needs — pushing real
organizations toward workarounds (shared credentials, informal scope
bypasses) that would undermine the isolation this ADR exists to
guarantee. Modes 2/3, gated by an explicit per-role/per-action policy
rather than blanket inheritance, are the narrower, still-safe
alternative.

## Consequences

Every future PACK-08 (and later) consumer needing regional
authorization calls `check_regional_scope_access` rather than
implementing its own comparison — mirroring the project's existing
"one atomic check, many callers" pattern (canon 19d.14).
`OrganizationalInheritancePolicy` (Owner decision, above) becomes a new
canonical, versioned entity owned by `organization-service`, reviewable
and auditable independently of any specific `OrganizationalRelation`,
and gated by the same "consuming domains may restrict further, never
broaden" rule other cross-service policy consumption already follows
project-wide. `RegionalScopeAccessGranted`/
`RegionalScopeAccessRevoked` events (specification section 13) are
emitted for modes 3–5 specifically (the exceptions to default-deny),
not for ordinary exact-scope access, keeping the audit trail focused on
the access that actually needed an explicit decision.

## Privacy impact

`check_regional_scope_access` returns a boolean (and, optionally, a
reason code) — never an `Organization` graph, a role-holder list, or a
member list (mirrors `docs/packs/PACK-08-SPECIFICATION.md` section 12).
Institutional oversight (mode 6) is explicitly data-access-free by
default, preventing an auditor or DPO title from becoming a backdoor
into personal data absent its own separate, purpose-bound grant.

## Security impact

This ADR is the primary mechanism closing GAP-015 (regional isolation
enforcement) and GAP-016 (universal admin prevention) from
`ARCHITECTURE-GAP-REGISTER.md`, and directly implements HI-24. Because
every mode is independently evaluated and default is deny, a
compromised `RoleAssignment`/`OrganizationalAuthority` record scoped to
one node cannot be replayed against an unrelated node's data — the
atomic check re-validates scope match at evaluation time regardless of
what the caller presents.

## Migration impact

None performed by this ADR — `check_regional_scope_access` does not
exist in any service today. A future implementation pack introduces it
fresh; no existing authorization path is modified by this ADR alone.
ADR-035 separately decides how existing `scope_id`/`scope_type`/
`region_code` fields feed (or do not feed) into this new check.

## Testing requirements

A future implementation pack must add: negative tests proving
default-deny across every pair of unrelated scopes; tests proving no
implicit downward/upward inheritance absent an explicit policy; tests
for each of the six modes independently; a test proving a `role_code`
string alone, with no active assignment record, never satisfies any
mode; a test proving an expired or suspended `RoleAssignment`/
`OrganizationalAuthority` (ADR-036, specification section 10) fails
every mode; a test proving institutional oversight (mode 6) grants no
data access absent a separate mode-1–4 grant; a confused-deputy
regression test presenting a token/reference valid for scope A against
an action scoped to B; a test proving a `temporary_supervision_by`
relation with no `valid_until` is rejected at write time; a test proving
a temporary-supervision grant defaults to (and cannot silently exceed)
90 days absent a narrower explicit duration; a test proving an
extension past `valid_until` requires a new governed decision and audit
record rather than mutating the existing grant; and a test proving a
consuming domain's own stricter local rule can further restrict, but
never broaden, what an active `OrganizationalInheritancePolicy` grants.

## Unresolved questions

**OD-8 and OD-10 are closed by the Owner decision, above.** Remaining,
non-blocking:

- Exact reason-code granularity for `AccessResult`'s denial explanation
  (a single `CROSS_SCOPE_ACCESS_DENIED` versus a more granular code per
  mode attempted) — tracked as `docs/packs/PACK-08-OPEN-DECISIONS.md`
  item OD-9.
- Whether a future legal-review round narrows the 90-day default
  maximum temporary-supervision duration for specific organizational
  forms (the Owner decision permits only narrowing, never widening,
  that default) — tracked as a legal-refinement note under OD-10's
  closed entry, not a reopening of the architectural question itself.

## Reversibility

Reversible with cost before code exists. Once real scope-authorization
decisions are made against production-shaped data, narrowing any of
the six modes is a major-version-equivalent change; adding a seventh
mode (should one prove necessary) remains additive, subject to its own
ADR.

## Related canon version

Authored against canon version `0.6.0`. **This ADR performs no canon
edit; `CANON_VERSION` and the canon checksum are unchanged.**
`check_regional_scope_access`, its six access modes, and
`OrganizationalInheritancePolicy` are proposed application-layer/
contract concepts, not yet canon entities. Per the owner decision
recorded above, canon codification of this model (at minimum,
`OrganizationalInheritancePolicy` and the default-deny structural
invariant alongside INV-01 through INV-10) is a **required**, not
optional, step of the future mandatory canon amendment round (ADR-032's
Related canon version section) — no PACK-08 implementation begins
before that round is drafted and accepted.

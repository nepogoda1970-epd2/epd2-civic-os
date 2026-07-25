# ADR-035: Cross-domain scope classification and migration

## Status

`accepted`

## Date

2026-07-25

## Owner decision

Accepted 2026-07-25, in the PACK-08 spec-correction round.
**`RoleAssignment.scope_id` migration rule (closes OD-11 at policy
level):** every existing and future `role_code` must be classified into
exactly one of **six** categories, replacing this ADR's original
two-way (organization-reference / process-local) simplification for
this specific field:

1. **Organization scope** — the `role_code`'s `scope_id` names an
   `Organization`/`OrganizationalUnit` node.
2. **Jurisdiction scope** — the `role_code`'s `scope_id` (or an
   accompanying field) names a legal/geographic jurisdiction, not an
   `Organization`.
3. **CivicSpace scope** — the `role_code`'s `scope_id` names a
   `CivicSpace` (canon 8.2), distinct from both 1 and 2.
4. **Process-local scope** — the `role_code`'s `scope_id` names a
   specific process/decision/challenge instance, unrelated to
   organizational or jurisdictional structure (this ADR's original
   "category 2").
5. **Global/system scope** — the `role_code` is platform-wide by design
   (e.g. a system-level review role with no narrower scope). **A
   global/system classification never implies universal administrative
   access** — HI-11 (no universal administrator) applies to
   global/system-scoped roles exactly as it does to every other role;
   "global scope" describes the role's _scope field_, not a grant of
   authority over every domain.
6. **Invalid/legacy ambiguous** — the `role_code`'s current usage cannot
   be classified into 1–5 without further review. **A `role_code`
   classified here is migration-blocked**: no future implementation may
   wire it into `check_regional_scope_access` (ADR-034) or any
   organization-scope-aware logic until it is reclassified into 1–5 by
   its own explicit review.

**No silent reinterpretation is allowed** for any `role_code`, in any
category. **Implementation must include a complete `role_code`-keyed
migration table, populated and reviewed, before any data migration
touching `RoleAssignment.scope_id` begins** — restated from this ADR's
original "no automated bulk rewrite" principle, now stated specifically
as a precondition, not merely a general caution.

**This closes OD-11 "at policy level" only**: the six-category rule,
the migration-blocked treatment of ambiguous roles, and the
global/system non-privilege rule are now settled and binding. The
actual, concrete enumeration of every current `role_code` value against
these six categories remains a required pre-implementation task
(`docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-11, updated), not an
open architectural question.

**This acceptance does not authorize implementation.** The canon
amendment required before implementation (ADR-032/033/034's own Related
canon version sections) also covers, where relevant, any
`RoleAssignment.scope_id` `role_code` reclassified into category 1
(organization scope) or 3 (CivicSpace scope) above, since those
categories depend on canon concepts (`Organization`, `CivicSpace`) whose
ownership/authorization model this ADR's sibling ADRs propose.
`CANON_VERSION` and the canon checksum are unchanged by this correction
round.

## Context

Six services already carry generic, pre-PACK-08 fields whose
relationship to the new `Organization`/`OrganizationalScope` model
(ADR-032/034) is not yet decided: `Membership.organization_id` and
`Membership.region_code` (canon 8.3, `membership-service`);
`RoleAssignment.scope_id` (canon 8.4, `governance-service`);
`ProcessEligibilityPolicy.jurisdiction`/`scope_type`/`scope_id`
(canon 19d, `eligibility-service`, ADR-028);
`PartyMembershipEligibilityPolicy.scope_type`/`scope_id`
(`membership-service`); `ParticipationCredential.scope_type`/`scope_id`
(`credential-service`); `Delegation.scope_type`/`scope_id`
(`delegation-service`); atomic-capability-check `required_scope_type`/
`required_scope_id` literals in `voting-service` and
`initiative-service`; and `transparency-service`'s
`GENERALIZE_TO_ROLE_SCOPE` redaction-transformation enum value.
`docs/handover/PACK-07-SPEC-FINAL.md` section 11 already establishes
that every one of these fields is, today, "opaque, caller-supplied ...
never dereferenced" — a deliberate, honest placeholder pending PACK-08.
`PACK-08-PROPOSAL.md` section 3.4 requires this inventory and a
per-field ADR decision among "becomes an organization reference,"
"remains a process-local opaque scope," "represents legal jurisdiction
rather than organization," or "requires a compatibility field/event
migration" — with an explicit prohibition on "automated bulk rewrite ...
without a reviewed mapping."

## Problem

Six fields, five services, and at least three genuinely different
underlying meanings ("which organizational node," "which legal/
geographic jurisdiction," "which specific process instance this
capability check applies to") are currently indistinguishable by field
name alone (`scope_id`/`scope_type` appears in all three categories).
Without an explicit, field-by-field classification, a future
implementation could plausibly "wire up" `organization-service` by
reinterpreting some of these fields incorrectly — for instance,
treating `ProcessEligibilityPolicy.scope_id` (today, structurally
opaque per ADR-028) as automatically meaning "an `Organization` node,"
which would silently and incorrectly bind every process-eligibility
policy to the organizational hierarchy even where the policy is
genuinely process-local and organization-independent. The governing
request's own instruction — "Do not silently reinterpret existing
fields" — is the exact discipline this ADR exists to enforce.

## Considered options

- **Option A — reinterpret every `scope_id`/`region_code`/`organization_id`
  field as an `Organization` reference automatically,** on the theory
  that "scope" always eventually means organizational scope.
- **Option B — leave every existing field untouched and require all
  organizational-scope consumers to add a wholly new, separate field,**
  never touching or classifying the existing ones.
- **Option C — classify each field individually, by its actual current
  behavior and consumers, into one of four categories (organization
  reference / process-local opaque scope / legal jurisdiction /
  needs compatibility strategy), publish the classification as a
  migration matrix, and require any actual field-level change to be
  additive and reviewed, never a bulk rewrite.**

## Decision

**Option C.** The complete, field-by-field classification is published
as `docs/packs/PACK-08-MIGRATION-MATRIX.md` (this ADR's primary
deliverable); the classification categories and their meaning are fixed
here:

1. **Becomes an organization reference.** The field already means "an
   `Organization` node" in intent, and gains a real referent for the
   first time once `organization-service` exists. Applies to:
   `Membership.organization_id` (canon 8.3).
2. **Remains a process-local, opaque scope.** The field means "the
   specific object instance this capability/policy check applies to,"
   unrelated to organizational hierarchy, and is not reclassified.
   Applies to: `ParticipationCredential.scope_type`/`scope_id`
   (credential-service); `Delegation.scope_type`/`scope_id`
   (delegation-service); `voting-service`/`initiative-service`'s
   `required_scope_type`/`required_scope_id` capability-check literals;
   `PartyMembershipEligibilityPolicy.scope_type`/`scope_id`
   (membership-service); `ProcessEligibilityPolicy.scope_type`/`scope_id`
   (eligibility-service, ADR-028 — "structure only," unchanged).
3. **Represents legal jurisdiction, not organization.** The field means
   a legal/geographic fact external to this platform's own
   organizational structure. Applies to:
   `ProcessEligibilityPolicy.jurisdiction` (eligibility-service,
   ADR-028).
4. **Requires a compatibility strategy.** The field's current meaning
   is ambiguous, partially organizational, or would break existing
   consumers if reinterpreted outright, and needs an additive
   transition path rather than a direct reclassification. Applies to:
   `Membership.region_code` (canon 8.3); `RoleAssignment.scope_id`
   (canon 8.4 — see below, classification is per-role-code, not
   universal).

**`RoleAssignment.scope_id`'s classification is deliberately
per-`role_code`, not universal, and is now governed by the six-category
scheme fixed in the "Owner decision" section above, not by this ADR's
four top-level categories directly.** The four categories immediately
above continue to govern the _other five_ fields in scope for this ADR
(`Membership.organization_id`, `Membership.region_code`,
`ProcessEligibilityPolicy.jurisdiction`/`scope_type`/`scope_id`, and the
process-local `scope_type`/`scope_id` pairs on credential-service,
delegation-service, voting-service, initiative-service, and
membership-service's `PartyMembershipEligibilityPolicy`) exactly as
originally decided. `RoleAssignment.scope_id` alone is carved out as
category 4 ("requires a compatibility strategy") and, within that
carve-out, is further split into the six sub-categories the Owner
decision fixes above (organization scope / jurisdiction scope /
CivicSpace scope / process-local scope / global-system scope /
invalid-legacy-ambiguous) — a finer partition than the original
two-way (organization-reference / process-local) split this ADR first
proposed for this field, superseded by the Owner decision. Today,
`governance-service`'s `scope_covers(role_scope_id, subject_scope_id)`
(its own generic containment helper) is used across multiple, unrelated
role kinds. A role whose `role_code` names an organizationally-scoped
function (e.g. a future `organizational_administrator` `RoleAssignment`,
should one be modeled there rather than as `OrganizationalAuthority`,
ADR-036) is classified into the Owner decision's category 1
(organization scope); a role whose `role_code` names a process-local
function (e.g. a technical-challenge reviewer role scoped to one
`GovernanceDecision`) is classified into category 4 (process-local
scope) there. No single migration statement covers
`RoleAssignment.scope_id` as a whole — this ADR requires a **decision
table keyed by `role_code`**, classifying each entry into one of the
Owner decision's six categories, not a blanket field reinterpretation,
published as part of the migration matrix
(`docs/packs/PACK-08-MIGRATION-MATRIX.md` section 2.3).

**`transparency-service`'s `GENERALIZE_TO_ROLE_SCOPE`** is explicitly
flagged as a **false cognate** — a redaction-generalization strategy
name (statistical disclosure control, unrelated to organizational
scope) that merely contains the substring "scope." No classification
or migration applies; the migration matrix records this purely to
prevent a future implementer from conflating the two because of the
shared word.

**No automated bulk rewrite occurs.** Every category-4 field's actual
transition (e.g. `Membership.region_code`'s eventual relationship to a
new `OrganizationalScope` reference) is deferred to a future
implementation pack, which must add the new field additively, preserve
the old field through a deprecation window, and never reinterpret the
existing field's stored values in place.

## Rejected options

**Rejected: Option A (blanket reinterpretation).** Directly
contradicted by the governing request's "do not silently reinterpret
existing fields" instruction and by concrete evidence: `ADR-028`
explicitly designed `ProcessEligibilityPolicy.scope_type`/`scope_id` as
"structure only," deliberately deferring exactly this decision to
PACK-08 rather than assuming an organizational meaning prematurely —
reinterpreting it now, unreviewed, would retroactively violate that
ADR's own stated intent and could silently and incorrectly bind
process-local eligibility policies to specific organizational nodes
that were never part of the original design.

**Rejected: Option B (never touch or classify).** Would leave the six
fields' actual relationship to the new organizational domain
permanently undocumented, forcing every future consumer to
independently re-derive (or guess) what each field means relative to
`Organization` — precisely the ambiguity this ADR exists to resolve.
Publishing a classification costs nothing today (no field is actually
changed) and materially de-risks every later implementation pack that
would otherwise face this question without guidance.

## Consequences

A future implementation pack consults `docs/packs/PACK-08-MIGRATION-MATRIX.md`
before writing any code that touches these six fields; category-1 and
category-4 fields require additive schema changes (new nullable
fields, never renamed/repurposed existing ones); category-2 and
category-3 fields require no change at all — their current meaning is
confirmed correct and stable. The `RoleAssignment.scope_id`
per-`role_code` decision table becomes part of `organization-service`'s
own future integration work with `governance-service` (a narrow read
edge, per ADR-032), not a `governance-service`-internal change.

## Privacy impact

No new personal data is introduced by classification alone (no code
changes accompany this ADR). The eventual category-1 migration
(`Membership.organization_id` gaining a real referent) does not by
itself expose any new fact externally — `Membership`'s existing
restricted-by-default rule (ADR-028 item 3) is unaffected; only
`membership-service`'s own internal ability to validate the reference
changes, once implemented.

## Security impact

Preventing silent reinterpretation directly prevents a subtle
authorization-bypass class of bug: if `ProcessEligibilityPolicy.scope_id`
were silently treated as an `Organization` reference without review,
a future `check_regional_scope_access` (ADR-034) call built on a
mistaken assumption about what that field means could grant or deny
access based on the wrong criterion entirely, without any test
necessarily catching it (the field would still be a syntactically
valid UUID either way). The classification, once published, is the
guardrail future code review checks new usage against.

## Migration impact

This is the ADR whose entire subject is migration impact — restated,
concisely: category 1 (`Membership.organization_id`) requires no schema
change, only a future behavioral change (real validation once
`organization-service` exists); category 4 fields
(`Membership.region_code`, per-`role_code` `RoleAssignment.scope_id`
entries) require additive new fields alongside preserved legacy fields,
never in-place reinterpretation; categories 2 and 3 require no change.
Every existing event payload schema carrying any of these fields
(e.g. `membership-activated-payload.v1.schema.json`,
`contracts/schemas/membership.schema.json`) is unmodified by this ADR
and remains unmodified until a future implementation pack makes the
specific additive change its own category requires, under its own
review and its own version-consistency verification
(`scripts/verify_versions.py`).

## Testing requirements

A future implementation pack must add: a compatibility test asserting
every category-2/3 field's existing schema validates unchanged; a test
asserting a category-1/4 field's new additive companion field is
nullable and does not alter existing valid instances' validity; a
`role_code`-keyed parametrized test enumerating the
`RoleAssignment.scope_id` decision table and asserting each entry's
classification is actually exercised; a test asserting that every
`role_code` classified as category 6 (invalid/legacy ambiguous) in the
Owner decision's six-category scheme is rejected if any code path
attempts to wire it into `check_regional_scope_access` (ADR-034) or any
other organization-scope-aware logic, proving the migration-blocked
rule is enforced and not merely documented; a test asserting that a
category-5 (global/system scope) `role_code` grants no broader access
than its own explicitly-defined scope — i.e. that no code path treats
"global scope" as "universal administrative access" (HI-11); and a
static test (mirroring
`tests/repository/test_pack07_duplicated_logic_parity.py`'s AST-based
style) confirming no source file introduces a new dereference of a
category-2/3 field as though it were an `Organization` reference.

## Unresolved questions

- **OD-11 is closed at policy level by the Owner decision, above**: the
  six-category classification scheme, the migration-blocked treatment
  of category-6 (invalid/legacy ambiguous) `role_code` values, and the
  global/system non-privilege rule are settled and binding. What
  remains open is not the architecture but the enumeration: the exact
  `role_code`-keyed decision table for `RoleAssignment.scope_id` is not
  yet fully populated by this ADR, pending an inventory of every
  currently-defined `role_code` value across `governance-service`'s own
  tests/fixtures, classified against the six fixed categories. This
  remaining enumeration work is a required pre-implementation task,
  tracked as `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-11
  (updated).
- Whether `Membership.region_code`'s eventual deprecation window has a
  fixed end date/version, or remains indefinitely dual-written pending
  a separate future ADR — tracked as OD-12.
- Whether a future canon edit should rename `RoleAssignment.scope_id`
  to something more specific once its organizational vs. process-local
  split is fully resolved, or whether the single field name persists
  with category-specific documentation only — tracked as OD-13.

## Reversibility

Reversible at essentially no cost today — this ADR changes no field,
no schema, and no behavior. Once a future implementation pack acts on
this classification (adding category-1/4 companion fields), reversing
that specific addition becomes a minor, additive-removal change, not a
major one, since nothing existing was altered in place.

## Related canon version

Authored against canon version `0.6.0`. `CANON_VERSION` and the canon
checksum are unchanged by this ADR and by the PACK-08 spec-correction
round that accepted it.

**A canon amendment is now REQUIRED — not conditional — before any
implementation that acts on this ADR's classification decisions.** This
ADR's classification work is, by itself, non-invasive: canon 8.3/8.4/19d's
existing field definitions (`organization_id`, `region_code`, `scope_id`,
`jurisdiction`) are read and classified here, not amended, and no field
is renamed, added, or removed by this ADR alone. However, per the Owner
decision recorded in `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-18
and restated in this ADR's own "Owner decision" section above, canon
amendment is required wherever this ADR's classification actually
depends on, or feeds into, the canon-relevant concepts PACK-08
introduces (`Organization`, `CivicSpace`, `OrganizationalRelation`,
`OrganizationalAuthority`, `OrganizationalScope`, regional scope
authorization, institutional authority lifecycle, reorganization and
successor invariants) — concretely, any `role_code` this ADR's
migration table (once populated) classifies into category 1
(organization scope) or category 3 (CivicSpace scope) is only
implementable once a future, separate canon ADR proposing the actual
canon 8.x additions/amendments for those concepts has been prepared and
accepted, and `CANON_VERSION` is bumped accordingly. Category 2, 4, and
5 classifications (jurisdiction, process-local, global/system) do not
themselves depend on new canon concepts and are not blocked by the
canon amendment on that basis alone — though PACK-08 implementation as
a whole remains blocked pending the canon amendment regardless, per the
Owner decision above and per ADR-032/033/034's own identical
restatement of that same gate.

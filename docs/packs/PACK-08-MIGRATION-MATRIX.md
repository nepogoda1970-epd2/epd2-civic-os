# CLAUDE-PACK-08 — Cross-domain scope classification and migration matrix

Companion deliverable to ADR-035
(`docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md`).
This document is the complete, field-by-field classification the
governing request's item 9 requires. **No field, schema, event, or API
listed below is changed by this document or by ADR-035.** Every entry
records a decision for a future implementation pack to execute,
additively, under its own review.

## 1. How to read this matrix

Each row states: the field and its owning service; its **current
meaning**, verified against the actual source in this repository (not
assumed); its **target meaning** once PACK-08's organization domain
exists; its **canonical owner** going forward; its **compatibility
strategy**; and its **event impact**, **API impact**, and **test
impact**. The classification categories are fixed by ADR-035:

1. Becomes an organization reference.
2. Remains a process-local, opaque scope.
3. Represents legal jurisdiction, not organization.
4. Requires a compatibility strategy (additive companion field).

A fifth, informal marker, **false cognate**, flags a name collision
that is not actually the same concept at all and requires no
classification.

**Exception — `RoleAssignment.scope_id` (section 2.3):** this single
field is governed by its own, finer, **six-category** scheme fixed by
an owner decision in the correction round (organization scope /
jurisdiction scope / CivicSpace scope / process-local scope /
global-system scope / invalid-legacy-ambiguous), classified
per-`role_code`, not by the four top-level categories above. This
finer sub-scheme applies to `RoleAssignment.scope_id` specifically; the
four-category scheme above continues to govern every other field in
this matrix.

## 2. Matrix

### 2.1 `Membership.organization_id` (canon 8.3, `membership-service`)

- **Current meaning:** an opaque UUID, written by `membership-service`,
  never dereferenced or validated against any other service
  (`docs/handover/PACK-07-SPEC-FINAL.md` section 11).
- **Target meaning:** a real reference to an `Organization` node owned
  by `organization-service` (ADR-032).
- **Classification:** 1 — becomes an organization reference.
- **Canonical owner going forward:** `organization-service` owns the
  referent; `membership-service` continues to own the field itself
  (the foreign-key-shaped reference lives on `Membership`, unchanged).
- **Compatibility strategy:** none needed — the field's shape (a UUID)
  does not change; only its _validation behavior_ changes, once a
  future implementation pack wires a narrow
  `organization-service` read into `membership-service`'s own
  application layer to confirm the referenced `Organization` exists and
  is active before accepting a `MembershipApplication` naming it.
- **Event impact:** `membership-application-submitted-payload.v1`,
  `membership-activated-payload.v1`, and `membership.schema.json` all
  already carry `organization_id` unchanged; no payload schema edit is
  required.
- **API impact:** none — `contracts/openapi/pack-07.yaml`'s existing
  operations are unaffected; a future implementation may add a new,
  separate `organization-service` read operation, not a change to any
  existing PACK-07 operation.
- **Test impact:** a future implementation pack adds a negative test
  (submitting a `MembershipApplication` naming a nonexistent/dissolved
  `Organization` is rejected) to `services/membership-service/tests/`;
  no existing test changes.

### 2.2 `Membership.region_code` (canon 8.3, `membership-service`)

- **Current meaning:** an open, free-form string field on `Membership`,
  carrying no validated relationship to any organizational or
  jurisdictional entity today.
- **Target meaning:** ambiguous by design today — could mean "the
  member's own regional organizational unit" (category 1-adjacent) or
  "a legal/geographic region the member resides in" (category 3-adjacent);
  the repository's current usage does not disambiguate, and no single
  reinterpretation is safe to assume.
- **Classification:** 4 — requires a compatibility strategy.
- **Canonical owner going forward:** unchanged — `membership-service`
  continues to own `region_code` itself as a legacy field.
- **Compatibility strategy:** a future implementation pack adds a new,
  additive, nullable `organizational_scope_reference` field to
  `Membership` (or an equivalent read model) **alongside** `region_code`,
  never replacing it, through a deprecation window whose end condition
  is an explicit future decision (`docs/packs/PACK-08-OPEN-DECISIONS.md`
  item OD-12) — not fixed by this document. `region_code`'s existing
  stored values are never reinterpreted, rewritten, or backfilled
  automatically.
- **Event impact:** `membership-activated-payload.v1.schema.json` and
  related event schemas keep `region_code` unchanged; a future
  implementation adds the new field as an additive, optional payload
  field only when the compatibility strategy above is actually
  executed.
- **API impact:** none to existing operations; a future new field is
  additive per canon section 25's minor-version discipline.
- **Test impact:** a future implementation pack adds a schema
  backward-compatibility test proving existing `Membership` instances
  (with only `region_code`, no new field) still validate.

### 2.3 `RoleAssignment.scope_id` (canon 8.4, `governance-service`)

**Owner decision (correction round, 2026-07-25), superseding this
section's original two-way (organization-reference / process-local)
classification:** every existing and future `role_code` on
`RoleAssignment.scope_id` must be classified into exactly one of
**six** categories, not the top-level four-category scheme sections
2.1–2.11 otherwise use for the other fields in this matrix:

1. **Organization scope** — the `role_code`'s `scope_id` names an
   `Organization`/`OrganizationalUnit` node.
2. **Jurisdiction scope** — the `role_code`'s `scope_id` (or an
   accompanying field) names a legal/geographic jurisdiction, not an
   `Organization`.
3. **CivicSpace scope** — the `role_code`'s `scope_id` names a
   `CivicSpace` (canon 8.2), distinct from both 1 and 2.
4. **Process-local scope** — the `role_code`'s `scope_id` names a
   specific process/decision/challenge instance, unrelated to
   organizational or jurisdictional structure.
5. **Global/system scope** — the `role_code` is platform-wide by
   design (e.g. a system-level review role with no narrower scope).
   **A global/system classification never implies universal
   administrative access** — HI-11 (no universal administrator)
   applies to global/system-scoped roles exactly as it does to every
   other role.
6. **Invalid/legacy ambiguous** — the `role_code`'s current usage
   cannot be classified into 1–5 without further review. **A
   `role_code` classified here is migration-blocked**: no future
   implementation may wire it into `check_regional_scope_access`
   (ADR-034) or any organization-scope-aware logic until it is
   reclassified into 1–5 by its own explicit review.

- **Current meaning:** a generic `UUID` scope reference, consumed by
  `governance-service`'s own `scope_covers(role_scope_id, subject_scope_id)`
  helper, across every `role_code` this service defines — the field
  itself carries no information about _what kind_ of scope it names.
- **Target meaning:** depends on the specific `role_code` — some
  existing/future roles are genuinely organizationally scoped
  (category 1); some may reference a `CivicSpace` (category 3); some
  are process-local (category 4, e.g. scoped to one
  `GovernanceDecision` or `TechnicalChallenge`); some are platform-wide
  by design (category 5); and any whose current usage cannot yet be
  classified without further review are held in category 6, migration-
  blocked, until reclassified.
- **Classification:** per-`role_code`, not universal, against the six
  categories above — see ADR-035's own "Owner decision" section. **No
  silent reinterpretation is allowed for any `role_code`, in any
  category.** A specific `role_code`-keyed table is **not** fully
  enumerated by this document (tracked as
  `docs/packs/PACK-08-OPEN-DECISIONS.md` item OD-11, closed at policy
  level, enumeration still open) pending an inventory of every
  `role_code` value currently defined in `governance-service`'s own
  tests/fixtures. **Implementation must include this complete
  `role_code`-keyed migration table, populated and reviewed, before any
  data migration touching `RoleAssignment.scope_id` begins** — a
  precondition, not merely a general caution.
- **Canonical owner going forward:** `governance-service` continues to
  own `RoleAssignment` and `scope_id` itself; where a specific
  `role_code`'s `scope_id` is classified as category 1 (organization
  scope) or category 3 (CivicSpace scope), `organization-service` owns
  the referent, read via a narrow edge (ADR-032), never a write edge.
  Category-5 (global/system) `role_code` values remain owned entirely
  by `governance-service`, with no `organization-service` involvement
  at all, and never imply universal administrative access regardless
  of their platform-wide scope.
- **Compatibility strategy:** none needed at the field level — `scope_id`
  remains a single `UUID` field regardless of classification; only the
  _validation and interpretation_ differs by `role_code`, applied at
  the application layer, not the schema layer. Category-6 (invalid/
  legacy ambiguous) `role_code` values receive no compatibility
  strategy at all until reclassified — they are migration-blocked, not
  migrated under a placeholder strategy.
- **Event impact:** none — `governance-role-assignment-payload.v1.schema.json`
  is unaffected; `scope_id`'s type and presence are unchanged regardless
  of which category applies to a given `role_code`.
- **API impact:** none to existing operations.
- **Test impact:** a future implementation pack adds the `role_code`-keyed
  decision table (OD-11) as a parametrized test enumerating every
  `role_code` value and its classification against all six categories;
  a negative test proving a category-1/3 `role_code`'s `scope_id` is
  validated against a real `Organization`/`CivicSpace` while a
  category-4 `role_code`'s is not; a test proving a category-6
  `role_code` is rejected by any code path that attempts to wire it
  into `check_regional_scope_access` or other organization-scope-aware
  logic; and a test proving a category-5 `role_code` grants no broader
  access than its own explicitly-defined scope (i.e. "global scope"
  never becomes "universal administrative access," HI-11).

### 2.4 `ProcessEligibilityPolicy.jurisdiction` (canon 19d, `eligibility-service`, ADR-028)

- **Current meaning:** an open string naming a legal/geographic
  jurisdiction (e.g. a country or supranational-body code), explicitly
  documented by ADR-028 item 6 as "structure only" and never
  dereferenced.
- **Target meaning:** unchanged — a legal/geographic jurisdiction fact,
  explicitly and permanently distinct from any `Organization` reference
  (specification section 2/4).
- **Classification:** 3 — represents legal jurisdiction, not
  organization.
- **Canonical owner going forward:** unchanged — `eligibility-service`.
- **Compatibility strategy:** none — no change of any kind. This entry
  exists in the matrix specifically to record the negative decision
  ("this is not becoming an organization reference") so a future
  implementer does not assume otherwise merely because PACK-08 exists.
- **Event impact:** none.
- **API impact:** none.
- **Test impact:** a future implementation pack may add a regression
  test asserting `jurisdiction` is never used as an
  `organization-service` lookup key, to guard against exactly the
  silent-reinterpretation risk this matrix exists to prevent.

### 2.5 `ProcessEligibilityPolicy.scope_type` / `scope_id` (canon 19d, `eligibility-service`, ADR-028)

- **Current meaning:** open string / opaque UUID, explicitly "structure
  only" per ADR-028 (section 17/29 reference), never dereferenced.
- **Target meaning:** unchanged for now — remains process-local. A
  future process type that is genuinely organization-bound may
  _additionally_ carry a distinct `OrganizationalScope` reference field
  (specification section 4), but `scope_type`/`scope_id` themselves are
  not reclassified.
- **Classification:** 2 — remains a process-local, opaque scope.
- **Canonical owner going forward:** unchanged — `eligibility-service`.
- **Compatibility strategy:** none needed for these two fields; if a
  future implementation pack adds an organization-bound process type,
  it adds a new, separate, additive field rather than reinterpreting
  these two.
- **Event impact / API impact:** none.
- **Test impact:** none beyond the general false-reinterpretation
  regression test noted in 2.4.

### 2.6 `PartyMembershipEligibilityPolicy.scope_type` / `scope_id` (`membership-service`)

- **Current meaning, target meaning, classification, strategy, impacts:**
  identical reasoning to 2.5, applied to `membership-service`'s own
  policy entity. Classification: 2 — remains process-local.

### 2.7 `ParticipationCredential.scope_type` / `scope_id` (`credential-service`)

- **Current meaning:** the specific process/ballot/action instance a
  credential is scoped to validate against (canon 10.1).
- **Target meaning:** unchanged.
- **Classification:** 2 — remains a process-local, opaque scope.
- **Canonical owner / strategy / impacts:** unchanged; no migration.

### 2.8 `Delegation.scope_type` / `scope_id` (`delegation-service`)

- **Current meaning:** the specific process instance a delegation
  applies to (canon 16.1).
- **Target meaning:** unchanged.
- **Classification:** 2 — remains a process-local, opaque scope.
- **Canonical owner / strategy / impacts:** unchanged; no migration.

### 2.9 `voting-service`/`initiative-service` `required_scope_type` / `required_scope_id` (atomic capability check literals)

- **Current meaning:** the specific object instance (a ballot, an
  initiative) an atomic capability check validates against — an
  application-layer literal, not a stored entity field.
- **Target meaning:** unchanged.
- **Classification:** 2 — remains process-local.
- **Canonical owner / strategy / impacts:** unchanged; no migration.

### 2.10 `transparency-service`'s `GENERALIZE_TO_ROLE_SCOPE` (`DisclosurePolicy` redaction-transformation enum value)

- **Current meaning:** a statistical-disclosure-control
  redaction-generalization strategy name (canon 19a.3) — "generalize
  this field's value to the level of the subject's role/scope
  category" — entirely unrelated to organizational or regional scope.
- **Target meaning:** unchanged.
- **Classification:** **false cognate** — no classification category
  applies; flagged here purely so a future implementer does not
  conflate this enum value with `OrganizationalScope` merely because
  both contain the word "scope."
- **Canonical owner / strategy / impacts:** unchanged; no migration.

### 2.11 `civic_space_id` (referenced by the governing request; no such field exists in the repository today)

- **Current meaning:** none — this exact field name does not appear
  anywhere in the repository (verified by repository-wide search).
  Canon 8.2's own `CivicSpace` primary key is `space_id`.
- **Target meaning:** a naming-convention recommendation, not a
  migration: any future foreign-key field elsewhere that references a
  `CivicSpace` should be named `civic_space_id` explicitly, for clarity
  against the generic `scope_id` pattern already overloaded across
  section 2.3–2.9's entries; `CivicSpace.space_id` itself is not
  renamed.
- **Classification:** naming clarification, not a migration category.
- **Canonical owner / strategy / impacts:** none — no existing field
  changes.

## 3. Summary table

| Field                                                                 | Service                            | Classification                                                                                                   | Change required now                                                         |
| --------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `Membership.organization_id`                                          | membership-service                 | 1 — becomes organization reference                                                                               | None (behavioral only, future)                                              |
| `Membership.region_code`                                              | membership-service                 | 4 — compatibility strategy                                                                                       | None (future additive field)                                                |
| `RoleAssignment.scope_id`                                             | governance-service                 | per-`role_code`, six-category scheme (org/jurisdiction/CivicSpace/process-local/global-system/invalid-ambiguous) | None (future per-role decision table; category-6 entries migration-blocked) |
| `ProcessEligibilityPolicy.jurisdiction`                               | eligibility-service                | 3 — legal jurisdiction                                                                                           | None                                                                        |
| `ProcessEligibilityPolicy.scope_type`/`scope_id`                      | eligibility-service                | 2 — process-local                                                                                                | None                                                                        |
| `PartyMembershipEligibilityPolicy.scope_type`/`scope_id`              | membership-service                 | 2 — process-local                                                                                                | None                                                                        |
| `ParticipationCredential.scope_type`/`scope_id`                       | credential-service                 | 2 — process-local                                                                                                | None                                                                        |
| `Delegation.scope_type`/`scope_id`                                    | delegation-service                 | 2 — process-local                                                                                                | None                                                                        |
| `required_scope_type`/`required_scope_id` (capability-check literals) | voting-service, initiative-service | 2 — process-local                                                                                                | None                                                                        |
| `GENERALIZE_TO_ROLE_SCOPE`                                            | transparency-service               | false cognate                                                                                                    | None                                                                        |
| `civic_space_id` (naming convention only)                             | n/a — no field exists              | naming clarification                                                                                             | None                                                                        |

**No automated bulk rewrite occurs as a result of this document.**
Every "None" above means literally none — this matrix records
decisions for a future implementation pack to execute individually,
under its own review, not a batch of changes this document performs.

## 4. Cross-reference

- Classification method and rationale: `docs/adr/ADR-035-cross-domain-scope-classification-and-migration.md`.
- Concept-separation rule these classifications enforce:
  `docs/packs/PACK-08-SPECIFICATION.md` sections 2 and 4.
- Open, unresolved items surfaced by this matrix:
  `docs/packs/PACK-08-OPEN-DECISIONS.md` items OD-11, OD-12, OD-13.

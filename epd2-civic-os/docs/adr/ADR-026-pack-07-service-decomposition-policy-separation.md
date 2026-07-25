# ADR-026: PACK-07 service decomposition and participant/party-membership policy separation

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3) and the three
consistency corrections applied to it. No further amendment: the
service-decomposition and policy-separation content below — the
`eligibility-service`/`membership-service` split, `ParticipantEligibilityPolicy`
vs. `PartyMembershipEligibilityPolicy` separation, and `ParticipationRightsProfile`'s
internal/non-authoritative characterization (fifth amendment, item 1) —
is accepted verbatim. Canon implementation follows in a separate,
dedicated canon-edit task per canon section 26; this acceptance alone
authorizes no service code (`docs/review/PACK-07-OWNER-DECISIONS.md`
section 1).

## Canon implementation (2026-07-25, follow-on task)

Recorded in canon 0.6.0, new section 19d.1 (service/ownership overview)
and 19d.13 (`ParticipationRightsProfile`, internal/non-authoritative).
`RoleAssignment` (8.4), `Membership` (8.3), and every other existing
canon entity are unchanged by this ADR's content.

## Context

`docs/handover/PACK-07-SPEC.md` section 18 (Design decision D5) proposed
one new service, `membership-service`, owning `Membership` (canon 8.3),
both new Policy entities (`ParticipantEligibilityPolicy`,
`PartyMembershipEligibilityPolicy`), `AffiliationDeclaration`,
`ConflictAssessment`, and the derived `ParticipationRightsProfile` read
model — with the participant/party-member separation (section 6, Design
decision D1) enforced only at the Python-module level inside that one
service, not at the physical-service boundary.

The project owner has reviewed this proposal and requires a different
decomposition: general platform-participation eligibility must be owned
by the **existing** `eligibility-service` (canon 5.2, 9.1–9.3, already
implemented since PACK-02), not folded into a new service alongside
party-specific machinery. Only party membership itself — application,
continuing-membership evaluation, affiliation, and conflict handling —
belongs to the new `membership-service`.

The project owner has since issued a fifth, mandatory amendment,
incorporated directly into this ADR's own item 3, below:
`ParticipationRightsProfile` must be characterized explicitly as an
**internal, non-authoritative** derived view, never itself a mechanism
any service or frontend may rely on to grant or deny an action. The
corresponding enforcement-boundary rule (atomic capability checks or
single-purpose scoped capability tokens as the **only** permitted
enforcement mechanism) is fixed in full by ADR-027, not restated here.

## Problem

Without this amendment, `membership-service` would become the sole
owner of both the general participant-eligibility policy and the
party-specific policy, which risks exactly the kind of silent
conflation item 4 of the originating instruction already warned against
at the rule-content level (section 6 of the specification) — except
this time at the service-ownership level: a single service evaluating
both dimensions can too easily let party-specific logic leak into a
participant-facing evaluation path, or vice versa, with no service
boundary forcing the two apart. It would also mean the one service
already responsible for general eligibility evaluation since PACK-02
(`eligibility-service`, owning `EligibilityRule`/`EligibilityDecision`/
`EligibilitySnapshot`) would have no relationship at all to this pack's
new `ParticipantEligibilityPolicy` entity, even though both concern the
same subject: whether a confirmed participant may take part in a given
process.

## Considered options

- Option A (the specification's own original recommendation, section 18)
  — one new service, `membership-service`, owning `Membership` and all
  four new entities, with participant/party-member separation enforced
  only at the module level.
- Option B (the project owner's decision) — split ownership across the
  existing `eligibility-service` (general participation eligibility) and
  a new `membership-service` (party membership, affiliation, conflict).
- Option C — fold everything into `eligibility-service` itself, treating
  party membership as one more eligibility dimension. Not seriously
  considered: `Membership` (canon 8.3) already has a canon-declared
  owner, "Membership Service", distinct from `EligibilityRule`'s
  "Eligibility Engine" — collapsing the two would contradict canon's own
  existing ownership matrix (section 22) without any canon edit
  authorizing it.

## Decision

**Option B**, per the project owner's explicit instruction.

### 1. `eligibility-service` (existing service, extended) owns:

- **`ParticipantEligibilityPolicy`** (new, proposed) — the versioned,
  governance-adopted policy record governing general platform
  participation (section 7's `age_thresholds`, section 8's citizenship/
  residence conditions, as applied to participant-level actions only:
  `account_registration`, `public_participation`, `discussion`,
  `initiative_creation`, `initiative_support`, `civic_consultation`).
- **`ProcessEligibilityPolicy`** (new, proposed — amendment, added by
  ADR-028 item 6) — the versioned policy entity parameterizing every
  electoral/process-eligibility evaluation
  (`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
  `party_internal_voting_eligibility_met`,
  `party_office_candidacy_eligibility_met`) by process type,
  jurisdiction, territorial scope, effective date, and policy version —
  see ADR-028 for the full field/process-taxonomy definition and
  ADR-027 for the corresponding cross-service read boundary.
  `eligibility-service` is the sole computing party for all four
  electoral/process-eligibility claims, including the two party-internal
  ones, which it resolves by combining `ProcessEligibilityPolicy` with
  the existing `eligibility-service → membership-service` narrow read
  (item 2, below) — `membership-service` itself never computes an
  electoral-eligibility claim.
- **Evaluation of general platform participation rights** — the
  service's own, already-existing `EligibilityDecision`-producing
  machinery (canon 9.2, unchanged) is extended to consult
  `ParticipantEligibilityPolicy` as one of its `rule_version` sources,
  alongside the existing `EligibilityRule` (canon 9.1) mechanism, rather
  than introducing a second, parallel evaluation path.
- **Participant-side capability derivation** — the participant-facing
  half of `ParticipationRightsProfile` (`can_read_public`,
  `can_discuss`, `can_create_initiative`, `can_support_initiative`,
  `can_join_civic_consultation`) is computed by `eligibility-service`
  itself, from its own `ParticipantEligibilityPolicy` plus the existing
  `EligibilityDecision`/`EligibilitySnapshot` state.

### 2. `membership-service` (new service) owns:

- **`Membership`** (canon 8.3, implemented for the first time by this
  pack, `membership_type = party` scoped) — unchanged from the
  specification's own section 3/18.
- **`PartyMembershipEligibilityPolicy`** (new, proposed) — the
  versioned, governance-adopted policy record governing party-specific
  eligibility (party-scoped age thresholds, citizenship/residence
  conditions, incompatibility rules, membership-duration rules,
  exemptions, transitional rules — section 12, unchanged in shape from
  the specification).
- **`AffiliationDeclaration`** (new, proposed) — unchanged from section 10.
- **`ConflictAssessment`** (new, proposed) — unchanged from section 11.
- **Party-membership application and continuing-membership workflows**
  — the two-stage admission process (ADR-028 item 2), suspension,
  termination, and re-evaluation lifecycle.

### 3. `ParticipationRightsProfile` — an internal, non-authoritative derived view, composed across both services

**Decision, per the project owner's explicit instruction (fifth
amendment).** `ParticipationRightsProfile` (section 15) remains a
single, derived, non-stored read model — but it is now explicitly
characterized as **internal and non-authoritative**: it exists solely
to let a human-facing surface (a UI, a status page) display what the
system currently believes a subject's rights to be, and to let an
operator or the subject themselves inspect that belief. **No service,
no frontend, and no future consumer of any kind may use
`ParticipationRightsProfile`'s own boolean fields, directly or
indirectly, as the mechanism that actually grants or denies an
action.** The profile can be stale the instant after it is computed
(a policy can be superseded, a `Membership` status can change, a
`RoleAssignment` can be revoked) — treating it as authoritative would
silently reintroduce exactly the kind of cached, stale-fact risk this
pack's own `ProcessEligibilityPolicy` design (ADR-028) already forbids
for electoral eligibility specifically, now generalized to every
capability this profile surfaces. **The actual enforcement mechanism
for every action is always one of the two patterns ADR-027 fixes in
full — an atomic capability check or a single-purpose scoped capability
token — never a read of this profile.** It is no longer computed
entirely inside one service; it is composed from three
independently-computed inputs:

- **Participant eligibility results**, computed by `eligibility-service`
  (the participant-side booleans in item 1, above).
- **Party membership eligibility and status**, computed by
  `membership-service` (`can_apply_for_party_membership`,
  `can_vote_as_party_member`, `can_stand_for_party_office`, plus the
  underlying `Membership.membership_status` and
  `PartyMembershipEligibilityPolicy` evaluation).
- **Applicable `RoleAssignment` checks**, read unchanged from
  `governance-service` (`can_hold_special_role`, exactly as section 15
  already specified — no new field on `RoleAssignment` itself).

Whichever service (or a thin composing caller) ultimately assembles the
full `ParticipationRightsProfile` object for a given query, no single
service is required to hold all three inputs' underlying raw state —
each service answers only for the dimension it owns, mirroring this
project's established narrow-read discipline (ADR-012, ADR-017,
ADR-022) rather than centralizing composition logic inside one service
that would then need read access to the other two's storage.

### 4. Rules, binding on both services

- **Participant policy and party-membership policy remain independently
  versioned and independently activated.** `ParticipantEligibilityPolicy`
  (owned by `eligibility-service`) and `PartyMembershipEligibilityPolicy`
  (owned by `membership-service`) each carry their own `policy_id`/
  `policy_version`/`status`/`adopted_by_decision_id` (section 12,
  unchanged in shape) — activating one never activates, supersedes, or
  otherwise affects the other.
- **A platform participant does not require a `Membership` record.**
  Every participant-level capability (`can_read_public` through
  `can_join_civic_consultation`) is reachable through
  `ParticipantEligibilityPolicy` and the existing `EligibilityDecision`
  machinery alone, with no dependency on `Membership` existing at all —
  restated from section 4's own "platform participant vs. party member"
  superset relationship, now also a service-boundary guarantee, not only
  a conceptual one.
- **`eligibility-service` must not create or mutate party `Membership`.**
  No command proposed on `eligibility-service` writes any field of
  `Membership`, `AffiliationDeclaration`, `ConflictAssessment`, or
  `PartyMembershipEligibilityPolicy` — those remain exclusively
  `membership-service` commands.
- **`membership-service` must not become the owner of general Civic OS
  participation eligibility.** `EligibilityRule`, `EligibilityDecision`,
  and `EligibilitySnapshot` (canon 9.1–9.3) remain exclusively owned by
  `eligibility-service`, unchanged; `membership-service` never writes
  any of the three, and `ParticipantEligibilityPolicy` itself — despite
  being new, proposed content this pack introduces — is owned by
  `eligibility-service`, not `membership-service`, precisely so that the
  general-participation policy surface stays with the service that
  already owns every other general-participation entity.

### 5. Design decision D1 (participant vs. party-member capability separation) — retained, unamended

The specification's own section 6 capability-separation table (which
rights the participant policy may grant versus which the party-member
policy may additionally govern) is **unchanged** by this ADR — the
service-decomposition amendment above is a physical-ownership decision,
not a change to which capabilities exist or what they mean. A party
member's capabilities remain the **union** of whatever
`ParticipantEligibilityPolicy` (now `eligibility-service`-owned) already
grants plus whatever `PartyMembershipEligibilityPolicy` (now
`membership-service`-owned) additionally grants — never a replacement.

Rejected alternative (unchanged from the specification): a single
combined policy with a boolean `applies_to_party_members`
discriminator — rejected for the same reason the specification gave,
now reinforced by the fact that the two policies are physically owned
by two different services, making an accidental cross-grant even less
structurally possible than a single-service module boundary alone would
have prevented.

## Consequences

`services/membership-service` becomes a new, additional workspace
member at implementation time (a separate, later task, not authorized
by this ADR alone), owning a strictly smaller entity set than the
specification's own section 18 originally proposed.
`services/eligibility-service` gains one new entity
(`ParticipantEligibilityPolicy`) and an extension to its existing
evaluation machinery — its first content addition since PACK-02.
`tests/repository/test_service_boundaries.py` will need boundary
coverage for two new/extended services rather than one once
implementation begins. The `ParticipationRightsProfile` composition
question (item 3, above) becomes a cross-pack read-boundary design
point, addressed in ADR-027 rather than resolved here. Characterizing
`ParticipationRightsProfile` as internal and non-authoritative (item 3,
fifth amendment) means no OpenAPI path may present it as an
authorization endpoint — any future read endpoint exposing it is
documented, at implementation time, as informational only, with every
actual authorization decision routed through ADR-027's atomic-
capability-check or scoped-capability-token pattern instead.

## Security impact

Splitting general participation eligibility from party-membership
eligibility across two services makes it structurally harder for a
future code change to accidentally grant a party-specific capability
(e.g. `can_vote_as_party_member`) through the participant-eligibility
evaluation path — the two paths are now enforced by different services'
own commands, not merely different modules inside one service. This
directly serves the human-control and separation-of-authority
principles already central to this project (CT-00-06, CT-00-10).

## Data impact

`ParticipantEligibilityPolicy`'s canonical owner changes from
`membership-service` (as the specification's section 3 table proposed)
to `eligibility-service`. `ProcessEligibilityPolicy` (new, added by
ADR-028 item 6) is likewise owned by `eligibility-service`.
`PartyMembershipEligibilityPolicy`, `AffiliationDeclaration`,
`ConflictAssessment`, and `Membership` retain `membership-service` as
their owner, unchanged from the specification.
No canonical entity's field shape changes as a result of this ADR —
only ownership. Canon section 22's ownership matrix, once ADR-028's
canon edit is performed, will therefore need two new
service-attribution notes (mirroring the existing "physically all four
implemented by one service" notes already present for
`transparency-service`/`governance-service`), not one.

## Migration impact

None — no `services/membership-service` directory exists yet, and
`services/eligibility-service` has not yet been extended with any
PACK-07 content. Both remain separate, later implementation tasks.

## Reversibility

Reversible with low cost at this stage (no code exists for either new
entity). Once real `ParticipantEligibilityPolicy`/
`PartyMembershipEligibilityPolicy` data exists under this split
ownership, consolidating the two services (or splitting further) would
become a migration-bearing change, the same reversibility profile every
prior pack's own service-decomposition ADR has had once real data
exists.

## Related canon version

Authored against canon version `0.5.0`. Proposes no canon change
itself — the ownership split described above is repository-side service
decomposition; the corresponding canon section 22 ownership-matrix
entries (`ParticipantEligibilityPolicy` → "Eligibility Engine" or a
newly-named owner; `PartyMembershipEligibilityPolicy`/
`AffiliationDeclaration`/`ConflictAssessment` → "Membership Service",
already canon's own existing label) are proposed as part of ADR-028's
canon-addition content, not this ADR's own.

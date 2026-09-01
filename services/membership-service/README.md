# Membership Service

New service (PACK-07 implementation round, ADR-026). Owns
`PartyMembershipEligibilityPolicy` (canon 19d.6), `Membership` (canon
8.3 — this is the first real implementation of that pre-existing
canonical entity), `MembershipApplication` (canon 19d.9),
`AffiliationDeclaration` (canon 19d.10), `ConflictAssessment` (canon
19d.11), and a duplicated `Appeal` (canon 14.3) for membership/conflict
appeal targets. No other service reads or writes this service's storage
directly (INV-03).

## Scope split from `eligibility-service` (ADR-026)

`eligibility-service` owns _general_ participant eligibility
(`ParticipantEligibilityPolicy`, `ProcessEligibilityPolicy`) and never
creates or modifies `Membership`. This service owns _party-specific_
membership admission, continuing eligibility, affiliation, and conflict
concerns, and never computes an electoral-eligibility claim itself
(canon 19d.1/19d.3) — it only ever exposes the two narrow derived
booleans `required_membership_status_met`/
`membership_duration_requirement_met` for `eligibility-service` to
combine with its own `ProcessEligibilityPolicy` party-internal rules.

## Two-stage `MembershipApplication` lifecycle (ADR-030 item 2)

`application_pending → eligibility_review → human_decision_pending →
approved/rejected → activated`. A passing Stage A (automated,
policy-based) evaluation never itself activates or rejects a
`Membership`. Only Stage B — an authorized human decision, carrying a
decision-maker/authority reference, the applicable `PartyMembershipEligibilityPolicy`
version, a `reason_code`, `decided_at`, and an `AuditEvent` reference —
may move a `MembershipApplication` to `approved`/`rejected`, and only a
subsequent, distinct `activated` step (never folded into `approved`)
sets `Membership.membership_status = active`.

## Human-control invariant (canon 19d.16)

No function in this module issues a final decision for admission,
rejection, suspension, termination/expulsion, an incompatibility
finding, restoration, or any other denial of a fundamental member
right without an authorized human decision reference. Automated
evaluation (`evaluate_membership_application_eligibility`) only ever
produces a `recommended` outcome plus reason codes — never a final
one — mirroring `ai-processing-service`'s own `human_review_status`
gate (ADR-023 D1) and this project's `INV-10` fail-closed default.

## Duplicated, not imported, logic (ADR-026/030)

`epd2_core`'s own charter forbids holding domain business rules, so
this service does not import the critical-policy four-gate activation
check from `eligibility-service`, nor the polymorphic `Appeal` entity
from `moderation-service` — both are independently re-implemented here,
verbatim in shape, and kept honest by
`tests/repository/test_pack07_duplicated_logic_parity.py`.

## Cross-service reads (ADR-027)

This service may call, `.application`-only:

- `epd2_identity_service.application.get_identity_participation_claims` —
  Stage A's identity-layer facts (never `.domain`/raw `IdentityRecord`
  fields).
- `epd2_eligibility_service.application.get_eligibility_decision`/a
  narrow participant-capability read — where a concrete process already
  requires one.
- `epd2_governance_service.application.verify_decision_authorizes_policy_activation` —
  both critical-policy activation (this service's own
  `PartyMembershipEligibilityPolicy`) and `ConflictAssessment`
  `decision_authority_reference` verification (the same generic
  approved-decision check, reused for both purposes).

`eligibility-service` calls back into this service's own
`application.get_membership_derived_claims` — the one function it may
import (never this module's `.storage`/`.domain`).

## Public disclosure (ADR-030 item 5)

Membership data is restricted by default. Application existence,
membership status, rejection, suspension, termination, affiliation
details, and conflict evidence are never exposed to another service or
consumer except as the two narrow derived claims above — disclosure of
membership status itself is always either opt-in (evidenced consent) or
legally mandated, never a default arising from the enum being
"already public-shaped".

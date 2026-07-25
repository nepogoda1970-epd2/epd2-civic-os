# ADR-029: PACK-07 reason-code additions

## Status

`accepted`

## Date

2026-07-24

## Owner decision

Accepted exactly as drafted, 2026-07-25, following architectural
approval of `docs/handover/PACK-07-SPEC-FINAL.md` (v3). No further
amendment: the removal of the generic `ELECTORAL_ELIGIBILITY_NOT_MET`
code and its replacement by the four specific
`ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET`/`PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET`/
`PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET`/`PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET`
codes, plus the remaining eight new codes, are accepted verbatim
(`docs/review/PACK-07-OWNER-DECISIONS.md` section 4).

## Canon implementation (2026-07-25, follow-on task)

Canon's own section 24 ("Стандарт reason codes") lists only the
project's generic, foundational codes and has not gained a new entry
for any prior pack's additive codes (PACK-02 through PACK-06 alike) —
every pack's own additive reason codes live exclusively in that pack's
executable `contracts/reason-codes/pack-0N.yml` registry, created at
the same time as that pack's service implementation, never at the
canon-acceptance stage. Consistent with that established precedent,
this ADR's codes are accepted and approved now, but
`contracts/reason-codes/pack-07.yml` itself remains deferred to the
future `membership-service`/`eligibility-service` implementation round
(no code exists yet to reference these codes by literal, and
`tests/contract/test_reason_codes_registry.py` has nothing to check
them against). See
`docs/handover/PACK-07-CANON-AMENDMENT-REPORT.md` for the full
precedent citation.

## Context

`docs/handover/PACK-07-SPEC.md` section 23 proposed an initial set of
reason codes for participation and party-membership policy evaluation,
including a single generic `ELECTORAL_ELIGIBILITY_NOT_MET`. ADR-028
(this same round) replaces the single `electoral_eligibility_met` claim
with four independently-derived claims
(`active_electoral_eligibility_met`, `passive_electoral_eligibility_met`,
`party_internal_voting_eligibility_met`,
`party_office_candidacy_eligibility_met`), and ADR-026/ADR-028 introduce
the two-stage admission process and the restricted-by-default
membership-privacy rule — none of which the specification's original
code list names precisely. The project owner has reviewed the
specification's list and requires eight further codes, plus a rule
about which of the new codes should be used in place of the generic
electoral code the specification proposed.

## Problem

Without registered codes matching the four separated electoral-
eligibility claims (ADR-028, item 1), a future implementation would
either reuse the single generic `ELECTORAL_ELIGIBILITY_NOT_MET` for all
four distinct failures — losing exactly the precision ADR-028 introduced
— or invent unregistered literals, silently bypassing
`test_reason_codes_registry.py`'s registry-completeness check, the same
test every prior pack's own additive codes already satisfy. Similarly,
without codes for the two-stage admission process (ADR-028, item 2) and
the membership-privacy default (ADR-028, item 3), those two new rules
would have no way to fail closed with an explainable reason (INV-09).

## Considered options

- Option A — a new, separate, non-canon registry file,
  `contracts/reason-codes/pack-07.yml`, following the exact pattern
  ADR-006/ADR-014/ADR-019/ADR-024 already established.
- Option B — extend `contracts/reason-codes/pack-05.yml` (governance) in
  place, on the theory that policy activation and human-decision
  requirements are "governance-adjacent."
- Option C — propose these codes as new canon section 24 entries,
  requiring a canon edit for what is, in every prior pack's own
  precedent, registry-file content.

## Decision

**Option A**, consistent with every prior pack's own precedent (ADR-004,
ADR-006, ADR-014, ADR-019, ADR-024).

**Codes carried forward, exactly as the specification's own section 23
proposed, with one replacement noted below:**
`PARTICIPANT_AGE_REQUIREMENT_NOT_MET`,
`PARTY_MEMBERSHIP_AGE_REQUIREMENT_NOT_MET`,
`CITIZENSHIP_REQUIREMENT_NOT_MET`, `RESIDENCE_REQUIREMENT_NOT_MET`,
`EID_ASSURANCE_LEVEL_INSUFFICIENT`,
`MEMBERSHIP_DURATION_REQUIREMENT_NOT_MET`,
`DUAL_PARTY_MEMBERSHIP_CONFLICT`, `POLITICAL_ASSOCIATION_CONFLICT`,
`PUBLIC_OFFICE_INCOMPATIBILITY`, `LOBBYING_ROLE_INCOMPATIBILITY`,
`ORGANIZATIONAL_AFFILIATION_CONFLICT`,
`DECLARED_INCOMPATIBLE_ORGANIZATION`, `CONFLICT_ASSESSMENT_PENDING`,
`CONFLICT_ASSESSMENT_REQUIRES_HUMAN_REVIEW`,
`PARTY_MEMBERSHIP_APPLICATION_REJECTED`, `PARTY_MEMBERSHIP_SUSPENDED`,
`PARTY_MEMBERSHIP_TERMINATED`, `PARTICIPATION_RIGHTS_RESTRICTED`,
`POLICY_EXCEPTION_NOT_AUTHORIZED`, `POLICY_VERSION_SUPERSEDED`,
`AFFILIATION_DECLARATION_INCOMPLETE`,
`AFFILIATION_DECLARATION_REQUIRES_UPDATE`,
`CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`.

**Replaced, per the project owner's explicit instruction:**
`ELECTORAL_ELIGIBILITY_NOT_MET` (the specification's own single, generic
code) is **removed from this pack's registry** and replaced everywhere a
more precise code applies — one of the four new electoral-eligibility
codes below. No code path in this pack's design may raise the generic
name; whichever of the four specific questions actually failed
determines which specific code is raised.

**New, added by this ADR per the project owner's explicit instruction:**

| Code                                         | Raised when                                                                                                                                                                                                                                                                                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ACTIVE_ELECTORAL_ELIGIBILITY_NOT_MET`       | `active_electoral_eligibility_met` (ADR-028, item 1) evaluates false for the applicable public electoral process — the subject may not vote in that process under the currently active policy.                                                                                                                                                       |
| `PASSIVE_ELECTORAL_ELIGIBILITY_NOT_MET`      | `passive_electoral_eligibility_met` (ADR-028, item 1) evaluates false — the subject may not stand as a candidate in that same public electoral process.                                                                                                                                                                                              |
| `PARTY_INTERNAL_VOTING_ELIGIBILITY_NOT_MET`  | `party_internal_voting_eligibility_met` (ADR-028, item 1) evaluates false — the subject may not vote in internal party decisions (`can_vote_as_party_member`'s underlying condition).                                                                                                                                                                |
| `PARTY_OFFICE_CANDIDACY_ELIGIBILITY_NOT_MET` | `party_office_candidacy_eligibility_met` (ADR-028, item 1) evaluates false — the subject may not stand for a party office (`can_stand_for_party_office`'s underlying condition).                                                                                                                                                                     |
| `MEMBERSHIP_HUMAN_APPROVAL_REQUIRED`         | A party-membership admission, suspension, termination, or restoration action is attempted while Stage B's authorized human decision (ADR-028, item 2) has not yet been recorded — the two-stage admission rule's own fail-closed code.                                                                                                               |
| `MEMBERSHIP_DECISION_AUTHORITY_INVALID`      | A membership decision is presented whose decision-maker/competent-body reference cannot be verified as authorized for that decision type (e.g. fails the `governance-service` or role-based authorization check backing ADR-028 item 2's decision-maker field).                                                                                      |
| `MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED`    | A caller attempts to expose raw `Membership` status, application existence, suspension, rejection, termination, or membership history outside of one of the four permitted publication bases (ADR-028, item 3) — the membership-privacy default's own fail-closed code.                                                                              |
| `MEMBERSHIP_PUBLICATION_CONSENT_MISSING`     | A publication of membership status is attempted on the "informed voluntary consent" basis (ADR-028, item 3's fourth permitted basis) without a recorded consent reference — distinguished from `MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED` (no basis claimed at all) by identifying specifically that the consent basis was claimed but not evidenced. |

**Reused generic codes (unchanged from the specification):**
`PERMISSION_DENIED`, `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`.
Reused canon-fixed codes (section 24): `EVENT_VERSION_UNSUPPORTED`,
`INTEGRITY_CHECK_FAILED`.

Option B is rejected for the same reason ADR-014/ADR-019/ADR-024
rejected merging into another pack's registry: Participation/Membership
Policy is a structurally distinct context from Governance (ADR-026's
own service split notwithstanding — `governance-service`'s role here is
limited to the two narrow authorization reads, section 13/ADR-027),
and those two narrow reads do not make this pack's own reason codes
governance-owned content. Option C is rejected because canon section
24 is fixed, canon-immutable content — every prior pack's additive
codes have used a registry file specifically so the canon document
itself never needs editing for this kind of addition.

## Consequences

`contracts/reason-codes/pack-07.yml` would exist as a new, independent
file once implementation begins, structurally validated the same way
`test_reason_codes_registry.py` already validates `pack-02.yml` through
`pack-06.yml`. Because ADR-026 splits ownership across
`eligibility-service` and `membership-service`, this single registry
file will need to document, per code, which of the two services raises
it — a first for this project, since every prior pack-level registry
file has belonged to exactly one physical service. `docs/review/
OPEN_QUESTIONS.md` item 10 (additive codes never folded back into
canon) is now seven additive layers deep if PACK-07 proceeds — worth
the project owner's attention again, not a blocker for this pack's own
Definition of Done.

## Security impact

`MEMBERSHIP_HUMAN_APPROVAL_REQUIRED` and
`MEMBERSHIP_DECISION_AUTHORITY_INVALID` are the two codes that make
ADR-028's two-stage admission rule fail-closed rather than merely
documented — the same role `AI_CONSEQUENTIAL_OUTPUT_NOT_REVIEWED`
already plays for PACK-06's own human-control guarantee.
`MEMBERSHIP_STATUS_DISCLOSURE_PROHIBITED` and
`MEMBERSHIP_PUBLICATION_CONSENT_MISSING` together make ADR-028's
membership-privacy default fail-closed. The four separated electoral-
eligibility codes ensure a failure on one specific electoral question
(e.g. passive eligibility) is never reported using a generic code that
would obscure which of the four distinct rights was actually denied —
directly serving INV-09's explainability requirement.

## Data impact

No canonical entity, field, or status is affected — this ADR proposes
only a non-canon registry file, the same category of addition ADR-006/
ADR-014/ADR-019/ADR-024 each already made.

## Migration impact

None — no PACK-07 service or registry file exists yet.

## Reversibility

Reversible with low cost — a registry file's entries can be added,
renamed, or removed with a version bump to the file itself, unlike a
canon-level change; the same reversibility profile ADR-006/ADR-014/
ADR-019/ADR-024 already have.

## Related canon version

Authored against canon version `0.5.0`. Proposes no canon change.

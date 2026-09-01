# ADR-019: PACK-05 reason-code additions

## Status

`accepted`

## Date

2026-07-23

## Owner decision

Accepted as proposed, 2026-07-23. The full code list (Decision, below —
the specification's original nine codes plus the four new codes this
ADR added: `RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE`,
`RESULT_FINALITY_DETERMINATION_DUPLICATE`,
`GOVERNANCE_DECISION_SUPERSEDED`,
`TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE`) is approved exactly as
drafted, with no amendments. `RESULT_FINALITY_NOT_AUTHORIZED`'s narrowed
meaning (per ADR-017's accepted asymmetric write-boundary decision) is
likewise accepted as drafted. Creating
`contracts/reason-codes/pack-05.yml` itself remains a separate,
implementation-time task, not authorized by this acceptance alone — the
exact final code list remains subject to confirmation once
`governance-service`'s real source exists, the same standing caveat
ADR-014 already carried for its own pack.

## Context

Canon section 24's fixed reason-code standard has no codes scoped to
role assignment, governance policy, governance decisions, or technical
challenges — the same kind of gap ADR-006 and ADR-014 each closed for
their own packs via an additive, non-canon registry file. `docs/handover/PACK-05-SPEC.md`
section 7 proposed an initial set; this ADR extends it with the codes
this drafting round's ADR-017/018/020 decisions require that the
specification itself did not yet name, per the owner's explicit
instruction to add precise codes for unresolved challenges, duplicate
finality determination, superseded governance decisions, and invalid
challenge-submitter eligibility.

## Problem

Without a registered code, an application-layer error would either reuse
an unrelated existing code (obscuring the real reason) or invent an
unregistered literal (silently bypassing `test_reason_codes_registry.py`'s
registry-completeness check, the same test PACK-02/03/04 all already
satisfy for their own additive codes).

## Considered options

- Option A — a new, separate, non-canon registry file,
  `contracts/reason-codes/pack-05.yml`, following the exact Option B
  pattern ADR-006/ADR-014 already established (codes both this and prior
  packs need, such as `PERMISSION_DENIED`, independently redeclared
  rather than shared by import).
- Option B — extend `contracts/reason-codes/pack-04.yml` in place, on
  the theory that Transparency and Governance are both "cross-cutting
  authority/disclosure" concerns.
- Option C — propose these codes as new canon section 24 entries,
  requiring a canon edit for what is, in every prior pack's precedent,
  registry-file content.

## Decision

**Option A**, consistent with every prior pack's own precedent (ADR-004,
ADR-006, ADR-014).

**New additive codes for `contracts/reason-codes/pack-05.yml`:**

From `docs/handover/PACK-05-SPEC.md` section 7, carried forward
unchanged: `ROLE_ASSIGNMENT_NOT_ACTIVE`, `ROLE_ASSIGNMENT_SCOPE_MISMATCH`,
`GOVERNANCE_POLICY_VIOLATION`, `TWO_ACTOR_APPROVAL_REQUIRED`,
`SAME_ACTOR_APPROVAL_REJECTED`, `TECHNICAL_CHALLENGE_WINDOW_CLOSED`,
`TECHNICAL_CHALLENGE_ALREADY_ADJUDICATED`,
`GOVERNANCE_DECISION_NOT_APPROVED`, `BALLOT_INVALIDATION_NOT_AUTHORIZED`.

**New, added by this ADR per the owner's explicit instruction:**

| Code                                        | Raised when                                                                                                                                                                                                                                          |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RESULT_FINALITY_BLOCKED_BY_OPEN_CHALLENGE` | A `result_finality_determination` `GovernanceDecision` is attempted for a `ResultPublication` that still has one or more `submitted`/`under_review` `TechnicalChallenge` records (ADR-018, D6).                                                      |
| `RESULT_FINALITY_DETERMINATION_DUPLICATE`   | A second, independent `result_finality_determination` decision is attempted for a `ResultPublication` that already has an `approved`, non-superseded one (ADR-018, D6) — a superseding decision must set `supersedes_decision_id` instead.           |
| `GOVERNANCE_DECISION_SUPERSEDED`            | Any command attempts to act on a `GovernanceDecision` (e.g. `voting-service.invalidate_ballot`'s validation read) whose current status is `superseded` — only the superseding decision, never the superseded one, may authorize a downstream action. |
| `TECHNICAL_CHALLENGE_SUBMITTER_INELIGIBLE`  | `submit_technical_challenge` is called by an actor whose `RoleAssignment` is not `active`, not in scope for the referenced `ResultPublication`, or does not match ADR-020 item 2's eligible-participant/authorized-observer criteria.                |

Removed from the specification's original proposal, superseded by the
above: `RESULT_FINALITY_NOT_AUTHORIZED` is retained but its meaning is
narrowed by ADR-017's decision — it now applies only to a would-be
direct query/action against `ResultPublication` finality state that
bypasses `governance-service.get_finality_status` entirely, since no
`tally-service` command exists for it to gate (ADR-017).

**Reused generic codes (unchanged from the specification):**
`PERMISSION_DENIED`, `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`.

Option B is rejected for the same reason ADR-014 rejected merging into
`pack-03.yml`: Transparency and Governance are structurally distinct
contexts (`docs/handover/PACK-05-SPEC.md` section 1), and a shared
registry file would blur which pack actually owns which code's
lifecycle. Option C is rejected because canon section 24 is fixed,
canon-immutable content — every prior pack's additive codes have used a
registry file specifically so the canon document itself never needs
editing for this kind of addition (a point ADR-010's own Context section
already draws out explicitly for why field/entity additions differ from
reason-code additions).

## Consequences

`contracts/reason-codes/pack-05.yml` would exist as a new, independent
file once implementation begins, structurally validated the same way
`test_reason_codes_registry.py` already validates `pack-02.yml`/
`pack-03.yml`/`pack-04.yml`. `docs/review/OPEN_QUESTIONS.md` item 10
(PACK-02's additive codes never folded back into canon) is now five
additive layers deep if PACK-05 proceeds — worth the project owner's
attention again, not a blocker for this pack's own Definition of Done.

## Security impact

`SAME_ACTOR_APPROVAL_REJECTED` and `GOVERNANCE_DECISION_SUPERSEDED` are
both directly security-relevant: the first is the code raised when
INV-08's separation-of-authority rule (section 9 of the specification)
is violated at the point of approval; the second prevents a stale,
already-superseded decision from being used to authorize a downstream
action (e.g. an old, corrected `ballot_invalidation` ruling being
replayed against `voting-service.invalidate_ballot` after a newer,
superseding decision has already been recorded).

## Data impact

No canonical entity, field, or status is affected — this ADR proposes
only a non-canon registry file, the same category of addition ADR-006/
ADR-014 already made.

## Migration impact

None — no PACK-05 service or registry file exists yet.

## Reversibility

Reversible with low cost — a registry file's entries can be added,
renamed, or removed with a version bump to the file itself, unlike a
canon-level change; the same reversibility profile ADR-006/ADR-014
already have.

## Related canon version

Authored against canon version `0.3.0`. Proposes no canon change.

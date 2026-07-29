# ADR-062: Purpose-scoped, time-bound privileged access management

## Status

`proposed`

## Date

2026-07-29

## Context

`FIR-INV-009` requires privileged access to be time-limited,
purpose-bound, approved where required and fully audited. `AGR-23`
requires the lifecycle that produces those properties. No pack implements
it today: PACK-08 can express an authority assignment, but an assignment
is a standing fact, not a bounded, justified, reviewable grant.

PACK-10 established the pattern this ADR generalises. `finance-service`
routes every command through one guard frame that checks scope, then
authority, then role incompatibility and self-approval, then conflict
declaration, then idempotency, then optimistic concurrency — in that
fixed order, with no command allowed to assemble its own sequence.

## Problem

1. A standing administrative assignment has no purpose, no expiry and no
   review trigger. It is indistinguishable, at the moment of an act, from
   a grant issued five minutes ago for a stated reason.
2. Without an explicit lifecycle, "approval" collapses into "someone
   clicked yes once", and the record afterwards cannot answer what was
   approved, for what, for how long, or whether it was ever used.
3. Without re-evaluation at activation and at each operation, a decision
   taken under one role set is executed under another.

## Considered options

- **Option A — role assignment is the grant.** Zero new machinery; also
  zero purpose, zero expiry and zero reviewability. Rejected: it fails
  `FIR-INV-009` on three of its four clauses.
- **Option B — grants with expiry only.** Time-bounding alone leaves a
  grant that is bounded but unexplained, and permits a wide grant for a
  narrow need. Rejected as insufficient.
- **Option C — a grant that is simultaneously purpose-, resource-,
  operation-, organization-scoped and time-bound, attributable,
  reviewable, revocable and auditable; with separation-of-duties
  evaluation at approval and again at activation, and authorization
  re-checked at every privileged operation.** **Chosen.**

## Decision

The `PrivilegedAccessGrant` lifecycle is
`requested → under_evaluation → approved|denied → activated → active →
expired|revoked → under_post_access_review → review_completed`.

`P12-PAM-002` makes the nine properties jointly mandatory: a grant
missing any one MUST NOT be issuable. This is a construction-time
invariant, not a validation step — the precedent is PACK-09's
`GovernedRecord`, whose `__post_init__` refuses a destroyed record that
carries no destruction evidence.

Expiry is automatic and in-place extension is prohibited
(`P12-PAM-006`). Continuation is a new request with a new decision. A
permanent standing superuser is not a designable mode (`P12-PAM-003`).

Separation of duties is evaluated at approval and **re-evaluated** at
activation (`P12-PAM-005`), because a role set can change in between; and
authorization is re-checked at every privileged operation
(`P12-PAM-010`), because a grant can expire or be revoked mid-session.

## Consequences

Easier: every privileged act has an answerable "under what authority, for
what purpose, decided by whom, valid until when"; dormant privilege
becomes visible; revocation is meaningful.

Harder: three checks where there was one, and a real latency cost at
every privileged operation. Operators will experience expiry as friction.
The implementation must make re-request cheap, because the failure mode
of an inconvenient control is a wider grant "to avoid the hassle" — which
is precisely `P12-PAM-003`'s prohibition being routed around socially
rather than technically.

## Security impact

Addresses T-P12-02 (self-approval), T-P12-03 (role accumulation) and
T-P12-04 (dormant standing privilege). Reduces the blast radius of
T-P12-05 and T-P12-06 without addressing their root cause, which is
PACK-14's.

## Data impact

Introduces new governed objects — `PrivilegedAccessRequest`,
`PrivilegedAccessDecision`, `PrivilegedAccessGrant`,
`SeparationOfDutiesEvaluation`, `PrivilegedAccessReview`,
`PostAccessReview` — all owned by PACK-12. No existing canonical entity
changes.

## Migration impact

None in this round. At implementation time, any pre-existing standing
administrative assignment would need converting into bounded grants;
whether that conversion is automatic or operator-driven is left open
(`OD-P12-04` context).

## Reversibility

Reversible with cost. The lifecycle is additive; abandoning it would
mean returning to standing assignments, which the register forbids.

## Related canon version

Authored against canon `0.8.0`. Proposes no canon version bump.

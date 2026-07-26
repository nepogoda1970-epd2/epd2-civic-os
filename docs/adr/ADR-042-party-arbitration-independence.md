# ADR-042: Party arbitration, dispute separation and procedural independence

## Status

`accepted`

## Date

2026-07-26

## Context

Internal party disputes — a contested expulsion, a challenged local
election, a complaint against an office-holder — are decided inside the
organization being complained about. That is the structural problem: the
people with the authority to run the procedure are frequently connected to
its subject matter, and the credibility of the outcome rests entirely on
whether the decision-maker was actually independent of the parties.

Two mechanisms are supposed to protect that, and both are routinely
implemented in ways that do nothing:

- **Role separation** degrades into one field. If a case carries a single
  "responsible person", then whoever runs the procedure also decides it,
  and there is no record of the difference because there was none.
- **Conflict of interest** degrades into a text box. If a conflict is a
  free-text note that changes no behaviour, then declaring one and not
  declaring one lead to the same workflow, and the declaration is theatre.

A third failure is more specific and more serious: **self-appointment**.
Nothing in an ordinary CRUD case model prevents the claimant, the
respondent, or the case handler from writing their own id into the
`decision_maker` field. The system will accept it, and the resulting
decision is worthless.

## Problem

How should arbitration and internal dispute cases be modelled so that:

- procedural authority, case handling and deciding are _distinguishable_
  roles, not one field;
- no participant can appoint themselves as independent decision-maker;
- the current case handler cannot appoint themselves either;
- a conflict of interest is a state that changes what the workflow
  permits;
- only a party holding a permitted role can record the decision;
- a closed case cannot be quietly edited; and
- an appeal is a real, separate governed object rather than a status
  rollback?

## Considered options

- **Option A — a separate `dispute-service`** with its own case model,
  distinct from compliance cases.
- **Option B — dispute-specific case types on the shared
  `ProceduralCase`**, with independence enforced by application-layer
  checks and an explicit conflict state.
- **Option C — Option B plus a mandatory panel** (three decision-makers,
  majority decision).

## Decision

**Option B.** Arbitration and internal disputes are `CaseType`
values — `party_arbitration` and `internal_dispute` — on the shared
`ProceduralCase`, with independence enforced as follows.

Option A was rejected because a dispute case needs exactly the same
deadlines, scope isolation, evidence references, decision record and audit
trail as every other governed case; duplicating that machinery would
duplicate its bugs. Option C was rejected as out of scope for this pack:
panel composition, quorum and majority rules are governance decisions this
round has no owner mandate for, and a fake panel (three fields, no rules)
would be worse than an honest single decision-maker.

### 1. Six distinguishable procedural roles

`ProceduralRole` is `procedural_authority`, `case_handler`,
`independent_decision_maker`, `claimant`, `respondent`, `submitter`.

`SEPARATED_ROLES` — the first three — may never be held by the same party
reference on one case. `ProceduralCase.__post_init__` checks that
`procedural_authority_reference`, `case_handler_reference` and
`assigned_decision_maker_reference` are three distinct values, so a case
violating the separation cannot be constructed at all, on any path,
including `dataclasses.replace`.

`PARTY_ROLES` — the last three — identify parties to the dispute.
`register_dispute_parties` records `DisputeParties` (claimant and
respondent, which must differ) _and_ writes the corresponding
`CaseRoleAssignment` rows, so the independence checks have something to
see. `CaseRoleAssignmentStore` is append-only: who held which role at
which point stays answerable.

### 2. Independence is one pure function, applied by one command

`domain.assert_decision_maker_eligible` is the single gate, called by
`application.assign_independent_decision_maker`. It refuses when:

| Condition                                                 | Reason code                         |
| --------------------------------------------------------- | ----------------------------------- |
| candidate == appointer (self-appointment)                 | `PROCEDURAL_INDEPENDENCE_VIOLATION` |
| appointer holds any `PARTY_ROLES` role on this case       | `PROCEDURAL_INDEPENDENCE_VIOLATION` |
| appointer is the current case handler                     | `PROCEDURAL_INDEPENDENCE_VIOLATION` |
| candidate holds any `PARTY_ROLES` role on this case       | `PROCEDURAL_INDEPENDENCE_VIOLATION` |
| candidate is the procedural authority or the case handler | `PROCEDURAL_INDEPENDENCE_VIOLATION` |
| no conflict declaration exists for the candidate          | `CONFLICT_OF_INTEREST_UNDECLARED`   |
| the candidate's declaration is in a blocking state        | `CONFLICT_OF_INTEREST_BLOCKING`     |

Making it a pure function over `(case, role_assignments,
conflict_declarations)` rather than a method means it is directly
testable against every combination without constructing a store, and
there is exactly one implementation to review.

### 3. Conflict of interest is an explicit state, not free text

`ConflictState` is `none_declared` / `declared` / `confirmed` / `waived`.
`BLOCKING_CONFLICT_STATES` is `{declared, confirmed}` — both make the
party ineligible for a separated role and ineligible to record a decision.
`waived` requires a recorded decider and timestamp
(`__post_init__` enforces it), so a waiver is always attributable.

**Absence of a declaration is not "no conflict".** A candidate with no
declaration at all is refused with `CONFLICT_OF_INTEREST_UNDECLARED`
(fail closed, PACK-09 required invariant 15) — the declaration is a
positive act, and requiring one is what makes `none_declared` meaningful.

`basis_code` is a short closed-vocabulary marker
(e.g. `same_local_branch`). Any human narrative lives in a document
referenced under PACK-11, never in this service.

### 4. Only a permitted role may decide

`application._resolve_deciding_role` decides who may record a
`CaseDecision`:

- for `party_arbitration` and `internal_dispute`, **only** the assigned
  `independent_decision_maker` — and if none has been assigned, the
  command fails with `DECISION_AUTHORITY_MISSING` rather than falling back
  to the procedural authority;
- for the other case types, the assigned decision-maker if there is one,
  otherwise the procedural authority;
- anyone else: `DECISION_AUTHORITY_MISSING`.

The deciding party is additionally re-checked against the case's conflict
declarations at decision time (`CONFLICT_OF_INTEREST_BLOCKING`), because a
conflict can be declared _after_ an appointment.

`CaseDecision` is create-once per case, records `decided_by_role`
alongside `decided_by_party_reference`, carries a `reason_code`, and holds
only `evidence_references` — never evidence content.

### 5. A closed case is immutable; an appeal is a separate case

Every case-mutating command calls `_require_case_open`; a closed case
raises `PROCEDURAL_CASE_CLOSED`. `file_appeal` requires the original case
to be `decided` or `closed`, opens a **new** `ProceduralCase` inside the
caller's own organization, and records an `AppealReference` linking the
two (`original_case_id` ≠ `appeal_case_id`, enforced). The original is
never reopened or edited, which is what keeps the closed-case guarantee
true rather than nominal.

### 6. Parties are per-case handles

Claimant, respondent, handler and decision-maker references are all
`mint_case_party_reference()` UUIDs — random, per-case, never reused,
never derived from identity/membership/account data, unresolvable inside
this service. Two disputes involving the same real person carry two
unrelated references. This is how ADR-038's invariant-1 guarantee reaches
arbitration specifically: even a full dump of every dispute case discloses
no cross-case linkage of people.

## Consequences

Easier: independence is auditable from the case's own role-assignment
history and conflict declarations; the reason code on a refusal says which
independence rule fired; an appeal chain is a graph of real objects.

Harder: staffing a dispute now takes several explicit calls — register
parties, assign a handler, file a conflict declaration for the candidate,
then appoint — where a single-field model took one. And a candidate with
_no_ declaration is blocked, which will surprise operators who expect
silence to mean "no conflict". Both are intentional.

Not implemented, honestly stated rather than glossed: there is **no**
panel/multi-decider model, no quorum rule, no recusal-and-replacement
workflow, and no automatic detection of conflicts from organizational
relationships. Conflicts must be declared; the system does not infer them.
Those belong to a later round with an owner mandate.

## Security impact

Self-appointment and handler-appointment are the two attacks this ADR
exists to close, and both are closed structurally rather than by policy:
the checks live in one pure function that the only appointment command
calls unconditionally. The role-separation check in
`ProceduralCase.__post_init__` means even a direct `replace()` on a stored
case cannot produce a role collision.

Because conflict absence fails closed, an attacker cannot benefit from
suppressing a declaration — the appointment simply does not proceed.

## Data impact

New schemas: `conflict-of-interest-declaration`, `case-decision` (shared
with ADR-041). `ProceduralCase` gains `case_handler_reference` alongside
the pre-existing `procedural_authority_reference` and
`assigned_decision_maker_reference`. No new event type is introduced for
arbitration specifically: role assignments and decisions are emitted as
`procedural_case.status_changed`, whose payload deliberately carries **no**
party reference at all — who holds which role is not broadcast.

## Migration impact

None. No pre-existing dispute data exists.

## Reversibility

Reversible with cost. Adding a panel model later is additive: the
independence gate would be applied per panel member, and `CaseDecision`
would gain a composition reference under a new ADR. Removing the
independence checks would be a security regression and would need its own
ADR arguing why.

## Related canon version

Canon `0.7.0`, no bump. Arbitration is expressed entirely as case types
and role assignments on compliance-service's own `ProceduralCase`; canon
names no arbitration entity, and no new event type is added.

## Amendment (Architecture & Domain Framework 0.8.1, same 0.9.0 round)

Framework hard invariants 52, 53, 54 and 69 extend this ADR's
independence rule from "who may decide a dispute" to "what a
consequential decision requires at all".

**`assert_due_process_complete`** encodes hard invariant 52 as six named
prerequisites — jurisdiction, legally effective notice, an opportunity to
respond, a human deciding actor, reasons, and an available remedy — and
names in its message the _one_ that is missing. A refusal that said only
"due process incomplete" would be unactionable for the party told to fix
it.

**Recusal blocks capability without erasing history** (invariant 53).
`RecusalRecord.prior_participation_codes` preserves what the recused
actor already did, and nothing removes those acts: they may themselves be
the subject of the appeal. `assert_actor_not_recused` compares against
`effective_at`, so a recusal recorded for a future date does not
retroactively invalidate earlier acts. It is applied to _every_
consequential command — scheduling a hearing and deciding filing
admissibility are exercises of authority too, not only final decisions.
A replacement who is themselves recused is refused, because otherwise a
recusal could be "resolved" by handing the matter to somebody equally
conflicted.

**Assessments are versioned, not overwritten** (invariant 54): a
superseding assessment names the one it supersedes rather than replacing
it.

**AI decides no consequential legal outcomes** (invariant 69). This is
enforced in two independent places, on purpose:
`InterimMeasure.__post_init__` refuses to construct a _granted_ measure
unless `decided_by_actor_class is ActorClass.HUMAN_AUTHORITY`, and
`assert_due_process_complete` refuses any decision made by a `service` or
`automated` actor. `human_case_handler` is a human but is deliberately
**not** sufficient: "a person did it" is not the same as "the competent
authority decided it".

`interim_measure.decided` publishes `decided_by_actor_class` by name, so
the guarantee is checkable by any subscriber rather than only by this
service's own tests.

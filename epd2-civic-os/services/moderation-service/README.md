# Moderation Service

Owns `ModerationCase`, `ModerationDecision`, `Appeal` (canon
`docs/canonical/TZ-00-domain-event-canon.md` section 14). ADR-005
consolidates two canon-named modules - "Moderation Service" and "Appeal
Service" - into this one physical package.

## Why this consolidation is safe (ADR-005 item 3, verbatim rationale)

> **`services/moderation-service`** (`epd2_moderation_service`) -
> `ModerationCase`, `ModerationDecision`, `Appeal`. Consolidates
> "Moderation Service" and "Appeal Service". Canon's explicit prohibition
> ("an appeal must not be finally decided by the author of the original
> decision", section 14.3) is a role-separation invariant enforced by an
> application-layer actor check (`appeal.reviewer_actor_id !=
original_decision.decided_by`), not a deployment-separation invariant -
> the same shape as PACK-02's existing `actor_is_authorized` checks,
> which live inside single services, not across separate ones.

In other words: putting "who investigated/decided the case" and "who
reviews an appeal against that decision" in the same physical service is
only dangerous if the _code_ lets one actor play both roles. It does not
require two separately deployed services to prevent that - it requires
one application-layer check, enforced every time, with no code path that
skips it. That check lives in `application.decide_appeal`:

```python
if reviewer_actor_id == decision.decided_by:
    raise PermissionDeniedError(
        "an appeal must not be finally decided by the actor who made the "
        "original moderation decision (canon section 14.3)"
    )
```

`decision` here is looked up from `appeal.decision_id`, so the check is
always made against the _actual_ `ModerationDecision.decided_by` on
record, never a caller-supplied claim. The check runs before any
mutation of `Appeal` or `ModerationCase`, and - critically - it is not
skippable via the command's own `event_id` idempotency mechanism: a
genuine idempotent replay of an already-recorded `event_id` can only ever
return a result that already passed this exact check the first time it
was computed (see `application.decide_appeal`'s own docstring). A brand
new call, for any `event_id` not already on record, always re-runs the
check.

`tests/test_application.py`'s
`test_decide_appeal_rejects_the_original_decider_as_reviewer` /
`test_decide_appeal_succeeds_for_a_different_reviewer` are this
service's flagship pair: same fixture decision and appeal, only the
`reviewer_actor_id` differs between the two calls, one direction denied,
the other accepted.

## No PACK-02 dependency (ADR-008)

`docs/handover/PACK-03-SPEC.md` and ADR-008's own enumerated
PACK-03-to-PACK-02 edge list name no PACK-02 service this service needs
to call. `pyproject.toml` declares exactly two dependencies -
`epd2-core` and `epd2-audit-core` - and no module in this package ever
imports `epd2_account_service`, `epd2_identity_service`,
`epd2_eligibility_service`, or `epd2_credential_service`. It also never
imports any other PACK-03 service (`epd2_voting_service`,
`epd2_initiative_service`, `epd2_deliberation_service`, ...) - every
input this service's commands need (`decided_by`, `opened_by`,
`submitted_by`, `assigned_moderator`, `reviewer_actor_id`) is a bare
actor-id `UUID`, supplied by the caller, never resolved by this service
itself.

## Entities and their state machines

### `ModerationCase` (canon 14.1)

Statuses: `open -> under_review -> action_proposed -> decided -> {appealed, closed}`,
plus `appealed -> closed`. See `domain.CASE_ALLOWED_TRANSITIONS`.

### `ModerationDecision` (canon 14.2)

No status field and no transition table - a `ModerationDecision` is
created once by `application.issue_decision` and is immutable
thereafter, mirroring `epd2_initiative_service`'s `InitiativeVersion`.
`ModerationDecisionStore` therefore exposes only `create`/`get`, never a
`save`.

`ModerationDecision.reason_code` is canon's own field name (section
14.2) - a reason-code-registry **value** describing why the decision was
made (e.g. `"MODERATION_POLICY_VIOLATION"`), supplied by the caller. This
is a completely different concept from the `reason_code` **class
attribute** every exception in `exceptions.py` carries (e.g.
`PermissionDeniedError.reason_code == "PERMISSION_DENIED"`), which
describes a failure of this service's own API. `domain.py` only checks
that the field is a non-empty string - a full reason-code registry
lookup is out of scope for the domain layer here, the same scope limit
every sibling PACK-02/03 service already draws for opaque reference
strings.

`audit_reference` is populated by `application.issue_decision` at
construction time with `str(resolved_event_id)` - the same id used as
that call's own `AppendAuditEventRequest.audit_event_id` - so the
decision's own record of "which audit entry documents me" is correct
from the moment it is created; there is no patch path (the dataclass is
frozen).

### `Appeal` (canon 14.3)

Statuses: `submitted -> admissibility_review -> under_review -> {upheld,
partially_upheld, rejected}`, plus `admissibility_review -> rejected` and
a `withdrawn` exit from any of `submitted`/`admissibility_review`/
`under_review`. See `domain.APPEAL_ALLOWED_TRANSITIONS` and
`domain.FINAL_APPEAL_OUTCOMES`.

## Application commands -> canon events (section 20.9, verbatim list)

| Command                | Transition                                                                  | Event                          |
| ---------------------- | --------------------------------------------------------------------------- | ------------------------------ |
| `open_moderation_case` | (create) `-> open`                                                          | `moderation.case_opened`       |
| `assign_moderator`     | `open -> under_review`                                                      | `moderation.case_assigned`     |
| `propose_action`       | `under_review -> action_proposed`                                           | _(none - see below)_           |
| `issue_decision`       | `action_proposed -> decided` (+ creates `ModerationDecision`)               | `moderation.decision_issued`   |
| `enforce_decision`     | _(no status field changes - see below)_                                     | `moderation.decision_enforced` |
| `submit_appeal`        | case `decided -> appealed` (+ creates `Appeal`)                             | `moderation.appeal_submitted`  |
| `decide_appeal`        | appeal `-> {upheld, partially_upheld, rejected}`, case `appealed -> closed` | `moderation.appeal_decided`    |

Every command follows the shared shape: `actor: ActorRef,
actor_is_authorized: bool, correlation_id: UUID, clock: Clock, event_id:
UUID | None = None`, and every state-changing command calls
`append_audit_event` (CT-00-07). `event_id` is the CT-00-04 idempotency
key: a repeated call with the same `event_id` looks up
`audit_store.get_by_event_id(...)` up front and, if found, returns the
already-recorded result instead of re-running a transition that would
otherwise fail (the entity has already moved past the state that
transition starts from).

### `propose_action`: a real transition with no canon event

Canon's own event-name list for this service (section 20.9) names
exactly six events - `case_opened`, `case_assigned`, `decision_issued`,
`decision_enforced`, `appeal_submitted`, `appeal_decided`. It names none
for the bare `under_review -> action_proposed` hop. This mirrors
`epd2_eligibility_service.application.create_eligibility_rule`'s own
precedent for "canon defines no domain event for this step": the
transition is still persisted and still audited (every state-changing
command must append an audit event, per CT-00-07) - it simply builds no
`EventEnvelope`. `ProposeActionResult` therefore has no `event` field.

### `enforce_decision`: no dedicated status field

`ModerationDecision` (canon 14.2) has no field recording whether it has
been enforced. This service's judgment call: `enforce_decision` does not
add an undocumented field to the canon entity, and it does not transition
`ModerationCase.status` either (the case stays `decided`) - enforcement
is recorded purely as an `EventEnvelope` + `AuditEvent` pair, never as a
mutation to either owned entity. Consequently `before_hash == after_hash`
for the decision in this audit entry by construction; that equality is
still meaningful tamper-evidence (it proves the decision record was
byte-for-byte unchanged at the instant enforcement was recorded), not a
bug. A future pack that needs "has this decision been enforced yet?" as
a queryable fact should add it as a proper canon field via its own ADR,
not have this service invent one silently.

### Appeal review walk: folded into `decide_appeal`

This pack implements no standalone commands for the
`submitted -> admissibility_review` or `admissibility_review ->
under_review` hops - canon names no event for either, and (unlike
`propose_action`, which is the terminus of its own command) both are
sub-steps of the same overall appeal review that `decide_appeal`
performs atomically in one call, walking
`submitted -> admissibility_review -> under_review -> <final outcome>`
and validating each hop against `domain.APPEAL_ALLOWED_TRANSITIONS` in
turn. One `EventEnvelope` (`moderation.appeal_decided`) and one
`AuditEvent` are emitted for the whole call - the intermediate hops are
persisted as part of the same final `Appeal` state, not separately
audited one-by-one, the same way `epd2_voting_service.open_ballot`
updates every locked `BallotOption` in one command without a
per-option audit entry.

One direct consequence: the standalone `admissibility_review -> rejected`
edge in `domain.APPEAL_ALLOWED_TRANSITIONS` (an appeal rejected as
inadmissible without ever reaching full `under_review`) is reachable at
the domain layer and tested there, but `decide_appeal` itself always
walks _through_ `under_review` on its way to any outcome including
`rejected`. Distinguishing "rejected for inadmissibility" from "rejected
after full review" as two different application-layer paths is left as a
documented gap (see "Known gaps" below) rather than invented without a
canon or spec basis for the distinction.

## Known gaps (documented, not silently dropped)

- **No `withdraw_appeal` command.** The domain-legal withdrawal
  transitions (`submitted`/`admissibility_review`/`under_review` ->
  `withdrawn`) exist in `domain.APPEAL_ALLOWED_TRANSITIONS` and are
  tested via `Appeal.with_status` in `tests/test_domain.py`, but this
  pack's command list (canon section 20.9's event list) names no
  `appeal.withdrawn` event and no dedicated command, so none is exposed
  in `application.py`.
- **No direct `decided -> closed` command** (a case closed with no
  appeal at all). Domain-legal and tested via `ModerationCase.with_status`,
  but not exposed as an application command - the only wired path to
  `closed` in this pack is `decided -> appealed -> closed`, via
  `submit_appeal` + `decide_appeal`.
- **`APPEAL_DEADLINE_EXPIRED` is reserved, not enforced.** Canon names
  this reason code (section 24) but gives `Appeal`/`ModerationDecision`
  no explicit deadline field (section 14.2/14.3's field lists have
  neither an `appeal_deadline_at` nor a `submitted_within_hours`).
  Rather than invent a canon field silently, this service reserves the
  reason code (see `exceptions.AppealDeadlineExpiredError`) for a future
  pack/ADR to wire up once canon defines where the deadline actually
  lives, and does not enforce any hardcoded deadline in `submit_appeal`
  today.

## Reason codes

Canon codes reused verbatim: `VALIDATION_UNKNOWN_STATUS`,
`VALIDATION_FORBIDDEN_TRANSITION`, `VALIDATION_RECORD_NOT_FOUND`,
`PERMISSION_DENIED`, `MODERATION_POLICY_VIOLATION` (an example
_decision-content_ value for `ModerationDecision.reason_code`, not an
exception code - see above), `APPEAL_DEADLINE_EXPIRED` (reserved, not
enforced - see "Known gaps").

Additive, this service's own (`exceptions.py`):
`MODERATION_CASE_DUPLICATE_CONFLICT`,
`MODERATION_DECISION_DUPLICATE_CONFLICT`,
`APPEAL_DUPLICATE_SUBMISSION_CONFLICT`.

Additive, audit-success classifications (`application.py`, info
severity): `MODERATION_CASE_STATUS_CHANGED`, `MODERATION_DECISION_ISSUED`,
`MODERATION_DECISION_ENFORCED`, `APPEAL_STATUS_CHANGED`,
`APPEAL_DECIDED`.

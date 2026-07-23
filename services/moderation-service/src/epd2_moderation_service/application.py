"""Moderation Service application layer: `open_moderation_case`,
`assign_moderator`, `propose_action`, `issue_decision`, `enforce_decision`,
`submit_appeal`, `decide_appeal` — canon sections 14.1/14.2/14.3,
`docs/handover/PACK-03-SPEC.md` section 5's event-name list.

Every command below accepts an optional caller-supplied `event_id`
(CT-00-04): a caller retrying the exact same command with the same
`event_id` gets back the already-recorded result instead of re-running
the transition (which would otherwise fail once the entity has already
moved past the state that transition starts from). `event_id` defaults to
a fresh `generate_uuid()` and is reused as
`AppendAuditEventRequest.audit_event_id`, exactly as
`epd2_credential_service.application.issue_participation_credential`
already established for PACK-02. The idempotency check happens by looking
up `audit_store.get_by_event_id(resolved_event_id)` up front — Audit
Core's own `append_audit_event` is itself idempotent by that same id, but
checking here too is required so this module never re-attempts a domain
transition that has already happened (which would raise a spurious
`Forbidden*TransitionError` on the second call).

No PACK-02 dependency (ADR-008): `docs/handover/PACK-03-SPEC.md` and
ADR-008's own enumerated edge list name no PACK-02 service this service
needs to call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_moderation_service.domain import (
    FINAL_APPEAL_OUTCOMES,
    Appeal,
    AppealStatus,
    ModerationCase,
    ModerationCaseStatus,
    ModerationDecision,
    ModerationDecisionType,
)
from epd2_moderation_service.events import (
    appeal_full_state_payload,
    build_appeal_decided_event,
    build_appeal_submitted_event,
    build_case_assigned_event,
    build_case_opened_event,
    build_decision_enforced_event,
    build_decision_issued_event,
    case_full_state_payload,
    decision_state_payload,
)
from epd2_moderation_service.exceptions import (
    UnknownAppealError,
    UnknownModerationCaseError,
    UnknownModerationDecisionError,
)
from epd2_moderation_service.storage import (
    AppealStore,
    ModerationCaseStore,
    ModerationDecisionStore,
)

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "moderation-service"

#: Audit `reason_code` classifications (ADR-006 item 2 pattern: one
#: generic classification per logical action-type, not one per specific
#: transition - the specific transition is already carried by the domain
#: event's own `event_type`, or in `propose_action`'s case, by `action`).
_CASE_STATUS_CHANGED = "MODERATION_CASE_STATUS_CHANGED"
_DECISION_ISSUED = "MODERATION_DECISION_ISSUED"
_DECISION_ENFORCED = "MODERATION_DECISION_ENFORCED"
_APPEAL_STATUS_CHANGED = "APPEAL_STATUS_CHANGED"
_APPEAL_DECIDED = "APPEAL_DECIDED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class CaseResult:
    case: ModerationCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ProposeActionResult:
    """No `event` field: `propose_action` has no canonical `EventEnvelope`
    (see this module's `propose_action` docstring)."""

    case: ModerationCase
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision: ModerationDecision
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class EnforceDecisionResult:
    decision: ModerationDecision
    case: ModerationCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AppealResult:
    appeal: Appeal
    case: ModerationCase
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DecideAppealResult:
    appeal: Appeal
    case: ModerationCase
    event: EventEnvelope
    audit_event: AuditEvent


def open_moderation_case(
    case_store: ModerationCaseStore,
    audit_store: AuditEventStore,
    *,
    moderation_case_id: UUID,
    target_type: str,
    target_id: UUID,
    opened_by: UUID,
    trigger_type: str,
    policy_version: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CaseResult:
    """Open a new `ModerationCase` in `open` status. Emits
    `moderation.case_opened`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to open a moderation case")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        case = case_store.get(moderation_case_id)
        if case is None:
            raise UnknownModerationCaseError(
                f"idempotent replay for event_id {resolved_event_id} found no case "
                f"{moderation_case_id}"
            )
        event = build_case_opened_event(
            event_id=resolved_event_id,
            case=case,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return CaseResult(case=case, event=event, audit_event=existing_audit)

    now = clock.now()
    case = ModerationCase(
        moderation_case_id=moderation_case_id,
        target_type=target_type,
        target_id=target_id,
        opened_by=opened_by,
        trigger_type=trigger_type,
        policy_version=policy_version,
        status=ModerationCaseStatus.OPEN,
        assigned_moderator=None,
    )
    stored = case_store.create(case)
    event = build_case_opened_event(
        event_id=resolved_event_id,
        case=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="moderation_case",
            target_id=stored.moderation_case_id,
            action="open_case",
            reason_code=_CASE_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(case_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return CaseResult(case=stored, event=event, audit_event=audit_event)


def assign_moderator(
    case_store: ModerationCaseStore,
    audit_store: AuditEventStore,
    *,
    moderation_case_id: UUID,
    moderator_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> CaseResult:
    """`open -> under_review`, recording `assigned_moderator`. Emits
    `moderation.case_assigned`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to assign a moderator")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        case = case_store.get(moderation_case_id)
        if case is None:
            raise UnknownModerationCaseError(f"unknown moderation_case_id: {moderation_case_id}")
        event = build_case_assigned_event(
            event_id=resolved_event_id,
            case=case,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return CaseResult(case=case, event=event, audit_event=existing_audit)

    case = case_store.get(moderation_case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {moderation_case_id}")

    before_hash = compute_payload_hash(case_full_state_payload(case))
    updated = case.with_assigned_moderator(moderator_id)
    case_store.save(updated)
    now = clock.now()
    event = build_case_assigned_event(
        event_id=resolved_event_id,
        case=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="moderation_case",
            target_id=updated.moderation_case_id,
            action="assign_moderator",
            reason_code=_CASE_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(case_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return CaseResult(case=updated, event=event, audit_event=audit_event)


def propose_action(
    case_store: ModerationCaseStore,
    audit_store: AuditEventStore,
    *,
    moderation_case_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ProposeActionResult:
    """`under_review -> action_proposed`.

    This pack's own canonical event-name list (`events.py` module
    docstring; `docs/handover/PACK-03-SPEC.md` section 5) names no domain
    event for this specific transition alone - only `case_opened`,
    `case_assigned`, `decision_issued`, `decision_enforced`,
    `appeal_submitted`, and `appeal_decided` are listed. This mirrors
    eligibility-service's own precedent (`create_eligibility_rule`:
    "canon defines no domain event for rule creation itself") for a real
    state change that is not itself one of the pack's named events.

    Unlike `create_eligibility_rule`, though, this command is still
    audited: every command in this service (including this one) accepts
    an `event_id` idempotency key, so - unlike
    `create_eligibility_rule`, which has no per-call id to key
    `append_audit_event`'s own idempotency off and therefore skips Audit
    Core entirely - there is a natural `audit_event_id` to use here even
    though there is no `EventEnvelope` to carry alongside it. Only the
    `ModerationCase` update and the `AuditEvent` are real outputs;
    `ProposeActionResult` has no `event` field.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to propose a moderation action")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        case = case_store.get(moderation_case_id)
        if case is None:
            raise UnknownModerationCaseError(f"unknown moderation_case_id: {moderation_case_id}")
        return ProposeActionResult(case=case, audit_event=existing_audit)

    case = case_store.get(moderation_case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {moderation_case_id}")

    before_hash = compute_payload_hash(case_full_state_payload(case))
    updated = case.with_status(ModerationCaseStatus.ACTION_PROPOSED)
    case_store.save(updated)
    now = clock.now()
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="moderation.case_action_proposed",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="moderation_case",
            target_id=updated.moderation_case_id,
            action="propose_action",
            reason_code=_CASE_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(case_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return ProposeActionResult(case=updated, audit_event=audit_event)


def issue_decision(
    case_store: ModerationCaseStore,
    decision_store: ModerationDecisionStore,
    audit_store: AuditEventStore,
    *,
    moderation_case_id: UUID,
    moderation_decision_id: UUID,
    decision_type: ModerationDecisionType,
    reason_code: str,
    policy_reference: str,
    decided_by: UUID,
    effective_from: datetime,
    effective_until: datetime | None,
    public_explanation: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DecisionResult:
    """`action_proposed -> decided` on the case; creates the immutable
    `ModerationDecision` record. Emits `moderation.decision_issued`.

    `reason_code` here is the *decision's own* domain field (canon
    section 14.2 - e.g. `"MODERATION_POLICY_VIOLATION"`), supplied by the
    caller from the reason-code registry describing why the decision was
    made - not to be confused with this module's own `PermissionDeniedError.
    reason_code` or any other exception's `reason_code`, which describe
    failures of this API, not the substance of a decision.

    `audit_reference` (canon section 14.2) is set to
    `str(resolved_event_id)` at construction time, since that is also the
    `audit_event_id` this same call appends under - the decision's own
    record of "which audit entry documents me" is correct from the moment
    it is created, never patched in afterward (`ModerationDecision` is
    immutable; there is no patch path).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to issue a moderation decision")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        decision = decision_store.get(moderation_decision_id)
        if decision is None:
            raise UnknownModerationDecisionError(
                f"unknown moderation_decision_id: {moderation_decision_id}"
            )
        event = build_decision_issued_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DecisionResult(decision=decision, event=event, audit_event=existing_audit)

    case = case_store.get(moderation_case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {moderation_case_id}")

    now = clock.now()
    decision = ModerationDecision(
        moderation_decision_id=moderation_decision_id,
        case_id=moderation_case_id,
        decision_type=decision_type,
        reason_code=reason_code,
        policy_reference=policy_reference,
        decided_by=decided_by,
        effective_from=effective_from,
        effective_until=effective_until,
        public_explanation=public_explanation,
        audit_reference=str(resolved_event_id),
    )
    stored_decision = decision_store.create(decision)
    updated_case = case.with_status(ModerationCaseStatus.DECIDED)
    case_store.save(updated_case)
    event = build_decision_issued_event(
        event_id=resolved_event_id,
        decision=stored_decision,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="moderation_decision",
            target_id=stored_decision.moderation_decision_id,
            action="issue_decision",
            reason_code=_DECISION_ISSUED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(decision_state_payload(stored_decision)),
        ),
        clock=clock,
    )
    return DecisionResult(decision=stored_decision, event=event, audit_event=audit_event)


def enforce_decision(
    case_store: ModerationCaseStore,
    decision_store: ModerationDecisionStore,
    audit_store: AuditEventStore,
    *,
    moderation_decision_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> EnforceDecisionResult:
    """Record that an already-issued `ModerationDecision` has been
    carried out (e.g. content actually hidden/restored). Emits
    `moderation.decision_enforced`.

    Deliberately does NOT transition `ModerationCase.status` any further:
    the case remains `decided`. `ModerationDecision` itself has no
    mutable "enforced" flag in canon's field list (section 14.2) -
    enforcement is recorded purely as an event + audit entry, not as a
    state change to either owned entity, so `before_hash`/`after_hash`
    below are equal by construction (still meaningful tamper-evidence:
    it shows the decision record was untouched at the moment enforcement
    was recorded).

    Judgment call (documented per this pack's own instructions): an
    alternative design considered also transitioning `decided -> closed`
    here when no appeal is expected to follow. That is rejected: it would
    make a later `submit_appeal` (which requires the case to still be
    `decided` - see `domain.CASE_ALLOWED_TRANSITIONS`) impossible for any
    case whose decision was ever enforced, even though canon gives no
    reason enforcement and appeal-eligibility should be coupled that way
    - in practice, an appeal typically follows a decision that has
    *already* taken effect. This pack therefore never auto-closes a case
    from `enforce_decision`; the only wired path to `closed` is
    `decided -> appealed -> closed`, via `submit_appeal` + `decide_appeal`.
    The domain-legal `decided -> closed` DIRECT transition (a case closed
    with no appeal at all) has no dedicated application-layer command in
    this pack - canon names no such command, and this pack's own Step 4
    command list does not list one either; it remains reachable only via
    `ModerationCase.with_status` directly, tested at the domain layer
    (`tests/test_domain.py`), not exposed as a command here. See
    README.md's "Known gaps" section.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to enforce a moderation decision")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        decision = decision_store.get(moderation_decision_id)
        if decision is None:
            raise UnknownModerationDecisionError(
                f"unknown moderation_decision_id: {moderation_decision_id}"
            )
        case = case_store.get(decision.case_id)
        if case is None:
            raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")
        event = build_decision_enforced_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return EnforceDecisionResult(
            decision=decision, case=case, event=event, audit_event=existing_audit
        )

    decision = decision_store.get(moderation_decision_id)
    if decision is None:
        raise UnknownModerationDecisionError(
            f"unknown moderation_decision_id: {moderation_decision_id}"
        )
    case = case_store.get(decision.case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")

    now = clock.now()
    event = build_decision_enforced_event(
        event_id=resolved_event_id,
        decision=decision,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    decision_payload_hash = compute_payload_hash(decision_state_payload(decision))
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="moderation_decision",
            target_id=decision.moderation_decision_id,
            action="enforce_decision",
            reason_code=_DECISION_ENFORCED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=decision_payload_hash,
            after_hash=decision_payload_hash,
        ),
        clock=clock,
    )
    return EnforceDecisionResult(decision=decision, case=case, event=event, audit_event=audit_event)


def submit_appeal(
    case_store: ModerationCaseStore,
    decision_store: ModerationDecisionStore,
    appeal_store: AppealStore,
    audit_store: AuditEventStore,
    *,
    appeal_id: UUID,
    decision_id: UUID,
    submitted_by: UUID,
    grounds: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> AppealResult:
    """`decided -> appealed` on the case; creates a new `Appeal` in
    `submitted`. Emits `moderation.appeal_submitted`.

    Open gap (documented per this pack's own instructions, Step 5): canon
    section 14.3 does not list an `appeal_deadline_at` field, so this
    command implements no `APPEAL_DEADLINE_EXPIRED` check - adding one
    would require inventing a canon field this pack was told not to
    invent silently. See README.md.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit an appeal")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        appeal = appeal_store.get(appeal_id)
        if appeal is None:
            raise UnknownAppealError(f"unknown appeal_id: {appeal_id}")
        decision = decision_store.get(appeal.decision_id)
        if decision is None:
            raise UnknownModerationDecisionError(
                f"unknown moderation_decision_id: {appeal.decision_id}"
            )
        case = case_store.get(decision.case_id)
        if case is None:
            raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")
        event = build_appeal_submitted_event(
            event_id=resolved_event_id,
            appeal=appeal,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return AppealResult(appeal=appeal, case=case, event=event, audit_event=existing_audit)

    decision = decision_store.get(decision_id)
    if decision is None:
        raise UnknownModerationDecisionError(f"unknown moderation_decision_id: {decision_id}")
    case = case_store.get(decision.case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")

    now = clock.now()
    appeal = Appeal(
        appeal_id=appeal_id,
        decision_id=decision_id,
        submitted_by=submitted_by,
        grounds=grounds,
        status=AppealStatus.SUBMITTED,
        reviewer_actor_id=None,
        result=None,
    )
    stored_appeal = appeal_store.create(appeal)
    updated_case = case.with_status(ModerationCaseStatus.APPEALED)
    case_store.save(updated_case)
    event = build_appeal_submitted_event(
        event_id=resolved_event_id,
        appeal=stored_appeal,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="appeal",
            target_id=stored_appeal.appeal_id,
            action="submit_appeal",
            reason_code=_APPEAL_STATUS_CHANGED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(appeal_full_state_payload(stored_appeal)),
        ),
        clock=clock,
    )
    return AppealResult(
        appeal=stored_appeal, case=updated_case, event=event, audit_event=audit_event
    )


def decide_appeal(
    case_store: ModerationCaseStore,
    decision_store: ModerationDecisionStore,
    appeal_store: AppealStore,
    audit_store: AuditEventStore,
    *,
    appeal_id: UUID,
    reviewer_actor_id: UUID,
    outcome: AppealStatus,
    result: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DecideAppealResult:
    """Move an `Appeal` from `submitted` through `admissibility_review`
    and `under_review` to `outcome` (one of `domain.FINAL_APPEAL_OUTCOMES`
    - `upheld`/`partially_upheld`/`rejected`), then close the associated
    `ModerationCase` (`appealed -> closed`). Emits
    `moderation.appeal_decided`.

    THIS IS THE SINGLE MOST IMPORTANT CHECK IN THIS SERVICE (CT-00-06;
    canon section 14.3: "Апелляцию не должен окончательно рассматривать
    автор исходного решения" - an appeal must not be finally decided by
    the author of the original decision). It is the one hard, tested
    precondition that makes ADR-005's consolidation of "Moderation
    Service" and "Appeal Service" into one physical package safe:
    `reviewer_actor_id` MUST differ from the original `ModerationDecision.
    decided_by`. This is checked before any transition is attempted,
    immediately after this call resolves the real `Appeal`/
    `ModerationDecision` records. A genuine idempotent replay of an
    already-recorded `event_id` does return earlier, via the cached-result
    branch below - but that branch can only ever return a result that
    already passed this exact check the first time it was computed: this
    check itself is never skipped for a call carrying a new
    (not-yet-recorded) `event_id`, so a permission failure can never be
    masked by, or hidden behind, a successful replay.

    `outcome=withdrawn` is intentionally rejected here (see
    `domain.FINAL_APPEAL_OUTCOMES`, which excludes `WITHDRAWN`): a
    withdrawal is submitter-initiated, not a reviewer decision outcome,
    and this pack's own Step 4 command list names no dedicated
    `withdraw_appeal` command. The domain-legal withdrawal transitions
    (`submitted`/`admissibility_review`/`under_review` -> `withdrawn`,
    see `domain.APPEAL_ALLOWED_TRANSITIONS`) remain reachable via
    `Appeal.with_status` directly and are tested at the domain layer, but
    have no dedicated application-layer command/event in this pack - see
    README.md's "Known gaps" section.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to decide an appeal")

    if outcome not in FINAL_APPEAL_OUTCOMES:
        raise ValueError(
            f"outcome must be one of {sorted(o.value for o in FINAL_APPEAL_OUTCOMES)}, "
            f"got {outcome.value!r}"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        appeal = appeal_store.get(appeal_id)
        if appeal is None:
            raise UnknownAppealError(f"unknown appeal_id: {appeal_id}")
        decision = decision_store.get(appeal.decision_id)
        if decision is None:
            raise UnknownModerationDecisionError(
                f"unknown moderation_decision_id: {appeal.decision_id}"
            )
        case = case_store.get(decision.case_id)
        if case is None:
            raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")
        event = build_appeal_decided_event(
            event_id=resolved_event_id,
            appeal=appeal,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DecideAppealResult(appeal=appeal, case=case, event=event, audit_event=existing_audit)

    appeal = appeal_store.get(appeal_id)
    if appeal is None:
        raise UnknownAppealError(f"unknown appeal_id: {appeal_id}")

    decision = decision_store.get(appeal.decision_id)
    if decision is None:
        raise UnknownModerationDecisionError(
            f"unknown moderation_decision_id: {appeal.decision_id}"
        )

    # CT-00-06: the load-bearing role-separation check. Must happen
    # before any mutation to either `Appeal` or `ModerationCase`.
    if reviewer_actor_id == decision.decided_by:
        raise PermissionDeniedError(
            "an appeal must not be finally decided by the actor who made the "
            "original moderation decision (canon section 14.3)"
        )

    case = case_store.get(decision.case_id)
    if case is None:
        raise UnknownModerationCaseError(f"unknown moderation_case_id: {decision.case_id}")

    before_hash = compute_payload_hash(appeal_full_state_payload(appeal))

    # Walk submitted -> admissibility_review -> under_review -> outcome,
    # each hop separately validated by `assert_appeal_transition_allowed`
    # inside `with_reviewer_and_status` (CT-00-03).
    stage_1 = appeal.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id,
        new_status=AppealStatus.ADMISSIBILITY_REVIEW,
        result=None,
    )
    stage_2 = stage_1.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id,
        new_status=AppealStatus.UNDER_REVIEW,
        result=None,
    )
    final_appeal = stage_2.with_reviewer_and_status(
        reviewer_actor_id=reviewer_actor_id,
        new_status=outcome,
        result=result,
    )
    appeal_store.save(final_appeal)
    updated_case = case.with_status(ModerationCaseStatus.CLOSED)
    case_store.save(updated_case)

    now = clock.now()
    event = build_appeal_decided_event(
        event_id=resolved_event_id,
        appeal=final_appeal,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="appeal",
            target_id=final_appeal.appeal_id,
            action="decide_appeal",
            reason_code=_APPEAL_DECIDED,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(appeal_full_state_payload(final_appeal)),
        ),
        clock=clock,
    )
    return DecideAppealResult(
        appeal=final_appeal, case=updated_case, event=event, audit_event=audit_event
    )


def get_moderation_decision(
    store: ModerationDecisionStore, *, moderation_decision_id: UUID
) -> ModerationDecision | None:
    """Plain, unaudited read of one `ModerationDecision` by id.

    Added under ADR-012 ("PACK-04 cross-pack read boundary"), which names
    `epd2_moderation_service.application` (never `.storage`/`.domain`) as
    the only authorized way `transparency-service` may read
    `ModerationDecision` records for `PublicLedgerEntry.subject_type =
    "moderation_decision"` (canon section 19a.5). Additive; does not
    change any existing function's signature or behavior.
    """
    return store.get(moderation_decision_id)

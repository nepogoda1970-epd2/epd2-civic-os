"""Canonical events emitted by Moderation Service.

Verbatim event-name list, `docs/handover/PACK-03-SPEC.md` section 5 /
canon section 20.9: `moderation.case_opened`, `moderation.case_assigned`,
`moderation.decision_issued`, `moderation.decision_enforced`,
`moderation.appeal_submitted`, `moderation.appeal_decided`.

No domain event exists for the `under_review -> action_proposed`
transition alone (`application.propose_action`) — this pack's own
canonical event-name list above does not name one. This mirrors
eligibility-service's `create_eligibility_rule` precedent of a real,
audited state change that is not itself one of the pack's named domain
events; see `application.propose_action`'s own docstring for the specific
way this pack still audits that step despite the missing `EventEnvelope`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_moderation_service.domain import Appeal, ModerationCase, ModerationDecision

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def case_state_payload(case: ModerationCase) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of a
    `ModerationCase`'s state, used for `moderation.case_opened`/
    `moderation.case_assigned` payloads. Deliberately excludes
    `opened_by`/`trigger_type`/`policy_version` — see
    `case_full_state_payload` for Audit Core's `before_hash`/`after_hash`,
    which needs the complete state to be a meaningful tamper-evidence
    check."""
    return {
        "moderation_case_id": str(case.moderation_case_id),
        "target_type": case.target_type,
        "target_id": str(case.target_id),
        "status": case.status.value,
        "assigned_moderator": (
            str(case.assigned_moderator) if case.assigned_moderator is not None else None
        ),
    }


def case_full_state_payload(case: ModerationCase) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ModerationCase`'s own
    state, used for Audit Core's `before_hash`/`after_hash`
    (`application.py`)."""
    payload = case_state_payload(case)
    payload.update(
        {
            "opened_by": str(case.opened_by),
            "trigger_type": case.trigger_type,
            "policy_version": case.policy_version,
        }
    )
    return payload


def decision_state_payload(decision: ModerationDecision) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ModerationDecision`'s own
    state — used both as the `moderation.decision_issued`/
    `moderation.decision_enforced` event payload and Audit Core's
    `after_hash`. Unlike `ModerationCase`/`Appeal` above/below, there is
    no separate "minimal" variant: `ModerationDecision` is immutable and
    already small, so its complete state is the natural event payload."""
    return {
        "moderation_decision_id": str(decision.moderation_decision_id),
        "case_id": str(decision.case_id),
        "decision_type": decision.decision_type.value,
        "reason_code": decision.reason_code,
        "policy_reference": decision.policy_reference,
        "decided_by": str(decision.decided_by),
        "effective_from": decision.effective_from.isoformat(),
        "effective_until": (
            decision.effective_until.isoformat() if decision.effective_until is not None else None
        ),
        "public_explanation": decision.public_explanation,
        "audit_reference": decision.audit_reference,
    }


def appeal_state_payload(appeal: Appeal) -> dict[str, object]:
    """Minimal, canonically-hashable event-payload snapshot of an
    `Appeal`'s state, used for `moderation.appeal_submitted`/
    `moderation.appeal_decided` payloads. Deliberately excludes
    `submitted_by`/`grounds` — see `appeal_full_state_payload` for Audit
    Core's `before_hash`/`after_hash`."""
    return {
        "appeal_id": str(appeal.appeal_id),
        "decision_id": str(appeal.decision_id),
        "status": appeal.status.value,
        "reviewer_actor_id": (
            str(appeal.reviewer_actor_id) if appeal.reviewer_actor_id is not None else None
        ),
        "result": appeal.result,
    }


def appeal_full_state_payload(appeal: Appeal) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `Appeal`'s own state,
    used for Audit Core's `before_hash`/`after_hash` (`application.py`)."""
    payload = appeal_state_payload(appeal)
    payload.update(
        {
            "submitted_by": str(appeal.submitted_by),
            "grounds": appeal.grounds,
        }
    )
    return payload


def build_case_opened_event(
    *,
    event_id: UUID,
    case: ModerationCase,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.case_opened",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(subject_type="moderation_case", subject_id=case.moderation_case_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=case_state_payload(case),
    )


def build_case_assigned_event(
    *,
    event_id: UUID,
    case: ModerationCase,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.case_assigned",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(subject_type="moderation_case", subject_id=case.moderation_case_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=case_state_payload(case),
    )


def build_decision_issued_event(
    *,
    event_id: UUID,
    decision: ModerationDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.decision_issued",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="moderation_decision", subject_id=decision.moderation_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=decision_state_payload(decision),
    )


def build_decision_enforced_event(
    *,
    event_id: UUID,
    decision: ModerationDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.decision_enforced",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="moderation_decision", subject_id=decision.moderation_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=decision_state_payload(decision),
    )


def build_appeal_submitted_event(
    *,
    event_id: UUID,
    appeal: Appeal,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.appeal_submitted",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(subject_type="appeal", subject_id=appeal.appeal_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=appeal_state_payload(appeal),
    )


def build_appeal_decided_event(
    *,
    event_id: UUID,
    appeal: Appeal,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="moderation.appeal_decided",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="moderation-service",
        actor=actor,
        subject=SubjectRef(subject_type="appeal", subject_id=appeal.appeal_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=appeal_state_payload(appeal),
    )

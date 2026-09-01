"""Canonical events emitted by Governance Service.

Verbatim event-name list, canon section 20.15 (added by canon 0.4.0,
ADR-018): `governance.role_assignment_requested`,
`governance.role_assignment_activated`, `governance.role_assignment_revoked`,
`governance.policy_proposed`, `governance.policy_activated`,
`governance.policy_superseded`, `governance.decision_proposed`,
`governance.decision_approved`, `governance.decision_rejected`,
`governance.decision_superseded`, `governance.technical_challenge_submitted`,
`governance.technical_challenge_adjudicated`.

`governance.decision_superseded` is emitted when a new, superseding
decision is *approved* with `supersedes_decision_id` set — never when the
superseded record's own status changes (canon 20.15: it never does).

This module is also where canon section 19b's "never published verbatim"
rules are actually drawn:

- `proposed_by_role_id`/`approved_by_role_id`/`rejected_by_role_id`/
  `assigned_by` are omitted entirely from every `*_public_payload`
  (mirrors `epd2_transparency_service.events`' own `*_role_id` omission
  convention for the equivalent canon 19a.6 rule).
- `RoleAssignment.actor_id` is likewise omitted from its own public
  payload — a `RoleAssignment` is internal authority-plumbing; no
  external event payload in this pack ever needs to reveal which actor
  holds which role.
- `TechnicalChallenge.submitter_authorization_reference` is omitted
  entirely (canon 19b.4: never published in original form; no
  generalized-label substitute field exists yet in this pack's scope).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_governance_service.domain import (
    GovernanceDecision,
    GovernancePolicy,
    RoleAssignment,
    TechnicalChallenge,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


# ---------------------------------------------------------------------------
# RoleAssignment payloads/events
# ---------------------------------------------------------------------------


def role_assignment_public_payload(assignment: RoleAssignment) -> dict[str, object]:
    """Public event payload for a `RoleAssignment` — omits `actor_id`
    and `assigned_by` entirely."""
    return {
        "role_assignment_id": str(assignment.role_assignment_id),
        "role_code": assignment.role_code,
        "scope_id": str(assignment.scope_id),
        "valid_from": assignment.valid_from.isoformat(),
        "valid_until": (
            assignment.valid_until.isoformat() if assignment.valid_until is not None else None
        ),
        "approval_reference": assignment.approval_reference,
        "status": assignment.status.value,
    }


def role_assignment_full_state_payload(assignment: RoleAssignment) -> dict[str, object]:
    """Full snapshot including `actor_id`/`assigned_by`, used only for
    Audit Core's `before_hash`/`after_hash`."""
    payload = role_assignment_public_payload(assignment)
    payload["actor_id"] = str(assignment.actor_id)
    payload["assigned_by"] = str(assignment.assigned_by)
    return payload


def build_role_assignment_requested_event(
    *,
    event_id: UUID,
    assignment: RoleAssignment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.role_assignment_requested",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="role_assignment", subject_id=assignment.role_assignment_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=role_assignment_public_payload(assignment),
    )


def build_role_assignment_activated_event(
    *,
    event_id: UUID,
    assignment: RoleAssignment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.role_assignment_activated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="role_assignment", subject_id=assignment.role_assignment_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=role_assignment_public_payload(assignment),
    )


def build_role_assignment_revoked_event(
    *,
    event_id: UUID,
    assignment: RoleAssignment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.role_assignment_revoked",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="role_assignment", subject_id=assignment.role_assignment_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=role_assignment_public_payload(assignment),
    )


# ---------------------------------------------------------------------------
# GovernancePolicy payloads/events
# ---------------------------------------------------------------------------


def governance_policy_public_payload(policy: GovernancePolicy) -> dict[str, object]:
    """Public event payload for a `GovernancePolicy` — omits
    `proposed_by_role_id`/`approved_by_role_id` entirely (canon 19b.2)."""
    return {
        "governance_policy_id": str(policy.governance_policy_id),
        "policy_type": policy.policy_type.value,
        "rule_definition": dict(policy.rule_definition),
        "effective_from": policy.effective_from.isoformat(),
        "version": policy.version,
        "status": policy.status.value,
    }


def governance_policy_full_state_payload(policy: GovernancePolicy) -> dict[str, object]:
    """Full snapshot including `proposed_by_role_id`/`approved_by_role_id`,
    used only for Audit Core's `before_hash`/`after_hash`."""
    payload = governance_policy_public_payload(policy)
    payload["proposed_by_role_id"] = str(policy.proposed_by_role_id)
    payload["approved_by_role_id"] = str(policy.approved_by_role_id)
    return payload


def build_policy_proposed_event(
    *,
    event_id: UUID,
    policy: GovernancePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.policy_proposed",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_policy", subject_id=policy.governance_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_policy_public_payload(policy),
    )


def build_policy_activated_event(
    *,
    event_id: UUID,
    policy: GovernancePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.policy_activated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_policy", subject_id=policy.governance_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_policy_public_payload(policy),
    )


def build_policy_superseded_event(
    *,
    event_id: UUID,
    policy: GovernancePolicy,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.policy_superseded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_policy", subject_id=policy.governance_policy_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_policy_public_payload(policy),
    )


# ---------------------------------------------------------------------------
# GovernanceDecision payloads/events
# ---------------------------------------------------------------------------


def governance_decision_public_payload(decision: GovernanceDecision) -> dict[str, object]:
    """Public event payload for a `GovernanceDecision` — omits
    `proposed_by_role_id`/`approved_by_role_id`/`rejected_by_role_id`
    entirely (canon 19b.3)."""
    return {
        "governance_decision_id": str(decision.governance_decision_id),
        "decision_type": decision.decision_type.value,
        "subject_reference": dict(decision.subject_reference),
        "reason_code": decision.reason_code,
        "evidence_references": list(decision.evidence_references),
        "finality_outcome": (
            decision.finality_outcome.value if decision.finality_outcome is not None else None
        ),
        "created_at": decision.created_at.isoformat(),
        "decided_at": decision.decided_at.isoformat() if decision.decided_at is not None else None,
        "supersedes_decision_id": (
            str(decision.supersedes_decision_id)
            if decision.supersedes_decision_id is not None
            else None
        ),
        "status": decision.status.value,
    }


def governance_decision_full_state_payload(decision: GovernanceDecision) -> dict[str, object]:
    """Full snapshot including `proposed_by_role_id`/
    `approved_by_role_id`/`rejected_by_role_id`, used only for Audit
    Core's `before_hash`/`after_hash`."""
    payload = governance_decision_public_payload(decision)
    payload["proposed_by_role_id"] = str(decision.proposed_by_role_id)
    payload["approved_by_role_id"] = (
        str(decision.approved_by_role_id) if decision.approved_by_role_id is not None else None
    )
    payload["rejected_by_role_id"] = (
        str(decision.rejected_by_role_id) if decision.rejected_by_role_id is not None else None
    )
    return payload


def build_decision_proposed_event(
    *,
    event_id: UUID,
    decision: GovernanceDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.decision_proposed",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_decision", subject_id=decision.governance_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_decision_public_payload(decision),
    )


def build_decision_approved_event(
    *,
    event_id: UUID,
    decision: GovernanceDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.decision_approved",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_decision", subject_id=decision.governance_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_decision_public_payload(decision),
    )


def build_decision_rejected_event(
    *,
    event_id: UUID,
    decision: GovernanceDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.decision_rejected",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_decision", subject_id=decision.governance_decision_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=governance_decision_public_payload(decision),
    )


def build_decision_superseded_event(
    *,
    event_id: UUID,
    superseded_decision: GovernanceDecision,
    superseding_decision: GovernanceDecision,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Canon 20.15: emitted when `superseding_decision` (already
    `approved`, with `supersedes_decision_id ==
    superseded_decision.governance_decision_id`) is recorded — never in
    response to any change to `superseded_decision` itself, which never
    changes (19b.3)."""
    payload = governance_decision_public_payload(superseded_decision)
    payload["superseded_by_decision_id"] = str(superseding_decision.governance_decision_id)
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.decision_superseded",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="governance_decision",
            subject_id=superseded_decision.governance_decision_id,
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# TechnicalChallenge payloads/events
# ---------------------------------------------------------------------------


def technical_challenge_public_payload(challenge: TechnicalChallenge) -> dict[str, object]:
    """Public event payload for a `TechnicalChallenge` — omits
    `submitter_authorization_reference` entirely in every case (canon
    19b.4: never published in original form; this pack defines no
    generalized-label substitute field)."""
    return {
        "technical_challenge_id": str(challenge.technical_challenge_id),
        "result_publication_id": str(challenge.result_publication_id),
        "submitter_authorization_type": challenge.submitter_authorization_type.value,
        "challenge_reason_code": challenge.challenge_reason_code,
        "evidence_references": list(challenge.evidence_references),
        "submitted_at": challenge.submitted_at.isoformat(),
        "governance_decision_id": (
            str(challenge.governance_decision_id)
            if challenge.governance_decision_id is not None
            else None
        ),
        "status": challenge.status.value,
    }


def technical_challenge_full_state_payload(challenge: TechnicalChallenge) -> dict[str, object]:
    """Full snapshot including `submitter_authorization_reference`,
    used only for Audit Core's `before_hash`/`after_hash` — this value
    stays restricted even there (never appears in any *public* event or
    payload; the audit trail is itself an internal, non-public record)."""
    payload = technical_challenge_public_payload(challenge)
    payload["submitter_authorization_reference"] = challenge.submitter_authorization_reference
    return payload


def build_technical_challenge_submitted_event(
    *,
    event_id: UUID,
    challenge: TechnicalChallenge,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.technical_challenge_submitted",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="technical_challenge", subject_id=challenge.technical_challenge_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=technical_challenge_public_payload(challenge),
    )


def build_technical_challenge_adjudicated_event(
    *,
    event_id: UUID,
    challenge: TechnicalChallenge,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    return build_event_envelope(
        event_id=event_id,
        event_type="governance.technical_challenge_adjudicated",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="governance-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="technical_challenge", subject_id=challenge.technical_challenge_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=technical_challenge_public_payload(challenge),
    )

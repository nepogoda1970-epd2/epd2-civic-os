"""Canonical events emitted by Organization Service (canon section 20.5,
19e.20; PACK-08 implementation round). Thirteen events total:
`organization.created` (pre-existing canon name, first real
implementation) plus the twelve events canon 0.7.0 added
(`organization.activated`/`.suspended`/`.dissolved`/`.merged`/`.split`/
`.successor_declared`, `organizational_relation.created`/`.ended`,
`organizational_authority.assigned`/`.revoked`,
`regional_scope_access.granted`/`.revoked`).

Per 19e.20's minimum/prohibited payload rule: every payload below carries
only the changed record's identifier, its new status, `effective_time`
(the record's own `valid_from`), and - where applicable - a
`decision_reference` and/or exactly one reason code. No raw name/identity
of any person, no full multi-party actor list, and no
voting-service/tally-service/VoteEnvelope field ever appears."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_organization_service.domain import (
    Organization,
    OrganizationalAuthority,
    OrganizationalRelation,
    RegionalScopeAccessDecision,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})


def organization_state_payload(organization: Organization) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `Organization`'s own
    state, used for Audit Core's `after_hash` - never broadcast on a wire
    event payload directly (mirrors every prior pack's own
    disclosure-by-default discipline)."""
    return {
        "organization_id": str(organization.organization_id),
        "name": organization.name,
        "legal_operator": organization.legal_operator,
        "organization_type": organization.organization_type,
        "status": organization.status.value,
        "default_policy_version": organization.default_policy_version,
        "organization_profile": organization.organization_profile,
        "effective_from": organization.effective_from.isoformat(),
        "effective_until": (
            organization.effective_until.isoformat() if organization.effective_until else None
        ),
        "dissolved_at": (
            organization.dissolved_at.isoformat() if organization.dissolved_at else None
        ),
        "successor_reference": (
            str(organization.successor_reference) if organization.successor_reference else None
        ),
        "parent_reference": (
            str(organization.parent_reference) if organization.parent_reference else None
        ),
    }


def relation_state_payload(relation: OrganizationalRelation) -> dict[str, object]:
    return {
        "relation_id": str(relation.relation_id),
        "relation_version": relation.relation_version,
        "relation_type": relation.relation_type.value,
        "relation_category": relation.relation_category.value,
        "source_organization_id": str(relation.source_organization_id),
        "target_organization_id": str(relation.target_organization_id),
        "status": relation.status.value,
        "valid_from": relation.valid_from.isoformat(),
        "valid_until": relation.valid_until.isoformat() if relation.valid_until else None,
        "supersedes_relation_id": (
            str(relation.supersedes_relation_id) if relation.supersedes_relation_id else None
        ),
        "authorizing_decision_reference": (
            str(relation.authorizing_decision_reference)
            if relation.authorizing_decision_reference
            else None
        ),
    }


def authority_state_payload(authority: OrganizationalAuthority) -> dict[str, object]:
    return {
        "authority_id": str(authority.authority_id),
        "authority_version": authority.authority_version,
        "role_code": authority.role_code,
        "scope_type": authority.scope.scope_type.value,
        "scope_reference": authority.scope.scope_reference,
        "assigned_subject_reference": str(authority.assigned_subject_reference),
        "valid_from": authority.valid_from.isoformat(),
        "valid_until": authority.valid_until.isoformat() if authority.valid_until else None,
        "status": authority.status.value,
        "policy_version": authority.policy_version,
        "decision_reference": str(authority.decision_reference),
        "revocation_reason_reference": authority.revocation_reason_reference,
        "grants_procedural_authority": authority.grants_procedural_authority,
        "grants_data_access": authority.grants_data_access,
    }


def _organization_event(
    *,
    event_type: str,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID | None = None,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "organization_id": str(organization.organization_id),
        "status": organization.status.value,
        "effective_time": organization.effective_from.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    if decision_reference is not None:
        payload["decision_reference"] = str(decision_reference)
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(subject_type="organization", subject_id=organization.organization_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_organization_created_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.created",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_activated_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.activated",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_suspended_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.suspended",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_dissolved_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.dissolved",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_merged_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.merged",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_split_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.split",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organization_successor_declared_event(
    *,
    event_id: UUID,
    organization: Organization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
    decision_reference: UUID,
) -> EventEnvelope:
    return _organization_event(
        event_type="organization.successor_declared",
        event_id=event_id,
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
        decision_reference=decision_reference,
    )


def build_organizational_relation_created_event(
    *,
    event_id: UUID,
    relation: OrganizationalRelation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "relation_id": str(relation.relation_id),
        "relation_type": relation.relation_type.value,
        "relation_category": relation.relation_category.value,
        "status": relation.status.value,
        "effective_time": relation.valid_from.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    if relation.authorizing_decision_reference is not None:
        payload["decision_reference"] = str(relation.authorizing_decision_reference)
    return build_event_envelope(
        event_id=event_id,
        event_type="organizational_relation.created",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(subject_type="organizational_relation", subject_id=relation.relation_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_organizational_relation_ended_event(
    *,
    event_id: UUID,
    relation: OrganizationalRelation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "relation_id": str(relation.relation_id),
        "status": relation.status.value,
        "effective_time": (
            relation.valid_until.isoformat() if relation.valid_until else occurred_at.isoformat()
        ),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="organizational_relation.ended",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(subject_type="organizational_relation", subject_id=relation.relation_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_organizational_authority_assigned_event(
    *,
    event_id: UUID,
    authority: OrganizationalAuthority,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "authority_id": str(authority.authority_id),
        "status": authority.status.value,
        "policy_version": authority.policy_version,
        "decision_reference": str(authority.decision_reference),
        "effective_time": authority.valid_from.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="organizational_authority.assigned",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="organizational_authority", subject_id=authority.authority_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_organizational_authority_revoked_event(
    *,
    event_id: UUID,
    authority: OrganizationalAuthority,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "authority_id": str(authority.authority_id),
        "status": authority.status.value,
        "revocation_reason_reference": authority.revocation_reason_reference,
        "policy_version": authority.policy_version,
        "effective_time": occurred_at.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="organizational_authority.revoked",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(
            subject_type="organizational_authority", subject_id=authority.authority_id
        ),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_regional_scope_access_granted_event(
    *,
    event_id: UUID,
    decision: RegionalScopeAccessDecision,
    actor: ActorRef,
    subject_id: UUID,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Created only for modes 2-5 (ancestor/descendant/delegated/temporary
    supervision) - mode 1 (exact-scope, the default) and mode 6
    (institutional oversight without data access, which grants no data
    access by definition) never create this event (canon 19e.20)."""
    payload: dict[str, object] = {
        "scope_type": decision.evaluated_scope.scope_type.value,
        "scope_reference": decision.evaluated_scope.scope_reference,
        "mode": decision.mode.value if decision.mode else None,
        "policy_version": decision.policy_version,
        "effective_time": decision.effective_time.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="regional_scope_access.granted",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(subject_type="regional_scope_access", subject_id=subject_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )


def build_regional_scope_access_revoked_event(
    *,
    event_id: UUID,
    scope: object,
    subject_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    payload: dict[str, object] = {
        "effective_time": occurred_at.isoformat(),
        "recorded_at": occurred_at.isoformat(),
    }
    return build_event_envelope(
        event_id=event_id,
        event_type="regional_scope_access.revoked",
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer="organization-service",
        actor=actor,
        subject=SubjectRef(subject_type="regional_scope_access", subject_id=subject_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=payload,
    )

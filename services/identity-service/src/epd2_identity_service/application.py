"""Identity Service application layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_identity_service.domain import (
    CANONICAL_EVENT_FOR_TRANSITION,
    AuthenticationAssuranceLevel,
    AuthenticationContext,
    IdentityAssuranceLevel,
    IdentityParticipationClaims,
    IdentityRecord,
    StepUpSatisfactionResult,
    VerificationStatus,
    assert_transition_allowed,
    evaluate_identity_participation_claims,
    evaluate_step_up_satisfaction,
)
from epd2_identity_service.events import (
    authentication_context_payload,
    build_authentication_context_event,
    build_identity_event,
    identity_record_payload,
)
from epd2_identity_service.exceptions import (
    UnknownAuthenticationContextError,
    UnknownIdentityRecordError,
)
from epd2_identity_service.storage import AuthenticationContextStore, IdentityRecordStore

#: Audit Core's own policy version for entries this service appends -
#: independent of the wire event schema version.
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "identity-service"
_TARGET_TYPE = "identity_record"

#: Audit reason_code by verification outcome, for `record_verification_result`.
#: See ADR-004 - VERIFIED/FAILED/EXPIRED reuse existing registry codes;
#: DUPLICATE_SUSPECTED/MANUAL_REVIEW_REQUIRED are new audit-only
#: classifications with no existing refusal code to reuse.
_AUDIT_REASON_FOR_OUTCOME: dict[VerificationStatus, str] = {
    VerificationStatus.VERIFIED: "IDENTITY_VERIFIED",
    VerificationStatus.FAILED: "IDENTITY_NOT_VERIFIED",
    VerificationStatus.EXPIRED: "IDENTITY_VERIFICATION_EXPIRED",
    VerificationStatus.DUPLICATE_SUSPECTED: "IDENTITY_DUPLICATE_SUSPECTED",
    VerificationStatus.MANUAL_REVIEW_REQUIRED: "IDENTITY_MANUAL_REVIEW_REQUIRED",
}


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class CommandResult:
    record: IdentityRecord
    event: EventEnvelope | None
    audit_event: AuditEvent | None = None


def start_identity_verification(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    account_id: UUID,
    verification_provider: str,
    verification_level: str,
    country: str,
    provider_reference: str,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> CommandResult:
    """Create a new `IdentityRecord` in `pending` status and emit
    `identity.verification_started`."""
    now = clock.now()
    record = IdentityRecord(
        identity_record_id=generate_uuid(),
        account_id=account_id,
        verification_provider=verification_provider,
        verification_level=verification_level,
        verification_status=VerificationStatus.PENDING,
        verified_at=None,
        expires_at=None,
        country=country,
        duplicate_check_status="not_checked",
        provider_reference=provider_reference,
    )
    store.save(record)
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type="identity.verification_started",
        record=record,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: starting an identity verification process is a
    # critical action for this service's own owned entity.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=record.identity_record_id,
            action="start_verification",
            reason_code="IDENTITY_VERIFICATION_STARTED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(identity_record_payload(record)),
        ),
        clock=clock,
    )
    return CommandResult(record=record, event=event, audit_event=audit_event)


def record_verification_result(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    identity_record_id: UUID,
    outcome: VerificationStatus,
    expires_at: datetime | None,
    duplicate_check_status: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Record the outcome of a verification attempt (CT-00-06: rejected if
    the actor is not authorized)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record a verification result")

    record = store.get(identity_record_id)
    if record is None:
        raise UnknownIdentityRecordError(f"unknown identity_record_id: {identity_record_id}")

    before_hash = compute_payload_hash(identity_record_payload(record))
    now = clock.now()
    previous_status = record.verification_status
    assert_transition_allowed(previous_status, outcome)
    updated = record.with_status(
        outcome,
        verified_at=now if outcome == VerificationStatus.VERIFIED else None,
        expires_at=expires_at,
        duplicate_check_status=duplicate_check_status,
    )
    store.save(updated)

    event_type = CANONICAL_EVENT_FOR_TRANSITION[(previous_status, outcome)]
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type=event_type,
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: recording a verification outcome is a critical
    # action. `reason_code` is classified by outcome (ADR-004).
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=updated.identity_record_id,
            action="record_verification_result",
            reason_code=_AUDIT_REASON_FOR_OUTCOME[outcome],
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(identity_record_payload(updated)),
        ),
        clock=clock,
    )
    return CommandResult(record=updated, event=event, audit_event=audit_event)


def revoke_verification(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    identity_record_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Explicitly revoke a `verified` record. Per ADR-002, this emits the
    canonical `identity.verification_expired` event (canon has no separate
    revocation event) - the audit trail's `reason_code` still records this
    distinctly as a revocation, not a natural expiry
    (`IDENTITY_VERIFICATION_REVOKED`, see ADR-004).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to revoke a verification")

    record = store.get(identity_record_id)
    if record is None:
        raise UnknownIdentityRecordError(f"unknown identity_record_id: {identity_record_id}")

    before_hash = compute_payload_hash(identity_record_payload(record))
    assert_transition_allowed(record.verification_status, VerificationStatus.EXPIRED)
    updated = record.with_status(VerificationStatus.EXPIRED)
    store.save(updated)

    now = clock.now()
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type=CANONICAL_EVENT_FOR_TRANSITION[
            (record.verification_status, VerificationStatus.EXPIRED)
        ],
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=updated.identity_record_id,
            action="revoke_verification",
            reason_code="IDENTITY_VERIFICATION_REVOKED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(identity_record_payload(updated)),
        ),
        clock=clock,
    )
    return CommandResult(record=updated, event=event, audit_event=audit_event)


def record_identity_attributes(
    store: IdentityRecordStore,
    audit_store: AuditEventStore,
    *,
    identity_record_id: UUID,
    date_of_birth: date | None = None,
    citizenship_status: tuple[str, ...] | None = None,
    residence_status: Mapping[str, object] | None = None,
    identity_assurance_level: IdentityAssuranceLevel | None = None,
    identity_scheme: str | None = None,
    attribute_verification_level: str | None = None,
    attribute_verified_at: datetime | None = None,
    attribute_valid_until: datetime | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> CommandResult:
    """Record or refresh canon 19d.2's additive identity/attribute
    fields on an existing `IdentityRecord` (PACK-07, canon-0.6.0). A
    wholly separate concern from `verification_status`
    (`record_verification_result` above) - this command never changes
    `verification_status`/`verified_at`/`expires_at`/
    `duplicate_check_status`, and `record_verification_result` never
    changes any field this command owns (`IdentityRecord.with_status`
    vs. `.with_attributes` - see `domain.py`).

    CT-00-06: rejected if the actor is not authorized, the same gate
    every other mutating command in this service applies.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record identity attributes")

    record = store.get(identity_record_id)
    if record is None:
        raise UnknownIdentityRecordError(f"unknown identity_record_id: {identity_record_id}")

    before_hash = compute_payload_hash(identity_record_payload(record))
    updated = record.with_attributes(
        date_of_birth=date_of_birth,
        citizenship_status=citizenship_status,
        residence_status=residence_status,
        identity_assurance_level=identity_assurance_level,
        identity_scheme=identity_scheme,
        attribute_verification_level=attribute_verification_level,
        attribute_verified_at=attribute_verified_at,
        attribute_valid_until=attribute_valid_until,
    )
    store.save(updated)

    now = clock.now()
    event = build_identity_event(
        event_id=generate_uuid(),
        event_type="identity.attributes_recorded",
        record=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=_TARGET_TYPE,
            target_id=updated.identity_record_id,
            action="record_identity_attributes",
            reason_code="IDENTITY_ATTRIBUTES_RECORDED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(identity_record_payload(updated)),
        ),
        clock=clock,
    )
    return CommandResult(record=updated, event=event, audit_event=audit_event)


@dataclass(frozen=True, slots=True)
class AuthenticationContextResult:
    context: AuthenticationContext
    event: EventEnvelope
    audit_event: AuditEvent


def establish_authentication_context(
    store: AuthenticationContextStore,
    audit_store: AuditEventStore,
    *,
    account_id: UUID,
    authentication_method: str,
    authentication_assurance_level: AuthenticationAssuranceLevel,
    provider_reference: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> AuthenticationContextResult:
    """Record a new `AuthenticationContext` (canon 19d.8) for a freshly
    authenticated session. `session_authenticated_at` is always this
    command's own clock time, never caller-supplied - a session's
    authentication moment is this service's own fact, not an input to
    trust from elsewhere."""
    if not actor_is_authorized:
        raise PermissionDeniedError(
            "actor is not authorized to establish an authentication context"
        )
    now = clock.now()
    context = AuthenticationContext(
        authentication_context_id=generate_uuid(),
        account_id=account_id,
        authentication_method=authentication_method,
        authentication_assurance_level=authentication_assurance_level,
        session_authenticated_at=now,
        provider_reference=provider_reference,
        step_up_completed_at=None,
    )
    store.save(context)
    event = build_authentication_context_event(
        event_id=generate_uuid(),
        event_type="identity.authentication_context_established",
        context=context,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="authentication_context",
            target_id=context.authentication_context_id,
            action="establish_authentication_context",
            reason_code="AUTHENTICATION_CONTEXT_ESTABLISHED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(authentication_context_payload(context)),
        ),
        clock=clock,
    )
    return AuthenticationContextResult(context=context, event=event, audit_event=audit_event)


def record_step_up_completion(
    store: AuthenticationContextStore,
    audit_store: AuditEventStore,
    *,
    authentication_context_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> AuthenticationContextResult:
    """Record that step-up authentication completed for an existing
    `AuthenticationContext` (canon 19d.8's `step_up_completed_at`)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to record step-up completion")
    context = store.get(authentication_context_id)
    if context is None:
        raise UnknownAuthenticationContextError(
            f"unknown authentication_context_id: {authentication_context_id}"
        )
    before_hash = compute_payload_hash(authentication_context_payload(context))
    now = clock.now()
    updated = context.with_step_up_completed(now)
    store.save(updated)
    event = build_authentication_context_event(
        event_id=generate_uuid(),
        event_type="identity.step_up_authentication_completed",
        context=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="authentication_context",
            target_id=updated.authentication_context_id,
            action="record_step_up_completion",
            reason_code="STEP_UP_AUTHENTICATION_COMPLETED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(authentication_context_payload(updated)),
        ),
        clock=clock,
    )
    return AuthenticationContextResult(context=updated, event=event, audit_event=audit_event)


def get_authentication_context(
    store: AuthenticationContextStore, *, authentication_context_id: UUID
) -> AuthenticationContext | None:
    """Plain, unaudited read of one `AuthenticationContext` by id (ADR-008
    pattern precedent)."""
    return store.get(authentication_context_id)


# =============================================================================
# ADR-027 narrow cross-pack reads (PACK-07 implementation round). These are
# the only two `epd2_identity_service.application` functions
# `eligibility-service`/`membership-service` may import
# (`tests/repository/test_service_boundaries.py`) - unaudited, side-effect
# free reads, mirroring `verify_role_assignment_for_action`'s (ADR-022) own
# precedent: compute the check where the raw data already lives, return
# only derived booleans/reason codes, never the underlying row.
# =============================================================================


def get_identity_participation_claims(
    store: IdentityRecordStore,
    *,
    identity_record_id: UUID,
    required_identity_assurance_level: str,
    minimum_age: int | None,
    eligible_citizenship_set: tuple[str, ...],
    residence_rule: Mapping[str, object] | None,
    territorial_scope_rule: Mapping[str, object] | None,
    evaluated_at: datetime,
) -> IdentityParticipationClaims:
    """ADR-027's narrow identity-claims read. Resolves the `IdentityRecord`
    (a lookup miss is treated identically to an unverified record - fail
    closed, never an exception, since a caller polling this read is asking
    a yes/no eligibility question, not performing a CRUD read) and
    delegates to the pure `domain.evaluate_identity_participation_claims`.
    """
    record = store.get(identity_record_id)
    return evaluate_identity_participation_claims(
        record,
        required_identity_assurance_level=required_identity_assurance_level,
        minimum_age=minimum_age,
        eligible_citizenship_set=eligible_citizenship_set,
        residence_rule=residence_rule,
        territorial_scope_rule=territorial_scope_rule,
        evaluated_at=evaluated_at,
    )


def check_authentication_step_up_satisfied(
    context_store: AuthenticationContextStore,
    identity_store: IdentityRecordStore,
    *,
    authentication_context_id: UUID,
    identity_record_id: UUID,
    required_authentication_assurance_level: str,
    required_identity_assurance_level: str,
    fresh_authentication_required: bool,
    maximum_authentication_age: timedelta | None,
    required_attribute_freshness: timedelta | None,
    reauthentication_reason: str,
    evaluated_at: datetime,
) -> StepUpSatisfactionResult:
    """ADR-030 item 7's narrow step-up-satisfaction read. Resolves the
    live `AuthenticationContext` and `IdentityRecord` internally and
    delegates to the pure `domain.evaluate_step_up_satisfaction` -
    `eligibility-service`/`membership-service` never receive
    `session_authenticated_at`, `provider_reference`, or any raw
    assurance field directly (ADR-027's step-up boundary consequence).
    """
    context = context_store.get(authentication_context_id)
    record = identity_store.get(identity_record_id)
    return evaluate_step_up_satisfaction(
        context=context,
        identity_assurance_level=(record.identity_assurance_level if record else None),
        attribute_verified_at=(record.attribute_verified_at if record else None),
        required_authentication_assurance_level=required_authentication_assurance_level,
        required_identity_assurance_level=required_identity_assurance_level,
        fresh_authentication_required=fresh_authentication_required,
        maximum_authentication_age=maximum_authentication_age,
        required_attribute_freshness=required_attribute_freshness,
        reauthentication_reason=reauthentication_reason,
        evaluated_at=evaluated_at,
    )

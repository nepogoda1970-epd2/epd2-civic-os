"""Credential Service application layer: `IssueParticipationCredential`,
`ValidateParticipationCredential`, `RevokeParticipationCredential` (pack
section 6.2).
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
from epd2_credential_service.domain import (
    CURRENT_CREDENTIAL_VERSION,
    CredentialStatus,
    CredentialType,
    ParticipationCredential,
    ValidationResult,
)
from epd2_credential_service.events import (
    build_credential_issued_event,
    build_credential_revoked_event,
    build_validation_failed_event,
    credential_full_state_payload,
)
from epd2_credential_service.exceptions import UnknownCredentialError
from epd2_credential_service.storage import CredentialStore
from epd2_credential_service.validation import validate_credential

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "credential-service"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


@dataclass(frozen=True, slots=True)
class IssueResult:
    credential: ParticipationCredential
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ValidateResult:
    result: ValidationResult
    event: EventEnvelope | None


@dataclass(frozen=True, slots=True)
class RevokeResult:
    credential: ParticipationCredential
    event: EventEnvelope
    audit_event: AuditEvent


def issue_participation_credential(
    store: CredentialStore,
    audit_store: AuditEventStore,
    *,
    credential_id: UUID,
    credential_type: CredentialType,
    scope_type: str,
    scope_id: UUID,
    valid_from: datetime,
    expires_at: datetime,
    usage_limit: int | None,
    rule_version: int,
    eligibility_snapshot_digest: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> IssueResult:
    """Issue a new opaque `ParticipationCredential`.

    `issuance_reference` is generated here via `generate_uuid()` - a
    random value never derived from any identity or account data (pack
    section 13.1: no deterministic credential ids computed from identity
    data) - and is only ever passed to `store.issue`, never returned.

    `event_id` is the idempotency key for CT-00-04 at the command level:
    a caller retrying this exact command (e.g. after a network timeout on
    the first attempt's response) should pass the *same* `event_id` it
    used on the original attempt, alongside the same `credential_id` and
    content. Doing so makes both the stored credential (`CredentialStore`'s
    own content-based dedup) and the audit trail (`Audit Core`'s
    `audit_event_id`-based dedup) converge on the same single record.
    Omitting `event_id` (the default) still dedupes the *stored*
    credential correctly, but each call mints a fresh domain event and
    therefore a fresh audit entry - see
    `docs/review/OPEN_QUESTIONS.md` for why the other services' analogous
    commands do not yet accept this parameter too.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to issue a credential")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    now = clock.now()
    credential = ParticipationCredential(
        credential_id=credential_id,
        credential_type=credential_type,
        scope_type=scope_type,
        scope_id=scope_id,
        issued_at=now,
        valid_from=valid_from,
        expires_at=expires_at,
        status=CredentialStatus.ISSUED,
        usage_limit=usage_limit,
        usage_counter=0,
        revocation_status="not_revoked",
        issuer_signature=None,
        credential_version=CURRENT_CREDENTIAL_VERSION,
        rule_version=rule_version,
        eligibility_snapshot_digest=eligibility_snapshot_digest,
    )
    issuance_reference = str(generate_uuid())
    stored = store.issue(credential, issuance_reference)
    event = build_credential_issued_event(
        event_id=resolved_event_id,
        credential=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: issuing a credential is a critical, politically
    # significant action and must leave an audit trail. `audit_event_id`
    # reuses the domain event's own `event_id` so a true retry of this
    # exact command (same event_id) is idempotent at the audit layer too.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="participation_credential",
            target_id=stored.credential_id,
            action="issue",
            reason_code="CREDENTIAL_ISSUED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(credential_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return IssueResult(credential=stored, event=event, audit_event=audit_event)


def validate_participation_credential(
    store: CredentialStore,
    *,
    credential_id: UUID,
    required_scope_type: str | None,
    required_scope_id: UUID | None,
    expected_rule_version: int | None,
    expected_digest: str | None,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> ValidateResult:
    """Fail-closed validation (pack section 6.4). Emits
    `credential.validation_failed` only when invalid - a successful
    validation is a query, not a state change, and canon defines no
    "validated" event (ADR-002). Deliberately not audited via Audit Core
    either, for the same reason CT-00-07 scopes "critical action" to state
    changes: a validation attempt (successful or failed) does not alter
    `ParticipationCredential` state, so it carries no `before_hash`/
    `after_hash` to record and is not itself a politically significant
    action under INV-04 - only `issue`/`revoke` are."""
    credential = store.get(credential_id)
    now = clock.now()
    if credential is None:
        result = ValidationResult(
            valid=False,
            scope_type=None,
            scope_id=None,
            expires_at=None,
            reason_codes=("VALIDATION_RECORD_NOT_FOUND",),
            credential_version=CURRENT_CREDENTIAL_VERSION,
        )
        event = build_validation_failed_event(
            event_id=generate_uuid(),
            credential_id=credential_id,
            reason_codes=result.reason_codes,
            actor=actor,
            correlation_id=correlation_id,
            occurred_at=now,
        )
        return ValidateResult(result=result, event=event)

    result = validate_credential(
        credential,
        now=now,
        required_scope_type=required_scope_type,
        required_scope_id=required_scope_id,
        expected_rule_version=expected_rule_version,
        expected_digest=expected_digest,
    )
    if result.valid:
        return ValidateResult(result=result, event=None)

    event = build_validation_failed_event(
        event_id=generate_uuid(),
        credential_id=credential_id,
        reason_codes=result.reason_codes,
        actor=actor,
        correlation_id=correlation_id,
        occurred_at=now,
    )
    return ValidateResult(result=result, event=event)


def revoke_participation_credential(
    store: CredentialStore,
    audit_store: AuditEventStore,
    *,
    credential_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    causation_id: UUID | None,
    clock: Clock,
) -> RevokeResult:
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to revoke a credential")

    credential = store.get(credential_id)
    if credential is None:
        raise UnknownCredentialError(f"unknown credential_id: {credential_id}")

    before_hash = compute_payload_hash(credential_full_state_payload(credential))
    updated = credential.with_status(CredentialStatus.REVOKED)
    store.save(updated)
    now = clock.now()
    event = build_credential_revoked_event(
        event_id=generate_uuid(),
        credential=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    # CT-00-07 / INV-04: revoking a credential is a critical action.
    # `reason_code` reuses `CREDENTIAL_REVOKED` (the same code a later
    # failed validation attempt against this credential would report,
    # per ADR-004) since both describe the same real-world fact.
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="participation_credential",
            target_id=updated.credential_id,
            action="revoke",
            reason_code="CREDENTIAL_REVOKED",
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(credential_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return RevokeResult(credential=updated, event=event, audit_event=audit_event)

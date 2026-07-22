"""Tests for epd2_identity_service.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_identity_service.application import (
    PermissionDeniedError,
    record_verification_result,
    revoke_verification,
    start_identity_verification,
)
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.exceptions import UnknownIdentityRecordError
from epd2_identity_service.storage import InMemoryIdentityRecordStore

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _start(store: InMemoryIdentityRecordStore, audit_store: InMemoryAuditEventStore) -> object:
    return start_identity_verification(
        store,
        audit_store,
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        country="DE",
        provider_reference="ref-1",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).record


def test_start_identity_verification_emits_started_event() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    result = start_identity_verification(
        store,
        audit_store,
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        country="DE",
        provider_reference="ref-1",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.record.verification_status == VerificationStatus.PENDING
    assert result.event is not None
    assert result.event.event_type == "identity.verification_started"


def test_start_identity_verification_creates_audit_event() -> None:
    """CT-00-07 / INV-04."""
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    result = start_identity_verification(
        store,
        audit_store,
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        country="DE",
        provider_reference="ref-1",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.audit_event is not None
    assert result.audit_event.action == "start_verification"
    assert result.audit_event.reason_code == "IDENTITY_VERIFICATION_STARTED"
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_record_successful_verification_emits_verified_event() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    record = _start(store, audit_store)
    result = record_verification_result(
        store,
        audit_store,
        identity_record_id=record.identity_record_id,  # type: ignore[attr-defined]
        outcome=VerificationStatus.VERIFIED,
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        duplicate_check_status="clear",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.record.verification_status == VerificationStatus.VERIFIED
    assert result.record.verified_at == _CLOCK.now()
    assert result.event is not None
    assert result.event.event_type == "identity.verified"
    assert result.audit_event is not None
    assert result.audit_event.reason_code == "IDENTITY_VERIFIED"


def test_record_failed_verification_emits_failed_event() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    record = _start(store, audit_store)
    result = record_verification_result(
        store,
        audit_store,
        identity_record_id=record.identity_record_id,  # type: ignore[attr-defined]
        outcome=VerificationStatus.FAILED,
        expires_at=None,
        duplicate_check_status=None,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.event is not None
    assert result.event.event_type == "identity.verification_failed"
    assert result.audit_event is not None
    assert result.audit_event.reason_code == "IDENTITY_NOT_VERIFIED"


def test_record_verification_without_permission_is_denied() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    record = _start(store, audit_store)
    with pytest.raises(PermissionDeniedError):
        record_verification_result(
            store,
            audit_store,
            identity_record_id=record.identity_record_id,  # type: ignore[attr-defined]
            outcome=VerificationStatus.VERIFIED,
            expires_at=None,
            duplicate_check_status=None,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_record_verification_for_unknown_record_raises() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownIdentityRecordError):
        record_verification_result(
            store,
            audit_store,
            identity_record_id=uuid4(),
            outcome=VerificationStatus.VERIFIED,
            expires_at=None,
            duplicate_check_status=None,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_revoke_verification_emits_canonical_expired_event() -> None:
    """ADR-002: revocation maps to identity.verification_expired."""
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    record = _start(store, audit_store)
    verified = record_verification_result(
        store,
        audit_store,
        identity_record_id=record.identity_record_id,  # type: ignore[attr-defined]
        outcome=VerificationStatus.VERIFIED,
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        duplicate_check_status="clear",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).record

    result = revoke_verification(
        store,
        audit_store,
        identity_record_id=verified.identity_record_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.record.verification_status == VerificationStatus.EXPIRED
    assert result.event is not None
    assert result.event.event_type == "identity.verification_expired"
    # ADR-004: the audit reason_code still distinguishes an explicit
    # revocation from a natural expiry, even though the event name (above)
    # cannot.
    assert result.audit_event is not None
    assert result.audit_event.reason_code == "IDENTITY_VERIFICATION_REVOKED"


def test_revoke_verification_without_permission_is_denied() -> None:
    store = InMemoryIdentityRecordStore()
    audit_store = InMemoryAuditEventStore()
    record = _start(store, audit_store)
    verified = record_verification_result(
        store,
        audit_store,
        identity_record_id=record.identity_record_id,  # type: ignore[attr-defined]
        outcome=VerificationStatus.VERIFIED,
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        duplicate_check_status="clear",
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    ).record
    with pytest.raises(PermissionDeniedError):
        revoke_verification(
            store,
            audit_store,
            identity_record_id=verified.identity_record_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )

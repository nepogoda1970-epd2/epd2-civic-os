"""Tests for epd2_credential_service.application."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import (
    PermissionDeniedError,
    issue_participation_credential,
    revoke_participation_credential,
    validate_participation_credential,
)
from epd2_credential_service.domain import FORBIDDEN_FIELD_NAMES, CredentialType
from epd2_credential_service.exceptions import UnknownCredentialError
from epd2_credential_service.storage import InMemoryCredentialStore

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="service")


def _issue(
    store: InMemoryCredentialStore, audit_store: InMemoryAuditEventStore, **overrides: object
) -> object:
    defaults: dict[str, object] = {
        "credential_id": uuid4(),
        "credential_type": CredentialType.SPACE_ACCESS,
        "scope_type": "civic_space",
        "scope_id": uuid4(),
        "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
        "expires_at": datetime(2027, 1, 1, tzinfo=UTC),
        "usage_limit": None,
        "rule_version": 1,
        "eligibility_snapshot_digest": "a" * 64,
        "actor": _ACTOR,
        "actor_is_authorized": True,
        "correlation_id": uuid4(),
        "clock": _CLOCK,
    }
    defaults.update(overrides)
    return issue_participation_credential(store, audit_store, **defaults)  # type: ignore[arg-type]


def test_issue_emits_credential_issued_event() -> None:
    store = InMemoryCredentialStore()
    result = _issue(store, InMemoryAuditEventStore())
    assert result.event.event_type == "credential.issued"  # type: ignore[attr-defined]
    assert result.credential.status.value == "issued"  # type: ignore[attr-defined]


def test_issue_creates_audit_event() -> None:
    """CT-00-07 / INV-04: issuing a credential is a critical action and
    must leave a durable, tamper-evident audit trail."""
    store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    result = _issue(store, audit_store)
    audit_event = result.audit_event  # type: ignore[attr-defined]
    assert audit_event.action == "issue"
    assert audit_event.reason_code == "CREDENTIAL_ISSUED"
    assert audit_event.target_type == "participation_credential"
    assert audit_event.target_id == result.credential.credential_id  # type: ignore[attr-defined]
    assert audit_store.get_by_event_id(audit_event.audit_event_id) is not None


def test_issue_without_permission_is_denied() -> None:
    store = InMemoryCredentialStore()
    with pytest.raises(PermissionDeniedError):
        _issue(store, InMemoryAuditEventStore(), actor_is_authorized=False)


def test_issued_event_payload_contains_no_forbidden_identity_fields() -> None:
    """CT-00-08 / identity leakage: credential events must not contain
    identity fields."""
    store = InMemoryCredentialStore()
    result = _issue(store, InMemoryAuditEventStore())
    payload_text = json.dumps(result.event.payload)  # type: ignore[attr-defined]
    for forbidden in FORBIDDEN_FIELD_NAMES:
        assert forbidden not in payload_text


def test_validate_successful_credential_emits_no_event() -> None:
    store = InMemoryCredentialStore()
    credential = _issue(store, InMemoryAuditEventStore()).credential  # type: ignore[attr-defined]
    result = validate_participation_credential(
        store,
        credential_id=credential.credential_id,
        required_scope_type=None,
        required_scope_id=None,
        expected_rule_version=None,
        expected_digest=None,
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.result.valid
    assert result.event is None


def test_validate_unknown_credential_is_invalid_and_emits_failure_event() -> None:
    store = InMemoryCredentialStore()
    result = validate_participation_credential(
        store,
        credential_id=uuid4(),
        required_scope_type=None,
        required_scope_id=None,
        expected_rule_version=None,
        expected_digest=None,
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert not result.result.valid
    assert result.event is not None
    assert result.event.event_type == "credential.validation_failed"
    assert "VALIDATION_RECORD_NOT_FOUND" in result.result.reason_codes


def test_validation_result_contains_no_identity_fields() -> None:
    """CT-00-08: validation response never contains identity fields."""
    store = InMemoryCredentialStore()
    credential = _issue(store, InMemoryAuditEventStore()).credential  # type: ignore[attr-defined]
    result = validate_participation_credential(
        store,
        credential_id=credential.credential_id,
        required_scope_type=None,
        required_scope_id=None,
        expected_rule_version=None,
        expected_digest=None,
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result_field_names = set(result.result.__dataclass_fields__)
    assert not (result_field_names & FORBIDDEN_FIELD_NAMES)


def test_revoke_transitions_to_revoked_and_emits_event() -> None:
    store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    credential = _issue(store, audit_store).credential  # type: ignore[attr-defined]
    result = revoke_participation_credential(
        store,
        audit_store,
        credential_id=credential.credential_id,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert result.credential.status.value == "revoked"
    assert result.event.event_type == "credential.revoked"
    assert result.audit_event.action == "revoke"
    assert result.audit_event.reason_code == "CREDENTIAL_REVOKED"

    revalidated = validate_participation_credential(
        store,
        credential_id=credential.credential_id,
        required_scope_type=None,
        required_scope_id=None,
        expected_rule_version=None,
        expected_digest=None,
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert not revalidated.result.valid
    assert "CREDENTIAL_REVOKED" in revalidated.result.reason_codes


def test_revoke_without_permission_is_denied() -> None:
    store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    credential = _issue(store, audit_store).credential  # type: ignore[attr-defined]
    with pytest.raises(PermissionDeniedError):
        revoke_participation_credential(
            store,
            audit_store,
            credential_id=credential.credential_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_revoke_unknown_credential_raises() -> None:
    store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownCredentialError):
        revoke_participation_credential(
            store,
            audit_store,
            credential_id=uuid4(),
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_revoke_permission_denied_does_not_create_audit_event() -> None:
    """A refused command must not fabricate a false audit trail entry for
    an action that never happened."""
    store = InMemoryCredentialStore()
    audit_store = InMemoryAuditEventStore()
    credential = _issue(store, audit_store).credential  # type: ignore[attr-defined]
    before_count = len(
        audit_store.list_by_aggregate("participation_credential", credential.credential_id)
    )
    with pytest.raises(PermissionDeniedError):
        revoke_participation_credential(
            store,
            audit_store,
            credential_id=credential.credential_id,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )
    after_count = len(
        audit_store.list_by_aggregate("participation_credential", credential.credential_id)
    )
    assert after_count == before_count

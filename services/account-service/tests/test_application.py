"""Tests for epd2_account_service.application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_account_service.application import (
    PermissionDeniedError,
    change_account_status,
    create_account,
)
from epd2_account_service.domain import AccountStatus
from epd2_account_service.exceptions import ForbiddenAccountTransitionError, UnknownAccountError
from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef

_CLOCK = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="user")


def test_create_account_emits_account_created_event() -> None:
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    result = create_account(
        store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.account.account_status == AccountStatus.PENDING
    assert result.event is not None
    assert result.event.event_type == "account.created"
    assert store.get(result.account.account_id) == result.account


def test_create_account_creates_audit_event() -> None:
    """CT-00-07 / INV-04."""
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    result = create_account(
        store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.audit_event is not None
    assert result.audit_event.reason_code == "ACCOUNT_CREATED"
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_change_status_to_restricted_emits_canonical_event() -> None:
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    created = create_account(
        store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).account
    activated = change_account_status(
        store,
        audit_store,
        account_id=created.account_id,
        target_status=AccountStatus.ACTIVE,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert activated.event is None  # pending -> active has no canonical event name
    assert activated.audit_event is None  # no canonical event -> not audited (ADR-002)

    restricted = change_account_status(
        store,
        audit_store,
        account_id=created.account_id,
        target_status=AccountStatus.RESTRICTED,
        actor=_ACTOR,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    assert restricted.event is not None
    assert restricted.event.event_type == "account.restricted"
    assert restricted.audit_event is not None
    assert restricted.audit_event.reason_code == "ACCOUNT_STATUS_CHANGED"


def test_change_status_without_permission_is_denied() -> None:
    """CT-00-06: action without permission is rejected."""
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    created = create_account(
        store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).account
    with pytest.raises(PermissionDeniedError):
        change_account_status(
            store,
            audit_store,
            account_id=created.account_id,
            target_status=AccountStatus.ACTIVE,
            actor=_ACTOR,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )


def test_change_status_forbidden_transition_raises_and_does_not_mutate_store() -> None:
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    created = create_account(
        store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=_ACTOR,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).account
    with pytest.raises(ForbiddenAccountTransitionError):
        change_account_status(
            store,
            audit_store,
            account_id=created.account_id,
            target_status=AccountStatus.SUSPENDED,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )
    assert store.get(created.account_id) is not None
    assert store.get(created.account_id).account_status == AccountStatus.PENDING  # type: ignore[union-attr]


def test_change_status_unknown_account_raises() -> None:
    store = InMemoryAccountStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownAccountError, match="unknown account_id"):
        change_account_status(
            store,
            audit_store,
            account_id=uuid4(),
            target_status=AccountStatus.ACTIVE,
            actor=_ACTOR,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            causation_id=None,
            clock=_CLOCK,
        )

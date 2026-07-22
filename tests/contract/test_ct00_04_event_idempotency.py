"""CT-00-04 Event Idempotency (canon section 27): a repeat of the same
`event_id` does not create a second action. Exercised here at the
Audit Core boundary (the durable record every service's critical action
appends to) using a real service call, not a synthetic AuditEvent."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore


def test_repeated_credential_issuance_with_same_event_id_is_idempotent(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same issuance command (same
    `credential_id`, same content, same caller-supplied `event_id` -
    e.g. after a network timeout on the first attempt's response) must
    not create a second stored credential or a second audit entry."""
    credential_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        credential_id=credential_id,
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )

    assert first.credential == second.credential
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    # Only one AuditEvent exists for this credential's issuance - the
    # repeat did not append a second entry to the chain.
    entries = audit_store.list_by_aggregate("participation_credential", credential_id)
    assert len(entries) == 1
    assert entries[0].audit_event_id == first.audit_event.audit_event_id


def test_repeated_credential_issuance_without_shared_event_id_still_dedupes_storage(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Without a caller-supplied `event_id` (the default), the *stored*
    credential still dedupes correctly by `credential_id` + content (the
    service's own idempotency key, distinct from CT-00-04's event-level
    guarantee) - but each call mints its own domain event and audit entry.
    This is a documented, narrower guarantee than the shared-event_id case
    above; see docs/review/OPEN_QUESTIONS.md."""
    credential_id = uuid4()
    kwargs = dict(
        credential_id=credential_id,
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    first = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )

    assert first.credential == second.credential
    assert first.audit_event.audit_event_id != second.audit_event.audit_event_id


def test_repeated_event_id_with_different_content_is_a_conflict(
    audit_store: InMemoryAuditEventStore, actor: ActorRef, clock: FixedClock
) -> None:
    """A direct Audit Core replay with the same `audit_event_id` but
    different content must fail-closed, never silently overwrite."""
    from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event

    shared_id = uuid4()
    base = dict(
        audit_event_id=shared_id,
        occurred_at=clock.now(),
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="participation_credential",
        target_id=uuid4(),
        action="issue",
        reason_code="CREDENTIAL_ISSUED",
        policy_version="1.0",
        correlation_id=uuid4(),
        source_service="credential-service",
    )
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(event_type="credential.issued", **base),  # type: ignore[arg-type]
        clock=clock,
    )
    with pytest.raises(AuditEventConflictError):
        append_audit_event(
            audit_store,
            # Same audit_event_id, different event_type -> different content.
            AppendAuditEventRequest(
                event_type="credential.revoked",
                **base,  # type: ignore[arg-type]
            ),
            clock=clock,
        )

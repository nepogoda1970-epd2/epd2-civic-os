"""CT-00-07 Audit Creation (canon section 27): a critical action creates
an `AuditEvent`, for every service that owns one. Per-service unit tests
already cover this (services/*/tests/test_application.py); this file is
the cross-service, pack-numbered aggregation the pack itself asks for
(section 12.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from epd2_account_service.application import create_account
from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import create_eligibility_rule, evaluate_eligibility
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
)
from epd2_identity_service.application import start_identity_verification
from epd2_identity_service.storage import InMemoryIdentityRecordStore


def test_account_creation_creates_an_audit_event(
    account_store: InMemoryAccountStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_account(
        account_store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.audit_event is not None
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_identity_verification_start_creates_an_audit_event(
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = start_identity_verification(
        identity_store,
        audit_store,
        account_id=uuid4(),
        verification_provider="p",
        verification_level="basic",
        country="DE",
        provider_reference="r",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.audit_event is not None
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_eligibility_evaluation_creates_an_audit_event(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_decision_store: InMemoryEligibilityDecisionStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    result = evaluate_eligibility(
        eligibility_rule_store,
        eligibility_decision_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_credential_issuance_creates_an_audit_event(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = issue_participation_credential(
        credential_store,
        audit_store,
        credential_id=uuid4(),
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
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_denied_command_creates_no_audit_event(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A refused command must never fabricate an audit trail entry for an
    action that never happened (complements CT-00-06)."""
    import pytest

    from epd2_credential_service.application import PermissionDeniedError

    credential_id = uuid4()
    with pytest.raises(PermissionDeniedError):
        issue_participation_credential(
            credential_store,
            audit_store,
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
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert audit_store.list_by_aggregate("participation_credential", credential_id) == ()

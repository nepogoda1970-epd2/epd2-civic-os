"""CT-00-06 Missing Permission (canon section 27): an action without
authorization is rejected, for every service's critical commands."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_account_service.application import PermissionDeniedError as AccountPermissionDeniedError
from epd2_account_service.application import change_account_status, create_account
from epd2_account_service.domain import AccountStatus
from epd2_account_service.storage import InMemoryAccountStore
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import (
    PermissionDeniedError as CredentialPermissionDeniedError,
)
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import (
    PermissionDeniedError as EligibilityPermissionDeniedError,
)
from epd2_eligibility_service.application import create_eligibility_rule, evaluate_eligibility
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
)
from epd2_identity_service.application import (
    PermissionDeniedError as IdentityPermissionDeniedError,
)
from epd2_identity_service.application import (
    record_verification_result,
    start_identity_verification,
)
from epd2_identity_service.domain import VerificationStatus
from epd2_identity_service.storage import InMemoryIdentityRecordStore


def test_account_status_change_without_permission_is_denied(
    account_store: InMemoryAccountStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    created = create_account(
        account_store,
        audit_store,
        locale="en",
        terms_version="1.0",
        consent_status="granted",
        actor=actor,
        correlation_id=uuid4(),
        clock=clock,
    ).account
    with pytest.raises(AccountPermissionDeniedError) as excinfo:
        change_account_status(
            account_store,
            audit_store,
            account_id=created.account_id,
            target_status=AccountStatus.ACTIVE,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_identity_verification_result_without_permission_is_denied(
    identity_store: InMemoryIdentityRecordStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    record = start_identity_verification(
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
    ).record
    with pytest.raises(IdentityPermissionDeniedError) as excinfo:
        record_verification_result(
            identity_store,
            audit_store,
            identity_record_id=record.identity_record_id,
            outcome=VerificationStatus.VERIFIED,
            expires_at=None,
            duplicate_check_status=None,
            actor=actor,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            causation_id=None,
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_eligibility_evaluation_without_permission_is_denied(
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
    with pytest.raises(EligibilityPermissionDeniedError) as excinfo:
        evaluate_eligibility(
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
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"


def test_credential_issuance_without_permission_is_denied(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    with pytest.raises(CredentialPermissionDeniedError) as excinfo:
        issue_participation_credential(
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
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=clock,
        )
    assert excinfo.value.reason_code == "PERMISSION_DENIED"

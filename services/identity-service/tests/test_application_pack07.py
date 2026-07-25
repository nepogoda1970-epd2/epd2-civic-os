"""Tests for epd2_identity_service.application's PACK-07/ADR-027 narrow
cross-pack reads: `get_identity_participation_claims` and
`check_authentication_step_up_satisfied` - the only two
`epd2_identity_service.application` functions
`eligibility-service`/`membership-service` may import."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from epd2_identity_service.application import (
    check_authentication_step_up_satisfied,
    get_identity_participation_claims,
)
from epd2_identity_service.domain import (
    AuthenticationAssuranceLevel,
    AuthenticationContext,
    IdentityAssuranceLevel,
    IdentityRecord,
    VerificationStatus,
)
from epd2_identity_service.storage import (
    InMemoryAuthenticationContextStore,
    InMemoryIdentityRecordStore,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_verified_record(
    store: InMemoryIdentityRecordStore,
    *,
    identity_assurance_level: IdentityAssuranceLevel = IdentityAssuranceLevel.SUBSTANTIAL,
    date_of_birth: datetime | None = None,
    citizenship_status: tuple[str, ...] = ("DE",),
    attribute_verified_at: datetime | None = None,
) -> UUID:
    identity_record_id = uuid4()
    record = IdentityRecord(
        identity_record_id=identity_record_id,
        account_id=uuid4(),
        verification_provider="provider",
        verification_level="substantial",
        verification_status=VerificationStatus.VERIFIED,
        verified_at=_NOW,
        expires_at=None,
        country="DE",
        duplicate_check_status="unique",
        provider_reference="ref",
        date_of_birth=(date_of_birth.date() if date_of_birth else None),
        citizenship_status=citizenship_status,
        identity_assurance_level=identity_assurance_level,
        attribute_verified_at=attribute_verified_at,
    )
    store.save(record)
    return identity_record_id


# =============================================================================
# get_identity_participation_claims (ADR-027)
# =============================================================================


def test_get_identity_participation_claims_fails_closed_for_unknown_record() -> None:
    store = InMemoryIdentityRecordStore()
    claims = get_identity_participation_claims(
        store,
        identity_record_id=uuid4(),
        required_identity_assurance_level="substantial",
        minimum_age=None,
        eligible_citizenship_set=(),
        residence_rule=None,
        territorial_scope_rule=None,
        evaluated_at=_NOW,
    )
    assert claims.identity_verified is False
    assert claims.reason_codes == ("IDENTITY_NOT_VERIFIED",)


def test_get_identity_participation_claims_true_when_verified_and_assurance_met() -> None:
    store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(store)
    claims = get_identity_participation_claims(
        store,
        identity_record_id=identity_record_id,
        required_identity_assurance_level="substantial",
        minimum_age=None,
        eligible_citizenship_set=(),
        residence_rule=None,
        territorial_scope_rule=None,
        evaluated_at=_NOW,
    )
    assert claims.identity_verified is True
    assert claims.identity_assurance_requirement_met is True


def test_get_identity_participation_claims_fails_when_assurance_below_requirement() -> None:
    store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(
        store, identity_assurance_level=IdentityAssuranceLevel.LOW
    )
    claims = get_identity_participation_claims(
        store,
        identity_record_id=identity_record_id,
        required_identity_assurance_level="substantial",
        minimum_age=None,
        eligible_citizenship_set=(),
        residence_rule=None,
        territorial_scope_rule=None,
        evaluated_at=_NOW,
    )
    assert claims.identity_assurance_requirement_met is False
    assert "IDENTITY_ASSURANCE_REQUIREMENT_NOT_MET" in claims.reason_codes


# =============================================================================
# check_authentication_step_up_satisfied (ADR-030 item 7)
# =============================================================================


def test_check_authentication_step_up_satisfied_fails_closed_with_no_context() -> None:
    context_store = InMemoryAuthenticationContextStore()
    identity_store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(identity_store)
    result = check_authentication_step_up_satisfied(
        context_store,
        identity_store,
        authentication_context_id=uuid4(),
        identity_record_id=identity_record_id,
        required_authentication_assurance_level="substantial",
        required_identity_assurance_level="substantial",
        fresh_authentication_required=True,
        maximum_authentication_age=timedelta(minutes=15),
        required_attribute_freshness=None,
        reauthentication_reason="high-stakes action",
        evaluated_at=_NOW,
    )
    assert result.satisfied is False
    assert result.reauthentication_reason == "high-stakes action"


def test_check_authentication_step_up_satisfied_true_when_all_conditions_met() -> None:
    context_store = InMemoryAuthenticationContextStore()
    identity_store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(identity_store)
    context = AuthenticationContext(
        authentication_context_id=uuid4(),
        account_id=uuid4(),
        authentication_method="password+otp",
        authentication_assurance_level=AuthenticationAssuranceLevel.SUBSTANTIAL,
        session_authenticated_at=_NOW - timedelta(minutes=5),
        provider_reference="ref",
    )
    context_store.save(context)
    result = check_authentication_step_up_satisfied(
        context_store,
        identity_store,
        authentication_context_id=context.authentication_context_id,
        identity_record_id=identity_record_id,
        required_authentication_assurance_level="substantial",
        required_identity_assurance_level="substantial",
        fresh_authentication_required=True,
        maximum_authentication_age=timedelta(minutes=15),
        required_attribute_freshness=None,
        reauthentication_reason="high-stakes action",
        evaluated_at=_NOW,
    )
    assert result.satisfied is True
    assert result.reauthentication_reason is None


def test_check_authentication_step_up_satisfied_fails_when_session_too_old() -> None:
    context_store = InMemoryAuthenticationContextStore()
    identity_store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(identity_store)
    context = AuthenticationContext(
        authentication_context_id=uuid4(),
        account_id=uuid4(),
        authentication_method="password+otp",
        authentication_assurance_level=AuthenticationAssuranceLevel.SUBSTANTIAL,
        session_authenticated_at=_NOW - timedelta(hours=2),
        provider_reference="ref",
    )
    context_store.save(context)
    result = check_authentication_step_up_satisfied(
        context_store,
        identity_store,
        authentication_context_id=context.authentication_context_id,
        identity_record_id=identity_record_id,
        required_authentication_assurance_level="substantial",
        required_identity_assurance_level="substantial",
        fresh_authentication_required=True,
        maximum_authentication_age=timedelta(minutes=15),
        required_attribute_freshness=None,
        reauthentication_reason="high-stakes action",
        evaluated_at=_NOW,
    )
    assert result.satisfied is False
    assert result.reauthentication_reason == "high-stakes action"


def test_check_authentication_step_up_satisfied_fails_when_attribute_stale() -> None:
    context_store = InMemoryAuthenticationContextStore()
    identity_store = InMemoryIdentityRecordStore()
    identity_record_id = _make_verified_record(
        identity_store, attribute_verified_at=_NOW - timedelta(days=400)
    )
    context = AuthenticationContext(
        authentication_context_id=uuid4(),
        account_id=uuid4(),
        authentication_method="password+otp",
        authentication_assurance_level=AuthenticationAssuranceLevel.SUBSTANTIAL,
        session_authenticated_at=_NOW - timedelta(minutes=5),
        provider_reference="ref",
    )
    context_store.save(context)
    result = check_authentication_step_up_satisfied(
        context_store,
        identity_store,
        authentication_context_id=context.authentication_context_id,
        identity_record_id=identity_record_id,
        required_authentication_assurance_level="substantial",
        required_identity_assurance_level="substantial",
        fresh_authentication_required=True,
        maximum_authentication_age=timedelta(minutes=15),
        required_attribute_freshness=timedelta(days=365),
        reauthentication_reason="high-stakes action",
        evaluated_at=_NOW,
    )
    assert result.satisfied is False

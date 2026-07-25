"""Tests for epd2_identity_service.domain."""

from __future__ import annotations

from uuid import uuid4

import pytest

from epd2_identity_service.domain import (
    AuthenticationAssuranceLevel,
    AuthenticationContext,
    IdentityAssuranceLevel,
    IdentityRecord,
    VerificationStatus,
    assert_transition_allowed,
    parse_authentication_assurance_level,
    parse_identity_assurance_level,
    parse_status,
)
from epd2_identity_service.exceptions import (
    ForbiddenVerificationTransitionError,
    UnknownAuthenticationAssuranceLevelError,
    UnknownIdentityAssuranceLevelError,
    UnknownVerificationStatusError,
)

#: Canon section 7.3's original ten fields.
_CANON_7_3_FIELD_NAMES = {
    "identity_record_id",
    "account_id",
    "verification_provider",
    "verification_level",
    "verification_status",
    "verified_at",
    "expires_at",
    "country",
    "duplicate_check_status",
    "provider_reference",
}
#: Canon 19d.2's eight additive fields (canon-0.6.0, PACK-07).
_CANON_19D_2_FIELD_NAMES = {
    "date_of_birth",
    "citizenship_status",
    "residence_status",
    "identity_assurance_level",
    "identity_scheme",
    "attribute_verification_level",
    "attribute_verified_at",
    "attribute_valid_until",
}
_ALLOWED_FIELD_NAMES = _CANON_7_3_FIELD_NAMES | _CANON_19D_2_FIELD_NAMES
_FORBIDDEN_SUBSTRINGS = ("vote", "ballot", "initiative", "delegat", "political", "preference")


def test_identity_record_has_exactly_the_canonical_field_set() -> None:
    """Regression guard for canon section 7.3 + 19d.2's exact field
    list (canon-0.6.0)."""
    field_names = {f for f in IdentityRecord.__dataclass_fields__}
    assert field_names == _ALLOWED_FIELD_NAMES


def test_identity_record_field_names_contain_no_forbidden_terms() -> None:
    for field_name in IdentityRecord.__dataclass_fields__:
        lowered = field_name.lower()
        for forbidden in _FORBIDDEN_SUBSTRINGS:
            assert forbidden not in lowered, f"field {field_name!r} looks participation-related"


def test_parse_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownVerificationStatusError):
        parse_status("trusted_forever")


def test_pending_to_verified_is_allowed() -> None:
    assert_transition_allowed(VerificationStatus.PENDING, VerificationStatus.VERIFIED)


def test_expired_to_verified_is_forbidden() -> None:
    with pytest.raises(ForbiddenVerificationTransitionError):
        assert_transition_allowed(VerificationStatus.EXPIRED, VerificationStatus.VERIFIED)


def test_failed_to_duplicate_suspected_is_forbidden() -> None:
    with pytest.raises(ForbiddenVerificationTransitionError):
        assert_transition_allowed(VerificationStatus.FAILED, VerificationStatus.DUPLICATE_SUSPECTED)


def test_with_status_updates_only_requested_fields() -> None:
    from datetime import UTC, datetime

    record = IdentityRecord(
        identity_record_id=uuid4(),
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        verification_status=VerificationStatus.PENDING,
        verified_at=None,
        expires_at=None,
        country="DE",
        duplicate_check_status="not_checked",
        provider_reference="ref-1",
    )
    verified_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated = record.with_status(VerificationStatus.VERIFIED, verified_at=verified_at)
    assert updated.verification_status == VerificationStatus.VERIFIED
    assert updated.verified_at == verified_at
    assert updated.country == "DE"  # unchanged


# --- PACK-07 additions (canon 19d.2 / 19d.8, canon-0.6.0) -------------------


def _bare_record() -> IdentityRecord:
    """An `IdentityRecord` built with none of canon 19d.2's eight new
    keyword arguments supplied - proves every pre-PACK-07 call site in
    this repository still constructs a valid record unchanged."""
    return IdentityRecord(
        identity_record_id=uuid4(),
        account_id=uuid4(),
        verification_provider="provider-x",
        verification_level="basic",
        verification_status=VerificationStatus.PENDING,
        verified_at=None,
        expires_at=None,
        country="DE",
        duplicate_check_status="not_checked",
        provider_reference="ref-1",
    )


def test_identity_record_canon_19d_2_fields_default_to_nothing_asserted() -> None:
    record = _bare_record()
    assert record.date_of_birth is None
    assert record.citizenship_status == ()
    assert record.residence_status is None
    assert record.identity_assurance_level is IdentityAssuranceLevel.NONE
    assert record.identity_scheme is None
    assert record.attribute_verification_level is None
    assert record.attribute_verified_at is None
    assert record.attribute_valid_until is None


def test_citizenship_status_is_always_a_tuple_never_a_single_boolean() -> None:
    """Canon 19d.2: 'допускает безгражданство и множественное
    гражданство, никогда не единственное булево значение'."""
    stateless = _bare_record().with_attributes(citizenship_status=())
    multiple = _bare_record().with_attributes(citizenship_status=("DE", "FR"))
    assert stateless.citizenship_status == ()
    assert multiple.citizenship_status == ("DE", "FR")


def test_with_attributes_never_touches_verification_lifecycle_fields() -> None:
    from datetime import UTC, date, datetime

    record = _bare_record()
    updated = record.with_attributes(
        date_of_birth=date(1990, 1, 1),
        citizenship_status=("DE",),
        identity_assurance_level=IdentityAssuranceLevel.SUBSTANTIAL,
        identity_scheme="de_personalausweis_online",
        attribute_verification_level="high",
        attribute_verified_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert updated.verification_status == record.verification_status
    assert updated.verified_at == record.verified_at
    assert updated.expires_at == record.expires_at
    assert updated.duplicate_check_status == record.duplicate_check_status
    assert updated.date_of_birth == date(1990, 1, 1)
    assert updated.identity_assurance_level == IdentityAssuranceLevel.SUBSTANTIAL


def test_with_status_never_touches_canon_19d_2_fields() -> None:
    from datetime import date

    record = _bare_record().with_attributes(
        date_of_birth=date(1990, 1, 1), citizenship_status=("DE",)
    )
    updated = record.with_status(VerificationStatus.VERIFIED)
    assert updated.date_of_birth == date(1990, 1, 1)
    assert updated.citizenship_status == ("DE",)


def test_attribute_valid_until_before_verified_at_is_rejected() -> None:
    from datetime import UTC, datetime

    with pytest.raises(ValueError, match="attribute_valid_until"):
        _bare_record().with_attributes(
            attribute_verified_at=datetime(2026, 6, 1, tzinfo=UTC),
            attribute_valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_identity_scheme_rejects_empty_string() -> None:
    with pytest.raises(ValueError, match="identity_scheme"):
        _bare_record().with_attributes(identity_scheme="")


def test_identity_assurance_level_and_authentication_assurance_level_are_distinct_types() -> None:
    """Canon 19d.8: 'пять раздельных, никогда не взаимозаменяемых
    понятий' - confirmed here at the type level, not just by convention."""
    assert IdentityAssuranceLevel is not AuthenticationAssuranceLevel  # type: ignore[comparison-overlap]
    assert {m.value for m in IdentityAssuranceLevel} == {
        m.value for m in AuthenticationAssuranceLevel
    }


def test_parse_identity_assurance_level_rejects_unknown_value() -> None:
    with pytest.raises(UnknownIdentityAssuranceLevelError):
        parse_identity_assurance_level("omniscient")


def test_parse_authentication_assurance_level_rejects_unknown_value() -> None:
    with pytest.raises(UnknownAuthenticationAssuranceLevelError):
        parse_authentication_assurance_level("omniscient")


def test_authentication_context_requires_timezone_aware_session_authenticated_at() -> None:
    from datetime import datetime

    with pytest.raises(ValueError, match="session_authenticated_at"):
        AuthenticationContext(
            authentication_context_id=uuid4(),
            account_id=uuid4(),
            authentication_method="password_totp",
            authentication_assurance_level=AuthenticationAssuranceLevel.SUBSTANTIAL,
            session_authenticated_at=datetime(2026, 1, 1),  # naive - rejected
            provider_reference="provider-ref",
        )


def test_authentication_context_with_step_up_completed() -> None:
    from datetime import UTC, datetime

    context = AuthenticationContext(
        authentication_context_id=uuid4(),
        account_id=uuid4(),
        authentication_method="password_totp",
        authentication_assurance_level=AuthenticationAssuranceLevel.SUBSTANTIAL,
        session_authenticated_at=datetime(2026, 1, 1, tzinfo=UTC),
        provider_reference="provider-ref",
    )
    assert context.step_up_completed_at is None
    completed_at = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)
    updated = context.with_step_up_completed(completed_at)
    assert updated.step_up_completed_at == completed_at
    # Original fields carried over unchanged.
    assert updated.authentication_method == context.authentication_method
    assert updated.session_authenticated_at == context.session_authenticated_at

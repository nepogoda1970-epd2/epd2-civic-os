"""Tests for epd2_identity_service.domain."""

from __future__ import annotations

from uuid import uuid4

import pytest

from epd2_identity_service.domain import (
    IdentityRecord,
    VerificationStatus,
    assert_transition_allowed,
    parse_status,
)
from epd2_identity_service.exceptions import (
    ForbiddenVerificationTransitionError,
    UnknownVerificationStatusError,
)

_ALLOWED_FIELD_NAMES = {
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
_FORBIDDEN_SUBSTRINGS = ("vote", "ballot", "initiative", "delegat", "political", "preference")


def test_identity_record_has_exactly_the_canonical_field_set() -> None:
    """Regression guard for canon section 7.3's exact field list."""
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

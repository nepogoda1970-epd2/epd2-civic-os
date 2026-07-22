"""Tests for epd2_credential_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_credential_service.domain import (
    FORBIDDEN_FIELD_NAMES,
    CredentialStatus,
    ParticipationCredential,
    assert_transition_allowed,
    parse_status,
)
from epd2_credential_service.exceptions import (
    ForbiddenCredentialTransitionError,
    UnknownCredentialStatusError,
)

_ALLOWED_FIELDS = {
    "credential_id",
    "credential_type",
    "scope_type",
    "scope_id",
    "issued_at",
    "valid_from",
    "expires_at",
    "status",
    "usage_limit",
    "usage_counter",
    "revocation_status",
    "issuer_signature",
    "credential_version",
    "rule_version",
    "eligibility_snapshot_digest",
}


def _make(**overrides: object) -> ParticipationCredential:
    defaults: dict[str, object] = {
        "credential_id": uuid4(),
        "credential_type": "space_access",
        "scope_type": "civic_space",
        "scope_id": uuid4(),
        "issued_at": datetime(2026, 1, 1, tzinfo=UTC),
        "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
        "expires_at": datetime(2027, 1, 1, tzinfo=UTC),
        "status": CredentialStatus.ISSUED,
        "usage_limit": None,
        "usage_counter": 0,
        "revocation_status": "not_revoked",
        "issuer_signature": None,
        "credential_version": 1,
        "rule_version": 1,
        "eligibility_snapshot_digest": "a" * 64,
    }
    defaults.update(overrides)
    from epd2_credential_service.domain import CredentialType

    if isinstance(defaults["credential_type"], str):
        defaults["credential_type"] = CredentialType(defaults["credential_type"])
    return ParticipationCredential(**defaults)  # type: ignore[arg-type]


def test_participation_credential_has_exactly_the_allowed_field_set() -> None:
    field_names = set(ParticipationCredential.__dataclass_fields__)
    assert field_names == _ALLOWED_FIELDS


def test_participation_credential_never_has_forbidden_fields() -> None:
    field_names = set(ParticipationCredential.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)


def test_parse_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownCredentialStatusError):
        parse_status("eternal")


def test_issued_to_active_is_allowed() -> None:
    assert_transition_allowed(CredentialStatus.ISSUED, CredentialStatus.ACTIVE)


def test_revoked_to_active_is_forbidden() -> None:
    """CT-00-03: forbidden transition. revoked is terminal."""
    with pytest.raises(ForbiddenCredentialTransitionError):
        assert_transition_allowed(CredentialStatus.REVOKED, CredentialStatus.ACTIVE)


def test_expired_to_active_is_forbidden() -> None:
    with pytest.raises(ForbiddenCredentialTransitionError):
        assert_transition_allowed(CredentialStatus.EXPIRED, CredentialStatus.ACTIVE)


def test_with_status_transitions_and_updates_revocation_status() -> None:
    credential = _make(status=CredentialStatus.ACTIVE)
    revoked = credential.with_status(CredentialStatus.REVOKED)
    assert revoked.status == CredentialStatus.REVOKED
    assert revoked.revocation_status == "revoked"
    assert credential.status == CredentialStatus.ACTIVE  # original unchanged


def test_negative_usage_counter_is_rejected() -> None:
    with pytest.raises(ValueError, match="usage_counter"):
        _make(usage_counter=-1)


def test_usage_counter_exceeding_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="usage_limit"):
        _make(usage_limit=1, usage_counter=2)

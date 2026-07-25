"""Tests for epd2_credential_service.validation (pack section 6.4, fail-closed)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from epd2_credential_service.domain import CredentialStatus, CredentialType, ParticipationCredential
from epd2_credential_service.validation import validate_credential

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _make(**overrides: object) -> ParticipationCredential:
    defaults: dict[str, object] = {
        "credential_id": uuid4(),
        "credential_type": CredentialType.SPACE_ACCESS,
        "scope_type": "civic_space",
        "scope_id": uuid4(),
        "issued_at": datetime(2026, 1, 1, tzinfo=UTC),
        "valid_from": datetime(2026, 1, 1, tzinfo=UTC),
        "expires_at": datetime(2027, 1, 1, tzinfo=UTC),
        "status": CredentialStatus.ACTIVE,
        "usage_limit": None,
        "usage_counter": 0,
        "revocation_status": "not_revoked",
        "issuer_signature": None,
        "credential_version": 1,
        "rule_version": 1,
        "eligibility_snapshot_digest": "a" * 64,
    }
    defaults.update(overrides)
    return ParticipationCredential(**defaults)  # type: ignore[arg-type]


def test_valid_credential_passes() -> None:
    credential = _make()
    result = validate_credential(credential, now=_NOW)
    assert result.valid
    assert result.reason_codes == ()
    assert result.scope_type == "civic_space"


def test_expired_credential_is_invalid() -> None:
    credential = _make(expires_at=datetime(2026, 1, 2, tzinfo=UTC))
    result = validate_credential(credential, now=_NOW)
    assert not result.valid
    assert "CREDENTIAL_EXPIRED" in result.reason_codes


def test_revoked_credential_is_invalid() -> None:
    credential = _make(status=CredentialStatus.REVOKED, revocation_status="revoked")
    result = validate_credential(credential, now=_NOW)
    assert not result.valid
    assert "CREDENTIAL_REVOKED" in result.reason_codes


def test_unsupported_version_is_invalid() -> None:
    credential = _make(credential_version=99)
    result = validate_credential(credential, now=_NOW)
    assert not result.valid
    assert "EVENT_VERSION_UNSUPPORTED" in result.reason_codes


def test_scope_mismatch_is_invalid() -> None:
    credential = _make(scope_type="civic_space", scope_id=uuid4())
    result = validate_credential(credential, now=_NOW, required_scope_type="ballot")
    assert not result.valid
    assert "CREDENTIAL_SCOPE_MISMATCH" in result.reason_codes


def test_scope_id_mismatch_is_invalid() -> None:
    credential = _make(scope_type="civic_space")
    result = validate_credential(
        credential, now=_NOW, required_scope_type="civic_space", required_scope_id=uuid4()
    )
    assert not result.valid
    assert "CREDENTIAL_SCOPE_MISMATCH" in result.reason_codes


def test_rule_version_mismatch_is_invalid() -> None:
    credential = _make(rule_version=1)
    result = validate_credential(credential, now=_NOW, expected_rule_version=2)
    assert not result.valid
    assert "CREDENTIAL_RULE_VERSION_MISMATCH" in result.reason_codes


def test_digest_mismatch_is_invalid() -> None:
    credential = _make(eligibility_snapshot_digest="a" * 64)
    result = validate_credential(credential, now=_NOW, expected_digest="b" * 64)
    assert not result.valid
    assert "CREDENTIAL_DIGEST_MISMATCH" in result.reason_codes


def test_missing_digest_is_invalid() -> None:
    credential = _make(eligibility_snapshot_digest="")
    result = validate_credential(credential, now=_NOW)
    assert not result.valid
    assert "CREDENTIAL_REQUIRED_FIELD_MISSING" in result.reason_codes


def test_invalid_result_never_reveals_scope_or_expiry() -> None:
    credential = _make(status=CredentialStatus.REVOKED, revocation_status="revoked")
    result = validate_credential(credential, now=_NOW)
    assert result.scope_type is None
    assert result.scope_id is None
    assert result.expires_at is None


def test_multiple_simultaneous_failures_are_all_reported_without_duplicates() -> None:
    credential = _make(
        status=CredentialStatus.REVOKED,
        revocation_status="revoked",
        expires_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    result = validate_credential(credential, now=_NOW)
    assert "CREDENTIAL_REVOKED" in result.reason_codes
    assert "CREDENTIAL_EXPIRED" in result.reason_codes
    assert len(result.reason_codes) == len(set(result.reason_codes))

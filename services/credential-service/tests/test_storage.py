"""Tests for epd2_credential_service.storage.

Confirms issuance_reference (pack section 5.3) never leaves the store's
internal representation via any public method.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_credential_service.domain import CredentialStatus, CredentialType, ParticipationCredential
from epd2_credential_service.exceptions import CredentialIssuanceConflictError
from epd2_credential_service.storage import InMemoryCredentialStore


def _make(**overrides: object) -> ParticipationCredential:
    defaults: dict[str, object] = {
        "credential_id": uuid4(),
        "credential_type": CredentialType.SPACE_ACCESS,
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
    return ParticipationCredential(**defaults)  # type: ignore[arg-type]


def test_issue_then_get_returns_public_credential_only() -> None:
    store = InMemoryCredentialStore()
    credential = _make()
    stored = store.issue(credential, issuance_reference="internal-ref-1")
    fetched = store.get(credential.credential_id)
    assert fetched == stored
    assert not hasattr(fetched, "issuance_reference")


def test_issuance_reference_never_leaves_the_service_via_public_dto() -> None:
    store = InMemoryCredentialStore()
    credential = _make()
    store.issue(credential, issuance_reference="internal-ref-1")
    fetched = store.get(credential.credential_id)
    assert fetched is not None
    public_values = [getattr(fetched, f) for f in fetched.__dataclass_fields__]
    assert "internal-ref-1" not in public_values


def test_idempotent_reissue_of_identical_credential_succeeds() -> None:
    store = InMemoryCredentialStore()
    credential = _make()
    first = store.issue(credential, issuance_reference="internal-ref-1")
    second = store.issue(credential, issuance_reference="internal-ref-1")
    assert first == second


def test_conflicting_reissue_is_rejected() -> None:
    store = InMemoryCredentialStore()
    credential = _make()
    store.issue(credential, issuance_reference="internal-ref-1")
    conflicting = _make(credential_id=credential.credential_id, rule_version=2)
    with pytest.raises(CredentialIssuanceConflictError):
        store.issue(conflicting, issuance_reference="internal-ref-2")


def test_issuance_reference_for_is_internal_lookup_only() -> None:
    store = InMemoryCredentialStore()
    credential = _make()
    store.issue(credential, issuance_reference="internal-ref-1")
    assert store.issuance_reference_for(credential.credential_id) == "internal-ref-1"
    assert store.issuance_reference_for(uuid4()) is None

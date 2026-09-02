from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from _ctrl03_builders import BAVARIA, BERLIN, NOW, object_for, service
from epd2_control_plane_service.credential_lifecycle import (
    ALGORITHM_RULES,
    PQ_TRACK_ACTIVE,
    AssuranceProfile,
    CredentialClass,
    LifecycleOperation,
    LifecycleState,
    Refusal,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused


def test_profiles_pin_governed_algorithms_and_pq_is_inactive() -> None:
    assert ALGORITHM_RULES[AssuranceProfile.TRUST_ES384].algorithm == "ES384"
    assert ALGORITHM_RULES[AssuranceProfile.SERVICE_JWS_ES256].algorithm == "ES256"
    assert ALGORITHM_RULES[AssuranceProfile.MTLS].algorithm == "X509"
    assert ALGORITHM_RULES[AssuranceProfile.ENCRYPTION_AES256_GCM].algorithm == "A256GCM"
    assert PQ_TRACK_ACTIVE is False


@pytest.mark.parametrize(
    ("algorithm", "curve"),
    [("none", "P-256"), ("ES384", "P-256"), ("ES256", "P-384")],
)
def test_algorithm_none_wrong_alg_and_key_mismatch_rejected(algorithm: str, curve: str) -> None:
    svc = service()
    item = replace(object_for(), algorithm=algorithm, curve_or_mode=curve)
    with pytest.raises(AuthorizationRefused) as error:
        svc.register(item)
    assert error.value.reason_code == Refusal.WRONG_ALGORITHM


def test_profile_cannot_be_reused_for_wrong_credential_class() -> None:
    svc = service()
    item = replace(
        object_for(CredentialClass.PASSKEY),
        credential_class=CredentialClass.SERVICE_CREDENTIAL,
    )
    with pytest.raises(AuthorizationRefused) as error:
        svc.register(item)
    assert error.value.reason_code == Refusal.WRONG_PURPOSE


def test_cryptoperiod_ceiling_is_enforced() -> None:
    svc = service()
    item = replace(object_for(), valid_until=NOW + timedelta(days=91))
    with pytest.raises(AuthorizationRefused) as error:
        svc.register(item)
    assert error.value.reason_code == Refusal.EXPIRED


def test_assertion_validation_pins_purpose_scope_location_and_trust_version() -> None:
    svc = service()
    item = svc.register(object_for())
    assert svc.validate_assertion(
        item.object_id,
        expected_purpose=item.purpose,
        expected_scope=BERLIN,
        trusted_locations=frozenset({"https://trust.epd.invalid/jwks"}),
        minimum_trust_version=3,
        now=NOW + timedelta(minutes=1),
    )
    with pytest.raises(AuthorizationRefused):
        svc.validate_assertion(
            item.object_id,
            expected_purpose="human-authentication",
            expected_scope=BERLIN,
            trusted_locations=frozenset({"https://trust.epd.invalid/jwks"}),
            minimum_trust_version=3,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(AuthorizationRefused):
        svc.validate_assertion(
            item.object_id,
            expected_purpose=item.purpose,
            expected_scope=BAVARIA,
            trusted_locations=frozenset({"https://trust.epd.invalid/jwks"}),
            minimum_trust_version=3,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(AuthorizationRefused):
        svc.validate_assertion(
            item.object_id,
            expected_purpose=item.purpose,
            expected_scope=BERLIN,
            trusted_locations=frozenset({"https://attacker.invalid/jwks"}),
            minimum_trust_version=3,
            now=NOW + timedelta(minutes=1),
        )
    with pytest.raises(AuthorizationRefused):
        svc.validate_assertion(
            item.object_id,
            expected_purpose=item.purpose,
            expected_scope=BERLIN,
            trusted_locations=frozenset({"https://trust.epd.invalid/jwks"}),
            minimum_trust_version=4,
            now=NOW + timedelta(minutes=1),
        )


def test_voting_key_is_reference_only_without_generic_custody() -> None:
    svc = service()
    voting = svc.register(object_for(CredentialClass.VOTING_KEY_REFERENCE))
    assert voting.custody_ref is None
    assert voting.provider_ref is None
    with pytest.raises(AuthorizationRefused) as custody_error:
        svc.register(
            replace(
                object_for(CredentialClass.VOTING_KEY_REFERENCE, object_id="voting:bad"),
                provider_ref="provider:generic",
                custody_ref="custody:generic",
            )
        )
    assert custody_error.value.reason_code == Refusal.VOTING_BOUNDARY
    with pytest.raises(AuthorizationRefused) as error:
        svc.request_operation(
            request_id="vote-revoke",
            operation=LifecycleOperation.REVOKE,
            target_id=voting.object_id,
            requester_id="requester",
            reason="forbidden generic action",
            evidence_refs=("evidence:1",),
            now=NOW,
            expires_at=NOW + timedelta(hours=1),
            idempotency_key="vote-revoke",
        )
    assert error.value.reason_code == Refusal.VOTING_BOUNDARY


def test_revoked_and_expired_assertions_fail_closed() -> None:
    svc = service()
    item = svc.register(replace(object_for(), state=LifecycleState.REVOKED))
    with pytest.raises(AuthorizationRefused):
        svc.validate_assertion(
            item.object_id,
            expected_purpose=item.purpose,
            expected_scope=BERLIN,
            trusted_locations=frozenset({"https://trust.epd.invalid/jwks"}),
            minimum_trust_version=3,
            now=NOW,
        )

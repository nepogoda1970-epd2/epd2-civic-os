from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl03_builders import BAVARIA, BERLIN, NOW, object_for, service
from epd2_control_plane_service.credential_lifecycle import (
    CredentialClass,
    LifecycleState,
    Refusal,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused


def test_regional_issuance_accepts_exact_scope_without_root_hot_path() -> None:
    svc = service()
    item = object_for(CredentialClass.MTLS_CERTIFICATE, object_id="mtls:berlin:1")

    registered = svc.request_regional_issuance(
        item,
        issuer_scope=BERLIN,
        root_hot_path=False,
    )

    assert registered.object_id == item.object_id


@pytest.mark.parametrize(
    ("issuer_scope", "root_hot_path", "reason"),
    [
        (BAVARIA, False, Refusal.WRONG_SCOPE),
        (BERLIN, True, "ROOT_HOT_PATH"),
    ],
)
def test_regional_issuance_rejects_scope_escape_and_root_hot_path(
    issuer_scope, root_hot_path: bool, reason: str
) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        service().request_regional_issuance(
            object_for(CredentialClass.SERVICE_CREDENTIAL),
            issuer_scope=issuer_scope,
            root_hot_path=root_hot_path,
        )

    assert error.value.reason_code == reason


def test_regional_issuer_cannot_issue_human_credentials() -> None:
    with pytest.raises(AuthorizationRefused) as error:
        service().request_regional_issuance(
            object_for(CredentialClass.HUMAN_CREDENTIAL),
            issuer_scope=BERLIN,
            root_hot_path=False,
        )

    assert error.value.reason_code == Refusal.WRONG_PURPOSE


def test_recovery_ceremony_preserves_threshold_and_requires_real_quorum() -> None:
    svc = service()
    ceremony = svc.begin_recovery_ceremony(
        ceremony_id="recovery:1",
        key_reference="keyref:service:1",
        participant_ids=("custodian-a", "custodian-b", "custodian-c"),
        threshold=2,
        previous_threshold=2,
        evidence_ref="evidence:recovery:1",
        now=NOW,
    )
    assert ceremony.state is LifecycleState.REQUESTED

    with pytest.raises(AuthorizationRefused) as error:
        svc.complete_recovery_ceremony(
            ceremony.ceremony_id,
            approving_participants=("custodian-a", "custodian-a"),
            now=NOW + timedelta(minutes=1),
        )
    assert error.value.reason_code == Refusal.QUORUM

    completed = svc.complete_recovery_ceremony(
        ceremony.ceremony_id,
        approving_participants=("custodian-a", "custodian-b"),
        now=NOW + timedelta(minutes=2),
    )
    assert completed.state is LifecycleState.COMPLETED


@pytest.mark.parametrize(
    ("participants", "threshold", "previous_threshold"),
    [
        (("a", "b", "c"), 1, 2),
        (("a", "b", "c"), 2, 3),
        (("a", "a", "b"), 2, 2),
    ],
)
def test_recovery_ceremony_rejects_weak_or_duplicate_quorum(
    participants: tuple[str, ...], threshold: int, previous_threshold: int
) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        service().begin_recovery_ceremony(
            ceremony_id="bad-recovery",
            key_reference="keyref:service:1",
            participant_ids=participants,
            threshold=threshold,
            previous_threshold=previous_threshold,
            evidence_ref="evidence:bad",
            now=NOW,
        )

    assert error.value.reason_code == Refusal.QUORUM


def test_voting_recovery_remains_outside_generic_control_plane() -> None:
    with pytest.raises(AuthorizationRefused) as error:
        service().begin_recovery_ceremony(
            ceremony_id="voting-recovery",
            key_reference="voting:keyref:1",
            participant_ids=("a", "b", "c"),
            threshold=2,
            previous_threshold=2,
            evidence_ref="evidence:voting",
            now=NOW,
        )

    assert error.value.reason_code == Refusal.VOTING_BOUNDARY


def test_secret_access_review_follows_expiry_and_is_independent() -> None:
    svc = service()
    svc.grant_secret_access(
        grant_id="secret-jit:review",
        actor_id="operator",
        target_ref="provider-secret:mail",
        capability="SECRET.USE_IN_CUSTODY_SESSION",
        scope=BERLIN,
        now=NOW,
        expires_at=NOW + timedelta(minutes=5),
        approval_refs=("approval:a", "approval:b"),
    )

    with pytest.raises(AuthorizationRefused) as active_error:
        svc.review_secret_access(
            "secret-jit:review", reviewer_id="reviewer", review_ref="review:early"
        )
    assert active_error.value.reason_code == "WRONG_STATE"

    svc.expire_due(NOW + timedelta(minutes=6))
    with pytest.raises(AuthorizationRefused) as self_error:
        svc.review_secret_access(
            "secret-jit:review", reviewer_id="operator", review_ref="review:self"
        )
    assert self_error.value.reason_code == "SELF_REVIEW"

    svc.review_secret_access(
        "secret-jit:review", reviewer_id="reviewer", review_ref="review:independent"
    )
    assert svc.checkpoint()["secret_grants"]["secret-jit:review"]["review_ref"] == (
        "review:independent"
    )

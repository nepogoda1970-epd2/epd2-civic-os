from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl03_builders import BERLIN, NOW, approve_security, execute, object_for, request, service
from epd2_control_plane_service.credential_lifecycle import (
    CTRL01_ACCEPTED_SHA256,
    CTRL02_WORKING_SHA256,
    CTRL03_ACTIONS,
    DIRECT_DB_COUNTS_AS_LIFECYCLE,
    FREEZE_REJECTS_POST_VALIDATION_CHANGE,
    MUTATION_FIXTURES_REQUIRED,
    SELF_STATE,
    UNIVERSAL_ADMIN_EXISTS,
    UNIVERSAL_SECRET_READER_EXISTS,
    CredentialClass,
    LifecycleOperation,
    LifecycleState,
    Refusal,
    action_inventory,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused


def test_secret_jit_is_short_exact_approved_and_returns_reference_only() -> None:
    svc = service()
    grant = svc.grant_secret_access(
        grant_id="secret-jit:1",
        actor_id="operator",
        target_ref="provider-secret:mail",
        capability="SECRET.USE_IN_CUSTODY_SESSION",
        scope=BERLIN,
        now=NOW,
        expires_at=NOW + timedelta(minutes=10),
        approval_refs=("approval:1", "approval:2"),
    )
    assert grant.expires_at - grant.valid_from <= timedelta(minutes=15)
    session_ref = svc.use_secret_access(
        grant.grant_id,
        actor_id="operator",
        now=NOW + timedelta(minutes=1),
        use_ref="use:1",
    )
    assert session_ref == "custody-session:secret-jit:1"
    assert "secret-value" not in session_ref


@pytest.mark.parametrize(
    ("minutes", "approvals"), [(16, ("a", "b")), (10, ("a",)), (10, ("a", "a"))]
)
def test_secret_jit_rejects_long_or_insufficient_grants(
    minutes: int, approvals: tuple[str, ...]
) -> None:
    with pytest.raises(AuthorizationRefused) as error:
        service().grant_secret_access(
            grant_id="bad",
            actor_id="operator",
            target_ref="provider-secret:mail",
            capability="SECRET.USE_IN_CUSTODY_SESSION",
            scope=BERLIN,
            now=NOW,
            expires_at=NOW + timedelta(minutes=minutes),
            approval_refs=approvals,
        )
    assert error.value.reason_code == Refusal.SECRET_VISIBILITY


def test_secret_jit_expiry_and_clock_rollback_do_not_revive() -> None:
    svc = service()
    svc.grant_secret_access(
        grant_id="secret-jit:1",
        actor_id="operator",
        target_ref="provider-secret:mail",
        capability="SECRET.USE_IN_CUSTODY_SESSION",
        scope=BERLIN,
        now=NOW,
        expires_at=NOW + timedelta(minutes=5),
        approval_refs=("a", "b"),
    )
    svc.expire_due(NOW + timedelta(minutes=6))
    with pytest.raises(AuthorizationRefused):
        svc.use_secret_access(
            "secret-jit:1",
            actor_id="operator",
            now=NOW + timedelta(minutes=1),
            use_ref="rollback",
        )


def test_secret_jit_cannot_be_used_after_expiry_without_sweeper() -> None:
    svc = service()
    svc.grant_secret_access(
        grant_id="secret-jit:direct-expiry",
        actor_id="operator",
        target_ref="provider-secret:mail",
        capability="SECRET.USE_IN_CUSTODY_SESSION",
        scope=BERLIN,
        now=NOW,
        expires_at=NOW + timedelta(minutes=5),
        approval_refs=("a", "b"),
    )
    with pytest.raises(AuthorizationRefused) as error:
        svc.use_secret_access(
            "secret-jit:direct-expiry",
            actor_id="operator",
            now=NOW + timedelta(minutes=6),
            use_ref="late-use",
        )
    assert error.value.reason_code == Refusal.EXPIRED


def test_safe_read_model_has_no_secret_or_excess_identity_fields() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PROVIDER_SECRET))
    model = svc.safe_read_model()[0]
    forbidden = {"private_key", "raw_secret", "token", "password_verifier", "subject_ref"}
    assert not forbidden & set(model)


def test_audit_is_hash_linked_append_only_and_contains_no_secret() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    approve_security(svc)
    execute(svc)
    events = svc.events
    assert events[0].previous_hash == "GENESIS"
    assert all(
        events[index].previous_hash == events[index - 1].event_hash
        for index in range(1, len(events))
    )
    assert "PRIVATE KEY" not in str(events)


def test_action_inventory_is_complete_unique_and_reauthorized() -> None:
    exported = action_inventory()
    assert len(exported) == len(CTRL03_ACTIONS)
    assert len({item.action_id for item in CTRL03_ACTIONS}) == len(CTRL03_ACTIONS)
    assert len({item.route for item in CTRL03_ACTIONS}) == len(CTRL03_ACTIONS)
    mutations = [item for item in CTRL03_ACTIONS if item.quorum > 0]
    assert all(item.commit_reauthorization and item.evidence_output for item in mutations)


def test_meta_governance_invariants() -> None:
    assert UNIVERSAL_ADMIN_EXISTS is False
    assert UNIVERSAL_SECRET_READER_EXISTS is False
    assert DIRECT_DB_COUNTS_AS_LIFECYCLE is False
    assert SELF_STATE == "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
    assert MUTATION_FIXTURES_REQUIRED == 44
    assert FREEZE_REJECTS_POST_VALIDATION_CHANGE is True
    assert CTRL01_ACCEPTED_SHA256.startswith("07134db1")
    assert CTRL02_WORKING_SHA256.startswith("f58bafe7")


def test_compromise_is_preserved_across_checkpoint_and_requires_review() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc, operation=LifecycleOperation.CONTAIN_COMPROMISE)
    approve_security(svc)
    from _ctrl03_builders import approve_trust

    approve_trust(svc)
    updated = execute(svc)
    assert updated.state is LifecycleState.COMPROMISED
    snapshot = svc.checkpoint()
    assert snapshot["objects"]["credential:old"]["compromised"] is True
    assert svc.requests[0].review_ref is None

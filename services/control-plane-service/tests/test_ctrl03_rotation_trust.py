from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from _ctrl03_builders import (
    BERLIN,
    NOW,
    approve_security,
    approve_trust,
    execute,
    object_for,
    request,
    service,
)
from epd2_control_plane_service.credential_lifecycle import (
    CredentialClass,
    LifecycleOperation,
    LifecycleState,
    Refusal,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused


def test_rotation_requires_old_new_link_and_bounded_overlap() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.SERVICE_CREDENTIAL))
    svc.register(
        object_for(
            CredentialClass.SERVICE_CREDENTIAL,
            object_id="credential:new",
            parent_id="credential:old",
            state=LifecycleState.REQUESTED,
        )
    )
    request(
        svc,
        operation=LifecycleOperation.ROTATE,
        new_object_id="credential:new",
        overlap_until=NOW + timedelta(hours=1),
    )
    approve_security(svc)
    updated = execute(svc)
    states = {item.object_id: item.state for item in svc.objects}
    assert updated.state is LifecycleState.ROTATING
    assert states["credential:new"] is LifecycleState.ACTIVE


def test_rotation_rejects_missing_link_and_indefinite_overlap() -> None:
    svc = service()
    svc.register(object_for())
    svc.register(object_for(object_id="credential:new", state=LifecycleState.REQUESTED))
    with pytest.raises(AuthorizationRefused):
        request(
            svc,
            operation=LifecycleOperation.ROTATE,
            new_object_id="credential:new",
            overlap_until=NOW + timedelta(days=2),
        )


def test_rotation_rejects_unlinked_replacement_at_execution() -> None:
    svc = service()
    svc.register(object_for())
    svc.register(object_for(object_id="credential:new", state=LifecycleState.REQUESTED))
    request(
        svc,
        operation=LifecycleOperation.ROTATE,
        new_object_id="credential:new",
        overlap_until=NOW + timedelta(hours=1),
    )
    approve_security(svc)
    with pytest.raises(AuthorizationRefused) as error:
        execute(svc)
    assert error.value.reason_code == "ROTATION_LINK"


def test_versioned_trust_set_rejects_stale_in_place_replacement() -> None:
    svc = service()
    v1 = svc.publish_trust_version(
        trust_set_id="regional-jwks",
        entries=("key-1",),
        now=NOW,
        previous_version=None,
    )
    v2 = svc.publish_trust_version(
        trust_set_id="regional-jwks",
        entries=("key-1", "key-2"),
        now=NOW + timedelta(minutes=1),
        previous_version=1,
    )
    assert v2.previous_version == v1.version
    with pytest.raises(AuthorizationRefused) as error:
        svc.publish_trust_version(
            trust_set_id="regional-jwks",
            entries=("attacker",),
            now=NOW + timedelta(minutes=2),
            previous_version=1,
        )
    assert error.value.reason_code == Refusal.STALE_TRUST_SET


def test_cross_region_rotation_is_rejected() -> None:
    from _ctrl03_builders import BAVARIA

    svc = service()
    svc.register(object_for())
    svc.register(
        object_for(
            object_id="credential:new",
            parent_id="credential:old",
            scope=BAVARIA,
            state=LifecycleState.REQUESTED,
        )
    )
    request(
        svc,
        operation=LifecycleOperation.ROTATE,
        new_object_id="credential:new",
        overlap_until=NOW + timedelta(hours=1),
    )
    approve_security(svc)
    with pytest.raises(AuthorizationRefused) as error:
        execute(svc)
    assert error.value.reason_code == Refusal.WRONG_PURPOSE


def test_high_impact_signing_rotation_needs_two_classes() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    svc.register(
        object_for(
            CredentialClass.JWS_SIGNING_KEY,
            object_id="credential:new",
            parent_id="credential:old",
            state=LifecycleState.REQUESTED,
        )
    )
    request(
        svc,
        operation=LifecycleOperation.ROTATE,
        new_object_id="credential:new",
        overlap_until=NOW + timedelta(hours=1),
    )
    approve_security(svc)
    with pytest.raises(AuthorizationRefused):
        execute(svc)
    approve_trust(svc)
    assert execute(svc).state is LifecycleState.ROTATING


def test_provider_drift_detects_silent_rotation() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    approve_security(svc)
    svc.provider.versions["credential:old"] += 1
    with pytest.raises(AuthorizationRefused) as error:
        execute(svc)
    assert error.value.reason_code == Refusal.STALE_PROVIDER


def test_wrong_region_assertion_is_not_hierarchy_inherited() -> None:
    svc = service()
    item = svc.register(object_for())
    with pytest.raises(AuthorizationRefused) as error:
        svc.validate_assertion(
            item.object_id,
            expected_purpose=item.purpose,
            expected_scope=replace(BERLIN, region_id="DE-BY", org_id="org-bavaria"),
            trusted_locations=frozenset({item.trust_location or ""}),
            minimum_trust_version=3,
            now=NOW,
        )
    assert error.value.reason_code == Refusal.WRONG_SCOPE

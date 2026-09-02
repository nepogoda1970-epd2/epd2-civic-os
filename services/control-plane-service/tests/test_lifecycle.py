"""W5 — credential, access and key lifecycle control surfaces."""

from __future__ import annotations

import pytest
from _control_plane_builders import LAND_BE, PLATFORM, T0, World, run_governed_flow
from epd2_control_plane_service.domain import (
    AuthorityState,
    CredentialClass,
    CredentialState,
    Right,
    TrustKeyReference,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused, VotingBoundaryViolation
from epd2_control_plane_service.inventory import INVENTORY


def test_all_seven_control_object_classes_are_represented() -> None:
    assert {c.value for c in CredentialClass} == {
        "HUMAN_AUTHENTICATOR",
        "RECOVERY_FACTOR",
        "SESSION_ARTIFACT",
        "SERVICE_WORKLOAD",
        "PLATFORM_KEY",
        "PROVIDER_SECRET",
        "VOTING_DOMAIN",
    }


def test_revoked_credential_is_never_resurrected(world: World) -> None:
    world.directory.set_human_credential_state("cred.p.ordinary.member", CredentialState.REVOKED)
    with pytest.raises(AuthorizationRefused) as excinfo:
        world.directory.set_human_credential_state("cred.p.ordinary.member", CredentialState.ACTIVE)
    assert excinfo.value.reason_code == "CTRL_CREDENTIAL_RESURRECTION"


def test_replacement_creates_a_new_identity_and_links_forward(world: World) -> None:
    world.directory.set_human_credential_state(
        "cred.p.ordinary.member", CredentialState.REPLACED, replaced_by="cred.member.2"
    )
    world.directory.put_human_credential(
        "cred.member.2", "p.ordinary.member", CredentialState.ACTIVE
    )
    old = world.directory.human_credential("cred.p.ordinary.member")
    assert old is not None and old[1] is CredentialState.REPLACED and old[2] == "cred.member.2"


def test_recovery_does_not_restore_a_suspended_organizational_authority(world: World) -> None:
    """FIR-SEC-004: recovery restores the ability to authenticate and nothing
    else. The suspended office stays suspended."""
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.SUSPENDED, recorded_at=T0, recorded_by="governance"
    )
    world.directory.set_human_credential_state(
        "cred.p.land.be.chair", CredentialState.RECOVERY_REQUIRED
    )

    run_governed_flow(
        world,
        request_id="req-recovery",
        action_id="CRED.HIGH_ASSURANCE_RECOVERY",
        requester="p.credential.operator",
        approvers=("p.recovery.approver", "p.recovery.second"),
        executor="p.credential.operator",
        scope=PLATFORM,
        object_ref="cred.p.land.be.chair",
    )
    world.directory.set_human_credential_state("cred.p.land.be.chair", CredentialState.ACTIVE)

    authority = world.directory.current_authority("a.land.be.chair")
    assert authority is not None and authority.state is AuthorityState.SUSPENDED

    with pytest.raises(AuthorizationRefused) as excinfo:
        world.plane.submit_request(
            request_id="req-after-recovery",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="post-recovery attempt",
            moment=T0,
        )
    assert excinfo.value.reason_code == "CTRL_AUTHORITY_SUSPENDED"


def test_voting_domain_key_is_an_external_reference_only(world: World) -> None:
    reference = world.directory.key_reference("key.voting.trustee.1")
    assert reference is not None
    assert reference.credential_class is CredentialClass.VOTING_DOMAIN
    assert reference.exportable is False
    for action_id in ("KEY.ROTATE", "KEY.DESTROY", "KEY.MARK_COMPROMISED"):
        with pytest.raises(VotingBoundaryViolation):
            world.plane.submit_request(
                request_id=f"req-voting-{action_id.split('.')[-1].lower()}",
                action_id=action_id,
                principal_id="p.key.custodian"
                if action_id != "KEY.MARK_COMPROMISED"
                else "p.security.operator",
                session_id="s.p.key.custodian"
                if action_id != "KEY.MARK_COMPROMISED"
                else "s.p.security.operator",
                scope=PLATFORM,
                object_ref="key.voting.trustee.1",
                purpose="attempt to operate voting key",
                moment=T0,
            )


def test_voting_key_reference_can_never_be_marked_exportable() -> None:
    with pytest.raises(ValueError, match="never exportable"):
        TrustKeyReference(
            key_reference_id="key.voting.bad",
            key_class="VOTING_TRUSTEE",
            credential_class=CredentialClass.VOTING_DOMAIN,
            algorithm="Ed25519",
            trust_state="CURRENT",
            custody_policy_ref="VOTING-TRUSTEE-POLICY",
            exportable=True,
        )


def test_threshold_policy_must_be_complete_and_well_formed() -> None:
    with pytest.raises(ValueError, match="both quorum_m and quorum_n"):
        TrustKeyReference(
            key_reference_id="key.partial",
            key_class="PLATFORM_SIGNING",
            credential_class=CredentialClass.PLATFORM_KEY,
            algorithm="ES384",
            trust_state="CURRENT",
            custody_policy_ref="KEY-POLICY-2026-004",
            quorum_m=2,
        )
    with pytest.raises(ValueError, match="1 <= m <= n"):
        TrustKeyReference(
            key_reference_id="key.badquorum",
            key_class="PLATFORM_SIGNING",
            credential_class=CredentialClass.PLATFORM_KEY,
            algorithm="ES384",
            trust_state="CURRENT",
            custody_policy_ref="KEY-POLICY-2026-004",
            quorum_m=5,
            quorum_n=3,
        )


def test_key_destruction_requires_the_strongest_quorum() -> None:
    destroy = INVENTORY.get("KEY.DESTROY")
    assert destroy.quorum_required >= 3
    assert destroy.four_eyes
    assert destroy.required_right_execute is Right.DESTROY


def test_service_credential_actions_are_platform_scoped_and_human_operated() -> None:
    for action_id in ("SERVICE_CRED.ISSUE", "SERVICE_CRED.ROTATE", "SERVICE_CRED.REVOKE"):
        action = INVENTORY.get(action_id)
        assert action.scope_level.value == "PLATFORM"
        assert action.actor_class.value == "HUMAN"


def test_every_lifecycle_semantic_is_present_in_the_inventory() -> None:
    """Each of the FIR-SEC-004 lifecycle verbs must be exercised by at least one
    governed action; a verb with no action would be an unimplementable right."""
    exercised = {a.required_right_execute for a in INVENTORY}
    for right in (
        Right.ACTIVATE,
        Right.SUSPEND_OR_QUARANTINE,
        Right.REVOKE,
        Right.RESTORE,
        Right.ROTATE_OR_REPLACE,
        Right.DESTROY,
        Right.READ_METADATA,
        Right.VIEW_OR_EXPORT_SECRET,
        Right.REVIEW_OR_AUDIT,
    ):
        assert right in exercised, right

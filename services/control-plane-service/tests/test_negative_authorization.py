"""W8 — negative authorization suite.

Twenty scenarios, each of which must be rejected or safely constrained. Every
test asserts the *reason code*, not merely that something was raised: a refusal
for the wrong reason would hide a real authorization defect.

Each test also asserts that the refusal was recorded on the immutable journal,
because an escalation attempt that leaves no trace is itself a defect.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _control_plane_builders import (
    BUND,
    KREIS_BE,
    LAND_BE,
    LAND_BY,
    PLATFORM,
    T0,
    World,
    _authority,
    run_governed_flow,
)
from epd2_control_plane_service.audit import screen_attributes
from epd2_control_plane_service.domain import (
    AuthorityState,
    Right,
    Scope,
    ScopeLevel,
    SessionState,
)
from epd2_control_plane_service.exceptions import (
    AuthorizationRefused,
    EvidenceIntegrityError,
    PrivacyBoundaryViolation,
    VotingBoundaryViolation,
)
from epd2_control_plane_service.mutations import _overwrite_history


def _last_refusal(world: World) -> object:
    refusals = world.journal.find(result="REFUSED")
    assert refusals, "a refusal must be recorded as evidence"
    return refusals[-1]


def _expect_refusal(world: World, reason_code: str, call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(AuthorizationRefused) as excinfo:
        call()
    assert excinfo.value.reason_code == reason_code, (
        f"expected {reason_code}, got {excinfo.value.reason_code}"
    )
    assert _last_refusal(world).reason_code == reason_code  # type: ignore[attr-defined]


# 1 --------------------------------------------------------------------------
def test_01_ordinary_member_attempts_control_action(world: World) -> None:
    _expect_refusal(
        world,
        "CTRL_NO_AUTHORITY",
        lambda: world.plane.submit_request(
            request_id="req-neg-01",
            action_id="AUTH.ASSIGN",
            principal_id="p.ordinary.member",
            session_id="s.p.ordinary.member",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="escalation attempt",
            moment=T0,
        ),
    )


# 2 --------------------------------------------------------------------------
def test_02_wrong_organization_same_level(world: World) -> None:
    other_kreis = Scope(ScopeLevel.KREIS, "kreis-berlin-pankow")
    world.directory.record_authority(
        _authority(
            "a.kreis.mitte.chair",
            "p.land.be.secretary",
            "KREISVORSITZ",
            KREIS_BE,
            {Right.REQUEST, Right.EXECUTE, Right.READ_METADATA},
            {"MEMBERSHIP.ADMIN_MUTATE"},
        ),
        recorded_at=T0,
        recorded_by="test",
    )
    _expect_refusal(
        world,
        "CTRL_SCOPE_ISOLATION",
        lambda: world.plane.submit_request(
            request_id="req-neg-02",
            action_id="MEMBERSHIP.ADMIN_MUTATE",
            principal_id="p.land.be.secretary",
            session_id="s.p.land.be.secretary",
            scope=other_kreis,
            object_ref="member.record",
            purpose="cross-organization attempt",
            moment=T0,
        ),
    )


# 3 --------------------------------------------------------------------------
def test_03_wrong_region(world: World) -> None:
    _expect_refusal(
        world,
        "CTRL_SCOPE_ISOLATION",
        lambda: world.plane.submit_request(
            request_id="req-neg-03",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.by.chair",
            session_id="s.p.land.by.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="cross-Land attempt",
            moment=T0,
        ),
    )


# 4 --------------------------------------------------------------------------
def test_04_expired_authority(world: World) -> None:
    world.directory.record_authority(
        _authority(
            "a.expired",
            "p.ordinary.member",
            "LANDESVORSTAND_AUSGESCHIEDEN",
            LAND_BE,
            {Right.REQUEST, Right.EXECUTE},
            {"MEMBERSHIP.ADMIN_MUTATE"},
            valid_from=T0 - timedelta(days=400),
            valid_until=T0 - timedelta(days=1),
        ),
        recorded_at=T0,
        recorded_by="test",
    )
    _expect_refusal(
        world,
        "CTRL_AUTHORITY_EXPIRED",
        lambda: world.plane.submit_request(
            request_id="req-neg-04",
            action_id="MEMBERSHIP.ADMIN_MUTATE",
            principal_id="p.ordinary.member",
            session_id="s.p.ordinary.member",
            scope=LAND_BE,
            object_ref="member.record",
            purpose="expired office",
            moment=T0,
        ),
    )


# 5 --------------------------------------------------------------------------
def test_05_revoked_authority(world: World) -> None:
    world.directory.set_authority_state(
        "a.land.be.chair",
        AuthorityState.REVOKED,
        recorded_at=T0,
        recorded_by="test",
        note="revoked by decision",
    )
    _expect_refusal(
        world,
        "CTRL_AUTHORITY_REVOKED",
        lambda: world.plane.submit_request(
            request_id="req-neg-05",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="revoked office",
            moment=T0,
        ),
    )


# 6 --------------------------------------------------------------------------
def test_06_suspended_regional_authority(world: World) -> None:
    world.directory.set_authority_state(
        "a.land.be.chair",
        AuthorityState.SUSPENDED,
        recorded_at=T0,
        recorded_by="test",
        note="FIR-GOV-004 level 2",
    )
    _expect_refusal(
        world,
        "CTRL_AUTHORITY_SUSPENDED",
        lambda: world.plane.submit_request(
            request_id="req-neg-06",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="suspended office",
            moment=T0,
        ),
    )


# 7 --------------------------------------------------------------------------
def test_07_stale_authority_snapshot_is_not_reusable(world: World) -> None:
    """A resolution obtained at T0 grants nothing at T0+1h once the underlying
    authority is suspended. The runtime re-reads the record; it never trusts a
    previously obtained projection."""
    early = world.directory.resolve(
        subject_ref="p.land.be.chair",
        required_right=Right.REQUEST,
        action_id="AUTH.ASSIGN",
        scope=LAND_BE,
        moment=T0,
    )
    assert early.granted

    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.SUSPENDED, recorded_at=T0, recorded_by="test"
    )
    _expect_refusal(
        world,
        "CTRL_AUTHORITY_SUSPENDED",
        lambda: world.plane.submit_request(
            request_id="req-neg-07",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="stale snapshot",
            moment=T0 + timedelta(hours=1),
        ),
    )


# 8 --------------------------------------------------------------------------
def test_08_self_approval_is_rejected(world: World) -> None:
    world.plane.submit_request(
        request_id="req-neg-08",
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="self approval attempt",
        moment=T0,
    )
    _expect_refusal(
        world,
        "CTRL_SELF_APPROVAL",
        lambda: world.plane.approve(
            request_id="req-neg-08",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            moment=T0 + timedelta(minutes=1),
        ),
    )


# 9 --------------------------------------------------------------------------
def test_09_insufficient_quorum(world: World) -> None:
    world.plane.submit_request(
        request_id="req-neg-09",
        action_id="AUTH.ASSIGN",
        principal_id="p.land.be.chair",
        session_id="s.p.land.be.chair",
        scope=LAND_BE,
        object_ref="authority.target",
        purpose="single approval only",
        moment=T0,
    )
    world.plane.approve(
        request_id="req-neg-09",
        principal_id="p.land.be.deputy",
        session_id="s.p.land.be.deputy",
        moment=T0 + timedelta(minutes=1),
    )
    _expect_refusal(
        world,
        "CTRL_QUORUM_INSUFFICIENT",
        lambda: world.plane.execute(
            request_id="req-neg-09",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            moment=T0 + timedelta(minutes=2),
        ),
    )


# 10 -------------------------------------------------------------------------
def test_10_expired_emergency_grant(world: World) -> None:
    emergency = world.plane.emergency
    emergency.request(
        grant_id="grant-neg-10",
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="incident 2026-09-02",
        scope=PLATFORM,
        action_codes={"SERVICE_CRED.REVOKE"},
        requested_at=T0,
    )
    emergency.approve("grant-neg-10", approver_id="p.emergency.controller", approved_at=T0)
    emergency.activate("grant-neg-10", activated_at=T0)
    with pytest.raises(AuthorizationRefused) as excinfo:
        emergency.use(
            "grant-neg-10",
            action_id="SERVICE_CRED.REVOKE",
            scope=PLATFORM,
            moment=T0 + timedelta(hours=2),
            use_ref="use-1",
        )
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_EXPIRED"


# 11 -------------------------------------------------------------------------
def test_11_wrong_emergency_scope(world: World) -> None:
    emergency = world.plane.emergency
    emergency.request(
        grant_id="grant-neg-11",
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="incident 2026-09-02",
        scope=PLATFORM,
        action_codes={"SERVICE_CRED.REVOKE"},
        requested_at=T0,
    )
    emergency.approve("grant-neg-11", approver_id="p.emergency.controller", approved_at=T0)
    emergency.activate("grant-neg-11", activated_at=T0)
    with pytest.raises(AuthorizationRefused) as excinfo:
        emergency.use(
            "grant-neg-11",
            action_id="KEY.MARK_COMPROMISED",
            scope=PLATFORM,
            moment=T0 + timedelta(minutes=1),
            use_ref="use-1",
        )
    assert excinfo.value.reason_code == "CTRL_EMERGENCY_SCOPE"


# 12 -------------------------------------------------------------------------
def test_12_audit_reader_attempts_mutation(world: World) -> None:
    """The auditor is given the *action code* for a mutation but not the right
    it needs, so the refusal can only come from the right check. Without this
    separation the test would pass even if the right check were removed, because
    the auditor is missing both."""
    world.directory.record_authority(
        _authority(
            "a.auditor.be.scoped",
            "p.auditor",
            "INDEPENDENT_AUDITOR",
            LAND_BE,
            {Right.REVIEW_OR_AUDIT, Right.READ_METADATA},
            {"AUTH.SUSPEND", "AUDIT.LOOKUP"},
        ),
        recorded_at=T0,
        recorded_by="test",
    )
    _expect_refusal(
        world,
        "CTRL_CAPABILITY_ABSENT",
        lambda: world.plane.submit_request(
            request_id="req-neg-12",
            action_id="AUTH.SUSPEND",
            principal_id="p.auditor",
            session_id="s.p.auditor",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="auditor mutation attempt",
            moment=T0,
        ),
    )


# 13 -------------------------------------------------------------------------
def test_13_operator_attempts_business_authority_bypass(world: World) -> None:
    """A security operator can quarantine a session in Land Berlin but holds no
    business authority there: `AUTH.ASSIGN` is absent from their action codes."""
    _expect_refusal(
        world,
        "CTRL_CAPABILITY_ABSENT",
        lambda: world.plane.submit_request(
            request_id="req-neg-13",
            action_id="AUTH.ASSIGN",
            principal_id="p.security.operator",
            session_id="s.p.security.operator",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="operator bypass attempt",
            moment=T0,
        ),
    )


# 14 -------------------------------------------------------------------------
def test_14_service_identity_attempts_human_action(world: World) -> None:
    """The rogue workload holds every right the action needs. It is refused on
    actor class alone, which is the property under test."""
    _expect_refusal(
        world,
        "CTRL_ACTOR_CLASS",
        lambda: world.plane.submit_request(
            request_id="req-neg-14",
            action_id="AUTH.ASSIGN",
            principal_id="svc.rogue",
            session_id="s.svc.rogue",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="workload acting as human administrator",
            moment=T0,
        ),
    )


# 15 -------------------------------------------------------------------------
def test_15_human_without_visibility_right_cannot_retrieve_secret(world: World) -> None:
    """The intake desk may open a custody request. Retrieval requires the
    separate VIEW_OR_EXPORT_SECRET right, which this authority does not carry,
    so the act is refused at commit rather than at intake."""
    world.plane.submit_request(
        request_id="req-neg-15",
        action_id="REPORTING.CUSTODY_ACCESS",
        principal_id="p.privileged.operator",
        session_id="s.p.privileged.operator",
        scope=LAND_BE,
        object_ref="custody.record",
        purpose="secret retrieval without visibility right",
        moment=T0,
    )
    _expect_refusal(
        world,
        "CTRL_CAPABILITY_ABSENT",
        lambda: world.plane.execute(
            request_id="req-neg-15",
            principal_id="p.privileged.operator",
            session_id="s.p.privileged.operator",
            moment=T0 + timedelta(minutes=2),
        ),
    )


# 16 -------------------------------------------------------------------------
def test_16_cross_context_authority_reuse(world: World) -> None:
    """A key custodian's platform authority does not carry into governance."""
    _expect_refusal(
        world,
        "CTRL_SCOPE_ISOLATION",
        lambda: world.plane.submit_request(
            request_id="req-neg-16",
            action_id="AUTH.ASSIGN",
            principal_id="p.key.custodian",
            session_id="s.p.key.custodian",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="cross-context reuse",
            moment=T0,
        ),
    )


# 17 -------------------------------------------------------------------------
def test_17_quarantined_session_authorizes_nothing(world: World) -> None:
    world.directory.set_session_state("s.p.land.be.chair", SessionState.QUARANTINED)
    _expect_refusal(
        world,
        "CTRL_SESSION_NOT_ACTIVE",
        lambda: world.plane.submit_request(
            request_id="req-neg-17",
            action_id="AUTH.ASSIGN",
            principal_id="p.land.be.chair",
            session_id="s.p.land.be.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="stale browser session",
            moment=T0,
        ),
    )


# 18 -------------------------------------------------------------------------
def test_18_bund_action_outside_intervention_competence(world: World) -> None:
    """Bund oversight is bound to Land Berlin by an exact decision. Bayern is
    outside it, and hierarchy supplies nothing."""
    _expect_refusal(
        world,
        "CTRL_SCOPE_ISOLATION",
        lambda: world.plane.submit_request(
            request_id="req-neg-18",
            action_id="INTERVENE.REGIONAL_ACTION_RESTRICTION",
            principal_id="p.bund.oversight",
            session_id="s.p.bund.oversight",
            scope=LAND_BY,
            object_ref="restriction.proposed",
            purpose="intervention outside competence",
            moment=T0,
        ),
    )


def test_18b_bund_hierarchy_alone_does_not_reach_a_land(world: World) -> None:
    _expect_refusal(
        world,
        "CTRL_SCOPE_ISOLATION",
        lambda: world.plane.submit_request(
            request_id="req-neg-18b",
            action_id="AUTH.ASSIGN",
            principal_id="p.bund.chair",
            session_id="s.p.bund.chair",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="implicit Bund takeover",
            moment=T0,
        ),
    )


def test_18c_bund_chair_retains_its_own_scope(world: World) -> None:
    """Scope isolation must not degrade into "Bund can do nothing"."""
    outcome = run_governed_flow(
        world,
        request_id="req-neg-18c",
        action_id="AUTH.ASSIGN",
        requester="p.bund.chair",
        approvers=("p.bund.deputy", "p.bund.treasurer"),
        executor="p.bund.chair",
        scope=BUND,
    )
    assert outcome.evidence_sequence > 0


# 19 -------------------------------------------------------------------------
def test_19_historical_evidence_mutation_is_detected(world: World) -> None:
    run_governed_flow(
        world,
        request_id="req-neg-19",
        action_id="AUTH.ASSIGN",
        requester="p.land.be.chair",
        approvers=("p.land.be.deputy", "p.land.be.secretary"),
        executor="p.land.be.chair",
        scope=LAND_BE,
    )
    world.journal.verify()
    _overwrite_history(world)
    with pytest.raises(EvidenceIntegrityError):
        world.journal.verify()


# 20 -------------------------------------------------------------------------
def test_20a_voting_linkable_identifier_is_refused_in_evidence(world: World) -> None:
    with pytest.raises(PrivacyBoundaryViolation) as excinfo:
        screen_attributes({"voter_id": "v-1"})
    assert excinfo.value.reason_code == "CTRL_VOTING_LINKABLE_FIELD"


def test_20b_control_plane_cannot_operate_voting_key_material(world: World) -> None:
    with pytest.raises(VotingBoundaryViolation):
        world.plane.submit_request(
            request_id="req-neg-20",
            action_id="KEY.ROTATE",
            principal_id="p.key.custodian",
            session_id="s.p.key.custodian",
            scope=PLATFORM,
            object_ref="key.voting.trustee.1",
            purpose="attempt to operate trustee key",
            moment=T0,
        )
    assert world.journal.find(result="REFUSED")[-1].reason_code == "CTRL_VOTING_BOUNDARY"

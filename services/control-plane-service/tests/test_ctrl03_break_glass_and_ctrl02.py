from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl03_builders import NOW, approve_security, execute, object_for, request, service
from epd2_control_plane_service.credential_lifecycle import (
    BreakGlassPhase,
    CredentialClass,
    Refusal,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.regional_operations import ApproverClass


def _declared_case():
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    case = svc.declare_break_glass(
        case_id="break-glass:1",
        target_id="credential:old",
        requester_id="requester",
        reason="suspected signing-key compromise",
        evidence_refs=("incident:1",),
        now=NOW,
        expires_at=NOW + timedelta(minutes=30),
    )
    return svc, case


def test_break_glass_requires_quorum_separate_custodian_sequence_and_review() -> None:
    svc, case = _declared_case()
    assert case.phase is BreakGlassPhase.DECLARED
    first = svc.approve_break_glass(
        case.case_id,
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=1),
    )
    assert first.phase is BreakGlassPhase.DECLARED
    approved = svc.approve_break_glass(
        case.case_id,
        approver_id="trust-1",
        approver_class=ApproverClass.TRUST_CUSTODIAN,
        now=NOW + timedelta(minutes=2),
    )
    assert approved.phase is BreakGlassPhase.APPROVED

    with pytest.raises(AuthorizationRefused) as separation_error:
        svc.activate_break_glass(
            case.case_id, custodian_id="security-1", now=NOW + timedelta(minutes=3)
        )
    assert separation_error.value.reason_code == Refusal.EXECUTION_SEPARATION

    activated = svc.activate_break_glass(
        case.case_id, custodian_id="custodian", now=NOW + timedelta(minutes=3)
    )
    assert activated.phase is BreakGlassPhase.ACTIVE
    for phase, minute in (
        (BreakGlassPhase.CONTAINED, 4),
        (BreakGlassPhase.REMEDIATED, 5),
        (BreakGlassPhase.VERIFIED, 6),
    ):
        activated = svc.advance_break_glass(
            case.case_id, next_phase=phase, now=NOW + timedelta(minutes=minute)
        )
        assert activated.phase is phase

    with pytest.raises(AuthorizationRefused):
        svc.review_break_glass(case.case_id, reviewer_id="custodian", review_ref="review:self")
    reviewed = svc.review_break_glass(
        case.case_id, reviewer_id="reviewer", review_ref="review:independent"
    )
    assert reviewed.phase is BreakGlassPhase.REVIEWED
    assert reviewed.review_ref == "review:independent"


def test_break_glass_is_short_lived_and_auto_expires() -> None:
    svc = service()
    svc.register(object_for(CredentialClass.JWS_SIGNING_KEY))
    with pytest.raises(AuthorizationRefused):
        svc.declare_break_glass(
            case_id="too-long",
            target_id="credential:old",
            requester_id="requester",
            reason="incident",
            evidence_refs=("incident:2",),
            now=NOW,
            expires_at=NOW + timedelta(hours=2),
        )

    svc, case = _declared_case()
    assert case.case_id in svc.expire_due(NOW + timedelta(minutes=31))
    assert svc.checkpoint()["break_glass"][case.case_id]["phase"] is BreakGlassPhase.EXPIRED


def test_break_glass_reauthorizes_approvers_at_activation() -> None:
    svc, case = _declared_case()
    svc.approve_break_glass(
        case.case_id,
        approver_id="security-1",
        approver_class=ApproverClass.SECURITY,
        now=NOW + timedelta(minutes=1),
    )
    svc.approve_break_glass(
        case.case_id,
        approver_id="trust-1",
        approver_class=ApproverClass.TRUST_CUSTODIAN,
        now=NOW + timedelta(minutes=2),
    )
    svc.authorities.update("trust1")
    with pytest.raises(AuthorizationRefused):
        svc.activate_break_glass(
            case.case_id, custodian_id="custodian", now=NOW + timedelta(minutes=3)
        )


@pytest.mark.parametrize("restriction", ["restricted", "quarantined"])
def test_active_ctrl02_restrictions_fail_closed_at_commit(restriction: str) -> None:
    svc = service()
    svc.register(object_for(CredentialClass.PASSKEY))
    request(svc)
    approve_security(svc)
    if restriction == "restricted":
        svc.ctrl02.restricted_targets.add("credential:old")
    else:
        svc.ctrl02.quarantined_sessions.add("credential:old")
    with pytest.raises(AuthorizationRefused) as error:
        execute(svc)
    assert error.value.reason_code.startswith("CTRL02_")

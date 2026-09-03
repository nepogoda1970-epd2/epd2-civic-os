"""CTRL-05 authorization: mandate, exact scope, unit, plane, right, session.

Every test here asserts a *refusal reason code*, not merely that something
failed. A refusal without its own code would let two different failures look
the same to a reviewer.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl05_builders import (
    BAVARIA_UNIT,
    NOW,
    OPS_UNIT,
    PRIVACY_UNIT,
    R,
    World,
    _mandate,
)
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_console import ActionType
from epd2_control_plane_service.oversight_console import (
    FORBIDDEN_OPERATIONAL_RIGHTS,
    REVIEWER_MAY_EXECUTE_OPERATIONS,
    UNIVERSAL_AUDITOR_EXISTS,
    AuditRight,
    EvidenceQuery,
    FindingSeverity,
    OversightRefusal,
    OversightScope,
    OversightSession,
    ReviewState,
    SessionState,
)
from epd2_control_plane_service.oversight_sources import EvidencePlane


@pytest.fixture
def world() -> World:
    return World()


def refusal(exc: pytest.ExceptionInfo[AuthorizationRefused]) -> str:
    return str(exc.value.reason_code)


# -- there is no universal auditor -------------------------------------------


def test_no_universal_auditor_constant() -> None:
    assert UNIVERSAL_AUDITOR_EXISTS is False
    assert REVIEWER_MAY_EXECUTE_OPERATIONS is False


def test_wildcard_capability_grants_no_oversight(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="super-admin")
    assert refusal(exc) == OversightRefusal.UNIVERSAL_AUDITOR.value


def test_actor_without_mandate_sees_nothing(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="unmandated")
    assert refusal(exc) == OversightRefusal.NO_MANDATE.value


def test_operational_rights_are_not_oversight_rights() -> None:
    assert "OPS.EXECUTE" in FORBIDDEN_OPERATIONAL_RIGHTS
    assert "SECRET.RAW_READ" in FORBIDDEN_OPERATIONAL_RIGHTS
    assert "KEY.CUSTODY" in FORBIDDEN_OPERATIONAL_RIGHTS
    assert "AUTHORITY.UNIVERSAL_ADMIN" in FORBIDDEN_OPERATIONAL_RIGHTS


# -- exact scope, no inheritance ---------------------------------------------


def test_other_organization_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="bavaria-auditor", scope=OPS_UNIT)
    assert refusal(exc) == OversightRefusal.WRONG_ORGANIZATION_SCOPE.value


def test_own_organization_other_unit_is_refused(world: World) -> None:
    """Same organization, different oversight unit: nothing is inherited."""
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="privacy-officer", scope=OPS_UNIT)
    assert refusal(exc) == OversightRefusal.WRONG_UNIT_SCOPE.value


def test_mandate_holder_cannot_widen_its_own_query_scope(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="auditor", scope=PRIVACY_UNIT)
    assert refusal(exc) == OversightRefusal.WRONG_UNIT_SCOPE.value


def test_bavaria_auditor_sees_no_berlin_evidence(world: World) -> None:
    result = world.search(principal="bavaria-auditor", scope=BAVARIA_UNIT)
    assert result["matched"] == 0
    assert result["records"] == []


def test_coarse_scope_identifiers_are_rejected() -> None:
    for coarse in ("*", "ALL", "GLOBAL"):
        with pytest.raises(ValueError):
            OversightScope("DE-BE", coarse, "unit-operations-audit")


# -- plane scope --------------------------------------------------------------


def test_plane_outside_mandate_is_refused(world: World) -> None:
    """`read-only-auditor` holds a CTRL-02-only mandate as well as a full one;
    a plane-anchored open on a plane no mandate covers is refused."""
    world.service._mandates.pop("MND-readonly")
    seen = world.search(principal="read-only-auditor")
    assert not [r for r in seen["records"] if r["reference"]["plane"] == EvidencePlane.CTRL04.value]
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.evidence(
            actor_ref="read-only-auditor",
            session_id="sess-read-only-auditor",
            scope=OPS_UNIT,
            reference_key="CTRL-04:ctrl04-operations-console:ctrl04-event-00000001",
            now=world.tick(),
        )
    assert refusal(exc) == OversightRefusal.PLANE_NOT_IN_MANDATE.value


def test_plane_restricted_mandate_filters_search(world: World) -> None:
    world.service._mandates.pop("MND-readonly")
    result = world.search(principal="read-only-auditor")
    planes = {r["reference"]["plane"] for r in result["records"]}
    assert planes == {EvidencePlane.CTRL02.value}


# -- rights are disjoint ------------------------------------------------------


def test_read_right_does_not_carry_review(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(principal="read-only-auditor")
    assert refusal(exc) == OversightRefusal.NO_RIGHT.value


def test_review_right_does_not_carry_attest(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    with pytest.raises(AuthorizationRefused) as exc:
        world.prepare(case.case_id, "ATTEST", AuditRight.ATTEST, principal="auditor")
    assert refusal(exc) == OversightRefusal.NO_RIGHT.value


def test_read_right_does_not_carry_correlate(world: World) -> None:
    world.service._mandates.pop("MND-ctrl02-only")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.action_chain(
            actor_ref="read-only-auditor",
            session_id="sess-read-only-auditor",
            scope=OPS_UNIT,
            correlation_ref=world.ctrl04_correlation,
            now=world.tick(),
        )
    assert refusal(exc) == OversightRefusal.NO_RIGHT.value


def test_mandate_cannot_be_created_for_an_unbacked_right() -> None:
    with pytest.raises(ValueError, match="without a backing authority grant"):
        _mandate(
            "MND-bad",
            "auditor",
            OPS_UNIT,
            frozenset({R.READ, R.EXPORT}),
            {R.READ: "ag-read"},
        )


# -- the mandate is backed by a live CTRL-02 grant ---------------------------


def test_mandate_bound_to_a_missing_grant_is_stale(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="stale-auditor")
    assert refusal(exc) in {
        OversightRefusal.STALE_AUTHORITY.value,
        OversightRefusal.AUTHORITY_UNRESOLVABLE.value,
    }


def test_regranted_authority_makes_the_mandate_stale(world: World) -> None:
    """A re-issued grant is a different grant; the mandate must be re-issued
    too rather than silently following the new authority."""
    world.search()  # works before
    grant = world.authorities._grants["ag-read"]
    world.authorities._grants["ag-read"] = type(grant)(
        grant_id="ag-read-v2",
        actor_id=grant.actor_id,
        actor_class=grant.actor_class,
        capability=grant.capability,
        scope=grant.scope,
        version=2,
    )
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert refusal(exc) == OversightRefusal.STALE_AUTHORITY.value


def test_expired_mandate_is_refused(world: World) -> None:
    world.service._mandates["MND-auditor"] = _mandate(
        "MND-auditor",
        "auditor",
        OPS_UNIT,
        frozenset({R.READ}),
        {R.READ: "ag-read"},
        valid_from=NOW - timedelta(days=10),
        valid_until=NOW - timedelta(days=1),
    )
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert refusal(exc) == OversightRefusal.MANDATE_EXPIRED.value


def test_superseded_mandate_is_refused(world: World) -> None:
    world.service.register_mandate(
        _mandate(
            "MND-auditor-2",
            "auditor",
            OPS_UNIT,
            frozenset({R.READ}),
            {R.READ: "ag-read"},
        )
    )
    world.service._mandates.pop("MND-auditor-2")
    world.service.supersede_mandate("MND-auditor", "MND-auditor-next")
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert refusal(exc) == OversightRefusal.MANDATE_SUPERSEDED.value


def test_mandate_without_a_governing_rule_is_impossible() -> None:
    with pytest.raises(ValueError, match="rule_version"):
        _mandate(
            "MND-x",
            "auditor",
            OPS_UNIT,
            frozenset({R.READ}),
            {R.READ: "ag-read"},
        ).__class__(
            mandate_id="MND-x",
            subject_ref="auditor",
            scope=OPS_UNIT,
            planes=frozenset({EvidencePlane.CTRL02}),
            rights=frozenset({R.READ}),
            rule_version="",
            source_decision_ref="",
            authority_bindings=frozenset({("AUDIT.READ", "ag-read")}),
            valid_from=NOW,
            valid_until=NOW + timedelta(days=1),
        )


# -- sessions -----------------------------------------------------------------


def test_revoked_session_is_refused_on_read(world: World) -> None:
    world.service.revoke_session("sess-auditor")
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert refusal(exc) == OversightRefusal.SESSION_REVOKED.value


def test_expired_session_is_refused_on_read(world: World) -> None:
    world.service.open_session(
        OversightSession(
            session_id="sess-auditor",
            principal_id="auditor",
            state=SessionState.ACTIVE,
            established_at=NOW - timedelta(hours=9),
            expires_at=NOW - timedelta(minutes=1),
            csrf_token="csrf-auditor",
        )
    )
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert refusal(exc) == OversightRefusal.SESSION_EXPIRED.value


def test_session_belonging_to_another_principal_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.search(
            actor_ref="auditor",
            session_id="sess-attestor",
            query=EvidenceQuery(scope=OPS_UNIT),
            now=world.tick(),
        )
    assert refusal(exc) == OversightRefusal.SESSION_PRINCIPAL_MISMATCH.value


def test_mutating_act_requires_the_session_csrf_token(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.open_case(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="not-the-token",
            scope=OPS_UNIT,
            title="x",
            evidence_refs=world.references()[:1],
            idempotency_key="csrf-1",
            now=world.tick(),
        )
    assert refusal(exc) == OversightRefusal.CSRF_INVALID.value


def test_missing_csrf_token_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.open_case(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token=None,
            scope=OPS_UNIT,
            title="x",
            evidence_refs=world.references()[:1],
            idempotency_key="csrf-2",
            now=world.tick(),
        )
    assert refusal(exc) == OversightRefusal.CSRF_INVALID.value


def test_reads_do_not_require_a_csrf_token(world: World) -> None:
    assert world.search()["matched"] > 0


# -- the reviewer never becomes an operator ----------------------------------


def test_oversight_acts_change_no_ctrl04_state(world: World) -> None:
    """The decisive structural property: a principal who *also* holds
    `OPS.EXECUTE` can drive every CTRL-05 act, and the CTRL-04 plane is
    byte-for-byte unchanged afterwards."""
    ctrl04 = world.ctrl04
    before_journal = len(ctrl04.journal)
    before_head = ctrl04.journal.head_hash()
    before_states = {a.action_id: a.state for a in ctrl04.actions()}
    before_results = len(world.ctrl04._results)

    refs = world.references()
    case = world.open_case(principal="dual-hat-operator", evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED, principal="dual-hat-operator")
    world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0], principal="dual-hat-operator")
    world.service.clarify(
        actor_ref="dual-hat-operator",
        session_id="sess-dual-hat-operator",
        csrf_token="csrf-dual-hat-operator",
        case_id=case.case_id,
        text="noted",
        evidence_ref=None,
        idempotency_key="dual-clar",
        now=world.tick(),
    )
    world.service.link_remediation(
        actor_ref="dual-hat-operator",
        session_id="sess-dual-hat-operator",
        csrf_token="csrf-dual-hat-operator",
        case_id=case.case_id,
        remediation_plane="CTRL-04",
        remediation_ref=world.ctrl04_action_id,
        idempotency_key="dual-rem",
        now=world.tick(),
    )

    assert len(ctrl04.journal) == before_journal
    assert ctrl04.journal.head_hash() == before_head
    assert {a.action_id: a.state for a in ctrl04.actions()} == before_states
    assert len(world.ctrl04._results) == before_results


def test_remediation_link_is_a_reference_not_an_execution(world: World) -> None:
    case = world.open_case()
    link = world.service.link_remediation(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        remediation_plane="CTRL-04",
        remediation_ref=world.ctrl04_action_id,
        idempotency_key="rem-1",
        now=world.tick(),
    )
    assert link.executed_by_ctrl05 is False
    view = world.service.case_view(case.case_id)
    assert view["remediation_links"][0]["executed_by_ctrl05"] is False


def test_oversight_console_exposes_no_operational_method(world: World) -> None:
    """No method on the service or on any source adapter can act on a plane."""
    forbidden = (
        "request",
        "approve",
        "commit",
        "execute",
        "dispatch",
        "resolve",
        "cancel",
        "rollback",
        "restore",
        "restart",
        "rotate",
        "revoke_grant",
        "write",
        "delete",
        "update_evidence",
        "shell",
        "sql",
    )
    for holder in (
        world.service,
        world.ctrl02_source,
        world.ctrl03_source,
        world.ctrl04_source,
    ):
        for name in forbidden:
            assert not hasattr(holder, name), f"{type(holder).__name__}.{name} must not exist"


def test_ctrl04_actions_remain_drivable_only_through_ctrl04(world: World) -> None:
    """Sanity check that the CTRL-04 plane is alive and CTRL-05 simply is not
    the way to reach it: a new CTRL-04 action still works through CTRL-04."""
    action = world.ctrl04_world.request(ActionType.SERVICE_RESTART, "svc-api")
    assert action.action_id
    assert not hasattr(world.service, "request")

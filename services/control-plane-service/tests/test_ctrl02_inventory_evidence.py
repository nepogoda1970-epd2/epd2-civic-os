from __future__ import annotations

from datetime import timedelta

from _ctrl02_builders import BERLIN, NOW, activate, approve_twice, request, service
from epd2_control_plane_service.regional_operations import (
    CTRL01_WORKING_PREDECESSOR_SHA256,
    CTRL02_ACTIONS,
    DENIALS_RAISE,
    DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED,
    FREEZE_REJECTS_POST_VALIDATION_CHANGE,
    MUTATION_FIXTURES_REQUIRED,
    SELF_STATE,
    Decision,
    action_inventory,
)


def test_every_mutation_has_action_authority_reauth_and_evidence() -> None:
    mutations = [item for item in CTRL02_ACTIONS if item.mutation]
    assert mutations
    assert len({item.action_id for item in CTRL02_ACTIONS}) == len(CTRL02_ACTIONS)
    assert len({(item.method, item.route) for item in CTRL02_ACTIONS}) == len(CTRL02_ACTIONS)
    assert all(item.required_capability for item in mutations)
    assert all(item.commit_reauthorization for item in mutations)
    assert all(item.evidence_output for item in mutations)


def test_inventory_is_runtime_derived() -> None:
    exported = action_inventory()
    assert len(exported) == len(CTRL02_ACTIONS)
    assert {item["action_id"] for item in exported} == {item.action_id for item in CTRL02_ACTIONS}


def test_meta_invariants_are_fail_closed() -> None:
    assert DIRECT_DB_MUTATION_COUNTS_AS_GOVERNED is False
    assert DENIALS_RAISE is True
    assert SELF_STATE == "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
    assert CTRL01_WORKING_PREDECESSOR_SHA256 == (
        "490d8ca31d4607da204f03addaf900161257b289d51ec6f0b7e52433fd5cbe71"
    )
    assert MUTATION_FIXTURES_REQUIRED == 40
    assert FREEZE_REJECTS_POST_VALIDATION_CHANGE is True


def test_dependency_unavailable_decision_is_not_allow() -> None:
    svc = service()
    svc.authorities.available = False
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id=None,
            capability="MEMBER.READ",
            scope=BERLIN,
            now=NOW,
        )
        is Decision.DEPENDENCY_UNAVAILABLE
    )


def test_server_clock_does_not_roll_back() -> None:
    svc = service()
    future = NOW + timedelta(hours=4)
    svc.effective_decision(
        session_id=None,
        authority_id=None,
        capability="MEMBER.READ",
        scope=BERLIN,
        now=future,
    )
    svc.effective_decision(
        session_id=None,
        authority_id=None,
        capability="MEMBER.READ",
        scope=BERLIN,
        now=NOW,
    )
    assert svc.checkpoint()["last_time"] == future.isoformat()


def test_audit_chain_is_append_only_and_linked() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    activate(svc)
    events = svc.events
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert events[0].previous_hash == "GENESIS"
    assert all(
        events[index].previous_hash == events[index - 1].event_hash
        for index in range(1, len(events))
    )
    assert len({event.event_hash for event in events}) == len(events)


def test_unrelated_capability_and_region_remain_available() -> None:
    svc = service()
    request(svc)
    approve_twice(svc)
    activate(svc)
    assert (
        svc.effective_decision(
            session_id=None,
            authority_id=None,
            capability="MEETING.READ",
            scope=BERLIN,
            now=NOW + timedelta(minutes=4),
        )
        is Decision.ALLOW
    )


def test_read_models_separate_active_pending_and_review() -> None:
    svc = service()
    request(svc)
    assert len(svc.pending_requests()) == 1
    assert not svc.active_interventions()
    approve_twice(svc)
    activate(svc)
    assert len(svc.active_interventions()) == 1
    assert not svc.pending_requests()
    svc.revoke(
        "request-1",
        actor_id="revoker",
        now=NOW + timedelta(minutes=5),
        idempotency_key="revoke:read-model",
    )
    assert len(svc.pending_reviews()) == 1

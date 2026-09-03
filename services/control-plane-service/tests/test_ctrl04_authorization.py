"""CTRL-04 authorization, separation of duties, commit-time reauthorization
and boundary tests (universal admin, hierarchy, voting, secrets, read/execute)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from _ctrl04_builders import ARTIFACT_B, BAVARIA, BERLIN, BUND, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import BackendState
from epd2_control_plane_service.operations_console import (
    ARBITRARY_SQL_SURFACE_EXISTS,
    BROWSER_STATE_IS_AUTHORITATIVE,
    CTRL01_ACCEPTED_SHA256,
    CTRL02_ACCEPTED_SHA256,
    CTRL03_ACCEPTED_SHA256,
    DIRECT_SHELL_SURFACE_EXISTS,
    DISPATCH_ACK_IS_SUCCESS,
    GATES_REQUIRED,
    MUTATION_FIXTURES_REQUIRED,
    SELF_STATE,
    UNIVERSAL_ADMIN_EXISTS,
    ActionState,
    ActionType,
    ApprovalState,
    EnvironmentClass,
    OperationalTarget,
    OperationsPolicy,
    OpsRefusal,
    TargetClass,
    TargetDomain,
)
from epd2_control_plane_service.regional_operations import ApproverClass


def refused(fn, code: OpsRefusal | str):  # type: ignore[no-untyped-def]
    with pytest.raises(AuthorizationRefused) as info:
        fn()
    expected = code.value if isinstance(code, OpsRefusal) else code
    assert str(info.value.reason_code) == expected, (info.value.reason_code, str(info.value))
    return info.value


# -- request-time authorization ----------------------------------------------


def test_request_requires_request_right_in_exact_scope() -> None:
    w = World()
    # Reader holds OPS.READ only: the projection cannot even be issued for OPS.REQUEST.
    with pytest.raises(AuthorizationRefused):
        w.projection("reader", "OPS.REQUEST")
    # A forged projection claiming OPS.REQUEST for the reader is refused as untrusted.
    forged = replace(w.projection("reader", "OPS.READ"), capability="OPS.REQUEST")
    refused(
        lambda: w.service.request(
            actor_ref="reader",
            session_id="sess-reader",
            projection=forged,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="forged",
            purpose="x",
            now=w.tick(),
        ),
        OpsRefusal.PROJECTION_UNTRUSTED,
    )
    # Correctly signed but a different act than presented.
    mismatched = w.projection("reader", "OPS.READ")
    refused(
        lambda: w.service.request(
            actor_ref="reader",
            session_id="sess-reader",
            projection=mismatched,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="mismatch",
            purpose="x",
            now=w.tick(),
        ),
        OpsRefusal.PROJECTION_MISMATCH,
    )
    assert all(r.result == "REFUSED" for r in w.service.journal.records())


def test_wrong_region_scope_refused_and_hierarchy_grants_nothing() -> None:
    w = World()
    refused(
        lambda: w.request(principal="bavaria-requester", scope=BAVARIA),
        OpsRefusal.WRONG_SCOPE,
    )
    # A "Bund" scope is not above Berlin; it is simply a different exact scope.
    refused(lambda: w.request(principal="bund-admin", scope=BUND), OpsRefusal.WRONG_SCOPE)
    assert not w.service.actions()


def test_projection_freshness_and_stale_projection() -> None:
    w = World()
    projection = w.projection("requester", "OPS.REQUEST")
    w.now = w.now + timedelta(minutes=6)
    refused(
        lambda: w.service.request(
            actor_ref="requester",
            session_id="sess-requester",
            projection=projection,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="old",
            purpose="x",
            now=w.tick(),
        ),
        OpsRefusal.PROJECTION_EXPIRED,
    )
    fresh = w.projection("requester", "OPS.REQUEST")
    w.authorities.update("g-req-r")  # version bump: projection is now stale
    refused(
        lambda: w.service.request(
            actor_ref="requester",
            session_id="sess-requester",
            projection=fresh,
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="stale",
            purpose="x",
            now=w.tick(),
        ),
        OpsRefusal.STALE_AUTHORITY,
    )


def test_revoked_and_expired_sessions_are_refused() -> None:
    w = World()
    w.service.revoke_session("sess-requester")
    refused(lambda: w.request(), OpsRefusal.SESSION_REVOKED)
    w2 = World()
    w2.now = w2.now + timedelta(hours=9)
    refused(lambda: w2.request(), OpsRefusal.SESSION_EXPIRED)
    w3 = World()
    refused(
        lambda: w3.service.request(
            actor_ref="requester",
            session_id="sess-executor",
            projection=w3.projection("requester", "OPS.REQUEST"),
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="x",
            purpose="x",
            now=w3.tick(),
        ),
        OpsRefusal.SESSION_PRINCIPAL_MISMATCH,
    )


def test_read_only_session_cannot_mutate_even_with_rights() -> None:
    w = World()
    # readonly-operator holds OPS.REQUEST and OPS.EXECUTE grants, but the session is read-only.
    refused(lambda: w.request(principal="readonly-operator"), OpsRefusal.READ_ONLY_SESSION)
    action = w.request()
    w.approve(action.action_id)
    refused(
        lambda: w.commit(action.action_id, principal="readonly-operator"),
        OpsRefusal.READ_ONLY_SESSION,
    )
    # Visibility still works for the read-only operator.
    target, grant = w.service.authorize_read(
        actor_ref="readonly-operator",
        session_id="sess-readonly-operator",
        projection=w.projection("readonly-operator", "OPS.READ"),
        action_type=ActionType.HEALTH_READ,
        target_id="svc-web",
        now=w.tick(),
    )
    assert target.target_id == "svc-web" and grant.capability == "OPS.READ"


def test_universal_admin_is_refused_everything() -> None:
    assert UNIVERSAL_ADMIN_EXISTS is False
    w = World()
    refused(lambda: w.request(principal="root"), OpsRefusal.UNIVERSAL_ADMIN)
    refused(
        lambda: w.service.authorize_read(
            actor_ref="root",
            session_id="sess-root",
            projection=w.projection("root", "OPS.REQUEST"),
            action_type=ActionType.HEALTH_READ,
            target_id="svc-web",
            now=w.tick(),
        ),
        OpsRefusal.UNIVERSAL_ADMIN,
    )


# -- approval and separation of duties ---------------------------------------


def test_self_approval_refused() -> None:
    w = World()
    action = w.request(principal="dual-hat")
    refused(lambda: w.approve(action.action_id, "dual-hat"), OpsRefusal.SELF_APPROVAL)
    assert w.service.action(action.action_id).state is ActionState.AWAITING_APPROVAL


def test_approver_may_not_execute() -> None:
    w = World()
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    w.authorities.add(
        AuthorityGrant(
            "g-ic-exec", "incident-commander", ActorClass.HUMAN, "OPS.EXECUTE", BERLIN, 1
        )
    )
    action = w.request()
    w.approve(action.action_id)
    refused(
        lambda: w.commit(action.action_id, principal="incident-commander"),
        OpsRefusal.APPROVER_EXECUTES,
    )
    assert w.adapter.dispatch_count == 0
    w.commit(action.action_id)
    assert w.adapter.dispatch_count == 1


def test_participants_may_not_review() -> None:
    w = World()
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    for who in ("requester", "executor", "incident-commander"):
        w.authorities.add(
            AuthorityGrant(f"g-{who}-rev", who, ActorClass.HUMAN, "OPS.REVIEW", BERLIN, 1)
        )
    done = w.full_restart()
    for who in ("requester", "executor", "incident-commander"):
        refused(lambda who=who: w.review(done.action_id, who), OpsRefusal.EXECUTOR_REVIEWS)
    assert w.review(done.action_id).reviewed_by == "reviewer"


def test_approval_class_and_duplicate_approval_rules() -> None:
    w = World()
    action = w.request()
    refused(
        lambda: w.approve(action.action_id, "security-officer", ApproverClass.SECURITY),
        OpsRefusal.APPROVER_CLASS_MISSING,
    )
    w.approve(action.action_id)
    refused(lambda: w.approve(action.action_id), OpsRefusal.APPROVAL_NOT_REQUIRED)


def test_high_impact_dual_control_requires_distinct_classes() -> None:
    w = World()
    action = w.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "bad", "target_artifact_digest": ARTIFACT_B},
    )
    w.approve(action.action_id)
    refused(lambda: w.commit(action.action_id), OpsRefusal.QUORUM_NOT_MET)
    refused(lambda: w.approve(action.action_id), OpsRefusal.DUPLICATE_APPROVAL)
    w.approve(action.action_id, "security-officer", ApproverClass.SECURITY)
    assert w.service.action(action.action_id).approval_state is ApprovalState.GRANTED
    assert len(w.service.approvals_of(action.action_id)) == 2


def test_approval_quorum_enforced_via_policy_switch() -> None:
    weak = World(policy=OperationsPolicy.governed().without("enforce_quorum"))
    action = weak.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "bad", "target_artifact_digest": ARTIFACT_B},
    )
    weak.approve(action.action_id)
    # With the obligation removed one approval completes the quorum: the governed
    # suite must therefore see the switch as a real enforcement.
    assert weak.service.action(action.action_id).state is ActionState.APPROVED
    strict = World()
    action = strict.request(
        ActionType.DEPLOYMENT_ROLLBACK,
        parameters={"reason": "bad", "target_artifact_digest": ARTIFACT_B},
    )
    strict.approve(action.action_id)
    assert strict.service.action(action.action_id).state is ActionState.AWAITING_APPROVAL


# -- commit-time reauthorization ---------------------------------------------


def test_stale_requester_authority_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.authorities.update("g-req-r", revoked=True)
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_AUTHORITY)
    assert w.adapter.dispatch_count == 0
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    w2.authorities.update("g-req-r")  # version change only
    refused(lambda: w2.commit(action.action_id), OpsRefusal.STALE_AUTHORITY)


def test_stale_approval_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.now = w.now + timedelta(minutes=31)
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_APPROVAL)
    assert w.service.approvals_of(action.action_id)[0].state is ApprovalState.EXPIRED
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    w2.authorities.update("g-ic", suspended=True)
    refused(lambda: w2.commit(action.action_id), OpsRefusal.STALE_APPROVAL)


def test_changed_target_version_refused_at_commit_and_approval() -> None:
    w = World()
    action = w.request()
    w.service.bump_target_version("svc-web")
    refused(lambda: w.approve(action.action_id), OpsRefusal.STALE_TARGET)
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    w2.service.bump_target_version("svc-web")
    refused(lambda: w2.commit(action.action_id), OpsRefusal.STALE_TARGET)


def test_changed_deployment_identity_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    target = w.service.target("svc-web")
    # Same version, different deployment identity (simulates an out-of-band redeploy
    # whose version bookkeeping was lost): identity is checked independently.
    w.service.register_target(replace(target, deployment_identity_ref="dep-web-0"))
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_DEPLOYMENT_IDENTITY)


def test_changed_environment_and_scope_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    target = w.service.target("svc-web")
    w.service.register_target(replace(target, environment=EnvironmentClass.NON_PRODUCTION))
    refused(lambda: w.commit(action.action_id), OpsRefusal.ENVIRONMENT_MISMATCH)
    # The executor legitimately holds EXECUTE in Bavaria too, so the projection
    # itself is valid for the re-scoped target; the commit-time check must still
    # notice that the scope differs from the one the request was authorized in.
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    w.authorities.add(
        AuthorityGrant("g-exec-by", "executor", ActorClass.HUMAN, "OPS.EXECUTE", BAVARIA, 1)
    )
    w.service.register_target(replace(target, scope=BAVARIA))
    refused(lambda: w.commit(action.action_id, scope=BAVARIA), OpsRefusal.WRONG_SCOPE)
    assert w.adapter.dispatch_count == 0


def test_tampered_parameters_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    stored = w.service.action(action.action_id)
    w.service._actions[action.action_id] = replace(stored, parameters={"reason": "tampered"})
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_PARAMETERS)


def test_revoked_requester_session_refused_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.service.revoke_session("sess-requester")
    refused(lambda: w.commit(action.action_id), OpsRefusal.SESSION_REVOKED)


def test_executor_session_and_authority_checked_at_commit() -> None:
    w = World()
    action = w.request()
    w.approve(action.action_id)
    w.service.revoke_session("sess-executor")
    refused(lambda: w.commit(action.action_id), OpsRefusal.SESSION_REVOKED)
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    projection = w2.projection("executor", "OPS.EXECUTE")
    w2.authorities.update("g-exec", revoked=True)
    refused(
        lambda: w2.service.commit(
            action_id=action.action_id,
            executor_ref="executor",
            session_id="sess-executor",
            projection=projection,
            now=w2.tick(),
        ),
        "OPS_AUTHORITY_REVOKED",
    )


def test_ctrl02_restriction_and_revision_are_honoured() -> None:
    w = World()
    w.ctrl02.restricted_targets.add("svc-web")
    refused(lambda: w.request(), OpsRefusal.CTRL02_RESTRICTED)
    w.ctrl02.restricted_targets.clear()
    action = w.request()
    w.approve(action.action_id)
    w.ctrl02.revision += 1
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_CTRL02)
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    w2.ctrl02.quarantined_sessions.add("sess-requester")
    w2.ctrl02.revision += 1
    refused(lambda: w2.commit(action.action_id), OpsRefusal.STALE_CTRL02)
    w3 = World()
    w3.ctrl02.available = False
    refused(lambda: w3.request(), OpsRefusal.ADAPTER_UNAVAILABLE)


# -- boundaries -----------------------------------------------------------------


def test_voting_domain_targets_are_unreachable_from_general_console() -> None:
    w = World()
    assert "svc-voting-tally" not in {t.target_id for t in w.service.targets()}
    refused(lambda: w.request(target_id="svc-voting-tally"), OpsRefusal.VOTING_BOUNDARY)
    refused(lambda: w.service.health("svc-voting-tally", now=w.now), OpsRefusal.VOTING_BOUNDARY)
    refused(
        lambda: w.service.authorize_read(
            actor_ref="reader",
            session_id="sess-reader",
            projection=w.projection("reader", "OPS.READ"),
            action_type=ActionType.STATUS_READ,
            target_id="svc-voting-tally",
            now=w.tick(),
        ),
        OpsRefusal.VOTING_BOUNDARY,
    )
    # Even an already-approved action is refused if the target is re-classified.
    action = w.request()
    w.approve(action.action_id)
    target = w.service.target("svc-web")
    w.service.register_target(replace(target, domain=TargetDomain.VOTING))
    refused(lambda: w.commit(action.action_id), OpsRefusal.VOTING_BOUNDARY)


def test_secret_bearing_metadata_is_redacted_everywhere() -> None:
    w = World()
    health = w.service.health("svc-web", now=w.now)
    assert health.details["api_token"] == "[REDACTED]"
    assert health.details["secret_ref"] == "vault://ops/web"
    assert "api_token" in health.redacted_fields
    degraded = w.service.health("int-payment", now=w.now)
    assert degraded.state.value == "DEGRADED"
    assert degraded.details["provider_password"] == "[REDACTED]"
    done = w.full_restart()
    result = w.service.result_of(done.action_id)
    assert result is not None and result.backend_metadata["api_token"] == "[REDACTED]"
    dump = (
        str(w.service.checkpoint())
        + str(w.service.read_model(now=w.now))
        + str(w.service.evidence_record(done.action_id))
    )
    assert "sk_live_" not in dump and "hunter2" not in dump
    for record in w.service.journal.records():
        assert "sk_live_" not in str(record.attributes)


def test_secret_value_in_journal_attribute_is_refused_not_stored() -> None:
    weak = World(policy=OperationsPolicy.governed().without("enforce_secret_redaction"))
    from epd2_control_plane_service.exceptions import PrivacyBoundaryViolation

    with pytest.raises(PrivacyBoundaryViolation):
        weak.full_restart()


def test_unavailable_and_degraded_states_are_typed() -> None:
    w = World()
    assert w.service.health("svc-legacy", now=w.now).state.value == "UNAVAILABLE"
    w.adapter.available = False
    assert w.service.health("svc-web", now=w.now).state.value == "UNAVAILABLE"
    assert w.service.job_queue("queue-mail", now=w.now).state == "UNAVAILABLE"


def test_declared_constants_and_predecessor_identities() -> None:
    assert SELF_STATE == "CANDIDATE_NOT_ACCEPTED"
    assert DIRECT_SHELL_SURFACE_EXISTS is False
    assert ARBITRARY_SQL_SURFACE_EXISTS is False
    assert BROWSER_STATE_IS_AUTHORITATIVE is False
    assert DISPATCH_ACK_IS_SUCCESS is False
    assert MUTATION_FIXTURES_REQUIRED == 48
    assert GATES_REQUIRED == 52
    assert (
        CTRL01_ACCEPTED_SHA256 == "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5"
    )
    assert (
        CTRL02_ACCEPTED_SHA256 == "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e"
    )
    assert (
        CTRL03_ACCEPTED_SHA256 == "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff"
    )
    assert OperationsPolicy.governed().is_governed()
    assert OperationsPolicy.governed().without("enforce_quorum").disabled_obligations() == (
        "enforce_quorum",
    )


def test_target_records_reject_coarse_identifiers() -> None:
    with pytest.raises(ValueError):
        OperationalTarget(
            target_id="ALL",
            target_class=TargetClass.SERVICE,
            domain=TargetDomain.GENERAL,
            environment=EnvironmentClass.PRODUCTION_LIKE,
            scope=BERLIN,
            deployment_identity_ref="dep",
            adapter_id="x",
            version=1,
        )


def test_wrong_target_restart_is_impossible_dispatch_carries_exact_target() -> None:
    w = World()
    w.adapter.inject_outcome("svc-api", BackendState.COMPLETED)
    action = w.request(target_id="svc-api")
    w.approve(action.action_id)
    w.commit(action.action_id)
    sent = w.adapter.dispatch_log[-1]
    assert sent.target_id == "svc-api"
    assert sent.deployment_identity_ref == "dep-web-1"
    assert sent.action_type == ActionType.SERVICE_RESTART.value
    assert sent.parameters_digest == action.parameters_digest

"""CTRL-04 hardening tests added after the adversarial review.

Each test here reproduces a defect the review found in the first candidate
and proves the corrected behaviour. They are kept separate so a reviewer can
see what was weak, not only that it is now strong.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from _ctrl04_builders import BERLIN, World
from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import (
    BackendState,
    DispatchAck,
    JsonFileStore,
    LocalFilesystemBackupAdapter,
    ReferenceOperationsAdapter,
    redact_metadata,
    scrub_text,
)
from epd2_control_plane_service.operations_api import ConsoleApp
from epd2_control_plane_service.operations_console import (
    ActionState,
    ActionType,
    EvidenceSealer,
    ExecutionState,
    FailureClassification,
    OperationsConsoleService,
    OpsRefusal,
)
from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant


def refused(fn, code: OpsRefusal | str):  # type: ignore[no-untyped-def]
    with pytest.raises(AuthorizationRefused) as info:
        fn()
    expected = code.value if isinstance(code, OpsRefusal) else code
    assert str(info.value.reason_code) == expected, (info.value.reason_code, str(info.value))
    return info.value


class Client:
    def __init__(self, world: World) -> None:
        self.world = world
        self.app = ConsoleApp(world.service, clock=lambda: world.tick())

    def call(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        session: str | None = "sess-requester",
    ) -> tuple[int, Any]:
        headers = {} if session is None else {"X-EPD2-Session": session}
        status, payload, _ = self.app.handle(
            method, path, headers, json.dumps(body).encode() if body is not None else b""
        )
        return status, payload


# -- finding 1: revoked/expired sessions on every route ----------------------


def test_revoked_session_is_refused_on_every_http_route() -> None:
    w = World()
    c = Client(w)
    done = w.full_restart()
    w.service.revoke_session("sess-reader")
    for path in (
        "/ops/v1/me",
        "/ops/v1/targets",
        "/ops/v1/actions",
        f"/ops/v1/actions/{done.action_id}",
        "/ops/v1/read-model",
        "/ops/v1/backups",
        "/ops/v1/maintenance",
        "/ops/v1/incidents",
        "/ops/v1/status?target_id=svc-web",
        f"/ops/v1/evidence/{done.action_id}",
    ):
        status, payload = c.call("GET", path, session="sess-reader")
        assert status == 401 and payload["error"] == OpsRefusal.SESSION_REVOKED.value, path
    status, payload = c.call("POST", f"/ops/v1/actions/{done.action_id}/resolve", {}, "sess-reader")
    assert status == 401 and payload["error"] == OpsRefusal.SESSION_REVOKED.value
    w.now = w.now + timedelta(hours=9)
    status, payload = c.call("GET", "/ops/v1/targets", session="sess-executor")
    assert status == 401 and payload["error"] == OpsRefusal.SESSION_EXPIRED.value


# -- finding 2: checkpoint bound to the journal and keyed seal -----------------


def _revive(
    store: JsonFileStore, w: World, payload: dict[str, Any], sealer: EvidenceSealer | None
) -> Any:
    return OperationsConsoleService.from_checkpoint(
        payload,
        authorities=w.authorities,
        signer=w.signer,
        adapters={"reference-adapter": w.adapter},
        ctrl02=w.ctrl02,
        ctrl03=w.ctrl03,
        store=store,
        sealer=sealer,
    )


def test_rewritten_chain_with_recomputed_anchor_is_refused_by_seal(tmp_path: Path) -> None:
    sealer = EvidenceSealer(secrets.token_bytes(32))
    store = JsonFileStore(tmp_path / "s.json")
    w = World(store=store)
    w.service.sealer = sealer
    w.adapter.inject_outcome("svc-web", BackendState.FAILED)
    failed = w.full_restart()
    assert failed.state is ActionState.FAILED
    payload = store.load()
    assert payload is not None
    # Attacker rewrites history to SUCCEEDED and recomputes the whole chain and anchor.
    forged = EvidenceJournal()
    for record in payload["journal"]:
        if record["correlation_ref"] == failed.action_id and record["result"] == "FAILED":
            record = {**record, "result": "SUCCEEDED", "reason_code": "OPS_RESULT_SUCCEEDED"}
        forged.append(
            occurred_at=__import__("datetime").datetime.fromisoformat(record["occurred_at"]),
            actor_ref=record["actor_ref"],
            actor_class=record["actor_class"],
            authority_basis=record["authority_basis"],
            action_id=record["action_id"],
            scope_key=record["scope_key"],
            object_ref=record["object_ref"],
            result=record["result"],
            reason_code=record["reason_code"],
            approval_refs=tuple(record["approval_refs"]),
            correlation_ref=record["correlation_ref"],
            attributes=record["attributes"],
        )
    payload["journal"] = forged.export()
    payload["journal_anchor"] = list(forged.anchor())
    with pytest.raises(AuthorizationRefused) as info:
        _revive(store, w, payload, sealer)
    assert info.value.reason_code == OpsRefusal.EVIDENCE_IMMUTABLE.value
    # A checkpoint carrying a seal cannot be loaded without the key either.
    with pytest.raises(AuthorizationRefused):
        _revive(store, w, store.load() or {}, None)
    # The untouched checkpoint loads with the key.
    revived = _revive(store, w, store.load() or {}, sealer)
    assert revived.action(failed.action_id).state is ActionState.FAILED


def test_action_tables_must_agree_with_journal_on_load(tmp_path: Path) -> None:
    store = JsonFileStore(tmp_path / "s.json")
    w = World(store=store)
    w.adapter.inject_outcome("svc-web", BackendState.FAILED)
    failed = w.full_restart()
    payload = store.load()
    assert payload is not None
    payload["actions"][failed.action_id]["state"] = "SUCCEEDED"
    payload["actions"][failed.action_id]["result_state"] = "SUCCEEDED"
    with pytest.raises(AuthorizationRefused) as info:
        _revive(store, w, payload, None)
    assert info.value.reason_code == OpsRefusal.EVIDENCE_IMMUTABLE.value
    payload = store.load()
    assert payload is not None
    payload["actions"][failed.action_id]["actor_ref"] = "ghost"
    with pytest.raises(AuthorizationRefused):
        _revive(store, w, payload, None)
    payload = store.load()
    assert payload is not None
    result_id = payload["actions"][failed.action_id]["result_id"]
    payload["results"][result_id]["failure_classification"] = "NONE"
    with pytest.raises(AuthorizationRefused):
        _revive(store, w, payload, None)


# -- finding 3: secrets in detail strings, ids and purpose -----------------------


def test_backend_detail_and_secret_named_ids_are_scrubbed() -> None:
    assert scrub_text("auth failed for password=hunter2 token sk_live_abc") == (
        "auth failed for password=[REDACTED] token [REDACTED]"
    )
    clean, redacted = redact_metadata(
        {
            "secret_id": "vault-approle",
            "token_id": "glpat-x",
            "client_secret_version": "v1",
            "secret_ref": "vault://x",
        }
    )
    assert clean["secret_id"] == "[REDACTED]" and clean["token_id"] == "[REDACTED]"
    assert clean["client_secret_version"] == "[REDACTED]" and clean["secret_ref"] == "vault://x"
    assert set(redacted) == {"secret_id", "token_id", "client_secret_version"}
    w = World()
    w.adapter.refuse_dispatch.add("svc-web")

    original = w.adapter.dispatch

    def leaky(request: Any) -> DispatchAck:
        original(request)
        return DispatchAck(False, None, "backend refused: password=hunter2 token=sk_live_zzz")

    w.adapter.dispatch = leaky  # type: ignore[method-assign]
    done = w.full_restart()
    result = w.service.result_of(done.action_id)
    assert result is not None and "hunter2" not in result.detail and "sk_live_" not in result.detail
    dump = json.dumps([r.hashable() for r in w.service.journal.records()])
    assert "hunter2" not in dump and "sk_live_" not in dump


def test_secret_in_purpose_is_scrubbed_not_a_denial_of_service() -> None:
    w = World()
    w.tick()
    action = w.service.request(
        actor_ref="requester",
        session_id="sess-requester",
        projection=w.projection("requester", "OPS.REQUEST"),
        action_type=ActionType.SERVICE_RESTART,
        target_id="svc-web",
        parameters={"reason": "x"},
        idempotency_key="purpose",
        purpose="please use sk_live_secret123 for this",
        now=w.now,
    )
    model = w.service.read_model(now=w.now)
    assert "sk_live_" not in json.dumps(model)
    view = w.service.action_view(action.action_id)
    assert "sk_live_" not in view["purpose"]


def test_opaque_token_value_never_reaches_journal() -> None:
    w = World()
    w.adapter.configure_target(
        "svc-api",
        capabilities=w.adapter.capabilities("svc-api"),
        metadata={"provider_api_token": "opaque-value-without-known-prefix"},
    )
    done = w.full_restart("svc-api")
    for record in w.service.journal.records():
        assert "opaque-value-without-known-prefix" not in json.dumps(record.hashable())
    result = w.service.result_of(done.action_id)
    assert result is not None and result.backend_metadata["provider_api_token"] == "[REDACTED]"


# -- finding 4: CTRL-02 state for approvers and executors ----------------------


def test_ctrl02_quarantine_applies_to_approver_and_executor_sessions() -> None:
    w = World()
    w.ctrl02.quarantined_sessions.add("sess-incident-commander")
    action = w.request()
    refused(lambda: w.approve(action.action_id), OpsRefusal.CTRL02_RESTRICTED)
    w2 = World()
    action = w2.request()
    w2.approve(action.action_id)
    w2.ctrl02.quarantined_sessions.add("sess-executor")
    w2.ctrl02.revision += 1
    # Revision drift is caught first for the requester binding; keep it stable
    # and test the executor's own session check in isolation.
    w3 = World()
    action = w3.request()
    w3.approve(action.action_id)
    w3.ctrl02.quarantined_sessions.add("sess-executor")
    refused(lambda: w3.commit(action.action_id), OpsRefusal.CTRL02_RESTRICTED)
    assert w3.adapter.dispatch_count == 0
    w4 = World()
    action = w4.request()
    w4.approve(action.action_id)
    w4.ctrl02.quarantined_sessions.add("sess-incident-commander")
    refused(lambda: w4.commit(action.action_id), OpsRefusal.STALE_APPROVAL)
    w5 = World()
    action = w5.request()
    w5.ctrl02.restricted_targets.add("svc-web")
    refused(lambda: w5.approve(action.action_id), OpsRefusal.CTRL02_RESTRICTED)


# -- finding 5: path traversal through governed identifiers ---------------------


def test_backup_set_id_cannot_escape_the_backup_root(tmp_path: Path) -> None:
    w = World()
    for bad in ("../escape", "/abs/path", "a/b", "..", "x y"):
        refused(
            lambda bad=bad: w.request(
                ActionType.BACKUP_REQUEST,
                "db-members",
                parameters={"reason": "x", "backup_set_id": bad},
            ),
            OpsRefusal.PARAMETER_INVALID,
        )
    adapter = LocalFilesystemBackupAdapter(tmp_path / "root")
    for bad in ("../escape", "a/b", ""):
        with pytest.raises(ValueError):
            adapter.backup_path(bad, "0" * 64)
    with pytest.raises(ValueError):
        adapter.backup_path("ok", "../x")
    refused(
        lambda: w.request(
            ActionType.DEPLOYMENT_ROLLBACK,
            parameters={"reason": "x", "target_artifact_digest": "../x"},
        ),
        OpsRefusal.PARAMETER_INVALID,
    )
    refused(
        lambda: w.request(
            ActionType.MAINTENANCE_EXIT, "svc-web", parameters={"reason": "x", "window_id": "../MW"}
        ),
        OpsRefusal.PARAMETER_INVALID,
    )


# -- finding 6: lost dispatch acknowledgement ------------------------------------


def test_dispatch_exception_is_terminal_failure_with_evidence_and_no_retry() -> None:
    w = World()

    def explode(request: Any) -> DispatchAck:
        raise ConnectionError("ack lost on the wire")

    w.adapter.dispatch = explode  # type: ignore[method-assign]
    action = w.request()
    w.approve(action.action_id)
    done = w.commit(action.action_id)
    assert done.state is ActionState.FAILED
    result = w.service.result_of(action.action_id)
    assert result is not None
    assert result.failure_classification is FailureClassification.ADAPTER_UNAVAILABLE
    assert "ack lost" not in result.detail and "ConnectionError" in result.detail
    assert w.service.journal.records()[-1].result == "FAILED"
    w.adapter.dispatch = ReferenceOperationsAdapter.dispatch.__get__(w.adapter)  # type: ignore[method-assign]
    refused(lambda: w.commit(action.action_id), OpsRefusal.DUPLICATE_EXECUTION)
    assert w.adapter.dispatch_count == 0
    assert action.target_id not in w.service._executing_targets


# -- finding 7: malformed requests are governed refusals -----------------------------


def test_malformed_requests_are_refused_with_evidence_not_crashes() -> None:
    w = World()
    before = len(w.service.journal)
    refused(
        lambda: w.request(
            ActionType.MAINTENANCE_ENTER, parameters={"reason": "x", "duration_minutes": "abc"}
        ),
        OpsRefusal.PARAMETER_INVALID,
    )
    refused(lambda: w.request(idempotency_key="has space"), OpsRefusal.PARAMETER_INVALID)
    w.tick()
    refused(
        lambda: w.service.request(
            actor_ref="requester",
            session_id="sess-requester",
            projection=w.projection("requester", "OPS.REQUEST"),
            action_type=ActionType.SERVICE_RESTART,
            target_id="svc-web",
            parameters={"reason": "x"},
            idempotency_key="k",
            purpose="x",
            now=w.now,
            incident_ref=["x"],  # type: ignore[arg-type]
        ),
        OpsRefusal.PARAMETER_INVALID,
    )
    assert len(w.service.journal) == before + 3
    assert all(r.result == "REFUSED" for r in w.service.journal.records()[-3:])
    c = Client(w)
    assert c.call("POST", "/ops/v1/actions/OPA-000001")[0] == 404
    assert c.call("POST", "/ops/v1/actions/OPA-000001/")[0] == 404


def test_api_internal_errors_are_refused_without_traceback() -> None:
    w = World()
    c = Client(w)

    def boom(**kwargs: Any) -> Any:
        raise RuntimeError("unexpected")

    w.service.request = boom  # type: ignore[method-assign]
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "x"},
            "idempotency_key": "k",
        },
    )
    assert status == 500 and payload == {"error": "OPS_INTERNAL_REFUSAL", "detail": "RuntimeError"}


# -- finding 8: read-only sessions cannot review or cancel ----------------------------


def test_read_only_session_cannot_review_or_cancel() -> None:
    w = World()
    w.authorities.add(
        AuthorityGrant("g-ro-rev", "readonly-operator", ActorClass.HUMAN, "OPS.REVIEW", BERLIN, 1)
    )
    done = w.full_restart()
    refused(lambda: w.review(done.action_id, "readonly-operator"), OpsRefusal.READ_ONLY_SESSION)
    pending = w.request(principal="requester-2", idempotency_key="ro-cancel")
    w.service._sessions["sess-requester-2"] = replace(
        w.service.session("sess-requester-2"),
        read_only=True,  # type: ignore[arg-type]
    )
    w.tick()
    refused(
        lambda: w.service.cancel(
            action_id=pending.action_id,
            actor_ref="requester-2",
            session_id="sess-requester-2",
            now=w.now,
        ),
        OpsRefusal.READ_ONLY_SESSION,
    )


# -- finding 9: read model scoped ---------------------------------------------------------


def test_read_model_is_scope_filtered_for_all_collections() -> None:
    w = World()
    w.completed_backup()
    w.active_window("svc-web")
    c = Client(w)
    status, model = c.call("GET", "/ops/v1/read-model", session="sess-bavaria-requester")
    assert status == 200
    assert model["targets"] == [] and model["actions"] == []
    assert model["maintenance_windows"] == [] and model["backup_operations"] == []
    assert model["incidents"] == []
    status, model = c.call("GET", "/ops/v1/read-model", session="sess-reader")
    assert model["maintenance_windows"] and model["backup_operations"] and model["incidents"]


# -- finding 12: timeout keeps the target guarded until a late outcome -----------------


def test_timeout_keeps_target_guarded_until_late_outcome_is_observed() -> None:
    w = World()
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=1)
    first = w.request(idempotency_key="t1")
    w.approve(first.action_id)
    w.commit(first.action_id)
    w.now = w.now + timedelta(minutes=31)
    timed_out = w.resolve(first.action_id)
    assert timed_out.execution_state is ExecutionState.TIMED_OUT
    second = w.request(idempotency_key="t2", principal="requester-2")
    w.approve(second.action_id)
    refused(lambda: w.commit(second.action_id), OpsRefusal.CONFLICTING_EXECUTION)
    # The backend eventually reports; observing it releases the guard and is journaled.
    w.resolve(first.action_id)
    assert w.service.journal.records()[-1].result == "LATE_BACKEND_OUTCOME"
    assert w.service.action(first.action_id).state is ActionState.FAILED
    assert w.commit(second.action_id).state is ActionState.EXECUTING


def test_refused_action_evidence_is_reachable_over_http() -> None:
    w = World()
    c = Client(w)
    status, _payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "x"},
            "idempotency_key": "k",
        },
        session="sess-readonly-operator",
    )
    assert status == 403
    action_id = w.service.journal.records()[-1].correlation_ref
    status, record = c.call("GET", f"/ops/v1/evidence/{action_id}", session="sess-reader")
    assert status == 200 and record["result_state"] == "REFUSED"
    status, record = c.call(
        "GET", f"/ops/v1/evidence/{action_id}", session="sess-bavaria-requester"
    )
    assert status == 403


def test_refused_attempt_on_existing_action_survives_restart(tmp_path: Path) -> None:
    store = JsonFileStore(tmp_path / "s.json")
    w = World(store=store)
    action = w.request()
    w.approve(action.action_id)
    w.authorities.update("g-req-r", revoked=True)
    refused(lambda: w.commit(action.action_id), OpsRefusal.STALE_AUTHORITY)
    assert w.service.journal.records()[-1].result == "REFUSED"
    revived = _revive(store, w, store.load() or {}, None)
    assert revived.action(action.action_id).state is ActionState.APPROVED

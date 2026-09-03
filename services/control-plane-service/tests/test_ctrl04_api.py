"""CTRL-04 HTTP API: transport, negative paths and non-authoritative browser."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any

from _ctrl04_builders import World
from epd2_control_plane_service.operations_adapters import BackendState
from epd2_control_plane_service.operations_api import CONSOLE_HTML, ConsoleApp, serve
from epd2_control_plane_service.operations_console import OpsRefusal


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


def test_unauthenticated_and_unknown_routes() -> None:
    c = Client(World())
    assert c.call("GET", "/ops/v1/targets", session=None)[0] == 401
    assert c.call("GET", "/ops/v1/targets", session="sess-nobody")[0] == 401
    status, payload = c.call("GET", "/ops/v1/nothing")
    assert status == 404 and payload["error"] == OpsRefusal.NOT_FOUND.value
    status, payload = c.call("PUT", "/ops/v1/targets")
    assert status == 405
    status, html, content_type = c.app.handle("GET", "/", {}, b"")
    assert status == 200 and html == CONSOLE_HTML and content_type.startswith("text/html")


def test_no_shell_sql_or_secret_surface_exists() -> None:
    c = Client(World())
    for path in (
        "/ops/v1/shell",
        "/ops/v1/exec",
        "/ops/v1/sql",
        "/ops/v1/ssh",
        "/ops/v1/secrets",
        "/ops/v1/sql/run",
    ):
        for method in ("GET", "POST"):
            status, payload = c.call(method, path, {"command": "id"} if method == "POST" else None)
            assert status == 403, path
            assert payload["error"] == "OPS_DIRECT_EXECUTION_SURFACE_ABSENT", path


def test_browser_cannot_supply_authoritative_state() -> None:
    c = Client(World())
    for field in (
        "approval_state",
        "state",
        "result_state",
        "authority_ref",
        "approvals",
        "projection",
        "signature",
        "outcome",
    ):
        status, payload = c.call(
            "POST",
            "/ops/v1/actions",
            {
                "action_type": "OPS.SERVICE.RESTART",
                "target_id": "svc-web",
                "parameters": {"reason": "x"},
                "idempotency_key": "k",
                field: "APPROVED",
            },
        )
        assert status == 400 and payload["error"] == OpsRefusal.BROWSER_STATE_REJECTED.value, field
    assert not c.world.service.actions()


def test_http_lifecycle_and_derived_results() -> None:
    w = World()
    c = Client(w)
    w.adapter.inject_outcome("svc-web", BackendState.COMPLETED, polls=1)
    status, action = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "ticket-1"},
            "idempotency_key": "http-1",
            "purpose": "ticket-1",
        },
        session="sess-dual-hat",
    )
    assert status == 202 and action["state"] == "AWAITING_APPROVAL"
    action_id = action["action_id"]
    # Same idempotency key over HTTP returns the same action.
    status, again = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "ticket-1"},
            "idempotency_key": "http-1",
        },
        session="sess-dual-hat",
    )
    assert status == 202 and again["action_id"] == action_id
    # Insufficient authority: reader cannot request; executor cannot approve.
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "x"},
            "idempotency_key": "r",
        },
        session="sess-reader",
    )
    assert status == 403 and payload["error"] == "OPS_WRONG_SCOPE"
    status, payload = c.call(
        "POST",
        f"/ops/v1/actions/{action_id}/approve",
        {"approver_class": "INCIDENT_COMMANDER"},
        session="sess-executor",
    )
    assert status == 403
    status, payload = c.call(
        "POST",
        f"/ops/v1/actions/{action_id}/approve",
        {"approver_class": "INCIDENT_COMMANDER"},
        session="sess-dual-hat",
    )
    assert status == 403 and payload["error"] == OpsRefusal.SELF_APPROVAL.value
    status, payload = c.call(
        "POST",
        f"/ops/v1/actions/{action_id}/approve",
        {"approver_class": "INCIDENT_COMMANDER"},
        session="sess-incident-commander",
    )
    assert status == 200 and payload["state"] == "APPROVED"
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/commit", {}, session="sess-incident-commander"
    )
    assert status == 403
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/commit", {}, session="sess-executor"
    )
    assert status == 200 and payload["state"] == "EXECUTING" and payload["result"] is None
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/commit", {}, session="sess-executor"
    )
    assert status == 403 and payload["error"] == OpsRefusal.DUPLICATE_EXECUTION.value
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/resolve", {}, session="sess-reader"
    )
    assert (
        status == 200
        and payload["state"] == "EXECUTING"
        and payload["execution"]["state"] == "RUNNING"
    )
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/resolve", {}, session="sess-reader"
    )
    assert (
        status == 200
        and payload["state"] == "SUCCEEDED"
        and payload["result"]["state"] == "SUCCEEDED"
    )
    assert payload["result"]["backend_metadata"]["api_token"] == "[REDACTED]"
    from _ctrl04_builders import BERLIN
    from epd2_control_plane_service.regional_operations import ActorClass, AuthorityGrant

    w.authorities.add(
        AuthorityGrant("g-exec-rev", "executor", ActorClass.HUMAN, "OPS.REVIEW", BERLIN, 1)
    )
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/review", {}, session="sess-executor"
    )
    assert status == 403 and payload["error"] == OpsRefusal.EXECUTOR_REVIEWS.value
    status, payload = c.call(
        "POST", f"/ops/v1/actions/{action_id}/review", {}, session="sess-reviewer"
    )
    assert status == 200 and payload["review_state"] == "REVIEWED"
    status, evidence = c.call("GET", f"/ops/v1/evidence/{action_id}", session="sess-reader")
    assert status == 200 and evidence["schema"] == "epd2.ctrl04.evidence.v1"
    assert evidence["actor_ref"] == "dual-hat" and evidence["result_state"] == "SUCCEEDED"
    status, evidence = c.call("GET", "/ops/v1/evidence/OPA-424242", session="sess-reader")
    assert status == 404


def test_reads_are_scope_filtered_and_typed() -> None:
    w = World()
    c = Client(w)
    status, payload = c.call("GET", "/ops/v1/targets", session="sess-bavaria-requester")
    assert status == 200 and payload["targets"] == []
    status, payload = c.call(
        "GET", "/ops/v1/status?target_id=svc-web", session="sess-bavaria-requester"
    )
    assert status == 403 and payload["error"] == "OPS_WRONG_SCOPE"
    status, payload = c.call(
        "GET", "/ops/v1/status?target_id=svc-voting-tally", session="sess-reader"
    )
    assert status == 403 and payload["error"] == OpsRefusal.VOTING_BOUNDARY.value
    status, payload = c.call("GET", "/ops/v1/targets", session="sess-reader")
    ids = {t["target_id"] for t in payload["targets"]}
    assert "svc-voting-tally" not in ids and "svc-web" in ids
    legacy = {t["target_id"]: t for t in payload["targets"]}["svc-legacy"]
    assert legacy["unavailable_actions"]["OPS.SERVICE.RESTART"] == "UNSUPPORTED_BY_BACKEND"
    assert legacy["deployment_identity"]["release_ref"] == "rel-1.3.9"
    status, payload = c.call("GET", "/ops/v1/health?target_id=int-payment", session="sess-reader")
    assert (
        payload["health"]["state"] == "DEGRADED"
        and payload["health"]["details"]["provider_password"] == "[REDACTED]"
    )
    status, payload = c.call("GET", "/ops/v1/health?target_id=svc-legacy", session="sess-reader")
    assert payload["health"]["state"] == "UNAVAILABLE"
    status, payload = c.call("GET", "/ops/v1/jobs?target_id=queue-mail", session="sess-reader")
    assert payload["queue"]["state"] == "RUNNING" and payload["queue"]["depth"] == 12
    status, payload = c.call("GET", "/ops/v1/jobs?target_id=svc-web", session="sess-reader")
    assert status == 400
    status, payload = c.call(
        "GET", "/ops/v1/integrations?target_id=int-payment", session="sess-reader"
    )
    assert payload["health"]["state"] == "DEGRADED"
    status, payload = c.call(
        "GET", "/ops/v1/deployment-identity?target_id=svc-web", session="sess-reader"
    )
    assert (
        payload["deployment_identity"]["artifact_digest"] == "a" * 64
        and payload["deployment_identity"]["change_ref"] == "chg-101"
    )
    status, payload = c.call(
        "GET", "/ops/v1/recovery-readiness?target_id=db-members", session="sess-reader"
    )
    assert payload["recovery_readiness"]["readiness"] == "NOT_READY"
    status, payload = c.call("GET", "/ops/v1/me", session="sess-readonly-operator")
    assert payload["read_only"] is True
    status, payload = c.call("GET", "/ops/v1/read-model", session="sess-reader")
    assert status == 200 and payload["self_state"] == "CANDIDATE_NOT_ACCEPTED"
    status, payload = c.call("GET", "/ops/v1/catalogue", session=None)
    assert status == 200 and any(
        a["action_id"] == "OPS.RESTORE.REQUEST" and a["destructive_confirmation"]
        for a in payload["actions"]
    )


def test_read_only_operator_over_http_cannot_mutate() -> None:
    c = Client(World())
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "x"},
            "idempotency_key": "ro",
        },
        session="sess-readonly-operator",
    )
    assert status == 403 and payload["error"] == OpsRefusal.READ_ONLY_SESSION.value


def test_invalid_bodies_are_refused() -> None:
    c = Client(World())
    status, payload, _ = c.app.handle(
        "POST", "/ops/v1/actions", {"X-EPD2-Session": "sess-requester"}, b"{not json"
    )
    assert status == 400
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {"action_type": "OPS.DELETE.EVERYTHING", "target_id": "svc-web", "idempotency_key": "k"},
    )
    assert status == 400 and payload["error"] == OpsRefusal.UNKNOWN_ACTION.value
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": "x"},
        },
    )
    assert status == 400 and payload["error"] == OpsRefusal.IDEMPOTENCY_CONFLICT.value
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "svc-web",
            "parameters": {"reason": 5},
            "idempotency_key": "k",
        },
    )
    assert status == 400
    status, payload = c.call(
        "POST",
        "/ops/v1/actions",
        {
            "action_type": "OPS.SERVICE.RESTART",
            "target_id": "nope",
            "parameters": {"reason": "x"},
            "idempotency_key": "k",
        },
    )
    assert status == 404
    status, payload = c.call(
        "POST", "/ops/v1/actions/OPA-000001/approve", {"approver_class": "GOD"}
    )
    assert status in {400, 404}


def test_real_http_server_round_trip() -> None:
    w = World()
    app = ConsoleApp(w.service, clock=lambda: w.tick())
    server = serve(app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        req = urllib.request.Request(
            base + "/ops/v1/targets", headers={"X-EPD2-Session": "sess-reader"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers["Content-Security-Policy"].startswith("default-src 'self'")
            data = json.loads(resp.read())
        assert {t["target_id"] for t in data["targets"]} >= {"svc-web", "db-members"}
        req = urllib.request.Request(
            base + "/ops/v1/shell",
            data=b"{}",
            headers={"X-EPD2-Session": "sess-reader", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=5)
            raise AssertionError("shell surface must not exist")
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
        with urllib.request.urlopen(base + "/", timeout=5) as resp:
            html = resp.read().decode()
        assert "Explicit confirmation required" in html and "READ_ONLY" in html
    finally:
        server.shutdown()
        server.server_close()

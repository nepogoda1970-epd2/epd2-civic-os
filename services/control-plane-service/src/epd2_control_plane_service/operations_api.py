"""CTRL-04 Operations Console HTTP API and embedded console UI.

The API is a thin governed transport over `OperationsConsoleService`. The
browser supplies *intent* only (which action, which target, which governed
parameters). Authority, approval state, execution state and results are
resolved server-side from the CTRL-02 authority directory, the console's own
records and the adapter's own report. Any client attempt to supply those
fields is refused, not ignored.

There is deliberately no shell, SQL or raw provider endpoint. Requests for
such surfaces are answered with a governed refusal so that their absence is
observable rather than implicit.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_console import (
    ACTION_CATALOGUE,
    CTRL04_ACTIONS,
    SELF_STATE,
    STAGE,
    ActionType,
    AuthorityProjection,
    OperationsConsoleService,
    OpsRefusal,
    TargetClass,
)
from epd2_control_plane_service.regional_operations import ApproverClass, ExactScope

__all__ = ["CONSOLE_HTML", "FORBIDDEN_CLIENT_FIELDS", "ConsoleApp", "serve"]

SESSION_HEADER = "X-EPD2-Session"

#: Fields a client may never supply. Their presence is a refusal, because a
#: browser is not an authority source and not a result source.
FORBIDDEN_CLIENT_FIELDS = frozenset(
    {
        "state",
        "approval_state",
        "execution_state",
        "result_state",
        "result",
        "authority_ref",
        "authority_version",
        "authority_projection",
        "projection",
        "approvals",
        "approval_ids",
        "approved",
        "outcome",
        "backend_outcome",
        "signature",
        "grant_id",
        "actor_ref",
        "principal_id",
        "read_only",
    }
)

FORBIDDEN_SURFACES = (
    "/ops/v1/shell",
    "/ops/v1/exec",
    "/ops/v1/sql",
    "/ops/v1/ssh",
    "/ops/v1/secrets",
)


class ApiError(Exception):
    def __init__(self, status: int, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.reason_code = reason_code
        self.detail = detail


class ConsoleApp:
    """Transport-independent request handler."""

    def __init__(
        self,
        service: OperationsConsoleService,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.service = service
        self.clock = clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()

    # -- helpers -------------------------------------------------------------

    def _principal(self, headers: Mapping[str, str]) -> tuple[str, str]:
        lowered = {k.lower(): v for k, v in headers.items()}
        session_id = lowered.get(SESSION_HEADER.lower(), "")
        session = self.service.session(session_id)
        if session is None:
            raise ApiError(401, OpsRefusal.NO_SESSION.value, "no console session")
        usable, why = session.usable_at(self.clock())
        if not usable:
            assert why is not None
            raise ApiError(401, why.value, f"session {why.value}")
        return session_id, session.principal_id

    def _projection(
        self,
        principal_id: str,
        capability: str,
        scope: ExactScope,
        approver_class: str | None = None,
    ) -> AuthorityProjection:
        """Resolve a projection server-side from the authority directory."""
        now = self.clock()
        try:
            grant = self.service.authorities.require(
                actor_id=principal_id,
                capability=capability,
                scope=scope,
                now=now,
                approver_class=None if approver_class is None else ApproverClass(approver_class),
            )
        except AuthorizationRefused as exc:
            raise ApiError(403, f"OPS_{exc.reason_code}", str(exc)) from exc
        return self.service.signer.issue(grant, now=now)

    def _readable_targets(self, principal_id: str) -> list[Any]:
        now = self.clock()
        out = []
        for target in self.service.targets():
            try:
                self.service.authorities.require(
                    actor_id=principal_id, capability="OPS.READ", scope=target.scope, now=now
                )
            except AuthorizationRefused:
                continue
            out.append(target)
        return out

    def _read_target(
        self, headers: Mapping[str, str], target_id: str, action_type: ActionType
    ) -> Any:
        session_id, principal = self._principal(headers)
        try:
            target = self.service.target(target_id)
        except AuthorizationRefused as exc:
            raise ApiError(404, str(exc.reason_code), str(exc)) from exc
        projection = self._projection(principal, "OPS.READ", target.scope)
        try:
            self.service.authorize_read(
                actor_ref=principal,
                session_id=session_id,
                projection=projection,
                action_type=action_type,
                target_id=target_id,
                now=self.clock(),
            )
        except AuthorizationRefused as exc:
            raise ApiError(403, str(exc.reason_code), str(exc)) from exc
        return target

    @staticmethod
    def _reject_client_state(body: Mapping[str, Any]) -> None:
        present = sorted(set(body) & FORBIDDEN_CLIENT_FIELDS)
        if present:
            raise ApiError(
                400,
                OpsRefusal.BROWSER_STATE_REJECTED.value,
                f"client may not supply authoritative fields: {present}",
            )

    # -- dispatch -------------------------------------------------------------

    def handle(
        self, method: str, raw_path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, Any] | str, str]:
        """Return (status, payload, content_type)."""
        parts = urlsplit(raw_path)
        path = parts.path.rstrip("/") or "/"
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        try:
            if path in FORBIDDEN_SURFACES or any(
                path.startswith(p + "/") for p in FORBIDDEN_SURFACES
            ):
                raise ApiError(
                    403,
                    "OPS_DIRECT_EXECUTION_SURFACE_ABSENT",
                    "no shell, SQL, SSH or raw secret surface exists in the operations console",
                )
            if method == "GET":
                return self._get(path, query, headers)
            if method == "POST":
                payload: dict[str, Any] = json.loads(body.decode() or "{}") if body else {}
                if not isinstance(payload, dict):
                    raise ApiError(
                        400, OpsRefusal.PARAMETER_INVALID.value, "body must be an object"
                    )
                return self._post(path, payload, headers)
            raise ApiError(405, "OPS_METHOD_NOT_ALLOWED", "method not allowed")
        except ApiError as exc:
            return exc.status, {"error": exc.reason_code, "detail": exc.detail}, "application/json"
        except AuthorizationRefused as exc:
            status = 404 if exc.reason_code == OpsRefusal.NOT_FOUND.value else 403
            return status, {"error": str(exc.reason_code), "detail": str(exc)}, "application/json"
        except json.JSONDecodeError as exc:
            return (
                400,
                {"error": OpsRefusal.PARAMETER_INVALID.value, "detail": str(exc)},
                "application/json",
            )
        except Exception as exc:
            return (
                500,
                {"error": "OPS_INTERNAL_REFUSAL", "detail": type(exc).__name__},
                "application/json",
            )

    def _get(
        self, path: str, query: Mapping[str, str], headers: Mapping[str, str]
    ) -> tuple[int, Any, str]:
        now = self.clock()
        if path == "/":
            return 200, CONSOLE_HTML, "text/html; charset=utf-8"
        if path == "/ops/v1/catalogue":
            return (
                200,
                {"stage": STAGE, "self_state": SELF_STATE, "actions": list(CTRL04_ACTIONS)},
                "application/json",
            )
        session_id, principal = self._principal(headers)
        session = self.service.session(session_id)
        assert session is not None
        if path == "/ops/v1/me":
            grants = [
                {
                    "grant_id": g.grant_id,
                    "capability": g.capability,
                    "scope": g.scope.key,
                    "version": g.version,
                    "approver_class": None if g.approver_class is None else g.approver_class.value,
                }
                for g in self.service.authorities._grants.values()
                if g.actor_id == principal and g.usable_at(now)
            ]
            return (
                200,
                {
                    "principal_id": principal,
                    "session_state": session.state.value,
                    "read_only": session.read_only,
                    "usable": session.usable_at(now)[0],
                    "grants": grants,
                    "note": (
                        "frontend visibility is not authorization; "
                        "every act is re-authorized server-side"
                    ),
                },
                "application/json",
            )
        if path == "/ops/v1/targets":
            return (
                200,
                {"targets": [self._target_view(t) for t in self._readable_targets(principal)]},
                "application/json",
            )
        if path in {
            "/ops/v1/status",
            "/ops/v1/health",
            "/ops/v1/deployment-identity",
            "/ops/v1/recovery-readiness",
            "/ops/v1/jobs",
            "/ops/v1/integrations",
        }:
            target_id = query.get("target_id", "")
            action_type = {
                "/ops/v1/status": ActionType.STATUS_READ,
                "/ops/v1/health": ActionType.HEALTH_READ,
                "/ops/v1/deployment-identity": ActionType.DEPLOYMENT_IDENTITY_READ,
                "/ops/v1/recovery-readiness": ActionType.RECOVERY_READINESS_READ,
                "/ops/v1/jobs": ActionType.JOBS_READ,
                "/ops/v1/integrations": ActionType.INTEGRATION_READ,
            }[path]
            target = self._read_target(headers, target_id, action_type)
            if path == "/ops/v1/jobs":
                if target.target_class is not TargetClass.JOB_QUEUE:
                    raise ApiError(
                        400, OpsRefusal.PARAMETER_INVALID.value, "target is not a job queue"
                    )
                snap = self.service.job_queue(target_id, now=now)
                return (
                    200,
                    {"queue": {**asdict(snap), "observed_at": snap.observed_at.isoformat()}},
                    "application/json",
                )
            if (
                path == "/ops/v1/integrations"
                and target.target_class is not TargetClass.INTEGRATION
            ):
                raise ApiError(
                    400, OpsRefusal.PARAMETER_INVALID.value, "target is not an integration"
                )
            health = self.service.health(target_id, now=now)
            identity = self.service.deployment_identity(target_id)
            payload: dict[str, Any] = {"target": self._target_view(target)}
            if path in {"/ops/v1/status", "/ops/v1/health", "/ops/v1/integrations"}:
                payload["health"] = {
                    "state": health.state.value,
                    "observed_at": health.observed_at.isoformat(),
                    "details": dict(health.details),
                    "redacted_fields": list(health.redacted_fields),
                }
            if path in {"/ops/v1/status", "/ops/v1/deployment-identity"}:
                payload["deployment_identity"] = None if identity is None else asdict(identity)
            if path == "/ops/v1/recovery-readiness":
                payload["recovery_readiness"] = self.service.recovery_readiness(target_id, now=now)
            return 200, payload, "application/json"
        if path == "/ops/v1/backups":
            return (
                200,
                {
                    "operations": [
                        self._enum_dict(asdict(b))
                        for b in self.service.backup_operations()
                        if self._can_read(principal, b.target_id)
                    ]
                },
                "application/json",
            )
        if path == "/ops/v1/maintenance":
            # Housekeeping on read: due expiries are recorded before listing so
            # that the console never shows an expired window as active.
            self.service.expire_due(now=now)
            return (
                200,
                {
                    "windows": [
                        {**self._enum_dict(asdict(w)), "active_now": w.is_active_at(now)}
                        for w in self.service.maintenance_windows()
                        if self._can_read(principal, w.target_id)
                    ]
                },
                "application/json",
            )
        if path == "/ops/v1/incidents":
            return (
                200,
                {
                    "incidents": [
                        self._enum_dict(asdict(i))
                        for i in self.service.incidents()
                        if self._can_read(principal, i.target_id)
                    ]
                },
                "application/json",
            )
        if path == "/ops/v1/actions":
            return (
                200,
                {
                    "actions": [
                        self.service.action_view(a.action_id)
                        for a in self.service.actions()
                        if self._can_read(principal, a.target_id)
                    ]
                },
                "application/json",
            )
        if path.startswith("/ops/v1/actions/"):
            action_id = path.rsplit("/", 1)[1]
            action = self.service.action(action_id)
            if not self._can_read(principal, action.target_id):
                raise ApiError(
                    403, OpsRefusal.WRONG_SCOPE.value, "no read authority in target scope"
                )
            return 200, self.service.action_view(action_id), "application/json"
        if path.startswith("/ops/v1/evidence/"):
            action_id = path.rsplit("/", 1)[1]
            record = self.service.evidence_record(action_id)
            target_id = str(record["target_ref"]).split("@", 1)[0]
            try:
                self._read_target(headers, target_id, ActionType.EVIDENCE_LOOKUP)
            except ApiError as exc:
                if exc.status != 404:
                    raise
                # Refused request against an unknown target: scope by the
                # recorded scope key instead of a target lookup.
                if not any(
                    t.scope.key == record["region_scope"] for t in self._readable_targets(principal)
                ):
                    raise ApiError(
                        403, OpsRefusal.WRONG_SCOPE.value, "no read authority in scope"
                    ) from exc
            return 200, record, "application/json"
        if path == "/ops/v1/read-model":
            model = self.service.read_model(now=now)
            readable = {t.target_id for t in self._readable_targets(principal)}
            model["targets"] = [t for t in model["targets"] if t["target_id"] in readable]
            model["actions"] = [a for a in model["actions"] if a["target_id"] in readable]
            model["maintenance_windows"] = [
                w for w in model["maintenance_windows"] if w["target_id"] in readable
            ]
            model["backup_operations"] = [
                b for b in model["backup_operations"] if b["target_id"] in readable
            ]
            model["incidents"] = [i for i in model["incidents"] if i["target_id"] in readable]
            return 200, model, "application/json"
        raise ApiError(404, OpsRefusal.NOT_FOUND.value, "unknown route")

    def _can_read(self, principal: str, target_id: str) -> bool:
        try:
            target = self.service.target(target_id)
            self.service.authorities.require(
                actor_id=principal, capability="OPS.READ", scope=target.scope, now=self.clock()
            )
            return True
        except AuthorizationRefused:
            return False

    @staticmethod
    def _enum_dict(value: Mapping[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, datetime):
                out[key] = item.isoformat()
            elif hasattr(item, "value") and not isinstance(item, str | int):
                out[key] = item.value
            elif isinstance(item, str) and hasattr(item, "value"):
                out[key] = str(item)
            elif isinstance(item, tuple):
                out[key] = list(item)
            else:
                out[key] = item
        return out

    def _target_view(self, target: Any) -> dict[str, Any]:
        identity = self.service.deployment_identity(target.target_id)
        adapter = self.service.adapters.get(target.adapter_id)
        supported = (
            sorted(c.value for c in adapter.capabilities(target.target_id))
            if adapter and adapter.available
            else []
        )
        unavailable = {}
        for spec in ACTION_CATALOGUE.values():
            if not spec.mutation or spec.capability is None:
                continue
            if target.target_class not in spec.target_classes:
                unavailable[spec.action_type.value] = "NOT_APPLICABLE_TO_TARGET_CLASS"
            elif adapter is None or not adapter.available:
                unavailable[spec.action_type.value] = "BACKEND_ADAPTER_UNAVAILABLE"
            elif spec.capability.value not in supported:
                unavailable[spec.action_type.value] = "UNSUPPORTED_BY_BACKEND"
        return {
            "target_id": target.target_id,
            "display_name": target.display_name,
            "target_class": target.target_class.value,
            "environment": target.environment.value,
            "production_like": target.environment.value == "PRODUCTION_LIKE",
            "scope": target.scope.key,
            "version": target.version,
            "adapter_id": target.adapter_id,
            "adapter_available": bool(adapter and adapter.available),
            "supported_capabilities": supported,
            "unavailable_actions": unavailable,
            "deployment_identity_ref": target.deployment_identity_ref,
            "deployment_identity": None if identity is None else asdict(identity),
        }

    def _post(
        self, path: str, body: dict[str, Any], headers: Mapping[str, str]
    ) -> tuple[int, Any, str]:
        self._reject_client_state(body)
        session_id, principal = self._principal(headers)
        now = self.clock()
        if path == "/ops/v1/actions":
            try:
                action_type = ActionType(str(body.get("action_type", "")))
            except ValueError as exc:
                raise ApiError(400, OpsRefusal.UNKNOWN_ACTION.value, "unknown action type") from exc
            target_id = str(body.get("target_id", ""))
            parameters = body.get("parameters", {})
            if not isinstance(parameters, dict) or any(
                not isinstance(v, str) for v in parameters.values()
            ):
                raise ApiError(
                    400, OpsRefusal.PARAMETER_INVALID.value, "parameters must be a string map"
                )
            idempotency_key = str(body.get("idempotency_key", ""))
            if not idempotency_key:
                raise ApiError(
                    400, OpsRefusal.IDEMPOTENCY_CONFLICT.value, "idempotency_key is mandatory"
                )
            try:
                target = self.service.target(target_id)
            except AuthorizationRefused as exc:
                raise ApiError(404, str(exc.reason_code), str(exc)) from exc
            projection = self._projection(principal, "OPS.REQUEST", target.scope)
            action = self.service.request(
                actor_ref=principal,
                session_id=session_id,
                projection=projection,
                action_type=action_type,
                target_id=target_id,
                parameters=parameters,
                idempotency_key=idempotency_key,
                purpose=str(body.get("purpose", ""))[:512],
                now=now,
                incident_ref=body.get("incident_ref"),
            )
            return 202, self.service.action_view(action.action_id), "application/json"
        if path.startswith("/ops/v1/actions/"):
            parts = path.split("/")
            if len(parts) != 6 or not parts[5]:
                raise ApiError(404, OpsRefusal.NOT_FOUND.value, "unknown route")
            action_id, verb = parts[4], parts[5]
            action = self.service.action(action_id)
            target = self.service.target(action.target_id)
            if verb == "approve":
                approver_class = str(body.get("approver_class", ""))
                if approver_class not in ApproverClass.__members__:
                    raise ApiError(
                        400, OpsRefusal.APPROVER_CLASS_MISSING.value, "approver_class required"
                    )
                projection = self._projection(
                    principal, "OPS.APPROVE", target.scope, approver_class
                )
                updated = self.service.approve(
                    action_id=action_id,
                    approver_ref=principal,
                    session_id=session_id,
                    projection=projection,
                    approver_class=approver_class,
                    now=now,
                )
                return 200, self.service.action_view(updated.action_id), "application/json"
            if verb == "commit":
                projection = self._projection(principal, "OPS.EXECUTE", target.scope)
                updated = self.service.commit(
                    action_id=action_id,
                    executor_ref=principal,
                    session_id=session_id,
                    projection=projection,
                    now=now,
                )
                return 200, self.service.action_view(updated.action_id), "application/json"
            if verb == "resolve":
                if not self._can_read(principal, action.target_id):
                    raise ApiError(
                        403, OpsRefusal.WRONG_SCOPE.value, "no read authority in target scope"
                    )
                updated = self.service.resolve(action_id=action_id, now=now)
                return 200, self.service.action_view(updated.action_id), "application/json"
            if verb == "cancel":
                updated = self.service.cancel(
                    action_id=action_id, actor_ref=principal, session_id=session_id, now=now
                )
                return 200, self.service.action_view(updated.action_id), "application/json"
            if verb == "review":
                projection = self._projection(principal, "OPS.REVIEW", target.scope)
                updated = self.service.review(
                    action_id=action_id,
                    reviewer_ref=principal,
                    session_id=session_id,
                    projection=projection,
                    now=now,
                )
                return 200, self.service.action_view(updated.action_id), "application/json"
        raise ApiError(404, OpsRefusal.NOT_FOUND.value, "unknown route")


def serve(app: ConsoleApp, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        server_version = "EPD2-CTRL04/0.1"

        def _run(self, method: str) -> None:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length else b""
            status, payload, content_type = app.handle(
                method, self.path, dict(self.headers.items()), body
            )
            data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'",
            )
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._run("GET")

        def do_POST(self) -> None:
            self._run("POST")

        def log_message(self, *args: Any) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


#: The embedded single-page console. Kept as a sibling file so that the UI
#: source is reviewable as HTML; it is served verbatim and carries no data.
CONSOLE_HTML = (Path(__file__).with_name("operations_console.html")).read_text(encoding="utf-8")

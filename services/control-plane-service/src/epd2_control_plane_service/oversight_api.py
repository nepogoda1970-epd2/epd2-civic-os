"""CTRL-05 Audit & Oversight Console HTTP API and embedded console UI.

The API is a thin governed transport over `OversightConsoleService`. The
browser supplies *intent* only: which scope, which evidence reference, which
governed act. Integrity verdicts, authority, mandates, review state and export
redaction are all resolved server-side; a client attempt to supply any of them
is refused rather than ignored.

Two absences are deliberate and observable:

* there is no shell, SSH, SQL, exec, Kubernetes or raw-secret surface, and
* there is no route that executes, requests, approves or cancels any CTRL-04
  operational action.

Requests for such paths are answered with a governed refusal so that the
absence is provable from outside the process rather than asserted in prose.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.oversight_console import (
    CTRL05_ACTIONS,
    EXPORT_PURPOSES,
    MAX_EXPORT_RECORDS,
    MAX_GRAPH_DEPTH,
    MAX_GRAPH_NODES,
    MAX_QUERY_LIMIT,
    SELF_STATE,
    STAGE,
    AuditRight,
    EvidenceQuery,
    FindingSeverity,
    OversightConsoleService,
    OversightRefusal,
    OversightScope,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import EvidencePlane

__all__ = [
    "CONSOLE_HTML",
    "FORBIDDEN_CLIENT_FIELDS",
    "FORBIDDEN_SURFACES",
    "OversightApp",
    "serve",
]

SESSION_HEADER = "X-EPD2-Session"
CSRF_HEADER = "X-EPD2-CSRF"

#: Fields a client may never supply. A browser is neither an integrity source,
#: an authority source, nor a review-state source.
FORBIDDEN_CLIENT_FIELDS = frozenset(
    {
        "integrity",
        "integrity_state",
        "trustworthy",
        "recomputed_hash",
        "recorded_hash",
        "event_hash",
        "content_digest",
        "verified",
        "verified_by",
        "mandate_id",
        "mandate_ref",
        "authority_ref",
        "authority_version",
        "authority_grant_id",
        "grant_id",
        "rights",
        "planes_granted",
        "state",
        "case_state",
        "case_version",
        "version",
        "actor_ref",
        "principal_id",
        "attested_by",
        "outcome",
        "payload_digest",
        "redaction_decision",
        "redacted_fields",
        "dropped_fields",
        "allow_fields",
        "policy",
        "self_state",
    }
)

#: Surfaces that must not exist. Their absence is asserted by refusal.
FORBIDDEN_SURFACES = (
    "/audit/v1/shell",
    "/audit/v1/exec",
    "/audit/v1/sql",
    "/audit/v1/ssh",
    "/audit/v1/kubectl",
    "/audit/v1/secrets",
    "/audit/v1/keys",
    "/audit/v1/operations",
    "/audit/v1/actions/execute",
    "/audit/v1/evidence/mutate",
)


class ApiError(Exception):
    def __init__(self, status: int, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.reason_code = reason_code
        self.detail = detail


def _scope_from(payload: Mapping[str, Any]) -> OversightScope:
    try:
        return OversightScope(
            region_id=str(payload["region_id"]),
            org_id=str(payload["org_id"]),
            unit_id=str(payload["unit_id"]),
        )
    except KeyError as exc:
        raise ApiError(
            400,
            OversightRefusal.PARAMETER_INVALID.value,
            "an exact scope (region_id, org_id, unit_id) is required on every route",
        ) from exc
    except (ValueError, TypeError) as exc:
        raise ApiError(400, OversightRefusal.PARAMETER_INVALID.value, str(exc)) from exc


def _str(payload: Mapping[str, Any], key: str, *, required: bool = True) -> str:
    value = payload.get(key)
    if value is None:
        if required:
            raise ApiError(400, OversightRefusal.PARAMETER_INVALID.value, f"{key} is required")
        return ""
    if not isinstance(value, str):
        raise ApiError(400, OversightRefusal.PARAMETER_INVALID.value, f"{key} must be a string")
    return value


def _int(payload: Mapping[str, Any], key: str, default: int) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ApiError(400, OversightRefusal.PARAMETER_INVALID.value, f"{key} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ApiError(
            400, OversightRefusal.PARAMETER_INVALID.value, f"{key} must be an integer"
        ) from exc


class OversightApp:
    """Transport-independent request handler for the oversight console."""

    def __init__(
        self,
        service: OversightConsoleService,
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
            raise ApiError(401, OversightRefusal.NO_SESSION.value, "no oversight session")
        usable, why = session.usable_at(self.clock())
        if not usable:
            assert why is not None
            raise ApiError(401, why.value, f"session {why.value}")
        return session_id, session.principal_id

    def _csrf(self, headers: Mapping[str, str]) -> str | None:
        lowered = {k.lower(): v for k, v in headers.items()}
        return lowered.get(CSRF_HEADER.lower())

    @staticmethod
    def _reject_client_state(body: Mapping[str, Any]) -> None:
        present = sorted(set(body) & FORBIDDEN_CLIENT_FIELDS)
        if present:
            raise ApiError(
                400,
                OversightRefusal.BROWSER_STATE_REJECTED.value,
                f"client may not supply authoritative fields: {present}",
            )

    # -- dispatch ------------------------------------------------------------

    def handle(
        self, method: str, raw_path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, Any] | str, str]:
        """Return (status, payload, content_type).

        See `handle_with_headers` for the response headers a transport must
        also emit; this signature is kept for callers that only need the body.
        """
        status, payload, content_type, _extra = self.handle_with_headers(
            method, raw_path, headers, body
        )
        return status, payload, content_type

    def handle_with_headers(
        self, method: str, raw_path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, Any] | str, str, dict[str, str]]:
        """Return (status, payload, content_type, extra response headers).

        The session's CSRF token is a credential, so it is returned as a
        response *header* on `/audit/v1/me` and never inside a read body: a
        body is logged, cached and re-serialised in places a header is not.
        """
        extra: dict[str, str] = {}
        parts_for_csrf = urlsplit(raw_path).path.rstrip("/") or "/"
        if method == "GET" and parts_for_csrf == "/audit/v1/me":
            lowered = {k.lower(): v for k, v in headers.items()}
            session = self.service.session(lowered.get(SESSION_HEADER.lower(), ""))
            if session is not None and session.usable_at(self.clock())[0]:
                extra[CSRF_HEADER] = session.csrf_token
        status, payload, content_type = self._handle(method, raw_path, headers, body)
        if status != 200:
            extra.pop(CSRF_HEADER, None)
        return status, payload, content_type, extra

    def _handle(
        self, method: str, raw_path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, Any] | str, str]:
        parts = urlsplit(raw_path)
        path = parts.path.rstrip("/") or "/"
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        try:
            if path in FORBIDDEN_SURFACES or any(
                path.startswith(p + "/") for p in FORBIDDEN_SURFACES
            ):
                raise ApiError(
                    403,
                    OversightRefusal.EXECUTION_SURFACE_ABSENT.value,
                    "the oversight console has no shell, SQL, SSH, exec, cluster, secret "
                    "or operational-execution surface",
                )
            if method == "GET":
                return self._get(path, query, headers)
            if method == "POST":
                payload: Any = json.loads(body.decode() or "{}") if body else {}
                if not isinstance(payload, dict):
                    raise ApiError(
                        400, OversightRefusal.PARAMETER_INVALID.value, "body must be an object"
                    )
                return self._post(path, payload, headers)
            raise ApiError(405, "AUD_METHOD_NOT_ALLOWED", "method not allowed")
        except ApiError as exc:
            return exc.status, {"error": exc.reason_code, "detail": exc.detail}, "application/json"
        except AuthorizationRefused as exc:
            status = 404 if exc.reason_code == OversightRefusal.NOT_FOUND.value else 403
            return status, {"error": str(exc.reason_code), "detail": str(exc)}, "application/json"
        except json.JSONDecodeError as exc:
            return (
                400,
                {"error": OversightRefusal.PARAMETER_INVALID.value, "detail": str(exc)},
                "application/json",
            )
        except (ValueError, TypeError, KeyError) as exc:
            return (
                400,
                {"error": OversightRefusal.PARAMETER_INVALID.value, "detail": type(exc).__name__},
                "application/json",
            )
        except Exception as exc:  # never leak a traceback
            return (
                500,
                {"error": "AUD_INTERNAL_REFUSAL", "detail": type(exc).__name__},
                "application/json",
            )

    # -- reads ---------------------------------------------------------------

    def _get(
        self, path: str, query: Mapping[str, str], headers: Mapping[str, str]
    ) -> tuple[int, Any, str]:
        now = self.clock()
        if path == "/":
            return 200, CONSOLE_HTML, "text/html; charset=utf-8"
        if path == "/audit/v1/catalogue":
            return (
                200,
                {
                    "stage": STAGE,
                    "self_state": SELF_STATE,
                    "actions": [dict(a) for a in CTRL05_ACTIONS],
                    "export_purposes": {k: sorted(v) for k, v in EXPORT_PURPOSES.items()},
                    "bounds": {
                        "query_limit": MAX_QUERY_LIMIT,
                        "graph_nodes": MAX_GRAPH_NODES,
                        "graph_depth": MAX_GRAPH_DEPTH,
                        "export_records": MAX_EXPORT_RECORDS,
                    },
                    "absent_surfaces": list(FORBIDDEN_SURFACES),
                    "operational_execution_surface": "ABSENT",
                    "secret_surface": "ABSENT",
                },
                "application/json",
            )
        session_id, principal = self._principal(headers)
        session = self.service.session(session_id)
        assert session is not None
        if path == "/audit/v1/me":
            mandates = [
                {
                    "mandate_id": m.mandate_id,
                    "scope": m.scope.key,
                    "organization": m.scope.organization_key,
                    "unit": m.scope.unit_id,
                    "planes": sorted(p.value for p in m.planes),
                    "rights": sorted(r.value for r in m.rights),
                    "competence_ref": m.competence_ref,
                    "usable": m.usable_at(now)[0],
                }
                for m in self.service.mandates_of(principal)
            ]
            return (
                200,
                {
                    "principal_id": principal,
                    "session_state": session.state.value,
                    "usable": session.usable_at(now)[0],
                    "mandates": mandates,
                    "universal_auditor": False,
                    "may_execute_operations": False,
                    "note": (
                        "frontend visibility is not authorization and not an integrity "
                        "verdict; every act and every integrity claim is derived server-side"
                    ),
                },
                "application/json",
            )
        # Every case-shaped read is scoped: the caller names its exact
        # oversight scope in the query string and the service resolves the
        # mandate for it. There is no route that lists everything.
        if path == "/audit/v1/read-model":
            scope = _scope_from(query)
            return (
                200,
                self.service.governed_read_model(
                    actor_ref=principal, session_id=session_id, scope=scope, now=now
                ),
                "application/json",
            )
        if path == "/audit/v1/cases":
            scope = _scope_from(query)
            return (
                200,
                {
                    "scope": scope.key,
                    "cases": self.service.governed_cases(
                        actor_ref=principal, session_id=session_id, scope=scope, now=now
                    ),
                },
                "application/json",
            )
        if path.startswith("/audit/v1/cases/"):
            scope = _scope_from(query)
            case_id = path.rsplit("/", 1)[-1]
            try:
                return (
                    200,
                    self.service.governed_case(
                        actor_ref=principal,
                        session_id=session_id,
                        scope=scope,
                        case_id=case_id,
                        now=now,
                    ),
                    "application/json",
                )
            except AuthorizationRefused as exc:
                status = 404 if str(exc.reason_code) == OversightRefusal.UNKNOWN_CASE.value else 403
                raise ApiError(status, str(exc.reason_code), str(exc)) from exc
        if path == "/audit/v1/exports":
            scope = _scope_from(query)
            return (
                200,
                {
                    "scope": scope.key,
                    "exports": self.service.governed_exports(
                        actor_ref=principal, session_id=session_id, scope=scope, now=now
                    ),
                },
                "application/json",
            )
        if path == "/audit/v1/journal":
            return (
                200,
                {
                    "head_hash": self.service.journal.head_hash(),
                    "count": len(self.service.journal),
                    "append_only": True,
                },
                "application/json",
            )
        if path == "/audit/v1/voting-verification":
            scope = _scope_from(query)
            return (
                200,
                self.service.voting_verification_status(
                    actor_ref=principal, session_id=session_id, scope=scope, now=now
                ),
                "application/json",
            )
        raise ApiError(404, OversightRefusal.NOT_FOUND.value, "unknown route")

    # -- acts ----------------------------------------------------------------

    def _post(
        self, path: str, payload: dict[str, Any], headers: Mapping[str, str]
    ) -> tuple[int, Any, str]:
        now = self.clock()
        self._reject_client_state(payload)
        session_id, principal = self._principal(headers)
        csrf = self._csrf(headers)

        if path == "/audit/v1/evidence/search":
            scope = _scope_from(payload)
            planes = payload.get("planes") or []
            if not isinstance(planes, list):
                raise ApiError(
                    400, OversightRefusal.PARAMETER_INVALID.value, "planes must be a list"
                )
            try:
                query = EvidenceQuery(
                    scope=scope,
                    planes=frozenset(EvidencePlane(str(p)) for p in planes),
                    correlation_ref=payload.get("correlation_ref") or None,
                    action_code=payload.get("action_code") or None,
                    actor_ref=payload.get("subject_actor_ref") or None,
                    object_ref=payload.get("object_ref") or None,
                    result=payload.get("result") or None,
                    limit=_int(payload, "limit", 100),
                )
            except ValueError as exc:
                raise ApiError(400, OversightRefusal.PARAMETER_INVALID.value, str(exc)) from exc
            return (
                200,
                self.service.search(
                    actor_ref=principal, session_id=session_id, query=query, now=now
                ),
                "application/json",
            )

        if path == "/audit/v1/evidence/open":
            scope = _scope_from(payload)
            envelope = self.service.evidence(
                actor_ref=principal,
                session_id=session_id,
                scope=scope,
                reference_key=_str(payload, "reference_key"),
                now=now,
            )
            return 200, {"record": envelope.as_dict()}, "application/json"

        if path == "/audit/v1/evidence/verify":
            scope = _scope_from(payload)
            return (
                200,
                self.service.verify_evidence(
                    actor_ref=principal,
                    session_id=session_id,
                    scope=scope,
                    reference_key=_str(payload, "reference_key"),
                    now=now,
                ),
                "application/json",
            )

        if path == "/audit/v1/correlation/chain":
            scope = _scope_from(payload)
            return (
                200,
                self.service.action_chain(
                    actor_ref=principal,
                    session_id=session_id,
                    scope=scope,
                    correlation_ref=_str(payload, "correlation_ref"),
                    now=now,
                ),
                "application/json",
            )

        if path == "/audit/v1/correlation/graph":
            scope = _scope_from(payload)
            graph = self.service.correlation_graph(
                actor_ref=principal,
                session_id=session_id,
                scope=scope,
                anchor=_str(payload, "anchor"),
                depth=_int(payload, "depth", 1),
                now=now,
            )
            return 200, graph.as_dict(), "application/json"

        if path == "/audit/v1/cases":
            scope = _scope_from(payload)
            refs = payload.get("evidence_refs")
            if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
                raise ApiError(
                    400,
                    OversightRefusal.PARAMETER_INVALID.value,
                    "evidence_refs must be a list of reference keys",
                )
            case = self.service.open_case(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                scope=scope,
                title=_str(payload, "title"),
                evidence_refs=refs,
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return 201, self.service.case_view(case.case_id), "application/json"

        if path == "/audit/v1/cases/clarify":
            clarification = self.service.clarify(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                case_id=_str(payload, "case_id"),
                text=_str(payload, "text"),
                evidence_ref=payload.get("evidence_ref") or None,
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {
                    "clarification_id": clarification.clarification_id,
                    "case": self.service.case_view(clarification.case_id),
                    "source_evidence_mutated": False,
                },
                "application/json",
            )

        if path == "/audit/v1/prepare":
            try:
                right = AuditRight(_str(payload, "right"))
            except ValueError as exc:
                raise ApiError(
                    400, OversightRefusal.PARAMETER_INVALID.value, "unknown right"
                ) from exc
            ticket = self.service.prepare(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                case_id=_str(payload, "case_id"),
                act=_str(payload, "act"),
                right=right,
                now=now,
            )
            return 200, {"ticket": ticket}, "application/json"

        if path == "/audit/v1/cases/dispose":
            try:
                disposition = ReviewState(_str(payload, "disposition"))
            except ValueError as exc:
                raise ApiError(
                    400, OversightRefusal.PARAMETER_INVALID.value, "unknown disposition"
                ) from exc
            record = self.service.dispose(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                ticket_id=_str(payload, "ticket_id"),
                disposition=disposition,
                rationale=_str(payload, "rationale"),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {
                    "disposition_id": record.disposition_id,
                    "case": self.service.case_view(record.case_id),
                },
                "application/json",
            )

        if path == "/audit/v1/findings":
            try:
                severity = FindingSeverity(_str(payload, "severity"))
            except ValueError as exc:
                raise ApiError(
                    400, OversightRefusal.PARAMETER_INVALID.value, "unknown severity"
                ) from exc
            finding = self.service.raise_finding(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                ticket_id=_str(payload, "ticket_id"),
                severity=severity,
                summary=_str(payload, "summary"),
                evidence_ref=_str(payload, "evidence_ref"),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {"finding_id": finding.finding_id, "case": self.service.case_view(finding.case_id)},
                "application/json",
            )

        if path == "/audit/v1/findings/dispute":
            superseded, dispute = self.service.dispute_finding(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                finding_id=_str(payload, "finding_id"),
                rationale=_str(payload, "rationale"),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {
                    "disputed_finding_id": superseded.finding_id,
                    "dispute_finding_id": dispute.finding_id,
                    "original_retained": True,
                    "case": self.service.case_view(dispute.case_id),
                },
                "application/json",
            )

        if path == "/audit/v1/remediation":
            link = self.service.link_remediation(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                case_id=_str(payload, "case_id"),
                remediation_plane=_str(payload, "remediation_plane"),
                remediation_ref=_str(payload, "remediation_ref"),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {
                    "link_id": link.link_id,
                    "executed_by_ctrl05": False,
                    "case": self.service.case_view(link.case_id),
                },
                "application/json",
            )

        if path == "/audit/v1/cases/attest":
            attestation = self.service.attest(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                ticket_id=_str(payload, "ticket_id"),
                statement=_str(payload, "statement"),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return (
                201,
                {
                    "attestation_id": attestation.attestation_id,
                    "case": self.service.case_view(attestation.case_id),
                },
                "application/json",
            )

        if path == "/audit/v1/cases/close":
            case = self.service.close_case(
                actor_ref=principal,
                session_id=session_id,
                csrf_token=csrf,
                case_id=_str(payload, "case_id"),
                expected_version=_int(payload, "expected_version", -1),
                idempotency_key=_str(payload, "idempotency_key"),
                now=now,
            )
            return 200, self.service.case_view(case.case_id), "application/json"

        if path == "/audit/v1/exports":
            refs = payload.get("evidence_refs")
            if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
                raise ApiError(
                    400,
                    OversightRefusal.PARAMETER_INVALID.value,
                    "evidence_refs must be a list of reference keys",
                )
            return (
                201,
                self.service.export(
                    actor_ref=principal,
                    session_id=session_id,
                    csrf_token=csrf,
                    ticket_id=_str(payload, "ticket_id"),
                    purpose=_str(payload, "purpose"),
                    evidence_refs=refs,
                    idempotency_key=_str(payload, "idempotency_key"),
                    now=now,
                ),
                "application/json",
            )

        raise ApiError(404, OversightRefusal.NOT_FOUND.value, "unknown route")


def serve(app: OversightApp, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        server_version = "EPD2-CTRL05/0.1"

        def _run(self, method: str) -> None:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length else b""
            status, payload, content_type, extra = app.handle_with_headers(
                method, self.path, dict(self.headers.items()), body
            )
            data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for name, value in extra.items():
                self.send_header(name, value)
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


#: The embedded single-page console, kept as a sibling file so that the UI
#: source is reviewable as HTML. It is served verbatim and carries no data.
CONSOLE_HTML = (Path(__file__).with_name("oversight_console.html")).read_text(encoding="utf-8")

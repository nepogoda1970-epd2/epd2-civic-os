"""CTRL-05 HTTP API: intent in, authority out. The browser is not an authority
source, not an integrity source and not a review-state source, and the absent
surfaces are absent observably."""

from __future__ import annotations

import json
from typing import Any

import pytest
from _ctrl05_builders import NOW, OPS_UNIT, PRIVACY_UNIT, World
from epd2_control_plane_service.oversight_api import (
    CONSOLE_HTML,
    CSRF_HEADER,
    FORBIDDEN_CLIENT_FIELDS,
    FORBIDDEN_SURFACES,
    SESSION_HEADER,
    OversightApp,
)
from epd2_control_plane_service.oversight_console import (
    EXPORT_PURPOSES,
    OversightRefusal,
    ReviewState,
)


@pytest.fixture
def world() -> World:
    return World()


class Client:
    def __init__(self, world: World, principal: str = "auditor") -> None:
        self.world = world
        self.app = OversightApp(world.service, clock=lambda: world.tick())
        self.principal = principal

    def headers(self, *, csrf: str | None = "auto", session: str | None = None) -> dict[str, str]:
        head = {SESSION_HEADER: session or f"sess-{self.principal}"}
        if csrf == "auto":
            head[CSRF_HEADER] = f"csrf-{self.principal}"
        elif csrf is not None:
            head[CSRF_HEADER] = csrf
        return head

    def get(self, path: str, **kw: Any) -> tuple[int, Any]:
        status, payload, _ = self.app.handle("GET", path, self.headers(**kw), b"")
        return status, payload

    def get_scoped(self, path: str, scope: Any = OPS_UNIT, **kw: Any) -> tuple[int, Any]:
        query = f"?region_id={scope.region_id}&org_id={scope.org_id}&unit_id={scope.unit_id}"
        return self.get(path + query, **kw)

    def headers_and_body(self, path: str, **kw: Any) -> tuple[int, Any, dict[str, str]]:
        status, payload, _c, extra = self.app.handle_with_headers(
            "GET", path, self.headers(**kw), b""
        )
        return status, payload, extra

    def post(self, path: str, body: dict[str, Any] | None = None, **kw: Any) -> tuple[int, Any]:
        status, payload, _ = self.app.handle(
            "POST", path, self.headers(**kw), json.dumps(body or {}).encode()
        )
        return status, payload

    def scope(self, scope: Any = OPS_UNIT) -> dict[str, str]:
        return {
            "region_id": scope.region_id,
            "org_id": scope.org_id,
            "unit_id": scope.unit_id,
        }


@pytest.fixture
def client(world: World) -> Client:
    return Client(world)


# -- the absent surfaces are observably absent -------------------------------


def test_every_forbidden_surface_is_refused_with_a_reason(client: Client) -> None:
    for path in FORBIDDEN_SURFACES:
        for method in ("GET", "POST"):
            status, payload = client.get(path) if method == "GET" else client.post(path, {})
            assert status == 403, path
            assert payload["error"] == OversightRefusal.EXECUTION_SURFACE_ABSENT.value


def test_a_subpath_of_a_forbidden_surface_is_also_refused(client: Client) -> None:
    status, payload = client.post("/audit/v1/shell/run", {"cmd": "ls"})
    assert status == 403
    assert payload["error"] == OversightRefusal.EXECUTION_SURFACE_ABSENT.value


def test_the_catalogue_declares_the_absences(client: Client) -> None:
    status, payload = client.get("/audit/v1/catalogue")
    assert status == 200
    assert payload["operational_execution_surface"] == "ABSENT"
    assert payload["secret_surface"] == "ABSENT"
    assert set(payload["absent_surfaces"]) == set(FORBIDDEN_SURFACES)
    assert payload["self_state"] == "CANDIDATE_NOT_ACCEPTED"
    assert len(payload["actions"]) == 14
    assert set(payload["export_purposes"]) == set(EXPORT_PURPOSES)


def test_no_route_requests_approves_or_executes_a_ctrl04_action(client: Client) -> None:
    for path in (
        "/audit/v1/actions",
        "/audit/v1/actions/commit",
        "/audit/v1/ops/execute",
        "/audit/v1/remediation/execute",
    ):
        status, payload = client.post(path, {})
        assert status in {403, 404}
        assert payload["error"] in {
            OversightRefusal.NOT_FOUND.value,
            OversightRefusal.EXECUTION_SURFACE_ABSENT.value,
        }


def test_unknown_method_is_refused(client: Client) -> None:
    status, payload, _ = client.app.handle("DELETE", "/audit/v1/cases", client.headers(), b"")
    assert status == 405
    assert payload["error"] == "AUD_METHOD_NOT_ALLOWED"


# -- sessions on every route --------------------------------------------------


def test_every_route_requires_a_usable_session(client: Client, world: World) -> None:
    world.service.revoke_session("sess-auditor")
    for path in ("/audit/v1/me", "/audit/v1/journal"):
        status, payload = client.get(path)
        assert status == 401, path
        assert payload["error"] == OversightRefusal.SESSION_REVOKED.value
    for path in ("/audit/v1/read-model", "/audit/v1/cases", "/audit/v1/exports"):
        status, payload = client.get_scoped(path)
        assert status == 401, path
        assert payload["error"] == OversightRefusal.SESSION_REVOKED.value
    status, payload = client.post("/audit/v1/evidence/search", client.scope())
    assert status == 401


def test_missing_session_header_is_refused(client: Client) -> None:
    status, payload, _ = client.app.handle("GET", "/audit/v1/me", {}, b"")
    assert status == 401
    assert payload["error"] == OversightRefusal.NO_SESSION.value


def test_the_session_header_is_case_insensitive(client: Client) -> None:
    status, _payload, _ = client.app.handle(
        "GET", "/audit/v1/me", {"x-epd2-session": "sess-auditor"}, b""
    )
    assert status == 200


def test_the_catalogue_needs_no_session(client: Client) -> None:
    status, _payload, _ = client.app.handle("GET", "/audit/v1/catalogue", {}, b"")
    assert status == 200


def test_the_ui_is_served_without_data(client: Client) -> None:
    status, payload, content_type = client.app.handle("GET", "/", {}, b"")
    assert status == 200
    assert content_type.startswith("text/html")
    assert payload == CONSOLE_HTML
    assert "sess-auditor" not in payload


# -- the browser is not an authority -----------------------------------------


def test_a_client_supplied_authoritative_field_is_refused(client: Client) -> None:
    for field in sorted(FORBIDDEN_CLIENT_FIELDS):
        status, payload = client.post(
            "/audit/v1/evidence/search", {**client.scope(), field: "forged"}
        )
        assert status == 400, field
        assert payload["error"] == OversightRefusal.BROWSER_STATE_REJECTED.value


def test_a_client_cannot_assert_integrity(client: Client, world: World) -> None:
    ref = world.references()[0]
    status, payload = client.post(
        "/audit/v1/evidence/verify",
        {**client.scope(), "reference_key": ref, "trustworthy": True},
    )
    assert status == 400
    assert payload["error"] == OversightRefusal.BROWSER_STATE_REJECTED.value


def test_integrity_comes_from_the_server(client: Client, world: World) -> None:
    ref = world.references()[0]
    status, payload = client.post(
        "/audit/v1/evidence/verify", {**client.scope(), "reference_key": ref}
    )
    assert status == 200
    assert payload["verified_by"] == "CTRL-05 independent re-derivation"
    assert payload["trustworthy"] is True


def test_me_never_returns_an_operational_capability(client: Client, world: World) -> None:
    dual = Client(world, "dual-hat-operator")
    status, payload = dual.get("/audit/v1/me")
    assert status == 200
    assert payload["may_execute_operations"] is False
    assert payload["universal_auditor"] is False
    text = json.dumps(payload)
    assert "OPS.EXECUTE" not in text


# -- CSRF on mutations, not on reads -----------------------------------------


def test_a_mutation_without_the_csrf_header_is_refused(client: Client, world: World) -> None:
    status, payload = client.post(
        "/audit/v1/cases",
        {
            **client.scope(),
            "title": "no csrf",
            "evidence_refs": world.references()[:1],
            "idempotency_key": "api-nocsrf",
        },
        csrf=None,
    )
    assert status == 403
    assert payload["error"] == OversightRefusal.CSRF_INVALID.value


def test_a_mutation_with_a_wrong_csrf_token_is_refused(client: Client, world: World) -> None:
    status, payload = client.post(
        "/audit/v1/cases",
        {
            **client.scope(),
            "title": "bad csrf",
            "evidence_refs": world.references()[:1],
            "idempotency_key": "api-badcsrf",
        },
        csrf="nope",
    )
    assert status == 403
    assert payload["error"] == OversightRefusal.CSRF_INVALID.value


def test_reads_need_no_csrf_header(client: Client) -> None:
    status, payload = client.post("/audit/v1/evidence/search", client.scope(), csrf=None)
    assert status == 200
    assert payload["matched"] > 0


# -- scope is mandatory and exact --------------------------------------------


def test_a_route_without_an_exact_scope_is_refused(client: Client) -> None:
    status, payload = client.post("/audit/v1/evidence/search", {})
    assert status == 400
    assert payload["error"] == OversightRefusal.PARAMETER_INVALID.value


def test_a_coarse_scope_is_refused(client: Client) -> None:
    status, payload = client.post(
        "/audit/v1/evidence/search",
        {"region_id": "DE-BE", "org_id": "*", "unit_id": "unit-operations-audit"},
    )
    assert status == 400
    assert payload["error"] == OversightRefusal.PARAMETER_INVALID.value


def test_another_units_scope_is_refused(client: Client) -> None:
    status, payload = client.post("/audit/v1/evidence/search", client.scope(PRIVACY_UNIT))
    assert status == 403
    assert payload["error"] == OversightRefusal.WRONG_UNIT_SCOPE.value


# -- the whole governed journey over HTTP ------------------------------------


def test_the_full_review_journey_over_http(client: Client, world: World) -> None:
    search_status, search = client.post(
        "/audit/v1/evidence/search", {**client.scope(), "limit": 50}
    )
    assert search_status == 200
    refs = [r["reference"]["key"] for r in search["records"]]

    status, case = client.post(
        "/audit/v1/cases",
        {
            **client.scope(),
            "title": "restart chain under review",
            "evidence_refs": refs[:3],
            "idempotency_key": "api-open",
        },
    )
    assert status == 201
    case_id = case["case_id"]

    status, ticket = client.post(
        "/audit/v1/prepare",
        {"case_id": case_id, "act": "DISPOSE", "right": "AUDIT.REVIEW"},
    )
    assert status == 200
    status, disposed = client.post(
        "/audit/v1/cases/dispose",
        {
            "ticket_id": ticket["ticket"]["ticket_id"],
            "disposition": ReviewState.FINDING_RAISED.value,
            "rationale": "the authority basis is thin",
            "idempotency_key": "api-disp",
        },
    )
    assert status == 201
    assert disposed["case"]["dispositions"][0]["state"] == ReviewState.FINDING_RAISED.value

    status, ticket = client.post(
        "/audit/v1/prepare",
        {"case_id": case_id, "act": "FINDING", "right": "AUDIT.REVIEW"},
    )
    assert status == 200
    status, finding = client.post(
        "/audit/v1/findings",
        {
            "ticket_id": ticket["ticket"]["ticket_id"],
            "severity": "HIGH",
            "summary": "approval recorded without a class",
            "evidence_ref": refs[0],
            "idempotency_key": "api-find",
        },
    )
    assert status == 201
    finding_id = finding["finding_id"]

    status, dispute = client.post(
        "/audit/v1/findings/dispute",
        {
            "finding_id": finding_id,
            "rationale": "the class is recorded in the CTRL-02 record",
            "idempotency_key": "api-disp2",
        },
    )
    assert status == 201
    assert dispute["original_retained"] is True

    attestor = Client(world, "attestor")
    status, ticket = attestor.post(
        "/audit/v1/prepare",
        {"case_id": case_id, "act": "ATTEST", "right": "AUDIT.ATTEST"},
    )
    assert status == 200
    status, attested = attestor.post(
        "/audit/v1/cases/attest",
        {
            "ticket_id": ticket["ticket"]["ticket_id"],
            "statement": "reviewed under MND-attestor",
            "idempotency_key": "api-att",
        },
    )
    assert status == 201

    status, ticket = client.post(
        "/audit/v1/prepare",
        {"case_id": case_id, "act": "EXPORT", "right": "AUDIT.EXPORT"},
    )
    assert status == 200
    status, export = client.post(
        "/audit/v1/exports",
        {
            "ticket_id": ticket["ticket"]["ticket_id"],
            "purpose": "GOVERNANCE_REPORT",
            "evidence_refs": refs[:2],
            "idempotency_key": "api-exp",
        },
    )
    assert status == 201
    assert export["redaction_decision"]["dropped_fields"]

    status, closed = attestor.post(
        "/audit/v1/cases/close",
        {
            "case_id": case_id,
            "expected_version": attested["case"]["version"],
            "idempotency_key": "api-close",
        },
    )
    assert status == 200
    assert closed["state"] == ReviewState.CLOSED.value
    assert closed["history_is_append_only"] is True


def test_case_read_and_journal_routes(client: Client, world: World) -> None:
    _status, case = client.post(
        "/audit/v1/cases",
        {
            **client.scope(),
            "title": "read routes",
            "evidence_refs": world.references()[:1],
            "idempotency_key": "api-read",
        },
    )
    status, one = client.get_scoped(f"/audit/v1/cases/{case['case_id']}")
    assert status == 200 and one["case_id"] == case["case_id"]
    status, many = client.get_scoped("/audit/v1/cases")
    assert status == 200 and len(many["cases"]) == 1 and many["scope"] == OPS_UNIT.key
    status, journal = client.get("/audit/v1/journal")
    assert status == 200 and journal["append_only"] is True and journal["count"] > 0
    status, model = client.get_scoped("/audit/v1/read-model")
    assert status == 200 and model["schema"] == "epd2.ctrl05.oversight-read-model/1"
    assert model["scope"] == OPS_UNIT.key


def test_unknown_case_is_a_404(client: Client) -> None:
    status, payload = client.get_scoped("/audit/v1/cases/CASE-999999")
    assert status == 404
    assert payload["error"] == OversightRefusal.UNKNOWN_CASE.value


def test_voting_verification_route_is_reference_only(client: Client) -> None:
    status, payload = client.get(
        "/audit/v1/voting-verification"
        "?region_id=DE-BE&org_id=org-berlin&unit_id=unit-operations-audit"
    )
    assert status == 200
    assert payload["voting_internal_access"] == "NONE"
    assert payload["voting_control_path"] == "NONE"


# -- malformed input refuses, never crashes ----------------------------------


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/audit/v1/evidence/search", {"planes": "CTRL-02"}),
        ("/audit/v1/evidence/open", {"reference_key": 42}),
        ("/audit/v1/evidence/verify", {"reference_key": None}),
        ("/audit/v1/correlation/graph", {"anchor": "x", "depth": "deep"}),
        ("/audit/v1/cases", {"title": "x", "evidence_refs": "not-a-list"}),
        ("/audit/v1/cases", {"title": "x", "evidence_refs": [1, 2]}),
        ("/audit/v1/prepare", {"case_id": "CASE-1", "act": "DISPOSE", "right": "AUDIT.NOPE"}),
        ("/audit/v1/cases/dispose", {"ticket_id": "T", "disposition": "NOT_A_STATE"}),
        ("/audit/v1/findings", {"ticket_id": "T", "severity": "APOCALYPTIC"}),
        ("/audit/v1/exports", {"ticket_id": "T", "purpose": "X", "evidence_refs": {}}),
    ],
)
def test_malformed_input_is_a_refusal_not_a_traceback(
    client: Client, path: str, body: dict[str, Any]
) -> None:
    payload = {**client.scope(), **body}
    status, response = client.post(path, payload)
    assert status in {400, 403, 404}, (path, status, response)
    assert response["error"].startswith("AUD_")
    assert "Traceback" not in json.dumps(response)


def test_a_non_object_body_is_refused(client: Client) -> None:
    status, payload, _ = client.app.handle(
        "POST", "/audit/v1/evidence/search", client.headers(), b"[1,2,3]"
    )
    assert status == 400
    assert payload["error"] == OversightRefusal.PARAMETER_INVALID.value


def test_broken_json_is_refused(client: Client) -> None:
    status, payload, _ = client.app.handle(
        "POST", "/audit/v1/evidence/search", client.headers(), b"{not json"
    )
    assert status == 400
    assert payload["error"] == OversightRefusal.PARAMETER_INVALID.value


def test_an_unknown_route_is_a_404(client: Client) -> None:
    for method in ("GET", "POST"):
        status, payload = (
            client.get("/audit/v1/nope") if method == "GET" else client.post("/audit/v1/nope")
        )
        assert status == 404
        assert payload["error"] == OversightRefusal.NOT_FOUND.value


# -- no secret ever leaves the API -------------------------------------------


def test_no_api_response_carries_a_secret(client: Client, world: World) -> None:
    _status, search = client.post("/audit/v1/evidence/search", {**client.scope(), "limit": 50})
    refs = [r["reference"]["key"] for r in search["records"]]
    _status, _case = client.post(
        "/audit/v1/cases",
        {
            **client.scope(),
            "title": "secret sweep",
            "evidence_refs": refs[:2],
            "idempotency_key": "api-secret",
        },
    )
    bodies = [search]
    for path in ("/audit/v1/me", "/audit/v1/journal"):
        _status, payload = client.get(path)
        bodies.append(payload)
    for path in ("/audit/v1/read-model", "/audit/v1/cases", "/audit/v1/exports"):
        _status, payload = client.get_scoped(path)
        bodies.append(payload)
    text = json.dumps(bodies).lower()
    for marker in ("sk_live_", "hunter2", "begin private key", "akia"):
        assert marker not in text
    # No session credential appears in any read body — not another session's
    # token, and not the requesting session's own.
    assert "csrf-attestor" not in text
    assert "csrf-auditor" not in text


def test_the_ui_source_asserts_no_state_of_its_own() -> None:
    """The page may render server values; it may not compute authority or
    integrity, and it must escape everything it renders."""
    assert "esc(" in CONSOLE_HTML
    assert "recomputed_hash" not in CONSOLE_HTML.split("<script>")[1].split("function badge")[0]
    for claim in ("trustworthy=true", "grants.push", "localStorage", "sessionStorage"):
        assert claim not in CONSOLE_HTML


def test_the_ui_declares_the_boundary(client: Client) -> None:
    assert "read-and-review" in CONSOLE_HTML
    assert "NOT_AN_OPERATOR" in CONSOLE_HTML
    assert "visibility is not authorization" in CONSOLE_HTML


def test_clock_is_monotonic_across_the_api(client: Client, world: World) -> None:
    world.now = NOW
    first = client.get("/audit/v1/me")[0]
    second = client.get("/audit/v1/me")[0]
    assert first == second == 200

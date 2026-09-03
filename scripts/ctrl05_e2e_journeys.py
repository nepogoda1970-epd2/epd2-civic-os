#!/usr/bin/env python3
"""CTRL-05 end-to-end journeys J01-J22 over the real HTTP API.

Every journey drives the Audit & Oversight Console through its HTTP transport
against **real evidence**: a real CTRL-02 `RegionalOperationsService`
intervention, a real CTRL-03 `CredentialLifecycleService` key revocation and
real CTRL-04 Operations Console actions, each with its own hash-chained
journal, plus a `JsonFileStore` whose persisted evidence survives a console
restart.

Nothing here is a mock of an evidence plane: the records the oversight console
reads were produced by the accepted CTRL-02/03/04 runtimes installed on
canonical `main`, in this process, by actually performing those governed
operations. The integration class is recorded as
`REAL_INSTALLED_CTRL02_CTRL03_CTRL04_PLANES`.

This script claims no CTRL-05 acceptance, no CTRL-layer closure and no
production readiness.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/control-plane-service/src"))
sys.path.insert(0, str(ROOT / "services/control-plane-service/tests"))
sys.path.insert(0, str(ROOT / "packages/python/epd2-core/src"))
sys.path.insert(0, str(ROOT / "scripts"))

from epd2_control_plane_service.operations_adapters import JsonFileStore  # noqa: E402
from epd2_control_plane_service.operations_console import (  # noqa: E402
    ActionType,
    EvidenceSealer,
)
from epd2_control_plane_service.oversight_api import (  # noqa: E402
    CSRF_HEADER,
    FORBIDDEN_SURFACES,
    SESSION_HEADER,
    OversightApp,
    serve,
)
from epd2_control_plane_service.oversight_console import (  # noqa: E402
    EXPORT_PURPOSES,
    MAX_GRAPH_DEPTH,
    MAX_QUERY_LIMIT,
    OversightConsoleService,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import (  # noqa: E402
    EvidencePlane,
    IntegrityState,
)

from ctrl05_common import runtime_source_digest  # type: ignore[import-not-found]  # noqa: E402

VALIDATION = ROOT / "validation/ctrl05"
SEAL_KEY = b"ctrl05-e2e-evidence-seal-key-0123456789"


class Http:
    def __init__(self, base: str) -> None:
        self.base = base
        self.last_headers: dict[str, str] = {}

    def call(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        session: str | None = None,
        csrf: str | None = None,
    ) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if session:
            headers[SESSION_HEADER] = session
        if csrf:
            headers[CSRF_HEADER] = csrf
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read()
                self.last_headers = dict(response.headers.items())
                content_type = response.headers.get("Content-Type", "")
                if "json" not in content_type:
                    return response.status, raw.decode(errors="replace")
                return response.status, json.loads(raw or b"{}")
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            try:
                return exc.code, json.loads(payload or b"{}")
            except json.JSONDecodeError:
                return exc.code, {"raw": payload.decode(errors="replace")}


class Runner:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(self, journey: str, title: str, ok: bool, observations: dict[str, Any]) -> None:
        self.results.append(
            {
                "journey": journey,
                "title": title,
                "status": "PASS" if ok else "FAIL",
                "observations": observations,
            }
        )
        print(f"{journey} {'PASS' if ok else 'FAIL'} {title}", flush=True)


def scope_body(scope: Any, **extra: Any) -> dict[str, Any]:
    return {
        "region_id": scope.region_id,
        "org_id": scope.org_id,
        "unit_id": scope.unit_id,
        **extra,
    }


def main() -> int:
    from _ctrl05_builders import (  # type: ignore[import-not-found]
        BAVARIA_UNIT,
        OPS_UNIT,
        PRIVACY_UNIT,
        World,
    )

    runner = Runner()
    with tempfile.TemporaryDirectory(prefix="ctrl05-e2e-") as td:
        store_path = Path(td) / "ctrl05.json"
        w = World(store=JsonFileStore(store_path), sealer=EvidenceSealer(SEAL_KEY))
        # A second real CTRL-04 action, so the correlation surface has more
        # than one chain to distinguish.
        second = w.ctrl04_world.request(ActionType.SERVICE_RESTART, "svc-api")
        w.ctrl04_world.approve(second.action_id)
        w.ctrl04_world.commit(second.action_id)
        w.ctrl04_world.resolve(second.action_id)

        app = OversightApp(w.service, clock=lambda: w.tick())
        server = serve(app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        http = Http(f"http://127.0.0.1:{server.server_address[1]}")
        AUD, ATT = "sess-auditor", "sess-attestor"
        CT = "csrf-attestor"
        try:
            # J01 the console and its catalogue declare the boundary
            status, page = http.call("GET", "/")
            cstatus, catalogue = http.call("GET", "/audit/v1/catalogue")
            ok = (
                status == 200
                and isinstance(page, str)
                and "read-and-review" in page
                and cstatus == 200
                and catalogue["operational_execution_surface"] == "ABSENT"
                and catalogue["secret_surface"] == "ABSENT"
                and catalogue["self_state"] == "CANDIDATE_NOT_ACCEPTED"
                and len(catalogue["actions"]) == 14
            )
            runner.record(
                "J01",
                "console served and catalogue declares the absent surfaces",
                ok,
                {
                    "actions": len(catalogue.get("actions", [])),
                    "absent": catalogue.get("absent_surfaces"),
                    "self_state": catalogue.get("self_state"),
                },
            )

            # J02 no session, no oversight
            anon = [
                http.call("GET", p)[0]
                for p in (
                    "/audit/v1/me",
                    "/audit/v1/read-model?region_id=DE-BE&org_id=org-berlin"
                    "&unit_id=unit-operations-audit",
                )
            ]
            revoked = http.call("GET", "/audit/v1/me", session="sess-nobody")
            runner.record(
                "J02",
                "every oversight route requires a usable session",
                all(s == 401 for s in anon) and revoked[0] == 401,
                {"anonymous_statuses": anon, "unknown_session": revoked},
            )

            # J03 the mandate, not the role, is what is visible
            status, me = http.call("GET", "/audit/v1/me", session=AUD)
            csrf_probe = http.last_headers.get(CSRF_HEADER, "")
            ok = (
                status == 200
                and "csrf_token" not in me
                and bool(csrf_probe)
                and me["universal_auditor"] is False
                and me["may_execute_operations"] is False
                and {m["mandate_id"] for m in me["mandates"]} == {"MND-auditor"}
                and sorted(me["mandates"][0]["rights"])
                == ["AUDIT.CORRELATE", "AUDIT.EXPORT", "AUDIT.READ", "AUDIT.REVIEW"]
            )
            runner.record(
                "J03",
                "the mandate and its exact rights are what the principal holds",
                ok,
                {
                    "mandates": [m["mandate_id"] for m in me.get("mandates", [])],
                    "rights": me.get("mandates", [{}])[0].get("rights"),
                    "note": me.get("note"),
                    "csrf_delivered_as_header": bool(csrf_probe),
                    "csrf_in_body": "csrf_token" in me,
                },
            )
            # The CSRF token is a credential: it arrives as a response
            # header on /audit/v1/me and never inside a read body.
            csrf = http.last_headers.get(CSRF_HEADER, "")
            assert "csrf_token" not in me, "a read body must not carry a session token"

            # J04 real evidence from three real planes, all independently verified
            status, search = http.call(
                "POST",
                "/audit/v1/evidence/search",
                scope_body(OPS_UNIT, limit=MAX_QUERY_LIMIT),
                session=AUD,
            )
            planes = {r["reference"]["plane"] for r in search["records"]}
            refs = [r["reference"]["key"] for r in search["records"]]
            ok = (
                status == 200
                and planes
                == {
                    EvidencePlane.CTRL02.value,
                    EvidencePlane.CTRL03.value,
                    EvidencePlane.CTRL04.value,
                }
                and search["integrity_summary"]
                == {IntegrityState.VERIFIED.value: search["matched"]}
                and search["unavailable_planes"] == {}
            )
            runner.record(
                "J04",
                "real CTRL-02/03/04 evidence read and independently verified",
                ok,
                {
                    "planes": sorted(planes),
                    "matched": search.get("matched"),
                    "integrity": search.get("integrity_summary"),
                },
            )

            # J05 one record opened and re-derived
            ctrl04_ref = next(r for r in refs if r.startswith(EvidencePlane.CTRL04.value))
            ostatus, opened = http.call(
                "POST",
                "/audit/v1/evidence/open",
                scope_body(OPS_UNIT, reference_key=ctrl04_ref),
                session=AUD,
            )
            vstatus, verdict = http.call(
                "POST",
                "/audit/v1/evidence/verify",
                scope_body(OPS_UNIT, reference_key=ctrl04_ref),
                session=AUD,
            )
            ok = (
                ostatus == 200
                and vstatus == 200
                and verdict["state"] == IntegrityState.VERIFIED.value
                and verdict["recorded_hash"] == verdict["recomputed_hash"]
                and verdict["verified_by"] == "CTRL-05 independent re-derivation"
                and opened["record"]["reference"]["key"] == ctrl04_ref
            )
            runner.record(
                "J05",
                "a record is opened and its integrity re-derived by CTRL-05 itself",
                ok,
                {
                    "reference": ctrl04_ref,
                    "verdict": verdict.get("state"),
                    "verified_by": verdict.get("verified_by"),
                },
            )

            # J06 the CTRL-04 action chain is reconstructed from real evidence
            status, chain = http.call(
                "POST",
                "/audit/v1/correlation/chain",
                scope_body(OPS_UNIT, correlation_ref=w.ctrl04_correlation),
                session=AUD,
            )
            ok = (
                status == 200
                and len(chain["steps"]) >= 4
                and all(
                    s["integrity"]["state"] == IntegrityState.VERIFIED.value for s in chain["steps"]
                )
            )
            runner.record(
                "J06",
                "request-approval-execution-result chain rebuilt from the CTRL-04 journal",
                ok,
                {"steps": len(chain.get("steps", [])), "correlation": chain.get("correlation_ref")},
            )

            # J07 the correlation graph is bounded and has no person node
            status, graph = http.call(
                "POST",
                "/audit/v1/correlation/graph",
                scope_body(OPS_UNIT, anchor=w.ctrl04_correlation, depth=1),
                session=AUD,
            )
            over, _ = http.call(
                "POST",
                "/audit/v1/correlation/graph",
                scope_body(OPS_UNIT, anchor=w.ctrl04_correlation, depth=MAX_GRAPH_DEPTH + 1),
                session=AUD,
            )
            coarse, coarse_payload = http.call(
                "POST",
                "/audit/v1/correlation/graph",
                scope_body(OPS_UNIT, anchor="*", depth=1),
                session=AUD,
            )
            ok = (
                status == 200
                and graph["person_nodes"] == 0
                and over == 403
                and coarse == 403
                and coarse_payload["error"] == "AUD_UNBOUNDED_QUERY_FORBIDDEN"
            )
            runner.record(
                "J07",
                "correlation is bounded, anchored and carries no person node",
                ok,
                {"nodes": len(graph.get("nodes", [])), "over_depth": over, "coarse": coarse},
            )

            # J08 exact organization scope, no inheritance
            other_org, other_org_payload = http.call(
                "POST",
                "/audit/v1/evidence/search",
                scope_body(OPS_UNIT),
                session="sess-bavaria-auditor",
            )
            own, own_payload = http.call(
                "POST",
                "/audit/v1/evidence/search",
                scope_body(BAVARIA_UNIT),
                session="sess-bavaria-auditor",
            )
            ok = (
                other_org == 403
                and other_org_payload["error"] == "AUD_WRONG_ORGANIZATION_SCOPE"
                and own == 200
                and own_payload["matched"] == 0
            )
            runner.record(
                "J08",
                "another organization is refused and inherits nothing",
                ok,
                {
                    "cross_org": [other_org, other_org_payload.get("error")],
                    "own_scope_matched": own_payload.get("matched"),
                },
            )

            # J09 exact unit scope inside the same organization
            cross_unit, cross_payload = http.call(
                "POST",
                "/audit/v1/evidence/search",
                scope_body(OPS_UNIT),
                session="sess-privacy-officer",
            )
            widen, widen_payload = http.call(
                "POST", "/audit/v1/evidence/search", scope_body(PRIVACY_UNIT), session=AUD
            )
            ok = (
                cross_unit == 403
                and cross_payload["error"] == "AUD_WRONG_UNIT_SCOPE"
                and widen == 403
                and widen_payload["error"] == "AUD_WRONG_UNIT_SCOPE"
            )
            runner.record(
                "J09",
                "a different oversight unit in the same organization reaches nothing",
                ok,
                {
                    "privacy_into_ops": cross_payload.get("error"),
                    "ops_into_privacy": widen_payload.get("error"),
                },
            )

            # J10 a universal capability grants nothing
            uni, uni_payload = http.call(
                "POST",
                "/audit/v1/evidence/search",
                scope_body(OPS_UNIT),
                session="sess-super-admin",
            )
            nomandate, nomandate_payload = http.call(
                "POST", "/audit/v1/evidence/search", scope_body(OPS_UNIT), session="sess-unmandated"
            )
            ok = (
                uni == 403
                and uni_payload["error"] == "AUD_UNIVERSAL_AUDITOR_FORBIDDEN"
                and nomandate == 403
                and nomandate_payload["error"] == "AUD_NO_OVERSIGHT_MANDATE"
            )
            runner.record(
                "J10",
                "no universal auditor and no visibility without a mandate",
                ok,
                {
                    "universal": uni_payload.get("error"),
                    "unmandated": nomandate_payload.get("error"),
                },
            )

            # J11 a case is opened on exact evidence, with CSRF
            nocsrf, nocsrf_payload = http.call(
                "POST",
                "/audit/v1/cases",
                scope_body(
                    OPS_UNIT, title="no csrf", evidence_refs=refs[:1], idempotency_key="j11-nocsrf"
                ),
                session=AUD,
            )
            status, case = http.call(
                "POST",
                "/audit/v1/cases",
                scope_body(
                    OPS_UNIT,
                    title="restart chain under review",
                    evidence_refs=refs[:3],
                    idempotency_key="j11-open",
                ),
                session=AUD,
                csrf=csrf,
            )
            case_id = case.get("case_id", "")
            ok = (
                nocsrf == 403
                and nocsrf_payload["error"] == "AUD_CSRF_TOKEN_INVALID"
                and status == 201
                and case["evidence_refs"] == refs[:3]
                and "MND-auditor" in case["mandate_ref"]
            )
            runner.record(
                "J11",
                "a review case names its exact evidence and requires the session CSRF token",
                ok,
                {
                    "without_csrf": nocsrf_payload.get("error"),
                    "case_id": case_id,
                    "mandate_ref": case.get("mandate_ref"),
                },
            )

            # J12 annotation never touches the source
            ctrl02_head_before = [e.event_hash for e in w.ctrl02._events]
            ctrl04_head_before = w.ctrl04.journal.head_hash()
            status, clarified = http.call(
                "POST",
                "/audit/v1/cases/clarify",
                {
                    "case_id": case_id,
                    "text": "the approval class is recorded in the CTRL-02 record itself",
                    "evidence_ref": refs[0],
                    "idempotency_key": "j12",
                },
                session=AUD,
                csrf=csrf,
            )
            ok = (
                status == 201
                and clarified["source_evidence_mutated"] is False
                and [e.event_hash for e in w.ctrl02._events] == ctrl02_head_before
                and w.ctrl04.journal.head_hash() == ctrl04_head_before
            )
            runner.record(
                "J12",
                "an annotation is a new record; the source planes are byte-identical",
                ok,
                {
                    "source_mutated": clarified.get("source_evidence_mutated"),
                    "ctrl04_head_unchanged": w.ctrl04.journal.head_hash() == ctrl04_head_before,
                },
            )

            # J13 prepare then commit: the disposition
            status, ticket = http.call(
                "POST",
                "/audit/v1/prepare",
                {"case_id": case_id, "act": "DISPOSE", "right": "AUDIT.REVIEW"},
                session=AUD,
                csrf=csrf,
            )
            tid = ticket["ticket"]["ticket_id"]
            dstatus, disposed = http.call(
                "POST",
                "/audit/v1/cases/dispose",
                {
                    "ticket_id": tid,
                    "disposition": ReviewState.FINDING_RAISED.value,
                    "rationale": "the authority basis is recorded but thin",
                    "idempotency_key": "j13",
                },
                session=AUD,
                csrf=csrf,
            )
            replay, replay_payload = http.call(
                "POST",
                "/audit/v1/cases/dispose",
                {
                    "ticket_id": tid,
                    "disposition": ReviewState.NO_FINDING.value,
                    "rationale": "replay",
                    "idempotency_key": "j13-replay",
                },
                session=AUD,
                csrf=csrf,
            )
            ok = (
                status == 200
                and dstatus == 201
                and disposed["case"]["dispositions"][0]["state"] == ReviewState.FINDING_RAISED.value
                and replay == 403
                and replay_payload["error"] == "AUD_REPLAYED_REQUEST"
            )
            runner.record(
                "J13",
                "a disposition is committed under a single-use reauthorization ticket",
                ok,
                {"ticket": tid, "replay": replay_payload.get("error")},
            )

            # J14 a finding bound to an exact, verified reference
            _s, ticket = http.call(
                "POST",
                "/audit/v1/prepare",
                {"case_id": case_id, "act": "FINDING", "right": "AUDIT.REVIEW"},
                session=AUD,
                csrf=csrf,
            )
            status, finding = http.call(
                "POST",
                "/audit/v1/findings",
                {
                    "ticket_id": ticket["ticket"]["ticket_id"],
                    "severity": "HIGH",
                    "summary": "approval recorded without an explicit class",
                    "evidence_ref": refs[0],
                    "idempotency_key": "j14",
                },
                session=AUD,
                csrf=csrf,
            )
            raised = finding["case"]["findings"][0]
            ok = (
                status == 201
                and raised["evidence_reference"]["key"] == refs[0]
                and raised["evidence_content_digest"]
                and raised["severity"] == "HIGH"
            )
            runner.record(
                "J14",
                "a finding names one exact verified evidence record",
                ok,
                {
                    "finding": raised.get("finding_id"),
                    "evidence": raised.get("evidence_reference", {}).get("key"),
                },
            )

            # J15 dispute: the original stands
            status, dispute = http.call(
                "POST",
                "/audit/v1/findings/dispute",
                {
                    "finding_id": raised["finding_id"],
                    "rationale": "the class is in the CTRL-02 record, this is not a defect",
                    "idempotency_key": "j15",
                },
                session=AUD,
                csrf=csrf,
            )
            ids = {f["finding_id"] for f in dispute["case"]["findings"]}
            ok = (
                status == 201
                and dispute["original_retained"] is True
                and {raised["finding_id"], dispute["dispute_finding_id"]} <= ids
                and len(ids) == 2
            )
            runner.record(
                "J15",
                "a disputed finding is retained beside its dispute",
                ok,
                {"findings": sorted(ids), "original_retained": dispute.get("original_retained")},
            )

            # J16 remediation is a reference, never an execution
            journal_before = len(w.ctrl04.journal)
            status, link = http.call(
                "POST",
                "/audit/v1/remediation",
                {
                    "case_id": case_id,
                    "remediation_plane": "CTRL-04",
                    "remediation_ref": w.ctrl04_action_id,
                    "idempotency_key": "j16",
                },
                session=AUD,
                csrf=csrf,
            )
            ok = (
                status == 201
                and link["executed_by_ctrl05"] is False
                and len(w.ctrl04.journal) == journal_before
            )
            runner.record(
                "J16",
                "a remediation link references CTRL-04 without acting on it",
                ok,
                {
                    "executed_by_ctrl05": link.get("executed_by_ctrl05"),
                    "ctrl04_journal_unchanged": len(w.ctrl04.journal) == journal_before,
                },
            )

            # J17 a reviewer cannot attest; an attestor can
            _s, refused_ticket = http.call(
                "POST",
                "/audit/v1/prepare",
                {"case_id": case_id, "act": "ATTEST", "right": "AUDIT.ATTEST"},
                session=AUD,
                csrf=csrf,
            )
            _s, _att_me = http.call("GET", "/audit/v1/me", session=ATT)
            _s, att_ticket = http.call(
                "POST",
                "/audit/v1/prepare",
                {"case_id": case_id, "act": "ATTEST", "right": "AUDIT.ATTEST"},
                session=ATT,
                csrf=CT,
            )
            status, attested = http.call(
                "POST",
                "/audit/v1/cases/attest",
                {
                    "ticket_id": att_ticket["ticket"]["ticket_id"],
                    "statement": "reviewed under MND-attestor against the records named here",
                    "idempotency_key": "j17",
                },
                session=ATT,
                csrf=CT,
            )
            attestation = attested["case"]["attestations"][0]
            ok = (
                refused_ticket.get("error") == "AUD_RIGHT_ABSENT"
                and status == 201
                and attestation["attested_by"] == "attestor"
                and attestation["attested_case_version"] == attested["case"]["version"] - 1
            )
            runner.record(
                "J17",
                "review and attestation are separate rights held by separate principals",
                ok,
                {
                    "reviewer_attempt": refused_ticket.get("error"),
                    "attested_by": attestation.get("attested_by"),
                    "attested_version": attestation.get("attested_case_version"),
                },
            )

            # J18 purpose-bound export with an evidenced redaction
            per_purpose: dict[str, Any] = {}
            for purpose in EXPORT_PURPOSES:
                _s, ticket = http.call(
                    "POST",
                    "/audit/v1/prepare",
                    {"case_id": case_id, "act": "EXPORT", "right": "AUDIT.EXPORT"},
                    session=AUD,
                    csrf=csrf,
                )
                estatus, export = http.call(
                    "POST",
                    "/audit/v1/exports",
                    {
                        "ticket_id": ticket["ticket"]["ticket_id"],
                        "purpose": purpose,
                        "evidence_refs": refs[:2],
                        "idempotency_key": f"j18-{purpose}",
                    },
                    session=AUD,
                    csrf=csrf,
                )
                rows = export["payload"]["records"] if estatus == 201 else []
                per_purpose[purpose] = {
                    "status": estatus,
                    "fields": sorted({k for row in rows for k in row}),
                    "dropped": export.get("redaction_decision", {}).get("dropped_fields"),
                    "decision": export.get("export", {}).get("redaction_decision_id"),
                }
            # An unknown purpose is probed with a *real* prepared ticket, so
            # the refusal is the purpose check and not a missing ticket.
            _s, bad_ticket = http.call(
                "POST",
                "/audit/v1/prepare",
                {"case_id": case_id, "act": "EXPORT", "right": "AUDIT.EXPORT"},
                session=AUD,
                csrf=csrf,
            )
            unknown, unknown_payload = http.call(
                "POST",
                "/audit/v1/exports",
                {
                    "ticket_id": bad_ticket["ticket"]["ticket_id"],
                    "purpose": "ANYTHING",
                    "evidence_refs": refs[:1],
                    "idempotency_key": "j18-bad",
                },
                session=AUD,
                csrf=csrf,
            )
            no_ticket, no_ticket_payload = http.call(
                "POST",
                "/audit/v1/exports",
                {
                    "ticket_id": "TKT-000000",
                    "purpose": "STATISTICAL",
                    "evidence_refs": refs[:1],
                    "idempotency_key": "j18-noticket",
                },
                session=AUD,
                csrf=csrf,
            )
            ok = (
                all(
                    v["status"] == 201 and v["decision"] and set(v["fields"]) <= EXPORT_PURPOSES[p]
                    for p, v in per_purpose.items()
                )
                and unknown == 403
                and unknown_payload.get("error") == "AUD_EXPORT_PURPOSE_UNKNOWN"
                and no_ticket == 404
                and no_ticket_payload.get("error") == "AUD_NOT_FOUND"
            )
            runner.record(
                "J18",
                "every export is purpose-bound and its redaction is recorded as evidence",
                ok,
                {
                    "purposes": per_purpose,
                    "unknown_purpose": unknown_payload.get("error"),
                    "without_a_ticket": no_ticket_payload.get("error"),
                },
            )

            # J19 no secret and no person identifier anywhere on the API
            bodies: list[Any] = [search]
            scope_query = (
                f"?region_id={OPS_UNIT.region_id}&org_id={OPS_UNIT.org_id}"
                f"&unit_id={OPS_UNIT.unit_id}"
            )
            for path in (
                "/audit/v1/me",
                "/audit/v1/journal",
                "/audit/v1/read-model" + scope_query,
                "/audit/v1/cases" + scope_query,
                "/audit/v1/exports" + scope_query,
                f"/audit/v1/cases/{case_id}" + scope_query,
            ):
                bodies.append(http.call("GET", path, session=AUD)[1])
            text = json.dumps(bodies).lower()
            markers = [m for m in ("sk_live_", "hunter2", "begin private key", "akia") if m in text]
            person = [
                m
                for m in ('"member_id"', '"person_id"', '"national_id"', '"date_of_birth"')
                if m in text
            ]
            runner.record(
                "J19",
                "no secret material and no person identifier reaches any oversight route",
                not markers and not person,
                {"secret_markers": markers, "person_fields": person},
            )

            # J20 the absent surfaces are absent, observably
            surfaces = {}
            for path in FORBIDDEN_SURFACES:
                status, payload = http.call("POST", path, {}, session=AUD, csrf=csrf)
                surfaces[path] = [status, payload.get("error")]
            ctrl04_states_before = {a.action_id: a.state.value for a in w.ctrl04.actions()}
            for path in ("/audit/v1/actions", "/audit/v1/ops/execute", "/audit/v1/actions/commit"):
                http.call("POST", path, {"action_id": w.ctrl04_action_id}, session=AUD, csrf=csrf)
            ok = all(
                v[0] == 403 and v[1] == "AUD_EXECUTION_SURFACE_ABSENT" for v in surfaces.values()
            ) and ctrl04_states_before == {a.action_id: a.state.value for a in w.ctrl04.actions()}
            runner.record(
                "J20",
                "no shell, SQL, SSH, secret or CTRL-04 execution surface exists",
                ok,
                {"surfaces": surfaces, "ctrl04_states_unchanged": True},
            )

            # J21 the voting boundary: reference only
            status, voting = http.call(
                "GET",
                "/audit/v1/voting-verification"
                f"?region_id={OPS_UNIT.region_id}&org_id={OPS_UNIT.org_id}"
                f"&unit_id={OPS_UNIT.unit_id}",
                session=AUD,
            )
            envelopes, _u = w.service._all_envelopes()
            voting_envelope = next(e for e in envelopes if e.domain.value == "VOTING")
            blocked, blocked_payload = http.call(
                "POST",
                "/audit/v1/evidence/open",
                scope_body(OPS_UNIT, reference_key=voting_envelope.reference.key),
                session=AUD,
            )
            visible = [r for r in search["records"] if r["domain"] == "VOTING"]
            ok = (
                status == 200
                and voting["voting_internal_access"] == "NONE"
                and voting["voting_control_path"] == "NONE"
                and voting["member_identifiers_exposed"] == 0
                and blocked == 403
                and blocked_payload["error"] == "AUD_VOTING_BOUNDARY"
                and not visible
            )
            runner.record(
                "J21",
                "real voting-domain evidence exists and is refused; only a reference is offered",
                ok,
                {
                    "voting_reference": voting.get("interfaces", [{}])[0].get("interface_id"),
                    "blocked_open": blocked_payload.get("error"),
                    "voting_records_visible": len(visible),
                },
            )

            # J22 restart: the persisted evidence re-verifies and the history stands
            before_case = http.call("GET", f"/audit/v1/cases/{case_id}" + scope_query, session=AUD)[
                1
            ]
            before_head = w.service.journal.head_hash()
            persisted = json.loads(store_path.read_text())
            revived = OversightConsoleService.from_checkpoint(
                persisted,
                authorities=w.authorities,
                sources={
                    EvidencePlane.CTRL02.value: w.ctrl02_source,
                    EvidencePlane.CTRL03.value: w.ctrl03_source,
                    EvidencePlane.CTRL04.value: w.ctrl04_source,
                },
                voting_verification=w.voting,
                sealer=EvidenceSealer(SEAL_KEY),
            )
            after_case = revived.case_view(case_id)
            forged = json.loads(store_path.read_text())
            forged["journal_seal"] = "0" * 64
            try:
                OversightConsoleService.from_checkpoint(
                    forged,
                    authorities=w.authorities,
                    sources={
                        EvidencePlane.CTRL02.value: w.ctrl02_source,
                        EvidencePlane.CTRL03.value: w.ctrl03_source,
                        EvidencePlane.CTRL04.value: w.ctrl04_source,
                    },
                    voting_verification=w.voting,
                    sealer=EvidenceSealer(SEAL_KEY),
                )
                forged_refused = False
            except Exception:
                forged_refused = True
            revived.journal.verify()
            ok = (
                after_case == before_case
                and revived.journal.head_hash() == before_head
                and forged_refused
            )
            runner.record(
                "J22",
                "persisted oversight evidence survives a restart and a forged seal is refused",
                ok,
                {
                    "case_identical": after_case == before_case,
                    "journal_head": revived.journal.head_hash(),
                    "records": len(revived.journal),
                    "forged_seal_refused": forged_refused,
                },
            )
        finally:
            server.shutdown()
            server.server_close()

    passed = sum(r["status"] == "PASS" for r in runner.results)
    payload = {
        "schema": "epd2.ctrl05.e2e-journeys/1",
        "stage": "CTRL-05",
        "transport": "real HTTP (ThreadingHTTPServer) over loopback",
        "integration_class": "REAL_INSTALLED_CTRL02_CTRL03_CTRL04_PLANES",
        "evidence_planes": {
            "CTRL-02": (
                "RegionalOperationsService: a real intervention requested, approved twice and "
                "activated; its own hash-chained AuditEvent sequence is what CTRL-05 reads"
            ),
            "CTRL-03": (
                "CredentialLifecycleService: a real JWS signing key revoked under security and "
                "trust-custodian approval; its own LifecycleAuditEvent chain is read"
            ),
            "CTRL-04": (
                "OperationsConsoleService: real service-restart actions through "
                "request/approve/commit/resolve, plus a real refusal on a voting-domain target; "
                "its EvidenceJournal is read and re-derived"
            ),
            "store": "JsonFileStore — persisted checkpoint reloaded and re-verified in J22",
        },
        "non_claim": (
            "This evidence shows the governed oversight semantics over the real installed "
            "CTRL-02/03/04 planes. It is not a CTRL-05 acceptance, not a CTRL-layer closure, "
            "not a production-readiness statement and not a security certification."
        ),
        "runtime_source_digest": runtime_source_digest(),
        "executed_at": datetime.now(UTC).isoformat(),
        "journeys_total": 22,
        "journeys_passed": passed,
        "journeys": runner.results,
        "self_state": "CANDIDATE_NOT_ACCEPTED",
    }
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / "e2e_journeys_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(f"CTRL05_E2E:{passed}/22_PASS")
    return 0 if passed == 22 else 1


if __name__ == "__main__":
    _ = timedelta
    sys.exit(main())

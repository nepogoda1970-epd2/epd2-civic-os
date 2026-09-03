#!/usr/bin/env python3
"""CTRL-04 browser journeys: the embedded console UI driven by a real browser.

Requires Playwright with a Chromium build (`python -m playwright install chromium`).
When Playwright is unavailable the script exits 3 and writes an explicit
NOT_EXECUTED result rather than a simulated pass.

Verified in the browser:

* B01 read-only operator sees visibility but no executable controls, with the
  reason shown; production-like and health badges are rendered;
* B02 a requester can request a MEDIUM action; the HIGH/DESTRUCTIVE request
  path forces the explicit confirmation dialog and a mismatched phrase is not
  sent;
* B03 the approval and commit controls appear only for principals holding the
  right, the approver cannot commit, and the result state is rendered from the
  server's derived result (never from the page);
* B04 evidence lookup by action id renders the governed record; a forged
  client field is refused by the API with the reason visible in the log.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/control-plane-service/src"))
sys.path.insert(0, str(ROOT / "packages/python/epd2-core/src"))
sys.path.insert(0, str(ROOT / "scripts"))

VALIDATION = ROOT / "validation/ctrl04"


def write(payload: dict[str, object]) -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / "browser_journeys_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        write(
            {
                "schema": "epd2.ctrl04.browser-journeys/1",
                "status": "NOT_EXECUTED",
                "reason": "playwright not importable in this interpreter",
                "self_state": "CANDIDATE_NOT_ACCEPTED",
            }
        )
        print("CTRL04_BROWSER:NOT_EXECUTED")
        return 3

    from epd2_control_plane_service.operations_api import ConsoleApp, serve

    from ctrl04_common import runtime_source_digest  # type: ignore[import-not-found]
    from ctrl04_e2e_journeys import ART_B, build_world  # type: ignore[import-not-found]

    results: list[dict[str, object]] = []

    def record(journey: str, title: str, ok: bool, observations: dict[str, object]) -> None:
        results.append(
            {
                "journey": journey,
                "title": title,
                "status": "PASS" if ok else "FAIL",
                "observations": observations,
            }
        )
        print(f"{journey} {'PASS' if ok else 'FAIL'} {title}", flush=True)

    with tempfile.TemporaryDirectory(prefix="ctrl04-browser-") as td:
        service, adapters, _store, _authorities = build_world(Path(td))
        app = ConsoleApp(service)
        server = serve(app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        shots = VALIDATION / "browser"
        shots.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                # bypass_csp lets the harness evaluate its own wait predicates; the
                # served CSP itself is verified separately by the HTTP tests.
                context = browser.new_context(
                    viewport={"width": 1400, "height": 900}, bypass_csp=True
                )
                # B01 read-only operator
                page = context.new_page()
                page.goto(f"{base}/?session=sess-readonly-operator")
                page.wait_for_selector("#targets tbody tr")
                page.wait_for_function("document.querySelector('#f-why').innerText.length > 0")
                header = page.inner_text("#who")
                submit_disabled = page.is_disabled("#f-submit")
                why = page.inner_text("#f-why")
                prod_badges = page.locator("#targets .badge.PRODUCTION_LIKE").count()
                health_badges = (
                    page.locator("#targets .badge.HEALTHY").count()
                    + page.locator("#targets .badge.DEGRADED").count()
                    + page.locator("#targets .badge.UNAVAILABLE").count()
                )
                voting_listed = "svc-voting-tally" in page.inner_text("#targets")
                page.screenshot(path=str(shots / "B01_read_only.png"), full_page=True)
                ok = (
                    "READ_ONLY" in header
                    and submit_disabled
                    and "read-only" in why
                    and prod_badges >= 5
                    and health_badges >= 5
                    and not voting_listed
                )
                record(
                    "B01",
                    "read-only visibility without executable controls",
                    ok,
                    {
                        "header": header,
                        "submit_disabled": submit_disabled,
                        "why": why,
                        "production_badges": prod_badges,
                        "health_badges": health_badges,
                        "voting_listed": voting_listed,
                    },
                )
                page.close()

                # B02 requester: MEDIUM request, then HIGH path with confirmation dialog
                page = context.new_page()
                page.goto(f"{base}/?session=sess-requester")
                page.wait_for_selector("#targets tbody tr")
                page.select_option("#f-action", "OPS.SERVICE.RESTART")
                page.select_option("#f-target", "svc-ref")
                page.fill("#f-reason", "browser restart")
                page.fill("#f-idem", "b02-restart")
                page.click("#f-submit")
                page.wait_for_selector("#actions tbody tr")
                row = page.inner_text("#actions tbody tr")
                medium_ok = "AWAITING_APPROVAL" in row and "OPS.SERVICE.RESTART" in row
                page.select_option("#f-action", "OPS.DEPLOYMENT.ROLLBACK")
                page.fill("#f-extra", f"target_artifact_digest={ART_B}")
                page.fill("#f-idem", "b02-rollback")
                page.click("#f-submit")
                page.wait_for_selector("dialog#confirm[open]")
                dialog_text = page.inner_text("#c-text")
                page.fill("#c-phrase", "wrong phrase")
                page.click("#c-ok")
                page.wait_for_timeout(300)
                log_after_wrong = page.inner_text("#log")
                rows_after_wrong = page.locator("#actions tbody tr").count()
                page.click("#f-submit")
                page.wait_for_selector("dialog#confirm[open]")
                page.fill("#c-phrase", "CONFIRM-DESTRUCTIVE:svc-ref")
                page.click("#c-ok")
                page.wait_for_function("document.querySelectorAll('#actions tbody tr').length >= 2")
                rollback_row = page.inner_text("#actions tbody tr:nth-child(2)")
                page.screenshot(
                    path=str(shots / "B02_request_and_confirmation.png"), full_page=True
                )
                ok = (
                    medium_ok
                    and "HIGH" in dialog_text
                    and "mismatch" in log_after_wrong
                    and rows_after_wrong == 1
                    and "OPS.DEPLOYMENT.ROLLBACK" in rollback_row
                    and "need INCIDENT_COMMANDER+SECURITY" in rollback_row
                )
                record(
                    "B02",
                    "request with explicit confirmation for high-impact actions",
                    ok,
                    {
                        "medium_row": row[:120],
                        "dialog": dialog_text[:160],
                        "wrong_phrase_not_sent": "mismatch" in log_after_wrong
                        and rows_after_wrong == 1,
                        "rollback_row": rollback_row[:160],
                    },
                )
                page.close()

                # B03 approver sees approve, cannot commit; executor commits; result derived
                page = context.new_page()
                page.goto(f"{base}/?session=sess-incident-commander")
                page.wait_for_selector("#actions tbody tr")
                approve_buttons = page.locator("button[data-act=approve]").count()
                commit_buttons_for_approver = page.locator("button[data-act=commit]").count()
                page.once("dialog", lambda d: d.accept("INCIDENT_COMMANDER"))
                page.click("#actions tbody tr:nth-child(1) button[data-act=approve]")
                page.wait_for_function(
                    "document.querySelector('#actions tbody tr').innerText.includes('APPROVED')"
                )
                after_approve = page.inner_text("#actions tbody tr:nth-child(1)")
                commit_after = page.locator(
                    "#actions tbody tr:nth-child(1) button[data-act=commit]"
                ).count()
                page.close()
                page = context.new_page()
                page.goto(f"{base}/?session=sess-executor")
                page.wait_for_selector("#actions tbody tr")
                exec_commit = page.locator(
                    "#actions tbody tr:nth-child(1) button[data-act=commit]"
                ).count()
                page.click("#actions tbody tr:nth-child(1) button[data-act=commit]")
                page.wait_for_function(
                    "document.querySelector('#actions tbody tr').innerText.includes('EXECUTING')"
                )
                executing_row = page.inner_text("#actions tbody tr:nth-child(1)")
                page.click("#actions tbody tr:nth-child(1) button[data-act=resolve]")
                page.wait_for_function(
                    "document.querySelector('#actions tbody tr').innerText.includes('SUCCEEDED')"
                )
                final_row = page.inner_text("#actions tbody tr:nth-child(1)")
                page.screenshot(path=str(shots / "B03_lifecycle.png"), full_page=True)
                ok = (
                    approve_buttons >= 1
                    and commit_buttons_for_approver == 0
                    and "APPROVED" in after_approve
                    and commit_after == 0
                    and exec_commit == 1
                    and "EXECUTING" in executing_row
                    and "PENDING" in executing_row
                    and "SUCCEEDED" in final_row
                    and "COMPLETED by executor" in final_row
                )
                record(
                    "B03",
                    "approval and commit rights separated; result derived server-side",
                    ok,
                    {
                        "approver_sees_commit": commit_buttons_for_approver,
                        "executing_row": executing_row[:160],
                        "final_row": final_row[:200],
                    },
                )

                # B04 evidence lookup and forged client field
                action_id = final_row.split()[0]
                page.fill("#e-id", action_id)
                page.click("#e-go")
                page.wait_for_function(
                    "document.querySelector('#e-out').innerText.includes('epd2.ctrl04.evidence.v1')"
                )
                evidence_text = page.inner_text("#e-out")
                forged = page.evaluate(
                    "async () => { const r = await fetch('/ops/v1/actions', {method:'POST', "
                    "headers:{'Content-Type':'application/json','X-EPD2-Session':'sess-executor'}, "
                    "body: JSON.stringify({action_type:'OPS.SERVICE.RESTART', target_id:'svc-ref', "
                    "parameters:{reason:'x'}, idempotency_key:'forge', "
                    "approval_state:'GRANTED'})}); "
                    "return [r.status, await r.json()]; }"
                )
                page.screenshot(path=str(shots / "B04_evidence.png"), full_page=True)
                ok = (
                    '"actor_ref": "requester"' in evidence_text
                    and '"result_state": "SUCCEEDED"' in evidence_text
                    and forged[0] == 400
                    and forged[1]["error"] == "OPS_BROWSER_STATE_NOT_AUTHORITATIVE"
                )
                record(
                    "B04",
                    "evidence lookup and refusal of client-supplied authoritative state",
                    ok,
                    {"action_id": action_id, "forged": forged},
                )
                page.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            adapters["local-process"].stop_all()
    passed = sum(r["status"] == "PASS" for r in results)
    write(
        {
            "schema": "epd2.ctrl04.browser-journeys/1",
            "status": "PASS" if passed == 4 else "FAIL",
            "browser": "chromium (playwright)",
            "executed_at": datetime.now(UTC).isoformat(),
            "runtime_source_digest": runtime_source_digest(),
            "journeys_total": 4,
            "journeys_passed": passed,
            "journeys": results,
            "screenshots": sorted(p.name for p in (VALIDATION / "browser").glob("*.png")),
            "self_state": "CANDIDATE_NOT_ACCEPTED",
        }
    )
    print(f"CTRL04_BROWSER:{passed}/4_PASS")
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    _ = timedelta  # keep datetime helpers available for extension
    sys.exit(main())

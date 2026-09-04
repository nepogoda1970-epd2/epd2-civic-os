#!/usr/bin/env python3
"""CTRL-05 browser journeys: the embedded oversight console in a real browser.

Requires Playwright with a Chromium build. When Playwright is unavailable the
script exits 3 and writes an explicit NOT_EXECUTED result rather than a
simulated pass.

Verified in the browser:

* B01 a mandated reviewer sees evidence from the three real planes with the
  server's integrity verdicts rendered, and the page states the boundary;
* B02 a principal with no mandate sees nothing and is told why; the reason is
  the server's, not the page's;
* B03 the governed act is two-phase in the UI: nothing can be committed
  before a ticket is prepared, and the ticket is single-use;
* B04 an export renders its purpose-bound redaction, and a client-forged
  authoritative field is refused by the API with the reason visible in the log;
* B05 the page offers no operational control at all, and driving the CTRL-04
  routes from inside the page leaves the CTRL-04 plane unchanged.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/control-plane-service/src"))
sys.path.insert(0, str(ROOT / "services/control-plane-service/tests"))
sys.path.insert(0, str(ROOT / "packages/python/epd2-core/src"))
sys.path.insert(0, str(ROOT / "scripts"))

VALIDATION = ROOT / "validation/ctrl05"
JOURNEY_TOTAL = 5


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
                "schema": "epd2.ctrl05.browser-journeys/1",
                "status": "NOT_EXECUTED",
                "reason": "playwright not importable in this interpreter",
                "self_state": "CANDIDATE_NOT_ACCEPTED",
            }
        )
        print("CTRL05_BROWSER:NOT_EXECUTED")
        return 3

    from _ctrl05_builders import OPS_UNIT, World  # type: ignore[import-not-found]
    from epd2_control_plane_service.operations_adapters import JsonFileStore
    from epd2_control_plane_service.operations_console import EvidenceSealer
    from epd2_control_plane_service.oversight_api import OversightApp, serve

    from ctrl05_common import runtime_source_digest  # type: ignore[import-not-found]

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

    with tempfile.TemporaryDirectory(prefix="ctrl05-browser-") as td:
        w = World(
            store=JsonFileStore(Path(td) / "ctrl05.json"),
            sealer=EvidenceSealer(b"ctrl05-browser-seal-key-0123456789"),
        )
        app = OversightApp(w.service, clock=lambda: w.tick())
        server = serve(app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        shots = VALIDATION / "browser"
        shots.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as pw:
                # The environment pre-provisions Chromium; a pinned build
                # directory is used verbatim rather than downloading one.
                candidates = sorted(
                    Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")).glob(
                        "chromium-*/chrome-linux/chrome"
                    )
                )
                launch: dict[str, object] = {}
                if candidates and not Path(pw.chromium.executable_path).exists():
                    launch["executable_path"] = str(candidates[-1])
                browser = pw.chromium.launch(**launch)
                # bypass_csp lets the harness evaluate its own wait predicates;
                # the served CSP itself is verified separately by the HTTP tests.
                context = browser.new_context(
                    viewport={"width": 1500, "height": 1000}, bypass_csp=True
                )

                # -- B01 a mandated reviewer sees the three real planes -------
                page = context.new_page()
                page.goto(f"{base}/?session=sess-auditor")
                page.wait_for_function("document.getElementById('boundary').innerText.length > 0")
                boundary = page.inner_text("#boundary")
                header = page.inner_text("#who")
                page.fill("#q-region", OPS_UNIT.region_id)
                page.fill("#q-org", OPS_UNIT.org_id)
                page.fill("#q-unit", OPS_UNIT.unit_id)
                page.fill("#q-limit", "200")
                page.click("#q-go")
                page.wait_for_selector("#records tbody tr")
                page.wait_for_function(
                    "document.querySelectorAll('#records tbody tr').length >= 10"
                )
                rows = page.inner_text("#records")
                summary = page.inner_text("#q-summary")
                verified = page.locator("#records .badge.VERIFIED").count()
                planes = {
                    p
                    for p in ("CTRL-02", "CTRL-03", "CTRL-04")
                    if page.locator(f"#records .badge:text-is('{p}')").count() > 0
                }
                page.screenshot(path=str(shots / "B01_evidence.png"), full_page=True)
                ok = (
                    "read-and-review" in boundary
                    and "ABSENT" in boundary
                    and "MANDATED" in header
                    and "NOT_AN_OPERATOR" in header
                    and planes == {"CTRL-02", "CTRL-03", "CTRL-04"}
                    and verified >= 10
                    and "VOTING" not in rows
                    and "integrity" in summary
                )
                record(
                    "B01",
                    "a mandated reviewer sees the three real planes with server integrity verdicts",
                    ok,
                    {
                        "boundary": boundary[:200],
                        "header": header,
                        "planes_rendered": sorted(planes),
                        "verified_badges": verified,
                        "summary": summary[:200],
                    },
                )
                first_ref = page.inner_text("#records tbody tr:nth-child(1) td:nth-child(1)")
                page.close()

                # -- B02 no mandate, nothing visible, and the reason is given -
                page = context.new_page()
                page.goto(f"{base}/?session=sess-unmandated")
                page.wait_for_function("document.getElementById('q-why').innerText.length > 0")
                why = page.inner_text("#q-why")
                header_nm = page.inner_text("#who")
                search_disabled = page.is_disabled("#q-go")
                case_disabled = page.is_disabled("#c-open")
                page.screenshot(path=str(shots / "B02_no_mandate.png"), full_page=True)
                ok = (
                    "no oversight mandate" in why
                    and "NO_MANDATE" in header_nm
                    and search_disabled
                    and case_disabled
                )
                record(
                    "B02",
                    "without a mandate nothing is visible and the reason is shown",
                    ok,
                    {
                        "why": why,
                        "header": header_nm,
                        "search_disabled": search_disabled,
                        "case_disabled": case_disabled,
                    },
                )
                page.close()

                # -- B03 two-phase governed act ------------------------------
                page = context.new_page()
                page.goto(f"{base}/?session=sess-auditor")
                page.wait_for_function("document.getElementById('q-go').disabled === false")
                page.fill("#q-limit", "200")
                page.click("#q-go")
                page.wait_for_selector("#records tbody tr")
                page.click("#records tbody tr:nth-child(1) button[data-act=pick]")
                page.click("#records tbody tr:nth-child(2) button[data-act=pick]")
                page.fill("#c-title", "browser-driven review")
                page.fill("#c-idem", "b03-open")
                page.click("#c-open")
                page.wait_for_selector("#cases tbody tr")
                commit_disabled_before = page.is_disabled("#p-commit")
                page.select_option("#p-act", "DISPOSE")
                page.click("#p-prep")
                page.wait_for_function(
                    "document.getElementById('p-ticket').innerText.startsWith('ticket ')"
                )
                ticket_text = page.inner_text("#p-ticket")
                commit_enabled = not page.is_disabled("#p-commit")
                page.select_option("#p-disp", "FINDING_RAISED")
                page.fill("#p-text", "the authority basis is thin")
                page.fill("#p-idem", "b03-disp")
                page.click("#p-commit")
                page.wait_for_function(
                    "document.getElementById('p-ticket').innerText === 'ticket consumed'"
                )
                consumed_disabled = page.is_disabled("#p-commit")
                case_row = page.inner_text("#cases tbody tr")
                page.screenshot(path=str(shots / "B03_two_phase.png"), full_page=True)
                ok = (
                    commit_disabled_before
                    and ticket_text.startswith("ticket TKT-")
                    and commit_enabled
                    and consumed_disabled
                    and "FINDING_RAISED" in case_row
                )
                record(
                    "B03",
                    "a governed act is prepared then committed, and the ticket is single-use",
                    ok,
                    {
                        "commit_disabled_before_prepare": commit_disabled_before,
                        "ticket": ticket_text[:80],
                        "commit_enabled_after_prepare": commit_enabled,
                        "commit_disabled_after_use": consumed_disabled,
                        "case_row": case_row[:200],
                    },
                )

                # -- B04 export redaction and a forged authoritative field ---
                page.select_option("#p-act", "EXPORT")
                page.click("#p-prep")
                page.wait_for_function(
                    "document.getElementById('p-ticket').innerText.startsWith('ticket ')"
                )
                page.select_option("#p-purpose", "STATISTICAL")
                page.fill("#p-text", first_ref)
                page.fill("#p-idem", "b04-exp")
                page.click("#p-commit")
                page.wait_for_function(
                    "document.getElementById('log').innerText.includes('/audit/v1/exports')"
                )
                log_text = page.inner_text("#log")
                exports = page.evaluate(
                    "async () => { const r = await fetch('/audit/v1/exports"
                    "?region_id=DE-BE&org_id=org-berlin&unit_id=unit-operations-audit', "
                    "{headers:{'X-EPD2-Session':'sess-auditor'}}); return await r.json(); }"
                )
                forged = page.evaluate(
                    "async () => { const r = await fetch('/audit/v1/evidence/search', "
                    "{method:'POST', headers:{'Content-Type':'application/json',"
                    "'X-EPD2-Session':'sess-auditor'}, body: JSON.stringify("
                    "{region_id:'DE-BE', org_id:'org-berlin', "
                    "unit_id:'unit-operations-audit', trustworthy:true})}); "
                    "return [r.status, await r.json()]; }"
                )
                page.screenshot(path=str(shots / "B04_export_and_forgery.png"), full_page=True)
                exported = exports.get("exports", [])
                ok = (
                    "/audit/v1/exports" in log_text
                    and len(exported) == 1
                    and exported[0]["purpose"] == "STATISTICAL"
                    and exported[0]["redaction_decision_id"]
                    and exported[0]["payload_digest"]
                    and forged[0] == 400
                    and forged[1]["error"] == "AUD_BROWSER_STATE_NOT_AUTHORITATIVE"
                )
                record(
                    "B04",
                    "an export shows its purpose-bound redaction; a forged client field is refused",
                    ok,
                    {"forged": forged, "exports": exported, "log_excerpt": log_text[:240]},
                )

                # -- B05 no operational control from the page ----------------
                before = (
                    len(w.ctrl04.journal),
                    w.ctrl04.journal.head_hash(),
                    {a.action_id: a.state.value for a in w.ctrl04.actions()},
                )
                # "Commit act" is the *oversight* two-phase commit, verified in
                # B03. What must not exist is a control that acts on a CTRL-04
                # target: an approval, an execution, a restart, a rollback, a
                # dispatch or a result resolution.
                operational_controls = page.evaluate(
                    "() => Array.from(document.querySelectorAll('button')).map("
                    "b => b.innerText.toLowerCase()).filter(t => "
                    "['approve','execute','restart','rollback','dispatch','resolve',"
                    "'maintenance','backup','restore'].some(k => t.includes(k))).length"
                )
                operational_labels = page.evaluate(
                    "() => Array.from(document.querySelectorAll('button')).map("
                    "b => b.innerText.trim())"
                )
                attempts = page.evaluate(
                    "async () => { const out = []; "
                    "for (const p of ['/audit/v1/shell','/audit/v1/sql','/audit/v1/secrets',"
                    "'/audit/v1/operations','/audit/v1/actions/execute']) { "
                    "const r = await fetch(p, {method:'POST', headers:{"
                    "'Content-Type':'application/json','X-EPD2-Session':'sess-auditor'}, "
                    "body:'{}'}); out.push([p, r.status, (await r.json()).error]); } "
                    "return out; }"
                )
                after = (
                    len(w.ctrl04.journal),
                    w.ctrl04.journal.head_hash(),
                    {a.action_id: a.state.value for a in w.ctrl04.actions()},
                )
                page.screenshot(path=str(shots / "B05_no_operations.png"), full_page=True)
                ok = (
                    operational_controls == 0
                    and all(
                        row[1] == 403 and row[2] == "AUD_EXECUTION_SURFACE_ABSENT"
                        for row in attempts
                    )
                    and before == after
                )
                record(
                    "B05",
                    "the page offers no operational control and CTRL-04 is untouched",
                    ok,
                    {
                        "operational_buttons": operational_controls,
                        "button_labels": operational_labels,
                        "attempts": attempts,
                        "ctrl04_unchanged": before == after,
                    },
                )
                page.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()

    passed = sum(r["status"] == "PASS" for r in results)
    write(
        {
            "schema": "epd2.ctrl05.browser-journeys/1",
            "status": "PASS" if passed == JOURNEY_TOTAL else "FAIL",
            "browser": "chromium (playwright)",
            "executed_at": datetime.now(UTC).isoformat(),
            "runtime_source_digest": runtime_source_digest(),
            "journeys_total": JOURNEY_TOTAL,
            "journeys_passed": passed,
            "journeys": results,
            "screenshots": sorted(p.name for p in (VALIDATION / "browser").glob("*.png")),
            "self_state": "CANDIDATE_NOT_ACCEPTED",
        }
    )
    print(f"CTRL05_BROWSER:{passed}/{JOURNEY_TOTAL}_PASS")
    return 0 if passed == JOURNEY_TOTAL else 1


if __name__ == "__main__":
    sys.exit(main())

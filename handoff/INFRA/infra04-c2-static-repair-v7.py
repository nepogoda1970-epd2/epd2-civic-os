from pathlib import Path

p = Path('scripts/infra04/build_changed_manifest.py')
s = p.read_text()
needle = '"note": "Exact current-byte install delta against canonical main after runtime evidence generation. This self-describing manifest and governed package additions SHA256SUMS.txt / ACCEPTANCE/FREEZE-INVENTORY.json are intentionally excluded from the recursive file list.",'
repl = '''"note": (\n            "Exact current-byte install delta against canonical main after runtime evidence "\n            "generation. This self-describing manifest and governed package additions "\n            "SHA256SUMS.txt / ACCEPTANCE/FREEZE-INVENTORY.json are intentionally excluded "\n            "from the recursive file list."\n        ),'''
if needle not in s:
    raise SystemExit('manifest note anchor missing')
p.write_text(s.replace(needle, repl, 1))

p = Path('scripts/ctrl05_validator.py')
lines = p.read_text().splitlines(True)
for n in {364, 379, 431, 821, 906, 931, 954, 990, 1033, 1086, 1173}:
    lines[n - 1] = lines[n - 1].replace('  # type: ignore[import-not-found]', '').replace('  # type: ignore[attr-defined]', '')
s = ''.join(lines)
old = '''    coarse = [\n        refusal(\n            lambda anchor=anchor: w.service.action_chain(\n                actor_ref="auditor",\n                session_id="sess-auditor",\n                scope=OPS_UNIT,\n                correlation_ref=anchor,\n                now=w.tick(),\n            )\n        )\n        for anchor in ("", "*", "ALL", "GLOBAL")\n    ]\n'''
new = '''    coarse = []\n    for anchor in ("", "*", "ALL", "GLOBAL"):\n        def action(anchor: str = anchor) -> Any:\n            return w.service.action_chain(\n                actor_ref="auditor",\n                session_id="sess-auditor",\n                scope=OPS_UNIT,\n                correlation_ref=anchor,\n                now=w.tick(),\n            )\n\n        coarse.append(refusal(action))\n'''
if old not in s:
    raise SystemExit('g28 anchor missing')
s = s.replace(old, new, 1)
old = '''    observed = {}\n    for label, mutate in (\n        ("grant_withdrawn", lambda w: w.authorities._grants.pop("ag-rev")),\n        ("mandate_superseded", lambda w: w.service.supersede_mandate("MND-auditor", "MND-next")),\n        ("session_revoked", lambda w: w.service.revoke_session("sess-auditor")),\n    ):\n'''
new = '''    observed = {}\n\n    def grant_withdrawn(w: Any) -> Any:\n        return w.authorities._grants.pop("ag-rev")\n\n    def mandate_superseded(w: Any) -> Any:\n        return w.service.supersede_mandate("MND-auditor", "MND-next")\n\n    def session_revoked(w: Any) -> Any:\n        return w.service.revoke_session("sess-auditor")\n\n    for label, mutate in (\n        ("grant_withdrawn", grant_withdrawn),\n        ("mandate_superseded", mandate_superseded),\n        ("session_revoked", session_revoked),\n    ):\n'''
if old not in s:
    raise SystemExit('g45 anchor missing')
s = s.replace(old, new, 1)
old = '''        observed[label] = refusal(\n            lambda w=w, ticket=ticket: w.service.dispose(\n                actor_ref="auditor",\n                session_id="sess-auditor",\n                csrf_token="csrf-auditor",\n                ticket_id=ticket["ticket_id"],\n                disposition=ReviewState.NO_FINDING,\n                rationale="after the change",\n                idempotency_key="g45",\n                now=w.tick(),\n            )\n        )\n'''
new = '''        def dispose_after_change(w: Any = w, ticket: Any = ticket) -> Any:\n            return w.service.dispose(\n                actor_ref="auditor",\n                session_id="sess-auditor",\n                csrf_token="csrf-auditor",\n                ticket_id=ticket["ticket_id"],\n                disposition=ReviewState.NO_FINDING,\n                rationale="after the change",\n                idempotency_key="g45",\n                now=w.tick(),\n            )\n\n        observed[label] = refusal(dispose_after_change)\n'''
if old not in s:
    raise SystemExit('g45 disposal anchor missing')
s = s.replace(old, new, 1)
old = '''    observed = {}\n    for label, act in (\n        ("no_mandate_search", lambda: w.search(principal="unmandated")),\n'''
new = '''    observed: dict[str, dict[str, Any]] = {}\n    for label, act in (\n        ("no_mandate_search", lambda: w.search(principal="unmandated")),\n'''
if old not in s:
    raise SystemExit('g50 anchor missing')
p.write_text(s.replace(old, new, 1))

p = Path('scripts/ctrl05_browser_journeys.py')
s = p.read_text()
p.write_text(s.replace('browser = pw.chromium.launch(**launch)  # type: ignore[arg-type]', 'browser = pw.chromium.launch(**launch)'))

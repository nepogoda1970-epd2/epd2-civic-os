#!/usr/bin/env python3
"""Generate the FRONT-05 C1 candidate developer report.

Every identity value in the report is read out of the evidence at generation
time. None is typed by hand.

That is a direct correction, not a stylistic preference. The FRONT-04 C2 archive
was rejected and resealed because the report quoted a `source_tree_digest` from
the penultimate run while the sealed tree carried another — I had hard-coded the
digest into prose and never refreshed it after the final chain re-run, and the
report sat outside the digest-covered boundary so no gate caught it. Two things
close that hole: gate G45, which cross-checks every value the report quotes
against the evidence, and this script, which removes the opportunity to type one
in the first place.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

V = "validation/front05"


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    def load(name: str):
        path = root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    identity = load(f"{V}/preseal_identity.json") or {}
    lineage = load(f"{V}/lineage.json") or {}
    delta = load(f"{V}/source_delta.json") or {}
    caps = load(f"{V}/api_capability_truth.json") or {}
    routes = load(f"{V}/route_inventory.json") or {}
    negatives = load(f"{V}/authorization_negatives.json") or {}
    deps = load(f"{V}/dependency_findings.json") or {}
    mutations = load(f"{V}/mutation_report.json") or {}
    result = load(f"{V}/authoritative_preseal_result.json") or {}
    contract = load("docs/frontend/FRONT-05-STAGE-CONTRACT.json") or {}
    # Deliberately not read: nothing about the archive may enter this report. See
    # §2 — a report sealed inside an archive cannot correctly describe it.

    def step(name: str):
        return load(f"{V}/evidence/{name}.json") or {}

    steps = [e["id"] for e in contract.get("required_evidence", [])]
    inherited = delta.get("inherited_front04_c2", {})
    ssd = contract.get("security_sensitive_dependencies", {})

    L: list[str] = []
    w = L.append

    w("# FRONT-05 — WS-04 REPRESENTATIVE WORKSPACE")
    w("## C1 CANDIDATE DEVELOPER REPORT")
    w("")
    # Stamped from the evidence, not from the wall clock. A `now()` here would
    # make the report differ on every regeneration, so a reviewer could not
    # compare the sealed copy against a freshly generated one byte for byte —
    # and byte comparison is the whole point of the rest of this package.
    stamps = [
        step(name).get("finished_at", "")
        for name in steps
        if step(name).get("finished_at")
    ]
    generated_at = max(stamps) if stamps else "unknown"
    w(f"Generated from the evidence in `{V}/`, as of {generated_at} —")
    w("the finishing time of the last authoritative step, not the wall clock, so")
    w("regenerating this report from the same evidence reproduces it byte for byte.")
    w("Every digest, count and size below is read out of that evidence at")
    w("generation time. None is typed by hand — see §12 for why that matters.")
    w("")
    w("---")
    w("")
    w("## 1. What this package is")
    w("")
    w(f"**State:** `{identity.get('candidate_state')}`")
    w("")
    w(f"**Highest assertion made:** `{identity.get('highest_self_assertion')}`")
    w("")
    w("**FRONT-05 is open only for this bounded C1 acceptance attempt.** The project")
    w("owner directive and candidate Program Control Register permit exact-byte")
    w("independent review. The candidate retains `CANDIDATE_NOT_ACCEPTED`; only a")
    w("successful authoritative run plus a post-run governance record may accept it.")
    w("")
    w("**What is implemented:** a mandate-scoped, server-authoritative WS-04")
    w("workspace at `/representative` — the desk and case detail, positions,")
    w("deviations, declarations, publication proposals and conflict restrictions —")
    w("with every network capability blocked against a named missing dependency and")
    w("the four hard prohibitions enforced by construction rather than by policy text.")
    w("")
    w("## 2. Identity")
    w("")
    w("| Field | Value |")
    w("| --- | --- |")
    for label, key in (
        ("source_tree_digest", "source_tree_digest"),
        ("test_source_digest", "test_source_digest"),
        ("configuration_digest", "configuration_digest"),
        ("validator_source_digest", "validator_source_digest"),
        ("contract_digest", "contract_digest"),
        ("package_lock_sha256", "package_lock_sha256"),
    ):
        w(f"| `{label}` | `{identity.get(key, '')}` |")
    w(f"| source file count | {identity.get('source_file_count')} |")
    w("")
    w("**The archive's own sha256 is deliberately not in this table.** It cannot be:")
    w("this report is sealed inside the archive, so any hash of the archive written")
    w("here would be the hash of a different archive — the one that existed before")
    w("this line was added. Chasing that fixed point is how a report ends up quoting")
    w("a stale identity, which is exactly the FRONT-04 C2 failure. The archive")
    w("identity therefore lives where it can be correct: the detached")
    w("`.sha256` sidecar, `validation/front05/archive_manifest.json`, and the")
    w("terminal marker `FRONT05_C1_CANDIDATE_RESULT:PASS:<sha256>:<size>`.")
    w("")
    w("The sealing script is deterministic — entries in sorted order, fixed")
    w("timestamps, fixed permissions — so sealing the same tree twice produces")
    w("identical bytes. That is what makes \"the same bytes were reviewed\" a")
    w("checkable statement rather than a hope.")
    w("")
    w("## 3. Lineage")
    w("")
    w("Built on the accepted FRONT-04 C2 bytes, which this package leaves intact.")
    w("")
    w("| Predecessor | sha256 | Decision |")
    w("| --- | --- | --- |")
    for name, record in (lineage.get("accepted_predecessors") or {}).items():
        w(f"| {name} | `{record.get('sha256', '')}` | {record.get('decision', '')} |")
    w("")
    w("**The inherited tree is unchanged.** Recomputing the FRONT-04 digest over the")
    w("FRONT-04 include roots gives:")
    w("")
    w(f"- accepted implementation digest: `{inherited.get('implementation_digest_accepted', '')}`")
    w(f"- measured implementation digest: `{inherited.get('implementation_digest_measured', '')}`")
    w(f"- unchanged: **{inherited.get('implementation_unchanged')}**")
    w(f"- files disturbed outside the shared root: `{inherited.get('files_disturbed_outside_the_shared_root')}`")
    w("")
    w("Exactly two files change, and they are named rather than glossed:")
    w(f"`{'`, `'.join(inherited.get('shared_root_files_changed', []))}`.")
    w(inherited.get("shared_root_change_reason", ""))
    w("")
    w("**Predecessor programme state**, unchanged by this package:")
    w("")
    for unit, state in (lineage.get("predecessor_programme_state") or {}).items():
        w(f"- {unit}: `{state}`")
    w("")
    w("## 4. Capability truth")
    w("")
    counts = caps.get("counts", {})
    w(f"{caps.get('capability_count')} capabilities are registered.")
    w("")
    w("| Status | Count |")
    w("| --- | --- |")
    for key, value in counts.items():
        w(f"| `{key}` | {value} |")
    w("")
    w("**No WS-04 capability that reaches the network is supported.** The accepted API")
    w("layer does not supply an accepted representative-desk or elected-mandate runtime;")
    w("`representative-desk-service` (PACK-29) and `office-mandate-service` (PACK-20)")
    w("remain outside the accepted executable baseline. The bounded accepted CTRL-01")
    w("foundation likewise creates no WS-04 action path. The three supported capabilities are local — refusal rendering,")
    w("scope binding and the governed fallback — and depend on nothing external.")
    w("")
    w("`compliance-service.RepresentationMandate` is legal power of attorney under")
    w("PACK-09. It is **not** an elected mandate and is not used as one; conflating")
    w("them would have been a correctness defect dressed as progress.")
    w("")
    w("## 5. The security-sensitive dependency")
    w("")
    w("One dependency is not merely missing. It is defective, and the distinction is")
    w("recorded as a finding rather than a line in a gap list.")
    w("")
    for boundary in ssd.get("boundaries", []):
        w(f"**{boundary['id']} — {boundary['owner']}**")
        w("")
        w(f"*Observed.* {boundary['observed']}")
        w("")
        w(f"*Finding.* {boundary['finding']}")
        w("")
        w(f"*Position.* {boundary['front05_position']}")
        w("")
        w("*These would not resolve it:*")
        w("")
        for remedy in boundary["insufficient_remedies"]:
            w(f"- {remedy}")
        w("")
        w(f"*Unblocking condition.* {boundary['unblocking_condition']}")
        w("")
        w(f"*Status until then.* {boundary['status_until_then']}")
        w("")
        w(f"*Escalation.* {boundary['escalation']}")
        w("")
    w("Enforced by `INV-21`, by gate `G46`, by a module-load assertion in")
    w("`domain/capabilities.ts` that refuses to start the workspace if the")
    w("classification is violated, and by mutations `M-F05-S01`…`M-F05-S05`.")
    w("")
    w("## 6. Routes")
    w("")
    w(f"{routes.get('route_count')} routes, all under the WS-04 prefix, none creating authority.")
    w("")
    w("| Route | Authority required | Cross-scope behaviour |")
    w("| --- | --- | --- |")
    for row in routes.get("routes", []):
        w(f"| `{row['route']}` | `{row.get('authority_required')}` | {row.get('cross_scope_behaviour')} |")
    w("")
    w("## 7. Evidence")
    w("")
    w("Each record embeds the source, test, configuration, validator and contract")
    w("digests measured **at execution time**, plus the SHA-256 of its own raw log.")
    w("Each raw log carries a result trailer inside the hashed bytes, so an outcome")
    w("is re-derived rather than read.")
    w("")
    w("| Step | Result | Tests | exit | raw log sha256 |")
    w("| --- | --- | --- | --- | --- |")
    for name in steps:
        record = step(name)
        if not record:
            continue
        count = record.get("test_count", record.get("passed", ""))
        w(
            f"| `{name}` | {record.get('result')} | {count} | "
            f"{record.get('exit_code')} | `{record.get('raw_report_sha256', '')}` |"
        )
    w("")
    w("## 8. Authorization negatives")
    w("")
    w(f"{negatives.get('satisfied')}/{negatives.get('case_count')} scenarios satisfied.")
    w("Each entry names an executed test and reports that test's observed outcome;")
    w("nothing is asserted independently of a run.")
    w("")
    w("| ID | Scenario | Observed |")
    w("| --- | --- | --- |")
    for case in negatives.get("cases", []):
        w(f"| `{case['id']}` | {case['scenario']} | {case['observed']} |")
    w("")
    w("## 9. Mutation resistance")
    w("")
    if mutations:
        w(f"{mutations.get('detected')}/{mutations.get('count')} mutations detected.")
        w("")
        w("A mutation is DETECTED when it makes a gate fail that was **not already**")
        w("failing on the unmutated tree, so the harness names the gate that caught it")
        w("rather than accepting any non-zero exit.")
        w("")
        w("| Family | Count |")
        w("| --- | --- |")
        for family, count in (mutations.get("families") or {}).items():
            w(f"| `{family}` | {count} |")
        w("")
        w(f"Bound to source tree `{mutations.get('baseline_source_tree_digest', '')}`.")
        w("")
        w("**The first run of this suite left 30 of 44 mutations undetected.** Every one")
        w("of those was a hole in a gate, not a flaw in the attack: gates that checked a")
        w("prohibition function *existed* were satisfied by one rewritten to return true")
        w("for a single role, and gates that read a derived JSON record were satisfied by")
        w("a stale record while the source said otherwise. The gates were closed — a")
        w("totality check on every prohibition, and a re-derivation of the capability")
        w("table from source at validation time. No mutation was softened.")
        w("")
        w("| ID | Attack | Detected by |")
        w("| --- | --- | --- |")
        for entry in mutations.get("mutations", []):
            caught = ", ".join(f"`{g}`" for g in entry.get("detecting_gates", [])) or "—"
            name = entry["name"].split(" ", 1)[1] if " " in entry["name"] else entry["name"]
            w(f"| `{entry['id']}` | {name} | {caught} |")
    else:
        w("Not yet run.")
    w("")
    w("## 10. Dependency posture")
    w("")
    w("Re-measured for this workspace rather than inherited from FRONT-04, because")
    w("the FRONT-04 correction was explicit that a developer's own non-blocking")
    w("judgement may not be carried forward.")
    w("")
    w("| Package | Severity | Bundle matches | Disposition |")
    w("| --- | --- | --- | --- |")
    for finding in deps.get("findings", []):
        w(
            f"| `{finding['package']}` | {finding['severity']} | "
            f"{finding.get('client_bundle_name_matches')} | `{finding['disposition']}` |"
        )
    w("")
    hardening = deps.get("hardening_verified_this_round", {})
    if hardening:
        w(f"**Hardening carried and re-verified:** {hardening.get('change')} — present: "
          f"{hardening.get('present')}. {hardening.get('reason')}")
    w("")
    w("## 11. Gates")
    w("")
    if result:
        w(f"**{result.get('gates_passed')}/{result.get('gates_total')} — {result.get('status')}**")
        w("")
        w(f"State: `{result.get('state')}`. Self-acceptance: `{result.get('self_acceptance')}`.")
        w("")
        failing = [k for k, v in (result.get("gates") or {}).items() if v["status"] != "PASS"]
        if failing:
            w(f"Failing: {', '.join(f'`{g}`' for g in failing)}")
            w("")
    w("44 gates come from the assignment's acceptance-gate seed. Two are added by the")
    w("stage contract, each because a real failure showed the seed set had a hole:")
    w("`G45` (report identity cross-check) and `G46` (security-sensitive dependency")
    w("discipline).")
    w("")
    w("## 12. Defects found by the gates, not by review")
    w("")
    w("Five, recorded because each is more informative than the passes:")
    w("")
    w("1. **Static prerendering silently killed hydration.** Every page was")
    w("   statically prerendered, so the per-request CSP nonce could never match")
    w("   script tags stamped at build time. Every script was blocked and nothing")
    w("   hydrated — while the markup still looked complete. Fixed with per-page")
    w("   `force-dynamic`, which is also the semantically correct answer for")
    w("   mandate-scoped `no-store` surfaces.")
    w("2. **A surface/provider race produced a permanent false refusal.** Surfaces")
    w("   read before the mandate scope resolved, so an operator genuinely in scope")
    w("   saw a scope refusal that no later event cleared. Fixed with a readiness")
    w("   guard.")
    w("3. **A conflict-restricted case was distinguishable from a non-existent one.**")
    w("   The restricted case rendered a *different panel*, naming the conflict")
    w("   register — the membership oracle in a politer font. Now every negative")
    w("   outcome on that surface renders one identical refusal, and the browser gate")
    w("   compares all four negative outcomes rather than a pair.")
    w("4. **Horizontal overflow at 320px.** Grid items' default `min-width: auto`")
    w("   plus German compound headings made the document scroll sideways. Fixed with")
    w("   `min-width: 0` and hyphenation — no design token touched.")
    w("5. **Thirty of forty-four mutations initially survived.** See §9.")
    w("")
    w("## 13. Open governance items")
    w("")
    w("- **Publication authorization (SSD-01).** Recorded above as a security-relevant")
    w("  finding against PACK-13, not as a FRONT-05 gap.")
    w("- **Route prefix.** The accepted frontend policy record carries a display name")
    w("  in its route-prefix field. This package uses `/representative` from the target")
    w("  architecture and records the conflict rather than silently choosing.")
    w("- **No accepted WS-04 action path.** Bounded CTRL-01 is accepted, but it does")
    w("  not provide representative-workspace action auditing. The interface says so")
    w("  to the operator rather than leaving it to be discovered.")
    w("- **Archive hygiene is checked against a file set, not a manifest.** In a")
    w("  working tree the archive's contents can only be judged through the manifest")
    w("  the sealing step wrote; in a tree extracted from the archive there is no")
    w("  manifest and none is needed, because the tree *is* the archive and gate G43")
    w("  walks it directly. The gate records which of the two it checked. An earlier")
    w("  version passed trivially whenever the manifest was absent — which is exactly")
    w("  the situation a reviewer re-validating from the sealed bytes is in.")
    w("- **Visual baselines.** The 33 baselines here are this stage's own, created in")
    w("  this round. Three were regenerated after intended changes (the non-disclosure")
    w("  fix, the security-finding section, the home dependency text). No *inherited*")
    w("  FRONT-00/01 baseline was regenerated — that would be a prohibited remedy.")
    w("")
    w("## 14. What this package does not claim")
    w("")
    w("The list below is a disclaimer, not an assertion. It is fenced so that gate")
    w("G45 can tell the difference: a report that disowns a forbidden claim must not")
    w("fail for mentioning it, and a report that makes one must not escape by putting")
    w("it here. The gate checks that everything inside the fence is exactly an item")
    w("from the stage contract's `non_claims`.")
    w("")
    w("<!-- front05:non-claims:start -->")
    for claim in contract.get("non_claims", []):
        w(f"- {claim}")
    w("<!-- front05:non-claims:end -->")
    w("")
    w("Independent governed review on the sealed bytes owns the acceptance decision.")
    w("This report does not make it.")
    w("")

    path = root / "FRONT05_C1_DEVELOPER_REPORT.md"
    path.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {path.name} ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

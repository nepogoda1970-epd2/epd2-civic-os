#!/usr/bin/env python3
"""FRONT-05 governed validator.

46 gates. G01-G44 come from the assignment's acceptance-gate seed; G45 and G46
are added by the stage contract, each because a real failure showed that the
seed set had a hole:

* **G45 — report identity cross-check.** The FRONT-04 C2 archive was rejected
  and resealed because the developer report quoted a `source_tree_digest` from a
  penultimate run while the sealed tree carried another. The report sat outside
  the digest-covered boundary, so no gate looked at it. G45 reads every 64-hex
  digest and every byte size the report quotes and compares each against the
  evidence record it names.

* **G46 — security-sensitive dependency discipline.** `transparency-service`
  authorises publication by a caller-supplied `actor_is_authorized` boolean,
  which is a self-asserted authorization rather than an authorization. Recorded
  as a neutral gap it would invite a later round to add a route over the top of
  it and call the capability supported. G46 enforces that a capability whose
  dependency is classified `SECURITY_SENSITIVE_BOUNDARY` stays blocked, states a
  finding, and is never recorded as a declared limitation.

The gates read the **stage contract** as their authority rather than constants
baked in here, so an independent reviewer can replace the contract and re-run
the validator against the unchanged implementation.

What these gates guarantee: stale, transplanted or silently edited evidence
produces a deterministic FAIL, and every prohibition of the assignment is
checked against the code rather than against a claim about the code. What they
do not guarantee, and no local validator can: immunity against an actor who
rewrites every artifact consistently. The control for that is independent
re-execution from the sealed bytes, which this validator does not perform and
does not claim to.

Usage:
    python3 scripts/validate_front05.py [root] [--output PATH]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# Do not write bytecode caches. G43, running on a tree extracted from the
# archive, walks the tree it is standing in — so a `__pycache__` directory
# created by this very run would be reported as an archive-hygiene failure. The
# validator must not contaminate the thing it measures.
sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
import front05_digest as digest

WS = "frontend/representative-workspace"
CONTRACT_JSON = "docs/frontend/FRONT-05-STAGE-CONTRACT.json"
CONTRACT_MD = "docs/frontend/FRONT-05-STAGE-CONTRACT.md"
EVIDENCE_DIR = "validation/front05/evidence"
RAW_DIR = "validation/front05/raw"
RAW_TRAILER = "FRONT05_RAW_RESULT"

# Accepted predecessor identities, pinned. A mutation to any of these is caught.
FRONT04_C2_SHA = "1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8"
FRONT04_C2_TREE = "eee6bf1e80f9e5b5ce18618611513b871b195a163e98948d55d99f61276f2f2e"
FRONT03_C1_SHA = "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26"
FRONT02_C21_SHA = "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179"

parser = argparse.ArgumentParser()
parser.add_argument("root", nargs="?", default=".")
parser.add_argument("--output")
parser.add_argument("--report", default="FRONT05_C1_DEVELOPER_REPORT.md")
args = parser.parse_args()
R = Path(args.root).resolve()

gates: dict[str, dict[str, Any]] = {}


def text(rel: str) -> str:
    p = R / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def exists(rel: str) -> bool:
    return (R / rel).exists()


def load(rel: str) -> Any:
    try:
        return json.loads((R / rel).read_text(encoding="utf-8"))
    except Exception:
        return None


def rows(rel: str) -> list[dict[str, str]]:
    p = R / rel
    if not p.is_file():
        return []
    with p.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def gate(name: str, errors: list[str]) -> None:
    gates[name] = {"status": "PASS" if not errors else "FAIL", "errors": errors}


CONTRACT: dict[str, Any] = load(CONTRACT_JSON) or {}
CURRENT = digest.summary(R)
FULL = digest.compute(R)


def production_sources() -> dict[str, str]:
    """Every production TypeScript source of the workspace.

    Tests, configuration and the governed fixture module are excluded. The
    fixture is excluded because G-fixture proves separately that it cannot enter
    a production build, and including it here would make the content scans below
    fail on the fixture's own clearly-marked prototype data.
    """
    out: dict[str, str] = {}
    for base in ("app", "components", "domain", "policies", "runtime", "content"):
        root = R / WS / base
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.suffix not in {".ts", ".tsx"} or not p.is_file():
                continue
            rel = str(p.relative_to(R))
            if rel.endswith("governedTestRuntime.ts"):
                continue
            out[rel] = p.read_text(encoding="utf-8", errors="replace")
    return out


def strip_comments(body: str) -> str:
    """Source with comments and string literals removed.

    Several prohibitions below are checked by scanning for a token. A naive scan
    over raw text flags the very files that *document* the prohibition — the
    policy module listing forbidden analytics vendors, the middleware comment
    explaining why `'unsafe-inline'` is the wrong fix. Those are the files doing
    the right thing, so the scans run over code with comments and literals
    removed and a token found there is a real use.
    """
    body = re.sub(r"/\*[\s\S]*?\*/", " ", body)
    body = re.sub(r"(?m)^\s*//.*$", " ", body)
    body = re.sub(r"(?<![:\w])//.*$", " ", body, flags=re.M)
    body = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', body)
    body = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", body)
    body = re.sub(r"`(?:[^`\\]|\\.)*`", "``", body)
    return body


def function_body(source: str, name: str) -> str | None:
    """The body of a named exported function, or None if it is not there."""
    match = re.search(
        rf"export function {re.escape(name)}\s*(?:<[^>]*>)?\s*\([^)]*\)\s*:\s*([^{{]*)\{{",
        source,
    )
    if match is None:
        return None
    start = match.end() - 1
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : index]
    return None


def total_refusal(source: str, name: str) -> list[str]:
    """Check that a prohibition is a *total* refusal, not a conditional one.

    A gate that only checks the function exists is satisfied by a function that
    returns true for one role — which is exactly how a prohibition gets quietly
    repealed. So the declared return type must be the literal `false`, and the
    body must contain no return other than `return false`. The mutation suite
    attacks each of these directly, and every one of them survived an earlier
    version of this validator that checked only for the name.
    """
    problems: list[str] = []
    match = re.search(
        rf"export function {re.escape(name)}\s*(?:<[^>]*>)?\s*\([^)]*\)\s*:\s*([A-Za-z<>\[\] |]+?)\s*\{{",
        source,
    )
    if match is None:
        return [f"prohibition-function-missing:{name}"]
    if match.group(1).strip() != "false":
        problems.append(f"prohibition-return-type-widened:{name}:{match.group(1).strip()}")
    body = function_body(source, name)
    if body is None:
        return problems + [f"prohibition-body-unreadable:{name}"]
    returns = [r.strip() for r in re.findall(r"return\s+([^;]+);", body)]
    if returns != ["false"]:
        problems.append(f"prohibition-not-total:{name}:{returns}")
    return problems


PROD = production_sources()

# Source files several gates read. Hoisted so the gates can be written in any
# order without one silently depending on another having run first.
authority_src = text(f"{WS}/policies/authority.ts")
bnd = text(f"{WS}/policies/boundaries.ts")
conf = text(f"{WS}/policies/confidentiality.ts")
ws_policy = text(f"{WS}/policies/workspace.ts")
scope_src = text(f"{WS}/domain/scope.ts")
types_src = text(f"{WS}/domain/types.ts")
workflow = text(f"{WS}/domain/caseWorkflow.ts")
pub = text(f"{WS}/domain/publication.ts")
dev = text(f"{WS}/domain/deviation.ts")
conflict = text(f"{WS}/domain/conflict.ts")
decl = text(f"{WS}/domain/declaration.ts")
session_src = text(f"{WS}/domain/session.ts")
ports = text(f"{WS}/runtime/ports.ts")
de = text(f"{WS}/content/de.ts")
lang = text(f"{WS}/policies/language.ts")
ws_css = text(f"{WS}/app/workspace.css")
mw = text(f"{WS}/middleware.ts")
config = text(f"{WS}/next.config.ts")
spec = text(f"{WS}/tests/browser/front05.browser.spec.ts")
ALL_PROD = "\n".join(PROD.values())
CODE = {rel: strip_comments(body) for rel, body in PROD.items()}
CAPS = load("validation/front05/api_capability_truth.json") or {}
ROUTES = load("validation/front05/route_inventory.json") or {}
SCOPES = load("validation/front05/mandate_scope_inventory.json") or {}
DEPS = load("validation/front05/dependency_reconciliation.json") or {}


# =========================================================== G01 bootstrap_freshness
# The package was built against the recorded entering baseline, and the
# governance state it declares matches the one the register actually carries.
e: list[str] = []
if not CONTRACT:
    e.append("stage-contract-missing-or-unparseable")
else:
    gs = CONTRACT.get("governance_state", {})
    opening = gs.get("stage_opening", {})
    if opening.get("canonically_opened") is not True:
        e.append("bounded-c1-stage-not-opened-for-independent-review")
    if gs.get("candidate_internal_state") != "CANDIDATE_NOT_ACCEPTED":
        e.append("candidate-internal-state-wrong")
    if gs.get("highest_permitted_self_assertion") != "PASS_FOR_INDEPENDENT_ACCEPTANCE":
        e.append("self-assertion-ceiling-wrong")
    if CONTRACT.get("scope_class") != "BOUNDED WS-04 FRONTEND CANDIDATE":
        e.append("scope-class-wrong")
    ratification = CONTRACT.get("ratification", {})
    if ratification.get("status_in_candidate") != "PROPOSED_FOR_GOVERNED_RATIFICATION":
        e.append("contract-ratification-proposal-missing")
for required in (
    "schema", "contract_version", "hard_invariants", "required_evidence",
    "evidence_binding_fields", "required_routes", "gates",
    "security_sensitive_dependencies", "report_identity_crosscheck",
    "minimum_mutation_count", "authoritative_result_path",
):
    if required not in CONTRACT:
        e.append(f"contract-field-missing:{required}")
if not exists(CONTRACT_MD):
    e.append("contract-markdown-mirror-missing")
gate("G01", e)

# =========================================================== G02 baseline_identity
# The source-set digest is computable, the exclusion set hides no source, and
# the identity records exist.
e = []
if FULL["exclusion_audit_problems"]:
    e.extend(f"exclusion-audit:{p}" for p in FULL["exclusion_audit_problems"])
if FULL["file_count"] < 100:
    e.append(f"implausible-file-count:{FULL['file_count']}")
if not CURRENT["source_tree_digest"]:
    e.append("source-tree-digest-missing")
manifest = load("validation/front05/source_manifest.json")
if not manifest:
    e.append("source-manifest-missing")
elif manifest.get("source_tree_digest") != CURRENT["source_tree_digest"]:
    e.append("source-manifest-digest-stale")
gate("G02", e)

# =========================================================== G03 accepted_front_lineage
# The pinned predecessor identities are the accepted ones, and the acceptance
# records they come from are present and unmodified.
e = []
lineage_src = text(f"{WS}/runtime/productionRuntime.ts")
for label, value in (
    ("front04C2Sha256", FRONT04_C2_SHA),
    ("front04C2SourceTreeDigest", FRONT04_C2_TREE),
    ("front03C1Sha256", FRONT03_C1_SHA),
    ("front02C21Sha256", FRONT02_C21_SHA),
):
    if value not in lineage_src:
        e.append(f"lineage-value-missing-or-changed:{label}")
record = load("docs/frontend/FRONT-04-C2-ACCEPTANCE-RECORD.json")
if not record:
    e.append("front04-c2-acceptance-record-missing")
else:
    if record.get("candidate", {}).get("sha256") != FRONT04_C2_SHA:
        e.append("front04-c2-sha-mismatch")
    if record.get("candidate", {}).get("source_tree_digest") != FRONT04_C2_TREE:
        e.append("front04-c2-tree-mismatch")
    if record.get("decision") != "ACCEPTED":
        e.append("front04-c2-not-accepted")
lineage = load("validation/front05/lineage.json")
if not lineage:
    e.append("lineage-record-missing")
gate("G03", e)

# =========================================================== G04 design_preservation
# Every inherited token is reproduced byte for byte, and the workspace adds none.
e = []
globals_css = text("frontend/web-shell/app/globals.css")
ws_css = text(f"{WS}/app/workspace.css")


def tokens_of(css: str) -> dict[str, str]:
    if ":root {" not in css:
        return {}
    block = css[css.index(":root {") : css.index("}", css.index(":root {"))]
    out = {}
    for line in block.splitlines():
        m = re.match(r"\s*(--[a-z0-9-]+):\s*(.+);\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


inherited = tokens_of(globals_css)
mine = tokens_of(ws_css)
if not inherited:
    e.append("inherited-stylesheet-missing")
if not mine:
    e.append("workspace-stylesheet-missing")
for name, value in mine.items():
    if inherited.get(name) != value:
        e.append(f"token-diverges:{name}")
policy = text(f"{WS}/policies/visualBaseline.ts")
for name, value in mine.items():
    if f'"{name}": "{value}"' not in policy:
        e.append(f"token-not-registered-in-policy:{name}")
if "FRONT05_DESIGN_CHANGE_DECISIONS = Object.freeze([] as const)" not in policy:
    e.append("design-change-decision-claimed-without-one")
# The additions block introduces no literal colour of its own.
if "WS-04 additions." in ws_css:
    additions = ws_css[ws_css.index("WS-04 additions.") :]
    if re.search(r"#[0-9a-fA-F]{3,8}\b", additions):
        e.append("additions-introduce-a-literal-colour")
gate("G04", e)

# =========================================================== G05 workspace_origin_boundary
# Separate origin, no import of another workspace's runtime, isolation headers.
e = []
ws_policy = text(f"{WS}/policies/workspace.ts")
if 'WS04_ORIGIN = "https://represent.epd.example"' not in ws_policy:
    e.append("origin-wrong-or-missing")
if 'WS04_ROUTE_PREFIX = "/representative"' not in ws_policy:
    e.append("route-prefix-wrong-or-missing")
for rel, body in PROD.items():
    for foreign in ("web-shell", "voting-client"):
        if re.search(rf'from\s+"[^"]*{foreign}', body):
            e.append(f"cross-workspace-import:{rel}:{foreign}")
config = text(f"{WS}/next.config.ts")
for header in (
    '"X-Frame-Options", value: "DENY"',
    '"X-Content-Type-Options", value: "nosniff"',
    '"Referrer-Policy", value: "no-referrer"',
    '"Cross-Origin-Opener-Policy", value: "same-origin"',
    '"Cross-Origin-Resource-Policy", value: "same-origin"',
):
    if header.replace('"', '"') not in config.replace("key: ", "").replace(" ", " "):
        # tolerate formatting: check the key and the value independently
        key = header.split(",")[0].strip('"')
        val = header.split("value: ")[1].strip('"')
        if key not in config or val not in config:
            e.append(f"security-header-missing:{key}")
mw = text(f"{WS}/middleware.ts")
for directive in (
    "default-src 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'none'",
):
    if directive not in mw:
        e.append(f"csp-directive-missing:{directive}")
# The policy is the array of directives the middleware joins, not the file. The
# file legitimately explains in prose why 'unsafe-inline' is the wrong fix, and
# an earlier version of this gate failed the very comment that says so.
policy_block = re.search(r"const policy = \[([\s\S]*?)\]\.join", mw)
if policy_block is None:
    e.append("csp-policy-array-not-found")
else:
    for forbidden in ("unsafe-inline", "unsafe-eval"):
        if forbidden in policy_block.group(1):
            e.append(f"csp-weakened:{forbidden}")
if "no-store" not in config:
    e.append("no-store-missing")
gate("G05", e)

# =========================================================== G06 route_inventory
# Every implemented route is declared, every declared route is implemented, and
# each records its scope source, authority and cross-scope behaviour.
e = []
if not ROUTES:
    e.append("route-inventory-missing")
else:
    if ROUTES.get("undeclared_routes"):
        e.extend(f"undeclared-route:{r}" for r in ROUTES["undeclared_routes"])
    if ROUTES.get("unimplemented_routes"):
        e.extend(f"unimplemented-route:{r}" for r in ROUTES["unimplemented_routes"])
    prefix = CONTRACT.get("workspace", {}).get("route_prefix", "/representative")
    for row in ROUTES.get("routes", []):
        if row["route"] != "/" and not row["route"].startswith(prefix):
            e.append(f"route-outside-prefix:{row['route']}")
        if row.get("routing_creates_authority"):
            e.append(f"route-creates-authority:{row['route']}")
        for field in ("scope_source", "cross_scope_behaviour", "authority_required"):
            if row.get(field) in (None, ""):
                e.append(f"route-field-missing:{row['route']}:{field}")
    declared = {r["route"] for r in CONTRACT.get("required_routes", [])}
    found = {r["route"] for r in ROUTES.get("routes", [])}
    if declared != found:
        e.append(f"route-set-mismatch:{sorted(declared ^ found)}")
gate("G06", e)

# =========================================================== G07 api_capability_truth
# The capability register is complete, uses the contract's vocabulary, names a
# dependency for every block, and reports nothing on the network as supported.
e = []
vocabulary = set(CONTRACT.get("capability_status_vocabulary", []))
if not CAPS:
    e.append("capability-truth-missing")
else:
    if CAPS.get("no_network_capability_supported") is not True:
        e.append("a-network-capability-is-reported-supported")
    if CAPS.get("counts", {}).get("SUPPORTED_WITH_DECLARED_LIMITATION", 0) != 0:
        e.append("declared-limitation-used-without-a-supported-path")
    for cap in CAPS.get("capabilities", []):
        if cap.get("status") not in vocabulary:
            e.append(f"status-outside-vocabulary:{cap.get('id')}")
        if cap.get("status") == "BLOCKED_BY_DEPENDENCY" and len(cap.get("missingDependency", "")) < 20:
            e.append(f"blocked-without-a-named-dependency:{cap.get('id')}")
        if not cap.get("frontendBehaviour"):
            e.append(f"no-declared-frontend-behaviour:{cap.get('id')}")
    blockable = set(CONTRACT.get("capabilities_that_may_be_dependency_blocked", []))
    must_unsupported = set(CONTRACT.get("capabilities_that_must_be_unsupported", []))
    must_local = set(CONTRACT.get("capabilities_that_must_be_local_real_paths", []))
    for cap in CAPS.get("capabilities", []):
        cid, status = cap.get("id"), cap.get("status")
        if status == "BLOCKED_BY_DEPENDENCY" and cid not in blockable:
            e.append(f"capability-blocked-but-not-blockable-by-contract:{cid}")
        if cid in must_unsupported and status != "UNSUPPORTED":
            e.append(f"capability-must-be-unsupported:{cid}")
        if cid in must_local and status != "SUPPORTED_REAL_PATH":
            e.append(f"local-capability-not-a-real-path:{cid}")
    # The derived record must actually be derived from the *current* source. A
    # stale table is how a capability gets quietly promoted: edit the register,
    # leave the JSON alone, and every gate that reads the JSON is satisfied.
    try:
        import build_front05_records as records

        rederived = records.capability_truth(R)
    except Exception as exc:  # pragma: no cover
        rederived = None
        e.append(f"capability-truth-not-rederivable:{exc}")
    if rederived is not None:
        live = {c["id"]: c for c in rederived["capabilities"]}
        recorded = {c["id"]: c for c in CAPS.get("capabilities", [])}
        if set(live) != set(recorded):
            e.append(f"capability-record-stale:ids:{sorted(set(live) ^ set(recorded))}")
        for cid, cap in live.items():
            other = recorded.get(cid)
            if other is None:
                continue
            for field in ("status", "dependencyClass", "missingDependency", "securityFinding"):
                if cap.get(field) != other.get(field):
                    e.append(f"capability-record-stale:{cid}:{field}")

    # The CSV mirror must agree with the register it is derived from.
    csv_rows = rows("docs/frontend/FRONT-05-CAPABILITY-STATUS-MATRIX.csv")
    by_id = {c["id"]: c for c in CAPS.get("capabilities", [])}
    if len(csv_rows) != len(by_id):
        e.append("capability-csv-row-count-mismatch")
    for row in csv_rows:
        cap = by_id.get(row.get("capability_id"))
        if cap is None:
            e.append(f"capability-csv-unknown-row:{row.get('capability_id')}")
        elif row.get("status") != cap.get("status"):
            e.append(f"capability-csv-status-mismatch:{row.get('capability_id')}")
gate("G07", e)

# =========================================================== G08 mandate_scope_inventory
e = []
if not SCOPES:
    e.append("scope-inventory-missing")
else:
    if SCOPES.get("unbounded_scope_representable") is not False:
        e.append("an-unbounded-scope-is-representable")
    if SCOPES.get("cross_mandate_action_count", 1) != 0:
        e.append("a-cross-mandate-action-exists")
    for action in SCOPES.get("actions", []):
        for field in (
            "scope_source", "required_authority", "resource_scope",
            "cross_scope_behaviour", "expected_refusal_state",
        ):
            if not action.get(field):
                e.append(f"scope-field-missing:{action.get('action')}:{field}")
        if action.get("resource_scope") != "single mandate":
            e.append(f"action-not-single-mandate:{action.get('action')}")
scope_src = text(f"{WS}/domain/scope.ts")
for required in ("bindScope", "ScopeBound", "mayReadAcrossMandates"):
    if required not in scope_src:
        e.append(f"scope-primitive-missing:{required}")
e.extend(total_refusal(scope_src, "mayReadAcrossMandates"))
e.extend(total_refusal(authority_src, "crossMandateAccessAvailableFor"))
# The guard that makes a foreign mandate unreachable must still be the guard.
if "requestedMandateId !== null && requestedMandateId !== scope.mandateId" not in scope_src:
    e.append("scope-mismatch-guard-removed-or-rewritten")
resolved = function_body(scope_src, "resolvedMandateIds")
if resolved is None:
    e.append("resolvedMandateIds-missing")
elif re.search(r"\[[^\]]*,[^\]]*\]", resolved):
    e.append("more-than-one-mandate-can-be-resolved")
# No forbidden universal role may appear in the role list itself.
role_list = re.search(r"export const WS04_ROLES = Object\.freeze\(\[([\s\S]*?)\]", authority_src)
if role_list is None:
    e.append("role-list-not-found")
else:
    for forbidden in re.findall(
        r'"([^"]+)"',
        re.search(
            r"FORBIDDEN_UNIVERSAL_ROLES = Object\.freeze\(\[([\s\S]*?)\]",
            authority_src,
        ).group(1)
        if re.search(r"FORBIDDEN_UNIVERSAL_ROLES", authority_src)
        else "",
    ):
        if f'"{forbidden}"' in role_list.group(1):
            e.append(f"forbidden-universal-role-is-a-ws04-role:{forbidden}")
gate("G08", e)

# =========================================================== G09 auth_session
e = []
session_src = text(f"{WS}/domain/session.ts")
types_src = text(f"{WS}/domain/types.ts")
for state in (
    "anonymous", "authenticated", "stepped_up", "step_up_required",
    "expired", "revoked", "scope_changed", "authority_suspended", "authority_expired",
):
    if f'"{state}"' not in types_src:
        e.append(f"session-state-missing:{state}")
for negative in ("expired", "revoked", "scope_changed", "authority_suspended", "authority_expired"):
    m = re.search(rf"\n  {negative}: \{{([^}}]*)\}}", session_src)
    if m is None:
        e.append(f"no-transition-row-for:{negative}")
        continue
    row = m.group(1)
    for working in ("authenticated", "stepped_up"):
        if f": \"{working}\"" in row:
            e.append(f"terminal-state-returns-to-work:{negative}->{working}")
if "interruptionFor" not in session_src:
    e.append("no-interruption-model")
gate("G09", e)

# =========================================================== G10 step_up
e = []
authority_src = text(f"{WS}/policies/authority.ts")
if "stepUpRequired" not in authority_src:
    e.append("no-step-up-predicate")
if "commitTimeRevalidationRequired" not in authority_src:
    e.append("no-commit-time-revalidation-predicate")
if 'return impact === "high" || impact === "consequential"' not in authority_src:
    e.append("step-up-not-required-for-high-impact")
if 'return impact === "consequential"' not in authority_src:
    e.append("commit-revalidation-not-required-for-consequential")
if "step_up_authentication" not in json.dumps(CAPS):
    e.append("step-up-capability-not-registered")
gate("G10", e)

# =========================================================== G11 server_authorization_negatives
e = []
negatives = load("validation/front05/authorization_negatives.json")
minimum = CONTRACT.get("minimum_authorization_negative_count", 12)
if not negatives:
    e.append("authorization-negatives-record-missing")
else:
    cases = negatives.get("cases", [])
    if len(cases) < minimum:
        e.append(f"too-few-authorization-negatives:{len(cases)}<{minimum}")
    for case in cases:
        for field in ("id", "scenario", "expected", "observed", "evidence"):
            if not case.get(field):
                e.append(f"negative-field-missing:{case.get('id')}:{field}")
        if case.get("observed") != case.get("expected"):
            e.append(f"negative-not-satisfied:{case.get('id')}")
# Hiding a control is never authorization: the offer function is presentation
# only and the runtime refuses regardless.
if "presentation only" not in authority_src:
    e.append("offer-function-not-documented-as-presentation-only")
e.extend(total_refusal(bnd, "clientMayDecide"))
gate("G11", e)

# =========================================================== G12 wrong_mandate_isolation
e = []
if "nonDisclosing: true" not in scope_src:
    e.append("scope-refusal-not-non-disclosing")
detail_src = text(f"{WS}/components/CaseDetailSurface.tsx")
if "CASE_UNAVAILABLE" not in detail_src:
    e.append("case-detail-has-no-single-refusal")
# Exactly one refusal object may be rendered by the case-detail surface.
rendered = set(re.findall(r"refusal=\{([A-Za-z_][A-Za-z0-9_]*)\}", detail_src))
if rendered != {"CASE_UNAVAILABLE"}:
    e.append(f"case-detail-renders-multiple-refusals:{sorted(rendered)}")
if "DependencyPanel" in detail_src:
    e.append("case-detail-renders-a-dependency-panel-and-can-disclose")
not_found = text(f"{WS}/app/not-found.tsx")
if "gehört nicht zu Ihrem Mandat oder existiert nicht" not in not_found:
    e.append("not-found-wording-diverges-from-the-scope-refusal")
gate("G12", e)

# =========================================================== G13 representative_home
e = []
home = text(f"{WS}/components/HomeSurface.tsx")
for block in ("queueSummary", "pendingDeclarations", "pendingWork", "proposals", "alerts"):
    if block not in home:
        e.append(f"home-block-missing:{block}")
if "nothingActionable" not in home:
    e.append("home-claims-counts-it-cannot-substantiate")
if "capabilitySummary" not in home:
    e.append("home-does-not-state-the-workspace-capability-state")
gate("G13", e)

# =========================================================== G14 case_queue_detail
e = []
desk = text(f"{WS}/components/DeskSurface.tsx")
for state in ("new", "assigned", "triaged", "awaiting_response", "closed", "archived", "unavailable"):
    if f'"{state}"' not in types_src:
        e.append(f"case-state-missing:{state}")
if "data-case-queue" not in desk:
    e.append("no-queue-marker")
if "desk.empty" not in desk and "empty" not in desk:
    e.append("empty-list-claim-not-guarded")
gate("G14", e)

# =========================================================== G15 case_triage_real_path
# Transitions are server-authoritative, carry a version precondition, and the
# uncertain outcome is first-class rather than collapsed into failure.
e = []
workflow = text(f"{WS}/domain/caseWorkflow.ts")
if "clientMayCommitCaseTransition" not in workflow:
    e.append("client-commit-not-refused")
if "requiresVersion: true" not in workflow:
    e.append("transition-without-a-version-precondition")
if "UNCERTAIN_CASE" not in workflow:
    e.append("no-uncertain-outcome")
if 'committed: "unknown"' not in workflow:
    e.append("uncertain-outcome-claims-knowledge-it-lacks")
if "retryOfferedFor" not in workflow:
    e.append("no-retry-policy")
retry_fn = re.search(r"export function retryOfferedFor\([\s\S]*?\n\}", workflow)
if retry_fn is None:
    e.append("retry-policy-function-not-found")
elif 'kind === "refused"' not in retry_fn.group(0):
    e.append("retry-offered-for-outcomes-other-than-a-plain-refusal")
gate("G15", e)

# =========================================================== G16 confidential_storage_boundary
e = []
conf = text(f"{WS}/policies/confidentiality.ts")
if "CONFIDENTIAL_FIELD_NAMES" not in conf:
    e.append("no-confidential-field-list")
if "assertNoConfidentialContent" not in conf:
    e.append("no-confidentiality-assertion")
assert_body = function_body(conf, "assertNoConfidentialContent")
if assert_body is None:
    e.append("confidentiality-assertion-missing")
elif "throw" not in assert_body:
    e.append("confidential-payload-stripped-rather-than-refused")
for rel, body in CODE.items():
    for pattern, label in (
        (r"\blocalStorage\s*\.\s*setItem", "localStorage-write"),
        (r"\bsessionStorage\s*\.\s*setItem", "sessionStorage-write"),
        (r"\bindexedDB\s*\.\s*open", "indexeddb-open"),
        (r"\bdocument\s*\.\s*cookie\s*=", "cookie-write"),
        (r"\bcaches\s*\.\s*open", "cache-open"),
        (r"console\s*\.\s*log", "console-log"),
    ):
        if re.search(pattern, body):
            e.append(f"{label}:{rel}")
gate("G16", e)

# =========================================================== G17 staff_assignment_boundary
e = []
if "mandate_staff_assigned" not in authority_src:
    e.append("no-assigned-staff-authority-level")
if "case.assign" not in workflow:
    e.append("assignment-action-not-registered")
# The frontend may not create authority the server does not recognise.
if "assigneeLabel" not in types_src:
    e.append("assignment-not-displayable")
if re.search(r"case_assignment[\s\S]{0,600}BLOCKED", json.dumps(CAPS)) is None:
    e.append("assignment-capability-not-blocked")
gate("G17", e)

# =========================================================== G18 position_workflow
e = []
for state in ("draft", "submitted_internal", "proposed_for_publication", "public_approved_rendition", "superseded"):
    if f'"{state}"' not in types_src:
        e.append(f"position-state-missing:{state}")
positions = text(f"{WS}/components/PositionSurface.tsx")
if "draftNotSaved" not in positions:
    e.append("draft-persistence-not-stated")
gate("G18", e)

# =========================================================== G19 deviation_workflow
e = []
dev = text(f"{WS}/domain/deviation.ts")
if "deviationAltersDecision" not in dev:
    e.append("no-total-refusal-that-a-deviation-alters-a-decision")
if "referencedDecision === null" not in dev:
    e.append("deviation-permitted-without-a-decision-reference")
if "explanationMinLength" not in dev:
    e.append("deviation-permitted-without-a-substantive-explanation")
if "referenceVerified" not in dev:
    e.append("decision-reference-verification-not-modelled")
gate("G19", e)

# =========================================================== G20 version_provenance
e = []
for required in ("version", "provenance"):
    if required not in types_src:
        e.append(f"provenance-field-missing:{required}")
if "supersedes" not in dev:
    e.append("no-supersession-model")
if "ifVersion" not in text(f"{WS}/runtime/ports.ts"):
    e.append("mutations-without-a-version-precondition")
gate("G20", e)

# =========================================================== G21 meeting_declaration
e = []
decl = text(f"{WS}/domain/declaration.ts")
if "OBLIGATION_REMAINS_OPEN" not in decl:
    e.append("blocked-submission-does-not-state-the-open-obligation")
if "obligationDischarged" not in decl:
    e.append("no-obligation-model")
if 'state === "accepted" && record.submittedAt !== null' not in decl:
    e.append("obligation-discharged-on-insufficient-evidence")
gate("G21", e)

# =========================================================== G22 conflict_recusal
e = []
conflict = text(f"{WS}/domain/conflict.ts")
e.extend(total_refusal(authority_src, "maySelfClearConflict"))
if "maySelfClearConflict" not in conflict:
    e.append("self-clear-refusal-not-used-by-the-domain")
for fn in ("restrictedFor", "anyRestrictionActive"):
    body = function_body(conflict, fn)
    if body is None:
        e.append(f"conflict-function-missing:{fn}")
    elif "if (!knowledge.known) return true;" not in body:
        e.append(f"unknown-restriction-treated-as-cleared:{fn}")
if "FORBIDDEN_CONFLICT_ACTION_IDS" not in conflict:
    e.append("no-forbidden-conflict-action-list")
if "conflictOfficerMay" not in authority_src:
    e.append("conflict-officer-scope-not-bounded")
gate("G22", e)

# =========================================================== G23 publication_proposal
e = []
pub = text(f"{WS}/domain/publication.ts")
if "PROPOSAL_DISCLAIMER" not in pub:
    e.append("no-proposal-disclaimer")
if "keine Veröffentlichung" not in pub or "keine Freigabe" not in pub:
    e.append("disclaimer-does-not-deny-publication-and-approval")
if "PUBLICATION_MODEL_GAP" not in pub:
    e.append("missing-server-proposal-state-not-recorded")
if "mayPresentAsPublic" not in pub:
    e.append("no-guard-on-presenting-material-as-public")
gate("G23", e)

# =========================================================== G24 final_publication_separation
# Approval must be unreachable by construction: no state transition, no action
# descriptor, no port method, and a total refusal.
e = []
e.extend(total_refusal(bnd, "ws04MayApprovePublication"))
e.extend(total_refusal(bnd, "proposalEqualsPublicApproved"))
if "ws04MayReachApproved" not in pub:
    e.append("no-total-reachability-refusal")
reach = function_body(pub, "ws04MayReachApproved")
if reach is not None and [r.strip() for r in re.findall(r"return\s+([^;]+);", reach)] != ["false"]:
    e.append("approval-reachability-refusal-not-total")
# WS-04 may originate only the two permitted states, and the list must say so.
originable = re.search(r"STATES_WS04_MAY_ORIGINATE = Object\.freeze\(\[([\s\S]*?)\]", bnd)
if originable is None:
    e.append("originable-state-list-missing")
elif "approved_by_publication_authority" in originable.group(1):
    e.append("approval-is-listed-as-originable-by-ws04")
transitions = re.search(r"const TRANSITIONS[\s\S]*?\n\}\);", pub)
if transitions is None:
    e.append("publication-transition-table-not-found")
elif "approved_by_publication_authority:" in transitions.group(0):
    body = transitions.group(0)
    for line in body.splitlines():
        if "approved_by_publication_authority" in line and "{}" not in line and ":" in line.split("approved_by_publication_authority")[1][:3]:
            pass
    if re.search(r':\s*"approved_by_publication_authority"', body):
        e.append("a-transition-reaches-approval")
ports = text(f"{WS}/runtime/ports.ts")
if re.search(r"\bapprove\s*:", ports):
    e.append("an-approval-port-method-exists")
# An approval action id may appear exactly where it is *forbidden* — inside
# FORBIDDEN_PUBLICATION_ACTION_IDS — and nowhere else. An earlier version of
# this check compared loose counts and let an added descriptor through.
forbidden_block = re.search(
    r"FORBIDDEN_PUBLICATION_ACTION_IDS = Object\.freeze\(\[([\s\S]*?)\]", pub
)
declared_block = re.search(
    r"PUBLICATION_ACTIONS: readonly ActionDescriptor\[\] = Object\.freeze\(\[([\s\S]*?)\n\]\);",
    pub,
)
for token in ("publication.approve", "publication.publish", "publication.release",
              "publication.force_publish", "publication.self_approve"):
    if declared_block and token in declared_block.group(1):
        e.append(f"approval-action-offered:{token}")
    for rel, body in PROD.items():
        if token in body and not rel.endswith("domain/publication.ts"):
            e.append(f"approval-action-id-used:{rel}:{token}")
if forbidden_block is None:
    e.append("forbidden-publication-action-list-missing")
gate("G24", e)

# =========================================================== G25 registry_custody_prohibition
e = []
bnd = text(f"{WS}/policies/boundaries.ts")
e.extend(total_refusal(bnd, "mayMutateRegistry"))
if "PROTECTED_REGISTRIES" not in bnd:
    e.append("no-protected-registry-list")
registry_port = re.search(r"RegistryReferencePort = \{([\s\S]*?)\n\};", ports)
if registry_port is None:
    e.append("registry-port-not-found")
else:
    body = registry_port.group(1)
    for verb in ("write", "create", "update", "delete", "mutate", "patch"):
        if re.search(rf"\b{verb}\s*:", body):
            e.append(f"registry-mutation-shape-exists:{verb}")
gate("G25", e)

# =========================================================== G26 eligibility_decision_prohibition
e = []
e.extend(total_refusal(bnd, "mayDecideEligibility"))
if "ELIGIBILITY_DECISIONS" not in bnd:
    e.append("no-eligibility-decision-list")
eligibility_port = re.search(r"EligibilityDisplayPort = \{([\s\S]*?)\n\};", ports)
if eligibility_port is None:
    e.append("eligibility-port-not-found")
elif re.search(r"\b(decide|grant|deny|approve)\s*:", eligibility_port.group(1)):
    e.append("an-eligibility-decision-shape-exists")
gate("G26", e)

# =========================================================== G27 commit_reauthorization
e = []
if "commitTimeRevalidationRequired" not in authority_src:
    e.append("no-commit-time-revalidation")
if "RevalidationNotice" not in text(f"{WS}/components/primitives.tsx"):
    e.append("no-revalidation-notice-primitive")
if "revalidationNotice" not in text(f"{WS}/content/de.ts"):
    e.append("revalidation-notice-has-no-text")
if "keine Berechtigung" not in text(f"{WS}/content/de.ts"):
    e.append("visible-control-not-denied-as-authorization")
gate("G27", e)

# =========================================================== G28 idempotency
e = []
if "retryToken" in ports or "idempotency" in ports.lower():
    pass
# At this baseline no mutation is executable, so the property to check is that
# no automatic retry of an unknown outcome exists anywhere.
for rel, body in CODE.items():
    if re.search(r"setTimeout\([^)]*retry", body, re.I) or re.search(r"\bwhile\s*\(true\)", body):
        e.append(f"automatic-retry-loop:{rel}")
if "Nicht erneut absenden" not in workflow:
    e.append("uncertain-outcome-does-not-warn-against-resubmission")
if "retryOfferedFor" not in workflow:
    e.append("no-explicit-retry-policy")
gate("G28", e)

# =========================================================== G29 concurrency
e = []
if "STALE_CASE" not in workflow:
    e.append("no-stale-version-outcome")
if "WS04-CASE-409" not in workflow:
    e.append("stale-version-not-distinguished")
if "preconditionFor" not in workflow:
    e.append("no-version-precondition-helper")
if "inFlight" not in text(f"{WS}/components/WorkspaceProvider.tsx"):
    e.append("no-single-in-flight-guard")
gate("G29", e)

# =========================================================== G30 degraded_mode
e = []
de = text(f"{WS}/content/de.ts")
if "intakePaused" not in de:
    e.append("degraded-mode-not-modelled")
if "fallback" not in de:
    e.append("no-governed-fallback-text")
if "GovernedFallback" not in text(f"{WS}/components/primitives.tsx"):
    e.append("no-governed-fallback-primitive")
missing_fallback = [
    name
    for name in (
        "DeskSurface", "CaseDetailSurface", "PositionSurface", "DeviationSurface",
        "DeclarationSurface", "PublicationSurface", "ConflictSurface", "HomeSurface",
    )
    if "GovernedFallback" not in text(f"{WS}/components/{name}.tsx")
]
if missing_fallback:
    e.append(f"surfaces-without-a-governed-fallback:{missing_fallback}")
gate("G30", e)

# =========================================================== G31 browser_storage
e = []
if "storageAllowed" not in ws_policy:
    e.append("no-storage-policy-function")
if "permittedPurposes" not in ws_policy:
    e.append("no-closed-purpose-list")
storage_body = function_body(ws_policy, "storageAllowed")
if storage_body is None:
    e.append("storage-policy-body-unreadable")
elif "if (!permitted.includes(purpose)) return false;" not in storage_body:
    e.append("storage-purpose-check-inverted-or-removed")
for rel, body in CODE.items():
    if re.search(r"\b(localStorage|sessionStorage|indexedDB)\b", body) and "policies/" not in rel:
        e.append(f"storage-api-used-outside-policy:{rel}")
gate("G31", e)

# =========================================================== G32 service_worker_cache
e = []
if "serviceWorkerRegisteredByThisPackage: false" not in ws_policy:
    e.append("service-worker-position-not-declared")
for rel, body in CODE.items():
    if re.search(r"serviceWorker\s*\.\s*register", body):
        e.append(f"service-worker-registered:{rel}")
    if re.search(r"\bcaches\s*\.", body):
        e.append(f"cache-storage-used:{rel}")
if exists(f"{WS}/public/sw.js") or exists(f"{WS}/app/sw.ts"):
    e.append("a-service-worker-file-ships")
gate("G32", e)

# =========================================================== G33 privacy_telemetry
e = []
if "TELEMETRY_ALLOWED_FIELDS" not in conf:
    e.append("no-telemetry-allowlist")
if "TELEMETRY_PLATFORM_CONNECTED = false" not in conf:
    e.append("telemetry-platform-claimed-connected")
if "if (!TELEMETRY_PLATFORM_CONNECTED) return false;" not in conf:
    e.append("telemetry-does-not-fail-closed")
if "carriesCaseContent: false" not in conf:
    e.append("error-reporting-may-carry-case-content")
for rel, body in CODE.items():
    for pattern in (r"\bgtag\s*\(", r"\bdataLayer\b", r"\bplausible\s*\(", r"\b_paq\b"):
        if re.search(pattern, body, re.I):
            e.append(f"analytics-call:{rel}")
gate("G33", e)

# =========================================================== G34 scoped_search
e = []
if "SEARCH_POLICY" not in conf:
    e.append("no-search-policy")
if "crossMandateSearch: false" not in conf:
    e.append("cross-mandate-search-not-prohibited")
if "searchRequestAdmissible" not in scope_src:
    e.append("no-search-admissibility-check")
for rel, body in PROD.items():
    if re.search(r'<input[^>]*type="search"', body) or 'role="search"' in body:
        e.append(f"a-search-surface-is-rendered:{rel}")
    if re.search(r'<input[^>]*name="q"', body):
        e.append(f"an-unscoped-query-field-is-rendered:{rel}")
search_port = re.search(r"search:\s*\(([\s\S]*?)\) =>", ports)
if search_port is None:
    e.append("search-port-not-found")
elif "ScopeBound" not in search_port.group(1):
    e.append("search-port-is-not-scope-bound")
gate("G34", e)

# ---------------------------------------------------------------- evidence helpers
def evidence(step: str) -> dict[str, Any] | None:
    return load(f"{EVIDENCE_DIR}/{step}.json")


def raw_result(step: str, record: dict[str, Any]) -> tuple[str, list[str]]:
    """Re-derive a step's outcome from its own raw log rather than reading it.

    The trailer is inside the hashed bytes, so a summary that claims PASS while
    its log records a non-zero exit is caught here, and editing the log to agree
    breaks the hash checked alongside.
    """
    problems: list[str] = []
    rel = record.get("raw_report_path", "")
    path = R / rel
    if not path.is_file():
        return "MISSING", [f"raw-log-missing:{step}"]
    body = path.read_text(encoding="utf-8", errors="replace")
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha != record.get("raw_report_sha256"):
        problems.append(f"raw-log-hash-mismatch:{step}")
    m = re.search(
        rf"^{RAW_TRAILER} command=(\S+) exit_code=(-?\d+) finished_at=(\S+)\s*$",
        body,
        re.M,
    )
    if m is None:
        return "NO_TRAILER", problems + [f"raw-log-has-no-result-trailer:{step}"]
    if m.group(1) != step:
        problems.append(f"raw-log-trailer-names-another-step:{step}:{m.group(1)}")
    derived = "PASS" if m.group(2) == "0" else "FAIL"
    if derived != record.get("result"):
        problems.append(
            f"recorded-result-contradicts-raw-log:{step}:"
            f"{record.get('result')}!={derived}"
        )
    return derived, problems


REQUIRED_STEPS = [e["id"] for e in CONTRACT.get("required_evidence", [])]
ADVISORY_STEPS = {"dependency_audit"}

# =========================================================== G35 accessibility
e = []
browser = evidence("browser")
if browser is None:
    e.append("browser-evidence-missing")
else:
    if browser.get("result") != "PASS":
        e.append("browser-suite-did-not-pass")
    if browser.get("failed", 0) != 0:
        e.append(f"browser-failures:{browser.get('failed')}")
spec = text(f"{WS}/tests/browser/front05.browser.spec.ts")
if "@a11y" not in spec:
    e.append("no-accessibility-assertions")
if "AxeBuilder" not in spec:
    e.append("axe-not-used")
if "serious" not in spec or "critical" not in spec:
    e.append("axe-impact-threshold-not-enforced")
if "skip link" not in spec.lower():
    e.append("skip-link-not-exercised")
gate("G35", e)

# =========================================================== G36 responsive
e = []
pw = text(f"{WS}/playwright.config.ts")
for project in ("mobile", "desktop", "wide"):
    if f'name: "{project}"' not in pw:
        e.append(f"viewport-project-missing:{project}")
if "does not scroll the document horizontally" not in spec:
    e.append("no-reflow-assertion")
if "setViewportSize({ width: 320" not in spec:
    e.append("reflow-not-checked-at-320px")
gate("G36", e)

# =========================================================== G37 i18n
e = []
lang = text(f"{WS}/policies/language.ts")
if "localeAffects" not in lang:
    e.append("no-locale-neutrality-function")
if "LOCALE_CHANGES_NOTHING_ABOUT" not in lang:
    e.append("no-locale-neutrality-list")
if 'AUTHORITATIVE_LOCALE: Locale = "de"' not in lang:
    e.append("authoritative-locale-not-german")
lang_test = text(f"{WS}/tests/front05.language.test.ts")
if "byte-identical under both locales" not in lang_test:
    e.append("locale-neutrality-asserted-but-not-demonstrated")
gate("G37", e)

# =========================================================== G38 real_build
e = []
for step in ("build", "build_production_profile"):
    record = evidence(step)
    if record is None:
        e.append(f"build-evidence-missing:{step}")
        continue
    if record.get("result") != "PASS":
        e.append(f"build-failed:{step}")
    derived, problems = raw_result(step, record)
    e.extend(problems)
for step in ("typecheck", "lint", "format"):
    record = evidence(step)
    if record is None:
        e.append(f"static-evidence-missing:{step}")
    elif record.get("result") != "PASS":
        e.append(f"static-step-failed:{step}")
gate("G38", e)

# =========================================================== G39 browser_e2e
e = []
for step in ("browser", "browser_production", "visual", "authorization_negative"):
    record = evidence(step)
    if record is None:
        e.append(f"evidence-missing:{step}")
        continue
    if record.get("result") != "PASS":
        e.append(f"suite-failed:{step}")
    if record.get("passed", 0) == 0:
        e.append(f"suite-ran-nothing:{step}")
    derived, problems = raw_result(step, record)
    e.extend(problems)
prod_spec = text(f"{WS}/tests/browser/front05.production.browser.spec.ts")
if "the workspace still hydrates under the production CSP" not in prod_spec:
    e.append("hydration-not-asserted-under-the-production-policy")
gate("G39", e)

# =========================================================== G40 voting_boundary
e = []
e.extend(total_refusal(bnd, "votingDomainAccessAvailableFor"))
if "VOTING_DOMAIN_PROHIBITIONS" not in bnd:
    e.append("no-voting-prohibition-list")
# A voting token appearing inside a prohibition list is the prohibition doing
# its job. What must not exist is a voting-domain identifier used as a value: a
# field, a parameter, a property access.
for token in ("ballotId", "ballot_id", "confirmationCode", "confirmation_code",
              "retryToken", "retry_token", "tally", "intermediateResult"):
    for rel, body in CODE.items():
        if re.search(rf"\b{token}\b", body):
            e.append(f"voting-domain-identifier-used:{rel}:{token}")
for prohibited in ("ballot", "tally", "vote"):
    if prohibited not in bnd.lower():
        e.append(f"voting-prohibition-list-does-not-mention:{prohibited}")
if "votingBoundary" not in de:
    e.append("voting-boundary-not-stated-to-the-operator")
gate("G40", e)

# =========================================================== G41 dependency_reconciliation
e = []
if not DEPS:
    e.append("dependency-reconciliation-missing")
else:
    for key, expected in (
        ("no_security_sensitive_capability_is_supported", True),
        ("no_security_sensitive_capability_is_a_declared_limitation", True),
        ("every_security_sensitive_capability_states_a_finding", True),
        ("caller_asserted_authorization_treated_as_sufficient", False),
    ):
        if DEPS.get("assertions", {}).get(key) is not expected:
            e.append(f"dependency-assertion-wrong:{key}")
    if not DEPS.get("absent_dependencies"):
        e.append("no-absent-dependencies-recorded")
audit = evidence("dependency_audit")
if audit is None:
    e.append("dependency-audit-evidence-missing")
else:
    findings = load("validation/front05/dependency_findings.json")
    if findings is None:
        e.append("dependency-findings-disposition-missing")
    else:
        permitted = {
            "NOT_REACHABLE_IN_PRODUCTION_BUNDLE",
            "BUILD_TIME_ONLY",
            "FIXED",
            "REMOVED_BY_CONFIGURATION",
            "DEFERRED_TO_OWNING_SECURITY_STAGE",
            "ACCEPTED_RISK_WITH_NAMED_OWNER",
        }
        # A disposition is only as good as what backs it. Every one must name
        # its evidence and a future owner, and the reachability claim must be a
        # measurement rather than an assertion: "not in the bundle" is only
        # admissible when the bundle was actually scanned.
        if findings.get("client_bundle_scan", {}).get("matches_per_package") is None:
            e.append("no-client-bundle-scan-behind-the-dispositions")
        for row in findings.get("findings", []):
            if row.get("disposition") == "NOT_REACHABLE_IN_PRODUCTION_BUNDLE":
                if row.get("client_bundle_name_matches", -1) != 0:
                    e.append(f"unreachability-claimed-without-a-clean-scan:{row.get('package')}")
            if not row.get("future_owner"):
                e.append(f"disposition-without-an-owner:{row.get('package')}")
            if len(row.get("exploit_preconditions", "")) < 40:
                e.append(f"disposition-without-stated-preconditions:{row.get('package')}")
        for row in findings.get("findings", []):
            for field in (
                "package", "advisory", "severity", "dependency_path",
                "runtime_or_build_time", "reachable_in_production_bundle",
                "disposition", "evidence",
            ):
                if field not in row:
                    e.append(f"finding-field-missing:{row.get('package')}:{field}")
            if row.get("disposition") not in permitted:
                e.append(f"disposition-not-permitted:{row.get('package')}")
gate("G41", e)

# =========================================================== G42 mutation_suite
e = []
report = load("validation/front05/mutation_report.json")
minimum = CONTRACT.get("minimum_mutation_count", 40)
if report is None:
    e.append("mutation-report-missing")
else:
    mutations = report.get("mutations", [])
    if len(mutations) < minimum:
        e.append(f"too-few-mutations:{len(mutations)}<{minimum}")
    undetected = [m["id"] for m in mutations if not m.get("detected")]
    if undetected:
        e.extend(f"mutation-not-detected:{m}" for m in undetected)
    for m in mutations:
        if not m.get("detecting_gates"):
            e.append(f"mutation-without-a-detecting-gate:{m.get('id')}")
    if report.get("baseline_source_tree_digest") != CURRENT["source_tree_digest"]:
        e.append("mutation-report-bound-to-another-source-tree")
gate("G42", e)

# =========================================================== G43 archive_hygiene
#
# Hygiene is a property of a *file set*, so this gate checks a file set rather
# than trusting a manifest. Which file set depends on where the validator is
# running, and the difference is detected rather than assumed:
#
#  * In a working tree, `node_modules` and `.next` legitimately exist — they are
#    excluded from the archive, not from the checkout — so the archive's contents
#    can only be judged through the manifest the sealing step wrote.
#  * In a tree extracted from the archive, those directories are absent, so the
#    tree *is* the archive and can be walked directly.
#
# An earlier version passed trivially whenever the manifest was missing, which is
# precisely the situation a reviewer re-validating from the sealed bytes is in:
# the gate would have reported PASS having checked nothing.
e = []
FORBIDDEN_DIRS = (
    "node_modules", ".next", "test-results", "playwright-report",
    "coverage", "__pycache__", ".turbo", ".swc", ".venv",
)
FORBIDDEN_SUFFIXES = (".env", ".pem", ".key", ".p12", ".pfx", ".pyc")
staged = load("validation/front05/archive_manifest.json")
in_working_tree = (R / "node_modules").is_dir() or (R / f"{WS}/.next").is_dir()


def hygiene_problems(names) -> list[str]:
    problems = []
    for name in names:
        parts = name.split("/")
        for bad in FORBIDDEN_DIRS:
            if bad in parts:
                problems.append(f"forbidden-path:{name}")
                break
        if name.endswith(FORBIDDEN_SUFFIXES):
            problems.append(f"secret-shaped-or-generated-file:{name}")
    return problems


if in_working_tree:
    if staged is None:
        e.append("archive-manifest-missing-so-hygiene-is-unverified")
    else:
        e.extend(hygiene_problems(staged.get("entries", [])))
        if staged.get("entry_count", 0) < 100:
            e.append("archive-implausibly-small")
        # The three self-describing artifacts must be absent from the archive
        # they describe. Their presence would also make the seal
        # non-deterministic, which the manifest claims it is not.
        for self_describing in (
            staged.get("filename", ""),
            f"{staged.get('filename', '')}.sha256",
            "validation/front05/archive_manifest.json",
        ):
            if self_describing and self_describing in staged.get("entries", []):
                e.append(f"self-describing-artifact-sealed-inside:{self_describing}")
else:
    walked = [
        str(p.relative_to(R).as_posix())
        for p in R.rglob("*")
        if p.is_file()
    ]
    if len(walked) < 100:
        e.append("extracted-tree-implausibly-small")
    e.extend(hygiene_problems(walked))
    # In an extract the manifest is optional — it ships beside the archive — but
    # if a reviewer placed it here, it must agree with what is actually present.
    if staged is not None:
        missing = sorted(set(staged.get("entries", [])) - set(walked))
        if missing:
            e.append(f"manifest-lists-entries-absent-from-the-tree:{missing[:3]}")
gates["G43"] = {"status": "PASS" if not e else "FAIL", "errors": e}
gates["G43"]["checked"] = "manifest" if in_working_tree else "extracted-tree"

# =========================================================== G44 same_bytes_identity
e = []
integrity = load("validation/front05/verification_integrity.json")
if integrity is None:
    e.append("verification-integrity-missing")
else:
    if integrity.get("source_unchanged_by_verification") is not True:
        e.append("verification-mutated-the-source-tree")
    if integrity.get("source_tree_digest_after") != CURRENT["source_tree_digest"]:
        e.append("source-tree-changed-after-verification")
    if integrity.get("files_changed_during_verification"):
        e.append(f"files-changed:{integrity['files_changed_during_verification']}")
# Every authoritative record must be bound to the tree that is here now.
for step in REQUIRED_STEPS:
    record = evidence(step)
    if record is None:
        e.append(f"evidence-missing:{step}")
        continue
    if record.get("source_tree_digest") != CURRENT["source_tree_digest"]:
        e.append(f"SOURCE_TREE_EVIDENCE_MISMATCH:{step}")
    if record.get("test_source_digest") != CURRENT["test_source_digest"]:
        e.append(f"TEST_SOURCE_EVIDENCE_MISMATCH:{step}")
    if record.get("configuration_digest") != CURRENT["config_digest"]:
        e.append(f"CONFIG_EVIDENCE_MISMATCH:{step}")
    if record.get("package_lock_sha256") != CURRENT["package_lock_sha256"]:
        e.append(f"LOCKFILE_EVIDENCE_MISMATCH:{step}")
    for field in CONTRACT.get("evidence_binding_fields", []):
        if field not in record:
            e.append(f"binding-field-missing:{step}:{field}")
    derived, problems = raw_result(step, record)
    e.extend(problems)
    if step not in ADVISORY_STEPS and record.get("result") != "PASS":
        e.append(f"authoritative-step-not-pass:{step}")
# No competing authoritative result may sit alongside the real one.
authoritative = CONTRACT.get("authoritative_result_path", "")
for candidate in sorted((R / "validation/front05").glob("*result*.json")):
    rel = str(candidate.relative_to(R))
    if rel != authoritative:
        e.append(f"competing-authoritative-result:{rel}")
gate("G44", e)

# =========================================================== G45 report_identity_crosscheck
#
# The gate that would have caught my own FRONT-04 C2 rejection.
#
# That archive was rejected and resealed because the developer report quoted a
# `source_tree_digest` from the penultimate run while the sealed tree carried
# another. The report sat outside the digest-covered boundary — necessarily, since
# it quotes the digest of the tree that contains it — so no gate looked at it, and
# a reviewer had to notice by eye. This gate reads every 64-hex digest and every
# byte size the report quotes and requires each to appear in the evidence.
e = []
report_path = args.report
report_text = text(report_path)
if not report_text:
    e.append(f"developer-report-missing:{report_path}")
else:
    # The set of identity values the evidence chain actually holds.
    known_digests: set[str] = {
        CURRENT["source_tree_digest"],
        CURRENT["test_source_digest"],
        CURRENT["config_digest"],
        CURRENT["validator_source_digest"],
        CURRENT["contract_digest"],
        CURRENT["package_lock_sha256"],
        FRONT04_C2_SHA,
        FRONT04_C2_TREE,
        FRONT03_C1_SHA,
        FRONT02_C21_SHA,
    }
    for step in REQUIRED_STEPS:
        record = evidence(step)
        if record:
            known_digests.add(record.get("raw_report_sha256", ""))
            known_digests.add(record.get("source_tree_digest", ""))
    for extra in ("preseal_identity.json", "lineage.json", "source_delta.json",
                  "authoritative_preseal_result.json", "archive_manifest.json"):
        payload = load(f"validation/front05/{extra}")
        if payload:
            known_digests |= {
                v for v in re.findall(r"\b[0-9a-f]{64}\b", json.dumps(payload))
            }
    known_digests.discard("")

    quoted = set(re.findall(r"\b[0-9a-f]{64}\b", report_text))
    unknown = sorted(quoted - known_digests)
    for value in unknown:
        e.append(f"report-quotes-a-digest-absent-from-the-evidence:{value[:16]}…")

    # Any digest the report labels as the source tree must be *the* source tree.
    for match in re.finditer(
        r"(source[_ ]tree[_ ]digest|Quell(?:baum)?[- ]?Digest)\D{0,40}?([0-9a-f]{64})",
        report_text,
        re.I,
    ):
        if match.group(2) != CURRENT["source_tree_digest"]:
            e.append("report-source-tree-digest-is-stale")

    # The report must not quote the archive's own sha256 or size. It cannot do so
    # correctly — the report is sealed inside the archive, so any such value would
    # describe a different archive — and quoting one anyway is the exact shape of
    # the FRONT-04 C2 defect. The identity belongs in the detached sidecar, the
    # archive manifest and the terminal marker, all of which sit outside the bytes
    # they describe.
    manifest = load("validation/front05/archive_manifest.json")
    if manifest:
        if str(manifest.get("sha256", "")) and str(manifest["sha256"]) in report_text:
            e.append("report-quotes-the-archive-sha-it-is-sealed-inside")
        size = str(manifest.get("size_bytes", ""))
        if size and re.search(rf"\b{re.escape(size)}\b", report_text):
            e.append("report-quotes-the-archive-size-it-is-sealed-inside")

    # The report may not assert acceptance — but it is required to *disown* the
    # forbidden claims, and an earlier version of this gate failed the report for
    # doing exactly that. So the disclaimer list is fenced, the fence is excluded
    # from the claim scan, and the fence itself is checked to contain nothing but
    # the stage contract's own non-claims. A claim smuggled inside the fence is
    # therefore caught by the fence check rather than escaping through it.
    fence = re.search(
        r"<!-- front05:non-claims:start -->([\s\S]*?)<!-- front05:non-claims:end -->",
        report_text,
    )
    if fence is None:
        e.append("report-has-no-non-claims-fence")
        scanned = report_text
    else:
        permitted = {c.strip().lower() for c in CONTRACT.get("non_claims", [])}
        for line in fence.group(1).splitlines():
            item = line.strip().lstrip("-").strip()
            if not item:
                continue
            if item.lower() not in permitted:
                e.append(f"non-claims-fence-contains-something-else:{item[:60]}")
        scanned = report_text.replace(fence.group(0), "")
    for claim in CONTRACT.get("forbidden_claim_strings", []):
        if re.search(re.escape(claim), scanned, re.I):
            e.append(f"report-makes-a-forbidden-claim:{claim}")
gate("G45", e)

# =========================================================== G46 security_sensitive_dependency_discipline
#
# A dependency that is missing and a dependency that is defective are different
# findings. `transparency-service` authorises publication by a caller-supplied
# `actor_is_authorized` boolean, which is a self-asserted authorization: the
# caller declares its own permission and the service accepts the declaration.
# Recorded as a neutral gap, that would invite a later round to add a proposal
# route over the top of it and mark the capability supported — inheriting the
# defect. This gate keeps the classification load-bearing.
e = []
ssd = CONTRACT.get("security_sensitive_dependencies", {})
if not ssd:
    e.append("contract-declares-no-security-sensitive-dependency-discipline")
else:
    if not ssd.get("boundaries"):
        e.append("no-security-sensitive-boundary-recorded")
    for boundary in ssd.get("boundaries", []):
        for field in (
            "id", "owner", "capabilities", "observed", "finding",
            "front05_position", "insufficient_remedies",
            "unblocking_condition", "status_until_then", "escalation",
        ):
            if not boundary.get(field):
                e.append(f"boundary-field-missing:{boundary.get('id')}:{field}")
        if len(boundary.get("finding", "")) < 100:
            e.append(f"boundary-finding-not-substantive:{boundary.get('id')}")

declared = {
    cap
    for boundary in ssd.get("boundaries", [])
    for cap in boundary.get("capabilities", [])
}
flagged = {
    c["id"]
    for c in CAPS.get("capabilities", [])
    if c.get("dependencyClass") == "SECURITY_SENSITIVE_BOUNDARY"
}
if declared != flagged:
    e.append(f"contract-and-register-disagree:{sorted(declared ^ flagged)}")

for cap in CAPS.get("capabilities", []):
    cls = cap.get("dependencyClass")
    if cls not in ("ABSENT", "SECURITY_SENSITIVE_BOUNDARY", "PROHIBITED"):
        e.append(f"dependency-class-outside-vocabulary:{cap.get('id')}:{cls}")
    if cls != "SECURITY_SENSITIVE_BOUNDARY":
        if cap.get("securityFinding"):
            e.append(f"security-finding-on-an-unflagged-capability:{cap.get('id')}")
        continue
    # The rule itself.
    if cap.get("status") not in ("BLOCKED_BY_DEPENDENCY", "UNSUPPORTED"):
        e.append(f"security-sensitive-capability-is-supported:{cap.get('id')}")
    if cap.get("status") == "SUPPORTED_WITH_DECLARED_LIMITATION":
        e.append(f"security-sensitive-capability-recorded-as-a-limitation:{cap.get('id')}")
    if len(cap.get("securityFinding", "")) < 100:
        e.append(f"security-sensitive-capability-without-a-finding:{cap.get('id')}")

# The defect cannot be inherited if there is nowhere in the code to put it.
for rel, body in CODE.items():
    if re.search(r"\b(actor_is_authorized|actorIsAuthorized|isAuthorized)\s*[:,)=]", body):
        e.append(f"caller-asserted-authorization-field-in-source:{rel}")
if "callerAssertedAuthorizationSufficient" not in pub:
    e.append("no-total-refusal-of-caller-asserted-authorization")
if "securitySensitiveBoundariesRespected" not in text(f"{WS}/domain/capabilities.ts"):
    e.append("classification-not-enforced-at-module-load")
if 'classification: "SECURITY_SENSITIVE_BOUNDARY"' not in pub:
    e.append("publication-gap-not-classified-as-security-sensitive")

# It must reach the reviewer as a finding, not only as a code comment.
recon = text("docs/frontend/FRONT-05-PACK-DEPENDENCY-RECONCILIATION.md")
if "self-asserted authorization" not in recon:
    e.append("security-finding-absent-from-the-reconciliation-document")
if "Remedies that would not resolve it" not in recon:
    e.append("insufficient-remedies-not-published")
gate("G46", e)

# ---------------------------------------------------------------- output
passed = sum(1 for g in gates.values() if g["status"] == "PASS")
ok = passed == len(gates)
result = {
    "schema": "epd2.front05.authoritative-candidate-result/1",
    "stage": "FRONT-05 — WS-04 Representative Workspace",
    "candidate_state": "CANDIDATE_NOT_ACCEPTED",
    "authority": "AUTHORITATIVE",
    "self_acceptance": False,
    "state": "PASS_FOR_INDEPENDENT_ACCEPTANCE" if ok else "FAIL",
    "acceptance_meaning": CONTRACT.get("acceptance_meaning", ""),
    "stage_contract": {
        "path": CONTRACT_JSON,
        "contract_version": CONTRACT.get("contract_version"),
        "contract_digest": CURRENT["contract_digest"],
        "ratification_status": (CONTRACT.get("ratification") or {}).get("status_in_candidate"),
        "canonically_opened_stage": (CONTRACT.get("governance_state") or {})
        .get("stage_opening", {})
        .get("canonically_opened"),
    },
    "binding": {
        "source_tree_digest": CURRENT["source_tree_digest"],
        "test_source_digest": CURRENT["test_source_digest"],
        "configuration_digest": CURRENT["config_digest"],
        "validator_source_digest": CURRENT["validator_source_digest"],
        "package_lock_sha256": CURRENT["package_lock_sha256"],
        "source_file_count": CURRENT["file_count"],
    },
    "gates_total": len(gates),
    "gates_passed": passed,
    "status": "PASS" if ok else "FAIL",
    "note": (
        "PASS_FOR_INDEPENDENT_ACCEPTANCE is the highest assertion a candidate-run "
        "validator may make. It is not acceptance. Independent governed review "
        "on the sealed bytes and a post-run governance record own that decision."
    ),
    "gates": gates,
}
serialised = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
if args.output:
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(serialised, encoding="utf-8")
print(serialised)
sys.exit(0 if result["status"] == "PASS" else 1)

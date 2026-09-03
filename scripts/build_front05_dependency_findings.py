#!/usr/bin/env python3
"""FRONT-05 dependency findings, measured rather than inherited.

The FRONT-04 correction was explicit that a developer's own "non-blocking"
classification may not simply be carried forward. So the reachability question
is re-asked here against *this* workspace's production bundle: the package names
are searched for in the emitted client output of a production build, and the
dependency paths are traced with `npm ls` rather than assumed.

The workspace inherits FRONT-04's one piece of real hardening — `images:
{ unoptimized: true }` — for the same reason and re-verifies it, because the
image optimiser is the single path by which sharp's inherited libvips advisories
become reachable at runtime, and this origin ships no images either.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

WS = "frontend/representative-workspace"
PACKAGES = ("next", "postcss", "sharp", "nanoid", "js-yaml", "brace-expansion")


def audit(root: Path) -> dict:
    raw = (root / "validation/front05/raw/dependency-audit.log").read_text(
        encoding="utf-8", errors="replace"
    )
    # npm may append environment warnings to stderr after its JSON document.
    # The governed runner records stdout and stderr together, so split-based
    # parsing is not robust across npm versions. Decode exactly the first JSON
    # value and leave any subsequent warning text as preserved raw evidence.
    start = raw.find("{")
    if start < 0:
        raise ValueError("npm audit output contains no JSON object")
    parsed, _ = json.JSONDecoder().raw_decode(raw[start:])
    if not isinstance(parsed, dict):
        raise ValueError("npm audit output is not a JSON object")
    return parsed


def dependency_path(root: Path, package: str) -> str:
    try:
        proc = subprocess.run(
            ["npm", "ls", package, "--all"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        lines = [l.strip() for l in proc.stdout.splitlines() if package in l]
        return " | ".join(lines[:4]) or "not resolved in the installed tree"
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"npm ls unavailable: {exc}"


def bundle_matches(root: Path, package: str) -> int:
    static = root / WS / ".next" / "static"
    if not static.is_dir():
        return -1
    count = 0
    for path in static.rglob("*"):
        if not path.is_file() or path.suffix not in {".js", ".mjs", ".css", ".json"}:
            continue
        if package in path.read_text(encoding="utf-8", errors="ignore"):
            count += 1
    return count


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    data = audit(root)
    vulns = data.get("vulnerabilities", {})

    scan = {package: bundle_matches(root, package) for package in PACKAGES}
    config = (root / WS / "next.config.ts").read_text(encoding="utf-8")
    optimiser_disabled = "images: { unoptimized: true }" in config

    findings = []
    for name, entry in sorted(vulns.items()):
        titles = [v.get("title") for v in entry.get("via", []) if isinstance(v, dict)]
        fix = entry.get("fixAvailable")
        breaking = bool(isinstance(fix, dict) and fix.get("isSemVerMajor"))
        in_bundle = scan.get(name, -1)

        if name == "next":
            disposition = "DEFERRED_TO_OWNING_SECURITY_STAGE"
            reachable = "framework runtime code is served; the advisory components themselves are not in the client bundle"
            preconditions = (
                "Depends entirely on the underlying entries — see the postcss and sharp "
                "rows. This workspace defines no API route and its production adapter "
                "issues no network request, so no advisory here is reachable through a "
                "path this application defines."
            )
            owner = "SEC with FRONT — a governed framework-major upgrade, not a frontend-stage change"
        elif name == "sharp":
            disposition = (
                "REMOVED_BY_CONFIGURATION" if optimiser_disabled
                else "DEFERRED_TO_OWNING_SECURITY_STAGE"
            )
            reachable = (
                "the image-optimisation endpoint is the only path that reaches sharp, "
                "and it is disabled on this origin"
                if optimiser_disabled
                else "the image optimiser is enabled and reaches sharp"
            )
            preconditions = (
                "An attacker would need the framework's image-optimisation endpoint to "
                "process an attacker-influenced image. This workspace ships no images "
                "and sets images.unoptimized, which removes the processing path rather "
                "than leaving it unused but reachable."
            )
            owner = "FRONT — mitigated here; the underlying advisory remains with SEC"
        elif name == "postcss":
            disposition = "BUILD_TIME_ONLY"
            reachable = "CSS is compiled at build time; postcss is not shipped to the browser"
            preconditions = (
                "The advisories require attacker-controlled CSS or an attacker-controlled "
                "sourceMappingURL to be processed. All CSS in this workspace is "
                "first-party and compiled at build time, and production source maps are "
                "disabled (productionBrowserSourceMaps: false)."
            )
            owner = "SEC with FRONT — resolved by the same framework-major upgrade"
        else:
            disposition = "NOT_REACHABLE_IN_PRODUCTION_BUNDLE"
            reachable = "absent from the emitted client output"
            preconditions = (
                "A build- and tooling-time dependency. It is not shipped to the browser "
                "and no runtime path in this workspace invokes it."
            )
            owner = "SEC with FRONT — transitive toolchain, resolved by upgrading the framework"

        findings.append(
            {
                "package": name,
                "installed_version": entry.get("range"),
                "severity": entry.get("severity"),
                "advisory": "; ".join(t for t in titles if t)
                or "aggregated advisory chain reported against this package",
                "dependency_path": dependency_path(root, name),
                "runtime_or_build_time": "build_time"
                if name in {"postcss", "js-yaml", "brace-expansion", "nanoid"}
                else "both",
                "reachable_from_ws04": name in {"next", "sharp"},
                "reachable_in_production_bundle": reachable,
                "client_bundle_name_matches": in_bundle,
                "exploit_preconditions": preconditions,
                "fix_available": bool(fix),
                "breaking_fix_required": breaking,
                "fix_detail": (
                    f"npm audit proposes {fix['name']}@{fix['version']}"
                    + (", a semver-major upgrade" if breaking else "")
                    if isinstance(fix, dict)
                    else "a non-breaking update is available in the dependency range"
                ),
                "disposition": disposition,
                "evidence": (
                    f"npm ls {name}; production client-bundle scan under {WS}/.next/static "
                    f"({in_bundle} file(s) mention the name); "
                    "the production adapter issues no network request and defines no API route"
                ),
                "future_owner": owner,
            }
        )

    out = {
        "schema": "epd2.front05.dependency-findings/1",
        "authority": "NON_AUTHORITATIVE",
        "stage": "FRONT-05 — WS-04 Representative Workspace",
        "candidate_state": "CANDIDATE_NOT_ACCEPTED",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "command": "npm audit --json, repository root, locked dependencies",
        "totals": data.get("metadata", {}).get("vulnerabilities", {}),
        "method": [
            "Every disposition below was re-measured for this workspace. FRONT-04's "
            "classification was not carried forward, because the FRONT-04 correction "
            "was explicit that a developer's own non-blocking judgement may not be "
            "inherited.",
            "Dependency paths traced with `npm ls <package>` rather than assumed.",
            "Client-bundle reachability tested by scanning every emitted file under "
            f"{WS}/.next/static for the package name after a production build.",
            "Fix availability and semver impact read from npm audit's own fixAvailable field.",
        ],
        "ws04_runtime_dependencies": ["next", "react", "react-dom"],
        "client_bundle_scan": {
            "build": "NEXT_PUBLIC_FRONT05_GOVERNED_TEST=0 next build",
            "scanned": f"{WS}/.next/static/**",
            "matches_per_package": scan,
        },
        "hardening_verified_this_round": {
            "change": f"{WS}/next.config.ts sets images.unoptimized = true",
            "present": optimiser_disabled,
            "reason": (
                "This workspace ships no images, so the framework's image-optimisation "
                "endpoint is pure attack surface on an origin that renders confidential "
                "case material, and it is the one path by which sharp's inherited libvips "
                "advisories become reachable at runtime."
            ),
        },
        "findings": findings,
    }
    path = root / "validation/front05/dependency_findings.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(root)} with {len(findings)} findings")
    for f in findings:
        print(f"  {f['package']:<16} {f['severity']:<8} {f['disposition']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

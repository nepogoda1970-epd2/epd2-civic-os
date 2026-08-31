from __future__ import annotations

import json
import pathlib
import sys

C9_ROOT = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C9"
C9_ZIP = C9_ROOT + ".zip"
C10_ROOT = "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C10"
C10_ZIP = C10_ROOT + ".zip"
OLD_INV = "docs/api/API-02/API02_C8_TO_C9_CORRECTION_INVENTORY.json"
NEW_INV = "docs/api/API-02/API02_C9_TO_C10_CORRECTION_INVENTORY.json"


def current_candidate_dict(d: dict) -> bool:
    for key in ("candidate_root", "candidate_filename"):
        v = d.get(key)
        if isinstance(v, str) and (v == C9_ROOT or v == C9_ZIP):
            return True
    root = d.get("root")
    filename = d.get("filename")
    if isinstance(root, str) and root == C9_ROOT:
        return True
    if isinstance(filename, str) and filename == C9_ZIP:
        # Entering-baseline records also have filename=C9; exclude explicit entering roles.
        if str(d.get("status", "")).startswith("CORRECTED_BY_THIS_CANDIDATE"):
            return False
        if d.get("role") == "C9" and any(k in d for k in ("version", "root", "classification")):
            return True
    return False


def walk_current(v):
    if isinstance(v, dict):
        is_current = current_candidate_dict(v)
        if is_current:
            if v.get("candidate_root") == C9_ROOT:
                v["candidate_root"] = C10_ROOT
            if v.get("candidate_filename") == C9_ZIP:
                v["candidate_filename"] = C10_ZIP
            if v.get("root") == C9_ROOT:
                v["root"] = C10_ROOT
            if v.get("filename") == C9_ZIP:
                v["filename"] = C10_ZIP
            if v.get("role") == "C9":
                v["role"] = "C10"
            if v.get("version") == "0.1_C9":
                v["version"] = "0.1_C10"
        for x in v.values():
            walk_current(x)
    elif isinstance(v, list):
        for x in v:
            walk_current(x)


def walk_titles(v):
    if isinstance(v, dict):
        for k, x in list(v.items()):
            if isinstance(x, str):
                if x == "Exact C5 -> API02-C9 transition inventory and the C8 -> C9 correction record":
                    v[k] = "Exact accepted-predecessor transition inventory and current correction record"
                elif x == "Exact C5 → API02-C9 transition inventory and the C8 → C9 correction record":
                    v[k] = "Exact accepted-predecessor transition inventory and current correction record"
            else:
                walk_titles(x)
    elif isinstance(v, list):
        for x in v:
            walk_titles(x)


def patch_validation(root: pathlib.Path) -> None:
    for p in (root / "validation/api02").glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        walk_current(d)
        walk_titles(d)
        p.write_text(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def patch_lineage(root: pathlib.Path) -> None:
    p = root / "docs/api/API-02/API02_LINEAGE.json"
    d = json.loads(p.read_text())

    def walk(v):
        if isinstance(v, dict):
            for k, x in list(v.items()):
                if isinstance(x, str):
                    x = x.replace(OLD_INV, NEW_INV)
                    x = x.replace("API02_C8_TO_C9_CORRECTION_INVENTORY.json", "API02_C9_TO_C10_CORRECTION_INVENTORY.json")
                    if x in ("C8 → C9", "C8 -> C9"):
                        x = "current correction round"
                    v[k] = x
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(d)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    root = pathlib.Path(sys.argv[1]).resolve()
    patch_validation(root)
    patch_lineage(root)
    print("API02_C10_CARRIED_EVIDENCE_RECONCILIATION:PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

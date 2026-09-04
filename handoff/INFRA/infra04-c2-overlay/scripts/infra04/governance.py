"""Region-anchored governance freshness reconciliation (G01..G09, G42).

The canonical registers are prose, and prose regions can disagree with each
other. Reading "the PCR says X" is therefore not evidence; reading *which
region* says X, and reporting where the regions disagree, is.

This module anchors every governance fact to a named region of the Program
Control Register:

===================  ===================================================
region               what it is
===================  ===================================================
``primary_position`` the fenced ``Current primary position`` block
``layer_table``      the program-layer control-state table
``immediate``        section 9, the immediate execution decision
``transitions``      the recorded authoritative transition sections
===================  ===================================================

A fact confirmed by several regions is strong. A fact asserted by one
region and contradicted — or merely not yet carried — by another is
reported as a **named discrepancy**, never silently resolved in the
direction that happens to suit the candidate. INFRA-04 does not edit the
registers; it records what they say and what it therefore may and may not
claim.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.acceptance.canonical import sha256_bytes
from scripts.infra04 import codes

PCR_PATH = "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"
MASTER_PATH = "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
ENTRYPOINT_PATH = "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md"

#: PCR regions that describe the *current* state. Facts are compared only
#: across these; the transition sections are kept as evidence, not compared.
CURRENT_STATE_REGIONS = ("primary_position", "layer_table", "immediate")

#: Stages whose acceptance INFRA-04 consumes, and the record that proves it.
DEPENDENCY_RECORDS: dict[str, str] = {
    "INFRA-01": "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
    "INFRA-02": "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json",
    "INFRA-03": "docs/infra/INFRA-03/INFRA03_C1_ACCEPTANCE_RECORD.json",
    "API-06": "docs/api/API-06/API06_C1_ACCEPTANCE_RECORD.json",
    "OPS-01": "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json",
    "OPS-02": "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json",
    "OPS-03": "docs/ops/OPS-03/OPS03_C3_ACCEPTANCE_RECORD.json",
    "CTRL-01": "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json",
    "CTRL-04": "docs/ctrl/CTRL-04/CTRL04_C1_ACCEPTANCE_RECORD.json",
}

#: Stages INFRA-04 must NOT claim accepted. Governance has recorded no
#: acceptance for them; the candidate consumes nothing from them.
UNACCEPTED_STAGES = ("INFRA-04", "INFRA-05", "INFRA-06", "INFRA-07", "SEC-01")


@dataclass(frozen=True)
class GovernanceFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def _show(root: Path, ref: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path}"],
        capture_output=True,
        timeout=180,
        check=True,
    ).stdout


def target_authority(root: Path) -> dict[str, str]:
    """The live canonical target, re-read from the remote at call time."""

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        ).stdout.strip()

    git("fetch", "--no-tags", "origin", "main")
    return {
        "repository": "nepogoda1970-epd2/epd2-civic-os",
        "branch": "main",
        "commit": git("rev-parse", "origin/main"),
        "tree": git("rev-parse", "origin/main^{tree}"),
        "commit_timestamp": git("show", "-s", "--format=%cI", "origin/main"),
    }


def _regions(text: str) -> dict[str, str]:
    """Split the PCR into the four regions facts are anchored to."""
    regions: dict[str, str] = {}
    primary = re.search(r"Current primary position:\s*```text(?P<body>.*?)```", text, re.DOTALL)
    regions["primary_position"] = primary.group("body") if primary else ""
    regions["layer_table"] = "\n".join(line for line in text.splitlines() if line.startswith("| "))
    immediate = re.search(
        r"## 9\. Immediate execution decision(?P<body>.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    regions["immediate"] = immediate.group("body") if immediate else ""
    regions["transitions"] = "\n".join(
        line
        for line in text.splitlines()
        if (line.startswith("**") and "transition" in line.lower())
        or (line.startswith("**") and "acceptance" in line.lower())
    )
    return regions


_ACCEPTED = re.compile(r"ACCEPTED\s*/\s*CLOSED", re.IGNORECASE)

#: Any stage token, used to bound how far a statement about one stage may
#: reach: a sentence about INFRA-02 stops where INFRA-03 is mentioned.
_STAGE_TOKEN = re.compile(r"\b(?:DATA|API|INFRA|OPS|CTRL|FRONT|SEC|PILOT)-\d\d\b")

#: Stage-level state vocabulary. Bare OPEN/CLOSED are deliberately absent:
#: they describe *layers*, and reading them as a stage state turns "the
#: layer remains open" into a claim about whichever stage is nearest.
_STATE_VOCABULARY = re.compile(
    r"ACCEPTED\s*/\s*CLOSED"
    r"|ACCEPTED_IMPLEMENTATION_BASELINE"
    r"|\bNOT_ACCEPTED\b"
    r"|\bACCEPTED\b"
    r"|QUALIFICATION ELIGIBLE"
    r"|\bNEXT\b",
    re.IGNORECASE,
)

_WINDOW = 260

#: Maximum distance between a stage token and a state keyword that is still
#: read as "this state belongs to this stage".
_PREDICATE_DISTANCE = 120

#: Indirection markers. "OPS-03 qualification must bind the exact accepted
#: API-06 identity" says nothing about OPS-03's own state, and reading the
#: nearby "accepted" as OPS-03's state would be exactly the false claim
#: gate G08 exists to prevent.
_INDIRECTION = (
    "must",
    "requires",
    "require",
    "prerequisite",
    "bind",
    "depends",
    "pending",
    "await",
    "before",
    "unless",
    "reuse",
    "may ",
)


def _normalise(raw: str) -> str:
    if _ACCEPTED.match(raw.strip()):
        return "ACCEPTED_CLOSED"
    return raw.strip().upper().replace(" ", "_").replace("/", "_")


def _family(state: str) -> str:
    """Collapse wording variance to the governance family it belongs to."""
    if state in {"ACCEPTED", "ACCEPTED_CLOSED", "ACCEPTED_IMPLEMENTATION_BASELINE"}:
        return "ACCEPTED_FAMILY"
    return state


def _stage_state(region_text: str, stage: str) -> str:
    """What one region says about one stage. UNKNOWN when it says nothing.

    Every mention of the stage is read within a bounded window that stops
    at the next stage token, so a state belonging to a neighbouring stage
    is never attributed to this one.
    """
    states: set[str] = set()
    for match in re.finditer(rf"{re.escape(stage)}\b", region_text):
        window = region_text[match.end() : match.end() + _WINDOW]
        boundary = _STAGE_TOKEN.search(window)
        if boundary is not None:
            window = window[: boundary.start()]
        found = _STATE_VOCABULARY.search(window)
        if found is None:
            continue
        intervening = window[: found.start()].lower()
        if len(intervening) > _PREDICATE_DISTANCE:
            continue
        if any(marker in intervening for marker in _INDIRECTION):
            continue
        states.add(_normalise(found.group(0)))
    if not states:
        return "UNKNOWN"
    if "ACCEPTED_CLOSED" in states:
        return "ACCEPTED_CLOSED"
    return sorted(states)[0]


def reconcile(root: Path, candidate_pcr_hash: str | None = None) -> dict[str, Any]:
    """Read the registers and build the region-anchored reconciliation.

    Nothing here mutates a register. The result carries the target
    authority, the controlling document digests, the per-region facts, the
    named discrepancies and the honest list of what INFRA-04 may claim.
    """
    authority = target_authority(root)
    ref = authority["commit"]
    documents: dict[str, str] = {}
    for path in (ENTRYPOINT_PATH, PCR_PATH, MASTER_PATH):
        documents[path] = sha256_bytes(_show(root, ref, path))
    pcr_text = _show(root, ref, PCR_PATH).decode("utf-8", errors="replace")
    master_text = _show(root, ref, MASTER_PATH).decode("utf-8", errors="replace")
    regions = _regions(pcr_text)

    stages = sorted(set(DEPENDENCY_RECORDS) | set(UNACCEPTED_STAGES))
    # Current-state regions only. The transition sections are historical by
    # construction — an old line reading "API-06 NEXT" records what was true
    # then, so comparing it against the present state would manufacture
    # discrepancies instead of finding them.
    per_region: dict[str, dict[str, str]] = {
        name: {stage: _stage_state(regions[name], stage) for stage in stages}
        for name in CURRENT_STATE_REGIONS
    }

    records: dict[str, dict[str, Any]] = {}
    for stage, path in sorted(DEPENDENCY_RECORDS.items()):
        try:
            raw = _show(root, ref, path)
        except subprocess.CalledProcessError:
            records[stage] = {"record": path, "present": False, "sha256": ""}
            continue
        records[stage] = {"record": path, "present": True, "sha256": sha256_bytes(raw)}

    findings: list[GovernanceFinding] = []
    accepted: dict[str, bool] = {}
    discrepancies: list[dict[str, Any]] = []
    lagging: list[dict[str, Any]] = []
    for stage in stages:
        by_region = {
            name: per_region[name][stage]
            for name in per_region
            if per_region[name][stage] != "UNKNOWN"
        }
        # "ACCEPTED" and "ACCEPTED / CLOSED" are the same governance family
        # written two ways; only a genuine difference in family counts as a
        # discrepancy, so wording variance does not manufacture findings.
        asserted = {state for state in by_region.values()}
        families = {_family(state) for state in by_region.values()}
        record_present = records.get(stage, {}).get("present", False)
        is_accepted = "ACCEPTED_CLOSED" in asserted and bool(record_present)
        accepted[stage] = is_accepted
        if len(families) > 1:
            discrepancies.append(
                {
                    "stage": stage,
                    "states_by_region": by_region,
                    "families": sorted(families),
                    "silent_regions": sorted(
                        name for name in per_region if per_region[name][stage] == "UNKNOWN"
                    ),
                    "acceptance_record_present": record_present,
                    "resolution": (
                        "acceptance is taken only where a recorded governance decision "
                        "exists; a region that does not yet carry the newer state is "
                        "reported as lagging, not overridden"
                    ),
                }
            )
        silent = sorted(name for name in per_region if per_region[name][stage] == "UNKNOWN")
        if is_accepted and silent:
            # A recorded acceptance that some current-state region does not
            # yet carry. This is a governance-hygiene observation about the
            # register, not a defect in this candidate — and it is named
            # rather than quietly read past.
            lagging.append(
                {
                    "stage": stage,
                    "carried_by": sorted(
                        name
                        for name, state in per_region.items()
                        if state[stage] == "ACCEPTED_CLOSED"
                    ),
                    "not_yet_carried_by": silent,
                    "acceptance_record": records.get(stage, {}).get("record"),
                    "observation": (
                        "the acceptance is proven by the recorded governance decision "
                        "and carried by the region(s) listed; the remaining region(s) "
                        "do not yet restate it. INFRA-04 records this and neither "
                        "edits the register nor treats the silence as a refusal."
                    ),
                }
            )
        if "ACCEPTED_CLOSED" in asserted and not record_present:
            findings.append(
                GovernanceFinding(
                    codes.UNACCEPTED_DEPENDENCY_CLAIMED_ACCEPTED,
                    stage,
                    "a register region calls the stage accepted but no acceptance "
                    "record exists on the canonical target",
                )
            )
    for stage in UNACCEPTED_STAGES:
        if accepted.get(stage):
            findings.append(
                GovernanceFinding(
                    codes.UNACCEPTED_DEPENDENCY_CLAIMED_ACCEPTED,
                    stage,
                    "INFRA-04 must treat this stage as not accepted",
                )
            )

    infra_layer_open = bool(re.search(r"INFRA\s*(?:LAYER)?\s*=?\s*OPEN", pcr_text, re.IGNORECASE))
    if not infra_layer_open:
        findings.append(
            GovernanceFinding(
                codes.INFRA_LAYER_CLOSURE_CLAIMED,
                "pcr",
                "the register no longer states that the INFRA layer is open; "
                "INFRA-04 may not proceed on an assumed closure",
            )
        )

    return {
        "schema": "epd2.infra04.governance-reconciliation/1",
        "note": "Region-anchored reconciliation against the live canonical target. "
        "INFRA-04 reads the registers and never edits them; a region that "
        "lags behind a recorded acceptance is named as a discrepancy rather "
        "than resolved in the candidate's favour.",
        "target_authority": authority,
        "controlling_documents": documents,
        "master_maintenance_level": (
            match.group(0)
            if (match := re.search(r"\bV2\d\b", master_text)) is not None
            else "UNKNOWN"
        ),
        "candidate_pcr_hash": candidate_pcr_hash or documents[PCR_PATH],
        "region_facts": per_region,
        "acceptance_records": records,
        "accepted": accepted,
        "unaccepted_declared": list(UNACCEPTED_STAGES),
        "infra_layer_open": infra_layer_open,
        "region_discrepancies": discrepancies,
        "lagging_regions": lagging,
        "findings": [finding.describe() for finding in findings],
        "infra04_claims": {
            "self_state": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
            "claims_acceptance_of_itself": False,
            "claims_infra_layer_closed": False,
            "claims_production_readiness": False,
            "claims_certification": False,
        },
    }


def check_freshness(
    root: Path, recorded: dict[str, str], subject: str = "governance"
) -> list[GovernanceFinding]:
    """Re-read the target: an advanced target must be re-reconciled."""
    current = target_authority(root)
    findings: list[GovernanceFinding] = []
    if current["commit"] != recorded.get("commit"):
        findings.append(
            GovernanceFinding(
                codes.PREDECESSOR_BINDING_OMITTED,
                subject,
                f"canonical target advanced from {str(recorded.get('commit'))[:12]} to "
                f"{current['commit'][:12]} during the run; re-reconcile before any seal",
            )
        )
    return findings

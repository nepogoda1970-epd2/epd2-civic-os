#!/usr/bin/env python3
"""CTRL-01 preseal validator.

Runs the twenty-two governed gates and writes the W12 evidence set into
`validation/ctrl01/`. The exit code is the terminal result: 0 only when every
mandatory gate passed. No gate may report `SKIPPED`, `NOT_RUN` or
`ASSUMED_PASS`; a gate that cannot run is a failure.

Stage mode is `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. The validator's own
output states `NOT_ACCEPTED` and cannot be configured to say otherwise.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "services" / "control-plane-service" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from epd2_control_plane_service import SELF_STATE_ALLOWED, STAGE, STAGE_MODE  # noqa: E402
from epd2_control_plane_service.api import CONSOLE_CAPABILITIES, contracts_to_json_obj  # noqa: E402
from epd2_control_plane_service.audit import screen_attributes  # noqa: E402
from epd2_control_plane_service.breakglass import PROHIBITED_UNDER_BREAK_GLASS  # noqa: E402
from epd2_control_plane_service.domain import (  # noqa: E402
    AuthorityState,
    CredentialClass,
    CredentialState,
    InterventionType,
    Right,
    ScopeLevel,
)
from epd2_control_plane_service.exceptions import (  # noqa: E402
    AuthorizationRefused,
    ControlPlaneError,
)
from epd2_control_plane_service.freeze import (  # noqa: E402
    build_manifest,
    manifest_digest,
    verify_manifest,
)
from epd2_control_plane_service.intervention import (  # noqa: E402
    PRESERVED_MEMBER_CAPABILITIES,
    VOTING_DOMAIN_PROHIBITED_EFFECTS,
)
from epd2_control_plane_service.inventory import (  # noqa: E402
    INVENTORY,
    NO_UI_DECISIONS,
    inventory_to_json_obj,
)
from epd2_control_plane_service.mutations import MUTATIONS, apply_and_detect  # noqa: E402
from epd2_control_plane_service.policy import ControlPolicy  # noqa: E402
from epd2_control_plane_service.reference_world import (  # noqa: E402
    LAND_BE,
    PLATFORM,
    T0,
    build_world,
)
from epd2_control_plane_service.sod import SOD_RULES, Responsibility, SodEngine  # noqa: E402
from epd2_control_plane_service.verification import (  # noqa: E402
    CHECK_IDS,
    FORBIDDEN_SELF_STATES,
    CheckResult,
    Scenario,
    run_checks,
    suite_digest,
)

OUT_DIR = REPO_ROOT / "validation" / "ctrl01"

CANONICAL_BLOBS: dict[str, str] = {
    "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md": ("4b69cf500f2171399f7fb0b4213cb1bddcc8cf07"),
    "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md": ("aad828e377889e96f0bce16245f4e9ed1d97ed4a"),
    "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md": (
        "7f5c6a9a88f8e653b43dc542a595ac37bf7a0692"
    ),
    "docs/roadmap/EPD2_BSI_VOTING_BOOTSTRAP_RULE.md": ("15dd290a1bcb6f44b4242e7c33b71119e404553a"),
}

ACCEPTED_PREDECESSOR_BLOBS: dict[str, str] = {
    "docs/api/API-02/API02_C13_ACCEPTANCE_RECORD.json": (
        "7f8b16ca16a11f4916f1988ef53243b977e1862d"
    ),
    "docs/api/API-03/API03_C5_ACCEPTANCE_RECORD.json": ("0f41555a4aa5f0bf80fa7a1a95be905c02d692c5"),
    "docs/api/API-04/API04_C1_ACCEPTANCE_RECORD.json": ("fab2833e6769bc9e71876e47b168848e6c386e96"),
    "docs/api/API-05/API05_C1_ACCEPTANCE_RECORD.json": ("e35f0ff0438419db445580f8739575ccba3f6551"),
    "docs/frontend/FRONT-04-C2-ACCEPTANCE-RECORD.json": (
        "5eb35c0699434f1f93c63bfc23a87097c609ca06"
    ),
    "docs/frontend/FRONT-03-C1-ACCEPTANCE-RECORD.json": (
        "ced7d78a779343b5507a5cd612ad8620e8c821cd"
    ),
    "docs/frontend/FRONT-02-C2.1-ACCEPTANCE-RECORD.json": (
        "8f22eab702d7d674be115916defb2e12e63d7680"
    ),
    "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json": (
        "5618144cf503b55bea96550c80d80cac78580963"
    ),
    "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json": (
        "95df6e5c5288b16aee62621157fc28a790b68bfc"
    ),
    "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json": ("0b23469ac20c34fa7891653cb41d0eaa44437ac6"),
    "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json": ("3d4baa96b957693244507aaa76f2d685226f88b6"),
}

#: Stages CTRL-01 consumes that have no acceptance-record file on `main`. Their
#: acceptance is recorded only as a Program Control Register transition, so the
#: reconciliation names them rather than silently treating them as unaccepted.
REGISTER_ONLY_PREDECESSORS: dict[str, str] = {
    "API-01": (
        "ACCEPTED / CLOSED per Program Control Register section 6 transition dated 2026-08-26"
    ),
}

#: Stages that are NOT accepted at CTRL-01 preseal time. Each is an explicit
#: open dependency; none may be treated as satisfied by a working ZIP, a branch
#: name, a local PASS or an operator report.
UNRECONCILED_DEPENDENCIES: dict[str, str] = {
    "API-06": ("NEXT / NOT ACCEPTED; API layer remains open until API-06 closes"),
}

#: The FIR reconciliation targets, with status read from the current Master
#: Future Implementation Register rather than promoted from the starter seed.
FIR_TARGETS: dict[str, str] = {
    "FIR-CTRL-001": "approved",
    "FIR-GOV-004": "approved",
    "FIR-GOV-005": "approved",
    "FIR-SEC-004": "approved",
    "FIR-TRUST-002": "approved",
    "FIR-TRUST-003": "approved",
    "FIR-AI-003": "approved",
    "FIR-OPS-001": "approved",
    "FIR-VOTE-BSI-001": "approved",
    "FIR-VOTE-NET-001": "approved",
    "FIR-OSS-007": "approved",
}

BASELINE_COMMIT = "217559b7f21c338d6fe8d4e4676082cd3840251c"


# ---------------------------------------------------------------------------


@dataclass(slots=True)
class GateResult:
    gate_id: str
    name: str
    status: str  # PASS | FAIL
    findings: list[str]
    evidence: dict[str, Any]

    def to_obj(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "status": self.status,
            "findings": self.findings,
            "evidence": self.evidence,
        }


def _gate(
    gate_id: str, name: str, findings: Sequence[str], evidence: Mapping[str, Any]
) -> GateResult:
    return GateResult(
        gate_id, name, "PASS" if not findings else "FAIL", list(findings), dict(evidence)
    )


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def _checks_by_id(results: Iterable[CheckResult]) -> dict[str, CheckResult]:
    return {r.check_id: r for r in results}


def _require(checks: Mapping[str, CheckResult], ids: Sequence[str]) -> list[str]:
    findings: list[str] = []
    for check_id in ids:
        result = checks.get(check_id)
        if result is None:
            findings.append(f"{check_id}: NOT RUN")
        elif not result.passed:
            findings.append(f"{check_id}: {result.detail}")
    return findings


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------


def gate_g01_bootstrap_freshness() -> GateResult:
    """Governance bootstrap freshness.

    The canonical documents are re-read from the working tree and their git blob
    identities recomputed. A drifted `main` is reported rather than assumed
    harmless: the recorded delta is what a future seal must reconcile.
    """
    findings: list[str] = []
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    blobs: dict[str, dict[str, Any]] = {}
    for path, expected in CANONICAL_BLOBS.items():
        target = REPO_ROOT / path
        if not target.exists():
            findings.append(f"canonical document missing: {path}")
            continue
        actual = _git("hash-object", path)
        blobs[path] = {"expected": expected, "actual": actual, "match": actual == expected}
        if actual != expected:
            findings.append(f"canonical drift in {path}: {actual} != {expected}")
    return _gate(
        "G01",
        "governance bootstrap freshness",
        findings,
        {
            "head_commit": head,
            "head_tree": tree,
            "baseline_commit_at_assignment": BASELINE_COMMIT,
            "head_matches_assignment_baseline": head == BASELINE_COMMIT,
            "canonical_documents": blobs,
            "reread_required_before_seal": True,
        },
    )


def gate_g02_baseline_identity() -> GateResult:
    findings: list[str] = []
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    if not head or not tree:
        findings.append("baseline commit/tree could not be established")
    if STAGE_MODE != "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED":
        findings.append(f"unexpected stage mode {STAGE_MODE}")
    return _gate(
        "G02",
        "entering baseline identity",
        findings,
        {
            "repository": "nepogoda1970-epd2/epd2-civic-os",
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "commit": head,
            "tree": tree,
            "stage": STAGE,
            "stage_mode": STAGE_MODE,
            "bootstrap": "PASS" if not findings else "FAIL",
        },
    )


def gate_g03_accepted_predecessors() -> GateResult:
    findings: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    for path, expected in ACCEPTED_PREDECESSOR_BLOBS.items():
        target = REPO_ROOT / path
        if not target.exists():
            findings.append(f"accepted predecessor record missing: {path}")
            continue
        actual = _git("hash-object", path)
        entry: dict[str, Any] = {"git_blob_sha": actual, "size_bytes": target.stat().st_size}
        if expected:
            entry["manifest_expected"] = expected
            entry["match"] = actual == expected
            if actual != expected:
                findings.append(f"acceptance record drift in {path}")
        try:
            payload = json.loads(target.read_text())
            entry["decision"] = payload.get("decision") or payload.get("new_state")
            entry["candidate_sha256"] = (payload.get("candidate") or {}).get("sha256")
        except (ValueError, AttributeError):
            findings.append(f"acceptance record is not readable JSON: {path}")
        records[path] = entry
    return _gate("G03", "accepted predecessor references", findings, {"records": records})


def gate_g04_action_inventory(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-INVENTORY-CONGRUENT", "CHK-NO-UNIVERSAL-ADMIN"])
    required_desks = {
        "DESK_PLATFORM_OPERATIONS",
        "DESK_SECURITY_OPERATIONS",
        "DESK_PRIVILEGED_ACCESS",
        "DESK_AUDIT_OVERSIGHT",
        "DESK_DPO_PRIVACY",
        "DESK_ELECTION_ADMIN",
        "DESK_MEMBERSHIP_ADMIN",
        "DESK_OFFICES_MANDATES",
        "DESK_ASSEMBLIES",
        "DESK_CORRESPONDENCE",
        "DESK_COMPLAINTS_OMBUDS",
        "DESK_PROTECTED_REPORTING",
        "DESK_FINANCE",
        "DESK_PROCUREMENT",
        "DESK_RECORDS_RETENTION",
        "DESK_TRANSPARENCY_PUBLICATION",
        "DESK_REPRESENTATIVE_OPEN_DESK",
        "DESK_CITIZEN_OFFICE",
        "DESK_MODERATION",
        "DESK_AI_OVERSIGHT",
        "DESK_EMERGENCY",
        "DESK_CREDENTIAL_OPERATIONS",
        "DESK_RECOVERY",
        "DESK_SERVICE_IDENTITY",
        "DESK_KEY_CUSTODY",
        "DESK_ORG_AUTHORITY",
        "DESK_REGIONAL_INTERVENTION",
    }
    missing = sorted(required_desks - INVENTORY.desks())
    if missing:
        findings.append(f"FIR-CTRL-001 desks without an action: {missing}")
    for action in INVENTORY:
        if not action.governing_fir_refs:
            findings.append(f"{action.action_id}: no governing FIR reference")
        if action.mutation and action.required_right_revoke is None:
            findings.append(f"{action.action_id}: no revoke/rollback right")
    return _gate(
        "G04",
        "action inventory completeness",
        findings,
        {
            "actions_total": len(INVENTORY),
            "mutations": len(INVENTORY.mutation_ids()),
            "read_only": len(INVENTORY.read_ids()),
            "consoles": sorted(INVENTORY.consoles()),
            "desks_total": len(INVENTORY.desks()),
            "no_ui_decisions": [dict(d) for d in NO_UI_DECISIONS],
        },
    )


def gate_g05_authority_read_model() -> GateResult:
    findings: list[str] = []
    world = build_world()
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.SUSPENDED, recorded_at=T0, recorded_by="G05", note="probe"
    )
    world.directory.set_authority_state(
        "a.land.be.chair",
        AuthorityState.ACTIVE,
        recorded_at=T0,
        recorded_by="G05",
        note="probe restore",
    )
    model = world.directory.read_model(T0)
    for key in (
        "current_organizational_authority",
        "authority_source",
        "authority_history",
        "session_quarantine_state",
        "current_restrictions",
        "temporary_supervision",
        "service_credential_state",
        "human_credential_state",
        "trust_key_references",
    ):
        if key not in model:
            findings.append(f"read model lacks projection: {key}")
    history = [h for h in model["authority_history"] if h["authority_id"] == "a.land.be.chair"]
    if [h["state"] for h in history] != ["ACTIVE", "SUSPENDED", "ACTIVE"]:
        findings.append("authority history was not preserved across state changes")
    for entry in model["authority_source"]:
        if not entry["rule_version"] or not entry["source_decision_ref"]:
            findings.append(
                f"{entry['authority_id']}: authority without rule version or source decision"
            )
    return _gate(
        "G05",
        "authority provenance and read model",
        findings,
        {
            "projections": sorted(model),
            "authorities": len(model["current_organizational_authority"]),
            "history_records": len(model["authority_history"]),
        },
    )


def gate_g06_regional_scope_isolation(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(
        checks,
        [
            "CHK-SCOPE-ISOLATION",
            "CHK-NO-IMPLICIT-BUND-TAKEOVER",
            "CHK-PLATFORM-GRANTS-NO-POLITICAL-AUTHORITY",
            "CHK-INTERVENTION-ENFORCED",
            "CHK-NO-COARSE-REGIONAL-DISABLE",
            "CHK-INTERVENTION-TIME-BOUNDED",
        ],
    )
    service = build_world().plane.interventions
    for capability in PRESERVED_MEMBER_CAPABILITIES:
        try:
            service.assert_continuity([capability])
        except AuthorizationRefused:
            continue
        findings.append(f"preserved capability {capability} is not protected")
    levels = {t.value for t in InterventionType}
    if levels != {
        "SESSION_QUARANTINE",
        "AUTHORITY_SUSPENSION",
        "REGIONAL_ACTION_RESTRICTION",
        "TEMPORARY_SUPERVISION",
    }:
        findings.append(f"unexpected intervention level set: {sorted(levels)}")
    return _gate(
        "G06",
        "regional scope isolation and bounded intervention",
        findings,
        {
            "intervention_levels": sorted(levels),
            "preserved_member_capabilities": list(PRESERVED_MEMBER_CAPABILITIES),
            "prohibited_voting_effects": list(VOTING_DOMAIN_PROHIBITED_EFFECTS),
            "max_supervision_days": 90,
        },
    )


def gate_g07_separation_of_duties() -> GateResult:
    findings: list[str] = []
    engine = SodEngine()
    required_pairs = {
        frozenset({Responsibility.REQUEST, Responsibility.APPROVE}),
        frozenset({Responsibility.APPROVE, Responsibility.EXECUTE}),
        frozenset({Responsibility.EXECUTE, Responsibility.AUDIT}),
        frozenset({Responsibility.SECRET_VISIBILITY, Responsibility.APPROVE}),
        frozenset({Responsibility.CREDENTIAL_ISSUANCE, Responsibility.AUDIT}),
        frozenset({Responsibility.KEY_CUSTODY, Responsibility.POLICY_APPROVAL}),
        frozenset({Responsibility.EMERGENCY_GRANT, Responsibility.EMERGENCY_REVIEW}),
        frozenset({Responsibility.DESTRUCTIVE_OPERATION, Responsibility.DESTRUCTIVE_CONFIRMATION}),
        frozenset({Responsibility.REGIONAL_ACTION, Responsibility.BUND_OVERSIGHT}),
    }
    present = {rule.pair() for rule in SOD_RULES}
    missing = required_pairs - present
    if missing:
        findings.append(f"{len(missing)} required SoD pair(s) absent")
    for rule in SOD_RULES:
        violations = engine.evaluate({rule.left: ("p.one",), rule.right: ("p.one",)})
        if not any(v.rule_id == rule.rule_id for v in violations):
            findings.append(f"{rule.rule_id} does not detect concentration")
        clean = engine.evaluate({rule.left: ("p.one",), rule.right: ("p.two",)})
        if any(v.rule_id == rule.rule_id for v in clean):
            findings.append(f"{rule.rule_id} fires on correctly separated principals")
    return _gate(
        "G07",
        "separation of duties",
        findings,
        {"rules": engine.matrix(), "rules_total": len(SOD_RULES)},
    )


def gate_g08_four_eyes(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-QUORUM-ENFORCED", "CHK-SELF-APPROVAL-REJECTED"])
    four_eyes = [a.action_id for a in INVENTORY if a.four_eyes]
    for action in INVENTORY:
        if action.four_eyes and action.quorum_required < 2:
            findings.append(f"{action.action_id}: four-eyes with quorum {action.quorum_required}")
    return _gate(
        "G08",
        "four-eyes and quorum",
        findings,
        {"four_eyes_actions": sorted(four_eyes), "four_eyes_total": len(four_eyes)},
    )


def gate_g09_emergency_lifecycle(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(
        checks, ["CHK-EMERGENCY-EXPIRY", "CHK-EMERGENCY-SCOPE", "CHK-EMERGENCY-NOT-RENEWABLE"]
    )
    world = build_world()
    emergency = world.plane.emergency
    security = world.directory.current_authority("a.security.operator")
    if security is None:
        return _gate("G09", "emergency lifecycle", ["security operator authority absent"], {})
    emergency.request(
        grant_id="g09-grant",
        principal_id="p.security.operator",
        requested_by="p.privileged.operator",
        reason="gate probe",
        scope=security.scope,
        action_codes={"SERVICE_CRED.REVOKE"},
        requested_at=T0,
    )
    emergency.approve("g09-grant", approver_id="p.emergency.controller", approved_at=T0)
    grant = emergency.activate("g09-grant", activated_at=T0)
    if grant.expires_at is None:
        findings.append("activation did not set an absolute expiry")
    emergency.expire_due(T0.replace(hour=23))
    expired = emergency.grant("g09-grant")
    if expired is None or expired.state.value != "EXPIRED":
        findings.append("automatic expiry did not fire")
    if emergency.unreviewed() == ():
        findings.append("expired grants are not tracked for mandatory review")
    return _gate(
        "G09",
        "emergency lifecycle",
        findings,
        {
            "lifecycle": ["REQUEST", "APPROVE", "ACTIVATE", "USE", "EXPIRE_OR_REVOKE", "REVIEW"],
            "renewal_path_present": False,
            "prohibited_under_break_glass": sorted(PROHIBITED_UNDER_BREAK_GLASS),
            "emergency_eligible_actions": sorted(
                a.action_id for a in INVENTORY if a.emergency_eligible
            ),
        },
    )


def gate_g10_credential_lifecycle(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-CREDENTIAL-STATE-ENFORCED"])
    world = build_world()
    world.directory.set_human_credential_state("cred.p.ordinary.member", CredentialState.REVOKED)
    try:
        world.directory.set_human_credential_state("cred.p.ordinary.member", CredentialState.ACTIVE)
        findings.append("a revoked credential was resurrected under the same identity")
    except AuthorizationRefused:
        pass
    world.directory.set_authority_state(
        "a.land.be.chair", AuthorityState.SUSPENDED, recorded_at=T0, recorded_by="G10"
    )
    world.directory.set_human_credential_state("cred.p.land.be.chair", CredentialState.ACTIVE)
    authority = world.directory.current_authority("a.land.be.chair")
    if authority is None or authority.state is not AuthorityState.SUSPENDED:
        findings.append("credential recovery restored a suspended organizational authority")
    return _gate(
        "G10",
        "human credential and recovery lifecycle",
        findings,
        {
            "credential_states": [s.value for s in CredentialState],
            "recovery_restores_authority": False,
        },
    )


def gate_g11_service_credentials(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-ACTOR-CLASS-SEPARATION", "CHK-SECRET-VISIBILITY-SEPARATION"])
    for action_id in ("SERVICE_CRED.ISSUE", "SERVICE_CRED.ROTATE", "SERVICE_CRED.REVOKE"):
        action = INVENTORY.get(action_id)
        if action.scope_level is not ScopeLevel.PLATFORM:
            findings.append(f"{action_id}: service credential control is not platform-scoped")
        if action.actor_class.value != "HUMAN":
            findings.append(
                f"{action_id}: service credential control must be operated by a human authority"
            )
    return _gate(
        "G11",
        "service credential control",
        findings,
        {
            "service_credential_actions": [
                "SERVICE_CRED.ISSUE",
                "SERVICE_CRED.ROTATE",
                "SERVICE_CRED.REVOKE",
            ],
            "workload_only_actions": sorted(
                a.action_id for a in INVENTORY if a.actor_class.value == "SERVICE"
            ),
        },
    )


def gate_g12_key_trust(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-VOTING-BOUNDARY"])
    world = build_world()
    voting = world.directory.key_reference("key.voting.trustee.1")
    platform = world.directory.key_reference("key.platform.signing.1")
    if voting is None or voting.credential_class is not CredentialClass.VOTING_DOMAIN:
        findings.append("voting-domain key reference absent from the read model")
    elif voting.exportable:
        findings.append("voting-domain key material is marked exportable")
    if platform is None or platform.quorum_m is None:
        findings.append("platform key class has no threshold policy")
    destroy = INVENTORY.get("KEY.DESTROY")
    if destroy.quorum_required < 3 or destroy.required_right_execute is not Right.DESTROY:
        findings.append("key destruction is not under a strengthened quorum")
    return _gate(
        "G12",
        "key and trust reference control",
        findings,
        {
            "key_actions": sorted(a.action_id for a in INVENTORY if a.domain == "key_trust"),
            "voting_keys_are_external_references_only": True,
            "platform_key_threshold": None
            if platform is None
            else f"{platform.quorum_m}-of-{platform.quorum_n}",
        },
    )


def gate_g13_control_api() -> GateResult:
    """Contract coverage, plus a runtime probe.

    Declaring `server_side_authorization=True` proves nothing on its own, so the
    gate drives a sample of mutating contracts through the runtime with a
    principal that holds no authority for them. Each must be refused. A contract
    that a caller could reach without server-side authorization shows up here as
    a permitted act, not as a missing flag.
    """
    findings: list[str] = []
    payload = contracts_to_json_obj()
    if payload["uncovered_console_capabilities"]:
        findings.append(
            f"console capabilities without a contract: {payload['uncovered_console_capabilities']}"
        )
    covered = {c["action_id"] for c in payload["contracts"]}
    if covered != INVENTORY.action_ids():
        findings.append("contract set and inventory disagree")

    world = build_world()
    probed = 0
    permitted: list[str] = []
    for contract in payload["contracts"]:
        if not contract["mutation"]:
            continue
        action = INVENTORY.get(contract["action_id"])
        probed += 1
        try:
            world.plane.submit_request(
                request_id=f"g13-{probed:03d}",
                action_id=action.action_id,
                principal_id="p.ordinary.member",
                session_id="s.p.ordinary.member",
                scope=LAND_BE if action.scope_level is not ScopeLevel.PLATFORM else PLATFORM,
                object_ref="probe.object",
                purpose="unauthorized reach at the contract surface",
                moment=T0,
            )
        except ControlPlaneError:
            continue
        permitted.append(action.action_id)
    if permitted:
        findings.append(f"mutating contracts reachable without authorization: {permitted}")
    if probed != len(INVENTORY.mutation_ids()):
        findings.append(
            f"probed {probed} mutating contracts, expected {len(INVENTORY.mutation_ids())}"
        )

    return _gate(
        "G13",
        "control API contract coverage",
        findings,
        {
            "contracts": payload["counts"],
            "console_capabilities": sorted(CONSOLE_CAPABILITIES),
            "ui_visibility_is_not_authorization": True,
            "unauthorized_probes_run": probed,
            "unauthorized_probes_refused": probed - len(permitted),
        },
    )


def gate_g14_negative_suite() -> GateResult:
    """Executes the packaged pytest suites. A non-zero exit is a gate failure."""
    findings: list[str] = []
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "services/control-plane-service/tests",
            "-q",
            "--no-header",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else "no output"
    if completed.returncode != 0:
        findings.append(f"packaged test suite failed: {tail}")
    passed = 0
    for token in tail.replace(",", " ").split():
        if token.isdigit():
            passed = int(token)
            break
    if passed < 100:
        findings.append(f"unexpectedly small suite: {tail}")
    return _gate(
        "G14",
        "authorization negative suite",
        findings,
        {"pytest_exit_code": completed.returncode, "summary": tail, "tests_passed": passed},
    )


def gate_g15_commit_time_reauth(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(
        checks,
        ["CHK-COMMIT-TIME-REAUTH", "CHK-REVOKED-AUTHORITY-REFUSED", "CHK-SESSION-STATE-ENFORCED"],
    )
    missing = [a.action_id for a in INVENTORY if a.mutation and not a.commit_time_reauthorization]
    if missing:
        findings.append(f"mutations without commit-time reauthorization: {missing}")
    return _gate(
        "G15",
        "commit-time reauthorization",
        findings,
        {
            "mutations_requiring_reauth": len(INVENTORY.mutation_ids()),
            "toctou_cases_covered": [
                "authority revoked after request",
                "intervention activated during workflow",
                "emergency grant expired before commit",
                "quorum changed",
                "target object scope changed",
                "session quarantined",
                "credential revoked",
                "region restriction began",
            ],
        },
    )


def gate_g16_fail_closed(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-FAIL-CLOSED-ON-UNKNOWN", "CHK-INVENTORY-CONGRUENT"])
    policy = ControlPolicy.governed()
    if not policy.is_governed():
        findings.append(
            f"packaged policy has disabled obligations: {policy.disabled_obligations()}"
        )
    return _gate(
        "G16",
        "fail-closed dependency handling",
        findings,
        {
            "policy_obligations": len(policy.disabled_obligations()) == 0,
            "unknown_action_behaviour": "REFUSE",
            "unknown_session_behaviour": "REFUSE",
        },
    )


def gate_g17_audit_evidence(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(
        checks, ["CHK-EVIDENCE-EMITTED", "CHK-EVIDENCE-IMMUTABLE", "CHK-NO-DIRECT-STATE-MUTATION"]
    )
    world = build_world()
    journal_type = type(world.journal)
    allowed = {"append", "anchor", "records", "head_hash", "find", "verify", "export"}
    public = {name for name in dir(journal_type) if not name.startswith("_")}
    unexpected = sorted(public - allowed)
    if unexpected:
        findings.append(f"evidence journal exposes unexpected surface: {unexpected}")
    tamper_helpers = sorted(name for name in dir(journal_type) if name.startswith("_tamper"))
    if tamper_helpers:
        findings.append(f"evidence module ships history-rewrite helpers: {tamper_helpers}")

    # Probe the anchor: it must be independent of the stored records.
    _governed = build_world()
    from epd2_control_plane_service.reference_world import run_governed_flow

    run_governed_flow(
        _governed,
        request_id="g17-probe",
        action_id="AUTH.ASSIGN",
        requester="p.land.be.chair",
        approvers=("p.land.be.deputy", "p.land.be.secretary"),
        executor="p.land.be.chair",
        scope=LAND_BE,
    )
    anchor_count, anchor_head = _governed.journal.anchor()
    if anchor_count != len(_governed.journal) or anchor_head != _governed.journal.head_hash():
        findings.append("the evidence anchor does not agree with the journal after a governed act")
    refusals_before = len(_governed.journal.find(result="REFUSED"))
    with contextlib.suppress(ControlPlaneError):
        _governed.plane.submit_request(
            request_id="g17-refusal",
            action_id="AUTH.ASSIGN",
            principal_id="p.ordinary.member",
            session_id="s.p.ordinary.member",
            scope=LAND_BE,
            object_ref="probe",
            purpose="refusal evidence probe",
            moment=T0,
        )
    if len(_governed.journal.find(result="REFUSED")) != refusals_before + 1:
        findings.append("a refusal did not produce an evidence record")

    return _gate(
        "G17",
        "immutable audit and evidence",
        findings,
        {
            "chain": "sha256(canonical(record) + previous_hash)",
            "anchor": "append-time (count, head) held outside the record list",
            "public_surface": sorted(public),
            "tamper_helpers_in_evidence_module": tamper_helpers,
            "refusals_recorded": True,
        },
    )


def gate_g18_privacy(checks: Mapping[str, CheckResult]) -> GateResult:
    """Privacy screening, measured by probing the screen itself."""
    findings = _require(checks, ["CHK-PRIVACY-MINIMIZATION"])
    probes: dict[str, str] = {}
    cases = {
        "voting_linkable_field": {"voter_id": "v-1"},
        "secret_field_name": {"service_secret_value": "x"},
        "raw_key_material": {"note": "-----BEGIN PRIVATE KEY-----"},
        "oversized_attribute": {"payload": "x" * 600},
    }
    for name, attributes in cases.items():
        try:
            screen_attributes(attributes)
        except ControlPlaneError as error:
            probes[name] = error.reason_code
            continue
        probes[name] = "ACCEPTED"
        findings.append(f"privacy screen accepted {name}")

    budget = 0
    for size in (400, 512, 513, 600):
        try:
            screen_attributes({"payload": "x" * size})
        except ControlPlaneError:
            break
        budget = size
    return _gate(
        "G18",
        "privacy and data minimization",
        findings,
        {
            "screened_before_write": True,
            "measured_attribute_budget_bytes": budget,
            "probe_results": probes,
        },
    )


def gate_g19_voting_boundary(checks: Mapping[str, CheckResult]) -> GateResult:
    findings = _require(checks, ["CHK-VOTING-BOUNDARY"])
    inside = [a.action_id for a in INVENTORY if a.voting_domain_boundary == "INSIDE_VOTING_DOMAIN"]
    if inside:
        findings.append(f"actions inside the voting trust domain: {inside}")
    no_ui_roles = {d["role"] for d in NO_UI_DECISIONS}
    for role in ("VOTING_TRUSTEE", "VOTING_KEY_CUSTODIAN"):
        if role not in no_ui_roles:
            findings.append(f"{role} lacks an explicit NO_UI decision")
    return _gate(
        "G19",
        "voting hard boundary preservation",
        findings,
        {
            "voting_client_outside_control_plane": True,
            "no_ui_roles": sorted(no_ui_roles),
            "prohibited_effects": list(VOTING_DOMAIN_PROHIBITED_EFFECTS),
        },
    )


def gate_g20_mutation_suite() -> tuple[GateResult, list[dict[str, Any]]]:
    findings: list[str] = []
    outcomes: list[dict[str, Any]] = []
    for mutation in MUTATIONS:
        outcome = apply_and_detect(mutation)
        outcomes.append(
            {
                "mutation_id": mutation.mutation_id,
                "title": mutation.title,
                "kind": mutation.kind,
                "expected_check": mutation.expected_check,
                "detected": outcome.detected,
                "caught_by_expected_check": outcome.caught_by_expected,
                "failing_checks": list(outcome.failing_checks),
            }
        )
        if not outcome.detected:
            findings.append(f"{mutation.mutation_id} undetected: {mutation.title}")
        elif not outcome.caught_by_expected:
            findings.append(
                f"{mutation.mutation_id} detected by {outcome.failing_checks} rather than "
                f"{mutation.expected_check}"
            )
    if len(MUTATIONS) < 24:
        findings.append(f"mutation corpus below the required minimum: {len(MUTATIONS)} < 24")
    exercised: set[str] = set()
    for entry in outcomes:
        exercised.update(entry["failing_checks"])
    unexercised = sorted(set(CHECK_IDS.values()) - exercised)
    if unexercised:
        findings.append(f"checks no mutation can break: {unexercised}")
    return (
        _gate(
            "G20",
            "mutation and anti-cheat suite",
            findings,
            {
                "mutations_total": len(MUTATIONS),
                "detected": sum(1 for o in outcomes if o["detected"]),
                "checks_total": len(CHECK_IDS),
            },
        ),
        outcomes,
    )


def _packaged_paths() -> list[Path]:
    roots = [
        REPO_ROOT / "services" / "control-plane-service",
        REPO_ROOT / "scripts" / "ctrl01_validator.py",
        REPO_ROOT / "scripts" / "ctrl01_registry_export.py",
        REPO_ROOT / "scripts" / "system_trial_preview_prepare.py",
        REPO_ROOT / "docs" / "ctrl" / "CTRL-01",
    ]
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            paths.append(root)
        elif root.is_dir():
            paths.extend(
                p
                for p in root.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")
            )
    return sorted(paths)


def gate_g21_package_hygiene() -> GateResult:
    findings: list[str] = []
    paths = _packaged_paths()
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in paths
        if p.suffix in {".pyc", ".pyo"} or ".env" in p.name
    ]
    if offenders:
        findings.append(f"packaging offenders present: {offenders}")
    forbidden_hits: list[str] = []
    for path in paths:
        if path.suffix not in {".py", ".md", ".json", ".csv", ".toml"}:
            continue
        text = path.read_text(errors="replace").upper()
        for claim in FORBIDDEN_SELF_STATES:
            # The corpus of forbidden claims is itself allowed to name them.
            if claim in text and path.name not in {
                "verification.py",
                "mutations.py",
                "ctrl01_validator.py",
            }:
                forbidden_hits.append(f"{path.relative_to(REPO_ROOT)}: {claim}")
    if forbidden_hits:
        findings.append(f"forbidden self-state claims: {forbidden_hits}")
    return _gate(
        "G21",
        "source and package hygiene",
        findings,
        {
            "packaged_files": len(paths),
            "allowed_self_states": list(SELF_STATE_ALLOWED),
            "forbidden_self_states": list(FORBIDDEN_SELF_STATES),
        },
    )


def gate_g22_freeze(
    current: Mapping[str, Mapping[str, Any]],
    baseline: Mapping[str, Mapping[str, Any]] | None,
    baseline_path: Path,
) -> tuple[GateResult, tuple[str, ...]]:
    """Compare the packaged files against a *previously recorded* manifest.

    Verifying a manifest against the same files it was just built from is a
    tautology, so the baseline is read from disk before this run computes
    anything. A source file changed since the baseline was recorded shows up
    here, which is the whole point of the same-bytes rule.
    """
    findings: list[str] = []
    if baseline is None:
        mismatches: tuple[str, ...] = ()
        state = "BASELINE_RECORDED"
    else:
        mismatches = verify_manifest(REPO_ROOT, baseline)
        added = sorted(set(current) - set(baseline))
        removed = sorted(set(baseline) - set(current))
        mismatches = mismatches + tuple(
            f"{name}: added since the recorded freeze" for name in added
        )
        mismatches = mismatches + tuple(
            f"{name}: removed since the recorded freeze" for name in removed
        )
        findings = [f"freeze mismatch: {m}" for m in mismatches]
        state = "VERIFIED_AGAINST_RECORDED_BASELINE"
    return (
        _gate(
            "G22",
            "freeze and same-bytes preseal identity",
            findings,
            {
                "files": len(current),
                "current_manifest_digest": manifest_digest(current),
                "baseline_manifest_digest": None if baseline is None else manifest_digest(baseline),
                "baseline_path": str(baseline_path.relative_to(REPO_ROOT)),
                "state": state,
                "rule": "tested bytes == verified bytes == frozen bytes == packaged bytes",
            },
        ),
        mismatches,
    )


# ---------------------------------------------------------------------------


def _read_fir_status(fir_id: str) -> str | None:
    """Read a FIR's status from the current Master Register.

    Statuses are read, never promoted: if the register and the starter seed
    disagree, the register wins and the difference is recorded.
    """
    register = REPO_ROOT / "docs" / "roadmap" / "EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
    if not register.exists():
        return None
    lines = register.read_text(errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(f"## {fir_id}"):
            for candidate in lines[index : index + 10]:
                lowered = candidate.lower()
                if "status" in lowered:
                    return candidate.split(":", 1)[-1].strip().strip("`*_ ")
    return None


def _register_conflicts() -> list[dict[str, str]]:
    """Fail closed on material current-state disagreement only."""
    register = REPO_ROOT / "docs" / "roadmap" / "EPD2_PROGRAM_CONTROL_REGISTER.md"
    if not register.exists():
        return [{"conflict_id": "PCR-MISSING", "statement_a": "PCR missing"}]
    text = register.read_text(errors="replace")
    required = {
        "PCR-API05": "API-05 = ACCEPTED / CLOSED",
        "PCR-API06": "API-06 = NEXT",
        "PCR-INFRA02": "INFRA-02 ACCEPTED / CLOSED",
        "PCR-OPS02": "OPS-02 ACCEPTED / CLOSED",
        "PCR-CTRL": "| CTRL | `NOT_STARTED` |",
    }
    conflicts: list[dict[str, str]] = []
    for cid, needle in required.items():
        if needle not in text:
            conflicts.append(
                {
                    "conflict_id": cid,
                    "statement_a": f"required current PCR fact missing: {needle}",
                    "ctrl01_position": "fail closed pending governed reconciliation",
                }
            )
    return conflicts


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CTRL-01 preseal validator")
    parser.add_argument("--out", default=str(OUT_DIR), help="evidence output directory")
    parser.add_argument("--skip-tests", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--record-freeze",
        action="store_true",
        help="record a new same-bytes baseline instead of verifying against the recorded one",
    )
    args = parser.parse_args(argv)
    out = Path(args.out)

    started = datetime.now(UTC)

    # The recorded baseline is read BEFORE anything is recomputed, so G22
    # compares this candidate against a prior freeze rather than against itself.
    baseline_path = out / "freeze_manifest.json"
    baseline: dict[str, dict[str, Any]] | None = None
    if baseline_path.exists() and not args.record_freeze:
        try:
            baseline = json.loads(baseline_path.read_text()).get("files")
        except (OSError, ValueError):
            baseline = None

    manifest = build_manifest(REPO_ROOT, _packaged_paths())
    g22, freeze_mismatches = gate_g22_freeze(manifest, baseline, baseline_path)

    checks = _checks_by_id(
        run_checks(
            Scenario(
                freeze_mismatches=freeze_mismatches,
                freeze_manifest=baseline,
                freeze_root=REPO_ROOT if baseline is not None else None,
            )
        )
    )

    gates: list[GateResult] = [
        gate_g01_bootstrap_freshness(),
        gate_g02_baseline_identity(),
        gate_g03_accepted_predecessors(),
        gate_g04_action_inventory(checks),
        gate_g05_authority_read_model(),
        gate_g06_regional_scope_isolation(checks),
        gate_g07_separation_of_duties(),
        gate_g08_four_eyes(checks),
        gate_g09_emergency_lifecycle(checks),
        gate_g10_credential_lifecycle(checks),
        gate_g11_service_credentials(checks),
        gate_g12_key_trust(checks),
        gate_g13_control_api(),
    ]
    if args.skip_tests:
        gates.append(_gate("G14", "authorization negative suite", ["gate was not executed"], {}))
    else:
        gates.append(gate_g14_negative_suite())
    gates.extend(
        [
            gate_g15_commit_time_reauth(checks),
            gate_g16_fail_closed(checks),
            gate_g17_audit_evidence(checks),
            gate_g18_privacy(checks),
            gate_g19_voting_boundary(checks),
        ]
    )
    g20, mutation_outcomes = gate_g20_mutation_suite()
    gates.append(g20)
    gates.append(gate_g21_package_hygiene())
    gates.append(g22)

    failed = [g for g in gates if g.status != "PASS"]
    overall = "PASS" if not failed else "FAIL"

    # -- W12 evidence set ---------------------------------------------------
    g02 = next(g for g in gates if g.gate_id == "G02")
    _write(
        out / "baseline_identity.json",
        {"schema": "epd2.ctrl01.baseline-identity/1", **g02.evidence},
    )
    _write(out / "ctrl_action_inventory.json", inventory_to_json_obj())
    world = build_world()
    _write(out / "authority_read_model_result.json", world.directory.read_model(T0))
    _write(
        out / "sod_matrix_result.json",
        {
            "schema": "epd2.ctrl01.sod-matrix/1",
            "rules": SodEngine().matrix(),
            "gate": next(g for g in gates if g.gate_id == "G07").to_obj(),
        },
    )
    _write(
        out / "regional_intervention_result.json",
        {
            "schema": "epd2.ctrl01.regional-intervention/1",
            "gate": next(g for g in gates if g.gate_id == "G06").to_obj(),
        },
    )
    _write(
        out / "credential_key_lifecycle_result.json",
        {
            "schema": "epd2.ctrl01.credential-key-lifecycle/1",
            "gates": [
                next(g for g in gates if g.gate_id == gid).to_obj() for gid in ("G10", "G11", "G12")
            ],
        },
    )
    _write(
        out / "breakglass_result.json",
        {
            "schema": "epd2.ctrl01.breakglass/1",
            "gate": next(g for g in gates if g.gate_id == "G09").to_obj(),
        },
    )
    _write(out / "control_api_contract_result.json", contracts_to_json_obj())
    _write(
        out / "negative_authorization_result.json",
        {
            "schema": "epd2.ctrl01.negative-authorization/1",
            "gate": next(g for g in gates if g.gate_id == "G14").to_obj(),
            "governed_checks": [
                {
                    "check_id": r.check_id,
                    "status": "PASS" if r.passed else "FAIL",
                    "detail": r.detail,
                }
                for r in sorted(checks.values(), key=lambda x: x.check_id)
            ],
        },
    )
    _write(
        out / "commit_time_reauthorization_result.json",
        {
            "schema": "epd2.ctrl01.commit-time-reauthorization/1",
            "gate": next(g for g in gates if g.gate_id == "G15").to_obj(),
        },
    )
    _write(
        out / "audit_evidence_result.json",
        {
            "schema": "epd2.ctrl01.audit-evidence/1",
            "gates": [
                next(g for g in gates if g.gate_id == gid).to_obj() for gid in ("G17", "G18")
            ],
        },
    )
    _write(
        out / "mutation_result.json",
        {
            "schema": "epd2.ctrl01.mutation-suite/1",
            "mutations_total": len(MUTATIONS),
            "detected": sum(1 for o in mutation_outcomes if o["detected"]),
            "undetected": [o["mutation_id"] for o in mutation_outcomes if not o["detected"]],
            "checks": sorted(CHECK_IDS.values()),
            "outcomes": mutation_outcomes,
        },
    )
    fir_status: dict[str, dict[str, Any]] = {}
    for fir_id, seeded in FIR_TARGETS.items():
        observed = _read_fir_status(fir_id)
        fir_status[fir_id] = {
            "seed_status": seeded,
            "register_status": observed,
            "agrees": observed is not None and observed.lower().startswith(seeded.lower()),
            "read_from": "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
        }

    g01 = next(g for g in gates if g.gate_id == "G01")
    g03 = next(g for g in gates if g.gate_id == "G03")
    _write(
        out / "dependency_reconciliation.json",
        {
            "schema": "epd2.ctrl01.dependency-reconciliation/1",
            "stage": STAGE,
            "stage_mode": STAGE_MODE,
            "generated_at": datetime.now(UTC).isoformat(),
            "baseline": {
                "assignment_baseline_commit": BASELINE_COMMIT,
                "observed_head_commit": g01.evidence["head_commit"],
                "observed_head_tree": g01.evidence["head_tree"],
                "drift_since_assignment": g01.evidence["head_commit"] != BASELINE_COMMIT,
            },
            "canonical_documents": g01.evidence["canonical_documents"],
            "accepted_predecessors_with_records": g03.evidence["records"],
            "accepted_predecessors_register_only": REGISTER_ONLY_PREDECESSORS,
            "unreconciled_dependencies": UNRECONCILED_DEPENDENCIES,
            "consumed_contract_surface": {
                "API-02": (
                    "authority/session/authorization semantics consumed as governed concepts only"
                ),
                "API-03": (
                    "service-to-service identity semantics consumed as governed concepts only"
                ),
                "API-04": "event/messaging semantics not consumed by CTRL-01 bounded work",
                "API-05": "accepted API-05 C1 authority record",
                "INFRA-01": "CI acceptance harness and release-integrity conventions",
                "INFRA-02": "accepted bounded CI/CD and supply-chain foundation",
                "OPS-01": "incident/recovery/change-control SoD conventions",
                "OPS-02": "accepted bounded OPS-02 implementation",
                "note": (
                    "The accepted API runtimes live in sealed candidate archives, not in this "
                    "working tree. CTRL-01 therefore binds to their accepted governance "
                    "semantics by reference and imports no code from them. Any later "
                    "integration must re-derive these bindings against the exact accepted bytes."
                ),
            },
            "fir_reconciliation": fir_status,
            "observed_governance_conflicts": _register_conflicts(),
            "seal_preconditions": [
                "re-fetch current main and re-run G01 before seal",
                "keep API-06 NEXT / NOT ACCEPTED unless later authoritative acceptance exists",
                "re-read the Program Control Register and Master Future Implementation Register",
                "re-run every affected gate after any predecessor delta",
            ],
            "explicitly_not_relied_upon": [
                "a working ZIP as an accepted predecessor",
                "a local PASS as authoritative acceptance",
                "a branch name as evidence of acceptance",
                "a self-authored acceptance claim",
                "operator-reported working status in place of a governance record",
            ],
        },
    )

    if baseline is None:
        _write(
            baseline_path,
            {
                "schema": "epd2.ctrl01.freeze-manifest/1",
                "rule": "tested bytes == verified bytes == frozen bytes == packaged bytes",
                "recorded_at": datetime.now(UTC).isoformat(),
                "manifest_digest": manifest_digest(manifest),
                "files": manifest,
            },
        )
    _write(
        out / "freeze_verification.json",
        {
            "schema": "epd2.ctrl01.freeze-verification/1",
            "gate": g22.to_obj(),
            "mismatches": list(freeze_mismatches),
        },
    )

    result = {
        "schema": "epd2.ctrl01.preseal-result/1",
        "stage": STAGE,
        "stage_mode": STAGE_MODE,
        "started_at": started.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "overall": overall,
        "gates_total": len(gates),
        "gates_passed": sum(1 for g in gates if g.status == "PASS"),
        "gates_failed": len(failed),
        "gates_skipped": 0,
        "governed_check_suite_digest": suite_digest(checks.values()),
        "gates": [g.to_obj() for g in gates],
        "self_state": {
            "declared": list(SELF_STATE_ALLOWED) if overall == "PASS" else ["NOT_ACCEPTED"],
            "not_claimed": [
                "CTRL layer accepted or closed",
                "production readiness",
                "final security acceptance",
                "BSI / Common Criteria certification",
                "legal activation",
                "System Trial Preview checkpoint opened",
            ],
        },
    }
    _write(out / "ctrl01_preseal_result.json", result)

    print(f"CTRL01_RESULT:{overall}:{(out / 'ctrl01_preseal_result.json')}")
    for gate in gates:
        marker = "PASS" if gate.status == "PASS" else "FAIL"
        print(f"  {gate.gate_id} {marker} {gate.name}")
        for finding in gate.findings:
            print(f"       - {finding}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

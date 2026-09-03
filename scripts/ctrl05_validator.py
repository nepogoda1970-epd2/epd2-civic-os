#!/usr/bin/env python3
"""CTRL-05 fifty-six-gate developer validator.

Every gate executes a probe against the real runtime, the real CTRL-02/03/04
evidence planes, the repository or a governed evidence file, and records what
it observed. A gate PASSes only on the evidence its own probe produced; no
gate inherits PASS from another. The validator emits
`CTRL05_RESULT:PASS|FAIL:<n>/56_PASS` and a PRESEAL result file whose
self-state is always `CANDIDATE_NOT_ACCEPTED`.

This validator claims no CTRL-05 acceptance, no CTRL-layer closure, no
production readiness and no security certification.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services/control-plane-service"
VALIDATION = ROOT / "validation/ctrl05"
sys.path.insert(0, str(SERVICE / "src"))
sys.path.insert(0, str(SERVICE / "tests"))
sys.path.insert(0, str(ROOT / "packages/python/epd2-core/src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ctrl05_common import (  # type: ignore[import-not-found]  # noqa: E402
    RUNTIME_FILES,
    runtime_source_digest,
)

BASE_COMMIT = "2ceb77be91448462262b84f278a00cfe6dd4228e"
BASE_TREE = "ec057046e235bbd438a4aaa1a23e9f40dff804a2"
MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
SELF_STATE = "CANDIDATE_NOT_ACCEPTED"

#: (acceptance record path, accepted candidate sha256, accepted size)
PREDECESSORS: dict[str, tuple[str, str, int]] = {
    "CTRL-01": (
        "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json",
        "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5",
        190099,
    ),
    "CTRL-02": (
        "docs/ctrl/CTRL-02/CTRL02_ACCEPTANCE_RECORD.json",
        "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e",
        16720456,
    ),
    "CTRL-03": (
        "docs/ctrl/CTRL-03/CTRL03_C1_ACCEPTANCE_RECORD.json",
        "89fca0f6c975a7c0e1eb70c2e3ad5229830e781c91d86637a81f99e39ac7b0ff",
        16788860,
    ),
    "CTRL-04": (
        "docs/ctrl/CTRL-04/CTRL04_C1_ACCEPTANCE_RECORD.json",
        "346acc12316ac4a8f2be45c889aa9002172710da61c67ec88e54a976bb5733a2",
        18419399,
    ),
}
INFRA_OPS: dict[str, tuple[str, str]] = {
    "INFRA-01": (
        "docs/infra/INFRA-01/INFRA01_C3_ACCEPTANCE_RECORD.json",
        "5cd90da141056badc38ee3fb34f2d648002ace5b87c6a0cce1d331431364b131",
    ),
    "INFRA-02": (
        "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json",
        "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
    ),
    "INFRA-03": (
        "docs/infra/INFRA-03/INFRA03_C1_ACCEPTANCE_RECORD.json",
        "6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1",
    ),
    "OPS-01": (
        "docs/ops/OPS-01/OPS01_C2_ACCEPTANCE_RECORD.json",
        "39a6b02af03269a8ebf61216503fa03df2abf4e5194aa3c45c6f4bb176f2ad27",
    ),
    "OPS-02": (
        "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json",
        "ac3b543b0cb3a8e45f7d973c841769d0b4c6e7af649a54aee034f3e0b6afc125",
    ),
}
NOT_ACCEPTED_DEPENDENCIES = ("OPS-03",)

#: Files installed by the accepted predecessors that CTRL-05 must not touch.
INSTALLED_PREDECESSOR_FILES = (
    "services/control-plane-service/src/epd2_control_plane_service/authority.py",
    "services/control-plane-service/src/epd2_control_plane_service/audit.py",
    "services/control-plane-service/src/epd2_control_plane_service/regional_operations.py",
    "services/control-plane-service/src/epd2_control_plane_service/credential_lifecycle.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_console.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_adapters.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_api.py",
    "services/control-plane-service/src/epd2_control_plane_service/operations_console.html",
)

GATE_NAMES = (
    "exact_repository_baseline_recorded",
    "mandatory_bootstrap_docs_read_and_digested",
    "exact_ctrl01_accepted_identity_bound",
    "exact_ctrl02_accepted_identity_bound",
    "exact_ctrl03_accepted_identity_bound",
    "exact_ctrl04_accepted_identity_bound",
    "installed_predecessor_runtime_unmodified",
    "relevant_infra_and_ops_identities_bound_or_recorded_unaccepted",
    "no_universal_auditor_capability",
    "exact_organization_scope_without_inheritance",
    "exact_oversight_unit_scope_without_inheritance",
    "oversight_mandate_required_for_any_visibility",
    "mandate_bound_to_live_authority_grant_and_version",
    "mandate_carries_rule_version_and_source_decision",
    "audit_rights_are_disjoint",
    "operational_rights_grant_no_oversight",
    "oversight_grants_no_operational_execution",
    "no_shell_sql_ssh_exec_or_cluster_surface",
    "no_raw_secret_visibility_in_any_surface",
    "no_secret_material_in_evidence_or_export",
    "source_evidence_immutable_to_ctrl05",
    "annotation_is_an_append_only_superseding_record",
    "integrity_independently_re_derived",
    "broken_hash_chain_reported_not_hidden",
    "untrustworthy_evidence_cannot_carry_a_finding",
    "fail_closed_on_unavailable_source_or_authority",
    "unmapped_evidence_stream_is_invisible",
    "no_unbounded_global_evidence_query",
    "bounded_correlation_graph_without_person_nodes",
    "action_chain_reconstructed_from_real_ctrl04_evidence",
    "no_persistent_voting_person_identifier",
    "no_voting_isolation_bypass_reference_only",
    "no_new_cross_domain_universal_person_index",
    "typed_oversight_mandate",
    "typed_evidence_reference_and_envelope",
    "typed_review_case_and_disposition",
    "typed_finding_and_dispute",
    "typed_attestation_bound_to_case_version",
    "typed_export_request_and_redaction_decision",
    "review_history_is_append_only",
    "case_version_optimistic_concurrency_enforced",
    "disposition_required_before_attestation",
    "attestation_required_before_closure",
    "commit_time_reauthorization_on_every_governed_act",
    "stale_authority_rejected_at_commit_time",
    "evidence_divergence_rejected_at_commit_time",
    "ticket_replay_rejected",
    "idempotency_enforced_on_every_mutation",
    "purpose_bound_export_with_evidenced_redaction",
    "every_refusal_is_evidence_bearing",
    "oversight_evidence_survives_restart_and_reverifies",
    "rewritten_or_resealed_checkpoint_refused",
    "frontend_asserts_neither_authority_nor_integrity",
    "mutation_and_e2e_evidence_bound_to_runtime_digest",
    "browser_journeys_executed_in_a_real_browser",
    "package_pre_post_verification_and_review_readiness",
)
assert len(GATE_NAMES) == 56, len(GATE_NAMES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(name: str, payload: dict[str, Any]) -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load(name: str) -> dict[str, Any]:
    path = VALIDATION / name
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def refusal(fn: Callable[[], Any]) -> str | None:
    """The reason code of the refusal a probe expected, or None if it did not
    refuse. A gate that expects a refusal fails when nothing is refused."""
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    try:
        fn()
    except AuthorizationRefused as exc:
        return str(exc.reason_code)
    return None


def world(**kwargs: Any) -> Any:
    from _ctrl05_builders import World  # type: ignore[import-not-found]

    return World(**kwargs)


def source(*names: str) -> str:
    return "\n".join((ROOT / n).read_text() for n in names)


RUNTIME_SOURCE = property


# ---------------------------------------------------------------------------
# Gate probes. Each returns (passed, observations).
# ---------------------------------------------------------------------------

Probe = Callable[[], tuple[bool, dict[str, Any]]]


def g01() -> tuple[bool, dict[str, Any]]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    obs: dict[str, Any] = {
        "observed_commit": head,
        "observed_tree": tree,
        "contract_commit": BASE_COMMIT,
        "contract_tree": BASE_TREE,
        "pcr_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md"),
        "master_sha256": sha256(
            ROOT / "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md"
        ),
        "entrypoint_sha256": sha256(ROOT / "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md"),
    }
    write("baseline_identity.json", {"schema": "epd2.ctrl05.baseline-identity/1", **obs})
    return bool(head == BASE_COMMIT and tree == BASE_TREE), obs


def g02() -> tuple[bool, dict[str, Any]]:
    docs = [
        "docs/roadmap/EPD2_PROJECT_ENTRYPOINT.md",
        "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md",
        "docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md",
        "docs/ctrl/CTRL-01/CTRL-01-SPECIFICATION.md",
        "docs/ctrl/CTRL-01/CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json",
        "docs/ctrl/CTRL-02/CTRL02_ACCEPTANCE_RECORD.json",
        "docs/ctrl/CTRL-03/CTRL03_STAGE_CONTRACT.md",
        "docs/ctrl/CTRL-04/CTRL04_STAGE_CONTRACT.md",
        "docs/ctrl/CTRL-04/CTRL04_SPECIFICATION.md",
        "docs/ctrl/CTRL-04/CTRL04_C1_ACCEPTANCE_RECORD.json",
        "docs/ctrl/CTRL-04/CTRL04_C1_CANONICAL_INSTALLATION_MANIFEST.json",
    ]
    digests = {d: sha256(ROOT / d) for d in docs if (ROOT / d).is_file()}
    missing = [d for d in docs if not (ROOT / d).is_file()]
    write(
        "bootstrap_reading.json",
        {"schema": "epd2.ctrl05.bootstrap-reading/1", "documents": digests, "missing": missing},
    )
    return not missing, {"documents_read": len(digests), "missing": missing}


def _predecessor(stage: str) -> tuple[bool, dict[str, Any]]:
    path, expected_sha, expected_size = PREDECESSORS[stage]
    from epd2_control_plane_service import oversight_console as oc

    bound = {
        "CTRL-01": oc.CTRL01_ACCEPTED_SHA256,
        "CTRL-02": oc.CTRL02_ACCEPTED_SHA256,
        "CTRL-03": oc.CTRL03_ACCEPTED_SHA256,
        "CTRL-04": oc.CTRL04_ACCEPTED_SHA256,
    }[stage]
    record = json.loads((ROOT / path).read_text())
    text = json.dumps(record)
    obs = {
        "record": path,
        "record_decision": record.get("decision"),
        "expected_sha256": expected_sha,
        "runtime_bound_sha256": bound,
        "sha_in_record": expected_sha in text,
        "size_in_record": str(expected_size) in text,
    }
    ok = (
        bound == expected_sha
        and expected_sha in text
        and str(expected_size) in text
        and "ACCEPTED" in str(record.get("decision", ""))
    )
    return ok, obs


def g03() -> tuple[bool, dict[str, Any]]:
    return _predecessor("CTRL-01")


def g04() -> tuple[bool, dict[str, Any]]:
    return _predecessor("CTRL-02")


def g05() -> tuple[bool, dict[str, Any]]:
    return _predecessor("CTRL-03")


def g06() -> tuple[bool, dict[str, Any]]:
    return _predecessor("CTRL-04")


def g07() -> tuple[bool, dict[str, Any]]:
    """The installed predecessor runtime is byte-identical to `main`."""
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE_COMMIT, "--", *INSTALLED_PREDECESSOR_FILES],
        cwd=ROOT,
        text=True,
    ).split()
    digests = {f: sha256(ROOT / f) for f in INSTALLED_PREDECESSOR_FILES}
    return not changed, {"modified": changed, "files": len(digests), "digests": digests}


def g08() -> tuple[bool, dict[str, Any]]:
    bound = {}
    for stage, (path, expected) in INFRA_OPS.items():
        record = ROOT / path
        bound[stage] = {
            "record_present": record.is_file(),
            "expected_sha256": expected,
            "sha_in_record": record.is_file() and expected in record.read_text(),
        }
    unaccepted = {}
    for stage in NOT_ACCEPTED_DEPENDENCIES:
        hits = list((ROOT / "docs").rglob(f"*{stage.replace('-', '')}*ACCEPTANCE_RECORD*.json"))
        unaccepted[stage] = {"acceptance_record_found": [p.name for p in hits]}
    ok = all(v["sha_in_record"] for v in bound.values()) and all(
        not v["acceptance_record_found"] for v in unaccepted.values()
    )
    write(
        "dependency_identities.json",
        {
            "schema": "epd2.ctrl05.dependency-identities/1",
            "bound": bound,
            "recorded_unaccepted": unaccepted,
        },
    )
    return ok, {"bound": bound, "recorded_unaccepted": unaccepted}


def g09() -> tuple[bool, dict[str, Any]]:
    """A wildcard or universal capability grants no oversight competence."""
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    code = refusal(lambda: w.search(principal="super-admin"))
    src = source(RUNTIME_FILES[0])
    return (
        code == oc.OversightRefusal.UNIVERSAL_AUDITOR.value
        and oc.UNIVERSAL_AUDITOR_EXISTS is False
        and "UNIVERSAL_CAPABILITY_NAMES" in src
    ), {
        "refusal": code,
        "universal_auditor_exists": oc.UNIVERSAL_AUDITOR_EXISTS,
        "universal_names": sorted(oc.UNIVERSAL_CAPABILITY_NAMES),
    }


def g10() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import BAVARIA_UNIT, OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    other_org = refusal(lambda: w.search(principal="bavaria-auditor", scope=OPS_UNIT))
    empty = w.search(principal="bavaria-auditor", scope=BAVARIA_UNIT)
    contains = OPS_UNIT.contains(oc.OversightScope("DE-BE", "org-berlin", "unit-privacy-oversight"))
    return (
        other_org == oc.OversightRefusal.WRONG_ORGANIZATION_SCOPE.value
        and empty["matched"] == 0
        and contains is False
    ), {"cross_org_refusal": other_org, "own_scope_matched": empty["matched"], "contains": contains}


def g11() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service import oversight_console as oc
    from epd2_control_plane_service.oversight_sources import EvidencePlane

    w = world()
    other_unit = refusal(lambda: w.search(principal="privacy-officer", scope=OPS_UNIT))
    # Unmapped evidence is invisible: unit scope fails closed.
    w.service.evidence_units.pop(f"{EvidencePlane.CTRL04.value}:{w.ctrl04_source.stream_id()}")
    after = w.search(limit=200)
    ctrl04 = [r for r in after["records"] if r["reference"]["plane"] == EvidencePlane.CTRL04.value]
    return (other_unit == oc.OversightRefusal.WRONG_UNIT_SCOPE.value and not ctrl04), {
        "cross_unit_refusal": other_unit,
        "ctrl04_visible_when_unmapped": len(ctrl04),
    }


def g12() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    code = refusal(lambda: w.search(principal="unmandated"))
    return code == oc.OversightRefusal.NO_MANDATE.value, {"refusal": code}


def g13() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    missing_grant = refusal(lambda: w.search(principal="stale-auditor"))
    w2 = world()
    w2.search()
    grant = w2.authorities._grants["ag-read"]
    w2.authorities._grants["ag-read"] = type(grant)(
        grant_id="ag-read-v2",
        actor_id=grant.actor_id,
        actor_class=grant.actor_class,
        capability=grant.capability,
        scope=grant.scope,
        version=2,
    )
    reissued = refusal(lambda: w2.search())
    return (
        missing_grant
        in {
            oc.OversightRefusal.STALE_AUTHORITY.value,
            oc.OversightRefusal.AUTHORITY_UNRESOLVABLE.value,
        }
        and reissued == oc.OversightRefusal.STALE_AUTHORITY.value
    ), {"missing_grant": missing_grant, "reissued_grant": reissued}


def g14() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT, RULE, _mandate  # type: ignore[import-not-found]
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    mandate = w.service.mandate("MND-auditor")
    assert mandate is not None
    try:
        oc.OversightMandate(
            mandate_id="MND-bad",
            subject_ref="auditor",
            scope=OPS_UNIT,
            planes=frozenset(oc.EvidencePlane),
            rights=frozenset({oc.AuditRight.READ}),
            rule_version="",
            source_decision_ref="",
            authority_bindings=frozenset({("AUDIT.READ", "ag-read")}),
            valid_from=mandate.valid_from,
            valid_until=mandate.valid_until,
        )
        rejected = False
    except ValueError:
        rejected = True
    unbacked = False
    try:
        _mandate("MND-x", "auditor", OPS_UNIT, frozenset({oc.AuditRight.EXPORT}), {})
    except ValueError:
        unbacked = True
    return (
        bool(mandate.rule_version == RULE and mandate.source_decision_ref) and rejected and unbacked
    ), {
        "competence_ref": mandate.competence_ref,
        "empty_rule_rejected": rejected,
        "unbacked_right_rejected": unbacked,
    }


def g15() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    review_without_right = refusal(lambda: w.open_case(principal="read-only-auditor"))
    case = w.open_case()
    w.dispose(case.case_id, oc.ReviewState.NO_FINDING)
    attest_without_right = refusal(
        lambda: w.prepare(case.case_id, "ATTEST", oc.AuditRight.ATTEST, principal="auditor")
    )
    export_without_right = refusal(
        lambda: w.prepare(
            case.case_id, "EXPORT", oc.AuditRight.EXPORT, principal="dual-hat-operator"
        )
    )
    rights = {r.value for r in oc.AuditRight}
    return (
        review_without_right == oc.OversightRefusal.NO_RIGHT.value
        and attest_without_right == oc.OversightRefusal.NO_RIGHT.value
        and export_without_right == oc.OversightRefusal.NO_RIGHT.value
        and rights
        == {"AUDIT.READ", "AUDIT.CORRELATE", "AUDIT.REVIEW", "AUDIT.ATTEST", "AUDIT.EXPORT"}
    ), {
        "review": review_without_right,
        "attest": attest_without_right,
        "export": export_without_right,
        "rights": sorted(rights),
    }


def g16() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service import oversight_console as oc

    forbidden = set(oc.FORBIDDEN_OPERATIONAL_RIGHTS)
    w = world()
    # An operational right is never accepted as an oversight right.
    accepted = [r for r in forbidden if r in {x.value for x in oc.AuditRight}]
    # The dual-hat principal holds OPS.EXECUTE and still needs a mandate right.
    code = refusal(
        lambda: w.prepare(
            w.open_case(principal="dual-hat-operator").case_id,
            "EXPORT",
            oc.AuditRight.EXPORT,
            principal="dual-hat-operator",
        )
    )
    return (
        not accepted
        and {"OPS.EXECUTE", "SECRET.RAW_READ", "KEY.CUSTODY", "AUTHORITY.UNIVERSAL_ADMIN"}
        <= forbidden
        and code == oc.OversightRefusal.NO_RIGHT.value
    ), {"forbidden_operational_rights": sorted(forbidden), "dual_hat_export": code}


def g17() -> tuple[bool, dict[str, Any]]:
    """Behavioural: a full oversight journey by a principal who also holds
    `OPS.EXECUTE` leaves the CTRL-04 plane byte-identical."""
    from epd2_control_plane_service import oversight_console as oc

    w = world()
    before = (
        len(w.ctrl04.journal),
        w.ctrl04.journal.head_hash(),
        tuple(sorted((a.action_id, a.state.value) for a in w.ctrl04.actions())),
        len(w.ctrl04._results),
    )
    refs = w.references()
    case = w.open_case(principal="dual-hat-operator", evidence_refs=refs[:2])
    w.dispose(case.case_id, oc.ReviewState.FINDING_RAISED, principal="dual-hat-operator")
    w.raise_finding(case.case_id, oc.FindingSeverity.HIGH, refs[0], principal="dual-hat-operator")
    w.service.link_remediation(
        actor_ref="dual-hat-operator",
        session_id="sess-dual-hat-operator",
        csrf_token="csrf-dual-hat-operator",
        case_id=case.case_id,
        remediation_plane="CTRL-04",
        remediation_ref=w.ctrl04_action_id,
        idempotency_key="g17-rem",
        now=w.tick(),
    )
    after = (
        len(w.ctrl04.journal),
        w.ctrl04.journal.head_hash(),
        tuple(sorted((a.action_id, a.state.value) for a in w.ctrl04.actions())),
        len(w.ctrl04._results),
    )
    absent = [
        n
        for n in ("request", "approve", "commit", "execute", "dispatch", "resolve", "cancel")
        if hasattr(w.service, n)
    ]
    link = w.service.remediations_of(case.case_id)[0]
    return (
        before == after
        and not absent
        and link.executed_by_ctrl05 is False
        and oc.REVIEWER_MAY_EXECUTE_OPERATIONS is False
    ), {
        "ctrl04_unchanged": before == after,
        "journal_head_before": before[1],
        "journal_head_after": after[1],
        "operational_methods_present": absent,
        "remediation_executed_by_ctrl05": link.executed_by_ctrl05,
    }


def g18() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_api import (
        FORBIDDEN_SURFACES,
        OversightApp,
    )
    from epd2_control_plane_service.oversight_console import OversightRefusal

    w = world()
    app = OversightApp(w.service, clock=lambda: w.tick())
    observed = {}
    for path in FORBIDDEN_SURFACES:
        status, payload, _ = app.handle("POST", path, {"X-EPD2-Session": "sess-auditor"}, b"{}")
        observed[path] = [status, payload.get("error") if isinstance(payload, dict) else None]
    ok = all(
        v[0] == 403 and v[1] == OversightRefusal.EXECUTION_SURFACE_ABSENT.value
        for v in observed.values()
    )
    src = source(RUNTIME_FILES[0], RUNTIME_FILES[1], RUNTIME_FILES[2])
    # No execution primitive may exist in the runtime at all. `kubectl`, `sql`
    # and the rest appear in the runtime only as *refused route names*, which
    # is what makes their absence observable from outside — so the check is
    # that each is declared absent, not that the word never occurs.
    banned = [
        token
        for token in (
            "subprocess.",
            "os.system",
            "os.popen",
            "pty.spawn",
            "shutil.rmtree",
            "eval(",
            "exec(",
            "__import__(",
        )
        if token in src
    ]
    # `re.compile` is a regular-expression compile, not code execution; the
    # bare builtin would be, so it is checked for separately.
    banned += [t for t in ("compile(",) if t in src.replace("re.compile(", "")]
    declared_absent = {
        kind: any(kind in p for p in FORBIDDEN_SURFACES)
        for kind in ("shell", "exec", "sql", "ssh", "kubectl", "secrets", "keys")
    }
    return (ok and not banned and all(declared_absent.values())), {
        "surfaces": observed,
        "banned_primitives": banned,
        "declared_absent": declared_absent,
    }


def g19() -> tuple[bool, dict[str, Any]]:
    """No route, method or read model exposes secret material.

    The probe *injects* a secret into every governed free-text field first: a
    sweep over fields nobody ever wrote a secret into cannot fail, and so is
    not a check at all.
    """
    from epd2_control_plane_service.oversight_api import OversightApp
    from epd2_control_plane_service.oversight_console import FindingSeverity, ReviewState

    w = world()
    app = OversightApp(w.service, clock=lambda: w.tick())
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2], title="password=hunter2 sk_live_abcdef review")
    w.service.clarify(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        text="the token was sk_live_abcdef and " + "AKIA" + "IOSFODNN7EXAMPLE",
        evidence_ref=refs[0],
        idempotency_key="g19-clar",
        now=w.tick(),
    )
    w.service.link_remediation(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        remediation_plane="sk_live_abcdef password=hunter2",
        remediation_ref="OPA-000001",
        idempotency_key="g19-rem",
        now=w.tick(),
    )
    w.dispose(
        case.case_id,
        ReviewState.FINDING_RAISED,
        rationale="the credential sk_live_abcdef was in the log",
    )
    w.raise_finding(
        case.case_id,
        FindingSeverity.HIGH,
        refs[0],
        summary="token sk_live_abcdef appeared in the provider log",
    )
    w.attest(case.case_id, statement="sk_live_abcdef was observed")
    scope_query = (
        f"?region_id={case.scope.region_id}&org_id={case.scope.org_id}&unit_id={case.scope.unit_id}"
    )
    bodies: list[Any] = []
    for path in (
        "/audit/v1/me",
        "/audit/v1/journal",
        "/audit/v1/read-model" + scope_query,
        "/audit/v1/cases" + scope_query,
        f"/audit/v1/cases/{case.case_id}" + scope_query,
        "/audit/v1/exports" + scope_query,
    ):
        _s, payload, _c = app.handle("GET", path, {"X-EPD2-Session": "sess-auditor"}, b"")
        bodies.append(payload)
    _s, search, _c = app.handle(
        "POST",
        "/audit/v1/evidence/search",
        {"X-EPD2-Session": "sess-auditor"},
        json.dumps(
            {
                "region_id": "DE-BE",
                "org_id": "org-berlin",
                "unit_id": "unit-operations-audit",
                "limit": 200,
            }
        ).encode(),
    )
    bodies.append(search)
    text = json.dumps(bodies).lower()
    markers = [
        "sk_live_",
        "hunter2",
        "begin private key",
        "akia" + "iosfodnn7example",
        "-----begin",
        "csrf-auditor",
    ]
    hits = [m for m in markers if m in text]
    secret_routes = [
        n
        for n in ("secret", "secrets", "key_material", "reveal", "decrypt")
        if hasattr(w.service, n)
    ]
    return not hits and not secret_routes, {"marker_hits": hits, "secret_methods": secret_routes}


def g20() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import EXPORT_PURPOSES

    w = world()
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:3])
    hits: dict[str, list[str]] = {}
    for purpose in EXPORT_PURPOSES:
        result = w.export(case.case_id, purpose, refs[:3], idempotency_key=f"g20-{purpose}")
        text = json.dumps(result).lower()
        hits[purpose] = [
            m for m in ("sk_live_", "hunter2", "begin private key", "akia") if m in text
        ]
    journal = json.dumps(w.service.journal.export()).lower()
    journal_hits = [m for m in ("sk_live_", "hunter2", "begin private key") if m in journal]
    return (not any(hits.values()) and not journal_hits), {
        "export_hits": hits,
        "journal_hits": journal_hits,
    }


def g21() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import SOURCE_EVIDENCE_IS_MUTABLE

    w = world()
    ctrl02_before = [(e.event_id, e.event_hash) for e in w.ctrl02._events]
    ctrl03_before = [(e.event_id, e.event_hash) for e in w.ctrl03.events]
    ctrl04_before = w.ctrl04.journal.head_hash()
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2])
    w.service.clarify(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        text="annotated, not edited",
        evidence_ref=refs[0],
        idempotency_key="g21",
        now=w.tick(),
    )
    w.dispose(
        case.case_id,
        __import__(
            "epd2_control_plane_service.oversight_console", fromlist=["ReviewState"]
        ).ReviewState.NO_FINDING,
    )
    unchanged = (
        [(e.event_id, e.event_hash) for e in w.ctrl02._events] == ctrl02_before
        and [(e.event_id, e.event_hash) for e in w.ctrl03.events] == ctrl03_before
        and w.ctrl04.journal.head_hash() == ctrl04_before
    )
    # The behavioural probe: nothing reachable from the console exposes a
    # method that could act on a plane, and the console holds no public handle
    # to the planes at all.
    reachable = [
        f"{name}.{verb}"
        # `journal` is CTRL-05's *own* append-only evidence store; appending to
        # it is the point. Every other attribute must be inert.
        for name in vars(w.service)
        if name != "journal"
        for verb in (
            "approve",
            "commit",
            "execute",
            "dispatch",
            "resolve",
            "activate",
            "revoke",
            "rotate",
            "append",
            "write",
            "delete",
        )
        if hasattr(getattr(w.service, name), verb)
    ]
    return (
        unchanged
        and not reachable
        and not hasattr(w.service, "sources")
        and SOURCE_EVIDENCE_IS_MUTABLE is False
    ), {
        "planes_unchanged": unchanged,
        "reachable_plane_methods": reachable,
        "public_sources_attribute": hasattr(w.service, "sources"),
    }


def g22() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import ReviewState

    w = world()
    case = w.open_case()
    w.dispose(case.case_id, ReviewState.NEEDS_CLARIFICATION, rationale="first")
    w.dispose(case.case_id, ReviewState.NO_FINDING, rationale="second")
    view = w.service.case_view(case.case_id)
    states = [d["state"] for d in view["dispositions"]]
    supersedes = view["dispositions"][1]["supersedes"]
    return (
        states == [ReviewState.NEEDS_CLARIFICATION.value, ReviewState.NO_FINDING.value]
        and supersedes == view["dispositions"][0]["disposition_id"]
        and view["history_is_append_only"] is True
        and view["clarifications"] == []
    ), {"states": states, "supersedes": supersedes}


def g23() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_sources import IntegrityState

    w = world()
    verdicts = {}
    for plane in ("CTRL-02", "CTRL-03", "CTRL-04"):
        ref = next(r for r in w.references() if r.startswith(plane))
        verdict = w.service.verify_evidence(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            reference_key=ref,
            now=w.tick(),
        )
        verdicts[plane] = {
            "state": verdict["state"],
            "recorded": verdict["recorded_hash"][:16],
            "recomputed": verdict["recomputed_hash"][:16],
            "verified_by": verdict["verified_by"],
        }
    ok = all(
        v["state"] == IntegrityState.VERIFIED.value and v["recorded"] == v["recomputed"]
        for v in verdicts.values()
    ) and all(v["verified_by"].startswith("CTRL-05") for v in verdicts.values())
    return ok, verdicts


def _tamper_ctrl02(w: Any, index: int, **changes: Any) -> None:
    events = list(w.ctrl02._events)
    original = events[index]
    events[index] = type(original)(
        **{
            **{f: getattr(original, f) for f in original.__dataclass_fields__},
            **changes,
        }
    )
    w.ctrl02._events = events


def g24() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_sources import IntegrityState

    w = world()
    _tamper_ctrl02(w, 1, reason="rewritten after the fact")
    rewritten = {
        r["reference"]["key"]: r["integrity"]["state"]
        for r in w.search(limit=200)["records"]
        if r["reference"]["plane"] == "CTRL-02"
    }
    w2 = world()
    events = list(w2.ctrl02._events)
    del events[1]
    w2.ctrl02._events = events
    truncated = {
        r["reference"]["key"]: r["integrity"]["state"]
        for r in w2.search(limit=200)["records"]
        if r["reference"]["plane"] == "CTRL-02"
    }
    broken = {
        IntegrityState.HASH_MISMATCH.value,
        IntegrityState.CHAIN_BROKEN.value,
        IntegrityState.SEQUENCE_BROKEN.value,
    }
    return (bool(set(rewritten.values()) & broken) and bool(set(truncated.values()) & broken)), {
        "rewritten": rewritten,
        "truncated": truncated,
    }


def g25() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import FindingSeverity, OversightRefusal

    w = world()
    refs = [r for r in w.references() if r.startswith("CTRL-02")]
    case = w.open_case(evidence_refs=refs[:1])
    _tamper_ctrl02(w, 0, reason="rewritten")
    code = refusal(lambda: w.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0]))
    return code in {
        OversightRefusal.EVIDENCE_UNTRUSTWORTHY.value,
        OversightRefusal.EVIDENCE_DIVERGED.value,
        OversightRefusal.UNKNOWN_EVIDENCE.value,
    }, {"refusal": code}


def g26() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_console import OversightRefusal

    w = world()
    w.ctrl02_source.available = False
    reported = w.search(limit=200)
    w2 = world()
    w2.ctrl04_source.available = False
    chain = refusal(
        lambda: w2.service.action_chain(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            correlation_ref=w2.ctrl04_correlation,
            now=w2.tick(),
        )
    )
    return (
        "CTRL-02" in reported["unavailable_planes"]
        and not [r for r in reported["records"] if r["reference"]["plane"] == "CTRL-02"]
        and chain == OversightRefusal.SOURCE_UNAVAILABLE.value
    ), {"search_unavailable": reported["unavailable_planes"], "chain_refusal": chain}


def g27() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import BAVARIA_UNIT, OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_sources import EvidencePlane

    w = world()
    for plane, src in (
        (EvidencePlane.CTRL02, w.ctrl02_source),
        (EvidencePlane.CTRL03, w.ctrl03_source),
        (EvidencePlane.CTRL04, w.ctrl04_source),
    ):
        w.service.evidence_units.pop(f"{plane.value}:{src.stream_id()}")
    blind = w.search(limit=200)
    # Identically named units in two organizations must not merge.
    w2 = world()
    same_name = OPS_UNIT.unit_id == BAVARIA_UNIT.unit_id
    bavaria = w2.search(principal="bavaria-auditor", scope=BAVARIA_UNIT)
    return (blind["matched"] == 0 and same_name and bavaria["matched"] == 0), {
        "matched_when_unmapped": blind["matched"],
        "unit_names_identical": same_name,
        "cross_org_same_unit_matched": bavaria["matched"],
    }


def g28() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_console import (
        MAX_QUERY_LIMIT,
        EvidenceQuery,
        OversightRefusal,
    )

    w = world()
    try:
        EvidenceQuery(scope=OPS_UNIT, limit=MAX_QUERY_LIMIT + 1)
        bounded = False
    except ValueError:
        bounded = True
    coarse = [
        refusal(
            lambda anchor=anchor: w.service.action_chain(
                actor_ref="auditor",
                session_id="sess-auditor",
                scope=OPS_UNIT,
                correlation_ref=anchor,
                now=w.tick(),
            )
        )
        for anchor in ("", "*", "ALL", "GLOBAL")
    ]
    truncated = w.search(limit=2)
    no_global = not hasattr(w.service, "all_evidence") and not hasattr(w.service, "dump")
    return (
        bounded
        and all(c == OversightRefusal.UNBOUNDED_QUERY.value for c in coarse)
        and truncated["truncated"] is True
        and no_global
    ), {"limit_bounded": bounded, "coarse_refusals": coarse, "truncated": truncated["truncated"]}


def g29() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_console import (
        MAX_GRAPH_DEPTH,
        MAX_GRAPH_NODES,
        OversightRefusal,
    )
    from epd2_control_plane_service.oversight_sources import PERSON_IDENTIFIER_FIELDS

    w = world()
    graph = w.service.correlation_graph(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        anchor=w.ctrl04_correlation,
        depth=1,
        now=w.tick(),
    ).as_dict()
    over_depth = refusal(
        lambda: w.service.correlation_graph(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            anchor=w.ctrl04_correlation,
            depth=MAX_GRAPH_DEPTH + 1,
            now=w.tick(),
        )
    )
    person_keys = [k for n in graph["nodes"] for k in n if k in PERSON_IDENTIFIER_FIELDS]
    return (
        over_depth == OversightRefusal.GRAPH_LIMIT.value
        and graph["person_nodes"] == 0
        and not person_keys
        and len(graph["nodes"]) <= MAX_GRAPH_NODES
        and {e["relation"] for e in graph["edges"]} <= {"same-correlation", "chain-successor"}
    ), {
        "nodes": len(graph["nodes"]),
        "edges": sorted({e["relation"] for e in graph["edges"]}),
        "over_depth_refusal": over_depth,
        "person_keys": person_keys,
    }


def g30() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]
    from epd2_control_plane_service.oversight_sources import IntegrityState

    w = world()
    chain = w.service.action_chain(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        correlation_ref=w.ctrl04_correlation,
        now=w.tick(),
    )
    acts = [s["action_code"] for s in chain["steps"]]
    verified = all(s["integrity"]["state"] == IntegrityState.VERIFIED.value for s in chain["steps"])
    return (
        len(chain["steps"]) >= 4 and verified and chain["correlation_ref"] == w.ctrl04_correlation
    ), {"steps": len(chain["steps"]), "action_codes": acts, "all_verified": verified}


def g31() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_sources import (
        PERSON_IDENTIFIER_FIELDS,
        SourceUnavailable,
        VotingVerificationReference,
    )

    w = world()
    result = w.search(limit=200)
    leaked = [
        k
        for row in result["records"]
        for k in list(row) + list(row.get("attributes") or {})
        if k.lower() in PERSON_IDENTIFIER_FIELDS
    ]
    try:
        w.voting.register(
            VotingVerificationReference(
                interface_id="v-bad",
                published_digest="1" * 64,
                verification_status="member_id=42",
                published_at="2026-09-03T00:00:00+00:00",
            )
        )
        screened = False
    except SourceUnavailable:
        screened = True
    return not leaked and screened, {
        "leaked_fields": sorted(set(leaked)),
        "identity_reference_screened": screened,
        "person_identifier_field_count": len(PERSON_IDENTIFIER_FIELDS),
    }


def g32() -> tuple[bool, dict[str, Any]]:
    from _ctrl05_builders import OPS_UNIT  # type: ignore[import-not-found]

    w = world()
    status = w.service.voting_verification_status(
        actor_ref="auditor", session_id="sess-auditor", scope=OPS_UNIT, now=w.tick()
    )
    voting_records = [r for r in w.search(limit=200)["records"] if r["domain"] == "VOTING"]
    reach = [
        n
        for n in ("voting_ballots", "voting_members", "ballots", "members", "tally", "decrypt")
        if hasattr(w.service, n) or hasattr(w.voting, n)
    ]
    return (
        status["voting_internal_access"] == "NONE"
        and status["voting_control_path"] == "NONE"
        and status["member_identifiers_exposed"] == 0
        and not voting_records
        and not reach
    ), {
        "status": {k: v for k, v in status.items() if k != "interfaces"},
        "voting_domain_records_visible": len(voting_records),
        "reach_methods": reach,
    }


def g33() -> tuple[bool, dict[str, Any]]:
    """No structure in the runtime is a cross-domain person index.

    `global_person_key` and its siblings occur in the runtime only inside
    `PERSON_IDENTIFIER_FIELDS`, the screen that refuses them — so the check is
    that they are screened, and that no index-shaped structure exists.
    """
    from epd2_control_plane_service.oversight_sources import PERSON_IDENTIFIER_FIELDS

    src = source(RUNTIME_FILES[0], RUNTIME_FILES[1])
    banned = [
        token
        for token in (
            "person_index",
            "universal_subject_index",
            "cross_domain_identity",
            "identity_graph",
            "subject_directory",
        )
        if token in src
    ]
    screened = {
        name: name in PERSON_IDENTIFIER_FIELDS
        for name in ("global_person_key", "universal_subject_id", "person_id", "member_id")
    }
    w = world()
    graph = w.service.correlation_graph(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=__import__("_ctrl05_builders", fromlist=["OPS_UNIT"]).OPS_UNIT,
        anchor=w.ctrl04_correlation,
        depth=1,
        now=w.tick(),
    ).as_dict()
    node_kinds = sorted({n.get("kind", "evidence") for n in graph["nodes"]})
    return (
        not banned
        and all(screened.values())
        and graph["person_nodes"] == 0
        and "person" not in node_kinds
    ), {
        "index_structures": banned,
        "screened_identifiers": screened,
        "node_kinds": node_kinds,
    }


def _typed(*names: str) -> tuple[bool, dict[str, Any]]:
    import dataclasses

    from epd2_control_plane_service import oversight_console as oc
    from epd2_control_plane_service import oversight_sources as os_

    obs: dict[str, Any] = {}
    ok = True
    for name in names:
        cls = getattr(oc, name, None) or getattr(os_, name, None)
        if cls is None or not dataclasses.is_dataclass(cls):
            ok = False
            obs[name] = "absent or not a dataclass"
            continue
        params = dataclasses.fields(cls)
        frozen = cls.__dataclass_params__.frozen  # type: ignore[attr-defined]
        obs[name] = {
            "frozen": frozen,
            "fields": [f.name for f in params],
        }
        ok = ok and frozen and len(params) >= 3
    return ok, obs


def g34() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("OversightMandate", "OversightScope")
    from epd2_control_plane_service import oversight_console as oc

    fields = set(obs["OversightMandate"]["fields"])
    required = {
        "mandate_id",
        "subject_ref",
        "scope",
        "planes",
        "rights",
        "rule_version",
        "source_decision_ref",
        "authority_bindings",
        "valid_from",
        "valid_until",
    }
    return ok and required <= fields and timedelta(days=365) == oc.MAX_MANDATE_LIFETIME, obs


def g35() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("EvidenceReference", "EvidenceEnvelope", "IntegrityVerification")
    fields = set(obs["EvidenceEnvelope"]["fields"])
    return ok and {"reference", "domain", "scope_key", "integrity"} <= fields, obs


def g36() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("ReviewCase", "ReviewDisposition")
    fields = set(obs["ReviewDisposition"]["fields"])
    return ok and {"state", "rationale", "decided_by", "supersedes"} <= fields, obs


def g37() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("ReviewFinding")
    fields = set(obs["ReviewFinding"]["fields"])
    return ok and {"evidence_reference", "evidence_content_digest", "dispute_ref"} <= fields, obs


def g38() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("ReviewAttestation")
    fields = set(obs["ReviewAttestation"]["fields"])
    w = world()
    from epd2_control_plane_service.oversight_console import ReviewState

    case = w.open_case()
    w.dispose(case.case_id, ReviewState.NO_FINDING)
    version = w.service.case(case.case_id).version
    attestation = w.attest(case.case_id)
    obs["bound_case_version"] = [version, attestation.case_version]
    return (
        ok
        and {"case_version", "reauthorized_at", "mandate_ref", "authority_version"} <= fields
        and attestation.case_version == version
    ), obs


def g39() -> tuple[bool, dict[str, Any]]:
    ok, obs = _typed("EvidenceExportRequest", "RedactionDecision")
    fields = set(obs["RedactionDecision"]["fields"])
    return ok and {"purpose", "allowed_fields", "dropped_fields", "decided_by"} <= fields, obs


def g40() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import (
        FindingSeverity,
        FindingState,
        ReviewState,
    )

    w = world()
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2])
    w.dispose(case.case_id, ReviewState.FINDING_RAISED)
    finding = w.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    superseded, dispute = w.service.dispute_finding(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        finding_id=finding.finding_id,
        rationale="disputed",
        idempotency_key="g40",
        now=w.tick(),
    )
    view = w.service.case_view(case.case_id)
    ids = {f["finding_id"] for f in view["findings"]}
    removers = [
        n
        for n in ("delete_case", "remove_finding", "withdraw_disposition", "purge", "amend")
        if hasattr(w.service, n)
    ]
    return (
        {finding.finding_id, dispute.finding_id} <= ids
        and superseded.state is FindingState.DISPUTED
        and not removers
        and view["history_is_append_only"] is True
    ), {"finding_ids": sorted(ids), "removers": removers}


def g41() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import OversightRefusal, ReviewState

    w = world()
    case = w.open_case()
    ticket = w.prepare(
        case.case_id,
        "DISPOSE",
        __import__(
            "epd2_control_plane_service.oversight_console", fromlist=["AuditRight"]
        ).AuditRight.REVIEW,
    )
    w.dispose(case.case_id, ReviewState.NEEDS_CLARIFICATION)
    code = refusal(
        lambda: w.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="stale",
            idempotency_key="g41",
            now=w.tick(),
        )
    )
    w2 = world()
    case2 = w2.open_case()
    w2.dispose(case2.case_id, ReviewState.NO_FINDING)
    w2.attest(case2.case_id)
    close_stale = refusal(
        lambda: w2.service.close_case(
            actor_ref="attestor",
            session_id="sess-attestor",
            csrf_token="csrf-attestor",
            case_id=case2.case_id,
            expected_version=1,
            idempotency_key="g41-close",
            now=w2.tick(),
        )
    )
    return (
        code == OversightRefusal.STALE_CASE_VERSION.value
        and close_stale == OversightRefusal.STALE_CASE_VERSION.value
    ), {"dispose_refusal": code, "close_refusal": close_stale}


def g42() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import OversightRefusal

    w = world()
    case = w.open_case()
    code = refusal(lambda: w.attest(case.case_id))
    return code == OversightRefusal.DISPOSITION_REQUIRED.value, {"refusal": code}


def g43() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import OversightRefusal, ReviewState

    w = world()
    case = w.open_case()
    w.dispose(case.case_id, ReviewState.NO_FINDING)
    code = refusal(
        lambda: w.service.close_case(
            actor_ref="attestor",
            session_id="sess-attestor",
            csrf_token="csrf-attestor",
            case_id=case.case_id,
            expected_version=w.service.case(case.case_id).version,
            idempotency_key="g43",
            now=w.tick(),
        )
    )
    return code == OversightRefusal.ATTESTATION_WITHOUT_AUTHORITY.value, {"refusal": code}


def g44() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import AuditRight, OversightRefusal

    w = world()
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2])
    ticket = w.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    captured = {
        "mandate_id": ticket["mandate_id"],
        "authority_grant_id": ticket["authority_grant_id"],
        "authority_version": ticket["authority_version"],
        "case_version": ticket["case_version"],
        "evidence_digests": len(ticket["evidence_digests"]),
        "expires_at": ticket["expires_at"],
    }
    # No ticket, no act.
    no_ticket = refusal(
        lambda: w.service.export(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id="TKT-000000",
            purpose="STATISTICAL",
            evidence_refs=refs[:1],
            idempotency_key="g44",
            now=w.tick(),
        )
    )
    src = source(RUNTIME_FILES[0])
    reauthorized = src.count("self._reauthorize(")
    return (
        all(captured.values())
        and no_ticket == OversightRefusal.NOT_FOUND.value
        and reauthorized >= 4
    ), {"ticket": captured, "no_ticket_refusal": no_ticket, "reauthorize_call_sites": reauthorized}


def g45() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import (
        AuditRight,
        OversightRefusal,
        ReviewState,
    )

    observed = {}
    for label, mutate in (
        ("grant_withdrawn", lambda w: w.authorities._grants.pop("ag-rev")),
        ("mandate_superseded", lambda w: w.service.supersede_mandate("MND-auditor", "MND-next")),
        ("session_revoked", lambda w: w.service.revoke_session("sess-auditor")),
    ):
        w = world()
        case = w.open_case()
        ticket = w.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
        mutate(w)
        observed[label] = refusal(
            lambda w=w, ticket=ticket: w.service.dispose(
                actor_ref="auditor",
                session_id="sess-auditor",
                csrf_token="csrf-auditor",
                ticket_id=ticket["ticket_id"],
                disposition=ReviewState.NO_FINDING,
                rationale="after the change",
                idempotency_key="g45",
                now=w.tick(),
            )
        )
    # An expired ticket is also refused.
    w = world()
    case = w.open_case()
    ticket = w.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    observed["ticket_expired"] = refusal(
        lambda: w.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="too late",
            idempotency_key="g45-late",
            now=w.now + timedelta(minutes=11),
        )
    )
    acceptable = {
        OversightRefusal.STALE_AUTHORITY.value,
        OversightRefusal.AUTHORITY_UNRESOLVABLE.value,
        OversightRefusal.MANDATE_SUPERSEDED.value,
        OversightRefusal.SESSION_REVOKED.value,
    }
    return all(v in acceptable for v in observed.values()), observed


def g46() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import (
        AuditRight,
        OversightRefusal,
        ReviewState,
    )

    w = world()
    refs = [r for r in w.references() if r.startswith("CTRL-02")]
    case = w.open_case(evidence_refs=refs[:1])
    ticket = w.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    _tamper_ctrl02(w, 0, reason="changed after the reviewer read it")
    code = refusal(
        lambda: w.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="on a stale reading",
            idempotency_key="g46",
            now=w.tick(),
        )
    )
    return code == OversightRefusal.EVIDENCE_DIVERGED.value, {"refusal": code}


def g47() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import (
        AuditRight,
        OversightRefusal,
        ReviewState,
    )

    w = world()
    case = w.open_case()
    ticket = w.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    w.service.dispose(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        ticket_id=ticket["ticket_id"],
        disposition=ReviewState.NO_FINDING,
        rationale="first",
        idempotency_key="g47-a",
        now=w.tick(),
    )
    replay = refusal(
        lambda: w.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.FINDING_RAISED,
            rationale="replay",
            idempotency_key="g47-b",
            now=w.tick(),
        )
    )
    other_actor = None
    w2 = world()
    case2 = w2.open_case()
    ticket2 = w2.prepare(case2.case_id, "DISPOSE", AuditRight.REVIEW)
    other_actor = refusal(
        lambda: w2.service.dispose(
            actor_ref="dual-hat-operator",
            session_id="sess-dual-hat-operator",
            csrf_token="csrf-dual-hat-operator",
            ticket_id=ticket2["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="not my ticket",
            idempotency_key="g47-c",
            now=w2.tick(),
        )
    )
    return (
        replay == OversightRefusal.REPLAYED_REQUEST.value
        and other_actor == OversightRefusal.PARAMETER_INVALID.value
    ), {"replay": replay, "other_actor": other_actor}


def g48() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import FindingSeverity, ReviewState

    w = world()
    refs = w.references()
    first = w.open_case(evidence_refs=refs[:2], idempotency_key="g48-open")
    second = w.open_case(evidence_refs=refs[:2], idempotency_key="g48-open")
    w.dispose(first.case_id, ReviewState.FINDING_RAISED, idempotency_key="g48-disp")
    f1 = w.raise_finding(first.case_id, FindingSeverity.HIGH, refs[0], idempotency_key="g48-find")
    f2 = w.raise_finding(first.case_id, FindingSeverity.LOW, refs[1], idempotency_key="g48-find")
    e1 = w.export(first.case_id, "STATISTICAL", refs[:1], idempotency_key="g48-exp")
    e2 = w.export(first.case_id, "STATISTICAL", refs[:1], idempotency_key="g48-exp")
    return (
        first.case_id == second.case_id
        and f1.finding_id == f2.finding_id
        and e1["export"]["export_id"] == e2["export_id"]
        and len(w.service.cases()) == 1
    ), {
        "cases": len(w.service.cases()),
        "case_ids_equal": first.case_id == second.case_id,
        "finding_ids_equal": f1.finding_id == f2.finding_id,
        "export_ids_equal": e1["export"]["export_id"] == e2["export_id"],
    }


def g49() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_console import EXPORT_PURPOSES, OversightRefusal

    w = world()
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2])
    per_purpose = {}
    for purpose, allowed in EXPORT_PURPOSES.items():
        result = w.export(case.case_id, purpose, refs[:2], idempotency_key=f"g49-{purpose}")
        rows = result["payload"]["records"]
        outside = [k for row in rows for k in row if k not in allowed]
        decision = w.service.redaction(result["export"]["redaction_decision_id"])
        per_purpose[purpose] = {
            "fields_outside_purpose": outside,
            "dropped": list(result["redaction_decision"]["dropped_fields"]),
            "decision_recorded": decision is not None,
            "payload_digest": result["export"]["payload_digest"][:16],
        }
    unknown = refusal(lambda: w.export(case.case_id, "ANYTHING", refs[:1]))
    out_of_case = refusal(lambda: w.export(case.case_id, "STATISTICAL", refs[:4]))
    ok = (
        all(
            not v["fields_outside_purpose"] and v["decision_recorded"] for v in per_purpose.values()
        )
        and unknown == OversightRefusal.EXPORT_PURPOSE_UNKNOWN.value
        and out_of_case == OversightRefusal.EXPORT_OUT_OF_PURPOSE.value
    )
    return ok, {
        "purposes": per_purpose,
        "unknown_purpose": unknown,
        "out_of_case": out_of_case,
    }


def g50() -> tuple[bool, dict[str, Any]]:
    """Every refusal appends its own journal record."""
    from epd2_control_plane_service.oversight_console import AuditRight

    w = world()
    observed = {}
    for label, act in (
        ("no_mandate_search", lambda: w.search(principal="unmandated")),
        ("universal_search", lambda: w.search(principal="super-admin")),
        ("review_without_right", lambda: w.open_case(principal="read-only-auditor")),
        (
            "attest_without_right",
            lambda: w.prepare(w.open_case().case_id, "ATTEST", AuditRight.ATTEST),
        ),
    ):
        before = len(w.service.journal)
        code = refusal(act)
        observed[label] = {"refusal": code, "journal_growth": len(w.service.journal) - before}
    refused_records = [r for r in w.service.journal.records() if r.result == "REFUSED"]
    return (
        all(v["refusal"] and v["journal_growth"] > 0 for v in observed.values())
        and len(refused_records) >= 4
    ), {"observed": observed, "refused_records": len(refused_records)}


def g51() -> tuple[bool, dict[str, Any]]:
    import tempfile

    from epd2_control_plane_service.operations_adapters import JsonFileStore
    from epd2_control_plane_service.operations_console import EvidenceSealer
    from epd2_control_plane_service.oversight_console import (
        FindingSeverity,
        OversightConsoleService,
        ReviewState,
    )
    from epd2_control_plane_service.oversight_sources import EvidencePlane

    key = b"ctrl05-gate-evidence-seal-key-0123456789"
    with tempfile.TemporaryDirectory(prefix="ctrl05-g51-") as td:
        path = Path(td) / "ctrl05.json"
        w = world(store=JsonFileStore(path), sealer=EvidenceSealer(key))
        refs = w.references()
        case = w.open_case(evidence_refs=refs[:2])
        w.dispose(case.case_id, ReviewState.FINDING_RAISED)
        w.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
        w.attest(case.case_id)
        w.export(case.case_id, "GOVERNANCE_REPORT", refs[:2])
        before = w.service.case_view(case.case_id)
        persisted = json.loads(path.read_text())
        restored = OversightConsoleService.from_checkpoint(
            persisted,
            authorities=w.authorities,
            sources={
                EvidencePlane.CTRL02.value: w.ctrl02_source,
                EvidencePlane.CTRL03.value: w.ctrl03_source,
                EvidencePlane.CTRL04.value: w.ctrl04_source,
            },
            voting_verification=w.voting,
            sealer=EvidenceSealer(key),
        )
        after = restored.case_view(case.case_id)
    return (
        before == after
        and restored.journal.head_hash() == w.service.journal.head_hash()
        and len(restored.journal) == len(w.service.journal)
    ), {
        "case_identical": before == after,
        "journal_head": restored.journal.head_hash(),
        "journal_records": len(restored.journal),
        "store_file_used": True,
    }


def g52() -> tuple[bool, dict[str, Any]]:
    from datetime import datetime as _dt

    from epd2_control_plane_service.audit import EvidenceJournal
    from epd2_control_plane_service.exceptions import AuthorizationRefused
    from epd2_control_plane_service.operations_console import EvidenceSealer
    from epd2_control_plane_service.oversight_console import (
        OversightConsoleService,
        ReviewState,
    )
    from epd2_control_plane_service.oversight_sources import EvidencePlane

    key = b"ctrl05-gate-evidence-seal-key-0123456789"
    w = world(sealer=EvidenceSealer(key))
    case = w.open_case()
    w.dispose(case.case_id, ReviewState.NO_FINDING)
    w.attest(case.case_id)

    def restore(payload: dict[str, Any], sealer_key: bytes = key) -> str | None:
        try:
            OversightConsoleService.from_checkpoint(
                payload,
                authorities=w.authorities,
                sources={
                    EvidencePlane.CTRL02.value: w.ctrl02_source,
                    EvidencePlane.CTRL03.value: w.ctrl03_source,
                    EvidencePlane.CTRL04.value: w.ctrl04_source,
                },
                voting_verification=w.voting,
                sealer=EvidenceSealer(sealer_key),
            )
        except (AuthorizationRefused, ValueError) as exc:
            return f"{type(exc).__name__}"
        return None

    observed: dict[str, Any] = {}
    # 1. A naive edit.
    payload = w.service.checkpoint()
    payload["journal"][0]["reason_code"] = "AUD_NOT_REALLY"
    observed["naive_edit"] = restore(payload)
    # 2. A fully re-chained and re-anchored rewrite: only the keyed seal catches it.
    payload = w.service.checkpoint()
    payload["journal"][0]["reason_code"] = "AUD_NOT_REALLY"
    journal = EvidenceJournal()
    rebuilt = []
    for record in payload["journal"]:
        event = journal.append(
            occurred_at=_dt.fromisoformat(record["occurred_at"]),
            actor_ref=record["actor_ref"],
            actor_class=record["actor_class"],
            authority_basis=record["authority_basis"],
            action_id=record["action_id"],
            scope_key=record["scope_key"],
            object_ref=record["object_ref"],
            result=record["result"],
            reason_code=record["reason_code"],
            approval_refs=tuple(record["approval_refs"]),
            correlation_ref=record["correlation_ref"],
            attributes=record["attributes"],
        )
        rebuilt.append(
            {
                **record,
                "sequence": event.sequence,
                "event_hash": event.event_hash,
                "previous_event_hash": event.previous_event_hash,
            }
        )
    payload["journal"] = rebuilt
    payload["journal_anchor"] = list(journal.anchor())
    observed["rechained"] = restore(payload)
    # 3. A forged case table with no journal trail behind it.
    payload = w.service.checkpoint()
    payload["cases"][case.case_id]["state"] = ReviewState.CLOSED.value
    observed["forged_case_table"] = restore(payload)
    # 4. A forged attestation actor.
    payload = w.service.checkpoint()
    next(iter(payload["attestations"].values()))["attested_by"] = "never-attested"
    observed["forged_attestation"] = restore(payload)
    # 5. A dropped record.
    payload = w.service.checkpoint()
    payload["journal"] = payload["journal"][:-1]
    observed["dropped_record"] = restore(payload)
    # 6. Another key.
    observed["other_key"] = restore(
        w.service.checkpoint(), b"a-completely-different-key-0123456789"
    )
    # 7. The untouched checkpoint still loads.
    observed["untouched_loads"] = restore(w.service.checkpoint()) is None
    forgeries = [k for k in observed if k != "untouched_loads"]
    return (
        all(observed[k] is not None for k in forgeries) and observed["untouched_loads"] is True
    ), observed


def g53() -> tuple[bool, dict[str, Any]]:
    from epd2_control_plane_service.oversight_api import (
        CONSOLE_HTML,
        FORBIDDEN_CLIENT_FIELDS,
        OversightApp,
    )
    from epd2_control_plane_service.oversight_console import (
        FRONTEND_MAY_ASSERT_AUTHORITY,
        FRONTEND_MAY_ASSERT_INTEGRITY,
        OversightRefusal,
    )

    w = world()
    app = OversightApp(w.service, clock=lambda: w.tick())
    refused = {}
    for field in sorted(FORBIDDEN_CLIENT_FIELDS):
        status, payload, _ = app.handle(
            "POST",
            "/audit/v1/evidence/search",
            {"X-EPD2-Session": "sess-auditor"},
            json.dumps(
                {
                    "region_id": "DE-BE",
                    "org_id": "org-berlin",
                    "unit_id": "unit-operations-audit",
                    field: "forged",
                }
            ).encode(),
        )
        refused[field] = [status, payload.get("error") if isinstance(payload, dict) else None]
    all_refused = all(
        v[0] == 400 and v[1] == OversightRefusal.BROWSER_STATE_REJECTED.value
        for v in refused.values()
    )
    # Behavioural, not textual: a script-shaped title travels through the API
    # verbatim (it is data) and every render path in the page consumes only the
    # escaped object, so the count of raw and escaped ingestions must match.
    hostile = "<img src=x onerror=alert(1)>"
    case = w.open_case(title=hostile)
    _s, served, _c = app.handle(
        "GET",
        f"/audit/v1/cases/{case.case_id}?region_id={case.scope.region_id}"
        f"&org_id={case.scope.org_id}&unit_id={case.scope.unit_id}",
        {"X-EPD2-Session": "sess-auditor"},
        b"",
    )
    served_verbatim = isinstance(served, dict) and served.get("title") == hostile
    raw_ingestions = CONSOLE_HTML.count("await r.json()")
    escaped_ingestions = CONSOLE_HTML.count("esc(await r.json())")
    escapes = (
        "const esc=" in CONSOLE_HTML and raw_ingestions > 0 and raw_ingestions == escaped_ingestions
    )
    ui_claims = [
        token
        for token in (
            "localStorage",
            "sessionStorage",
            "recomputed_hash=",
            "trustworthy=true",
            "grants.push",
            "csrf_token",
        )
        if token in CONSOLE_HTML
    ]
    return (
        all_refused
        and not ui_claims
        and escapes
        and served_verbatim
        and FRONTEND_MAY_ASSERT_INTEGRITY is False
        and FRONTEND_MAY_ASSERT_AUTHORITY is False
    ), {
        "forbidden_client_fields": len(refused),
        "all_refused": all_refused,
        "ui_claims": ui_claims,
        "hostile_title_served_as_data": served_verbatim,
        "json_ingestions": [raw_ingestions, escaped_ingestions],
        "all_ingestions_escaped": escapes,
    }


def g54() -> tuple[bool, dict[str, Any]]:
    digest = runtime_source_digest()
    files = {
        "mutation_result.json": load("mutation_result.json"),
        "e2e_journeys_result.json": load("e2e_journeys_result.json"),
        "browser_journeys_result.json": load("browser_journeys_result.json"),
    }
    obs: dict[str, Any] = {"runtime_source_digest": digest}
    ok = True
    for name, payload in files.items():
        recorded = payload.get("runtime_source_digest")
        obs[name] = {"present": bool(payload), "digest_matches": recorded == digest}
        if not payload or recorded != digest:
            ok = False
    return ok, obs


def g55() -> tuple[bool, dict[str, Any]]:
    payload = load("browser_journeys_result.json")
    shots = sorted(p.name for p in (VALIDATION / "browser").glob("*.png"))
    ok = (
        payload.get("status") == "PASS"
        and "chromium" in str(payload.get("browser", "")).lower()
        and payload.get("journeys_passed") == payload.get("journeys_total")
        and len(shots) >= payload.get("journeys_total", 0)
    )
    return bool(ok), {
        "status": payload.get("status"),
        "browser": payload.get("browser"),
        "journeys": [payload.get("journeys_passed"), payload.get("journeys_total")],
        "screenshots": shots,
    }


def g56(record_freeze: bool, runs: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Freeze, verify against the freeze, and record review readiness."""
    freeze_path = VALIDATION / "source_freeze.json"
    governed = sorted(
        {
            *(ROOT / f for f in RUNTIME_FILES),
            *(SERVICE / "tests").glob("*ctrl05*.py"),
            *(ROOT / "scripts").glob("*ctrl05*.py"),
            *(ROOT / "docs/ctrl/CTRL-05").glob("*"),
            *(ROOT / "contracts/control").glob("ctrl05*.json"),
        }
    )
    current = {p.relative_to(ROOT).as_posix(): sha256(p) for p in governed if p.is_file()}
    if record_freeze or not freeze_path.is_file():
        write(
            "source_freeze.json",
            {
                "schema": "epd2.ctrl05.source-freeze/1",
                "files": current,
                "runtime_source_digest": runtime_source_digest(),
            },
        )
    frozen = load("source_freeze.json")
    drift = sorted(
        k
        for k in set(current) | set(frozen.get("files", {}))
        if current.get(k) != frozen["files"].get(k)
    )
    checks = {
        "tests": runs["tests"]["ok"],
        "ruff": runs["ruff"]["ok"],
        "ruff_format": runs["ruff_format"]["ok"],
        "mypy": runs["mypy"]["ok"],
        "freeze_stable": not drift,
    }
    return all(checks.values()), {
        "files_frozen": len(current),
        "drift": drift,
        "checks": checks,
        "tests_summary": runs["tests"]["summary"],
    }


def run(command: list[str], env: dict[str, str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return {
        "command": " ".join(Path(c).name if c.startswith("/") else c for c in command),
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "summary": tail[-1] if tail else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-freeze", action="store_true")
    args = parser.parse_args()

    python = str(ROOT / ".venv/bin/python")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(SERVICE / "src"), env.get("PYTHONPATH", "")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    targets = [
        *RUNTIME_FILES[:3],
        *[str(p.relative_to(ROOT)) for p in sorted((SERVICE / "tests").glob("*ctrl05*.py"))],
        *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "scripts").glob("*ctrl05*.py"))],
    ]
    runs = {
        "tests": run(
            [
                python,
                "-m",
                "pytest",
                "services/control-plane-service/tests",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            env,
        ),
        "ruff": run([str(ROOT / ".venv/bin/ruff"), "check", *targets], env),
        "ruff_format": run([str(ROOT / ".venv/bin/ruff"), "format", "--check", *targets], env),
        "mypy": run([str(ROOT / ".venv/bin/mypy"), *RUNTIME_FILES[:3]], env),
    }
    forbidden = (
        "-----BEGIN " + "PRIVATE KEY-----",
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "AKIA" + "IOSFODNN7EXAMPLE",
    )
    governed_sources = [
        *(ROOT / f for f in RUNTIME_FILES),
        *(SERVICE / "tests").glob("*ctrl05*.py"),
        *(ROOT / "scripts").glob("*ctrl05*.py"),
    ]
    secret_hits = [
        p.relative_to(ROOT).as_posix()
        for p in governed_sources
        if p.is_file() and any(m in p.read_text(errors="ignore") for m in forbidden)
    ]
    write(
        "test_result.json",
        {"schema": "epd2.ctrl05.test-result/1", "runs": runs, "secret_scan_hits": secret_hits},
    )

    probes: list[Probe] = [globals()[f"g{i:02d}"] for i in range(1, 56)]
    results: list[dict[str, Any]] = []
    for index, probe in enumerate(probes, 1):
        gate_id = f"G{index:02d}"
        try:
            passed, obs = probe()
        except Exception as exc:  # a gate that explodes has not passed
            passed, obs = False, {"exception": f"{type(exc).__name__}: {exc}"}
        results.append(
            {
                "id": gate_id,
                "name": GATE_NAMES[index - 1],
                "status": "PASS" if passed else "FAIL",
                "executed": True,
                "observations": obs,
            }
        )
        print(f"{gate_id} {'PASS' if passed else 'FAIL'} {GATE_NAMES[index - 1]}", flush=True)

    try:
        passed56, obs56 = g56(args.record_freeze, runs)
    except Exception as exc:
        passed56, obs56 = False, {"exception": f"{type(exc).__name__}: {exc}"}
    if secret_hits:
        passed56 = False
        obs56["secret_scan_hits"] = secret_hits
    results.append(
        {
            "id": "G56",
            "name": GATE_NAMES[55],
            "status": "PASS" if passed56 else "FAIL",
            "executed": True,
            "observations": obs56,
        }
    )
    print(f"G56 {'PASS' if passed56 else 'FAIL'} {GATE_NAMES[55]}", flush=True)

    write("gate_results.json", {"schema": "epd2.ctrl05.gate-results/1", "gates": results})
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    failed = [r["id"] for r in results if r["status"] != "PASS"]
    mutation = load("mutation_result.json")
    result = {
        "schema": "epd2.ctrl05.preseal-result/1",
        "stage": "CTRL-05",
        "mode": MODE,
        "overall": "PASS" if not failed else "FAIL",
        "gates_total": 56,
        "gates_passed": passed_count,
        "gates_failed": failed,
        "gates_blocked_for_final_seal": [],
        "mutation_result": f"{mutation.get('detected', 0)}/52 DETECTED",
        "e2e_result": f"{load('e2e_journeys_result.json').get('journeys_passed', 0)}/22 PASS",
        "browser_result": load("browser_journeys_result.json").get("status"),
        "tests": runs["tests"]["summary"],
        "runtime_source_digest": runtime_source_digest(),
        "self_state": SELF_STATE,
        "self_acceptance": False,
        "certification_claim": "NONE",
        "non_claim": (
            "no CTRL-05 acceptance, no CTRL layer closure, no production readiness, "
            "no legal activation, no final security acceptance, no BSI or Common "
            "Criteria certification"
        ),
    }
    write("preseal_result.json", result)
    print(
        f"CTRL05_RESULT:{'PASS' if not failed else 'FAIL'}:{passed_count}/56_PASS",
        flush=True,
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    _ = (inspect, re)  # kept for gate extension
    sys.exit(main())

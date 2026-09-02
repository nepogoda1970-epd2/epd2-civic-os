#!/usr/bin/env python3
"""Run forty-four isolated CTRL-03 source mutants against its executable tests."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "services/control-plane-service/src/epd2_control_plane_service/credential_lifecycle.py"
)
TESTS = ROOT / "services/control-plane-service/tests"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    name: str
    old: str
    new: str


MUTATIONS = (
    Mutation(
        "M01",
        "pq_track_activated",
        "PQ_TRACK_ACTIVE: Final = False",
        "PQ_TRACK_ACTIVE: Final = True",
    ),
    Mutation(
        "M02",
        "rotation_overlap_extended",
        "MAX_ROTATION_OVERLAP: Final = timedelta(hours=24)",
        "MAX_ROTATION_OVERLAP: Final = timedelta(days=365)",
    ),
    Mutation(
        "M03",
        "secret_jit_extended",
        "MAX_SECRET_JIT: Final = timedelta(minutes=15)",
        "MAX_SECRET_JIT: Final = timedelta(days=1)",
    ),
    Mutation(
        "M04",
        "universal_admin",
        "UNIVERSAL_ADMIN_EXISTS: Final = False",
        "UNIVERSAL_ADMIN_EXISTS: Final = True",
    ),
    Mutation(
        "M05",
        "universal_secret_reader",
        "UNIVERSAL_SECRET_READER_EXISTS: Final = False",
        "UNIVERSAL_SECRET_READER_EXISTS: Final = True",
    ),
    Mutation(
        "M06",
        "direct_db_lifecycle",
        "DIRECT_DB_COUNTS_AS_LIFECYCLE: Final = False",
        "DIRECT_DB_COUNTS_AS_LIFECYCLE: Final = True",
    ),
    Mutation(
        "M07",
        "self_accepted",
        'SELF_STATE: Final = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"',
        'SELF_STATE: Final = "ACCEPTED"',
    ),
    Mutation(
        "M08",
        "fixture_reduction",
        "MUTATION_FIXTURES_REQUIRED: Final = 44",
        "MUTATION_FIXTURES_REQUIRED: Final = 43",
    ),
    Mutation(
        "M09",
        "post_validation_change_allowed",
        "FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = True",
        "FREEZE_REJECTS_POST_VALIDATION_CHANGE: Final = False",
    ),
    Mutation(
        "M10",
        "ctrl01_identity_drift",
        "07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5",
        "17134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5",
    ),
    Mutation(
        "M11",
        "ctrl02_identity_drift",
        "f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e",
        "0addb4dfaeb3097e22d15e3448b5d927d7c3b1d7d4dd3332230d23ccd999df1d",
    ),
    Mutation(
        "M12",
        "voting_custody_allowed",
        "if item.credential_class is CredentialClass.VOTING_KEY_REFERENCE and (",
        "if False and (",
    ),
    Mutation(
        "M13",
        "cryptoperiod_disabled",
        "item.valid_until - item.valid_from > rule.maximum_lifetime",
        "False",
    ),
    Mutation("M14", "cross_region_issuance", "if item.scope != issuer_scope:", "if False:"),
    Mutation("M15", "root_hot_path", "if root_hot_path:", "if False:"),
    Mutation(
        "M16",
        "issuer_purpose_escape",
        "if item.credential_class not in {",
        "if False and item.credential_class not in {",
    ),
    Mutation(
        "M17",
        "profile_class_escape",
        "if item.credential_class not in rule.allowed_classes:",
        "if False:",
    ),
    Mutation(
        "M18",
        "algorithm_none",
        'if item.algorithm in {None, "none", "NONE"} or item.algorithm != rule.algorithm:',
        "if False:",
    ),
    Mutation("M19", "curve_mismatch", "if item.curve_or_mode != rule.curve_or_mode:", "if False:"),
    Mutation(
        "M20",
        "operation_boundary",
        "return operation in by_class[item.credential_class]",
        "return True",
    ),
    Mutation(
        "M21",
        "high_impact_quorum",
        "return 2, frozenset({ApproverClass.SECURITY, ApproverClass.TRUST_CUSTODIAN})",
        "return 1, frozenset({ApproverClass.SECURITY})",
    ),
    Mutation("M22", "idempotency_conflict", "if previous[0] != digest:", "if False:"),
    Mutation(
        "M23",
        "missing_request_evidence",
        "if not reason.strip() or not tuple(evidence_refs):",
        "if False:",
    ),
    Mutation(
        "M24", "unbounded_rotation", "or overlap_until - moment > MAX_ROTATION_OVERLAP", "or False"
    ),
    Mutation(
        "M25",
        "self_approval",
        "if approver_id == request.requester_id or approver_id in {",
        "if False or approver_id in {",
    ),
    Mutation(
        "M26",
        "duplicate_approval",
        "or approver_id in {\n"
        "                approval.actor_id for approval in request.approvals\n"
        "            }",
        "or False",
    ),
    Mutation(
        "M27", "target_drift", "if item.version != request.expected_target_version:", "if False:"
    ),
    Mutation(
        "M28",
        "provider_drift",
        "if self.provider.version(item.object_id) != request.expected_provider_version:",
        "if False:",
    ),
    Mutation(
        "M29",
        "trust_drift",
        "if item.trust_version != request.expected_trust_version:",
        "if False:",
    ),
    Mutation(
        "M30",
        "approver_reauth",
        "for approval in request.approvals:\n            self.authorities.require(",
        "for approval in ():\n            self.authorities.require(",
    ),
    Mutation(
        "M31",
        "approval_is_execution",
        "if request.state is not LifecycleState.APPROVED:",
        "if request.state not in {LifecycleState.APPROVED, LifecycleState.PENDING_ACTIVATION}:",
    ),
    Mutation(
        "M32",
        "custodian_separation",
        "if custodian_id in {request.requester_id, *(a.actor_id for a in request.approvals)}:",
        "if False:",
    ),
    Mutation("M33", "cross_region_rotation", "or replacement.scope != item.scope", "or False"),
    Mutation("M34", "rotation_linkage", "if replacement.parent_id != item.object_id:", "if False:"),
    Mutation("M35", "session_invalidation", "and value.subject_ref == subject_ref", "and False"),
    Mutation("M36", "trust_in_place", "if previous_version != actual_previous:", "if False:"),
    Mutation("M37", "cross_purpose_assertion", "if item.purpose != expected_purpose:", "if False:"),
    Mutation("M38", "cross_region_assertion", "if item.scope != expected_scope:", "if False:"),
    Mutation(
        "M39",
        "revoked_assertion",
        "if item.state is not LifecycleState.ACTIVE or item.compromised:",
        "if False:",
    ),
    Mutation(
        "M40", "trust_location", "if item.trust_location not in trusted_locations:", "if False:"
    ),
    Mutation("M41", "secret_quorum", "or len(approvals) < 2", "or False"),
    Mutation("M42", "secret_expiry", "or moment >= grant.expires_at", "or False"),
    Mutation("M43", "recovery_threshold", "or threshold < previous_threshold", "or False"),
    Mutation(
        "M44", "audit_history_overwrite", "self._events.append(event)", "self._events[:] = [event]"
    ),
)


def main() -> int:
    if len(MUTATIONS) != 44 or len({item.mutation_id for item in MUTATIONS}) != 44:
        raise SystemExit("mutation inventory must contain exactly 44 unique fixtures")
    original = SOURCE.read_text()
    results: list[dict[str, object]] = []
    test_files = sorted(str(path) for path in TESTS.glob("test_ctrl03_*.py"))
    for mutation in MUTATIONS:
        if mutation.old not in original:
            results.append({**asdict(mutation), "detected": False, "reason": "anchor missing"})
            continue
        with tempfile.TemporaryDirectory(prefix=f"ctrl03-{mutation.mutation_id.lower()}-") as td:
            root = Path(td)
            package = root / "epd2_control_plane_service"
            shutil.copytree(SOURCE.parent, package)
            mutant = package / SOURCE.name
            mutant.write_text(original.replace(mutation.old, mutation.new, 1))
            try:
                py_compile.compile(str(mutant), doraise=True)
            except py_compile.PyCompileError as exc:
                results.append(
                    {**asdict(mutation), "detected": False, "reason": f"invalid mutant: {exc}"}
                )
                continue
            env = dict(os.environ)
            env["PYTHONPATH"] = os.pathsep.join([str(root), str(TESTS), env.get("PYTHONPATH", "")])
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", *test_files, "-q"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            results.append(
                {
                    **asdict(mutation),
                    "detected": completed.returncode == 1,
                    "pytest_returncode": completed.returncode,
                    "output_tail": completed.stdout[-1200:],
                }
            )
    detected = sum(bool(item["detected"]) for item in results)
    output = ROOT / "validation/ctrl03/mutation_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schema": "epd2.ctrl03.mutation-result/1",
                "mutations_total": len(results),
                "detected": detected,
                "undetected": [item["mutation_id"] for item in results if not item["detected"]],
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"CTRL03_MUTATIONS:{'PASS' if detected == 44 else 'FAIL'}:{detected}/44")
    return 0 if detected == 44 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""INFRA-04 targeted unit tests.

These cover the behaviour the gates depend on, and — just as importantly —
the *absence* of false positives: a fail-closed evaluator that fires on
honest input is as broken as one that stays silent on a defect, because it
would push the run into a FAIL it cannot explain.

Fixtures are intentionally duplicated between this module and
``test_infra04_mutation_suite.py``: the repository's type-checking
configuration maps test files as top-level modules, so importing one test
module from another would make the same file visible under two module names.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import multiprocessing
from pathlib import Path
from typing import Any

import pytest
from scripts.infra04 import API06, PREDECESSOR, codes, continuity, drift4, evaluators, governance
from scripts.infra04.config_ext import (
    SERVICE_CONFIG_CONTRACT,
    check_no_weakening,
    classify,
    validate_startup_config,
)
from scripts.infra04.drills import DRILLS
from scripts.infra04.gates import GATES, PACKAGE_PHASE_GATES, VERDICTS
from scripts.infra04.mutations import (
    MUTATION_INVARIANTS,
    MUTATION_TOTAL,
    coverage_document,
    detector_for,
    mutation_ids,
)
from scripts.infra04.readiness import (
    LEVEL_RANK,
    LEVELS,
    STATES,
    DependencyObservation,
    assess,
    check_degraded_explicit,
    check_level_claim,
    check_not_hardcoded,
    check_probe_backed,
)
from scripts.infra04.recovery import (
    POSTURE_CONTROLS,
    RECOVERY_PHASES,
    RecoveryEvidence,
    check_authority_singular,
    check_chain_complete,
    check_ledger_append_only,
    check_posture_preserved,
    check_within_target,
    security_posture,
)
from scripts.infra04.resilient_service import FENCE_NAMESPACE, LedgerChain, _fence_key
from scripts.infra04.trial_replay import (
    EXPECTED_INPUT_DIGESTS,
    INFRA_OBSERVABLE,
    NOT_INFRA_OBSERVABLE,
    load_inputs,
    replay,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _append_ledger_from_child(path: str, done: Any) -> None:
    LedgerChain(Path(path)).append("child-event", {"source": "child"})
    done.set()


# -- shared fixtures (duplicated on purpose, see the module docstring) -----


def dependency(
    name: str = "database",
    status: str = "ok",
    age: float | None = 0.0,
    bound: float = 15.0,
    consequential: bool = True,
) -> DependencyObservation:
    return DependencyObservation(
        name=name,
        status=status,
        age_seconds=age,
        freshness_bound_seconds=bound,
        consequential=consequential,
    )


def healthy_posture() -> dict[str, Any]:
    return {
        "mtls_required": "true",
        "session_revocation_enforced": "true",
        "csrf_enforced": "true",
        "commit_reauth_required": "true",
        "idempotency_enforced": "true",
        "allow_plaintext": "false",
    }


def minimal_config(**overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for item in SERVICE_CONFIG_CONTRACT:
        if not item.required:
            continue
        config[item.name] = {
            "listen_port": 8451,
            "mtls_required": "true",
        }.get(item.name, f"value-{item.name}")
    config.update(overrides)
    return config


def snapshot(ledger: LedgerChain) -> dict[str, Any]:
    lines = [line for line in ledger.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        "entry_count": len(lines),
        "line_digests": [hashlib.sha256(line.encode()).hexdigest() for line in lines],
        "chain_findings": ledger.verify(),
    }


# -- readiness -------------------------------------------------------------


def test_five_levels_are_ranked_monotonically() -> None:
    assert LEVELS == (
        "PROCESS_ALIVE",
        "SERVICE_REACHABLE",
        "SERVICE_READY",
        "DEPENDENCY_READY",
        "AUTHORITATIVELY_READY",
    )
    assert [LEVEL_RANK[level] for level in LEVELS] == sorted(LEVEL_RANK[level] for level in LEVELS)
    assert "DEGRADED_READ_ONLY" in STATES and "EXPLICITLY_UNAVAILABLE" in STATES


def test_level_ladder_is_gated_step_by_step() -> None:
    assert (
        assess(
            process_alive=True,
            transport_ok=False,
            service_invariants_ok=True,
            dependencies=[dependency()],
        ).level
        == "PROCESS_ALIVE"
    )
    assert (
        assess(
            process_alive=True,
            transport_ok=True,
            service_invariants_ok=False,
            dependencies=[dependency()],
        ).level
        == "SERVICE_REACHABLE"
    )
    assert (
        assess(
            process_alive=True,
            transport_ok=True,
            service_invariants_ok=True,
            dependencies=[dependency(status="unavailable", age=None)],
        ).level
        == "SERVICE_READY"
    )
    assert (
        assess(
            process_alive=True,
            transport_ok=True,
            service_invariants_ok=True,
            dependencies=[
                dependency(),
                dependency(name="telemetry", status="unavailable", age=None, consequential=False),
            ],
        ).level
        == "DEPENDENCY_READY"
    )
    assert assess(
        process_alive=True,
        transport_ok=True,
        service_invariants_ok=True,
        dependencies=[dependency()],
    ).authoritative


def test_draining_is_never_ready() -> None:
    assessment = assess(
        process_alive=True,
        transport_ok=True,
        service_invariants_ok=True,
        dependencies=[dependency()],
        draining=True,
    )
    assert assessment.state == "NOT_READY"
    assert not assessment.authoritative
    assert assessment.reasons


def test_every_downgrade_carries_a_reason() -> None:
    for dependencies in (
        [dependency(status="unavailable", age=None)],
        [dependency(age=900.0)],
        [dependency(name="telemetry", status="unavailable", age=None, consequential=False)],
    ):
        assessment = assess(
            process_alive=True,
            transport_ok=True,
            service_invariants_ok=True,
            dependencies=dependencies,
        )
        assert assessment.reasons, f"no reason recorded for {dependencies}"


def test_healthy_readiness_produces_no_findings() -> None:
    assessment = assess(
        process_alive=True,
        transport_ok=True,
        service_invariants_ok=True,
        dependencies=[dependency()],
    )
    assert check_level_claim("AUTHORITATIVELY_READY", assessment, "shell") == []
    assert check_degraded_explicit("READY", assessment, "shell") == []
    assert check_probe_backed("PASS", backend_proof=True, subject="shell") == []
    assert check_not_hardcoded("level = assess(...).level\n", "shell") == []


def test_unknown_claimed_level_is_refused() -> None:
    assessment = assess(
        process_alive=True,
        transport_ok=True,
        service_invariants_ok=True,
        dependencies=[dependency()],
    )
    findings = check_level_claim("TOTALLY_READY", assessment, "shell")
    assert [finding.code for finding in findings] == [codes.READY_WHEN_ONLY_ALIVE]


# -- configuration ---------------------------------------------------------


def test_infra03_contract_is_extended_not_replaced() -> None:
    from scripts.infra03.config import SERVICE_CONFIG_CONTRACT as INHERITED

    names = {item.name for item in SERVICE_CONFIG_CONTRACT}
    assert {item.name for item in INHERITED} <= names
    assert "readiness_ledger" in names and "fencing_role" in names


def test_valid_config_starts_and_missing_required_item_refuses() -> None:
    assert validate_startup_config(minimal_config()) == []
    broken = minimal_config()
    required = next(item.name for item in SERVICE_CONFIG_CONTRACT if item.required)
    broken[required] = ""
    assert validate_startup_config(broken)


def test_unknown_critical_item_refuses_startup() -> None:
    findings = validate_startup_config({**minimal_config(), "db_shadow_dsn": "postgres://x"})
    assert findings


def test_no_weakening_is_clean_on_honest_config() -> None:
    assert check_no_weakening({**minimal_config(), **healthy_posture()}) == []


def test_every_weakening_value_is_refused() -> None:
    for key, value in (
        ("mtls_required", "false"),
        ("allow_plaintext", "true"),
        ("skip_session_revocation", "true"),
        ("disable_csrf", "true"),
        ("skip_commit_reauth", "true"),
        ("disable_idempotency", "true"),
        ("auth_bypass", "true"),
    ):
        # The segment matters for mTLS: the public ingress terminates TLS,
        # not mTLS, so the refusal is asserted on an application service.
        config = {**minimal_config(), "network_segment": "application", key: value}
        findings = check_no_weakening(config)
        assert findings, f"{key}={value} was not refused"


def test_classification_covers_every_provided_item() -> None:
    classified = classify({**minimal_config(), **healthy_posture()})
    assert set(classified) >= set(minimal_config())
    assert all(classified.values())


# -- recovery evidence -----------------------------------------------------


def test_recovery_chain_requires_all_six_phases() -> None:
    chain = RecoveryEvidence(
        recovery_id="rc-test",
        failure_domain="service",
        environment="preview",
        instance_id="preview-1",
        target_seconds=45.0,
    )
    for name in RECOVERY_PHASES[:-1]:
        chain.phase(name, {"recorded": True})
    document = chain.as_document()
    assert document["complete"] is False
    assert [finding.code for finding in check_chain_complete(document, "rc")] == [
        codes.RECOVERY_EVIDENCE_INCOMPLETE
    ]
    chain.phase("readiness", {"level": "AUTHORITATIVELY_READY"})
    complete = chain.as_document()
    assert complete["complete"] is True
    assert check_chain_complete(complete, "rc") == []


def test_unknown_phase_is_rejected() -> None:
    chain = RecoveryEvidence("rc", "service", "preview", "preview-1")
    with pytest.raises(ValueError):
        chain.phase("cleanup", {"x": 1})


def test_recovery_without_a_bound_is_refused() -> None:
    findings = check_within_target({"elapsed_seconds": 1.0}, "service")
    assert [finding.code for finding in findings] == [codes.RECOVERY_TARGET_EXCEEDED]


def test_unmeasured_recovery_is_refused() -> None:
    findings = check_within_target({"recovery_target_seconds": 45.0}, "service")
    assert [finding.code for finding in findings] == [codes.RECOVERY_TARGET_EXCEEDED]


def test_posture_unreadable_counts_as_not_engaged() -> None:
    before = security_posture(healthy_posture())
    findings = check_posture_preserved(before, {}, "shell")
    assert {finding.code for finding in findings} == set(POSTURE_CONTROLS.values()) | {
        codes.PLAINTEXT_SERVICE_FALLBACK
    }


def test_preserved_posture_is_clean() -> None:
    posture = security_posture(healthy_posture())
    assert check_posture_preserved(posture, posture, "shell") == []


def test_two_distinct_fences_are_not_a_split_brain() -> None:
    """Distinct durable-writer roles hold distinct fences.

    A check that fired here would fire on every healthy runtime, and a check
    that always fires proves nothing.
    """
    documents = {
        "identity-runtime-shell": {
            "granted": True,
            "fence_reason": "held",
            "fence_key": "preview:identity-runtime-shell",
        },
        "membership-runtime-shell": {
            "granted": True,
            "fence_reason": "held",
            "fence_key": "preview:membership-runtime-shell",
        },
    }
    assert continuity.check_no_split_brain(documents, "runtime") == []


def test_a_non_holder_without_a_reason_is_refused() -> None:
    documents = {
        "writer-a": {"granted": True, "fence_key": "preview:writer"},
        "writer-b": {"granted": False, "fence_reason": ""},
    }
    findings = continuity.check_no_split_brain(documents, "runtime")
    assert [finding.code for finding in findings] == [codes.DEGRADED_STATE_NOT_EXPLICIT]


def test_an_unobservable_fence_is_read_as_held() -> None:
    """The safe reading of "I cannot see the fence" is that someone holds it."""

    class Unreachable:
        def admin_sql(self, *args: object, **kwargs: object) -> str:
            raise RuntimeError("cluster unavailable")

    assert continuity.fence_is_held(Unreachable(), "epd2_identity", "preview:writer") is True  # type: ignore[arg-type]


def test_only_one_instance_may_be_authoritative() -> None:
    assert (
        check_authority_singular(
            {
                "a": {"level": "AUTHORITATIVELY_READY", "state": "READY"},
                "b": {"level": "SERVICE_READY", "state": "DEGRADED_READ_ONLY"},
            },
            "runtime",
        )
        == []
    )
    findings = check_authority_singular(
        {
            "a": {"level": "AUTHORITATIVELY_READY", "state": "READY"},
            "b": {"level": "AUTHORITATIVELY_READY", "state": "READY"},
        },
        "runtime",
    )
    assert [finding.code for finding in findings] == [codes.AMBIGUOUS_WRITER_ACCEPTED]


def test_non_authoritative_instance_must_be_explicit() -> None:
    findings = check_authority_singular(
        {
            "a": {"level": "AUTHORITATIVELY_READY", "state": "READY"},
            "b": {"level": "SERVICE_READY", "state": "READY"},
        },
        "runtime",
    )
    assert [finding.code for finding in findings] == [codes.DEGRADED_STATE_NOT_EXPLICIT]


# -- evidence ledger -------------------------------------------------------


def test_ledger_chain_is_append_only_and_verifiable(tmp_path: Path) -> None:
    ledger = LedgerChain(tmp_path / "ledger.jsonl")
    for index in range(5):
        ledger.append("event", {"index": index})
    assert ledger.verify() == []
    assert len(ledger.entries()) == 5
    before = snapshot(ledger)
    ledger.append("event", {"index": 5})
    assert check_ledger_append_only(before, snapshot(ledger), "ledger") == []

    # Several service processes share this file. The child must wait while an
    # external process-level lock is held; a threading.Lock alone cannot do so.
    context = multiprocessing.get_context("fork")
    done = context.Event()
    process = context.Process(target=_append_ledger_from_child, args=(str(ledger.path), done))
    with ledger.path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            process.start()
            assert not done.wait(timeout=0.5)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    assert done.wait(timeout=5.0)
    process.join(timeout=5.0)
    assert process.exitcode == 0
    assert ledger.verify() == []


def test_ledger_redacts_secret_shaped_values(tmp_path: Path) -> None:
    ledger = LedgerChain(tmp_path / "ledger.jsonl")
    ledger.append("db-connect", {"dsn": "postgresql://rt_identity:hunter2@localhost/db"})
    text = ledger.path.read_text(encoding="utf-8")
    assert "hunter2" not in text


def test_fence_key_is_stable_and_namespaced() -> None:
    assert _fence_key("preview:identity") == _fence_key("preview:identity")
    assert _fence_key("preview:identity") != _fence_key("preview:membership")
    assert 0 < _fence_key("preview:identity") < 0x8000_0000
    assert FENCE_NAMESPACE == 0x4550_4432


# -- continuity ------------------------------------------------------------


def test_restart_budget_closes_after_exhaustion() -> None:
    budget = continuity.RestartBudget(service="shell", max_restarts=3)
    assert [budget.record(f"crash {index}") for index in range(3)] == [True, True, True]
    assert budget.failed
    assert budget.record("crash 4") is False
    assert "budget exhausted" in budget.reasons[-1]
    assert "never reported healthy" in budget.as_document()["declaration"]


def test_budget_within_limit_is_clean() -> None:
    budget = continuity.RestartBudget(service="shell", max_restarts=3)
    budget.record("crash 1")
    assert continuity.check_restart_bounding(budget, reported_healthy=True) == []


def test_failed_budget_may_not_read_healthy() -> None:
    budget = continuity.RestartBudget(service="shell", max_restarts=1)
    budget.record("crash 1")
    findings = continuity.check_restart_bounding(budget, reported_healthy=True)
    assert [finding.code for finding in findings] == [codes.RESTART_LOOP_UNBOUNDED]


def test_measurement_within_bound_passes_and_over_bound_fails() -> None:
    good = continuity.Measurement("restart", 45.0, 4.2, True)
    assert good.within_target is True
    assert continuity.check_measurements([good]) == []
    slow = continuity.Measurement("restart", 45.0, 90.0, True)
    assert [finding.code for finding in continuity.check_measurements([slow])] == [
        codes.RECOVERY_TARGET_EXCEEDED
    ]


def test_no_measurement_is_refused() -> None:
    assert [finding.code for finding in continuity.check_measurements([])] == [
        codes.RECOVERY_TARGET_EXCEEDED
    ]


def test_measure_records_a_raised_action_as_failure() -> None:
    def boom() -> bool:
        raise RuntimeError("recovery failed")

    measurement = continuity.measure("restart", 45.0, boom)
    assert measurement.succeeded is False
    assert "RuntimeError" in measurement.detail
    assert [finding.code for finding in continuity.check_measurements([measurement])] == [
        codes.RECOVERY_EVIDENCE_INCOMPLETE
    ]


def test_budget_reads_the_governed_policy() -> None:
    policy = json.loads(
        (REPO_ROOT / "infra/runtime/resilience_policy.json").read_text(encoding="utf-8")
    )
    budget = continuity.budget_from_policy("shell", policy)
    assert budget.max_restarts == policy["continuity_limits"]["max_restarts_per_service"]


# -- drift -----------------------------------------------------------------


def test_identical_baselines_reconcile_clean() -> None:
    baseline = {
        "baseline_digest": "a" * 64,
        "runtime_bytes": {
            "release_digest": "r" * 64,
            "deploy_tree_digest": "d" * 64,
            "observed_per_service": {"shell": "r" * 64},
        },
        "configuration": {
            "per_service_digest": {"shell": "c" * 64},
            "config_tree_digest": "t" * 64,
        },
        "schema_migrations": {
            "databases": {
                "epd2_identity": {
                    "entry_count": 1,
                    "ledger_digest": "l" * 64,
                    "entries": ["001.sql:aa"],
                }
            }
        },
        "trust_material": {
            "trust_tree_digest": "u" * 64,
            "authority_digest": {"application-ca": "v" * 64},
            "layout_findings": [],
        },
    }
    evidence, findings = drift4.reconcile(baseline, baseline)
    assert findings == []
    assert evidence["reconciled"] is True
    assert evidence["drift_total"] == 0


def test_unobservable_plane_counts_as_drift() -> None:
    baseline = {
        "release_digest": "r" * 64,
        "deploy_tree_digest": "d" * 64,
        "observed_per_service": {"shell": "r" * 64},
    }
    observed = {
        "release_digest": "r" * 64,
        "deploy_tree_digest": "d" * 64,
        "observed_per_service": {"shell": "unobservable: connection refused"},
    }
    findings = drift4.compare_runtime(baseline, observed)
    assert [finding.code for finding in findings] == [codes.RUNTIME_BYTE_DRIFT_IGNORED]


def test_tree_digest_is_content_addressed(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.txt").write_text("one", encoding="utf-8")
    (tmp_path / "a" / "two.txt").write_text("two", encoding="utf-8")
    first, count = drift4._tree_digest(tmp_path)
    assert count == 2
    assert first == drift4._tree_digest(tmp_path)[0]
    (tmp_path / "a" / "two.txt").write_text("TWO", encoding="utf-8")
    assert drift4._tree_digest(tmp_path)[0] != first


def test_missing_authority_is_trust_drift() -> None:
    findings = drift4.compare_trust(
        {"trust_tree_digest": "a" * 64, "authority_digest": {"data-ca": "x" * 64}},
        {"trust_tree_digest": "a" * 64, "authority_digest": {}},
    )
    assert [finding.code for finding in findings] == [codes.TRUST_DRIFT_IGNORED]


# -- evaluators: no false positives on honest material --------------------


def test_claim_scanners_are_silent_on_our_own_honest_text() -> None:
    honest = (
        "This candidate is not accepted and does not accept itself.\n"
        "No BSI, Common Criteria or EAL4 certification is claimed.\n"
        "The runtime is never production-ready and the INFRA layer is not closed.\n"
        "self_acceptance is false; acceptance is external.\n"
    )
    for check in (
        evaluators.check_no_certification_claim,
        evaluators.check_no_production_claim,
        evaluators.check_no_closure_claim,
        evaluators.check_no_self_acceptance,
    ):
        assert check(honest, "doc") == [], check.__name__


def test_stage_modules_and_docs_assert_no_forbidden_claim() -> None:
    """The real candidate material must survive its own claim scanners."""
    for path in sorted((REPO_ROOT / "scripts/infra04").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for check in (
            evaluators.check_no_certification_claim,
            evaluators.check_no_production_claim,
            evaluators.check_no_closure_claim,
            evaluators.check_no_self_acceptance,
        ):
            assert check(text, path.name) == [], f"{path.name}: {check.__name__}"


def test_secret_reference_is_not_a_secret_value() -> None:
    text = json.dumps(
        {
            "db_password_file": "/run/secrets/db-password__rt_identity",
            "password": "file:/run/secrets/db-password__rt_identity",
            "token": "REDACTED",
        }
    )
    assert evaluators.check_no_secret_values(text, "config") == []


def test_dsn_with_password_is_a_credential_in_evidence() -> None:
    text = 'dsn = "postgresql://rt_identity:hunter2@localhost:8432/epd2_identity"'
    findings = evaluators.check_no_secret_values(text, "evidence")
    assert [finding.code for finding in findings] == [codes.CREDENTIAL_IN_EVIDENCE]


def test_voting_scan_is_silent_on_category_labels() -> None:
    text = json.dumps({"refused": True, "category": "identity-or-correlation-header", "count": 1})
    assert evaluators.check_voting_domain_clean(text, "voting") == []


def test_voting_route_from_inside_the_domain_is_allowed() -> None:
    routes = [{"from_segment": "voting", "to_segment": "voting"}]
    assert evaluators.check_no_voting_route(routes, "inventory") == []


def test_gate_accounting_accepts_a_complete_clean_report() -> None:
    gates = [
        {"id": f"G{index:02d}", "result": "PASS", "evidence": "e.json"} for index in range(1, 4)
    ]
    assert evaluators.check_gate_accounting(gates, 3, "report") == []
    assert (
        evaluators.check_summary_consistency(
            {"pass": 3, "fail": 0, "blocked": 0, "all_passed": True}, gates, "report"
        )
        == []
    )


def test_blocked_gate_blocks_the_seal() -> None:
    gates = [
        {"id": "G01", "result": "PASS", "evidence": "e.json"},
        {"id": "G02", "result": "BLOCKED", "evidence": "e.json"},
    ]
    findings = evaluators.check_gate_accounting(gates, 2, "report")
    assert codes.FAILED_GATE_ACCEPTED in {finding.code for finding in findings}


def test_unevidenced_gate_did_not_execute() -> None:
    gates = [{"id": "G01", "result": "PASS", "evidence": ""}]
    findings = evaluators.check_gate_accounting(gates, 1, "report")
    assert codes.GATE_NOT_EXECUTED in {finding.code for finding in findings}


def test_summary_may_not_disagree_with_the_records() -> None:
    gates = [
        {"id": "G01", "result": "PASS", "evidence": "e.json"},
        {"id": "G02", "result": "FAIL", "evidence": "e.json"},
    ]
    findings = evaluators.check_summary_consistency({"pass": 2, "fail": 0}, gates, "report")
    # Both declared counts disagree with the records, so both are reported.
    assert {finding.code for finding in findings} == {codes.FAILED_GATE_ACCEPTED}
    assert len(findings) == 2


def test_honest_self_state_is_accepted() -> None:
    assert (
        evaluators.check_self_state(
            {
                "self_acceptance": False,
                "self_state": "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED",
                "authority": "external",
            },
            "record",
        )
        == []
    )


def test_predecessor_binding_accepts_exact_digests() -> None:
    assert (
        evaluators.check_predecessor_binding(
            {
                "predecessors": {
                    "INFRA-03": {"zip_sha256": PREDECESSOR["zip_sha256"]},
                    "API-06": {"zip_sha256": API06["zip_sha256"]},
                }
            },
            {
                "INFRA-03": str(PREDECESSOR["zip_sha256"]),
                "API-06": str(API06["zip_sha256"]),
            },
            "record",
        )
        == []
    )


def test_replay_that_executed_exactly_once_is_clean() -> None:
    assert (
        evaluators.check_replay_idempotent(
            {"idempotency_key": "op-1"},
            {"idempotency_key": "op-1", "replayed": True},
            1,
            "shell",
        )
        == []
    )


# -- predecessor identities ------------------------------------------------


def test_predecessor_identities_are_the_accepted_ones() -> None:
    assert PREDECESSOR["stage"] == "INFRA-03"
    assert (
        PREDECESSOR["zip_sha256"]
        == "6b49e02dbf38f9672c02c2540af051e3684cb4278b4330e91909e454f379d3c1"
    )
    assert PREDECESSOR["size_bytes"] == 16179206
    assert API06["zip_sha256"] == "3432b6615aa83c6f2860c015b7cafc2a18362aa371901616951a1bd5d263933c"
    assert len(str(PREDECESSOR["source_preseal_sha256"])) == 64


# -- catalog, gates and drills --------------------------------------------


def test_mutation_catalog_is_complete_distinct_and_mapped() -> None:
    assert len(mutation_ids()) == MUTATION_TOTAL == 48
    coverage = coverage_document()
    assert coverage["distinct_detector_total"] == 48
    assert coverage["distinctness_findings"] == []
    assert set(MUTATION_INVARIANTS) == {mutation.split("-", 1)[0] for mutation in mutation_ids()}
    assert detector_for("M01") == codes.READY_WHEN_ONLY_ALIVE
    with pytest.raises(KeyError):
        detector_for("M99")


def test_gate_catalog_matches_the_governed_target() -> None:
    assert len(GATES) == 54
    assert sorted(GATES) == [f"G{index:02d}" for index in range(1, 55)]
    assert PACKAGE_PHASE_GATES == ("G53",)
    assert VERDICTS == ("PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE_GOVERNED")
    assert "PASS_WITH_ENVIRONMENT_LIMITATION" not in VERDICTS


def test_drill_catalog_matches_the_governed_target() -> None:
    assert len(DRILLS) == 18
    assert sorted(DRILLS) == [f"J{index:02d}" for index in range(1, 19)]


def test_every_detector_code_is_distinct_and_namespaced() -> None:
    values = [
        value for name, value in vars(codes).items() if name.isupper() and isinstance(value, str)
    ]
    assert all(value.startswith("I04_") for value in values)
    assert len(values) == len(set(values))


# -- resilience policy -----------------------------------------------------


def test_policy_declares_every_failure_domain_and_bound() -> None:
    policy = json.loads(
        (REPO_ROOT / "infra/runtime/resilience_policy.json").read_text(encoding="utf-8")
    )
    assert policy["schema"] == "epd2.infra04.resilience-policy/1"
    assert len(policy["failure_domains"]) >= 8
    targets = policy["recovery_targets_seconds"]
    for name in (
        "service_restart_to_ready",
        "database_restart_to_ready",
        "dependency_recovery_to_authoritative",
        "restore_to_ready",
        "rollback_to_verified",
    ):
        assert isinstance(targets[name], int | float)
    assert "epd2_voting" not in json.dumps(policy["backup_policy"])
    assert policy["voting_domain"]["rule"]


def test_backup_allowlist_excludes_the_voting_domain() -> None:
    from scripts.infra04.backup import BACKUP_ALLOWLIST, VOTING_DATABASES

    assert "epd2_voting" not in BACKUP_ALLOWLIST
    assert VOTING_DATABASES == ("epd2_voting",)


# -- System Trial replay ---------------------------------------------------


def test_trial_inputs_are_byte_identical_to_the_bound_digests() -> None:
    _, digests = load_inputs(REPO_ROOT)
    assert digests == EXPECTED_INPUT_DIGESTS


def test_replay_reports_ownership_for_every_scenario() -> None:
    verdicts = {f"J{index:02d}": "PASS" for index in range(1, 19)}
    document = replay(REPO_ROOT, verdicts, {"stage": "INFRA-04"})
    assert document["executed"] is True
    assert document["harness_unmodified"] is True
    assert document["harness_findings"] == []
    assert document["trial_go_no_go"] == "NOT_DECIDED_BY_INFRA04"
    assert len(document["scenarios"]) == 12
    for scenario in document["scenarios"]:
        assert scenario["ownership"]
        assert scenario["result"] in {"PASS", "FAIL", "ENVIRONMENT_BLOCKED"}
    assert set(INFRA_OBSERVABLE) & set(NOT_INFRA_OBSERVABLE) == set()
    assert len(INFRA_OBSERVABLE) + len(NOT_INFRA_OBSERVABLE) == 12


def test_replay_never_converts_a_failed_drill_into_a_pass() -> None:
    verdicts = {f"J{index:02d}": "PASS" for index in range(1, 19)}
    verdicts["J05"] = "FAIL"
    document = replay(REPO_ROOT, verdicts, {"stage": "INFRA-04"})
    failed = [item for item in document["scenarios"] if item["result"] == "FAIL"]
    assert [item["scenario_id"] for item in failed] == ["F-02"]
    assert document["overall"] == "INFRA_OWNED_FAILURE_PRESENT"


def test_replay_reports_a_blocked_drill_as_environment_blocked() -> None:
    verdicts = {f"J{index:02d}": "PASS" for index in range(1, 19)}
    verdicts["J12"] = "BLOCKED"
    document = replay(REPO_ROOT, verdicts, {"stage": "INFRA-04"})
    blocked = {
        item["scenario_id"]
        for item in document["scenarios"]
        if item["result"] == "ENVIRONMENT_BLOCKED"
    }
    assert "F-08" in blocked
    assert document["infra_owned_failures"] == []


# -- governance ------------------------------------------------------------


def test_stage_state_reader_ignores_indirect_mentions() -> None:
    text = "OPS-03 qualification must independently bind the exact accepted API-06 identity."
    assert governance._stage_state(text, "OPS-03") == "UNKNOWN"


def test_stage_state_reader_reads_a_direct_statement() -> None:
    text = "bounded `INFRA-02 — CI/CD & Supply Chain` is `ACCEPTED / CLOSED` at exact SHA."
    assert governance._stage_state(text, "INFRA-02") == "ACCEPTED_CLOSED"


def test_stage_state_stops_at_the_next_stage_token() -> None:
    text = "INFRA-03…INFRA-07 remain governed separately; INFRA-02 is `ACCEPTED / CLOSED`."
    assert governance._stage_state(text, "INFRA-03") == "UNKNOWN"


def test_acceptance_family_collapses_wording_variance() -> None:
    assert governance._family("ACCEPTED") == governance._family("ACCEPTED_CLOSED")
    assert governance._family("QUALIFICATION_ELIGIBLE") != governance._family("ACCEPTED")


def test_unaccepted_stages_are_declared() -> None:
    assert "OPS-03" not in governance.UNACCEPTED_STAGES
    assert governance.DEPENDENCY_RECORDS["OPS-03"] == (
        "docs/ops/OPS-03/OPS03_C3_ACCEPTANCE_RECORD.json"
    )
    assert "INFRA-04" in governance.UNACCEPTED_STAGES
    assert "INFRA-03" not in governance.UNACCEPTED_STAGES

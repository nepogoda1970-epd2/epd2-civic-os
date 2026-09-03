"""CTRL-04 evidence schema, immutability and restart survival."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _ctrl04_builders import World
from epd2_control_plane_service.exceptions import AuthorizationRefused, EvidenceIntegrityError
from epd2_control_plane_service.operations_adapters import BackendState, JsonFileStore
from epd2_control_plane_service.operations_console import (
    ActionState,
    ActionType,
    OperationsConsoleService,
    OperationsPolicy,
    OpsRefusal,
)

REQUIRED = [
    "action_id",
    "request_id",
    "action_type",
    "actor_ref",
    "authority_ref",
    "target_ref",
    "environment",
    "parameters_digest",
    "requested_at",
    "authorization_decision",
    "execution_state",
    "result_state",
    "deployment_identity_ref",
    "evidence_digest",
]
FORBIDDEN = [
    "password",
    "private_key",
    "secret_value",
    "access_token",
    "refresh_token",
    "recovery_secret",
    "seed_phrase",
    "raw_hsm_material",
]


def test_evidence_record_satisfies_schema_and_provenance() -> None:
    w = World()
    done = w.full_restart()
    w.review(done.action_id)
    record = w.service.evidence_record(done.action_id)
    assert record["schema"] == "epd2.ctrl04.evidence.v1"
    for key in REQUIRED:
        assert key in record and record[key] not in ("", None, []), key
    assert record["actor_ref"] == "requester"
    assert record["authority_ref"] == "g-req-r@v1"
    assert record["target_ref"] == "svc-web@v1"
    assert record["deployment_identity_ref"] == "dep-web-1"
    assert record["environment"] == "PRODUCTION_LIKE"
    assert record["region_scope"] == "DE-BE:org-berlin"
    assert record["execution_state"] == "COMPLETED" and record["result_state"] == "SUCCEEDED"
    assert record["review_state"] == "REVIEWED"
    assert (
        record["approval_ref"] and record["approval_ref"][0]["approver_ref"] == "incident-commander"
    )
    assert record["approval_ref"][0]["authority_ref"] == "g-ic@v1"
    stages = [d["stage"] for d in record["authorization_decision"]]
    assert stages == ["REQUEST", "APPROVE", "COMMIT", "REVIEW"]
    assert all(d["allowed"] for d in record["authorization_decision"])
    assert record["authorization_decision"][-2]["authority_ref"] == "g-exec"
    assert record["authorization_decision"][-1]["authority_ref"] == "g-rev"
    text = json.dumps(record)
    for key in FORBIDDEN:
        assert f'"{key}"' not in text
    refs = record["evidence_refs"]
    assert len(refs) >= 4 and [r["evidence_id"] for r in refs] == sorted(
        r["evidence_id"] for r in refs
    )
    assert all(len(r["event_hash"]) == 64 for r in refs)
    assert len(record["evidence_digest"]) == 64


def test_every_privileged_mutation_has_immutable_action_id_and_journal_trail() -> None:
    w = World()
    ids = [w.full_restart().action_id for _ in range(3)]
    assert len(set(ids)) == 3
    for action_id in ids:
        records = [r for r in w.service.journal.records() if r.correlation_ref == action_id]
        assert [r.result for r in records] == [
            "REQUESTED",
            "APPROVED",
            "COMMIT_REAUTHORIZED",
            "DISPATCHED",
            "SUCCEEDED",
        ]
        assert records[1].approval_refs, "approval provenance recorded"
        assert (
            records[0].attributes["parameters_digest"]
            == w.service.action(action_id).parameters_digest
        )
        assert records[0].attributes["deployment_identity_ref"] == "dep-web-1"
        assert records[0].actor_ref == "requester" and records[3].actor_ref == "executor"
    w.service.journal.verify()


def test_refusals_cancellations_and_failures_are_journaled() -> None:
    w = World()
    with pytest.raises(AuthorizationRefused):
        w.request(principal="bavaria-requester", scope=__import__("_ctrl04_builders").BAVARIA)
    assert w.service.journal.records()[-1].result == "REFUSED"
    assert w.service.journal.records()[-1].reason_code == OpsRefusal.WRONG_SCOPE.value
    action = w.request()
    w.tick()
    w.service.cancel(
        action_id=action.action_id, actor_ref="requester", session_id="sess-requester", now=w.now
    )
    assert w.service.journal.records()[-1].result == "CANCELLED"
    w.adapter.inject_outcome("svc-web", BackendState.FAILED)
    failed = w.full_restart()
    assert failed.state is ActionState.FAILED
    assert w.service.journal.records()[-1].result == "FAILED"
    assert w.service.journal.records()[-1].correlation_ref == failed.action_id


def test_evidence_journal_detects_rewrite() -> None:
    w = World()
    w.full_restart()
    records = w.service.journal._records
    tampered = records[1]
    from dataclasses import replace

    records[1] = replace(tampered, actor_ref="someone-else")
    with pytest.raises(EvidenceIntegrityError):
        w.service.journal.verify()


def test_checkpoint_restart_preserves_history_and_refuses_tampered_history(tmp_path: Path) -> None:
    store = JsonFileStore(tmp_path / "ctrl04.json")
    w = World(store=store)
    done = w.full_restart()
    backup = w.completed_backup()
    head = w.service.journal.head_hash()
    count = len(w.service.journal)
    # "Restart": a fresh process loads the file.
    loaded = store.load()
    assert loaded is not None
    revived = OperationsConsoleService.from_checkpoint(
        loaded,
        authorities=w.authorities,
        signer=w.signer,
        adapters={"reference-adapter": w.adapter},
        ctrl02=w.ctrl02,
        ctrl03=w.ctrl03,
        store=store,
    )
    assert revived.journal.head_hash() == head and len(revived.journal) == count
    assert revived.action(done.action_id).state is ActionState.SUCCEEDED
    assert revived.evidence_record(done.action_id) == w.service.evidence_record(done.action_id)
    assert [b.operation_id for b in revived.backup_operations()] == [backup.operation_id]
    revived.journal.verify()
    # History continues after restart and remains chained.
    w2 = World.__new__(World)
    w2.__dict__.update(w.__dict__)
    w2.service = revived
    again = w2.full_restart()
    assert again.action_id != done.action_id
    revived.journal.verify()
    assert len(revived.journal) > count
    # Tampering with the persisted file is detected on load.
    tampered = json.loads(store.path.read_text())
    tampered["journal"][0]["actor_ref"] = "ghost"
    with pytest.raises(AuthorizationRefused) as info:
        OperationsConsoleService.from_checkpoint(
            tampered,
            authorities=w.authorities,
            signer=w.signer,
            adapters={"reference-adapter": w.adapter},
        )
    assert info.value.reason_code == OpsRefusal.EVIDENCE_IMMUTABLE.value
    truncated = json.loads(store.path.read_text())
    truncated["journal"] = truncated["journal"][:-1]
    with pytest.raises(AuthorizationRefused):
        OperationsConsoleService.from_checkpoint(
            truncated,
            authorities=w.authorities,
            signer=w.signer,
            adapters={"reference-adapter": w.adapter},
        )
    weak = OperationsPolicy.governed().without("enforce_evidence_immutability")
    assert weak.disabled_obligations() == ("enforce_evidence_immutability",)


def test_no_public_mutator_on_journal_and_history_never_rewritten() -> None:
    w = World()
    first = w.full_restart()
    before = [r.event_hash for r in w.service.journal.records()]
    w.full_restart()
    w.review(first.action_id)
    after = [r.event_hash for r in w.service.journal.records()]
    assert after[: len(before)] == before
    public = [n for n in dir(w.service.journal) if not n.startswith("_")]
    assert not any(
        n.startswith(("delete", "remove", "update", "rewrite", "truncate")) for n in public
    )
    assert not any(n.startswith("_tamper") for n in dir(type(w.service.journal)))


def test_evidence_lookup_by_action_id_for_unknown_id_fails_closed() -> None:
    w = World()
    with pytest.raises(AuthorizationRefused) as info:
        w.service.evidence_record("OPA-999999")
    assert info.value.reason_code == OpsRefusal.NOT_FOUND.value


def test_refused_request_is_looked_up_by_its_immutable_action_id() -> None:
    w = World()
    with pytest.raises(AuthorizationRefused):
        w.request(principal="readonly-operator")
    action_id = w.service.journal.records()[-1].correlation_ref
    record = w.service.evidence_record(action_id)
    assert record["result_state"] == "REFUSED"
    assert record["refusal_reason"] == OpsRefusal.READ_ONLY_SESSION.value
    assert record["actor_ref"] == "readonly-operator"
    assert record["failure_classification"] == "AUTHORIZATION_REFUSED"
    assert record["authorization_decision"][0]["allowed"] is False


def test_read_model_distinguishes_states_and_carries_no_secret() -> None:
    w = World()
    done = w.full_restart()
    model = w.service.read_model(now=w.now)
    view = {a["action_id"]: a for a in model["actions"]}[done.action_id]
    assert view["state"] == "SUCCEEDED" and view["execution"]["state"] == "COMPLETED"
    assert view["result"]["backend_metadata"]["api_token"] == "[REDACTED]"
    targets = {t["target_id"]: t for t in model["targets"]}
    assert targets["svc-web"]["production_like"] is True
    assert targets["svc-web"]["artifact_digest"] == "a" * 64
    assert "svc-voting-tally" not in targets
    assert model["self_state"] == "CANDIDATE_NOT_ACCEPTED"
    assert ActionType.STATUS_READ.value.startswith("OPS.")

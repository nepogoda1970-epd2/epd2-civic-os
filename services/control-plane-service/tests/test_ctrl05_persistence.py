"""CTRL-05 persistence: the journal is the truth and the tables are its
projection. A re-chained, re-sealed or table-forged checkpoint is refused."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from _ctrl05_builders import World
from epd2_control_plane_service.audit import EvidenceJournal
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import JsonFileStore
from epd2_control_plane_service.operations_console import EvidenceSealer
from epd2_control_plane_service.oversight_console import (
    FindingSeverity,
    OversightConsoleService,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import EvidencePlane

KEY = b"ctrl05-test-evidence-seal-key-0123456789"


def _rechain(payload: dict[str, Any]) -> dict[str, Any]:
    """Recompute the whole hash chain and the in-file anchor for a tampered
    journal, exactly as a capable tamperer would. Only the keyed seal — whose
    key never enters the file — can still catch it."""
    journal = EvidenceJournal()
    rebuilt = []
    for record in payload["journal"]:
        event = journal.append(
            occurred_at=datetime.fromisoformat(record["occurred_at"]),
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
    return payload


def _restore(world: World, payload: dict[str, Any], **kwargs: Any) -> OversightConsoleService:
    return OversightConsoleService.from_checkpoint(
        payload,
        authorities=world.authorities,
        sources={
            EvidencePlane.CTRL02.value: world.ctrl02_source,
            EvidencePlane.CTRL03.value: world.ctrl03_source,
            EvidencePlane.CTRL04.value: world.ctrl04_source,
        },
        voting_verification=world.voting,
        **kwargs,
    )


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(
        store=JsonFileStore(tmp_path / "ctrl05.json"),
        sealer=EvidenceSealer(KEY),
    )


def _worked_case(world: World) -> str:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    world.attest(case.case_id)
    world.export(case.case_id, "GOVERNANCE_REPORT", refs[:2])
    return case.case_id


def test_a_worked_case_survives_a_restart_intact(world: World) -> None:
    case_id = _worked_case(world)
    before = world.service.case_view(case_id)
    restored = _restore(world, world.service.checkpoint(), sealer=EvidenceSealer(KEY))
    assert restored.case_view(case_id) == before
    assert restored.journal.head_hash() == world.service.journal.head_hash()
    assert len(restored.journal) == len(world.service.journal)


def test_the_store_really_persisted_the_state(world: World, tmp_path: Path) -> None:
    case_id = _worked_case(world)
    path = tmp_path / "ctrl05.json"
    assert path.is_file()
    payload = json.loads(path.read_text())
    assert case_id in payload["cases"]
    restored = _restore(world, payload, sealer=EvidenceSealer(KEY))
    assert restored.case(case_id).case_id == case_id


def test_a_re_chained_checkpoint_is_refused(world: World) -> None:
    """A tamperer who rewrites the journal *and* recomputes the whole chain
    still cannot produce a valid keyed seal."""
    _worked_case(world)
    payload = world.service.checkpoint()
    records = payload["journal"]
    assert records
    records[0]["reason_code"] = "AUD_AUTHORIZED_BUT_ACTUALLY_NOT"
    with pytest.raises(AuthorizationRefused, match="seal does not verify"):
        _restore(world, _rechain(payload), sealer=EvidenceSealer(KEY))


def test_a_forged_seal_is_refused(world: World) -> None:
    _worked_case(world)
    payload = world.service.checkpoint()
    payload["journal_seal"] = "0" * 64
    with pytest.raises(AuthorizationRefused):
        _restore(world, payload, sealer=EvidenceSealer(KEY))


def test_a_checkpoint_sealed_with_another_key_is_refused(world: World) -> None:
    _worked_case(world)
    payload = world.service.checkpoint()
    with pytest.raises(AuthorizationRefused):
        _restore(world, payload, sealer=EvidenceSealer(b"a-different-key-0123456789abcdef"))


def test_a_forged_case_table_is_refused(world: World) -> None:
    """The tables are a projection: a case state with no journal trail behind
    it must not load."""
    case_id = _worked_case(world)
    payload = world.service.checkpoint()
    payload["cases"][case_id]["state"] = ReviewState.CLOSED.value
    with pytest.raises(AuthorizationRefused, match="no closing record"):
        _restore(world, payload, sealer=EvidenceSealer(KEY))


def test_a_forged_attestation_actor_is_refused(world: World) -> None:
    case_id = _worked_case(world)
    payload = world.service.checkpoint()
    attestation = next(iter(payload["attestations"].values()))
    assert attestation["case_id"] == case_id
    attestation["attested_by"] = "someone-who-never-attested"
    with pytest.raises(AuthorizationRefused, match="not backed by its own record"):
        _restore(world, payload, sealer=EvidenceSealer(KEY))


def test_a_dropped_journal_record_is_refused(world: World) -> None:
    _worked_case(world)
    payload = world.service.checkpoint()
    payload["journal"] = payload["journal"][:-1]
    with pytest.raises(AuthorizationRefused):
        _restore(world, payload, sealer=EvidenceSealer(KEY))


def test_an_unknown_checkpoint_schema_is_refused(world: World) -> None:
    payload = world.service.checkpoint()
    payload["schema"] = "epd2.ctrl05.checkpoint/999"
    with pytest.raises(ValueError, match="unknown checkpoint schema"):
        _restore(world, payload, sealer=EvidenceSealer(KEY))


def test_restored_console_keeps_refusing_what_it_refused_before(world: World) -> None:
    from epd2_control_plane_service.exceptions import AuthorizationRefused

    _worked_case(world)
    restored = _restore(world, world.service.checkpoint(), sealer=EvidenceSealer(KEY))
    with pytest.raises(AuthorizationRefused):
        restored.search(
            actor_ref="super-admin",
            session_id="sess-super-admin",
            query=__import__(
                "epd2_control_plane_service.oversight_console",
                fromlist=["EvidenceQuery"],
            ).EvidenceQuery(scope=world.service.case(_first_case(world)).scope),
            now=world.tick(),
        )


def _first_case(world: World) -> str:
    return next(iter(world.service.cases())).case_id


def test_restored_console_still_reads_the_live_planes(world: World) -> None:
    _worked_case(world)
    restored = _restore(world, world.service.checkpoint(), sealer=EvidenceSealer(KEY))
    from epd2_control_plane_service.oversight_console import EvidenceQuery

    result = restored.search(
        actor_ref="auditor",
        session_id="sess-auditor",
        query=EvidenceQuery(scope=world.service.case(_first_case(world)).scope, limit=200),
        now=world.tick(),
    )
    assert result["matched"] > 0
    assert result["unavailable_planes"] == {}


def test_consumed_tickets_stay_consumed_across_a_restart(world: World) -> None:
    from epd2_control_plane_service.exceptions import AuthorizationRefused
    from epd2_control_plane_service.oversight_console import AuditRight, OversightRefusal

    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.service.dispose(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        ticket_id=ticket["ticket_id"],
        disposition=ReviewState.NO_FINDING,
        rationale="done",
        idempotency_key="tk-1",
        now=world.tick(),
    )
    restored = _restore(world, world.service.checkpoint(), sealer=EvidenceSealer(KEY))
    with pytest.raises(AuthorizationRefused) as exc:
        restored.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.FINDING_RAISED,
            rationale="replay after restart",
            idempotency_key="tk-2",
            now=world.tick(),
        )
    assert str(exc.value.reason_code) == OversightRefusal.REPLAYED_REQUEST.value

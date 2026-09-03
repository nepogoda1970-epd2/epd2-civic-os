"""CTRL-05 purpose-bound export with an evidenced redaction decision."""

from __future__ import annotations

import json

import pytest
from _ctrl05_builders import OPS_UNIT, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.oversight_console import (
    EXPORT_PURPOSES,
    MAX_EXPORT_RECORDS,
    AuditRight,
    OversightRefusal,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import PERSON_IDENTIFIER_FIELDS


@pytest.fixture
def world() -> World:
    return World()


def code(exc: pytest.ExceptionInfo[AuthorizationRefused]) -> str:
    return str(exc.value.reason_code)


def test_every_purpose_has_a_bounded_field_allow_list() -> None:
    assert set(EXPORT_PURPOSES) == {
        "INTERNAL_REVIEW",
        "GOVERNANCE_REPORT",
        "EXTERNAL_AUDITOR",
        "STATISTICAL",
    }
    # The purposes narrow monotonically: each is a subset of the one above.
    assert EXPORT_PURPOSES["STATISTICAL"] <= EXPORT_PURPOSES["EXTERNAL_AUDITOR"]
    assert EXPORT_PURPOSES["EXTERNAL_AUDITOR"] <= EXPORT_PURPOSES["GOVERNANCE_REPORT"]
    assert EXPORT_PURPOSES["GOVERNANCE_REPORT"] <= EXPORT_PURPOSES["INTERNAL_REVIEW"]


def test_unknown_purpose_is_refused(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    with pytest.raises(AuthorizationRefused) as exc:
        world.export(case.case_id, "WHATEVER", refs[:1])
    assert code(exc) == OversightRefusal.EXPORT_PURPOSE_UNKNOWN.value


def test_export_without_the_export_right_is_refused(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2], principal="dual-hat-operator")
    with pytest.raises(AuthorizationRefused) as exc:
        world.prepare(case.case_id, "EXPORT", AuditRight.EXPORT, principal="dual-hat-operator")
    assert code(exc) == OversightRefusal.NO_RIGHT.value


def test_export_cannot_reach_outside_the_case(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:1])
    with pytest.raises(AuthorizationRefused) as exc:
        world.export(case.case_id, "INTERNAL_REVIEW", refs[:3])
    assert code(exc) == OversightRefusal.EXPORT_OUT_OF_PURPOSE.value


def test_export_record_bound_is_enforced(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    with pytest.raises(AuthorizationRefused) as exc:
        world.export(case.case_id, "STATISTICAL", refs[:1] * (MAX_EXPORT_RECORDS + 1))
    assert code(exc) == OversightRefusal.EXPORT_LIMIT.value


def test_statistical_export_drops_every_actor_and_authority_field(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    result = world.export(case.case_id, "STATISTICAL", refs[:2])
    allowed = EXPORT_PURPOSES["STATISTICAL"]
    assert result["payload"]["purpose"] == "STATISTICAL"
    for row in result["payload"]["records"]:
        assert set(row) <= allowed
        assert "actor_ref" not in row
        assert "authority_ref" not in row
    dropped = set(result["redaction_decision"]["dropped_fields"])
    assert {"actor_ref", "authority_ref", "reference"} <= dropped


def test_the_redaction_decision_is_recorded_and_referenced(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    result = world.export(case.case_id, "GOVERNANCE_REPORT", refs[:2])
    decision_id = result["export"]["redaction_decision_id"]
    assert decision_id
    decision = world.service.redaction(decision_id)
    assert decision is not None
    assert decision.purpose == "GOVERNANCE_REPORT"
    assert decision.dropped_fields
    assert decision.decided_by == "auditor"


def test_the_export_payload_digest_binds_the_exact_bytes(world: World) -> None:
    import hashlib

    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    result = world.export(case.case_id, "EXTERNAL_AUDITOR", refs[:2])
    recomputed = hashlib.sha256(
        json.dumps(result["payload"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert result["export"]["payload_digest"] == recomputed


def test_export_is_idempotent(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    first = world.export(case.case_id, "INTERNAL_REVIEW", refs[:2], idempotency_key="e-1")
    second = world.export(case.case_id, "INTERNAL_REVIEW", refs[:2], idempotency_key="e-1")
    assert second["export_id"] == first["export"]["export_id"]
    assert len(world.service.exports()) == 1


def test_no_export_carries_a_secret_or_a_person_identifier(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:3])
    for purpose in EXPORT_PURPOSES:
        result = world.export(case.case_id, purpose, refs[:3], idempotency_key=f"px-{purpose}")
        text = json.dumps(result)
        for marker in ("sk_live_", "hunter2", "BEGIN PRIVATE KEY", "AKIA"):
            assert marker.lower() not in text.lower()
        for row in result["payload"]["records"]:
            assert not set(row) & PERSON_IDENTIFIER_FIELDS


def test_export_is_journaled_with_its_purpose_and_digest(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    result = world.export(case.case_id, "GOVERNANCE_REPORT", refs[:2])
    events = world.service.events_of(case.case_id)
    exports = [e for e in events if e.act == "AUDIT.EVIDENCE.EXPORT"]
    assert exports
    text = json.dumps(world.service.journal.export())
    assert result["export"]["payload_digest"] in text
    assert "GOVERNANCE_REPORT" in text


def test_export_appears_in_the_read_model(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.export(case.case_id, "STATISTICAL", refs[:2])
    model = world.service.read_model(now=world.tick())
    assert len(model["exports"]) == 1
    assert model["exports"][0]["purpose"] == "STATISTICAL"
    assert model["secret_surface"] == "ABSENT"
    assert model["operational_execution_surface"] == "ABSENT"
    assert model["shell_sql_exec_surface"] == "ABSENT"


def test_export_requires_commit_time_reauthorization(world: World) -> None:
    """Without a prepared ticket there is no export at all."""
    refs = world.references()
    world.open_case(evidence_refs=refs[:2])
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.export(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id="TKT-000000",
            purpose="STATISTICAL",
            evidence_refs=refs[:2],
            idempotency_key="noticket",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.NOT_FOUND.value


def test_export_of_a_closed_case_still_names_its_redaction(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    world.attest(case.case_id)
    result = world.export(case.case_id, "EXTERNAL_AUDITOR", refs[:2])
    assert world.service.redaction(result["export"]["redaction_decision_id"]) is not None


def test_export_scope_is_the_cases_scope(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    result = world.export(case.case_id, "STATISTICAL", refs[:2])
    assert result["export"]["scope"] == OPS_UNIT.key

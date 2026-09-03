"""CTRL-05 hardening: one reproducing test per defect found by the independent
adversarial review of the first candidate.

Each test fails against the pre-review code. They are kept as their own module
so that a reviewer can see exactly which weaknesses a first pass produced.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from _ctrl05_builders import BAVARIA_UNIT, OPS_UNIT, PRIVACY_UNIT, R, World, _mandate
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.operations_adapters import JsonFileStore
from epd2_control_plane_service.operations_console import EvidenceSealer
from epd2_control_plane_service.oversight_api import (
    CSRF_HEADER,
    SESSION_HEADER,
    OversightApp,
)
from epd2_control_plane_service.oversight_console import (
    AuditRight,
    FindingSeverity,
    FindingState,
    OversightConsoleService,
    OversightRefusal,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import EvidencePlane

KEY = b"ctrl05-hardening-evidence-seal-key-0123456789"


@pytest.fixture
def world() -> World:
    return World()


@pytest.fixture
def sealed_world(tmp_path: Path) -> World:
    return World(store=JsonFileStore(tmp_path / "ctrl05.json"), sealer=EvidenceSealer(KEY))


def code(exc: pytest.ExceptionInfo[AuthorizationRefused]) -> str:
    return str(exc.value.reason_code)


def app_of(w: World) -> OversightApp:
    return OversightApp(w.service, clock=lambda: w.tick())


def scoped(path: str, scope: Any = OPS_UNIT) -> str:
    return f"{path}?region_id={scope.region_id}&org_id={scope.org_id}&unit_id={scope.unit_id}"


def get(w: World, path: str, session: str) -> tuple[int, Any]:
    status, payload, _ = app_of(w).handle("GET", path, {SESSION_HEADER: session}, b"")
    return status, payload


# -- 1. the read routes were readable by anyone with any session -------------


def test_the_case_list_is_scoped_to_the_readers_own_mandate(world: World) -> None:
    world.open_case(title="berlin-only case")
    status, mine = get(world, scoped("/audit/v1/cases"), "sess-auditor")
    assert status == 200 and len(mine["cases"]) == 1

    # Another organization, another unit, and no mandate at all: each is
    # refused, and none of them sees the Berlin case.
    for session, scope, expected in (
        ("sess-bavaria-auditor", BAVARIA_UNIT, 200),
        ("sess-privacy-officer", PRIVACY_UNIT, 200),
    ):
        status, payload = get(world, scoped("/audit/v1/cases", scope), session)
        assert status == expected
        assert payload["cases"] == []
    for session, scope in (
        ("sess-bavaria-auditor", OPS_UNIT),
        ("sess-privacy-officer", OPS_UNIT),
        ("sess-unmandated", OPS_UNIT),
    ):
        status, payload = get(world, scoped("/audit/v1/cases", scope), session)
        assert status == 403, (session, payload)
        assert payload["error"] in {
            OversightRefusal.WRONG_ORGANIZATION_SCOPE.value,
            OversightRefusal.WRONG_UNIT_SCOPE.value,
            OversightRefusal.NO_MANDATE.value,
        }


def test_a_single_case_outside_the_mandate_is_reported_unknown(world: World) -> None:
    case = world.open_case()
    status, payload = get(
        world, scoped(f"/audit/v1/cases/{case.case_id}", BAVARIA_UNIT), "sess-bavaria-auditor"
    )
    assert status == 404
    assert payload["error"] == OversightRefusal.UNKNOWN_CASE.value


def test_the_read_model_is_scoped_and_hides_the_governed_unit_map(world: World) -> None:
    world.open_case()
    status, model = get(world, scoped("/audit/v1/read-model"), "sess-auditor")
    assert status == 200
    assert model["scope"] == OPS_UNIT.key
    assert set(model["evidence_units"].values()) == {OPS_UNIT.key}
    status, other = get(world, scoped("/audit/v1/read-model", BAVARIA_UNIT), "sess-bavaria-auditor")
    assert status == 200
    assert other["cases"] == []
    assert other["evidence_units"] == {}
    assert other["evidence_count"] == 0


def test_the_export_list_is_scoped(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.export(case.case_id, "STATISTICAL", refs[:2])
    status, mine = get(world, scoped("/audit/v1/exports"), "sess-auditor")
    assert status == 200 and len(mine["exports"]) == 1
    status, other = get(world, scoped("/audit/v1/exports", BAVARIA_UNIT), "sess-bavaria-auditor")
    assert status == 200 and other["exports"] == []


# -- 2. action_chain returned the composed CTRL-04 record unscoped -----------


def test_the_composed_ctrl04_record_is_withheld_outside_the_mandate(world: World) -> None:
    """A legitimately scoped Bavarian reviewer, naming Berlin's correlation id
    by enumeration, must get nothing — not an empty chain plus the record."""
    chain = world.service.action_chain(
        actor_ref="bavaria-auditor",
        session_id="sess-bavaria-auditor",
        scope=BAVARIA_UNIT,
        correlation_ref=world.ctrl04_correlation,
        now=world.tick(),
    )
    assert chain["steps"] == []
    assert chain.get("composed_action_record") is None
    assert "DE-BE" not in json.dumps(chain)


def test_the_composed_record_is_served_inside_the_mandate(world: World) -> None:
    chain = world.service.action_chain(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        correlation_ref=world.ctrl04_correlation,
        now=world.tick(),
    )
    assert chain["steps"]
    assert chain.get("composed_action_record") is not None


# -- 3. the checkpoint cross-check compared counts, not content -------------


def _restore(w: World, payload: dict[str, Any]) -> OversightConsoleService:
    return OversightConsoleService.from_checkpoint(
        payload,
        authorities=w.authorities,
        sources={
            EvidencePlane.CTRL02.value: w.ctrl02_source,
            EvidencePlane.CTRL03.value: w.ctrl03_source,
            EvidencePlane.CTRL04.value: w.ctrl04_source,
        },
        voting_verification=w.voting,
        sealer=EvidenceSealer(KEY),
    )


def _worked(w: World) -> str:
    refs = w.references()
    case = w.open_case(evidence_refs=refs[:2], title="a real review")
    w.dispose(case.case_id, ReviewState.FINDING_RAISED, rationale="the basis is missing")
    w.raise_finding(
        case.case_id, FindingSeverity.CRITICAL, refs[0], summary="authority basis absent"
    )
    w.attest(case.case_id, statement="substantiated under MND-attestor")
    return case.case_id


def test_a_downgraded_finding_severity_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    finding = next(f for f in payload["findings"].values() if f["case_id"] == case_id)
    finding["severity"] = FindingSeverity.INFORMATIONAL.value
    with pytest.raises(AuthorizationRefused, match="disagrees with the record that raised it"):
        _restore(sealed_world, payload)


def test_a_rewritten_finding_summary_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    finding = next(f for f in payload["findings"].values() if f["case_id"] == case_id)
    finding["summary"] = "no issue found"
    with pytest.raises(AuthorizationRefused, match="disagrees with the record that raised it"):
        _restore(sealed_world, payload)


def test_a_reattributed_finding_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    finding = next(f for f in payload["findings"].values() if f["case_id"] == case_id)
    finding["raised_by"] = "someone-else"
    with pytest.raises(AuthorizationRefused, match="disagrees with the record that raised it"):
        _restore(sealed_world, payload)


def test_a_rewritten_disposition_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    disposition = next(d for d in payload["dispositions"].values() if d["case_id"] == case_id)
    disposition["state"] = ReviewState.NO_FINDING.value
    disposition["rationale"] = "no finding; closed as noise"
    with pytest.raises(AuthorizationRefused, match="disagrees with its own record"):
        _restore(sealed_world, payload)


def test_a_case_moved_into_another_unit_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    payload["cases"][case_id]["scope"]["unit_id"] = PRIVACY_UNIT.unit_id
    with pytest.raises(AuthorizationRefused, match="does not match the record that opened it"):
        _restore(sealed_world, payload)


def test_a_retitled_case_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    payload["cases"][case_id]["title"] = "routine check"
    with pytest.raises(AuthorizationRefused, match="does not match the record that opened it"):
        _restore(sealed_world, payload)


def test_a_rewritten_attestation_statement_is_refused_on_restore(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    payload = sealed_world.service.checkpoint()
    attestation = next(a for a in payload["attestations"].values() if a["case_id"] == case_id)
    attestation["statement"] = "nothing was found"
    with pytest.raises(AuthorizationRefused, match="disagrees with its own record"):
        _restore(sealed_world, payload)


def test_an_untouched_worked_case_still_restores(sealed_world: World) -> None:
    case_id = _worked(sealed_world)
    before = sealed_world.service.case_view(case_id)
    restored = _restore(sealed_world, sealed_world.service.checkpoint())
    assert restored.case_view(case_id) == before


# -- 4. the idempotency replay ran before any authority check ---------------


def test_a_replay_on_a_revoked_session_is_refused(world: World) -> None:
    refs = world.references()
    world.open_case(evidence_refs=refs[:1], idempotency_key="replay-1")
    world.service.revoke_session("sess-auditor")
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(evidence_refs=refs[:1], idempotency_key="replay-1")
    assert code(exc) == OversightRefusal.SESSION_REVOKED.value


def test_a_replay_without_the_csrf_token_is_refused(world: World) -> None:
    refs = world.references()
    world.open_case(evidence_refs=refs[:1], idempotency_key="replay-2")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.open_case(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token=None,
            scope=OPS_UNIT,
            title="x",
            evidence_refs=refs[:1],
            idempotency_key="replay-2",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.CSRF_INVALID.value


def test_a_replay_after_the_mandate_was_superseded_is_refused(world: World) -> None:
    refs = world.references()
    world.open_case(evidence_refs=refs[:1], idempotency_key="replay-3")
    world.service.supersede_mandate("MND-auditor", "MND-auditor-next")
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(evidence_refs=refs[:1], idempotency_key="replay-3")
    assert code(exc) == OversightRefusal.MANDATE_SUPERSEDED.value


def test_a_replayed_finding_still_needs_a_real_ticket(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0], idempotency_key="replay-f")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.raise_finding(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id="TKT-does-not-exist",
            severity=FindingSeverity.LOW,
            summary="replayed with a forged ticket",
            evidence_ref=refs[0],
            idempotency_key="replay-f",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.NOT_FOUND.value


def test_a_replay_is_itself_journaled(world: World) -> None:
    refs = world.references()
    world.open_case(evidence_refs=refs[:1], idempotency_key="replay-4")
    before = len(world.service.journal)
    world.open_case(evidence_refs=refs[:1], idempotency_key="replay-4")
    assert len(world.service.journal) > before
    replays = [r for r in world.service.journal.records() if r.result == "REPLAYED"]
    assert replays and replays[-1].reason_code == OversightRefusal.REPLAYED_REQUEST.value


def test_a_replayed_dispute_returns_the_original_and_its_dispute(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    finding = world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    first = world.service.dispute_finding(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        finding_id=finding.finding_id,
        rationale="disputed",
        idempotency_key="replay-d",
        now=world.tick(),
    )
    second = world.service.dispute_finding(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        finding_id=finding.finding_id,
        rationale="disputed again",
        idempotency_key="replay-d",
        now=world.tick(),
    )
    assert second[0].finding_id == first[0].finding_id
    assert second[1].finding_id == first[1].finding_id
    assert second[0].finding_id != second[1].finding_id
    assert second[0].state is FindingState.DISPUTED


# -- 5. refusals raised outside the guarded block left no evidence ----------


def test_an_unknown_case_refusal_is_evidence_bearing(world: World) -> None:
    for act in (
        lambda: world.prepare("CASE-999999", "DISPOSE", AuditRight.REVIEW),
        lambda: world.service.clarify(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            case_id="CASE-999999",
            text="x",
            evidence_ref=None,
            idempotency_key=f"unk-{world.tick().timestamp()}",
            now=world.now,
        ),
        lambda: world.service.close_case(
            actor_ref="attestor",
            session_id="sess-attestor",
            csrf_token="csrf-attestor",
            case_id="CASE-999999",
            expected_version=1,
            idempotency_key=f"unkc-{world.tick().timestamp()}",
            now=world.now,
        ),
        lambda: world.service.link_remediation(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            case_id="CASE-999999",
            remediation_plane="CTRL-04",
            remediation_ref="OPA-000001",
            idempotency_key=f"unkr-{world.tick().timestamp()}",
            now=world.now,
        ),
    ):
        before = len(world.service.journal)
        with pytest.raises(AuthorizationRefused) as exc:
            act()
        assert code(exc) == OversightRefusal.UNKNOWN_CASE.value
        assert len(world.service.journal) > before


def test_a_clock_rollback_is_evidence_bearing(world: World) -> None:
    from datetime import timedelta

    world.search()
    before = len(world.service.journal)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.search(
            actor_ref="auditor",
            session_id="sess-auditor",
            query=__import__(
                "epd2_control_plane_service.oversight_console",
                fromlist=["EvidenceQuery"],
            ).EvidenceQuery(scope=OPS_UNIT),
            now=world.now - timedelta(hours=1),
        )
    assert code(exc) == OversightRefusal.CLOCK_ROLLBACK.value
    assert len(world.service.journal) > before
    rolled = [
        r
        for r in world.service.journal.records()
        if r.reason_code == OversightRefusal.CLOCK_ROLLBACK.value
    ]
    assert rolled and rolled[-1].object_ref == "clock"


# -- 6. the correlation graph failed open on an unavailable plane -----------


def test_the_correlation_graph_fails_closed_on_an_unavailable_plane(world: World) -> None:
    world.ctrl02_source.available = False
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.correlation_graph(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            anchor=world.ctrl04_correlation,
            depth=2,
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.SOURCE_UNAVAILABLE.value


# -- 7. remediation_plane was the one unscrubbed governed field -------------


def test_every_governed_free_text_field_is_scrubbed(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2], title="password=hunter2 sk_live_abcdef review")
    world.service.clarify(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        text="the token was sk_live_abcdef and " + "AKIA" + "IOSFODNN7EXAMPLE",
        evidence_ref=refs[0],
        idempotency_key="scrub-1",
        now=world.tick(),
    )
    world.service.link_remediation(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        remediation_plane="sk_live_abcdef password=hunter2",
        remediation_ref="OPA-000001",
        idempotency_key="scrub-2",
        now=world.tick(),
    )
    world.dispose(
        case.case_id,
        ReviewState.FINDING_RAISED,
        rationale="the credential sk_live_abcdef was in the log",
    )
    world.raise_finding(
        case.case_id,
        FindingSeverity.HIGH,
        refs[0],
        summary="token sk_live_abcdef appeared in the provider log",
    )
    world.attest(case.case_id, statement="sk_live_abcdef was observed", principal="attestor")
    surfaces = {
        "case_view": world.service.case_view(case.case_id),
        "read_model": world.service.governed_read_model(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            now=world.tick(),
        ),
        "journal": world.service.journal.export(),
    }
    for name, payload in surfaces.items():
        text = json.dumps(payload)
        for marker in ("sk_live_abcdef", "hunter2", "AKIA" + "IOSFODNN7EXAMPLE"):
            assert marker not in text, f"{marker} reached {name}"


def test_an_export_carrying_secret_shaped_bytes_is_refused(world: World) -> None:
    """The sweep runs over the *unredacted* bytes, so it can actually fail."""
    from epd2_control_plane_service.oversight_console import SECRET_SHAPE_MARKERS

    assert "AKIA" in SECRET_SHAPE_MARKERS
    assert "ghp_" in SECRET_SHAPE_MARKERS
    assert "-----BEGIN" in SECRET_SHAPE_MARKERS


# -- 8. the console held live mutating handles to the planes ---------------


def test_the_console_exposes_no_handle_to_a_plane(world: World) -> None:
    assert not hasattr(world.service, "sources")
    assert world.service.plane_ids() == ("CTRL-02", "CTRL-03", "CTRL-04")
    for attribute in vars(world.service):
        value = getattr(world.service, attribute)
        for forbidden in ("approve", "commit", "execute", "dispatch", "resolve", "activate"):
            assert not hasattr(value, forbidden), f"{attribute}.{forbidden} is reachable"


# -- 9. the CSRF token appeared in a read body and in the checkpoint --------


def test_the_csrf_token_is_delivered_as_a_header_not_a_body(world: World) -> None:
    status, payload, _c, extra = app_of(world).handle_with_headers(
        "GET", "/audit/v1/me", {SESSION_HEADER: "sess-auditor"}, b""
    )
    assert status == 200
    assert "csrf_token" not in payload
    assert extra[CSRF_HEADER] == "csrf-auditor"
    assert "csrf-auditor" not in json.dumps(payload)


def test_no_session_token_is_persisted_in_a_checkpoint(sealed_world: World, tmp_path: Path) -> None:
    _worked(sealed_world)
    payload = json.loads((tmp_path / "ctrl05.json").read_text())
    for session in payload["sessions"].values():
        assert "csrf_token" not in session
    assert "csrf-auditor" not in json.dumps(payload)


def test_a_restored_session_cannot_mutate_with_the_old_token(sealed_world: World) -> None:
    _worked(sealed_world)
    restored = _restore(sealed_world, sealed_world.service.checkpoint())
    with pytest.raises(AuthorizationRefused) as exc:
        restored.open_case(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            scope=OPS_UNIT,
            title="after restart",
            evidence_refs=sealed_world.references()[:1],
            idempotency_key="after-restart",
            now=sealed_world.tick(),
        )
    assert code(exc) == OversightRefusal.CSRF_INVALID.value


# -- 10. the frontend gate asserted substrings, not behaviour --------------


def test_a_hostile_case_title_is_rendered_escaped(world: World) -> None:
    """The page escapes every server value at ingestion. The proof is that a
    script-shaped title survives as text, not as markup."""
    from epd2_control_plane_service.oversight_api import CONSOLE_HTML

    hostile = "<img src=x onerror=alert(1)>"
    case = world.open_case(title=hostile)
    view = world.service.case_view(case.case_id)
    # The server stores it verbatim (it is data), and the page escapes it.
    assert view["title"] == hostile
    assert "const esc=" in CONSOLE_HTML
    assert "esc(await r.json())" in CONSOLE_HTML
    # Every render path goes through the escaped object, never the raw one.
    assert "await r.json()" in CONSOLE_HTML
    assert CONSOLE_HTML.count("await r.json()") == CONSOLE_HTML.count("esc(await r.json())")


def test_the_frontend_never_decides_an_act_it_does_not_re_request(world: World) -> None:
    """Client-side `has(right)` only greys controls. The server refuses
    regardless — proven by driving the act with the control's precondition
    deliberately unmet."""
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(principal="read-only-auditor")
    assert code(exc) == OversightRefusal.NO_RIGHT.value


# -- minor findings ---------------------------------------------------------


def test_the_world_helper_builds_a_reviewed_case(world: World) -> None:
    case = world.reviewed_case()
    assert world.service.dispositions_of(case.case_id)


def test_a_mandate_cannot_borrow_an_operational_capability(world: World) -> None:
    """A mandate may not use `OPS.EXECUTE` (or any operational or universal
    capability) as the authority backing an audit right."""
    world.service.register_mandate(
        _mandate(
            "MND-opsright",
            "right-borrower",
            OPS_UNIT,
            frozenset({R.READ}),
            {R.READ: "ag-ops-borrow"},
        )
    )
    with pytest.raises(AuthorizationRefused) as exc:
        world.search(principal="right-borrower")
    assert code(exc) == OversightRefusal.OPERATIONAL_RIGHT_NOT_USABLE.value

"""CTRL-05 review lifecycle: append-only history, two-phase commit-time
reauthorization, case versioning, idempotency and disposition ordering."""

from __future__ import annotations

from datetime import timedelta

import pytest
from _ctrl05_builders import OPS_UNIT, R, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.oversight_console import (
    DISPOSITION_STATES,
    OPEN_STATES,
    AuditRight,
    FindingSeverity,
    FindingState,
    OversightRefusal,
    ReviewState,
)
from epd2_control_plane_service.oversight_sources import EvidencePlane


@pytest.fixture
def world() -> World:
    return World()


def code(exc: pytest.ExceptionInfo[AuthorizationRefused]) -> str:
    return str(exc.value.reason_code)


# -- a case always names its evidence ----------------------------------------


def test_case_must_name_the_evidence_it_reviews(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(evidence_refs=[])
    assert code(exc) == OversightRefusal.FINDING_WITHOUT_EVIDENCE.value


def test_case_cannot_name_evidence_outside_its_scope(world: World) -> None:
    world.service.evidence_units.pop(
        f"{EvidencePlane.CTRL03.value}:{world.ctrl03_source.stream_id()}"
    )
    ctrl03 = "CTRL-03:ctrl03-credential-lifecycle:ctrl03-event-00000001"
    with pytest.raises(AuthorizationRefused) as exc:
        world.open_case(evidence_refs=[ctrl03])
    assert code(exc) == OversightRefusal.WRONG_UNIT_SCOPE.value


def test_open_case_records_the_mandate_and_authority_that_allowed_it(world: World) -> None:
    case = world.open_case()
    assert "MND-auditor" in case.mandate_ref
    assert case.authority_ref.startswith("ag-rev@v")
    assert case.state in OPEN_STATES
    assert case.version == 1


def test_open_case_is_idempotent(world: World) -> None:
    first = world.open_case(idempotency_key="same")
    second = world.open_case(idempotency_key="same")
    assert first.case_id == second.case_id
    assert len(world.service.cases()) == 1


# -- append-only history ------------------------------------------------------


def test_dispositions_are_appended_never_replaced(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NEEDS_CLARIFICATION, rationale="need context")
    world.dispose(case.case_id, ReviewState.FINDING_RAISED, rationale="context received")
    view = world.service.case_view(case.case_id)
    assert [d["state"] for d in view["dispositions"]] == [
        ReviewState.NEEDS_CLARIFICATION.value,
        ReviewState.FINDING_RAISED.value,
    ]
    assert view["dispositions"][1]["supersedes"] == view["dispositions"][0]["disposition_id"]
    assert view["history_is_append_only"] is True


def test_a_disputed_finding_is_retained_alongside_its_dispute(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    finding = world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    superseded, dispute = world.service.dispute_finding(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        finding_id=finding.finding_id,
        rationale="the authority basis was recorded in CTRL-02, not here",
        idempotency_key="disp-1",
        now=world.tick(),
    )
    assert superseded.finding_id == finding.finding_id
    assert superseded.state is FindingState.DISPUTED
    assert dispute.finding_id != finding.finding_id
    ids = {f["finding_id"] for f in world.service.case_view(case.case_id)["findings"]}
    assert {finding.finding_id, dispute.finding_id} <= ids


def test_no_method_removes_a_case_record(world: World) -> None:
    for name in ("delete_case", "remove_finding", "withdraw_disposition", "purge"):
        assert not hasattr(world.service, name)


def test_the_oversight_journal_only_grows(world: World) -> None:
    before = len(world.service.journal)
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    assert len(world.service.journal) > before
    head = world.service.journal.head_hash()
    world.search()
    assert len(world.service.journal) > before
    assert world.service.journal.head_hash() != head


def test_a_refusal_is_itself_evidence(world: World) -> None:
    refs = world.references()  # a successful read first, so it is not counted
    before = len(world.service.journal)
    with pytest.raises(AuthorizationRefused):
        world.open_case(principal="read-only-auditor", evidence_refs=refs[:1])
    assert len(world.service.journal) > before
    refused = [r for r in world.service.journal.records() if r.result == "REFUSED"]
    assert refused and refused[-1].action_id == "AUDIT.CASE.OPEN"


def test_every_refusal_family_appends_its_own_record(world: World) -> None:
    refs = world.references()
    observed = {}
    for label, act in (
        ("no_mandate", lambda: world.search(principal="unmandated")),
        ("universal", lambda: world.search(principal="super-admin")),
        ("wrong_unit", lambda: world.search(principal="privacy-officer", scope=OPS_UNIT)),
        (
            "no_right",
            lambda: world.open_case(principal="read-only-auditor", evidence_refs=refs[:1]),
        ),
    ):
        before = len(world.service.journal)
        with pytest.raises(AuthorizationRefused):
            act()
        observed[label] = len(world.service.journal) - before
    assert all(growth > 0 for growth in observed.values()), observed


def test_a_second_attestation_on_an_attested_case_is_refused(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    world.attest(case.case_id, idempotency_key="att-1")
    with pytest.raises(AuthorizationRefused) as exc:
        world.attest(case.case_id, idempotency_key="att-2")
    assert code(exc) == OversightRefusal.DISPOSITION_REQUIRED.value


def test_a_disputed_finding_is_never_dropped_from_the_case(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    finding = world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    world.service.dispute_finding(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        finding_id=finding.finding_id,
        rationale="disputed",
        idempotency_key="drop-1",
        now=world.tick(),
    )
    stored = world.service.findings_of(case.case_id)
    assert finding.finding_id in {f.finding_id for f in stored}
    assert len(stored) == 2
    assert world.service.case(case.case_id).finding_ids[0] == finding.finding_id


# -- two-phase commit-time reauthorization -----------------------------------


def test_prepare_captures_authority_and_evidence_digests(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    assert ticket["case_id"] == case.case_id
    assert ticket["case_version"] == case.version
    assert ticket["authority_grant_id"] == "ag-rev"
    assert set(ticket["evidence_digests"]) == set(case.evidence_refs)
    assert ticket["consumed"] is False


def test_a_ticket_cannot_be_replayed(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.service.dispose(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        ticket_id=ticket["ticket_id"],
        disposition=ReviewState.NO_FINDING,
        rationale="first",
        idempotency_key="one",
        now=world.tick(),
    )
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.FINDING_RAISED,
            rationale="second",
            idempotency_key="two",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.REPLAYED_REQUEST.value


def test_a_ticket_is_bound_to_its_act(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.attest(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            statement="not what this ticket was prepared for",
            idempotency_key="mis-1",
            now=world.tick(),
        )
    assert code(exc) in {
        OversightRefusal.PARAMETER_INVALID.value,
        OversightRefusal.REPLAYED_REQUEST.value,
        OversightRefusal.NO_RIGHT.value,
    }


def test_a_ticket_is_bound_to_its_actor(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="dual-hat-operator",
            session_id="sess-dual-hat-operator",
            csrf_token="csrf-dual-hat-operator",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="not my ticket",
            idempotency_key="other-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.PARAMETER_INVALID.value


def test_an_expired_ticket_is_refused(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="too late",
            idempotency_key="late-1",
            now=world.now + timedelta(minutes=11),
        )
    assert code(exc) == OversightRefusal.STALE_AUTHORITY.value


def test_authority_withdrawn_between_prepare_and_commit_is_refused(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.authorities._grants.pop("ag-rev")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="authority gone",
            idempotency_key="gone-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.AUTHORITY_UNRESOLVABLE.value


def test_mandate_revoked_between_prepare_and_commit_is_refused(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.service.supersede_mandate("MND-auditor", "MND-auditor-next")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="mandate gone",
            idempotency_key="mgone-1",
            now=world.tick(),
        )
    assert code(exc) in {
        OversightRefusal.MANDATE_SUPERSEDED.value,
        OversightRefusal.STALE_AUTHORITY.value,
    }


def test_session_revoked_between_prepare_and_commit_is_refused(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.service.revoke_session("sess-auditor")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="session gone",
            idempotency_key="sgone-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.SESSION_REVOKED.value


def test_evidence_diverging_between_prepare_and_commit_is_refused(world: World) -> None:
    """The strongest of the commit-time checks: if the evidence under review
    changed after it was read, the act does not land on a stale reading."""
    refs = world.references(EvidencePlane.CTRL02)
    case = world.open_case(evidence_refs=refs[:1])
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    events = list(world.ctrl02._events)
    first = events[0]
    events[0] = type(first)(
        **{
            **{f: getattr(first, f) for f in first.__dataclass_fields__},
            "reason": "changed after the reviewer read it",
        }
    )
    world.ctrl02._events = events
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="based on a stale reading",
            idempotency_key="div-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.EVIDENCE_DIVERGED.value


def test_case_changing_between_prepare_and_commit_is_refused(world: World) -> None:
    case = world.open_case()
    ticket = world.prepare(case.case_id, "DISPOSE", AuditRight.REVIEW)
    world.dispose(case.case_id, ReviewState.NEEDS_CLARIFICATION)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id=ticket["ticket_id"],
            disposition=ReviewState.NO_FINDING,
            rationale="stale case version",
            idempotency_key="ver-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.STALE_CASE_VERSION.value


def test_unknown_ticket_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.dispose(
            actor_ref="auditor",
            session_id="sess-auditor",
            csrf_token="csrf-auditor",
            ticket_id="TKT-999999",
            disposition=ReviewState.NO_FINDING,
            rationale="no such ticket",
            idempotency_key="nt-1",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.NOT_FOUND.value


# -- findings -----------------------------------------------------------------


def test_a_finding_names_an_exact_verified_evidence_reference(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    finding = world.raise_finding(case.case_id, FindingSeverity.CRITICAL, refs[1])
    assert finding.evidence_reference.key == refs[1]
    assert finding.evidence_content_digest
    assert finding.state is FindingState.RAISED


def test_a_finding_cannot_name_evidence_outside_the_case_scope(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:1])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    with pytest.raises(AuthorizationRefused) as exc:
        world.raise_finding(
            case.case_id,
            FindingSeverity.HIGH,
            "CTRL-04:ctrl04-operations-console:nope",
        )
    assert code(exc) == OversightRefusal.FINDING_WITHOUT_EVIDENCE.value


def test_findings_are_idempotent_on_the_same_key(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    first = world.raise_finding(
        case.case_id, FindingSeverity.HIGH, refs[0], idempotency_key="f-same"
    )
    second = world.raise_finding(
        case.case_id, FindingSeverity.LOW, refs[1], idempotency_key="f-same"
    )
    assert first.finding_id == second.finding_id


# -- attestation and closure -------------------------------------------------


def test_attestation_requires_a_prior_disposition(world: World) -> None:
    case = world.open_case()
    with pytest.raises(AuthorizationRefused) as exc:
        world.attest(case.case_id)
    assert code(exc) == OversightRefusal.DISPOSITION_REQUIRED.value


def test_attestation_records_the_case_version_it_attested(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    version = world.service.case(case.case_id).version
    attestation = world.attest(case.case_id)
    assert attestation.case_version == version
    assert attestation.outcome is ReviewState.NO_FINDING
    assert attestation.reauthorized_at >= attestation.attested_at - timedelta(seconds=5)


def test_closure_requires_the_expected_version(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    world.attest(case.case_id)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.close_case(
            actor_ref="attestor",
            session_id="sess-attestor",
            csrf_token="csrf-attestor",
            case_id=case.case_id,
            expected_version=1,
            idempotency_key="close-bad",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.STALE_CASE_VERSION.value


def test_closure_requires_an_attestation(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.close_case(
            actor_ref="attestor",
            session_id="sess-attestor",
            csrf_token="csrf-attestor",
            case_id=case.case_id,
            expected_version=world.service.case(case.case_id).version,
            idempotency_key="close-noatt",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.ATTESTATION_WITHOUT_AUTHORITY.value


def test_a_closed_case_accepts_nothing_further(world: World) -> None:
    case = world.open_case()
    world.dispose(case.case_id, ReviewState.NO_FINDING)
    world.attest(case.case_id)
    closed = world.service.close_case(
        actor_ref="attestor",
        session_id="sess-attestor",
        csrf_token="csrf-attestor",
        case_id=case.case_id,
        expected_version=world.service.case(case.case_id).version,
        idempotency_key="close-ok",
        now=world.tick(),
    )
    assert closed.state is ReviewState.CLOSED
    with pytest.raises(AuthorizationRefused) as exc:
        world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    assert code(exc) == OversightRefusal.WRONG_STATE.value


def test_closed_case_history_is_still_complete(world: World) -> None:
    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    world.dispose(case.case_id, ReviewState.FINDING_RAISED)
    world.raise_finding(case.case_id, FindingSeverity.HIGH, refs[0])
    world.attest(case.case_id)
    world.service.close_case(
        actor_ref="attestor",
        session_id="sess-attestor",
        csrf_token="csrf-attestor",
        case_id=case.case_id,
        expected_version=world.service.case(case.case_id).version,
        idempotency_key="close-hist",
        now=world.tick(),
    )
    view = world.service.case_view(case.case_id)
    assert view["state"] == ReviewState.CLOSED.value
    assert view["dispositions"] and view["findings"] and view["attestations"]
    assert view["oversight_events"]


def test_disposition_states_are_the_documented_set() -> None:
    assert (
        frozenset(
            {
                ReviewState.NEEDS_CLARIFICATION,
                ReviewState.FINDING_RAISED,
                ReviewState.NO_FINDING,
            }
        )
        == DISPOSITION_STATES
    )
    assert ReviewState.CLOSED not in OPEN_STATES


# -- clock ---------------------------------------------------------------------


def test_a_clock_rollback_is_refused(world: World) -> None:
    world.search()
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


def test_rights_enum_is_the_documented_set() -> None:
    assert {r.value for r in R} == {
        "AUDIT.READ",
        "AUDIT.CORRELATE",
        "AUDIT.REVIEW",
        "AUDIT.ATTEST",
        "AUDIT.EXPORT",
    }

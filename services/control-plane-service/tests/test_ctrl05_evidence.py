"""CTRL-05 evidence: independent integrity, immutability, fail-closed sources,
secret redaction, person-identifier screening and the voting boundary.
"""

from __future__ import annotations

import pytest
from _ctrl05_builders import BAVARIA_UNIT, OPS_UNIT, PRIVACY_UNIT, World
from epd2_control_plane_service.exceptions import AuthorizationRefused
from epd2_control_plane_service.oversight_console import (
    FRONTEND_MAY_ASSERT_AUTHORITY,
    FRONTEND_MAY_ASSERT_INTEGRITY,
    MAX_GRAPH_DEPTH,
    MAX_GRAPH_NODES,
    MAX_QUERY_LIMIT,
    SOURCE_EVIDENCE_IS_MUTABLE,
    EvidenceQuery,
    OversightRefusal,
)
from epd2_control_plane_service.oversight_sources import (
    PERSON_IDENTIFIER_FIELDS,
    Ctrl02EvidenceSource,
    Ctrl04EvidenceSource,
    EvidencePlane,
    IntegrityState,
    SourceUnavailable,
    VotingVerificationReference,
    collect,
)


@pytest.fixture
def world() -> World:
    return World()


def code(exc: pytest.ExceptionInfo[AuthorizationRefused]) -> str:
    return str(exc.value.reason_code)


# -- real evidence, independently verified -----------------------------------


def test_all_three_planes_produce_real_verified_evidence(world: World) -> None:
    result = world.search(limit=MAX_QUERY_LIMIT)
    planes = {r["reference"]["plane"] for r in result["records"]}
    assert planes == {
        EvidencePlane.CTRL02.value,
        EvidencePlane.CTRL03.value,
        EvidencePlane.CTRL04.value,
    }
    assert result["integrity_summary"] == {IntegrityState.VERIFIED.value: result["matched"]}
    assert result["unavailable_planes"] == {}


def test_integrity_is_re_derived_not_read_from_the_record(world: World) -> None:
    ref = world.references(EvidencePlane.CTRL04)[0]
    verdict = world.service.verify_evidence(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        reference_key=ref,
        now=world.tick(),
    )
    assert verdict["state"] == IntegrityState.VERIFIED.value
    assert verdict["trustworthy"] is True
    assert verdict["recorded_hash"] == verdict["recomputed_hash"]
    assert verdict["verified_by"] == "CTRL-05 independent re-derivation"


def test_a_rewritten_source_record_is_reported_not_trusted(world: World) -> None:
    """CTRL-05 cannot repair the source; it must *report* the break."""
    events = list(world.ctrl02._events)
    tampered = events[1]
    events[1] = type(tampered)(
        **{
            **{f: getattr(tampered, f) for f in tampered.__dataclass_fields__},
            "reason": "silently rewritten after the fact",
        }
    )
    world.ctrl02._events = events
    result = world.search(limit=MAX_QUERY_LIMIT)
    states = {
        r["reference"]["key"]: r["integrity"]["state"]
        for r in result["records"]
        if r["reference"]["plane"] == EvidencePlane.CTRL02.value
    }
    assert IntegrityState.HASH_MISMATCH.value in states.values()
    assert any(s != IntegrityState.VERIFIED.value for s in states.values())


def test_a_broken_chain_is_reported_for_every_later_record(world: World) -> None:
    events = list(world.ctrl02._events)
    del events[1]
    world.ctrl02._events = events
    result = world.search(limit=MAX_QUERY_LIMIT)
    ctrl02 = [r for r in result["records"] if r["reference"]["plane"] == EvidencePlane.CTRL02.value]
    assert any(
        r["integrity"]["state"]
        in {IntegrityState.CHAIN_BROKEN.value, IntegrityState.SEQUENCE_BROKEN.value}
        for r in ctrl02
    )


def test_untrustworthy_evidence_cannot_carry_a_finding(world: World) -> None:
    from epd2_control_plane_service.oversight_console import FindingSeverity

    refs = world.references()
    case = world.open_case(evidence_refs=refs[:2])
    events = list(world.ctrl02._events)
    tampered = events[0]
    events[0] = type(tampered)(
        **{
            **{f: getattr(tampered, f) for f in tampered.__dataclass_fields__},
            "reason": "rewritten",
        }
    )
    world.ctrl02._events = events
    ctrl02_ref = next(r for r in refs if r.startswith(EvidencePlane.CTRL02.value))
    with pytest.raises(AuthorizationRefused) as exc:
        world.raise_finding(case.case_id, FindingSeverity.HIGH, ctrl02_ref)
    assert code(exc) in {
        OversightRefusal.EVIDENCE_UNTRUSTWORTHY.value,
        OversightRefusal.EVIDENCE_DIVERGED.value,
        OversightRefusal.UNKNOWN_EVIDENCE.value,
    }


# -- source evidence is immutable to CTRL-05 ---------------------------------


def test_source_evidence_is_declared_and_actually_immutable(world: World) -> None:
    assert SOURCE_EVIDENCE_IS_MUTABLE is False
    before = [(e.event_id, e.event_hash) for e in world.ctrl02._events]
    ctrl04_before = world.ctrl04.journal.head_hash()
    world.search(limit=MAX_QUERY_LIMIT)
    case = world.open_case()
    world.service.clarify(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        text="an annotation, not an edit",
        evidence_ref=world.references()[0],
        idempotency_key="clar-imm",
        now=world.tick(),
    )
    assert [(e.event_id, e.event_hash) for e in world.ctrl02._events] == before
    assert world.ctrl04.journal.head_hash() == ctrl04_before


def test_annotation_is_a_separate_record_referencing_the_source(world: World) -> None:
    case = world.open_case()
    ref = world.references()[0]
    clarification = world.service.clarify(
        actor_ref="auditor",
        session_id="sess-auditor",
        csrf_token="csrf-auditor",
        case_id=case.case_id,
        text="context added by oversight",
        evidence_ref=ref,
        idempotency_key="clar-sep",
        now=world.tick(),
    )
    assert clarification.evidence_reference is not None
    assert clarification.evidence_reference.key == ref
    view = world.service.case_view(case.case_id)
    assert view["clarifications"][0]["source_evidence_mutated"] is False


def test_source_adapters_expose_no_mutating_method(world: World) -> None:
    for source in (world.ctrl02_source, world.ctrl03_source, world.ctrl04_source):
        names = {n for n in dir(source) if not n.startswith("__")}
        assert not names & {
            "append",
            "write",
            "delete",
            "truncate",
            "replace",
            "set_event",
            "rewrite",
        }


# -- fail closed on unavailable sources --------------------------------------


def test_unavailable_plane_is_never_reported_as_absence_of_evidence(world: World) -> None:
    world.ctrl02_source.available = False
    result = world.search(limit=MAX_QUERY_LIMIT)
    assert EvidencePlane.CTRL02.value in result["unavailable_planes"]
    assert not [
        r for r in result["records"] if r["reference"]["plane"] == EvidencePlane.CTRL02.value
    ]


def test_correlation_fails_closed_when_a_plane_is_unavailable(world: World) -> None:
    world.ctrl04_source.available = False
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.action_chain(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            correlation_ref=world.ctrl04_correlation,
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.SOURCE_UNAVAILABLE.value


def test_collect_records_unavailability_per_plane(world: World) -> None:
    world.ctrl03_source.available = False
    envelopes, unavailable = collect(
        [world.ctrl02_source, world.ctrl03_source, world.ctrl04_source]
    )
    assert set(unavailable) == {EvidencePlane.CTRL03.value}
    assert envelopes


def test_a_raising_source_is_unavailable_not_empty() -> None:
    class Exploding:
        @property
        def events(self) -> None:
            raise RuntimeError("backend gone")

    source = Ctrl02EvidenceSource(Exploding())
    with pytest.raises(SourceUnavailable):
        source.envelopes()


def test_unmapped_evidence_stream_is_invisible(world: World) -> None:
    """Unit scope fails closed: evidence with no governed unit assignment is
    not visible to anyone, rather than visible to everyone."""
    world.service.evidence_units.pop(
        f"{EvidencePlane.CTRL04.value}:{world.ctrl04_source.stream_id()}"
    )
    result = world.search(limit=MAX_QUERY_LIMIT)
    assert not [
        r for r in result["records"] if r["reference"]["plane"] == EvidencePlane.CTRL04.value
    ]


def test_identically_named_units_in_two_organizations_do_not_merge(world: World) -> None:
    """`unit-operations-audit` exists in Berlin and in Bavaria; the Bavarian
    mandate must not reach Berlin's unscoped CTRL-03 evidence."""
    assert OPS_UNIT.unit_id == BAVARIA_UNIT.unit_id
    result = world.search(principal="bavaria-auditor", scope=BAVARIA_UNIT)
    assert result["matched"] == 0


def test_privacy_unit_sees_nothing_of_the_operations_unit(world: World) -> None:
    world.service.register_evidence_unit(
        EvidencePlane.CTRL02, world.ctrl02_source.stream_id(), PRIVACY_UNIT
    )
    result = world.search(principal="privacy-officer", scope=PRIVACY_UNIT)
    planes = {r["reference"]["plane"] for r in result["records"]}
    assert planes == {EvidencePlane.CTRL02.value}
    ops = world.search(limit=MAX_QUERY_LIMIT)
    assert not [r for r in ops["records"] if r["reference"]["plane"] == EvidencePlane.CTRL02.value]


# -- bounded queries ----------------------------------------------------------


def test_query_limit_is_bounded() -> None:
    with pytest.raises(ValueError):
        EvidenceQuery(scope=OPS_UNIT, limit=MAX_QUERY_LIMIT + 1)
    with pytest.raises(ValueError):
        EvidenceQuery(scope=OPS_UNIT, limit=0)


def test_truncation_is_reported(world: World) -> None:
    result = world.search(limit=2)
    assert result["matched"] == 2
    assert result["truncated"] is True


def test_action_chain_requires_an_exact_anchor(world: World) -> None:
    for anchor in ("", "*", "ALL"):
        with pytest.raises(AuthorizationRefused) as exc:
            world.service.action_chain(
                actor_ref="auditor",
                session_id="sess-auditor",
                scope=OPS_UNIT,
                correlation_ref=anchor,
                now=world.tick(),
            )
        assert code(exc) == OversightRefusal.UNBOUNDED_QUERY.value


def test_correlation_graph_is_bounded(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.correlation_graph(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            anchor=world.ctrl04_correlation,
            depth=MAX_GRAPH_DEPTH + 1,
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.GRAPH_LIMIT.value


def test_correlation_graph_has_no_person_nodes(world: World) -> None:
    graph = world.service.correlation_graph(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        anchor=world.ctrl04_correlation,
        depth=1,
        now=world.tick(),
    )
    payload = graph.as_dict()
    assert payload["person_nodes"] == 0
    assert len(payload["nodes"]) <= MAX_GRAPH_NODES
    for node in payload["nodes"]:
        assert not set(node) & PERSON_IDENTIFIER_FIELDS


def test_action_chain_reconstructs_the_real_ctrl04_lifecycle(world: World) -> None:
    chain = world.service.action_chain(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        correlation_ref=world.ctrl04_correlation,
        now=world.tick(),
    )
    assert chain["correlation_ref"] == world.ctrl04_correlation
    assert chain["steps"]
    assert all(
        step["integrity"]["state"] == IntegrityState.VERIFIED.value for step in chain["steps"]
    )


# -- no secret and no person identifier anywhere -----------------------------

#: Secret *material*. A governed reference (`secret_ref`, `hsm_slot_ref`, a
#: vault path) is deliberately not material and is kept as a reference — that
#: is the accepted CTRL-04 redaction semantics, and CTRL-05 inherits it. What
#: must never appear is the secret itself.
SECRET_MARKERS = (
    "sk_live_",
    "hunter2",
    "BEGIN PRIVATE KEY",
    "AKIA",
)


def _assert_no_secret(text: str) -> None:
    lowered = text.lower()
    for marker in SECRET_MARKERS:
        assert marker.lower() not in lowered, f"secret marker {marker!r} reached the surface"


def test_no_secret_reaches_the_read_model(world: World) -> None:
    import json

    world.open_case()
    _assert_no_secret(json.dumps(world.service.read_model(now=world.tick())))


def test_no_secret_reaches_evidence_records(world: World) -> None:
    import json

    result = world.search(limit=MAX_QUERY_LIMIT)
    _assert_no_secret(json.dumps(result))


def test_no_secret_reaches_the_ctrl04_action_record(world: World) -> None:
    import json

    record = world.ctrl04_source.action_record(world.ctrl04_action_id)
    assert record is not None
    _assert_no_secret(json.dumps(record))


def test_no_person_identifier_field_reaches_any_record(world: World) -> None:
    result = world.search(limit=MAX_QUERY_LIMIT)
    for row in result["records"]:
        assert not set(row) & PERSON_IDENTIFIER_FIELDS
        assert not set(row.get("attributes") or {}) & PERSON_IDENTIFIER_FIELDS


def test_person_identifier_field_set_covers_the_obvious_names() -> None:
    for name in ("person_id", "member_id", "national_id", "email", "date_of_birth"):
        assert name in PERSON_IDENTIFIER_FIELDS


def test_no_secret_reaches_the_oversight_journal(world: World) -> None:
    import json

    world.open_case()
    _assert_no_secret(json.dumps(world.service.journal.export()))


# -- voting boundary ----------------------------------------------------------


def test_voting_status_is_reference_only(world: World) -> None:
    status = world.service.voting_verification_status(
        actor_ref="auditor", session_id="sess-auditor", scope=OPS_UNIT, now=world.tick()
    )
    assert status["voting_internal_access"] == "NONE"
    assert status["voting_control_path"] == "NONE"
    assert status["member_identifiers_exposed"] == 0
    for reference in status["interfaces"]:
        assert not set(reference) & PERSON_IDENTIFIER_FIELDS
        assert reference["voting_internal_access"] == "NONE"
        assert reference["control_path"] == "NONE"


def test_voting_reference_carrying_an_identity_is_refused_at_the_boundary(world: World) -> None:
    with pytest.raises(SourceUnavailable):
        world.voting.register(
            VotingVerificationReference(
                interface_id="voting-verifier-x",
                published_digest="1" * 64,
                verification_status="member_id=42",
                published_at="2026-09-03T00:00:00+00:00",
            )
        )


def test_voting_domain_evidence_is_not_visible(world: World) -> None:
    """The CTRL-04 world contains a voting-domain target; its evidence must
    never appear in an oversight result."""
    result = world.search(limit=MAX_QUERY_LIMIT)
    assert all(r["domain"] != "VOTING" for r in result["records"])


def test_there_is_no_route_into_the_voting_domain(world: World) -> None:
    assert not hasattr(world.service, "voting_ballots")
    assert not hasattr(world.service, "voting_members")
    assert not hasattr(world.voting, "ballots")
    assert not hasattr(world.voting, "members")


# -- the frontend is not an authority ----------------------------------------


def test_frontend_asserts_neither_integrity_nor_authority() -> None:
    assert FRONTEND_MAY_ASSERT_INTEGRITY is False
    assert FRONTEND_MAY_ASSERT_AUTHORITY is False


def test_unknown_evidence_reference_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.evidence(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            reference_key="CTRL-04:ctrl04-operations-console:does-not-exist",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.UNKNOWN_EVIDENCE.value


def test_unknown_plane_prefix_is_refused(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.evidence(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            reference_key="CTRL-99:stream:event",
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.UNKNOWN_EVIDENCE.value


def test_ctrl04_source_reports_an_absent_action_record_as_none(world: World) -> None:
    source = Ctrl04EvidenceSource(world.ctrl04)
    assert source.action_record("OPA-999999") is None


def test_a_secret_reference_is_kept_as_a_reference_while_material_is_redacted(
    world: World,
) -> None:
    """The distinction is the point: oversight must be able to *see that* a
    credential reference was involved without ever seeing the credential."""
    result = world.search(limit=MAX_QUERY_LIMIT)
    ctrl04 = [r for r in result["records"] if r["reference"]["plane"] == EvidencePlane.CTRL04.value]
    attributes: dict[str, object] = {}
    for row in ctrl04:
        attributes.update(row.get("attributes") or {})
    references = {k: v for k, v in attributes.items() if k.endswith("_ref")}
    assert references, "no governed reference survived into the oversight surface"
    for key, value in attributes.items():
        if "token" in key or "password" in key or "material" in key:
            assert value in {"[REDACTED]", "", None} or not str(value).startswith("sk_live_")


# -- obligations that only a direct probe can reach --------------------------


def test_a_mandate_whose_rule_version_was_lost_is_refused(world: World) -> None:
    """A mandate can only be *created* with a governing rule; one that lost it
    in storage must still be refused at resolve time."""
    mandate = world.service.mandate("MND-auditor")
    assert mandate is not None
    object.__setattr__(mandate, "rule_version", "")
    with pytest.raises(AuthorizationRefused) as exc:
        world.search()
    assert code(exc) == OversightRefusal.COMPETENCE_SOURCE_MISSING.value


def test_a_query_whose_limit_was_forced_past_the_bound_is_refused(world: World) -> None:
    from epd2_control_plane_service.oversight_console import EvidenceQuery

    query = EvidenceQuery(scope=OPS_UNIT, limit=10)
    object.__setattr__(query, "limit", MAX_QUERY_LIMIT + 1)
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.search(
            actor_ref="auditor",
            session_id="sess-auditor",
            query=query,
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.QUERY_LIMIT.value


def test_the_action_chain_scrubs_the_composed_ctrl04_record(world: World) -> None:
    """The CTRL-04 action record is the one place a provider token could reach
    the oversight surface; it is scrubbed on the way through."""
    import json

    chain = world.service.action_chain(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        correlation_ref=world.ctrl04_correlation,
        now=world.tick(),
    )
    text = json.dumps(chain)
    assert "composed_record" in chain or "action_record" in chain or chain["steps"]
    _assert_no_secret(text)
    assert "sk_live_" not in text


def test_a_person_identifier_can_never_enter_the_oversight_journal(world: World) -> None:
    with pytest.raises(AuthorizationRefused) as exc:
        world.service._record(
            now=world.tick(),
            actor_ref="auditor",
            authority_basis="ag-read@v1",
            act="AUDIT.EVIDENCE.SEARCH",
            scope_key=OPS_UNIT.key,
            object_ref="evidence",
            result="READ",
            reason_code="AUD_AUTHORIZED",
            correlation="probe",
            attributes={"member_id": "42"},
        )
    assert code(exc) == OversightRefusal.PERSON_IDENTIFIER.value


def test_a_secret_can_never_enter_the_oversight_journal(world: World) -> None:
    import json

    world.service._record(
        now=world.tick(),
        actor_ref="auditor",
        authority_basis="ag-read@v1",
        act="AUDIT.EVIDENCE.SEARCH",
        scope_key=OPS_UNIT.key,
        object_ref="evidence",
        result="READ",
        reason_code="AUD_AUTHORIZED",
        correlation="probe",
        attributes={"api_token": "sk_live_leak", "note": "value sk_live_leak inline"},
    )
    text = json.dumps(world.service.journal.export())
    assert "sk_live_leak" not in text
    assert "evidence_redacted_fields" in text


def test_a_real_voting_domain_envelope_exists_and_is_filtered(world: World) -> None:
    """The boundary is exercised against a real record, not a hypothetical
    one: CTRL-04 journaled a refusal on a voting-domain target."""
    envelopes, _unavailable = world.service._all_envelopes()
    voting = [e for e in envelopes if e.domain.value == "VOTING"]
    assert voting, "the world must contain real voting-domain evidence"
    assert world.voting_domain_refs == frozenset({"svc-voting-tally"})
    visible = world.search(limit=MAX_QUERY_LIMIT)
    keys = {r["reference"]["key"] for r in visible["records"]}
    assert not keys & {e.reference.key for e in voting}


def test_a_voting_domain_record_cannot_be_opened_or_reviewed(world: World) -> None:
    envelopes, _unavailable = world.service._all_envelopes()
    voting = next(e for e in envelopes if e.domain.value == "VOTING")
    with pytest.raises(AuthorizationRefused) as exc:
        world.service.evidence(
            actor_ref="auditor",
            session_id="sess-auditor",
            scope=OPS_UNIT,
            reference_key=voting.reference.key,
            now=world.tick(),
        )
    assert code(exc) == OversightRefusal.VOTING_BOUNDARY.value


def test_a_correlation_graph_anchor_must_be_exact(world: World) -> None:
    for anchor in ("", "*", "ALL", "GLOBAL", "ANY"):
        with pytest.raises(AuthorizationRefused) as exc:
            world.service.correlation_graph(
                actor_ref="auditor",
                session_id="sess-auditor",
                scope=OPS_UNIT,
                anchor=anchor,
                depth=1,
                now=world.tick(),
            )
        assert code(exc) == OversightRefusal.UNBOUNDED_QUERY.value


def test_a_correlation_graph_may_not_be_anchored_on_a_person(world: World) -> None:
    for anchor in ("member_id", "person_id", "national_id", "email"):
        with pytest.raises(AuthorizationRefused) as exc:
            world.service.correlation_graph(
                actor_ref="auditor",
                session_id="sess-auditor",
                scope=OPS_UNIT,
                anchor=anchor,
                depth=1,
                now=world.tick(),
            )
        assert code(exc) == OversightRefusal.PERSON_IDENTIFIER.value


def test_a_plane_restricted_query_returns_only_that_plane(world: World) -> None:
    result = world.search(planes=frozenset({EvidencePlane.CTRL02}), limit=MAX_QUERY_LIMIT)
    planes = {r["reference"]["plane"] for r in result["records"]}
    assert planes == {EvidencePlane.CTRL02.value}
    assert result["matched"] > 0


def test_integrity_verification_is_the_governed_path(world: World) -> None:
    """The verdict must come from re-derivation, not from the record's own
    claim about itself."""
    ref = world.references()[0]
    verdict = world.service.verify_evidence(
        actor_ref="auditor",
        session_id="sess-auditor",
        scope=OPS_UNIT,
        reference_key=ref,
        now=world.tick(),
    )
    assert verdict["verified_by"] == "CTRL-05 independent re-derivation"
    assert verdict["detail"] != "integrity verification disabled"

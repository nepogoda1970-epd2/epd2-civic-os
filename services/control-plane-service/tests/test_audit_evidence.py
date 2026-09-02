"""W10 — audit and evidence, and the privacy boundary around it."""

from __future__ import annotations

import itertools

import pytest
from _control_plane_builders import LAND_BE, T0, World, run_governed_flow
from epd2_control_plane_service.audit import (
    GENESIS_PREVIOUS_HASH,
    EvidenceJournal,
    screen_attributes,
)
from epd2_control_plane_service.domain import VOTING_DOMAIN_FORBIDDEN_FIELDS
from epd2_control_plane_service.exceptions import (
    AuthorizationRefused,
    EvidenceIntegrityError,
    PrivacyBoundaryViolation,
)
from epd2_control_plane_service.mutations import (
    _overwrite_history,
    _rechain_history,
    _remove_audit_event,
    _truncate_newest_event,
)
from epd2_control_plane_service.reference_world import build_world
from epd2_control_plane_service.verification import recompute_chain

REQUIRED_FIELDS = (
    "actor_ref",
    "authority_basis",
    "action_id",
    "scope_key",
    "object_ref",
    "occurred_at",
    "result",
    "reason_code",
    "approval_refs",
    "correlation_ref",
)


def test_every_consequential_act_emits_a_complete_record(world: World) -> None:
    run_governed_flow(
        world,
        request_id="req-audit-1",
        action_id="AUTH.ASSIGN",
        requester="p.land.be.chair",
        approvers=("p.land.be.deputy", "p.land.be.secretary"),
        executor="p.land.be.chair",
        scope=LAND_BE,
    )
    executed = world.journal.find(action_id="AUTH.ASSIGN", result="EXECUTED")
    assert len(executed) == 1
    payload = executed[0].hashable()
    for field in REQUIRED_FIELDS:
        assert field in payload and payload[field] not in (None, ""), field
    assert executed[0].approval_refs == ("a.land.be.deputy", "a.land.be.secretary")


def test_refusals_are_recorded_with_their_reason(world: World) -> None:
    with pytest.raises(AuthorizationRefused):
        world.plane.submit_request(
            request_id="req-audit-2",
            action_id="AUTH.ASSIGN",
            principal_id="p.ordinary.member",
            session_id="s.p.ordinary.member",
            scope=LAND_BE,
            object_ref="authority.target",
            purpose="refusal evidence",
            moment=T0,
        )
    refusals = world.journal.find(result="REFUSED")
    assert refusals and refusals[-1].reason_code == "CTRL_NO_AUTHORITY"


def test_chain_starts_at_genesis_and_links_forward(world: World) -> None:
    run_governed_flow(
        world,
        request_id="req-audit-3",
        action_id="AUTH.ASSIGN",
        requester="p.land.be.chair",
        approvers=("p.land.be.deputy", "p.land.be.secretary"),
        executor="p.land.be.chair",
        scope=LAND_BE,
    )
    records = world.journal.records()
    assert records[0].previous_event_hash == GENESIS_PREVIOUS_HASH
    for earlier, later in itertools.pairwise(records):
        assert later.previous_event_hash == earlier.event_hash
    world.journal.verify()


def test_every_tampering_shape_is_detected(world: World) -> None:
    """Four shapes, including the two an unanchored chain walk cannot see:
    deleting the newest record, and rewriting a record while recomputing every
    hash forward."""
    for index in range(3):
        run_governed_flow(
            world,
            request_id=f"req-audit-4-{index}",
            action_id="AUTH.ASSIGN",
            requester="p.land.be.chair",
            approvers=("p.land.be.deputy", "p.land.be.secretary"),
            executor="p.land.be.chair",
            scope=LAND_BE,
        )
    world.journal.verify()
    anchor = world.journal.anchor()
    assert anchor == (len(world.journal), world.journal.head_hash())

    for shape, tamper in (
        ("interior deletion", _remove_audit_event),
        ("tail truncation", _truncate_newest_event),
        ("naive rewrite", _overwrite_history),
        ("re-chained rewrite", _rechain_history),
    ):
        fresh = build_world()
        run_governed_flow(
            fresh,
            request_id="req-audit-shape",
            action_id="AUTH.ASSIGN",
            requester="p.land.be.chair",
            approvers=("p.land.be.deputy", "p.land.be.secretary"),
            executor="p.land.be.chair",
            scope=LAND_BE,
        )
        fresh_anchor = fresh.journal.anchor()
        tamper(fresh)
        intact, _detail = recompute_chain(fresh.journal.records(), fresh_anchor)
        assert not intact, f"{shape} was not detected"
        with pytest.raises(EvidenceIntegrityError):
            fresh.journal.verify()


def test_journal_exposes_no_mutation_surface_at_all() -> None:
    """Not only is there no public update or delete — there is no private one
    either. The tampering helpers live in the mutation corpus, which is the
    attacker model, not in the evidence module."""
    public = {name for name in dir(EvidenceJournal) if not name.startswith("_")}
    assert public == {"append", "anchor", "records", "head_hash", "find", "verify", "export"}
    private = {name for name in dir(EvidenceJournal) if name.startswith("_tamper")}
    assert private == set()


@pytest.mark.parametrize("field", sorted(VOTING_DOMAIN_FORBIDDEN_FIELDS))
def test_no_voting_linkable_identifier_may_be_written(field: str) -> None:
    with pytest.raises(PrivacyBoundaryViolation):
        screen_attributes({field: "x"})


@pytest.mark.parametrize(
    "field",
    [
        "private_key",
        "service_secret_value",
        "user_password",
        "wrapping_seed_material",
        "ballot_plaintext",
    ],
)
def test_no_secret_material_may_be_written(field: str) -> None:
    with pytest.raises(PrivacyBoundaryViolation):
        screen_attributes({field: "value"})


def test_raw_secret_values_are_refused_whatever_the_field_name() -> None:
    with pytest.raises(PrivacyBoundaryViolation):
        screen_attributes({"note": "-----BEGIN PRIVATE KEY-----"})


def test_governed_references_remain_permitted() -> None:
    screen_attributes(
        {
            "key_reference_id": "key.platform.signing.1",
            "decision_ref": "BESCHLUSS-2026-001",
            "evidence_ref": "EVID-1",
        }
    )


def test_oversized_attributes_are_refused() -> None:
    with pytest.raises(PrivacyBoundaryViolation, match="minimization budget"):
        screen_attributes({"payload": "x" * 600})

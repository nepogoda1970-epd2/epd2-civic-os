"""Fault-injection matrix (PACK-16D §43).

Eleven named fault points, each armed in turn, each asserting what must be
true after the fault: either the transaction rolled back completely, or the
step was outside the transaction and the state it left is recoverable.

The injector is test-only by construction: production code depends on the
``hooks.FaultHook`` protocol and never imports this module, and a hook can
only arrive by being passed explicitly into a call.
"""

from __future__ import annotations

import pytest

from epd2_voting_service.reference.casting.transactions import (
    dispatch_outbox,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.election_record.builder import export_record
from epd2_voting_service.reference.publication.bulletin_board import EntryType
from epd2_voting_service.reference.publication.outbox import ObligationState
from epd2_voting_service.reference.testing.faults import (
    FaultInjector,
    FaultPoint,
    InjectedFault,
    armed,
)
from epd2_voting_service.reference.testing.fixtures import fixture_a
from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot

#: The fault points that occur inside a submission transaction. Every one
#: of them must leave the store byte-identical to its pre-call state.
TRANSACTIONAL_POINTS = [
    FaultPoint.AFTER_CAPABILITY_VALIDATION,
    FaultPoint.AFTER_PROOF_VALIDATION,
    FaultPoint.AFTER_SLOT_RESERVATION,
    FaultPoint.AFTER_BALLOT_PERSISTENCE,
    FaultPoint.AFTER_ENTITLEMENT_MUTATION,
    FaultPoint.BEFORE_TRANSACTION_COMMIT,
]


def _snapshot(fixture: object) -> tuple[object, ...]:
    store = fixture.store  # type: ignore[attr-defined]
    return (
        {k: repr(v) for k, v in store.continuations.items()},
        dict(store.accepted_ballots),
        dict(store.spoiled_ballots),
        {k: repr(v) for k, v in store.reservations.items()},
        dict(store.slot_owner),
        {k: repr(v) for k, v in store.obligations.items()},
        [repr(r) for r in store.outbox.rows],
        {k: repr(v) for k, v in store.idempotency.items()},
    )


def test_all_eleven_fault_points_are_declared() -> None:
    assert len(list(FaultPoint)) == 11
    assert {p.value for p in FaultPoint} == {
        "after_capability_validation",
        "after_proof_validation",
        "after_slot_reservation",
        "after_ballot_persistence",
        "after_entitlement_mutation",
        "before_transaction_commit",
        "after_commit",
        "before_outbox_publish",
        "after_board_append",
        "before_checkpoint_signing",
        "during_record_export",
    }


@pytest.mark.parametrize("point", TRANSACTIONAL_POINTS)
def test_cast_rolls_back_completely_at_every_transactional_point(
    point: FaultPoint,
) -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-cast")
    before = _snapshot(fixture)
    with armed(point) as injector, pytest.raises(InjectedFault):
        submit_cast_ballot(
            fixture.store,
            fixture.runtime,
            fixture.capabilities[0],
            envelope,
            "k",
            fault_hook=injector,
        )
    assert _snapshot(fixture) == before, f"state leaked past {point.value}"

    # recovery: the same request now succeeds
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k"
    )
    assert result.counted is True


@pytest.mark.parametrize("point", TRANSACTIONAL_POINTS)
def test_public_challenge_rolls_back_completely(point: FaultPoint) -> None:
    fixture = fixture_a()
    envelope, opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-chal")
    before = _snapshot(fixture)
    injector = FaultInjector()
    injector.arm(point)
    with pytest.raises(InjectedFault):
        submit_public_challenge(
            fixture.store,
            fixture.runtime,
            fixture.capabilities[0],
            envelope,
            opening,
            "k",
            fault_hook=injector,
        )
    assert _snapshot(fixture) == before

    result = submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, opening, "k"
    )
    assert result.counted is False
    # the cast entitlement survived both the fault and the retry
    assert fixture.store.continuations[fixture.capabilities[0]].cast_entitlement_available is True


def test_before_outbox_publish_leaves_the_obligation_pending() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-outbox")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    with armed(FaultPoint.BEFORE_OUTBOX_PUBLISH) as injector, pytest.raises(InjectedFault):
        dispatch_outbox(fixture.store, fault_hook=injector)
    assert len(fixture.store.outbox.pending()) == 1
    assert len(dispatch_outbox(fixture.store)) == 1


def test_after_commit_leaves_the_obligation_dispatched_and_not_repeated() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-commit")
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k"
    )
    with armed(FaultPoint.AFTER_COMMIT) as injector, pytest.raises(InjectedFault):
        dispatch_outbox(fixture.store, fault_hook=injector)
    states = {r.publication_obligation_id: r.state for r in fixture.store.outbox.rows}
    assert states[result.publication_obligation_id] is ObligationState.DISPATCHED
    assert dispatch_outbox(fixture.store) == []


def test_after_board_append_keeps_the_entry_and_the_tree_consistent() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    before_root = board.root()
    with armed(FaultPoint.AFTER_BOARD_APPEND) as injector, pytest.raises(InjectedFault):
        board.append(EntryType.PARAMETER_SET, b"p", fault_hook=injector)

    # append is not transactional: the entry is durable and the tree grew.
    # What must hold is that the board stays internally consistent and the
    # next checkpoint covers the entry rather than hiding it.
    assert len(board.entries) == 2
    assert board.root() != before_root
    checkpoint = board.publish_checkpoint()
    assert checkpoint.tree_size == 2
    assert checkpoint.root == board.root()


def test_before_checkpoint_signing_publishes_no_checkpoint() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    with armed(FaultPoint.BEFORE_CHECKPOINT_SIGNING) as injector, pytest.raises(InjectedFault):
        board.publish_checkpoint(fault_hook=injector)
    assert board.checkpoints == [], "an unsigned checkpoint was published"
    # retry produces exactly one checkpoint, chained from genesis
    checkpoint = board.publish_checkpoint()
    assert checkpoint.checkpoint_sequence == 0
    assert checkpoint.previous_checkpoint_hash == b"\x00" * 32


def test_during_record_export_loses_nothing() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-export")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    closed = close_and_build(fixture, [envelope], [])
    with armed(FaultPoint.DURING_RECORD_EXPORT) as injector, pytest.raises(InjectedFault):
        export_record(closed.record, fault_hook=injector)
    # export is pure: retrying produces the same bytes as if nothing happened
    assert export_record(closed.record) == closed.record.canonical_bytes()


def test_an_unarmed_injector_is_transparent() -> None:
    """A hook that is present but unarmed must not change any outcome."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"fi-noop")
    result = submit_cast_ballot(
        fixture.store,
        fixture.runtime,
        fixture.capabilities[0],
        envelope,
        "k",
        fault_hook=FaultInjector(),
    )
    assert result.counted is True


def test_a_fault_point_fires_once_and_disarms() -> None:
    injector = FaultInjector()
    injector.arm(FaultPoint.AFTER_COMMIT)
    with pytest.raises(InjectedFault):
        injector.trip("after_commit")
    injector.trip("after_commit")  # no longer armed


def test_production_modules_do_not_import_the_injector() -> None:
    """The test-only guarantee, checked with `ast` rather than by substring."""
    import ast
    import pathlib

    import epd2_voting_service.reference as reference_package

    root = pathlib.Path(reference_package.__file__).parent
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "testing" in path.relative_to(root).parts:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = {alias.name for alias in node.names}
                if (node.module or "").endswith("testing.faults") or names & {
                    "FaultInjector",
                    "InjectedFault",
                    "FaultPoint",
                }:
                    offenders.append(f"{path.relative_to(root)}:{node.lineno}")
            elif isinstance(node, ast.Import):
                offenders.extend(
                    f"{path.relative_to(root)}:{node.lineno}"
                    for alias in node.names
                    if alias.name.endswith("testing.faults")
                )
    assert offenders == [], f"production modules import the test injector: {offenders}"


def test_the_only_other_fault_point_call_site_is_covered() -> None:
    """Every `trip()` call site in production code is reachable by a test.

    `before_outbox_publish` used to have a second call site inside
    `seal_batch`, which no test armed and which was mislabelled anyway -
    sealing is not an outbox publish. That call site was removed rather
    than given a test it did not deserve. This guard fails if a new
    unreviewed one appears.
    """
    import ast
    import pathlib

    import epd2_voting_service.reference as reference_package

    root = pathlib.Path(reference_package.__file__).parent
    sites: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*.py")):
        if "testing" in path.relative_to(root).parts or path.name == "hooks.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "trip"
                and len(node.args) == 2
                and isinstance(node.args[1], ast.Constant)
            ):
                point = node.args[1].value
                assert isinstance(point, str)
                sites.append((str(path.relative_to(root)), point))

    named = {point for _, point in sites}
    assert named == {p.value for p in FaultPoint}, (
        f"call sites cover {sorted(named)}, declared points are "
        f"{sorted(p.value for p in FaultPoint)}"
    )
    by_point: dict[str, int] = {}
    for _, point in sites:
        by_point[point] = by_point.get(point, 0) + 1
    # each point is tripped from exactly the places this round reviewed
    assert by_point["before_outbox_publish"] == 1
    assert by_point["after_capability_validation"] == 2  # cast and challenge

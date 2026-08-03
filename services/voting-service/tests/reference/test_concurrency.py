"""Concurrency and race tests (PACK-16D §42).

**Limitation, stated up front.** These tests exercise real OS threads
against the reference store, whose transaction boundary is a re-entrant
lock. That proves the *logic* is race-free under the serialisation the
store provides. It does **not** prove anything about a production
datastore: there, the same invariants must come from row-level locking or
a serialisable isolation level, and demonstrating that is a PACK-17
obligation. A green run here is evidence about this implementation, not
about a deployment.

A barrier is used so the threads genuinely contend rather than running one
after another; each test asserts the §42 expectations directly.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import pytest

from epd2_voting_service.reference.casting.continuation import (
    CastEntitlementExhaustedError,
    PublicChallengeEntitlementExhaustedError,
)
from epd2_voting_service.reference.casting.idempotency import IdempotencyConflictError
from epd2_voting_service.reference.casting.store import CastCapacityUnavailableError
from epd2_voting_service.reference.casting.transactions import (
    Outcome,
    dispatch_outbox,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.publication.outbox import ObligationState
from epd2_voting_service.reference.publication.sealing import seal_batch
from epd2_voting_service.reference.testing.faults import FaultInjector, FaultPoint, InjectedFault
from epd2_voting_service.reference.testing.fixtures import deterministic_source, fixture_a
from epd2_voting_service.reference.testing.scenarios import make_ballot

REPEATS = 12


def _race(calls: list[Callable[[], Any]]) -> list[tuple[Any, BaseException | None]]:
    """Run every call on its own thread, released simultaneously."""
    barrier = threading.Barrier(len(calls))
    results: list[tuple[Any, BaseException | None]] = [(None, None)] * len(calls)

    def runner(index: int) -> None:
        barrier.wait()
        try:
            results[index] = (calls[index](), None)
        except BaseException as exc:  # the race outcome, not an error to hide
            results[index] = (None, exc)

    threads = [threading.Thread(target=runner, args=(i,)) for i in range(len(calls))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive(), "a racing thread deadlocked"
    return results


def _split(
    results: list[tuple[Any, BaseException | None]],
) -> tuple[list[Any], list[BaseException]]:
    accepted = [value for value, error in results if error is None]
    failed = [error for _, error in results if error is not None]
    return accepted, failed


# -- C-01 two simultaneous cast requests on one capability ---------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c01_two_simultaneous_casts_on_one_capability(repeat: int) -> None:
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c01-a-{repeat}".encode())
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, f"c01-b-{repeat}".encode())

    accepted, failed = _split(
        _race(
            [
                lambda: submit_cast_ballot(fixture.store, fixture.runtime, capability, first, "k1"),
                lambda: submit_cast_ballot(
                    fixture.store, fixture.runtime, capability, second, "k2"
                ),
            ]
        )
    )
    assert len(accepted) == 1, "double acceptance"
    assert all(isinstance(e, CastEntitlementExhaustedError) for e in failed)
    assert len(fixture.store.accepted_ballots) == 1
    assert fixture.store.continuations[capability].capability_consumed is True
    committed = [r for r in fixture.store.reservations.values() if r.committed]
    assert len(committed) == 1
    assert len(fixture.store.slot_owner) == 1, "an orphan slot survived"


# -- C-02 two simultaneous public challenges -----------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c02_two_simultaneous_public_challenges(repeat: int) -> None:
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, first_open = make_ballot(fixture, {"c1": ("opt-1",)}, f"c02-a-{repeat}".encode())
    second, second_open = make_ballot(fixture, {"c1": ("opt-2",)}, f"c02-b-{repeat}".encode())

    accepted, failed = _split(
        _race(
            [
                lambda: submit_public_challenge(
                    fixture.store, fixture.runtime, capability, first, first_open, "k1"
                ),
                lambda: submit_public_challenge(
                    fixture.store, fixture.runtime, capability, second, second_open, "k2"
                ),
            ]
        )
    )
    assert len(accepted) == 1
    assert all(isinstance(e, PublicChallengeEntitlementExhaustedError) for e in failed)
    assert len(fixture.store.spoiled_ballots) == 1
    state = fixture.store.continuations[capability]
    assert state.public_challenge_entitlement_available is False
    assert state.cast_entitlement_available is True


# -- C-03 cast and public challenge concurrently -------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c03_cast_and_public_challenge_concurrently(repeat: int) -> None:
    """Both are entitled at the start, but the outcome is order-dependent.

    A final cast consumes the capability outright: ``consume_for_cast()``
    clears the challenge entitlement as well, because a public challenge
    published *after* the ballot it was meant to test is not evidence of
    anything. So if the cast wins the race the challenge is refused, while
    if the challenge wins both succeed. What must hold in **either** order
    is that the cast is accepted exactly once, that no submission takes a
    slot reserved for the other class, and that nothing is left half-done.

    An earlier version of this test asserted that both always succeed. It
    passed most runs and failed roughly one in thirty - the assertion was
    wrong, not the implementation.
    """
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    cast, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c03-cast-{repeat}".encode())
    challenge, opening = make_ballot(fixture, {"c1": ("opt-2",)}, f"c03-chal-{repeat}".encode())

    results = _race(
        [
            lambda: submit_cast_ballot(fixture.store, fixture.runtime, capability, cast, "k-cast"),
            lambda: submit_public_challenge(
                fixture.store, fixture.runtime, capability, challenge, opening, "k-chal"
            ),
        ]
    )
    (cast_result, cast_error), (challenge_result, challenge_error) = results

    # The cast is entitled from the start and nothing can take that away:
    # a challenge does not consume the cast entitlement.
    assert cast_error is None, cast_error
    assert cast_result.counted is True
    assert fixture.store.accepted_ballots.keys() == {cast.ballot_id}

    state = fixture.store.continuations[capability]
    assert state.capability_consumed is True
    assert state.public_challenge_entitlement_available is False

    by_reference = {r.submission_reference: r for r in fixture.store.reservations.values()}
    cast_leaf = by_reference[cast.ballot_id].leaf_index
    assert cast_leaf < fixture.plan.cast_reserved_per_batch

    if challenge_error is None:
        # The challenge won the race: it published, and took a slot that is
        # not cast-reserved (`TC-75`).
        assert challenge_result.counted is False
        assert fixture.store.spoiled_ballots.keys() == {challenge.ballot_id}
        challenge_leaf = by_reference[challenge.ballot_id].leaf_index
        assert challenge_leaf != cast_leaf
        assert challenge_leaf >= fixture.plan.cast_reserved_per_batch
    else:
        # The cast won: the capability was already consumed, so the
        # challenge fails closed and leaves nothing behind.
        assert isinstance(challenge_error, PublicChallengeEntitlementExhaustedError)
        assert fixture.store.spoiled_ballots == {}
        assert challenge.ballot_id not in by_reference
        assert len(fixture.store.slot_owner) == 1


# -- C-04 same idempotency key concurrently ------------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c04_same_idempotency_key_concurrently(repeat: int) -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c04-{repeat}".encode())
    other, _ = make_ballot(fixture, {"c1": ("opt-2",)}, f"c04-other-{repeat}".encode())

    results = _race(
        [
            lambda: submit_cast_ballot(
                fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "same"
            ),
            lambda: submit_cast_ballot(
                fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "same"
            ),
            lambda: submit_cast_ballot(
                fixture.store, fixture.runtime, fixture.capabilities[1], other, "same"
            ),
        ]
    )
    accepted, failed = _split(results)
    outcomes = [r.outcome for r in accepted]
    assert outcomes.count(Outcome.ACCEPTED) == 1
    # the conflicting third request must fail, never silently replay
    assert any(
        isinstance(e, IdempotencyConflictError | CastEntitlementExhaustedError) for e in failed
    ), failed
    assert len(fixture.store.accepted_ballots) == 1


# -- C-05 two reservations for the same slot -----------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c05_two_reservations_for_the_same_slot(repeat: int) -> None:
    """Fixture C has exactly one cast-reserved slot and no shared reserve."""
    from epd2_voting_service.reference.testing.fixtures import fixture_c

    fixture = fixture_c()
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c05-a-{repeat}".encode())
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, f"c05-b-{repeat}".encode())

    accepted, failed = _split(
        _race(
            [
                lambda: submit_cast_ballot(
                    fixture.store, fixture.runtime, fixture.capabilities[0], first, "k1"
                ),
                lambda: submit_cast_ballot(
                    fixture.store, fixture.runtime, fixture.capabilities[1], second, "k2"
                ),
            ]
        )
    )
    assert len(accepted) == 1
    assert all(isinstance(e, CastCapacityUnavailableError) for e in failed), failed
    assert len(fixture.store.slot_owner) == 1
    # the loser's capability is untouched: a lost race is not a spent vote
    losers = [
        c
        for c in fixture.capabilities[:2]
        if fixture.store.continuations[c].cast_entitlement_available
    ]
    assert len(losers) == 1


# -- C-06 batch sealing during reservation -------------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c06_batch_sealing_during_reservation(repeat: int) -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c06-{repeat}".encode())
    sealed: list[Any] = []

    def do_seal() -> None:
        sealed.append(
            seal_batch(
                fixture.store,
                election_context_id=fixture.manifest.election_context_id,
                batch_sequence=0,
                batch_window_id="w0",
                capacity=fixture.runtime.batch_capacity,
                capacity_profile_id="test",
                source=deterministic_source(f"c06-seal-{repeat}".encode()),
            )
        )

    _race(
        [
            lambda: submit_cast_ballot(
                fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1"
            ),
            do_seal,
        ]
    )

    batch, opening = sealed[0]
    # whichever order the race resolved in, the batch is exactly full and
    # every real leaf recomputes against the published root
    assert len(opening.leaves) == batch.capacity
    assert opening.recompute_root() == batch.commitment_root
    references = [o.artifact_reference for o in opening.openings if o.artifact_reference]
    assert len(references) in (0, 1)
    assert len(references) == len(set(references))


# -- C-07 publication worker retry ---------------------------------------


@pytest.mark.parametrize("repeat", range(REPEATS))
def test_c07_publication_worker_retry(repeat: int) -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"c07-{repeat}".encode())
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1"
    )
    dispatched = _race([lambda: dispatch_outbox(fixture.store) for _ in range(4)])
    rows = [row for value, _ in dispatched if value for row in value]
    ids = [r.publication_obligation_id for r in rows]
    assert ids.count(result.publication_obligation_id) == 1, "obligation dispatched twice"
    assert fixture.store.outbox.pending() == []


# -- C-08 crash after persistence before outbox dispatch -----------------


def test_c08_crash_after_persistence_before_dispatch() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"c08")
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1"
    )
    injector = FaultInjector()
    injector.arm(FaultPoint.BEFORE_OUTBOX_PUBLISH)
    with pytest.raises(InjectedFault):
        dispatch_outbox(fixture.store, fault_hook=injector)

    # the obligation is not lost
    assert [r.publication_obligation_id for r in fixture.store.outbox.pending()] == [
        result.publication_obligation_id
    ]
    assert envelope.ballot_id in fixture.store.accepted_ballots
    recovered = dispatch_outbox(fixture.store)
    assert len(recovered) == 1


# -- C-09 crash after dispatch before acknowledgement --------------------


def test_c09_crash_after_dispatch_before_acknowledgement() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"c09")
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1"
    )
    injector = FaultInjector()
    injector.arm(FaultPoint.AFTER_COMMIT)
    with pytest.raises(InjectedFault):
        dispatch_outbox(fixture.store, fault_hook=injector)

    # DISPATCHED but never acknowledged: at-least-once, and the row is not
    # re-dispatched, so the board never sees a duplicate entry
    rows = {r.publication_obligation_id: r.state for r in fixture.store.outbox.rows}
    assert rows[result.publication_obligation_id] is ObligationState.DISPATCHED
    assert dispatch_outbox(fixture.store) == []
    assert len(fixture.store.outbox.rows) == 1


def test_no_capability_to_ballot_leakage_in_any_persisted_row() -> None:
    """§42's fifth expectation, asserted over every row the race can create."""
    fixture = fixture_a()
    envelope, opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"leak-chal")
    cast, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"leak-cast")
    capability = fixture.capabilities[0]
    submit_public_challenge(fixture.store, fixture.runtime, capability, envelope, opening, "k1")
    submit_cast_ballot(fixture.store, fixture.runtime, capability, cast, "k2")

    for reservation in fixture.store.reservations.values():
        assert capability not in str(reservation)
    for obligation in fixture.store.obligations.values():
        assert capability not in str(obligation)
    for row in fixture.store.outbox.rows:
        assert capability not in str(row)
    for state in fixture.store.continuations.values():
        assert cast.ballot_id not in str(state)
        assert envelope.ballot_id not in str(state)
    for key, value in fixture.store.idempotency.items():
        assert capability not in str(key)
        assert capability not in str(value)

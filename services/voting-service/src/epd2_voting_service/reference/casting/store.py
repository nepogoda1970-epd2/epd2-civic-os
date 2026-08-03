"""Reference transactional store (PACK-16D §24).

An in-memory store guarded by a single reentrant lock, with an explicit
transaction scope that rolls back **every** mutation on any exception.
This is the reference persistence engine: it demonstrates atomicity,
uniqueness, idempotency, compare-and-set and reservation expiry without
introducing a database dependency the repository does not already have.

The two halves of the acceptance boundary live in **separate maps with no
shared key** (`DM-10`): `continuations` is keyed by capability reference
and holds no ballot reference; `accepted_ballots` is keyed by ballot id
and holds no capability reference.
"""

from __future__ import annotations

import copy
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from epd2_voting_service.reference.casting.continuation import ContinuationState
from epd2_voting_service.reference.casting.idempotency import IdempotencyRecord
from epd2_voting_service.reference.publication.capacity import SlotClass
from epd2_voting_service.reference.publication.outbox import Outbox, PublicationObligation


class ReservationUnavailableError(RuntimeError):
    """Base class. Never raised directly.

    A cast and a public challenge exhaust different capacity and the
    PACK-16C catalogue gives them different reason codes, so they get
    different exception types. Catching the base class is still possible
    where the distinction genuinely does not matter.
    """

    reason_code = "RESERVATION_UNAVAILABLE"


class CastCapacityUnavailableError(ReservationUnavailableError):
    reason_code = "SUBMISSION_CAST_CAPACITY_UNAVAILABLE"


class PublicChallengeReservationUnavailableError(ReservationUnavailableError):
    reason_code = "CHALLENGE_PUBLIC_RESERVATION_UNAVAILABLE"


class DuplicateArtifactError(ValueError):
    reason_code = "ACCEPTANCE_DUPLICATE_BALLOT_ID"


@dataclass(frozen=True, slots=True)
class LeafReservation:
    """`DM-21`: anonymous, bound to a submission in flight, never to a
    capability."""

    reservation_id: str
    batch_sequence: int
    leaf_index: int
    slot_class: SlotClass
    submission_reference: str
    committed: bool = False


@dataclass
class ReferenceStore:
    """Everything the reference implementation persists."""

    continuations: dict[str, ContinuationState] = field(default_factory=dict)
    idempotency: dict[tuple[str, str, str], IdempotencyRecord] = field(default_factory=dict)
    accepted_ballots: dict[str, bytes] = field(default_factory=dict)
    spoiled_ballots: dict[str, bytes] = field(default_factory=dict)
    reservations: dict[str, LeafReservation] = field(default_factory=dict)
    slot_owner: dict[tuple[int, int], str] = field(default_factory=dict)
    obligations: dict[str, PublicationObligation] = field(default_factory=dict)
    outbox: Outbox = field(default_factory=Outbox)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @contextmanager
    def transaction(self) -> Iterator[ReferenceStore]:
        """All-or-nothing. A snapshot is restored on any exception."""
        with self._lock:
            snapshot = (
                dict(self.continuations),
                dict(self.idempotency),
                dict(self.accepted_ballots),
                dict(self.spoiled_ballots),
                dict(self.reservations),
                dict(self.slot_owner),
                dict(self.obligations),
                copy.deepcopy(self.outbox.rows),
            )
            try:
                yield self
            except BaseException:
                (
                    self.continuations,
                    self.idempotency,
                    self.accepted_ballots,
                    self.spoiled_ballots,
                    self.reservations,
                    self.slot_owner,
                    self.obligations,
                    self.outbox.rows,
                ) = (
                    dict(snapshot[0]),
                    dict(snapshot[1]),
                    dict(snapshot[2]),
                    dict(snapshot[3]),
                    dict(snapshot[4]),
                    dict(snapshot[5]),
                    dict(snapshot[6]),
                    list(snapshot[7]),
                )
                raise

    def reserve_leaf(
        self,
        *,
        reservation_id: str,
        batch_sequence: int,
        candidate_slots: list[tuple[int, SlotClass]],
        submission_reference: str,
        requested_class: SlotClass,
    ) -> LeafReservation:
        """Compare-and-set over `(batch_sequence, leaf_index)`.

        Reservation precedes durable acceptance; there is no path that
        accepts an artefact and then looks for a slot. ``requested_class``
        selects the reason code on exhaustion and is not used to widen the
        candidate list - the caller has already decided which slots this
        submission may take.
        """
        for leaf_index, slot_class in candidate_slots:
            key = (batch_sequence, leaf_index)
            if key in self.slot_owner:
                continue
            self.slot_owner[key] = reservation_id
            reservation = LeafReservation(
                reservation_id=reservation_id,
                batch_sequence=batch_sequence,
                leaf_index=leaf_index,
                slot_class=slot_class,
                submission_reference=submission_reference,
            )
            self.reservations[reservation_id] = reservation
            return reservation
        if requested_class is SlotClass.CAST_RESERVED:
            raise CastCapacityUnavailableError(
                "no cast-eligible leaf slot is available in this batch"
            )
        raise PublicChallengeReservationUnavailableError(
            "no challenge-eligible leaf slot is available in this batch"
        )

    def release_reservation(self, reservation_id: str) -> None:
        reservation = self.reservations.pop(reservation_id, None)
        if reservation is None:
            return
        key = (reservation.batch_sequence, reservation.leaf_index)
        if self.slot_owner.get(key) == reservation_id:
            del self.slot_owner[key]

    def commit_reservation(self, reservation_id: str) -> LeafReservation:
        reservation = self.reservations[reservation_id]
        committed = LeafReservation(
            reservation_id=reservation.reservation_id,
            batch_sequence=reservation.batch_sequence,
            leaf_index=reservation.leaf_index,
            slot_class=reservation.slot_class,
            submission_reference=reservation.submission_reference,
            committed=True,
        )
        self.reservations[reservation_id] = committed
        return committed

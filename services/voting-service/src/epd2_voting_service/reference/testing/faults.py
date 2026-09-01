"""Controlled fault injection (PACK-16D §43). Test-only."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum


class FaultPoint(StrEnum):
    AFTER_CAPABILITY_VALIDATION = "after_capability_validation"
    AFTER_PROOF_VALIDATION = "after_proof_validation"
    AFTER_SLOT_RESERVATION = "after_slot_reservation"
    AFTER_BALLOT_PERSISTENCE = "after_ballot_persistence"
    AFTER_ENTITLEMENT_MUTATION = "after_entitlement_mutation"
    BEFORE_TRANSACTION_COMMIT = "before_transaction_commit"
    AFTER_COMMIT = "after_commit"
    BEFORE_OUTBOX_PUBLISH = "before_outbox_publish"
    AFTER_BOARD_APPEND = "after_board_append"
    BEFORE_CHECKPOINT_SIGNING = "before_checkpoint_signing"
    DURING_RECORD_EXPORT = "during_record_export"


class InjectedFault(RuntimeError):
    """Raised at an armed fault point. Test-only; never in production."""

    reason_code = "INTERNAL_FAIL_CLOSED"


@dataclass
class FaultInjector:
    armed: set[FaultPoint] = field(default_factory=set)

    def arm(self, point: FaultPoint) -> None:
        self.armed.add(point)

    def trip(self, point: FaultPoint | str) -> None:
        """Accepts the plain string the production hook passes.

        ``hooks.trip`` deliberately types its point as ``str`` so that no
        production module has to import this enum. ``FaultPoint`` is a
        ``StrEnum``, so membership works either way; the value is
        normalised here rather than at every call site.
        """
        named = FaultPoint(point)
        if named in self.armed:
            self.armed.discard(named)
            raise InjectedFault(f"injected fault at {named.value}")


@contextmanager
def armed(point: FaultPoint) -> Iterator[FaultInjector]:
    injector = FaultInjector()
    injector.arm(point)
    yield injector

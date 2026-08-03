"""REFERENCE API — NOT PRODUCTION AUTHENTICATION (PACK-16D §49).

This is the local call surface the verification harness needs, and nothing
more. It performs **no authentication**. The ``capability_reference`` it
takes is a test-only anonymous capability fixture: a string that names a
row in the reference store. In production the equivalent value arrives
through the PACK-14/PACK-15 credential boundary and is never a bare string
passed by a caller.

Every method is a thin dispatch onto the transaction, publication and
verification modules. There is no business logic here on purpose: an API
layer that could decide anything would be a second place where an
invariant lives.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.casting.ballot import BallotEnvelope, BallotOpening
from epd2_voting_service.reference.casting.store import ReferenceStore
from epd2_voting_service.reference.casting.transactions import (
    ElectionRuntime,
    SubmissionResult,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.crypto.merkle import verify_consistency
from epd2_voting_service.reference.election_record.builder import (
    ElectionRecord,
    export_record,
)
from epd2_voting_service.reference.hooks import FaultHook
from epd2_voting_service.reference.publication.bulletin_board import (
    BulletinBoard,
    Checkpoint,
)
from epd2_voting_service.reference.publication.outbox import ObligationState
from epd2_voting_service.reference.schemas import validate_document
from epd2_voting_service.reference.verification.results import VerificationResult
from epd2_voting_service.reference.verification.verifier import (
    board_export_from,
    verify_record,
)

#: Printed by any harness that mounts this surface.
API_BANNER = "REFERENCE API\nNOT PRODUCTION AUTHENTICATION"


class ReferenceApiError(RuntimeError):
    reason_code = "REFERENCE_API_ERROR"


@dataclass(frozen=True, slots=True)
class PublicationState:
    """What a voter may learn about their own submission before closure.

    Deliberately *not* here: whether anyone else has voted, how many leaves
    are occupied, the batch's real count, or any timestamp finer than the
    window. ``included`` stays ``False`` until the batch's opening is
    published at closure, because inclusion is not knowable before then.
    """

    ballot_id: str
    confirmation_code: str
    batch_window_id: str
    obligation_state: str
    counted: bool
    included: bool


@dataclass
class ReferenceApi:
    """REFERENCE API. NOT PRODUCTION AUTHENTICATION."""

    store: ReferenceStore
    runtime: ElectionRuntime
    board: BulletinBoard

    # -- submission ----------------------------------------------------

    def submit_public_challenge(
        self,
        capability_reference: str,
        envelope: BallotEnvelope,
        opening: BallotOpening,
        idempotency_key: str,
        *,
        fault_hook: FaultHook | None = None,
    ) -> SubmissionResult:
        return submit_public_challenge(
            self.store,
            self.runtime,
            capability_reference,
            envelope,
            opening,
            idempotency_key,
            fault_hook=fault_hook,
        )

    def submit_cast_ballot(
        self,
        capability_reference: str,
        envelope: BallotEnvelope,
        idempotency_key: str,
        *,
        fault_hook: FaultHook | None = None,
    ) -> SubmissionResult:
        return submit_cast_ballot(
            self.store,
            self.runtime,
            capability_reference,
            envelope,
            idempotency_key,
            fault_hook=fault_hook,
        )

    # -- receipt and publication state ---------------------------------

    def get_publication_state(self, result: SubmissionResult) -> PublicationState:
        obligation = self.store.obligations.get(result.publication_obligation_id)
        if obligation is None:
            raise ReferenceApiError("no publication obligation for this submission")
        state = ObligationState.PENDING
        for row in self.store.outbox.rows:
            if row.publication_obligation_id == result.publication_obligation_id:
                state = row.state
        return PublicationState(
            ballot_id=result.ballot_id,
            confirmation_code=result.confirmation_code,
            batch_window_id=result.batch_window_id,
            obligation_state=state.value,
            counted=result.counted,
            included=self.board.closed and state is ObligationState.DISPATCHED,
        )

    # -- board ---------------------------------------------------------

    def get_board_checkpoint(self, index: int = -1) -> Checkpoint:
        if not self.board.checkpoints:
            raise ReferenceApiError("no checkpoint has been published yet")
        return self.board.checkpoints[index]

    def get_inclusion_proof(self, sequence: int) -> list[tuple[str, bytes]]:
        return self.board.inclusion_proof(sequence)

    def get_consistency_proof(self, old_tree_size: int) -> list[bytes]:
        return self.board.consistency_proof(old_tree_size)

    def check_consistency(self, old_tree_size: int) -> bool:
        """Convenience for the harness: prove, then verify independently."""
        proof = self.board.consistency_proof(old_tree_size)
        return verify_consistency(
            self.board.root_at(old_tree_size),
            old_tree_size,
            self.board.root(),
            len(self.board.entries),
            proof,
        )

    # -- record and verifier -------------------------------------------

    def export_election_record(
        self, record: ElectionRecord, *, fault_hook: FaultHook | None = None
    ) -> bytes:
        """Validate against the registered schema, then serialise.

        The registry is load-bearing here rather than decorative: a record
        whose field set has drifted from `election_record@1.0.0` is refused
        before any bytes leave, so a schema change cannot ship silently
        alongside an export.
        """
        validate_document(
            "election_record",
            {name: getattr(record, name) for name in record.__slots__},
        )
        return export_record(record, fault_hook=fault_hook)

    def run_verifier(
        self,
        record: ElectionRecord,
        spoiled_openings: dict[str, object] | None = None,
    ) -> VerificationResult:
        return verify_record(record, board_export_from(self.board), spoiled_openings)

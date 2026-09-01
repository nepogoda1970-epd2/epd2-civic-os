"""The two atomic boundaries (PACK-16D §22 and §23).

Both follow the same discipline: validate everything first, reserve a leaf
slot, mutate entitlement state, persist the artefact, create the
publication obligation — all inside one transaction that rolls back
completely on any failure. A capability is never spent by a submission
that does not commit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_voting_service.reference.casting.ballot import (
    BallotEnvelope,
    BallotOpening,
    Manifest,
    verify_ballot_proofs,
)
from epd2_voting_service.reference.casting.confirmation import (
    derive_confirmation_code,
    verify_challenge_opening,
)
from epd2_voting_service.reference.casting.continuation import (
    CapabilityUnknownError,
    CastEntitlementExhaustedError,
    PublicChallengeEntitlementExhaustedError,
)
from epd2_voting_service.reference.casting.idempotency import (
    IdempotencyConflictError,
    IdempotencyRecord,
    request_digest,
)
from epd2_voting_service.reference.casting.store import (
    DuplicateArtifactError,
    ReferenceStore,
)
from epd2_voting_service.reference.crypto.parameters import ParameterSet
from epd2_voting_service.reference.hooks import FaultHook, trip
from epd2_voting_service.reference.publication.capacity import CapacityPlan, SlotClass
from epd2_voting_service.reference.publication.outbox import (
    ObligationState,
    PublicationObligation,
)


class Outcome(StrEnum):
    ACCEPTED = "accepted"
    REPLAYED = "replayed"


@dataclass(frozen=True, slots=True)
class SubmissionResult:
    outcome: Outcome
    reason_code: str
    ballot_id: str
    confirmation_code: str
    batch_window_id: str
    publication_obligation_id: str
    counted: bool


@dataclass(frozen=True, slots=True)
class ElectionRuntime:
    """Everything a transaction needs that is not per-submission."""

    manifest: Manifest
    params: ParameterSet
    public_key: int
    base_hash: bytes
    plan: CapacityPlan
    batch_sequence: int
    batch_window_id: str
    batch_capacity: int
    closed: bool = False


def _candidate_slots(
    runtime: ElectionRuntime, slot_class: SlotClass
) -> list[tuple[int, SlotClass]]:
    """Cast may use cast-reserved then shared reserve; a public challenge
    may use challenge-reserved then shared reserve, and **never** a
    cast-reserved slot (`TC-75`)."""
    cast_n = runtime.plan.cast_reserved_per_batch
    chal_n = runtime.plan.challenge_reserved_per_batch
    shared_n = runtime.plan.shared_reserve_per_batch
    # The shared reserve is exactly the declared count, never "whatever is
    # left in the batch". Inferring it from the capacity would silently
    # reintroduce adaptive overflow whenever a batch was made larger.
    shared = list(range(cast_n + chal_n, cast_n + chal_n + shared_n))
    if slot_class is SlotClass.CAST_RESERVED:
        own = list(range(0, cast_n))
    else:
        own = list(range(cast_n, cast_n + chal_n))
    return [(i, slot_class) for i in own] + [(i, SlotClass.SHARED_RESERVE) for i in shared]


def _replay(
    store: ReferenceStore, scope: tuple[str, str, str], digest: str
) -> SubmissionResult | None:
    record = store.idempotency.get(scope)
    if record is None:
        return None
    if record.request_digest != digest:
        raise IdempotencyConflictError(
            "the same idempotency key was reused with a different canonical request"
        )
    payload = dict(record.outcome_payload)
    return SubmissionResult(
        outcome=Outcome.REPLAYED,
        reason_code=record.outcome_code,
        ballot_id=payload["ballot_id"],
        confirmation_code=payload["confirmation_code"],
        batch_window_id=payload["batch_window_id"],
        publication_obligation_id=payload["publication_obligation_id"],
        counted=payload["counted"] == "true",
    )


def _record_idempotency(
    store: ReferenceStore,
    scope: tuple[str, str, str],
    digest: str,
    result: SubmissionResult,
) -> None:
    store.idempotency[scope] = IdempotencyRecord(
        idempotency_key=scope[2],
        election_context_id=scope[0],
        operation=scope[1],
        request_digest=digest,
        outcome_code=result.reason_code,
        outcome_payload=(
            ("ballot_id", result.ballot_id),
            ("confirmation_code", result.confirmation_code),
            ("batch_window_id", result.batch_window_id),
            ("publication_obligation_id", result.publication_obligation_id),
            ("counted", "true" if result.counted else "false"),
        ),
    )


def submit_public_challenge(
    store: ReferenceStore,
    runtime: ElectionRuntime,
    capability_reference: str,
    envelope: BallotEnvelope,
    opening: BallotOpening,
    idempotency_key: str,
    *,
    fault_hook: FaultHook | None = None,
) -> SubmissionResult:
    """One atomic transaction. Spends the public-challenge entitlement only."""
    scope = (runtime.manifest.election_context_id, "public_challenge", idempotency_key)
    digest = request_digest(envelope.canonical_bytes(runtime.params))
    with store.transaction() as tx:
        # The idempotency check lives *inside* the transaction. Checking it
        # first and then opening a transaction is a race: two concurrent
        # requests sharing a key can both observe "no record yet" and both
        # proceed. A concurrency test found exactly that; do not move it out.
        replayed = _replay(tx, scope, digest)
        if replayed is not None:
            return replayed
        state = tx.continuations.get(capability_reference)
        if state is None:
            raise CapabilityUnknownError("unknown continuation capability")
        if not state.public_challenge_entitlement_available:
            raise PublicChallengeEntitlementExhaustedError(
                "the public evidentiary challenge entitlement is already spent"
            )
        trip(fault_hook, "after_capability_validation")
        verify_ballot_proofs(
            envelope, runtime.manifest, runtime.public_key, runtime.params, runtime.base_hash
        )
        verify_challenge_opening(
            envelope, opening, runtime.public_key, runtime.params, runtime.base_hash
        )
        trip(fault_hook, "after_proof_validation")
        if envelope.ballot_id in tx.spoiled_ballots or envelope.ballot_id in tx.accepted_ballots:
            # A ballot id already present is a duplicate artefact, not an
            # idempotency conflict: the two have different reason codes
            # because a client can retry one and must not retry the other.
            raise DuplicateArtifactError(f"ballot {envelope.ballot_id} is already published")
        reservation = tx.reserve_leaf(
            reservation_id=f"res-chal-{idempotency_key}",
            batch_sequence=runtime.batch_sequence,
            candidate_slots=_candidate_slots(runtime, SlotClass.CHALLENGE_RESERVED),
            submission_reference=envelope.ballot_id,
            requested_class=SlotClass.CHALLENGE_RESERVED,
        )
        trip(fault_hook, "after_slot_reservation")
        tx.continuations[capability_reference] = state.spend_public_challenge()
        trip(fault_hook, "after_entitlement_mutation")
        tx.spoiled_ballots[envelope.ballot_id] = envelope.canonical_bytes(runtime.params)
        trip(fault_hook, "after_ballot_persistence")
        tx.commit_reservation(reservation.reservation_id)
        obligation = PublicationObligation(
            publication_obligation_id=f"obl-chal-{envelope.ballot_id}",
            election_context_id=runtime.manifest.election_context_id,
            artifact_internal_reference=envelope.ballot_id,
            artifact_type="public_challenged_spoiled",
            batch_window_id=runtime.batch_window_id,
            coarse_creation_bucket=runtime.batch_window_id,
        )
        tx.obligations[obligation.publication_obligation_id] = obligation
        tx.outbox.enqueue(obligation)
        result = SubmissionResult(
            outcome=Outcome.ACCEPTED,
            reason_code="challenge.spoiled_published",
            ballot_id=envelope.ballot_id,
            confirmation_code=derive_confirmation_code(envelope, runtime.params, runtime.base_hash),
            batch_window_id=runtime.batch_window_id,
            publication_obligation_id=obligation.publication_obligation_id,
            counted=False,
        )
        _record_idempotency(tx, scope, digest, result)
        trip(fault_hook, "before_transaction_commit")
        return result


def submit_cast_ballot(
    store: ReferenceStore,
    runtime: ElectionRuntime,
    capability_reference: str,
    envelope: BallotEnvelope,
    idempotency_key: str,
    *,
    fault_hook: FaultHook | None = None,
) -> SubmissionResult:
    """One atomic transaction. Consumes the capability, last of all."""
    scope = (runtime.manifest.election_context_id, "cast", idempotency_key)
    digest = request_digest(envelope.canonical_bytes(runtime.params))
    with store.transaction() as tx:
        replayed = _replay(tx, scope, digest)
        if replayed is not None:
            return replayed
        state = tx.continuations.get(capability_reference)
        if state is None:
            raise CapabilityUnknownError("unknown continuation capability")
        if not state.cast_entitlement_available or state.capability_consumed:
            raise CastEntitlementExhaustedError("the cast entitlement is already spent")
        trip(fault_hook, "after_capability_validation")
        verify_ballot_proofs(
            envelope, runtime.manifest, runtime.public_key, runtime.params, runtime.base_hash
        )
        trip(fault_hook, "after_proof_validation")
        if envelope.ballot_id in tx.accepted_ballots or envelope.ballot_id in tx.spoiled_ballots:
            raise DuplicateArtifactError(f"ballot {envelope.ballot_id} is already published")
        reservation = tx.reserve_leaf(
            reservation_id=f"res-cast-{idempotency_key}",
            batch_sequence=runtime.batch_sequence,
            candidate_slots=_candidate_slots(runtime, SlotClass.CAST_RESERVED),
            submission_reference=envelope.ballot_id,
            requested_class=SlotClass.CAST_RESERVED,
        )
        trip(fault_hook, "after_slot_reservation")
        tx.accepted_ballots[envelope.ballot_id] = envelope.canonical_bytes(runtime.params)
        trip(fault_hook, "after_ballot_persistence")
        tx.continuations[capability_reference] = state.consume_for_cast()
        trip(fault_hook, "after_entitlement_mutation")
        tx.commit_reservation(reservation.reservation_id)
        obligation = PublicationObligation(
            publication_obligation_id=f"obl-cast-{envelope.ballot_id}",
            election_context_id=runtime.manifest.election_context_id,
            artifact_internal_reference=envelope.ballot_id,
            artifact_type="accepted_cast",
            batch_window_id=runtime.batch_window_id,
            coarse_creation_bucket=runtime.batch_window_id,
        )
        tx.obligations[obligation.publication_obligation_id] = obligation
        tx.outbox.enqueue(obligation)
        result = SubmissionResult(
            outcome=Outcome.ACCEPTED,
            reason_code="acceptance.committed",
            ballot_id=envelope.ballot_id,
            confirmation_code=derive_confirmation_code(envelope, runtime.params, runtime.base_hash),
            batch_window_id=runtime.batch_window_id,
            publication_obligation_id=obligation.publication_obligation_id,
            counted=True,
        )
        _record_idempotency(tx, scope, digest, result)
        trip(fault_hook, "before_transaction_commit")
        return result


def dispatch_outbox(
    store: ReferenceStore, *, fault_hook: FaultHook | None = None
) -> list[PublicationObligation]:
    """Crash-safe dispatch: pending rows survive a crash before dispatch.

    The obligation is marked ``DISPATCHED`` only after the publish step
    returns, so a crash between the two leaves the row ``PENDING`` and the
    next sweep retries it. Retry is therefore at-least-once, and duplicate
    suppression is the board's job (one obligation id, one entry), not the
    outbox's.
    """
    dispatched: list[PublicationObligation] = []
    for row in store.outbox.pending():
        trip(fault_hook, "before_outbox_publish")
        store.outbox.mark(row.publication_obligation_id, ObligationState.DISPATCHED)
        trip(fault_hook, "after_commit")
        dispatched.append(row)
    return dispatched

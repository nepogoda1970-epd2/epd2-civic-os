"""Batch sealing: turn reservations into a fixed-capacity sealed batch."""

from __future__ import annotations

from epd2_voting_service.reference.casting.store import ReferenceStore
from epd2_voting_service.reference.crypto.randomness import RandomSource
from epd2_voting_service.reference.publication.capacity import CapacityExhaustedError
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchOpening,
    LeafClass,
    LeafOpening,
    SealedBatch,
    cover_leaf,
    merkle_root,
    new_salt,
    real_leaf,
)


def seal_batch(
    store: ReferenceStore,
    *,
    election_context_id: str,
    batch_sequence: int,
    batch_window_id: str,
    capacity: int,
    capacity_profile_id: str,
    source: RandomSource,
) -> tuple[SealedBatch, BatchOpening]:
    """Every unused slot becomes a cover leaf, so the batch is always full."""
    leaves: list[bytes] = []
    openings: list[LeafOpening] = []
    committed = {
        r.leaf_index: r
        for r in store.reservations.values()
        if r.batch_sequence == batch_sequence and r.committed
    }
    # Sealing is the last point at which an over-full batch can be caught.
    # Reaching this is a defect upstream, not a condition to absorb: a
    # batch that quietly dropped a committed reservation would lose an
    # accepted ballot.
    overflow = sorted(index for index in committed if index >= capacity)
    if overflow or len(committed) > capacity:
        raise CapacityExhaustedError(
            f"batch {batch_sequence} has {len(committed)} committed reservations "
            f"for {capacity} leaves; out-of-range leaf indices {overflow}"
        )
    for leaf_index in range(capacity):
        reservation = committed.get(leaf_index)
        if reservation is None:
            leaves.append(cover_leaf(source))
            openings.append(
                LeafOpening(
                    leaf_index=leaf_index,
                    leaf_class=LeafClass.COVER,
                    salt=b"",
                    artifact_reference="",
                    artifact_digest=b"",
                )
            )
            continue
        reference = reservation.submission_reference
        if reference in store.accepted_ballots:
            leaf_class = LeafClass.ACCEPTED_CAST
            digest = store.accepted_ballots[reference]
        else:
            leaf_class = LeafClass.PUBLIC_CHALLENGED_SPOILED
            digest = store.spoiled_ballots[reference]
        opening = LeafOpening(
            leaf_index=leaf_index,
            leaf_class=leaf_class,
            salt=new_salt(source),
            artifact_reference=reference,
            artifact_digest=digest,
        )
        leaves.append(real_leaf(election_context_id, batch_sequence, opening))
        openings.append(opening)
    batch = SealedBatch(
        election_context_id=election_context_id,
        batch_sequence=batch_sequence,
        batch_window_id=batch_window_id,
        fixed_capacity_profile_id=capacity_profile_id,
        capacity=capacity,
        commitment_root=merkle_root(leaves),
    )
    return batch, BatchOpening(
        batch_sequence=batch_sequence, leaves=tuple(leaves), openings=tuple(openings)
    )

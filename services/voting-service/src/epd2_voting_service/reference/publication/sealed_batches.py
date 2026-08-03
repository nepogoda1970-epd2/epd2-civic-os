"""Sealed fixed-capacity batch commitments (PACK-16C `TC-27`..`TC-45`).

A batch is exactly `C` leaves. A real leaf is a hiding commitment over a
ballot artefact's digests under a high-entropy salt; a cover leaf is a
uniform random value of the leaf's exact size. Before closure the two are
indistinguishable; at closure every leaf is opened in full.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import DIGEST_BYTES, ZERO_KEY, h
from epd2_voting_service.reference.crypto.merkle import inclusion_proof as _merkle_inclusion_proof
from epd2_voting_service.reference.crypto.merkle import root as _merkle_root
from epd2_voting_service.reference.crypto.merkle import (
    verify_inclusion as _merkle_verify_inclusion,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource

SALT_BYTES = 32


class LeafClass(StrEnum):
    ACCEPTED_CAST = "accepted_cast"
    PUBLIC_CHALLENGED_SPOILED = "public_challenged_spoiled"
    COVER = "cover"


class BatchIntegrityError(ValueError):
    reason_code = "BULLETIN_BOARD_BATCH_ROOT_MISMATCH"


@dataclass(frozen=True, slots=True)
class LeafOpening:
    """Everything needed to recompute one leaf."""

    leaf_index: int
    leaf_class: LeafClass
    salt: bytes
    artifact_reference: str
    artifact_digest: bytes

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("leaf_index", encode_uint(self.leaf_index, 4)),
                ("leaf_class", encode_text(self.leaf_class.value)),
                ("salt", encode_bytes(self.salt)),
                ("artifact_reference", encode_text(self.artifact_reference)),
                ("artifact_digest", encode_bytes(self.artifact_digest)),
            ]
        )


def real_leaf(
    election_context_id: str,
    batch_sequence: int,
    opening: LeafOpening,
) -> bytes:
    """A domain-separated hiding commitment, indistinguishable from random."""
    payload = encode_struct(
        [
            ("election_context_id", encode_text(election_context_id)),
            ("batch_sequence", encode_uint(batch_sequence, 8)),
            ("opening", opening.canonical_bytes()),
        ]
    )
    return h(ZERO_KEY, DomainLabel.BATCH_LEAF, [payload])


def cover_leaf(source: RandomSource) -> bytes:
    """A uniform random value of the leaf's exact size. Not a hash of anything."""
    return source.random_bytes(DIGEST_BYTES)


def new_salt(source: RandomSource) -> bytes:
    return source.random_bytes(SALT_BYTES)


def merkle_root(leaves: list[bytes]) -> bytes:
    """Merkle root over exactly ``len(leaves)`` leaves.

    Delegates to ``crypto.merkle``, which uses the RFC 6962 shape. The root
    is a fixed 32 bytes whatever the occupancy, which is what makes a
    sealed batch's published size independent of how many real ballots it
    holds (`TC-33`).
    """
    if not leaves:
        raise BatchIntegrityError("a batch must have at least one leaf")
    return _merkle_root(leaves)


def inclusion_path(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """Sibling path from a leaf to the root, as (side, digest) pairs."""
    if not 0 <= index < len(leaves):
        raise BatchIntegrityError("leaf index out of range")
    return _merkle_inclusion_proof(leaves, index)


def verify_inclusion(leaf: bytes, path: list[tuple[str, bytes]], root: bytes) -> bool:
    return _merkle_verify_inclusion(leaf, path, root)


@dataclass(frozen=True, slots=True)
class SealedBatch:
    """The published commitment. Constant-shaped whatever the occupancy."""

    election_context_id: str
    batch_sequence: int
    batch_window_id: str
    fixed_capacity_profile_id: str
    capacity: int
    commitment_root: bytes

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("election_context_id", encode_text(self.election_context_id)),
                ("batch_sequence", encode_uint(self.batch_sequence, 8)),
                ("batch_window_id", encode_text(self.batch_window_id)),
                (
                    "fixed_capacity_profile_id",
                    encode_text(self.fixed_capacity_profile_id),
                ),
                ("capacity", encode_uint(self.capacity, 4)),
                ("commitment_root", encode_bytes(self.commitment_root)),
            ]
        )


@dataclass(frozen=True, slots=True)
class BatchOpening:
    """Published at closure only, in full."""

    batch_sequence: int
    leaves: tuple[bytes, ...]
    openings: tuple[LeafOpening, ...]

    def recompute_root(self) -> bytes:
        return merkle_root(list(self.leaves))

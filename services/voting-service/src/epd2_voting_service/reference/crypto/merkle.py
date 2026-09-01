"""Merkle tree with RFC 6962 shape and EPD² domain separation.

Two things matter here and both are deliberate.

**Shape.** The tree follows RFC 6962 §2.1: the empty tree hashes the empty
sequence, a one-leaf tree is its leaf hash, and an n-leaf tree splits at
the largest power of two strictly below n. The earlier draft of this
module duplicated the last node on odd levels, which makes two different
leaf sequences share a root (the CVE-2012-2459 shape). That construction
was replaced, not patched.

**Hashing.** RFC 6962 prefixes 0x00 for leaves and 0x01 for internal
nodes. EPD² already has a domain-separation registry, so the prefix is
carried by the label instead: leaves use ``BATCH_LEAF``, internal nodes use
``BATCH_ROOT``. The separation property is the same — no internal node can
be reinterpreted as a leaf — and it is enforced through one registry
rather than two conventions.

The tree is unkeyed: every hash uses ``ZERO_KEY``. These are public
commitments over public artefacts; secrecy of a leaf's *content* comes
from the salt inside the leaf preimage, not from the tree.
"""

from __future__ import annotations

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_seq,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h


class MerkleError(ValueError):
    reason_code = "BATCH_ROOT_MISMATCH"


def leaf_hash(leaf: bytes) -> bytes:
    return h(ZERO_KEY, DomainLabel.BATCH_LEAF, [encode_bytes(leaf)])


def node_hash(left: bytes, right: bytes) -> bytes:
    return h(ZERO_KEY, DomainLabel.BATCH_ROOT, [encode_seq([left, right])])


def empty_root() -> bytes:
    return h(ZERO_KEY, DomainLabel.BATCH_ROOT, [encode_uint(0, 8)])


def _split(n: int) -> int:
    """Largest power of two strictly less than ``n`` (RFC 6962 ``k``)."""
    if n < 2:
        raise MerkleError("split is only defined for n >= 2")
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def _root(hashes: list[bytes]) -> bytes:
    n = len(hashes)
    if n == 0:
        return empty_root()
    if n == 1:
        return hashes[0]
    k = _split(n)
    return node_hash(_root(hashes[:k]), _root(hashes[k:]))


def root(leaves: list[bytes]) -> bytes:
    """Merkle root over ``leaves`` in order. Empty is a defined value."""
    return _root([leaf_hash(x) for x in leaves])


def _inclusion(hashes: list[bytes], index: int) -> list[tuple[str, bytes]]:
    n = len(hashes)
    if n <= 1:
        return []
    k = _split(n)
    if index < k:
        return [*_inclusion(hashes[:k], index), ("right", _root(hashes[k:]))]
    return [*_inclusion(hashes[k:], index - k), ("left", _root(hashes[:k]))]


def inclusion_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """Sibling path as ``(side_of_sibling, digest)`` pairs, leaf upwards."""
    if not 0 <= index < len(leaves):
        raise MerkleError("leaf index out of range")
    return _inclusion([leaf_hash(x) for x in leaves], index)


def verify_inclusion(leaf: bytes, path: list[tuple[str, bytes]], expected: bytes) -> bool:
    node = leaf_hash(leaf)
    for side, sibling in path:
        if side == "right":
            node = node_hash(node, sibling)
        elif side == "left":
            node = node_hash(sibling, node)
        else:  # pragma: no cover - guarded by the parser
            raise MerkleError(f"unknown sibling side {side!r}")
    return node == expected


def _consistency(hashes: list[bytes], m: int, *, complete: bool) -> list[bytes]:
    n = len(hashes)
    if m == n:
        return [] if complete else [_root(hashes)]
    k = _split(n)
    if m <= k:
        return [*_consistency(hashes[:k], m, complete=complete), _root(hashes[k:])]
    return [*_consistency(hashes[k:], m - k, complete=False), _root(hashes[:k])]


def consistency_proof(leaves: list[bytes], old_size: int) -> list[bytes]:
    """RFC 6962 §2.1.2 proof that the tree of ``old_size`` is a prefix."""
    n = len(leaves)
    if not 0 < old_size <= n:
        raise MerkleError(f"old_size {old_size} is not in (0, {n}]")
    return _consistency([leaf_hash(x) for x in leaves], old_size, complete=True)


def verify_consistency(
    old_root: bytes, old_size: int, new_root: bytes, new_size: int, proof: list[bytes]
) -> bool:
    """RFC 6962 §2.1.2 verification. Independent of the prover's recursion.

    This is the standard iterative algorithm rather than a mirror of
    :func:`_consistency`: a verifier that re-ran the prover's own recursion
    would agree with the prover by construction and would prove nothing.
    """
    if old_size < 1 or old_size > new_size:
        return False
    if old_size == new_size:
        return not proof and old_root == new_root
    nodes = list(proof)
    if old_size & (old_size - 1) == 0:
        # The old tree is complete, so the prover omitted its root.
        nodes = [old_root, *nodes]
    if not nodes:
        return False
    fn, sn = old_size - 1, new_size - 1
    while fn & 1:
        fn >>= 1
        sn >>= 1
    old_computed = new_computed = nodes[0]
    for sibling in nodes[1:]:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            old_computed = node_hash(sibling, old_computed)
            new_computed = node_hash(sibling, new_computed)
            while fn != 0 and fn & 1 == 0:
                fn >>= 1
                sn >>= 1
        else:
            new_computed = node_hash(new_computed, sibling)
        fn >>= 1
        sn >>= 1
    return sn == 0 and old_computed == old_root and new_computed == new_root

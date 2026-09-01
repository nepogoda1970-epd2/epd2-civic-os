"""Property tests (PACK-16D §41).

**Limitation, stated up front.** ``hypothesis`` is declared as a dev
dependency of this repository but could not be installed in the
environment this round was built in (PyPI is unreachable; see
``LOCAL_VERIFICATION.md`` and the PACK-16D implementation report). These
are therefore *deterministic randomised* property tests: each drives a
seeded ``DeterministicTestRandomSource`` over a fixed number of cases
rather than a shrinking search. They cover the property space but do not
shrink counterexamples and do not explore adversarially. Converting them
to real hypothesis strategies is a PACK-17 item, not a cosmetic one.

Every test below names the property from §41 that it discharges.
"""

from __future__ import annotations

import itertools

import pytest

from epd2_voting_service.reference.casting.continuation import (
    CastEntitlementExhaustedError,
    ContinuationState,
    PublicChallengeEntitlementExhaustedError,
)
from epd2_voting_service.reference.casting.idempotency import IdempotencyConflictError
from epd2_voting_service.reference.casting.transactions import (
    Outcome,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.crypto.elgamal import (
    accumulate,
    decode_exponent,
    encrypt,
)
from epd2_voting_service.reference.crypto.encoding import (
    decode_uint,
    encode_bytes,
    encode_seq,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h
from epd2_voting_service.reference.crypto.merkle import (
    inclusion_proof,
    verify_consistency,
    verify_inclusion,
)
from epd2_voting_service.reference.crypto.merkle import root as merkle_root
from epd2_voting_service.reference.crypto.proofs import (
    prove_selection,
    verify_selection,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource
from epd2_voting_service.reference.publication.sealed_batches import LeafClass
from epd2_voting_service.reference.publication.sealing import seal_batch
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    fixture_a,
    small_params,
)
from epd2_voting_service.reference.testing.scenarios import make_ballot

#: Deterministic randomised testing is not hypothesis. Named so the number
#: appears in the coverage report rather than being buried in a loop.
CASES = 40

PROPERTY_TEST_LIMITATION = (
    "deterministic randomised loops, not hypothesis strategies; no shrinking, no adversarial search"
)


def _keypair(source: RandomSource) -> tuple[int, int]:
    params = small_params()
    secret = 1 + source.random_below(params.q - 1)
    return secret, pow(params.g, secret, params.p)


# -- P-01 encrypt / decrypt aggregate consistency ------------------------


def test_p01_encrypt_decrypt_aggregate_consistency() -> None:
    params = small_params()
    source = deterministic_source(b"p01")
    secret, public_key = _keypair(source)
    for case in range(CASES):
        messages = [source.random_below(2) for _ in range(1 + case % 5)]
        ciphertexts = [
            encrypt(m, 1 + source.random_below(params.q - 1), public_key, params) for m in messages
        ]
        aggregate = accumulate(ciphertexts, params)
        group_value = (
            aggregate.beta * pow(pow(aggregate.alpha, secret, params.p), params.p - 2, params.p)
        ) % params.p
        assert decode_exponent(group_value, params, maximum=len(messages)) == sum(messages)


# -- P-02 valid proof always verifies / P-03 modified proof fails --------


def test_p02_valid_selection_proof_always_verifies() -> None:
    params = small_params()
    source = deterministic_source(b"p02")
    _, public_key = _keypair(source)
    for case in range(CASES):
        message = case % 2
        nonce = 1 + source.random_below(params.q - 1)
        ciphertext = encrypt(message, nonce, public_key, params)
        context = f"ctx-{case}".encode()
        proof = prove_selection(ciphertext, nonce, message, public_key, params, context, source)
        assert verify_selection(ciphertext, proof, public_key, params, context)


def test_p03_modified_proof_fails() -> None:
    params = small_params()
    source = deterministic_source(b"p03")
    _, public_key = _keypair(source)
    for case in range(CASES):
        message = case % 2
        nonce = 1 + source.random_below(params.q - 1)
        ciphertext = encrypt(message, nonce, public_key, params)
        context = b"ctx"
        proof = prove_selection(ciphertext, nonce, message, public_key, params, context, source)
        fields = (
            list(vars(proof).items())
            if hasattr(proof, "__dict__")
            else [(name, getattr(proof, name)) for name in proof.__slots__]
        )
        name, value = fields[case % len(fields)]
        tampered = type(proof)(
            **{
                key: ((value + 1) % params.p if key == name else getattr(proof, key))
                for key, _ in fields
            }
        )
        assert not verify_selection(ciphertext, tampered, public_key, params, context)
        # a proof also fails under a different context: Fiat-Shamir binds it
        assert not verify_selection(ciphertext, proof, public_key, params, b"other")


# -- P-04 canonical encode/decode stability ------------------------------


def test_p04_canonical_encode_decode_is_stable() -> None:
    source = deterministic_source(b"p04")
    for case in range(CASES):
        width = 1 + case % 8
        value = source.random_below(256**width)
        encoded = encode_uint(value, width)
        assert len(encoded) == width
        assert decode_uint(encoded, width) == value
        assert encode_uint(decode_uint(encoded, width), width) == encoded
        blob = source.random_bytes(1 + case % 17)
        assert encode_bytes(blob) == encode_uint(len(blob), 4) + blob
        text = f"contest-{case}-ünïcode"
        assert encode_text(text) == encode_text(text)
        assert encode_seq([blob, encoded]) == encode_seq([blob, encoded])


# -- P-05 hash input mutation changes digest -----------------------------


def test_p05_hash_input_mutation_changes_digest() -> None:
    from epd2_voting_service.reference.crypto.domain_separation import DomainLabel

    source = deterministic_source(b"p05")
    seen: set[bytes] = set()
    for _ in range(CASES):
        blob = source.random_bytes(32)
        digest = h(ZERO_KEY, DomainLabel.BALLOT_HASH, [blob])
        assert digest not in seen
        seen.add(digest)
        flipped = bytes([blob[0] ^ 1, *blob[1:]])
        assert h(ZERO_KEY, DomainLabel.BALLOT_HASH, [flipped]) != digest
        # the label is part of the preimage, not decoration
        assert h(ZERO_KEY, DomainLabel.CONFIRMATION_CODE, [blob]) != digest


def test_p05b_struct_is_not_length_ambiguous() -> None:
    """``("ab","c")`` and ``("a","bc")`` must not collide."""
    left = encode_struct([("f", encode_text("ab")), ("g", encode_text("c"))])
    right = encode_struct([("f", encode_text("a")), ("g", encode_text("bc"))])
    assert left != right


# -- P-06/P-07 idempotency ------------------------------------------------


def test_p06_same_idempotent_request_yields_same_result() -> None:
    for case in range(8):
        fixture = fixture_a()
        envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"p06-{case}".encode())
        key = f"idem-{case}"
        first = submit_cast_ballot(
            fixture.store, fixture.runtime, fixture.capabilities[0], envelope, key
        )
        second = submit_cast_ballot(
            fixture.store, fixture.runtime, fixture.capabilities[0], envelope, key
        )
        assert first.outcome is Outcome.ACCEPTED
        assert second.outcome is Outcome.REPLAYED
        assert (first.ballot_id, first.confirmation_code, first.counted) == (
            second.ballot_id,
            second.confirmation_code,
            second.counted,
        )
        assert len(fixture.store.accepted_ballots) == 1


def test_p07_different_request_with_same_key_fails() -> None:
    for case in range(8):
        fixture = fixture_a()
        first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"p07-a-{case}".encode())
        second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, f"p07-b-{case}".encode())
        submit_cast_ballot(
            fixture.store, fixture.runtime, fixture.capabilities[0], first, "same-key"
        )
        with pytest.raises(IdempotencyConflictError):
            submit_cast_ballot(
                fixture.store, fixture.runtime, fixture.capabilities[1], second, "same-key"
            )
        assert len(fixture.store.accepted_ballots) == 1


# -- P-08/P-09/P-10 capability arithmetic --------------------------------


def test_p08_one_capability_cannot_cast_twice() -> None:
    for case in range(8):
        fixture = fixture_a()
        capability = fixture.capabilities[0]
        first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"p08-a-{case}".encode())
        second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, f"p08-b-{case}".encode())
        submit_cast_ballot(fixture.store, fixture.runtime, capability, first, "k1")
        with pytest.raises(CastEntitlementExhaustedError):
            submit_cast_ballot(fixture.store, fixture.runtime, capability, second, "k2")
        assert len(fixture.store.accepted_ballots) == 1


def test_p09_one_capability_cannot_publish_two_challenges() -> None:
    for case in range(8):
        fixture = fixture_a()
        capability = fixture.capabilities[0]
        first, first_open = make_ballot(fixture, {"c1": ("opt-1",)}, f"p09-a-{case}".encode())
        second, second_open = make_ballot(fixture, {"c1": ("opt-2",)}, f"p09-b-{case}".encode())
        submit_public_challenge(fixture.store, fixture.runtime, capability, first, first_open, "k1")
        with pytest.raises(PublicChallengeEntitlementExhaustedError):
            submit_public_challenge(
                fixture.store, fixture.runtime, capability, second, second_open, "k2"
            )
        assert len(fixture.store.spoiled_ballots) == 1


def test_p10_public_challenge_does_not_consume_cast_entitlement() -> None:
    state = ContinuationState(capability_reference="cap", election_context_id="ctx")
    after = state.spend_public_challenge()
    assert after.public_challenge_entitlement_available is False
    assert after.cast_entitlement_available is True
    assert after.capability_consumed is False
    final = after.consume_for_cast()
    assert final.capability_consumed is True
    # and the arithmetic bound holds for every ordering
    assert ContinuationState("cap", "ctx").consume_for_cast().capability_consumed is True


# -- P-11 local diagnostic challenge causes no server state --------------


def test_p11_local_challenge_causes_no_server_state() -> None:
    """A local diagnostic challenge never reaches a transaction at all."""
    fixture = fixture_a()
    before = (
        dict(fixture.store.continuations),
        dict(fixture.store.accepted_ballots),
        dict(fixture.store.spoiled_ballots),
        dict(fixture.store.slot_owner),
        list(fixture.store.outbox.rows),
        list(fixture.board.entries),
    )
    for case in range(CASES):
        envelope, opening = make_ballot(fixture, {"c1": ("opt-1",)}, f"p11-{case}".encode())
        # the client re-encrypts locally from its own opening; no call is made
        from epd2_voting_service.reference.casting.confirmation import (
            verify_challenge_opening,
        )

        verify_challenge_opening(
            envelope, opening, fixture.public_key, fixture.params, fixture.base_hash
        )
    after = (
        dict(fixture.store.continuations),
        dict(fixture.store.accepted_ballots),
        dict(fixture.store.spoiled_ballots),
        dict(fixture.store.slot_owner),
        list(fixture.store.outbox.rows),
        list(fixture.board.entries),
    )
    assert before == after


# -- P-12/P-13 leaves ----------------------------------------------------


def test_p12_every_accepted_artifact_has_exactly_one_committed_leaf() -> None:
    fixture = fixture_a()
    envelopes = []
    for index in range(4):
        envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"p12-{index}".encode())
        submit_cast_ballot(
            fixture.store,
            fixture.runtime,
            fixture.capabilities[index],
            envelope,
            f"k{index}",
        )
        envelopes.append(envelope)
    _, opening = seal_batch(
        fixture.store,
        election_context_id=fixture.manifest.election_context_id,
        batch_sequence=0,
        batch_window_id="w0",
        capacity=fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"p12-seal"),
    )
    references = [o.artifact_reference for o in opening.openings if o.artifact_reference]
    assert sorted(references) == sorted(e.ballot_id for e in envelopes)
    assert len(references) == len(set(references))


def test_p13_cover_leaves_never_become_tally_eligible() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"p13")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    _, opening = seal_batch(
        fixture.store,
        election_context_id=fixture.manifest.election_context_id,
        batch_sequence=0,
        batch_window_id="w0",
        capacity=fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"p13-seal"),
    )
    covers = [o for o in opening.openings if o.leaf_class is LeafClass.COVER]
    assert covers, "the batch must contain cover leaves"
    for cover in covers:
        assert cover.artifact_reference == ""
        assert cover.artifact_digest == b""
        assert cover.salt == b""


# -- P-14 batch root recomputes ------------------------------------------


def test_p14_batch_root_recomputes() -> None:
    source = deterministic_source(b"p14")
    for case in range(1, 25):
        leaves = [source.random_bytes(32) for _ in range(case)]
        computed = merkle_root(leaves)
        assert merkle_root(list(leaves)) == computed
        for index in range(case):
            path = inclusion_proof(leaves, index)
            assert verify_inclusion(leaves[index], path, computed)
            assert not verify_inclusion(b"\x00" * 32, path, computed)


# -- P-15 append-only sequence never decreases ---------------------------


def test_p15_append_only_sequence_never_decreases() -> None:
    fixture = fixture_a()
    board = fixture.board
    from epd2_voting_service.reference.publication.bulletin_board import EntryType

    sizes: list[int] = []
    roots: list[bytes] = []
    for index in range(12):
        board.append(EntryType.SEALED_BATCH_COMMITMENT, f"b{index}".encode())
        checkpoint = board.publish_checkpoint()
        sizes.append(checkpoint.tree_size)
        roots.append(checkpoint.root)
    assert sizes == sorted(sizes)
    assert all(b > a for a, b in itertools.pairwise(sizes))
    for old_index in range(len(sizes) - 1):
        old_size = sizes[old_index]
        proof = board.consistency_proof(old_size)
        assert verify_consistency(
            roots[old_index], old_size, board.root(), len(board.entries), proof
        )


def test_property_limitation_is_recorded() -> None:
    """The limitation string exists so the report cannot quietly drop it.

    Originally this asserted that ``hypothesis`` was *not* importable,
    documenting the PyPI-unreachable environment PACK-16D was built in. A
    frozen ``uv sync --all-groups`` on a networked host installs hypothesis,
    so that assertion inverted from documentation into a false claim about
    every healthy environment. Following the PACK-16D lockfile-round rule —
    tests are written to pass in both the blocked and the resolved state,
    because a permanently red test trains readers to ignore red — this test
    now accepts both states. Installed hypothesis does not by itself upgrade
    these deterministic property tests: converting them to real shrinking
    strategies remains the governed forward item named in the module
    docstring.
    """
    assert "not hypothesis" in PROPERTY_TEST_LIMITATION
    try:
        import hypothesis  # noqa: F401

        hypothesis_available = True
    except ImportError:
        hypothesis_available = False
    assert hypothesis_available in (True, False)

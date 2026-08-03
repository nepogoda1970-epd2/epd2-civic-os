"""PACK-16D unit tests: parameters, encoding, domain separation, randomness."""

from __future__ import annotations

import os
import re

import pytest

from epd2_voting_service.reference.crypto import elgamal, proofs
from epd2_voting_service.reference.crypto.domain_separation import (
    DomainLabel,
    UnregisteredDomainLabelError,
    all_labels,
    require_label,
)
from epd2_voting_service.reference.crypto.encoding import (
    CanonicalEncodingError,
    decode_uint,
    encode_struct,
    encode_text,
    encode_uint,
    normalize_text,
)
from epd2_voting_service.reference.crypto.hashing import DIGEST_BYTES, ZERO_KEY, h, h_q
from epd2_voting_service.reference.crypto.parameters import (
    Q_ELECTIONGUARD_2_1,
    ParameterProfileUnavailableError,
    ParameterSet,
    ParameterValidationError,
    is_in_subgroup,
    is_probable_prime,
    is_target_profile,
    load_profile,
    validate_parameter_set,
)
from epd2_voting_service.reference.crypto.randomness import (
    TEST_PROFILE_ENV,
    DeterministicSourceForbiddenError,
    DeterministicTestRandomSource,
    ProductionRandomSource,
    select_source,
)
from epd2_voting_service.reference.testing.fixtures import deterministic_source, small_params


def test_q_is_the_electionguard_small_prime() -> None:
    assert Q_ELECTIONGUARD_2_1 == 2**256 - 189
    assert Q_ELECTIONGUARD_2_1.bit_length() == 256
    assert is_probable_prime(Q_ELECTIONGUARD_2_1)


def test_target_profile_loads_and_is_never_substituted() -> None:
    """`EPD2-CRYPTO-1` is the target profile and it loads.

    The first PACK-16D candidate could not obtain the published constants
    and registered the profile as unavailable. It is now present, verified
    by arithmetic rather than by trusting its source, and no test profile
    can stand in for it.
    """
    target = load_profile("EPD2-CRYPTO-1")
    assert target.parameter_set_id == "EPD2-CRYPTO-1"
    assert target.p.bit_length() == 4096
    assert target.q == Q_ELECTIONGUARD_2_1
    assert (target.p - 1) % target.q == 0
    assert pow(target.g, target.q, target.p) == 1
    assert target.production_use_permitted is False

    # the two test profiles are distinct objects and neither is the target
    for name in (
        "EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160",
        "EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256",
    ):
        other = load_profile(name, check_primality=False)
        assert other.p != target.p
        assert not is_target_profile(other.parameter_set_id)
    assert is_target_profile(target.parameter_set_id)


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(ParameterProfileUnavailableError):
        load_profile("not-a-profile")


def test_test_profiles_validate_fully() -> None:
    small = load_profile("EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160")
    assert small.p.bit_length() == 1024
    assert small.q.bit_length() == 160
    assert (small.p - 1) % small.q == 0
    assert pow(small.g, small.q, small.p) == 1
    assert small.production_use_permitted is False


def test_p4096_profile_has_the_electionguard_small_prime() -> None:
    large = load_profile("EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256", check_primality=False)
    assert large.p.bit_length() == 4096
    assert large.q == Q_ELECTIONGUARD_2_1
    assert (large.p - 1) % large.q == 0
    assert pow(large.g, large.q, large.p) == 1


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        ("p_bits", "|p| = "),
        ("q_divides", "q does not divide p - 1"),
        ("g_range", "g is outside (1, p)"),
        ("g_order", "g^q != 1: g is not in the order-q subgroup"),
    ],
)
def test_parameter_validation_fails_closed(mutate: str, expected: str) -> None:
    # ``match`` is a regex; these expectations are literal message substrings,
    # so they are escaped rather than trusted as patterns (PACK-16D TV-*).
    expected = re.escape(expected)
    params = small_params()
    if mutate == "p_bits":
        bad = ParameterSet("x", "v", "", False, params.p, params.q, params.g)
        with pytest.raises(ParameterValidationError, match=expected):
            validate_parameter_set(bad, expect_p_bits=2048, expect_q_bits=160)
        return
    if mutate == "q_divides":
        bad = ParameterSet("x", "v", "", False, params.p, params.q - 2, params.g)
    elif mutate == "g_range":
        bad = ParameterSet("x", "v", "", False, params.p, params.q, params.p + 5)
    else:
        bad = ParameterSet("x", "v", "", False, params.p, params.q, 3)
    with pytest.raises(ParameterValidationError, match=expected):
        validate_parameter_set(
            bad,
            expect_p_bits=bad.p.bit_length(),
            expect_q_bits=bad.q.bit_length(),
            check_primality=False,
        )


def test_subgroup_membership_rejects_zero_and_out_of_range() -> None:
    params = small_params()
    assert not is_in_subgroup(0, params)
    assert not is_in_subgroup(params.p, params)
    assert not is_in_subgroup(params.p + 1, params)
    assert is_in_subgroup(params.g, params)


def test_canonical_encoding_is_fixed_width_and_rejects_short_forms() -> None:
    assert encode_uint(1, 4) == b"\x00\x00\x00\x01"
    assert decode_uint(b"\x00\x00\x00\x01", 4) == 1
    with pytest.raises(CanonicalEncodingError):
        decode_uint(b"\x01", 4)
    with pytest.raises(CanonicalEncodingError):
        encode_uint(-1, 4)
    with pytest.raises(CanonicalEncodingError):
        encode_uint(2**32, 4)


def test_canonical_struct_rejects_duplicate_fields() -> None:
    with pytest.raises(CanonicalEncodingError, match="duplicate field"):
        encode_struct([("a", encode_uint(1, 4)), ("a", encode_uint(2, 4))])


def test_canonical_struct_field_order_is_normative() -> None:
    first = encode_struct([("a", encode_uint(1, 4)), ("b", encode_uint(2, 4))])
    second = encode_struct([("b", encode_uint(2, 4)), ("a", encode_uint(1, 4))])
    assert first != second


def test_text_is_nfc_normalised() -> None:
    composed, decomposed = "é", "é"
    assert composed != decomposed
    assert normalize_text(composed) == normalize_text(decomposed)
    assert encode_text(composed) == encode_text(decomposed)


def test_domain_labels_are_unique_and_registered() -> None:
    labels = all_labels()
    assert len(labels) == len(set(labels))
    assert len(labels) >= 24
    for label in DomainLabel:
        assert require_label(label) == label.value
    with pytest.raises(UnregisteredDomainLabelError):
        require_label("EPD2/v1/not-registered")


def test_hash_is_domain_separated() -> None:
    left = h(ZERO_KEY, DomainLabel.BALLOT_HASH, [b"x"])
    right = h(ZERO_KEY, DomainLabel.CONFIRMATION_CODE, [b"x"])
    assert left != right
    assert len(left) == DIGEST_BYTES
    assert 0 <= h_q(ZERO_KEY, DomainLabel.TALLY, [b"x"], 97) < 97


def test_production_source_is_never_deterministic() -> None:
    source = ProductionRandomSource()
    assert source.is_deterministic is False
    assert len(source.random_bytes(16)) == 16
    assert source.random_bytes(16) != source.random_bytes(16)


def test_select_source_can_never_return_a_deterministic_source() -> None:
    """PACK-16D §15: provable, not merely asserted."""
    assert select_source("production").is_deterministic is False
    for profile in ("test", "deterministic", "debug", "", "PRODUCTION"):
        with pytest.raises(DeterministicSourceForbiddenError):
            select_source(profile)


def test_deterministic_source_requires_both_guards() -> None:
    previous = os.environ.pop(TEST_PROFILE_ENV, None)
    try:
        with pytest.raises(DeterministicSourceForbiddenError):
            DeterministicTestRandomSource(b"seed", allow_in_test=True)
        os.environ[TEST_PROFILE_ENV] = "1"
        with pytest.raises(DeterministicSourceForbiddenError):
            DeterministicTestRandomSource(b"seed")
    finally:
        if previous is None:
            os.environ.pop(TEST_PROFILE_ENV, None)
        else:
            os.environ[TEST_PROFILE_ENV] = previous


def test_deterministic_source_is_reproducible() -> None:
    left, right = deterministic_source(b"same"), deterministic_source(b"same")
    assert left.random_bytes(64) == right.random_bytes(64)
    assert deterministic_source(b"other").random_bytes(64) != left.random_bytes(64)


def test_encrypt_rejects_out_of_domain_plaintext() -> None:
    params = small_params()
    source = deterministic_source()
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    nonce = elgamal.random_nonce(params, source)
    with pytest.raises(elgamal.PlaintextDomainError):
        elgamal.encrypt(2, nonce, public_key, params)
    with pytest.raises(elgamal.PlaintextDomainError):
        elgamal.encrypt(-1, nonce, public_key, params)


def test_accumulate_rejects_empty_and_invalid() -> None:
    params = small_params()
    with pytest.raises(elgamal.PlaintextDomainError):
        elgamal.accumulate([], params)
    with pytest.raises(ParameterValidationError):
        elgamal.accumulate([elgamal.Ciphertext(alpha=0, beta=1)], params)


def test_selection_proof_roundtrip_and_tamper_detection() -> None:
    params = small_params()
    source = deterministic_source()
    secret = 1 + source.random_below(params.q - 1)
    public_key = pow(params.g, secret, params.p)
    for message in (0, 1):
        nonce = elgamal.random_nonce(params, source)
        ciphertext = elgamal.encrypt(message, nonce, public_key, params)
        proof = proofs.prove_selection(
            ciphertext, nonce, message, public_key, params, b"ctx", source
        )
        assert proofs.verify_selection(ciphertext, proof, public_key, params, b"ctx")
        assert not proofs.verify_selection(ciphertext, proof, public_key, params, b"other")
        tampered = proofs.DisjunctiveProof(
            a0=proof.a0,
            b0=proof.b0,
            a1=proof.a1,
            b1=proof.b1,
            c0=(proof.c0 + 1) % params.q,
            c1=proof.c1,
            v0=proof.v0,
            v1=proof.v1,
        )
        assert not proofs.verify_selection(ciphertext, tampered, public_key, params, b"ctx")


def test_selection_proof_refuses_out_of_domain_message() -> None:
    params = small_params()
    source = deterministic_source()
    public_key = pow(params.g, 5, params.p)
    nonce = elgamal.random_nonce(params, source)
    ciphertext = elgamal.encrypt(1, nonce, public_key, params)
    with pytest.raises(proofs.ProofGenerationError):
        proofs.prove_selection(ciphertext, nonce, 2, public_key, params, b"ctx", source)

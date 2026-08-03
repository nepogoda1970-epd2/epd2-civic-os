"""Threshold guardian reference path (correction §7, §19).

PACK-16B fixes 3-of-5 by default and 4-of-7 for high assurance. These tests
exercise the generic `k`-of-`n` engine at both configurations and, more
importantly, at the boundaries where it must refuse.

The tests run on the fast test profile because a DKG plus a tally is many
hundreds of modular exponentiations; `test_epd2_crypto_1.py` runs a 3-of-5
ceremony on the real parameters so the two are not confused.
"""

from __future__ import annotations

import dataclasses

import pytest

from epd2_voting_service.reference.crypto.elgamal import Ciphertext, accumulate, encrypt
from epd2_voting_service.reference.crypto.parameters import ParameterSet
from epd2_voting_service.reference.guardians.ceremony import (
    DEFAULT_QUORUM,
    HIGH_ASSURANCE_QUORUM,
    CeremonyResult,
    CompensatedDecryptionProhibited,
    GuardianConfigurationError,
    GuardianErrorCode,
    InvalidShareProofError,
    QuorumPolicy,
    UnknownGuardianError,
    compensated_decryption_share,
    derive_joint_public_key,
    guardian_public_share_key,
    run_ceremony,
    verify_ceremony,
    verify_possession,
    verify_share,
)
from epd2_voting_service.reference.guardians.threshold import (
    DuplicateGuardianShareError,
    InsufficientQuorumError,
    ThresholdMismatchError,
    ThresholdShare,
    combine_shares,
    compute_share,
    lagrange_coefficient,
    quorum_digest,
)
from epd2_voting_service.reference.guardians.threshold import (
    verify_share as verify_threshold_share,
)
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    small_params,
)

MESSAGES = (1, 0, 1, 1)


def _election(
    quorum: int, count: int, seed: bytes
) -> tuple[ParameterSet, CeremonyResult, Ciphertext]:
    params = small_params()
    source = deterministic_source(seed)
    result = run_ceremony(f"ctx-{quorum}-{count}", QuorumPolicy(quorum, count), params, source)
    key = result.transcript.joint_public_key
    aggregate = accumulate(
        [encrypt(m, 1 + source.random_below(params.q - 1), key, params) for m in MESSAGES],
        params,
    )
    return params, result, aggregate


def _shares(
    params: ParameterSet,
    result: CeremonyResult,
    aggregate: Ciphertext,
    sequences: tuple[int, ...],
) -> list[ThresholdShare]:
    source = deterministic_source(b"shares")
    return [
        compute_share(
            aggregate,
            result.secret(s),
            result.transcript,
            params,
            "c1",
            "opt-1",
            source,
        )
        for s in sequences
    ]


# -- configuration --------------------------------------------------------


def test_baseline_configurations_are_the_pack_16b_ones() -> None:
    assert DEFAULT_QUORUM == (3, 5)
    assert HIGH_ASSURANCE_QUORUM == (4, 7)
    QuorumPolicy(*DEFAULT_QUORUM).validate()
    QuorumPolicy(*HIGH_ASSURANCE_QUORUM).validate()


def test_4_of_7_configuration() -> None:
    policy = QuorumPolicy(4, 7).validate()
    assert policy.quorum == 4
    assert policy.guardian_count == 7


@pytest.mark.parametrize(
    ("quorum", "count"),
    [(0, 5), (6, 5), (3, 0), (2, 5), (3, 7), (1, 3)],
)
def test_invalid_configurations_fail_closed(quorum: int, count: int) -> None:
    """A quorum at or below half the roster lets two disjoint sets decrypt."""
    with pytest.raises(GuardianConfigurationError):
        QuorumPolicy(quorum, count).validate()


# -- ceremony -------------------------------------------------------------


def test_3_of_5_joint_key_derivation() -> None:
    params, result, _ = _election(3, 5, b"dkg-3-5")
    transcript = result.transcript
    ok, detail = verify_ceremony(transcript, params)
    assert ok, detail
    assert derive_joint_public_key(transcript, params) == transcript.joint_public_key
    assert len(transcript.guardians) == 5
    for record in transcript.guardians:
        assert len(record.coefficient_commitments) == 3
        assert verify_possession(record, params)
    assert transcript.digest(params)
    assert quorum_digest(transcript, params)


def test_shares_verify_against_published_commitments() -> None:
    """Feldman VSS: a wrong share is detectable by its receiver."""
    params, result, _ = _election(3, 5, b"dkg-verify")
    record = result.transcript.guardians[0]
    # a share the sender did not commit to must not verify
    assert not verify_share(1234567, 2, record.coefficient_commitments, params)


def test_a_corrupt_share_aborts_the_ceremony() -> None:
    params = small_params()
    with pytest.raises(InvalidShareProofError, match="does not match its published"):
        run_ceremony(
            "ctx-corrupt",
            QuorumPolicy(3, 5),
            params,
            deterministic_source(b"corrupt"),
            corrupt_share_from=2,
        )


def test_ceremony_rejects_a_tampered_transcript() -> None:
    params, result, _ = _election(3, 5, b"dkg-tamper")
    transcript = result.transcript
    forged = dataclasses.replace(transcript, joint_public_key=params.g)
    ok, detail = verify_ceremony(forged, params)
    assert not ok
    assert "joint public key" in detail

    incomplete = dataclasses.replace(transcript, complete=False)
    assert verify_ceremony(incomplete, params)[0] is False

    dropped = dataclasses.replace(transcript, guardians=transcript.guardians[:-1])
    assert verify_ceremony(dropped, params)[0] is False


# -- threshold decryption -------------------------------------------------


def test_3_of_5_quorum_decryption() -> None:
    params, result, aggregate = _election(3, 5, b"tally-3-5")
    for selection in [(1, 2, 3), (1, 3, 5), (3, 4, 5), (2, 4, 5)]:
        shares = _shares(params, result, aggregate, selection)
        value = combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )
        assert value == sum(MESSAGES)


def test_more_than_quorum_also_succeeds() -> None:
    params, result, aggregate = _election(3, 5, b"tally-4-5")
    for selection in [(1, 2, 3, 4), (1, 2, 3, 4, 5)]:
        shares = _shares(params, result, aggregate, selection)
        assert combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        ) == sum(MESSAGES)


def test_2_of_5_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"tally-2-5")
    shares = _shares(params, result, aggregate, (1, 2))
    with pytest.raises(InsufficientQuorumError, match="may not be reduced"):
        combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_4_of_7_quorum_success() -> None:
    params, result, aggregate = _election(4, 7, b"tally-4-7")
    for selection in [(1, 2, 3, 4), (2, 4, 6, 7), (1, 3, 5, 7)]:
        shares = _shares(params, result, aggregate, selection)
        assert combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        ) == sum(MESSAGES)


def test_3_of_7_rejected() -> None:
    params, result, aggregate = _election(4, 7, b"tally-3-7")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    with pytest.raises(InsufficientQuorumError):
        combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_duplicate_guardian_share_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"dup")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    with pytest.raises(DuplicateGuardianShareError, match="two shares"):
        combine_shares(
            [*shares, shares[0]],
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_invalid_guardian_share_proof_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"badproof")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    # Doubling leaves the subgroup, so it is caught by the cheaper check
    # first. That ordering is deliberate and worth pinning.
    outside = dataclasses.replace(shares[0], share=shares[0].share * 2 % params.p)
    ok, detail = verify_threshold_share(
        outside,
        aggregate,
        result.transcript,
        params,
    )
    assert not ok
    assert "not a subgroup member" in detail

    # Multiplying by g stays inside the subgroup, so this reaches the proof.
    tampered = dataclasses.replace(
        shares[0],
        share=shares[0].share * params.g % params.p,
    )
    ok, detail = verify_threshold_share(
        tampered,
        aggregate,
        result.transcript,
        params,
    )
    assert not ok
    assert "proof does not verify" in detail
    with pytest.raises(InvalidShareProofError):
        combine_shares(
            [tampered, shares[1], shares[2]],
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_unknown_guardian_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"unknown")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    stranger = dataclasses.replace(shares[0], guardian_sequence=99, guardian_id="guardian-99")
    ok, detail = verify_threshold_share(
        stranger,
        aggregate,
        result.transcript,
        params,
    )
    assert not ok
    assert "outside the roster" in detail
    with pytest.raises(UnknownGuardianError):
        guardian_public_share_key(result.transcript, 99, params)


def test_wrong_election_share_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"wrongelection")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    foreign = dataclasses.replace(shares[0], election_context_id="some-other-election")
    ok, detail = verify_threshold_share(
        foreign,
        aggregate,
        result.transcript,
        params,
    )
    assert not ok
    assert "different election" in detail


def test_wrong_ciphertext_share_rejected() -> None:
    params, result, aggregate = _election(3, 5, b"wrongct")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    other = accumulate(
        [encrypt(1, 12345, result.transcript.joint_public_key, params)],
        params,
    )
    ok, _ = verify_threshold_share(shares[0], other, result.transcript, params)
    assert not ok


def test_shares_for_different_options_cannot_be_combined() -> None:
    params, result, aggregate = _election(3, 5, b"mixed")
    shares = _shares(params, result, aggregate, (1, 2, 3))
    mixed = dataclasses.replace(shares[2], option_id="opt-2")
    with pytest.raises(ThresholdMismatchError, match="different contests or options"):
        combine_shares(
            [shares[0], shares[1], mixed],
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_threshold_reduction_rejected() -> None:
    """The quorum comes from the transcript; a caller cannot lower it."""
    params, result, aggregate = _election(3, 5, b"reduce")
    shares = _shares(params, result, aggregate, (1, 2))

    # Presenting a transcript that claims a smaller quorum does not help:
    # the joint key no longer derives, so the ceremony fails verification
    # before any share is combined.
    forged = dataclasses.replace(result.transcript, policy=QuorumPolicy(2, 5))
    ok, _ = verify_ceremony(forged, params)
    assert not ok, "a transcript with a rewritten quorum must not verify"

    with pytest.raises(InsufficientQuorumError):
        combine_shares(
            shares,
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )
    with pytest.raises(InsufficientQuorumError):
        combine_shares(
            [],
            aggregate,
            result.transcript,
            params,
            maximum=len(MESSAGES),
        )


def test_compensated_decryption_unavailable() -> None:
    """A missing guardian is covered by others, never reconstructed."""
    with pytest.raises(CompensatedDecryptionProhibited, match="prohibited"):
        compensated_decryption_share()

    import epd2_voting_service.reference.guardians.threshold as threshold_module

    body = pathlib_read(threshold_module.__file__)
    for banned in ("compensate", "reconstruct_secret", "escrow", "break_glass"):
        assert banned not in body.lower().replace("reconstructed", ""), banned


def pathlib_read(path: str) -> str:
    import pathlib

    return pathlib.Path(path).read_text()


def test_no_guardian_secret_leaves_the_transcript() -> None:
    """The public record must contain nothing that reveals a share."""
    params, result, _ = _election(3, 5, b"secrets")
    blob = result.transcript.canonical_bytes(params)
    for secret in result.secrets:
        assert secret.secret_key_share.to_bytes(params.q_bytes, "big") not in blob
        for coefficient in secret.coefficients:
            assert coefficient.to_bytes(params.q_bytes, "big") not in blob
    fields = set(type(result.transcript.guardians[0]).__slots__)
    assert "secret" not in " ".join(fields)


def test_lagrange_coefficients_reconstruct_at_zero() -> None:
    """The interpolation identity, checked directly rather than via a tally."""
    q = small_params().q
    for selection in [(1, 2, 3), (2, 3, 5), (1, 3, 4, 7)]:
        total = sum(lagrange_coefficient(s, selection, q) for s in selection) % q
        # sum of Lagrange basis polynomials evaluated at 0 is 1
        assert total == 1
    with pytest.raises(UnknownGuardianError):
        lagrange_coefficient(9, (1, 2, 3), q)


def test_error_codes_are_the_declared_ones() -> None:
    assert {code.value for code in GuardianErrorCode} == {
        "guardian.threshold_mismatch",
        "guardian.insufficient_quorum",
        "guardian.duplicate_share",
        "guardian.invalid_share_proof",
        "guardian.unknown_guardian",
    }

"""Confirmation-code derivation and challenge opening verification."""

from __future__ import annotations

from epd2_voting_service.reference.casting.ballot import (
    BallotEnvelope,
    BallotOpening,
    _context_bytes,
)
from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.elgamal import encrypt
from epd2_voting_service.reference.crypto.encoding import encode_struct, encode_text, encode_uint
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h
from epd2_voting_service.reference.crypto.parameters import ParameterSet

CONFIRMATION_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CONFIRMATION_GROUPS = 5
CONFIRMATION_GROUP_LEN = 5


class ChallengeOpeningError(ValueError):
    reason_code = "CHALLENGE_REENCRYPTION_MISMATCH"


def confirmation_input(envelope: BallotEnvelope, params: ParameterSet, base_hash: bytes) -> bytes:
    """The exact preimage the confirmation code is derived from.

    Exported so an independent implementation can be handed the input and
    derive the code itself, rather than being handed the code and asked to
    agree with it.
    """
    return encode_struct(
        [
            ("base_hash", encode_uint(int.from_bytes(base_hash, "big"), 32)),
            ("ballot", envelope.canonical_bytes(params)),
        ]
    )


def derive_confirmation_code(
    envelope: BallotEnvelope, params: ParameterSet, base_hash: bytes
) -> str:
    """`ADR-101`: derived from the ballot's encryptions and `H_E` only.

    It is a function of public ciphertexts, so anybody holding the
    published ballot can recompute it, and it carries no identity.
    """
    digest = h(
        ZERO_KEY,
        DomainLabel.CONFIRMATION_CODE,
        [confirmation_input(envelope, params, base_hash)],
    )
    value = int.from_bytes(digest, "big")
    chars: list[str] = []
    for _ in range(CONFIRMATION_GROUPS * CONFIRMATION_GROUP_LEN):
        chars.append(CONFIRMATION_ALPHABET[value % len(CONFIRMATION_ALPHABET)])
        value //= len(CONFIRMATION_ALPHABET)
    return "-".join(
        "".join(chars[i : i + CONFIRMATION_GROUP_LEN])
        for i in range(0, len(chars), CONFIRMATION_GROUP_LEN)
    )


def verify_challenge_opening(
    envelope: BallotEnvelope,
    opening: BallotOpening,
    public_key: int,
    params: ParameterSet,
    base_hash: bytes,
) -> None:
    """Re-encrypt from the published opening and compare, or fail closed."""
    if opening.ballot_id != envelope.ballot_id:
        raise ChallengeOpeningError("opening does not belong to this ballot")
    nonce_by_option = dict(opening.nonces)
    plaintext_by_option = dict(opening.plaintexts)
    prefix = encode_struct(
        [
            ("base_hash", encode_uint(int.from_bytes(base_hash, "big"), 32)),
            ("ballot_id", encode_text(envelope.ballot_id)),
        ]
    )
    for contest in envelope.contests:
        for selection in contest.selections:
            if selection.option_id not in nonce_by_option:
                raise ChallengeOpeningError(
                    f"opening is incomplete: no nonce for {selection.option_id!r}"
                )
            nonce = nonce_by_option[selection.option_id]
            message = plaintext_by_option.get(selection.option_id, 0)
            reencrypted = encrypt(message, nonce, public_key, params)
            if (reencrypted.alpha, reencrypted.beta) != (
                selection.ciphertext.alpha,
                selection.ciphertext.beta,
            ):
                raise ChallengeOpeningError(f"re-encryption mismatch for {selection.option_id!r}")
            _ = _context_bytes(prefix, contest.contest_id, selection.option_id)

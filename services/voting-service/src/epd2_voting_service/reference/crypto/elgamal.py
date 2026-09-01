"""Exponential ElGamal over the order-q subgroup (PACK-16D §16).

`Encrypt(m; r) = (g^r mod p, K^r * g^m mod p)`. Ciphertexts multiply
componentwise, which adds plaintexts. The plaintext domain is **strictly
bounded**: a selection is 0 or 1 and a contest total is bounded by its
selection limit. `decode_exponent` therefore searches a bounded range and
fails closed rather than looping.

There is no arbitrary-message encryption: the protocol only ever encrypts
exponents, so offering more would be an unused, untested attack surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.crypto.encoding import encode_group_element, encode_struct
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    ParameterValidationError,
    require_in_subgroup,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource

MAX_EXPONENT_SEARCH = 1024


class PlaintextDomainError(ValueError):
    """A plaintext outside the approved bounded domain was offered."""

    reason_code = "BALLOT_PREPARATION_CONTEST_INVALID"


class DecryptionDomainError(ValueError):
    """`g^m` did not decode to a plaintext inside the bounded domain."""

    reason_code = "TALLY_MISMATCH"


@dataclass(frozen=True, slots=True)
class Ciphertext:
    """An exponential-ElGamal ciphertext `(alpha, beta)`."""

    alpha: int
    beta: int

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        width = params.p_bytes
        return encode_struct(
            [
                ("alpha", encode_group_element(self.alpha, width)),
                ("beta", encode_group_element(self.beta, width)),
            ]
        )


def validate_ciphertext(ciphertext: Ciphertext, params: ParameterSet) -> Ciphertext:
    """Both components must be genuine subgroup members. Every time."""
    require_in_subgroup(ciphertext.alpha, params, "ciphertext alpha")
    require_in_subgroup(ciphertext.beta, params, "ciphertext beta")
    return ciphertext


def validate_public_key(public_key: int, params: ParameterSet) -> int:
    return require_in_subgroup(public_key, params, "public key")


def random_nonce(params: ParameterSet, source: RandomSource) -> int:
    """A uniform non-zero scalar in `[1, q-1]`."""
    return 1 + source.random_below(params.q - 1)


def encrypt(
    message: int,
    nonce: int,
    public_key: int,
    params: ParameterSet,
    *,
    max_message: int = 1,
) -> Ciphertext:
    """Encrypt a bounded exponent. Fails closed outside the domain."""
    if not 0 <= message <= max_message:
        raise PlaintextDomainError(f"plaintext {message} outside [0, {max_message}]")
    if not 0 < nonce < params.q:
        raise ParameterValidationError("nonce outside [1, q-1]")
    validate_public_key(public_key, params)
    alpha = pow(params.g, nonce, params.p)
    beta = pow(public_key, nonce, params.p) * pow(params.g, message, params.p) % params.p
    return Ciphertext(alpha=alpha, beta=beta)


def accumulate(ciphertexts: list[Ciphertext], params: ParameterSet) -> Ciphertext:
    """Homomorphic sum. An empty list is an error, never an identity."""
    if not ciphertexts:
        raise PlaintextDomainError("cannot accumulate an empty ciphertext list")
    alpha, beta = 1, 1
    for item in ciphertexts:
        validate_ciphertext(item, params)
        alpha = alpha * item.alpha % params.p
        beta = beta * item.beta % params.p
    return Ciphertext(alpha=alpha, beta=beta)


def decode_exponent(group_value: int, params: ParameterSet, *, maximum: int) -> int:
    """Recover `m` from `g^m`, over a bounded range only."""
    if maximum > MAX_EXPONENT_SEARCH:
        raise DecryptionDomainError("bounded exponent search limit exceeded")
    accumulator = 1
    for candidate in range(maximum + 1):
        if accumulator == group_value:
            return candidate
        accumulator = accumulator * params.g % params.p
    raise DecryptionDomainError("g^m did not decode inside the bounded domain")

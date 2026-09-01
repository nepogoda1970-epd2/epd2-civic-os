"""Non-interactive zero-knowledge proofs (PACK-16D §17).

Three proof kinds, all Fiat-Shamir over domain-separated hashes and all
verified from canonical bytes:

* :func:`prove_selection` / :func:`verify_selection` - disjunctive
  Chaum-Pedersen that a selection encrypts 0 or 1.
* :func:`prove_contest_sum` / :func:`verify_contest_sum` - Chaum-Pedersen
  that a contest's accumulated ciphertext encrypts exactly its selection
  limit.
* :func:`prove_decryption_share` / :func:`verify_decryption_share` -
  Chaum-Pedersen that a guardian's share was computed with the same
  secret its public commitment names.

No new proof system is invented: these are the standard constructions of
the adopted ElectionGuard lineage, re-expressed over this repository's
canonical encoding and domain-separation registry.

**No constant-time or side-channel claim is made about this module.**
Python's arbitrary-precision integers and ``pow()`` are not constant-time,
and neither the exponentiations nor the comparisons below are written to
be. A production implementation needs a constant-time bignum path; this is
recorded as a production blocker, not as a residual nicety.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.elgamal import Ciphertext, validate_ciphertext
from epd2_voting_service.reference.crypto.encoding import (
    encode_group_element,
    encode_scalar,
    encode_struct,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h_q
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    is_in_subgroup,
    require_in_subgroup,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource


class ProofGenerationError(RuntimeError):
    reason_code = "BALLOT_PROOF_GENERATION_FAILED"


@dataclass(frozen=True, slots=True)
class DisjunctiveProof:
    """Proof that a ciphertext encrypts 0 or 1."""

    a0: int
    b0: int
    a1: int
    b1: int
    c0: int
    c1: int
    v0: int
    v1: int

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        pw, qw = params.p_bytes, params.q_bytes
        return encode_struct(
            [
                ("a0", encode_group_element(self.a0, pw)),
                ("b0", encode_group_element(self.b0, pw)),
                ("a1", encode_group_element(self.a1, pw)),
                ("b1", encode_group_element(self.b1, pw)),
                ("c0", encode_scalar(self.c0, qw)),
                ("c1", encode_scalar(self.c1, qw)),
                ("v0", encode_scalar(self.v0, qw)),
                ("v1", encode_scalar(self.v1, qw)),
            ]
        )


@dataclass(frozen=True, slots=True)
class ChaumPedersenProof:
    """Proof of equality of two discrete logarithms."""

    a: int
    b: int
    challenge: int
    response: int

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        pw, qw = params.p_bytes, params.q_bytes
        return encode_struct(
            [
                ("a", encode_group_element(self.a, pw)),
                ("b", encode_group_element(self.b, pw)),
                ("challenge", encode_scalar(self.challenge, qw)),
                ("response", encode_scalar(self.response, qw)),
            ]
        )


def _selection_challenge(
    ciphertext: Ciphertext,
    public_key: int,
    commitments: tuple[int, int, int, int],
    context: bytes,
    params: ParameterSet,
) -> int:
    pw = params.p_bytes
    payload = encode_struct(
        [
            ("context", context),
            ("public_key", encode_group_element(public_key, pw)),
            ("alpha", encode_group_element(ciphertext.alpha, pw)),
            ("beta", encode_group_element(ciphertext.beta, pw)),
            ("a0", encode_group_element(commitments[0], pw)),
            ("b0", encode_group_element(commitments[1], pw)),
            ("a1", encode_group_element(commitments[2], pw)),
            ("b1", encode_group_element(commitments[3], pw)),
        ]
    )
    return h_q(ZERO_KEY, DomainLabel.SELECTION_PROOF, [payload], params.q)


def prove_selection(
    ciphertext: Ciphertext,
    nonce: int,
    message: int,
    public_key: int,
    params: ParameterSet,
    context: bytes,
    source: RandomSource,
) -> DisjunctiveProof:
    """Disjunctive Chaum-Pedersen for `message in {0, 1}`."""
    if message not in (0, 1):
        raise ProofGenerationError("selection proof is defined only for 0 or 1")
    p, q, g = params.p, params.q, params.g
    if message == 0:
        u0 = 1 + source.random_below(q - 1)
        a0, b0 = pow(g, u0, p), pow(public_key, u0, p)
        c1 = 1 + source.random_below(q - 1)
        v1 = 1 + source.random_below(q - 1)
        inv_alpha_c1 = pow(ciphertext.alpha, q - c1, p)
        beta_over_g = ciphertext.beta * pow(g, q - 1, p) % p
        a1 = pow(g, v1, p) * inv_alpha_c1 % p
        b1 = pow(public_key, v1, p) * pow(beta_over_g, q - c1, p) % p
        challenge = _selection_challenge(ciphertext, public_key, (a0, b0, a1, b1), context, params)
        c0 = (challenge - c1) % q
        v0 = (u0 + c0 * nonce) % q
    else:
        u1 = 1 + source.random_below(q - 1)
        a1, b1 = pow(g, u1, p), pow(public_key, u1, p)
        c0 = 1 + source.random_below(q - 1)
        v0 = 1 + source.random_below(q - 1)
        a0 = pow(g, v0, p) * pow(ciphertext.alpha, q - c0, p) % p
        b0 = pow(public_key, v0, p) * pow(ciphertext.beta, q - c0, p) % p
        challenge = _selection_challenge(ciphertext, public_key, (a0, b0, a1, b1), context, params)
        c1 = (challenge - c0) % q
        v1 = (u1 + c1 * nonce) % q
    return DisjunctiveProof(a0=a0, b0=b0, a1=a1, b1=b1, c0=c0, c1=c1, v0=v0, v1=v1)


def verify_selection(
    ciphertext: Ciphertext,
    proof: DisjunctiveProof,
    public_key: int,
    params: ParameterSet,
    context: bytes,
) -> bool:
    """Verify a disjunctive proof from canonical values only."""
    p, q, g = params.p, params.q, params.g
    # The public key is not a proof element, but an attacker-supplied key
    # outside the subgroup would make every equation below meaningless.
    # Check it here rather than trusting the caller to have done it.
    if not is_in_subgroup(public_key, params):
        return False
    for element in (proof.a0, proof.b0, proof.a1, proof.b1):
        if not is_in_subgroup(element, params):
            return False
    for scalar in (proof.c0, proof.c1, proof.v0, proof.v1):
        if not 0 <= scalar < q:
            return False
    if not is_in_subgroup(ciphertext.alpha, params) or not is_in_subgroup(ciphertext.beta, params):
        return False
    challenge = _selection_challenge(
        ciphertext, public_key, (proof.a0, proof.b0, proof.a1, proof.b1), context, params
    )
    if (proof.c0 + proof.c1) % q != challenge:
        return False
    if pow(g, proof.v0, p) != proof.a0 * pow(ciphertext.alpha, proof.c0, p) % p:
        return False
    if pow(public_key, proof.v0, p) != proof.b0 * pow(ciphertext.beta, proof.c0, p) % p:
        return False
    beta_over_g = ciphertext.beta * pow(g, q - 1, p) % p
    if pow(g, proof.v1, p) != proof.a1 * pow(ciphertext.alpha, proof.c1, p) % p:
        return False
    return pow(public_key, proof.v1, p) == proof.b1 * pow(beta_over_g, proof.c1, p) % p


def _cp_challenge(
    label: DomainLabel,
    base_b: int,
    target_a: int,
    target_b: int,
    commitment_a: int,
    commitment_b: int,
    context: bytes,
    params: ParameterSet,
) -> int:
    pw = params.p_bytes
    payload = encode_struct(
        [
            ("context", context),
            ("base_b", encode_group_element(base_b, pw)),
            ("target_a", encode_group_element(target_a, pw)),
            ("target_b", encode_group_element(target_b, pw)),
            ("commitment_a", encode_group_element(commitment_a, pw)),
            ("commitment_b", encode_group_element(commitment_b, pw)),
        ]
    )
    return h_q(ZERO_KEY, label, [payload], params.q)


def prove_contest_sum(
    accumulated: Ciphertext,
    nonce_sum: int,
    selection_limit: int,
    public_key: int,
    params: ParameterSet,
    context: bytes,
    source: RandomSource,
) -> ChaumPedersenProof:
    """Prove the accumulated contest ciphertext encrypts `selection_limit`."""
    p, q, g = params.p, params.q, params.g
    validate_ciphertext(accumulated, params)
    target_b = accumulated.beta * pow(g, q - (selection_limit % q), p) % p
    u = 1 + source.random_below(q - 1)
    a, b = pow(g, u, p), pow(public_key, u, p)
    challenge = _cp_challenge(
        DomainLabel.CONTEST_PROOF, public_key, accumulated.alpha, target_b, a, b, context, params
    )
    response = (u + challenge * nonce_sum) % q
    return ChaumPedersenProof(a=a, b=b, challenge=challenge, response=response)


def verify_contest_sum(
    accumulated: Ciphertext,
    proof: ChaumPedersenProof,
    selection_limit: int,
    public_key: int,
    params: ParameterSet,
    context: bytes,
) -> bool:
    p, q, g = params.p, params.q, params.g
    if not is_in_subgroup(public_key, params):
        return False
    if not is_in_subgroup(proof.a, params) or not is_in_subgroup(proof.b, params):
        return False
    if not 0 <= proof.challenge < q or not 0 <= proof.response < q:
        return False
    if not is_in_subgroup(accumulated.alpha, params):
        return False
    if not is_in_subgroup(accumulated.beta, params):
        return False
    target_b = accumulated.beta * pow(g, q - (selection_limit % q), p) % p
    challenge = _cp_challenge(
        DomainLabel.CONTEST_PROOF,
        public_key,
        accumulated.alpha,
        target_b,
        proof.a,
        proof.b,
        context,
        params,
    )
    if challenge != proof.challenge:
        return False
    if pow(g, proof.response, p) != proof.a * pow(accumulated.alpha, challenge, p) % p:
        return False
    return pow(public_key, proof.response, p) == proof.b * pow(target_b, challenge, p) % p


def prove_decryption_share(
    alpha: int,
    share: int,
    secret: int,
    guardian_public: int,
    params: ParameterSet,
    context: bytes,
    source: RandomSource,
) -> ChaumPedersenProof:
    """Prove `log_g(guardian_public) == log_alpha(share)`."""
    p, q, g = params.p, params.q, params.g
    require_in_subgroup(alpha, params, "decryption alpha")
    u = 1 + source.random_below(q - 1)
    a, b = pow(g, u, p), pow(alpha, u, p)
    challenge = _cp_challenge(
        DomainLabel.DECRYPTION_SHARE, alpha, guardian_public, share, a, b, context, params
    )
    response = (u + challenge * secret) % q
    return ChaumPedersenProof(a=a, b=b, challenge=challenge, response=response)


def verify_decryption_share(
    alpha: int,
    share: int,
    guardian_public: int,
    proof: ChaumPedersenProof,
    params: ParameterSet,
    context: bytes,
) -> bool:
    p, q, g = params.p, params.q, params.g
    for element in (proof.a, proof.b, alpha, share, guardian_public):
        if not is_in_subgroup(element, params):
            return False
    if not 0 <= proof.challenge < q or not 0 <= proof.response < q:
        return False
    challenge = _cp_challenge(
        DomainLabel.DECRYPTION_SHARE,
        alpha,
        guardian_public,
        share,
        proof.a,
        proof.b,
        context,
        params,
    )
    if challenge != proof.challenge:
        return False
    if pow(g, proof.response, p) != proof.a * pow(guardian_public, challenge, p) % p:
        return False
    return pow(alpha, proof.response, p) == proof.b * pow(share, challenge, p) % p

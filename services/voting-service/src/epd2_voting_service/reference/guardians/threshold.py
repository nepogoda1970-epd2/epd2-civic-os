"""Threshold decryption: quorum selection, Lagrange combination, verification.

Given `k`-of-`n` shares produced by `guardians.ceremony`, any `k` guardians
can jointly decrypt a ciphertext without any of them learning the joint
secret. The mechanism is Shamir interpolation in the exponent:

    M   = prod_l M_l^(w_l)    where  M_l = alpha^(s_l)
    w_l = prod_{j != l} j / (j - l)   mod q
    g^m = beta / M

Every share carries a Chaum-Pedersen proof that `M_l` really is
`alpha^(s_l)` for the same `s_l` whose public image `g^(s_l)` the verifier
derived from the ceremony commitments. A share without a valid proof is
rejected; it is never merely down-weighted.

**The quorum is not negotiable at runtime.** `combine_shares` takes the
policy from the ceremony transcript, not from its caller, and refuses a set
smaller than that policy's `k`. There is no path that accepts `k-1`.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.elgamal import Ciphertext, decode_exponent
from epd2_voting_service.reference.crypto.encoding import (
    encode_group_element,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h_q
from epd2_voting_service.reference.crypto.parameters import ParameterSet, is_in_subgroup
from epd2_voting_service.reference.crypto.proofs import (
    ChaumPedersenProof,
    prove_decryption_share,
    verify_decryption_share,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource
from epd2_voting_service.reference.guardians.ceremony import (
    CeremonyTranscript,
    DuplicateGuardianShareError,
    GuardianSecret,
    InsufficientQuorumError,
    InvalidShareProofError,
    ThresholdMismatchError,
    UnknownGuardianError,
    guardian_public_share_key,
)


@dataclass(frozen=True, slots=True)
class ThresholdShare:
    """One guardian's partial decryption of one ciphertext, with its proof."""

    election_context_id: str
    guardian_id: str
    guardian_sequence: int
    contest_id: str
    option_id: str
    #: `M_l = alpha^(s_l) mod p`
    share: int
    proof: ChaumPedersenProof

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("election_context_id", encode_text(self.election_context_id)),
                ("guardian_id", encode_text(self.guardian_id)),
                ("guardian_sequence", encode_uint(self.guardian_sequence, 4)),
                ("contest_id", encode_text(self.contest_id)),
                ("option_id", encode_text(self.option_id)),
                ("share", encode_group_element(self.share, params.p_bytes)),
                ("proof", self.proof.canonical_bytes(params)),
            ]
        )


def share_context(
    election_context_id: str,
    parameter_set_id: str,
    contest_id: str,
    option_id: str,
    guardian_sequence: int,
) -> bytes:
    """The Fiat-Shamir context a threshold share's proof is bound to.

    It names the election, the parameter set, the contest, the option and
    the guardian. A share proved for one of those does not verify for
    another, which is what makes cross-election and cross-option replay
    fail rather than merely be unlikely.
    """
    return encode_struct(
        [
            ("label", encode_text("threshold-decryption-share")),
            ("election_context_id", encode_text(election_context_id)),
            ("parameter_set_id", encode_text(parameter_set_id)),
            ("contest_id", encode_text(contest_id)),
            ("option_id", encode_text(option_id)),
            ("guardian_sequence", encode_uint(guardian_sequence, 4)),
        ]
    )


def compute_share(
    ciphertext: Ciphertext,
    secret: GuardianSecret,
    transcript: CeremonyTranscript,
    params: ParameterSet,
    contest_id: str,
    option_id: str,
    source: RandomSource,
) -> ThresholdShare:
    """Guardian `l` partially decrypts, and proves it did so correctly."""
    record = transcript.guardian(secret.guardian_sequence)
    value = pow(ciphertext.alpha, secret.secret_key_share, params.p)
    public_share_key = pow(params.g, secret.secret_key_share, params.p)
    context = share_context(
        transcript.election_context_id,
        params.parameter_set_id,
        contest_id,
        option_id,
        secret.guardian_sequence,
    )
    proof = prove_decryption_share(
        ciphertext.alpha,
        value,
        secret.secret_key_share,
        public_share_key,
        params,
        context,
        source,
    )
    return ThresholdShare(
        election_context_id=transcript.election_context_id,
        guardian_id=record.guardian_id,
        guardian_sequence=secret.guardian_sequence,
        contest_id=contest_id,
        option_id=option_id,
        share=value,
        proof=proof,
    )


def verify_share(
    share: ThresholdShare,
    ciphertext: Ciphertext,
    transcript: CeremonyTranscript,
    params: ParameterSet,
) -> tuple[bool, str]:
    """Verify one share against the ceremony. Public values only."""
    if share.election_context_id != transcript.election_context_id:
        return False, "share names a different election"
    try:
        record = transcript.guardian(share.guardian_sequence)
    except UnknownGuardianError:
        return False, "share is from a guardian outside the roster"
    if record.guardian_id != share.guardian_id:
        return False, "guardian id does not match the sequence in the roster"
    if not is_in_subgroup(share.share, params):
        return False, "share is not a subgroup member"
    expected_key = guardian_public_share_key(transcript, share.guardian_sequence, params)
    context = share_context(
        transcript.election_context_id,
        params.parameter_set_id,
        share.contest_id,
        share.option_id,
        share.guardian_sequence,
    )
    if not verify_decryption_share(
        ciphertext.alpha, share.share, expected_key, share.proof, params, context
    ):
        return False, "share proof does not verify against the ceremony commitments"
    return True, ""


def lagrange_coefficient(sequence: int, selection: tuple[int, ...], q: int) -> int:
    """`w_l = prod_{j != l} j / (j - l) mod q`, evaluated at zero.

    `q` is prime, so the inverse is `x^(q-2)`. A repeated sequence number
    would make `j - l` zero and the inverse undefined, which is one reason
    duplicate shares are rejected before this is ever called.
    """
    if sequence not in selection:
        raise UnknownGuardianError(f"guardian {sequence} is not in the selection")
    numerator = 1
    denominator = 1
    for other in selection:
        if other == sequence:
            continue
        numerator = numerator * other % q
        denominator = denominator * ((other - sequence) % q) % q
    if denominator == 0:
        raise DuplicateGuardianShareError("duplicate guardian sequence in selection")
    return numerator * pow(denominator, q - 2, q) % q


def combine_shares(
    shares: list[ThresholdShare],
    ciphertext: Ciphertext,
    transcript: CeremonyTranscript,
    params: ParameterSet,
    *,
    maximum: int,
) -> int:
    """Combine a quorum of verified shares into a plaintext.

    Fail-closed on: too few shares, a duplicate guardian, an unknown
    guardian, a share for another election, a share for another contest or
    option, and any share whose proof does not verify. None of these is a
    warning, and none is recoverable by dropping the offending share and
    continuing — a bad share means the set presented is not the set the
    quorum authorised.
    """
    policy = transcript.policy
    if not shares:
        raise InsufficientQuorumError(
            f"no decryption shares presented; the quorum is {policy.quorum}"
        )
    contest_id = shares[0].contest_id
    option_id = shares[0].option_id

    seen: set[int] = set()
    for share in shares:
        if share.guardian_sequence in seen:
            raise DuplicateGuardianShareError(
                f"guardian {share.guardian_sequence} presented two shares for "
                f"{contest_id}/{option_id}"
            )
        seen.add(share.guardian_sequence)
        if (share.contest_id, share.option_id) != (contest_id, option_id):
            raise ThresholdMismatchError(
                "shares for different contests or options cannot be combined"
            )

    if len(shares) < policy.quorum:
        raise InsufficientQuorumError(
            f"{len(shares)} shares presented; the ceremony fixed a quorum of "
            f"{policy.quorum} of {policy.guardian_count} and it may not be reduced"
        )

    for share in shares:
        ok, detail = verify_share(share, ciphertext, transcript, params)
        if not ok:
            raise InvalidShareProofError(f"guardian {share.guardian_sequence}: {detail}")

    selection = tuple(sorted(seen))
    combined = 1
    for share in shares:
        weight = lagrange_coefficient(share.guardian_sequence, selection, params.q)
        combined = combined * pow(share.share, weight, params.p) % params.p

    group_value = ciphertext.beta * pow(combined, params.p - 2, params.p) % params.p
    return decode_exponent(group_value, params, maximum=maximum)


def quorum_digest(transcript: CeremonyTranscript, params: ParameterSet) -> bytes:
    """A digest binding the quorum policy to this ceremony and election.

    Published in the election record so that a verifier compares the
    quorum it was told about with the quorum the ceremony actually ran.
    """
    payload = encode_struct(
        [
            ("election_context_id", encode_text(transcript.election_context_id)),
            ("parameter_set_id", encode_text(params.parameter_set_id)),
            ("policy", transcript.policy.canonical_bytes()),
            (
                "joint_public_key",
                encode_group_element(transcript.joint_public_key, params.p_bytes),
            ),
        ]
    )
    return h_q(ZERO_KEY, DomainLabel.GUARDIAN_COMMITMENT, [payload], params.q).to_bytes(
        params.q_bytes, "big"
    )

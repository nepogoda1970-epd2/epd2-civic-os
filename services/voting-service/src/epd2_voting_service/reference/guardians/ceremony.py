"""Threshold guardian key ceremony — reference implementation.

PACK-16B fixes a `k`-of-`n` guardian model: **3-of-5 by default, 4-of-7 for
high assurance**. PACK-16D's first candidate implemented one guardian and
one decryption share, which is not that model. This module implements the
threshold path.

**What this is.** A Feldman verifiable-secret-sharing distributed key
generation, in the shape ElectionGuard uses:

* guardian `i` draws a secret polynomial `P_i` of degree `k-1` over `Z_q`;
* it publishes commitments `K_{i,j} = g^{a_{i,j}} mod p` to every
  coefficient, and a Schnorr proof of possession of `a_{i,0}`;
* it sends guardian `l` the share `P_i(l) mod q`, which `l` verifies
  against the published commitments — a wrong share is *detectable*, which
  is the whole point of the commitments;
* guardian `l`'s secret key share is `s_l = sum_i P_i(l) mod q`;
* the joint public key is `K = prod_i K_{i,0}`, and the joint secret it
  corresponds to is `s = sum_i P_i(0)` — which no party ever holds.

Because `s_l = P(l)` for the summed polynomial `P`, the `s_l` are Shamir
shares of `s` at threshold `k`, and any `k` of them reconstruct a
decryption without reconstructing `s` itself.

**What this is not.** It is a *reference* ceremony, not a production one.
Shares are exchanged in-process rather than over an authenticated channel,
there is no HSM, no air gap, no human ceremony script and no key custody.
Those are PACK-17 and production obligations, recorded as such.

**Compensated decryption is deliberately absent.** ElectionGuard permits
available guardians to reconstruct a missing guardian's share. This
implementation does not, and `PACK-16D-THRESHOLD-GUARDIAN-REFERENCE-IMPLEMENTATION.md`
records why: a compensation path is a path by which `k` guardians recover
another guardian's secret, and the PACK-16B baseline prohibits it. A
missing guardian is handled by having enough others, not by reconstructing
them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_group_element,
    encode_scalar,
    encode_seq,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h, h_q
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    is_in_subgroup,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource

#: The two configurations PACK-16B fixes. The engine below is generic
#: `k`-of-`n`; these are the two the baseline names.
DEFAULT_QUORUM: tuple[int, int] = (3, 5)
HIGH_ASSURANCE_QUORUM: tuple[int, int] = (4, 7)


class GuardianErrorCode(StrEnum):
    """Reason codes this module can produce. Named, not stringly-typed."""

    THRESHOLD_MISMATCH = "guardian.threshold_mismatch"
    INSUFFICIENT_QUORUM = "guardian.insufficient_quorum"
    DUPLICATE_SHARE = "guardian.duplicate_share"
    INVALID_SHARE_PROOF = "guardian.invalid_share_proof"
    UNKNOWN_GUARDIAN = "guardian.unknown_guardian"


class GuardianConfigurationError(ValueError):
    reason_code = "GUARDIAN_THRESHOLD_MISMATCH"


class ThresholdMismatchError(ValueError):
    reason_code = "GUARDIAN_THRESHOLD_MISMATCH"


class InsufficientQuorumError(ValueError):
    reason_code = "GUARDIAN_INSUFFICIENT_QUORUM"


class DuplicateGuardianShareError(ValueError):
    reason_code = "GUARDIAN_DUPLICATE_SHARE"


class InvalidShareProofError(ValueError):
    reason_code = "GUARDIAN_INVALID_SHARE_PROOF"


class UnknownGuardianError(LookupError):
    reason_code = "GUARDIAN_UNKNOWN_GUARDIAN"


class CompensatedDecryptionProhibited(RuntimeError):
    """Raised by the placeholder that exists only to be unreachable.

    A reader looking for compensated decryption finds this and its reason,
    rather than finding nothing and assuming the feature was forgotten.
    """

    reason_code = "GUARDIAN_COMPENSATION_PROHIBITED"


@dataclass(frozen=True, slots=True)
class QuorumPolicy:
    """`k`-of-`n`, validated once and then immutable.

    The policy is bound into the election context, the ceremony transcript,
    the joint-key artefact and the election record, so that a later party
    cannot decide a smaller `k` is acceptable.
    """

    quorum: int
    guardian_count: int

    def validate(self) -> QuorumPolicy:
        if self.guardian_count < 1:
            raise GuardianConfigurationError("guardian count must be positive")
        if self.quorum < 1:
            raise GuardianConfigurationError("quorum must be positive")
        if self.quorum > self.guardian_count:
            raise GuardianConfigurationError(
                f"quorum {self.quorum} exceeds guardian count {self.guardian_count}"
            )
        if self.quorum * 2 <= self.guardian_count:
            # Not a cryptographic requirement, but a governance one: a
            # quorum at or below half the roster means two disjoint sets
            # could each decrypt, which defeats the point of the threshold.
            raise GuardianConfigurationError(
                f"quorum {self.quorum} of {self.guardian_count} allows two disjoint "
                "decrypting sets; a majority quorum is required"
            )
        return self

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("quorum", encode_uint(self.quorum, 4)),
                ("guardian_count", encode_uint(self.guardian_count, 4)),
            ]
        )


@dataclass(frozen=True, slots=True)
class SchnorrProof:
    """Proof of possession of the constant term of a guardian polynomial."""

    commitment: int
    challenge: int
    response: int

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("commitment", encode_group_element(self.commitment, params.p_bytes)),
                ("challenge", encode_scalar(self.challenge, params.q_bytes)),
                ("response", encode_scalar(self.response, params.q_bytes)),
            ]
        )


@dataclass(frozen=True, slots=True)
class GuardianRecord:
    """The public record of one guardian. Carries no secret.

    `guardian_id` is election-scoped and is **not** an account, member or
    voter identity: it names a role in one ceremony and nothing else.
    """

    guardian_id: str
    guardian_sequence: int
    election_context_id: str
    coefficient_commitments: tuple[int, ...]
    proof_of_possession: SchnorrProof

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("guardian_id", encode_text(self.guardian_id)),
                ("guardian_sequence", encode_uint(self.guardian_sequence, 4)),
                ("election_context_id", encode_text(self.election_context_id)),
                (
                    "coefficient_commitments",
                    encode_seq(
                        [
                            encode_group_element(c, params.p_bytes)
                            for c in self.coefficient_commitments
                        ]
                    ),
                ),
                ("proof_of_possession", self.proof_of_possession.canonical_bytes(params)),
            ]
        )


@dataclass(frozen=True, slots=True)
class GuardianSecret:
    """A guardian's private material. Never published, never in a record."""

    guardian_id: str
    guardian_sequence: int
    #: The guardian's own polynomial coefficients.
    coefficients: tuple[int, ...]
    #: `s_l = sum_i P_i(l)`, the guardian's share of the joint secret.
    secret_key_share: int


@dataclass(frozen=True, slots=True)
class CeremonyTranscript:
    """The public, verifiable outcome of a ceremony."""

    election_context_id: str
    policy: QuorumPolicy
    guardians: tuple[GuardianRecord, ...]
    joint_public_key: int
    parameter_set_id: str
    complete: bool

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("election_context_id", encode_text(self.election_context_id)),
                ("parameter_set_id", encode_text(self.parameter_set_id)),
                ("policy", self.policy.canonical_bytes()),
                (
                    "guardians",
                    encode_seq([g.canonical_bytes(params) for g in self.guardians]),
                ),
                (
                    "joint_public_key",
                    encode_group_element(self.joint_public_key, params.p_bytes),
                ),
                ("complete", encode_bytes(b"\x01" if self.complete else b"\x00")),
            ]
        )

    def digest(self, params: ParameterSet) -> bytes:
        return h(ZERO_KEY, DomainLabel.CEREMONY_TRANSCRIPT, [self.canonical_bytes(params)])

    def guardian(self, sequence: int) -> GuardianRecord:
        for record in self.guardians:
            if record.guardian_sequence == sequence:
                return record
        raise UnknownGuardianError(f"no guardian with sequence {sequence} in this ceremony")


# -- polynomial and commitment helpers -----------------------------------


def _evaluate(coefficients: tuple[int, ...], x: int, q: int) -> int:
    """Horner evaluation of a polynomial over `Z_q`."""
    value = 0
    for coefficient in reversed(coefficients):
        value = (value * x + coefficient) % q
    return value


def _commitment_product(commitments: tuple[int, ...], x: int, params: ParameterSet) -> int:
    """`prod_j K_j^(x^j) mod p` — the public image of `P(x)`."""
    result = 1
    exponent = 1
    for commitment in commitments:
        result = result * pow(commitment, exponent, params.p) % params.p
        exponent = exponent * x % params.q
    return result


def _proof_challenge(
    guardian_id: str,
    election_context_id: str,
    public_key: int,
    commitment: int,
    params: ParameterSet,
) -> int:
    payload = encode_struct(
        [
            ("guardian_id", encode_text(guardian_id)),
            ("election_context_id", encode_text(election_context_id)),
            ("parameter_set_id", encode_text(params.parameter_set_id)),
            ("public_key", encode_group_element(public_key, params.p_bytes)),
            ("commitment", encode_group_element(commitment, params.p_bytes)),
        ]
    )
    return h_q(ZERO_KEY, DomainLabel.GUARDIAN_PROOF, [payload], params.q)


def prove_possession(
    guardian_id: str,
    election_context_id: str,
    secret: int,
    params: ParameterSet,
    source: RandomSource,
) -> SchnorrProof:
    """Schnorr proof of knowledge of the polynomial's constant term."""
    public_key = pow(params.g, secret, params.p)
    nonce = 1 + source.random_below(params.q - 1)
    commitment = pow(params.g, nonce, params.p)
    challenge = _proof_challenge(guardian_id, election_context_id, public_key, commitment, params)
    response = (nonce + challenge * secret) % params.q
    return SchnorrProof(commitment=commitment, challenge=challenge, response=response)


def verify_possession(record: GuardianRecord, params: ParameterSet) -> bool:
    """Verify a guardian actually holds the secret behind its commitment."""
    if not record.coefficient_commitments:
        return False
    public_key = record.coefficient_commitments[0]
    proof = record.proof_of_possession
    for element in (public_key, proof.commitment):
        if not is_in_subgroup(element, params):
            return False
    if not 0 <= proof.challenge < params.q or not 0 <= proof.response < params.q:
        return False
    expected = _proof_challenge(
        record.guardian_id,
        record.election_context_id,
        public_key,
        proof.commitment,
        params,
    )
    if expected != proof.challenge:
        return False
    left = pow(params.g, proof.response, params.p)
    right = proof.commitment * pow(public_key, proof.challenge, params.p) % params.p
    return left == right


def verify_share(
    share: int,
    receiver_sequence: int,
    commitments: tuple[int, ...],
    params: ParameterSet,
) -> bool:
    """Feldman check: `g^share == prod_j K_j^(l^j)`.

    This is what makes the ceremony *verifiable* — a guardian that sends a
    wrong share is caught by the receiver rather than discovered at tally
    time.
    """
    if not 0 <= share < params.q:
        return False
    for commitment in commitments:
        if not is_in_subgroup(commitment, params):
            return False
    left = pow(params.g, share, params.p)
    return left == _commitment_product(commitments, receiver_sequence, params)


# -- the ceremony --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CeremonyResult:
    transcript: CeremonyTranscript
    secrets: tuple[GuardianSecret, ...]

    def secret(self, sequence: int) -> GuardianSecret:
        for value in self.secrets:
            if value.guardian_sequence == sequence:
                return value
        raise UnknownGuardianError(f"no guardian with sequence {sequence}")


def run_ceremony(
    election_context_id: str,
    policy: QuorumPolicy,
    params: ParameterSet,
    source: RandomSource,
    *,
    guardian_ids: tuple[str, ...] | None = None,
    corrupt_share_from: int | None = None,
) -> CeremonyResult:
    """Run a full reference DKG and return the transcript plus the secrets.

    The secrets are returned because a *reference* ceremony has to hand
    them to the test that will decrypt with them. In production they never
    leave the guardian's own custody, which is exactly the property this
    implementation does not model — see the module docstring.

    `corrupt_share_from` makes one guardian send a share that does not
    match its commitments, so the complaint path can be exercised.
    """
    policy.validate()
    if guardian_ids is None:
        guardian_ids = tuple(f"guardian-{index + 1}" for index in range(policy.guardian_count))
    if len(guardian_ids) != policy.guardian_count:
        raise GuardianConfigurationError(
            f"{len(guardian_ids)} guardian ids for {policy.guardian_count} guardians"
        )

    sequences = tuple(range(1, policy.guardian_count + 1))
    coefficients: dict[int, tuple[int, ...]] = {}
    commitments: dict[int, tuple[int, ...]] = {}
    records: list[GuardianRecord] = []

    for guardian_id, sequence in zip(guardian_ids, sequences, strict=True):
        own = tuple(1 + source.random_below(params.q - 1) for _ in range(policy.quorum))
        coefficients[sequence] = own
        commitments[sequence] = tuple(pow(params.g, a, params.p) for a in own)
        records.append(
            GuardianRecord(
                guardian_id=guardian_id,
                guardian_sequence=sequence,
                election_context_id=election_context_id,
                coefficient_commitments=commitments[sequence],
                proof_of_possession=prove_possession(
                    guardian_id, election_context_id, own[0], params, source
                ),
            )
        )

    # Share exchange, with every received share verified against the
    # sender's published commitments before it is accepted.
    secret_shares: dict[int, int] = dict.fromkeys(sequences, 0)
    for sender in sequences:
        for receiver in sequences:
            share = _evaluate(coefficients[sender], receiver, params.q)
            if corrupt_share_from == sender and receiver != sender:
                share = (share + 1) % params.q
            if not verify_share(share, receiver, commitments[sender], params):
                raise InvalidShareProofError(
                    f"guardian {sender} sent guardian {receiver} a share that does "
                    "not match its published commitments"
                )
            secret_shares[receiver] = (secret_shares[receiver] + share) % params.q

    for record in records:
        if not verify_possession(record, params):
            raise InvalidShareProofError(
                f"guardian {record.guardian_sequence} failed its proof of possession"
            )

    joint_public_key = 1
    for sequence in sequences:
        joint_public_key = joint_public_key * commitments[sequence][0] % params.p

    transcript = CeremonyTranscript(
        election_context_id=election_context_id,
        policy=policy,
        guardians=tuple(records),
        joint_public_key=joint_public_key,
        parameter_set_id=params.parameter_set_id,
        complete=True,
    )
    secrets = tuple(
        GuardianSecret(
            guardian_id=record.guardian_id,
            guardian_sequence=record.guardian_sequence,
            coefficients=coefficients[record.guardian_sequence],
            secret_key_share=secret_shares[record.guardian_sequence],
        )
        for record in records
    )
    return CeremonyResult(transcript=transcript, secrets=secrets)


def derive_joint_public_key(transcript: CeremonyTranscript, params: ParameterSet) -> int:
    """Re-derive the joint key from the commitments alone.

    A verifier must never accept the joint public key as a standalone
    value: it is a *derived* quantity, and deriving it is how a verifier
    learns that the guardians in the roster are the ones who made it.
    """
    joint = 1
    for record in transcript.guardians:
        if not record.coefficient_commitments:
            raise InvalidShareProofError(
                f"guardian {record.guardian_sequence} published no commitments"
            )
        joint = joint * record.coefficient_commitments[0] % params.p
    return joint


def guardian_public_share_key(
    transcript: CeremonyTranscript, sequence: int, params: ParameterSet
) -> int:
    """`g^(s_l)`, computed from public commitments only.

    This is what lets a verifier check guardian `l`'s decryption share
    without ever seeing `s_l`.
    """
    transcript.guardian(sequence)  # raises UnknownGuardianError
    value = 1
    for record in transcript.guardians:
        value = (
            value * _commitment_product(record.coefficient_commitments, sequence, params) % params.p
        )
    return value


def verify_ceremony(transcript: CeremonyTranscript, params: ParameterSet) -> tuple[bool, str]:
    """Full public verification of a ceremony transcript."""
    if transcript.parameter_set_id != params.parameter_set_id:
        return False, "ceremony was run under a different parameter set"
    try:
        transcript.policy.validate()
    except GuardianConfigurationError as exc:
        return False, str(exc)
    if len(transcript.guardians) != transcript.policy.guardian_count:
        return False, "roster size does not match the declared guardian count"
    sequences = [record.guardian_sequence for record in transcript.guardians]
    if sorted(sequences) != list(range(1, transcript.policy.guardian_count + 1)):
        return False, "guardian sequences are not 1..n without gaps or duplicates"
    if len({record.guardian_id for record in transcript.guardians}) != len(sequences):
        return False, "duplicate guardian id in the roster"
    for record in transcript.guardians:
        if len(record.coefficient_commitments) != transcript.policy.quorum:
            return False, (
                f"guardian {record.guardian_sequence} published "
                f"{len(record.coefficient_commitments)} commitments for a quorum of "
                f"{transcript.policy.quorum}"
            )
        if record.election_context_id != transcript.election_context_id:
            return False, f"guardian {record.guardian_sequence} names another election"
        if not verify_possession(record, params):
            return False, (f"guardian {record.guardian_sequence} failed its proof of possession")
    if derive_joint_public_key(transcript, params) != transcript.joint_public_key:
        return False, "joint public key does not derive from the published commitments"
    if not transcript.complete:
        return False, "ceremony is not marked complete"
    return True, ""


def compensated_decryption_share(*_args: object, **_kwargs: object) -> None:
    """Not implemented, and deliberately so.

    ElectionGuard permits available guardians to reconstruct a missing
    guardian's decryption share. That is a path by which a quorum recovers
    another guardian's secret material, and the PACK-16B baseline
    prohibits it. This function exists so the prohibition is discoverable
    in the code rather than only in a document.
    """
    raise CompensatedDecryptionProhibited(
        "compensated decryption is prohibited by the EPD2 baseline: a missing "
        "guardian is covered by having enough others, never by reconstructing "
        "the missing one"
    )

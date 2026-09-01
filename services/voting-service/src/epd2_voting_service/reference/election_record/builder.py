"""Deterministic election-record builder, including the tally (PACK-16D §34).

`build_record` is a pure function of its canonical inputs: the same inputs
always produce byte-identical output, which is what makes the record
digest meaningful.

The **no-intermediate-tally** invariant is enforced here in code, not in
configuration: `open_tally` raises unless the board is closed, and there is
no flag, argument or environment variable that relaxes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epd2_voting_service.reference.casting.ballot import BallotEnvelope, Manifest
from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.elgamal import (
    Ciphertext,
    accumulate,
    decode_exponent,
)
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_seq,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h
from epd2_voting_service.reference.crypto.parameters import ParameterSet
from epd2_voting_service.reference.crypto.proofs import (
    ChaumPedersenProof,
    prove_decryption_share,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource
from epd2_voting_service.reference.guardians.ceremony import (
    CeremonyTranscript,
    GuardianSecret,
)
from epd2_voting_service.reference.guardians.threshold import ThresholdShare
from epd2_voting_service.reference.hooks import FaultHook, trip
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchOpening,
    LeafClass,
    SealedBatch,
)


class IntermediateTallyProhibitedError(RuntimeError):
    """Hard invariant. No feature flag can disable this."""

    reason_code = "TALLY_PRE_CLOSURE_PROHIBITED"


class ReconciliationError(ValueError):
    reason_code = "BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED"


@dataclass(frozen=True, slots=True)
class GuardianShare:
    contest_id: str
    option_id: str
    guardian_index: int
    guardian_public: int
    share: int
    proof: ChaumPedersenProof


@dataclass(frozen=True, slots=True)
class ContestTally:
    contest_id: str
    option_id: str
    encrypted: Ciphertext
    plaintext: int


@dataclass(frozen=True, slots=True)
class ReconciliationRecord:
    accepted_cast: int
    public_challenged_spoiled: int
    cover: int
    max_valid_continuations: int
    k: int
    a: int

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("accepted_cast", encode_uint(self.accepted_cast, 8)),
                (
                    "public_challenged_spoiled",
                    encode_uint(self.public_challenged_spoiled, 8),
                ),
                ("cover", encode_uint(self.cover, 8)),
                ("E", encode_uint(self.max_valid_continuations, 8)),
                ("K", encode_uint(self.k, 4)),
                ("A", encode_uint(self.a, 4)),
            ]
        )


@dataclass(frozen=True, slots=True)
class ElectionRecord:
    manifest: Manifest
    params: ParameterSet
    joint_public_key: int
    base_hash: bytes
    sealed_batches: tuple[SealedBatch, ...]
    batch_openings: tuple[BatchOpening, ...]
    accepted_ballots: tuple[BallotEnvelope, ...]
    spoiled_ballots: tuple[BallotEnvelope, ...]
    reconciliation: ReconciliationRecord
    tallies: tuple[ContestTally, ...]
    shares: tuple[GuardianShare, ...] = field(default=())
    #: The guardian ceremony this election's joint key came from. A record
    #: without it cannot be verified: the joint public key is a derived
    #: quantity and must never be accepted standalone.
    ceremony: CeremonyTranscript | None = field(default=None)
    #: Threshold decryption shares, one per guardian per tallied option.
    threshold_shares: tuple[ThresholdShare, ...] = field(default=())

    def canonical_bytes(self) -> bytes:
        pw = self.params.p_bytes
        return encode_struct(
            [
                ("manifest", self.manifest.canonical_bytes()),
                ("parameter_set", self.params.canonical_bytes()),
                (
                    "joint_public_key",
                    encode_uint(self.joint_public_key, pw),
                ),
                ("base_hash", encode_bytes(self.base_hash)),
                (
                    "sealed_batches",
                    encode_seq([b.canonical_bytes() for b in self.sealed_batches]),
                ),
                (
                    "accepted_ballots",
                    encode_seq([b.canonical_bytes(self.params) for b in self.accepted_ballots]),
                ),
                (
                    "spoiled_ballots",
                    encode_seq([b.canonical_bytes(self.params) for b in self.spoiled_ballots]),
                ),
                (
                    "batch_openings",
                    encode_seq(
                        [
                            encode_struct(
                                [
                                    ("batch_sequence", encode_uint(o.batch_sequence, 8)),
                                    ("leaves", encode_seq(list(o.leaves))),
                                    (
                                        "openings",
                                        encode_seq([lo.canonical_bytes() for lo in o.openings]),
                                    ),
                                ]
                            )
                            for o in self.batch_openings
                        ]
                    ),
                ),
                ("reconciliation", self.reconciliation.canonical_bytes()),
                (
                    "tallies",
                    encode_seq(
                        [
                            encode_struct(
                                [
                                    ("contest_id", encode_text(t.contest_id)),
                                    ("option_id", encode_text(t.option_id)),
                                    ("encrypted", t.encrypted.canonical_bytes(self.params)),
                                    ("plaintext", encode_uint(t.plaintext, 8)),
                                ]
                            )
                            for t in self.tallies
                        ]
                    ),
                ),
                (
                    "ceremony",
                    self.ceremony.canonical_bytes(self.params)
                    if self.ceremony is not None
                    else encode_text(""),
                ),
                (
                    "threshold_shares",
                    encode_seq([t.canonical_bytes(self.params) for t in self.threshold_shares]),
                ),
                (
                    "shares",
                    encode_seq(
                        [
                            encode_struct(
                                [
                                    ("contest_id", encode_text(s.contest_id)),
                                    ("option_id", encode_text(s.option_id)),
                                    ("guardian_index", encode_uint(s.guardian_index, 4)),
                                    (
                                        "guardian_public",
                                        encode_uint(s.guardian_public, pw),
                                    ),
                                    ("share", encode_uint(s.share, pw)),
                                    ("proof", s.proof.canonical_bytes(self.params)),
                                ]
                            )
                            for s in self.shares
                        ]
                    ),
                ),
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.ELECTION_RECORD, [self.canonical_bytes()])


def open_tally(board_closed: bool) -> None:
    """The hard gate. Called before any tally construction."""
    if not board_closed:
        raise IntermediateTallyProhibitedError(
            "no tally artefact may be constructed before the closure checkpoint"
        )


def tally_accepted(
    accepted: list[BallotEnvelope],
    manifest: Manifest,
    params: ParameterSet,
    secret: int,
    guardian_public: int,
    source: RandomSource,
    *,
    board_closed: bool,
) -> tuple[list[ContestTally], list[GuardianShare]]:
    """Homomorphic accumulation, share decryption and bounded decode."""
    open_tally(board_closed)
    tallies: list[ContestTally] = []
    shares: list[GuardianShare] = []
    style = manifest.ballot_styles[0]
    for contest in style.contests:
        for option_id in contest.option_ids:
            gathered = [
                selection.ciphertext
                for envelope in accepted
                for encrypted_contest in envelope.contests
                if encrypted_contest.contest_id == contest.contest_id
                for selection in encrypted_contest.selections
                if selection.option_id == option_id
            ]
            if not gathered:
                continue
            aggregate = accumulate(gathered, params)
            share = pow(aggregate.alpha, secret, params.p)
            # The context binds the share to the contest and option it
            # decrypts. A bare label would let a share proved for one
            # option be presented for another.
            share_context = encode_struct(
                [
                    ("label", encode_text("tally")),
                    ("election_context_id", encode_text(manifest.election_context_id)),
                    ("contest_id", encode_text(contest.contest_id)),
                    ("option_id", encode_text(option_id)),
                ]
            )
            proof = prove_decryption_share(
                aggregate.alpha,
                share,
                secret,
                guardian_public,
                params,
                share_context,
                source,
            )
            shares.append(
                GuardianShare(
                    contest_id=contest.contest_id,
                    option_id=option_id,
                    guardian_index=1,
                    guardian_public=guardian_public,
                    share=share,
                    proof=proof,
                )
            )
            group_value = aggregate.beta * pow(share, params.p - 2, params.p) % params.p
            plaintext = decode_exponent(group_value, params, maximum=len(accepted))
            tallies.append(
                ContestTally(
                    contest_id=contest.contest_id,
                    option_id=option_id,
                    encrypted=aggregate,
                    plaintext=plaintext,
                )
            )
    return tallies, shares


def reconcile(
    openings: list[BatchOpening],
    accepted: list[BallotEnvelope],
    spoiled: list[BallotEnvelope],
    max_valid_continuations: int,
) -> ReconciliationRecord:
    """Every artefact maps to exactly one leaf and back. Fail closed."""
    counts = {
        LeafClass.ACCEPTED_CAST: 0,
        LeafClass.PUBLIC_CHALLENGED_SPOILED: 0,
        LeafClass.COVER: 0,
    }
    seen: set[str] = set()
    for opening in openings:
        for leaf_opening in opening.openings:
            counts[leaf_opening.leaf_class] += 1
            if leaf_opening.leaf_class is LeafClass.COVER:
                continue
            if leaf_opening.artifact_reference in seen:
                raise ReconciliationError(
                    f"artefact {leaf_opening.artifact_reference} maps to two leaves"
                )
            seen.add(leaf_opening.artifact_reference)
    accepted_ids = {e.ballot_id for e in accepted}
    spoiled_ids = {e.ballot_id for e in spoiled}
    if counts[LeafClass.ACCEPTED_CAST] != len(accepted_ids):
        raise ReconciliationError("accepted-cast leaves do not match accepted ballots")
    if counts[LeafClass.PUBLIC_CHALLENGED_SPOILED] != len(spoiled_ids):
        raise ReconciliationError("spoiled leaves do not match spoiled ballots")
    if not (accepted_ids | spoiled_ids) <= seen:
        raise ReconciliationError("an artefact has no committed leaf")
    if len(accepted_ids) > max_valid_continuations:
        raise ReconciliationError("accepted casts exceed E")
    if len(spoiled_ids) > max_valid_continuations:
        raise ReconciliationError("public challenges exceed E * K")
    return ReconciliationRecord(
        accepted_cast=counts[LeafClass.ACCEPTED_CAST],
        public_challenged_spoiled=counts[LeafClass.PUBLIC_CHALLENGED_SPOILED],
        cover=counts[LeafClass.COVER],
        max_valid_continuations=max_valid_continuations,
        k=1,
        a=1,
    )


def export_record(record: ElectionRecord, *, fault_hook: FaultHook | None = None) -> bytes:
    """Serialise the record for archival.

    Export is a pure function of the record: a crash here loses no state
    and the caller simply exports again. The fault point exists so that
    property can be demonstrated rather than asserted.
    """
    trip(fault_hook, "during_record_export")
    return record.canonical_bytes()


def decryption_share_context(election_context_id: str, contest_id: str, option_id: str) -> bytes:
    """The Fiat-Shamir context a decryption-share proof is bound to.

    Exported so the verifier derives it independently rather than being
    handed a context by the party whose proof it is checking.
    """
    return encode_struct(
        [
            ("label", encode_text("tally")),
            ("election_context_id", encode_text(election_context_id)),
            ("contest_id", encode_text(contest_id)),
            ("option_id", encode_text(option_id)),
        ]
    )


def tally_accepted_threshold(
    accepted: list[BallotEnvelope],
    manifest: Manifest,
    params: ParameterSet,
    ceremony: CeremonyTranscript,
    secrets: tuple[GuardianSecret, ...],
    source: RandomSource,
    *,
    board_closed: bool,
    quorum_selection: tuple[int, ...] | None = None,
) -> tuple[list[ContestTally], list[ThresholdShare]]:
    """Homomorphic accumulation followed by *threshold* decryption.

    This is the multi-guardian replacement for `tally_accepted`. The quorum
    is taken from the ceremony transcript, never from the caller: passing a
    `quorum_selection` chooses *which* guardians take part, not *how many*
    are required, and a selection smaller than the ceremony's `k` is
    refused inside `combine_shares`.
    """
    from epd2_voting_service.reference.guardians.threshold import (
        combine_shares,
        compute_share,
    )

    open_tally(board_closed)
    transcript = ceremony
    selection = quorum_selection or tuple(
        record.guardian_sequence for record in transcript.guardians[: transcript.policy.quorum]
    )
    by_sequence = {secret.guardian_sequence: secret for secret in secrets}

    tallies: list[ContestTally] = []
    all_shares: list[ThresholdShare] = []
    style = manifest.ballot_styles[0]
    for contest in style.contests:
        for option_id in contest.option_ids:
            gathered = [
                selection_ct.ciphertext
                for envelope in accepted
                for encrypted_contest in envelope.contests
                if encrypted_contest.contest_id == contest.contest_id
                for selection_ct in encrypted_contest.selections
                if selection_ct.option_id == option_id
            ]
            if not gathered:
                continue
            aggregate = accumulate(gathered, params)
            shares = [
                compute_share(
                    aggregate,
                    by_sequence[sequence],
                    transcript,
                    params,
                    contest.contest_id,
                    option_id,
                    source,
                )
                for sequence in selection
            ]
            plaintext = combine_shares(
                shares,
                aggregate,
                transcript,
                params,
                maximum=len(accepted),
            )
            all_shares.extend(shares)
            tallies.append(
                ContestTally(
                    contest_id=contest.contest_id,
                    option_id=option_id,
                    encrypted=aggregate,
                    plaintext=plaintext,
                )
            )
    return tallies, all_shares

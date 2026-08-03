"""Ballot construction, canonical envelope and ballot identity (PACK-16D §19).

Four identity values are kept structurally distinct, as `BP-*` requires:

* ``internal_object_id``  operational only, never published;
* ``ballot_id``           the public reference: client-random, election
                          scoped, non-sequential, derived from nothing;
* ``confirmation_code``   derived from the encryptions and ``H_E``;
* board position          assigned at publication, never here.

`ballot_id` is drawn from the random source and is deliberately *not* a
function of identity, credential, capability or content, so no published
value can be walked back to a person.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.elgamal import (
    Ciphertext,
    accumulate,
    encrypt,
    random_nonce,
    validate_ciphertext,
)
from epd2_voting_service.reference.crypto.encoding import (
    encode_seq,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h
from epd2_voting_service.reference.crypto.parameters import ParameterSet
from epd2_voting_service.reference.crypto.proofs import (
    ChaumPedersenProof,
    DisjunctiveProof,
    prove_contest_sum,
    prove_selection,
    verify_contest_sum,
    verify_selection,
)
from epd2_voting_service.reference.crypto.randomness import RandomSource

BALLOT_ID_BYTES = 32


class BallotStructureError(ValueError):
    reason_code = "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH"


class OvervoteError(ValueError):
    reason_code = "BALLOT_PREPARATION_OVERVOTE"


@dataclass(frozen=True, slots=True)
class ContestDefinition:
    contest_id: str
    option_ids: tuple[str, ...]
    selection_limit: int

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("contest_id", encode_text(self.contest_id)),
                ("option_ids", encode_seq([encode_text(o) for o in self.option_ids])),
                ("selection_limit", encode_uint(self.selection_limit, 4)),
            ]
        )


@dataclass(frozen=True, slots=True)
class BallotStyle:
    ballot_style_id: str
    contests: tuple[ContestDefinition, ...]

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("ballot_style_id", encode_text(self.ballot_style_id)),
                ("contests", encode_seq([c.canonical_bytes() for c in self.contests])),
            ]
        )


@dataclass(frozen=True, slots=True)
class Manifest:
    election_context_id: str
    ballot_styles: tuple[BallotStyle, ...]

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("election_context_id", encode_text(self.election_context_id)),
                ("ballot_styles", encode_seq([s.canonical_bytes() for s in self.ballot_styles])),
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.MANIFEST, [self.canonical_bytes()])

    def style(self, ballot_style_id: str) -> BallotStyle:
        for style in self.ballot_styles:
            if style.ballot_style_id == ballot_style_id:
                return style
        raise BallotStructureError(f"unknown ballot style {ballot_style_id!r}")


@dataclass(frozen=True, slots=True)
class EncryptedSelection:
    option_id: str
    ciphertext: Ciphertext
    proof: DisjunctiveProof

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("option_id", encode_text(self.option_id)),
                ("ciphertext", self.ciphertext.canonical_bytes(params)),
                ("proof", self.proof.canonical_bytes(params)),
            ]
        )


@dataclass(frozen=True, slots=True)
class EncryptedContest:
    contest_id: str
    selections: tuple[EncryptedSelection, ...]
    accumulated: Ciphertext
    sum_proof: ChaumPedersenProof

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("contest_id", encode_text(self.contest_id)),
                (
                    "selections",
                    encode_seq([s.canonical_bytes(params) for s in self.selections]),
                ),
                ("accumulated", self.accumulated.canonical_bytes(params)),
                ("sum_proof", self.sum_proof.canonical_bytes(params)),
            ]
        )


@dataclass(frozen=True, slots=True)
class BallotEnvelope:
    """The canonical wire object. Carries no identity of any kind."""

    ballot_id: str
    election_context_id: str
    ballot_style_id: str
    parameter_set_id: str
    manifest_digest: bytes
    contests: tuple[EncryptedContest, ...]

    def canonical_bytes(self, params: ParameterSet) -> bytes:
        return encode_struct(
            [
                ("ballot_id", encode_text(self.ballot_id)),
                ("election_context_id", encode_text(self.election_context_id)),
                ("ballot_style_id", encode_text(self.ballot_style_id)),
                ("parameter_set_id", encode_text(self.parameter_set_id)),
                ("manifest_digest", encode_uint(int.from_bytes(self.manifest_digest, "big"), 32)),
                ("contests", encode_seq([c.canonical_bytes(params) for c in self.contests])),
            ]
        )

    def digest(self, params: ParameterSet) -> bytes:
        return h(ZERO_KEY, DomainLabel.BALLOT_HASH, [self.canonical_bytes(params)])


@dataclass(frozen=True, slots=True)
class BallotOpening:
    """The nonces of a challenged ballot. Never produced for a cast ballot."""

    ballot_id: str
    nonces: tuple[tuple[str, int], ...]
    plaintexts: tuple[tuple[str, int], ...] = field(default=())


def new_ballot_id(source: RandomSource) -> str:
    """Client-random, structureless, election-scoped public reference."""
    return source.random_bytes(BALLOT_ID_BYTES).hex()


def _context_bytes(envelope_prefix: bytes, contest_id: str, option_id: str) -> bytes:
    return encode_struct(
        [
            ("prefix", envelope_prefix),
            ("contest_id", encode_text(contest_id)),
            ("option_id", encode_text(option_id)),
        ]
    )


def encrypt_ballot(
    manifest: Manifest,
    ballot_style_id: str,
    selections: dict[str, tuple[str, ...]],
    public_key: int,
    params: ParameterSet,
    base_hash: bytes,
    source: RandomSource,
) -> tuple[BallotEnvelope, BallotOpening]:
    """Encrypt a ballot and return the envelope plus its opening.

    The opening is returned to the *client only*. The cast path destroys
    it; only the public evidentiary challenge path ever publishes it.
    """
    style = manifest.style(ballot_style_id)
    ballot_id = new_ballot_id(source)
    prefix = encode_struct(
        [
            ("base_hash", encode_uint(int.from_bytes(base_hash, "big"), 32)),
            ("ballot_id", encode_text(ballot_id)),
        ]
    )
    contests: list[EncryptedContest] = []
    nonces: list[tuple[str, int]] = []
    plaintexts: list[tuple[str, int]] = []
    for contest in style.contests:
        chosen = tuple(selections.get(contest.contest_id, ()))
        unknown = set(chosen) - set(contest.option_ids)
        if unknown:
            raise BallotStructureError(f"unknown option(s) {sorted(unknown)}")
        if len(chosen) > contest.selection_limit:
            raise OvervoteError(
                f"contest {contest.contest_id}: {len(chosen)} selections exceed "
                f"limit {contest.selection_limit}"
            )
        encrypted: list[EncryptedSelection] = []
        nonce_sum = 0
        # Real options first, then placeholders that absorb the undervote so
        # that every contest accumulates to exactly its selection limit.
        option_plaintexts = [(o, 1 if o in chosen else 0) for o in contest.option_ids]
        placeholders = contest.selection_limit - len(chosen)
        for index in range(contest.selection_limit):
            option_plaintexts.append(
                (f"{contest.contest_id}#placeholder-{index}", 1 if index < placeholders else 0)
            )
        for option_id, message in option_plaintexts:
            nonce = random_nonce(params, source)
            ciphertext = encrypt(message, nonce, public_key, params)
            context = _context_bytes(prefix, contest.contest_id, option_id)
            proof = prove_selection(ciphertext, nonce, message, public_key, params, context, source)
            encrypted.append(EncryptedSelection(option_id, ciphertext, proof))
            nonces.append((option_id, nonce))
            plaintexts.append((option_id, message))
            nonce_sum = (nonce_sum + nonce) % params.q
        accumulated = accumulate([s.ciphertext for s in encrypted], params)
        sum_context = _context_bytes(prefix, contest.contest_id, "#sum")
        sum_proof = prove_contest_sum(
            accumulated,
            nonce_sum,
            contest.selection_limit,
            public_key,
            params,
            sum_context,
            source,
        )
        contests.append(
            EncryptedContest(
                contest_id=contest.contest_id,
                selections=tuple(encrypted),
                accumulated=accumulated,
                sum_proof=sum_proof,
            )
        )
    envelope = BallotEnvelope(
        ballot_id=ballot_id,
        election_context_id=manifest.election_context_id,
        ballot_style_id=ballot_style_id,
        parameter_set_id=params.parameter_set_id,
        manifest_digest=manifest.digest(),
        contests=tuple(contests),
    )
    opening = BallotOpening(ballot_id=ballot_id, nonces=tuple(nonces), plaintexts=tuple(plaintexts))
    return envelope, opening


def verify_ballot_proofs(
    envelope: BallotEnvelope,
    manifest: Manifest,
    public_key: int,
    params: ParameterSet,
    base_hash: bytes,
) -> None:
    """Full structural and cryptographic validation. Raises on any failure."""
    if envelope.election_context_id != manifest.election_context_id:
        raise BallotStructureError("election context mismatch")
    if envelope.manifest_digest != manifest.digest():
        raise BallotStructureError("manifest digest mismatch")
    if envelope.parameter_set_id != params.parameter_set_id:
        raise BallotStructureError("parameter set mismatch")
    style = manifest.style(envelope.ballot_style_id)
    if len(envelope.contests) != len(style.contests):
        raise BallotStructureError("contest count does not match the ballot style")
    prefix = encode_struct(
        [
            ("base_hash", encode_uint(int.from_bytes(base_hash, "big"), 32)),
            ("ballot_id", encode_text(envelope.ballot_id)),
        ]
    )
    for defined, submitted in zip(style.contests, envelope.contests, strict=True):
        if defined.contest_id != submitted.contest_id:
            raise BallotStructureError("contest order does not match the ballot style")
        expected = len(defined.option_ids) + defined.selection_limit
        if len(submitted.selections) != expected:
            raise BallotStructureError(
                f"contest {defined.contest_id}: expected {expected} selections, "
                f"got {len(submitted.selections)}"
            )
        for selection in submitted.selections:
            validate_ciphertext(selection.ciphertext, params)
            context = _context_bytes(prefix, defined.contest_id, selection.option_id)
            if not verify_selection(
                selection.ciphertext, selection.proof, public_key, params, context
            ):
                raise BallotStructureError(f"selection proof failed for {selection.option_id!r}")
        recomputed = accumulate([s.ciphertext for s in submitted.selections], params)
        if (recomputed.alpha, recomputed.beta) != (
            submitted.accumulated.alpha,
            submitted.accumulated.beta,
        ):
            raise BallotStructureError("accumulated ciphertext does not recompute")
        sum_context = _context_bytes(prefix, defined.contest_id, "#sum")
        if not verify_contest_sum(
            submitted.accumulated,
            submitted.sum_proof,
            defined.selection_limit,
            public_key,
            params,
            sum_context,
        ):
            raise BallotStructureError(f"contest sum proof failed for {defined.contest_id!r}")

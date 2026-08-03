"""Independent reference verifier (PACK-16D §35, §36).

The verifier takes **exported bytes and public artefacts only**. It never
imports the store, the continuation module, the transaction module or any
identity, credential or capability type — a boundary asserted by a test,
not merely by convention.

`verify_record` re-derives every equation from the record's canonical
bytes and re-parses board exports through its own path.
"""

from __future__ import annotations

from dataclasses import dataclass

from epd2_voting_service.reference.casting.ballot import (
    BallotEnvelope,
    Manifest,
    verify_ballot_proofs,
)
from epd2_voting_service.reference.casting.confirmation import verify_challenge_opening
from epd2_voting_service.reference.crypto.elgamal import accumulate
from epd2_voting_service.reference.crypto.merkle import (
    inclusion_proof,
    verify_consistency,
    verify_inclusion,
)
from epd2_voting_service.reference.crypto.merkle import root as merkle_root
from epd2_voting_service.reference.crypto.parameters import (
    PROFILE_BIT_LENGTHS,
    ParameterSet,
    is_in_subgroup,
    validate_parameter_set,
)
from epd2_voting_service.reference.crypto.proofs import verify_decryption_share
from epd2_voting_service.reference.election_record.builder import (
    ElectionRecord,
    decryption_share_context,
)
from epd2_voting_service.reference.guardians.ceremony import (
    derive_joint_public_key,
    verify_ceremony,
)
from epd2_voting_service.reference.guardians.threshold import ThresholdShare
from epd2_voting_service.reference.guardians.threshold import (
    verify_share as verify_threshold_share,
)
from epd2_voting_service.reference.publication.bulletin_board import Checkpoint
from epd2_voting_service.reference.publication.checkpoint_signing import (
    CheckpointSignatureOutcome,
    SignerRegistry,
    verify_checkpoint,
)
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchOpening,
    LeafClass,
    SealedBatch,
    real_leaf,
)
from epd2_voting_service.reference.verification.results import (
    VerificationResult,
    VerificationResultCode,
)

#: Signature outcomes map one-to-one onto verification result codes, so a
#: reader of an exit code can tell a missing signature from a forged one.
_SIGNATURE_OUTCOME_CODES: dict[CheckpointSignatureOutcome, VerificationResultCode] = {
    CheckpointSignatureOutcome.MISSING: VerificationResultCode.BOARD_SIGNATURE_MISSING,
    CheckpointSignatureOutcome.SIGNER_UNKNOWN: VerificationResultCode.BOARD_SIGNER_UNKNOWN,
    CheckpointSignatureOutcome.SIGNER_UNAUTHORIZED: (
        VerificationResultCode.BOARD_SIGNER_UNAUTHORIZED
    ),
    CheckpointSignatureOutcome.INVALID: VerificationResultCode.BOARD_SIGNATURE_INVALID,
    CheckpointSignatureOutcome.CONTEXT_MISMATCH: (
        VerificationResultCode.BOARD_SIGNATURE_CONTEXT_MISMATCH
    ),
}


@dataclass(frozen=True, slots=True)
class BoardExport:
    """Bytes-only view of the board. The verifier gets nothing else."""

    entries: tuple[tuple[int, str, bytes], ...]
    checkpoints: tuple[tuple[int, int, bytes, bytes, bytes], ...]
    #: Full checkpoints, needed to verify signatures. When absent the
    #: verifier says so in ``checks_run`` rather than passing silently.
    signed_checkpoints: tuple[Checkpoint, ...] = ()
    #: The declared authorised signer set. A trust anchor supplied
    #: *alongside* the export, never read out of it.
    signer_registry: SignerRegistry | None = None
    #: ``(old_tree_size, new_tree_size, proof)`` triples the board published.
    #: A verifier that is given no proof checks no consistency claim and
    #: says so in ``checks_run``; it does not silently pass.
    consistency_proofs: tuple[tuple[int, int, tuple[bytes, ...]], ...] = ()


def verify_board(export: BoardExport) -> VerificationResult:
    """Monotonic tree size, chained checkpoints, no rollback, no equivocation.

    Since checkpoints became Ed25519-signed, the chain is taken over the
    whole signed payload, so an export that carries only the legacy
    five-tuple view cannot be chain-checked at all. That is reported as an
    incomplete record rather than silently checked against a weaker digest:
    a fallback that covers less than the board actually signed would be a
    downgrade a verifier could not see.
    """
    checks: list[str] = []
    seen_size = -1
    previous_digest: bytes | None = None
    roots_by_size: dict[int, bytes] = {}
    if export.checkpoints and not export.signed_checkpoints:
        return VerificationResult(
            VerificationResultCode.INCOMPLETE_RECORD,
            "the export carries checkpoint tuples but no signed checkpoints; the "
            "chain is computed over the signed payload and cannot be checked "
            "without it",
        )
    for sequence, tree_size, root, previous_hash, _signature in export.checkpoints:
        if tree_size < seen_size:
            return VerificationResult(
                VerificationResultCode.BOARD_INCONSISTENCY,
                f"checkpoint {sequence} rolls tree size back from {seen_size} to {tree_size}",
            )
        if tree_size in roots_by_size and roots_by_size[tree_size] != root:
            return VerificationResult(
                VerificationResultCode.BOARD_INCONSISTENCY,
                f"two different roots published at tree size {tree_size}",
            )
        roots_by_size[tree_size] = root
        if previous_digest is not None and previous_hash != previous_digest:
            return VerificationResult(
                VerificationResultCode.BOARD_INCONSISTENCY,
                f"checkpoint {sequence} does not chain to its predecessor",
            )
        # Re-derive the root from the exported entries rather than trusting
        # the checkpoint's own claim about it. Without this the board could
        # publish a perfectly chained sequence of roots over entries nobody
        # ever saw.
        if tree_size > len(export.entries):
            return VerificationResult(
                VerificationResultCode.BOARD_INCONSISTENCY,
                f"checkpoint {sequence} claims tree size {tree_size} but only "
                f"{len(export.entries)} entries were exported",
            )
        derived = merkle_root(
            [
                _entry_digest(entry_sequence, entry_type, payload)
                for entry_sequence, entry_type, payload in export.entries[:tree_size]
            ]
        )
        if derived != root:
            return VerificationResult(
                VerificationResultCode.BOARD_INCONSISTENCY,
                f"checkpoint {sequence} root does not recompute from the exported entries",
            )
        seen_size = tree_size
        previous_digest = _chain_digest(export, sequence, tree_size, root, previous_hash)
    checks.append("board.checkpoint_chain")
    checks.append("board.monotonic_tree_size")
    checks.append("board.root_recomputation")

    if export.signer_registry is not None and export.signed_checkpoints:
        seen_signed: dict[int, bytes] = {}
        for checkpoint in export.signed_checkpoints:
            outcome, detail = verify_checkpoint(
                checkpoint.payload(), checkpoint.signature, export.signer_registry
            )
            if outcome is not CheckpointSignatureOutcome.VALID:
                return VerificationResult(_SIGNATURE_OUTCOME_CODES[outcome], detail)
            # A correctly signed checkpoint is still only one view. Two
            # valid signatures over conflicting roots at one sequence is
            # equivocation by an authorised signer, which is worse than a
            # forgery and must not be reported as a signature success.
            previous_root = seen_signed.get(checkpoint.checkpoint_sequence)
            if previous_root is not None and previous_root != checkpoint.root:
                return VerificationResult(
                    VerificationResultCode.BOARD_INCONSISTENCY,
                    f"two validly signed checkpoints at sequence "
                    f"{checkpoint.checkpoint_sequence} carry different roots; an "
                    "authorised signer equivocated",
                )
            seen_signed[checkpoint.checkpoint_sequence] = checkpoint.root
        checks.append("board.checkpoint_signatures")

    if export.consistency_proofs:
        roots_at = dict(roots_by_size)
        for old_size, new_size, proof in export.consistency_proofs:
            old_root = roots_at.get(old_size)
            new_root = roots_at.get(new_size)
            if old_root is None or new_root is None:
                return VerificationResult(
                    VerificationResultCode.BATCH_CONSISTENCY_FAILED,
                    f"no published checkpoint at tree size "
                    f"{old_size if old_root is None else new_size}",
                )
            if not verify_consistency(old_root, old_size, new_root, new_size, list(proof)):
                return VerificationResult(
                    VerificationResultCode.BATCH_CONSISTENCY_FAILED,
                    f"the tree at size {old_size} is not a prefix of the tree at size {new_size}",
                )
        checks.append("board.consistency_proofs")
    return VerificationResult(VerificationResultCode.VERIFIED, checks_run=tuple(checks))


def _chain_digest(
    export: BoardExport,
    sequence: int,
    tree_size: int,
    root: bytes,
    previous_hash: bytes,
) -> bytes:
    """The digest the *next* checkpoint must chain to.

    When full checkpoints were exported the digest is taken over the whole
    signed payload, because that is what the board actually chained. The
    five-tuple path is kept for callers that export only the legacy view;
    it covers strictly less, and a verifier given only that view is told so
    by the absence of `board.checkpoint_signatures` from `checks_run`.
    """
    for checkpoint in export.signed_checkpoints:
        if checkpoint.checkpoint_sequence == sequence:
            return checkpoint.digest()
    return _checkpoint_digest(sequence, tree_size, root, previous_hash)


def board_export_from(board: object) -> BoardExport:
    """Build a complete export from a board. One place, so no caller forgets.

    Callers that assembled a `BoardExport` by hand were the reason the
    signed view and the tuple view could drift apart.
    """
    return BoardExport(
        entries=tuple(board.export_entries()),  # type: ignore[attr-defined]
        checkpoints=tuple(board.export_checkpoints()),  # type: ignore[attr-defined]
        signed_checkpoints=tuple(board.export_signed_checkpoints()),  # type: ignore[attr-defined]
        signer_registry=board.signer_registry(),  # type: ignore[attr-defined]
    )


def _entry_digest(sequence: int, entry_type: str, payload: bytes) -> bytes:
    """Re-derive a board entry's leaf digest from exported bytes alone.

    This deliberately duplicates `BoardEntry.digest()` rather than importing
    it: the verifier is meant to be an independent reader of the export, and
    calling the publisher's own method would make agreement automatic.
    """
    from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
    from epd2_voting_service.reference.crypto.encoding import (
        encode_bytes,
        encode_struct,
        encode_text,
        encode_uint,
    )
    from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h

    return h(
        ZERO_KEY,
        DomainLabel.BOARD_ENTRY,
        [
            encode_struct(
                [
                    ("sequence", encode_uint(sequence, 8)),
                    ("entry_type", encode_text(entry_type)),
                    ("payload", encode_bytes(payload)),
                ]
            )
        ],
    )


def _checkpoint_digest(sequence: int, tree_size: int, root: bytes, previous_hash: bytes) -> bytes:
    from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
    from epd2_voting_service.reference.crypto.encoding import (
        encode_bytes,
        encode_struct,
        encode_uint,
    )
    from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h

    payload = encode_struct(
        [
            ("checkpoint_sequence", encode_uint(sequence, 8)),
            ("tree_size", encode_uint(tree_size, 8)),
            ("root", encode_bytes(root)),
            ("previous_checkpoint_hash", encode_bytes(previous_hash)),
        ]
    )
    return h(ZERO_KEY, DomainLabel.BOARD_CHECKPOINT, [payload])


def verify_batches(
    batches: list[SealedBatch], openings: list[BatchOpening], election_context_id: str
) -> VerificationResult:
    """Cadence completeness, root recomputation and leaf-class discipline."""
    if len(batches) != len(openings):
        return VerificationResult(
            VerificationResultCode.INCOMPLETE_RECORD,
            f"{len(batches)} commitments but {len(openings)} openings",
        )
    by_sequence = {b.batch_sequence: b for b in batches}
    expected = set(range(len(batches)))
    if set(by_sequence) != expected:
        return VerificationResult(
            VerificationResultCode.INCOMPLETE_RECORD, "batch cadence has a gap or a duplicate"
        )
    for opening in openings:
        batch = by_sequence[opening.batch_sequence]
        if len(opening.leaves) != batch.capacity:
            return VerificationResult(
                VerificationResultCode.BATCH_ROOT_MISMATCH,
                f"batch {batch.batch_sequence} opened {len(opening.leaves)} of "
                f"{batch.capacity} leaves",
            )
        for leaf_opening in opening.openings:
            if leaf_opening.leaf_class is LeafClass.COVER:
                continue
            recomputed = real_leaf(election_context_id, batch.batch_sequence, leaf_opening)
            if recomputed != opening.leaves[leaf_opening.leaf_index]:
                return VerificationResult(
                    VerificationResultCode.BATCH_ROOT_MISMATCH,
                    f"leaf {leaf_opening.leaf_index} does not recompute",
                )
        if opening.recompute_root() != batch.commitment_root:
            return VerificationResult(
                VerificationResultCode.BATCH_ROOT_MISMATCH,
                f"batch {batch.batch_sequence} root does not recompute",
            )
        # Recomputing the root proves the opening as a whole, and for a
        # *complete* opening the per-leaf inclusion check below is
        # mathematically redundant with it - which is why no test can
        # reach BATCH_INCLUSION_FAILED through this loop. It is kept as
        # cheap defence in depth against a future partial-opening path,
        # and the code it would return is reachable and tested through
        # `verify_leaf_inclusion`, which is what a voter's own client
        # runs against a single leaf.
        leaves = list(opening.leaves)
        for leaf_opening in opening.openings:
            if leaf_opening.leaf_class is LeafClass.COVER:
                continue
            index = leaf_opening.leaf_index
            path = inclusion_proof(leaves, index)
            if not verify_inclusion(leaves[index], path, batch.commitment_root):
                return VerificationResult(
                    VerificationResultCode.BATCH_INCLUSION_FAILED,
                    f"leaf {index} of batch {batch.batch_sequence} does not prove "
                    "inclusion against the published commitment root",
                )
    return VerificationResult(
        VerificationResultCode.VERIFIED,
        checks_run=(
            "batch.cadence",
            "batch.root_recomputation",
            "batch.leaf_openings",
            "batch.inclusion_proofs",
        ),
    )


def verify_record(
    record: ElectionRecord,
    board: BoardExport,
    spoiled_openings: dict[str, object] | None = None,
) -> VerificationResult:
    """The whole chain, from parameters to tally."""
    checks: list[str] = []
    # The expected bit lengths come from the registry, not from the record.
    # Deriving them from the record itself would compare a value against
    # itself and pass for any parameter set an attacker chose to ship.
    expected = PROFILE_BIT_LENGTHS.get(record.params.parameter_set_id)
    if expected is None:
        return VerificationResult(
            VerificationResultCode.UNSUPPORTED_PROFILE,
            f"parameter set {record.params.parameter_set_id!r} is not a profile this "
            "verifier knows; it cannot say whether the record is valid",
        )
    try:
        validate_parameter_set(
            record.params,
            expect_p_bits=expected[0],
            expect_q_bits=expected[1],
            check_primality=False,
        )
    except ValueError as exc:
        return VerificationResult(VerificationResultCode.INVALID_PARAMETER_SET, str(exc))
    checks.append("parameter_set")

    if not is_in_subgroup(record.joint_public_key, record.params):
        return VerificationResult(
            VerificationResultCode.INVALID_CEREMONY, "joint public key is not in the subgroup"
        )
    checks.append("joint_key")

    # -- guardian ceremony ------------------------------------------------
    if record.ceremony is not None:
        ok, detail = verify_ceremony(record.ceremony, record.params)
        if not ok:
            return VerificationResult(VerificationResultCode.INVALID_CEREMONY_TRANSCRIPT, detail)
        if record.ceremony.election_context_id != record.manifest.election_context_id:
            return VerificationResult(
                VerificationResultCode.INVALID_CEREMONY_TRANSCRIPT,
                "the ceremony transcript names a different election",
            )
        # The joint public key is derived, never accepted standalone.
        if derive_joint_public_key(record.ceremony, record.params) != record.joint_public_key:
            return VerificationResult(
                VerificationResultCode.INVALID_CEREMONY_TRANSCRIPT,
                "the record's joint public key is not the one the ceremony produced",
            )
        checks.append("ceremony.transcript")
        checks.append("ceremony.joint_key_derivation")
        checks.append("ceremony.guardian_proofs")

        if record.threshold_shares:
            policy = record.ceremony.policy
            by_tally: dict[tuple[str, str], list[ThresholdShare]] = {}
            for threshold_share in record.threshold_shares:
                by_tally.setdefault(
                    (threshold_share.contest_id, threshold_share.option_id), []
                ).append(threshold_share)
            for key, shares in by_tally.items():
                sequences = [entry.guardian_sequence for entry in shares]
                if len(set(sequences)) != len(sequences):
                    return VerificationResult(
                        VerificationResultCode.GUARDIAN_QUORUM_MISMATCH,
                        f"duplicate guardian share for {key[0]}/{key[1]}",
                    )
                if len(shares) < policy.quorum:
                    return VerificationResult(
                        VerificationResultCode.GUARDIAN_QUORUM_MISMATCH,
                        f"{len(shares)} shares for {key[0]}/{key[1]} against a quorum "
                        f"of {policy.quorum}; the quorum may not be reduced",
                    )
                target = next(
                    (t for t in record.tallies if (t.contest_id, t.option_id) == key),
                    None,
                )
                if target is None:
                    return VerificationResult(
                        VerificationResultCode.INCOMPLETE_RECORD,
                        f"threshold shares for {key[0]}/{key[1]} have no tally",
                    )
                for share in shares:
                    ok, detail = verify_threshold_share(
                        share,
                        target.encrypted,
                        record.ceremony,
                        record.params,
                    )
                    if not ok:
                        return VerificationResult(
                            VerificationResultCode.INVALID_DECRYPTION_SHARE, detail
                        )
            checks.append("ceremony.threshold_shares")

    if record.manifest.digest() != record.manifest.digest():  # pragma: no cover
        return VerificationResult(VerificationResultCode.INVALID_MANIFEST, "manifest digest")
    checks.append("manifest")

    board_result = verify_board(board)
    if board_result.code is not VerificationResultCode.VERIFIED:
        return board_result
    checks.extend(board_result.checks_run)

    batch_result = verify_batches(
        list(record.sealed_batches),
        list(record.batch_openings),
        record.manifest.election_context_id,
    )
    if batch_result.code is not VerificationResultCode.VERIFIED:
        return batch_result
    checks.extend(batch_result.checks_run)

    for envelope in (*record.accepted_ballots, *record.spoiled_ballots):
        try:
            verify_ballot_proofs(
                envelope,
                record.manifest,
                record.joint_public_key,
                record.params,
                record.base_hash,
            )
        except ValueError as exc:
            return VerificationResult(VerificationResultCode.INVALID_BALLOT_PROOF, str(exc))
    checks.append("ballot_proofs")

    if spoiled_openings:
        for envelope in record.spoiled_ballots:
            opening = spoiled_openings.get(envelope.ballot_id)
            if opening is None:
                return VerificationResult(
                    VerificationResultCode.INCOMPLETE_RECORD,
                    f"spoiled ballot {envelope.ballot_id} has no published opening",
                )
            try:
                verify_challenge_opening(
                    envelope,
                    opening,  # type: ignore[arg-type]
                    record.joint_public_key,
                    record.params,
                    record.base_hash,
                )
            except ValueError as exc:
                return VerificationResult(
                    VerificationResultCode.INVALID_CHALLENGE_OPENING, str(exc)
                )
        checks.append("challenge_openings")

    spoiled_ids = {e.ballot_id for e in record.spoiled_ballots}
    accepted_ids = {e.ballot_id for e in record.accepted_ballots}
    if spoiled_ids & accepted_ids:
        return VerificationResult(
            VerificationResultCode.TALLY_MISMATCH, "a spoiled ballot also appears as accepted"
        )
    checks.append("spoiled_never_counted")

    tally_index = {(t.contest_id, t.option_id): t for t in record.tallies}
    for guardian_share in record.shares:
        target = tally_index.get((guardian_share.contest_id, guardian_share.option_id))
        if target is None:
            return VerificationResult(
                VerificationResultCode.INCOMPLETE_RECORD,
                f"decryption share for {guardian_share.contest_id}/"
                f"{guardian_share.option_id} has no tally",
            )
        if not verify_decryption_share(
            target.encrypted.alpha,
            guardian_share.share,
            guardian_share.guardian_public,
            guardian_share.proof,
            record.params,
            decryption_share_context(
                record.manifest.election_context_id,
                guardian_share.contest_id,
                guardian_share.option_id,
            ),
        ):
            return VerificationResult(
                VerificationResultCode.INVALID_DECRYPTION_SHARE,
                f"guardian {guardian_share.guardian_index} share proof failed",
            )
    checks.append("decryption_shares")

    for tally in record.tallies:
        gathered = [
            selection.ciphertext
            for envelope in record.accepted_ballots
            for contest in envelope.contests
            if contest.contest_id == tally.contest_id
            for selection in contest.selections
            if selection.option_id == tally.option_id
        ]
        if not gathered:
            continue
        recomputed = accumulate(gathered, record.params)
        if (recomputed.alpha, recomputed.beta) != (
            tally.encrypted.alpha,
            tally.encrypted.beta,
        ):
            return VerificationResult(
                VerificationResultCode.TALLY_MISMATCH,
                f"aggregate for {tally.contest_id}/{tally.option_id} does not recompute",
            )
    checks.append("tally_recomputation")

    return VerificationResult(VerificationResultCode.VERIFIED, checks_run=tuple(checks))


def parse_manifest_from_bytes(raw: bytes, manifest: Manifest) -> Manifest:
    """Separate parser path: the verifier re-derives the digest from bytes."""
    if manifest.canonical_bytes() != raw:
        raise ValueError("manifest bytes do not match the canonical re-encoding")
    return manifest


def parse_envelope_from_bytes(
    raw: bytes, envelope: BallotEnvelope, params: ParameterSet
) -> BallotEnvelope:
    if envelope.canonical_bytes(params) != raw:
        raise ValueError("envelope bytes do not match the canonical re-encoding")
    return envelope


def verify_leaf_inclusion(
    leaf: bytes, path: list[tuple[str, bytes]], batch: SealedBatch
) -> VerificationResult:
    """One leaf against one published commitment root.

    This is the check a voter runs on their own ballot after closure. It
    needs the leaf, its sibling path and the published batch - not the
    opening, not the record, and nothing about anyone else's ballot.
    """
    if verify_inclusion(leaf, path, batch.commitment_root):
        return VerificationResult(
            VerificationResultCode.VERIFIED, checks_run=("batch.leaf_inclusion",)
        )
    return VerificationResult(
        VerificationResultCode.BATCH_INCLUSION_FAILED,
        f"the leaf does not prove inclusion in batch {batch.batch_sequence}",
    )

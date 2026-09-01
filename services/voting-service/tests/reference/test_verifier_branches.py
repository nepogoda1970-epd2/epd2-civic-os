"""Verifier failure branches and result-code coverage (§37, §59).

Every ``VerificationResultCode`` the reference verifier can return is
reached by a test here or in the negative corpus, so the reason-code
coverage figure in the implementation report is measured rather than
asserted. Codes the reference verifier cannot currently return are listed
in ``UNREACHABLE_IN_REFERENCE_VERIFIER`` with the reason — an honest gap,
not a silent one.
"""

from __future__ import annotations

import dataclasses

import pytest

from epd2_voting_service.reference.casting.ballot import Manifest
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    ParameterValidationError,
    is_probable_prime,
    require_in_subgroup,
)
from epd2_voting_service.reference.crypto.randomness import (
    ProductionRandomSource,
    RandomnessUnavailableError,
)
from epd2_voting_service.reference.election_record.builder import ElectionRecord, GuardianShare
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchIntegrityError,
    inclusion_path,
    merkle_root,
    verify_inclusion,
)
from epd2_voting_service.reference.testing.fixtures import (
    Fixture,
    deterministic_source,
    fixture_a,
)
from epd2_voting_service.reference.testing.fixtures import (
    small_params as small_params_for_branches,
)
from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot
from epd2_voting_service.reference.verification.results import (
    EXIT_CODES,
    NOT_CHECKED,
    VerificationResult,
    VerificationResultCode,
)
from epd2_voting_service.reference.verification.verifier import (
    BoardExport,
    board_export_from,
    parse_envelope_from_bytes,
    parse_manifest_from_bytes,
    verify_record,
)

#: Codes the reference verifier never returns this round, with the reason.
UNREACHABLE_IN_REFERENCE_VERIFIER: dict[str, str] = {
    "VERIFIED_WITH_WARNINGS": (
        "no reference check emits a warning yet; the code exists so a future "
        "check can degrade without renumbering"
    ),
    "INVALID_SCHEMA": (
        "reached by the schema registry; see the negative corpus cases "
        "unknown_critical_field and missing_critical_field"
    ),
    "INVALID_CANONICAL_ENCODING": (
        "reached by the canonical encoder; see the negative corpus cases "
        "non_canonical_integer and duplicate_field"
    ),
    "INVALID_MANIFEST": (
        "the reference record carries one manifest object, so the digest cannot "
        "disagree with itself; a wire-format verifier reaching this code is a "
        "PACK-17 item"
    ),
    "BATCH_INCLUSION_FAILED": (
        "unreachable through verify_batches, because for a complete opening "
        "the per-leaf check is redundant with root recomputation; reachable "
        "and tested through verify_leaf_inclusion, which is the check a "
        "voter's own client runs"
    ),
    "BATCH_RECONCILIATION_FAILED": (
        "raised by reconcile() as ReconciliationError before a record can be "
        "built; see the negative corpus cases duplicate_opening and "
        "cover_leaf_in_tally"
    ),
    "ARCHIVE_CORRUPTION": (
        "archive integrity is checked by the packaging step, not by "
        "verify_record; no reference archive reader exists this round"
    ),
}


def _record_and_board(fixture: Fixture) -> tuple[ElectionRecord, BoardExport]:
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"vb")
    from epd2_voting_service.reference.casting.transactions import submit_cast_ballot

    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    closed = close_and_build(fixture, [envelope], [])
    export = board_export_from(fixture.board)
    return closed.record, export


def test_every_exit_code_is_distinct_and_stable() -> None:
    assert len(set(EXIT_CODES.values())) == len(EXIT_CODES)
    assert set(EXIT_CODES) == set(VerificationResultCode)
    assert EXIT_CODES[VerificationResultCode.VERIFIED] == 0


def test_unreachable_codes_are_declared_and_still_exist() -> None:
    for name, reason in UNREACHABLE_IN_REFERENCE_VERIFIER.items():
        assert name in VerificationResultCode.__members__
        assert reason, name


def test_not_checked_is_never_empty_and_names_vo_08() -> None:
    result = VerificationResult(VerificationResultCode.VERIFIED)
    assert len(result.not_checked) == len(NOT_CHECKED) == 9
    assert any("VO-08" in line for line in result.not_checked)
    assert any("same checkpoints to everyone" in line for line in result.not_checked)


def test_invalid_parameter_set_branch() -> None:
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    broken = dataclasses.replace(
        record,
        params=ParameterSet(
            record.params.parameter_set_id,
            "v",
            "",
            False,
            record.params.p,
            record.params.q,
            3,
        ),
    )
    result = verify_record(broken, export)
    assert result.code is VerificationResultCode.INVALID_PARAMETER_SET
    assert result.exit_code == 21


def test_invalid_ceremony_branch() -> None:
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    broken = dataclasses.replace(record, joint_public_key=3)
    result = verify_record(broken, export)
    assert result.code is VerificationResultCode.INVALID_CEREMONY
    assert result.exit_code == 22


def test_invalid_ballot_proof_branch() -> None:
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    envelope = record.accepted_ballots[0]
    broken = dataclasses.replace(
        record,
        accepted_ballots=(dataclasses.replace(envelope, manifest_digest=b"\x00" * 32),),
    )
    result = verify_record(broken, export)
    assert result.code is VerificationResultCode.INVALID_BALLOT_PROOF
    assert result.exit_code == 30


def test_invalid_challenge_opening_branch() -> None:
    fixture = fixture_a()
    challenged, opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"vb-chal")
    from epd2_voting_service.reference.casting.transactions import submit_public_challenge

    submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], challenged, opening, "k"
    )
    closed = close_and_build(fixture, [], [challenged])
    export = board_export_from(fixture.board)
    good = verify_record(closed.record, export, {challenged.ballot_id: opening})
    assert good.code is VerificationResultCode.VERIFIED, good.detail
    assert "challenge_openings" in good.checks_run

    _, wrong_opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"vb-other")
    bad = verify_record(closed.record, export, {challenged.ballot_id: wrong_opening})
    assert bad.code is VerificationResultCode.INVALID_CHALLENGE_OPENING
    assert bad.exit_code == 31


def test_missing_spoiled_opening_is_an_incomplete_record() -> None:
    fixture = fixture_a()
    challenged, opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"vb-missing")
    from epd2_voting_service.reference.casting.transactions import submit_public_challenge

    submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], challenged, opening, "k"
    )
    closed = close_and_build(fixture, [], [challenged])
    export = board_export_from(fixture.board)
    result = verify_record(closed.record, export, {"some-other-ballot": opening})
    assert result.code is VerificationResultCode.INCOMPLETE_RECORD
    assert result.exit_code == 10


def test_orphan_decryption_share_is_an_incomplete_record() -> None:
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    orphan = dataclasses.replace(
        record.shares[0],
        contest_id="contest-that-has-no-tally",
    )
    broken = dataclasses.replace(record, shares=(orphan,))
    result = verify_record(broken, export)
    assert result.code is VerificationResultCode.INCOMPLETE_RECORD


def test_invalid_decryption_share_branch() -> None:
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    share = record.shares[0]
    forged = GuardianShare(
        contest_id=share.contest_id,
        option_id=share.option_id,
        guardian_index=share.guardian_index,
        guardian_public=share.guardian_public,
        share=(share.share * 2) % record.params.p,
        proof=share.proof,
    )
    broken = dataclasses.replace(record, shares=(forged,))
    result = verify_record(broken, export)
    assert result.code is VerificationResultCode.INVALID_DECRYPTION_SHARE
    assert result.exit_code == 50


def test_parser_path_rejects_bytes_that_do_not_re_encode() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"vb-parse")
    assert (
        parse_manifest_from_bytes(fixture.manifest.canonical_bytes(), fixture.manifest)
        is fixture.manifest
    )
    with pytest.raises(ValueError, match="canonical re-encoding"):
        parse_manifest_from_bytes(b"not the manifest", fixture.manifest)

    raw = envelope.canonical_bytes(fixture.params)
    assert parse_envelope_from_bytes(raw, envelope, fixture.params) is envelope
    with pytest.raises(ValueError, match="canonical re-encoding"):
        parse_envelope_from_bytes(raw + b"\x00", envelope, fixture.params)


def test_manifest_style_lookup_fails_closed() -> None:
    fixture = fixture_a()
    with pytest.raises((KeyError, LookupError, ValueError)):
        fixture.manifest.style("no-such-style")
    assert isinstance(fixture.manifest, Manifest)


# -- residual branches in supporting modules -----------------------------


def test_batch_helpers_fail_closed_on_bad_input() -> None:
    with pytest.raises(BatchIntegrityError, match="at least one leaf"):
        merkle_root([])
    with pytest.raises(BatchIntegrityError, match="out of range"):
        inclusion_path([b"a", b"b"], 5)
    leaves = [b"a", b"b", b"c"]
    root = merkle_root(leaves)
    assert verify_inclusion(leaves[1], inclusion_path(leaves, 1), root)
    assert not verify_inclusion(leaves[1], inclusion_path(leaves, 0), root)


def test_production_random_source_reports_failure_rather_than_degrading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = ProductionRandomSource()

    def broken(count: int) -> bytes:
        raise OSError("entropy pool unavailable")

    monkeypatch.setattr(
        "epd2_voting_service.reference.crypto.randomness.secrets.token_bytes", broken
    )
    with pytest.raises(RandomnessUnavailableError):
        source.random_bytes(32)
    with pytest.raises(RandomnessUnavailableError):
        source.random_below(97)


def test_production_random_source_rejects_non_positive_bounds() -> None:
    source = ProductionRandomSource()
    with pytest.raises(ValueError):
        source.random_bytes(0)
    with pytest.raises(ValueError):
        source.random_below(0)


def test_primality_helper_rejects_small_and_composite_values() -> None:
    assert is_probable_prime(2) is True
    assert is_probable_prime(3) is True
    assert is_probable_prime(1) is False
    assert is_probable_prime(0) is False
    assert is_probable_prime(-7) is False
    assert is_probable_prime(9) is False
    assert is_probable_prime(561) is False  # Carmichael number
    assert is_probable_prime(104729) is True


def test_require_in_subgroup_names_the_value_it_rejected() -> None:
    fixture = fixture_a()
    with pytest.raises(ParameterValidationError, match="joint public key"):
        require_in_subgroup(fixture.params.p + 1, fixture.params, "joint public key")


# -- batch inclusion and consistency codes (§48) -------------------------


def test_batch_inclusion_failed_branch() -> None:
    """The check a voter runs on their own leaf, in both directions."""
    from epd2_voting_service.reference.publication.sealed_batches import inclusion_path
    from epd2_voting_service.reference.verification.verifier import (
        verify_batches,
        verify_leaf_inclusion,
    )

    fixture = fixture_a()
    record, _ = _record_and_board(fixture)
    batch, opening = record.sealed_batches[0], record.batch_openings[0]
    assert (
        verify_batches([batch], [opening], fixture.manifest.election_context_id).code
        is VerificationResultCode.VERIFIED
    )

    leaves = list(opening.leaves)
    real = next(o for o in opening.openings if o.artifact_reference)
    good = verify_leaf_inclusion(
        leaves[real.leaf_index], inclusion_path(leaves, real.leaf_index), batch
    )
    assert good.code is VerificationResultCode.VERIFIED
    assert good.checks_run == ("batch.leaf_inclusion",)

    # a leaf that is not in this batch does not prove inclusion
    bad = verify_leaf_inclusion(b"\xaa" * 32, inclusion_path(leaves, real.leaf_index), batch)
    assert bad.code is VerificationResultCode.BATCH_INCLUSION_FAILED
    assert bad.exit_code == 43

    # nor does a real leaf under someone else's path
    other = (real.leaf_index + 1) % len(leaves)
    assert (
        verify_leaf_inclusion(leaves[real.leaf_index], inclusion_path(leaves, other), batch).code
        is VerificationResultCode.BATCH_INCLUSION_FAILED
    )


def test_board_consistency_proofs_are_checked_when_supplied() -> None:
    from epd2_voting_service.reference.publication.bulletin_board import EntryType
    from epd2_voting_service.reference.verification.verifier import verify_board

    fixture = fixture_a()
    board = fixture.board
    sizes: list[int] = []
    for index in range(4):
        board.append(EntryType.SEALED_BATCH_COMMITMENT, f"b{index}".encode())
        sizes.append(board.publish_checkpoint().tree_size)

    good = BoardExport(
        entries=tuple(board.export_entries()),
        checkpoints=tuple(board.export_checkpoints()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        consistency_proofs=(
            (sizes[0], sizes[-1], tuple(board.consistency_proof(sizes[0]))),
            (sizes[1], sizes[-1], tuple(board.consistency_proof(sizes[1]))),
        ),
    )
    verdict = verify_board(good)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail
    assert "board.consistency_proofs" in verdict.checks_run

    corrupted = BoardExport(
        entries=good.entries,
        checkpoints=good.checkpoints,
        signed_checkpoints=good.signed_checkpoints,
        signer_registry=good.signer_registry,
        consistency_proofs=((sizes[0], sizes[-1], (b"\x00" * 32,)),),
    )
    bad = verify_board(corrupted)
    assert bad.code is VerificationResultCode.BATCH_CONSISTENCY_FAILED
    assert bad.exit_code == 44

    unknown_size = BoardExport(
        entries=good.entries,
        checkpoints=good.checkpoints,
        signed_checkpoints=good.signed_checkpoints,
        signer_registry=good.signer_registry,
        consistency_proofs=((999, sizes[-1], ()),),
    )
    assert verify_board(unknown_size).code is VerificationResultCode.BATCH_CONSISTENCY_FAILED


def test_a_board_export_without_proofs_claims_no_consistency_check() -> None:
    """Absence of a proof must not read as a passed check."""
    from epd2_voting_service.reference.publication.bulletin_board import EntryType
    from epd2_voting_service.reference.verification.verifier import verify_board

    fixture = fixture_a()
    fixture.board.append(EntryType.ELECTION_MANIFEST, b"m")
    fixture.board.publish_checkpoint()
    verdict = verify_board(board_export_from(fixture.board))
    assert verdict.code is VerificationResultCode.VERIFIED
    assert "board.consistency_proofs" not in verdict.checks_run


# -- gaps closed after the first documentation pass ----------------------


def test_reserved_domain_labels_are_declared_accurately() -> None:
    """A registry may not list a label nothing uses without saying so."""
    import pathlib as _pathlib

    import epd2_voting_service.reference as _reference
    from epd2_voting_service.reference.crypto.domain_separation import (
        RESERVED_WITHOUT_CALL_SITE,
        DomainLabel,
    )

    root = _pathlib.Path(_reference.__file__).parent
    body = "\n".join(
        path.read_text() for path in root.rglob("*.py") if path.name != "domain_separation.py"
    )
    unused = {label.value for label in DomainLabel if f"DomainLabel.{label.name}" not in body}
    assert unused == set(RESERVED_WITHOUT_CALL_SITE)


def test_profile_bit_lengths_come_from_code_not_from_the_file() -> None:
    """The length check must not compare a value against itself."""
    from epd2_voting_service.reference.crypto.parameters import (
        PROFILE_BIT_LENGTHS,
        PROFILE_REGISTRY,
        load_profile,
    )

    assert set(PROFILE_BIT_LENGTHS) == set(PROFILE_REGISTRY)
    assert PROFILE_BIT_LENGTHS["EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160"] == (1024, 160)
    assert PROFILE_BIT_LENGTHS["EPD2-TESTONLY-NOTCONFORMANT-P4096-Q256"] == (4096, 256)
    assert PROFILE_BIT_LENGTHS["EPD2-CRYPTO-1"] == (4096, 256)
    small = load_profile("EPD2-TESTONLY-NOTCONFORMANT-P1024-Q160")
    assert (small.p.bit_length(), small.q.bit_length()) == (1024, 160)


def test_record_digest_covers_the_openings_and_the_shares() -> None:
    """A digest that omits an artefact does not commit to it."""
    fixture = fixture_a()
    record, _ = _record_and_board(fixture)
    baseline = record.digest()

    opening = record.batch_openings[0]
    shortened = dataclasses.replace(
        record,
        batch_openings=(dataclasses.replace(opening, openings=opening.openings[:-1]),),
    )
    assert shortened.digest() != baseline

    share = record.shares[0]
    reshared = dataclasses.replace(
        record,
        shares=(dataclasses.replace(share, guardian_index=share.guardian_index + 1),),
    )
    assert reshared.digest() != baseline


def test_decryption_share_proof_is_bound_to_its_contest_and_option() -> None:
    """A share proved for one option must not verify for another."""
    from epd2_voting_service.reference.crypto.proofs import verify_decryption_share
    from epd2_voting_service.reference.election_record.builder import (
        decryption_share_context,
    )

    fixture = fixture_a()
    record, _ = _record_and_board(fixture)
    share = record.shares[0]
    tally = next(
        t
        for t in record.tallies
        if (t.contest_id, t.option_id) == (share.contest_id, share.option_id)
    )
    right = decryption_share_context(
        record.manifest.election_context_id, share.contest_id, share.option_id
    )
    wrong = decryption_share_context(
        record.manifest.election_context_id, share.contest_id, "some-other-option"
    )
    assert verify_decryption_share(
        tally.encrypted.alpha,
        share.share,
        share.guardian_public,
        share.proof,
        record.params,
        right,
    )
    assert not verify_decryption_share(
        tally.encrypted.alpha,
        share.share,
        share.guardian_public,
        share.proof,
        record.params,
        wrong,
    )


def test_ballot_proof_verifiers_reject_a_public_key_outside_the_subgroup() -> None:
    from epd2_voting_service.reference.crypto.proofs import (
        prove_selection,
        verify_contest_sum,
        verify_selection,
    )

    fixture = fixture_a()
    params = fixture.params
    source = deterministic_source(b"pk-check")
    nonce = 1 + source.random_below(params.q - 1)
    from epd2_voting_service.reference.crypto.elgamal import encrypt

    ciphertext = encrypt(1, nonce, fixture.public_key, params)
    proof = prove_selection(ciphertext, nonce, 1, fixture.public_key, params, b"ctx", source)
    assert verify_selection(ciphertext, proof, fixture.public_key, params, b"ctx")
    # 3 is almost certainly not in the order-q subgroup of these parameters
    assert not verify_selection(ciphertext, proof, 3, params, b"ctx")

    contest = _record_and_board(fixture_a())[0].accepted_ballots[0].contests[0]
    assert not verify_contest_sum(contest.accumulated, contest.sum_proof, 1, 3, params, b"ctx")


def test_checkpoint_roots_are_re_derived_from_the_exported_entries() -> None:
    """A chained sequence of roots over entries nobody saw must not verify."""
    from epd2_voting_service.reference.publication.bulletin_board import EntryType
    from epd2_voting_service.reference.verification.verifier import verify_board

    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.append(EntryType.PARAMETER_SET, b"p")
    checkpoint = board.publish_checkpoint()

    honest = board_export_from(board)
    verdict = verify_board(honest)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail
    assert "board.root_recomputation" in verdict.checks_run

    # same checkpoints, but one entry's payload was altered after the fact
    altered = BoardExport(
        entries=((0, "election_manifest", b"tampered"), honest.entries[1]),
        checkpoints=honest.checkpoints,
        signed_checkpoints=honest.signed_checkpoints,
        signer_registry=honest.signer_registry,
    )
    assert verify_board(altered).code is VerificationResultCode.BOARD_INCONSISTENCY

    # a checkpoint claiming more entries than were exported
    overclaimed = BoardExport(
        entries=(honest.entries[0],),
        signed_checkpoints=honest.signed_checkpoints,
        signer_registry=honest.signer_registry,
        checkpoints=(
            (
                checkpoint.checkpoint_sequence,
                checkpoint.tree_size,
                checkpoint.root,
                checkpoint.previous_checkpoint_hash,
                checkpoint.signature,
            ),
        ),
    )
    result = verify_board(overclaimed)
    assert result.code is VerificationResultCode.BOARD_INCONSISTENCY
    assert "only 1 entries were exported" in result.detail


# -- error classes that had no test before the documentation pass --------


def test_decode_exponent_fails_closed_outside_its_bound() -> None:
    from epd2_voting_service.reference.crypto.elgamal import (
        DecryptionDomainError,
        decode_exponent,
    )

    params = small_params_for_branches()
    # g^3 is in the subgroup but outside a maximum of 2
    value = pow(params.g, 3, params.p)
    assert decode_exponent(value, params, maximum=3) == 3
    with pytest.raises(DecryptionDomainError):
        decode_exponent(value, params, maximum=2)
    with pytest.raises(DecryptionDomainError):
        decode_exponent(2, params, maximum=8)


def test_merkle_helpers_fail_closed() -> None:
    from epd2_voting_service.reference.crypto.merkle import (
        MerkleError,
        consistency_proof,
        inclusion_proof,
    )

    leaves = [b"a", b"b", b"c"]
    with pytest.raises(MerkleError, match="out of range"):
        inclusion_proof(leaves, 3)
    with pytest.raises(MerkleError):
        consistency_proof(leaves, 0)
    with pytest.raises(MerkleError):
        consistency_proof(leaves, 4)


def test_board_integrity_errors_are_raised_for_out_of_range_requests() -> None:
    from epd2_voting_service.reference.publication.bulletin_board import (
        BoardIntegrityError,
        EntryType,
    )

    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    with pytest.raises(BoardIntegrityError, match="out of range"):
        board.inclusion_proof(5)
    with pytest.raises(BoardIntegrityError):
        board.consistency_proof(0)
    with pytest.raises(BoardIntegrityError):
        board.consistency_proof(9)
    with pytest.raises(BoardIntegrityError, match="tree size out of range"):
        board.root_at(9)


def test_reference_api_reports_missing_state_rather_than_guessing() -> None:
    from epd2_voting_service.reference.api import ReferenceApi, ReferenceApiError
    from epd2_voting_service.reference.casting.transactions import Outcome, SubmissionResult

    fixture = fixture_a()
    api = ReferenceApi(store=fixture.store, runtime=fixture.runtime, board=fixture.board)
    with pytest.raises(ReferenceApiError, match="no checkpoint"):
        api.get_board_checkpoint()
    phantom = SubmissionResult(
        outcome=Outcome.ACCEPTED,
        reason_code="acceptance.committed",
        ballot_id="nope",
        confirmation_code="XXXXX",
        batch_window_id="w0",
        publication_obligation_id="obl-does-not-exist",
        counted=True,
    )
    with pytest.raises(ReferenceApiError, match="no publication obligation"):
        api.get_publication_state(phantom)


def test_capacity_exhaustion_is_caught_at_sealing_time() -> None:
    """A batch that cannot hold its committed reservations must not seal."""
    from epd2_voting_service.reference.publication.capacity import CapacityExhaustedError
    from epd2_voting_service.reference.publication.sealing import seal_batch

    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"overfull")
    from epd2_voting_service.reference.casting.transactions import submit_cast_ballot

    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    with pytest.raises(CapacityExhaustedError, match="committed reservations"):
        seal_batch(
            fixture.store,
            election_context_id=fixture.manifest.election_context_id,
            batch_sequence=0,
            batch_window_id="w0",
            capacity=0,
            capacity_profile_id="test",
            source=deterministic_source(b"overfull-seal"),
        )


def test_export_validates_the_record_against_its_registered_schema() -> None:
    """The schema registry is load-bearing on the export path."""
    from epd2_voting_service.reference.api import ReferenceApi
    from epd2_voting_service.reference.schemas import SCHEMA_REGISTRY, UnknownCriticalFieldError

    fixture = fixture_a()
    record, _ = _record_and_board(fixture)
    api = ReferenceApi(store=fixture.store, runtime=fixture.runtime, board=fixture.board)
    assert api.export_election_record(record) == record.canonical_bytes()

    descriptor = SCHEMA_REGISTRY["election_record"]
    assert set(descriptor.critical_fields) | set(descriptor.optional_fields) == set(
        record.__slots__
    ), "the registered schema has drifted from the record it describes"
    with pytest.raises(UnknownCriticalFieldError):
        from epd2_voting_service.reference.schemas import validate_document

        validate_document(
            "election_record",
            {**{n: getattr(record, n) for n in record.__slots__}, "turnout": 3},
        )


def test_unsupported_profile_branch() -> None:
    """An unknown parameter set is refused, not measured against itself."""
    fixture = fixture_a()
    record, export = _record_and_board(fixture)
    stranger = dataclasses.replace(
        record,
        params=dataclasses.replace(record.params, parameter_set_id="EPD2-NOT-REGISTERED"),
    )
    result = verify_record(stranger, export)
    assert result.code is VerificationResultCode.UNSUPPORTED_PROFILE
    assert result.exit_code == 11
    assert "not a profile this verifier knows" in result.detail

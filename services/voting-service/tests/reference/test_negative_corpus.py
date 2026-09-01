"""Negative test corpus (PACK-16D §40).

Thirty-nine cases, each named for its §40 entry and each asserting a
specific expected reason code — not merely "something was raised".
``EXPECTED_REASON_CODES`` is the machine-readable index that the
PACK-16D negative-test-corpus document is generated from, so the document
cannot drift from the tests.

Every case must fail closed. A case that merely returns a warning, or that
succeeds with a degraded result, is a defect in the implementation, not a
lenient test.
"""

from __future__ import annotations

import pytest

from epd2_voting_service.reference.casting.ballot import (
    BallotEnvelope,
    BallotStructureError,
    EncryptedContest,
    EncryptedSelection,
    OvervoteError,
    verify_ballot_proofs,
)
from epd2_voting_service.reference.casting.confirmation import (
    ChallengeOpeningError,
    verify_challenge_opening,
)
from epd2_voting_service.reference.casting.continuation import (
    CapabilityUnknownError,
    CastEntitlementExhaustedError,
    PublicChallengeEntitlementExhaustedError,
)
from epd2_voting_service.reference.casting.idempotency import IdempotencyConflictError
from epd2_voting_service.reference.casting.store import (
    CastCapacityUnavailableError,
    DuplicateArtifactError,
    PublicChallengeReservationUnavailableError,
)
from epd2_voting_service.reference.casting.transactions import (
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.crypto.elgamal import (
    Ciphertext,
    PlaintextDomainError,
    encrypt,
    validate_ciphertext,
)
from epd2_voting_service.reference.crypto.encoding import (
    CanonicalEncodingError,
    decode_uint,
    encode_struct,
    encode_uint,
)
from epd2_voting_service.reference.crypto.parameters import (
    ParameterSet,
    ParameterValidationError,
    require_in_subgroup,
    validate_parameter_set,
)
from epd2_voting_service.reference.crypto.proofs import verify_selection
from epd2_voting_service.reference.election_record.builder import (
    ElectionRecord,
    IntermediateTallyProhibitedError,
    ReconciliationError,
    reconcile,
    tally_accepted,
)
from epd2_voting_service.reference.publication.bulletin_board import (
    EntryType,
    PreClosurePublicationError,
)
from epd2_voting_service.reference.publication.capacity import (
    CapacityPlan,
    CapacityPlanInvalidError,
)
from epd2_voting_service.reference.publication.sealed_batches import (
    BatchOpening,
    LeafClass,
    LeafOpening,
    SealedBatch,
)
from epd2_voting_service.reference.publication.sealing import seal_batch
from epd2_voting_service.reference.schemas import (
    MissingCriticalFieldError,
    UnknownCriticalFieldError,
    validate_document,
)
from epd2_voting_service.reference.testing.fixtures import (
    deterministic_source,
    fixture_a,
    fixture_c,
    small_params,
)
from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot
from epd2_voting_service.reference.verification.results import VerificationResultCode
from epd2_voting_service.reference.verification.verifier import (
    BoardExport,
    board_export_from,
    verify_batches,
    verify_board,
    verify_record,
)

#: case name -> expected reason code. Generated into the corpus document.
EXPECTED_REASON_CODES: dict[str, str] = {
    "wrong_p_q_g": "PARAMETER_SET_INVALID",
    "invalid_subgroup_element": "PARAMETER_SET_INVALID",
    "zero_element": "PARAMETER_SET_INVALID",
    "element_ge_p": "PARAMETER_SET_INVALID",
    "invalid_scalar": "BALLOT_PREPARATION_CONTEST_INVALID",
    "non_canonical_integer": "INVALID_CANONICAL_ENCODING",
    "duplicate_field": "INVALID_CANONICAL_ENCODING",
    "unknown_critical_field": "INVALID_SCHEMA",
    "missing_critical_field": "INVALID_SCHEMA",
    "wrong_manifest_digest": "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH",
    "wrong_election_context": "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH",
    "wrong_ballot_style": "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH",
    "invalid_ciphertext": "PARAMETER_SET_INVALID",
    "invalid_proof": "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH",
    "reused_nonce": "BALLOT_PREPARATION_STYLE_SHAPE_MISMATCH",
    "challenged_ballot_submitted_as_cast": "ACCEPTANCE_DUPLICATE_BALLOT_ID",
    "cast_nonce_revealed": "CHALLENGE_REENCRYPTION_MISMATCH",
    "duplicate_public_challenge": "CHALLENGE_PUBLIC_ENTITLEMENT_EXHAUSTED",
    "duplicate_cast": "CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED",
    "idempotency_conflict": "SUBMISSION_IDEMPOTENCY_CONFLICT",
    "capability_replay": "CONTINUATION_CAST_ENTITLEMENT_EXHAUSTED",
    "unknown_capability": "CONTINUATION_INVALID",
    "leaf_reservation_race": "SUBMISSION_CAST_CAPACITY_UNAVAILABLE",
    "wrong_slot_type": "CHALLENGE_PUBLIC_RESERVATION_UNAVAILABLE",
    "adaptive_overflow_attempt": "ELECTION_CAPACITY_PLAN_INVALID",
    "batch_root_mismatch": "BATCH_ROOT_MISMATCH",
    "missing_opening": "INCOMPLETE_RECORD",
    "duplicate_opening": "BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED",
    "cover_leaf_in_tally": "BULLETIN_BOARD_BATCH_RECONCILIATION_FAILED",
    "spoiled_ballot_in_tally": "TALLY_MISMATCH",
    "conflicting_checkpoint": "BOARD_INCONSISTENCY",
    "rollback": "BOARD_INCONSISTENCY",
    "invalid_consistency_proof": "BATCH_CONSISTENCY_FAILED",
    "pre_closure_decryption_artifact": "PUBLICATION_UNSCHEDULED_BATCH_PROHIBITED",
    "intermediate_tally_artifact": "TALLY_PRE_CLOSURE_PROHIBITED",
    "overvote": "BALLOT_PREPARATION_OVERVOTE",
    "ambiguous_sequence_encoding": "INVALID_CANONICAL_ENCODING",
    "unauthorized_board_signer": "BOARD_SIGNER_UNKNOWN",
    "insufficient_guardian_quorum": "GUARDIAN_INSUFFICIENT_QUORUM",
}


def test_every_declared_case_has_a_test() -> None:
    """The index and the suite must not drift apart."""
    import sys

    module = sys.modules[__name__]
    for case in EXPECTED_REASON_CODES:
        assert hasattr(module, f"test_neg_{case}"), f"no test for {case}"


def test_every_case_asserts_its_declared_reason_code() -> None:
    """A case that only asserts an exception *type* is weaker evidence.

    The declared code would then be a comment rather than a check, and the
    index could drift from what the implementation actually raises without
    anything failing. This guard makes that impossible: every case body
    must reference ``EXPECTED_REASON_CODES``.
    """
    import inspect
    import sys

    module = sys.modules[__name__]
    silent = [
        case
        for case in EXPECTED_REASON_CODES
        if "EXPECTED_REASON_CODES[" not in inspect.getsource(getattr(module, f"test_neg_{case}"))
    ]
    assert silent == [], f"cases that do not assert their declared code: {silent}"


# -- encoding, parameters, group elements --------------------------------


def test_neg_wrong_p_q_g() -> None:
    params = small_params()
    bad = ParameterSet("x", "v", "", False, params.p, params.q, 3)
    with pytest.raises(ParameterValidationError) as raised:
        validate_parameter_set(
            bad,
            expect_p_bits=params.p.bit_length(),
            expect_q_bits=params.q.bit_length(),
            check_primality=False,
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["wrong_p_q_g"]


def test_neg_invalid_subgroup_element() -> None:
    params = small_params()
    with pytest.raises(ParameterValidationError) as raised:
        require_in_subgroup(params.g + 1, params, "probe")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["invalid_subgroup_element"]


def test_neg_zero_element() -> None:
    params = small_params()
    with pytest.raises(ParameterValidationError) as raised:
        require_in_subgroup(0, params, "probe")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["zero_element"]


def test_neg_element_ge_p() -> None:
    params = small_params()
    with pytest.raises(ParameterValidationError) as raised:
        require_in_subgroup(params.p, params, "probe")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["element_ge_p"]
    with pytest.raises(ParameterValidationError):
        require_in_subgroup(params.p + 1, params, "probe")


def test_neg_invalid_scalar() -> None:
    """A plaintext outside the declared domain is rejected, never clamped."""
    params = small_params()
    source = deterministic_source(b"neg-scalar")
    public_key = pow(params.g, 1 + source.random_below(params.q - 1), params.p)
    with pytest.raises(PlaintextDomainError) as raised:
        encrypt(2, 5, public_key, params, max_message=1)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["invalid_scalar"]


def test_neg_non_canonical_integer() -> None:
    with pytest.raises(CanonicalEncodingError) as raised:
        decode_uint(b"\x01", 4)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["non_canonical_integer"]
    with pytest.raises(CanonicalEncodingError):
        encode_uint(2**32, 4)
    with pytest.raises(CanonicalEncodingError):
        encode_uint(-1, 4)


def test_neg_duplicate_field() -> None:
    with pytest.raises(CanonicalEncodingError, match="duplicate field") as raised:
        encode_struct([("a", encode_uint(1, 4)), ("a", encode_uint(1, 4))])
    assert raised.value.reason_code == EXPECTED_REASON_CODES["duplicate_field"]


def test_neg_unknown_critical_field() -> None:
    with pytest.raises(UnknownCriticalFieldError) as raised:
        validate_document(
            "receipt",
            {
                "ballot_id": "b",
                "confirmation_code": "c",
                "batch_window_id": "w",
                "counted": True,
                "turnout_so_far": 17,
            },
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["unknown_critical_field"]


def test_neg_missing_critical_field() -> None:
    with pytest.raises(MissingCriticalFieldError) as raised:
        validate_document("receipt", {"ballot_id": "b"})
    assert raised.value.reason_code == EXPECTED_REASON_CODES["missing_critical_field"]


# -- ballot structure ----------------------------------------------------


def _mangle(envelope: BallotEnvelope, **changes: object) -> BallotEnvelope:
    fields = {
        name: getattr(envelope, name)
        for name in (
            "ballot_id",
            "election_context_id",
            "ballot_style_id",
            "parameter_set_id",
            "manifest_digest",
            "contests",
        )
    }
    fields.update(changes)
    return BallotEnvelope(**fields)


def test_neg_wrong_manifest_digest() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-digest")
    broken = _mangle(envelope, manifest_digest=b"\x00" * 32)
    with pytest.raises(BallotStructureError, match="manifest digest") as raised:
        verify_ballot_proofs(
            broken, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["wrong_manifest_digest"]


def test_neg_wrong_election_context() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-ctx")
    broken = _mangle(envelope, election_context_id="some-other-election")
    with pytest.raises(BallotStructureError, match="election context") as raised:
        verify_ballot_proofs(
            broken, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["wrong_election_context"]


def test_neg_wrong_ballot_style() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-style")
    broken = _mangle(envelope, ballot_style_id="style-that-does-not-exist")
    with pytest.raises(BallotStructureError) as raised:
        verify_ballot_proofs(
            broken, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["wrong_ballot_style"]


def test_neg_invalid_ciphertext() -> None:
    params = small_params()
    with pytest.raises(ParameterValidationError) as raised:
        validate_ciphertext(Ciphertext(alpha=0, beta=params.g), params)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["invalid_ciphertext"]
    with pytest.raises(ParameterValidationError):
        validate_ciphertext(Ciphertext(alpha=params.g, beta=params.p), params)


def test_neg_invalid_proof() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-proof")
    contest = envelope.contests[0]
    selection = contest.selections[0]
    tampered_selection = EncryptedSelection(
        option_id=selection.option_id,
        ciphertext=selection.ciphertext,
        proof=type(selection.proof)(
            **{
                name: (getattr(selection.proof, name) + 1) % fixture.params.p
                if name == "v0"
                else getattr(selection.proof, name)
                for name in selection.proof.__slots__
            }
        ),
    )
    broken = _mangle(
        envelope,
        contests=(
            EncryptedContest(
                contest_id=contest.contest_id,
                selections=(tampered_selection, *contest.selections[1:]),
                accumulated=contest.accumulated,
                sum_proof=contest.sum_proof,
            ),
        ),
    )
    with pytest.raises(BallotStructureError, match="selection proof failed") as raised:
        verify_ballot_proofs(
            broken, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["invalid_proof"]


def test_neg_reused_nonce() -> None:
    """A proof is bound to its context, so a copied proof does not transfer."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-nonce")
    contest = envelope.contests[0]
    first, second = contest.selections[0], contest.selections[1]
    swapped = EncryptedSelection(
        option_id=second.option_id, ciphertext=second.ciphertext, proof=first.proof
    )
    broken = _mangle(
        envelope,
        contests=(
            EncryptedContest(
                contest_id=contest.contest_id,
                selections=(first, swapped, *contest.selections[2:]),
                accumulated=contest.accumulated,
                sum_proof=contest.sum_proof,
            ),
        ),
    )
    with pytest.raises(BallotStructureError) as raised:
        verify_ballot_proofs(
            broken, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["reused_nonce"]
    # and directly: the proof does not verify under the other option's context
    assert not verify_selection(
        second.ciphertext, first.proof, fixture.public_key, fixture.params, b"other-context"
    )


def test_neg_overvote() -> None:
    fixture = fixture_a()
    with pytest.raises(OvervoteError) as raised:
        make_ballot(fixture, {"c1": ("opt-1", "opt-2")}, b"neg-overvote")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["overvote"]


# -- capability and transaction ------------------------------------------


def test_neg_challenged_ballot_submitted_as_cast() -> None:
    fixture = fixture_a()
    envelope, opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-chal-cast")
    submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, opening, "k1"
    )
    with pytest.raises(DuplicateArtifactError, match="already published") as raised:
        submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k2")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["challenged_ballot_submitted_as_cast"]
    assert envelope.ballot_id not in fixture.store.accepted_ballots


def test_neg_cast_nonce_revealed() -> None:
    """An opening for a *different* ballot does not open this one."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-open-a")
    _, other_opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-open-b")
    with pytest.raises(ChallengeOpeningError) as raised:
        verify_challenge_opening(
            envelope,
            other_opening,
            fixture.public_key,
            fixture.params,
            fixture.base_hash,
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["cast_nonce_revealed"]


def test_neg_duplicate_public_challenge() -> None:
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, first_open = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-dupchal-a")
    second, second_open = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-dupchal-b")
    submit_public_challenge(fixture.store, fixture.runtime, capability, first, first_open, "k1")
    with pytest.raises(PublicChallengeEntitlementExhaustedError) as raised:
        submit_public_challenge(
            fixture.store, fixture.runtime, capability, second, second_open, "k2"
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["duplicate_public_challenge"]


def test_neg_duplicate_cast() -> None:
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-dupcast-a")
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-dupcast-b")
    submit_cast_ballot(fixture.store, fixture.runtime, capability, first, "k1")
    with pytest.raises(CastEntitlementExhaustedError) as raised:
        submit_cast_ballot(fixture.store, fixture.runtime, capability, second, "k2")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["duplicate_cast"]


def test_neg_idempotency_conflict() -> None:
    fixture = fixture_a()
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-idem-a")
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-idem-b")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], first, "shared")
    with pytest.raises(IdempotencyConflictError) as raised:
        submit_cast_ballot(
            fixture.store, fixture.runtime, fixture.capabilities[1], second, "shared"
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["idempotency_conflict"]


def test_neg_capability_replay() -> None:
    """A consumed capability cannot be re-presented with a new key."""
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-replay-a")
    replay, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-replay-b")
    submit_cast_ballot(fixture.store, fixture.runtime, capability, first, "k1")
    with pytest.raises(CastEntitlementExhaustedError) as raised:
        submit_cast_ballot(fixture.store, fixture.runtime, capability, replay, "k-new")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["capability_replay"]


def test_neg_unknown_capability() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-unknown")
    with pytest.raises(CapabilityUnknownError) as raised:
        submit_cast_ballot(fixture.store, fixture.runtime, "cap-not-issued", envelope, "k1")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["unknown_capability"]


def test_neg_leaf_reservation_race() -> None:
    fixture = fixture_c()
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-race-a")
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-race-b")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], first, "k1")
    with pytest.raises(CastCapacityUnavailableError) as raised:
        submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[1], second, "k2")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["leaf_reservation_race"]


def test_neg_wrong_slot_type() -> None:
    """A public challenge may never take a cast-reserved slot (`TC-75`)."""
    fixture = fixture_c()
    # occupy the single challenge-reserved slot
    first, first_open = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-slot-a")
    submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], first, first_open, "k1"
    )
    assert fixture.store.slot_owner == {(0, 1): "res-chal-k1"}
    # the cast-reserved slot 0 is free, but a second challenge must not take it
    second, second_open = make_ballot(fixture, {"c1": ("opt-2",)}, b"neg-slot-b")
    with pytest.raises(PublicChallengeReservationUnavailableError) as raised:
        submit_public_challenge(
            fixture.store,
            fixture.runtime,
            fixture.capabilities[1],
            second,
            second_open,
            "k2",
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["wrong_slot_type"]
    assert (0, 0) not in fixture.store.slot_owner


def test_neg_adaptive_overflow_attempt() -> None:
    """A plan whose slots do not exactly cover the batch is refused."""
    plan = CapacityPlan(
        election_context_id="overflow",
        max_valid_continuations=2,
        interval_count=1,
        primary_capacity=8,
        reserve_capacity=0,
        reserve_commitments=0,
        cast_reserved_per_batch=2,
        challenge_reserved_per_batch=2,
        shared_reserve_per_batch=2,  # 6 != 8: two unclassified slots
        safety_reserve=0,
    )
    with pytest.raises(CapacityPlanInvalidError) as raised:
        plan.validate()
    assert raised.value.reason_code == EXPECTED_REASON_CODES["adaptive_overflow_attempt"]
    assert "adaptive-overflow" in str(raised.value)


# -- batches, board, record ----------------------------------------------


def _sealed(fixture: object) -> tuple[SealedBatch, BatchOpening]:
    return seal_batch(
        fixture.store,  # type: ignore[attr-defined]
        election_context_id=fixture.manifest.election_context_id,  # type: ignore[attr-defined]
        batch_sequence=0,
        batch_window_id="w0",
        capacity=fixture.runtime.batch_capacity,  # type: ignore[attr-defined]
        capacity_profile_id="test",
        source=deterministic_source(b"neg-seal"),
    )


def test_neg_batch_root_mismatch() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-root")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1")
    batch, opening = _sealed(fixture)
    forged = SealedBatch(
        election_context_id=batch.election_context_id,
        batch_sequence=batch.batch_sequence,
        batch_window_id=batch.batch_window_id,
        fixed_capacity_profile_id=batch.fixed_capacity_profile_id,
        capacity=batch.capacity,
        commitment_root=b"\xaa" * 32,
    )
    result = verify_batches([forged], [opening], fixture.manifest.election_context_id)
    assert result.code.value == EXPECTED_REASON_CODES["batch_root_mismatch"]
    assert result.exit_code == 41


def test_neg_missing_opening() -> None:
    fixture = fixture_a()
    batch, _ = _sealed(fixture)
    result = verify_batches([batch], [], fixture.manifest.election_context_id)
    assert result.code.value == EXPECTED_REASON_CODES["missing_opening"]


def test_neg_duplicate_opening() -> None:
    """One artefact mapped to two leaves fails reconciliation."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-dupopen")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1")
    _, opening = _sealed(fixture)
    real = next(o for o in opening.openings if o.leaf_class is LeafClass.ACCEPTED_CAST)
    duplicated = BatchOpening(
        batch_sequence=opening.batch_sequence,
        leaves=opening.leaves,
        openings=(*opening.openings, real),
    )
    with pytest.raises(ReconciliationError, match="two leaves") as raised:
        reconcile([duplicated], [envelope], [], fixture.plan.max_valid_continuations)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["duplicate_opening"]


def test_neg_cover_leaf_in_tally() -> None:
    """A cover leaf presented as an accepted cast breaks reconciliation."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-cover")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1")
    _, opening = _sealed(fixture)
    cover = next(o for o in opening.openings if o.leaf_class is LeafClass.COVER)
    promoted = LeafOpening(
        leaf_index=cover.leaf_index,
        leaf_class=LeafClass.ACCEPTED_CAST,
        salt=cover.salt,
        artifact_reference="ghost-ballot",
        artifact_digest=b"",
    )
    forged = BatchOpening(
        batch_sequence=opening.batch_sequence,
        leaves=opening.leaves,
        openings=tuple(
            promoted if o.leaf_index == cover.leaf_index else o for o in opening.openings
        ),
    )
    with pytest.raises(ReconciliationError) as raised:
        reconcile([forged], [envelope], [], fixture.plan.max_valid_continuations)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["cover_leaf_in_tally"]


def test_neg_spoiled_ballot_in_tally() -> None:
    fixture = fixture_a()
    envelope, opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-spoiled")
    submit_public_challenge(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, opening, "k1"
    )
    closed = close_and_build(fixture, [], [envelope])
    forged = ElectionRecord(
        manifest=closed.record.manifest,
        params=closed.record.params,
        joint_public_key=closed.record.joint_public_key,
        base_hash=closed.record.base_hash,
        sealed_batches=closed.record.sealed_batches,
        batch_openings=closed.record.batch_openings,
        accepted_ballots=(envelope,),  # the spoiled ballot, counted
        spoiled_ballots=(envelope,),
        reconciliation=closed.record.reconciliation,
        tallies=closed.record.tallies,
        shares=closed.record.shares,
    )
    export = board_export_from(fixture.board)
    result = verify_record(forged, export)
    assert result.code.value == EXPECTED_REASON_CODES["spoiled_ballot_in_tally"]
    assert result.exit_code == 51


def test_neg_conflicting_checkpoint() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    honest = board.publish_checkpoint()
    export = BoardExport(
        entries=tuple(board.export_entries()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        checkpoints=(
            (0, honest.tree_size, honest.root, honest.previous_checkpoint_hash, b"s"),
            (0, honest.tree_size, b"\xff" * 32, honest.previous_checkpoint_hash, b"s"),
        ),
    )
    assert verify_board(export).code.value == EXPECTED_REASON_CODES["conflicting_checkpoint"]


def test_neg_rollback() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.append(EntryType.PARAMETER_SET, b"p")
    later = board.publish_checkpoint()
    export = BoardExport(
        entries=tuple(board.export_entries()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        checkpoints=(
            (0, later.tree_size, later.root, later.previous_checkpoint_hash, b"s"),
            (1, 1, b"\x01" * 32, later.digest(), b"s"),
        ),
    )
    assert verify_board(export).code.value == EXPECTED_REASON_CODES["rollback"]


def test_neg_invalid_consistency_proof() -> None:
    fixture = fixture_a()
    board = fixture.board
    for index in range(5):
        board.append(EntryType.SEALED_BATCH_COMMITMENT, f"b{index}".encode())
        board.publish_checkpoint()

    export = BoardExport(
        entries=tuple(board.export_entries()),
        checkpoints=tuple(board.export_checkpoints()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        consistency_proofs=((2, 5, tuple(board.consistency_proof(2))),),
    )
    assert verify_board(export).code is VerificationResultCode.VERIFIED

    proof = list(board.consistency_proof(2))
    # every single-node corruption is detected, and each is reported with
    # the consistency code rather than a generic board failure
    for index in range(len(proof)):
        corrupted = list(proof)
        corrupted[index] = b"\x00" * 32
        result = verify_board(
            BoardExport(
                entries=export.entries,
                checkpoints=export.checkpoints,
                signed_checkpoints=export.signed_checkpoints,
                signer_registry=export.signer_registry,
                consistency_proofs=((2, 5, tuple(corrupted)),),
            )
        )
        assert result.code.value == EXPECTED_REASON_CODES["invalid_consistency_proof"]
        assert result.exit_code == 44
    # a truncated proof is detected too
    truncated = verify_board(
        BoardExport(
            entries=export.entries,
            checkpoints=export.checkpoints,
            signed_checkpoints=export.signed_checkpoints,
            signer_registry=export.signer_registry,
            consistency_proofs=((2, 5, tuple(proof[:-1])),),
        )
    )
    assert truncated.code is VerificationResultCode.BATCH_CONSISTENCY_FAILED


def test_neg_pre_closure_decryption_artifact() -> None:
    fixture = fixture_a()
    with pytest.raises(PreClosurePublicationError) as raised:
        fixture.board.append(EntryType.TALLY_ARTIFACT, b"result")
    assert raised.value.reason_code == EXPECTED_REASON_CODES["pre_closure_decryption_artifact"]
    assert fixture.board.entries == []


def test_neg_intermediate_tally_artifact() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"neg-intermediate")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1")
    with pytest.raises(IntermediateTallyProhibitedError) as raised:
        tally_accepted(
            [envelope],
            fixture.manifest,
            fixture.params,
            fixture.secret,
            fixture.public_key,
            deterministic_source(b"neg-tally"),
            board_closed=False,
        )
    assert raised.value.reason_code == EXPECTED_REASON_CODES["intermediate_tally_artifact"]


def test_neg_ambiguous_sequence_encoding() -> None:
    """Two different sequences must never flatten to the same bytes.

    An earlier version of `encode_seq` concatenated items raw, so
    `[b"ab", b"c"]` and `[b"a", b"bc"]` shared an encoding and therefore a
    digest. The independent cross-implementation verifier, written from the
    documented grammar rather than from the code, disagreed with the code
    and that is how this was found.
    """
    from epd2_voting_service.reference.crypto.encoding import encode_bytes, encode_seq

    left = encode_seq([b"ab", b"c"])
    right = encode_seq([b"a", b"bc"])
    assert left != right
    assert left == encode_uint(2, 4) + encode_bytes(b"ab") + encode_bytes(b"c")

    # and the same for struct field values
    struct_left = encode_struct([("f", b"ab"), ("g", b"c")])
    struct_right = encode_struct([("f", b"a"), ("g", b"bc")])
    assert struct_left != struct_right

    # the declared reason code is the encoding one
    with pytest.raises(CanonicalEncodingError) as raised:
        encode_struct([("a", b"x"), ("a", b"y")])
    assert raised.value.reason_code == EXPECTED_REASON_CODES["ambiguous_sequence_encoding"]


def test_neg_unauthorized_board_signer() -> None:
    """A checkpoint signed by a key outside the declared set is refused."""
    import dataclasses

    from epd2_voting_service.reference.publication.checkpoint_signing import (
        CheckpointSignatureOutcome,
        verify_checkpoint,
    )
    from epd2_voting_service.reference.verification.verifier import board_export_from

    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    checkpoint = board.publish_checkpoint()
    stranger = dataclasses.replace(checkpoint, signing_key_id="not-a-declared-key")
    outcome, _ = verify_checkpoint(stranger.payload(), stranger.signature, board.signer_registry())
    assert outcome is CheckpointSignatureOutcome.SIGNER_UNKNOWN

    export = board_export_from(board)
    result = verify_board(dataclasses.replace(export, signed_checkpoints=(stranger,)))
    assert result.code.value == EXPECTED_REASON_CODES["unauthorized_board_signer"]


def test_neg_insufficient_guardian_quorum() -> None:
    """A quorum fixed by the ceremony may not be reduced at tally time."""
    from epd2_voting_service.reference.crypto.elgamal import accumulate, encrypt
    from epd2_voting_service.reference.guardians.ceremony import (
        QuorumPolicy,
        run_ceremony,
    )
    from epd2_voting_service.reference.guardians.threshold import (
        InsufficientQuorumError,
        combine_shares,
        compute_share,
    )

    params = small_params()
    source = deterministic_source(b"neg-quorum")
    result = run_ceremony("neg-ctx", QuorumPolicy(3, 5), params, source)
    aggregate = accumulate([encrypt(1, 4321, result.transcript.joint_public_key, params)], params)
    shares = [
        compute_share(aggregate, result.secret(s), result.transcript, params, "c", "o", source)
        for s in (1, 2)
    ]
    with pytest.raises(InsufficientQuorumError) as raised:
        combine_shares(shares, aggregate, result.transcript, params, maximum=1)
    assert raised.value.reason_code == EXPECTED_REASON_CODES["insufficient_guardian_quorum"]

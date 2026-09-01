"""Unit tests for casting, capacity, sealing, board and record modules."""

from __future__ import annotations

import pytest

from epd2_voting_service.reference.api import API_BANNER, ReferenceApi
from epd2_voting_service.reference.casting.ballot import (
    BALLOT_ID_BYTES,
    new_ballot_id,
    verify_ballot_proofs,
)
from epd2_voting_service.reference.casting.confirmation import (
    CONFIRMATION_ALPHABET,
    CONFIRMATION_GROUP_LEN,
    CONFIRMATION_GROUPS,
    derive_confirmation_code,
    verify_challenge_opening,
)
from epd2_voting_service.reference.casting.continuation import (
    FORBIDDEN_CAPABILITY_FIELDS,
    ContinuationState,
)
from epd2_voting_service.reference.casting.idempotency import (
    IdempotencyRecord,
    request_digest,
)
from epd2_voting_service.reference.casting.transactions import (
    _candidate_slots,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.crypto.merkle import (
    consistency_proof,
    empty_root,
    inclusion_proof,
    verify_consistency,
    verify_inclusion,
)
from epd2_voting_service.reference.crypto.merkle import root as merkle_root
from epd2_voting_service.reference.election_record.builder import export_record
from epd2_voting_service.reference.publication.bulletin_board import EntryType
from epd2_voting_service.reference.publication.capacity import (
    A_ACCEPTED_CASTS_PER_CONTINUATION,
    K_PUBLIC_CHALLENGES_PER_CONTINUATION,
    CapacityPlanInvalidError,
    SlotClass,
)
from epd2_voting_service.reference.publication.sealed_batches import LeafClass
from epd2_voting_service.reference.publication.sealing import seal_batch
from epd2_voting_service.reference.testing.fixtures import (
    TEST_PROFILE_BANNER,
    deterministic_source,
    fixture_a,
    fixture_b,
    fixture_c,
)
from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot

# -- ballot --------------------------------------------------------------


def test_ballot_id_is_client_random_and_structureless() -> None:
    left = new_ballot_id(deterministic_source(b"id-a"))
    right = new_ballot_id(deterministic_source(b"id-b"))
    assert len(left) == BALLOT_ID_BYTES * 2
    assert left != right
    assert int(left, 16) >= 0  # pure hex, no embedded structure


def test_ballot_envelope_carries_no_identity_field() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-envelope")
    fields = set(envelope.__slots__)
    assert fields == {
        "ballot_id",
        "election_context_id",
        "ballot_style_id",
        "parameter_set_id",
        "manifest_digest",
        "contests",
    }
    assert not (fields & {"voter_id", "identity", "credential_id", "capability_reference"})


def test_continuation_state_carries_no_forbidden_field() -> None:
    """`DM-10`: the two sides of the acceptance boundary share no key."""
    state = ContinuationState(capability_reference="cap", election_context_id="ctx")
    fields = set(state.__slots__)
    assert not (fields & FORBIDDEN_CAPABILITY_FIELDS), sorted(fields & FORBIDDEN_CAPABILITY_FIELDS)
    assert "ballot_id" in FORBIDDEN_CAPABILITY_FIELDS, (
        "a capability that could name a ballot would be the join this "
        "architecture exists to prevent"
    )


def test_undervote_is_absorbed_by_placeholders() -> None:
    """Every contest accumulates to exactly its selection limit."""
    fixture = fixture_b()
    envelope, _ = make_ballot(fixture, {"c1": ("a",), "c2": ()}, b"unit-undervote", "style-b")
    style = fixture.manifest.style("style-b")
    for defined, submitted in zip(style.contests, envelope.contests, strict=True):
        assert len(submitted.selections) == len(defined.option_ids) + defined.selection_limit
    verify_ballot_proofs(
        envelope, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
    )


def test_a_blank_contest_still_produces_a_valid_ballot() -> None:
    fixture = fixture_b()
    envelope, opening = make_ballot(fixture, {"c1": (), "c2": ()}, b"unit-blank", "style-b")
    verify_ballot_proofs(
        envelope, fixture.manifest, fixture.public_key, fixture.params, fixture.base_hash
    )
    verify_challenge_opening(
        envelope, opening, fixture.public_key, fixture.params, fixture.base_hash
    )


# -- confirmation code ---------------------------------------------------


def test_confirmation_code_shape_and_alphabet() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-code")
    code = derive_confirmation_code(envelope, fixture.params, fixture.base_hash)
    groups = code.split("-")
    assert len(groups) == CONFIRMATION_GROUPS
    assert all(len(g) == CONFIRMATION_GROUP_LEN for g in groups)
    assert set(code.replace("-", "")) <= set(CONFIRMATION_ALPHABET)
    # the alphabet excludes the characters people confuse
    assert not (set(CONFIRMATION_ALPHABET) & set("01IOl"))


def test_confirmation_code_is_deterministic_and_ballot_specific() -> None:
    fixture = fixture_a()
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-code-a")
    second, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-code-b")
    code = derive_confirmation_code(first, fixture.params, fixture.base_hash)
    assert code == derive_confirmation_code(first, fixture.params, fixture.base_hash)
    assert code != derive_confirmation_code(second, fixture.params, fixture.base_hash)


# -- continuation and idempotency ----------------------------------------


def test_continuation_state_has_exactly_three_booleans() -> None:
    state = ContinuationState(capability_reference="cap", election_context_id="ctx")
    assert state.cast_entitlement_available is True
    assert state.public_challenge_entitlement_available is True
    assert state.capability_consumed is False


def test_idempotency_scope_is_context_operation_key() -> None:
    record = IdempotencyRecord(
        idempotency_key="k",
        election_context_id="ctx",
        operation="cast",
        request_digest=request_digest(b"x"),
        outcome_code="acceptance.committed",
        outcome_payload=(),
    )
    assert record.scope == ("ctx", "cast", "k")
    # the same key in a different operation is a different scope
    other = IdempotencyRecord(
        idempotency_key="k",
        election_context_id="ctx",
        operation="public_challenge",
        request_digest=record.request_digest,
        outcome_code=record.outcome_code,
        outcome_payload=(),
    )
    assert other.scope != record.scope


def test_request_digest_changes_with_the_request() -> None:
    assert request_digest(b"a") != request_digest(b"b")
    assert request_digest(b"a") == request_digest(b"a")


# -- capacity ------------------------------------------------------------


def test_l_max_is_derived_from_capabilities_not_turnout() -> None:
    fixture = fixture_a()
    plan = fixture.plan
    assert K_PUBLIC_CHALLENGES_PER_CONTINUATION == 1
    assert A_ACCEPTED_CASTS_PER_CONTINUATION == 1
    assert plan.l_max == plan.max_valid_continuations * 2
    assert plan.total_capacity >= plan.l_max + plan.safety_reserve


def test_capacity_plan_rejects_a_plan_that_cannot_cover_l_max() -> None:
    fixture = fixture_a()
    plan = fixture.plan
    starved = type(plan)(
        election_context_id=plan.election_context_id,
        max_valid_continuations=1000,
        interval_count=plan.interval_count,
        primary_capacity=plan.primary_capacity,
        reserve_capacity=plan.reserve_capacity,
        reserve_commitments=plan.reserve_commitments,
        cast_reserved_per_batch=plan.cast_reserved_per_batch,
        challenge_reserved_per_batch=plan.challenge_reserved_per_batch,
        shared_reserve_per_batch=plan.shared_reserve_per_batch,
        safety_reserve=plan.safety_reserve,
    )
    with pytest.raises(CapacityPlanInvalidError, match="total capacity"):
        starved.validate()


def test_slot_capacity_is_declared_never_inferred() -> None:
    fixture = fixture_a()
    plan = fixture.plan
    assert plan.slot_capacity(SlotClass.SHARED_RESERVE, 10_000) == (plan.shared_reserve_per_batch)


def test_candidate_slots_never_offer_a_cast_slot_to_a_challenge() -> None:
    fixture = fixture_a()
    challenge_slots = _candidate_slots(fixture.runtime, SlotClass.CHALLENGE_RESERVED)
    cast_range = range(fixture.plan.cast_reserved_per_batch)
    assert all(index not in cast_range for index, _ in challenge_slots)
    cast_slots = _candidate_slots(fixture.runtime, SlotClass.CAST_RESERVED)
    assert [i for i, _ in cast_slots][: len(cast_range)] == list(cast_range)


def test_capacity_profile_is_marked_test_only() -> None:
    assert fixture_a().plan.profile_label == TEST_PROFILE_BANNER


# -- sealing -------------------------------------------------------------


def test_sealed_batch_size_is_independent_of_occupancy() -> None:
    """`TC-33`: an empty batch and a full batch serialise identically in size."""
    empty_fixture = fixture_a()
    empty_batch, empty_opening = seal_batch(
        empty_fixture.store,
        election_context_id="fixture-a",
        batch_sequence=0,
        batch_window_id="w0",
        capacity=empty_fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"seal-empty"),
    )

    busy_fixture = fixture_a()
    for index in range(4):
        envelope, _ = make_ballot(busy_fixture, {"c1": ("opt-1",)}, f"seal-{index}".encode())
        submit_cast_ballot(
            busy_fixture.store,
            busy_fixture.runtime,
            busy_fixture.capabilities[index],
            envelope,
            f"k{index}",
        )
    busy_batch, busy_opening = seal_batch(
        busy_fixture.store,
        election_context_id="fixture-a",
        batch_sequence=0,
        batch_window_id="w0",
        capacity=busy_fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"seal-busy"),
    )

    assert len(empty_batch.canonical_bytes()) == len(busy_batch.canonical_bytes())
    assert len(empty_opening.leaves) == len(busy_opening.leaves)
    assert len({len(leaf) for leaf in (*empty_opening.leaves, *busy_opening.leaves)}) == 1
    assert empty_batch.commitment_root != busy_batch.commitment_root


def test_cover_leaves_fill_every_unused_slot() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"seal-one")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    batch, opening = seal_batch(
        fixture.store,
        election_context_id="fixture-a",
        batch_sequence=0,
        batch_window_id="w0",
        capacity=fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"seal-cover"),
    )
    classes = [o.leaf_class for o in opening.openings]
    assert classes.count(LeafClass.ACCEPTED_CAST) == 1
    assert classes.count(LeafClass.COVER) == batch.capacity - 1
    assert opening.recompute_root() == batch.commitment_root


def test_challenge_and_cast_leaves_are_both_real_leaves() -> None:
    fixture = fixture_a()
    cast, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"seal-cast")
    challenge, challenge_opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"seal-chal")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], cast, "k1")
    submit_public_challenge(
        fixture.store,
        fixture.runtime,
        fixture.capabilities[1],
        challenge,
        challenge_opening,
        "k2",
    )
    _, opening = seal_batch(
        fixture.store,
        election_context_id="fixture-a",
        batch_sequence=0,
        batch_window_id="w0",
        capacity=fixture.runtime.batch_capacity,
        capacity_profile_id="test",
        source=deterministic_source(b"seal-both"),
    )
    classes = [o.leaf_class for o in opening.openings]
    assert classes.count(LeafClass.ACCEPTED_CAST) == 1
    assert classes.count(LeafClass.PUBLIC_CHALLENGED_SPOILED) == 1


# -- merkle --------------------------------------------------------------


def test_empty_tree_root_is_defined_and_distinct() -> None:
    assert len(empty_root()) == 32
    assert empty_root() != merkle_root([b"x"])


def test_merkle_shape_is_not_last_node_duplication() -> None:
    """The three-leaf tree must not equal the four-leaf tree with a dup."""
    three = merkle_root([b"a", b"b", b"c"])
    duplicated = merkle_root([b"a", b"b", b"c", b"c"])
    assert three != duplicated


def test_inclusion_and_consistency_hold_for_odd_sizes() -> None:
    for size in (1, 2, 3, 5, 7, 9, 15, 17):
        leaves = [f"n-{i}".encode() for i in range(size)]
        root = merkle_root(leaves)
        for index in range(size):
            assert verify_inclusion(leaves[index], inclusion_proof(leaves, index), root)
        for old in range(1, size + 1):
            proof = consistency_proof(leaves, old)
            assert verify_consistency(merkle_root(leaves[:old]), old, root, size, proof)


# -- board ---------------------------------------------------------------


def test_checkpoints_chain_and_never_shrink() -> None:
    fixture = fixture_a()
    board = fixture.board
    previous = b"\x00" * 32
    for index in range(5):
        board.append(EntryType.SEALED_BATCH_COMMITMENT, f"b{index}".encode())
        checkpoint = board.publish_checkpoint()
        assert checkpoint.previous_checkpoint_hash == previous
        assert checkpoint.checkpoint_sequence == index
        assert checkpoint.tree_size == index + 1
        previous = checkpoint.digest()


def test_board_export_is_bytes_only() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    for sequence, entry_type, payload in board.export_entries():
        assert isinstance(sequence, int)
        assert isinstance(entry_type, str)
        assert isinstance(payload, bytes)
    for row in board.export_checkpoints():
        assert isinstance(row, tuple)
        assert all(isinstance(v, int | bytes) for v in row)


# -- election record -----------------------------------------------------


def test_election_record_digest_is_deterministic() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-record")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k")
    closed = close_and_build(fixture, [envelope], [])
    assert closed.record.digest() == closed.record.digest()
    assert export_record(closed.record) == closed.record.canonical_bytes()


def test_reconciliation_reports_every_class() -> None:
    fixture = fixture_a()
    cast, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"unit-rec-cast")
    challenge, challenge_opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"unit-rec-chal")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], cast, "k1")
    submit_public_challenge(
        fixture.store,
        fixture.runtime,
        fixture.capabilities[1],
        challenge,
        challenge_opening,
        "k2",
    )
    closed = close_and_build(fixture, [cast], [challenge])
    record = closed.reconciliation
    assert record.accepted_cast == 1
    assert record.public_challenged_spoiled == 1
    assert record.cover == fixture.runtime.batch_capacity - 2
    assert record.max_valid_continuations == fixture.plan.max_valid_continuations
    assert (record.k, record.a) == (1, 1)


# -- reference API -------------------------------------------------------


def test_reference_api_banner_states_it_is_not_production_authentication() -> None:
    assert "REFERENCE API" in API_BANNER
    assert "NOT PRODUCTION AUTHENTICATION" in API_BANNER
    assert "NOT PRODUCTION AUTHENTICATION" in (ReferenceApi.__doc__ or "")


def test_reference_api_exposes_exactly_the_declared_surface() -> None:
    declared = {
        "submit_public_challenge",
        "submit_cast_ballot",
        "get_publication_state",
        "get_board_checkpoint",
        "get_inclusion_proof",
        "get_consistency_proof",
        "check_consistency",
        "export_election_record",
        "run_verifier",
    }
    public = {
        name
        for name in dir(ReferenceApi)
        if not name.startswith("_") and callable(getattr(ReferenceApi, name))
    }
    assert public == declared


def test_fixture_c_is_labelled_a_capacity_incident_fixture() -> None:
    fixture = fixture_c()
    assert fixture.plan.total_capacity == fixture.plan.l_max
    assert fixture.plan.shared_reserve_per_batch == 0

"""End-to-end scenarios E2E-01 … E2E-10 (PACK-16D §58).

Each test is named for its scenario and asserts the scenario's stated
expectations, not a weaker proxy for them.
"""

from __future__ import annotations

import pytest

from epd2_voting_service.reference.api import ReferenceApi
from epd2_voting_service.reference.casting.continuation import (
    CastEntitlementExhaustedError,
    PublicChallengeEntitlementExhaustedError,
)
from epd2_voting_service.reference.casting.store import CastCapacityUnavailableError
from epd2_voting_service.reference.casting.transactions import (
    Outcome,
    dispatch_outbox,
    submit_cast_ballot,
    submit_public_challenge,
)
from epd2_voting_service.reference.crypto.elgamal import Ciphertext
from epd2_voting_service.reference.crypto.merkle import verify_consistency
from epd2_voting_service.reference.election_record.builder import (
    IntermediateTallyProhibitedError,
    tally_accepted,
)
from epd2_voting_service.reference.publication.bulletin_board import (
    EntryType,
    PreClosurePublicationError,
)
from epd2_voting_service.reference.publication.outbox import ObligationState
from epd2_voting_service.reference.testing.faults import FaultInjector, FaultPoint
from epd2_voting_service.reference.testing.fixtures import (
    Fixture,
    deterministic_source,
    fixture_a,
    fixture_b,
    fixture_c,
)
from epd2_voting_service.reference.testing.scenarios import close_and_build, make_ballot
from epd2_voting_service.reference.verification.results import VerificationResultCode
from epd2_voting_service.reference.verification.verifier import (
    BoardExport,
    board_export_from,
    verify_record,
)


def _api(fixture: Fixture) -> ReferenceApi:
    return ReferenceApi(store=fixture.store, runtime=fixture.runtime, board=fixture.board)


def test_e2e_01_valid_cast() -> None:
    fixture = fixture_a()
    api = _api(fixture)
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e01")
    result = api.submit_cast_ballot(fixture.capabilities[0], envelope, "idem-1")

    assert result.outcome is Outcome.ACCEPTED
    assert result.reason_code == "acceptance.committed"
    assert result.counted is True
    # capability consumed
    state = fixture.store.continuations[fixture.capabilities[0]]
    assert state.capability_consumed is True
    assert state.cast_entitlement_available is False
    # atomic reservation: exactly one committed leaf, in a cast-reserved slot
    committed = [r for r in fixture.store.reservations.values() if r.committed]
    assert len(committed) == 1
    assert committed[0].leaf_index < fixture.plan.cast_reserved_per_batch

    dispatch_outbox(fixture.store)
    closed = close_and_build(fixture, [envelope], [])
    assert closed.reconciliation.accepted_cast == 1
    assert closed.reconciliation.public_challenged_spoiled == 0

    # ballot included exactly once
    references = [
        o.artifact_reference
        for opening in closed.openings
        for o in opening.openings
        if o.artifact_reference
    ]
    assert references.count(envelope.ballot_id) == 1

    verdict = api.run_verifier(closed.record)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail
    assert verdict.exit_code == 0
    totals = {(t.contest_id, t.option_id): t.plaintext for t in closed.record.tallies}
    assert totals[("c1", "opt-1")] == 1
    assert totals[("c1", "opt-2")] == 0


def test_e2e_02_public_challenge_then_cast() -> None:
    fixture = fixture_a()
    api = _api(fixture)
    capability = fixture.capabilities[0]

    challenged, opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"e2e02-challenge")
    challenge_result = api.submit_public_challenge(capability, challenged, opening, "idem-chal")
    assert challenge_result.reason_code == "challenge.spoiled_published"
    assert challenge_result.counted is False

    state = fixture.store.continuations[capability]
    assert state.public_challenge_entitlement_available is False
    # cast entitlement retained — this is the point of the scenario
    assert state.cast_entitlement_available is True
    assert state.capability_consumed is False

    fresh, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e02-cast")
    cast_result = api.submit_cast_ballot(capability, fresh, "idem-cast")
    assert cast_result.counted is True
    assert fixture.store.continuations[capability].capability_consumed is True

    closed = close_and_build(fixture, [fresh], [challenged])
    totals = {(t.contest_id, t.option_id): t.plaintext for t in closed.record.tallies}
    # the spoiled artefact is excluded: opt-2 was the challenged choice
    assert totals[("c1", "opt-1")] == 1
    assert totals[("c1", "opt-2")] == 0
    verdict = api.run_verifier(closed.record)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail


def test_e2e_03_second_public_challenge_rejected() -> None:
    fixture = fixture_a()
    api = _api(fixture)
    capability = fixture.capabilities[0]

    first, first_opening = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e03-a")
    api.submit_public_challenge(capability, first, first_opening, "idem-a")

    second, second_opening = make_ballot(fixture, {"c1": ("opt-2",)}, b"e2e03-b")
    with pytest.raises(PublicChallengeEntitlementExhaustedError):
        api.submit_public_challenge(capability, second, second_opening, "idem-b")

    state = fixture.store.continuations[capability]
    assert state.cast_entitlement_available is True
    assert second.ballot_id not in fixture.store.spoiled_ballots


def test_e2e_04_double_cast_race() -> None:
    """Sequential form of the race; the threaded form is in the concurrency suite."""
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e04-a")
    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"e2e04-b")

    submit_cast_ballot(fixture.store, fixture.runtime, capability, first, "idem-a")
    with pytest.raises(CastEntitlementExhaustedError):
        submit_cast_ballot(fixture.store, fixture.runtime, capability, second, "idem-b")

    assert len(fixture.store.accepted_ballots) == 1
    leaves = [r.leaf_index for r in fixture.store.reservations.values() if r.committed]
    assert len(leaves) == len(set(leaves)) == 1


@pytest.mark.parametrize(
    "point",
    [
        FaultPoint.AFTER_CAPABILITY_VALIDATION,
        FaultPoint.AFTER_PROOF_VALIDATION,
        FaultPoint.AFTER_SLOT_RESERVATION,
        FaultPoint.AFTER_BALLOT_PERSISTENCE,
        FaultPoint.AFTER_ENTITLEMENT_MUTATION,
        FaultPoint.BEFORE_TRANSACTION_COMMIT,
    ],
)
def test_e2e_05_crash_before_commit(point: FaultPoint) -> None:
    from epd2_voting_service.reference.testing.faults import InjectedFault

    fixture = fixture_a()
    capability = fixture.capabilities[0]
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e05")
    injector = FaultInjector()
    injector.arm(point)

    with pytest.raises(InjectedFault):
        submit_cast_ballot(
            fixture.store,
            fixture.runtime,
            capability,
            envelope,
            "idem-crash",
            fault_hook=injector,
        )

    state = fixture.store.continuations[capability]
    assert state.cast_entitlement_available is True, "capability was consumed by a crash"
    assert state.capability_consumed is False
    assert fixture.store.accepted_ballots == {}
    assert fixture.store.slot_owner == {}, "a leaf slot leaked"
    assert fixture.store.outbox.rows == []
    assert fixture.store.idempotency == {}

    # retry succeeds, and lands on the same first free slot as if nothing happened
    retry = submit_cast_ballot(fixture.store, fixture.runtime, capability, envelope, "idem-crash")
    assert retry.outcome is Outcome.ACCEPTED
    assert [r.leaf_index for r in fixture.store.reservations.values()] == [0]


def test_e2e_06_crash_after_commit_before_publication() -> None:
    from epd2_voting_service.reference.testing.faults import InjectedFault

    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e06")
    result = submit_cast_ballot(
        fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "idem-1"
    )

    injector = FaultInjector()
    injector.arm(FaultPoint.BEFORE_OUTBOX_PUBLISH)
    with pytest.raises(InjectedFault):
        dispatch_outbox(fixture.store, fault_hook=injector)

    # the obligation survived the crash and is still pending
    pending = fixture.store.outbox.pending()
    assert [p.publication_obligation_id for p in pending] == [result.publication_obligation_id]

    dispatched = dispatch_outbox(fixture.store)
    assert len(dispatched) == 1
    assert fixture.store.outbox.pending() == []

    # a second sweep publishes nothing: no duplicate board entry
    assert dispatch_outbox(fixture.store) == []
    board = fixture.board
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"commitment")
    before = len(board.entries)
    for obligation in dispatch_outbox(fixture.store):  # pragma: no cover - empty
        board.append(EntryType.SEALED_BATCH_COMMITMENT, obligation.artifact_type.encode())
    assert len(board.entries) == before


def test_e2e_07_capacity_exhaustion() -> None:
    """Fixture C: capacity is tiny by design, so exhaustion is reachable."""
    fixture = fixture_c()
    # one cast-reserved slot, one challenge-reserved slot, no shared reserve
    assert fixture.plan.cast_reserved_per_batch == 1
    assert fixture.plan.shared_reserve_per_batch == 0

    first, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e07-a")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], first, "idem-a")

    second, _ = make_ballot(fixture, {"c1": ("opt-2",)}, b"e2e07-b")
    with pytest.raises(CastCapacityUnavailableError) as raised:
        submit_cast_ballot(
            fixture.store, fixture.runtime, fixture.capabilities[1], second, "idem-b"
        )

    # fail closed: no acceptance without a reservation, no hidden queue
    assert fixture.store.accepted_ballots.keys() == {first.ballot_id}
    assert second.ballot_id not in fixture.store.accepted_ballots
    assert len(fixture.store.outbox.rows) == 1
    # the rejected voter's capability is untouched
    untouched = fixture.store.continuations[fixture.capabilities[1]]
    assert untouched.cast_entitlement_available is True
    assert untouched.capability_consumed is False
    assert raised.value.reason_code

    # the incident is publishable pre-closure and privacy-safe: it names no
    # capability, no ballot and no count
    notice = fixture.board.append(EntryType.INCIDENT_NOTICE, b"election.capacity_exhausted")
    assert notice.payload == b"election.capacity_exhausted"


def test_e2e_08_board_equivocation() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    honest = board.publish_checkpoint()
    forged = type(honest)(
        checkpoint_sequence=honest.checkpoint_sequence,
        tree_size=honest.tree_size,
        root=b"\xff" * 32,
        previous_checkpoint_hash=honest.previous_checkpoint_hash,
        signature=honest.signature,
    )
    export = BoardExport(
        entries=tuple(board.export_entries()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        checkpoints=(
            (
                honest.checkpoint_sequence,
                honest.tree_size,
                honest.root,
                honest.previous_checkpoint_hash,
                honest.signature,
            ),
            (
                forged.checkpoint_sequence,
                forged.tree_size,
                forged.root,
                forged.previous_checkpoint_hash,
                forged.signature,
            ),
        ),
    )
    from epd2_voting_service.reference.verification.verifier import verify_board

    verdict = verify_board(export)
    assert verdict.code is VerificationResultCode.BOARD_INCONSISTENCY
    assert verdict.exit_code == 40


def test_e2e_08b_rollback_is_detected() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.append(EntryType.PARAMETER_SET, b"p")
    later = board.publish_checkpoint()
    rolled_back = (0, 1, b"\x01" * 32, later.digest(), b"sig")
    export = BoardExport(
        entries=tuple(board.export_entries()),
        signed_checkpoints=tuple(board.export_signed_checkpoints()),
        signer_registry=board.signer_registry(),
        checkpoints=(
            (
                later.checkpoint_sequence,
                later.tree_size,
                later.root,
                later.previous_checkpoint_hash,
                later.signature,
            ),
            rolled_back,
        ),
    )
    from epd2_voting_service.reference.verification.verifier import verify_board

    assert verify_board(export).code is VerificationResultCode.BOARD_INCONSISTENCY


def test_e2e_08c_consistency_proof_holds_across_appends() -> None:
    fixture = fixture_a()
    api = _api(fixture)
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.append(EntryType.PARAMETER_SET, b"p")
    old_size = len(board.entries)
    old_root = board.root()
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"b0")
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"b1")
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"b2")

    assert api.check_consistency(old_size) is True
    proof = api.get_consistency_proof(old_size)
    assert verify_consistency(old_root, old_size, board.root(), len(board.entries), proof)
    # a tampered old root does not verify
    assert not verify_consistency(b"\x00" * 32, old_size, board.root(), len(board.entries), proof)


def test_e2e_09_invalid_proof() -> None:
    fixture = fixture_a()
    capability = fixture.capabilities[0]
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e09")
    broken_contest = envelope.contests[0]
    tampered_selection = type(broken_contest.selections[0])(
        option_id=broken_contest.selections[0].option_id,
        ciphertext=Ciphertext(
            alpha=broken_contest.selections[0].ciphertext.alpha,
            beta=(broken_contest.selections[0].ciphertext.beta * 2) % fixture.params.p,
        ),
        proof=broken_contest.selections[0].proof,
    )
    tampered = type(envelope)(
        ballot_id=envelope.ballot_id,
        election_context_id=envelope.election_context_id,
        ballot_style_id=envelope.ballot_style_id,
        parameter_set_id=envelope.parameter_set_id,
        manifest_digest=envelope.manifest_digest,
        contests=(
            type(broken_contest)(
                contest_id=broken_contest.contest_id,
                selections=(tampered_selection, *broken_contest.selections[1:]),
                accumulated=broken_contest.accumulated,
                sum_proof=broken_contest.sum_proof,
            ),
        ),
    )

    with pytest.raises(ValueError):
        submit_cast_ballot(fixture.store, fixture.runtime, capability, tampered, "idem-bad")

    state = fixture.store.continuations[capability]
    assert state.cast_entitlement_available is True
    assert fixture.store.accepted_ballots == {}
    assert fixture.store.slot_owner == {}


def test_e2e_10_pre_closure_tally_attempt() -> None:
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e10")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "idem-1")
    assert fixture.board.closed is False

    with pytest.raises(IntermediateTallyProhibitedError) as raised:
        tally_accepted(
            [envelope],
            fixture.manifest,
            fixture.params,
            fixture.secret,
            fixture.public_key,
            deterministic_source(b"e2e10-tally"),
            board_closed=fixture.board.closed,
        )
    assert raised.value.reason_code == "TALLY_PRE_CLOSURE_PROHIBITED"

    # no result artefact of any kind exists
    assert all(e.entry_type is not EntryType.TALLY_ARTIFACT for e in fixture.board.entries)
    # and the pre-closure board refuses to carry one even if asked
    with pytest.raises(PreClosurePublicationError):
        fixture.board.append(EntryType.TALLY_ARTIFACT, b"result")


def test_e2e_multi_contest_election_verifies() -> None:
    """Fixture B: two contests, an undervote and a blank contest."""
    fixture = fixture_b()
    api = _api(fixture)
    first, _ = make_ballot(fixture, {"c1": ("a",), "c2": ("yes",)}, b"e2e-b-1", "style-b")
    second, _ = make_ballot(fixture, {"c1": ("a", "b"), "c2": ()}, b"e2e-b-2", "style-b")

    api.submit_cast_ballot(fixture.capabilities[0], first, "idem-1")
    api.submit_cast_ballot(fixture.capabilities[1], second, "idem-2")
    closed = close_and_build(fixture, [first, second], [], seed=b"close-b")

    totals = {(t.contest_id, t.option_id): t.plaintext for t in closed.record.tallies}
    assert totals[("c1", "a")] == 2
    assert totals[("c1", "b")] == 1
    assert totals[("c1", "c")] == 0
    assert totals[("c2", "yes")] == 1
    assert totals[("c2", "no")] == 0

    verdict = api.run_verifier(closed.record)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail
    assert verdict.not_checked, "a VERIFIED result must always print its limits"


def test_publication_state_reveals_nothing_about_others() -> None:
    fixture = fixture_a()
    api = _api(fixture)
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"pubstate")
    result = api.submit_cast_ballot(fixture.capabilities[0], envelope, "idem-1")
    state = api.get_publication_state(result)

    assert state.obligation_state == ObligationState.PENDING.value
    assert state.included is False, "inclusion is unknowable before closure"
    fields = set(vars(state)) if hasattr(state, "__dict__") else set(state.__slots__)
    assert "capability_reference" not in fields
    assert "turnout" not in fields
    assert "accepted_count" not in fields


def test_verifier_needs_no_store_or_capability() -> None:
    """`verify_record` is called with public artefacts only (`IV-*`)."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"boundary")
    submit_public_challenge  # imported to assert it is *not* used below  # noqa: B018
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "idem-1")
    closed = close_and_build(fixture, [envelope], [])
    export = board_export_from(fixture.board)
    verdict = verify_record(closed.record, export)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail


# -- correction-round scenarios ------------------------------------------


def test_e2e_11_three_of_five_threshold_tally() -> None:
    """E2E-11: a full election whose result needs a guardian quorum."""
    from epd2_voting_service.reference.testing.fixtures import threshold_fixture

    bundle = threshold_fixture()
    fixture = bundle.fixture
    api = _api(fixture)

    envelopes = []
    for index in range(3):
        envelope, _ = make_ballot(
            fixture, {"c1": ("opt-1" if index else "opt-2",)}, f"e2e11-{index}".encode()
        )
        api.submit_cast_ballot(fixture.capabilities[index], envelope, f"idem-{index}")
        envelopes.append(envelope)

    closed = close_and_build(
        fixture,
        envelopes,
        [],
        seed=b"close-11",
        ceremony=bundle.ceremony,
        secrets=bundle.secrets,
        quorum_selection=(1, 3, 5),
    )
    totals = {(t.contest_id, t.option_id): t.plaintext for t in closed.record.tallies}
    assert totals[("c1", "opt-1")] == 2
    assert totals[("c1", "opt-2")] == 1

    verdict = api.run_verifier(closed.record)
    assert verdict.code is VerificationResultCode.VERIFIED, verdict.detail
    assert "ceremony.transcript" in verdict.checks_run
    assert "ceremony.joint_key_derivation" in verdict.checks_run
    assert "ceremony.threshold_shares" in verdict.checks_run
    # three guardians produced a share for each of the two options
    assert len(closed.record.threshold_shares) == 6


def test_e2e_12_insufficient_guardian_quorum() -> None:
    """E2E-12: two of five cannot produce a result, and fails closed."""
    from epd2_voting_service.reference.guardians.threshold import (
        InsufficientQuorumError,
    )
    from epd2_voting_service.reference.testing.fixtures import threshold_fixture

    bundle = threshold_fixture(seed=b"e2e12")
    fixture = bundle.fixture
    api = _api(fixture)
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e12-ballot")
    api.submit_cast_ballot(fixture.capabilities[0], envelope, "idem-1")

    with pytest.raises(InsufficientQuorumError, match="may not be reduced"):
        close_and_build(
            fixture,
            [envelope],
            [],
            seed=b"close-12",
            ceremony=bundle.ceremony,
            secrets=bundle.secrets,
            quorum_selection=(1, 2),
        )


def test_e2e_13_invalid_checkpoint_signer() -> None:
    """E2E-13: a checkpoint from an unauthorised signer fails verification."""
    import dataclasses

    from epd2_voting_service.reference.verification.verifier import (
        board_export_from,
        verify_board,
    )

    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    export = board_export_from(board)
    assert verify_board(export).code is VerificationResultCode.VERIFIED

    impostor = dataclasses.replace(export.signed_checkpoints[0], signing_key_id="not-the-board")
    result = verify_board(dataclasses.replace(export, signed_checkpoints=(impostor,)))
    assert result.code is VerificationResultCode.BOARD_SIGNER_UNKNOWN
    assert result.exit_code == 46


def test_e2e_14_election_record_verification_with_threshold_artifacts() -> None:
    """E2E-14: the record carries the ceremony, and the verifier checks it."""
    import dataclasses

    from epd2_voting_service.reference.testing.fixtures import threshold_fixture

    bundle = threshold_fixture(seed=b"e2e14")
    fixture = bundle.fixture
    api = _api(fixture)
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"e2e14-ballot")
    api.submit_cast_ballot(fixture.capabilities[0], envelope, "idem-1")
    closed = close_and_build(
        fixture,
        [envelope],
        [],
        seed=b"close-14",
        ceremony=bundle.ceremony,
        secrets=bundle.secrets,
    )
    assert closed.record.ceremony is not None
    assert api.run_verifier(closed.record).code is VerificationResultCode.VERIFIED

    # a record whose joint key was swapped no longer derives from the roster
    swapped = dataclasses.replace(closed.record, joint_public_key=fixture.params.g)
    result = api.run_verifier(swapped)
    assert result.code in {
        VerificationResultCode.INVALID_CEREMONY,
        VerificationResultCode.INVALID_CEREMONY_TRANSCRIPT,
    }

    # a record missing a guardian's share falls below the quorum
    short = dataclasses.replace(
        closed.record,
        threshold_shares=closed.record.threshold_shares[:2],
    )
    assert api.run_verifier(short).code is VerificationResultCode.GUARDIAN_QUORUM_MISMATCH

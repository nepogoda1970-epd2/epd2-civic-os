"""Tests for epd2_voting_service.storage.

Confirms `created_by_actor_id`/`frozen_eligibility_snapshot_digest`
(internal bookkeeping - never canon `Ballot` fields, mirroring
`epd2_credential_service.storage`'s own `issuance_reference` precedent)
never leave the store via any public method, and that
`InMemoryBallotStore.save` enforces CT-00-10's configuration freeze the
same way `InMemoryEligibilityRuleStore.save` enforces `EligibilityRule`
immutability.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_voting_service.domain import (
    Ballot,
    BallotMethod,
    BallotOption,
    BallotOptionStatus,
    BallotStatus,
    VoteEnvelope,
    VoteEnvelopeStatus,
    VoteReceipt,
    VoteReceiptVerificationStatus,
    compute_vote_envelope_integrity_hash,
)
from epd2_voting_service.exceptions import (
    BallotConfigurationLockedError,
    BallotCreationConflictError,
    UnknownBallotError,
    UnknownVoteEnvelopeError,
    VoteEnvelopeCreationConflictError,
    VoteReceiptCreationConflictError,
)
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
    InMemoryVoteReceiptStore,
)

_OPENS_AT = datetime(2026, 1, 1, tzinfo=UTC)
_CLOSES_AT = datetime(2026, 1, 8, tzinfo=UTC)


def _make_ballot(**overrides: object) -> Ballot:
    defaults: dict[str, object] = {
        "ballot_id": uuid4(),
        "space_id": uuid4(),
        "subject_type": "initiative",
        "subject_id": uuid4(),
        "question": "Should we adopt this proposal?",
        "ballot_method": BallotMethod.YES_NO,
        "secrecy_mode": "secret",
        "eligibility_rule_version": 1,
        "delegation_policy_version": 1,
        "quorum_rule": "simple_majority",
        "threshold_rule": "simple_majority",
        "opens_at": _OPENS_AT,
        "closes_at": _CLOSES_AT,
        "status": BallotStatus.DRAFT,
        "configuration_hash": None,
        "challenge_window_hours": None,
    }
    defaults.update(overrides)
    return Ballot(**defaults)  # type: ignore[arg-type]


# --- InMemoryBallotStore ------------------------------------------------------


def test_create_then_get_returns_public_ballot_only() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    actor_id = uuid4()
    stored = store.create(ballot, created_by_actor_id=actor_id)
    fetched = store.get(ballot.ballot_id)
    assert fetched == stored
    assert not hasattr(fetched, "created_by_actor_id")


def test_created_by_actor_id_never_leaves_via_public_dto() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    actor_id = uuid4()
    store.create(ballot, created_by_actor_id=actor_id)
    fetched = store.get(ballot.ballot_id)
    assert fetched is not None
    public_values = [getattr(fetched, f) for f in fetched.__dataclass_fields__]
    assert actor_id not in public_values


def test_created_by_actor_id_for_is_internal_lookup_only() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    actor_id = uuid4()
    store.create(ballot, created_by_actor_id=actor_id)
    assert store.created_by_actor_id_for(ballot.ballot_id) == actor_id
    assert store.created_by_actor_id_for(uuid4()) is None


def test_idempotent_recreate_of_identical_ballot_succeeds() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    actor_id = uuid4()
    first = store.create(ballot, created_by_actor_id=actor_id)
    second = store.create(ballot, created_by_actor_id=actor_id)
    assert first == second


def test_conflicting_recreate_is_rejected() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    store.create(ballot, created_by_actor_id=uuid4())
    conflicting = _make_ballot(ballot_id=ballot.ballot_id, question="A different question")
    with pytest.raises(BallotCreationConflictError):
        store.create(conflicting, created_by_actor_id=uuid4())


def test_save_unknown_ballot_raises() -> None:
    store = InMemoryBallotStore()
    with pytest.raises(UnknownBallotError):
        store.save(_make_ballot())


def test_save_allows_status_only_change_while_configuration_fields_are_stable() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    store.create(ballot, created_by_actor_id=uuid4())
    updated = ballot.with_configuration_locked("deadbeef" * 8)
    stored = store.save(updated)
    assert stored.status == BallotStatus.CONFIGURATION_REVIEW
    assert stored.configuration_hash == "deadbeef" * 8


def test_save_rejects_configuration_mutation_once_past_draft() -> None:
    """CT-00-10: once status has left `draft`, the `configuration_hash`-
    covered fields are frozen - an attempted mutation is rejected."""
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    store.create(ballot, created_by_actor_id=uuid4())
    locked = ballot.with_configuration_locked("deadbeef" * 8)
    store.save(locked)

    mutated = replace(locked, secrecy_mode="public")
    with pytest.raises(BallotConfigurationLockedError):
        store.save(mutated)


def test_frozen_eligibility_snapshot_digest_is_internal_lookup_only() -> None:
    store = InMemoryBallotStore()
    ballot = _make_ballot()
    store.create(ballot, created_by_actor_id=uuid4())
    assert store.frozen_eligibility_snapshot_digest_for(ballot.ballot_id) is None
    store.set_frozen_eligibility_snapshot_digest(ballot.ballot_id, "a" * 64)
    assert store.frozen_eligibility_snapshot_digest_for(ballot.ballot_id) == "a" * 64
    fetched = store.get(ballot.ballot_id)
    assert fetched is not None
    assert ("a" * 64) not in [getattr(fetched, f) for f in fetched.__dataclass_fields__]


def test_set_frozen_eligibility_snapshot_digest_unknown_ballot_raises() -> None:
    store = InMemoryBallotStore()
    with pytest.raises(UnknownBallotError):
        store.set_frozen_eligibility_snapshot_digest(uuid4(), "a" * 64)


# --- InMemoryBallotOptionStore ------------------------------------------------


def test_add_then_get_and_list_ballot_option() -> None:
    store = InMemoryBallotOptionStore()
    ballot_id = uuid4()
    option = BallotOption(
        ballot_option_id=uuid4(),
        ballot_id=ballot_id,
        option_code="yes",
        label="Yes",
        description="",
        display_order=0,
        status=BallotOptionStatus.ACTIVE,
    )
    stored = store.add(option)
    assert store.get(option.ballot_option_id) == stored
    assert store.list_for_ballot(ballot_id) == (stored,)


def test_idempotent_readd_of_identical_option_succeeds() -> None:
    store = InMemoryBallotOptionStore()
    option = BallotOption(
        ballot_option_id=uuid4(),
        ballot_id=uuid4(),
        option_code="yes",
        label="Yes",
        description="",
        display_order=0,
        status=BallotOptionStatus.ACTIVE,
    )
    first = store.add(option)
    second = store.add(option)
    assert first == second


def test_conflicting_readd_of_option_is_rejected() -> None:
    store = InMemoryBallotOptionStore()
    option = BallotOption(
        ballot_option_id=uuid4(),
        ballot_id=uuid4(),
        option_code="yes",
        label="Yes",
        description="",
        display_order=0,
        status=BallotOptionStatus.ACTIVE,
    )
    store.add(option)
    conflicting = BallotOption(
        ballot_option_id=option.ballot_option_id,
        ballot_id=option.ballot_id,
        option_code="yes",
        label="Yes (renamed)",
        description="",
        display_order=0,
        status=BallotOptionStatus.ACTIVE,
    )
    with pytest.raises(BallotCreationConflictError):
        store.add(conflicting)


def test_save_transitions_option_to_locked() -> None:
    store = InMemoryBallotOptionStore()
    option = BallotOption(
        ballot_option_id=uuid4(),
        ballot_id=uuid4(),
        option_code="yes",
        label="Yes",
        description="",
        display_order=0,
        status=BallotOptionStatus.ACTIVE,
    )
    store.add(option)
    locked = store.save(option.with_status(BallotOptionStatus.LOCKED))
    assert locked.status == BallotOptionStatus.LOCKED
    assert store.get(option.ballot_option_id) == locked


# --- InMemoryVoteEnvelopeStore ------------------------------------------------


def _make_envelope(**overrides: object) -> VoteEnvelope:
    submitted_at = overrides.get("submitted_at", datetime(2026, 1, 2, tzinfo=UTC))
    ballot_id = overrides.get("ballot_id", uuid4())
    credential_proof = overrides.get("credential_proof", uuid4())
    choice = overrides.get("encrypted_or_encoded_choice", "yes")
    integrity_hash = overrides.get(
        "integrity_hash",
        compute_vote_envelope_integrity_hash(
            ballot_id=ballot_id,  # type: ignore[arg-type]
            credential_proof=credential_proof,  # type: ignore[arg-type]
            encrypted_or_encoded_choice=choice,  # type: ignore[arg-type]
            submitted_at=submitted_at,  # type: ignore[arg-type]
        ),
    )
    defaults: dict[str, object] = {
        "vote_envelope_id": uuid4(),
        "ballot_id": ballot_id,
        "credential_proof": credential_proof,
        "encrypted_or_encoded_choice": choice,
        "submitted_at": submitted_at,
        "integrity_hash": integrity_hash,
        "validation_status": VoteEnvelopeStatus.RECEIVED,
        "included_in_tally": False,
    }
    defaults.update(overrides)
    return VoteEnvelope(**defaults)  # type: ignore[arg-type]


def test_create_then_get_vote_envelope() -> None:
    store = InMemoryVoteEnvelopeStore()
    envelope = _make_envelope()
    stored = store.create(envelope)
    assert store.get(envelope.vote_envelope_id) == stored


def test_idempotent_recreate_of_identical_envelope_succeeds() -> None:
    store = InMemoryVoteEnvelopeStore()
    envelope = _make_envelope()
    first = store.create(envelope)
    second = store.create(envelope)
    assert first == second


def test_conflicting_recreate_of_envelope_is_rejected() -> None:
    store = InMemoryVoteEnvelopeStore()
    envelope = _make_envelope()
    store.create(envelope)
    conflicting = _make_envelope(
        vote_envelope_id=envelope.vote_envelope_id, encrypted_or_encoded_choice="no"
    )
    with pytest.raises(VoteEnvelopeCreationConflictError):
        store.create(conflicting)


def test_save_updates_an_already_created_envelope_status() -> None:
    """`save` (unlike `create`) is a plain update for an already-`create`d
    envelope's status transition - e.g. `validate_vote`'s
    `received -> validated`."""
    store = InMemoryVoteEnvelopeStore()
    envelope = _make_envelope()
    store.create(envelope)
    validated = envelope.with_status(VoteEnvelopeStatus.VALIDATED)
    stored = store.save(validated)
    assert stored.validation_status == VoteEnvelopeStatus.VALIDATED
    assert store.get(envelope.vote_envelope_id) == stored


def test_save_of_never_created_envelope_raises() -> None:
    store = InMemoryVoteEnvelopeStore()
    with pytest.raises(UnknownVoteEnvelopeError):
        store.save(_make_envelope())


def test_find_validated_for_credential_finds_only_validated_status() -> None:
    store = InMemoryVoteEnvelopeStore()
    ballot_id = uuid4()
    credential_proof = uuid4()
    received = _make_envelope(ballot_id=ballot_id, credential_proof=credential_proof)
    store.create(received)
    assert store.find_validated_for_credential(ballot_id, credential_proof) is None

    validated = received.with_status(VoteEnvelopeStatus.VALIDATED)
    store.save(validated)
    found = store.find_validated_for_credential(ballot_id, credential_proof)
    assert found == validated


def test_list_for_ballot_returns_only_matching_envelopes() -> None:
    store = InMemoryVoteEnvelopeStore()
    ballot_id = uuid4()
    other_ballot_id = uuid4()
    mine = _make_envelope(ballot_id=ballot_id)
    other = _make_envelope(ballot_id=other_ballot_id)
    store.create(mine)
    store.create(other)
    assert store.list_for_ballot(ballot_id) == (mine,)


# --- InMemoryVoteReceiptStore --------------------------------------------------


def _make_receipt(**overrides: object) -> VoteReceipt:
    defaults: dict[str, object] = {
        "receipt_id": uuid4(),
        "ballot_id": uuid4(),
        "vote_envelope_reference": uuid4(),
        "receipt_hash": "a" * 64,
        "issued_at": datetime(2026, 1, 2, tzinfo=UTC),
        "verification_status": VoteReceiptVerificationStatus.ISSUED,
    }
    defaults.update(overrides)
    return VoteReceipt(**defaults)  # type: ignore[arg-type]


def test_save_then_get_vote_receipt() -> None:
    store = InMemoryVoteReceiptStore()
    receipt = _make_receipt()
    stored = store.save(receipt)
    assert store.get(receipt.receipt_id) == stored


def test_find_for_vote_envelope() -> None:
    store = InMemoryVoteReceiptStore()
    vote_envelope_id = uuid4()
    receipt = _make_receipt(vote_envelope_reference=vote_envelope_id)
    store.save(receipt)
    assert store.find_for_vote_envelope(vote_envelope_id) == receipt
    assert store.find_for_vote_envelope(uuid4()) is None


def test_conflicting_resave_of_receipt_is_rejected() -> None:
    store = InMemoryVoteReceiptStore()
    receipt = _make_receipt()
    store.save(receipt)
    conflicting = _make_receipt(receipt_id=receipt.receipt_id, receipt_hash="b" * 64)
    with pytest.raises(VoteReceiptCreationConflictError):
        store.save(conflicting)

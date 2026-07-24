"""Tests for epd2_voting_service.application.

Exercises the full command set against real PACK-02 collaborators
(`epd2_credential_service`, `epd2_eligibility_service`) through their
`application`-layer functions only (ADR-008) - never their `storage`/
`domain` modules - the same boundary `application.py` itself respects.
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
    evaluate_eligibility,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_voting_service.application import (
    PermissionDeniedError,
    add_ballot_option,
    approve_ballot_configuration,
    cancel_ballot,
    cast_vote,
    close_ballot,
    create_ballot,
    get_ballot,
    invalidate_ballot,
    issue_vote_receipt,
    open_ballot,
    pause_ballot,
    resume_ballot,
    submit_ballot_for_configuration_review,
    validate_vote,
)
from epd2_voting_service.domain import (
    BallotMethod,
    BallotOptionStatus,
    BallotStatus,
    VoteEnvelopeStatus,
    VoteReceiptVerificationStatus,
)
from epd2_voting_service.exceptions import (
    BallotAlreadyClosedError,
    BallotConfigurationLockedError,
    BallotInvalidationNotAuthorizedError,
    BallotNotOpenError,
    DuplicateVoteError,
    UnknownEligibilitySnapshotReferenceError,
    VoteEnvelopeNotReceiptEligibleError,
)
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
    InMemoryVoteReceiptStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)
_OPENS_AT = datetime(2026, 1, 1, tzinfo=UTC)
_CLOSES_AT = datetime(2026, 1, 8, tzinfo=UTC)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


class _Fixture:
    """One fully-wired set of in-memory stores for one test."""

    def __init__(self) -> None:
        self.ballot_store = InMemoryBallotStore()
        self.option_store = InMemoryBallotOptionStore()
        self.envelope_store = InMemoryVoteEnvelopeStore()
        self.receipt_store = InMemoryVoteReceiptStore()
        self.audit_store = InMemoryAuditEventStore()
        self.credential_store = InMemoryCredentialStore()
        self.rule_store = InMemoryEligibilityRuleStore()
        self.decision_store = InMemoryEligibilityDecisionStore()
        self.snapshot_store = InMemoryEligibilitySnapshotStore()
        # A second audit store instance shared with eligibility/credential
        # setup calls, kept separate from `self.audit_store` is
        # unnecessary here - PACK-02 setup reuses `self.audit_store` too.


def _make_eligibility_snapshot(fx: _Fixture, *, rule_version: int = 1) -> UUID:
    """Build one real, evaluated `EligibilitySnapshot` via PACK-02's own
    application layer, so `submit_ballot_for_configuration_review` has
    something genuine to freeze against."""
    actor = _actor()
    rule = create_eligibility_rule(
        fx.rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=rule_version,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=_OPENS_AT,
        valid_until=None,
    )
    decision = evaluate_eligibility(
        fx.rule_store,
        fx.decision_store,
        fx.audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=rule_version,
        subject_reference=uuid4(),
        process_id=uuid4(),
        evaluated_claims={"membership_status": "active", "verification_level": "basic"},
        evaluator_version="1.0",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    ).decision
    snapshot_result = create_eligibility_snapshot(
        fx.snapshot_store,
        fx.audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=rule_version,
        eligible_decisions=[decision],
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=_CLOCK,
    )
    return snapshot_result.snapshot.eligibility_snapshot_id


def _issue_ballot_access_credential(
    fx: _Fixture, *, ballot_id: UUID, rule_version: int, digest: str
) -> UUID:
    credential_id = uuid4()
    issue_participation_credential(
        fx.credential_store,
        fx.audit_store,
        credential_id=credential_id,
        credential_type=CredentialType.BALLOT_ACCESS,
        scope_type="ballot",
        scope_id=ballot_id,
        valid_from=_OPENS_AT,
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=rule_version,
        eligibility_snapshot_digest=digest,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return credential_id


def _create_draft_ballot(fx: _Fixture, creator: ActorRef, **overrides: object) -> UUID:
    ballot_id = uuid4()
    kwargs: dict[str, object] = {
        "ballot_id": ballot_id,
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
        "challenge_window_hours": None,
    }
    kwargs.update(overrides)
    create_ballot(
        fx.ballot_store,
        fx.audit_store,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        **kwargs,  # type: ignore[arg-type]
    )
    return ballot_id


def _fully_scheduled_ballot(fx: _Fixture) -> tuple[UUID, ActorRef, ActorRef, str]:
    """A ballot taken all the way through `scheduled`, with its
    `BallotOption` rows added while still `draft`. Returns
    `(ballot_id, creator, approver, snapshot_digest)`."""
    creator = _actor()
    approver = _actor()
    ballot_id = _create_draft_ballot(fx, creator)

    add_ballot_option(
        fx.ballot_store,
        fx.option_store,
        ballot_id=ballot_id,
        ballot_option_id=uuid4(),
        option_code="yes",
        label="Yes",
        description="",
        display_order=0,
        actor_is_authorized=True,
    )
    add_ballot_option(
        fx.ballot_store,
        fx.option_store,
        ballot_id=ballot_id,
        ballot_option_id=uuid4(),
        option_code="no",
        label="No",
        description="",
        display_order=1,
        actor_is_authorized=True,
    )

    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    approve_ballot_configuration(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=approver,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    digest = fx.ballot_store.frozen_eligibility_snapshot_digest_for(ballot_id)
    assert digest is not None
    return ballot_id, creator, approver, digest


def _opened_ballot(fx: _Fixture) -> tuple[UUID, str]:
    ballot_id, _creator, approver, digest = _fully_scheduled_ballot(fx)
    open_ballot(
        fx.ballot_store,
        fx.option_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=approver,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return ballot_id, digest


# --- create_ballot ------------------------------------------------------------


def test_create_ballot_creates_draft_and_audits() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    result = create_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Should we adopt this proposal?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="simple_majority",
        threshold_rule="simple_majority",
        opens_at=_OPENS_AT,
        closes_at=_CLOSES_AT,
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.ballot.status == BallotStatus.DRAFT
    assert result.event is not None
    assert result.event.event_type == "ballot.created"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None


def test_create_ballot_without_permission_is_denied() -> None:
    fx = _Fixture()
    with pytest.raises(PermissionDeniedError):
        create_ballot(
            fx.ballot_store,
            fx.audit_store,
            ballot_id=uuid4(),
            space_id=uuid4(),
            subject_type="initiative",
            subject_id=uuid4(),
            question="?",
            ballot_method=BallotMethod.YES_NO,
            secrecy_mode="secret",
            eligibility_rule_version=1,
            delegation_policy_version=1,
            quorum_rule="simple_majority",
            threshold_rule="simple_majority",
            opens_at=_OPENS_AT,
            closes_at=_CLOSES_AT,
            challenge_window_hours=None,
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_create_ballot_is_idempotent_for_same_event_id_and_content() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    event_id = uuid4()
    correlation_id = uuid4()
    kwargs: dict[str, object] = {
        "ballot_id": ballot_id,
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
        "challenge_window_hours": None,
    }
    first = create_ballot(
        fx.ballot_store,
        fx.audit_store,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
        **kwargs,  # type: ignore[arg-type]
    )
    second = create_ballot(
        fx.ballot_store,
        fx.audit_store,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first.ballot == second.ballot
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


# --- submit_ballot_for_configuration_review / rule freeze --------------------


def test_submit_ballot_for_configuration_review_freezes_against_real_snapshot() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)

    result = submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.ballot.status == BallotStatus.CONFIGURATION_REVIEW
    assert result.ballot.configuration_hash is not None
    assert result.event is None  # canon names no event for this sub-step
    digest = fx.ballot_store.frozen_eligibility_snapshot_digest_for(ballot_id)
    assert digest is not None and len(digest) == 64


def test_submit_ballot_for_configuration_review_rejects_unknown_snapshot() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    with pytest.raises(UnknownEligibilitySnapshotReferenceError):
        submit_ballot_for_configuration_review(
            fx.ballot_store,
            fx.audit_store,
            fx.snapshot_store,
            ballot_id=ballot_id,
            eligibility_snapshot_id=uuid4(),
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_submit_ballot_for_configuration_review_rejects_rule_version_mismatch() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator, eligibility_rule_version=2)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    with pytest.raises(ValueError, match="rule_version"):
        submit_ballot_for_configuration_review(
            fx.ballot_store,
            fx.audit_store,
            fx.snapshot_store,
            ballot_id=ballot_id,
            eligibility_snapshot_id=snapshot_id,
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_configuration_mutation_after_configuration_review_is_rejected() -> None:
    """CT-00-10: explicit end-to-end proof that a configuration-field
    mutation attempt after `configuration_review` is rejected."""
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    locked_ballot = fx.ballot_store.get(ballot_id)
    assert locked_ballot is not None
    mutated = replace(locked_ballot, quorum_rule="unanimous")
    with pytest.raises(BallotConfigurationLockedError):
        fx.ballot_store.save(mutated)


# --- approve_ballot_configuration (second-actor check, ADR-009 item 7) -------


def test_approve_ballot_configuration_by_different_actor_succeeds() -> None:
    fx = _Fixture()
    ballot_id, creator, approver, _digest = _fully_scheduled_ballot(fx)
    ballot = fx.ballot_store.get(ballot_id)
    assert ballot is not None
    assert ballot.status == BallotStatus.SCHEDULED
    assert creator.actor_id != approver.actor_id


def test_approve_ballot_configuration_emits_both_locked_and_scheduled_events() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    approver = _actor()
    result = approve_ballot_configuration(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=approver,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.configuration_locked_event.event_type == "ballot.configuration_locked"
    assert result.scheduled_event.event_type == "ballot.scheduled"
    assert result.ballot.status == BallotStatus.SCHEDULED
    assert (
        fx.audit_store.get_by_event_id(result.configuration_locked_audit_event.audit_event_id)
        is not None
    )
    assert fx.audit_store.get_by_event_id(result.scheduled_audit_event.audit_event_id) is not None


def test_approve_ballot_configuration_by_same_actor_as_creator_is_denied() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(PermissionDeniedError):
        approve_ballot_configuration(
            fx.ballot_store,
            fx.audit_store,
            ballot_id=ballot_id,
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- add_ballot_option / freeze --------------------------------------------


def test_add_ballot_option_after_freeze_is_rejected() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    snapshot_id = _make_eligibility_snapshot(fx, rule_version=1)
    submit_ballot_for_configuration_review(
        fx.ballot_store,
        fx.audit_store,
        fx.snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(BallotConfigurationLockedError):
        add_ballot_option(
            fx.ballot_store,
            fx.option_store,
            ballot_id=ballot_id,
            ballot_option_id=uuid4(),
            option_code="yes",
            label="Yes",
            description="",
            display_order=0,
            actor_is_authorized=True,
        )


def test_add_ballot_option_abstain_is_ordinary_row() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    option = add_ballot_option(
        fx.ballot_store,
        fx.option_store,
        ballot_id=ballot_id,
        ballot_option_id=uuid4(),
        option_code="abstain",
        label="Abstain",
        description="",
        display_order=2,
        actor_is_authorized=True,
    )
    assert option.option_code == "abstain"


# --- open_ballot / pause / resume --------------------------------------------


def test_open_ballot_locks_all_options() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    assert digest
    ballot = fx.ballot_store.get(ballot_id)
    assert ballot is not None
    assert ballot.status == BallotStatus.OPEN
    options = fx.option_store.list_for_ballot(ballot_id)
    assert len(options) == 2
    assert all(o.status == BallotOptionStatus.LOCKED for o in options)


def test_pause_and_resume_ballot() -> None:
    fx = _Fixture()
    ballot_id, _digest = _opened_ballot(fx)
    actor = _actor()
    paused = pause_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert paused.ballot.status == BallotStatus.PAUSED
    resumed = resume_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert resumed.ballot.status == BallotStatus.OPEN


# --- cast_vote ----------------------------------------------------------------


def test_cast_vote_creates_received_envelope_and_audits() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    result = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.envelope.validation_status == VoteEnvelopeStatus.RECEIVED
    assert result.event.event_type == "vote.received"
    assert fx.audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None
    assert result.superseded_envelope is None


def test_cast_vote_rejects_when_ballot_not_open() -> None:
    fx = _Fixture()
    ballot_id, _creator, _approver, digest = _fully_scheduled_ballot(fx)  # still `scheduled`
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    with pytest.raises(BallotNotOpenError):
        cast_vote(
            fx.ballot_store,
            fx.envelope_store,
            fx.audit_store,
            fx.credential_store,
            vote_envelope_id=uuid4(),
            ballot_id=ballot_id,
            credential_proof=credential_id,
            encrypted_or_encoded_choice="yes",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_cast_vote_rejects_invalid_credential() -> None:
    fx = _Fixture()
    ballot_id, _digest = _opened_ballot(fx)
    # A credential never issued at all - definitely invalid.
    with pytest.raises(PermissionDeniedError):
        cast_vote(
            fx.ballot_store,
            fx.envelope_store,
            fx.audit_store,
            fx.credential_store,
            vote_envelope_id=uuid4(),
            ballot_id=ballot_id,
            credential_proof=uuid4(),
            encrypted_or_encoded_choice="yes",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_cast_vote_supersedes_previous_validated_vote() -> None:
    """ADR-009 items 1-2: a participant may change their vote before
    close; only the newest `validated` envelope counts."""
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()

    first_id = uuid4()
    first = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=first_id,
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=first.envelope.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )

    second_id = uuid4()
    second = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=second_id,
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="no",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert second.superseded_envelope is not None
    assert second.superseded_envelope.vote_envelope_id == first_id
    assert second.superseded_envelope.validation_status == VoteEnvelopeStatus.SUPERSEDED
    assert second.superseded_event is not None
    assert second.superseded_event.event_type == "vote.superseded"
    assert second.superseded_audit_event is not None

    stored_first = fx.envelope_store.get(first_id)
    assert stored_first is not None
    assert stored_first.validation_status == VoteEnvelopeStatus.SUPERSEDED


def test_cast_vote_after_close_with_no_prior_vote_raises_ballot_already_closed() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    late_clock = FixedClock(_CLOSES_AT + timedelta(hours=1))
    with pytest.raises(BallotAlreadyClosedError):
        cast_vote(
            fx.ballot_store,
            fx.envelope_store,
            fx.audit_store,
            fx.credential_store,
            vote_envelope_id=uuid4(),
            ballot_id=ballot_id,
            credential_proof=credential_id,
            encrypted_or_encoded_choice="yes",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=late_clock,
        )


def test_cast_vote_after_close_with_prior_validated_vote_raises_duplicate_vote() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    first = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=first.envelope.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    late_clock = FixedClock(_CLOSES_AT + timedelta(hours=1))
    with pytest.raises(DuplicateVoteError):
        cast_vote(
            fx.ballot_store,
            fx.envelope_store,
            fx.audit_store,
            fx.credential_store,
            vote_envelope_id=uuid4(),
            ballot_id=ballot_id,
            credential_proof=credential_id,
            encrypted_or_encoded_choice="no",
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=late_clock,
        )


def test_cast_vote_is_idempotent_for_same_event_id_and_inputs() -> None:
    """CT-00-04's highest-stakes case: a duplicate vote-submission
    delivery (same `event_id`, same `vote_envelope_id`, same inputs,
    same `FixedClock`) must be a no-op - no double supersession, no
    duplicate audit entry."""
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    correlation_id = uuid4()

    first_id = uuid4()
    cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=first_id,
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
    )
    validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=first_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
    )

    event_id = uuid4()
    second_id = uuid4()
    a = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=second_id,
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="no",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    b = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=second_id,
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="no",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=correlation_id,
        clock=_CLOCK,
        event_id=event_id,
    )
    assert a.envelope == b.envelope
    assert a.audit_event.audit_event_id == b.audit_event.audit_event_id
    # The first envelope was superseded exactly once - a replay of the
    # second cast_vote call must not raise, and must not re-supersede or
    # double-audit it.
    assert b.superseded_envelope is None  # already superseded by call `a`
    stored_first = fx.envelope_store.get(first_id)
    assert stored_first is not None
    assert stored_first.validation_status == VoteEnvelopeStatus.SUPERSEDED


# --- validate_vote --------------------------------------------------------------


def test_validate_vote_marks_valid_envelope_validated() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    cast = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=cast.envelope.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.envelope.validation_status == VoteEnvelopeStatus.VALIDATED
    assert result.event.event_type == "vote.validated"
    assert result.audit_event.reason_code == "VOTE_VALIDATED"


def test_validate_vote_rejects_tampered_integrity_hash() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    cast = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    # Simulate tampering: overwrite the stored envelope's integrity_hash
    # directly (bypassing cast_vote's own honest computation).
    tampered = replace(cast.envelope, integrity_hash="0" * 64)
    fx.envelope_store._envelopes[tampered.vote_envelope_id] = tampered

    result = validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=tampered.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.envelope.validation_status == VoteEnvelopeStatus.REJECTED
    assert result.event.event_type == "vote.rejected"
    assert result.audit_event.reason_code == "VOTE_REJECTED"


# --- close_ballot / cancel_ballot --------------------------------------------


def test_close_ballot() -> None:
    fx = _Fixture()
    ballot_id, _digest = _opened_ballot(fx)
    result = close_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.ballot.status == BallotStatus.CLOSED
    assert result.event is not None
    assert result.event.event_type == "ballot.closed"


def test_cancel_ballot_from_draft() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = _create_draft_ballot(fx, creator)
    result = cancel_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.ballot.status == BallotStatus.CANCELLED
    assert result.event is not None
    assert result.event.event_type == "ballot.cancelled"


# --- issue_vote_receipt --------------------------------------------------------


def test_issue_vote_receipt_after_validation() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    cast = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    validate_vote(
        fx.envelope_store,
        fx.audit_store,
        vote_envelope_id=cast.envelope.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = issue_vote_receipt(
        fx.envelope_store,
        fx.receipt_store,
        fx.audit_store,
        receipt_id=uuid4(),
        vote_envelope_id=cast.envelope.vote_envelope_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.receipt.verification_status == VoteReceiptVerificationStatus.ISSUED
    assert result.receipt.receipt_hash
    assert result.audit_event.reason_code == "RECEIPT_ISSUED"


def test_issue_vote_receipt_rejects_non_eligible_envelope() -> None:
    fx = _Fixture()
    ballot_id, digest = _opened_ballot(fx)
    credential_id = _issue_ballot_access_credential(
        fx, ballot_id=ballot_id, rule_version=1, digest=digest
    )
    actor = _actor()
    cast = cast_vote(
        fx.ballot_store,
        fx.envelope_store,
        fx.audit_store,
        fx.credential_store,
        vote_envelope_id=uuid4(),
        ballot_id=ballot_id,
        credential_proof=credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    # Still `received`, never validated - not receipt-eligible.
    with pytest.raises(VoteEnvelopeNotReceiptEligibleError):
        issue_vote_receipt(
            fx.envelope_store,
            fx.receipt_store,
            fx.audit_store,
            receipt_id=uuid4(),
            vote_envelope_id=cast.envelope.vote_envelope_id,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


# --- PACK-05 (ADR-017 Option B): invalidate_ballot ---------------------------


def _create_test_ballot(fx: _Fixture, *, ballot_id: UUID, creator: ActorRef) -> None:
    create_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Should we adopt this proposal?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="simple_majority",
        threshold_rule="simple_majority",
        opens_at=_OPENS_AT,
        closes_at=_CLOSES_AT,
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )


class _FakeApprovedBallotInvalidationDecision:
    """A minimal stand-in for a `governance-service`
    `GovernanceDecision`, used only to exercise `invalidate_ballot`'s own
    logic in isolation from a real `epd2_governance_service` store -
    this module intentionally has no import of
    `epd2_governance_service.storage`/`.domain` (ADR-017), so its own
    tests construct the smallest duck-typed object `invalidate_ballot`
    actually reads from (`decision_type.value`,
    `subject_reference.get(...)`, `.governance_decision_id`, `.status`).
    """

    def __init__(self, *, ballot_id: UUID, decision_type: str = "ballot_invalidation") -> None:
        self.governance_decision_id = uuid4()
        self.decision_type = _FakeDecisionType(decision_type)
        self.subject_reference = {"ballot_id": str(ballot_id)}
        self.status = _FakeDecisionStatus("approved")


class _FakeDecisionType:
    def __init__(self, value: str) -> None:
        self.value = value


class _FakeDecisionStatus:
    def __init__(self, value: str) -> None:
        self.value = value


class _FakeGovernanceDecisionStore:
    """Duck-typed stand-in for governance-service's own store, wired
    directly to `epd2_governance_service.application.get_governance_decision`
    /`is_current_approved_decision`'s expected `.get`/`.find_superseding`
    surface."""

    def __init__(self, decision: _FakeApprovedBallotInvalidationDecision | None) -> None:
        self._decision = decision
        self._superseded = False

    def get(self, governance_decision_id: UUID) -> object | None:
        if (
            self._decision is not None
            and self._decision.governance_decision_id == governance_decision_id
        ):
            return self._decision
        return None

    def find_superseding(self, governance_decision_id: UUID) -> object | None:
        return object() if self._superseded else None


def test_invalidate_ballot_succeeds_with_approved_scoped_decision() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    _create_test_ballot(fx, ballot_id=ballot_id, creator=creator)

    decision = _FakeApprovedBallotInvalidationDecision(ballot_id=ballot_id)
    governance_decision_store = _FakeGovernanceDecisionStore(decision)

    result = invalidate_ballot(
        fx.ballot_store,
        governance_decision_store,
        fx.audit_store,
        ballot_id=ballot_id,
        governance_decision_id=decision.governance_decision_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.ballot.status is BallotStatus.INVALIDATED
    assert result.event is not None
    assert result.event.event_type == "ballot.invalidated"


def test_invalidate_ballot_rejects_wrong_ballot_scope() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    _create_test_ballot(fx, ballot_id=ballot_id, creator=creator)

    decision = _FakeApprovedBallotInvalidationDecision(ballot_id=uuid4())  # different ballot
    governance_decision_store = _FakeGovernanceDecisionStore(decision)

    with pytest.raises(BallotInvalidationNotAuthorizedError):
        invalidate_ballot(
            fx.ballot_store,
            governance_decision_store,
            fx.audit_store,
            ballot_id=ballot_id,
            governance_decision_id=decision.governance_decision_id,
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_invalidate_ballot_rejects_wrong_decision_type() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    _create_test_ballot(fx, ballot_id=ballot_id, creator=creator)

    decision = _FakeApprovedBallotInvalidationDecision(ballot_id=ballot_id, decision_type="mandate")
    governance_decision_store = _FakeGovernanceDecisionStore(decision)

    with pytest.raises(BallotInvalidationNotAuthorizedError):
        invalidate_ballot(
            fx.ballot_store,
            governance_decision_store,
            fx.audit_store,
            ballot_id=ballot_id,
            governance_decision_id=decision.governance_decision_id,
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_invalidate_ballot_rejects_unknown_decision_id() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    _create_test_ballot(fx, ballot_id=ballot_id, creator=creator)

    governance_decision_store = _FakeGovernanceDecisionStore(None)

    with pytest.raises(BallotInvalidationNotAuthorizedError):
        invalidate_ballot(
            fx.ballot_store,
            governance_decision_store,
            fx.audit_store,
            ballot_id=ballot_id,
            governance_decision_id=uuid4(),
            actor=creator,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_invalidate_ballot_without_permission_is_denied() -> None:
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    _create_test_ballot(fx, ballot_id=ballot_id, creator=creator)
    decision = _FakeApprovedBallotInvalidationDecision(ballot_id=ballot_id)
    governance_decision_store = _FakeGovernanceDecisionStore(decision)

    with pytest.raises(PermissionDeniedError):
        invalidate_ballot(
            fx.ballot_store,
            governance_decision_store,
            fx.audit_store,
            ballot_id=ballot_id,
            governance_decision_id=decision.governance_decision_id,
            actor=creator,
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_application_module_path_exists() -> None:
    import epd2_voting_service

    package_dir = Path(inspect.getfile(epd2_voting_service)).parent
    assert (package_dir / "application.py").exists()


def test_get_ballot_read_accessor() -> None:
    """Additive (PACK-04, ADR-012 item 3): backs
    `epd2_transparency_service.application.publish_ledger_entry` for
    `subject_type = "result_publication"` (ballot context)."""
    fx = _Fixture()
    creator = _actor()
    ballot_id = uuid4()
    create_ballot(
        fx.ballot_store,
        fx.audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Should we adopt this proposal?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="simple_majority",
        threshold_rule="simple_majority",
        opens_at=_OPENS_AT,
        closes_at=_CLOSES_AT,
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    found = get_ballot(fx.ballot_store, ballot_id=ballot_id)
    assert found is not None
    assert found.ballot_id == ballot_id
    assert get_ballot(fx.ballot_store, ballot_id=uuid4()) is None

"""CT-00-04 Event Idempotency (canon section 27): a repeat of the same
`event_id` does not create a second action. Exercised here at the
Audit Core boundary (the durable record every service's critical action
appends to) using a real service call, not a synthetic AuditEvent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_audit_core.exceptions import AuditEventConflictError
from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_credential_service.application import issue_participation_credential
from epd2_credential_service.domain import CredentialType
from epd2_credential_service.storage import InMemoryCredentialStore
from epd2_delegation_service.application import create_delegation
from epd2_delegation_service.storage import InMemoryDelegationStore
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
)
from epd2_eligibility_service.storage import (
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_voting_service.application import (
    approve_ballot_configuration,
    cast_vote,
    create_ballot,
    open_ballot,
    submit_ballot_for_configuration_review,
)
from epd2_voting_service.domain import BallotMethod
from epd2_voting_service.storage import (
    InMemoryBallotOptionStore,
    InMemoryBallotStore,
    InMemoryVoteEnvelopeStore,
)


def test_repeated_credential_issuance_with_same_event_id_is_idempotent(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same issuance command (same
    `credential_id`, same content, same caller-supplied `event_id` -
    e.g. after a network timeout on the first attempt's response) must
    not create a second stored credential or a second audit entry."""
    credential_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        credential_id=credential_id,
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )

    assert first.credential == second.credential
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    # Only one AuditEvent exists for this credential's issuance - the
    # repeat did not append a second entry to the chain.
    entries = audit_store.list_by_aggregate("participation_credential", credential_id)
    assert len(entries) == 1
    assert entries[0].audit_event_id == first.audit_event.audit_event_id


def test_repeated_credential_issuance_without_shared_event_id_still_dedupes_storage(
    credential_store: InMemoryCredentialStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Without a caller-supplied `event_id` (the default), the *stored*
    credential still dedupes correctly by `credential_id` + content (the
    service's own idempotency key, distinct from CT-00-04's event-level
    guarantee) - but each call mints its own domain event and audit entry.
    This is a documented, narrower guarantee than the shared-event_id case
    above; see docs/review/OPEN_QUESTIONS.md."""
    credential_id = uuid4()
    kwargs = dict(
        credential_id=credential_id,
        credential_type=CredentialType.SPACE_ACCESS,
        scope_type="civic_space",
        scope_id=uuid4(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        expires_at=datetime(2027, 1, 1, tzinfo=UTC),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest="a" * 64,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    first = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = issue_participation_credential(
        credential_store,
        audit_store,
        **kwargs,  # type: ignore[arg-type]
    )

    assert first.credential == second.credential
    assert first.audit_event.audit_event_id != second.audit_event.audit_event_id


def test_repeated_event_id_with_different_content_is_a_conflict(
    audit_store: InMemoryAuditEventStore, actor: ActorRef, clock: FixedClock
) -> None:
    """A direct Audit Core replay with the same `audit_event_id` but
    different content must fail-closed, never silently overwrite."""
    from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event

    shared_id = uuid4()
    base = dict(
        audit_event_id=shared_id,
        occurred_at=clock.now(),
        actor_id=actor.actor_id,
        actor_type=actor.actor_type,
        target_type="participation_credential",
        target_id=uuid4(),
        action="issue",
        reason_code="CREDENTIAL_ISSUED",
        policy_version="1.0",
        correlation_id=uuid4(),
        source_service="credential-service",
    )
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(event_type="credential.issued", **base),  # type: ignore[arg-type]
        clock=clock,
    )
    with pytest.raises(AuditEventConflictError):
        append_audit_event(
            audit_store,
            # Same audit_event_id, different event_type -> different content.
            AppendAuditEventRequest(
                event_type="credential.revoked",
                **base,  # type: ignore[arg-type]
            ),
            clock=clock,
        )


# =============================================================================
# PACK-03: `cast_vote` (voting-service) - canon's own flagship idempotency
# case per the pack spec - and `create_delegation` (delegation-service).
# =============================================================================


def test_repeated_cast_vote_with_same_event_id_is_idempotent(
    ballot_store: InMemoryBallotStore,
    ballot_option_store: InMemoryBallotOptionStore,
    vote_envelope_store: InMemoryVoteEnvelopeStore,
    audit_store: InMemoryAuditEventStore,
    credential_store: InMemoryCredentialStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same `cast_vote` command (same
    `vote_envelope_id`, same content, same caller-supplied `event_id`)
    must not create a second stored `VoteEnvelope` or a second audit
    entry - canon's own flagship CT-00-04 case for this pack."""
    rule = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=uuid4(),
        rule_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=clock.now(),
        valid_until=None,
    )
    snapshot = create_eligibility_snapshot(
        eligibility_snapshot_store,
        audit_store,
        eligibility_rule_id=rule.eligibility_rule_id,
        rule_version=1,
        eligible_decisions=(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        causation_id=None,
        clock=clock,
    ).snapshot

    ballot_id = uuid4()
    credential = issue_participation_credential(
        credential_store,
        audit_store,
        credential_id=uuid4(),
        credential_type=CredentialType.BALLOT_ACCESS,
        scope_type="ballot",
        scope_id=ballot_id,
        valid_from=clock.now(),
        expires_at=clock.now() + timedelta(days=365),
        usage_limit=None,
        rule_version=1,
        eligibility_snapshot_digest=snapshot.digest,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).credential

    creator = ActorRef(actor_id=uuid4(), actor_type="service")
    create_ballot(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        space_id=uuid4(),
        subject_type="initiative",
        subject_id=uuid4(),
        question="Shall this pass?",
        ballot_method=BallotMethod.YES_NO,
        secrecy_mode="secret",
        eligibility_rule_version=1,
        delegation_policy_version=1,
        quorum_rule="none",
        threshold_rule="simple_majority",
        opens_at=clock.now(),
        closes_at=clock.now() + timedelta(days=1),
        challenge_window_hours=None,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    submit_ballot_for_configuration_review(
        ballot_store,
        audit_store,
        eligibility_snapshot_store,
        ballot_id=ballot_id,
        eligibility_snapshot_id=snapshot.eligibility_snapshot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    approve_ballot_configuration(
        ballot_store,
        audit_store,
        ballot_id=ballot_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    open_ballot(
        ballot_store,
        ballot_option_store,
        audit_store,
        ballot_id=ballot_id,
        actor=creator,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    vote_envelope_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        vote_envelope_id=vote_envelope_id,
        ballot_id=ballot_id,
        credential_proof=credential.credential_id,
        encrypted_or_encoded_choice="yes",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = cast_vote(
        ballot_store,
        vote_envelope_store,
        audit_store,
        credential_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = cast_vote(
        ballot_store,
        vote_envelope_store,
        audit_store,
        credential_store,
        **kwargs,  # type: ignore[arg-type]
    )

    assert first.envelope == second.envelope
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    entries = audit_store.list_by_aggregate("vote_envelope", vote_envelope_id)
    assert len(entries) == 1
    assert entries[0].audit_event_id == first.audit_event.audit_event_id


def test_repeated_create_delegation_with_same_event_id_is_idempotent(
    delegation_store: InMemoryDelegationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same `create_delegation` command (same
    `delegation_id`, same content, same caller-supplied `event_id`) must
    not create a second stored `Delegation` or a second audit entry."""
    delegation_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        delegation_id=delegation_id,
        delegator_actor_id=uuid4(),
        delegate_actor_id=uuid4(),
        scope_type="ballot",
        scope_id=uuid4(),
        valid_from=clock.now(),
        valid_until=None,
        revocation_status="not_revoked",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = create_delegation(delegation_store, audit_store, **kwargs)  # type: ignore[arg-type]
    second = create_delegation(delegation_store, audit_store, **kwargs)  # type: ignore[arg-type]

    assert first.delegation == second.delegation
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    entries = audit_store.list_by_aggregate("delegation", delegation_id)
    assert len(entries) == 1
    assert entries[0].audit_event_id == first.audit_event.audit_event_id

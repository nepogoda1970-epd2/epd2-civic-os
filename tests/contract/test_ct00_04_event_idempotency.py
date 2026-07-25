"""CT-00-04 Event Idempotency (canon section 27): a repeat of the same
`event_id` does not create a second action. Exercised here at the
Audit Core boundary (the durable record every service's critical action
appends to) using a real service call, not a synthetic AuditEvent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_ai_processing_service.application import request_ai_processing
from epd2_ai_processing_service.storage import InMemoryAIProcessingRecordStore
from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
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
    record_digital_decision,
)
from epd2_eligibility_service.storage import (
    InMemoryAssemblyDecisionStore,
    InMemoryDigitalDecisionStore,
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_governance_service.application import request_role_assignment
from epd2_governance_service.domain import RoleAssignment, RoleAssignmentStatus
from epd2_governance_service.storage import InMemoryRoleAssignmentStore
from epd2_membership_service.application import declare_affiliation, open_conflict_assessment
from epd2_membership_service.storage import (
    InMemoryAffiliationDeclarationStore,
    InMemoryConflictAssessmentStore,
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


# =============================================================================
# PACK-05: `request_role_assignment` (governance-service).
# =============================================================================


def test_repeated_request_role_assignment_with_same_event_id_is_idempotent(
    role_assignment_store: InMemoryRoleAssignmentStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same `request_role_assignment` command
    (same `role_assignment_id`, same content, same caller-supplied
    `event_id`) must not create a second stored `RoleAssignment` or a
    second audit entry."""
    granter = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="governance_policy_approver",
            scope_id=uuid4(),
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    role_assignment_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        role_assignment_id=role_assignment_id,
        actor_id=uuid4(),
        role_code="observer",
        scope_id=uuid4(),
        valid_from=clock.now(),
        valid_until=None,
        granter_role_assignment_id=granter.role_assignment_id,
        approval_reference=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = request_role_assignment(role_assignment_store, audit_store, **kwargs)  # type: ignore[arg-type]
    second = request_role_assignment(role_assignment_store, audit_store, **kwargs)  # type: ignore[arg-type]

    assert first.assignment == second.assignment
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    entries = audit_store.list_by_aggregate("role_assignment", role_assignment_id)
    assert len(entries) == 1


# =============================================================================
# PACK-06: `request_ai_processing` (ai-processing-service).
# =============================================================================


def test_repeated_request_ai_processing_with_same_event_id_is_idempotent(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A caller retrying the exact same `request_ai_processing` command
    (same `ai_processing_record_id`, same content, same caller-supplied
    `event_id`) must not create a second stored `AIProcessingRecord` or a
    second audit entry."""
    record_store = InMemoryAIProcessingRecordStore()
    record_id = uuid4()
    event_id = uuid4()
    kwargs = dict(
        ai_processing_record_id=record_id,
        purpose_code="summarization",
        target_type="initiative",
        target_id=uuid4(),
        input_version="v1",
        model_provider="internal",
        model_name="internal-model",
        model_version="1.0",
        prompt_template_version="v1",
        is_consequential=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
        event_id=event_id,
    )
    first = request_ai_processing(record_store, audit_store, **kwargs)  # type: ignore[arg-type]
    second = request_ai_processing(record_store, audit_store, **kwargs)  # type: ignore[arg-type]

    assert first.record == second.record
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id
    entries = audit_store.list_by_aggregate("ai_processing_record", record_id)
    assert len(entries) == 1


# =============================================================================
# PACK-07: `record_digital_decision` (eligibility-service) and
# `declare_affiliation`/`open_conflict_assessment` (membership-service).
#
# Unlike every command exercised above, none of PACK-07's application
# functions accept a caller-supplied `event_id`/`audit_event_id` - each
# call mints a fresh one via `generate_uuid()` (`epd2_eligibility_service.
# application` / `epd2_membership_service.application`), so calling the
# command itself twice is not the right way to exercise CT-00-04 here (it
# would just produce two independent audit entries, one per call). What
# CT-00-04 actually requires - that *reprocessing the same event envelope*
# never double-appends - is instead exercised directly at the Audit Core
# boundary: build an `AppendAuditEventRequest` that mirrors a real audit
# entry a PACK-07 command already produced (same `audit_event_id`, same
# content - a message-bus redelivery of that exact event) and confirm the
# second `append_audit_event` call returns the existing record rather than
# creating a new one, per `epd2_audit_core.application.append_audit_event`'s
# own idempotency contract (also exercised directly by
# `test_repeated_event_id_with_different_content_is_a_conflict` above).
# =============================================================================


def _replay_request(audit_event: object) -> AppendAuditEventRequest:
    """Build an `AppendAuditEventRequest` that exactly reproduces an
    already-appended `AuditEvent` - i.e. a redelivery of the same event,
    not a new one - for the PACK-07 tests below."""
    return AppendAuditEventRequest(
        audit_event_id=audit_event.audit_event_id,  # type: ignore[attr-defined]
        event_type=audit_event.event_type,  # type: ignore[attr-defined]
        occurred_at=audit_event.occurred_at,  # type: ignore[attr-defined]
        actor_id=audit_event.actor_id,  # type: ignore[attr-defined]
        actor_type=audit_event.actor_type,  # type: ignore[attr-defined]
        target_type=audit_event.target_type,  # type: ignore[attr-defined]
        target_id=audit_event.target_id,  # type: ignore[attr-defined]
        action=audit_event.action,  # type: ignore[attr-defined]
        reason_code=audit_event.reason_code,  # type: ignore[attr-defined]
        policy_version=audit_event.policy_version,  # type: ignore[attr-defined]
        correlation_id=audit_event.correlation_id,  # type: ignore[attr-defined]
        source_service=audit_event.source_service,  # type: ignore[attr-defined]
        before_hash=audit_event.before_hash,  # type: ignore[attr-defined]
        after_hash=audit_event.after_hash,  # type: ignore[attr-defined]
    )


def test_repeated_record_digital_decision_audit_replay_is_idempotent(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """A message-bus redelivery of the exact same `eligibility.
    digital_decision_recorded` audit entry (same `audit_event_id`, same
    content) that `record_digital_decision` (eligibility-service,
    PACK-07) already appended must not create a second audit entry - see
    this section's header note on why the command itself is called only
    once here."""
    digital_decision_id = uuid4()
    first = record_digital_decision(
        InMemoryDigitalDecisionStore(),
        InMemoryAssemblyDecisionStore(),
        audit_store,
        digital_decision_id=digital_decision_id,
        process_reference={"process_id": str(uuid4())},
        digital_result="approved",
        decision_effect="advisory",
        formal_confirmation_required=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    second = append_audit_event(audit_store, _replay_request(first.audit_event), clock=clock)

    assert second == first.audit_event
    entries = audit_store.list_by_aggregate("digital_decision", digital_decision_id)
    assert len(entries) == 1


def test_repeated_declare_affiliation_audit_replay_is_idempotent(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Same guarantee as above, for `declare_affiliation`'s
    `AffiliationDeclared` audit entry (membership-service, PACK-07)."""
    affiliation_declaration_id = uuid4()
    first = declare_affiliation(
        InMemoryAffiliationDeclarationStore(),
        audit_store,
        affiliation_declaration_id=affiliation_declaration_id,
        subject_reference=uuid4(),
        affiliation_type="other_party_membership",
        declared_reference="Other Party e.V.",
        valid_from=clock.now(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    second = append_audit_event(audit_store, _replay_request(first.audit_event), clock=clock)

    assert second == first.audit_event
    entries = audit_store.list_by_aggregate("affiliation_declaration", affiliation_declaration_id)
    assert len(entries) == 1


def test_repeated_open_conflict_assessment_audit_replay_is_idempotent(
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Same guarantee as above, for `open_conflict_assessment`'s
    `ConflictAssessmentOpened` audit entry (membership-service,
    PACK-07)."""
    conflict_assessment_id = uuid4()
    first = open_conflict_assessment(
        InMemoryConflictAssessmentStore(),
        audit_store,
        conflict_assessment_id=conflict_assessment_id,
        subject_reference=uuid4(),
        conflict_type="dual_party_membership",
        reviewed_by_role_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    second = append_audit_event(audit_store, _replay_request(first.audit_event), clock=clock)

    assert second == first.audit_event
    entries = audit_store.list_by_aggregate("conflict_assessment", conflict_assessment_id)
    assert len(entries) == 1

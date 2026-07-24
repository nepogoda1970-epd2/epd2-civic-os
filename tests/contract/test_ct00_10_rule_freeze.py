"""CT-00-10 Rule Freeze (canon section 27): once a `Ballot` opens, its
configuration cannot change.

`Ballot` itself is out of PACK-02's scope (pack section 3.2 - voting is a
future pack). What PACK-02 owns and must freeze the same way is
`EligibilityRule` (canon section 9.1): once a `(eligibility_rule_id,
rule_version)` pair is created, its content is immutable - the same
"freeze after commitment" invariant CT-00-10 tests for `Ballot`, applied
to the one canon entity in this pack's scope that has a freeze
requirement.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_delegation_service.application import (
    activate_delegation,
    create_delegation,
    resolve_delegation_snapshot,
)
from epd2_delegation_service.exceptions import SnapshotFrozenError
from epd2_delegation_service.storage import InMemoryDelegationSnapshotStore, InMemoryDelegationStore
from epd2_eligibility_service.application import (
    create_eligibility_rule,
    create_eligibility_snapshot,
)
from epd2_eligibility_service.exceptions import RuleVersionFrozenError
from epd2_eligibility_service.storage import (
    InMemoryEligibilityRuleStore,
    InMemoryEligibilitySnapshotStore,
)
from epd2_governance_service.application import (
    approve_governance_decision,
    propose_governance_decision,
    reject_governance_decision,
)
from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    GovernanceDecisionType,
    RoleAssignment,
    RoleAssignmentStatus,
)
from epd2_governance_service.exceptions import ForbiddenGovernanceDecisionTransitionError
from epd2_governance_service.storage import (
    InMemoryGovernanceDecisionStore,
    InMemoryRoleAssignmentStore,
    InMemoryTechnicalChallengeStore,
)
from epd2_voting_service.application import create_ballot, submit_ballot_for_configuration_review
from epd2_voting_service.domain import BallotMethod
from epd2_voting_service.exceptions import BallotConfigurationLockedError
from epd2_voting_service.storage import InMemoryBallotStore


def test_identical_resubmission_of_a_rule_version_is_idempotent(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    rule_id = uuid4()
    scope_id = uuid4()
    kwargs = dict(
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=scope_id,
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    first = create_eligibility_rule(
        eligibility_rule_store,
        **kwargs,  # type: ignore[arg-type]
    )
    second = create_eligibility_rule(
        eligibility_rule_store,
        **kwargs,  # type: ignore[arg-type]
    )
    assert first == second


def test_conflicting_resubmission_of_a_rule_version_is_rejected(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    """Once (eligibility_rule_id, rule_version) exists, its content is
    frozen - a later attempt to change it (even a single field) must
    fail-closed, never silently overwrite."""
    rule_id = uuid4()
    create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    with pytest.raises(RuleVersionFrozenError) as excinfo:
        create_eligibility_rule(
            eligibility_rule_store,
            eligibility_rule_id=rule_id,
            rule_version=1,
            scope_type="civic_space",
            scope_id=uuid4(),  # different content -> frozen conflict
            required_membership_status="active",
            required_verification_level="basic",
            region_constraint=None,
            minimum_membership_age=None,
            exclusion_conditions=(),
            valid_from=datetime(2026, 1, 1, tzinfo=UTC),
            valid_until=None,
        )
    assert excinfo.value.reason_code == "ELIGIBILITY_RULE_VERSION_FROZEN"


def test_a_new_rule_version_is_a_separate_unfrozen_entity(
    eligibility_rule_store: InMemoryEligibilityRuleStore,
) -> None:
    """Freezing applies per-version, not per-rule-id - creating rule_version
    2 for the same eligibility_rule_id is a distinct, independently
    freezable entity (this is how a rule change reaches the system at all:
    a new version, never mutating an old one)."""
    rule_id = uuid4()
    v1 = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=1,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="active",
        required_verification_level="basic",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
    )
    v2 = create_eligibility_rule(
        eligibility_rule_store,
        eligibility_rule_id=rule_id,
        rule_version=2,
        scope_type="civic_space",
        scope_id=uuid4(),
        required_membership_status="suspended",
        required_verification_level="enhanced",
        region_constraint=None,
        minimum_membership_age=None,
        exclusion_conditions=(),
        valid_from=datetime(2026, 6, 1, tzinfo=UTC),
        valid_until=None,
    )
    assert v1.rule_version == 1
    assert v2.rule_version == 2
    assert v1 != v2


# =============================================================================
# PACK-03: `Ballot` is now in scope, so CT-00-10 can be exercised directly -
# a real `EligibilitySnapshot`-backed ballot freeze - plus the
# delegation-service analogue (`DelegationSnapshot` freeze by
# `(ballot_id, input_hash)`).
# =============================================================================


def test_ballot_configuration_freeze_against_a_real_eligibility_snapshot(
    ballot_store: InMemoryBallotStore,
    audit_store: InMemoryAuditEventStore,
    eligibility_rule_store: InMemoryEligibilityRuleStore,
    eligibility_snapshot_store: InMemoryEligibilitySnapshotStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Once a ballot leaves `draft` (here, `draft -> configuration_review`
    via `submit_ballot_for_configuration_review`, freezing it against a
    real, application-layer-created `EligibilitySnapshot` - not a
    synthetic one), a later attempt to change a configuration-hash-covered
    field (e.g. `question`) is rejected by `InMemoryBallotStore.save`
    itself, mirroring `InMemoryEligibilityRuleStore.save`'s own
    freeze-by-version precedent above."""
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
        actor=actor,
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
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    stored_ballot = ballot_store.get(ballot_id)
    assert stored_ballot is not None
    # `question` is not itself one of `configuration_fields` - mutate
    # `threshold_rule`, which is, to actually exercise the freeze check.
    mutated = replace(stored_ballot, threshold_rule="two_thirds_majority")
    with pytest.raises(BallotConfigurationLockedError):
        ballot_store.save(mutated)


def test_delegation_snapshot_resubmission_with_different_content_is_frozen(
    delegation_store: InMemoryDelegationStore,
    delegation_snapshot_store: InMemoryDelegationSnapshotStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """CT-00-10's delegation-service analogue (canon prohibition #4): a
    `DelegationSnapshot` re-submission for the same `(ballot_id,
    input_hash)` key but with *different* resolution content (here,
    because a real, active `Delegation` was created between the two
    calls, changing `resolved_weights`) raises `SnapshotFrozenError`,
    never silently overwriting the first snapshot."""
    ballot_id = uuid4()
    scope_id = uuid4()
    delegator_id = uuid4()

    first = resolve_delegation_snapshot(
        delegation_store,
        delegation_snapshot_store,
        audit_store,
        ballot_id=ballot_id,
        policy_version=1,
        delegator_actor_ids=frozenset({delegator_id}),
        scope_type="ballot",
        scope_id=scope_id,
        direct_voters=frozenset(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert first.snapshot.resolved_weights == {}

    # A real, active delegation created *between* the two resolutions
    # changes what the same inputs resolve to.
    delegation_id = uuid4()
    create_delegation(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        delegator_actor_id=delegator_id,
        delegate_actor_id=uuid4(),
        scope_type="ballot",
        scope_id=scope_id,
        valid_from=clock.now(),
        valid_until=None,
        revocation_status="not_revoked",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    activate_delegation(
        delegation_store,
        audit_store,
        delegation_id=delegation_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    with pytest.raises(SnapshotFrozenError):
        resolve_delegation_snapshot(
            delegation_store,
            delegation_snapshot_store,
            audit_store,
            ballot_id=ballot_id,
            policy_version=1,
            delegator_actor_ids=frozenset({delegator_id}),
            scope_type="ballot",
            scope_id=scope_id,
            direct_voters=frozenset(),
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


# =============================================================================
# PACK-05: `GovernanceDecision` (governance-service, canon 19b.3) - the
# "freeze after commitment" invariant applied to this pack's own entity: a
# `GovernanceDecision` is immutable once `approved` or `rejected` - no
# further transition of the SAME row is ever allowed (a correction is
# always a brand-new decision with `supersedes_decision_id` set, never a
# further status change of this one).
# =============================================================================


def test_approved_governance_decision_cannot_then_be_rejected(
    governance_decision_store: InMemoryGovernanceDecisionStore,
    role_assignment_store: InMemoryRoleAssignmentStore,
    technical_challenge_store: InMemoryTechnicalChallengeStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    proposer = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="ballot_invalidation_proposer",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    approver = role_assignment_store.create(
        RoleAssignment(
            role_assignment_id=uuid4(),
            actor_id=uuid4(),
            role_code="ballot_invalidation_approver",
            scope_id=GLOBAL_SCOPE_ID,
            valid_from=clock.now(),
            valid_until=None,
            assigned_by=uuid4(),
            approval_reference=None,
            status=RoleAssignmentStatus.ACTIVE,
        )
    )
    ballot_id = uuid4()
    decision = propose_governance_decision(
        governance_decision_store,
        role_assignment_store,
        technical_challenge_store,
        audit_store,
        governance_decision_id=uuid4(),
        decision_type=GovernanceDecisionType.BALLOT_INVALIDATION,
        subject_reference={"ballot_id": str(ballot_id)},
        proposed_by_role_id=proposer.role_assignment_id,
        reason_code="X",
        evidence_references=(),
        supersedes_decision_id=None,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    ).decision
    approve_governance_decision(
        governance_decision_store,
        role_assignment_store,
        technical_challenge_store,
        audit_store,
        governance_decision_id=decision.governance_decision_id,
        approved_by_role_id=approver.role_assignment_id,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    with pytest.raises(ForbiddenGovernanceDecisionTransitionError):
        reject_governance_decision(
            governance_decision_store,
            role_assignment_store,
            technical_challenge_store,
            audit_store,
            governance_decision_id=decision.governance_decision_id,
            rejected_by_role_id=approver.role_assignment_id,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )

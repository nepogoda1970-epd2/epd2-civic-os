"""Governance Service application layer: `request_role_assignment`,
`activate_role_assignment`, `revoke_role_assignment`,
`propose_governance_policy`, `activate_governance_policy`,
`propose_governance_decision`, `approve_governance_decision`,
`reject_governance_decision`, `submit_technical_challenge`,
`begin_technical_challenge_review`, plus the read functions
`get_governance_decision` and `get_finality_status` — canon section 19b,
canon section 20.15's twelve-event catalog, ADR-016 through ADR-020.

Every state-changing command below accepts an optional caller-supplied
`event_id` (CT-00-04), the same idempotency pattern every prior pack's
services already establish: a retried call with the same `event_id`
returns the already-recorded result instead of re-attempting a
transition that would otherwise fail once the entity has moved past its
starting state.

Two-actor approval (ADR-020 item 1, INV-08) is enforced structurally
here, not merely by a caller-supplied boolean: every command that
requires it resolves the caller-supplied `RoleAssignment` id(s) from
`role_store`, checks each is `active` (unexpired, per the command's own
`clock`) and carries a `role_code` this pack's own `_*_ROLES` mapping
allows for that specific action, checks each covers the acted-on
subject's scope (`domain.scope_covers`), and — the actual "same actor"
rule ADR-020 item 1 names — checks the two resolved `RoleAssignment`
rows do not share the same `actor_id` (never merely that their
`role_assignment_id`s differ, which two records for the same real actor
could still satisfy).

Read-only cross-pack dependency (ADR-017, the first bidirectional
relationship in this project — `voting-service` reads back from this
service, see its own `invalidate_ballot` command): this module calls
`epd2_tally_service.application.get_result_publication` (an existing,
ADR-012-sanctioned read function) directly, from
`submit_technical_challenge` and `get_finality_status`, to read
`ResultPublication.challenge_deadline_at`. No PACK-02 identity/account/
eligibility/credential service, no `deliberation-service`, and no
`delegation-service` is ever imported here (ADR-017 Decision, explicit
exclusions) — see `tests/repository/test_service_boundaries.py`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_governance_service.domain import (
    GLOBAL_SCOPE_ID,
    PILOT_ROLE_CODES,
    FinalityOutcome,
    FinalityStatus,
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    GovernancePolicy,
    GovernancePolicyStatus,
    GovernancePolicyType,
    RoleAssignment,
    RoleAssignmentStatus,
    SubmitterAuthorizationType,
    TechnicalChallenge,
    TechnicalChallengeStatus,
    scope_covers,
)
from epd2_governance_service.events import (
    build_decision_approved_event,
    build_decision_proposed_event,
    build_decision_rejected_event,
    build_decision_superseded_event,
    build_policy_activated_event,
    build_policy_proposed_event,
    build_policy_superseded_event,
    build_role_assignment_activated_event,
    build_role_assignment_requested_event,
    build_role_assignment_revoked_event,
    build_technical_challenge_adjudicated_event,
    build_technical_challenge_submitted_event,
    governance_decision_full_state_payload,
    governance_policy_full_state_payload,
    role_assignment_full_state_payload,
    technical_challenge_full_state_payload,
)
from epd2_governance_service.exceptions import (
    GovernanceDecisionSupersededError,
    ResultFinalityBlockedByOpenChallengeError,
    ResultFinalityDeterminationDuplicateError,
    RoleAssignmentNotActiveError,
    RoleAssignmentScopeMismatchError,
    SameActorApprovalRejectedError,
    TechnicalChallengeSubmitterIneligibleError,
    TechnicalChallengeWindowClosedError,
    TwoActorApprovalRequiredError,
    UnknownGovernanceDecisionError,
    UnknownGovernancePolicyError,
    UnknownRoleAssignmentError,
    UnknownTechnicalChallengeError,
)
from epd2_governance_service.storage import (
    GovernanceDecisionStore,
    GovernancePolicyStore,
    RoleAssignmentStore,
    TechnicalChallengeStore,
)
from epd2_tally_service.application import get_result_publication

#: Audit Core's own policy version for entries this service appends -
#: independent of `events.EVENT_VERSION` (the wire event schema version).
AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "governance-service"

#: Audit `reason_code` classifications (ADR-006/ADR-014/ADR-019 pattern:
#: one generic classification per logical action-type).
_ROLE_ASSIGNMENT_AUDIT = "GOVERNANCE_ROLE_ASSIGNMENT_STATUS_CHANGED"
_POLICY_AUDIT = "GOVERNANCE_POLICY_STATUS_CHANGED"
_DECISION_AUDIT = "GOVERNANCE_DECISION_STATUS_CHANGED"
_CHALLENGE_AUDIT = "TECHNICAL_CHALLENGE_STATUS_CHANGED"


class PermissionDeniedError(PermissionError):
    reason_code = "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# ADR-020 §1 role-scoping tables (this pack's own, repository-side
# authorization design - see this module's own docstring)
# ---------------------------------------------------------------------------

_POLICY_PROPOSER_ROLES: frozenset[str] = frozenset({"governance_policy_proposer"})
_POLICY_APPROVER_ROLES: frozenset[str] = frozenset({"governance_policy_approver"})

_DECISION_PROPOSER_ROLES: dict[GovernanceDecisionType, frozenset[str]] = {
    GovernanceDecisionType.BALLOT_INVALIDATION: frozenset({"ballot_invalidation_proposer"}),
    GovernanceDecisionType.TECHNICAL_CHALLENGE_ADJUDICATION: frozenset(
        {"technical_challenge_reviewer", "governance_reviewer"}
    ),
    GovernanceDecisionType.RESULT_FINALITY_DETERMINATION: frozenset(
        {"governance_reviewer", "oversight_reviewer"}
    ),
    GovernanceDecisionType.MANDATE: frozenset({"oversight_reviewer"}),
    GovernanceDecisionType.OVERSIGHT_DIRECTIVE: frozenset({"oversight_reviewer"}),
}

_DECISION_APPROVER_ROLES: dict[GovernanceDecisionType, frozenset[str]] = {
    GovernanceDecisionType.BALLOT_INVALIDATION: frozenset({"ballot_invalidation_approver"}),
    GovernanceDecisionType.TECHNICAL_CHALLENGE_ADJUDICATION: frozenset(
        {"technical_challenge_reviewer", "governance_reviewer"}
    ),
    GovernanceDecisionType.RESULT_FINALITY_DETERMINATION: frozenset(
        {"governance_reviewer", "oversight_reviewer"}
    ),
    GovernanceDecisionType.MANDATE: frozenset({"oversight_reviewer"}),
    GovernanceDecisionType.OVERSIGHT_DIRECTIVE: frozenset({"oversight_reviewer"}),
}


def _decision_subject_scope_id(
    decision_type: GovernanceDecisionType,
    subject_reference: dict[str, object],
    challenge_store: TechnicalChallengeStore | None = None,
) -> UUID:
    """Resolve the scope a `RoleAssignment` must cover to propose/approve/
    reject a `GovernanceDecision` of `decision_type` — the referenced
    subject's own id for `ballot_invalidation`/`result_finality_
    determination`, or `GLOBAL_SCOPE_ID` for `mandate`/
    `oversight_directive` (canon 19b.3: their exact subject-form is left
    to a later implementation task).

    `technical_challenge_adjudication` resolves to the *challenged
    `ResultPublication`'s* id, not the `TechnicalChallenge`'s own id —
    a reviewer's `RoleAssignment.scope_id` is granted against the
    result being reviewed (the thing an operator can actually scope a
    role to ahead of time), never against an individual challenge's own
    randomly-generated id, which cannot be known before that challenge
    is ever submitted. Falls back to the challenge's own id only if
    `challenge_store` is not supplied or the challenge cannot be found
    (defensive; every real call site passes `challenge_store`).
    """
    if decision_type is GovernanceDecisionType.BALLOT_INVALIDATION:
        return UUID(str(subject_reference["ballot_id"]))
    if decision_type is GovernanceDecisionType.TECHNICAL_CHALLENGE_ADJUDICATION:
        technical_challenge_id = UUID(str(subject_reference["technical_challenge_id"]))
        if challenge_store is not None:
            challenge = challenge_store.get(technical_challenge_id)
            if challenge is not None:
                return challenge.result_publication_id
        return technical_challenge_id
    if decision_type is GovernanceDecisionType.RESULT_FINALITY_DETERMINATION:
        return UUID(str(subject_reference["result_publication_id"]))
    return GLOBAL_SCOPE_ID


def _require_active_in_scope_role(
    role_store: RoleAssignmentStore,
    *,
    role_assignment_id: UUID,
    allowed_role_codes: frozenset[str],
    subject_scope_id: UUID,
    now: datetime,
) -> RoleAssignment:
    role = role_store.get(role_assignment_id)
    if role is None:
        raise UnknownRoleAssignmentError(f"unknown role_assignment_id: {role_assignment_id}")
    if not role.is_active_at(now):
        raise RoleAssignmentNotActiveError(
            f"role_assignment {role_assignment_id} is not active at {now.isoformat()}"
        )
    if role.role_code not in allowed_role_codes:
        raise PermissionDeniedError(
            f"role_assignment {role_assignment_id} (role_code={role.role_code!r}) is not "
            f"authorized for this action; requires one of {sorted(allowed_role_codes)}"
        )
    if not scope_covers(role.scope_id, subject_scope_id):
        raise RoleAssignmentScopeMismatchError(
            f"role_assignment {role_assignment_id} (scope_id={role.scope_id}) does not cover "
            f"subject scope {subject_scope_id}"
        )
    return role


def _assert_distinct_actors(first: RoleAssignment, second: RoleAssignment) -> None:
    """ADR-020 item 1's actual "same actor" rule: compares the
    underlying `actor_id` behind each resolved `RoleAssignment`, not
    merely their (necessarily different, since they are different rows)
    `role_assignment_id` values — two different `RoleAssignment` rows
    can still belong to the same real actor."""
    if first.actor_id == second.actor_id:
        raise SameActorApprovalRejectedError(
            "the same underlying actor may not both propose/grant and approve this action "
            "(no role may approve or grant its own assignment)"
        )


@dataclass(frozen=True, slots=True)
class RoleAssignmentResult:
    assignment: RoleAssignment
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class GovernancePolicyResult:
    policy: GovernancePolicy
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ActivateGovernancePolicyResult:
    policy: GovernancePolicy
    superseded_policy: GovernancePolicy | None
    event: EventEnvelope
    superseded_event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class GovernanceDecisionResult:
    decision: GovernanceDecision
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DecideGovernanceDecisionResult:
    """Result of `approve_governance_decision`/`reject_governance_decision`.
    `superseded_decision`/`superseded_event` are populated only when
    `supersedes_decision_id` was set and this call approved the
    decision. `challenge`/`challenge_event` are populated only when
    `decision_type == technical_challenge_adjudication`."""

    decision: GovernanceDecision
    superseded_decision: GovernanceDecision | None
    challenge: TechnicalChallenge | None
    event: EventEnvelope
    superseded_event: EventEnvelope | None
    challenge_event: EventEnvelope | None
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class TechnicalChallengeResult:
    challenge: TechnicalChallenge
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# RoleAssignment commands
# ---------------------------------------------------------------------------


def request_role_assignment(
    role_store: RoleAssignmentStore,
    audit_store: AuditEventStore,
    *,
    role_assignment_id: UUID,
    actor_id: UUID,
    role_code: str,
    scope_id: UUID,
    valid_from: datetime,
    valid_until: datetime | None,
    granter_role_assignment_id: UUID,
    approval_reference: str | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> RoleAssignmentResult:
    """Create a new `RoleAssignment` in `pending` status (canon 8.4;
    physically implemented here per ADR-016). `role_code` must be one of
    `domain.PILOT_ROLE_CODES` (ADR-020 §5) — a pilot-scoped, application-
    layer check, never a structural invariant of `RoleAssignment` itself
    (canon 19b.1 keeps `role_code` an open string at canon level).

    The granting `RoleAssignment` (`granter_role_assignment_id`) must be
    `active` and its underlying actor must differ from `actor_id`
    (ADR-020 item 6's "no actor may seed or approve their own
    assignment", applied here to ordinary grants too: "no role may
    approve or grant its own assignment").
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to request a role assignment")
    if role_code not in PILOT_ROLE_CODES:
        raise PermissionDeniedError(
            f"role_code {role_code!r} is not part of the pilot role taxonomy "
            f"({sorted(PILOT_ROLE_CODES)})"
        )

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        assignment = role_store.get(role_assignment_id)
        if assignment is None:
            raise UnknownRoleAssignmentError(
                f"idempotent replay for event_id {resolved_event_id} found no role assignment "
                f"{role_assignment_id}"
            )
        event = build_role_assignment_requested_event(
            event_id=resolved_event_id,
            assignment=assignment,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return RoleAssignmentResult(assignment=assignment, event=event, audit_event=existing_audit)

    now = clock.now()
    granter = role_store.get(granter_role_assignment_id)
    if granter is None:
        raise UnknownRoleAssignmentError(
            f"unknown granter_role_assignment_id: {granter_role_assignment_id}"
        )
    if not granter.is_active_at(now):
        raise RoleAssignmentNotActiveError(
            f"granter role_assignment {granter_role_assignment_id} is not active at "
            f"{now.isoformat()}"
        )
    if granter.actor_id == actor_id:
        raise SameActorApprovalRejectedError(
            "no role may grant a RoleAssignment to its own actor (ADR-020 item 6)"
        )

    assignment = RoleAssignment(
        role_assignment_id=role_assignment_id,
        actor_id=actor_id,
        role_code=role_code,
        scope_id=scope_id,
        valid_from=valid_from,
        valid_until=valid_until,
        assigned_by=granter_role_assignment_id,
        approval_reference=approval_reference,
        status=RoleAssignmentStatus.PENDING,
    )
    stored = role_store.create(assignment)
    event = build_role_assignment_requested_event(
        event_id=resolved_event_id,
        assignment=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="role_assignment",
            target_id=stored.role_assignment_id,
            action="request_role_assignment",
            reason_code=_ROLE_ASSIGNMENT_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(role_assignment_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return RoleAssignmentResult(assignment=stored, event=event, audit_event=audit_event)


def activate_role_assignment(
    role_store: RoleAssignmentStore,
    audit_store: AuditEventStore,
    *,
    role_assignment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> RoleAssignmentResult:
    """`pending -> active` (canon 20.15: `governance.role_assignment_activated`)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate a role assignment")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        assignment = role_store.get(role_assignment_id)
        if assignment is None:
            raise UnknownRoleAssignmentError(f"unknown role_assignment_id: {role_assignment_id}")
        event = build_role_assignment_activated_event(
            event_id=resolved_event_id,
            assignment=assignment,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return RoleAssignmentResult(assignment=assignment, event=event, audit_event=existing_audit)

    assignment = role_store.get(role_assignment_id)
    if assignment is None:
        raise UnknownRoleAssignmentError(f"unknown role_assignment_id: {role_assignment_id}")
    before_hash = compute_payload_hash(role_assignment_full_state_payload(assignment))
    updated = assignment.with_status(RoleAssignmentStatus.ACTIVE)
    role_store.save(updated)
    now = clock.now()
    event = build_role_assignment_activated_event(
        event_id=resolved_event_id,
        assignment=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="role_assignment",
            target_id=updated.role_assignment_id,
            action="activate_role_assignment",
            reason_code=_ROLE_ASSIGNMENT_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(role_assignment_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return RoleAssignmentResult(assignment=updated, event=event, audit_event=audit_event)


def revoke_role_assignment(
    role_store: RoleAssignmentStore,
    audit_store: AuditEventStore,
    *,
    role_assignment_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> RoleAssignmentResult:
    """`active|pending|suspended -> revoked` (canon 20.15:
    `governance.role_assignment_revoked`)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to revoke a role assignment")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        assignment = role_store.get(role_assignment_id)
        if assignment is None:
            raise UnknownRoleAssignmentError(f"unknown role_assignment_id: {role_assignment_id}")
        event = build_role_assignment_revoked_event(
            event_id=resolved_event_id,
            assignment=assignment,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return RoleAssignmentResult(assignment=assignment, event=event, audit_event=existing_audit)

    assignment = role_store.get(role_assignment_id)
    if assignment is None:
        raise UnknownRoleAssignmentError(f"unknown role_assignment_id: {role_assignment_id}")
    before_hash = compute_payload_hash(role_assignment_full_state_payload(assignment))
    updated = assignment.with_status(RoleAssignmentStatus.REVOKED)
    role_store.save(updated)
    now = clock.now()
    event = build_role_assignment_revoked_event(
        event_id=resolved_event_id,
        assignment=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="role_assignment",
            target_id=updated.role_assignment_id,
            action="revoke_role_assignment",
            reason_code=_ROLE_ASSIGNMENT_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(role_assignment_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return RoleAssignmentResult(assignment=updated, event=event, audit_event=audit_event)


def get_role_assignment(
    store: RoleAssignmentStore, *, role_assignment_id: UUID
) -> RoleAssignment | None:
    """Plain, unaudited read of one `RoleAssignment` by id."""
    return store.get(role_assignment_id)


# ---------------------------------------------------------------------------
# GovernancePolicy commands
# ---------------------------------------------------------------------------


def propose_governance_policy(
    policy_store: GovernancePolicyStore,
    role_store: RoleAssignmentStore,
    audit_store: AuditEventStore,
    *,
    governance_policy_id: UUID,
    policy_type: GovernancePolicyType,
    rule_definition: dict[str, object],
    effective_from: datetime,
    proposed_by_role_id: UUID,
    approved_by_role_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> GovernancePolicyResult:
    """Create a new `GovernancePolicy` in `draft` status (canon 19b.2).
    `version` is assigned automatically as one more than the highest
    version ever created for `policy_type` (canon: "монотонно
    возрастающее"). Both `proposed_by_role_id` and `approved_by_role_id`
    must already be active, in the correct role, and distinct actors
    (ADR-020 item 1) at proposal time; `activate_governance_policy`
    re-validates both at activation time, since validity can change in
    between.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to propose a governance policy")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        policy = policy_store.get(governance_policy_id)
        if policy is None:
            raise UnknownGovernancePolicyError(
                f"idempotent replay for event_id {resolved_event_id} found no governance policy "
                f"{governance_policy_id}"
            )
        event = build_policy_proposed_event(
            event_id=resolved_event_id,
            policy=policy,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return GovernancePolicyResult(policy=policy, event=event, audit_event=existing_audit)

    now = clock.now()
    proposer = _require_active_in_scope_role(
        role_store,
        role_assignment_id=proposed_by_role_id,
        allowed_role_codes=_POLICY_PROPOSER_ROLES,
        subject_scope_id=GLOBAL_SCOPE_ID,
        now=now,
    )
    approver = _require_active_in_scope_role(
        role_store,
        role_assignment_id=approved_by_role_id,
        allowed_role_codes=_POLICY_APPROVER_ROLES,
        subject_scope_id=GLOBAL_SCOPE_ID,
        now=now,
    )
    _assert_distinct_actors(proposer, approver)

    next_version = policy_store.latest_version_for_policy_type(policy_type.value) + 1
    policy = GovernancePolicy(
        governance_policy_id=governance_policy_id,
        policy_type=policy_type,
        rule_definition=rule_definition,
        effective_from=effective_from,
        proposed_by_role_id=proposed_by_role_id,
        approved_by_role_id=approved_by_role_id,
        version=next_version,
        status=GovernancePolicyStatus.DRAFT,
    )
    stored = policy_store.create(policy)
    event = build_policy_proposed_event(
        event_id=resolved_event_id,
        policy=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="governance_policy",
            target_id=stored.governance_policy_id,
            action="propose_governance_policy",
            reason_code=_POLICY_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(governance_policy_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return GovernancePolicyResult(policy=stored, event=event, audit_event=audit_event)


def activate_governance_policy(
    policy_store: GovernancePolicyStore,
    role_store: RoleAssignmentStore,
    audit_store: AuditEventStore,
    *,
    governance_policy_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> ActivateGovernancePolicyResult:
    """`draft -> active` (ADR-020 item 1: requires re-validating both
    `proposed_by_role_id` and `approved_by_role_id` are still active, in
    the correct role, in scope, and distinct actors). If another policy
    is already `active` for the same `policy_type`, this call also
    transitions it `active -> superseded` (canon 19b.2: "не более одной
    активной версии одновременно")."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate a governance policy")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        policy = policy_store.get(governance_policy_id)
        if policy is None:
            raise UnknownGovernancePolicyError(
                f"unknown governance_policy_id: {governance_policy_id}"
            )
        event = build_policy_activated_event(
            event_id=resolved_event_id,
            policy=policy,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return ActivateGovernancePolicyResult(
            policy=policy,
            superseded_policy=None,
            event=event,
            superseded_event=None,
            audit_event=existing_audit,
        )

    policy = policy_store.get(governance_policy_id)
    if policy is None:
        raise UnknownGovernancePolicyError(f"unknown governance_policy_id: {governance_policy_id}")

    now = clock.now()
    proposer = _require_active_in_scope_role(
        role_store,
        role_assignment_id=policy.proposed_by_role_id,
        allowed_role_codes=_POLICY_PROPOSER_ROLES,
        subject_scope_id=GLOBAL_SCOPE_ID,
        now=now,
    )
    approver = _require_active_in_scope_role(
        role_store,
        role_assignment_id=policy.approved_by_role_id,
        allowed_role_codes=_POLICY_APPROVER_ROLES,
        subject_scope_id=GLOBAL_SCOPE_ID,
        now=now,
    )
    _assert_distinct_actors(proposer, approver)

    superseded_policy: GovernancePolicy | None = None
    superseded_event: EventEnvelope | None = None
    currently_active = policy_store.get_active_for_policy_type(policy.policy_type.value)
    if (
        currently_active is not None
        and currently_active.governance_policy_id != governance_policy_id
    ):
        superseded_now = clock.now()
        superseded_updated = currently_active.with_status(GovernancePolicyStatus.SUPERSEDED)
        policy_store.save(superseded_updated)
        superseded_policy = superseded_updated
        superseded_event = build_policy_superseded_event(
            event_id=generate_uuid(),
            policy=superseded_updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=superseded_now,
        )
        append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=generate_uuid(),
                event_type="governance.policy_superseded",
                occurred_at=superseded_now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="governance_policy",
                target_id=superseded_updated.governance_policy_id,
                action="supersede_governance_policy",
                reason_code=_POLICY_AUDIT,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=compute_payload_hash(
                    governance_policy_full_state_payload(currently_active)
                ),
                after_hash=compute_payload_hash(
                    governance_policy_full_state_payload(superseded_updated)
                ),
            ),
            clock=clock,
        )

    before_hash = compute_payload_hash(governance_policy_full_state_payload(policy))
    updated = policy.with_status(GovernancePolicyStatus.ACTIVE)
    policy_store.save(updated)
    now = clock.now()
    event = build_policy_activated_event(
        event_id=resolved_event_id,
        policy=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="governance_policy",
            target_id=updated.governance_policy_id,
            action="activate_governance_policy",
            reason_code=_POLICY_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(governance_policy_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return ActivateGovernancePolicyResult(
        policy=updated,
        superseded_policy=superseded_policy,
        event=event,
        superseded_event=superseded_event,
        audit_event=audit_event,
    )


# ---------------------------------------------------------------------------
# GovernanceDecision commands
# ---------------------------------------------------------------------------


def propose_governance_decision(
    decision_store: GovernanceDecisionStore,
    role_store: RoleAssignmentStore,
    challenge_store: TechnicalChallengeStore,
    audit_store: AuditEventStore,
    *,
    governance_decision_id: UUID,
    decision_type: GovernanceDecisionType,
    subject_reference: dict[str, object],
    proposed_by_role_id: UUID,
    reason_code: str,
    evidence_references: Sequence[str],
    supersedes_decision_id: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> GovernanceDecisionResult:
    """Create a new `GovernanceDecision` in `proposed` status (canon
    19b.3). For `decision_type = result_finality_determination`, canon
    19b.5's "no finality while any challenge remains unresolved" rule is
    checked here too (in addition to `approve_governance_decision`,
    which is the authoritative enforcement point — this early check only
    gives faster feedback to a caller proposing a decision that could
    never be approved).
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to propose a governance decision")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        decision = decision_store.get(governance_decision_id)
        if decision is None:
            raise UnknownGovernanceDecisionError(
                f"idempotent replay for event_id {resolved_event_id} found no governance decision "
                f"{governance_decision_id}"
            )
        event = build_decision_proposed_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return GovernanceDecisionResult(decision=decision, event=event, audit_event=existing_audit)

    now = clock.now()
    subject_scope_id = _decision_subject_scope_id(decision_type, subject_reference, challenge_store)
    _require_active_in_scope_role(
        role_store,
        role_assignment_id=proposed_by_role_id,
        allowed_role_codes=_DECISION_PROPOSER_ROLES[decision_type],
        subject_scope_id=subject_scope_id,
        now=now,
    )

    if decision_type is GovernanceDecisionType.RESULT_FINALITY_DETERMINATION:
        result_publication_id = UUID(str(subject_reference["result_publication_id"]))
        if challenge_store.has_unresolved_challenges(result_publication_id):
            raise ResultFinalityBlockedByOpenChallengeError(
                f"result_publication {result_publication_id} still has unresolved challenges"
            )
        if (
            supersedes_decision_id is None
            and decision_store.get_current_result_finality_determination(result_publication_id)
            is not None
        ):
            raise ResultFinalityDeterminationDuplicateError(
                f"result_publication {result_publication_id} already has an approved, "
                "non-superseded result_finality_determination decision"
            )

    decision = GovernanceDecision(
        governance_decision_id=governance_decision_id,
        decision_type=decision_type,
        subject_reference=subject_reference,
        proposed_by_role_id=proposed_by_role_id,
        approved_by_role_id=None,
        rejected_by_role_id=None,
        reason_code=reason_code,
        evidence_references=tuple(evidence_references),
        finality_outcome=None,
        created_at=now,
        decided_at=None,
        supersedes_decision_id=supersedes_decision_id,
        status=GovernanceDecisionStatus.PROPOSED,
    )
    stored = decision_store.create(decision)
    event = build_decision_proposed_event(
        event_id=resolved_event_id,
        decision=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="governance_decision",
            target_id=stored.governance_decision_id,
            action="propose_governance_decision",
            reason_code=_DECISION_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(governance_decision_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return GovernanceDecisionResult(decision=stored, event=event, audit_event=audit_event)


def _adjudicate_linked_challenge_if_any(
    challenge_store: TechnicalChallengeStore,
    audit_store: AuditEventStore,
    *,
    decision: GovernanceDecision,
    new_challenge_status: TechnicalChallengeStatus,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID,
    clock: Clock,
) -> tuple[TechnicalChallenge | None, EventEnvelope | None]:
    """Side effect of `approve_governance_decision`/
    `reject_governance_decision` when `decision.decision_type ==
    technical_challenge_adjudication` (canon 19b.4's `under_review ->
    upheld`/`under_review -> rejected` transitions, which exist only
    "through a linked GovernanceDecision", never as a standalone
    command)."""
    if decision.decision_type is not GovernanceDecisionType.TECHNICAL_CHALLENGE_ADJUDICATION:
        return None, None
    technical_challenge_id = UUID(str(decision.subject_reference["technical_challenge_id"]))
    challenge = challenge_store.get(technical_challenge_id)
    if challenge is None:
        raise UnknownTechnicalChallengeError(
            f"unknown technical_challenge_id: {technical_challenge_id}"
        )
    before_hash = compute_payload_hash(technical_challenge_full_state_payload(challenge))
    updated = challenge.with_status(
        new_challenge_status, governance_decision_id=decision.governance_decision_id
    )
    challenge_store.save(updated)
    now = clock.now()
    event = build_technical_challenge_adjudicated_event(
        event_id=generate_uuid(),
        challenge=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=now,
    )
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=generate_uuid(),
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="technical_challenge",
            target_id=updated.technical_challenge_id,
            action="adjudicate_technical_challenge",
            reason_code=_CHALLENGE_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(technical_challenge_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return updated, event


def approve_governance_decision(
    decision_store: GovernanceDecisionStore,
    role_store: RoleAssignmentStore,
    challenge_store: TechnicalChallengeStore,
    audit_store: AuditEventStore,
    *,
    governance_decision_id: UUID,
    approved_by_role_id: UUID,
    finality_outcome: FinalityOutcome | None = None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DecideGovernanceDecisionResult:
    """`proposed -> approved` (ADR-020 item 1: two-actor approval,
    required for every `GovernanceDecision` approval, which includes
    ballot invalidation and result-finality determination as named
    `decision_type` values). When `decision_type ==
    technical_challenge_adjudication`, also transitions the linked
    `TechnicalChallenge` to `upheld` (canon 19b.4). When
    `decision_type == result_finality_determination`, re-validates canon
    19b.5's no-open-challenge and no-duplicate rules and requires
    `finality_outcome`. When `supersedes_decision_id` was set at
    proposal time, also emits `governance.decision_superseded`.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to approve a governance decision")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        decision = decision_store.get(governance_decision_id)
        if decision is None:
            raise UnknownGovernanceDecisionError(
                f"unknown governance_decision_id: {governance_decision_id}"
            )
        event = build_decision_approved_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DecideGovernanceDecisionResult(
            decision=decision,
            superseded_decision=None,
            challenge=None,
            event=event,
            superseded_event=None,
            challenge_event=None,
            audit_event=existing_audit,
        )

    decision = decision_store.get(governance_decision_id)
    if decision is None:
        raise UnknownGovernanceDecisionError(
            f"unknown governance_decision_id: {governance_decision_id}"
        )

    now = clock.now()
    subject_scope_id = _decision_subject_scope_id(
        decision.decision_type, dict(decision.subject_reference), challenge_store
    )
    proposer = _require_active_in_scope_role(
        role_store,
        role_assignment_id=decision.proposed_by_role_id,
        allowed_role_codes=_DECISION_PROPOSER_ROLES[decision.decision_type],
        subject_scope_id=subject_scope_id,
        now=now,
    )
    approver = _require_active_in_scope_role(
        role_store,
        role_assignment_id=approved_by_role_id,
        allowed_role_codes=_DECISION_APPROVER_ROLES[decision.decision_type],
        subject_scope_id=subject_scope_id,
        now=now,
    )
    _assert_distinct_actors(proposer, approver)

    resolved_finality_outcome: FinalityOutcome | None = None
    if decision.decision_type is GovernanceDecisionType.RESULT_FINALITY_DETERMINATION:
        if finality_outcome is None:
            raise TwoActorApprovalRequiredError(
                "finality_outcome is required to approve a result_finality_determination decision"
            )
        result_publication_id = UUID(str(decision.subject_reference["result_publication_id"]))
        if challenge_store.has_unresolved_challenges(result_publication_id):
            raise ResultFinalityBlockedByOpenChallengeError(
                f"result_publication {result_publication_id} still has unresolved challenges"
            )
        current = decision_store.get_current_result_finality_determination(result_publication_id)
        if (
            current is not None
            and current.governance_decision_id != decision.supersedes_decision_id
        ):
            raise ResultFinalityDeterminationDuplicateError(
                f"result_publication {result_publication_id} already has an approved, "
                "non-superseded result_finality_determination decision"
            )
        resolved_finality_outcome = finality_outcome

    superseded_decision: GovernanceDecision | None = None
    superseded_event: EventEnvelope | None = None
    if decision.supersedes_decision_id is not None:
        target = decision_store.get(decision.supersedes_decision_id)
        if target is None or target.status is not GovernanceDecisionStatus.APPROVED:
            raise UnknownGovernanceDecisionError(
                f"supersedes_decision_id {decision.supersedes_decision_id} does not reference an "
                "approved governance decision"
            )
        if decision_store.find_superseding(target.governance_decision_id) is not None:
            raise GovernanceDecisionSupersededError(
                f"governance_decision {target.governance_decision_id} has already been superseded"
            )

    before_hash = compute_payload_hash(governance_decision_full_state_payload(decision))
    updated = decision.with_approved(
        approved_by_role_id=approved_by_role_id,
        decided_at=now,
        finality_outcome=resolved_finality_outcome,
    )
    decision_store.save(updated)
    event = build_decision_approved_event(
        event_id=resolved_event_id,
        decision=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="governance_decision",
            target_id=updated.governance_decision_id,
            action="approve_governance_decision",
            reason_code=_DECISION_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(governance_decision_full_state_payload(updated)),
        ),
        clock=clock,
    )

    if updated.supersedes_decision_id is not None:
        target = decision_store.get(updated.supersedes_decision_id)
        assert target is not None  # validated above
        superseded_decision = target
        superseded_event = build_decision_superseded_event(
            event_id=generate_uuid(),
            superseded_decision=target,
            superseding_decision=updated,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=resolved_event_id,
            occurred_at=now,
        )
        append_audit_event(
            audit_store,
            AppendAuditEventRequest(
                audit_event_id=generate_uuid(),
                event_type=superseded_event.event_type,
                occurred_at=now,
                actor_id=actor.actor_id,
                actor_type=actor.actor_type,
                target_type="governance_decision",
                target_id=target.governance_decision_id,
                action="supersede_governance_decision",
                reason_code=_DECISION_AUDIT,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=compute_payload_hash(governance_decision_full_state_payload(target)),
                after_hash=compute_payload_hash(governance_decision_full_state_payload(target)),
            ),
            clock=clock,
        )

    challenge, challenge_event = _adjudicate_linked_challenge_if_any(
        challenge_store,
        audit_store,
        decision=updated,
        new_challenge_status=TechnicalChallengeStatus.UPHELD,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=resolved_event_id,
        clock=clock,
    )

    return DecideGovernanceDecisionResult(
        decision=updated,
        superseded_decision=superseded_decision,
        challenge=challenge,
        event=event,
        superseded_event=superseded_event,
        challenge_event=challenge_event,
        audit_event=audit_event,
    )


def reject_governance_decision(
    decision_store: GovernanceDecisionStore,
    role_store: RoleAssignmentStore,
    challenge_store: TechnicalChallengeStore,
    audit_store: AuditEventStore,
    *,
    governance_decision_id: UUID,
    rejected_by_role_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> DecideGovernanceDecisionResult:
    """`proposed -> rejected` (ADR-020 item 1: two-actor approval). When
    `decision_type == technical_challenge_adjudication`, also
    transitions the linked `TechnicalChallenge` to `rejected`."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to reject a governance decision")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        decision = decision_store.get(governance_decision_id)
        if decision is None:
            raise UnknownGovernanceDecisionError(
                f"unknown governance_decision_id: {governance_decision_id}"
            )
        event = build_decision_rejected_event(
            event_id=resolved_event_id,
            decision=decision,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return DecideGovernanceDecisionResult(
            decision=decision,
            superseded_decision=None,
            challenge=None,
            event=event,
            superseded_event=None,
            challenge_event=None,
            audit_event=existing_audit,
        )

    decision = decision_store.get(governance_decision_id)
    if decision is None:
        raise UnknownGovernanceDecisionError(
            f"unknown governance_decision_id: {governance_decision_id}"
        )

    now = clock.now()
    subject_scope_id = _decision_subject_scope_id(
        decision.decision_type, dict(decision.subject_reference), challenge_store
    )
    proposer = _require_active_in_scope_role(
        role_store,
        role_assignment_id=decision.proposed_by_role_id,
        allowed_role_codes=_DECISION_PROPOSER_ROLES[decision.decision_type],
        subject_scope_id=subject_scope_id,
        now=now,
    )
    rejecter = _require_active_in_scope_role(
        role_store,
        role_assignment_id=rejected_by_role_id,
        allowed_role_codes=_DECISION_APPROVER_ROLES[decision.decision_type],
        subject_scope_id=subject_scope_id,
        now=now,
    )
    _assert_distinct_actors(proposer, rejecter)

    before_hash = compute_payload_hash(governance_decision_full_state_payload(decision))
    updated = decision.with_rejected(rejected_by_role_id=rejected_by_role_id, decided_at=now)
    decision_store.save(updated)
    event = build_decision_rejected_event(
        event_id=resolved_event_id,
        decision=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="governance_decision",
            target_id=updated.governance_decision_id,
            action="reject_governance_decision",
            reason_code=_DECISION_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(governance_decision_full_state_payload(updated)),
        ),
        clock=clock,
    )

    challenge, challenge_event = _adjudicate_linked_challenge_if_any(
        challenge_store,
        audit_store,
        decision=updated,
        new_challenge_status=TechnicalChallengeStatus.REJECTED,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=resolved_event_id,
        clock=clock,
    )

    return DecideGovernanceDecisionResult(
        decision=updated,
        superseded_decision=None,
        challenge=challenge,
        event=event,
        superseded_event=None,
        challenge_event=challenge_event,
        audit_event=audit_event,
    )


def get_governance_decision(
    store: GovernanceDecisionStore, *, governance_decision_id: UUID
) -> GovernanceDecision | None:
    """Plain, unaudited read of one `GovernanceDecision` by id.

    Added under ADR-017 ("PACK-05 cross-pack boundary"), which names
    `epd2_governance_service.application` (never `.storage`/`.domain`)
    as the one authorized way `voting-service.invalidate_ballot` may
    read a `GovernanceDecision` before invalidating its own `Ballot`
    (canon 19b.6, ADR-017 Option B) — the first reverse/bidirectional
    cross-pack read edge in this project. Additive; does not change any
    existing function's signature or behavior.
    """
    return store.get(governance_decision_id)


def is_current_approved_decision(
    store: GovernanceDecisionStore, decision: GovernanceDecision
) -> bool:
    """`True` if `decision` is `approved` and has not since been
    superseded — the check `voting-service.invalidate_ballot` must make
    before trusting a `ballot_invalidation` decision (canon 19b.3/19b.6;
    `GOVERNANCE_DECISION_SUPERSEDED`, ADR-019).

    Compares `decision.status.value` (a plain string) rather than enum
    identity (`decision.status is GovernanceDecisionStatus.APPROVED`)
    deliberately: `voting-service.invalidate_ballot` calls this function
    across the ADR-017 reverse read edge without ever importing
    `epd2_governance_service.domain` (only `.application`, per the
    boundary this project's `.application`-only convention already
    established for every other cross-pack edge), so its own tests
    construct duck-typed decision objects that carry a `.value`-bearing
    `status` without being a real `GovernanceDecisionStatus` instance.
    """
    return (
        decision.status.value == GovernanceDecisionStatus.APPROVED.value
        and store.find_superseding(decision.governance_decision_id) is None
    )


def get_finality_status(
    decision_store: GovernanceDecisionStore,
    challenge_store: TechnicalChallengeStore,
    *,
    result_publication_id: UUID,
) -> FinalityStatus:
    """Derived read model (canon 19b.3/19b.6) — never a stored field.
    See `domain.FinalityStatus` for the exact four-value derivation this
    function implements verbatim."""
    if challenge_store.has_unresolved_challenges(result_publication_id):
        return FinalityStatus.FINALITY_BLOCKED
    current = decision_store.get_current_result_finality_determination(result_publication_id)
    if current is None:
        return FinalityStatus.PROVISIONAL
    if current.finality_outcome is FinalityOutcome.FINAL:
        return FinalityStatus.FINAL
    if current.finality_outcome is FinalityOutcome.INVALIDATED:
        return FinalityStatus.INVALIDATED
    return FinalityStatus.PROVISIONAL


# ---------------------------------------------------------------------------
# TechnicalChallenge commands
# ---------------------------------------------------------------------------


def submit_technical_challenge(
    challenge_store: TechnicalChallengeStore,
    role_store: RoleAssignmentStore,
    result_publication_store: Any,
    audit_store: AuditEventStore,
    *,
    technical_challenge_id: UUID,
    result_publication_id: UUID,
    submitter_authorization_type: SubmitterAuthorizationType,
    submitter_authorization_reference: str,
    challenge_reason_code: str,
    evidence_references: Sequence[str],
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> TechnicalChallengeResult:
    """Create a new `TechnicalChallenge` in `submitted` status (canon
    19b.4). `submitted_at` (the command's own clock reading) must
    strictly precede the referenced `ResultPublication.
    challenge_deadline_at` (read via the ADR-012/017-sanctioned
    `epd2_tally_service.application.get_result_publication`).

    Authorization validation boundary (canon 19b.4, exactly as
    specified): a `role_assignment`-type reference is validated locally
    — parsed as a `RoleAssignment.role_assignment_id`, required active
    and in scope for `result_publication_id`
    (`TechnicalChallengeSubmitterIneligibleError` otherwise). A
    `participation_credential`-type reference is never dereferenced or
    re-verified against any upstream service — accepted as an opaque,
    caller-supplied proof, exactly as `publish_ledger_entry`'s
    caller-supplied `raw_content` already established for PACK-04.

    `result_publication_store` is accepted as an `Any`-typed passthrough
    parameter (the same ADR-008/ADR-012 convention `epd2_voting_service.
    application`/`epd2_transparency_service.application` already use for
    their own cross-pack store parameters): this module's only import of
    `epd2_tally_service` is `.application.get_result_publication`, never
    `.storage`/`.domain`, so it cannot reach past that function's own
    public contract even for a type annotation.
    """
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to submit a technical challenge")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        challenge = challenge_store.get(technical_challenge_id)
        if challenge is None:
            raise UnknownTechnicalChallengeError(
                f"idempotent replay for event_id {resolved_event_id} found no technical challenge "
                f"{technical_challenge_id}"
            )
        event = build_technical_challenge_submitted_event(
            event_id=resolved_event_id,
            challenge=challenge,
            actor=actor,
            correlation_id=correlation_id,
            causation_id=None,
            occurred_at=existing_audit.occurred_at,
        )
        return TechnicalChallengeResult(
            challenge=challenge, event=event, audit_event=existing_audit
        )

    result_publication = get_result_publication(
        result_publication_store, result_publication_id=result_publication_id
    )
    if result_publication is None:
        raise UnknownTechnicalChallengeError(
            f"unknown result_publication_id referenced by challenge: {result_publication_id}"
        )

    now = clock.now()
    if now >= result_publication.challenge_deadline_at:
        raise TechnicalChallengeWindowClosedError(
            f"result_publication {result_publication_id}'s challenge window closed at "
            f"{result_publication.challenge_deadline_at.isoformat()}"
        )

    if submitter_authorization_type is SubmitterAuthorizationType.ROLE_ASSIGNMENT:
        try:
            role_assignment_id = UUID(submitter_authorization_reference)
        except ValueError as exc:
            raise TechnicalChallengeSubmitterIneligibleError(
                "role_assignment-type submitter_authorization_reference must be a valid "
                "RoleAssignment id"
            ) from exc
        role = role_store.get(role_assignment_id)
        if (
            role is None
            or not role.is_active_at(now)
            or not scope_covers(role.scope_id, result_publication_id)
        ):
            raise TechnicalChallengeSubmitterIneligibleError(
                f"role_assignment {role_assignment_id} is not an active, in-scope RoleAssignment "
                f"for result_publication {result_publication_id}"
            )
    # submitter_authorization_type is participation_credential: accepted as an
    # opaque, caller-supplied proof, never dereferenced (see docstring above).

    challenge = TechnicalChallenge(
        technical_challenge_id=technical_challenge_id,
        result_publication_id=result_publication_id,
        submitter_authorization_type=submitter_authorization_type,
        submitter_authorization_reference=submitter_authorization_reference,
        challenge_reason_code=challenge_reason_code,
        evidence_references=tuple(evidence_references),
        submitted_at=now,
        governance_decision_id=None,
        status=TechnicalChallengeStatus.SUBMITTED,
    )
    stored = challenge_store.create(challenge)
    event = build_technical_challenge_submitted_event(
        event_id=resolved_event_id,
        challenge=stored,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type=event.event_type,
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="technical_challenge",
            target_id=stored.technical_challenge_id,
            action="submit_technical_challenge",
            reason_code=_CHALLENGE_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(technical_challenge_full_state_payload(stored)),
        ),
        clock=clock,
    )
    return TechnicalChallengeResult(challenge=stored, event=event, audit_event=audit_event)


def begin_technical_challenge_review(
    challenge_store: TechnicalChallengeStore,
    audit_store: AuditEventStore,
    *,
    technical_challenge_id: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
    event_id: UUID | None = None,
) -> TechnicalChallenge:
    """`submitted -> under_review` (canon 19b.4). Deliberately has no
    corresponding canonical event — canon section 20.15's twelve-event
    catalog names only `governance.technical_challenge_submitted` and
    `governance.technical_challenge_adjudicated`; this transition is
    audited (CT-00-07) but does not emit a domain event envelope, since
    inventing a thirteenth event not in canon's catalog is out of this
    pack's scope (requirement 15: do not change canon 0.4.0)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to begin a technical challenge review")

    resolved_event_id = event_id if event_id is not None else generate_uuid()
    existing_audit = audit_store.get_by_event_id(resolved_event_id)
    if existing_audit is not None:
        challenge = challenge_store.get(technical_challenge_id)
        if challenge is None:
            raise UnknownTechnicalChallengeError(
                f"unknown technical_challenge_id: {technical_challenge_id}"
            )
        return challenge

    challenge = challenge_store.get(technical_challenge_id)
    if challenge is None:
        raise UnknownTechnicalChallengeError(
            f"unknown technical_challenge_id: {technical_challenge_id}"
        )
    before_hash = compute_payload_hash(technical_challenge_full_state_payload(challenge))
    updated = challenge.with_status(TechnicalChallengeStatus.UNDER_REVIEW)
    challenge_store.save(updated)
    now = clock.now()
    append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=resolved_event_id,
            event_type="governance.technical_challenge_review_started",
            occurred_at=now,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type="technical_challenge",
            target_id=updated.technical_challenge_id,
            action="begin_technical_challenge_review",
            reason_code=_CHALLENGE_AUDIT,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=compute_payload_hash(technical_challenge_full_state_payload(updated)),
        ),
        clock=clock,
    )
    return updated


def get_technical_challenge(
    store: TechnicalChallengeStore, *, technical_challenge_id: UUID
) -> TechnicalChallenge | None:
    """Plain, unaudited read of one `TechnicalChallenge` by id."""
    return store.get(technical_challenge_id)

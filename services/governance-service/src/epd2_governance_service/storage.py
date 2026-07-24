"""Storage protocols and in-memory reference adapters for Governance
Service's four owned entities: `RoleAssignment`, `GovernancePolicy`,
`GovernanceDecision`, `TechnicalChallenge` (canon section 19b / 8.4). A
durable backend can implement these same protocols without any change to
`application.py`.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_governance_service.domain import (
    UNRESOLVED_TECHNICAL_CHALLENGE_STATUSES,
    GovernanceDecision,
    GovernanceDecisionStatus,
    GovernanceDecisionType,
    GovernancePolicy,
    GovernancePolicyStatus,
    RoleAssignment,
    TechnicalChallenge,
)
from epd2_governance_service.exceptions import (
    GovernanceDecisionConflictError,
    GovernancePolicyConflictError,
    RoleAssignmentConflictError,
    TechnicalChallengeConflictError,
)


class RoleAssignmentStore(Protocol):
    def create(self, assignment: RoleAssignment) -> RoleAssignment:
        """Create a new `RoleAssignment`. Idempotent by content: if
        `assignment.role_assignment_id` already exists with identical
        content, returns the existing record; if it exists with
        different content, raises `RoleAssignmentConflictError`."""
        ...

    def save(self, assignment: RoleAssignment) -> None:
        """Persist a `status` transition."""
        ...

    def get(self, role_assignment_id: UUID) -> RoleAssignment | None: ...

    def list_by_actor(self, actor_id: UUID) -> tuple[RoleAssignment, ...]:
        """Every `RoleAssignment` ever granted to `actor_id`, in
        creation order — used for self-grant/self-approval detection
        (comparing an actor's own existing assignments' `actor_id`
        against a proposed grant's `actor_id`)."""
        ...


class GovernancePolicyStore(Protocol):
    def create(self, policy: GovernancePolicy) -> GovernancePolicy:
        """Create a new policy. Idempotent by content."""
        ...

    def save(self, policy: GovernancePolicy) -> None:
        """Persist a `status` transition (`draft -> active` or
        `active -> superseded`)."""
        ...

    def get(self, governance_policy_id: UUID) -> GovernancePolicy | None: ...

    def get_active_for_policy_type(self, policy_type: str) -> GovernancePolicy | None:
        """Return the currently `active` policy for `policy_type`, or
        `None`. Canon section 19b.2: "не более одной активной версии
        на policy_type одновременно" — the in-memory adapter enforces
        this invariant by construction (see
        `InMemoryGovernancePolicyStore.save`)."""
        ...

    def latest_version_for_policy_type(self, policy_type: str) -> int:
        """The highest `version` ever created for `policy_type`, or `0`
        if none exist yet — used to enforce canon 19b.2's "монотонно
        возрастающее в пределах одного policy_type"."""
        ...


class GovernanceDecisionStore(Protocol):
    def create(self, decision: GovernanceDecision) -> GovernanceDecision:
        """Create a new decision. Idempotent by content."""
        ...

    def save(self, decision: GovernanceDecision) -> None:
        """Persist the one-shot `proposed -> approved` or
        `proposed -> rejected` transition. A `GovernanceDecision` is
        never saved a second time after this (19b.3 immutability)."""
        ...

    def get(self, governance_decision_id: UUID) -> GovernanceDecision | None: ...

    def find_superseding(self, governance_decision_id: UUID) -> GovernanceDecision | None:
        """Return the (at most one, by construction — 19b.5's
        no-contradictory-decisions rule) other, `approved`
        `GovernanceDecision` whose `supersedes_decision_id` equals
        `governance_decision_id`, or `None` if this decision has not
        been superseded. Only `approved` candidates count — a merely
        `proposed` (not yet decided) supersession attempt must never
        make the target look already-superseded before its own
        approval completes. This is the derived "is this decision
        superseded" check (19b.3), never a stored value."""
        ...

    def get_current_result_finality_determination(
        self, result_publication_id: UUID
    ) -> GovernanceDecision | None:
        """The current (non-superseded), `approved`
        `result_finality_determination` decision for
        `result_publication_id`, or `None`. Canon 19b.5: at most one
        may ever exist at a time."""
        ...

    def list_by_decision_type(
        self, decision_type: GovernanceDecisionType
    ) -> tuple[GovernanceDecision, ...]: ...


class TechnicalChallengeStore(Protocol):
    def create(self, challenge: TechnicalChallenge) -> TechnicalChallenge:
        """Create a new challenge. Idempotent by content."""
        ...

    def save(self, challenge: TechnicalChallenge) -> None:
        """Persist a `status` transition."""
        ...

    def get(self, technical_challenge_id: UUID) -> TechnicalChallenge | None: ...

    def list_by_result_publication(
        self, result_publication_id: UUID
    ) -> tuple[TechnicalChallenge, ...]:
        """Every `TechnicalChallenge` ever submitted against
        `result_publication_id`, in creation order — used to enforce
        canon 19b.5's "no finality while any challenge remains
        unresolved" rule."""
        ...

    def has_unresolved_challenges(self, result_publication_id: UUID) -> bool:
        """`True` if any `TechnicalChallenge` for `result_publication_id`
        is currently `submitted` or `under_review`."""
        ...


class InMemoryRoleAssignmentStore:
    def __init__(self) -> None:
        self._assignments: dict[UUID, RoleAssignment] = {}
        self._by_actor: dict[UUID, list[UUID]] = {}

    def create(self, assignment: RoleAssignment) -> RoleAssignment:
        existing = self._assignments.get(assignment.role_assignment_id)
        if existing is not None:
            if existing == assignment:
                return existing
            raise RoleAssignmentConflictError(
                f"role_assignment_id {assignment.role_assignment_id} already exists "
                "with different content"
            )
        self._assignments[assignment.role_assignment_id] = assignment
        self._by_actor.setdefault(assignment.actor_id, []).append(assignment.role_assignment_id)
        return assignment

    def save(self, assignment: RoleAssignment) -> None:
        self._assignments[assignment.role_assignment_id] = assignment

    def get(self, role_assignment_id: UUID) -> RoleAssignment | None:
        return self._assignments.get(role_assignment_id)

    def list_by_actor(self, actor_id: UUID) -> tuple[RoleAssignment, ...]:
        ids = self._by_actor.get(actor_id, [])
        return tuple(self._assignments[i] for i in ids)


class InMemoryGovernancePolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, GovernancePolicy] = {}
        self._active_by_policy_type: dict[str, UUID] = {}
        self._latest_version_by_policy_type: dict[str, int] = {}

    def create(self, policy: GovernancePolicy) -> GovernancePolicy:
        existing = self._policies.get(policy.governance_policy_id)
        if existing is not None:
            if existing == policy:
                return existing
            raise GovernancePolicyConflictError(
                f"governance_policy_id {policy.governance_policy_id} already exists "
                "with different content"
            )
        self._policies[policy.governance_policy_id] = policy
        current = self._latest_version_by_policy_type.get(policy.policy_type.value, 0)
        self._latest_version_by_policy_type[policy.policy_type.value] = max(current, policy.version)
        return policy

    def save(self, policy: GovernancePolicy) -> None:
        self._policies[policy.governance_policy_id] = policy
        if policy.status is GovernancePolicyStatus.ACTIVE:
            self._active_by_policy_type[policy.policy_type.value] = policy.governance_policy_id
        elif (
            self._active_by_policy_type.get(policy.policy_type.value) == policy.governance_policy_id
        ):
            del self._active_by_policy_type[policy.policy_type.value]

    def get(self, governance_policy_id: UUID) -> GovernancePolicy | None:
        return self._policies.get(governance_policy_id)

    def get_active_for_policy_type(self, policy_type: str) -> GovernancePolicy | None:
        policy_id = self._active_by_policy_type.get(policy_type)
        return self._policies.get(policy_id) if policy_id is not None else None

    def latest_version_for_policy_type(self, policy_type: str) -> int:
        return self._latest_version_by_policy_type.get(policy_type, 0)


class InMemoryGovernanceDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[UUID, GovernanceDecision] = {}
        self._by_decision_type: dict[GovernanceDecisionType, list[UUID]] = {}

    def create(self, decision: GovernanceDecision) -> GovernanceDecision:
        existing = self._decisions.get(decision.governance_decision_id)
        if existing is not None:
            if existing == decision:
                return existing
            raise GovernanceDecisionConflictError(
                f"governance_decision_id {decision.governance_decision_id} already exists "
                "with different content"
            )
        self._decisions[decision.governance_decision_id] = decision
        self._by_decision_type.setdefault(decision.decision_type, []).append(
            decision.governance_decision_id
        )
        return decision

    def save(self, decision: GovernanceDecision) -> None:
        self._decisions[decision.governance_decision_id] = decision

    def get(self, governance_decision_id: UUID) -> GovernanceDecision | None:
        return self._decisions.get(governance_decision_id)

    def find_superseding(self, governance_decision_id: UUID) -> GovernanceDecision | None:
        for decision in self._decisions.values():
            if (
                decision.supersedes_decision_id == governance_decision_id
                and decision.status is GovernanceDecisionStatus.APPROVED
            ):
                return decision
        return None

    def get_current_result_finality_determination(
        self, result_publication_id: UUID
    ) -> GovernanceDecision | None:
        candidates = [
            d
            for d in self._decisions.values()
            if d.decision_type is GovernanceDecisionType.RESULT_FINALITY_DETERMINATION
            and d.status is GovernanceDecisionStatus.APPROVED
            and d.subject_reference.get("result_publication_id") == str(result_publication_id)
            and self.find_superseding(d.governance_decision_id) is None
        ]
        if not candidates:
            return None
        # By 19b.5 construction, exactly one non-superseded, approved
        # result_finality_determination can ever exist per publication.
        return candidates[0]

    def list_by_decision_type(
        self, decision_type: GovernanceDecisionType
    ) -> tuple[GovernanceDecision, ...]:
        ids = self._by_decision_type.get(decision_type, [])
        return tuple(self._decisions[i] for i in ids)


class InMemoryTechnicalChallengeStore:
    def __init__(self) -> None:
        self._challenges: dict[UUID, TechnicalChallenge] = {}
        self._by_result_publication: dict[UUID, list[UUID]] = {}

    def create(self, challenge: TechnicalChallenge) -> TechnicalChallenge:
        existing = self._challenges.get(challenge.technical_challenge_id)
        if existing is not None:
            if existing == challenge:
                return existing
            raise TechnicalChallengeConflictError(
                f"technical_challenge_id {challenge.technical_challenge_id} already exists "
                "with different content"
            )
        self._challenges[challenge.technical_challenge_id] = challenge
        self._by_result_publication.setdefault(challenge.result_publication_id, []).append(
            challenge.technical_challenge_id
        )
        return challenge

    def save(self, challenge: TechnicalChallenge) -> None:
        self._challenges[challenge.technical_challenge_id] = challenge

    def get(self, technical_challenge_id: UUID) -> TechnicalChallenge | None:
        return self._challenges.get(technical_challenge_id)

    def list_by_result_publication(
        self, result_publication_id: UUID
    ) -> tuple[TechnicalChallenge, ...]:
        ids = self._by_result_publication.get(result_publication_id, [])
        return tuple(self._challenges[i] for i in ids)

    def has_unresolved_challenges(self, result_publication_id: UUID) -> bool:
        return any(
            c.status in UNRESOLVED_TECHNICAL_CHALLENGE_STATUSES
            for c in self.list_by_result_publication(result_publication_id)
        )

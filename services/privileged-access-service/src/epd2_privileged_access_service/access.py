"""Bounded context 1 of 3 - privileged access management (ADR-062).

The `PrivilegedAccessGrant` lifecycle and the objects around it:

```text
requested -> under_evaluation -> approved | denied -> activated
          -> active -> expired | revoked
          -> under_post_access_review -> review_completed
```

Two construction-time invariants carry most of the weight, and both are
enforced in `__post_init__` rather than by a validation step a caller
could skip:

- **Nine properties, jointly mandatory** (`P12-PAM-002`). A grant is
  purpose-, resource-, operation- and organization-scoped, time-bound,
  attributable, reviewable, revocable and auditable. A grant missing any
  one of them is not constructible. The precedent is PACK-09's
  `GovernedRecord`, which refuses a destroyed record carrying no
  destruction evidence.
- **No standing superuser** (`P12-PAM-003`). `EffectiveWindow` has no
  "no end" option and the policy caps the duration, so an unbounded
  grant cannot be expressed.

Renewal is a new request with a new decision; `renew` deliberately does
not exist. Extension in place would make "time-bound" advisory.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_privileged_access_service.domain import (
    DUAL_CONTROL_RISK_CLASSES,
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RiskClass,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    ApproverCountInsufficientError,
    ForbiddenTransitionError,
    GrantDormantError,
    GrantExpiredError,
    GrantNotActivatedError,
    GrantRevokedError,
    JustificationMissingError,
    OperationNotGrantedError,
    PrivilegeOrganizationMismatchError,
    PrivilegeScopeMismatchError,
    RiskClassificationUndeterminedError,
    SelfApprovalProhibitedError,
    StandingAccessProhibitedError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import PrivilegedAccessPolicy
from epd2_privileged_access_service.roles import (
    OperationalAssignmentRole,
    assert_not_self_approval,
)


class GrantState(StrEnum):
    """The lifecycle states of a privileged access grant."""

    REQUESTED = "requested"
    UNDER_EVALUATION = "under_evaluation"
    APPROVED = "approved"
    DENIED = "denied"
    ACTIVATED = "activated"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNDER_POST_ACCESS_REVIEW = "under_post_access_review"
    REVIEW_COMPLETED = "review_completed"


_ALLOWED_TRANSITIONS: frozenset[tuple[GrantState, GrantState]] = frozenset(
    {
        (GrantState.REQUESTED, GrantState.UNDER_EVALUATION),
        (GrantState.UNDER_EVALUATION, GrantState.APPROVED),
        (GrantState.UNDER_EVALUATION, GrantState.DENIED),
        (GrantState.APPROVED, GrantState.ACTIVATED),
        (GrantState.APPROVED, GrantState.EXPIRED),
        (GrantState.APPROVED, GrantState.REVOKED),
        (GrantState.ACTIVATED, GrantState.ACTIVE),
        (GrantState.ACTIVATED, GrantState.REVOKED),
        (GrantState.ACTIVE, GrantState.EXPIRED),
        (GrantState.ACTIVE, GrantState.REVOKED),
        (GrantState.EXPIRED, GrantState.UNDER_POST_ACCESS_REVIEW),
        (GrantState.REVOKED, GrantState.UNDER_POST_ACCESS_REVIEW),
        (GrantState.UNDER_POST_ACCESS_REVIEW, GrantState.REVIEW_COMPLETED),
    }
)

#: States in which a grant may authorise an operation. Deliberately two,
#: not "anything that is not terminal": a grant that has been approved
#: but never activated authorises nothing.
USABLE_STATES: frozenset[GrantState] = frozenset({GrantState.ACTIVATED, GrantState.ACTIVE})


def resolve_grant_state(value: str) -> GrantState:
    try:
        return GrantState(value)
    except ValueError as exc:
        raise UnknownStatusError(f"unknown privileged grant state {value!r}") from exc


@dataclass(frozen=True, slots=True)
class ResourceScope:
    """What a grant may reach, beyond the organization.

    `domain` names one bounded context or record family;
    `resource_references` optionally narrows to named objects. An empty
    `resource_references` means "the whole domain within the
    organization", which is why `domain` may never be blank."""

    domain: str
    resource_references: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        require_text(self.domain, "domain")

    def admits(self, domain: str, resource_reference: str | None = None) -> bool:
        if domain != self.domain:
            return False
        if not self.resource_references:
            return True
        return resource_reference is not None and resource_reference in self.resource_references

    def assert_admits(self, domain: str, resource_reference: str | None = None) -> None:
        if not self.admits(domain, resource_reference):
            raise PrivilegeScopeMismatchError(
                f"resource {domain}/{resource_reference or '*'} lies outside the grant's scope"
            )

    def to_payload(self) -> dict[str, object]:
        return {"domain": self.domain, "resource_references": sorted(self.resource_references)}


@dataclass(frozen=True, slots=True)
class SeparationOfDutiesEvaluation:
    """The recorded outcome of one separation-of-duties evaluation.

    Two of these exist per grant by design: one at approval and one at
    activation (`P12-PAM-005`), because a subject's role set can change
    in between and activating on the stale evaluation would be acting on
    a fact that is no longer true."""

    evaluation_id: UUID
    evaluated_at: datetime
    subject_reference: str
    held_roles: frozenset[str]
    outcome: str
    stage: str

    def __post_init__(self) -> None:
        require_timezone(self.evaluated_at, context="SeparationOfDutiesEvaluation.evaluated_at")
        require_text(self.subject_reference, "subject_reference")
        if self.stage not in {"approval", "activation"}:
            raise UnknownStatusError(f"unknown evaluation stage {self.stage!r}")
        if self.outcome not in {"passed", "refused"}:
            raise UnknownStatusError(f"unknown evaluation outcome {self.outcome!r}")

    def to_payload(self) -> dict[str, object]:
        return {
            "evaluation_id": str(self.evaluation_id),
            "evaluated_at": self.evaluated_at.isoformat(),
            "held_roles": sorted(self.held_roles),
            "outcome": self.outcome,
            "stage": self.stage,
        }


@dataclass(frozen=True, slots=True)
class GrantHistoryEntry:
    """One append-only entry in a grant's own history."""

    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    actor_reference: str
    state_after: GrantState

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="GrantHistoryEntry.occurred_at")
        require_text(self.action, "action")
        if self.sequence < 1:
            raise StandingAccessProhibitedError("sequence must be a positive integer")

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "action": self.action,
            "reason": self.reason.to_payload(),
            "state_after": str(self.state_after),
        }


@dataclass(frozen=True, slots=True)
class PrivilegedAccessRequest:
    """A request for privileged access.

    Nine mandatory attributes (`P12-PAM-001`); each missing one raises a
    distinct reason code, because "your request was incomplete" is not an
    actionable message."""

    request_id: UUID
    subject_reference: str
    requested_role: OperationalAssignmentRole
    organization_scope: OrganizationalScopeRef
    resource_scope: ResourceScope
    requested_operations: frozenset[str]
    purpose: PurposeBinding
    requested_window: EffectiveWindow
    risk_class: RiskClass
    data_classes: frozenset[str]
    requested_at: datetime

    def __post_init__(self) -> None:
        require_text(self.subject_reference, "subject_reference")
        require_timezone(self.requested_at, context="PrivilegedAccessRequest.requested_at")
        if not self.requested_operations:
            raise OperationNotGrantedError("a request must name at least one operation")
        if not self.data_classes:
            raise RiskClassificationUndeterminedError(
                "a request must name at least one data class so risk can be assessed"
            )
        if not self.purpose.justification_reference.strip():
            raise JustificationMissingError("a request requires a written justification")

    def to_state_payload(self) -> dict[str, object]:
        return {
            "request_id": str(self.request_id),
            "subject_reference": self.subject_reference,
            "requested_role": str(self.requested_role),
            "organization_scope": self.organization_scope.to_payload(),
            "resource_scope": self.resource_scope.to_payload(),
            "requested_operations": sorted(self.requested_operations),
            "purpose": self.purpose.to_payload(),
            "requested_window": self.requested_window.to_payload(),
            "risk_class": str(self.risk_class),
            "data_classes": sorted(self.data_classes),
            "requested_at": self.requested_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class PrivilegedAccessGrant:
    """A governed privileged access grant.

    The nine `P12-PAM-002` properties, in field form: `purpose`,
    `resource_scope`, `permitted_operations`, `organization_scope`,
    `window` (time-bound), `subject_reference` (attributable), `history`
    plus `review_reference` (reviewable), `state` supporting `REVOKED`
    (revocable), and every transition emitting an event (auditable)."""

    grant_id: UUID
    request_id: UUID
    subject_reference: str
    role: OperationalAssignmentRole
    organization_scope: OrganizationalScopeRef
    resource_scope: ResourceScope
    permitted_operations: frozenset[str]
    purpose: PurposeBinding
    window: EffectiveWindow
    risk_class: RiskClass
    policy_version: str
    approvers: tuple[str, ...]
    state: GrantState = GrantState.REQUESTED
    activated_at: datetime | None = None
    last_used_at: datetime | None = None
    approval_evaluation: SeparationOfDutiesEvaluation | None = None
    activation_evaluation: SeparationOfDutiesEvaluation | None = None
    review_reference: str | None = None
    history: tuple[GrantHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.subject_reference, "subject_reference")
        require_text(self.policy_version, "policy_version")
        if not self.permitted_operations:
            raise OperationNotGrantedError("a grant must name at least one permitted operation")
        if self.subject_reference in self.approvers:
            raise SelfApprovalProhibitedError(
                "the grant subject may not appear among its own approvers"
            )
        if len(set(self.approvers)) != len(self.approvers):
            raise ApproverCountInsufficientError("approvers must be distinct subjects")
        if self.activated_at is not None:
            require_timezone(self.activated_at, context="PrivilegedAccessGrant.activated_at")
        if self.last_used_at is not None:
            require_timezone(self.last_used_at, context="PrivilegedAccessGrant.last_used_at")

    # -- lifecycle ---------------------------------------------------------

    def _next_sequence(self) -> int:
        return len(self.history) + 1

    def with_state(
        self,
        target: GrantState,
        *,
        at: datetime,
        action: str,
        reason: ReasonCoded,
        actor_reference: str,
    ) -> PrivilegedAccessGrant:
        if (self.state, target) not in _ALLOWED_TRANSITIONS:
            raise ForbiddenTransitionError(
                f"invalid privileged grant transition {self.state.value} -> {target.value}"
            )
        entry = GrantHistoryEntry(
            sequence=self._next_sequence(),
            occurred_at=at,
            action=action,
            reason=reason,
            actor_reference=actor_reference,
            state_after=target,
        )
        activated = self.activated_at
        if target is GrantState.ACTIVATED:
            activated = at
        return replace(self, state=target, activated_at=activated, history=(*self.history, entry))

    def with_evaluation(self, evaluation: SeparationOfDutiesEvaluation) -> PrivilegedAccessGrant:
        if evaluation.stage == "approval":
            return replace(self, approval_evaluation=evaluation)
        return replace(self, activation_evaluation=evaluation)

    def with_use(self, at: datetime) -> PrivilegedAccessGrant:
        require_timezone(at, context="PrivilegedAccessGrant.with_use")
        return replace(self, last_used_at=at)

    def with_review(self, reference: str) -> PrivilegedAccessGrant:
        return replace(self, review_reference=require_text(reference, "review_reference"))

    # -- authorization -----------------------------------------------------

    def assert_usable(
        self,
        *,
        at: datetime,
        policy: PrivilegedAccessPolicy,
        operation: str,
        domain: str,
        resource_reference: str | None,
        scope: OrganizationalScopeRef,
        purpose: Purpose,
    ) -> None:
        """Re-check every dimension at the moment of the act
        (`P12-PAM-010`).

        Order matters and is fixed: revocation, then state, then time,
        then dormancy, then organization, then resource, then operation,
        then purpose. A revoked grant must report revocation, not
        expiry - the two mean different things to an operator."""
        require_timezone(at, context="PrivilegedAccessGrant.assert_usable")
        if self.state is GrantState.REVOKED:
            raise GrantRevokedError("the grant was revoked")
        if self.state is GrantState.EXPIRED:
            raise GrantExpiredError("the grant has expired")
        if self.state not in USABLE_STATES:
            raise GrantNotActivatedError(
                f"a grant in state {self.state.value} authorises no operation"
            )
        if not self.window.covers(at):
            raise GrantExpiredError("the grant's effective window does not cover this instant")
        if self.last_used_at is not None and at - self.last_used_at > policy.dormancy_interval:
            raise GrantDormantError(
                "the grant has been dormant past the policy interval and requires review"
            )
        if scope.organization_id != self.organization_scope.organization_id:
            raise PrivilegeOrganizationMismatchError(
                "the grant belongs to a different organization"
            )
        self.resource_scope.assert_admits(domain, resource_reference)
        if operation not in self.permitted_operations:
            raise OperationNotGrantedError(
                f"operation {operation!r} is outside the grant's operation set"
            )
        self.purpose.assert_admits(purpose)

    def requires_dual_control(self) -> bool:
        return self.risk_class in DUAL_CONTROL_RISK_CLASSES

    def to_state_payload(self) -> dict[str, object]:
        return {
            "grant_id": str(self.grant_id),
            "request_id": str(self.request_id),
            "subject_reference": self.subject_reference,
            "role": str(self.role),
            "organization_scope": self.organization_scope.to_payload(),
            "resource_scope": self.resource_scope.to_payload(),
            "permitted_operations": sorted(self.permitted_operations),
            "purpose": self.purpose.to_payload(),
            "window": self.window.to_payload(),
            "risk_class": str(self.risk_class),
            "policy_version": self.policy_version,
            "approvers": list(self.approvers),
            "state": str(self.state),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "approval_evaluation": (
                self.approval_evaluation.to_payload() if self.approval_evaluation else None
            ),
            "activation_evaluation": (
                self.activation_evaluation.to_payload() if self.activation_evaluation else None
            ),
            "review_reference": self.review_reference,
            "history": [entry.to_payload() for entry in self.history],
        }


def assert_approver_set_sufficient(
    approvers: tuple[str, ...],
    *,
    requester_reference: str,
    risk_class: RiskClass,
    policy: PrivilegedAccessPolicy,
) -> None:
    """Raise unless the approver set satisfies the risk class and
    contains neither the requester nor a duplicate."""
    for approver in approvers:
        assert_not_self_approval(requester_reference, approver, action="approve_privileged_access")
    required = policy.required_approvers(risk_class)
    distinct = set(approvers)
    if len(distinct) < required:
        raise ApproverCountInsufficientError(
            f"risk class {risk_class!s} requires {required} distinct approvers, got {len(distinct)}"
        )


@dataclass(frozen=True, slots=True)
class PrivilegedAccessReview:
    """A periodic or post-access review outcome (`P12-PAM-008`)."""

    review_id: UUID
    grant_id: UUID
    organization_scope: OrganizationalScopeRef
    review_kind: str
    reviewer_reference: str
    reviewed_at: datetime
    outcome: str
    reason: ReasonCoded
    findings_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.reviewed_at, context="PrivilegedAccessReview.reviewed_at")
        require_text(self.reviewer_reference, "reviewer_reference")
        if self.review_kind not in {"periodic", "post_access"}:
            raise UnknownStatusError(f"unknown review kind {self.review_kind!r}")
        if self.outcome not in {"accepted", "revoke_recommended", "findings_raised"}:
            raise UnknownStatusError(f"unknown review outcome {self.outcome!r}")

    def to_state_payload(self) -> dict[str, object]:
        return {
            "review_id": str(self.review_id),
            "grant_id": str(self.grant_id),
            "organization_scope": self.organization_scope.to_payload(),
            "review_kind": self.review_kind,
            "reviewer_reference": self.reviewer_reference,
            "reviewed_at": self.reviewed_at.isoformat(),
            "outcome": self.outcome,
            "reason": self.reason.to_payload(),
            "findings_reference": self.findings_reference,
        }

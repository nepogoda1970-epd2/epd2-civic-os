"""Emergency access - a separate, dual-controlled, notified workflow
(ADR-063).

Break-glass is deliberately **not** a flag on the ordinary grant. It has
its own request object, its own decision, its own state machine and its
own event family, because a bypass that is a field on the normal path
becomes the cheapest route through it (`P12-BG-001`).

Five properties are the ones an implementation is most likely to soften,
so each is enforced structurally here rather than by convention:

- a documented emergency condition is required (`P12-BG-002`);
- the activator and the approver must differ (`P12-BG-003`);
- the notification is not suppressible by the activator or by anyone
  that actor can direct (`P12-BG-007`);
- an undelivered notification escalates and never silently completes
  (`P12-BG-008`);
- renewal is a new dual-controlled decision, so there is no `extend`
  method (`P12-BG-013`).

Nothing here reaches ballot-level or uncertified tally material
(`P12-BG-010`), disables audit (`P12-BG-011`) or suspends a hard
invariant (`P12-BG-009`). Those are not checks that could pass or fail:
this package defines no type capable of expressing them.

The notification **transport** belongs to the later gateway and incident
packs. What is fixed now is the port, the obligation and the evidence;
`NotificationPort` below is that port, and the reference adapter in
`storage` is deterministic and local. Nothing here claims that a
notification is delivered in a production environment.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_privileged_access_service.domain import (
    EffectiveWindow,
    OrganizationalScopeRef,
    PurposeBinding,
    ReasonCoded,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    BreakGlassConditionAbsentError,
    BreakGlassDualControlMissingError,
    BreakGlassNotificationUndeliveredError,
    BreakGlassRenewalRequiresDecisionError,
    BreakGlassScopeTooBroadError,
    ForbiddenTransitionError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import PrivilegedAccessPolicy
from epd2_privileged_access_service.roles import assert_distinct_reviewer


class BreakGlassState(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    ACTIVATED = "activated"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNDER_INDEPENDENT_REVIEW = "under_independent_review"
    REVIEW_COMPLETED = "review_completed"
    ESCALATED = "escalated"


_ALLOWED_TRANSITIONS: frozenset[tuple[BreakGlassState, BreakGlassState]] = frozenset(
    {
        (BreakGlassState.REQUESTED, BreakGlassState.APPROVED),
        (BreakGlassState.REQUESTED, BreakGlassState.DENIED),
        (BreakGlassState.APPROVED, BreakGlassState.ACTIVATED),
        (BreakGlassState.APPROVED, BreakGlassState.ESCALATED),
        (BreakGlassState.ACTIVATED, BreakGlassState.EXPIRED),
        (BreakGlassState.ACTIVATED, BreakGlassState.REVOKED),
        (BreakGlassState.ACTIVATED, BreakGlassState.ESCALATED),
        (BreakGlassState.EXPIRED, BreakGlassState.UNDER_INDEPENDENT_REVIEW),
        (BreakGlassState.REVOKED, BreakGlassState.UNDER_INDEPENDENT_REVIEW),
        (BreakGlassState.ESCALATED, BreakGlassState.UNDER_INDEPENDENT_REVIEW),
        (BreakGlassState.UNDER_INDEPENDENT_REVIEW, BreakGlassState.REVIEW_COMPLETED),
    }
)


def resolve_break_glass_state(value: str) -> BreakGlassState:
    try:
        return BreakGlassState(value)
    except ValueError as exc:
        raise UnknownStatusError(f"unknown break-glass state {value!r}") from exc


@dataclass(frozen=True, slots=True)
class EmergencyCondition:
    """The documented emergency a break-glass activation rests on.

    A reference plus a classification, never free prose: `P12-BG-002`
    requires the condition to be documented, and a text field nobody can
    resolve is not documentation."""

    condition_reference: str
    condition_class: str
    declared_at: datetime
    declared_by: str

    def __post_init__(self) -> None:
        if not self.condition_reference or not self.condition_reference.strip():
            raise BreakGlassConditionAbsentError(
                "a break-glass activation requires a documented emergency condition reference"
            )
        require_text(self.condition_class, "condition_class")
        require_text(self.declared_by, "declared_by")
        require_timezone(self.declared_at, context="EmergencyCondition.declared_at")

    def to_payload(self) -> dict[str, object]:
        return {
            "condition_reference": self.condition_reference,
            "condition_class": self.condition_class,
            "declared_at": self.declared_at.isoformat(),
        }


class NotificationPort(Protocol):
    """The out-of-band notification boundary (`P12-BG-008`).

    The transport is the later gateway and incident packs'; this port is
    the obligation PACK-12 fixes now so those packs inherit a contract
    rather than a blank space.

    `dispatch` returns the outcome rather than raising, because a failed
    dispatch is a governed fact that must be recorded and escalated - not
    an exception that could be swallowed by a caller's error handling."""

    def dispatch(
        self,
        *,
        activation_id: UUID,
        organization_scope: OrganizationalScopeRef,
        recipient_class: str,
        activator_reference: str,
    ) -> NotificationOutcome: ...


@dataclass(frozen=True, slots=True)
class NotificationOutcome:
    """What a dispatch attempt produced.

    `suppressed_by` exists so that an attempt to suppress is *recorded*
    rather than silently effective; `assert_not_suppressed_by_activator`
    then refuses it (`P12-BG-007`)."""

    delivered: bool
    dispatch_reference: str
    recipient_class: str
    failure_reason: str | None = None
    suppressed_by: str | None = None

    def __post_init__(self) -> None:
        require_text(self.dispatch_reference, "dispatch_reference")
        require_text(self.recipient_class, "recipient_class")
        if not self.delivered and not self.failure_reason:
            raise BreakGlassNotificationUndeliveredError(
                "an undelivered notification must carry its failure reason"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "delivered": self.delivered,
            "dispatch_reference": self.dispatch_reference,
            "recipient_class": self.recipient_class,
            "failure_reason": self.failure_reason,
            "suppressed_by": self.suppressed_by,
        }


def assert_notification_not_suppressed(
    outcome: NotificationOutcome, *, activator_reference: str, directed_subjects: frozenset[str]
) -> None:
    """Raise if the activator, or anyone that actor can direct,
    suppressed the notification (`P12-BG-007`).

    The second clause is the load-bearing one: an activator who also
    administers the notification channel has suppressed it without ever
    touching a suppression control, so the check covers subjects the
    activator directs, not only the activator."""
    if outcome.suppressed_by is None:
        return
    if outcome.suppressed_by == activator_reference or outcome.suppressed_by in directed_subjects:
        raise BreakGlassNotificationUndeliveredError(
            "the out-of-band notification was suppressed by the activator or a subject they "
            "direct; the activation is refused and escalated"
        )


@dataclass(frozen=True, slots=True)
class BreakGlassHistoryEntry:
    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    actor_reference: str
    state_after: BreakGlassState

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="BreakGlassHistoryEntry.occurred_at")
        require_text(self.action, "action")

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "action": self.action,
            "reason": self.reason.to_payload(),
            "state_after": str(self.state_after),
        }


@dataclass(frozen=True, slots=True)
class BreakGlassActivation:
    """One governed emergency access activation.

    `justification_reference` is immutable after construction
    (`P12-BG-012`): there is no method that replaces it, and later
    clarification is an appended history entry."""

    activation_id: UUID
    organization_scope: OrganizationalScopeRef
    activator_reference: str
    approver_reference: str
    condition: EmergencyCondition
    purpose: PurposeBinding
    resource_domain: str
    permitted_operations: frozenset[str]
    window: EffectiveWindow
    policy_version: str
    state: BreakGlassState = BreakGlassState.REQUESTED
    notification: NotificationOutcome | None = None
    session_reference: UUID | None = None
    independent_review_reference: str | None = None
    history: tuple[BreakGlassHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.activator_reference, "activator_reference")
        require_text(self.resource_domain, "resource_domain")
        require_text(self.policy_version, "policy_version")
        if not self.approver_reference or not self.approver_reference.strip():
            raise BreakGlassDualControlMissingError(
                "a break-glass activation requires a distinct approver"
            )
        if self.approver_reference == self.activator_reference:
            raise BreakGlassDualControlMissingError(
                "the activator and the approver of a break-glass must be different subjects"
            )
        if not self.permitted_operations:
            raise BreakGlassScopeTooBroadError(
                "a break-glass activation must name its permitted operations explicitly"
            )

    def _next_sequence(self) -> int:
        return len(self.history) + 1

    def with_state(
        self,
        target: BreakGlassState,
        *,
        at: datetime,
        action: str,
        reason: ReasonCoded,
        actor_reference: str,
    ) -> BreakGlassActivation:
        if (self.state, target) not in _ALLOWED_TRANSITIONS:
            raise ForbiddenTransitionError(
                f"invalid break-glass transition {self.state.value} -> {target.value}"
            )
        entry = BreakGlassHistoryEntry(
            sequence=self._next_sequence(),
            occurred_at=at,
            action=action,
            reason=reason,
            actor_reference=actor_reference,
            state_after=target,
        )
        return replace(self, state=target, history=(*self.history, entry))

    def with_notification(self, outcome: NotificationOutcome) -> BreakGlassActivation:
        return replace(self, notification=outcome)

    def with_session(self, session_id: UUID) -> BreakGlassActivation:
        return replace(self, session_reference=session_id)

    def with_independent_review(self, reference: str) -> BreakGlassActivation:
        return replace(
            self, independent_review_reference=require_text(reference, "review reference")
        )

    def assert_scope_narrow(self, policy: PrivilegedAccessPolicy) -> None:
        """Raise if the emergency scope exceeds what the policy permits
        (`P12-BG-004`)."""
        policy.assert_break_glass_duration_allowed(self.window.duration)
        if "*" in self.permitted_operations or "all" in self.permitted_operations:
            raise BreakGlassScopeTooBroadError(
                "a break-glass activation may not request a wildcard operation set"
            )

    def to_state_payload(self) -> dict[str, object]:
        return {
            "activation_id": str(self.activation_id),
            "organization_scope": self.organization_scope.to_payload(),
            "activator_reference": self.activator_reference,
            "approver_reference": self.approver_reference,
            "condition": self.condition.to_payload(),
            "purpose": self.purpose.to_payload(),
            "resource_domain": self.resource_domain,
            "permitted_operations": sorted(self.permitted_operations),
            "window": self.window.to_payload(),
            "policy_version": self.policy_version,
            "state": str(self.state),
            "notification": self.notification.to_payload() if self.notification else None,
            "session_reference": str(self.session_reference) if self.session_reference else None,
            "independent_review_reference": self.independent_review_reference,
            "history": [entry.to_payload() for entry in self.history],
        }


def assert_renewal_is_new_decision(previous: BreakGlassActivation, proposed_id: UUID) -> None:
    """Raise if a caller tries to extend an activation in place.

    There is no `extend` method on `BreakGlassActivation`; this function
    exists so that a caller reaching for one gets the reason code rather
    than an `AttributeError` (`P12-BG-013`)."""
    if proposed_id == previous.activation_id:
        raise BreakGlassRenewalRequiresDecisionError(
            "break-glass renewal is a new dual-controlled decision with a new activation, "
            "never an extension of the existing one"
        )


@dataclass(frozen=True, slots=True)
class BreakGlassIndependentReview:
    """The mandatory post-hoc review (`P12-BG-014`)."""

    review_id: UUID
    activation_id: UUID
    organization_scope: OrganizationalScopeRef
    reviewer_reference: str
    reviewed_at: datetime
    outcome: str
    reason: ReasonCoded
    findings_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.reviewed_at, context="BreakGlassIndependentReview.reviewed_at")
        require_text(self.reviewer_reference, "reviewer_reference")
        if self.outcome not in {"justified", "unjustified", "findings_raised"}:
            raise UnknownStatusError(f"unknown break-glass review outcome {self.outcome!r}")

    def assert_reviewer_independent(self, activation: BreakGlassActivation) -> None:
        assert_distinct_reviewer(
            self.reviewer_reference,
            activator=activation.activator_reference,
            approver=activation.approver_reference,
        )

    def to_state_payload(self) -> dict[str, object]:
        return {
            "review_id": str(self.review_id),
            "activation_id": str(self.activation_id),
            "organization_scope": self.organization_scope.to_payload(),
            "reviewer_reference": self.reviewer_reference,
            "reviewed_at": self.reviewed_at.isoformat(),
            "outcome": self.outcome,
            "reason": self.reason.to_payload(),
            "findings_reference": self.findings_reference,
        }

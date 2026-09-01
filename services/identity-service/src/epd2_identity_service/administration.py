"""Privileged identity administration - boundaries, not a mechanism.

**PACK-14 defines no new privileged mechanism and no universal identity
console.** PACK-12's `privileged-access-service` already owns JIT grants,
break-glass, separation of duties and audit-before-event; this module is
the identity domain's read of that model: which of ADR-087's six roles
may do what here, and which combinations are refused.

Because a cross-service import is forbidden
(`tests/repository/test_service_boundaries.py`), the PACK-12 grant
arrives as a **value object** the caller carries in - `PrivilegedGrantRef`
- rather than as a call into that service. The grant is verified there
and presented here; this module checks that one is present, current,
scoped to the right purpose, and held by an actor who is permitted to
act on this case.

Two refusals carry most of the weight:

- **A Support Agent cannot change an account owner or complete a
  recovery alone.** Support impersonation is a first-class threat.
- **A System Admin has no automatic identity content access.** Operating
  the system is not reading the people in it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from epd2_identity_service.exceptions import (
    BreakGlassJustificationMissingError,
    IdentityAdministrationPermissionDeniedError,
    PrivilegedApprovalMissingError,
    SeparationOfDutiesViolatedError,
    SupportActionNotPermittedError,
    SystemAdminIdentityAccessRefusedError,
    UnknownPrivilegedRoleError,
)
from epd2_identity_service.identifiers import ScopedIdentityReference, require_timezone


class IdentityAdminRole(StrEnum):
    """ADR-087's six roles, and no seventh."""

    SECURITY_ADMIN = "security_admin"
    SYSTEM_ADMIN = "system_admin"
    SUPPORT_AGENT = "support_agent"
    RECOVERY_REVIEWER = "recovery_reviewer"
    IDENTITY_PROOFING_REVIEWER = "identity_proofing_reviewer"
    AUDITOR = "auditor"


def parse_admin_role(value: str) -> IdentityAdminRole:
    try:
        return IdentityAdminRole(value)
    except ValueError as exc:
        raise UnknownPrivilegedRoleError(
            f"unknown identity administration role: {value!r}"
        ) from exc


class AdminAction(StrEnum):
    """The privileged acts this domain exposes at all.

    There is no `read_any_account`, no `export_all_identities` and no
    `impersonate` member - the universal identity console PACK-14
    explicitly does not create.
    """

    APPLY_RESTRICTION = "apply_restriction"
    LIFT_RESTRICTION = "lift_restriction"
    APPLY_LOCK = "apply_lock"
    RELEASE_LOCK = "release_lock"
    REVOKE_CREDENTIAL = "revoke_credential"
    REVIEW_SUSPICIOUS_ACTIVITY = "review_suspicious_activity"
    REVIEW_RECOVERY = "review_recovery"
    APPROVE_RECOVERY = "approve_recovery"
    REVIEW_IDENTITY_PROOFING = "review_identity_proofing"
    READ_IDENTITY_CONTENT = "read_identity_content"
    READ_AUDIT_TRAIL = "read_audit_trail"
    BREAK_GLASS = "break_glass"


#: Which role may perform which act. Deliberately explicit rather than
#: hierarchical: a hierarchy makes Security Admin a superset of Support
#: Agent, which is precisely how "support can do anything support's
#: manager can do" gets built.
ROLE_PERMISSIONS: dict[IdentityAdminRole, frozenset[AdminAction]] = {
    IdentityAdminRole.SECURITY_ADMIN: frozenset(
        {
            AdminAction.APPLY_RESTRICTION,
            AdminAction.LIFT_RESTRICTION,
            AdminAction.APPLY_LOCK,
            AdminAction.RELEASE_LOCK,
            AdminAction.REVOKE_CREDENTIAL,
            AdminAction.REVIEW_SUSPICIOUS_ACTIVITY,
            AdminAction.BREAK_GLASS,
        }
    ),
    #: No identity content, and no recovery approval. A System Admin
    #: keeps the system running.
    IdentityAdminRole.SYSTEM_ADMIN: frozenset({AdminAction.REVIEW_SUSPICIOUS_ACTIVITY}),
    #: Support may look at a case and prepare it. It may not decide one,
    #: and it may not touch a credential or an owner.
    IdentityAdminRole.SUPPORT_AGENT: frozenset(
        {AdminAction.REVIEW_RECOVERY, AdminAction.REVIEW_SUSPICIOUS_ACTIVITY}
    ),
    IdentityAdminRole.RECOVERY_REVIEWER: frozenset(
        {AdminAction.REVIEW_RECOVERY, AdminAction.APPROVE_RECOVERY}
    ),
    IdentityAdminRole.IDENTITY_PROOFING_REVIEWER: frozenset(
        {AdminAction.REVIEW_IDENTITY_PROOFING, AdminAction.READ_IDENTITY_CONTENT}
    ),
    #: Read-only, and deliberately unable to act on anything it reads.
    IdentityAdminRole.AUDITOR: frozenset({AdminAction.READ_AUDIT_TRAIL}),
}

#: Acts a Support Agent may never perform, named individually so the
#: refusal message can say which one was attempted.
SUPPORT_PROHIBITED: frozenset[AdminAction] = frozenset(
    {
        AdminAction.APPROVE_RECOVERY,
        AdminAction.REVOKE_CREDENTIAL,
        AdminAction.APPLY_RESTRICTION,
        AdminAction.LIFT_RESTRICTION,
        AdminAction.READ_IDENTITY_CONTENT,
        AdminAction.BREAK_GLASS,
    }
)


@dataclass(frozen=True, slots=True)
class PrivilegedGrantRef:
    """A PACK-12 grant, as this domain receives it.

    A value object, not a call: the grant is issued, approved and audited
    by `privileged-access-service`, and this module verifies only that
    the caller presents one that is current and purpose-scoped. Building
    a second grant mechanism here is exactly the "parallel privileged
    model" PACK-14 is forbidden to create.
    """

    grant_reference: str
    role: IdentityAdminRole
    purpose: str
    granted_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.granted_at, "granted_at")
        require_timezone(self.expires_at, "expires_at")
        if not self.grant_reference:
            raise PrivilegedApprovalMissingError("a grant reference must not be empty")
        if self.expires_at <= self.granted_at:
            raise PrivilegedApprovalMissingError("a JIT grant expires after it is granted")

    def assert_current(self, now: datetime, *, purpose: str) -> None:
        if require_timezone(now, "now") >= self.expires_at:
            raise PrivilegedApprovalMissingError("the privileged grant has expired")
        if self.purpose != purpose:
            raise PrivilegedApprovalMissingError(
                f"the grant is scoped to {self.purpose!r}, not {purpose!r}"
            )


@dataclass(frozen=True, slots=True)
class BreakGlassInvocation:
    """Break-glass, with the two things it is always missing when it goes
    wrong: a justification and a second actor."""

    justification: str
    second_actor_reference: ScopedIdentityReference | None
    invoked_at: datetime
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.invoked_at, "invoked_at")
        if not self.justification or self.second_actor_reference is None:
            raise BreakGlassJustificationMissingError(
                "break-glass requires a written justification and a second actor"
            )
        if not self.reason_code:
            raise BreakGlassJustificationMissingError(
                "break-glass carries a registered reason code"
            )


def assert_role_permits(role: IdentityAdminRole, action: AdminAction) -> None:
    """The role table, plus the two named refusals.

    Support and System Admin get their own exception types rather than a
    generic permission error, because both are threats the threat model
    names and an audit trail that says only "permission denied" cannot
    show how often either was attempted.
    """
    if role is IdentityAdminRole.SUPPORT_AGENT and action in SUPPORT_PROHIBITED:
        raise SupportActionNotPermittedError(
            f"a Support Agent may not perform {action.value}; "
            "support impersonation is a first-class threat"
        )
    if role is IdentityAdminRole.SYSTEM_ADMIN and action is AdminAction.READ_IDENTITY_CONTENT:
        raise SystemAdminIdentityAccessRefusedError(
            "a System Admin has no automatic identity content access"
        )
    if action not in ROLE_PERMISSIONS[role]:
        raise IdentityAdministrationPermissionDeniedError(
            f"{role.value} may not perform {action.value}"
        )


def assert_separation_of_duties(
    *,
    actor_reference: ScopedIdentityReference,
    case_initiator_reference: ScopedIdentityReference | None,
    case_subject_reference: ScopedIdentityReference | None,
) -> None:
    """No reviewer approves their own action, and none decides their own
    case."""
    if case_initiator_reference is not None and actor_reference == case_initiator_reference:
        raise SeparationOfDutiesViolatedError("the actor initiated this case and may not decide it")
    if case_subject_reference is not None and actor_reference == case_subject_reference:
        raise SeparationOfDutiesViolatedError("the actor is the subject of this case")


def authorize_privileged_action(
    *,
    role: IdentityAdminRole,
    action: AdminAction,
    grant: PrivilegedGrantRef | None,
    actor_reference: ScopedIdentityReference,
    case_initiator_reference: ScopedIdentityReference | None,
    case_subject_reference: ScopedIdentityReference | None,
    now: datetime,
    audit_available: bool,
    break_glass: BreakGlassInvocation | None = None,
) -> None:
    """The single gate every privileged identity act passes.

    `audit_available` is checked **first**. Workflow matrix §4: when
    audit is unavailable, consequential operations refuse - there is no
    unlogged privileged act, and checking it last would mean the
    authorization work happened before the refusal, which is exactly how
    a "just this once" bypass gets added later.
    """
    if not audit_available:
        from epd2_identity_service.exceptions import AuditUnavailableError

        raise AuditUnavailableError(
            "the audit path is unavailable; no privileged identity act proceeds unlogged"
        )
    assert_role_permits(role, action)
    if action is AdminAction.BREAK_GLASS and break_glass is None:
        raise BreakGlassJustificationMissingError(
            "break-glass requires a justification and a second actor"
        )
    if grant is None:
        raise PrivilegedApprovalMissingError(
            f"{action.value} requires a current PACK-12 grant and none was presented"
        )
    grant.assert_current(now, purpose=action.value)
    if grant.role is not role:
        raise PrivilegedApprovalMissingError(
            f"the grant is issued for {grant.role.value}, not {role.value}"
        )
    assert_separation_of_duties(
        actor_reference=actor_reference,
        case_initiator_reference=case_initiator_reference,
        case_subject_reference=case_subject_reference,
    )


def refuse_owner_change_by_support(role: IdentityAdminRole) -> None:
    """ "Support cannot change owner", as a call site. Always raises for a
    Support Agent, and refuses the operation outright for everyone else -
    because there is no account-owner-change operation in this domain at
    all: an account has no owner field to change, only credentials to
    enroll and revoke through the governed paths."""
    if role is IdentityAdminRole.SUPPORT_AGENT:
        raise SupportActionNotPermittedError("a Support Agent may not change an account's owner")
    raise IdentityAdministrationPermissionDeniedError(
        "there is no account-owner-change operation; access changes through credential "
        "enrollment and the governed recovery workflow"
    )

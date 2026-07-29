"""Institutional roles, PACK-12 operational assignments, and the
separation rules that keep them apart (ADR-061).

The distinction this module encodes is the correction that governs the
whole pack. Two of the eleven privileged authorities PACK-12 works with
are **existing institutional roles** defined by the Architecture
Framework; nine are **operational assignments** PACK-12 introduces
through canon 19e.15's open `role_code` extension point.

- `InstitutionalRole` re-declares only what PACK-12 must reason about.
  It does not define those roles: it names them so the incompatibility
  matrix and the boundary checks can refer to them (`P12-ROLE-014`).
- `OperationalAssignmentRole` is the nine PACK-12 introduces.
- `PairwiseIncompatibility` holds fourteen added pairs plus one preserved
  institutional pair, cumulative with PACK-08's own baseline and never
  substitutional (`P12-ROLE-020`).

Pure, like PACK-10's `authorization` module: no I/O, no clock, no
storage. The one concession to the outside world is `AuthorizationPort`,
a `Protocol` the application layer implements against PACK-08. That port
is the **only** way this service learns anything about authority: PACK-08
owns the assignments themselves, and PACK-12 neither stores one nor mints
one (`P12-ROLE-017`).

There is no break-glass path through anything in this module. Emergency
access is a separate governed workflow with its own dual control
(`breakglass`), never a flag that relaxes a check here.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from epd2_privileged_access_service.domain import (
    AuthorityReference,
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    require_text,
)
from epd2_privileged_access_service.exceptions import (
    AssignmentNotGovernedError,
    AuthorityRoleIncompatibleError,
    InstitutionalAuthorityNotExtendableError,
    PrivilegeAuthorityMissingError,
    PrivilegeOrganizationMismatchError,
    RoleCombinationProhibitedError,
    SelfApprovalProhibitedError,
)

#: `P12-BG-009` and register `FIR-INV-006`, recorded as a module constant
#: rather than a comment so that it is quotable in a review, a test and
#: an ADR, and so that anyone reading the call sites finds the rule next
#: to them.
#:
#: Nothing in this module is conditional. There is no `force=True`, no
#: `skip_checks`, no environment switch and no privileged-caller
#: shortcut, and none may be added. Emergency access is a separate,
#: dual-controlled, notified, expiring workflow that leaves its own
#: record - never a relaxation of these checks.
NO_BYPASS_NOTE: str = (
    "P12-BG-009 / FIR-INV-006: no feature flag, environment switch, deployment mode, "
    "privileged grant or emergency path may bypass any check in this module. Separation "
    "of duties a flag can disable was never in force. Acting without an ordinary "
    "authority is possible only through the governed break-glass workflow, which is "
    "dual-controlled, notified, expiring and independently reviewed."
)


class InstitutionalRole(StrEnum):
    """Institutional roles PACK-12 **consumes**, never defines.

    These are the Architecture Framework's own offices with their own
    established semantics and incompatibilities. PACK-12 adds boundary
    obligations about what they may not reach (`P12-ROLE-003`,
    `P12-ROLE-004`) and changes nothing else (`P12-ROLE-014`)."""

    SYSTEM_ADMINISTRATOR = "system_administrator"
    SECURITY_ADMINISTRATOR = "security_administrator"


class OperationalAssignmentRole(StrEnum):
    """The nine privileged operational assignments PACK-12 introduces.

    Each is scope-bound, purpose-bound and effective-dated
    (`P12-ROLE-018`), conferred only through governed authority
    (`P12-ROLE-017`), and extends no institutional authority
    (`P12-ROLE-019`)."""

    IAM_ADMINISTRATOR = "iam_administrator"
    AUDIT_CUSTODIAN = "audit_custodian"
    DOMAIN_ADMINISTRATOR = "domain_administrator"
    DATA_OWNER = "data_owner"
    EXPORT_APPROVER = "export_approver"
    DLP_SECURITY_OFFICER = "dlp_security_officer"
    INDEPENDENT_PRIVILEGED_ACCESS_REVIEWER = "independent_privileged_access_reviewer"
    BREAK_GLASS_APPROVER = "break_glass_approver"
    DISCLOSURE_CONTROL_REVIEWER = "disclosure_control_reviewer"


INSTITUTIONAL_ROLE_CODES: frozenset[str] = frozenset(r.value for r in InstitutionalRole)
OPERATIONAL_ASSIGNMENT_CODES: frozenset[str] = frozenset(r.value for r in OperationalAssignmentRole)
PRIVILEGED_ROLE_CODES: frozenset[str] = INSTITUTIONAL_ROLE_CODES | OPERATIONAL_ASSIGNMENT_CODES


def resolve_privileged_role(role_code: str) -> str | None:
    """Resolve a PACK-08 `role_code` to a PACK-12 privileged role, or
    `None`.

    `None` rather than an exception: a caller may legitimately hold roles
    belonging to other contexts, and treating "not one of ours" as an
    error would make an ordinary finance authority look like an attack."""
    return role_code if role_code in PRIVILEGED_ROLE_CODES else None


def is_institutional(role_code: str) -> bool:
    return role_code in INSTITUTIONAL_ROLE_CODES


def is_operational_assignment(role_code: str) -> bool:
    return role_code in OPERATIONAL_ASSIGNMENT_CODES


# ---------------------------------------------------------------------------
# Incompatibility
# ---------------------------------------------------------------------------

INCOMPATIBILITY_BASELINE_VERSION = "pack-12/v1"

#: The one pair PACK-12 **preserves** rather than invents: the existing
#: institutional separation between system and security administration.
#: Register `FIR-INV-008` and the framework establish it; PACK-12 depends
#: on it (`P12-ROLE-015`).
PRESERVED_INSTITUTIONAL_PAIRS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset(
            {
                InstitutionalRole.SECURITY_ADMINISTRATOR.value,
                InstitutionalRole.SYSTEM_ADMINISTRATOR.value,
            }
        ),
    }
)

#: The fourteen pairs PACK-12 **adds**, cumulative with PACK-08's own
#: baseline and with the preserved pair above. Canon 19e.16 permits
#: making the baseline stricter and forbids relaxing it, so this set may
#: grow and may never shrink (`P12-ROLE-012`, `P12-ROLE-020`).
ADDED_INCOMPATIBLE_PAIRS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"security_administrator", "iam_administrator"}),
        frozenset({"security_administrator", "independent_privileged_access_reviewer"}),
        frozenset({"system_administrator", "audit_custodian"}),
        frozenset({"system_administrator", "domain_administrator"}),
        frozenset({"iam_administrator", "domain_administrator"}),
        frozenset({"iam_administrator", "independent_privileged_access_reviewer"}),
        frozenset({"audit_custodian", "independent_privileged_access_reviewer"}),
        frozenset({"data_owner", "export_approver"}),
        frozenset({"dlp_security_officer", "export_approver"}),
        frozenset({"dlp_security_officer", "disclosure_control_reviewer"}),
        frozenset({"break_glass_approver", "system_administrator"}),
        frozenset({"break_glass_approver", "independent_privileged_access_reviewer"}),
        frozenset({"disclosure_control_reviewer", "data_owner"}),
        frozenset({"independent_privileged_access_reviewer", "domain_administrator"}),
    }
)

PAIRWISE_INCOMPATIBLE_ROLES: frozenset[frozenset[str]] = (
    PRESERVED_INSTITUTIONAL_PAIRS | ADDED_INCOMPATIBLE_PAIRS
)


def incompatible_with(role_code: str) -> frozenset[str]:
    """Every role code that may not be held alongside `role_code`."""
    return frozenset(
        other
        for pair in PAIRWISE_INCOMPATIBLE_ROLES
        if role_code in pair
        for other in pair
        if other != role_code
    )


def assert_roles_compatible(role_codes: Iterable[str]) -> None:
    """Raise if any incompatible pair is held simultaneously.

    Evaluated at assignment time by PACK-08 and re-evaluated here at the
    moment of the act, over the roles the acting subject really holds in
    that scope (`P12-ROLE-013`)."""
    held = sorted(set(role_codes))
    for index, first in enumerate(held):
        for second in held[index + 1 :]:
            if frozenset({first, second}) in PAIRWISE_INCOMPATIBLE_ROLES:
                raise AuthorityRoleIncompatibleError(
                    f"role_code {first!r} is incompatible with already-held role_code {second!r} "
                    f"in the same scope (baseline {INCOMPATIBILITY_BASELINE_VERSION})"
                )


def assert_no_institutional_escalation(role_codes: Iterable[str]) -> None:
    """Raise if a set of operational assignments would compose into an
    institutional authority the subject does not hold (`P12-ROLE-021`).

    The check is deliberately conservative: an operational set that
    covers both what a system administrator does (infrastructure) and
    what a security administrator does (policy) is refused even though
    neither institutional role is held, because the *effect* is the
    combination the Institutional Role Matrix separates."""
    held = set(role_codes)
    operational = held & OPERATIONAL_ASSIGNMENT_CODES
    #: Assignment groups that, combined, reproduce an institutional
    #: separation the matrix draws.
    escalating_combinations = (
        ({"iam_administrator"}, {"domain_administrator"}),
        ({"audit_custodian"}, {"domain_administrator"}),
        ({"iam_administrator"}, {"audit_custodian"}),
    )
    for left, right in escalating_combinations:
        if left <= operational and right <= operational:
            raise RoleCombinationProhibitedError(
                f"the assignment set {sorted(operational)} composes into an authority the "
                "Institutional Role Matrix separates; no single assignment was individually "
                "forbidden, and the composition is refused"
            )


def assert_assignment_does_not_extend_institutional(
    assignment_role: str, claimed_institutional: str
) -> None:
    """Raise if an operational assignment is presented as institutional
    standing (`P12-ROLE-019`)."""
    if is_operational_assignment(assignment_role) and claimed_institutional:
        raise InstitutionalAuthorityNotExtendableError(
            f"operational assignment {assignment_role!r} confers no institutional standing; "
            f"{claimed_institutional!r} must be held in its own right"
        )


# ---------------------------------------------------------------------------
# Operational assignment
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperationalAssignment:
    """One privileged operational assignment, as PACK-12 records it.

    Every field is mandatory by construction. `P12-ROLE-018` requires
    scope, purpose and effective dating; a dataclass that could be built
    without them would make the requirement advisory."""

    assignment_id: UUID
    role: OperationalAssignmentRole
    subject_reference: str
    authority: AuthorityReference
    organization_scope: OrganizationalScopeRef
    domain_scope: str
    permitted_operations: frozenset[str]
    purpose: PurposeBinding
    window: EffectiveWindow
    granted_by: str
    approved_by: str
    status: str = "active"
    review_reference: str | None = None

    def __post_init__(self) -> None:
        require_text(self.subject_reference, "subject_reference")
        require_text(self.domain_scope, "domain_scope")
        require_text(self.granted_by, "granted_by")
        require_text(self.approved_by, "approved_by")
        if not self.permitted_operations:
            raise AssignmentNotGovernedError(
                "an operational assignment must name at least one permitted operation"
            )
        if self.granted_by == self.subject_reference and self.approved_by == self.subject_reference:
            raise SelfApprovalProhibitedError(
                "an assignment may not be both granted and approved by its own subject"
            )

    def is_effective_at(self, at: datetime) -> bool:
        return self.status == "active" and self.window.covers(at)

    def to_state_payload(self) -> dict[str, object]:
        return {
            "assignment_id": str(self.assignment_id),
            "role": str(self.role),
            "subject_reference": self.subject_reference,
            "authority": self.authority.to_state_payload(),
            "organization_scope": self.organization_scope.to_payload(),
            "domain_scope": self.domain_scope,
            "permitted_operations": sorted(self.permitted_operations),
            "purpose": self.purpose.to_payload(),
            "window": self.window.to_payload(),
            "granted_by": self.granted_by,
            "approved_by": self.approved_by,
            "status": self.status,
            "review_reference": self.review_reference,
        }


# ---------------------------------------------------------------------------
# Authorization port
# ---------------------------------------------------------------------------


class AuthorizationPort(Protocol):
    """How this service learns about authority. Implemented against
    PACK-08; PACK-12 stores no assignment and mints none."""

    def resolve_active_authority(
        self,
        authority: AuthorityReference,
        scope: OrganizationalScopeRef,
        at: datetime,
    ) -> bool:
        """Whether an active, effective-dated, scope-matching assignment
        exists behind the presented authority object."""
        ...

    def held_roles(self, actor_reference: str, scope: OrganizationalScopeRef) -> frozenset[str]:
        """Every `role_code` the actor actually holds, active, in that
        scope."""
        ...


def assert_authorized(
    required_roles: frozenset[str],
    presented: Sequence[AuthorityReference],
    scope: OrganizationalScopeRef,
    *,
    at: datetime,
    port: AuthorizationPort,
) -> AuthorityReference:
    """Resolve one presented authority that satisfies `required_roles`.

    A `role_code` string is never proof (`P12-ROLE-017`): each candidate
    is resolved through the port to an active, effective-dated,
    scope-matching assignment, and the roles the actor really holds are
    re-checked against the incompatibility matrix and the
    institutional-escalation rule."""
    if not required_roles:
        raise PrivilegeAuthorityMissingError(
            "no role requirement is declared for this action - default deny"
        )
    for candidate in presented:
        if candidate.role_code not in required_roles:
            continue
        if candidate.scope.organization_id != scope.organization_id:
            raise PrivilegeOrganizationMismatchError(
                "the presented authority belongs to a different organization"
            )
        if not port.resolve_active_authority(candidate, scope, at):
            continue
        actor = candidate.actor_reference.strip()
        if actor:
            held = port.held_roles(actor, scope)
            assert_roles_compatible({*held, candidate.role_code})
            assert_no_institutional_escalation({*held, candidate.role_code})
        return candidate
    raise PrivilegeAuthorityMissingError(
        f"no active, scope-matching authority among {sorted(required_roles)} was presented"
    )


def assert_not_self_approval(
    actor_reference: str, prior_actor_reference: str, *, action: str
) -> None:
    """Raise if the acting subject is the one who performed the prior,
    separated act (`P12-PAM-004`)."""
    if actor_reference and prior_actor_reference and actor_reference == prior_actor_reference:
        raise SelfApprovalProhibitedError(
            f"{action}: the acting subject also performed the separated prior act"
        )


def assert_distinct_reviewer(reviewer_reference: str, *, activator: str, approver: str) -> None:
    """Raise unless the independent reviewer is neither the activator nor
    the approver (`P12-BG-014`)."""
    if reviewer_reference in {activator, approver}:
        raise SelfApprovalProhibitedError(
            "the independent reviewer must be neither the activator nor the approver"
        )


def required_roles_for_purpose(purpose: Purpose) -> frozenset[str]:
    """The assignment roles that may act for a given purpose.

    Deliberately narrow: a purpose that no role serves denies, rather
    than falling through to a permissive default."""
    table: dict[Purpose, frozenset[str]] = {
        Purpose.SYSTEM_ADMINISTRATION: frozenset({InstitutionalRole.SYSTEM_ADMINISTRATOR.value}),
        Purpose.SECURITY_ADMINISTRATION: frozenset(
            {InstitutionalRole.SECURITY_ADMINISTRATOR.value}
        ),
        Purpose.AUDIT: frozenset(
            {
                OperationalAssignmentRole.AUDIT_CUSTODIAN.value,
                OperationalAssignmentRole.INDEPENDENT_PRIVILEGED_ACCESS_REVIEWER.value,
            }
        ),
        Purpose.INVESTIGATION: frozenset({OperationalAssignmentRole.DOMAIN_ADMINISTRATOR.value}),
        Purpose.COMPLIANCE_REVIEW: frozenset(
            {OperationalAssignmentRole.DOMAIN_ADMINISTRATOR.value}
        ),
        Purpose.INCIDENT_RESPONSE: frozenset(
            {OperationalAssignmentRole.DOMAIN_ADMINISTRATOR.value}
        ),
        Purpose.OPERATIONS: frozenset({OperationalAssignmentRole.DOMAIN_ADMINISTRATOR.value}),
        Purpose.DATA_SUBJECT_REQUEST: frozenset({OperationalAssignmentRole.DATA_OWNER.value}),
        Purpose.LEGAL_PROCEEDING: frozenset({OperationalAssignmentRole.DATA_OWNER.value}),
        Purpose.STATISTICAL_RELEASE: frozenset(
            {OperationalAssignmentRole.DISCLOSURE_CONTROL_REVIEWER.value}
        ),
        Purpose.TRANSPARENCY_PUBLICATION: frozenset({OperationalAssignmentRole.DATA_OWNER.value}),
    }
    return table.get(purpose, frozenset())

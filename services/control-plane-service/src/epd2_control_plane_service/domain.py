"""CTRL-01 control-plane domain model.

Governed by `FIR-CTRL-001` (unified control plane), `FIR-GOV-004` (regional
authority suspension and intervention), `FIR-GOV-005` (statutory party-organ
competence binding), `FIR-SEC-004` (access, credential and key authority
lifecycle) and `FIR-TRUST-002`/`FIR-TRUST-003` (resilient trust, key classes).

The hard rule expressed by these types is that a control-plane authority is
never a single undifferentiated `admin` capability. Authority is always the
conjunction of: an exact subject, an exact office/role code, an exact
organizational scope, an exact capability, an exact governing rule version, an
exact source decision, a validity window and a current lifecycle state. Any
unresolved element fails closed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

__all__ = [
    "MAX_SUPERVISION_DAYS",
    "VOTING_DOMAIN_FORBIDDEN_FIELDS",
    "ActorClass",
    "AuthorityState",
    "BreakGlassGrant",
    "BreakGlassState",
    "ControlAction",
    "CredentialClass",
    "CredentialState",
    "InterventionType",
    "OrganizationalAuthority",
    "Principal",
    "RegionalAdministrationRestriction",
    "Right",
    "Scope",
    "ScopeLevel",
    "ServiceCredential",
    "Session",
    "SessionState",
    "TemporarySupervision",
    "TrustKeyReference",
]


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ActorClass(StrEnum):
    """Class of actor that may hold a right on a control action.

    `HUMAN` and `SERVICE` are disjoint. A service identity may never satisfy a
    right that an inventory entry reserves for a human actor, and a human may
    never satisfy a right reserved for a workload identity. This is the
    machine-readable form of the `FIR-SEC-004` rule that a workload credential
    is not a human authentication credential.
    """

    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class Right(StrEnum):
    """Separable capabilities, per `FIR-SEC-004` "rights are separate
    capabilities" and the `FIR-GOV-005` request/approval/execution split.

    No role label grants the whole set. The inventory names, per action, which
    right is required for each step of the workflow.
    """

    REQUEST = "REQUEST"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"
    ACTIVATE = "ACTIVATE"
    SUSPEND_OR_QUARANTINE = "SUSPEND_OR_QUARANTINE"
    REVOKE = "REVOKE"
    RESTORE = "RESTORE"
    ROTATE_OR_REPLACE = "ROTATE_OR_REPLACE"
    DESTROY = "DESTROY"
    READ_METADATA = "READ_METADATA"
    VIEW_OR_EXPORT_SECRET = "VIEW_OR_EXPORT_SECRET"
    REVIEW_OR_AUDIT = "REVIEW_OR_AUDIT"


class ScopeLevel(StrEnum):
    """Territorial level of a formal Gebietsverband, per `FIR-GOV-005` section 2.

    `PLATFORM` is the technical operations scope. It is deliberately *not* the
    top of the political hierarchy: platform operation creates no party-organ
    competence, and Bund competence creates no platform authority.
    """

    PLATFORM = "PLATFORM"
    BUND = "BUND"
    LAND = "LAND"
    KREIS = "KREIS"
    ORT = "ORT"


class AuthorityState(StrEnum):
    """`OrganizationalAuthority` lifecycle, per `FIR-GOV-004` intervention
    level 2: `ACTIVE -> SUSPENDED -> ACTIVE | REVOKED`, with ordinary expiry."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class SessionState(StrEnum):
    """Session lifecycle, per `FIR-SEC-004`: `ACTIVE -> QUARANTINED | REVOKED |
    EXPIRED`. Session invalidation is a distinct act from credential
    revocation."""

    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class CredentialClass(StrEnum):
    """Control-object classes of `FIR-SEC-004`. Their authority semantics may
    not be collapsed into one another."""

    HUMAN_AUTHENTICATOR = "HUMAN_AUTHENTICATOR"
    RECOVERY_FACTOR = "RECOVERY_FACTOR"
    SESSION_ARTIFACT = "SESSION_ARTIFACT"
    SERVICE_WORKLOAD = "SERVICE_WORKLOAD"
    PLATFORM_KEY = "PLATFORM_KEY"
    PROVIDER_SECRET = "PROVIDER_SECRET"
    VOTING_DOMAIN = "VOTING_DOMAIN"


class CredentialState(StrEnum):
    """`FIR-SEC-004` human credential lifecycle semantics. A revoked or
    replaced credential is never resurrected under the same identity."""

    PENDING_ENROLLMENT = "PENDING_ENROLLMENT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    REVOKED = "REVOKED"
    REPLACED = "REPLACED"
    DESTROYED = "DESTROYED"


class InterventionType(StrEnum):
    """The four distinct `FIR-GOV-004` levels. There is deliberately no
    `REGION_DISABLED` member: "contain authority, not the region"."""

    SESSION_QUARANTINE = "SESSION_QUARANTINE"
    AUTHORITY_SUSPENSION = "AUTHORITY_SUSPENSION"
    REGIONAL_ACTION_RESTRICTION = "REGIONAL_ACTION_RESTRICTION"
    TEMPORARY_SUPERVISION = "TEMPORARY_SUPERVISION"


class BreakGlassState(StrEnum):
    """`REQUEST -> APPROVE -> ACTIVATE -> USE -> EXPIRE/REVOKE -> REVIEW`."""

    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    REVIEWED = "REVIEWED"


#: `FIR-GOV-004` intervention level 4 and the resilient-trust model cap
#: temporary supervision at 90 days; extension requires a new governed
#: decision rather than a silent prolongation of the existing one.
MAX_SUPERVISION_DAYS = 90

#: Field names that would create an identity/ballot correlation channel if they
#: ever appeared in generic control-plane evidence (`FIR-VOTE-NET-001`,
#: `FIR-GOV-004` voting carve-out, `FIR-GOV-005` section 19). The control plane
#: refuses to emit them rather than filtering them at the reader.
VOTING_DOMAIN_FORBIDDEN_FIELDS = frozenset(
    {
        "ballot",
        "ballot_content",
        "ballot_id",
        "ballot_ref",
        "voter_id",
        "voter_reference",
        "voting_member_id",
        "voting_person_id",
        "voting_credential",
        "voting_credential_id",
        "voting_nonce",
        "vote_choice",
        "vote_token",
        "tally_share",
        "trustee_key",
        "trustee_share",
        "member_person_id",
        "person_id",
        "national_id",
    }
)


_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


def _require_id(value: str, label: str) -> str:
    if not _ID_PATTERN.match(value):
        raise ValueError(f"{label} is not a well-formed stable identifier: {value!r}")
    return value


def _require_aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Scope:
    """An exact organizational scope.

    Containment is deliberately *not* hierarchical inheritance. `contains`
    answers "is this the same scope", not "is this at or above that scope",
    because `FIR-GOV-005` section 1 forbids a higher organizational level from
    automatically inheriting the authority of a lower one. Oversight across
    scopes exists only where a `ControlAction` explicitly declares an
    `oversight_of` relation bound to a rule version and a source decision.
    """

    level: ScopeLevel
    org_id: str

    def __post_init__(self) -> None:
        _require_id(self.org_id, "Scope.org_id")

    @property
    def key(self) -> str:
        return f"{self.level.value}:{self.org_id}"

    def contains(self, other: Scope) -> bool:
        """Exact-scope match. No hierarchy-derived widening."""
        return self.level is other.level and self.org_id == other.org_id

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.key


@dataclass(frozen=True, slots=True)
class Principal:
    """An acting subject: a natural person holding governed offices, or a
    workload identity. `actor_class` is authoritative and is never inferred
    from the roles a principal happens to hold."""

    principal_id: str
    actor_class: ActorClass
    display_reference: str

    def __post_init__(self) -> None:
        _require_id(self.principal_id, "Principal.principal_id")


@dataclass(frozen=True, slots=True)
class OrganizationalAuthority:
    """The authoritative governed authority record (`FIR-GOV-005` section 16).

    A runtime authority projection is a short-lived representation of this
    record and never a replacement for it: `is_effective_at` is re-evaluated at
    every consequential act.
    """

    authority_id: str
    subject_ref: str
    office_code: str
    scope: Scope
    capabilities: frozenset[Right]
    action_codes: frozenset[str]
    rule_version: str
    source_decision_ref: str
    appointed_by_ref: str
    valid_from: datetime
    valid_until: datetime | None
    state: AuthorityState
    evidence_refs: tuple[str, ...] = ()
    #: Scopes over which this authority carries an explicitly granted oversight
    #: competence. Empty for every ordinary authority. It never appears by
    #: virtue of the holder's position in the hierarchy.
    oversight_of: frozenset[str] = frozenset()
    #: The single scope the source decision actually names. An oversight grant is
    #: honoured only when `oversight_of` is exactly this scope, so widening the
    #: grant, or re-pointing it at a scope the decision does not cover, both fail
    #: closed rather than silently extending the decision.
    oversight_decision_scope: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.authority_id, "OrganizationalAuthority.authority_id")
        _require_aware(self.valid_from, "OrganizationalAuthority.valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "OrganizationalAuthority.valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("OrganizationalAuthority validity window is empty")
        if not self.rule_version or not self.source_decision_ref:
            # FIR-GOV-005 section 16: authority without an exact governing rule
            # version and an exact source decision is unresolvable and must fail
            # closed rather than default to permitted.
            raise ValueError(
                "OrganizationalAuthority requires rule_version and source_decision_ref"
            )

    def is_effective_at(self, moment: datetime) -> bool:
        if self.state is not AuthorityState.ACTIVE:
            return False
        if moment < self.valid_from:
            return False
        return not (self.valid_until is not None and moment >= self.valid_until)

    def with_state(self, state: AuthorityState) -> OrganizationalAuthority:
        return replace(self, state=state)


@dataclass(frozen=True, slots=True)
class Session:
    """A runtime session. Quarantine is an independent act from credential
    revocation (`FIR-SEC-004` session lifecycle)."""

    session_id: str
    principal_id: str
    state: SessionState
    established_at: datetime
    assurance_level: str

    def __post_init__(self) -> None:
        _require_id(self.session_id, "Session.session_id")
        _require_aware(self.established_at, "Session.established_at")


@dataclass(frozen=True, slots=True)
class ServiceCredential:
    """A workload credential (`FIR-SEC-004` class 6). `holder_service` is the
    owning workload; a human principal can never present one."""

    credential_id: str
    holder_service: str
    credential_class: CredentialClass
    state: CredentialState
    scope: Scope
    not_after: datetime | None = None

    def __post_init__(self) -> None:
        _require_id(self.credential_id, "ServiceCredential.credential_id")


@dataclass(frozen=True, slots=True)
class TrustKeyReference:
    """A *reference* to platform or voting-domain key material.

    The control plane records key class, custody policy and trust state. It
    never carries private material, and for `VOTING_DOMAIN` class it is an
    external governed reference only: no control-plane right can operate it
    (`FIR-GOV-005` section 19, `FIR-SEC-004` class 9).
    """

    key_reference_id: str
    key_class: str
    credential_class: CredentialClass
    algorithm: str
    trust_state: str
    custody_policy_ref: str
    exportable: bool = False
    quorum_m: int | None = None
    quorum_n: int | None = None

    def __post_init__(self) -> None:
        _require_id(self.key_reference_id, "TrustKeyReference.key_reference_id")
        if self.credential_class is CredentialClass.VOTING_DOMAIN and self.exportable:
            raise ValueError(
                "voting-domain key material is never exportable through the control plane"
            )
        if (self.quorum_m is None) != (self.quorum_n is None):
            raise ValueError("threshold policy requires both quorum_m and quorum_n")
        if (
            self.quorum_m is not None
            and self.quorum_n is not None
            and not 1 <= self.quorum_m <= self.quorum_n
        ):
            raise ValueError("threshold policy requires 1 <= m <= n")


@dataclass(frozen=True, slots=True)
class RegionalAdministrationRestriction:
    """`FIR-GOV-004` minimum restriction contract.

    Every temporary level-2..4 intervention carries a mandatory `valid_until`.
    `affected_action_codes` is a closed, registered set: free-text action
    classes are rejected at construction by the intervention service, which
    validates them against the action inventory.
    """

    restriction_id: str
    intervention_type: InterventionType
    target_scope: Scope
    affected_authority_ids: frozenset[str]
    affected_action_codes: frozenset[str]
    valid_from: datetime
    valid_until: datetime | None
    reason_code: str
    rule_version: str
    decision_ref: str
    initiating_authority_id: str
    approving_authority_id: str | None
    notification_evidence_ref: str
    review_deadline: datetime
    evidence_refs: tuple[str, ...] = ()
    superseded_by: str | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_id(self.restriction_id, "RegionalAdministrationRestriction.restriction_id")
        _require_aware(self.valid_from, "RegionalAdministrationRestriction.valid_from")
        _require_aware(self.review_deadline, "RegionalAdministrationRestriction.review_deadline")
        if self.valid_until is None:
            raise ValueError(
                "FIR-GOV-004 requires a mandatory valid_until for every temporary intervention; "
                "indefinite restrictions are prohibited"
            )
        _require_aware(self.valid_until, "RegionalAdministrationRestriction.valid_until")
        if self.valid_until <= self.valid_from:
            raise ValueError("restriction validity window is empty")
        if (
            not self.affected_action_codes
            and self.intervention_type is InterventionType.REGIONAL_ACTION_RESTRICTION
        ):
            raise ValueError(
                "a REGIONAL_ACTION_RESTRICTION must name the exact action codes it freezes; "
                "a scope-wide disable is prohibited"
            )
        if not self.reason_code or not self.rule_version or not self.decision_ref:
            raise ValueError("restriction requires reason_code, rule_version and decision_ref")

    def is_active_at(self, moment: datetime) -> bool:
        if self.revoked_at is not None and moment >= self.revoked_at:
            return False
        if self.superseded_by is not None:
            return False
        assert self.valid_until is not None  # guaranteed by __post_init__
        return self.valid_from <= moment < self.valid_until

    def restricts(self, action_code: str, scope: Scope, authority_id: str | None) -> bool:
        if not self.target_scope.contains(scope):
            return False
        if self.affected_authority_ids and authority_id not in self.affected_authority_ids:
            return False
        return action_code in self.affected_action_codes


@dataclass(frozen=True, slots=True)
class TemporarySupervision:
    """`FIR-GOV-004` level 4. Narrow functional substitution, never a takeover.

    `granted_action_codes` must be a subset of what the supervised scope itself
    could lawfully do, and the supervisor gains no authority in any other scope.
    """

    supervision_id: str
    supervised_scope: Scope
    supervisor_authority_id: str
    granted_action_codes: frozenset[str]
    valid_from: datetime
    valid_until: datetime
    decision_ref: str
    rule_version: str
    review_deadline: datetime
    confirmation_organ: str

    def __post_init__(self) -> None:
        _require_id(self.supervision_id, "TemporarySupervision.supervision_id")
        _require_aware(self.valid_from, "TemporarySupervision.valid_from")
        _require_aware(self.valid_until, "TemporarySupervision.valid_until")
        span = self.valid_until - self.valid_from
        if span.days > MAX_SUPERVISION_DAYS or span.total_seconds() <= 0:
            raise ValueError(
                f"temporary supervision must be positive and at most {MAX_SUPERVISION_DAYS} days; "
                "extension requires a new governed decision"
            )
        if not self.granted_action_codes:
            raise ValueError("temporary supervision must name the exact functions it substitutes")

    def is_active_at(self, moment: datetime) -> bool:
        return self.valid_from <= moment < self.valid_until


@dataclass(frozen=True, slots=True)
class BreakGlassGrant:
    """A bounded emergency grant (`FIR-CTRL-001` break-glass boundary,
    `FIR-SEC-004` break-glass row).

    Expiry is absolute and computed from activation; there is no renewal field,
    because a renewable emergency grant is a permanent privilege in disguise.
    A follow-on emergency requires a new REQUEST with its own approval.
    """

    grant_id: str
    principal_id: str
    reason: str
    scope: Scope
    action_codes: frozenset[str]
    state: BreakGlassState
    requested_at: datetime
    requested_by: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    activated_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    used_action_refs: tuple[str, ...] = ()
    review_ref: str | None = None
    prohibited_action_codes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _require_id(self.grant_id, "BreakGlassGrant.grant_id")
        if not self.reason.strip():
            raise ValueError("break-glass requires an explicit reason")
        if not self.action_codes:
            raise ValueError("break-glass requires an exact action scope")

    def is_usable_at(self, moment: datetime) -> bool:
        if self.state is not BreakGlassState.ACTIVE:
            return False
        if self.revoked_at is not None and moment >= self.revoked_at:
            return False
        return not (self.expires_at is None or moment >= self.expires_at)


@dataclass(frozen=True, slots=True)
class ControlAction:
    """One entry of the machine-readable administrative action inventory (W1).

    Every runtime control-plane mutation resolves to exactly one of these. The
    inventory is the authorization contract: the runtime reads required rights,
    quorum, emergency eligibility and evidence obligations from here rather than
    from a role label.
    """

    action_id: str
    domain: str
    actor_class: ActorClass
    required_right_request: Right
    required_right_approve: Right | None
    required_right_execute: Right
    required_right_revoke: Right | None
    required_right_audit: Right
    secret_visibility_right: Right | None
    scope_level: ScopeLevel
    object_class: str
    mutation: bool
    quorum_required: int
    four_eyes: bool
    emergency_eligible: bool
    max_grant_seconds: int | None
    commit_time_reauthorization: bool
    immutable_evidence_required: bool
    console_id: str
    desk_id: str
    route: str
    assurance_level: str
    step_up_required: bool
    incompatible_rights: frozenset[tuple[Right, Right]]
    sensitive_data_classes: frozenset[str]
    voting_domain_boundary: str
    governing_fir_refs: tuple[str, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        _require_id(self.action_id, "ControlAction.action_id")
        if self.four_eyes and self.quorum_required < 2:
            raise ValueError(f"{self.action_id}: four-eyes requires quorum >= 2")
        if self.quorum_required >= 1 and self.required_right_approve is None:
            raise ValueError(f"{self.action_id}: quorum requires an approve right")
        if self.mutation and not self.immutable_evidence_required:
            raise ValueError(
                f"{self.action_id}: every consequential mutation must emit immutable evidence"
            )
        if self.mutation and not self.commit_time_reauthorization:
            raise ValueError(
                f"{self.action_id}: every consequential mutation re-checks authority at commit"
            )
        if self.emergency_eligible and self.max_grant_seconds is None:
            raise ValueError(
                f"{self.action_id}: emergency-eligible actions require a bounded grant lifetime"
            )


@dataclass(frozen=True, slots=True)
class ControlRequest:
    """A governed request moving through REQUEST -> APPROVE -> EXECUTE."""

    request_id: str
    action_id: str
    requested_by: str
    requesting_authority_id: str
    target_scope: Scope
    object_ref: str
    purpose: str
    requested_at: datetime
    approvals: tuple[tuple[str, str], ...] = ()  # (principal_id, authority_id)
    executed_at: datetime | None = None
    refused_reason: str | None = None
    parameters: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.request_id, "ControlRequest.request_id")
        _require_aware(self.requested_at, "ControlRequest.requested_at")

    def approver_ids(self) -> frozenset[str]:
        return frozenset(principal for principal, _ in self.approvals)

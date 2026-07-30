"""Privileged data-plane operations (PACK-13 §26).

**PACK-12 remains the owner.** This module adds no privileged-access
model, no role, no approval workflow and no session mechanism: it holds
the *gates* the data plane applies to a PACK-12 grant it was handed.

Five refusals, each restating a rule that a production data plane is
exactly where it would be lost:

- **Database operator privilege is not domain-content authority**
  (`P13-SEC-001`). Holding the highest role on the cluster confers no
  right to read a membership record, and `require_domain_content_authority`
  refuses the substitution.
- **Migration execution requires a scoped privileged grant**
  (`P13-SEC-002`) — purpose-bound, time-bound, approved, evidenced.
- **Direct SQL requires a governed migration or emergency context**
  (`P13-SEC-003`). There is no arbitrary-SQL path in this package, and
  `require_governed_sql_context` refuses one presented from outside.
- **Schema publication and destructive migration require separation of
  duties** (`P13-SEC-004`).
- **Break-glass disables no audit and no invariant** (`P13-SEC-006`,
  FIR-INV-006). `BreakGlassContext` *adds* obligations; it has no field
  that could remove one.

`P13-SEC-005` — there is no universal database administrator with
unrestricted domain-content access — is expressed as
`INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS`: the role that operates the cluster
and the role that may read a domain's content are different roles, and
FIR-INV-014 makes them incompatible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    DomainReference,
    EvidenceReference,
    OrganizationScopeReference,
    PrivilegedGrantReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    ManualSqlProhibitedError,
    MigrationSeparationOfDutiesMissingError,
    OperatorPrivilegeInsufficientError,
    PrivilegeAuthorityMissingError,
)


class DataPlaneRole(StrEnum):
    """The operational data-plane roles this package distinguishes.

    Not an authorization model — PACK-08 and PACK-12 own those. These
    exist only so the incompatibility `P13-SEC-005` names can be stated
    as data."""

    CLUSTER_OPERATOR = "cluster_operator"
    MIGRATION_EXECUTOR = "migration_executor"
    SCHEMA_STEWARD = "schema_steward"
    DOMAIN_CONTENT_READER = "domain_content_reader"
    DEAD_LETTER_REVIEWER = "dead_letter_reviewer"


#: The pairs no subject may hold together. `CLUSTER_OPERATOR` with
#: `DOMAIN_CONTENT_READER` is the universal-administrator role
#: FIR-INV-014 forbids; the others prevent a single subject from both
#: proposing and executing the two acts §26 separates.
INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS: frozenset[frozenset[DataPlaneRole]] = frozenset(
    {
        frozenset({DataPlaneRole.CLUSTER_OPERATOR, DataPlaneRole.DOMAIN_CONTENT_READER}),
        frozenset({DataPlaneRole.CLUSTER_OPERATOR, DataPlaneRole.DEAD_LETTER_REVIEWER}),
        frozenset({DataPlaneRole.MIGRATION_EXECUTOR, DataPlaneRole.SCHEMA_STEWARD}),
    }
)


def reject_incompatible_roles(roles: frozenset[DataPlaneRole], *, subject: ActorReference) -> None:
    """Refuse a role combination the matrix forbids."""
    for pair in INCOMPATIBLE_DATA_PLANE_ROLE_PAIRS:
        if pair <= roles:
            raise OperatorPrivilegeInsufficientError(
                f"subject {subject.actor_id} would hold {sorted(r.value for r in pair)} "
                f"together; the role that operates the cluster and the role that may read a "
                f"domain's content are different roles (P13-SEC-005, FIR-INV-014)"
            )


class DataPlaneOperation(StrEnum):
    """The operations that require a scoped grant."""

    MIGRATION_EXECUTION = "migration_execution"
    DESTRUCTIVE_MIGRATION = "destructive_migration"
    SCHEMA_ACTIVATION = "schema_activation"
    DIRECT_SQL = "direct_sql"
    EVENT_REPLAY = "event_replay"
    CONSUMER_CHECKPOINT_REWIND = "consumer_checkpoint_rewind"
    PROJECTION_REBUILD = "projection_rebuild"
    DEAD_LETTER_REVIEW = "dead_letter_review"


#: Which operations require separation of duties in addition to a grant
#: (`P13-SEC-004`).
SEPARATION_OF_DUTIES_OPERATIONS: frozenset[DataPlaneOperation] = frozenset(
    {
        DataPlaneOperation.DESTRUCTIVE_MIGRATION,
        DataPlaneOperation.SCHEMA_ACTIVATION,
    }
)


def require_scoped_grant(
    grant: PrivilegedGrantReference | None,
    *,
    operation: DataPlaneOperation,
    scope: OrganizationScopeReference,
    now: datetime,
) -> PrivilegedGrantReference:
    """Refuse an operation with no grant, the wrong grant, an expired
    grant or a grant for another scope.

    Four checks rather than one, because a caller who presented *a* grant
    and was refused needs to know which of the four facts was wrong."""
    require_timezone(now, field="now")
    if grant is None:
        raise PrivilegeAuthorityMissingError(
            f"{operation.value} requires a scoped PACK-12 privileged grant — purpose-bound, "
            f"time-bound, approved, evidenced (P13-SEC-002)"
        )
    if grant.operation != operation.value:
        raise PrivilegeAuthorityMissingError(
            f"the presented grant authorizes {grant.operation!r}, not {operation.value!r}; a "
            f"purpose may narrow what is reachable, never widen it"
        )
    if now >= grant.expires_at:
        raise PrivilegeAuthorityMissingError(
            f"grant {grant.grant_id} expired at {grant.expires_at.isoformat()}; authority "
            f"that lapsed is not authority"
        )
    if not grant.scope.matches(scope):
        raise PrivilegeAuthorityMissingError(
            f"grant {grant.grant_id} is scoped to organization "
            f"{grant.scope.organization_id} and the operation targets "
            f"{scope.organization_id}"
        )
    return grant


def require_separation_of_duties(
    *, operation: DataPlaneOperation, proposer: ActorReference, approver: ActorReference
) -> None:
    """Refuse a separated operation performed by one subject
    (`P13-SEC-004`)."""
    if operation not in SEPARATION_OF_DUTIES_OPERATIONS:
        return
    if proposer.actor_id == approver.actor_id:
        raise MigrationSeparationOfDutiesMissingError(
            f"{operation.value} requires separation of duties; the proposer and the approver "
            f"are the same subject"
        )


def require_domain_content_authority(
    *,
    holds_cluster_privilege: bool,
    holds_domain_content_authority: bool,
    domain: DomainReference,
) -> None:
    """Refuse cluster privilege presented as domain-content authority.

    Stated as two independent booleans rather than a single privilege
    level, because the whole point is that one does not imply the
    other."""
    if holds_domain_content_authority:
        return
    if holds_cluster_privilege:
        raise OperatorPrivilegeInsufficientError(
            f"cluster privilege confers no right to read {domain.domain_name}'s content; "
            f"database operator privilege is not domain-content authority (P13-SEC-001)"
        )
    raise OperatorPrivilegeInsufficientError(
        f"no domain-content authority for {domain.domain_name} was presented"
    )


class SqlExecutionContext(StrEnum):
    """The two governed contexts in which direct SQL may run
    (`P13-SEC-003`), and the one that is refused.

    `AD_HOC` exists in this enum precisely so it can be refused by name:
    an enum that omitted it would leave the refusal to a `None` check,
    and a `None` check is easier to accidentally satisfy."""

    GOVERNED_MIGRATION = "governed_migration"
    BREAK_GLASS_EMERGENCY = "break_glass_emergency"
    AD_HOC = "ad_hoc"


@dataclass(frozen=True, slots=True)
class BreakGlassContext:
    """An emergency context that **adds** obligations.

    Every field is an obligation, and there is deliberately no field that
    could disable one: no `skip_audit`, no `bypass_invariant`, no
    `suppress_notification`. `P13-SEC-006` and FIR-INV-006 are enforced
    by the absence of a switch, not by a check that a switch is off."""

    break_glass_id: UUID
    activated_by: ActorReference
    independent_reviewer: ActorReference
    activated_at: datetime
    expires_at: datetime
    evidence: EvidenceReference
    notification_sent: bool

    def __post_init__(self) -> None:
        require_timezone(self.activated_at, field="BreakGlassContext.activated_at")
        require_timezone(self.expires_at, field="BreakGlassContext.expires_at")
        if self.expires_at <= self.activated_at:
            raise ValueError("a break-glass context expires after it is activated")
        if self.activated_by.actor_id == self.independent_reviewer.actor_id:
            raise MigrationSeparationOfDutiesMissingError(
                "a break-glass activation is independently reviewed; the activator is not "
                "the reviewer"
            )
        if not self.notification_sent:
            raise PrivilegeAuthorityMissingError(
                "a break-glass activation notifies; an emergency path that adds no obligation "
                "is a bypass with a friendlier name (FIR-INV-006)"
            )

    @property
    def disables_audit(self) -> bool:
        """Always `False`. Break-glass disables no audit and no
        invariant; the property exists so a test can assert the answer
        rather than infer it from a missing field."""
        return False


def require_governed_sql_context(
    context: SqlExecutionContext,
    *,
    grant: PrivilegedGrantReference | None,
    break_glass: BreakGlassContext | None,
    scope: OrganizationScopeReference,
    now: datetime,
) -> None:
    """Refuse direct SQL outside a governed migration or emergency
    context (`P13-MIG-011`, `P13-SEC-003`).

    There is no arbitrary-SQL execution path anywhere in this package.
    This function exists to refuse one presented from outside it, and to
    make the refusal reason-coded rather than an import error."""
    if context is SqlExecutionContext.AD_HOC:
        raise ManualSqlProhibitedError(
            "direct SQL happens in a governed migration or an emergency context that leaves "
            "PACK-12 session evidence; there is no manual, undocumented production SQL"
        )
    if context is SqlExecutionContext.GOVERNED_MIGRATION:
        require_scoped_grant(grant, operation=DataPlaneOperation.DIRECT_SQL, scope=scope, now=now)
        return
    if break_glass is None:
        raise PrivilegeAuthorityMissingError(
            "an emergency SQL context requires an activated, notified, independently "
            "reviewed break-glass context with its own evidence"
        )
    require_timezone(now, field="now")
    if now >= break_glass.expires_at:
        raise PrivilegeAuthorityMissingError(
            f"break-glass context {break_glass.break_glass_id} expired at "
            f"{break_glass.expires_at.isoformat()}"
        )


@dataclass(frozen=True, slots=True)
class PrivilegedActionRecord:
    """One reason-coded privileged data-plane action (§27's requirement
    that a privileged action is reason-coded).

    Carries no query text, no affected rows and no payload: `P13-OBS-002`
    forbids unrestricted query text in telemetry, and an action record is
    telemetry that outlives the action."""

    action_id: UUID
    operation: DataPlaneOperation
    actor: ActorReference
    scope: OrganizationScopeReference
    grant_id: UUID
    reason_code: str
    performed_at: datetime
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        require_timezone(self.performed_at, field="PrivilegedActionRecord.performed_at")
        if not self.reason_code:
            raise PrivilegeAuthorityMissingError(
                "a privileged action carries a registered reason code; free text is not a reason"
            )


#: What a privileged grant does **not** confer, stated as data so a
#: surface can display it and a test can assert it.
GRANT_CONFERS_NOTHING_ELSE: Mapping[str, str] = {
    "domain_content_read": (
        "A grant to execute a migration is not a grant to read the migrated domain's "
        "content (P13-SEC-001)."
    ),
    "export": (
        "No grant in this package produces data for a recipient; export is PACK-12's "
        "governed path (P13-EXPORT-004)."
    ),
    "audit_mutation": (
        "No grant permits altering an audit record; audit-core owns the chain and PACK-13 "
        "holds no mutating control over it."
    ),
    "voting_material": (
        "No grant reaches ballot content, a voting credential or an intermediate tally; "
        "none of it exists in this plane to reach."
    ),
}

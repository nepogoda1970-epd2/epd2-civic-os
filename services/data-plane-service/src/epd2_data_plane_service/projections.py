"""Projection and read-model governance (PACK-13 §21; ADR-076).

A read model makes hard queries easy, and that is exactly the risk. A
projection can quietly become three things it must not be: an
authoritative source, a cross-domain database, and an authorization
bypass. All three happen without anyone deciding.

So every projection here has a **named owner, declared source events, a
schema version and a rebuild strategy** (`P13-PROJ-001`); undeclared
projections do not exist, because `ProjectionDefinition` requires all
four. And four prohibitions are refusals rather than notes:

- **A read model is never authoritative and creates no legal effect**
  (`P13-PROJ-002`, `P13-PROJ-003`). `require_authoritative_source`
  refuses a legal-effect decision taken against one.
- **A projection never widens source authorization** (`P13-PROJ-004`).
  The projection's authorization is the *narrowest* of its inputs, and a
  definition that claims otherwise cannot be constructed.
- **A projection is not a hidden cross-domain database**
  (`P13-PROJ-005`). A multi-domain projection requires every source
  domain's ADR approval, recorded on the definition.
- **No projection uses a global identity bridge** (`P13-PROJ-006`). The
  prohibited-key guard applies to every projected row.

Two positive obligations: **staleness is visible** (`P13-PROJ-008`), so a
consequential decision path reads the lag and refuses when it is
unacceptable; and **deletion propagates with evidence**
(`P13-PROJ-009`), because a projection that outlives its source is an
undeletable copy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    DomainReference,
    EvidenceReference,
    OrganizationScopeReference,
    reject_prohibited_payload_keys,
    require_organization_scope,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    ProjectionAuthorizationWideningProhibitedError,
    ProjectionDeletionNotPropagatedError,
    ProjectionNotAuthoritativeError,
    ProjectionRebuildFailedError,
    ProjectionRebuildRequiredError,
    ProjectionStaleError,
    RecordUnderLegalHoldError,
)


class AuthorizationTier(StrEnum):
    """A coarse ordering of authorization strictness, used only to
    compute the *narrowest* of a projection's inputs.

    Deliberately coarse and deliberately not an authorization decision:
    PACK-12 owns those. This exists so `P13-PROJ-004`'s "narrowest of its
    inputs" is computable rather than asserted."""

    PUBLIC = "public"
    ORGANIZATION_MEMBER = "organization_member"
    ROLE_RESTRICTED = "role_restricted"
    PRIVILEGED = "privileged"


_TIER_STRICTNESS: Mapping[AuthorizationTier, int] = {
    AuthorizationTier.PUBLIC: 0,
    AuthorizationTier.ORGANIZATION_MEMBER: 1,
    AuthorizationTier.ROLE_RESTRICTED: 2,
    AuthorizationTier.PRIVILEGED: 3,
}


def narrowest_tier(tiers: Sequence[AuthorizationTier]) -> AuthorizationTier:
    """The strictest tier among `tiers`.

    "Narrowest" in the specification's sense means "hardest to reach": a
    projection of a privileged source and a public source is reachable
    only by whoever could reach the privileged one."""
    if not tiers:
        raise ValueError("a projection has at least one source")
    return max(tiers, key=lambda tier: _TIER_STRICTNESS[tier])


@dataclass(frozen=True, slots=True)
class ProjectionSource:
    """One declared source of a projection (`P13-PROJ-001`).

    Source events are declared by family, not discovered by subscription:
    a projection that consumed whatever arrived would have no answer to
    "can this be rebuilt from approved sources alone"."""

    owning_domain: DomainReference
    event_families: tuple[str, ...]
    authorization_tier: AuthorizationTier
    adr_approval_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.event_families:
            raise ValueError("a projection source declares at least one event family")


class RebuildStrategy(StrEnum):
    FROM_SOURCE_EVENTS = "from_source_events"
    FROM_SNAPSHOT_AND_EVENTS = "from_snapshot_and_events"
    NOT_REBUILDABLE = "not_rebuildable"


@dataclass(frozen=True, slots=True)
class ProjectionDefinition:
    """A declared projection.

    Multi-domain projections are admissible only where **every** source
    domain has approved that specific projection under ADR
    (`P13-PROJ-005`); construction refuses otherwise, so an unapproved
    cross-domain read model cannot exist to be queried."""

    projection_id: UUID
    projection_name: str
    owner: DomainReference
    sources: tuple[ProjectionSource, ...]
    schema_version_id: UUID
    rebuild_strategy: RebuildStrategy
    max_acceptable_lag_events: int
    authoritative: bool = False

    def __post_init__(self) -> None:
        if not self.sources:
            raise ValueError("a projection declares its source events (P13-PROJ-001)")
        if self.authoritative:
            raise ProjectionNotAuthoritativeError(
                f"projection {self.projection_name!r} declares itself authoritative; a read "
                f"model is not authoritative and creates no legal effect (P13-PROJ-002)"
            )
        if self.max_acceptable_lag_events < 0:
            raise ValueError("max_acceptable_lag_events must not be negative")
        domains = {source.owning_domain.domain_name for source in self.sources}
        if len(domains) > 1:
            unapproved = [
                source.owning_domain.domain_name
                for source in self.sources
                if not source.adr_approval_reference
            ]
            if unapproved:
                raise ProjectionAuthorizationWideningProhibitedError(
                    f"projection {self.projection_name!r} joins {sorted(domains)} and source "
                    f"domain(s) {sorted(unapproved)} have not approved it under ADR; a "
                    f"multi-domain projection is admissible only with every source domain's "
                    f"approval (P13-PROJ-005)"
                )

    @property
    def effective_authorization_tier(self) -> AuthorizationTier:
        """The narrowest authorization of the projection's inputs."""
        return narrowest_tier([source.authorization_tier for source in self.sources])

    @property
    def is_multi_domain(self) -> bool:
        return len({source.owning_domain.domain_name for source in self.sources}) > 1

    def require_no_authorization_widening(self, reader_tier: AuthorizationTier) -> None:
        """Refuse a read by someone who could not read the sources.

        If the reader could not read the source, the projection does not
        let them read the derivative (`P13-PROJ-004`)."""
        required = self.effective_authorization_tier
        if _TIER_STRICTNESS[reader_tier] < _TIER_STRICTNESS[required]:
            raise ProjectionAuthorizationWideningProhibitedError(
                f"projection {self.projection_name!r} carries the narrowest authorization of "
                f"its inputs ({required.value}); a reader at {reader_tier.value} could not "
                f"read the sources and does not reach the derivative"
            )


@dataclass(frozen=True, slots=True)
class ProjectionCheckpoint:
    """How far a projection has consumed its sources."""

    projection_id: UUID
    ordering_scope_key: str
    position: int
    updated_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.updated_at, field="ProjectionCheckpoint.updated_at")
        if self.position < 0:
            raise ValueError("a projection checkpoint position must not be negative")


@dataclass(frozen=True, slots=True)
class ProjectionLag:
    """Measured lag, reported as a **band** (`P13-EVT-009`).

    The exact figure is retained on the record for the owner's own
    threshold comparison, and the band is what an event or a cross-
    organization surface carries: an exact lag across organizations is
    itself information."""

    projection_id: UUID
    events_behind: int
    lag_band: str
    observed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="ProjectionLag.observed_at")
        if self.events_behind < 0:
            raise ValueError("events_behind must not be negative")


class ProjectionHealth(StrEnum):
    HEALTHY = "healthy"
    LAGGING = "lagging"
    STALE = "stale"
    REBUILD_REQUIRED = "rebuild_required"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProjectionStaleness:
    """The visible staleness state (`P13-PROJ-008`, `P13-PROJ-012`).

    A stale projection that looks fresh is worse than one that is plainly
    unavailable, so `health` is a required field with no default: a
    projection whose health nobody set does not exist."""

    projection_id: UUID
    health: ProjectionHealth
    lag: ProjectionLag
    max_acceptable_lag_events: int

    @property
    def acceptable_for_consequential_use(self) -> bool:
        return (
            self.health is ProjectionHealth.HEALTHY
            and self.lag.events_behind <= self.max_acceptable_lag_events
        )

    def require_acceptable_for_consequential_use(self, *, context: str) -> None:
        """Block a consequential use of an unacceptably stale
        projection."""
        if self.health in (ProjectionHealth.REBUILD_REQUIRED, ProjectionHealth.FAILED):
            raise ProjectionRebuildRequiredError(
                f"{context}: projection {self.projection_id} is {self.health.value} and "
                f"cannot serve until rebuilt"
            )
        if not self.acceptable_for_consequential_use:
            raise ProjectionStaleError(
                f"{context}: projection {self.projection_id} is {self.lag.events_behind} "
                f"events behind, past the {self.max_acceptable_lag_events} a consequential "
                f"decision accepts; the decision path reads the lag rather than assuming "
                f"freshness"
            )


@dataclass(frozen=True, slots=True)
class ProjectionRebuild:
    """One rebuild, from approved sources alone (`P13-PROJ-007`)."""

    rebuild_id: UUID
    projection_id: UUID
    from_position: int
    to_position: int
    started_at: datetime
    completed_at: datetime | None = None
    succeeded: bool | None = None
    records_rebuilt: int = 0

    def __post_init__(self) -> None:
        require_timezone(self.started_at, field="ProjectionRebuild.started_at")
        if self.completed_at is not None:
            require_timezone(self.completed_at, field="ProjectionRebuild.completed_at")
        if self.to_position < self.from_position:
            raise ValueError("a rebuild range is ascending")

    def completed(
        self, *, at: datetime, succeeded: bool, records_rebuilt: int
    ) -> ProjectionRebuild:
        return replace(
            self,
            completed_at=require_timezone(at, field="at"),
            succeeded=succeeded,
            records_rebuilt=records_rebuilt,
        )

    def require_succeeded(self) -> None:
        if self.succeeded is not True:
            raise ProjectionRebuildFailedError(
                f"rebuild {self.rebuild_id} of projection {self.projection_id} did not "
                f"complete; the projection is marked failed and stale rather than silently "
                f"serving partial data"
            )


@dataclass(frozen=True, slots=True)
class DeletionTombstone:
    """A record that something was deleted, without preserving what
    (`P13-RET-003`)."""

    tombstone_id: UUID
    source_record_id: UUID
    scope: OrganizationScopeReference
    source_decision_reference: UUID
    applied_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.applied_at, field="DeletionTombstone.applied_at")


@dataclass(frozen=True, slots=True)
class ProjectionEvidence:
    """Evidence that a propagation happened (`P13-PROJ-009`)."""

    evidence_reference: EvidenceReference
    projection_id: UUID
    source_record_id: UUID
    propagated_at: datetime
    outcome: str

    def __post_init__(self) -> None:
        require_timezone(self.propagated_at, field="ProjectionEvidence.propagated_at")


@dataclass(frozen=True, slots=True)
class DeletionPropagation:
    """One source deletion's journey into one projection."""

    projection_id: UUID
    source_record_id: UUID
    tombstone: DeletionTombstone | None
    evidence: ProjectionEvidence | None
    source_under_legal_hold: bool = False

    def require_propagated(self) -> None:
        """Refuse to report a deletion complete before it reached the
        projection.

        A legal hold changes the answer rather than the obligation: a
        held record is *preserved*, and the hold authorizes no access to
        it (`P13-PROJ-010`, `P13-RET-005`)."""
        if self.source_under_legal_hold:
            raise RecordUnderLegalHoldError(
                f"source record {self.source_record_id} is under legal hold, so the "
                f"projection preserves it; the hold does not authorize reading it"
            )
        if self.tombstone is None or self.evidence is None:
            raise ProjectionDeletionNotPropagatedError(
                f"projection {self.projection_id}: the deletion of source record "
                f"{self.source_record_id} has not reached it with a tombstone and evidence; "
                f"a projection that outlives its source is an undeletable copy"
            )


@dataclass(frozen=True, slots=True)
class ProjectedRow:
    """One row a projection holds.

    Construction enforces the two invariants that a projection is most
    likely to lose: **organizational scope is carried into every
    projection** (`P13-PROJ-011`), and **no global identity bridge**
    appears in the projected values (`P13-PROJ-006`)."""

    projection_id: UUID
    row_key: str
    scope: OrganizationScopeReference
    values: Mapping[str, str]
    source_schema_version_id: UUID

    def __post_init__(self) -> None:
        require_organization_scope(self.scope, context=f"projected row {self.row_key!r}")
        reject_prohibited_payload_keys(
            dict(self.values), context=f"projection row {self.row_key!r}"
        )


def require_authoritative_source(*, reading_projection: bool, context: str) -> None:
    """Refuse a legal-effect decision taken against a read model.

    Called from the decision path rather than from the projection: the
    projection cannot know why it is being read, and the decision knows
    exactly what it is about to do (`P13-PROJ-003`)."""
    if reading_projection:
        raise ProjectionNotAuthoritativeError(
            f"{context}: a decision with legal effect reads the authoritative record, never a "
            f"projection; the read model is derived and creates no legal effect"
        )

"""Search and export integration contracts (PACK-13 §22, §23).

**PACK-12 remains the policy owner of both.** This module supplies
delivery and persistence contracts and does not restate, extend or relax
a single PACK-12 rule (`P13-SRCH-001`, `P13-EXPORT-001`). Everything here
is a place for a value PACK-12's own rules read.

Search (§22). A search projection carries **index version**, **source
version** and **authorization version**, so PACK-12's staleness and
cache-partitioning rules have real values rather than assumptions.
Deletion produces an index tombstone and index-removal evidence
referencing the source decision. The search engine is **never an
authoritative source** (`P13-SRCH-007`): it holds pointers and permitted
fields, and the truth stays with the owning domain.

Export (§23). Export request persistence, an **immutable manifest**,
artifact metadata, delivery reference, access evidence, expiry,
revocation, destruction attestation and cumulative release history —
each persisted with the semantics PACK-12 defines. And the single most
important refusal in this module: **there is no raw database export
bypass** (`P13-EXPORT-004`). A dump, replica, backup extract or analytics
copy is not an export route, and `reject_raw_export_route` says so with
its own reason code.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    ClassificationReference,
    DomainReference,
    EvidenceReference,
    OrganizationScopeReference,
    RetentionScheduleReference,
    reject_prohibited_payload_keys,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    CrossDomainDirectAccessDeniedError,
    ProjectionDeletionNotPropagatedError,
    ProjectionStaleError,
    RawExportProhibitedError,
)

# ---------------------------------------------------------------------------
# Search integration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SearchProjectionVersions:
    """The three versions `P13-SRCH-002` requires a search projection to
    carry.

    Three separate values, because they answer three separate questions:
    *which index shape is this*, *which revision of the source is
    reflected*, and *which authorization snapshot was applied*. A single
    "version" would make an authorization change indistinguishable from a
    content change, which is exactly the case PACK-12's re-resolution
    rules exist for."""

    index_version: str
    source_version: int
    authorization_version: str

    def __post_init__(self) -> None:
        if not self.index_version or not self.authorization_version:
            raise ValueError("index_version and authorization_version must not be empty")
        if self.source_version < 0:
            raise ValueError("source_version must not be negative")


@dataclass(frozen=True, slots=True)
class SearchProjectionUpdate:
    """One update to the search projection.

    The payload guard runs here as well as at the outbox: a search
    projection is the one derived store most likely to be handed a
    convenient bundle of personal fields (`P13-SRCH-006` keeps unrelated
    domains out of it; this keeps forbidden keys out)."""

    projection_id: UUID
    source_record_id: UUID
    owning_domain: DomainReference
    scope: OrganizationScopeReference
    versions: SearchProjectionVersions
    permitted_fields: Mapping[str, str]
    updated_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.updated_at, field="SearchProjectionUpdate.updated_at")
        reject_prohibited_payload_keys(
            dict(self.permitted_fields),
            context=f"search projection update for {self.source_record_id}",
        )


def reject_foreign_domain_index_write(
    update: SearchProjectionUpdate, *, writing_domain: DomainReference
) -> None:
    """No unrelated domain writes to the search engine
    (`P13-SRCH-006`)."""
    if update.owning_domain.domain_name != writing_domain.domain_name:
        raise CrossDomainDirectAccessDeniedError(
            f"{writing_domain.domain_name!r} attempted to write a search projection owned by "
            f"{update.owning_domain.domain_name!r}; the index is written by the owner of the "
            f"source, never by an unrelated domain"
        )


@dataclass(frozen=True, slots=True)
class SearchIndexTombstone:
    """The tombstone a deletion produces (`P13-SRCH-003`)."""

    tombstone_id: UUID
    source_record_id: UUID
    scope: OrganizationScopeReference
    source_decision_reference: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.created_at, field="SearchIndexTombstone.created_at")


@dataclass(frozen=True, slots=True)
class IndexRemovalEvidence:
    """Evidence that the record left the index, referencing the source
    decision (`P13-SRCH-003`, PACK-12 `P12-SRCH-015`)."""

    evidence: EvidenceReference
    tombstone_id: UUID
    removed_at: datetime
    source_decision_reference: UUID

    def __post_init__(self) -> None:
        require_timezone(self.removed_at, field="IndexRemovalEvidence.removed_at")


@dataclass(frozen=True, slots=True)
class ReindexRequest:
    """Reindex is a governed operation with its own event
    (`P13-SRCH-004`)."""

    reindex_id: UUID
    projection_id: UUID
    requested_by: ActorReference
    scope: OrganizationScopeReference
    requested_at: datetime
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, field="ReindexRequest.requested_at")


class SearchProjectionFailure(StrEnum):
    NONE = "none"
    UPDATE_FAILED = "update_failed"
    REBUILD_REQUIRED = "rebuild_required"
    TOMBSTONE_NOT_APPLIED = "tombstone_not_applied"


@dataclass(frozen=True, slots=True)
class SearchProjectionState:
    """What the PACK-12 search path reads before serving a result.

    `authoritative` is fixed to `False` and validated, because
    `P13-SRCH-007` is the kind of rule that erodes: an index that is fast
    and complete starts being treated as the source."""

    projection_id: UUID
    lag_events: int
    max_acceptable_lag_events: int
    failure: SearchProjectionFailure = SearchProjectionFailure.NONE
    authoritative: bool = False

    def __post_init__(self) -> None:
        if self.authoritative:
            raise ValueError(
                "the search engine is never an authoritative source; it holds pointers and "
                "permitted fields, and the truth stays with the owning domain (P13-SRCH-007)"
            )

    def require_serveable(self, *, context: str) -> None:
        """Expose lag to the search path (`P13-SRCH-005`) and refuse when
        it is past what the caller accepts."""
        if self.failure is SearchProjectionFailure.TOMBSTONE_NOT_APPLIED:
            raise ProjectionDeletionNotPropagatedError(
                f"{context}: an index tombstone has not been applied to projection "
                f"{self.projection_id}; a deleted record must not remain findable"
            )
        if self.lag_events > self.max_acceptable_lag_events:
            raise ProjectionStaleError(
                f"{context}: search projection {self.projection_id} is {self.lag_events} "
                f"events behind, past the {self.max_acceptable_lag_events} this path accepts"
            )


# ---------------------------------------------------------------------------
# Export integration
# ---------------------------------------------------------------------------


class ExportRequestStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    GENERATED = "generated"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DESTROYED = "destroyed"


@dataclass(frozen=True, slots=True)
class ExportManifest:
    """The immutable manifest (`P13-EXPORT-002`).

    Frozen and digest-bearing: a manifest that could be edited after
    generation would make every downstream attestation meaningless."""

    manifest_id: UUID
    content_digest: str
    generated_at: datetime
    item_count: int

    def __post_init__(self) -> None:
        require_timezone(self.generated_at, field="ExportManifest.generated_at")
        if len(self.content_digest) != 64:
            raise ValueError("an export manifest carries a SHA-256 content digest")
        if self.item_count < 0:
            raise ValueError("item_count must not be negative")


@dataclass(frozen=True, slots=True)
class ExportArtifactMetadata:
    """Metadata about the produced artifact — never its bytes."""

    artifact_id: UUID
    manifest_id: UUID
    byte_size: int
    classification: ClassificationReference
    retention_schedule: RetentionScheduleReference

    def __post_init__(self) -> None:
        if self.byte_size < 0:
            raise ValueError("byte_size must not be negative")


@dataclass(frozen=True, slots=True)
class ExportDeliveryReference:
    """Where and when the artifact was delivered. An opaque reference,
    never a credential or a link containing one."""

    delivery_id: UUID
    recipient_reference: UUID
    delivered_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.delivered_at, field="ExportDeliveryReference.delivered_at")


@dataclass(frozen=True, slots=True)
class ExportAccessEvidence:
    """One recorded access to a delivered artifact."""

    access_id: UUID
    artifact_id: UUID
    accessed_by: ActorReference
    accessed_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.accessed_at, field="ExportAccessEvidence.accessed_at")


@dataclass(frozen=True, slots=True)
class ExportDestructionAttestation:
    """A recipient's statement that the copy was destroyed.

    A statement, not a verified fact — PACK-12 says so and this package
    does not upgrade it. The field name says `attested_by`, not
    `verified_by`, for that reason."""

    attestation_id: UUID
    artifact_id: UUID
    attested_by: ActorReference
    attested_at: datetime
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        require_timezone(self.attested_at, field="ExportDestructionAttestation.attested_at")


@dataclass(frozen=True, slots=True)
class CumulativeReleaseHistoryEntry:
    """One entry in the cumulative release history PACK-12's disclosure
    control reads (`FIR-INV-011`)."""

    entry_id: UUID
    export_request_id: UUID
    scope: OrganizationScopeReference
    released_at: datetime
    cohort_reference: UUID

    def __post_init__(self) -> None:
        require_timezone(self.released_at, field="CumulativeReleaseHistoryEntry.released_at")


@dataclass(frozen=True, slots=True)
class ExportRequestRecord:
    """The persisted export request and its lifecycle.

    Every transition is explicit and none is reversible into an earlier
    state: a revoked export does not become delivered again."""

    export_request_id: UUID
    requested_by: ActorReference
    scope: OrganizationScopeReference
    status: ExportRequestStatus
    requested_at: datetime
    expires_at: datetime
    manifest: ExportManifest | None = None
    artifact: ExportArtifactMetadata | None = None
    delivery: ExportDeliveryReference | None = None
    revoked_at: datetime | None = None
    destruction: ExportDestructionAttestation | None = None

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, field="ExportRequestRecord.requested_at")
        require_timezone(self.expires_at, field="ExportRequestRecord.expires_at")
        if self.expires_at <= self.requested_at:
            raise ValueError("an export request expires after it is made")
        if self.revoked_at is not None:
            require_timezone(self.revoked_at, field="ExportRequestRecord.revoked_at")

    def with_manifest(self, manifest: ExportManifest) -> ExportRequestRecord:
        """Attach the immutable manifest.

        Refuses to replace an existing one: `P13-EXPORT-002`'s manifest
        is immutable, and a replacement path would be the only way that
        immutability could be lost."""
        if self.manifest is not None:
            raise RawExportProhibitedError(
                f"export request {self.export_request_id} already carries manifest "
                f"{self.manifest.manifest_id}; an export manifest is immutable"
            )
        return replace(self, manifest=manifest, status=ExportRequestStatus.GENERATED)

    def revoked(self, *, at: datetime) -> ExportRequestRecord:
        return replace(
            self,
            status=ExportRequestStatus.REVOKED,
            revoked_at=require_timezone(at, field="at"),
        )


class ExportRoute(StrEnum):
    """Every way data could leave the data plane.

    Exactly one is an export route. The others are enumerated here so
    that "there is no raw database export bypass" is a checkable claim
    rather than a sentence in a document (`P13-EXPORT-004`)."""

    GOVERNED_EXPORT = "governed_export"
    DATABASE_DUMP = "database_dump"
    READ_REPLICA_QUERY = "read_replica_query"
    BACKUP_EXTRACT = "backup_extract"
    ANALYTICS_COPY = "analytics_copy"
    DIRECT_TABLE_READ = "direct_table_read"


#: The only admissible route. A frozenset of one, so that widening it is
#: a visible change to a named constant.
ADMISSIBLE_EXPORT_ROUTES: frozenset[ExportRoute] = frozenset({ExportRoute.GOVERNED_EXPORT})


def reject_raw_export_route(route: ExportRoute, *, context: str) -> None:
    """Refuse any path that produces data for a recipient outside
    PACK-12's governed export.

    This is the single most likely way the export controls get defeated,
    and it is defeated by infrastructure, not by application code — so
    this refusal is a backstop that names the route, not the whole
    control."""
    if route not in ADMISSIBLE_EXPORT_ROUTES:
        raise RawExportProhibitedError(
            f"{context}: {route.value!r} is not an export route; any path producing data for "
            f"a recipient goes through PACK-12's governed export (P13-EXPORT-004)"
        )

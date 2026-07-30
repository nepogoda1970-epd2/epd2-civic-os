"""Search and export integration contracts (PACK-13 §22, §23).

PACK-12 remains the policy owner of both. These tests assert the
*contracts* PACK-13 supplies, and above all the one refusal that keeps
the export controls from being defeated: there is no raw database export
bypass.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import (
    NOW,
    OTHER_DOMAIN,
    OWNER_DOMAIN,
    actor,
    classification,
    evidence,
    retention,
    scope,
    uid,
)

from epd2_data_plane_service.exceptions import (
    CrossDomainDirectAccessDeniedError,
    GlobalUserIdentifierProhibitedError,
    ProjectionDeletionNotPropagatedError,
    ProjectionStaleError,
    RawExportProhibitedError,
)
from epd2_data_plane_service.integration import (
    ADMISSIBLE_EXPORT_ROUTES,
    CumulativeReleaseHistoryEntry,
    ExportArtifactMetadata,
    ExportDeliveryReference,
    ExportDestructionAttestation,
    ExportManifest,
    ExportRequestRecord,
    ExportRequestStatus,
    ExportRoute,
    IndexRemovalEvidence,
    ReindexRequest,
    SearchIndexTombstone,
    SearchProjectionFailure,
    SearchProjectionState,
    SearchProjectionUpdate,
    SearchProjectionVersions,
    reject_foreign_domain_index_write,
    reject_raw_export_route,
)


def _versions() -> SearchProjectionVersions:
    return SearchProjectionVersions(
        index_version="idx-3", source_version=17, authorization_version="authz-2"
    )


def _update(fields: dict[str, str] | None = None) -> SearchProjectionUpdate:
    return SearchProjectionUpdate(
        projection_id=uid(5100),
        source_record_id=uid(5101),
        owning_domain=OWNER_DOMAIN,
        scope=scope(),
        versions=_versions(),
        permitted_fields=fields or {"title": "Membership record"},
        updated_at=NOW,
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_a_search_projection_carries_three_distinct_versions() -> None:
    """`P13-SRCH-002`: index version, source version and authorization
    version answer three separate questions."""
    versions = _versions()
    assert versions.index_version == "idx-3"
    assert versions.source_version == 17
    assert versions.authorization_version == "authz-2"


def test_the_three_versions_are_all_required() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        SearchProjectionVersions(index_version="", source_version=1, authorization_version="a")


def test_a_search_projection_update_rejects_a_person_key() -> None:
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        _update({"email": "a@b.c"})


def test_no_unrelated_domain_writes_to_the_search_engine() -> None:
    """`P13-SRCH-006`."""
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        reject_foreign_domain_index_write(_update(), writing_domain=OTHER_DOMAIN)


def test_the_owning_domain_writes_its_own_projection() -> None:
    reject_foreign_domain_index_write(_update(), writing_domain=OWNER_DOMAIN)


def test_the_search_engine_is_never_authoritative() -> None:
    """`P13-SRCH-007`: it holds pointers and permitted fields; the truth
    stays with the owning domain."""
    with pytest.raises(ValueError, match="never an authoritative source"):
        SearchProjectionState(
            projection_id=uid(5100),
            lag_events=0,
            max_acceptable_lag_events=10,
            authoritative=True,
        )


def test_search_lag_is_exposed_to_the_search_path() -> None:
    """`P13-SRCH-005`."""
    state = SearchProjectionState(
        projection_id=uid(5100), lag_events=50, max_acceptable_lag_events=10
    )
    with pytest.raises(ProjectionStaleError):
        state.require_serveable(context="query")


def test_an_unapplied_tombstone_blocks_serving() -> None:
    """A deleted record must not remain findable (`P13-SRCH-003`)."""
    state = SearchProjectionState(
        projection_id=uid(5100),
        lag_events=0,
        max_acceptable_lag_events=10,
        failure=SearchProjectionFailure.TOMBSTONE_NOT_APPLIED,
    )
    with pytest.raises(ProjectionDeletionNotPropagatedError):
        state.require_serveable(context="query")


def test_a_fresh_healthy_index_serves() -> None:
    SearchProjectionState(
        projection_id=uid(5100), lag_events=0, max_acceptable_lag_events=10
    ).require_serveable(context="query")


def test_deletion_produces_a_tombstone_and_index_removal_evidence() -> None:
    tombstone = SearchIndexTombstone(
        tombstone_id=uid(5200),
        source_record_id=uid(5101),
        scope=scope(),
        source_decision_reference=uid(5202),
        created_at=NOW,
    )
    removal = IndexRemovalEvidence(
        evidence=evidence(),
        tombstone_id=tombstone.tombstone_id,
        removed_at=NOW,
        source_decision_reference=tombstone.source_decision_reference,
    )
    assert removal.source_decision_reference == uid(5202)


def test_reindex_is_a_governed_operation_with_a_reason_code() -> None:
    request = ReindexRequest(
        reindex_id=uid(5300),
        projection_id=uid(5100),
        requested_by=actor(),
        scope=scope(),
        requested_at=NOW,
        reason_code="PROJECTION_REBUILD_REQUIRED",
    )
    assert request.reason_code == "PROJECTION_REBUILD_REQUIRED"


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def _request() -> ExportRequestRecord:
    return ExportRequestRecord(
        export_request_id=uid(5400),
        requested_by=actor(),
        scope=scope(),
        status=ExportRequestStatus.APPROVED,
        requested_at=NOW,
        expires_at=NOW + timedelta(days=7),
    )


def _manifest(*, n: int = 1) -> ExportManifest:
    return ExportManifest(
        manifest_id=uid(5500 + n),
        content_digest=f"{n}" * 64,
        generated_at=NOW,
        item_count=12,
    )


def test_only_the_governed_export_route_is_admissible() -> None:
    """`P13-EXPORT-004`: a dump, replica, backup extract or analytics
    copy is not an export route."""
    assert frozenset({ExportRoute.GOVERNED_EXPORT}) == ADMISSIBLE_EXPORT_ROUTES
    for route in ExportRoute:
        if route is ExportRoute.GOVERNED_EXPORT:
            reject_raw_export_route(route, context="export")
        else:
            with pytest.raises(RawExportProhibitedError):
                reject_raw_export_route(route, context="export")


def test_every_non_export_route_is_enumerated_by_name() -> None:
    names = {r.value for r in ExportRoute}
    assert {"database_dump", "read_replica_query", "backup_extract", "analytics_copy"} <= names


def test_an_export_manifest_is_immutable_once_attached() -> None:
    """`P13-EXPORT-002`."""
    record = _request().with_manifest(_manifest())
    assert record.status is ExportRequestStatus.GENERATED
    with pytest.raises(RawExportProhibitedError, match="immutable"):
        record.with_manifest(_manifest(n=2))


def test_a_manifest_carries_a_sha256_digest() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        ExportManifest(
            manifest_id=uid(5500), content_digest="short", generated_at=NOW, item_count=1
        )


def test_an_export_request_expires_after_it_is_made() -> None:
    with pytest.raises(ValueError, match="expires after"):
        ExportRequestRecord(
            export_request_id=uid(5400),
            requested_by=actor(),
            scope=scope(),
            status=ExportRequestStatus.REQUESTED,
            requested_at=NOW,
            expires_at=NOW,
        )


def test_revocation_moves_the_request_and_records_when() -> None:
    revoked = _request().revoked(at=NOW + timedelta(days=1))
    assert revoked.status is ExportRequestStatus.REVOKED
    assert revoked.revoked_at == NOW + timedelta(days=1)


def test_artifact_metadata_carries_no_bytes() -> None:
    metadata = ExportArtifactMetadata(
        artifact_id=uid(5600),
        manifest_id=uid(5501),
        byte_size=1024,
        classification=classification(),
        retention_schedule=retention(),
    )
    assert "artifact_bytes" not in metadata.__slots__
    assert "payload" not in metadata.__slots__


def test_a_delivery_reference_is_opaque() -> None:
    reference = ExportDeliveryReference(
        delivery_id=uid(5700), recipient_reference=uid(5701), delivered_at=NOW
    )
    assert "url" not in reference.__slots__
    assert "token" not in reference.__slots__


def test_a_destruction_attestation_is_attested_not_verified() -> None:
    """PACK-12 says a destruction attestation is a recipient's statement,
    not a verified fact; PACK-13 does not upgrade it."""
    attestation = ExportDestructionAttestation(
        attestation_id=uid(5800),
        artifact_id=uid(5600),
        attested_by=actor(),
        attested_at=NOW,
        evidence=evidence(),
    )
    assert "attested_by" in attestation.__slots__
    assert "verified_by" not in attestation.__slots__


def test_the_cumulative_release_history_is_scoped_and_dated() -> None:
    entry = CumulativeReleaseHistoryEntry(
        entry_id=uid(5900),
        export_request_id=uid(5400),
        scope=scope(),
        released_at=NOW,
        cohort_reference=uid(5901),
    )
    assert entry.scope.organization_id == scope().organization_id

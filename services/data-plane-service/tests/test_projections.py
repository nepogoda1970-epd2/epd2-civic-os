"""Projection and read-model governance (PACK-13 §21; ADR-076).

Rebuild, lag, stale state, deletion propagation, legal hold and
authorization preservation — the six things a read model must not
quietly become.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import (
    NOW,
    OTHER_DOMAIN,
    OWNER_DOMAIN,
    evidence,
    scope,
    uid,
)

from epd2_data_plane_service.domain import DomainReference
from epd2_data_plane_service.exceptions import (
    GlobalUserIdentifierProhibitedError,
    ProjectionAuthorizationWideningProhibitedError,
    ProjectionDeletionNotPropagatedError,
    ProjectionNotAuthoritativeError,
    ProjectionRebuildFailedError,
    ProjectionRebuildRequiredError,
    ProjectionStaleError,
    RecordUnderLegalHoldError,
    VotingMaterialProhibitedError,
)
from epd2_data_plane_service.projections import (
    AuthorizationTier,
    DeletionPropagation,
    DeletionTombstone,
    ProjectedRow,
    ProjectionDefinition,
    ProjectionEvidence,
    ProjectionHealth,
    ProjectionLag,
    ProjectionRebuild,
    ProjectionSource,
    ProjectionStaleness,
    RebuildStrategy,
    narrowest_tier,
    require_authoritative_source,
)


def _source(
    *,
    domain: DomainReference = OWNER_DOMAIN,
    tier: AuthorizationTier = AuthorizationTier.ORGANIZATION_MEMBER,
    approval: str | None = None,
) -> ProjectionSource:
    return ProjectionSource(
        owning_domain=domain,
        event_families=("membership.recorded",),
        authorization_tier=tier,
        adr_approval_reference=approval,
    )


def _definition(
    *, sources: tuple[ProjectionSource, ...] | None = None, max_lag: int = 5
) -> ProjectionDefinition:
    return ProjectionDefinition(
        projection_id=uid(4400),
        projection_name="membership-overview",
        owner=OWNER_DOMAIN,
        sources=sources or (_source(),),
        schema_version_id=uid(4401),
        rebuild_strategy=RebuildStrategy.FROM_SOURCE_EVENTS,
        max_acceptable_lag_events=max_lag,
    )


def _staleness(events_behind: int, health: ProjectionHealth) -> ProjectionStaleness:
    return ProjectionStaleness(
        projection_id=uid(4400),
        health=health,
        lag=ProjectionLag(
            projection_id=uid(4400),
            events_behind=events_behind,
            lag_band="low",
            observed_at=NOW,
        ),
        max_acceptable_lag_events=5,
    )


# ---------------------------------------------------------------------------
# Declaration
# ---------------------------------------------------------------------------


def test_a_projection_declares_owner_sources_schema_and_rebuild_strategy() -> None:
    definition = _definition()
    assert definition.owner.domain_name == OWNER_DOMAIN.domain_name
    assert definition.sources[0].event_families
    assert definition.schema_version_id
    assert definition.rebuild_strategy is RebuildStrategy.FROM_SOURCE_EVENTS


def test_a_projection_declaring_itself_authoritative_cannot_exist() -> None:
    """`P13-PROJ-002`: a read model is not authoritative."""
    with pytest.raises(ProjectionNotAuthoritativeError):
        ProjectionDefinition(
            projection_id=uid(4400),
            projection_name="p",
            owner=OWNER_DOMAIN,
            sources=(_source(),),
            schema_version_id=uid(1),
            rebuild_strategy=RebuildStrategy.FROM_SOURCE_EVENTS,
            max_acceptable_lag_events=0,
            authoritative=True,
        )


def test_a_projection_without_declared_sources_cannot_exist() -> None:
    with pytest.raises(ValueError, match="declares its source events"):
        ProjectionDefinition(
            projection_id=uid(4400),
            projection_name="p",
            owner=OWNER_DOMAIN,
            sources=(),
            schema_version_id=uid(1),
            rebuild_strategy=RebuildStrategy.FROM_SOURCE_EVENTS,
            max_acceptable_lag_events=0,
        )


def test_a_source_declares_at_least_one_event_family() -> None:
    with pytest.raises(ValueError, match="at least one event family"):
        ProjectionSource(
            owning_domain=OWNER_DOMAIN,
            event_families=(),
            authorization_tier=AuthorizationTier.PUBLIC,
        )


# ---------------------------------------------------------------------------
# Cross-domain and authorization
# ---------------------------------------------------------------------------


def test_a_multi_domain_projection_without_every_owners_approval_is_refused() -> None:
    """`P13-PROJ-005`: admissible only where every source domain has
    approved that specific projection under ADR."""
    with pytest.raises(ProjectionAuthorizationWideningProhibitedError):
        _definition(
            sources=(
                _source(approval="ADR-076-a"),
                _source(domain=OTHER_DOMAIN, approval=None),
            )
        )


def test_a_multi_domain_projection_with_every_approval_constructs() -> None:
    definition = _definition(
        sources=(
            _source(approval="ADR-076-a"),
            _source(domain=OTHER_DOMAIN, approval="ADR-076-b"),
        )
    )
    assert definition.is_multi_domain


def test_the_effective_authorization_is_the_narrowest_of_the_inputs() -> None:
    definition = _definition(
        sources=(
            _source(tier=AuthorizationTier.PUBLIC, approval="a"),
            _source(domain=OTHER_DOMAIN, tier=AuthorizationTier.PRIVILEGED, approval="b"),
        )
    )
    assert definition.effective_authorization_tier is AuthorizationTier.PRIVILEGED


def test_a_reader_below_the_narrowest_tier_is_refused() -> None:
    """`P13-PROJ-004`: if the reader could not read the source, the
    projection does not let them read the derivative."""
    definition = _definition(sources=(_source(tier=AuthorizationTier.PRIVILEGED),))
    with pytest.raises(ProjectionAuthorizationWideningProhibitedError):
        definition.require_no_authorization_widening(AuthorizationTier.ORGANIZATION_MEMBER)


def test_a_reader_at_or_above_the_tier_is_admitted() -> None:
    definition = _definition(sources=(_source(tier=AuthorizationTier.ROLE_RESTRICTED),))
    definition.require_no_authorization_widening(AuthorizationTier.PRIVILEGED)


def test_narrowest_tier_requires_at_least_one_source() -> None:
    with pytest.raises(ValueError, match="at least one source"):
        narrowest_tier([])


# ---------------------------------------------------------------------------
# Rows: scope and prohibited keys
# ---------------------------------------------------------------------------


def test_organizational_scope_is_carried_into_every_projected_row() -> None:
    row = ProjectedRow(
        projection_id=uid(4400),
        row_key="m-1",
        scope=scope(),
        values={"status": "active"},
        source_schema_version_id=uid(4401),
    )
    assert row.scope.organization_id == scope().organization_id


def test_a_projected_row_never_carries_a_global_identity_bridge() -> None:
    """`P13-PROJ-006`: a projection is exactly where the separation that
    schemas enforce could be reconstituted."""
    with pytest.raises(GlobalUserIdentifierProhibitedError):
        ProjectedRow(
            projection_id=uid(4400),
            row_key="m-1",
            scope=scope(),
            values={"person_id": "x"},
            source_schema_version_id=uid(4401),
        )


def test_a_projected_row_never_carries_voting_material() -> None:
    with pytest.raises(VotingMaterialProhibitedError):
        ProjectedRow(
            projection_id=uid(4400),
            row_key="m-1",
            scope=scope(),
            values={"tally": "3"},
            source_schema_version_id=uid(4401),
        )


# ---------------------------------------------------------------------------
# Staleness and rebuild
# ---------------------------------------------------------------------------


def test_a_healthy_projection_is_acceptable_for_consequential_use() -> None:
    _staleness(0, ProjectionHealth.HEALTHY).require_acceptable_for_consequential_use(
        context="decision"
    )


def test_an_over_lagged_projection_blocks_consequential_use() -> None:
    """`P13-PROJ-008`: the decision path reads the lag rather than
    assuming freshness."""
    with pytest.raises(ProjectionStaleError):
        _staleness(9, ProjectionHealth.STALE).require_acceptable_for_consequential_use(
            context="decision"
        )


def test_a_projection_requiring_rebuild_cannot_serve() -> None:
    with pytest.raises(ProjectionRebuildRequiredError):
        _staleness(0, ProjectionHealth.REBUILD_REQUIRED).require_acceptable_for_consequential_use(
            context="decision"
        )


def test_a_failed_projection_cannot_serve() -> None:
    with pytest.raises(ProjectionRebuildRequiredError):
        _staleness(0, ProjectionHealth.FAILED).require_acceptable_for_consequential_use(
            context="decision"
        )


def test_a_lagging_but_within_threshold_projection_is_not_acceptable_when_unhealthy() -> None:
    assert not _staleness(2, ProjectionHealth.LAGGING).acceptable_for_consequential_use


def test_a_completed_rebuild_records_its_outcome() -> None:
    rebuild = ProjectionRebuild(
        rebuild_id=uid(4500),
        projection_id=uid(4400),
        from_position=0,
        to_position=100,
        started_at=NOW,
    ).completed(at=NOW, succeeded=True, records_rebuilt=100)
    rebuild.require_succeeded()
    assert rebuild.records_rebuilt == 100


def test_an_incomplete_rebuild_is_marked_failed_rather_than_serving() -> None:
    rebuild = ProjectionRebuild(
        rebuild_id=uid(4500),
        projection_id=uid(4400),
        from_position=0,
        to_position=100,
        started_at=NOW,
    )
    with pytest.raises(ProjectionRebuildFailedError):
        rebuild.require_succeeded()


def test_a_rebuild_range_is_ascending() -> None:
    with pytest.raises(ValueError, match="ascending"):
        ProjectionRebuild(
            rebuild_id=uid(4500),
            projection_id=uid(4400),
            from_position=10,
            to_position=1,
            started_at=NOW,
        )


def test_lag_is_never_negative() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        ProjectionLag(projection_id=uid(4400), events_behind=-1, lag_band="none", observed_at=NOW)


# ---------------------------------------------------------------------------
# Deletion propagation and legal hold
# ---------------------------------------------------------------------------


def _tombstone() -> DeletionTombstone:
    return DeletionTombstone(
        tombstone_id=uid(4600),
        source_record_id=uid(4601),
        scope=scope(),
        source_decision_reference=uid(4602),
        applied_at=NOW,
    )


def _projection_evidence() -> ProjectionEvidence:
    return ProjectionEvidence(
        evidence_reference=evidence(),
        projection_id=uid(4400),
        source_record_id=uid(4601),
        propagated_at=NOW,
        outcome="propagated",
    )


def test_a_deletion_that_has_not_reached_the_projection_is_refused() -> None:
    """`P13-PROJ-009`: a projection that outlives its source is an
    undeletable copy."""
    propagation = DeletionPropagation(
        projection_id=uid(4400), source_record_id=uid(4601), tombstone=None, evidence=None
    )
    with pytest.raises(ProjectionDeletionNotPropagatedError):
        propagation.require_propagated()


def test_a_propagated_deletion_carries_a_tombstone_and_evidence() -> None:
    DeletionPropagation(
        projection_id=uid(4400),
        source_record_id=uid(4601),
        tombstone=_tombstone(),
        evidence=_projection_evidence(),
    ).require_propagated()


def test_a_held_source_is_preserved_and_the_hold_authorizes_no_access() -> None:
    """`P13-PROJ-010` with `P13-RET-005`."""
    propagation = DeletionPropagation(
        projection_id=uid(4400),
        source_record_id=uid(4601),
        tombstone=None,
        evidence=None,
        source_under_legal_hold=True,
    )
    with pytest.raises(RecordUnderLegalHoldError, match="does not authorize reading"):
        propagation.require_propagated()


def test_a_tombstone_records_that_something_was_deleted_not_what() -> None:
    """`P13-RET-003`."""
    tombstone = _tombstone()
    assert "values" not in tombstone.__slots__
    assert "content" not in tombstone.__slots__
    assert tombstone.source_decision_reference


# ---------------------------------------------------------------------------
# Legal effect
# ---------------------------------------------------------------------------


def test_a_legal_effect_decision_against_a_read_model_is_refused() -> None:
    with pytest.raises(ProjectionNotAuthoritativeError):
        require_authoritative_source(reading_projection=True, context="governance decision")


def test_a_legal_effect_decision_against_the_authoritative_record_proceeds() -> None:
    require_authoritative_source(reading_projection=False, context="governance decision")

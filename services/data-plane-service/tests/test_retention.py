"""Retention, legal hold and evidence in the data plane
(PACK-13 §24, §25; ADR-078).

The invariant this file exists for, restated once more because the data
plane is exactly where it would be lost: **a legal hold preserves data.
It does not authorize access, search, export or publication.**
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import NOW, actor, evidence, record_class, retention, scope, uid

from epd2_data_plane_service.exceptions import (
    GovernedRecordDeletionForbiddenError,
    LegalHoldStateUnknownError,
    RecordUnderLegalHoldError,
)
from epd2_data_plane_service.retention import (
    REFERENCE_BACKUP_STATEMENT,
    REQUIRED_RETENTION_CLASSES,
    BackupHorizonStatement,
    DeletionDecision,
    DeletionEligibility,
    DeletionEvidence,
    GovernedArtifactEvidence,
    GovernedArtifactKind,
    InfrastructurePersistentClass,
    LegalHoldObservation,
    LegalHoldState,
    RetentionBinding,
    require_evidence_for,
    require_hold_does_not_authorize,
    require_retention_binding,
)


def _binding(
    persistent_class: InfrastructurePersistentClass = InfrastructurePersistentClass.OUTBOX_RECORD,
) -> RetentionBinding:
    return RetentionBinding(
        persistent_class=persistent_class,
        record_class=record_class(),
        retention_schedule=retention(),
        scope=scope(),
    )


def _hold(state: LegalHoldState) -> LegalHoldObservation:
    return LegalHoldObservation(
        record_id=uid(6100),
        state=state,
        observed_at=NOW,
        observed_by=actor(),
        hold_reference=uid(6101) if state is LegalHoldState.HELD else None,
    )


def _decision(
    *, state: LegalHoldState, due: bool = True, governed: bool = False
) -> DeletionDecision:
    return DeletionDecision(
        record_id=uid(6100),
        binding=_binding(),
        hold=_hold(state),
        retention_due=due,
        governed_record=governed,
    )


# ---------------------------------------------------------------------------
# Retention applies to infrastructure
# ---------------------------------------------------------------------------


def test_every_infrastructure_persistent_class_requires_a_binding() -> None:
    """`P13-RET-006`: none is exempt by virtue of being
    infrastructure."""
    assert frozenset(InfrastructurePersistentClass) == REQUIRED_RETENTION_CLASSES


def test_the_four_groups_the_specification_names_are_all_covered() -> None:
    values = {c.value for c in InfrastructurePersistentClass}
    assert "projection_row" in values
    assert "outbox_record" in values
    assert "schema_registry_entry" in values
    assert "migration_evidence" in values


def test_a_missing_binding_is_refused() -> None:
    with pytest.raises(GovernedRecordDeletionForbiddenError, match="no retention binding"):
        require_retention_binding({InfrastructurePersistentClass.OUTBOX_RECORD: _binding()})


def test_a_complete_set_of_bindings_passes() -> None:
    require_retention_binding({cls: _binding(cls) for cls in InfrastructurePersistentClass})


def test_a_retention_binding_has_no_field_that_could_set_a_period() -> None:
    """PACK-09 decides retention; PACK-13 binds."""
    fields = _binding().__slots__
    assert "retention_period" not in fields
    assert "retain_until" not in fields
    assert "retention_schedule" in fields


# ---------------------------------------------------------------------------
# Legal hold
# ---------------------------------------------------------------------------


def test_a_hold_authorizes_nothing() -> None:
    """`P13-RET-005`."""
    observation = _hold(LegalHoldState.HELD)
    assert observation.authorizes_access is False
    require_hold_does_not_authorize(observation, context="investigation")


def test_a_held_record_names_the_hold_that_holds_it() -> None:
    with pytest.raises(LegalHoldStateUnknownError):
        LegalHoldObservation(
            record_id=uid(6100),
            state=LegalHoldState.HELD,
            observed_at=NOW,
            observed_by=actor(),
            hold_reference=None,
        )


def test_unknown_is_a_real_hold_state_not_an_absence() -> None:
    """§29: deletion does not proceed where hold state is unknown."""
    assert LegalHoldState.UNKNOWN in set(LegalHoldState)
    decision = _decision(state=LegalHoldState.UNKNOWN)
    assert decision.eligibility is DeletionEligibility.BLOCKED_UNKNOWN_HOLD_STATE


def test_an_unknown_hold_state_fails_closed() -> None:
    with pytest.raises(LegalHoldStateUnknownError):
        _decision(state=LegalHoldState.UNKNOWN).require_eligible(context="deletion job")


def test_a_held_record_is_preserved() -> None:
    with pytest.raises(RecordUnderLegalHoldError, match="authorizes no access"):
        _decision(state=LegalHoldState.HELD).require_eligible(context="deletion job")


def test_a_governed_record_is_disposed_of_through_pack_09s_process() -> None:
    with pytest.raises(GovernedRecordDeletionForbiddenError, match="governed record"):
        _decision(state=LegalHoldState.NOT_HELD, governed=True).require_eligible(
            context="deletion job"
        )


def test_a_record_not_yet_due_is_refused() -> None:
    with pytest.raises(GovernedRecordDeletionForbiddenError, match="not yet due"):
        _decision(state=LegalHoldState.NOT_HELD, due=False).require_eligible(context="deletion job")


def test_an_eligible_record_passes() -> None:
    decision = _decision(state=LegalHoldState.NOT_HELD)
    assert decision.eligibility is DeletionEligibility.ELIGIBLE
    decision.require_eligible(context="deletion job")


def test_deletion_evidence_uses_a_pack_11_reference_not_a_new_store() -> None:
    record = DeletionEvidence(
        evidence=evidence(),
        record_id=uid(6100),
        deleted_at=NOW,
        decided_by=actor(),
        retention_schedule=retention(),
    )
    assert record.evidence.evidence_bundle_id


# ---------------------------------------------------------------------------
# Backup horizon
# ---------------------------------------------------------------------------


def test_a_backup_horizon_states_its_consequence() -> None:
    """`P13-RET-004`: without the consequence, 'we deleted it' quietly
    means 'we deleted one copy'."""
    with pytest.raises(ValueError, match="states its consequence"):
        BackupHorizonStatement(horizon=timedelta(days=30), consequence="")


def test_a_backup_horizon_is_a_positive_duration() -> None:
    with pytest.raises(ValueError, match="positive duration"):
        BackupHorizonStatement(horizon=timedelta(0), consequence="x")


def test_the_reference_statement_says_the_gap_is_open_and_pack_17s() -> None:
    assert REFERENCE_BACKUP_STATEMENT.closed_by_pack == "PACK-17"
    assert "not a closure of the gap" in REFERENCE_BACKUP_STATEMENT.consequence


# ---------------------------------------------------------------------------
# Evidence (PACK-11 remains the owner)
# ---------------------------------------------------------------------------


def test_a_governed_artifact_without_evidence_is_refused() -> None:
    """`P13-DOC-002`, `P13-DOC-003`: an evidence reference, not an ad-hoc
    file path and not nothing."""
    with pytest.raises(GovernedRecordDeletionForbiddenError):
        require_evidence_for(GovernedArtifactKind.MIGRATION_PLAN, None, context="migration plan")


def test_a_governed_artifact_with_evidence_returns_it() -> None:
    reference = require_evidence_for(
        GovernedArtifactKind.SCHEMA_PUBLICATION_DECISION, evidence(), context="publication"
    )
    assert reference.content_digest


def test_replacement_is_supersession_and_never_overwrite() -> None:
    """`P13-DOC-004`: historical schemas remain immutable."""
    artifact = GovernedArtifactEvidence(
        artifact_kind=GovernedArtifactKind.SCHEMA_PUBLICATION_DECISION,
        artifact_id=uid(6200),
        evidence=evidence(),
        recorded_at=NOW,
        supersedes=uid(6199),
    )
    assert artifact.supersedes == uid(6199)
    assert "overwrites" not in artifact.__slots__


def test_an_artifact_does_not_supersede_itself() -> None:
    with pytest.raises(ValueError, match="does not supersede itself"):
        GovernedArtifactEvidence(
            artifact_kind=GovernedArtifactKind.MIGRATION_VERIFICATION,
            artifact_id=uid(6200),
            evidence=evidence(),
            recorded_at=NOW,
            supersedes=uid(6200),
        )


def test_every_governed_data_plane_artifact_kind_is_enumerated() -> None:
    values = {k.value for k in GovernedArtifactKind}
    assert "migration_plan" in values
    assert "migration_verification" in values
    assert "schema_publication_decision" in values
    assert "deletion_propagation" in values

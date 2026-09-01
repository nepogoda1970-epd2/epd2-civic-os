"""Migration discipline (PACK-13 §18, §19; ADR-075).

Immutable applied migrations, checksum mismatch, deterministic ordering,
expand/contract, the destructive approval gate, and the five automated
gates that stand between an approved plan and an irreversible change.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from _data_plane_builders import (
    NOW,
    approval,
    dry_run,
    evidence,
    grant,
    migration_definition,
    migration_plan,
    passing_gates,
    rollback,
    uid,
)

from epd2_data_plane_service.exceptions import (
    MigrationAlreadyAppliedError,
    MigrationChecksumMismatchError,
    MigrationDestructiveNotAuthorizedError,
    MigrationDryRunMissingError,
    MigrationEvidenceLinkageBrokenError,
    MigrationGlobalIdentifierProhibitedError,
    MigrationHoldStateUnknownError,
    MigrationNotApprovedError,
    MigrationObservationPeriodIncompleteError,
    MigrationOrderInvalidError,
    MigrationPartialFailureError,
    MigrationScopeLossDetectedError,
    MigrationSeparationOfDutiesMissingError,
    MigrationVotingUnlinkabilityAtRiskError,
    RollbackUnavailableError,
)
from epd2_data_plane_service.migrations import (
    DESTRUCTIVE_MIGRATION_CLASSES,
    EXPAND_CONTRACT_SEQUENCE,
    MIGRATION_RISK_GATES,
    MINIMUM_OBSERVATION_PERIOD,
    AppliedMigration,
    ExpandContractProgress,
    ExpandContractStep,
    MigrationApproval,
    MigrationClass,
    MigrationDefinition,
    MigrationExecution,
    MigrationExecutionStatus,
    MigrationPlan,
    MigrationRiskGate,
    MigrationRollbackDecision,
    MigrationVerification,
    evaluate_migration_gates,
    reject_out_of_order,
    reject_reapplication,
    require_destructive_authorization,
    require_dual_write_reconciliation,
    verify_checksum,
)


def _applied(
    definition: MigrationDefinition | None = None, *, at: datetime = NOW
) -> AppliedMigration:
    definition = definition or migration_definition()
    return AppliedMigration(
        migration_id=definition.migration_id,
        checksum=definition.checksum,
        ordering_position=definition.ordering_position,
        applied_at=at,
        execution_id=uid(900),
    )


# ---------------------------------------------------------------------------
# Immutability and checksums
# ---------------------------------------------------------------------------


def test_a_checksum_is_computed_from_the_definition_not_supplied() -> None:
    definition = migration_definition()
    assert len(definition.checksum) == 64
    assert definition.checksum == migration_definition().checksum


def test_changing_a_statement_changes_the_checksum() -> None:
    left = migration_definition(statements=("add column a",))
    right = migration_definition(statements=("add column b",))
    assert left.checksum != right.checksum


def test_a_checksum_mismatch_halts_and_is_never_auto_repaired() -> None:
    """`P13-MIG-004`: auto-repair erases the evidence of tampering, so
    there is no repair path in the module at all."""
    original = migration_definition(statements=("add column a",))
    edited = migration_definition(statements=("add column a", "drop column b"))
    with pytest.raises(MigrationChecksumMismatchError):
        verify_checksum(edited, _applied(original))


def test_a_matching_checksum_passes() -> None:
    definition = migration_definition()
    verify_checksum(definition, _applied(definition))


def test_reapplication_of_an_applied_migration_is_refused() -> None:
    definition = migration_definition()
    with pytest.raises(MigrationAlreadyAppliedError):
        reject_reapplication(definition, _applied(definition))


def test_a_never_applied_migration_may_be_applied() -> None:
    reject_reapplication(migration_definition(), None)


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


def test_ordering_is_deterministic_and_declared_not_discovered() -> None:
    plan = migration_plan(
        migrations=(
            migration_definition(migration_id="b", position=2),
            migration_definition(migration_id="a", position=1),
        )
    )
    assert [m.migration_id for m in plan.ordered_migrations] == ["a", "b"]


def test_colliding_ordering_positions_make_a_plan_unconstructable() -> None:
    with pytest.raises(MigrationOrderInvalidError):
        migration_plan(
            migrations=(
                migration_definition(migration_id="a", position=1),
                migration_definition(migration_id="b", position=1),
            )
        )


def test_a_migration_behind_applied_state_is_refused() -> None:
    applied = _applied(migration_definition(migration_id="a", position=5))
    with pytest.raises(MigrationOrderInvalidError):
        reject_out_of_order(migration_definition(migration_id="b", position=3), [applied])


def test_a_migration_ahead_of_applied_state_is_admitted() -> None:
    applied = _applied(migration_definition(migration_id="a", position=5))
    reject_out_of_order(migration_definition(migration_id="b", position=6), [applied])


def test_ordering_position_starts_at_one() -> None:
    with pytest.raises(MigrationOrderInvalidError):
        migration_definition(position=0)


# ---------------------------------------------------------------------------
# The five automated gates
# ---------------------------------------------------------------------------


def test_every_gate_has_a_name_and_all_five_are_enumerated() -> None:
    assert len(MIGRATION_RISK_GATES) == 5
    assert MigrationRiskGate.NO_GLOBAL_IDENTIFIER_CREATED in MIGRATION_RISK_GATES


def test_passing_gates_admit_the_migration() -> None:
    evaluate_migration_gates(passing_gates(), migration_id="m")


def test_a_global_identifier_gate_failure_refuses_first() -> None:
    """Ordered by irreversibility of the harm: an identity correlation is
    what no later migration can undo."""
    from dataclasses import replace

    gates = replace(
        passing_gates(), creates_cross_domain_person_key=True, organization_scope_preserved=False
    )
    with pytest.raises(MigrationGlobalIdentifierProhibitedError):
        evaluate_migration_gates(gates, migration_id="m")


def test_a_voting_unlinkability_gate_failure_is_refused() -> None:
    from dataclasses import replace

    with pytest.raises(MigrationVotingUnlinkabilityAtRiskError):
        evaluate_migration_gates(
            replace(passing_gates(), weakens_ballot_unlinkability=True), migration_id="m"
        )


def test_a_scope_loss_gate_failure_is_refused() -> None:
    from dataclasses import replace

    with pytest.raises(MigrationScopeLossDetectedError):
        evaluate_migration_gates(
            replace(passing_gates(), organization_scope_preserved=False), migration_id="m"
        )


def test_an_unresolved_hold_state_fails_closed() -> None:
    from dataclasses import replace

    with pytest.raises(MigrationHoldStateUnknownError):
        evaluate_migration_gates(
            replace(passing_gates(), legal_hold_state_resolved=False), migration_id="m"
        )


def test_deleting_retention_records_without_a_decision_is_refused() -> None:
    from dataclasses import replace

    with pytest.raises(MigrationHoldStateUnknownError):
        evaluate_migration_gates(
            replace(passing_gates(), retention_records_preserved=False), migration_id="m"
        )


def test_breaking_evidence_linkage_is_refused() -> None:
    from dataclasses import replace

    with pytest.raises(MigrationEvidenceLinkageBrokenError):
        evaluate_migration_gates(
            replace(passing_gates(), evidence_linkage_preserved=False), migration_id="m"
        )


def test_a_verification_must_evaluate_every_gate() -> None:
    with pytest.raises(MigrationScopeLossDetectedError):
        MigrationVerification(
            verification_id=uid(901),
            execution_id=uid(900),
            passed=True,
            gates_evaluated=(MigrationRiskGate.ORGANIZATION_SCOPE_PRESERVED,),
            evidence=evidence(),
            verified_at=NOW,
        )


def test_a_complete_verification_constructs() -> None:
    assert MigrationVerification(
        verification_id=uid(901),
        execution_id=uid(900),
        passed=True,
        gates_evaluated=MIGRATION_RISK_GATES,
        evidence=evidence(),
        verified_at=NOW,
    ).passed


# ---------------------------------------------------------------------------
# Destructive authorization and expand/contract
# ---------------------------------------------------------------------------


def test_a_destructive_class_must_declare_itself_destructive() -> None:
    with pytest.raises(MigrationDestructiveNotAuthorizedError):
        migration_definition(migration_class=MigrationClass.CONTRACT, destructive=False)


def test_the_destructive_classes_include_contract_and_emergency() -> None:
    """An emergency migration is not exempt from approval: break-glass
    adds obligations rather than removing them."""
    assert MigrationClass.CONTRACT in DESTRUCTIVE_MIGRATION_CLASSES
    assert MigrationClass.EMERGENCY in DESTRUCTIVE_MIGRATION_CLASSES


def _contract_plan(**kwargs: object) -> MigrationPlan:
    return migration_plan(
        migration_class=MigrationClass.CONTRACT,
        migrations=(
            migration_definition(
                migration_id="0009_drop_old",
                migration_class=MigrationClass.CONTRACT,
                position=9,
                destructive=True,
            ),
        ),
        **kwargs,  # type: ignore[arg-type]
    )


def test_a_destructive_plan_without_approval_is_refused() -> None:
    with pytest.raises(MigrationNotApprovedError):
        require_destructive_authorization(_contract_plan(), now=NOW)


def test_a_destructive_plan_without_dry_run_evidence_is_refused() -> None:
    with pytest.raises(MigrationDryRunMissingError):
        require_destructive_authorization(_contract_plan(with_approval=True), now=NOW)


def test_a_destructive_plan_before_the_observation_period_is_refused() -> None:
    plan = _contract_plan(
        with_approval=True, with_dry_run=True, old_writes_stopped_at=NOW - timedelta(days=1)
    )
    with pytest.raises(MigrationObservationPeriodIncompleteError):
        require_destructive_authorization(plan, now=NOW)


def test_a_destructive_plan_with_no_recorded_stop_moment_is_refused() -> None:
    plan = _contract_plan(with_approval=True, with_dry_run=True)
    with pytest.raises(MigrationObservationPeriodIncompleteError):
        require_destructive_authorization(plan, now=NOW)


def test_a_destructive_plan_after_the_observation_period_is_authorized() -> None:
    plan = _contract_plan(
        with_approval=True,
        with_dry_run=True,
        old_writes_stopped_at=NOW - MINIMUM_OBSERVATION_PERIOD[MigrationClass.CONTRACT],
    )
    require_destructive_authorization(plan, now=NOW)


def test_a_non_destructive_plan_needs_no_destructive_gate() -> None:
    require_destructive_authorization(migration_plan(), now=NOW)


def test_the_observation_period_is_never_zero_for_contract() -> None:
    """`P13-XC-003`: 'remove the old structure' is never same-day with
    'stop old writes'."""
    assert MINIMUM_OBSERVATION_PERIOD[MigrationClass.CONTRACT] > timedelta(0)


def test_separation_of_duties_is_enforced_on_the_approval_itself() -> None:
    from _data_plane_builders import actor

    with pytest.raises(MigrationSeparationOfDutiesMissingError):
        MigrationApproval(
            approval_id=uid(902),
            proposed_by=actor(1),
            approved_by=actor(1),
            approved_at=NOW,
            evidence=evidence(),
        )


def test_dual_write_without_reconciliation_is_refused() -> None:
    """`P13-XC-002`: two unreconciled writes are two sources of truth
    pretending to be one."""
    with pytest.raises(MigrationNotApprovedError):
        require_dual_write_reconciliation(migration_plan(), dual_write_deployed=True)


def test_dual_write_with_a_reconciliation_strategy_is_admitted() -> None:
    plan = migration_plan(reconciliation="nightly digest comparison with divergence evidence")
    require_dual_write_reconciliation(plan, dual_write_deployed=True)


def test_the_expand_contract_sequence_has_its_nine_steps_in_order() -> None:
    assert len(EXPAND_CONTRACT_SEQUENCE) == 9
    assert EXPAND_CONTRACT_SEQUENCE[0] is ExpandContractStep.ADD_STRUCTURE
    assert EXPAND_CONTRACT_SEQUENCE[-1] is ExpandContractStep.ARCHIVE_EVIDENCE


def test_removing_the_old_structure_requires_its_predecessors() -> None:
    progress = ExpandContractProgress(plan_id=uid(903))
    with pytest.raises(MigrationObservationPeriodIncompleteError):
        progress.require_prerequisites(ExpandContractStep.REMOVE_OLD_STRUCTURE)


def test_a_completed_sequence_admits_the_destructive_step() -> None:
    progress = ExpandContractProgress(plan_id=uid(903))
    for step in EXPAND_CONTRACT_SEQUENCE:
        if step is ExpandContractStep.REMOVE_OLD_STRUCTURE:
            progress.require_prerequisites(step)
            break
        progress = progress.with_step(step)


def test_governed_dual_access_is_the_one_optional_step() -> None:
    """`P13-XC-001` step 2 is 'only if governed', so its absence does not
    block the sequence."""
    progress = ExpandContractProgress(plan_id=uid(903))
    for step in (
        ExpandContractStep.ADD_STRUCTURE,
        ExpandContractStep.BACKFILL,
        ExpandContractStep.VERIFY,
    ):
        progress = progress.with_step(step)
    progress.require_prerequisites(ExpandContractStep.MIGRATE_CONSUMERS)


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------


def test_an_untested_rollback_is_declared_rather_than_presented() -> None:
    with pytest.raises(RollbackUnavailableError, match="never been exercised"):
        rollback(available=True, tested=False)


def test_neither_rollback_nor_forward_fix_only_is_refused() -> None:
    with pytest.raises(RollbackUnavailableError):
        MigrationRollbackDecision(
            rollback_available=False,
            tested=False,
            forward_fix_only=False,
            statement="unspecified",
        )


def test_forward_fix_only_is_an_honest_declaration() -> None:
    decision = rollback(available=False)
    assert decision.forward_fix_only
    assert not decision.rollback_available


def test_a_rollback_cannot_be_both_available_and_forward_fix_only() -> None:
    with pytest.raises(ValueError, match="not both"):
        MigrationRollbackDecision(
            rollback_available=True, tested=True, forward_fix_only=True, statement="both"
        )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def test_a_failed_execution_that_did_not_preserve_state_is_refused() -> None:
    with pytest.raises(MigrationPartialFailureError):
        MigrationExecution(
            execution_id=uid(900),
            plan_id=uid(19001),
            status=MigrationExecutionStatus.FAILED,
            started_at=NOW,
            grant=grant("migration_execution"),
            state_preserved=False,
        )


def test_a_failed_execution_that_preserved_state_constructs() -> None:
    execution = MigrationExecution(
        execution_id=uid(900),
        plan_id=uid(19001),
        status=MigrationExecutionStatus.FAILED,
        started_at=NOW,
        grant=grant("migration_execution"),
        failure_position=3,
        failure_reason_code="MIGRATION_PARTIAL_FAILURE",
    )
    assert execution.state_preserved


def test_dry_run_evidence_records_what_would_be_affected() -> None:
    assert dry_run().rows_would_be_affected == 12


def test_an_approval_records_its_evidence() -> None:
    assert approval().evidence.content_digest

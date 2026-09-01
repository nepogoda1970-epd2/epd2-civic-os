"""Database migration discipline (PACK-13 §18, §19; ADR-075).

A migration runs with elevated privilege, changes structure irreversibly,
and is usually reviewed less carefully than the application code it
supports. In this system it can also do things no application code could:
drop an organizational-scope column, break a hash-linked evidence chain,
delete records under legal hold, or create the global identifier
FIR-INV-001 forbids.

So five checks here are **automated gates, not reviewer vigilance**
(`P13-MIG-012` through `P13-MIG-016`), and each has its own reason code:
scope loss, hold state unknown, evidence linkage broken, global
identifier creation, voting unlinkability weakened.

The other load-bearing decisions:

- **A migration is immutable once applied** (`P13-MIG-001`). Editing one
  is refused; a correction is a *new* migration.
- **A checksum mismatch halts and escalates** (`P13-MIG-004`). It is
  never auto-repaired, because auto-repair erases the evidence of
  tampering.
- **Ordering is deterministic** (`P13-MIG-003`) and comes from a declared
  position, never from filesystem order, authorship timestamps or
  discovery order.
- **Destructive migrations require separate approval with separation of
  duties** (`P13-MIG-006`, `P13-SEC-004`), dry-run evidence
  (`P13-MIG-010`) and an elapsed observation period (`P13-XC-003`).
- **Rollback is either real or explicitly declared forward-fix-only**
  (`P13-MIG-009`). An unexercised rollback script is declared untested
  rather than presented as a safety net.

This module creates **no real destructive production migration**. The
executor is a reference, in-process simulation whose purpose is to make
the gates testable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    DomainReference,
    EvidenceReference,
    PrivilegedGrantReference,
    content_digest,
    require_timezone,
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


class MigrationClass(StrEnum):
    """The classes ADR-075 names. The class determines the controls, so
    it is a required field rather than a label."""

    EXPAND = "expand"
    BACKFILL = "backfill"
    SWITCH = "switch"
    CONTRACT = "contract"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"


#: The classes that are destructive and therefore inherit `P13-MIG-006`.
#: `CONTRACT` is step 8 of expand/contract (`P13-XC-004`); `EMERGENCY` is
#: here because an emergency migration is not exempt from approval — it
#: uses break-glass, which *adds* obligations rather than removing them
#: (FIR-INV-006).
DESTRUCTIVE_MIGRATION_CLASSES: frozenset[MigrationClass] = frozenset(
    {MigrationClass.CONTRACT, MigrationClass.EMERGENCY}
)

#: The minimum observation period per change class, before the
#: destructive step may run (`P13-XC-003`). Stated so that "remove the
#: old structure" is never same-day with "stop old writes".
MINIMUM_OBSERVATION_PERIOD: Mapping[MigrationClass, timedelta] = {
    MigrationClass.EXPAND: timedelta(0),
    MigrationClass.BACKFILL: timedelta(0),
    MigrationClass.SWITCH: timedelta(days=7),
    MigrationClass.CONTRACT: timedelta(days=14),
    MigrationClass.CORRECTIVE: timedelta(days=1),
    MigrationClass.EMERGENCY: timedelta(0),
}


class MigrationRiskGate(StrEnum):
    """The five automated gates, named so an execution can record which
    ones it evaluated rather than leaving that to inference."""

    ORGANIZATION_SCOPE_PRESERVED = "organization_scope_preserved"
    RETENTION_AND_HOLD_PRESERVED = "retention_and_hold_preserved"
    EVIDENCE_LINKAGE_PRESERVED = "evidence_linkage_preserved"
    NO_GLOBAL_IDENTIFIER_CREATED = "no_global_identifier_created"
    VOTING_UNLINKABILITY_PRESERVED = "voting_unlinkability_preserved"


MIGRATION_RISK_GATES: tuple[MigrationRiskGate, ...] = tuple(MigrationRiskGate)


@dataclass(frozen=True, slots=True)
class MigrationDefinition:
    """One immutable migration definition.

    `checksum` is computed from the statements at construction, so a
    definition cannot be built with a checksum that does not describe
    it. `ordering_position` is explicit and declared — never derived from
    a filename, a timestamp or a directory listing (`P13-MIG-003`)."""

    migration_id: str
    owning_domain: DomainReference
    migration_class: MigrationClass
    ordering_position: int
    statements: tuple[str, ...]
    declared_destructive: bool = False

    def __post_init__(self) -> None:
        if not self.migration_id:
            raise ValueError("migration_id must not be empty")
        if self.ordering_position < 1:
            raise MigrationOrderInvalidError("ordering_position starts at 1")
        if not self.statements:
            raise ValueError("a migration definition carries at least one statement")
        if self.migration_class in DESTRUCTIVE_MIGRATION_CLASSES and not self.declared_destructive:
            raise MigrationDestructiveNotAuthorizedError(
                f"migration {self.migration_id} is class "
                f"{self.migration_class.value!r} and must declare itself destructive; an "
                f"undeclared destructive migration skips its own approval gate"
            )

    @property
    def checksum(self) -> str:
        """The mandatory checksum (`P13-MIG-004`), derived from the
        migration ID, its ordering position and its statements.

        Computed rather than stored so that no code path can present a
        checksum for content it does not have."""
        material = "\n".join((self.migration_id, str(self.ordering_position), *self.statements))
        return content_digest(material)


@dataclass(frozen=True, slots=True)
class AppliedMigration:
    """The record of a migration that has been applied.

    Immutable, and the applied-state check against it is the permanent
    business-fact guard behind migration idempotency (ADR-077)."""

    migration_id: str
    checksum: str
    ordering_position: int
    applied_at: datetime
    execution_id: UUID

    def __post_init__(self) -> None:
        require_timezone(self.applied_at, field="AppliedMigration.applied_at")


@dataclass(frozen=True, slots=True)
class MigrationRollbackDecision:
    """Rollback is either real or explicitly forward-fix-only
    (`P13-MIG-009`).

    `tested` is required when `rollback_available` is true: an untested
    rollback script presented as a safety net is worse than an honest
    declaration that there is none."""

    rollback_available: bool
    tested: bool
    forward_fix_only: bool
    statement: str

    def __post_init__(self) -> None:
        if not self.statement:
            raise ValueError("a rollback decision records its statement")
        if self.rollback_available and self.forward_fix_only:
            raise ValueError("a change is rollback-capable or forward-fix-only, not both")
        if not self.rollback_available and not self.forward_fix_only:
            raise RollbackUnavailableError(
                "no rollback is available and the change has not been declared "
                "forward-fix-only; one of the two is required"
            )
        if self.rollback_available and not self.tested:
            raise RollbackUnavailableError(
                "a rollback that has never been exercised is declared untested, not "
                "presented as a safety net (P13-MIG-009)"
            )


@dataclass(frozen=True, slots=True)
class MigrationApproval:
    """A separate approval with separation of duties (`P13-SEC-004`)."""

    approval_id: UUID
    proposed_by: ActorReference
    approved_by: ActorReference
    approved_at: datetime
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        require_timezone(self.approved_at, field="MigrationApproval.approved_at")
        if self.proposed_by.actor_id == self.approved_by.actor_id:
            raise MigrationSeparationOfDutiesMissingError(
                "the proposer and the approver of a migration are different subjects"
            )


@dataclass(frozen=True, slots=True)
class DryRunEvidence:
    """Evidence that the migration was rehearsed (`P13-MIG-010`)."""

    dry_run_id: UUID
    performed_at: datetime
    rows_would_be_affected: int
    evidence: EvidenceReference

    def __post_init__(self) -> None:
        require_timezone(self.performed_at, field="DryRunEvidence.performed_at")
        if self.rows_would_be_affected < 0:
            raise ValueError("rows_would_be_affected must not be negative")


@dataclass(frozen=True, slots=True)
class DataBackfillReference:
    """A reference from a plan to the backfill that accompanies it.

    Data migration is separated from schema migration where the risk is
    material, so that a failure in one does not force a rollback of the
    other (`P13-MIG-007`)."""

    backfill_id: UUID
    separated_from_schema_migration: bool = True


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    """A plan: the ordered migrations, the class, the controls.

    Construction validates deterministic ordering, so a plan whose
    positions collide cannot exist to be executed."""

    plan_id: UUID
    owning_domain: DomainReference
    migration_class: MigrationClass
    migrations: tuple[MigrationDefinition, ...]
    rollback_decision: MigrationRollbackDecision
    evidence: EvidenceReference
    approval: MigrationApproval | None = None
    dry_run: DryRunEvidence | None = None
    backfill: DataBackfillReference | None = None
    old_writes_stopped_at: datetime | None = None
    dual_write_reconciliation_strategy: str | None = None

    def __post_init__(self) -> None:
        if not self.migrations:
            raise ValueError("a migration plan carries at least one migration")
        positions = [m.ordering_position for m in self.migrations]
        if len(set(positions)) != len(positions):
            raise MigrationOrderInvalidError(
                f"plan {self.plan_id}: ordering positions collide ({sorted(positions)}); "
                f"order is deterministic and does not depend on discovery order"
            )
        if self.old_writes_stopped_at is not None:
            require_timezone(
                self.old_writes_stopped_at, field="MigrationPlan.old_writes_stopped_at"
            )

    @property
    def ordered_migrations(self) -> tuple[MigrationDefinition, ...]:
        return tuple(sorted(self.migrations, key=lambda m: m.ordering_position))

    @property
    def is_destructive(self) -> bool:
        return self.migration_class in DESTRUCTIVE_MIGRATION_CLASSES or any(
            m.declared_destructive for m in self.migrations
        )


@dataclass(frozen=True, slots=True)
class MigrationCheckpoint:
    """A resumable position within one execution (`P13-MIG-008`)."""

    checkpoint_id: UUID
    execution_id: UUID
    position: int
    records_processed: int
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, field="MigrationCheckpoint.recorded_at")
        if self.position < 0 or self.records_processed < 0:
            raise ValueError("checkpoint position and record count must not be negative")


class MigrationExecutionStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class MigrationVerification:
    """The post-execution verification and its evidence."""

    verification_id: UUID
    execution_id: UUID
    passed: bool
    gates_evaluated: tuple[MigrationRiskGate, ...]
    evidence: EvidenceReference
    verified_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.verified_at, field="MigrationVerification.verified_at")
        missing = [gate for gate in MIGRATION_RISK_GATES if gate not in self.gates_evaluated]
        if missing:
            raise MigrationScopeLossDetectedError(
                f"verification {self.verification_id} did not evaluate every automated gate; "
                f"missing: {[g.value for g in missing]}"
            )


@dataclass(frozen=True, slots=True)
class MigrationExecution:
    """One execution of one plan."""

    execution_id: UUID
    plan_id: UUID
    status: MigrationExecutionStatus
    started_at: datetime
    grant: PrivilegedGrantReference
    checkpoints: tuple[MigrationCheckpoint, ...] = ()
    completed_at: datetime | None = None
    failure_position: int | None = None
    failure_reason_code: str | None = None
    state_preserved: bool = True
    verification: MigrationVerification | None = None

    def __post_init__(self) -> None:
        require_timezone(self.started_at, field="MigrationExecution.started_at")
        if self.completed_at is not None:
            require_timezone(self.completed_at, field="MigrationExecution.completed_at")
        if self.status is MigrationExecutionStatus.FAILED and not self.state_preserved:
            raise MigrationPartialFailureError(
                f"execution {self.execution_id} failed and did not preserve state; a partial "
                f"failure halts, preserves state and escalates, and never auto-continues"
            )


# ---------------------------------------------------------------------------
# The gates
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MigrationGateInputs:
    """What the five automated gates read.

    Each field is an observed fact about what the migration would do, and
    every one defaults to the *unsafe* value being explicitly stated
    rather than inferred: `legal_hold_state_resolved=False` fails closed,
    which is §29's required posture for unknown hold state."""

    organization_scope_preserved: bool
    legal_hold_state_resolved: bool
    retention_records_preserved: bool
    evidence_linkage_preserved: bool
    creates_cross_domain_person_key: bool
    weakens_ballot_unlinkability: bool


def evaluate_migration_gates(inputs: MigrationGateInputs, *, migration_id: str) -> None:
    """Run the five automated gates, raising the first failure.

    Order is by irreversibility of the harm, not by likelihood: an
    identity correlation and a weakened ballot boundary are the two that
    no later migration can undo, so they are checked before the others
    have a chance to mask them with a different refusal."""
    if inputs.creates_cross_domain_person_key:
        raise MigrationGlobalIdentifierProhibitedError(
            f"migration {migration_id} would create a structure correlating a person across "
            f"domains; this is an automated acceptance gate, not reviewer vigilance "
            f"(P13-MIG-015)"
        )
    if inputs.weakens_ballot_unlinkability:
        raise MigrationVotingUnlinkabilityAtRiskError(
            f"migration {migration_id} would weaken identity/ballot unlinkability (P13-MIG-016)"
        )
    if not inputs.organization_scope_preserved:
        raise MigrationScopeLossDetectedError(
            f"migration {migration_id} would lose organizational scope (P13-MIG-012)"
        )
    if not inputs.legal_hold_state_resolved:
        raise MigrationHoldStateUnknownError(
            f"migration {migration_id}: legal-hold state could not be resolved; the migration "
            f"fails closed rather than proceeding on an unknown hold state"
        )
    if not inputs.retention_records_preserved:
        raise MigrationHoldStateUnknownError(
            f"migration {migration_id} would delete retention or legal-hold records without "
            f"an explicit policy decision (P13-MIG-013)"
        )
    if not inputs.evidence_linkage_preserved:
        raise MigrationEvidenceLinkageBrokenError(
            f"migration {migration_id} would break document or evidence linkage; no migration "
            f"rewrites a hash-linked history (P13-MIG-014)"
        )


def verify_checksum(definition: MigrationDefinition, applied: AppliedMigration) -> None:
    """Halt and escalate on a checksum mismatch (`P13-MIG-004`).

    There is deliberately no repair path in this module. Auto-repair
    would remove exactly the signal this check exists to produce."""
    if definition.checksum != applied.checksum:
        raise MigrationChecksumMismatchError(
            f"migration {definition.migration_id}: recorded checksum {applied.checksum} does "
            f"not match the current definition's {definition.checksum}; an applied migration "
            f"is immutable, so this halts and escalates and is never auto-repaired"
        )


def reject_reapplication(definition: MigrationDefinition, applied: AppliedMigration | None) -> None:
    """Refuse re-application of an already-applied migration."""
    if applied is not None:
        raise MigrationAlreadyAppliedError(
            f"migration {definition.migration_id} was applied at "
            f"{applied.applied_at.isoformat()}; a correction is a new migration, never an "
            f"edit to this one"
        )


def reject_out_of_order(
    definition: MigrationDefinition, applied_migrations: Sequence[AppliedMigration]
) -> None:
    """Refuse a migration whose position precedes an applied one.

    Deterministic ordering means a later-numbered migration cannot be
    inserted behind one that already ran: the applied state fixes the
    ordering, and a plan that disagrees with it is invalid."""
    highest = max((a.ordering_position for a in applied_migrations), default=0)
    if definition.ordering_position <= highest:
        raise MigrationOrderInvalidError(
            f"migration {definition.migration_id} declares position "
            f"{definition.ordering_position} but position {highest} has already been applied; "
            f"ordering is deterministic and fixed by applied state"
        )


def require_destructive_authorization(plan: MigrationPlan, *, now: datetime) -> None:
    """The full destructive gate: approval, separation of duties, dry-run
    evidence, and an elapsed observation period."""
    require_timezone(now, field="now")
    if not plan.is_destructive:
        return
    if plan.approval is None:
        raise MigrationNotApprovedError(
            f"plan {plan.plan_id} is destructive and requires a separate approval with "
            f"separation of duties (P13-MIG-006)"
        )
    if plan.dry_run is None:
        raise MigrationDryRunMissingError(
            f"plan {plan.plan_id} is destructive and requires dry-run evidence (P13-MIG-010)"
        )
    minimum = MINIMUM_OBSERVATION_PERIOD[plan.migration_class]
    if minimum > timedelta(0):
        if plan.old_writes_stopped_at is None:
            raise MigrationObservationPeriodIncompleteError(
                f"plan {plan.plan_id}: the observation period cannot have elapsed because the "
                f"moment old writes stopped was never recorded (P13-XC-003)"
            )
        if now - plan.old_writes_stopped_at < minimum:
            raise MigrationObservationPeriodIncompleteError(
                f"plan {plan.plan_id}: {minimum} must elapse between stopping old writes and "
                f"removing the old structure; only {now - plan.old_writes_stopped_at} has"
            )


def require_dual_write_reconciliation(plan: MigrationPlan, *, dual_write_deployed: bool) -> None:
    """Dual-write is forbidden without an approved reconciliation
    strategy (`P13-XC-002`).

    Two unreconciled writes are two sources of truth pretending to be
    one."""
    if dual_write_deployed and not plan.dual_write_reconciliation_strategy:
        raise MigrationNotApprovedError(
            f"plan {plan.plan_id} deploys dual-write with no reconciliation strategy; a "
            f"defined way to detect and resolve divergence, with its own evidence, is "
            f"required before dual-write is admissible"
        )


class ExpandContractStep(StrEnum):
    """`P13-XC-001`'s nine steps, in order. Modelled so a plan can record
    which step it is at and the destructive gate can check that step 7
    genuinely preceded step 8."""

    ADD_STRUCTURE = "add_new_compatible_structure"
    GOVERNED_DUAL_ACCESS = "governed_dual_read_or_dual_write"
    BACKFILL = "backfill"
    VERIFY = "verify"
    MIGRATE_CONSUMERS = "migrate_consumers"
    STOP_OLD_WRITES = "stop_old_writes"
    OBSERVE = "observe"
    REMOVE_OLD_STRUCTURE = "remove_old_structure"
    ARCHIVE_EVIDENCE = "archive_evidence"


EXPAND_CONTRACT_SEQUENCE: tuple[ExpandContractStep, ...] = tuple(ExpandContractStep)


@dataclass(frozen=True, slots=True)
class ExpandContractProgress:
    """Which steps a plan has completed, with the moment each finished."""

    plan_id: UUID
    completed_steps: tuple[ExpandContractStep, ...] = field(default=())

    def require_prerequisites(self, step: ExpandContractStep) -> None:
        """Refuse a step whose predecessors have not completed.

        The sequence is normative, not advisory: step 8 without step 7 is
        exactly the same-day removal `P13-XC-003` exists to prevent."""
        index = EXPAND_CONTRACT_SEQUENCE.index(step)
        missing = [
            earlier
            for earlier in EXPAND_CONTRACT_SEQUENCE[:index]
            if earlier not in self.completed_steps
            and earlier is not ExpandContractStep.GOVERNED_DUAL_ACCESS
        ]
        if missing:
            raise MigrationObservationPeriodIncompleteError(
                f"plan {self.plan_id}: step {step.value!r} requires "
                f"{[s.value for s in missing]} to have completed first"
            )

    def with_step(self, step: ExpandContractStep) -> ExpandContractProgress:
        return ExpandContractProgress(
            plan_id=self.plan_id, completed_steps=(*self.completed_steps, step)
        )

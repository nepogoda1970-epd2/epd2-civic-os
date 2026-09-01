"""Retention, legal hold and evidence in the data plane
(PACK-13 §24, §25; ADR-078).

**PACK-09 owns retention, legal hold and destruction evidence. PACK-11
owns governed documents and evidence bundles.** Neither owns the places a
data plane copies data to: projections, caches, search indexes, outbox
records, dead-letter stores, replicas, backups and migration artifacts.
Every one of those is a copy that can outlive its source, and a deletion
that does not reach them is not a deletion.

So this module binds those infrastructure classes into PACK-09's system
without deciding anything PACK-09 decides:

- **Retention applies to infrastructure** (`P13-RET-006`). Every
  persistent class in `InfrastructurePersistentClass` carries a retention
  binding, and `require_retention_binding` refuses one that does not.
  None is exempt by virtue of being infrastructure.
- **A legal hold preserves data. It does not authorize access, search,
  export or publication** (`P13-RET-005`). This is restated at the type
  level: `LegalHoldState` has no field that could grant anything, and
  `require_hold_does_not_authorize` exists to refuse the confusion
  explicitly.
- **Where hold state is unknown, deletion fails closed** (§29's last
  row).
- **Backup retention is stated explicitly, with its consequence**
  (`P13-RET-004`). A record deleted from the live database but present
  in backups **is not deleted**; `BackupHorizonStatement` carries the
  horizon and says what it means. Closing that gap is PACK-17's.
- **Evidence uses PACK-11's mechanisms, not new ones** (ADR-078). There
  is deliberately no evidence *store* in this package — only references
  into PACK-11's.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_data_plane_service.domain import (
    ActorReference,
    EvidenceReference,
    OrganizationScopeReference,
    RecordClassReference,
    RetentionScheduleReference,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    GovernedRecordDeletionForbiddenError,
    LegalHoldStateUnknownError,
    RecordUnderLegalHoldError,
)


class InfrastructurePersistentClass(StrEnum):
    """The data-plane persistent classes that carry a retention binding.

    Enumerated so that "none is exempt by virtue of being
    infrastructure" is a testable claim: a test asserts that every member
    appears in `REQUIRED_RETENTION_CLASSES`."""

    OUTBOX_RECORD = "outbox_record"
    DEAD_LETTER_RECORD = "dead_letter_record"
    IDEMPOTENCY_RECORD = "idempotency_record"
    DEDUPLICATION_RECORD = "deduplication_record"
    CONSUMER_CHECKPOINT = "consumer_checkpoint"
    PROJECTION_ROW = "projection_row"
    SEARCH_PROJECTION_ENTRY = "search_projection_entry"
    SCHEMA_REGISTRY_ENTRY = "schema_registry_entry"
    MIGRATION_EVIDENCE = "migration_evidence"
    BACKFILL_REVIEW_ENTRY = "backfill_review_entry"
    EXPORT_REQUEST_RECORD = "export_request_record"


#: Every member. `P13-RET-006` names four groups — projections and
#: caches, events and outbox records, schema registry entries, migration
#: evidence — and this set is their expansion plus the derived stores
#: those groups imply.
REQUIRED_RETENTION_CLASSES: frozenset[InfrastructurePersistentClass] = frozenset(
    InfrastructurePersistentClass
)


class LegalHoldState(StrEnum):
    """The three hold states, including the one that matters most.

    `UNKNOWN` is a real state, not an absence: §29 assigns it the
    posture "deletion does not proceed where hold state is unknown", and
    a two-valued hold flag would make that impossible to express."""

    NOT_HELD = "not_held"
    HELD = "held"
    UNKNOWN = "unknown"


class DeletionEligibility(StrEnum):
    ELIGIBLE = "eligible"
    NOT_YET_DUE = "not_yet_due"
    BLOCKED_BY_HOLD = "blocked_by_hold"
    BLOCKED_UNKNOWN_HOLD_STATE = "blocked_unknown_hold_state"
    GOVERNED_RECORD = "governed_record"


@dataclass(frozen=True, slots=True)
class RetentionBinding:
    """One persistent class bound to PACK-09's decisions
    (`P13-RET-001`, `P13-RET-002`).

    PACK-13 supplies the binding; PACK-09 supplies the schedule, the
    record class and the hold. There is no field here that could set a
    retention period, because that decision is not this pack's."""

    persistent_class: InfrastructurePersistentClass
    record_class: RecordClassReference
    retention_schedule: RetentionScheduleReference
    scope: OrganizationScopeReference | None = None


def require_retention_binding(
    bindings: Mapping[InfrastructurePersistentClass, RetentionBinding],
) -> None:
    """Refuse a data plane in which some infrastructure class carries no
    retention binding (`P13-RET-006`)."""
    missing = sorted(cls.value for cls in REQUIRED_RETENTION_CLASSES if cls not in bindings)
    if missing:
        raise GovernedRecordDeletionForbiddenError(
            f"persistent class(es) {missing} carry no retention binding; none is exempt by "
            f"virtue of being infrastructure (P13-RET-006)"
        )


@dataclass(frozen=True, slots=True)
class LegalHoldObservation:
    """What the data plane observed about hold state — never what it
    decided.

    `observed_by` records the acting authority, and `authorizes_access`
    is a property fixed to `False`: a hold preserves, and the practical
    meaning of one is "the deletion job skips this record", never "the
    investigator may read this" (`P13-RET-005`)."""

    record_id: UUID
    state: LegalHoldState
    observed_at: datetime
    observed_by: ActorReference
    hold_reference: UUID | None = None

    def __post_init__(self) -> None:
        require_timezone(self.observed_at, field="LegalHoldObservation.observed_at")
        if self.state is LegalHoldState.HELD and self.hold_reference is None:
            raise LegalHoldStateUnknownError(
                "a held record names the hold that holds it; a hold with no reference cannot "
                "be lifted, reviewed or audited"
            )

    @property
    def authorizes_access(self) -> bool:
        """Always `False`. Exposed as a property so a caller that reaches
        for it gets the answer rather than inferring one, and so a test
        can assert the invariant directly."""
        return False


def require_hold_does_not_authorize(observation: LegalHoldObservation, *, context: str) -> None:
    """Refuse any attempt to read a hold as an access grant.

    The data plane is exactly where this confusion would be
    operationalised, which is why the refusal lives here rather than in a
    document."""
    if observation.authorizes_access:  # pragma: no cover - structurally unreachable
        raise RecordUnderLegalHoldError(
            f"{context}: a legal hold preserves data and does not authorize access, search, "
            f"export or publication"
        )


@dataclass(frozen=True, slots=True)
class DeletionEvidence:
    """Evidence that a deletion happened (`P13-RET-003`).

    A PACK-11 evidence reference, not a new evidence system: ADR-078
    rejected a separate data-plane evidence store for the same reason
    PACK-12's `OD-P12-06` did."""

    evidence: EvidenceReference
    record_id: UUID
    deleted_at: datetime
    decided_by: ActorReference
    retention_schedule: RetentionScheduleReference

    def __post_init__(self) -> None:
        require_timezone(self.deleted_at, field="DeletionEvidence.deleted_at")


@dataclass(frozen=True, slots=True)
class DeletionDecision:
    """The data plane's *observation* of PACK-09's decision.

    It computes eligibility from inputs PACK-09 supplies and refuses when
    they are missing. It decides nothing: `eligibility` is derived, and
    every branch that is not `ELIGIBLE` is a refusal."""

    record_id: UUID
    binding: RetentionBinding
    hold: LegalHoldObservation
    retention_due: bool
    governed_record: bool = False

    @property
    def eligibility(self) -> DeletionEligibility:
        if self.hold.state is LegalHoldState.UNKNOWN:
            return DeletionEligibility.BLOCKED_UNKNOWN_HOLD_STATE
        if self.hold.state is LegalHoldState.HELD:
            return DeletionEligibility.BLOCKED_BY_HOLD
        if self.governed_record:
            return DeletionEligibility.GOVERNED_RECORD
        if not self.retention_due:
            return DeletionEligibility.NOT_YET_DUE
        return DeletionEligibility.ELIGIBLE

    def require_eligible(self, *, context: str) -> None:
        """Raise the registered refusal for anything but eligibility.

        `BLOCKED_UNKNOWN_HOLD_STATE` fails closed, which is §29's
        required posture for a failed legal-hold propagation: deletion
        does not proceed where hold state is unknown."""
        eligibility = self.eligibility
        if eligibility is DeletionEligibility.BLOCKED_UNKNOWN_HOLD_STATE:
            raise LegalHoldStateUnknownError(
                f"{context}: hold state for record {self.record_id} could not be resolved; "
                f"deletion fails closed rather than proceeding on an unknown"
            )
        if eligibility is DeletionEligibility.BLOCKED_BY_HOLD:
            raise RecordUnderLegalHoldError(
                f"{context}: record {self.record_id} is under legal hold and is preserved; "
                f"the hold authorizes no access to it"
            )
        if eligibility is DeletionEligibility.GOVERNED_RECORD:
            raise GovernedRecordDeletionForbiddenError(
                f"{context}: record {self.record_id} is a governed record; its disposal is "
                f"PACK-09's governed process, not a storage-level delete"
            )
        if eligibility is DeletionEligibility.NOT_YET_DUE:
            raise GovernedRecordDeletionForbiddenError(
                f"{context}: record {self.record_id} is not yet due under retention schedule "
                f"{self.binding.retention_schedule.schedule_name!r}"
            )


@dataclass(frozen=True, slots=True)
class BackupHorizonStatement:
    """The explicit backup statement `P13-RET-004` requires.

    Carried as a value rather than left to prose, because the honest
    sentence — a record deleted from the live database but present in
    backups **is not deleted** — is exactly the one that goes missing
    when "we deleted it" quietly means "we deleted one copy"."""

    horizon: timedelta
    consequence: str
    closed_by_pack: str = "PACK-17"

    def __post_init__(self) -> None:
        if self.horizon <= timedelta(0):
            raise ValueError("a backup horizon is a positive duration")
        if not self.consequence:
            raise ValueError(
                "a backup horizon states its consequence; a horizon without one lets "
                "'we deleted it' mean 'we deleted one copy'"
            )


#: The statement this reference implementation makes about itself. It has
#: no backups, because it has no durable storage — and that is stated
#: rather than allowed to read as "the gap is closed".
REFERENCE_BACKUP_STATEMENT = BackupHorizonStatement(
    horizon=timedelta(days=1),
    consequence=(
        "This reference implementation persists nothing beyond a process lifetime, so it "
        "has no backups and no restore path. That is an absence of the capability, not a "
        "closure of the gap: a production data plane's backup horizon, and the consequence "
        "that a record deleted from the live database but present in backups is not deleted, "
        "are defined here and delivered by PACK-17."
    ),
)


# ---------------------------------------------------------------------------
# Evidence (PACK-11 remains the owner)
# ---------------------------------------------------------------------------


class GovernedArtifactKind(StrEnum):
    """The data-plane artifacts that carry PACK-11 evidence references
    (`P13-DOC-002`, `P13-DOC-003`)."""

    SCHEMA_PUBLICATION_DECISION = "schema_publication_decision"
    MIGRATION_PLAN = "migration_plan"
    MIGRATION_VERIFICATION = "migration_verification"
    BACKFILL_RECONCILIATION = "backfill_reconciliation"
    DELETION_PROPAGATION = "deletion_propagation"
    EXPORT_MANIFEST = "export_manifest"
    REPLAY = "replay"


@dataclass(frozen=True, slots=True)
class GovernedArtifactEvidence:
    """One data-plane artifact bound to PACK-11's evidence.

    `supersedes` is how replacement works here: historical schemas remain
    immutable and replacement is **supersession**, with digest and
    version history preserved (`P13-DOC-004`). There is no field that
    could overwrite an earlier artifact."""

    artifact_kind: GovernedArtifactKind
    artifact_id: UUID
    evidence: EvidenceReference
    recorded_at: datetime
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, field="GovernedArtifactEvidence.recorded_at")
        if self.supersedes == self.artifact_id:
            raise ValueError("an artifact does not supersede itself")


def require_evidence_for(
    kind: GovernedArtifactKind,
    evidence: EvidenceReference | None,
    *,
    context: str,
) -> EvidenceReference:
    """Refuse a governed data-plane artifact with no evidence reference.

    `P13-DOC-002` says migration plans and verification reports use
    evidence references, not ad-hoc file paths; `P13-DOC-003` says a
    schema publication decision has evidence. This is where both become
    unavoidable."""
    if evidence is None:
        raise GovernedRecordDeletionForbiddenError(
            f"{context}: a {kind.value} carries a PACK-11 evidence reference, not an ad-hoc "
            f"file path and not nothing"
        )
    return evidence

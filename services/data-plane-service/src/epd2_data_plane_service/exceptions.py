"""Data Plane Service exceptions, one class per stable reason code
(PACK-13; ADR-069 through ADR-078; canon section 24's reason-code
standard applied to this pack).

Every class below carries a `reason_code` class attribute whose literal
string is registered in `contracts/reason-codes/pack-13.yml`. No PACK-13
code path raises a bare `ValueError` or `PermissionError` with a
free-text message in place of one of these, and — per `P13-RSN-002` —
there is deliberately **no generic `DATA_ERROR` and no generic
`CONFLICT`**: a single code covering many causes tells an operator
nothing and an auditor less.

The hierarchy mirrors every earlier pack's: structural, lifecycle and
consistency violations subclass `ValueError`; authorization, scope,
ownership and separation-of-duties violations subclass `PermissionError`,
so a caller that already distinguishes those two categories across
PACK-02 through PACK-12 needs no PACK-13-specific handling.

Seven prefixes, matching the seven governed concerns of the reason-code
catalog:

- `SCHEMA_*` / contract-governance codes — the canonical schema registry
  and contract evolution;
- `MIGRATION_*` — migration control, plus `ROLLBACK_UNAVAILABLE` and
  `MANUAL_SQL_PROHIBITED`, which the catalog files with them;
- `BACKFILL_*` — the backfill runner;
- `CONCURRENCY_*` / `IDEMPOTENCY_*` — optimistic concurrency and
  idempotent execution;
- `EVENT_*` / `OUTBOX_*` / `DELIVERY_*` / `BROKER_*` — outbox and
  delivery semantics;
- `PROJECTION_*` — read-model governance;
- `DATAPLANE_*` — the structural boundary refusals.

Codes owned by earlier packs are re-raised through the thin subclasses at
the end of this module rather than shadowed by a PACK-13 synonym
(`P13-RSN-005`): one fact keeps one code.
"""

from __future__ import annotations


class DataPlaneError(Exception):
    """Base class for every governed PACK-13 refusal.

    `reason_code` is always a string registered in
    `contracts/reason-codes/pack-13.yml`."""

    reason_code: str = "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# SCHEMA_* and contract governance
# ---------------------------------------------------------------------------


class SchemaIncompatibleError(DataPlaneError, ValueError):
    """The proposed version is incompatible under the declared mode."""

    reason_code = "SCHEMA_INCOMPATIBLE"


class SchemaCompatibilityUnknownError(DataPlaneError, ValueError):
    """The checker could not classify the change; manual review is
    required (`P13-COMPAT-002`). `unknown` is a first-class outcome, never
    a placeholder that decays into "probably compatible"."""

    reason_code = "SCHEMA_COMPATIBILITY_UNKNOWN"


class SchemaOwnerMissingError(DataPlaneError, PermissionError):
    """No registered owner; publication refused (`P13-REG-007`)."""

    reason_code = "SCHEMA_OWNER_MISSING"


class SchemaNotApprovedError(DataPlaneError, PermissionError):
    """Activation attempted before approval."""

    reason_code = "SCHEMA_NOT_APPROVED"


class SchemaDigestMismatchError(DataPlaneError, ValueError):
    """The content does not match the recorded `content_digest`."""

    reason_code = "SCHEMA_DIGEST_MISMATCH"


class SchemaDuplicateContentError(DataPlaneError, ValueError):
    """Content identical to a registered version after the format's own
    canonicalization; accidental republication is blocked
    (`P13-REG-005d`)."""

    reason_code = "SCHEMA_DUPLICATE_CONTENT"


class SchemaDuplicateContentReviewRequiredError(DataPlaneError, ValueError):
    """Identical content submitted as a new version without a
    `governance_justification`; reason-coded review is required."""

    reason_code = "SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED"


class SchemaVersionIdentityImmutableError(DataPlaneError, ValueError):
    """An attempt to re-point, merge or rewrite a historical
    `schema_version_id` because of digest equality (`P13-REG-005g`)."""

    reason_code = "SCHEMA_VERSION_IDENTITY_IMMUTABLE"


class SchemaGovernanceJustificationMissingError(DataPlaneError, ValueError):
    """A governed re-issue lacks its justification (`P13-REG-005e`)."""

    reason_code = "SCHEMA_GOVERNANCE_JUSTIFICATION_MISSING"


class SchemaExamplesInvalidError(DataPlaneError, ValueError):
    """The schema's own fixtures do not validate against it
    (`P13-REG-008`)."""

    reason_code = "SCHEMA_EXAMPLES_INVALID"


class SchemaLifecycleTransitionForbiddenError(DataPlaneError, ValueError):
    """The requested lifecycle transition is not declared."""

    reason_code = "SCHEMA_LIFECYCLE_TRANSITION_FORBIDDEN"


class SchemaRetiredError(DataPlaneError, ValueError):
    """A retired version was used for new traffic. The version itself is
    retained — deleting it would orphan history (`P13-REG-004`)."""

    reason_code = "SCHEMA_RETIRED"


class SchemaRegistryUnavailableError(DataPlaneError, ValueError):
    """The registry could not be reached; publication is blocked while
    already-resolved traffic continues (§29)."""

    reason_code = "SCHEMA_REGISTRY_UNAVAILABLE"


class ConsumerNotReadyError(DataPlaneError, ValueError):
    """A registered consumer has not migrated (`P13-API-009`)."""

    reason_code = "CONSUMER_NOT_READY"


class ConsumerNotRegisteredError(DataPlaneError, ValueError):
    """The consumer receives no compatibility protection — a stated
    consequence, not one to be discovered (`P13-REG-009`)."""

    reason_code = "CONSUMER_NOT_REGISTERED"


class BreakingChangeNotApprovedError(DataPlaneError, PermissionError):
    """A breaking change lacks its required approval (`P13-GOV-002`)."""

    reason_code = "BREAKING_CHANGE_NOT_APPROVED"


class DeprecationWindowIncompleteError(DataPlaneError, ValueError):
    """Retirement attempted before the coexistence window elapsed."""

    reason_code = "DEPRECATION_WINDOW_INCOMPLETE"


class SemanticReviewRequiredError(DataPlaneError, ValueError):
    """An invisible-class change requires human assessment
    (`P13-COMPAT-004`)."""

    reason_code = "SEMANTIC_REVIEW_REQUIRED"


class LegalReviewRequiredError(DataPlaneError, ValueError):
    """The change touches legal effect or retention semantics
    (`P13-GOV-003`)."""

    reason_code = "LEGAL_REVIEW_REQUIRED"


class SecurityReviewRequiredError(DataPlaneError, ValueError):
    """The change touches authorization implication or identity linkage
    (`P13-GOV-003`)."""

    reason_code = "SECURITY_REVIEW_REQUIRED"


# ---------------------------------------------------------------------------
# MIGRATION_*
# ---------------------------------------------------------------------------


class MigrationChecksumMismatchError(DataPlaneError, ValueError):
    """An applied migration's content changed. This halts and escalates;
    it is never auto-repaired, because auto-repair erases the evidence of
    tampering (`P13-MIG-004`, ADR-075)."""

    reason_code = "MIGRATION_CHECKSUM_MISMATCH"


class MigrationOrderInvalidError(DataPlaneError, ValueError):
    """Ordering position conflicts with applied state (`P13-MIG-003`)."""

    reason_code = "MIGRATION_ORDER_INVALID"


class MigrationAlreadyAppliedError(DataPlaneError, ValueError):
    """Re-application attempted. The applied-state check is the permanent
    business-fact guard behind migration idempotency (ADR-077)."""

    reason_code = "MIGRATION_ALREADY_APPLIED"


class MigrationNotApprovedError(DataPlaneError, PermissionError):
    """A migration class requiring approval lacks it."""

    reason_code = "MIGRATION_NOT_APPROVED"


class MigrationSeparationOfDutiesMissingError(DataPlaneError, PermissionError):
    """Proposer and approver are the same subject (`P13-SEC-004`)."""

    reason_code = "MIGRATION_SEPARATION_OF_DUTIES_MISSING"


class MigrationPartialFailureError(DataPlaneError, ValueError):
    """Execution halted mid-way; state is preserved and escalated, never
    auto-continued (§29)."""

    reason_code = "MIGRATION_PARTIAL_FAILURE"


class MigrationDryRunMissingError(DataPlaneError, ValueError):
    """No dry-run evidence (`P13-MIG-010`)."""

    reason_code = "MIGRATION_DRY_RUN_MISSING"


class MigrationDestructiveNotAuthorizedError(DataPlaneError, PermissionError):
    """A destructive step without its separate approval (`P13-MIG-006`)."""

    reason_code = "MIGRATION_DESTRUCTIVE_NOT_AUTHORIZED"


class MigrationObservationPeriodIncompleteError(DataPlaneError, ValueError):
    """The contract step was attempted too early: divergence is found by
    running, not by reviewing (`P13-XC-003`)."""

    reason_code = "MIGRATION_OBSERVATION_PERIOD_INCOMPLETE"


class MigrationScopeLossDetectedError(DataPlaneError, ValueError):
    """Organizational scope would be lost (`P13-MIG-012`)."""

    reason_code = "MIGRATION_SCOPE_LOSS_DETECTED"


class MigrationHoldStateUnknownError(DataPlaneError, ValueError):
    """Legal-hold state could not be resolved; the migration fails closed
    (`P13-MIG-013`, §29's last row)."""

    reason_code = "MIGRATION_HOLD_STATE_UNKNOWN"


class MigrationEvidenceLinkageBrokenError(DataPlaneError, ValueError):
    """Document or evidence linkage would break (`P13-MIG-014`)."""

    reason_code = "MIGRATION_EVIDENCE_LINKAGE_BROKEN"


class MigrationGlobalIdentifierProhibitedError(DataPlaneError, PermissionError):
    """The migration would create a global user identifier
    (`P13-MIG-015`, FIR-INV-001). An automated gate, not reviewer
    vigilance."""

    reason_code = "MIGRATION_GLOBAL_IDENTIFIER_PROHIBITED"


class MigrationVotingUnlinkabilityAtRiskError(DataPlaneError, PermissionError):
    """The migration would weaken ballot unlinkability (`P13-MIG-016`,
    FIR-INV-002)."""

    reason_code = "MIGRATION_VOTING_UNLINKABILITY_AT_RISK"


class RollbackUnavailableError(DataPlaneError, ValueError):
    """No tested rollback exists; the change is forward-fix-only, and
    says so rather than presenting an unexercised script as a safety net
    (`P13-MIG-009`)."""

    reason_code = "ROLLBACK_UNAVAILABLE"


class ManualSqlProhibitedError(DataPlaneError, PermissionError):
    """Direct SQL outside a governed migration or emergency context
    (`P13-MIG-011`, `P13-SEC-003`)."""

    reason_code = "MANUAL_SQL_PROHIBITED"


# ---------------------------------------------------------------------------
# BACKFILL_*
# ---------------------------------------------------------------------------


class BackfillConflictError(DataPlaneError, ValueError):
    """The target is already populated with a different value."""

    reason_code = "BACKFILL_CONFLICT"


class BackfillSourceIncompleteError(DataPlaneError, ValueError):
    """The source lacks a fact the target requires; the record is routed
    to review and never filled with a default or an inference
    (`P13-BF-011`)."""

    reason_code = "BACKFILL_SOURCE_INCOMPLETE"


class BackfillInvariantViolationError(DataPlaneError, ValueError):
    """The written record would violate a domain invariant. Writing
    through the database rather than the domain does not make an invalid
    record valid (`P13-BF-010`)."""

    reason_code = "BACKFILL_INVARIANT_VIOLATION"


class BackfillCheckpointLostError(DataPlaneError, ValueError):
    """The resume position is unavailable (`P13-BF-004`)."""

    reason_code = "BACKFILL_CHECKPOINT_LOST"


class BackfillReconciliationFailedError(DataPlaneError, ValueError):
    """Counts do not reconcile (`P13-BF-014`)."""

    reason_code = "BACKFILL_RECONCILIATION_FAILED"


# ---------------------------------------------------------------------------
# CONCURRENCY_* and IDEMPOTENCY_*
# ---------------------------------------------------------------------------


class ConcurrencyStaleAggregateVersionError(DataPlaneError, ValueError):
    """The expected version does not match the actual one
    (`P13-CC-002`)."""

    reason_code = "CONCURRENCY_STALE_AGGREGATE_VERSION"


class ConcurrencyApprovalOnChangedVersionError(DataPlaneError, ValueError):
    """The aggregate moved since the approver saw it, so the approval is
    returned for a fresh decision (`P13-CC-005`). "Approve" means
    "approve *this*", not "approve whatever is there now"."""

    reason_code = "CONCURRENCY_APPROVAL_ON_CHANGED_VERSION"


class ConcurrencyLastWriteWinsProhibitedError(DataPlaneError, ValueError):
    """The record class forbids overwrite resolution (`P13-CC-003`)."""

    reason_code = "CONCURRENCY_LAST_WRITE_WINS_PROHIBITED"


class ConcurrencyAuthorityLapsedError(DataPlaneError, PermissionError):
    """Effective-dated authority expired between command construction and
    command execution (`P13-CC-006`)."""

    reason_code = "CONCURRENCY_AUTHORITY_LAPSED"


class IdempotencyKeyReusedWithDifferentPayloadError(DataPlaneError, ValueError):
    """Same key, different content. This is a conflict, never a replay
    (`P13-IDEM-004`)."""

    reason_code = "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD"


class IdempotencyKeyScopeInvalidError(DataPlaneError, ValueError):
    """The key is not scoped to a domain and an operation
    (`P13-IDEM-002`)."""

    reason_code = "IDEMPOTENCY_KEY_SCOPE_INVALID"


class IdempotencyRecordExpiredError(DataPlaneError, ValueError):
    """The idempotency window closed. For a consequential operation the
    permanent business-fact guard governs instead; the expiry never
    silently admits a duplicate (`P13-IDEM-006`)."""

    reason_code = "IDEMPOTENCY_RECORD_EXPIRED"


class IdempotencyGlobalIdentifierProhibitedError(DataPlaneError, PermissionError):
    """The key derives from a global user identifier, which would turn a
    key space into a correlation space (`P13-IDEM-003`, FIR-INV-001)."""

    reason_code = "IDEMPOTENCY_GLOBAL_IDENTIFIER_PROHIBITED"


# ---------------------------------------------------------------------------
# EVENT_*, OUTBOX_*, DELIVERY_*, BROKER_*
# ---------------------------------------------------------------------------


class EventDuplicateSuppressedError(DataPlaneError, ValueError):
    """A duplicate delivery was absorbed and counted (`P13-DEL-004`)."""

    reason_code = "EVENT_DUPLICATE_SUPPRESSED"


class EventOrderingGapDetectedError(DataPlaneError, ValueError):
    """A sequence gap in the ordering scope — a governed fact that raises
    an event, not a silent absence (`P13-ORD-006`)."""

    reason_code = "EVENT_ORDERING_GAP_DETECTED"


class EventOutOfOrderError(DataPlaneError, ValueError):
    """An event arrived behind the checkpoint (`P13-DEL-006`)."""

    reason_code = "EVENT_OUT_OF_ORDER"


class EventVersionUnsupportedError(DataPlaneError, ValueError):
    """The consumer supports no such version; it fails closed rather than
    attempting a partial parse (`P13-EVO-006`)."""

    reason_code = "EVENT_VERSION_UNSUPPORTED"


class EventPoisonMessageError(DataPlaneError, ValueError):
    """Deterministic failure across attempts; detected as such rather
    than retried forever (`P13-DEL-012`)."""

    reason_code = "EVENT_POISON_MESSAGE"


class EventDeadLetterRequiredError(DataPlaneError, ValueError):
    """Retry is exhausted; the record moves to the dead-letter store with
    its failure context (`P13-DEL-008`, `P13-DEL-009`)."""

    reason_code = "EVENT_DEAD_LETTER_REQUIRED"


class EventReplayNotAuthorizedError(DataPlaneError, PermissionError):
    """Replay without authority or scope (`P13-DEL-010`)."""

    reason_code = "EVENT_REPLAY_NOT_AUTHORIZED"


class OutboxPublicationPendingError(DataPlaneError, ValueError):
    """Committed but not yet published. Publication is pending, never
    lost (§29's broker-unavailable row)."""

    reason_code = "OUTBOX_PUBLICATION_PENDING"


class OutboxBacklogThresholdExceededError(DataPlaneError, ValueError):
    """The backlog is past its alert threshold; backlog is a first-class
    health signal, not an incidental metric."""

    reason_code = "OUTBOX_BACKLOG_THRESHOLD_EXCEEDED"


class BrokerUnavailableError(DataPlaneError, ValueError):
    """The broker could not be reached. Commands still commit."""

    reason_code = "BROKER_UNAVAILABLE"


class DeliveryAcknowledgementMissingError(DataPlaneError, ValueError):
    """Dispatched, acknowledgement unknown. Treated as *unknown*, not as
    failure and not as success (`P13-DEL-007`)."""

    reason_code = "DELIVERY_ACKNOWLEDGEMENT_MISSING"


# ---------------------------------------------------------------------------
# PROJECTION_*
# ---------------------------------------------------------------------------


class ProjectionStaleError(DataPlaneError, ValueError):
    """Lag exceeds the freshness a consequential decision requires. A
    stale projection that looks fresh is worse than one plainly
    unavailable (`P13-PROJ-008`)."""

    reason_code = "PROJECTION_STALE"


class ProjectionRebuildRequiredError(DataPlaneError, ValueError):
    """The projection cannot serve until rebuilt."""

    reason_code = "PROJECTION_REBUILD_REQUIRED"


class ProjectionRebuildFailedError(DataPlaneError, ValueError):
    """The rebuild did not complete; the projection is marked failed and
    stale rather than silently serving partial data (§29)."""

    reason_code = "PROJECTION_REBUILD_FAILED"


class ProjectionDeletionNotPropagatedError(DataPlaneError, ValueError):
    """A source deletion has not reached the projection. A projection
    that outlives its source is an undeletable copy (`P13-PROJ-009`)."""

    reason_code = "PROJECTION_DELETION_NOT_PROPAGATED"


class ProjectionAuthorizationWideningProhibitedError(DataPlaneError, PermissionError):
    """The projection would expose more than its sources
    (`P13-PROJ-004`)."""

    reason_code = "PROJECTION_AUTHORIZATION_WIDENING_PROHIBITED"


class ProjectionNotAuthoritativeError(DataPlaneError, PermissionError):
    """A legal-effect decision was attempted against a read model
    (`P13-PROJ-002`, `P13-PROJ-003`)."""

    reason_code = "PROJECTION_NOT_AUTHORITATIVE"


# ---------------------------------------------------------------------------
# DATAPLANE_* — the structural boundary refusals
# ---------------------------------------------------------------------------


class CrossDomainDirectAccessDeniedError(DataPlaneError, PermissionError):
    """A direct read or write across a domain boundary. A query that
    works is not thereby permitted (`P13-DP-013`, `P13-DP-014`)."""

    reason_code = "DATAPLANE_CROSS_DOMAIN_DIRECT_ACCESS_DENIED"


class AuditDirectWriteDeniedError(DataPlaneError, PermissionError):
    """A non-owner domain attempted to write audit persistence directly
    instead of submitting through the governed ingestion contract
    (`P13-DP-014a`)."""

    reason_code = "DATAPLANE_AUDIT_DIRECT_WRITE_DENIED"


class AuditIngestionContractRequiredError(DataPlaneError, PermissionError):
    """An audit record arrived by a path other than the ingestion port,
    API or versioned command (`P13-DP-014a`)."""

    reason_code = "DATAPLANE_AUDIT_INGESTION_CONTRACT_REQUIRED"


class ReservedBoundarySchemaProhibitedError(DataPlaneError, PermissionError):
    """A schema was proposed for a reserved future boundary whose owner
    is not yet established (`P13-OWN-011`)."""

    reason_code = "DATAPLANE_RESERVED_BOUNDARY_SCHEMA_PROHIBITED"


class OrganizationScopeMissingError(DataPlaneError, ValueError):
    """A scoped record arrived without scope (`P13-DP-005`,
    `P13-CTX-002`)."""

    reason_code = "DATAPLANE_ORGANIZATION_SCOPE_MISSING"


class GlobalUserIdentifierProhibitedError(DataPlaneError, PermissionError):
    """A structure that would correlate a person across domains
    (`P13-DP-008`, `P13-DP-016`, FIR-INV-001)."""

    reason_code = "DATAPLANE_GLOBAL_USER_IDENTIFIER_PROHIBITED"


class VotingMaterialProhibitedError(DataPlaneError, PermissionError):
    """Ballot, credential or tally material in the general plane
    (`P13-DP-012`, `P13-VOTE-001`..`007`, FIR-INV-002)."""

    reason_code = "DATAPLANE_VOTING_MATERIAL_PROHIBITED"


class RawExportProhibitedError(DataPlaneError, PermissionError):
    """An export route bypassing PACK-12. A dump, replica, backup extract
    or analytics copy is not an export route (`P13-EXPORT-004`)."""

    reason_code = "DATAPLANE_RAW_EXPORT_PROHIBITED"


class OperatorPrivilegeInsufficientError(DataPlaneError, PermissionError):
    """Cluster privilege presented as domain-content authority. Holding
    the highest database role confers no right to read a membership
    record (`P13-SEC-001`, `P13-SEC-005`)."""

    reason_code = "DATAPLANE_OPERATOR_PRIVILEGE_INSUFFICIENT"


class DatabaseUnavailableError(DataPlaneError, ValueError):
    """The database could not be reached; consequential actions fail
    closed rather than proceeding on cached state (§29)."""

    reason_code = "DATAPLANE_DATABASE_UNAVAILABLE"


class ReplicaStaleError(DataPlaneError, ValueError):
    """A consequential read was attempted against a stale replica (§29)."""

    reason_code = "DATAPLANE_REPLICA_STALE"


# ---------------------------------------------------------------------------
# Codes owned by earlier packs, re-raised rather than shadowed
# (`P13-RSN-005`). Each subclass exists only so PACK-13 call sites can
# raise the *owning pack's* code without inventing a PACK-13 synonym for
# a fact another pack already named.
# ---------------------------------------------------------------------------


class RecordUnderLegalHoldError(DataPlaneError, PermissionError):
    """PACK-09's code: deletion is blocked by a hold. The hold preserves;
    it authorizes nothing (`P13-RET-005`)."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


class LegalHoldStateUnknownError(DataPlaneError, ValueError):
    """PACK-09's code: hold state is unresolvable, so deletion fails
    closed."""

    reason_code = "LEGAL_HOLD_STATE_UNKNOWN"


class OrganizationScopeUndeterminedError(DataPlaneError, ValueError):
    """PACK-09's code: scope is not resolvable."""

    reason_code = "ORGANIZATION_SCOPE_UNDETERMINED"


class OrganizationScopeMismatchError(DataPlaneError, PermissionError):
    """PACK-08's code: a cross-scope act is refused."""

    reason_code = "ORGANIZATION_SCOPE_MISMATCH"


class PermissionDeniedError(DataPlaneError, PermissionError):
    """PACK-02's generic authorization refusal, used only where no
    narrower registered code applies."""

    reason_code = "PERMISSION_DENIED"


class RecordNotFoundError(DataPlaneError, ValueError):
    """PACK-02's code: the record is absent or out of scope."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class OptimisticConcurrencyConflictError(DataPlaneError, ValueError):
    """PACK-09's generic version conflict, used where the narrower
    `CONCURRENCY_STALE_AGGREGATE_VERSION` does not apply."""

    reason_code = "OPTIMISTIC_CONCURRENCY_CONFLICT"


class AuditChainBrokenError(DataPlaneError, ValueError):
    """PACK-02's code: chain verification failed."""

    reason_code = "AUDIT_CHAIN_BROKEN"


class PrivilegeAuthorityMissingError(DataPlaneError, PermissionError):
    """PACK-12's code: migration execution or direct SQL without a scoped
    privileged grant (`P13-SEC-002`)."""

    reason_code = "PRIVILEGE_AUTHORITY_MISSING"


class GovernedRecordDeletionForbiddenError(DataPlaneError, PermissionError):
    """PACK-09's code: deletion of a governed record through a
    storage-level path."""

    reason_code = "GOVERNED_RECORD_DELETION_FORBIDDEN"

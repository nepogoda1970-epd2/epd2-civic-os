"""PACK-09 domain model - Compliance, Records Governance & Legal Workflows.

Owned by `compliance-service` (ADR-038). Six entity families:

1. **Records governance** - `RetentionPolicy`, `RetentionStartEvent`,
   `GovernedRecord`, `DisposalEligibility`, `DestructionAuthorization`,
   `DestructionEvidence` (ADR-039).
2. **Legal Hold** - `LegalHold`, `LegalHoldScope`,
   `LegalHoldHistoryEntry`, `HoldApplicability` (ADR-039).
3. **Data catalog & processing registry** - `DataAsset`,
   `ProcessingActivity`, `LegalBasis` (ADR-040).
4. **Governed procedural cases** - `ProceduralCase`, `CaseRoleAssignment`,
   `CaseDecision`, `AppealReference` (ADR-041).
5. **Deadlines** - `DeadlineDefinition`, `ProceduralDeadline`,
   `DeadlineHistoryEntry` (ADR-041).
6. **Data-subject/legal requests and party arbitration** -
   `DataSubjectRequest`, `DisputeParties`,
   `ConflictOfInterestDeclaration` (ADR-040/ADR-042).

Cross-cutting rules this module enforces *structurally*, so no
application-layer caller can opt out of them:

- **No global user ID (invariant 1).** No entity here carries a
  `user_id`, `person_id`, `member_id`, `account_id` or any other
  identifier intended to be the same value across identity, membership,
  communication, finance, voting and case contexts. Natural persons
  appear only as a `CasePartyReference` - a per-case, randomly minted
  UUID with no meaning and no resolution path outside the case that
  minted it (see `mint_case_party_reference`) - or as an opaque
  `authority_reference` UUID pointing at an organization-service or
  governance-service role assignment, never at a person. Asserted
  structurally by `tests/contract/test_ct00_08_identity_leakage.py`.
- **Explicit timezone handling.** Every `datetime` field on every entity
  is validated timezone-aware at construction (`_require_aware`). Every
  deadline additionally carries an explicit IANA `timezone` string whose
  validity is checked with `zoneinfo` - due-date arithmetic never
  silently assumes UTC (invariant 15).
- **Append-only deadline history (invariant 6).** `ProceduralDeadline`
  has no settable `due_at`/`status`: both are *derived* from an
  append-only `history` tuple. Every transition appends a
  `DeadlineHistoryEntry` recording `due_at_before`/`due_at_after`; no
  entry is ever rewritten or dropped, so a suspension, extension,
  resumption, completion or expiration can never overwrite what came
  before.
- **No voting linkage (invariant 12).** No entity references a `Ballot`,
  `VoteEnvelope`, `Tally`, `ResultPublication` or `Delegation`, and this
  module imports nothing from those packages. Asserted by
  `tests/contract/test_ct00_09_vote_linkability.py` and by
  `tests/repository/test_service_boundaries.py`.
- **No document bytes.** Evidence is always a *reference*
  (`evidence_references`), never content - document storage and
  cryptographic version chains are deferred to PACK-11 (ADR-038).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from epd2_compliance_service.exceptions import (
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    DataSubjectRequestTransitionInvalidError,
    DeadlineTimezoneUndeterminedError,
    DeadlineTransitionInvalidError,
    LegalHoldPropagationUnresolvedError,
    LegalHoldScopeMismatchError,
    LegalHoldTransitionInvalidError,
    ProceduralCaseTransitionInvalidError,
    ProceduralIndependenceViolationError,
    ProceduralRoleConflictError,
    ProcessingActivityTransitionInvalidError,
    ProcessingRegistryIdentityPayloadRejectedError,
    ProcessingRegistryIncompleteError,
)
from epd2_core.identifiers import generate_uuid

# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

#: Field/attribute names this service refuses to accept anywhere in a
#: registry or case payload, because storing them would turn
#: compliance-service into a second identity store (invariant 11) or
#: reintroduce a global person identifier (invariant 1). Checked by
#: `reject_identity_payload_keys`.
FORBIDDEN_IDENTITY_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "address",
        "authentication_secret",
        "credential_secret",
        "date_of_birth",
        "eid_attributes",
        "eid_token",
        "email",
        "first_name",
        "full_name",
        "given_name",
        "global_user_id",
        "identity_document_number",
        "identity_id",
        "identity_record",
        "kyc_payload",
        "last_name",
        "member_id",
        "national_id",
        "passport_number",
        "person_id",
        "phone",
        "phone_number",
        "surname",
        "tax_id",
        "user_id",
    }
)


def _require_aware(value: datetime, field_name: str) -> None:
    """Every datetime crossing this service's boundary must be
    timezone-aware. A naive datetime is a hard construction error, never
    a value silently interpreted as UTC."""
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def require_timezone(timezone_name: str) -> ZoneInfo:
    """Resolve an explicit IANA timezone name, or refuse to proceed.

    Deadline arithmetic is only meaningful against a named civil
    timezone; an empty, missing or unknown name is a fail-closed refusal
    (`DeadlineTimezoneUndeterminedError`), never a silent fallback to
    UTC."""
    if not timezone_name:
        raise DeadlineTimezoneUndeterminedError("an explicit IANA timezone name is required")
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise DeadlineTimezoneUndeterminedError(f"unknown IANA timezone {timezone_name!r}") from exc


def reject_identity_payload_keys(payload: dict[str, str], *, where: str) -> None:
    """Raise if `payload` carries any field name from
    `FORBIDDEN_IDENTITY_FIELD_NAMES` (invariants 1, 11 and 13).

    Applied to every free-form metadata mapping this service accepts, so
    a caller cannot smuggle identity attributes into the compliance store
    (or, transitively, into an audit payload) by nesting them in an
    otherwise-permitted field."""
    offending = sorted(set(payload) & FORBIDDEN_IDENTITY_FIELD_NAMES)
    if offending:
        raise ProcessingRegistryIdentityPayloadRejectedError(
            f"{where} may not carry identity field(s): {offending}"
        )


class ScopeCapability(StrEnum):
    """What a cross-scope authority grant permits its holder to do inside
    another organization's scope.

    Deliberately narrow and enumerated: there is no "all" capability and
    no wildcard, so a grant can never quietly widen."""

    READ_CASE = "read_case"
    MANAGE_CASE = "manage_case"
    MANAGE_DEADLINE = "manage_deadline"
    READ_PROCESSING_REGISTRY = "read_processing_registry"
    AUTHORIZE_DESTRUCTION = "authorize_destruction"


@dataclass(frozen=True, slots=True)
class CrossScopeAuthorityGrant:
    """An explicit, time-bounded permission for `grantee_organization_id`
    to exercise `capabilities` inside `granting_organization_id`.

    This is the *only* way any organizational boundary is crossed in
    PACK-09. There is no hierarchy-derived inheritance: a Bund-level
    organization holds nothing over a Landesverband's cases unless that
    Landesverband issued a grant, and a Kreisverband holds nothing over
    its parent Land's cases either (invariant 2). The grant must also be
    *presented* by the caller (`RequestContext.authority_references`) -
    merely existing in the store is not enough, so an over-broad standing
    grant cannot be exercised by accident."""

    grant_id: UUID
    granting_organization_id: UUID
    grantee_organization_id: UUID
    capabilities: frozenset[ScopeCapability]
    valid_from: datetime
    valid_until: datetime | None
    authorizing_decision_reference: UUID
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "valid_until")
        if self.revoked_at is not None:
            _require_aware(self.revoked_at, "revoked_at")
        if not self.capabilities:
            raise ValueError("a cross-scope authority grant must name at least one capability")
        if self.granting_organization_id == self.grantee_organization_id:
            raise ValueError("a cross-scope grant must name two different organizations")

    def permits(
        self,
        *,
        granting_organization_id: UUID,
        grantee_organization_id: UUID,
        capability: ScopeCapability,
        at: datetime,
    ) -> bool:
        _require_aware(at, "at")
        if self.revoked_at is not None and at >= self.revoked_at:
            return False
        if at < self.valid_from:
            return False
        if self.valid_until is not None and at >= self.valid_until:
            return False
        return (
            self.granting_organization_id == granting_organization_id
            and self.grantee_organization_id == grantee_organization_id
            and capability in self.capabilities
        )


def mint_case_party_reference() -> UUID:
    """Mint a fresh, meaningless, per-case party handle.

    This is how a natural person appears anywhere in PACK-09: as a
    randomly generated UUID minted *for one case*, never reused across
    cases, never derived from any identity/membership/account value, and
    with no resolution path inside this service. Two cases involving the
    same real person carry two unrelated references, which is exactly
    what invariant 1 ("no global user ID") requires."""
    return generate_uuid()


# ---------------------------------------------------------------------------
# 1. Records governance
# ---------------------------------------------------------------------------


class RecordSensitivity(StrEnum):
    """Classification level of a governed record (ADR-039)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RetentionTrigger(StrEnum):
    """The real-world event that starts a retention period running."""

    CREATED_AT = "created_at"
    CASE_CLOSED_AT = "case_closed_at"
    MEMBERSHIP_ENDED_AT = "membership_ended_at"
    CONTRACT_ENDED_AT = "contract_ended_at"
    PROCESSING_ENDED_AT = "processing_ended_at"


class DispositionAction(StrEnum):
    """What a retention policy prescribes once retention expires."""

    DELETE = "delete"
    ANONYMIZE = "anonymize"
    ARCHIVE = "archive"
    REVIEW = "review"


#: Disposition actions that physically destroy or irreversibly alter the
#: governed material. Only these are blocked by an active Legal Hold
#: (invariant 3); `archive`/`review` are non-destructive and stay
#: available so a held record can still be moved into managed storage or
#: put in front of a reviewer.
DESTRUCTIVE_DISPOSITION_ACTIONS: frozenset[DispositionAction] = frozenset(
    {DispositionAction.DELETE, DispositionAction.ANONYMIZE}
)


class GovernedRecordState(StrEnum):
    """Lifecycle of a governed record's *metadata* (never its content -
    compliance-service holds no document bytes)."""

    ACTIVE = "active"
    DISPOSAL_AUTHORIZED = "disposal_authorized"
    DESTROYED = "destroyed"


_ALLOWED_RECORD_TRANSITIONS: frozenset[tuple[GovernedRecordState, GovernedRecordState]] = frozenset(
    {
        (GovernedRecordState.ACTIVE, GovernedRecordState.DISPOSAL_AUTHORIZED),
        # An authorization can be withdrawn (or invalidated by a policy
        # supersession) - back to `active`, never straight to destroyed.
        (GovernedRecordState.DISPOSAL_AUTHORIZED, GovernedRecordState.ACTIVE),
        (GovernedRecordState.DISPOSAL_AUTHORIZED, GovernedRecordState.DESTROYED),
    }
)


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """A versioned retention schedule for one record class in one
    organization (ADR-039).

    `(policy_id, policy_version)` is unique: superseding a policy always
    creates a NEW record with an incremented `policy_version` and sets
    `supersedes_policy_version` - the previous version's row is never
    rewritten, so what a past disposal decision was made under stays
    answerable."""

    policy_id: UUID
    organization_id: UUID
    record_class: str
    trigger: RetentionTrigger
    retention_days: int
    disposition_action: DispositionAction
    policy_version: int
    valid_from: datetime
    valid_until: datetime | None = None
    supersedes_policy_version: int | None = None
    authorizing_decision_reference: UUID | None = None

    def __post_init__(self) -> None:
        if self.retention_days < 0:
            raise ValueError("retention_days must be non-negative")
        if self.policy_version < 1:
            raise ValueError("policy_version must be a positive integer")
        if self.supersedes_policy_version is not None and (
            self.supersedes_policy_version >= self.policy_version
        ):
            raise ValueError("supersedes_policy_version must be lower than policy_version")
        _require_text(self.record_class, "record_class")
        _require_aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be after valid_from")

    def due_at(self, retention_start: datetime) -> datetime:
        """The instant at which retention expires for a record whose
        retention started at `retention_start`."""
        _require_aware(retention_start, "retention_start")
        return retention_start + timedelta(days=self.retention_days)

    def is_effective_at(self, at: datetime) -> bool:
        _require_aware(at, "at")
        if at < self.valid_from:
            return False
        return self.valid_until is None or at < self.valid_until


@dataclass(frozen=True, slots=True)
class RetentionStartEvent:
    """An explicit, recorded retention-start fact.

    Retention never starts implicitly: until one of these exists for a
    record, disposal-eligibility evaluation fails closed with
    `RetentionStartUndeterminedError` (invariant 15)."""

    retention_start_event_id: UUID
    record_id: UUID
    organization_id: UUID
    trigger: RetentionTrigger
    occurred_at: datetime
    recorded_at: datetime
    source_reference: str

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_aware(self.recorded_at, "recorded_at")
        _require_text(self.source_reference, "source_reference")
        if self.recorded_at < self.occurred_at:
            raise ValueError("recorded_at must not be before occurred_at")


@dataclass(frozen=True, slots=True)
class GovernedRecord:
    """Compliance-side *metadata* about a record another service owns.

    `source_reference` is an opaque pointer back to the owning service's
    own object (e.g. `"membership-service:membership:<uuid>"`); this
    service never holds the record's content, and deliberately has no
    field that could carry it."""

    record_id: UUID
    organization_id: UUID
    record_class: str
    sensitivity: RecordSensitivity
    created_at: datetime
    retention_policy_id: UUID
    retention_policy_version: int
    source_reference: str
    state: GovernedRecordState = GovernedRecordState.ACTIVE
    record_version: int = 1
    retention_start_at: datetime | None = None
    destruction_authorization_id: UUID | None = None
    destruction_evidence_id: UUID | None = None

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")
        _require_text(self.record_class, "record_class")
        _require_text(self.source_reference, "source_reference")
        if self.retention_policy_version < 1:
            raise ValueError("retention_policy_version must be a positive integer")
        if self.record_version < 1:
            raise ValueError("record_version must be a positive integer")
        if self.retention_start_at is not None:
            _require_aware(self.retention_start_at, "retention_start_at")
        if self.state is GovernedRecordState.DESTROYED and self.destruction_evidence_id is None:
            raise ValueError("a destroyed record must reference its destruction evidence")

    def with_state(self, target: GovernedRecordState) -> GovernedRecord:
        if (self.state, target) not in _ALLOWED_RECORD_TRANSITIONS:
            raise ProceduralCaseTransitionInvalidError(
                f"invalid governed-record transition {self.state.value} -> {target.value}"
            )
        return replace(self, state=target, record_version=self.record_version + 1)

    def with_destruction_evidence(self, evidence_id: UUID) -> GovernedRecord:
        """Move to `destroyed` and attach the evidence reference in one
        construction.

        A separate method rather than `with_state(DESTROYED)` followed by
        a `replace`, because `__post_init__` refuses a `destroyed` record
        that carries no evidence reference - the two facts are one
        transition, and there is deliberately no intermediate state where
        a record is destroyed with nothing proving it."""
        if (self.state, GovernedRecordState.DESTROYED) not in _ALLOWED_RECORD_TRANSITIONS:
            raise ProceduralCaseTransitionInvalidError(
                f"invalid governed-record transition {self.state.value} -> destroyed"
            )
        return replace(
            self,
            state=GovernedRecordState.DESTROYED,
            destruction_evidence_id=evidence_id,
            record_version=self.record_version + 1,
        )

    def with_retention_start(self, start_event: RetentionStartEvent) -> GovernedRecord:
        if start_event.record_id != self.record_id:
            raise ValueError("retention start event does not belong to this record")
        if start_event.organization_id != self.organization_id:
            raise LegalHoldScopeMismatchError(
                "retention start event organization does not match the record's"
            )
        return replace(
            self,
            retention_start_at=start_event.occurred_at,
            record_version=self.record_version + 1,
        )

    def rebound_to_policy_version(self, policy_version: int) -> GovernedRecord:
        """Move this record onto a newer version of its retention policy.

        Always resets `state` to `active` and drops any standing
        `destruction_authorization_id`: an authorization issued under the
        superseded version can never survive the supersession, which is
        the structural half of invariant 5 (no policy rewrite may
        silently authorize destruction)."""
        if policy_version < 1:
            raise ValueError("policy_version must be a positive integer")
        if self.state is GovernedRecordState.DESTROYED:
            raise ProceduralCaseTransitionInvalidError(
                "a destroyed record cannot be rebound to a new retention policy version"
            )
        return replace(
            self,
            retention_policy_version=policy_version,
            state=GovernedRecordState.ACTIVE,
            destruction_authorization_id=None,
            record_version=self.record_version + 1,
        )


@dataclass(frozen=True, slots=True)
class DisposalEligibility:
    """The deterministic outcome of evaluating one record against its
    policy and every applicable Legal Hold.

    `eligible` is only ever `True` when the retention start is known, the
    due time has passed, and no active or indeterminate hold applies;
    every other outcome carries the `reason_code` explaining the
    refusal."""

    record_id: UUID
    organization_id: UUID
    evaluated_at: datetime
    retention_policy_id: UUID
    retention_policy_version: int
    due_at: datetime | None
    eligible: bool
    reason_code: str | None
    blocking_hold_ids: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.evaluated_at, "evaluated_at")
        if self.due_at is not None:
            _require_aware(self.due_at, "due_at")
        if self.eligible and self.reason_code is not None:
            raise ValueError("an eligible evaluation must not carry a refusal reason code")
        if not self.eligible and not self.reason_code:
            raise ValueError("an ineligible evaluation must carry a reason code")
        if self.eligible and self.blocking_hold_ids:
            raise ValueError("an eligible evaluation must not list blocking holds")


@dataclass(frozen=True, slots=True)
class DestructionAuthorization:
    """A separate, explicit authorization step between "eligible" and
    "destroyed" (invariant 4).

    Bound to the exact `retention_policy_version` and `record_version` it
    was issued against, so a later policy supersession or record change
    makes it stale (`DestructionAuthorizationStaleError`) instead of
    silently remaining usable."""

    authorization_id: UUID
    record_id: UUID
    organization_id: UUID
    disposition_action: DispositionAction
    retention_policy_id: UUID
    retention_policy_version: int
    authorized_record_version: int
    authorized_at: datetime
    authorized_by_authority_reference: UUID
    eligibility_evaluated_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.authorized_at, "authorized_at")
        _require_aware(self.eligibility_evaluated_at, "eligibility_evaluated_at")
        if self.authorized_at < self.eligibility_evaluated_at:
            raise ValueError("authorized_at must not precede eligibility_evaluated_at")
        if self.retention_policy_version < 1 or self.authorized_record_version < 1:
            raise ValueError("policy and record versions must be positive integers")


@dataclass(frozen=True, slots=True)
class DestructionEvidence:
    """Immutable proof that a destruction actually happened.

    Created exactly once per record (enforced by
    `application.execute_destruction` plus the store's own
    `create_once`), never updated and never deleted - it outlives the
    record whose destruction it evidences, which is the whole point.

    `evidence_digest` is an opaque, caller-computed digest of whatever
    the executing system considers its proof (a tombstone id, a storage
    receipt). No document bytes and no personal payload are stored here
    (invariant 13); PACK-11 owns real evidence content."""

    evidence_id: UUID
    record_id: UUID
    organization_id: UUID
    authorization_id: UUID
    disposition_action: DispositionAction
    executed_at: datetime
    executed_by_authority_reference: UUID
    evidence_digest: str
    retention_policy_id: UUID
    retention_policy_version: int

    def __post_init__(self) -> None:
        _require_aware(self.executed_at, "executed_at")
        _require_text(self.evidence_digest, "evidence_digest")
        if self.retention_policy_version < 1:
            raise ValueError("retention_policy_version must be a positive integer")


# ---------------------------------------------------------------------------
# 2. Legal Hold
# ---------------------------------------------------------------------------


class LegalHoldStatus(StrEnum):
    """Lifecycle of a Legal Hold.

    `INDETERMINATE` is a real, storable state, not a placeholder: it is
    what a hold record carries when its authority source could not be
    confirmed. Any record touched by an indeterminate hold fails closed
    with `LegalHoldStateUnknownError` rather than being treated as
    unheld (invariant 15)."""

    ACTIVE = "active"
    RELEASED = "released"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class LegalHoldScope:
    """What a hold covers. All three dimensions are additive (a record is
    covered if it matches *any* of them), and all are evaluated only
    within the hold's own organization."""

    record_ids: frozenset[UUID] = frozenset()
    record_classes: frozenset[str] = frozenset()
    case_ids: frozenset[UUID] = frozenset()

    def __post_init__(self) -> None:
        if not self.record_ids and not self.record_classes and not self.case_ids:
            raise ValueError("a Legal Hold scope must name at least one record, class or case")


@dataclass(frozen=True, slots=True)
class LegalHoldHistoryEntry:
    """One append-only entry in a hold's own audit history."""

    sequence: int
    occurred_at: datetime
    action: str
    reason_code: str
    actor_authority_reference: UUID
    status_after: LegalHoldStatus

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_text(self.action, "action")
        _require_text(self.reason_code, "reason_code")
        if self.sequence < 1:
            raise ValueError("sequence must be a positive integer")


@dataclass(frozen=True, slots=True)
class LegalHold:
    """A Legal Hold over governed records in one organization (ADR-039).

    `history` is append-only: `release` appends, it never rewrites the
    issue entry."""

    hold_id: UUID
    organization_id: UUID
    matter_reference: str
    scope: LegalHoldScope
    issued_at: datetime
    issued_by_authority_reference: UUID
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    released_at: datetime | None = None
    released_by_authority_reference: UUID | None = None
    history: tuple[LegalHoldHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.issued_at, "issued_at")
        _require_text(self.matter_reference, "matter_reference")
        if self.status is LegalHoldStatus.RELEASED and self.released_at is None:
            raise ValueError("a released hold must carry released_at")
        if self.released_at is not None:
            _require_aware(self.released_at, "released_at")
            if self.released_at < self.issued_at:
                raise ValueError("released_at must not precede issued_at")

    def covers(self, record: GovernedRecord) -> bool:
        """Whether this hold's *scope* names `record`, independent of the
        hold's status.

        Scope matching never crosses organizations: a hold issued by one
        organization can never reach another's record even if the record
        id were guessed (invariant 2)."""
        if self.organization_id != record.organization_id:
            return False
        return (
            record.record_id in self.scope.record_ids
            or record.record_class in self.scope.record_classes
        )

    def is_blocking(self, record: GovernedRecord) -> bool:
        """Whether this hold *actively* blocks destruction of `record`.

        An `INDETERMINATE` hold is deliberately NOT reported as blocking
        here: the caller must distinguish it, because "unknown" is a
        fail-closed refusal with its own reason code, not the same
        outcome as a known active hold."""
        return self.status is LegalHoldStatus.ACTIVE and self.covers(record)

    def is_indeterminate_for(self, record: GovernedRecord) -> bool:
        return self.status is LegalHoldStatus.INDETERMINATE and self.covers(record)

    def _next_sequence(self) -> int:
        return len(self.history) + 1

    def with_issue_entry(self, *, reason_code: str) -> LegalHold:
        entry = LegalHoldHistoryEntry(
            sequence=self._next_sequence(),
            occurred_at=self.issued_at,
            action="issued",
            reason_code=reason_code,
            actor_authority_reference=self.issued_by_authority_reference,
            status_after=self.status,
        )
        return replace(self, history=(*self.history, entry))

    def release(
        self, at: datetime, *, released_by_authority_reference: UUID, reason_code: str
    ) -> LegalHold:
        """Release this hold, appending (never overwriting) history."""
        _require_aware(at, "at")
        if self.status is not LegalHoldStatus.ACTIVE:
            raise LegalHoldTransitionInvalidError(
                f"only an active Legal Hold can be released; this one is {self.status.value}"
            )
        if at < self.issued_at:
            raise LegalHoldTransitionInvalidError("release time must not precede issue time")
        entry = LegalHoldHistoryEntry(
            sequence=self._next_sequence(),
            occurred_at=at,
            action="released",
            reason_code=reason_code,
            actor_authority_reference=released_by_authority_reference,
            status_after=LegalHoldStatus.RELEASED,
        )
        return replace(
            self,
            status=LegalHoldStatus.RELEASED,
            released_at=at,
            released_by_authority_reference=released_by_authority_reference,
            history=(*self.history, entry),
        )

    def mark_indeterminate(
        self, at: datetime, *, actor_authority_reference: UUID, reason_code: str
    ) -> LegalHold:
        """Record that this hold's authority could no longer be
        confirmed. Every covered record now fails closed."""
        _require_aware(at, "at")
        if self.status is LegalHoldStatus.RELEASED:
            raise LegalHoldTransitionInvalidError(
                "a released Legal Hold cannot become indeterminate"
            )
        entry = LegalHoldHistoryEntry(
            sequence=self._next_sequence(),
            occurred_at=at,
            action="marked_indeterminate",
            reason_code=reason_code,
            actor_authority_reference=actor_authority_reference,
            status_after=LegalHoldStatus.INDETERMINATE,
        )
        return replace(self, status=LegalHoldStatus.INDETERMINATE, history=(*self.history, entry))


@dataclass(frozen=True, slots=True)
class HoldApplicability:
    """The resolved hold picture for one record at one instant."""

    record_id: UUID
    blocking_hold_ids: tuple[UUID, ...]
    indeterminate_hold_ids: tuple[UUID, ...]

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocking_hold_ids)

    @property
    def is_undetermined(self) -> bool:
        return bool(self.indeterminate_hold_ids)


def evaluate_hold_applicability(
    record: GovernedRecord, holds: tuple[LegalHold, ...]
) -> HoldApplicability:
    """Resolve every hold in `holds` against `record`.

    Pure function, no storage access - the application layer supplies the
    candidate holds so this stays deterministic and directly testable."""
    blocking = tuple(hold.hold_id for hold in holds if hold.is_blocking(record))
    indeterminate = tuple(hold.hold_id for hold in holds if hold.is_indeterminate_for(record))
    return HoldApplicability(
        record_id=record.record_id,
        blocking_hold_ids=blocking,
        indeterminate_hold_ids=indeterminate,
    )


# ---------------------------------------------------------------------------
# 3. Data catalog & processing registry
# ---------------------------------------------------------------------------


class LegalBasis(StrEnum):
    """A *managed* classification of the legal basis a processing
    activity is recorded under (ADR-040).

    Making this an enum rather than free text is what "legal basis as a
    managed field" means here: the value is drawn from a closed,
    reviewable list so the registry can be queried and audited. It
    explicitly makes NO claim that the chosen basis is legally
    sufficient, correctly chosen, or that recording it satisfies GDPR,
    BDSG or party law - that determination stays a human legal judgement
    outside this system (ADR-040)."""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"
    PARTY_STATUTE = "party_statute"
    OTHER_DOCUMENTED = "other_documented"


class RegistryEntryStatus(StrEnum):
    """Lifecycle shared by `DataAsset` and `ProcessingActivity`."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


_ALLOWED_REGISTRY_TRANSITIONS: frozenset[tuple[RegistryEntryStatus, RegistryEntryStatus]] = (
    frozenset(
        {
            (RegistryEntryStatus.DRAFT, RegistryEntryStatus.ACTIVE),
            (RegistryEntryStatus.DRAFT, RegistryEntryStatus.DEPRECATED),
            (RegistryEntryStatus.ACTIVE, RegistryEntryStatus.SUSPENDED),
            (RegistryEntryStatus.SUSPENDED, RegistryEntryStatus.ACTIVE),
            (RegistryEntryStatus.ACTIVE, RegistryEntryStatus.DEPRECATED),
            (RegistryEntryStatus.SUSPENDED, RegistryEntryStatus.DEPRECATED),
        }
    )
)


@dataclass(frozen=True, slots=True)
class DataAsset:
    """A Data Catalog entry: one governed store/dataset in one
    organization, tied to the record class and retention policy that
    govern it."""

    asset_id: UUID
    organization_id: UUID
    name: str
    asset_class: str
    system_reference: str
    record_class: str
    retention_policy_reference: UUID
    status: RegistryEntryStatus
    valid_from: datetime
    owner_authority_reference: UUID
    asset_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.valid_from, "valid_from")
        for name, value in (
            ("name", self.name),
            ("asset_class", self.asset_class),
            ("system_reference", self.system_reference),
            ("record_class", self.record_class),
        ):
            if not value or not value.strip():
                raise ProcessingRegistryIncompleteError(f"DataAsset.{name} is required")
        if self.asset_version < 1:
            raise ValueError("asset_version must be a positive integer")

    def with_status(self, target: RegistryEntryStatus) -> DataAsset:
        if (self.status, target) not in _ALLOWED_REGISTRY_TRANSITIONS:
            raise ProcessingActivityTransitionInvalidError(
                f"invalid data-asset transition {self.status.value} -> {target.value}"
            )
        return replace(self, status=target, asset_version=self.asset_version + 1)


@dataclass(frozen=True, slots=True)
class ProcessingActivity:
    """A Processing Registry entry (ADR-040).

    Everything here is *categorical*: categories of data, categories of
    data subjects, categories of recipients. No individual data subject
    is ever named, and `reject_identity_payload_keys` is applied to the
    optional `additional_metadata` mapping so none can be smuggled in."""

    activity_id: UUID
    organization_id: UUID
    name: str
    purpose: str
    legal_basis: LegalBasis
    data_subject_categories: tuple[str, ...]
    personal_data_categories: tuple[str, ...]
    recipient_categories: tuple[str, ...]
    retention_policy_reference: UUID
    technical_organizational_measures: tuple[str, ...]
    controller_reference: UUID
    process_owner_authority_reference: UUID
    system_references: tuple[str, ...]
    status: RegistryEntryStatus
    valid_from: datetime
    data_asset_references: tuple[UUID, ...] = ()
    activity_version: int = 1
    supersedes_activity_version: int | None = None
    dpo_review_reference: UUID | None = None
    additional_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_aware(self.valid_from, "valid_from")
        if self.activity_version < 1:
            raise ValueError("activity_version must be a positive integer")
        if self.supersedes_activity_version is not None and (
            self.supersedes_activity_version >= self.activity_version
        ):
            raise ValueError("supersedes_activity_version must be lower than activity_version")
        for name, text in (("name", self.name), ("purpose", self.purpose)):
            if not text or not text.strip():
                raise ProcessingRegistryIncompleteError(f"ProcessingActivity.{name} is required")
        for name, values in (
            ("data_subject_categories", self.data_subject_categories),
            ("personal_data_categories", self.personal_data_categories),
            ("technical_organizational_measures", self.technical_organizational_measures),
            ("system_references", self.system_references),
        ):
            if not values:
                raise ProcessingRegistryIncompleteError(
                    f"ProcessingActivity.{name} must list at least one entry"
                )
        reject_identity_payload_keys(
            dict(self.additional_metadata), where="ProcessingActivity.additional_metadata"
        )

    def with_status(self, target: RegistryEntryStatus) -> ProcessingActivity:
        if (self.status, target) not in _ALLOWED_REGISTRY_TRANSITIONS:
            raise ProcessingActivityTransitionInvalidError(
                f"invalid processing-activity transition {self.status.value} -> {target.value}"
            )
        return replace(self, status=target, activity_version=self.activity_version + 1)


# ---------------------------------------------------------------------------
# 4. Governed procedural cases
# ---------------------------------------------------------------------------


class CaseType(StrEnum):
    DATA_SUBJECT_REQUEST = "data_subject_request"
    COMPLIANCE_REVIEW = "compliance_review"
    PARTY_ARBITRATION = "party_arbitration"
    INTERNAL_DISPUTE = "internal_dispute"
    LEGAL_REQUEST = "legal_request"


class CaseStatus(StrEnum):
    OPEN = "open"
    ADMISSIBILITY_REVIEW = "admissibility_review"
    ACTIVE = "active"
    STAYED = "stayed"
    DECIDED = "decided"
    CLOSED = "closed"


_ALLOWED_CASE_TRANSITIONS: frozenset[tuple[CaseStatus, CaseStatus]] = frozenset(
    {
        (CaseStatus.OPEN, CaseStatus.ADMISSIBILITY_REVIEW),
        (CaseStatus.ADMISSIBILITY_REVIEW, CaseStatus.ACTIVE),
        (CaseStatus.ADMISSIBILITY_REVIEW, CaseStatus.CLOSED),
        (CaseStatus.ACTIVE, CaseStatus.STAYED),
        (CaseStatus.STAYED, CaseStatus.ACTIVE),
        (CaseStatus.ACTIVE, CaseStatus.DECIDED),
        (CaseStatus.DECIDED, CaseStatus.CLOSED),
    }
)


class ProceduralRole(StrEnum):
    """The distinguishable procedural roles (invariant 8).

    `PROCEDURAL_AUTHORITY` (who owns the procedure), `CASE_HANDLER` (who
    runs it day to day) and `INDEPENDENT_DECISION_MAKER` (who decides)
    are three separate roles that may never be held by the same party
    reference on one case."""

    PROCEDURAL_AUTHORITY = "procedural_authority"
    CASE_HANDLER = "case_handler"
    INDEPENDENT_DECISION_MAKER = "independent_decision_maker"
    CLAIMANT = "claimant"
    RESPONDENT = "respondent"
    SUBMITTER = "submitter"


#: The three roles that must stay mutually exclusive on any one case.
SEPARATED_ROLES: frozenset[ProceduralRole] = frozenset(
    {
        ProceduralRole.PROCEDURAL_AUTHORITY,
        ProceduralRole.CASE_HANDLER,
        ProceduralRole.INDEPENDENT_DECISION_MAKER,
    }
)

#: Roles whose holder is a party to the dispute and therefore can never
#: also be the independent decision-maker (invariant 9).
PARTY_ROLES: frozenset[ProceduralRole] = frozenset(
    {ProceduralRole.CLAIMANT, ProceduralRole.RESPONDENT, ProceduralRole.SUBMITTER}
)


@dataclass(frozen=True, slots=True)
class CaseRoleAssignment:
    """Who holds which procedural role on one case.

    `party_reference` is a `mint_case_party_reference()` handle or an
    opaque authority reference - never a person identifier
    (invariant 1)."""

    assignment_id: UUID
    case_id: UUID
    organization_id: UUID
    role: ProceduralRole
    party_reference: UUID
    assigned_at: datetime
    assigned_by_party_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.assigned_at, "assigned_at")


class ConflictState(StrEnum):
    """An explicit conflict-of-interest state, never free text
    (invariant 10). Each value changes what the workflow permits."""

    NONE_DECLARED = "none_declared"
    DECLARED = "declared"
    CONFIRMED = "confirmed"
    WAIVED = "waived"


#: Conflict states that make a party ineligible to take a separated
#: procedural role or to record a decision.
BLOCKING_CONFLICT_STATES: frozenset[ConflictState] = frozenset(
    {ConflictState.DECLARED, ConflictState.CONFIRMED}
)


@dataclass(frozen=True, slots=True)
class ConflictOfInterestDeclaration:
    """A conflict declaration attached to one party on one case.

    `basis_code` is a short, closed-vocabulary marker (e.g.
    `"same_local_branch"`); the human narrative, if any, lives in a
    referenced document under PACK-11, never here."""

    declaration_id: UUID
    case_id: UUID
    organization_id: UUID
    party_reference: UUID
    state: ConflictState
    basis_code: str
    declared_at: datetime
    decided_by_party_reference: UUID | None = None
    decided_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_aware(self.declared_at, "declared_at")
        _require_text(self.basis_code, "basis_code")
        if self.decided_at is not None:
            _require_aware(self.decided_at, "decided_at")
        if self.state in {ConflictState.CONFIRMED, ConflictState.WAIVED} and (
            self.decided_by_party_reference is None or self.decided_at is None
        ):
            raise ValueError(
                "a confirmed or waived conflict declaration must record who decided it and when"
            )

    @property
    def is_blocking(self) -> bool:
        return self.state in BLOCKING_CONFLICT_STATES


class DecisionOutcome(StrEnum):
    UPHELD = "upheld"
    PARTIALLY_UPHELD = "partially_upheld"
    DISMISSED = "dismissed"
    INADMISSIBLE = "inadmissible"
    SETTLED = "settled"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class CaseDecision:
    """The decision record of a governed case (ADR-041/ADR-042).

    Evidence is referenced, never embedded (`evidence_references`)."""

    decision_id: UUID
    case_id: UUID
    organization_id: UUID
    outcome: DecisionOutcome
    reason_code: str
    decided_at: datetime
    decided_by_party_reference: UUID
    decided_by_role: ProceduralRole
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.decided_at, "decided_at")
        _require_text(self.reason_code, "reason_code")


@dataclass(frozen=True, slots=True)
class AppealReference:
    """A link from a decided case to the separate case that reviews it.

    An appeal is never an in-place mutation of the original case; it is
    its own governed case plus this reference (ADR-042)."""

    appeal_id: UUID
    organization_id: UUID
    original_case_id: UUID
    appeal_case_id: UUID
    filed_at: datetime
    filed_by_party_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.filed_at, "filed_at")
        if self.original_case_id == self.appeal_case_id:
            raise ValueError("an appeal must reference a different case than the original")


@dataclass(frozen=True, slots=True)
class ProceduralStep:
    """One required step in a case's workflow."""

    step_code: str
    required: bool
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_text(self.step_code, "step_code")
        if self.completed_at is not None:
            _require_aware(self.completed_at, "completed_at")

    @property
    def is_outstanding(self) -> bool:
        return self.required and self.completed_at is None


@dataclass(frozen=True, slots=True)
class ProceduralCase:
    """A legally governed case (ADR-041).

    `procedural_authority_reference`, `case_handler_reference` and
    `assigned_decision_maker_reference` are always three distinct
    references (invariant 8), enforced in `__post_init__` so no
    construction path can produce a case that violates it. The
    decision-maker is assigned only through
    `application.assign_independent_decision_maker`, which additionally
    enforces invariants 9 and 10."""

    case_id: UUID
    organization_id: UUID
    case_type: CaseType
    status: CaseStatus
    opened_at: datetime
    subject_reference: str
    procedural_authority_reference: UUID
    workflow_type: str
    required_steps: tuple[ProceduralStep, ...] = ()
    evidence_references: tuple[str, ...] = ()
    case_handler_reference: UUID | None = None
    assigned_decision_maker_reference: UUID | None = None
    decision_id: UUID | None = None
    closure_reason_code: str | None = None
    closed_at: datetime | None = None
    case_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.opened_at, "opened_at")
        _require_text(self.subject_reference, "subject_reference")
        _require_text(self.workflow_type, "workflow_type")
        if self.case_version < 1:
            raise ValueError("case_version must be a positive integer")
        if self.closed_at is not None:
            _require_aware(self.closed_at, "closed_at")
        if self.status is CaseStatus.CLOSED and self.closure_reason_code is None:
            raise ValueError("a closed case must carry a closure reason code")
        distinct = [
            reference
            for reference in (
                self.procedural_authority_reference,
                self.case_handler_reference,
                self.assigned_decision_maker_reference,
            )
            if reference is not None
        ]
        if len(distinct) != len(set(distinct)):
            raise ProceduralRoleConflictError(
                "procedural authority, case handler and independent decision-maker "
                "must be three distinct references"
            )

    @property
    def outstanding_steps(self) -> tuple[str, ...]:
        return tuple(step.step_code for step in self.required_steps if step.is_outstanding)

    def transition(
        self, target: CaseStatus, at: datetime, *, closure_reason_code: str | None = None
    ) -> ProceduralCase:
        _require_aware(at, "at")
        if (self.status, target) not in _ALLOWED_CASE_TRANSITIONS:
            raise ProceduralCaseTransitionInvalidError(
                f"invalid case transition {self.status.value} -> {target.value}"
            )
        if target is CaseStatus.CLOSED and not closure_reason_code:
            raise ProceduralCaseTransitionInvalidError(
                "closing a case requires an explicit closure reason code"
            )
        if target is CaseStatus.DECIDED and self.decision_id is None:
            raise ProceduralCaseTransitionInvalidError(
                "a case cannot move to decided before its decision is recorded"
            )
        return replace(
            self,
            status=target,
            closed_at=at if target is CaseStatus.CLOSED else self.closed_at,
            closure_reason_code=(
                closure_reason_code if target is CaseStatus.CLOSED else self.closure_reason_code
            ),
            case_version=self.case_version + 1,
        )

    def with_case_handler(self, party_reference: UUID) -> ProceduralCase:
        if party_reference == self.procedural_authority_reference:
            raise ProceduralRoleConflictError(
                "the procedural authority may not also be the case handler"
            )
        if party_reference == self.assigned_decision_maker_reference:
            raise ProceduralRoleConflictError(
                "the independent decision-maker may not also be the case handler"
            )
        return replace(
            self, case_handler_reference=party_reference, case_version=self.case_version + 1
        )

    def with_decision_maker(self, party_reference: UUID) -> ProceduralCase:
        if party_reference in {
            self.procedural_authority_reference,
            self.case_handler_reference,
        }:
            raise ProceduralIndependenceViolationError(
                "the independent decision-maker must differ from the procedural authority "
                "and the case handler"
            )
        return replace(
            self,
            assigned_decision_maker_reference=party_reference,
            case_version=self.case_version + 1,
        )

    def with_decision(self, decision: CaseDecision) -> ProceduralCase:
        if decision.case_id != self.case_id:
            raise ValueError("decision does not belong to this case")
        if self.decision_id is not None and self.decision_id != decision.decision_id:
            raise ProceduralCaseTransitionInvalidError(
                "this case already carries a different decision"
            )
        return replace(self, decision_id=decision.decision_id, case_version=self.case_version + 1)

    def with_evidence_reference(self, reference: str) -> ProceduralCase:
        _require_text(reference, "evidence reference")
        if reference in self.evidence_references:
            return self
        return replace(
            self,
            evidence_references=(*self.evidence_references, reference),
            case_version=self.case_version + 1,
        )

    def with_completed_step(self, step_code: str, at: datetime) -> ProceduralCase:
        _require_aware(at, "at")
        known = {step.step_code for step in self.required_steps}
        if step_code not in known:
            raise ProceduralCaseTransitionInvalidError(
                f"unknown required step {step_code!r} for this case"
            )
        steps = tuple(
            replace(step, completed_at=at)
            if step.step_code == step_code and step.completed_at is None
            else step
            for step in self.required_steps
        )
        return replace(self, required_steps=steps, case_version=self.case_version + 1)


def assert_decision_maker_eligible(
    *,
    case: ProceduralCase,
    candidate_party_reference: UUID,
    appointing_party_reference: UUID,
    role_assignments: tuple[CaseRoleAssignment, ...],
    conflict_declarations: tuple[ConflictOfInterestDeclaration, ...],
) -> None:
    """Enforce invariants 9 and 10 for an independent-decision-maker
    appointment. Pure function; the application layer supplies the case's
    own role assignments and conflict declarations.

    Refuses when: the candidate appoints themselves; the appointer is a
    party to the dispute or the current case handler; the candidate holds
    any party role on this case; the candidate is the procedural
    authority or case handler; no conflict declaration exists for the
    candidate; or the candidate's declaration is in a blocking state."""
    if candidate_party_reference == appointing_party_reference:
        raise ProceduralIndependenceViolationError(
            "a party may not appoint themselves as independent decision-maker"
        )

    roles_by_party: dict[UUID, set[ProceduralRole]] = {}
    for assignment in role_assignments:
        roles_by_party.setdefault(assignment.party_reference, set()).add(assignment.role)

    appointer_roles = roles_by_party.get(appointing_party_reference, set())
    if appointer_roles & PARTY_ROLES:
        raise ProceduralIndependenceViolationError(
            "a claimant, respondent or submitter may not appoint the independent decision-maker"
        )
    if (
        ProceduralRole.CASE_HANDLER in appointer_roles
        or appointing_party_reference == case.case_handler_reference
    ):
        raise ProceduralIndependenceViolationError(
            "the case handler may not appoint the independent decision-maker"
        )

    candidate_roles = roles_by_party.get(candidate_party_reference, set())
    if candidate_roles & PARTY_ROLES:
        raise ProceduralIndependenceViolationError(
            "a party to the dispute may not become the independent decision-maker"
        )
    if candidate_party_reference in {
        case.procedural_authority_reference,
        case.case_handler_reference,
    }:
        raise ProceduralIndependenceViolationError(
            "the independent decision-maker must differ from the procedural authority "
            "and the case handler"
        )

    declarations = [
        declaration
        for declaration in conflict_declarations
        if declaration.party_reference == candidate_party_reference
        and declaration.case_id == case.case_id
    ]
    if not declarations:
        raise ConflictOfInterestUndeclaredError(
            "the candidate has filed no conflict-of-interest declaration on this case"
        )
    if any(declaration.is_blocking for declaration in declarations):
        raise ConflictOfInterestBlockingError(
            "the candidate has a declared or confirmed conflict of interest on this case"
        )


@dataclass(frozen=True, slots=True)
class DisputeParties:
    """Claimant/respondent handles for an arbitration or internal dispute.

    Both are per-case references (`mint_case_party_reference`); this
    service never learns who they are."""

    case_id: UUID
    organization_id: UUID
    claimant_reference: UUID
    respondent_reference: UUID

    def __post_init__(self) -> None:
        if self.claimant_reference == self.respondent_reference:
            raise ProceduralRoleConflictError("claimant and respondent must be distinct parties")


# ---------------------------------------------------------------------------
# 5. Deadlines
# ---------------------------------------------------------------------------


class DeadlineStatus(StrEnum):
    RUNNING = "running"
    SUSPENDED = "suspended"
    SATISFIED = "satisfied"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class DeadlineEventType(StrEnum):
    """Every way a deadline's state can change. One append-only history
    entry per occurrence (invariant 6)."""

    STARTED = "started"
    SUSPENDED = "suspended"
    RESUMED = "resumed"
    EXTENDED = "extended"
    SATISFIED = "satisfied"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


_TERMINAL_DEADLINE_STATES: frozenset[DeadlineStatus] = frozenset(
    {DeadlineStatus.SATISFIED, DeadlineStatus.EXPIRED, DeadlineStatus.CANCELLED}
)

_STATUS_AFTER_EVENT: dict[DeadlineEventType, DeadlineStatus] = {
    DeadlineEventType.STARTED: DeadlineStatus.RUNNING,
    DeadlineEventType.SUSPENDED: DeadlineStatus.SUSPENDED,
    DeadlineEventType.RESUMED: DeadlineStatus.RUNNING,
    DeadlineEventType.EXTENDED: DeadlineStatus.RUNNING,
    DeadlineEventType.SATISFIED: DeadlineStatus.SATISFIED,
    DeadlineEventType.EXPIRED: DeadlineStatus.EXPIRED,
    DeadlineEventType.ESCALATED: DeadlineStatus.ESCALATED,
    DeadlineEventType.CANCELLED: DeadlineStatus.CANCELLED,
    DeadlineEventType.SUPERSEDED: DeadlineStatus.CANCELLED,
}


@dataclass(frozen=True, slots=True)
class DeadlineDefinition:
    """A reusable deadline template owned by one organization.

    `timezone` is the IANA name the resulting due dates are computed and
    reported in - always explicit, never inherited from an ambient
    process timezone."""

    definition_id: UUID
    organization_id: UUID
    deadline_code: str
    duration_days: int
    timezone: str
    escalation_after_days: int | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _require_text(self.deadline_code, "deadline_code")
        if self.duration_days < 0:
            raise ValueError("duration_days must be non-negative")
        if self.escalation_after_days is not None and self.escalation_after_days < 0:
            raise ValueError("escalation_after_days must be non-negative")
        require_timezone(self.timezone)

    def due_at(self, started_at: datetime) -> datetime:
        """Compute the due instant for a deadline started at
        `started_at`, in this definition's own civil timezone.

        The arithmetic is done on the *local civil* clock (convert to the
        named zone, add days, re-attach the zone), so a period that spans
        a DST boundary lands on the same wall-clock time on the due date
        rather than drifting by an hour."""
        _require_aware(started_at, "started_at")
        zone = require_timezone(self.timezone)
        local_start = started_at.astimezone(zone)
        local_due = local_start + timedelta(days=self.duration_days)
        return local_due.replace(tzinfo=zone)


@dataclass(frozen=True, slots=True)
class DeadlineHistoryEntry:
    """One immutable entry in a deadline's append-only history.

    Both `due_at_before` and `due_at_after` are recorded on every entry,
    so a later suspension/extension can never obscure what the due time
    used to be (invariant 6)."""

    sequence: int
    event_type: DeadlineEventType
    occurred_at: datetime
    due_at_before: datetime | None
    due_at_after: datetime | None
    remaining_seconds: int | None
    reason_code: str
    actor_party_reference: UUID

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        _require_text(self.reason_code, "reason_code")
        if self.sequence < 1:
            raise ValueError("sequence must be a positive integer")
        for name, value in (
            ("due_at_before", self.due_at_before),
            ("due_at_after", self.due_at_after),
        ):
            if value is not None:
                _require_aware(value, name)
        if self.remaining_seconds is not None and self.remaining_seconds < 0:
            raise ValueError("remaining_seconds must be non-negative")


@dataclass(frozen=True, slots=True)
class ProceduralDeadline:
    """A live deadline instance on one case.

    `status` and `due_at` are *derived* from `history`, never stored
    independently - there is deliberately no way to set either directly,
    which is how invariant 6 (append-only history) and invariant 7 (no
    silent reset) are made structural rather than merely conventional."""

    deadline_id: UUID
    definition_id: UUID
    case_id: UUID
    organization_id: UUID
    deadline_code: str
    timezone: str
    started_at: datetime
    history: tuple[DeadlineHistoryEntry, ...]
    supersedes_deadline_id: UUID | None = None
    superseded_by_deadline_id: UUID | None = None

    def __post_init__(self) -> None:
        _require_text(self.deadline_code, "deadline_code")
        _require_aware(self.started_at, "started_at")
        require_timezone(self.timezone)
        if not self.history:
            raise DeadlineTransitionInvalidError(
                "a deadline must be created with at least its 'started' history entry"
            )
        if self.history[0].event_type is not DeadlineEventType.STARTED:
            raise DeadlineTransitionInvalidError(
                "the first deadline history entry must be 'started'"
            )
        expected = list(range(1, len(self.history) + 1))
        if [entry.sequence for entry in self.history] != expected:
            raise DeadlineTransitionInvalidError(
                "deadline history sequences must be contiguous and start at 1"
            )

    @property
    def status(self) -> DeadlineStatus:
        return _STATUS_AFTER_EVENT[self.history[-1].event_type]

    @property
    def due_at(self) -> datetime | None:
        for entry in reversed(self.history):
            if entry.due_at_after is not None:
                return entry.due_at_after
        return None

    @property
    def remaining_seconds(self) -> int | None:
        return self.history[-1].remaining_seconds

    def _append(self, entry: DeadlineHistoryEntry) -> ProceduralDeadline:
        return replace(self, history=(*self.history, entry))

    def _next_sequence(self) -> int:
        return len(self.history) + 1

    def _require_status(self, allowed: frozenset[DeadlineStatus], action: str) -> None:
        if self.status not in allowed:
            raise DeadlineTransitionInvalidError(
                f"cannot {action} a deadline in status {self.status.value}"
            )

    def _current_due_at(self) -> datetime:
        current_due = self.due_at
        if current_due is None:
            raise DeadlineTransitionInvalidError("this deadline has no due time to work from")
        return current_due

    def suspend(
        self, at: datetime, *, reason_code: str, actor_party_reference: UUID
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        self._require_status(frozenset({DeadlineStatus.RUNNING}), "suspend")
        current_due = self._current_due_at()
        remaining = max(0, int((current_due - at).total_seconds()))
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.SUSPENDED,
                occurred_at=at,
                due_at_before=current_due,
                due_at_after=None,
                remaining_seconds=remaining,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def resume(
        self, at: datetime, *, reason_code: str, actor_party_reference: UUID
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        self._require_status(frozenset({DeadlineStatus.SUSPENDED}), "resume")
        remaining = self.history[-1].remaining_seconds
        if remaining is None:
            raise DeadlineTransitionInvalidError(
                "suspended deadline carries no remaining time to resume from"
            )
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.RESUMED,
                occurred_at=at,
                due_at_before=self.due_at,
                due_at_after=at + timedelta(seconds=remaining),
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def extend(
        self,
        at: datetime,
        *,
        additional_days: int,
        reason_code: str,
        actor_party_reference: UUID,
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        if additional_days <= 0:
            raise DeadlineTransitionInvalidError("an extension must add a positive number of days")
        self._require_status(
            frozenset({DeadlineStatus.RUNNING, DeadlineStatus.ESCALATED}), "extend"
        )
        current_due = self._current_due_at()
        zone = require_timezone(self.timezone)
        local_due = current_due.astimezone(zone) + timedelta(days=additional_days)
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.EXTENDED,
                occurred_at=at,
                due_at_before=current_due,
                due_at_after=local_due.replace(tzinfo=zone),
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def satisfy(
        self, at: datetime, *, reason_code: str, actor_party_reference: UUID
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        self._require_status(
            frozenset({DeadlineStatus.RUNNING, DeadlineStatus.SUSPENDED, DeadlineStatus.ESCALATED}),
            "satisfy",
        )
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.SATISFIED,
                occurred_at=at,
                due_at_before=self.due_at,
                due_at_after=self.due_at,
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def escalate(
        self, at: datetime, *, reason_code: str, actor_party_reference: UUID
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        self._require_status(frozenset({DeadlineStatus.RUNNING}), "escalate")
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.ESCALATED,
                occurred_at=at,
                due_at_before=self.due_at,
                due_at_after=self.due_at,
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def expire(
        self, at: datetime, *, reason_code: str, actor_party_reference: UUID
    ) -> ProceduralDeadline:
        _require_aware(at, "at")
        self._require_status(
            frozenset({DeadlineStatus.RUNNING, DeadlineStatus.ESCALATED}), "expire"
        )
        current_due = self._current_due_at()
        if at < current_due:
            raise DeadlineTransitionInvalidError("a deadline cannot expire before its own due time")
        return self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.EXPIRED,
                occurred_at=at,
                due_at_before=current_due,
                due_at_after=current_due,
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )

    def supersede(
        self,
        at: datetime,
        *,
        successor_deadline_id: UUID,
        reason_code: str,
        actor_party_reference: UUID,
    ) -> ProceduralDeadline:
        """Explicitly retire this deadline in favour of
        `successor_deadline_id`.

        This is the *only* way a deadline is replaced (invariant 7): the
        replacement is recorded on both sides and the old instance keeps
        its full history rather than disappearing."""
        _require_aware(at, "at")
        if self.status in _TERMINAL_DEADLINE_STATES:
            raise DeadlineTransitionInvalidError(
                f"a {self.status.value} deadline cannot be superseded"
            )
        superseded = self._append(
            DeadlineHistoryEntry(
                sequence=self._next_sequence(),
                event_type=DeadlineEventType.SUPERSEDED,
                occurred_at=at,
                due_at_before=self.due_at,
                due_at_after=self.due_at,
                remaining_seconds=None,
                reason_code=reason_code,
                actor_party_reference=actor_party_reference,
            )
        )
        return replace(superseded, superseded_by_deadline_id=successor_deadline_id)

    def is_overdue_at(self, at: datetime) -> bool:
        _require_aware(at, "at")
        current_due = self.due_at
        if current_due is None or self.status not in {
            DeadlineStatus.RUNNING,
            DeadlineStatus.ESCALATED,
        }:
            return False
        return at >= current_due


def build_started_deadline(
    *,
    deadline_id: UUID,
    definition: DeadlineDefinition,
    case_id: UUID,
    organization_id: UUID,
    started_at: datetime,
    reason_code: str,
    actor_party_reference: UUID,
    supersedes_deadline_id: UUID | None = None,
) -> ProceduralDeadline:
    """Create a deadline instance with its mandatory first history entry,
    due time computed from `definition` in that definition's own
    timezone."""
    _require_aware(started_at, "started_at")
    if definition.organization_id != organization_id:
        raise LegalHoldScopeMismatchError(
            "deadline definition belongs to a different organization than the case"
        )
    due_at = definition.due_at(started_at)
    entry = DeadlineHistoryEntry(
        sequence=1,
        event_type=DeadlineEventType.STARTED,
        occurred_at=started_at,
        due_at_before=None,
        due_at_after=due_at,
        remaining_seconds=None,
        reason_code=reason_code,
        actor_party_reference=actor_party_reference,
    )
    return ProceduralDeadline(
        deadline_id=deadline_id,
        definition_id=definition.definition_id,
        case_id=case_id,
        organization_id=organization_id,
        deadline_code=definition.deadline_code,
        timezone=definition.timezone,
        started_at=started_at,
        history=(entry,),
        supersedes_deadline_id=supersedes_deadline_id,
    )


# ---------------------------------------------------------------------------
# 6. Data-subject and legal requests
# ---------------------------------------------------------------------------


class DataSubjectRequestType(StrEnum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"
    OTHER_LEGAL_REQUEST = "other_legal_request"


class IdentityVerificationStatus(StrEnum):
    """How far identity verification for a request has got.

    This is a *status only*. compliance-service stores no identity
    attribute, no document, no eID assertion and no verification
    evidence - only which of these four states a request is in, plus an
    opaque `identity_verification_reference` pointing at the service that
    actually performed it (invariant 11)."""

    NOT_VERIFIED = "not_verified"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"


class DataSubjectRequestStatus(StrEnum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    IN_PROGRESS = "in_progress"
    ANSWERED = "answered"
    REFUSED = "refused"
    CLOSED = "closed"


_ALLOWED_REQUEST_TRANSITIONS: frozenset[
    tuple[DataSubjectRequestStatus, DataSubjectRequestStatus]
] = frozenset(
    {
        (DataSubjectRequestStatus.RECEIVED, DataSubjectRequestStatus.CLASSIFIED),
        (DataSubjectRequestStatus.CLASSIFIED, DataSubjectRequestStatus.IN_PROGRESS),
        (DataSubjectRequestStatus.CLASSIFIED, DataSubjectRequestStatus.REFUSED),
        (DataSubjectRequestStatus.IN_PROGRESS, DataSubjectRequestStatus.ANSWERED),
        (DataSubjectRequestStatus.IN_PROGRESS, DataSubjectRequestStatus.REFUSED),
        (DataSubjectRequestStatus.ANSWERED, DataSubjectRequestStatus.CLOSED),
        (DataSubjectRequestStatus.REFUSED, DataSubjectRequestStatus.CLOSED),
    }
)


class ResponseDecision(StrEnum):
    GRANTED = "granted"
    PARTIALLY_GRANTED = "partially_granted"
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class DataSubjectRequest:
    """A data-subject or other legal request, always attached to its own
    governed `ProceduralCase` (ADR-041).

    Carries no identity data whatsoever: the requester appears as a
    per-case `requester_party_reference`, and verification is a status
    plus an opaque reference to the service that performed it."""

    request_id: UUID
    case_id: UUID
    organization_id: UUID
    request_type: DataSubjectRequestType
    status: DataSubjectRequestStatus
    requester_party_reference: UUID
    received_at: datetime
    scope_description_code: str
    identity_verification_status: IdentityVerificationStatus
    identity_verification_reference: UUID | None = None
    assigned_handler_reference: UUID | None = None
    search_result_references: tuple[str, ...] = ()
    response_decision: ResponseDecision | None = None
    limitation_reason_code: str | None = None
    completion_evidence_reference: str | None = None
    request_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.received_at, "received_at")
        _require_text(self.scope_description_code, "scope_description_code")
        if self.request_version < 1:
            raise ValueError("request_version must be a positive integer")
        needs_limitation = {ResponseDecision.REFUSED, ResponseDecision.PARTIALLY_GRANTED}
        if self.response_decision in needs_limitation and not self.limitation_reason_code:
            raise ValueError(
                "a refused or partially granted response must carry a limitation reason code"
            )

    def with_status(self, target: DataSubjectRequestStatus) -> DataSubjectRequest:
        if (self.status, target) not in _ALLOWED_REQUEST_TRANSITIONS:
            raise DataSubjectRequestTransitionInvalidError(
                f"invalid data-subject request transition {self.status.value} -> {target.value}"
            )
        return replace(self, status=target, request_version=self.request_version + 1)

    def with_identity_verification(
        self, status: IdentityVerificationStatus, *, verification_reference: UUID | None
    ) -> DataSubjectRequest:
        return replace(
            self,
            identity_verification_status=status,
            identity_verification_reference=verification_reference,
            request_version=self.request_version + 1,
        )

    def with_search_result_reference(self, reference: str) -> DataSubjectRequest:
        _require_text(reference, "search result reference")
        if reference in self.search_result_references:
            return self
        return replace(
            self,
            search_result_references=(*self.search_result_references, reference),
            request_version=self.request_version + 1,
        )

    def with_response(
        self,
        decision: ResponseDecision,
        *,
        limitation_reason_code: str | None,
        completion_evidence_reference: str | None,
    ) -> DataSubjectRequest:
        return replace(
            self,
            response_decision=decision,
            limitation_reason_code=limitation_reason_code,
            completion_evidence_reference=completion_evidence_reference,
            request_version=self.request_version + 1,
        )


# ---------------------------------------------------------------------------
# 7. Record classification and Legal Hold propagation
#     (Framework 0.8.1 AGR-13, section 11, section 13.1)
# ---------------------------------------------------------------------------


class DataClassification(StrEnum):
    """Framework 0.8.1 section 11's data classification, as applied to a
    record class.

    The classes are the Framework's own, and each one carries different
    general-search, scoped-search, export and public-release rules in that
    section's matrix. PACK-09 records the classification and the
    eligibility profile; enforcing them on a search index or an export
    pipeline is PACK-12's job (AGR-24). Recording them here is what gives
    PACK-12 something authoritative to enforce against instead of
    inferring sensitivity from context."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    AUDIT_EVIDENCE = "audit_evidence"
    PERSONAL_COMMUNICATION = "personal_communication"


class SearchExportEligibility(StrEnum):
    """What may be done with records of this class.

    Framework section 11: "search result не расширяет source
    authorization", "export является отдельным объектом", and highly
    confidential material is excluded from general search entirely. This
    enum is the declarative half of those rules."""

    GENERAL_SEARCH_AND_EXPORT = "general_search_and_export"
    SCOPED_SEARCH_GOVERNED_EXPORT = "scoped_search_governed_export"
    DEDICATED_INDEX_ONLY = "dedicated_index_only"
    NO_INDEX = "no_index"


@dataclass(frozen=True, slots=True)
class RecordClass:
    """The classification that binds a family of records to its retention
    schedule, its custodian and the authority that may dispose of it.

    Framework AGR-13 (*Critical*) records that the baseline had "нет
    classes, disposition, hold propagation, destruction proof". This is
    the classes half; `RecordClassRef` in `references.py` is how PACK-10,
    PACK-11 and PACK-12 will point at one.

    `record_owner_authority_reference` and `custodian_reference` are
    deliberately separate: the owner decides policy for the class, the
    custodian physically holds the material, and
    `disposition_authority_reference` is who may authorize destruction.
    Collapsing them would recreate the "operator certifies their own
    operation" problem Framework hard invariant 45 forbids in the finance
    domain and AGR-15 generalizes."""

    record_class_id: UUID
    organization_id: UUID
    record_class_code: str
    record_category: str
    sensitivity: RecordSensitivity
    data_classification: DataClassification
    record_owner_authority_reference: UUID
    custodian_reference: UUID
    disposition_authority_reference: UUID
    retention_policy_reference: UUID
    search_export_eligibility: SearchExportEligibility
    legal_hold_applicable: bool
    valid_from: datetime
    valid_until: datetime | None = None
    record_class_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.valid_from, "valid_from")
        if self.valid_until is not None:
            _require_aware(self.valid_until, "valid_until")
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be after valid_from")
        _require_text(self.record_class_code, "record_class_code")
        _require_text(self.record_category, "record_category")
        if self.record_class_version < 1:
            raise ValueError("record_class_version must be a positive integer")
        if self.record_owner_authority_reference == self.disposition_authority_reference:
            raise ProceduralRoleConflictError(
                "the record owner and the disposition authority must be different references: "
                "an owner authorizing destruction of its own class is self-certification"
            )


class DerivativeKind(StrEnum):
    """The kinds of governed derivative a hold must reach.

    Framework section 11: "legal hold распространяется на релевантные
    replicas / indexes / exports, но не превращает audit в вечный content
    archive". The last clause is why `AUDIT_ENTRY` is absent from this
    enum - audit records are not a derivative a hold propagates content
    into."""

    REPLICA = "replica"
    SEARCH_INDEX = "search_index"
    EXPORT_DATASET = "export_dataset"
    BACKUP_SET = "backup_set"
    CACHED_RENDITION = "cached_rendition"


class PropagationState(StrEnum):
    """Whether a hold has actually reached a known derivative.

    `UNKNOWN` and `FAILED` both fail closed on destruction. That is the
    entire point of modelling propagation at all: a hold that the primary
    store honours while a search index quietly keeps a copy is not a hold,
    and a system that cannot tell the difference must refuse to destroy
    rather than assume the best."""

    UNKNOWN = "unknown"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


#: Propagation states that permit destruction to proceed. Everything else
#: raises `LEGAL_HOLD_PROPAGATION_UNRESOLVED`.
_RESOLVED_PROPAGATION_STATES: frozenset[PropagationState] = frozenset(
    {PropagationState.CONFIRMED, PropagationState.NOT_APPLICABLE}
)


@dataclass(frozen=True, slots=True)
class HoldPropagationRecord:
    """One hold, one known governed derivative, one propagation state.

    `evidence_reference` is an opaque digest or receipt from whatever
    system confirmed the propagation - PACK-09 records that confirmation
    exists and where, never the derivative's contents."""

    propagation_id: UUID
    hold_id: UUID
    organization_id: UUID
    derivative_kind: DerivativeKind
    derivative_reference: str
    state: PropagationState
    recorded_at: datetime
    evidence_reference: str = ""
    failure_reason_code: str | None = None

    def __post_init__(self) -> None:
        _require_aware(self.recorded_at, "recorded_at")
        _require_text(self.derivative_reference, "derivative_reference")
        if self.state is PropagationState.FAILED and not self.failure_reason_code:
            raise ValueError("a failed propagation record must carry its failure reason code")
        if self.state is PropagationState.CONFIRMED and not self.evidence_reference:
            raise ValueError(
                "a confirmed propagation must reference the evidence that confirmed it"
            )

    @property
    def is_resolved(self) -> bool:
        return self.state in _RESOLVED_PROPAGATION_STATES


def assert_hold_propagation_resolved(
    propagations: tuple[HoldPropagationRecord, ...], *, hold_id: UUID
) -> None:
    """Raise `LEGAL_HOLD_PROPAGATION_UNRESOLVED` unless every known
    derivative of `hold_id` is in a resolved propagation state.

    Fail-closed by construction: an *empty* propagation set is treated as
    resolved (a hold with no known derivatives has nothing outstanding),
    but any recorded derivative in `unknown`, `pending` or `failed` blocks
    destruction of the primary record. The asymmetry is deliberate -
    PACK-09 can only reason about derivatives it has been told about, and
    it refuses on the ones it has."""
    unresolved = [
        record for record in propagations if record.hold_id == hold_id and not record.is_resolved
    ]
    if unresolved:
        raise LegalHoldPropagationUnresolvedError(
            f"legal hold {hold_id} has {len(unresolved)} unresolved derivative propagation(s): "
            + ", ".join(
                f"{record.derivative_kind.value}={record.state.value}" for record in unresolved
            )
        )

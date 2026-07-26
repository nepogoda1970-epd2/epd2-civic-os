"""Storage protocols and in-memory reference adapters for
compliance-service's owned entities (PACK-09).

Follows the same pattern PACK-02 through PACK-08 already establish (see
`services/organization-service/src/epd2_organization_service/storage.py`):
an explicit `Protocol` per aggregate plus a deliberately simple in-memory
adapter. No production persistence is introduced here - real databases,
migrations and an event bus stay assigned to PACK-13 (ADR-038).

Three storage rules are load-bearing for this pack's own invariants and
are therefore enforced *by the store*, not merely by convention:

1. **No delete method exists anywhere in this module** (invariant 4). A
   governed record cannot be removed through storage at all; the only
   way it reaches `destroyed` is the controlled disposal workflow in
   `application`, which leaves the metadata row in place with its
   evidence reference attached. `GovernedRecordStore` deliberately has
   no `delete`/`remove`/`purge` operation for a caller to reach for -
   asserted by `tests/repository/test_service_boundaries.py`.
2. **Destruction evidence is create-once**
   (`DestructionEvidenceStore.create_once` raises rather than
   overwriting), so a replayed execution can never mint a second,
   divergent evidence record.
3. **Every scoped lookup takes the caller's `organization_id`**
   (invariant 2). The `get_in_scope` methods return `None` for a record
   that exists but belongs to another organization - identical to "no
   such record" - so a foreign resource id cannot be used to probe for
   existence. The unscoped `get_unscoped` variants exist only for the
   application layer's own hold/authority resolution and are never
   reachable from a request path.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_compliance_service.casework import (
    CaseParty,
    Filing,
    Hearing,
    InterimMeasure,
    JurisdictionDetermination,
    LegalCase,
    ProceduralDecision,
    RecusalRecord,
    Remedy,
    ReplacementAssignment,
    RepresentationMandate,
)
from epd2_compliance_service.dataprotection import (
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    ProcessingActivationDecision,
)
from epd2_compliance_service.domain import (
    AppealReference,
    CaseDecision,
    CaseRoleAssignment,
    ConflictOfInterestDeclaration,
    CrossScopeAuthorityGrant,
    DataAsset,
    DataSubjectRequest,
    DeadlineDefinition,
    DestructionAuthorization,
    DestructionEvidence,
    DisputeParties,
    GovernedRecord,
    HoldPropagationRecord,
    LegalHold,
    ProceduralCase,
    ProceduralDeadline,
    ProcessingActivity,
    RecordClass,
    RetentionPolicy,
    RetentionStartEvent,
)
from epd2_compliance_service.exceptions import (
    DestructionAlreadyExecutedError,
    DuplicateLegalEffectPreventedError,
    FilingSequenceConflictError,
    NoticeEffectAlreadyEstablishedError,
    ProceduralCaseTransitionInvalidError,
    RetentionPolicyVersionConflictError,
)
from epd2_compliance_service.notices import (
    DeadlineTrigger,
    NoticeEffectDecision,
    OfficialNotice,
    ServiceAttempt,
)

# ---------------------------------------------------------------------------
# Cross-scope authority grants
# ---------------------------------------------------------------------------


class CrossScopeAuthorityGrantStore(Protocol):
    def save(self, grant: CrossScopeAuthorityGrant) -> CrossScopeAuthorityGrant: ...

    def get(self, grant_id: UUID) -> CrossScopeAuthorityGrant | None: ...


class InMemoryCrossScopeAuthorityGrantStore:
    """Explicit, per-grant authority for one organization to act inside
    another's scope.

    There is deliberately no "parent organization inherits everything"
    rule anywhere in this service: a Bund-level actor reaching a Land's
    case needs a grant issued *by that Land*, exactly like any other
    cross-organization actor (invariant 2)."""

    def __init__(self) -> None:
        self._grants: dict[UUID, CrossScopeAuthorityGrant] = {}

    def save(self, grant: CrossScopeAuthorityGrant) -> CrossScopeAuthorityGrant:
        self._grants[grant.grant_id] = grant
        return grant

    def get(self, grant_id: UUID) -> CrossScopeAuthorityGrant | None:
        return self._grants.get(grant_id)


# ---------------------------------------------------------------------------
# Retention policies
# ---------------------------------------------------------------------------


class RetentionPolicyStore(Protocol):
    def create_version(self, policy: RetentionPolicy) -> RetentionPolicy: ...

    def get_version(self, policy_id: UUID, policy_version: int) -> RetentionPolicy | None: ...

    def latest_version(self, policy_id: UUID) -> RetentionPolicy | None: ...

    def list_versions(self, policy_id: UUID) -> tuple[RetentionPolicy, ...]: ...


class InMemoryRetentionPolicyStore:
    """Append-only by `(policy_id, policy_version)`.

    A previously-registered version is never rewritten: re-registering
    the same `(policy_id, policy_version)` with different content raises
    `RetentionPolicyVersionConflictError`, and re-registering it with
    identical content is a no-op replay. This is what makes "what policy
    version was this disposal decided under" permanently answerable."""

    def __init__(self) -> None:
        self._versions: dict[tuple[UUID, int], RetentionPolicy] = {}

    def create_version(self, policy: RetentionPolicy) -> RetentionPolicy:
        key = (policy.policy_id, policy.policy_version)
        existing = self._versions.get(key)
        if existing is not None:
            if existing != policy:
                raise RetentionPolicyVersionConflictError(
                    f"retention policy {policy.policy_id} version {policy.policy_version} "
                    "is already registered with different content"
                )
            return existing
        self._versions[key] = policy
        return policy

    def get_version(self, policy_id: UUID, policy_version: int) -> RetentionPolicy | None:
        return self._versions.get((policy_id, policy_version))

    def latest_version(self, policy_id: UUID) -> RetentionPolicy | None:
        versions = self.list_versions(policy_id)
        return versions[-1] if versions else None

    def list_versions(self, policy_id: UUID) -> tuple[RetentionPolicy, ...]:
        matching = [
            policy for (stored_id, _), policy in self._versions.items() if stored_id == policy_id
        ]
        return tuple(sorted(matching, key=lambda policy: policy.policy_version))


# ---------------------------------------------------------------------------
# Governed records and retention start events
# ---------------------------------------------------------------------------


class GovernedRecordStore(Protocol):
    """Note the absence of any delete operation - see this module's own
    docstring, rule 1."""

    def save(self, record: GovernedRecord) -> GovernedRecord: ...

    def get_in_scope(self, record_id: UUID, organization_id: UUID) -> GovernedRecord | None: ...

    def get_unscoped(self, record_id: UUID) -> GovernedRecord | None: ...

    def list_for_organization(self, organization_id: UUID) -> tuple[GovernedRecord, ...]: ...


class InMemoryGovernedRecordStore:
    def __init__(self) -> None:
        self._records: dict[UUID, GovernedRecord] = {}

    def save(self, record: GovernedRecord) -> GovernedRecord:
        self._records[record.record_id] = record
        return record

    def get_in_scope(self, record_id: UUID, organization_id: UUID) -> GovernedRecord | None:
        record = self._records.get(record_id)
        if record is None or record.organization_id != organization_id:
            return None
        return record

    def get_unscoped(self, record_id: UUID) -> GovernedRecord | None:
        return self._records.get(record_id)

    def list_for_organization(self, organization_id: UUID) -> tuple[GovernedRecord, ...]:
        return tuple(
            record for record in self._records.values() if record.organization_id == organization_id
        )


class RetentionStartEventStore(Protocol):
    def append(self, event: RetentionStartEvent) -> RetentionStartEvent: ...

    def list_for_record(self, record_id: UUID) -> tuple[RetentionStartEvent, ...]: ...


class InMemoryRetentionStartEventStore:
    """Append-only. A record may legitimately accumulate several start
    events (e.g. a case is reopened and re-closed); the application layer
    takes the latest one and records which it used."""

    def __init__(self) -> None:
        self._events: list[RetentionStartEvent] = []

    def append(self, event: RetentionStartEvent) -> RetentionStartEvent:
        for existing in self._events:
            if existing.retention_start_event_id == event.retention_start_event_id:
                return existing
        self._events.append(event)
        return event

    def list_for_record(self, record_id: UUID) -> tuple[RetentionStartEvent, ...]:
        return tuple(event for event in self._events if event.record_id == record_id)


# ---------------------------------------------------------------------------
# Legal Hold
# ---------------------------------------------------------------------------


class LegalHoldStore(Protocol):
    def save(self, hold: LegalHold) -> LegalHold: ...

    def get_in_scope(self, hold_id: UUID, organization_id: UUID) -> LegalHold | None: ...

    def list_for_organization(self, organization_id: UUID) -> tuple[LegalHold, ...]: ...


class InMemoryLegalHoldStore:
    def __init__(self) -> None:
        self._holds: dict[UUID, LegalHold] = {}

    def save(self, hold: LegalHold) -> LegalHold:
        self._holds[hold.hold_id] = hold
        return hold

    def get_in_scope(self, hold_id: UUID, organization_id: UUID) -> LegalHold | None:
        hold = self._holds.get(hold_id)
        if hold is None or hold.organization_id != organization_id:
            return None
        return hold

    def list_for_organization(self, organization_id: UUID) -> tuple[LegalHold, ...]:
        return tuple(
            hold for hold in self._holds.values() if hold.organization_id == organization_id
        )


# ---------------------------------------------------------------------------
# Destruction authorization and evidence
# ---------------------------------------------------------------------------


class DestructionAuthorizationStore(Protocol):
    def save(self, authorization: DestructionAuthorization) -> DestructionAuthorization: ...

    def get(self, authorization_id: UUID) -> DestructionAuthorization | None: ...


class InMemoryDestructionAuthorizationStore:
    def __init__(self) -> None:
        self._authorizations: dict[UUID, DestructionAuthorization] = {}

    def save(self, authorization: DestructionAuthorization) -> DestructionAuthorization:
        self._authorizations[authorization.authorization_id] = authorization
        return authorization

    def get(self, authorization_id: UUID) -> DestructionAuthorization | None:
        return self._authorizations.get(authorization_id)


class DestructionEvidenceStore(Protocol):
    def create_once(self, evidence: DestructionEvidence) -> DestructionEvidence: ...

    def get_for_record(self, record_id: UUID) -> DestructionEvidence | None: ...


class InMemoryDestructionEvidenceStore:
    """Create-once storage: exactly one evidence record per governed
    record, ever.

    An identical replay returns the stored record (so a retried
    destruction command is idempotent); a *different* second attempt
    raises `DestructionAlreadyExecutedError`."""

    def __init__(self) -> None:
        self._by_record: dict[UUID, DestructionEvidence] = {}

    def create_once(self, evidence: DestructionEvidence) -> DestructionEvidence:
        existing = self._by_record.get(evidence.record_id)
        if existing is not None:
            if existing != evidence:
                raise DestructionAlreadyExecutedError(
                    f"destruction evidence already exists for record {evidence.record_id} "
                    "with different content"
                )
            return existing
        self._by_record[evidence.record_id] = evidence
        return evidence

    def get_for_record(self, record_id: UUID) -> DestructionEvidence | None:
        return self._by_record.get(record_id)


# ---------------------------------------------------------------------------
# Data catalog and processing registry
# ---------------------------------------------------------------------------


class DataAssetStore(Protocol):
    def save(self, asset: DataAsset) -> DataAsset: ...

    def get_in_scope(self, asset_id: UUID, organization_id: UUID) -> DataAsset | None: ...


class InMemoryDataAssetStore:
    def __init__(self) -> None:
        self._assets: dict[UUID, DataAsset] = {}

    def save(self, asset: DataAsset) -> DataAsset:
        self._assets[asset.asset_id] = asset
        return asset

    def get_in_scope(self, asset_id: UUID, organization_id: UUID) -> DataAsset | None:
        asset = self._assets.get(asset_id)
        if asset is None or asset.organization_id != organization_id:
            return None
        return asset


class ProcessingActivityStore(Protocol):
    def save(self, activity: ProcessingActivity) -> ProcessingActivity: ...

    def get_in_scope(
        self, activity_id: UUID, organization_id: UUID
    ) -> ProcessingActivity | None: ...

    def list_for_organization(self, organization_id: UUID) -> tuple[ProcessingActivity, ...]: ...


class InMemoryProcessingActivityStore:
    def __init__(self) -> None:
        self._activities: dict[UUID, ProcessingActivity] = {}

    def save(self, activity: ProcessingActivity) -> ProcessingActivity:
        self._activities[activity.activity_id] = activity
        return activity

    def get_in_scope(self, activity_id: UUID, organization_id: UUID) -> ProcessingActivity | None:
        activity = self._activities.get(activity_id)
        if activity is None or activity.organization_id != organization_id:
            return None
        return activity

    def list_for_organization(self, organization_id: UUID) -> tuple[ProcessingActivity, ...]:
        return tuple(
            activity
            for activity in self._activities.values()
            if activity.organization_id == organization_id
        )


# ---------------------------------------------------------------------------
# Cases, roles, conflicts, decisions, appeals
# ---------------------------------------------------------------------------


class ProceduralCaseStore(Protocol):
    def save(self, case: ProceduralCase) -> ProceduralCase: ...

    def get_in_scope(self, case_id: UUID, organization_id: UUID) -> ProceduralCase | None: ...

    def get_unscoped(self, case_id: UUID) -> ProceduralCase | None: ...


class InMemoryProceduralCaseStore:
    def __init__(self) -> None:
        self._cases: dict[UUID, ProceduralCase] = {}

    def save(self, case: ProceduralCase) -> ProceduralCase:
        self._cases[case.case_id] = case
        return case

    def get_in_scope(self, case_id: UUID, organization_id: UUID) -> ProceduralCase | None:
        case = self._cases.get(case_id)
        if case is None or case.organization_id != organization_id:
            return None
        return case

    def get_unscoped(self, case_id: UUID) -> ProceduralCase | None:
        return self._cases.get(case_id)


class CaseRoleAssignmentStore(Protocol):
    def append(self, assignment: CaseRoleAssignment) -> CaseRoleAssignment: ...

    def list_for_case(self, case_id: UUID) -> tuple[CaseRoleAssignment, ...]: ...


class InMemoryCaseRoleAssignmentStore:
    """Append-only: a role assignment is never rewritten, so who held
    which procedural role at which point stays answerable."""

    def __init__(self) -> None:
        self._assignments: list[CaseRoleAssignment] = []

    def append(self, assignment: CaseRoleAssignment) -> CaseRoleAssignment:
        for existing in self._assignments:
            if existing.assignment_id == assignment.assignment_id:
                return existing
        self._assignments.append(assignment)
        return assignment

    def list_for_case(self, case_id: UUID) -> tuple[CaseRoleAssignment, ...]:
        return tuple(
            assignment for assignment in self._assignments if assignment.case_id == case_id
        )


class ConflictDeclarationStore(Protocol):
    def save(self, declaration: ConflictOfInterestDeclaration) -> ConflictOfInterestDeclaration: ...

    def list_for_case(self, case_id: UUID) -> tuple[ConflictOfInterestDeclaration, ...]: ...


class InMemoryConflictDeclarationStore:
    def __init__(self) -> None:
        self._declarations: dict[UUID, ConflictOfInterestDeclaration] = {}

    def save(self, declaration: ConflictOfInterestDeclaration) -> ConflictOfInterestDeclaration:
        self._declarations[declaration.declaration_id] = declaration
        return declaration

    def list_for_case(self, case_id: UUID) -> tuple[ConflictOfInterestDeclaration, ...]:
        return tuple(
            declaration
            for declaration in self._declarations.values()
            if declaration.case_id == case_id
        )


class CaseDecisionStore(Protocol):
    def create_once(self, decision: CaseDecision) -> CaseDecision: ...

    def get_for_case(self, case_id: UUID) -> CaseDecision | None: ...


class InMemoryCaseDecisionStore:
    def __init__(self) -> None:
        self._by_case: dict[UUID, CaseDecision] = {}

    def create_once(self, decision: CaseDecision) -> CaseDecision:
        existing = self._by_case.get(decision.case_id)
        if existing is not None:
            if existing != decision:
                raise ProceduralCaseTransitionInvalidError(
                    f"case {decision.case_id} already carries a different decision"
                )
            return existing
        self._by_case[decision.case_id] = decision
        return decision

    def get_for_case(self, case_id: UUID) -> CaseDecision | None:
        return self._by_case.get(case_id)


class AppealReferenceStore(Protocol):
    def append(self, appeal: AppealReference) -> AppealReference: ...

    def list_for_original_case(self, case_id: UUID) -> tuple[AppealReference, ...]: ...


class InMemoryAppealReferenceStore:
    def __init__(self) -> None:
        self._appeals: list[AppealReference] = []

    def append(self, appeal: AppealReference) -> AppealReference:
        for existing in self._appeals:
            if existing.appeal_id == appeal.appeal_id:
                return existing
        self._appeals.append(appeal)
        return appeal

    def list_for_original_case(self, case_id: UUID) -> tuple[AppealReference, ...]:
        return tuple(appeal for appeal in self._appeals if appeal.original_case_id == case_id)


class DisputePartiesStore(Protocol):
    def save(self, parties: DisputeParties) -> DisputeParties: ...

    def get_for_case(self, case_id: UUID) -> DisputeParties | None: ...


class InMemoryDisputePartiesStore:
    def __init__(self) -> None:
        self._by_case: dict[UUID, DisputeParties] = {}

    def save(self, parties: DisputeParties) -> DisputeParties:
        self._by_case[parties.case_id] = parties
        return parties

    def get_for_case(self, case_id: UUID) -> DisputeParties | None:
        return self._by_case.get(case_id)


# ---------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------


class DeadlineDefinitionStore(Protocol):
    def save(self, definition: DeadlineDefinition) -> DeadlineDefinition: ...

    def get_in_scope(
        self, definition_id: UUID, organization_id: UUID
    ) -> DeadlineDefinition | None: ...


class InMemoryDeadlineDefinitionStore:
    def __init__(self) -> None:
        self._definitions: dict[UUID, DeadlineDefinition] = {}

    def save(self, definition: DeadlineDefinition) -> DeadlineDefinition:
        self._definitions[definition.definition_id] = definition
        return definition

    def get_in_scope(self, definition_id: UUID, organization_id: UUID) -> DeadlineDefinition | None:
        definition = self._definitions.get(definition_id)
        if definition is None or definition.organization_id != organization_id:
            return None
        return definition


class ProceduralDeadlineStore(Protocol):
    def save(self, deadline: ProceduralDeadline) -> ProceduralDeadline: ...

    def get_in_scope(
        self, deadline_id: UUID, organization_id: UUID
    ) -> ProceduralDeadline | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[ProceduralDeadline, ...]: ...


class InMemoryProceduralDeadlineStore:
    """Stores whole `ProceduralDeadline` values, whose own `history` is
    append-only by construction.

    `save` refuses a write that would shorten or rewrite an existing
    instance's history - a second, independent guard for invariant 6 that
    does not rely on every caller going through the domain methods."""

    def __init__(self) -> None:
        self._deadlines: dict[UUID, ProceduralDeadline] = {}

    def save(self, deadline: ProceduralDeadline) -> ProceduralDeadline:
        existing = self._deadlines.get(deadline.deadline_id)
        if existing is not None:
            previous = existing.history
            incoming = deadline.history
            if len(incoming) < len(previous) or incoming[: len(previous)] != previous:
                raise ValueError(
                    f"deadline {deadline.deadline_id} history is append-only; "
                    "a write may only add entries to the existing prefix"
                )
        self._deadlines[deadline.deadline_id] = deadline
        return deadline

    def get_in_scope(self, deadline_id: UUID, organization_id: UUID) -> ProceduralDeadline | None:
        deadline = self._deadlines.get(deadline_id)
        if deadline is None or deadline.organization_id != organization_id:
            return None
        return deadline

    def list_for_case(self, case_id: UUID) -> tuple[ProceduralDeadline, ...]:
        return tuple(
            deadline for deadline in self._deadlines.values() if deadline.case_id == case_id
        )


# ---------------------------------------------------------------------------
# Data-subject requests
# ---------------------------------------------------------------------------


class DataSubjectRequestStore(Protocol):
    def save(self, request: DataSubjectRequest) -> DataSubjectRequest: ...

    def get_in_scope(
        self, request_id: UUID, organization_id: UUID
    ) -> DataSubjectRequest | None: ...


class InMemoryDataSubjectRequestStore:
    def __init__(self) -> None:
        self._requests: dict[UUID, DataSubjectRequest] = {}

    def save(self, request: DataSubjectRequest) -> DataSubjectRequest:
        self._requests[request.request_id] = request
        return request

    def get_in_scope(self, request_id: UUID, organization_id: UUID) -> DataSubjectRequest | None:
        request = self._requests.get(request_id)
        if request is None or request.organization_id != organization_id:
            return None
        return request


# ===========================================================================
# Framework 0.8.1 additions — legal-case substrate, notices, data protection
#
# Same three rules as above, extended to the new aggregates:
#   1. no delete method anywhere;
#   2. create-once where a second write would mean a second legal effect
#      (`NoticeEffectDecisionStore.create_once`,
#      `DeadlineTriggerStore.create_once`, `FilingStore.append`);
#   3. every scoped lookup takes the caller's `organization_id` and
#      reports a foreign object as absent.
# ===========================================================================


class LegalCaseStore(Protocol):
    def save(self, case: LegalCase) -> LegalCase: ...

    def get_in_scope(self, legal_case_id: UUID, organization_id: UUID) -> LegalCase | None: ...

    def get_unscoped(self, legal_case_id: UUID) -> LegalCase | None: ...


class InMemoryLegalCaseStore:
    """Note the absence of any listing method that is not scoped to one
    organization: there is no `list_all`, so a caller cannot enumerate an
    organization's caseload, let alone the repository's."""

    def __init__(self) -> None:
        self._cases: dict[UUID, LegalCase] = {}

    def save(self, case: LegalCase) -> LegalCase:
        existing = self._cases.get(case.legal_case_id)
        if existing is not None:
            previous = existing.transition_history
            incoming = case.transition_history
            if len(incoming) < len(previous) or incoming[: len(previous)] != previous:
                raise ValueError(
                    f"legal case {case.legal_case_id} transition history is append-only"
                )
        self._cases[case.legal_case_id] = case
        return case

    def get_in_scope(self, legal_case_id: UUID, organization_id: UUID) -> LegalCase | None:
        case = self._cases.get(legal_case_id)
        if case is None or case.organization_id != organization_id:
            return None
        return case

    def get_unscoped(self, legal_case_id: UUID) -> LegalCase | None:
        return self._cases.get(legal_case_id)


class JurisdictionStore(Protocol):
    def append(self, determination: JurisdictionDetermination) -> JurisdictionDetermination: ...

    def save(self, determination: JurisdictionDetermination) -> JurisdictionDetermination: ...

    def get(self, jurisdiction_id: UUID) -> JurisdictionDetermination | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[JurisdictionDetermination, ...]: ...


class InMemoryJurisdictionStore:
    """Keeps every determination a case has ever had.

    A transfer or a challenge writes a NEW state for the determination it
    concerns and, for a transfer, a new determination for the successor -
    nothing is removed, so `list_for_case` is the preserved jurisdiction
    history Framework 13.1 requires."""

    def __init__(self) -> None:
        self._determinations: dict[UUID, JurisdictionDetermination] = {}
        self._order: list[UUID] = []

    def append(self, determination: JurisdictionDetermination) -> JurisdictionDetermination:
        if determination.jurisdiction_id in self._determinations:
            return self._determinations[determination.jurisdiction_id]
        self._determinations[determination.jurisdiction_id] = determination
        self._order.append(determination.jurisdiction_id)
        return determination

    def save(self, determination: JurisdictionDetermination) -> JurisdictionDetermination:
        if determination.jurisdiction_id not in self._determinations:
            return self.append(determination)
        self._determinations[determination.jurisdiction_id] = determination
        return determination

    def get(self, jurisdiction_id: UUID) -> JurisdictionDetermination | None:
        return self._determinations.get(jurisdiction_id)

    def list_for_case(self, case_id: UUID) -> tuple[JurisdictionDetermination, ...]:
        return tuple(
            self._determinations[key]
            for key in self._order
            if self._determinations[key].case_id == case_id
        )


class CasePartyStore(Protocol):
    def append(self, party: CaseParty) -> CaseParty: ...

    def list_for_case(self, case_id: UUID) -> tuple[CaseParty, ...]: ...


class InMemoryCasePartyStore:
    def __init__(self) -> None:
        self._parties: list[CaseParty] = []

    def append(self, party: CaseParty) -> CaseParty:
        for existing in self._parties:
            if existing.case_party_id == party.case_party_id:
                return existing
        self._parties.append(party)
        return party

    def list_for_case(self, case_id: UUID) -> tuple[CaseParty, ...]:
        return tuple(party for party in self._parties if party.case_id == case_id)


class RepresentationStore(Protocol):
    def save(self, mandate: RepresentationMandate) -> RepresentationMandate: ...

    def get(self, mandate_id: UUID) -> RepresentationMandate | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[RepresentationMandate, ...]: ...


class InMemoryRepresentationStore:
    """Revocation updates the mandate in place *by design*: the mandate is
    one object with a lifecycle, and what must survive it is the docket,
    not the mandate's former status. Prior filings reference the mandate
    id and are never touched."""

    def __init__(self) -> None:
        self._mandates: dict[UUID, RepresentationMandate] = {}
        self._order: list[UUID] = []

    def save(self, mandate: RepresentationMandate) -> RepresentationMandate:
        if mandate.mandate_id not in self._mandates:
            self._order.append(mandate.mandate_id)
        self._mandates[mandate.mandate_id] = mandate
        return mandate

    def get(self, mandate_id: UUID) -> RepresentationMandate | None:
        return self._mandates.get(mandate_id)

    def list_for_case(self, case_id: UUID) -> tuple[RepresentationMandate, ...]:
        return tuple(
            self._mandates[key] for key in self._order if self._mandates[key].case_id == case_id
        )


class FilingStore(Protocol):
    def append(self, filing: Filing) -> Filing: ...

    def update_intake(self, filing: Filing) -> Filing: ...

    def get_in_scope(self, filing_id: UUID, organization_id: UUID) -> Filing | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[Filing, ...]: ...

    def next_sequence(self, case_id: UUID) -> int: ...


class InMemoryFilingStore:
    """The docket. Append-only in the strongest sense available here:

    - `append` refuses a duplicate `docket_sequence` for a case
      (`FILING_SEQUENCE_CONFLICT`) and refuses a re-append of an existing
      filing id with different content;
    - `update_intake` permits ONLY intake-state changes and the
      supersession link - it compares every other field and refuses if
      any differs, so "correct a filing in place" is impossible even
      through the store;
    - there is no delete."""

    def __init__(self) -> None:
        self._filings: dict[UUID, Filing] = {}
        self._order: list[UUID] = []

    def append(self, filing: Filing) -> Filing:
        existing = self._filings.get(filing.filing_id)
        if existing is not None:
            if existing != filing:
                raise FilingSequenceConflictError(
                    f"filing {filing.filing_id} already exists with different content; a "
                    "correction must be a new filing that supersedes it"
                )
            return existing
        for other in self.list_for_case(filing.case_id):
            if other.docket_sequence == filing.docket_sequence:
                raise FilingSequenceConflictError(
                    f"docket sequence {filing.docket_sequence} is already used on case "
                    f"{filing.case_id}"
                )
        self._filings[filing.filing_id] = filing
        self._order.append(filing.filing_id)
        return filing

    def update_intake(self, filing: Filing) -> Filing:
        existing = self._filings.get(filing.filing_id)
        if existing is None:
            raise FilingSequenceConflictError(
                f"filing {filing.filing_id} does not exist and cannot be updated"
            )
        immutable = (
            "case_id",
            "organization_id",
            "docket_sequence",
            "filing_type",
            "filed_by_party_reference",
            "submitted_at",
            "received_at",
            "document_references",
            "evidence_references",
            "supersedes_filing_id",
        )
        for field_name in immutable:
            if getattr(existing, field_name) != getattr(filing, field_name):
                raise FilingSequenceConflictError(
                    f"filing {filing.filing_id} is immutable except for its intake state; "
                    f"{field_name} may not change"
                )
        self._filings[filing.filing_id] = filing
        return filing

    def get_in_scope(self, filing_id: UUID, organization_id: UUID) -> Filing | None:
        filing = self._filings.get(filing_id)
        if filing is None or filing.organization_id != organization_id:
            return None
        return filing

    def list_for_case(self, case_id: UUID) -> tuple[Filing, ...]:
        return tuple(
            self._filings[key] for key in self._order if self._filings[key].case_id == case_id
        )

    def next_sequence(self, case_id: UUID) -> int:
        return len(self.list_for_case(case_id)) + 1


class HearingStore(Protocol):
    def save(self, hearing: Hearing) -> Hearing: ...

    def get_in_scope(self, hearing_id: UUID, organization_id: UUID) -> Hearing | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[Hearing, ...]: ...


class InMemoryHearingStore:
    def __init__(self) -> None:
        self._hearings: dict[UUID, Hearing] = {}

    def save(self, hearing: Hearing) -> Hearing:
        existing = self._hearings.get(hearing.hearing_id)
        if existing is not None:
            previous, incoming = existing.history, hearing.history
            if len(incoming) < len(previous) or incoming[: len(previous)] != previous:
                raise ValueError(f"hearing {hearing.hearing_id} history is append-only")
        self._hearings[hearing.hearing_id] = hearing
        return hearing

    def get_in_scope(self, hearing_id: UUID, organization_id: UUID) -> Hearing | None:
        hearing = self._hearings.get(hearing_id)
        if hearing is None or hearing.organization_id != organization_id:
            return None
        return hearing

    def list_for_case(self, case_id: UUID) -> tuple[Hearing, ...]:
        return tuple(hearing for hearing in self._hearings.values() if hearing.case_id == case_id)


class InterimMeasureStore(Protocol):
    def save(self, measure: InterimMeasure) -> InterimMeasure: ...

    def get_in_scope(self, measure_id: UUID, organization_id: UUID) -> InterimMeasure | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[InterimMeasure, ...]: ...


class InMemoryInterimMeasureStore:
    def __init__(self) -> None:
        self._measures: dict[UUID, InterimMeasure] = {}

    def save(self, measure: InterimMeasure) -> InterimMeasure:
        self._measures[measure.measure_id] = measure
        return measure

    def get_in_scope(self, measure_id: UUID, organization_id: UUID) -> InterimMeasure | None:
        measure = self._measures.get(measure_id)
        if measure is None or measure.organization_id != organization_id:
            return None
        return measure

    def list_for_case(self, case_id: UUID) -> tuple[InterimMeasure, ...]:
        return tuple(measure for measure in self._measures.values() if measure.case_id == case_id)


class ProceduralDecisionStore(Protocol):
    def save(self, decision: ProceduralDecision) -> ProceduralDecision: ...

    def get_in_scope(
        self, decision_id: UUID, organization_id: UUID
    ) -> ProceduralDecision | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[ProceduralDecision, ...]: ...


class InMemoryProceduralDecisionStore:
    """A decision's operative content is immutable once issued; only its
    state history grows. `save` enforces both: the append-only prefix
    check on `state_history`, and an equality check on the operative
    fields."""

    def __init__(self) -> None:
        self._decisions: dict[UUID, ProceduralDecision] = {}

    def save(self, decision: ProceduralDecision) -> ProceduralDecision:
        existing = self._decisions.get(decision.decision_id)
        if existing is not None:
            previous, incoming = existing.state_history, decision.state_history
            if len(incoming) < len(previous) or incoming[: len(previous)] != previous:
                raise ValueError(f"decision {decision.decision_id} state history is append-only")
            for field_name in ("operative_result", "decision_type", "issued_at", "case_id"):
                if getattr(existing, field_name) != getattr(decision, field_name):
                    raise ValueError(
                        f"decision {decision.decision_id} operative content is immutable; "
                        f"{field_name} may not change"
                    )
        self._decisions[decision.decision_id] = decision
        return decision

    def get_in_scope(self, decision_id: UUID, organization_id: UUID) -> ProceduralDecision | None:
        decision = self._decisions.get(decision_id)
        if decision is None or decision.organization_id != organization_id:
            return None
        return decision

    def list_for_case(self, case_id: UUID) -> tuple[ProceduralDecision, ...]:
        return tuple(
            decision for decision in self._decisions.values() if decision.case_id == case_id
        )


class RemedyStore(Protocol):
    def save(self, remedy: Remedy) -> Remedy: ...

    def get_in_scope(self, remedy_id: UUID, organization_id: UUID) -> Remedy | None: ...

    def list_for_decision(self, decision_id: UUID) -> tuple[Remedy, ...]: ...


class InMemoryRemedyStore:
    def __init__(self) -> None:
        self._remedies: dict[UUID, Remedy] = {}

    def save(self, remedy: Remedy) -> Remedy:
        self._remedies[remedy.remedy_id] = remedy
        return remedy

    def get_in_scope(self, remedy_id: UUID, organization_id: UUID) -> Remedy | None:
        remedy = self._remedies.get(remedy_id)
        if remedy is None or remedy.organization_id != organization_id:
            return None
        return remedy

    def list_for_decision(self, decision_id: UUID) -> tuple[Remedy, ...]:
        return tuple(
            remedy for remedy in self._remedies.values() if remedy.decision_id == decision_id
        )


class RecusalStore(Protocol):
    def append(self, recusal: RecusalRecord) -> RecusalRecord: ...

    def append_replacement(self, assignment: ReplacementAssignment) -> ReplacementAssignment: ...

    def list_for_case(self, case_id: UUID) -> tuple[RecusalRecord, ...]: ...

    def list_replacements_for_case(self, case_id: UUID) -> tuple[ReplacementAssignment, ...]: ...


class InMemoryRecusalStore:
    """Append-only in both directions.

    A superseding recusal is a NEW record pointing at the one it
    supersedes; the earlier record stays, which is what Framework hard
    invariant 54 means by "conflict declarations versioned; superseding
    допустим, overwrite запрещён"."""

    def __init__(self) -> None:
        self._recusals: list[RecusalRecord] = []
        self._replacements: list[ReplacementAssignment] = []

    def append(self, recusal: RecusalRecord) -> RecusalRecord:
        for existing in self._recusals:
            if existing.recusal_id == recusal.recusal_id:
                return existing
        self._recusals.append(recusal)
        return recusal

    def append_replacement(self, assignment: ReplacementAssignment) -> ReplacementAssignment:
        for existing in self._replacements:
            if existing.assignment_id == assignment.assignment_id:
                return existing
        self._replacements.append(assignment)
        return assignment

    def list_for_case(self, case_id: UUID) -> tuple[RecusalRecord, ...]:
        return tuple(record for record in self._recusals if record.case_id == case_id)

    def list_replacements_for_case(self, case_id: UUID) -> tuple[ReplacementAssignment, ...]:
        return tuple(record for record in self._replacements if record.case_id == case_id)


# --- Notices ---------------------------------------------------------------


class OfficialNoticeStore(Protocol):
    def save(self, notice: OfficialNotice) -> OfficialNotice: ...

    def get_in_scope(self, notice_id: UUID, organization_id: UUID) -> OfficialNotice | None: ...


class InMemoryOfficialNoticeStore:
    def __init__(self) -> None:
        self._notices: dict[UUID, OfficialNotice] = {}

    def save(self, notice: OfficialNotice) -> OfficialNotice:
        self._notices[notice.notice_id] = notice
        return notice

    def get_in_scope(self, notice_id: UUID, organization_id: UUID) -> OfficialNotice | None:
        notice = self._notices.get(notice_id)
        if notice is None or notice.organization_id != organization_id:
            return None
        return notice


class ServiceAttemptStore(Protocol):
    def append(self, attempt: ServiceAttempt) -> ServiceAttempt: ...

    def save(self, attempt: ServiceAttempt) -> ServiceAttempt: ...

    def list_for_notice(self, notice_id: UUID) -> tuple[ServiceAttempt, ...]: ...


class InMemoryServiceAttemptStore:
    def __init__(self) -> None:
        self._attempts: dict[UUID, ServiceAttempt] = {}
        self._order: list[UUID] = []

    def append(self, attempt: ServiceAttempt) -> ServiceAttempt:
        if attempt.attempt_id in self._attempts:
            return self._attempts[attempt.attempt_id]
        self._attempts[attempt.attempt_id] = attempt
        self._order.append(attempt.attempt_id)
        return attempt

    def save(self, attempt: ServiceAttempt) -> ServiceAttempt:
        if attempt.attempt_id not in self._attempts:
            return self.append(attempt)
        self._attempts[attempt.attempt_id] = attempt
        return attempt

    def list_for_notice(self, notice_id: UUID) -> tuple[ServiceAttempt, ...]:
        return tuple(
            self._attempts[key] for key in self._order if self._attempts[key].notice_id == notice_id
        )


class NoticeEffectStore(Protocol):
    def create_once(self, decision: NoticeEffectDecision) -> NoticeEffectDecision: ...

    def get_for_notice(self, notice_id: UUID) -> NoticeEffectDecision | None: ...

    def get_in_scope(
        self, effect_id: UUID, organization_id: UUID
    ) -> NoticeEffectDecision | None: ...


class InMemoryNoticeEffectStore:
    """Create-once per notice.

    An identical replay returns the stored determination (so a retried
    command is idempotent); a *different* second determination for a
    notice that already took legal effect raises
    `NOTICE_EFFECT_ALREADY_ESTABLISHED`. This is where "legal effect
    создаётся ровно один раз" is enforced at the storage layer rather
    than trusted to callers."""

    def __init__(self) -> None:
        self._by_notice: dict[UUID, NoticeEffectDecision] = {}
        self._by_id: dict[UUID, NoticeEffectDecision] = {}

    def create_once(self, decision: NoticeEffectDecision) -> NoticeEffectDecision:
        existing = self._by_notice.get(decision.notice_id)
        if existing is not None:
            if existing == decision:
                return existing
            if existing.establishes_legal_effect:
                raise NoticeEffectAlreadyEstablishedError(
                    f"notice {decision.notice_id} already has a legal-effect determination"
                )
        self._by_notice[decision.notice_id] = decision
        self._by_id[decision.effect_id] = decision
        return decision

    def get_for_notice(self, notice_id: UUID) -> NoticeEffectDecision | None:
        return self._by_notice.get(notice_id)

    def get_in_scope(self, effect_id: UUID, organization_id: UUID) -> NoticeEffectDecision | None:
        decision = self._by_id.get(effect_id)
        if decision is None or decision.organization_id != organization_id:
            return None
        return decision


class DeadlineTriggerStore(Protocol):
    def create_once(self, trigger: DeadlineTrigger) -> DeadlineTrigger: ...

    def get_for_deadline(self, deadline_id: UUID) -> DeadlineTrigger | None: ...

    def list_for_case(self, case_id: UUID) -> tuple[DeadlineTrigger, ...]: ...


class InMemoryDeadlineTriggerStore:
    def __init__(self) -> None:
        self._by_deadline: dict[UUID, DeadlineTrigger] = {}
        self._order: list[UUID] = []

    def create_once(self, trigger: DeadlineTrigger) -> DeadlineTrigger:
        existing = self._by_deadline.get(trigger.deadline_id)
        if existing is not None:
            if existing != trigger:
                raise DuplicateLegalEffectPreventedError(
                    f"deadline {trigger.deadline_id} was already triggered by "
                    f"{existing.source.value}"
                )
            return existing
        self._by_deadline[trigger.deadline_id] = trigger
        self._order.append(trigger.deadline_id)
        return trigger

    def get_for_deadline(self, deadline_id: UUID) -> DeadlineTrigger | None:
        return self._by_deadline.get(deadline_id)

    def list_for_case(self, case_id: UUID) -> tuple[DeadlineTrigger, ...]:
        return tuple(
            self._by_deadline[key]
            for key in self._order
            if self._by_deadline[key].case_id == case_id
        )


# --- Records governance and data protection --------------------------------


class RecordClassStore(Protocol):
    def save(self, record_class: RecordClass) -> RecordClass: ...

    def get_in_scope(self, record_class_id: UUID, organization_id: UUID) -> RecordClass | None: ...


class InMemoryRecordClassStore:
    def __init__(self) -> None:
        self._classes: dict[UUID, RecordClass] = {}

    def save(self, record_class: RecordClass) -> RecordClass:
        self._classes[record_class.record_class_id] = record_class
        return record_class

    def get_in_scope(self, record_class_id: UUID, organization_id: UUID) -> RecordClass | None:
        record_class = self._classes.get(record_class_id)
        if record_class is None or record_class.organization_id != organization_id:
            return None
        return record_class


class HoldPropagationStore(Protocol):
    def save(self, record: HoldPropagationRecord) -> HoldPropagationRecord: ...

    def list_for_hold(self, hold_id: UUID) -> tuple[HoldPropagationRecord, ...]: ...


class InMemoryHoldPropagationStore:
    def __init__(self) -> None:
        self._records: dict[UUID, HoldPropagationRecord] = {}
        self._order: list[UUID] = []

    def save(self, record: HoldPropagationRecord) -> HoldPropagationRecord:
        if record.propagation_id not in self._records:
            self._order.append(record.propagation_id)
        self._records[record.propagation_id] = record
        return record

    def list_for_hold(self, hold_id: UUID) -> tuple[HoldPropagationRecord, ...]:
        return tuple(
            self._records[key] for key in self._order if self._records[key].hold_id == hold_id
        )


class DPIAStore(Protocol):
    def save_requirement(
        self, determination: DPIARequirementDetermination
    ) -> DPIARequirementDetermination: ...

    def get_requirement(self, activity_id: UUID) -> DPIARequirementDetermination | None: ...

    def save(self, dpia: DataProtectionImpactAssessment) -> DataProtectionImpactAssessment: ...

    def get_for_activity(self, activity_id: UUID) -> DataProtectionImpactAssessment | None: ...

    def get_in_scope(
        self, dpia_id: UUID, organization_id: UUID
    ) -> DataProtectionImpactAssessment | None: ...


class InMemoryDPIAStore:
    def __init__(self) -> None:
        self._requirements: dict[UUID, DPIARequirementDetermination] = {}
        self._by_activity: dict[UUID, DataProtectionImpactAssessment] = {}
        self._by_id: dict[UUID, DataProtectionImpactAssessment] = {}

    def save_requirement(
        self, determination: DPIARequirementDetermination
    ) -> DPIARequirementDetermination:
        self._requirements[determination.activity_id] = determination
        return determination

    def get_requirement(self, activity_id: UUID) -> DPIARequirementDetermination | None:
        return self._requirements.get(activity_id)

    def save(self, dpia: DataProtectionImpactAssessment) -> DataProtectionImpactAssessment:
        self._by_activity[dpia.activity_id] = dpia
        self._by_id[dpia.dpia_id] = dpia
        return dpia

    def get_for_activity(self, activity_id: UUID) -> DataProtectionImpactAssessment | None:
        return self._by_activity.get(activity_id)

    def get_in_scope(
        self, dpia_id: UUID, organization_id: UUID
    ) -> DataProtectionImpactAssessment | None:
        dpia = self._by_id.get(dpia_id)
        if dpia is None or dpia.organization_id != organization_id:
            return None
        return dpia


class ProcessingActivationStore(Protocol):
    def save(self, decision: ProcessingActivationDecision) -> ProcessingActivationDecision: ...

    def get_for_activity(self, activity_id: UUID) -> ProcessingActivationDecision | None: ...


class InMemoryProcessingActivationStore:
    def __init__(self) -> None:
        self._by_activity: dict[UUID, ProcessingActivationDecision] = {}

    def save(self, decision: ProcessingActivationDecision) -> ProcessingActivationDecision:
        self._by_activity[decision.activity_id] = decision
        return decision

    def get_for_activity(self, activity_id: UUID) -> ProcessingActivationDecision | None:
        return self._by_activity.get(activity_id)

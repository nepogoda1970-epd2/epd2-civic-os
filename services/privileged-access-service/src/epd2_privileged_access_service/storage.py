"""Storage ports and in-memory reference adapters (PACK-12).

Same shape PACK-02 through PACK-11 established: one explicit `Protocol`
per aggregate, plus a deliberately simple in-memory adapter. **No
production persistence is introduced here** - real databases, migrations,
outbox tables, the production event plane and a real search index stay
assigned to PACK-13.

Five storage rules are load-bearing for this pack's own invariants and
are therefore enforced *by the store*, not merely by convention:

1. **No delete method exists anywhere in this module** - not on a port,
   not on an adapter. Session evidence, query audit and export records
   are exactly the material an actor under investigation would want gone.
   The single module-level `delete_privileged_record` exists to *refuse*,
   mirroring PACK-10's and PACK-11's precedent.
2. **Sealed session evidence is append-only.** `SealedSessionStore.append`
   refuses to replace a stored session, so `P12-SES-004`'s seal cannot be
   undone through the storage layer.
3. **Scope isolation by default.** Every query that can return more than
   one record takes a required keyword-only `scope` and filters on it. A
   read with no scope is not a broader query, it is a missing
   authorization boundary.
4. **Optimistic concurrency is the application layer's job.** No version
   column is invented here.
5. **The adapters are reference implementations, not a data plane.** Not
   concurrency-safe, not durable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_audit_core.storage import AuditEventStore
from epd2_core.event_envelope import EventEnvelope
from epd2_privileged_access_service.access import (
    PrivilegedAccessGrant,
    PrivilegedAccessRequest,
    PrivilegedAccessReview,
)
from epd2_privileged_access_service.breakglass import (
    BreakGlassActivation,
    BreakGlassIndependentReview,
    NotificationOutcome,
    NotificationPort,
)
from epd2_privileged_access_service.disclosure import (
    DisclosureRiskAssessment,
    ReleaseHistory,
    ReleaseHistoryEntry,
)
from epd2_privileged_access_service.dlp import DlpAssessment
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    AuditMutationProhibitedError,
    IdempotencyConflictError,
    SessionEvidenceIncompleteError,
)
from epd2_privileged_access_service.export import (
    ExportAccessEvent,
    ExportArtifact,
    ExportDestructionAttestation,
    ExportRequest,
)
from epd2_privileged_access_service.search import (
    IndexedRecord,
    IndexPolicy,
    IndexRemovalEvidence,
    QueryDecision,
)
from epd2_privileged_access_service.sessions import (
    PrivilegedSession,
    SealedPrivilegedSession,
)

#: Audit Core's append-only event store port, named here so the PACK-12
#: application layer depends on *that* port rather than on a local
#: re-declaration. PACK-12 never defines its own audit store: the hash
#: chain, the conflict detection and the verification stay with PACK-02
#: (`OD-P12-06`), and PACK-12 holds no mutating control over it.
PrivilegedAuditEventStore = AuditEventStore


def delete_privileged_record(record: object) -> None:
    """The single delete-shaped function in this package, and it refuses.

    Session evidence, query audit and export lifecycle records are the
    material an actor under investigation would most want removed. A port
    that offered `delete` would be publishing an act the domain forbids
    and inviting an adapter to implement it (`P12-ROLE-006`)."""
    raise AuditMutationProhibitedError(
        "PACK-12 records are append-only; deletion is refused. Retention and disposal "
        "decisions belong to PACK-09 and reach this material through its own governed "
        "process, never through a storage-level delete."
    )


def _in_scope(record_scope: OrganizationalScopeRef, scope: OrganizationalScopeRef) -> bool:
    return record_scope.organization_id == scope.organization_id


# ---------------------------------------------------------------------------
# Idempotency and event sink
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    event_id: UUID
    command: str
    request_digest: str
    aggregate_id: UUID
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, context="IdempotencyRecord.recorded_at")


class CommandIdempotencyStore(Protocol):
    def get(self, event_id: UUID) -> IdempotencyRecord | None: ...

    def put(self, record: IdempotencyRecord) -> None: ...


class InMemoryCommandIdempotencyStore:
    def __init__(self) -> None:
        self._by_event: dict[UUID, IdempotencyRecord] = {}

    def get(self, event_id: UUID) -> IdempotencyRecord | None:
        return self._by_event.get(event_id)

    def put(self, record: IdempotencyRecord) -> None:
        existing = self._by_event.get(record.event_id)
        if existing is not None and existing.request_digest != record.request_digest:
            raise IdempotencyConflictError(
                f"event_id {record.event_id} was already used with different content"
            )
        self._by_event[record.event_id] = record


class EventSink(Protocol):
    def publish(self, envelope: EventEnvelope) -> None: ...

    def published(self) -> tuple[EventEnvelope, ...]: ...


class InMemoryEventSink:
    def __init__(self) -> None:
        self._events: list[EventEnvelope] = []

    def publish(self, envelope: EventEnvelope) -> None:
        self._events.append(envelope)

    def published(self) -> tuple[EventEnvelope, ...]:
        return tuple(self._events)


# ---------------------------------------------------------------------------
# Privileged access
# ---------------------------------------------------------------------------


class PrivilegedAccessRequestStore(Protocol):
    def save(self, request: PrivilegedAccessRequest) -> None: ...

    def get(self, request_id: UUID) -> PrivilegedAccessRequest | None: ...


class InMemoryPrivilegedAccessRequestStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, PrivilegedAccessRequest] = {}

    def save(self, request: PrivilegedAccessRequest) -> None:
        self._by_id[request.request_id] = request

    def get(self, request_id: UUID) -> PrivilegedAccessRequest | None:
        return self._by_id.get(request_id)


class PrivilegedGrantStore(Protocol):
    def save(self, grant: PrivilegedAccessGrant) -> None: ...

    def get(self, grant_id: UUID) -> PrivilegedAccessGrant | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[PrivilegedAccessGrant, ...]: ...

    def list_for_subject(
        self, *, scope: OrganizationalScopeRef, subject_reference: str
    ) -> tuple[PrivilegedAccessGrant, ...]: ...


class InMemoryPrivilegedGrantStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, PrivilegedAccessGrant] = {}

    def save(self, grant: PrivilegedAccessGrant) -> None:
        self._by_id[grant.grant_id] = grant

    def get(self, grant_id: UUID) -> PrivilegedAccessGrant | None:
        return self._by_id.get(grant_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[PrivilegedAccessGrant, ...]:
        return tuple(g for g in self._by_id.values() if _in_scope(g.organization_scope, scope))

    def list_for_subject(
        self, *, scope: OrganizationalScopeRef, subject_reference: str
    ) -> tuple[PrivilegedAccessGrant, ...]:
        return tuple(
            g for g in self.list_for_scope(scope=scope) if g.subject_reference == subject_reference
        )


class PrivilegedReviewStore(Protocol):
    def save(self, review: PrivilegedAccessReview) -> None: ...

    def list_for_grant(self, grant_id: UUID) -> tuple[PrivilegedAccessReview, ...]: ...


class InMemoryPrivilegedReviewStore:
    def __init__(self) -> None:
        self._by_grant: dict[UUID, list[PrivilegedAccessReview]] = {}

    def save(self, review: PrivilegedAccessReview) -> None:
        self._by_grant.setdefault(review.grant_id, []).append(review)

    def list_for_grant(self, grant_id: UUID) -> tuple[PrivilegedAccessReview, ...]:
        return tuple(self._by_grant.get(grant_id, ()))


# ---------------------------------------------------------------------------
# Break-glass
# ---------------------------------------------------------------------------


class BreakGlassStore(Protocol):
    def save(self, activation: BreakGlassActivation) -> None: ...

    def get(self, activation_id: UUID) -> BreakGlassActivation | None: ...

    def list_for_scope(
        self, *, scope: OrganizationalScopeRef
    ) -> tuple[BreakGlassActivation, ...]: ...


class InMemoryBreakGlassStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, BreakGlassActivation] = {}

    def save(self, activation: BreakGlassActivation) -> None:
        self._by_id[activation.activation_id] = activation

    def get(self, activation_id: UUID) -> BreakGlassActivation | None:
        return self._by_id.get(activation_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[BreakGlassActivation, ...]:
        return tuple(a for a in self._by_id.values() if _in_scope(a.organization_scope, scope))


class BreakGlassReviewStore(Protocol):
    def save(self, review: BreakGlassIndependentReview) -> None: ...

    def get_for_activation(self, activation_id: UUID) -> BreakGlassIndependentReview | None: ...


class InMemoryBreakGlassReviewStore:
    def __init__(self) -> None:
        self._by_activation: dict[UUID, BreakGlassIndependentReview] = {}

    def save(self, review: BreakGlassIndependentReview) -> None:
        self._by_activation[review.activation_id] = review

    def get_for_activation(self, activation_id: UUID) -> BreakGlassIndependentReview | None:
        return self._by_activation.get(activation_id)


class ReferenceNotificationAdapter:
    """A deterministic, local notification adapter.

    The real transport belongs to the later gateway and incident packs.
    This adapter records dispatch attempts so tests can exercise the
    obligation and the escalation path. **It does not deliver a
    notification anywhere**, and nothing in this package claims that it
    does."""

    def __init__(self, *, deliver: bool = True, suppressed_by: str | None = None) -> None:
        self._deliver = deliver
        self._suppressed_by = suppressed_by
        self.dispatched: list[dict[str, object]] = []

    def dispatch(
        self,
        *,
        activation_id: UUID,
        organization_scope: OrganizationalScopeRef,
        recipient_class: str,
        activator_reference: str,
    ) -> NotificationOutcome:
        self.dispatched.append(
            {
                "activation_id": str(activation_id),
                "organization_id": str(organization_scope.organization_id),
                "recipient_class": recipient_class,
            }
        )
        return NotificationOutcome(
            delivered=self._deliver,
            dispatch_reference=f"reference-dispatch:{activation_id}",
            recipient_class=recipient_class,
            failure_reason=None if self._deliver else "reference adapter configured to fail",
            suppressed_by=self._suppressed_by,
        )


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class PrivilegedSessionStore(Protocol):
    def save(self, session: PrivilegedSession) -> None: ...

    def get(self, session_id: UUID) -> PrivilegedSession | None: ...


class InMemoryPrivilegedSessionStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, PrivilegedSession] = {}

    def save(self, session: PrivilegedSession) -> None:
        self._by_id[session.session_id] = session

    def get(self, session_id: UUID) -> PrivilegedSession | None:
        return self._by_id.get(session_id)


class SealedSessionStore(Protocol):
    def append(self, session: SealedPrivilegedSession) -> None: ...

    def get(self, session_id: UUID) -> SealedPrivilegedSession | None: ...

    def head_hash(self) -> str: ...

    def list_chain(self) -> tuple[SealedPrivilegedSession, ...]: ...


class InMemorySealedSessionStore:
    """Append-only, and it means it.

    `append` refuses to replace a stored session. Sealing is the point
    where evidence becomes reviewable; a store that let a second `append`
    overwrite the first would make the seal decorative."""

    def __init__(self) -> None:
        self._chain: list[SealedPrivilegedSession] = []
        self._by_id: dict[UUID, SealedPrivilegedSession] = {}

    def append(self, session: SealedPrivilegedSession) -> None:
        existing = self._by_id.get(session.session_id)
        if existing is not None:
            raise SessionEvidenceIncompleteError(
                f"session {session.session_id} is already sealed; sealed evidence is append-only"
            )
        self._chain.append(session)
        self._by_id[session.session_id] = session

    def get(self, session_id: UUID) -> SealedPrivilegedSession | None:
        return self._by_id.get(session_id)

    def head_hash(self) -> str:
        from epd2_privileged_access_service.sessions import GENESIS_PREVIOUS_HASH

        return self._chain[-1].integrity_reference if self._chain else GENESIS_PREVIOUS_HASH

    def list_chain(self) -> tuple[SealedPrivilegedSession, ...]:
        return tuple(self._chain)

    def replace_review(self, session: SealedPrivilegedSession) -> None:
        """Attach a review outcome without breaking the seal.

        Permitted because review status lives outside the integrity hash;
        `verify()` returns the same answer before and after."""
        stored = self._by_id.get(session.session_id)
        if stored is None:
            raise SessionEvidenceIncompleteError("no sealed session with that identifier")
        if stored.integrity_reference != session.integrity_reference:
            raise AuditMutationProhibitedError("the sealed payload of a session may not be altered")
        self._by_id[session.session_id] = session
        self._chain = [session if s.session_id == session.session_id else s for s in self._chain]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class SearchIndexStore(Protocol):
    def index(self, record: IndexedRecord) -> None: ...

    def candidates(
        self, *, scope: OrganizationalScopeRef, domains: frozenset[str]
    ) -> tuple[IndexedRecord, ...]: ...

    def remove(self, record_reference: str, evidence: IndexRemovalEvidence) -> None: ...

    def removals(self) -> tuple[IndexRemovalEvidence, ...]: ...


class InMemorySearchIndexStore:
    """A deterministic reference index.

    `remove` is the one removal path, and it requires evidence: a record
    can leave the index, but never quietly (`P12-SRCH-015`). That is a
    different act from `delete_privileged_record`, which refuses - the
    index is a derived projection, and removing a projection entry is not
    destroying a governed record."""

    def __init__(self) -> None:
        self._records: dict[str, IndexedRecord] = {}
        self._removals: list[IndexRemovalEvidence] = []

    def index(self, record: IndexedRecord) -> None:
        self._records[record.record_reference] = record

    def candidates(
        self, *, scope: OrganizationalScopeRef, domains: frozenset[str]
    ) -> tuple[IndexedRecord, ...]:
        return tuple(
            r
            for r in self._records.values()
            if _in_scope(r.organization_scope, scope) and r.domain in domains
        )

    def remove(self, record_reference: str, evidence: IndexRemovalEvidence) -> None:
        self._records.pop(record_reference, None)
        self._removals.append(evidence)

    def removals(self) -> tuple[IndexRemovalEvidence, ...]:
        return tuple(self._removals)


@dataclass(frozen=True, slots=True)
class QueryAudit:
    """The typed query-audit record PACK-12 owns.

    PACK-12 owns this record and its event semantics; the audit chain it
    is appended to remains PACK-02's, and PACK-12 gains no mutating
    control over `audit-core` (`OD-P12-06`)."""

    query_id: UUID
    organization_scope: OrganizationalScopeRef
    requester_reference: str
    mode: str
    purpose: str
    query_digest: str
    authorized_count: int
    suppressed_band: str
    policy_version: str
    executed_at: datetime
    grant_reference: UUID | None = None

    def __post_init__(self) -> None:
        require_timezone(self.executed_at, context="QueryAudit.executed_at")

    def to_state_payload(self) -> dict[str, object]:
        return {
            "query_id": str(self.query_id),
            "organization_scope": self.organization_scope.to_payload(),
            "requester_reference": self.requester_reference,
            "mode": self.mode,
            "purpose": self.purpose,
            "query_digest": self.query_digest,
            "authorized_count": self.authorized_count,
            "suppressed_band": self.suppressed_band,
            "policy_version": self.policy_version,
            "executed_at": self.executed_at.isoformat(),
            "grant_reference": str(self.grant_reference) if self.grant_reference else None,
        }


class QueryAuditStore(Protocol):
    def save(self, audit: QueryAudit) -> None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[QueryAudit, ...]: ...

    def similar_digests(
        self, *, scope: OrganizationalScopeRef, requester_reference: str, digest_prefix: str
    ) -> tuple[str, ...]: ...


class InMemoryQueryAuditStore:
    def __init__(self) -> None:
        self._records: list[QueryAudit] = []

    def save(self, audit: QueryAudit) -> None:
        self._records.append(audit)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[QueryAudit, ...]:
        return tuple(a for a in self._records if _in_scope(a.organization_scope, scope))

    def similar_digests(
        self, *, scope: OrganizationalScopeRef, requester_reference: str, digest_prefix: str
    ) -> tuple[str, ...]:
        return tuple(
            a.query_digest
            for a in self.list_for_scope(scope=scope)
            if a.requester_reference == requester_reference
            and a.query_digest.startswith(digest_prefix)
        )


class IndexPolicyStore(Protocol):
    def save(self, policy: IndexPolicy) -> None: ...

    def get(self, index_name: str) -> IndexPolicy | None: ...


class InMemoryIndexPolicyStore:
    def __init__(self) -> None:
        self._by_name: dict[str, IndexPolicy] = {}

    def save(self, policy: IndexPolicy) -> None:
        self._by_name[policy.index_name] = policy

    def get(self, index_name: str) -> IndexPolicy | None:
        return self._by_name.get(index_name)


class SearchCacheStore(Protocol):
    def get(self, fingerprint: str) -> QueryDecision | None: ...

    def put(self, fingerprint: str, decision: QueryDecision) -> None: ...


class InMemorySearchCacheStore:
    """Keyed by the authorization-context fingerprint, never by the query
    alone (`P12-SRCH-009`)."""

    def __init__(self) -> None:
        self._entries: dict[str, QueryDecision] = {}

    def get(self, fingerprint: str) -> QueryDecision | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, decision: QueryDecision) -> None:
        self._entries[fingerprint] = decision


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class ExportRequestStore(Protocol):
    def save(self, request: ExportRequest) -> None: ...

    def get(self, export_id: UUID) -> ExportRequest | None: ...

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[ExportRequest, ...]: ...


class InMemoryExportRequestStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, ExportRequest] = {}

    def save(self, request: ExportRequest) -> None:
        self._by_id[request.export_id] = request

    def get(self, export_id: UUID) -> ExportRequest | None:
        return self._by_id.get(export_id)

    def list_for_scope(self, *, scope: OrganizationalScopeRef) -> tuple[ExportRequest, ...]:
        return tuple(
            r for r in self._by_id.values() if _in_scope(r.scope.organization_scope, scope)
        )


class ExportArtifactStore(Protocol):
    def save(self, artifact: ExportArtifact) -> None: ...

    def get(self, artifact_id: UUID) -> ExportArtifact | None: ...


class InMemoryExportArtifactStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, ExportArtifact] = {}

    def save(self, artifact: ExportArtifact) -> None:
        self._by_id[artifact.artifact_id] = artifact

    def get(self, artifact_id: UUID) -> ExportArtifact | None:
        return self._by_id.get(artifact_id)


class ExportAccessStore(Protocol):
    def record(self, event: ExportAccessEvent) -> None: ...

    def list_for_artifact(self, artifact_id: UUID) -> tuple[ExportAccessEvent, ...]: ...


class InMemoryExportAccessStore:
    def __init__(self) -> None:
        self._events: list[ExportAccessEvent] = []

    def record(self, event: ExportAccessEvent) -> None:
        self._events.append(event)

    def list_for_artifact(self, artifact_id: UUID) -> tuple[ExportAccessEvent, ...]:
        return tuple(e for e in self._events if e.artifact_id == artifact_id)


class DlpAssessmentStore(Protocol):
    def save(self, assessment: DlpAssessment) -> None: ...

    def get_for_export(self, export_id: UUID) -> DlpAssessment | None: ...


class InMemoryDlpAssessmentStore:
    def __init__(self) -> None:
        self._by_export: dict[UUID, DlpAssessment] = {}

    def save(self, assessment: DlpAssessment) -> None:
        self._by_export[assessment.export_id] = assessment

    def get_for_export(self, export_id: UUID) -> DlpAssessment | None:
        return self._by_export.get(export_id)


class DisclosureAssessmentStore(Protocol):
    def save(self, assessment: DisclosureRiskAssessment) -> None: ...

    def get(self, assessment_id: UUID) -> DisclosureRiskAssessment | None: ...


class InMemoryDisclosureAssessmentStore:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DisclosureRiskAssessment] = {}

    def save(self, assessment: DisclosureRiskAssessment) -> None:
        self._by_id[assessment.assessment_id] = assessment

    def get(self, assessment_id: UUID) -> DisclosureRiskAssessment | None:
        return self._by_id.get(assessment_id)


class ReleaseHistoryStore(Protocol):
    def record(self, entry: ReleaseHistoryEntry) -> None: ...

    def window(
        self, *, scope: OrganizationalScopeRef, start: datetime, end: datetime
    ) -> ReleaseHistory: ...


class InMemoryReleaseHistoryStore:
    """Bounded, scoped release history (`OD-P12-08`).

    `available` is settable so tests can exercise the fail-closed path:
    "could not read the history" must not be silently indistinguishable
    from "no prior releases"."""

    def __init__(self, *, available: bool = True) -> None:
        self._entries: list[ReleaseHistoryEntry] = []
        self.available = available

    def record(self, entry: ReleaseHistoryEntry) -> None:
        self._entries.append(entry)

    def window(
        self, *, scope: OrganizationalScopeRef, start: datetime, end: datetime
    ) -> ReleaseHistory:
        entries = tuple(
            e
            for e in self._entries
            if _in_scope(e.organization_scope, scope) and start <= e.released_at <= end
        )
        return ReleaseHistory(
            organization_scope=scope,
            window_start=start,
            window_end=end,
            entries=entries,
            available=self.available,
        )


class DestructionAttestationStore(Protocol):
    def save(self, attestation: ExportDestructionAttestation) -> None: ...

    def get_for_export(self, export_id: UUID) -> ExportDestructionAttestation | None: ...


class InMemoryDestructionAttestationStore:
    def __init__(self) -> None:
        self._by_export: dict[UUID, ExportDestructionAttestation] = {}

    def save(self, attestation: ExportDestructionAttestation) -> None:
        self._by_export[attestation.export_id] = attestation

    def get_for_export(self, export_id: UUID) -> ExportDestructionAttestation | None:
        return self._by_export.get(export_id)


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PrivilegedStores:
    """Every store one PACK-12 command layer needs, bundled.

    Constructed per caller, never shared: a shared store would let one
    caller's idempotency record silently satisfy another's replay check."""

    requests: PrivilegedAccessRequestStore
    grants: PrivilegedGrantStore
    reviews: PrivilegedReviewStore
    break_glass: BreakGlassStore
    break_glass_reviews: BreakGlassReviewStore
    sessions: PrivilegedSessionStore
    sealed_sessions: SealedSessionStore
    index: SearchIndexStore
    index_policies: IndexPolicyStore
    query_audit: QueryAuditStore
    search_cache: SearchCacheStore
    exports: ExportRequestStore
    artifacts: ExportArtifactStore
    export_access: ExportAccessStore
    dlp_assessments: DlpAssessmentStore
    disclosure_assessments: DisclosureAssessmentStore
    release_history: ReleaseHistoryStore
    attestations: DestructionAttestationStore
    idempotency: CommandIdempotencyStore
    audit: PrivilegedAuditEventStore
    sink: EventSink
    notifications: NotificationPort

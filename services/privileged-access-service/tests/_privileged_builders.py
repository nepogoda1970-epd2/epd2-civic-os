"""Deterministic builders and test doubles for the Privileged Access
Service suite.

Everything here is deterministic and injected. There is no shared
mutable module state and no test reads the system clock: `FixedClock` is
the only source of time, so a test that depends on an interval says so by
advancing it rather than by sleeping (`P12-TEST-002`).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_privileged_access_service.breakglass import NotificationPort
from epd2_privileged_access_service.domain import (
    AuthorityReference,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RequestContext,
)
from epd2_privileged_access_service.storage import (
    InMemoryBreakGlassReviewStore,
    InMemoryBreakGlassStore,
    InMemoryCommandIdempotencyStore,
    InMemoryDestructionAttestationStore,
    InMemoryDisclosureAssessmentStore,
    InMemoryDlpAssessmentStore,
    InMemoryEventSink,
    InMemoryExportAccessStore,
    InMemoryExportArtifactStore,
    InMemoryExportRequestStore,
    InMemoryIndexPolicyStore,
    InMemoryPrivilegedAccessRequestStore,
    InMemoryPrivilegedGrantStore,
    InMemoryPrivilegedReviewStore,
    InMemoryPrivilegedSessionStore,
    InMemoryQueryAuditStore,
    InMemoryReleaseHistoryStore,
    InMemorySealedSessionStore,
    InMemorySearchCacheStore,
    InMemorySearchIndexStore,
    PrivilegedStores,
    ReferenceNotificationAdapter,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


class FixedClock:
    """A clock a test moves on purpose."""

    def __init__(self, at: datetime = T0) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advance(self, delta: timedelta) -> None:
        self._at = self._at + delta

    def set(self, at: datetime) -> None:
        self._at = at


class StubAuthorizationPort:
    """A test double for PACK-08's authority resolution.

    `resolve_active_authority` answers from an explicit allow-list of
    authority ids, so a test can express "this assignment is no longer
    active" without reaching into another package."""

    def __init__(
        self,
        *,
        held: dict[str, frozenset[str]] | None = None,
        inactive: frozenset[UUID] = frozenset(),
    ) -> None:
        self._held = dict(held or {})
        self._inactive = inactive

    def resolve_active_authority(
        self,
        authority: AuthorityReference,
        scope: OrganizationalScopeRef,
        at: datetime,
    ) -> bool:
        return authority.authority_id not in self._inactive

    def held_roles(self, actor_reference: str, scope: OrganizationalScopeRef) -> frozenset[str]:
        return self._held.get(actor_reference, frozenset())

    def grant_role(self, actor_reference: str, *roles: str) -> None:
        self._held[actor_reference] = frozenset(roles)


class StubSourceAuthorizationPort:
    """Result-time re-resolution of source authorization
    (`P12-SRCH-005`)."""

    def __init__(
        self,
        *,
        openable: frozenset[str] | None = None,
        retrievable: frozenset[str] | None = None,
    ) -> None:
        self._openable = openable
        self._retrievable = retrievable

    def may_open(
        self,
        *,
        requester_reference: str,
        record_reference: str,
        domain: str,
        scope: OrganizationalScopeRef,
        at: datetime,
    ) -> bool:
        return self._openable is None or record_reference in self._openable

    def is_retrievable(self, *, record_reference: str, at: datetime) -> bool:
        return self._retrievable is None or record_reference in self._retrievable


def authority(
    role_code: str,
    scope: OrganizationalScopeRef,
    actor_reference: str = "",
) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(),
        role_code=role_code,
        scope=scope,
        actor_reference=actor_reference,
    )


def context(
    role_code: str,
    scope: OrganizationalScopeRef,
    actor_reference: str = "",
    *,
    event_id: UUID | None = None,
    purpose: Purpose | None = None,
) -> RequestContext:
    return RequestContext(
        scope=scope,
        authorities=(authority(role_code, scope, actor_reference),),
        event_id=event_id or uuid4(),
        declared_purpose=purpose,
    )


def purpose_binding(
    purpose: Purpose = Purpose.OPERATIONS, basis: str | None = None
) -> PurposeBinding:
    return PurposeBinding(
        purpose=purpose,
        justification_reference="justification:ticket-1",
        basis_reference=basis,
    )


def reason(code: str = "PRIVILEGE_ACCESS_REQUEST_RECORDED") -> ReasonCoded:
    return ReasonCoded(reason_code=code, authority_reference="authority:office-1")


def build_stores(*, notifications: NotificationPort | None = None) -> PrivilegedStores:
    """A complete, isolated store bundle.

    Constructed per test, never shared: a shared bundle would let one
    test's idempotency record satisfy another's replay check, and the
    resulting green run would mean nothing.

    `notifications` is injectable so a test can express a failing or
    suppressed out-of-band channel without reaching into a frozen
    bundle."""
    return PrivilegedStores(
        requests=InMemoryPrivilegedAccessRequestStore(),
        grants=InMemoryPrivilegedGrantStore(),
        reviews=InMemoryPrivilegedReviewStore(),
        break_glass=InMemoryBreakGlassStore(),
        break_glass_reviews=InMemoryBreakGlassReviewStore(),
        sessions=InMemoryPrivilegedSessionStore(),
        sealed_sessions=InMemorySealedSessionStore(),
        index=InMemorySearchIndexStore(),
        index_policies=InMemoryIndexPolicyStore(),
        query_audit=InMemoryQueryAuditStore(),
        search_cache=InMemorySearchCacheStore(),
        exports=InMemoryExportRequestStore(),
        artifacts=InMemoryExportArtifactStore(),
        export_access=InMemoryExportAccessStore(),
        dlp_assessments=InMemoryDlpAssessmentStore(),
        disclosure_assessments=InMemoryDisclosureAssessmentStore(),
        release_history=InMemoryReleaseHistoryStore(),
        attestations=InMemoryDestructionAttestationStore(),
        idempotency=InMemoryCommandIdempotencyStore(),
        audit=InMemoryAuditEventStore(),
        sink=InMemoryEventSink(),
        notifications=notifications or ReferenceNotificationAdapter(),
    )

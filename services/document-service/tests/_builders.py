"""Shared, deterministic test builders for `document-service`.

Every builder here produces a *valid* object by default and takes keyword
overrides for the one field a given test wants to break. That shape is
deliberate: a test that constructs twenty fields inline hides which of
them it is actually about, and a test that breaks one field by overriding
it says exactly what it is testing.

Nothing here is a fixture. `pytest` fixtures would tie these builders to
one runner and would make them unusable from the property-style loops
several tests use.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_document_service.application import DocumentStores
from epd2_document_service.authorization import DocumentRole
from epd2_document_service.documents import GovernedDocument, default_review_requirement
from epd2_document_service.domain import (
    AccessProfile,
    AuthorityReference,
    ConflictDeclaration,
    ContentDescriptor,
    DocumentKind,
    OrganizationalScopeRef,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    RequestContext,
    RetentionBinding,
    SensitivityClass,
    content_digest_of,
)
from epd2_document_service.storage import (
    InMemoryAdmissibilityDeterminationStore,
    InMemoryApprovalRecordStore,
    InMemoryCommandIdempotencyStore,
    InMemoryContentStore,
    InMemoryDocumentVersionStore,
    InMemoryEventSink,
    InMemoryEvidenceBundleStore,
    InMemoryEvidenceRecordStore,
    InMemoryGovernedDocumentStore,
    InMemoryPublicationAuthorizationStore,
    InMemoryPublicationRenditionStore,
    InMemoryReviewRecordStore,
    InMemoryRevocationStore,
    InMemorySignatureDeterminationStore,
    InMemorySupersessionStore,
)
from epd2_document_service.versions import (
    GENESIS_PREVIOUS_HASH,
    DocumentVersion,
    seal_version,
)

#: A fixed instant every test builds from, so no test depends on real
#: elapsed time and every hash in the suite is reproducible.
T0 = datetime(2026, 7, 1, 9, 0, tzinfo=UTC)


def at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def clock_at(minutes: int) -> FixedClock:
    return FixedClock(at(minutes))


def scope(organization_id: UUID | None = None) -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=organization_id or uuid4())


class FakeAuthorizationPort:
    """A test double for PACK-08.

    Two behaviours a real port has and a naive double would not:

    - `resolve_active_authority` returns `False` for an authority whose
      scope differs from the presented one, so scope isolation is
      genuinely exercised rather than assumed;
    - `held_roles` returns exactly what was granted, so a test can grant
      an *incompatible* pair and see the act-time matrix re-check fire.

    `deny_all` exists so a test can simulate a revoked assignment without
    reconstructing the whole authority object."""

    def __init__(self) -> None:
        self._roles: dict[tuple[str, UUID], tuple[DocumentRole, ...]] = {}
        self.deny_all = False

    def grant(
        self, actor_reference: str, organization_scope: OrganizationalScopeRef, *roles: DocumentRole
    ) -> None:
        self._roles[(actor_reference, organization_scope.organization_id)] = tuple(roles)

    def resolve_active_authority(
        self, authority: AuthorityReference, presented_scope: OrganizationalScopeRef
    ) -> bool:
        if self.deny_all:
            return False
        return authority.scope.organization_id == presented_scope.organization_id

    def held_roles(
        self, actor_reference: str, presented_scope: OrganizationalScopeRef
    ) -> tuple[DocumentRole, ...]:
        return self._roles.get((actor_reference, presented_scope.organization_id), ())


def authority(
    role: DocumentRole,
    organization_scope: OrganizationalScopeRef,
    port: FakeAuthorizationPort,
    *,
    actor_reference: str | None = None,
    also_holds: tuple[DocumentRole, ...] = (),
) -> AuthorityReference:
    """Mint an authority and register the roles its actor holds.

    `also_holds` lets a test grant a second, possibly incompatible role to
    the same actor - which is the only way to exercise the act-time
    incompatibility re-check, since the presented authority itself names
    only one role."""
    actor = actor_reference or f"actor-{role.value}-{uuid4().hex[:8]}"
    port.grant(actor, organization_scope, role, *also_holds)
    return AuthorityReference(
        authority_id=uuid4(),
        role_code=role.value,
        scope=organization_scope,
        actor_reference=actor,
    )


def no_conflict(declared_by: str = "actor") -> ConflictDeclaration:
    return ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by=declared_by)


def context(
    presented_authority: AuthorityReference,
    *,
    organization_scope: OrganizationalScopeRef | None = None,
    conflict: ConflictDeclaration | None = None,
    event_id: UUID | None = None,
    access_profile: AccessProfile | None = None,
    correlation_id: str | None = None,
) -> RequestContext:
    return RequestContext(
        scope=organization_scope or presented_authority.scope,
        authorities=(presented_authority,),
        conflict=conflict or no_conflict(presented_authority.actor_reference),
        event_id=event_id or uuid4(),
        access_profile=access_profile,
        correlation_id=correlation_id,
    )


def reason(code: str = "DOCUMENT_VERSION_RECORDED", reference: str = "authority-1") -> ReasonCoded:
    return ReasonCoded(reason_code=code, authority_reference=reference)


def provenance(**overrides: Any) -> Provenance:
    base: dict[str, Any] = {
        "kind": ProvenanceKind.CAPTURED_FROM_PROCEEDING,
        "captured_at": T0,
        "recorded_at": T0,
        "source_system_reference": "assembly-2026-07-01",
    }
    base.update(overrides)
    return Provenance(**base)


def retention_binding(**overrides: Any) -> RetentionBinding:
    base: dict[str, Any] = {
        "record_class_reference": "pack-09:record-class:minutes",
        "retention_policy_reference": "pack-09:retention-policy:minutes",
        "retention_policy_version": 1,
        "bound_at": T0,
    }
    base.update(overrides)
    return RetentionBinding(**base)


def access_profile(
    organization_scope: OrganizationalScopeRef,
    max_sensitivity: SensitivityClass = SensitivityClass.CONFIDENTIAL,
) -> AccessProfile:
    return AccessProfile(
        max_sensitivity=max_sensitivity,
        scope=organization_scope,
        purpose_reference="governed-read",
    )


def governed_document(
    organization_scope: OrganizationalScopeRef,
    custodian: AuthorityReference,
    **overrides: Any,
) -> GovernedDocument:
    base: dict[str, Any] = {
        "document_id": uuid4(),
        "scope": organization_scope,
        "kind": DocumentKind.MEETING_MINUTES,
        "sensitivity": SensitivityClass.INTERNAL,
        "title_reference": "title-ref-1",
        "created_at": T0,
        "custodian": custodian,
        "review_requirement": default_review_requirement(
            DocumentKind.MEETING_MINUTES,
            policy_reference="review-policy/minutes",
            policy_version=1,
        ),
    }
    base.update(overrides)
    return GovernedDocument(**base)


def version(
    document: GovernedDocument,
    recorded_by: AuthorityReference,
    *,
    number: int = 1,
    previous_hash: str = GENESIS_PREVIOUS_HASH,
    content: bytes = b"document content v1",
    **overrides: Any,
) -> DocumentVersion:
    """A sealed, chain-valid version.

    Sealed by default because an unsealed version is not a thing the rest
    of the service ever sees: `application.record_version` seals on the
    single construction path, and a test that built an unsealed one would
    be testing a state the system cannot reach."""
    base: dict[str, Any] = {
        "version_id": uuid4(),
        "document_id": document.document_id,
        "scope": document.scope,
        "version_number": number,
        "kind": document.kind,
        "sensitivity": document.sensitivity,
        "title_reference": document.title_reference,
        "content": ContentDescriptor(
            digest=content_digest_of(content),
            media_type="text/plain",
            byte_length=len(content),
        ),
        "provenance": provenance(),
        "recorded_at": at(number),
        "recorded_by": recorded_by,
        "previous_version_hash": previous_hash,
        "version_hash": "0" * 64,
    }
    base.update(overrides)
    return seal_version(DocumentVersion(**base))


def chain(
    document: GovernedDocument, recorded_by: AuthorityReference, length: int
) -> tuple[DocumentVersion, ...]:
    """A valid chain of `length` sealed versions."""
    built: list[DocumentVersion] = []
    previous = GENESIS_PREVIOUS_HASH
    for number in range(1, length + 1):
        current = version(
            document,
            recorded_by,
            number=number,
            previous_hash=previous,
            content=f"document content v{number}".encode(),
        )
        built.append(current)
        previous = current.version_hash
    return tuple(built)


def tamper(target: DocumentVersion, **overrides: Any) -> DocumentVersion:
    """Alter a stored version *without* resealing it.

    The precise shape of the attack `verify_version_chain` exists to
    detect: the record changes, the stored `version_hash` does not, and
    recomputation therefore disagrees with it."""
    return replace(target, **overrides)


def stores() -> DocumentStores:
    """A fresh set of in-memory stores.

    Constructed per test, never shared. A shared store would let one
    test's idempotency record silently satisfy another test's replay
    check."""
    return DocumentStores(
        documents=InMemoryGovernedDocumentStore(),
        versions=InMemoryDocumentVersionStore(),
        content=InMemoryContentStore(),
        reviews=InMemoryReviewRecordStore(),
        approvals=InMemoryApprovalRecordStore(),
        publication_authorizations=InMemoryPublicationAuthorizationStore(),
        renditions=InMemoryPublicationRenditionStore(),
        supersessions=InMemorySupersessionStore(),
        revocations=InMemoryRevocationStore(),
        signatures=InMemorySignatureDeterminationStore(),
        admissibilities=InMemoryAdmissibilityDeterminationStore(),
        evidence=InMemoryEvidenceRecordStore(),
        bundles=InMemoryEvidenceBundleStore(),
        idempotency=InMemoryCommandIdempotencyStore(),
        audit=InMemoryAuditEventStore(),
        sink=InMemoryEventSink(),
    )


class Fixture:
    """A fully-wired document context: stores, a port, and one authority
    per role, all in one organizational scope.

    Bundled because almost every application-level test needs all of them
    and because building them separately in each test would put the
    seven-role separation-of-duties setup - the thing most likely to be
    got subtly wrong - in forty places instead of one."""

    def __init__(self) -> None:
        self.scope = scope()
        self.port = FakeAuthorizationPort()
        self.stores = stores()
        self.custodian = authority(DocumentRole.DOCUMENT_CUSTODIAN, self.scope, self.port)
        self.author = authority(DocumentRole.DOCUMENT_AUTHOR, self.scope, self.port)
        self.reviewer = authority(DocumentRole.DOCUMENT_REVIEWER, self.scope, self.port)
        self.approver = authority(DocumentRole.DOCUMENT_APPROVER, self.scope, self.port)
        self.legal_reviewer = authority(DocumentRole.LEGAL_REVIEWER, self.scope, self.port)
        self.publisher = authority(DocumentRole.PUBLICATION_OFFICER, self.scope, self.port)
        self.evidence_custodian = authority(DocumentRole.EVIDENCE_CUSTODIAN, self.scope, self.port)
        self.independent_reader = authority(DocumentRole.INDEPENDENT_READER, self.scope, self.port)

    def context(self, presented: AuthorityReference, **overrides: Any) -> RequestContext:
        overrides.setdefault("organization_scope", self.scope)
        return context(presented, **overrides)

"""Organization Service application layer (PACK-08 implementation round,
canon-0.7.0 section 19e; ADR-032 through ADR-037).

This module imports no other service's package (`epd2_core`/
`epd2_audit_core` only - the same ALWAYS_ALLOWED boundary every prior
pack's own service observes, `tests/repository/test_service_boundaries.py`).
Organization Service is the sole authoritative owner of every entity it
manages (task section 3); other services may only consume
`check_regional_scope_access`'s narrow result or a read function below -
no other service is wired to call this module in this implementation
round (out of this round's own scope; a future round may add that edge
under its own ADR)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_core.identifiers import generate_uuid
from epd2_organization_service.domain import (
    AccessMode,
    AuthorityStatus,
    CivicSpace,
    CivicSpaceStatus,
    InheritanceMode,
    Organization,
    OrganizationalAuthority,
    OrganizationalRelation,
    OrganizationalScope,
    OrganizationalUnit,
    OrganizationStatus,
    RegionalScopeAccessDecision,
    RelationCategory,
    RelationStatus,
    RelationType,
    ScopeDelegationGrant,
    ScopeType,
    assert_no_unpermitted_hierarchy_overlap,
    assert_temporary_supervision_window_valid,
    find_role_incompatibility,
    is_effective,
    would_create_hierarchy_cycle,
    would_create_supervision_cycle,
)
from epd2_organization_service.events import (
    authority_state_payload,
    build_organization_activated_event,
    build_organization_created_event,
    build_organization_dissolved_event,
    build_organization_merged_event,
    build_organization_split_event,
    build_organization_successor_declared_event,
    build_organization_suspended_event,
    build_organizational_authority_assigned_event,
    build_organizational_authority_revoked_event,
    build_organizational_relation_created_event,
    build_organizational_relation_ended_event,
    build_regional_scope_access_granted_event,
    build_regional_scope_access_revoked_event,
    organization_state_payload,
    relation_state_payload,
)
from epd2_organization_service.exceptions import (
    AuthorityAssignmentInvalidError,
    AuthorityRoleIncompatibleError,
    CrossScopeAccessDeniedError,
    OrganizationalAuthorityNotUsableError,
    OrganizationalCycleForbiddenError,
    OrganizationDualControlViolationError,
    OrganizationNotActiveError,
    OrganizationSelfAssignmentForbiddenError,
    PermissionDeniedError,
    SuccessorTransferRequiresDecisionError,
    UnknownOrganizationalAuthorityError,
    UnknownOrganizationalRelationError,
    UnknownOrganizationError,
)
from epd2_organization_service.storage import (
    CivicSpaceStore,
    OrganizationalAuthorityStore,
    OrganizationalHierarchyOverlapPolicyStore,
    OrganizationalInheritancePolicyStore,
    OrganizationalRelationStore,
    OrganizationalUnitStore,
    OrganizationStore,
    ScopeDelegationGrantStore,
)

AUDIT_POLICY_VERSION = "1.0"
_SOURCE_SERVICE = "organization-service"


def _audit(
    audit_store: AuditEventStore,
    *,
    event: EventEnvelope,
    target_type: str,
    target_id: UUID,
    action: str,
    reason_code: str,
    actor: ActorRef,
    correlation_id: UUID,
    after_state: dict[str, object],
    clock: Clock,
) -> AuditEvent:
    return append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            actor_id=actor.actor_id,
            actor_type=actor.actor_type,
            target_type=target_type,
            target_id=target_id,
            action=action,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash="",
            after_hash=compute_payload_hash(after_state),
        ),
        clock=clock,
    )


# =============================================================================
# Organization lifecycle (canon 19e.10, task section 8)
# =============================================================================


@dataclass(frozen=True, slots=True)
class OrganizationResult:
    organization: Organization
    event: EventEnvelope
    audit_event: AuditEvent


def create_organization(
    store: OrganizationStore,
    audit_store: AuditEventStore,
    *,
    organization_id: UUID,
    name: str,
    legal_operator: str,
    organization_type: str,
    organization_profile: str,
    default_policy_version: str,
    effective_from: datetime,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> OrganizationResult:
    """Canon 19e.10: a new node, status `draft` initially, requiring an
    `authorizing_decision_reference` - never activated automatically."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an organization")
    organization = Organization(
        organization_id=organization_id,
        name=name,
        legal_operator=legal_operator,
        organization_type=organization_type,
        status=OrganizationStatus.DRAFT,
        default_policy_version=default_policy_version,
        organization_profile=organization_profile,
        effective_from=effective_from,
    )
    store.save(organization)
    now = clock.now()
    event = build_organization_created_event(
        event_id=generate_uuid(),
        organization=organization,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
        decision_reference=authorizing_decision_reference,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organization",
        target_id=organization.organization_id,
        action="create",
        reason_code="ORGANIZATION_CREATED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=organization_state_payload(organization),
        clock=clock,
    )
    return OrganizationResult(organization=organization, event=event, audit_event=audit_event)


def _transition_organization(
    store: OrganizationStore,
    audit_store: AuditEventStore,
    *,
    organization_id: UUID,
    new_status: OrganizationStatus,
    dissolved_at: datetime | None,
    event_builder: Callable[..., EventEnvelope],
    action: str,
    reason_code: str,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> OrganizationResult:
    if not actor_is_authorized:
        raise PermissionDeniedError(f"actor is not authorized to {action} this organization")
    organization = store.get(organization_id)
    if organization is None:
        raise UnknownOrganizationError(f"unknown organization_id: {organization_id}")
    updated = organization.with_status(new_status, dissolved_at=dissolved_at)
    store.save(updated)
    now = clock.now()
    event = event_builder(
        event_id=generate_uuid(),
        organization=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
        decision_reference=authorizing_decision_reference,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organization",
        target_id=updated.organization_id,
        action=action,
        reason_code=reason_code,
        actor=actor,
        correlation_id=correlation_id,
        after_state=organization_state_payload(updated),
        clock=clock,
    )
    return OrganizationResult(organization=updated, event=event, audit_event=audit_event)


def activate_organization(
    store: OrganizationStore,
    audit_store: AuditEventStore,
    *,
    organization_id: UUID,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> OrganizationResult:
    """Canon 19e.10: `draft -> active`; never automatic on creation."""
    return _transition_organization(
        store,
        audit_store,
        organization_id=organization_id,
        new_status=OrganizationStatus.ACTIVE,
        dissolved_at=None,
        event_builder=build_organization_activated_event,
        action="activate",
        reason_code="ORGANIZATION_ACTIVATED",
        authorizing_decision_reference=authorizing_decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )


def suspend_organization(
    store: OrganizationStore,
    audit_store: AuditEventStore,
    *,
    organization_id: UUID,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> OrganizationResult:
    """Canon 19e.10: `active -> restricted` (this implementation's
    "suspend" workflow name maps onto canon 8.1's `restricted` status -
    reversible)."""
    return _transition_organization(
        store,
        audit_store,
        organization_id=organization_id,
        new_status=OrganizationStatus.RESTRICTED,
        dissolved_at=None,
        event_builder=build_organization_suspended_event,
        action="suspend",
        reason_code="ORGANIZATION_SUSPENDED",
        authorizing_decision_reference=authorizing_decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )


def dissolve_organization(
    store: OrganizationStore,
    audit_store: AuditEventStore,
    *,
    organization_id: UUID,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> OrganizationResult:
    """Canon 19e.10: `active`/`restricted -> archived`; `dissolved_at`
    fixed; irreversible through this workflow - a dissolved organization
    can never issue new authority (enforced by `assign_organizational_authority`
    below) and is never silently reactivated."""
    now = clock.now()
    return _transition_organization(
        store,
        audit_store,
        organization_id=organization_id,
        new_status=OrganizationStatus.ARCHIVED,
        dissolved_at=now,
        event_builder=build_organization_dissolved_event,
        action="dissolve",
        reason_code="ORGANIZATION_DISSOLVED",
        authorizing_decision_reference=authorizing_decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )


def rename_organization(
    store: OrganizationStore,
    *,
    organization_id: UUID,
    new_name: str,
    actor_is_authorized: bool,
) -> Organization:
    """Canon 19e.10: an additive, versioned name change; never touches
    `organization_id`, hierarchy relations, or authority assignments."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to rename this organization")
    organization = store.get(organization_id)
    if organization is None:
        raise UnknownOrganizationError(f"unknown organization_id: {organization_id}")
    updated = organization.with_rename(new_name)
    store.save(updated)
    return updated


@dataclass(frozen=True, slots=True)
class MergeResult:
    source_results: tuple[OrganizationResult, ...]
    relations: tuple[OrganizationalRelation, ...]


def merge_organizations(
    organization_store: OrganizationStore,
    relation_store: OrganizationalRelationStore,
    audit_store: AuditEventStore,
    *,
    source_organization_ids: Sequence[UUID],
    target_organization_id: UUID,
    authorizing_decision_reference: UUID,
    valid_from: datetime,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> MergeResult:
    """Canon 19e.10: each source node gains a `merged_into` continuity
    relation targeting the resulting node, and each source is dissolved
    in the SAME governed decision - never left ambiguously active. This
    relation alone never transfers authority (19e.10's hard invariant,
    enforced by `assign_organizational_authority`/`successor-transfer`
    checks, never by this function)."""
    if not source_organization_ids:
        raise ValueError("source_organization_ids must not be empty")
    relations: list[OrganizationalRelation] = []
    source_results: list[OrganizationResult] = []
    for source_id in source_organization_ids:
        relation = OrganizationalRelation(
            relation_id=generate_uuid(),
            relation_version=1,
            relation_type=RelationType.MERGED_INTO,
            source_organization_id=source_id,
            target_organization_id=target_organization_id,
            status=RelationStatus.ACTIVE,
            valid_from=valid_from,
            recorded_at=clock.now(),
            authorizing_decision_reference=authorizing_decision_reference,
        )
        relation_store.save(relation)
        relations.append(relation)
        result = _transition_organization(
            organization_store,
            audit_store,
            organization_id=source_id,
            new_status=OrganizationStatus.ARCHIVED,
            dissolved_at=clock.now(),
            event_builder=build_organization_merged_event,
            action="merge",
            reason_code="ORGANIZATION_MERGED",
            authorizing_decision_reference=authorizing_decision_reference,
            actor=actor,
            actor_is_authorized=actor_is_authorized,
            correlation_id=correlation_id,
            clock=clock,
        )
        source_results.append(result)
    return MergeResult(source_results=tuple(source_results), relations=tuple(relations))


@dataclass(frozen=True, slots=True)
class SplitResult:
    source_result: OrganizationResult | None
    relations: tuple[OrganizationalRelation, ...]


def split_organization(
    organization_store: OrganizationStore,
    relation_store: OrganizationalRelationStore,
    audit_store: AuditEventStore,
    *,
    source_organization_id: UUID,
    resulting_organization_ids: Sequence[UUID],
    source_continues: bool,
    authorizing_decision_reference: UUID,
    valid_from: datetime,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> SplitResult:
    """Canon 19e.10: the source node gains one or more `split_from`
    relations from the resulting nodes; whether the source continues is
    an explicit decision field (`source_continues`), never inferred."""
    if not resulting_organization_ids:
        raise ValueError("resulting_organization_ids must not be empty")
    relations: list[OrganizationalRelation] = []
    for resulting_id in resulting_organization_ids:
        relation = OrganizationalRelation(
            relation_id=generate_uuid(),
            relation_version=1,
            relation_type=RelationType.SPLIT_FROM,
            source_organization_id=resulting_id,
            target_organization_id=source_organization_id,
            status=RelationStatus.ACTIVE,
            valid_from=valid_from,
            recorded_at=clock.now(),
            authorizing_decision_reference=authorizing_decision_reference,
        )
        relation_store.save(relation)
        relations.append(relation)

    source_result: OrganizationResult | None = None
    if not source_continues:
        source_result = _transition_organization(
            organization_store,
            audit_store,
            organization_id=source_organization_id,
            new_status=OrganizationStatus.ARCHIVED,
            dissolved_at=clock.now(),
            event_builder=build_organization_split_event,
            action="split",
            reason_code="ORGANIZATION_SPLIT",
            authorizing_decision_reference=authorizing_decision_reference,
            actor=actor,
            actor_is_authorized=actor_is_authorized,
            correlation_id=correlation_id,
            clock=clock,
        )
    return SplitResult(source_result=source_result, relations=tuple(relations))


def declare_successor(
    organization_store: OrganizationStore,
    relation_store: OrganizationalRelationStore,
    audit_store: AuditEventStore,
    *,
    predecessor_organization_id: UUID,
    successor_organization_id: UUID,
    authorizing_decision_reference: UUID,
    valid_from: datetime,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> tuple[OrganizationalRelation, OrganizationResult]:
    """Canon 19e.10: `successor_of` recorded as its own explicit governed
    decision; `successor_reference` is populated at the same time as a
    read-optimization convenience, never as the sole record of the fact."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to declare a successor")
    predecessor = organization_store.get(predecessor_organization_id)
    if predecessor is None:
        raise UnknownOrganizationError(f"unknown organization_id: {predecessor_organization_id}")
    relation = OrganizationalRelation(
        relation_id=generate_uuid(),
        relation_version=1,
        relation_type=RelationType.SUCCESSOR_OF,
        source_organization_id=successor_organization_id,
        target_organization_id=predecessor_organization_id,
        status=RelationStatus.ACTIVE,
        valid_from=valid_from,
        recorded_at=clock.now(),
        authorizing_decision_reference=authorizing_decision_reference,
    )
    relation_store.save(relation)
    updated_predecessor = predecessor.with_successor_reference(successor_organization_id)
    organization_store.save(updated_predecessor)
    now = clock.now()
    event = build_organization_successor_declared_event(
        event_id=generate_uuid(),
        organization=updated_predecessor,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
        decision_reference=authorizing_decision_reference,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organization",
        target_id=updated_predecessor.organization_id,
        action="declare_successor",
        reason_code="ORGANIZATION_SUCCESSOR_DECLARED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=organization_state_payload(updated_predecessor),
        clock=clock,
    )
    return relation, OrganizationResult(
        organization=updated_predecessor, event=event, audit_event=audit_event
    )


def assert_successor_transfer_has_own_decision(
    *, reorganization_decision_reference: UUID, transfer_decision_reference: UUID | None
) -> None:
    """Canon 19e.10's hard invariant: a `merged_into`/`split_from`/
    `successor_of` relation never itself authorizes an authority/role/
    access transfer. Any actual transfer requires its OWN explicit
    decision reference, distinct from the reorganization decision
    itself (though both may be recorded in the same governed session)."""
    if transfer_decision_reference is None:
        raise SuccessorTransferRequiresDecisionError(
            "an authority/role/access transfer following a merger, split, or successor "
            "declaration requires its own explicit governed decision, distinct from the "
            "reorganization decision (canon 19e.10)"
        )


# =============================================================================
# OrganizationalUnit / CivicSpace - thin lifecycle wrappers reusing the
# same status machinery as Organization.
# =============================================================================


def create_organizational_unit(
    store: OrganizationalUnitStore,
    *,
    organizational_unit_id: UUID,
    owning_organization_id: UUID,
    unit_type: str,
    valid_from: datetime,
    actor_is_authorized: bool,
    clock: Clock,
) -> OrganizationalUnit:
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create an organizational unit")
    unit = OrganizationalUnit(
        organizational_unit_id=organizational_unit_id,
        owning_organization_id=owning_organization_id,
        unit_type=unit_type,
        status=OrganizationStatus.DRAFT,
        valid_from=valid_from,
        recorded_at=clock.now(),
    )
    store.save(unit)
    return unit


def create_civic_space(
    store: CivicSpaceStore,
    *,
    space_id: UUID,
    organization_id: UUID,
    name: str,
    space_type: str,
    visibility: str,
    participation_policy_id: UUID | None,
    actor_is_authorized: bool,
) -> CivicSpace:
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create a civic space")
    space = CivicSpace(
        space_id=space_id,
        organization_id=organization_id,
        name=name,
        space_type=space_type,
        visibility=visibility,
        participation_policy_id=participation_policy_id,
        status=CivicSpaceStatus.DRAFT,
    )
    store.save(space)
    return space


def activate_civic_space(
    store: CivicSpaceStore, *, space_id: UUID, actor_is_authorized: bool
) -> CivicSpace:
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this civic space")
    space = store.get(space_id)
    if space is None:
        raise UnknownOrganizationError(f"unknown space_id: {space_id}")
    updated = space.with_status(CivicSpaceStatus.ACTIVE)
    store.save(updated)
    return updated


# =============================================================================
# OrganizationalRelation (canon 19e.7) - cycle + overlap validation.
# =============================================================================


@dataclass(frozen=True, slots=True)
class RelationResult:
    relation: OrganizationalRelation
    event: EventEnvelope
    audit_event: AuditEvent


def create_organizational_relation(
    relation_store: OrganizationalRelationStore,
    overlap_policy_store: OrganizationalHierarchyOverlapPolicyStore,
    audit_store: AuditEventStore,
    *,
    relation_id: UUID,
    relation_type: RelationType,
    source_organization_id: UUID,
    target_organization_id: UUID,
    valid_from: datetime,
    valid_until: datetime | None = None,
    authorizing_decision_reference: UUID | None,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> RelationResult:
    """Canon 19e.7: rejects a hierarchy-category cycle unconditionally,
    a `temporary_supervision_by` cycle unconditionally, and an
    unpermitted hierarchy overlap unless an active
    `OrganizationalHierarchyOverlapPolicy` allows it for these relation
    types."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create this relation")
    if relation_type is RelationType.TEMPORARY_SUPERVISION_BY:
        assert_temporary_supervision_window_valid(valid_from, valid_until)
        existing_supervision = [
            (r.source_organization_id, r.target_organization_id)
            for r in relation_store.list_active_by_type(RelationType.TEMPORARY_SUPERVISION_BY)
        ]
        if would_create_supervision_cycle(
            existing_supervision,
            supervisor_organization_id=source_organization_id,
            supervised_organization_id=target_organization_id,
        ):
            raise OrganizationalCycleForbiddenError(
                "temporary_supervision_by may not form a cycle (canon 19e.7)"
            )

    existing_hierarchy_edges = [
        (r.source_organization_id, r.target_organization_id, r.relation_type)
        for r in relation_store.list_active()
        if r.relation_category is RelationCategory.HIERARCHY
    ]
    if would_create_hierarchy_cycle(
        existing_hierarchy_edges,
        source_organization_id=source_organization_id,
        target_organization_id=target_organization_id,
        relation_type=relation_type,
    ):
        raise OrganizationalCycleForbiddenError(
            "this relation would create a containment/subordination cycle (canon 19e.7)"
        )

    if relation_type in (RelationType.PARENT_OF, RelationType.SUBORDINATE_TO):
        policy = overlap_policy_store.resolve_for_relation_type(relation_type, at=valid_from)
        overlap_permitted = policy is not None and policy.overlap_permitted
        existing_active = [
            (
                r.source_organization_id,
                r.target_organization_id,
                r.relation_type,
                r.valid_from,
                r.valid_until,
            )
            for r in relation_store.list_active()
        ]
        assert_no_unpermitted_hierarchy_overlap(
            existing_active,
            source_organization_id=source_organization_id,
            target_organization_id=target_organization_id,
            relation_type=relation_type,
            valid_from=valid_from,
            valid_until=valid_until,
            overlap_permitted=overlap_permitted,
        )

    relation = OrganizationalRelation(
        relation_id=relation_id,
        relation_version=1,
        relation_type=relation_type,
        source_organization_id=source_organization_id,
        target_organization_id=target_organization_id,
        status=RelationStatus.ACTIVE,
        valid_from=valid_from,
        valid_until=valid_until,
        recorded_at=clock.now(),
        authorizing_decision_reference=authorizing_decision_reference,
    )
    relation_store.save(relation)
    now = clock.now()
    event = build_organizational_relation_created_event(
        event_id=generate_uuid(),
        relation=relation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organizational_relation",
        target_id=relation.relation_id,
        action="create",
        reason_code="ORGANIZATIONAL_RELATION_CREATED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=relation_state_payload(relation),
        clock=clock,
    )
    return RelationResult(relation=relation, event=event, audit_event=audit_event)


def end_organizational_relation(
    relation_store: OrganizationalRelationStore,
    audit_store: AuditEventStore,
    *,
    relation_id: UUID,
    valid_until: datetime,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> RelationResult:
    """Canon 19e.7: sets `valid_until` on the existing record - never an
    in-place edit of any other field. A territorial reassignment (a new
    relation version) is a separate `create_organizational_relation` call,
    never implied by this function."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to end this relation")
    relation = relation_store.get(relation_id)
    if relation is None:
        raise UnknownOrganizationalRelationError(f"unknown relation_id: {relation_id}")
    updated = relation.with_valid_until(valid_until)
    relation_store.save(updated)
    now = clock.now()
    event = build_organizational_relation_ended_event(
        event_id=generate_uuid(),
        relation=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organizational_relation",
        target_id=updated.relation_id,
        action="end",
        reason_code="ORGANIZATIONAL_RELATION_ENDED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=relation_state_payload(updated),
        clock=clock,
    )
    return RelationResult(relation=updated, event=event, audit_event=audit_event)


def reassign_territorial_parent(
    relation_store: OrganizationalRelationStore,
    overlap_policy_store: OrganizationalHierarchyOverlapPolicyStore,
    audit_store: AuditEventStore,
    *,
    old_relation_id: UUID,
    child_organization_id: UUID,
    new_parent_organization_id: UUID,
    relation_type: RelationType,
    reassignment_at: datetime,
    authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> tuple[RelationResult, RelationResult]:
    """Canon 19e.10: territorial reassignment - the old hierarchy relation
    gets `valid_until`, and a new relation version is created with its own
    `valid_from`, never an in-place edit of the existing record."""
    ended = end_organizational_relation(
        relation_store,
        audit_store,
        relation_id=old_relation_id,
        valid_until=reassignment_at,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )
    if relation_type is RelationType.PARENT_OF:
        source_id, target_id = new_parent_organization_id, child_organization_id
    else:
        source_id, target_id = child_organization_id, new_parent_organization_id
    created = create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=generate_uuid(),
        relation_type=relation_type,
        source_organization_id=source_id,
        target_organization_id=target_id,
        valid_from=reassignment_at,
        authorizing_decision_reference=authorizing_decision_reference,
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )
    return ended, created


def recompute_parent_reference(
    relation_store: OrganizationalRelationStore, *, organization_id: UUID, at: datetime
) -> UUID | None:
    """Canon 19e.4: `parent_reference` is never authoritative - it is
    always recomputed from the current active hierarchy-category
    `OrganizationalRelation` set. Returns `None` where there is zero or
    more than one concurrent parent (multiple concurrent parents are
    permitted per 19e.7/19e.8 but `parent_reference` may not arbitrarily
    pick one - it is omitted entirely in that case, per 19e.3's own
    stated option)."""
    parents: set[UUID] = set()
    for relation in relation_store.list_active_for_organization(organization_id):
        if relation.relation_category is not RelationCategory.HIERARCHY:
            continue
        if not is_effective(relation.valid_from, relation.valid_until, at=at):
            continue
        if relation.relation_type is RelationType.PARENT_OF and relation.target_organization_id == (
            organization_id
        ):
            parents.add(relation.source_organization_id)
        elif (
            relation.relation_type is RelationType.SUBORDINATE_TO
            and relation.source_organization_id == organization_id
        ):
            parents.add(relation.target_organization_id)
    if len(parents) == 1:
        return next(iter(parents))
    return None


# =============================================================================
# OrganizationalAuthority (canon 19e.15/19e.16/19e.17)
# =============================================================================


@dataclass(frozen=True, slots=True)
class AuthorityResult:
    authority: OrganizationalAuthority
    event: EventEnvelope
    audit_event: AuditEvent


def assign_organizational_authority(
    organization_store: OrganizationStore,
    authority_store: OrganizationalAuthorityStore,
    audit_store: AuditEventStore,
    *,
    authority_id: UUID,
    role_code: str,
    scope: OrganizationalScope,
    appointing_authority_reference: UUID,
    assigned_subject_reference: UUID,
    valid_from: datetime,
    policy_version: str,
    decision_reference: UUID,
    grants_procedural_authority: bool,
    grants_data_access: bool,
    valid_until: datetime | None = None,
    require_dual_control: bool = False,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> AuthorityResult:
    """Canon 19e.15/19e.17: self-assignment is structurally forbidden
    (`Organization.__post_init__`... actually `OrganizationalAuthority.
    __post_init__` - appointing actor may never equal the assigned
    subject); the assignment must not violate the section 19e.16 minimum
    incompatibility baseline; an organization scope target must be
    `active` (canon 24 `ORGANIZATION_NOT_ACTIVE`); `require_dual_control`
    starts the assignment as `proposed` rather than `active` (19e.17 rule
    6 - a separate `activate_organizational_authority` call is then
    required, by a DIFFERENT actor, to bring it live)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to assign organizational authority")
    if appointing_authority_reference == assigned_subject_reference:
        raise OrganizationSelfAssignmentForbiddenError(
            "self-assignment of institutional authority is forbidden (canon 19e.16 rule 6)"
        )

    if scope.scope_type is ScopeType.ORGANIZATION_SCOPE:
        organization = organization_store.get(UUID(scope.scope_reference))
        if organization is None:
            raise UnknownOrganizationError(f"unknown organization_id: {scope.scope_reference}")
        if organization.status is not OrganizationStatus.ACTIVE:
            raise OrganizationNotActiveError(
                f"organization {organization.organization_id} is not active "
                f"(status={organization.status.value!r})"
            )
        if valid_from < organization.effective_from:
            raise AuthorityAssignmentInvalidError(
                "authority cannot begin before organization existence (canon 19e.17 rule 1)"
            )
        if organization.dissolved_at is not None and (
            valid_until is None or valid_until > organization.dissolved_at
        ):
            raise AuthorityAssignmentInvalidError(
                "authority cannot remain active after organization dissolution unless "
                "explicitly migrated (canon 19e.17 rule 2)"
            )

    existing_active = authority_store.list_active_for_subject_and_scope(
        assigned_subject_reference=assigned_subject_reference, scope=scope, at=valid_from
    )
    conflicting = find_role_incompatibility((a.role_code for a in existing_active), role_code)
    if conflicting is not None:
        raise AuthorityRoleIncompatibleError(
            f"role_code {role_code!r} is incompatible with already-held role_code "
            f"{conflicting!r} for this subject and scope (canon 19e.16)"
        )

    status = AuthorityStatus.PROPOSED if require_dual_control else AuthorityStatus.ACTIVE
    authority = OrganizationalAuthority(
        authority_id=authority_id,
        authority_version=1,
        role_code=role_code,
        scope=scope,
        appointing_authority_reference=appointing_authority_reference,
        assigned_subject_reference=assigned_subject_reference,
        valid_from=valid_from,
        valid_until=valid_until,
        status=status,
        policy_version=policy_version,
        decision_reference=decision_reference,
        grants_procedural_authority=grants_procedural_authority,
        grants_data_access=grants_data_access,
    )
    authority_store.save(authority)
    now = clock.now()
    event = build_organizational_authority_assigned_event(
        event_id=generate_uuid(),
        authority=authority,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organizational_authority",
        target_id=authority.authority_id,
        action="assign",
        reason_code="ORGANIZATIONAL_AUTHORITY_ASSIGNED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=authority_state_payload(authority),
        clock=clock,
    )
    return AuthorityResult(authority=authority, event=event, audit_event=audit_event)


def activate_organizational_authority(
    authority_store: OrganizationalAuthorityStore,
    *,
    authority_id: UUID,
    activating_actor_reference: UUID,
    actor_is_authorized: bool,
) -> OrganizationalAuthority:
    """Canon 19e.17 rule 6: proposal and activation are separated where
    dual control is required. `activating_actor_reference` must differ
    from `appointing_authority_reference` (19e.16 rule 8: one person
    cannot satisfy both sides of a dual-control action)."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to activate this authority")
    authority = authority_store.get(authority_id)
    if authority is None:
        raise UnknownOrganizationalAuthorityError(f"unknown authority_id: {authority_id}")
    if activating_actor_reference == authority.appointing_authority_reference:
        raise OrganizationDualControlViolationError(
            "the activating actor must differ from the proposing appointing_authority_reference "
            "(canon 19e.16 rule 8 / 19e.17 rule 5)"
        )
    updated = authority.with_status(AuthorityStatus.ACTIVE)
    authority_store.save(updated)
    return updated


def revoke_organizational_authority(
    authority_store: OrganizationalAuthorityStore,
    audit_store: AuditEventStore,
    *,
    authority_id: UUID,
    revocation_reason_reference: str,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> AuthorityResult:
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to revoke this authority")
    authority = authority_store.get(authority_id)
    if authority is None:
        raise UnknownOrganizationalAuthorityError(f"unknown authority_id: {authority_id}")
    updated = authority.with_status(
        AuthorityStatus.REVOKED, revocation_reason_reference=revocation_reason_reference
    )
    authority_store.save(updated)
    now = clock.now()
    event = build_organizational_authority_revoked_event(
        event_id=generate_uuid(),
        authority=updated,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organizational_authority",
        target_id=updated.authority_id,
        action="revoke",
        reason_code="ORGANIZATIONAL_AUTHORITY_REVOKED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=authority_state_payload(updated),
        clock=clock,
    )
    return AuthorityResult(authority=updated, event=event, audit_event=audit_event)


def assert_authority_usable(authority: OrganizationalAuthority, *, at: datetime) -> None:
    """Canon 19e.17 rule 7: expired, revoked, or suspended authority
    cannot be used."""
    if not authority.is_usable(at=at):
        raise OrganizationalAuthorityNotUsableError(
            f"authority {authority.authority_id} is not usable at {at.isoformat()} "
            f"(status={authority.status.value!r})"
        )


# =============================================================================
# Regional scope authorization (canon 19e.12) - default-deny engine.
# =============================================================================


def _hierarchy_ancestors(
    relation_store: OrganizationalRelationStore, *, organization_id: UUID, at: datetime
) -> set[UUID]:
    """BFS up the active `parent_of`/`subordinate_to` edges from
    `organization_id`, returning every ancestor reachable at `at`."""
    ancestors: set[UUID] = set()
    frontier = [organization_id]
    visited: set[UUID] = set()
    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        for relation in relation_store.list_active_for_organization(node):
            if relation.relation_category is not RelationCategory.HIERARCHY:
                continue
            if not is_effective(relation.valid_from, relation.valid_until, at=at):
                continue
            parent: UUID | None = None
            if relation.relation_type is RelationType.PARENT_OF and (
                relation.target_organization_id == node
            ):
                parent = relation.source_organization_id
            elif (
                relation.relation_type is RelationType.SUBORDINATE_TO
                and relation.source_organization_id == node
            ):
                parent = relation.target_organization_id
            if parent is not None and parent not in ancestors:
                ancestors.add(parent)
                frontier.append(parent)
    return ancestors


def check_regional_scope_access(
    relation_store: OrganizationalRelationStore,
    inheritance_policy_store: OrganizationalInheritancePolicyStore,
    delegation_store: ScopeDelegationGrantStore,
    authority_store: OrganizationalAuthorityStore,
    *,
    actor_scope: OrganizationalScope,
    target_scope: OrganizationalScope,
    role_code: str | None,
    action_code: str,
    access_kind: str = "data_access",
    evaluated_at: datetime,
    audit_reference: UUID | None = None,
) -> RegionalScopeAccessDecision:
    """Canon 19e.12: a narrow, atomic, server-side, default-deny read.
    `access_kind` is `"data_access"` (the default - modes 1-5 only, mode
    6 never itself satisfies a data-access check) or
    `"procedural_oversight"` (mode 6 alone may satisfy it). Role names and
    hierarchy position are never, by themselves, treated as proof of
    authority (19e.12's hard rules) - every branch below resolves through
    an actual, currently-effective record."""
    now = evaluated_at

    # Mode 1: exact-scope access.
    if actor_scope.matches(target_scope):
        return RegionalScopeAccessDecision(
            allowed=True,
            reason_code="",
            evaluated_scope=target_scope,
            policy_version=actor_scope.policy_version,
            effective_time=now,
            mode=AccessMode.EXACT_SCOPE,
            audit_reference=audit_reference,
        )

    # Modes 2/3 only apply between two organization-scope references.
    if (
        actor_scope.scope_type is ScopeType.ORGANIZATION_SCOPE
        and target_scope.scope_type is ScopeType.ORGANIZATION_SCOPE
        and role_code is not None
    ):
        actor_org_id = UUID(actor_scope.scope_reference)
        target_org_id = UUID(target_scope.scope_reference)
        policy = inheritance_policy_store.resolve_for_role(role_code, at=now)
        if policy is not None:
            # Mode 2: ancestor-scope access - actor is an ancestor of target.
            if policy.allows(InheritanceMode.ANCESTOR):
                target_ancestors = _hierarchy_ancestors(
                    relation_store, organization_id=target_org_id, at=now
                )
                if actor_org_id in target_ancestors:
                    return RegionalScopeAccessDecision(
                        allowed=True,
                        reason_code="",
                        evaluated_scope=target_scope,
                        policy_version=str(policy.policy_version),
                        effective_time=now,
                        mode=AccessMode.ANCESTOR_SCOPE,
                        audit_reference=audit_reference,
                    )
            # Mode 3: descendant-scope access - actor is a descendant of target.
            if policy.allows(InheritanceMode.DESCENDANT):
                actor_ancestors = _hierarchy_ancestors(
                    relation_store, organization_id=actor_org_id, at=now
                )
                if target_org_id in actor_ancestors:
                    return RegionalScopeAccessDecision(
                        allowed=True,
                        reason_code="",
                        evaluated_scope=target_scope,
                        policy_version=str(policy.policy_version),
                        effective_time=now,
                        mode=AccessMode.DESCENDANT_SCOPE,
                        audit_reference=audit_reference,
                    )

    # Mode 4: explicitly delegated cross-scope access.
    grant = delegation_store.find_usable(
        delegate_scope=actor_scope, target_scope=target_scope, action_code=action_code, at=now
    )
    if grant is not None:
        return RegionalScopeAccessDecision(
            allowed=True,
            reason_code="",
            evaluated_scope=target_scope,
            policy_version=grant.policy_version,
            effective_time=now,
            mode=AccessMode.DELEGATED_CROSS_SCOPE,
            audit_reference=audit_reference,
        )

    # Mode 5: temporary supervision.
    if (
        actor_scope.scope_type is ScopeType.ORGANIZATION_SCOPE
        and target_scope.scope_type is ScopeType.ORGANIZATION_SCOPE
    ):
        actor_org_id = UUID(actor_scope.scope_reference)
        target_org_id = UUID(target_scope.scope_reference)
        for relation in relation_store.list_active_by_type(RelationType.TEMPORARY_SUPERVISION_BY):
            if (
                relation.source_organization_id == actor_org_id
                and relation.target_organization_id == target_org_id
                and is_effective(relation.valid_from, relation.valid_until, at=now)
            ):
                return RegionalScopeAccessDecision(
                    allowed=True,
                    reason_code="",
                    evaluated_scope=target_scope,
                    policy_version=None,
                    effective_time=now,
                    mode=AccessMode.TEMPORARY_SUPERVISION,
                    audit_reference=audit_reference,
                )

    # Mode 6: institutional oversight without implicit data access -
    # never satisfies a data_access check, only procedural_oversight.
    if access_kind == "procedural_oversight":
        for authority in authority_store.list_active_for_scope(target_scope, at=now):
            if authority.grants_procedural_authority:
                return RegionalScopeAccessDecision(
                    allowed=True,
                    reason_code="",
                    evaluated_scope=target_scope,
                    policy_version=authority.policy_version,
                    effective_time=now,
                    mode=AccessMode.INSTITUTIONAL_OVERSIGHT_WITHOUT_DATA_ACCESS,
                    audit_reference=audit_reference,
                )

    return RegionalScopeAccessDecision(
        allowed=False,
        reason_code="CROSS_SCOPE_ACCESS_DENIED",
        evaluated_scope=target_scope,
        policy_version=None,
        effective_time=now,
        mode=None,
        audit_reference=audit_reference,
    )


def assert_regional_scope_access_allowed(decision: RegionalScopeAccessDecision) -> None:
    if not decision.allowed:
        raise CrossScopeAccessDeniedError(f"regional scope access denied: {decision.reason_code}")


#: Canon 19e.20: `regional_scope_access.granted` is created only for modes
#: 2-5 - mode 1 (exact-scope, the default) and mode 6 (institutional
#: oversight without data access, which grants no data access by
#: definition) never create this event.
_GRANT_EVENT_MODES = frozenset(
    {
        AccessMode.ANCESTOR_SCOPE,
        AccessMode.DESCENDANT_SCOPE,
        AccessMode.DELEGATED_CROSS_SCOPE,
        AccessMode.TEMPORARY_SUPERVISION,
    }
)


@dataclass(frozen=True, slots=True)
class RegionalScopeAccessAuditResult:
    event: EventEnvelope
    audit_event: AuditEvent


def record_regional_scope_access_grant(
    audit_store: AuditEventStore,
    *,
    decision: RegionalScopeAccessDecision,
    subject_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> RegionalScopeAccessAuditResult | None:
    """The sanctioned way a caller records `regional_scope_access.granted`
    plus its audit event, once `check_regional_scope_access` (a pure,
    side-effect-free read, mirroring every prior pack's own atomic-
    capability-check pattern) has returned an allowed decision. Returns
    `None` for mode 1/6 decisions, which never create this event (canon
    19e.20) - and for any denied decision, which the caller should audit
    itself as a rejected-access record where policy requires it (task
    section 21)."""
    if not decision.allowed or decision.mode not in _GRANT_EVENT_MODES:
        return None
    now = clock.now()
    event = build_regional_scope_access_granted_event(
        event_id=generate_uuid(),
        decision=decision,
        actor=actor,
        subject_id=subject_id,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="regional_scope_access",
        target_id=subject_id,
        action="grant",
        reason_code="REGIONAL_SCOPE_ACCESS_GRANTED",
        actor=actor,
        correlation_id=correlation_id,
        after_state={
            "scope_type": decision.evaluated_scope.scope_type.value,
            "scope_reference": decision.evaluated_scope.scope_reference,
            "mode": decision.mode.value if decision.mode else None,
        },
        clock=clock,
    )
    return RegionalScopeAccessAuditResult(event=event, audit_event=audit_event)


def record_regional_scope_access_revocation(
    audit_store: AuditEventStore,
    *,
    subject_id: UUID,
    actor: ActorRef,
    correlation_id: UUID,
    clock: Clock,
) -> RegionalScopeAccessAuditResult:
    """Records `regional_scope_access.revoked` plus its audit event -
    called by whichever caller revokes the underlying delegation/
    temporary-supervision/inheritance-policy grant that previously
    satisfied a `regional_scope_access.granted` record for `subject_id`."""
    now = clock.now()
    event = build_regional_scope_access_revoked_event(
        event_id=generate_uuid(),
        scope=None,
        subject_id=subject_id,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="regional_scope_access",
        target_id=subject_id,
        action="revoke",
        reason_code="REGIONAL_SCOPE_ACCESS_REVOKED",
        actor=actor,
        correlation_id=correlation_id,
        after_state={"subject_id": str(subject_id)},
        clock=clock,
    )
    return RegionalScopeAccessAuditResult(event=event, audit_event=audit_event)


def create_scope_delegation_grant(
    delegation_store: ScopeDelegationGrantStore,
    *,
    grant_id: UUID,
    delegate_scope: OrganizationalScope,
    target_scope: OrganizationalScope,
    action_code: str,
    authorizing_decision_reference: UUID,
    policy_version: str,
    valid_from: datetime,
    valid_until: datetime | None,
    actor_is_authorized: bool,
) -> ScopeDelegationGrant:
    """Section 19e.12 mode 4: a time-bounded, purpose-recorded delegation
    record - always its own explicit governed decision, never implied by
    hierarchy position."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to create a scope delegation grant")
    grant = ScopeDelegationGrant(
        grant_id=grant_id,
        delegate_scope=delegate_scope,
        target_scope=target_scope,
        action_code=action_code,
        authorizing_decision_reference=authorizing_decision_reference,
        policy_version=policy_version,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    delegation_store.save(grant)
    return grant


def extend_temporary_supervision(
    relation_store: OrganizationalRelationStore,
    audit_store: AuditEventStore,
    *,
    relation_id: UUID,
    new_valid_until: datetime,
    new_authorizing_decision_reference: UUID,
    actor: ActorRef,
    actor_is_authorized: bool,
    correlation_id: UUID,
    clock: Clock,
) -> RelationResult:
    """Canon 19e.14: extending a temporary-supervision window requires a
    NEW, separately governed decision and creates its own new audit
    record - never a silent extension of the existing record. Modeled as:
    end the current relation at its own current `valid_until`, then
    create a new relation version covering the extended window."""
    if not actor_is_authorized:
        raise PermissionDeniedError("actor is not authorized to extend temporary supervision")
    current = relation_store.get(relation_id)
    if current is None:
        raise UnknownOrganizationalRelationError(f"unknown relation_id: {relation_id}")
    if current.relation_type is not RelationType.TEMPORARY_SUPERVISION_BY:
        raise ValueError(
            "extend_temporary_supervision only applies to temporary_supervision_by relations"
        )
    assert_temporary_supervision_window_valid(current.valid_from, new_valid_until)

    ended = end_organizational_relation(
        relation_store,
        audit_store,
        relation_id=relation_id,
        valid_until=current.valid_until if current.valid_until else clock.now(),
        actor=actor,
        actor_is_authorized=actor_is_authorized,
        correlation_id=correlation_id,
        clock=clock,
    )
    new_relation = OrganizationalRelation(
        relation_id=generate_uuid(),
        relation_version=current.relation_version + 1,
        relation_type=RelationType.TEMPORARY_SUPERVISION_BY,
        source_organization_id=current.source_organization_id,
        target_organization_id=current.target_organization_id,
        status=RelationStatus.ACTIVE,
        valid_from=current.valid_from,
        valid_until=new_valid_until,
        recorded_at=clock.now(),
        supersedes_relation_id=current.relation_id,
        authorizing_decision_reference=new_authorizing_decision_reference,
    )
    relation_store.save(new_relation)
    now = clock.now()
    event = build_organizational_relation_created_event(
        event_id=generate_uuid(),
        relation=new_relation,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=None,
        occurred_at=now,
    )
    audit_event = _audit(
        audit_store,
        event=event,
        target_type="organizational_relation",
        target_id=new_relation.relation_id,
        action="extend_temporary_supervision",
        reason_code="ORGANIZATIONAL_RELATION_CREATED",
        actor=actor,
        correlation_id=correlation_id,
        after_state=relation_state_payload(new_relation),
        clock=clock,
    )
    del ended  # the ended-relation result is available via relation_store if needed
    return RelationResult(relation=new_relation, event=event, audit_event=audit_event)

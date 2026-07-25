"""Application-layer tests for Organization Service (PACK-08
implementation round). Covers task section 24's required test list:
reorganization (merge/split/successor, no automatic transfer),
authority lifecycle (self-assignment, incompatible role, expired/revoked/
dissolved-organization rejection, dual control), and regional
authorization (default deny, all six access modes, expired delegation,
cross-Land denial, no universal admin, confused-deputy prevention)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from epd2_organization_service.application import (
    activate_organization,
    activate_organizational_authority,
    assert_regional_scope_access_allowed,
    assert_successor_transfer_has_own_decision,
    assign_organizational_authority,
    check_regional_scope_access,
    create_organization,
    create_organizational_relation,
    create_scope_delegation_grant,
    declare_successor,
    dissolve_organization,
    end_organizational_relation,
    merge_organizations,
    reassign_territorial_parent,
    recompute_parent_reference,
    revoke_organizational_authority,
    split_organization,
    suspend_organization,
)
from epd2_organization_service.domain import (
    InstitutionalRole,
    Organization,
    OrganizationStatus,
    RelationStatus,
    RelationType,
    organization_scope,
)
from epd2_organization_service.exceptions import (
    AuthorityRoleIncompatibleError,
    CrossScopeAccessDeniedError,
    OrganizationalAuthorityNotUsableError,
    OrganizationalCycleForbiddenError,
    OrganizationDualControlViolationError,
    OrganizationNotActiveError,
    OrganizationSelfAssignmentForbiddenError,
    SuccessorTransferRequiresDecisionError,
)
from epd2_organization_service.storage import (
    InMemoryOrganizationalAuthorityStore,
    InMemoryOrganizationalHierarchyOverlapPolicyStore,
    InMemoryOrganizationalInheritancePolicyStore,
    InMemoryOrganizationalRelationStore,
    InMemoryOrganizationStore,
    InMemoryScopeDelegationGrantStore,
)

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef

T0 = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(T0)


@pytest.fixture
def actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


@pytest.fixture
def organization_store() -> InMemoryOrganizationStore:
    return InMemoryOrganizationStore()


@pytest.fixture
def relation_store() -> InMemoryOrganizationalRelationStore:
    return InMemoryOrganizationalRelationStore()


@pytest.fixture
def overlap_policy_store() -> InMemoryOrganizationalHierarchyOverlapPolicyStore:
    return InMemoryOrganizationalHierarchyOverlapPolicyStore()


@pytest.fixture
def inheritance_policy_store() -> InMemoryOrganizationalInheritancePolicyStore:
    return InMemoryOrganizationalInheritancePolicyStore()


@pytest.fixture
def authority_store() -> InMemoryOrganizationalAuthorityStore:
    return InMemoryOrganizationalAuthorityStore()


@pytest.fixture
def delegation_store() -> InMemoryScopeDelegationGrantStore:
    return InMemoryScopeDelegationGrantStore()


@pytest.fixture
def audit_store() -> InMemoryAuditEventStore:
    return InMemoryAuditEventStore()


def _create_active_organization(
    organization_store: InMemoryOrganizationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
    **overrides: object,
) -> Organization:
    defaults: dict[str, object] = dict(
        organization_id=uuid4(),
        name="Landesverband Beispiel",
        legal_operator="Beispiel e.V.",
        organization_type="party_unit",
        organization_profile="landesverband",
        default_policy_version="1.0",
        effective_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    defaults.update(overrides)
    result = create_organization(organization_store, audit_store, **defaults)  # type: ignore[arg-type]
    activated = activate_organization(
        organization_store,
        audit_store,
        organization_id=result.organization.organization_id,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    return activated.organization


# ---------------------------------------------------------------------------
# Organization lifecycle
# ---------------------------------------------------------------------------


def test_create_activate_suspend_dissolve_organization(
    organization_store: InMemoryOrganizationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    assert organization.status is OrganizationStatus.ACTIVE

    suspended = suspend_organization(
        organization_store,
        audit_store,
        organization_id=organization.organization_id,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert suspended.organization.status is OrganizationStatus.RESTRICTED

    dissolved = dissolve_organization(
        organization_store,
        audit_store,
        organization_id=organization.organization_id,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert dissolved.organization.status is OrganizationStatus.ARCHIVED
    assert dissolved.organization.dissolved_at is not None
    assert dissolved.audit_event is not None


# ---------------------------------------------------------------------------
# Reorganization: merge / split / successor - no automatic transfer.
# ---------------------------------------------------------------------------


def test_merge_dissolves_sources_and_creates_merged_into_relations(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    source_a = _create_active_organization(organization_store, audit_store, actor, clock)
    source_b = _create_active_organization(organization_store, audit_store, actor, clock)
    target = _create_active_organization(organization_store, audit_store, actor, clock)

    result = merge_organizations(
        organization_store,
        relation_store,
        audit_store,
        source_organization_ids=[source_a.organization_id, source_b.organization_id],
        target_organization_id=target.organization_id,
        authorizing_decision_reference=uuid4(),
        valid_from=T0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert len(result.relations) == 2
    for relation in result.relations:
        assert relation.relation_type is RelationType.MERGED_INTO
        assert relation.target_organization_id == target.organization_id
    for source_result in result.source_results:
        assert source_result.organization.status is OrganizationStatus.ARCHIVED


def test_split_creates_split_from_relations_and_respects_source_continues(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    source = _create_active_organization(organization_store, audit_store, actor, clock)
    result_a = _create_active_organization(organization_store, audit_store, actor, clock)
    result_b = _create_active_organization(organization_store, audit_store, actor, clock)

    split = split_organization(
        organization_store,
        relation_store,
        audit_store,
        source_organization_id=source.organization_id,
        resulting_organization_ids=[result_a.organization_id, result_b.organization_id],
        source_continues=True,
        authorizing_decision_reference=uuid4(),
        valid_from=T0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert split.source_result is None  # source_continues=True -> not dissolved
    assert len(split.relations) == 2
    for relation in split.relations:
        assert relation.relation_type is RelationType.SPLIT_FROM
        assert relation.target_organization_id == source.organization_id


def test_declare_successor_populates_successor_reference(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    predecessor = _create_active_organization(organization_store, audit_store, actor, clock)
    successor = _create_active_organization(organization_store, audit_store, actor, clock)

    relation, result = declare_successor(
        organization_store,
        relation_store,
        audit_store,
        predecessor_organization_id=predecessor.organization_id,
        successor_organization_id=successor.organization_id,
        authorizing_decision_reference=uuid4(),
        valid_from=T0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert relation.relation_type is RelationType.SUCCESSOR_OF
    assert result.organization.successor_reference == successor.organization_id


def test_successor_transfer_requires_its_own_explicit_decision() -> None:
    """Canon 19e.10's hard invariant: no automatic role/authority/access
    transfer from a merge/split/succession relation alone."""
    with pytest.raises(SuccessorTransferRequiresDecisionError):
        assert_successor_transfer_has_own_decision(
            reorganization_decision_reference=uuid4(), transfer_decision_reference=None
        )
    # Passes when an explicit, distinct decision reference is supplied.
    assert_successor_transfer_has_own_decision(
        reorganization_decision_reference=uuid4(), transfer_decision_reference=uuid4()
    )


def test_merge_never_itself_creates_or_extends_authority(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """No OrganizationalAuthority row is created as a side effect of
    merge_organizations - authority must be assigned via its own explicit
    assign_organizational_authority call, gated by its own decision."""
    source = _create_active_organization(organization_store, audit_store, actor, clock)
    target = _create_active_organization(organization_store, audit_store, actor, clock)
    merge_organizations(
        organization_store,
        relation_store,
        audit_store,
        source_organization_ids=[source.organization_id],
        target_organization_id=target.organization_id,
        authorizing_decision_reference=uuid4(),
        valid_from=T0,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert authority_store.list_all() == ()


# ---------------------------------------------------------------------------
# OrganizationalRelation: cycles, overlap, graph query.
# ---------------------------------------------------------------------------


def test_create_relation_and_query_graph(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    parent = _create_active_organization(organization_store, audit_store, actor, clock)
    child = _create_active_organization(organization_store, audit_store, actor, clock)

    result = create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=parent.organization_id,
        target_organization_id=child.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.relation.status is RelationStatus.ACTIVE
    graph = relation_store.list_active_for_organization(parent.organization_id)
    assert len(graph) == 1


def test_multiple_relation_types_between_same_organizations(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    a = _create_active_organization(organization_store, audit_store, actor, clock)
    b = _create_active_organization(organization_store, audit_store, actor, clock)

    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.OPERATES_WITHIN,
        source_organization_id=a.organization_id,
        target_organization_id=b.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.AFFILIATED_WITH,
        source_organization_id=a.organization_id,
        target_organization_id=b.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    relations = relation_store.list_active_for_organization(a.organization_id)
    assert len(relations) == 2
    assert {r.relation_type for r in relations} == {
        RelationType.OPERATES_WITHIN,
        RelationType.AFFILIATED_WITH,
    }


def test_forbidden_hierarchical_cycle_rejected_end_to_end(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    a = _create_active_organization(organization_store, audit_store, actor, clock)
    b = _create_active_organization(organization_store, audit_store, actor, clock)
    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=a.organization_id,
        target_organization_id=b.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(OrganizationalCycleForbiddenError):
        create_organizational_relation(
            relation_store,
            overlap_policy_store,
            audit_store,
            relation_id=uuid4(),
            relation_type=RelationType.PARENT_OF,
            source_organization_id=b.organization_id,
            target_organization_id=a.organization_id,
            valid_from=T0,
            authorizing_decision_reference=uuid4(),
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


def test_relation_end_sets_valid_until(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    a = _create_active_organization(organization_store, audit_store, actor, clock)
    b = _create_active_organization(organization_store, audit_store, actor, clock)
    result = create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=a.organization_id,
        target_organization_id=b.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    ended = end_organizational_relation(
        relation_store,
        audit_store,
        relation_id=result.relation.relation_id,
        valid_until=T0 + timedelta(days=100),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert ended.relation.status is RelationStatus.ENDED
    assert ended.relation.valid_until == T0 + timedelta(days=100)


def test_territorial_reassignment_ends_old_and_creates_new_relation(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    child = _create_active_organization(organization_store, audit_store, actor, clock)
    old_parent = _create_active_organization(organization_store, audit_store, actor, clock)
    new_parent = _create_active_organization(organization_store, audit_store, actor, clock)

    original = create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=old_parent.organization_id,
        target_organization_id=child.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    ended, created = reassign_territorial_parent(
        relation_store,
        overlap_policy_store,
        audit_store,
        old_relation_id=original.relation.relation_id,
        child_organization_id=child.organization_id,
        new_parent_organization_id=new_parent.organization_id,
        relation_type=RelationType.PARENT_OF,
        reassignment_at=T0 + timedelta(days=200),
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert ended.relation.status is RelationStatus.ENDED
    assert created.relation.source_organization_id == new_parent.organization_id
    parent_ref = recompute_parent_reference(
        relation_store, organization_id=child.organization_id, at=T0 + timedelta(days=201)
    )
    assert parent_ref == new_parent.organization_id


def test_parent_reference_omitted_when_multiple_concurrent_parents(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Canon 19e.3/19e.4: parent_reference may be omitted entirely where
    more than one concurrent parent-shaped edge exists - never arbitrarily
    picking one."""
    from epd2_organization_service.domain import (
        OrganizationalHierarchyOverlapPolicy,
        PolicyStatus,
    )

    child = _create_active_organization(organization_store, audit_store, actor, clock)
    parent_a = _create_active_organization(organization_store, audit_store, actor, clock)
    parent_b = _create_active_organization(organization_store, audit_store, actor, clock)

    overlap_policy_store.save(
        OrganizationalHierarchyOverlapPolicy(
            policy_id=uuid4(),
            policy_version=1,
            applicable_relation_types=(RelationType.PARENT_OF,),
            overlap_permitted=True,
            authorizing_decision_reference=uuid4(),
            status=PolicyStatus.ACTIVE,
            valid_from=T0,
        )
    )
    for parent in (parent_a, parent_b):
        create_organizational_relation(
            relation_store,
            overlap_policy_store,
            audit_store,
            relation_id=uuid4(),
            relation_type=RelationType.PARENT_OF,
            source_organization_id=parent.organization_id,
            target_organization_id=child.organization_id,
            valid_from=T0,
            authorizing_decision_reference=uuid4(),
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )
    parent_ref = recompute_parent_reference(
        relation_store, organization_id=child.organization_id, at=T0 + timedelta(days=1)
    )
    assert parent_ref is None


# ---------------------------------------------------------------------------
# OrganizationalAuthority: assignment, incompatibility, lifecycle,
# dual control.
# ---------------------------------------------------------------------------


def test_valid_authority_assignment(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    result = assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.DPO.value,
        scope=organization_scope(organization.organization_id),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.authority.role_code == InstitutionalRole.DPO.value


def test_self_assignment_rejected_end_to_end(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    subject = uuid4()
    with pytest.raises(OrganizationSelfAssignmentForbiddenError):
        assign_organizational_authority(
            organization_store,
            authority_store,
            audit_store,
            authority_id=uuid4(),
            role_code=InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR.value,
            scope=organization_scope(organization.organization_id),
            appointing_authority_reference=subject,
            assigned_subject_reference=subject,
            valid_from=T0,
            policy_version="1.0",
            decision_reference=uuid4(),
            grants_procedural_authority=True,
            grants_data_access=True,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


def test_incompatible_role_assignment_rejected(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    scope = organization_scope(organization.organization_id)
    subject = uuid4()
    assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.ELECTION_OFFICER.value,
        scope=scope,
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=subject,
        valid_from=T0,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(AuthorityRoleIncompatibleError):
        assign_organizational_authority(
            organization_store,
            authority_store,
            audit_store,
            authority_id=uuid4(),
            role_code=InstitutionalRole.INDEPENDENT_AUDITOR.value,
            scope=scope,
            appointing_authority_reference=uuid4(),
            assigned_subject_reference=subject,
            valid_from=T0,
            policy_version="1.0",
            decision_reference=uuid4(),
            grants_procedural_authority=True,
            grants_data_access=False,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


def test_authority_assignment_rejected_for_non_active_organization(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    result = create_organization(
        organization_store,
        audit_store,
        organization_id=uuid4(),
        name="Draft Verband",
        legal_operator="Beispiel e.V.",
        organization_type="party_unit",
        organization_profile="kreisverband",
        default_policy_version="1.0",
        effective_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(OrganizationNotActiveError):
        assign_organizational_authority(
            organization_store,
            authority_store,
            audit_store,
            authority_id=uuid4(),
            role_code=InstitutionalRole.DPO.value,
            scope=organization_scope(result.organization.organization_id),
            appointing_authority_reference=uuid4(),
            assigned_subject_reference=uuid4(),
            valid_from=T0,
            policy_version="1.0",
            decision_reference=uuid4(),
            grants_procedural_authority=True,
            grants_data_access=False,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


def test_authority_assignment_rejected_for_dissolved_organization(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    dissolve_organization(
        organization_store,
        audit_store,
        organization_id=organization.organization_id,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(OrganizationNotActiveError):
        assign_organizational_authority(
            organization_store,
            authority_store,
            audit_store,
            authority_id=uuid4(),
            role_code=InstitutionalRole.DPO.value,
            scope=organization_scope(organization.organization_id),
            appointing_authority_reference=uuid4(),
            assigned_subject_reference=uuid4(),
            valid_from=T0,
            policy_version="1.0",
            decision_reference=uuid4(),
            grants_procedural_authority=True,
            grants_data_access=False,
            actor=actor,
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=clock,
        )


def test_expired_authority_rejected_by_assert_usable(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    from epd2_organization_service.application import assert_authority_usable

    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    result = assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.DPO.value,
        scope=organization_scope(organization.organization_id),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        valid_until=T0 + timedelta(days=30),
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(OrganizationalAuthorityNotUsableError):
        assert_authority_usable(result.authority, at=T0 + timedelta(days=31))


def test_revoked_authority_rejected(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    from epd2_organization_service.application import assert_authority_usable

    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    result = assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.DPO.value,
        scope=organization_scope(organization.organization_id),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    revoked = revoke_organizational_authority(
        authority_store,
        audit_store,
        authority_id=result.authority.authority_id,
        revocation_reason_reference="policy_violation",
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    with pytest.raises(OrganizationalAuthorityNotUsableError):
        assert_authority_usable(revoked.authority, at=T0)


def test_dual_control_enforcement(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """Canon 19e.16 rule 8 / 19e.17 rule 5: the activating actor must
    differ from the proposing appointing_authority_reference."""
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    proposer = uuid4()
    result = assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.ELECTION_BOARD_MEMBER.value,
        scope=organization_scope(organization.organization_id),
        appointing_authority_reference=proposer,
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        require_dual_control=True,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    assert result.authority.status.value == "proposed"

    with pytest.raises(OrganizationDualControlViolationError):
        activate_organizational_authority(
            authority_store,
            authority_id=result.authority.authority_id,
            activating_actor_reference=proposer,
            actor_is_authorized=True,
        )

    activated = activate_organizational_authority(
        authority_store,
        authority_id=result.authority.authority_id,
        activating_actor_reference=uuid4(),
        actor_is_authorized=True,
    )
    assert activated.status.value == "active"


# ---------------------------------------------------------------------------
# Regional scope authorization (canon 19e.12): default deny + six modes.
# ---------------------------------------------------------------------------


def test_default_deny_when_no_mode_matches(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    actor_scope = organization_scope(uuid4())
    target_scope = organization_scope(uuid4())
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=actor_scope,
        target_scope=target_scope,
        role_code=None,
        action_code="read",
        evaluated_at=T0,
    )
    assert not decision.allowed
    assert decision.reason_code == "CROSS_SCOPE_ACCESS_DENIED"
    with pytest.raises(CrossScopeAccessDeniedError):
        assert_regional_scope_access_allowed(decision)


def test_exact_scope_access_granted(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    org_id = uuid4()
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(org_id),
        target_scope=organization_scope(org_id),
        role_code=None,
        action_code="read",
        evaluated_at=T0,
    )
    assert decision.allowed
    assert decision.mode is not None and decision.mode.value == "exact_scope"


def test_ancestor_scope_access_requires_inheritance_policy(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    parent = _create_active_organization(organization_store, audit_store, actor, clock)
    child = _create_active_organization(organization_store, audit_store, actor, clock)
    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=parent.organization_id,
        target_organization_id=child.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )

    # Without a policy, ancestor access is denied (never assumed from
    # hierarchy position alone).
    denied = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(parent.organization_id),
        target_scope=organization_scope(child.organization_id),
        role_code="kreisvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert not denied.allowed

    from epd2_organization_service.domain import (
        InheritanceMode,
        OrganizationalInheritancePolicy,
        PolicyStatus,
    )

    inheritance_policy_store.save(
        OrganizationalInheritancePolicy(
            policy_id=uuid4(),
            policy_version=1,
            role_code="kreisvorsitzender",
            inheritance_mode=InheritanceMode.ANCESTOR,
            authorizing_decision_reference=uuid4(),
            status=PolicyStatus.ACTIVE,
            valid_from=T0,
        )
    )
    granted = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(parent.organization_id),
        target_scope=organization_scope(child.organization_id),
        role_code="kreisvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert granted.allowed
    assert granted.mode is not None and granted.mode.value == "ancestor_scope"


def test_descendant_scope_access_symmetric_to_ancestor(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    parent = _create_active_organization(organization_store, audit_store, actor, clock)
    child = _create_active_organization(organization_store, audit_store, actor, clock)
    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.PARENT_OF,
        source_organization_id=parent.organization_id,
        target_organization_id=child.organization_id,
        valid_from=T0,
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    from epd2_organization_service.domain import (
        InheritanceMode,
        OrganizationalInheritancePolicy,
        PolicyStatus,
    )

    inheritance_policy_store.save(
        OrganizationalInheritancePolicy(
            policy_id=uuid4(),
            policy_version=1,
            role_code="ortsverbandsvorsitzender",
            inheritance_mode=InheritanceMode.DESCENDANT,
            authorizing_decision_reference=uuid4(),
            status=PolicyStatus.ACTIVE,
            valid_from=T0,
        )
    )
    granted = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(child.organization_id),
        target_scope=organization_scope(parent.organization_id),
        role_code="ortsverbandsvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert granted.allowed
    assert granted.mode is not None and granted.mode.value == "descendant_scope"


def test_cross_land_denial_without_explicit_grant(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    """Task section 24: cross-Land denial - a Landesverband-scoped actor
    never receives another Land's data without an explicit mode 4/5
    grant."""
    land_a = organization_scope(uuid4())
    land_b = organization_scope(uuid4())
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=land_a,
        target_scope=land_b,
        role_code="landesvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert not decision.allowed


def test_delegated_cross_scope_access_granted_and_expires(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    delegate = organization_scope(uuid4())
    target = organization_scope(uuid4())
    create_scope_delegation_grant(
        delegation_store,
        grant_id=uuid4(),
        delegate_scope=delegate,
        target_scope=target,
        action_code="read",
        authorizing_decision_reference=uuid4(),
        policy_version="1.0",
        valid_from=T0,
        valid_until=T0 + timedelta(days=30),
        actor_is_authorized=True,
    )
    granted = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=delegate,
        target_scope=target,
        role_code=None,
        action_code="read",
        evaluated_at=T0 + timedelta(days=1),
    )
    assert granted.allowed
    assert granted.mode is not None and granted.mode.value == "delegated_cross_scope"

    expired = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=delegate,
        target_scope=target,
        role_code=None,
        action_code="read",
        evaluated_at=T0 + timedelta(days=31),
    )
    assert not expired.allowed


def test_temporary_supervision_grants_access_within_window(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    supervisor = _create_active_organization(organization_store, audit_store, actor, clock)
    supervised = _create_active_organization(organization_store, audit_store, actor, clock)
    create_organizational_relation(
        relation_store,
        overlap_policy_store,
        audit_store,
        relation_id=uuid4(),
        relation_type=RelationType.TEMPORARY_SUPERVISION_BY,
        source_organization_id=supervisor.organization_id,
        target_organization_id=supervised.organization_id,
        valid_from=T0,
        valid_until=T0 + timedelta(days=60),
        authorizing_decision_reference=uuid4(),
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(supervisor.organization_id),
        target_scope=organization_scope(supervised.organization_id),
        role_code=None,
        action_code="read",
        evaluated_at=T0 + timedelta(days=10),
    )
    assert decision.allowed
    assert decision.mode is not None and decision.mode.value == "temporary_supervision"


def test_institutional_oversight_without_data_access_never_grants_data_access(
    organization_store: InMemoryOrganizationStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
) -> None:
    """Canon 19e.12 mode 6: grants_procedural_authority=True but
    grants_data_access=False must never itself satisfy a data_access
    check - only a procedural_oversight check."""
    organization = _create_active_organization(organization_store, audit_store, actor, clock)
    scope = organization_scope(organization.organization_id)
    assign_organizational_authority(
        organization_store,
        authority_store,
        audit_store,
        authority_id=uuid4(),
        role_code=InstitutionalRole.INDEPENDENT_AUDITOR.value,
        scope=scope,
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
        actor=actor,
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=clock,
    )
    actor_scope = organization_scope(uuid4())
    data_access_denied = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=actor_scope,
        target_scope=scope,
        role_code=None,
        action_code="read",
        access_kind="data_access",
        evaluated_at=T0,
    )
    assert not data_access_denied.allowed

    procedural_granted = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=actor_scope,
        target_scope=scope,
        role_code=None,
        action_code="oversee",
        access_kind="procedural_oversight",
        evaluated_at=T0,
    )
    assert procedural_granted.allowed
    assert (
        procedural_granted.mode is not None
        and procedural_granted.mode.value == "institutional_oversight_without_data_access"
    )


def test_no_universal_admin_via_global_scope_inheritance(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    """Canon 19e.12: no universal administrator may emerge through scope
    inheritance - a role_code with no matching policy never grants
    ancestor/descendant access, regardless of how broad its name sounds."""
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(uuid4()),
        target_scope=organization_scope(uuid4()),
        role_code="bundesvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert not decision.allowed


def test_confused_deputy_prevention_scope_revalidated_every_call(
    organization_store: InMemoryOrganizationStore,
    relation_store: InMemoryOrganizationalRelationStore,
    overlap_policy_store: InMemoryOrganizationalHierarchyOverlapPolicyStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
    audit_store: InMemoryAuditEventStore,
    actor: ActorRef,
    clock: FixedClock,
) -> None:
    """An authorization for scope A is never honored against scope B
    merely because the same delegation grant is presented - every check
    re-validates actor scope against the SPECIFIC target scope."""
    delegate = organization_scope(uuid4())
    target_a = organization_scope(uuid4())
    target_b = organization_scope(uuid4())
    create_scope_delegation_grant(
        delegation_store,
        grant_id=uuid4(),
        delegate_scope=delegate,
        target_scope=target_a,
        action_code="read",
        authorizing_decision_reference=uuid4(),
        policy_version="1.0",
        valid_from=T0,
        valid_until=None,
        actor_is_authorized=True,
    )
    allowed_a = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=delegate,
        target_scope=target_a,
        role_code=None,
        action_code="read",
        evaluated_at=T0,
    )
    denied_b = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=delegate,
        target_scope=target_b,
        role_code=None,
        action_code="read",
        evaluated_at=T0,
    )
    assert allowed_a.allowed
    assert not denied_b.allowed


def test_role_name_alone_is_never_proof_of_authority(
    relation_store: InMemoryOrganizationalRelationStore,
    inheritance_policy_store: InMemoryOrganizationalInheritancePolicyStore,
    delegation_store: InMemoryScopeDelegationGrantStore,
    authority_store: InMemoryOrganizationalAuthorityStore,
) -> None:
    """Even a role_code that sounds authoritative grants nothing without
    a resolved policy/grant/authority record."""
    decision = check_regional_scope_access(
        relation_store,
        inheritance_policy_store,
        delegation_store,
        authority_store,
        actor_scope=organization_scope(uuid4()),
        target_scope=organization_scope(uuid4()),
        role_code="bundesvorsitzender",
        action_code="read",
        evaluated_at=T0,
    )
    assert not decision.allowed
    assert decision.reason_code == "CROSS_SCOPE_ACCESS_DENIED"

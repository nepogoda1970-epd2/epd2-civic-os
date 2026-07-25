"""Tests for epd2_organization_service.storage's in-memory reference
adapters, focused on the resolution/lookup logic beyond plain save/get
(effective-dated queries, `resolve_for_*` version-selection procedures,
and scope-matching lookups), per this round's own item 20 ("effective-
dated queries must be deterministic; historical records must not be
overwritten")."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from epd2_organization_service.domain import (
    AuthorityStatus,
    InheritanceMode,
    OrganizationalAuthority,
    OrganizationalHierarchyOverlapPolicy,
    OrganizationalInheritancePolicy,
    OrganizationalRelation,
    OrganizationalScope,
    PolicyStatus,
    RelationStatus,
    RelationType,
    ScopeDelegationGrant,
    organization_scope,
)
from epd2_organization_service.storage import (
    InMemoryOrganizationalAuthorityStore,
    InMemoryOrganizationalHierarchyOverlapPolicyStore,
    InMemoryOrganizationalInheritancePolicyStore,
    InMemoryOrganizationalRelationStore,
    InMemoryScopeDelegationGrantStore,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


# ---------------------------------------------------------------------------
# OrganizationalRelationStore
# ---------------------------------------------------------------------------


def _relation(
    *,
    source_organization_id: object = None,
    target_organization_id: object = None,
    relation_type: RelationType = RelationType.PARENT_OF,
    status: RelationStatus = RelationStatus.ACTIVE,
    valid_until: datetime | None = None,
) -> OrganizationalRelation:
    return OrganizationalRelation(
        relation_id=uuid4(),
        relation_version=1,
        relation_type=relation_type,
        source_organization_id=source_organization_id or uuid4(),  # type: ignore[arg-type]
        target_organization_id=target_organization_id or uuid4(),  # type: ignore[arg-type]
        status=status,
        valid_from=_NOW - timedelta(days=1),
        valid_until=valid_until,
        recorded_at=_NOW,
    )


def test_relation_store_list_active_excludes_ended_and_superseded() -> None:
    store = InMemoryOrganizationalRelationStore()
    active = _relation(status=RelationStatus.ACTIVE)
    ended = _relation(status=RelationStatus.ENDED)
    superseded = _relation(status=RelationStatus.SUPERSEDED)
    draft = _relation(status=RelationStatus.DRAFT)
    for relation in (active, ended, superseded, draft):
        store.save(relation)
    result = store.list_active()
    assert result == (active,)


def test_relation_store_list_active_for_organization_matches_source_or_target() -> None:
    store = InMemoryOrganizationalRelationStore()
    a, b, c = uuid4(), uuid4(), uuid4()
    as_source = _relation(source_organization_id=a, target_organization_id=b)
    as_target = _relation(source_organization_id=b, target_organization_id=a)
    unrelated = _relation(source_organization_id=b, target_organization_id=c)
    for relation in (as_source, as_target, unrelated):
        store.save(relation)
    result = set(store.list_active_for_organization(a))
    assert result == {as_source, as_target}


def test_relation_store_list_active_by_type_filters_correctly() -> None:
    store = InMemoryOrganizationalRelationStore()
    parent_of = _relation(relation_type=RelationType.PARENT_OF)
    affiliated = _relation(relation_type=RelationType.AFFILIATED_WITH)
    for relation in (parent_of, affiliated):
        store.save(relation)
    result = store.list_active_by_type(RelationType.PARENT_OF)
    assert result == (parent_of,)


def test_relation_store_list_all_includes_every_status_ever_saved() -> None:
    """Append-only-by-identity: saving a new version under the same
    relation_id must not erase the store's ability to answer list_all
    with whatever was most recently saved for every id it has seen -
    the store never silently drops history the caller wants to keep."""
    store = InMemoryOrganizationalRelationStore()
    active = _relation(status=RelationStatus.ACTIVE)
    ended = _relation(status=RelationStatus.ENDED)
    store.save(active)
    store.save(ended)
    assert set(store.list_all()) == {active, ended}


def test_relation_store_get_returns_none_for_unknown_id() -> None:
    store = InMemoryOrganizationalRelationStore()
    assert store.get(uuid4()) is None


# ---------------------------------------------------------------------------
# OrganizationalHierarchyOverlapPolicyStore.resolve_for_relation_type
# ---------------------------------------------------------------------------


def _overlap_policy(
    *,
    policy_version: int,
    status: PolicyStatus = PolicyStatus.ACTIVE,
    applicable_relation_types: tuple[RelationType, ...] = (RelationType.PARENT_OF,),
    valid_from: datetime = _NOW - timedelta(days=10),
    valid_until: datetime | None = None,
) -> OrganizationalHierarchyOverlapPolicy:
    return OrganizationalHierarchyOverlapPolicy(
        policy_id=uuid4(),
        policy_version=policy_version,
        applicable_relation_types=applicable_relation_types,
        overlap_permitted=True,
        authorizing_decision_reference=uuid4(),
        status=status,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def test_overlap_policy_store_resolves_highest_version_among_overlapping_candidates() -> None:
    store = InMemoryOrganizationalHierarchyOverlapPolicyStore()
    v1 = _overlap_policy(policy_version=1)
    v2 = _overlap_policy(policy_version=2)
    store.save(v1)
    store.save(v2)
    resolved = store.resolve_for_relation_type(RelationType.PARENT_OF, at=_NOW)
    assert resolved is not None
    assert resolved.policy_version == 2


def test_overlap_policy_store_excludes_non_active_status() -> None:
    store = InMemoryOrganizationalHierarchyOverlapPolicyStore()
    store.save(_overlap_policy(policy_version=1, status=PolicyStatus.DRAFT))
    resolved = store.resolve_for_relation_type(RelationType.PARENT_OF, at=_NOW)
    assert resolved is None


def test_overlap_policy_store_excludes_out_of_window_policy() -> None:
    store = InMemoryOrganizationalHierarchyOverlapPolicyStore()
    store.save(
        _overlap_policy(
            policy_version=1,
            valid_from=_NOW - timedelta(days=30),
            valid_until=_NOW - timedelta(days=1),
        )
    )
    resolved = store.resolve_for_relation_type(RelationType.PARENT_OF, at=_NOW)
    assert resolved is None


def test_overlap_policy_store_excludes_non_applicable_relation_type() -> None:
    store = InMemoryOrganizationalHierarchyOverlapPolicyStore()
    store.save(
        _overlap_policy(policy_version=1, applicable_relation_types=(RelationType.SUBORDINATE_TO,))
    )
    resolved = store.resolve_for_relation_type(RelationType.PARENT_OF, at=_NOW)
    assert resolved is None


# ---------------------------------------------------------------------------
# OrganizationalInheritancePolicyStore.resolve_for_role
# ---------------------------------------------------------------------------


def _inheritance_policy(
    *,
    policy_version: int,
    role_code: str = "kreisvorsitzender",
    status: PolicyStatus = PolicyStatus.ACTIVE,
    inheritance_mode: InheritanceMode = InheritanceMode.ANCESTOR,
    valid_from: datetime = _NOW - timedelta(days=10),
    valid_until: datetime | None = None,
) -> OrganizationalInheritancePolicy:
    return OrganizationalInheritancePolicy(
        policy_id=uuid4(),
        policy_version=policy_version,
        role_code=role_code,
        inheritance_mode=inheritance_mode,
        authorizing_decision_reference=uuid4(),
        status=status,
        valid_from=valid_from,
        valid_until=valid_until,
    )


def test_inheritance_policy_store_resolves_highest_version_for_role() -> None:
    store = InMemoryOrganizationalInheritancePolicyStore()
    v1 = _inheritance_policy(policy_version=1)
    v2 = _inheritance_policy(policy_version=2)
    store.save(v1)
    store.save(v2)
    resolved = store.resolve_for_role("kreisvorsitzender", at=_NOW)
    assert resolved is not None
    assert resolved.policy_version == 2


def test_inheritance_policy_store_excludes_mismatched_role_code() -> None:
    store = InMemoryOrganizationalInheritancePolicyStore()
    store.save(_inheritance_policy(policy_version=1, role_code="landesvorsitzender"))
    resolved = store.resolve_for_role("kreisvorsitzender", at=_NOW)
    assert resolved is None


def test_inheritance_policy_store_excludes_non_active_status() -> None:
    store = InMemoryOrganizationalInheritancePolicyStore()
    store.save(_inheritance_policy(policy_version=1, status=PolicyStatus.DRAFT))
    resolved = store.resolve_for_role("kreisvorsitzender", at=_NOW)
    assert resolved is None


def test_inheritance_policy_store_excludes_out_of_window_policy() -> None:
    store = InMemoryOrganizationalInheritancePolicyStore()
    store.save(
        _inheritance_policy(
            policy_version=1,
            valid_from=_NOW - timedelta(days=30),
            valid_until=_NOW - timedelta(days=1),
        )
    )
    resolved = store.resolve_for_role("kreisvorsitzender", at=_NOW)
    assert resolved is None


# ---------------------------------------------------------------------------
# OrganizationalAuthorityStore
# ---------------------------------------------------------------------------


def _authority(
    *,
    assigned_subject_reference: object = None,
    scope: OrganizationalScope | None = None,
    status: AuthorityStatus = AuthorityStatus.ACTIVE,
    valid_until: datetime | None = None,
) -> OrganizationalAuthority:
    return OrganizationalAuthority(
        authority_id=uuid4(),
        authority_version=1,
        role_code="election_officer",
        scope=scope or organization_scope(uuid4()),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=assigned_subject_reference or uuid4(),  # type: ignore[arg-type]
        valid_from=_NOW - timedelta(days=1),
        status=status,
        policy_version="1.0",
        decision_reference=uuid4(),
        valid_until=valid_until,
        revocation_reason_reference=(
            "no longer required" if status == AuthorityStatus.REVOKED else None
        ),
    )


def test_authority_store_list_active_for_subject_and_scope_matches_both() -> None:
    store = InMemoryOrganizationalAuthorityStore()
    subject = uuid4()
    scope = organization_scope(uuid4())
    matching = _authority(assigned_subject_reference=subject, scope=scope)
    wrong_subject = _authority(scope=scope)
    wrong_scope = _authority(assigned_subject_reference=subject)
    for authority in (matching, wrong_subject, wrong_scope):
        store.save(authority)
    result = store.list_active_for_subject_and_scope(
        assigned_subject_reference=subject, scope=scope, at=_NOW
    )
    assert result == (matching,)


def test_authority_store_list_active_for_subject_and_scope_excludes_expired() -> None:
    store = InMemoryOrganizationalAuthorityStore()
    subject = uuid4()
    scope = organization_scope(uuid4())
    expired = _authority(
        assigned_subject_reference=subject, scope=scope, valid_until=_NOW - timedelta(days=1)
    )
    store.save(expired)
    result = store.list_active_for_subject_and_scope(
        assigned_subject_reference=subject, scope=scope, at=_NOW
    )
    assert result == ()


def test_authority_store_list_active_for_subject_and_scope_excludes_revoked() -> None:
    store = InMemoryOrganizationalAuthorityStore()
    subject = uuid4()
    scope = organization_scope(uuid4())
    revoked = _authority(
        assigned_subject_reference=subject, scope=scope, status=AuthorityStatus.REVOKED
    )
    store.save(revoked)
    result = store.list_active_for_subject_and_scope(
        assigned_subject_reference=subject, scope=scope, at=_NOW
    )
    assert result == ()


def test_authority_store_list_active_for_scope_ignores_subject() -> None:
    store = InMemoryOrganizationalAuthorityStore()
    scope = organization_scope(uuid4())
    first = _authority(scope=scope)
    second = _authority(scope=scope)
    other_scope = _authority()
    for authority in (first, second, other_scope):
        store.save(authority)
    result = set(store.list_active_for_scope(scope, at=_NOW))
    assert result == {first, second}


def test_authority_store_list_all_returns_every_saved_row() -> None:
    store = InMemoryOrganizationalAuthorityStore()
    a = _authority()
    b = _authority(status=AuthorityStatus.REVOKED)
    store.save(a)
    store.save(b)
    assert set(store.list_all()) == {a, b}


# ---------------------------------------------------------------------------
# ScopeDelegationGrantStore.find_usable
# ---------------------------------------------------------------------------


def _grant(
    *,
    delegate_scope: OrganizationalScope | None = None,
    target_scope: OrganizationalScope | None = None,
    action_code: str = "read",
    status: PolicyStatus = PolicyStatus.ACTIVE,
    valid_until: datetime | None = None,
) -> ScopeDelegationGrant:
    return ScopeDelegationGrant(
        grant_id=uuid4(),
        delegate_scope=delegate_scope or organization_scope(uuid4()),
        target_scope=target_scope or organization_scope(uuid4()),
        action_code=action_code,
        authorizing_decision_reference=uuid4(),
        policy_version="1.0",
        valid_from=_NOW - timedelta(days=1),
        valid_until=valid_until,
        status=status,
    )


def test_delegation_grant_store_find_usable_matches_scope_and_action() -> None:
    store = InMemoryScopeDelegationGrantStore()
    delegate = organization_scope(uuid4())
    target = organization_scope(uuid4())
    grant = _grant(delegate_scope=delegate, target_scope=target, action_code="read")
    store.save(grant)
    found = store.find_usable(
        delegate_scope=delegate, target_scope=target, action_code="read", at=_NOW
    )
    assert found == grant


def test_delegation_grant_store_find_usable_excludes_wrong_action_code() -> None:
    store = InMemoryScopeDelegationGrantStore()
    delegate = organization_scope(uuid4())
    target = organization_scope(uuid4())
    store.save(_grant(delegate_scope=delegate, target_scope=target, action_code="read"))
    found = store.find_usable(
        delegate_scope=delegate, target_scope=target, action_code="write", at=_NOW
    )
    assert found is None


def test_delegation_grant_store_find_usable_excludes_expired_grant() -> None:
    store = InMemoryScopeDelegationGrantStore()
    delegate = organization_scope(uuid4())
    target = organization_scope(uuid4())
    store.save(
        _grant(
            delegate_scope=delegate,
            target_scope=target,
            valid_until=_NOW - timedelta(days=1),
        )
    )
    found = store.find_usable(
        delegate_scope=delegate, target_scope=target, action_code="read", at=_NOW
    )
    assert found is None


def test_delegation_grant_store_find_usable_excludes_non_active_status() -> None:
    store = InMemoryScopeDelegationGrantStore()
    delegate = organization_scope(uuid4())
    target = organization_scope(uuid4())
    store.save(_grant(delegate_scope=delegate, target_scope=target, status=PolicyStatus.SUPERSEDED))
    found = store.find_usable(
        delegate_scope=delegate, target_scope=target, action_code="read", at=_NOW
    )
    assert found is None


def test_delegation_grant_store_find_usable_excludes_mismatched_target_scope() -> None:
    store = InMemoryScopeDelegationGrantStore()
    delegate = organization_scope(uuid4())
    store.save(_grant(delegate_scope=delegate, target_scope=organization_scope(uuid4())))
    found = store.find_usable(
        delegate_scope=delegate,
        target_scope=organization_scope(uuid4()),
        action_code="read",
        at=_NOW,
    )
    assert found is None

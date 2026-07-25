"""Storage protocols and in-memory reference adapters for Organization
Service's owned entities (PACK-08 implementation round, canon-0.7.0).

Per this round's own item 20 ("follow the repository's existing reference
implementation pattern... in-memory repositories are acceptable... but
repository interfaces must be explicit; effective-dated queries must be
deterministic; historical records must not be overwritten"): every store
below keeps every version of every record it has ever seen (append-only
by identity + version), so a historical or future-dated query is always
answerable without ever mutating or deleting a past record."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from epd2_organization_service.domain import (
    AuthorityStatus,
    CivicSpace,
    Organization,
    OrganizationalAuthority,
    OrganizationalHierarchyOverlapPolicy,
    OrganizationalInheritancePolicy,
    OrganizationalRelation,
    OrganizationalScope,
    OrganizationalUnit,
    RelationStatus,
    RelationType,
    ScopeDelegationGrant,
    is_effective,
)


class OrganizationStore(Protocol):
    def save(self, organization: Organization) -> None: ...

    def get(self, organization_id: UUID) -> Organization | None: ...

    def list_all(self) -> tuple[Organization, ...]: ...


class InMemoryOrganizationStore:
    def __init__(self) -> None:
        self._organizations: dict[UUID, Organization] = {}

    def save(self, organization: Organization) -> None:
        self._organizations[organization.organization_id] = organization

    def get(self, organization_id: UUID) -> Organization | None:
        return self._organizations.get(organization_id)

    def list_all(self) -> tuple[Organization, ...]:
        return tuple(self._organizations.values())


class OrganizationalUnitStore(Protocol):
    def save(self, unit: OrganizationalUnit) -> None: ...

    def get(self, organizational_unit_id: UUID) -> OrganizationalUnit | None: ...


class InMemoryOrganizationalUnitStore:
    def __init__(self) -> None:
        self._units: dict[UUID, OrganizationalUnit] = {}

    def save(self, unit: OrganizationalUnit) -> None:
        self._units[unit.organizational_unit_id] = unit

    def get(self, organizational_unit_id: UUID) -> OrganizationalUnit | None:
        return self._units.get(organizational_unit_id)


class CivicSpaceStore(Protocol):
    def save(self, space: CivicSpace) -> None: ...

    def get(self, space_id: UUID) -> CivicSpace | None: ...


class InMemoryCivicSpaceStore:
    def __init__(self) -> None:
        self._spaces: dict[UUID, CivicSpace] = {}

    def save(self, space: CivicSpace) -> None:
        self._spaces[space.space_id] = space

    def get(self, space_id: UUID) -> CivicSpace | None:
        return self._spaces.get(space_id)


class OrganizationalRelationStore(Protocol):
    def save(self, relation: OrganizationalRelation) -> None: ...

    def get(self, relation_id: UUID) -> OrganizationalRelation | None: ...

    def list_active(self) -> tuple[OrganizationalRelation, ...]: ...

    def list_active_for_organization(
        self, organization_id: UUID
    ) -> tuple[OrganizationalRelation, ...]: ...

    def list_active_by_type(
        self, relation_type: RelationType
    ) -> tuple[OrganizationalRelation, ...]: ...

    def list_all(self) -> tuple[OrganizationalRelation, ...]: ...


class InMemoryOrganizationalRelationStore:
    def __init__(self) -> None:
        self._relations: dict[UUID, OrganizationalRelation] = {}

    def save(self, relation: OrganizationalRelation) -> None:
        self._relations[relation.relation_id] = relation

    def get(self, relation_id: UUID) -> OrganizationalRelation | None:
        return self._relations.get(relation_id)

    def list_active(self) -> tuple[OrganizationalRelation, ...]:
        return tuple(r for r in self._relations.values() if r.status is RelationStatus.ACTIVE)

    def list_active_for_organization(
        self, organization_id: UUID
    ) -> tuple[OrganizationalRelation, ...]:
        return tuple(
            r
            for r in self.list_active()
            if r.source_organization_id == organization_id
            or r.target_organization_id == organization_id
        )

    def list_active_by_type(
        self, relation_type: RelationType
    ) -> tuple[OrganizationalRelation, ...]:
        return tuple(r for r in self.list_active() if r.relation_type is relation_type)

    def list_all(self) -> tuple[OrganizationalRelation, ...]:
        return tuple(self._relations.values())


class OrganizationalHierarchyOverlapPolicyStore(Protocol):
    def save(self, policy: OrganizationalHierarchyOverlapPolicy) -> None: ...

    def get(self, policy_id: UUID) -> OrganizationalHierarchyOverlapPolicy | None: ...

    def resolve_for_relation_type(
        self, relation_type: RelationType, *, at: datetime
    ) -> OrganizationalHierarchyOverlapPolicy | None: ...


class InMemoryOrganizationalHierarchyOverlapPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, OrganizationalHierarchyOverlapPolicy] = {}

    def save(self, policy: OrganizationalHierarchyOverlapPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: UUID) -> OrganizationalHierarchyOverlapPolicy | None:
        return self._policies.get(policy_id)

    def resolve_for_relation_type(
        self, relation_type: RelationType, *, at: datetime
    ) -> OrganizationalHierarchyOverlapPolicy | None:
        candidates = [
            policy
            for policy in self._policies.values()
            if (
                policy.status.value == "active"
                and relation_type in policy.applicable_relation_types
                and is_effective(policy.valid_from, policy.valid_until, at=at)
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.policy_version)


class OrganizationalInheritancePolicyStore(Protocol):
    def save(self, policy: OrganizationalInheritancePolicy) -> None: ...

    def get(self, policy_id: UUID) -> OrganizationalInheritancePolicy | None: ...

    def resolve_for_role(
        self, role_code: str, *, at: datetime
    ) -> OrganizationalInheritancePolicy | None: ...


class InMemoryOrganizationalInheritancePolicyStore:
    def __init__(self) -> None:
        self._policies: dict[UUID, OrganizationalInheritancePolicy] = {}

    def save(self, policy: OrganizationalInheritancePolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: UUID) -> OrganizationalInheritancePolicy | None:
        return self._policies.get(policy_id)

    def resolve_for_role(
        self, role_code: str, *, at: datetime
    ) -> OrganizationalInheritancePolicy | None:
        candidates = [
            policy
            for policy in self._policies.values()
            if (
                policy.status.value == "active"
                and policy.role_code == role_code
                and is_effective(policy.valid_from, policy.valid_until, at=at)
            )
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.policy_version)


class OrganizationalAuthorityStore(Protocol):
    def save(self, authority: OrganizationalAuthority) -> None: ...

    def get(self, authority_id: UUID) -> OrganizationalAuthority | None: ...

    def list_active_for_subject_and_scope(
        self, *, assigned_subject_reference: UUID, scope: OrganizationalScope, at: datetime
    ) -> tuple[OrganizationalAuthority, ...]: ...

    def list_active_for_scope(
        self, scope: OrganizationalScope, *, at: datetime
    ) -> tuple[OrganizationalAuthority, ...]: ...

    def list_all(self) -> tuple[OrganizationalAuthority, ...]: ...


class InMemoryOrganizationalAuthorityStore:
    def __init__(self) -> None:
        self._authorities: dict[UUID, OrganizationalAuthority] = {}

    def save(self, authority: OrganizationalAuthority) -> None:
        self._authorities[authority.authority_id] = authority

    def get(self, authority_id: UUID) -> OrganizationalAuthority | None:
        return self._authorities.get(authority_id)

    def list_active_for_subject_and_scope(
        self, *, assigned_subject_reference: UUID, scope: OrganizationalScope, at: datetime
    ) -> tuple[OrganizationalAuthority, ...]:
        return tuple(
            a
            for a in self._authorities.values()
            if a.assigned_subject_reference == assigned_subject_reference
            and a.scope.matches(scope)
            and a.status is AuthorityStatus.ACTIVE
            and is_effective(a.valid_from, a.valid_until, at=at)
        )

    def list_active_for_scope(
        self, scope: OrganizationalScope, *, at: datetime
    ) -> tuple[OrganizationalAuthority, ...]:
        return tuple(
            a
            for a in self._authorities.values()
            if a.scope.matches(scope)
            and a.status is AuthorityStatus.ACTIVE
            and is_effective(a.valid_from, a.valid_until, at=at)
        )

    def list_all(self) -> tuple[OrganizationalAuthority, ...]:
        return tuple(self._authorities.values())


class ScopeDelegationGrantStore(Protocol):
    def save(self, grant: ScopeDelegationGrant) -> None: ...

    def get(self, grant_id: UUID) -> ScopeDelegationGrant | None: ...

    def find_usable(
        self,
        *,
        delegate_scope: OrganizationalScope,
        target_scope: OrganizationalScope,
        action_code: str,
        at: datetime,
    ) -> ScopeDelegationGrant | None: ...


class InMemoryScopeDelegationGrantStore:
    def __init__(self) -> None:
        self._grants: dict[UUID, ScopeDelegationGrant] = {}

    def save(self, grant: ScopeDelegationGrant) -> None:
        self._grants[grant.grant_id] = grant

    def get(self, grant_id: UUID) -> ScopeDelegationGrant | None:
        return self._grants.get(grant_id)

    def find_usable(
        self,
        *,
        delegate_scope: OrganizationalScope,
        target_scope: OrganizationalScope,
        action_code: str,
        at: datetime,
    ) -> ScopeDelegationGrant | None:
        for grant in self._grants.values():
            if (
                grant.delegate_scope.matches(delegate_scope)
                and grant.target_scope.matches(target_scope)
                and grant.action_code == action_code
                and grant.is_usable(at=at)
            ):
                return grant
        return None

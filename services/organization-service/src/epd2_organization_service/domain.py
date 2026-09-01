"""Organization & Regional Scope domain model (PACK-08 implementation
round, canon-0.7.0 section 19e; ADR-032 through ADR-037).

Field names below follow `docs/canonical/TZ-00-domain-event-canon.md`
section 19e exactly (the canonical, ADR-037-amended source), not the
CLAUDE-PACK-08 implementation-round request's own re-listed field
suggestions where the two differ - the same reconciliation ADR-037
itself already performed for `OrganizationalAuthority` (canon 19e.15's
own naming note: `role_code`/`scope`, not `authority_type`/four separate
scope fields). Two further reconciliations this module makes, documented
inline where they occur:

- `Organization.status` uses canon 8.1's own four values (`draft`/
  `active`/`restricted`/`archived`); this implementation round's
  "activate/suspend/dissolve" workflow language (section 7/8 of the
  implementation request) maps onto those exact values
  (`suspend` -> `restricted`, `dissolve` -> `archived`) - there is no
  separate `suspended`/`dissolved` status value.
- The role-incompatibility baseline's "election auditor" and "finance
  administrator" are not, themselves, named institutional roles in
  canon 19e.16's exact seven-role list. This module maps "election
  auditor" to `independent_auditor` acting on an election process, and
  "finance administrator"/generic operational decision-making roles to
  `organizational_administrator`/`election_board_member`/
  `election_officer`, per `PAIRWISE_INCOMPATIBLE_ROLES` below - see that
  constant's own docstring.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import replace as dataclasses_replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_organization_service.exceptions import (
    ForbiddenOrganizationTransitionError,
    OrganizationalCycleForbiddenError,
    OrganizationalRelationOverlapError,
    OrganizationSelfAssignmentForbiddenError,
    TemporarySupervisionWindowInvalidError,
    UnknownOrganizationStatusError,
)

# =============================================================================
# Shared effective-dating helpers (canon 19e.9)
# =============================================================================


def _require_tz_aware(value: datetime | None, field_name: str) -> None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def is_effective(valid_from: datetime, valid_until: datetime | None, *, at: datetime) -> bool:
    """Canon 19e.9: `[valid_from, valid_until)` - `at` is covered if
    `valid_from <= at` and (`valid_until` is None or `at < valid_until`).
    A future-dated `valid_from` (`at < valid_from`) is never effective yet,
    even though the record already exists and is queryable."""
    if at < valid_from:
        return False
    return not (valid_until is not None and at >= valid_until)


def windows_overlap(
    a_from: datetime,
    a_until: datetime | None,
    b_from: datetime,
    b_until: datetime | None,
) -> bool:
    """Half-open interval overlap test for two `[valid_from, valid_until)`
    windows (canon 19e.9's overlap-validation rule)."""
    a_end = a_until if a_until is not None else datetime.max.replace(tzinfo=a_from.tzinfo)
    b_end = b_until if b_until is not None else datetime.max.replace(tzinfo=b_from.tzinfo)
    return a_from < b_end and b_from < a_end


# =============================================================================
# Organization (canon 8.1, extended 19e.3) / OrganizationalUnit (19e.5)
# =============================================================================


class OrganizationStatus(StrEnum):
    """Canon 8.1's exact, unchanged four-value status list."""

    DRAFT = "draft"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    ARCHIVED = "archived"


#: Canon 19e.10: create -> draft; activate -> draft->active; suspend ->
#: active->restricted (reversible); dissolve -> active/restricted->archived
#: (irreversible through this workflow).
ORGANIZATION_ALLOWED_TRANSITIONS: frozenset[tuple[OrganizationStatus, OrganizationStatus]] = (
    frozenset(
        {
            (OrganizationStatus.DRAFT, OrganizationStatus.ACTIVE),
            (OrganizationStatus.ACTIVE, OrganizationStatus.RESTRICTED),
            (OrganizationStatus.RESTRICTED, OrganizationStatus.ACTIVE),
            (OrganizationStatus.ACTIVE, OrganizationStatus.ARCHIVED),
            (OrganizationStatus.RESTRICTED, OrganizationStatus.ARCHIVED),
        }
    )
)


def parse_organization_status(value: str) -> OrganizationStatus:
    try:
        return OrganizationStatus(value)
    except ValueError as exc:
        raise UnknownOrganizationStatusError(f"unknown organization status: {value!r}") from exc


def assert_organization_transition_allowed(
    current: OrganizationStatus, target: OrganizationStatus
) -> None:
    if (current, target) not in ORGANIZATION_ALLOWED_TRANSITIONS:
        raise ForbiddenOrganizationTransitionError(
            f"organization transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: Canon 19e.3's open, extensible `organization_profile` taxonomy - at
#: least these named profiles are supported at launch (task section 5).
#: Extended at the repository level, never by a canon edit (mirrors
#: `identity_scheme`'s own established open-string-extensible pattern).
KNOWN_ORGANIZATION_PROFILES: frozenset[str] = frozenset(
    {
        "bund",
        "landesverband",
        "kreisverband",
        "bezirksverband",
        "ortsverband",
        "ortsgruppe",
        "non_territorial_unit",
        "cross_regional_unit",
        "special_unit",
        "working_group",
    }
)


@dataclass(frozen=True, slots=True)
class Organization:
    """Canon 8.1's six existing fields, unchanged, plus 19e.3's six new
    additive fields. `parent_reference` is never authoritative (19e.4) -
    it is recomputed by `application.recompute_parent_reference`, never
    set directly by a caller; this dataclass accepts it only so a
    recomputed value can be stored back onto an immutable snapshot."""

    organization_id: UUID
    name: str
    legal_operator: str
    organization_type: str
    status: OrganizationStatus
    default_policy_version: str
    organization_profile: str
    effective_from: datetime
    effective_until: datetime | None = None
    dissolved_at: datetime | None = None
    successor_reference: UUID | None = None
    parent_reference: UUID | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.legal_operator:
            raise ValueError("legal_operator must not be empty")
        if not self.organization_type:
            raise ValueError("organization_type must not be empty")
        if not self.organization_profile:
            raise ValueError("organization_profile must not be empty")
        _require_tz_aware(self.effective_from, "effective_from")
        _require_tz_aware(self.effective_until, "effective_until")
        _require_tz_aware(self.dissolved_at, "dissolved_at")
        if self.status is OrganizationStatus.ARCHIVED and self.dissolved_at is None:
            raise ValueError("dissolved_at is required once status=archived")

    def with_status(
        self,
        new_status: OrganizationStatus,
        *,
        dissolved_at: datetime | None = None,
    ) -> Organization:
        assert_organization_transition_allowed(self.status, new_status)
        return dataclasses_replace(
            self,
            status=new_status,
            dissolved_at=dissolved_at if dissolved_at is not None else self.dissolved_at,
        )

    def with_parent_reference(self, parent_reference: UUID | None) -> Organization:
        """The ONLY sanctioned way `parent_reference` ever changes - always
        called from `application.recompute_parent_reference`, never from a
        direct command (19e.4)."""
        return dataclasses_replace(self, parent_reference=parent_reference)

    def with_successor_reference(self, successor_reference: UUID) -> Organization:
        return dataclasses_replace(self, successor_reference=successor_reference)

    def with_rename(self, new_name: str) -> Organization:
        """Canon 19e.10: renaming is additive/versioned at the read-model
        level (the caller is expected to retain the prior `Organization`
        snapshot for historical queryability, section 19e.9); renaming
        alone never touches `organization_id`, relations, or authority."""
        if not new_name:
            raise ValueError("new_name must not be empty")
        return dataclasses_replace(self, name=new_name)


@dataclass(frozen=True, slots=True)
class OrganizationalUnit:
    """Canon 19e.5: a lighter-weight node for subordinate structures not
    themselves a full `Organization` in the legal/statutory sense.
    Modeled as its own entity (per this implementation round's explicit
    field list) sharing `Organization`'s status/lifecycle machinery and
    service ownership - never a parallel hierarchy."""

    organizational_unit_id: UUID
    owning_organization_id: UUID
    unit_type: str
    status: OrganizationStatus
    valid_from: datetime
    valid_until: datetime | None = None
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.unit_type:
            raise ValueError("unit_type must not be empty")
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")
        _require_tz_aware(self.recorded_at, "recorded_at")

    def with_status(self, new_status: OrganizationStatus) -> OrganizationalUnit:
        assert_organization_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)


# =============================================================================
# CivicSpace (canon 8.2, unchanged - 19e.6). First real implementation.
# =============================================================================


class CivicSpaceStatus(StrEnum):
    """Canon 8.2's exact, unchanged five-value status list."""

    DRAFT = "draft"
    ACTIVE = "active"
    READ_ONLY = "read_only"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


CIVIC_SPACE_ALLOWED_TRANSITIONS: frozenset[tuple[CivicSpaceStatus, CivicSpaceStatus]] = frozenset(
    {
        (CivicSpaceStatus.DRAFT, CivicSpaceStatus.ACTIVE),
        (CivicSpaceStatus.ACTIVE, CivicSpaceStatus.READ_ONLY),
        (CivicSpaceStatus.ACTIVE, CivicSpaceStatus.SUSPENDED),
        (CivicSpaceStatus.SUSPENDED, CivicSpaceStatus.ACTIVE),
        (CivicSpaceStatus.READ_ONLY, CivicSpaceStatus.ACTIVE),
        (CivicSpaceStatus.ACTIVE, CivicSpaceStatus.ARCHIVED),
        (CivicSpaceStatus.SUSPENDED, CivicSpaceStatus.ARCHIVED),
        (CivicSpaceStatus.READ_ONLY, CivicSpaceStatus.ARCHIVED),
    }
)


def parse_civic_space_status(value: str) -> CivicSpaceStatus:
    try:
        return CivicSpaceStatus(value)
    except ValueError as exc:
        raise UnknownOrganizationStatusError(f"unknown civic space status: {value!r}") from exc


def assert_civic_space_transition_allowed(
    current: CivicSpaceStatus, target: CivicSpaceStatus
) -> None:
    if (current, target) not in CIVIC_SPACE_ALLOWED_TRANSITIONS:
        raise ForbiddenOrganizationTransitionError(
            f"civic space transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class CivicSpace:
    """Canon 8.2's exact, unchanged seven-field set."""

    space_id: UUID
    organization_id: UUID
    name: str
    space_type: str
    visibility: str
    participation_policy_id: UUID | None
    status: CivicSpaceStatus

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.space_type:
            raise ValueError("space_type must not be empty")
        if not self.visibility:
            raise ValueError("visibility must not be empty")

    def with_status(self, new_status: CivicSpaceStatus) -> CivicSpace:
        assert_civic_space_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)


# =============================================================================
# OrganizationalRelation (canon 19e.7) - multiple typed directed graphs.
# =============================================================================


class RelationType(StrEnum):
    """Canon 19e.7's nine relation types, open-extensible within each
    category (a new category requires an ADR)."""

    PARENT_OF = "parent_of"
    SUBORDINATE_TO = "subordinate_to"
    AFFILIATED_WITH = "affiliated_with"
    SUCCESSOR_OF = "successor_of"
    MERGED_INTO = "merged_into"
    SPLIT_FROM = "split_from"
    TEMPORARY_SUPERVISION_BY = "temporary_supervision_by"
    OPERATES_WITHIN = "operates_within"
    PARTICIPATES_IN = "participates_in"


class RelationCategory(StrEnum):
    HIERARCHY = "hierarchy"
    CONTINUITY = "continuity"
    COOPERATION = "cooperation"


#: relation_category is derived from relation_type, never set
#: independently (canon 19e.7).
RELATION_CATEGORY_BY_TYPE: Mapping[RelationType, RelationCategory] = {
    RelationType.PARENT_OF: RelationCategory.HIERARCHY,
    RelationType.SUBORDINATE_TO: RelationCategory.HIERARCHY,
    RelationType.SUCCESSOR_OF: RelationCategory.CONTINUITY,
    RelationType.MERGED_INTO: RelationCategory.CONTINUITY,
    RelationType.SPLIT_FROM: RelationCategory.CONTINUITY,
    RelationType.AFFILIATED_WITH: RelationCategory.COOPERATION,
    RelationType.TEMPORARY_SUPERVISION_BY: RelationCategory.COOPERATION,
    RelationType.OPERATES_WITHIN: RelationCategory.COOPERATION,
    RelationType.PARTICIPATES_IN: RelationCategory.COOPERATION,
}

#: Cycles are structurally forbidden, without exception, for these two
#: relation types (canon 19e.7).
HIERARCHY_RELATION_TYPES: frozenset[RelationType] = frozenset(
    {RelationType.PARENT_OF, RelationType.SUBORDINATE_TO}
)

#: `temporary_supervision_by` may not form a cycle (a node may not
#: supervise itself, directly or transitively) even though it is a
#: cooperation-category relation type (canon 19e.7).
CYCLE_CHECKED_COOPERATION_TYPES: frozenset[RelationType] = frozenset(
    {RelationType.TEMPORARY_SUPERVISION_BY}
)


def relation_category_for(relation_type: RelationType) -> RelationCategory:
    return RELATION_CATEGORY_BY_TYPE[relation_type]


class RelationStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ENDED = "ended"


RELATION_ALLOWED_TRANSITIONS: frozenset[tuple[RelationStatus, RelationStatus]] = frozenset(
    {
        (RelationStatus.DRAFT, RelationStatus.ACTIVE),
        (RelationStatus.ACTIVE, RelationStatus.SUPERSEDED),
        (RelationStatus.ACTIVE, RelationStatus.ENDED),
    }
)


def assert_relation_transition_allowed(current: RelationStatus, target: RelationStatus) -> None:
    if (current, target) not in RELATION_ALLOWED_TRANSITIONS:
        raise ForbiddenOrganizationTransitionError(
            f"relation transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class OrganizationalRelation:
    """Canon 19e.7's exact field set."""

    relation_id: UUID
    relation_version: int
    relation_type: RelationType
    source_organization_id: UUID
    target_organization_id: UUID
    status: RelationStatus
    valid_from: datetime
    valid_until: datetime | None = None
    recorded_at: datetime | None = None
    supersedes_relation_id: UUID | None = None
    authorizing_decision_reference: UUID | None = None

    @property
    def relation_category(self) -> RelationCategory:
        return relation_category_for(self.relation_type)

    def __post_init__(self) -> None:
        if self.relation_version < 1:
            raise ValueError("relation_version must be >= 1")
        if self.source_organization_id == self.target_organization_id:
            raise OrganizationalCycleForbiddenError(
                "a relation may never target its own source_organization_id"
            )
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")
        _require_tz_aware(self.recorded_at, "recorded_at")
        if self.relation_type is RelationType.TEMPORARY_SUPERVISION_BY and self.valid_until is None:
            raise TemporarySupervisionWindowInvalidError(
                "temporary_supervision_by requires a mandatory valid_until "
                "(canon 19e.14) - open-ended supervision is forbidden"
            )

    def with_status(self, new_status: RelationStatus) -> OrganizationalRelation:
        assert_relation_transition_allowed(self.status, new_status)
        return dataclasses_replace(self, status=new_status)

    def with_valid_until(self, valid_until: datetime) -> OrganizationalRelation:
        """Ends an active relation by setting `valid_until` (never an
        in-place edit of any other field, canon 19e.9/19e.10)."""
        return dataclasses_replace(self, valid_until=valid_until, status=RelationStatus.ENDED)


#: Canon 19e.14: temporary supervision's default maximum duration.
TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS = 90


def assert_temporary_supervision_window_valid(
    valid_from: datetime,
    valid_until: datetime | None,
    *,
    max_days: int = TEMPORARY_SUPERVISION_DEFAULT_MAX_DAYS,
) -> None:
    """Canon 19e.14: `valid_from`/`valid_until` are both mandatory for
    `temporary_supervision_by`; the window may not exceed `max_days`
    (default 90; a future legal review may set a narrower, never wider,
    limit for a specific organizational form - the `max_days` parameter
    is exactly that narrowing hook)."""
    if valid_until is None:
        raise TemporarySupervisionWindowInvalidError(
            "temporary_supervision_by requires a mandatory valid_until - "
            "open-ended supervision is forbidden (canon 19e.14)"
        )
    if valid_until <= valid_from:
        raise TemporarySupervisionWindowInvalidError("valid_until must be after valid_from")
    if valid_until - valid_from > timedelta(days=max_days):
        raise TemporarySupervisionWindowInvalidError(
            f"temporary supervision window exceeds the maximum duration of {max_days} days "
            "(canon 19e.14)"
        )


def would_create_hierarchy_cycle(
    existing_edges: Iterable[tuple[UUID, UUID, RelationType]],
    *,
    source_organization_id: UUID,
    target_organization_id: UUID,
    relation_type: RelationType,
) -> bool:
    """Canon 19e.7: cycles are forbidden, without exception, for
    `parent_of`/`subordinate_to`. `existing_edges` is every currently
    active hierarchy-category edge as `(source, target, relation_type)`.
    Normalizes every edge (existing + candidate) to `(parent, child)` and
    checks whether `parent` is already reachable from `child` - i.e.
    whether adding the candidate edge would make an ancestor its own
    descendant."""
    if relation_type not in HIERARCHY_RELATION_TYPES:
        return False

    def _normalize(source: UUID, target: UUID, rel_type: RelationType) -> tuple[UUID, UUID]:
        # parent_of: source is parent, target is child.
        # subordinate_to: source is child, target is parent.
        if rel_type is RelationType.PARENT_OF:
            return source, target
        return target, source

    parent, child = _normalize(source_organization_id, target_organization_id, relation_type)

    # Build child -> {parents} adjacency from existing hierarchy edges.
    parents_of: dict[UUID, set[UUID]] = {}
    for edge_source, edge_target, edge_type in existing_edges:
        if edge_type not in HIERARCHY_RELATION_TYPES:
            continue
        edge_parent, edge_child = _normalize(edge_source, edge_target, edge_type)
        parents_of.setdefault(edge_child, set()).add(edge_parent)

    # Cycle exists if `child` is already an ancestor of `parent`, i.e. if
    # `parent` can reach `child` by walking up its own existing parent
    # edges - or if child == parent outright. (Walking up from `parent`
    # and asking "do we ever reach `child`?" is the correct direction:
    # it detects that `child` already transitively parents `parent`,
    # which is exactly what the candidate edge `parent -> child` would
    # turn into a loop.)
    if parent == child:
        return True
    visited: set[UUID] = set()
    frontier = [parent]
    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        for candidate_ancestor in parents_of.get(node, ()):
            if candidate_ancestor == child:
                return True
            frontier.append(candidate_ancestor)
    return False


def would_create_supervision_cycle(
    existing_edges: Iterable[tuple[UUID, UUID]],
    *,
    supervisor_organization_id: UUID,
    supervised_organization_id: UUID,
) -> bool:
    """Canon 19e.7: `temporary_supervision_by` may not form a cycle (a
    node may not supervise itself, directly or transitively).
    `existing_edges` is every currently active
    `(supervisor, supervised)` pair."""
    if supervisor_organization_id == supervised_organization_id:
        return True
    supervised_by: dict[UUID, set[UUID]] = {}
    for supervisor, supervised in existing_edges:
        supervised_by.setdefault(supervised, set()).add(supervisor)
    visited: set[UUID] = set()
    frontier = [supervisor_organization_id]
    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        for upstream_supervisor in supervised_by.get(node, ()):
            if upstream_supervisor == supervised_organization_id:
                return True
            frontier.append(upstream_supervisor)
    return False


def assert_no_unpermitted_hierarchy_overlap(
    existing_active_edges: Sequence[tuple[UUID, UUID, RelationType, datetime, datetime | None]],
    *,
    source_organization_id: UUID,
    target_organization_id: UUID,
    relation_type: RelationType,
    valid_from: datetime,
    valid_until: datetime | None,
    overlap_permitted: bool,
) -> None:
    """Canon 19e.7/19e.9: a new hierarchy-category edge whose
    `[valid_from, valid_until)` window overlaps an existing active edge
    asserting a *different* parent for the same child (or a second
    concurrent child for the same parent-shaped role) is rejected unless
    an `OrganizationalHierarchyOverlapPolicy` explicitly permits overlap
    for these relation types (`overlap_permitted=True`, resolved by the
    caller against the policy store before calling this function)."""
    if relation_type not in HIERARCHY_RELATION_TYPES or overlap_permitted:
        return
    for edge_source, edge_target, edge_type, edge_from, edge_until in existing_active_edges:
        if edge_type not in HIERARCHY_RELATION_TYPES:
            continue
        # Same "child" node contradictorily claimed by two different
        # parent-shaped edges at overlapping times.
        same_child = edge_type is relation_type and (
            (relation_type is RelationType.PARENT_OF and edge_target == target_organization_id)
            or (
                relation_type is RelationType.SUBORDINATE_TO
                and edge_source == source_organization_id
            )
        )
        if same_child and windows_overlap(valid_from, valid_until, edge_from, edge_until):
            raise OrganizationalRelationOverlapError(
                "overlapping hierarchy-category relation without a permitting "
                "OrganizationalHierarchyOverlapPolicy (canon 19e.7/19e.8)"
            )


# =============================================================================
# OrganizationalHierarchyOverlapPolicy (canon 19e.8)
# =============================================================================


class PolicyStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class OrganizationalHierarchyOverlapPolicy:
    """Canon 19e.8's minimum fields."""

    policy_id: UUID
    policy_version: int
    applicable_relation_types: tuple[RelationType, ...]
    overlap_permitted: bool
    authorizing_decision_reference: UUID
    status: PolicyStatus
    valid_from: datetime
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if not self.applicable_relation_types:
            raise ValueError("applicable_relation_types must not be empty")
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")


# =============================================================================
# OrganizationalInheritancePolicy (canon 19e.13)
# =============================================================================


class InheritanceMode(StrEnum):
    ANCESTOR = "ancestor"
    DESCENDANT = "descendant"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class OrganizationalInheritancePolicy:
    """Canon 19e.13's minimum fields. Owned exclusively by the
    Organization & Regional Scope domain; consuming domains may apply
    stricter rules but may never broaden the authority it grants."""

    policy_id: UUID
    policy_version: int
    role_code: str
    inheritance_mode: InheritanceMode
    authorizing_decision_reference: UUID
    status: PolicyStatus
    valid_from: datetime
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        if self.policy_version < 1:
            raise ValueError("policy_version must be >= 1")
        if not self.role_code:
            raise ValueError("role_code must not be empty")
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")

    def allows(self, mode: InheritanceMode) -> bool:
        return self.inheritance_mode is InheritanceMode.BOTH or self.inheritance_mode is mode


# =============================================================================
# OrganizationalScope (canon 19e.11) - reusable value shape, not owned.
# =============================================================================


class ScopeType(StrEnum):
    """Canon 19e.11: an `OrganizationalScope` always names exactly which
    of the four section 19e.2 concepts it references."""

    ORGANIZATION_SCOPE = "organization_scope"
    JURISDICTION_SCOPE = "jurisdiction_scope"
    CIVIC_SPACE_SCOPE = "civic_space_scope"
    PROCESS_SCOPE = "process_scope"


@dataclass(frozen=True, slots=True)
class OrganizationalScope:
    """Canon 19e.11's reusable, opaque scope-reference value shape.
    `scope_reference` is an opaque string (e.g. an `organization_id`'s
    string form, a jurisdiction code, a `space_id`'s string form, or an
    opaque `scope_type:scope_id` process-local pair) - never dereferenced
    by this type itself; only the owning domain's application layer
    resolves its meaning."""

    scope_type: ScopeType
    scope_reference: str
    owning_domain: str = "organization-service"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    policy_version: str | None = None

    def __post_init__(self) -> None:
        if not self.scope_reference:
            raise ValueError("scope_reference must not be empty")
        if not self.owning_domain:
            raise ValueError("owning_domain must not be empty")
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")

    def matches(self, other: OrganizationalScope) -> bool:
        """Exact-scope match (section 19e.12 mode 1)."""
        return self.scope_type == other.scope_type and self.scope_reference == other.scope_reference


def organization_scope(organization_id: UUID) -> OrganizationalScope:
    return OrganizationalScope(
        scope_type=ScopeType.ORGANIZATION_SCOPE, scope_reference=str(organization_id)
    )


# =============================================================================
# OrganizationalAuthority (canon 19e.15)
# =============================================================================


class InstitutionalRole(StrEnum):
    """Canon 19e.16's minimum seven named institutional roles. `role_code`
    itself remains an open string (new roles may be added by
    configuration + ADR review, canon 19e.15); this enum is the known,
    canonically-named subset the incompatibility baseline (19e.16)
    reasons about."""

    DPO = "dpo"
    ELECTION_BOARD_MEMBER = "election_board_member"
    ELECTION_OFFICER = "election_officer"
    INDEPENDENT_AUDITOR = "independent_auditor"
    FINANCE_AUDITOR = "finance_auditor"
    PARTY_ARBITRATOR = "party_arbitrator"
    ORGANIZATIONAL_ADMINISTRATOR = "organizational_administrator"


KNOWN_INSTITUTIONAL_ROLES: frozenset[str] = frozenset(role.value for role in InstitutionalRole)

#: Section 19e.16's minimum baseline incompatibility matrix, version 1.0
#: (versioned and extensible per that section's own closing rule - a
#: future legal review may add pairs, i.e. make this stricter, never
#: remove a pair). Each entry is an unordered pair of `role_code` values
#: that may never both be held, active, by the SAME `assigned_subject_
#: reference`, in the SAME `OrganizationalScope`, at the SAME time.
#:
#: Reconciliation note: canon 19e.16's own text names "election auditor"
#: (rule 1) and "finance administrator" (rule 3), neither of which is one
#: of the seven canonically-named roles. This module maps "election
#: auditor" to `independent_auditor` (the canonical role for
#: verification/read-only audit authority, applied here to an election
#: process) and "finance administrator" to `organizational_administrator`
#: (the canonical role for scope-limited administrative authority,
#: applied here to financial administration) - the same kind of
#: implementation-level reconciliation ADR-037 itself performed for
#: `OrganizationalAuthority`'s own field names.
ROLE_INCOMPATIBILITY_BASELINE_VERSION = "1.0"
PAIRWISE_INCOMPATIBLE_ROLES: frozenset[frozenset[str]] = frozenset(
    {
        # Rule 1: election officer <-> election auditor (independent_auditor).
        frozenset({InstitutionalRole.ELECTION_OFFICER, InstitutionalRole.INDEPENDENT_AUDITOR}),
        # Rule 3: finance auditor <-> finance administrator
        # (organizational_administrator).
        frozenset(
            {InstitutionalRole.FINANCE_AUDITOR, InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR}
        ),
        # Rule 4: independent auditor cannot audit actions they performed
        # or approved - modeled as incompatibility with every operational
        # decision-making role in the same scope.
        frozenset({InstitutionalRole.INDEPENDENT_AUDITOR, InstitutionalRole.ELECTION_BOARD_MEMBER}),
        frozenset(
            {
                InstitutionalRole.INDEPENDENT_AUDITOR,
                InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR,
            }
        ),
        # Rule 5: party arbitrator cannot hold an operational role in the
        # affected organization.
        frozenset(
            {InstitutionalRole.PARTY_ARBITRATOR, InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR}
        ),
        frozenset({InstitutionalRole.PARTY_ARBITRATOR, InstitutionalRole.ELECTION_BOARD_MEMBER}),
        frozenset({InstitutionalRole.PARTY_ARBITRATOR, InstitutionalRole.ELECTION_OFFICER}),
        frozenset({InstitutionalRole.PARTY_ARBITRATOR, InstitutionalRole.FINANCE_AUDITOR}),
        # Rule 7: DPO procedural independence must be preserved from
        # administrative decision-making.
        frozenset({InstitutionalRole.DPO, InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR}),
    }
)


def find_role_incompatibility(
    existing_role_codes: Iterable[str], candidate_role_code: str
) -> str | None:
    """Canon 19e.16: returns the conflicting `role_code`, if
    `candidate_role_code` may never be combined with any of
    `existing_role_codes` (already scoped by the caller to the same
    `assigned_subject_reference` + same `OrganizationalScope` + all
    currently active). Returns `None` if no baseline pair matches -
    unknown/non-canonical role codes never conflict under this baseline
    (extensible: a future version may add pairs involving them)."""
    for existing_code in existing_role_codes:
        if frozenset({existing_code, candidate_role_code}) in PAIRWISE_INCOMPATIBLE_ROLES:
            return existing_code
    return None


class AuthorityStatus(StrEnum):
    """Canon 19e.15's `status` field. `PROPOSED` supports 19e.17 rule 6
    (proposal and activation separated where dual control is required)."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


AUTHORITY_ALLOWED_TRANSITIONS: frozenset[tuple[AuthorityStatus, AuthorityStatus]] = frozenset(
    {
        (AuthorityStatus.PROPOSED, AuthorityStatus.ACTIVE),
        (AuthorityStatus.PROPOSED, AuthorityStatus.REVOKED),
        (AuthorityStatus.ACTIVE, AuthorityStatus.SUSPENDED),
        (AuthorityStatus.ACTIVE, AuthorityStatus.REVOKED),
        (AuthorityStatus.ACTIVE, AuthorityStatus.EXPIRED),
        (AuthorityStatus.SUSPENDED, AuthorityStatus.ACTIVE),
        (AuthorityStatus.SUSPENDED, AuthorityStatus.REVOKED),
        (AuthorityStatus.SUSPENDED, AuthorityStatus.EXPIRED),
    }
)


def assert_authority_transition_allowed(current: AuthorityStatus, target: AuthorityStatus) -> None:
    if (current, target) not in AUTHORITY_ALLOWED_TRANSITIONS:
        raise ForbiddenOrganizationTransitionError(
            f"authority transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class OrganizationalAuthority:
    """Canon 19e.15's exact field set."""

    authority_id: UUID
    authority_version: int
    role_code: str
    scope: OrganizationalScope
    appointing_authority_reference: UUID
    assigned_subject_reference: UUID
    valid_from: datetime
    status: AuthorityStatus
    policy_version: str
    decision_reference: UUID
    audit_reference: UUID | None = None
    valid_until: datetime | None = None
    revocation_reason_reference: str | None = None
    grants_procedural_authority: bool = False
    grants_data_access: bool = False

    def __post_init__(self) -> None:
        if self.authority_version < 1:
            raise ValueError("authority_version must be >= 1")
        if not self.role_code:
            raise ValueError("role_code must not be empty")
        if self.appointing_authority_reference == self.assigned_subject_reference:
            raise OrganizationSelfAssignmentForbiddenError(
                "appointing_authority_reference must never equal assigned_subject_reference "
                "(canon 19e.16 rule 6 / 19e.17 rule 4)"
            )
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")
        if self.status is AuthorityStatus.REVOKED and not self.revocation_reason_reference:
            raise ValueError("revocation_reason_reference is required once status=revoked")

    def is_usable(self, *, at: datetime) -> bool:
        """Canon 19e.17 rule 7: expired, revoked, or suspended authority
        cannot be used."""
        if self.status is not AuthorityStatus.ACTIVE:
            return False
        return is_effective(self.valid_from, self.valid_until, at=at)

    def with_status(
        self,
        new_status: AuthorityStatus,
        *,
        revocation_reason_reference: str | None = None,
    ) -> OrganizationalAuthority:
        assert_authority_transition_allowed(self.status, new_status)
        return dataclasses_replace(
            self,
            status=new_status,
            revocation_reason_reference=(
                revocation_reason_reference
                if revocation_reason_reference is not None
                else self.revocation_reason_reference
            ),
        )


# =============================================================================
# Regional scope authorization result (canon 19e.12)
# =============================================================================


class AccessMode(StrEnum):
    """Canon 19e.12's six explicit access modes."""

    EXACT_SCOPE = "exact_scope"
    ANCESTOR_SCOPE = "ancestor_scope"
    DESCENDANT_SCOPE = "descendant_scope"
    DELEGATED_CROSS_SCOPE = "delegated_cross_scope"
    TEMPORARY_SUPERVISION = "temporary_supervision"
    INSTITUTIONAL_OVERSIGHT_WITHOUT_DATA_ACCESS = "institutional_oversight_without_data_access"


@dataclass(frozen=True, slots=True)
class RegionalScopeAccessDecision:
    """The narrow, atomic result `check_regional_scope_access` returns -
    never more than this (section 12's privacy/minimization rules)."""

    allowed: bool
    reason_code: str
    evaluated_scope: OrganizationalScope
    policy_version: str | None
    effective_time: datetime
    mode: AccessMode | None = None
    audit_reference: UUID | None = None


# =============================================================================
# Scope delegation grant - reference-implementation support for section
# 19e.12 mode 4 ("explicitly delegated cross-scope access"). Canon names
# the requirement (a time-bounded, purpose-recorded delegation record)
# without fixing a dedicated entity name; this module introduces the
# minimal shape needed to implement the mode concretely, owned by
# organization-service like everything else in this file.
# =============================================================================


@dataclass(frozen=True, slots=True)
class ScopeDelegationGrant:
    grant_id: UUID
    delegate_scope: OrganizationalScope
    target_scope: OrganizationalScope
    action_code: str
    authorizing_decision_reference: UUID
    policy_version: str
    valid_from: datetime
    valid_until: datetime | None = None
    status: PolicyStatus = PolicyStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.action_code:
            raise ValueError("action_code must not be empty")
        _require_tz_aware(self.valid_from, "valid_from")
        _require_tz_aware(self.valid_until, "valid_until")

    def is_usable(self, *, at: datetime) -> bool:
        return self.status is PolicyStatus.ACTIVE and is_effective(
            self.valid_from, self.valid_until, at=at
        )

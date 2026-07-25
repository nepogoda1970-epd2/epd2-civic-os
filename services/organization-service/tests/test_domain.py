"""Domain-level tests for Organization Service (PACK-08 implementation
round). Covers this round's own task section 24 requirements: valid
creation, invalid lifecycle transitions, cycle/overlap detection,
role-incompatibility baseline, and temporary-supervision window
validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from epd2_organization_service.domain import (
    AuthorityStatus,
    CivicSpace,
    CivicSpaceStatus,
    InstitutionalRole,
    Organization,
    OrganizationalAuthority,
    OrganizationalRelation,
    OrganizationalScope,
    OrganizationStatus,
    RelationStatus,
    RelationType,
    ScopeType,
    assert_organization_transition_allowed,
    assert_temporary_supervision_window_valid,
    find_role_incompatibility,
    is_effective,
    organization_scope,
    windows_overlap,
    would_create_hierarchy_cycle,
    would_create_supervision_cycle,
)
from epd2_organization_service.exceptions import (
    ForbiddenOrganizationTransitionError,
    OrganizationalCycleForbiddenError,
    OrganizationSelfAssignmentForbiddenError,
    TemporarySupervisionWindowInvalidError,
)

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = datetime(2026, 6, 1, tzinfo=UTC)


def _organization(**overrides: object) -> Organization:
    defaults = dict(
        organization_id=uuid4(),
        name="Kreisverband Beispiel",
        legal_operator="Beispiel e.V.",
        organization_type="party_unit",
        status=OrganizationStatus.DRAFT,
        default_policy_version="1.0",
        organization_profile="kreisverband",
        effective_from=T0,
    )
    defaults.update(overrides)
    return Organization(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Organization: valid creation / lifecycle transitions
# ---------------------------------------------------------------------------


def test_valid_organization_creation() -> None:
    organization = _organization()
    assert organization.status is OrganizationStatus.DRAFT
    assert organization.parent_reference is None


def test_organization_requires_dissolved_at_once_archived() -> None:
    with pytest.raises(ValueError):
        _organization(status=OrganizationStatus.ARCHIVED)


@pytest.mark.parametrize(
    "current,target",
    [
        (OrganizationStatus.DRAFT, OrganizationStatus.ACTIVE),
        (OrganizationStatus.ACTIVE, OrganizationStatus.RESTRICTED),
        (OrganizationStatus.RESTRICTED, OrganizationStatus.ACTIVE),
        (OrganizationStatus.ACTIVE, OrganizationStatus.ARCHIVED),
        (OrganizationStatus.RESTRICTED, OrganizationStatus.ARCHIVED),
    ],
)
def test_allowed_organization_transitions(
    current: OrganizationStatus, target: OrganizationStatus
) -> None:
    assert_organization_transition_allowed(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        (OrganizationStatus.DRAFT, OrganizationStatus.RESTRICTED),
        (OrganizationStatus.DRAFT, OrganizationStatus.ARCHIVED),
        (OrganizationStatus.ARCHIVED, OrganizationStatus.ACTIVE),
        (OrganizationStatus.ARCHIVED, OrganizationStatus.RESTRICTED),
    ],
)
def test_forbidden_organization_transitions(
    current: OrganizationStatus, target: OrganizationStatus
) -> None:
    with pytest.raises(ForbiddenOrganizationTransitionError):
        assert_organization_transition_allowed(current, target)


def test_archived_organization_never_reactivates() -> None:
    """Canon 19e.10: a dissolved organization is never silently
    reactivated - only a new node, optionally successor-linked, continues
    its work."""
    organization = _organization(status=OrganizationStatus.ARCHIVED, dissolved_at=T1)
    with pytest.raises(ForbiddenOrganizationTransitionError):
        organization.with_status(OrganizationStatus.ACTIVE)


# ---------------------------------------------------------------------------
# Effective dating: historical / future-dated / supersession
# ---------------------------------------------------------------------------


def test_is_effective_current_state() -> None:
    assert is_effective(T0, None, at=T1)
    assert not is_effective(T0, None, at=T0 - timedelta(days=1))


def test_is_effective_future_dated_not_yet_effective() -> None:
    """Canon 19e.9: a future-dated valid_from is not yet effective for
    scope-authorization purposes, even though the record already exists."""
    future_from = T1 + timedelta(days=30)
    assert not is_effective(future_from, None, at=T1)
    assert is_effective(future_from, None, at=future_from + timedelta(days=1))


def test_is_effective_historical_window_closed() -> None:
    assert is_effective(T0, T1, at=T0 + timedelta(days=1))
    assert not is_effective(T0, T1, at=T1)  # half-open: valid_until excluded


def test_windows_overlap_detects_conflicting_ranges() -> None:
    assert windows_overlap(T0, T1, T0 + timedelta(days=10), None)
    assert not windows_overlap(T0, T1, T1, None)


def test_supersession_never_mutates_prior_record() -> None:
    """A correction is always a new version, never an in-place edit -
    the prior Organization snapshot remains untouched."""
    original = _organization(name="Alter Name")
    renamed = original.with_rename("Neuer Name")
    assert original.name == "Alter Name"
    assert renamed.name == "Neuer Name"
    assert renamed.organization_id == original.organization_id


# ---------------------------------------------------------------------------
# CivicSpace
# ---------------------------------------------------------------------------


def test_civic_space_valid_creation_and_lifecycle() -> None:
    space = CivicSpace(
        space_id=uuid4(),
        organization_id=uuid4(),
        name="Bundesweite Mitgliederversammlung",
        space_type="assembly",
        visibility="members_only",
        participation_policy_id=None,
        status=CivicSpaceStatus.DRAFT,
    )
    activated = space.with_status(CivicSpaceStatus.ACTIVE)
    assert activated.status is CivicSpaceStatus.ACTIVE


# ---------------------------------------------------------------------------
# OrganizationalRelation: typed relations, cycles, overlap
# ---------------------------------------------------------------------------


def _relation(**overrides: object) -> OrganizationalRelation:
    defaults = dict(
        relation_id=uuid4(),
        relation_version=1,
        relation_type=RelationType.PARENT_OF,
        source_organization_id=uuid4(),
        target_organization_id=uuid4(),
        status=RelationStatus.ACTIVE,
        valid_from=T0,
    )
    defaults.update(overrides)
    return OrganizationalRelation(**defaults)  # type: ignore[arg-type]


def test_valid_typed_relation_categories() -> None:
    parent_of = _relation(relation_type=RelationType.PARENT_OF)
    assert parent_of.relation_category.value == "hierarchy"
    affiliated = _relation(relation_type=RelationType.AFFILIATED_WITH)
    assert affiliated.relation_category.value == "cooperation"
    successor = _relation(relation_type=RelationType.SUCCESSOR_OF)
    assert successor.relation_category.value == "continuity"


def test_relation_may_not_target_its_own_source() -> None:
    org_id = uuid4()
    with pytest.raises(OrganizationalCycleForbiddenError):
        _relation(source_organization_id=org_id, target_organization_id=org_id)


def test_temporary_supervision_requires_valid_until() -> None:
    with pytest.raises(TemporarySupervisionWindowInvalidError):
        _relation(relation_type=RelationType.TEMPORARY_SUPERVISION_BY, valid_until=None)


def test_forbidden_hierarchical_cycle_detected() -> None:
    """A -> B (parent_of), attempting B -> A (parent_of) would create a
    two-node cycle - forbidden without exception (canon 19e.7)."""
    a, b = uuid4(), uuid4()
    existing = [(a, b, RelationType.PARENT_OF)]
    assert would_create_hierarchy_cycle(
        existing,
        source_organization_id=b,
        target_organization_id=a,
        relation_type=RelationType.PARENT_OF,
    )


def test_non_cyclic_hierarchy_edge_is_allowed() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    existing = [(a, b, RelationType.PARENT_OF)]
    assert not would_create_hierarchy_cycle(
        existing,
        source_organization_id=b,
        target_organization_id=c,
        relation_type=RelationType.PARENT_OF,
    )


def test_affiliated_with_mutual_edges_never_flagged_as_cycles() -> None:
    """Cooperation-category `affiliated_with` explicitly permits mutual
    edges - cycle-freedom is not a blanket rule outside hierarchy/
    temporary_supervision_by (canon 19e.7)."""
    a, b = uuid4(), uuid4()
    # would_create_hierarchy_cycle only ever applies to hierarchy types;
    # affiliated_with is never even checked.
    assert not would_create_hierarchy_cycle(
        [(a, b, RelationType.AFFILIATED_WITH)],
        source_organization_id=b,
        target_organization_id=a,
        relation_type=RelationType.AFFILIATED_WITH,
    )


def test_temporary_supervision_cycle_forbidden_even_though_cooperation_category() -> None:
    a, b = uuid4(), uuid4()
    existing = [(a, b)]
    assert would_create_supervision_cycle(
        existing, supervisor_organization_id=b, supervised_organization_id=a
    )


def test_temporary_supervision_window_max_duration_enforced() -> None:
    """91-day request rejected by default (task section 11)."""
    with pytest.raises(TemporarySupervisionWindowInvalidError):
        assert_temporary_supervision_window_valid(T0, T0 + timedelta(days=91))
    # Exactly 90 days is allowed.
    assert_temporary_supervision_window_valid(T0, T0 + timedelta(days=90))


def test_temporary_supervision_open_ended_rejected() -> None:
    with pytest.raises(TemporarySupervisionWindowInvalidError):
        assert_temporary_supervision_window_valid(T0, None)


def test_temporary_supervision_narrower_policy_limit_supported() -> None:
    """A narrower (never wider) max_days may be supplied by a future
    legal-review hook (task section 11)."""
    assert_temporary_supervision_window_valid(T0, T0 + timedelta(days=29), max_days=30)
    with pytest.raises(TemporarySupervisionWindowInvalidError):
        assert_temporary_supervision_window_valid(T0, T0 + timedelta(days=31), max_days=30)


# ---------------------------------------------------------------------------
# OrganizationalScope
# ---------------------------------------------------------------------------


def test_organizational_scope_exact_match() -> None:
    org_id = uuid4()
    a = organization_scope(org_id)
    b = organization_scope(org_id)
    assert a.matches(b)
    assert a.scope_type is ScopeType.ORGANIZATION_SCOPE


def test_organizational_scope_different_type_never_matches() -> None:
    org_id = uuid4()
    a = organization_scope(org_id)
    b = OrganizationalScope(scope_type=ScopeType.JURISDICTION_SCOPE, scope_reference=str(org_id))
    assert not a.matches(b)


# ---------------------------------------------------------------------------
# OrganizationalAuthority: self-assignment, incompatibility, lifecycle
# ---------------------------------------------------------------------------


def _authority(**overrides: object) -> OrganizationalAuthority:
    defaults = dict(
        authority_id=uuid4(),
        authority_version=1,
        role_code=InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR.value,
        scope=organization_scope(uuid4()),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=T0,
        status=AuthorityStatus.ACTIVE,
        policy_version="1.0",
        decision_reference=uuid4(),
    )
    defaults.update(overrides)
    return OrganizationalAuthority(**defaults)  # type: ignore[arg-type]


def test_valid_authority_appointment() -> None:
    authority = _authority()
    assert authority.is_usable(at=T0)


def test_self_assignment_rejected() -> None:
    subject = uuid4()
    with pytest.raises(OrganizationSelfAssignmentForbiddenError):
        _authority(appointing_authority_reference=subject, assigned_subject_reference=subject)


def test_expired_authority_not_usable() -> None:
    authority = _authority(valid_from=T0, valid_until=T1)
    assert not authority.is_usable(at=T1 + timedelta(days=1))


def test_revoked_authority_not_usable() -> None:
    authority = _authority(status=AuthorityStatus.REVOKED, revocation_reason_reference="misconduct")
    assert not authority.is_usable(at=T0)


def test_revoked_status_requires_reason_reference() -> None:
    with pytest.raises(ValueError):
        _authority(status=AuthorityStatus.REVOKED)


def test_suspended_authority_not_usable() -> None:
    authority = _authority(status=AuthorityStatus.SUSPENDED)
    assert not authority.is_usable(at=T0)


@pytest.mark.parametrize(
    "role_a,role_b",
    [
        (InstitutionalRole.ELECTION_OFFICER, InstitutionalRole.INDEPENDENT_AUDITOR),
        (InstitutionalRole.FINANCE_AUDITOR, InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR),
        (InstitutionalRole.DPO, InstitutionalRole.ORGANIZATIONAL_ADMINISTRATOR),
        (InstitutionalRole.PARTY_ARBITRATOR, InstitutionalRole.ELECTION_BOARD_MEMBER),
    ],
)
def test_incompatible_role_pairs_rejected(
    role_a: InstitutionalRole, role_b: InstitutionalRole
) -> None:
    conflict = find_role_incompatibility([role_a.value], role_b.value)
    assert conflict == role_a.value


def test_compatible_roles_never_flagged() -> None:
    assert (
        find_role_incompatibility(
            [InstitutionalRole.DPO.value], InstitutionalRole.INDEPENDENT_AUDITOR.value
        )
        is None
    )


def test_unknown_role_code_never_conflicts_under_baseline() -> None:
    assert find_role_incompatibility(["some_future_role"], "another_future_role") is None

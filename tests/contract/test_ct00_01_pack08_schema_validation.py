"""CT-00-01 Schema Validation (canon section 27), PACK-08 additions
(canon-0.7.0 section 19e, ADR-032 through ADR-037) - added alongside
(never replacing) `test_ct00_01_schema_validation.py`'s own PACK-02
through PACK-07 coverage, mirroring the precedent
`test_ct00_01_pack07_schema_validation.py` set for a new, schema-heavy
pack: a dedicated new file rather than an edit to the giant pre-existing
one.

Validates every new PACK-08 entity schema under `contracts/schemas/`
(`Organization`, `OrganizationalUnit`, `CivicSpace`,
`OrganizationalRelation`, `OrganizationalAuthority`) and every new
PACK-08 event payload schema under `contracts/events/` (the shared
`organization.*` seven-event payload, plus
`organizational_relation.created`/`.ended`,
`organizational_authority.assigned`/`.revoked`,
`regional_scope_access.granted`/`.revoked`) against real,
directly-constructed domain instances - each one satisfies every real
`__post_init__` structural invariant the domain class enforces.

Requires nothing beyond `epd2_core.minimal_json_schema` (always
available, stdlib-only) for validation itself.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from _schema_helpers import load_event_schema, load_schema, to_jsonable

from epd2_core.event_envelope import ActorRef
from epd2_core.minimal_json_schema import validate
from epd2_organization_service.domain import (
    AccessMode,
    AuthorityStatus,
    CivicSpace,
    CivicSpaceStatus,
    Organization,
    OrganizationalAuthority,
    OrganizationalRelation,
    OrganizationalUnit,
    OrganizationStatus,
    RegionalScopeAccessDecision,
    RelationStatus,
    RelationType,
    organization_scope,
)
from epd2_organization_service.events import (
    build_organization_activated_event,
    build_organization_created_event,
    build_organizational_authority_assigned_event,
    build_organizational_authority_revoked_event,
    build_organizational_relation_created_event,
    build_organizational_relation_ended_event,
    build_regional_scope_access_granted_event,
    build_regional_scope_access_revoked_event,
)

_OCCURRED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


# ---------------------------------------------------------------------------
# Entity schemas (contracts/schemas/)
# ---------------------------------------------------------------------------


def test_organization_instance_validates() -> None:
    organization = Organization(
        organization_id=uuid4(),
        name="Landesverband Beispiel",
        legal_operator="Beispiel e.V.",
        organization_type="party_unit",
        status=OrganizationStatus.ACTIVE,
        default_policy_version="1.0",
        organization_profile="landesverband",
        effective_from=_OCCURRED_AT,
    )
    instance = {
        "organization_id": str(organization.organization_id),
        "name": organization.name,
        "legal_operator": organization.legal_operator,
        "organization_type": organization.organization_type,
        "status": organization.status.value,
        "default_policy_version": organization.default_policy_version,
        "organization_profile": organization.organization_profile,
        "effective_from": organization.effective_from.isoformat(),
        "effective_until": None,
        "dissolved_at": None,
        "successor_reference": None,
        "parent_reference": None,
    }
    validate(instance, load_schema("organization.schema.json"))


def test_organizational_unit_instance_validates() -> None:
    unit = OrganizationalUnit(
        organizational_unit_id=uuid4(),
        owning_organization_id=uuid4(),
        unit_type="working_group",
        status=OrganizationStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
    )
    assert unit.recorded_at is not None
    instance = {
        "organizational_unit_id": str(unit.organizational_unit_id),
        "owning_organization_id": str(unit.owning_organization_id),
        "unit_type": unit.unit_type,
        "status": unit.status.value,
        "valid_from": unit.valid_from.isoformat(),
        "valid_until": None,
        "recorded_at": unit.recorded_at.isoformat(),
    }
    validate(instance, load_schema("organizational-unit.schema.json"))


def test_civic_space_instance_validates() -> None:
    space = CivicSpace(
        space_id=uuid4(),
        organization_id=uuid4(),
        name="Mitglieder-Forum",
        space_type="discussion_forum",
        visibility="members_only",
        participation_policy_id=uuid4(),
        status=CivicSpaceStatus.ACTIVE,
    )
    instance = {
        "space_id": str(space.space_id),
        "organization_id": str(space.organization_id),
        "name": space.name,
        "space_type": space.space_type,
        "visibility": space.visibility,
        "participation_policy_id": str(space.participation_policy_id),
        "status": space.status.value,
    }
    validate(instance, load_schema("civic-space.schema.json"))


def test_organizational_relation_instance_validates() -> None:
    relation = OrganizationalRelation(
        relation_id=uuid4(),
        relation_version=1,
        relation_type=RelationType.PARENT_OF,
        source_organization_id=uuid4(),
        target_organization_id=uuid4(),
        status=RelationStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
        authorizing_decision_reference=uuid4(),
    )
    instance = {
        "relation_id": str(relation.relation_id),
        "relation_version": relation.relation_version,
        "relation_type": relation.relation_type.value,
        "relation_category": relation.relation_category.value,
        "source_organization_id": str(relation.source_organization_id),
        "target_organization_id": str(relation.target_organization_id),
        "status": relation.status.value,
        "valid_from": relation.valid_from.isoformat(),
        "valid_until": None,
        "supersedes_relation_id": None,
        "authorizing_decision_reference": str(relation.authorizing_decision_reference),
    }
    validate(instance, load_schema("organizational-relation.schema.json"))


def test_organizational_authority_instance_validates() -> None:
    authority = OrganizationalAuthority(
        authority_id=uuid4(),
        authority_version=1,
        role_code="election_officer",
        scope=organization_scope(uuid4()),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=_OCCURRED_AT,
        status=AuthorityStatus.ACTIVE,
        policy_version="1.0",
        decision_reference=uuid4(),
        grants_procedural_authority=True,
        grants_data_access=False,
    )
    instance = {
        "authority_id": str(authority.authority_id),
        "authority_version": authority.authority_version,
        "role_code": authority.role_code,
        "scope_type": authority.scope.scope_type.value,
        "scope_reference": authority.scope.scope_reference,
        "appointing_authority_reference": str(authority.appointing_authority_reference),
        "assigned_subject_reference": str(authority.assigned_subject_reference),
        "valid_from": authority.valid_from.isoformat(),
        "valid_until": None,
        "status": authority.status.value,
        "policy_version": authority.policy_version,
        "decision_reference": str(authority.decision_reference),
        "revocation_reason_reference": None,
        "grants_procedural_authority": True,
        "grants_data_access": False,
    }
    validate(instance, load_schema("organizational-authority.schema.json"))


# ---------------------------------------------------------------------------
# Event payload schemas (contracts/events/)
# ---------------------------------------------------------------------------


def test_organization_status_event_payload_validates_for_created_and_activated() -> None:
    """The shared organization.* payload builder is exercised through two
    of its seven event_type callers (organization.created,
    organization.activated) - all seven share one payload shape, verified
    directly against events.py."""
    organization = Organization(
        organization_id=uuid4(),
        name="Landesverband Beispiel",
        legal_operator="Beispiel e.V.",
        organization_type="party_unit",
        status=OrganizationStatus.DRAFT,
        default_policy_version="1.0",
        organization_profile="landesverband",
        effective_from=_OCCURRED_AT,
    )
    schema = load_event_schema("organization-status-payload.v1.schema.json")

    created_event = build_organization_created_event(
        event_id=uuid4(),
        organization=organization,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
        decision_reference=uuid4(),
    )
    validate(to_jsonable(created_event.payload), schema)

    activated = organization.with_status(OrganizationStatus.ACTIVE)
    activated_event = build_organization_activated_event(
        event_id=uuid4(),
        organization=activated,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
        decision_reference=uuid4(),
    )
    validate(to_jsonable(activated_event.payload), schema)


def test_organizational_relation_created_event_payload_validates() -> None:
    relation = OrganizationalRelation(
        relation_id=uuid4(),
        relation_version=1,
        relation_type=RelationType.AFFILIATED_WITH,
        source_organization_id=uuid4(),
        target_organization_id=uuid4(),
        status=RelationStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
        authorizing_decision_reference=uuid4(),
    )
    event = build_organizational_relation_created_event(
        event_id=uuid4(),
        relation=relation,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("organizational-relation-created-payload.v1.schema.json"),
    )


def test_organizational_relation_ended_event_payload_validates() -> None:
    relation = OrganizationalRelation(
        relation_id=uuid4(),
        relation_version=1,
        relation_type=RelationType.AFFILIATED_WITH,
        source_organization_id=uuid4(),
        target_organization_id=uuid4(),
        status=RelationStatus.ACTIVE,
        valid_from=_OCCURRED_AT,
        recorded_at=_OCCURRED_AT,
    ).with_valid_until(datetime(2026, 6, 1, tzinfo=UTC))
    event = build_organizational_relation_ended_event(
        event_id=uuid4(),
        relation=relation,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("organizational-relation-ended-payload.v1.schema.json"),
    )


def test_organizational_authority_assigned_event_payload_validates() -> None:
    authority = OrganizationalAuthority(
        authority_id=uuid4(),
        authority_version=1,
        role_code="election_officer",
        scope=organization_scope(uuid4()),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=_OCCURRED_AT,
        status=AuthorityStatus.ACTIVE,
        policy_version="1.0",
        decision_reference=uuid4(),
    )
    event = build_organizational_authority_assigned_event(
        event_id=uuid4(),
        authority=authority,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("organizational-authority-assigned-payload.v1.schema.json"),
    )


def test_organizational_authority_revoked_event_payload_validates() -> None:
    authority = OrganizationalAuthority(
        authority_id=uuid4(),
        authority_version=1,
        role_code="election_officer",
        scope=organization_scope(uuid4()),
        appointing_authority_reference=uuid4(),
        assigned_subject_reference=uuid4(),
        valid_from=_OCCURRED_AT,
        status=AuthorityStatus.ACTIVE,
        policy_version="1.0",
        decision_reference=uuid4(),
    ).with_status(AuthorityStatus.REVOKED, revocation_reason_reference="no longer required")
    event = build_organizational_authority_revoked_event(
        event_id=uuid4(),
        authority=authority,
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("organizational-authority-revoked-payload.v1.schema.json"),
    )


def test_regional_scope_access_granted_event_payload_validates() -> None:
    decision = RegionalScopeAccessDecision(
        allowed=True,
        reason_code="",
        evaluated_scope=organization_scope(uuid4()),
        policy_version="1.0",
        effective_time=_OCCURRED_AT,
        mode=AccessMode.ANCESTOR_SCOPE,
        audit_reference=uuid4(),
    )
    event = build_regional_scope_access_granted_event(
        event_id=uuid4(),
        decision=decision,
        actor=_actor(),
        subject_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("regional-scope-access-granted-payload.v1.schema.json"),
    )


def test_regional_scope_access_revoked_event_payload_validates() -> None:
    event = build_regional_scope_access_revoked_event(
        event_id=uuid4(),
        scope=None,
        subject_id=uuid4(),
        actor=_actor(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_OCCURRED_AT,
    )
    validate(
        to_jsonable(event.payload),
        load_event_schema("regional-scope-access-revoked-payload.v1.schema.json"),
    )

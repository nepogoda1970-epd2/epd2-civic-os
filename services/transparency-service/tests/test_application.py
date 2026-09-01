"""Tests for epd2_transparency_service.application.

Exercises the full command set against in-memory stores only. Covers
CT-00-04 (idempotency), CT-00-06 (missing permission), CT-00-07 (audit
creation), and the pack's own structural guarantees (forbidden fields
never reach a public payload, duplicate-subject-event rejection,
superseding side effects).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_core.event_envelope import ActorRef
from epd2_transparency_service.application import (
    PermissionDeniedError,
    activate_disclosure_policy,
    correct_ledger_entry,
    define_disclosure_policy,
    generate_audit_export_package,
    publish_audit_export_package,
    publish_ledger_entry,
    publish_lobby_log_entry,
    submit_lobby_log_entry,
    verify_audit_export_package,
)
from epd2_transparency_service.domain import (
    DisclosureClass,
    FieldRule,
    IncludedTargetType,
    LedgerSubjectType,
    LobbyLogContactMethod,
    LobbyLogRelatedSubjectType,
    Transformation,
)
from epd2_transparency_service.exceptions import (
    LedgerEntryAlreadyPublishedError,
    PublicationNotAllowedError,
    UnknownPublicLedgerEntryError,
)
from epd2_transparency_service.storage import (
    InMemoryAuditExportPackageStore,
    InMemoryDisclosurePolicyStore,
    InMemoryLobbyLogEntryStore,
    InMemoryPublicLedgerEntryStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)
_CLOCK = FixedClock(_NOW)


def _actor() -> ActorRef:
    return ActorRef(actor_id=uuid4(), actor_type="service")


def _activated_policy(
    policy_store: InMemoryDisclosurePolicyStore,
    audit_store: InMemoryAuditEventStore,
    *,
    applies_to_subject_type: str,
    field_rules: tuple[FieldRule, ...] = (),
) -> UUID:
    defined = define_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=uuid4(),
        applies_to_subject_type=applies_to_subject_type,
        field_rules=field_rules,
        effective_from=_NOW,
        version=1,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    activate_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=defined.policy.disclosure_policy_id,
        approved_by_role_id=uuid4(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    return defined.policy.disclosure_policy_id


def test_publish_ledger_entry_requires_authorization() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(policy_store, audit_store, applies_to_subject_type="initiative")
    with pytest.raises(PermissionDeniedError):
        publish_ledger_entry(
            ledger_store,
            policy_store,
            audit_store,
            public_ledger_entry_id=uuid4(),
            subject_type=LedgerSubjectType.INITIATIVE,
            subject_id=uuid4(),
            subject_event_id=uuid4(),
            raw_content={},
            published_by_role_id=uuid4(),
            redaction_notice=None,
            actor=_actor(),
            actor_is_authorized=False,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_publish_ledger_entry_requires_active_policy() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(PublicationNotAllowedError):
        publish_ledger_entry(
            ledger_store,
            policy_store,
            audit_store,
            public_ledger_entry_id=uuid4(),
            subject_type=LedgerSubjectType.INITIATIVE,
            subject_id=uuid4(),
            subject_event_id=uuid4(),
            raw_content={},
            published_by_role_id=uuid4(),
            redaction_notice=None,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_publish_ledger_entry_is_idempotent_by_event_id() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(
        policy_store,
        audit_store,
        applies_to_subject_type="initiative",
        field_rules=(FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),),
    )
    event_id = uuid4()
    kwargs = dict(
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        raw_content={"title": "x"},
        published_by_role_id=uuid4(),
        redaction_notice=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
        event_id=event_id,
    )
    first = publish_ledger_entry(ledger_store, policy_store, audit_store, **kwargs)  # type: ignore[arg-type]
    second = publish_ledger_entry(ledger_store, policy_store, audit_store, **kwargs)  # type: ignore[arg-type]
    assert first.entry == second.entry
    assert first.audit_event.audit_event_id == second.audit_event.audit_event_id


def test_publish_ledger_entry_rejects_duplicate_subject_event_id() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(
        policy_store,
        audit_store,
        applies_to_subject_type="initiative",
        field_rules=(FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),),
    )
    subject_event_id = uuid4()
    publish_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=subject_event_id,
        raw_content={"title": "x"},
        published_by_role_id=uuid4(),
        redaction_notice=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(LedgerEntryAlreadyPublishedError):
        publish_ledger_entry(
            ledger_store,
            policy_store,
            audit_store,
            public_ledger_entry_id=uuid4(),
            subject_type=LedgerSubjectType.INITIATIVE,
            subject_id=uuid4(),
            subject_event_id=subject_event_id,
            raw_content={"title": "y"},
            published_by_role_id=uuid4(),
            redaction_notice=None,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_publish_ledger_entry_creates_audit_event() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(
        policy_store,
        audit_store,
        applies_to_subject_type="initiative",
        field_rules=(FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),),
    )
    result = publish_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        raw_content={"title": "x"},
        published_by_role_id=uuid4(),
        redaction_notice=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert audit_store.get_by_event_id(result.audit_event.audit_event_id) is not None
    assert result.audit_event.target_type == "public_ledger_entry"


def test_publish_ledger_entry_never_leaks_role_id_in_public_payload() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(
        policy_store,
        audit_store,
        applies_to_subject_type="initiative",
        field_rules=(FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),),
    )
    role_id = uuid4()
    result = publish_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        raw_content={"title": "x"},
        published_by_role_id=role_id,
        redaction_notice=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert str(role_id) not in str(result.event.payload)


def test_correct_ledger_entry_sets_supersedes_entry_id() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(
        policy_store,
        audit_store,
        applies_to_subject_type="initiative",
        field_rules=(FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),),
    )
    original = publish_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        raw_content={"title": "x"},
        published_by_role_id=uuid4(),
        redaction_notice=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    correction = correct_ledger_entry(
        ledger_store,
        policy_store,
        audit_store,
        new_public_ledger_entry_id=uuid4(),
        supersedes_entry_id=original.entry.public_ledger_entry_id,
        raw_content={"title": "x (fixed)"},
        published_by_role_id=uuid4(),
        redaction_notice="fixed typo",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert correction.entry.supersedes_entry_id == original.entry.public_ledger_entry_id
    # The original row itself is never rewritten.
    assert ledger_store.get(original.entry.public_ledger_entry_id) == original.entry


def test_correct_ledger_entry_unknown_original_raises() -> None:
    ledger_store = InMemoryPublicLedgerEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    with pytest.raises(UnknownPublicLedgerEntryError):
        correct_ledger_entry(
            ledger_store,
            policy_store,
            audit_store,
            new_public_ledger_entry_id=uuid4(),
            supersedes_entry_id=uuid4(),
            raw_content={},
            published_by_role_id=uuid4(),
            redaction_notice=None,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_generate_and_publish_audit_export_package_roundtrip() -> None:
    package_store = InMemoryAuditExportPackageStore()
    audit_store = InMemoryAuditEventStore()
    generated = generate_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=uuid4(),
        scope_description="test scope",
        requested_by_role_id=uuid4(),
        included_target_types=(IncludedTargetType.INITIATIVE,),
        redaction_notice=None,
        supersedes_package_id=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert generated.package.status.value == "generated"
    published = publish_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=generated.package.audit_export_package_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert published.package.status.value == "published"
    verification = verify_audit_export_package(published.package)
    assert verification.is_intact


def test_publish_audit_export_package_supersedes_old_package() -> None:
    package_store = InMemoryAuditExportPackageStore()
    audit_store = InMemoryAuditEventStore()
    old_generated = generate_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=uuid4(),
        scope_description="v1",
        requested_by_role_id=uuid4(),
        included_target_types=(IncludedTargetType.INITIATIVE,),
        redaction_notice=None,
        supersedes_package_id=None,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    old_published = publish_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=old_generated.package.audit_export_package_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    new_generated = generate_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=uuid4(),
        scope_description="v2",
        requested_by_role_id=uuid4(),
        included_target_types=(IncludedTargetType.INITIATIVE,),
        redaction_notice=None,
        supersedes_package_id=old_published.package.audit_export_package_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    new_published = publish_audit_export_package(
        package_store,
        audit_store,
        audit_export_package_id=new_generated.package.audit_export_package_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert new_published.superseded_package is not None
    assert new_published.superseded_package.status.value == "superseded"
    reloaded_old = package_store.get(old_published.package.audit_export_package_id)
    assert reloaded_old is not None
    assert reloaded_old.status.value == "superseded"
    # Old package content untouched - only status changed.
    assert reloaded_old.package_digest == old_published.package.package_digest


def test_activate_disclosure_policy_supersedes_previous_active_version() -> None:
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    first_id = _activated_policy(policy_store, audit_store, applies_to_subject_type="initiative")
    second_defined = define_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="initiative",
        field_rules=(),
        effective_from=_NOW,
        version=2,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    result = activate_disclosure_policy(
        policy_store,
        audit_store,
        disclosure_policy_id=second_defined.policy.disclosure_policy_id,
        approved_by_role_id=uuid4(),
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert result.superseded_policy is not None
    assert result.superseded_policy.disclosure_policy_id == first_id
    assert result.superseded_policy.status.value == "superseded"
    active_now = policy_store.get_active_for_subject_type("initiative")
    assert active_now is not None
    assert active_now.disclosure_policy_id == second_defined.policy.disclosure_policy_id


def test_submit_and_publish_lobby_log_entry() -> None:
    lobby_store = InMemoryLobbyLogEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    _activated_policy(policy_store, audit_store, applies_to_subject_type="lobby_log_entry")
    submitted = submit_lobby_log_entry(
        lobby_store,
        audit_store,
        lobby_log_entry_id=uuid4(),
        submitted_by_role_id=uuid4(),
        organization_name="Acme Advocacy",
        related_subject_type=LobbyLogRelatedSubjectType.INITIATIVE,
        related_subject_id=uuid4(),
        contact_date=_NOW,
        contact_method=LobbyLogContactMethod.MEETING,
        topic_summary="topic",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert submitted.entry.status.value == "submitted"
    published = publish_lobby_log_entry(
        lobby_store,
        policy_store,
        audit_store,
        lobby_log_entry_id=submitted.entry.lobby_log_entry_id,
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    assert published.entry.status.value == "published"


def test_submit_lobby_log_entry_rejects_missing_mandatory_field() -> None:
    lobby_store = InMemoryLobbyLogEntryStore()
    audit_store = InMemoryAuditEventStore()
    from epd2_transparency_service.exceptions import LobbyLogEntryIncompleteError

    with pytest.raises(LobbyLogEntryIncompleteError):
        submit_lobby_log_entry(
            lobby_store,
            audit_store,
            lobby_log_entry_id=uuid4(),
            submitted_by_role_id=uuid4(),
            organization_name="",
            related_subject_type=LobbyLogRelatedSubjectType.INITIATIVE,
            related_subject_id=uuid4(),
            contact_date=_NOW,
            contact_method=LobbyLogContactMethod.MEETING,
            topic_summary="topic",
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )


def test_publish_lobby_log_entry_requires_active_policy() -> None:
    lobby_store = InMemoryLobbyLogEntryStore()
    policy_store = InMemoryDisclosurePolicyStore()
    audit_store = InMemoryAuditEventStore()
    submitted = submit_lobby_log_entry(
        lobby_store,
        audit_store,
        lobby_log_entry_id=uuid4(),
        submitted_by_role_id=uuid4(),
        organization_name="Acme Advocacy",
        related_subject_type=LobbyLogRelatedSubjectType.INITIATIVE,
        related_subject_id=uuid4(),
        contact_date=_NOW,
        contact_method=LobbyLogContactMethod.MEETING,
        topic_summary="topic",
        actor=_actor(),
        actor_is_authorized=True,
        correlation_id=uuid4(),
        clock=_CLOCK,
    )
    with pytest.raises(PublicationNotAllowedError):
        publish_lobby_log_entry(
            lobby_store,
            policy_store,
            audit_store,
            lobby_log_entry_id=submitted.entry.lobby_log_entry_id,
            actor=_actor(),
            actor_is_authorized=True,
            correlation_id=uuid4(),
            clock=_CLOCK,
        )

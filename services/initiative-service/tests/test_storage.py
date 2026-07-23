"""Tests for epd2_initiative_service.storage.

Covers idempotent create-or-conflict for every owned entity's store, the
canon-11.2 `InitiativeVersion` rule-freeze (`VersionFrozenError`), and
canon-11.3's one-active-support-per-participant invariant
(`DuplicateSupportError`).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_initiative_service.domain import (
    Amendment,
    AmendmentStatus,
    Initiative,
    InitiativeStatus,
    InitiativeVersion,
    SourceRecord,
    SourceVerificationStatus,
    SupportRecord,
    SupportStatus,
)
from epd2_initiative_service.exceptions import (
    AmendmentCreationConflictError,
    DuplicateSupportError,
    InitiativeCreationConflictError,
    InitiativeVersionFrozenError,
    SourceRecordCreationConflictError,
    SupportRecordCreationConflictError,
)
from epd2_initiative_service.storage import (
    InMemoryAmendmentStore,
    InMemoryInitiativeStore,
    InMemoryInitiativeVersionStore,
    InMemorySourceRecordStore,
    InMemorySupportRecordStore,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _initiative(**overrides: object) -> Initiative:
    kwargs: dict[str, object] = dict(
        initiative_id=uuid4(),
        space_id=uuid4(),
        current_version_id=None,
        author_actor_id=uuid4(),
        initiative_type="citizen_law",
        workflow_id=uuid4(),
        status=InitiativeStatus.DRAFT,
        support_count=0,
        created_at=_NOW,
    )
    kwargs.update(overrides)
    return Initiative(**kwargs)  # type: ignore[arg-type]


def _version(**overrides: object) -> InitiativeVersion:
    kwargs: dict[str, object] = dict(
        initiative_version_id=uuid4(),
        initiative_id=uuid4(),
        version_number=1,
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=(),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
        created_by_actor_id=uuid4(),
        content_hash="a" * 64,
    )
    kwargs.update(overrides)
    return InitiativeVersion(**kwargs)  # type: ignore[arg-type]


def _support(**overrides: object) -> SupportRecord:
    kwargs: dict[str, object] = dict(
        support_record_id=uuid4(),
        initiative_id=uuid4(),
        support_actor_reference=uuid4(),
        credential_reference=uuid4(),
        created_at=_NOW,
        status=SupportStatus.ACTIVE,
    )
    kwargs.update(overrides)
    return SupportRecord(**kwargs)  # type: ignore[arg-type]


def _amendment(**overrides: object) -> Amendment:
    kwargs: dict[str, object] = dict(
        amendment_id=uuid4(),
        initiative_id=uuid4(),
        target_version_id=uuid4(),
        proposer_actor_id=uuid4(),
        proposed_change="Change",
        justification="Because",
        status=AmendmentStatus.DRAFT,
        decision_reference=None,
    )
    kwargs.update(overrides)
    return Amendment(**kwargs)  # type: ignore[arg-type]


def _source(**overrides: object) -> SourceRecord:
    kwargs: dict[str, object] = dict(
        source_id=uuid4(),
        source_type="report",
        title="Title",
        publisher="Publisher",
        publication_date=None,
        url="https://example.org",
        archive_reference=None,
        verification_status=SourceVerificationStatus.UNVERIFIED,
        added_by_actor_id=uuid4(),
        accessed_at=_NOW,
        content_hash="a" * 64,
        valid_until=None,
    )
    kwargs.update(overrides)
    return SourceRecord(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# InitiativeStore
# ---------------------------------------------------------------------------


def test_initiative_store_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryInitiativeStore()
    initiative = _initiative()
    first = store.create(initiative)
    second = store.create(initiative)
    assert first == second == initiative


def test_initiative_store_create_conflicts_on_different_content() -> None:
    store = InMemoryInitiativeStore()
    initiative = _initiative()
    store.create(initiative)
    with pytest.raises(InitiativeCreationConflictError):
        store.create(replace(initiative, initiative_type="different_type"))


def test_initiative_store_get_returns_none_for_unknown_id() -> None:
    store = InMemoryInitiativeStore()
    assert store.get(uuid4()) is None


def test_initiative_store_save_persists_update() -> None:
    store = InMemoryInitiativeStore()
    initiative = _initiative()
    store.create(initiative)
    updated = initiative.with_status(InitiativeStatus.SUBMITTED)
    store.save(updated)
    fetched = store.get(initiative.initiative_id)
    assert fetched is not None
    assert fetched.status == InitiativeStatus.SUBMITTED


# ---------------------------------------------------------------------------
# InitiativeVersionStore
# ---------------------------------------------------------------------------


def test_version_store_save_is_idempotent_for_identical_content() -> None:
    store = InMemoryInitiativeVersionStore()
    version = _version()
    first = store.save(version)
    second = store.save(version)
    assert first == second == version


def test_version_store_save_freezes_on_different_content_same_key() -> None:
    """Canon 11.2: a published version never changes."""
    store = InMemoryInitiativeVersionStore()
    version = _version()
    store.save(version)
    with pytest.raises(InitiativeVersionFrozenError):
        store.save(replace(version, title="A different title"))


def test_version_store_get_by_key_and_by_id() -> None:
    store = InMemoryInitiativeVersionStore()
    version = _version()
    store.save(version)
    assert store.get(version.initiative_id, version.version_number) == version
    assert store.get_by_id(version.initiative_version_id) == version


def test_version_store_latest_version() -> None:
    store = InMemoryInitiativeVersionStore()
    initiative_id = uuid4()
    v1 = _version(initiative_id=initiative_id, version_number=1)
    v2 = _version(initiative_id=initiative_id, version_number=2)
    store.save(v1)
    store.save(v2)
    assert store.latest_version(initiative_id) == v2


def test_version_store_latest_version_none_when_absent() -> None:
    store = InMemoryInitiativeVersionStore()
    assert store.latest_version(uuid4()) is None


# ---------------------------------------------------------------------------
# SupportRecordStore
# ---------------------------------------------------------------------------


def test_support_store_create_is_idempotent_for_identical_content() -> None:
    store = InMemorySupportRecordStore()
    support = _support()
    first = store.create(support)
    second = store.create(support)
    assert first == second == support


def test_support_store_create_conflicts_on_different_content_same_id() -> None:
    store = InMemorySupportRecordStore()
    support = _support()
    store.create(support)
    with pytest.raises(SupportRecordCreationConflictError):
        store.create(replace(support, credential_reference=uuid4()))


def test_support_store_rejects_second_active_support_same_participant() -> None:
    """Canon 11.3: one participant may have at most one active support
    per initiative."""
    store = InMemorySupportRecordStore()
    initiative_id = uuid4()
    actor_reference = uuid4()
    first = _support(initiative_id=initiative_id, support_actor_reference=actor_reference)
    store.create(first)
    second = _support(initiative_id=initiative_id, support_actor_reference=actor_reference)
    with pytest.raises(DuplicateSupportError):
        store.create(second)


def test_support_store_allows_active_support_after_prior_one_withdrawn() -> None:
    store = InMemorySupportRecordStore()
    initiative_id = uuid4()
    actor_reference = uuid4()
    first = _support(initiative_id=initiative_id, support_actor_reference=actor_reference)
    store.create(first)
    store.save(replace(first, status=SupportStatus.WITHDRAWN))
    second = _support(initiative_id=initiative_id, support_actor_reference=actor_reference)
    stored = store.create(second)
    assert stored.status == SupportStatus.ACTIVE


def test_support_store_allows_active_support_for_different_participants() -> None:
    store = InMemorySupportRecordStore()
    initiative_id = uuid4()
    first = _support(initiative_id=initiative_id)
    second = _support(initiative_id=initiative_id)
    store.create(first)
    store.create(second)
    assert store.get(first.support_record_id) is not None
    assert store.get(second.support_record_id) is not None


def test_support_store_allows_active_support_for_different_initiatives() -> None:
    store = InMemorySupportRecordStore()
    actor_reference = uuid4()
    first = _support(support_actor_reference=actor_reference)
    second = _support(support_actor_reference=actor_reference)
    store.create(first)
    store.create(second)
    assert store.get(first.support_record_id) is not None
    assert store.get(second.support_record_id) is not None


# ---------------------------------------------------------------------------
# AmendmentStore
# ---------------------------------------------------------------------------


def test_amendment_store_create_is_idempotent_for_identical_content() -> None:
    store = InMemoryAmendmentStore()
    amendment = _amendment()
    first = store.create(amendment)
    second = store.create(amendment)
    assert first == second == amendment


def test_amendment_store_create_conflicts_on_different_content() -> None:
    store = InMemoryAmendmentStore()
    amendment = _amendment()
    store.create(amendment)
    with pytest.raises(AmendmentCreationConflictError):
        store.create(replace(amendment, justification="A different reason"))


# ---------------------------------------------------------------------------
# SourceRecordStore
# ---------------------------------------------------------------------------


def test_source_store_create_is_idempotent_for_identical_content() -> None:
    store = InMemorySourceRecordStore()
    source = _source()
    first = store.create(source)
    second = store.create(source)
    assert first == second == source


def test_source_store_create_conflicts_on_different_content() -> None:
    store = InMemorySourceRecordStore()
    source = _source()
    store.create(source)
    with pytest.raises(SourceRecordCreationConflictError):
        store.create(replace(source, title="A different title"))


def test_source_store_save_persists_verification_status_update() -> None:
    store = InMemorySourceRecordStore()
    source = _source()
    store.create(source)
    updated = source.with_verification_status(SourceVerificationStatus.AUTOMATICALLY_CHECKED)
    store.save(updated)
    fetched = store.get(source.source_id)
    assert fetched is not None
    assert fetched.verification_status == SourceVerificationStatus.AUTOMATICALLY_CHECKED

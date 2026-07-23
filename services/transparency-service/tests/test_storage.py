"""Tests for epd2_transparency_service.storage's in-memory reference
adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_transparency_service.domain import (
    LEDGER_GENESIS_HASH,
    AuditExportPackage,
    AuditExportPackageStatus,
    DisclosurePolicy,
    DisclosurePolicyStatus,
    IncludedTargetType,
    LedgerSubjectType,
    PublicLedgerEntry,
    PublicLedgerEntryStatus,
)
from epd2_transparency_service.exceptions import (
    AuditExportPackageConflictError,
    DisclosurePolicyConflictError,
    PublicLedgerEntryConflictError,
)
from epd2_transparency_service.storage import (
    InMemoryAuditExportPackageStore,
    InMemoryDisclosurePolicyStore,
    InMemoryPublicLedgerEntryStore,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)


def _entry(**overrides: object) -> PublicLedgerEntry:
    defaults: dict[str, object] = dict(
        public_ledger_entry_id=uuid4(),
        subject_type=LedgerSubjectType.INITIATIVE,
        subject_id=uuid4(),
        subject_event_id=uuid4(),
        published_at=_NOW,
        published_by_role_id=uuid4(),
        content_snapshot={"title": "x"},
        content_hash="a" * 64,
        previous_entry_hash=LEDGER_GENESIS_HASH,
        disclosure_policy_id=uuid4(),
        redaction_notice=None,
        supersedes_entry_id=None,
        status=PublicLedgerEntryStatus.PUBLISHED,
    )
    defaults.update(overrides)
    return PublicLedgerEntry(**defaults)  # type: ignore[arg-type]


def test_ledger_entry_store_head_hash_starts_at_genesis() -> None:
    store = InMemoryPublicLedgerEntryStore()
    assert store.head_hash() == LEDGER_GENESIS_HASH


def test_ledger_entry_store_head_hash_tracks_creation_order() -> None:
    store = InMemoryPublicLedgerEntryStore()
    first = _entry(content_hash="a" * 64)
    store.create(first)
    assert store.head_hash() == "a" * 64
    second = _entry(content_hash="b" * 64)
    store.create(second)
    assert store.head_hash() == "b" * 64


def test_ledger_entry_store_create_is_idempotent_by_content() -> None:
    store = InMemoryPublicLedgerEntryStore()
    entry = _entry()
    first = store.create(entry)
    second = store.create(entry)
    assert first == second


def test_ledger_entry_store_create_conflict_on_different_content() -> None:
    store = InMemoryPublicLedgerEntryStore()
    entry_id = uuid4()
    store.create(_entry(public_ledger_entry_id=entry_id, content_hash="a" * 64))
    with pytest.raises(PublicLedgerEntryConflictError):
        store.create(_entry(public_ledger_entry_id=entry_id, content_hash="b" * 64))


def test_ledger_entry_store_get_by_subject_event_id() -> None:
    store = InMemoryPublicLedgerEntryStore()
    subject_event_id = uuid4()
    entry = _entry(subject_event_id=subject_event_id)
    store.create(entry)
    found = store.get_by_subject_event_id(subject_event_id)
    assert found == entry
    assert store.get_by_subject_event_id(uuid4()) is None


def _package(**overrides: object) -> AuditExportPackage:
    defaults: dict[str, object] = dict(
        audit_export_package_id=uuid4(),
        scope_description="test",
        requested_by_role_id=uuid4(),
        included_target_types=(IncludedTargetType.INITIATIVE,),
        event_count=0,
        chain_proof=(),
        package_digest="c" * 64,
        integrity_proof="d" * 64,
        generated_at=_NOW,
        redaction_notice=None,
        supersedes_package_id=None,
        status=AuditExportPackageStatus.GENERATED,
    )
    defaults.update(overrides)
    return AuditExportPackage(**defaults)  # type: ignore[arg-type]


def test_audit_export_package_store_create_conflict() -> None:
    store = InMemoryAuditExportPackageStore()
    package_id = uuid4()
    store.create(_package(audit_export_package_id=package_id, scope_description="v1"))
    with pytest.raises(AuditExportPackageConflictError):
        store.create(_package(audit_export_package_id=package_id, scope_description="v2"))


def test_audit_export_package_store_save_persists_status_change() -> None:
    store = InMemoryAuditExportPackageStore()
    package = _package()
    store.create(package)
    updated = package.with_status(AuditExportPackageStatus.PUBLISHED)
    store.save(updated)
    assert store.get(package.audit_export_package_id) == updated


def _policy(**overrides: object) -> DisclosurePolicy:
    defaults: dict[str, object] = dict(
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="initiative",
        field_rules=(),
        small_cell_threshold=10,
        effective_from=_NOW,
        approved_by_role_id=None,
        version=1,
        status=DisclosurePolicyStatus.DRAFT,
    )
    defaults.update(overrides)
    return DisclosurePolicy(**defaults)  # type: ignore[arg-type]


def test_disclosure_policy_store_conflict() -> None:
    store = InMemoryDisclosurePolicyStore()
    policy_id = uuid4()
    store.create(_policy(disclosure_policy_id=policy_id, version=1))
    with pytest.raises(DisclosurePolicyConflictError):
        store.create(_policy(disclosure_policy_id=policy_id, version=2))


def test_disclosure_policy_store_tracks_active_by_subject_type() -> None:
    store = InMemoryDisclosurePolicyStore()
    policy = _policy(approved_by_role_id=uuid4(), status=DisclosurePolicyStatus.DRAFT)
    store.create(policy)
    assert store.get_active_for_subject_type("initiative") is None
    active = policy.with_status(DisclosurePolicyStatus.ACTIVE, approved_by_role_id=uuid4())
    store.save(active)
    found = store.get_active_for_subject_type("initiative")
    assert found is not None
    assert found.disclosure_policy_id == policy.disclosure_policy_id
    superseded = active.with_status(DisclosurePolicyStatus.SUPERSEDED)
    store.save(superseded)
    assert store.get_active_for_subject_type("initiative") is None

"""Tests for epd2_transparency_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_transparency_service.domain import (
    LEDGER_GENESIS_HASH,
    AuditExportPackage,
    AuditExportPackageStatus,
    ChainProofItem,
    DisclosureClass,
    DisclosurePolicy,
    DisclosurePolicyStatus,
    FieldRule,
    ForbiddenAuditExportPackageTransitionError,
    ForbiddenDisclosurePolicyTransitionError,
    ForbiddenLobbyLogEntryTransitionError,
    IncludedTargetType,
    LedgerSubjectType,
    LobbyLogContactMethod,
    LobbyLogEntry,
    LobbyLogEntryStatus,
    LobbyLogRelatedSubjectType,
    PublicLedgerEntry,
    PublicLedgerEntryStatus,
    Transformation,
    apply_disclosure_policy,
    assert_no_forbidden_fields,
    band_small_cell_value,
    is_within_publication_deadline,
    resolve_field_rule,
)

_NOW = datetime(2026, 1, 5, tzinfo=UTC)


def test_public_ledger_entry_rejects_forbidden_content_field() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        PublicLedgerEntry(
            public_ledger_entry_id=uuid4(),
            subject_type=LedgerSubjectType.INITIATIVE,
            subject_id=uuid4(),
            subject_event_id=uuid4(),
            published_at=_NOW,
            published_by_role_id=uuid4(),
            content_snapshot={"account_id": str(uuid4())},
            content_hash="a" * 64,
            previous_entry_hash=LEDGER_GENESIS_HASH,
            disclosure_policy_id=uuid4(),
            redaction_notice=None,
            supersedes_entry_id=None,
            status=PublicLedgerEntryStatus.PUBLISHED,
        )


def test_public_ledger_entry_has_no_transition_helper() -> None:
    """There is no `with_status`/transition table for this entity at all
    (canon section 19a.1) — it is constructed once, already `published`."""
    entry = PublicLedgerEntry(
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
    assert not hasattr(entry, "with_status")


def _chain_proof_item(position: int, event_hash: str, previous: str) -> ChainProofItem:
    return ChainProofItem(
        event_hash=event_hash,
        previous_event_hash=previous,
        event_type="initiative.published",
        occurred_at=_NOW,
        target_type="initiative",
        target_id=uuid4(),
        action="publish_initiative",
        reason_code="INITIATIVE_PUBLISHED",
        correlation_id=uuid4(),
        source_service="initiative-service",
        sequence_position=position,
    )


def test_audit_export_package_rejects_non_contiguous_sequence_positions() -> None:
    items = (
        _chain_proof_item(1, "a" * 64, "0" * 64),
        _chain_proof_item(3, "b" * 64, "a" * 64),
    )
    with pytest.raises(ValueError, match="contiguous"):
        AuditExportPackage(
            audit_export_package_id=uuid4(),
            scope_description="test",
            requested_by_role_id=uuid4(),
            included_target_types=(IncludedTargetType.INITIATIVE,),
            event_count=2,
            chain_proof=items,
            package_digest="c" * 64,
            integrity_proof="d" * 64,
            generated_at=_NOW,
            redaction_notice=None,
            supersedes_package_id=None,
            status=AuditExportPackageStatus.GENERATED,
        )


def _package(status: AuditExportPackageStatus) -> AuditExportPackage:
    return AuditExportPackage(
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
        status=status,
    )


def test_audit_export_package_allowed_transition() -> None:
    package = _package(AuditExportPackageStatus.GENERATED)
    updated = package.with_status(AuditExportPackageStatus.PUBLISHED)
    assert updated.status is AuditExportPackageStatus.PUBLISHED


def test_audit_export_package_forbidden_transition() -> None:
    package = _package(AuditExportPackageStatus.GENERATED)
    with pytest.raises(ForbiddenAuditExportPackageTransitionError):
        package.with_status(AuditExportPackageStatus.SUPERSEDED)


def test_audit_export_package_no_return_to_generated() -> None:
    package = _package(AuditExportPackageStatus.PUBLISHED)
    with pytest.raises(ForbiddenAuditExportPackageTransitionError):
        package.with_status(AuditExportPackageStatus.GENERATED)


def _policy(status: DisclosurePolicyStatus, approved: bool = False) -> DisclosurePolicy:
    return DisclosurePolicy(
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="initiative",
        field_rules=(),
        small_cell_threshold=10,
        effective_from=_NOW,
        approved_by_role_id=uuid4() if approved else None,
        version=1,
        status=status,
    )


def test_disclosure_policy_activation_requires_approver() -> None:
    policy = _policy(DisclosurePolicyStatus.DRAFT)
    with pytest.raises(ValueError, match="approved_by_role_id"):
        policy.with_status(DisclosurePolicyStatus.ACTIVE)


def test_disclosure_policy_activation_succeeds_with_approver() -> None:
    policy = _policy(DisclosurePolicyStatus.DRAFT)
    updated = policy.with_status(DisclosurePolicyStatus.ACTIVE, approved_by_role_id=uuid4())
    assert updated.status is DisclosurePolicyStatus.ACTIVE
    assert updated.approved_by_role_id is not None


def test_disclosure_policy_forbidden_transition() -> None:
    policy = _policy(DisclosurePolicyStatus.DRAFT)
    with pytest.raises(ForbiddenDisclosurePolicyTransitionError):
        policy.with_status(DisclosurePolicyStatus.SUPERSEDED)


def test_disclosure_policy_rejects_reclassifying_forbidden_field() -> None:
    with pytest.raises(ValueError, match="structurally forbidden"):
        DisclosurePolicy(
            disclosure_policy_id=uuid4(),
            applies_to_subject_type="initiative",
            field_rules=(FieldRule("account_id", DisclosureClass.PUBLIC, Transformation.NONE),),
            small_cell_threshold=10,
            effective_from=_NOW,
            approved_by_role_id=None,
            version=1,
            status=DisclosurePolicyStatus.DRAFT,
        )


def test_resolve_field_rule_defaults_to_prohibited_when_missing() -> None:
    policy = _policy(DisclosurePolicyStatus.ACTIVE, approved=True)
    rule = resolve_field_rule(policy, "not_a_configured_field")
    assert rule.disclosure_class is DisclosureClass.PROHIBITED


def test_resolve_field_rule_defaults_to_prohibited_when_ambiguous() -> None:
    policy = DisclosurePolicy(
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="initiative",
        field_rules=(
            FieldRule("title", DisclosureClass.PUBLIC, Transformation.NONE),
            FieldRule("title", DisclosureClass.REDACTED, Transformation.SUPPRESS),
        ),
        small_cell_threshold=10,
        effective_from=_NOW,
        approved_by_role_id=uuid4(),
        version=1,
        status=DisclosurePolicyStatus.ACTIVE,
    )
    rule = resolve_field_rule(policy, "title")
    assert rule.disclosure_class is DisclosureClass.PROHIBITED


def test_apply_disclosure_policy_drops_structurally_forbidden_field_unconditionally() -> None:
    policy = _policy(DisclosurePolicyStatus.ACTIVE, approved=True)
    result = apply_disclosure_policy(policy, {"account_id": str(uuid4()), "title": "x"})
    assert "account_id" not in result
    # 'title' has no configured rule either -> also dropped (fail-closed).
    assert "title" not in result


def test_apply_disclosure_policy_generalizes_to_role_scope() -> None:
    policy = DisclosurePolicy(
        disclosure_policy_id=uuid4(),
        applies_to_subject_type="moderation_decision",
        field_rules=(
            FieldRule(
                "decided_by",
                DisclosureClass.REDACTED,
                Transformation.GENERALIZE_TO_ROLE_SCOPE,
                replacement_label="moderator",
            ),
        ),
        small_cell_threshold=10,
        effective_from=_NOW,
        approved_by_role_id=uuid4(),
        version=1,
        status=DisclosurePolicyStatus.ACTIVE,
    )
    result = apply_disclosure_policy(policy, {"decided_by": str(uuid4())})
    assert result["decided_by"] == "moderator"


def test_band_small_cell_value() -> None:
    assert band_small_cell_value(0, 10) == 0
    assert band_small_cell_value(5, 10) == "1-9"
    assert band_small_cell_value(9, 10) == "1-9"
    assert band_small_cell_value(10, 10) == 10
    assert band_small_cell_value(500, 10) == 500


def test_assert_no_forbidden_fields_passes_for_clean_content() -> None:
    assert_no_forbidden_fields({"title": "x", "status": "published"})


def test_lobby_log_entry_transition_and_deadline() -> None:
    entry = LobbyLogEntry(
        lobby_log_entry_id=uuid4(),
        submitted_by_role_id=uuid4(),
        organization_name="Acme",
        related_subject_type=LobbyLogRelatedSubjectType.INITIATIVE,
        related_subject_id=uuid4(),
        contact_date=_NOW,
        contact_method=LobbyLogContactMethod.MEETING,
        topic_summary="topic",
        submitted_at=_NOW,
        published_at=None,
        supersedes_entry_id=None,
        status=LobbyLogEntryStatus.SUBMITTED,
    )
    assert is_within_publication_deadline(entry, _NOW)
    updated = entry.with_published(_NOW)
    assert updated.status is LobbyLogEntryStatus.PUBLISHED
    assert updated.published_at == _NOW
    with pytest.raises(ForbiddenLobbyLogEntryTransitionError):
        updated.with_published(_NOW)


def test_lobby_log_entry_requires_published_at_iff_published() -> None:
    with pytest.raises(ValueError, match="published_at"):
        LobbyLogEntry(
            lobby_log_entry_id=uuid4(),
            submitted_by_role_id=uuid4(),
            organization_name="Acme",
            related_subject_type=LobbyLogRelatedSubjectType.INITIATIVE,
            related_subject_id=uuid4(),
            contact_date=_NOW,
            contact_method=LobbyLogContactMethod.MEETING,
            topic_summary="topic",
            submitted_at=_NOW,
            published_at=None,
            supersedes_entry_id=None,
            status=LobbyLogEntryStatus.PUBLISHED,
        )

"""Tests for epd2_initiative_service.domain.

Covers every `ALLOWED_*_TRANSITIONS` pair (plus at least one forbidden
transition) for each of the five owned entities, `SupportRecord`'s
`FORBIDDEN_FIELD_NAMES` identity-separation guarantee, and the
deterministic content-hash helpers.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_initiative_service.domain import (
    ALLOWED_AMENDMENT_TRANSITIONS,
    ALLOWED_INITIATIVE_TRANSITIONS,
    ALLOWED_SOURCE_VERIFICATION_TRANSITIONS,
    ALLOWED_SUPPORT_TRANSITIONS,
    FORBIDDEN_FIELD_NAMES,
    Amendment,
    AmendmentStatus,
    Initiative,
    InitiativeStatus,
    InitiativeVersion,
    SourceRecord,
    SourceVerificationStatus,
    SupportRecord,
    SupportStatus,
    compute_initiative_version_content_hash,
    compute_source_record_content_hash,
    parse_amendment_status,
    parse_initiative_status,
    parse_source_verification_status,
    parse_support_status,
)
from epd2_initiative_service.exceptions import (
    ForbiddenAmendmentTransitionError,
    ForbiddenInitiativeTransitionError,
    ForbiddenSourceVerificationTransitionError,
    ForbiddenSupportTransitionError,
    UnknownAmendmentStatusError,
    UnknownInitiativeStatusError,
    UnknownSourceVerificationStatusError,
    UnknownSupportStatusError,
)

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_initiative(status: InitiativeStatus = InitiativeStatus.DRAFT) -> Initiative:
    return Initiative(
        initiative_id=uuid4(),
        space_id=uuid4(),
        current_version_id=uuid4(),
        author_actor_id=uuid4(),
        initiative_type="citizen_law",
        workflow_id=uuid4(),
        status=status,
        support_count=0,
        created_at=_NOW,
    )


def _make_support(status: SupportStatus = SupportStatus.ACTIVE) -> SupportRecord:
    return SupportRecord(
        support_record_id=uuid4(),
        initiative_id=uuid4(),
        support_actor_reference=uuid4(),
        credential_reference=uuid4(),
        created_at=_NOW,
        status=status,
    )


def _make_amendment(status: AmendmentStatus = AmendmentStatus.DRAFT) -> Amendment:
    return Amendment(
        amendment_id=uuid4(),
        initiative_id=uuid4(),
        target_version_id=uuid4(),
        proposer_actor_id=uuid4(),
        proposed_change="Change section 3",
        justification="Clarifies intent",
        status=status,
        decision_reference=None,
    )


def _make_source(
    status: SourceVerificationStatus = SourceVerificationStatus.UNVERIFIED,
) -> SourceRecord:
    return SourceRecord(
        source_id=uuid4(),
        source_type="report",
        title="Impact study",
        publisher="Institute",
        publication_date=_NOW,
        url="https://example.org/report",
        archive_reference=None,
        verification_status=status,
        added_by_actor_id=uuid4(),
        accessed_at=_NOW,
        content_hash="a" * 64,
        valid_until=None,
    )


# ---------------------------------------------------------------------------
# Initiative
# ---------------------------------------------------------------------------


def test_parse_initiative_status_accepts_known_values() -> None:
    assert parse_initiative_status("draft") == InitiativeStatus.DRAFT


def test_parse_initiative_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownInitiativeStatusError):
        parse_initiative_status("super_draft")


def test_initiative_status_enum_has_exactly_fifteen_values() -> None:
    assert len(list(InitiativeStatus)) == 15


def test_initiative_transition_table_has_exactly_28_edges() -> None:
    assert len(ALLOWED_INITIATIVE_TRANSITIONS) == 28


@pytest.mark.parametrize(
    "current,target", sorted(ALLOWED_INITIATIVE_TRANSITIONS, key=lambda p: (p[0], p[1]))
)
def test_every_allowed_initiative_transition_succeeds(
    current: InitiativeStatus, target: InitiativeStatus
) -> None:
    initiative = _make_initiative(status=current)
    updated = initiative.with_status(target)
    assert updated.status == target


def test_initiative_forbidden_transition_draft_to_qualified() -> None:
    initiative = _make_initiative(status=InitiativeStatus.DRAFT)
    with pytest.raises(ForbiddenInitiativeTransitionError):
        initiative.with_status(InitiativeStatus.QUALIFIED)


def test_initiative_archived_is_terminal() -> None:
    initiative = _make_initiative(status=InitiativeStatus.ARCHIVED)
    for target in InitiativeStatus:
        if target == InitiativeStatus.ARCHIVED:
            continue
        with pytest.raises(ForbiddenInitiativeTransitionError):
            initiative.with_status(target)


def test_initiative_voting_never_returns_to_ready_for_ballot() -> None:
    initiative = _make_initiative(status=InitiativeStatus.VOTING)
    with pytest.raises(ForbiddenInitiativeTransitionError):
        initiative.with_status(InitiativeStatus.READY_FOR_BALLOT)


def test_initiative_requires_timezone_aware_created_at() -> None:
    with pytest.raises(ValueError, match="created_at"):
        Initiative(
            initiative_id=uuid4(),
            space_id=uuid4(),
            current_version_id=None,
            author_actor_id=uuid4(),
            initiative_type="citizen_law",
            workflow_id=uuid4(),
            status=InitiativeStatus.DRAFT,
            support_count=0,
            created_at=datetime(2026, 1, 1),
        )


def test_initiative_rejects_negative_support_count() -> None:
    with pytest.raises(ValueError, match="support_count"):
        _make_initiative().with_support_count(-1)


def test_initiative_current_version_id_defaults_to_none_capable() -> None:
    initiative = Initiative(
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
    assert initiative.current_version_id is None
    updated = initiative.with_current_version_id(uuid4())
    assert updated.current_version_id is not None


# ---------------------------------------------------------------------------
# InitiativeVersion
# ---------------------------------------------------------------------------


def test_initiative_version_rejects_non_positive_version_number() -> None:
    with pytest.raises(ValueError, match="version_number"):
        InitiativeVersion(
            initiative_version_id=uuid4(),
            initiative_id=uuid4(),
            version_number=0,
            title="t",
            problem_statement="p",
            proposed_solution="s",
            affected_groups=(),
            expected_effects="e",
            risks="r",
            estimated_resources="res",
            legal_questions="lq",
            source_references=(),
            created_by_actor_id=uuid4(),
            content_hash="a" * 64,
        )


def test_compute_initiative_version_content_hash_is_deterministic() -> None:
    kwargs = dict(
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=("group_a", "group_b"),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(uuid4(),),
    )
    a = compute_initiative_version_content_hash(**kwargs)  # type: ignore[arg-type]
    b = compute_initiative_version_content_hash(**kwargs)  # type: ignore[arg-type]
    assert a == b
    assert isinstance(a, str)
    assert len(a) == 64


def test_compute_initiative_version_content_hash_changes_with_content() -> None:
    kwargs = dict(
        title="Title",
        problem_statement="Problem",
        proposed_solution="Solution",
        affected_groups=("group_a",),
        expected_effects="Effects",
        risks="Risks",
        estimated_resources="Resources",
        legal_questions="Questions",
        source_references=(),
    )
    a = compute_initiative_version_content_hash(**kwargs)  # type: ignore[arg-type]
    other_kwargs = {**kwargs, "title": "Different title"}
    b = compute_initiative_version_content_hash(**other_kwargs)  # type: ignore[arg-type]
    assert a != b


# ---------------------------------------------------------------------------
# SupportRecord
# ---------------------------------------------------------------------------


def test_parse_support_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownSupportStatusError):
        parse_support_status("super_active")


@pytest.mark.parametrize(
    "current,target", sorted(ALLOWED_SUPPORT_TRANSITIONS, key=lambda p: (p[0], p[1]))
)
def test_every_allowed_support_transition_succeeds(
    current: SupportStatus, target: SupportStatus
) -> None:
    support = _make_support(status=current)
    updated = support.with_status(target)
    assert updated.status == target


def test_support_withdrawn_is_terminal() -> None:
    support = _make_support(status=SupportStatus.WITHDRAWN)
    with pytest.raises(ForbiddenSupportTransitionError):
        support.with_status(SupportStatus.ACTIVE)


def test_support_invalidated_is_terminal() -> None:
    support = _make_support(status=SupportStatus.INVALIDATED)
    with pytest.raises(ForbiddenSupportTransitionError):
        support.with_status(SupportStatus.WITHDRAWN)


def test_support_record_never_has_forbidden_identity_fields() -> None:
    """INV-01/INV-03: `SupportRecord` may only ever carry opaque
    references, never a direct account/person/identity-record link."""
    field_names = set(SupportRecord.__dataclass_fields__)
    assert field_names & FORBIDDEN_FIELD_NAMES == set()


def test_support_record_requires_timezone_aware_created_at() -> None:
    with pytest.raises(ValueError, match="created_at"):
        SupportRecord(
            support_record_id=uuid4(),
            initiative_id=uuid4(),
            support_actor_reference=uuid4(),
            credential_reference=uuid4(),
            created_at=datetime(2026, 1, 1),
            status=SupportStatus.ACTIVE,
        )


# ---------------------------------------------------------------------------
# Amendment
# ---------------------------------------------------------------------------


def test_parse_amendment_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownAmendmentStatusError):
        parse_amendment_status("super_draft")


def test_amendment_transition_table_has_exactly_11_edges() -> None:
    assert len(ALLOWED_AMENDMENT_TRANSITIONS) == 11


@pytest.mark.parametrize(
    "current,target", sorted(ALLOWED_AMENDMENT_TRANSITIONS, key=lambda p: (p[0], p[1]))
)
def test_every_allowed_amendment_transition_succeeds(
    current: AmendmentStatus, target: AmendmentStatus
) -> None:
    amendment = _make_amendment(status=current)
    updated = amendment.with_status(target)
    assert updated.status == target


def test_amendment_accepted_is_terminal() -> None:
    amendment = _make_amendment(status=AmendmentStatus.ACCEPTED)
    with pytest.raises(ForbiddenAmendmentTransitionError):
        amendment.with_status(AmendmentStatus.WITHDRAWN)


def test_amendment_draft_cannot_jump_to_accepted() -> None:
    amendment = _make_amendment(status=AmendmentStatus.DRAFT)
    with pytest.raises(ForbiddenAmendmentTransitionError):
        amendment.with_status(AmendmentStatus.ACCEPTED)


def test_amendment_with_decision_reference() -> None:
    amendment = _make_amendment(status=AmendmentStatus.DRAFT)
    ref = uuid4()
    updated = amendment.with_decision_reference(ref)
    assert updated.decision_reference == ref
    assert amendment.decision_reference is None


# ---------------------------------------------------------------------------
# SourceRecord
# ---------------------------------------------------------------------------


def test_parse_source_verification_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownSourceVerificationStatusError):
        parse_source_verification_status("super_checked")


def test_source_verification_transition_table_has_exactly_13_edges() -> None:
    assert len(ALLOWED_SOURCE_VERIFICATION_TRANSITIONS) == 13


@pytest.mark.parametrize(
    "current,target", sorted(ALLOWED_SOURCE_VERIFICATION_TRANSITIONS, key=lambda p: (p[0], p[1]))
)
def test_every_allowed_source_verification_transition_succeeds(
    current: SourceVerificationStatus, target: SourceVerificationStatus
) -> None:
    source = _make_source(status=current)
    updated = source.with_verification_status(target)
    assert updated.verification_status == target


def test_source_unavailable_has_no_outgoing_edges() -> None:
    source = _make_source(status=SourceVerificationStatus.UNAVAILABLE)
    for target in SourceVerificationStatus:
        if target == SourceVerificationStatus.UNAVAILABLE:
            continue
        with pytest.raises(ForbiddenSourceVerificationTransitionError):
            source.with_verification_status(target)


def test_source_outdated_has_no_outgoing_edges() -> None:
    source = _make_source(status=SourceVerificationStatus.OUTDATED)
    for target in SourceVerificationStatus:
        if target == SourceVerificationStatus.OUTDATED:
            continue
        with pytest.raises(ForbiddenSourceVerificationTransitionError):
            source.with_verification_status(target)


def test_source_disputed_can_reach_human_checked() -> None:
    """Canon 12.1's sole reverse edge: a human review can resolve a
    dispute."""
    source = _make_source(status=SourceVerificationStatus.DISPUTED)
    updated = source.with_verification_status(SourceVerificationStatus.HUMAN_CHECKED)
    assert updated.verification_status == SourceVerificationStatus.HUMAN_CHECKED


def test_source_requires_timezone_aware_accessed_at() -> None:
    with pytest.raises(ValueError, match="accessed_at"):
        SourceRecord(
            source_id=uuid4(),
            source_type="report",
            title="t",
            publisher="p",
            publication_date=None,
            url="https://example.org",
            archive_reference=None,
            verification_status=SourceVerificationStatus.UNVERIFIED,
            added_by_actor_id=uuid4(),
            accessed_at=datetime(2026, 1, 1),
            content_hash="a" * 64,
            valid_until=None,
        )


def test_compute_source_record_content_hash_is_deterministic() -> None:
    kwargs = dict(
        source_type="report",
        title="Impact study",
        publisher="Institute",
        publication_date=_NOW,
        url="https://example.org/report",
        archive_reference=None,
    )
    a = compute_source_record_content_hash(**kwargs)  # type: ignore[arg-type]
    b = compute_source_record_content_hash(**kwargs)  # type: ignore[arg-type]
    assert a == b
    assert len(a) == 64


def test_compute_source_record_content_hash_changes_with_url() -> None:
    kwargs = dict(
        source_type="report",
        title="Impact study",
        publisher="Institute",
        publication_date=_NOW,
        url="https://example.org/report",
        archive_reference=None,
    )
    a = compute_source_record_content_hash(**kwargs)  # type: ignore[arg-type]
    other_kwargs = {**kwargs, "url": "https://example.org/other"}
    b = compute_source_record_content_hash(**other_kwargs)  # type: ignore[arg-type]
    assert a != b


def test_source_valid_until_and_publication_date_may_be_none() -> None:
    source = _make_source()
    updated = replace(source, publication_date=None, valid_until=None)
    assert updated.publication_date is None
    assert updated.valid_until is None


def test_source_rejects_naive_publication_date() -> None:
    with pytest.raises(ValueError, match="publication_date"):
        SourceRecord(
            source_id=uuid4(),
            source_type="report",
            title="t",
            publisher="p",
            publication_date=datetime(2026, 1, 1),
            url="https://example.org",
            archive_reference=None,
            verification_status=SourceVerificationStatus.UNVERIFIED,
            added_by_actor_id=uuid4(),
            accessed_at=_NOW,
            content_hash="a" * 64,
            valid_until=None,
        )

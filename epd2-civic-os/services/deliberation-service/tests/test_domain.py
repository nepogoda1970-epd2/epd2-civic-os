"""Tests for epd2_deliberation_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_deliberation_service.domain import (
    ALLOWED_DISCUSSION_TRANSITIONS,
    ALLOWED_VISIBILITY_TRANSITIONS,
    Contribution,
    ContributionType,
    ContributionVisibilityStatus,
    Discussion,
    DiscussionStatus,
    assert_contribution_visibility_transition_allowed,
    assert_discussion_transition_allowed,
    compute_contribution_content_hash,
    parse_contribution_type,
    parse_discussion_status,
    parse_visibility_status,
)
from epd2_deliberation_service.exceptions import (
    ForbiddenContributionVisibilityTransitionError,
    ForbiddenDiscussionTransitionError,
    UnknownContributionTypeError,
    UnknownContributionVisibilityStatusError,
    UnknownDiscussionStatusError,
)

# --- Discussion -----------------------------------------------------------


def _make_discussion(**overrides: object) -> Discussion:
    defaults: dict[str, object] = {
        "discussion_id": uuid4(),
        "subject_type": "initiative",
        "subject_id": uuid4(),
        "space_id": uuid4(),
        "status": DiscussionStatus.OPEN,
        "moderation_policy_id": None,
    }
    defaults.update(overrides)
    return Discussion(**defaults)  # type: ignore[arg-type]


def test_parse_discussion_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownDiscussionStatusError):
        parse_discussion_status("eternal")


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (DiscussionStatus.OPEN, DiscussionStatus.LIMITED),
        (DiscussionStatus.OPEN, DiscussionStatus.READ_ONLY),
        (DiscussionStatus.OPEN, DiscussionStatus.CLOSED),
        (DiscussionStatus.LIMITED, DiscussionStatus.OPEN),
        (DiscussionStatus.LIMITED, DiscussionStatus.READ_ONLY),
        (DiscussionStatus.LIMITED, DiscussionStatus.CLOSED),
        (DiscussionStatus.READ_ONLY, DiscussionStatus.OPEN),
        (DiscussionStatus.READ_ONLY, DiscussionStatus.CLOSED),
        (DiscussionStatus.CLOSED, DiscussionStatus.ARCHIVED),
    ],
)
def test_every_canon_discussion_transition_is_allowed(
    current: DiscussionStatus, target: DiscussionStatus
) -> None:
    assert_discussion_transition_allowed(current, target)


def test_archived_is_terminal() -> None:
    """CT-00-03: archived has no outgoing transition."""
    for status in DiscussionStatus:
        assert (DiscussionStatus.ARCHIVED, status) not in ALLOWED_DISCUSSION_TRANSITIONS


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (DiscussionStatus.CLOSED, DiscussionStatus.OPEN),
        (DiscussionStatus.ARCHIVED, DiscussionStatus.OPEN),
        (DiscussionStatus.OPEN, DiscussionStatus.ARCHIVED),
        (DiscussionStatus.OPEN, DiscussionStatus.OPEN),
    ],
)
def test_forbidden_discussion_transitions_are_rejected(
    current: DiscussionStatus, target: DiscussionStatus
) -> None:
    with pytest.raises(ForbiddenDiscussionTransitionError):
        assert_discussion_transition_allowed(current, target)


def test_discussion_with_status_transitions() -> None:
    discussion = _make_discussion(status=DiscussionStatus.OPEN)
    closed = discussion.with_status(DiscussionStatus.CLOSED)
    assert closed.status == DiscussionStatus.CLOSED
    assert discussion.status == DiscussionStatus.OPEN  # original unchanged


def test_discussion_with_status_rejects_forbidden_transition() -> None:
    discussion = _make_discussion(status=DiscussionStatus.CLOSED)
    with pytest.raises(ForbiddenDiscussionTransitionError):
        discussion.with_status(DiscussionStatus.OPEN)


def test_discussion_rejects_empty_subject_type() -> None:
    with pytest.raises(ValueError, match="subject_type"):
        _make_discussion(subject_type="")


# --- Contribution -----------------------------------------------------------


def _make_contribution(**overrides: object) -> Contribution:
    content_value = overrides.pop("content", "hello world")
    assert isinstance(content_value, str)
    content: str = content_value

    contribution_type_value = overrides.pop("contribution_type", ContributionType.COMMENT)
    assert isinstance(contribution_type_value, ContributionType)
    contribution_type: ContributionType = contribution_type_value

    content_hash = overrides.pop(
        "content_hash",
        compute_contribution_content_hash(
            content=content,
            contribution_type=contribution_type,
        ),
    )
    defaults: dict[str, object] = {
        "contribution_id": uuid4(),
        "discussion_id": uuid4(),
        "author_actor_id": uuid4(),
        "parent_contribution_id": None,
        "contribution_type": contribution_type,
        "content": content,
        "content_hash": content_hash,
        "visibility_status": ContributionVisibilityStatus.VISIBLE,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "edited_version": 1,
    }
    defaults.update(overrides)
    return Contribution(**defaults)  # type: ignore[arg-type]


def test_parse_contribution_type_rejects_unknown_value() -> None:
    with pytest.raises(UnknownContributionTypeError):
        parse_contribution_type("rant")


def test_parse_visibility_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownContributionVisibilityStatusError):
        parse_visibility_status("gone")


def test_compute_contribution_content_hash_is_deterministic() -> None:
    first = compute_contribution_content_hash(
        content="hello", contribution_type=ContributionType.COMMENT
    )
    second = compute_contribution_content_hash(
        content="hello", contribution_type=ContributionType.COMMENT
    )
    assert first == second


def test_compute_contribution_content_hash_changes_with_content() -> None:
    first = compute_contribution_content_hash(
        content="hello", contribution_type=ContributionType.COMMENT
    )
    second = compute_contribution_content_hash(
        content="goodbye", contribution_type=ContributionType.COMMENT
    )
    assert first != second


def test_contribution_rejects_mismatched_content_hash() -> None:
    with pytest.raises(ValueError, match="content_hash"):
        _make_contribution(content_hash="0" * 64)


def test_contribution_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="content"):
        _make_contribution(content="")


def test_contribution_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError, match="created_at"):
        _make_contribution(created_at=datetime(2026, 1, 1))


def test_contribution_rejects_edited_version_below_one() -> None:
    with pytest.raises(ValueError, match="edited_version"):
        _make_contribution(edited_version=0)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ContributionVisibilityStatus.VISIBLE,
            ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
        ),
        (ContributionVisibilityStatus.VISIBLE, ContributionVisibilityStatus.RESTRICTED),
        (
            ContributionVisibilityStatus.VISIBLE,
            ContributionVisibilityStatus.REMOVED_FROM_PUBLIC_VIEW,
        ),
        (
            ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
            ContributionVisibilityStatus.RESTORED,
        ),
        (ContributionVisibilityStatus.RESTRICTED, ContributionVisibilityStatus.RESTORED),
        (
            ContributionVisibilityStatus.REMOVED_FROM_PUBLIC_VIEW,
            ContributionVisibilityStatus.RESTORED,
        ),
        (ContributionVisibilityStatus.RESTORED, ContributionVisibilityStatus.VISIBLE),
    ],
)
def test_every_canon_visibility_transition_is_allowed(
    current: ContributionVisibilityStatus, target: ContributionVisibilityStatus
) -> None:
    assert_contribution_visibility_transition_allowed(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ContributionVisibilityStatus.VISIBLE, ContributionVisibilityStatus.RESTORED),
        (
            ContributionVisibilityStatus.TEMPORARILY_HIDDEN,
            ContributionVisibilityStatus.VISIBLE,
        ),
        (ContributionVisibilityStatus.RESTRICTED, ContributionVisibilityStatus.VISIBLE),
        (
            ContributionVisibilityStatus.REMOVED_FROM_PUBLIC_VIEW,
            ContributionVisibilityStatus.RESTRICTED,
        ),
        (ContributionVisibilityStatus.VISIBLE, ContributionVisibilityStatus.VISIBLE),
    ],
)
def test_forbidden_visibility_transitions_are_rejected(
    current: ContributionVisibilityStatus, target: ContributionVisibilityStatus
) -> None:
    with pytest.raises(ForbiddenContributionVisibilityTransitionError):
        assert_contribution_visibility_transition_allowed(current, target)


def test_no_visibility_status_has_an_outgoing_transition_other_than_the_canon_table() -> None:
    """Sanity check that the transition set has exactly the 7 canon edges."""
    assert len(ALLOWED_VISIBILITY_TRANSITIONS) == 7


def test_contribution_with_visibility_status_transitions() -> None:
    contribution = _make_contribution(visibility_status=ContributionVisibilityStatus.VISIBLE)
    hidden = contribution.with_visibility_status(ContributionVisibilityStatus.TEMPORARILY_HIDDEN)
    assert hidden.visibility_status == ContributionVisibilityStatus.TEMPORARILY_HIDDEN
    assert contribution.visibility_status == ContributionVisibilityStatus.VISIBLE  # unchanged


def test_contribution_with_edited_content_increments_version_and_recomputes_hash() -> None:
    contribution = _make_contribution(content="v1", edited_version=1)
    edited = contribution.with_edited_content("v2")
    assert edited.content == "v2"
    assert edited.edited_version == 2
    assert edited.content_hash == compute_contribution_content_hash(
        content="v2", contribution_type=contribution.contribution_type
    )
    assert edited.visibility_status == contribution.visibility_status  # unchanged by edit
    assert contribution.content == "v1"  # original unchanged

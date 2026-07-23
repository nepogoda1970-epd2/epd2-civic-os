"""Tests for epd2_deliberation_service.storage."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_deliberation_service.domain import (
    Contribution,
    ContributionType,
    ContributionVisibilityStatus,
    Discussion,
    DiscussionStatus,
    compute_contribution_content_hash,
)
from epd2_deliberation_service.exceptions import (
    ContributionCreationConflictError,
    DiscussionCreationConflictError,
)
from epd2_deliberation_service.storage import InMemoryContributionStore, InMemoryDiscussionStore


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


def _make_contribution(**overrides: object) -> Contribution:
    content_value = overrides.pop("content", "hello world")
    assert isinstance(content_value, str)
    content: str = content_value

    contribution_type_value = overrides.pop("contribution_type", ContributionType.COMMENT)
    assert isinstance(contribution_type_value, ContributionType)
    contribution_type: ContributionType = contribution_type_value

    defaults: dict[str, object] = {
        "contribution_id": uuid4(),
        "discussion_id": uuid4(),
        "author_actor_id": uuid4(),
        "parent_contribution_id": None,
        "contribution_type": contribution_type,
        "content": content,
        "content_hash": compute_contribution_content_hash(
            content=content,
            contribution_type=contribution_type,
        ),
        "visibility_status": ContributionVisibilityStatus.VISIBLE,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "edited_version": 1,
    }
    defaults.update(overrides)
    return Contribution(**defaults)  # type: ignore[arg-type]


# --- DiscussionStore --------------------------------------------------------


def test_create_then_get_returns_stored_discussion() -> None:
    store = InMemoryDiscussionStore()
    discussion = _make_discussion()
    stored = store.create(discussion)
    assert store.get(discussion.discussion_id) == stored


def test_idempotent_create_of_identical_discussion_succeeds() -> None:
    store = InMemoryDiscussionStore()
    discussion = _make_discussion()
    first = store.create(discussion)
    second = store.create(discussion)
    assert first == second


def test_conflicting_discussion_creation_is_rejected() -> None:
    store = InMemoryDiscussionStore()
    discussion = _make_discussion()
    store.create(discussion)
    conflicting = _make_discussion(discussion_id=discussion.discussion_id, subject_type="different")
    with pytest.raises(DiscussionCreationConflictError):
        store.create(conflicting)


def test_save_persists_a_status_update() -> None:
    store = InMemoryDiscussionStore()
    discussion = _make_discussion()
    store.create(discussion)
    updated = discussion.with_status(DiscussionStatus.CLOSED)
    store.save(updated)
    assert store.get(discussion.discussion_id) == updated


def test_get_unknown_discussion_returns_none() -> None:
    store = InMemoryDiscussionStore()
    assert store.get(uuid4()) is None


# --- ContributionStore -------------------------------------------------------


def test_create_then_get_returns_stored_contribution() -> None:
    store = InMemoryContributionStore()
    contribution = _make_contribution()
    stored = store.create(contribution)
    assert store.get(contribution.contribution_id) == stored


def test_idempotent_create_of_identical_contribution_succeeds() -> None:
    store = InMemoryContributionStore()
    contribution = _make_contribution()
    first = store.create(contribution)
    second = store.create(contribution)
    assert first == second


def test_conflicting_contribution_creation_is_rejected() -> None:
    store = InMemoryContributionStore()
    contribution = _make_contribution()
    store.create(contribution)
    conflicting = _make_contribution(
        contribution_id=contribution.contribution_id, content="something else"
    )
    with pytest.raises(ContributionCreationConflictError):
        store.create(conflicting)


def test_list_by_discussion_filters_correctly() -> None:
    store = InMemoryContributionStore()
    discussion_a = uuid4()
    discussion_b = uuid4()
    c1 = store.create(_make_contribution(discussion_id=discussion_a))
    c2 = store.create(_make_contribution(discussion_id=discussion_a, content="second"))
    store.create(_make_contribution(discussion_id=discussion_b, content="third"))
    results = store.list_by_discussion(discussion_a)
    assert set(results) == {c1, c2}


def test_get_unknown_contribution_returns_none() -> None:
    store = InMemoryContributionStore()
    assert store.get(uuid4()) is None

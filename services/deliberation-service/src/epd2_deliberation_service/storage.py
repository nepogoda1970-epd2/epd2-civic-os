"""Storage protocols and in-memory reference adapters for Deliberation
Service's two owned entities.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from epd2_deliberation_service.domain import Contribution, Discussion
from epd2_deliberation_service.exceptions import (
    ContributionCreationConflictError,
    DiscussionCreationConflictError,
)


class DiscussionStore(Protocol):
    def create(self, discussion: Discussion) -> Discussion:
        """Store a newly opened discussion. If `discussion.discussion_id`
        already exists with identical content, returns the existing
        record (idempotent). If it exists with different content, raises
        `DiscussionCreationConflictError`.
        """
        ...

    def save(self, discussion: Discussion) -> None:
        """Persist an update to an already-created discussion (e.g. after
        a status transition)."""
        ...

    def get(self, discussion_id: UUID) -> Discussion | None: ...


class ContributionStore(Protocol):
    def create(self, contribution: Contribution) -> Contribution:
        """Store a newly created contribution. If
        `contribution.contribution_id` already exists with identical
        content, returns the existing record (idempotent). If it exists
        with different content, raises `ContributionCreationConflictError`.
        """
        ...

    def save(self, contribution: Contribution) -> None:
        """Persist an update to an already-created contribution (e.g.
        after an edit or a visibility-status transition)."""
        ...

    def get(self, contribution_id: UUID) -> Contribution | None: ...

    def list_by_discussion(self, discussion_id: UUID) -> tuple[Contribution, ...]: ...


class InMemoryDiscussionStore:
    def __init__(self) -> None:
        self._discussions: dict[UUID, Discussion] = {}

    def create(self, discussion: Discussion) -> Discussion:
        existing = self._discussions.get(discussion.discussion_id)
        if existing is not None:
            if existing == discussion:
                return existing
            raise DiscussionCreationConflictError(
                f"discussion_id {discussion.discussion_id} already exists with different content"
            )
        self._discussions[discussion.discussion_id] = discussion
        return discussion

    def save(self, discussion: Discussion) -> None:
        self._discussions[discussion.discussion_id] = discussion

    def get(self, discussion_id: UUID) -> Discussion | None:
        return self._discussions.get(discussion_id)


class InMemoryContributionStore:
    def __init__(self) -> None:
        self._contributions: dict[UUID, Contribution] = {}

    def create(self, contribution: Contribution) -> Contribution:
        existing = self._contributions.get(contribution.contribution_id)
        if existing is not None:
            if existing == contribution:
                return existing
            raise ContributionCreationConflictError(
                f"contribution_id {contribution.contribution_id} already exists "
                "with different content"
            )
        self._contributions[contribution.contribution_id] = contribution
        return contribution

    def save(self, contribution: Contribution) -> None:
        self._contributions[contribution.contribution_id] = contribution

    def get(self, contribution_id: UUID) -> Contribution | None:
        return self._contributions.get(contribution_id)

    def list_by_discussion(self, discussion_id: UUID) -> tuple[Contribution, ...]:
        return tuple(c for c in self._contributions.values() if c.discussion_id == discussion_id)

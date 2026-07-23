"""`Discussion` and `Contribution`, per
`docs/canonical/TZ-00-domain-event-canon.md`, sections 13.1 and 13.2.

Canon already names one owner ("Discussion Service") for both entities -
no cross-pack consolidation judgment call was needed (ADR-005 section 3
item 2). Per ADR-008, this service has no PACK-02 dependency: it imports
nothing from `epd2_credential_service`, `epd2_eligibility_service`, or
`epd2_identity_service`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_deliberation_service.exceptions import (
    ForbiddenContributionVisibilityTransitionError,
    ForbiddenDiscussionTransitionError,
    UnknownContributionTypeError,
    UnknownContributionVisibilityStatusError,
    UnknownDiscussionStatusError,
)

# --- Discussion (canon 13.1) ---------------------------------------------


class DiscussionStatus(StrEnum):
    """Canon section 13.1's exact status list."""

    OPEN = "open"
    LIMITED = "limited"
    READ_ONLY = "read_only"
    CLOSED = "closed"
    ARCHIVED = "archived"


def parse_discussion_status(value: str) -> DiscussionStatus:
    try:
        return DiscussionStatus(value)
    except ValueError as exc:
        raise UnknownDiscussionStatusError(f"unknown discussion status: {value!r}") from exc


#: Canon section 13.1's transition table. `archived` is terminal (no
#: outgoing transition) - reached only from `closed`.
ALLOWED_DISCUSSION_TRANSITIONS: frozenset[tuple[DiscussionStatus, DiscussionStatus]] = frozenset(
    {
        (DiscussionStatus.OPEN, DiscussionStatus.LIMITED),
        (DiscussionStatus.OPEN, DiscussionStatus.READ_ONLY),
        (DiscussionStatus.OPEN, DiscussionStatus.CLOSED),
        (DiscussionStatus.LIMITED, DiscussionStatus.OPEN),
        (DiscussionStatus.LIMITED, DiscussionStatus.READ_ONLY),
        (DiscussionStatus.LIMITED, DiscussionStatus.CLOSED),
        (DiscussionStatus.READ_ONLY, DiscussionStatus.OPEN),
        (DiscussionStatus.READ_ONLY, DiscussionStatus.CLOSED),
        (DiscussionStatus.CLOSED, DiscussionStatus.ARCHIVED),
    }
)


def assert_discussion_transition_allowed(
    current: DiscussionStatus, target: DiscussionStatus
) -> None:
    if (current, target) not in ALLOWED_DISCUSSION_TRANSITIONS:
        raise ForbiddenDiscussionTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Discussion:
    """Canon section 13.1 fields exactly."""

    discussion_id: UUID
    subject_type: str
    subject_id: UUID
    space_id: UUID
    status: DiscussionStatus
    moderation_policy_id: UUID | None

    def __post_init__(self) -> None:
        if not self.subject_type:
            raise ValueError("subject_type must not be empty")

    def with_status(self, new_status: DiscussionStatus) -> Discussion:
        assert_discussion_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)


# --- Contribution (canon 13.2) -------------------------------------------


class ContributionType(StrEnum):
    """Canon section 13.2's exact type list. A separate enum from
    `ContributionVisibilityStatus` below - `contribution_type` never
    changes after creation, unlike `visibility_status`."""

    COMMENT = "comment"
    ARGUMENT_FOR = "argument_for"
    ARGUMENT_AGAINST = "argument_against"
    QUESTION = "question"
    ANSWER = "answer"
    PROPOSAL = "proposal"
    SOURCE_NOTE = "source_note"
    MODERATOR_NOTICE = "moderator_notice"


def parse_contribution_type(value: str) -> ContributionType:
    try:
        return ContributionType(value)
    except ValueError as exc:
        raise UnknownContributionTypeError(f"unknown contribution_type: {value!r}") from exc


class ContributionVisibilityStatus(StrEnum):
    """Canon section 13.2's exact visibility-status list."""

    VISIBLE = "visible"
    TEMPORARILY_HIDDEN = "temporarily_hidden"
    RESTRICTED = "restricted"
    REMOVED_FROM_PUBLIC_VIEW = "removed_from_public_view"
    RESTORED = "restored"


def parse_visibility_status(value: str) -> ContributionVisibilityStatus:
    try:
        return ContributionVisibilityStatus(value)
    except ValueError as exc:
        raise UnknownContributionVisibilityStatusError(
            f"unknown visibility_status: {value!r}"
        ) from exc


#: Canon section 13.2's transition table.
ALLOWED_VISIBILITY_TRANSITIONS: frozenset[
    tuple[ContributionVisibilityStatus, ContributionVisibilityStatus]
] = frozenset(
    {
        (ContributionVisibilityStatus.VISIBLE, ContributionVisibilityStatus.TEMPORARILY_HIDDEN),
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
    }
)


def assert_contribution_visibility_transition_allowed(
    current: ContributionVisibilityStatus, target: ContributionVisibilityStatus
) -> None:
    if (current, target) not in ALLOWED_VISIBILITY_TRANSITIONS:
        raise ForbiddenContributionVisibilityTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


def compute_contribution_content_hash(*, content: str, contribution_type: ContributionType) -> str:
    """Deterministic content hash, mirroring
    `epd2_eligibility_service.domain.compute_snapshot_digest`'s style:
    canonical-JSON-serialize the hashed fields, then SHA-256 the result.
    Only `content` and `contribution_type` participate - not
    `edited_version`/`visibility_status`/timestamps - so the hash answers
    exactly one question ("has the substantive content changed?"),
    independent of moderation or bookkeeping state."""
    payload = {"content": content, "contribution_type": contribution_type.value}
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Contribution:
    """Canon section 13.2 fields exactly.

    Physical deletion: canon section 13.2 states that physical deletion of
    a politically significant `Contribution` is allowed only under a
    separate retention policy, with audit proof preserved ("Физическое
    удаление политически значимого Contribution допускается только по
    отдельной retention policy, при сохранении audit proof"). This service
    deliberately implements **no** physical deletion at all - only
    `visibility_status` transitions (e.g. `-> removed_from_public_view`,
    which still preserves the row, its `content_hash`, and its full audit
    trail). A separate, not-yet-specified retention-policy process is
    canon's named mechanism for actual physical deletion; omitting it here
    is intentional scope discipline, not an oversight - see README.md.
    """

    contribution_id: UUID
    discussion_id: UUID
    author_actor_id: UUID
    parent_contribution_id: UUID | None
    contribution_type: ContributionType
    content: str
    content_hash: str
    visibility_status: ContributionVisibilityStatus
    created_at: datetime
    edited_version: int

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("content must not be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.edited_version < 1:
            raise ValueError("edited_version must be >= 1")
        expected_hash = compute_contribution_content_hash(
            content=self.content, contribution_type=self.contribution_type
        )
        if self.content_hash != expected_hash:
            raise ValueError("content_hash does not match content/contribution_type")

    def with_visibility_status(self, new_status: ContributionVisibilityStatus) -> Contribution:
        assert_contribution_visibility_transition_allowed(self.visibility_status, new_status)
        return replace(self, visibility_status=new_status)

    def with_edited_content(self, new_content: str) -> Contribution:
        """Create a new edited version: recomputes `content_hash` and
        increments `edited_version`. Does not change `visibility_status`
        (spec section 3: editing is orthogonal to moderation state)."""
        new_hash = compute_contribution_content_hash(
            content=new_content, contribution_type=self.contribution_type
        )
        return replace(
            self,
            content=new_content,
            content_hash=new_hash,
            edited_version=self.edited_version + 1,
        )

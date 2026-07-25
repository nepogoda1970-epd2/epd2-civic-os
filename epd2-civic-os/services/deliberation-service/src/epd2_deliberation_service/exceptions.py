"""Deliberation Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownDiscussionStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenDiscussionTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownDiscussionError(ValueError):
    """Raised for a plain lookup miss (no `Discussion` exists for the
    given `discussion_id`) - distinct from `UnknownDiscussionStatusError`
    (`VALIDATION_UNKNOWN_STATUS`), which describes an out-of-enum status
    value on a discussion that does exist (see ADR-004 precedent in
    credential-service)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class DiscussionCreationConflictError(ValueError):
    """A repeated creation request with the same `discussion_id` but
    different content (CT-00-04 analogue for creation)."""

    reason_code = "DISCUSSION_DUPLICATE_CREATION_CONFLICT"


class UnknownContributionTypeError(ValueError):
    """Raised for an out-of-enum `contribution_type` value. Reuses
    `VALIDATION_UNKNOWN_STATUS` rather than minting a separate code:
    canon section 24 has no distinct "unknown type" code, and this is the
    same class of fail-closed rejection (an out-of-enum value on a field
    with a closed value set) `VALIDATION_UNKNOWN_STATUS` already covers
    for every other service's status enums."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownContributionVisibilityStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenContributionVisibilityTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownContributionError(ValueError):
    """Raised for a plain lookup miss (no `Contribution` exists for the
    given `contribution_id`), including an unresolved
    `parent_contribution_id`."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class ContributionCreationConflictError(ValueError):
    """A repeated creation request with the same `contribution_id` but
    different content (CT-00-04 analogue for creation)."""

    reason_code = "CONTRIBUTION_DUPLICATE_CREATION_CONFLICT"

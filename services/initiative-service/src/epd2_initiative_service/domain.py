"""`Initiative`, `InitiativeVersion`, `SupportRecord`, `Amendment` (canon
section 11) and `SourceRecord` (canon section 12.1), per
`docs/canonical/TZ-00-domain-event-canon.md`.

Field lists, status enums, and the "rule freeze" / "one active support"
invariants are taken verbatim from canon; the exact transition graphs are
this service's own design decision (canon lists statuses, not edges) -
see the module-level `ALLOWED_*_TRANSITIONS` constants below and
`docs/handover/PACK-03-SPEC.md` for the pack that commissioned them.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
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

# ---------------------------------------------------------------------------
# Initiative (canon section 11.1)
# ---------------------------------------------------------------------------


class InitiativeStatus(StrEnum):
    """Canon section 11.1's exact status list."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETENESS_REVIEW = "completeness_review"
    REVISION_REQUIRED = "revision_required"
    PUBLISHED = "published"
    SUPPORT_COLLECTION = "support_collection"
    QUALIFIED = "qualified"
    DELIBERATION = "deliberation"
    LEGAL_REVIEW = "legal_review"
    READY_FOR_BALLOT = "ready_for_ballot"
    VOTING = "voting"
    ADOPTED = "adopted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


#: The initiative lifecycle graph. Canon section 11.1 only lists the
#: statuses, not the transition edges between them - this exact graph is
#: this service's own design decision (see module docstring). `withdrawn`
#: is reachable (by the author, pre-voting) from every non-terminal
#: status before `voting`; `archived` is the sole terminal archival step,
#: reachable only from the three terminal outcomes, and has no outgoing
#: edge of its own (fully terminal).
ALLOWED_INITIATIVE_TRANSITIONS: frozenset[tuple[InitiativeStatus, InitiativeStatus]] = frozenset(
    {
        (InitiativeStatus.DRAFT, InitiativeStatus.SUBMITTED),
        (InitiativeStatus.SUBMITTED, InitiativeStatus.COMPLETENESS_REVIEW),
        (InitiativeStatus.COMPLETENESS_REVIEW, InitiativeStatus.REVISION_REQUIRED),
        (InitiativeStatus.COMPLETENESS_REVIEW, InitiativeStatus.PUBLISHED),
        (InitiativeStatus.REVISION_REQUIRED, InitiativeStatus.SUBMITTED),
        (InitiativeStatus.PUBLISHED, InitiativeStatus.SUPPORT_COLLECTION),
        (InitiativeStatus.SUPPORT_COLLECTION, InitiativeStatus.QUALIFIED),
        (InitiativeStatus.SUPPORT_COLLECTION, InitiativeStatus.REJECTED),
        (InitiativeStatus.QUALIFIED, InitiativeStatus.DELIBERATION),
        (InitiativeStatus.DELIBERATION, InitiativeStatus.LEGAL_REVIEW),
        (InitiativeStatus.LEGAL_REVIEW, InitiativeStatus.READY_FOR_BALLOT),
        (InitiativeStatus.LEGAL_REVIEW, InitiativeStatus.REJECTED),
        (InitiativeStatus.READY_FOR_BALLOT, InitiativeStatus.VOTING),
        (InitiativeStatus.VOTING, InitiativeStatus.ADOPTED),
        (InitiativeStatus.VOTING, InitiativeStatus.REJECTED),
        (InitiativeStatus.DRAFT, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.SUBMITTED, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.COMPLETENESS_REVIEW, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.REVISION_REQUIRED, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.PUBLISHED, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.SUPPORT_COLLECTION, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.QUALIFIED, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.DELIBERATION, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.LEGAL_REVIEW, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.READY_FOR_BALLOT, InitiativeStatus.WITHDRAWN),
        (InitiativeStatus.ADOPTED, InitiativeStatus.ARCHIVED),
        (InitiativeStatus.REJECTED, InitiativeStatus.ARCHIVED),
        (InitiativeStatus.WITHDRAWN, InitiativeStatus.ARCHIVED),
    }
)


def parse_initiative_status(value: str) -> InitiativeStatus:
    try:
        return InitiativeStatus(value)
    except ValueError as exc:
        raise UnknownInitiativeStatusError(f"unknown initiative status: {value!r}") from exc


def assert_initiative_transition_allowed(
    current: InitiativeStatus, target: InitiativeStatus
) -> None:
    if (current, target) not in ALLOWED_INITIATIVE_TRANSITIONS:
        raise ForbiddenInitiativeTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Initiative:
    """Canon section 11.1 fields exactly, with one judgment call:
    `current_version_id` is typed `UUID | None` rather than a bare `UUID`.
    Canon lists the field but says nothing about whether an `Initiative`
    can exist before its first `InitiativeVersion` does - since
    `InitiativeVersion.initiative_id` itself must reference an existing
    `Initiative`, *some* order has to come first. This service creates the
    `Initiative` shell (`create_initiative`, `status == draft`) before any
    version exists (`current_version_id is None`), then requires
    `application.create_initiative_version` to attach the first (and
    every subsequent) version - see README.md."""

    initiative_id: UUID
    space_id: UUID
    current_version_id: UUID | None
    author_actor_id: UUID
    initiative_type: str
    workflow_id: UUID
    status: InitiativeStatus
    support_count: int
    created_at: datetime

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.support_count < 0:
            raise ValueError("support_count must not be negative")

    def with_status(self, new_status: InitiativeStatus) -> Initiative:
        assert_initiative_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)

    def with_support_count(self, new_support_count: int) -> Initiative:
        if new_support_count < 0:
            raise ValueError("support_count must not be negative")
        return replace(self, support_count=new_support_count)

    def with_current_version_id(self, new_version_id: UUID) -> Initiative:
        return replace(self, current_version_id=new_version_id)


# ---------------------------------------------------------------------------
# InitiativeVersion (canon section 11.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InitiativeVersion:
    """Canon section 11.2 fields exactly. No status field and no state
    machine - canon: "Опубликованная версия не изменяется. Любая
    редакция создаёт новую версию" (a published version never changes;
    any edit creates a new version). Immutability is enforced by
    `InitiativeVersionStore` (same `(initiative_id, version_number)`
    freeze pattern `epd2_eligibility_service`'s `EligibilityRuleStore`
    uses for `EligibilityRule`), not by anything in this dataclass
    itself.
    """

    initiative_version_id: UUID
    initiative_id: UUID
    version_number: int
    title: str
    problem_statement: str
    proposed_solution: str
    affected_groups: tuple[str, ...]
    expected_effects: str
    risks: str
    estimated_resources: str
    legal_questions: str
    source_references: tuple[UUID, ...]
    created_by_actor_id: UUID
    content_hash: str

    def __post_init__(self) -> None:
        if self.version_number < 1:
            raise ValueError("version_number must be >= 1")


def compute_initiative_version_content_hash(
    *,
    title: str,
    problem_statement: str,
    proposed_solution: str,
    affected_groups: Sequence[str],
    expected_effects: str,
    risks: str,
    estimated_resources: str,
    legal_questions: str,
    source_references: Sequence[UUID],
) -> str:
    """Deterministic content hash over exactly the content fields of an
    `InitiativeVersion` (everything except its own identifiers), mirroring
    `epd2_eligibility_service.domain.compute_snapshot_digest`'s style.
    Two versions with byte-identical content fields always hash the same,
    regardless of how the caller constructed the argument lists.
    """
    payload = {
        "title": title,
        "problem_statement": problem_statement,
        "proposed_solution": proposed_solution,
        "affected_groups": list(affected_groups),
        "expected_effects": expected_effects,
        "risks": risks,
        "estimated_resources": estimated_resources,
        "legal_questions": legal_questions,
        "source_references": [str(s) for s in source_references],
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# SupportRecord (canon section 11.3)
# ---------------------------------------------------------------------------


class SupportStatus(StrEnum):
    """Canon section 11.3's exact status list."""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    INVALIDATED = "invalidated"


#: Both non-active statuses are terminal - there is no path back to
#: `active` (canon does not describe reinstating a withdrawn/invalidated
#: support; a participant who wants to support again creates a new
#: `SupportRecord`, subject to the one-active-support invariant below).
ALLOWED_SUPPORT_TRANSITIONS: frozenset[tuple[SupportStatus, SupportStatus]] = frozenset(
    {
        (SupportStatus.ACTIVE, SupportStatus.WITHDRAWN),
        (SupportStatus.ACTIVE, SupportStatus.INVALIDATED),
    }
)


def parse_support_status(value: str) -> SupportStatus:
    try:
        return SupportStatus(value)
    except ValueError as exc:
        raise UnknownSupportStatusError(f"unknown support status: {value!r}") from exc


def assert_support_transition_allowed(current: SupportStatus, target: SupportStatus) -> None:
    if (current, target) not in ALLOWED_SUPPORT_TRANSITIONS:
        raise ForbiddenSupportTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


#: The complete, allowed public field set for `SupportRecord`. Any field
#: NOT in this set must never appear on it - identity separation
#: (INV-01/INV-03): a `SupportRecord` may only ever carry an opaque
#: `support_actor_reference`/`credential_reference`, never a direct
#: account/person/identity-record link. Enforced structurally (the
#: dataclass's own field set) and by `tests/test_domain.py`'s
#: `test_support_record_never_has_forbidden_fields`.
FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "account_id",
        "person_id",
        "identity_record_id",
    }
)


@dataclass(frozen=True, slots=True)
class SupportRecord:
    """Canon section 11.3 fields exactly. Structurally cannot carry
    identity data - see `FORBIDDEN_FIELD_NAMES` above."""

    support_record_id: UUID
    initiative_id: UUID
    support_actor_reference: UUID
    credential_reference: UUID
    created_at: datetime
    status: SupportStatus

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

    def with_status(self, new_status: SupportStatus) -> SupportRecord:
        assert_support_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)


# ---------------------------------------------------------------------------
# Amendment (canon section 11.4)
# ---------------------------------------------------------------------------


class AmendmentStatus(StrEnum):
    """Canon section 11.4's exact status list."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    UNDER_DISCUSSION = "under_discussion"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"


ALLOWED_AMENDMENT_TRANSITIONS: frozenset[tuple[AmendmentStatus, AmendmentStatus]] = frozenset(
    {
        (AmendmentStatus.DRAFT, AmendmentStatus.SUBMITTED),
        (AmendmentStatus.SUBMITTED, AmendmentStatus.PUBLISHED),
        (AmendmentStatus.PUBLISHED, AmendmentStatus.UNDER_DISCUSSION),
        (AmendmentStatus.UNDER_DISCUSSION, AmendmentStatus.ACCEPTED),
        (AmendmentStatus.UNDER_DISCUSSION, AmendmentStatus.REJECTED),
        (AmendmentStatus.DRAFT, AmendmentStatus.WITHDRAWN),
        (AmendmentStatus.SUBMITTED, AmendmentStatus.WITHDRAWN),
        (AmendmentStatus.PUBLISHED, AmendmentStatus.WITHDRAWN),
        (AmendmentStatus.UNDER_DISCUSSION, AmendmentStatus.WITHDRAWN),
        (AmendmentStatus.PUBLISHED, AmendmentStatus.SUPERSEDED),
        (AmendmentStatus.UNDER_DISCUSSION, AmendmentStatus.SUPERSEDED),
    }
)


def parse_amendment_status(value: str) -> AmendmentStatus:
    try:
        return AmendmentStatus(value)
    except ValueError as exc:
        raise UnknownAmendmentStatusError(f"unknown amendment status: {value!r}") from exc


def assert_amendment_transition_allowed(current: AmendmentStatus, target: AmendmentStatus) -> None:
    if (current, target) not in ALLOWED_AMENDMENT_TRANSITIONS:
        raise ForbiddenAmendmentTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class Amendment:
    """Canon section 11.4 fields exactly. `decision_reference` is
    optional (`None` until the amendment reaches a discussion outcome
    that records one - canon lists the field but not its nullability;
    treating it as absent until set is the least surprising reading)."""

    amendment_id: UUID
    initiative_id: UUID
    target_version_id: UUID
    proposer_actor_id: UUID
    proposed_change: str
    justification: str
    status: AmendmentStatus
    decision_reference: UUID | None

    def with_status(self, new_status: AmendmentStatus) -> Amendment:
        assert_amendment_transition_allowed(self.status, new_status)
        return replace(self, status=new_status)

    def with_decision_reference(self, decision_reference: UUID | None) -> Amendment:
        return replace(self, decision_reference=decision_reference)


# ---------------------------------------------------------------------------
# SourceRecord (canon section 12.1)
# ---------------------------------------------------------------------------


class SourceVerificationStatus(StrEnum):
    """Canon section 12.1's exact "Статусы проверки" list."""

    UNVERIFIED = "unverified"
    AUTOMATICALLY_CHECKED = "automatically_checked"
    HUMAN_CHECKED = "human_checked"
    DISPUTED = "disputed"
    UNAVAILABLE = "unavailable"
    OUTDATED = "outdated"


#: `disputed -> human_checked` is the sole reverse edge (a human review
#: can resolve a dispute); every other edge only ever moves a source
#: further from `unverified`, never back. The "no silent AI promotion to
#: human_checked" invariant (canon 12.1) is enforced by the *caller*
#: (`application.update_source_verification_status`), not here - this
#: graph only encodes which state changes are structurally possible.
ALLOWED_SOURCE_VERIFICATION_TRANSITIONS: frozenset[
    tuple[SourceVerificationStatus, SourceVerificationStatus]
] = frozenset(
    {
        (SourceVerificationStatus.UNVERIFIED, SourceVerificationStatus.AUTOMATICALLY_CHECKED),
        (SourceVerificationStatus.UNVERIFIED, SourceVerificationStatus.HUMAN_CHECKED),
        (SourceVerificationStatus.AUTOMATICALLY_CHECKED, SourceVerificationStatus.HUMAN_CHECKED),
        (SourceVerificationStatus.UNVERIFIED, SourceVerificationStatus.DISPUTED),
        (SourceVerificationStatus.AUTOMATICALLY_CHECKED, SourceVerificationStatus.DISPUTED),
        (SourceVerificationStatus.HUMAN_CHECKED, SourceVerificationStatus.DISPUTED),
        (SourceVerificationStatus.DISPUTED, SourceVerificationStatus.HUMAN_CHECKED),
        (SourceVerificationStatus.UNVERIFIED, SourceVerificationStatus.UNAVAILABLE),
        (SourceVerificationStatus.AUTOMATICALLY_CHECKED, SourceVerificationStatus.UNAVAILABLE),
        (SourceVerificationStatus.HUMAN_CHECKED, SourceVerificationStatus.UNAVAILABLE),
        (SourceVerificationStatus.UNVERIFIED, SourceVerificationStatus.OUTDATED),
        (SourceVerificationStatus.AUTOMATICALLY_CHECKED, SourceVerificationStatus.OUTDATED),
        (SourceVerificationStatus.HUMAN_CHECKED, SourceVerificationStatus.OUTDATED),
    }
)


def parse_source_verification_status(value: str) -> SourceVerificationStatus:
    try:
        return SourceVerificationStatus(value)
    except ValueError as exc:
        raise UnknownSourceVerificationStatusError(
            f"unknown source verification status: {value!r}"
        ) from exc


def assert_source_verification_transition_allowed(
    current: SourceVerificationStatus, target: SourceVerificationStatus
) -> None:
    if (current, target) not in ALLOWED_SOURCE_VERIFICATION_TRANSITIONS:
        raise ForbiddenSourceVerificationTransitionError(
            f"transition {current.value!r} -> {target.value!r} is not allowed"
        )


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Canon section 12.1 fields exactly. `publication_date` and
    `archive_reference` are optional (not every source has a known
    publication date or an archived snapshot yet); `valid_until` is
    optional per canon's own general pattern for expiry fields elsewhere
    in the canon (e.g. `EligibilityRule.valid_until`)."""

    source_id: UUID
    source_type: str
    title: str
    publisher: str
    publication_date: datetime | None
    url: str
    archive_reference: str | None
    verification_status: SourceVerificationStatus
    added_by_actor_id: UUID
    accessed_at: datetime
    content_hash: str
    valid_until: datetime | None

    def __post_init__(self) -> None:
        if self.accessed_at.tzinfo is None:
            raise ValueError("accessed_at must be timezone-aware")
        if self.publication_date is not None and self.publication_date.tzinfo is None:
            raise ValueError("publication_date must be timezone-aware")
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("valid_until must be timezone-aware")

    def with_verification_status(self, new_status: SourceVerificationStatus) -> SourceRecord:
        assert_source_verification_transition_allowed(self.verification_status, new_status)
        return replace(self, verification_status=new_status)


def compute_source_record_content_hash(
    *,
    source_type: str,
    title: str,
    publisher: str,
    publication_date: datetime | None,
    url: str,
    archive_reference: str | None,
) -> str:
    """Deterministic content hash over exactly what a `SourceRecord` *is*
    (its own bibliographic identity) - deliberately excludes
    `verification_status`/`added_by_actor_id`/`accessed_at`/`valid_until`,
    which describe this service's own administrative handling of the
    source, not the source itself. Mirrors
    `compute_initiative_version_content_hash`'s style."""
    payload = {
        "source_type": source_type,
        "title": title,
        "publisher": publisher,
        "publication_date": publication_date.isoformat() if publication_date else None,
        "url": url,
        "archive_reference": archive_reference,
    }
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()

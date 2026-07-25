"""AI Processing Service domain layer — canon section 17.1 (original
`AIProcessingRecord`) and section 19c ("ИИ-обработка — расширение / AI
Processing Context", added by canon 0.5.0, ADR-023/ADR-025).

`AIProcessingRecord` is the one canonical entity this pack owns (canon
19c: "остаётся единственной сущностью настоящего раздела"). Two closed,
canon-fixed statuses live on it, deliberately independent of one
another:

- `ProcessingStatus` (19c.1, new): the technical pipeline plane
  (`requested -> input_prepared -> processing -> {completed | failed |
  rejected_by_policy}`, `rejected_by_policy` also directly reachable from
  `requested`). Has **no stored `superseded` value** — whether a given
  processing attempt has been superseded is always a derived,
  query-time fact (`storage.AIProcessingRecordStore.find_superseding`),
  never a value this status enum itself carries.
- `HumanReviewStatus` (17.1, unchanged six-value enum — `not_required`,
  `pending`, `approved`, `approved_with_changes`, `rejected`,
  `superseded`): canon keeps `superseded` in the enum's *literal* value
  list, but 19c.1 clarifies it is "reached... exclusively when a new
  record is created... never as a standalone transition" — this
  package's reading (consistent with every other supersession precedent
  in this project: `GovernanceDecision.finality_outcome`/`FinalityStatus`,
  `PublicLedgerEntry.supersedes_entry_id`) is that `SUPERSEDED` is never
  a value any command *stores* directly on `human_review_status` itself;
  `__post_init__` below rejects constructing a record with it set. A
  derived accessor, `derive_effective_human_review_status`, is what
  actually surfaces `SUPERSEDED` to a reader — computed the same way
  `derive_disclosure_status` computes `DisclosureStatus`, never stored.

Both statuses' `superseded` meaning route through exactly one shared
field, `supersedes_ai_processing_record_id` (19c.2) — one mechanism
covers replacing a processing attempt and replacing a review outcome
alike; which of the two canon events fires
(`ai.processing_record_superseded` vs `ai.review_outcome_superseded`) is
an `application.py`-level choice made by the caller creating the
superseding record, not something this field or its presence alone
determines.

`RedactionManifest` (19c.4) is a canonical, immutable, embedded value
object — never a second entity, never caller-supplied (only
`ai-processing-service` itself ever constructs one). `AIDisclosurePackage`
(19c.6) is a contract/value object, never persisted by this pack or by
`transparency-service` — its only durable trace is the resulting
`PublicLedgerEntry` row (owned entirely by `transparency-service`) plus
the two opaque reference fields on `AIProcessingRecord` itself
(`disclosure_package_reference`/`disclosure_receipt_reference`, 19c.5).

Reviewer roles, use classes, and the purpose/target-type allow-lists
below are this pack's own repository-side configuration (ADR-022,
ADR-025 §2/§3) — canon 19c.9 explicitly leaves the reviewer-verification
mechanism and any such allow-list to implementation, not canon text.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from epd2_ai_processing_service.exceptions import (
    UnknownHumanReviewStatusError,
    UnknownProcessingStatusError,
)

# ---------------------------------------------------------------------------
# ProcessingStatus (19c.1, new field/status — technical pipeline plane)
# ---------------------------------------------------------------------------


class ProcessingStatus(StrEnum):
    REQUESTED = "requested"
    INPUT_PREPARED = "input_prepared"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED_BY_POLICY = "rejected_by_policy"


PROCESSING_STATUS_ALLOWED_TRANSITIONS: frozenset[tuple[ProcessingStatus, ProcessingStatus]] = (
    frozenset(
        {
            (ProcessingStatus.REQUESTED, ProcessingStatus.INPUT_PREPARED),
            (ProcessingStatus.REQUESTED, ProcessingStatus.REJECTED_BY_POLICY),
            (ProcessingStatus.INPUT_PREPARED, ProcessingStatus.PROCESSING),
            (ProcessingStatus.INPUT_PREPARED, ProcessingStatus.REJECTED_BY_POLICY),
            (ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED),
            (ProcessingStatus.PROCESSING, ProcessingStatus.FAILED),
            (ProcessingStatus.PROCESSING, ProcessingStatus.REJECTED_BY_POLICY),
        }
    )
)

TERMINAL_PROCESSING_STATUSES: frozenset[ProcessingStatus] = frozenset(
    {ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.REJECTED_BY_POLICY}
)


class ForbiddenProcessingStatusTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


def assert_processing_status_transition_allowed(
    current: ProcessingStatus, target: ProcessingStatus
) -> None:
    if (current, target) not in PROCESSING_STATUS_ALLOWED_TRANSITIONS:
        raise ForbiddenProcessingStatusTransitionError(
            f"processing_status transition {current.value!r} -> {target.value!r} is not allowed"
        )


def parse_processing_status(value: str) -> ProcessingStatus:
    """Parse `value` into a `ProcessingStatus`, raising
    `UnknownProcessingStatusError` (fail-closed, CT-00-02) if it is not
    one of the six canonical values - never guesses or defaults."""
    try:
        return ProcessingStatus(value)
    except ValueError as exc:
        raise UnknownProcessingStatusError(f"unknown processing_status: {value!r}") from exc


# ---------------------------------------------------------------------------
# HumanReviewStatus (17.1, unchanged six-value enum; semantics per 19c.1)
# ---------------------------------------------------------------------------


class HumanReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_WITH_CHANGES = "approved_with_changes"
    REJECTED = "rejected"
    #: Never directly stored by any command (see module docstring) — kept
    #: in the enum because canon 17.1's six-value list is unchanged by
    #: canon 0.5.0; only ever produced by `derive_effective_human_review_status`.
    SUPERSEDED = "superseded"


#: The only stored-by-command transitions. `not_required` is terminal
#: (assigned only at creation, for non-consequential use, 19c.8) and
#: `superseded` is never a transition target here — see module docstring.
HUMAN_REVIEW_STATUS_ALLOWED_TRANSITIONS: frozenset[tuple[HumanReviewStatus, HumanReviewStatus]] = (
    frozenset(
        {
            (HumanReviewStatus.PENDING, HumanReviewStatus.APPROVED),
            (HumanReviewStatus.PENDING, HumanReviewStatus.APPROVED_WITH_CHANGES),
            (HumanReviewStatus.PENDING, HumanReviewStatus.REJECTED),
        }
    )
)

TERMINAL_HUMAN_REVIEW_STATUSES: frozenset[HumanReviewStatus] = frozenset(
    {
        HumanReviewStatus.NOT_REQUIRED,
        HumanReviewStatus.APPROVED,
        HumanReviewStatus.APPROVED_WITH_CHANGES,
        HumanReviewStatus.REJECTED,
    }
)


class ForbiddenHumanReviewStatusTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


def assert_human_review_status_transition_allowed(
    current: HumanReviewStatus, target: HumanReviewStatus
) -> None:
    if (current, target) not in HUMAN_REVIEW_STATUS_ALLOWED_TRANSITIONS:
        raise ForbiddenHumanReviewStatusTransitionError(
            f"human_review_status transition {current.value!r} -> {target.value!r} is not allowed"
        )


def parse_human_review_status(value: str) -> HumanReviewStatus:
    """Parse `value` into a `HumanReviewStatus`, raising
    `UnknownHumanReviewStatusError` (fail-closed, CT-00-02) if it is not
    one of the six canonical values - never guesses or defaults."""
    try:
        return HumanReviewStatus(value)
    except ValueError as exc:
        raise UnknownHumanReviewStatusError(f"unknown human_review_status: {value!r}") from exc


def derive_effective_human_review_status(
    record: AIProcessingRecord, *, superseding_record: AIProcessingRecord | None
) -> HumanReviewStatus:
    """The derived, never-stored read model for `human_review_status`'s
    `superseded` value (19c.1) — `superseding_record` is whatever
    `storage.AIProcessingRecordStore.find_superseding` returned for
    `record.ai_processing_record_id` (a record whose own
    `supersedes_ai_processing_record_id` points back at this one), or
    `None` if this record has not been superseded."""
    if superseding_record is not None:
        return HumanReviewStatus.SUPERSEDED
    return record.human_review_status


# ---------------------------------------------------------------------------
# RedactionManifest (19c.4) — embedded, immutable value object
# ---------------------------------------------------------------------------


class RedactionResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class RedactionManifest:
    """Canon 19c.4's exact nine fields. Constructed exactly once, by
    `ai-processing-service` itself, at the moment the redaction/
    provenance validation step completes — never accepted as
    caller-supplied input (`application.py` never trusts a caller-
    supplied `redaction_applied`-style flag). Never contains raw input,
    removed values, or any identity/credential/vote content — only
    category-level metadata about what was checked and what was found
    and excluded.
    """

    redaction_policy_reference: str
    redaction_policy_version: str
    input_classification: str
    checked_field_categories: tuple[str, ...]
    removed_field_categories: tuple[str, ...]
    prepared_input_hash: str
    validator_version: str
    validated_at: datetime
    result: RedactionResult

    def __post_init__(self) -> None:
        if not self.redaction_policy_reference:
            raise ValueError("redaction_policy_reference must not be empty")
        if not self.redaction_policy_version:
            raise ValueError("redaction_policy_version must not be empty")
        if not self.input_classification:
            raise ValueError("input_classification must not be empty")
        if not self.prepared_input_hash:
            raise ValueError("prepared_input_hash must not be empty")
        if not self.validator_version:
            raise ValueError("validator_version must not be empty")
        if self.validated_at.tzinfo is None:
            raise ValueError("validated_at must be timezone-aware")
        if not frozenset(self.removed_field_categories) <= frozenset(self.checked_field_categories):
            raise ValueError(
                "removed_field_categories must be a subset of checked_field_categories"
            )


# ---------------------------------------------------------------------------
# DisclosureStatus (19c.5) — derived, never-stored read model
# ---------------------------------------------------------------------------


class DisclosureStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING_PACKAGE = "pending_package"
    PENDING_PUBLICATION = "pending_publication"
    PUBLISHED = "published"


def derive_disclosure_status(record: AIProcessingRecord) -> DisclosureStatus:
    """Computed fresh from three stored fields (19c.5) — never
    independently mutable, the same "derived, not stored" principle as
    `FinalityStatus` (governance-service, canon 19b.3)."""
    if not record.disclosure_required:
        return DisclosureStatus.NOT_REQUIRED
    if record.disclosure_package_reference is None:
        return DisclosureStatus.PENDING_PACKAGE
    if record.disclosure_receipt_reference is None:
        return DisclosureStatus.PENDING_PUBLICATION
    return DisclosureStatus.PUBLISHED


# ---------------------------------------------------------------------------
# AIProcessingRecord (canon 17.1 + 19c)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AIProcessingRecord:
    """Canon 17.1's original thirteen fields (`ai_processing_record_id`
    through `correction_reference`) plus canon 19c's additions. The
    *same physical row* (same `ai_processing_record_id`) is updated in
    place across its own technical/review lifecycle via `with_*` methods
    below (mirroring `RoleAssignment.with_status`/
    `GovernanceDecision.with_approved`) — a **correction** is always a
    *different* row, a brand-new `AIProcessingRecord` whose own
    `supersedes_ai_processing_record_id` points back at this one
    (19c.2), never a rewrite of this row's own fields.
    """

    # --- canon 17.1, unchanged ---
    ai_processing_record_id: UUID
    purpose_code: str
    target_type: str
    target_id: UUID
    input_version: str
    model_provider: str
    model_name: str
    model_version: str
    prompt_template_version: str
    output_reference: str | None
    created_at: datetime
    human_review_status: HumanReviewStatus
    correction_reference: str | None

    # --- canon 19c.1/19c.2, new ---
    processing_status: ProcessingStatus
    supersedes_ai_processing_record_id: UUID | None

    # --- canon 19c.3, new: model governance and deployment ---
    deployment_version: str | None
    system_policy_version: str | None
    generation_settings: Mapping[str, object] | None
    processing_region: str | None
    data_retention_mode: str | None
    external_provider_flag: bool

    # --- canon 19c.3, new: provenance and integrity ---
    input_hash: str | None
    output_hash: str | None

    # --- canon 19c.3, new: confidence and uncertainty ---
    confidence_score: float | None
    uncertainty_indicator: str | None

    # --- canon 19c.3, new: explainability ---
    explanation_reference: str | None
    reason_codes: tuple[str, ...]

    # --- canon 19c.3, new: reviewer provenance ---
    human_reviewer_reference: UUID | None

    # --- canon 19c.3, new: lifecycle timestamps ---
    completed_at: datetime | None
    reviewed_at: datetime | None

    # --- canon 19c.4, new: embedded, immutable value object ---
    redaction_manifest: RedactionManifest | None

    # --- canon 19c.5, new: disclosure lifecycle ---
    disclosure_required: bool
    disclosure_package_reference: UUID | None
    disclosure_receipt_reference: UUID | None

    def __post_init__(self) -> None:
        if not self.purpose_code:
            raise ValueError("purpose_code must not be empty")
        if not self.target_type:
            raise ValueError("target_type must not be empty")
        if not self.input_version:
            raise ValueError("input_version must not be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.completed_at is not None and self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")
        if self.reviewed_at is not None and self.reviewed_at.tzinfo is None:
            raise ValueError("reviewed_at must be timezone-aware")
        if self.human_review_status is HumanReviewStatus.SUPERSEDED:
            raise ValueError(
                "human_review_status must never be stored as 'superseded' directly — "
                "it is a derived read-model value only (see derive_effective_human_review_status)"
            )
        if (
            self.processing_status in (ProcessingStatus.INPUT_PREPARED, ProcessingStatus.PROCESSING)
            and self.redaction_manifest is None
        ):
            raise ValueError(
                f"redaction_manifest is required once processing_status has reached "
                f"{self.processing_status.value!r}"
            )
        if self.processing_status is ProcessingStatus.COMPLETED and self.redaction_manifest is None:
            raise ValueError("redaction_manifest is required once processing_status = completed")
        if self.disclosure_package_reference is not None and not self.disclosure_required:
            raise ValueError("disclosure_package_reference set but disclosure_required is False")
        if (
            self.disclosure_receipt_reference is not None
            and self.disclosure_package_reference is None
        ):
            raise ValueError("disclosure_receipt_reference set before disclosure_package_reference")
        if self.confidence_score is not None and not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be within [0.0, 1.0]")

    def with_processing_status(
        self,
        new_status: ProcessingStatus,
        *,
        redaction_manifest: RedactionManifest | None = None,
        input_hash: str | None = None,
        output_reference: str | None = None,
        output_hash: str | None = None,
        confidence_score: float | None = None,
        uncertainty_indicator: str | None = None,
        explanation_reference: str | None = None,
        reason_codes: tuple[str, ...] | None = None,
        completed_at: datetime | None = None,
    ) -> AIProcessingRecord:
        assert_processing_status_transition_allowed(self.processing_status, new_status)
        changes: dict[str, Any] = {"processing_status": new_status}
        if redaction_manifest is not None:
            changes["redaction_manifest"] = redaction_manifest
        if input_hash is not None:
            changes["input_hash"] = input_hash
        if output_reference is not None:
            changes["output_reference"] = output_reference
        if output_hash is not None:
            changes["output_hash"] = output_hash
        if confidence_score is not None:
            changes["confidence_score"] = confidence_score
        if uncertainty_indicator is not None:
            changes["uncertainty_indicator"] = uncertainty_indicator
        if explanation_reference is not None:
            changes["explanation_reference"] = explanation_reference
        if reason_codes is not None:
            changes["reason_codes"] = reason_codes
        if completed_at is not None:
            changes["completed_at"] = completed_at
        return replace(self, **changes)

    def with_human_review_status(
        self,
        new_status: HumanReviewStatus,
        *,
        human_reviewer_reference: UUID,
        reviewed_at: datetime,
        output_reference: str | None = None,
    ) -> AIProcessingRecord:
        assert_human_review_status_transition_allowed(self.human_review_status, new_status)
        changes: dict[str, Any] = {
            "human_review_status": new_status,
            "human_reviewer_reference": human_reviewer_reference,
            "reviewed_at": reviewed_at,
        }
        if output_reference is not None:
            changes["output_reference"] = output_reference
        return replace(self, **changes)

    def with_disclosure_package_reference(
        self, disclosure_package_reference: UUID
    ) -> AIProcessingRecord:
        if not self.disclosure_required:
            raise ValueError(
                "cannot set disclosure_package_reference when disclosure_required is False"
            )
        if self.disclosure_package_reference is not None:
            raise ValueError("disclosure_package_reference is already set and is never rewritten")
        return replace(self, disclosure_package_reference=disclosure_package_reference)

    def with_disclosure_receipt_reference(
        self, disclosure_receipt_reference: UUID
    ) -> AIProcessingRecord:
        if self.disclosure_package_reference is None:
            raise ValueError(
                "disclosure_package_reference must be set before a receipt can be recorded"
            )
        if self.disclosure_receipt_reference is not None:
            raise ValueError("disclosure_receipt_reference is already set and is never rewritten")
        return replace(self, disclosure_receipt_reference=disclosure_receipt_reference)


# ---------------------------------------------------------------------------
# AIDisclosurePackage (19c.6) — contract/value object, never persisted
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AIDisclosurePackage:
    """Canon 19c.6: a transient contract/value object `ai-processing-
    service` constructs and hands to
    `transparency-service.publish_ledger_entry` as caller-supplied
    `raw_content` — never itself persisted by either service. Carries
    only the mandatory-disclosure content 19c.6 names as required;
    structurally cannot carry any of 19c.6's prohibited content (raw
    input, private output, hidden prompt, reviewer identity, any
    `RoleAssignment` UUID, identity/credential/vote data, hidden
    reasoning), since none of those has a field here at all.
    """

    ai_processing_record_reference: UUID
    purpose_code: str
    approved_public_model_category: str
    approved_public_model_version: str
    processed_at: datetime
    human_review_outcome: HumanReviewStatus
    prompt_template_version: str
    system_policy_version: str

    def __post_init__(self) -> None:
        if self.human_review_outcome not in (
            HumanReviewStatus.APPROVED,
            HumanReviewStatus.APPROVED_WITH_CHANGES,
        ):
            raise ValueError(
                "an AIDisclosurePackage may only be constructed for a verified human-approved "
                "outcome (approved or approved_with_changes)"
            )
        if not self.purpose_code:
            raise ValueError("purpose_code must not be empty")
        if self.processed_at.tzinfo is None:
            raise ValueError("processed_at must be timezone-aware")

    def to_raw_content(self) -> dict[str, object]:
        """The exact, JSON-safe `raw_content` passed to
        `transparency-service.publish_ledger_entry` — every value here is
        already public-safe by construction (see class docstring)."""
        return {
            "ai_processing_record_reference": str(self.ai_processing_record_reference),
            "purpose_code": self.purpose_code,
            "approved_public_model_category": self.approved_public_model_category,
            "approved_public_model_version": self.approved_public_model_version,
            "processed_at": self.processed_at.isoformat(),
            "human_review_outcome": self.human_review_outcome.value,
            "prompt_template_version": self.prompt_template_version,
            "system_policy_version": self.system_policy_version,
        }


# ---------------------------------------------------------------------------
# Use classes, reviewer roles, purpose/target allow-lists (ADR-022/ADR-025,
# repository-side configuration — canon 19c.9 leaves this to implementation)
# ---------------------------------------------------------------------------


class UseClass(StrEnum):
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"
    DRAFTING = "drafting"
    ANOMALY_INDICATION = "anomaly_indication"
    POLICY_COMPLIANCE_ASSISTANCE = "policy_compliance_assistance"


#: Repository-level closed allow-list for `purpose_code` (ADR-025 §2) —
#: one purpose_code per use class, no free-text purpose_code accepted.
PURPOSE_CODES: frozenset[str] = frozenset(use_class.value for use_class in UseClass)

#: Repository-level closed allow-list for `target_type` (ADR-025 §2).
TARGET_TYPES: frozenset[str] = frozenset(
    {
        "initiative",
        "initiative_version",
        "contribution",
        "discussion_post",
        "moderation_case",
        "governance_policy_draft",
        "participation_pattern_report",
    }
)

#: `target_type` values considered "moderation-adjacent" (ADR-022's own
#: phrase) — these route `classification` review to `ai_moderation_reviewer`
#: rather than the default `ai_output_reviewer`.
MODERATION_ADJACENT_TARGET_TYPES: frozenset[str] = frozenset({"contribution", "initiative"})

#: Repository-level closed allow-list for permitted purpose/target
#: combinations (ADR-025 §2 — "purpose_code/target_type/permitted
#: combinations").
PERMITTED_PURPOSE_TARGET_COMBINATIONS: dict[UseClass, frozenset[str]] = {
    UseClass.SUMMARIZATION: frozenset({"initiative", "initiative_version", "discussion_post"}),
    UseClass.CLASSIFICATION: frozenset(
        {"contribution", "initiative", "discussion_post", "moderation_case"}
    ),
    UseClass.RECOMMENDATION: frozenset({"initiative", "discussion_post"}),
    UseClass.DRAFTING: frozenset({"initiative_version", "governance_policy_draft"}),
    UseClass.ANOMALY_INDICATION: frozenset({"participation_pattern_report"}),
    UseClass.POLICY_COMPLIANCE_ASSISTANCE: frozenset({"governance_policy_draft"}),
}


class AITargetReferenceMalformedError(ValueError):
    reason_code = "AI_TARGET_REFERENCE_MALFORMED"


def assert_purpose_target_combination_allowed(use_class: UseClass, target_type: str) -> None:
    if target_type not in TARGET_TYPES:
        raise AITargetReferenceMalformedError(
            f"target_type {target_type!r} is not a recognized type"
        )
    allowed = PERMITTED_PURPOSE_TARGET_COMBINATIONS.get(use_class, frozenset())
    if target_type not in allowed:
        raise AITargetReferenceMalformedError(
            f"target_type {target_type!r} is not permitted for use class {use_class.value!r}"
        )


#: ADR-022's four-role reviewer taxonomy (repository-side, not a canon
#: enumeration — canon 19c.9).
REVIEWER_ROLE_CODES: frozenset[str] = frozenset(
    {
        "ai_output_reviewer",
        "ai_moderation_reviewer",
        "ai_governance_reviewer",
        "ai_publication_reviewer",
    }
)

#: Use classes/target types for which reviewer independence is mandatory
#: (ADR-025 §3: "moderation-, governance-, ballot-adjacent-, and
#: official-publication uses") — self-review is prohibited for these,
#: never merely discouraged.
INDEPENDENT_REVIEW_REQUIRED_USE_CLASSES: frozenset[UseClass] = frozenset(
    {UseClass.CLASSIFICATION, UseClass.POLICY_COMPLIANCE_ASSISTANCE}
)


def required_reviewer_role_codes(use_class: UseClass, target_type: str) -> frozenset[str]:
    """The base reviewer role required for `use_class`/`target_type`
    (ADR-022's table) — a caller-supplied official/public-publication
    requirement additionally requires `ai_publication_reviewer` from a
    *second*, independently-authorized reviewer (`application.
    publish_ai_disclosure_package`'s own reviewer-verification step),
    never folded into this single-role check."""
    if use_class is UseClass.CLASSIFICATION and target_type in MODERATION_ADJACENT_TARGET_TYPES:
        return frozenset({"ai_moderation_reviewer"})
    if use_class is UseClass.POLICY_COMPLIANCE_ASSISTANCE:
        return frozenset({"ai_governance_reviewer"})
    return frozenset({"ai_output_reviewer"})


def review_requires_independent_reviewer(
    use_class: UseClass, *, is_official_publication: bool
) -> bool:
    """ADR-025 §3: self-review is prohibited (not merely discouraged) for
    moderation-, governance-, ballot-adjacent-, and official-publication
    uses. `is_official_publication` covers the ballot-adjacent/official-
    publication cases; `use_class` membership in
    `INDEPENDENT_REVIEW_REQUIRED_USE_CLASSES` covers moderation/
    governance."""
    return is_official_publication or use_class in INDEPENDENT_REVIEW_REQUIRED_USE_CLASSES


# ---------------------------------------------------------------------------
# Consequential-use semantics (19c.8) — a repository-side classification
# helper, not a canon-level closed list (canon defines the concept, not a
# closed enumeration of every possible consequential case).
# ---------------------------------------------------------------------------


def is_official_or_public_use(*, is_official_publication: bool) -> bool:
    """Thin, explicit wrapper kept for call-site readability — an
    official/public artifact is always the caller's own explicit
    declaration (never inferred by this pack from `target_type` alone),
    consistent with canon 19c.9's rule that `AIProcessingRecord` never
    makes a publication decision itself."""
    return is_official_publication

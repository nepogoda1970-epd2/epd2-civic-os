"""DLP controls (ADR-067, first half).

Eighteen policy-level controls, one assessment object, and one rule that
matters more than the rest: **detection fails closed** (`P12-DLP-005`).
An assessment the system could not complete blocks the export pending
manual review. A DLP layer that produces a finding and then lets the
export proceed because the detector timed out is worse than no DLP
layer, because it manufactures the appearance of assurance.

`P12-DLP-004` is a documentation obligation this module carries in code:
watermarking, expiry and revocation are deterrent, attribution and
containment controls. Nothing here claims they guarantee deletion or
non-disclosure at an external recipient, and `WATERMARK_LIMITATION_NOTE`
exists so the limit travels with the control rather than living only in
a specification nobody reads at 2am.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    DlpAssessmentIncompleteError,
    DlpForbiddenDataDetectedError,
    DlpFrequencyLimitExceededError,
    DlpRepeatedRequestRiskError,
    DlpReviewRequiredError,
    DlpSizeLimitExceededError,
    DlpUnusualVolumeReviewError,
    UnknownStatusError,
)
from epd2_privileged_access_service.policy import PrivilegedAccessPolicy

#: `P12-DLP-004`, recorded next to the controls it qualifies.
WATERMARK_LIMITATION_NOTE: str = (
    "P12-DLP-004: watermarking, expiry and revocation are deterrent, attribution and "
    "containment controls. They do not guarantee deletion or non-disclosure at an external "
    "recipient. Once delivered, data is outside the platform's trust boundary; revocation "
    "withdraws authorization and blocks further platform-mediated access, and reaches no "
    "copy the recipient already holds."
)


class DlpControl(StrEnum):
    """The eighteen policy-level controls (`P12-DLP-001`)."""

    FIELD_SUPPRESSION = "field_suppression"
    FIELD_MASKING = "field_masking"
    REDACTION = "redaction"
    PSEUDONYMIZATION = "pseudonymization"
    AGGREGATION = "aggregation"
    COHORT_THRESHOLD = "cohort_threshold"
    RECIPIENT_RESTRICTION = "recipient_restriction"
    WATERMARKING = "watermarking"
    EXPIRY = "expiry"
    ACCESS_LIMIT = "access_limit"
    TRANSFER_CHANNEL_RESTRICTION = "transfer_channel_restriction"
    SIZE_LIMIT = "size_limit"
    FREQUENCY_LIMIT = "frequency_limit"
    REPEATED_REQUEST_DETECTION = "repeated_request_detection"
    UNUSUAL_VOLUME_REVIEW = "unusual_volume_review"
    FORBIDDEN_DATA_DETECTION = "forbidden_data_detection"
    MANUAL_REVIEW_TRIGGER = "manual_review_trigger"
    DESTRUCTION_ATTESTATION = "destruction_attestation"


ALL_DLP_CONTROLS: frozenset[DlpControl] = frozenset(DlpControl)

#: Controls whose failure to complete must block rather than pass.
FAIL_CLOSED_CONTROLS: frozenset[DlpControl] = frozenset(
    {
        DlpControl.FORBIDDEN_DATA_DETECTION,
        DlpControl.COHORT_THRESHOLD,
        DlpControl.RECIPIENT_RESTRICTION,
    }
)


class DlpOutcome(StrEnum):
    PASSED = "passed"
    TRANSFORMS_REQUIRED = "transforms_required"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    REFUSED = "refused"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class DlpFinding:
    control: DlpControl
    field_name: str | None
    severity: str
    detail_reference: str

    def __post_init__(self) -> None:
        require_text(self.detail_reference, "detail_reference")
        if self.severity not in {"informational", "warning", "blocking"}:
            raise UnknownStatusError(f"unknown DLP severity {self.severity!r}")

    def to_payload(self) -> dict[str, object]:
        return {
            "control": str(self.control),
            "field_name": self.field_name,
            "severity": self.severity,
            "detail_reference": self.detail_reference,
        }


@dataclass(frozen=True, slots=True)
class DlpAssessment:
    """One completed - or explicitly incomplete - DLP assessment.

    `completed_controls` is compared against `FAIL_CLOSED_CONTROLS` at
    construction: an assessment that did not finish a fail-closed control
    cannot be recorded as `PASSED`, whatever the caller passes for
    `outcome`."""

    assessment_id: UUID
    export_id: UUID
    organization_scope: OrganizationalScopeRef
    assessor_reference: str
    assessed_at: datetime
    completed_controls: frozenset[DlpControl]
    findings: tuple[DlpFinding, ...]
    required_transforms: frozenset[DlpControl]
    outcome: DlpOutcome

    def __post_init__(self) -> None:
        require_text(self.assessor_reference, "assessor_reference")
        require_timezone(self.assessed_at, context="DlpAssessment.assessed_at")
        missing = FAIL_CLOSED_CONTROLS - self.completed_controls
        if missing and self.outcome in {DlpOutcome.PASSED, DlpOutcome.TRANSFORMS_REQUIRED}:
            raise DlpAssessmentIncompleteError(
                f"fail-closed controls {sorted(c.value for c in missing)} did not complete; "
                "the assessment cannot be recorded as passing"
            )
        if any(f.severity == "blocking" for f in self.findings) and self.outcome is (
            DlpOutcome.PASSED
        ):
            raise DlpForbiddenDataDetectedError(
                "a blocking finding cannot coexist with a passing outcome"
            )

    @property
    def permits_export(self) -> bool:
        return self.outcome in {DlpOutcome.PASSED, DlpOutcome.TRANSFORMS_REQUIRED}

    def assert_permits_export(self) -> None:
        if self.outcome is DlpOutcome.INCOMPLETE:
            raise DlpAssessmentIncompleteError(
                "the DLP assessment did not complete; the export is blocked pending manual review"
            )
        if self.outcome is DlpOutcome.MANUAL_REVIEW_REQUIRED:
            raise DlpReviewRequiredError("manual DLP review is required before a decision")
        if self.outcome is DlpOutcome.REFUSED:
            raise DlpForbiddenDataDetectedError("the DLP assessment refused this export")

    def to_state_payload(self) -> dict[str, object]:
        return {
            "assessment_id": str(self.assessment_id),
            "export_id": str(self.export_id),
            "organization_scope": self.organization_scope.to_payload(),
            "assessor_reference": self.assessor_reference,
            "assessed_at": self.assessed_at.isoformat(),
            "completed_controls": sorted(c.value for c in self.completed_controls),
            "findings": [f.to_payload() for f in self.findings],
            "required_transforms": sorted(c.value for c in self.required_transforms),
            "outcome": str(self.outcome),
        }


def assert_assessor_is_not_approver(assessor_reference: str, approver_reference: str) -> None:
    """`P12-DLP-003`: assessment and approval are separate acts by
    separate subjects."""
    if assessor_reference and assessor_reference == approver_reference:
        from epd2_privileged_access_service.exceptions import ExportSelfApprovalProhibitedError

        raise ExportSelfApprovalProhibitedError(
            "the DLP officer who assessed an export may not approve it"
        )


def assert_volume_within_limits(
    *,
    record_count: int,
    recent_export_count: int,
    policy: PrivilegedAccessPolicy,
) -> None:
    """Size and frequency limits (`P12-DLP-001`)."""
    if record_count > policy.export_max_records:
        raise DlpSizeLimitExceededError(
            f"{record_count} records exceeds the permitted export size {policy.export_max_records}"
        )
    if recent_export_count >= policy.export_frequency_limit:
        raise DlpFrequencyLimitExceededError(
            f"{recent_export_count} exports inside the frequency window reaches the limit "
            f"{policy.export_frequency_limit}"
        )


def assert_no_repeated_extraction_pattern(
    *,
    similar_request_digests: Sequence[str],
    policy: PrivilegedAccessPolicy,
) -> None:
    """Repeated near-identical requests indicate an extraction pattern
    rather than a need."""
    if len(similar_request_digests) >= policy.export_frequency_limit:
        raise DlpRepeatedRequestRiskError(
            "repeated similar export requests indicate an extraction pattern and require review"
        )


def assert_volume_not_anomalous(*, record_count: int, typical_record_count: int) -> None:
    """A volume anomaly requires review rather than refusal: the point is
    a human look, not a block."""
    if typical_record_count > 0 and record_count > typical_record_count * 10:
        raise DlpUnusualVolumeReviewError(
            "the requested volume is an order of magnitude above the typical export and "
            "requires review"
        )


def apply_transforms(
    rows: Sequence[Mapping[str, str]],
    *,
    transforms: frozenset[DlpControl],
    suppressed_fields: frozenset[str],
    masked_fields: frozenset[str],
    pseudonymized_fields: frozenset[str],
) -> tuple[Mapping[str, str], ...]:
    """Apply the transform set to a projection.

    Suppression removes the key entirely rather than blanking it: a
    present-but-empty field still discloses that the field exists for
    this record, which for some record classes is the disclosure."""
    result: list[Mapping[str, str]] = []
    for row in rows:
        transformed: dict[str, str] = {}
        for name, value in row.items():
            if DlpControl.FIELD_SUPPRESSION in transforms and name in suppressed_fields:
                continue
            if DlpControl.FIELD_MASKING in transforms and name in masked_fields:
                transformed[name] = "*" * min(len(value), 8)
                continue
            if DlpControl.PSEUDONYMIZATION in transforms and name in pseudonymized_fields:
                from epd2_privileged_access_service.domain import deterministic_digest

                transformed[name] = f"pseudo:{deterministic_digest(name, value)[:16]}"
                continue
            transformed[name] = value
        result.append(transformed)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class DlpPolicyProfile:
    """Which controls are active for one record class and recipient
    category, at a recorded version."""

    profile_id: UUID
    record_class: str
    active_controls: frozenset[DlpControl]
    suppressed_fields: frozenset[str] = frozenset()
    masked_fields: frozenset[str] = frozenset()
    pseudonymized_fields: frozenset[str] = frozenset()
    policy_version: str = "pack-12-dlp/v1"

    def __post_init__(self) -> None:
        require_text(self.record_class, "record_class")
        require_text(self.policy_version, "policy_version")
        missing = FAIL_CLOSED_CONTROLS - self.active_controls
        if missing:
            raise DlpAssessmentIncompleteError(
                f"a DLP profile must keep the fail-closed controls active; missing "
                f"{sorted(c.value for c in missing)}"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "profile_id": str(self.profile_id),
            "record_class": self.record_class,
            "active_controls": sorted(c.value for c in self.active_controls),
            "policy_version": self.policy_version,
        }


def default_dlp_profile(record_class: str, profile_id: UUID) -> DlpPolicyProfile:
    """A reference profile with every control active.

    Reference defaults for a reference implementation, not an approved
    operational policy."""
    return DlpPolicyProfile(
        profile_id=profile_id, record_class=record_class, active_controls=ALL_DLP_CONTROLS
    )


def frequency_window_start(at: datetime, policy: PrivilegedAccessPolicy) -> datetime:
    require_timezone(at, context="frequency_window_start")
    return at - policy.export_frequency_window


def is_within_window(moment: datetime, *, start: datetime, end: datetime) -> bool:
    return start <= moment <= end


def window_length(policy: PrivilegedAccessPolicy) -> timedelta:
    return policy.export_frequency_window

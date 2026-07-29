"""Data loss prevention (`P12-DLP-*`, ADR-066)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_privileged_access_service.dlp import (
    ALL_DLP_CONTROLS,
    FAIL_CLOSED_CONTROLS,
    WATERMARK_LIMITATION_NOTE,
    DlpAssessment,
    DlpControl,
    DlpFinding,
    DlpOutcome,
    apply_transforms,
    assert_assessor_is_not_approver,
    assert_no_repeated_extraction_pattern,
    assert_volume_not_anomalous,
    assert_volume_within_limits,
    default_dlp_profile,
    frequency_window_start,
    is_within_window,
    window_length,
)
from epd2_privileged_access_service.domain import OrganizationalScopeRef
from epd2_privileged_access_service.exceptions import (
    DlpAssessmentIncompleteError,
    DlpForbiddenDataDetectedError,
    DlpFrequencyLimitExceededError,
    DlpRepeatedRequestRiskError,
    DlpReviewRequiredError,
    DlpSizeLimitExceededError,
    DlpUnusualVolumeReviewError,
    ExportSelfApprovalProhibitedError,
)
from epd2_privileged_access_service.policy import REFERENCE_POLICY

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
SCOPE = OrganizationalScopeRef(organization_id=uuid4())


def _assessment(**overrides: object) -> DlpAssessment:
    base: dict[str, object] = {
        "assessment_id": uuid4(),
        "export_id": uuid4(),
        "organization_scope": SCOPE,
        "assessor_reference": "actor:dlp",
        "assessed_at": T0,
        "completed_controls": frozenset(ALL_DLP_CONTROLS),
        "findings": (),
        "required_transforms": frozenset(),
        "outcome": DlpOutcome.PASSED,
    }
    base.update(overrides)
    return DlpAssessment(**base)  # type: ignore[arg-type]


class TestControlInventory:
    def test_the_control_set_is_closed_and_non_trivial(self) -> None:
        assert len(ALL_DLP_CONTROLS) >= 15

    def test_fail_closed_controls_are_a_named_subset(self) -> None:
        """A control that is merely "recommended" is a control that will
        be skipped under time pressure. The fail-closed set says which
        ones cannot be."""
        assert FAIL_CLOSED_CONTROLS
        assert FAIL_CLOSED_CONTROLS <= ALL_DLP_CONTROLS


class TestAssessmentCompleteness:
    def test_an_incomplete_assessment_never_permits_an_export(self) -> None:
        incomplete = _assessment(
            completed_controls=ALL_DLP_CONTROLS - FAIL_CLOSED_CONTROLS,
            outcome=DlpOutcome.INCOMPLETE,
        )
        assert not incomplete.permits_export
        with pytest.raises(DlpAssessmentIncompleteError):
            incomplete.assert_permits_export()

    def test_a_refused_assessment_never_permits_an_export(self) -> None:
        with pytest.raises(DlpForbiddenDataDetectedError):
            _assessment(outcome=DlpOutcome.REFUSED).assert_permits_export()

    def test_manual_review_required_blocks_until_reviewed(self) -> None:
        """Not the same refusal as "refused": one says a human must look,
        the other says a human already did."""
        with pytest.raises(DlpReviewRequiredError):
            _assessment(outcome=DlpOutcome.MANUAL_REVIEW_REQUIRED).assert_permits_export()

    def test_transforms_required_still_permits_the_export(self) -> None:
        """The transforms are the condition, not a refusal - the export
        proceeds carrying them."""
        assert _assessment(outcome=DlpOutcome.TRANSFORMS_REQUIRED).permits_export

    def test_a_complete_passing_assessment_permits(self) -> None:
        _assessment().assert_permits_export()

    def test_a_finding_records_a_reference_never_the_value(self) -> None:
        """A DLP finding that quoted the matched value would put the very
        data the control exists to protect into the assessment record."""
        finding = DlpFinding(
            control=DlpControl.FORBIDDEN_DATA_DETECTION,
            field_name="notes",
            severity="blocking",
            detail_reference="finding:1",
        )
        payload = finding.to_payload()
        assert set(payload) == {"control", "field_name", "severity", "detail_reference"}


class TestSeparation:
    def test_the_assessor_may_not_approve_what_they_assessed(self) -> None:
        """`P12-DLP-003`: assessment is not decision."""
        with pytest.raises(ExportSelfApprovalProhibitedError):
            assert_assessor_is_not_approver("actor:dlp", "actor:dlp")
        assert_assessor_is_not_approver("actor:dlp", "actor:approver")


class TestVolumeControls:
    def test_a_size_beyond_the_policy_maximum_is_refused(self) -> None:
        with pytest.raises(DlpSizeLimitExceededError):
            assert_volume_within_limits(
                record_count=REFERENCE_POLICY.export_max_records + 1,
                recent_export_count=0,
                policy=REFERENCE_POLICY,
            )

    def test_frequency_within_the_window_is_bounded(self) -> None:
        with pytest.raises(DlpFrequencyLimitExceededError):
            assert_volume_within_limits(
                record_count=1,
                recent_export_count=REFERENCE_POLICY.export_frequency_limit,
                policy=REFERENCE_POLICY,
            )

    def test_repeated_extraction_is_caught_where_one_request_would_not_be(self) -> None:
        """Twenty small exports are a bulk extraction spread thin. A
        per-request size check cannot see it; this one can."""
        digests = ["d" * 64] * REFERENCE_POLICY.export_frequency_limit
        with pytest.raises(DlpRepeatedRequestRiskError):
            assert_no_repeated_extraction_pattern(
                similar_request_digests=digests, policy=REFERENCE_POLICY
            )

    def test_an_anomalous_volume_is_sent_to_review_not_refused(self) -> None:
        with pytest.raises(DlpUnusualVolumeReviewError):
            assert_volume_not_anomalous(record_count=10_000, typical_record_count=10)

    def test_an_ordinary_request_passes_every_volume_control(self) -> None:
        assert_volume_within_limits(record_count=10, recent_export_count=0, policy=REFERENCE_POLICY)
        assert_no_repeated_extraction_pattern(similar_request_digests=[], policy=REFERENCE_POLICY)
        assert_volume_not_anomalous(record_count=10, typical_record_count=10)


class TestTransforms:
    def test_suppression_removes_masking_replaces_pseudonymisation_stabilises(
        self,
    ) -> None:
        rows = [{"title": "Minutes", "notes": "sensitive", "member": "actor:1"}]
        out = apply_transforms(
            rows,
            transforms=frozenset(
                {
                    DlpControl.FIELD_SUPPRESSION,
                    DlpControl.FIELD_MASKING,
                    DlpControl.PSEUDONYMIZATION,
                }
            ),
            suppressed_fields=frozenset({"notes"}),
            masked_fields=frozenset({"title"}),
            pseudonymized_fields=frozenset({"member"}),
        )
        assert "notes" not in out[0]
        assert out[0]["title"] != "Minutes"
        assert out[0]["member"] != "actor:1"

    def test_pseudonymisation_is_stable_within_a_call(self) -> None:
        rows = [{"member": "actor:1"}, {"member": "actor:1"}, {"member": "actor:2"}]
        out = apply_transforms(
            rows,
            transforms=frozenset({DlpControl.PSEUDONYMIZATION}),
            suppressed_fields=frozenset(),
            masked_fields=frozenset(),
            pseudonymized_fields=frozenset({"member"}),
        )
        assert out[0]["member"] == out[1]["member"]
        assert out[0]["member"] != out[2]["member"]

    def test_no_transform_leaves_rows_untouched(self) -> None:
        rows = [{"title": "Minutes"}]
        out = apply_transforms(
            rows,
            transforms=frozenset(),
            suppressed_fields=frozenset(),
            masked_fields=frozenset(),
            pseudonymized_fields=frozenset(),
        )
        assert out == ({"title": "Minutes"},)


class TestWatermarkHonesty:
    def test_the_limitation_is_stated_where_the_control_lives(self) -> None:
        """`P12-DLP-004`: a watermark marks a copy. It does not stop one
        being made, and the code must not imply otherwise."""
        assert "P12-DLP-004" in WATERMARK_LIMITATION_NOTE
        assert "reaches no copy the recipient already holds" in WATERMARK_LIMITATION_NOTE


class TestWindows:
    def test_the_frequency_window_is_taken_from_the_policy(self) -> None:
        start = frequency_window_start(T0, REFERENCE_POLICY)
        assert T0 - start == REFERENCE_POLICY.export_frequency_window
        assert window_length(REFERENCE_POLICY) == REFERENCE_POLICY.export_frequency_window

    def test_window_membership_is_inclusive_at_both_ends(self) -> None:
        """Inclusive, deliberately: a frequency window that excluded its
        own boundary would let a request placed exactly on the edge
        escape the count."""
        end = T0 + timedelta(hours=1)
        assert is_within_window(T0, start=T0, end=end)
        assert is_within_window(end, start=T0, end=end)
        assert not is_within_window(end + timedelta(seconds=1), start=T0, end=end)


class TestProfiles:
    def test_a_default_profile_names_its_record_class_and_version(self) -> None:
        profile = default_dlp_profile("membership_record", uuid4())
        assert profile.record_class == "membership_record"
        assert profile.policy_version

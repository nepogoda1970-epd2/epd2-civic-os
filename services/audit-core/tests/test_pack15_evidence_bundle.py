"""PACK-15 audit separation and `EvidenceBundle` v1 tests (ADR-097).

Asserts stream separation, the closed section list, the prohibited-content
list, the nine validation checks, complementary small-cell suppression,
export authorization, and the intermediate-tally prohibition.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from epd2_audit_core.voting_evidence_bundle import (
    BUNDLE_SCHEMA_VERSION,
    BUNDLE_SECTIONS,
    AuditStream,
    BundleSigningCustody,
    EvidenceBundleInvalidError,
    EvidenceBundlePreclosureRefusedError,
    EvidenceBundleScopeRefusedError,
    IntermediateTallyProhibitedError,
    assert_export_authorized,
    assert_no_intermediate_tally,
    assert_streams_separable,
    build_bundle,
    suppress_small_cells,
    validate_bundle,
)

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


def _bundle(*, context_closed: bool = True, custody: BundleSigningCustody | None = None):  # type: ignore[no-untyped-def]
    custody = custody or BundleSigningCustody()
    return build_bundle(
        voting_context_reference="vc-1",
        context_metadata={"voting_type": "organizational_election"},
        configuration_versions={"rule_set_version": "1.0.0", "timing_profile": "reference"},
        eligibility_totals={"approved": 40, "denied": 12, "review_required": 9},
        assertion_totals={"minted": 40, "queued": 40, "released": 40, "picked_up": 38},
        credential_totals={"issued": 38, "redeemed": 35, "revoked": 0},
        integrity_commitments={"AS-03": "abc123"},
        provenance={"authority": "independent_auditor"},
        minimum_cell=5,
        generated_at_bucket=NOW,
        custody=custody,
        context_closed=context_closed,
    )


def test_no_export_may_span_the_identity_side_and_the_voting_side() -> None:
    with pytest.raises(EvidenceBundleScopeRefusedError):
        assert_streams_separable([AuditStream.ASSERTION, AuditStream.CREDENTIAL])
    with pytest.raises(EvidenceBundleScopeRefusedError):
        assert_streams_separable([AuditStream.ELIGIBILITY, AuditStream.CREDENTIAL])
    assert_streams_separable([AuditStream.ELIGIBILITY, AuditStream.ASSERTION])
    assert_streams_separable([AuditStream.CREDENTIAL])


def test_there_are_six_streams() -> None:
    assert len(list(AuditStream)) == 6


def test_the_bundle_section_list_is_closed_and_complete() -> None:
    bundle = _bundle()
    assert sorted(bundle.sections) == sorted(BUNDLE_SECTIONS)
    assert len(BUNDLE_SECTIONS) == 8
    assert bundle.bundle_schema_version == BUNDLE_SCHEMA_VERSION


def test_a_bundle_carrying_a_forbidden_key_is_refused() -> None:
    custody = BundleSigningCustody()
    for forbidden in ("account_id", "context_pseudonym", "voting_credential_id", "ballot_id"):
        with pytest.raises(EvidenceBundleInvalidError):
            build_bundle(
                voting_context_reference="vc-1",
                context_metadata={forbidden: "x"},
                configuration_versions={},
                eligibility_totals={},
                assertion_totals={},
                credential_totals={},
                integrity_commitments={},
                provenance={},
                minimum_cell=5,
                generated_at_bucket=NOW,
                custody=custody,
                context_closed=True,
            )


def test_a_valid_bundle_validates_and_a_tampered_one_does_not() -> None:
    custody = BundleSigningCustody()
    bundle = _bundle(custody=custody)
    validate_bundle(bundle, custody=custody)
    other = BundleSigningCustody(secret=b"a-different-key")
    with pytest.raises(EvidenceBundleInvalidError):
        validate_bundle(bundle, custody=other)


def test_small_cells_are_suppressed_not_rounded_and_complementary() -> None:
    published, suppressed = suppress_small_cells(
        {"a": 40, "b": 3, "c": 20}, minimum_cell=5, section="eligibility_totals"
    )
    assert published["b"] is None
    assert len(suppressed) == 2, "a lone suppressed cell is recoverable by differencing"
    assert {cell.method for cell in suppressed} == {"primary", "complementary"}


def test_suppression_below_the_floor_is_refused() -> None:
    with pytest.raises(EvidenceBundleInvalidError):
        suppress_small_cells({"a": 1}, minimum_cell=3, section="eligibility_totals")


def test_count_consistency_is_enforced() -> None:
    custody = BundleSigningCustody()
    with pytest.raises(EvidenceBundleInvalidError):
        bad = build_bundle(
            voting_context_reference="vc-1",
            context_metadata={},
            configuration_versions={},
            eligibility_totals={"approved": 40},
            assertion_totals={"minted": 10, "queued": 40, "released": 40, "picked_up": 38},
            credential_totals={"issued": 38, "redeemed": 35},
            integrity_commitments={},
            provenance={},
            minimum_cell=5,
            generated_at_bucket=NOW,
            custody=custody,
            context_closed=True,
        )
        validate_bundle(bad, custody=custody)


def test_redeemed_may_not_exceed_issued() -> None:
    custody = BundleSigningCustody()
    bundle = build_bundle(
        voting_context_reference="vc-1",
        context_metadata={},
        configuration_versions={},
        eligibility_totals={"approved": 40},
        assertion_totals={"minted": 40, "queued": 40, "released": 40, "picked_up": 38},
        credential_totals={"issued": 30, "redeemed": 35},
        integrity_commitments={},
        provenance={},
        minimum_cell=5,
        generated_at_bucket=NOW,
        custody=custody,
        context_closed=True,
    )
    with pytest.raises(EvidenceBundleInvalidError):
        validate_bundle(bundle, custody=custody)


def test_a_pre_closure_bundle_carries_no_outcome_bearing_totals() -> None:
    custody = BundleSigningCustody()
    bundle = _bundle(context_closed=False, custody=custody)
    validate_bundle(bundle, custody=custody)
    for section in ("eligibility_totals", "assertion_totals", "credential_totals"):
        assert bundle.sections[section] == {"suppressed": "pre_closure"}


def test_export_authorization_requires_the_auditor_role_a_grant_and_one_context() -> None:
    with pytest.raises(EvidenceBundleScopeRefusedError):
        assert_export_authorized(
            role="eligibility_officer",
            grant_reference="g",
            contexts=["vc-1"],
            streams=[AuditStream.CREDENTIAL],
            context_closed=True,
            dual_control_reference=None,
        )
    with pytest.raises(EvidenceBundleScopeRefusedError):
        assert_export_authorized(
            role="independent_auditor",
            grant_reference=None,
            contexts=["vc-1"],
            streams=[AuditStream.CREDENTIAL],
            context_closed=True,
            dual_control_reference=None,
        )
    with pytest.raises(EvidenceBundleScopeRefusedError):
        assert_export_authorized(
            role="independent_auditor",
            grant_reference="g",
            contexts=["vc-1", "vc-2"],
            streams=[AuditStream.CREDENTIAL],
            context_closed=True,
            dual_control_reference=None,
        )
    assert_export_authorized(
        role="independent_auditor",
        grant_reference="g",
        contexts=["vc-1"],
        streams=[AuditStream.CREDENTIAL],
        context_closed=True,
        dual_control_reference=None,
    )


def test_a_pre_closure_export_requires_dual_control() -> None:
    with pytest.raises(EvidenceBundlePreclosureRefusedError):
        assert_export_authorized(
            role="independent_auditor",
            grant_reference="g",
            contexts=["vc-1"],
            streams=[AuditStream.CREDENTIAL],
            context_closed=False,
            dual_control_reference=None,
        )
    assert_export_authorized(
        role="independent_auditor",
        grant_reference="g",
        contexts=["vc-1"],
        streams=[AuditStream.CREDENTIAL],
        context_closed=False,
        dual_control_reference="dual-1",
    )


@pytest.mark.parametrize(
    "key",
    ["vote_totals", "option_totals", "candidate_totals", "turnout", "partial_results"],
)
def test_outcome_bearing_disclosure_before_closure_is_refused(key: str) -> None:
    with pytest.raises(IntermediateTallyProhibitedError):
        assert_no_intermediate_tally({key: 1}, context_closed=False)
    assert_no_intermediate_tally({key: 1}, context_closed=True)

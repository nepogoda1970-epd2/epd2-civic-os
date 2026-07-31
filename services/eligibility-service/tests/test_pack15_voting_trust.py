"""PACK-15 identity-side unit, invariant and privacy tests.

Covers the timing controls (`OD-P15-02`), the scoped-attribute adapter,
the eligibility/assertion domain, the assertion issuer's signing boundary
(`OD-P15-01`) and the PACK-14 handoff acceptance boundary.

Every test here asserts a property the specification states normatively;
none asserts an implementation detail that could change without the
architecture changing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from epd2_core.event_envelope import ActorRef
from epd2_eligibility_service.voting_assertion_issuer import (
    AssertionIssuer,
    FutureKeyServiceCustody,
    MinimizedDecisionInput,
    SystemSecureRandom,
    TestKeyCustody,
    assert_production_custody,
)
from epd2_eligibility_service.voting_attributes import (
    PERMITTED_ATTRIBUTE_NAMES,
    PROHIBITED_ATTRIBUTE_NAMES,
    ingest_scoped_attributes,
)
from epd2_eligibility_service.voting_eligibility import (
    ASSERTION_FIELD_NAMES,
    ASSERTION_PURPOSE,
    ASSERTION_RESULT_APPROVED,
    AssertionStatus,
    EligibilityAssertion,
    EligibilityDecisionStatus,
    assert_no_assertion_credential_pair,
    transition_permitted,
)
from epd2_eligibility_service.voting_handoff import (
    HandoffAcceptance,
    HandoffBinding,
    VotingHandoffArtifact,
    verify_handoff,
)
from epd2_eligibility_service.voting_timing import (
    DEFAULT_MINIMUM_COHORT_SIZE,
    ISSUANCE_MODE_QUEUED,
    IssuanceTimingProfile,
    classify_cohort_size,
    coarsen,
)
from epd2_eligibility_service.voting_trust_events import (
    ASSERTION_MINTED,
    build_assertion_event,
)
from epd2_eligibility_service.voting_trust_exceptions import (
    HandoffAlreadyUsedError,
    HandoffAudienceMismatchError,
    HandoffOriginMismatchError,
    IssuanceWindowGuaranteeError,
    ProhibitedAttributeError,
    SystemDependencyUnavailableError,
    TimingProfileOutOfBoundsError,
    UndeclaredAttributeError,
    VotingBoundaryIntegrityError,
)

NOW = datetime(2026, 8, 1, 10, 7, 42, tzinfo=UTC)
AUDIENCE = "credential-issuer"


def _issuer(profile: IssuanceTimingProfile | None = None) -> AssertionIssuer:
    return AssertionIssuer(
        custody=TestKeyCustody(),
        random=SystemSecureRandom(),
        profile=profile or IssuanceTimingProfile(),
        audience=AUDIENCE,
    )


def _decision() -> MinimizedDecisionInput:
    return MinimizedDecisionInput(
        voting_context_reference="vc-1",
        eligibility_result=ASSERTION_RESULT_APPROVED,
        eligibility_class="full_member",
        organizational_scope="DE-BE-01",
        required_assurance_satisfied=True,
    )


# -- timing controls (OD-P15-02) --------------------------------------------


def test_queued_is_the_only_issuance_mode() -> None:
    assert IssuanceTimingProfile().issuance_mode == ISSUANCE_MODE_QUEUED
    with pytest.raises(TimingProfileOutOfBoundsError):
        IssuanceTimingProfile(issuance_mode="immediate")


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("timestamp_granularity_seconds", 30),
        ("release_delay_min_seconds", 5),
        ("minimum_cohort_size", 1),
        ("cohort_wait_max_seconds", 60),
        ("disclosure_min_cell", 3),
    ],
)
def test_values_below_the_hard_floor_are_refused_never_clamped(field_name: str, value: int) -> None:
    overrides: dict[str, Any] = {field_name: value}
    with pytest.raises(TimingProfileOutOfBoundsError):
        IssuanceTimingProfile(**overrides)


def test_release_window_may_not_collapse_to_a_fixed_offset() -> None:
    with pytest.raises(TimingProfileOutOfBoundsError):
        IssuanceTimingProfile(release_delay_min_seconds=100, release_delay_max_seconds=120)


def test_small_electorate_raises_the_cohort_and_forbids_per_scope_metrics() -> None:
    profile = IssuanceTimingProfile()
    assert profile.is_small_electorate(11)
    assert profile.effective_minimum_cohort(11) == 3
    assert profile.effective_minimum_cohort(400) == DEFAULT_MINIMUM_COHORT_SIZE
    assert profile.effective_timestamp_granularity(11) >= 3600
    assert profile.per_scope_metrics_permitted(11) is False
    assert profile.per_scope_metrics_permitted(800) is True


def test_timestamps_are_coarsened_to_the_governed_bucket() -> None:
    assert coarsen(NOW, 300).isoformat() == "2026-08-01T10:05:00+00:00"


def test_cohort_of_one_is_never_released_immediately() -> None:
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    entry = issuer.enqueue(assertion, batch_reference="b1", now=NOW, jitter_fraction=0.5)
    release_now, cohort_class, below = issuer.release_decision(
        entry, cohort_size=1, now=entry.release_not_before, eligible_population=800
    )
    assert release_now is False
    assert cohort_class is classify_cohort_size(1, DEFAULT_MINIMUM_COHORT_SIZE)
    assert below is True


def test_access_is_never_denied_for_want_of_a_cohort() -> None:
    """At `cohort_wait_max` the assertion is released regardless."""
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    entry = issuer.enqueue(assertion, batch_reference="b1", now=NOW, jitter_fraction=0.0)
    release_now, _, below = issuer.release_decision(
        entry, cohort_size=1, now=entry.cohort_wait_deadline, eligible_population=800
    )
    assert release_now is True
    assert below is True


def test_a_full_cohort_releases_at_its_scheduled_time() -> None:
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    entry = issuer.enqueue(assertion, batch_reference="b1", now=NOW, jitter_fraction=1.0)
    release_now, _, below = issuer.release_decision(
        entry,
        cohort_size=DEFAULT_MINIMUM_COHORT_SIZE,
        now=entry.release_not_before,
        eligible_population=800,
    )
    assert release_now is True
    assert below is False


def test_the_window_guarantee_refuses_a_profile_that_could_strand_an_assertion() -> None:
    profile = IssuanceTimingProfile()
    with pytest.raises(IssuanceWindowGuaranteeError):
        profile.assert_window_guarantee(
            issuance_window_start=NOW,
            issuance_window_end=NOW + timedelta(minutes=30),
            eligible_population=800,
        )
    profile.assert_window_guarantee(
        issuance_window_start=NOW,
        issuance_window_end=NOW + timedelta(days=2),
        eligible_population=800,
    )


# -- scoped attribute adapter -----------------------------------------------


@pytest.mark.parametrize("prohibited", sorted(PROHIBITED_ATTRIBUTE_NAMES))
def test_every_prohibited_identity_attribute_is_refused(prohibited: str) -> None:
    with pytest.raises(ProhibitedAttributeError):
        ingest_scoped_attributes(
            {prohibited: "value"},
            declared_names=frozenset({prohibited}),
            source_owner="membership-service",
            source_version="v1",
        )


def test_an_undeclared_attribute_is_refused_not_dropped() -> None:
    with pytest.raises(UndeclaredAttributeError):
        ingest_scoped_attributes(
            {"membership_active": True},
            declared_names=frozenset({"age_threshold_met"}),
            source_owner="membership-service",
            source_version="v1",
        )


def test_a_predicate_must_arrive_as_a_predicate_not_as_its_source_value() -> None:
    with pytest.raises(UndeclaredAttributeError):
        ingest_scoped_attributes(
            {"membership_active": "active"},
            declared_names=frozenset({"membership_active"}),
            source_owner="membership-service",
            source_version="v1",
        )


def test_permitted_and_prohibited_attribute_sets_are_disjoint() -> None:
    assert not (PERMITTED_ATTRIBUTE_NAMES & PROHIBITED_ATTRIBUTE_NAMES)


def test_no_permitted_attribute_is_a_date_of_birth_or_an_address() -> None:
    assert "date_of_birth" not in PERMITTED_ATTRIBUTE_NAMES
    assert "address" not in PERMITTED_ATTRIBUTE_NAMES
    assert "age_threshold_met" in PERMITTED_ATTRIBUTE_NAMES


# -- the crossing artifact --------------------------------------------------


def test_the_assertion_wire_payload_is_exactly_the_closed_twelve_field_list() -> None:
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    assert sorted(assertion.wire_payload()) == sorted(ASSERTION_FIELD_NAMES)
    assert len(ASSERTION_FIELD_NAMES) == 12


def test_a_denial_is_never_asserted_across_the_boundary() -> None:
    with pytest.raises(VotingBoundaryIntegrityError):
        EligibilityAssertion(
            assertion_id=uuid4(),
            voting_context_reference="vc-1",
            eligibility_result="denied",
            eligibility_class="full_member",
            organizational_scope="DE-BE-01",
            required_assurance_satisfied=True,
            issued_at_bucket=NOW,
            expires_at=NOW + timedelta(hours=1),
            audience=AUDIENCE,
            purpose=ASSERTION_PURPOSE,
            nonce="n",
            status=AssertionStatus.MINTED,
        )


def test_no_payload_may_pair_an_assertion_with_a_credential() -> None:
    with pytest.raises(VotingBoundaryIntegrityError):
        assert_no_assertion_credential_pair({"assertion_id": "a", "voting_credential_id": "c"})
    assert_no_assertion_credential_pair({"assertion_id": "a"})
    assert_no_assertion_credential_pair({"voting_credential_id": "c"})


def test_the_nonce_is_high_entropy_and_not_derived_from_the_decision() -> None:
    issuer = _issuer()
    first = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    second = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    assert first.nonce != second.nonce
    assert len(first.nonce) == 64


def test_assertion_integrity_verifies_and_a_tampered_assertion_does_not() -> None:
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    assert issuer.verify_integrity(assertion) is True
    tampered = EligibilityAssertion(
        assertion_id=assertion.assertion_id,
        voting_context_reference="vc-2",
        eligibility_result=assertion.eligibility_result,
        eligibility_class=assertion.eligibility_class,
        organizational_scope=assertion.organizational_scope,
        required_assurance_satisfied=assertion.required_assurance_satisfied,
        issued_at_bucket=assertion.issued_at_bucket,
        expires_at=assertion.expires_at,
        audience=assertion.audience,
        purpose=assertion.purpose,
        nonce=assertion.nonce,
        status=assertion.status,
        integrity_metadata=assertion.integrity_metadata,
    )
    assert issuer.verify_integrity(tampered) is False


# -- the signing boundary (OD-P15-01) ---------------------------------------


def test_a_test_signing_key_is_refused_outside_a_test_trust_store() -> None:
    with pytest.raises(SystemDependencyUnavailableError):
        assert_production_custody(TestKeyCustody())


def test_an_unbound_key_service_fails_closed_rather_than_signing() -> None:
    custody = FutureKeyServiceCustody()
    for call in (lambda: custody.key_identifier(), lambda: custody.sign(b"x")):
        with pytest.raises(SystemDependencyUnavailableError):
            call()


def test_the_minimized_decision_input_carries_no_participant_field() -> None:
    fields = set(MinimizedDecisionInput.__dataclass_fields__)
    assert fields == {
        "voting_context_reference",
        "eligibility_result",
        "eligibility_class",
        "organizational_scope",
        "required_assurance_satisfied",
    }


# -- handoff acceptance -----------------------------------------------------


def _artifact() -> VotingHandoffArtifact:
    return VotingHandoffArtifact(
        value="opaque-artifact-value",
        voting_context_reference="vc-1",
        audience="pack15-boundary",
        origin="https://vote.epd.example",
        expires_at=NOW + timedelta(minutes=5),
    )


def _binding() -> HandoffBinding:
    return HandoffBinding(
        expected_audience="pack15-boundary",
        allowed_origins=("https://vote.epd.example",),
    )


def test_a_handoff_is_single_use() -> None:
    digest = verify_handoff(
        _artifact(),
        binding=_binding(),
        voting_context_reference="vc-1",
        now=NOW,
        previous=None,
    )
    previous = HandoffAcceptance(
        acceptance_id=uuid4(),
        artifact_digest=digest,
        voting_context_reference="vc-1",
        audience="pack15-boundary",
        origin="https://vote.epd.example",
        accepted_at=NOW,
    )
    with pytest.raises(HandoffAlreadyUsedError):
        verify_handoff(
            _artifact(),
            binding=_binding(),
            voting_context_reference="vc-1",
            now=NOW,
            previous=previous,
        )


def test_origin_and_audience_are_checked_before_anything_else_is_read() -> None:
    wrong_origin = VotingHandoffArtifact(
        value="v",
        voting_context_reference="vc-1",
        audience="pack15-boundary",
        origin="https://app.epd.example",
        expires_at=NOW + timedelta(minutes=5),
    )
    with pytest.raises(HandoffOriginMismatchError):
        verify_handoff(
            wrong_origin,
            binding=_binding(),
            voting_context_reference="vc-1",
            now=NOW,
            previous=None,
        )
    wrong_audience = VotingHandoffArtifact(
        value="v",
        voting_context_reference="vc-1",
        audience="someone-else",
        origin="https://vote.epd.example",
        expires_at=NOW + timedelta(minutes=5),
    )
    with pytest.raises(HandoffAudienceMismatchError):
        verify_handoff(
            wrong_audience,
            binding=_binding(),
            voting_context_reference="vc-1",
            now=NOW,
            previous=None,
        )


def test_a_handoff_acceptance_record_carries_no_account_field() -> None:
    fields = set(HandoffAcceptance.__dataclass_fields__)
    assert "account_id" not in fields
    assert "person_id" not in fields
    assert "session_id" not in fields
    assert "participant_reference" not in fields


# -- events -----------------------------------------------------------------


def test_an_assertion_event_carries_no_credential_reference_and_is_coarsened() -> None:
    issuer = _issuer()
    assertion = issuer.mint(
        assertion_id=uuid4(),
        decision=_decision(),
        now=NOW,
        expires_at=NOW + timedelta(hours=4),
        eligible_population=800,
    )
    event = build_assertion_event(
        event_id=uuid4(),
        event_type=ASSERTION_MINTED,
        assertion=assertion,
        granularity_seconds=300,
        actor=ActorRef(actor_id=uuid4(), actor_type="service"),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=NOW,
    )
    assert "voting_credential_id" not in event.payload
    assert "nonce" not in event.payload
    assert event.occurred_at.second == 0
    assert event.producer == "eligibility-service"


# -- decision transitions ---------------------------------------------------


def test_a_superseded_decision_is_terminal() -> None:
    assert transition_permitted(
        EligibilityDecisionStatus.APPROVED, EligibilityDecisionStatus.SUPERSEDED
    )
    assert not transition_permitted(
        EligibilityDecisionStatus.SUPERSEDED, EligibilityDecisionStatus.APPROVED
    )


def test_review_required_is_not_a_denial() -> None:
    """The difference is what the participant must do next.

    A denial is contestable and terminal until disputed; a review is a
    wait. Asserting the two enum members are distinct would be a
    tautology, so what is asserted here is the thing that actually
    differs: `review_required` still has a path to `approved` through
    review, and `denied` does not.
    """
    assert transition_permitted(
        EligibilityDecisionStatus.REVIEW_REQUIRED, EligibilityDecisionStatus.UNDER_REVIEW
    )
    assert transition_permitted(
        EligibilityDecisionStatus.UNDER_REVIEW, EligibilityDecisionStatus.APPROVED
    )
    assert not transition_permitted(
        EligibilityDecisionStatus.DENIED, EligibilityDecisionStatus.UNDER_REVIEW
    )
    assert not transition_permitted(
        EligibilityDecisionStatus.DENIED, EligibilityDecisionStatus.APPROVED
    )
    # The only way out of a denial is a dispute, which is the appeal path
    # the reason code is required to name.
    assert transition_permitted(
        EligibilityDecisionStatus.DENIED, EligibilityDecisionStatus.DISPUTED
    )

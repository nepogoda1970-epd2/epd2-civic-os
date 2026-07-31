"""PACK-15 Voting Context Registry tests (VC-01).

Asserts the properties the specification states normatively: dual-control
activation, the immutable activation snapshot, the revocation-cutoff
maxima, the disclosure floor, the small-electorate rule, the prohibition
on activating the public-election profile, and that a voting context
carries no participant or outcome data at all.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_governance_service.voting_contexts import (
    CLOSED_STATUSES,
    FORBIDDEN_FIELD_NAMES,
    ActivationSnapshot,
    DisclosureControlProfile,
    DualControlRequiredError,
    InMemoryVotingContextStore,
    VotingContext,
    VotingContextConfigurationInvalidError,
    VotingContextNotActiveError,
    VotingContextScopeMismatchError,
    VotingContextStatus,
    VotingType,
    VotingWindow,
    assert_no_participant_data,
    compute_snapshot_digest,
)

NOW = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)


def _context(
    *,
    voting_type: VotingType = VotingType.ORGANIZATIONAL_ELECTION,
    status: VotingContextStatus = VotingContextStatus.CONFIGURED,
    cutoff_offset: timedelta = timedelta(0),
    eligible_population: int = 800,
) -> VotingContext:
    voting_window = VotingWindow(starts_at=NOW + timedelta(days=2), ends_at=NOW + timedelta(days=4))
    issuance_window = VotingWindow(starts_at=NOW, ends_at=NOW + timedelta(days=2))
    return VotingContext(
        voting_context_id=uuid4(),
        voting_context_reference="vc-1",
        version=1,
        voting_type=voting_type,
        organizational_scope="DE-BE",
        status=status,
        voting_window=voting_window,
        credential_issuance_window=issuance_window,
        revocation_cutoff=voting_window.starts_at + cutoff_offset,
        eligibility_rule_set_reference="rs-1",
        eligibility_rule_set_version="1.0.0",
        required_assurance="substantial",
        participation_class="full_member",
        privacy_profile="standard",
        audit_profile="standard",
        disclosure_control=DisclosureControlProfile(),
        eligible_population=eligible_population,
    )


def test_activation_requires_two_distinct_approvers() -> None:
    context = _context()
    with pytest.raises(DualControlRequiredError):
        context.activate(now=NOW, approver="ops", second_approver="ops")
    with pytest.raises(DualControlRequiredError):
        context.activate(now=NOW, approver="ops", second_approver="")
    activated = context.activate(now=NOW, approver="ops", second_approver="governance")
    assert activated.status is VotingContextStatus.ACTIVE


def test_activation_captures_an_immutable_snapshot_of_the_critical_parameters() -> None:
    activated = _context().activate(now=NOW, approver="ops", second_approver="governance")
    snapshot = activated.activation_snapshot
    assert isinstance(snapshot, ActivationSnapshot)
    assert snapshot.snapshot_digest == compute_snapshot_digest(activated.critical_parameters())
    activated.assert_snapshot_intact()


def test_a_drifted_critical_parameter_is_detected() -> None:
    activated = _context().activate(now=NOW, approver="ops", second_approver="governance")
    drifted = VotingContext(
        voting_context_id=activated.voting_context_id,
        voting_context_reference=activated.voting_context_reference,
        version=activated.version,
        voting_type=activated.voting_type,
        organizational_scope="DE-BY",
        status=activated.status,
        voting_window=activated.voting_window,
        credential_issuance_window=activated.credential_issuance_window,
        revocation_cutoff=activated.revocation_cutoff,
        eligibility_rule_set_reference=activated.eligibility_rule_set_reference,
        eligibility_rule_set_version=activated.eligibility_rule_set_version,
        required_assurance=activated.required_assurance,
        participation_class=activated.participation_class,
        privacy_profile=activated.privacy_profile,
        audit_profile=activated.audit_profile,
        disclosure_control=activated.disclosure_control,
        eligible_population=activated.eligible_population,
        activation_snapshot=activated.activation_snapshot,
    )
    with pytest.raises(VotingContextConfigurationInvalidError):
        drifted.assert_snapshot_intact()


def test_a_critical_change_requires_a_new_version_that_must_be_activated_again() -> None:
    activated = _context().activate(now=NOW, approver="ops", second_approver="governance")
    next_version = activated.new_version_with(required_assurance="high")
    assert next_version.version == activated.version + 1
    assert next_version.status is VotingContextStatus.DRAFT
    assert next_version.activation_snapshot is None


def test_the_public_election_profile_is_never_activated() -> None:
    context = _context(voting_type=VotingType.PUBLIC_ELECTION_PROFILE)
    with pytest.raises(VotingContextConfigurationInvalidError):
        context.activate(now=NOW, approver="ops", second_approver="governance")


def test_the_revocation_cutoff_maximum_is_enforced_per_context_type() -> None:
    with pytest.raises(VotingContextConfigurationInvalidError):
        _context(voting_type=VotingType.ORGANIZATIONAL_ELECTION, cutoff_offset=timedelta(hours=1))
    _context(voting_type=VotingType.ORGANIZATIONAL_ELECTION, cutoff_offset=timedelta(0))


def test_the_disclosure_minimum_cell_has_a_floor_of_five() -> None:
    with pytest.raises(VotingContextConfigurationInvalidError):
        DisclosureControlProfile(minimum_cell=3)
    assert DisclosureControlProfile().minimum_cell == 5


def test_a_small_electorate_publishes_no_per_scope_metric() -> None:
    with pytest.raises(VotingContextConfigurationInvalidError):
        DisclosureControlProfile(small_electorate=True, per_scope_metrics_permitted=True)
    DisclosureControlProfile(small_electorate=True, per_scope_metrics_permitted=False)


def test_issuance_is_refused_outside_the_issuance_state_and_window() -> None:
    context = _context(status=VotingContextStatus.ISSUANCE_OPEN)
    context.assert_issuance_permitted(NOW + timedelta(hours=1))
    with pytest.raises(VotingContextNotActiveError):
        context.assert_issuance_permitted(NOW + timedelta(days=3))
    with pytest.raises(VotingContextNotActiveError):
        _context(status=VotingContextStatus.ACTIVE).assert_issuance_permitted(NOW)


def test_scope_isolation_is_enforced() -> None:
    context = _context()
    context.assert_scope("DE-BE")
    with pytest.raises(VotingContextScopeMismatchError):
        context.assert_scope("DE-BY")


def test_a_voting_context_carries_no_participant_or_outcome_data() -> None:
    fields = set(VotingContext.__dataclass_fields__)
    assert not (fields & FORBIDDEN_FIELD_NAMES)
    with pytest.raises(VotingContextConfigurationInvalidError):
        assert_no_participant_data({"turnout": 5})
    with pytest.raises(VotingContextConfigurationInvalidError):
        assert_no_participant_data({"account_id": "a"})


def test_outcome_evidence_is_only_available_after_closure() -> None:
    assert not _context(status=VotingContextStatus.ISSUANCE_OPEN).closed_for_outcome_evidence
    assert _context(status=VotingContextStatus.VOTING_CLOSED).closed_for_outcome_evidence
    assert VotingContextStatus.VOTING_CLOSED in CLOSED_STATUSES


def test_a_forbidden_transition_is_refused() -> None:
    context = _context(status=VotingContextStatus.ISSUANCE_OPEN)
    with pytest.raises(VotingContextNotActiveError):
        context.transition(VotingContextStatus.TALLIED)
    assert context.transition(VotingContextStatus.ISSUANCE_CLOSED).status is (
        VotingContextStatus.ISSUANCE_CLOSED
    )


def test_the_store_keeps_versions_separately() -> None:
    store = InMemoryVotingContextStore()
    first = _context()
    store.save(first)
    activated = first.activate(now=NOW, approver="ops", second_approver="governance")
    store.save(activated)
    second = activated.new_version_with(required_assurance="high")
    store.save(second)
    assert len(store.versions("vc-1")) == 2
    latest = store.latest("vc-1")
    assert latest is not None and latest.version == 2

"""Domain tests for data-protection governance and the DPIA gate
(Architecture & Domain Framework 0.8.1 section 13.1), plus records
classification and Legal Hold propagation (section 11).

The gate these tests defend is the one that decides whether a processing
activity may run at all. Its most important property is that it fails
closed on *absence*: an activity nobody ever assessed is not an activity
that passed.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_compliance_service.dataprotection import (
    DPIA_REQUIRING_RISK_CLASSES,
    ConsentWithdrawalRecord,
    DataProtectionImpactAssessment,
    DPIARequirementDetermination,
    DPIAStatus,
    ProcessingActivationDecision,
    ProcessingActivationState,
    ProcessingRiskClass,
    TransferAssessment,
    TransferMechanism,
    assert_activation_permitted,
    assert_dpo_independence,
)
from epd2_compliance_service.domain import (
    DataClassification,
    DerivativeKind,
    HoldPropagationRecord,
    PropagationState,
    RecordClass,
    RecordSensitivity,
    SearchExportEligibility,
    assert_hold_propagation_resolved,
)
from epd2_compliance_service.exceptions import (
    DPIANotApprovedError,
    DPIARequiredError,
    DPOIndependenceRequiredError,
    LegalHoldPropagationUnresolvedError,
    ProceduralRoleConflictError,
)

T0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
T1 = T0 + timedelta(days=30)
T2 = T0 + timedelta(days=400)

ORG = uuid4()
ACTIVITY_ID = uuid4()
HOLD_ID = uuid4()
REVIEWER = uuid4()
CONTROLLER = uuid4()
PROCESS_OWNER = uuid4()
OWNER = uuid4()
CUSTODIAN = uuid4()
DISPOSITION_AUTHORITY = uuid4()


def _requirement(*, required: bool = True) -> DPIARequirementDetermination:
    return DPIARequirementDetermination(
        determination_id=uuid4(),
        activity_id=ACTIVITY_ID,
        organization_id=ORG,
        risk_class=ProcessingRiskClass.HIGH if required else ProcessingRiskClass.LOW,
        dpia_required=required,
        determined_at=T0,
        determined_by_party_reference=REVIEWER,
        basis_reference="dp-policy:risk-matrix:v2",
    )


def _dpia(
    *, status: DPIAStatus = DPIAStatus.APPROVED, valid_until: datetime | None = T2
) -> DataProtectionImpactAssessment:
    return DataProtectionImpactAssessment(
        dpia_id=uuid4(),
        activity_id=ACTIVITY_ID,
        organization_id=ORG,
        status=status,
        risk_class=ProcessingRiskClass.HIGH,
        reviewer_party_reference=REVIEWER,
        created_at=T0,
        updated_at=T0,
        approval_reference="approval:1" if status is DPIAStatus.APPROVED else None,
        approved_at=T0 if status is DPIAStatus.APPROVED else None,
        valid_until=valid_until,
    )


def _record_class(**overrides: object) -> RecordClass:
    base = {
        "record_class_id": uuid4(),
        "organization_id": ORG,
        "record_class_code": "case.arbitration.file",
        "record_category": "procedural_case_file",
        "sensitivity": RecordSensitivity.CONFIDENTIAL,
        "data_classification": DataClassification.CONFIDENTIAL,
        "record_owner_authority_reference": OWNER,
        "custodian_reference": CUSTODIAN,
        "disposition_authority_reference": DISPOSITION_AUTHORITY,
        "retention_policy_reference": uuid4(),
        "search_export_eligibility": SearchExportEligibility.SCOPED_SEARCH_GOVERNED_EXPORT,
        "legal_hold_applicable": True,
        "valid_from": T0,
    }
    base.update(overrides)
    return RecordClass(**base)  # type: ignore[arg-type]


def _propagation(
    *, state: PropagationState = PropagationState.CONFIRMED, hold_id: UUID | None = None
) -> HoldPropagationRecord:
    return HoldPropagationRecord(
        propagation_id=uuid4(),
        hold_id=hold_id or HOLD_ID,
        organization_id=ORG,
        derivative_kind=DerivativeKind.SEARCH_INDEX,
        derivative_reference="index:cases",
        state=state,
        recorded_at=T0,
        evidence_reference=(
            "propagation-evidence:1" if state is PropagationState.CONFIRMED else ""
        ),
        failure_reason_code=(
            "LEGAL_HOLD_PROPAGATION_UNRESOLVED" if state is PropagationState.FAILED else None
        ),
    )


# ===========================================================================
# The DPIA gate
# ===========================================================================


def test_the_gate_fails_closed_when_nobody_ever_evaluated_the_requirement() -> None:
    """The most important test in this file. An activity with NO
    requirement determination is not an activity that passed - it is one
    nobody assessed, and it must not activate."""
    with pytest.raises(DPIARequiredError) as excinfo:
        assert_activation_permitted(
            risk_class=ProcessingRiskClass.HIGH, requirement=None, dpia=None, at=T0
        )
    assert excinfo.value.reason_code == "DPIA_REQUIRED"


def test_the_gate_fails_closed_even_for_a_low_risk_activity_never_assessed() -> None:
    """Low risk does not mean 'skip the question'. 'We asked and the
    answer was no' and 'nobody asked' are different states."""
    with pytest.raises(DPIARequiredError):
        assert_activation_permitted(
            risk_class=ProcessingRiskClass.LOW, requirement=None, dpia=None, at=T0
        )


def test_a_recorded_not_required_determination_permits_activation() -> None:
    assert_activation_permitted(
        risk_class=ProcessingRiskClass.LOW,
        requirement=_requirement(required=False),
        dpia=None,
        at=T0,
    )


def test_a_required_dpia_that_does_not_exist_blocks_activation() -> None:
    with pytest.raises(DPIARequiredError):
        assert_activation_permitted(
            risk_class=ProcessingRiskClass.HIGH,
            requirement=_requirement(required=True),
            dpia=None,
            at=T0,
        )


def test_a_dpia_that_is_not_approved_blocks_activation() -> None:
    for status in (DPIAStatus.DRAFT, DPIAStatus.UNDER_REVIEW, DPIAStatus.EXPIRED):
        with pytest.raises(DPIANotApprovedError) as excinfo:
            assert_activation_permitted(
                risk_class=ProcessingRiskClass.HIGH,
                requirement=_requirement(),
                dpia=_dpia(status=status),
                at=T0,
            )
        assert excinfo.value.reason_code == "DPIA_NOT_APPROVED"


def test_an_approved_dpia_past_its_validity_activates_nothing() -> None:
    """'Expired' is the practical meaning of an approval past its
    `valid_until`, even before anybody transitions the record."""
    dpia = _dpia(valid_until=T1)
    assert dpia.status is DPIAStatus.APPROVED
    assert dpia.is_activating_at(T0) is True
    assert dpia.is_activating_at(T2) is False
    with pytest.raises(DPIANotApprovedError):
        assert_activation_permitted(
            risk_class=ProcessingRiskClass.HIGH,
            requirement=_requirement(),
            dpia=dpia,
            at=T2,
        )


def test_the_high_risk_classes_are_named_rather_than_inferred() -> None:
    assert {
        ProcessingRiskClass.HIGH,
        ProcessingRiskClass.SPECIAL_CATEGORY,
    } == DPIA_REQUIRING_RISK_CLASSES


def test_the_full_gate_passes_only_when_every_step_is_satisfied() -> None:
    assert_activation_permitted(
        risk_class=ProcessingRiskClass.HIGH,
        requirement=_requirement(),
        dpia=_dpia(),
        at=T0,
    )


# ===========================================================================
# Reviewer independence
# ===========================================================================


def test_the_reviewer_may_not_be_the_controller_or_the_process_owner() -> None:
    """An assessment signed off by the party that wants the processing is
    not a review."""
    assert_dpo_independence(
        reviewer_party_reference=REVIEWER,
        controller_reference=CONTROLLER,
        process_owner_authority_reference=PROCESS_OWNER,
    )
    with pytest.raises(DPOIndependenceRequiredError) as as_controller:
        assert_dpo_independence(
            reviewer_party_reference=CONTROLLER,
            controller_reference=CONTROLLER,
            process_owner_authority_reference=PROCESS_OWNER,
        )
    assert as_controller.value.reason_code == "DPO_INDEPENDENCE_REQUIRED"
    with pytest.raises(DPOIndependenceRequiredError):
        assert_dpo_independence(
            reviewer_party_reference=PROCESS_OWNER,
            controller_reference=CONTROLLER,
            process_owner_authority_reference=PROCESS_OWNER,
        )


# ===========================================================================
# DPIA lifecycle
# ===========================================================================


def test_the_dpia_transition_table_is_closed_and_versions_the_record() -> None:
    draft = _dpia(status=DPIAStatus.DRAFT)
    with pytest.raises(DPIANotApprovedError):
        draft.with_status(DPIAStatus.APPROVED, T1)

    reviewed = draft.with_status(DPIAStatus.UNDER_REVIEW, T1)
    approved = reviewed.with_status(
        DPIAStatus.APPROVED, T1, approval_reference="approval:1", valid_until=T2
    )
    assert approved.approved_at == T1
    assert approved.approval_reference == "approval:1"
    assert approved.dpia_version == draft.dpia_version + 2


def test_an_approved_dpia_records_its_approval_reference() -> None:
    with pytest.raises(ValueError, match="approval artefact"):
        _dpia(status=DPIAStatus.APPROVED).__class__(
            dpia_id=uuid4(),
            activity_id=ACTIVITY_ID,
            organization_id=ORG,
            status=DPIAStatus.APPROVED,
            risk_class=ProcessingRiskClass.HIGH,
            reviewer_party_reference=REVIEWER,
            created_at=T0,
            updated_at=T0,
            approval_reference=None,
            approved_at=T0,
        )


# ===========================================================================
# Activation decisions
# ===========================================================================


def test_an_activation_decision_records_its_reason_whether_it_activates_or_not() -> None:
    for state in ProcessingActivationState:
        decision = ProcessingActivationDecision(
            activation_decision_id=uuid4(),
            activity_id=ACTIVITY_ID,
            organization_id=ORG,
            state=state,
            decided_at=T0,
            decided_by_authority_reference=CONTROLLER,
            reason_code="COMPLIANCE_PROCESSING_ACTIVATION_DECIDED",
            effective_from=T0 if state is ProcessingActivationState.ACTIVATED else None,
        )
        assert decision.reason_code


def test_an_activation_decision_requires_a_reason_code() -> None:
    with pytest.raises(ValueError, match="reason"):
        ProcessingActivationDecision(
            activation_decision_id=uuid4(),
            activity_id=ACTIVITY_ID,
            organization_id=ORG,
            state=ProcessingActivationState.ACTIVATED,
            decided_at=T0,
            decided_by_authority_reference=CONTROLLER,
            reason_code="",
            effective_from=T0,
        )


# ===========================================================================
# Consent withdrawal and transfers
# ===========================================================================


def test_withdrawing_consent_does_not_by_itself_delete_anything() -> None:
    """Conflating withdrawal with deletion would let a withdrawal destroy
    evidence a statutory retention duty or an active hold still
    requires."""
    record = ConsentWithdrawalRecord(
        withdrawal_id=uuid4(),
        activity_id=ACTIVITY_ID,
        organization_id=ORG,
        withdrawn_at=T0,
        subject_party_reference=uuid4(),
        affects_records_of_class="case.arbitration.file",
    )
    assert record.retention_obligation_persists is True
    assert not hasattr(record, "deletes_records")


def test_a_transfer_assessment_records_its_mechanism_by_name() -> None:
    assessment = TransferAssessment(
        assessment_id=uuid4(),
        activity_id=ACTIVITY_ID,
        organization_id=ORG,
        mechanism=TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES,
        recipient_category="processor.hosting",
        assessed_at=T0,
        assessed_by_party_reference=REVIEWER,
    )
    assert assessment.mechanism in set(TransferMechanism)


# ===========================================================================
# Records classification (Framework section 11)
# ===========================================================================


def test_the_record_owner_may_not_also_be_the_disposition_authority() -> None:
    """Separating who owns a record from who may authorize destroying it
    is the whole point of the class."""
    with pytest.raises(ProceduralRoleConflictError, match="self-certification"):
        _record_class(disposition_authority_reference=OWNER)


def test_a_record_class_states_its_search_and_export_eligibility_explicitly() -> None:
    """A downstream pack must be able to tell whether it may index or
    export a class at all - and `no_index` has to be expressible."""
    restricted = _record_class(
        search_export_eligibility=SearchExportEligibility.NO_INDEX,
        data_classification=DataClassification.PERSONAL_COMMUNICATION,
    )
    assert restricted.search_export_eligibility is SearchExportEligibility.NO_INDEX


def test_a_record_class_is_versioned_rather_than_rewritten() -> None:
    original = _record_class()
    superseded = replace(
        original,
        valid_until=T1,
        record_class_version=original.record_class_version + 1,
    )
    assert superseded.record_class_version == 2
    assert original.valid_until is None


# ===========================================================================
# Legal Hold propagation (Framework section 11)
# ===========================================================================


def test_an_unresolved_derivative_blocks_destruction() -> None:
    """A hold that has not reached a replica, index, export or backup is
    not an effective hold."""
    for state in (PropagationState.UNKNOWN, PropagationState.PENDING, PropagationState.FAILED):
        with pytest.raises(LegalHoldPropagationUnresolvedError) as excinfo:
            assert_hold_propagation_resolved((_propagation(state=state),), hold_id=HOLD_ID)
        assert excinfo.value.reason_code == "LEGAL_HOLD_PROPAGATION_UNRESOLVED"


def test_confirmed_and_not_applicable_are_both_resolved() -> None:
    for state in (PropagationState.CONFIRMED, PropagationState.NOT_APPLICABLE):
        assert _propagation(state=state).is_resolved is True
        assert_hold_propagation_resolved((_propagation(state=state),), hold_id=HOLD_ID)


def test_an_empty_propagation_set_is_treated_as_resolved_and_this_is_deliberate() -> None:
    """The asymmetry is intentional and is documented rather than hidden:
    PACK-09 can only reason about derivatives it has been told about. It
    refuses on the ones it has; it cannot refuse on ones nobody
    registered. The honest consequence is that propagation completeness is
    a deployment responsibility, not something this service can
    guarantee."""
    assert_hold_propagation_resolved((), hold_id=HOLD_ID)


def test_a_propagation_record_for_another_hold_does_not_block_this_one() -> None:
    other = _propagation(state=PropagationState.FAILED, hold_id=uuid4())
    assert_hold_propagation_resolved((other,), hold_id=HOLD_ID)


def test_a_failed_propagation_must_carry_a_reason_code() -> None:
    with pytest.raises(ValueError, match="reason"):
        HoldPropagationRecord(
            propagation_id=uuid4(),
            hold_id=HOLD_ID,
            organization_id=ORG,
            derivative_kind=DerivativeKind.EXPORT_DATASET,
            derivative_reference="export:1",
            state=PropagationState.FAILED,
            recorded_at=T0,
            failure_reason_code=None,
        )


def test_every_derivative_kind_the_framework_names_is_expressible() -> None:
    assert {kind.value for kind in DerivativeKind} == {
        "replica",
        "search_index",
        "export_dataset",
        "backup_set",
        "cached_rendition",
    }

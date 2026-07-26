"""Domain tests for the legal-case substrate (Architecture & Domain
Framework 0.8.1 section 13.1), organised by the mandatory test matrix in
that document's section 13.4.

These are pure-domain tests: no stores, no clock injection, no
application layer. Each one asserts that a Framework hard invariant is
*structural* - that the failure mode is inexpressible or refused by
construction - rather than merely conventional. Where an invariant is
enforced by `__post_init__`, the test constructs the forbidden object and
asserts the refusal, because a guard that only exists in a command can be
bypassed by the next command somebody writes.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_compliance_service.casework import (
    SUBSTANTIVE_CASE_STATUSES,
    ActorClass,
    AttendanceState,
    CaseAccessProfile,
    CaseKind,
    CaseParty,
    CaseTransitionEntry,
    ConfidentialityClass,
    ConflictAssessmentOutcome,
    DecisionStateEntry,
    DecisionType,
    EffectStatus,
    EnforceabilityStatus,
    Filing,
    FilingIntakeState,
    FilingType,
    FinalityStatus,
    Hearing,
    HearingAttendance,
    HearingHistoryEntry,
    HearingStatus,
    InterimMeasure,
    InterimMeasureStatus,
    JurisdictionDetermination,
    JurisdictionStatus,
    JurisdictionType,
    LegalCase,
    LegalCaseStatus,
    OperativeResult,
    PartyRole,
    ProceduralDecision,
    RecusalRecord,
    Remedy,
    RemedyKind,
    RemedyStatus,
    ReplacementAssignment,
    RepresentationAuthority,
    RepresentationMandate,
    RepresentationStatus,
    assert_actor_not_recused,
    assert_due_process_complete,
    assert_may_decide_substantively,
    mint_case_party_reference,
)
from epd2_compliance_service.exceptions import (
    DecisionNotEnforceableError,
    DueProcessPrerequisiteMissingError,
    FilingSequenceConflictError,
    InterimMeasureAuthorityDeniedError,
    JurisdictionMissingError,
    JurisdictionNotCompetentError,
    JurisdictionScopeMismatchError,
    ProceduralCaseTransitionInvalidError,
    RecusedActorDeniedError,
    RemedyUnavailableError,
    RepresentationExpiredError,
    RepresentationInvalidError,
    RepresentationRevokedError,
)

T0 = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
T1 = T0 + timedelta(days=7)
T2 = T0 + timedelta(days=30)
BERLIN = "Europe/Berlin"
REASON = "COMPLIANCE_LEGAL_CASE_STATUS_CHANGED"

ORG = uuid4()
CASE_ID = uuid4()
AUTHORITY = mint_case_party_reference()
OTHER_AUTHORITY = mint_case_party_reference()
APPLICANT = mint_case_party_reference()
REPRESENTATIVE = mint_case_party_reference()


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _jurisdiction(
    *,
    status: JurisdictionStatus = JurisdictionStatus.CONFIRMED,
    valid_until: datetime | None = None,
    case_id: UUID | None = None,
    organization_id: UUID | None = None,
) -> JurisdictionDetermination:
    return JurisdictionDetermination(
        jurisdiction_id=uuid4(),
        case_id=case_id or CASE_ID,
        organization_id=organization_id or ORG,
        jurisdiction_type=JurisdictionType.PARTY_STATUTE,
        case_kind=CaseKind.ARBITRATION,
        competent_authority_reference=AUTHORITY,
        status=status,
        determined_at=T0,
        determined_by_authority_reference=AUTHORITY,
        valid_from=T0,
        valid_until=valid_until,
        basis_reference="statute:s.14",
    )


def _case(
    *,
    path: tuple[LegalCaseStatus, ...] = (LegalCaseStatus.INTAKE,),
    jurisdiction_id: UUID | None = None,
) -> LegalCase:
    history = tuple(
        CaseTransitionEntry(
            sequence=index + 1,
            status_after=status,
            occurred_at=T0 + timedelta(hours=index),
            reason_code=REASON,
            actor_authority_reference=AUTHORITY,
        )
        for index, status in enumerate(path)
    )
    return LegalCase(
        legal_case_id=CASE_ID,
        organization_id=ORG,
        case_kind=CaseKind.ARBITRATION,
        opened_at=T0,
        subject_reference="dispute:1",
        confidentiality_class=ConfidentialityClass.CONFIDENTIAL,
        access_profile=CaseAccessProfile.NAMED_PARTIES_ONLY,
        transition_history=history,
        governing_policy_reference="policy:arbitration:v1",
        jurisdiction_id=jurisdiction_id,
        case_version=len(history),
    )


def _filing(**overrides: object) -> Filing:
    base = {
        "filing_id": uuid4(),
        "case_id": CASE_ID,
        "organization_id": ORG,
        "docket_sequence": 1,
        "filing_type": FilingType.INITIATING_SUBMISSION,
        "filed_by_party_reference": APPLICANT,
        "submitted_at": T0,
        "received_at": T0 + timedelta(hours=1),
        "intake_state": FilingIntakeState.RECEIVED,
    }
    base.update(overrides)
    return Filing(**base)  # type: ignore[arg-type]


def _hearing() -> Hearing:
    return Hearing(
        hearing_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        convening_authority_reference=AUTHORITY,
        agenda_code="hearing.substantive",
        scheduled_at=T1,
        timezone=BERLIN,
        history=(
            HearingHistoryEntry(
                sequence=1,
                status_after=HearingStatus.SCHEDULED,
                occurred_at=T0,
                scheduled_at_before=T1,
                scheduled_at_after=T1,
                reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
                actor_authority_reference=AUTHORITY,
            ),
        ),
    )


def _decision(**overrides: object) -> ProceduralDecision:
    base = {
        "decision_id": uuid4(),
        "case_id": CASE_ID,
        "organization_id": ORG,
        "decision_type": DecisionType.SUBSTANTIVE,
        "deciding_authority_reference": AUTHORITY,
        "decided_by_party_reference": AUTHORITY,
        "operative_result": OperativeResult.UPHELD,
        "issued_at": T0,
        "state_history": (
            DecisionStateEntry(
                sequence=1,
                occurred_at=T0,
                effect_status=EffectStatus.PENDING,
                finality_status=FinalityStatus.OPEN_TO_REMEDY,
                enforceability_status=EnforceabilityStatus.NOT_ENFORCEABLE,
                reason_code="COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
                actor_authority_reference=AUTHORITY,
            ),
        ),
        "reason_code": "COMPLIANCE_PROCEDURAL_DECISION_STATE_CHANGED",
        "reasons_reference": "reasons:1",
    }
    base.update(overrides)
    return ProceduralDecision(**base)  # type: ignore[arg-type]


def _interim(**overrides: object) -> InterimMeasure:
    base = {
        "measure_id": uuid4(),
        "case_id": CASE_ID,
        "organization_id": ORG,
        "measure_kind": "suspension",
        "requested_by_party_reference": APPLICANT,
        "decided_by_authority_reference": AUTHORITY,
        "decided_by_actor_class": ActorClass.HUMAN_AUTHORITY,
        "legal_basis_reference": "statute:s.22",
        "scope_description_code": "measure.scope.suspension",
        "status": InterimMeasureStatus.GRANTED,
        "decided_at": T0,
        "starts_at": T0,
        "ends_at": T2,
        "reasons_reference": "reasons:interim",
    }
    base.update(overrides)
    return InterimMeasure(**base)  # type: ignore[arg-type]


def _recusal(
    *, outcome: ConflictAssessmentOutcome = ConflictAssessmentOutcome.RECUSAL_REQUIRED
) -> RecusalRecord:
    return RecusalRecord(
        recusal_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        party_reference=AUTHORITY,
        conflict_declaration_id=uuid4(),
        assessment_outcome=outcome,
        effective_at=T1,
        reviewed_by_party_reference=OTHER_AUTHORITY,
        prior_participation_codes=("filing.admissibility_decided", "hearing.scheduled"),
    )


# ===========================================================================
# 1. Jurisdiction (Framework hard invariant 52)
# ===========================================================================


def test_a_case_without_jurisdiction_cannot_enter_a_substantive_status() -> None:
    """The gate is on the *aggregate*, not on a command: a case with no
    jurisdiction determination refuses the transition itself, so no
    command can route around it."""
    case = _case(
        path=(
            LegalCaseStatus.INTAKE,
            LegalCaseStatus.JURISDICTION_REVIEW,
            LegalCaseStatus.ADMISSIBILITY_REVIEW,
        )
    )
    with pytest.raises(JurisdictionMissingError) as excinfo:
        case.transition(
            LegalCaseStatus.SUBSTANTIVE_REVIEW,
            T1,
            reason_code=REASON,
            actor_authority_reference=AUTHORITY,
        )
    assert excinfo.value.reason_code == "JURISDICTION_MISSING"


def test_every_substantive_status_is_covered_by_the_jurisdiction_gate() -> None:
    """The gate list and the statuses that mean 'deciding on the merits'
    must not drift apart. Stated as a test so adding a ninth status forces
    a decision about it rather than silently escaping the gate."""
    assert {
        LegalCaseStatus.SUBSTANTIVE_REVIEW,
        LegalCaseStatus.HEARING,
        LegalCaseStatus.DECIDED,
    } == SUBSTANTIVE_CASE_STATUSES


def test_a_challenged_jurisdiction_stops_permitting_substantive_decisions() -> None:
    """A contested competence must not keep producing binding outcomes
    while the challenge is pending."""
    determination = _jurisdiction()
    assert determination.permits_substantive_decision_at(T1) is True

    challenged = determination.challenge(T1, reason_code="JURISDICTION_NOT_COMPETENT")
    assert challenged.status is JurisdictionStatus.CHALLENGED
    assert challenged.permits_substantive_decision_at(T1) is False


def test_a_transfer_preserves_the_outgoing_determination_rather_than_rewriting_it() -> None:
    """Framework 13.1, 'preserved jurisdiction history': acts performed
    while an authority was competent must stay attributable to it after
    any number of transfers."""
    outgoing = _jurisdiction()
    successor_id = uuid4()
    transferred = outgoing.transfer_to(
        successor_id, at=T1, reason_code="JURISDICTION_TRANSFER_REQUIRED"
    )

    assert transferred.status is JurisdictionStatus.TRANSFERRED
    assert transferred.valid_until == T1
    assert transferred.transferred_to_jurisdiction_id == successor_id
    # The outgoing determination still names its OWN authority - it was not
    # rewritten to describe the successor.
    assert transferred.competent_authority_reference == outgoing.competent_authority_reference
    assert transferred.determined_by_authority_reference == (
        outgoing.determined_by_authority_reference
    )
    # And it still permits nothing going forward.
    assert transferred.permits_substantive_decision_at(T2) is False


def test_a_transferred_determination_cannot_be_challenged_afterwards() -> None:
    transferred = _jurisdiction().transfer_to(uuid4(), at=T1, reason_code="X")
    with pytest.raises(JurisdictionNotCompetentError):
        transferred.challenge(T2, reason_code="Y")


def test_a_determination_outside_its_validity_window_permits_nothing() -> None:
    expired = _jurisdiction(valid_until=T1)
    assert expired.permits_substantive_decision_at(T0) is True
    assert expired.permits_substantive_decision_at(T2) is False


def test_binding_a_foreign_determination_to_a_case_is_refused() -> None:
    case = _case()
    with pytest.raises(JurisdictionScopeMismatchError):
        case.with_jurisdiction(_jurisdiction(case_id=uuid4()))
    with pytest.raises(JurisdictionScopeMismatchError):
        case.with_jurisdiction(_jurisdiction(organization_id=uuid4()))


def test_assert_may_decide_substantively_refuses_each_way_it_can_fail() -> None:
    determination = _jurisdiction()
    open_case = _case(jurisdiction_id=determination.jurisdiction_id)

    # No determination at all.
    with pytest.raises(JurisdictionMissingError):
        assert_may_decide_substantively(
            case=open_case,
            jurisdiction=None,
            acting_authority_reference=AUTHORITY,
            at=T1,
        )
    # A determination for another case.
    with pytest.raises(JurisdictionScopeMismatchError):
        assert_may_decide_substantively(
            case=open_case,
            jurisdiction=_jurisdiction(case_id=uuid4()),
            acting_authority_reference=AUTHORITY,
            at=T1,
        )
    # A challenged determination.
    with pytest.raises(JurisdictionNotCompetentError):
        assert_may_decide_substantively(
            case=open_case,
            jurisdiction=determination.challenge(T0, reason_code="X"),
            acting_authority_reference=AUTHORITY,
            at=T1,
        )
    # The happy path stays happy.
    assert_may_decide_substantively(
        case=open_case,
        jurisdiction=determination,
        acting_authority_reference=AUTHORITY,
        at=T1,
    )


# ===========================================================================
# 2. Parties and representation (Framework hard invariant 15)
# ===========================================================================


def test_a_party_reference_is_a_per_case_handle_and_never_reused() -> None:
    """Framework hard invariant 1: no global user ID. Two cases involving
    the same real person carry two unrelated handles, and there is no
    derivation or lookup that turns one into the other."""
    minted = {mint_case_party_reference() for _ in range(512)}
    assert len(minted) == 512


def test_a_mandate_grants_enumerated_authorities_not_a_role() -> None:
    mandate = RepresentationMandate(
        mandate_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        represented_party_reference=APPLICANT,
        representative_reference=REPRESENTATIVE,
        authorities=frozenset({RepresentationAuthority.FILE_SUBMISSIONS}),
        valid_from=T0,
    )
    mandate.assert_permits(RepresentationAuthority.FILE_SUBMISSIONS, at=T1)
    with pytest.raises(RepresentationInvalidError) as excinfo:
        mandate.assert_permits(RepresentationAuthority.WITHDRAW_CASE, at=T1)
    assert excinfo.value.reason_code == "REPRESENTATION_INVALID"


def test_an_expired_mandate_and_a_revoked_mandate_refuse_with_distinct_codes() -> None:
    """Three different failures, three different codes: a party told
    'invalid' when the real problem is 'expired' cannot correct it."""
    mandate = RepresentationMandate(
        mandate_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        represented_party_reference=APPLICANT,
        representative_reference=REPRESENTATIVE,
        authorities=frozenset({RepresentationAuthority.FILE_SUBMISSIONS}),
        valid_from=T0,
        valid_until=T1,
    )
    with pytest.raises(RepresentationExpiredError) as expired:
        mandate.assert_permits(RepresentationAuthority.FILE_SUBMISSIONS, at=T2)
    assert expired.value.reason_code == "REPRESENTATION_EXPIRED"

    revoked = mandate.revoke(T0 + timedelta(hours=1), reason_code="REPRESENTATION_REVOKED")
    assert revoked.status is RepresentationStatus.REVOKED
    with pytest.raises(RepresentationRevokedError) as revoked_error:
        revoked.assert_permits(RepresentationAuthority.FILE_SUBMISSIONS, at=T1)
    assert revoked_error.value.reason_code == "REPRESENTATION_REVOKED"


def test_revocation_does_not_rewrite_the_mandate_history() -> None:
    """Revocation is forward-looking. The mandate keeps its original
    validity window, so 'was this representative authorized on the day
    they filed?' stays answerable."""
    mandate = RepresentationMandate(
        mandate_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        represented_party_reference=APPLICANT,
        representative_reference=REPRESENTATIVE,
        authorities=frozenset({RepresentationAuthority.RECEIVE_SERVICE}),
        valid_from=T0,
    )
    revoked = mandate.revoke(T1, reason_code="REPRESENTATION_REVOKED")
    assert revoked.valid_from == mandate.valid_from
    assert revoked.revoked_at == T1
    assert revoked.authorities == mandate.authorities


def test_a_case_party_records_service_authorization_explicitly() -> None:
    party = CaseParty(
        case_party_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        party_reference=APPLICANT,
        role=PartyRole.RESPONDENT,
        registered_at=T0,
    )
    assert party.is_authorized_service_recipient is False


# ===========================================================================
# 3. Filings and the immutable docket
# ===========================================================================


def test_a_rejected_filing_stays_on_the_docket_with_its_reason() -> None:
    """'This was filed and refused' is itself a fact the record has to
    preserve, so rejection is a state, not a deletion."""
    rejected = _filing().reject(reason_code="FILING_INADMISSIBLE")
    assert rejected.intake_state is FilingIntakeState.REJECTED
    assert rejected.rejection_reason_code == "FILING_INADMISSIBLE"
    assert rejected.docket_sequence == 1


def test_a_rejected_filing_must_carry_a_reason_code() -> None:
    with pytest.raises(ValueError, match="rejection reason code"):
        _filing(intake_state=FilingIntakeState.REJECTED)


def test_only_a_received_filing_can_be_admitted_or_rejected() -> None:
    admitted = _filing().admit()
    with pytest.raises(FilingSequenceConflictError):
        admitted.admit()
    with pytest.raises(FilingSequenceConflictError):
        admitted.reject(reason_code="FILING_INADMISSIBLE")


def test_supersession_preserves_the_original_position_and_content() -> None:
    """Correction is supersession, not mutation."""
    original = _filing(docket_sequence=3)
    successor_id = uuid4()
    superseded = original.mark_superseded(successor_id)
    assert superseded.docket_sequence == 3
    assert superseded.submitted_at == original.submitted_at
    assert superseded.received_at == original.received_at
    assert superseded.superseded_by_filing_id == successor_id


def test_a_filing_cannot_supersede_itself() -> None:
    filing = _filing()
    with pytest.raises(FilingSequenceConflictError):
        filing.mark_superseded(filing.filing_id)
    with pytest.raises(FilingSequenceConflictError):
        _filing(supersedes_filing_id=filing.filing_id, filing_id=filing.filing_id)


def test_submitted_at_and_received_at_are_distinct_and_ordered() -> None:
    """A deadline running from receipt must not silently use the
    submitter's clock, so the two instants are separate fields and
    receipt may never precede submission."""
    filing = _filing()
    assert filing.received_at > filing.submitted_at
    with pytest.raises(ValueError, match="received_at must not precede"):
        _filing(submitted_at=T1, received_at=T0)


def test_a_docket_sequence_must_be_positive() -> None:
    with pytest.raises(FilingSequenceConflictError):
        _filing(docket_sequence=0)


# ===========================================================================
# 4. Hearings
# ===========================================================================


def test_hearing_status_is_derived_from_the_append_only_history() -> None:
    hearing = _hearing()
    assert hearing.status is HearingStatus.SCHEDULED

    rescheduled = hearing.reschedule(
        T0 + timedelta(days=1),
        new_scheduled_at=T2,
        reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
        actor_authority_reference=AUTHORITY,
    )
    assert rescheduled.status is HearingStatus.RESCHEDULED
    assert rescheduled.scheduled_at == T2
    assert len(rescheduled.history) == 2
    # The original entry is untouched.
    assert rescheduled.history[0] == hearing.history[0]
    assert rescheduled.history[1].scheduled_at_before == T1
    assert rescheduled.history[1].scheduled_at_after == T2


def test_rescheduling_a_hearing_changes_no_deadline() -> None:
    """Framework hard invariant 60: an infrastructure or scheduling event
    does not silently change a legal deadline. The hearing carries only a
    *reference* to its submissions deadline, and rescheduling does not
    touch it."""
    deadline_id = uuid4()
    hearing = replace(_hearing(), submissions_deadline_id=deadline_id)
    rescheduled = hearing.reschedule(
        T0 + timedelta(days=1),
        new_scheduled_at=T2,
        reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
        actor_authority_reference=AUTHORITY,
    )
    assert rescheduled.submissions_deadline_id == deadline_id


def test_a_completed_hearing_can_carry_a_minutes_reference_but_no_minutes() -> None:
    completed = _hearing().complete(
        T2,
        reason_code="COMPLIANCE_HEARING_STATUS_CHANGED",
        actor_authority_reference=AUTHORITY,
    )
    assert completed.status is HearingStatus.COMPLETED
    assert completed.minutes_reference is None
    assert not hasattr(completed, "minutes")


def test_attendance_is_recorded_per_party_without_naming_anybody() -> None:
    hearing = _hearing().with_attendance(
        HearingAttendance(party_reference=APPLICANT, state=AttendanceState.EXCUSED, recorded_at=T1)
    )
    assert hearing.attendance[0].state is AttendanceState.EXCUSED
    field_names = {field for field in dir(hearing.attendance[0]) if not field.startswith("_")}
    assert field_names == {"party_reference", "state", "recorded_at"}


# ===========================================================================
# 5. Interim measures (Framework hard invariant 69)
# ===========================================================================


def test_a_granted_interim_measure_requires_a_human_deciding_authority() -> None:
    """AI decides no consequential legal outcomes. Enforced in
    `__post_init__`, so the object cannot exist - not merely be
    refused by one command."""
    for actor_class in (ActorClass.SERVICE, ActorClass.AUTOMATED):
        with pytest.raises(InterimMeasureAuthorityDeniedError) as excinfo:
            _interim(decided_by_actor_class=actor_class)
        assert excinfo.value.reason_code == "INTERIM_MEASURE_AUTHORITY_DENIED"


def test_a_human_case_handler_cannot_grant_an_interim_measure_either() -> None:
    """`human_case_handler` is a human, but not the deciding authority.
    The distinction matters: 'a person did it' is not the same as 'the
    competent authority decided it'."""
    with pytest.raises(InterimMeasureAuthorityDeniedError):
        _interim(decided_by_actor_class=ActorClass.HUMAN_CASE_HANDLER)


def test_an_indefinite_or_unreasoned_interim_measure_is_not_expressible() -> None:
    """Both refusals are reason-coded, not bare `ValueError`s: an
    indefinite or unreasoned measure is a governance refusal a party can
    be told about and can appeal, not a programming mistake."""
    with pytest.raises(InterimMeasureAuthorityDeniedError) as indefinite:
        _interim(ends_at=None, review_due_at=None)
    assert indefinite.value.reason_code == "INTERIM_MEASURE_AUTHORITY_DENIED"

    with pytest.raises(DueProcessPrerequisiteMissingError) as unreasoned:
        _interim(reasons_reference="")
    assert unreasoned.value.reason_code == "DUE_PROCESS_PREREQUISITE_MISSING"


def test_a_refused_interim_measure_may_be_recorded_by_any_actor_class() -> None:
    """The human-authority requirement is on *granting*. Recording that a
    measure was requested or refused is not a consequential legal
    outcome."""
    refused = _interim(
        status=InterimMeasureStatus.REFUSED,
        decided_by_actor_class=ActorClass.HUMAN_CASE_HANDLER,
        ends_at=None,
        review_due_at=None,
        reasons_reference="",
    )
    assert refused.status is InterimMeasureStatus.REFUSED
    assert refused.is_in_force_at(T1) is False


def test_a_granted_measure_is_in_force_only_inside_its_window() -> None:
    measure = _interim(starts_at=T1, ends_at=T2)
    assert measure.is_in_force_at(T0) is False
    assert measure.is_in_force_at(T1) is True
    assert measure.is_in_force_at(T2) is False


# ===========================================================================
# 6. Procedural decisions: three separate facts
# ===========================================================================


def test_effect_finality_and_enforceability_are_independent() -> None:
    decision = _decision()
    assert decision.effect_status is EffectStatus.PENDING
    assert decision.finality_status is FinalityStatus.OPEN_TO_REMEDY
    assert decision.enforceability_status is EnforceabilityStatus.NOT_ENFORCEABLE

    in_effect = decision.commence_effect(T1, reason_code="R", actor_authority_reference=AUTHORITY)
    assert in_effect.effect_status is EffectStatus.IN_EFFECT
    # Commencing effect changed NEITHER of the other two.
    assert in_effect.finality_status is FinalityStatus.OPEN_TO_REMEDY
    assert in_effect.enforceability_status is EnforceabilityStatus.NOT_ENFORCEABLE

    final = in_effect.become_final(T2, reason_code="R", actor_authority_reference=AUTHORITY)
    assert final.finality_status is FinalityStatus.FINAL
    # Becoming final did not make it enforceable.
    assert final.enforceability_status is EnforceabilityStatus.NOT_ENFORCEABLE


def test_a_decision_cannot_become_enforceable_while_its_effect_is_not_in_effect() -> None:
    with pytest.raises(DecisionNotEnforceableError) as excinfo:
        _decision().become_enforceable(T1, reason_code="R", actor_authority_reference=AUTHORITY)
    assert excinfo.value.reason_code == "DECISION_NOT_ENFORCEABLE"


def test_suspending_effect_also_stays_enforceability() -> None:
    """A suspended decision that stayed enforceable is exactly the failure
    Framework hard invariant 52 exists to prevent, so the coupling lives
    in the aggregate and no caller can suspend one without the other."""
    enforceable = (
        _decision()
        .commence_effect(T1, reason_code="R", actor_authority_reference=AUTHORITY)
        .become_enforceable(T1, reason_code="R", actor_authority_reference=AUTHORITY)
    )
    assert enforceable.enforceability_status is EnforceabilityStatus.ENFORCEABLE

    suspended = enforceable.suspend_effect(T2, reason_code="R", actor_authority_reference=AUTHORITY)
    assert suspended.effect_status is EffectStatus.SUSPENDED
    assert suspended.enforceability_status is EnforceabilityStatus.STAYED


def test_the_state_history_is_append_only_and_fully_reconstructible() -> None:
    decision = _decision().commence_effect(
        T1, reason_code="R1", actor_authority_reference=AUTHORITY
    )
    later = decision.become_final(T2, reason_code="R2", actor_authority_reference=AUTHORITY)
    assert [entry.sequence for entry in later.state_history] == [1, 2, 3]
    assert later.state_history[0].effect_status is EffectStatus.PENDING
    assert later.state_history[1].reason_code == "R1"
    assert later.state_history[2].reason_code == "R2"


def test_an_appeal_points_at_a_different_case() -> None:
    decision = _decision()
    with pytest.raises(ValueError, match="different case"):
        decision.with_appeal(decision.case_id)


# ===========================================================================
# 7. Remedies and due process (Framework hard invariant 52)
# ===========================================================================


def _remedy(**overrides: object) -> Remedy:
    base = {
        "remedy_id": uuid4(),
        "case_id": CASE_ID,
        "organization_id": ORG,
        "decision_id": uuid4(),
        "remedy_kind": RemedyKind.APPEAL,
        "status": RemedyStatus.AVAILABLE,
        "available_from": T0,
        "available_until": T2,
        "competent_authority_reference": AUTHORITY,
    }
    base.update(overrides)
    return Remedy(**base)  # type: ignore[arg-type]


def test_a_remedy_outside_its_window_is_refused_with_its_own_code() -> None:
    remedy = _remedy(available_from=T1, available_until=T2)
    with pytest.raises(RemedyUnavailableError) as early:
        remedy.assert_available_at(T0)
    assert early.value.reason_code == "REMEDY_UNAVAILABLE"
    with pytest.raises(RemedyUnavailableError):
        remedy.assert_available_at(T2 + timedelta(days=1))
    remedy.assert_available_at(T1)


def test_exercising_a_remedy_records_the_resulting_case() -> None:
    resulting = uuid4()
    exercised = _remedy().exercise(T1, resulting_case_id=resulting)
    assert exercised.status is RemedyStatus.EXERCISED
    assert exercised.exercised_at == T1
    assert exercised.resulting_case_id == resulting


def test_due_process_names_the_specific_missing_prerequisite() -> None:
    """Six prerequisites, six distinct messages. A refusal that said only
    'due process incomplete' would be unactionable for the party told to
    fix it."""
    complete = {
        "jurisdiction_confirmed": True,
        "notice_effect_established": True,
        "response_opportunity_given": True,
        "decided_by_actor_class": ActorClass.HUMAN_AUTHORITY,
        "reasons_reference": "reasons:1",
        "remedy_available": True,
    }
    assert_due_process_complete(**complete)  # type: ignore[arg-type]

    for key, broken, expected_fragment in (
        ("jurisdiction_confirmed", False, "jurisdiction"),
        ("notice_effect_established", False, "notice"),
        ("response_opportunity_given", False, "opportunity to respond"),
        ("decided_by_actor_class", ActorClass.AUTOMATED, "human decision"),
        ("reasons_reference", "", "reasons"),
        ("remedy_available", False, "remedy"),
    ):
        arguments = dict(complete)
        arguments[key] = broken
        with pytest.raises(DueProcessPrerequisiteMissingError) as excinfo:
            assert_due_process_complete(**arguments)  # type: ignore[arg-type]
        assert excinfo.value.reason_code == "DUE_PROCESS_PREREQUISITE_MISSING"
        # The message names the ONE prerequisite that is missing, so a
        # party told to fix it knows what to fix.
        message = str(excinfo.value)
        missing = message.split("missing: ", 1)[1]
        assert expected_fragment in missing


def test_an_ai_actor_can_never_satisfy_the_due_process_gate() -> None:
    """Framework hard invariant 69, stated once more at the gate that
    matters: whatever else is in place, an automated decider fails."""
    for actor_class in (ActorClass.AUTOMATED, ActorClass.SERVICE):
        with pytest.raises(DueProcessPrerequisiteMissingError):
            assert_due_process_complete(
                jurisdiction_confirmed=True,
                notice_effect_established=True,
                response_opportunity_given=True,
                decided_by_actor_class=actor_class,
                reasons_reference="reasons:1",
                remedy_available=True,
            )


# ===========================================================================
# 8. Recusal (Framework hard invariants 53 and 54)
# ===========================================================================


def test_a_blocking_recusal_denies_the_actor_from_its_effective_date() -> None:
    recusals = (_recusal(),)
    # Before the effective date the actor was competent, and that stays true.
    assert_actor_not_recused(actor_party_reference=AUTHORITY, recusals=recusals, at=T0)
    with pytest.raises(RecusedActorDeniedError) as excinfo:
        assert_actor_not_recused(actor_party_reference=AUTHORITY, recusals=recusals, at=T2)
    assert excinfo.value.reason_code == "RECUSED_ACTOR_DENIED"


def test_recusal_blocks_capability_without_erasing_prior_participation() -> None:
    """Framework hard invariant 53. The record of what the recused actor
    already did survives - it has to, because those acts may themselves be
    the subject of the appeal."""
    recusal = _recusal()
    assert recusal.blocks_decision_capability is True
    assert recusal.prior_participation_codes == (
        "filing.admissibility_decided",
        "hearing.scheduled",
    )


def test_a_non_blocking_assessment_outcome_denies_nobody() -> None:
    for outcome in (
        ConflictAssessmentOutcome.NO_CONFLICT,
        ConflictAssessmentOutcome.CONFLICT_MITIGATED,
    ):
        recusal = _recusal(outcome=outcome)
        assert recusal.blocks_decision_capability is False
        assert_actor_not_recused(actor_party_reference=AUTHORITY, recusals=(recusal,), at=T2)


def test_a_superseding_assessment_names_the_one_it_supersedes() -> None:
    """Framework hard invariant 54: declarations are versioned, not
    overwritten."""
    first = _recusal(outcome=ConflictAssessmentOutcome.NO_CONFLICT)
    second = replace(
        _recusal(),
        recusal_id=uuid4(),
        supersedes_recusal_id=first.recusal_id,
    )
    assert second.supersedes_recusal_id == first.recusal_id
    # Both records still exist independently; nothing was rewritten.
    assert first.assessment_outcome is ConflictAssessmentOutcome.NO_CONFLICT


def test_a_replacement_assignment_points_at_the_recusal_it_closes() -> None:
    recusal = _recusal()
    assignment = ReplacementAssignment(
        assignment_id=uuid4(),
        case_id=CASE_ID,
        organization_id=ORG,
        recusal_id=recusal.recusal_id,
        replacement_party_reference=OTHER_AUTHORITY,
        assigned_by_authority_reference=OTHER_AUTHORITY,
        assigned_at=T2,
    )
    assert assignment.recusal_id == recusal.recusal_id


# ===========================================================================
# 9. Case lifecycle
# ===========================================================================


def test_case_status_is_derived_and_the_transition_table_is_closed() -> None:
    case = _case()
    assert case.status is LegalCaseStatus.INTAKE
    with pytest.raises(ProceduralCaseTransitionInvalidError):
        case.transition(
            LegalCaseStatus.CLOSED,
            T1,
            reason_code=REASON,
            actor_authority_reference=AUTHORITY,
            closure_reason_code=REASON,
        )


def test_closing_a_case_requires_an_explicit_closure_reason() -> None:
    determination = _jurisdiction()
    decided = _case(
        path=(
            LegalCaseStatus.INTAKE,
            LegalCaseStatus.JURISDICTION_REVIEW,
            LegalCaseStatus.ADMISSIBILITY_REVIEW,
            LegalCaseStatus.SUBSTANTIVE_REVIEW,
            LegalCaseStatus.DECIDED,
        ),
        jurisdiction_id=determination.jurisdiction_id,
    )
    with pytest.raises(ProceduralCaseTransitionInvalidError, match="closure reason"):
        decided.transition(
            LegalCaseStatus.CLOSED,
            T2,
            reason_code=REASON,
            actor_authority_reference=AUTHORITY,
        )
    closed = decided.transition(
        LegalCaseStatus.CLOSED,
        T2,
        reason_code=REASON,
        actor_authority_reference=AUTHORITY,
        closure_reason_code="COMPLIANCE_LEGAL_CASE_STATUS_CHANGED",
    )
    assert closed.is_closed is True
    assert closed.closed_at == T2


def test_the_transition_history_is_append_only_and_versions_the_case() -> None:
    determination = _jurisdiction()
    case = _case(jurisdiction_id=determination.jurisdiction_id)
    moved = case.transition(
        LegalCaseStatus.JURISDICTION_REVIEW,
        T1,
        reason_code=REASON,
        actor_authority_reference=AUTHORITY,
    )
    assert moved.transition_history[: len(case.transition_history)] == case.transition_history
    assert moved.case_version == case.case_version + 1

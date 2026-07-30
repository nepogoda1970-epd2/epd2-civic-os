"""PACK-14 workflow tests: recovery, proofing, linking, forms, events and
persistence.

Completes task section 30's coverage for the governed workflows and the
governed assets around them.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from _pack14_builders import NOW, account_id, reference, scope

from epd2_identity_service.account_security_events import (
    ACCOUNT_SECURITY_EVENT_TYPES,
    PUBLIC_PROJECTION_ALLOWED,
    REQUIRES_REASON_CODE,
    account_payload,
    build_account_security_event,
    proofing_payload,
    recovery_payload,
    subject_type_for,
    voting_handoff_payload,
)
from epd2_identity_service.domain import (
    AuthenticationAssuranceLevel,
    IdentityAssuranceLevel,
)
from epd2_identity_service.exceptions import (
    AccountLinkingConflictError,
    AccountLinkingDeniedError,
    AccountLinkingProofMissingError,
    ContactAutoMergeRefusedError,
    DuplicateAccountSuspectedError,
    IdempotencyKeyReusedError,
    IdentityProofingInconclusiveError,
    IdentityProofingInsufficientError,
    ProofingDoesNotApproveMembershipError,
    RecordUnderLegalHoldError,
    RecoveryCoolingOffActiveError,
    RecoveryCredentialsNotRevokedError,
    RecoveryDualControlRequiredError,
    RecoveryRiskAcceptanceRequiredError,
    RecoveryRiskTooHighError,
    RetentionScheduleUnconfirmedError,
    SecurityQuestionRefusedError,
    UnknownAccountSecurityEventTypeError,
    UnknownFormIdError,
)
from epd2_identity_service.forms import (
    CLOSURE_MEMBERSHIP_NOTICE_DE,
    CONTENT_IN_FORCE,
    CONTENT_VERSION,
    FORMS,
    PROOFING_NOTICE_DE,
    RECEIPT_CLOSING_DE,
    RefusalText,
    assert_governed_text,
    form,
    governed_text,
)
from epd2_identity_service.identifiers import MappingPurpose
from epd2_identity_service.linking import (
    LinkKind,
    ProofOfControl,
    approve_link,
    refuse_automatic_provider_merge,
    refuse_merge_by_contact,
    refuse_merge_by_personal_attributes,
    refuse_silent_reassignment,
    request_link,
    route_duplicate_to_review,
)
from epd2_identity_service.passwords import refuse_security_question
from epd2_identity_service.persistence import (
    PACK14_EXPIRY_INDEXES,
    PACK14_MIGRATIONS,
    PACK14_RETENTION,
    PACK14_UNIQUE_CONSTRAINTS,
    IdempotencyRecord,
    MigrationKind,
    assert_disposition_permitted,
    assert_idempotent,
    assert_nonce_unused,
    retention_binding,
)
from epd2_identity_service.proofing import (
    IdentityProofingDecision,
    IdentityProofingMethod,
    ProofingState,
    attach_evidence,
    refuse_citizenship_inference,
    refuse_membership_inference,
    route_to_manual_review,
    start_case,
)
from epd2_identity_service.proofing import (
    record_decision as record_proofing_decision,
)
from epd2_identity_service.providers import ProviderSubjectReference
from epd2_identity_service.recovery import (
    RecoveryAssessment,
    RecoveryDecision,
    RecoveryEvidenceReference,
    RecoveryRequest,
    RecoveryRiskAcceptance,
    RecoveryRiskClassification,
    RecoveryState,
    StatedRecoveryReason,
    assert_emergency_recovery_cannot_elevate,
    begin_credential_replacement,
    complete_recovery,
    open_recovery,
    record_assessment,
    record_decision,
    verify_alternate_method,
)
from epd2_identity_service.recovery import (
    attach_evidence as attach_recovery_evidence,
)
from epd2_identity_service.secret_storage import hash_token
from epd2_identity_service.stepup import StepUpBinding, StepUpResult, StepUpStatus

REQUESTER = reference(account_id(), purpose=MappingPurpose.RECOVERY)
REVIEWER = reference(
    account_id("88888888-8888-4888-8888-888888888888"), purpose=MappingPurpose.RECOVERY
)
SECOND = reference(
    account_id("99999999-9999-4999-8999-999999999999"), purpose=MappingPurpose.RECOVERY
)


def _open_case(*, emergency: bool = False) -> RecoveryRequest:
    return open_recovery(
        recovery_id=uuid4(),
        account_id=account_id(),
        requester_reference=REQUESTER,
        stated_reason=StatedRecoveryReason.DEVICE_LOST,
        entry_channel_class="email",
        entry_channel_changed_at=None,
        requested_at=NOW,
        contact_protective_window=timedelta(days=7),
        emergency=emergency,
    )


def _assessment(
    *, dual_control: bool = True, cooling: timedelta = timedelta(hours=48)
) -> RecoveryAssessment:
    return RecoveryAssessment(
        assessed_at=NOW,
        classification=RecoveryRiskClassification.ELEVATED,
        named_signals=("new_device_new_location_immediate_credential_change",),
        required_assurance=AuthenticationAssuranceLevel.HIGH,
        cooling_off=cooling,
        dual_control_required=dual_control,
    )


def _evidence() -> RecoveryEvidenceReference:
    return RecoveryEvidenceReference(
        evidence_reference_id=uuid4(),
        bundle_reference="pack11/bundle/1",
        evidence_class="assisted_channel_record",
        recorded_at=NOW,
    )


# --- recovery ---------------------------------------------------------------


def test_the_full_governed_recovery_workflow() -> None:
    case = _open_case()
    assessed = record_assessment(case, assessment=_assessment())
    assert assessed.state is RecoveryState.COOLING_OFF
    verified = verify_alternate_method(
        assessed, method_independent_of_lost_credential=True, verified=True
    )
    with_evidence = attach_recovery_evidence(verified, evidence=_evidence())
    decided = record_decision(
        with_evidence,
        decision=RecoveryDecision(
            decided_at=NOW + timedelta(days=3),
            reviewer_reference=REVIEWER,
            approved=True,
            reason_code="MANUAL_REVIEW_REQUIRED",
            second_approver_reference=SECOND,
            grant_reference="grant/1",
        ),
        now=NOW + timedelta(days=3),
    )
    assert decided.state is RecoveryState.APPROVED
    replacing = begin_credential_replacement(
        decided, credentials_revoked=True, sessions_revoked=True
    )
    completed = complete_recovery(
        replacing,
        replacement_assurance=AuthenticationAssuranceLevel.HIGH,
        replaced_assurance=AuthenticationAssuranceLevel.HIGH,
        out_of_band_notified=True,
        risk_acceptance=None,
    )
    assert completed.state is RecoveryState.COMPLETED
    assert completed.credentials_revoked and completed.sessions_revoked


def test_a_refused_risk_assessment_ends_the_case_with_its_own_code() -> None:
    case = _open_case()
    with pytest.raises(RecoveryRiskTooHighError):
        record_assessment(
            case,
            assessment=RecoveryAssessment(
                assessed_at=NOW,
                classification=RecoveryRiskClassification.REFUSED,
                named_signals=("account_holds_privileged_grant",),
                required_assurance=AuthenticationAssuranceLevel.HIGH,
                cooling_off=timedelta(hours=48),
                dual_control_required=True,
            ),
        )


def test_a_decision_before_cooling_off_has_elapsed_is_refused() -> None:
    case = record_assessment(_open_case(), assessment=_assessment())
    with pytest.raises(RecoveryCoolingOffActiveError):
        record_decision(
            case,
            decision=RecoveryDecision(
                decided_at=NOW + timedelta(hours=1),
                reviewer_reference=REVIEWER,
                approved=True,
                reason_code="MANUAL_REVIEW_REQUIRED",
                second_approver_reference=SECOND,
                grant_reference="grant/1",
            ),
            now=NOW + timedelta(hours=1),
        )


def test_high_assurance_recovery_requires_a_second_approver() -> None:
    case = record_assessment(_open_case(), assessment=_assessment())
    with pytest.raises(RecoveryDualControlRequiredError):
        record_decision(
            case,
            decision=RecoveryDecision(
                decided_at=NOW + timedelta(days=3),
                reviewer_reference=REVIEWER,
                approved=True,
                reason_code="MANUAL_REVIEW_REQUIRED",
                second_approver_reference=None,
                grant_reference="grant/1",
            ),
            now=NOW + timedelta(days=3),
        )


def test_completion_is_refused_before_credentials_and_sessions_are_revoked() -> None:
    case = record_assessment(_open_case(), assessment=_assessment())
    with_evidence = attach_recovery_evidence(case, evidence=_evidence())
    decided = record_decision(
        with_evidence,
        decision=RecoveryDecision(
            decided_at=NOW + timedelta(days=3),
            reviewer_reference=REVIEWER,
            approved=True,
            reason_code="MANUAL_REVIEW_REQUIRED",
            second_approver_reference=SECOND,
            grant_reference="grant/1",
        ),
        now=NOW + timedelta(days=3),
    )
    with pytest.raises(RecoveryCredentialsNotRevokedError):
        begin_credential_replacement(decided, credentials_revoked=True, sessions_revoked=False)
    with pytest.raises(RecoveryCredentialsNotRevokedError):
        complete_recovery(
            decided,
            replacement_assurance=AuthenticationAssuranceLevel.HIGH,
            replaced_assurance=AuthenticationAssuranceLevel.HIGH,
            out_of_band_notified=True,
            risk_acceptance=None,
        )


def test_a_confidence_shortfall_needs_an_explicit_reason_coded_acceptance() -> None:
    case = record_assessment(_open_case(), assessment=_assessment())
    with_evidence = attach_recovery_evidence(case, evidence=_evidence())
    decided = record_decision(
        with_evidence,
        decision=RecoveryDecision(
            decided_at=NOW + timedelta(days=3),
            reviewer_reference=REVIEWER,
            approved=True,
            reason_code="MANUAL_REVIEW_REQUIRED",
            second_approver_reference=SECOND,
            grant_reference="grant/1",
        ),
        now=NOW + timedelta(days=3),
    )
    replacing = begin_credential_replacement(
        decided, credentials_revoked=True, sessions_revoked=True
    )
    with pytest.raises(RecoveryRiskAcceptanceRequiredError):
        complete_recovery(
            replacing,
            replacement_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
            replaced_assurance=AuthenticationAssuranceLevel.HIGH,
            out_of_band_notified=True,
            risk_acceptance=None,
        )
    completed = complete_recovery(
        replacing,
        replacement_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        replaced_assurance=AuthenticationAssuranceLevel.HIGH,
        out_of_band_notified=True,
        risk_acceptance=RecoveryRiskAcceptance(
            authority_reference="security-board/2026-07",
            reason_code="RECOVERY_RISK_ACCEPTANCE_REQUIRED",
            accepted_at=NOW + timedelta(days=3),
        ),
    )
    assert completed.risk_acceptance is not None


def test_emergency_recovery_does_not_immediately_authorize_a_high_risk_action() -> None:
    case = record_assessment(
        _open_case(emergency=True), assessment=_assessment(cooling=timedelta(hours=1))
    )
    with_evidence = attach_recovery_evidence(case, evidence=_evidence())
    decided = record_decision(
        with_evidence,
        decision=RecoveryDecision(
            decided_at=NOW + timedelta(hours=2),
            reviewer_reference=REVIEWER,
            approved=True,
            reason_code="MANUAL_REVIEW_REQUIRED",
            second_approver_reference=SECOND,
            grant_reference="grant/1",
        ),
        now=NOW + timedelta(hours=2),
    )
    completed = complete_recovery(
        begin_credential_replacement(decided, credentials_revoked=True, sessions_revoked=True),
        replacement_assurance=AuthenticationAssuranceLevel.HIGH,
        replaced_assurance=AuthenticationAssuranceLevel.HIGH,
        out_of_band_notified=True,
        risk_acceptance=None,
    )
    from epd2_identity_service.exceptions import RecoveryElevationRefusedError

    with pytest.raises(RecoveryElevationRefusedError):
        assert_emergency_recovery_cannot_elevate(
            completed, required_assurance=AuthenticationAssuranceLevel.HIGH
        )
    assert_emergency_recovery_cannot_elevate(
        completed, required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL
    )


def test_security_questions_are_refused_outright() -> None:
    with pytest.raises(SecurityQuestionRefusedError):
        refuse_security_question("Wie hieß Ihre erste Schule?")


# --- identity proofing ------------------------------------------------------


def test_a_method_cannot_be_started_for_an_assurance_it_cannot_reach() -> None:
    with pytest.raises(IdentityProofingInsufficientError):
        start_case(
            case_id=uuid4(),
            account_id=account_id(),
            method=IdentityProofingMethod.EMAIL_VERIFIED,
            requested_assurance=IdentityAssuranceLevel.HIGH,
            started_at=NOW,
        )


def test_a_reviewed_method_cannot_be_decided_automatically() -> None:
    case = start_case(
        case_id=uuid4(),
        account_id=account_id(),
        method=IdentityProofingMethod.DOCUMENT_ASSISTED,
        requested_assurance=IdentityAssuranceLevel.SUBSTANTIAL,
        started_at=NOW,
    )
    from epd2_identity_service.proofing import IdentityEvidenceReference

    with_evidence = attach_evidence(
        case,
        evidence=IdentityEvidenceReference(
            evidence_reference_id=uuid4(),
            bundle_reference="pack11/bundle/9",
            evidence_class="identity_document",
            recorded_at=NOW,
        ),
    )
    decision = IdentityProofingDecision(
        decided_at=NOW,
        verified=True,
        achieved_assurance=IdentityAssuranceLevel.SUBSTANTIAL,
        deciding_authority="proofing-reviewer/1",
        reason_code="IDENTITY_VERIFIED",
    )
    with pytest.raises(IdentityProofingInconclusiveError):
        record_proofing_decision(with_evidence, decision=decision)
    reviewed = route_to_manual_review(with_evidence)
    verified = record_proofing_decision(reviewed, decision=decision)
    assert verified.state is ProofingState.VERIFIED


def test_proofing_never_approves_membership_and_never_implies_citizenship() -> None:
    case = start_case(
        case_id=uuid4(),
        account_id=account_id(),
        method=IdentityProofingMethod.EID,
        requested_assurance=IdentityAssuranceLevel.HIGH,
        started_at=NOW,
    )
    with pytest.raises(ProofingDoesNotApproveMembershipError):
        refuse_membership_inference(case)
    with pytest.raises(IdentityProofingInsufficientError):
        refuse_citizenship_inference("eIDAS-DE")


def test_a_proofing_event_carries_a_bundle_reference_and_no_attributes() -> None:
    payload = proofing_payload(
        method="document_assisted",
        evidence_reference="pack11/bundle/9",
        achieved_assurance="substantial",
        deciding_authority="proofing-reviewer/1",
    )
    assert "declared_name" not in payload
    assert "date_of_birth" not in payload
    assert payload["evidence_reference"] == "pack11/bundle/9"


# --- account linking --------------------------------------------------------


def test_all_four_merges_are_refused() -> None:
    with pytest.raises(ContactAutoMergeRefusedError):
        refuse_merge_by_contact(account_id(), account_id("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    with pytest.raises(AccountLinkingDeniedError):
        refuse_merge_by_personal_attributes(("name", "date_of_birth"))
    with pytest.raises(AccountLinkingDeniedError):
        refuse_automatic_provider_merge(
            ProviderSubjectReference(issuer="https://idp.example", subject_digest="ab" * 32)
        )
    link = request_link(
        link_request_id=uuid4(),
        account_id=account_id(),
        initiator_reference=reference(account_id()),
        kind=LinkKind.EXTERNAL_PROVIDER,
        requested_at=NOW,
        subject_reference=ProviderSubjectReference(
            issuer="https://idp.example", subject_digest="cd" * 32
        ),
    )
    with pytest.raises(AccountLinkingConflictError):
        refuse_silent_reassignment(link)


def test_linking_needs_both_proofs_and_a_bound_step_up() -> None:
    from epd2_identity_service.linking import record_proof

    subject = ProviderSubjectReference(issuer="https://idp.example", subject_digest="ef" * 32)
    link = request_link(
        link_request_id=uuid4(),
        account_id=account_id(),
        initiator_reference=reference(account_id()),
        kind=LinkKind.EXTERNAL_PROVIDER,
        requested_at=NOW,
        subject_reference=subject,
    )
    step_up = StepUpResult(
        challenge_id=uuid4(),
        binding=_link_binding(),
        achieved_assurance=AuthenticationAssuranceLevel.HIGH,
        method=__import__(
            "epd2_identity_service.assurance", fromlist=["AuthenticationMethod"]
        ).AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        completed_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        status=StepUpStatus.SATISFIED,
    )
    with pytest.raises(AccountLinkingProofMissingError):
        approve_link(link, step_up=step_up, existing_links=(), approved_at=NOW)
    proven = record_proof(
        link,
        this_side=ProofOfControl(method="passkey", established_at=NOW),
        other_side=ProofOfControl(method="provider_assertion", established_at=NOW),
    )
    approved = approve_link(proven, step_up=step_up, existing_links=(), approved_at=NOW)
    assert approved.state.value == "approved"


def _link_binding() -> StepUpBinding:
    from epd2_identity_service.identifiers import SessionId
    from epd2_identity_service.stepup import StepUpBinding

    return StepUpBinding(
        actor_reference=reference(account_id()),
        session_id=SessionId(uuid4()),
        action_code="link_account",
        resource_type="account_link",
        resource_id=uuid4(),
        resource_version=1,
    )


def test_a_suspected_duplicate_is_routed_to_review_not_merged() -> None:
    with pytest.raises(DuplicateAccountSuspectedError):
        route_duplicate_to_review(
            candidate_account_id=account_id(), named_signals=("same_normalized_email",)
        )


# --- forms and governed content ---------------------------------------------


def test_the_form_inventory_carries_all_fifteen_forms() -> None:
    assert len(FORMS) == 15
    assert {key for key in FORMS} == {f"F-P14-{index:02d}" for index in range(1, 16)}
    for definition in FORMS.values():
        assert definition.provisional is True
        assert definition.retention_class in PACK14_RETENTION


def test_the_content_catalogue_is_versioned_and_not_yet_in_force() -> None:
    assert CONTENT_VERSION == "P14-DE-1.0.0"
    assert CONTENT_IN_FORCE is False


def test_a_refusal_text_cannot_omit_the_body_or_the_next_step() -> None:
    RefusalText(
        reason_de="Ihr Konto ist derzeit gesperrt.",
        responsible_body_de="Zuständig ist die Sicherheitsverwaltung.",
        next_step_de="Sie können Widerspruch einlegen.",
    )
    with pytest.raises(ValueError, match="nächsten möglichen Schritt"):
        RefusalText(
            reason_de="Ihr Konto ist derzeit gesperrt.",
            responsible_body_de="Zuständig ist die Sicherheitsverwaltung.",
            next_step_de="   ",
        )


def test_consequential_content_is_never_invented_at_a_call_site() -> None:
    assert governed_text("SESSION_EXPIRED").startswith("Ihre Sitzung ist abgelaufen")
    with pytest.raises(UnknownFormIdError):
        governed_text("NO_SUCH_CODE")
    assert_governed_text(CLOSURE_MEMBERSHIP_NOTICE_DE)
    assert_governed_text(PROOFING_NOTICE_DE)
    assert_governed_text(RECEIPT_CLOSING_DE)
    with pytest.raises(UnknownFormIdError):
        assert_governed_text("Ihr Konto wurde geschlossen.")


def test_the_closure_notice_says_closure_is_not_resignation() -> None:
    assert "beendet nicht Ihre Mitgliedschaft" in CLOSURE_MEMBERSHIP_NOTICE_DE
    assert form("F-P14-13").step_up_required is True


def test_the_proofing_notice_carries_canon_19d2_s_prohibition() -> None:
    assert "keine Aussage über Ihre Staatsangehörigkeit" in PROOFING_NOTICE_DE


# --- events -----------------------------------------------------------------


def test_the_event_catalogue_has_fifty_nine_types_in_nine_families() -> None:
    assert len(ACCOUNT_SECURITY_EVENT_TYPES) == 59
    assert len(set(ACCOUNT_SECURITY_EVENT_TYPES)) == 59
    prefixes = {event_type.split(".", 1)[0] for event_type in ACCOUNT_SECURITY_EVENT_TYPES}
    assert len(prefixes) == 9
    for event_type in ACCOUNT_SECURITY_EVENT_TYPES:
        assert subject_type_for(event_type)


def test_no_pack14_event_is_publicly_projectable() -> None:
    assert frozenset() == PUBLIC_PROJECTION_ALLOWED


def test_an_adverse_event_without_a_reason_code_is_refused() -> None:
    actor = reference(account_id())
    for event_type in sorted(REQUIRES_REASON_CODE):
        with pytest.raises(UnknownAccountSecurityEventTypeError):
            build_account_security_event(
                event_id=uuid4(),
                event_type=event_type,
                subject_id=uuid4(),
                actor=actor,
                payload={"account_status": "active"},
                correlation_id=uuid4(),
                causation_id=None,
                occurred_at=NOW,
            )


def test_an_unknown_event_type_and_major_version_both_fail_closed() -> None:
    actor = reference(account_id())
    with pytest.raises(UnknownAccountSecurityEventTypeError):
        build_account_security_event(
            event_id=uuid4(),
            event_type="account.invented",
            subject_id=uuid4(),
            actor=actor,
            payload={},
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=NOW,
        )
    from epd2_identity_service.exceptions import (
        UnsupportedAccountSecurityEventVersionError,
    )

    with pytest.raises(UnsupportedAccountSecurityEventVersionError):
        build_account_security_event(
            event_id=uuid4(),
            event_type="account.created",
            subject_id=uuid4(),
            actor=actor,
            payload=account_payload(account_status="pending"),
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=NOW,
            event_version="2.0",
        )


def test_a_locked_event_reports_the_unchanged_account_status() -> None:
    payload = account_payload(
        account_status="active",
        reason_code="ACCOUNT_LOCKED",
        lock_reference=str(uuid4()),
        expires_at=NOW + timedelta(minutes=15),
    )
    assert payload["account_status"] == "active"
    assert payload["lock_reference"]


def test_a_recovery_event_names_signals_and_a_role_not_a_score_or_a_reviewer() -> None:
    payload = recovery_payload(
        risk_classification="elevated",
        named_signals=("repeated_partial_recoveries",),
        reviewer_role="recovery_reviewer",
        dual_control_satisfied=True,
        reason_code="MANUAL_REVIEW_REQUIRED",
    )
    assert payload["named_signals"] == ["repeated_partial_recoveries"]
    assert "risk_score" not in payload
    assert "reviewer_id" not in payload


def test_a_voting_handoff_event_carries_purpose_and_expiry_only() -> None:
    context = uuid4()
    payload = voting_handoff_payload(
        purpose="voting_entry", voting_context_id=context, expires_at=NOW + timedelta(minutes=2)
    )
    assert set(payload) == {"purpose", "voting_context_id", "expires_at"}


# --- persistence ------------------------------------------------------------


def test_the_migration_list_is_ordered_expand_only_and_reversible() -> None:
    sequences = [migration.sequence for migration in PACK14_MIGRATIONS]
    assert sequences == sorted(sequences) == list(range(1, len(PACK14_MIGRATIONS) + 1))
    assert all(migration.kind is MigrationKind.EXPAND for migration in PACK14_MIGRATIONS)
    assert all(migration.reversible for migration in PACK14_MIGRATIONS)


def test_every_uniqueness_rule_and_expiry_index_states_its_rationale() -> None:
    assert PACK14_UNIQUE_CONSTRAINTS
    assert PACK14_EXPIRY_INDEXES
    for constraint in PACK14_UNIQUE_CONSTRAINTS:
        assert constraint.rationale
    for index in PACK14_EXPIRY_INDEXES:
        assert index.rationale


def test_every_record_class_has_a_schedule_and_none_is_confirmed_yet() -> None:
    """`OD-P14-07` in one assertion."""
    for record_class, binding in PACK14_RETENTION.items():
        assert binding.record_class == record_class
        assert binding.duration_confirmed is False
        assert binding.deletion_effect


def test_deletion_under_a_hold_and_an_unknown_hold_state_both_refuse() -> None:
    with pytest.raises(RecordUnderLegalHoldError):
        assert_disposition_permitted("recovery_evidence", legal_hold_state=True, dispute_open=False)
    with pytest.raises(RecordUnderLegalHoldError):
        assert_disposition_permitted("recovery_evidence", legal_hold_state=None, dispute_open=False)
    with pytest.raises(RecordUnderLegalHoldError):
        assert_disposition_permitted("recovery_evidence", legal_hold_state=False, dispute_open=True)


def test_a_destructive_disposition_is_refused_while_the_schedule_is_unconfirmed() -> None:
    with pytest.raises(RetentionScheduleUnconfirmedError):
        assert_disposition_permitted(
            "voting_handoff_issuance", legal_hold_state=False, dispute_open=False
        )
    assert retention_binding("voting_handoff_issuance").legal_hold_applies is False


def test_idempotency_distinguishes_a_replay_from_a_reused_key() -> None:
    record = IdempotencyRecord(
        idempotency_key="k",
        request_digest="d",
        operation="create_account",
        recorded_at=NOW,
    )
    assert (
        assert_idempotent(
            record, idempotency_key="k", request_digest="d", operation="create_account"
        )
        is True
    )
    assert (
        assert_idempotent(None, idempotency_key="k", request_digest="d", operation="create_account")
        is False
    )
    with pytest.raises(IdempotencyKeyReusedError):
        assert_idempotent(
            record, idempotency_key="k", request_digest="other", operation="create_account"
        )


def test_a_nonce_is_single_use_across_the_whole_store() -> None:
    from epd2_identity_service.exceptions import NonceAlreadyUsedError

    seen = frozenset({hash_token("nonce-1").digest})
    assert_nonce_unused("nonce-2", seen=seen)
    with pytest.raises(NonceAlreadyUsedError):
        assert_nonce_unused("nonce-1", seen=seen)


def test_the_scope_helper_stays_stable_for_the_suite() -> None:
    assert scope().level.value == "land"

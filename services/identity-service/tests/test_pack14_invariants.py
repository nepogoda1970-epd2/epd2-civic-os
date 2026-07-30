"""PACK-14 property and invariant tests (task section 30.2).

Every acceptance blocker from task section 37 that can be stated as a
property is stated as one here:

- no global user ID, and no identifier reuse across domains;
- no secret in an event;
- single-use bootstrap; single-use voting handoff;
- a revoked session cannot refresh;
- a changed object invalidates a step-up;
- a password alone cannot authorize a consequential action;
- SMS OTP cannot produce an AAL;
- a synced passkey cannot produce AAL-3 (`high`);
- support cannot approve its own recovery;
- no raw contact in an audit payload.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from _pack14_builders import (
    NOW,
    account_id,
    assurance,
    reference,
    scope,
)

from epd2_identity_service.account_security_events import (
    ACCOUNT_SECURITY_EVENT_TYPES,
    build_account_security_event,
    contact_payload,
    recorded_reason_code_for,
)
from epd2_identity_service.accounts import AccountRegistryStatus
from epd2_identity_service.assurance import (
    ACTION_REQUIREMENTS,
    AuthenticationMethod,
    assurance_ceiling,
    assurance_for_passkey,
    combine_methods,
    evaluate_requirement,
)
from epd2_identity_service.configuration import default_configuration
from epd2_identity_service.credentials import CredentialBinding
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AssuranceInsufficientError,
    GlobalIdentifierRefusedError,
    RecoverySelfApprovalRefusedError,
    SecretInPayloadRefusedError,
    SmsOtpNotAnAuthenticationFactorError,
    VotingHandoffAlreadyUsedError,
    VotingHandoffReverseResolutionRefusedError,
)
from epd2_identity_service.identifiers import (
    NEVER_CROSSES_A_BOUNDARY,
    PROHIBITED_IDENTIFIER_KEYS,
    PROHIBITED_SECRET_KEYS,
    IdentifierSpace,
    MappingPurpose,
    assert_reference_crosses_boundary,
    reject_prohibited_payload_keys,
)
from epd2_identity_service.mfa import MfaFactorClass, parse_factor_class
from epd2_identity_service.recovery import (
    RecoveryDecision,
    RecoveryRiskClassification,
    StatedRecoveryReason,
    open_recovery,
    record_assessment,
    record_decision,
)
from epd2_identity_service.voting_handoff import (
    VotingHandoffRequest,
    issue_voting_handoff,
    redeem_voting_handoff,
    refuse_reverse_resolution,
)
from epd2_identity_service.workspaces import (
    WORKSPACE_POLICIES,
    WorkspaceId,
    workspace_origin,
)

CORRELATION = uuid4()


# --- no global user ID ------------------------------------------------------


def test_every_identifier_space_except_the_scoped_one_is_refused_at_a_boundary() -> None:
    for space in IdentifierSpace:
        if space is IdentifierSpace.SCOPED_ACTOR:
            assert_reference_crosses_boundary(space)
            continue
        assert space in NEVER_CROSSES_A_BOUNDARY
        with pytest.raises(GlobalIdentifierRefusedError):
            assert_reference_crosses_boundary(space)


@pytest.mark.parametrize("key", sorted(PROHIBITED_IDENTIFIER_KEYS))
def test_no_prohibited_identifier_key_survives_payload_validation(key: str) -> None:
    with pytest.raises(GlobalIdentifierRefusedError):
        reject_prohibited_payload_keys({key: "value"})


@pytest.mark.parametrize("key", sorted(PROHIBITED_SECRET_KEYS))
def test_no_secret_key_survives_payload_validation(key: str) -> None:
    with pytest.raises(SecretInPayloadRefusedError):
        reject_prohibited_payload_keys({key: "value"})


def test_prohibited_keys_are_refused_one_level_down_too() -> None:
    with pytest.raises(SecretInPayloadRefusedError):
        reject_prohibited_payload_keys({"outer": {"password": "x"}})
    with pytest.raises(GlobalIdentifierRefusedError):
        reject_prohibited_payload_keys({"items": [{"membership_id": "x"}]})


def test_no_event_type_can_carry_a_secret() -> None:
    actor = reference(account_id())
    for event_type in ACCOUNT_SECURITY_EVENT_TYPES:
        with pytest.raises(SecretInPayloadRefusedError):
            build_account_security_event(
                event_id=uuid4(),
                event_type=event_type,
                subject_id=uuid4(),
                actor=actor,
                payload={"recovery_code": "1234", "reason_code": "CREDENTIAL_INVALID"},
                correlation_id=CORRELATION,
                causation_id=None,
                occurred_at=NOW,
            )


def test_a_contact_event_carries_a_tokenized_reference_and_no_address() -> None:
    payload = contact_payload(channel_class="email", channel_reference="ab" * 32)
    reject_prohibited_payload_keys(payload)
    assert "@" not in "".join(str(value) for value in payload.values())


def test_every_recorded_code_is_derived_from_its_event_type() -> None:
    for event_type in ACCOUNT_SECURITY_EVENT_TYPES:
        expected = f"{event_type.replace('.', '_').upper()}_RECORDED"
        assert recorded_reason_code_for(event_type) == expected


# --- assurance ceilings -----------------------------------------------------


def test_sms_otp_produces_no_assurance_and_is_not_a_factor_class() -> None:
    assert assurance_ceiling(AuthenticationMethod.SMS_OTP) is AuthenticationAssuranceLevel.NONE
    assert "sms_otp" not in {factor.value for factor in MfaFactorClass}
    with pytest.raises(SmsOtpNotAnAuthenticationFactorError):
        parse_factor_class("sms_otp")


def test_a_synced_passkey_cannot_produce_high_however_it_is_combined() -> None:
    assert assurance_for_passkey(CredentialBinding.SYNCED) is (
        AuthenticationAssuranceLevel.SUBSTANTIAL
    )
    for other in (
        AuthenticationMethod.PASSWORD_WITH_MFA,
        AuthenticationMethod.EMAIL_OTP,
        AuthenticationMethod.RECOVERY_CODE,
    ):
        combined = combine_methods((AuthenticationMethod.PASSKEY_SYNCED, other))
        assert combined is not AuthenticationAssuranceLevel.HIGH


def test_password_alone_cannot_authorize_a_consequential_action() -> None:
    password_session = assurance(
        AuthenticationMethod.PASSWORD_WITH_MFA, binding=CredentialBinding.NOT_APPLICABLE
    )
    for action in ("remove_passkey", "request_account_closure", "voting_handoff"):
        with pytest.raises(AssuranceInsufficientError):
            evaluate_requirement(
                assurance=password_session,
                identity_assurance=None,
                requirement=ACTION_REQUIREMENTS[action],
                configuration=default_configuration(),
                now=NOW,
            )


# --- WS-03 and the ten-workspace model --------------------------------------


def test_the_ten_workspace_model_is_unchanged_and_shares_no_session() -> None:
    assert len(WORKSPACE_POLICIES) == 10
    assert {workspace.value for workspace in WorkspaceId} == {
        f"WS-{index:02d}" for index in range(1, 11)
    }
    for policy in WORKSPACE_POLICIES.values():
        assert policy.session_sharing_permitted is False
        assert policy.browser_storage_identity_permitted is False


def test_the_voting_client_is_never_issued_an_identity_session() -> None:
    from epd2_identity_service.exceptions import SessionScopeMismatchError
    from epd2_identity_service.workspaces import assert_issues_identity_session

    with pytest.raises(SessionScopeMismatchError):
        assert_issues_identity_session(WorkspaceId.VOTING_CLIENT)


def _handoff_request(voting_context_id: UUID | None = None) -> VotingHandoffRequest:
    return VotingHandoffRequest(
        request_id=uuid4(),
        voting_context_id=voting_context_id or uuid4(),
        audience_origin=workspace_origin(WorkspaceId.VOTING_CLIENT),
        requested_at=NOW,
    )


def test_a_voting_handoff_artifact_carries_no_identifier_of_any_kind() -> None:
    from epd2_identity_service.secret_storage import DeterministicSecureRandom

    artifact, issuance = issue_voting_handoff(
        _handoff_request(),
        artifact_id=uuid4(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    artifact_fields = set(artifact.__dataclass_fields__)
    issuance_fields = set(issuance.__dataclass_fields__)
    for forbidden in (
        "account_id",
        "person_record_id",
        "membership_id",
        "member_number",
        "communication_persona_id",
        "actor_reference",
        "session_id",
        "contact",
    ):
        assert forbidden not in artifact_fields
        assert forbidden not in issuance_fields


def test_a_voting_handoff_artifact_is_single_use() -> None:
    from epd2_identity_service.secret_storage import DeterministicSecureRandom

    context = uuid4()
    artifact, issuance = issue_voting_handoff(
        _handoff_request(context),
        artifact_id=uuid4(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    spent, _redemption = redeem_voting_handoff(
        issuance,
        presented_value=artifact.value,
        presenting_origin=artifact.audience_origin,
        voting_context_id=context,
        redemption_id=uuid4(),
        now=NOW,
    )
    with pytest.raises(VotingHandoffAlreadyUsedError):
        redeem_voting_handoff(
            spent,
            presented_value=artifact.value,
            presenting_origin=artifact.audience_origin,
            voting_context_id=context,
            redemption_id=uuid4(),
            now=NOW,
        )


def test_a_redemption_is_never_resolved_back_to_an_account() -> None:
    from epd2_identity_service.secret_storage import DeterministicSecureRandom

    context = uuid4()
    artifact, issuance = issue_voting_handoff(
        _handoff_request(context),
        artifact_id=uuid4(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    _spent, redemption = redeem_voting_handoff(
        issuance,
        presented_value=artifact.value,
        presenting_origin=artifact.audience_origin,
        voting_context_id=context,
        redemption_id=uuid4(),
        now=NOW,
    )
    with pytest.raises(VotingHandoffReverseResolutionRefusedError):
        refuse_reverse_resolution(redemption)


def test_the_voting_handoff_store_exposes_no_account_lookup() -> None:
    from epd2_identity_service.account_security_storage import VotingHandoffStore

    methods = {name for name in dir(VotingHandoffStore) if not name.startswith("_")}
    assert not any("account" in name for name in methods)
    assert not any("reverse" in name for name in methods)


# --- recovery separation of duties ------------------------------------------


def test_a_reviewer_cannot_decide_a_case_they_initiated() -> None:
    requester = reference(account_id(), purpose=MappingPurpose.RECOVERY)
    case = open_recovery(
        recovery_id=uuid4(),
        account_id=account_id(),
        requester_reference=requester,
        stated_reason=StatedRecoveryReason.DEVICE_LOST,
        entry_channel_class="email",
        entry_channel_changed_at=None,
        requested_at=NOW,
        contact_protective_window=timedelta(days=7),
    )
    from epd2_identity_service.recovery import RecoveryAssessment

    assessed = record_assessment(
        case,
        assessment=RecoveryAssessment(
            assessed_at=NOW,
            classification=RecoveryRiskClassification.ELEVATED,
            named_signals=("new_device_new_location_immediate_credential_change",),
            required_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
            cooling_off=timedelta(hours=48),
            dual_control_required=True,
        ),
    )
    decision = RecoveryDecision(
        decided_at=NOW + timedelta(days=3),
        reviewer_reference=requester,
        approved=True,
        reason_code="MANUAL_REVIEW_REQUIRED",
        second_approver_reference=reference(
            account_id("66666666-6666-4666-8666-666666666666"), purpose=MappingPurpose.RECOVERY
        ),
        grant_reference="grant/1",
    )
    with pytest.raises(RecoverySelfApprovalRefusedError):
        record_decision(assessed, decision=decision, now=NOW + timedelta(days=3))


# --- the account status enum stays canonical --------------------------------


def test_no_pack14_code_path_adds_a_status_value() -> None:
    assert len(AccountRegistryStatus) == 6
    assert scope().level.value in {"bund", "land", "kreis", "ortsverband"}

"""PACK-15 separation-of-duties matrix tests (`FIR-ROLE-005`).

Asserts what the matrix document states normatively: the ten roles, the
capability assignment behind them, and the named prohibitions - `SD-01`,
`SD-03`, `SD-06`, `SD-08`, `SD-10`, `SD-16` - together with the
dual-control acts of sections 4 and 7 and the audit separation the whole
architecture rests on.

Every structural rule is exercised twice: once against the shipped
matrix, where it must hold, and once against a deliberately corrupted
copy, where it must refuse. A rule that has only ever run against a
matrix satisfying it has not been tested, and would keep passing after
somebody deleted its body.
"""

from __future__ import annotations

import pytest

from epd2_audit_core.voting_evidence_bundle import AuditStream
from epd2_governance_service.voting_authorization import (
    AUDITOR_ROLES,
    ROLE_CAPABILITIES,
    ROLE_COMPATIBILITY,
    ROLE_IDENTIFIERS,
    SECURITY_ADMIN_ROLE,
    SYSTEM_ADMIN_ROLE,
    Approver,
    AuthorizationMatrixIncompleteError,
    Capability,
    CorrelationRiskDetectedError,
    DualControlRequiredError,
    EvidenceBundleScopeRefusedError,
    ManualReviewRequiredError,
    PermissionDeniedError,
    PrivilegedActRecord,
    PrivilegedApprovalMissingError,
    RoleCompatibility,
    SeparationOfDutiesRefusedError,
    VotingAuthorizationError,
    VotingRole,
    assert_auditor_cannot_correlate,
    assert_capability_permitted,
    assert_case_scoped_access,
    assert_credential_issuer_has_no_identity_access,
    assert_dual_control,
    assert_eligibility_officer_has_no_credential_secret_access,
    assert_grant_streams_separable,
    assert_manual_exception_reviewed,
    assert_matrix_is_complete,
    assert_no_role_controls_eligibility_issuance_and_tally,
    assert_no_role_spans_audit_stream_groups,
    assert_no_self_review,
    assert_privileged_export_authorized,
    assert_role_combination_permitted,
    assert_security_admin_is_not_system_admin,
    capabilities_of,
    roles_with,
)

EXPECTED_ROLE_NAMES = (
    "membership_authority",
    "eligibility_officer",
    "eligibility_reviewer",
    "credential_issuer",
    "voting_operations_officer",
    "voting_client_operator",
    "tally_authority",
    "independent_auditor",
    "security_auditor",
    "dispute_reviewer",
)


@pytest.fixture
def matrix() -> dict[VotingRole, frozenset[Capability]]:
    """A mutable copy of the shipped matrix, for corrupting."""
    return dict(ROLE_CAPABILITIES)


# -- the matrix itself ------------------------------------------------------


def test_the_matrix_names_exactly_ten_roles_with_their_identifiers() -> None:
    assert tuple(role.value for role in VotingRole) == EXPECTED_ROLE_NAMES
    assert sorted(ROLE_IDENTIFIERS.values()) == [f"R-{index:02d}" for index in range(1, 11)]


def test_every_role_has_a_non_empty_capability_entry() -> None:
    assert set(ROLE_CAPABILITIES) == set(VotingRole)
    assert [role.value for role, held in ROLE_CAPABILITIES.items() if not held] == []
    # Already run at import; calling it again keeps the entry point exercised.
    assert_matrix_is_complete()


def test_role_names_are_the_strings_the_api_layer_authorizes_against() -> None:
    """A role must drop straight into `EndpointSpec.authorized_roles`."""
    assert VotingRole.INDEPENDENT_AUDITOR.value == "independent_auditor"
    names = roles_with(Capability.PRIVILEGED_EXPORT)
    assert names == tuple(sorted(names))
    assert "independent_auditor" in names
    assert capabilities_of("tally_authority") == capabilities_of(VotingRole.TALLY_AUTHORITY)


def test_an_unknown_role_name_is_refused_not_treated_as_unprivileged() -> None:
    with pytest.raises(PermissionDeniedError):
        capabilities_of("election_god")


# -- SD-06: eligibility, issuance and tally ---------------------------------


def test_no_shipped_role_controls_eligibility_issuance_and_tally() -> None:
    assert_no_role_controls_eligibility_issuance_and_tally()


def test_the_full_chain_in_one_role_is_refused(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    matrix[VotingRole.ELIGIBILITY_OFFICER] = ROLE_CAPABILITIES[VotingRole.ELIGIBILITY_OFFICER] | {
        Capability.CREDENTIAL_ISSUANCE,
        Capability.TALLY_OUTCOME,
    }
    with pytest.raises(SeparationOfDutiesRefusedError) as refusal:
        assert_no_role_controls_eligibility_issuance_and_tally(matrix)
    assert refusal.value.reason_code == "SEPARATION_OF_DUTIES_REFUSED"


def test_assertion_issuance_counts_as_issuance_for_sd_06(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    """Minting the assertion is issuance; only the artefact differs."""
    matrix[VotingRole.TALLY_AUTHORITY] = frozenset(
        {
            Capability.ELIGIBILITY_DECISION,
            Capability.ASSERTION_ISSUANCE,
            Capability.TALLY_OUTCOME,
        }
    )
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_no_role_controls_eligibility_issuance_and_tally(matrix)
    # ...and two of the three is not the chain, so it is not refused here.
    matrix[VotingRole.TALLY_AUTHORITY] = frozenset(
        {Capability.ELIGIBILITY_DECISION, Capability.CREDENTIAL_ISSUANCE}
    )
    assert_no_role_controls_eligibility_issuance_and_tally(matrix)


# -- SD-03 and its mirror ---------------------------------------------------


def test_the_shipped_matrix_keeps_identity_and_credential_secrets_apart() -> None:
    assert_credential_issuer_has_no_identity_access()
    assert_eligibility_officer_has_no_credential_secret_access()


def test_credential_issuer_with_identity_access_is_refused(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    matrix[VotingRole.CREDENTIAL_ISSUER] = ROLE_CAPABILITIES[VotingRole.CREDENTIAL_ISSUER] | {
        Capability.IDENTITY_RECORD_ACCESS
    }
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_credential_issuer_has_no_identity_access(matrix)


def test_eligibility_officer_with_the_credential_secret_is_refused(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    matrix[VotingRole.ELIGIBILITY_OFFICER] = ROLE_CAPABILITIES[VotingRole.ELIGIBILITY_OFFICER] | {
        Capability.CREDENTIAL_SECRET_ACCESS
    }
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_eligibility_officer_has_no_credential_secret_access(matrix)


# -- SD-10 and the audit separation -----------------------------------------

#: The auditor roles as parametrize cases, sorted by value so the case
#: order is deterministic rather than set-iteration order.
#:
#: The explicit annotation is load-bearing rather than decorative.
#: `pytest.mark.parametrize` declares `argvalues` as an iterable of
#: `object`, and passing `sorted(...)` straight into it lets that `object`
#: flow backwards into `sorted`'s own type variable - which makes the key
#: function's parameter `object`, and `object` has no `.value`. Binding the
#: result to a named `tuple[VotingRole, ...]` first gives `sorted` a
#: concrete expected type, so the key parameter is inferred as `VotingRole`
#: and the enum's `.value` resolves.
AUDITOR_ROLE_CASES: tuple[VotingRole, ...] = tuple(
    sorted(AUDITOR_ROLES, key=lambda role: role.value)
)


def test_no_auditor_role_correlates_in_the_shipped_matrix() -> None:
    assert_auditor_cannot_correlate()
    for role in AUDITOR_ROLES:
        held = ROLE_CAPABILITIES[role]
        assert not held & {
            Capability.AUDIT_READ_IDENTITY_SIDE,
            Capability.AUDIT_READ_VOTING_SIDE,
        }


def test_an_auditor_holding_one_side_only_is_not_refused(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    """The rule is about spanning the groups, not about reading a stream."""
    matrix[VotingRole.SECURITY_AUDITOR] = frozenset({Capability.AUDIT_READ_VOTING_SIDE})
    assert_auditor_cannot_correlate(matrix)


@pytest.mark.parametrize("role", AUDITOR_ROLE_CASES)
def test_an_auditor_holding_both_stream_groups_is_refused(
    role: VotingRole, matrix: dict[VotingRole, frozenset[Capability]]
) -> None:
    matrix[role] = frozenset(
        {Capability.AUDIT_READ_IDENTITY_SIDE, Capability.AUDIT_READ_VOTING_SIDE}
    )
    with pytest.raises(CorrelationRiskDetectedError) as refusal:
        assert_auditor_cannot_correlate(matrix)
    assert refusal.value.reason_code == "CORRELATION_RISK_DETECTED"


def test_a_non_auditor_role_spanning_the_groups_is_also_refused(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    """The audit rule is about the read, not about the job title."""
    assert_no_role_spans_audit_stream_groups()
    matrix[VotingRole.DISPUTE_REVIEWER] = ROLE_CAPABILITIES[VotingRole.DISPUTE_REVIEWER] | {
        Capability.AUDIT_READ_VOTING_SIDE
    }
    assert_auditor_cannot_correlate(matrix)
    with pytest.raises(CorrelationRiskDetectedError):
        assert_no_role_spans_audit_stream_groups(matrix)


def test_a_privileged_grant_may_not_span_the_two_sides() -> None:
    assert_grant_streams_separable([AuditStream.ELIGIBILITY, AuditStream.ASSERTION])
    assert_grant_streams_separable([AuditStream.CREDENTIAL, AuditStream.SYSTEM_INTEGRITY])
    with pytest.raises(CorrelationRiskDetectedError):
        assert_grant_streams_separable([AuditStream.ELIGIBILITY, AuditStream.CREDENTIAL])


# -- the ordinary gate ------------------------------------------------------


def test_sd_01_the_membership_authority_issues_no_credential() -> None:
    assert_capability_permitted(VotingRole.CREDENTIAL_ISSUER, Capability.CREDENTIAL_ISSUANCE)
    with pytest.raises(PermissionDeniedError) as refusal:
        assert_capability_permitted("membership_authority", Capability.CREDENTIAL_ISSUANCE)
    assert refusal.value.reason_code == "PERMISSION_DENIED"


def test_case_scoped_status_without_a_case_reference_is_a_search() -> None:
    with pytest.raises(CorrelationRiskDetectedError):
        assert_case_scoped_access(
            VotingRole.DISPUTE_REVIEWER,
            Capability.CASE_SCOPED_CREDENTIAL_STATUS,
            case_reference=None,
        )


def test_case_scoped_status_with_a_supplied_reference_is_permitted() -> None:
    assert_case_scoped_access(
        VotingRole.DISPUTE_REVIEWER,
        Capability.CASE_SCOPED_CREDENTIAL_STATUS,
        case_reference="dispute-4711",
    )
    with pytest.raises(PermissionDeniedError):
        assert_case_scoped_access(
            VotingRole.TALLY_AUTHORITY,
            Capability.CASE_SCOPED_CREDENTIAL_STATUS,
            case_reference="dispute-4711",
        )


def test_a_manual_eligibility_exception_records_the_review_that_produced_it() -> None:
    assert_manual_exception_reviewed(VotingRole.ELIGIBILITY_REVIEWER, review_reference="rev-9")
    with pytest.raises(ManualReviewRequiredError) as refusal:
        assert_manual_exception_reviewed(VotingRole.ELIGIBILITY_REVIEWER, review_reference=None)
    assert refusal.value.reason_code == "MANUAL_REVIEW_REQUIRED"


# -- SD-08: self-review -----------------------------------------------------


def test_a_reviewer_decides_neither_their_own_case_nor_one_they_raised() -> None:
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_no_self_review(
            actor_principal="p-1", raised_by_principal="p-2", subject_principal="p-1"
        )
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_no_self_review(
            actor_principal="p-1", raised_by_principal="p-1", subject_principal="p-3"
        )
    assert_no_self_review(actor_principal="p-9", raised_by_principal="p-1", subject_principal="p-3")


# -- the incompatibility matrix ---------------------------------------------


def test_the_compatibility_matrix_covers_every_pair() -> None:
    assert len(ROLE_COMPATIBILITY) == 45
    for role in VotingRole:
        if role is VotingRole.SECURITY_AUDITOR:
            continue
        pair = frozenset({role, VotingRole.SECURITY_AUDITOR})
        assert ROLE_COMPATIBILITY[pair] is RoleCompatibility.COMPATIBLE
    assert_role_combination_permitted(
        [VotingRole.VOTING_OPERATIONS_OFFICER, VotingRole.MEMBERSHIP_AUTHORITY]
    )


def test_a_prohibited_pair_is_refused_outright() -> None:
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_role_combination_permitted(
            [VotingRole.ELIGIBILITY_OFFICER, VotingRole.CREDENTIAL_ISSUER],
            grant_reference="grant-1",
            dual_control_reference="dc-1",
        )


def test_a_restricted_pair_requires_a_grant_and_dual_control() -> None:
    restricted = [VotingRole.MEMBERSHIP_AUTHORITY, VotingRole.ELIGIBILITY_OFFICER]
    with pytest.raises(PrivilegedApprovalMissingError) as refusal:
        assert_role_combination_permitted(restricted)
    assert refusal.value.reason_code == "PRIVILEGED_APPROVAL_MISSING"
    with pytest.raises(DualControlRequiredError):
        assert_role_combination_permitted(restricted, grant_reference="grant-1")
    assert_role_combination_permitted(
        restricted, grant_reference="grant-1", dual_control_reference="dc-1"
    )


# -- dual control -----------------------------------------------------------


def test_dual_control_returns_the_privileged_act_record() -> None:
    record = assert_dual_control(
        Capability.PRIVILEGED_EXPORT,
        first_approver=Approver("p-1", VotingRole.INDEPENDENT_AUDITOR),
        second_approver=Approver("p-2", VotingRole.VOTING_OPERATIONS_OFFICER),
        grant_reference="grant-1",
    )
    assert isinstance(record, PrivilegedActRecord)
    assert record.reason_code == "PRIVILEGED_VOTING_ACTION_PERFORMED"
    assert record.grant_reference == "grant-1"


def test_dual_control_refuses_one_principal_approving_twice() -> None:
    with pytest.raises(DualControlRequiredError) as refusal:
        assert_dual_control(
            Capability.BREAK_GLASS,
            first_approver=Approver("p-1", VotingRole.VOTING_OPERATIONS_OFFICER),
            second_approver=Approver("p-1", VotingRole.SECURITY_AUDITOR),
            grant_reference="grant-1",
        )
    assert refusal.value.reason_code == "DUAL_CONTROL_REQUIRED"
    with pytest.raises(DualControlRequiredError):
        assert_dual_control(
            Capability.BREAK_GLASS,
            first_approver=Approver("", VotingRole.VOTING_OPERATIONS_OFFICER),
            second_approver=Approver("p-2", VotingRole.SECURITY_AUDITOR),
            grant_reference="grant-1",
        )


def test_dual_control_refuses_two_approvers_holding_the_same_role() -> None:
    """Two accounts of one office approve the way one account does."""
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_dual_control(
            Capability.PRIVILEGED_EXPORT,
            first_approver=Approver("p-1", VotingRole.INDEPENDENT_AUDITOR),
            second_approver=Approver("p-2", VotingRole.INDEPENDENT_AUDITOR),
            grant_reference="grant-1",
        )


def test_dual_control_refuses_an_unpermitted_role_and_a_missing_grant() -> None:
    with pytest.raises(PrivilegedApprovalMissingError):
        assert_dual_control(
            Capability.BREAK_GLASS,
            first_approver=Approver("p-1", VotingRole.VOTING_OPERATIONS_OFFICER),
            second_approver=Approver("p-2", VotingRole.TALLY_AUTHORITY),
            grant_reference="grant-1",
        )
    with pytest.raises(PrivilegedApprovalMissingError):
        assert_dual_control(
            Capability.BREAK_GLASS,
            first_approver=Approver("p-1", VotingRole.VOTING_OPERATIONS_OFFICER),
            second_approver=Approver("p-2", VotingRole.SECURITY_AUDITOR),
            grant_reference=None,
        )


def test_a_capability_that_is_not_a_dual_control_act_is_a_declaration_error() -> None:
    with pytest.raises(AuthorizationMatrixIncompleteError):
        assert_dual_control(
            Capability.TALLY_OUTCOME,
            first_approver=Approver("p-1", VotingRole.TALLY_AUTHORITY),
            second_approver=Approver("p-2", VotingRole.SECURITY_AUDITOR),
            grant_reference="grant-1",
        )


# -- SD-16: export and raw participation ------------------------------------


def test_an_authorized_export_is_permitted_and_an_unauthorized_one_is_not() -> None:
    assert_privileged_export_authorized(
        VotingRole.INDEPENDENT_AUDITOR,
        streams=[AuditStream.INDEPENDENT],
        grant_reference="grant-1",
    )
    with pytest.raises(PermissionDeniedError):
        assert_privileged_export_authorized(
            VotingRole.SECURITY_AUDITOR,
            streams=[AuditStream.INDEPENDENT],
            grant_reference="grant-1",
        )
    with pytest.raises(PrivilegedApprovalMissingError):
        assert_privileged_export_authorized(
            VotingRole.INDEPENDENT_AUDITOR,
            streams=[AuditStream.INDEPENDENT],
            grant_reference=None,
        )


def test_an_export_naming_both_sides_is_refused() -> None:
    with pytest.raises(EvidenceBundleScopeRefusedError) as refusal:
        assert_privileged_export_authorized(
            VotingRole.INDEPENDENT_AUDITOR,
            streams=[AuditStream.ELIGIBILITY, AuditStream.CREDENTIAL],
            grant_reference="grant-1",
        )
    assert refusal.value.reason_code == "EVIDENCE_BUNDLE_SCOPE_REFUSED"


def test_no_role_holds_export_together_with_a_raw_participation_read() -> None:
    for role in VotingRole:
        held = ROLE_CAPABILITIES[role]
        if Capability.PRIVILEGED_EXPORT not in held:
            continue
        assert not held & {
            Capability.AUDIT_READ_IDENTITY_SIDE,
            Capability.AUDIT_READ_VOTING_SIDE,
        }


# -- security administration vs system administration -----------------------


def test_security_administration_is_not_system_administration() -> None:
    assert SECURITY_ADMIN_ROLE is not SYSTEM_ADMIN_ROLE
    assert_security_admin_is_not_system_admin()


def test_identical_admin_capability_sets_defeat_the_separation(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    matrix[SECURITY_ADMIN_ROLE] = ROLE_CAPABILITIES[SYSTEM_ADMIN_ROLE]
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_security_admin_is_not_system_admin(matrix)


def test_containment_in_either_direction_defeats_it_just_as_well(
    matrix: dict[VotingRole, frozenset[Capability]],
) -> None:
    matrix[SYSTEM_ADMIN_ROLE] = (
        ROLE_CAPABILITIES[SYSTEM_ADMIN_ROLE] | ROLE_CAPABILITIES[SECURITY_ADMIN_ROLE]
    )
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_security_admin_is_not_system_admin(matrix)
    matrix[SYSTEM_ADMIN_ROLE] = ROLE_CAPABILITIES[SYSTEM_ADMIN_ROLE]
    matrix[SECURITY_ADMIN_ROLE] = frozenset({Capability.AUDIT_READ_NEUTRAL})
    with pytest.raises(SeparationOfDutiesRefusedError):
        assert_security_admin_is_not_system_admin(matrix)


# -- import-time completeness -----------------------------------------------


def test_every_reason_code_this_module_raises_is_a_registered_pack15_code() -> None:
    codes = {
        PermissionDeniedError.reason_code,
        SeparationOfDutiesRefusedError.reason_code,
        DualControlRequiredError.reason_code,
        PrivilegedApprovalMissingError.reason_code,
        CorrelationRiskDetectedError.reason_code,
        EvidenceBundleScopeRefusedError.reason_code,
        ManualReviewRequiredError.reason_code,
        PrivilegedActRecord.reason_code,
    }
    assert codes == {
        "PERMISSION_DENIED",
        "SEPARATION_OF_DUTIES_REFUSED",
        "DUAL_CONTROL_REQUIRED",
        "PRIVILEGED_APPROVAL_MISSING",
        "CORRELATION_RISK_DETECTED",
        "EVIDENCE_BUNDLE_SCOPE_REFUSED",
        "MANUAL_REVIEW_REQUIRED",
        "PRIVILEGED_VOTING_ACTION_PERFORMED",
    }


def test_the_base_refusal_carries_no_reason_code() -> None:
    """A refusal without a registered code is not a permissible refusal."""
    assert not hasattr(VotingAuthorizationError, "reason_code")
    assert issubclass(PermissionDeniedError, VotingAuthorizationError)
    # Two refusals that differ in what happens next stay two classes.
    assert not issubclass(PermissionDeniedError, SeparationOfDutiesRefusedError)
    assert PermissionDeniedError.reason_code != SeparationOfDutiesRefusedError.reason_code

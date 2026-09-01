"""Role separation (`P12-ROLE-*`, FIR-INV-008, FIR-INV-014, ADR-061)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from _privileged_builders import StubAuthorizationPort, authority

from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
)
from epd2_privileged_access_service.exceptions import (
    AssignmentNotGovernedError,
    AuthorityRoleIncompatibleError,
    InstitutionalAuthorityNotExtendableError,
    PrivilegeAuthorityMissingError,
    PrivilegeOrganizationMismatchError,
    RoleCombinationProhibitedError,
    SelfApprovalProhibitedError,
)
from epd2_privileged_access_service.roles import (
    ADDED_INCOMPATIBLE_PAIRS,
    INSTITUTIONAL_ROLE_CODES,
    NO_BYPASS_NOTE,
    OPERATIONAL_ASSIGNMENT_CODES,
    PAIRWISE_INCOMPATIBLE_ROLES,
    PRESERVED_INSTITUTIONAL_PAIRS,
    InstitutionalRole,
    OperationalAssignment,
    OperationalAssignmentRole,
    assert_assignment_does_not_extend_institutional,
    assert_authorized,
    assert_distinct_reviewer,
    assert_no_institutional_escalation,
    assert_not_self_approval,
    assert_roles_compatible,
    incompatible_with,
    is_institutional,
    is_operational_assignment,
    required_roles_for_purpose,
    resolve_privileged_role,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


class TestRoleInventory:
    def test_two_institutional_roles_are_consumed_not_defined(self) -> None:
        """PACK-12 adds no canonically-named institutional office
        (`P12-ROLE-014`). System and security administrator are the
        Architecture Framework's, referenced here."""
        assert (
            frozenset({"system_administrator", "security_administrator"})
            == INSTITUTIONAL_ROLE_CODES
        )

    def test_nine_operational_assignments_are_introduced(self) -> None:
        assert len(OPERATIONAL_ASSIGNMENT_CODES) == 9

    def test_the_two_sets_do_not_overlap(self) -> None:
        assert not (INSTITUTIONAL_ROLE_CODES & OPERATIONAL_ASSIGNMENT_CODES)

    def test_classification_helpers_agree_with_the_sets(self) -> None:
        assert is_institutional("security_administrator")
        assert is_operational_assignment("data_owner")
        assert resolve_privileged_role("finance_auditor") is None


class TestIncompatibilityMatrix:
    def test_pack08_baseline_is_preserved_not_replaced(self) -> None:
        """Canon 19e.16 permits a stricter baseline and forbids a relaxed
        one. The preserved pairs must remain in the effective matrix."""
        assert PRESERVED_INSTITUTIONAL_PAIRS <= PAIRWISE_INCOMPATIBLE_ROLES

    def test_pack12_additions_are_additive(self) -> None:
        assert ADDED_INCOMPATIBLE_PAIRS <= PAIRWISE_INCOMPATIBLE_ROLES
        assert PAIRWISE_INCOMPATIBLE_ROLES == (
            PRESERVED_INSTITUTIONAL_PAIRS | ADDED_INCOMPATIBLE_PAIRS
        )

    def test_the_rule_setter_may_not_also_be_the_operator(self) -> None:
        """FIR-INV-008, role pair 1."""
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible({"security_administrator", "system_administrator"})

    def test_the_reviewer_holds_no_operational_privilege_in_scope(self) -> None:
        """Role pair 15."""
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible(
                {"independent_privileged_access_reviewer", "domain_administrator"}
            )

    def test_assessment_may_not_decide_what_it_assessed(self) -> None:
        """Role pair 10."""
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible({"dlp_security_officer", "export_approver"})

    def test_a_compatible_pair_passes(self) -> None:
        assert_roles_compatible({"data_owner", "audit_custodian"})

    def test_incompatible_with_is_symmetric(self) -> None:
        assert "system_administrator" in incompatible_with("security_administrator")
        assert "security_administrator" in incompatible_with("system_administrator")

    def test_no_role_set_spans_every_domain(self) -> None:
        """FIR-INV-014: there is no combination that is a universal
        administrator. Asserted by construction - holding all privileged
        roles at once is refused."""
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible(INSTITUTIONAL_ROLE_CODES | OPERATIONAL_ASSIGNMENT_CODES)


class TestInstitutionalEscalation:
    def test_an_operational_assignment_may_not_widen_an_office(self) -> None:
        """`P12-ROLE-019`."""
        with pytest.raises(RoleCombinationProhibitedError):
            assert_no_institutional_escalation({"iam_administrator", "domain_administrator"})

    def test_an_operational_assignment_confers_no_institutional_standing(self) -> None:
        with pytest.raises(InstitutionalAuthorityNotExtendableError):
            assert_assignment_does_not_extend_institutional(
                "iam_administrator", "security_administrator"
            )

    def test_an_ordinary_operational_set_passes(self) -> None:
        assert_no_institutional_escalation({"data_owner"})


class TestSelfApproval:
    def test_the_same_subject_may_not_occupy_both_ends(self) -> None:
        with pytest.raises(SelfApprovalProhibitedError):
            assert_not_self_approval("actor:a", "actor:a", action="approve")

    def test_distinct_subjects_pass(self) -> None:
        assert_not_self_approval("actor:a", "actor:b", action="approve")

    def test_empty_references_do_not_silently_match(self) -> None:
        assert_not_self_approval("", "", action="approve")

    def test_the_break_glass_reviewer_is_neither_party(self) -> None:
        with pytest.raises(SelfApprovalProhibitedError):
            assert_distinct_reviewer("actor:a", activator="actor:a", approver="actor:b")
        with pytest.raises(SelfApprovalProhibitedError):
            assert_distinct_reviewer("actor:b", activator="actor:a", approver="actor:b")
        assert_distinct_reviewer("actor:c", activator="actor:a", approver="actor:b")


class TestAuthorization:
    def test_a_role_code_string_is_never_proof(self) -> None:
        """`P12-ROLE-017`: the presented authority is resolved through the
        port. An unresolvable assignment denies even though the string
        matches."""
        scope = OrganizationalScopeRef(organization_id=uuid4())
        presented = authority("data_owner", scope, "actor:a")
        port = StubAuthorizationPort(inactive=frozenset({presented.authority_id}))
        with pytest.raises(PrivilegeAuthorityMissingError):
            assert_authorized(frozenset({"data_owner"}), (presented,), scope, at=T0, port=port)

    def test_an_empty_requirement_set_denies(self) -> None:
        scope = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(PrivilegeAuthorityMissingError):
            assert_authorized(frozenset(), (), scope, at=T0, port=StubAuthorizationPort())

    def test_a_foreign_scope_authority_is_refused(self) -> None:
        scope = OrganizationalScopeRef(organization_id=uuid4())
        other = OrganizationalScopeRef(organization_id=uuid4())
        with pytest.raises(PrivilegeOrganizationMismatchError):
            assert_authorized(
                frozenset({"data_owner"}),
                (authority("data_owner", other, "actor:a"),),
                scope,
                at=T0,
                port=StubAuthorizationPort(),
            )

    def test_held_roles_are_rechecked_at_the_act(self) -> None:
        scope = OrganizationalScopeRef(organization_id=uuid4())
        port = StubAuthorizationPort(held={"actor:a": frozenset({"export_approver"})})
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_authorized(
                frozenset({"dlp_security_officer"}),
                (authority("dlp_security_officer", scope, "actor:a"),),
                scope,
                at=T0,
                port=port,
            )

    def test_a_resolvable_authority_is_returned(self) -> None:
        scope = OrganizationalScopeRef(organization_id=uuid4())
        presented = authority("data_owner", scope, "actor:a")
        resolved = assert_authorized(
            frozenset({"data_owner"}),
            (presented,),
            scope,
            at=T0,
            port=StubAuthorizationPort(),
        )
        assert resolved is presented


class TestPurposeRoleTable:
    def test_an_unserved_purpose_denies_rather_than_defaulting_open(self) -> None:
        for purpose in Purpose:
            roles = required_roles_for_purpose(purpose)
            assert roles <= (INSTITUTIONAL_ROLE_CODES | OPERATIONAL_ASSIGNMENT_CODES)

    def test_system_administration_is_the_institutional_office_only(self) -> None:
        assert required_roles_for_purpose(Purpose.SYSTEM_ADMINISTRATION) == frozenset(
            {InstitutionalRole.SYSTEM_ADMINISTRATOR.value}
        )


class TestOperationalAssignment:
    def _assignment(self, **overrides: object) -> OperationalAssignment:
        scope = OrganizationalScopeRef(organization_id=uuid4())
        from epd2_privileged_access_service.domain import EffectiveWindow

        base: dict[str, object] = {
            "assignment_id": uuid4(),
            "role": OperationalAssignmentRole.DATA_OWNER,
            "subject_reference": "actor:a",
            "authority": authority("data_owner", scope, "actor:a"),
            "organization_scope": scope,
            "domain_scope": "membership",
            "permitted_operations": frozenset({"read"}),
            "purpose": PurposeBinding(purpose=Purpose.OPERATIONS, justification_reference="j"),
            "window": EffectiveWindow(valid_from=T0, valid_until=T0 + timedelta(hours=2)),
            "granted_by": "actor:b",
            "approved_by": "actor:c",
        }
        base.update(overrides)
        return OperationalAssignment(**base)  # type: ignore[arg-type]

    def test_requires_at_least_one_operation(self) -> None:
        with pytest.raises(AssignmentNotGovernedError):
            self._assignment(permitted_operations=frozenset())

    def test_may_not_be_self_granted_and_self_approved(self) -> None:
        with pytest.raises(SelfApprovalProhibitedError):
            self._assignment(granted_by="actor:a", approved_by="actor:a")

    def test_is_effective_only_inside_its_window_and_while_active(self) -> None:
        assignment = self._assignment()
        assert assignment.is_effective_at(T0)
        assert not assignment.is_effective_at(T0 + timedelta(hours=3))


class TestNoBypass:
    def test_the_note_is_present_and_explicit(self) -> None:
        """FIR-INV-006 is a structural claim; the note is what a reader
        finds when they look for the flag that does not exist."""
        assert "no feature flag" in NO_BYPASS_NOTE
        assert "bypass" in NO_BYPASS_NOTE

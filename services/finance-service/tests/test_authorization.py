"""Tests for `epd2_finance_service.authorization` - the canon 19f.14
incompatibility matrix, the action-authority table, the conflict
declaration, self-approval and auditor independence.

Nothing here is conditional on a flag: `test_no_function_in_the_package
_accepts_a_bypass_flag_parameter` proves the whole package offers no
parameter that could switch a check off (`ФИН-42`).
"""

from __future__ import annotations

import ast
import pathlib
from uuid import UUID, uuid4

import pytest

import epd2_finance_service
from epd2_finance_service.authorization import (
    ACTION_REQUIREMENTS,
    AUDITOR_INCOMPATIBLE_ROLES,
    INCOMPATIBLE_ROLE_PAIRS,
    NO_BREAK_GLASS_NOTE,
    PARTY_HANDLE_RESOLUTION_ROLE_CODE,
    FinanceActionAuthority,
    FinanceRole,
    assert_auditor_independent,
    assert_authorized,
    assert_conflict_declared,
    assert_not_self_approval,
    assert_roles_compatible,
    incompatible_roles_for,
    resolve_finance_role,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    OrganizationalScopeRef,
)
from epd2_finance_service.exceptions import (
    AuditorIndependenceViolationError,
    AuthorityRoleIncompatibleError,
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    FinanceAuthorityMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    SelfApprovalProhibitedError,
)

#: Parameter names that would amount to a switch able to turn a finance
#: check off. `ФИН-42`: a separation of duties a flag can disable was never
#: in force, so none of these may exist anywhere in the package.
BYPASS_PARAMETER_NAMES: frozenset[str] = frozenset(
    {
        "force",
        "forced",
        "bypass",
        "break_glass",
        "emergency",
        "override",
        "unsafe",
        "skip",
        "skip_checks",
        "skip_validation",
        "ignore_checks",
        "disable_checks",
        "feature_flag",
        "allow_unauthorized",
        "privileged",
    }
)

#: The canon 19f.14 hard role pairs, written out here rather than read off
#: the module, so a silent softening of `INCOMPATIBLE_ROLE_PAIRS` fails a
#: test instead of quietly passing one.
CANON_INCOMPATIBLE_PAIRS: tuple[tuple[FinanceRole, FinanceRole], ...] = (
    (FinanceRole.FINANCE_AUDITOR, FinanceRole.FINANCE_ADMINISTRATOR),
    (FinanceRole.FINANCE_AUDITOR, FinanceRole.PAYMENT_AUTHORIZER),
    (FinanceRole.FINANCE_AUDITOR, FinanceRole.PAYMENT_EXECUTOR),
    (FinanceRole.FINANCE_AUDITOR, FinanceRole.REPORT_SIGNATORY),
    (FinanceRole.PAYMENT_AUTHORIZER, FinanceRole.PAYMENT_EXECUTOR),
    (FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.ORGANIZATIONAL_ADMINISTRATOR),
)


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _authority(
    role_code: str, *, scope: OrganizationalScopeRef, actor: str = ""
) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(), role_code=role_code, scope=scope, actor_reference=actor
    )


class _Port:
    """Test double for `authorization.AuthorizationPort`.

    `active` is the set of authority ids PACK-08 would answer for; `held`
    is what each opaque actor reference actually holds in the scope. Both
    are explicit per test, because "the port answered yes" is the fact
    every authority check in this module depends on."""

    def __init__(
        self,
        *,
        active: frozenset[UUID] = frozenset(),
        held: dict[str, frozenset[FinanceRole]] | None = None,
    ) -> None:
        self.active = active
        self.held = {} if held is None else held

    def resolve_active_authority(
        self, authority: AuthorityReference, scope: OrganizationalScopeRef
    ) -> bool:
        return (
            authority.authority_id in self.active
            and authority.scope.organization_id == scope.organization_id
        )

    def held_roles(
        self, actor_reference: str, scope: OrganizationalScopeRef
    ) -> frozenset[FinanceRole]:
        return self.held.get(actor_reference, frozenset())


def _finance_package_functions() -> list[tuple[str, str, str]]:
    """Every `(module, function, parameter)` triple in the package."""
    package_root = pathlib.Path(epd2_finance_service.__file__).parent
    triples: list[tuple[str, str, str]] = []
    for path in sorted(package_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            arguments = node.args
            named = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
            if arguments.vararg is not None:
                named.append(arguments.vararg)
            if arguments.kwarg is not None:
                named.append(arguments.kwarg)
            triples.extend((path.name, node.name, argument.arg) for argument in named)
    return triples


# =============================================================================
# The incompatibility matrix (canon 19f.14, `ФИН-30`)
# =============================================================================


def test_the_matrix_in_the_module_is_exactly_the_canon_matrix() -> None:
    assert (
        frozenset(frozenset(pair) for pair in CANON_INCOMPATIBLE_PAIRS) == INCOMPATIBLE_ROLE_PAIRS
    )


@pytest.mark.parametrize(("first", "second"), CANON_INCOMPATIBLE_PAIRS)
def test_the_incompatibility_matrix_refuses_each_canon_listed_pair(
    first: FinanceRole, second: FinanceRole
) -> None:
    with pytest.raises(AuthorityRoleIncompatibleError) as excinfo:
        assert_roles_compatible({first, second})
    assert excinfo.value.reason_code == "AUTHORITY_ROLE_INCOMPATIBLE"


def test_a_single_role_and_a_compatible_pair_are_permitted() -> None:
    assert_roles_compatible({FinanceRole.FINANCE_AUDITOR})
    assert_roles_compatible({FinanceRole.PAYMENT_AUTHORIZER, FinanceRole.REPORT_SIGNATORY})


def test_the_incompatible_set_for_a_role_is_derived_from_the_matrix() -> None:
    assert incompatible_roles_for(FinanceRole.FINANCE_AUDITOR) == frozenset(
        {
            FinanceRole.FINANCE_ADMINISTRATOR,
            FinanceRole.PAYMENT_AUTHORIZER,
            FinanceRole.PAYMENT_EXECUTOR,
            FinanceRole.REPORT_SIGNATORY,
        }
    )
    assert incompatible_roles_for(FinanceRole.FINANCE_AUDITOR) == AUDITOR_INCOMPATIBLE_ROLES


def test_authorising_and_executing_a_payment_are_never_one_role() -> None:
    authorize = ACTION_REQUIREMENTS["authorize_payment"]
    execute = ACTION_REQUIREMENTS["execute_payment"]
    assert authorize == frozenset({FinanceRole.PAYMENT_AUTHORIZER})
    assert execute == frozenset({FinanceRole.PAYMENT_EXECUTOR})
    assert not authorize & execute


def test_the_four_action_level_authorities_are_never_institutional_roles() -> None:
    action_names = {str(authority) for authority in FinanceActionAuthority}
    assert action_names == {
        "transaction_creator",
        "transaction_reviewer",
        "report_preparer",
        "report_approver",
    }
    granted = {str(role) for roles in ACTION_REQUIREMENTS.values() for role in roles}
    assert not action_names & granted


def test_the_auditor_may_perform_exactly_one_action_in_the_table() -> None:
    auditor_actions = {
        action
        for action, roles in ACTION_REQUIREMENTS.items()
        if FinanceRole.FINANCE_AUDITOR in roles
    }
    assert auditor_actions == {"record_audit_opinion"}


# =============================================================================
# A role name is not an authority (`ФИН-45`, `ФИН-41`)
# =============================================================================


def test_a_role_name_alone_is_not_proof_of_authority() -> None:
    scope = _scope()
    presented = _authority("finance_administrator", scope=scope, actor="actor-a")
    with pytest.raises(FinanceAuthorityMissingError) as excinfo:
        assert_authorized("post_transaction", (presented,), scope, port=_Port())
    assert excinfo.value.reason_code == "FINANCE_AUTHORITY_MISSING"


def test_an_unresolvable_authority_refuses_with_the_authority_missing_code() -> None:
    scope = _scope()
    invented = _authority("finance_administrator", scope=scope, actor="actor-a")
    port = _Port(active=frozenset({uuid4()}))
    with pytest.raises(FinanceAuthorityMissingError) as excinfo:
        assert_authorized("post_transaction", (invented,), scope, port=port)
    assert excinfo.value.reason_code == "FINANCE_AUTHORITY_MISSING"


def test_a_resolved_authority_is_returned_so_the_act_can_record_which_one_acted() -> None:
    scope = _scope()
    presented = _authority("finance_administrator", scope=scope, actor="actor-a")
    port = _Port(
        active=frozenset({presented.authority_id}),
        held={"actor-a": frozenset({FinanceRole.FINANCE_ADMINISTRATOR})},
    )
    assert assert_authorized("post_transaction", (presented,), scope, port=port) is presented


def test_an_unknown_role_code_resolves_to_no_finance_role_and_therefore_denies() -> None:
    assert resolve_finance_role("universal_administrator") is None
    assert resolve_finance_role(PARTY_HANDLE_RESOLUTION_ROLE_CODE) is None
    scope = _scope()
    presented = _authority(PARTY_HANDLE_RESOLUTION_ROLE_CODE, scope=scope, actor="actor-a")
    port = _Port(active=frozenset({presented.authority_id}))
    with pytest.raises(FinanceAuthorityMissingError):
        assert_authorized("post_transaction", (presented,), scope, port=port)


def test_an_action_absent_from_the_requirements_table_denies_rather_than_defaulting_open() -> None:
    scope = _scope()
    presented = _authority("finance_administrator", scope=scope, actor="actor-a")
    port = _Port(active=frozenset({presented.authority_id}))
    with pytest.raises(FinanceAuthorityMissingError):
        assert_authorized("invent_a_new_command", (presented,), scope, port=port)


def test_resolving_a_party_handle_is_not_a_grantable_finance_action() -> None:
    assert "resolve_party_handle" not in ACTION_REQUIREMENTS
    assert PARTY_HANDLE_RESOLUTION_ROLE_CODE not in {str(role) for role in FinanceRole}


def test_an_act_with_no_presented_authority_at_all_refuses() -> None:
    with pytest.raises(FinanceAuthorityMissingError):
        assert_authorized("post_transaction", (), _scope(), port=_Port())


# =============================================================================
# Scope (`ФИН-03`, `ФИН-04`, `ФИН-37`)
# =============================================================================


def test_an_undetermined_organizational_scope_denies_before_any_other_check() -> None:
    presented = _authority("finance_administrator", scope=_scope(), actor="actor-a")
    with pytest.raises(OrganizationScopeUndeterminedError) as excinfo:
        assert_authorized("post_transaction", (presented,), None, port=_Port())
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_UNDETERMINED"


def test_an_authority_scoped_to_another_organization_may_not_act_in_this_one() -> None:
    here, elsewhere = _scope(), _scope()
    presented = _authority("finance_administrator", scope=elsewhere, actor="actor-a")
    port = _Port(active=frozenset({presented.authority_id}))
    with pytest.raises(OrganizationScopeMismatchError) as excinfo:
        assert_authorized("post_transaction", (presented,), here, port=port)
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_MISMATCH"


def test_holding_something_elsewhere_is_a_different_refusal_from_holding_nothing() -> None:
    here, elsewhere = _scope(), _scope()
    foreign = _authority("finance_administrator", scope=elsewhere, actor="actor-a")
    local_wrong_role = _authority("report_signatory", scope=here, actor="actor-b")
    port = _Port(active=frozenset({foreign.authority_id, local_wrong_role.authority_id}))
    with pytest.raises(OrganizationScopeMismatchError):
        assert_authorized("post_transaction", (foreign,), here, port=port)
    with pytest.raises(FinanceAuthorityMissingError):
        assert_authorized("post_transaction", (local_wrong_role,), here, port=port)


# =============================================================================
# The act-time incompatibility re-check (canon 19f.14 second pass)
# =============================================================================


def test_the_matrix_is_re_checked_at_the_moment_of_the_act() -> None:
    scope = _scope()
    presented = _authority("finance_administrator", scope=scope, actor="actor-a")
    port = _Port(
        active=frozenset({presented.authority_id}),
        held={
            "actor-a": frozenset({FinanceRole.FINANCE_ADMINISTRATOR, FinanceRole.FINANCE_AUDITOR})
        },
    )
    with pytest.raises(AuthorityRoleIncompatibleError):
        assert_authorized("post_transaction", (presented,), scope, port=port)


# =============================================================================
# Self-approval (`ФИН-31`)
# =============================================================================


def test_the_same_actor_may_not_act_on_its_own_earlier_act() -> None:
    with pytest.raises(SelfApprovalProhibitedError) as excinfo:
        assert_not_self_approval("actor-a", "actor-a", action="report approval")
    assert excinfo.value.reason_code == "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"


def test_a_different_actor_may_act_on_an_earlier_act() -> None:
    assert_not_self_approval("actor-a", "actor-b", action="report approval")


def test_a_blank_actor_reference_neither_passes_nor_fails_the_self_approval_check() -> None:
    assert_not_self_approval("", "actor-a", action="report approval")
    assert_not_self_approval("actor-a", "  ", action="report approval")


# =============================================================================
# Conflict of interest (`ФИН-32`)
# =============================================================================


def test_an_undeclared_conflict_fails_closed() -> None:
    undeclared = ConflictDeclaration(state=ConflictDeclaration.UNDECLARED, declared_by="board")
    with pytest.raises(ConflictOfInterestUndeclaredError) as excinfo:
        assert_conflict_declared(undeclared, action="contribution acceptance")
    assert excinfo.value.reason_code == "CONFLICT_OF_INTEREST_UNDECLARED"


def test_a_missing_conflict_declaration_is_the_same_answer_as_undeclared() -> None:
    with pytest.raises(ConflictOfInterestUndeclaredError):
        assert_conflict_declared(None, action="contribution acceptance")


def test_a_declared_blocking_conflict_refuses_with_its_own_code() -> None:
    blocking = ConflictDeclaration(state=ConflictDeclaration.BLOCKING, declared_by="board")
    with pytest.raises(ConflictOfInterestBlockingError) as excinfo:
        assert_conflict_declared(blocking, action="payment authorization")
    assert excinfo.value.reason_code == "CONFLICT_OF_INTEREST_BLOCKING"


def test_declared_none_and_declared_non_blocking_both_pass() -> None:
    assert_conflict_declared(
        ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board"), action="act"
    )
    assert_conflict_declared(
        ConflictDeclaration(state=ConflictDeclaration.DECLARED_NON_BLOCKING, declared_by="board"),
        action="act",
    )


# =============================================================================
# Auditor independence (`ФИН-29`, `ФИН-30`)
# =============================================================================


def test_an_independent_auditor_passes_every_check() -> None:
    scope = _scope()
    auditor = _authority("finance_auditor", scope=scope, actor="actor-auditor")
    port = _Port(held={"actor-auditor": frozenset({FinanceRole.FINANCE_AUDITOR})})
    assert_auditor_independent(auditor, ("actor-admin", "actor-signatory"), scope, port=port)


def test_the_auditor_fails_the_independence_check_against_a_preparer_or_approver() -> None:
    scope = _scope()
    auditor = _authority("finance_auditor", scope=scope, actor="actor-auditor")
    with pytest.raises(AuditorIndependenceViolationError) as excinfo:
        assert_auditor_independent(auditor, ("actor-admin", "actor-auditor"), scope)
    assert excinfo.value.reason_code == "FINANCE_AUDITOR_INDEPENDENCE_VIOLATION"


def test_an_auditor_who_also_administers_the_audited_scope_is_refused() -> None:
    scope = _scope()
    auditor = _authority("finance_auditor", scope=scope, actor="actor-auditor")
    port = _Port(
        held={
            "actor-auditor": frozenset(
                {FinanceRole.FINANCE_AUDITOR, FinanceRole.FINANCE_ADMINISTRATOR}
            )
        }
    )
    with pytest.raises(AuditorIndependenceViolationError):
        assert_auditor_independent(auditor, (), scope, port=port)


def test_an_engagement_requires_the_auditor_role_and_not_merely_some_authority() -> None:
    scope = _scope()
    administrator = _authority("finance_administrator", scope=scope, actor="actor-admin")
    with pytest.raises(AuditorIndependenceViolationError):
        assert_auditor_independent(administrator, (), scope)


def test_a_foreign_scoped_auditor_keeps_the_scope_refusal_rather_than_the_independence_one() -> (
    None
):
    auditor = _authority("finance_auditor", scope=_scope(), actor="actor-auditor")
    with pytest.raises(OrganizationScopeMismatchError):
        assert_auditor_independent(auditor, (), _scope())


# =============================================================================
# No break-glass (`ФИН-42`)
# =============================================================================


def test_no_function_in_the_package_accepts_a_bypass_flag_parameter() -> None:
    offending = [
        (module, function, parameter)
        for module, function, parameter in _finance_package_functions()
        if parameter.lower() in BYPASS_PARAMETER_NAMES
    ]
    assert offending == []


def test_the_no_break_glass_rule_is_recorded_as_a_quotable_module_constant() -> None:
    assert "FIN-42" in NO_BREAK_GLASS_NOTE
    assert "emergency" in NO_BREAK_GLASS_NOTE

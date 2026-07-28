"""Scoped authorization, the incompatibility matrix and separation of
duties (FIR-INV-006, FIR-INV-013, FIR-INV-014).
"""

from __future__ import annotations

import pytest
from _builders import FakeAuthorizationPort, authority, scope

from epd2_document_service.authorization import (
    ACTION_REQUIREMENTS,
    NO_BREAK_GLASS_NOTE,
    AuthorizationPort,
    DocumentAction,
    DocumentRole,
    assert_access_permitted,
    assert_authorized,
    assert_not_self_approval,
    assert_reader_independent,
    assert_reviewer_qualified,
    assert_roles_compatible,
    assert_scope_determined,
    incompatible_roles_for,
    resolve_document_role,
)
from epd2_document_service.domain import (
    AccessProfile,
    AuthorityReference,
    DocumentKind,
    SensitivityClass,
)
from epd2_document_service.exceptions import (
    AuditorIndependenceViolationError,
    AuthorityRoleIncompatibleError,
    DocumentAuthorityMissingError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    RestrictedAccessDeniedError,
    SelfApprovalProhibitedError,
)

# ---------------------------------------------------------------------------
# The table itself
# ---------------------------------------------------------------------------


def test_every_action_has_a_requirement_entry() -> None:
    """An action absent from the table denies, which is the safe default -
    but it is also a bug, because it means a command can never be
    performed. This test is what keeps the enum and the table together."""
    missing = [a.value for a in DocumentAction if a not in ACTION_REQUIREMENTS]
    assert missing == []


def test_every_requirement_names_at_least_one_role() -> None:
    empty = [a.value for a, roles in ACTION_REQUIREMENTS.items() if not roles]
    assert empty == []


def test_approval_accepts_only_the_approver_role() -> None:
    """Every widening of who may approve is a narrowing of what approval
    means."""
    assert ACTION_REQUIREMENTS[DocumentAction.APPROVE_VERSION] == frozenset(
        {DocumentRole.DOCUMENT_APPROVER}
    )


def test_publication_accepts_only_the_publication_officer() -> None:
    for action in (
        DocumentAction.AUTHORIZE_PUBLICATION,
        DocumentAction.PUBLISH_VERSION,
        DocumentAction.ISSUE_PUBLICATION_RENDITION,
    ):
        assert ACTION_REQUIREMENTS[action] == frozenset({DocumentRole.PUBLICATION_OFFICER})


def test_admissibility_is_a_legal_determination_only() -> None:
    assert ACTION_REQUIREMENTS[DocumentAction.DETERMINE_ADMISSIBILITY] == frozenset(
        {DocumentRole.LEGAL_REVIEWER}
    )


def test_the_fake_port_satisfies_the_real_protocol() -> None:
    """Guards against the test double drifting from the interface it
    stands in for."""
    port: AuthorizationPort = FakeAuthorizationPort()
    assert callable(port.resolve_active_authority)
    assert callable(port.held_roles)


def test_the_no_break_glass_rule_is_stated_as_a_quotable_constant() -> None:
    assert "FIR-INV-006" in NO_BREAK_GLASS_NOTE
    assert "flag" in NO_BREAK_GLASS_NOTE


# ---------------------------------------------------------------------------
# Role resolution
# ---------------------------------------------------------------------------


def test_a_foreign_role_code_resolves_to_none_rather_than_raising() -> None:
    """A caller may legitimately hold roles from other contexts; treating
    a finance authority as an attack would be wrong."""
    assert resolve_document_role("finance_administrator") is None
    assert resolve_document_role("document_approver") is DocumentRole.DOCUMENT_APPROVER


# ---------------------------------------------------------------------------
# The incompatibility matrix
# ---------------------------------------------------------------------------


def test_the_matrix_is_symmetric() -> None:
    """An asymmetric incompatibility is a bug that only appears when the
    roles are granted in the other order."""
    for role in DocumentRole:
        for other in incompatible_roles_for(role):
            assert role in incompatible_roles_for(other), f"{role} / {other} asymmetric"


def test_no_role_is_incompatible_with_itself() -> None:
    for role in DocumentRole:
        assert role not in incompatible_roles_for(role)


def test_the_three_eyes_roles_are_mutually_incompatible() -> None:
    for pair in (
        (DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_REVIEWER),
        (DocumentRole.DOCUMENT_AUTHOR, DocumentRole.DOCUMENT_APPROVER),
        (DocumentRole.DOCUMENT_REVIEWER, DocumentRole.DOCUMENT_APPROVER),
    ):
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible(pair)


def test_an_author_may_not_also_publish() -> None:
    """An author who can publish needs neither review nor approval to
    reach the public."""
    with pytest.raises(AuthorityRoleIncompatibleError):
        assert_roles_compatible(
            (DocumentRole.DOCUMENT_AUTHOR, DocumentRole.PUBLICATION_OFFICER)
        )


def test_an_independent_reader_may_hold_no_operational_role() -> None:
    """Independence is not a permission level; it is the absence of a
    stake in the material."""
    operational = set(DocumentRole) - {DocumentRole.INDEPENDENT_READER}
    for role in operational:
        with pytest.raises(AuthorityRoleIncompatibleError):
            assert_roles_compatible((DocumentRole.INDEPENDENT_READER, role))


def test_a_custodian_may_also_author() -> None:
    """Custody is administrative; separating it from authorship would make
    ordinary record-keeping need two people for no governance gain."""
    assert_roles_compatible((DocumentRole.DOCUMENT_CUSTODIAN, DocumentRole.DOCUMENT_AUTHOR))


def test_a_compatible_set_passes() -> None:
    assert_roles_compatible(
        (DocumentRole.DOCUMENT_APPROVER, DocumentRole.DOCUMENT_CUSTODIAN)
    )


# ---------------------------------------------------------------------------
# assert_authorized
# ---------------------------------------------------------------------------


def test_an_authority_in_another_scope_is_not_considered() -> None:
    """Scope is never inherited into authority: a Bund-level assignment
    does not carry into a Kreis."""
    port = FakeAuthorizationPort()
    here, elsewhere = scope(), scope()
    foreign = authority(DocumentRole.DOCUMENT_APPROVER, elsewhere, port)
    with pytest.raises(DocumentAuthorityMissingError):
        assert_authorized(DocumentAction.APPROVE_VERSION, (foreign,), here, port=port)


def test_a_role_code_alone_proves_nothing() -> None:
    """The presented authority must resolve to a live assignment. A
    fabricated `role_code` fails exactly here."""
    port = FakeAuthorizationPort()
    here = scope()
    fabricated = AuthorityReference(
        authority_id=authority(DocumentRole.DOCUMENT_APPROVER, here, port).authority_id,
        role_code="document_approver",
        scope=here,
        actor_reference="actor-x",
    )
    port.deny_all = True
    with pytest.raises(DocumentAuthorityMissingError):
        assert_authorized(DocumentAction.APPROVE_VERSION, (fabricated,), here, port=port)


def test_a_wrong_role_for_the_action_is_refused() -> None:
    port = FakeAuthorizationPort()
    here = scope()
    reviewer = authority(DocumentRole.DOCUMENT_REVIEWER, here, port)
    with pytest.raises(DocumentAuthorityMissingError):
        assert_authorized(DocumentAction.APPROVE_VERSION, (reviewer,), here, port=port)


def test_the_matrix_is_re_checked_at_the_moment_of_the_act() -> None:
    """The case PACK-08's assignment-time check cannot catch.

    The presented authority names one legal role. The actor has *since*
    acquired a conflicting one, and only an act-time re-check over the
    roles actually held sees it."""
    port = FakeAuthorizationPort()
    here = scope()
    approver = authority(
        DocumentRole.DOCUMENT_APPROVER,
        here,
        port,
        actor_reference="actor-both",
        also_holds=(DocumentRole.DOCUMENT_AUTHOR,),
    )
    with pytest.raises(AuthorityRoleIncompatibleError):
        assert_authorized(DocumentAction.APPROVE_VERSION, (approver,), here, port=port)


def test_a_correct_authority_is_returned() -> None:
    port = FakeAuthorizationPort()
    here = scope()
    approver = authority(DocumentRole.DOCUMENT_APPROVER, here, port)
    assert (
        assert_authorized(DocumentAction.APPROVE_VERSION, (approver,), here, port=port) is approver
    )


def test_no_presented_authority_at_all_denies() -> None:
    port = FakeAuthorizationPort()
    with pytest.raises(DocumentAuthorityMissingError):
        assert_authorized(DocumentAction.APPROVE_VERSION, (), scope(), port=port)


# ---------------------------------------------------------------------------
# Separation of duties per act
# ---------------------------------------------------------------------------


def test_the_same_actor_may_not_perform_both_acts() -> None:
    with pytest.raises(SelfApprovalProhibitedError):
        assert_not_self_approval("actor-a", "actor-a", action="approve_version")


def test_different_actors_pass() -> None:
    assert_not_self_approval("actor-a", "actor-b", action="approve_version")


def test_an_unrecorded_prior_actor_is_refused_not_assumed() -> None:
    """"Cannot be shown to be a different person" must not be read as
    "is". An act whose prior actor was not recorded fails closed."""
    for acting, prior in (("actor-a", ""), ("", "actor-b"), ("", "")):
        with pytest.raises(SelfApprovalProhibitedError):
            assert_not_self_approval(acting, prior, action="approve_version")


# ---------------------------------------------------------------------------
# Qualified review
# ---------------------------------------------------------------------------


def test_a_legal_opinion_requires_a_legal_reviewer() -> None:
    """FIR-PROG-002's foundation: a general reviewer signing off a legal
    opinion would put a qualification claim on a review nobody qualified
    made."""
    for kind in (DocumentKind.LEGAL_OPINION, DocumentKind.EXPERT_OPINION):
        with pytest.raises(DocumentAuthorityMissingError):
            assert_reviewer_qualified(kind, DocumentRole.DOCUMENT_REVIEWER)
        assert_reviewer_qualified(kind, DocumentRole.LEGAL_REVIEWER)


def test_an_ordinary_document_accepts_an_ordinary_reviewer() -> None:
    assert_reviewer_qualified(DocumentKind.MEETING_MINUTES, DocumentRole.DOCUMENT_REVIEWER)


# ---------------------------------------------------------------------------
# Access profiles
# ---------------------------------------------------------------------------


def test_a_missing_access_profile_denies() -> None:
    """The caller who forgot to present one is indistinguishable from the
    caller who has none."""
    with pytest.raises(RestrictedAccessDeniedError):
        assert_access_permitted(None, SensitivityClass.INTERNAL, scope())


def test_an_access_profile_from_another_scope_is_refused() -> None:
    here = scope()
    foreign = AccessProfile(
        max_sensitivity=SensitivityClass.RESTRICTED,
        scope=scope(),
        purpose_reference="audit",
    )
    with pytest.raises(OrganizationScopeMismatchError):
        assert_access_permitted(foreign, SensitivityClass.INTERNAL, here)


def test_an_insufficient_ceiling_is_refused() -> None:
    here = scope()
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.INTERNAL, scope=here, purpose_reference="audit"
    )
    with pytest.raises(RestrictedAccessDeniedError):
        assert_access_permitted(profile, SensitivityClass.RESTRICTED, here)
    assert assert_access_permitted(profile, SensitivityClass.INTERNAL, here) is profile


# ---------------------------------------------------------------------------
# Independence
# ---------------------------------------------------------------------------


def test_an_independent_reader_with_an_operational_role_is_refused() -> None:
    """Independence is re-verified at the moment of the read: a reader who
    acquired an operational role after the grant is no longer
    independent, and the grant does not know that."""
    port = FakeAuthorizationPort()
    here = scope()
    reader = authority(
        DocumentRole.INDEPENDENT_READER,
        here,
        port,
        actor_reference="actor-conflicted",
        also_holds=(DocumentRole.DOCUMENT_APPROVER,),
    )
    with pytest.raises(AuditorIndependenceViolationError):
        assert_reader_independent(reader, here, port=port)


def test_a_genuinely_independent_reader_passes() -> None:
    port = FakeAuthorizationPort()
    here = scope()
    reader = authority(DocumentRole.INDEPENDENT_READER, here, port)
    assert_reader_independent(reader, here, port=port)


def test_independence_is_only_checked_for_the_independent_role() -> None:
    port = FakeAuthorizationPort()
    here = scope()
    custodian = authority(DocumentRole.DOCUMENT_CUSTODIAN, here, port)
    assert_reader_independent(custodian, here, port=port)


def test_an_independent_reader_without_an_actor_reference_is_refused() -> None:
    port = FakeAuthorizationPort()
    here = scope()
    anonymous = AuthorityReference(
        authority_id=authority(DocumentRole.INDEPENDENT_READER, here, port).authority_id,
        role_code="independent_reader",
        scope=here,
        actor_reference="",
    )
    with pytest.raises(AuditorIndependenceViolationError):
        assert_reader_independent(anonymous, here, port=port)


def test_scope_determination_is_the_first_gate() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError):
        assert_scope_determined(None)
    here = scope()
    assert assert_scope_determined(here) is here

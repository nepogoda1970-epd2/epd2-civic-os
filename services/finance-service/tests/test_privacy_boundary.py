"""The privacy boundary of `epd2_finance_service`, proved structurally.

Canon 19f.15 and `ФИН-01`: there is no global user identifier in this
context - no `UserId`, no `PersonId`, no reusable member, voter,
credential or ballot identifier - and a party appears only as an opaque,
purpose-scoped, perimeter-scoped `FinancePartyHandle`. `ФИН-36`: finance
records, identifiers and audit metadata form no correlation bridge into
voting.

Three independent scans back that up, because a single one would be easy
to satisfy accidentally:

1. `dataclasses.fields` over **every** dataclass the package defines - the
   authoritative statement of what a finance record holds;
2. a scan of the executable code of every module (identifiers, attribute
   names, parameter names and string literals, with docstrings and
   comments excluded), permitting the prohibited-key register in
   `domain.py` and nothing else;
3. the behavioural checks: a handle presented for the wrong purpose or
   the wrong perimeter refuses, a forbidden inbound reference kind
   refuses, and `as_reference()` is the only form a party takes on a wire.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
from dataclasses import fields, is_dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

import epd2_finance_service
from epd2_finance_service import (
    application,
    authorization,
    domain,
    events,
    exceptions,
    ledger,
    projections,
    records,
    references,
    reporting,
    storage,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    FinancePartyHandle,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    ReasonCoded,
    RetentionBinding,
)
from epd2_finance_service.exceptions import (
    ForbiddenIdentityLinkageError,
    PartyHandlePurposeMismatchError,
)
from epd2_finance_service.records import (
    ContributionKind,
    ContributionReceipt,
    ExpenseClaim,
    FinanceContribution,
    GovernedAct,
)
from epd2_finance_service.references import assert_reference_kind_allowed

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_SCOPE = OrganizationalScopeRef(organization_id=uuid4())
_OTHER_SCOPE = OrganizationalScopeRef(organization_id=uuid4())
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)
_NO_CONFLICT = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board")

#: The identity field names canon 19f.15 forbids outright. Not the whole of
#: `domain.PROHIBITED_IDENTITY_KEYS`: these six are the ones that would be
#: a *field* of a finance record, and none may appear anywhere in the
#: package's executable code except in that register itself.
FORBIDDEN_IDENTITY_FIELD_NAMES: tuple[str, ...] = (
    "user_id",
    "person_id",
    "member_id",
    "ballot_id",
    "vote_id",
    "credential_id",
)

#: The name of the one register in `domain.py` that is allowed to spell
#: those six strings, because refusing them is what it is for.
PERMITTED_REGISTER_NAME = "PROHIBITED_IDENTITY_KEYS"

PACKAGE_MODULES = (
    application,
    authorization,
    domain,
    events,
    exceptions,
    ledger,
    projections,
    records,
    references,
    reporting,
    storage,
)


def _authority(*, actor: str) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(),
        role_code="finance_administrator",
        scope=_SCOPE,
        actor_reference=actor,
    )


def _act() -> GovernedAct:
    return GovernedAct(
        at=_NOW,
        by_authority=_authority(actor="actor-admin"),
        reason=_REASON,
        policy=_POLICY,
        conflict=_NO_CONFLICT,
    )


def _handle(
    purpose: HandlePurpose = HandlePurpose.CONTRIBUTION,
    perimeter: OrganizationalScopeRef | None = None,
) -> FinancePartyHandle:
    return FinancePartyHandle(
        handle_id=uuid4(),
        purpose=purpose,
        perimeter=_SCOPE if perimeter is None else perimeter,
    )


def _package_dataclasses() -> dict[str, type]:
    """Every dataclass the package itself declares, keyed by qualified name."""
    found: dict[str, type] = {}
    for module in PACKAGE_MODULES:
        for _, member in inspect.getmembers(module, inspect.isclass):
            if not member.__module__.startswith(epd2_finance_service.__name__):
                continue
            if is_dataclass(member):
                found[f"{member.__module__}.{member.__qualname__}"] = member
    return found


def _module_paths() -> list[pathlib.Path]:
    package_root = pathlib.Path(epd2_finance_service.__file__).parent
    return sorted(package_root.glob("*.py"))


def _docstring_constant_ids(tree: ast.Module) -> set[int]:
    """The `id()` of every `Constant` node that is a docstring.

    Docstrings are prose, and prose that *names* a forbidden key in order
    to explain why it is forbidden is the opposite of a leak. Comments are
    absent from the AST entirely and so are excluded for free."""
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            docstrings.add(id(body[0].value))
    return docstrings


def _permitted_register_constant_ids(tree: ast.Module) -> set[int]:
    """The `id()` of every string constant inside the permitted register."""
    permitted: set[int] = set()
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == PERMITTED_REGISTER_NAME
            for target in targets
        ):
            continue
        for descendant in ast.walk(node):
            if isinstance(descendant, ast.Constant) and isinstance(descendant.value, str):
                permitted.add(id(descendant))
    return permitted


def _code_tokens(path: pathlib.Path) -> set[str]:
    """Every name and string literal the module's executable code contains.

    Identifiers, attribute names, parameter names, keyword-argument names,
    class and function names, import aliases and string literals - minus
    docstrings, minus the constants of the one permitted register."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    excluded = _docstring_constant_ids(tree) | _permitted_register_constant_ids(tree)
    tokens: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.arg):
            tokens.add(node.arg)
        elif isinstance(node, ast.keyword):
            if node.arg is not None:
                tokens.add(node.arg)
        elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            tokens.add(node.name)
        elif isinstance(node, ast.alias):
            tokens.add(node.asname or node.name)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in excluded
        ):
            tokens.add(node.value)
    return tokens


# =============================================================================
# Scan 1: no dataclass field is a prohibited identity key (`ФИН-01`)
# =============================================================================


def test_no_dataclass_field_in_the_finance_package_is_a_prohibited_identity_key() -> None:
    offending: list[str] = []
    for qualified_name, dataclass_type in _package_dataclasses().items():
        for field in fields(dataclass_type):
            if field.name in FORBIDDEN_IDENTITY_FIELD_NAMES:
                offending.append(f"{qualified_name}.{field.name}")
    assert offending == []


def test_the_dataclass_scan_actually_sees_the_packages_aggregates() -> None:
    scanned = set(_package_dataclasses())
    for expected in (
        "epd2_finance_service.ledger.JournalEntry",
        "epd2_finance_service.records.FinanceContribution",
        "epd2_finance_service.reporting.FinanceReportVersion",
        "epd2_finance_service.domain.FinancePartyHandle",
        "epd2_finance_service.projections.PublishedReportProjection",
    ):
        assert expected in scanned
    assert len(scanned) > 40


def test_no_dataclass_field_names_a_membership_or_voting_record() -> None:
    offending: list[str] = []
    for qualified_name, dataclass_type in _package_dataclasses().items():
        for field in fields(dataclass_type):
            lowered = field.name.lower()
            if any(
                fragment in lowered
                for fragment in ("membership", "ballot", "voter", "tally", "delegation")
            ):
                offending.append(f"{qualified_name}.{field.name}")
    assert offending == []


# =============================================================================
# Scan 2: the source text (`ФИН-01`, `ФИН-02`)
# =============================================================================


@pytest.mark.parametrize("path", _module_paths(), ids=lambda path: path.name)
def test_no_module_names_a_prohibited_identity_key_in_its_executable_code(
    path: pathlib.Path,
) -> None:
    tokens = _code_tokens(path)
    offending = sorted(name for name in FORBIDDEN_IDENTITY_FIELD_NAMES if name in tokens)
    assert offending == [], f"{path.name} spells {offending} outside the permitted register"


def test_the_permitted_register_is_the_one_place_those_strings_are_spelled() -> None:
    assert set(FORBIDDEN_IDENTITY_FIELD_NAMES) <= domain.PROHIBITED_IDENTITY_KEYS
    domain_path = pathlib.Path(domain.__file__)
    tree = ast.parse(domain_path.read_text(encoding="utf-8"))
    permitted = _permitted_register_constant_ids(tree)
    assert permitted, "the permitted register was not found in domain.py"
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) in permitted
    }
    assert set(FORBIDDEN_IDENTITY_FIELD_NAMES) <= literals


def test_the_source_scan_would_notice_a_prohibited_key_if_one_were_added(
    tmp_path: pathlib.Path,
) -> None:
    """A negative control on the scan itself.

    A structural test that cannot fail is a structural test that proves
    nothing, so this feeds the scanner a module shaped exactly like a leak
    - a dataclass field, a keyword argument and a payload key - and
    requires it to catch all three."""
    leaky = tmp_path / "leaky.py"
    leaky.write_text(
        '"""A docstring mentioning user_id, which must not count."""\n'
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\n"
        "class Leak:\n"
        "    member_id: str\n\n\n"
        "def emit(*, person_id: str) -> dict[str, object]:\n"
        '    return {"ballot_id": person_id}\n',
        encoding="utf-8",
    )
    tokens = _code_tokens(leaky)
    assert {"member_id", "person_id", "ballot_id"} <= tokens
    assert "user_id" not in tokens


# =============================================================================
# Scan 3: the handle is the only party form (`ФИН-01`)
# =============================================================================


def test_a_party_handle_presented_for_the_wrong_purpose_refuses() -> None:
    handle = _handle(HandlePurpose.CONTRIBUTION)
    with pytest.raises(PartyHandlePurposeMismatchError) as excinfo:
        handle.assert_usable_for(HandlePurpose.SPONSORSHIP, _SCOPE)
    assert excinfo.value.reason_code == "FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH"


def test_a_party_handle_presented_outside_its_perimeter_refuses() -> None:
    handle = _handle(HandlePurpose.CONTRIBUTION)
    with pytest.raises(PartyHandlePurposeMismatchError) as excinfo:
        handle.assert_usable_for(HandlePurpose.CONTRIBUTION, _OTHER_SCOPE)
    assert excinfo.value.reason_code == "FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH"


@pytest.mark.parametrize("purpose", list(HandlePurpose))
def test_a_handle_is_valid_for_exactly_one_purpose(purpose: HandlePurpose) -> None:
    handle = _handle(purpose)
    handle.assert_usable_for(purpose, _SCOPE)
    for other in HandlePurpose:
        if other is purpose:
            continue
        with pytest.raises(PartyHandlePurposeMismatchError):
            handle.assert_usable_for(other, _SCOPE)


def test_two_handles_for_one_party_in_two_purposes_are_unequal_by_construction() -> None:
    contribution_handle = _handle(HandlePurpose.CONTRIBUTION)
    sponsorship_handle = _handle(HandlePurpose.SPONSORSHIP)
    assert contribution_handle != sponsorship_handle
    assert contribution_handle.as_reference() != sponsorship_handle.as_reference()


def test_the_handles_as_reference_is_the_only_wire_form() -> None:
    handle = _handle(HandlePurpose.CONTRIBUTION)
    public_methods = {
        name
        for name, member in inspect.getmembers(FinancePartyHandle, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public_methods == {"assert_usable_for", "as_reference"}
    assert handle.as_reference().startswith("fph:")
    assert not hasattr(handle, "to_payload")
    assert not hasattr(handle, "resolve")


@pytest.mark.parametrize(
    "smuggled",
    ["Erika Mustermann", "DE02120300000000202051", "member-42", "user-1", "", "  "],
)
def test_a_party_field_refuses_anything_that_is_not_an_opaque_handle_reference(
    smuggled: str,
) -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        ContributionReceipt(
            receipt_id=uuid4(),
            kind=ContributionKind.DONATION,
            received_at=_NOW,
            method="bank_transfer",
            amount=Money(50_000, "EUR"),
            contributor_handle_reference=smuggled,
        )
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_every_party_bearing_record_refuses_a_direct_identity() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        ExpenseClaim(
            claim_id=uuid4(),
            scope=_SCOPE,
            claimant_handle_reference="member-42",
            purpose_class="travel",
            amount=Money(12_000, "EUR"),
            retention=_RETENTION,
        )


def test_a_contribution_carries_the_handle_reference_and_never_a_handle_object() -> None:
    handle = _handle(HandlePurpose.CONTRIBUTION)
    receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=_NOW,
        method="bank_transfer",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=handle.as_reference(),
    )
    contribution = FinanceContribution(
        contribution_id=uuid4(), scope=_SCOPE, receipt=receipt, retention=_RETENTION
    )
    assert isinstance(contribution.receipt.contributor_handle_reference, str)
    assert str(handle.handle_id) in contribution.receipt.contributor_handle_reference
    state = events.finance_contribution_state_payload(contribution)
    domain.reject_identity_payload_keys(state, context="contribution state")


def test_a_forbidden_inbound_reference_kind_refuses() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        assert_reference_kind_allowed("participation_credential")
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_no_module_holds_a_read_or_write_edge_into_voting_or_membership() -> None:
    forbidden_type_names = {
        "VoteEnvelope",
        "Tally",
        "Ballot",
        "Delegation",
        "DelegationSnapshot",
        "ParticipationCredential",
        "Membership",
        "IdentityRecord",
    }
    for path in _module_paths():
        tokens = _code_tokens(path)
        assert not tokens & forbidden_type_names, path.name


def test_the_finance_party_handle_is_derived_from_nothing() -> None:
    parameters = set(inspect.signature(FinancePartyHandle).parameters)
    assert parameters == {"handle_id", "purpose", "perimeter", "policy_version"}
    with pytest.raises(TypeError):
        FinancePartyHandle(  # type: ignore[call-arg]
            handle_id=uuid4(),
            purpose=HandlePurpose.CONTRIBUTION,
            perimeter=_SCOPE,
            derived_from="Erika Mustermann",
        )


def test_the_prohibited_key_register_is_a_frozenset_and_cannot_be_extended_at_runtime() -> None:
    assert isinstance(domain.PROHIBITED_IDENTITY_KEYS, frozenset)
    with pytest.raises(AttributeError):
        domain.PROHIBITED_IDENTITY_KEYS.add("something_else")  # type: ignore[attr-defined]

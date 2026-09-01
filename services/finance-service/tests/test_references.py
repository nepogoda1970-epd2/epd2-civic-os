"""Tests for `epd2_finance_service.references` - the typed pointers this
context holds at records other packs own, the outward references other
packs may hold at finance records, and the refusals that keep foreign
concepts out.

Two structural claims are proved here rather than asserted in prose: no
reference type carries an assertion about a document (`ФИН-21`), and the
package imports no other service's code at all (`ФИН-44`).
"""

from __future__ import annotations

import ast
import pathlib
from dataclasses import fields, is_dataclass, replace
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

import epd2_finance_service
from epd2_finance_service.domain import (
    FinancePartyHandle,
    HandlePurpose,
    OrganizationalScopeRef,
    PolicyBinding,
    RetentionBinding,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    EvidenceAssertionUnavailableError,
    EvidenceReferenceMissingError,
    ForbiddenIdentityLinkageError,
    RetentionBindingMissingError,
    UnauthorizedStateTransitionError,
)
from epd2_finance_service.references import (
    FORBIDDEN_DOCUMENT_ASSERTION_KEYS,
    FORBIDDEN_DOCUMENT_CONTENT_KEYS,
    FORBIDDEN_INBOUND_REFERENCE_KINDS,
    ContributionReference,
    DocumentReference,
    FinanceAuditEngagementReference,
    FinancePartyHandleReference,
    FinanceRecordReference,
    FinanceReportReference,
    FinanceReportVersionReference,
    ForeignRecordReference,
    LegalCaseReference,
    LegalHoldReference,
    LobbyingContactReference,
    NoticeEffectReference,
    OrganizationalScopeReference,
    PolicyVersionReference,
    ReferenceOwner,
    RetentionClassReference,
    SponsorshipReference,
    assert_no_document_content,
    assert_not_lobbying_subject,
    assert_reference_kind_allowed,
    require_retention_binding,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_SCOPE = OrganizationalScopeRef(organization_id=uuid4())
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)

#: The service packages this one is allowed to import. `ФИН-44`: every
#: cross-service fact arrives through a published interface, never through
#: a code edge into another service's package.
PERMITTED_FIRST_PARTY_PACKAGES: frozenset[str] = frozenset(
    {"epd2_core", "epd2_audit_core", "epd2_finance_service"}
)

#: Field names that would make a reference an assertion about the record it
#: points at. Only PACK-11 may say a document is authentic, signed,
#: admitted, valid or publishable (`ФИН-21`).
FORBIDDEN_ASSERTION_FIELD_NAMES: frozenset[str] = frozenset(
    {"is_authentic", "is_signed", "is_admitted", "is_valid", "is_publishable", "is_active"}
)

#: Every reference type this module publishes.
REFERENCE_TYPES: tuple[type, ...] = (
    ForeignRecordReference,
    LegalCaseReference,
    LegalHoldReference,
    RetentionClassReference,
    NoticeEffectReference,
    DocumentReference,
    LobbyingContactReference,
    OrganizationalScopeReference,
    PolicyVersionReference,
    FinanceRecordReference,
    FinanceReportReference,
    FinanceReportVersionReference,
    ContributionReference,
    SponsorshipReference,
    FinanceAuditEngagementReference,
    FinancePartyHandleReference,
)


def _imported_top_level_packages() -> set[str]:
    package_root = pathlib.Path(epd2_finance_service.__file__).parent
    imported: set[str] = set()
    for path in sorted(package_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module.split(".", 1)[0])
    return imported


# =============================================================================
# No cross-service code edge (`ФИН-44`)
# =============================================================================


def test_the_finance_package_imports_no_other_service_package() -> None:
    first_party = {name for name in _imported_top_level_packages() if name.startswith("epd2_")}
    assert first_party <= PERMITTED_FIRST_PARTY_PACKAGES
    assert first_party == PERMITTED_FIRST_PARTY_PACKAGES


def test_pack_09_reference_shapes_are_finance_side_mirrors_and_not_imports() -> None:
    assert LegalCaseReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert LegalCaseReference.__module__.startswith(epd2_finance_service.__name__)
    assert "epd2_compliance_service" not in _imported_top_level_packages()


# =============================================================================
# A reference asserts nothing about what it points at (`ФИН-21`)
# =============================================================================


def test_no_reference_type_carries_an_assertion_field() -> None:
    offending: list[str] = []
    for reference_type in REFERENCE_TYPES:
        assert is_dataclass(reference_type)
        for field in fields(reference_type):
            if field.name in FORBIDDEN_ASSERTION_FIELD_NAMES:
                offending.append(f"{reference_type.__qualname__}.{field.name}")
    assert offending == []


def test_a_payload_asserting_something_about_a_document_refuses() -> None:
    with pytest.raises(EvidenceAssertionUnavailableError) as excinfo:
        assert_no_document_content({"is_authentic": True}, context="finance record")
    assert excinfo.value.reason_code == "FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE"


@pytest.mark.parametrize("key", sorted(FORBIDDEN_DOCUMENT_ASSERTION_KEYS))
def test_every_forbidden_document_assertion_key_refuses(key: str) -> None:
    with pytest.raises(EvidenceAssertionUnavailableError):
        assert_no_document_content({key: True}, context="finance record")


@pytest.mark.parametrize("key", sorted(FORBIDDEN_DOCUMENT_CONTENT_KEYS))
def test_every_forbidden_document_content_key_refuses(key: str) -> None:
    with pytest.raises(EvidenceAssertionUnavailableError):
        assert_no_document_content({key: "..."}, context="finance record")


def test_a_document_assertion_nested_one_level_down_refuses_too() -> None:
    payload = {"evidence": [{"document": {"extracted_text": "..."}}]}
    with pytest.raises(EvidenceAssertionUnavailableError):
        assert_no_document_content(payload, context="finance record")


def test_a_reference_only_document_payload_passes() -> None:
    reference = DocumentReference(
        external_reference="pack-11-doc-1",
        scope=_SCOPE,
        kind="invoice",
        version_reference="v3",
    )
    payload = reference.to_payload()
    assert_no_document_content(payload, context="document reference")
    assert payload["owner"] == str(ReferenceOwner.PACK_11_DOCUMENTS)
    assert payload["version_reference"] == "v3"


def test_a_document_reference_requires_a_kind_and_a_non_empty_reference() -> None:
    with pytest.raises(EvidenceReferenceMissingError):
        DocumentReference(external_reference="doc-1", scope=_SCOPE, kind="  ")
    with pytest.raises(EvidenceReferenceMissingError):
        DocumentReference(external_reference="  ", scope=_SCOPE, kind="invoice")
    with pytest.raises(EvidenceReferenceMissingError):
        DocumentReference(
            external_reference="doc-1", scope=_SCOPE, kind="invoice", version_reference="  "
        )


# =============================================================================
# Legal hold state is never cached (`ФИН-22`)
# =============================================================================


def test_a_legal_hold_reference_caches_no_active_flag() -> None:
    field_names = {field.name for field in fields(LegalHoldReference)}
    assert "is_active" not in field_names
    assert "held_until" not in field_names
    assert field_names == {"external_reference", "scope", "observed_at"}


def test_a_legal_hold_reference_records_when_the_pointer_was_taken_not_when_checked() -> None:
    hold = LegalHoldReference(external_reference="pack-09-hold-1", scope=_SCOPE, observed_at=_NOW)
    assert hold.observed_at == _NOW
    assert hold.owner is ReferenceOwner.PACK_09_COMPLIANCE
    with pytest.raises(AccountingPeriodUndeterminedError):
        LegalHoldReference(
            external_reference="pack-09-hold-1",
            scope=_SCOPE,
            observed_at=datetime(2026, 3, 1, 12, 0),
        )


def test_a_governed_finance_record_must_name_the_record_class_it_is_bound_to() -> None:
    with pytest.raises(RetentionBindingMissingError) as excinfo:
        require_retention_binding(None)
    assert excinfo.value.reason_code == "FINANCE_RETENTION_BINDING_MISSING"
    binding = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
    assert require_retention_binding(binding) is binding


def test_a_retention_class_reference_produces_the_binding_a_record_stores() -> None:
    reference = RetentionClassReference(external_reference="finance.record.v1", scope=_SCOPE)
    binding = reference.as_binding(bound_at=_NOW)
    assert binding.record_class_reference == "finance.record.v1"
    assert binding.bound_at == _NOW
    with pytest.raises(AccountingPeriodUndeterminedError):
        reference.as_binding(bound_at=datetime(2026, 3, 1, 12, 0))


# =============================================================================
# The PACK-35 boundary, re-exported and not reimplemented (`ФИН-20`)
# =============================================================================


def test_the_lobbying_refusal_is_the_one_implementation_re_exported() -> None:
    from epd2_finance_service.records import (
        assert_not_lobbying_subject as records_implementation,
    )

    assert assert_not_lobbying_subject is records_implementation
    with pytest.raises(UnauthorizedStateTransitionError):
        assert_not_lobbying_subject("meeting")


def test_a_lobbying_contact_reference_is_the_one_place_a_pack_35_kind_is_legitimate() -> None:
    reference = LobbyingContactReference(
        external_reference="pack-35-contact-1", scope=_SCOPE, contact_kind="meeting"
    )
    assert reference.owner is ReferenceOwner.PACK_35_LOBBYING
    assert reference.to_payload()["contact_kind"] == "meeting"
    with pytest.raises(EvidenceReferenceMissingError):
        LobbyingContactReference(
            external_reference="pack-35-contact-1", scope=_SCOPE, contact_kind="  "
        )


# =============================================================================
# Forbidden inbound reference kinds (`ФИН-36`)
# =============================================================================


@pytest.mark.parametrize("kind", sorted(FORBIDDEN_INBOUND_REFERENCE_KINDS))
def test_every_forbidden_inbound_reference_kind_refuses(kind: str) -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        assert_reference_kind_allowed(kind)


@pytest.mark.parametrize(
    "kind", ["Ballot", " VOTE ", "vote-envelope", "delegation snapshot", "Membership"]
)
def test_the_forbidden_kind_check_normalises_case_spacing_and_hyphens(kind: str) -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        assert_reference_kind_allowed(kind)


@pytest.mark.parametrize("kind", ["invoice", "bank_statement", "legal_case", "policy_version"])
def test_an_ordinary_finance_reference_kind_passes(kind: str) -> None:
    assert_reference_kind_allowed(kind)


def test_the_forbidden_kind_set_covers_voting_identity_and_membership() -> None:
    for kind in ("ballot", "vote", "tally", "delegation", "credential", "identity", "membership"):
        assert kind in FORBIDDEN_INBOUND_REFERENCE_KINDS


# =============================================================================
# The outward references other packs may hold
# =============================================================================


def test_each_finance_record_reference_kind_is_a_distinct_type() -> None:
    record_id = uuid4()
    report = FinanceReportReference(record_id=record_id, scope=_SCOPE)
    version = FinanceReportVersionReference(record_id=record_id, scope=_SCOPE)
    contribution = ContributionReference(record_id=record_id, scope=_SCOPE)
    sponsorship = SponsorshipReference(record_id=record_id, scope=_SCOPE)
    engagement = FinanceAuditEngagementReference(record_id=record_id, scope=_SCOPE)
    distinct = {
        type(reference) for reference in (report, version, contribution, sponsorship, engagement)
    }
    assert {reference_type.__name__ for reference_type in distinct} == {
        "FinanceReportReference",
        "FinanceReportVersionReference",
        "ContributionReference",
        "SponsorshipReference",
        "FinanceAuditEngagementReference",
    }
    # Structurally identical on the wire, and still not interchangeable:
    # mypy refuses the two types at every call site, which is the point.
    assert report.to_payload() == version.to_payload()


def test_an_outward_finance_reference_carries_no_state() -> None:
    field_names = {field.name for field in fields(FinanceReportVersionReference)}
    assert field_names == {"record_id", "scope"}
    assert "state" not in field_names
    assert "is_published" not in field_names


def test_a_party_handle_reference_is_typed_and_never_enters_a_public_payload() -> None:
    handle = FinancePartyHandle(
        handle_id=uuid4(), purpose=HandlePurpose.CONTRIBUTION, perimeter=_SCOPE
    )
    reference = FinancePartyHandleReference.from_handle(handle)
    assert reference.record_id == handle.handle_id
    assert reference.purpose is HandlePurpose.CONTRIBUTION
    assert reference.scope is handle.perimeter
    payload = reference.to_payload()
    assert "purpose" not in payload
    assert set(payload) == {"owner", "record_id", "organization_id"}


def test_an_outward_scope_reference_emits_and_never_compares() -> None:
    reference = OrganizationalScopeReference.from_scope(_SCOPE)
    assert not hasattr(reference, "assert_matches")
    assert reference.as_scope() == _SCOPE
    assert reference.to_payload()["organization_id"] == str(_SCOPE.organization_id)
    with pytest.raises(EvidenceReferenceMissingError):
        OrganizationalScopeReference(organization_id=uuid4(), scope_kind="  ")


def test_a_policy_version_reference_carries_no_rule_and_no_effective_date() -> None:
    reference = PolicyVersionReference.from_binding(_POLICY)
    field_names = {field.name for field in fields(reference)}
    assert field_names == {"policy_kind", "policy_id", "policy_version"}
    assert "effective_from" not in field_names
    assert reference.to_payload() == {
        "policy_kind": "income_classification",
        "policy_id": "income",
        "policy_version": "2026.1",
    }
    with pytest.raises(EvidenceReferenceMissingError):
        replace(reference, policy_version="  ")


def test_every_inward_reference_names_the_context_that_owns_its_target() -> None:
    assert LegalCaseReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert LegalHoldReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert RetentionClassReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert NoticeEffectReference.owner is ReferenceOwner.PACK_09_COMPLIANCE
    assert DocumentReference.owner is ReferenceOwner.PACK_11_DOCUMENTS
    assert LobbyingContactReference.owner is ReferenceOwner.PACK_35_LOBBYING
    assert OrganizationalScopeReference.owner is ReferenceOwner.PACK_08_ORGANIZATION
    assert FinanceRecordReference.owner is ReferenceOwner.PACK_10_FINANCE
    assert PolicyVersionReference.owner is ReferenceOwner.PACK_10_FINANCE


def test_a_notice_effect_reference_carries_no_verdict_of_its_own() -> None:
    field_names = {field.name for field in fields(NoticeEffectReference)}
    assert field_names == {"external_reference", "scope"}
    for forbidden in ("verdict", "outcome", "accepted", "decision"):
        assert forbidden not in field_names


def test_a_legal_case_reference_points_at_no_person() -> None:
    field_names = {field.name for field in fields(LegalCaseReference)}
    assert field_names == {"external_reference", "scope"}
    reference = LegalCaseReference(external_reference="pack-09-case-1", scope=_SCOPE)
    assert set(reference.to_payload()) == {"owner", "external_reference", "organization_id"}


def test_an_empty_external_reference_refuses_on_every_inward_reference() -> None:
    for reference_type in (LegalCaseReference, RetentionClassReference, NoticeEffectReference):
        with pytest.raises(EvidenceReferenceMissingError):
            reference_type(external_reference="  ", scope=_SCOPE)

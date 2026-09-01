"""Governed determinations — ADR-053's four PACK-11 interface
requirements.

ADR-053 recorded that until all four exist, PACK-10 "records the reference
and the absence of the assertion — it does not simulate any of the four
with a local heuristic". These tests are what makes that contract
checkable from PACK-11's side: an absent determination is reported as
absent, a stale one does not carry forward, and nothing in this module
computes an answer.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from _builders import Fixture, at, governed_document, reason, scope, version

from epd2_document_service.determinations import (
    AdmissibilityDetermination,
    AdmissibilityStatus,
    DocumentResolution,
    SignatureDetermination,
    SignatureForm,
    SignatureStatus,
    absent_admissibility_status,
    absent_signature_status,
    assert_determination_current,
    require_admissibility_determination,
    require_signature_determination,
)
from epd2_document_service.documents import GovernedDocument
from epd2_document_service.domain import DocumentKind
from epd2_document_service.exceptions import (
    DocumentDeterminationMissingError,
    DocumentDeterminationNotPermittedError,
    DocumentDeterminationStaleError,
    DocumentFieldInvalidError,
)
from epd2_document_service.versions import DocumentVersion


def _setup() -> tuple[Fixture, GovernedDocument, DocumentVersion]:
    fixture = Fixture()
    document = governed_document(fixture.scope, fixture.custodian)
    recorded = version(document, fixture.author)
    return fixture, document, recorded


def _signature(
    fixture: Fixture,
    document: GovernedDocument,
    recorded: DocumentVersion,
    **overrides: object,
) -> SignatureDetermination:
    base = {
        "determination_id": uuid4(),
        "scope": fixture.scope,
        "document_id": document.document_id,
        "version_number": recorded.version_number,
        "determined_version_hash": recorded.version_hash,
        "status": SignatureStatus.SIGNED_VERIFIED,
        "determined_at": at(6),
        "determined_by": fixture.custodian,
        "reason": reason("DOCUMENT_SIGNATURE_DETERMINED"),
        "form": SignatureForm.QUALIFIED_ELECTRONIC,
        "verification_basis_reference": "validation-report-7",
    }
    base.update(overrides)
    return SignatureDetermination(**base)  # type: ignore[arg-type]


def _admissibility(
    fixture: Fixture,
    document: GovernedDocument,
    recorded: DocumentVersion,
    **overrides: object,
) -> AdmissibilityDetermination:
    base = {
        "determination_id": uuid4(),
        "scope": fixture.scope,
        "document_id": document.document_id,
        "version_number": recorded.version_number,
        "determined_version_hash": recorded.version_hash,
        "procedure_reference": "case-2026-11",
        "status": AdmissibilityStatus.ADMITTED,
        "determined_at": at(7),
        "determined_by": fixture.legal_reviewer,
        "reason": reason("DOCUMENT_ADMISSIBILITY_DETERMINED"),
    }
    base.update(overrides)
    return AdmissibilityDetermination(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Requirement 1 — reference resolution
# ---------------------------------------------------------------------------


def test_a_resolved_reference_reports_existence_and_kind_and_nothing_else() -> None:
    """A consumer asked "does this exist and what kind is it?"; every
    additional field would be an answer to a question it did not ask,
    exported across a bounded-context boundary."""
    resolution = DocumentResolution(
        reference="epd2-doc:x:v1",
        scope=scope(),
        exists=True,
        kind=DocumentKind.LEGAL_OPINION,
        current_version_number=3,
    )
    payload = resolution.to_payload()
    assert set(payload) == {
        "reference",
        "organization_id",
        "exists",
        "kind",
        "current_version_number",
        "is_revoked",
    }


def test_a_resolved_document_must_report_its_kind() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        DocumentResolution(reference="r", scope=scope(), exists=True)


def test_an_unresolved_reference_must_not_report_a_kind() -> None:
    """Reporting a kind would confirm the existence the resolution just
    denied - which is how a not-found answer becomes an existence
    oracle."""
    with pytest.raises(DocumentFieldInvalidError):
        DocumentResolution(
            reference="r", scope=scope(), exists=False, kind=DocumentKind.LEGAL_OPINION
        )


def test_an_unresolved_reference_is_a_normal_returnable_answer() -> None:
    resolution = DocumentResolution(reference="r", scope=scope(), exists=False)
    assert resolution.exists is False
    assert resolution.kind is None


# ---------------------------------------------------------------------------
# Requirement 2 — signature status
# ---------------------------------------------------------------------------


def test_the_absent_signature_answer_is_an_explicit_value() -> None:
    """`not_determined` rather than `None`: a consumer receiving `None`
    might read it as `not_signed`."""
    assert absent_signature_status() is SignatureStatus.NOT_DETERMINED


def test_a_recorded_determination_cannot_claim_not_determined() -> None:
    fixture, document, recorded = _setup()
    with pytest.raises(DocumentFieldInvalidError):
        _signature(fixture, document, recorded, status=SignatureStatus.NOT_DETERMINED)


def test_a_verified_status_must_reference_what_the_verification_relied_on() -> None:
    """A status asserting that a verification happened must say what it
    was; restating the reasoning here would create a second version of it
    that can disagree with the original."""
    fixture, document, recorded = _setup()
    for status in (SignatureStatus.SIGNED_VERIFIED, SignatureStatus.SIGNATURE_INVALID):
        with pytest.raises(DocumentFieldInvalidError):
            _signature(
                fixture,
                document,
                recorded,
                status=status,
                verification_basis_reference=None,
            )


def test_a_signed_status_must_record_the_signature_form() -> None:
    """Legal weight differs sharply between forms, and a consumer that
    only learned "signed" would flatten that difference."""
    fixture, document, recorded = _setup()
    with pytest.raises(DocumentFieldInvalidError):
        _signature(fixture, document, recorded, form=None)


def test_signed_unverified_is_a_real_answer_and_is_not_signed_original() -> None:
    """The honest answer for a scanned ink signature: neither "signed" nor
    "not signed", and collapsing it into either would be inventing the
    verification this service just said it could not perform."""
    fixture, document, recorded = _setup()
    determination = _signature(
        fixture,
        document,
        recorded,
        status=SignatureStatus.SIGNED_UNVERIFIED,
        form=SignatureForm.SCANNED_HANDWRITTEN,
        verification_basis_reference=None,
    )
    assert determination.is_signed_original is False


def test_only_a_verified_signature_counts_as_a_signed_original() -> None:
    fixture, document, recorded = _setup()
    assert _signature(fixture, document, recorded).is_signed_original is True
    assert (
        _signature(
            fixture,
            document,
            recorded,
            status=SignatureStatus.NOT_SIGNED,
            form=None,
            verification_basis_reference=None,
        ).is_signed_original
        is False
    )


def test_an_absent_signature_determination_is_a_reason_coded_refusal() -> None:
    """Not a guess. This is the whole of ADR-053 requirement 2."""
    _fixture, _document, recorded = _setup()
    with pytest.raises(DocumentDeterminationMissingError):
        require_signature_determination(None, recorded)


def test_a_determination_does_not_carry_forward_to_a_changed_version() -> None:
    fixture, document, recorded = _setup()
    determination = _signature(fixture, document, recorded)
    other = version(document, fixture.author, content=b"different content")
    with pytest.raises(DocumentDeterminationStaleError):
        require_signature_determination(determination, other)


def test_a_determination_for_another_version_number_is_stale() -> None:
    fixture, document, recorded = _setup()
    determination = _signature(fixture, document, recorded, version_number=2)
    with pytest.raises(DocumentDeterminationStaleError):
        assert_determination_current(determination, recorded)


def test_a_determination_for_another_document_is_stale() -> None:
    fixture, document, recorded = _setup()
    other_document = governed_document(fixture.scope, fixture.custodian)
    determination = _signature(fixture, document, recorded, document_id=other_document.document_id)
    with pytest.raises(DocumentDeterminationStaleError):
        assert_determination_current(determination, recorded)


def test_a_current_determination_is_returned() -> None:
    fixture, document, recorded = _setup()
    determination = _signature(fixture, document, recorded)
    assert require_signature_determination(determination, recorded) is determination


def test_a_signature_payload_carries_no_signature_value() -> None:
    """The signature *value* is content; only the determination travels."""
    fixture, document, recorded = _setup()
    payload = _signature(fixture, document, recorded).to_payload()
    assert "signature_value" not in payload
    assert payload["signature_status"] == "signed_verified"


# ---------------------------------------------------------------------------
# Requirement 3 — admissibility
# ---------------------------------------------------------------------------


def test_the_absent_admissibility_answer_is_an_explicit_value() -> None:
    assert absent_admissibility_status() is AdmissibilityStatus.NOT_DETERMINED


def test_an_admissibility_determination_is_bound_to_a_procedure() -> None:
    """Admissibility is never a property of a document in the abstract."""
    fixture, document, recorded = _setup()
    with pytest.raises(DocumentFieldInvalidError):
        _admissibility(fixture, document, recorded, procedure_reference="  ")


def test_an_admission_in_one_procedure_says_nothing_about_another() -> None:
    """Silently reusing it would be this service extending a body's
    decision beyond what that body decided."""
    fixture, document, recorded = _setup()
    determination = _admissibility(fixture, document, recorded)
    with pytest.raises(DocumentDeterminationNotPermittedError):
        require_admissibility_determination(
            determination, recorded, procedure_reference="another-case"
        )


def test_an_admission_with_limitation_must_state_the_limitation() -> None:
    """An unstated limitation is no limitation."""
    fixture, document, recorded = _setup()
    with pytest.raises(DocumentFieldInvalidError):
        _admissibility(
            fixture, document, recorded, status=AdmissibilityStatus.ADMITTED_WITH_LIMITATION
        )


def test_an_admission_with_limitation_still_permits_reliance() -> None:
    """Returning False would be safer-looking and wrong: it would suppress
    material a competent body admitted."""
    fixture, document, recorded = _setup()
    limited = _admissibility(
        fixture,
        document,
        recorded,
        status=AdmissibilityStatus.ADMITTED_WITH_LIMITATION,
        limitation_reference="limited-to-facts-in-paragraph-3",
    )
    assert limited.permits_reliance is True


def test_not_admitted_and_deferred_do_not_permit_reliance() -> None:
    fixture, document, recorded = _setup()
    for status in (AdmissibilityStatus.NOT_ADMITTED, AdmissibilityStatus.DEFERRED):
        assert _admissibility(fixture, document, recorded, status=status).permits_reliance is False


def test_a_recorded_admissibility_cannot_claim_not_determined() -> None:
    fixture, document, recorded = _setup()
    with pytest.raises(DocumentFieldInvalidError):
        _admissibility(fixture, document, recorded, status=AdmissibilityStatus.NOT_DETERMINED)


def test_an_absent_admissibility_determination_is_a_reason_coded_refusal() -> None:
    _fixture, _document, recorded = _setup()
    with pytest.raises(DocumentDeterminationMissingError):
        require_admissibility_determination(None, recorded, procedure_reference="case-1")


def test_a_stale_admissibility_determination_does_not_carry_forward() -> None:
    fixture, document, recorded = _setup()
    determination = _admissibility(fixture, document, recorded)
    changed = replace(recorded, version_hash="f" * 64)
    with pytest.raises(DocumentDeterminationStaleError):
        require_admissibility_determination(
            determination, changed, procedure_reference="case-2026-11"
        )

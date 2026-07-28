"""Domain primitives: scope, content, provenance, reasons, retention,
holds, access profiles and the three emission boundaries.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from _builders import T0, at, provenance, retention_binding, scope

from epd2_document_service.domain import (
    FORBIDDEN_CONTENT_KEYS,
    OFFICIAL_RECORD_KINDS,
    PROHIBITED_IDENTITY_KEYS,
    PROHIBITED_VOTING_KEYS,
    QUALIFIED_OPINION_KINDS,
    AccessProfile,
    ConflictDeclaration,
    ContentDescriptor,
    DispositionAuthorization,
    DocumentKind,
    HoldState,
    LegalHoldBinding,
    OrganizationalScopeRef,
    ProvenanceKind,
    ReasonCoded,
    RequestContext,
    SensitivityClass,
    assert_conflict_declared,
    assert_emission_safe,
    assert_no_document_content,
    content_digest_of,
    deterministic_digest,
    reject_identity_payload_keys,
    reject_voting_linkage_keys,
    require_digest,
    require_reference,
    require_text,
    require_timezone,
    sensitivity_rank,
)
from epd2_document_service.exceptions import (
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    DocumentContentLeakError,
    DocumentFieldInvalidError,
    DocumentReferenceInvalidError,
    DocumentTimestampNaiveError,
    ForbiddenIdentityLinkageError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    RetentionBindingMissingError,
    VotingLinkageForbiddenError,
)

# ---------------------------------------------------------------------------
# Structural helpers
# ---------------------------------------------------------------------------


def test_require_text_refuses_empty_and_whitespace() -> None:
    assert require_text("x", "f") == "x"
    for bad in ("", "   ", "\t\n"):
        with pytest.raises(DocumentFieldInvalidError):
            require_text(bad, "f")


def test_require_timezone_refuses_a_naive_datetime() -> None:
    """Assuming UTC would invent a fact that then travels into a hash
    nobody can later contradict."""
    with pytest.raises(DocumentTimestampNaiveError):
        require_timezone(datetime(2026, 1, 1), context="test")
    aware = datetime(2026, 1, 1, tzinfo=UTC)
    assert require_timezone(aware, context="test") is aware


def test_deterministic_digest_is_stable_and_separator_safe() -> None:
    """`("ab","cd")` and `("abc","d")` must not collide.

    A plain concatenation would make them identical, which would let two
    different requests share one idempotency key."""
    assert deterministic_digest("a", "b") == deterministic_digest("a", "b")
    assert deterministic_digest("ab", "cd") != deterministic_digest("abc", "d")


def test_content_digest_is_sha256_hex_and_refuses_non_bytes() -> None:
    assert require_digest(content_digest_of(b""), "d")
    with pytest.raises(DocumentFieldInvalidError):
        content_digest_of("not bytes")  # type: ignore[arg-type]


def test_require_digest_rejects_anything_that_is_not_a_64_hex_digest() -> None:
    for bad in ("", "abc", "A" * 64, "z" * 64, "a" * 63, "a" * 65):
        with pytest.raises(DocumentFieldInvalidError):
            require_digest(bad, "digest")


def test_require_reference_uses_the_reference_code_not_the_field_code() -> None:
    """A missing reference is reported as a missing reference, so an
    operator is not left reading a generic validation error."""
    with pytest.raises(DocumentReferenceInvalidError):
        require_reference("  ", "external_reference")


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def test_an_undetermined_scope_denies_rather_than_defaulting() -> None:
    subject = scope()
    with pytest.raises(OrganizationScopeUndeterminedError):
        subject.assert_matches(None)


def test_a_foreign_scope_is_refused() -> None:
    with pytest.raises(OrganizationScopeMismatchError):
        scope().assert_matches(scope())


def test_a_matching_scope_passes() -> None:
    subject = scope()
    subject.assert_matches(OrganizationalScopeRef(organization_id=subject.organization_id))


def test_an_empty_scope_kind_is_undetermined() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError):
        OrganizationalScopeRef(organization_id=uuid4(), scope_kind="  ")


def test_request_context_require_scope_denies_on_none() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError):
        RequestContext(scope=None).require_scope()


# ---------------------------------------------------------------------------
# Taxonomies
# ---------------------------------------------------------------------------


def test_sensitivity_ranking_is_monotonic() -> None:
    order = [
        SensitivityClass.PUBLIC,
        SensitivityClass.INTERNAL,
        SensitivityClass.CONFIDENTIAL,
        SensitivityClass.RESTRICTED,
    ]
    ranks = [sensitivity_rank(s) for s in order]
    assert ranks == sorted(ranks)
    assert len(set(ranks)) == len(ranks)


def test_official_record_kinds_and_qualified_opinion_kinds_are_disjoint() -> None:
    """A document is either the record of a proceeding or an opinion about
    one; treating a legal opinion as an official record would give it the
    minutes' review requirements and not the legal one's."""
    assert OFFICIAL_RECORD_KINDS.isdisjoint(QUALIFIED_OPINION_KINDS)


def test_the_taxonomy_covers_every_use_the_register_names() -> None:
    """The kinds the master register's foundation-only FIR entries need."""
    for expected in (
        DocumentKind.MEETING_MINUTES,
        DocumentKind.DECISION_RECORD,
        DocumentKind.CANDIDACY_DOCUMENT,
        DocumentKind.INITIATIVE_ATTACHMENT,
        DocumentKind.LEGAL_OPINION,
        DocumentKind.EXPERT_OPINION,
        DocumentKind.FINANCE_EVIDENCE,
        DocumentKind.OFFICIAL_CORRESPONDENCE,
        DocumentKind.APPEAL_RECORD,
        DocumentKind.SEPA_MANDATE_EVIDENCE,
        DocumentKind.PUBLIC_TRANSPARENCY_DOCUMENT,
    ):
        assert expected in set(DocumentKind)


# ---------------------------------------------------------------------------
# Content descriptor
# ---------------------------------------------------------------------------


def test_a_content_descriptor_carries_the_digest_and_never_the_bytes() -> None:
    descriptor = ContentDescriptor(
        digest=content_digest_of(b"abc"), media_type="text/plain", byte_length=3
    )
    payload = descriptor.to_payload()
    assert payload["content_digest"] == content_digest_of(b"abc")
    assert not any(key in payload for key in FORBIDDEN_CONTENT_KEYS)


def test_a_content_descriptor_refuses_a_negative_length_and_empty_media_type() -> None:
    digest = content_digest_of(b"")
    with pytest.raises(DocumentFieldInvalidError):
        ContentDescriptor(digest=digest, media_type="text/plain", byte_length=-1)
    with pytest.raises(DocumentFieldInvalidError):
        ContentDescriptor(digest=digest, media_type=" ", byte_length=0)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_provenance_refuses_recording_before_capture() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        provenance(captured_at=at(5), recorded_at=at(1))


def test_ai_generated_material_requires_an_analysis_provenance_reference() -> None:
    """FIR-AI-002: an AI output with no provenance contract is not
    attributable, and this context refuses to store one as if it were."""
    with pytest.raises(DocumentFieldInvalidError):
        provenance(kind=ProvenanceKind.GENERATED_BY_AI_ANALYSIS)
    ok = provenance(
        kind=ProvenanceKind.GENERATED_BY_AI_ANALYSIS,
        analysis_provenance_reference="ai:analysis:1234",
    )
    assert ok.analysis_provenance_reference == "ai:analysis:1234"


def test_provenance_payload_carries_no_identity_key() -> None:
    reject_identity_payload_keys(provenance().to_payload(), context="provenance")


# ---------------------------------------------------------------------------
# Reasons and conflicts
# ---------------------------------------------------------------------------


def test_a_reason_code_must_be_upper_case_and_non_empty() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        ReasonCoded(reason_code="document_approved", authority_reference="a")
    with pytest.raises(DocumentFieldInvalidError):
        ReasonCoded(reason_code="  ", authority_reference="a")


def test_an_undeclared_or_absent_conflict_fails_closed() -> None:
    """Silence and "I have not checked" tell this service exactly as much,
    so both raise the same error."""
    with pytest.raises(ConflictOfInterestUndeclaredError):
        assert_conflict_declared(None, action="approve")
    with pytest.raises(ConflictOfInterestUndeclaredError):
        assert_conflict_declared(
            ConflictDeclaration(state=ConflictDeclaration.UNDECLARED, declared_by="a"),
            action="approve",
        )


def test_a_blocking_conflict_has_its_own_refusal() -> None:
    with pytest.raises(ConflictOfInterestBlockingError):
        assert_conflict_declared(
            ConflictDeclaration(state=ConflictDeclaration.BLOCKING, declared_by="a"),
            action="approve",
        )


def test_a_declared_non_blocking_conflict_passes() -> None:
    assert_conflict_declared(
        ConflictDeclaration(state=ConflictDeclaration.DECLARED_NON_BLOCKING, declared_by="a"),
        action="approve",
    )


# ---------------------------------------------------------------------------
# Retention and legal hold
# ---------------------------------------------------------------------------


def test_a_retention_binding_requires_both_pack_09_references() -> None:
    with pytest.raises(RetentionBindingMissingError):
        retention_binding(record_class_reference=" ")
    with pytest.raises(RetentionBindingMissingError):
        retention_binding(retention_policy_reference=" ")


def test_a_retention_policy_version_must_be_positive() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        retention_binding(retention_policy_version=0)


def test_an_active_hold_blocks_and_an_indeterminate_hold_is_undetermined() -> None:
    """The two are distinct facts with distinct consequences: collapsing
    them would let "we could not reach PACK-09" read later as "there was a
    hold"."""
    subject = scope()
    active = LegalHoldBinding(
        hold_reference="h-1", scope=subject, state=HoldState.ACTIVE, observed_at=T0
    )
    unknown = LegalHoldBinding(
        hold_reference="h-2", scope=subject, state=HoldState.INDETERMINATE, observed_at=T0
    )
    released = LegalHoldBinding(
        hold_reference="h-3", scope=subject, state=HoldState.RELEASED, observed_at=T0
    )
    assert (active.blocks_destruction, active.is_undetermined) == (True, False)
    assert (unknown.blocks_destruction, unknown.is_undetermined) == (False, True)
    assert (released.blocks_destruction, released.is_undetermined) == (False, False)


def test_a_disposition_authorization_requires_a_positive_version_count() -> None:
    with pytest.raises(DocumentFieldInvalidError):
        DispositionAuthorization(
            authorization_reference="pack-09:auth:1",
            scope=scope(),
            authorized_at=T0,
            authorized_version_count=0,
            disposition_action="delete",
        )


# ---------------------------------------------------------------------------
# Access profile
# ---------------------------------------------------------------------------


def test_an_access_profile_permits_only_up_to_its_ceiling() -> None:
    profile = AccessProfile(
        max_sensitivity=SensitivityClass.CONFIDENTIAL,
        scope=scope(),
        purpose_reference="audit",
    )
    assert profile.permits(SensitivityClass.PUBLIC) is True
    assert profile.permits(SensitivityClass.CONFIDENTIAL) is True
    assert profile.permits(SensitivityClass.RESTRICTED) is False


# ---------------------------------------------------------------------------
# The three emission boundaries
# ---------------------------------------------------------------------------


def test_every_prohibited_identity_key_is_caught_at_the_top_level() -> None:
    for key in PROHIBITED_IDENTITY_KEYS:
        with pytest.raises(ForbiddenIdentityLinkageError):
            reject_identity_payload_keys({key: "value"}, context="test")


def test_a_prohibited_identity_key_nested_in_a_list_is_caught() -> None:
    """A key one level down is the same leak as one at the top, and the
    list case is the one a naive dict-only walk misses."""
    payload = {"items": [{"inner": {"email": "a@b.c"}}]}
    with pytest.raises(ForbiddenIdentityLinkageError):
        reject_identity_payload_keys(payload, context="test")


def test_identity_key_matching_is_case_insensitive() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        reject_identity_payload_keys({"Email": "a@b.c"}, context="test")


def test_every_prohibited_voting_key_is_caught() -> None:
    for key in PROHIBITED_VOTING_KEYS:
        with pytest.raises(VotingLinkageForbiddenError):
            reject_voting_linkage_keys({key: "value"}, context="test")


def test_voting_linkage_has_its_own_error_not_the_identity_one() -> None:
    """Different invariants, different reason codes: reporting a
    voting-isolation breach under an identity code would misclassify it."""
    with pytest.raises(VotingLinkageForbiddenError):
        reject_voting_linkage_keys({"ballot_id": "x"}, context="test")


def test_every_forbidden_content_key_is_caught() -> None:
    for key in FORBIDDEN_CONTENT_KEYS:
        with pytest.raises(DocumentContentLeakError):
            assert_no_document_content({key: "value"}, context="test")


def test_a_raw_byte_value_is_caught_whatever_its_key_is() -> None:
    """The one value-level check worth making: a key-name check sees
    names, and bytes under an innocuous key are still content."""
    with pytest.raises(DocumentContentLeakError):
        assert_no_document_content({"note_reference": b"scanned page"}, context="test")
    with pytest.raises(DocumentContentLeakError):
        assert_no_document_content({"a": [{"b": bytearray(b"x")}]}, context="test")


def test_assert_emission_safe_runs_all_three_checks() -> None:
    assert_emission_safe({"document_id": "1", "kind": "meeting_minutes"}, context="ok")
    with pytest.raises(DocumentContentLeakError):
        assert_emission_safe({"content": "x"}, context="c")
    with pytest.raises(ForbiddenIdentityLinkageError):
        assert_emission_safe({"member_id": "x"}, context="i")
    with pytest.raises(VotingLinkageForbiddenError):
        assert_emission_safe({"tally_id": "x"}, context="v")


def test_a_clean_payload_passes_every_boundary() -> None:
    payload = {
        "document_id": str(uuid4()),
        "content_descriptor": {"content_digest": "a" * 64, "byte_length": 12},
        "title_reference": "title-ref-1",
        "nested": [{"authority_id": str(uuid4()), "role_code": "document_approver"}],
    }
    assert_emission_safe(payload, context="clean")

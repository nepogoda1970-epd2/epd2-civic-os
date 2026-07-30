"""Compatibility assessment (PACK-13 §14; ADR-074).

Additive field, required field, removed field, type change, enum
extension, semantic-risk manual review, and the reason-code semantic
change — plus the rule that governs all of them: `unknown` is never
collapsed into "probably compatible".
"""

from __future__ import annotations

import pytest
from _data_plane_builders import BASE_SCHEMA, clean_assessment, human_verdict

from epd2_data_plane_service.compatibility import (
    SEMANTIC_RISK_CLASSES,
    CompatibilityAssessment,
    HumanVerdict,
    SemanticRiskClass,
    StructuralChangeKind,
    assess_structural_change,
    diff_documents,
    require_compatible_under_mode,
    require_review_complete,
)
from epd2_data_plane_service.exceptions import (
    LegalReviewRequiredError,
    SchemaCompatibilityUnknownError,
    SchemaIncompatibleError,
    SecurityReviewRequiredError,
    SemanticReviewRequiredError,
)
from epd2_data_plane_service.registry import CompatibilityMode


def _with(properties: dict[str, object], required: list[str] | None = None) -> dict[str, object]:
    document: dict[str, object] = {
        "type": "object",
        "properties": {**BASE_SCHEMA["properties"], **properties},
        "required": required if required is not None else list(BASE_SCHEMA["required"]),
    }
    return document


def _without(field: str) -> dict[str, object]:
    properties = {k: v for k, v in BASE_SCHEMA["properties"].items() if k != field}
    required = [r for r in BASE_SCHEMA["required"] if r != field]
    document: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    return document


# ---------------------------------------------------------------------------
# The structural differ
# ---------------------------------------------------------------------------


def test_an_identical_document_is_fully_compatible() -> None:
    verdict = assess_structural_change(BASE_SCHEMA, BASE_SCHEMA)
    assert verdict.verdict is CompatibilityMode.FULL
    assert verdict.changes == ()


def test_an_additive_optional_field_is_backward_compatible_at_best() -> None:
    verdict = assess_structural_change(BASE_SCHEMA, _with({"note": {"type": "string"}}))
    assert verdict.verdict is CompatibilityMode.BACKWARD
    assert verdict.changes[0].kind is StructuralChangeKind.FIELD_ADDED_OPTIONAL


def test_an_additive_field_carrying_a_default_escalates_to_unknown() -> None:
    """`P13-COMPAT-003`: adding a field changes what a payload means if
    the field's absence previously carried meaning."""
    verdict = assess_structural_change(
        BASE_SCHEMA, _with({"note": {"type": "string", "default": "none"}})
    )
    assert verdict.verdict is CompatibilityMode.UNKNOWN


def test_an_additive_field_carrying_a_declared_obligation_escalates() -> None:
    verdict = assess_structural_change(
        BASE_SCHEMA,
        _with({"note": {"type": "string"}}),
        additive_fields_carrying_obligation=["note"],
    )
    assert verdict.verdict is CompatibilityMode.UNKNOWN


def test_a_new_required_field_is_breaking() -> None:
    verdict = assess_structural_change(
        BASE_SCHEMA,
        _with({"note": {"type": "string"}}, required=[*BASE_SCHEMA["required"], "note"]),
    )
    assert verdict.verdict is CompatibilityMode.BREAKING


def test_a_removed_field_is_breaking() -> None:
    verdict = assess_structural_change(BASE_SCHEMA, _without("status"))
    assert verdict.verdict is CompatibilityMode.BREAKING
    assert any(c.kind is StructuralChangeKind.FIELD_REMOVED for c in verdict.changes)


def test_a_type_change_is_breaking() -> None:
    verdict = assess_structural_change(BASE_SCHEMA, _with({"status": {"type": "integer"}}))
    assert verdict.verdict is CompatibilityMode.BREAKING
    assert any(c.kind is StructuralChangeKind.TYPE_CHANGED for c in verdict.changes)


def test_an_enum_extension_is_unknown_not_additive_safe() -> None:
    """`P13-EVO-011`: a consumer switching exhaustively over the old set
    now has an unhandled value."""
    verdict = assess_structural_change(
        BASE_SCHEMA,
        _with({"status": {"type": "string", "enum": ["active", "suspended", "lapsed"]}}),
    )
    assert verdict.verdict is CompatibilityMode.UNKNOWN


def test_an_enum_value_removal_is_breaking() -> None:
    verdict = assess_structural_change(
        BASE_SCHEMA, _with({"status": {"type": "string", "enum": ["active"]}})
    )
    assert verdict.verdict is CompatibilityMode.BREAKING


def test_a_changed_default_is_unknown() -> None:
    before = _with({"status": {"type": "string", "default": "active"}})
    after = _with({"status": {"type": "string", "default": "suspended"}})
    verdict = assess_structural_change(before, after)
    assert verdict.verdict is CompatibilityMode.UNKNOWN


def test_relaxing_a_required_field_is_forward_compatible() -> None:
    after: dict[str, object] = {
        "type": "object",
        "properties": BASE_SCHEMA["properties"],
        "required": ["membership_id"],
    }
    verdict = assess_structural_change(BASE_SCHEMA, after)
    assert verdict.verdict is CompatibilityMode.FORWARD


def test_the_diff_is_deterministic_and_ordered() -> None:
    after = _with({"zeta": {"type": "string"}, "alpha": {"type": "string"}})
    first = diff_documents(BASE_SCHEMA, after)
    second = diff_documents(BASE_SCHEMA, after)
    assert first == second
    added = [c.field_path for c in first if c.kind is StructuralChangeKind.FIELD_ADDED_OPTIONAL]
    assert added == sorted(added)


# ---------------------------------------------------------------------------
# Semantic risk and review
# ---------------------------------------------------------------------------


def test_a_semantic_risk_class_forces_unknown_however_clean_the_diff() -> None:
    """`P13-COMPAT-004`: the invisible classes are never classifiable by
    an automated checker."""
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.ENUM_MEANING_CHANGE}))
    assert assessment.automated_verdict is CompatibilityMode.FULL
    assert assessment.combined_verdict is CompatibilityMode.UNKNOWN
    assert assessment.requires_semantic_review


def test_a_reason_code_semantic_change_requires_review() -> None:
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.REASON_CODE_SEMANTICS_CHANGE}))
    with pytest.raises(SemanticReviewRequiredError):
        require_review_complete(assessment, context="family")


def test_a_legal_effect_change_requires_legal_review() -> None:
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.LEGAL_EFFECT_CHANGE}))
    assert assessment.mandates_legal_review
    with pytest.raises(LegalReviewRequiredError):
        require_review_complete(assessment, context="family")


def test_a_retention_semantics_change_requires_legal_review() -> None:
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.RETENTION_SEMANTICS_CHANGE}))
    with pytest.raises(LegalReviewRequiredError):
        require_review_complete(assessment, context="family")


def test_an_identity_linkage_change_requires_security_review() -> None:
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.IDENTITY_LINKAGE_CHANGE}))
    assert assessment.mandates_security_review
    with pytest.raises(SecurityReviewRequiredError):
        require_review_complete(assessment, context="family")


def test_an_organization_scope_semantics_change_requires_security_review() -> None:
    assessment = clean_assessment(
        risks=frozenset({SemanticRiskClass.ORGANIZATION_SCOPE_SEMANTICS_CHANGE})
    )
    with pytest.raises(SecurityReviewRequiredError):
        require_review_complete(assessment, context="family")


def test_an_unclassifiable_structural_change_requires_review() -> None:
    assessment = clean_assessment(
        proposed=_with({"status": {"type": "string", "enum": ["active", "suspended", "lapsed"]}})
    )
    with pytest.raises(SchemaCompatibilityUnknownError):
        require_review_complete(assessment, context="family")


def test_a_human_verdict_completes_the_review() -> None:
    assessment = clean_assessment(
        risks=frozenset({SemanticRiskClass.ENUM_MEANING_CHANGE}),
        human=human_verdict(CompatibilityMode.BACKWARD),
    )
    require_review_complete(assessment, context="family")
    assert assessment.combined_verdict is CompatibilityMode.BACKWARD


def test_a_reviewer_may_escalate_but_not_silently_downgrade() -> None:
    """The worse of the two verdicts governs."""
    breaking = assess_structural_change(BASE_SCHEMA, _without("status"))
    assessment = CompatibilityAssessment(
        assessment_id=clean_assessment().assessment_id,
        family_id=clean_assessment().family_id,
        previous_version_id=None,
        proposed_version_label="2.0.0",
        structural=breaking,
        human=human_verdict(CompatibilityMode.BACKWARD),
    )
    assert assessment.combined_verdict is CompatibilityMode.BREAKING


def test_a_human_verdict_requires_a_recorded_rationale() -> None:
    from _data_plane_builders import NOW, actor

    with pytest.raises(SemanticReviewRequiredError):
        HumanVerdict(
            verdict=CompatibilityMode.FULL, reviewer=actor(), reviewed_at=NOW, rationale=""
        )


def test_the_semantic_risk_set_is_complete() -> None:
    assert frozenset(SemanticRiskClass) == SEMANTIC_RISK_CLASSES
    assert len(SEMANTIC_RISK_CLASSES) == 8


# ---------------------------------------------------------------------------
# Mode enforcement
# ---------------------------------------------------------------------------


def test_a_breaking_proposal_is_refused_under_a_backward_family() -> None:
    breaking = assess_structural_change(BASE_SCHEMA, _without("status"))
    assessment = CompatibilityAssessment(
        assessment_id=clean_assessment().assessment_id,
        family_id=clean_assessment().family_id,
        previous_version_id=None,
        proposed_version_label="2.0.0",
        structural=breaking,
        human=human_verdict(CompatibilityMode.BREAKING),
    )
    with pytest.raises(SchemaIncompatibleError):
        require_compatible_under_mode(
            assessment, declared_mode=CompatibilityMode.BACKWARD, context="family"
        )


def test_a_breaking_family_accepts_a_breaking_proposal() -> None:
    breaking = assess_structural_change(BASE_SCHEMA, _without("status"))
    assessment = CompatibilityAssessment(
        assessment_id=clean_assessment().assessment_id,
        family_id=clean_assessment().family_id,
        previous_version_id=None,
        proposed_version_label="2.0.0",
        structural=breaking,
        human=human_verdict(CompatibilityMode.BREAKING),
    )
    require_compatible_under_mode(
        assessment, declared_mode=CompatibilityMode.BREAKING, context="family"
    )


def test_an_unknown_verdict_never_reaches_the_mode_check_silently() -> None:
    assessment = clean_assessment(risks=frozenset({SemanticRiskClass.EVENT_MEANING_CHANGE}))
    with pytest.raises(SchemaCompatibilityUnknownError):
        require_compatible_under_mode(
            assessment, declared_mode=CompatibilityMode.BACKWARD, context="family"
        )


def test_a_full_family_demands_full_compatibility() -> None:
    assessment = clean_assessment(proposed=_with({"note": {"type": "string"}}))
    with pytest.raises(SchemaIncompatibleError):
        require_compatible_under_mode(
            assessment, declared_mode=CompatibilityMode.FULL, context="family"
        )


def test_an_identical_proposal_satisfies_every_mode() -> None:
    assessment = clean_assessment()
    for mode in (
        CompatibilityMode.FULL,
        CompatibilityMode.BACKWARD,
        CompatibilityMode.FORWARD,
        CompatibilityMode.BREAKING,
    ):
        require_compatible_under_mode(assessment, declared_mode=mode, context="family")

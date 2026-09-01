"""Deterministic compatibility assessment (PACK-13 §14; ADR-074).

The checker answers a **narrow structural question** — did a field
disappear, did a type change, did a required set tighten — and answers it
the same way every time. It does not answer the question that actually
breaks consumers: did the meaning change while the bytes stayed the same.

So the module has two halves, and the split is the point:

- `assess_structural_change` classifies what a differ can see. Its
  verdict is the **automated verdict**.
- `SEMANTIC_RISK_CLASSES` enumerates the change classes that are
  structurally invisible and **always** escalate to manual review
  (`P13-COMPAT-004`). Their presence forces the combined verdict to
  `UNKNOWN` no matter how clean the structural diff is.

Three rules are enforced rather than documented:

1. **`unknown` is never collapsed into "probably compatible"**
   (`P13-COMPAT-002`). A change the checker cannot classify is `unknown`
   and requires review.
2. **An additive change is not automatically safe** (`P13-COMPAT-003`).
   Adding a field is classified `BACKWARD` at best, and only when it is
   optional, has no new default, and carries no declared obligation; an
   additive change with any of those is escalated.
3. **The automated verdict and the human verdict are separate fields**
   (ADR-074). A `CompatibilityAssessment` carrying only the tool's
   answer is incomplete, and `require_review_complete` says so.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from epd2_data_plane_service.domain import ActorReference, require_timezone
from epd2_data_plane_service.exceptions import (
    LegalReviewRequiredError,
    SchemaCompatibilityUnknownError,
    SchemaIncompatibleError,
    SecurityReviewRequiredError,
    SemanticReviewRequiredError,
)
from epd2_data_plane_service.registry import CompatibilityMode


class SemanticRiskClass(StrEnum):
    """The change classes no automated checker can see.

    Each is a case where the serialized bytes may be identical before and
    after, and every consumer is nonetheless now wrong. §14.1's four bold
    rows are here, plus the three §17 and ADR-074 add: organization-scope
    semantics, retention semantics and authorization implication."""

    ENUM_MEANING_CHANGE = "enum_meaning_change"
    REASON_CODE_SEMANTICS_CHANGE = "reason_code_semantics_change"
    EVENT_MEANING_CHANGE = "event_meaning_change"
    IDENTITY_LINKAGE_CHANGE = "identity_linkage_change"
    ORGANIZATION_SCOPE_SEMANTICS_CHANGE = "organization_scope_semantics_change"
    RETENTION_SEMANTICS_CHANGE = "retention_semantics_change"
    AUTHORIZATION_IMPLICATION_CHANGE = "authorization_implication_change"
    LEGAL_EFFECT_CHANGE = "legal_effect_change"


#: The complete set. Named as a constant so a test can assert that the
#: checker never classifies one of these automatically.
SEMANTIC_RISK_CLASSES: frozenset[SemanticRiskClass] = frozenset(SemanticRiskClass)

#: Which review a given semantic-risk class mandates (`P13-GOV-003`).
#: A class may appear in more than one map value's domain — legal effect
#: needs legal review; identity linkage needs security review; both need
#: the semantic review every entry here implies.
LEGAL_REVIEW_CLASSES: frozenset[SemanticRiskClass] = frozenset(
    {
        SemanticRiskClass.LEGAL_EFFECT_CHANGE,
        SemanticRiskClass.RETENTION_SEMANTICS_CHANGE,
    }
)
SECURITY_REVIEW_CLASSES: frozenset[SemanticRiskClass] = frozenset(
    {
        SemanticRiskClass.IDENTITY_LINKAGE_CHANGE,
        SemanticRiskClass.AUTHORIZATION_IMPLICATION_CHANGE,
        SemanticRiskClass.ORGANIZATION_SCOPE_SEMANTICS_CHANGE,
    }
)


class StructuralChangeKind(StrEnum):
    """The change kinds the structural differ recognises."""

    FIELD_ADDED_OPTIONAL = "field_added_optional"
    FIELD_ADDED_REQUIRED = "field_added_required"
    FIELD_REMOVED = "field_removed"
    TYPE_CHANGED = "type_changed"
    ENUM_VALUE_ADDED = "enum_value_added"
    ENUM_VALUE_REMOVED = "enum_value_removed"
    REQUIRED_TIGHTENED = "required_tightened"
    REQUIRED_RELAXED = "required_relaxed"
    DEFAULT_CHANGED = "default_changed"
    DEFAULT_ADDED = "default_added"
    DEFAULT_REMOVED = "default_removed"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True, slots=True)
class StructuralChange:
    """One observed difference between two schema documents."""

    kind: StructuralChangeKind
    field_path: str
    detail: str = ""


#: How each structural change kind maps to a compatibility verdict when
#: taken alone. `UNCLASSIFIED` maps to `UNKNOWN`, which is the whole
#: reason the kind exists: a difference the differ does not understand is
#: reported, never dropped.
_KIND_VERDICTS: Mapping[StructuralChangeKind, CompatibilityMode] = {
    # Adding an optional field is the only change this table calls
    # backward compatible, and even that is conditional: see
    # `assess_structural_change`, which escalates it when the field
    # carries a default or a declared obligation (`P13-COMPAT-003`).
    StructuralChangeKind.FIELD_ADDED_OPTIONAL: CompatibilityMode.BACKWARD,
    StructuralChangeKind.FIELD_ADDED_REQUIRED: CompatibilityMode.BREAKING,
    StructuralChangeKind.FIELD_REMOVED: CompatibilityMode.BREAKING,
    StructuralChangeKind.TYPE_CHANGED: CompatibilityMode.BREAKING,
    # Enum extension is assessed on its own and never assumed
    # additive-safe (`P13-EVO-011`): a consumer that switches
    # exhaustively over the old set now has an unhandled value.
    StructuralChangeKind.ENUM_VALUE_ADDED: CompatibilityMode.UNKNOWN,
    StructuralChangeKind.ENUM_VALUE_REMOVED: CompatibilityMode.BREAKING,
    StructuralChangeKind.REQUIRED_TIGHTENED: CompatibilityMode.BREAKING,
    StructuralChangeKind.REQUIRED_RELAXED: CompatibilityMode.FORWARD,
    # A changed default changes what the absent case means, which no
    # differ can evaluate against a consumer's expectations.
    StructuralChangeKind.DEFAULT_CHANGED: CompatibilityMode.UNKNOWN,
    StructuralChangeKind.DEFAULT_ADDED: CompatibilityMode.UNKNOWN,
    StructuralChangeKind.DEFAULT_REMOVED: CompatibilityMode.UNKNOWN,
    StructuralChangeKind.UNCLASSIFIED: CompatibilityMode.UNKNOWN,
}

#: Verdict severity, worst last. Combining verdicts takes the worst, and
#: `UNKNOWN` sorts above `BREAKING` deliberately: a change known to break
#: has a migration plan; a change nobody has classified does not.
_VERDICT_SEVERITY: Mapping[CompatibilityMode, int] = {
    CompatibilityMode.FULL: 0,
    CompatibilityMode.BACKWARD: 1,
    CompatibilityMode.FORWARD: 1,
    CompatibilityMode.BREAKING: 2,
    CompatibilityMode.UNKNOWN: 3,
}


def _properties(document: Mapping[str, Any]) -> Mapping[str, Any]:
    properties = document.get("properties", {})
    return properties if isinstance(properties, Mapping) else {}


def _required(document: Mapping[str, Any]) -> frozenset[str]:
    required = document.get("required", [])
    if isinstance(required, Sequence) and not isinstance(required, str | bytes):
        return frozenset(str(name) for name in required)
    return frozenset()


def _type_of(field_schema: Mapping[str, Any]) -> str:
    value = field_schema.get("type")
    if isinstance(value, list):
        return ",".join(sorted(str(item) for item in value))
    return "" if value is None else str(value)


def _enum_of(field_schema: Mapping[str, Any]) -> frozenset[str]:
    value = field_schema.get("enum")
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return frozenset(str(item) for item in value)
    return frozenset()


def diff_documents(
    previous: Mapping[str, Any], proposed: Mapping[str, Any]
) -> tuple[StructuralChange, ...]:
    """Compute the ordered, deterministic structural diff.

    Deterministic in the strict sense the acceptance criteria need: the
    same two documents always produce the same tuple in the same order,
    because every iteration is over a sorted key set. A differ whose
    output ordering depended on dictionary insertion order would make
    every recorded assessment unreproducible."""
    changes: list[StructuralChange] = []
    previous_properties = _properties(previous)
    proposed_properties = _properties(proposed)
    previous_required = _required(previous)
    proposed_required = _required(proposed)

    for name in sorted(set(previous_properties) - set(proposed_properties)):
        changes.append(
            StructuralChange(
                kind=StructuralChangeKind.FIELD_REMOVED,
                field_path=name,
                detail="a consumer reads it",
            )
        )

    for name in sorted(set(proposed_properties) - set(previous_properties)):
        field_schema = proposed_properties[name]
        schema_mapping = field_schema if isinstance(field_schema, Mapping) else {}
        kind = (
            StructuralChangeKind.FIELD_ADDED_REQUIRED
            if name in proposed_required
            else StructuralChangeKind.FIELD_ADDED_OPTIONAL
        )
        detail = "default present" if "default" in schema_mapping else ""
        changes.append(StructuralChange(kind=kind, field_path=name, detail=detail))

    for name in sorted(set(previous_properties) & set(proposed_properties)):
        before = previous_properties[name]
        after = proposed_properties[name]
        before_map: Mapping[str, Any] = before if isinstance(before, Mapping) else {}
        after_map: Mapping[str, Any] = after if isinstance(after, Mapping) else {}
        changes.extend(_diff_field(name, before_map, after_map))

    for name in sorted(proposed_required - previous_required):
        if name in previous_properties:
            changes.append(
                StructuralChange(
                    kind=StructuralChangeKind.REQUIRED_TIGHTENED,
                    field_path=name,
                    detail="previously valid producers become invalid",
                )
            )
    for name in sorted(previous_required - proposed_required):
        changes.append(
            StructuralChange(kind=StructuralChangeKind.REQUIRED_RELAXED, field_path=name)
        )

    return tuple(changes)


def _diff_field(
    name: str, before: Mapping[str, Any], after: Mapping[str, Any]
) -> list[StructuralChange]:
    changes: list[StructuralChange] = []
    if _type_of(before) != _type_of(after):
        changes.append(
            StructuralChange(
                kind=StructuralChangeKind.TYPE_CHANGED,
                field_path=name,
                detail=f"{_type_of(before)!r} -> {_type_of(after)!r}",
            )
        )
    before_enum, after_enum = _enum_of(before), _enum_of(after)
    for value in sorted(after_enum - before_enum):
        changes.append(
            StructuralChange(
                kind=StructuralChangeKind.ENUM_VALUE_ADDED, field_path=name, detail=value
            )
        )
    for value in sorted(before_enum - after_enum):
        changes.append(
            StructuralChange(
                kind=StructuralChangeKind.ENUM_VALUE_REMOVED, field_path=name, detail=value
            )
        )
    has_before_default = "default" in before
    has_after_default = "default" in after
    if has_before_default and not has_after_default:
        changes.append(StructuralChange(kind=StructuralChangeKind.DEFAULT_REMOVED, field_path=name))
    elif has_after_default and not has_before_default:
        changes.append(StructuralChange(kind=StructuralChangeKind.DEFAULT_ADDED, field_path=name))
    elif has_before_default and before["default"] != after["default"]:
        changes.append(
            StructuralChange(
                kind=StructuralChangeKind.DEFAULT_CHANGED,
                field_path=name,
                detail="the absent case now means something else",
            )
        )
    return changes


def _worst(verdicts: Sequence[CompatibilityMode]) -> CompatibilityMode:
    if not verdicts:
        return CompatibilityMode.FULL
    return max(verdicts, key=lambda mode: _VERDICT_SEVERITY[mode])


@dataclass(frozen=True, slots=True)
class StructuralVerdict:
    """The automated half of an assessment."""

    verdict: CompatibilityMode
    changes: tuple[StructuralChange, ...]

    @property
    def requires_manual_review(self) -> bool:
        return self.verdict is CompatibilityMode.UNKNOWN


def assess_structural_change(
    previous: Mapping[str, Any],
    proposed: Mapping[str, Any],
    *,
    additive_fields_carrying_obligation: Sequence[str] = (),
) -> StructuralVerdict:
    """Classify what the differ can see.

    `additive_fields_carrying_obligation` is how a submitter declares
    that a newly added optional field creates an obligation the consumer
    does not know about — the third of `P13-COMPAT-003`'s three ways an
    additive change is unsafe. Declared fields escalate to `UNKNOWN`
    rather than passing as backward compatible."""
    changes = diff_documents(previous, proposed)
    obligated = frozenset(additive_fields_carrying_obligation)
    verdicts: list[CompatibilityMode] = []
    for change in changes:
        verdict = _KIND_VERDICTS[change.kind]
        if change.kind is StructuralChangeKind.FIELD_ADDED_OPTIONAL and (
            change.field_path in obligated or change.detail == "default present"
        ):
            # An additive change is not automatically safe: a default
            # changes what absence means, and a declared obligation is
            # invisible to the differ (`P13-COMPAT-003`).
            verdict = CompatibilityMode.UNKNOWN
        verdicts.append(verdict)
    return StructuralVerdict(verdict=_worst(verdicts), changes=changes)


@dataclass(frozen=True, slots=True)
class HumanVerdict:
    """The reviewer's half of an assessment (`P13-COMPAT-004`).

    Stored as its own field, never merged into the automated one: an
    assessment carrying only the tool's answer is incomplete, and the two
    verdicts disagreeing is information rather than a problem to be
    smoothed over."""

    verdict: CompatibilityMode
    reviewer: ActorReference
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        require_timezone(self.reviewed_at, field="HumanVerdict.reviewed_at")
        if not self.rationale:
            raise SemanticReviewRequiredError(
                "a human compatibility verdict requires a recorded rationale; a verdict "
                "without one is an opinion the next reviewer cannot evaluate"
            )


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment:
    """One recorded assessment of one proposed change.

    Carries the automated verdict, the declared semantic-risk classes and
    — where review has happened — the human verdict. `combined_verdict`
    is computed, never stored, so it cannot drift from its inputs."""

    assessment_id: UUID
    family_id: UUID
    previous_version_id: UUID | None
    proposed_version_label: str
    structural: StructuralVerdict
    semantic_risk_classes: frozenset[SemanticRiskClass] = frozenset()
    human: HumanVerdict | None = None

    @property
    def automated_verdict(self) -> CompatibilityMode:
        return self.structural.verdict

    @property
    def requires_semantic_review(self) -> bool:
        """True when the change touches an invisible class, or when the
        differ could not classify it. Either way a human decides."""
        return bool(self.semantic_risk_classes) or self.structural.requires_manual_review

    @property
    def combined_verdict(self) -> CompatibilityMode:
        """The verdict the publication path acts on.

        While a semantic-risk class is present and unreviewed, the
        combined verdict is `UNKNOWN` regardless of how clean the
        structural diff is. Once a human verdict exists, the *worse* of
        the two governs — a reviewer may escalate a clean structural
        verdict, and may not silently downgrade a breaking one."""
        if self.human is None:
            if self.requires_semantic_review:
                return CompatibilityMode.UNKNOWN
            return self.automated_verdict
        return _worst([self.automated_verdict, self.human.verdict])

    @property
    def mandates_legal_review(self) -> bool:
        return bool(self.semantic_risk_classes & LEGAL_REVIEW_CLASSES)

    @property
    def mandates_security_review(self) -> bool:
        return bool(self.semantic_risk_classes & SECURITY_REVIEW_CLASSES)


def require_review_complete(assessment: CompatibilityAssessment, *, context: str) -> None:
    """Refuse to proceed on an assessment whose required review has not
    happened.

    Three distinct refusals, because an operator needs to know *which*
    review is missing: legal review for legal-effect and retention
    semantics, security review for identity linkage, authorization
    implication and organization scope, and semantic review for
    everything else the checker could not classify (`P13-GOV-003`)."""
    if assessment.human is not None:
        return
    if assessment.mandates_legal_review:
        raise LegalReviewRequiredError(
            f"{context}: the change touches legal effect or retention semantics and requires "
            f"legal review before publication"
        )
    if assessment.mandates_security_review:
        raise SecurityReviewRequiredError(
            f"{context}: the change touches authorization implication, identity linkage or "
            f"organizational scope and requires security review before publication"
        )
    if assessment.semantic_risk_classes:
        raise SemanticReviewRequiredError(
            f"{context}: the change belongs to an invisible class "
            f"({sorted(c.value for c in assessment.semantic_risk_classes)}) and always "
            f"requires human assessment; no automated checker classifies it"
        )
    if assessment.structural.requires_manual_review:
        raise SchemaCompatibilityUnknownError(
            f"{context}: the checker could not classify this change; unknown is a real "
            f"outcome requiring manual review, never a default to compatible"
        )


def require_compatible_under_mode(
    assessment: CompatibilityAssessment, *, declared_mode: CompatibilityMode, context: str
) -> None:
    """Refuse a proposal that is incompatible under the family's declared
    mode.

    `FULL` demands `FULL`; `BACKWARD` and `FORWARD` accept their own
    direction or better; `BREAKING` accepts anything, because a family
    declared breaking has already accepted the migration obligation.
    `UNKNOWN` is never accepted here — `require_review_complete` handles
    it, and reaching this function with an unknown verdict means review
    was skipped."""
    verdict = assessment.combined_verdict
    if verdict is CompatibilityMode.UNKNOWN:
        raise SchemaCompatibilityUnknownError(
            f"{context}: the combined verdict is unknown; manual review is required before "
            f"a compatibility decision exists to check against the declared mode"
        )
    if declared_mode is CompatibilityMode.BREAKING:
        return
    acceptable: Mapping[CompatibilityMode, frozenset[CompatibilityMode]] = {
        CompatibilityMode.FULL: frozenset({CompatibilityMode.FULL}),
        CompatibilityMode.BACKWARD: frozenset({CompatibilityMode.FULL, CompatibilityMode.BACKWARD}),
        CompatibilityMode.FORWARD: frozenset({CompatibilityMode.FULL, CompatibilityMode.FORWARD}),
    }
    if verdict not in acceptable[declared_mode]:
        raise SchemaIncompatibleError(
            f"{context}: the proposed version is {verdict.value!r} and the family is governed "
            f"under {declared_mode.value!r}; publication is refused"
        )

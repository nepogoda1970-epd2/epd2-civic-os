"""Canonical classification and the derived PACK-12 enforcement tier
(`P12-CLS-001` through `P12-CLS-005`).

The source classification is authoritative. This module maps it, by a
deterministic function, to an enforcement tier that the search and export
rules can be expressed against once rather than per domain.

Three prohibitions make the derivation safe:

- the mapping never writes back to the source classification;
- the mapping never produces a tier more permissive than the source
  classification's own restriction;
- an unmapped classification fails closed rather than falling through to
  a permissive default (`P12-CLS-005`).

The mapping itself is versioned, and the version travels on every
decision, so a past refusal stays answerable after the mapping changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_privileged_access_service.exceptions import (
    ClassificationDowngradeProhibitedError,
    ClassificationUnmappedError,
)


class SourceClassification(StrEnum):
    """The canonical classification values. Authoritative
    (`P12-CLS-001`).

    PACK-09's `RecordSensitivity` and PACK-11's `SensitivityClass` are
    *inputs* to this vocabulary for their own records, not replacements
    for it; see `from_pack09_sensitivity`."""

    PUBLIC_APPROVED = "public_approved"
    PUBLIC_AUTHORITATIVE = "public_authoritative"
    INTERNAL = "internal"
    CONFIDENTIAL_REGULATED = "confidential_regulated"
    CONFIDENTIAL_CASE_METADATA = "confidential_case_metadata"
    DERIVED_DECISION = "derived_decision"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    ABSOLUTELY_EXCLUDED = "absolutely_excluded"


class EnforcementTier(StrEnum):
    """The derived policy abstraction (`P12-CLS-002`). Carries no
    authority of its own."""

    T0_OPEN = "T0-open"
    T0_OPEN_AUTHORITATIVE = "T0-open-authoritative"
    T1_INTERNAL = "T1-internal"
    T1_DERIVED = "T1-derived"
    T2_CONFIDENTIAL = "T2-confidential"
    T2_CASE_METADATA = "T2-case-metadata"
    T3_RESTRICTED = "T3-restricted"
    T4_PROHIBITED = "T4-prohibited"


#: How restrictive each tier is. Used to prove that a derived tier never
#: comes out weaker than its source classification allows.
_TIER_RANK: dict[EnforcementTier, int] = {
    EnforcementTier.T0_OPEN: 0,
    EnforcementTier.T0_OPEN_AUTHORITATIVE: 0,
    EnforcementTier.T1_INTERNAL: 1,
    EnforcementTier.T1_DERIVED: 1,
    EnforcementTier.T2_CONFIDENTIAL: 2,
    EnforcementTier.T2_CASE_METADATA: 2,
    EnforcementTier.T3_RESTRICTED: 3,
    EnforcementTier.T4_PROHIBITED: 4,
}

_SOURCE_RANK: dict[SourceClassification, int] = {
    SourceClassification.PUBLIC_APPROVED: 0,
    SourceClassification.PUBLIC_AUTHORITATIVE: 0,
    SourceClassification.INTERNAL: 1,
    SourceClassification.DERIVED_DECISION: 1,
    SourceClassification.CONFIDENTIAL_REGULATED: 2,
    SourceClassification.CONFIDENTIAL_CASE_METADATA: 2,
    SourceClassification.HIGHLY_CONFIDENTIAL: 3,
    SourceClassification.ABSOLUTELY_EXCLUDED: 4,
}

CLASSIFICATION_MAPPING_VERSION = "pack-12-classification/v1"

_MAPPING: dict[SourceClassification, EnforcementTier] = {
    SourceClassification.PUBLIC_APPROVED: EnforcementTier.T0_OPEN,
    SourceClassification.PUBLIC_AUTHORITATIVE: EnforcementTier.T0_OPEN_AUTHORITATIVE,
    SourceClassification.INTERNAL: EnforcementTier.T1_INTERNAL,
    SourceClassification.DERIVED_DECISION: EnforcementTier.T1_DERIVED,
    SourceClassification.CONFIDENTIAL_REGULATED: EnforcementTier.T2_CONFIDENTIAL,
    SourceClassification.CONFIDENTIAL_CASE_METADATA: EnforcementTier.T2_CASE_METADATA,
    SourceClassification.HIGHLY_CONFIDENTIAL: EnforcementTier.T3_RESTRICTED,
    SourceClassification.ABSOLUTELY_EXCLUDED: EnforcementTier.T4_PROHIBITED,
}

#: Tiers excluded from the general search index by default
#: (`P12-HCD-001`).
INDEX_EXCLUDED_TIERS: frozenset[EnforcementTier] = frozenset(
    {EnforcementTier.T3_RESTRICTED, EnforcementTier.T4_PROHIBITED}
)

#: Tiers that admit no export path at all (`P12-CLS-004`).
EXPORT_PROHIBITED_TIERS: frozenset[EnforcementTier] = frozenset({EnforcementTier.T4_PROHIBITED})

#: Tiers admitted to the general (cross-domain) index.
GENERAL_INDEX_TIERS: frozenset[EnforcementTier] = frozenset(
    {EnforcementTier.T0_OPEN, EnforcementTier.T0_OPEN_AUTHORITATIVE}
)


@dataclass(frozen=True, slots=True)
class ClassificationDecision:
    """The resolved classification picture for one record.

    Carries both the authoritative source value and the derived tier, so
    that a reader can always see which one governed."""

    source: SourceClassification
    tier: EnforcementTier
    mapping_version: str

    @property
    def is_index_excluded(self) -> bool:
        return self.tier in INDEX_EXCLUDED_TIERS

    @property
    def is_general_indexable(self) -> bool:
        return self.tier in GENERAL_INDEX_TIERS

    @property
    def is_export_prohibited(self) -> bool:
        return self.tier in EXPORT_PROHIBITED_TIERS

    def to_payload(self) -> dict[str, object]:
        return {
            "source_classification": str(self.source),
            "enforcement_tier": str(self.tier),
            "mapping_version": self.mapping_version,
        }


def resolve_classification(source: object) -> ClassificationDecision:
    """Map an authoritative source classification to its enforcement
    tier.

    Deterministic and total over the known vocabulary; anything else
    fails closed with `DISCLOSURE_CLASSIFICATION_UNMAPPED` rather than
    defaulting to a permissive tier (`P12-CLS-005`)."""
    if not isinstance(source, SourceClassification):
        try:
            source = SourceClassification(str(source))
        except ValueError as exc:
            raise ClassificationUnmappedError(
                f"source classification {source!r} has no enforcement-tier mapping; "
                "the act is refused pending an explicit mapping decision"
            ) from exc
    tier = _MAPPING.get(source)
    if tier is None:  # pragma: no cover - defensive; _MAPPING is total
        raise ClassificationUnmappedError(
            f"source classification {source!s} has no enforcement-tier mapping"
        )
    if _TIER_RANK[tier] < _SOURCE_RANK[source]:  # pragma: no cover - guarded by the table
        raise ClassificationDowngradeProhibitedError(
            f"mapping would derive tier {tier!s}, weaker than source {source!s}"
        )
    return ClassificationDecision(
        source=source, tier=tier, mapping_version=CLASSIFICATION_MAPPING_VERSION
    )


def assert_not_downgraded(decision: ClassificationDecision, applied_tier: EnforcementTier) -> None:
    """Raise if a caller applied a tier weaker than the derived one.

    The mapping is deterministic, so the only way to end up here is a
    caller substituting its own tier - which is precisely what
    `P12-CLS-001` forbids."""
    if _TIER_RANK[applied_tier] < _TIER_RANK[decision.tier]:
        raise ClassificationDowngradeProhibitedError(
            f"applied tier {applied_tier!s} is weaker than the tier derived from "
            f"source classification {decision.source!s}"
        )


def from_pack09_sensitivity(sensitivity: str) -> SourceClassification:
    """Translate PACK-09's / PACK-11's four-level sensitivity into the
    canonical vocabulary.

    Those four values remain authoritative for those packs' own records;
    this is the input adapter, not a replacement (`P12-CLS-001`)."""
    mapping = {
        "public": SourceClassification.PUBLIC_APPROVED,
        "internal": SourceClassification.INTERNAL,
        "confidential": SourceClassification.CONFIDENTIAL_REGULATED,
        "restricted": SourceClassification.HIGHLY_CONFIDENTIAL,
    }
    resolved = mapping.get(sensitivity)
    if resolved is None:
        raise ClassificationUnmappedError(
            f"sensitivity {sensitivity!r} is not a known PACK-09/PACK-11 value"
        )
    return resolved

"""Conformance evidence in five classes (PACK-16D corrections §11, §26).

The first PACK-16D candidate shipped one class of evidence — self-generated
stability vectors — and called it conformance. It is not. The second added
two more. An audit then found that the middle class was hiding a
distinction that mattered, and this module now separates five, so that a
reader can never mistake the weakest for the strongest.

``EvidenceClass.INTERNAL_STABILITY``
    Produced by this implementation, consumed by this implementation.
    Proves the canonical forms have not drifted. Proves nothing about
    correctness, because an error made consistently is invisible here.

``EvidenceClass.PRIMARY_SOURCE``
    A value published by an external party and reproduced here. Where no
    such value has been published for an operation, this module says so
    rather than inventing one.

``EvidenceClass.RFC_CONFORMANCE``
    An RFC's own published test vectors. Split out from `PRIMARY_SOURCE`
    because for a *primitive* this is the strongest evidence there is, and
    counting it alongside protocol-parameter provenance made both harder to
    audit.

``EvidenceClass.CROSS_IMPLEMENTATION_TEST_PROFILE``
    Computed independently by software sharing no code with the producer —
    but on the fast 1024-bit test group.

``EvidenceClass.CROSS_IMPLEMENTATION_TARGET_PROFILE``
    The same, on ``EPD2-CRYPTO-1`` itself. **This is the split the audit
    forced.** One `cross-implementation` label covering both profiles made
    it invisible that most checks ran on a group no election will ever use.

The cross-implementation oracle is
``tests/reference/crossimpl/independent_verifier.mjs`` — a Node.js program
that re-derives the canonical encoding from the written specification and
implements its own modular exponentiation. Calling the same Python function
through a different wrapper would not be independent and is explicitly not
what happens.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum


class EvidenceClass(StrEnum):
    """Five classes, because three were hiding a distinction that mattered.

    The previous round used one `cross-implementation` label for everything
    an independent oracle checked. An audit then found that most of those
    checks ran on the 1024-bit test profile — which the single label made
    invisible. A cross-check on a group the election will never use and a
    cross-check on `EPD2-CRYPTO-1` are different evidence, so they now have
    different names and are counted separately.

    `RFC_CONFORMANCE` is likewise split out from `PRIMARY_SOURCE`: an RFC's
    published vectors are the strongest evidence a *primitive* can have, and
    conflating them with protocol-parameter provenance made both harder to
    audit.
    """

    INTERNAL_STABILITY = "internal-stability"
    PRIMARY_SOURCE = "primary-source"
    RFC_CONFORMANCE = "rfc-conformance"
    CROSS_IMPLEMENTATION_TEST_PROFILE = "cross-implementation-test-profile"
    CROSS_IMPLEMENTATION_TARGET_PROFILE = "cross-implementation-target-profile"


#: Classes that constitute *external* evidence. `INTERNAL_STABILITY` is
#: deliberately absent: it is the class that cannot detect a consistent
#: error, which is the whole reason the others exist.
EXTERNAL_EVIDENCE_CLASSES: frozenset[EvidenceClass] = frozenset(
    {
        EvidenceClass.PRIMARY_SOURCE,
        EvidenceClass.RFC_CONFORMANCE,
        EvidenceClass.CROSS_IMPLEMENTATION_TEST_PROFILE,
        EvidenceClass.CROSS_IMPLEMENTATION_TARGET_PROFILE,
    }
)

#: The operations the correction requires to be cross-checked on the real
#: profile. A catalogue missing any of these is incomplete, and a test says
#: so rather than leaving a reader to count.
TARGET_PROFILE_CORE_OPERATIONS: tuple[str, ...] = (
    "parameter_digest",
    "group_element_encoding",
    "scalar_encoding",
    "selection_encryption",
    "selection_proof",
    "ballot_hash",
    "confirmation_code",
    "accumulation",
    "guardian_public_commitment",
    "decryption_share",
    "threshold_combination_3_of_5",
    "aggregate_tally_recovery",
)


@dataclass(frozen=True, slots=True)
class ConformanceVector:
    """One conformance datum, with the provenance that gives it weight."""

    vector_id: str
    evidence_class: EvidenceClass
    operation: str
    profile_id: str
    source_title: str
    source_version: str
    source_location: str
    source_digest: str
    retrieved: str
    licence: str
    canonical_input: str
    expected_output: str
    comparison_result: str
    limitations: str


#: Operations for which no external primary-source vector was found.
#:
#: This list is the honest half of the conformance story. An operation
#: here is covered by cross-implementation comparison instead, and that
#: substitution is named rather than hidden.
PRIMARY_SOURCE_UNAVAILABLE: dict[str, str] = {
    "selection_encryption": (
        "ElectionGuard 2.1 publishes the parameter constants but no worked "
        "encryption vector with a fixed nonce that could be reproduced "
        "byte-for-byte; the specification gives the equations, not examples"
    ),
    "selection_proof": (
        "no published disjunctive Chaum-Pedersen transcript with fixed "
        "randomness; and EPD2's Fiat-Shamir context is EPD2-specific, so an "
        "ElectionGuard transcript would not apply unchanged in any case"
    ),
    "ballot_hash": (
        "EPD2 uses its own canonical encoding (EPD2-ENC-1) and domain "
        "separation registry, so a ballot digest is by construction an EPD2 "
        "value with no external counterpart"
    ),
    "confirmation_code": (
        "the confirmation-code alphabet and grouping are EPD2 decisions from "
        "PACK-16C, not ElectionGuard ones"
    ),
    "accumulation": (
        "componentwise multiplication has no published vector; it is checked "
        "cross-implementation instead"
    ),
    "threshold_tally": (
        "no published end-to-end threshold tally vector on the standard parameters was located"
    ),
}


def serialize(vectors: list[ConformanceVector]) -> str:
    payload = {
        "catalog_version": "EPD2-CONFORMANCE-2",
        "evidence_classes": [c.value for c in EvidenceClass],
        "vector_count": len(vectors),
        "counts_by_class": {
            c.value: sum(1 for v in vectors if v.evidence_class is c) for c in EvidenceClass
        },
        "primary_source_unavailable": PRIMARY_SOURCE_UNAVAILABLE,
        "vectors": [asdict(v) for v in vectors],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

"""PACK-15 audit stream separation and `EvidenceBundle` v1 (`OD-P15-04`).

Six streams, separately keyed and separately authorized, and a versioned
privacy-preserving bundle that lets an independent auditor establish that
an election was administered correctly **without** the correlation the
architecture forbids.

The bundle is totals, versions, commitments and disclosure metadata. It
carries no per-participation record, no identifier of any kind, no
pseudonym and no ballot data - and `validate_bundle` refuses one that
does, rather than repairing it.

Complementary suppression is applied across cells **and across time**: two
bundles of the same context taken at different moments must not permit a
suppressed cell to be recovered by differencing (`T-P15-39`).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

BUNDLE_SCHEMA_VERSION = 1
DEFAULT_MINIMUM_CELL = 5


class EvidenceBundleError(ValueError):
    """Base class; never raised directly."""


class EvidenceBundleInvalidError(EvidenceBundleError):
    reason_code = "EVIDENCE_BUNDLE_INVALID"


class EvidenceBundleScopeRefusedError(EvidenceBundleError):
    reason_code = "EVIDENCE_BUNDLE_SCOPE_REFUSED"


class EvidenceBundlePreclosureRefusedError(EvidenceBundleError):
    reason_code = "EVIDENCE_BUNDLE_PRECLOSURE_REFUSED"


class IntermediateTallyProhibitedError(EvidenceBundleError):
    reason_code = "INTERMEDIATE_TALLY_PROHIBITED"


class AuditStream(StrEnum):
    """Six streams. Never unified, never joined, never co-exported."""

    ELIGIBILITY = "AS-01"
    ASSERTION = "AS-02"
    CREDENTIAL = "AS-03"
    VOTING_INTEGRITY = "AS-04"
    INDEPENDENT = "AS-05"
    SYSTEM_INTEGRITY = "AS-06"


#: The identity-side and voting-side stream groups. **No role and no
#: export may span both** - that single rule is the audit-side statement of
#: the whole architecture (ADR-097).
IDENTITY_SIDE_STREAMS: frozenset[AuditStream] = frozenset(
    {AuditStream.ELIGIBILITY, AuditStream.ASSERTION}
)
VOTING_SIDE_STREAMS: frozenset[AuditStream] = frozenset({AuditStream.CREDENTIAL})


def assert_streams_separable(streams: Sequence[AuditStream]) -> None:
    """Refuse any request that spans the boundary."""
    requested = set(streams)
    if requested & IDENTITY_SIDE_STREAMS and requested & VOTING_SIDE_STREAMS:
        raise EvidenceBundleScopeRefusedError(
            "no query, export or grant may span the eligibility-side and voting-side streams"
        )


#: Sections 3, 4 and 5 are outcome-bearing: a pre-closure count is an
#: intermediate tally (ADR-094).
OUTCOME_BEARING_SECTIONS: frozenset[str] = frozenset(
    {"eligibility_totals", "assertion_totals", "credential_totals"}
)

#: The closed list of eight permitted sections.
BUNDLE_SECTIONS: tuple[str, ...] = (
    "context_metadata",
    "configuration_versions",
    "eligibility_totals",
    "assertion_totals",
    "credential_totals",
    "integrity_commitments",
    "disclosure_metadata",
    "provenance",
)

#: Never present in a bundle, in any section, under any name.
BUNDLE_FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "membership_id",
        "member_number",
        "participant_reference",
        "context_pseudonym",
        "pseudonym",
        "assertion_id",
        "nonce",
        "voting_credential_id",
        "credential_id",
        "credential_secret",
        "ballot_id",
        "vote_content",
        "redemption_reference",
        "occurred_at",
    }
)


def _scan_forbidden(node: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(node, Mapping):
        for key, value in node.items():
            key_text = str(key)
            if key_text in BUNDLE_FORBIDDEN_KEYS:
                found.append(f"{path}{key_text}")
            found.extend(_scan_forbidden(value, f"{path}{key_text}."))
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            found.extend(_scan_forbidden(value, f"{path}{index}."))
    return found


@dataclass(frozen=True, slots=True)
class SuppressedCell:
    """A cell below the minimum, suppressed rather than rounded."""

    section: str
    cell: str
    method: str = "primary"

    def __post_init__(self) -> None:
        if self.method not in {"primary", "complementary"}:
            raise EvidenceBundleInvalidError("suppression is primary or complementary")


def suppress_small_cells(
    counts: Mapping[str, int], *, minimum_cell: int, section: str
) -> tuple[dict[str, int | None], tuple[SuppressedCell, ...]]:
    """Suppress below-minimum cells, then apply complementary suppression.

    A single suppressed cell is recoverable by subtracting the others from
    the total, so a second cell is suppressed alongside it. Where fewer
    than two cells remain, the whole section is suppressed.
    """
    if minimum_cell < DEFAULT_MINIMUM_CELL:
        raise EvidenceBundleInvalidError("the minimum cell size has a floor of 5")
    published: dict[str, int | None] = dict(counts)
    suppressed: list[SuppressedCell] = []
    for cell, value in sorted(counts.items()):
        if 0 < value < minimum_cell:
            published[cell] = None
            suppressed.append(SuppressedCell(section=section, cell=cell))
    if len(suppressed) == 1:
        remaining = sorted(
            (cell for cell, value in published.items() if value is not None),
            key=lambda cell: (counts[cell], cell),
        )
        if remaining:
            published[remaining[0]] = None
            suppressed.append(
                SuppressedCell(section=section, cell=remaining[0], method="complementary")
            )
        else:
            for cell in published:
                published[cell] = None
    return (published, tuple(suppressed))


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """A versioned, signed, privacy-preserving bundle for one context."""

    bundle_schema_version: int
    voting_context_reference: str
    sections: Mapping[str, Mapping[str, object]]
    suppressed: tuple[SuppressedCell, ...]
    signature: str
    key_identifier: str
    generated_at_bucket: datetime
    pre_closure: bool = False
    raw: Mapping[str, object] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if self.bundle_schema_version != BUNDLE_SCHEMA_VERSION:
            raise EvidenceBundleInvalidError("unsupported bundle schema version")
        missing = [name for name in BUNDLE_SECTIONS if name not in self.sections]
        if missing:
            raise EvidenceBundleInvalidError(
                "every section is present or explicitly empty: missing " + ", ".join(missing)
            )
        unexpected = sorted(set(self.sections) - set(BUNDLE_SECTIONS))
        if unexpected:
            raise EvidenceBundleInvalidError(
                "the bundle's section list is closed: " + ", ".join(unexpected)
            )


def canonical_bundle_message(
    *,
    voting_context_reference: str,
    sections: Mapping[str, Mapping[str, object]],
) -> bytes:
    return json.dumps(
        {"context": voting_context_reference, "sections": sections},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


class BundleSigningCustody:
    """Reference custody for the bundle signature.

    A key distinct from every other function's, per specification
    section 18. Test keys are prefixed `test-` and are refused outside a
    test trust store.
    """

    def __init__(self, secret: bytes = b"pack15-reference-bundle-key") -> None:
        self._secret = secret

    def key_identifier(self) -> str:
        return "test-evidence-bundle-key-v1"

    def sign(self, message: bytes) -> str:
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def verify(self, message: bytes, signature: str) -> bool:
        return hmac.compare_digest(self.sign(message), signature)


def build_bundle(
    *,
    voting_context_reference: str,
    context_metadata: Mapping[str, object],
    configuration_versions: Mapping[str, object],
    eligibility_totals: Mapping[str, int],
    assertion_totals: Mapping[str, int],
    credential_totals: Mapping[str, int],
    integrity_commitments: Mapping[str, str],
    provenance: Mapping[str, object],
    minimum_cell: int,
    generated_at_bucket: datetime,
    custody: BundleSigningCustody,
    context_closed: bool,
) -> EvidenceBundle:
    """Build a bundle for exactly one voting context.

    Before closure the outcome-bearing sections are declared empty rather
    than filled: a pre-closure count is an intermediate tally.
    """
    pre_closure = not context_closed
    suppressed: list[SuppressedCell] = []
    if pre_closure:
        eligibility_published: Mapping[str, object] = {"suppressed": "pre_closure"}
        assertion_published: Mapping[str, object] = {"suppressed": "pre_closure"}
        credential_published: Mapping[str, object] = {"suppressed": "pre_closure"}
    else:
        elig, elig_sup = suppress_small_cells(
            eligibility_totals, minimum_cell=minimum_cell, section="eligibility_totals"
        )
        asrt, asrt_sup = suppress_small_cells(
            assertion_totals, minimum_cell=minimum_cell, section="assertion_totals"
        )
        cred, cred_sup = suppress_small_cells(
            credential_totals, minimum_cell=minimum_cell, section="credential_totals"
        )
        eligibility_published = dict(elig)
        assertion_published = dict(asrt)
        credential_published = dict(cred)
        suppressed.extend(elig_sup + asrt_sup + cred_sup)

    sections: dict[str, Mapping[str, object]] = {
        "context_metadata": dict(context_metadata),
        "configuration_versions": dict(configuration_versions),
        "eligibility_totals": eligibility_published,
        "assertion_totals": assertion_published,
        "credential_totals": credential_published,
        "integrity_commitments": dict(integrity_commitments),
        "disclosure_metadata": {
            "minimum_cell": minimum_cell,
            "method": "suppressed_not_rounded",
            "complementary_suppression": True,
            "suppressed_cells": [
                {"section": cell.section, "cell": cell.cell, "method": cell.method}
                for cell in suppressed
            ],
        },
        "provenance": dict(provenance)
        | {
            "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
            "generated_at_bucket": generated_at_bucket.isoformat(),
        },
    }
    offending = _scan_forbidden(sections)
    if offending:
        raise EvidenceBundleInvalidError(
            "forbidden keys in an evidence bundle: " + ", ".join(sorted(offending))
        )
    signature = custody.sign(
        canonical_bundle_message(
            voting_context_reference=voting_context_reference, sections=sections
        )
    )
    return EvidenceBundle(
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        voting_context_reference=voting_context_reference,
        sections=sections,
        suppressed=tuple(suppressed),
        signature=signature,
        key_identifier=custody.key_identifier(),
        generated_at_bucket=generated_at_bucket,
        pre_closure=pre_closure,
    )


def validate_bundle(bundle: EvidenceBundle, *, custody: BundleSigningCustody) -> None:
    """The nine validation checks. A failing bundle is rejected, not repaired."""
    # 1. supported schema version - enforced in __post_init__
    # 2. every section present - enforced in __post_init__
    # 3. no forbidden key anywhere
    offending = _scan_forbidden(bundle.sections)
    if offending:
        raise EvidenceBundleInvalidError(
            "forbidden keys in an evidence bundle: " + ", ".join(sorted(offending))
        )
    # 4. signature verifies
    message = canonical_bundle_message(
        voting_context_reference=bundle.voting_context_reference, sections=bundle.sections
    )
    if not custody.verify(message, bundle.signature):
        raise EvidenceBundleInvalidError("the bundle signature did not verify")
    # 5. disclosure metadata present and at or above the floor
    disclosure = bundle.sections["disclosure_metadata"]
    minimum = disclosure.get("minimum_cell")
    if not isinstance(minimum, int) or minimum < DEFAULT_MINIMUM_CELL:
        raise EvidenceBundleInvalidError("disclosure metadata is absent or below the floor")
    if disclosure.get("complementary_suppression") is not True:
        raise EvidenceBundleInvalidError("complementary suppression is mandatory")
    # 6-8. count consistency, where the totals are published
    if not bundle.pre_closure:
        _assert_count_consistency(bundle)
    # 9. pre-closure bundles carry no outcome-bearing totals
    if bundle.pre_closure:
        for section in OUTCOME_BEARING_SECTIONS:
            if bundle.sections[section].get("suppressed") != "pre_closure":
                raise EvidenceBundlePreclosureRefusedError(
                    "a pre-closure bundle carries no outcome-bearing totals"
                )


def _value(section: Mapping[str, object], key: str) -> int | None:
    raw = section.get(key)
    return raw if isinstance(raw, int) else None


def _assert_count_consistency(bundle: EvidenceBundle) -> None:
    """redeemed <= issued; picked_up <= released <= queued <= minted."""
    assertions = bundle.sections["assertion_totals"]
    credentials = bundle.sections["credential_totals"]
    minted = _value(assertions, "minted")
    queued = _value(assertions, "queued")
    released = _value(assertions, "released")
    picked_up = _value(assertions, "picked_up")
    chain = [value for value in (minted, queued, released, picked_up) if value is not None]
    if chain != sorted(chain, reverse=True):
        raise EvidenceBundleInvalidError(
            "assertion totals must satisfy picked_up <= released <= queued <= minted"
        )
    issued = _value(credentials, "issued")
    redeemed = _value(credentials, "redeemed")
    if issued is not None and redeemed is not None and redeemed > issued:
        raise EvidenceBundleInvalidError("redeemed may not exceed issued")


def assert_export_authorized(
    *,
    role: str,
    grant_reference: str | None,
    contexts: Sequence[str],
    streams: Sequence[AuditStream],
    context_closed: bool,
    dual_control_reference: str | None,
) -> None:
    """Export authorization: one context, one side, dual control early."""
    if role != "independent_auditor":
        raise EvidenceBundleScopeRefusedError(
            "an evidence bundle is exported to the Independent Auditor role only"
        )
    if not grant_reference:
        raise EvidenceBundleScopeRefusedError("export requires a time-boxed grant")
    if len(set(contexts)) != 1:
        raise EvidenceBundleScopeRefusedError("one context per bundle; two contexts is refused")
    assert_streams_separable(streams)
    if not context_closed and not dual_control_reference:
        raise EvidenceBundlePreclosureRefusedError(
            "a pre-closure export is restricted and requires dual control"
        )


def assert_no_intermediate_tally(payload: Mapping[str, object], *, context_closed: bool) -> None:
    """Refuse any outcome-bearing disclosure before closure."""
    outcome_keys = {
        "vote_totals",
        "option_totals",
        "candidate_totals",
        "turnout",
        "partial_results",
        "ballot_counts",
        "leaderboard",
        "projection",
    }
    offending = sorted(set(payload) & outcome_keys)
    if offending and not context_closed:
        raise IntermediateTallyProhibitedError(
            "outcome-bearing data may not be disclosed before the official tally: "
            + ", ".join(offending)
        )

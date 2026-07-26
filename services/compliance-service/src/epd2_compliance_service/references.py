"""Stable typed references PACK-09 exports to later packs.

Architecture & Domain Framework 0.8.1 section 13.1 requires PACK-09 to
publish "stable references for PACK-10/11/19/21-24: `LegalCaseRef`,
`DeadlineRef`, `NoticeEffectRef`, `HoldRef`, `RecordClassRef`", and
section 7's dependency map names the same set as PACK-09's outward
interface. This module is that interface.

Every type here is a *reference*, not an entity: a frozen, slotted
dataclass carrying an id, the organizational scope the referenced object
lives in, and nothing else. That shape is deliberate and load-bearing:

- **A reference carries its scope.** A downstream pack that holds a
  `LegalCaseRef` cannot use it to reach into another organization,
  because the scope travels with the id and PACK-09's own guards compare
  it (Framework hard invariant 13, "региональный доступ работает по
  default deny").
- **A reference carries no content.** No name, no status, no payload. A
  later pack that wants the object's state has to ask PACK-09 for it and
  pass a `RequestContext`; it cannot infer state from a reference it was
  handed (Framework 2.2: "cache / read model не является source of
  truth").
- **A reference is never a person.** `CasePartyRef` wraps a per-case
  handle minted by `casework.mint_case_party_reference`; there is no
  `PersonRef`, `UserRef` or `MemberRef` in this module and there must
  never be one (Framework hard invariant 1, "нет глобального user ID").

## Placeholders

`EvidenceRef`, `DocumentRef` and `NoticeProofPackageRef` are
**placeholders for PACK-11**. PACK-09 stores no document bytes and no
evidence content (Framework 13.2); these types exist so a PACK-09 case,
filing, hearing or notice can *point at* material PACK-11 will own,
without PACK-09 acquiring it. Their `kind` field is an open string
precisely because PACK-11 — not PACK-09 — will define the taxonomy.

`AdmissionDecisionRef` is an **interface-only placeholder for PACK-19**.
PACK-09 implements no candidacy, nomination or ballot-admission entity
(Framework 13.2 and the explicit scope exclusion); this reference exists
so PACK-19 can later link an admission decision to a PACK-09 case,
deadline and notice effect without PACK-09 modelling admission itself.

`FinanceEvidenceRef` is the same for PACK-10, named in Framework section
7's dependency map.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ScopedRef:
    """Base shape shared by every reference this module exports: an
    identifier plus the organization it belongs to.

    Subclasses add nothing but their own name. The name matters — a
    `DeadlineRef` and a `HoldRef` are not interchangeable even though
    both are (UUID, UUID) pairs — and mypy enforces it at every call
    site."""

    id: UUID
    organization_id: UUID


@dataclass(frozen=True, slots=True)
class LegalCaseRef(ScopedRef):
    """Points at a `casework.LegalCase`. Consumed by PACK-10 (finance
    cases), PACK-11 (documents attached to a case), PACK-19 (candidacy
    appeals), PACK-23 (complaints) and PACK-24 (investigations)."""


@dataclass(frozen=True, slots=True)
class FilingRef(ScopedRef):
    """Points at an entry in a case's append-only docket. Consumed by
    PACK-11, which will own the documents a filing references."""


@dataclass(frozen=True, slots=True)
class DeadlineRef(ScopedRef):
    """Points at a `domain.ProceduralDeadline`. Consumed by PACK-10,
    PACK-19, PACK-21 and PACK-23."""


@dataclass(frozen=True, slots=True)
class NoticeRef(ScopedRef):
    """Points at a `notices.OfficialNotice` - the notice document-shape
    itself, which is not yet a legal effect."""


@dataclass(frozen=True, slots=True)
class ServiceAttemptRef(ScopedRef):
    """Points at one recorded attempt to serve a notice. Carries no
    legal effect on its own - see `NoticeEffectRef`."""


@dataclass(frozen=True, slots=True)
class NoticeEffectRef(ScopedRef):
    """Points at a `notices.NoticeEffectDecision` - the ONLY object in
    this repository that can start a procedural deadline.

    Framework hard invariants 39 and 40: delivery/read telemetry never
    establishes legally effective notice; legal notice requires an
    authorized object, a valid method, proof and a governed effect
    decision. PACK-22 will implement channels and will consume this
    reference; it will not produce legal effect itself."""


@dataclass(frozen=True, slots=True)
class NoticeProofPackageRef(ScopedRef):
    """Placeholder for the evidence-grade service proof package PACK-11
    will own (Framework AGR-08: "evidence-grade service package"). PACK-09
    records that a package exists and where, never its contents."""


@dataclass(frozen=True, slots=True)
class DeadlineTriggerRef(ScopedRef):
    """Points at the recorded fact that a specific governed trigger
    started a specific deadline, exactly once."""


@dataclass(frozen=True, slots=True)
class HoldRef(ScopedRef):
    """Points at a `domain.LegalHold`. Consumed by PACK-10, PACK-11 and
    PACK-24. Framework section 11: "legal hold распространяется на
    релевантные replicas / indexes / exports"."""


@dataclass(frozen=True, slots=True)
class RecordClassRef(ScopedRef):
    """Points at a `domain.RecordClass` - the classification that binds a
    record to its retention schedule, custodian and disposition
    authority. Consumed by PACK-10, PACK-11 and PACK-12."""


@dataclass(frozen=True, slots=True)
class RemedyRef(ScopedRef):
    """Points at a `casework.Remedy` - the appeal/review route attached
    to a procedural decision. Consumed by PACK-19 and PACK-23."""


@dataclass(frozen=True, slots=True)
class ProceduralDecisionRef(ScopedRef):
    """Points at a `casework.ProceduralDecision`."""


@dataclass(frozen=True, slots=True)
class ProcessingActivityRef(ScopedRef):
    """Points at a `domain.ProcessingActivity` in the processing
    registry."""


@dataclass(frozen=True, slots=True)
class DPIARef(ScopedRef):
    """Points at a `dataprotection.DataProtectionImpactAssessment`."""


@dataclass(frozen=True, slots=True)
class ProcessingActivationDecisionRef(ScopedRef):
    """Points at the governed decision that did (or did not) activate a
    processing activity."""


@dataclass(frozen=True, slots=True)
class CasePartyRef(ScopedRef):
    """Points at a `casework.CaseParty`.

    The wrapped id is a per-case handle minted by
    `casework.mint_case_party_reference` - meaningless, never reused
    across cases, and not resolvable to a person by this or any other
    service. It is emphatically NOT a user, member, account or identity
    reference, and there is no type in this module that is."""


@dataclass(frozen=True, slots=True)
class JurisdictionRef(ScopedRef):
    """Points at a `casework.JurisdictionDetermination` - the recorded
    decision that a specific competent authority has jurisdiction over a
    specific case kind in a specific scope."""


# ---------------------------------------------------------------------------
# Placeholders owned by later packs
# ---------------------------------------------------------------------------


class PlaceholderOwner(StrEnum):
    """Which pack will own the object a placeholder reference points at.

    Recorded on the reference so a reviewer can tell at a glance that a
    PACK-09 field is a forward declaration rather than something PACK-09
    implements."""

    PACK_10_FINANCE = "pack-10-finance"
    PACK_11_DOCUMENTS = "pack-11-documents"
    PACK_19_CANDIDACY = "pack-19-candidacy"
    PACK_21_ASSEMBLIES = "pack-21-assemblies"
    PACK_22_COMMUNICATIONS = "pack-22-communications"


@dataclass(frozen=True, slots=True)
class PlaceholderRef:
    """A forward reference to an object a later pack will own.

    Deliberately *not* a `ScopedRef` subclass: a placeholder carries an
    opaque `external_reference` string rather than a UUID, because
    PACK-09 does not get to decide the identifier shape of a domain it
    does not own. It carries `owner` so the deferral is explicit in data,
    and `kind` as an open string because the owning pack defines the
    taxonomy."""

    owner: PlaceholderOwner
    kind: str
    external_reference: str
    organization_id: UUID

    def __post_init__(self) -> None:
        _require_text(self.kind, "kind")
        _require_text(self.external_reference, "external_reference")


@dataclass(frozen=True, slots=True)
class EvidenceRef(PlaceholderRef):
    """Placeholder for PACK-11's evidence object. PACK-09 records that a
    filing, hearing or decision *cites* evidence, never the evidence
    itself (Framework hard invariant 44: evidence admission requires
    provenance, integrity, custody, relevance decision and preserved
    version - all PACK-11 concerns)."""


@dataclass(frozen=True, slots=True)
class DocumentRef(PlaceholderRef):
    """Placeholder for PACK-11's governed document. Framework hard
    invariant 43: a stored document is not an authoritative record, a
    signed original, admitted evidence or a publishable rendition -
    PACK-09 asserts none of those about anything it points at."""


@dataclass(frozen=True, slots=True)
class FinanceEvidenceRef(PlaceholderRef):
    """Placeholder for PACK-10's finance evidence, named in Framework
    section 7's dependency map."""


@dataclass(frozen=True, slots=True)
class AdmissionDecisionRef(PlaceholderRef):
    """Interface-only placeholder for PACK-19's admission decision.

    PACK-09 implements no candidacy, nomination or ballot-admission
    entity whatsoever. This exists so PACK-19 can later attach an
    admission decision to a PACK-09 case, deadline and notice effect.
    Framework hard invariant 35: nomination does not create ballot
    admission; admission is a separate audited decision - made by
    PACK-19, not here."""


@dataclass(frozen=True, slots=True)
class MinutesRef(PlaceholderRef):
    """Placeholder for the minutes/record of a hearing. Owned by PACK-11
    (as a document) or PACK-21 (for assemblies); PACK-09 stores only the
    reference."""

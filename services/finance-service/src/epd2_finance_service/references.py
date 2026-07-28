"""Finance Service outward references and the boundary refusals that keep
foreign concepts out (PACK-10 sections 9.7, 11 and 12; canon 0.8.0
sections 19f.15, 19f.21, 19f.22 and 19f.23).

Two directions meet in one module, and conflating them is the mistake
this docstring exists to prevent:

- **Inward-facing.** The typed pointers this bounded context holds at
  records other contexts own - a PACK-09 legal case, legal hold, record
  class and notice-effect decision, a PACK-11 document, a PACK-35
  lobbying contact, a PACK-08 organizational scope. Every one is an
  opaque pointer plus the minimum typed metadata finance genuinely
  needs. None carries the referenced record's content, and none carries
  an assertion about it: holding a reference to evidence does not make
  finance the owner of the evidence (`ФИН-21`, canon 19f.22).
- **Outward-facing.** The references *other* packs may hold at finance
  records (spec 11.1 point 2). Same shape, opposite direction: an
  identifier plus the organizational scope, and no content, so a
  PACK-09 case can cite a finance record without PACK-09 acquiring it.

**Why finance re-declares PACK-09's reference types instead of importing
them.** Spec section 11 says the reference types consumed here are
"PACK-09's own `references.py` exports". Literally importing
`epd2_compliance_service.references` would give `finance-service` an
undeclared dependency on another service package - its `pyproject.toml`
declares `epd2-core` and `epd2-audit-core` and nothing else - and would
make a cross-service *code* edge out of what canon 19f.22 says must be a
typed reference and a published interface (`ФИН-44`). The shapes below
are therefore finance-side mirrors, deliberately structurally identical
to PACK-09's `ScopedRef` and `PlaceholderRef`, carrying PACK-09's
identifiers exactly as `domain.RetentionBinding`,
`reporting.ReportingObligation` and `reporting.ExternalAcceptanceReference`
already carry them: as opaque strings. Spec 11.1 point 3 records the
typed-alias option; it is a PACK-09-side change and is not taken here.

**What is deliberately absent.** No reference type in this module has an
`is_authentic`, `is_signed`, `is_admitted`, `is_valid` or
`is_publishable` field, and none ever will (spec 12: the mechanism is
structural, not a naming convention). `LegalHoldReference` carries no
`is_active`, because hold state is re-read immediately before every
disposal-relevant action and never cached (`ФИН-22`, spec 11). There is
no reference type here that resolves to a person, and the four
assertion functions at the foot of the module make the remaining
boundaries enforceable rather than merely documented.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_finance_service.domain import (
    FinancePartyHandle,
    HandlePurpose,
    OrganizationalScopeRef,
    PolicyBinding,
    RetentionBinding,
    require_timezone,
)
from epd2_finance_service.exceptions import (
    EvidenceAssertionUnavailableError,
    EvidenceReferenceMissingError,
    ForbiddenIdentityLinkageError,
    RetentionBindingMissingError,
)
from epd2_finance_service.records import (
    assert_not_lobbying_subject as _assert_not_lobbying_subject,
)

# ---------------------------------------------------------------------------
# Shared shape
# ---------------------------------------------------------------------------


def _require_reference_text(value: str, field_name: str) -> None:
    """Structural non-emptiness check for a reference field.

    Raises `EvidenceReferenceMissingError` rather than the generic
    field-validation code `domain` uses, because every string this module
    validates *is* a reference, and an empty one is precisely "a required
    reference is absent" (`ФИН-40`: the refusal names what went wrong)."""
    if not value or not value.strip():
        raise EvidenceReferenceMissingError(f"{field_name} must be a non-empty reference")


class ReferenceOwner(StrEnum):
    """Which context owns the record a reference points at.

    Recorded on the reference itself, so a reviewer can tell at a glance
    that a finance field is a pointer into somebody else's domain rather
    than something PACK-10 implements. It is a `ClassVar` on each type
    below and not a constructor argument: an owner a caller could pass in
    is an owner a caller could get wrong, and the whole point of these
    types is that the boundary is not negotiable at the call site."""

    PACK_08_ORGANIZATION = "pack-08-organization"
    PACK_09_COMPLIANCE = "pack-09-compliance"
    PACK_10_FINANCE = "pack-10-finance"
    PACK_11_DOCUMENTS = "pack-11-documents"
    PACK_35_LOBBYING = "pack-35-lobbying"


@dataclass(frozen=True, slots=True)
class ForeignRecordReference:
    """The shape every inward reference in this module shares: an opaque
    external reference plus the organizational scope it lives in.

    Mirrors PACK-09's `PlaceholderRef` on purpose. The identifier is a
    string and not a `UUID` because PACK-10 does not get to decide the
    identifier shape of a domain it does not own, and the scope travels
    with it because a reference that lost its scope would be a reference
    usable to reach into another organization (`ФИН-03`, `ФИН-04`).

    `owner` is an unassigned `ClassVar` here: this base is never
    instantiated directly, and a subclass that forgot to declare its
    owner fails on attribute access rather than silently claiming
    finance's own."""

    owner: ClassVar[ReferenceOwner]

    external_reference: str
    scope: OrganizationalScopeRef

    def __post_init__(self) -> None:
        _require_reference_text(self.external_reference, "external_reference")

    def to_payload(self) -> dict[str, object]:
        """The wire form: owner and opaque reference, never the scope's
        internals beyond its id. Deterministic and content-free."""
        return {
            "owner": str(self.owner),
            "external_reference": self.external_reference,
            "organization_id": str(self.scope.organization_id),
        }


# ---------------------------------------------------------------------------
# PACK-09: cases, holds, record classes, notice effects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LegalCaseReference(ForeignRecordReference):
    """A PACK-09 governed procedural case (`LegalCaseRef`).

    Held where a contribution escalates: `records.FinanceContribution.escalate`
    demands a case reference precisely because an escalation naming no
    case is an unresolved record with no owner. What finance may do with
    it is cite it - the case's own lifecycle, admissibility, hearings,
    decisions and remedies stay PACK-09's (spec 11, canon 19f.22), so
    this type carries no case state, no case kind decided here and no
    party. A `CasePartyRef` equivalent is absent by design: it would be
    the one reference in this module that pointed at a person."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


@dataclass(frozen=True, slots=True)
class LegalHoldReference(ForeignRecordReference):
    """A PACK-09 legal hold (`HoldRef`) asserted over finance records.

    **Carries no `is_active` and no `held_until`, deliberately.** Canon
    19f.22 requires hold state to be re-read immediately before every
    disposal-relevant action and never cached; a boolean on this object
    would be a cache, and a stale one would authorise exactly the
    destruction `ФИН-22` forbids. `observed_at` records when this pointer
    was recorded on a finance record - not when the hold was last checked,
    which is a question only PACK-09 can answer at the moment it is
    asked."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE

    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        ForeignRecordReference.__post_init__(self)
        if self.observed_at is not None:
            require_timezone(self.observed_at, context="LegalHoldReference.observed_at")


@dataclass(frozen=True, slots=True)
class RetentionClassReference(ForeignRecordReference):
    """A PACK-09 record class (`RecordClassRef`).

    Every governed finance record must name one (`ФИН-24` in the spec's
    numbering of this binding, reason code
    `FINANCE_RETENTION_BINDING_MISSING`): a record with no record class
    has no retention schedule, no custodian and no disposition authority,
    and nothing in this service may invent one for it. Retention and
    legal-hold *semantics* stay PACK-09's; PACK-10 stores the binding and
    the date it was bound (`ФИН-22`, `ФИН-23`)."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE

    def as_binding(self, *, bound_at: datetime) -> RetentionBinding:
        """Produce the `domain.RetentionBinding` a governed record stores.

        The conversion lives here rather than on `RetentionBinding` so the
        domain value object stays free of any knowledge of who owns record
        classes; `require_retention_binding` below is the check that the
        result actually reached the record."""
        return RetentionBinding(
            record_class_reference=self.external_reference,
            bound_at=require_timezone(bound_at, context="RetentionClassReference.as_binding"),
        )


@dataclass(frozen=True, slots=True)
class NoticeEffectReference(ForeignRecordReference):
    """A PACK-09 `NoticeEffectDecision` (`NoticeEffectRef`) - the **only**
    authoritative input to the report acceptance transition.

    Canon 19f.17 and `ФИН-26`/`ФИН-27`: submission is not acceptance, and
    delivery, receipt, read and acknowledgement telemetry is never a legal
    act. Those four are recorded as their own facts by
    `reporting.ExternalAcceptanceReference`, whose `kind` decides whether
    the transition may run; this reference type is the pointer at the
    governed decision behind an authoritative one.

    It carries no verdict field. A verdict stored here would be finance
    restating a PACK-09 determination in its own words, and a restated
    determination is one that can disagree with the original."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_09_COMPLIANCE


# ---------------------------------------------------------------------------
# PACK-11: documents
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentReference(ForeignRecordReference):
    """A PACK-11 governed document: identity and version only.

    **No bytes, no extracted text, no rendition, no signature value, no
    custody chain** (spec 12, `ФИН-21`). `kind` is an open string because
    PACK-11 - not PACK-10 - defines the document taxonomy;
    `domain.EvidenceKind` is finance's *expectation* of what kind of
    document a record should have, which is a different statement and
    lives on `domain.EvidenceReference`.

    `version_reference` is the one piece of typed metadata beyond identity
    that finance genuinely needs: a report cites the document version it
    was prepared against, and "the document" without a version is a moving
    target. It is still opaque - a pointer at PACK-11's version, never a
    number this service increments.

    There is no `is_authentic`, `is_signed`, `is_admitted`, `is_valid` or
    `is_publishable` field, and `assert_no_document_content` below refuses
    any payload that grew one. Where a finance decision needs such an
    assertion, it fails closed with
    `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` rather than assuming."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_11_DOCUMENTS

    kind: str = ""
    version_reference: str | None = None

    def __post_init__(self) -> None:
        ForeignRecordReference.__post_init__(self)
        _require_reference_text(self.kind, "kind")
        if self.version_reference is not None:
            _require_reference_text(self.version_reference, "version_reference")

    def to_payload(self) -> dict[str, object]:
        payload = ForeignRecordReference.to_payload(self)
        payload["kind"] = self.kind
        payload["version_reference"] = self.version_reference
        return payload


# ---------------------------------------------------------------------------
# PACK-35: lobbying, meetings, access
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LobbyingContactReference(ForeignRecordReference):
    """A **cross-reference only** to a PACK-35 contact, meeting or access
    record. Never owned here, never resolved here, never a finance record.

    Canon 19f.9 and `ФИН-20`: PACK-10 records a measurable financial value
    attributable to a party organization; PACK-35 records a contact,
    meeting, access or influence relationship with no financial value
    recorded. A meeting that produced a sponsorship yields two records
    linked by one typed reference - this one - and neither owns the other.

    `contact_kind` is an open PACK-35 string and is *not* validated
    against `records.PACK_35_SUBJECT_KINDS`: that set exists to refuse a
    PACK-35 subject being recorded **as** a finance record, and this type
    is the sanctioned opposite - the one place a PACK-35 kind is
    legitimate, because here it labels somebody else's record rather than
    one of ours. Validating it against the same set would refuse exactly
    the integration canon 19f.9 requires."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_35_LOBBYING

    contact_kind: str = ""

    def __post_init__(self) -> None:
        ForeignRecordReference.__post_init__(self)
        _require_reference_text(self.contact_kind, "contact_kind")

    def to_payload(self) -> dict[str, object]:
        payload = ForeignRecordReference.to_payload(self)
        payload["contact_kind"] = self.contact_kind
        return payload


# ---------------------------------------------------------------------------
# PACK-08: the outward form of an organizational scope
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrganizationalScopeReference:
    """The outward form of `domain.OrganizationalScopeRef`.

    **Why a second type for the same two values.**
    `OrganizationalScopeRef` is the *inward* value: it is what every guard
    in this service compares (`assert_matches`), and it raises on an
    undetermined scope so that default-deny is structural (`ФИН-04`).
    That behaviour is exactly wrong on the way out - a projection or an
    event payload emits a scope, it does not authorise against one - and a
    single type doing both invites a reader to believe that emitting a
    scope checked something. This type therefore emits and never
    compares: it has no `assert_matches`, and getting the inward value
    back requires the explicit `as_scope()` call.

    Deliberately not a `ForeignRecordReference` subclass: PACK-08 scopes
    are identified by UUID throughout this repository, and wrapping one in
    an opaque string would lose that."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_08_ORGANIZATION

    organization_id: UUID
    scope_kind: str = "organization"

    def __post_init__(self) -> None:
        _require_reference_text(self.scope_kind, "scope_kind")

    @classmethod
    def from_scope(cls, scope: OrganizationalScopeRef) -> OrganizationalScopeReference:
        """The outward form of an inward scope."""
        return cls(organization_id=scope.organization_id, scope_kind=scope.scope_kind)

    def as_scope(self) -> OrganizationalScopeRef:
        """Back to the inward value, for a caller that must now compare.

        Explicit rather than implicit: the conversion is where a reader
        should notice that authorisation is about to happen."""
        return OrganizationalScopeRef(
            organization_id=self.organization_id, scope_kind=self.scope_kind
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "owner": str(self.owner),
            "organization_id": str(self.organization_id),
            "scope_kind": self.scope_kind,
        }


# ---------------------------------------------------------------------------
# PACK-10's own outward references (spec 11.1 point 2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PolicyVersionReference:
    """A pointer at one version of a `FinancePolicy` (spec section 13).

    Finance owns these, so the identifier is typed rather than opaque -
    but the reference still carries no rule, no threshold and no
    classification table. That is the point: a protected decision stores
    the *binding* it used (`domain.PolicyBinding`), and a projection
    carries this pointer so a reader can ask which version produced a
    figure, without the projection becoming a second, drifting copy of
    the policy itself (`ФИН-23`).

    `effective_from` is absent here on purpose. `PolicyBinding` carries
    it because a decision must record the date it applied; a *reference*
    that carried it would let a reader compute applicability from the
    reference alone, which is a policy evaluation this module does not
    get to perform."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_10_FINANCE

    policy_kind: str
    policy_id: str
    policy_version: str

    def __post_init__(self) -> None:
        _require_reference_text(self.policy_kind, "policy_kind")
        _require_reference_text(self.policy_id, "policy_id")
        _require_reference_text(self.policy_version, "policy_version")

    @classmethod
    def from_binding(cls, binding: PolicyBinding) -> PolicyVersionReference:
        """The reference form of a stored binding, dropping the effective
        date for the reason given above."""
        return cls(
            policy_kind=binding.policy_kind,
            policy_id=binding.policy_id,
            policy_version=binding.policy_version,
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "policy_kind": self.policy_kind,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class FinanceRecordReference:
    """The shape of every reference *other* packs hold at a finance
    record: an identifier plus the owning scope, and nothing else.

    Spec 11.1 point 1 records the semantic correction this type exists to
    make readable. PACK-09 exports `FinanceEvidenceRef`, whose name says
    "evidence" but whose target is a PACK-10 **finance record** - a
    transaction, contribution, sponsorship agreement, report version or
    snapshot - and not evidence content, which is PACK-11's (`ФИН-21`).
    Nobody holding one of these holds evidence.

    A distinct type per record kind, exactly as PACK-09's `ScopedRef`
    subclasses are distinct: a `ContributionReference` and a
    `FinanceReportVersionReference` are not interchangeable even though
    both are (UUID, scope) pairs, and mypy enforces it at every call
    site."""

    owner: ClassVar[ReferenceOwner] = ReferenceOwner.PACK_10_FINANCE

    record_id: UUID
    scope: OrganizationalScopeRef

    def to_payload(self) -> dict[str, object]:
        return {
            "owner": str(self.owner),
            "record_id": str(self.record_id),
            "organization_id": str(self.scope.organization_id),
        }


@dataclass(frozen=True, slots=True)
class FinanceReportReference(FinanceRecordReference):
    """Points at a report identity - the series, not one version of it."""


@dataclass(frozen=True, slots=True)
class FinanceReportVersionReference(FinanceRecordReference):
    """Points at one `reporting.FinanceReportVersion`.

    Carries no state: a holder that wants to know whether the version is
    published must ask, because a cached status is how a superseded
    version keeps being presented as current (`ФИН-25`, `ФИН-34`)."""


@dataclass(frozen=True, slots=True)
class ContributionReference(FinanceRecordReference):
    """Points at a `records.FinanceContribution` - the record, never the
    contributor."""


@dataclass(frozen=True, slots=True)
class SponsorshipReference(FinanceRecordReference):
    """Points at a `records.SponsorshipAgreement`. The natural target of a
    PACK-35 cross-link, from the other side of
    `LobbyingContactReference`."""


@dataclass(frozen=True, slots=True)
class FinanceAuditEngagementReference(FinanceRecordReference):
    """Points at a `reporting.AuditEngagement`. Carries neither the
    conclusion nor any finding: canon 20.17 group 5 admits the fact of an
    audit and the conclusion class, and finding content is projected
    nowhere."""


@dataclass(frozen=True, slots=True)
class FinancePartyHandleReference(FinanceRecordReference):
    """Points at a `domain.FinancePartyHandle`: the handle id and the
    purpose it was minted for, resolvable by nobody outside the party
    registry (spec 11.1 point 2).

    **This type never enters a public projection, an export or a
    published report, in any form or at any level of derivation** (canon
    19f.15, canon 20.17 group 6). It exists so an internal, authorised
    caller can pass a typed handle pointer instead of a bare UUID, and
    for no other reason. It deliberately has no `to_payload()` override
    adding the purpose: the inherited payload is already more than a
    public surface may see, and adding purpose would make the leak
    richer rather than the type safer."""

    purpose: HandlePurpose

    @classmethod
    def from_handle(cls, handle: FinancePartyHandle) -> FinancePartyHandleReference:
        """The reference form of a minted handle. The perimeter travels as
        the scope, because a handle presented outside the perimeter it was
        minted for is refused (`ФИН-01`)."""
        return cls(record_id=handle.handle_id, scope=handle.perimeter, purpose=handle.purpose)


# ---------------------------------------------------------------------------
# The boundary, made enforceable
# ---------------------------------------------------------------------------

#: Field names that would amount to a document's **content**. PACK-11
#: owns document bytes, renditions, extracted text and custody; a finance
#: payload carrying any of these has stopped being a reference (spec 12,
#: `ФИН-21`, canon 19f.23).
FORBIDDEN_DOCUMENT_CONTENT_KEYS: frozenset[str] = frozenset(
    {
        "content",
        "text",
        "bytes",
        "body",
        "extracted_text",
        "ocr_text",
        "document_content",
        "document_bytes",
        "file_bytes",
        "raw_content",
    }
)

#: Field names that would amount to an **assertion about** a document.
#: Spec 12 makes the prevention structural rather than a naming
#: convention: the reference types have no such field to read, and this
#: set is the backstop for a payload assembled somewhere else.
FORBIDDEN_DOCUMENT_ASSERTION_KEYS: frozenset[str] = frozenset(
    {"is_authentic", "is_signed", "is_admitted", "is_valid", "is_publishable"}
)


def assert_no_document_content(payload: Mapping[str, object], *, context: str = "") -> None:
    """Raise if `payload` carries a document's content, or an assertion
    about a document, in any nested position.

    Canon 19f.23 and `ФИН-21`: only PACK-11 can say that a document is
    authentic, signed, admitted, legally valid or publishable, and only
    PACK-11 holds what is inside it. A finance payload that answered
    either question would be this service asserting something it has no
    means of knowing - which is worse than not answering, because the
    answer would look authoritative.

    **Both defects raise the same `EvidenceAssertionUnavailableError`, and
    that is a compromise worth naming.** Content and assertion are
    different failures: one is holding what belongs to PACK-11, the other
    is claiming what only PACK-11 may claim. Canon section 24 registers no
    separate reason code for the first, and inventing a `FINANCE_*` code
    here would put an unregistered string on a governed refusal
    (`ФИН-40`). `FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE` is the closest
    registered code and covers both readings of 19f.23; the message names
    which of the two actually occurred, so an operator is not left
    guessing.

    **What it does not catch.** A key-name check sees names, not values.
    A payload that hides a scanned invoice in a field called
    `note_reference` passes here and is caught by nothing in this module.
    The structural defence is that no type in this module has a field for
    such a value; this function guards payloads assembled elsewhere."""

    def walk(node: object, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                key_text = str(key).lower()
                location = f"{context}: " if context else ""
                where = path or "<root>"
                if key_text in FORBIDDEN_DOCUMENT_ASSERTION_KEYS:
                    raise EvidenceAssertionUnavailableError(
                        f"{location}assertion key {key!s} at {where} - only PACK-11 may "
                        "assert authenticity, signature, admissibility, validity or "
                        "publishability of a document"
                    )
                if key_text in FORBIDDEN_DOCUMENT_CONTENT_KEYS:
                    raise EvidenceAssertionUnavailableError(
                        f"{location}document-content key {key!s} at {where} - a finance "
                        "record holds a reference to a document, never the document"
                    )
                walk(value, f"{path}.{key!s}" if path else str(key))
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload, "")


#: The PACK-35 refusal, re-exported here rather than reimplemented.
#:
#: **Choice made, and why.** The task of this module is to name every
#: foreign concept the context refuses, and a boundary section that
#: silently omitted lobbying would read as though no such boundary
#: existed. But the rule and its subject-kind set
#: (`records.PACK_35_SUBJECT_KINDS`) already live in `records`, next to
#: the `ExternalFinancialBenefit` aggregate whose intake calls it, and a
#: second copy is a second thing to keep in step. So: one implementation,
#: re-exported under its own name - not renamed to
#: `assert_not_lobbying_disclosure`, because two names for one function is
#: how a codebase ends up with two functions. The real check is
#: `records.assert_not_lobbying_subject`; it raises
#: `UnauthorizedStateTransitionError`, not an identity or disclosure code,
#: for the reason documented there.
assert_not_lobbying_subject = _assert_not_lobbying_subject


def require_retention_binding(binding: RetentionBinding | None) -> RetentionBinding:
    """Return the PACK-09 record-class binding, or raise.

    A governed finance record must name its record class (`ФИН-22`,
    `ФИН-23`, reason code `FINANCE_RETENTION_BINDING_MISSING`). Absence is
    not "retain indefinitely" and not "dispose when convenient" - it is a
    record nobody has assigned a retention schedule, a custodian or a
    disposition authority to, and this service may invent none of the
    three. Fails closed (`ФИН-41`).

    A function rather than a field default, because a default would be
    exactly the invented schedule this refuses."""
    if binding is None:
        raise RetentionBindingMissingError(
            "a governed finance record must name the PACK-09 record class it is bound to"
        )
    return binding


#: Reference kinds this service refuses to accept at all, in either
#: direction (canon 19f.23, `ФИН-36`).
#:
#: No entity of the finance context has a read or write edge to
#: `VoteEnvelope`, `Tally`, `Ballot`, `Delegation`, `DelegationSnapshot`
#: or `ParticipationCredential` - not directly and not through
#: scope-authorization - and no finance identifier, handle, event payload
#: or audit-metadata element forms a correlation bridge into voting. The
#: identity and membership kinds are here for the neighbouring rule
#: (`ФИН-01`): identity belongs to `identity-service` and membership to
#: `membership-service`, and this context reads neither into its records.
#:
#: The set is about *shapes of foreign record*, not about one service's
#: naming, which is why the plural and the qualified forms are all listed:
#: a refusal that only recognised `ballot` would be defeated by `ballots`.
FORBIDDEN_INBOUND_REFERENCE_KINDS: frozenset[str] = frozenset(
    {
        "ballot",
        "ballots",
        "vote",
        "votes",
        "vote_envelope",
        "voteenvelope",
        "voter",
        "voter_roll",
        "tally",
        "tallies",
        "delegation",
        "delegation_snapshot",
        "credential",
        "credentials",
        "participation_credential",
        "identity",
        "identity_record",
        "identityrecord",
        "membership",
        "membership_record",
        "member",
    }
)


def assert_reference_kind_allowed(kind: str) -> None:
    """Raise unless `kind` names a reference this context may hold.

    `ФИН-36`, canon 19f.23: finance records, identifiers and audit
    metadata never form a correlation bridge into voting. The check runs
    at the *kind* level and therefore before any identifier is stored,
    which is the only point at which the refusal is cheap - once a ballot
    reference is inside a governed, append-only record it cannot be
    deleted (`ФИН-05`), only regretted.

    Raises `ForbiddenIdentityLinkageError`
    (`FINANCE_FORBIDDEN_IDENTITY_LINKAGE`) for every kind in the set,
    including the voting ones: `ФИН-36` and `ФИН-01` are the same
    prohibition seen from two sides, and canon section 24 registers no
    separate "forbidden voting linkage" code.

    **What it does not catch.** This is an exact match on a normalised
    token - lower-cased, trimmed, hyphens folded to underscores - and not
    a substring scan. `ballot_id_for_audit` is not in the set and passes;
    the key-level defence for that is `domain.reject_identity_payload_keys`,
    which does list `ballot_id` and `vote_id` and runs over every event
    payload and every projection payload. Neither function is a
    replacement for the structural fact that no type in this package has a
    field for any of these."""
    normalised = kind.strip().lower().replace("-", "_").replace(" ", "_")
    if normalised in FORBIDDEN_INBOUND_REFERENCE_KINDS:
        raise ForbiddenIdentityLinkageError(
            f"reference kind {kind!r} belongs to the voting, identity or membership contexts "
            "and may never be referenced from a finance record"
        )

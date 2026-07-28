"""Finance Service domain primitives (PACK-10, canon 0.8.0 section 19f).

This module holds the value objects, the identity-minimisation model and
the pure invariant functions the rest of the service is built on. It has
no I/O, no clock and no storage: every function here is deterministic and
testable in isolation, exactly as `compliance-service.domain` is for
PACK-09.

Three rules shape everything below:

- **Money is exact.** `Money` carries integer minor units, an explicit
  currency and an explicit scale. There is no float anywhere in the
  finance domain, and cross-currency arithmetic raises rather than
  silently netting (canon 19f.3, `ФИН-08`, `ФИН-09`).
- **A party is never a person.** `FinancePartyHandle` is an opaque,
  purpose-scoped, perimeter-scoped handle. There is no `UserId`,
  `PersonId`, `MemberId` or membership reference in this module and
  there must never be one (canon 19f.15, `ФИН-01`).
- **Everything protected is scoped.** `OrganizationalScopeRef` travels
  with every record and every reference; an undeterminable scope denies
  (`ФИН-03`, `ФИН-04`).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    CurrencyUnsupportedError,
    EvidenceReferenceMissingError,
    ForbiddenIdentityLinkageError,
    MonetaryAmountInvalidError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    PartyHandlePurposeMismatchError,
)

# ---------------------------------------------------------------------------
# Identity minimisation
# ---------------------------------------------------------------------------

#: Field names that may never appear in a finance record, a finance event
#: payload or a publication projection (canon 19f.15, `ФИН-01`/`ФИН-02`).
#: The list is deliberately about *shapes of identity*, not about a single
#: service's naming: any of these arriving at a finance boundary is a
#: forbidden identity linkage, whoever produced it.
PROHIBITED_IDENTITY_KEYS: frozenset[str] = frozenset(
    {
        "user_id",
        "userid",
        "person_id",
        "personid",
        "global_user_id",
        "member_id",
        "membership_id",
        "account_id",
        "identity_record_id",
        "credential_id",
        "voter_id",
        "ballot_id",
        "vote_id",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "full_name",
        "first_name",
        "last_name",
        "name",
        "address",
        "postal_address",
        "date_of_birth",
        "birth_date",
        "national_id",
        "tax_id",
        "iban",
        "bic",
        "bank_account",
        "bank_account_number",
        "card_number",
        "pan",
        "password",
        "secret",
        "token",
    }
)


def reject_identity_payload_keys(payload: dict[str, object], *, context: str) -> None:
    """Raise if any prohibited identity key appears in `payload`.

    Applied at every event-construction and projection boundary. Nested
    mappings are walked, because a prohibited key one level down is the
    same leak as one at the top (`ФИН-02`)."""

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                key_text = str(key)
                if key_text.lower() in PROHIBITED_IDENTITY_KEYS:
                    raise ForbiddenIdentityLinkageError(
                        f"{context}: prohibited identity key {key_text!r} at {path or '<root>'}"
                    )
                walk(value, f"{path}.{key_text}" if path else key_text)
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload, "")


class HandlePurpose(StrEnum):
    """The purposes a `FinancePartyHandle` may be minted for.

    A handle is valid for exactly one purpose. There is no cross-purpose
    lookup in this service, and presenting a handle for another purpose
    raises (canon 19f.15, `ФИН-01`)."""

    CONTRIBUTION = "contribution"
    MEMBERSHIP_FEE = "membership_fee"
    SPONSORSHIP = "sponsorship"
    EXTERNAL_INFLUENCE = "external_influence"
    EXPENSE_CLAIMANT = "expense_claimant"
    OBLIGATION_COUNTERPARTY = "obligation_counterparty"
    REPORT_SIGNATORY = "report_signatory"


@dataclass(frozen=True, slots=True)
class OrganizationalScopeRef:
    """A PACK-08 organizational scope, carried by every finance record.

    Opaque by construction: an id plus the scope kind PACK-08 assigned.
    This service never interprets the hierarchy itself - inheritance and
    access modes stay with `organization-service` (canon 19f.19)."""

    organization_id: UUID
    scope_kind: str = "organization"

    def __post_init__(self) -> None:
        if not self.scope_kind or not self.scope_kind.strip():
            raise OrganizationScopeUndeterminedError("scope_kind must be a non-empty string")

    def assert_matches(self, other: OrganizationalScopeRef | None) -> None:
        """Raise unless `other` is the same scope. `None` is undetermined
        and denies rather than defaulting (`ФИН-04`)."""
        if other is None:
            raise OrganizationScopeUndeterminedError("organizational scope is undetermined")
        if other.organization_id != self.organization_id:
            raise OrganizationScopeMismatchError(
                "organizational scope does not match the target record's scope"
            )


@dataclass(frozen=True, slots=True)
class FinancePartyHandle:
    """A purpose-scoped, perimeter-scoped, opaque party reference.

    Derived from nothing: the id is minted by the service, never computed
    from a name, an account, a membership or any participation value. Two
    handles for the same legal person in different purposes are unequal
    by construction, and nothing in this service can join them - the
    matching act lives in the party registry and is audited there
    (canon 19f.15, `ФИН-01`, `ФИН-36`).

    `pseudonymisation is not anonymity`: a handle is personal data and is
    re-identifiable by an authorised resolver. It limits correlation and
    accidental exposure, nothing more."""

    handle_id: UUID
    purpose: HandlePurpose
    perimeter: OrganizationalScopeRef
    policy_version: str = "party_handle/v1"

    def assert_usable_for(self, purpose: HandlePurpose, perimeter: OrganizationalScopeRef) -> None:
        """Raise unless this handle was minted for exactly this purpose
        and perimeter (`ФИН-01`)."""
        if self.purpose is not purpose:
            raise PartyHandlePurposeMismatchError(
                f"handle minted for purpose {self.purpose!s}, presented for {purpose!s}"
            )
        if self.perimeter.organization_id != perimeter.organization_id:
            raise PartyHandlePurposeMismatchError(
                "handle presented outside the reporting perimeter it was minted for"
            )

    def as_reference(self) -> str:
        """The only form a handle may take in an event payload or a
        projection: an opaque string, never the underlying identity."""
        return f"fph:{self.purpose!s}:{self.handle_id}"


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------

#: Currencies this reference implementation governs. Extending the set is
#: a `FinancePolicy(currency)` decision, not a code change (canon 19f.20);
#: the tuple here is the reference seed the in-memory adapters start from.
GOVERNED_CURRENCIES: frozenset[str] = frozenset({"EUR"})

#: Minor-unit exponent per governed currency.
CURRENCY_SCALE: dict[str, int] = {"EUR": 2}


class RoundingRule(StrEnum):
    """Rounding rules a computed amount may record. Every computed amount
    carries the rule it was produced under (`ФИН-08`)."""

    HALF_UP = "half_up"
    HALF_EVEN = "half_even"
    EXACT = "exact"


@dataclass(frozen=True, slots=True)
class Money:
    """An exact monetary amount: integer minor units plus explicit
    currency, scale and rounding rule.

    No floating point is accepted anywhere - not in the constructor, not
    in arithmetic, not in serialisation (`ФИН-08`). Cross-currency
    arithmetic raises: two amounts in different currencies never net
    silently (`ФИН-09`)."""

    minor_units: int
    currency: str
    scale: int = 2
    rounding: RoundingRule = RoundingRule.EXACT

    def __post_init__(self) -> None:
        if isinstance(self.minor_units, bool) or not isinstance(self.minor_units, int):
            raise MonetaryAmountInvalidError(
                "minor_units must be an int - floating-point money is forbidden"
            )
        currency = self.currency
        if not isinstance(currency, str) or currency != currency.upper() or len(currency) != 3:
            raise CurrencyUnsupportedError(
                f"currency must be a 3-letter upper-case code, got {currency!r}"
            )
        if currency not in GOVERNED_CURRENCIES:
            raise CurrencyUnsupportedError(
                f"currency {currency} is not governed by the active policy"
            )
        if self.scale != CURRENCY_SCALE[currency]:
            raise MonetaryAmountInvalidError(
                f"scale {self.scale} does not match the governed scale for {currency}"
            )

    # -- arithmetic ---------------------------------------------------

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyUnsupportedError(
                "cross-currency arithmetic requires an explicit recorded conversion"
            )

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.minor_units + other.minor_units, self.currency, self.scale, self.rounding)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.minor_units - other.minor_units, self.currency, self.scale, self.rounding)

    def negated(self) -> Money:
        return Money(-self.minor_units, self.currency, self.scale, self.rounding)

    @property
    def is_zero(self) -> bool:
        return self.minor_units == 0

    @property
    def is_positive(self) -> bool:
        return self.minor_units > 0

    def assert_non_zero(self, *, context: str) -> None:
        """Zero-value postings are refused unless a typed non-monetary
        record is explicitly used instead (canon 19f.4)."""
        if self.is_zero:
            raise MonetaryAmountInvalidError(f"{context}: a zero-value monetary posting is refused")

    def to_payload(self) -> dict[str, object]:
        """Deterministic, float-free serialisation."""
        return {
            "minor_units": self.minor_units,
            "currency": self.currency,
            "scale": self.scale,
            "rounding": str(self.rounding),
        }


def sum_money(amounts: tuple[Money, ...]) -> dict[str, int]:
    """Total minor units per currency. Never nets across currencies."""
    totals: dict[str, int] = {}
    for amount in amounts:
        totals[amount.currency] = totals.get(amount.currency, 0) + amount.minor_units
    return totals


# ---------------------------------------------------------------------------
# Provenance, evidence, policy and retention bindings
# ---------------------------------------------------------------------------


class ProvenanceKind(StrEnum):
    """How a financial fact entered the service. Every transaction
    records one; `IMPORTED` additionally requires a batch reference
    (`ФИН-38`)."""

    MANUAL_ENTRY = "manual_entry"
    IMPORTED = "imported"
    DERIVED_CORRECTION = "derived_correction"
    DERIVED_REVERSAL = "derived_reversal"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a financial fact came from, recorded immutably at intake."""

    kind: ProvenanceKind
    source_system_reference: str
    recorded_by_authority: str
    import_batch_reference: str | None = None
    external_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.source_system_reference.strip():
            raise MonetaryAmountInvalidError("source_system_reference must be non-empty")
        if not self.recorded_by_authority.strip():
            raise MonetaryAmountInvalidError("recorded_by_authority must be non-empty")

    def to_payload(self) -> dict[str, object]:
        return {
            "kind": str(self.kind),
            "source_system_reference": self.source_system_reference,
            "import_batch_reference": self.import_batch_reference,
            "external_reference": self.external_reference,
        }


class EvidenceKind(StrEnum):
    """The document kinds a finance record may point at. PACK-11 owns the
    documents themselves; this enum is the finance-side expectation, not
    a document taxonomy (`ФИН-21`)."""

    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    BANK_STATEMENT = "bank_statement"
    VALUATION_REPORT = "valuation_report"
    DONATION_DECLARATION = "donation_declaration"
    SPONSORSHIP_AGREEMENT = "sponsorship_agreement"
    AUDIT_WORKING_PAPER = "audit_working_paper"
    SIGNED_REPORT = "signed_report"
    SUBMISSION_RECEIPT = "submission_receipt"
    PUBLICATION_RENDITION = "publication_rendition"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """A scoped pointer at material PACK-11 will own.

    Deliberately shaped like PACK-09's `PlaceholderRef`: an owner, an open
    kind, an opaque external reference and a scope. It carries no
    `is_authentic`, `is_signed`, `is_admitted` or `is_publishable` field,
    because holding a reference asserts none of those (`ФИН-21`)."""

    kind: EvidenceKind
    external_reference: str
    scope: OrganizationalScopeRef
    owner: str = "pack-11-documents"

    def __post_init__(self) -> None:
        if not self.external_reference.strip():
            raise EvidenceReferenceMissingError("evidence external_reference must be non-empty")

    def to_payload(self) -> dict[str, object]:
        return {
            "kind": str(self.kind),
            "owner": self.owner,
            "external_reference": self.external_reference,
        }


@dataclass(frozen=True, slots=True)
class PolicyBinding:
    """The exact policy id and version a protected decision used.

    Stored on the decision, never resolved at read time: a later policy
    change must not silently rewrite a past decision (canon 19f.20,
    `ФИН-23`)."""

    policy_kind: str
    policy_id: str
    policy_version: str
    effective_from: date

    def to_payload(self) -> dict[str, object]:
        return {
            "policy_kind": self.policy_kind,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "effective_from": self.effective_from.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class RetentionBinding:
    """The PACK-09 record class a finance record is bound to. Retention
    and legal-hold semantics stay PACK-09's (`ФИН-22`, `ФИН-23`)."""

    record_class_reference: str
    bound_at: datetime

    def __post_init__(self) -> None:
        if not self.record_class_reference.strip():
            raise EvidenceReferenceMissingError("record_class_reference must be non-empty")
        require_timezone(self.bound_at, context="RetentionBinding.bound_at")


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def require_timezone(moment: datetime, *, context: str) -> datetime:
    """Every stored instant is timezone-explicit; a naive datetime is
    refused rather than assumed to be UTC (`ФИН-39`).

    The refusal carries `FINANCE_ACCOUNTING_PERIOD_UNDETERMINED`, not a
    monetary code: canon section 24 gives that code the meaning "no
    period, or no timezone-explicit period, could be determined", which
    is exactly what a naive instant leaves behind. An earlier draft of
    this function raised `MonetaryAmountInvalidError`, which would have
    reported a time defect under a money code."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise AccountingPeriodUndeterminedError(
            f"{context}: a naive datetime is refused - an explicit timezone is required"
        )
    return moment


# ---------------------------------------------------------------------------
# Deterministic identifiers
# ---------------------------------------------------------------------------


def deterministic_digest(*parts: str) -> str:
    """A stable content digest used for snapshots and idempotency keys.

    Deterministic across processes and runs: the same inputs always
    produce the same digest, which is what makes snapshot immutability
    and idempotent replay checkable (`ФИН-24`)."""
    joined = "".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReasonCoded:
    """A recorded reason for a governed act: the canonical code plus the
    authority that invoked it. Free text is not a reason (`ФИН-40`)."""

    reason_code: str
    authority_reference: str
    note_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.reason_code.strip() or self.reason_code != self.reason_code.upper():
            raise MonetaryAmountInvalidError("reason_code must be a non-empty upper-case code")
        if not self.authority_reference.strip():
            raise MonetaryAmountInvalidError("authority_reference must be non-empty")

    def to_payload(self) -> dict[str, object]:
        return {
            "reason_code": self.reason_code,
            "authority_reference": self.authority_reference,
            "note_reference": self.note_reference,
        }


@dataclass(frozen=True, slots=True)
class ReportingPeriodRef:
    """The reporting period a financial fact is allocated to. Explicit on
    every record; never inferred from the posting timestamp alone
    (`ФИН-39`)."""

    period_id: UUID
    label: str
    scope: OrganizationalScopeRef

    def to_payload(self) -> dict[str, object]:
        return {"period_id": str(self.period_id), "label": self.label}


@dataclass(frozen=True, slots=True)
class AuthorityReference:
    """A PACK-08 institutional authority assignment, as presented by the
    caller. The service resolves it through the authorisation port; a
    `role_code` string alone is never proof of authority (`ФИН-45`)."""

    authority_id: UUID
    role_code: str
    scope: OrganizationalScopeRef
    actor_reference: str = ""

    def __post_init__(self) -> None:
        if not self.role_code.strip():
            raise MonetaryAmountInvalidError("role_code must be non-empty")

    def to_payload(self) -> dict[str, object]:
        return {
            "authority_id": str(self.authority_id),
            "role_code": self.role_code,
            "actor_reference": self.actor_reference or None,
        }


@dataclass(frozen=True, slots=True)
class ConflictDeclaration:
    """The conflict-of-interest state declared for a protected action.

    `UNDECLARED` is a real state and it fails closed: the service refuses
    the protected action rather than treating silence as "no conflict"
    (`ФИН-32`)."""

    state: str
    declared_by: str
    related_party_group_reference: str | None = None

    UNDECLARED = "undeclared"
    NONE = "none"
    DECLARED_NON_BLOCKING = "declared_non_blocking"
    BLOCKING = "blocking"

    @property
    def is_blocking(self) -> bool:
        return self.state == self.BLOCKING

    @property
    def is_undeclared(self) -> bool:
        return self.state == self.UNDECLARED


@dataclass(frozen=True, slots=True)
class RequestContext:
    """What a caller presents with every command.

    Mirrors PACK-09's `RequestContext`: the caller's own scope, the
    authorities it asserts, the conflict state it declares, and the
    caller-supplied `event_id` that makes the command idempotent."""

    scope: OrganizationalScopeRef | None
    authorities: tuple[AuthorityReference, ...] = ()
    conflict: ConflictDeclaration | None = None
    event_id: UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)

    def require_scope(self) -> OrganizationalScopeRef:
        if self.scope is None:
            raise OrganizationScopeUndeterminedError(
                "organizational scope is undetermined - default deny"
            )
        return self.scope

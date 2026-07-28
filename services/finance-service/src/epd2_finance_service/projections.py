"""Finance Service derived read models - versioned, non-authoritative, and
the single surface anything leaves this context through (PACK-10 sections
8.4, 9.6 and 9.7; canon 0.8.0 sections 19f.21 and 20.17's
public-projection subsection).

`ФИН-34`: public finance representations are derived, versioned and
**never authoritative**. Nothing here is a source of truth, nothing here
is written back into an aggregate, and every object carries the
provenance canon 19f.21 makes mandatory - the report version, the
`ReportSnapshot` reference, the perimeter's scope, the source's lifecycle
state and the moment of generation - so a reader can always answer "what
was this derived from, and is it still current?" without asking the
service.

Four rules shape the module:

- **A projection is never authoritative, and cannot be made to look it.**
  `is_authoritative` is a read-only property returning `False`, not a
  field. A field could be constructed `True`; a property cannot, and the
  distinction survives `dataclasses.replace`, deserialisation and every
  future field somebody adds.
- **Correction and supersession are visible, never silent.** Canon 19f.21
  requires that amendment, restatement and a superseded or stale state be
  *visible* in the representation. `SourceCorrectionStatus` is therefore
  a mandatory part of every projection's provenance, defaulting to
  `current` only where the source aggregate itself says so.
- **Emission is one chokepoint.** Spec 9.7: every export or projection
  leaves through this module, so PACK-12 can attach data-loss prevention
  at exactly one place rather than auditing every call site. Each builder
  runs `domain.reject_identity_payload_keys` over its own `to_payload()`
  output *before* returning the projection, so a projection that would
  leak an identity key never comes into existence - not even to be
  discarded later by a caller who might forget.
- **Aggregate before emitting, and refuse a cell too small.** `ФИН-35`
  and `FINANCE_STATISTICAL_DISCLOSURE_RISK`: statistical disclosure
  control runs *before* release, not as a post-publication review.

**Payload key naming.** `FinanceAccount.account_id` serialises as
`finance_account_id`, exactly as in `events`: `account_id` is in
`domain.PROHIBITED_IDENTITY_KEYS` because in every other context in this
repository it means a *user* account, and a projection that emitted it
would fail its own emission check. The rename is not cosmetic - it is the
reason the check can stay blunt.

**What this module does not decide.** It does not decide what must be
published. That is a legal question (spec 9.6, OD-7), and the answer
arrives as a disclosure-obligation reference the caller supplies and this
module refuses to proceed without. `MINIMUM_CELL_SIZE` is a floor this
code will not go below, not a legal threshold it claims to know.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID

from epd2_finance_service.domain import (
    Money,
    reject_identity_payload_keys,
    require_timezone,
)
from epd2_finance_service.exceptions import (
    ForbiddenIdentityLinkageError,
    MonetaryAmountInvalidError,
    PublicationNotAllowedError,
    StatisticalDisclosureRiskError,
)
from epd2_finance_service.ledger import AccountingPeriod, FinanceAccount
from epd2_finance_service.records import (
    PARTY_HANDLE_REFERENCE_PREFIX,
    ContributionState,
    FinanceContribution,
    SponsorshipAgreement,
    SponsorshipState,
    assert_disclosure_classified,
)
from epd2_finance_service.references import (
    OrganizationalScopeReference,
    PolicyVersionReference,
)
from epd2_finance_service.reporting import (
    AuditEngagement,
    AuditEngagementState,
    FinanceReportVersion,
    ReportState,
)

# ---------------------------------------------------------------------------
# Projection versions and source status
# ---------------------------------------------------------------------------

#: The version string carried by every projection built for a public
#: consumer. Versioned because canon 19f.21 requires it: a representation
#: whose shape changed without its version changing is one no consumer can
#: reproduce or contest later.
PUBLIC_PROJECTION_VERSION: str = "finance_public/v1"

#: The version string for the internal register views. Separate from the
#: public one on purpose - if the two ever shared a version, a change
#: forced by an internal need would silently renumber the public contract.
INTERNAL_PROJECTION_VERSION: str = "finance_internal/v1"


class SourceCorrectionStatus(StrEnum):
    """Whether the record a projection was derived from has since been
    corrected or displaced (canon 19f.21: correction, withdrawal and a
    stale or superseded state must be *visible*, not silent).

    **One canon term has no member here, and that is a gap worth
    naming.** 19f.21 lists withdrawal (`отзыв`) alongside correction and
    supersession. `reporting.ReportState` models no withdrawal: canon
    19f.17 fixes twelve states and none of them is "withdrawn", so a
    `WITHDRAWN` member would be a status no aggregate could ever produce -
    an enum member that is only ever a lie. When a withdrawal state is
    added to the report lifecycle, it belongs here too; until then a
    withdrawn publication surfaces as `SUPERSEDED`, which understates it,
    and this comment is the record of that."""

    CURRENT = "current"
    AMENDED = "amended"
    RESTATED = "restated"
    SUPERSEDED = "superseded"


def correction_status_for_report_state(
    state: ReportState, *, superseded_by_version_reference: UUID | None = None
) -> SourceCorrectionStatus:
    """Map a report version's own state onto the projection's correction
    status.

    A successor version *entering* `amended` or `restated` is itself the
    correction; a predecessor becomes `superseded`. Both are visible
    facts, and `superseded_by_version_reference` is honoured even when the
    version's own state has not yet been re-read, because a projection
    that knows a successor exists and reports `current` anyway is the
    precise failure 19f.21 forbids."""
    if superseded_by_version_reference is not None:
        return SourceCorrectionStatus.SUPERSEDED
    if state is ReportState.SUPERSEDED:
        return SourceCorrectionStatus.SUPERSEDED
    if state is ReportState.AMENDED:
        return SourceCorrectionStatus.AMENDED
    if state is ReportState.RESTATED:
        return SourceCorrectionStatus.RESTATED
    return SourceCorrectionStatus.CURRENT


# ---------------------------------------------------------------------------
# The shared projection shape
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class FinanceProjection:
    """Provenance every derived read model carries (canon 19f.21).

    Keyword-only: a base class with six provenance fields and subclasses
    with their own would otherwise force every subclass field to carry a
    default just to satisfy positional ordering, and a default is exactly
    what a provenance field must not have.

    `source_lifecycle_state` is a plain string rather than a union of the
    five source enums, because a consumer's question is "draft, reviewed,
    audited, approved or published?" and the answer must be readable
    without importing this package. The builders always pass the source
    aggregate's own `str(state)`, never a re-spelled synonym."""

    projection_version: str
    generated_at: datetime
    scope: OrganizationalScopeReference
    source_lifecycle_state: str
    correction_status: SourceCorrectionStatus = SourceCorrectionStatus.CURRENT
    source_snapshot_id: UUID | None = None
    source_report_version_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.projection_version.strip():
            raise MonetaryAmountInvalidError("projection_version must be a non-empty string")
        if not self.source_lifecycle_state.strip():
            raise MonetaryAmountInvalidError("source_lifecycle_state must be a non-empty string")
        require_timezone(self.generated_at, context="FinanceProjection.generated_at")

    @property
    def is_authoritative(self) -> bool:
        """Always `False` (`ФИН-34`).

        **Why a property and not a field.** A field can be set: a
        constructor argument, a `dataclasses.replace`, a deserialiser
        reading an attacker-supplied JSON object, or simply a future
        builder that passes `True` by accident, and the projection would
        then *claim* authority it does not have. A read-only property has
        no such path - there is nothing to assign, `frozen=True` refuses
        assignment to the name anyway, and `slots=True` means no instance
        dictionary can shadow it. The value is hard-coded rather than
        derived, because there is no input under which it would be true:
        a derived representation never becomes the accounting source of
        truth, however authoritative its source was."""
        return False

    def _provenance_payload(self) -> dict[str, object]:
        """The provenance block canon 19f.21 makes mandatory."""
        return {
            "projection_version": self.projection_version,
            "generated_at": self.generated_at.isoformat(),
            "organization_id": str(self.scope.organization_id),
            "scope_kind": self.scope.scope_kind,
            "source_lifecycle_state": self.source_lifecycle_state,
            "correction_status": str(self.correction_status),
            "source_snapshot_id": (
                None if self.source_snapshot_id is None else str(self.source_snapshot_id)
            ),
            "source_report_version_id": (
                None
                if self.source_report_version_id is None
                else str(self.source_report_version_id)
            ),
            "is_authoritative": self.is_authoritative,
        }

    def to_payload(self) -> dict[str, object]:
        """The emittable form. Subclasses extend the provenance block and
        never replace it: a payload without provenance is a figure with no
        way back to what produced it."""
        return self._provenance_payload()


def _assert_emittable(projection: FinanceProjection) -> None:
    """Run the identity-key rejection over a projection's own payload.

    Called by every builder before it returns, so the check covers fields
    that did not exist when the builder was written. `ФИН-02`: the point
    is not that today's fields are safe - it is that a careless future
    field cannot ship. It walks nested structures, so a prohibited key one
    level down fails the same way as one at the top.

    It is a key-shape check and nothing more. A projection that put a
    contributor's name in a field called `benefit_description` passes
    here; the defence against that is that no builder below accepts free
    text from outside the aggregate it derives from."""
    reject_identity_payload_keys(
        projection.to_payload(), context=f"projection {type(projection).__name__}"
    )


def _require_money_non_negative(amount: Money | None, field_name: str) -> None:
    """A published figure may be zero, but a negative published total is
    almost always a sign-convention bug reaching a public surface. Refused
    here rather than explained later."""
    if amount is not None and amount.minor_units < 0:
        raise MonetaryAmountInvalidError(f"{field_name} must not be negative in a projection")


def _money_payload(amount: Money | None) -> object:
    return None if amount is None else amount.to_payload()


def _require_disclosure_obligation(reference: str) -> str:
    """Raise unless the caller named the obligation that justifies the
    disclosure.

    Canon 20.17 group 2: public projection of contributions, sponsorship
    and external financial benefit is permitted **only to the extent an
    effective disclosure obligation prescribes**. A projection built
    without naming one is publication with no legal basis recorded, which
    is why the refusal is `PublicationNotAllowedError`
    (`PUBLICATION_NOT_ALLOWED`) and not a validation code: nothing is
    malformed, the act itself is not permitted."""
    if not reference or not reference.strip():
        raise PublicationNotAllowedError(
            "a disclosure projection must name the effective disclosure obligation that "
            "prescribes it; publication is permitted only to that extent"
        )
    return reference


def _require_opaque_party_reference(reference: str | None, field_name: str) -> str | None:
    """Raise unless a party appears as the opaque `fph:` handle reference.

    `ФИН-01`: the resolved value never reaches this module, and anything
    that is not a handle reference - a name, an IBAN, a user id - is a
    forbidden identity linkage whoever produced it. `None` is permitted
    and means the source could not be established, which is a fact about
    the receipt rather than a defect of the projection."""
    if reference is None:
        return None
    if not reference.startswith(PARTY_HANDLE_REFERENCE_PREFIX):
        raise ForbiddenIdentityLinkageError(
            f"{field_name} must be an opaque party-handle reference, not a resolved identity"
        )
    return reference


# ---------------------------------------------------------------------------
# Group 1 - internal register views (canon 20.17, 19f.4-19f.6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class AccountBalanceProjection(FinanceProjection):
    """The derived balance of one chart-of-accounts node.

    **Never publicly projected, in any form.** Canon 20.17 group 1: public
    projection of individual accounting, period, register and provenance
    events is not permitted at all; only aggregated derived figures
    *inside a published report version* may be public. A public consumer
    therefore never sees this object - it sees a `PublishedReportProjection`
    whose totals were computed from many of these. The class carries the
    internal projection version for that reason, and building one is not a
    publication decision.

    The balance is passed in, not computed here: `ledger` models postings
    and balance checks, not balances, and a second summation living in a
    read model is a second answer that can disagree with the register
    (spec 8.4, `TrialBalanceView`: "the balancing check is on the entries,
    not on this view")."""

    finance_account_id: UUID
    account_code: str
    classification_code: str
    closing_balance: Money

    @classmethod
    def from_account(
        cls,
        account: FinanceAccount,
        *,
        closing_balance: Money,
        generated_at: datetime,
        source_snapshot_id: UUID | None = None,
    ) -> AccountBalanceProjection:
        """Derive the view from the account aggregate and a balance
        computed against posted entries."""
        projection = cls(
            projection_version=INTERNAL_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(account.scope),
            source_lifecycle_state=str(account.status),
            source_snapshot_id=source_snapshot_id,
            finance_account_id=account.account_id,
            account_code=account.code,
            classification_code=account.classification_code,
            closing_balance=closing_balance,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        payload = FinanceProjection._provenance_payload(self)
        payload["finance_account_id"] = str(self.finance_account_id)
        payload["account_code"] = self.account_code
        payload["classification_code"] = self.classification_code
        payload["closing_balance"] = self.closing_balance.to_payload()
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class PeriodSummaryProjection(FinanceProjection):
    """Aggregated register totals for one accounting period.

    **Never publicly projected as such** (canon 20.17 group 1), for the
    same reason as `AccountBalanceProjection`: a period total that reached
    the public outside a published report version would be an accounting
    figure with no report, no approval, no signature, no audit and no
    publication authorisation behind it - an alternative source of truth,
    which is exactly what `ФИН-34` denies a derived view the right to be.

    Totals are held per currency and never netted across currencies
    (`ФИН-09`), as a sorted tuple rather than a mapping so the payload is
    deterministic and the projection stays hashable."""

    period_id: UUID
    period_label: str
    period_timezone_name: str
    opens_at: datetime
    closes_at: datetime
    total_minor_units_by_currency: tuple[tuple[str, int], ...]

    @classmethod
    def from_period(
        cls,
        period: AccountingPeriod,
        *,
        total_minor_units_by_currency: Mapping[str, int],
        generated_at: datetime,
        source_snapshot_id: UUID | None = None,
    ) -> PeriodSummaryProjection:
        """Derive the view from the period aggregate and per-currency
        totals computed over posted entries."""
        totals = tuple(sorted(total_minor_units_by_currency.items()))
        projection = cls(
            projection_version=INTERNAL_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(period.scope),
            source_lifecycle_state=str(period.status),
            source_snapshot_id=source_snapshot_id,
            period_id=period.period_id,
            period_label=period.label,
            period_timezone_name=period.timezone_name,
            opens_at=period.opens_at,
            closes_at=period.closes_at,
            total_minor_units_by_currency=totals,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        payload = FinanceProjection._provenance_payload(self)
        payload["period_id"] = str(self.period_id)
        payload["period_label"] = self.period_label
        payload["period_timezone_name"] = self.period_timezone_name
        payload["opens_at"] = self.opens_at.isoformat()
        payload["closes_at"] = self.closes_at.isoformat()
        payload["total_minor_units_by_currency"] = [
            {"currency": currency, "minor_units": minor_units}
            for currency, minor_units in self.total_minor_units_by_currency
        ]
        return payload


# ---------------------------------------------------------------------------
# Group 2 - disclosure-obliged views (canon 20.17, 19f.7-19f.9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class ContributionDisclosureProjection(FinanceProjection):
    """The disclosure-obliged view of one accepted contribution.

    Canon 20.17 group 2: publication is permitted **only to the extent an
    effective disclosure obligation prescribes**, and canon 19f.21 admits
    only governed authoritative records as sources - a published report
    version and *accepted* contributions. `from_contribution` therefore
    refuses any contribution that is not `accepted` and any projection
    that cannot name its obligation.

    **The party, and a place where the canon and the brief disagree.** The
    object holds the contributor only as the opaque `fph:` reference and
    never a resolved value, which is the strictest form in which finance
    can identify a party at all. But canon 19f.15 and 20.17 group 6 go
    further: a `FinancePartyHandle` never appears in a public
    representation, in any form or at any level of derivation, and 19f.21
    repeats it. So the handle reference lives on the object - it is what
    lets a caller group contributions by party for the legally required
    aggregation, inside the service - and `to_payload()`, which is the
    emission surface, omits it entirely. A projection that carried it onto
    the wire would satisfy "opaque" and violate "never".

    The receipt instant is likewise absent: the projection carries the
    reporting period label. An exact timestamp is a far stronger
    identifier than any disclosure obligation asks for, and the
    aggregation the obligation prescribes happens at period level
    anyway."""

    contribution_id: UUID
    contribution_kind: str
    reporting_period_label: str
    disclosure_obligation_reference: str
    disclosed_amount: Money | None = None
    disclosed_in_kind_amount: Money | None = None
    disclosure_policy: PolicyVersionReference | None = None
    contributor_handle_reference: str | None = None

    def __post_init__(self) -> None:
        FinanceProjection.__post_init__(self)
        _require_disclosure_obligation(self.disclosure_obligation_reference)
        _require_opaque_party_reference(
            self.contributor_handle_reference, "contributor_handle_reference"
        )
        _require_money_non_negative(self.disclosed_amount, "disclosed_amount")
        _require_money_non_negative(self.disclosed_in_kind_amount, "disclosed_in_kind_amount")

    @classmethod
    def from_contribution(
        cls,
        contribution: FinanceContribution,
        *,
        disclosure_obligation_reference: str,
        reporting_period_label: str,
        generated_at: datetime,
        disclosure_policy: PolicyVersionReference | None = None,
        source_report_version_id: UUID | None = None,
        source_snapshot_id: UUID | None = None,
    ) -> ContributionDisclosureProjection:
        """Derive the view from an **accepted** contribution.

        Every other state refuses with `PublicationNotAllowedError`, and
        the quarantined case is the one worth stating: a quarantined
        contribution is the recorded admission that its source or
        verification is still open (`ФИН-16`), and publishing it would
        present an unresolved question as a disclosed fact."""
        if contribution.state is not ContributionState.ACCEPTED:
            raise PublicationNotAllowedError(
                f"only an accepted contribution is publicly projected; this one is "
                f"{contribution.state!s}"
            )
        receipt = contribution.receipt
        in_kind = receipt.in_kind_valuation
        projection = cls(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(contribution.scope),
            source_lifecycle_state=str(contribution.state),
            source_snapshot_id=source_snapshot_id,
            source_report_version_id=source_report_version_id,
            contribution_id=contribution.contribution_id,
            contribution_kind=str(receipt.kind),
            reporting_period_label=reporting_period_label,
            disclosure_obligation_reference=_require_disclosure_obligation(
                disclosure_obligation_reference
            ),
            disclosed_amount=receipt.amount,
            disclosed_in_kind_amount=None if in_kind is None else in_kind.valued_amount,
            disclosure_policy=disclosure_policy,
            contributor_handle_reference=receipt.contributor_handle_reference,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        """Emits no party reference at all - see the class docstring."""
        payload = FinanceProjection._provenance_payload(self)
        payload["contribution_id"] = str(self.contribution_id)
        payload["contribution_kind"] = self.contribution_kind
        payload["reporting_period_label"] = self.reporting_period_label
        payload["disclosure_obligation_reference"] = self.disclosure_obligation_reference
        payload["disclosed_amount"] = _money_payload(self.disclosed_amount)
        payload["disclosed_in_kind_amount"] = _money_payload(self.disclosed_in_kind_amount)
        payload["disclosure_policy"] = (
            None if self.disclosure_policy is None else self.disclosure_policy.to_payload()
        )
        payload["contributor_is_recorded"] = self.contributor_handle_reference is not None
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class SponsorshipDisclosureProjection(FinanceProjection):
    """The disclosure-obliged view of one sponsorship agreement.

    Same rule as `ContributionDisclosureProjection` - obligation-bounded
    publication, opaque party on the object and no party on the wire - plus
    the disclosure classification, which sponsorship has and contributions
    do not. `records.assert_disclosure_classified` is reused rather than
    re-implemented: a missing classification is neither "publishable" nor
    "not publishable", it is unknown, and an unknown disclosure state
    fails closed (`ФИН-19`, `ФИН-35`).

    Only a `disclosure_classified` or `terminated` agreement is projected.
    A `registered`, `under_review`, `approved` or `rejected` one is not:
    approval says the agreement is permitted, and only classification says
    anything about publishing it. A terminated agreement stays projectable
    because ending an agreement does not retract the obligation to have
    disclosed it - the termination is visible in
    `source_lifecycle_state`."""

    agreement_id: UUID
    disclosure_class: str
    period_start: date
    period_end: date
    disclosure_obligation_reference: str
    disclosed_value: Money | None = None
    disclosed_in_kind_amount: Money | None = None
    disclosure_policy: PolicyVersionReference | None = None
    sponsor_handle_reference: str | None = None

    #: The two agreement states a disclosure projection may be built from.
    _PROJECTABLE_STATES: ClassVar[frozenset[SponsorshipState]] = frozenset(
        {SponsorshipState.DISCLOSURE_CLASSIFIED, SponsorshipState.TERMINATED}
    )

    def __post_init__(self) -> None:
        FinanceProjection.__post_init__(self)
        assert_disclosure_classified(self.disclosure_class, action="a disclosure projection")
        _require_disclosure_obligation(self.disclosure_obligation_reference)
        _require_opaque_party_reference(self.sponsor_handle_reference, "sponsor_handle_reference")
        _require_money_non_negative(self.disclosed_value, "disclosed_value")
        _require_money_non_negative(self.disclosed_in_kind_amount, "disclosed_in_kind_amount")

    @classmethod
    def from_agreement(
        cls,
        agreement: SponsorshipAgreement,
        *,
        disclosure_obligation_reference: str,
        generated_at: datetime,
        disclosure_policy: PolicyVersionReference | None = None,
        source_report_version_id: UUID | None = None,
        source_snapshot_id: UUID | None = None,
    ) -> SponsorshipDisclosureProjection:
        """Derive the view from a disclosure-classified agreement."""
        if agreement.review_state not in cls._PROJECTABLE_STATES:
            raise PublicationNotAllowedError(
                f"only a disclosure-classified or terminated sponsorship agreement is publicly "
                f"projected; this one is {agreement.review_state!s}"
            )
        in_kind = agreement.in_kind_valuation
        projection = cls(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(agreement.scope),
            source_lifecycle_state=str(agreement.review_state),
            source_snapshot_id=source_snapshot_id,
            source_report_version_id=source_report_version_id,
            agreement_id=agreement.agreement_id,
            disclosure_class=assert_disclosure_classified(
                agreement.disclosure_class, action="a sponsorship disclosure projection"
            ),
            period_start=agreement.period_start,
            period_end=agreement.period_end,
            disclosure_obligation_reference=_require_disclosure_obligation(
                disclosure_obligation_reference
            ),
            disclosed_value=agreement.value,
            disclosed_in_kind_amount=None if in_kind is None else in_kind.valued_amount,
            disclosure_policy=disclosure_policy,
            sponsor_handle_reference=agreement.sponsor_handle_reference,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        """Emits no sponsor reference and no benefit description.

        The description is free text written by a finance officer, and
        free text is where a name, an address or a bank detail reaches a
        public surface without any field being called that (`ФИН-02`).
        What the obligation requires published is the classification, the
        value and the period; the description is not one of them."""
        payload = FinanceProjection._provenance_payload(self)
        payload["sponsorship_agreement_id"] = str(self.agreement_id)
        payload["disclosure_class"] = self.disclosure_class
        payload["period_start"] = self.period_start.isoformat()
        payload["period_end"] = self.period_end.isoformat()
        payload["disclosure_obligation_reference"] = self.disclosure_obligation_reference
        payload["disclosed_value"] = _money_payload(self.disclosed_value)
        payload["disclosed_in_kind_amount"] = _money_payload(self.disclosed_in_kind_amount)
        payload["disclosure_policy"] = (
            None if self.disclosure_policy is None else self.disclosure_policy.to_payload()
        )
        payload["sponsor_is_recorded"] = self.sponsor_handle_reference is not None
        return payload


# ---------------------------------------------------------------------------
# Group 3 - budgets (canon 20.17, 19f.10-19f.12)
# ---------------------------------------------------------------------------


def _assert_aggregate_categories(labels: tuple[str, ...]) -> None:
    """Refuse a category label that is a record identifier.

    A "category" whose name is a UUID is one record presented as an
    aggregate, which is the individual `expense_claim.*`/`payment.*`
    projection canon 20.17 group 3 forbids, arriving through the one field
    shaped to hold many values."""
    for label in labels:
        if not label.strip():
            raise MonetaryAmountInvalidError("a budget category label must be non-empty")
        try:
            UUID(label.strip())
        except ValueError:
            continue
        raise PublicationNotAllowedError(
            f"budget category {label!r} is a record identifier, not an aggregate category; "
            "individual expense claims and payments are never publicly projected"
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetSummaryProjection(FinanceProjection):
    """Aggregated figures of one **approved** budget version.

    Canon 20.17 group 3: public projection of expenses, payments, budgets,
    assets and obligations is permitted only at the aggregated level of an
    approved budget version and a published report version, and individual
    `expense_claim.*` and `payment.*` are not projected at all. This class
    has no field for a claim, a payment, a claimant, an authorisation or a
    settlement, and there is no builder that would accept one - the
    structural absence is the enforcement.

    The residual leak is not a missing field but a misused one: category
    totals keyed by record identifier are per-record projection wearing an
    aggregate's clothes. `_assert_aggregate_categories` therefore refuses
    any category label that parses as a UUID. That catches the obvious
    form and not a caller who labels one claim `"office costs"`; nothing
    in a pure module can distinguish a genuine category of one from a
    disguised record, which is what `assert_no_small_cell_disclosure`
    exists for.

    Budget itself is not modelled as an aggregate in this package - PACK-10's
    pure modules stop at `budget.approved`/`budget.amended` events - so
    this projection is built from typed arguments rather than from a
    `Budget` object. That is a real asymmetry with the other five, not a
    shortcut: there is no aggregate to derive from."""

    budget_id: UUID
    budget_version: int
    reporting_period_label: str
    approved_total: Money
    approved_total_by_category: tuple[tuple[str, Money], ...] = ()

    def __post_init__(self) -> None:
        FinanceProjection.__post_init__(self)
        if self.budget_version < 1:
            raise MonetaryAmountInvalidError("budget_version must be a positive integer")
        _require_money_non_negative(self.approved_total, "approved_total")
        _assert_aggregate_categories(tuple(label for label, _ in self.approved_total_by_category))

    @classmethod
    def from_approved_budget(
        cls,
        *,
        budget_id: UUID,
        budget_version: int,
        scope: OrganizationalScopeReference,
        reporting_period_label: str,
        approved_total: Money,
        generated_at: datetime,
        approved_total_by_category: Mapping[str, Money] | None = None,
        source_report_version_id: UUID | None = None,
        source_snapshot_id: UUID | None = None,
    ) -> BudgetSummaryProjection:
        """Build the aggregated view of an approved budget version.

        `source_lifecycle_state` is the literal `"approved"`: the only
        budget state canon 20.17 group 3 admits into a public projection,
        and hard-coded here rather than accepted as a parameter so a draft
        budget cannot be projected by passing the wrong string."""
        categories: Mapping[str, Money] = (
            {} if approved_total_by_category is None else approved_total_by_category
        )
        projection = cls(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=scope,
            source_lifecycle_state="approved",
            source_snapshot_id=source_snapshot_id,
            source_report_version_id=source_report_version_id,
            budget_id=budget_id,
            budget_version=budget_version,
            reporting_period_label=reporting_period_label,
            approved_total=approved_total,
            approved_total_by_category=tuple(sorted(categories.items(), key=lambda item: item[0])),
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        payload = FinanceProjection._provenance_payload(self)
        payload["budget_id"] = str(self.budget_id)
        payload["budget_version"] = self.budget_version
        payload["reporting_period_label"] = self.reporting_period_label
        payload["approved_total"] = self.approved_total.to_payload()
        payload["approved_total_by_category"] = [
            {"category": label, "approved_total": amount.to_payload()}
            for label, amount in self.approved_total_by_category
        ]
        return payload


# ---------------------------------------------------------------------------
# Group 4 - the published report version (canon 20.17, 19f.16-19f.17)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class PublishedReportProjection(FinanceProjection):
    """The public view of a report version - and only a `published` one.

    Canon 20.17 group 4: only a version in state `published` is publicly
    projected, and `finance_report.snapshot_frozen`,
    `finance_report.validation_finding_recorded` and
    `finance_report.correction_requested` are not projected at all. Every
    other state raises `PublicationNotAllowedError`, including
    `externally_accepted`: an authority's acceptance decision is not a
    publication decision, and publication needs its own authorisation
    (`ФИН-28`, `ФИН-34`).

    **The snapshot id is provenance, not the snapshot event.** Canon
    19f.21 requires every representation to carry a reference to its
    `ReportSnapshot`; canon 20.17 group 4 forbids projecting the
    `snapshot_frozen` *event*. Those are different objects: the first is a
    pointer that lets a reader ask which frozen source set produced a
    figure, the second would publish the freezing act with its included
    identifier sets. This projection carries the first and nothing of the
    second.

    It carries no figures of its own. The aggregated totals a published
    report contains are the report's content, prepared, reviewed,
    approved, signed and audited as such; re-deriving them in a read model
    would create a second set that can disagree with the published one
    (`ФИН-34`)."""

    report_id: UUID
    version: int
    reporting_period_label: str
    publication_reference: str
    published_at: datetime
    audit_engagement_id: UUID | None = None
    superseded_by_version_reference: UUID | None = None

    def __post_init__(self) -> None:
        FinanceProjection.__post_init__(self)
        if self.version < 1:
            raise MonetaryAmountInvalidError("version must be a positive integer")
        if not self.publication_reference.strip():
            raise PublicationNotAllowedError(
                "a published report projection must name the publication record it derives from"
            )
        require_timezone(self.published_at, context="PublishedReportProjection.published_at")

    @classmethod
    def from_report_version(
        cls,
        version: FinanceReportVersion,
        *,
        generated_at: datetime,
        superseded_by_version_reference: UUID | None = None,
    ) -> PublishedReportProjection:
        """Derive the view from a `published` report version.

        Three refusals, each its own fact: a state other than `published`;
        a version carrying no publication record, which cannot occur
        through `FinanceReportVersion.publish` but is checked because a
        version reconstructed from storage could arrive that way; and a
        version with no bound snapshot, which `FinanceReportVersion`'s own
        `__post_init__` already forbids for any non-preparable state and
        which is re-checked here so the projection never emits a null
        provenance pointer (`ФИН-24`)."""
        if version.state is not ReportState.PUBLISHED:
            raise PublicationNotAllowedError(
                f"only a published report version is publicly projected; this one is "
                f"{version.state!s}"
            )
        publication = version.publication_reference
        if publication is None:
            raise PublicationNotAllowedError(
                "a published report version must carry the publication record that published it"
            )
        if version.snapshot_id is None:
            raise PublicationNotAllowedError(
                "a published report version must name the frozen snapshot it was computed from"
            )
        audit = version.audit_reference
        projection = cls(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(version.scope),
            source_lifecycle_state=str(version.state),
            correction_status=correction_status_for_report_state(
                version.state,
                superseded_by_version_reference=superseded_by_version_reference,
            ),
            source_snapshot_id=version.snapshot_id,
            source_report_version_id=version.version_id,
            report_id=version.report_id,
            version=version.version,
            reporting_period_label=version.period.label,
            publication_reference=publication.publication_reference,
            published_at=publication.published_at,
            audit_engagement_id=None if audit is None else audit.engagement_id,
            superseded_by_version_reference=superseded_by_version_reference,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        payload = FinanceProjection._provenance_payload(self)
        payload["report_id"] = str(self.report_id)
        payload["version"] = self.version
        payload["reporting_period_label"] = self.reporting_period_label
        payload["publication_reference"] = self.publication_reference
        payload["published_at"] = self.published_at.isoformat()
        payload["audit_engagement_id"] = (
            None if self.audit_engagement_id is None else str(self.audit_engagement_id)
        )
        payload["superseded_by_version_reference"] = (
            None
            if self.superseded_by_version_reference is None
            else str(self.superseded_by_version_reference)
        )
        return payload


# ---------------------------------------------------------------------------
# Group 5 - the audit (canon 20.17, 19f.18)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditConclusionProjection(FinanceProjection):
    """The fact that an audit happened, and the class it concluded with.

    Canon 20.17 group 5 admits exactly two things into a public
    projection: the fact of the audit and the `AuditConclusion` class.
    Finding content is projected nowhere, and neither
    `AuditFinding.summary_reference` (a pointer, but a pointer to a
    finding) nor `AuditConclusion.reason` nor its evidence references
    appear on this object at all.

    **Two fields an earlier draft carried and this one does not.** A
    `finding_count`, because a count is not the fact of an audit and not
    the conclusion class, and in a small perimeter "three findings" is
    disclosive about a handful of people. And the auditor's
    `AuthorityReference`: naming the auditor may well be required by some
    obligation, but that is a separate disclosure decision with its own
    authority, and canon 20.17 group 5 does not grant it here. Both are
    omissions, not oversights."""

    engagement_id: UUID
    conclusion_class: str
    concluded_at: datetime
    reporting_period_label: str

    def __post_init__(self) -> None:
        FinanceProjection.__post_init__(self)
        if not self.conclusion_class.strip():
            raise MonetaryAmountInvalidError("conclusion_class must be a non-empty string")
        require_timezone(self.concluded_at, context="AuditConclusionProjection.concluded_at")

    @classmethod
    def from_engagement(
        cls,
        engagement: AuditEngagement,
        *,
        generated_at: datetime,
        source_report_version_id: UUID | None = None,
    ) -> AuditConclusionProjection:
        """Derive the view from a **concluded** engagement.

        An open or in-progress engagement refuses: canon 20.17 group 5
        admits the conclusion class, and an engagement that has not
        concluded has none. Projecting the bare fact that an audit is
        under way would also publish a mid-audit state as a finished one
        to any reader who did not check the lifecycle field."""
        if engagement.state is not AuditEngagementState.CONCLUDED:
            raise PublicationNotAllowedError(
                f"only a concluded audit engagement is publicly projected; this one is "
                f"{engagement.state!s}"
            )
        conclusion = engagement.conclusion
        if conclusion is None:
            raise PublicationNotAllowedError(
                "a concluded audit engagement must carry the conclusion it concluded with"
            )
        projection = cls(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=generated_at,
            scope=OrganizationalScopeReference.from_scope(engagement.scope),
            source_lifecycle_state=str(engagement.state),
            source_report_version_id=source_report_version_id,
            engagement_id=engagement.engagement_id,
            conclusion_class=conclusion.conclusion_class,
            concluded_at=conclusion.concluded_at,
            reporting_period_label=engagement.period.label,
        )
        _assert_emittable(projection)
        return projection

    def to_payload(self) -> dict[str, object]:
        payload = FinanceProjection._provenance_payload(self)
        payload["audit_engagement_id"] = str(self.engagement_id)
        payload["conclusion_class"] = self.conclusion_class
        payload["concluded_at"] = self.concluded_at.isoformat()
        payload["reporting_period_label"] = self.reporting_period_label
        return payload


# ---------------------------------------------------------------------------
# Statistical disclosure control (`ФИН-35`)
# ---------------------------------------------------------------------------

#: The smallest non-zero cell this module will emit.
#:
#: **Five is a floor, not a legal threshold, and this module does not get
#: to set the real one.** The applicable minimum is a
#: `FinancePolicy(statistical_disclosure)` value bound to the
#: representation and effective-dated (canon 19f.21, spec section 13); it
#: depends on the jurisdiction, the obligation and the population, and no
#: constant in a pure module can know it. Five is the conventional
#: starting point in official statistics and is used here for one purpose:
#: so that a caller with no policy value still cannot emit a cell of one
#: or two by omission. A policy value *above* five is honoured; a policy
#: value *below* five is refused, because a code-level floor that any
#: caller can lower is not a floor.
MINIMUM_CELL_SIZE: int = 5


def assert_no_small_cell_disclosure(
    cell_counts: Mapping[str, int], *, context: str, minimum_cell_size: int | None = None
) -> None:
    """Raise if any non-zero cell is below the applicable minimum.

    `ФИН-35`, reason code `FINANCE_STATISTICAL_DISCLOSURE_RISK`: control
    is applied **before** emission, which is why this is an assertion a
    builder calls and not a review a publisher performs. An empty cell
    passes - zero says "nobody", which discloses nobody - while a cell of
    one is the whole problem: an aggregate of one person is that person.

    A negative count fails too. It is a bug rather than a disclosure, but
    a mapping this function cannot interpret is not one it may pass, and
    failing closed on it is cheaper than the alternative (`ФИН-41`).

    **The residual risk this does not catch, stated plainly.** It sees one
    mapping at one moment, so it cannot see *differencing*. Publish a
    report version with a cell of 7, publish a corrected version whose
    same cell is 6, and the difference identifies one contributor exactly
    - and both releases passed this check individually. The same holds
    across overlapping cells inside a single release (a total and its
    parts), across a public projection and a separately published
    aggregate, and across a finance figure and any other public dataset
    about the same population. Defending against differencing needs state
    this module deliberately does not hold: the history of what has
    already been released, and a policy about what may be released next.
    Until a suppression policy owns that history, this function is a floor
    on the most obvious failure and nothing more, and calling it does not
    mean a release is safe."""
    minimum = MINIMUM_CELL_SIZE if minimum_cell_size is None else minimum_cell_size
    if minimum < MINIMUM_CELL_SIZE:
        raise StatisticalDisclosureRiskError(
            f"{context}: a minimum cell size of {minimum} is below the module floor of "
            f"{MINIMUM_CELL_SIZE}; a policy may raise the threshold, never lower it"
        )
    for cell, count in cell_counts.items():
        if count != 0 and count < minimum:
            raise StatisticalDisclosureRiskError(
                f"{context}: cell {cell!r} holds {count} and the applicable minimum is "
                f"{minimum}; the view is suppressed rather than emitted"
            )

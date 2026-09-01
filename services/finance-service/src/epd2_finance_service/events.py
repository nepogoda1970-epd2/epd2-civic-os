"""Canonical events emitted by Finance Service (canon section 20.17,
PACK-10 implementation round).

Seventy-two event types, no more and no fewer. `FINANCE_EVENT_TYPES`
carries them with the canon's own aggregate prefixes and **no**
`finance.` service prefix bolted on: canon 20.17 writes
`finance_account.created`, not `finance.finance_account_created`, and a
name invented here would not be the canonical name whatever it read like.
`finance-service` is the sole owner of every one of them (ADR-048); no
other service publishes into this stream, and the cross-pack consumers
canon 20.17 names (PACK-09, PACK-11, PACK-12, PACK-13, PACK-35) read it
and never write it.

Three distinct payload jobs live in this module and are deliberately not
interchangeable:

- **State payloads** (`*_state_payload`) are full, canonically-hashable
  snapshots for Audit Core's `before_hash`/`after_hash`. They cover
  *every* field of their aggregate. PACK-07's contract work found a
  `membership-service` "full state" snapshot that silently omitted three
  fields, which had left those fields outside the tamper-evidence hash -
  a snapshot that is only nearly complete is worse than an obviously
  partial one, because nothing signals the gap. None of these is ever a
  wire payload: they carry free-text business fields (a benefit
  description, a counter-performance, a valuation basis) that are fine
  inside a hash and forbidden on the wire.
- **Wire payloads** are what the 72 named builders assemble: identifiers,
  enum values, timestamps, one reason code, policy-version references,
  opaque outward references and monetary amounts only where the event's
  stated fact needs them. Nothing else.
- **The safe metadata** canon 20.17 makes mandatory is added by
  `build_finance_event` and not by 72 hand-written copies, so no builder
  can forget the organizational scope or the stable aggregate identifier.

**Why some `to_payload()` methods are not reused here.** Several value
objects in `domain` expose a `to_payload()` that is deliberately
wire-minimal: `AuthorityReference.to_payload()` omits its scope,
`Provenance.to_payload()` omits `recorded_by_authority`,
`EvidenceReference.to_payload()` omits its scope, and
`ReportingPeriodRef.to_payload()` omits its scope. That is correct for a
wire payload and wrong for a tamper-evidence hash, where an omitted field
is a field nobody can prove was not changed. The state payloads below
therefore use local `_*_state` serialisers covering every field, and
reuse `to_payload()` only where it is already complete (`Money`,
`PolicyBinding`, `ReasonCoded`).

**Where the acting authority appears, and where it never does.** Canon
20.17 permits a reference to the acting authority where disclosure of the
authority is allowed, and never the identity of the actor behind it.
`_authority_on_the_wire` therefore emits `authority_id` and `role_code`
and drops `actor_reference`, which is the closest thing this service holds
to an actor-level identifier (`ФИН-01`). The full `AuthorityReference`,
`actor_reference` included, appears only inside state payloads that are
hashed and never transmitted.

**One place where canon 19f.15 and canon 20.17 pull against each other,
recorded rather than papered over.** 19f.15 says a `FinancePartyHandle`
never appears in an event payload at all; 20.17 makes the stable
identifier of the affected aggregate mandatory safe metadata on every
event, and for the three `finance_party_handle.*` events the affected
aggregate *is* the handle. The two cannot both hold literally. This module
resolves it the narrow way: the opaque `fph:` reference (and nothing from
which an identity is derivable) travels on the handle's own events and on
the contribution events whose contributor is that handle, and the resolved
value never travels anywhere - which is the prohibition canon 20.17 states
explicitly for `finance_party_handle.resolved`. A projection layer still
owes the stricter 19f.15 reading: `PUBLIC_PROJECTION_ALLOWED` excludes all
three handle events in every form.

**No payload in this module carries** a name, an address, a bank detail, a
payment identifier, an identity document, evidence content, document
bytes, any voting information, a credential value or a secret.
`domain.reject_identity_payload_keys` runs over every assembled payload as
a structural backstop, so a future builder that reaches for one of those
key names fails closed rather than shipping it (`ФИН-02`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from uuid import UUID

from epd2_core.event_envelope import ActorRef, EventEnvelope, SubjectRef, build_event_envelope
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    EvidenceReference,
    FinancePartyHandle,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ReasonCoded,
    ReportingPeriodRef,
    RetentionBinding,
    reject_identity_payload_keys,
    require_timezone,
    sum_money,
)
from epd2_finance_service.ledger import (
    AccountingPeriod,
    FinanceAccount,
    FinancialTransaction,
    JournalEntry,
    LedgerHistoryEntry,
    PeriodReopeningRecord,
    PostingLine,
)
from epd2_finance_service.records import (
    ContributionAssessment,
    ContributionReceipt,
    ExpenseClaim,
    ExternalFinancialBenefit,
    FinanceContribution,
    FinancialAsset,
    FinancialObligation,
    InKindValuation,
    PaymentAuthorization,
    RecordHistoryEntry,
    SponsorshipAgreement,
)
from epd2_finance_service.reporting import (
    ApprovalRecord,
    AuditConclusion,
    AuditEngagement,
    AuditFinding,
    AuditOpinionReference,
    CorrectionRequest,
    ExternalAcceptanceReference,
    ExternalSubmissionReference,
    FinanceReportVersion,
    PerimeterSnapshot,
    PublicationReference,
    ReportingObligation,
    ReportingPerimeterDefinition,
    ReportSnapshot,
    ReviewRecord,
    SignatureRecord,
)

EVENT_VERSION = "1.0"
SUPPORTED_MAJOR_VERSIONS = frozenset({1})

#: The canonical producer name. Canon 20.17: `finance-service` owns every
#: one of the seventy-two events without exception, so this is a constant
#: and never a parameter.
_PRODUCER = "finance-service"


class UnknownFinanceEventTypeError(ValueError):
    """Raised when an event type outside `FINANCE_EVENT_TYPES` is offered
    to `build_finance_event`.

    Deliberately declared here and **not** in `exceptions.py`: that module
    holds one class per reason code registered in
    `contracts/reason-codes/pack-10.yml`, and an unknown event type is a
    programming error inside this service, not a governed refusal a caller
    could act on. Giving it a `FINANCE_*` reason code would advertise it as
    a business outcome (canon 19f.13 `ФИН-40` is about protected denials,
    which this is not).
    """


# ---------------------------------------------------------------------------
# The seventy-two canonical event types (canon 20.17)
# ---------------------------------------------------------------------------

#: Every event type of canon 20.17, in the canon's own order, with the
#: canon's own names. The tuple is the single source of truth: the generic
#: builder rejects anything absent from it, and `FINANCE_EVENT_AGGREGATES`
#: and `PUBLIC_PROJECTION_ALLOWED` are both keyed by it, so a name added
#: here without an aggregate mapping is a visible inconsistency rather
#: than a silent one.
FINANCE_EVENT_TYPES: tuple[str, ...] = (
    # Accounts, periods, the accounting register, provenance (19f.4-19f.6)
    "finance_account.created",
    "finance_account.status_changed",
    "accounting_period.opened",
    "accounting_period.closed",
    "accounting_period.reopening_requested",
    "accounting_period.reopened",
    "journal_entry.drafted",
    "journal_entry.posted",
    "journal_entry.reversed",
    "financial_transaction.recorded",
    "financial_transaction.classification_changed",
    "reconciliation.recorded",
    "import_batch.registered",
    "import_batch.completed",
    "import_batch.rejected",
    "import_batch.duplicate_detected",
    # Contributions, sponsorship, external financial benefit (19f.7-19f.9)
    "finance_contribution.received",
    "finance_contribution.quarantined",
    "finance_contribution.assessed",
    "finance_contribution.accepted",
    "finance_contribution.rejected",
    "finance_contribution.return_required",
    "finance_contribution.returned",
    "finance_contribution.escalated",
    "finance_in_kind_valuation.recorded",
    "sponsorship.registered",
    "sponsorship.approved",
    "sponsorship.rejected",
    "sponsorship.disclosure_classified",
    "external_financial_benefit.recorded",
    # Expenses, payments, budgets, assets, obligations (19f.10-19f.12)
    "expense_claim.submitted",
    "expense_claim.reviewed",
    "expense_claim.approved",
    "expense_claim.rejected",
    "expense_claim.corrected",
    "payment.authorized",
    "payment.settled",
    "budget.approved",
    "budget.amended",
    "financial_asset.recorded",
    "financial_asset.revalued",
    "financial_asset.written_off",
    "financial_obligation.recorded",
    "financial_obligation.revalued",
    "financial_obligation.settled",
    "financial_obligation.written_off",
    # Reporting obligation and the report lifecycle (19f.16, 19f.17)
    "reporting_obligation.created",
    "reporting_perimeter.defined",
    "finance_report.snapshot_frozen",
    "finance_report.prepared",
    "finance_report.validation_finding_recorded",
    "finance_report.consolidated",
    "finance_report.internally_reviewed",
    "finance_report.auditor_reviewed",
    "finance_report.correction_requested",
    "finance_report.approved",
    "finance_report.signed",
    "finance_report.submitted",
    "finance_report.external_acknowledgement_recorded",
    "finance_report.acceptance_recorded",
    "finance_report.published",
    "finance_report.restated",
    "finance_report.amended",
    "finance_report.superseded",
    # Audit and finance policy (19f.18, 19f.20)
    "finance_audit.opened",
    "finance_audit.finding_recorded",
    "finance_audit.concluded",
    "finance_policy.version_published",
    "finance_policy.superseded",
    # The purpose-scoped party reference (19f.15)
    "finance_party_handle.minted",
    "finance_party_handle.merged",
    "finance_party_handle.resolved",
)

_FINANCE_EVENT_TYPE_SET: frozenset[str] = frozenset(FINANCE_EVENT_TYPES)

#: Canon 20.17's prefix-to-aggregate table, verbatim. The canon states
#: that the prefix of an event name determines its aggregate
#: unambiguously, so the mapping is
#: recorded per prefix and `FINANCE_EVENT_AGGREGATES` is derived from it.
#: Typing it out per event type instead would let one of seventy-two
#: entries drift from its prefix without anything noticing.
#:
#: Two entries are alternatives in the canon's own text rather than single
#: names, and are reproduced as such: `finance_in_kind_valuation.*` names
#: "the valued aggregate", which is a `FinanceContribution` or an
#: `ExternalFinancialBenefit` depending on what was valued, and
#: `finance_report.*` names `FinanceReport / ReportSnapshot`.
#: `_FINANCE_REPORT_SNAPSHOT_EVENTS` below disambiguates the one
#: `finance_report.*` event whose aggregate is the snapshot.
FINANCE_EVENT_AGGREGATE_BY_PREFIX: dict[str, str] = {
    "finance_account": "FinanceAccount",
    "accounting_period": "AccountingPeriod",
    "journal_entry": "JournalEntry",
    "financial_transaction": "FinancialTransaction",
    "import_batch": "ImportBatch",
    "reconciliation": "ReconciliationRecord",
    "finance_contribution": "FinanceContribution",
    "finance_in_kind_valuation": "FinanceContribution|ExternalFinancialBenefit",
    "sponsorship": "SponsorshipAgreement",
    "external_financial_benefit": "ExternalFinancialBenefit",
    "expense_claim": "ExpenseClaim",
    "payment": "PaymentAuthorization",
    "budget": "Budget",
    "financial_asset": "FinancialAsset",
    "financial_obligation": "FinancialObligation",
    "reporting_obligation": "ReportingObligation",
    "reporting_perimeter": "ReportingPerimeterDefinition",
    "finance_report": "FinanceReport",
    "finance_audit": "AuditEngagement",
    "finance_policy": "FinancePolicy",
    "finance_party_handle": "FinancePartyHandle",
}

#: The `finance_report.*` events whose affected aggregate is the
#: `ReportSnapshot` half of the canon's `FinanceReport / ReportSnapshot`
#: pair. Only freezing acts on the snapshot; every other report event acts
#: on a version of the report itself.
_FINANCE_REPORT_SNAPSHOT_EVENTS: frozenset[str] = frozenset({"finance_report.snapshot_frozen"})


def _aggregate_for(event_type: str) -> str:
    prefix = event_type.split(".", 1)[0]
    if event_type in _FINANCE_REPORT_SNAPSHOT_EVENTS:
        return "ReportSnapshot"
    return FINANCE_EVENT_AGGREGATE_BY_PREFIX[prefix]


#: Every event type mapped to the aggregate canon 20.17 assigns it.
#: Derived, never hand-listed, so `set(FINANCE_EVENT_AGGREGATES)` and
#: `set(FINANCE_EVENT_TYPES)` are equal by construction.
FINANCE_EVENT_AGGREGATES: dict[str, str] = {
    event_type: _aggregate_for(event_type) for event_type in FINANCE_EVENT_TYPES
}


def _types_with_prefix(*prefixes: str) -> frozenset[str]:
    """Every canonical event type carrying one of `prefixes`."""
    wanted = set(prefixes)
    return frozenset(
        event_type for event_type in FINANCE_EVENT_TYPES if event_type.split(".", 1)[0] in wanted
    )


# ---------------------------------------------------------------------------
# The public-projection rule, per canon 20.17's six groups
# ---------------------------------------------------------------------------

# Group 1 - accounts, periods, the accounting register, provenance
# (19f.4-19f.6): public projection of individual events of this group is
# not permitted. No individual event of this group reaches the public;
# only aggregated derived figures inside a published report version may.
# So: nothing from this group enters the set.
_PUBLIC_GROUP_LEDGER: frozenset[str] = frozenset()

# Group 2 - contributions, sponsorship, external financial benefit
# (19f.7-19f.9): projection is permitted solely to the extent an active
# disclosure obligation prescribes - so the group is
# projectable in principle, and it is the active disclosure obligation,
# not this module, that fixes the extent. The rule is uniform across the
# group and the canon carves out no member of it, so every member is
# admitted here; admission is permission to be considered by a disclosure
# policy, never permission to publish.
_PUBLIC_GROUP_INCOME: frozenset[str] = _types_with_prefix(
    "finance_contribution",
    "finance_in_kind_valuation",
    "sponsorship",
    "external_financial_benefit",
)

# Group 3 - expenses, payments, budgets, assets, obligations
# (19f.10-19f.12): projection is permitted only at the aggregated level of
# an approved budget version and a published report version, and
# individual `expense_claim.*` and `payment.*` are named as not projected.
# The only events of this group that *are* the approved budget version are
# `budget.approved` and `budget.amended`; individual asset and obligation
# events are individual records and reach the public only as aggregated
# figures inside a published report, which is that report's projection and
# not theirs.
_PUBLIC_GROUP_SPENDING: frozenset[str] = frozenset({"budget.approved", "budget.amended"})

# Group 4 - reporting obligation and the report lifecycle (19f.16,
# 19f.17): only the version in status `published` is publicly projected,
# and `snapshot_frozen`, `validation_finding_recorded` and
# `correction_requested` are named as not projected. Only the publication
# event itself qualifies. `reporting_obligation.created` and
# `reporting_perimeter.defined` are in this group too and are not the
# published version, so they stay out; the perimeter reaches the public
# only as part of the published version it was frozen into.
_PUBLIC_GROUP_REPORT: frozenset[str] = frozenset({"finance_report.published"})

# Group 5 - audit and finance policy (19f.18, 19f.20): only the fact of an
# audit and the `AuditConclusion` class are publicly projected, together
# with the identifier and version of the policy in force; the content of
# findings is not projected. So the fact of an engagement and its class
# qualify and `finance_audit.finding_recorded` does not.
# `finance_policy.superseded` is admitted with the publication event: the
# projectable fact is *which policy version is in force*, and a
# projection that only ever learns of publications reports a superseded
# version as current forever.
_PUBLIC_GROUP_AUDIT_POLICY: frozenset[str] = frozenset(
    {
        "finance_audit.opened",
        "finance_audit.concluded",
        "finance_policy.version_published",
        "finance_policy.superseded",
    }
)

# Group 6 - the purpose-scoped party reference (19f.15): public projection
# is never permitted - not in any extent, and not in any derived form.
_PUBLIC_GROUP_PARTY_HANDLE: frozenset[str] = frozenset()

#: The event types canon 20.17 permits to appear in a public projection at
#: all. Membership here is necessary and never sufficient: canon 19f.21
#: adds that a permitted projection exists only as a derived, versioned,
#: non-authoritative representation under a disclosure policy and the
#: statistical disclosure-control rules, and is never the authoritative
#: source of a fact. Absence, by contrast, is final.
PUBLIC_PROJECTION_ALLOWED: frozenset[str] = (
    _PUBLIC_GROUP_LEDGER
    | _PUBLIC_GROUP_INCOME
    | _PUBLIC_GROUP_SPENDING
    | _PUBLIC_GROUP_REPORT
    | _PUBLIC_GROUP_AUDIT_POLICY
    | _PUBLIC_GROUP_PARTY_HANDLE
)


# ---------------------------------------------------------------------------
# Serialisation primitives
# ---------------------------------------------------------------------------


def _identifier(value: UUID | None) -> str | None:
    """A `UUID` as its canonical string, `None` preserved as `None`."""
    return None if value is None else str(value)


def _instant(value: datetime | None) -> str | None:
    """A timezone-explicit instant as ISO-8601. Never normalised to UTC:
    the stored offset is part of what was recorded (`ФИН-39`)."""
    return None if value is None else value.isoformat()


def _day(value: date | None) -> str | None:
    """A civil date as ISO-8601."""
    return None if value is None else value.isoformat()


def _money(value: Money | None) -> dict[str, object] | None:
    """A monetary amount through `Money.to_payload()`, which is already
    complete and float-free (`ФИН-08`)."""
    return None if value is None else value.to_payload()


def _policy(value: PolicyBinding | None) -> dict[str, object] | None:
    """A policy binding through its own complete `to_payload()`. The
    binding travels, never a resolved-at-read-time lookup (`ФИН-23`)."""
    return None if value is None else value.to_payload()


def _scope(scope: OrganizationalScopeRef) -> dict[str, object]:
    """An organizational scope in the two-field shape canon 20.17 makes
    mandatory safe metadata."""
    return {"organization_scope": str(scope.organization_id), "scope_kind": scope.scope_kind}


def _authority_on_the_wire(authority: AuthorityReference | None) -> dict[str, object] | None:
    """The only shape an acting authority takes in an event payload.

    `authority_id` and `role_code` and nothing else: canon 20.17 permits a
    reference to the authority where disclosure of the authority is
    allowed and **never** the identity of the actor behind it, and
    `actor_reference` is the closest thing this service holds to that
    (`ФИН-01`). Dropping it here rather than at 72 call sites is what makes
    the omission impossible to forget."""
    if authority is None:
        return None
    return {"authority_id": str(authority.authority_id), "role_code": authority.role_code}


def _authority_state(authority: AuthorityReference | None) -> dict[str, object] | None:
    """An `AuthorityReference` with all four of its fields, for hashing
    only.

    Not `AuthorityReference.to_payload()`, which omits `scope`: for a wire
    payload that omission is correct, and for a tamper-evidence hash it
    would leave the scope of every recorded act unprovable."""
    if authority is None:
        return None
    return {
        "authority_id": str(authority.authority_id),
        "role_code": authority.role_code,
        "actor_reference": authority.actor_reference or None,
        "scope": _scope(authority.scope),
    }


def _reason_state(reason: ReasonCoded | None) -> dict[str, object] | None:
    """A `ReasonCoded` through its own `to_payload()`, which covers all
    three fields."""
    return None if reason is None else reason.to_payload()


def _retention_state(retention: RetentionBinding | None) -> dict[str, object] | None:
    """A `RetentionBinding`'s two fields. It has no `to_payload()` of its
    own, and inventing one in `domain` for a hashing need would put a
    serialisation concern in the invariant module."""
    if retention is None:
        return None
    return {
        "record_class_reference": retention.record_class_reference,
        "bound_at": _instant(retention.bound_at),
    }


def _period_ref_state(period: ReportingPeriodRef) -> dict[str, object]:
    """A `ReportingPeriodRef` with its scope included - which
    `ReportingPeriodRef.to_payload()` deliberately drops."""
    return {
        "period_id": str(period.period_id),
        "label": period.label,
        "scope": _scope(period.scope),
    }


def _evidence_state(reference: EvidenceReference) -> dict[str, object]:
    """An `EvidenceReference` with all four fields, scope included -
    `EvidenceReference.to_payload()` drops the scope. A *reference* only:
    PACK-11 owns the document, and no content or byte ever appears here
    (`ФИН-21`)."""
    return {
        "kind": reference.kind.value,
        "owner": reference.owner,
        "external_reference": reference.external_reference,
        "scope": _scope(reference.scope),
    }


def _evidence_list_state(references: Sequence[EvidenceReference]) -> list[object]:
    """An ordered evidence tuple. Order is preserved because it is part of
    the stored state, and a hash over a re-sorted list would not be a hash
    of what is stored."""
    return [_evidence_state(reference) for reference in references]


def _provenance_state(provenance: Provenance) -> dict[str, object]:
    """A `Provenance` with all five fields, including
    `recorded_by_authority` - which `Provenance.to_payload()` drops, and
    which is exactly the field a provenance dispute turns on
    (`ФИН-38`)."""
    return {
        "kind": provenance.kind.value,
        "source_system_reference": provenance.source_system_reference,
        "recorded_by_authority": provenance.recorded_by_authority,
        "import_batch_reference": provenance.import_batch_reference,
        "external_reference": provenance.external_reference,
    }


def _conflict_state(conflict: ConflictDeclaration | None) -> dict[str, object] | None:
    """A `ConflictDeclaration`'s three fields. `None` stays `None` and is
    not flattened into `"undeclared"`: the aggregate treats the two the
    same when refusing an action, but they are different stored states and
    a hash must be able to tell them apart (`ФИН-32`)."""
    if conflict is None:
        return None
    return {
        "state": conflict.state,
        "declared_by": conflict.declared_by,
        "related_party_group_reference": conflict.related_party_group_reference,
    }


def _history_state(
    history: Sequence[LedgerHistoryEntry | RecordHistoryEntry],
) -> list[object]:
    """An append-only history tuple, entry by entry.

    One serialiser for both entry types: `ledger.LedgerHistoryEntry` and
    `records.RecordHistoryEntry` are field-for-field identical and
    deliberately share no base class in those modules, and introducing one
    here purely to serialise them would put a structural claim about two
    aggregates' histories into an events module."""
    return [
        {
            "sequence": entry.sequence,
            "occurred_at": _instant(entry.occurred_at),
            "action": entry.action,
            "reason": _reason_state(entry.reason),
            "acting_authority": _authority_state(entry.acting_authority),
            "state_after": entry.state_after,
            "policy": _policy(entry.policy),
        }
        for entry in history
    ]


def _in_kind_valuation_state(valuation: InKindValuation | None) -> dict[str, object] | None:
    """An `InKindValuation`'s five fields, for hashing only. `basis` is
    free text and is why this never becomes a wire payload."""
    if valuation is None:
        return None
    return {
        "basis": valuation.basis,
        "method_reference": valuation.method_reference,
        "valuation_date": _day(valuation.valuation_date),
        "evidence_reference": _evidence_state(valuation.evidence_reference),
        "valued_amount": _money(valuation.valued_amount),
    }


# ---------------------------------------------------------------------------
# State payloads for Audit Core's before_hash / after_hash
# ---------------------------------------------------------------------------
#
# Every function below covers **every** field of its aggregate. Two naming
# rules apply throughout and are not cosmetic:
#
# - No key is ever `account_id`, `name`, `address`, `iban` or any other
#   member of `domain.PROHIBITED_IDENTITY_KEYS`, even inside a state
#   payload that is only hashed. A state payload that would be refused by
#   `reject_identity_payload_keys` is one nobody can safely reuse, and
#   `FinanceAccount.account_id` therefore serialises as
#   `finance_account_id` (`ФИН-02`).
# - Nested value objects are serialised through the `_*_state` helpers
#   above, never through their wire-minimal `to_payload()`.


def finance_account_state_payload(account: FinanceAccount) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinanceAccount`'s own
    state (all nine fields), used for Audit Core's `after_hash`.

    `has_postings` is in the hash because it is what freezes `code` and
    `classification_code` (`ФИН-13`): a snapshot that omitted it could not
    show *when* those two became immutable."""
    return {
        "finance_account_id": str(account.account_id),
        "code": account.code,
        "classification_code": account.classification_code,
        "scope": _scope(account.scope),
        "retention": _retention_state(account.retention),
        "status": account.status.value,
        "has_postings": account.has_postings,
        "classification_policy": _policy(account.classification_policy),
        "history": _history_state(account.history),
    }


def _reopening_record_state(record: PeriodReopeningRecord) -> dict[str, object]:
    """All eleven fields of one create-once `PeriodReopeningRecord`,
    including both sides of the dual control (`ФИН-11`)."""
    return {
        "reopening_record_id": str(record.record_id),
        "period_id": str(record.period_id),
        "requested_by": _authority_state(record.requested_by),
        "approved_by": _authority_state(record.approved_by),
        "reason": _reason_state(record.reason),
        "policy": _policy(record.policy),
        "requested_at": _instant(record.requested_at),
        "approved_at": _instant(record.approved_at),
        "closed_state_digest": record.closed_state_digest,
        "legal_case_reference": record.legal_case_reference,
        "hold_reference": record.hold_reference,
    }


def accounting_period_state_payload(period: AccountingPeriod) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `AccountingPeriod`'s own
    state (all nine fields), used for Audit Core's `after_hash`.

    `reopening_records` is included in full rather than as a count: each
    record is the evidence that dual control happened for one reopening,
    and a count would leave the substance of every reopening outside the
    hash (`ФИН-11`). `state_digest` is added alongside the fields because
    the period's own digest is what a reopening record snapshots, and a
    dispute about *what* was reopened is answered by comparing the two."""
    return {
        "period_id": str(period.period_id),
        "label": period.label,
        "scope": _scope(period.scope),
        "timezone_name": period.timezone_name,
        "opens_at": _instant(period.opens_at),
        "closes_at": _instant(period.closes_at),
        "status": period.status.value,
        "reopening_records": [_reopening_record_state(r) for r in period.reopening_records],
        "history": _history_state(period.history),
        "state_digest": period.state_digest(),
    }


def _posting_line_state(line: PostingLine) -> dict[str, object]:
    """All five fields of one `PostingLine`. Direction lives in `side` and
    magnitude in `amount`, never a signed amount - the aggregate refuses a
    negative magnitude, and a serialiser that netted them would invent the
    second representation `ledger` exists to prevent."""
    return {
        "finance_account_id": str(line.account_id),
        "side": line.side.value,
        "amount": _money(line.amount),
        "dimension_references": list(line.dimension_references),
        "memo_reference": line.memo_reference,
    }


def journal_entry_state_payload(entry: JournalEntry) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `JournalEntry`'s own state
    (all eleven fields), used for Audit Core's `after_hash`.

    `lines` are hashed **in order**, because the ordered tuple is the
    authoritative record of monetary effect and a re-sorted list is a
    different record. Both backward links are present: `reverses_entry_id`
    and `corrects_entry_id` are two distinguishable acts and collapsing
    them would make a correction chain unreadable (`ФИН-06`)."""
    return {
        "journal_entry_id": str(entry.entry_id),
        "scope": _scope(entry.scope),
        "period": _period_ref_state(entry.period),
        "lines": [_posting_line_state(line) for line in entry.lines],
        "reason": _reason_state(entry.reason),
        "status": entry.status.value,
        "entry_sequence": entry.entry_sequence,
        "financial_transaction_id": _identifier(entry.transaction_id),
        "reverses_entry_id": _identifier(entry.reverses_entry_id),
        "corrects_entry_id": _identifier(entry.corrects_entry_id),
        "evidence": _evidence_list_state(entry.evidence),
    }


def financial_transaction_state_payload(transaction: FinancialTransaction) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinancialTransaction`'s
    own state (all eighteen fields), used for Audit Core's `after_hash`.

    `version` is in the hash: it is the optimistic-concurrency token, and
    two states differing only in version are two states. `provenance` is
    hashed with `recorded_by_authority` included, which is the anchor
    `assert_provenance_unchanged` protects (`ФИН-40`)."""
    return {
        "financial_transaction_id": str(transaction.transaction_id),
        "scope": _scope(transaction.scope),
        "provenance": _provenance_state(transaction.provenance),
        "transaction_date": _day(transaction.transaction_date),
        "posting_date": _day(transaction.posting_date),
        "recorded_at": _instant(transaction.recorded_at),
        "reporting_period": _period_ref_state(transaction.reporting_period),
        "value_date": _day(transaction.value_date),
        "classification_code": transaction.classification_code,
        "classification_policy": _policy(transaction.classification_policy),
        "party_handle_reference": transaction.party_handle_reference,
        "evidence": _evidence_list_state(transaction.evidence),
        "status": transaction.status.value,
        "journal_entry_id": _identifier(transaction.journal_entry_id),
        "internal_transfer_reference": transaction.internal_transfer_reference,
        "corrects_transaction_id": _identifier(transaction.corrects_transaction_id),
        "reverses_transaction_id": _identifier(transaction.reverses_transaction_id),
        "version": transaction.version,
    }


def _contribution_receipt_state(receipt: ContributionReceipt) -> dict[str, object]:
    """All eight fields of the create-once `ContributionReceipt`. This is
    the fact every later decision is recorded *around*, and
    `assert_receipt_unchanged` compares whole receipts - so a snapshot
    missing a field would be a snapshot that could not detect the edit the
    aggregate refuses (`ФИН-18`)."""
    return {
        "receipt_id": str(receipt.receipt_id),
        "kind": receipt.kind.value,
        "received_at": _instant(receipt.received_at),
        "method": receipt.method,
        "amount": _money(receipt.amount),
        "in_kind_valuation": _in_kind_valuation_state(receipt.in_kind_valuation),
        "contributor_handle_reference": receipt.contributor_handle_reference,
        "evidence": _evidence_list_state(receipt.evidence),
    }


def _contribution_assessment_state(
    assessment: ContributionAssessment | None,
) -> dict[str, object] | None:
    """All eleven fields of a `ContributionAssessment`.

    The three unknowns stay three separate booleans and codes -
    `source_determined`, `verification_complete` and a policy-bound
    `classification_code` - because the aggregate refuses acceptance for
    each with its own reason code, and a single "resolved" flag in the
    hash would make it impossible to prove which one was open
    (`ФИН-16`, `ФИН-41`)."""
    if assessment is None:
        return None
    return {
        "assessment_id": str(assessment.assessment_id),
        "assessed_at": _instant(assessment.assessed_at),
        "assessed_by": _authority_state(assessment.assessed_by),
        "source_determined": assessment.source_determined,
        "verification_complete": assessment.verification_complete,
        "prohibited": assessment.prohibited,
        "classification_code": assessment.classification_code,
        "policy": _policy(assessment.policy),
        "aggregation_snapshot_digest": assessment.aggregation_snapshot_digest,
        "related_party_group_reference": assessment.related_party_group_reference,
        "intermediary_declaration_reference": assessment.intermediary_declaration_reference,
    }


def finance_contribution_state_payload(contribution: FinanceContribution) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinanceContribution`'s own
    state (all nine fields), used for Audit Core's `after_hash`."""
    return {
        "finance_contribution_id": str(contribution.contribution_id),
        "scope": _scope(contribution.scope),
        "receipt": _contribution_receipt_state(contribution.receipt),
        "retention": _retention_state(contribution.retention),
        "state": contribution.state.value,
        "assessment": _contribution_assessment_state(contribution.assessment),
        "conflict": _conflict_state(contribution.conflict),
        "legal_case_reference": contribution.legal_case_reference,
        "history": _history_state(contribution.history),
    }


def sponsorship_state_payload(agreement: SponsorshipAgreement) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `SponsorshipAgreement`'s own
    state (all eighteen fields), used for Audit Core's `after_hash`.

    `benefit_description` and `counter_performance` are free-text fields
    and are in the hash precisely because they are: whether a
    counter-performance was described is the whole difference between
    sponsorship and a donation (`ФИН-19`), and it must be provable that the
    description was not rewritten afterwards. Neither ever leaves this
    module on a wire payload."""
    return {
        "sponsorship_agreement_id": str(agreement.agreement_id),
        "scope": _scope(agreement.scope),
        "sponsor_handle_reference": agreement.sponsor_handle_reference,
        "benefit_description": agreement.benefit_description,
        "period_start": _day(agreement.period_start),
        "period_end": _day(agreement.period_end),
        "retention": _retention_state(agreement.retention),
        "value": _money(agreement.value),
        "in_kind_valuation": _in_kind_valuation_state(agreement.in_kind_valuation),
        "counter_performance": agreement.counter_performance,
        "counter_performance_absent_policy_binding": _policy(
            agreement.counter_performance_absent_policy_binding
        ),
        "linked_activity_reference": agreement.linked_activity_reference,
        "disclosure_class": agreement.disclosure_class,
        "review_state": agreement.review_state.value,
        "conflict": _conflict_state(agreement.conflict),
        "conflict_reference": agreement.conflict_reference,
        "evidence": _evidence_list_state(agreement.evidence),
        "history": _history_state(agreement.history),
    }


def external_benefit_state_payload(benefit: ExternalFinancialBenefit) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `ExternalFinancialBenefit`'s
    own state (all thirteen fields), used for Audit Core's `after_hash`.

    `subject_kind` is in the hash because it is what keeps this record a
    finance record: the constructor refuses a PACK-35 subject, and the hash
    is what shows the subject was not changed into one afterwards
    (`ФИН-20`)."""
    return {
        "external_financial_benefit_id": str(benefit.benefit_id),
        "scope": _scope(benefit.scope),
        "benefit_type": benefit.benefit_type.value,
        "retention": _retention_state(benefit.retention),
        "subject_kind": benefit.subject_kind,
        "value": _money(benefit.value),
        "in_kind_valuation": _in_kind_valuation_state(benefit.in_kind_valuation),
        "state": benefit.state.value,
        "assessment_outcome": benefit.assessment_outcome,
        "disclosure_class": benefit.disclosure_class,
        "provider_handle_reference": benefit.provider_handle_reference,
        "evidence": _evidence_list_state(benefit.evidence),
        "history": _history_state(benefit.history),
    }


def expense_claim_state_payload(claim: ExpenseClaim) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `ExpenseClaim`'s own state
    (all eleven fields), used for Audit Core's `after_hash`.

    The claimant appears only as the opaque purpose-scoped handle
    reference, here as everywhere (`ФИН-01`)."""
    return {
        "expense_claim_id": str(claim.claim_id),
        "scope": _scope(claim.scope),
        "claimant_handle_reference": claim.claimant_handle_reference,
        "purpose_class": claim.purpose_class,
        "amount": _money(claim.amount),
        "retention": _retention_state(claim.retention),
        "evidence": _evidence_list_state(claim.evidence),
        "state": claim.state.value,
        "payment_authorization_id": _identifier(claim.payment_authorization_id),
        "corrects_claim_id": _identifier(claim.corrects_claim_id),
        "history": _history_state(claim.history),
    }


def payment_authorization_state_payload(
    authorization: PaymentAuthorization,
) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `PaymentAuthorization`'s own
    state (all thirteen fields), used for Audit Core's `after_hash`.

    Both authorities are hashed in full: the separation of authorising from
    executing is the invariant this record exists for, and only a snapshot
    carrying both can show it held (`ФИН-31`)."""
    return {
        "payment_authorization_id": str(authorization.authorization_id),
        "scope": _scope(authorization.scope),
        "payable_kind": authorization.payable_kind,
        "payable_reference": str(authorization.payable_reference),
        "authorising_authority": _authority_state(authorization.authorising_authority),
        "amount": _money(authorization.amount),
        "authorized_at": _instant(authorization.authorized_at),
        "reason": _reason_state(authorization.reason),
        "state": authorization.state.value,
        "payee_handle_reference": authorization.payee_handle_reference,
        "executed_by": _authority_state(authorization.executed_by),
        "executed_at": _instant(authorization.executed_at),
        "evidence": _evidence_list_state(authorization.evidence),
    }


def financial_asset_state_payload(asset: FinancialAsset) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinancialAsset`'s own state
    (all twelve fields), used for Audit Core's `after_hash`.

    `method_reference` and `valuation_date` are hashed with the valuation
    itself: an unexplained change of carrying value is indistinguishable
    from an unrecorded write-off, so the three have to move together
    (canon 19f.11)."""
    return {
        "financial_asset_id": str(asset.asset_id),
        "scope": _scope(asset.scope),
        "asset_class": asset.asset_class,
        "valuation": _money(asset.valuation),
        "valuation_date": _day(asset.valuation_date),
        "method_reference": asset.method_reference,
        "retention": _retention_state(asset.retention),
        "state": asset.state.value,
        "asset_reference": asset.asset_reference,
        "legal_case_reference": asset.legal_case_reference,
        "evidence": _evidence_list_state(asset.evidence),
        "history": _history_state(asset.history),
    }


def financial_obligation_state_payload(obligation: FinancialObligation) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinancialObligation`'s own
    state (all thirteen fields), used for Audit Core's `after_hash`."""
    return {
        "financial_obligation_id": str(obligation.obligation_id),
        "scope": _scope(obligation.scope),
        "obligation_type": obligation.obligation_type.value,
        "amount": _money(obligation.amount),
        "valuation_date": _day(obligation.valuation_date),
        "method_reference": obligation.method_reference,
        "retention": _retention_state(obligation.retention),
        "state": obligation.state.value,
        "counterparty_handle_reference": obligation.counterparty_handle_reference,
        "settlement_authorization_id": _identifier(obligation.settlement_authorization_id),
        "legal_case_reference": obligation.legal_case_reference,
        "evidence": _evidence_list_state(obligation.evidence),
        "history": _history_state(obligation.history),
    }


def reporting_obligation_state_payload(obligation: ReportingObligation) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ReportingObligation`'s own
    state (all eight fields), used for Audit Core's `after_hash`.

    `fulfilling_submission_reference` is in the hash because fulfilment
    exists only through a recorded submission: without it in the snapshot,
    a `fulfilled` status would be unfalsifiable (canon 19f.16)."""
    return {
        "reporting_obligation_id": str(obligation.obligation_id),
        "scope": _scope(obligation.scope),
        "period": _period_ref_state(obligation.period),
        "obligation_kind": obligation.obligation_kind.value,
        "statutory_deadline_reference": obligation.statutory_deadline_reference,
        "state": obligation.state.value,
        "fulfilling_submission_reference": obligation.fulfilling_submission_reference,
        "history": _history_state(obligation.history),
    }


def perimeter_definition_state_payload(
    definition: ReportingPerimeterDefinition,
) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a
    `ReportingPerimeterDefinition`'s own state (all eight fields), used for
    Audit Core's `after_hash`.

    `included_scopes` is hashed in stored order, not sorted. The *digest*
    computed by `reporting.freeze_perimeter` sorts, deliberately, so two
    freezes of one definition agree; this snapshot is of the definition
    record as stored, and re-ordering it here would hash something other
    than what exists (`ФИН-25`)."""
    return {
        "perimeter_definition_id": str(definition.definition_id),
        "scope": _scope(definition.scope),
        "definition_version": definition.version,
        "effective_from": _day(definition.effective_from),
        "included_scopes": [_scope(scope) for scope in definition.included_scopes],
        "effective_until": _day(definition.effective_until),
        "state": definition.state.value,
        "history": _history_state(definition.history),
    }


def _perimeter_snapshot_state(perimeter: PerimeterSnapshot) -> dict[str, object]:
    """All five fields of a frozen `PerimeterSnapshot`."""
    return {
        "perimeter_definition_id": str(perimeter.definition_id),
        "definition_version": perimeter.definition_version,
        "included_scopes": [_scope(scope) for scope in perimeter.included_scopes],
        "digest": perimeter.digest,
        "frozen_at": _instant(perimeter.frozen_at),
    }


def report_snapshot_state_payload(snapshot: ReportSnapshot) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `ReportSnapshot`'s own state
    (all nine fields), used for Audit Core's `after_hash`.

    The included transaction and entry identifiers are hashed in full, not
    as counts. `content_digest` already covers them, but it is a value the
    record stores: hashing the identifiers alongside it is what lets a
    reader detect a snapshot whose digest and contents were changed
    together, which the constructor's own consistency check cannot
    (`ФИН-24`)."""
    return {
        "report_snapshot_id": str(snapshot.snapshot_id),
        "scope": _scope(snapshot.scope),
        "period": _period_ref_state(snapshot.period),
        "perimeter": _perimeter_snapshot_state(snapshot.perimeter),
        "content_digest": snapshot.content_digest,
        "frozen_at": _instant(snapshot.frozen_at),
        "policy_bindings": [binding.to_payload() for binding in snapshot.policy_bindings],
        "included_transaction_ids": [
            str(identifier) for identifier in snapshot.included_transaction_ids
        ],
        "included_entry_ids": [str(identifier) for identifier in snapshot.included_entry_ids],
    }


def _review_record_state(review: ReviewRecord) -> dict[str, object]:
    """All five fields of one internal `ReviewRecord`."""
    return {
        "review_id": str(review.review_id),
        "reviewed_at": _instant(review.reviewed_at),
        "reviewer": _authority_state(review.reviewer),
        "outcome": review.outcome.value,
        "finding_references": list(review.finding_references),
    }


def _correction_request_state(request: CorrectionRequest) -> dict[str, object]:
    """All five fields of one recorded `CorrectionRequest`."""
    return {
        "correction_request_id": str(request.request_id),
        "requested_at": _instant(request.requested_at),
        "requested_by": _authority_state(request.requested_by),
        "reason": _reason_state(request.reason),
        "finding_references": list(request.finding_references),
    }


def _approval_record_state(approval: ApprovalRecord | None) -> dict[str, object] | None:
    """All five fields of the create-once `ApprovalRecord`."""
    if approval is None:
        return None
    return {
        "approval_id": str(approval.approval_id),
        "approved_at": _instant(approval.approved_at),
        "approved_by": _authority_state(approval.approved_by),
        "reason": _reason_state(approval.reason),
        "policy": _policy(approval.policy),
    }


def _signature_record_state(signature: SignatureRecord | None) -> dict[str, object] | None:
    """All five fields of the create-once `SignatureRecord`. A record that a
    named authority signed - never a cryptographic signature value, of
    which PACK-10 holds none."""
    if signature is None:
        return None
    return {
        "signature_id": str(signature.signature_id),
        "signed_at": _instant(signature.signed_at),
        "signed_by": _authority_state(signature.signed_by),
        "reason": _reason_state(signature.reason),
        "policy": _policy(signature.policy),
    }


def _audit_opinion_reference_state(
    reference: AuditOpinionReference | None,
) -> dict[str, object] | None:
    """All four fields of an `AuditOpinionReference` - a reference to a
    concluded engagement, never the conclusion itself."""
    if reference is None:
        return None
    return {
        "audit_engagement_id": str(reference.engagement_id),
        "conclusion_reference": reference.conclusion_reference,
        "auditor": _authority_state(reference.auditor),
        "recorded_at": _instant(reference.recorded_at),
    }


def _submission_reference_state(
    reference: ExternalSubmissionReference | None,
) -> dict[str, object] | None:
    """All three fields of the create-once `ExternalSubmissionReference`."""
    if reference is None:
        return None
    return {
        "submission_reference": reference.submission_reference,
        "recipient_reference": reference.recipient_reference,
        "submitted_at": _instant(reference.submitted_at),
    }


def _acceptance_reference_state(
    reference: ExternalAcceptanceReference | None,
) -> dict[str, object] | None:
    """All four fields of an `ExternalAcceptanceReference`, `kind` included.

    `kind` is the field that decides whether the reference is a legal
    decision or delivery telemetry, so a snapshot without it could not
    show which one was stored (`ФИН-26`, `ФИН-27`)."""
    if reference is None:
        return None
    return {
        "notice_effect_reference": reference.notice_effect_reference,
        "kind": reference.kind.value,
        "decided_at": _instant(reference.decided_at),
        "deciding_authority_reference": reference.deciding_authority_reference,
    }


def _publication_reference_state(
    reference: PublicationReference | None,
) -> dict[str, object] | None:
    """All three fields of the create-once `PublicationReference`."""
    if reference is None:
        return None
    return {
        "publication_reference": reference.publication_reference,
        "publication_authorization_id": str(reference.authorization_id),
        "published_at": _instant(reference.published_at),
    }


def report_version_state_payload(version: FinanceReportVersion) -> dict[str, object]:
    """Full, canonically-hashable snapshot of a `FinanceReportVersion`'s own
    state (all nineteen fields), used for Audit Core's `after_hash`.

    The acknowledgement and the acceptance references are two separate
    fields in the hash, as they are on the aggregate: canon 19f.17 says
    acknowledgement never implies acceptance, and a snapshot that merged
    them into one "external reference" would erase exactly the distinction
    (`ФИН-26`, `ФИН-27`). `_PREPARABLE_STATES` is a `ClassVar` and not part
    of the state, so it is absent by intent, not by oversight."""
    return {
        "report_version_id": str(version.version_id),
        "report_id": str(version.report_id),
        "scope": _scope(version.scope),
        "period": _period_ref_state(version.period),
        "version": version.version,
        "state": version.state.value,
        "report_snapshot_id": _identifier(version.snapshot_id),
        "restatement_of_version_reference": _identifier(version.restatement_of_version_reference),
        "correction_kind": (
            None if version.correction_kind is None else version.correction_kind.value
        ),
        "review_records": [_review_record_state(review) for review in version.review_records],
        "correction_requests": [
            _correction_request_state(request) for request in version.correction_requests
        ],
        "approval_record": _approval_record_state(version.approval_record),
        "signature_record": _signature_record_state(version.signature_record),
        "audit_reference": _audit_opinion_reference_state(version.audit_reference),
        "external_submission_reference": _submission_reference_state(
            version.external_submission_reference
        ),
        "external_acknowledgement_reference": _acceptance_reference_state(
            version.external_acknowledgement_reference
        ),
        "external_acceptance_reference": _acceptance_reference_state(
            version.external_acceptance_reference
        ),
        "publication_reference": _publication_reference_state(version.publication_reference),
        "history": _history_state(version.history),
    }


def _audit_finding_state(finding: AuditFinding) -> dict[str, object]:
    """All six fields of one append-only `AuditFinding`. `summary_reference`
    is a pointer and never prose: findings are disclosed only under the
    disclosure policy and never in a form identifying anyone
    (`ФИН-35`)."""
    return {
        "audit_finding_id": str(finding.finding_id),
        "recorded_at": _instant(finding.recorded_at),
        "recorded_by": _authority_state(finding.recorded_by),
        "severity": finding.severity,
        "summary_reference": finding.summary_reference,
        "evidence": _evidence_list_state(finding.evidence),
    }


def _audit_conclusion_state(conclusion: AuditConclusion | None) -> dict[str, object] | None:
    """All six fields of the create-once `AuditConclusion`."""
    if conclusion is None:
        return None
    return {
        "audit_conclusion_id": str(conclusion.conclusion_id),
        "concluded_at": _instant(conclusion.concluded_at),
        "concluded_by": _authority_state(conclusion.concluded_by),
        "conclusion_class": conclusion.conclusion_class,
        "reason": _reason_state(conclusion.reason),
        "evidence": _evidence_list_state(conclusion.evidence),
    }


def audit_engagement_state_payload(engagement: AuditEngagement) -> dict[str, object]:
    """Full, canonically-hashable snapshot of an `AuditEngagement`'s own
    state (all eight fields), used for Audit Core's `after_hash`.

    `auditor` is hashed with its `actor_reference`, which is what the
    per-version independence check compares against the operational actor
    set: a snapshot carrying only the authority id could not show which
    actor the engagement was opened for (`ФИН-29`, `ФИН-30`)."""
    return {
        "audit_engagement_id": str(engagement.engagement_id),
        "scope": _scope(engagement.scope),
        "period": _period_ref_state(engagement.period),
        "auditor": _authority_state(engagement.auditor),
        "state": engagement.state.value,
        "findings": [_audit_finding_state(finding) for finding in engagement.findings],
        "conclusion": _audit_conclusion_state(engagement.conclusion),
        "history": _history_state(engagement.history),
    }


# ---------------------------------------------------------------------------
# The generic builder
# ---------------------------------------------------------------------------

#: The mandatory safe-metadata keys `build_finance_event` adds to every
#: payload (canon 20.17). The event type, the event version and
#: `occurred_at` are envelope fields and are not duplicated into the
#: payload; the organizational scope and the stable identifier of the
#: affected aggregate are not, so they are added here.
_SAFE_METADATA_KEYS: frozenset[str] = frozenset(
    {"organization_scope", "scope_kind", "aggregate_id"}
)


def build_finance_event(
    *,
    event_id: UUID,
    event_type: str,
    subject_type: str,
    subject_id: UUID,
    scope: OrganizationalScopeRef,
    payload: Mapping[str, object],
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """Build one canonical section-20.17 envelope, in a fixed order of
    checks.

    The order is the point, not an implementation detail:

    1. An `event_type` outside `FINANCE_EVENT_TYPES` raises
       `UnknownFinanceEventTypeError` **first**. Canon 20.17 fixes the
       seventy-two names, and a service publishing a seventy-third would
       put an unowned event type into the stream every listed consumer
       reads.
    2. `occurred_at` is required timezone-explicit through
       `domain.require_timezone`, which refuses a naive instant rather than
       assuming UTC (`ФИН-39`). `EventEnvelope` re-checks this, but with
       `InvalidEventEnvelopeError` and no finance reason code; asking here
       first is what makes the refusal a governed one.
    3. The mandatory safe metadata is merged **over** the caller's payload,
       so a builder cannot shadow the organizational scope or the aggregate
       identifier with a different value. Both are derived from the
       arguments the envelope's `subject` and the record's scope already
       use, so they cannot disagree with them either.
    4. `domain.reject_identity_payload_keys` walks the finished payload,
       nested values included. This is a structural backstop, not the
       primary control: the primary control is that each of the seventy-two
       builders below assembles a minimal payload by hand. The backstop is
       here because "someone will add a field later" is the failure mode
       `ФИН-02` exists for.
    5. Only then is the envelope built, with `build_event_envelope`
       computing `integrity.payload_hash` so no builder can compute it
       inconsistently.
    """
    if event_type not in _FINANCE_EVENT_TYPE_SET:
        raise UnknownFinanceEventTypeError(
            f"{event_type!r} is not one of the seventy-two canonical finance event types "
            "of canon section 20.17"
        )
    require_timezone(occurred_at, context=f"finance event {event_type}.occurred_at")
    final_payload: dict[str, object] = {
        **payload,
        # Canon 20.17's mandatory safe metadata: the record's
        # organizational scope and the stable identifier of the affected
        # aggregate. Never the acting actor's identity.
        "organization_scope": str(scope.organization_id),
        "scope_kind": scope.scope_kind,
        "aggregate_id": str(subject_id),
    }
    reject_identity_payload_keys(final_payload, context=f"finance event {event_type}")
    return build_event_envelope(
        event_id=event_id,
        event_type=event_type,
        event_version=EVENT_VERSION,
        occurred_at=occurred_at,
        producer=_PRODUCER,
        actor=actor,
        subject=SubjectRef(subject_type=subject_type, subject_id=subject_id),
        correlation_id=correlation_id,
        causation_id=causation_id,
        payload=final_payload,
    )


# ---------------------------------------------------------------------------
# Accounts, periods, the accounting register, provenance (19f.4-19f.6)
# ---------------------------------------------------------------------------
#
# Public projection of any individual event in this group is refused
# outright by canon 20.17; only aggregated derived figures inside a
# published report version ever reach the public. None of these payloads is
# shaped for publication, and none is in `PUBLIC_PROJECTION_ALLOWED`.


def build_finance_account_created_event(
    *,
    event_id: UUID,
    account: FinanceAccount,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_account.created` (canon 19f.4): a chart-of-accounts node
    created in an organizational scope.

    Carries the node's identity, its scope-unique code and its status. It
    does **not** carry the account's history, its retention binding or the
    classification policy binding - the first is the audit trail's business
    and the other two are internal bindings no consumer of this stream acts
    on."""
    payload: dict[str, object] = {
        "finance_account_id": str(account.account_id),
        "code": account.code,
        "status": account.status.value,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_account.created",
        subject_type="finance_account",
        subject_id=account.account_id,
        scope=account.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_account_status_changed_event(
    *,
    event_id: UUID,
    account: FinanceAccount,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_account.status_changed` (canon 19f.4): activation,
    restriction or closure.

    Carries the resulting status, the one reason code section 24 requires
    and the acting authority's reference. It does **not** carry the actor
    behind that authority, and it does not carry balances - a status change
    says nothing about what was posted."""
    payload: dict[str, object] = {
        "finance_account_id": str(account.account_id),
        "status": account.status.value,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_account.status_changed",
        subject_type="finance_account",
        subject_id=account.account_id,
        scope=account.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_accounting_period_opened_event(
    *,
    event_id: UUID,
    period: AccountingPeriod,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`accounting_period.opened` (canon 19f.5): the period's boundaries and
    its timezone fixed explicitly.

    The named IANA timezone travels with the boundaries because a boundary
    without one is not a civil-calendar fact (`ФИН-42`). It does **not**
    carry the period's reopening records or history."""
    payload: dict[str, object] = {
        "period_id": str(period.period_id),
        "label": period.label,
        "timezone_name": period.timezone_name,
        "opens_at": _instant(period.opens_at),
        "closes_at": _instant(period.closes_at),
        "status": period.status.value,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="accounting_period.opened",
        subject_type="accounting_period",
        subject_id=period.period_id,
        scope=period.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_accounting_period_closed_event(
    *,
    event_id: UUID,
    period: AccountingPeriod,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`accounting_period.closed` (canon 19f.5): the period locked, with the
    fingerprint of its closed state included.

    Canon 19f.5 asks for a fingerprint of the closing balances. This
    aggregate is pure and holds no balances, so what travels is
    `AccountingPeriod.state_digest()`, the digest of the
    identity, boundaries and lock state that a `PeriodReopeningRecord` also
    snapshots; the two are comparable, which is what a reopening dispute
    needs. A balances fingerprint belongs to whichever derived read model
    computes balances, and claiming to carry one here would be a claim this
    module cannot honour. The payload carries **no** balance figures for
    that reason."""
    payload: dict[str, object] = {
        "period_id": str(period.period_id),
        "status": period.status.value,
        "closed_state_digest": period.state_digest(),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="accounting_period.closed",
        subject_type="accounting_period",
        subject_id=period.period_id,
        scope=period.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_accounting_period_reopening_requested_event(
    *,
    event_id: UUID,
    period: AccountingPeriod,
    record: PeriodReopeningRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`accounting_period.reopening_requested` (canon 19f.5): a reopening of
    a closed period has been requested.

    Carries both sides of the dual control as authority references, because
    the record's existence *is* the evidence that dual control was
    satisfied (`ФИН-11`). It does **not** carry the actors behind either
    authority, and it does not carry the reopening's note reference or any
    free text explaining it."""
    payload: dict[str, object] = {
        "period_id": str(period.period_id),
        "reopening_record_id": str(record.record_id),
        "requested_at": _instant(record.requested_at),
        "requesting_authority": _authority_on_the_wire(record.requested_by),
        "approving_authority": _authority_on_the_wire(record.approved_by),
        "reason_code": record.reason.reason_code,
        "policy": _policy(record.policy),
        "closed_state_digest": record.closed_state_digest,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="accounting_period.reopening_requested",
        subject_type="accounting_period",
        subject_id=period.period_id,
        scope=period.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_accounting_period_reopened_event(
    *,
    event_id: UUID,
    period: AccountingPeriod,
    record: PeriodReopeningRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`accounting_period.reopened` (canon 19f.5): the period reopened
    against a `PeriodReopeningRecord`; authority, grounds and dual control
    are all mandatory.

    Carries the resulting status, the approving authority, the reason code,
    the bound policy version and the closed-state digest the record
    snapshots. The PACK-09 case and hold references are opaque outward
    references and travel as such; they are **not** interpreted here, and no
    retention or legal-hold decision is expressed by this event
    (`ФИН-22`)."""
    payload: dict[str, object] = {
        "period_id": str(period.period_id),
        "status": period.status.value,
        "reopening_record_id": str(record.record_id),
        "approved_at": _instant(record.approved_at),
        "approving_authority": _authority_on_the_wire(record.approved_by),
        "reason_code": record.reason.reason_code,
        "policy": _policy(record.policy),
        "closed_state_digest": record.closed_state_digest,
        "legal_case_reference": record.legal_case_reference,
        "hold_reference": record.hold_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="accounting_period.reopened",
        subject_type="accounting_period",
        subject_id=period.period_id,
        scope=period.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_journal_entry_drafted_event(
    *,
    event_id: UUID,
    entry: JournalEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`journal_entry.drafted` (canon 19f.4): a draft posting created.

    Carries the entry's identity, its status, its reporting period, its line
    count and its reason code. It deliberately carries **no** amounts and no
    posting lines: a draft has no monetary effect yet - `entry_sequence` is
    `None` until posting - and publishing its figures would put an
    unrealised effect into a stream five other packs read."""
    payload: dict[str, object] = {
        "journal_entry_id": str(entry.entry_id),
        "status": entry.status.value,
        "period_id": str(entry.period.period_id),
        "line_count": len(entry.lines),
        "reason_code": entry.reason.reason_code,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="journal_entry.drafted",
        subject_type="journal_entry",
        subject_id=entry.entry_id,
        scope=entry.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_journal_entry_posted_event(
    *,
    event_id: UUID,
    entry: JournalEntry,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`journal_entry.posted` (canon 19f.4): the entry posted, with the
    result of the balance check included.

    The balance check result is reported as per-currency debit and credit
    totals, never netted across currencies (`ФИН-09`). `balanced` is a
    *recorded outcome* and not a claim computed here: `JournalEntry`'s
    constructor and `ledger.post` both ran `assert_balanced`, so an
    unbalanced posted entry cannot exist to be described. The payload
    carries **no** posting lines, so no account-level breakdown of a single
    entry reaches the stream (`ФИН-03`)."""
    debit_totals = sum_money(tuple(line.amount for line in entry.lines if line.is_debit))
    credit_totals = sum_money(tuple(line.amount for line in entry.lines if not line.is_debit))
    payload: dict[str, object] = {
        "journal_entry_id": str(entry.entry_id),
        "status": entry.status.value,
        "entry_sequence": entry.entry_sequence,
        "period_id": str(entry.period.period_id),
        "financial_transaction_id": _identifier(entry.transaction_id),
        "balance_check": {
            "balanced": True,
            "debit_minor_units_by_currency": dict(debit_totals),
            "credit_minor_units_by_currency": dict(credit_totals),
        },
    }
    return build_finance_event(
        event_id=event_id,
        event_type="journal_entry.posted",
        subject_type="journal_entry",
        subject_id=entry.entry_id,
        scope=entry.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_journal_entry_reversed_event(
    *,
    event_id: UUID,
    entry: JournalEntry,
    reversal: JournalEntry,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`journal_entry.reversed` (canon 19f.4): a reversing entry posted; the
    reason code is mandatory.

    The subject is the **original** entry, whose status changed; the
    reversal's own identity travels as `reversing_entry_id` so the two acts
    stay distinguishable in the chain (`ФИН-06`). It carries **no** amounts:
    a reversal's lines are the original's with each side flipped and each
    amount unchanged, so restating them would add nothing a consumer cannot
    derive, and re-booking the corrected effect is an ordinary new entry
    with its own `journal_entry.posted`."""
    payload: dict[str, object] = {
        "journal_entry_id": str(entry.entry_id),
        "status": entry.status.value,
        "reversing_entry_id": str(reversal.entry_id),
        "reason_code": reason.reason_code,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="journal_entry.reversed",
        subject_type="journal_entry",
        subject_id=entry.entry_id,
        scope=entry.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_transaction_recorded_event(
    *,
    event_id: UUID,
    transaction: FinancialTransaction,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_transaction.recorded` (canon 19f.6): the business fact
    recorded.

    Carries the dates, the provenance kind, the import-batch reference where
    one exists, the reporting period and the counterparty as the opaque
    `fph:` handle reference only. It does **not** carry a bank detail, a
    payment identifier, a payer name or the provenance's
    `recorded_by_authority`; the source-system reference is deliberately
    absent too, since it identifies an external system and the batch
    reference already answers "where did this come from" (`ФИН-38`)."""
    payload: dict[str, object] = {
        "financial_transaction_id": str(transaction.transaction_id),
        "status": transaction.status.value,
        "transaction_date": _day(transaction.transaction_date),
        "posting_date": _day(transaction.posting_date),
        "value_date": _day(transaction.value_date),
        "reporting_period_id": str(transaction.reporting_period.period_id),
        "provenance_kind": transaction.provenance.kind.value,
        "import_batch_reference": transaction.provenance.import_batch_reference,
        "party_handle_reference": transaction.party_handle_reference,
        "internal_transfer_reference": transaction.internal_transfer_reference,
        "version": transaction.version,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_transaction.recorded",
        subject_type="financial_transaction",
        subject_id=transaction.transaction_id,
        scope=transaction.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_transaction_classification_changed_event(
    *,
    event_id: UUID,
    transaction: FinancialTransaction,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_transaction.classification_changed` (canon 19f.6):
    classification or reclassification of a register record.

    Carries the new classification code together with the exact policy
    version that produced it: a classification without its binding can be
    silently rewritten by a later policy change (`ФИН-23`). `version` travels
    so a consumer can tell two successive reclassifications apart. It does
    **not** carry the previous classification - the register's own history
    is authoritative for that, and a wire payload restating it would become a
    second, divergeable copy."""
    payload: dict[str, object] = {
        "financial_transaction_id": str(transaction.transaction_id),
        "status": transaction.status.value,
        "classification_code": transaction.classification_code,
        "policy": _policy(transaction.classification_policy),
        "version": transaction.version,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_transaction.classification_changed",
        subject_type="financial_transaction",
        subject_id=transaction.transaction_id,
        scope=transaction.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_reconciliation_recorded_event(
    *,
    event_id: UUID,
    reconciliation_record_id: UUID,
    scope: OrganizationalScopeRef,
    finance_account_id: UUID,
    period: ReportingPeriodRef,
    outcome_code: str,
    authority: AuthorityReference,
    reason: ReasonCoded,
    statement_reference: str | None,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`reconciliation.recorded` (canon 19f.6): a reconciliation act
    recorded.

    Takes typed arguments rather than an aggregate: `ReconciliationRecord`
    is a create-once, terminal record and PACK-10's pure modules do not
    model it, so this builder names exactly the facts canon 19f.6 fixes for
    it. `statement_reference` is an **opaque** pointer at material PACK-11
    owns: no statement content, no bank detail and no account number travels
    (`ФИН-21`). An auditor's own reconciliation is a finding on an
    `AuditEngagement` and never this event (canon 19f.18)."""
    payload: dict[str, object] = {
        "reconciliation_record_id": str(reconciliation_record_id),
        "finance_account_id": str(finance_account_id),
        "reporting_period_id": str(period.period_id),
        "outcome_code": outcome_code,
        "state": "recorded",
        "statement_reference": statement_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="reconciliation.recorded",
        subject_type="reconciliation_record",
        subject_id=reconciliation_record_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_import_batch_registered_event(
    *,
    event_id: UUID,
    import_batch_id: UUID,
    scope: OrganizationalScopeRef,
    provenance: Provenance,
    batch_fingerprint: str,
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`import_batch.registered` (canon 19f.6): a batch registered with the
    provenance of its source.

    The fingerprint is what makes replay detectable, so it travels; the
    import authority travels because canon 19f.6 keeps it separate from the
    posting authority and never implied by it. It carries **no** imported
    line content, no file bytes and no payer or payment identifier from the
    source file (`ФИН-21`, `ФИН-38`)."""
    payload: dict[str, object] = {
        "import_batch_id": str(import_batch_id),
        "state": "registered",
        "provenance_kind": provenance.kind.value,
        "source_system_reference": provenance.source_system_reference,
        "batch_fingerprint": batch_fingerprint,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="import_batch.registered",
        subject_type="import_batch",
        subject_id=import_batch_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_import_batch_completed_event(
    *,
    event_id: UUID,
    import_batch_id: UUID,
    scope: OrganizationalScopeRef,
    batch_fingerprint: str,
    applied_line_count: int,
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`import_batch.completed` (canon 19f.6): the batch applied.

    Carries a count of applied lines and nothing from the lines themselves:
    per-line results are append-only inside the batch record, and shipping
    them would put the imported register content into the event stream
    (`ФИН-21`). Re-application of an already-applied batch is forbidden, so
    this event is emitted at most once per batch."""
    payload: dict[str, object] = {
        "import_batch_id": str(import_batch_id),
        "state": "applied",
        "batch_fingerprint": batch_fingerprint,
        "applied_line_count": applied_line_count,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="import_batch.completed",
        subject_type="import_batch",
        subject_id=import_batch_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_import_batch_rejected_event(
    *,
    event_id: UUID,
    import_batch_id: UUID,
    scope: OrganizationalScopeRef,
    batch_fingerprint: str,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`import_batch.rejected` (canon 19f.6): the batch rejected.

    Carries exactly one reason code from section 24 and the deciding
    authority. It does **not** carry a per-line error listing or any
    rejected line's content: a rejection is a decision about the batch, and
    the diagnostics belong to the batch record a caller may read under
    scope (`ФИН-03`, `ФИН-40`)."""
    payload: dict[str, object] = {
        "import_batch_id": str(import_batch_id),
        "state": "rejected",
        "batch_fingerprint": batch_fingerprint,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="import_batch.rejected",
        subject_type="import_batch",
        subject_id=import_batch_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_import_batch_duplicate_detected_event(
    *,
    event_id: UUID,
    import_batch_id: UUID,
    scope: OrganizationalScopeRef,
    batch_fingerprint: str,
    matched_import_batch_id: UUID,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`import_batch.duplicate_detected` (canon 19f.6): a repeated or
    replayed import; the batch fingerprint matched an already-applied batch.

    Both batch identities and the shared fingerprint travel, because the
    fact *is* the collision. It carries **no** line content from either
    batch. This event does not itself permit the import: applying a batch
    whose fingerprint already exists needs an explicit, reason-coded
    override decision, which is a separate governed act."""
    payload: dict[str, object] = {
        "import_batch_id": str(import_batch_id),
        "batch_fingerprint": batch_fingerprint,
        "matched_import_batch_id": str(matched_import_batch_id),
        "reason_code": reason.reason_code,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="import_batch.duplicate_detected",
        subject_type="import_batch",
        subject_id=import_batch_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# Contributions, sponsorship, external financial benefit (19f.7-19f.9)
# ---------------------------------------------------------------------------
#
# The contributor, the sponsor and the provider appear in every payload of
# this group as an opaque `fph:` handle reference and in no other form: not
# a name, not an address, not a bank detail, not a payment identifier, not
# a membership or participation reference (`ФИН-01`, `ФИН-02`). Canon 20.17
# permits public projection of this group only to the extent an active
# disclosure obligation prescribes; that extent is a disclosure-policy
# decision, and these payloads are shaped for the authoritative stream, not
# for publication.


def build_finance_contribution_received_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.received` (canon 19f.7): a contribution receipt
    record created.

    Carries the amount, because the amount received *is* the fact, and the
    contributor solely as the opaque handle reference - or as `None`, which
    is itself the recorded fact that the source could not be established and
    the reason the contribution quarantines (`ФИН-16`). It does **not** carry
    the receipt's payment `method`, no evidence reference and no in-kind
    valuation basis; `in_kind` reports only *that* the receipt was
    non-monetary."""
    receipt = contribution.receipt
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "contribution_kind": receipt.kind.value,
        "received_at": _instant(receipt.received_at),
        "amount": _money(receipt.amount),
        "in_kind": receipt.in_kind_valuation is not None,
        "contributor_handle_reference": receipt.contributor_handle_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.received",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_quarantined_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.quarantined` (canon 19f.7): preliminary
    quarantine pending establishment of the source.

    Carries the reason code that says *which* unknown is open and the
    deciding authority. It carries **no** amount and no contributor
    reference: a quarantine is a governed admission that a question is
    still open, and a payload restating who paid what would make the
    unresolved record more disclosing than the resolved one."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.quarantined",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_assessed_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    assessment: ContributionAssessment,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.assessed` (canon 19f.8): an assessment recorded,
    with the `AggregationSnapshot` fingerprint included.

    The three unknowns travel as three separate flags, because the aggregate
    refuses acceptance for each with its own reason code and one merged
    "resolved" boolean would hide which was open (`ФИН-16`, `ФИН-41`). The
    aggregation digest travels so the threshold decision stays answerable
    against the aggregate it was taken on (`ФИН-14`, `ФИН-15`). It carries
    **no** aggregate total, no per-contributor sum and no list of the
    contributions aggregated - those are the splitting-detection view's own
    figures, subject to statistical disclosure control (`ФИН-35`)."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "assessment_id": str(assessment.assessment_id),
        "source_determined": assessment.source_determined,
        "verification_complete": assessment.verification_complete,
        "prohibited": assessment.prohibited,
        "classification_code": assessment.classification_code,
        "policy": _policy(assessment.policy),
        "aggregation_snapshot_digest": assessment.aggregation_snapshot_digest,
        "related_party_group_reference": assessment.related_party_group_reference,
        "assessing_authority": _authority_on_the_wire(assessment.assessed_by),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.assessed",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_accepted_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.accepted` (canon 19f.7): acceptance decided.

    Names the resolved assessment and the policy version it was accepted
    under, because acceptance is only ever reachable through one
    (`ФИН-16`, `ФИН-17`), plus the amount now recognised as income. The
    contributor travels as the opaque handle reference only. It carries
    **no** identity attribute of the contributor and no evidence reference
    for the verification that completed."""
    assessment = contribution.assessment
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "assessment_id": None if assessment is None else str(assessment.assessment_id),
        "classification_code": None if assessment is None else assessment.classification_code,
        "policy": None if assessment is None else _policy(assessment.policy),
        "amount": _money(contribution.receipt.amount),
        "contributor_handle_reference": contribution.receipt.contributor_handle_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.accepted",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_rejected_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.rejected` (canon 19f.7): rejection decided.

    Carries the reason code and the deciding authority and nothing more. No
    amount, no contributor reference and no free-text explanation: the
    receipt stays exactly as received and a rejection says only that the
    contribution was refused (`ФИН-18`, `ФИН-40`)."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.rejected",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_return_required_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.return_required` (canon 19f.7): a return
    obligation established.

    Carries the amount owed back, because the obligation is *for* that
    amount (`ФИН-17`), plus the reason code and the deciding authority. It
    carries **no** payee bank detail, no payment instruction and no
    contributor identity: how the return is executed is a
    `PaymentAuthorization`, and that record names an opaque payee handle
    too."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "amount": _money(contribution.receipt.amount),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.return_required",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_returned_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    payment_authorization_id: UUID | None,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.returned` (canon 19f.7): the return executed.

    Names the `PaymentAuthorization` the payment ran under, so a return with
    no authorisation is visible as one (`ФИН-31`). The contribution stays in
    the register as one that *was* received - the payload reports the
    returned state, never a deletion, because a returned contribution is
    never treated as never received. It carries **no** payment identifier,
    bank reference or transaction number from the executing system."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "payment_authorization_id": _identifier(payment_authorization_id),
        "amount": _money(contribution.receipt.amount),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.returned",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_contribution_escalated_event(
    *,
    event_id: UUID,
    contribution: FinanceContribution,
    legal_case_reference: str,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_contribution.escalated` (canon 19f.7): escalation into a
    PACK-09 legal case, by safe reference.

    The case reference is mandatory and travels **opaquely**: PACK-09 owns
    the case, the deadline, the notice and the legal hold, and this event
    neither interprets nor asserts any of them (`ФИН-22`, `ФИН-44`). It
    carries no case content, no allegation text, no amount and no
    contributor reference."""
    payload: dict[str, object] = {
        "finance_contribution_id": str(contribution.contribution_id),
        "state": contribution.state.value,
        "legal_case_reference": legal_case_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_contribution.escalated",
        subject_type="finance_contribution",
        subject_id=contribution.contribution_id,
        scope=contribution.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_in_kind_valuation_recorded_event(
    *,
    event_id: UUID,
    subject_type: str,
    subject_id: UUID,
    scope: OrganizationalScopeRef,
    valuation: InKindValuation,
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_in_kind_valuation.recorded` (canon 19f.9): a valuation of a
    non-monetary provision, with a reference to the method.

    The subject is the **valued aggregate**, which canon 20.17 leaves as
    either a `FinanceContribution` or an `ExternalFinancialBenefit`; the
    caller names which, since only the caller knows what it valued. Carries
    the method reference, the valuation date, the valued amount and the
    evidence pointer. It deliberately does **not** carry
    `InKindValuation.basis`: the basis is free text and canon 19f.9 asks for
    a reference to the method, which `method_reference` is. Nor does it carry
    any evidence content - the reference identifies material PACK-11 owns
    (`ФИН-21`)."""
    payload: dict[str, object] = {
        "valued_aggregate_type": subject_type,
        "valued_aggregate_id": str(subject_id),
        "method_reference": valuation.method_reference,
        "valuation_date": _day(valuation.valuation_date),
        "valued_amount": _money(valuation.valued_amount),
        "evidence_kind": valuation.evidence_reference.kind.value,
        "evidence_reference": valuation.evidence_reference.external_reference,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_in_kind_valuation.recorded",
        subject_type=subject_type,
        subject_id=subject_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_sponsorship_registered_event(
    *,
    event_id: UUID,
    agreement: SponsorshipAgreement,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`sponsorship.registered` (canon 19f.9): the agreement registered.

    Carries the agreed period, the value and the sponsor as the opaque
    handle reference. It deliberately does **not** carry
    `benefit_description` or `counter_performance`: both are free text, and
    whether a counter-performance exists is reported as a boolean on
    `sponsorship.approved` where the decision is made. Nothing here records
    a meeting, a contact, a calendar entry or an access relationship - those
    are PACK-35's entities and PACK-10 implements none of them
    (`ФИН-20`)."""
    payload: dict[str, object] = {
        "sponsorship_agreement_id": str(agreement.agreement_id),
        "review_state": agreement.review_state.value,
        "sponsor_handle_reference": agreement.sponsor_handle_reference,
        "period_start": _day(agreement.period_start),
        "period_end": _day(agreement.period_end),
        "value": _money(agreement.value),
        "in_kind": agreement.in_kind_valuation is not None,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="sponsorship.registered",
        subject_type="sponsorship_agreement",
        subject_id=agreement.agreement_id,
        scope=agreement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_sponsorship_approved_event(
    *,
    event_id: UUID,
    agreement: SponsorshipAgreement,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`sponsorship.approved` (canon 19f.9): the counter-performance, or an
    explicit policy classification of its absence, recorded.

    Reports *which* of the two grounds the approval rests on:
    `counter_performance_recorded` as a boolean, and the policy binding that
    classified the agreement as one without. It carries the description of
    neither - a free-text counter-performance on the wire would be exactly
    the disclosure-by-default this group forbids, and the boolean plus the
    binding is what a consumer needs to know the approval was not made on
    nothing (`ФИН-19`)."""
    described = bool(agreement.counter_performance and agreement.counter_performance.strip())
    payload: dict[str, object] = {
        "sponsorship_agreement_id": str(agreement.agreement_id),
        "review_state": agreement.review_state.value,
        "counter_performance_recorded": described,
        "counter_performance_absent_policy": _policy(
            agreement.counter_performance_absent_policy_binding
        ),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="sponsorship.approved",
        subject_type="sponsorship_agreement",
        subject_id=agreement.agreement_id,
        scope=agreement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_sponsorship_rejected_event(
    *,
    event_id: UUID,
    agreement: SponsorshipAgreement,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`sponsorship.rejected` (canon 19f.9): the agreement rejected.

    The reason code and the deciding authority, and nothing else: no
    sponsor reference, no value and no free-text ground. A rejected
    agreement is a refused offer, and the payload says no more than
    that."""
    payload: dict[str, object] = {
        "sponsorship_agreement_id": str(agreement.agreement_id),
        "review_state": agreement.review_state.value,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="sponsorship.rejected",
        subject_type="sponsorship_agreement",
        subject_id=agreement.agreement_id,
        scope=agreement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_sponsorship_disclosure_classified_event(
    *,
    event_id: UUID,
    agreement: SponsorshipAgreement,
    policy: PolicyBinding,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`sponsorship.disclosure_classified` (canon 19f.9): the disclosure
    classification established.

    The classification and the exact policy version that produced it travel
    together: a disclosure class resolved at read time could be silently
    rewritten by a later policy change, and a missing class is neither
    "publishable" nor "not publishable" but unknown, which fails closed
    (`ФИН-19`, `ФИН-35`). This event classifies; it publishes nothing, and
    carries no sponsor reference or value for a projection to pick up."""
    payload: dict[str, object] = {
        "sponsorship_agreement_id": str(agreement.agreement_id),
        "review_state": agreement.review_state.value,
        "disclosure_class": agreement.disclosure_class,
        "policy": _policy(policy),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="sponsorship.disclosure_classified",
        subject_type="sponsorship_agreement",
        subject_id=agreement.agreement_id,
        scope=agreement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_external_financial_benefit_recorded_event(
    *,
    event_id: UUID,
    benefit: ExternalFinancialBenefit,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`external_financial_benefit.recorded` (canon 19f.9): an external
    financial benefit recorded.

    `subject_kind` travels because it is the boundary marker: the aggregate
    refuses a PACK-35 subject at construction, and a consumer can see from
    the payload that what was recorded is a financially measurable benefit
    and not a meeting, a contact or an access grant (`ФИН-20`). The provider
    appears as the opaque handle reference only. It carries no assessment
    outcome, no disclosure class and no valuation basis - those follow as
    their own recorded acts."""
    payload: dict[str, object] = {
        "external_financial_benefit_id": str(benefit.benefit_id),
        "state": benefit.state.value,
        "benefit_type": benefit.benefit_type.value,
        "subject_kind": benefit.subject_kind,
        "value": _money(benefit.value),
        "in_kind": benefit.in_kind_valuation is not None,
        "provider_handle_reference": benefit.provider_handle_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="external_financial_benefit.recorded",
        subject_type="external_financial_benefit",
        subject_id=benefit.benefit_id,
        scope=benefit.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# Expenses, payments, budgets, assets and obligations (19f.10-19f.12)
# ---------------------------------------------------------------------------
#
# Canon 20.17 names individual `expense_claim.*` and `payment.*` as never
# publicly projected, and permits this group's public presence only at the
# aggregated level of an approved budget version or a published report
# version. `PUBLIC_PROJECTION_ALLOWED` therefore admits `budget.approved`
# and `budget.amended` and nothing else from this group. No payload below
# carries a payee bank detail, a payment identifier or an invoice number:
# an authorisation names a typed payable and an opaque payee handle, and
# execution names the executing authority - never the instrument.


def build_expense_claim_submitted_event(
    *,
    event_id: UUID,
    claim: ExpenseClaim,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`expense_claim.submitted` (canon 19f.10): the claim submitted.

    The claimant appears solely as the opaque purpose-scoped handle
    reference; `purpose_class` is a policy classification and not a
    description of what was bought. It carries **no** evidence reference,
    no receipt content and no vendor or invoice identifier (`ФИН-01`,
    `ФИН-21`)."""
    payload: dict[str, object] = {
        "expense_claim_id": str(claim.claim_id),
        "state": claim.state.value,
        "claimant_handle_reference": claim.claimant_handle_reference,
        "purpose_class": claim.purpose_class,
        "amount": _money(claim.amount),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="expense_claim.submitted",
        subject_type="expense_claim",
        subject_id=claim.claim_id,
        scope=claim.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_expense_claim_reviewed_event(
    *,
    event_id: UUID,
    claim: ExpenseClaim,
    authority: AuthorityReference,
    reason: ReasonCoded,
    conflict: ConflictDeclaration | None,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`expense_claim.reviewed` (canon 19f.10): a review added.

    Reports the reviewer's declared conflict state, because an undeclared
    state fails closed and a consumer must be able to see that the
    declaration existed (`ФИН-32`). It reports the *state* only - never
    `declared_by` or the related-party group reference, both of which point
    back toward a person. It carries no review notes or findings text."""
    payload: dict[str, object] = {
        "expense_claim_id": str(claim.claim_id),
        "state": claim.state.value,
        "conflict_state": None if conflict is None else conflict.state,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="expense_claim.reviewed",
        subject_type="expense_claim",
        subject_id=claim.claim_id,
        scope=claim.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_expense_claim_approved_event(
    *,
    event_id: UUID,
    claim: ExpenseClaim,
    policy: PolicyBinding | None,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`expense_claim.approved` (canon 19f.10): approval.

    Carries the approving authority and the approval-threshold policy
    version the decision was taken under, so a later policy change cannot
    silently rewrite what this approval meant (`ФИН-23`). The approver is
    never the claimant - the aggregate refuses that - and the payload
    carries **no** actor reference through which the two could be compared
    outside this service (`ФИН-31`)."""
    payload: dict[str, object] = {
        "expense_claim_id": str(claim.claim_id),
        "state": claim.state.value,
        "amount": _money(claim.amount),
        "policy": _policy(policy),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="expense_claim.approved",
        subject_type="expense_claim",
        subject_id=claim.claim_id,
        scope=claim.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_expense_claim_rejected_event(
    *,
    event_id: UUID,
    claim: ExpenseClaim,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`expense_claim.rejected` (canon 19f.10): rejection.

    The reason code and the deciding authority only. No amount, no claimant
    reference and no free-text ground: a rejection that travelled with the
    claimant handle would let a consumer build a per-claimant refusal
    history out of the stream."""
    payload: dict[str, object] = {
        "expense_claim_id": str(claim.claim_id),
        "state": claim.state.value,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="expense_claim.rejected",
        subject_type="expense_claim",
        subject_id=claim.claim_id,
        scope=claim.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_expense_claim_corrected_event(
    *,
    event_id: UUID,
    claim: ExpenseClaim,
    correcting_claim_id: UUID,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`expense_claim.corrected` (canon 19f.10): the correction recorded as a
    separate record, never as an in-place edit.

    The subject is the corrected claim; the correcting claim's identity
    travels as `correcting_claim_id`, which is the link canon 19f.10
    requires. It carries **no** before/after amounts: the two claims are
    separate records with their own events, and a diff on the wire would be
    a third representation neither of them owns (`ФИН-05`)."""
    payload: dict[str, object] = {
        "expense_claim_id": str(claim.claim_id),
        "state": claim.state.value,
        "correcting_claim_id": str(correcting_claim_id),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="expense_claim.corrected",
        subject_type="expense_claim",
        subject_id=claim.claim_id,
        scope=claim.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_payment_authorized_event(
    *,
    event_id: UUID,
    authorization: PaymentAuthorization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`payment.authorized` (canon 19f.10): a payment authorised.

    Names the payable through the typed `(payable_kind, payable_reference)`
    pair the aggregate uses, never a free string, and the payee solely as
    the opaque handle reference. It carries **no** bank account, IBAN, card
    number, payment reference or execution instruction: this service
    integrates with no bank and no payment provider, and an authorisation
    is a decision, not an instrument (`ФИН-01`)."""
    payload: dict[str, object] = {
        "payment_authorization_id": str(authorization.authorization_id),
        "state": authorization.state.value,
        "payable_kind": authorization.payable_kind,
        "payable_reference": str(authorization.payable_reference),
        "amount": _money(authorization.amount),
        "authorized_at": _instant(authorization.authorized_at),
        "authorising_authority": _authority_on_the_wire(authorization.authorising_authority),
        "payee_handle_reference": authorization.payee_handle_reference,
        "reason_code": authorization.reason.reason_code,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="payment.authorized",
        subject_type="payment_authorization",
        subject_id=authorization.authorization_id,
        scope=authorization.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_payment_settled_event(
    *,
    event_id: UUID,
    authorization: PaymentAuthorization,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`payment.settled` (canon 19f.10): executed, by an authority that is
    not the authorising one.

    Both authority references travel, because the separation of the two acts
    is the fact this event records and a payload naming only the executor
    would leave it unverifiable from the stream (`ФИН-31`). Neither actor
    reference travels. It carries **no** payment identifier, settlement
    reference or bank confirmation - execution happened outside this system
    and this event records only that it was recorded here."""
    payload: dict[str, object] = {
        "payment_authorization_id": str(authorization.authorization_id),
        "state": authorization.state.value,
        "amount": _money(authorization.amount),
        "executed_at": _instant(authorization.executed_at),
        "authorising_authority": _authority_on_the_wire(authorization.authorising_authority),
        "executing_authority": _authority_on_the_wire(authorization.executed_by),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="payment.settled",
        subject_type="payment_authorization",
        subject_id=authorization.authorization_id,
        scope=authorization.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_budget_approved_event(
    *,
    event_id: UUID,
    budget_id: UUID,
    scope: OrganizationalScopeRef,
    budget_version: int,
    period: ReportingPeriodRef,
    approved_total: Money | None,
    policy: PolicyBinding | None,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`budget.approved` (canon 19f.12): a budget version approved.

    Typed arguments rather than an aggregate: PACK-10's pure modules do not
    model `Budget`, so this builder names the facts canon 19f.12 fixes. The
    approved total is the aggregated figure the permitted public projection
    of this group rests on. It carries **no** budget lines and no actual
    amounts at all: an actual on a budget line is not stored anywhere - it
    is a derived read model over posted register entries - and putting one
    on this event would make the budget an alternative source of truth about
    real transactions, which canon 19f.12 forbids outright (`ФИН-12`)."""
    payload: dict[str, object] = {
        "budget_id": str(budget_id),
        "budget_version": budget_version,
        "state": "approved",
        "reporting_period_id": str(period.period_id),
        "approved_total": _money(approved_total),
        "policy": _policy(policy),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="budget.approved",
        subject_type="budget",
        subject_id=budget_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_budget_amended_event(
    *,
    event_id: UUID,
    budget_id: UUID,
    scope: OrganizationalScopeRef,
    budget_version: int,
    supersedes_budget_version: int,
    period: ReportingPeriodRef,
    approved_total: Money | None,
    policy: PolicyBinding | None,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`budget.amended` (canon 19f.12): a new version supersedes the previous
    one.

    Both version numbers travel, because an amendment is a *new version* and
    never an edit of the approved one, and the superseded version stays
    readable (`ФИН-05`). As with `budget.approved`, no budget line and no
    actual amount appears (`ФИН-12`)."""
    payload: dict[str, object] = {
        "budget_id": str(budget_id),
        "budget_version": budget_version,
        "supersedes_budget_version": supersedes_budget_version,
        "state": "approved",
        "reporting_period_id": str(period.period_id),
        "approved_total": _money(approved_total),
        "policy": _policy(policy),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="budget.amended",
        subject_type="budget",
        subject_id=budget_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_asset_recorded_event(
    *,
    event_id: UUID,
    asset: FinancialAsset,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_asset.recorded` (canon 19f.11): an asset position recorded.

    The valuation travels with its date and its method reference, since an
    amount without those two is an opinion (`ФИН-18`). It carries **no**
    evidence content, no location or serial number, and no maintenance,
    inventory or depreciation data - PACK-10 builds no asset-management
    system and claims none."""
    payload: dict[str, object] = {
        "financial_asset_id": str(asset.asset_id),
        "state": asset.state.value,
        "asset_class": asset.asset_class,
        "asset_reference": asset.asset_reference,
        "valuation": _money(asset.valuation),
        "valuation_date": _day(asset.valuation_date),
        "method_reference": asset.method_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_asset.recorded",
        subject_type="financial_asset",
        subject_id=asset.asset_id,
        scope=asset.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_asset_revalued_event(
    *,
    event_id: UUID,
    asset: FinancialAsset,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_asset.revalued` (canon 19f.11): revaluation, with a
    reference to the method.

    The new carrying value, its date and the method reference travel
    together: an unexplained change of carrying value is indistinguishable
    from an unrecorded write-off, which is why the method is mandatory here
    and in the aggregate. It carries **no** previous value - the earlier
    `financial_asset.recorded` or `.revalued` event already stated it, and
    restating it would create a second, divergeable history."""
    payload: dict[str, object] = {
        "financial_asset_id": str(asset.asset_id),
        "state": asset.state.value,
        "valuation": _money(asset.valuation),
        "valuation_date": _day(asset.valuation_date),
        "method_reference": asset.method_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_asset.revalued",
        subject_type="financial_asset",
        subject_id=asset.asset_id,
        scope=asset.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_asset_written_off_event(
    *,
    event_id: UUID,
    asset: FinancialAsset,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_asset.written_off` (canon 19f.11): a write-off with
    authority and grounds.

    A write-off removes value from the books, so the authority and exactly
    one reason code are both mandatory and both travel; where a PACK-09 case
    still concerns the asset, its opaque reference travels too, so a
    write-off can never quietly close something a case is still about
    (`ФИН-22`). It carries no case content and asserts nothing about
    retention or legal hold, which stay PACK-09's decisions."""
    payload: dict[str, object] = {
        "financial_asset_id": str(asset.asset_id),
        "state": asset.state.value,
        "legal_case_reference": asset.legal_case_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_asset.written_off",
        subject_type="financial_asset",
        subject_id=asset.asset_id,
        scope=asset.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_obligation_recorded_event(
    *,
    event_id: UUID,
    obligation: FinancialObligation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_obligation.recorded` (canon 19f.11): an obligation position
    recorded.

    Every liability shape - receivable, payable, loan, credit, guarantee,
    contingent, long-term - travels as `obligation_type` on this one event,
    because they share one lifecycle and one valuation model. The
    counterparty appears solely as the opaque handle reference. It carries
    **no** contract text, no bank detail and no schedule of instalments."""
    payload: dict[str, object] = {
        "financial_obligation_id": str(obligation.obligation_id),
        "state": obligation.state.value,
        "obligation_type": obligation.obligation_type.value,
        "amount": _money(obligation.amount),
        "valuation_date": _day(obligation.valuation_date),
        "method_reference": obligation.method_reference,
        "counterparty_handle_reference": obligation.counterparty_handle_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_obligation.recorded",
        subject_type="financial_obligation",
        subject_id=obligation.obligation_id,
        scope=obligation.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_obligation_revalued_event(
    *,
    event_id: UUID,
    obligation: FinancialObligation,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_obligation.revalued` (canon 19f.11): revaluation, with a
    reference to the method.

    Same rule as the asset revaluation: value, date and method reference
    move together or not at all. No previous value and no counterparty
    reference travel."""
    payload: dict[str, object] = {
        "financial_obligation_id": str(obligation.obligation_id),
        "state": obligation.state.value,
        "amount": _money(obligation.amount),
        "valuation_date": _day(obligation.valuation_date),
        "method_reference": obligation.method_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_obligation.revalued",
        subject_type="financial_obligation",
        subject_id=obligation.obligation_id,
        scope=obligation.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_obligation_settled_event(
    *,
    event_id: UUID,
    obligation: FinancialObligation,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_obligation.settled` (canon 19f.11): the obligation settled.

    Names the `PaymentAuthorization` that permitted the payment, which the
    aggregate requires to reference *this* obligation: settling without one,
    or against someone else's, is the failure canon 19f.11 names
    (`ФИН-31`). It carries **no** payment identifier or bank confirmation."""
    payload: dict[str, object] = {
        "financial_obligation_id": str(obligation.obligation_id),
        "state": obligation.state.value,
        "settlement_authorization_id": _identifier(obligation.settlement_authorization_id),
        "amount": _money(obligation.amount),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_obligation.settled",
        subject_type="financial_obligation",
        subject_id=obligation.obligation_id,
        scope=obligation.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_financial_obligation_written_off_event(
    *,
    event_id: UUID,
    obligation: FinancialObligation,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`financial_obligation.written_off` (canon 19f.11): a write-off with
    authority and grounds.

    As for the asset write-off, the authority and exactly one reason code
    are mandatory, and a contingent liability an open PACK-09 case still
    concerns must cite that case, which travels as an opaque reference
    (`ФИН-22`). No case content travels."""
    payload: dict[str, object] = {
        "financial_obligation_id": str(obligation.obligation_id),
        "state": obligation.state.value,
        "obligation_type": obligation.obligation_type.value,
        "legal_case_reference": obligation.legal_case_reference,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="financial_obligation.written_off",
        subject_type="financial_obligation",
        subject_id=obligation.obligation_id,
        scope=obligation.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# Reporting obligation and the report lifecycle (19f.16, 19f.17)
# ---------------------------------------------------------------------------
#
# Canon 20.17 projects only the version in status `published`, and names
# `finance_report.snapshot_frozen`,
# `finance_report.validation_finding_recorded` and
# `finance_report.correction_requested` as never projected. No payload here
# carries report figures: a report version's numbers live in the frozen
# snapshot it was computed from and reach the public only through the
# published rendition, never through this stream.


def build_reporting_obligation_created_event(
    *,
    event_id: UUID,
    obligation: ReportingObligation,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`reporting_obligation.created` (canon 19f.16): a reporting duty
    recorded.

    `statutory_deadline_reference` is a PACK-09 `DeadlineRef` carried as an
    **opaque** string: this service neither computes nor interprets the
    deadline, and asserting a date here would be an assertion PACK-09 owns
    (`ФИН-44`). It carries no report structure, no figures and no
    fulfilment claim - fulfilment happens only through a recorded
    submission."""
    payload: dict[str, object] = {
        "reporting_obligation_id": str(obligation.obligation_id),
        "state": obligation.state.value,
        "obligation_kind": obligation.obligation_kind.value,
        "reporting_period_id": str(obligation.period.period_id),
        "statutory_deadline_reference": obligation.statutory_deadline_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="reporting_obligation.created",
        subject_type="reporting_obligation",
        subject_id=obligation.obligation_id,
        scope=obligation.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_reporting_perimeter_defined_event(
    *,
    event_id: UUID,
    definition: ReportingPerimeterDefinition,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`reporting_perimeter.defined` (canon 19f.16): a version of the
    reporting perimeter activated.

    The included organizational scopes travel, because they are exactly the
    safe metadata canon 20.17 names and because the perimeter is
    authoritative rather than derived: canon 19f.16 forbids reading it off
    the hierarchy as it stands at report time, which would make a report's
    meaning depend on a later reorganisation (`ФИН-25`). It carries no
    hierarchy, no access mode and no inheritance rule - those stay with
    `organization-service` (canon 19f.19)."""
    payload: dict[str, object] = {
        "perimeter_definition_id": str(definition.definition_id),
        "definition_version": definition.version,
        "state": definition.state.value,
        "effective_from": _day(definition.effective_from),
        "effective_until": _day(definition.effective_until),
        "included_organization_scopes": [
            str(scope.organization_id) for scope in definition.included_scopes
        ],
    }
    return build_finance_event(
        event_id=event_id,
        event_type="reporting_perimeter.defined",
        subject_type="reporting_perimeter_definition",
        subject_id=definition.definition_id,
        scope=definition.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_snapshot_frozen_event(
    *,
    event_id: UUID,
    snapshot: ReportSnapshot,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.snapshot_frozen` (canon 19f.16): the source snapshot
    frozen.

    Carries the content digest, the frozen perimeter's digest and identity,
    and **counts** of the included transactions and entries. It deliberately
    does not carry the identifier lists themselves: shipping every
    transaction and entry id of a reporting period would put a bulk index of
    the register into an event stream five other packs read, and the digest
    is what makes the snapshot's contents provable without disclosing them
    (`ФИН-03`, `ФИН-24`). Canon 20.17 names this event as never publicly
    projected."""
    payload: dict[str, object] = {
        "report_snapshot_id": str(snapshot.snapshot_id),
        "reporting_period_id": str(snapshot.period.period_id),
        "content_digest": snapshot.content_digest,
        "frozen_at": _instant(snapshot.frozen_at),
        "perimeter_definition_id": str(snapshot.perimeter.definition_id),
        "perimeter_definition_version": snapshot.perimeter.definition_version,
        "perimeter_digest": snapshot.perimeter.digest,
        "included_transaction_count": len(snapshot.included_transaction_ids),
        "included_entry_count": len(snapshot.included_entry_ids),
        "policy_binding_count": len(snapshot.policy_bindings),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.snapshot_frozen",
        subject_type="report_snapshot",
        subject_id=snapshot.snapshot_id,
        scope=snapshot.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_prepared_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.prepared` (canon 19f.17): a version prepared from a
    frozen snapshot.

    The snapshot binding is the point of the event: a version names exactly
    one snapshot for life and never rebinds it, and every later state
    requires that binding (`ФИН-24`). Preparation is not a state transition
    in canon 19f.17, so the payload reports the version's unchanged state
    rather than inventing a `prepared` status the canon does not define. It
    carries **no** report figures."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "report_id": str(version.report_id),
        "version": version.version,
        "state": version.state.value,
        "report_snapshot_id": _identifier(version.snapshot_id),
        "reporting_period_id": str(version.period.period_id),
        "preparing_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.prepared",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_validation_finding_recorded_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    review: ReviewRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.validation_finding_recorded` (canon 19f.17): a
    validation finding recorded.

    Carries the review's outcome and its **opaque** finding references, and
    no finding content: finance records that findings exist and stays out of
    what they say. `findings_open` is neither a failure nor a completion, and
    the payload reports the outcome verbatim rather than reducing it to a
    pass/fail flag (`ФИН-33`). Canon 20.17 names this event as never
    publicly projected."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "review_id": str(review.review_id),
        "outcome": review.outcome.value,
        "finding_references": list(review.finding_references),
        "reviewing_authority": _authority_on_the_wire(review.reviewer),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.validation_finding_recorded",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_consolidated_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    consolidated_scopes: tuple[OrganizationalScopeRef, ...],
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.consolidated` (canon 19f.17): a consolidation
    recorded.

    Carries the scopes consolidated, which are safe metadata, and the
    consolidating authority, which canon 19f.19 requires to be explicit.
    Consolidation is a **read**: no higher scope writes into a lower one,
    and this event asserts no write into any of the scopes it names
    (`ФИН-37`). It carries no consolidated figures and no elimination
    detail."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "version": version.version,
        "consolidated_organization_scopes": [
            str(scope.organization_id) for scope in consolidated_scopes
        ],
        "consolidating_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.consolidated",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_internally_reviewed_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.internally_reviewed` (canon 19f.17): internal review
    closed.

    Reports how many recorded reviews completed, which is the fact the
    transition rests on - closing review on top of open findings would make
    the review decorative (`ФИН-33`). It carries **no** finding references or
    content; those belong to `finance_report.validation_finding_recorded`,
    which is separately non-projectable."""
    completed = sum(1 for review in version.review_records if review.is_complete)
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "completed_review_count": completed,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.internally_reviewed",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_auditor_reviewed_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    reference: AuditOpinionReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.auditor_reviewed` (canon 19f.17): auditor review,
    which requires a concluded engagement for the same scope and period.

    Carries the engagement identity and the **conclusion reference**, never
    the conclusion itself: the conclusion lives on the `AuditEngagement`,
    which the report may not write into, and its canonical name is
    `AuditConclusion` and never "opinion" - nothing here may be read as the
    opinion of a statutory audit. No finding content travels."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "audit_engagement_id": str(reference.engagement_id),
        "conclusion_reference": reference.conclusion_reference,
        "auditor_authority": _authority_on_the_wire(reference.auditor),
        "recorded_at": _instant(reference.recorded_at),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.auditor_reviewed",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_correction_requested_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    request: CorrectionRequest,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.correction_requested` (canon 19f.17): a correction
    request recorded.

    The payload reports the version's **unchanged** state: canon 19f.17
    defines twelve statuses and no `correction_required` among them, so a
    request is a fact recorded against the version and never a status of it.
    Finding references travel opaquely; no requested-change text travels.
    Canon 20.17 names this event as never publicly projected."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "correction_request_id": str(request.request_id),
        "requested_at": _instant(request.requested_at),
        "requesting_authority": _authority_on_the_wire(request.requested_by),
        "reason_code": request.reason.reason_code,
        "finding_references": list(request.finding_references),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.correction_requested",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_approved_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    approval: ApprovalRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.approved` (canon 19f.17): approval by the body policy
    names.

    Carries the approving authority and the policy version the approval rule
    came from (`ФИН-23`). Approval is not publication and implies none: no
    publication authorisation is asserted here, and canon 19f.17 states in
    both directions that neither implies the other (`ФИН-28`, `ФИН-34`). It
    carries no figures."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "approval_id": str(approval.approval_id),
        "approved_at": _instant(approval.approved_at),
        "approving_authority": _authority_on_the_wire(approval.approved_by),
        "reason_code": approval.reason.reason_code,
        "policy": _policy(approval.policy),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.approved",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_signed_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    signature: SignatureRecord,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.signed` (canon 19f.17): the signature of the legally
    responsible signatory.

    A record *that* a named authority signed, and never a signature value:
    PACK-10 implements no signing primitive and claims none, so no key, no
    certificate and no digest of a signed document travels. The signatory is
    a `report_signatory` authority reference, never a person, and never the
    same actor as the approver (`ФИН-31`, `ФИН-33`)."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "signature_id": str(signature.signature_id),
        "signed_at": _instant(signature.signed_at),
        "signing_authority": _authority_on_the_wire(signature.signed_by),
        "reason_code": signature.reason.reason_code,
        "policy": _policy(signature.policy),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.signed",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_submitted_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    reference: ExternalSubmissionReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.submitted` (canon 19f.17): the submission recorded.

    One fact, from which nothing follows: not acknowledgement, not
    acceptance, not fulfilment of the reporting obligation - that last is
    recorded on the obligation itself (`ФИН-26`). Both references are opaque
    strings pointing at an act performed outside this system, which
    integrates with no authority's submission portal. No document bytes and
    no rendition travel (`ФИН-21`)."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "submission_reference": reference.submission_reference,
        "recipient_reference": reference.recipient_reference,
        "submitted_at": _instant(reference.submitted_at),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.submitted",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_external_acknowledgement_recorded_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    reference: ExternalAcceptanceReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.external_acknowledgement_recorded` (canon 19f.17): a
    recorded acknowledgement, which is **not** a sign of acceptance.

    `external_status_kind` travels so a consumer can see which of the four
    telemetry kinds was stored, and `implies_acceptance` is stated as a
    literal `False` rather than left to be inferred: canon 19f.17 is
    explicit that acknowledgement does not imply legal acceptance, and a
    consumer that read a stored delivery receipt as a decision would be the
    exact failure `ФИН-26` and `ФИН-27` exist to prevent. No acceptance
    authority reference travels, because none exists on this fact."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "notice_effect_reference": reference.notice_effect_reference,
        "external_status_kind": reference.kind.value,
        "recorded_at": _instant(reference.decided_at),
        "implies_acceptance": False,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.external_acknowledgement_recorded",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_acceptance_recorded_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    reference: ExternalAcceptanceReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.acceptance_recorded` (canon 19f.17): recorded only
    with an authoritative reference from the competent body.

    `external_status_kind` travels here too, and it is the field that makes
    the event checkable: only
    `authoritative_acceptance_decision` may drive this transition, and an
    acknowledgement, receipt, delivery record or read status offered instead
    is refused by the aggregate rather than silently promoted. Acceptance is
    never inferred from elapsed time, silence, delivery or publication
    (`ФИН-26`, `ФИН-27`)."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "notice_effect_reference": reference.notice_effect_reference,
        "external_status_kind": reference.kind.value,
        "decided_at": _instant(reference.decided_at),
        "deciding_authority_reference": reference.deciding_authority_reference,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.acceptance_recorded",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_published_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    reference: PublicationReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.published` (canon 19f.17): publication of a version in
    status `published`.

    Names the separate publication authorisation the publication ran under,
    because approval is not publication and publication is not approval
    (`ФИН-28`, `ФИН-34`). The only event of the report lifecycle canon 20.17
    permits in a public projection - and even then as a derived, versioned,
    non-authoritative representation under the disclosure policy and the
    statistical disclosure-control rules (19f.21), never as the
    authoritative source. It carries the publication reference, not the
    published rendition: the document belongs to PACK-11 (`ФИН-21`)."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "report_id": str(version.report_id),
        "version": version.version,
        "state": version.state.value,
        "reporting_period_id": str(version.period.period_id),
        "publication_reference": reference.publication_reference,
        "publication_authorization_id": str(reference.authorization_id),
        "published_at": _instant(reference.published_at),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.published",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_restated_event(
    *,
    event_id: UUID,
    successor: FinanceReportVersion,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.restated` (canon 19f.17): a restatement version
    created.

    The subject is the **successor**, which is the version that came into
    existence; the typed backward link to the version it restates travels as
    `restates_report_version_id`. A restatement is one of the canon's two
    correction routes and never an overwrite - the predecessor becomes
    `superseded` and stays readable forever (`ФИН-05`, `ФИН-25`). The
    successor carries no snapshot yet: changed figures need their own, so no
    snapshot identifier and no figures travel."""
    payload: dict[str, object] = {
        "report_version_id": str(successor.version_id),
        "report_id": str(successor.report_id),
        "version": successor.version,
        "state": successor.state.value,
        "restates_report_version_id": _identifier(successor.restatement_of_version_reference),
        "correction_kind": (
            None if successor.correction_kind is None else successor.correction_kind.value
        ),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.restated",
        subject_type="finance_report_version",
        subject_id=successor.version_id,
        scope=successor.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_amended_event(
    *,
    event_id: UUID,
    successor: FinanceReportVersion,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.amended` (canon 19f.17): an amendment version created.

    The second of the canon's two correction routes, kept a separate event
    from `finance_report.restated` because the two are distinct legal acts
    and a single "corrected" event would erase which one happened. Same
    shape as the restatement: the successor is the subject, the backward
    link travels, the predecessor is superseded and remains readable, and no
    figures travel."""
    payload: dict[str, object] = {
        "report_version_id": str(successor.version_id),
        "report_id": str(successor.report_id),
        "version": successor.version,
        "state": successor.state.value,
        "amends_report_version_id": _identifier(successor.restatement_of_version_reference),
        "correction_kind": (
            None if successor.correction_kind is None else successor.correction_kind.value
        ),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.amended",
        subject_type="finance_report_version",
        subject_id=successor.version_id,
        scope=successor.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_report_superseded_event(
    *,
    event_id: UUID,
    version: FinanceReportVersion,
    superseded_by_version_id: UUID,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.superseded` (canon 19f.17): a version displaced by a
    later one.

    The subject is the displaced version and the successor's identity
    travels alongside. Supersession is not deletion: a submitted or
    published version that later turned out wrong is part of the record of
    what was reported, stays readable forever, and this event says only that
    a later version now stands in front of it (`ФИН-05`)."""
    payload: dict[str, object] = {
        "report_version_id": str(version.version_id),
        "state": version.state.value,
        "superseded_by_report_version_id": str(superseded_by_version_id),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_report.superseded",
        subject_type="finance_report_version",
        subject_id=version.version_id,
        scope=version.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# Independent audit and finance policy (19f.18, 19f.20)
# ---------------------------------------------------------------------------
#
# Canon 20.17 permits a public projection of the *fact* of an audit and the
# `AuditConclusion` class, plus the identifier and version of the policy in
# force; the content of findings is never projected.
# `finance_audit.finding_recorded` is therefore absent from
# `PUBLIC_PROJECTION_ALLOWED` while the other two audit events are in it.


def build_finance_audit_opened_event(
    *,
    event_id: UUID,
    engagement: AuditEngagement,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_audit.opened` (canon 19f.18): an engagement opened, with the
    result of the independence check included.

    `independence_verified` is a recorded outcome, not a claim computed
    here: `AuditEngagement.open` runs `assert_auditor_independent` before it
    returns, so an engagement that failed the check does not exist to be
    described. Canon 19f.18 requires the check again at every finding and at
    conclusion, because a role granted mid-engagement would otherwise never
    surface (`ФИН-29`, `ФИН-30`). The auditor travels as an authority
    reference; the operational actor set the check ran against does **not**,
    since it is a set of actor references."""
    payload: dict[str, object] = {
        "audit_engagement_id": str(engagement.engagement_id),
        "state": engagement.state.value,
        "reporting_period_id": str(engagement.period.period_id),
        "auditor_authority": _authority_on_the_wire(engagement.auditor),
        "independence_verified": True,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_audit.opened",
        subject_type="audit_engagement",
        subject_id=engagement.engagement_id,
        scope=engagement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_audit_finding_recorded_event(
    *,
    event_id: UUID,
    engagement: AuditEngagement,
    finding: AuditFinding,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_audit.finding_recorded` (canon 19f.18): an audit finding
    added.

    Carries the severity and an **opaque** summary reference, never the
    finding's prose: canon 20.17 places the content of findings outside any
    public projection, and a payload carrying it would put that content into
    a stream from which a projection could later be derived (`ФИН-35`). No
    evidence content travels either. A finding is append-only and survives
    every later engagement; a correction is a further finding, not an edit
    of this one."""
    payload: dict[str, object] = {
        "audit_engagement_id": str(engagement.engagement_id),
        "state": engagement.state.value,
        "audit_finding_id": str(finding.finding_id),
        "severity": finding.severity,
        "summary_reference": finding.summary_reference,
        "recorded_at": _instant(finding.recorded_at),
        "recording_authority": _authority_on_the_wire(finding.recorded_by),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_audit.finding_recorded",
        subject_type="audit_engagement",
        subject_id=engagement.engagement_id,
        scope=engagement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_audit_concluded_event(
    *,
    event_id: UUID,
    engagement: AuditEngagement,
    conclusion: AuditConclusion,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_audit.concluded` (canon 19f.18): the `AuditConclusion` class
    fixed.

    Carries the conclusion **class** and the recorded finding count, which
    is the extent canon 20.17 permits a public projection to reach. The
    canonical name is `AuditConclusion` and never "opinion": nothing in this
    payload may be read as the opinion of a statutory audit. No finding
    content and no working-paper reference travels. A conclusion is
    create-once - a changed conclusion is a new engagement (`ФИН-05`)."""
    payload: dict[str, object] = {
        "audit_engagement_id": str(engagement.engagement_id),
        "state": engagement.state.value,
        "audit_conclusion_id": str(conclusion.conclusion_id),
        "conclusion_class": conclusion.conclusion_class,
        "concluded_at": _instant(conclusion.concluded_at),
        "concluding_authority": _authority_on_the_wire(conclusion.concluded_by),
        "reason_code": conclusion.reason.reason_code,
        "finding_count": len(engagement.findings),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_audit.concluded",
        subject_type="audit_engagement",
        subject_id=engagement.engagement_id,
        scope=engagement.scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_policy_version_published_event(
    *,
    event_id: UUID,
    finance_policy_id: UUID,
    scope: OrganizationalScopeRef,
    policy: PolicyBinding,
    jurisdiction_reference: str,
    prepared_by: AuthorityReference,
    approved_by: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_policy.version_published` (canon 19f.20): a policy version
    became effective.

    Takes typed arguments because PACK-10's pure modules model the
    *binding*, not the `FinancePolicy` aggregate: `PolicyBinding` carries
    exactly the identifier, version and effective date this event must
    state. The jurisdiction reference travels because a policy is never
    implicitly global, and both the preparing and the approving authority
    travel because the critical policy kinds require dual approval with an
    approver distinct from the preparer.

    It carries **no** threshold value, category list or chart of accounts.
    That is deliberate and it is the whole point of 19f.20: German statutory
    thresholds are inputs to a governed, effective-dated policy and are
    never constants of canon or code, and an event stream carrying them
    would become a second, unversioned copy of the policy."""
    payload: dict[str, object] = {
        "finance_policy_id": str(finance_policy_id),
        "state": "active",
        "policy": _policy(policy),
        "jurisdiction_reference": jurisdiction_reference,
        "preparing_authority": _authority_on_the_wire(prepared_by),
        "approving_authority": _authority_on_the_wire(approved_by),
        "reason_code": reason.reason_code,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_policy.version_published",
        subject_type="finance_policy",
        subject_id=finance_policy_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_policy_superseded_event(
    *,
    event_id: UUID,
    finance_policy_id: UUID,
    scope: OrganizationalScopeRef,
    policy: PolicyBinding,
    superseded_by_policy_version: str,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_policy.superseded` (canon 19f.20): a version displaced by a
    later one.

    Both version strings travel: supersession requires a version increment,
    and the superseded version stays readable forever because a past
    decision is interpretable only against the rules that produced it. It
    carries **no** threshold or category content, for the same reason
    `finance_policy.version_published` does not, and it asserts nothing
    about decisions already bound to the superseded version - a later policy
    change never rewrites a past decision (`ФИН-23`)."""
    payload: dict[str, object] = {
        "finance_policy_id": str(finance_policy_id),
        "state": "superseded",
        "policy": _policy(policy),
        "superseded_by_policy_version": superseded_by_policy_version,
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_policy.superseded",
        subject_type="finance_policy",
        subject_id=finance_policy_id,
        scope=scope,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# The purpose-scoped party reference (19f.15)
# ---------------------------------------------------------------------------
#
# Canon 20.17 forbids a public projection of these three events never, in
# no extent and in no derived form, and `PUBLIC_PROJECTION_ALLOWED`
# excludes all three.
#
# Each payload carries the opaque handle reference, its declared purpose and
# its perimeter, and nothing else. There is no identifying attribute in any
# of them, and none can be derived from one: the handle id is minted by the
# service and computed from no name, account, membership, credential,
# participation or voting value (`ФИН-01`). Pseudonymisation is not
# anonymity - a handle is personal data, re-identifiable by an authorised
# resolver through the party registry - which is why these three events stay
# out of every projection rather than being treated as safe because they
# look opaque.


def build_finance_party_handle_minted_event(
    *,
    event_id: UUID,
    handle: FinancePartyHandle,
    authority: AuthorityReference,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_party_handle.minted` (canon 19f.15): a handle minted,
    **without identifying attributes**.

    Carries only the opaque reference, the one declared purpose the handle
    is valid for, its perimeter and the party-handle policy version. It
    carries no name, address, date of birth, national or tax identifier,
    bank detail, identity-document reference, email, phone, credential
    value, membership or participation identifier and no voting-related
    value - the whole list canon 19f.15 says this context never stores."""
    payload: dict[str, object] = {
        "party_handle_reference": handle.as_reference(),
        "purpose": handle.purpose.value,
        "perimeter": _scope(handle.perimeter),
        "policy_version": handle.policy_version,
        "minting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_party_handle.minted",
        subject_type="finance_party_handle",
        subject_id=handle.handle_id,
        scope=handle.perimeter,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_party_handle_merged_event(
    *,
    event_id: UUID,
    handle: FinancePartyHandle,
    merged_handle: FinancePartyHandle,
    authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_party_handle.merged` (canon 19f.15): two references
    recognised as one party.

    Carries both opaque references, the shared purpose and perimeter, the
    reason code and the authority - and nothing about *why* the two are the
    same party, which would be the identifying attribute the merge was
    performed on. The subject is the surviving handle. A merge never
    rewrites a historical finance record: earlier records keep the reference
    they were written with, and this event is the governed, reason-coded,
    auditable matching act that contribution aggregation relies on
    (`ФИН-36`)."""
    payload: dict[str, object] = {
        "party_handle_reference": handle.as_reference(),
        "merged_party_handle_reference": merged_handle.as_reference(),
        "purpose": handle.purpose.value,
        "perimeter": _scope(handle.perimeter),
        "reason_code": reason.reason_code,
        "acting_authority": _authority_on_the_wire(authority),
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_party_handle.merged",
        subject_type="finance_party_handle",
        subject_id=handle.handle_id,
        scope=handle.perimeter,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )


def build_finance_party_handle_resolved_event(
    *,
    event_id: UUID,
    handle: FinancePartyHandle,
    resolving_authority: AuthorityReference,
    reason: ReasonCoded,
    actor: ActorRef,
    correlation_id: UUID,
    causation_id: UUID | None,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_party_handle.resolved` (canon 19f.15): the access audit of a
    resolution - **the resolved value itself is not part of the payload**.

    Canon 20.17 states that prohibition explicitly and adds it to the
    forbidden-payload list for this one event, and canon 19f.15 restates it:
    a resolution event records who resolved what, under which authority and
    for what purpose, *without the value*. This builder therefore takes no
    parameter that could carry a resolved identity - there is no argument
    for a name, a party record or a registry row, so a caller cannot supply
    one by mistake. Resolution itself requires a separately granted
    authority available only to the party-registry module, and this event is
    the audit trail of that access, never its result."""
    payload: dict[str, object] = {
        "party_handle_reference": handle.as_reference(),
        "purpose": handle.purpose.value,
        "perimeter": _scope(handle.perimeter),
        "reason_code": reason.reason_code,
        "resolving_authority": _authority_on_the_wire(resolving_authority),
        "resolved_value_disclosed": False,
    }
    return build_finance_event(
        event_id=event_id,
        event_type="finance_party_handle.resolved",
        subject_type="finance_party_handle",
        subject_id=handle.handle_id,
        scope=handle.perimeter,
        payload=payload,
        actor=actor,
        correlation_id=correlation_id,
        causation_id=causation_id,
        occurred_at=occurred_at,
    )

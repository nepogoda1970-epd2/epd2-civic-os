"""Finance Service governed records - contributions, sponsorship,
external financial benefit, expenses, payments, obligations, assets and
governed transfers (PACK-10 sections 4.4-4.7 and 8.2.7-8.2.14; canon
0.8.0 sections 19f.7-19f.11).

Pure, like `ledger`: no I/O, no clock, no storage, no cross-service
imports. Identifiers and timestamps are always passed in.

Every aggregate here is a frozen, slotted dataclass with an append-only
`history` tuple. Nothing is rewritten: each state change returns a NEW
instance and appends one `RecordHistoryEntry` carrying the acting
`AuthorityReference` and a `ReasonCoded`, so what a past decision was,
who took it and under which code stays answerable (`ФИН-05`, `ФИН-40`).
Those values always travel together, which is why they are one
`GovernedAct` value object rather than four parameters a future
transition could forget one of.

Three rules run through the whole module:

- **The unknown fails closed.** An undetermined source, an incomplete
  verification, an unresolved classification or an undeclared conflict
  never resolves into "accepted"; it resolves into a governed
  exceptional state or a refusal (`ФИН-16`, `ФИН-32`, `ФИН-41`).
- **A create-once record is never edited.** A contribution receipt, a
  payment authorization and a reimbursement are written once. Rejection,
  return and escalation append decisions around the receipt and leave it
  exactly as received (`ФИН-18`, canon 19f.7).
- **Requesting, approving, authorising and executing are different
  acts.** A claimant may not review, approve, authorise or execute their
  own claim, and an authoriser may not execute their own authorization
  (`ФИН-31`, canon 19f.10).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    EvidenceReference,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    ReasonCoded,
    RetentionBinding,
    require_timezone,
)
from epd2_finance_service.exceptions import (
    ConflictOfInterestBlockingError,
    ConflictOfInterestUndeclaredError,
    ContributionClassificationUndeterminedError,
    ContributionProhibitedError,
    ContributionReturnRequiredError,
    ContributionSourceUndeterminedError,
    ContributionVerificationIncompleteError,
    CounterPerformanceMissingError,
    EvidenceReferenceMissingError,
    ForbiddenIdentityLinkageError,
    ImmutableRecordModificationAttemptedError,
    InKindValuationMissingError,
    MonetaryAmountInvalidError,
    PaymentAuthorizationMissingError,
    SelfApprovalProhibitedError,
    SponsorshipDisclosureIncompleteError,
    TransferPairUnresolvedError,
    UnauthorizedStateTransitionError,
    ValuationMethodMissingError,
    WriteOffNotAuthorizedError,
)

# ---------------------------------------------------------------------------
# Shared structural helpers
# ---------------------------------------------------------------------------

#: The only shape a party may take in a finance record: the opaque string
#: `FinancePartyHandle.as_reference()` produces (canon 19f.15, `ФИН-01`).
PARTY_HANDLE_REFERENCE_PREFIX = "fph:"


def _require_text(value: str, field_name: str) -> None:
    """Structural non-emptiness check, raising the code `domain.py`
    already uses for field validation rather than a bare `ValueError`
    (`ФИН-40`)."""
    if not value or not value.strip():
        raise MonetaryAmountInvalidError(f"{field_name} must be a non-empty string")


def _require_party_handle_reference(value: str, field_name: str) -> None:
    """Refuse anything that is not an opaque party-handle reference, so a
    name, an IBAN or a user id cannot be smuggled into a party field
    (`ФИН-01`, `ФИН-02`)."""
    if not value.startswith(PARTY_HANDLE_REFERENCE_PREFIX):
        raise ForbiddenIdentityLinkageError(
            f"{field_name} must be an opaque party-handle reference, not a direct identity"
        )


@dataclass(frozen=True, slots=True)
class GovernedAct:
    """Who acted, when, under which reason code and against which policy
    version.

    One value object rather than four parameters: these travel together
    on every governed transition here, and a transition that could omit
    one of them would be a transition whose history entry is incomplete
    (`ФИН-40`, `ФИН-45`). `conflict` is carried by acts that require a
    declaration; `None` is "undeclared" and fails closed (`ФИН-32`)."""

    at: datetime
    by_authority: AuthorityReference
    reason: ReasonCoded
    policy: PolicyBinding | None = None
    conflict: ConflictDeclaration | None = None

    def __post_init__(self) -> None:
        require_timezone(self.at, context="GovernedAct.at")


def assert_conflict_resolved(conflict: ConflictDeclaration | None, *, action: str) -> None:
    """Raise unless the deciding authority's conflict state permits
    `action`.

    `None` and `undeclared` are the same answer - unknown - and both fail
    closed rather than being read as "no conflict"; a declared blocking
    conflict refuses outright (`ФИН-32`, canon 19f.7/19f.10)."""
    if conflict is None or conflict.is_undeclared:
        raise ConflictOfInterestUndeclaredError(
            f"{action} requires a declared conflict-of-interest state - undeclared fails closed"
        )
    if conflict.is_blocking:
        raise ConflictOfInterestBlockingError(f"a declared blocking conflict refuses {action}")


@dataclass(frozen=True, slots=True)
class RecordHistoryEntry:
    """One append-only entry in a governed record's decision history.

    Entries are appended and never rewritten, so a reversal of opinion is
    visible as a later entry rather than as an edited earlier one
    (`ФИН-05`, `ФИН-40`)."""

    sequence: int
    occurred_at: datetime
    action: str
    reason: ReasonCoded
    acting_authority: AuthorityReference
    state_after: str
    policy: PolicyBinding | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise MonetaryAmountInvalidError("sequence must be a positive integer")
        _require_text(self.action, "action")
        _require_text(self.state_after, "state_after")
        require_timezone(self.occurred_at, context="RecordHistoryEntry.occurred_at")


def _appended(
    history: tuple[RecordHistoryEntry, ...], act: GovernedAct, action: str, state_after: str
) -> tuple[RecordHistoryEntry, ...]:
    """Append one history entry, numbering it from the existing tuple."""
    entry = RecordHistoryEntry(
        sequence=len(history) + 1,
        occurred_at=act.at,
        action=action,
        reason=act.reason,
        acting_authority=act.by_authority,
        state_after=state_after,
        policy=act.policy,
    )
    return (*history, entry)


# ---------------------------------------------------------------------------
# Valuation of non-monetary value
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InKindValuation:
    """The basis on which a non-monetary contribution or benefit was
    valued (`ФИН-18`, canon 19f.7/19f.11).

    A valuation without a named method is an opinion, not a valuation -
    hence `ValuationMethodMissingError` on an empty `method_reference` -
    and one without an evidence reference cannot be re-performed by
    anyone reviewing it later."""

    basis: str
    method_reference: str
    valuation_date: date
    evidence_reference: EvidenceReference
    valued_amount: Money | None = None

    def __post_init__(self) -> None:
        if not self.method_reference or not self.method_reference.strip():
            raise ValuationMethodMissingError("an in-kind valuation must name its method reference")
        if not self.basis or not self.basis.strip():
            raise InKindValuationMissingError("an in-kind valuation must state its basis")


def assert_valuation_method(method_reference: str | None) -> str:
    """Raise unless a valuation names its method, and return it.

    Canon 19f.11 forbids revaluation without a method reference and a
    valuation date: an unexplained change of carrying value is
    indistinguishable from an unrecorded write-off."""
    if method_reference is None or not method_reference.strip():
        raise ValuationMethodMissingError("a valuation must name its valuation method reference")
    return method_reference


# ---------------------------------------------------------------------------
# Contributions
# ---------------------------------------------------------------------------


class ContributionKind(StrEnum):
    """Income kinds this aggregate governs (spec 4.2/4.4). The detailed
    taxonomy is a versioned `FinancePolicy(income_classification)`; this
    enum is only the structural family."""

    DONATION = "donation"
    MEMBERSHIP_FEE = "membership_fee"
    OFFICE_HOLDER_LEVY = "office_holder_levy"
    EVENT_INCOME = "event_income"
    PUBLIC_FUNDING = "public_funding"
    OTHER_INCOME = "other_income"


class ContributionState(StrEnum):
    """Contribution lifecycle (spec 8.2.7, canon 19f.7).

    `QUARANTINED` is where the unknown lands: an anonymous or
    unverifiable contribution is neither an ordinary accepted
    contribution nor silently dropped, but sits in a governed exceptional
    state until an authority decides (`ФИН-16`)."""

    RECEIVED = "received"
    QUARANTINED = "quarantined"
    ASSESSED = "assessed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RETURN_REQUIRED = "return_required"
    RETURNED = "returned"
    ESCALATED = "escalated"


#: Permitted contribution transitions. `received` -> `accepted` is
#: deliberately absent: canon 19f.7 forbids the direct hop, because
#: acceptance must always follow a resolved, policy-bound assessment
#: (`ФИН-16`, `ФИН-17`). The `quarantined` -> `quarantined` self-edge is
#: intentional: re-assessing a quarantined contribution that is still
#: unresolved appends a new decision and leaves it quarantined, rather
#: than being refused as "no change".
_ALLOWED_CONTRIBUTION_TRANSITIONS: frozenset[tuple[ContributionState, ContributionState]] = (
    frozenset(
        {
            (ContributionState.RECEIVED, ContributionState.QUARANTINED),
            (ContributionState.RECEIVED, ContributionState.ASSESSED),
            (ContributionState.QUARANTINED, ContributionState.QUARANTINED),
            (ContributionState.QUARANTINED, ContributionState.ASSESSED),
            (ContributionState.QUARANTINED, ContributionState.REJECTED),
            (ContributionState.QUARANTINED, ContributionState.RETURN_REQUIRED),
            (ContributionState.QUARANTINED, ContributionState.ESCALATED),
            (ContributionState.ASSESSED, ContributionState.QUARANTINED),
            (ContributionState.ASSESSED, ContributionState.ACCEPTED),
            (ContributionState.ASSESSED, ContributionState.REJECTED),
            (ContributionState.ASSESSED, ContributionState.RETURN_REQUIRED),
            (ContributionState.ASSESSED, ContributionState.ESCALATED),
            (ContributionState.ACCEPTED, ContributionState.RETURN_REQUIRED),
            (ContributionState.RETURN_REQUIRED, ContributionState.RETURNED),
            (ContributionState.RETURN_REQUIRED, ContributionState.ESCALATED),
        }
    )
)


@dataclass(frozen=True, slots=True)
class ContributionReceipt:
    """What was actually received - written once, never edited (`ФИН-18`,
    canon 19f.7).

    Either a monetary `amount` or an `in_kind_valuation`, never neither:
    a non-monetary contribution with no valuation basis has no financial
    value to report (`InKindValuationMissingError`). A contributor
    appears only as an opaque handle reference, or as `None` where the
    source could not be established - a fact about the receipt and,
    separately, the reason the contribution quarantines (`ФИН-01`,
    `ФИН-16`)."""

    receipt_id: UUID
    kind: ContributionKind
    received_at: datetime
    method: str
    amount: Money | None = None
    in_kind_valuation: InKindValuation | None = None
    contributor_handle_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.received_at, context="ContributionReceipt.received_at")
        _require_text(self.method, "method")
        if self.amount is None and self.in_kind_valuation is None:
            raise InKindValuationMissingError(
                "a contribution receipt must carry a monetary amount or an in-kind valuation"
            )
        if self.amount is not None:
            self.amount.assert_non_zero(context="ContributionReceipt.amount")
        if self.contributor_handle_reference is not None:
            _require_party_handle_reference(
                self.contributor_handle_reference, "contributor_handle_reference"
            )


@dataclass(frozen=True, slots=True)
class ContributionAssessment:
    """The outcome of assessing one contribution against a bound policy
    version (spec 8.2.7, canon 19f.7/19f.8).

    `is_resolved` is deliberately a conjunction of separate facts: an
    unestablished source, an incomplete verification and a classification
    no policy version produced are three different unknowns, each with
    its own reason code, and none may be papered over by the others.
    `aggregation_snapshot_digest` freezes the aggregate the threshold
    decision was taken on, so a later policy change never rewrites a past
    decision (`ФИН-14`, `ФИН-15`)."""

    assessment_id: UUID
    assessed_at: datetime
    assessed_by: AuthorityReference
    source_determined: bool
    verification_complete: bool
    prohibited: bool = False
    classification_code: str = ""
    policy: PolicyBinding | None = None
    aggregation_snapshot_digest: str | None = None
    related_party_group_reference: str | None = None
    intermediary_declaration_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.assessed_at, context="ContributionAssessment.assessed_at")

    @property
    def is_resolved(self) -> bool:
        """Whether this assessment permits any acceptance decision."""
        return (
            self.source_determined
            and self.verification_complete
            and self.policy is not None
            and bool(self.classification_code.strip())
        )


@dataclass(frozen=True, slots=True)
class FinanceContribution:
    """A contribution: one create-once receipt plus an append-only
    decision history (spec 8.2.7, canon 19f.7).

    The receipt is the fact; every later assessment, acceptance,
    rejection, return and escalation is a decision recorded *around* it,
    and `assert_receipt_unchanged` makes that structural rather than
    merely intended (`ФИН-18`)."""

    contribution_id: UUID
    scope: OrganizationalScopeRef
    receipt: ContributionReceipt
    retention: RetentionBinding
    state: ContributionState = ContributionState.RECEIVED
    assessment: ContributionAssessment | None = None
    conflict: ConflictDeclaration | None = None
    legal_case_reference: str | None = None
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        if self.state is ContributionState.ACCEPTED and self.assessment is None:
            raise ContributionClassificationUndeterminedError(
                "an accepted contribution must carry the resolved assessment it was accepted on"
            )

    def _to(
        self,
        target: ContributionState,
        act: GovernedAct,
        action: str,
        *,
        assessment: ContributionAssessment | None = None,
        legal_case_reference: str | None = None,
    ) -> FinanceContribution:
        if (self.state, target) not in _ALLOWED_CONTRIBUTION_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} contribution cannot transition to {target!s}"
            )
        self.scope.assert_matches(act.by_authority.scope)
        updated = replace(
            self,
            state=target,
            assessment=self.assessment if assessment is None else assessment,
            conflict=self.conflict if act.conflict is None else act.conflict,
            legal_case_reference=legal_case_reference or self.legal_case_reference,
            history=_appended(self.history, act, action, str(target)),
        )
        assert_receipt_unchanged(self, updated)
        return updated

    def quarantine(self, act: GovernedAct) -> FinanceContribution:
        """Move the contribution into the governed exceptional state.

        Where an anonymous, unverifiable, foreign-linked or
        suspected-intermediary contribution lands. Neither a rejection
        nor an acceptance: the recorded admission that the question is
        still open (`ФИН-16`)."""
        return self._to(ContributionState.QUARANTINED, act, "quarantined")

    def assess(self, assessment: ContributionAssessment, act: GovernedAct) -> FinanceContribution:
        """Record an assessment against a bound policy version.

        An unresolved assessment does not produce an `assessed`
        contribution: it quarantines. That is the whole of the
        fail-closed rule - the record never sits in a state from which
        acceptance looks routine while its source or verification is
        still open (`ФИН-16`, canon 19f.7)."""
        target = (
            ContributionState.ASSESSED if assessment.is_resolved else ContributionState.QUARANTINED
        )
        return self._to(target, act, "assessed", assessment=assessment)

    def accept(self, act: GovernedAct) -> FinanceContribution:
        """Accept the contribution as ordinary income.

        Every refusal is a distinct reason code, asked in order: is
        there an assessment, was the source established (`ФИН-16`), did
        verification complete, did a policy version classify it
        (`ФИН-41`), does policy prohibit it, is a return already owed
        (`ФИН-17`), is the conflict state declared (`ФИН-32`).
        `received` -> `accepted` never happens: the transition table
        holds no such edge."""
        if self.state is ContributionState.RETURN_REQUIRED:
            raise ContributionReturnRequiredError(
                "a return obligation is open on this contribution and blocks acceptance"
            )
        assessment = self.assessment
        if assessment is None:
            raise ContributionClassificationUndeterminedError(
                "acceptance requires a resolved assessment bound to a policy version"
            )
        if not assessment.source_determined:
            raise ContributionSourceUndeterminedError(
                "the contributor source could not be established - acceptance is refused"
            )
        if not assessment.verification_complete:
            raise ContributionVerificationIncompleteError(
                "a required verification or declaration is missing - acceptance is refused"
            )
        if assessment.policy is None or not assessment.classification_code.strip():
            raise ContributionClassificationUndeterminedError(
                "no policy-bound classification could be determined for this contribution"
            )
        if assessment.prohibited:
            raise ContributionProhibitedError(
                "policy classifies this contribution as prohibited or restricted"
            )
        assert_conflict_resolved(act.conflict, action="contribution acceptance")
        return self._to(ContributionState.ACCEPTED, act, "accepted")

    def reject(self, act: GovernedAct) -> FinanceContribution:
        """Refuse the contribution, leaving the receipt untouched."""
        return self._to(ContributionState.REJECTED, act, "rejected")

    def require_return(self, act: GovernedAct) -> FinanceContribution:
        """Record that this contribution must be returned (`ФИН-17`)."""
        return self._to(ContributionState.RETURN_REQUIRED, act, "return_required")

    def mark_returned(self, act: GovernedAct) -> FinanceContribution:
        """Record the completed return. The contribution stays in the
        register as one that *was* received: a returned contribution is
        never treated as never received (canon 19f.7)."""
        return self._to(ContributionState.RETURNED, act, "returned")

    def escalate(self, act: GovernedAct, *, legal_case_reference: str) -> FinanceContribution:
        """Escalate, citing the PACK-09 legal case opened for it.

        The case reference is mandatory: an escalation naming no case is
        an unresolved record with no owner. The case process itself stays
        PACK-09's (canon 19f.7, `ФИН-22`)."""
        _require_text(legal_case_reference, "legal_case_reference")
        return self._to(
            ContributionState.ESCALATED, act, "escalated", legal_case_reference=legal_case_reference
        )


def assert_receipt_unchanged(before: FinanceContribution, after: FinanceContribution) -> None:
    """Raise if a decision altered the create-once receipt (`ФИН-18`).

    Applied to every contribution transition, so "rejection, return and
    escalation leave the receipt unchanged" is a checked property of the
    code rather than a convention transitions are trusted to follow."""
    if before.receipt != after.receipt:
        raise ImmutableRecordModificationAttemptedError(
            "the contribution receipt is create-once and cannot be edited by a later decision"
        )


# ---------------------------------------------------------------------------
# Sponsorship
# ---------------------------------------------------------------------------


class SponsorshipState(StrEnum):
    """Sponsorship agreement lifecycle (spec 8.2.8, canon 19f.9)."""

    REGISTERED = "registered"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISCLOSURE_CLASSIFIED = "disclosure_classified"
    TERMINATED = "terminated"


_ALLOWED_SPONSORSHIP_TRANSITIONS: frozenset[tuple[SponsorshipState, SponsorshipState]] = frozenset(
    {
        (SponsorshipState.REGISTERED, SponsorshipState.UNDER_REVIEW),
        (SponsorshipState.UNDER_REVIEW, SponsorshipState.APPROVED),
        (SponsorshipState.UNDER_REVIEW, SponsorshipState.REJECTED),
        (SponsorshipState.APPROVED, SponsorshipState.DISCLOSURE_CLASSIFIED),
        (SponsorshipState.APPROVED, SponsorshipState.TERMINATED),
        (SponsorshipState.DISCLOSURE_CLASSIFIED, SponsorshipState.TERMINATED),
    }
)


def assert_disclosure_classified(disclosure_class: str | None, *, action: str) -> str:
    """Raise unless a disclosure classification has been recorded.

    A missing classification is not "not publishable" and not
    "publishable" - it is unknown, and an unknown disclosure state fails
    closed (`ФИН-19`, `ФИН-35`)."""
    if disclosure_class is None or not disclosure_class.strip():
        raise SponsorshipDisclosureIncompleteError(
            f"{action} requires a recorded disclosure classification"
        )
    return disclosure_class


@dataclass(frozen=True, slots=True)
class SponsorshipAgreement:
    """A payment or benefit with an agreed counter-performance (spec
    8.2.8, canon 19f.9).

    The difference between sponsorship and a donation is the
    counter-performance, and it is *never* inferred from the amount or
    from who paid. Either a counter-performance is described, or a policy
    version explicitly classifies this agreement as one without; absent
    both, approval is refused (`ФИН-19`).

    Nothing here records a meeting, a contact, a calendar entry or an
    access relationship - those belong to PACK-35 (`ФИН-20`, see
    `assert_not_lobbying_subject`)."""

    agreement_id: UUID
    scope: OrganizationalScopeRef
    sponsor_handle_reference: str
    benefit_description: str
    period_start: date
    period_end: date
    retention: RetentionBinding
    value: Money | None = None
    in_kind_valuation: InKindValuation | None = None
    counter_performance: str | None = None
    counter_performance_absent_policy_binding: PolicyBinding | None = None
    linked_activity_reference: str | None = None
    disclosure_class: str | None = None
    review_state: SponsorshipState = SponsorshipState.REGISTERED
    conflict: ConflictDeclaration | None = None
    conflict_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_party_handle_reference(self.sponsor_handle_reference, "sponsor_handle_reference")
        _require_text(self.benefit_description, "benefit_description")
        if self.period_end < self.period_start:
            raise MonetaryAmountInvalidError("period_end must not precede period_start")
        if self.value is None and self.in_kind_valuation is None:
            raise InKindValuationMissingError(
                "a sponsorship agreement must carry a monetary value or an in-kind valuation"
            )

    def _to(
        self,
        target: SponsorshipState,
        act: GovernedAct,
        action: str,
        *,
        disclosure_class: str | None = None,
    ) -> SponsorshipAgreement:
        if (self.review_state, target) not in _ALLOWED_SPONSORSHIP_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.review_state!s} sponsorship agreement cannot transition to {target!s}"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            review_state=target,
            disclosure_class=disclosure_class or self.disclosure_class,
            conflict=self.conflict if act.conflict is None else act.conflict,
            history=_appended(self.history, act, action, str(target)),
        )

    def begin_review(self, act: GovernedAct) -> SponsorshipAgreement:
        """Open the review that approval must come out of."""
        return self._to(SponsorshipState.UNDER_REVIEW, act, "review_opened")

    def approve(self, act: GovernedAct) -> SponsorshipAgreement:
        """Approve the agreement.

        Refused unless a counter-performance is recorded **or**
        `counter_performance_absent_policy_binding` names the policy
        version that classified this agreement as one without: an
        approval that can cite neither is an approval of something nobody
        has characterised (`ФИН-19`, canon 19f.9). A blocking or
        undeclared conflict refuses independently (`ФИН-32`)."""
        described = bool(self.counter_performance and self.counter_performance.strip())
        if not described and self.counter_performance_absent_policy_binding is None:
            raise CounterPerformanceMissingError(
                "approval requires a recorded counter-performance, or an explicit policy "
                "binding classifying this agreement as one without"
            )
        assert_conflict_resolved(act.conflict, action="sponsorship approval")
        return self._to(SponsorshipState.APPROVED, act, "approved")

    def reject(self, act: GovernedAct) -> SponsorshipAgreement:
        """Refuse the agreement with a recorded reason."""
        return self._to(SponsorshipState.REJECTED, act, "rejected")

    def classify_disclosure(
        self, act: GovernedAct, *, disclosure_class: str
    ) -> SponsorshipAgreement:
        """Bind the disclosure classification and, through `act.policy`,
        the policy version that produced it.

        Whether a *downward* reclassification would escape publication is
        a policy question the application layer refuses separately
        (`ФИН-13`); what this method refuses is an empty or missing
        classification (`ФИН-19`, `ФИН-35`)."""
        assert_disclosure_classified(disclosure_class, action="disclosure classification")
        return self._to(
            SponsorshipState.DISCLOSURE_CLASSIFIED,
            act,
            "disclosure_classified",
            disclosure_class=disclosure_class,
        )

    def terminate(self, act: GovernedAct) -> SponsorshipAgreement:
        """End the agreement with a recorded reason."""
        return self._to(SponsorshipState.TERMINATED, act, "terminated")


# ---------------------------------------------------------------------------
# External financial benefit and the PACK-35 boundary
# ---------------------------------------------------------------------------

#: Subject kinds PACK-35 owns. PACK-10 records a **measurable financial
#: value or a financially valued benefit** attributable to a party
#: organization; PACK-35 records a **contact, meeting, access or
#: influence relationship** with no financial value recorded. A meeting
#: that produced a sponsorship yields two records - a PACK-10 agreement
#: and, later, a PACK-35 meeting record - linked by one typed reference,
#: neither owning the other (spec 4.5, canon 19f.9, `ФИН-20`).
PACK_35_SUBJECT_KINDS: frozenset[str] = frozenset(
    {"meeting", "contact", "access_grant", "calendar_entry", "lobbying_register_entry"}
)


def assert_not_lobbying_subject(subject_kind: str) -> None:
    """Refuse to record a PACK-35 subject on a finance record.

    Raises `UnauthorizedStateTransitionError`, deliberately: nothing is
    leaking, so this is not an identity-linkage failure, and no
    disclosure is missing, so it is not a disclosure failure. What is
    wrong is that the *act itself* is not one this context may perform -
    PACK-10 implements none of PACK-35's entities, and a benefit record
    bent into a meeting log would be that implementation arriving by the
    back door (spec 4.5, canon 19f.9, `ФИН-20`). A pure function on the
    subject kind, so it is callable at any boundary accepting a
    caller-supplied kind."""
    if subject_kind.strip().lower() in PACK_35_SUBJECT_KINDS:
        raise UnauthorizedStateTransitionError(
            f"subject kind {subject_kind!r} belongs to PACK-35 (lobbying, meetings, access) "
            "and may not be recorded as a finance record"
        )


class ExternalBenefitType(StrEnum):
    """Financially measurable external benefits received without an
    agreement (spec 8.2.9, canon 19f.9)."""

    PAID_THIRD_PARTY_SUPPORT = "paid_third_party_support"
    IN_KIND_CAMPAIGN_SUPPORT = "in_kind_campaign_support"
    SUBSIDISED_SERVICE = "subsidised_service"
    GUARANTEE = "guarantee"
    FORGIVEN_DEBT = "forgiven_debt"
    OTHER_MEASURABLE_BENEFIT = "other_measurable_benefit"


class ExternalBenefitState(StrEnum):
    """`recorded` -> `valued` -> `assessed` -> (`disclosed` |
    `not_publishable`) (spec 8.2.9)."""

    RECORDED = "recorded"
    VALUED = "valued"
    ASSESSED = "assessed"
    DISCLOSED = "disclosed"
    NOT_PUBLISHABLE = "not_publishable"


_ALLOWED_BENEFIT_TRANSITIONS: frozenset[tuple[ExternalBenefitState, ExternalBenefitState]] = (
    frozenset(
        {
            (ExternalBenefitState.RECORDED, ExternalBenefitState.VALUED),
            (ExternalBenefitState.VALUED, ExternalBenefitState.VALUED),
            (ExternalBenefitState.VALUED, ExternalBenefitState.ASSESSED),
            (ExternalBenefitState.ASSESSED, ExternalBenefitState.DISCLOSED),
            (ExternalBenefitState.ASSESSED, ExternalBenefitState.NOT_PUBLISHABLE),
        }
    )
)


@dataclass(frozen=True, slots=True)
class ExternalFinancialBenefit:
    """A financially measurable benefit received without an agreement
    (spec 8.2.9, canon 19f.9).

    `subject_kind` is checked against `PACK_35_SUBJECT_KINDS` at
    construction: this aggregate exists to record value, and the moment
    its subject is a meeting or a contact it has stopped being a finance
    record (`ФИН-20`). Recording a benefit with no valuation basis is
    refused (`ФИН-19`)."""

    benefit_id: UUID
    scope: OrganizationalScopeRef
    benefit_type: ExternalBenefitType
    retention: RetentionBinding
    subject_kind: str = "financial_benefit"
    value: Money | None = None
    in_kind_valuation: InKindValuation | None = None
    state: ExternalBenefitState = ExternalBenefitState.RECORDED
    assessment_outcome: str | None = None
    disclosure_class: str | None = None
    provider_handle_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        assert_not_lobbying_subject(self.subject_kind)
        if self.value is None and self.in_kind_valuation is None:
            raise InKindValuationMissingError(
                "an external financial benefit must carry a value or an in-kind valuation"
            )
        if self.provider_handle_reference is not None:
            _require_party_handle_reference(
                self.provider_handle_reference, "provider_handle_reference"
            )

    def _to(
        self,
        target: ExternalBenefitState,
        act: GovernedAct,
        action: str,
        *,
        valuation: InKindValuation | None = None,
        assessment_outcome: str | None = None,
        disclosure_class: str | None = None,
    ) -> ExternalFinancialBenefit:
        if (self.state, target) not in _ALLOWED_BENEFIT_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} external benefit cannot transition to {target!s}"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            in_kind_valuation=valuation or self.in_kind_valuation,
            assessment_outcome=assessment_outcome or self.assessment_outcome,
            disclosure_class=disclosure_class or self.disclosure_class,
            history=_appended(self.history, act, action, str(target)),
        )

    def record_valuation(
        self, valuation: InKindValuation, act: GovernedAct
    ) -> ExternalFinancialBenefit:
        """Attach or restate the valuation basis. `InKindValuation`
        refuses an empty method reference itself (`ФИН-18`)."""
        return self._to(ExternalBenefitState.VALUED, act, "valued", valuation=valuation)

    def assess(self, act: GovernedAct, *, outcome: str) -> ExternalFinancialBenefit:
        """Assess whether this benefit is legally a contribution, against
        the policy version `act.policy` names (`ФИН-23`)."""
        _require_text(outcome, "outcome")
        return self._to(ExternalBenefitState.ASSESSED, act, "assessed", assessment_outcome=outcome)

    def classify_disclosure(
        self, act: GovernedAct, *, disclosure_class: str, publishable: bool
    ) -> ExternalFinancialBenefit:
        """Classify disclosure. An empty classification is refused, since
        an unknown disclosure state fails closed (`ФИН-35`)."""
        assert_disclosure_classified(disclosure_class, action="benefit disclosure classification")
        target = (
            ExternalBenefitState.DISCLOSED if publishable else ExternalBenefitState.NOT_PUBLISHABLE
        )
        return self._to(target, act, "disclosure_classified", disclosure_class=disclosure_class)


# ---------------------------------------------------------------------------
# Expenses, payment authorization and reimbursement
# ---------------------------------------------------------------------------


def assert_not_self_acting(
    claimant_handle_reference: str, authority: AuthorityReference, *, action: str
) -> None:
    """Refuse an act taken by the person who benefits from it (`ФИН-31`,
    canon 19f.10).

    Compares the claimant's purpose-scoped handle reference with the
    authority's `actor_reference`, the only actor-level value this
    service holds. Where both are present and equal the act is refused
    whichever role the authority names: holding `payment_authorizer`
    does not make self-payment lawful. An authority carrying no actor
    reference is not *cleared* here either - the caller resolves it
    through the authorisation port first."""
    actor = authority.actor_reference.strip()
    if actor and actor == claimant_handle_reference.strip():
        raise SelfApprovalProhibitedError(
            f"the claimant may not perform {action} on their own claim"
        )


class ExpenseClaimState(StrEnum):
    """Expense claim lifecycle (spec 8.2.10, canon 19f.10)."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYMENT_AUTHORIZED = "payment_authorized"
    SETTLED = "settled"
    CORRECTED = "corrected"


_ALLOWED_CLAIM_TRANSITIONS: frozenset[tuple[ExpenseClaimState, ExpenseClaimState]] = frozenset(
    {
        (ExpenseClaimState.SUBMITTED, ExpenseClaimState.UNDER_REVIEW),
        (ExpenseClaimState.UNDER_REVIEW, ExpenseClaimState.APPROVED),
        (ExpenseClaimState.UNDER_REVIEW, ExpenseClaimState.REJECTED),
        (ExpenseClaimState.APPROVED, ExpenseClaimState.PAYMENT_AUTHORIZED),
        (ExpenseClaimState.PAYMENT_AUTHORIZED, ExpenseClaimState.SETTLED),
        (ExpenseClaimState.SETTLED, ExpenseClaimState.CORRECTED),
        (ExpenseClaimState.REJECTED, ExpenseClaimState.CORRECTED),
    }
)


class PaymentAuthorizationState(StrEnum):
    """`authorized` -> (`executed` | `revoked`) (spec 8.2.11)."""

    AUTHORIZED = "authorized"
    EXECUTED = "executed"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class PaymentAuthorization:
    """A create-once authorization to pay one governed payable (spec
    8.2.11, canon 19f.10).

    Separate from the claim, because authorising and executing must be
    separable and because obligations, contribution returns and other
    payables need the same shape. The payable is referenced by a typed
    `(payable_kind, payable_reference)` pair, never a free string. Only
    `execute` and `revoke` change it, each at most once; there is no edit
    path for an executed authorization (`ФИН-31`, `ФИН-05`)."""

    authorization_id: UUID
    scope: OrganizationalScopeRef
    payable_kind: str
    payable_reference: UUID
    authorising_authority: AuthorityReference
    amount: Money
    authorized_at: datetime
    reason: ReasonCoded
    state: PaymentAuthorizationState = PaymentAuthorizationState.AUTHORIZED
    payee_handle_reference: str | None = None
    executed_by: AuthorityReference | None = None
    executed_at: datetime | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.payable_kind, "payable_kind")
        require_timezone(self.authorized_at, context="PaymentAuthorization.authorized_at")
        self.amount.assert_non_zero(context="PaymentAuthorization.amount")
        self.scope.assert_matches(self.authorising_authority.scope)
        if self.payee_handle_reference is not None:
            _require_party_handle_reference(self.payee_handle_reference, "payee_handle_reference")
        if self.executed_at is not None:
            require_timezone(self.executed_at, context="PaymentAuthorization.executed_at")

    @property
    def is_executable(self) -> bool:
        """Whether this authorization may still be executed."""
        return self.state is PaymentAuthorizationState.AUTHORIZED

    def execute(self, by_authority: AuthorityReference, *, at: datetime) -> PaymentAuthorization:
        """Record execution by an authority distinct from the authoriser.

        Executing an already-executed authorization edits a create-once
        record; executing a revoked one is a forbidden transition; and an
        executor equal to the authoriser - by authority id or by actor
        reference - is the self-approval canon 19f.10 forbids outright
        (`ФИН-31`)."""
        if self.state is PaymentAuthorizationState.EXECUTED:
            raise ImmutableRecordModificationAttemptedError(
                "an executed payment authorization cannot be executed or edited again"
            )
        if self.state is PaymentAuthorizationState.REVOKED:
            raise UnauthorizedStateTransitionError(
                "a revoked payment authorization can never be executed"
            )
        if by_authority.authority_id == self.authorising_authority.authority_id:
            raise SelfApprovalProhibitedError(
                "the executing authority must differ from the authorising authority"
            )
        executor = by_authority.actor_reference.strip()
        authoriser = self.authorising_authority.actor_reference.strip()
        if executor and authoriser and executor == authoriser:
            raise SelfApprovalProhibitedError(
                "the executing actor must differ from the authorising actor"
            )
        if self.payee_handle_reference is not None:
            assert_not_self_acting(self.payee_handle_reference, by_authority, action="execution")
        require_timezone(at, context="PaymentAuthorization.execute")
        return replace(
            self, state=PaymentAuthorizationState.EXECUTED, executed_by=by_authority, executed_at=at
        )

    def revoke(self, act: GovernedAct) -> PaymentAuthorization:
        """Revoke before execution. An executed authorization is
        immutable and cannot be revoked after the fact (`ФИН-05`)."""
        if self.state is PaymentAuthorizationState.EXECUTED:
            raise ImmutableRecordModificationAttemptedError(
                "an executed payment authorization cannot be revoked"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(self, state=PaymentAuthorizationState.REVOKED, reason=act.reason)


@dataclass(frozen=True, slots=True)
class ExpenseClaim:
    """A claim for reimbursement, with an append-only review history
    (spec 8.2.10, canon 19f.10).

    Review, approval, authorisation and execution are four distinct acts
    by four distinct authorities, and the claimant performs none of them:
    every transition runs `assert_not_self_acting` first (`ФИН-31`).
    Settlement additionally requires a bound authorization - a payment no
    one authorised is refused rather than reconstructed (canon
    19f.10)."""

    claim_id: UUID
    scope: OrganizationalScopeRef
    claimant_handle_reference: str
    purpose_class: str
    amount: Money
    retention: RetentionBinding
    evidence: tuple[EvidenceReference, ...] = ()
    state: ExpenseClaimState = ExpenseClaimState.SUBMITTED
    payment_authorization_id: UUID | None = None
    corrects_claim_id: UUID | None = None
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_party_handle_reference(self.claimant_handle_reference, "claimant_handle_reference")
        _require_text(self.purpose_class, "purpose_class")
        self.amount.assert_non_zero(context="ExpenseClaim.amount")
        if not self.evidence and self.state is not ExpenseClaimState.SUBMITTED:
            raise EvidenceReferenceMissingError(
                "an expense claim under review must cite at least one evidence reference"
            )
        if self.corrects_claim_id == self.claim_id:
            raise UnauthorizedStateTransitionError("an expense claim cannot correct itself")

    def _to(
        self,
        target: ExpenseClaimState,
        act: GovernedAct,
        action: str,
        *,
        payment_authorization_id: UUID | None = None,
    ) -> ExpenseClaim:
        if (self.state, target) not in _ALLOWED_CLAIM_TRANSITIONS:
            raise UnauthorizedStateTransitionError(
                f"a {self.state!s} expense claim cannot transition to {target!s}"
            )
        assert_not_self_acting(self.claimant_handle_reference, act.by_authority, action=action)
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=target,
            payment_authorization_id=payment_authorization_id or self.payment_authorization_id,
            history=_appended(self.history, act, action, str(target)),
        )

    def review(self, act: GovernedAct) -> ExpenseClaim:
        """Open review. The reviewer declares a conflict state; unknown
        fails closed (`ФИН-32`)."""
        assert_conflict_resolved(act.conflict, action="expense claim review")
        return self._to(ExpenseClaimState.UNDER_REVIEW, act, "review")

    def approve(self, act: GovernedAct) -> ExpenseClaim:
        """Approve the claim. The approver is never the claimant, and an
        undeclared or blocking conflict refuses (`ФИН-31`, `ФИН-32`)."""
        assert_conflict_resolved(act.conflict, action="expense claim approval")
        return self._to(ExpenseClaimState.APPROVED, act, "approval")

    def reject(self, act: GovernedAct) -> ExpenseClaim:
        """Refuse the claim with a recorded reason."""
        return self._to(ExpenseClaimState.REJECTED, act, "rejection")

    def authorize_payment(
        self, authorization: PaymentAuthorization, act: GovernedAct
    ) -> ExpenseClaim:
        """Bind the payment authorization raised for this claim.

        The authorization must reference this claim and still be
        `authorized`: binding a revoked or already-executed one would let
        a settled payment cite something that never permitted it. The
        authorising authority is checked against the claimant too
        (`ФИН-31`)."""
        if authorization.payable_reference != self.claim_id:
            raise PaymentAuthorizationMissingError(
                "the payment authorization does not reference this expense claim"
            )
        if not authorization.is_executable:
            raise PaymentAuthorizationMissingError(
                f"a {authorization.state!s} payment authorization cannot be bound to a claim"
            )
        assert_not_self_acting(
            self.claimant_handle_reference,
            authorization.authorising_authority,
            action="payment authorization",
        )
        return self._to(
            ExpenseClaimState.PAYMENT_AUTHORIZED,
            act,
            "payment_authorization",
            payment_authorization_id=authorization.authorization_id,
        )

    def settle(self, act: GovernedAct) -> ExpenseClaim:
        """Record settlement by the executing authority.

        Refused outright when no authorization has been bound: settlement
        without an authorization is the failure canon 19f.10 names first
        (`ФИН-31`)."""
        if self.payment_authorization_id is None:
            raise PaymentAuthorizationMissingError(
                "settlement requires a bound, valid payment authorization"
            )
        return self._to(ExpenseClaimState.SETTLED, act, "settlement")

    def correct(self, act: GovernedAct) -> ExpenseClaim:
        """Mark this claim as corrected by a later claim.

        The correcting claim is a NEW record carrying `corrects_claim_id`;
        a settled claim is never edited in place (canon 19f.10)."""
        return self._to(ExpenseClaimState.CORRECTED, act, "correction")


@dataclass(frozen=True, slots=True)
class Reimbursement:
    """The create-once payout record of a settled expense claim.

    The payout is a fact in its own right, not a derived reading of the
    claim's state: it names the claim, the authorization that permitted
    the payment and the executing authority. There is no mutator - a
    wrong reimbursement is corrected by a correcting claim and a new
    record (`ФИН-05`, `ФИН-31`)."""

    reimbursement_id: UUID
    scope: OrganizationalScopeRef
    claim_id: UUID
    authorization_id: UUID
    amount: Money
    settled_at: datetime
    executed_by: AuthorityReference
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        require_timezone(self.settled_at, context="Reimbursement.settled_at")
        self.amount.assert_non_zero(context="Reimbursement.amount")
        self.scope.assert_matches(self.executed_by.scope)


# ---------------------------------------------------------------------------
# Obligations and assets
# ---------------------------------------------------------------------------


class ObligationType(StrEnum):
    """Every liability shape lives here (spec 8.2.14, canon 19f.11).

    There is deliberately no separate `Liability` aggregate: splitting it
    out would duplicate an identical lifecycle and valuation model."""

    RECEIVABLE = "receivable"
    PAYABLE = "payable"
    LOAN = "loan"
    CREDIT = "credit"
    GUARANTEE = "guarantee"
    CONTINGENT_LIABILITY = "contingent_liability"
    LONG_TERM_OBLIGATION = "long_term_obligation"
    OTHER = "other"


class PositionState(StrEnum):
    """Shared lifecycle of assets and obligations: `recorded` -> `valued`
    -> (`revalued`)* -> terminal (canon 19f.11)."""

    RECORDED = "recorded"
    VALUED = "valued"
    REVALUED = "revalued"
    SETTLED = "settled"
    WRITTEN_OFF = "written_off"
    EXPIRED = "expired"
    DISPOSED = "disposed"


#: Terminal position states. A record in one of these is closed, and any
#: further change is an edit of a settled record, which `ФИН-05` refuses.
_TERMINAL_POSITION_STATES: frozenset[PositionState] = frozenset(
    {
        PositionState.SETTLED,
        PositionState.WRITTEN_OFF,
        PositionState.EXPIRED,
        PositionState.DISPOSED,
    }
)


def assert_write_off_authorized(
    by_authority: AuthorityReference | None,
    reason: ReasonCoded | None,
    *,
    legal_case_reference: str | None = None,
    requires_case_citation: bool = False,
) -> tuple[AuthorityReference, ReasonCoded]:
    """Raise unless a write-off names both an authority and a reason.

    A write-off removes value from the books, so canon 19f.11 requires
    the authority the policy names and a recorded reason - never a bare
    state change. Where a PACK-09 case still concerns the position, the
    case must be cited too, so a write-off cannot quietly close something
    a case is still about (`ФИН-22`)."""
    if by_authority is None or reason is None:
        raise WriteOffNotAuthorizedError(
            "a write-off requires both a named authority and a recorded reason code"
        )
    if requires_case_citation and (
        legal_case_reference is None or not legal_case_reference.strip()
    ):
        raise WriteOffNotAuthorizedError(
            "writing off a position an open legal case still concerns must cite that case"
        )
    return by_authority, reason


@dataclass(frozen=True, slots=True)
class FinancialObligation:
    """A receivable, payable, loan, credit, guarantee, contingent or
    long-term obligation (spec 8.2.14, canon 19f.11).

    Settlement requires a `PaymentAuthorization` referencing *this*
    obligation, revaluation requires a method reference and a valuation
    date, and a write-off requires an authority and a reason. A settled
    obligation is terminal and is never edited (`ФИН-05`, `ФИН-31`)."""

    obligation_id: UUID
    scope: OrganizationalScopeRef
    obligation_type: ObligationType
    amount: Money
    valuation_date: date
    method_reference: str
    retention: RetentionBinding
    state: PositionState = PositionState.RECORDED
    counterparty_handle_reference: str | None = None
    settlement_authorization_id: UUID | None = None
    legal_case_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        assert_valuation_method(self.method_reference)
        self.amount.assert_non_zero(context="FinancialObligation.amount")
        if self.counterparty_handle_reference is not None:
            _require_party_handle_reference(
                self.counterparty_handle_reference, "counterparty_handle_reference"
            )

    def _assert_open(self, action: str) -> None:
        if self.state in _TERMINAL_POSITION_STATES:
            raise ImmutableRecordModificationAttemptedError(
                f"a {self.state!s} obligation is closed and refuses {action}"
            )

    @classmethod
    def record(
        cls,
        act: GovernedAct,
        *,
        obligation_id: UUID,
        scope: OrganizationalScopeRef,
        obligation_type: ObligationType,
        amount: Money,
        valuation_date: date,
        method_reference: str,
        retention: RetentionBinding,
        counterparty_handle_reference: str | None = None,
        evidence: tuple[EvidenceReference, ...] = (),
    ) -> FinancialObligation:
        """Record a new obligation with its opening history entry.

        A classmethod rather than a bare constructor call so the first
        history entry - who recorded it, when, and under which reason
        code - cannot be omitted (`ФИН-40`)."""
        scope.assert_matches(act.by_authority.scope)
        return cls(
            obligation_id=obligation_id,
            scope=scope,
            obligation_type=obligation_type,
            amount=amount,
            valuation_date=valuation_date,
            method_reference=method_reference,
            retention=retention,
            state=PositionState.VALUED,
            counterparty_handle_reference=counterparty_handle_reference,
            evidence=evidence,
            history=_appended((), act, "recorded", str(PositionState.VALUED)),
        )

    def revalue(
        self, act: GovernedAct, *, amount: Money, valuation_date: date, method_reference: str | None
    ) -> FinancialObligation:
        """Restate the carrying value, naming the method used.

        An unnamed method raises `ValuationMethodMissingError`: an
        unexplained change of carrying value is indistinguishable from an
        unrecorded write-off (canon 19f.11)."""
        self._assert_open("revaluation")
        method = assert_valuation_method(method_reference)
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            amount=amount,
            valuation_date=valuation_date,
            method_reference=method,
            state=PositionState.REVALUED,
            history=_appended(self.history, act, "revalued", str(PositionState.REVALUED)),
        )

    def settle(
        self, act: GovernedAct, *, authorization: PaymentAuthorization | None
    ) -> FinancialObligation:
        """Settle the obligation through a payment authorization.

        The authorization is mandatory and must reference this
        obligation: settling without one is the failure canon 19f.11
        names, and settling against someone else's authorization is the
        same failure wearing a reference (`ФИН-31`)."""
        self._assert_open("settlement")
        if authorization is None:
            raise PaymentAuthorizationMissingError(
                "settling an obligation requires a payment authorization"
            )
        if authorization.payable_reference != self.obligation_id:
            raise PaymentAuthorizationMissingError(
                "the payment authorization does not reference this obligation"
            )
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            state=PositionState.SETTLED,
            settlement_authorization_id=authorization.authorization_id,
            history=_appended(self.history, act, "settled", str(PositionState.SETTLED)),
        )

    def write_off(
        self,
        *,
        at: datetime,
        by_authority: AuthorityReference | None,
        reason: ReasonCoded | None,
        legal_case_reference: str | None = None,
    ) -> FinancialObligation:
        """Write the obligation off with authority and a reason.

        `by_authority` and `reason` are optional in the signature only
        so that their absence is a governed `WriteOffNotAuthorizedError`
        rather than a type error at a boundary populated from a request.
        A contingent liability an open case still concerns must cite that
        case (canon 19f.11, `ФИН-22`)."""
        self._assert_open("write-off")
        needs_case = (
            self.obligation_type is ObligationType.CONTINGENT_LIABILITY
            and self.legal_case_reference is not None
        )
        case = legal_case_reference or self.legal_case_reference
        authority, recorded = assert_write_off_authorized(
            by_authority, reason, legal_case_reference=case, requires_case_citation=needs_case
        )
        self.scope.assert_matches(authority.scope)
        act = GovernedAct(at=at, by_authority=authority, reason=recorded)
        return replace(
            self,
            state=PositionState.WRITTEN_OFF,
            legal_case_reference=case,
            history=_appended(self.history, act, "written_off", str(PositionState.WRITTEN_OFF)),
        )


@dataclass(frozen=True, slots=True)
class FinancialAsset:
    """A financially relevant asset position (spec 8.2.13, canon 19f.11).

    Deliberately minimal: PACK-10 builds no asset-management system, so
    there is no maintenance schedule, no inventory operation and no
    depreciation engine - only a recorded valuation, its date and the
    method behind it. `revalue` and `write_off` carry the same rules the
    obligation aggregate does."""

    asset_id: UUID
    scope: OrganizationalScopeRef
    asset_class: str
    valuation: Money
    valuation_date: date
    method_reference: str
    retention: RetentionBinding
    state: PositionState = PositionState.VALUED
    asset_reference: str | None = None
    legal_case_reference: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()
    history: tuple[RecordHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.asset_class, "asset_class")
        assert_valuation_method(self.method_reference)

    def _assert_open(self, action: str) -> None:
        if self.state in _TERMINAL_POSITION_STATES:
            raise ImmutableRecordModificationAttemptedError(
                f"a {self.state!s} asset is closed and refuses {action}"
            )

    def revalue(
        self,
        act: GovernedAct,
        *,
        valuation: Money,
        valuation_date: date,
        method_reference: str | None,
    ) -> FinancialAsset:
        """Restate the carrying value, naming the method used (`ФИН-18`,
        canon 19f.11)."""
        self._assert_open("revaluation")
        method = assert_valuation_method(method_reference)
        self.scope.assert_matches(act.by_authority.scope)
        return replace(
            self,
            valuation=valuation,
            valuation_date=valuation_date,
            method_reference=method,
            state=PositionState.REVALUED,
            history=_appended(self.history, act, "revalued", str(PositionState.REVALUED)),
        )

    def write_off(
        self,
        *,
        at: datetime,
        by_authority: AuthorityReference | None,
        reason: ReasonCoded | None,
        legal_case_reference: str | None = None,
    ) -> FinancialAsset:
        """Write the asset off with authority and a reason.

        Disposal of an asset under a PACK-09 legal hold is refused
        upstream by PACK-09; what this method guarantees is that the
        write-off itself is authorized, reason-coded and, where a case
        concerns the asset, case-citing (canon 19f.11)."""
        self._assert_open("write-off")
        case = legal_case_reference or self.legal_case_reference
        authority, recorded = assert_write_off_authorized(
            by_authority,
            reason,
            legal_case_reference=case,
            requires_case_citation=self.legal_case_reference is not None,
        )
        self.scope.assert_matches(authority.scope)
        act = GovernedAct(at=at, by_authority=authority, reason=recorded)
        return replace(
            self,
            state=PositionState.WRITTEN_OFF,
            legal_case_reference=case,
            history=_appended(self.history, act, "written_off", str(PositionState.WRITTEN_OFF)),
        )


# ---------------------------------------------------------------------------
# Governed transfers between organizational units
# ---------------------------------------------------------------------------


class TransferDirection(StrEnum):
    """Which end of a governed transfer a leg represents."""

    OUTGOING = "outgoing"
    INCOMING = "incoming"


@dataclass(frozen=True, slots=True)
class TransferLeg:
    """One scoped side of a governed transfer.

    A leg is not a transfer: it is what one organizational unit records.
    The *pair* is what consolidation eliminates, and it eliminates it
    exactly once (`ФИН-37`, canon 19f.6/19f.19)."""

    leg_id: UUID
    scope: OrganizationalScopeRef
    direction: TransferDirection
    amount: Money
    transaction_id: UUID | None = None

    def __post_init__(self) -> None:
        self.amount.assert_non_zero(context="TransferLeg.amount")


def assert_transfer_pair_resolvable(
    legs: tuple[TransferLeg, ...],
) -> tuple[TransferLeg, TransferLeg]:
    """Raise unless `legs` is a complete, resolvable transfer pair.

    Four refusals, all `TransferPairUnresolvedError`: there must be
    exactly **two** legs (one leg is a half-recorded movement
    consolidation would double-count or drop); they must sit in
    **different scopes** (a movement inside one unit is not a transfer,
    and pairing a scope with itself would let the record be eliminated
    against itself); there must be one **outgoing** and one **incoming**
    leg; and the **amounts must be equal**, since a transfer that changes
    value in flight is two facts, not one. A contribution is income to
    exactly one unit; any onward movement is a transfer, never new income
    (canon 19f.6)."""
    if len(legs) != 2:
        raise TransferPairUnresolvedError(
            f"a governed transfer needs exactly two legs, found {len(legs)}"
        )
    first, second = legs
    if first.scope.organization_id == second.scope.organization_id:
        raise TransferPairUnresolvedError(
            "the two legs of a governed transfer must sit in different organizational scopes"
        )
    if {first.direction, second.direction} != {
        TransferDirection.OUTGOING,
        TransferDirection.INCOMING,
    }:
        raise TransferPairUnresolvedError(
            "a governed transfer needs one outgoing and one incoming leg"
        )
    if first.amount != second.amount:
        raise TransferPairUnresolvedError(
            "the two legs of a governed transfer must carry the same amount"
        )
    return first, second


@dataclass(frozen=True, slots=True)
class GovernedTransfer:
    """Two scoped legs bound by one `internal_transfer_reference` (spec
    4.3, canon 19f.6).

    The shared reference is the whole point: it lets consolidation
    recognise the pair and eliminate it exactly once, without a higher
    scope ever writing into a lower one (`ФИН-37`). The pair is validated
    at construction, so an incomplete or same-scope transfer cannot be
    stored and discovered later."""

    transfer_id: UUID
    internal_transfer_reference: str
    legs: tuple[TransferLeg, ...]
    reason: ReasonCoded
    recorded_at: datetime
    recorded_by: AuthorityReference
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.internal_transfer_reference, "internal_transfer_reference")
        require_timezone(self.recorded_at, context="GovernedTransfer.recorded_at")
        assert_transfer_pair_resolvable(self.legs)

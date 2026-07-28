"""Tests for `epd2_finance_service.records` - contributions and their
exceptional states, sponsorship, external financial benefit, expense
claims, payment authorization, obligations and governed transfers.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    EvidenceKind,
    EvidenceReference,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    ReasonCoded,
    RetentionBinding,
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
from epd2_finance_service.records import (
    PACK_35_SUBJECT_KINDS,
    ContributionAssessment,
    ContributionKind,
    ContributionReceipt,
    ContributionState,
    ExpenseClaim,
    ExpenseClaimState,
    ExternalBenefitType,
    ExternalFinancialBenefit,
    FinanceContribution,
    FinancialObligation,
    GovernedAct,
    InKindValuation,
    ObligationType,
    PaymentAuthorization,
    PaymentAuthorizationState,
    PositionState,
    Reimbursement,
    SponsorshipAgreement,
    SponsorshipState,
    TransferDirection,
    TransferLeg,
    assert_not_lobbying_subject,
    assert_not_self_acting,
    assert_transfer_pair_resolvable,
    assert_valuation_method,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)
_NO_CONFLICT = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board")
_UNDECLARED = ConflictDeclaration(state=ConflictDeclaration.UNDECLARED, declared_by="board")
_BLOCKING = ConflictDeclaration(state=ConflictDeclaration.BLOCKING, declared_by="board")


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _authority(scope: OrganizationalScopeRef, *, actor: str) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(),
        role_code="finance_administrator",
        scope=scope,
        actor_reference=actor,
    )


def _handle_reference(purpose: HandlePurpose = HandlePurpose.CONTRIBUTION) -> str:
    return f"fph:{purpose!s}:{uuid4()}"


def _evidence(scope: OrganizationalScopeRef) -> tuple[EvidenceReference, ...]:
    return (EvidenceReference(kind=EvidenceKind.RECEIPT, external_reference="doc-1", scope=scope),)


def _act(
    scope: OrganizationalScopeRef,
    *,
    actor: str = "actor-admin",
    conflict: ConflictDeclaration | None = _NO_CONFLICT,
    policy: PolicyBinding | None = None,
) -> GovernedAct:
    return GovernedAct(
        at=_NOW,
        by_authority=_authority(scope, actor=actor),
        reason=_REASON,
        policy=policy,
        conflict=conflict,
    )


def _valuation(scope: OrganizationalScopeRef, *, method: str = "market_price") -> InKindValuation:
    return InKindValuation(
        basis="comparable market price",
        method_reference=method,
        valuation_date=date(2026, 2, 1),
        evidence_reference=_evidence(scope)[0],
        valued_amount=Money(30_000, "EUR"),
    )


#: The default monetary amount of a test receipt, held as a module-level
#: value because a call in a default argument is evaluated once at import.
_DEFAULT_RECEIPT_AMOUNT = Money(50_000, "EUR")


def _receipt(
    *,
    amount: Money | None = _DEFAULT_RECEIPT_AMOUNT,
    contributor: str | None = None,
    in_kind: InKindValuation | None = None,
) -> ContributionReceipt:
    return ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="bank_transfer",
        amount=amount,
        in_kind_valuation=in_kind,
        contributor_handle_reference=_handle_reference() if contributor is None else contributor,
    )


def _contribution(
    scope: OrganizationalScopeRef, *, receipt: ContributionReceipt | None = None
) -> FinanceContribution:
    return FinanceContribution(
        contribution_id=uuid4(),
        scope=scope,
        receipt=_receipt() if receipt is None else receipt,
        retention=_RETENTION,
    )


def _assessment(
    scope: OrganizationalScopeRef,
    *,
    source_determined: bool = True,
    verification_complete: bool = True,
    prohibited: bool = False,
    classification_code: str = "income.donation",
    policy: PolicyBinding | None = _POLICY,
) -> ContributionAssessment:
    return ContributionAssessment(
        assessment_id=uuid4(),
        assessed_at=_NOW,
        assessed_by=_authority(scope, actor="actor-admin"),
        source_determined=source_determined,
        verification_complete=verification_complete,
        prohibited=prohibited,
        classification_code=classification_code,
        policy=policy,
        aggregation_snapshot_digest="digest-1",
    )


def _agreement(
    scope: OrganizationalScopeRef,
    *,
    counter_performance: str | None = "logo placement",
    absent_policy: PolicyBinding | None = None,
) -> SponsorshipAgreement:
    return SponsorshipAgreement(
        agreement_id=uuid4(),
        scope=scope,
        sponsor_handle_reference=_handle_reference(HandlePurpose.SPONSORSHIP),
        benefit_description="conference stand",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        retention=_RETENTION,
        value=Money(200_000, "EUR"),
        counter_performance=counter_performance,
        counter_performance_absent_policy_binding=absent_policy,
    )


def _claim(
    scope: OrganizationalScopeRef, *, claimant: str, state: ExpenseClaimState | None = None
) -> ExpenseClaim:
    return ExpenseClaim(
        claim_id=uuid4(),
        scope=scope,
        claimant_handle_reference=claimant,
        purpose_class="travel",
        amount=Money(12_000, "EUR"),
        retention=_RETENTION,
        evidence=_evidence(scope),
        state=ExpenseClaimState.SUBMITTED if state is None else state,
    )


def _authorization(
    scope: OrganizationalScopeRef,
    *,
    payable_reference: UUID,
    authoriser_actor: str = "actor-authorizer",
    payee: str | None = None,
) -> PaymentAuthorization:
    return PaymentAuthorization(
        authorization_id=uuid4(),
        scope=scope,
        payable_kind="expense_claim",
        payable_reference=payable_reference,
        authorising_authority=_authority(scope, actor=authoriser_actor),
        amount=Money(12_000, "EUR"),
        authorized_at=_NOW,
        reason=_REASON,
        payee_handle_reference=payee,
    )


# =============================================================================
# Contribution intake and the exceptional states (`ФИН-16`)
# =============================================================================


def test_an_anonymous_or_unestablished_contribution_source_refuses() -> None:
    scope = _scope()
    anonymous_receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="cash",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=None,
    )
    unestablished = _contribution(scope, receipt=anonymous_receipt)
    assert unestablished.receipt.contributor_handle_reference is None
    assessed = unestablished.assess(_assessment(scope, source_determined=False), _act(scope))
    assert assessed.state is ContributionState.QUARANTINED
    with pytest.raises(ContributionSourceUndeterminedError) as excinfo:
        assessed.accept(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED"


def test_an_incomplete_verification_refuses_acceptance() -> None:
    scope = _scope()
    contribution = _contribution(scope)
    quarantined = contribution.assess(_assessment(scope, verification_complete=False), _act(scope))
    assert quarantined.state is ContributionState.QUARANTINED
    with pytest.raises(ContributionVerificationIncompleteError) as excinfo:
        quarantined.accept(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE"


def test_a_prohibited_classification_refuses() -> None:
    scope = _scope()
    assessed = _contribution(scope).assess(_assessment(scope, prohibited=True), _act(scope))
    assert assessed.state is ContributionState.ASSESSED
    with pytest.raises(ContributionProhibitedError) as excinfo:
        assessed.accept(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_PROHIBITED"


def test_an_unresolved_classification_refuses_acceptance() -> None:
    scope = _scope()
    quarantined = _contribution(scope).assess(_assessment(scope, policy=None), _act(scope))
    with pytest.raises(ContributionClassificationUndeterminedError) as excinfo:
        quarantined.accept(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_CLASSIFICATION_UNDETERMINED"


def test_a_contribution_never_hops_straight_from_received_to_accepted() -> None:
    scope = _scope()
    with pytest.raises(ContributionClassificationUndeterminedError):
        _contribution(scope).accept(_act(scope))


def test_an_accepted_contribution_must_carry_the_assessment_it_was_accepted_on() -> None:
    scope = _scope()
    with pytest.raises(ContributionClassificationUndeterminedError):
        FinanceContribution(
            contribution_id=uuid4(),
            scope=scope,
            receipt=_receipt(),
            retention=_RETENTION,
            state=ContributionState.ACCEPTED,
        )


def test_acceptance_with_an_open_return_obligation_refuses() -> None:
    scope = _scope()
    assessed = _contribution(scope).assess(_assessment(scope), _act(scope))
    return_required = assessed.require_return(_act(scope))
    with pytest.raises(ContributionReturnRequiredError) as excinfo:
        return_required.accept(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_RETURN_REQUIRED"


def test_acceptance_requires_a_declared_conflict_state() -> None:
    scope = _scope()
    assessed = _contribution(scope).assess(_assessment(scope), _act(scope))
    with pytest.raises(ConflictOfInterestUndeclaredError):
        assessed.accept(_act(scope, conflict=_UNDECLARED))
    with pytest.raises(ConflictOfInterestBlockingError):
        assessed.accept(_act(scope, conflict=_BLOCKING))


def test_an_accepted_contribution_records_the_resolved_assessment() -> None:
    scope = _scope()
    accepted = _contribution(scope).assess(_assessment(scope), _act(scope)).accept(_act(scope))
    assert accepted.state is ContributionState.ACCEPTED
    assert accepted.assessment is not None
    assert accepted.assessment.is_resolved is True
    assert accepted.history[-1].state_after == "accepted"


# =============================================================================
# The create-once receipt (`ФИН-17`, `ФИН-18`)
# =============================================================================


def test_rejection_return_and_escalation_leave_the_receipt_byte_identical() -> None:
    scope = _scope()
    receipt = _receipt()
    contribution = _contribution(scope, receipt=receipt)
    assessed = contribution.assess(_assessment(scope), _act(scope))

    rejected = assessed.reject(_act(scope))
    assert rejected.receipt is receipt
    assert rejected.receipt == receipt

    returned = assessed.require_return(_act(scope)).mark_returned(_act(scope))
    assert returned.state is ContributionState.RETURNED
    assert returned.receipt is receipt

    escalated = assessed.escalate(_act(scope), legal_case_reference="pack-09-case-1")
    assert escalated.state is ContributionState.ESCALATED
    assert escalated.receipt is receipt
    assert escalated.legal_case_reference == "pack-09-case-1"


def test_an_escalation_must_name_the_legal_case_opened_for_it() -> None:
    scope = _scope()
    assessed = _contribution(scope).assess(_assessment(scope), _act(scope))
    with pytest.raises(MonetaryAmountInvalidError):
        assessed.escalate(_act(scope), legal_case_reference="  ")


def test_an_in_kind_contribution_without_a_valuation_basis_refuses() -> None:
    with pytest.raises(InKindValuationMissingError) as excinfo:
        ContributionReceipt(
            receipt_id=uuid4(),
            kind=ContributionKind.OTHER_INCOME,
            received_at=datetime(2026, 2, 10, tzinfo=UTC),
            method="in_kind",
            amount=None,
            in_kind_valuation=None,
        )
    assert excinfo.value.reason_code == "FINANCE_IN_KIND_VALUATION_MISSING"


def test_a_valuation_without_a_method_reference_refuses() -> None:
    scope = _scope()
    with pytest.raises(ValuationMethodMissingError) as excinfo:
        _valuation(scope, method="  ")
    assert excinfo.value.reason_code == "FINANCE_VALUATION_METHOD_MISSING"
    with pytest.raises(ValuationMethodMissingError):
        assert_valuation_method(None)
    assert assert_valuation_method("market_price") == "market_price"


def test_a_valuation_without_a_basis_refuses() -> None:
    scope = _scope()
    with pytest.raises(InKindValuationMissingError):
        InKindValuation(
            basis="   ",
            method_reference="market_price",
            valuation_date=date(2026, 2, 1),
            evidence_reference=_evidence(scope)[0],
        )


def test_a_contributor_appears_only_as_an_opaque_handle_reference() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        _receipt(contributor="Erika Mustermann")
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


# =============================================================================
# Sponsorship (`ФИН-19`)
# =============================================================================


def test_sponsorship_approval_without_counter_performance_or_policy_refuses() -> None:
    scope = _scope()
    agreement = _agreement(scope, counter_performance=None).begin_review(_act(scope))
    with pytest.raises(CounterPerformanceMissingError) as excinfo:
        agreement.approve(_act(scope))
    assert excinfo.value.reason_code == "FINANCE_COUNTER_PERFORMANCE_MISSING"


def test_sponsorship_approval_passes_on_an_explicit_policy_classification_of_none() -> None:
    scope = _scope()
    agreement = _agreement(scope, counter_performance=None, absent_policy=_POLICY)
    approved = agreement.begin_review(_act(scope)).approve(_act(scope))
    assert approved.review_state is SponsorshipState.APPROVED


def test_sponsorship_approval_passes_on_a_described_counter_performance() -> None:
    scope = _scope()
    approved = _agreement(scope).begin_review(_act(scope)).approve(_act(scope))
    assert approved.review_state is SponsorshipState.APPROVED


def test_sponsorship_approval_refuses_an_undeclared_conflict() -> None:
    scope = _scope()
    agreement = _agreement(scope).begin_review(_act(scope))
    with pytest.raises(ConflictOfInterestUndeclaredError):
        agreement.approve(_act(scope, conflict=_UNDECLARED))


def test_a_missing_disclosure_classification_fails_closed() -> None:
    scope = _scope()
    approved = _agreement(scope).begin_review(_act(scope)).approve(_act(scope))
    with pytest.raises(SponsorshipDisclosureIncompleteError) as excinfo:
        approved.classify_disclosure(_act(scope), disclosure_class="  ")
    assert excinfo.value.reason_code == "FINANCE_SPONSORSHIP_DISCLOSURE_INCOMPLETE"


def test_a_sponsorship_agreement_needs_a_value_or_an_in_kind_valuation() -> None:
    scope = _scope()
    with pytest.raises(InKindValuationMissingError):
        SponsorshipAgreement(
            agreement_id=uuid4(),
            scope=scope,
            sponsor_handle_reference=_handle_reference(HandlePurpose.SPONSORSHIP),
            benefit_description="conference stand",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            retention=_RETENTION,
        )


def test_approval_is_reachable_only_out_of_a_recorded_review() -> None:
    scope = _scope()
    with pytest.raises(UnauthorizedStateTransitionError):
        _agreement(scope).approve(_act(scope))


# =============================================================================
# The PACK-35 boundary (`ФИН-20`)
# =============================================================================


def test_a_pack_35_lobbying_subject_refuses() -> None:
    scope = _scope()
    with pytest.raises(UnauthorizedStateTransitionError) as excinfo:
        ExternalFinancialBenefit(
            benefit_id=uuid4(),
            scope=scope,
            benefit_type=ExternalBenefitType.PAID_THIRD_PARTY_SUPPORT,
            retention=_RETENTION,
            subject_kind="meeting",
            value=Money(30_000, "EUR"),
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


@pytest.mark.parametrize("subject_kind", sorted(PACK_35_SUBJECT_KINDS))
def test_every_pack_35_subject_kind_is_refused_as_a_finance_record(subject_kind: str) -> None:
    with pytest.raises(UnauthorizedStateTransitionError):
        assert_not_lobbying_subject(subject_kind)


def test_a_financial_benefit_subject_is_the_one_kind_this_context_records() -> None:
    scope = _scope()
    benefit = ExternalFinancialBenefit(
        benefit_id=uuid4(),
        scope=scope,
        benefit_type=ExternalBenefitType.IN_KIND_CAMPAIGN_SUPPORT,
        retention=_RETENTION,
        value=Money(30_000, "EUR"),
    )
    assert benefit.subject_kind == "financial_benefit"
    valued = benefit.record_valuation(_valuation(scope), _act(scope))
    assessed = valued.assess(_act(scope), outcome="not_a_contribution")
    classified = assessed.classify_disclosure(
        _act(scope), disclosure_class="public", publishable=True
    )
    assert classified.disclosure_class == "public"


def test_an_external_benefit_without_a_valuation_basis_refuses() -> None:
    scope = _scope()
    with pytest.raises(InKindValuationMissingError):
        ExternalFinancialBenefit(
            benefit_id=uuid4(),
            scope=scope,
            benefit_type=ExternalBenefitType.GUARANTEE,
            retention=_RETENTION,
        )


# =============================================================================
# Expense claims and payments (`ФИН-31`)
# =============================================================================


def test_a_claimant_may_not_review_approve_authorise_or_execute_their_own_claim() -> None:
    scope = _scope()
    claimant = _handle_reference(HandlePurpose.EXPENSE_CLAIMANT)
    claim = _claim(scope, claimant=claimant)
    own_act = _act(scope, actor=claimant)

    with pytest.raises(SelfApprovalProhibitedError) as excinfo:
        claim.review(own_act)
    assert excinfo.value.reason_code == "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"

    under_review = claim.review(_act(scope, actor="actor-reviewer"))
    with pytest.raises(SelfApprovalProhibitedError):
        under_review.approve(own_act)

    approved = under_review.approve(_act(scope, actor="actor-approver"))
    self_authorization = _authorization(
        scope, payable_reference=claim.claim_id, authoriser_actor=claimant
    )
    with pytest.raises(SelfApprovalProhibitedError):
        approved.authorize_payment(self_authorization, _act(scope, actor="actor-authorizer"))

    authorization = _authorization(scope, payable_reference=claim.claim_id)
    authorized = approved.authorize_payment(authorization, _act(scope, actor="actor-authorizer"))
    with pytest.raises(SelfApprovalProhibitedError):
        authorized.settle(own_act)


def test_the_self_acting_check_is_blind_to_the_role_the_authority_names() -> None:
    scope = _scope()
    claimant = _handle_reference(HandlePurpose.EXPENSE_CLAIMANT)
    payment_authorizer = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_authorizer",
        scope=scope,
        actor_reference=claimant,
    )
    with pytest.raises(SelfApprovalProhibitedError):
        assert_not_self_acting(claimant, payment_authorizer, action="payment authorization")


def test_the_payment_authorizer_may_not_be_the_executor_of_the_same_payment() -> None:
    scope = _scope()
    authorization = _authorization(scope, payable_reference=uuid4())
    same_authority = authorization.authorising_authority
    with pytest.raises(SelfApprovalProhibitedError) as excinfo:
        authorization.execute(same_authority, at=_NOW)
    assert excinfo.value.reason_code == "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"

    same_actor_other_grant = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_executor",
        scope=scope,
        actor_reference=same_authority.actor_reference,
    )
    with pytest.raises(SelfApprovalProhibitedError):
        authorization.execute(same_actor_other_grant, at=_NOW)


def test_a_distinct_executor_may_execute_an_authorization_exactly_once() -> None:
    scope = _scope()
    authorization = _authorization(scope, payable_reference=uuid4())
    executor = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_executor",
        scope=scope,
        actor_reference="actor-executor",
    )
    executed = authorization.execute(executor, at=_NOW)
    assert executed.state is PaymentAuthorizationState.EXECUTED
    assert executed.executed_by is executor
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        executed.execute(executor, at=_NOW)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        executed.revoke(_act(scope))


def test_a_revoked_authorization_can_never_be_executed() -> None:
    scope = _scope()
    revoked = _authorization(scope, payable_reference=uuid4()).revoke(_act(scope))
    executor = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_executor",
        scope=scope,
        actor_reference="actor-executor",
    )
    with pytest.raises(UnauthorizedStateTransitionError):
        revoked.execute(executor, at=_NOW)


def test_settlement_without_a_bound_authorization_refuses() -> None:
    scope = _scope()
    claimant = _handle_reference(HandlePurpose.EXPENSE_CLAIMANT)
    approved = _claim(scope, claimant=claimant, state=ExpenseClaimState.PAYMENT_AUTHORIZED)
    with pytest.raises(PaymentAuthorizationMissingError) as excinfo:
        approved.settle(_act(scope, actor="actor-executor"))
    assert excinfo.value.reason_code == "FINANCE_PAYMENT_AUTHORIZATION_MISSING"


def test_an_authorization_for_another_payable_cannot_be_bound_to_this_claim() -> None:
    scope = _scope()
    claimant = _handle_reference(HandlePurpose.EXPENSE_CLAIMANT)
    approved = _claim(scope, claimant=claimant, state=ExpenseClaimState.APPROVED)
    foreign = _authorization(scope, payable_reference=uuid4())
    with pytest.raises(PaymentAuthorizationMissingError):
        approved.authorize_payment(foreign, _act(scope, actor="actor-authorizer"))


def test_an_already_executed_authorization_cannot_be_bound_to_a_claim() -> None:
    scope = _scope()
    claimant = _handle_reference(HandlePurpose.EXPENSE_CLAIMANT)
    approved = _claim(scope, claimant=claimant, state=ExpenseClaimState.APPROVED)
    executor = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_executor",
        scope=scope,
        actor_reference="actor-executor",
    )
    executed = _authorization(scope, payable_reference=approved.claim_id).execute(executor, at=_NOW)
    with pytest.raises(PaymentAuthorizationMissingError):
        approved.authorize_payment(executed, _act(scope, actor="actor-authorizer"))


def test_a_claimant_appears_only_as_an_opaque_handle_reference() -> None:
    scope = _scope()
    with pytest.raises(ForbiddenIdentityLinkageError):
        _claim(scope, claimant="member-42")


def test_a_reimbursement_is_a_create_once_payout_record() -> None:
    scope = _scope()
    executor = AuthorityReference(
        authority_id=uuid4(),
        role_code="payment_executor",
        scope=scope,
        actor_reference="actor-executor",
    )
    reimbursement = Reimbursement(
        reimbursement_id=uuid4(),
        scope=scope,
        claim_id=uuid4(),
        authorization_id=uuid4(),
        amount=Money(12_000, "EUR"),
        settled_at=_NOW,
        executed_by=executor,
    )
    assert not [name for name in dir(reimbursement) if name in {"amend", "update", "delete"}]


# =============================================================================
# Obligations, valuation and write-off
# =============================================================================


def test_a_write_off_requires_both_a_named_authority_and_a_recorded_reason() -> None:
    scope = _scope()
    obligation = FinancialObligation.record(
        _act(scope),
        obligation_id=uuid4(),
        scope=scope,
        obligation_type=ObligationType.PAYABLE,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
    )
    with pytest.raises(WriteOffNotAuthorizedError) as excinfo:
        obligation.write_off(at=_NOW, by_authority=None, reason=_REASON)
    assert excinfo.value.reason_code == "FINANCE_WRITE_OFF_NOT_AUTHORIZED"
    with pytest.raises(WriteOffNotAuthorizedError):
        obligation.write_off(
            at=_NOW, by_authority=_authority(scope, actor="actor-admin"), reason=None
        )
    written_off = obligation.write_off(
        at=_NOW, by_authority=_authority(scope, actor="actor-admin"), reason=_REASON
    )
    assert written_off.state is PositionState.WRITTEN_OFF


def test_a_settled_obligation_is_terminal_and_refuses_a_further_change() -> None:
    scope = _scope()
    obligation = FinancialObligation.record(
        _act(scope),
        obligation_id=uuid4(),
        scope=scope,
        obligation_type=ObligationType.PAYABLE,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
    )
    authorization = _authorization(scope, payable_reference=obligation.obligation_id)
    settled = obligation.settle(_act(scope), authorization=authorization)
    assert settled.state is PositionState.SETTLED
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        settled.write_off(
            at=_NOW, by_authority=_authority(scope, actor="actor-admin"), reason=_REASON
        )


def test_settling_an_obligation_without_an_authorization_refuses() -> None:
    scope = _scope()
    obligation = FinancialObligation.record(
        _act(scope),
        obligation_id=uuid4(),
        scope=scope,
        obligation_type=ObligationType.RECEIVABLE,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
    )
    with pytest.raises(PaymentAuthorizationMissingError):
        obligation.settle(_act(scope), authorization=None)


def test_a_revaluation_without_a_method_reference_refuses() -> None:
    scope = _scope()
    obligation = FinancialObligation.record(
        _act(scope),
        obligation_id=uuid4(),
        scope=scope,
        obligation_type=ObligationType.LOAN,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
    )
    with pytest.raises(ValuationMethodMissingError):
        obligation.revalue(
            _act(scope),
            amount=Money(6_000, "EUR"),
            valuation_date=date(2026, 4, 1),
            method_reference=None,
        )


# =============================================================================
# Governed transfers (`ФИН-37`)
# =============================================================================


def test_a_governed_transfer_needs_two_legs_in_two_different_scopes() -> None:
    here, elsewhere = _scope(), _scope()
    outgoing = TransferLeg(
        leg_id=uuid4(),
        scope=here,
        direction=TransferDirection.OUTGOING,
        amount=Money(5_000, "EUR"),
    )
    incoming = TransferLeg(
        leg_id=uuid4(),
        scope=elsewhere,
        direction=TransferDirection.INCOMING,
        amount=Money(5_000, "EUR"),
    )
    assert assert_transfer_pair_resolvable((outgoing, incoming)) == (outgoing, incoming)
    with pytest.raises(TransferPairUnresolvedError) as excinfo:
        assert_transfer_pair_resolvable((outgoing,))
    assert excinfo.value.reason_code == "FINANCE_TRANSFER_PAIR_UNRESOLVED"


def test_a_transfer_inside_one_scope_is_not_a_transfer() -> None:
    here = _scope()
    first = TransferLeg(
        leg_id=uuid4(),
        scope=here,
        direction=TransferDirection.OUTGOING,
        amount=Money(5_000, "EUR"),
    )
    second = TransferLeg(
        leg_id=uuid4(),
        scope=here,
        direction=TransferDirection.INCOMING,
        amount=Money(5_000, "EUR"),
    )
    with pytest.raises(TransferPairUnresolvedError):
        assert_transfer_pair_resolvable((first, second))


def test_a_transfer_that_changes_value_in_flight_is_two_facts_not_one() -> None:
    here, elsewhere = _scope(), _scope()
    outgoing = TransferLeg(
        leg_id=uuid4(),
        scope=here,
        direction=TransferDirection.OUTGOING,
        amount=Money(5_000, "EUR"),
    )
    incoming = TransferLeg(
        leg_id=uuid4(),
        scope=elsewhere,
        direction=TransferDirection.INCOMING,
        amount=Money(4_000, "EUR"),
    )
    with pytest.raises(TransferPairUnresolvedError):
        assert_transfer_pair_resolvable((outgoing, incoming))

"""Tests for `epd2_finance_service.events` - the seventy-two canonical
section-20.17 event types, the envelope version, the identity-key backstop
and the completeness of the Audit Core state payloads.

The state-payload tests assert against `dataclasses.fields`, not against a
hand-written list: PACK-07 found a "full state" snapshot that silently
omitted three fields, which left them outside the tamper-evidence hash.
A field added to any aggregate in future therefore fails a test here until
its serialiser is updated.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from epd2_core.event_envelope import ActorRef, EventEnvelope
from epd2_finance_service import events
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    EvidenceKind,
    EvidenceReference,
    FinancePartyHandle,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    ReportingPeriodRef,
    RetentionBinding,
    reject_identity_payload_keys,
)
from epd2_finance_service.events import (
    EVENT_VERSION,
    FINANCE_EVENT_AGGREGATES,
    FINANCE_EVENT_TYPES,
    PUBLIC_PROJECTION_ALLOWED,
    SUPPORTED_MAJOR_VERSIONS,
    UnknownFinanceEventTypeError,
    accounting_period_state_payload,
    audit_engagement_state_payload,
    build_finance_event,
    expense_claim_state_payload,
    external_benefit_state_payload,
    finance_account_state_payload,
    finance_contribution_state_payload,
    financial_asset_state_payload,
    financial_obligation_state_payload,
    financial_transaction_state_payload,
    journal_entry_state_payload,
    payment_authorization_state_payload,
    perimeter_definition_state_payload,
    report_snapshot_state_payload,
    report_version_state_payload,
    reporting_obligation_state_payload,
    sponsorship_state_payload,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    ForbiddenIdentityLinkageError,
)
from epd2_finance_service.ledger import (
    AccountingPeriod,
    FinanceAccount,
    FinancialTransaction,
    JournalEntry,
    PostingLine,
    PostingSide,
    post,
)
from epd2_finance_service.records import (
    ContributionKind,
    ContributionReceipt,
    ExpenseClaim,
    ExternalBenefitType,
    ExternalFinancialBenefit,
    FinanceContribution,
    FinancialAsset,
    FinancialObligation,
    GovernedAct,
    InKindValuation,
    ObligationType,
    PaymentAuthorization,
    SponsorshipAgreement,
)
from epd2_finance_service.reporting import (
    ApprovalRecord,
    AuditConclusion,
    AuditEngagement,
    AuditFinding,
    AuditOpinionReference,
    CorrectionKind,
    CorrectionRequest,
    ExternalAcceptanceReference,
    ExternalStatusKind,
    ExternalSubmissionReference,
    FinanceReportVersion,
    PublicationAuthorization,
    PublicationReference,
    ReportingObligation,
    ReportingObligationKind,
    ReportingPerimeterDefinition,
    ReportSnapshot,
    ReviewOutcome,
    ReviewRecord,
    SignatureRecord,
    freeze_perimeter,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_SCOPE = OrganizationalScopeRef(organization_id=uuid4())
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=_NOW)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)
_NO_CONFLICT = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board")
_ACTOR = ActorRef(actor_id=uuid4(), actor_type="organizational_authority")

#: The count canon 20.17 fixes. Written as a literal so a seventy-third
#: name cannot arrive unnoticed.
CANON_EVENT_TYPE_COUNT = 72


def _authority(*, actor: str, role_code: str = "finance_administrator") -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(), role_code=role_code, scope=_SCOPE, actor_reference=actor
    )


def _act(*, actor: str = "actor-admin") -> GovernedAct:
    return GovernedAct(
        at=_NOW,
        by_authority=_authority(actor=actor),
        reason=_REASON,
        policy=_POLICY,
        conflict=_NO_CONFLICT,
    )


def _period_ref() -> ReportingPeriodRef:
    return ReportingPeriodRef(period_id=uuid4(), label="2026", scope=_SCOPE)


def _evidence() -> tuple[EvidenceReference, ...]:
    return (EvidenceReference(kind=EvidenceKind.RECEIPT, external_reference="doc-1", scope=_SCOPE),)


def _handle(purpose: HandlePurpose = HandlePurpose.CONTRIBUTION) -> FinancePartyHandle:
    return FinancePartyHandle(handle_id=uuid4(), purpose=purpose, perimeter=_SCOPE)


def _valuation() -> InKindValuation:
    return InKindValuation(
        basis="comparable market price",
        method_reference="market_price",
        valuation_date=date(2026, 2, 1),
        evidence_reference=_evidence()[0],
        valued_amount=Money(30_000, "EUR"),
    )


# =============================================================================
# One instance of every aggregate that has a state payload
# =============================================================================


def _account() -> FinanceAccount:
    account = FinanceAccount(
        account_id=uuid4(),
        code="1000",
        classification_code="asset",
        scope=_SCOPE,
        retention=_RETENTION,
    )
    return account.activate(
        at=_NOW, by_authority=_authority(actor="actor-admin"), reason=_REASON
    ).mark_first_posting()


def _period() -> AccountingPeriod:
    return AccountingPeriod(
        period_id=uuid4(),
        label="2026",
        scope=_SCOPE,
        timezone_name="Europe/Berlin",
        opens_at=datetime(2026, 1, 1, tzinfo=UTC),
        closes_at=datetime(2027, 1, 1, tzinfo=UTC),
    )


def _lines() -> tuple[PostingLine, ...]:
    return (
        PostingLine(
            account_id=uuid4(),
            side=PostingSide.DEBIT,
            amount=Money(10_000, "EUR"),
            dimension_references=("cost-centre-1",),
            memo_reference="memo-1",
        ),
        PostingLine(account_id=uuid4(), side=PostingSide.CREDIT, amount=Money(10_000, "EUR")),
    )


def _entry() -> JournalEntry:
    period = _period()
    draft = JournalEntry(
        entry_id=uuid4(),
        scope=_SCOPE,
        period=period.as_reference(),
        lines=_lines(),
        reason=_REASON,
        transaction_id=uuid4(),
        evidence=_evidence(),
    )
    return post(draft, 1, period=period)


def _transaction() -> FinancialTransaction:
    provenance = Provenance(
        kind=ProvenanceKind.IMPORTED,
        source_system_reference="bank-feed",
        recorded_by_authority="treasury",
        import_batch_reference="fp-2026-03",
        external_reference="stmt-1",
    )
    recorded = FinancialTransaction(
        transaction_id=uuid4(),
        scope=_SCOPE,
        provenance=provenance,
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        recorded_at=_NOW,
        reporting_period=_period_ref(),
        value_date=date(2026, 2, 3),
        party_handle_reference=_handle().as_reference(),
        evidence=_evidence(),
        internal_transfer_reference="transfer-1",
    )
    return recorded.classify(
        classification_code="income.donation", policy=_POLICY, expected_version=1
    )


def _contribution() -> FinanceContribution:
    receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="bank_transfer",
        amount=Money(50_000, "EUR"),
        in_kind_valuation=None,
        contributor_handle_reference=_handle().as_reference(),
        evidence=_evidence(),
    )
    contribution = FinanceContribution(
        contribution_id=uuid4(), scope=_SCOPE, receipt=receipt, retention=_RETENTION
    )
    quarantined = contribution.quarantine(_act())
    return quarantined.escalate(_act(), legal_case_reference="pack-09-case-1")


def _agreement() -> SponsorshipAgreement:
    agreement = SponsorshipAgreement(
        agreement_id=uuid4(),
        scope=_SCOPE,
        sponsor_handle_reference=_handle(HandlePurpose.SPONSORSHIP).as_reference(),
        benefit_description="conference stand",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        retention=_RETENTION,
        value=Money(200_000, "EUR"),
        in_kind_valuation=_valuation(),
        counter_performance="logo placement",
        counter_performance_absent_policy_binding=_POLICY,
        linked_activity_reference="pack-35-contact-1",
        conflict_reference="conflict-1",
        evidence=_evidence(),
    )
    reviewed = agreement.begin_review(_act())
    approved = reviewed.approve(_act())
    return approved.classify_disclosure(_act(), disclosure_class="public")


def _benefit() -> ExternalFinancialBenefit:
    benefit = ExternalFinancialBenefit(
        benefit_id=uuid4(),
        scope=_SCOPE,
        benefit_type=ExternalBenefitType.PAID_THIRD_PARTY_SUPPORT,
        retention=_RETENTION,
        value=Money(30_000, "EUR"),
        provider_handle_reference=_handle(HandlePurpose.EXTERNAL_INFLUENCE).as_reference(),
        evidence=_evidence(),
    )
    valued = benefit.record_valuation(_valuation(), _act())
    assessed = valued.assess(_act(), outcome="not_a_contribution")
    return assessed.classify_disclosure(_act(), disclosure_class="public", publishable=True)


def _claim() -> ExpenseClaim:
    claim = ExpenseClaim(
        claim_id=uuid4(),
        scope=_SCOPE,
        claimant_handle_reference=_handle(HandlePurpose.EXPENSE_CLAIMANT).as_reference(),
        purpose_class="travel",
        amount=Money(12_000, "EUR"),
        retention=_RETENTION,
        evidence=_evidence(),
        corrects_claim_id=uuid4(),
    )
    reviewed = claim.review(_act(actor="actor-reviewer"))
    return reviewed.approve(_act(actor="actor-approver"))


def _authorization() -> PaymentAuthorization:
    authorization = PaymentAuthorization(
        authorization_id=uuid4(),
        scope=_SCOPE,
        payable_kind="expense_claim",
        payable_reference=uuid4(),
        authorising_authority=_authority(actor="actor-authorizer", role_code="payment_authorizer"),
        amount=Money(12_000, "EUR"),
        authorized_at=_NOW,
        reason=_REASON,
        payee_handle_reference=_handle(HandlePurpose.EXPENSE_CLAIMANT).as_reference(),
        evidence=_evidence(),
    )
    executor = _authority(actor="actor-executor", role_code="payment_executor")
    return authorization.execute(executor, at=_NOW)


def _asset() -> FinancialAsset:
    asset = FinancialAsset(
        asset_id=uuid4(),
        scope=_SCOPE,
        asset_class="office_equipment",
        valuation=Money(80_000, "EUR"),
        valuation_date=date(2026, 1, 15),
        method_reference="historic_cost",
        retention=_RETENTION,
        asset_reference="inventory-1",
        legal_case_reference="pack-09-case-2",
        evidence=_evidence(),
    )
    return asset.revalue(
        _act(),
        valuation=Money(70_000, "EUR"),
        valuation_date=date(2026, 3, 1),
        method_reference="market_price",
    )


def _obligation() -> FinancialObligation:
    obligation = FinancialObligation.record(
        _act(),
        obligation_id=uuid4(),
        scope=_SCOPE,
        obligation_type=ObligationType.PAYABLE,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
        counterparty_handle_reference=_handle(HandlePurpose.OBLIGATION_COUNTERPARTY).as_reference(),
        evidence=_evidence(),
    )
    return obligation.write_off(
        at=_NOW,
        by_authority=_authority(actor="actor-admin"),
        reason=_REASON,
        legal_case_reference="pack-09-case-3",
    )


def _reporting_obligation() -> ReportingObligation:
    obligation = ReportingObligation(
        obligation_id=uuid4(),
        scope=_SCOPE,
        period=_period_ref(),
        obligation_kind=ReportingObligationKind.STATUTORY_ANNUAL_REPORT,
        statutory_deadline_reference="pack-09-deadline-1",
    )
    return obligation.activate(_act()).fulfil(_act(), submission_reference="submission-1")


def _perimeter_definition() -> ReportingPerimeterDefinition:
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=_SCOPE,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(_SCOPE,),
        effective_until=date(2027, 1, 1),
    )
    return definition.activate(_act())


def _snapshot(period: ReportingPeriodRef | None = None) -> ReportSnapshot:
    return ReportSnapshot.freeze(
        snapshot_id=uuid4(),
        scope=_SCOPE,
        period=_period_ref() if period is None else period,
        perimeter=freeze_perimeter(_perimeter_definition(), _NOW),
        frozen_at=_NOW,
        policy_bindings=(_POLICY,),
        included_transaction_ids=(uuid4(),),
        included_entry_ids=(uuid4(), uuid4()),
    )


def _report_version() -> tuple[FinanceReportVersion, PublicationReference]:
    """A fully-walked report version plus its publication record.

    Every optional field on `FinanceReportVersion` is populated, so the
    state-payload completeness test sees a real value in each rather than
    a `None` that would hide a missing key."""
    period = _period_ref()
    snapshot = _snapshot(period)
    version = FinanceReportVersion(
        version_id=uuid4(), report_id=uuid4(), scope=_SCOPE, period=period, version=1
    )
    version = version.prepare(snapshot, _act(actor="actor-preparer"))
    version = version.record_correction_request(
        CorrectionRequest(
            request_id=uuid4(),
            requested_at=_NOW,
            requested_by=_authority(actor="actor-reviewer"),
            reason=_REASON,
            finding_references=("finding-1",),
        ),
        _act(actor="actor-reviewer"),
    )
    version = version.record_review(
        ReviewRecord(
            review_id=uuid4(),
            reviewed_at=_NOW,
            reviewer=_authority(actor="actor-reviewer"),
            outcome=ReviewOutcome.COMPLETE,
            finding_references=("finding-1",),
        ),
        _act(actor="actor-reviewer"),
    )
    version = version.complete_internal_review(_act(actor="actor-reviewer"))
    version = version.record_auditor_review(
        AuditOpinionReference(
            engagement_id=uuid4(),
            conclusion_reference="conclusion-1",
            auditor=_authority(actor="actor-auditor", role_code="finance_auditor"),
            recorded_at=_NOW,
        ),
        _act(actor="actor-reviewer"),
    )
    version = version.approve(
        ApprovalRecord(
            approval_id=uuid4(),
            approved_at=_NOW,
            approved_by=_authority(actor="actor-approver"),
            reason=_REASON,
            policy=_POLICY,
        ),
        _act(actor="actor-approver"),
    )
    version = version.sign(
        SignatureRecord(
            signature_id=uuid4(),
            signed_at=_NOW,
            signed_by=_authority(actor="actor-signatory", role_code="report_signatory"),
            reason=_REASON,
            policy=_POLICY,
        ),
        _act(actor="actor-signatory"),
    )
    version = version.record_submission(
        ExternalSubmissionReference(
            submission_reference="submission-1",
            recipient_reference="bundestagsverwaltung",
            submitted_at=_NOW,
        ),
        _act(actor="actor-signatory"),
    )
    version = version.record_external_acknowledgement(
        ExternalAcceptanceReference(
            notice_effect_reference="ack-1",
            kind=ExternalStatusKind.ACKNOWLEDGEMENT,
            decided_at=_NOW,
            deciding_authority_reference="recipient-desk",
        ),
        _act(actor="actor-signatory"),
    )
    version = version.record_external_acceptance(
        ExternalAcceptanceReference(
            notice_effect_reference="notice-effect-1",
            kind=ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION,
            decided_at=_NOW,
            deciding_authority_reference="recipient-desk",
        ),
        _act(actor="actor-signatory"),
    )
    authorization = PublicationAuthorization(
        authorization_id=uuid4(),
        scope=_SCOPE,
        authorized_by=_authority(actor="actor-orgadmin"),
        authorized_at=_NOW,
        reason=_REASON,
        policy=_POLICY,
    )
    reference = PublicationReference(
        publication_reference="publication-1",
        authorization_id=authorization.authorization_id,
        published_at=_NOW,
    )
    version = version.publish(
        reference, _act(actor="actor-signatory"), publication_authorization=authorization
    )
    superseded, successor = version.create_successor_version(
        _act(actor="actor-preparer"),
        version_id=uuid4(),
        correction_kind=CorrectionKind.RESTATEMENT,
    )
    assert successor.restatement_of_version_reference == version.version_id
    return superseded, reference


def _engagement() -> AuditEngagement:
    auditor = _authority(actor="actor-auditor", role_code="finance_auditor")
    engagement = AuditEngagement.open(
        _act(),
        engagement_id=uuid4(),
        scope=_SCOPE,
        period=_period_ref(),
        auditor=auditor,
    )
    with_finding = engagement.record_finding(
        AuditFinding(
            finding_id=uuid4(),
            recorded_at=_NOW,
            recorded_by=auditor,
            severity="minor",
            summary_reference="finding-ref-1",
            evidence=_evidence(),
        ),
        _act(actor="actor-auditor"),
    )
    return with_finding.conclude(
        AuditConclusion(
            conclusion_id=uuid4(),
            concluded_at=_NOW,
            concluded_by=auditor,
            conclusion_class="unqualified",
            reason=_REASON,
            evidence=_evidence(),
        ),
        _act(actor="actor-auditor"),
    )


# =============================================================================
# The state-payload completeness table
# =============================================================================

#: Where a state payload spells an aggregate field under a different key.
#: `FinanceAccount.account_id` cannot travel as `account_id`, because that
#: key is in `domain.PROHIBITED_IDENTITY_KEYS` (a PACK-02 platform user
#: account), so it serialises as `finance_account_id` (`ФИН-02`).
_FIELD_RENAMES: dict[str, dict[str, str]] = {
    "FinanceAccount": {"account_id": "finance_account_id"},
    "AccountingPeriod": {},
    "JournalEntry": {
        "entry_id": "journal_entry_id",
        "transaction_id": "financial_transaction_id",
    },
    "FinancialTransaction": {"transaction_id": "financial_transaction_id"},
    "FinanceContribution": {"contribution_id": "finance_contribution_id"},
    "SponsorshipAgreement": {"agreement_id": "sponsorship_agreement_id"},
    "ExternalFinancialBenefit": {"benefit_id": "external_financial_benefit_id"},
    "ExpenseClaim": {"claim_id": "expense_claim_id"},
    "PaymentAuthorization": {"authorization_id": "payment_authorization_id"},
    "FinancialAsset": {"asset_id": "financial_asset_id"},
    "FinancialObligation": {"obligation_id": "financial_obligation_id"},
    "ReportingObligation": {"obligation_id": "reporting_obligation_id"},
    "ReportingPerimeterDefinition": {
        "definition_id": "perimeter_definition_id",
        "version": "definition_version",
    },
    "ReportSnapshot": {"snapshot_id": "report_snapshot_id"},
    "FinanceReportVersion": {
        "version_id": "report_version_id",
        "snapshot_id": "report_snapshot_id",
    },
    "AuditEngagement": {"engagement_id": "audit_engagement_id"},
}


def _state_payload_cases() -> list[tuple[str, object, Mapping[str, object]]]:
    """One `(aggregate name, instance, state payload)` triple per payload."""
    version, _ = _report_version()
    return [
        ("FinanceAccount", _account(), finance_account_state_payload(_account())),
        ("AccountingPeriod", _period(), accounting_period_state_payload(_period())),
        ("JournalEntry", _entry(), journal_entry_state_payload(_entry())),
        (
            "FinancialTransaction",
            _transaction(),
            financial_transaction_state_payload(_transaction()),
        ),
        (
            "FinanceContribution",
            _contribution(),
            finance_contribution_state_payload(_contribution()),
        ),
        ("SponsorshipAgreement", _agreement(), sponsorship_state_payload(_agreement())),
        ("ExternalFinancialBenefit", _benefit(), external_benefit_state_payload(_benefit())),
        ("ExpenseClaim", _claim(), expense_claim_state_payload(_claim())),
        (
            "PaymentAuthorization",
            _authorization(),
            payment_authorization_state_payload(_authorization()),
        ),
        ("FinancialAsset", _asset(), financial_asset_state_payload(_asset())),
        ("FinancialObligation", _obligation(), financial_obligation_state_payload(_obligation())),
        (
            "ReportingObligation",
            _reporting_obligation(),
            reporting_obligation_state_payload(_reporting_obligation()),
        ),
        (
            "ReportingPerimeterDefinition",
            _perimeter_definition(),
            perimeter_definition_state_payload(_perimeter_definition()),
        ),
        ("ReportSnapshot", _snapshot(), report_snapshot_state_payload(_snapshot())),
        ("FinanceReportVersion", version, report_version_state_payload(version)),
        ("AuditEngagement", _engagement(), audit_engagement_state_payload(_engagement())),
    ]


STATE_PAYLOAD_CASES: list[tuple[str, object, Mapping[str, object]]] = _state_payload_cases()


# =============================================================================
# The seventy-two canonical event types (canon 20.17)
# =============================================================================


def test_there_are_exactly_seventy_two_canonical_event_types() -> None:
    assert len(FINANCE_EVENT_TYPES) == CANON_EVENT_TYPE_COUNT
    assert len(set(FINANCE_EVENT_TYPES)) == CANON_EVENT_TYPE_COUNT


def test_every_canonical_event_type_carries_a_canon_aggregate_prefix() -> None:
    assert set(FINANCE_EVENT_AGGREGATES) == set(FINANCE_EVENT_TYPES)
    for event_type in FINANCE_EVENT_TYPES:
        assert "." in event_type
        assert not event_type.startswith("finance.")
        assert FINANCE_EVENT_AGGREGATES[event_type]


def test_every_canonical_event_type_has_a_named_builder() -> None:
    missing = [
        event_type
        for event_type in FINANCE_EVENT_TYPES
        if not callable(getattr(events, f"build_{event_type.replace('.', '_')}_event", None))
    ]
    assert missing == []


def test_an_event_type_outside_the_canon_list_is_refused_first() -> None:
    with pytest.raises(UnknownFinanceEventTypeError):
        build_finance_event(
            event_id=uuid4(),
            event_type="finance_account.invented",
            subject_type="finance_account",
            subject_id=uuid4(),
            scope=_SCOPE,
            payload={},
            actor=_ACTOR,
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_NOW,
        )


@pytest.mark.parametrize("event_type", FINANCE_EVENT_TYPES)
def test_every_canonical_event_builds_an_envelope_whose_version_major_is_supported(
    event_type: str,
) -> None:
    envelope = build_finance_event(
        event_id=uuid4(),
        event_type=event_type,
        subject_type=event_type.split(".", 1)[0],
        subject_id=uuid4(),
        scope=_SCOPE,
        payload={"reason_code": _REASON.reason_code},
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    assert envelope.event_type == event_type
    assert int(envelope.event_version.split(".", 1)[0]) in SUPPORTED_MAJOR_VERSIONS


def test_the_declared_event_version_major_is_itself_supported() -> None:
    assert int(EVENT_VERSION.split(".", 1)[0]) in SUPPORTED_MAJOR_VERSIONS


def test_every_envelope_carries_the_mandatory_safe_metadata() -> None:
    envelope = build_finance_event(
        event_id=uuid4(),
        event_type="finance_account.created",
        subject_type="finance_account",
        subject_id=uuid4(),
        scope=_SCOPE,
        payload={"organization_scope": "a-lie", "aggregate_id": "another-lie"},
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    assert envelope.payload["organization_scope"] == str(_SCOPE.organization_id)
    assert envelope.payload["scope_kind"] == _SCOPE.scope_kind
    assert envelope.payload["aggregate_id"] == str(envelope.subject.subject_id)


def test_a_naive_occurred_at_is_refused_with_a_governed_reason_code() -> None:
    with pytest.raises(AccountingPeriodUndeterminedError) as excinfo:
        build_finance_event(
            event_id=uuid4(),
            event_type="finance_account.created",
            subject_type="finance_account",
            subject_id=uuid4(),
            scope=_SCOPE,
            payload={},
            actor=_ACTOR,
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=datetime(2026, 3, 1, 12, 0),
        )
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED"


# =============================================================================
# The identity backstop (`ФИН-02`)
# =============================================================================


def test_an_event_payload_carrying_a_prohibited_identity_key_is_refused() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        build_finance_event(
            event_id=uuid4(),
            event_type="finance_contribution.received",
            subject_type="finance_contribution",
            subject_id=uuid4(),
            scope=_SCOPE,
            payload={"member_id": "m-1"},
            actor=_ACTOR,
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_NOW,
        )
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_a_prohibited_identity_key_nested_in_an_event_payload_is_refused_too() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        build_finance_event(
            event_id=uuid4(),
            event_type="finance_contribution.received",
            subject_type="finance_contribution",
            subject_id=uuid4(),
            scope=_SCOPE,
            payload={"contributor": [{"details": {"iban": "DE00"}}]},
            actor=_ACTOR,
            correlation_id=uuid4(),
            causation_id=None,
            occurred_at=_NOW,
        )


def test_the_acting_authority_travels_without_the_actor_behind_it() -> None:
    account = _account()
    envelope = events.build_finance_account_status_changed_event(
        event_id=uuid4(),
        account=account,
        authority=_authority(actor="actor-admin"),
        reason=_REASON,
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    authority_payload = envelope.payload["acting_authority"]
    assert isinstance(authority_payload, dict)
    assert "actor_reference" not in authority_payload
    assert "actor-admin" not in str(envelope.payload)


# =============================================================================
# The handle-resolution event (canon 19f.15, canon 20.17)
# =============================================================================


def test_the_handle_resolution_event_does_not_carry_the_resolved_value() -> None:
    handle = _handle()
    envelope = events.build_finance_party_handle_resolved_event(
        event_id=uuid4(),
        handle=handle,
        resolving_authority=_authority(
            actor="actor-resolver", role_code="finance_party_handle_resolver"
        ),
        reason=_REASON,
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    assert envelope.event_type == "finance_party_handle.resolved"
    assert envelope.payload["resolved_value_disclosed"] is False
    assert envelope.payload["party_handle_reference"] == handle.as_reference()
    reject_identity_payload_keys(dict(envelope.payload), context="resolution event")


def test_the_resolution_builder_takes_no_parameter_that_could_carry_an_identity() -> None:
    parameters = set(
        events.build_finance_party_handle_resolved_event.__code__.co_varnames[
            : events.build_finance_party_handle_resolved_event.__code__.co_argcount
            + events.build_finance_party_handle_resolved_event.__code__.co_kwonlyargcount
        ]
    )
    assert parameters == {
        "event_id",
        "handle",
        "resolving_authority",
        "reason",
        "actor",
        "correlation_id",
        "causation_id",
        "occurred_at",
    }


def test_no_party_handle_event_is_publicly_projectable() -> None:
    handle_events = {
        event_type
        for event_type in FINANCE_EVENT_TYPES
        if event_type.startswith("finance_party_handle.")
    }
    assert len(handle_events) == 3
    assert not handle_events & PUBLIC_PROJECTION_ALLOWED


def test_no_individual_register_event_is_publicly_projectable() -> None:
    register_prefixes = (
        "finance_account.",
        "accounting_period.",
        "journal_entry.",
        "financial_transaction.",
        "reconciliation.",
        "import_batch.",
    )
    for event_type in FINANCE_EVENT_TYPES:
        if event_type.startswith(register_prefixes):
            assert event_type not in PUBLIC_PROJECTION_ALLOWED


# =============================================================================
# Audit state payloads cover every field of their aggregate
# =============================================================================


@pytest.mark.parametrize(
    ("name", "instance", "payload"),
    STATE_PAYLOAD_CASES,
    ids=[case[0] for case in STATE_PAYLOAD_CASES],
)
def test_every_audit_state_payload_covers_every_field_of_its_aggregate(
    name: str, instance: object, payload: Mapping[str, object]
) -> None:
    renames = _FIELD_RENAMES[name]
    expected = {renames.get(field.name, field.name) for field in fields(instance)}  # type: ignore[arg-type]
    assert expected <= set(payload), f"{name}: {sorted(expected - set(payload))} not in the payload"


@pytest.mark.parametrize(
    ("name", "instance", "payload"),
    STATE_PAYLOAD_CASES,
    ids=[case[0] for case in STATE_PAYLOAD_CASES],
)
def test_every_audit_state_payload_passes_the_identity_key_rejection(
    name: str, instance: object, payload: Mapping[str, object]
) -> None:
    reject_identity_payload_keys(dict(payload), context=f"state payload {name}")


@pytest.mark.parametrize(
    ("name", "instance", "payload"),
    STATE_PAYLOAD_CASES,
    ids=[case[0] for case in STATE_PAYLOAD_CASES],
)
def test_every_audit_state_payload_is_free_of_floating_point_values(
    name: str, instance: object, payload: Mapping[str, object]
) -> None:
    def walk(node: object) -> None:
        assert not isinstance(node, float), f"{name} carries a float"
        if isinstance(node, Mapping):
            for value in node.values():
                walk(value)
        elif isinstance(node, list | tuple):
            for value in node:
                walk(value)

    walk(payload)


def test_a_state_payload_records_the_history_a_wire_payload_omits() -> None:
    account = _account()
    state = finance_account_state_payload(account)
    envelope = events.build_finance_account_created_event(
        event_id=uuid4(),
        account=account,
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    assert "history" in state
    assert "history" not in envelope.payload
    assert "retention" in state
    assert "retention" not in envelope.payload


# =============================================================================
# A representative pass over the real named builders
# =============================================================================


def _builder_cases() -> list[tuple[str, Callable[[], EventEnvelope]]]:
    """One real named builder per aggregate family, invoked for real.

    The generic-builder test above covers all seventy-two names through the
    one chokepoint every builder routes through; this list exercises the
    named builders themselves, so a builder that assembled its payload by
    hand instead of calling `build_finance_event` would still be checked."""
    correlation_id = uuid4()
    version, publication = _report_version()
    return [
        (
            "finance_account.created",
            lambda: events.build_finance_account_created_event(
                event_id=uuid4(),
                account=_account(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "accounting_period.opened",
            lambda: events.build_accounting_period_opened_event(
                event_id=uuid4(),
                period=_period(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "journal_entry.posted",
            lambda: events.build_journal_entry_posted_event(
                event_id=uuid4(),
                entry=_entry(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "financial_transaction.recorded",
            lambda: events.build_financial_transaction_recorded_event(
                event_id=uuid4(),
                transaction=_transaction(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "finance_contribution.received",
            lambda: events.build_finance_contribution_received_event(
                event_id=uuid4(),
                contribution=_contribution(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "sponsorship.registered",
            lambda: events.build_sponsorship_registered_event(
                event_id=uuid4(),
                agreement=_agreement(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "external_financial_benefit.recorded",
            lambda: events.build_external_financial_benefit_recorded_event(
                event_id=uuid4(),
                benefit=_benefit(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "expense_claim.submitted",
            lambda: events.build_expense_claim_submitted_event(
                event_id=uuid4(),
                claim=_claim(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "payment.authorized",
            lambda: events.build_payment_authorized_event(
                event_id=uuid4(),
                authorization=_authorization(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "financial_asset.recorded",
            lambda: events.build_financial_asset_recorded_event(
                event_id=uuid4(),
                asset=_asset(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "financial_obligation.recorded",
            lambda: events.build_financial_obligation_recorded_event(
                event_id=uuid4(),
                obligation=_obligation(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "reporting_obligation.created",
            lambda: events.build_reporting_obligation_created_event(
                event_id=uuid4(),
                obligation=_reporting_obligation(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "reporting_perimeter.defined",
            lambda: events.build_reporting_perimeter_defined_event(
                event_id=uuid4(),
                definition=_perimeter_definition(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "finance_report.snapshot_frozen",
            lambda: events.build_finance_report_snapshot_frozen_event(
                event_id=uuid4(),
                snapshot=_snapshot(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "finance_report.published",
            lambda: events.build_finance_report_published_event(
                event_id=uuid4(),
                version=version,
                reference=publication,
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
        (
            "finance_audit.opened",
            lambda: events.build_finance_audit_opened_event(
                event_id=uuid4(),
                engagement=_engagement(),
                actor=_ACTOR,
                correlation_id=correlation_id,
                causation_id=None,
                occurred_at=_NOW,
            ),
        ),
    ]


BUILDER_CASES: list[tuple[str, Callable[[], EventEnvelope]]] = _builder_cases()


@pytest.mark.parametrize(
    ("event_type", "builder"), BUILDER_CASES, ids=[case[0] for case in BUILDER_CASES]
)
def test_a_named_builder_produces_a_canonical_envelope_at_a_supported_version(
    event_type: str, builder: Callable[[], EventEnvelope]
) -> None:
    envelope = builder()
    assert envelope.event_type == event_type
    assert int(envelope.event_version.split(".", 1)[0]) in SUPPORTED_MAJOR_VERSIONS
    assert envelope.producer == "finance-service"
    assert envelope.integrity.payload_hash
    reject_identity_payload_keys(dict(envelope.payload), context=event_type)


@pytest.mark.parametrize(
    ("event_type", "builder"), BUILDER_CASES, ids=[case[0] for case in BUILDER_CASES]
)
def test_a_named_builder_never_puts_an_actor_reference_on_the_wire(
    event_type: str, builder: Callable[[], EventEnvelope]
) -> None:
    payload_text = str(builder().payload)
    for actor in ("actor-admin", "actor-approver", "actor-signatory", "actor-auditor"):
        assert actor not in payload_text


def test_the_subject_id_of_a_handle_event_is_the_handle_and_never_a_person() -> None:
    handle = _handle()
    envelope = events.build_finance_party_handle_minted_event(
        event_id=uuid4(),
        handle=handle,
        authority=_authority(actor="actor-admin"),
        actor=_ACTOR,
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=_NOW,
    )
    assert envelope.subject.subject_type == "finance_party_handle"
    assert envelope.subject.subject_id == handle.handle_id
    assert isinstance(envelope.subject.subject_id, UUID)

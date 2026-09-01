"""Application-layer tests for `epd2_finance_service.application`.

Organised around the guarantees the command frame makes, in the order it
makes them: scope, authority, separation of duties, conflict declaration,
idempotency, optimistic concurrency - then the audit append and the
canonical event.

Two module-wide claims are proved here rather than per command. Every
timestamp on every audit row and every published envelope is the injected
`FixedClock`'s value, so no command reads the wall clock; and every
refusal the whole suite relies on carries a `reason_code` registered in
`contracts/reason-codes/pack-10.yml` (`ФИН-40`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import yaml

from epd2_audit_core.storage import InMemoryAuditEventStore
from epd2_core.clock import FixedClock
from epd2_finance_service import application as app
from epd2_finance_service.authorization import (
    FinanceRole,
    assert_authorized,
    assert_conflict_declared,
    assert_not_self_approval,
    assert_roles_compatible,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    EvidenceKind,
    EvidenceReference,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    RequestContext,
    RetentionBinding,
    reject_identity_payload_keys,
    require_timezone,
)
from epd2_finance_service.exceptions import (
    ContributionAggregationUnresolvedError,
    FinanceError,
    FinanceRecordNotFoundError,
    ForbiddenIdentityLinkageError,
    IdempotencyConflictError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    PartyHandleResolutionDeniedError,
    PaymentAuthorizationMissingError,
    PublicationNotAllowedError,
    ReclassificationBypassDeniedError,
    SelfApprovalProhibitedError,
    UnauthorizedStateTransitionError,
    WriteOffNotAuthorizedError,
)
from epd2_finance_service.ledger import (
    AccountStatus,
    PostingLine,
    PostingSide,
)
from epd2_finance_service.projections import assert_no_small_cell_disclosure
from epd2_finance_service.records import (
    ContributionKind,
    ContributionReceipt,
    ContributionState,
    ExternalBenefitType,
    ObligationType,
    SponsorshipAgreement,
)
from epd2_finance_service.references import (
    assert_no_document_content,
    require_retention_binding,
)
from epd2_finance_service.reporting import (
    CorrectionKind,
    ExternalStatusKind,
    GovernedAct,
    PerimeterDefinitionState,
    PublicationAuthorization,
    ReportingPerimeterDefinition,
    ReportState,
    ReviewOutcome,
    delete_report_version,
)
from epd2_finance_service.storage import (
    InMemoryAccountingPeriodStore,
    InMemoryAuditEngagementStore,
    InMemoryCommandIdempotencyStore,
    InMemoryEventSink,
    InMemoryExpenseClaimStore,
    InMemoryExternalFinancialBenefitStore,
    InMemoryFinanceAccountStore,
    InMemoryFinanceContributionStore,
    InMemoryFinancePartyHandleStore,
    InMemoryFinanceReportVersionStore,
    InMemoryFinancialObligationStore,
    InMemoryFinancialTransactionStore,
    InMemoryImportBatchStore,
    InMemoryJournalEntryStore,
    InMemoryPaymentAuthorizationStore,
    InMemoryPerimeterSnapshotStore,
    InMemoryPublicationAuthorizationStore,
    InMemoryReimbursementStore,
    InMemoryReportingPerimeterDefinitionStore,
    InMemoryReportSnapshotStore,
    InMemorySponsorshipAgreementStore,
    delete_finance_record,
)

FIXED = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_OPENS = datetime(2026, 1, 1, tzinfo=UTC)
_CLOSES = datetime(2027, 1, 1, tzinfo=UTC)
_BERLIN = "Europe/Berlin"
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_RETENTION = RetentionBinding(record_class_reference="finance.record.v1", bound_at=FIXED)
_POLICY = PolicyBinding(
    policy_kind="income_classification",
    policy_id="income",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)
_NO_CONFLICT = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board")

#: The registry every governed refusal's `reason_code` must appear in.
REASON_CODE_REGISTRY = (
    Path(__file__).resolve().parents[3] / "contracts" / "reason-codes" / "pack-10.yml"
)


def _registered_reason_codes() -> frozenset[str]:
    raw = yaml.safe_load(REASON_CODE_REGISTRY.read_text(encoding="utf-8"))
    return frozenset(str(entry["code"]) for entry in raw)


REGISTERED_CODES: frozenset[str] = _registered_reason_codes()


# =============================================================================
# One fully wired finance-service instance
# =============================================================================


class _Port:
    """Test double for `authorization.AuthorizationPort`.

    `active` is what PACK-08 would confirm; `held` is what each opaque
    actor reference actually holds in the scope. Tests mutate both
    explicitly, because "PACK-08 said yes" is the fact every authority
    check depends on and it must never be implicit."""

    def __init__(self) -> None:
        self.active: dict[UUID, AuthorityReference] = {}
        self.held: dict[str, frozenset[FinanceRole]] = {}

    def grant(self, authority: AuthorityReference, role: FinanceRole | None) -> AuthorityReference:
        self.active[authority.authority_id] = authority
        actor = authority.actor_reference.strip()
        if actor:
            self.held[actor] = frozenset() if role is None else frozenset({role})
        return authority

    def resolve_active_authority(
        self, authority: AuthorityReference, scope: OrganizationalScopeRef
    ) -> bool:
        known = self.active.get(authority.authority_id)
        return (
            known is not None
            and known.role_code == authority.role_code
            and authority.scope.organization_id == scope.organization_id
        )

    def held_roles(
        self, actor_reference: str, scope: OrganizationalScopeRef
    ) -> frozenset[FinanceRole]:
        return self.held.get(actor_reference, frozenset())


@dataclass(slots=True)
class World:
    """Every store the commands need, plus the authorities and the clock."""

    accounts: InMemoryFinanceAccountStore
    periods: InMemoryAccountingPeriodStore
    entries: InMemoryJournalEntryStore
    transactions: InMemoryFinancialTransactionStore
    batches: InMemoryImportBatchStore
    contributions: InMemoryFinanceContributionStore
    sponsorships: InMemorySponsorshipAgreementStore
    benefits: InMemoryExternalFinancialBenefitStore
    claims: InMemoryExpenseClaimStore
    authorizations: InMemoryPaymentAuthorizationStore
    reimbursements: InMemoryReimbursementStore
    obligations: InMemoryFinancialObligationStore
    perimeters: InMemoryReportingPerimeterDefinitionStore
    perimeter_snapshots: InMemoryPerimeterSnapshotStore
    snapshots: InMemoryReportSnapshotStore
    versions: InMemoryFinanceReportVersionStore
    publications: InMemoryPublicationAuthorizationStore
    engagements: InMemoryAuditEngagementStore
    handles: InMemoryFinancePartyHandleStore
    idempotency: InMemoryCommandIdempotencyStore
    audit: InMemoryAuditEventStore
    sink: InMemoryEventSink
    clock: FixedClock
    port: _Port
    scope: OrganizationalScopeRef
    other_scope: OrganizationalScopeRef
    admin: AuthorityReference
    admin2: AuthorityReference
    orgadmin: AuthorityReference
    payer: AuthorityReference
    executor: AuthorityReference
    signatory: AuthorityReference
    auditor: AuthorityReference
    resolver: AuthorityReference


def _authority(role_code: str, actor: str, scope: OrganizationalScopeRef) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(), role_code=role_code, scope=scope, actor_reference=actor
    )


def _world() -> World:
    scope = OrganizationalScopeRef(organization_id=uuid4())
    other_scope = OrganizationalScopeRef(organization_id=uuid4())
    port = _Port()
    admin = port.grant(
        _authority("finance_administrator", "actor-admin", scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    admin2 = port.grant(
        _authority("finance_administrator", "actor-admin2", scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    orgadmin = port.grant(
        _authority("organizational_administrator", "actor-orgadmin", scope),
        FinanceRole.ORGANIZATIONAL_ADMINISTRATOR,
    )
    payer = port.grant(
        _authority("payment_authorizer", "actor-authorizer", scope),
        FinanceRole.PAYMENT_AUTHORIZER,
    )
    executor = port.grant(
        _authority("payment_executor", "actor-executor", scope), FinanceRole.PAYMENT_EXECUTOR
    )
    signatory = port.grant(
        _authority("report_signatory", "actor-signatory", scope), FinanceRole.REPORT_SIGNATORY
    )
    auditor = port.grant(
        _authority("finance_auditor", "actor-auditor", scope), FinanceRole.FINANCE_AUDITOR
    )
    resolver = port.grant(
        _authority("finance_party_handle_resolver", "actor-resolver", scope), None
    )
    return World(
        accounts=InMemoryFinanceAccountStore(),
        periods=InMemoryAccountingPeriodStore(),
        entries=InMemoryJournalEntryStore(),
        transactions=InMemoryFinancialTransactionStore(),
        batches=InMemoryImportBatchStore(),
        contributions=InMemoryFinanceContributionStore(),
        sponsorships=InMemorySponsorshipAgreementStore(),
        benefits=InMemoryExternalFinancialBenefitStore(),
        claims=InMemoryExpenseClaimStore(),
        authorizations=InMemoryPaymentAuthorizationStore(),
        reimbursements=InMemoryReimbursementStore(),
        obligations=InMemoryFinancialObligationStore(),
        perimeters=InMemoryReportingPerimeterDefinitionStore(),
        perimeter_snapshots=InMemoryPerimeterSnapshotStore(),
        snapshots=InMemoryReportSnapshotStore(),
        versions=InMemoryFinanceReportVersionStore(),
        publications=InMemoryPublicationAuthorizationStore(),
        engagements=InMemoryAuditEngagementStore(),
        handles=InMemoryFinancePartyHandleStore(),
        idempotency=InMemoryCommandIdempotencyStore(),
        audit=InMemoryAuditEventStore(),
        sink=InMemoryEventSink(),
        clock=FixedClock(FIXED),
        port=port,
        scope=scope,
        other_scope=other_scope,
        admin=admin,
        admin2=admin2,
        orgadmin=orgadmin,
        payer=payer,
        executor=executor,
        signatory=signatory,
        auditor=auditor,
        resolver=resolver,
    )


def _context(
    world: World,
    *authorities: AuthorityReference,
    event_id: UUID | None = None,
    scope: OrganizationalScopeRef | None = None,
    conflict: ConflictDeclaration | None = _NO_CONFLICT,
) -> RequestContext:
    return RequestContext(
        scope=world.scope if scope is None else scope,
        authorities=authorities,
        conflict=conflict,
        event_id=uuid4() if event_id is None else event_id,
        correlation_id="finance-workflow-1",
    )


def _evidence(world: World) -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(kind=EvidenceKind.RECEIPT, external_reference="doc-1", scope=world.scope),
    )


def _lines(debit: UUID, credit: UUID, amount: int) -> tuple[PostingLine, ...]:
    return (
        PostingLine(account_id=debit, side=PostingSide.DEBIT, amount=Money(amount, "EUR")),
        PostingLine(account_id=credit, side=PostingSide.CREDIT, amount=Money(amount, "EUR")),
    )


def _open_period(world: World) -> UUID:
    period_id = uuid4()
    app.open_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        label="2026",
        timezone_name=_BERLIN,
        opens_at=_OPENS,
        closes_at=_CLOSES,
    )
    return period_id


def _active_accounts(world: World) -> tuple[UUID, UUID]:
    identifiers: list[UUID] = []
    for code, classification in (("1000", "asset"), ("4000", "income")):
        account_id = uuid4()
        app.create_finance_account(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            account_id=account_id,
            code=code,
            classification_code=classification,
            retention=_RETENTION,
        )
        app.change_finance_account_status(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            account_id=account_id,
            target_status=AccountStatus.ACTIVE,
            reason=_REASON,
        )
        identifiers.append(account_id)
    return identifiers[0], identifiers[1]


def _post_entry(world: World, period_id: UUID, cash: UUID, income: UUID, amount: int) -> UUID:
    entry_id = uuid4()
    app.draft_journal_entry(
        world.entries,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
        period_id=period_id,
        lines=_lines(cash, income, amount),
        reason=_REASON,
    )
    app.post_journal_entry(
        world.entries,
        world.periods,
        world.accounts,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
    )
    return entry_id


def _mint_handle(world: World, purpose: HandlePurpose) -> str:
    return app.mint_party_handle(
        world.handles,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        handle_id=uuid4(),
        purpose=purpose,
    ).handle.as_reference()


def _receipt(
    world: World, *, contributor: str, amount: int = 50_000, received_at: datetime | None = None
) -> ContributionReceipt:
    return ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC) if received_at is None else received_at,
        method="bank_transfer",
        amount=Money(amount, "EUR"),
        contributor_handle_reference=contributor,
    )


def _record_contribution(
    world: World, receipt: ContributionReceipt, *, event_id: UUID | None = None
) -> UUID:
    contribution_id = uuid4()
    app.record_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin, event_id=event_id),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        receipt=receipt,
        retention=_RETENTION,
    )
    return contribution_id


def _assess(
    world: World,
    contribution_id: UUID,
    *,
    related_party_group_reference: str | None = None,
) -> app.ContributionResult:
    return app.assess_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        assessment_id=uuid4(),
        window_start=_OPENS,
        window_end=_CLOSES,
        policy=_POLICY,
        classification_code="income.donation",
        source_determined=True,
        verification_complete=True,
        reason=_REASON,
        related_party_group_reference=related_party_group_reference,
    )


def _active_perimeter(world: World) -> None:
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=world.scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(world.scope,),
        state=PerimeterDefinitionState.DRAFT,
    ).activate(
        GovernedAct(at=FIXED, by_authority=world.admin, reason=_REASON, conflict=_NO_CONFLICT)
    )
    world.perimeters.save(definition)


@dataclass(slots=True)
class ReportWorkflow:
    """The identifiers a fully-walked reporting workflow produced."""

    period_id: UUID
    version_id: UUID
    report_id: UUID
    engagement_id: UUID
    snapshot_id: UUID


def _walk_report_to_published(world: World, period_id: UUID) -> ReportWorkflow:
    _active_perimeter(world)
    snapshot = app.freeze_report_snapshot(
        world.snapshots,
        world.perimeters,
        world.perimeter_snapshots,
        world.periods,
        world.transactions,
        world.entries,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        snapshot_id=uuid4(),
        period_id=period_id,
        effective_on=date(2026, 6, 1),
    ).snapshot
    version_id, report_id = uuid4(), uuid4()
    app.prepare_report_version(
        world.versions,
        world.snapshots,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        report_id=report_id,
        period_id=period_id,
        snapshot_id=snapshot.snapshot_id,
        reason=_REASON,
    )
    app.complete_internal_report_review(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        review_id=uuid4(),
        outcome=ReviewOutcome.COMPLETE,
        reason=_REASON,
    )
    engagement_id = uuid4()
    version = world.versions.get(version_id)
    assert version is not None
    app.open_audit_engagement(
        world.engagements,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        period_id=period_id,
        auditor=world.auditor,
        reason=_REASON,
        operational_actor_references=tuple(version.operational_actor_references),
    )
    app.record_audit_finding(
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.auditor),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        finding_id=uuid4(),
        severity="minor",
        summary_reference="finding-ref-1",
        reason=_REASON,
    )
    app.conclude_audit_engagement(
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.auditor),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        conclusion_id=uuid4(),
        conclusion_class="unqualified",
        reason=_REASON,
        minimum_findings=1,
    )
    app.record_auditor_review(
        world.versions,
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        engagement_id=engagement_id,
        conclusion_reference="conclusion-1",
        reason=_REASON,
    )
    app.approve_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.orgadmin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        approval_id=uuid4(),
        reason=_REASON,
    )
    app.sign_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        signature_id=uuid4(),
        reason=_REASON,
    )
    app.submit_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        submission_reference="submission-1",
        recipient_reference="bundestagsverwaltung",
        reason=_REASON,
    )
    app.record_external_acknowledgement(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        notice_effect_reference="ack-1",
        kind=ExternalStatusKind.ACKNOWLEDGEMENT,
        reason=_REASON,
    )
    app.record_external_acceptance(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        notice_effect_reference="notice-effect-1",
        kind=ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION,
        reason=_REASON,
    )
    publication = PublicationAuthorization(
        authorization_id=uuid4(),
        scope=world.scope,
        authorized_by=world.orgadmin,
        authorized_at=FIXED,
        reason=_REASON,
    )
    world.publications.save(publication)
    app.publish_report_version(
        world.versions,
        world.publications,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        publication_authorization_id=publication.authorization_id,
        publication_reference="publication-1",
        reason=_REASON,
    )
    return ReportWorkflow(
        period_id=period_id,
        version_id=version_id,
        report_id=report_id,
        engagement_id=engagement_id,
        snapshot_id=snapshot.snapshot_id,
    )


def _full_workflow(world: World) -> ReportWorkflow:
    """Register, contribute, claim, pay, report and publish - one pass."""
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    _post_entry(world, period_id, cash, income, 2_500)

    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    contribution_id = _record_contribution(world, _receipt(world, contributor=contributor))
    _assess(world, contribution_id)
    app.decide_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        decision=ContributionState.ACCEPTED,
        reason=_REASON,
    )

    claimant = _mint_handle(world, HandlePurpose.EXPENSE_CLAIMANT)
    claim_id = uuid4()
    app.submit_expense_claim(
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        claim_id=claim_id,
        claimant_handle_reference=claimant,
        purpose_class="travel",
        amount=Money(12_000, "EUR"),
        retention=_RETENTION,
        evidence=_evidence(world),
    )
    app.approve_expense_claim(
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin2),
        port=world.port,
        clock=world.clock,
        claim_id=claim_id,
        reason=_REASON,
    )
    authorization = app.authorize_payment(
        world.authorizations,
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.payer),
        port=world.port,
        clock=world.clock,
        authorization_id=uuid4(),
        payable_kind="expense_claim",
        payable_reference=claim_id,
        amount=Money(12_000, "EUR"),
        reason=_REASON,
    ).authorization
    app.settle_payment(
        world.authorizations,
        world.claims,
        world.reimbursements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.executor),
        port=world.port,
        clock=world.clock,
        authorization_id=authorization.authorization_id,
        reimbursement_id=uuid4(),
    )
    return _walk_report_to_published(world, period_id)


# =============================================================================
# The fixed clock is the only time source (`ФИН-39`)
# =============================================================================


def test_a_fixed_clock_is_the_only_time_source_any_command_reads() -> None:
    world = _world()
    _full_workflow(world)
    audit_events = world.audit.list_all()
    assert audit_events
    assert all(event.occurred_at == FIXED for event in audit_events)
    assert all(event.recorded_at == FIXED for event in audit_events)
    published = world.sink.published()
    assert published
    assert all(envelope.occurred_at == FIXED for envelope in published)


def test_a_command_records_the_clocks_instant_and_never_the_wall_clock() -> None:
    world = _world()
    period_id = _open_period(world)
    stored = world.periods.get(period_id)
    assert stored is not None
    assert stored.opens_at == _OPENS
    audit_event = world.audit.list_all()[0]
    assert audit_event.occurred_at == FIXED
    assert audit_event.recorded_at == FIXED
    assert world.sink.published()[0].occurred_at == FIXED


# =============================================================================
# Idempotency
# =============================================================================


def test_a_replayed_command_returns_the_same_aggregate_and_appends_no_second_audit_event() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    receipt = _receipt(world, contributor=contributor)
    event_id = uuid4()
    contribution_id = uuid4()
    first = app.record_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin, event_id=event_id),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        receipt=receipt,
        retention=_RETENTION,
    )
    audit_before = len(world.audit.list_all())
    events_before = len(world.sink.published())
    replay = app.record_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin, event_id=event_id),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        receipt=receipt,
        retention=_RETENTION,
    )
    assert replay.contribution == first.contribution
    assert replay.audit_event.audit_event_id == first.audit_event.audit_event_id
    assert len(world.audit.list_all()) == audit_before
    assert len(world.sink.published()) == events_before


def test_the_same_event_id_with_different_content_raises_the_idempotency_conflict() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    receipt = _receipt(world, contributor=contributor)
    event_id = uuid4()
    _record_contribution(world, receipt, event_id=event_id)
    with pytest.raises(IdempotencyConflictError) as excinfo:
        _record_contribution(world, receipt, event_id=event_id)
    assert excinfo.value.reason_code == "FINANCE_IDEMPOTENCY_CONFLICT"


def test_a_command_without_a_caller_supplied_event_id_refuses() -> None:
    world = _world()
    context = RequestContext(
        scope=world.scope,
        authorities=(world.admin,),
        conflict=_NO_CONFLICT,
        event_id=None,
    )
    with pytest.raises(IdempotencyConflictError):
        app.open_accounting_period(
            world.periods,
            world.idempotency,
            world.audit,
            world.sink,
            context=context,
            port=world.port,
            clock=world.clock,
            period_id=uuid4(),
            label="2026",
            timezone_name=_BERLIN,
            opens_at=_OPENS,
            closes_at=_CLOSES,
        )


def test_an_event_id_reused_by_a_different_command_is_a_conflict_not_a_replay() -> None:
    world = _world()
    event_id = uuid4()
    app.open_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin, event_id=event_id),
        port=world.port,
        clock=world.clock,
        period_id=uuid4(),
        label="2026",
        timezone_name=_BERLIN,
        opens_at=_OPENS,
        closes_at=_CLOSES,
    )
    with pytest.raises(IdempotencyConflictError):
        app.create_finance_account(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin, event_id=event_id),
            port=world.port,
            clock=world.clock,
            account_id=uuid4(),
            code="1000",
            classification_code="asset",
            retention=_RETENTION,
        )


# =============================================================================
# Optimistic concurrency
# =============================================================================


def test_an_expected_version_mismatch_refuses() -> None:
    world = _world()
    cash, _income = _active_accounts(world)
    with pytest.raises(OptimisticConcurrencyConflictError) as excinfo:
        app.change_finance_account_status(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            account_id=cash,
            target_status=AccountStatus.RESTRICTED,
            reason=_REASON,
            expected_account_version=99,
        )
    assert excinfo.value.reason_code == "OPTIMISTIC_CONCURRENCY_CONFLICT"


def test_an_expected_contribution_version_mismatch_refuses() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    contribution_id = _record_contribution(world, _receipt(world, contributor=contributor))
    with pytest.raises(OptimisticConcurrencyConflictError):
        app.assess_contribution(
            world.contributions,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            contribution_id=contribution_id,
            assessment_id=uuid4(),
            window_start=_OPENS,
            window_end=_CLOSES,
            policy=_POLICY,
            classification_code="income.donation",
            source_determined=True,
            verification_complete=True,
            reason=_REASON,
            expected_contribution_version=42,
        )


def test_the_matching_expected_version_is_accepted() -> None:
    world = _world()
    cash, _income = _active_accounts(world)
    stored = world.accounts.get(cash)
    assert stored is not None
    result = app.change_finance_account_status(
        world.accounts,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        account_id=cash,
        target_status=AccountStatus.RESTRICTED,
        reason=_REASON,
        expected_account_version=len(stored.history),
    )
    assert result.account.status is AccountStatus.RESTRICTED


# =============================================================================
# Scope isolation on reads and writes (`ФИН-03`, `ФИН-04`)
# =============================================================================


def test_a_foreign_scope_read_answers_not_found_rather_than_disclosing_existence() -> None:
    world = _world()
    period_id = _open_period(world)
    foreign_admin = world.port.grant(
        _authority("finance_administrator", "actor-foreign", world.other_scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    with pytest.raises(FinanceRecordNotFoundError) as excinfo:
        app.get_period_summary(
            world.periods,
            world.entries,
            context=_context(world, foreign_admin, scope=world.other_scope),
            clock=world.clock,
            period_id=period_id,
        )
    assert excinfo.value.reason_code == "VALIDATION_RECORD_NOT_FOUND"


def test_a_foreign_scope_report_read_answers_not_found_too() -> None:
    world = _world()
    workflow = _full_workflow(world)
    foreign_admin = world.port.grant(
        _authority("finance_administrator", "actor-foreign", world.other_scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    with pytest.raises(FinanceRecordNotFoundError):
        app.get_published_report_projection(
            world.versions,
            context=_context(world, foreign_admin, scope=world.other_scope),
            clock=world.clock,
            version_id=workflow.version_id,
        )


def test_a_read_of_a_record_that_does_not_exist_answers_the_same_refusal() -> None:
    world = _world()
    with pytest.raises(FinanceRecordNotFoundError):
        app.get_period_summary(
            world.periods,
            world.entries,
            context=_context(world, world.admin),
            clock=world.clock,
            period_id=uuid4(),
        )


def test_a_write_by_a_caller_holding_authority_in_the_records_own_scope_names_the_boundary() -> (
    None
):
    world = _world()
    period_id = _open_period(world)
    foreign_admin = world.port.grant(
        _authority("finance_administrator", "actor-foreign", world.other_scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    context = RequestContext(
        scope=world.other_scope,
        authorities=(foreign_admin, world.admin),
        conflict=_NO_CONFLICT,
        event_id=uuid4(),
    )
    with pytest.raises(OrganizationScopeMismatchError) as excinfo:
        app.close_accounting_period(
            world.periods,
            world.idempotency,
            world.audit,
            world.sink,
            context=context,
            port=world.port,
            clock=world.clock,
            period_id=period_id,
            reason=_REASON,
        )
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_MISMATCH"


def test_a_command_with_an_undetermined_scope_denies_before_anything_else() -> None:
    world = _world()
    context = RequestContext(
        scope=None, authorities=(world.admin,), conflict=_NO_CONFLICT, event_id=uuid4()
    )
    with pytest.raises(OrganizationScopeUndeterminedError) as excinfo:
        app.create_finance_account(
            world.accounts,
            world.idempotency,
            world.audit,
            world.sink,
            context=context,
            port=world.port,
            clock=world.clock,
            account_id=uuid4(),
            code="1000",
            classification_code="asset",
            retention=_RETENTION,
        )
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_UNDETERMINED"


# =============================================================================
# The audit chain (`ФИН-40`)
# =============================================================================


def test_the_audit_hash_chain_verifies_after_a_full_multi_command_workflow() -> None:
    world = _world()
    _full_workflow(world)
    result = world.audit.verify_chain()
    assert result.is_intact is True
    assert result.broken_at_index is None
    assert result.checked_count > 25
    assert result.checked_count == len(world.audit.list_all())


def test_every_audited_command_publishes_exactly_one_canonical_envelope() -> None:
    world = _world()
    _full_workflow(world)
    assert len(world.sink.published()) == len(world.audit.list_all())
    for envelope in world.sink.published():
        reject_identity_payload_keys(dict(envelope.payload), context=envelope.event_type)


def test_every_audit_row_carries_a_registered_reason_code() -> None:
    world = _world()
    _full_workflow(world)
    codes = {event.reason_code for event in world.audit.list_all()}
    assert codes
    assert codes <= REGISTERED_CODES


# =============================================================================
# Aggregation and reclassification (`ФИН-13`, `ФИН-14`, `ФИН-15`)
# =============================================================================


def test_a_reclassification_that_would_drop_an_obligation_refuses() -> None:
    world = _world()
    period_id = _open_period(world)
    provenance = Provenance(
        kind=ProvenanceKind.IMPORTED,
        source_system_reference="bank-feed",
        recorded_by_authority="treasury",
        import_batch_reference="fp-2026-03",
        external_reference="stmt-1",
    )
    batch_id = uuid4()
    app.register_import_batch(
        world.batches,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        batch_id=batch_id,
        provenance=provenance,
        fingerprint="fp-2026-03",
        record_count=1,
    )
    transaction_id = uuid4()
    app.record_financial_transaction(
        world.transactions,
        world.periods,
        world.batches,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        transaction_id=transaction_id,
        provenance=provenance,
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        period_id=period_id,
    )
    with pytest.raises(ReclassificationBypassDeniedError) as excinfo:
        app.reclassify_financial_transaction(
            world.transactions,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            transaction_id=transaction_id,
            classification_code="income.other",
            policy=_POLICY,
            current_obligation_references=frozenset({"disclosure.donation"}),
            resulting_obligation_references=frozenset(),
        )
    assert excinfo.value.reason_code == "FINANCE_RECLASSIFICATION_BYPASS_DENIED"


def test_a_reclassification_that_keeps_every_obligation_is_permitted() -> None:
    world = _world()
    period_id = _open_period(world)
    provenance = Provenance(
        kind=ProvenanceKind.MANUAL_ENTRY,
        source_system_reference="treasury-desk",
        recorded_by_authority="treasury",
    )
    transaction_id = uuid4()
    app.record_financial_transaction(
        world.transactions,
        world.periods,
        world.batches,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        transaction_id=transaction_id,
        provenance=provenance,
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        period_id=period_id,
    )
    result = app.reclassify_financial_transaction(
        world.transactions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        transaction_id=transaction_id,
        classification_code="income.donation",
        policy=_POLICY,
        current_obligation_references=frozenset({"disclosure.donation"}),
        resulting_obligation_references=frozenset({"disclosure.donation", "review.board"}),
    )
    assert result.transaction.classification_policy is _POLICY


def test_split_contributions_inside_one_policy_window_aggregate() -> None:
    single = _world()
    contributor = _mint_handle(single, HandlePurpose.CONTRIBUTION)
    lone_id = _record_contribution(single, _receipt(single, contributor=contributor, amount=9_000))
    lone_assessment = _assess(single, lone_id).contribution.assessment
    assert lone_assessment is not None

    split = _world()
    split_contributor = _mint_handle(split, HandlePurpose.CONTRIBUTION)
    first_id = _record_contribution(
        split, _receipt(split, contributor=split_contributor, amount=4_500)
    )
    second_id = _record_contribution(
        split,
        _receipt(
            split,
            contributor=split_contributor,
            amount=4_500,
            received_at=datetime(2026, 4, 10, tzinfo=UTC),
        ),
    )
    aggregated = split.contributions.list_for_party_in_window(
        scope=split.scope,
        party_handle_reference=split_contributor,
        window_start=_OPENS,
        window_end=_CLOSES,
    )
    assert {record.contribution_id for record in aggregated} == {first_id, second_id}
    split_assessment = _assess(split, second_id).contribution.assessment
    assert split_assessment is not None
    assert split_assessment.aggregation_snapshot_digest is not None
    assert (
        split_assessment.aggregation_snapshot_digest != lone_assessment.aggregation_snapshot_digest
    )


def test_a_related_party_group_reference_changes_the_aggregation_snapshot() -> None:
    unrelated = _world()
    contributor = _mint_handle(unrelated, HandlePurpose.CONTRIBUTION)
    contribution_id = _record_contribution(unrelated, _receipt(unrelated, contributor=contributor))
    plain = _assess(unrelated, contribution_id).contribution.assessment
    assert plain is not None

    related = _world()
    related_contributor = _mint_handle(related, HandlePurpose.CONTRIBUTION)
    related_id = _record_contribution(related, _receipt(related, contributor=related_contributor))
    grouped = _assess(
        related, related_id, related_party_group_reference="group-1"
    ).contribution.assessment
    assert grouped is not None
    assert grouped.related_party_group_reference == "group-1"
    assert grouped.aggregation_snapshot_digest != plain.aggregation_snapshot_digest


def test_an_unattributed_contribution_cannot_be_assessed_against_an_aggregate() -> None:
    world = _world()
    anonymous = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="cash",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=None,
    )
    contribution_id = _record_contribution(world, anonymous)
    with pytest.raises(ContributionAggregationUnresolvedError) as excinfo:
        _assess(world, contribution_id)
    assert excinfo.value.reason_code == "FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED"


def test_a_contribution_received_outside_the_presented_window_refuses() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    contribution_id = _record_contribution(
        world,
        _receipt(world, contributor=contributor, received_at=datetime(2025, 2, 10, tzinfo=UTC)),
    )
    with pytest.raises(ContributionAggregationUnresolvedError):
        _assess(world, contribution_id)


# =============================================================================
# Separation of duties inside the commands (`ФИН-31`, `ФИН-33`)
# =============================================================================


def test_settlement_by_the_authorizing_actor_refuses() -> None:
    world = _world()
    claimant = _mint_handle(world, HandlePurpose.EXPENSE_CLAIMANT)
    claim_id = uuid4()
    app.submit_expense_claim(
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        claim_id=claim_id,
        claimant_handle_reference=claimant,
        purpose_class="travel",
        amount=Money(12_000, "EUR"),
        retention=_RETENTION,
        evidence=_evidence(world),
    )
    app.approve_expense_claim(
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin2),
        port=world.port,
        clock=world.clock,
        claim_id=claim_id,
        reason=_REASON,
    )
    authorization = app.authorize_payment(
        world.authorizations,
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.payer),
        port=world.port,
        clock=world.clock,
        authorization_id=uuid4(),
        payable_kind="expense_claim",
        payable_reference=claim_id,
        amount=Money(12_000, "EUR"),
        reason=_REASON,
    ).authorization
    # PACK-08 later grants the authorising actor the executor role: the
    # role check now passes and the actor-level rule must still refuse.
    executor_same_actor = world.port.grant(
        _authority("payment_executor", "actor-authorizer", world.scope),
        FinanceRole.PAYMENT_EXECUTOR,
    )
    with pytest.raises(SelfApprovalProhibitedError) as excinfo:
        app.settle_payment(
            world.authorizations,
            world.claims,
            world.reimbursements,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, executor_same_actor),
            port=world.port,
            clock=world.clock,
            authorization_id=authorization.authorization_id,
        )
    assert excinfo.value.reason_code == "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"


def test_approving_ones_own_expense_claim_refuses() -> None:
    world = _world()
    claimant = _mint_handle(world, HandlePurpose.EXPENSE_CLAIMANT)
    claimant_authority = world.port.grant(
        _authority("finance_administrator", claimant, world.scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    claim_id = uuid4()
    app.submit_expense_claim(
        world.claims,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        claim_id=claim_id,
        claimant_handle_reference=claimant,
        purpose_class="travel",
        amount=Money(12_000, "EUR"),
        retention=_RETENTION,
        evidence=_evidence(world),
    )
    with pytest.raises(SelfApprovalProhibitedError):
        app.approve_expense_claim(
            world.claims,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, claimant_authority),
            port=world.port,
            clock=world.clock,
            claim_id=claim_id,
            reason=_REASON,
        )


def test_settlement_without_an_authorization_refuses() -> None:
    world = _world()
    with pytest.raises(PaymentAuthorizationMissingError) as excinfo:
        app.settle_payment(
            world.authorizations,
            world.claims,
            world.reimbursements,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.executor),
            port=world.port,
            clock=world.clock,
            authorization_id=None,
        )
    assert excinfo.value.reason_code == "FINANCE_PAYMENT_AUTHORIZATION_MISSING"


def test_a_write_off_without_dual_control_refuses() -> None:
    world = _world()
    obligation_id = uuid4()
    app.record_financial_obligation(
        world.obligations,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        obligation_id=obligation_id,
        obligation_type=ObligationType.PAYABLE,
        amount=Money(7_500, "EUR"),
        valuation_date=date(2026, 2, 1),
        method_reference="nominal",
        retention=_RETENTION,
        reason=_REASON,
    )
    with pytest.raises(WriteOffNotAuthorizedError) as excinfo:
        app.write_off_financial_obligation(
            world.obligations,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            obligation_id=obligation_id,
            approving_authority=world.admin,
            reason=_REASON,
        )
    assert excinfo.value.reason_code == "FINANCE_WRITE_OFF_NOT_AUTHORIZED"
    written_off = app.write_off_financial_obligation(
        world.obligations,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        obligation_id=obligation_id,
        approving_authority=world.admin2,
        reason=_REASON,
    ).obligation
    assert written_off.state.value == "written_off"


# =============================================================================
# Handles and publication inside the commands
# =============================================================================


def test_minting_a_handle_with_an_identifying_attribute_refuses() -> None:
    world = _world()
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        app.mint_party_handle(
            world.handles,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            handle_id=uuid4(),
            purpose=HandlePurpose.CONTRIBUTION,
            attributes={"full_name": "somebody"},
        )
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_resolving_a_handle_requires_the_separate_resolution_authority() -> None:
    world = _world()
    handle = app.mint_party_handle(
        world.handles,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        handle_id=uuid4(),
        purpose=HandlePurpose.CONTRIBUTION,
    ).handle
    with pytest.raises(PartyHandleResolutionDeniedError) as excinfo:
        app.resolve_party_handle(
            world.handles,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            handle_id=handle.handle_id,
            purpose=HandlePurpose.CONTRIBUTION,
            reason=_REASON,
        )
    assert excinfo.value.reason_code == "FINANCE_PARTY_HANDLE_RESOLUTION_DENIED"


def test_a_resolution_is_audited_and_discloses_no_resolved_value() -> None:
    world = _world()
    handle = app.mint_party_handle(
        world.handles,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        handle_id=uuid4(),
        purpose=HandlePurpose.CONTRIBUTION,
    ).handle
    resolution = app.resolve_party_handle(
        world.handles,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin, world.resolver),
        port=world.port,
        clock=world.clock,
        handle_id=handle.handle_id,
        purpose=HandlePurpose.CONTRIBUTION,
        reason=_REASON,
        registry_resolution_reference="registry-row-1",
    )
    assert resolution.event.event_type == "finance_party_handle.resolved"
    assert resolution.event.payload["resolved_value_disclosed"] is False
    assert "registry-row-1" not in str(resolution.event.payload)
    assert resolution.audit_event.occurred_at == FIXED


def test_publication_without_a_separate_authorisation_refuses_from_the_command() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    workflow = _walk_report_to_published(world, period_id)
    published = world.versions.get(workflow.version_id)
    assert published is not None
    assert published.state is ReportState.PUBLISHED

    other = _world()
    other_period = _open_period(other)
    other_cash, other_income = _active_accounts(other)
    _post_entry(other, other_period, other_cash, other_income, 10_000)
    accepted_workflow = _walk_report_up_to_acceptance(other, other_period)
    with pytest.raises(PublicationNotAllowedError) as excinfo:
        app.publish_report_version(
            other.versions,
            other.publications,
            other.idempotency,
            other.audit,
            other.sink,
            context=_context(other, other.signatory),
            port=other.port,
            clock=other.clock,
            version_id=accepted_workflow,
            publication_authorization_id=None,
            publication_reference="publication-1",
            reason=_REASON,
        )
    assert excinfo.value.reason_code == "PUBLICATION_NOT_ALLOWED"


def _walk_report_up_to_acceptance(world: World, period_id: UUID) -> UUID:
    """The report workflow stopped one step short of publication."""
    _active_perimeter(world)
    snapshot = app.freeze_report_snapshot(
        world.snapshots,
        world.perimeters,
        world.perimeter_snapshots,
        world.periods,
        world.transactions,
        world.entries,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        snapshot_id=uuid4(),
        period_id=period_id,
        effective_on=date(2026, 6, 1),
    ).snapshot
    version_id = uuid4()
    app.prepare_report_version(
        world.versions,
        world.snapshots,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        report_id=uuid4(),
        period_id=period_id,
        snapshot_id=snapshot.snapshot_id,
        reason=_REASON,
    )
    app.complete_internal_report_review(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        review_id=uuid4(),
        outcome=ReviewOutcome.COMPLETE,
        reason=_REASON,
    )
    engagement_id = uuid4()
    version = world.versions.get(version_id)
    assert version is not None
    app.open_audit_engagement(
        world.engagements,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        period_id=period_id,
        auditor=world.auditor,
        reason=_REASON,
        operational_actor_references=tuple(version.operational_actor_references),
    )
    app.record_audit_finding(
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.auditor),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        finding_id=uuid4(),
        severity="minor",
        summary_reference="finding-ref-1",
        reason=_REASON,
    )
    app.conclude_audit_engagement(
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.auditor),
        port=world.port,
        clock=world.clock,
        engagement_id=engagement_id,
        conclusion_id=uuid4(),
        conclusion_class="unqualified",
        reason=_REASON,
        minimum_findings=1,
    )
    app.record_auditor_review(
        world.versions,
        world.engagements,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        engagement_id=engagement_id,
        conclusion_reference="conclusion-1",
        reason=_REASON,
    )
    app.approve_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.orgadmin),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        approval_id=uuid4(),
        reason=_REASON,
    )
    app.sign_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        signature_id=uuid4(),
        reason=_REASON,
    )
    app.submit_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        submission_reference="submission-1",
        recipient_reference="bundestagsverwaltung",
        reason=_REASON,
    )
    app.record_external_acceptance(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.signatory),
        port=world.port,
        clock=world.clock,
        version_id=version_id,
        notice_effect_reference="notice-effect-1",
        kind=ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION,
        reason=_REASON,
    )
    return version_id


def test_a_corrected_report_version_supersedes_its_predecessor_through_the_command() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    workflow = _walk_report_to_published(world, period_id)
    corrected = app.create_corrected_report_version(
        world.versions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        version_id=workflow.version_id,
        successor_version_id=uuid4(),
        correction_kind=CorrectionKind.RESTATEMENT,
        reason=_REASON,
    )
    assert corrected.superseded.state is ReportState.SUPERSEDED
    assert corrected.successor.state is ReportState.RESTATED
    assert corrected.successor.restatement_of_version_reference == workflow.version_id
    stored = world.versions.get(workflow.version_id)
    assert stored is not None
    assert stored.state is ReportState.SUPERSEDED


def test_a_pack_35_lobbying_subject_refuses_from_the_command() -> None:
    world = _world()
    with pytest.raises(UnauthorizedStateTransitionError) as excinfo:
        app.record_external_financial_benefit(
            world.benefits,
            world.idempotency,
            world.audit,
            world.sink,
            context=_context(world, world.admin),
            port=world.port,
            clock=world.clock,
            benefit_id=uuid4(),
            benefit_type=ExternalBenefitType.PAID_THIRD_PARTY_SUPPORT,
            retention=_RETENTION,
            subject_kind="meeting",
            value=Money(30_000, "EUR"),
        )
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_a_sponsorship_is_registered_and_approved_through_the_commands() -> None:
    world = _world()
    sponsor = _mint_handle(world, HandlePurpose.SPONSORSHIP)
    agreement = SponsorshipAgreement(
        agreement_id=uuid4(),
        scope=world.scope,
        sponsor_handle_reference=sponsor,
        benefit_description="conference stand",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        retention=_RETENTION,
        value=Money(200_000, "EUR"),
        counter_performance="logo placement",
    )
    app.register_sponsorship(
        world.sponsorships,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        agreement=agreement,
    )
    approved = app.approve_sponsorship(
        world.sponsorships,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        agreement_id=agreement.agreement_id,
        reason=_REASON,
    ).agreement
    assert approved.review_state.value == "approved"


# =============================================================================
# Every refusal is reason-coded, and every code is registered (`ФИН-40`)
# =============================================================================


def _closed_period_posting() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    entry_id = uuid4()
    app.draft_journal_entry(
        world.entries,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
        period_id=period_id,
        lines=_lines(cash, income, 1_000),
        reason=_REASON,
    )
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    app.post_journal_entry(
        world.entries,
        world.periods,
        world.accounts,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
    )


def _foreign_scope_read() -> None:
    world = _world()
    period_id = _open_period(world)
    foreign_admin = world.port.grant(
        _authority("finance_administrator", "actor-foreign", world.other_scope),
        FinanceRole.FINANCE_ADMINISTRATOR,
    )
    app.get_period_summary(
        world.periods,
        world.entries,
        context=_context(world, foreign_admin, scope=world.other_scope),
        clock=world.clock,
        period_id=period_id,
    )


def _stale_expected_version() -> None:
    world = _world()
    cash, _income = _active_accounts(world)
    app.change_finance_account_status(
        world.accounts,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        account_id=cash,
        target_status=AccountStatus.RESTRICTED,
        reason=_REASON,
        expected_account_version=99,
    )


def _replayed_event_id_with_other_content() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    event_id = uuid4()
    _record_contribution(world, _receipt(world, contributor=contributor), event_id=event_id)
    _record_contribution(world, _receipt(world, contributor=contributor), event_id=event_id)


def _scope_with_no_organization() -> None:
    scope = OrganizationalScopeRef(organization_id=uuid4())
    scope.assert_matches(None)


def _foreign_scope_write() -> None:
    scope = OrganizationalScopeRef(organization_id=uuid4())
    scope.assert_matches(OrganizationalScopeRef(organization_id=uuid4()))


#: `(callable, expected reason code)` pairs, one per governed refusal the
#: rest of this suite depends on. The point is not the raising - other
#: modules already assert that - but that each refusal names a code the
#: registry knows (`ФИН-40`).
REFUSAL_CASES: tuple[tuple[Callable[[], object], str], ...] = (
    (lambda: Money(1.5, "EUR"), "FINANCE_MONETARY_AMOUNT_INVALID"),  # type: ignore[arg-type]
    (lambda: Money(1_000, "USD"), "FINANCE_CURRENCY_UNSUPPORTED"),
    (_closed_period_posting, "FINANCE_ACCOUNTING_PERIOD_CLOSED"),
    (
        lambda: require_timezone(datetime(2026, 3, 1), context="test"),
        "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED",
    ),
    (
        lambda: assert_no_small_cell_disclosure({"cell": 1}, context="test"),
        "FINANCE_STATISTICAL_DISCLOSURE_RISK",
    ),
    (
        lambda: reject_identity_payload_keys({"user_id": "u"}, context="test"),
        "FINANCE_FORBIDDEN_IDENTITY_LINKAGE",
    ),
    (
        lambda: assert_no_document_content({"is_authentic": True}, context="test"),
        "FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE",
    ),
    (lambda: require_retention_binding(None), "FINANCE_RETENTION_BINDING_MISSING"),
    (
        lambda: assert_authorized("post_transaction", (), None, port=_world().port),
        "ORGANIZATION_SCOPE_UNDETERMINED",
    ),
    (_scope_with_no_organization, "ORGANIZATION_SCOPE_UNDETERMINED"),
    (_foreign_scope_write, "ORGANIZATION_SCOPE_MISMATCH"),
    (
        lambda: assert_roles_compatible(
            {FinanceRole.FINANCE_AUDITOR, FinanceRole.FINANCE_ADMINISTRATOR}
        ),
        "AUTHORITY_ROLE_INCOMPATIBLE",
    ),
    (
        lambda: assert_not_self_approval("actor-a", "actor-a", action="test"),
        "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED",
    ),
    (lambda: assert_conflict_declared(None, action="test"), "CONFLICT_OF_INTEREST_UNDECLARED"),
    (
        lambda: assert_conflict_declared(
            ConflictDeclaration(state=ConflictDeclaration.BLOCKING, declared_by="board"),
            action="test",
        ),
        "CONFLICT_OF_INTEREST_BLOCKING",
    ),
    (lambda: delete_finance_record(object()), "GOVERNED_RECORD_DELETION_FORBIDDEN"),
    (_foreign_scope_read, "VALIDATION_RECORD_NOT_FOUND"),
    (_stale_expected_version, "OPTIMISTIC_CONCURRENCY_CONFLICT"),
    (_replayed_event_id_with_other_content, "FINANCE_IDEMPOTENCY_CONFLICT"),
)


@pytest.mark.parametrize(
    ("refusal", "expected_code"), REFUSAL_CASES, ids=[code for _, code in REFUSAL_CASES]
)
def test_every_listed_refusal_carries_a_registered_reason_code(
    refusal: Callable[[], object], expected_code: str
) -> None:
    with pytest.raises(FinanceError) as excinfo:
        refusal()
    assert excinfo.value.reason_code == expected_code
    assert excinfo.value.reason_code in REGISTERED_CODES


def test_every_finance_exception_class_carries_a_registered_reason_code() -> None:
    unregistered: list[str] = []
    stack: list[type[FinanceError]] = [FinanceError]
    seen: set[type[FinanceError]] = set()
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        stack.extend(cls.__subclasses__())
        if cls.reason_code not in REGISTERED_CODES:
            unregistered.append(f"{cls.__name__} -> {cls.reason_code}")
    assert unregistered == []
    assert len(seen) > 40


def test_the_reason_code_registry_loads_and_is_non_trivial() -> None:
    assert REASON_CODE_REGISTRY.is_file()
    assert len(REGISTERED_CODES) > 80
    assert "FINANCE_AUTHORITY_MISSING" in REGISTERED_CODES


def test_a_technical_failure_is_deliberately_not_a_governed_reason_code() -> None:
    from epd2_finance_service.exceptions import FinanceTechnicalError

    assert not issubclass(FinanceTechnicalError, FinanceError)
    assert not hasattr(FinanceTechnicalError, "reason_code")


# =============================================================================
# Queries return derived, non-authoritative projections (`ФИН-34`)
# =============================================================================


def test_every_query_answers_with_a_non_authoritative_projection() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    _post_entry(world, period_id, cash, income, 2_500)
    workflow = _walk_report_to_published(world, period_id)

    balance = app.get_account_balance_projection(
        world.accounts,
        world.entries,
        context=_context(world, world.admin),
        clock=world.clock,
        account_id=cash,
        period_id=period_id,
        currency="EUR",
    )
    assert balance.closing_balance == Money(12_500, "EUR")
    assert balance.is_authoritative is False

    summary = app.get_period_summary(
        world.periods,
        world.entries,
        context=_context(world, world.admin),
        clock=world.clock,
        period_id=period_id,
    )
    assert dict(summary.total_minor_units_by_currency) == {"EUR": 12_500}
    assert summary.is_authoritative is False

    report = app.get_published_report_projection(
        world.versions,
        context=_context(world, world.admin),
        clock=world.clock,
        version_id=workflow.version_id,
    )
    assert report.publication_reference == "publication-1"
    assert report.is_authoritative is False

    conclusion = app.get_audit_conclusion_projection(
        world.engagements,
        context=_context(world, world.admin),
        clock=world.clock,
        engagement_id=workflow.engagement_id,
    )
    assert conclusion.conclusion_class == "unqualified"
    assert conclusion.is_authoritative is False


def test_a_contribution_disclosure_query_omits_the_party_on_the_wire() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    contribution_id = _record_contribution(world, _receipt(world, contributor=contributor))
    _assess(world, contribution_id)
    app.decide_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        decision=ContributionState.ACCEPTED,
        reason=_REASON,
    )
    disclosures = app.list_contribution_disclosures(
        world.contributions,
        context=_context(world, world.admin),
        clock=world.clock,
        disclosure_obligation_reference="ParteienG-25",
        reporting_period_label="2026",
    )
    assert len(disclosures) == 1
    payload = disclosures[0].to_payload()
    assert "contributor_handle_reference" not in payload
    assert contributor not in str(payload)


def test_deleting_a_report_version_raises_even_after_a_successor_exists() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    workflow = _walk_report_to_published(world, period_id)
    stored = world.versions.get(workflow.version_id)
    assert stored is not None
    with pytest.raises(FinanceError) as excinfo:
        delete_report_version(stored)
    assert excinfo.value.reason_code == "GOVERNED_RECORD_DELETION_FORBIDDEN"


def test_the_returned_contribution_keeps_the_receipt_it_was_recorded_with() -> None:
    world = _world()
    contributor = _mint_handle(world, HandlePurpose.CONTRIBUTION)
    receipt = _receipt(world, contributor=contributor)
    contribution_id = _record_contribution(world, receipt)
    _assess(world, contribution_id)
    app.decide_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        decision=ContributionState.RETURN_REQUIRED,
        reason=_REASON,
    )
    returned = app.return_contribution(
        world.contributions,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.executor),
        port=world.port,
        clock=world.clock,
        contribution_id=contribution_id,
        reason=_REASON,
    ).contribution
    assert returned.state is ContributionState.RETURNED
    assert returned.receipt == receipt
    assert returned.receipt is receipt


def test_a_reversal_and_a_correction_both_go_through_their_own_commands() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    entry_id = _post_entry(world, period_id, cash, income, 10_000)
    reversal = app.reverse_journal_entry(
        world.entries,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=entry_id,
        reversal_entry_id=uuid4(),
        reason=_REASON,
    )
    assert reversal.entry.status.value == "reversed"
    assert reversal.reversal.status.value == "draft"
    second = _post_entry(world, period_id, cash, income, 2_500)
    correcting = app.correct_journal_entry(
        world.entries,
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        entry_id=second,
        correcting_entry_id=uuid4(),
        replacement_lines=_lines(cash, income, 2_600),
        reason=_REASON,
    ).entry
    assert correcting.corrects_entry_id == second
    still_posted = world.entries.get(second)
    assert still_posted is not None
    assert still_posted.status.value == "posted"


def test_a_period_reopening_is_dual_controlled_through_the_commands() -> None:
    world = _world()
    period_id = _open_period(world)
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    reopening = app.request_period_reopening(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reopening_record_id=uuid4(),
        approving_authority=world.orgadmin,
        reason=_REASON,
        policy=_POLICY,
    ).reopening_record
    reopened = app.reopen_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.orgadmin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reopening_record=reopening,
    ).period
    assert reopened.status.value == "reopened"
    assert reopened.reopening_records == (reopening,)


def test_a_posted_entry_latches_the_accounts_first_posting_flag() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    stored = world.accounts.get(cash)
    assert stored is not None
    assert stored.has_postings is True


def test_a_closed_period_still_answers_a_read() -> None:
    world = _world()
    period_id = _open_period(world)
    cash, income = _active_accounts(world)
    _post_entry(world, period_id, cash, income, 10_000)
    app.close_accounting_period(
        world.periods,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        period_id=period_id,
        reason=_REASON,
    )
    summary = app.get_period_summary(
        world.periods,
        world.entries,
        context=_context(world, world.admin),
        clock=world.clock,
        period_id=period_id,
    )
    assert dict(summary.total_minor_units_by_currency) == {"EUR": 10_000}
    assert summary.source_lifecycle_state == "closed"


def test_an_import_batch_and_its_transaction_share_the_batch_reference() -> None:
    world = _world()
    period_id = _open_period(world)
    provenance = Provenance(
        kind=ProvenanceKind.IMPORTED,
        source_system_reference="bank-feed",
        recorded_by_authority="treasury",
        import_batch_reference="fp-2026-03",
        external_reference="stmt-1",
    )
    app.register_import_batch(
        world.batches,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        batch_id=uuid4(),
        provenance=provenance,
        fingerprint="fp-2026-03",
        record_count=1,
    )
    transaction_id = uuid4()
    result = app.record_financial_transaction(
        world.transactions,
        world.periods,
        world.batches,
        world.idempotency,
        world.audit,
        world.sink,
        context=_context(world, world.admin),
        port=world.port,
        clock=world.clock,
        transaction_id=transaction_id,
        provenance=provenance,
        transaction_date=date(2026, 2, 1),
        posting_date=date(2026, 2, 2),
        period_id=period_id,
    )
    assert result.transaction.provenance.import_batch_reference == "fp-2026-03"
    stored_batch = world.batches.find_by_fingerprint(scope=world.scope, fingerprint="fp-2026-03")
    assert stored_batch is not None
    assert stored_batch.fingerprint == result.transaction.provenance.import_batch_reference

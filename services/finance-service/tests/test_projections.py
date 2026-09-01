"""Tests for `epd2_finance_service.projections` - the derived, versioned,
never-authoritative read models, the states each may be built from, the
identity-key rejection on every emitted payload and the statistical
disclosure floor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

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
    ReasonCoded,
    ReportingPeriodRef,
    RetentionBinding,
    reject_identity_payload_keys,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    ForbiddenIdentityLinkageError,
    MonetaryAmountInvalidError,
    PublicationNotAllowedError,
    SponsorshipDisclosureIncompleteError,
    StatisticalDisclosureRiskError,
)
from epd2_finance_service.ledger import AccountingPeriod, AccountStatus, FinanceAccount
from epd2_finance_service.projections import (
    INTERNAL_PROJECTION_VERSION,
    MINIMUM_CELL_SIZE,
    PUBLIC_PROJECTION_VERSION,
    AccountBalanceProjection,
    AuditConclusionProjection,
    BudgetSummaryProjection,
    ContributionDisclosureProjection,
    FinanceProjection,
    PeriodSummaryProjection,
    PublishedReportProjection,
    SourceCorrectionStatus,
    SponsorshipDisclosureProjection,
    assert_no_small_cell_disclosure,
    correction_status_for_report_state,
)
from epd2_finance_service.records import (
    ContributionAssessment,
    ContributionKind,
    ContributionReceipt,
    FinanceContribution,
    GovernedAct,
    SponsorshipAgreement,
)
from epd2_finance_service.references import (
    OrganizationalScopeReference,
    PolicyVersionReference,
)
from epd2_finance_service.reporting import (
    ApprovalRecord,
    AuditConclusion,
    AuditEngagement,
    AuditOpinionReference,
    CorrectionKind,
    ExternalAcceptanceReference,
    ExternalStatusKind,
    ExternalSubmissionReference,
    FinanceReportVersion,
    PublicationAuthorization,
    PublicationReference,
    ReportingPerimeterDefinition,
    ReportSnapshot,
    ReportState,
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
_OBLIGATION = "ParteienG-25"

#: Field-name fragments that would make a budget projection a second
#: source of truth about what actually happened (`ФИН-12`).
ACTUAL_AMOUNT_FRAGMENTS: tuple[str, ...] = ("actual", "spent", "consumed", "realised", "realized")


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


def _handle_reference(purpose: HandlePurpose = HandlePurpose.CONTRIBUTION) -> str:
    return FinancePartyHandle(handle_id=uuid4(), purpose=purpose, perimeter=_SCOPE).as_reference()


def _account() -> FinanceAccount:
    account = FinanceAccount(
        account_id=uuid4(),
        code="1000",
        classification_code="asset",
        scope=_SCOPE,
        retention=_RETENTION,
    )
    return account.activate(at=_NOW, by_authority=_authority(actor="actor-admin"), reason=_REASON)


def _period() -> AccountingPeriod:
    return AccountingPeriod(
        period_id=uuid4(),
        label="2026",
        scope=_SCOPE,
        timezone_name="Europe/Berlin",
        opens_at=datetime(2026, 1, 1, tzinfo=UTC),
        closes_at=datetime(2027, 1, 1, tzinfo=UTC),
    )


def _accepted_contribution() -> FinanceContribution:
    receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="bank_transfer",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=_handle_reference(),
    )
    contribution = FinanceContribution(
        contribution_id=uuid4(), scope=_SCOPE, receipt=receipt, retention=_RETENTION
    )
    assessment = ContributionAssessment(
        assessment_id=uuid4(),
        assessed_at=_NOW,
        assessed_by=_authority(actor="actor-admin"),
        source_determined=True,
        verification_complete=True,
        classification_code="income.donation",
        policy=_POLICY,
        aggregation_snapshot_digest="digest-1",
    )
    return contribution.assess(assessment, _act()).accept(_act())


def _classified_agreement() -> SponsorshipAgreement:
    agreement = SponsorshipAgreement(
        agreement_id=uuid4(),
        scope=_SCOPE,
        sponsor_handle_reference=_handle_reference(HandlePurpose.SPONSORSHIP),
        benefit_description="conference stand",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        retention=_RETENTION,
        value=Money(200_000, "EUR"),
        counter_performance="logo placement",
    )
    approved = agreement.begin_review(_act()).approve(_act())
    return approved.classify_disclosure(_act(), disclosure_class="public")


def _accepted_version() -> tuple[FinanceReportVersion, PublicationAuthorization]:
    period = _period_ref()
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=_SCOPE,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(_SCOPE,),
    ).activate(_act())
    snapshot = ReportSnapshot.freeze(
        snapshot_id=uuid4(),
        scope=_SCOPE,
        period=period,
        perimeter=freeze_perimeter(definition, _NOW),
        frozen_at=_NOW,
        policy_bindings=(_POLICY,),
        included_transaction_ids=(uuid4(),),
        included_entry_ids=(uuid4(),),
    )
    version = FinanceReportVersion(
        version_id=uuid4(), report_id=uuid4(), scope=_SCOPE, period=period, version=1
    ).prepare(snapshot, _act(actor="actor-preparer"))
    version = version.record_review(
        ReviewRecord(
            review_id=uuid4(),
            reviewed_at=_NOW,
            reviewer=_authority(actor="actor-reviewer"),
            outcome=ReviewOutcome.COMPLETE,
        ),
        _act(actor="actor-reviewer"),
    ).complete_internal_review(_act(actor="actor-reviewer"))
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
        ),
        _act(actor="actor-approver"),
    )
    version = version.sign(
        SignatureRecord(
            signature_id=uuid4(),
            signed_at=_NOW,
            signed_by=_authority(actor="actor-signatory", role_code="report_signatory"),
            reason=_REASON,
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
    version = version.record_external_acceptance(
        ExternalAcceptanceReference(
            notice_effect_reference="notice-effect-1",
            kind=ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION,
            decided_at=_NOW,
        ),
        _act(actor="actor-signatory"),
    )
    authorization = PublicationAuthorization(
        authorization_id=uuid4(),
        scope=_SCOPE,
        authorized_by=_authority(actor="actor-orgadmin"),
        authorized_at=_NOW,
        reason=_REASON,
    )
    return version, authorization


def _published_version() -> tuple[FinanceReportVersion, PublicationReference]:
    accepted, authorization = _accepted_version()
    reference = PublicationReference(
        publication_reference="publication-1",
        authorization_id=authorization.authorization_id,
        published_at=_NOW,
    )
    published = accepted.publish(
        reference, _act(actor="actor-signatory"), publication_authorization=authorization
    )
    return published, reference


def _concluded_engagement() -> AuditEngagement:
    auditor = _authority(actor="actor-auditor", role_code="finance_auditor")
    engagement = AuditEngagement.open(
        _act(), engagement_id=uuid4(), scope=_SCOPE, period=_period_ref(), auditor=auditor
    )
    return engagement.conclude(
        AuditConclusion(
            conclusion_id=uuid4(),
            concluded_at=_NOW,
            concluded_by=auditor,
            conclusion_class="unqualified",
            reason=_REASON,
            evidence=(
                EvidenceReference(
                    kind=EvidenceKind.AUDIT_WORKING_PAPER,
                    external_reference="paper-1",
                    scope=_SCOPE,
                ),
            ),
        ),
        _act(actor="actor-auditor"),
    )


def _every_projection() -> list[tuple[str, FinanceProjection]]:
    """One instance of every projection class in the module."""
    published, _ = _published_version()
    return [
        (
            "AccountBalanceProjection",
            AccountBalanceProjection.from_account(
                _account(), closing_balance=Money(12_500, "EUR"), generated_at=_NOW
            ),
        ),
        (
            "PeriodSummaryProjection",
            PeriodSummaryProjection.from_period(
                _period(), total_minor_units_by_currency={"EUR": 12_500}, generated_at=_NOW
            ),
        ),
        (
            "ContributionDisclosureProjection",
            ContributionDisclosureProjection.from_contribution(
                _accepted_contribution(),
                disclosure_obligation_reference=_OBLIGATION,
                reporting_period_label="2026",
                generated_at=_NOW,
                disclosure_policy=PolicyVersionReference.from_binding(_POLICY),
            ),
        ),
        (
            "SponsorshipDisclosureProjection",
            SponsorshipDisclosureProjection.from_agreement(
                _classified_agreement(),
                disclosure_obligation_reference=_OBLIGATION,
                generated_at=_NOW,
            ),
        ),
        (
            "BudgetSummaryProjection",
            BudgetSummaryProjection.from_approved_budget(
                budget_id=uuid4(),
                budget_version=1,
                scope=OrganizationalScopeReference.from_scope(_SCOPE),
                reporting_period_label="2026",
                approved_total=Money(500_000, "EUR"),
                generated_at=_NOW,
                approved_total_by_category={"office costs": Money(120_000, "EUR")},
            ),
        ),
        (
            "PublishedReportProjection",
            PublishedReportProjection.from_report_version(published, generated_at=_NOW),
        ),
        (
            "AuditConclusionProjection",
            AuditConclusionProjection.from_engagement(_concluded_engagement(), generated_at=_NOW),
        ),
    ]


PROJECTIONS: list[tuple[str, FinanceProjection]] = _every_projection()
PROJECTION_IDS: list[str] = [name for name, _ in PROJECTIONS]


# =============================================================================
# Nothing derived is ever authoritative (`ФИН-34`)
# =============================================================================


@pytest.mark.parametrize(("name", "projection"), PROJECTIONS, ids=PROJECTION_IDS)
def test_every_projection_is_non_authoritative(name: str, projection: FinanceProjection) -> None:
    assert projection.is_authoritative is False
    assert projection.to_payload()["is_authoritative"] is False


@pytest.mark.parametrize(("name", "projection"), PROJECTIONS, ids=PROJECTION_IDS)
def test_no_projection_carries_an_assignable_authority_flag(
    name: str, projection: FinanceProjection
) -> None:
    field_names = {field.name for field in fields(projection)}
    assert "is_authoritative" not in field_names
    with pytest.raises(AttributeError):
        object.__setattr__(projection, "is_authoritative", True)


@pytest.mark.parametrize(("name", "projection"), PROJECTIONS, ids=PROJECTION_IDS)
def test_every_projection_carries_the_mandatory_provenance_block(
    name: str, projection: FinanceProjection
) -> None:
    payload = projection.to_payload()
    for key in (
        "projection_version",
        "generated_at",
        "organization_id",
        "scope_kind",
        "source_lifecycle_state",
        "correction_status",
        "is_authoritative",
    ):
        assert key in payload, f"{name} omits {key}"


@pytest.mark.parametrize(("name", "projection"), PROJECTIONS, ids=PROJECTION_IDS)
def test_every_projection_payload_passes_the_identity_key_rejection(
    name: str, projection: FinanceProjection
) -> None:
    reject_identity_payload_keys(projection.to_payload(), context=f"projection {name}")


@pytest.mark.parametrize(("name", "projection"), PROJECTIONS, ids=PROJECTION_IDS)
def test_no_projection_payload_carries_a_floating_point_figure(
    name: str, projection: FinanceProjection
) -> None:
    def walk(node: object) -> None:
        assert not isinstance(node, float), f"{name} carries a float"
        if isinstance(node, Mapping):
            for value in node.values():
                walk(value)
        elif isinstance(node, list | tuple):
            for value in node:
                walk(value)

    walk(projection.to_payload())


def test_the_public_and_internal_projection_versions_are_separate_contracts() -> None:
    assert PUBLIC_PROJECTION_VERSION != INTERNAL_PROJECTION_VERSION
    balance = AccountBalanceProjection.from_account(
        _account(), closing_balance=Money(1, "EUR"), generated_at=_NOW
    )
    assert balance.projection_version == INTERNAL_PROJECTION_VERSION
    published, _ = _published_version()
    report = PublishedReportProjection.from_report_version(published, generated_at=_NOW)
    assert report.projection_version == PUBLIC_PROJECTION_VERSION


def test_a_projection_refuses_a_naive_generation_instant() -> None:
    with pytest.raises(AccountingPeriodUndeterminedError) as excinfo:
        AccountBalanceProjection.from_account(
            _account(),
            closing_balance=Money(1, "EUR"),
            generated_at=datetime(2026, 3, 1, 12, 0),
        )
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED"


# =============================================================================
# Only a published report version projects (canon 20.17 group 4)
# =============================================================================


def test_only_a_published_report_version_projects() -> None:
    published, _ = _published_version()
    projection = PublishedReportProjection.from_report_version(published, generated_at=_NOW)
    assert projection.publication_reference == "publication-1"
    assert projection.source_lifecycle_state == "published"
    assert projection.source_snapshot_id == published.snapshot_id


def test_an_externally_accepted_version_is_not_yet_publicly_projectable() -> None:
    accepted, _ = _accepted_version()
    assert accepted.state is ReportState.EXTERNALLY_ACCEPTED
    with pytest.raises(PublicationNotAllowedError) as excinfo:
        PublishedReportProjection.from_report_version(accepted, generated_at=_NOW)
    assert excinfo.value.reason_code == "PUBLICATION_NOT_ALLOWED"


@pytest.mark.parametrize("correction_kind", list(CorrectionKind))
def test_a_correction_entry_state_is_not_publicly_projectable(
    correction_kind: CorrectionKind,
) -> None:
    published, _ = _published_version()
    superseded, successor = published.create_successor_version(
        _act(actor="actor-preparer"), version_id=uuid4(), correction_kind=correction_kind
    )
    assert superseded.state is ReportState.SUPERSEDED
    with pytest.raises(PublicationNotAllowedError):
        PublishedReportProjection.from_report_version(successor, generated_at=_NOW)
    with pytest.raises(PublicationNotAllowedError):
        PublishedReportProjection.from_report_version(superseded, generated_at=_NOW)


def test_a_superseded_publication_is_visible_as_superseded_and_never_as_current() -> None:
    published, _ = _published_version()
    successor_id = uuid4()
    projection = PublishedReportProjection.from_report_version(
        published, generated_at=_NOW, superseded_by_version_reference=successor_id
    )
    assert projection.correction_status is SourceCorrectionStatus.SUPERSEDED
    assert projection.to_payload()["superseded_by_version_reference"] == str(successor_id)


def test_the_correction_status_mapping_never_reports_current_for_a_displaced_version() -> None:
    assert correction_status_for_report_state(ReportState.PUBLISHED) is (
        SourceCorrectionStatus.CURRENT
    )
    assert correction_status_for_report_state(ReportState.SUPERSEDED) is (
        SourceCorrectionStatus.SUPERSEDED
    )
    assert correction_status_for_report_state(ReportState.AMENDED) is (
        SourceCorrectionStatus.AMENDED
    )
    assert correction_status_for_report_state(ReportState.RESTATED) is (
        SourceCorrectionStatus.RESTATED
    )
    assert (
        correction_status_for_report_state(
            ReportState.PUBLISHED, superseded_by_version_reference=uuid4()
        )
        is SourceCorrectionStatus.SUPERSEDED
    )


def test_only_a_concluded_audit_engagement_projects() -> None:
    auditor = _authority(actor="actor-auditor", role_code="finance_auditor")
    open_engagement = AuditEngagement.open(
        _act(), engagement_id=uuid4(), scope=_SCOPE, period=_period_ref(), auditor=auditor
    )
    with pytest.raises(PublicationNotAllowedError):
        AuditConclusionProjection.from_engagement(open_engagement, generated_at=_NOW)


def test_an_audit_projection_carries_no_finding_content_and_no_auditor() -> None:
    projection = AuditConclusionProjection.from_engagement(
        _concluded_engagement(), generated_at=_NOW
    )
    payload = projection.to_payload()
    field_names = {field.name for field in fields(projection)}
    assert "finding_count" not in field_names
    assert "auditor" not in field_names
    assert not any("finding" in key for key in payload)
    assert not any("auditor" in key for key in payload)


# =============================================================================
# Disclosure-obliged views (canon 20.17 group 2)
# =============================================================================


def test_only_an_accepted_contribution_is_publicly_projected() -> None:
    receipt = ContributionReceipt(
        receipt_id=uuid4(),
        kind=ContributionKind.DONATION,
        received_at=datetime(2026, 2, 10, tzinfo=UTC),
        method="cash",
        amount=Money(50_000, "EUR"),
        contributor_handle_reference=None,
    )
    quarantined = FinanceContribution(
        contribution_id=uuid4(), scope=_SCOPE, receipt=receipt, retention=_RETENTION
    ).quarantine(_act())
    with pytest.raises(PublicationNotAllowedError) as excinfo:
        ContributionDisclosureProjection.from_contribution(
            quarantined,
            disclosure_obligation_reference=_OBLIGATION,
            reporting_period_label="2026",
            generated_at=_NOW,
        )
    assert excinfo.value.reason_code == "PUBLICATION_NOT_ALLOWED"


def test_a_disclosure_projection_must_name_the_obligation_that_prescribes_it() -> None:
    with pytest.raises(PublicationNotAllowedError):
        ContributionDisclosureProjection.from_contribution(
            _accepted_contribution(),
            disclosure_obligation_reference="  ",
            reporting_period_label="2026",
            generated_at=_NOW,
        )


def test_a_contribution_disclosure_never_puts_the_party_on_the_wire() -> None:
    contribution = _accepted_contribution()
    projection = ContributionDisclosureProjection.from_contribution(
        contribution,
        disclosure_obligation_reference=_OBLIGATION,
        reporting_period_label="2026",
        generated_at=_NOW,
    )
    handle_reference = contribution.receipt.contributor_handle_reference
    assert projection.contributor_handle_reference == handle_reference
    payload = projection.to_payload()
    assert "contributor_handle_reference" not in payload
    assert payload["contributor_is_recorded"] is True
    assert handle_reference is not None
    assert handle_reference not in str(payload)


def test_a_contribution_disclosure_carries_the_period_label_and_not_the_receipt_instant() -> None:
    projection = ContributionDisclosureProjection.from_contribution(
        _accepted_contribution(),
        disclosure_obligation_reference=_OBLIGATION,
        reporting_period_label="2026",
        generated_at=_NOW,
    )
    field_names = {field.name for field in fields(projection)}
    assert "received_at" not in field_names
    assert projection.reporting_period_label == "2026"


def test_a_resolved_identity_offered_as_a_party_reference_refuses() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        ContributionDisclosureProjection(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=_NOW,
            scope=OrganizationalScopeReference.from_scope(_SCOPE),
            source_lifecycle_state="accepted",
            contribution_id=uuid4(),
            contribution_kind="donation",
            reporting_period_label="2026",
            disclosure_obligation_reference=_OBLIGATION,
            contributor_handle_reference="Erika Mustermann",
        )
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_a_negative_published_total_refuses() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        ContributionDisclosureProjection(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=_NOW,
            scope=OrganizationalScopeReference.from_scope(_SCOPE),
            source_lifecycle_state="accepted",
            contribution_id=uuid4(),
            contribution_kind="donation",
            reporting_period_label="2026",
            disclosure_obligation_reference=_OBLIGATION,
            disclosed_amount=Money(-1, "EUR"),
        )


def test_only_a_disclosure_classified_or_terminated_agreement_is_projected() -> None:
    agreement = SponsorshipAgreement(
        agreement_id=uuid4(),
        scope=_SCOPE,
        sponsor_handle_reference=_handle_reference(HandlePurpose.SPONSORSHIP),
        benefit_description="conference stand",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        retention=_RETENTION,
        value=Money(200_000, "EUR"),
        counter_performance="logo placement",
    )
    approved = agreement.begin_review(_act()).approve(_act())
    with pytest.raises(PublicationNotAllowedError):
        SponsorshipDisclosureProjection.from_agreement(
            approved, disclosure_obligation_reference=_OBLIGATION, generated_at=_NOW
        )


def test_a_sponsorship_projection_without_a_disclosure_classification_fails_closed() -> None:
    with pytest.raises(SponsorshipDisclosureIncompleteError):
        SponsorshipDisclosureProjection(
            projection_version=PUBLIC_PROJECTION_VERSION,
            generated_at=_NOW,
            scope=OrganizationalScopeReference.from_scope(_SCOPE),
            source_lifecycle_state="disclosure_classified",
            agreement_id=uuid4(),
            disclosure_class="  ",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            disclosure_obligation_reference=_OBLIGATION,
        )


def test_a_sponsorship_projection_never_puts_the_sponsor_on_the_wire() -> None:
    agreement = _classified_agreement()
    projection = SponsorshipDisclosureProjection.from_agreement(
        agreement, disclosure_obligation_reference=_OBLIGATION, generated_at=_NOW
    )
    payload = projection.to_payload()
    assert "sponsor_handle_reference" not in payload
    assert agreement.sponsor_handle_reference not in str(payload)


# =============================================================================
# Budgets are never a second source of truth about actuals (`ФИН-12`)
# =============================================================================


def test_a_budget_summary_projection_has_no_field_for_an_actual_amount() -> None:
    projection = BudgetSummaryProjection.from_approved_budget(
        budget_id=uuid4(),
        budget_version=1,
        scope=OrganizationalScopeReference.from_scope(_SCOPE),
        reporting_period_label="2026",
        approved_total=Money(500_000, "EUR"),
        generated_at=_NOW,
    )
    field_names = {field.name for field in fields(projection)}
    offending = [
        name
        for name in field_names
        if any(fragment in name.lower() for fragment in ACTUAL_AMOUNT_FRAGMENTS)
    ]
    assert offending == []
    payload_keys = set(projection.to_payload())
    assert not [
        key
        for key in payload_keys
        if any(fragment in key.lower() for fragment in ACTUAL_AMOUNT_FRAGMENTS)
    ]
    assert projection.source_lifecycle_state == "approved"


def test_a_budget_category_that_is_a_record_identifier_refuses() -> None:
    with pytest.raises(PublicationNotAllowedError):
        BudgetSummaryProjection.from_approved_budget(
            budget_id=uuid4(),
            budget_version=1,
            scope=OrganizationalScopeReference.from_scope(_SCOPE),
            reporting_period_label="2026",
            approved_total=Money(500_000, "EUR"),
            generated_at=_NOW,
            approved_total_by_category={str(uuid4()): Money(1_000, "EUR")},
        )


def test_a_budget_projection_carries_no_claim_payment_or_claimant_field() -> None:
    field_names = {field.name for field in fields(BudgetSummaryProjection)}
    for forbidden in ("claim_id", "payment_id", "claimant_handle_reference", "authorization_id"):
        assert forbidden not in field_names


# =============================================================================
# Statistical disclosure control (`ФИН-35`)
# =============================================================================


def test_a_small_cell_refuses() -> None:
    with pytest.raises(StatisticalDisclosureRiskError) as excinfo:
        assert_no_small_cell_disclosure({"land_a": 1}, context="donation disclosure")
    assert excinfo.value.reason_code == "FINANCE_STATISTICAL_DISCLOSURE_RISK"


def test_an_empty_cell_passes_because_zero_discloses_nobody() -> None:
    assert_no_small_cell_disclosure({"land_a": 0, "land_b": MINIMUM_CELL_SIZE}, context="view")


def test_a_negative_cell_count_fails_closed() -> None:
    with pytest.raises(StatisticalDisclosureRiskError):
        assert_no_small_cell_disclosure({"land_a": -1}, context="view")


def test_a_policy_may_raise_the_cell_threshold_but_never_lower_it() -> None:
    assert_no_small_cell_disclosure({"land_a": 20}, context="view", minimum_cell_size=10)
    with pytest.raises(StatisticalDisclosureRiskError):
        assert_no_small_cell_disclosure({"land_a": 6}, context="view", minimum_cell_size=10)
    with pytest.raises(StatisticalDisclosureRiskError) as excinfo:
        assert_no_small_cell_disclosure({"land_a": 2}, context="view", minimum_cell_size=2)
    assert "below the module floor" in str(excinfo.value)


def test_the_module_floor_is_the_conventional_official_statistics_starting_point() -> None:
    assert MINIMUM_CELL_SIZE == 5


# =============================================================================
# Internal register views never reach the public (canon 20.17 group 1)
# =============================================================================


def test_an_account_balance_view_carries_the_internal_projection_version_only() -> None:
    projection = AccountBalanceProjection.from_account(
        _account(), closing_balance=Money(12_500, "EUR"), generated_at=_NOW
    )
    assert projection.projection_version == INTERNAL_PROJECTION_VERSION
    assert projection.source_lifecycle_state == str(AccountStatus.ACTIVE)
    assert projection.to_payload()["closing_balance"] == Money(12_500, "EUR").to_payload()


def test_a_period_summary_holds_totals_per_currency_and_never_nets_them() -> None:
    projection = PeriodSummaryProjection.from_period(
        _period(),
        total_minor_units_by_currency={"EUR": 12_500, "CHF": 700},
        generated_at=_NOW,
    )
    assert projection.total_minor_units_by_currency == (("CHF", 700), ("EUR", 12_500))
    assert projection.projection_version == INTERNAL_PROJECTION_VERSION

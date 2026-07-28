"""Tests for `epd2_finance_service.reporting` - the reporting perimeter,
the create-once snapshot, the twelve canonical report states, the
submission/acknowledgement/acceptance distinction, publication and the
independent audit engagement.
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from epd2_finance_service.domain import (
    AuthorityReference,
    ConflictDeclaration,
    OrganizationalScopeRef,
    PolicyBinding,
    ReasonCoded,
    ReportingPeriodRef,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    AuditIncompleteError,
    AuditorIndependenceViolationError,
    ExternalAcceptanceMissingError,
    ExternalAcknowledgementNotAuthoritativeError,
    GovernedRecordDeletionForbiddenError,
    ImmutableRecordModificationAttemptedError,
    PublicationNotAllowedError,
    ReportApprovalMissingError,
    ReportingPerimeterUndeterminedError,
    ReportSignOffMissingError,
    ReportSnapshotMismatchError,
    ReportSnapshotMissingError,
    ReportValidationIncompleteError,
    SelfApprovalProhibitedError,
    UnauthorizedStateTransitionError,
)
from epd2_finance_service.records import GovernedAct
from epd2_finance_service.reporting import (
    ALLOWED_REPORT_TRANSITIONS,
    CORRECTION_ENTRY_STATES,
    OPERATIONAL_STATE_SYNONYMS,
    PUBLICATION_GUARDED_SOURCE_STATE,
    ApprovalRecord,
    AuditConclusion,
    AuditEngagement,
    AuditEngagementState,
    AuditFinding,
    AuditOpinionReference,
    CorrectionKind,
    CorrectionRequest,
    ExternalAcceptanceReference,
    ExternalStatusKind,
    ExternalSubmissionReference,
    FinanceReportVersion,
    PerimeterDefinitionState,
    PublicationAuthorization,
    PublicationReference,
    ReportingObligation,
    ReportingObligationKind,
    ReportingObligationState,
    ReportingPerimeterDefinition,
    ReportSnapshot,
    ReportState,
    ReviewOutcome,
    ReviewRecord,
    SignatureRecord,
    assert_no_inferred_acceptance,
    assert_report_transition_allowed,
    delete_report_version,
    freeze_perimeter,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
_REASON = ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="board-decision-1")
_POLICY = PolicyBinding(
    policy_kind="reporting_obligation",
    policy_id="report",
    policy_version="2026.1",
    effective_from=date(2026, 1, 1),
)
_NO_CONFLICT = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="board")

#: The twelve canonical report statuses, in the order canon 19f.17 lists
#: them, written out rather than read off the enum so a rename in the
#: package fails a test instead of silently redefining the canon.
CANON_REPORT_STATE_NAMES: tuple[str, ...] = (
    "draft",
    "internally_reviewed",
    "auditor_reviewed",
    "approved",
    "signed",
    "submitted",
    "externally_acknowledged",
    "externally_accepted",
    "published",
    "amended",
    "restated",
    "superseded",
)

#: Edges the canon lifecycle does not have. Each one is a step somebody
#: would plausibly try to take, and each must refuse.
FORBIDDEN_REPORT_EDGES: tuple[tuple[ReportState, ReportState], ...] = (
    (ReportState.DRAFT, ReportState.AUDITOR_REVIEWED),
    (ReportState.DRAFT, ReportState.APPROVED),
    (ReportState.DRAFT, ReportState.SIGNED),
    (ReportState.DRAFT, ReportState.SUBMITTED),
    (ReportState.DRAFT, ReportState.PUBLISHED),
    (ReportState.INTERNALLY_REVIEWED, ReportState.APPROVED),
    (ReportState.INTERNALLY_REVIEWED, ReportState.SIGNED),
    (ReportState.AUDITOR_REVIEWED, ReportState.SIGNED),
    (ReportState.APPROVED, ReportState.SUBMITTED),
    (ReportState.APPROVED, ReportState.PUBLISHED),
    (ReportState.SIGNED, ReportState.PUBLISHED),
    (ReportState.SIGNED, ReportState.EXTERNALLY_ACCEPTED),
    (ReportState.SUBMITTED, ReportState.PUBLISHED),
    (ReportState.EXTERNALLY_ACKNOWLEDGED, ReportState.PUBLISHED),
    (ReportState.PUBLISHED, ReportState.AMENDED),
    (ReportState.PUBLISHED, ReportState.RESTATED),
    (ReportState.AMENDED, ReportState.APPROVED),
    (ReportState.RESTATED, ReportState.PUBLISHED),
    (ReportState.SUPERSEDED, ReportState.DRAFT),
    (ReportState.SUPERSEDED, ReportState.PUBLISHED),
)


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _authority(
    scope: OrganizationalScopeRef, *, actor: str, role_code: str = "finance_administrator"
) -> AuthorityReference:
    return AuthorityReference(
        authority_id=uuid4(), role_code=role_code, scope=scope, actor_reference=actor
    )


def _act(scope: OrganizationalScopeRef, *, actor: str = "actor-admin") -> GovernedAct:
    return GovernedAct(
        at=_NOW,
        by_authority=_authority(scope, actor=actor),
        reason=_REASON,
        policy=_POLICY,
        conflict=_NO_CONFLICT,
    )


def _period_ref(scope: OrganizationalScopeRef) -> ReportingPeriodRef:
    return ReportingPeriodRef(period_id=uuid4(), label="2026", scope=scope)


def _active_perimeter(scope: OrganizationalScopeRef) -> ReportingPerimeterDefinition:
    definition = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(scope,),
    )
    return definition.activate(_act(scope))


def _snapshot(
    scope: OrganizationalScopeRef, period: ReportingPeriodRef, *, snapshot_id: UUID | None = None
) -> ReportSnapshot:
    return ReportSnapshot.freeze(
        snapshot_id=uuid4() if snapshot_id is None else snapshot_id,
        scope=scope,
        period=period,
        perimeter=freeze_perimeter(_active_perimeter(scope), _NOW),
        frozen_at=_NOW,
        policy_bindings=(_POLICY,),
        included_transaction_ids=(uuid4(),),
        included_entry_ids=(uuid4(),),
    )


def _draft_version(
    scope: OrganizationalScopeRef, period: ReportingPeriodRef
) -> FinanceReportVersion:
    return FinanceReportVersion(
        version_id=uuid4(), report_id=uuid4(), scope=scope, period=period, version=1
    )


def _review(scope: OrganizationalScopeRef, *, outcome: ReviewOutcome) -> ReviewRecord:
    return ReviewRecord(
        review_id=uuid4(),
        reviewed_at=_NOW,
        reviewer=_authority(scope, actor="actor-reviewer"),
        outcome=outcome,
    )


def _audit_reference(
    scope: OrganizationalScopeRef, *, actor: str = "actor-auditor"
) -> AuditOpinionReference:
    return AuditOpinionReference(
        engagement_id=uuid4(),
        conclusion_reference="conclusion-1",
        auditor=_authority(scope, actor=actor, role_code="finance_auditor"),
        recorded_at=_NOW,
    )


def _internally_reviewed(
    scope: OrganizationalScopeRef, period: ReportingPeriodRef
) -> FinanceReportVersion:
    version = _draft_version(scope, period).prepare(
        _snapshot(scope, period), _act(scope, actor="actor-preparer")
    )
    version = version.record_review(
        _review(scope, outcome=ReviewOutcome.COMPLETE), _act(scope, actor="actor-reviewer")
    )
    return version.complete_internal_review(_act(scope, actor="actor-reviewer"))


def _signed(scope: OrganizationalScopeRef, period: ReportingPeriodRef) -> FinanceReportVersion:
    version = _internally_reviewed(scope, period)
    version = version.record_auditor_review(
        _audit_reference(scope), _act(scope, actor="actor-reviewer")
    )
    approval = ApprovalRecord(
        approval_id=uuid4(),
        approved_at=_NOW,
        approved_by=_authority(scope, actor="actor-approver"),
        reason=_REASON,
    )
    version = version.approve(approval, _act(scope, actor="actor-approver"))
    signature = SignatureRecord(
        signature_id=uuid4(),
        signed_at=_NOW,
        signed_by=_authority(scope, actor="actor-signatory", role_code="report_signatory"),
        reason=_REASON,
    )
    return version.sign(signature, _act(scope, actor="actor-signatory"))


def _submitted(scope: OrganizationalScopeRef, period: ReportingPeriodRef) -> FinanceReportVersion:
    reference = ExternalSubmissionReference(
        submission_reference="submission-1",
        recipient_reference="bundestagsverwaltung",
        submitted_at=_NOW,
    )
    return _signed(scope, period).record_submission(reference, _act(scope, actor="actor-signatory"))


def _acceptance_reference(kind: ExternalStatusKind) -> ExternalAcceptanceReference:
    return ExternalAcceptanceReference(
        notice_effect_reference="notice-effect-1", kind=kind, decided_at=_NOW
    )


def _accepted(scope: OrganizationalScopeRef, period: ReportingPeriodRef) -> FinanceReportVersion:
    return _submitted(scope, period).record_external_acceptance(
        _acceptance_reference(ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION),
        _act(scope, actor="actor-signatory"),
    )


def _publication_authorization(scope: OrganizationalScopeRef) -> PublicationAuthorization:
    return PublicationAuthorization(
        authorization_id=uuid4(),
        scope=scope,
        authorized_by=_authority(scope, actor="actor-orgadmin"),
        authorized_at=_NOW,
        reason=_REASON,
    )


def _published(
    scope: OrganizationalScopeRef, period: ReportingPeriodRef
) -> tuple[FinanceReportVersion, PublicationAuthorization]:
    authorization = _publication_authorization(scope)
    reference = PublicationReference(
        publication_reference="publication-1",
        authorization_id=authorization.authorization_id,
        published_at=_NOW,
    )
    version = _accepted(scope, period).publish(
        reference,
        _act(scope, actor="actor-signatory"),
        publication_authorization=authorization,
    )
    return version, authorization


# =============================================================================
# The twelve canonical states (canon 19f.17)
# =============================================================================


def test_the_twelve_canonical_report_states_exist_with_the_canon_names_in_order() -> None:
    assert tuple(state.value for state in ReportState) == CANON_REPORT_STATE_NAMES
    assert len(CANON_REPORT_STATE_NAMES) == 12


def test_the_transition_table_covers_every_canonical_state() -> None:
    assert set(ALLOWED_REPORT_TRANSITIONS) == set(ReportState)


def test_the_superseded_state_is_terminal_in_the_strict_sense() -> None:
    assert ALLOWED_REPORT_TRANSITIONS[ReportState.SUPERSEDED] == frozenset()


def test_every_state_can_be_superseded_because_a_displaced_version_stays_readable() -> None:
    for state in ReportState:
        if state is ReportState.SUPERSEDED:
            continue
        assert ReportState.SUPERSEDED in ALLOWED_REPORT_TRANSITIONS[state]


@pytest.mark.parametrize(("current", "target"), FORBIDDEN_REPORT_EDGES)
def test_the_allowed_transition_table_refuses_each_forbidden_edge(
    current: ReportState, target: ReportState
) -> None:
    with pytest.raises(UnauthorizedStateTransitionError) as excinfo:
        assert_report_transition_allowed(current, target)
    assert excinfo.value.reason_code == "VALIDATION_FORBIDDEN_TRANSITION"


def test_the_ordinary_forward_path_is_permitted_edge_by_edge() -> None:
    ordered = [
        ReportState.DRAFT,
        ReportState.INTERNALLY_REVIEWED,
        ReportState.AUDITOR_REVIEWED,
        ReportState.APPROVED,
        ReportState.SIGNED,
        ReportState.SUBMITTED,
        ReportState.EXTERNALLY_ACKNOWLEDGED,
        ReportState.EXTERNALLY_ACCEPTED,
        ReportState.PUBLISHED,
    ]
    for current, target in itertools.pairwise(ordered):
        assert_report_transition_allowed(current, target)


def test_an_acceptance_decision_arriving_without_an_acknowledgement_is_reachable() -> None:
    assert_report_transition_allowed(ReportState.SUBMITTED, ReportState.EXTERNALLY_ACCEPTED)


def test_the_publication_fast_path_is_a_guard_and_not_a_table_edge() -> None:
    assert PUBLICATION_GUARDED_SOURCE_STATE is ReportState.SIGNED
    assert ReportState.PUBLISHED not in ALLOWED_REPORT_TRANSITIONS[ReportState.SIGNED]


def test_the_operational_synonym_map_invents_no_thirteenth_state() -> None:
    mapped = {state for state in OPERATIONAL_STATE_SYNONYMS.values() if state is not None}
    assert mapped <= set(ReportState)
    assert OPERATIONAL_STATE_SYNONYMS["correction_required"] is None
    assert OPERATIONAL_STATE_SYNONYMS["audit_requested"] is None


# =============================================================================
# Perimeter and snapshot (`ФИН-24`, `ФИН-25`)
# =============================================================================


def test_only_an_active_perimeter_definition_can_be_frozen() -> None:
    scope = _scope()
    draft = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(scope,),
    )
    with pytest.raises(ReportingPerimeterUndeterminedError) as excinfo:
        freeze_perimeter(draft, _NOW)
    assert excinfo.value.reason_code == "FINANCE_REPORTING_PERIMETER_UNDETERMINED"


def test_an_empty_perimeter_cannot_be_activated() -> None:
    scope = _scope()
    empty = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(),
    )
    with pytest.raises(ReportingPerimeterUndeterminedError):
        empty.activate(_act(scope))


def test_an_active_perimeter_definition_is_immutable_and_a_change_is_a_new_version() -> None:
    scope = _scope()
    active = _active_perimeter(scope)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        active.amend_draft(included_scopes=(scope, _scope()))


def test_the_perimeter_digest_is_order_independent() -> None:
    scope = _scope()
    other = _scope()
    first = ReportingPerimeterDefinition(
        definition_id=uuid4(),
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(scope, other),
        state=PerimeterDefinitionState.ACTIVE,
    )
    second = ReportingPerimeterDefinition(
        definition_id=first.definition_id,
        scope=scope,
        version=1,
        effective_from=date(2026, 1, 1),
        included_scopes=(other, scope),
        state=PerimeterDefinitionState.ACTIVE,
    )
    assert freeze_perimeter(first, _NOW).digest == freeze_perimeter(second, _NOW).digest


def test_a_snapshot_whose_digest_does_not_match_its_contents_cannot_exist() -> None:
    scope = _scope()
    period = _period_ref(scope)
    with pytest.raises(ImmutableRecordModificationAttemptedError) as excinfo:
        ReportSnapshot(
            snapshot_id=uuid4(),
            scope=scope,
            period=period,
            perimeter=freeze_perimeter(_active_perimeter(scope), _NOW),
            content_digest="not-the-real-digest",
            frozen_at=_NOW,
        )
    assert excinfo.value.reason_code == "FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED"


def test_a_frozen_snapshot_offers_no_edit_path_but_an_explicit_refusal() -> None:
    scope = _scope()
    period = _period_ref(scope)
    snapshot = _snapshot(scope, period)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        snapshot.with_changes(frozen_at=_NOW + timedelta(days=1))


def test_a_version_binds_exactly_one_snapshot_and_refuses_another() -> None:
    scope = _scope()
    period = _period_ref(scope)
    bound = _snapshot(scope, period)
    other = _snapshot(scope, period)
    version = _draft_version(scope, period).prepare(bound, _act(scope, actor="actor-preparer"))
    assert version.snapshot_id == bound.snapshot_id
    with pytest.raises(ReportSnapshotMismatchError) as excinfo:
        version.assert_snapshot(other)
    assert excinfo.value.reason_code == "FINANCE_REPORT_SNAPSHOT_MISMATCH"
    with pytest.raises(ReportSnapshotMismatchError):
        version.with_changes(snapshot_id=other.snapshot_id)


def test_an_act_with_no_snapshot_at_all_is_a_different_refusal_from_a_mismatch() -> None:
    scope = _scope()
    period = _period_ref(scope)
    version = _draft_version(scope, period)
    with pytest.raises(ReportSnapshotMissingError) as excinfo:
        version.assert_snapshot(None)
    assert excinfo.value.reason_code == "FINANCE_REPORT_SNAPSHOT_MISSING"


def test_a_snapshot_frozen_for_another_period_is_not_this_reports_source_data() -> None:
    scope = _scope()
    period = _period_ref(scope)
    foreign_period_snapshot = _snapshot(scope, _period_ref(scope))
    with pytest.raises(ReportSnapshotMismatchError):
        _draft_version(scope, period).prepare(
            foreign_period_snapshot, _act(scope, actor="actor-preparer")
        )


def test_internal_review_cannot_be_completed_on_a_version_that_was_never_prepared() -> None:
    scope = _scope()
    period = _period_ref(scope)
    version = _draft_version(scope, period)
    with pytest.raises(ReportSnapshotMissingError):
        version.complete_internal_review(_act(scope))


def test_a_non_preparable_state_must_name_the_snapshot_it_was_computed_from() -> None:
    scope = _scope()
    period = _period_ref(scope)
    with pytest.raises(ReportSnapshotMissingError):
        FinanceReportVersion(
            version_id=uuid4(),
            report_id=uuid4(),
            scope=scope,
            period=period,
            version=1,
            state=ReportState.SUBMITTED,
        )


# =============================================================================
# Six distinguishable acts (`ФИН-33`)
# =============================================================================


def test_preparation_approval_signing_submission_and_publication_are_distinct_acts() -> None:
    scope = _scope()
    period = _period_ref(scope)
    reviewed = _internally_reviewed(scope, period)

    with pytest.raises(AuditIncompleteError) as audit_excinfo:
        reviewed.approve(
            ApprovalRecord(
                approval_id=uuid4(),
                approved_at=_NOW,
                approved_by=_authority(scope, actor="actor-approver"),
                reason=_REASON,
            ),
            _act(scope, actor="actor-approver"),
        )
    assert audit_excinfo.value.reason_code == "FINANCE_AUDIT_INCOMPLETE"

    audited = reviewed.record_auditor_review(
        _audit_reference(scope), _act(scope, actor="actor-reviewer")
    )
    with pytest.raises(SelfApprovalProhibitedError):
        audited.approve(
            ApprovalRecord(
                approval_id=uuid4(),
                approved_at=_NOW,
                approved_by=_authority(scope, actor="actor-preparer"),
                reason=_REASON,
            ),
            _act(scope, actor="actor-preparer"),
        )

    approval = ApprovalRecord(
        approval_id=uuid4(),
        approved_at=_NOW,
        approved_by=_authority(scope, actor="actor-approver"),
        reason=_REASON,
    )
    approved = audited.approve(approval, _act(scope, actor="actor-approver"))
    with pytest.raises(SelfApprovalProhibitedError):
        approved.sign(
            SignatureRecord(
                signature_id=uuid4(),
                signed_at=_NOW,
                signed_by=_authority(scope, actor="actor-approver"),
                reason=_REASON,
            ),
            _act(scope, actor="actor-approver"),
        )

    signed = _signed(scope, period)
    assert signed.state is ReportState.SIGNED
    submitted = _submitted(scope, period)
    assert submitted.state is ReportState.SUBMITTED


def test_signing_requires_a_recorded_approval() -> None:
    scope = _scope()
    period = _period_ref(scope)
    audited = _internally_reviewed(scope, period).record_auditor_review(
        _audit_reference(scope), _act(scope, actor="actor-reviewer")
    )
    signature = SignatureRecord(
        signature_id=uuid4(),
        signed_at=_NOW,
        signed_by=_authority(scope, actor="actor-signatory", role_code="report_signatory"),
        reason=_REASON,
    )
    with pytest.raises(ReportApprovalMissingError) as excinfo:
        audited.sign(signature, _act(scope, actor="actor-signatory"))
    assert excinfo.value.reason_code == "FINANCE_REPORT_APPROVAL_MISSING"


def test_submission_requires_the_legally_responsible_signature() -> None:
    scope = _scope()
    period = _period_ref(scope)
    audited = _internally_reviewed(scope, period).record_auditor_review(
        _audit_reference(scope), _act(scope, actor="actor-reviewer")
    )
    approval = ApprovalRecord(
        approval_id=uuid4(),
        approved_at=_NOW,
        approved_by=_authority(scope, actor="actor-approver"),
        reason=_REASON,
    )
    approved = audited.approve(approval, _act(scope, actor="actor-approver"))
    reference = ExternalSubmissionReference(
        submission_reference="submission-1",
        recipient_reference="bundestagsverwaltung",
        submitted_at=_NOW,
    )
    with pytest.raises(ReportSignOffMissingError) as excinfo:
        approved.record_submission(reference, _act(scope, actor="actor-signatory"))
    assert excinfo.value.reason_code == "FINANCE_REPORT_SIGN_OFF_MISSING"


def test_completing_internal_review_on_open_findings_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    version = _draft_version(scope, period).prepare(
        _snapshot(scope, period), _act(scope, actor="actor-preparer")
    )
    with_findings = version.record_review(
        _review(scope, outcome=ReviewOutcome.FINDINGS_OPEN), _act(scope, actor="actor-reviewer")
    )
    with pytest.raises(ReportValidationIncompleteError) as excinfo:
        with_findings.complete_internal_review(_act(scope, actor="actor-reviewer"))
    assert excinfo.value.reason_code == "FINANCE_REPORT_VALIDATION_INCOMPLETE"


def test_an_auditor_who_prepared_the_version_fails_the_independence_re_check() -> None:
    scope = _scope()
    period = _period_ref(scope)
    reviewed = _internally_reviewed(scope, period)
    assert "actor-preparer" in reviewed.operational_actor_references
    with pytest.raises(AuditorIndependenceViolationError) as excinfo:
        reviewed.record_auditor_review(
            _audit_reference(scope, actor="actor-preparer"), _act(scope, actor="actor-reviewer")
        )
    assert excinfo.value.reason_code == "FINANCE_AUDITOR_INDEPENDENCE_VIOLATION"


# =============================================================================
# Submission, acknowledgement, acceptance (`ФИН-26`, `ФИН-27`)
# =============================================================================


def test_submission_does_not_imply_acknowledgement_nor_acknowledgement_acceptance() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    assert submitted.state is ReportState.SUBMITTED
    assert submitted.external_acknowledgement_reference is None
    assert submitted.external_acceptance_reference is None

    acknowledged = submitted.record_external_acknowledgement(
        _acceptance_reference(ExternalStatusKind.ACKNOWLEDGEMENT),
        _act(scope, actor="actor-signatory"),
    )
    assert acknowledged.state is ReportState.EXTERNALLY_ACKNOWLEDGED
    assert acknowledged.external_acceptance_reference is None
    with pytest.raises(ExternalAcceptanceMissingError):
        assert_no_inferred_acceptance(acknowledged, _NOW)


def test_an_authoritative_decision_offered_as_an_acknowledgement_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    with pytest.raises(UnauthorizedStateTransitionError):
        submitted.record_external_acknowledgement(
            _acceptance_reference(ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION),
            _act(scope, actor="actor-signatory"),
        )


@pytest.mark.parametrize(
    "kind",
    [
        ExternalStatusKind.ACKNOWLEDGEMENT,
        ExternalStatusKind.RECEIPT,
        ExternalStatusKind.DELIVERY_TELEMETRY,
        ExternalStatusKind.READ_STATUS,
    ],
)
def test_acceptance_from_delivery_telemetry_refuses(kind: ExternalStatusKind) -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    with pytest.raises(ExternalAcknowledgementNotAuthoritativeError) as excinfo:
        submitted.record_external_acceptance(
            _acceptance_reference(kind), _act(scope, actor="actor-signatory")
        )
    assert excinfo.value.reason_code == "FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE"


def test_acceptance_with_no_reference_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    with pytest.raises(ExternalAcceptanceMissingError) as excinfo:
        submitted.record_external_acceptance(None, _act(scope, actor="actor-signatory"))
    assert excinfo.value.reason_code == "FINANCE_EXTERNAL_ACCEPTANCE_MISSING"


def test_elapsed_time_never_produces_acceptance() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    for elapsed in (timedelta(0), timedelta(weeks=6), timedelta(days=3650)):
        with pytest.raises(ExternalAcceptanceMissingError):
            assert_no_inferred_acceptance(submitted, _NOW + elapsed)


def test_a_stored_delivery_receipt_read_back_as_acceptance_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    # A version rehydrated from storage with delivery telemetry sitting in
    # the acceptance field: the transition guard refuses that input, and
    # this is the read-back guard refusing the same thing on the way out.
    rehydrated = replace(
        submitted,
        external_acceptance_reference=_acceptance_reference(ExternalStatusKind.DELIVERY_TELEMETRY),
    )
    with pytest.raises(ExternalAcknowledgementNotAuthoritativeError) as excinfo:
        assert_no_inferred_acceptance(rehydrated, _NOW)
    assert excinfo.value.reason_code == "FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE"


def test_a_recorded_authoritative_decision_is_the_only_route_to_acceptance() -> None:
    scope = _scope()
    period = _period_ref(scope)
    accepted = _accepted(scope, period)
    assert accepted.state is ReportState.EXTERNALLY_ACCEPTED
    assert_no_inferred_acceptance(accepted, _NOW)


def test_assert_no_inferred_acceptance_refuses_a_naive_now() -> None:
    scope = _scope()
    period = _period_ref(scope)
    accepted = _accepted(scope, period)
    with pytest.raises(AccountingPeriodUndeterminedError) as excinfo:
        assert_no_inferred_acceptance(accepted, datetime(2026, 3, 1, 12, 0))
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED"


# =============================================================================
# Publication (`ФИН-28`, `ФИН-34`)
# =============================================================================


def test_publication_requires_a_separate_authorisation() -> None:
    scope = _scope()
    period = _period_ref(scope)
    accepted = _accepted(scope, period)
    reference = PublicationReference(
        publication_reference="publication-1", authorization_id=uuid4(), published_at=_NOW
    )
    with pytest.raises(PublicationNotAllowedError) as excinfo:
        accepted.publish(
            reference, _act(scope, actor="actor-signatory"), publication_authorization=None
        )
    assert excinfo.value.reason_code == "PUBLICATION_NOT_ALLOWED"


def test_a_publication_record_must_name_the_authorisation_presented() -> None:
    scope = _scope()
    period = _period_ref(scope)
    accepted = _accepted(scope, period)
    authorization = _publication_authorization(scope)
    mismatched = PublicationReference(
        publication_reference="publication-1", authorization_id=uuid4(), published_at=_NOW
    )
    with pytest.raises(PublicationNotAllowedError):
        accepted.publish(
            mismatched,
            _act(scope, actor="actor-signatory"),
            publication_authorization=authorization,
        )


def test_publication_of_an_unapproved_version_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    reviewed = _internally_reviewed(scope, period)
    authorization = _publication_authorization(scope)
    reference = PublicationReference(
        publication_reference="publication-1",
        authorization_id=authorization.authorization_id,
        published_at=_NOW,
    )
    with pytest.raises(PublicationNotAllowedError):
        reviewed.publish(
            reference,
            _act(scope, actor="actor-signatory"),
            publication_authorization=authorization,
        )


def test_a_signed_version_may_be_published_only_through_the_guarded_path() -> None:
    scope = _scope()
    period = _period_ref(scope)
    signed = _signed(scope, period)
    authorization = _publication_authorization(scope)
    reference = PublicationReference(
        publication_reference="publication-1",
        authorization_id=authorization.authorization_id,
        published_at=_NOW,
    )
    published = signed.publish(
        reference, _act(scope, actor="actor-signatory"), publication_authorization=authorization
    )
    assert published.state is ReportState.PUBLISHED
    assert published.publication_reference == reference


def test_a_published_version_is_field_immutable() -> None:
    scope = _scope()
    period = _period_ref(scope)
    published, _ = _published(scope, period)
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        published.with_changes(restatement_of_version_reference=uuid4())


# =============================================================================
# Correction by successor version (`ФИН-05`, `ФИН-25`)
# =============================================================================


@pytest.mark.parametrize("correction_kind", list(CorrectionKind))
def test_an_amended_successor_supersedes_a_predecessor_that_stays_readable(
    correction_kind: CorrectionKind,
) -> None:
    scope = _scope()
    period = _period_ref(scope)
    published, _ = _published(scope, period)
    superseded, successor = published.create_successor_version(
        _act(scope, actor="actor-preparer"),
        version_id=uuid4(),
        correction_kind=correction_kind,
    )
    assert superseded.state is ReportState.SUPERSEDED
    assert superseded.publication_reference == published.publication_reference
    assert superseded.snapshot_id == published.snapshot_id
    assert successor.state is correction_kind.entry_state
    assert successor.state in CORRECTION_ENTRY_STATES
    assert successor.restatement_of_version_reference == published.version_id
    assert successor.correction_kind is correction_kind
    assert successor.version == published.version + 1
    assert successor.snapshot_id is None


def test_a_correction_entry_state_requires_the_typed_backward_reference() -> None:
    scope = _scope()
    period = _period_ref(scope)
    with pytest.raises(UnauthorizedStateTransitionError):
        FinanceReportVersion(
            version_id=uuid4(),
            report_id=uuid4(),
            scope=scope,
            period=period,
            version=2,
            state=ReportState.RESTATED,
            correction_kind=CorrectionKind.RESTATEMENT,
        )


def test_a_correction_entry_state_requires_the_matching_correction_kind() -> None:
    scope = _scope()
    period = _period_ref(scope)
    with pytest.raises(UnauthorizedStateTransitionError):
        FinanceReportVersion(
            version_id=uuid4(),
            report_id=uuid4(),
            scope=scope,
            period=period,
            version=2,
            state=ReportState.AMENDED,
            correction_kind=CorrectionKind.RESTATEMENT,
            restatement_of_version_reference=uuid4(),
        )


def test_a_report_version_cannot_restate_itself() -> None:
    scope = _scope()
    period = _period_ref(scope)
    version_id = uuid4()
    with pytest.raises(UnauthorizedStateTransitionError):
        FinanceReportVersion(
            version_id=version_id,
            report_id=uuid4(),
            scope=scope,
            period=period,
            version=1,
            restatement_of_version_reference=version_id,
        )


def test_a_correction_request_is_a_recorded_fact_and_not_a_thirteenth_state() -> None:
    scope = _scope()
    period = _period_ref(scope)
    version = _draft_version(scope, period).prepare(
        _snapshot(scope, period), _act(scope, actor="actor-preparer")
    )
    request = CorrectionRequest(
        request_id=uuid4(),
        requested_at=_NOW,
        requested_by=_authority(scope, actor="actor-reviewer"),
        reason=_REASON,
    )
    with_request = version.record_correction_request(request, _act(scope, actor="actor-reviewer"))
    assert with_request.state is ReportState.DRAFT
    assert with_request.correction_requests == (request,)


def test_a_submitted_version_refuses_a_correction_request_and_needs_a_successor() -> None:
    scope = _scope()
    period = _period_ref(scope)
    submitted = _submitted(scope, period)
    request = CorrectionRequest(
        request_id=uuid4(),
        requested_at=_NOW,
        requested_by=_authority(scope, actor="actor-reviewer"),
        reason=_REASON,
    )
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        submitted.record_correction_request(request, _act(scope, actor="actor-reviewer"))


def test_deleting_a_report_version_raises() -> None:
    scope = _scope()
    period = _period_ref(scope)
    published, _ = _published(scope, period)
    with pytest.raises(GovernedRecordDeletionForbiddenError) as excinfo:
        delete_report_version(published)
    assert excinfo.value.reason_code == "GOVERNED_RECORD_DELETION_FORBIDDEN"


# =============================================================================
# Reporting obligation (canon 19f.16)
# =============================================================================


def test_a_reporting_obligation_is_fulfilled_only_by_a_recorded_submission() -> None:
    scope = _scope()
    period = _period_ref(scope)
    obligation = ReportingObligation(
        obligation_id=uuid4(),
        scope=scope,
        period=period,
        obligation_kind=ReportingObligationKind.STATUTORY_ANNUAL_REPORT,
        statutory_deadline_reference="pack-09-deadline-1",
    ).activate(_act(scope))
    with pytest.raises(UnauthorizedStateTransitionError):
        obligation.fulfil(_act(scope), submission_reference="  ")
    fulfilled = obligation.fulfil(_act(scope), submission_reference="submission-1")
    assert fulfilled.state is ReportingObligationState.FULFILLED
    assert fulfilled.fulfilling_submission_reference == "submission-1"


def test_an_obligation_cannot_be_fulfilled_without_ever_having_been_active() -> None:
    scope = _scope()
    period = _period_ref(scope)
    created = ReportingObligation(
        obligation_id=uuid4(),
        scope=scope,
        period=period,
        obligation_kind=ReportingObligationKind.INTERIM_REPORT,
        statutory_deadline_reference="pack-09-deadline-1",
    )
    with pytest.raises(UnauthorizedStateTransitionError):
        created.fulfil(_act(scope), submission_reference="submission-1")


# =============================================================================
# The independent audit engagement (`ФИН-29`, `ФИН-30`)
# =============================================================================


def _engagement(scope: OrganizationalScopeRef, period: ReportingPeriodRef) -> AuditEngagement:
    return AuditEngagement.open(
        _act(scope),
        engagement_id=uuid4(),
        scope=scope,
        period=period,
        auditor=_authority(scope, actor="actor-auditor", role_code="finance_auditor"),
    )


def test_an_engagement_records_findings_and_concludes_exactly_once() -> None:
    scope = _scope()
    period = _period_ref(scope)
    engagement = _engagement(scope, period)
    assert engagement.state is AuditEngagementState.OPENED
    finding = AuditFinding(
        finding_id=uuid4(),
        recorded_at=_NOW,
        recorded_by=engagement.auditor,
        severity="minor",
        summary_reference="finding-ref-1",
    )
    in_progress = engagement.record_finding(finding, _act(scope, actor="actor-auditor"))
    assert in_progress.state is AuditEngagementState.IN_PROGRESS
    conclusion = AuditConclusion(
        conclusion_id=uuid4(),
        concluded_at=_NOW,
        concluded_by=engagement.auditor,
        conclusion_class="unqualified",
        reason=_REASON,
    )
    concluded = in_progress.conclude(conclusion, _act(scope, actor="actor-auditor"))
    assert concluded.state is AuditEngagementState.CONCLUDED
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        concluded.conclude(conclusion, _act(scope, actor="actor-auditor"))
    with pytest.raises(ImmutableRecordModificationAttemptedError):
        concluded.record_finding(finding, _act(scope, actor="actor-auditor"))


def test_a_concluding_authority_other_than_the_engagements_auditor_refuses() -> None:
    scope = _scope()
    period = _period_ref(scope)
    engagement = _engagement(scope, period)
    conclusion = AuditConclusion(
        conclusion_id=uuid4(),
        concluded_at=_NOW,
        concluded_by=_authority(scope, actor="actor-other", role_code="finance_auditor"),
        conclusion_class="unqualified",
        reason=_REASON,
    )
    with pytest.raises(AuditorIndependenceViolationError):
        engagement.conclude(conclusion, _act(scope, actor="actor-other"))


def test_a_policy_minimum_finding_count_is_enforced_at_conclusion() -> None:
    scope = _scope()
    period = _period_ref(scope)
    engagement = _engagement(scope, period)
    conclusion = AuditConclusion(
        conclusion_id=uuid4(),
        concluded_at=_NOW,
        concluded_by=engagement.auditor,
        conclusion_class="unqualified",
        reason=_REASON,
    )
    with pytest.raises(AuditIncompleteError):
        engagement.conclude(conclusion, _act(scope, actor="actor-auditor"), minimum_findings=1)


def test_independence_is_re_checked_at_every_finding_not_only_at_opening() -> None:
    scope = _scope()
    period = _period_ref(scope)
    engagement = _engagement(scope, period)
    finding = AuditFinding(
        finding_id=uuid4(),
        recorded_at=_NOW,
        recorded_by=engagement.auditor,
        severity="minor",
        summary_reference="finding-ref-1",
    )
    with pytest.raises(AuditorIndependenceViolationError):
        engagement.record_finding(
            finding,
            _act(scope, actor="actor-auditor"),
            operational_actor_references=("actor-auditor",),
        )


def test_a_concluded_engagement_must_carry_the_conclusion_it_concluded_with() -> None:
    scope = _scope()
    period = _period_ref(scope)
    with pytest.raises(AuditIncompleteError):
        AuditEngagement(
            engagement_id=uuid4(),
            scope=scope,
            period=period,
            auditor=_authority(scope, actor="actor-auditor", role_code="finance_auditor"),
            state=AuditEngagementState.CONCLUDED,
        )

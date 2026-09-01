"""Finance Service command and query layer (PACK-10, canon 0.8.0 section
19f; ADR-048).

Every state-changing command below routes through **one** private frame,
`_guard`, and finishes through **one** private tail, `_finish`. That is
the whole design idea of this module: a guard a command can forget is a
guard that is not in force, so no command is allowed to assemble its own
sequence of checks. `_guard` enforces, in this fixed order:

1. **Scope, before anything else (`ФИН-04`).** `RequestContext.
   require_scope()` refuses an undeterminable scope before any other
   check, any read and any write. The target record's scope is then
   re-asserted against it (`ФИН-03`).
2. **Authority (`ФИН-45`).** The action's required roles are resolved
   through `authorization.assert_authorized`, which resolves the
   *presented authority object* to an active, effective-dated,
   scope-matching assignment through `AuthorizationPort`. A `role_code`
   string is never proof, and an action absent from `ACTION_REQUIREMENTS`
   denies with `FINANCE_AUTHORITY_MISSING`.
3. **Role incompatibility and self-approval (`ФИН-30`, `ФИН-31`).** The
   canon 19f.14 matrix is re-checked at the moment of the act over the
   roles the acting actor really holds, and every prior actor the command
   names is compared with the acting one through
   `assert_not_self_approval`.
4. **Conflict declaration (`ФИН-32`).** `assert_conflict_declared` fails
   closed on `None` and on `undeclared`, and refuses a declared blocking
   conflict with its own code. This module treats **every** command as a
   protected action, which is stricter than canon 19f.13's "protected
   actions" and never softer.
5. **Idempotency.** The caller supplies `RequestContext.event_id`.
   `storage.CommandIdempotencyStore` is consulted first: the same
   `event_id` with the same `request_digest` returns the recorded
   aggregate without re-attempting the transition; the same `event_id`
   with a different digest raises `IdempotencyConflictError`.
6. **Optimistic concurrency (`HI-51`).** Every mutating command takes an
   optional `expected_*_version`; a mismatch raises
   `OptimisticConcurrencyConflictError`. See `_history_version` for where
   each aggregate's version actually comes from - no parallel counter is
   invented here.

`_finish` then appends to Audit Core, publishes the canonical envelope to
the `EventSink`, and only then records the idempotency row. **Audit
before event**: an event that escaped without an audit row is an
unaccountable act, and the reverse ordering is the one that produces it.

## Why two idempotency mechanisms

Audit Core's `get_by_event_id` makes the *audit append* idempotent, and
nothing more: replaying an audit event with the same id and identical
content is a no-op. That guarantees nothing about the aggregate - a
retried `record_contribution` carrying a fresh `event_id` would pass the
audit check and mint a second governed record for one real receipt, which
`ФИН-14` aggregation would then count twice. `CommandIdempotencyStore`
answers the command-level question ("did this exact request already
execute, and what did it produce?"); Audit Core answers the audit-level
one and stays in place as the second line of defence, catching the window
where a command appended its audit row and died before persisting its
idempotency row. Neither subsumes the other, and removing either leaves a
real hole.

## Two-tier scope errors (PACK-09's pattern, carried over unchanged)

`_load_scoped` reports a record in a foreign scope with the same
`FinanceRecordNotFoundError` and the same message shape as a record that
does not exist, so a foreign identifier discloses nothing. The specific
`ORGANIZATION_SCOPE_MISMATCH` refusal is reachable only by a caller that
already presented an authority scoped *to that organization* - it has
asserted it believes it holds authority there, so telling it "wrong
scope" reveals nothing it did not already claim. Reads never reach the
specific refusal at all.

## What this module deliberately does not do

No production persistence, no HTTP surface, no real event bus (PACK-13),
no bank or payment-provider integration, no document storage (PACK-11),
no retention or legal-hold decision (PACK-09), no lobbying-contact record
(PACK-35, `ФИН-20`) and no identity of any kind (`ФИН-01`). It imports
only `epd2_core`, `epd2_audit_core` and its own package, and it reads no
other service's storage (`ФИН-44`). No command reads system time: a
`Clock` is injected into every one of them (`ФИН-39`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import NoReturn, TypeVar
from uuid import UUID, uuid5

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_audit_core.storage import AuditEventStore
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope, compute_payload_hash
from epd2_finance_service.authorization import (
    PARTY_HANDLE_RESOLUTION_ROLE_CODE as _AUTHORIZATION_RESOLUTION_ROLE_CODE,
)
from epd2_finance_service.authorization import (
    AuthorizationPort,
    FinanceRole,
    assert_authorized,
    assert_conflict_declared,
    assert_not_self_approval,
    assert_roles_compatible,
    resolve_finance_role,
)
from epd2_finance_service.domain import (
    AuthorityReference,
    EvidenceReference,
    FinancePartyHandle,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    RequestContext,
    RetentionBinding,
    deterministic_digest,
    reject_identity_payload_keys,
    sum_money,
)
from epd2_finance_service.events import (
    accounting_period_state_payload,
    audit_engagement_state_payload,
    build_accounting_period_closed_event,
    build_accounting_period_opened_event,
    build_accounting_period_reopened_event,
    build_accounting_period_reopening_requested_event,
    build_expense_claim_approved_event,
    build_expense_claim_submitted_event,
    build_external_financial_benefit_recorded_event,
    build_finance_account_created_event,
    build_finance_account_status_changed_event,
    build_finance_audit_concluded_event,
    build_finance_audit_finding_recorded_event,
    build_finance_audit_opened_event,
    build_finance_contribution_accepted_event,
    build_finance_contribution_assessed_event,
    build_finance_contribution_quarantined_event,
    build_finance_contribution_received_event,
    build_finance_contribution_rejected_event,
    build_finance_contribution_return_required_event,
    build_finance_contribution_returned_event,
    build_finance_party_handle_minted_event,
    build_finance_party_handle_resolved_event,
    build_finance_report_acceptance_recorded_event,
    build_finance_report_amended_event,
    build_finance_report_approved_event,
    build_finance_report_auditor_reviewed_event,
    build_finance_report_external_acknowledgement_recorded_event,
    build_finance_report_internally_reviewed_event,
    build_finance_report_prepared_event,
    build_finance_report_published_event,
    build_finance_report_restated_event,
    build_finance_report_signed_event,
    build_finance_report_snapshot_frozen_event,
    build_finance_report_submitted_event,
    build_finance_report_validation_finding_recorded_event,
    build_financial_obligation_recorded_event,
    build_financial_obligation_written_off_event,
    build_financial_transaction_classification_changed_event,
    build_financial_transaction_recorded_event,
    build_import_batch_registered_event,
    build_journal_entry_drafted_event,
    build_journal_entry_posted_event,
    build_journal_entry_reversed_event,
    build_payment_authorized_event,
    build_payment_settled_event,
    build_sponsorship_approved_event,
    build_sponsorship_registered_event,
    expense_claim_state_payload,
    external_benefit_state_payload,
    finance_account_state_payload,
    finance_contribution_state_payload,
    financial_obligation_state_payload,
    financial_transaction_state_payload,
    journal_entry_state_payload,
    payment_authorization_state_payload,
    report_snapshot_state_payload,
    report_version_state_payload,
    sponsorship_state_payload,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    AuditIncompleteError,
    ContributionAggregationUnresolvedError,
    CurrencyUnsupportedError,
    DuplicateTransactionError,
    ExternalAcceptanceMissingError,
    FinanceAuthorityMissingError,
    FinanceRecordNotFoundError,
    ForbiddenIdentityLinkageError,
    IdempotencyConflictError,
    ImportProvenanceMissingError,
    OptimisticConcurrencyConflictError,
    OrganizationScopeMismatchError,
    PartyHandleResolutionDeniedError,
    PaymentAuthorizationMissingError,
    PeriodReopeningNotAuthorizedError,
    PublicationNotAllowedError,
    ReclassificationBypassDeniedError,
    ReportingPerimeterUndeterminedError,
    ReportSignOffMissingError,
    UnauthorizedStateTransitionError,
    WriteOffNotAuthorizedError,
)
from epd2_finance_service.ledger import (
    AccountingPeriod,
    AccountStatus,
    EntryStatus,
    FinanceAccount,
    FinancialTransaction,
    JournalEntry,
    PeriodReopeningRecord,
    PostingLine,
    correct,
    post,
    reverse,
)
from epd2_finance_service.projections import (
    AccountBalanceProjection,
    AuditConclusionProjection,
    ContributionDisclosureProjection,
    PeriodSummaryProjection,
    PublishedReportProjection,
)
from epd2_finance_service.records import (
    ContributionAssessment,
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
    Reimbursement,
    SponsorshipAgreement,
    SponsorshipState,
    assert_not_lobbying_subject,
)
from epd2_finance_service.references import PolicyVersionReference
from epd2_finance_service.reporting import (
    ApprovalRecord,
    AuditConclusion,
    AuditEngagement,
    AuditEngagementState,
    AuditFinding,
    AuditOpinionReference,
    CorrectionKind,
    ExternalAcceptanceReference,
    ExternalStatusKind,
    ExternalSubmissionReference,
    FinanceReportVersion,
    PublicationReference,
    ReportSnapshot,
    ReviewOutcome,
    ReviewRecord,
    SignatureRecord,
    freeze_perimeter,
)
from epd2_finance_service.storage import (
    AccountingPeriodStore,
    AuditEngagementStore,
    CommandIdempotencyStore,
    EventSink,
    ExpenseClaimStore,
    ExternalFinancialBenefitStore,
    FinanceAccountStore,
    FinanceContributionStore,
    FinancePartyHandleStore,
    FinanceReportVersionStore,
    FinancialObligationStore,
    FinancialTransactionStore,
    IdempotencyRecord,
    ImportBatchRecord,
    ImportBatchStore,
    JournalEntryStore,
    PaymentAuthorizationStore,
    PerimeterSnapshotStore,
    PublicationAuthorizationStore,
    ReimbursementStore,
    ReportingPerimeterDefinitionStore,
    ReportSnapshotStore,
    SponsorshipAgreementStore,
    transaction_fingerprint,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Audit Core policy version for the entries this service appends -
#: independent of `events.EVENT_VERSION`, which versions the wire schema.
AUDIT_POLICY_VERSION = "1.0"

_SOURCE_SERVICE = "finance-service"

#: The `actor_type` every finance audit row and every finance envelope
#: carries. Canon 19f.15 states that the actor of a finance action is
#: represented by a reference to the *authority*, never by the person
#: behind it, and this is that reference. `ActorRef.actor_id`
#: is therefore the resolved `AuthorityReference.authority_id`, which is
#: the only actor-shaped value this service is permitted to hold
#: (`ФИН-01`, `ФИН-02`).
_ACTOR_TYPE = "finance_authority"

#: The role code a party-handle resolution requires (canon 19f.15: handle
#: resolution requires a separate, explicitly granted authority).
#:
#: Defined once in `authorization.PARTY_HANDLE_RESOLUTION_ROLE_CODE` and
#: re-exported here for the command that consumes it. It is deliberately
#: **not** a `FinanceRole` and deliberately absent from
#: `ACTION_REQUIREMENTS`: resolution is not a finance action at all, it is
#: the party registry's act, and modelling it as one more finance role
#: would make it grantable alongside the others. `resolve_party_handle`
#: therefore does not go through `assert_authorized`; it resolves this one
#: authority through the port directly and refuses everything else with
#: `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`. An earlier draft declared the
#: string a second time in this module, which is exactly how two sources of
#: truth for one privilege drift apart.
PARTY_HANDLE_RESOLUTION_ROLE_CODE: str = _AUTHORIZATION_RESOLUTION_ROLE_CODE

#: Namespace for deriving a UUID correlation id from a free-text
#: `RequestContext.correlation_id`.
#:
#: `RequestContext` types `correlation_id` as `str | None` while
#: `EventEnvelope` requires a `UUID`. Rather than refusing a caller whose
#: correlation id is not a UUID - which would be a technical refusal
#: dressed as a governed one - a non-UUID string is mapped deterministically
#: through `uuid5`, so the same correlation string always yields the same
#: envelope correlation id and two events of one request correlate.
_CORRELATION_NAMESPACE = UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

# Audit `reason_code` classifications. Canon section 24's own list is
# refusal-only and has no code meaning "this succeeded", so - exactly as
# ADR-006/ADR-014/ADR-019/ADR-029 and PACK-09 already do - one generic
# classification per logical act type is used for the audit row, while
# every *refusal* carries the registered code of its `exceptions.py`
# class. These are audit classifications, never refusal codes.
_AUDIT_ACCOUNT = "FINANCE_ACCOUNT_STATE_CHANGED"
_AUDIT_PERIOD = "FINANCE_ACCOUNTING_PERIOD_STATE_CHANGED"
_AUDIT_ENTRY = "FINANCE_JOURNAL_ENTRY_STATE_CHANGED"
_AUDIT_TRANSACTION = "FINANCE_TRANSACTION_STATE_CHANGED"
_AUDIT_IMPORT = "FINANCE_IMPORT_BATCH_STATE_CHANGED"
_AUDIT_CONTRIBUTION = "FINANCE_CONTRIBUTION_STATE_CHANGED"
_AUDIT_SPONSORSHIP = "FINANCE_SPONSORSHIP_STATE_CHANGED"
_AUDIT_BENEFIT = "FINANCE_EXTERNAL_BENEFIT_STATE_CHANGED"
_AUDIT_CLAIM = "FINANCE_EXPENSE_CLAIM_STATE_CHANGED"
_AUDIT_PAYMENT = "FINANCE_PAYMENT_STATE_CHANGED"
_AUDIT_OBLIGATION = "FINANCE_OBLIGATION_STATE_CHANGED"
_AUDIT_SNAPSHOT = "FINANCE_REPORT_SNAPSHOT_FROZEN"
_AUDIT_REPORT = "FINANCE_REPORT_STATE_CHANGED"
_AUDIT_ENGAGEMENT = "FINANCE_AUDIT_ENGAGEMENT_STATE_CHANGED"
_AUDIT_HANDLE = "FINANCE_PARTY_HANDLE_ACCESS_RECORDED"

#: Command name -> the `authorization.ACTION_REQUIREMENTS` key whose role
#: set the command requires.
#:
#: **This table is a mapping onto an existing closed table, not a second
#: authority model.** `ACTION_REQUIREMENTS` lives in `authorization.py`,
#: which this module may not modify, and it names forty governed
#: actions - fewer than the commands here. Where a command has no key of
#: its own, it is mapped onto the *nearest governed action with the right
#: role set*, and the mapping is written down here rather than inlined at
#: the call site so the whole assignment is reviewable in one place. The
#: key names the **authority requirement consulted**, never the act
#: recorded: the audit row's `action` is always the command name.
#:
#: Two mappings are weaker than the canon asks and are called out as such:
#: `register_import_batch` maps onto `post_transaction`, while canon 19f.6
#: says import authority is separate and not implied by posting authority;
#: and `write_off_financial_obligation` maps onto `record_obligation`,
#: while canon 19f.11 names a policy-specific write-off authority. Both
#: would need a new `ACTION_REQUIREMENTS` entry, which is a change to
#: `authorization.py`. The commands compensate where they can - the
#: write-off additionally requires a second, distinct approving authority
#: - but the underlying role set is the one the mapped key names.
_ACTION_FOR_COMMAND: dict[str, str] = {
    "create_finance_account": "manage_chart_of_accounts",
    "change_finance_account_status": "manage_chart_of_accounts",
    "open_accounting_period": "open_period",
    "close_accounting_period": "close_period",
    "request_period_reopening": "request_period_reopening",
    "reopen_accounting_period": "approve_period_reopening",
    "draft_journal_entry": "post_transaction",
    "post_journal_entry": "post_transaction",
    "reverse_journal_entry": "reverse_transaction",
    "correct_journal_entry": "correct_transaction",
    "record_financial_transaction": "post_transaction",
    "reclassify_financial_transaction": "reclassify_transaction",
    "register_import_batch": "register_import_batch",
    "record_contribution": "record_contribution",
    "assess_contribution": "assess_contribution",
    "decide_contribution": "accept_contribution",
    "return_contribution": "return_contribution",
    "register_sponsorship": "record_sponsorship",
    "approve_sponsorship": "approve_sponsorship",
    "record_external_financial_benefit": "record_external_benefit",
    "submit_expense_claim": "record_expense",
    "approve_expense_claim": "approve_expense",
    "authorize_payment": "authorize_payment",
    "settle_payment": "execute_payment",
    "record_financial_obligation": "record_obligation",
    "write_off_financial_obligation": "write_off_position",
    "freeze_report_snapshot": "create_snapshot",
    "prepare_report_version": "prepare_report",
    "complete_internal_report_review": "record_review",
    # The auditor's own act is concluding the engagement
    # (`record_audit_opinion`). Writing that conclusion's *reference* onto
    # the report version is a report-side act, and canon 19f.18 forbids the
    # audit module from writing into an aggregate it audits - so this maps
    # onto its own `record_auditor_review` entry, which excludes the
    # `finance_auditor` role, and never onto the auditor's own action key.
    "record_auditor_review": "record_auditor_review",
    "approve_report_version": "approve_report",
    "sign_report_version": "sign_report",
    "submit_report_version": "record_external_submission",
    "record_external_acknowledgement": "record_external_acceptance",
    "record_external_acceptance": "record_external_acceptance",
    "publish_report_version": "create_publication_projection",
    "create_corrected_report_version": "create_report_version",
    "open_audit_engagement": "request_audit",
    "record_audit_finding": "record_audit_opinion",
    "conclude_audit_engagement": "record_audit_opinion",
    "mint_party_handle": "mint_party_handle",
}


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------


#: The aggregate type `_load_scoped` and `_replayed_aggregate` are generic
#: over. Written as an explicit `TypeVar` rather than PEP 695 type
#: parameters (which Ruff's UP047 would prefer) because the mypy build this
#: repository is verified with cannot parse PEP 695 function syntax at all -
#: it fails with a bare `Expected '('`. A type checker that cannot read the
#: file checks nothing in it, which is a worse outcome than one suppressed
#: style rule.
_AggregateT = TypeVar("_AggregateT")


def _raise_not_found(what: str, identifier: UUID) -> NoReturn:
    """Raise the single, non-disclosing "not found for this caller" error.

    Deliberately identical whether the record does not exist at all or
    exists in another organizational scope, so a foreign identifier
    reveals nothing (`ФИН-03`). Typed `NoReturn` so every call site's
    `is None` check narrows afterwards without a cast."""
    raise FinanceRecordNotFoundError(f"{what} {identifier} was not found")


def _load_scoped(  # noqa: UP047 - see `_AggregateT`
    getter: Callable[[UUID], _AggregateT | None],
    identifier: UUID,
    scope_of: Callable[[_AggregateT], OrganizationalScopeRef],
    *,
    scope: OrganizationalScopeRef,
    context: RequestContext,
    what: str,
    for_write: bool = False,
) -> _AggregateT:
    """Load one record and apply PACK-09's two-tier scope rule.

    A missing record and a foreign-scope record answer identically
    (`FinanceRecordNotFoundError`), so existence is not disclosed. The
    specific `ORGANIZATION_SCOPE_MISMATCH` refusal is reachable only on a
    **write** by a caller that presented an authority scoped to the
    record's own organization - such a caller has already asserted it
    believes it holds authority there, so naming the boundary tells it
    nothing new. Reads never reach it."""
    record = getter(identifier)
    if record is None:
        _raise_not_found(what, identifier)
    record_scope = scope_of(record)
    if record_scope.organization_id == scope.organization_id:
        return record
    if for_write and any(
        authority.scope.organization_id == record_scope.organization_id
        for authority in context.authorities
    ):
        raise OrganizationScopeMismatchError(
            f"{what} {identifier} belongs to another organizational scope"
        )
    _raise_not_found(what, identifier)


def _history_version(history: Sequence[object]) -> int:
    """The optimistic-concurrency version of an aggregate that carries an
    append-only history tuple.

    **Derived, never stored.** `FinanceAccount`, `AccountingPeriod`,
    `FinanceContribution`, `SponsorshipAgreement`,
    `ExternalFinancialBenefit`, `ExpenseClaim`, `FinancialObligation`,
    `FinanceReportVersion` and `AuditEngagement` all append exactly one
    history entry per governed transition, so the length of that tuple
    *is* the number of transitions the caller has seen. Inventing a
    parallel `version` column next to it would be a second answer to "is
    this stale?", and two answers that can disagree are worse than one.
    `FinancialTransaction` is the exception: it carries an explicit
    `version` field, which its own `_check_version` already enforces, and
    that field is used for it instead."""
    return len(history)


#: Journal entries and payment authorizations carry neither a history
#: tuple nor a version field, so their lifecycle position is their
#: version: each state is reachable at most once, so the ordinal is
#: monotonic exactly as a counter would be.
_ENTRY_VERSIONS: dict[EntryStatus, int] = {
    EntryStatus.DRAFT: 1,
    EntryStatus.POSTED: 2,
    EntryStatus.REVERSED: 3,
}

_AUTHORIZATION_VERSIONS: dict[PaymentAuthorizationState, int] = {
    PaymentAuthorizationState.AUTHORIZED: 1,
    PaymentAuthorizationState.EXECUTED: 2,
    PaymentAuthorizationState.REVOKED: 2,
}


def _check_expected_version(actual: int, expected: int | None, *, what: str) -> None:
    if expected is not None and expected != actual:
        raise OptimisticConcurrencyConflictError(
            f"{what} is at version {actual}, caller expected {expected}"
        )


def _state_hash(payload: Mapping[str, object]) -> str:
    """Audit Core's `before_hash`/`after_hash` over one of `events`' own
    canonical state payloads, through `epd2_core`'s canonical-JSON hash so
    two structurally identical snapshots always hash identically."""
    return compute_payload_hash(payload)


def _actor_for(authority: AuthorityReference) -> ActorRef:
    """The `ActorRef` a finance event and a finance audit row carry.

    The resolved authority, never the person behind it (canon 19f.15).
    `AuthorityReference.actor_reference` - the opaque actor pointer -
    stays out of both, because `events._authority_on_the_wire` drops it
    from every payload and putting it in the envelope's actor would
    reintroduce it one field away (`ФИН-01`, `ФИН-02`)."""
    return ActorRef(actor_id=authority.authority_id, actor_type=_ACTOR_TYPE)


def _as_uuid(value: str | None, *, fallback: UUID | None = None) -> UUID | None:
    if value is None:
        return fallback
    try:
        return UUID(value)
    except ValueError:
        return uuid5(_CORRELATION_NAMESPACE, value)


def _correlation_uuid(context: RequestContext, *, fallback: UUID) -> UUID:
    resolved = _as_uuid(context.correlation_id, fallback=fallback)
    return fallback if resolved is None else resolved


def _request_digest(command: str, parts: Sequence[str]) -> str:
    """The content digest of one command invocation.

    Covers the command name and every caller-supplied value the command
    acts on, so a retry of the *same* request is recognisable and a
    different request carrying a recycled `event_id` is a conflict rather
    than a silent replay of something else."""
    return deterministic_digest(command, "|", *(f"{part}" for part in parts))


# ---------------------------------------------------------------------------
# The shared command frame
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _CommandGuard:
    """Everything `_guard` resolved, handed to the command body."""

    command: str
    scope: OrganizationalScopeRef
    authority: AuthorityReference
    actor: ActorRef
    now: datetime
    event_id: UUID
    request_digest: str
    correlation_id: UUID
    causation_id: UUID | None
    replay: IdempotencyRecord | None


def _guard(
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    *,
    command: str,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    request_parts: Sequence[str],
    target_scope: OrganizationalScopeRef | None = None,
    prior_actor_references: Sequence[str] = (),
    resolved_authority: AuthorityReference | None = None,
    current_version: int | None = None,
    expected_version: int | None = None,
    version_label: str = "record",
) -> _CommandGuard:
    """The one frame every state-changing command routes through.

    The order of the six checks is the guarantee, not an implementation
    detail - see this module's docstring. Nothing here is conditional on a
    flag, an environment or a privileged grant: `ФИН-42` forbids that, and
    `authorization.NO_BREAK_GLASS_NOTE` states why in full."""
    # 1. Scope first (`ФИН-04`): an undeterminable scope denies before any
    # other check. `_load_scoped` has already matched the target record's
    # scope for commands that loaded one; re-asserting it here means a
    # command that obtained its record by some other route still cannot
    # act across a boundary (`ФИН-03`).
    scope = context.require_scope()
    if target_scope is not None:
        target_scope.assert_matches(scope)

    # 2. Authority (`ФИН-45`): the presented authority object is resolved
    # to an active, effective-dated, scope-matching assignment. A role
    # *name* proves nothing, and a command with no `ACTION_REQUIREMENTS`
    # key of its own would deny here rather than default open.
    if resolved_authority is not None:
        # The single, named exception, and it is narrower rather than
        # wider: `resolve_party_handle` is not one of the forty
        # governed finance actions and must never become one (canon
        # 19f.15), so its authority is resolved by
        # `_resolve_party_handle_authority` - an exact role code, this
        # exact scope, an active assignment - and handed in here. Any other
        # command presenting a pre-resolved authority is refused, so this
        # parameter cannot become a way past `assert_authorized`.
        if command != "resolve_party_handle":
            raise FinanceAuthorityMissingError(
                f"{command!r} may not present a pre-resolved authority; authority is resolved "
                "through the action requirements table"
            )
        authority = resolved_authority
    else:
        action = _ACTION_FOR_COMMAND.get(command)
        if action is None:
            raise FinanceAuthorityMissingError(
                f"{command!r} has no assigned finance authority requirement - default deny"
            )
        authority = assert_authorized(action, context.authorities, scope, port=port)

    # 3. Role incompatibility (`ФИН-30`) and self-approval (`ФИН-31`).
    # `assert_authorized` already re-ran the canon 19f.14 matrix over the
    # held roles plus the accepted one; it is re-run here over the held
    # set alone so that the matrix stays enforced in this frame even if a
    # future authorisation path stops doing it. Self-approval is compared
    # per object, not per grant: both acts can sit inside one perfectly
    # compatible role set.
    acting_actor = authority.actor_reference.strip()
    if acting_actor:
        assert_roles_compatible(port.held_roles(acting_actor, scope))
    for prior in prior_actor_references:
        assert_not_self_approval(authority.actor_reference, prior, action=command)

    # 4. Conflict declaration (`ФИН-32`): `None` and `undeclared` are the
    # same answer - unknown - and both fail closed; a declared blocking
    # conflict refuses with its own code. Every command in this module is
    # treated as a protected action, which is stricter than the canon's
    # "protected actions" and never softer.
    assert_conflict_declared(context.conflict, action=command)

    # 5. Idempotency. The command store answers first, because it is the
    # only one that knows what the command *produced*; Audit Core's
    # `get_by_event_id` is the second line of defence below.
    now = clock.now()
    event_id = context.event_id
    if event_id is None:
        raise IdempotencyConflictError(
            f"{command} requires a caller-supplied event_id on the request context"
        )
    digest = _request_digest(command, request_parts)
    recorded = idempotency_store.get(event_id)
    if recorded is not None:
        if recorded.command != command or recorded.request_digest != digest:
            raise IdempotencyConflictError(
                f"event_id {event_id} was already used by {recorded.command} with different "
                "content; the same event_id may only replay the identical request"
            )
        return _CommandGuard(
            command=command,
            scope=scope,
            authority=authority,
            actor=_actor_for(authority),
            now=now,
            event_id=event_id,
            request_digest=digest,
            correlation_id=_correlation_uuid(context, fallback=event_id),
            causation_id=_as_uuid(context.causation_id),
            replay=recorded,
        )
    # The second line of defence. Audit Core's own idempotency covers the
    # audit append and nothing else, but an audit row under this event_id
    # with no command record means a previous run appended its audit entry
    # and died before persisting the command record. Re-running the
    # transition now would mutate the aggregate a second time under one
    # audit row, so this fails closed rather than guessing.
    if audit_store.get_by_event_id(event_id) is not None:
        raise IdempotencyConflictError(
            f"event_id {event_id} already has an audit entry but no recorded command result; "
            "the previous execution did not complete and is not safely replayable"
        )

    # 6. Optimistic concurrency (`HI-51`). After idempotency on purpose: a
    # true replay must not fail on a version the first execution already
    # advanced past.
    if current_version is not None:
        _check_expected_version(current_version, expected_version, what=version_label)

    return _CommandGuard(
        command=command,
        scope=scope,
        authority=authority,
        actor=_actor_for(authority),
        now=now,
        event_id=event_id,
        request_digest=digest,
        correlation_id=_correlation_uuid(context, fallback=event_id),
        causation_id=_as_uuid(context.causation_id),
        replay=None,
    )


def _finish(
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    guard: _CommandGuard,
    *,
    event: EventEnvelope,
    aggregate_id: UUID,
    target_type: str,
    reason_code: str,
    before_hash: str,
    after_hash: str,
    clock: Clock,
) -> AuditEvent:
    """Append the audit row, publish the envelope, record the command.

    The order is the point. **Audit first**: an event that reached the
    stream without an audit row is an act nobody can account for, and the
    reverse ordering is exactly what produces one. **Idempotency last**:
    the command record claims "this ran and produced that", and it must
    not be able to claim it before both durable effects exist."""
    audit_event = append_audit_event(
        audit_store,
        AppendAuditEventRequest(
            audit_event_id=guard.event_id,
            event_type=event.event_type,
            occurred_at=guard.now,
            actor_id=guard.actor.actor_id,
            actor_type=guard.actor.actor_type,
            target_type=target_type,
            target_id=aggregate_id,
            action=guard.command,
            reason_code=reason_code,
            policy_version=AUDIT_POLICY_VERSION,
            correlation_id=guard.correlation_id,
            source_service=_SOURCE_SERVICE,
            before_hash=before_hash,
            after_hash=after_hash,
        ),
        clock=clock,
    )
    sink.publish(event)
    idempotency_store.put(
        IdempotencyRecord(
            event_id=guard.event_id,
            command=guard.command,
            request_digest=guard.request_digest,
            aggregate_id=aggregate_id,
            recorded_at=guard.now,
        )
    )
    return audit_event


def _replayed_audit(audit_store: AuditEventStore, guard: _CommandGuard) -> AuditEvent:
    """The audit row a replayed command returns.

    A recorded command result without its audit row is a broken
    invariant, not a replay: `_finish` writes the audit row first, so the
    command record cannot exist without it."""
    audit_event = audit_store.get_by_event_id(guard.event_id)
    if audit_event is None:  # pragma: no cover - unreachable through _finish
        raise IdempotencyConflictError(
            f"event_id {guard.event_id} has a recorded command result but no audit entry"
        )
    return audit_event


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
#
# One frozen result per aggregate family, each carrying the new aggregate,
# the canonical `EventEnvelope` and the `AuditEvent` - PACK-07's and
# PACK-09's shape exactly. Commands whose one act produces two governed
# objects (a reversal, a settlement, a correction) carry both, so a caller
# cannot record one half and drop the other.


@dataclass(frozen=True, slots=True)
class FinanceAccountResult:
    account: FinanceAccount
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AccountingPeriodResult:
    period: AccountingPeriod
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PeriodReopeningRequestResult:
    period: AccountingPeriod
    reopening_record: PeriodReopeningRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class JournalEntryResult:
    entry: JournalEntry
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class JournalEntryReversalResult:
    entry: JournalEntry
    reversal: JournalEntry
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class FinancialTransactionResult:
    transaction: FinancialTransaction
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ImportBatchResult:
    batch: ImportBatchRecord
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ContributionResult:
    contribution: FinanceContribution
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SponsorshipResult:
    agreement: SponsorshipAgreement
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ExternalBenefitResult:
    benefit: ExternalFinancialBenefit
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ExpenseClaimResult:
    claim: ExpenseClaim
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PaymentAuthorizationResult:
    authorization: PaymentAuthorization
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PaymentSettlementResult:
    authorization: PaymentAuthorization
    claim: ExpenseClaim | None
    reimbursement: Reimbursement | None
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class FinancialObligationResult:
    obligation: FinancialObligation
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ReportSnapshotResult:
    snapshot: ReportSnapshot
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ReportVersionResult:
    version: FinanceReportVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class CorrectedReportVersionResult:
    superseded: FinanceReportVersion
    successor: FinanceReportVersion
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AuditEngagementResult:
    engagement: AuditEngagement
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PartyHandleResult:
    handle: FinancePartyHandle
    event: EventEnvelope
    audit_event: AuditEvent


def _replayed_aggregate(  # noqa: UP047 - see `_AggregateT`
    getter: Callable[[UUID], _AggregateT | None],
    record: IdempotencyRecord,
    *,
    what: str,
) -> _AggregateT:
    """The aggregate a replayed command returns, without re-attempting the
    transition that produced it.

    A recorded command result pointing at an aggregate that is not there
    is a broken store, not an idempotent replay, and it refuses rather
    than silently re-executing."""
    stored = getter(record.aggregate_id)
    if stored is None:
        raise IdempotencyConflictError(
            f"the recorded result of event_id {record.event_id} names {what} "
            f"{record.aggregate_id}, which is no longer readable"
        )
    return stored


# ---------------------------------------------------------------------------
# Chart of accounts (canon 19f.4)
# ---------------------------------------------------------------------------


def create_finance_account(
    account_store: FinanceAccountStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    account_id: UUID,
    code: str,
    classification_code: str,
    retention: RetentionBinding,
    classification_policy: PolicyBinding | None = None,
) -> FinanceAccountResult:
    """Create a chart-of-accounts node in the caller's own scope.

    The account starts `draft` and is not postable until
    `change_finance_account_status` activates it. `code` is unique within
    the scope and nowhere else - an account belongs to exactly one scope
    and is never shared, so a duplicate code here refuses while the same
    code in another unit is untouched (`ФИН-03`, canon 19f.4). `retention`
    binds the node to a PACK-09 record class; this service expresses no
    retention or legal-hold decision of its own (`ФИН-22`)."""
    scope = context.require_scope()
    if account_store.find_by_code(scope=scope, code=code) is not None:
        raise UnauthorizedStateTransitionError(
            f"finance account code {code!r} is already used in this organizational scope"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="create_finance_account",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(account_id), code, classification_code),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(account_store.get, guard.replay, what="finance account")
        audit_event = _replayed_audit(audit_store, guard)
        return FinanceAccountResult(
            account=stored,
            event=build_finance_account_created_event(
                event_id=guard.event_id,
                account=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    account = FinanceAccount(
        account_id=account_id,
        code=code,
        classification_code=classification_code,
        scope=guard.scope,
        retention=retention,
        status=AccountStatus.DRAFT,
        classification_policy=classification_policy,
    )
    account_store.save(account)
    event = build_finance_account_created_event(
        event_id=guard.event_id,
        account=account,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=account.account_id,
        target_type="finance_account",
        reason_code=_AUDIT_ACCOUNT,
        before_hash="",
        after_hash=_state_hash(finance_account_state_payload(account)),
        clock=clock,
    )
    return FinanceAccountResult(account=account, event=event, audit_event=audit_event)


def change_finance_account_status(
    account_store: FinanceAccountStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    account_id: UUID,
    target_status: AccountStatus,
    reason: ReasonCoded,
    expected_account_version: int | None = None,
) -> FinanceAccountResult:
    """Activate, restrict or close an account (canon 19f.4).

    The permitted transitions live in `ledger._ALLOWED_ACCOUNT_TRANSITIONS`
    and are consulted by the aggregate, so `closed` refuses everything
    rather than partially applying it; `draft` is not a target, because an
    account is never un-activated. The version guarding this command is
    the account's own history length - see `_history_version`."""
    scope = context.require_scope()
    account = _load_scoped(
        account_store.get,
        account_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="finance account",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="change_finance_account_status",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(account_id), str(target_status), reason.reason_code),
        target_scope=account.scope,
        current_version=_history_version(account.history),
        expected_version=expected_account_version,
        version_label="finance account",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(account_store.get, guard.replay, what="finance account")
        audit_event = _replayed_audit(audit_store, guard)
        return FinanceAccountResult(
            account=stored,
            event=build_finance_account_status_changed_event(
                event_id=guard.event_id,
                account=stored,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(finance_account_state_payload(account))
    if target_status is AccountStatus.ACTIVE:
        updated = account.activate(at=guard.now, by_authority=guard.authority, reason=reason)
    elif target_status is AccountStatus.RESTRICTED:
        updated = account.restrict(at=guard.now, by_authority=guard.authority, reason=reason)
    elif target_status is AccountStatus.CLOSED:
        updated = account.close(at=guard.now, by_authority=guard.authority, reason=reason)
    else:
        raise UnauthorizedStateTransitionError(
            f"{target_status!s} is not a reachable finance account status"
        )
    account_store.save(updated)
    event = build_finance_account_status_changed_event(
        event_id=guard.event_id,
        account=updated,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=updated.account_id,
        target_type="finance_account",
        reason_code=_AUDIT_ACCOUNT,
        before_hash=before,
        after_hash=_state_hash(finance_account_state_payload(updated)),
        clock=clock,
    )
    return FinanceAccountResult(account=updated, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Accounting periods (canon 19f.5)
# ---------------------------------------------------------------------------


def open_accounting_period(
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    period_id: UUID,
    label: str,
    timezone_name: str,
    opens_at: datetime,
    closes_at: datetime,
) -> AccountingPeriodResult:
    """Open an accounting period for the caller's scope (canon 19f.5).

    `timezone_name` is a mandatory IANA name and the boundaries must be
    timezone-explicit: a period boundary is a civil-calendar fact, and a
    naive instant is refused rather than assumed to be UTC (`ФИН-39`,
    `ФИН-42`). Overlap with an existing period is refused here rather than
    left to `find_covering`, which would otherwise answer with whichever
    of two overlapping periods it happened to reach first."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="open_accounting_period",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(period_id), label, timezone_name, opens_at.isoformat()),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(period_store.get, guard.replay, what="accounting period")
        audit_event = _replayed_audit(audit_store, guard)
        return AccountingPeriodResult(
            period=stored,
            event=build_accounting_period_opened_event(
                event_id=guard.event_id,
                period=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    period = AccountingPeriod(
        period_id=period_id,
        label=label,
        scope=guard.scope,
        timezone_name=timezone_name,
        opens_at=opens_at,
        closes_at=closes_at,
    )
    for existing in period_store.list_for_scope(scope=guard.scope):
        if existing.opens_at < period.closes_at and period.opens_at < existing.closes_at:
            raise AccountingPeriodUndeterminedError(
                f"accounting period {label} overlaps the existing period {existing.label}; "
                "a moment covered by two periods has no determinable period"
            )
    period_store.save(period)
    event = build_accounting_period_opened_event(
        event_id=guard.event_id,
        period=period,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=period.period_id,
        target_type="accounting_period",
        reason_code=_AUDIT_PERIOD,
        before_hash="",
        after_hash=_state_hash(accounting_period_state_payload(period)),
        clock=clock,
    )
    return AccountingPeriodResult(period=period, event=event, audit_event=audit_event)


def close_accounting_period(
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    period_id: UUID,
    reason: ReasonCoded,
    expected_period_version: int | None = None,
) -> AccountingPeriodResult:
    """Lock the period against ordinary postings (`ФИН-10`).

    The only route back to a postable state is `request_period_reopening`
    followed by `reopen_accounting_period` - dual-controlled,
    reason-coded, and leaving a create-once record (`ФИН-11`). The
    intermediate `closing` state is reachable through
    `AccountingPeriod.begin_closing`; this round exposes no command for
    it, because nothing in the canon requires the freeze to be a separate
    governed act and `close` from `open` is an enumerated transition."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="close_accounting_period",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(period_id), reason.reason_code),
        target_scope=period.scope,
        current_version=_history_version(period.history),
        expected_version=expected_period_version,
        version_label="accounting period",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(period_store.get, guard.replay, what="accounting period")
        audit_event = _replayed_audit(audit_store, guard)
        return AccountingPeriodResult(
            period=stored,
            event=build_accounting_period_closed_event(
                event_id=guard.event_id,
                period=stored,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(accounting_period_state_payload(period))
    closed = period.close(at=guard.now, by_authority=guard.authority, reason=reason)
    period_store.save(closed)
    event = build_accounting_period_closed_event(
        event_id=guard.event_id,
        period=closed,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=closed.period_id,
        target_type="accounting_period",
        reason_code=_AUDIT_PERIOD,
        before_hash=before,
        after_hash=_state_hash(accounting_period_state_payload(closed)),
        clock=clock,
    )
    return AccountingPeriodResult(period=closed, event=event, audit_event=audit_event)


def request_period_reopening(
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    period_id: UUID,
    reopening_record_id: UUID,
    approving_authority: AuthorityReference,
    reason: ReasonCoded,
    policy: PolicyBinding,
    legal_case_reference: str | None = None,
    hold_reference: str | None = None,
    expected_period_version: int | None = None,
) -> PeriodReopeningRequestResult:
    """Build the create-once `PeriodReopeningRecord` a reopening needs
    (`ФИН-11`).

    The caller's own resolved authority is the requester and
    `approving_authority` is the second half of the dual control;
    `ledger.assert_reopening_dual_control`, which
    `PeriodReopeningRecord.__post_init__` runs, refuses the two being one
    authority *or* one actor. Constructing the record **is** the evidence
    that dual control happened, which is why it is a separate act from
    applying it.

    **The record is not stored.** `storage.py` deliberately offers no
    `PeriodReopeningRecordStore`: a reopening record is create-once *on
    the period aggregate*, and a separate table would allow a period whose
    status and whose reopening history disagree. A replay therefore
    answers from `AccountingPeriod.reopening_records` when the reopening
    has already been applied, and otherwise rebuilds the record from the
    same request - which is deterministic, because every input is
    caller-supplied and `closed_state_digest` is a pure function of the
    still-closed period."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="request_period_reopening",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(period_id),
            str(reopening_record_id),
            str(approving_authority.authority_id),
            reason.reason_code,
            policy.policy_version,
        ),
        target_scope=period.scope,
        # No `prior_actor_references` here, deliberately. The frame's
        # generic `assert_not_self_approval` would fire first and refuse
        # with `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`, masking the code
        # canon 19f.13 assigns to exactly this failure:
        # `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED` (`ФИН-11`), raised by
        # `ledger.assert_reopening_dual_control` inside
        # `PeriodReopeningRecord.__post_init__`. Both refuse the same act;
        # the specific code is the one a caller can act on.
        current_version=_history_version(period.history),
        expected_version=expected_period_version,
        version_label="accounting period",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(period_store.get, guard.replay, what="accounting period")
        audit_event = _replayed_audit(audit_store, guard)
        applied = next(
            (
                candidate
                for candidate in stored.reopening_records
                if candidate.record_id == reopening_record_id
            ),
            None,
        )
        replayed_record = (
            applied
            if applied is not None
            else stored.request_reopening(
                record_id=reopening_record_id,
                requested_by=guard.authority,
                approved_by=approving_authority,
                reason=reason,
                policy=policy,
                requested_at=audit_event.occurred_at,
                approved_at=audit_event.occurred_at,
                legal_case_reference=legal_case_reference,
                hold_reference=hold_reference,
            )
        )
        return PeriodReopeningRequestResult(
            period=stored,
            reopening_record=replayed_record,
            event=build_accounting_period_reopening_requested_event(
                event_id=guard.event_id,
                period=stored,
                record=replayed_record,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    record = period.request_reopening(
        record_id=reopening_record_id,
        requested_by=guard.authority,
        approved_by=approving_authority,
        reason=reason,
        policy=policy,
        requested_at=guard.now,
        approved_at=guard.now,
        legal_case_reference=legal_case_reference,
        hold_reference=hold_reference,
    )
    state_hash = _state_hash(accounting_period_state_payload(period))
    event = build_accounting_period_reopening_requested_event(
        event_id=guard.event_id,
        period=period,
        record=record,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=period.period_id,
        target_type="accounting_period",
        reason_code=_AUDIT_PERIOD,
        # The period itself does not change when a reopening is requested,
        # so before and after are the same snapshot. Recording both rather
        # than leaving them empty is what makes the audit row provable
        # against the state the approval was given on (`ФИН-11`).
        before_hash=state_hash,
        after_hash=state_hash,
        clock=clock,
    )
    return PeriodReopeningRequestResult(
        period=period, reopening_record=record, event=event, audit_event=audit_event
    )


def reopen_accounting_period(
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    period_id: UUID,
    reopening_record: PeriodReopeningRecord,
    expected_period_version: int | None = None,
) -> AccountingPeriodResult:
    """Apply a reopening record, moving the period to `reopened`
    (`ФИН-11`).

    Dual control is enforced twice over, and deliberately so: the record
    could not have been constructed without it, and `AccountingPeriod.
    reopen` re-runs `assert_reopening_dual_control` on the record it is
    handed - both refusing with the code canon 19f.13 assigns. The
    approving authority named on the record must also be the one acting
    here - otherwise an approval granted to one authority could be
    exercised by another."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="reopen_accounting_period",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(period_id), str(reopening_record.record_id)),
        target_scope=period.scope,
        # As in `request_period_reopening`: `AccountingPeriod.reopen` re-runs
        # `assert_reopening_dual_control` on the record it is handed and
        # refuses with `FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED`, which is
        # the code canon 19f.13 gives this failure. The frame's generic
        # self-approval check is not wired in here because it would refuse
        # the same act one step earlier under a less specific code.
        current_version=_history_version(period.history),
        expected_version=expected_period_version,
        version_label="accounting period",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(period_store.get, guard.replay, what="accounting period")
        audit_event = _replayed_audit(audit_store, guard)
        return AccountingPeriodResult(
            period=stored,
            event=build_accounting_period_reopened_event(
                event_id=guard.event_id,
                period=stored,
                record=reopening_record,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    if reopening_record.approved_by.authority_id != guard.authority.authority_id:
        raise PeriodReopeningNotAuthorizedError(
            "the reopening must be applied by the authority the record names as approver"
        )
    before = _state_hash(accounting_period_state_payload(period))
    reopened = period.reopen(reopening_record, at=guard.now)
    period_store.save(reopened)
    event = build_accounting_period_reopened_event(
        event_id=guard.event_id,
        period=reopened,
        record=reopening_record,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=reopened.period_id,
        target_type="accounting_period",
        reason_code=_AUDIT_PERIOD,
        before_hash=before,
        after_hash=_state_hash(accounting_period_state_payload(reopened)),
        clock=clock,
    )
    return AccountingPeriodResult(period=reopened, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# The accounting register (canon 19f.4, 19f.6)
# ---------------------------------------------------------------------------


def draft_journal_entry(
    entry_store: JournalEntryStore,
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    entry_id: UUID,
    period_id: UUID,
    lines: tuple[PostingLine, ...],
    reason: ReasonCoded,
    transaction_id: UUID | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
) -> JournalEntryResult:
    """Draft a posting. The balancing rule is enforced at construction, so
    an unbalanced entry cannot exist even as a draft (`ФИН-07`).

    The reporting period is resolved from the stored `AccountingPeriod`
    rather than taken as a caller-supplied reference, so an entry cannot
    name a period that does not exist in its scope. The period lock is
    **not** checked here: a draft has no monetary effect, and `ФИН-10`
    binds the check to the posting command, which re-runs it."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="draft_journal_entry",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(entry_id),
            str(period_id),
            reason.reason_code,
            *(f"{line.account_id}:{line.side}:{line.amount.minor_units}" for line in lines),
        ),
        target_scope=period.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(entry_store.get, guard.replay, what="journal entry")
        audit_event = _replayed_audit(audit_store, guard)
        return JournalEntryResult(
            entry=stored,
            event=build_journal_entry_drafted_event(
                event_id=guard.event_id,
                entry=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    entry = JournalEntry(
        entry_id=entry_id,
        scope=guard.scope,
        period=period.as_reference(),
        lines=lines,
        reason=reason,
        status=EntryStatus.DRAFT,
        transaction_id=transaction_id,
        evidence=evidence,
    )
    entry_store.save(entry)
    event = build_journal_entry_drafted_event(
        event_id=guard.event_id,
        entry=entry,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=entry.entry_id,
        target_type="journal_entry",
        reason_code=_AUDIT_ENTRY,
        before_hash="",
        after_hash=_state_hash(journal_entry_state_payload(entry)),
        clock=clock,
    )
    return JournalEntryResult(entry=entry, event=event, audit_event=audit_event)


def post_journal_entry(
    entry_store: JournalEntryStore,
    period_store: AccountingPeriodStore,
    account_store: FinanceAccountStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    entry_id: UUID,
    expected_entry_version: int | None = None,
) -> JournalEntryResult:
    """Post a draft entry into an open period.

    **The period lock is re-checked here, inside the posting command**
    (`ФИН-10`; canon 19f.5 requires the refusal to happen inside the
    posting command itself, not only at intake). `ledger.post`
    checks it too, and that duplication is deliberate: the canon requires
    the refusal to live in the command, and a future call path that
    reached the aggregate differently must not be able to bypass it.
    `closing` denies exactly as `closed` does.

    The posting sequence is allocated **last**, after every check has
    passed, because a number handed out and then discarded leaves a hole
    in a gap-free sequence - and a hole in a posting sequence is what an
    auditor reads as a removed entry. Each account touched has
    `has_postings` latched, which is what freezes its code and
    classification afterwards (`ФИН-13`)."""
    scope = context.require_scope()
    entry = _load_scoped(
        entry_store.get,
        entry_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="journal entry",
        for_write=True,
    )
    period = _load_scoped(
        period_store.get,
        entry.period.period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="post_journal_entry",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(entry_id),),
        target_scope=entry.scope,
        current_version=_ENTRY_VERSIONS[entry.status],
        expected_version=expected_entry_version,
        version_label="journal entry",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(entry_store.get, guard.replay, what="journal entry")
        audit_event = _replayed_audit(audit_store, guard)
        return JournalEntryResult(
            entry=stored,
            event=build_journal_entry_posted_event(
                event_id=guard.event_id,
                entry=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    # `ФИН-10`, inside the posting command itself.
    period.assert_open_for_posting()
    before = _state_hash(journal_entry_state_payload(entry))
    sequence = entry_store.next_sequence(scope=guard.scope, period_id=period.period_id)
    posted = post(entry, sequence, period=period)
    entry_store.save(posted)
    for line in posted.lines:
        account = account_store.get(line.account_id)
        if account is not None and account.scope.organization_id == guard.scope.organization_id:
            account_store.save(account.mark_first_posting())
    event = build_journal_entry_posted_event(
        event_id=guard.event_id,
        entry=posted,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=posted.entry_id,
        target_type="journal_entry",
        reason_code=_AUDIT_ENTRY,
        before_hash=before,
        after_hash=_state_hash(journal_entry_state_payload(posted)),
        clock=clock,
    )
    return JournalEntryResult(entry=posted, event=event, audit_event=audit_event)


def reverse_journal_entry(
    entry_store: JournalEntryStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    entry_id: UUID,
    reversal_entry_id: UUID,
    reason: ReasonCoded,
    evidence: tuple[EvidenceReference, ...] = (),
    expected_entry_version: int | None = None,
) -> JournalEntryReversalResult:
    """Reverse a posted entry with an equal and opposite new entry
    (`ФИН-06`).

    Both halves of the act are returned and both are stored: the original
    marked `reversed` and the reversal as a **draft**, which is posted
    through `post_journal_entry` and takes its own never-reused
    `entry_sequence`. Nothing about the original's content is rewritten -
    `ledger.reverse` flips each side and leaves each amount alone, so
    reversal by negation, which would be a second representation of the
    same effect, cannot arise."""
    scope = context.require_scope()
    entry = _load_scoped(
        entry_store.get,
        entry_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="journal entry",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="reverse_journal_entry",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(entry_id), str(reversal_entry_id), reason.reason_code),
        target_scope=entry.scope,
        current_version=_ENTRY_VERSIONS[entry.status],
        expected_version=expected_entry_version,
        version_label="journal entry",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(entry_store.get, guard.replay, what="journal entry")
        replayed_reversal = _replayed_aggregate(
            entry_store.get,
            IdempotencyRecord(
                event_id=guard.replay.event_id,
                command=guard.replay.command,
                request_digest=guard.replay.request_digest,
                aggregate_id=reversal_entry_id,
                recorded_at=guard.replay.recorded_at,
            ),
            what="reversing journal entry",
        )
        audit_event = _replayed_audit(audit_store, guard)
        return JournalEntryReversalResult(
            entry=stored,
            reversal=replayed_reversal,
            event=build_journal_entry_reversed_event(
                event_id=guard.event_id,
                entry=stored,
                reversal=replayed_reversal,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(journal_entry_state_payload(entry))
    reversed_entry, reversal = reverse(
        entry,
        entry_id=reversal_entry_id,
        reason=reason,
        evidence=evidence,
        transaction_id=entry.transaction_id,
    )
    entry_store.save(reversed_entry)
    entry_store.save(reversal)
    event = build_journal_entry_reversed_event(
        event_id=guard.event_id,
        entry=reversed_entry,
        reversal=reversal,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=reversed_entry.entry_id,
        target_type="journal_entry",
        reason_code=_AUDIT_ENTRY,
        before_hash=before,
        after_hash=_state_hash(journal_entry_state_payload(reversed_entry)),
        clock=clock,
    )
    return JournalEntryReversalResult(
        entry=reversed_entry, reversal=reversal, event=event, audit_event=audit_event
    )


def correct_journal_entry(
    entry_store: JournalEntryStore,
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    entry_id: UUID,
    correcting_entry_id: UUID,
    replacement_lines: tuple[PostingLine, ...],
    reason: ReasonCoded,
    correction_period_id: UUID | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
) -> JournalEntryResult:
    """Correct a posted entry with a NEW entry linked by
    `corrects_entry_id` (`ФИН-06`).

    The original is left `posted` and untouched: a correction is not a
    reversal, and both links exist precisely so the two acts stay
    distinguishable in the chain. `correction_period_id` lets the
    correction be booked into a later period when the original's has
    closed - which is the governed alternative to reopening one.

    The correcting entry is emitted as `journal_entry.drafted`. Canon
    20.17's seventy-two event types include no `journal_entry.corrected`,
    and inventing a seventy-third is exactly what
    `events.build_finance_event` refuses; the correcting entry *is* a new
    draft, and its later posting emits its own `journal_entry.posted`."""
    scope = context.require_scope()
    target = _load_scoped(
        entry_store.get,
        entry_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="journal entry",
        for_write=True,
    )
    correction_period = (
        None
        if correction_period_id is None
        else _load_scoped(
            period_store.get,
            correction_period_id,
            lambda value: value.scope,
            scope=scope,
            context=context,
            what="accounting period",
            for_write=True,
        )
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="correct_journal_entry",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(entry_id),
            str(correcting_entry_id),
            reason.reason_code,
            *(
                f"{line.account_id}:{line.side}:{line.amount.minor_units}"
                for line in replacement_lines
            ),
        ),
        target_scope=target.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(entry_store.get, guard.replay, what="journal entry")
        audit_event = _replayed_audit(audit_store, guard)
        return JournalEntryResult(
            entry=stored,
            event=build_journal_entry_drafted_event(
                event_id=guard.event_id,
                entry=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    correcting = correct(
        target,
        replacement_lines,
        entry_id=correcting_entry_id,
        reason=reason,
        period=None if correction_period is None else correction_period.as_reference(),
        evidence=evidence,
        transaction_id=target.transaction_id,
    )
    entry_store.save(correcting)
    event = build_journal_entry_drafted_event(
        event_id=guard.event_id,
        entry=correcting,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=correcting.entry_id,
        target_type="journal_entry",
        reason_code=_AUDIT_ENTRY,
        before_hash=_state_hash(journal_entry_state_payload(target)),
        after_hash=_state_hash(journal_entry_state_payload(correcting)),
        clock=clock,
    )
    return JournalEntryResult(entry=correcting, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# The transaction register, provenance and imports (canon 19f.6)
# ---------------------------------------------------------------------------


def record_financial_transaction(
    transaction_store: FinancialTransactionStore,
    period_store: AccountingPeriodStore,
    batch_store: ImportBatchStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    transaction_id: UUID,
    provenance: Provenance,
    transaction_date: date,
    posting_date: date,
    period_id: UUID,
    value_date: date | None = None,
    party_handle_reference: str | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
    internal_transfer_reference: str | None = None,
) -> FinancialTransactionResult:
    """Record a business fact and its provenance (`ФИН-38`).

    An **imported** transaction that names no import batch is refused
    twice over: `FinancialTransaction.__post_init__` rejects the missing
    `import_batch_reference`, and this command additionally requires the
    named batch to be *registered in this scope*, because a batch
    reference nobody can resolve is provenance in name only. A transaction
    whose intake fingerprint already exists in the scope is a duplicate
    and refuses with `FINANCE_DUPLICATE_TRANSACTION` - see
    `storage.transaction_fingerprint` for exactly what that digest can and
    cannot answer."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    if provenance.kind is ProvenanceKind.IMPORTED:
        reference = (provenance.import_batch_reference or "").strip()
        if not reference:
            raise ImportProvenanceMissingError(
                "an imported transaction must name the import batch it arrived in"
            )
        if batch_store.find_by_fingerprint(scope=scope, fingerprint=reference) is None:
            raise ImportProvenanceMissingError(
                f"import batch fingerprint {reference!r} is not registered in this scope; "
                "an unresolvable batch reference is provenance in name only"
            )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_financial_transaction",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(transaction_id),
            str(provenance.kind),
            provenance.source_system_reference,
            provenance.external_reference or "",
            transaction_date.isoformat(),
            posting_date.isoformat(),
        ),
        target_scope=period.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            transaction_store.get, guard.replay, what="financial transaction"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return FinancialTransactionResult(
            transaction=stored,
            event=build_financial_transaction_recorded_event(
                event_id=guard.event_id,
                transaction=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    transaction = FinancialTransaction(
        transaction_id=transaction_id,
        scope=guard.scope,
        provenance=provenance,
        transaction_date=transaction_date,
        posting_date=posting_date,
        recorded_at=guard.now,
        reporting_period=period.as_reference(),
        value_date=value_date,
        party_handle_reference=party_handle_reference,
        evidence=evidence,
        internal_transfer_reference=internal_transfer_reference,
    )
    fingerprint = transaction_fingerprint(transaction)
    existing = transaction_store.find_by_fingerprint(scope=guard.scope, fingerprint=fingerprint)
    if existing is not None and existing.transaction_id != transaction_id:
        raise DuplicateTransactionError(
            f"a transaction with the same intake identity already exists in this scope as "
            f"{existing.transaction_id}"
        )
    transaction_store.save(transaction)
    event = build_financial_transaction_recorded_event(
        event_id=guard.event_id,
        transaction=transaction,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=transaction.transaction_id,
        target_type="financial_transaction",
        reason_code=_AUDIT_TRANSACTION,
        before_hash="",
        after_hash=_state_hash(financial_transaction_state_payload(transaction)),
        clock=clock,
    )
    return FinancialTransactionResult(transaction=transaction, event=event, audit_event=audit_event)


def reclassify_financial_transaction(
    transaction_store: FinancialTransactionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    transaction_id: UUID,
    classification_code: str,
    policy: PolicyBinding,
    current_obligation_references: frozenset[str] = frozenset(),
    resulting_obligation_references: frozenset[str] = frozenset(),
    expected_transaction_version: int | None = None,
) -> FinancialTransactionResult:
    """Classify or reclassify a transaction against a bound policy version
    (`ФИН-13`, `ФИН-23`).

    A reclassification that would **drop** a disclosure, review,
    aggregation or reporting obligation is refused with
    `FINANCE_RECLASSIFICATION_BYPASS_DENIED`: canon 19f.4 and `ФИН-13`
    forbid using reclassification as an escape from an obligation, and
    the check is set-based rather than judgemental - every obligation the
    current classification carries must still be carried afterwards.

    **The two obligation sets arrive as typed arguments, not as something
    this module derives.** Which obligations a classification carries is
    an output of a versioned `FinancePolicy`, and PACK-10 implements no
    policy engine (canon 19f.20); computing them here would be this
    service inventing the policy it is supposed to be bound by. Passing
    them explicitly keeps the refusal checkable and the ignorance
    honest.

    Optimistic concurrency uses `FinancialTransaction.version`, the one
    aggregate in this package that carries an explicit version field; the
    aggregate re-checks it itself in `_check_version`."""
    scope = context.require_scope()
    transaction = _load_scoped(
        transaction_store.get,
        transaction_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="financial transaction",
        for_write=True,
    )
    dropped = current_obligation_references - resulting_obligation_references
    if dropped:
        raise ReclassificationBypassDeniedError(
            "this reclassification would drop the obligation(s) "
            f"{sorted(dropped)}; reclassification never removes a disclosure, review, "
            "aggregation or reporting obligation"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="reclassify_financial_transaction",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(transaction_id), classification_code, policy.policy_version),
        target_scope=transaction.scope,
        current_version=transaction.version,
        expected_version=expected_transaction_version,
        version_label="financial transaction",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            transaction_store.get, guard.replay, what="financial transaction"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return FinancialTransactionResult(
            transaction=stored,
            event=build_financial_transaction_classification_changed_event(
                event_id=guard.event_id,
                transaction=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(financial_transaction_state_payload(transaction))
    classified = transaction.classify(
        classification_code=classification_code,
        policy=policy,
        expected_version=transaction.version,
    )
    transaction_store.save(classified)
    event = build_financial_transaction_classification_changed_event(
        event_id=guard.event_id,
        transaction=classified,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=classified.transaction_id,
        target_type="financial_transaction",
        reason_code=_AUDIT_TRANSACTION,
        before_hash=before,
        after_hash=_state_hash(financial_transaction_state_payload(classified)),
        clock=clock,
    )
    return FinancialTransactionResult(transaction=classified, event=event, audit_event=audit_event)


def register_import_batch(
    batch_store: ImportBatchStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    batch_id: UUID,
    provenance: Provenance,
    fingerprint: str,
    record_count: int = 0,
) -> ImportBatchResult:
    """Register an ingestion act before anything is booked from it
    (`ФИН-38`).

    Registration precedes application on purpose: a crash between the two
    leaves a `registered` row rather than a silently re-appliable file. A
    fingerprint that already reached `applied` in this scope refuses with
    `FINANCE_DUPLICATE_IMPORT` - the store raises it, because the index
    that has to survive two workers racing is a storage concern. Two
    organizations importing byte-identical files do not collide: the index
    is scoped (`ФИН-03`).

    **The authority mapping is weaker than canon 19f.6 asks.** The canon
    says import authority is separate and not implied by posting
    authority; `ACTION_REQUIREMENTS` has no import entry, so this command
    maps onto `post_transaction`. See `_ACTION_FOR_COMMAND`."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="register_import_batch",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(batch_id), fingerprint, provenance.source_system_reference),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(batch_store.get, guard.replay, what="import batch")
        audit_event = _replayed_audit(audit_store, guard)
        return ImportBatchResult(
            batch=stored,
            event=build_import_batch_registered_event(
                event_id=guard.event_id,
                import_batch_id=stored.batch_id,
                scope=stored.scope,
                provenance=stored.provenance,
                batch_fingerprint=stored.fingerprint,
                authority=guard.authority,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    batch = batch_store.register(
        ImportBatchRecord(
            batch_id=batch_id,
            scope=guard.scope,
            provenance=provenance,
            fingerprint=fingerprint,
            registered_at=guard.now,
            record_count=record_count,
        )
    )
    event = build_import_batch_registered_event(
        event_id=guard.event_id,
        import_batch_id=batch.batch_id,
        scope=batch.scope,
        provenance=batch.provenance,
        batch_fingerprint=batch.fingerprint,
        authority=guard.authority,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=batch.batch_id,
        target_type="import_batch",
        reason_code=_AUDIT_IMPORT,
        before_hash="",
        after_hash=_state_hash(
            {
                "import_batch_id": str(batch.batch_id),
                "fingerprint": batch.fingerprint,
                "status": str(batch.status),
                "provenance": batch.provenance.to_payload(),
                "registered_at": batch.registered_at.isoformat(),
            }
        ),
        clock=clock,
    )
    return ImportBatchResult(batch=batch, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Contributions (canon 19f.7, 19f.8)
# ---------------------------------------------------------------------------


def record_contribution(
    contribution_store: FinanceContributionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    contribution_id: UUID,
    receipt: ContributionReceipt,
    retention: RetentionBinding,
) -> ContributionResult:
    """Record a contribution receipt (canon 19f.7).

    The receipt is create-once and every later act is a decision recorded
    *around* it; `records.assert_receipt_unchanged` runs on every
    transition, so "rejection, return and escalation leave the receipt
    unchanged" (`ФИН-17`) is a checked property rather than a convention.
    A receipt whose contributor could not be established carries `None`
    and is not an error here: it is the fact that quarantines the
    contribution at assessment (`ФИН-16`)."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_contribution",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(contribution_id),
            str(receipt.receipt_id),
            str(receipt.kind),
            receipt.received_at.isoformat(),
        ),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(contribution_store.get, guard.replay, what="contribution")
        audit_event = _replayed_audit(audit_store, guard)
        return ContributionResult(
            contribution=stored,
            event=build_finance_contribution_received_event(
                event_id=guard.event_id,
                contribution=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    contribution = FinanceContribution(
        contribution_id=contribution_id,
        scope=guard.scope,
        receipt=receipt,
        retention=retention,
        conflict=context.conflict,
    )
    contribution_store.save(contribution)
    event = build_finance_contribution_received_event(
        event_id=guard.event_id,
        contribution=contribution,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=contribution.contribution_id,
        target_type="finance_contribution",
        reason_code=_AUDIT_CONTRIBUTION,
        before_hash="",
        after_hash=_state_hash(finance_contribution_state_payload(contribution)),
        clock=clock,
    )
    return ContributionResult(contribution=contribution, event=event, audit_event=audit_event)


def assess_contribution(
    contribution_store: FinanceContributionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    contribution_id: UUID,
    assessment_id: UUID,
    window_start: datetime,
    window_end: datetime,
    policy: PolicyBinding,
    classification_code: str,
    source_determined: bool,
    verification_complete: bool,
    reason: ReasonCoded,
    prohibited: bool = False,
    related_party_group_reference: str | None = None,
    intermediary_declaration_reference: str | None = None,
    expected_contribution_version: int | None = None,
) -> ContributionResult:
    """Assess a contribution against the aggregate over its policy window
    (`ФИН-14`, `ФИН-15`).

    Threshold evaluation runs on the **aggregate**, never on one gift
    (canon 19f.8): the window query sums every contribution the same
    purpose-scoped handle made in `[window_start, window_end)`, so six
    payments below a threshold are visible as one figure. The resolved
    aggregate is frozen into `aggregation_snapshot_digest`, which is what
    stops a later policy change from rewriting a past decision (`ФИН-23`).

    **An unresolvable aggregate refuses** with
    `FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED`. Two cases reach it: a
    receipt whose contributor could not be established has no aggregation
    key at all - it is not "somebody else's", it is unattributed, and
    aggregating it to a stranger would be worse than refusing; and a
    contribution whose receipt instant falls outside the presented window
    means the window is the wrong one, not that the aggregate is empty.

    An assessment that is not *resolved* does not produce an `assessed`
    contribution - `FinanceContribution.assess` quarantines it instead,
    so the record never sits in a state from which acceptance looks
    routine while its source or verification is still open (`ФИН-16`)."""
    scope = context.require_scope()
    contribution = _load_scoped(
        contribution_store.get,
        contribution_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="contribution",
        for_write=True,
    )
    handle_reference = contribution.receipt.contributor_handle_reference
    if handle_reference is None:
        raise ContributionAggregationUnresolvedError(
            f"contribution {contribution_id} names no contributor handle, so no aggregate over "
            "the policy period and perimeter can be resolved"
        )
    if not window_start <= contribution.receipt.received_at < window_end:
        raise ContributionAggregationUnresolvedError(
            f"contribution {contribution_id} was received outside the presented aggregation "
            "window; the aggregate the threshold would be taken on is not this one"
        )
    aggregated = contribution_store.list_for_party_in_window(
        scope=scope,
        party_handle_reference=handle_reference,
        window_start=window_start,
        window_end=window_end,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="assess_contribution",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(contribution_id),
            str(assessment_id),
            window_start.isoformat(),
            window_end.isoformat(),
            classification_code,
            policy.policy_version,
            str(source_determined),
            str(verification_complete),
            str(prohibited),
        ),
        target_scope=contribution.scope,
        current_version=_history_version(contribution.history),
        expected_version=expected_contribution_version,
        version_label="contribution",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(contribution_store.get, guard.replay, what="contribution")
        audit_event = _replayed_audit(audit_store, guard)
        return ContributionResult(
            contribution=stored,
            event=_contribution_state_event(
                stored,
                guard,
                reason=reason,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    digest = deterministic_digest(
        handle_reference,
        "|",
        window_start.isoformat(),
        "|",
        window_end.isoformat(),
        "|",
        policy.policy_kind,
        ":",
        policy.policy_version,
        "|",
        *sorted(
            f"{candidate.contribution_id}:"
            f"{'' if candidate.receipt.amount is None else candidate.receipt.amount.minor_units}"
            for candidate in aggregated
        ),
        "|",
        related_party_group_reference or "",
        "|",
        intermediary_declaration_reference or "",
    )
    assessment = ContributionAssessment(
        assessment_id=assessment_id,
        assessed_at=guard.now,
        assessed_by=guard.authority,
        source_determined=source_determined,
        verification_complete=verification_complete,
        prohibited=prohibited,
        classification_code=classification_code,
        policy=policy,
        aggregation_snapshot_digest=digest,
        related_party_group_reference=related_party_group_reference,
        intermediary_declaration_reference=intermediary_declaration_reference,
    )
    before = _state_hash(finance_contribution_state_payload(contribution))
    assessed = contribution.assess(
        assessment,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            policy=policy,
            conflict=context.conflict,
        ),
    )
    contribution_store.save(assessed)
    event = _contribution_state_event(assessed, guard, reason=reason, occurred_at=guard.now)
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=assessed.contribution_id,
        target_type="finance_contribution",
        reason_code=_AUDIT_CONTRIBUTION,
        before_hash=before,
        after_hash=_state_hash(finance_contribution_state_payload(assessed)),
        clock=clock,
    )
    return ContributionResult(contribution=assessed, event=event, audit_event=audit_event)


def _contribution_state_event(
    contribution: FinanceContribution,
    guard: _CommandGuard,
    *,
    reason: ReasonCoded,
    occurred_at: datetime,
) -> EventEnvelope:
    """The canonical envelope for the state a contribution decision landed
    in.

    Chosen from the resulting state rather than from the caller's
    intention, because `FinanceContribution.assess` may legitimately
    quarantine what was submitted as an assessment (`ФИН-16`), and an
    event claiming `assessed` for a quarantined record would be the
    stream disagreeing with the register."""
    assessment = contribution.assessment
    if contribution.state is ContributionState.ASSESSED and assessment is not None:
        return build_finance_contribution_assessed_event(
            event_id=guard.event_id,
            contribution=contribution,
            assessment=assessment,
            actor=guard.actor,
            correlation_id=guard.correlation_id,
            causation_id=guard.causation_id,
            occurred_at=occurred_at,
        )
    if contribution.state is ContributionState.ACCEPTED:
        builder = build_finance_contribution_accepted_event
    elif contribution.state is ContributionState.REJECTED:
        builder = build_finance_contribution_rejected_event
    elif contribution.state is ContributionState.RETURN_REQUIRED:
        builder = build_finance_contribution_return_required_event
    else:
        builder = build_finance_contribution_quarantined_event
    return builder(
        event_id=guard.event_id,
        contribution=contribution,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=occurred_at,
    )


def decide_contribution(
    contribution_store: FinanceContributionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    contribution_id: UUID,
    decision: ContributionState,
    reason: ReasonCoded,
    policy: PolicyBinding | None = None,
    expected_contribution_version: int | None = None,
) -> ContributionResult:
    """Accept, reject or require the return of an assessed contribution
    (`ФИН-17`).

    `received` -> `accepted` is not reachable and never becomes reachable:
    the transition table holds no such edge, so acceptance always follows
    a resolved, policy-bound assessment. Acceptance asks its refusals in
    order, each with its own code - assessment present, source
    established, verification complete, classification policy-bound, not
    prohibited, no open return obligation, conflict declared - and the
    receipt is untouched whichever way the decision goes."""
    scope = context.require_scope()
    contribution = _load_scoped(
        contribution_store.get,
        contribution_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="contribution",
        for_write=True,
    )
    if decision not in (
        ContributionState.ACCEPTED,
        ContributionState.REJECTED,
        ContributionState.RETURN_REQUIRED,
    ):
        raise UnauthorizedStateTransitionError(
            f"{decision!s} is not a contribution decision this command takes"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="decide_contribution",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(contribution_id), str(decision), reason.reason_code),
        target_scope=contribution.scope,
        current_version=_history_version(contribution.history),
        expected_version=expected_contribution_version,
        version_label="contribution",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(contribution_store.get, guard.replay, what="contribution")
        audit_event = _replayed_audit(audit_store, guard)
        return ContributionResult(
            contribution=stored,
            event=_contribution_state_event(
                stored, guard, reason=reason, occurred_at=audit_event.occurred_at
            ),
            audit_event=audit_event,
        )

    act = GovernedAct(
        at=guard.now,
        by_authority=guard.authority,
        reason=reason,
        policy=policy,
        conflict=context.conflict,
    )
    before = _state_hash(finance_contribution_state_payload(contribution))
    if decision is ContributionState.ACCEPTED:
        decided = contribution.accept(act)
    elif decision is ContributionState.REJECTED:
        decided = contribution.reject(act)
    else:
        decided = contribution.require_return(act)
    contribution_store.save(decided)
    event = _contribution_state_event(decided, guard, reason=reason, occurred_at=guard.now)
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=decided.contribution_id,
        target_type="finance_contribution",
        reason_code=_AUDIT_CONTRIBUTION,
        before_hash=before,
        after_hash=_state_hash(finance_contribution_state_payload(decided)),
        clock=clock,
    )
    return ContributionResult(contribution=decided, event=event, audit_event=audit_event)


def return_contribution(
    contribution_store: FinanceContributionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    contribution_id: UUID,
    reason: ReasonCoded,
    payment_authorization_id: UUID | None = None,
    expected_contribution_version: int | None = None,
) -> ContributionResult:
    """Record the completed return of a contribution (canon 19f.7).

    The contribution stays in the register as one that *was* received: a
    returned contribution is never treated as never received, and its
    receipt is untouched (`ФИН-17`). `payment_authorization_id` cites the
    authorization the outward payment ran under, where one exists - the
    return itself is a payment and is authorised like any other."""
    scope = context.require_scope()
    contribution = _load_scoped(
        contribution_store.get,
        contribution_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="contribution",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="return_contribution",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(contribution_id),
            reason.reason_code,
            str(payment_authorization_id or ""),
        ),
        target_scope=contribution.scope,
        current_version=_history_version(contribution.history),
        expected_version=expected_contribution_version,
        version_label="contribution",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(contribution_store.get, guard.replay, what="contribution")
        audit_event = _replayed_audit(audit_store, guard)
        return ContributionResult(
            contribution=stored,
            event=build_finance_contribution_returned_event(
                event_id=guard.event_id,
                contribution=stored,
                payment_authorization_id=payment_authorization_id,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(finance_contribution_state_payload(contribution))
    returned = contribution.mark_returned(
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        )
    )
    contribution_store.save(returned)
    event = build_finance_contribution_returned_event(
        event_id=guard.event_id,
        contribution=returned,
        payment_authorization_id=payment_authorization_id,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=returned.contribution_id,
        target_type="finance_contribution",
        reason_code=_AUDIT_CONTRIBUTION,
        before_hash=before,
        after_hash=_state_hash(finance_contribution_state_payload(returned)),
        clock=clock,
    )
    return ContributionResult(contribution=returned, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Sponsorship and external financial benefit (canon 19f.9)
# ---------------------------------------------------------------------------


def register_sponsorship(
    agreement_store: SponsorshipAgreementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    agreement: SponsorshipAgreement,
) -> SponsorshipResult:
    """Register a sponsorship agreement in the caller's scope.

    The aggregate is taken whole rather than assembled from a dozen
    keyword arguments: `SponsorshipAgreement.__post_init__` already
    refuses an agreement with neither a monetary value nor an in-kind
    valuation and a sponsor reference that is not an opaque handle, and
    re-listing its fields here would put the same construction rules in
    two places. Its scope must be the caller's - `_guard` re-asserts
    that."""
    agreement.scope.assert_matches(context.require_scope())
    guard = _guard(
        idempotency_store,
        audit_store,
        command="register_sponsorship",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(agreement.agreement_id),
            agreement.sponsor_handle_reference,
            agreement.period_start.isoformat(),
            agreement.period_end.isoformat(),
        ),
        target_scope=agreement.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            agreement_store.get, guard.replay, what="sponsorship agreement"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return SponsorshipResult(
            agreement=stored,
            event=build_sponsorship_registered_event(
                event_id=guard.event_id,
                agreement=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )
    if agreement.review_state is not SponsorshipState.REGISTERED:
        raise UnauthorizedStateTransitionError(
            f"a sponsorship agreement is registered in the {SponsorshipState.REGISTERED!s} state, "
            f"not {agreement.review_state!s}"
        )

    agreement_store.save(agreement)
    event = build_sponsorship_registered_event(
        event_id=guard.event_id,
        agreement=agreement,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=agreement.agreement_id,
        target_type="sponsorship_agreement",
        reason_code=_AUDIT_SPONSORSHIP,
        before_hash="",
        after_hash=_state_hash(sponsorship_state_payload(agreement)),
        clock=clock,
    )
    return SponsorshipResult(agreement=agreement, event=event, audit_event=audit_event)


def approve_sponsorship(
    agreement_store: SponsorshipAgreementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    agreement_id: UUID,
    reason: ReasonCoded,
    policy: PolicyBinding | None = None,
    expected_agreement_version: int | None = None,
) -> SponsorshipResult:
    """Approve a sponsorship agreement (`ФИН-19`).

    Refused unless a counter-performance is recorded **or**
    `counter_performance_absent_policy_binding` names the policy version
    that classified this agreement as one without: the difference between
    sponsorship and a donation is the counter-performance, and it is never
    inferred from the amount or from who paid (canon 19f.9). A registered
    agreement is moved through `under_review` first, because approval must
    come out of a review - two history entries for one governed act, which
    is what the append-only history is for."""
    scope = context.require_scope()
    agreement = _load_scoped(
        agreement_store.get,
        agreement_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="sponsorship agreement",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="approve_sponsorship",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(agreement_id), reason.reason_code),
        target_scope=agreement.scope,
        current_version=_history_version(agreement.history),
        expected_version=expected_agreement_version,
        version_label="sponsorship agreement",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            agreement_store.get, guard.replay, what="sponsorship agreement"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return SponsorshipResult(
            agreement=stored,
            event=build_sponsorship_approved_event(
                event_id=guard.event_id,
                agreement=stored,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    act = GovernedAct(
        at=guard.now,
        by_authority=guard.authority,
        reason=reason,
        policy=policy,
        conflict=context.conflict,
    )
    before = _state_hash(sponsorship_state_payload(agreement))
    reviewed = (
        agreement.begin_review(act)
        if agreement.review_state is SponsorshipState.REGISTERED
        else agreement
    )
    approved = reviewed.approve(act)
    agreement_store.save(approved)
    event = build_sponsorship_approved_event(
        event_id=guard.event_id,
        agreement=approved,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=approved.agreement_id,
        target_type="sponsorship_agreement",
        reason_code=_AUDIT_SPONSORSHIP,
        before_hash=before,
        after_hash=_state_hash(sponsorship_state_payload(approved)),
        clock=clock,
    )
    return SponsorshipResult(agreement=approved, event=event, audit_event=audit_event)


def record_external_financial_benefit(
    benefit_store: ExternalFinancialBenefitStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    benefit_id: UUID,
    benefit_type: ExternalBenefitType,
    retention: RetentionBinding,
    subject_kind: str = "financial_benefit",
    value: Money | None = None,
    in_kind_valuation: InKindValuation | None = None,
    provider_handle_reference: str | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
) -> ExternalBenefitResult:
    """Record a financially measurable benefit received without an
    agreement (canon 19f.9).

    **A PACK-35 subject refuses before anything is written** (`ФИН-20`).
    `records.assert_not_lobbying_subject` is called here, ahead of the
    guard's authority resolution and ahead of every store call, as well as
    inside the aggregate's constructor: PACK-10 implements none of
    PACK-35's entities, and a benefit record bent into a meeting log would
    be that implementation arriving by the back door. The refusal is a
    forbidden *transition*, not an identity leak and not a missing
    disclosure - see that function for why it carries that code.

    A benefit with neither a value nor an in-kind valuation is refused by
    the aggregate: an unvalued benefit has no financial value to report
    (`ФИН-18`)."""
    scope = context.require_scope()
    assert_not_lobbying_subject(subject_kind)
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_external_financial_benefit",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(benefit_id), str(benefit_type), subject_kind),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            benefit_store.get, guard.replay, what="external financial benefit"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return ExternalBenefitResult(
            benefit=stored,
            event=build_external_financial_benefit_recorded_event(
                event_id=guard.event_id,
                benefit=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    benefit = ExternalFinancialBenefit(
        benefit_id=benefit_id,
        scope=guard.scope,
        benefit_type=benefit_type,
        retention=retention,
        subject_kind=subject_kind,
        value=value,
        in_kind_valuation=in_kind_valuation,
        provider_handle_reference=provider_handle_reference,
        evidence=evidence,
    )
    benefit_store.save(benefit)
    event = build_external_financial_benefit_recorded_event(
        event_id=guard.event_id,
        benefit=benefit,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=benefit.benefit_id,
        target_type="external_financial_benefit",
        reason_code=_AUDIT_BENEFIT,
        before_hash="",
        after_hash=_state_hash(external_benefit_state_payload(benefit)),
        clock=clock,
    )
    return ExternalBenefitResult(benefit=benefit, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Expenses, payments and positions (canon 19f.10, 19f.11)
# ---------------------------------------------------------------------------


def submit_expense_claim(
    claim_store: ExpenseClaimStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    claim_id: UUID,
    claimant_handle_reference: str,
    purpose_class: str,
    amount: Money,
    retention: RetentionBinding,
    evidence: tuple[EvidenceReference, ...] = (),
) -> ExpenseClaimResult:
    """Submit an expense claim.

    The claimant appears only as a purpose-scoped `fph:` handle
    reference - `ExpenseClaim.__post_init__` refuses anything else
    (`ФИН-01`). Review, approval, authorisation and execution are four
    later acts by four different authorities, and the claimant performs
    none of them (`ФИН-31`)."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="submit_expense_claim",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(claim_id),
            claimant_handle_reference,
            purpose_class,
            str(amount.minor_units),
            amount.currency,
        ),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(claim_store.get, guard.replay, what="expense claim")
        audit_event = _replayed_audit(audit_store, guard)
        return ExpenseClaimResult(
            claim=stored,
            event=build_expense_claim_submitted_event(
                event_id=guard.event_id,
                claim=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    claim = ExpenseClaim(
        claim_id=claim_id,
        scope=guard.scope,
        claimant_handle_reference=claimant_handle_reference,
        purpose_class=purpose_class,
        amount=amount,
        retention=retention,
        evidence=evidence,
    )
    claim_store.save(claim)
    event = build_expense_claim_submitted_event(
        event_id=guard.event_id,
        claim=claim,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=claim.claim_id,
        target_type="expense_claim",
        reason_code=_AUDIT_CLAIM,
        before_hash="",
        after_hash=_state_hash(expense_claim_state_payload(claim)),
        clock=clock,
    )
    return ExpenseClaimResult(claim=claim, event=event, audit_event=audit_event)


def approve_expense_claim(
    claim_store: ExpenseClaimStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    claim_id: UUID,
    reason: ReasonCoded,
    policy: PolicyBinding | None = None,
    expected_claim_version: int | None = None,
) -> ExpenseClaimResult:
    """Review and approve an expense claim (`ФИН-31`, `ФИН-32`).

    **The claimant may not review, approve, authorise or execute their own
    claim.** That is checked twice: `_guard` compares the acting
    authority's actor reference with the claimant's handle through
    `assert_not_self_approval`, and every `ExpenseClaim` transition runs
    `records.assert_not_self_acting` first, blind to role - holding
    `payment_authorizer` does not make self-payment lawful.

    A submitted claim is moved through `under_review` in the same act,
    because approval must come out of a review; both transitions append
    their own history entry and both run the self-acting check. An
    undeclared or blocking conflict refuses independently (`ФИН-32`)."""
    scope = context.require_scope()
    claim = _load_scoped(
        claim_store.get,
        claim_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="expense claim",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="approve_expense_claim",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(claim_id), reason.reason_code),
        target_scope=claim.scope,
        prior_actor_references=(claim.claimant_handle_reference,),
        current_version=_history_version(claim.history),
        expected_version=expected_claim_version,
        version_label="expense claim",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(claim_store.get, guard.replay, what="expense claim")
        audit_event = _replayed_audit(audit_store, guard)
        return ExpenseClaimResult(
            claim=stored,
            event=build_expense_claim_approved_event(
                event_id=guard.event_id,
                claim=stored,
                policy=policy,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    act = GovernedAct(
        at=guard.now,
        by_authority=guard.authority,
        reason=reason,
        policy=policy,
        conflict=context.conflict,
    )
    before = _state_hash(expense_claim_state_payload(claim))
    reviewed = claim.review(act) if claim.state is ExpenseClaimState.SUBMITTED else claim
    approved = reviewed.approve(act)
    claim_store.save(approved)
    event = build_expense_claim_approved_event(
        event_id=guard.event_id,
        claim=approved,
        policy=policy,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=approved.claim_id,
        target_type="expense_claim",
        reason_code=_AUDIT_CLAIM,
        before_hash=before,
        after_hash=_state_hash(expense_claim_state_payload(approved)),
        clock=clock,
    )
    return ExpenseClaimResult(claim=approved, event=event, audit_event=audit_event)


def authorize_payment(
    authorization_store: PaymentAuthorizationStore,
    claim_store: ExpenseClaimStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    authorization_id: UUID,
    payable_kind: str,
    payable_reference: UUID,
    amount: Money,
    reason: ReasonCoded,
    payee_handle_reference: str | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
) -> PaymentAuthorizationResult:
    """Authorise a payment for one governed payable (canon 19f.10).

    A create-once record, separate from the claim precisely because
    authorising and executing must be separable acts and because
    obligations, contribution returns and other payables need the same
    shape. The payable is named by a typed `(payable_kind,
    payable_reference)` pair, never a free string.

    Where the payable is an expense claim, the claim is bound to this
    authorization in the same act, which is what makes settlement without
    an authorization structurally impossible rather than merely
    discouraged (`ФИН-31`). Binding runs
    `records.assert_not_self_acting` against the claimant, so the
    claimant cannot authorise their own payment."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="authorize_payment",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(authorization_id),
            payable_kind,
            str(payable_reference),
            str(amount.minor_units),
            amount.currency,
        ),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            authorization_store.get, guard.replay, what="payment authorization"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return PaymentAuthorizationResult(
            authorization=stored,
            event=build_payment_authorized_event(
                event_id=guard.event_id,
                authorization=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    authorization = PaymentAuthorization(
        authorization_id=authorization_id,
        scope=guard.scope,
        payable_kind=payable_kind,
        payable_reference=payable_reference,
        authorising_authority=guard.authority,
        amount=amount,
        authorized_at=guard.now,
        reason=reason,
        payee_handle_reference=payee_handle_reference,
        evidence=evidence,
    )
    if payable_kind == "expense_claim":
        claim = _load_scoped(
            claim_store.get,
            payable_reference,
            lambda value: value.scope,
            scope=guard.scope,
            context=context,
            what="expense claim",
            for_write=True,
        )
        claim_store.save(
            claim.authorize_payment(
                authorization,
                GovernedAct(
                    at=guard.now,
                    by_authority=guard.authority,
                    reason=reason,
                    conflict=context.conflict,
                ),
            )
        )
    authorization_store.save(authorization)
    event = build_payment_authorized_event(
        event_id=guard.event_id,
        authorization=authorization,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=authorization.authorization_id,
        target_type="payment_authorization",
        reason_code=_AUDIT_PAYMENT,
        before_hash="",
        after_hash=_state_hash(payment_authorization_state_payload(authorization)),
        clock=clock,
    )
    return PaymentAuthorizationResult(
        authorization=authorization, event=event, audit_event=audit_event
    )


def settle_payment(
    authorization_store: PaymentAuthorizationStore,
    claim_store: ExpenseClaimStore,
    reimbursement_store: ReimbursementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    authorization_id: UUID | None,
    reimbursement_id: UUID | None = None,
    reason: ReasonCoded | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
    expected_authorization_version: int | None = None,
) -> PaymentSettlementResult:
    """Execute an authorised payment (`ФИН-31`, `ФИН-33`).

    **The executor must differ from the authorizer**, by authority id and
    by actor reference, and both comparisons refuse - a dual-control rule
    one person can satisfy alone is not one. The check runs twice: in
    `_guard`, against the authorising actor, and again in
    `PaymentAuthorization.execute`.

    **Settlement with no valid authorization refuses with
    `FINANCE_PAYMENT_AUTHORIZATION_MISSING`.** All four ways of not having
    one answer identically - no id presented, an id naming nothing, an id
    naming another scope's authorization, and an authorization already
    executed or revoked - which is both the canon's refusal (19f.10,
    INV-08) and, for the foreign-scope case, non-disclosing: the caller
    cannot tell existence from absence.

    Where the payable is an expense claim, the claim is settled and a
    create-once `Reimbursement` is written in the same act: the payout is
    a fact in its own right, not a derived reading of the claim's
    state."""
    scope = context.require_scope()
    if authorization_id is None:
        raise PaymentAuthorizationMissingError(
            "settlement requires a valid payment authorization; none was presented"
        )
    authorization = authorization_store.get(authorization_id)
    if (
        authorization is None
        or authorization.scope.organization_id != scope.organization_id
        or not authorization.is_executable
    ):
        raise PaymentAuthorizationMissingError(
            f"payment authorization {authorization_id} is not a valid, executable authorization "
            "in this organizational scope"
        )
    settlement_reason = reason if reason is not None else authorization.reason
    guard = _guard(
        idempotency_store,
        audit_store,
        command="settle_payment",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(authorization_id), str(reimbursement_id or "")),
        target_scope=authorization.scope,
        prior_actor_references=(authorization.authorising_authority.actor_reference,),
        current_version=_AUTHORIZATION_VERSIONS[authorization.state],
        expected_version=expected_authorization_version,
        version_label="payment authorization",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            authorization_store.get, guard.replay, what="payment authorization"
        )
        audit_event = _replayed_audit(audit_store, guard)
        replayed_claim = (
            claim_store.get(stored.payable_reference)
            if stored.payable_kind == "expense_claim"
            else None
        )
        return PaymentSettlementResult(
            authorization=stored,
            claim=replayed_claim,
            reimbursement=reimbursement_store.find_for_claim(
                scope=guard.scope, claim_id=stored.payable_reference
            ),
            event=build_payment_settled_event(
                event_id=guard.event_id,
                authorization=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(payment_authorization_state_payload(authorization))
    executed = authorization.execute(guard.authority, at=guard.now)
    settled_claim: ExpenseClaim | None = None
    reimbursement: Reimbursement | None = None
    if executed.payable_kind == "expense_claim":
        claim = _load_scoped(
            claim_store.get,
            executed.payable_reference,
            lambda value: value.scope,
            scope=guard.scope,
            context=context,
            what="expense claim",
            for_write=True,
        )
        settled_claim = claim.settle(
            GovernedAct(
                at=guard.now,
                by_authority=guard.authority,
                reason=settlement_reason,
                conflict=context.conflict,
            )
        )
        claim_store.save(settled_claim)
        if reimbursement_id is not None:
            reimbursement = Reimbursement(
                reimbursement_id=reimbursement_id,
                scope=guard.scope,
                claim_id=settled_claim.claim_id,
                authorization_id=executed.authorization_id,
                amount=executed.amount,
                settled_at=guard.now,
                executed_by=guard.authority,
                evidence=evidence,
            )
            reimbursement_store.save(reimbursement)
    authorization_store.save(executed)
    event = build_payment_settled_event(
        event_id=guard.event_id,
        authorization=executed,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=executed.authorization_id,
        target_type="payment_authorization",
        reason_code=_AUDIT_PAYMENT,
        before_hash=before,
        after_hash=_state_hash(payment_authorization_state_payload(executed)),
        clock=clock,
    )
    return PaymentSettlementResult(
        authorization=executed,
        claim=settled_claim,
        reimbursement=reimbursement,
        event=event,
        audit_event=audit_event,
    )


def record_financial_obligation(
    obligation_store: FinancialObligationStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    obligation_id: UUID,
    obligation_type: ObligationType,
    amount: Money,
    valuation_date: date,
    method_reference: str,
    retention: RetentionBinding,
    reason: ReasonCoded,
    counterparty_handle_reference: str | None = None,
    evidence: tuple[EvidenceReference, ...] = (),
) -> FinancialObligationResult:
    """Record a receivable, payable, loan, credit, guarantee, contingent
    or long-term obligation (canon 19f.11).

    One aggregate covers every liability shape - `obligation_type` is the
    difference, and a separate `Liability` entity would duplicate an
    identical lifecycle and valuation model. A valuation with no named
    method is refused: an unexplained carrying value is
    indistinguishable from an unrecorded write-off."""
    scope = context.require_scope()
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_financial_obligation",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(obligation_id),
            str(obligation_type),
            str(amount.minor_units),
            amount.currency,
            valuation_date.isoformat(),
        ),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            obligation_store.get, guard.replay, what="financial obligation"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return FinancialObligationResult(
            obligation=stored,
            event=build_financial_obligation_recorded_event(
                event_id=guard.event_id,
                obligation=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    obligation = FinancialObligation.record(
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        obligation_id=obligation_id,
        scope=guard.scope,
        obligation_type=obligation_type,
        amount=amount,
        valuation_date=valuation_date,
        method_reference=method_reference,
        retention=retention,
        counterparty_handle_reference=counterparty_handle_reference,
        evidence=evidence,
    )
    obligation_store.save(obligation)
    event = build_financial_obligation_recorded_event(
        event_id=guard.event_id,
        obligation=obligation,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=obligation.obligation_id,
        target_type="financial_obligation",
        reason_code=_AUDIT_OBLIGATION,
        before_hash="",
        after_hash=_state_hash(financial_obligation_state_payload(obligation)),
        clock=clock,
    )
    return FinancialObligationResult(obligation=obligation, event=event, audit_event=audit_event)


def write_off_financial_obligation(
    obligation_store: FinancialObligationStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    obligation_id: UUID,
    approving_authority: AuthorityReference,
    reason: ReasonCoded,
    legal_case_reference: str | None = None,
    expected_obligation_version: int | None = None,
) -> FinancialObligationResult:
    """Write an obligation off, under authority and dual control
    (`FINANCE_WRITE_OFF_NOT_AUTHORIZED`, canon 19f.11).

    A write-off removes value from the books, so it needs both a named
    authority and a recorded reason - `records.assert_write_off_authorized`
    refuses a bare state change - and, here, a **second** authority that
    is neither the same assignment nor the same actor as the one acting;
    both comparisons refuse with `FINANCE_WRITE_OFF_NOT_AUTHORIZED`.
    Canon 19f.11 makes dual control a policy threshold; this command
    applies it unconditionally, which is stricter and never softer. The
    role gate is separate and additive: `_ACTION_FOR_COMMAND` maps this
    command onto `write_off_position`, which exists in
    `ACTION_REQUIREMENTS` precisely so that recording a debt and erasing
    one are not the same privilege. An earlier draft of this docstring
    described the dual control as compensating for the absence of that
    entry; the entry exists, and the two checks answer different
    questions - who may write off at all, and whether one actor may do
    it alone.

    A contingent liability an open PACK-09 case still concerns must cite
    that case; the aggregate refuses without it (`ФИН-22`)."""
    scope = context.require_scope()
    obligation = _load_scoped(
        obligation_store.get,
        obligation_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="financial obligation",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="write_off_financial_obligation",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(obligation_id),
            str(approving_authority.authority_id),
            reason.reason_code,
            legal_case_reference or "",
        ),
        target_scope=obligation.scope,
        # No `prior_actor_references`: the dual-control refusal for a
        # write-off is `FINANCE_WRITE_OFF_NOT_AUTHORIZED` (canon 19f.11),
        # and the frame's generic self-approval check would mask it with
        # `CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED`. The check below does
        # the same comparison and carries the right code.
        current_version=_history_version(obligation.history),
        expected_version=expected_obligation_version,
        version_label="financial obligation",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(
            obligation_store.get, guard.replay, what="financial obligation"
        )
        audit_event = _replayed_audit(audit_store, guard)
        return FinancialObligationResult(
            obligation=stored,
            event=build_financial_obligation_written_off_event(
                event_id=guard.event_id,
                obligation=stored,
                authority=guard.authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    approving_actor = approving_authority.actor_reference.strip()
    acting_actor = guard.authority.actor_reference.strip()
    if approving_authority.authority_id == guard.authority.authority_id or (
        approving_actor and acting_actor and approving_actor == acting_actor
    ):
        raise WriteOffNotAuthorizedError(
            "a write-off needs a second, distinct approving authority - dual control one "
            "authority or one actor can satisfy alone is not dual control"
        )
    obligation.scope.assert_matches(approving_authority.scope)
    before = _state_hash(financial_obligation_state_payload(obligation))
    written_off = obligation.write_off(
        at=guard.now,
        by_authority=guard.authority,
        reason=reason,
        legal_case_reference=legal_case_reference,
    )
    obligation_store.save(written_off)
    event = build_financial_obligation_written_off_event(
        event_id=guard.event_id,
        obligation=written_off,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=written_off.obligation_id,
        target_type="financial_obligation",
        reason_code=_AUDIT_OBLIGATION,
        before_hash=before,
        after_hash=_state_hash(financial_obligation_state_payload(written_off)),
        clock=clock,
    )
    return FinancialObligationResult(obligation=written_off, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Reporting: snapshot, versions, review, audit, submission, publication
# (canon 19f.16, 19f.17)
# ---------------------------------------------------------------------------


def freeze_report_snapshot(
    snapshot_store: ReportSnapshotStore,
    perimeter_store: ReportingPerimeterDefinitionStore,
    perimeter_snapshot_store: PerimeterSnapshotStore,
    period_store: AccountingPeriodStore,
    transaction_store: FinancialTransactionStore,
    entry_store: JournalEntryStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    snapshot_id: UUID,
    period_id: UUID,
    effective_on: date,
    additional_policy_bindings: tuple[PolicyBinding, ...] = (),
) -> ReportSnapshotResult:
    """Freeze the source data a report version will be computed from
    (`ФИН-24`).

    Create-once and terminal: `InMemoryReportSnapshotStore.save` refuses
    to replace an existing snapshot **at all**, not merely a differing
    one, because a second freeze can only mean the command ran twice and
    two runs may have read two different register states. The idempotent
    retry belongs to `CommandIdempotencyStore`, which returns the first
    snapshot instead of freezing again.

    The perimeter is resolved from the **active, effective-dated**
    `ReportingPerimeterDefinition` and frozen alongside; no active
    definition raises `FINANCE_REPORTING_PERIMETER_UNDETERMINED` rather
    than falling back to the organizational hierarchy as it stands now,
    which canon 19f.16 forbids because it would make a report's meaning
    depend on a later reorganisation.

    The policy bindings that classified the included transactions travel
    into the digest, so "which policy version produced this figure" stays
    answerable after the policy changes (`ФИН-23`)."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    definition = perimeter_store.resolve_active(scope=scope, effective_on=effective_on)
    if definition is None:
        raise ReportingPerimeterUndeterminedError(
            f"no active reporting perimeter definition is effective on {effective_on.isoformat()} "
            "for this scope; the perimeter is undetermined, not the hierarchy as it stands"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="freeze_report_snapshot",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(snapshot_id), str(period_id), effective_on.isoformat()),
        target_scope=period.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(snapshot_store.get, guard.replay, what="report snapshot")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportSnapshotResult(
            snapshot=stored,
            event=build_finance_report_snapshot_frozen_event(
                event_id=guard.event_id,
                snapshot=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    perimeter = perimeter_snapshot_store.freeze_once(freeze_perimeter(definition, guard.now))
    transactions = transaction_store.list_for_period(scope=guard.scope, period_id=period_id)
    entries = entry_store.list_for_period(scope=guard.scope, period_id=period_id)
    bindings = {
        (
            binding.policy_kind,
            binding.policy_id,
            binding.policy_version,
            binding.effective_from,
        ): binding
        for binding in (
            *additional_policy_bindings,
            *(
                transaction.classification_policy
                for transaction in transactions
                if transaction.classification_policy is not None
            ),
        )
    }
    snapshot = ReportSnapshot.freeze(
        snapshot_id=snapshot_id,
        scope=guard.scope,
        period=period.as_reference(),
        perimeter=perimeter,
        frozen_at=guard.now,
        policy_bindings=tuple(bindings[key] for key in sorted(bindings, key=lambda k: str(k))),
        included_transaction_ids=tuple(transaction.transaction_id for transaction in transactions),
        included_entry_ids=tuple(
            entry.entry_id for entry in entries if entry.status is not EntryStatus.DRAFT
        ),
    )
    snapshot_store.save(snapshot)
    event = build_finance_report_snapshot_frozen_event(
        event_id=guard.event_id,
        snapshot=snapshot,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=snapshot.snapshot_id,
        target_type="finance_report_snapshot",
        reason_code=_AUDIT_SNAPSHOT,
        before_hash="",
        after_hash=_state_hash(report_snapshot_state_payload(snapshot)),
        clock=clock,
    )
    return ReportSnapshotResult(snapshot=snapshot, event=event, audit_event=audit_event)


def prepare_report_version(
    version_store: FinanceReportVersionStore,
    snapshot_store: ReportSnapshotStore,
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    report_id: UUID,
    period_id: UUID,
    snapshot_id: UUID,
    reason: ReasonCoded,
    version_number: int = 1,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Bind the frozen snapshot a report version is computed from
    (`ФИН-24`).

    Preparation is **not** a state transition: canon 19f.17 has it
    performed *from* a frozen snapshot and lists no post-preparation
    status, so the version stays `draft` - or in its `amended`/`restated`
    correction entry state - and gains the binding every later state
    requires. A version names exactly one snapshot for life, and one
    frozen for another period is not this report's source data.

    A version that does not yet exist is created here in `draft`, so
    preparation is one command rather than a create-then-prepare pair
    whose halves could be separated by a crash."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    snapshot = _load_scoped(
        snapshot_store.get,
        snapshot_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report snapshot",
        for_write=True,
    )
    existing = version_store.get(version_id)
    version = (
        existing
        if existing is not None
        else FinanceReportVersion(
            version_id=version_id,
            report_id=report_id,
            scope=scope,
            period=period.as_reference(),
            version=version_number,
        )
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="prepare_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(report_id), str(snapshot_id)),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_prepared_event(
                event_id=guard.event_id,
                version=stored,
                authority=guard.authority,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = "" if existing is None else _state_hash(report_version_state_payload(version))
    prepared = version.prepare(
        snapshot,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
    )
    version_store.save(prepared)
    event = build_finance_report_prepared_event(
        event_id=guard.event_id,
        version=prepared,
        authority=guard.authority,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=prepared.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(prepared)),
        clock=clock,
    )
    return ReportVersionResult(version=prepared, event=event, audit_event=audit_event)


def complete_internal_report_review(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    review_id: UUID,
    outcome: ReviewOutcome,
    reason: ReasonCoded,
    finding_references: tuple[str, ...] = (),
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record one internal review pass and, where it cleared, close
    internal review (`ФИН-33`).

    A review with `findings_open` is recorded and the version stays where
    it is: recording it as progress would make the review decorative, and
    closing review on top of open findings is what `ФИН-33` refuses. Only
    a `complete` review moves the version to `internally_reviewed`, and
    the aggregate re-checks that at least one completed review exists
    rather than trusting this command's arithmetic.

    The two outcomes emit two different canonical events -
    `finance_report.validation_finding_recorded` and
    `finance_report.internally_reviewed` - because they are two different
    facts."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="complete_internal_report_review",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(review_id), str(outcome)),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    review = ReviewRecord(
        review_id=review_id,
        reviewed_at=guard.now,
        reviewer=guard.authority,
        outcome=outcome,
        finding_references=finding_references,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        replayed_review = next(
            (candidate for candidate in stored.review_records if candidate.review_id == review_id),
            review,
        )
        return ReportVersionResult(
            version=stored,
            event=(
                build_finance_report_internally_reviewed_event(
                    event_id=guard.event_id,
                    version=stored,
                    authority=guard.authority,
                    reason=reason,
                    actor=guard.actor,
                    correlation_id=guard.correlation_id,
                    causation_id=guard.causation_id,
                    occurred_at=audit_event.occurred_at,
                )
                if outcome is ReviewOutcome.COMPLETE
                else build_finance_report_validation_finding_recorded_event(
                    event_id=guard.event_id,
                    version=stored,
                    review=replayed_review,
                    actor=guard.actor,
                    correlation_id=guard.correlation_id,
                    causation_id=guard.causation_id,
                    occurred_at=audit_event.occurred_at,
                )
            ),
            audit_event=audit_event,
        )

    act = GovernedAct(
        at=guard.now,
        by_authority=guard.authority,
        reason=reason,
        conflict=context.conflict,
    )
    before = _state_hash(report_version_state_payload(version))
    recorded = version.record_review(review, act)
    if outcome is ReviewOutcome.COMPLETE:
        updated = recorded.complete_internal_review(act)
        event = build_finance_report_internally_reviewed_event(
            event_id=guard.event_id,
            version=updated,
            authority=guard.authority,
            reason=reason,
            actor=guard.actor,
            correlation_id=guard.correlation_id,
            causation_id=guard.causation_id,
            occurred_at=guard.now,
        )
    else:
        updated = recorded
        event = build_finance_report_validation_finding_recorded_event(
            event_id=guard.event_id,
            version=updated,
            review=review,
            actor=guard.actor,
            correlation_id=guard.correlation_id,
            causation_id=guard.causation_id,
            occurred_at=guard.now,
        )
    version_store.save(updated)
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=updated.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(updated)),
        clock=clock,
    )
    return ReportVersionResult(version=updated, event=event, audit_event=audit_event)


def record_auditor_review(
    version_store: FinanceReportVersionStore,
    engagement_store: AuditEngagementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    engagement_id: UUID,
    conclusion_reference: str,
    reason: ReasonCoded,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record the independent auditor's review of a report version
    (canon 19f.17).

    **A concluded `AuditEngagement` for the same scope and the same period
    is required**, and its absence refuses with `FINANCE_AUDIT_INCOMPLETE`
    - an engagement that is open, in progress, in another scope or for
    another period is not a review of *this* report. Independence is
    re-verified here, not assumed from the engagement's opening
    (`ФИН-29`): `FinanceReportVersion.record_auditor_review` runs
    `assert_auditor_independent` against the actor set read off this
    version's own history, which is where the canon's action-level
    "auditor against report preparer" and "auditor against report
    approver" rows live - both invisible to any role check."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    engagement = _load_scoped(
        engagement_store.get,
        engagement_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="audit engagement",
        for_write=True,
    )
    if engagement.state is not AuditEngagementState.CONCLUDED or engagement.conclusion is None:
        raise AuditIncompleteError(
            f"audit engagement {engagement_id} is {engagement.state!s}; auditor review requires a "
            "concluded engagement for this scope and period"
        )
    if engagement.period.period_id != version.period.period_id:
        raise AuditIncompleteError(
            f"audit engagement {engagement_id} covers another reporting period than this report "
            "version"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_auditor_review",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(engagement_id), conclusion_reference),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    reference = AuditOpinionReference(
        engagement_id=engagement.engagement_id,
        conclusion_reference=conclusion_reference,
        auditor=engagement.auditor,
        recorded_at=guard.now,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_auditor_reviewed_event(
                event_id=guard.event_id,
                version=stored,
                reference=stored.audit_reference or reference,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    reviewed = version.record_auditor_review(
        reference,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        port=port,
    )
    version_store.save(reviewed)
    event = build_finance_report_auditor_reviewed_event(
        event_id=guard.event_id,
        version=reviewed,
        reference=reference,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=reviewed.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(reviewed)),
        clock=clock,
    )
    return ReportVersionResult(version=reviewed, event=event, audit_event=audit_event)


def approve_report_version(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    approval_id: UUID,
    reason: ReasonCoded,
    policy: PolicyBinding | None = None,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Approve a report version (`ФИН-33`).

    A version with no recorded audit reference refuses with
    `FINANCE_AUDIT_INCOMPLETE`, and the approver may not be the actor who
    prepared it - canon 19f.14's "creator against approver of the same
    object" row, checked per object because both acts fit comfortably
    inside one compatible role set. Approval is not publication and
    publication is not approval (`ФИН-28`); this command grants
    neither."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="approve_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(approval_id), reason.reason_code),
        target_scope=version.scope,
        prior_actor_references=tuple(version.actor_references_for("prepared")),
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    approval = ApprovalRecord(
        approval_id=approval_id,
        approved_at=guard.now,
        approved_by=guard.authority,
        reason=reason,
        policy=policy,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_approved_event(
                event_id=guard.event_id,
                version=stored,
                approval=stored.approval_record or approval,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    approved = version.approve(
        approval,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            policy=policy,
            conflict=context.conflict,
        ),
    )
    version_store.save(approved)
    event = build_finance_report_approved_event(
        event_id=guard.event_id,
        version=approved,
        approval=approval,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=approved.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(approved)),
        clock=clock,
    )
    return ReportVersionResult(version=approved, event=event, audit_event=audit_event)


def sign_report_version(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    signature_id: UUID,
    reason: ReasonCoded,
    policy: PolicyBinding | None = None,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record the legally responsible signature (`ФИН-33`).

    Signing is a `report_signatory` act and a distinct one from approval,
    so the resolved authority's role is checked explicitly here:
    `ACTION_REQUIREMENTS`'s `approve_report` entry admits the
    organizational administrator too, and canon 19f.17 does not. Signing
    one's own approval collapses two of the six distinguishable acts into
    one and is refused by the aggregate (`ФИН-31`).

    The signature is a **record that a named authority signed**, never a
    cryptographic signature value: PACK-10 implements no signing
    primitive and claims none."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="sign_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(signature_id), reason.reason_code),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    signature = SignatureRecord(
        signature_id=signature_id,
        signed_at=guard.now,
        signed_by=guard.authority,
        reason=reason,
        policy=policy,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_signed_event(
                event_id=guard.event_id,
                version=stored,
                signature=stored.signature_record or signature,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    if resolve_finance_role(guard.authority.role_code) is not FinanceRole.REPORT_SIGNATORY:
        raise ReportSignOffMissingError(
            "the legally responsible signature requires a report_signatory authority; "
            f"{guard.authority.role_code!r} cannot sign a report version"
        )
    before = _state_hash(report_version_state_payload(version))
    signed = version.sign(
        signature,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            policy=policy,
            conflict=context.conflict,
        ),
    )
    version_store.save(signed)
    event = build_finance_report_signed_event(
        event_id=guard.event_id,
        version=signed,
        signature=signature,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=signed.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(signed)),
        clock=clock,
    )
    return ReportVersionResult(version=signed, event=event, audit_event=audit_event)


def submit_report_version(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    submission_reference: str,
    recipient_reference: str,
    reason: ReasonCoded,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record that a signed version was submitted (canon 19f.17).

    Submission is **one fact and implies nothing further**: not
    acknowledgement, not acceptance, not fulfilment of the reporting
    obligation - that last is recorded on the obligation itself, against
    this submission reference (`ФИН-26`). Refused without the legally
    responsible signature."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="submit_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), submission_reference, recipient_reference),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    reference = ExternalSubmissionReference(
        submission_reference=submission_reference,
        recipient_reference=recipient_reference,
        submitted_at=guard.now,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_submitted_event(
                event_id=guard.event_id,
                version=stored,
                reference=stored.external_submission_reference or reference,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    submitted = version.record_submission(
        reference,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
    )
    version_store.save(submitted)
    event = build_finance_report_submitted_event(
        event_id=guard.event_id,
        version=submitted,
        reference=reference,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=submitted.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(submitted)),
        clock=clock,
    )
    return ReportVersionResult(version=submitted, event=event, audit_event=audit_event)


def record_external_acknowledgement(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    notice_effect_reference: str,
    kind: ExternalStatusKind,
    reason: ReasonCoded,
    deciding_authority_reference: str | None = None,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record that the recipient acknowledged receipt (`ФИН-26`,
    `ФИН-27`).

    Storable, and *only* that: an acknowledgement, a receipt, delivery
    telemetry and a read status are all real facts and all deserve a
    create-once record, and none of them is a legal decision. An
    authoritative acceptance decision offered here is refused rather than
    silently downgraded - it belongs on `record_external_acceptance`,
    where the acceptance transition and its guard live."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_external_acknowledgement",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), notice_effect_reference, str(kind)),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    reference = ExternalAcceptanceReference(
        notice_effect_reference=notice_effect_reference,
        kind=kind,
        decided_at=guard.now,
        deciding_authority_reference=deciding_authority_reference,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_external_acknowledgement_recorded_event(
                event_id=guard.event_id,
                version=stored,
                reference=stored.external_acknowledgement_reference or reference,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    acknowledged = version.record_external_acknowledgement(
        reference,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
    )
    version_store.save(acknowledged)
    event = build_finance_report_external_acknowledgement_recorded_event(
        event_id=guard.event_id,
        version=acknowledged,
        reference=reference,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=acknowledged.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(acknowledged)),
        clock=clock,
    )
    return ReportVersionResult(version=acknowledged, event=event, audit_event=audit_event)


def record_external_acceptance(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    notice_effect_reference: str | None,
    kind: ExternalStatusKind = ExternalStatusKind.AUTHORITATIVE_ACCEPTANCE_DECISION,
    reason: ReasonCoded,
    deciding_authority_reference: str | None = None,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Record an authoritative external acceptance decision (`ФИН-26`,
    `ФИН-27`).

    The narrowest gate in this service. **Absence refuses** with
    `FINANCE_EXTERNAL_ACCEPTANCE_MISSING`: acceptance is never inferred,
    and no elapsed-time path to it exists - the answer to "the authority
    has not replied in six weeks, may we treat it as accepted?" is no,
    whatever the clock says (`reporting.assert_no_inferred_acceptance`).
    **Telemetry refuses** with
    `FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE`: an
    acknowledgement, a receipt, a delivery record and a read status are
    all storable facts and none is a legal acceptance decision, and the
    refusal names which was offered. Only a governed PACK-09
    notice-effect decision drives this transition."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_external_acceptance",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), notice_effect_reference or "", str(kind)),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    reference = (
        None
        if notice_effect_reference is None
        else ExternalAcceptanceReference(
            notice_effect_reference=notice_effect_reference,
            kind=kind,
            decided_at=guard.now,
            deciding_authority_reference=deciding_authority_reference,
        )
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        recorded_reference = stored.external_acceptance_reference
        if recorded_reference is None:  # pragma: no cover - a recorded acceptance always has one
            raise IdempotencyConflictError(
                f"the recorded result of event_id {guard.event_id} carries no acceptance reference"
            )
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_acceptance_recorded_event(
                event_id=guard.event_id,
                version=stored,
                reference=recorded_reference,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    accepted = version.record_external_acceptance(
        reference,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
    )
    version_store.save(accepted)
    # `FinanceReportVersion.record_external_acceptance` refuses `None` and
    # refuses telemetry, so the recorded reference is the authoritative one
    # it just bound - read back off the aggregate rather than re-narrowed
    # here, so the event can only ever carry what the register carries.
    recorded_reference = accepted.external_acceptance_reference
    if recorded_reference is None:  # pragma: no cover - the transition just set it
        raise ExternalAcceptanceMissingError(
            "the accepted report version carries no external acceptance reference"
        )
    event = build_finance_report_acceptance_recorded_event(
        event_id=guard.event_id,
        version=accepted,
        reference=recorded_reference,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=accepted.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(accepted)),
        clock=clock,
    )
    return ReportVersionResult(version=accepted, event=event, audit_event=audit_event)


def publish_report_version(
    version_store: FinanceReportVersionStore,
    publication_authorization_store: PublicationAuthorizationStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    publication_authorization_id: UUID | None,
    publication_reference: str,
    reason: ReasonCoded,
    expected_report_state_version: int | None = None,
) -> ReportVersionResult:
    """Publish a report version against a **separate** publication
    authorisation (`ФИН-28`, `ФИН-34`).

    Publication is not approval and approval is not publication, and canon
    19f.17 says so in both directions. A missing, unknown or foreign-scope
    authorisation all refuse identically with `PUBLICATION_NOT_ALLOWED` -
    which is also non-disclosing, since a caller cannot tell an
    authorisation that does not exist from one it may not see. The
    aggregate then requires three independent facts: a recorded approval,
    the authorisation presented and scoped here, and a publication record
    naming *that* authorisation."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    if publication_authorization_id is None:
        raise PublicationNotAllowedError(
            "publication requires a separate publication authorisation; none was presented"
        )
    authorization = publication_authorization_store.get(publication_authorization_id)
    if authorization is None or authorization.scope.organization_id != scope.organization_id:
        raise PublicationNotAllowedError(
            f"publication authorisation {publication_authorization_id} is not a valid "
            "authorisation in this organizational scope"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="publish_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(version_id),
            str(publication_authorization_id),
            publication_reference,
        ),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    reference = PublicationReference(
        publication_reference=publication_reference,
        authorization_id=authorization.authorization_id,
        published_at=guard.now,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(version_store.get, guard.replay, what="report version")
        audit_event = _replayed_audit(audit_store, guard)
        return ReportVersionResult(
            version=stored,
            event=build_finance_report_published_event(
                event_id=guard.event_id,
                version=stored,
                reference=stored.publication_reference or reference,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    published = version.publish(
        reference,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        publication_authorization=authorization,
    )
    version_store.save(published)
    event = build_finance_report_published_event(
        event_id=guard.event_id,
        version=published,
        reference=reference,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=published.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(published)),
        clock=clock,
    )
    return ReportVersionResult(version=published, event=event, audit_event=audit_event)


def create_corrected_report_version(
    version_store: FinanceReportVersionStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    version_id: UUID,
    successor_version_id: UUID,
    correction_kind: CorrectionKind,
    reason: ReasonCoded,
    expected_report_state_version: int | None = None,
) -> CorrectedReportVersionResult:
    """Create the amendment or restatement a material correction requires
    (`ФИН-25`).

    Both halves of one act are returned and both are stored, so a caller
    cannot record the successor while leaving its predecessor live -
    which is how two versions of one report end up both current. **The
    predecessor is never rewritten**: it becomes `superseded` and stays
    readable forever, including when it was already submitted,
    acknowledged or published (`ФИН-05`). The successor starts in
    `amended` or `restated` with **no snapshot**, because changed figures
    need their own, and must be reviewed, audited, approved and signed
    again - never resuming with decisions given for different figures."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="create_corrected_report_version",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(version_id), str(successor_version_id), str(correction_kind)),
        target_scope=version.scope,
        current_version=_history_version(version.history),
        expected_version=expected_report_state_version,
        version_label="report version",
    )
    if guard.replay is not None:
        replayed_predecessor = _replayed_aggregate(
            version_store.get, guard.replay, what="report version"
        )
        replayed_successor = version_store.get(successor_version_id)
        if replayed_successor is None:  # pragma: no cover - written in the same act
            raise IdempotencyConflictError(
                f"the recorded result of event_id {guard.event_id} names a successor version "
                f"{successor_version_id} that is no longer readable"
            )
        audit_event = _replayed_audit(audit_store, guard)
        return CorrectedReportVersionResult(
            superseded=replayed_predecessor,
            successor=replayed_successor,
            event=_correction_event(
                replayed_successor, guard, reason=reason, occurred_at=audit_event.occurred_at
            ),
            audit_event=audit_event,
        )

    before = _state_hash(report_version_state_payload(version))
    superseded, successor = version.create_successor_version(
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        version_id=successor_version_id,
        correction_kind=correction_kind,
    )
    version_store.save(superseded)
    version_store.save(successor)
    event = _correction_event(successor, guard, reason=reason, occurred_at=guard.now)
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=superseded.version_id,
        target_type="finance_report_version",
        reason_code=_AUDIT_REPORT,
        before_hash=before,
        after_hash=_state_hash(report_version_state_payload(superseded)),
        clock=clock,
    )
    return CorrectedReportVersionResult(
        superseded=superseded, successor=successor, event=event, audit_event=audit_event
    )


def _correction_event(
    successor: FinanceReportVersion,
    guard: _CommandGuard,
    *,
    reason: ReasonCoded,
    occurred_at: datetime,
) -> EventEnvelope:
    """`finance_report.amended` or `finance_report.restated`.

    Two events rather than one "corrected", because canon 19f.17's two
    correction routes are distinct legal acts and a single event would
    erase which one happened. The subject is the successor - the version
    that came into existence - and the typed backward link travels in the
    payload."""
    builder = (
        build_finance_report_amended_event
        if successor.correction_kind is CorrectionKind.AMENDMENT
        else build_finance_report_restated_event
    )
    return builder(
        event_id=guard.event_id,
        successor=successor,
        authority=guard.authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=occurred_at,
    )


# ---------------------------------------------------------------------------
# The independent audit engagement (canon 19f.18)
# ---------------------------------------------------------------------------


def open_audit_engagement(
    engagement_store: AuditEngagementStore,
    period_store: AccountingPeriodStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    engagement_id: UUID,
    period_id: UUID,
    auditor: AuthorityReference,
    reason: ReasonCoded,
    operational_actor_references: tuple[str, ...] = (),
) -> AuditEngagementResult:
    """Open an independent audit engagement (`ФИН-29`, `ФИН-30`).

    **Independence is verified, not assumed**, and verified again at every
    finding and at the conclusion - checking only at opening would miss a
    role granted mid-engagement, which is exactly why
    `authorization.assert_auditor_independent` is a free function the
    aggregate calls at all three points rather than a property latched on
    once. Four things are checked: the auditor's authority is scoped to
    the audited scope, its role is `finance_auditor`, its actor appears
    nowhere in `operational_actor_references` - the actors who prepared,
    reviewed, approved, authorised, executed or signed the material under
    audit - and the roles it actually holds there carry none of
    `AUDITOR_INCOMPATIBLE_ROLES`.

    The requesting authority and the auditor are two different presented
    authorities on purpose: `request_audit` is an administrative act and
    `finance_auditor` is the audited party's counterpart, and the matrix
    makes the two hard-incompatible in one scope."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="open_audit_engagement",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(engagement_id), str(period_id), str(auditor.authority_id)),
        target_scope=period.scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(engagement_store.get, guard.replay, what="audit engagement")
        audit_event = _replayed_audit(audit_store, guard)
        return AuditEngagementResult(
            engagement=stored,
            event=build_finance_audit_opened_event(
                event_id=guard.event_id,
                engagement=stored,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    engagement = AuditEngagement.open(
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        engagement_id=engagement_id,
        scope=guard.scope,
        period=period.as_reference(),
        auditor=auditor,
        operational_actor_references=operational_actor_references,
        port=port,
    )
    engagement_store.save(engagement)
    event = build_finance_audit_opened_event(
        event_id=guard.event_id,
        engagement=engagement,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=engagement.engagement_id,
        target_type="finance_audit_engagement",
        reason_code=_AUDIT_ENGAGEMENT,
        before_hash="",
        after_hash=_state_hash(audit_engagement_state_payload(engagement)),
        clock=clock,
    )
    return AuditEngagementResult(engagement=engagement, event=event, audit_event=audit_event)


def record_audit_finding(
    engagement_store: AuditEngagementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    engagement_id: UUID,
    finding_id: UUID,
    severity: str,
    summary_reference: str,
    reason: ReasonCoded,
    evidence: tuple[EvidenceReference, ...] = (),
    operational_actor_references: tuple[str, ...] = (),
    expected_engagement_version: int | None = None,
) -> AuditEngagementResult:
    """Append an audit finding, re-checking independence (canon 19f.18).

    The second of the three independence checks, and the one where a role
    granted *after* the engagement opened surfaces. A recorded finding is
    never edited and survives every later engagement; a correction is a
    further finding. `summary_reference` is a pointer, not prose: findings
    are disclosed only per disclosure policy and never in a form
    identifying individuals (`ФИН-35`).

    An auditor's own reconciliation is *a finding*, never an authoritative
    `ReconciliationRecord` - the audit module writes into nothing it
    audits."""
    scope = context.require_scope()
    engagement = _load_scoped(
        engagement_store.get,
        engagement_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="audit engagement",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="record_audit_finding",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(engagement_id), str(finding_id), severity, summary_reference),
        target_scope=engagement.scope,
        current_version=_history_version(engagement.history),
        expected_version=expected_engagement_version,
        version_label="audit engagement",
    )
    finding = AuditFinding(
        finding_id=finding_id,
        recorded_at=guard.now,
        recorded_by=guard.authority,
        severity=severity,
        summary_reference=summary_reference,
        evidence=evidence,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(engagement_store.get, guard.replay, what="audit engagement")
        audit_event = _replayed_audit(audit_store, guard)
        replayed_finding = next(
            (candidate for candidate in stored.findings if candidate.finding_id == finding_id),
            finding,
        )
        return AuditEngagementResult(
            engagement=stored,
            event=build_finance_audit_finding_recorded_event(
                event_id=guard.event_id,
                engagement=stored,
                finding=replayed_finding,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(audit_engagement_state_payload(engagement))
    updated = engagement.record_finding(
        finding,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        operational_actor_references=operational_actor_references,
        port=port,
    )
    engagement_store.save(updated)
    event = build_finance_audit_finding_recorded_event(
        event_id=guard.event_id,
        engagement=updated,
        finding=finding,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=updated.engagement_id,
        target_type="finance_audit_engagement",
        reason_code=_AUDIT_ENGAGEMENT,
        before_hash=before,
        after_hash=_state_hash(audit_engagement_state_payload(updated)),
        clock=clock,
    )
    return AuditEngagementResult(engagement=updated, event=event, audit_event=audit_event)


def conclude_audit_engagement(
    engagement_store: AuditEngagementStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    engagement_id: UUID,
    conclusion_id: UUID,
    conclusion_class: str,
    reason: ReasonCoded,
    evidence: tuple[EvidenceReference, ...] = (),
    operational_actor_references: tuple[str, ...] = (),
    minimum_findings: int = 0,
    expected_engagement_version: int | None = None,
) -> AuditEngagementResult:
    """Conclude the engagement, create-once (canon 19f.18).

    The canonical name is `AuditConclusion` and never "opinion": no object
    here may be read as the opinion of a statutory audit. Four refusals: a
    second conclusion is an edit of a create-once record, since a changed
    conclusion is a *new engagement*; a concluding authority other than
    this engagement's own auditor and a failed independence re-check - the
    third of the three - both refuse as independence violations; and fewer
    findings than `minimum_findings` refuses as an incomplete audit, that
    count being a versioned policy value passed in, never a constant this
    module gets to choose."""
    scope = context.require_scope()
    engagement = _load_scoped(
        engagement_store.get,
        engagement_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="audit engagement",
        for_write=True,
    )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="conclude_audit_engagement",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(engagement_id), str(conclusion_id), conclusion_class),
        target_scope=engagement.scope,
        current_version=_history_version(engagement.history),
        expected_version=expected_engagement_version,
        version_label="audit engagement",
    )
    conclusion = AuditConclusion(
        conclusion_id=conclusion_id,
        concluded_at=guard.now,
        concluded_by=guard.authority,
        conclusion_class=conclusion_class,
        reason=reason,
        evidence=evidence,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(engagement_store.get, guard.replay, what="audit engagement")
        audit_event = _replayed_audit(audit_store, guard)
        return AuditEngagementResult(
            engagement=stored,
            event=build_finance_audit_concluded_event(
                event_id=guard.event_id,
                engagement=stored,
                conclusion=stored.conclusion or conclusion,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    before = _state_hash(audit_engagement_state_payload(engagement))
    concluded = engagement.conclude(
        conclusion,
        GovernedAct(
            at=guard.now,
            by_authority=guard.authority,
            reason=reason,
            conflict=context.conflict,
        ),
        operational_actor_references=operational_actor_references,
        port=port,
        minimum_findings=minimum_findings,
    )
    engagement_store.save(concluded)
    event = build_finance_audit_concluded_event(
        event_id=guard.event_id,
        engagement=concluded,
        conclusion=conclusion,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=concluded.engagement_id,
        target_type="finance_audit_engagement",
        reason_code=_AUDIT_ENGAGEMENT,
        before_hash=before,
        after_hash=_state_hash(audit_engagement_state_payload(concluded)),
        clock=clock,
    )
    return AuditEngagementResult(engagement=concluded, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# The purpose-scoped party handle (canon 19f.15)
# ---------------------------------------------------------------------------


def mint_party_handle(
    handle_store: FinancePartyHandleStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    handle_id: UUID,
    purpose: HandlePurpose,
    policy_version: str = "party_handle/v1",
    attributes: Mapping[str, object] | None = None,
) -> PartyHandleResult:
    """Mint an opaque, purpose-scoped, perimeter-scoped party handle
    (`ФИН-01`).

    **No identifying attribute may be supplied, and `attributes` exists in
    order to refuse one.** A handle is derived from *nothing*: not from a
    name, an account, a membership, a credential, a participation value or
    another handle (canon 19f.15). The parameter is the honest API for an
    act the domain forbids - like `storage.delete_finance_record` - so a
    caller reaching for it gets a reason-coded refusal naming the
    offending key rather than a silently ignored argument.
    `domain.reject_identity_payload_keys` runs first, so a prohibited key
    is named exactly; anything else non-empty is refused too, because
    "which non-identifying attributes are safe to derive a handle from" is
    not a question this service is allowed to answer.

    Two handles for the same legal person in different purposes are
    unequal by construction and nothing here can join them: the matching
    act lives in the party registry and is audited there (`ФИН-36`)."""
    scope = context.require_scope()
    supplied = {} if attributes is None else dict(attributes)
    if supplied:
        reject_identity_payload_keys(supplied, context="mint_party_handle")
        raise ForbiddenIdentityLinkageError(
            f"a party handle is derived from nothing; attribute(s) {sorted(supplied)} were "
            "supplied and are refused"
        )
    guard = _guard(
        idempotency_store,
        audit_store,
        command="mint_party_handle",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(handle_id), str(purpose), policy_version),
        target_scope=scope,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(handle_store.get, guard.replay, what="party handle")
        audit_event = _replayed_audit(audit_store, guard)
        return PartyHandleResult(
            handle=stored,
            event=build_finance_party_handle_minted_event(
                event_id=guard.event_id,
                handle=stored,
                authority=guard.authority,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    handle = FinancePartyHandle(
        handle_id=handle_id,
        purpose=purpose,
        perimeter=guard.scope,
        policy_version=policy_version,
    )
    handle_store.put(handle)
    event = build_finance_party_handle_minted_event(
        event_id=guard.event_id,
        handle=handle,
        authority=guard.authority,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=handle.handle_id,
        target_type="finance_party_handle",
        reason_code=_AUDIT_HANDLE,
        before_hash="",
        after_hash=_state_hash(
            {
                "party_handle_reference": handle.as_reference(),
                "purpose": str(handle.purpose),
                "perimeter": str(handle.perimeter.organization_id),
                "policy_version": handle.policy_version,
            }
        ),
        clock=clock,
    )
    return PartyHandleResult(handle=handle, event=event, audit_event=audit_event)


def _resolve_party_handle_authority(
    context: RequestContext, scope: OrganizationalScopeRef, port: AuthorizationPort
) -> AuthorityReference:
    """Resolve the **separate** authority a handle resolution requires
    (canon 19f.15).

    Deliberately not `assert_authorized`: resolution is not one of the
    forty governed finance actions and must not become one, because a
    resolution role listed in `ACTION_REQUIREMENTS` would be grantable
    alongside the ordinary finance roles. The bar here is *narrower* than
    `assert_authorized`'s, not wider - an exact role code, this exact
    scope, and an active assignment behind the presented object - and
    every failure answers with the one code canon 19f.15 assigns,
    `FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`, without distinguishing which
    condition failed."""
    for authority in context.authorities:
        if authority.role_code.strip() != PARTY_HANDLE_RESOLUTION_ROLE_CODE:
            continue
        if authority.scope.organization_id != scope.organization_id:
            continue
        if not port.resolve_active_authority(authority, scope):
            continue
        return authority
    raise PartyHandleResolutionDeniedError(
        "resolving a party handle requires a separately granted, active "
        f"{PARTY_HANDLE_RESOLUTION_ROLE_CODE} authority in this perimeter; none was presented"
    )


def resolve_party_handle(
    handle_store: FinancePartyHandleStore,
    idempotency_store: CommandIdempotencyStore,
    audit_store: AuditEventStore,
    sink: EventSink,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    handle_id: UUID,
    purpose: HandlePurpose,
    reason: ReasonCoded,
    registry_resolution_reference: str | None = None,
) -> PartyHandleResult:
    """Authorise and audit one act of resolving a party handle
    (`FINANCE_PARTY_HANDLE_RESOLUTION_DENIED`, canon 19f.15).

    Three things make this command unlike every other one here.

    **The authority is separate.** Resolution requires an explicitly
    granted `finance_party_handle_resolver` authority and nothing else
    passes - not `finance_administrator`, not an organizational
    administrator, not any privileged grant (`ФИН-42`). See
    `_resolve_party_handle_authority`.

    **The act itself is audited, and the resolved value never appears.**
    `finance_party_handle.resolved` records who resolved what, under which
    authority and for what purpose, *without the value* - the event
    builder takes no parameter that could carry one, so a caller cannot
    supply it by mistake (canon 19f.15, canon 20.17's forbidden-payload
    list for this one event).

    **Nothing is returned but the handle.** Finance does not hold the join
    between a handle and a legal person and must not: re-identification is
    the party registry's act. `registry_resolution_reference` is an opaque
    pointer to the registry's own record of what it resolved, carried only
    into the request digest so a replay is recognisable, and never into
    the payload, the audit row or the return value. The handle's purpose
    and perimeter are re-asserted first: a handle presented for another
    purpose is refused before the resolution is authorised at all."""
    scope = context.require_scope()
    handle = _load_scoped(
        handle_store.get,
        handle_id,
        lambda value: value.perimeter,
        scope=scope,
        context=context,
        what="party handle",
        for_write=True,
    )
    handle.assert_usable_for(purpose, scope)
    resolution_authority = _resolve_party_handle_authority(context, scope, port)
    guard = _guard(
        idempotency_store,
        audit_store,
        command="resolve_party_handle",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(handle_id), str(purpose), registry_resolution_reference or ""),
        target_scope=handle.perimeter,
        resolved_authority=resolution_authority,
    )
    if guard.replay is not None:
        stored = _replayed_aggregate(handle_store.get, guard.replay, what="party handle")
        audit_event = _replayed_audit(audit_store, guard)
        return PartyHandleResult(
            handle=stored,
            event=build_finance_party_handle_resolved_event(
                event_id=guard.event_id,
                handle=stored,
                resolving_authority=resolution_authority,
                reason=reason,
                actor=guard.actor,
                correlation_id=guard.correlation_id,
                causation_id=guard.causation_id,
                occurred_at=audit_event.occurred_at,
            ),
            audit_event=audit_event,
        )

    event = build_finance_party_handle_resolved_event(
        event_id=guard.event_id,
        handle=handle,
        resolving_authority=resolution_authority,
        reason=reason,
        actor=guard.actor,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
        occurred_at=guard.now,
    )
    access_hash = _state_hash(
        {
            "party_handle_reference": handle.as_reference(),
            "purpose": str(handle.purpose),
            "perimeter": str(handle.perimeter.organization_id),
            "resolved_value_disclosed": False,
        }
    )
    audit_event = _finish(
        idempotency_store,
        audit_store,
        sink,
        guard,
        event=event,
        aggregate_id=handle.handle_id,
        target_type="finance_party_handle",
        reason_code=_AUDIT_HANDLE,
        # A resolution changes no state, so the two hashes are the same
        # access snapshot. Neither carries the resolved value, and neither
        # ever will: the hash is over the *act of access*, not its result.
        before_hash=access_hash,
        after_hash=access_hash,
        clock=clock,
    )
    return PartyHandleResult(handle=handle, event=event, audit_event=audit_event)


# ---------------------------------------------------------------------------
# Queries (canon 19f.21, `ФИН-34`)
# ---------------------------------------------------------------------------
#
# Every read below is scope-filtered and returns a `projections.*` object
# rather than an aggregate wherever a projection exists, because a
# projection carries the provenance canon 19f.21 makes mandatory - the
# report version, the snapshot reference, the source's lifecycle state, its
# correction status and the moment of generation - and a bare aggregate
# carries none of it. Nothing here is authoritative
# (`FinanceProjection.is_authoritative` is a property returning `False`,
# not a field), nothing here is written back, and a foreign-scope read
# answers `VALIDATION_RECORD_NOT_FOUND` exactly as a nonexistent record
# does.


def get_account_balance_projection(
    account_store: FinanceAccountStore,
    entry_store: JournalEntryStore,
    *,
    context: RequestContext,
    clock: Clock,
    account_id: UUID,
    period_id: UUID,
    currency: str,
) -> AccountBalanceProjection:
    """The derived closing balance of one account for one period.

    Summed over **posted** entries only: a draft has no monetary effect,
    and including one would publish an unrealised figure. `currency` is
    required and never inferred (`ФИН-09`); an account carrying postings in
    more than one currency has no single balance and refuses, because
    netting across currencies without a recorded conversion is precisely
    what the invariant forbids.

    Never publicly projected in any form (canon 20.17 group 1): only
    aggregated figures *inside a published report version* reach the
    public, which is why this object carries the internal projection
    version."""
    scope = context.require_scope()
    account = _load_scoped(
        account_store.get,
        account_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="finance account",
    )
    debits: list[Money] = []
    credits: list[Money] = []
    for entry in entry_store.list_for_period(scope=scope, period_id=period_id):
        if entry.status is EntryStatus.DRAFT:
            continue
        for line in entry.lines:
            if line.account_id != account_id:
                continue
            (debits if line.is_debit else credits).append(line.amount)
    debit_totals = sum_money(tuple(debits))
    credit_totals = sum_money(tuple(credits))
    currencies = set(debit_totals) | set(credit_totals)
    if currencies - {currency}:
        raise CurrencyUnsupportedError(
            f"account {account_id} carries postings in {sorted(currencies)}; a balance in "
            f"{currency} would require a recorded conversion"
        )
    return AccountBalanceProjection.from_account(
        account,
        closing_balance=Money(
            debit_totals.get(currency, 0) - credit_totals.get(currency, 0), currency
        ),
        generated_at=clock.now(),
    )


def get_period_summary(
    period_store: AccountingPeriodStore,
    entry_store: JournalEntryStore,
    *,
    context: RequestContext,
    clock: Clock,
    period_id: UUID,
) -> PeriodSummaryProjection:
    """Aggregated register totals for one accounting period.

    Totals are the per-currency debit sums over posted entries and are
    **never netted across currencies** (`ФИН-09`). Debits are used rather
    than debits-minus-credits because every posted entry balances by
    construction (`ФИН-07`), so the debit total is the period's turnover
    and the difference would always be zero - a number that says
    nothing."""
    scope = context.require_scope()
    period = _load_scoped(
        period_store.get,
        period_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="accounting period",
    )
    debits: list[Money] = []
    for entry in entry_store.list_for_period(scope=scope, period_id=period_id):
        if entry.status is EntryStatus.DRAFT:
            continue
        debits.extend(line.amount for line in entry.lines if line.is_debit)
    return PeriodSummaryProjection.from_period(
        period,
        total_minor_units_by_currency=sum_money(tuple(debits)),
        generated_at=clock.now(),
    )


def list_contribution_disclosures(
    contribution_store: FinanceContributionStore,
    *,
    context: RequestContext,
    clock: Clock,
    disclosure_obligation_reference: str,
    reporting_period_label: str,
    disclosure_policy: PolicyVersionReference | None = None,
    source_report_version_id: UUID | None = None,
) -> tuple[ContributionDisclosureProjection, ...]:
    """The disclosure-obliged view of every **accepted** contribution in
    the caller's scope.

    Publication is permitted only to the extent an effective disclosure
    obligation prescribes, so `disclosure_obligation_reference` is
    mandatory and the projection refuses to exist without it: this module
    does not decide what must be published, and pretending to would be
    this service answering a legal question (spec 9.6, canon 20.17 group
    2).

    Only `accepted` contributions are projected. A quarantined one is the
    recorded admission that its source or verification is still open
    (`ФИН-16`), and publishing it would present an unresolved question as
    a disclosed fact - so those are filtered out here rather than left to
    raise one at a time. The contributor handle stays on the object for
    in-service aggregation and is absent from `to_payload()` entirely
    (canon 19f.15)."""
    scope = context.require_scope()
    return tuple(
        ContributionDisclosureProjection.from_contribution(
            contribution,
            disclosure_obligation_reference=disclosure_obligation_reference,
            reporting_period_label=reporting_period_label,
            generated_at=clock.now(),
            disclosure_policy=disclosure_policy,
            source_report_version_id=source_report_version_id,
        )
        for contribution in contribution_store.list_for_scope(scope=scope)
        if contribution.state is ContributionState.ACCEPTED
    )


def get_published_report_projection(
    version_store: FinanceReportVersionStore,
    *,
    context: RequestContext,
    clock: Clock,
    version_id: UUID,
    superseded_by_version_reference: UUID | None = None,
) -> PublishedReportProjection:
    """The public view of a **published** report version.

    Every other state refuses, `externally_accepted` included: an
    authority's acceptance decision is not a publication decision, and
    publication needs its own authorisation (`ФИН-28`, `ФИН-34`). The
    projection carries the snapshot id as provenance - a pointer that lets
    a reader ask which frozen source set produced a figure - and nothing
    of the `snapshot_frozen` event itself, which canon 20.17 group 4 does
    not permit projecting. It carries no figures: those are the report's
    own content, and re-deriving them here would create a second set that
    can disagree with the published one."""
    scope = context.require_scope()
    version = _load_scoped(
        version_store.get,
        version_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="report version",
    )
    return PublishedReportProjection.from_report_version(
        version,
        generated_at=clock.now(),
        superseded_by_version_reference=superseded_by_version_reference,
    )


def get_audit_conclusion_projection(
    engagement_store: AuditEngagementStore,
    *,
    context: RequestContext,
    clock: Clock,
    engagement_id: UUID,
    source_report_version_id: UUID | None = None,
) -> AuditConclusionProjection:
    """The fact that an audit happened, and the class it concluded with.

    Canon 20.17 group 5 admits exactly those two things: finding content
    is projected nowhere, the conclusion's reason and evidence appear
    nowhere, and neither does the auditor's identity - naming the auditor
    may well be required by some obligation, but that is a separate
    disclosure decision with its own authority. An open or in-progress
    engagement refuses: it has no conclusion class, and projecting the
    bare fact would publish a mid-audit state as a finished one."""
    scope = context.require_scope()
    engagement = _load_scoped(
        engagement_store.get,
        engagement_id,
        lambda value: value.scope,
        scope=scope,
        context=context,
        what="audit engagement",
    )
    return AuditConclusionProjection.from_engagement(
        engagement,
        generated_at=clock.now(),
        source_report_version_id=source_report_version_id,
    )

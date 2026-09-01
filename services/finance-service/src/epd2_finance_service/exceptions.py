"""Finance Service exceptions, one per stable, machine-readable reason
code (canon section 24 and 19f.13; ADR-004's registry rule applied to
PACK-10).

Every class below carries a `reason_code` class attribute whose literal
string is registered in `contracts/reason-codes/pack-10.yml`. No finance
code path may raise a bare `ValueError` or `PermissionError` with a
free-text message in place of one of these (canon 19f.13 `ФИН-40`,
"protected denials and transitions are reason-coded").

The hierarchy mirrors every earlier pack's: structural and lifecycle
violations subclass `ValueError`; authorization, scope and
separation-of-duties violations subclass `PermissionError`, so a caller
that already distinguishes those two categories across PACK-02 through
PACK-09 needs no PACK-10-specific handling.

Codes fall into three groups:

- `FINANCE_*` codes introduced by canon 0.8.0 section 24 for this
  context;
- codes reused verbatim from earlier packs where the semantics are
  identical (`ORGANIZATION_SCOPE_MISMATCH`, `PERMISSION_DENIED`,
  `OPTIMISTIC_CONCURRENCY_CONFLICT`, ...), never shadowed by a
  `FINANCE_` duplicate;
- purely technical, non-business failures, which are documented in
  `docs/contracts/finance-command-query-contracts.md` and are *not*
  reason codes: they surface as `FinanceTechnicalError` and never as a
  governed refusal.
"""

from __future__ import annotations


class FinanceError(Exception):
    """Base class for every governed finance refusal.

    `reason_code` is always a string registered in
    `contracts/reason-codes/pack-10.yml`."""

    reason_code: str = "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# Money, currency, balancing
# ---------------------------------------------------------------------------


class MonetaryAmountInvalidError(FinanceError, ValueError):
    """Amount is not expressible as integer minor units with a recorded
    scale and rounding rule, or is zero where a non-zero posting is
    required (`ФИН-08`, `ФИН-09`)."""

    reason_code = "FINANCE_MONETARY_AMOUNT_INVALID"


class CurrencyUnsupportedError(FinanceError, ValueError):
    """Currency is not governed by the active policy, or cross-currency
    arithmetic was attempted without a recorded conversion (`ФИН-09`)."""

    reason_code = "FINANCE_CURRENCY_UNSUPPORTED"


class JournalEntryUnbalancedError(FinanceError, ValueError):
    """Debit and credit minor units differ for at least one currency
    (`ФИН-07`)."""

    reason_code = "FINANCE_JOURNAL_ENTRY_UNBALANCED"


# ---------------------------------------------------------------------------
# Ledger immutability, periods, provenance
# ---------------------------------------------------------------------------


class ImmutableRecordModificationAttemptedError(FinanceError, ValueError):
    """An attempt to modify a posted entry, a frozen snapshot, a
    submitted report version or any create-once record (`ФИН-05`,
    `ФИН-24`, `ФИН-25`)."""

    reason_code = "FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED"


class AccountingPeriodClosedError(FinanceError, ValueError):
    """The target accounting period is closed; ordinary postings are
    refused inside the posting command itself (`ФИН-10`)."""

    reason_code = "FINANCE_ACCOUNTING_PERIOD_CLOSED"


class AccountingPeriodUndeterminedError(FinanceError, ValueError):
    """No period, or no timezone-explicit period, could be determined for
    the requested effective date (`ФИН-39`, `ФИН-41`)."""

    reason_code = "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED"


class PeriodReopeningNotAuthorizedError(FinanceError, PermissionError):
    """Reopening lacks authority, a reason reference, or dual control
    (`ФИН-11`)."""

    reason_code = "FINANCE_PERIOD_REOPENING_NOT_AUTHORIZED"


class ImportProvenanceMissingError(FinanceError, ValueError):
    """A transaction was submitted without the provenance its source
    class requires (`ФИН-38`)."""

    reason_code = "FINANCE_IMPORT_PROVENANCE_MISSING"


class DuplicateTransactionError(FinanceError, ValueError):
    """A transaction with the same external reference already exists in
    this scope (`ФИН-38`)."""

    reason_code = "FINANCE_DUPLICATE_TRANSACTION"


class DuplicateImportError(FinanceError, ValueError):
    """An import batch fingerprint matches an already-applied batch."""

    reason_code = "FINANCE_DUPLICATE_IMPORT"


class InvalidCorrectionTargetError(FinanceError, ValueError):
    """The correction or reversal target does not exist, is not posted,
    is already reversed, or belongs to another scope (`ФИН-06`)."""

    reason_code = "FINANCE_CORRECTION_TARGET_INVALID"


class TransferPairUnresolvedError(FinanceError, ValueError):
    """A governed inter-scope transfer has no resolvable counterpart
    (`ФИН-37`)."""

    reason_code = "FINANCE_TRANSFER_PAIR_UNRESOLVED"


class BudgetActualWriteForbiddenError(FinanceError, ValueError):
    """An attempt to store an actual amount on a budget line; actuals are
    derived from the ledger (`ФИН-12`)."""

    reason_code = "FINANCE_BUDGET_ACTUAL_WRITE_FORBIDDEN"


class ReclassificationBypassDeniedError(FinanceError, ValueError):
    """The requested reclassification would drop a disclosure, review,
    aggregation or reporting obligation (`ФИН-13`)."""

    reason_code = "FINANCE_RECLASSIFICATION_BYPASS_DENIED"


# ---------------------------------------------------------------------------
# Contributions, sponsorship, external influence
# ---------------------------------------------------------------------------


class ContributionSourceUndeterminedError(FinanceError, ValueError):
    """Contributor source is anonymous or could not be established; the
    contribution fails closed into a governed exceptional state
    (`ФИН-16`)."""

    reason_code = "FINANCE_CONTRIBUTION_SOURCE_UNDETERMINED"


class ContributionVerificationIncompleteError(FinanceError, ValueError):
    """A required verification or declaration is missing (`ФИН-16`)."""

    reason_code = "FINANCE_CONTRIBUTION_VERIFICATION_INCOMPLETE"


class ContributionClassificationUndeterminedError(FinanceError, ValueError):
    """No policy-bound classification could be determined (`ФИН-41`)."""

    reason_code = "FINANCE_CONTRIBUTION_CLASSIFICATION_UNDETERMINED"


class ContributionProhibitedError(FinanceError, ValueError):
    """Policy classifies this contribution as prohibited or restricted
    (`ФИН-16`)."""

    reason_code = "FINANCE_CONTRIBUTION_PROHIBITED"


class ContributionAggregationUnresolvedError(FinanceError, ValueError):
    """The aggregate over the relevant period and perimeter could not be
    resolved (`ФИН-14`, `ФИН-15`)."""

    reason_code = "FINANCE_CONTRIBUTION_AGGREGATION_UNRESOLVED"


class ContributionReturnRequiredError(FinanceError, ValueError):
    """A return obligation exists and blocks the requested action
    (`ФИН-17`)."""

    reason_code = "FINANCE_CONTRIBUTION_RETURN_REQUIRED"


class InKindValuationMissingError(FinanceError, ValueError):
    """A non-monetary contribution or benefit lacks a valuation basis
    (`ФИН-18`)."""

    reason_code = "FINANCE_IN_KIND_VALUATION_MISSING"


class ValuationMethodMissingError(FinanceError, ValueError):
    """A valuation or revaluation lacks a method reference."""

    reason_code = "FINANCE_VALUATION_METHOD_MISSING"


class CounterPerformanceMissingError(FinanceError, ValueError):
    """Sponsorship approval without a counter-performance record and
    without an explicit policy classification stating none exists
    (`ФИН-19`)."""

    reason_code = "FINANCE_COUNTER_PERFORMANCE_MISSING"


class SponsorshipDisclosureIncompleteError(FinanceError, ValueError):
    """A required disclosure classification or declaration is missing
    (`ФИН-19`, `ФИН-35`)."""

    reason_code = "FINANCE_SPONSORSHIP_DISCLOSURE_INCOMPLETE"


# ---------------------------------------------------------------------------
# Payments, obligations, evidence
# ---------------------------------------------------------------------------


class PaymentAuthorizationMissingError(FinanceError, ValueError):
    """Settlement was attempted without a valid authorization
    (`ФИН-31`)."""

    reason_code = "FINANCE_PAYMENT_AUTHORIZATION_MISSING"


class WriteOffNotAuthorizedError(FinanceError, PermissionError):
    """A write-off lacks the authority or dual control policy requires."""

    reason_code = "FINANCE_WRITE_OFF_NOT_AUTHORIZED"


class EvidenceReferenceMissingError(FinanceError, ValueError):
    """A required evidence or document reference is absent (`ФИН-18`,
    `ФИН-21`)."""

    reason_code = "FINANCE_EVIDENCE_REFERENCE_MISSING"


class EvidenceAssertionUnavailableError(FinanceError, ValueError):
    """An assertion about a document - authentic, signed, admitted - is
    required, and only PACK-11 can make it (`ФИН-21`)."""

    reason_code = "FINANCE_EVIDENCE_ASSERTION_UNAVAILABLE"


class RetentionBindingMissingError(FinanceError, ValueError):
    """A governed finance record has no PACK-09 record-class binding
    (`ФИН-22`, `ФИН-23`)."""

    reason_code = "FINANCE_RETENTION_BINDING_MISSING"


# ---------------------------------------------------------------------------
# Reporting, audit, publication
# ---------------------------------------------------------------------------


class ReportingPerimeterUndeterminedError(FinanceError, ValueError):
    """No effective perimeter definition for the period (`ФИН-41`)."""

    reason_code = "FINANCE_REPORTING_PERIMETER_UNDETERMINED"


class ReportSnapshotMissingError(FinanceError, ValueError):
    """Preparation, validation or submission was attempted without a
    frozen snapshot (`ФИН-24`)."""

    reason_code = "FINANCE_REPORT_SNAPSHOT_MISSING"


class ReportSnapshotMismatchError(FinanceError, ValueError):
    """The report version is bound to a different snapshot than the one
    presented (`ФИН-24`, `ФИН-25`)."""

    reason_code = "FINANCE_REPORT_SNAPSHOT_MISMATCH"


class ReportValidationIncompleteError(FinanceError, ValueError):
    """Required validations have not completed, or blocking findings are
    open (`ФИН-33`)."""

    reason_code = "FINANCE_REPORT_VALIDATION_INCOMPLETE"


class ReportApprovalMissingError(FinanceError, ValueError):
    """The action requires an approval that has not been recorded
    (`ФИН-33`)."""

    reason_code = "FINANCE_REPORT_APPROVAL_MISSING"


class ReportSignOffMissingError(FinanceError, ValueError):
    """The action requires the legally responsible sign-off (`ФИН-33`)."""

    reason_code = "FINANCE_REPORT_SIGN_OFF_MISSING"


class ReportStatusUnknownError(FinanceError, ValueError):
    """The report status could not be determined - fail closed
    (`ФИН-41`)."""

    reason_code = "FINANCE_REPORT_STATUS_UNKNOWN"


class AuditIncompleteError(FinanceError, ValueError):
    """Auditor review requires a concluded engagement for this scope and
    period (`ФИН-29`, `ФИН-33`)."""

    reason_code = "FINANCE_AUDIT_INCOMPLETE"


class AuditorIndependenceViolationError(FinanceError, PermissionError):
    """The candidate auditor fails the independence check for this scope
    and period (`ФИН-29`, `ФИН-30`)."""

    reason_code = "FINANCE_AUDITOR_INDEPENDENCE_VIOLATION"


class ExternalAcknowledgementNotAuthoritativeError(FinanceError, ValueError):
    """An acknowledgement, receipt, delivery record or read status was
    offered as acceptance (`ФИН-26`, `ФИН-27`)."""

    reason_code = "FINANCE_EXTERNAL_ACKNOWLEDGEMENT_NOT_AUTHORITATIVE"


class ExternalAcceptanceMissingError(FinanceError, ValueError):
    """A transition to an accepted state was attempted without an
    explicit authoritative external reference (`ФИН-26`)."""

    reason_code = "FINANCE_EXTERNAL_ACCEPTANCE_MISSING"


class StatisticalDisclosureRiskError(FinanceError, ValueError):
    """The requested view would breach the small-cell or combination
    rules (`ФИН-35`)."""

    reason_code = "FINANCE_STATISTICAL_DISCLOSURE_RISK"


class ForbiddenIdentityLinkageError(FinanceError, ValueError):
    """A global person identifier, membership identifier or other
    prohibited identity linkage was submitted to a finance record or a
    finance event (`ФИН-01`, `ФИН-02`, `ФИН-36`)."""

    reason_code = "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


class PartyHandlePurposeMismatchError(FinanceError, ValueError):
    """A handle was presented for a purpose or perimeter it was not
    minted for (`ФИН-01`)."""

    reason_code = "FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH"


class PartyHandleResolutionDeniedError(FinanceError, PermissionError):
    """Handle resolution was attempted without the separate resolution
    authority (`ФИН-01`)."""

    reason_code = "FINANCE_PARTY_HANDLE_RESOLUTION_DENIED"


class PolicyMissingError(FinanceError, ValueError):
    """No applicable policy of the required kind exists for this scope
    and date (`ФИН-41`)."""

    reason_code = "FINANCE_POLICY_MISSING"


class PolicyVersionUnknownError(FinanceError, ValueError):
    """The referenced policy version does not exist or is not readable
    (`ФИН-41`)."""

    reason_code = "FINANCE_POLICY_VERSION_UNKNOWN"


class CrossScopeConsolidationDeniedError(FinanceError, PermissionError):
    """Consolidation lacks explicit authority, or would write into a
    lower scope (`ФИН-37`)."""

    reason_code = "FINANCE_CROSS_SCOPE_CONSOLIDATION_DENIED"


class FinanceAuthorityMissingError(FinanceError, PermissionError):
    """No active, scope-matching finance authority for this action
    (`ФИН-45`)."""

    reason_code = "FINANCE_AUTHORITY_MISSING"


class PublicationNotAllowedError(FinanceError, PermissionError):
    """Publication without a separate publication authorization, or of a
    version that is not approved and audited (`ФИН-28`, `ФИН-34`)."""

    reason_code = "PUBLICATION_NOT_ALLOWED"


class UnauthorizedStateTransitionError(FinanceError, ValueError):
    """The requested lifecycle transition is not in the allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


# ---------------------------------------------------------------------------
# Reused, pre-existing codes (never shadowed by FINANCE_ duplicates)
# ---------------------------------------------------------------------------


class OrganizationScopeMismatchError(FinanceError, PermissionError):
    """The asserted organizational scope does not match the target
    record's (`ФИН-03`)."""

    reason_code = "ORGANIZATION_SCOPE_MISMATCH"


class OrganizationScopeUndeterminedError(FinanceError, PermissionError):
    """Organizational scope could not be determined - default deny
    (`ФИН-04`)."""

    reason_code = "ORGANIZATION_SCOPE_UNDETERMINED"


class AuthorityRoleIncompatibleError(FinanceError, PermissionError):
    """The actor holds a role combination canon 19f.14 forbids
    (`ФИН-30`)."""

    reason_code = "AUTHORITY_ROLE_INCOMPATIBLE"


class SelfApprovalProhibitedError(FinanceError, PermissionError):
    """Self-approval of a personally created or personally benefiting act
    (`ФИН-31`)."""

    reason_code = "CONFLICT_REVIEW_SELF_APPROVAL_PROHIBITED"


class ConflictOfInterestUndeclaredError(FinanceError, PermissionError):
    """Conflict state is undeclared for a protected action - fail closed
    (`ФИН-32`)."""

    reason_code = "CONFLICT_OF_INTEREST_UNDECLARED"


class ConflictOfInterestBlockingError(FinanceError, PermissionError):
    """A declared conflict blocks this action (`ФИН-32`)."""

    reason_code = "CONFLICT_OF_INTEREST_BLOCKING"


class RecordUnderLegalHoldError(FinanceError, ValueError):
    """A PACK-09 legal hold blocks the disposal-relevant action
    (`ФИН-22`)."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


class GovernedRecordDeletionForbiddenError(FinanceError, ValueError):
    """Any deletion attempt on a governed finance record (`ФИН-05`)."""

    reason_code = "GOVERNED_RECORD_DELETION_FORBIDDEN"


class FinanceRecordNotFoundError(FinanceError, ValueError):
    """Unknown record - also the deliberately non-disclosing answer for a
    record that exists in another organizational scope (`ФИН-03`)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class OptimisticConcurrencyConflictError(FinanceError, ValueError):
    """A stale `expected_*_version` was presented."""

    reason_code = "OPTIMISTIC_CONCURRENCY_CONFLICT"


class IdempotencyConflictError(FinanceError, ValueError):
    """The same `event_id` was replayed with a different payload; the
    identical payload returns the recorded result instead."""

    reason_code = "FINANCE_IDEMPOTENCY_CONFLICT"


class PermissionDeniedError(FinanceError, PermissionError):
    """The caller holds no authority for this operation at all."""

    reason_code = "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# Technical, non-governed failures
# ---------------------------------------------------------------------------


class FinanceTechnicalError(RuntimeError):
    """A technical failure that is deliberately *not* a business reason
    code: an adapter fault, a serialization failure, a programming error
    surfaced at a port boundary.

    Documented separately in
    `docs/contracts/finance-command-query-contracts.md` so that a
    technical fault can never be mistaken for a governed refusal."""

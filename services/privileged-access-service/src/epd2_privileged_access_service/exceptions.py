"""Privileged Access Service exceptions, one class per stable reason code
(PACK-12; ADR-061 through ADR-068; canon section 24's reason-code
standard applied to this pack).

Every class below carries a `reason_code` class attribute whose literal
string is registered in `contracts/reason-codes/pack-12.yml`. No PACK-12
code path may raise a bare `ValueError` or `PermissionError` with a
free-text message in place of one of these (`P12-RSN-002`: a single
generic `FORBIDDEN` is forbidden, because a refusal is the only thing an
operator, an auditor and an affected participant all see).

The hierarchy mirrors every earlier pack's: structural and lifecycle
violations subclass `ValueError`; authorization, scope and
separation-of-duties violations subclass `PermissionError`, so a caller
that already distinguishes those two categories across PACK-02 through
PACK-11 needs no PACK-12-specific handling.

Four prefixes, matching the four governed concerns (`P12-RSN-001`):

- `PRIVILEGE_*` - privileged administration, PAM, break-glass, sessions;
- `SEARCH_*` - authorization-aware search and indexing;
- `EXPORT_*` - governed data export and DLP;
- `DISCLOSURE_*` - statistical disclosure control.

Codes owned by earlier packs are re-raised through the thin subclasses at
the end of this module rather than shadowed by a PACK-12 synonym
(`P12-RSN-003`): one fact keeps one code.
"""

from __future__ import annotations


class PrivilegedAccessError(Exception):
    """Base class for every governed PACK-12 refusal.

    `reason_code` is always a string registered in
    `contracts/reason-codes/pack-12.yml`."""

    reason_code: str = "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# PRIVILEGE_* - roles, authority, separation of duties
# ---------------------------------------------------------------------------


class PrivilegeAuthorityMissingError(PrivilegedAccessError, PermissionError):
    """No active, scope-matching privileged authority exists for this
    operation (`P12-PAM-002`)."""

    reason_code = "PRIVILEGE_AUTHORITY_MISSING"


class SeparationOfDutiesConflictError(PrivilegedAccessError, PermissionError):
    """The act would place two separated duties with one subject."""

    reason_code = "PRIVILEGE_SEPARATION_OF_DUTIES_CONFLICT"


class RoleCombinationProhibitedError(PrivilegedAccessError, PermissionError):
    """The subject holds a pair the incompatibility matrix forbids, or a
    composition of assignments would yield an institutional authority the
    subject does not hold (`P12-ROLE-012`, `P12-ROLE-021`)."""

    reason_code = "PRIVILEGE_ROLE_COMBINATION_PROHIBITED"


class SelfApprovalProhibitedError(PrivilegedAccessError, PermissionError):
    """Requester and approver are the same subject (`P12-PAM-004`)."""

    reason_code = "PRIVILEGE_SELF_APPROVAL_PROHIBITED"


class InsufficientApproverError(PrivilegedAccessError, PermissionError):
    """The presented approver lacks the role the risk class requires."""

    reason_code = "PRIVILEGE_INSUFFICIENT_APPROVER"


class ApproverCountInsufficientError(PrivilegedAccessError, PermissionError):
    """Fewer approvers than the risk class requires."""

    reason_code = "PRIVILEGE_APPROVER_COUNT_INSUFFICIENT"


class PrivilegeScopeMismatchError(PrivilegedAccessError, PermissionError):
    """The requested resource lies outside the grant's resource scope."""

    reason_code = "PRIVILEGE_SCOPE_MISMATCH"


class PrivilegePurposeMismatchError(PrivilegedAccessError, PermissionError):
    """The operation does not serve the grant's declared purpose."""

    reason_code = "PRIVILEGE_PURPOSE_MISMATCH"


class OperationNotGrantedError(PrivilegedAccessError, PermissionError):
    """The operation is outside the grant's operation set."""

    reason_code = "PRIVILEGE_OPERATION_NOT_GRANTED"


class PrivilegeOrganizationMismatchError(PrivilegedAccessError, PermissionError):
    """The grant belongs to a different organization (`P12-ORG-004`)."""

    reason_code = "PRIVILEGE_ORGANIZATION_MISMATCH"


class GrantExpiredError(PrivilegedAccessError, PermissionError):
    """The grant's end instant has passed (`P12-PAM-006`)."""

    reason_code = "PRIVILEGE_GRANT_EXPIRED"


class GrantRevokedError(PrivilegedAccessError, PermissionError):
    """The grant was withdrawn before expiry (`P12-PAM-007`)."""

    reason_code = "PRIVILEGE_GRANT_REVOKED"


class GrantNotActivatedError(PrivilegedAccessError, PermissionError):
    """The grant is approved but not yet activated."""

    reason_code = "PRIVILEGE_GRANT_NOT_ACTIVATED"


class GrantDormantError(PrivilegedAccessError, PermissionError):
    """The grant is unused past the dormancy interval and requires
    review before further use (`P12-PAM-009`)."""

    reason_code = "PRIVILEGE_GRANT_DORMANT"


class StandingAccessProhibitedError(PrivilegedAccessError, ValueError):
    """A permanent, unbounded grant was requested (`P12-PAM-003`)."""

    reason_code = "PRIVILEGE_STANDING_ACCESS_PROHIBITED"


class JustificationMissingError(PrivilegedAccessError, ValueError):
    """No written justification was supplied (`P12-PAM-001`)."""

    reason_code = "PRIVILEGE_JUSTIFICATION_MISSING"


class RiskClassificationUndeterminedError(PrivilegedAccessError, ValueError):
    """The risk class could not be determined; fail closed."""

    reason_code = "PRIVILEGE_RISK_CLASSIFICATION_UNDETERMINED"


class AssignmentNotGovernedError(PrivilegedAccessError, PermissionError):
    """An operational assignment was asserted without governed authority
    (`P12-ROLE-017`)."""

    reason_code = "PRIVILEGE_ASSIGNMENT_NOT_GOVERNED"


class AssignmentNotEffectiveDatedError(PrivilegedAccessError, ValueError):
    """An operational assignment lacks scope, purpose or effective dating
    (`P12-ROLE-018`)."""

    reason_code = "PRIVILEGE_ASSIGNMENT_NOT_EFFECTIVE_DATED"


class InstitutionalAuthorityNotExtendableError(PrivilegedAccessError, PermissionError):
    """An operational assignment was used to claim institutional
    authority (`P12-ROLE-019`)."""

    reason_code = "PRIVILEGE_INSTITUTIONAL_AUTHORITY_NOT_EXTENDABLE"


# ---------------------------------------------------------------------------
# PRIVILEGE_* - break-glass
# ---------------------------------------------------------------------------


class BreakGlassConditionAbsentError(PrivilegedAccessError, ValueError):
    """No documented emergency condition (`P12-BG-002`)."""

    reason_code = "PRIVILEGE_BREAK_GLASS_CONDITION_ABSENT"


class BreakGlassDualControlMissingError(PrivilegedAccessError, PermissionError):
    """Activator and approver are the same, or the approver is absent
    (`P12-BG-003`)."""

    reason_code = "PRIVILEGE_BREAK_GLASS_DUAL_CONTROL_MISSING"


class BreakGlassNotificationUndeliveredError(PrivilegedAccessError, ValueError):
    """Out-of-band notification could not be dispatched. The activation
    escalates and never silently completes (`P12-BG-008`)."""

    reason_code = "PRIVILEGE_BREAK_GLASS_NOTIFICATION_UNDELIVERED"


class BreakGlassScopeTooBroadError(PrivilegedAccessError, ValueError):
    """The requested emergency scope exceeds the narrow-scope requirement
    (`P12-BG-004`)."""

    reason_code = "PRIVILEGE_BREAK_GLASS_SCOPE_TOO_BROAD"


class BreakGlassRenewalRequiresDecisionError(PrivilegedAccessError, ValueError):
    """Extension was attempted in place of a new dual-controlled decision
    (`P12-BG-013`)."""

    reason_code = "PRIVILEGE_BREAK_GLASS_RENEWAL_REQUIRES_DECISION"


# ---------------------------------------------------------------------------
# PRIVILEGE_* - session evidence and audit custody
# ---------------------------------------------------------------------------


class SessionEvidenceIncompleteError(PrivilegedAccessError, ValueError):
    """A session cannot be sealed because required evidence fields are
    missing (`P12-SES-001`)."""

    reason_code = "PRIVILEGE_SESSION_EVIDENCE_INCOMPLETE"


class AuditMutationProhibitedError(PrivilegedAccessError, PermissionError):
    """An attempt to modify or delete an audit record under custody
    (`P12-ROLE-006`)."""

    reason_code = "PRIVILEGE_AUDIT_MUTATION_PROHIBITED"


class PrivilegedSessionSecretForbiddenError(PrivilegedAccessError, ValueError):
    """Session evidence, or an event payload, carried a secret, a
    credential or a full sensitive payload (`P12-SES-002`)."""

    reason_code = "PRIVILEGE_SESSION_SECRET_FORBIDDEN"


class IdempotencyConflictError(PrivilegedAccessError, ValueError):
    """The same `event_id` was presented for a different request."""

    reason_code = "PRIVILEGE_IDEMPOTENCY_CONFLICT"


# ---------------------------------------------------------------------------
# SEARCH_*
# ---------------------------------------------------------------------------


class SearchSourceAuthorizationDeniedError(PrivilegedAccessError, PermissionError):
    """The requester could not open the source record directly, so search
    must not surface it (`P12-SRCH-003`)."""

    reason_code = "SEARCH_SOURCE_AUTHORIZATION_DENIED"


class SearchScopeUndeterminedError(PrivilegedAccessError, PermissionError):
    """No organization scope was resolvable; default deny
    (`P12-SRCH-010`)."""

    reason_code = "SEARCH_SCOPE_UNDETERMINED"


class SearchOrganizationMismatchError(PrivilegedAccessError, PermissionError):
    """The query reaches outside the requester's organizational scope."""

    reason_code = "SEARCH_ORGANIZATION_MISMATCH"


class SearchPurposeMismatchError(PrivilegedAccessError, PermissionError):
    """The declared purpose does not admit this query (`P12-SRCH-011`)."""

    reason_code = "SEARCH_PURPOSE_MISMATCH"


class SearchModeNotPermittedError(PrivilegedAccessError, PermissionError):
    """The requested search mode is not available to this subject."""

    reason_code = "SEARCH_MODE_NOT_PERMITTED"


class HighlyConfidentialDomainExcludedError(PrivilegedAccessError, PermissionError):
    """The target domain is excluded from the index by policy
    (`P12-HCD-001`)."""

    reason_code = "SEARCH_HIGHLY_CONFIDENTIAL_DOMAIN_EXCLUDED"


class SearchBallotContentProhibitedError(PrivilegedAccessError, PermissionError):
    """Ballot-level material may never be indexed or searched
    (`P12-VOTE-001`, `P12-HCD-003`). An occurrence is an incident, not a
    routine denial."""

    reason_code = "SEARCH_BALLOT_CONTENT_PROHIBITED"


class SearchUncertifiedResultProhibitedError(PrivilegedAccessError, PermissionError):
    """Intermediate, partial or non-certified tally material may never be
    searched (`P12-VOTE-001`, `P12-VOTE-006`)."""

    reason_code = "SEARCH_UNCERTIFIED_RESULT_PROHIBITED"


class SearchIndexAuthorizationStaleError(PrivilegedAccessError, PermissionError):
    """The index view could not be reconciled with current source
    authorization (`P12-SRCH-005`)."""

    reason_code = "SEARCH_INDEX_AUTHORIZATION_STALE"


class SearchCacheContextMismatchError(PrivilegedAccessError, PermissionError):
    """A cache entry did not match the effective authorization context
    (`P12-SRCH-009`)."""

    reason_code = "SEARCH_CACHE_CONTEXT_MISMATCH"


class IndexPolicyViolationError(PrivilegedAccessError, ValueError):
    """An indexing attempt violates `IndexPolicy` or `IndexFieldPolicy`."""

    reason_code = "SEARCH_INDEX_POLICY_VIOLATION"


# ---------------------------------------------------------------------------
# EXPORT_*
# ---------------------------------------------------------------------------


class ExportAuthorityMissingError(PrivilegedAccessError, PermissionError):
    """No export authority for this record class in this scope."""

    reason_code = "EXPORT_AUTHORITY_MISSING"


class DataOwnerMissingError(PrivilegedAccessError, PermissionError):
    """No authoritative data owner could be resolved (`P12-ORG-007`)."""

    reason_code = "EXPORT_DATA_OWNER_MISSING"


class ExportApprovalMissingError(PrivilegedAccessError, PermissionError):
    """No approval, or approval by an ineligible subject."""

    reason_code = "EXPORT_APPROVAL_MISSING"


class ExportSelfApprovalProhibitedError(PrivilegedAccessError, PermissionError):
    """The requester approved their own export (`P12-EXP-006`)."""

    reason_code = "EXPORT_SELF_APPROVAL_PROHIBITED"


class ExportPurposeMissingError(PrivilegedAccessError, ValueError):
    """No declared purpose (`P12-EXP-002`)."""

    reason_code = "EXPORT_PURPOSE_MISSING"


class ExportPurposeMismatchError(PrivilegedAccessError, PermissionError):
    """The requested data does not serve the declared purpose."""

    reason_code = "EXPORT_PURPOSE_MISMATCH"


class ExportLegalBasisMissingError(PrivilegedAccessError, ValueError):
    """A basis reference is required for this class or recipient and is
    absent."""

    reason_code = "EXPORT_LEGAL_BASIS_MISSING"


class ExportOrganizationMismatchError(PrivilegedAccessError, PermissionError):
    """Cross-organizational export without its own scope and basis
    (`P12-ORG-006`)."""

    reason_code = "EXPORT_ORGANIZATION_MISMATCH"


class RecipientNotAuthorizedError(PrivilegedAccessError, PermissionError):
    """The recipient or recipient category may not receive this class."""

    reason_code = "EXPORT_RECIPIENT_NOT_AUTHORIZED"


class RecipientObligationMissingError(PrivilegedAccessError, ValueError):
    """Required downstream obligations were not recorded
    (`P12-EXP-014`)."""

    reason_code = "EXPORT_RECIPIENT_OBLIGATION_MISSING"


class TransferChannelProhibitedError(PrivilegedAccessError, PermissionError):
    """The requested channel is not permitted for this class or
    recipient."""

    reason_code = "EXPORT_TRANSFER_CHANNEL_PROHIBITED"


class FieldNotExportableError(PrivilegedAccessError, PermissionError):
    """A requested field is denied by field policy (`P12-EXP-008`)."""

    reason_code = "EXPORT_FIELD_NOT_EXPORTABLE"


class BulkExtractionNotAuthorizedError(PrivilegedAccessError, PermissionError):
    """Read permission was presented as bulk-export authority
    (`P12-EXP-005`)."""

    reason_code = "EXPORT_BULK_EXTRACTION_NOT_AUTHORIZED"


class SearchPermissionInsufficientError(PrivilegedAccessError, PermissionError):
    """Search permission was presented as export authority
    (`P12-EXP-004`)."""

    reason_code = "EXPORT_SEARCH_PERMISSION_INSUFFICIENT"


class AdminPrivilegeInsufficientError(PrivilegedAccessError, PermissionError):
    """Administrative privilege was presented as export authority
    (`P12-EXP-006`)."""

    reason_code = "EXPORT_ADMIN_PRIVILEGE_INSUFFICIENT"


class ExportBallotContentProhibitedError(PrivilegedAccessError, PermissionError):
    """Ballot-level material may never be exported (`P12-VOTE-001`)."""

    reason_code = "EXPORT_BALLOT_CONTENT_PROHIBITED"


class ExportUncertifiedResultProhibitedError(PrivilegedAccessError, PermissionError):
    """Intermediate, partial or non-certified tally material may never be
    exported (`P12-VOTE-001`, `P12-VOTE-006`)."""

    reason_code = "EXPORT_UNCERTIFIED_RESULT_PROHIBITED"


class ResultPublicationNotOwnedError(PrivilegedAccessError, PermissionError):
    """A certified result may be released only by the authoritative
    voting and result-certification domain, never through a PACK-12
    export path (`P12-VOTE-004`, `P12-VOTE-005`)."""

    reason_code = "EXPORT_RESULT_PUBLICATION_NOT_OWNED"


class LegalHoldNotAuthorizationError(PrivilegedAccessError, PermissionError):
    """A legal hold was presented as permission to export
    (`P12-EXP-017`)."""

    reason_code = "EXPORT_LEGAL_HOLD_NOT_AUTHORIZATION"


class SourceRecordRevokedError(PrivilegedAccessError, ValueError):
    """A source record is revoked or deleted and may not enter a new
    export (`P12-EXP-018`)."""

    reason_code = "EXPORT_SOURCE_RECORD_REVOKED"


class ExportManifestMissingError(PrivilegedAccessError, ValueError):
    """No immutable manifest is bound to the artifact (`P12-EXP-021`)."""

    reason_code = "EXPORT_MANIFEST_MISSING"


class ExportManifestMismatchError(PrivilegedAccessError, ValueError):
    """The artifact does not match its manifest digest."""

    reason_code = "EXPORT_MANIFEST_MISMATCH"


class ArtifactExpiredError(PrivilegedAccessError, PermissionError):
    """The artifact's expiry has passed (`P12-EXP-010`)."""

    reason_code = "EXPORT_ARTIFACT_EXPIRED"


class ArtifactRevokedError(PrivilegedAccessError, PermissionError):
    """Authorization for the artifact was withdrawn (`P12-EXP-012`)."""

    reason_code = "EXPORT_ARTIFACT_REVOKED"


# ---------------------------------------------------------------------------
# EXPORT_DLP_*
# ---------------------------------------------------------------------------


class DlpReviewRequiredError(PrivilegedAccessError, ValueError):
    """Manual DLP review is required before a decision."""

    reason_code = "EXPORT_DLP_REVIEW_REQUIRED"


class DlpAssessmentMissingError(PrivilegedAccessError, ValueError):
    """No completed DLP assessment (`P12-DLP-002`)."""

    reason_code = "EXPORT_DLP_ASSESSMENT_MISSING"


class DlpAssessmentIncompleteError(PrivilegedAccessError, ValueError):
    """Detection could not complete; fail closed (`P12-DLP-005`)."""

    reason_code = "EXPORT_DLP_ASSESSMENT_INCOMPLETE"


class DlpForbiddenDataDetectedError(PrivilegedAccessError, ValueError):
    """Forbidden data was found in the candidate set."""

    reason_code = "EXPORT_DLP_FORBIDDEN_DATA_DETECTED"


class DlpSizeLimitExceededError(PrivilegedAccessError, ValueError):
    """Export exceeds the permitted size."""

    reason_code = "EXPORT_DLP_SIZE_LIMIT_EXCEEDED"


class DlpFrequencyLimitExceededError(PrivilegedAccessError, ValueError):
    """Export frequency exceeds the permitted rate."""

    reason_code = "EXPORT_DLP_FREQUENCY_LIMIT_EXCEEDED"


class DlpUnusualVolumeReviewError(PrivilegedAccessError, ValueError):
    """Volume anomaly requires review."""

    reason_code = "EXPORT_DLP_UNUSUAL_VOLUME_REVIEW"


class DlpRepeatedRequestRiskError(PrivilegedAccessError, ValueError):
    """Repeated similar requests indicate an extraction pattern."""

    reason_code = "EXPORT_DLP_REPEATED_REQUEST_RISK"


class DlpAccessLimitExceededError(PrivilegedAccessError, PermissionError):
    """The artifact's access or download limit has been reached."""

    reason_code = "EXPORT_DLP_ACCESS_LIMIT_EXCEEDED"


# ---------------------------------------------------------------------------
# DISCLOSURE_*
# ---------------------------------------------------------------------------


class DisclosureAssessmentMissingError(PrivilegedAccessError, ValueError):
    """No disclosure-risk assessment where one is required
    (`P12-SDC-001`)."""

    reason_code = "DISCLOSURE_ASSESSMENT_MISSING"


class DisclosureThresholdFailedError(PrivilegedAccessError, ValueError):
    """A cohort is below the applicable threshold."""

    reason_code = "DISCLOSURE_THRESHOLD_FAILED"


class DisclosureSuppressionRequiredError(PrivilegedAccessError, ValueError):
    """Release requires suppression that was not applied."""

    reason_code = "DISCLOSURE_SUPPRESSION_REQUIRED"


class DisclosureComplementRecoverableError(PrivilegedAccessError, ValueError):
    """A suppressed value is recoverable from totals or neighbours
    (`P12-SDC-007`)."""

    reason_code = "DISCLOSURE_COMPLEMENT_RECOVERABLE"


class DisclosureRepeatedQueryRiskError(PrivilegedAccessError, ValueError):
    """Successive queries permit differencing (`P12-SDC-003`)."""

    reason_code = "DISCLOSURE_REPEATED_QUERY_RISK"


class DisclosureCumulativeReleaseRiskError(PrivilegedAccessError, ValueError):
    """Individually permissible releases are jointly re-identifying
    (`P12-SDC-004`)."""

    reason_code = "DISCLOSURE_CUMULATIVE_RELEASE_RISK"


class DisclosureExceptionNotApprovedError(PrivilegedAccessError, PermissionError):
    """An override was applied without an approved exception
    (`P12-SDC-006`)."""

    reason_code = "DISCLOSURE_EXCEPTION_NOT_APPROVED"


class DisclosureExceptionExpiredError(PrivilegedAccessError, PermissionError):
    """The approved exception's conditions no longer hold."""

    reason_code = "DISCLOSURE_EXCEPTION_EXPIRED"


class DisclosurePublicationAuthorityMissingError(PrivilegedAccessError, PermissionError):
    """Raw-data access was presented as authority to publish
    (`P12-SDC-002`)."""

    reason_code = "DISCLOSURE_PUBLICATION_AUTHORITY_MISSING"


class ClassificationUnmappedError(PrivilegedAccessError, ValueError):
    """The source classification has no enforcement-tier mapping; fail
    closed (`P12-CLS-005`)."""

    reason_code = "DISCLOSURE_CLASSIFICATION_UNMAPPED"


class ClassificationDowngradeProhibitedError(PrivilegedAccessError, ValueError):
    """An enforcement tier was used to lower an authoritative source
    classification (`P12-CLS-001`)."""

    reason_code = "DISCLOSURE_CLASSIFICATION_DOWNGRADE_PROHIBITED"


class ReleaseHistoryUnavailableError(PrivilegedAccessError, ValueError):
    """Required release history could not be read, so cumulative risk
    cannot be evaluated; fail closed (`P12-SDC-004`)."""

    reason_code = "DISCLOSURE_RELEASE_HISTORY_UNAVAILABLE"


# ---------------------------------------------------------------------------
# Codes owned by earlier packs, re-raised rather than shadowed
# ---------------------------------------------------------------------------


class OrganizationScopeMismatchError(PrivilegedAccessError, PermissionError):
    """PACK-08's code. Cross-scope refusal."""

    reason_code = "ORGANIZATION_SCOPE_MISMATCH"


class OrganizationScopeUndeterminedError(PrivilegedAccessError, PermissionError):
    """PACK-08's code. Undeterminable scope; default deny."""

    reason_code = "ORGANIZATION_SCOPE_UNDETERMINED"


class CrossScopeAccessDeniedError(PrivilegedAccessError, PermissionError):
    """PACK-08's code. Cross-scope read without an access mode."""

    reason_code = "CROSS_SCOPE_ACCESS_DENIED"


class AuthorityRoleIncompatibleError(PrivilegedAccessError, PermissionError):
    """PACK-08's code. Role pair violation at assignment time."""

    reason_code = "AUTHORITY_ROLE_INCOMPATIBLE"


class RecordUnderLegalHoldError(PrivilegedAccessError, PermissionError):
    """PACK-09's code. Disposal blocked by a hold."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


class LegalHoldStateUnknownError(PrivilegedAccessError, PermissionError):
    """PACK-09's code. Indeterminate hold; fail closed."""

    reason_code = "LEGAL_HOLD_STATE_UNKNOWN"


class RecordNotFoundError(PrivilegedAccessError, ValueError):
    """PACK-02's code. Unknown grant, request or artifact identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class OptimisticConcurrencyConflictError(PrivilegedAccessError, ValueError):
    """PACK-02's code. Stale expected version on a governed object."""

    reason_code = "OPTIMISTIC_CONCURRENCY_CONFLICT"


class ForbiddenTransitionError(PrivilegedAccessError, ValueError):
    """PACK-02's code. A lifecycle transition the state machine forbids."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownStatusError(PrivilegedAccessError, ValueError):
    """PACK-02's code. An unrecognised status string."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class PermissionDeniedError(PrivilegedAccessError, PermissionError):
    """PACK-02's generic code, used only where no specific code fits."""

    reason_code = "PERMISSION_DENIED"


class PublicationNotAllowedError(PrivilegedAccessError, PermissionError):
    """PACK-04's code. Publication without its own authorization."""

    reason_code = "PUBLICATION_NOT_ALLOWED"


class DisclosurePolicyViolationError(PrivilegedAccessError, ValueError):
    """PACK-04's code. Emission violating an applicable disclosure
    policy."""

    reason_code = "DISCLOSURE_POLICY_VIOLATION"

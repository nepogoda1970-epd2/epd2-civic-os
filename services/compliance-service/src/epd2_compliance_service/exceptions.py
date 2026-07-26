"""Compliance Service exceptions, one per stable, machine-readable reason
code (canon section 24; ADR-004's registry rule, applied to PACK-09).

Every class below carries a `reason_code` class attribute whose literal
string is registered in `contracts/reason-codes/pack-09.yml` - verified
structurally by `tests/contract/test_reason_codes_registry.py`'s pack-09
parametrization. No compliance code path may raise a bare `ValueError`
or `PermissionError` with a free-text message in place of one of these
(PACK-09 required-invariant 14, "reason-coded denial").

The exception hierarchy deliberately mirrors every earlier pack's own:
structural/lifecycle violations subclass `ValueError`, authorization and
scope violations subclass `PermissionError`, so a caller that already
distinguishes those two categories across PACK-02 through PACK-08 needs
no PACK-09-specific handling to keep doing so.

Fail-closed codes (PACK-09 required-invariant 15) are grouped last: each
one names a *specific* condition under which the service refuses to act
because it could not establish a fact it needs, never a generic
catch-all. `ComplianceRecordNotFoundError` doubles as the deliberately
non-disclosing outcome for a cross-organization read (see
`application._resolve_in_scope_or_not_found`): a caller holding a
foreign organization's resource id learns nothing beyond "not found".

`UnknownComplianceRecordError` is retained as a backwards-compatible
alias of `ComplianceRecordNotFoundError` so the name used by the
pre-review PACK-09 draft keeps resolving; both carry the same
`VALIDATION_RECORD_NOT_FOUND` code.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Records governance / retention / destruction
# ---------------------------------------------------------------------------


class RetentionDispositionNotDueError(ValueError):
    """The calculated retention due time has not been reached."""

    reason_code = "RETENTION_DISPOSITION_NOT_DUE"


class RetentionStartUndeterminedError(ValueError):
    """No retention start event has been recorded for this record, so the
    retention due time cannot be calculated - fail closed rather than
    treat "no start" as "started at creation" (invariant 15)."""

    reason_code = "RETENTION_START_UNDETERMINED"


class RetentionPolicyVersionConflictError(ValueError):
    """A retention policy id/version pair is already registered with
    different content, or a supersession skipped the required version
    increment."""

    reason_code = "RETENTION_POLICY_VERSION_CONFLICT"


class RetentionPolicyRebindRequiresReevaluationError(ValueError):
    """A governed record's effective retention policy version changed and
    disposal eligibility has not been re-evaluated and re-authorized
    under the new version (invariant 5: no policy rewrite may silently
    authorize destruction of already-governed records)."""

    reason_code = "RETENTION_POLICY_REBIND_REQUIRES_REEVALUATION"


class DestructionAuthorizationRequiredError(ValueError):
    """Execution of a disposal/destruction was requested without a valid,
    matching `DestructionAuthorization` (invariant 4: destruction is
    never an ordinary CRUD delete)."""

    reason_code = "DESTRUCTION_AUTHORIZATION_REQUIRED"


class DestructionAuthorizationStaleError(ValueError):
    """The supplied `DestructionAuthorization` was issued against a
    different retention policy version or a different record version than
    the record now carries."""

    reason_code = "DESTRUCTION_AUTHORIZATION_STALE"


class DestructionAlreadyExecutedError(ValueError):
    """Destruction evidence already exists for this record and a second,
    *different* execution was attempted. An identical replay is
    idempotent and never reaches this error - see
    `application.execute_destruction`."""

    reason_code = "DESTRUCTION_ALREADY_EXECUTED"


class GovernedRecordDeletionForbiddenError(ValueError):
    """A caller attempted to remove a governed record through an ordinary
    delete path instead of the controlled disposal workflow."""

    reason_code = "GOVERNED_RECORD_DELETION_FORBIDDEN"


# ---------------------------------------------------------------------------
# Legal Hold
# ---------------------------------------------------------------------------


class RecordUnderLegalHoldError(PermissionError):
    """At least one active Legal Hold applies to this record; every
    destructive disposition is refused (invariant 3)."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


class LegalHoldScopeMismatchError(ValueError):
    """A Legal Hold was applied to, or evaluated against, a record in a
    different organizational scope."""

    reason_code = "LEGAL_HOLD_SCOPE_MISMATCH"


class LegalHoldTransitionInvalidError(ValueError):
    """A Legal Hold lifecycle transition is not permitted (for example
    releasing an already-released hold with different release
    metadata)."""

    reason_code = "LEGAL_HOLD_TRANSITION_INVALID"


class LegalHoldStateUnknownError(PermissionError):
    """The hold state relevant to this record could not be established -
    the operation is refused rather than assumed unheld (invariant 15)."""

    reason_code = "LEGAL_HOLD_STATE_UNKNOWN"


# ---------------------------------------------------------------------------
# Data catalog / processing registry
# ---------------------------------------------------------------------------


class ProcessingRegistryIncompleteError(ValueError):
    """A processing activity or data asset is missing a field the
    registry requires."""

    reason_code = "PROCESSING_REGISTRY_INCOMPLETE"


class ProcessingActivityTransitionInvalidError(ValueError):
    """The requested processing-activity lifecycle transition is not
    permitted."""

    reason_code = "PROCESSING_ACTIVITY_TRANSITION_INVALID"


class ProcessingRegistryIdentityPayloadRejectedError(ValueError):
    """A registry write carried a field this service refuses to store
    because it would amount to holding identity data (invariant 11:
    compliance-service never acquires eID/KYC identity)."""

    reason_code = "PROCESSING_REGISTRY_IDENTITY_PAYLOAD_REJECTED"


# ---------------------------------------------------------------------------
# Governed cases, deadlines, requests
# ---------------------------------------------------------------------------


class ProceduralCaseTransitionInvalidError(ValueError):
    """The requested procedural case state transition is not permitted."""

    reason_code = "PROCEDURAL_CASE_TRANSITION_INVALID"


class ProceduralCaseClosedError(ValueError):
    """A closed case cannot be modified by an ordinary command; reopening
    is its own governed transition."""

    reason_code = "PROCEDURAL_CASE_CLOSED"


class DeadlineTransitionInvalidError(ValueError):
    """The requested procedural deadline state transition is not
    permitted."""

    reason_code = "DEADLINE_TRANSITION_INVALID"


class DeadlineSilentReplacementRejectedError(ValueError):
    """A command would have created a second, competing deadline instance
    for a (case, deadline_code) pair that already has a live one, without
    an explicit supersession (invariant 7)."""

    reason_code = "DEADLINE_SILENT_REPLACEMENT_REJECTED"


class DeadlineTimezoneUndeterminedError(ValueError):
    """A deadline was supplied without an explicit IANA timezone, or with
    a naive datetime - due-date arithmetic is refused rather than
    silently assuming UTC (invariant 15)."""

    reason_code = "DEADLINE_TIMEZONE_UNDETERMINED"


class DataSubjectRequestTransitionInvalidError(ValueError):
    """The requested data-subject/legal request state transition is not
    permitted."""

    reason_code = "DATA_SUBJECT_REQUEST_TRANSITION_INVALID"


class IdentityVerificationInsufficientError(PermissionError):
    """A data-subject request cannot be answered because its identity
    verification status is not `verified`. No identity payload is stored
    or requested by this service to change that (invariant 11)."""

    reason_code = "IDENTITY_VERIFICATION_INSUFFICIENT"


# ---------------------------------------------------------------------------
# Arbitration / disputes / procedural independence
# ---------------------------------------------------------------------------


class ProceduralIndependenceViolationError(PermissionError):
    """The requested role assignment would breach independence: a party
    to the dispute, or the current case handler, cannot become the
    independent decision-maker, and nobody may appoint themselves
    (invariants 8 and 9)."""

    reason_code = "PROCEDURAL_INDEPENDENCE_VIOLATION"


class ProceduralRoleConflictError(PermissionError):
    """One party reference would hold two procedural roles that must stay
    separate (procedural authority / case handler / independent
    decision-maker)."""

    reason_code = "PROCEDURAL_ROLE_CONFLICT"


class ConflictOfInterestBlockingError(PermissionError):
    """A declared and confirmed conflict of interest makes this party
    ineligible for the requested procedural role or decision
    (invariant 10)."""

    reason_code = "CONFLICT_OF_INTEREST_BLOCKING"


class ConflictOfInterestUndeclaredError(ValueError):
    """An independent decision-maker assignment, or a decision, was
    attempted before the required conflict-of-interest declaration
    existed - fail closed (invariants 10 and 15)."""

    reason_code = "CONFLICT_OF_INTEREST_UNDECLARED"


class DecisionAuthorityMissingError(PermissionError):
    """The acting party does not hold a procedural role permitted to
    record this decision.

    Registered as `DECISION_AUTHORITY_DENIED` (Framework 0.8.1 section
    10's name). `DecisionAuthorityDeniedError` below is an alias."""

    reason_code = "DECISION_AUTHORITY_DENIED"


# ---------------------------------------------------------------------------
# Scope isolation and fail-closed guards
# ---------------------------------------------------------------------------


class CrossOrganizationCaseAccessDeniedError(PermissionError):
    """A read or write crossed its target's owning organizational scope
    without a valid, explicitly-presented cross-scope authority grant
    (PACK-09 required invariant 2; Framework 0.8.1 hard invariant 13,
    "региональный доступ работает по default deny").

    The registered code is `CROSS_SCOPE_ACCESS_DENIED` - the name
    Framework 0.8.1 section 10 uses. `CrossScopeAccessDeniedError` below
    is an alias for the same class, so either name resolves."""

    reason_code = "CROSS_SCOPE_ACCESS_DENIED"


class OrganizationScopeUndeterminedError(PermissionError):
    """The requesting context carried no resolvable organizational scope,
    or an entity was submitted without one; the operation is refused
    rather than defaulted (invariant 15)."""

    reason_code = "ORGANIZATION_SCOPE_UNDETERMINED"


class CrossScopeAuthorityInvalidError(PermissionError):
    """A cross-scope authority grant was presented but is unknown,
    expired, revoked, issued by the wrong organization, or does not carry
    the capability this operation needs."""

    reason_code = "CROSS_SCOPE_AUTHORITY_INVALID"


class ComplianceRecordNotFoundError(ValueError):
    """The referenced record does not exist *for this caller*.

    Deliberately identical for "no such record anywhere" and "the record
    exists but belongs to another organization and the caller presented
    no cross-scope authority", so a resource id from a foreign
    organization discloses nothing beyond this safe error."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


#: Backwards-compatible alias for the name the pre-review PACK-09 draft
#: used. Same class, same reason code - kept so no external caller breaks.
UnknownComplianceRecordError = ComplianceRecordNotFoundError


class ComplianceCommandConflictError(ValueError):
    """A command was replayed with the same `event_id` but different
    content (the CT-00-04 idempotency contract's conflict half)."""

    reason_code = "COMPLIANCE_COMMAND_CONFLICT"


class OptimisticConcurrencyConflictError(ValueError):
    """The caller-supplied `expected_version` does not match the stored
    record's current version."""

    reason_code = "OPTIMISTIC_CONCURRENCY_CONFLICT"


class PermissionDeniedError(PermissionError):
    """Generic authorization refusal, reusing PACK-02's pre-existing
    registered code rather than inventing a PACK-09 synonym."""

    reason_code = "PERMISSION_DENIED"


#: Framework 0.8.1 section 10 names these two codes; the classes above
#: carry them. Aliases so either name resolves at a call site.
CrossScopeAccessDeniedError = CrossOrganizationCaseAccessDeniedError
DecisionAuthorityDeniedError = DecisionAuthorityMissingError


# ===========================================================================
# Framework 0.8.1 additions — the common legal-case substrate
#
# Architecture & Domain Framework 0.8.1 section 13.1 makes jurisdiction,
# parties/representation, filings, hearings, interim measures, decision
# effect/finality/enforceability, notice legal effect, recusal hooks and
# the DPIA gate part of PACK-09's acceptance criteria. Each condition
# below gets its own stable, machine-readable code (section 10), because a
# caller has to be able to tell "you have no jurisdiction" from "your
# mandate expired" from "the notice never took legal effect" without
# parsing prose.
# ===========================================================================


# --- Jurisdiction ----------------------------------------------------------


class JurisdictionMissingError(PermissionError):
    """The case carries no confirmed jurisdiction determination, so it
    cannot proceed to a substantive decision.

    Framework 0.8.1 hard invariant 52: no disciplinary sanction without
    jurisdiction, notice, response opportunity, human decision, reasons
    and remedy. Fail closed - an unknown jurisdiction is never treated as
    a permissive one."""

    reason_code = "JURISDICTION_MISSING"


class JurisdictionNotCompetentError(PermissionError):
    """The authority named in the request is not the competent authority
    recorded for this case kind in this scope.

    Framework hard invariant 15: a role name is not proof of authority."""

    reason_code = "JURISDICTION_NOT_COMPETENT"


class JurisdictionTransferRequiredError(PermissionError):
    """The matter belongs to a different competent authority; it must be
    transferred through the governed transfer path rather than decided
    here."""

    reason_code = "JURISDICTION_TRANSFER_REQUIRED"


class JurisdictionScopeMismatchError(PermissionError):
    """The jurisdiction determination's organizational scope does not
    match the case's."""

    reason_code = "JURISDICTION_SCOPE_MISMATCH"


# --- Parties and representation --------------------------------------------


class RepresentationInvalidError(PermissionError):
    """The representation mandate does not authorize this action - it
    covers a different case, a different party, or an action outside its
    declared authority scope.

    Framework 0.8.1: a representative receives only the powers the
    mandate grants; downstream never widens scope (hard invariant 14)."""

    reason_code = "REPRESENTATION_INVALID"


class RepresentationExpiredError(PermissionError):
    """The mandate's validity window has closed. Prior filings made while
    it was valid remain on the docket untouched."""

    reason_code = "REPRESENTATION_EXPIRED"


class RepresentationRevokedError(PermissionError):
    """The mandate was revoked or withdrawn. As with expiry, this blocks
    new actions only; it never erases what was already filed."""

    reason_code = "REPRESENTATION_REVOKED"


# --- Filings and docket ----------------------------------------------------


class FilingInadmissibleError(ValueError):
    """The filing was rejected at intake. The rejection is recorded on the
    docket as its own entry - an inadmissible filing is not deleted."""

    reason_code = "FILING_INADMISSIBLE"


class FilingSequenceConflictError(ValueError):
    """A docket write would break the append-only sequence: a duplicate
    sequence number, a non-contiguous jump, or an attempt to overwrite an
    existing entry.

    Framework 0.8.1 AGR-09: "immutable docket"."""

    reason_code = "FILING_SEQUENCE_CONFLICT"


# --- Hearings --------------------------------------------------------------


class HearingTransitionInvalidError(ValueError):
    """The requested hearing lifecycle transition is not permitted."""

    reason_code = "HEARING_TRANSITION_INVALID"


# --- Interim measures ------------------------------------------------------


class InterimMeasureAuthorityDeniedError(PermissionError):
    """The actor may not impose this interim measure.

    Two distinct refusals share this code because both are the same
    architectural fact - the actor lacks the authority: an ordinary case
    handler acting without the authority an interim measure requires, and
    an AI/automated actor attempting one at all (Framework hard invariant
    69: AI does not decide sanction, and hard invariant 5: AI takes no
    final consequential decision)."""

    reason_code = "INTERIM_MEASURE_AUTHORITY_DENIED"


# --- Decisions, effect, finality, enforceability, remedies ------------------


class DecisionNotEffectiveError(ValueError):
    """The decision has been issued but its effect has not commenced, or
    its effect is currently suspended.

    Framework 0.8.1 section 13.1 requires issuance, effect, finality and
    enforceability to be four separate states; collapsing them is the
    defect this code exists to surface."""

    reason_code = "DECISION_NOT_EFFECTIVE"


class DecisionNotFinalError(ValueError):
    """The decision is still open to a remedy, so it is not final."""

    reason_code = "DECISION_NOT_FINAL"


class DecisionNotEnforceableError(ValueError):
    """The decision is not enforceable: it is not yet effective, not yet
    final where finality is a precondition, or its enforceability has
    been stayed."""

    reason_code = "DECISION_NOT_ENFORCEABLE"


class RemedyUnavailableError(ValueError):
    """No remedy route is open for this decision - the remedy window has
    closed, the decision is already final and unappealable, or the
    requested remedy kind does not apply."""

    reason_code = "REMEDY_UNAVAILABLE"


class DueProcessPrerequisiteMissingError(PermissionError):
    """A sanction or a restriction of a fundamental right was attempted
    without one of its mandatory prerequisites.

    Framework 0.8.1 hard invariant 52 lists them exhaustively:
    jurisdiction, notice, opportunity to respond, human decision, reasons,
    remedy. The refusal names which one is missing; the code is the same
    for all six because the architectural fact is one - due process was
    not complete."""

    reason_code = "DUE_PROCESS_PREREQUISITE_MISSING"


# --- Recusal ---------------------------------------------------------------


class RecusalRequiredError(PermissionError):
    """A conflict assessment concluded that this actor must recuse
    themselves before acting further on this matter."""

    reason_code = "RECUSAL_REQUIRED"


class RecusedActorDeniedError(PermissionError):
    """A recused actor attempted an action their recusal blocks.

    Framework hard invariant 53: recusal immediately blocks decision
    capability without erasing history - the prior participation record
    stays."""

    reason_code = "RECUSED_ACTOR_DENIED"


# --- Official notice and legal effect --------------------------------------


class NoticeMethodInvalidError(ValueError):
    """The service method is not one this notice kind authorizes for this
    recipient.

    Framework hard invariant 40: legal notice requires an authorized
    object, a valid method, proof, and a governed effect decision."""

    reason_code = "NOTICE_METHOD_INVALID"


class ServiceNotProvenError(PermissionError):
    """Service of the notice is not proven: no attempt succeeded, or the
    attempts recorded do not meet the deemed-service rule invoked.

    Delivery and read telemetry are inputs to this determination, never
    substitutes for it (Framework hard invariant 39)."""

    reason_code = "SERVICE_NOT_PROVEN"


class NoticeEffectUndeterminedError(PermissionError):
    """The service state could not be established, so no legal effect can
    be determined. Fail closed - an unknown service state never becomes
    an effective notice."""

    reason_code = "NOTICE_EFFECT_UNDETERMINED"


class NoticeEffectAlreadyEstablishedError(ValueError):
    """A legal effect already exists for this notice, and a *different*
    one was requested. An identical replay is idempotent and never
    reaches this error."""

    reason_code = "NOTICE_EFFECT_ALREADY_ESTABLISHED"


class DuplicateLegalEffectPreventedError(ValueError):
    """A retry or replay would have produced a second consequential legal
    effect from one governed decision.

    Framework hard invariant 59: retry/replay does not repeat a
    consequential legal effect."""

    reason_code = "DUPLICATE_LEGAL_EFFECT_PREVENTED"


class DeadlineTriggerInvalidError(ValueError):
    """The supplied deadline trigger is not a governed trigger: it is
    delivery or read telemetry, an unknown source, or a notice effect
    belonging to another case or organization.

    Framework 0.8.1 section 13.1: only a `NoticeEffectDecision` (or
    another explicitly governed trigger) starts a procedural deadline."""

    reason_code = "DEADLINE_TRIGGER_INVALID"


# --- Data protection governance and the DPIA gate --------------------------


class DPIARequiredError(ValueError):
    """This processing activity's risk classification requires a data
    protection impact assessment, and none is recorded."""

    reason_code = "DPIA_REQUIRED"


class DPIANotApprovedError(PermissionError):
    """A DPIA exists but is not in an approved state - it is draft, under
    review, rejected, or expired."""

    reason_code = "DPIA_NOT_APPROVED"


class ProcessingActivationBlockedError(PermissionError):
    """Activation of the processing activity is blocked.

    The gate is deliberately separate from the DPIA's own status: an
    activity can have an approved DPIA and still be blocked for another
    recorded reason, and the caller needs to be able to tell which."""

    reason_code = "PROCESSING_ACTIVATION_BLOCKED"


class DPOIndependenceRequiredError(PermissionError):
    """The data protection officer reviewing or approving this processing
    is the same party as its operational process owner or controller.

    Framework 0.8.1 AGR-12 and the institutional role matrix: DPO
    independence is structural - the DPO must not self-approve
    operational processing."""

    reason_code = "DPO_INDEPENDENCE_REQUIRED"


# --- Legal Hold propagation and destruction --------------------------------


class LegalHoldPropagationUnresolvedError(PermissionError):
    """The hold's propagation to a known governed derivative - a replica,
    index, or export - is unconfirmed or failed.

    Framework section 11: a legal hold extends to relevant replicas,
    indexes and exports. An unresolved propagation state fails closed:
    the primary record cannot be destroyed while the system cannot show
    the hold reached everything it must."""

    reason_code = "LEGAL_HOLD_PROPAGATION_UNRESOLVED"


class DestructionBlockedByHoldError(PermissionError):
    """A destruction *command* was refused because a hold applies.

    Distinct from `RECORD_UNDER_LEGAL_HOLD`, which is the *eligibility
    verdict's* reason code: this one is the command-level denial, and it
    also covers the case where the hold applies to a known derivative
    rather than to the primary record."""

    reason_code = "DESTRUCTION_BLOCKED_BY_HOLD"

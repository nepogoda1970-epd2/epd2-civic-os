"""Privileged Access Service command layer (PACK-12).

Three logical bounded contexts - privileged administration,
authorization-aware search, and governed export with DLP and disclosure
control - share **one** package boundary and **one** command frame
(`OD-P12-04`). They are separated by module, by aggregate and by role,
not by process: a second deployable would have bought nothing here and
would have cost a second audit path, which is exactly what `OD-P12-06`
forbids.

Every state-changing command routes through one private frame, `_guard`,
and finishes through one private tail, `_finish`. A guard a command can
forget is a guard that is not in force, so no command assembles its own
sequence of checks.

`_guard` enforces, in this fixed order:

1. **Scope, before anything else.** `RequestContext.require_scope()`
   refuses an undeterminable scope before any other check, any read and
   any write; the target record's scope is then re-asserted against it,
   so a command holding a record obtained by some other route still
   cannot act across a boundary (`P12-ORG-003`, FIR-INV-013).
2. **Authority.** `roles.assert_authorized` resolves the *presented
   authority object* through `AuthorizationPort` to an active,
   effective-dated, scope-matching assignment. A `role_code` string is
   never proof (`P12-ROLE-017`), and a command absent from
   `ACTION_REQUIREMENTS` denies rather than defaulting open.
3. **Role incompatibility and institutional escalation.** The matrix is
   re-checked at the moment of the act against the roles the actor
   really holds, and no operational assignment may widen an institutional
   office (`P12-ROLE-019`).
4. **Self-approval and separation of duties.** Every prior actor the
   command names is compared with the acting one
   (`P12-PAM-004`, `P12-BG-003`, `P12-EXP-006`, `P12-SDC-006`).
5. **Purpose.** Where the caller declares a purpose, it must be one the
   resolved role may serve (`required_roles_for_purpose`).
6. **Idempotency.** The caller supplies `RequestContext.event_id`. The
   same `event_id` with the same request digest returns the recorded
   aggregate without re-attempting the transition; the same `event_id`
   with different content raises.
7. **Optimistic concurrency.** Mutating commands take an optional
   `expected_*_version`; a mismatch raises. Deliberately after
   idempotency: a true replay must not fail on a version the first
   execution already advanced past.

`_finish` then appends to Audit Core, publishes the canonical envelope,
and only then records the idempotency row. **Audit before event**: an
event that escaped without an audit row is an unaccountable act, and the
reverse ordering is the one that produces it.

## One command, several catalog events

A few governed operations are single atomic acts that the Event Catalog
names with more than one event - a search that is submitted, authorized,
executed and partly suppressed is one act, not four. `_finish` therefore
takes an ordered sequence of `_Emission`s. The **first** carries the
command's own `event_id` and is the idempotency anchor; the rest carry
deterministic `uuid5` identifiers derived from it and the event type, so
a replay produces byte-identical audit rows that `append_audit_event`
recognises as its own rather than duplicating. Every emission gets its
own audit row: a governed fact worth an event is a governed fact worth
accounting for.

## No bypass

`roles.NO_BYPASS_NOTE` states the rule this module lives under, and there
is no code path that contradicts it. No parameter, environment variable,
policy field or privileged grant relaxes any check here. Emergency access
is a *separate*, dual-controlled, notified, expiring, independently
reviewed workflow (`break_glass.py`) that adds its own record - never a
softening of this one (`P12-BG-009`, FIR-INV-006).

## What this module deliberately does not do

No production database, no real event bus, no external IAM or IdP, no
MFA, no HSM or PKI, no production search engine, no production DLP
provider, no voting, no incident-response platform and no external
recipient portal. It mints no identity and no institutional office. It
holds **no** mutating control over `audit-core`: it appends and it reads,
and `AuditMutationProhibitedError` exists because "we simply never call
it" is not a control (`OD-P12-06`). Retention and legal hold remain
PACK-09's; session evidence sealing reuses PACK-11's bundles. No command
reads system time: a `Clock` is injected into every one of them.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from epd2_audit_core.application import AppendAuditEventRequest, append_audit_event
from epd2_audit_core.domain import AuditEvent
from epd2_core.canonical_json import canonical_dumps
from epd2_core.clock import Clock
from epd2_core.event_envelope import ActorRef, EventEnvelope
from epd2_privileged_access_service import events as privileged_events
from epd2_privileged_access_service.access import (
    GrantState,
    PrivilegedAccessGrant,
    PrivilegedAccessRequest,
    PrivilegedAccessReview,
    ResourceScope,
    SeparationOfDutiesEvaluation,
    assert_approver_set_sufficient,
)
from epd2_privileged_access_service.breakglass import (
    BreakGlassActivation,
    BreakGlassIndependentReview,
    BreakGlassState,
    EmergencyCondition,
    NotificationOutcome,
    assert_notification_not_suppressed,
    assert_renewal_is_new_decision,
)
from epd2_privileged_access_service.classification import ClassificationDecision
from epd2_privileged_access_service.disclosure import (
    CohortObservation,
    CohortPolicy,
    DisclosureExceptionDecision,
    DisclosureExceptionRequest,
    DisclosureRiskAssessment,
    DisclosureRule,
    ReleaseHistoryEntry,
    SuppressionDecision,
    assert_release_permitted,
    assert_suppression_applied,
    evaluate_cohort_threshold,
    evaluate_complement_protection,
    evaluate_cumulative,
    evaluate_differencing,
)
from epd2_privileged_access_service.dlp import (
    DlpAssessment,
    DlpControl,
    DlpOutcome,
    DlpPolicyProfile,
    apply_transforms,
    assert_assessor_is_not_approver,
    assert_no_repeated_extraction_pattern,
    assert_volume_within_limits,
    frequency_window_start,
)
from epd2_privileged_access_service.domain import (
    AuthorityReference,
    EffectiveWindow,
    OrganizationalScopeRef,
    Purpose,
    PurposeBinding,
    ReasonCoded,
    RequestContext,
    RiskClass,
    deterministic_digest,
)
from epd2_privileged_access_service.exceptions import (
    BreakGlassNotificationUndeliveredError,
    DisclosureAssessmentMissingError,
    DlpAssessmentMissingError,
    ExportApprovalMissingError,
    ExportManifestMissingError,
    IdempotencyConflictError,
    OptimisticConcurrencyConflictError,
    PrivilegeAuthorityMissingError,
    PrivilegePurposeMismatchError,
    RecordNotFoundError,
    SessionEvidenceIncompleteError,
    UnknownStatusError,
)
from epd2_privileged_access_service.export import (
    DatasetManifest,
    ExportAccessEvent,
    ExportArtifact,
    ExportDestructionAttestation,
    ExportRequest,
    ExportState,
    assert_certified_result_not_exported,
    assert_cross_scope_basis,
    assert_export_authority,
    assert_hold_is_not_authorization,
    assert_recipient_eligible,
    assert_source_records_current,
    build_artifact,
    permitted_field_set,
)
from epd2_privileged_access_service.policy import PrivilegedAccessPolicy
from epd2_privileged_access_service.roles import (
    AuthorizationPort,
    InstitutionalRole,
    OperationalAssignmentRole,
    assert_authorized,
    assert_distinct_reviewer,
    assert_no_institutional_escalation,
    assert_not_self_approval,
    assert_roles_compatible,
    required_roles_for_purpose,
)
from epd2_privileged_access_service.search import (
    IndexPolicy,
    IndexRemovalEvidence,
    QueryDecision,
    QueryRequest,
    SearchCacheKey,
    SourceAuthorizationPort,
    assert_cache_context_matches,
    assert_query_admissible,
    execute_query,
)
from epd2_privileged_access_service.sessions import (
    OperationSummary,
    PrivilegedSession,
    SealedPrivilegedSession,
    SessionState,
)
from epd2_privileged_access_service.storage import (
    IdempotencyRecord,
    PrivilegedStores,
    QueryAudit,
)

_SOURCE_SERVICE = "privileged-access-service"

#: The policy version recorded on every audit row this service writes.
#: Distinct from `PrivilegedAccessPolicy.policy_version`, which versions
#: the *numeric* policy: this one versions the command layer's own
#: governance rules, so a numeric change does not masquerade as a rule
#: change or the reverse (`OD-P12-03`).
AUDIT_POLICY_VERSION = "pack-12/v1"

_EMISSION_NAMESPACE = uuid5(NAMESPACE_URL, "https://epd2.invalid/pack-12/emission")


# ---------------------------------------------------------------------------
# Reason codes for successfully-audited acts
# ---------------------------------------------------------------------------
#
# The PACK-12 catalog, like canon section 24, registers refusals. An audit
# row for an act that *succeeded* still needs a registered classification,
# and inventing free text at the call site is exactly what `P12-RSN-002`
# forbids. These are declared once, here, and registered in
# `contracts/reason-codes/pack-12.yml` with the same seven mandatory
# fields as every other code.

RC_ACCESS_REQUESTED = "PRIVILEGE_ACCESS_REQUEST_RECORDED"
RC_ACCESS_APPROVED = "PRIVILEGE_ACCESS_APPROVAL_RECORDED"
RC_ACCESS_DENIED = "PRIVILEGE_ACCESS_DENIAL_RECORDED"
RC_ACCESS_ACTIVATED = "PRIVILEGE_ACCESS_ACTIVATION_RECORDED"
RC_ACCESS_EXPIRED = "PRIVILEGE_ACCESS_EXPIRY_RECORDED"
RC_ACCESS_REVOKED = "PRIVILEGE_ACCESS_REVOCATION_RECORDED"
RC_REVIEW_REQUESTED = "PRIVILEGE_ACCESS_REVIEW_REQUEST_RECORDED"
RC_REVIEW_COMPLETED = "PRIVILEGE_ACCESS_REVIEW_RECORDED"
RC_SESSION_STARTED = "PRIVILEGE_SESSION_START_RECORDED"
RC_SESSION_ENDED = "PRIVILEGE_SESSION_END_RECORDED"
RC_SESSION_SEALED = "PRIVILEGE_SESSION_EVIDENCE_SEALED_RECORDED"
RC_BREAK_GLASS_REQUESTED = "PRIVILEGE_BREAK_GLASS_REQUEST_RECORDED"
RC_BREAK_GLASS_APPROVED = "PRIVILEGE_BREAK_GLASS_APPROVAL_RECORDED"
RC_BREAK_GLASS_ACTIVATED = "PRIVILEGE_BREAK_GLASS_ACTIVATION_RECORDED"
RC_BREAK_GLASS_NOTIFIED = "PRIVILEGE_BREAK_GLASS_NOTIFICATION_RECORDED"
RC_BREAK_GLASS_EXPIRED = "PRIVILEGE_BREAK_GLASS_EXPIRY_RECORDED"
RC_BREAK_GLASS_REVOKED = "PRIVILEGE_BREAK_GLASS_REVOCATION_RECORDED"
RC_BREAK_GLASS_REVIEWED = "PRIVILEGE_BREAK_GLASS_REVIEW_RECORDED"
RC_QUERY_SUBMITTED = "SEARCH_QUERY_SUBMISSION_RECORDED"
RC_QUERY_AUTHORIZED = "SEARCH_QUERY_AUTHORIZATION_RECORDED"
RC_QUERY_EXECUTED = "SEARCH_QUERY_EXECUTION_RECORDED"
RC_QUERY_DENIED = "SEARCH_QUERY_DENIAL_RECORDED"
RC_RESULT_SUPPRESSED = "SEARCH_RESULT_SUPPRESSED"
RC_INDEX_POLICY_CHANGED = "SEARCH_INDEX_POLICY_CHANGE_RECORDED"
RC_REINDEX_REQUESTED = "SEARCH_INDEX_REINDEX_REQUEST_RECORDED"
RC_INDEX_REMOVAL = "SEARCH_INDEX_REMOVAL_RECORDED"
RC_EXPORT_REQUESTED = "EXPORT_REQUEST_RECORDED"
RC_EXPORT_DLP_ASSESSED = "EXPORT_DLP_ASSESSMENT_RECORDED"
RC_EXPORT_DISCLOSURE_ASSESSED = "EXPORT_DISCLOSURE_ASSESSMENT_RECORDED"
RC_EXPORT_APPROVED = "EXPORT_APPROVAL_RECORDED"
RC_EXPORT_DENIED = "EXPORT_DENIAL_RECORDED"
RC_ARTIFACT_GENERATED = "EXPORT_ARTIFACT_GENERATION_RECORDED"
RC_ARTIFACT_DELIVERED = "EXPORT_ARTIFACT_DELIVERY_RECORDED"
RC_ARTIFACT_ACCESSED = "EXPORT_ARTIFACT_ACCESS_RECORDED"
RC_ARTIFACT_EXPIRED = "EXPORT_ARTIFACT_EXPIRY_RECORDED"
RC_EXPORT_REVOKED = "EXPORT_REVOCATION_RECORDED"
RC_DESTRUCTION_ATTESTED = "EXPORT_DESTRUCTION_ATTESTATION_RECORDED"
RC_DISCLOSURE_ASSESSED = "DISCLOSURE_RISK_ASSESSMENT_RECORDED"
RC_DISCLOSURE_SUPPRESSED = "DISCLOSURE_SUPPRESSION_RECORDED"
RC_DISCLOSURE_EXCEPTION_REQUESTED = "DISCLOSURE_EXCEPTION_REQUEST_RECORDED"
RC_DISCLOSURE_EXCEPTION_DECIDED = "DISCLOSURE_EXCEPTION_DECISION_RECORDED"
RC_DISCLOSURE_CUMULATIVE_FLAGGED = "DISCLOSURE_CUMULATIVE_RISK_RECORDED"
RC_PUBLICATION_OBSERVED = "DISCLOSURE_GOVERNED_PUBLICATION_OBSERVED"


# ---------------------------------------------------------------------------
# Which authority each command requires
# ---------------------------------------------------------------------------
#
# A command absent from this table cannot be authorized: `assert_authorized`
# refuses an empty requirement set with `PRIVILEGE_AUTHORITY_MISSING`
# rather than falling through. Adding a command therefore *forces* an
# explicit authority decision - the failure mode of forgetting is denial,
# not silent permission (`P12-ROLE-020`).

_SEC = InstitutionalRole.SECURITY_ADMINISTRATOR.value
_SYS = InstitutionalRole.SYSTEM_ADMINISTRATOR.value
_IAM = OperationalAssignmentRole.IAM_ADMINISTRATOR.value
_AUDIT = OperationalAssignmentRole.AUDIT_CUSTODIAN.value
_DOMAIN = OperationalAssignmentRole.DOMAIN_ADMINISTRATOR.value
_OWNER = OperationalAssignmentRole.DATA_OWNER.value
_EXPORTER = OperationalAssignmentRole.EXPORT_APPROVER.value
_DLP = OperationalAssignmentRole.DLP_SECURITY_OFFICER.value
_REVIEWER = OperationalAssignmentRole.INDEPENDENT_PRIVILEGED_ACCESS_REVIEWER.value
_BREAK_GLASS = OperationalAssignmentRole.BREAK_GLASS_APPROVER.value
_DISCLOSURE = OperationalAssignmentRole.DISCLOSURE_CONTROL_REVIEWER.value

ACTION_REQUIREMENTS: dict[str, frozenset[str]] = {
    # Privileged administration
    "request_privileged_access": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT}),
    "approve_privileged_access": frozenset({_SEC}),
    "deny_privileged_access": frozenset({_SEC}),
    "activate_privileged_access": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT}),
    "expire_privileged_access": frozenset({_SEC, _REVIEWER}),
    "revoke_privileged_access": frozenset({_SEC, _REVIEWER}),
    "request_access_review": frozenset({_SEC, _REVIEWER}),
    "complete_access_review": frozenset({_REVIEWER}),
    # Sessions
    "start_privileged_session": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT}),
    "record_session_operation": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT}),
    "end_privileged_session": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT}),
    "seal_privileged_session": frozenset({_AUDIT}),
    # Break-glass
    "request_break_glass": frozenset({_SYS, _DOMAIN, _SEC}),
    "approve_break_glass": frozenset({_BREAK_GLASS}),
    "activate_break_glass": frozenset({_SYS, _DOMAIN, _SEC}),
    "expire_break_glass": frozenset({_SEC, _BREAK_GLASS}),
    "revoke_break_glass": frozenset({_SEC, _BREAK_GLASS}),
    "complete_break_glass_review": frozenset({_REVIEWER}),
    # Search
    "submit_search_query": frozenset({_IAM, _DOMAIN, _SEC, _SYS, _OWNER, _AUDIT, _REVIEWER}),
    "change_index_policy": frozenset({_SEC}),
    "request_reindex": frozenset({_SEC, _DOMAIN}),
    "evidence_index_removal": frozenset({_DOMAIN, _OWNER}),
    # Export
    "request_data_export": frozenset({_DOMAIN, _OWNER, _AUDIT, _REVIEWER}),
    "record_dlp_assessment": frozenset({_DLP}),
    "record_disclosure_assessment": frozenset({_DISCLOSURE}),
    "approve_data_export": frozenset({_EXPORTER}),
    "deny_data_export": frozenset({_EXPORTER}),
    "generate_export_artifact": frozenset({_OWNER, _DOMAIN}),
    "deliver_export_artifact": frozenset({_OWNER, _DOMAIN}),
    "access_export_artifact": frozenset({_OWNER, _DOMAIN, _AUDIT, _REVIEWER}),
    "expire_export_artifact": frozenset({_OWNER, _DOMAIN, _SEC}),
    "revoke_data_export": frozenset({_OWNER, _SEC, _EXPORTER}),
    "attest_export_destruction": frozenset({_OWNER, _EXPORTER}),
    # Disclosure control
    "assess_disclosure_risk": frozenset({_DISCLOSURE}),
    "request_disclosure_exception": frozenset({_OWNER, _DOMAIN}),
    "decide_disclosure_exception": frozenset({_DISCLOSURE}),
    "observe_governed_publication": frozenset({_DISCLOSURE, _AUDIT}),
}


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GrantResult:
    grant: PrivilegedAccessGrant
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AccessRequestResult:
    request: PrivilegedAccessRequest
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AccessReviewResult:
    review: PrivilegedAccessReview
    grant: PrivilegedAccessGrant
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SessionResult:
    session: PrivilegedSession
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SealedSessionResult:
    sealed: SealedPrivilegedSession
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class BreakGlassResult:
    activation: BreakGlassActivation
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class BreakGlassReviewResult:
    review: BreakGlassIndependentReview
    activation: BreakGlassActivation
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class SearchResult:
    decision: QueryDecision
    query_audit: QueryAudit
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class IndexPolicyResult:
    policy: IndexPolicy
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class IndexRemovalResult:
    evidence: IndexRemovalEvidence
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ExportRequestResult:
    request: ExportRequest
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DlpAssessmentResult:
    assessment: DlpAssessment
    request: ExportRequest
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DisclosureAssessmentResult:
    assessment: DisclosureRiskAssessment
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class ArtifactResult:
    artifact: ExportArtifact
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class AttestationResult:
    attestation: ExportDestructionAttestation
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class DisclosureExceptionResult:
    request: DisclosureExceptionRequest
    decision: DisclosureExceptionDecision | None
    event: EventEnvelope
    audit_event: AuditEvent


@dataclass(frozen=True, slots=True)
class PublicationObservationResult:
    publication_reference: str
    event: EventEnvelope
    audit_event: AuditEvent


# ---------------------------------------------------------------------------
# Private frame
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


@dataclass(frozen=True, slots=True)
class _Emission:
    """One catalog event plus the audit row that accounts for it."""

    event: EventEnvelope
    target_type: str
    target_id: UUID
    reason_code: str
    before_hash: str = ""
    after_hash: str = ""


def _actor_for(authority: AuthorityReference) -> ActorRef:
    """The envelope actor.

    Derived from the *authority*, never from a person: `actor_id` is the
    authority assignment's own id, so the trail records which office
    acted. Which human exercised the office is deliberately not knowable
    from here (FIR-INV-001)."""
    return ActorRef(actor_id=authority.authority_id, actor_type="organizational_authority")


def _as_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None


def _correlation_uuid(context: RequestContext, *, fallback: UUID) -> UUID:
    return _as_uuid(context.correlation_id) or fallback


def _emission_audit_id(event_id: UUID, event_type: str, ordinal: int) -> UUID:
    """The audit id for a non-primary emission.

    Deterministic in the command's own `event_id`, the event type and the
    position, so a replay of the same command produces the same ids and
    `append_audit_event` recognises identical rows instead of appending
    duplicates."""
    return uuid5(_EMISSION_NAMESPACE, f"{event_id}:{ordinal}:{event_type}")


def _state_hash(payload: Mapping[str, object]) -> str:
    """The canonical hash of a state snapshot, for audit before/after.

    Uses `epd2_core.canonical_json` so two independently-constructed
    representations of the same logical state hash identically - the same
    guarantee `sessions.compute_session_hash` and `audit-core` rely on."""
    return hashlib.sha256(canonical_dumps(dict(payload)).encode("utf-8")).hexdigest()


def _guard(
    stores: PrivilegedStores,
    *,
    command: str,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    request_parts: Sequence[str],
    target_scope: OrganizationalScopeRef | None = None,
    prior_actor_references: Sequence[str] = (),
    declared_purpose: Purpose | None = None,
    current_version: int | None = None,
    expected_version: int | None = None,
    version_label: str = "record",
    allow_audited_replay: bool = False,
) -> _CommandGuard:
    """The one frame every state-changing command routes through.

    The order of the seven checks is the guarantee, not an implementation
    detail. Nothing here is conditional on a flag, an environment or a
    privileged grant: FIR-INV-006 forbids it and `roles.NO_BYPASS_NOTE`
    states why in full."""
    scope = context.require_scope()
    if target_scope is not None:
        target_scope.assert_matches(scope)

    now = clock.now()
    required = ACTION_REQUIREMENTS.get(command, frozenset())
    if not required:
        raise PrivilegeAuthorityMissingError(
            f"command {command!r} declares no authority requirement - default deny"
        )
    authority = assert_authorized(required, context.authorities, scope, at=now, port=port)

    acting_actor = authority.actor_reference.strip()
    if acting_actor:
        held = {*port.held_roles(acting_actor, scope), authority.role_code}
        assert_roles_compatible(held)
        assert_no_institutional_escalation(held)
    for prior in prior_actor_references:
        assert_not_self_approval(authority.actor_reference, prior, action=command)

    if declared_purpose is not None:
        admitted = required_roles_for_purpose(declared_purpose)
        if authority.role_code not in admitted:
            raise PrivilegePurposeMismatchError(
                f"role {authority.role_code!r} may not act for purpose {declared_purpose!s}"
            )

    event_id = context.event_id
    if event_id is None:
        raise IdempotencyConflictError(
            f"{command} requires a caller-supplied event_id on the request context"
        )
    digest = deterministic_digest(command, *request_parts)
    recorded = stores.idempotency.get(event_id)
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
    # The second line of defence. An audit row under this event_id with no
    # command record means a previous run appended its audit entry and died
    # before persisting the command record; re-running the transition now
    # would mutate the aggregate a second time under one audit row.
    #
    # `allow_audited_replay` is set only by commands whose refusal path
    # writes audit rows but changes no aggregate - a denied query is the
    # case. Re-evaluating one is deterministic, and `append_audit_event`
    # deduplicates the identical row, so refusing the replay would turn a
    # correctly-recorded denial into a confusing conflict.
    if not allow_audited_replay and stores.audit.get_by_event_id(event_id) is not None:
        raise IdempotencyConflictError(
            f"event_id {event_id} already has an audit entry but no recorded command result; "
            "the previous execution did not complete and is not safely replayable"
        )

    if (
        current_version is not None
        and expected_version is not None
        and current_version != expected_version
    ):
        raise OptimisticConcurrencyConflictError(
            f"{version_label} version is {current_version}, caller expected {expected_version}"
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
        replay=None,
    )


def _finish(
    stores: PrivilegedStores,
    guard: _CommandGuard,
    emissions: Sequence[_Emission],
    *,
    aggregate_id: UUID,
    clock: Clock,
) -> AuditEvent:
    """Append the audit rows, publish the envelopes, record the command.

    The order is the point. **Audit first**: an event that reached the
    stream without an audit row is an act nobody can account for.
    **Idempotency last**: the command record claims "this ran and
    produced that", and it must not be able to claim it before every
    durable effect exists.

    Returns the audit row of the *last* emission - the one that carries
    the command's outcome. The *first* emission carries the command's own
    `event_id` and is what `_guard`'s second line of defence looks for."""
    if not emissions:  # pragma: no cover - a command with no event is a bug
        raise SessionEvidenceIncompleteError(
            f"{guard.command} produced no event; a governed act without an event is unaccountable"
        )
    audit_event: AuditEvent | None = None
    for ordinal, emission in enumerate(emissions):
        audit_id = (
            guard.event_id
            if ordinal == 0
            else _emission_audit_id(guard.event_id, emission.event.event_type, ordinal)
        )
        audit_event = append_audit_event(
            stores.audit,
            AppendAuditEventRequest(
                audit_event_id=audit_id,
                event_type=emission.event.event_type,
                occurred_at=guard.now,
                actor_id=guard.actor.actor_id,
                actor_type=guard.actor.actor_type,
                target_type=emission.target_type,
                target_id=emission.target_id,
                action=guard.command,
                reason_code=emission.reason_code,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=guard.correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=emission.before_hash,
                after_hash=emission.after_hash,
            ),
            clock=clock,
        )
        stores.sink.publish(emission.event)
    stores.idempotency.put(
        IdempotencyRecord(
            event_id=guard.event_id,
            command=guard.command,
            request_digest=guard.request_digest,
            aggregate_id=aggregate_id,
            recorded_at=guard.now,
        )
    )
    assert audit_event is not None
    return audit_event


def _replayed_audit(stores: PrivilegedStores, guard: _CommandGuard) -> AuditEvent:
    audit_event = stores.audit.get_by_event_id(guard.event_id)
    if audit_event is None:  # pragma: no cover - unreachable through _finish
        raise IdempotencyConflictError(
            f"event_id {guard.event_id} has a recorded command result but no audit entry"
        )
    return audit_event


def _event(
    guard: _CommandGuard,
    *,
    event_type: str,
    aggregate_id: UUID,
    payload: Mapping[str, object],
) -> EventEnvelope:
    return privileged_events.build_privileged_event(
        event_id=guard.event_id,
        event_type=event_type,
        occurred_at=guard.now,
        actor=guard.actor,
        aggregate_id=aggregate_id,
        scope=guard.scope,
        payload=payload,
        correlation_id=guard.correlation_id,
        causation_id=guard.causation_id,
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
#
# A record in a foreign scope reports the *same* not-found error as one
# that does not exist (`P12-ORG-005`). Distinguishing them would let a
# caller confirm the existence of another organization's grants, sessions
# or exports by probing identifiers.


def _raise_not_found(what: str, identifier: UUID) -> None:
    raise RecordNotFoundError(f"no {what} with id {identifier}")


def guard_placeholder_id(name: str) -> UUID:
    """A stable identifier for a not-found report about a named, not
    UUID-keyed record. Exists so `_raise_not_found` keeps one message
    shape for every kind of record."""
    return uuid5(_EMISSION_NAMESPACE, f"named-record:{name}")


def _load_grant(
    stores: PrivilegedStores, grant_id: UUID, scope: OrganizationalScopeRef
) -> PrivilegedAccessGrant:
    grant = stores.grants.get(grant_id)
    if grant is None or grant.organization_scope.organization_id != scope.organization_id:
        _raise_not_found("privileged access grant", grant_id)
        raise AssertionError  # pragma: no cover - _raise_not_found always raises
    return grant


def _load_activation(
    stores: PrivilegedStores, activation_id: UUID, scope: OrganizationalScopeRef
) -> BreakGlassActivation:
    activation = stores.break_glass.get(activation_id)
    if activation is None or activation.organization_scope.organization_id != scope.organization_id:
        _raise_not_found("break-glass activation", activation_id)
        raise AssertionError  # pragma: no cover
    return activation


def _load_session(
    stores: PrivilegedStores, session_id: UUID, scope: OrganizationalScopeRef
) -> PrivilegedSession:
    session = stores.sessions.get(session_id)
    if session is None or session.organization_scope.organization_id != scope.organization_id:
        _raise_not_found("privileged session", session_id)
        raise AssertionError  # pragma: no cover
    return session


def _load_export(
    stores: PrivilegedStores, export_id: UUID, scope: OrganizationalScopeRef
) -> ExportRequest:
    request = stores.exports.get(export_id)
    if request is None or request.scope.organization_scope.organization_id != scope.organization_id:
        _raise_not_found("export request", export_id)
        raise AssertionError  # pragma: no cover
    return request


def _load_artifact(
    stores: PrivilegedStores, artifact_id: UUID, scope: OrganizationalScopeRef
) -> tuple[ExportArtifact, ExportRequest]:
    artifact = stores.artifacts.get(artifact_id)
    if artifact is None:
        _raise_not_found("export artifact", artifact_id)
        raise AssertionError  # pragma: no cover
    request = _load_export(stores, artifact.export_id, scope)
    return artifact, request


# ---------------------------------------------------------------------------
# Commands: privileged access lifecycle
# ---------------------------------------------------------------------------


def request_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    request_id: UUID,
    subject_reference: str,
    requested_role: OperationalAssignmentRole,
    resource_scope: ResourceScope,
    requested_operations: frozenset[str],
    purpose: PurposeBinding,
    requested_window: EffectiveWindow,
    risk_class: RiskClass,
    data_classes: frozenset[str],
) -> AccessRequestResult:
    """Record a request for privileged access (`P12-PAM-001`).

    The request is not access. It carries the nine mandatory attributes,
    and the ceiling on its window is checked here rather than at
    activation so an inadmissible request is refused while it is still
    only a request."""
    guard = _guard(
        stores,
        command="request_privileged_access",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(request_id),
            subject_reference,
            str(requested_role),
            str(risk_class),
        ),
    )
    if guard.replay is not None:
        replayed = stores.requests.get(guard.replay.aggregate_id)
        if replayed is None:  # pragma: no cover - defensive
            _raise_not_found("privileged access request", guard.replay.aggregate_id)
            raise AssertionError  # pragma: no cover
        return AccessRequestResult(
            request=replayed,
            event=_rebuilt_request_event(replayed, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    policy.assert_grant_duration_allowed(requested_window.duration)
    request = PrivilegedAccessRequest(
        request_id=request_id,
        subject_reference=subject_reference,
        requested_role=requested_role,
        organization_scope=guard.scope,
        resource_scope=resource_scope,
        requested_operations=requested_operations,
        purpose=purpose,
        requested_window=requested_window,
        risk_class=risk_class,
        data_classes=data_classes,
        requested_at=guard.now,
    )
    stores.requests.save(request)

    event = _event(
        guard,
        event_type="privileged_access.requested",
        aggregate_id=request_id,
        payload=privileged_events.access_requested_payload(
            request_id=request_id,
            role=str(requested_role),
            operations=requested_operations,
            risk_class=str(risk_class),
            data_classes=data_classes,
            purpose=str(purpose.purpose),
            valid_from=requested_window.valid_from.isoformat(),
            valid_until=requested_window.valid_until.isoformat(),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_request",
                target_id=request_id,
                reason_code=RC_ACCESS_REQUESTED,
                after_hash=_state_hash(request.to_state_payload()),
            ),
        ),
        aggregate_id=request_id,
        clock=clock,
    )
    return AccessRequestResult(request=request, event=event, audit_event=audit_event)


def _rebuilt_request_event(request: PrivilegedAccessRequest, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="privileged_access.requested",
        aggregate_id=request.request_id,
        payload=privileged_events.access_requested_payload(
            request_id=request.request_id,
            role=str(request.requested_role),
            operations=request.requested_operations,
            risk_class=str(request.risk_class),
            data_classes=request.data_classes,
            purpose=str(request.purpose.purpose),
            valid_from=request.requested_window.valid_from.isoformat(),
            valid_until=request.requested_window.valid_until.isoformat(),
        ),
    )


def approve_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    request_id: UUID,
    grant_id: UUID,
    approvers: tuple[str, ...],
    reason: ReasonCoded,
    granted_window: EffectiveWindow | None = None,
) -> GrantResult:
    """Approve a request and mint the grant it authorises.

    Three separations are enforced together, because each alone is
    defeatable: the approver set excludes the requester
    (`assert_approver_set_sufficient`), the *acting* approver is not the
    requester (`prior_actor_references`), and the roles the approver
    actually holds are re-checked against the incompatibility matrix
    inside `_guard`."""
    request = stores.requests.get(request_id)
    if request is None:
        _raise_not_found("privileged access request", request_id)
        raise AssertionError  # pragma: no cover

    guard = _guard(
        stores,
        command="approve_privileged_access",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(request_id), str(grant_id), *sorted(approvers)),
        target_scope=request.organization_scope,
        prior_actor_references=(request.subject_reference,),
    )
    if guard.replay is not None:
        return _replayed_grant(stores, guard, "privileged_access.approved")

    assert_approver_set_sufficient(
        approvers,
        requester_reference=request.subject_reference,
        risk_class=request.risk_class,
        policy=policy,
    )
    window = granted_window or request.requested_window
    policy.assert_grant_duration_allowed(window.duration)

    grant = PrivilegedAccessGrant(
        grant_id=grant_id,
        request_id=request_id,
        subject_reference=request.subject_reference,
        role=request.requested_role,
        organization_scope=request.organization_scope,
        resource_scope=request.resource_scope,
        permitted_operations=request.requested_operations,
        purpose=request.purpose,
        window=window,
        risk_class=request.risk_class,
        policy_version=policy.policy_version,
        approvers=approvers,
    )
    before_hash = _state_hash(grant.to_state_payload())
    evaluation = SeparationOfDutiesEvaluation(
        evaluation_id=uuid5(_EMISSION_NAMESPACE, f"sod-approval:{grant_id}"),
        evaluated_at=guard.now,
        subject_reference=request.subject_reference,
        held_roles=port.held_roles(request.subject_reference, guard.scope),
        outcome="passed",
        stage="approval",
    )
    grant = grant.with_evaluation(evaluation)
    grant = grant.with_state(
        GrantState.UNDER_EVALUATION,
        at=guard.now,
        action="evaluate_privileged_access",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    ).with_state(
        GrantState.APPROVED,
        at=guard.now,
        action="approve_privileged_access",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type="privileged_access.approved",
        aggregate_id=grant_id,
        payload=privileged_events.access_decision_payload(
            grant_id=grant_id,
            approver_references=approvers,
            reason_code=reason.reason_code,
            policy_version=policy.policy_version,
            evaluation_reference=str(evaluation.evaluation_id),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=RC_ACCESS_APPROVED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return GrantResult(grant=grant, event=event, audit_event=audit_event)


def deny_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    request_id: UUID,
    grant_id: UUID,
    reason: ReasonCoded,
) -> GrantResult:
    """Deny a request, and record the denial as a governed act.

    A denial creates the grant aggregate in `DENIED` so the refusal has a
    durable, reviewable subject. A request that was refused with no
    record is a request nobody can show was considered."""
    request = stores.requests.get(request_id)
    if request is None:
        _raise_not_found("privileged access request", request_id)
        raise AssertionError  # pragma: no cover

    guard = _guard(
        stores,
        command="deny_privileged_access",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(request_id), str(grant_id), reason.reason_code),
        target_scope=request.organization_scope,
        prior_actor_references=(request.subject_reference,),
    )
    if guard.replay is not None:
        return _replayed_grant(stores, guard, "privileged_access.denied")

    grant = PrivilegedAccessGrant(
        grant_id=grant_id,
        request_id=request_id,
        subject_reference=request.subject_reference,
        role=request.requested_role,
        organization_scope=request.organization_scope,
        resource_scope=request.resource_scope,
        permitted_operations=request.requested_operations,
        purpose=request.purpose,
        window=request.requested_window,
        risk_class=request.risk_class,
        policy_version=policy.policy_version,
        approvers=(),
    )
    before_hash = _state_hash(grant.to_state_payload())
    grant = grant.with_state(
        GrantState.UNDER_EVALUATION,
        at=guard.now,
        action="evaluate_privileged_access",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    ).with_state(
        GrantState.DENIED,
        at=guard.now,
        action="deny_privileged_access",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type="privileged_access.denied",
        aggregate_id=grant_id,
        payload=privileged_events.access_decision_payload(
            grant_id=grant_id,
            approver_references=(),
            reason_code=reason.reason_code,
            policy_version=policy.policy_version,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=RC_ACCESS_DENIED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return GrantResult(grant=grant, event=event, audit_event=audit_event)


def activate_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    grant_id: UUID,
    requested_operation: str,
    requested_domain: str,
    requested_purpose: Purpose,
    reason: ReasonCoded,
    expected_history_length: int | None = None,
) -> GrantResult:
    """Activate an approved grant.

    Activation re-checks **everything**, and that is the whole point of
    the command existing separately from approval (`P12-PAM-006`):
    separation of duties, effective authority, organization scope,
    purpose, requested operation, validity period, revocation state, and
    the policy version the grant was approved under. Time passes between
    approval and activation, and every one of these can have changed in
    it."""
    grant = _load_grant(stores, grant_id, context.require_scope())
    guard = _guard(
        stores,
        command="activate_privileged_access",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(grant_id), requested_operation, requested_domain),
        target_scope=grant.organization_scope,
        prior_actor_references=grant.approvers,
        current_version=len(grant.history),
        expected_version=expected_history_length,
        version_label="grant history",
    )
    if guard.replay is not None:
        return _replayed_grant(stores, guard, "privileged_access.activated")

    # Re-check, at the moment of activation, every dimension approval
    # established. The order below is deliberate: revocation and expiry
    # before scope, because a revoked grant must report revocation.
    if grant.state is GrantState.REVOKED:
        grant.assert_usable(
            at=guard.now,
            policy=policy,
            operation=requested_operation,
            domain=requested_domain,
            resource_reference=None,
            scope=guard.scope,
            purpose=requested_purpose,
        )
    grant.window.assert_covers(guard.now)
    grant.organization_scope.assert_matches(guard.scope)
    grant.resource_scope.assert_admits(requested_domain, None)
    grant.purpose.assert_admits(requested_purpose)
    if requested_operation not in grant.permitted_operations:
        raise PrivilegePurposeMismatchError(
            f"operation {requested_operation!r} is outside the grant's operation set"
        )
    if grant.policy_version != policy.policy_version:
        raise OptimisticConcurrencyConflictError(
            f"the grant was approved under policy {grant.policy_version!r}; the current policy "
            f"is {policy.policy_version!r} and activation requires a fresh decision"
        )
    assert_not_self_approval(
        guard.authority.actor_reference,
        grant.approvers[0] if grant.approvers else "",
        action="activate_privileged_access",
    )

    before_hash = _state_hash(grant.to_state_payload())
    evaluation = SeparationOfDutiesEvaluation(
        evaluation_id=uuid5(_EMISSION_NAMESPACE, f"sod-activation:{grant_id}"),
        evaluated_at=guard.now,
        subject_reference=grant.subject_reference,
        held_roles=port.held_roles(grant.subject_reference, guard.scope),
        outcome="passed",
        stage="activation",
    )
    grant = grant.with_evaluation(evaluation).with_state(
        GrantState.ACTIVATED,
        at=guard.now,
        action="activate_privileged_access",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type="privileged_access.activated",
        aggregate_id=grant_id,
        payload=privileged_events.access_state_payload(
            grant_id=grant_id,
            state=str(grant.state),
            reason_code=reason.reason_code,
            policy_version=policy.policy_version,
            at=guard.now.isoformat(),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=RC_ACCESS_ACTIVATED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return GrantResult(grant=grant, event=event, audit_event=audit_event)


def _transition_grant(
    stores: PrivilegedStores,
    *,
    command: str,
    event_type: str,
    audit_reason_code: str,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    grant_id: UUID,
    target: GrantState,
    reason: ReasonCoded,
    expected_history_length: int | None,
) -> GrantResult:
    """The shared body of `expire_privileged_access` and
    `revoke_privileged_access`.

    Shared because the two differ only in target state and reason code -
    and because two hand-written copies of a guarded transition drift."""
    grant = _load_grant(stores, grant_id, context.require_scope())
    guard = _guard(
        stores,
        command=command,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(grant_id), str(target), reason.reason_code),
        target_scope=grant.organization_scope,
        current_version=len(grant.history),
        expected_version=expected_history_length,
        version_label="grant history",
    )
    if guard.replay is not None:
        return _replayed_grant(stores, guard, event_type)

    before_hash = _state_hash(grant.to_state_payload())
    grant = grant.with_state(
        target,
        at=guard.now,
        action=command,
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type=event_type,
        aggregate_id=grant_id,
        payload=privileged_events.access_state_payload(
            grant_id=grant_id,
            state=str(grant.state),
            reason_code=reason.reason_code,
            policy_version=policy.policy_version,
            at=guard.now.isoformat(),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=audit_reason_code,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return GrantResult(grant=grant, event=event, audit_event=audit_event)


def expire_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    grant_id: UUID,
    reason: ReasonCoded,
    expected_history_length: int | None = None,
) -> GrantResult:
    """Expire a grant. Expiry is a recorded act, not the mere absence of
    a renewal: a grant that simply stops working leaves nothing to
    review, and `P12-PAM-007` forbids automatic renewal precisely so that
    continued access always costs a fresh decision."""
    return _transition_grant(
        stores,
        command="expire_privileged_access",
        event_type="privileged_access.expired",
        audit_reason_code=RC_ACCESS_EXPIRED,
        context=context,
        port=port,
        clock=clock,
        policy=policy,
        grant_id=grant_id,
        target=GrantState.EXPIRED,
        reason=reason,
        expected_history_length=expected_history_length,
    )


def revoke_privileged_access(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    grant_id: UUID,
    reason: ReasonCoded,
    expected_history_length: int | None = None,
) -> GrantResult:
    """Revoke a grant with immediate effect (`P12-PAM-009`).

    Revocation is not deletion. The grant, its history and every session
    it authorised remain; what stops is the authority to act."""
    return _transition_grant(
        stores,
        command="revoke_privileged_access",
        event_type="privileged_access.revoked",
        audit_reason_code=RC_ACCESS_REVOKED,
        context=context,
        port=port,
        clock=clock,
        policy=policy,
        grant_id=grant_id,
        target=GrantState.REVOKED,
        reason=reason,
        expected_history_length=expected_history_length,
    )


def request_access_review(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    grant_id: UUID,
    review_kind: str,
    reason: ReasonCoded,
) -> GrantResult:
    """Open a periodic or post-access review of a grant (`P12-PAM-008`).

    A post-access review moves the grant into
    `UNDER_POST_ACCESS_REVIEW`; a periodic review does not, because a
    grant under periodic review is still a live grant and suspending it
    silently would be a control acting as an outage."""
    grant = _load_grant(stores, grant_id, context.require_scope())
    guard = _guard(
        stores,
        command="request_access_review",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(grant_id), review_kind),
        target_scope=grant.organization_scope,
        prior_actor_references=(grant.subject_reference,),
    )
    if guard.replay is not None:
        return _replayed_grant(stores, guard, "privileged_access.review_requested")

    before_hash = _state_hash(grant.to_state_payload())
    if review_kind == "post_access":
        grant = grant.with_state(
            GrantState.UNDER_POST_ACCESS_REVIEW,
            at=guard.now,
            action="request_access_review",
            reason=reason,
            actor_reference=guard.authority.actor_reference,
        )
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type="privileged_access.review_requested",
        aggregate_id=grant_id,
        payload=privileged_events.review_payload(
            review_id=guard.event_id,
            grant_id=grant_id,
            review_kind=review_kind,
            outcome="requested",
            reason_code=reason.reason_code,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=RC_REVIEW_REQUESTED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return GrantResult(grant=grant, event=event, audit_event=audit_event)


def complete_access_review(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    grant_id: UUID,
    review_id: UUID,
    review_kind: str,
    outcome: str,
    reason: ReasonCoded,
    findings_reference: str | None = None,
) -> AccessReviewResult:
    """Record the outcome of a review.

    The reviewer must be neither the grant's subject nor one of its
    approvers: a review by a party to the decision under review is not a
    review (role pairs 3, 7, 8 and 13 in the separation matrix say the
    same thing structurally)."""
    grant = _load_grant(stores, grant_id, context.require_scope())
    guard = _guard(
        stores,
        command="complete_access_review",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(grant_id), str(review_id), outcome),
        target_scope=grant.organization_scope,
        prior_actor_references=(grant.subject_reference, *grant.approvers),
    )
    if guard.replay is not None:
        reviews = stores.reviews.list_for_grant(grant_id)
        replayed = next((r for r in reviews if r.review_id == review_id), None)
        if replayed is None:  # pragma: no cover - defensive
            _raise_not_found("privileged access review", review_id)
            raise AssertionError  # pragma: no cover
        return AccessReviewResult(
            review=replayed,
            grant=grant,
            event=_rebuilt_review_event(replayed, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    review = PrivilegedAccessReview(
        review_id=review_id,
        grant_id=grant_id,
        organization_scope=grant.organization_scope,
        review_kind=review_kind,
        reviewer_reference=guard.authority.actor_reference,
        reviewed_at=guard.now,
        outcome=outcome,
        reason=reason,
        findings_reference=findings_reference,
    )
    stores.reviews.save(review)

    before_hash = _state_hash(grant.to_state_payload())
    if grant.state is GrantState.UNDER_POST_ACCESS_REVIEW:
        grant = grant.with_state(
            GrantState.REVIEW_COMPLETED,
            at=guard.now,
            action="complete_access_review",
            reason=reason,
            actor_reference=guard.authority.actor_reference,
        )
    grant = grant.with_review(str(review_id))
    stores.grants.save(grant)

    event = _rebuilt_review_event(review, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_access_grant",
                target_id=grant_id,
                reason_code=RC_REVIEW_COMPLETED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=grant_id,
        clock=clock,
    )
    return AccessReviewResult(review=review, grant=grant, event=event, audit_event=audit_event)


def _rebuilt_review_event(review: PrivilegedAccessReview, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="privileged_access.review_completed",
        aggregate_id=review.grant_id,
        payload=privileged_events.review_payload(
            review_id=review.review_id,
            grant_id=review.grant_id,
            review_kind=review.review_kind,
            outcome=review.outcome,
            reason_code=review.reason.reason_code,
        ),
    )


def _replayed_grant(stores: PrivilegedStores, guard: _CommandGuard, event_type: str) -> GrantResult:
    """Rebuild the result of an already-executed grant command.

    The stored aggregate is authoritative; the envelope is rebuilt from
    it rather than cached, so a replay can never return an event that
    disagrees with the state it describes."""
    grant = stores.grants.get(guard.replay.aggregate_id) if guard.replay else None
    if grant is None:  # pragma: no cover - defensive
        _raise_not_found("privileged access grant", guard.event_id)
        raise AssertionError  # pragma: no cover
    if event_type == "privileged_access.approved":
        payload = privileged_events.access_decision_payload(
            grant_id=grant.grant_id,
            approver_references=grant.approvers,
            reason_code=grant.history[-1].reason.reason_code if grant.history else "",
            policy_version=grant.policy_version,
            evaluation_reference=(
                str(grant.approval_evaluation.evaluation_id) if grant.approval_evaluation else None
            ),
        )
    elif event_type == "privileged_access.denied":
        payload = privileged_events.access_decision_payload(
            grant_id=grant.grant_id,
            approver_references=(),
            reason_code=grant.history[-1].reason.reason_code if grant.history else "",
            policy_version=grant.policy_version,
        )
    elif event_type == "privileged_access.review_requested":
        payload = privileged_events.review_payload(
            review_id=guard.event_id,
            grant_id=grant.grant_id,
            review_kind="post_access",
            outcome="requested",
            reason_code=grant.history[-1].reason.reason_code if grant.history else "",
        )
    else:
        payload = privileged_events.access_state_payload(
            grant_id=grant.grant_id,
            state=str(grant.state),
            reason_code=grant.history[-1].reason.reason_code if grant.history else "",
            policy_version=grant.policy_version,
            at=guard.now.isoformat(),
        )
    return GrantResult(
        grant=grant,
        event=_event(guard, event_type=event_type, aggregate_id=grant.grant_id, payload=payload),
        audit_event=_replayed_audit(stores, guard),
    )


# ---------------------------------------------------------------------------
# Commands: privileged sessions
# ---------------------------------------------------------------------------


def start_privileged_session(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    session_id: UUID,
    grant_id: UUID,
    target_system: str,
    target_domain: str,
    requested_purpose: Purpose,
    reason: ReasonCoded,
    break_glass_marker: bool = False,
) -> SessionResult:
    """Open a privileged session under an activated grant
    (`P12-SES-001`).

    `assert_usable` runs first and in full: state, window, dormancy,
    organization, resource, operation and purpose. A grant that was
    activated an hour ago is not a grant that is usable now."""
    grant = _load_grant(stores, grant_id, context.require_scope())
    guard = _guard(
        stores,
        command="start_privileged_session",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(session_id), str(grant_id), target_system, target_domain),
        target_scope=grant.organization_scope,
    )
    if guard.replay is not None:
        return _replayed_session(stores, guard, "privileged_session.started")

    for operation in sorted(grant.permitted_operations):
        grant.assert_usable(
            at=guard.now,
            policy=policy,
            operation=operation,
            domain=target_domain,
            resource_reference=None,
            scope=guard.scope,
            purpose=requested_purpose,
        )

    session = PrivilegedSession(
        session_id=session_id,
        actor_reference=grant.subject_reference,
        effective_role=str(grant.role),
        grant_reference=grant_id,
        purpose=grant.purpose,
        target_system=target_system,
        target_domain=target_domain,
        organization_scope=grant.organization_scope,
        permitted_operations=grant.permitted_operations,
        started_at=guard.now,
        approval_references=grant.approvers,
        break_glass_marker=break_glass_marker,
        previous_hash=stores.sealed_sessions.head_hash(),
    )
    stores.sessions.save(session)

    before_hash = _state_hash(grant.to_state_payload())
    if grant.state is GrantState.ACTIVATED:
        grant = grant.with_state(
            GrantState.ACTIVE,
            at=guard.now,
            action="start_privileged_session",
            reason=reason,
            actor_reference=guard.authority.actor_reference,
        )
    grant = grant.with_use(guard.now)
    stores.grants.save(grant)

    event = _event(
        guard,
        event_type="privileged_session.started",
        aggregate_id=session_id,
        payload=privileged_events.session_started_payload(
            session_id=session_id,
            grant_reference=grant_id,
            effective_role=str(grant.role),
            purpose=str(grant.purpose.purpose),
            permitted_operations=grant.permitted_operations,
            break_glass_marker=break_glass_marker,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_session",
                target_id=session_id,
                reason_code=RC_SESSION_STARTED,
                before_hash=before_hash,
                after_hash=_state_hash(grant.to_state_payload()),
            ),
        ),
        aggregate_id=session_id,
        clock=clock,
    )
    return SessionResult(session=session, event=event, audit_event=audit_event)


def record_session_operation(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    session_id: UUID,
    sequence: int,
    operation: str,
    resource_domain: str,
    resource_reference: str | None,
    outcome: str,
    summary_reference: str,
) -> PrivilegedSession:
    """Record one operation performed inside a live session
    (`P12-SES-002`).

    **This command deliberately emits no event and writes no audit row of
    its own**, and the reason is worth stating rather than discovering.
    The evidence of what happened inside a session is the session record
    itself: an append-only summary chain that is hashed and sealed at the
    end (`seal_privileged_session`), whose integrity reference links into
    the sealed-session chain. Per-operation audit rows would duplicate
    that evidence in a second place, and two records of one fact are two
    records that can disagree - which is exactly the second evidence
    system `OD-P12-06` forbids.

    What it does do is re-run the authority frame and re-check the grant
    at the moment of the act. Idempotency is by `sequence`: an
    out-of-order or repeated sequence is refused rather than appended,
    so a retried call cannot inflate the record.

    A `summary_reference` is an opaque pointer, never content: the
    session record carries no user content, no credential and no payload
    (`P12-SES-007`), and `PROHIBITED_PAYLOAD_KEYS` enforces that at seal
    time."""
    session = _load_session(stores, session_id, context.require_scope())
    guard = _guard(
        stores,
        command="record_session_operation",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(session_id), str(sequence), operation),
        target_scope=session.organization_scope,
        allow_audited_replay=True,
    )
    grant = _load_grant(stores, session.grant_reference, guard.scope)
    grant.assert_usable(
        at=guard.now,
        policy=policy,
        operation=operation,
        domain=resource_domain,
        resource_reference=resource_reference,
        scope=guard.scope,
        purpose=session.purpose.purpose,
    )
    expected = len(session.operation_summaries) + 1
    if sequence != expected:
        raise OptimisticConcurrencyConflictError(
            f"session {session_id} expects operation sequence {expected}, got {sequence}"
        )

    session = session.with_operation(
        OperationSummary(
            sequence=sequence,
            occurred_at=guard.now,
            operation=operation,
            resource_domain=resource_domain,
            resource_reference=resource_reference,
            outcome=outcome,
            summary_reference=summary_reference,
        )
    )
    if resource_reference is not None:
        session = session.with_accessed_resource(resource_reference)
    stores.sessions.save(session)
    stores.grants.save(grant.with_use(guard.now))
    return session


def end_privileged_session(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    session_id: UUID,
) -> SessionResult:
    """Close a session. The record stops accumulating; nothing is
    removed."""
    session = _load_session(stores, session_id, context.require_scope())
    guard = _guard(
        stores,
        command="end_privileged_session",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(session_id),),
        target_scope=session.organization_scope,
        current_version=len(session.operation_summaries),
        expected_version=None,
    )
    if guard.replay is not None:
        return _replayed_session(stores, guard, "privileged_session.ended")

    session = session.end(guard.now)
    stores.sessions.save(session)

    event = _event(
        guard,
        event_type="privileged_session.ended",
        aggregate_id=session_id,
        payload=privileged_events.session_ended_payload(
            session_id=session_id,
            operation_count=len(session.operation_summaries),
            ended_at=guard.now.isoformat(),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_session",
                target_id=session_id,
                reason_code=RC_SESSION_ENDED,
                after_hash=_state_hash(session.hashable_fields()),
            ),
        ),
        aggregate_id=session_id,
        clock=clock,
    )
    return SessionResult(session=session, event=event, audit_event=audit_event)


def seal_privileged_session(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    session_id: UUID,
    evidence_bundle_reference: str,
) -> SealedSessionResult:
    """Seal an ended session into the tamper-evident chain
    (`P12-SES-003`).

    "Tamper-**evident**", precisely: the hash chain makes alteration
    detectable, and nothing here prevents it. A claim of tamper
    resistance would require controls - hardware roots of trust,
    independent custody - that this package does not implement and does
    not pretend to (FIR-INV-015).

    The evidence bundle reference is PACK-11's. PACK-12 defines no
    parallel evidence store (`P12-SES-005`)."""
    session = _load_session(stores, session_id, context.require_scope())
    guard = _guard(
        stores,
        command="seal_privileged_session",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(session_id), evidence_bundle_reference),
        target_scope=session.organization_scope,
        prior_actor_references=(session.actor_reference,),
    )
    if guard.replay is not None:
        sealed = stores.sealed_sessions.get(session_id)
        if sealed is None:  # pragma: no cover - defensive
            _raise_not_found("sealed privileged session", session_id)
            raise AssertionError  # pragma: no cover
        return SealedSessionResult(
            sealed=sealed,
            event=_rebuilt_seal_event(sealed, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    # The chain head is read at seal time, not at session start: a
    # session that began before another was sealed still links to the
    # head that existed when *it* was sealed.
    session = replace(session, previous_hash=stores.sealed_sessions.head_hash())
    sealed = session.seal(evidence_bundle_reference=evidence_bundle_reference)
    stores.sealed_sessions.append(sealed)
    stores.sessions.save(replace(session, state=SessionState.SEALED))

    event = _rebuilt_seal_event(sealed, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="privileged_session",
                target_id=session_id,
                reason_code=RC_SESSION_SEALED,
                after_hash=sealed.integrity_reference,
            ),
        ),
        aggregate_id=session_id,
        clock=clock,
    )
    return SealedSessionResult(sealed=sealed, event=event, audit_event=audit_event)


def _rebuilt_seal_event(sealed: SealedPrivilegedSession, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="privileged_session.evidence_sealed",
        aggregate_id=sealed.session_id,
        payload=privileged_events.session_sealed_payload(
            session_id=sealed.session_id,
            integrity_reference=sealed.integrity_reference,
            evidence_bundle_reference=sealed.evidence_bundle_reference,
        ),
    )


def _replayed_session(
    stores: PrivilegedStores, guard: _CommandGuard, event_type: str
) -> SessionResult:
    session = stores.sessions.get(guard.replay.aggregate_id) if guard.replay else None
    if session is None:  # pragma: no cover - defensive
        _raise_not_found("privileged session", guard.event_id)
        raise AssertionError  # pragma: no cover
    if event_type == "privileged_session.started":
        payload = privileged_events.session_started_payload(
            session_id=session.session_id,
            grant_reference=session.grant_reference,
            effective_role=session.effective_role,
            purpose=str(session.purpose.purpose),
            permitted_operations=session.permitted_operations,
            break_glass_marker=session.break_glass_marker,
        )
    else:
        payload = privileged_events.session_ended_payload(
            session_id=session.session_id,
            operation_count=len(session.operation_summaries),
            ended_at=(session.ended_at or session.started_at).isoformat(),
        )
    return SessionResult(
        session=session,
        event=_event(
            guard, event_type=event_type, aggregate_id=session.session_id, payload=payload
        ),
        audit_event=_replayed_audit(stores, guard),
    )


# ---------------------------------------------------------------------------
# Commands: break-glass
# ---------------------------------------------------------------------------
#
# A separate workflow, not a mode of the one above. Nothing in this
# section relaxes a check anywhere else in this module; everything in it
# *adds* an obligation - a second approver, a notification, a shorter
# ceiling, an independent review (`P12-BG-009`, FIR-INV-006).


def request_break_glass(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    activation_id: UUID,
    condition: EmergencyCondition,
    purpose: PurposeBinding,
    resource_domain: str,
    permitted_operations: frozenset[str],
    window: EffectiveWindow,
    approver_reference: str,
    reason: ReasonCoded,
) -> BreakGlassResult:
    """Request emergency access against a documented condition.

    The condition is mandatory and is not a free-text excuse: without a
    `condition_reference` there is nothing to review afterwards, which is
    what `BreakGlassConditionAbsentError` says. The window is checked
    against the break-glass ceiling, which is far shorter than the
    ordinary grant ceiling."""
    guard = _guard(
        stores,
        command="request_break_glass",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(activation_id), condition.condition_reference, resource_domain),
        prior_actor_references=(approver_reference,),
    )
    if guard.replay is not None:
        return _replayed_break_glass(stores, guard, "break_glass.requested")

    policy.assert_break_glass_duration_allowed(window.duration)
    activation = BreakGlassActivation(
        activation_id=activation_id,
        organization_scope=guard.scope,
        activator_reference=guard.authority.actor_reference,
        approver_reference=approver_reference,
        condition=condition,
        purpose=purpose,
        resource_domain=resource_domain,
        permitted_operations=permitted_operations,
        window=window,
        policy_version=policy.policy_version,
    )
    activation.assert_scope_narrow(policy)
    stores.break_glass.save(activation)

    event = _event(
        guard,
        event_type="break_glass.requested",
        aggregate_id=activation_id,
        payload=privileged_events.break_glass_payload(
            activation_id=activation_id,
            condition_reference=condition.condition_reference,
            condition_class=condition.condition_class,
            permitted_operations=permitted_operations,
            valid_until=window.valid_until.isoformat(),
            reason_code=reason.reason_code,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=RC_BREAK_GLASS_REQUESTED,
                after_hash=_state_hash(activation.to_state_payload()),
            ),
        ),
        aggregate_id=activation_id,
        clock=clock,
    )
    return BreakGlassResult(activation=activation, event=event, audit_event=audit_event)


def approve_break_glass(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    reason: ReasonCoded,
    previous_activation_id: UUID | None = None,
) -> BreakGlassResult:
    """The second control (`P12-BG-003`).

    The approving authority must not be the activator, and the check is
    made twice over: `prior_actor_references` compares the acting
    authority with the recorded activator, and the `break_glass_approver`
    role is pairwise incompatible with `system_administrator` - the most
    likely activator - in the separation matrix.

    A renewal is a *new decision*, never an extension
    (`assert_renewal_is_new_decision`): passing the previous activation
    proves a distinct identifier and forces the whole workflow again."""
    activation = _load_activation(stores, activation_id, context.require_scope())
    guard = _guard(
        stores,
        command="approve_break_glass",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(activation_id), reason.reason_code),
        target_scope=activation.organization_scope,
        prior_actor_references=(activation.activator_reference,),
    )
    if guard.replay is not None:
        return _replayed_break_glass(stores, guard, "break_glass.approved")

    if previous_activation_id is not None:
        previous = _load_activation(stores, previous_activation_id, guard.scope)
        assert_renewal_is_new_decision(previous, activation_id)

    before_hash = _state_hash(activation.to_state_payload())
    activation = activation.with_state(
        BreakGlassState.APPROVED,
        at=guard.now,
        action="approve_break_glass",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.break_glass.save(activation)

    event = _event(
        guard,
        event_type="break_glass.approved",
        aggregate_id=activation_id,
        payload=privileged_events.break_glass_payload(
            activation_id=activation_id,
            condition_reference=activation.condition.condition_reference,
            condition_class=activation.condition.condition_class,
            permitted_operations=activation.permitted_operations,
            valid_until=activation.window.valid_until.isoformat(),
            reason_code=reason.reason_code,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=RC_BREAK_GLASS_APPROVED,
                before_hash=before_hash,
                after_hash=_state_hash(activation.to_state_payload()),
            ),
        ),
        aggregate_id=activation_id,
        clock=clock,
    )
    return BreakGlassResult(activation=activation, event=event, audit_event=audit_event)


def activate_break_glass(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    recipient_class: str,
    reason: ReasonCoded,
    directed_subjects: frozenset[str] = frozenset(),
) -> BreakGlassResult:
    """Activate approved emergency access and notify.

    Notification is **part of the act**, not a side effect
    (`P12-BG-006`). Two consequences follow, and both are implemented
    here rather than left to an operator:

    - A notification the activator suppressed, or that was directed only
      at the activator, is not a notification
      (`assert_notification_not_suppressed`).
    - An undelivered notification escalates rather than passing silently
      (`P12-BG-008`): the activation moves to `ESCALATED`, a
      `break_glass.notification_dispatched` event is emitted carrying the
      failure, and `BreakGlassNotificationUndeliveredError` is raised.
      Emergency access whose notification failed is emergency access
      nobody was told about.

    The transport itself is PACK-17's; `NotificationPort` is the seam."""
    activation = _load_activation(stores, activation_id, context.require_scope())
    guard = _guard(
        stores,
        command="activate_break_glass",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(activation_id), recipient_class),
        target_scope=activation.organization_scope,
        prior_actor_references=(activation.approver_reference,),
    )
    if guard.replay is not None:
        return _replayed_break_glass(stores, guard, "break_glass.activated")

    before_hash = _state_hash(activation.to_state_payload())
    outcome: NotificationOutcome = stores.notifications.dispatch(
        activation_id=activation_id,
        organization_scope=activation.organization_scope,
        recipient_class=recipient_class,
        activator_reference=activation.activator_reference,
    )
    assert_notification_not_suppressed(
        outcome,
        activator_reference=activation.activator_reference,
        directed_subjects=directed_subjects,
    )

    target_state = BreakGlassState.ACTIVATED if outcome.delivered else BreakGlassState.ESCALATED
    activation = activation.with_notification(outcome).with_state(
        target_state,
        at=guard.now,
        action="activate_break_glass",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.break_glass.save(activation)

    activation_event = _event(
        guard,
        event_type="break_glass.activated",
        aggregate_id=activation_id,
        payload=privileged_events.break_glass_payload(
            activation_id=activation_id,
            condition_reference=activation.condition.condition_reference,
            condition_class=activation.condition.condition_class,
            permitted_operations=activation.permitted_operations,
            valid_until=activation.window.valid_until.isoformat(),
            reason_code=reason.reason_code,
        ),
    )
    notification_event = _event(
        guard,
        event_type="break_glass.notification_dispatched",
        aggregate_id=activation_id,
        payload=privileged_events.notification_dispatched_payload(
            activation_id=activation_id,
            recipient_class=outcome.recipient_class,
            delivered=outcome.delivered,
            dispatch_reference=outcome.dispatch_reference,
            failure_reason=outcome.failure_reason,
        ),
    )
    after_hash = _state_hash(activation.to_state_payload())
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=activation_event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=RC_BREAK_GLASS_ACTIVATED,
                before_hash=before_hash,
                after_hash=after_hash,
            ),
            _Emission(
                event=notification_event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=RC_BREAK_GLASS_NOTIFIED,
                before_hash=after_hash,
                after_hash=after_hash,
            ),
        ),
        aggregate_id=activation_id,
        clock=clock,
    )
    if not outcome.delivered:
        raise BreakGlassNotificationUndeliveredError(
            f"break-glass activation {activation_id} could not be notified "
            f"({outcome.failure_reason or 'no reason reported'}); the activation is escalated "
            "and the failure is recorded, not suppressed"
        )
    return BreakGlassResult(activation=activation, event=activation_event, audit_event=audit_event)


def _transition_break_glass(
    stores: PrivilegedStores,
    *,
    command: str,
    event_type: str,
    audit_reason_code: str,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    target: BreakGlassState,
    reason: ReasonCoded,
) -> BreakGlassResult:
    activation = _load_activation(stores, activation_id, context.require_scope())
    guard = _guard(
        stores,
        command=command,
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(activation_id), str(target), reason.reason_code),
        target_scope=activation.organization_scope,
    )
    if guard.replay is not None:
        return _replayed_break_glass(stores, guard, event_type)

    before_hash = _state_hash(activation.to_state_payload())
    activation = activation.with_state(
        target,
        at=guard.now,
        action=command,
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    )
    stores.break_glass.save(activation)

    event = _event(
        guard,
        event_type=event_type,
        aggregate_id=activation_id,
        payload=privileged_events.break_glass_payload(
            activation_id=activation_id,
            condition_reference=activation.condition.condition_reference,
            condition_class=activation.condition.condition_class,
            permitted_operations=activation.permitted_operations,
            valid_until=activation.window.valid_until.isoformat(),
            reason_code=reason.reason_code,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=audit_reason_code,
                before_hash=before_hash,
                after_hash=_state_hash(activation.to_state_payload()),
            ),
        ),
        aggregate_id=activation_id,
        clock=clock,
    )
    return BreakGlassResult(activation=activation, event=event, audit_event=audit_event)


def expire_break_glass(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    reason: ReasonCoded,
) -> BreakGlassResult:
    """Expire emergency access. There is no renewal path from here: a
    continued emergency needs a new activation, a new approval and a new
    notification (`P12-BG-013`)."""
    return _transition_break_glass(
        stores,
        command="expire_break_glass",
        event_type="break_glass.expired",
        audit_reason_code=RC_BREAK_GLASS_EXPIRED,
        context=context,
        port=port,
        clock=clock,
        activation_id=activation_id,
        target=BreakGlassState.EXPIRED,
        reason=reason,
    )


def revoke_break_glass(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    reason: ReasonCoded,
) -> BreakGlassResult:
    """Withdraw emergency access before its window closes."""
    return _transition_break_glass(
        stores,
        command="revoke_break_glass",
        event_type="break_glass.revoked",
        audit_reason_code=RC_BREAK_GLASS_REVOKED,
        context=context,
        port=port,
        clock=clock,
        activation_id=activation_id,
        target=BreakGlassState.REVOKED,
        reason=reason,
    )


def complete_break_glass_review(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    activation_id: UUID,
    review_id: UUID,
    outcome: str,
    reason: ReasonCoded,
    findings_reference: str | None = None,
) -> BreakGlassReviewResult:
    """Independent post-hoc review of an emergency activation
    (`P12-BG-014`).

    The reviewer must be neither the activator nor the approver -
    `assert_distinct_reviewer` and `assert_reviewer_independent` check it
    from both directions, and the role pair table makes
    `break_glass_approver` and `independent_privileged_access_reviewer`
    structurally incompatible on top."""
    activation = _load_activation(stores, activation_id, context.require_scope())
    guard = _guard(
        stores,
        command="complete_break_glass_review",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(activation_id), str(review_id), outcome),
        target_scope=activation.organization_scope,
        prior_actor_references=(
            activation.activator_reference,
            activation.approver_reference,
        ),
    )
    if guard.replay is not None:
        replayed = stores.break_glass_reviews.get_for_activation(activation_id)
        if replayed is None:  # pragma: no cover - defensive
            _raise_not_found("break-glass independent review", review_id)
            raise AssertionError  # pragma: no cover
        return BreakGlassReviewResult(
            review=replayed,
            activation=activation,
            event=_rebuilt_break_glass_review_event(replayed, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    assert_distinct_reviewer(
        guard.authority.actor_reference,
        activator=activation.activator_reference,
        approver=activation.approver_reference,
    )
    review = BreakGlassIndependentReview(
        review_id=review_id,
        activation_id=activation_id,
        organization_scope=activation.organization_scope,
        reviewer_reference=guard.authority.actor_reference,
        reviewed_at=guard.now,
        outcome=outcome,
        reason=reason,
        findings_reference=findings_reference,
    )
    review.assert_reviewer_independent(activation)
    stores.break_glass_reviews.save(review)

    before_hash = _state_hash(activation.to_state_payload())
    if activation.state in {
        BreakGlassState.EXPIRED,
        BreakGlassState.REVOKED,
        BreakGlassState.ESCALATED,
    }:
        activation = activation.with_state(
            BreakGlassState.UNDER_INDEPENDENT_REVIEW,
            at=guard.now,
            action="complete_break_glass_review",
            reason=reason,
            actor_reference=guard.authority.actor_reference,
        )
    activation = activation.with_state(
        BreakGlassState.REVIEW_COMPLETED,
        at=guard.now,
        action="complete_break_glass_review",
        reason=reason,
        actor_reference=guard.authority.actor_reference,
    ).with_independent_review(str(review_id))
    stores.break_glass.save(activation)

    event = _rebuilt_break_glass_review_event(review, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="break_glass_activation",
                target_id=activation_id,
                reason_code=RC_BREAK_GLASS_REVIEWED,
                before_hash=before_hash,
                after_hash=_state_hash(activation.to_state_payload()),
            ),
        ),
        aggregate_id=activation_id,
        clock=clock,
    )
    return BreakGlassReviewResult(
        review=review, activation=activation, event=event, audit_event=audit_event
    )


def _rebuilt_break_glass_review_event(
    review: BreakGlassIndependentReview, guard: _CommandGuard
) -> EventEnvelope:
    return _event(
        guard,
        event_type="break_glass.independent_review_completed",
        aggregate_id=review.activation_id,
        payload=privileged_events.review_payload(
            review_id=review.review_id,
            grant_id=review.activation_id,
            review_kind="break_glass_independent",
            outcome=review.outcome,
            reason_code=review.reason.reason_code,
        ),
    )


def _replayed_break_glass(
    stores: PrivilegedStores, guard: _CommandGuard, event_type: str
) -> BreakGlassResult:
    activation = stores.break_glass.get(guard.replay.aggregate_id) if guard.replay else None
    if activation is None:  # pragma: no cover - defensive
        _raise_not_found("break-glass activation", guard.event_id)
        raise AssertionError  # pragma: no cover
    payload = privileged_events.break_glass_payload(
        activation_id=activation.activation_id,
        condition_reference=activation.condition.condition_reference,
        condition_class=activation.condition.condition_class,
        permitted_operations=activation.permitted_operations,
        valid_until=activation.window.valid_until.isoformat(),
        reason_code=activation.history[-1].reason.reason_code if activation.history else "",
    )
    return BreakGlassResult(
        activation=activation,
        event=_event(
            guard,
            event_type=event_type,
            aggregate_id=activation.activation_id,
            payload=payload,
        ),
        audit_event=_replayed_audit(stores, guard),
    )


# ---------------------------------------------------------------------------
# Commands: authorization-aware search
# ---------------------------------------------------------------------------


def submit_search_query(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    source_port: SourceAuthorizationPort,
    clock: Clock,
    request: QueryRequest,
    index_name: str,
    authorization_version: int = 1,
) -> SearchResult:
    """Submit, authorize and execute one query (`P12-SRCH-001`).

    One command, because it is one act. The catalog names four events for
    it - submitted, authorized (or denied), executed, and, where
    something was withheld, restricted-result-suppressed - and all of
    them are emitted here in order, each with its own audit row.

    **Investigation is a purpose, not a mode** (`OD-P12-02`). There is no
    unrestricted investigative search: `SearchMode` has exactly two
    members, and `Purpose.INVESTIGATION` narrows the ordinary scoped
    search like every other purpose while requiring an explicit grant
    (`GRANT_REQUIRED_PURPOSES`).

    The result cache is keyed by the full authorization context, not by
    the query: a cache hit computed under a different requester, mode,
    purpose, policy version or authorization version is refused rather
    than served (`P12-SRCH-009`). That is why `SearchCacheKey` carries
    all seven fields and the fingerprint covers all of them.

    A refusal by `assert_query_admissible` emits the submission and the
    denial, and re-raises. It records **no idempotency row**, because it
    changed no aggregate; a replay re-evaluates deterministically and
    `append_audit_event` recognises the identical rows rather than
    duplicating them. That is what `allow_audited_replay` is for."""
    guard = _guard(
        stores,
        command="submit_search_query",
        context=context,
        port=port,
        clock=clock,
        request_parts=(
            str(request.query_id),
            request.query_digest,
            str(request.mode),
            str(request.purpose),
        ),
        target_scope=request.scope.organization_scope,
        allow_audited_replay=True,
    )
    if guard.replay is not None:
        return _replayed_search(stores, guard)

    submitted_event = _event(
        guard,
        event_type="search_query.submitted",
        aggregate_id=request.query_id,
        payload=privileged_events.query_submitted_payload(
            query_id=request.query_id,
            mode=str(request.mode),
            purpose=str(request.purpose),
            query_digest=request.query_digest,
            domains=request.scope.domains,
        ),
    )

    index_policy = stores.index_policies.get(index_name)
    if index_policy is None:
        _raise_not_found("index policy", request.query_id)
        raise AssertionError  # pragma: no cover

    try:
        assert_query_admissible(request, caller_scope=guard.scope)
    except Exception as refusal:
        denied_event = _event(
            guard,
            event_type="search_query.denied",
            aggregate_id=request.query_id,
            payload=privileged_events.query_denied_payload(
                query_id=request.query_id,
                reason_code=getattr(refusal, "reason_code", "PERMISSION_DENIED"),
            ),
        )
        _append_only(
            stores,
            guard,
            (
                _Emission(
                    event=submitted_event,
                    target_type="query_audit",
                    target_id=request.query_id,
                    reason_code=RC_QUERY_SUBMITTED,
                ),
                _Emission(
                    event=denied_event,
                    target_type="query_audit",
                    target_id=request.query_id,
                    reason_code=RC_QUERY_DENIED,
                ),
            ),
            clock=clock,
        )
        raise

    cache_key = SearchCacheKey(
        requester_reference=request.requester_reference,
        organization_id=str(request.scope.organization_scope.organization_id),
        mode=str(request.mode),
        purpose=str(request.purpose),
        query_digest=request.query_digest,
        policy_version=index_policy.policy_version,
        authorization_version=authorization_version,
    )
    cached = stores.search_cache.get(cache_key.fingerprint())
    if cached is not None:
        assert_cache_context_matches(cache_key, cache_key)
        decision = cached
    else:
        decision = execute_query(
            request,
            stores.index.candidates(
                scope=request.scope.organization_scope, domains=request.scope.domains
            ),
            caller_scope=guard.scope,
            index_policy=index_policy,
            port=source_port,
            at=guard.now,
        )
        stores.search_cache.put(cache_key.fingerprint(), decision)

    query_audit = QueryAudit(
        query_id=request.query_id,
        organization_scope=request.scope.organization_scope,
        requester_reference=request.requester_reference,
        mode=str(request.mode),
        purpose=str(request.purpose),
        query_digest=request.query_digest,
        authorized_count=decision.authorized_count,
        suppressed_band=decision.suppressed_band,
        policy_version=decision.policy_version,
        executed_at=guard.now,
        grant_reference=request.grant_reference,
    )
    stores.query_audit.save(query_audit)

    authorized_event = _event(
        guard,
        event_type="search_query.authorized",
        aggregate_id=request.query_id,
        payload=privileged_events.query_authorized_payload(
            query_id=request.query_id,
            mode=str(request.mode),
            purpose=str(request.purpose),
            grant_reference=request.grant_reference,
        ),
    )
    executed_event = _event(
        guard,
        event_type="search_query.executed",
        aggregate_id=request.query_id,
        payload=privileged_events.query_executed_payload(
            query_id=request.query_id,
            authorized_count=decision.authorized_count,
            suppressed_band=decision.suppressed_band,
            policy_version=decision.policy_version,
        ),
    )
    emissions = [
        _Emission(
            event=submitted_event,
            target_type="query_audit",
            target_id=request.query_id,
            reason_code=RC_QUERY_SUBMITTED,
        ),
        _Emission(
            event=authorized_event,
            target_type="query_audit",
            target_id=request.query_id,
            reason_code=RC_QUERY_AUTHORIZED,
        ),
        _Emission(
            event=executed_event,
            target_type="query_audit",
            target_id=request.query_id,
            reason_code=RC_QUERY_EXECUTED,
            after_hash=_state_hash(query_audit.to_state_payload()),
        ),
    ]
    if decision.suppressed_band != "none":
        emissions.append(
            _Emission(
                event=_event(
                    guard,
                    event_type="search_query.restricted_result_suppressed",
                    aggregate_id=request.query_id,
                    payload=privileged_events.query_suppressed_payload(
                        query_id=request.query_id,
                        suppressed_band=decision.suppressed_band,
                        policy_version=decision.policy_version,
                    ),
                ),
                target_type="query_audit",
                target_id=request.query_id,
                reason_code=RC_RESULT_SUPPRESSED,
            )
        )

    audit_event = _finish(stores, guard, emissions, aggregate_id=request.query_id, clock=clock)
    return SearchResult(
        decision=decision,
        query_audit=query_audit,
        event=executed_event,
        audit_event=audit_event,
    )


def _append_only(
    stores: PrivilegedStores,
    guard: _CommandGuard,
    emissions: Sequence[_Emission],
    *,
    clock: Clock,
) -> None:
    """Record emissions for an act that changed no aggregate.

    Used only on the search-denial path. Deliberately does **not** write
    an idempotency row: there is no aggregate state a replay could skip
    re-deriving, and a stored row would turn a deterministic re-denial
    into a spurious conflict."""
    for ordinal, emission in enumerate(emissions):
        audit_id = (
            guard.event_id
            if ordinal == 0
            else _emission_audit_id(guard.event_id, emission.event.event_type, ordinal)
        )
        append_audit_event(
            stores.audit,
            AppendAuditEventRequest(
                audit_event_id=audit_id,
                event_type=emission.event.event_type,
                occurred_at=guard.now,
                actor_id=guard.actor.actor_id,
                actor_type=guard.actor.actor_type,
                target_type=emission.target_type,
                target_id=emission.target_id,
                action=guard.command,
                reason_code=emission.reason_code,
                policy_version=AUDIT_POLICY_VERSION,
                correlation_id=guard.correlation_id,
                source_service=_SOURCE_SERVICE,
                before_hash=emission.before_hash,
                after_hash=emission.after_hash,
            ),
            clock=clock,
        )
        stores.sink.publish(emission.event)


def _replayed_search(stores: PrivilegedStores, guard: _CommandGuard) -> SearchResult:
    query_id = guard.replay.aggregate_id if guard.replay else guard.event_id
    records = stores.query_audit.list_for_scope(scope=guard.scope)
    recorded = next((r for r in records if r.query_id == query_id), None)
    if recorded is None:  # pragma: no cover - defensive
        _raise_not_found("query audit record", query_id)
        raise AssertionError  # pragma: no cover
    decision = QueryDecision(
        query_id=recorded.query_id,
        authorized=True,
        results=(),
        authorized_count=recorded.authorized_count,
        suppressed_band=recorded.suppressed_band,
        facets={},
        policy_version=recorded.policy_version,
    )
    event = _event(
        guard,
        event_type="search_query.executed",
        aggregate_id=query_id,
        payload=privileged_events.query_executed_payload(
            query_id=query_id,
            authorized_count=recorded.authorized_count,
            suppressed_band=recorded.suppressed_band,
            policy_version=recorded.policy_version,
        ),
    )
    return SearchResult(
        decision=decision,
        query_audit=recorded,
        event=event,
        audit_event=_replayed_audit(stores, guard),
    )


def change_index_policy(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: IndexPolicy,
) -> IndexPolicyResult:
    """Change what may be indexed and how (`P12-SRCH-003`).

    Index policy is security policy: what enters the index decides what
    a query can ever reach. Only `security_administrator` may change it,
    and the previous version is recorded so a widening is visible as a
    diff rather than as a state."""
    guard = _guard(
        stores,
        command="change_index_policy",
        context=context,
        port=port,
        clock=clock,
        request_parts=(policy.index_name, policy.policy_version),
    )
    previous = stores.index_policies.get(policy.index_name)
    if guard.replay is not None:
        stored = previous
        if stored is None:  # pragma: no cover - defensive
            _raise_not_found("index policy", guard.event_id)
            raise AssertionError  # pragma: no cover
        return IndexPolicyResult(
            policy=stored,
            event=_rebuilt_index_policy_event(stored, "", guard),
            audit_event=_replayed_audit(stores, guard),
        )

    previous_version = previous.policy_version if previous else ""
    stores.index_policies.save(policy)

    event = _rebuilt_index_policy_event(policy, previous_version, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="index_policy",
                target_id=guard.event_id,
                reason_code=RC_INDEX_POLICY_CHANGED,
                before_hash=_state_hash({"policy_version": previous_version}),
                after_hash=_state_hash({"policy_version": policy.policy_version}),
            ),
        ),
        aggregate_id=guard.event_id,
        clock=clock,
    )
    return IndexPolicyResult(policy=policy, event=event, audit_event=audit_event)


def _rebuilt_index_policy_event(
    policy: IndexPolicy, previous_version: str, guard: _CommandGuard
) -> EventEnvelope:
    return _event(
        guard,
        event_type="search_index.policy_changed",
        aggregate_id=guard.event_id,
        payload=privileged_events.index_policy_changed_payload(
            index_name=policy.index_name,
            previous_version=previous_version,
            new_version=policy.policy_version,
            authority_reference=str(guard.authority.authority_id),
        ),
    )


def request_reindex(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    index_name: str,
    reason: ReasonCoded,
) -> IndexPolicyResult:
    """Ask for an index rebuild under the current policy.

    A reindex re-applies the *current* policy, which means it can only
    ever narrow what a stale index exposes, never widen it: the widening
    decision is `change_index_policy`'s and is audited there."""
    stored = stores.index_policies.get(index_name)
    if stored is None:
        _raise_not_found("index policy", guard_placeholder_id(index_name))
        raise AssertionError  # pragma: no cover
    guard = _guard(
        stores,
        command="request_reindex",
        context=context,
        port=port,
        clock=clock,
        request_parts=(index_name, reason.reason_code),
    )
    if guard.replay is not None:
        return IndexPolicyResult(
            policy=stored,
            event=_rebuilt_reindex_event(stored, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    event = _rebuilt_reindex_event(stored, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="index_policy",
                target_id=guard.event_id,
                reason_code=RC_REINDEX_REQUESTED,
            ),
        ),
        aggregate_id=guard.event_id,
        clock=clock,
    )
    return IndexPolicyResult(policy=stored, event=event, audit_event=audit_event)


def _rebuilt_reindex_event(policy: IndexPolicy, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="search_index.reindex_requested",
        aggregate_id=guard.event_id,
        payload=privileged_events.index_policy_changed_payload(
            index_name=policy.index_name,
            previous_version=policy.policy_version,
            new_version=policy.policy_version,
            authority_reference=str(guard.authority.authority_id),
        ),
    )


def evidence_index_removal(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    removal_id: UUID,
    record_reference: str,
    source_decision_reference: str,
    reason: ReasonCoded,
) -> IndexRemovalResult:
    """Record that a record left the index, with evidence
    (`P12-SRCH-015`).

    Removal from the index is not deletion of the record, and the
    `source_decision_reference` says whose decision it followed: PACK-09
    owns retention and erasure, PACK-11 owns document disposition. An
    index that dropped a record on its own authority would be an
    unaccountable erasure path."""
    guard = _guard(
        stores,
        command="evidence_index_removal",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(removal_id), record_reference, source_decision_reference),
    )
    if guard.replay is not None:
        existing = next((r for r in stores.index.removals() if r.removal_id == removal_id), None)
        if existing is None:  # pragma: no cover - defensive
            _raise_not_found("index removal evidence", removal_id)
            raise AssertionError  # pragma: no cover
        return IndexRemovalResult(
            evidence=existing,
            event=_rebuilt_removal_event(existing, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    evidence = IndexRemovalEvidence(
        removal_id=removal_id,
        record_reference=record_reference,
        organization_scope=guard.scope,
        removed_at=guard.now,
        source_decision_reference=source_decision_reference,
        reason_code=reason.reason_code,
    )
    stores.index.remove(record_reference, evidence)

    event = _rebuilt_removal_event(evidence, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="index_policy",
                target_id=removal_id,
                reason_code=RC_INDEX_REMOVAL,
                after_hash=_state_hash(evidence.to_payload()),
            ),
        ),
        aggregate_id=removal_id,
        clock=clock,
    )
    return IndexRemovalResult(evidence=evidence, event=event, audit_event=audit_event)


def _rebuilt_removal_event(evidence: IndexRemovalEvidence, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="search_index.removal_evidenced",
        aggregate_id=evidence.removal_id,
        payload=privileged_events.index_removal_payload(
            removal_id=evidence.removal_id,
            record_reference=evidence.record_reference,
            source_decision_reference=evidence.source_decision_reference,
            reason_code=evidence.reason_code,
        ),
    )


# ---------------------------------------------------------------------------
# Commands: governed data export
# ---------------------------------------------------------------------------


def request_data_export(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    request: ExportRequest,
    classifications: Sequence[ClassificationDecision],
    has_search_permission: bool,
    has_read_permission: bool,
    has_admin_privilege: bool,
    has_data_owner_authority: bool,
    has_approver: bool,
    under_legal_hold: bool = False,
    cross_scope_basis_reference: str | None = None,
    certified_result_domains: frozenset[str] = frozenset(),
) -> ExportRequestResult:
    """Open a governed export request (`P12-EXP-001`).

    Five distinct things must all be true before an export is even a
    request, and `assert_export_authority` refuses if any is missing:
    search permission is not read permission, read permission is not
    export authority, administrative privilege is not data ownership, and
    none of them is an approval. Bulk extraction is the case where the
    difference matters most, and it is the case where treating one as
    another is easiest.

    A legal hold is **not** an authorization
    (`assert_hold_is_not_authorization`): it can only ever block. Reading
    a hold as permission is a specific, tempting error, so it has its own
    refusal.

    A certified result is never exported through this path
    (`P12-VOTE-005`): the authoritative artifact is the publication
    rendition PACK-04 issues, and an export copy that looked
    authoritative would be a second source of truth for a result."""
    guard = _guard(
        stores,
        command="request_data_export",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(request.export_id), request.requested_format),
        target_scope=request.scope.organization_scope,
        declared_purpose=request.purpose.purpose,
    )
    if guard.replay is not None:
        return _replayed_export(stores, guard, "data_export.requested")

    assert_export_authority(
        has_search_permission=has_search_permission,
        has_read_permission=has_read_permission,
        has_admin_privilege=has_admin_privilege,
        has_data_owner_authority=has_data_owner_authority,
        has_approver=has_approver,
    )
    assert_hold_is_not_authorization(
        under_legal_hold=under_legal_hold, has_export_authority=has_data_owner_authority
    )
    assert_recipient_eligible(request.recipient, classifications)
    assert_cross_scope_basis(request, cross_scope_basis_reference=cross_scope_basis_reference)
    for domain in sorted(request.scope.domains):
        assert_certified_result_not_exported(
            domain=domain, is_certified=domain in certified_result_domains
        )

    stored = request.with_state(ExportState.DLP_ASSESSMENT, action="request_data_export")
    stores.exports.save(stored)

    event = _event(
        guard,
        event_type="data_export.requested",
        aggregate_id=request.export_id,
        payload=privileged_events.export_requested_payload(
            export_id=request.export_id,
            purpose=str(request.purpose.purpose),
            domains=request.scope.domains,
            record_classes=request.scope.record_classes,
            recipient_category=str(request.recipient.category),
            requested_format=request.requested_format,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=request.export_id,
                reason_code=RC_EXPORT_REQUESTED,
                after_hash=_state_hash(stored.to_state_payload()),
            ),
        ),
        aggregate_id=request.export_id,
        clock=clock,
    )
    return ExportRequestResult(request=stored, event=event, audit_event=audit_event)


def record_dlp_assessment(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    export_id: UUID,
    assessment_id: UUID,
    completed_controls: frozenset[DlpControl],
    findings: tuple[object, ...] = (),
    required_transforms: frozenset[DlpControl] = frozenset(),
    outcome: str = "permitted",
    record_count: int = 0,
) -> DlpAssessmentResult:
    """Record the DLP assessment that must precede any approval
    (`P12-DLP-001`).

    Three volume rules run here, against the versioned policy rather than
    against numbers written into this function (`OD-P12-03`): size,
    frequency within the window, and repeated-extraction pattern across
    this requester's recent request digests. The last is the one a
    single-request check cannot catch - twenty small exports are a bulk
    extraction spread thin.

    The assessor is recorded so `assert_assessor_is_not_approver` can
    refuse at approval time. Assessment is not decision
    (`P12-DLP-003`)."""
    export_request = _load_export(stores, export_id, context.require_scope())
    guard = _guard(
        stores,
        command="record_dlp_assessment",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), str(assessment_id), outcome),
        target_scope=export_request.scope.organization_scope,
        prior_actor_references=(export_request.requester_reference,),
    )
    if guard.replay is not None:
        stored_assessment = stores.dlp_assessments.get_for_export(export_id)
        if stored_assessment is None:  # pragma: no cover - defensive
            _raise_not_found("DLP assessment", assessment_id)
            raise AssertionError  # pragma: no cover
        return DlpAssessmentResult(
            assessment=stored_assessment,
            request=export_request,
            event=_rebuilt_assessment_event(
                export_id, str(assessment_id), stored_assessment.outcome, "dlp", guard
            ),
            audit_event=_replayed_audit(stores, guard),
        )

    window_start = frequency_window_start(guard.now, policy)
    recent = [
        r
        for r in stores.exports.list_for_scope(scope=guard.scope)
        if r.requester_reference == export_request.requester_reference
        and r.requested_at >= window_start
    ]
    assert_volume_within_limits(
        record_count=record_count, recent_export_count=len(recent), policy=policy
    )
    assert_no_repeated_extraction_pattern(
        similar_request_digests=stores.query_audit.similar_digests(
            scope=guard.scope,
            requester_reference=export_request.requester_reference,
            digest_prefix=deterministic_digest(str(export_id))[:8],
        ),
        policy=policy,
    )

    assessment = DlpAssessment(
        assessment_id=assessment_id,
        export_id=export_id,
        organization_scope=export_request.scope.organization_scope,
        assessor_reference=guard.authority.actor_reference,
        assessed_at=guard.now,
        completed_controls=completed_controls,
        findings=tuple(findings),  # type: ignore[arg-type]
        required_transforms=required_transforms,
        outcome=_resolve_dlp_outcome(outcome),
    )
    stores.dlp_assessments.save(assessment)

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(
        ExportState.DISCLOSURE_ASSESSMENT, action="record_dlp_assessment"
    )
    updated = replace(updated, dlp_assessment_reference=str(assessment_id))
    stores.exports.save(updated)

    event = _rebuilt_assessment_event(
        export_id, str(assessment_id), assessment.outcome, "dlp", guard
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_EXPORT_DLP_ASSESSED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return DlpAssessmentResult(
        assessment=assessment, request=updated, event=event, audit_event=audit_event
    )


def _resolve_dlp_outcome(value: str) -> DlpOutcome:
    try:
        return DlpOutcome(value)
    except ValueError as exc:
        raise UnknownStatusError(f"unknown DLP outcome {value!r}") from exc


def _rebuilt_assessment_event(
    export_id: UUID,
    assessment_reference: str,
    outcome: object,
    kind: str,
    guard: _CommandGuard,
) -> EventEnvelope:
    event_type = (
        "data_export.dlp_assessment_completed"
        if kind == "dlp"
        else "data_export.disclosure_assessment_completed"
    )
    return _event(
        guard,
        event_type=event_type,
        aggregate_id=export_id,
        payload=privileged_events.export_assessment_payload(
            export_id=export_id,
            assessment_reference=assessment_reference,
            outcome=str(outcome),
            assessment_kind=kind,
        ),
    )


def record_disclosure_assessment(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    export_id: UUID,
    assessment_id: UUID,
) -> DlpAssessmentResult:
    """Attach a completed disclosure-risk assessment to an export.

    The assessment itself is produced by `assess_disclosure_risk`; this
    command records that the export was measured against it. Two
    commands, because the risk assessment has a life of its own - a
    statistical release is assessed whether or not anyone exports it."""
    export_request = _load_export(stores, export_id, context.require_scope())
    assessment = stores.disclosure_assessments.get(assessment_id)
    if assessment is None:
        _raise_not_found("disclosure risk assessment", assessment_id)
        raise AssertionError  # pragma: no cover

    guard = _guard(
        stores,
        command="record_disclosure_assessment",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), str(assessment_id)),
        target_scope=export_request.scope.organization_scope,
        prior_actor_references=(export_request.requester_reference,),
    )
    if guard.replay is not None:
        return DlpAssessmentResult(
            assessment=_require_dlp(stores, export_id),
            request=export_request,
            event=_rebuilt_assessment_event(
                export_id, str(assessment_id), "recorded", "disclosure", guard
            ),
            audit_event=_replayed_audit(stores, guard),
        )

    before_hash = _state_hash(export_request.to_state_payload())
    updated = replace(export_request, disclosure_assessment_reference=str(assessment_id))
    stores.exports.save(updated)

    event = _rebuilt_assessment_event(
        export_id,
        str(assessment_id),
        "passed" if assessment.passed else "failed",
        "disclosure",
        guard,
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_EXPORT_DISCLOSURE_ASSESSED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return DlpAssessmentResult(
        assessment=_require_dlp(stores, export_id),
        request=updated,
        event=event,
        audit_event=audit_event,
    )


def _require_dlp(stores: PrivilegedStores, export_id: UUID) -> DlpAssessment:
    assessment = stores.dlp_assessments.get_for_export(export_id)
    if assessment is None:
        raise DlpAssessmentMissingError(
            f"export {export_id} has no recorded DLP assessment; assessment precedes decision"
        )
    return assessment


def approve_data_export(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    export_id: UUID,
    permitted_fields: frozenset[str],
    reason: ReasonCoded,
) -> ExportRequestResult:
    """Approve an export, fixing the field set it may ever carry.

    Four separations meet here and none is redundant: the requester is
    not the approver (`P12-EXP-006`), the DLP assessor is not the
    approver (`P12-DLP-003`), the data owner is not the export approver
    (role pair 9), and the DLP officer is not the export approver (role
    pair 10). The permitted field set is recorded as a digest on the
    event so a later artifact can be checked against what was actually
    approved rather than against what someone remembers approving."""
    export_request = _load_export(stores, export_id, context.require_scope())
    dlp_assessment = _require_dlp(stores, export_id)
    if export_request.disclosure_assessment_reference is None:
        raise DisclosureAssessmentMissingError(
            f"export {export_id} has no recorded disclosure assessment"
        )

    guard = _guard(
        stores,
        command="approve_data_export",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), *sorted(permitted_fields)),
        target_scope=export_request.scope.organization_scope,
        prior_actor_references=(
            export_request.requester_reference,
            export_request.data_owner_reference,
            dlp_assessment.assessor_reference,
        ),
    )
    if guard.replay is not None:
        return _replayed_export(stores, guard, "data_export.approved")

    assert_assessor_is_not_approver(
        dlp_assessment.assessor_reference, guard.authority.actor_reference
    )
    dlp_assessment.assert_permits_export()

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(
        ExportState.APPROVED, action="approve_data_export"
    ).with_approver(guard.authority.actor_reference)
    stores.exports.save(updated)

    event = _event(
        guard,
        event_type="data_export.approved",
        aggregate_id=export_id,
        payload=privileged_events.export_decision_payload(
            export_id=export_id,
            approver_reference=guard.authority.actor_reference,
            reason_code=reason.reason_code,
            permitted_field_digest=deterministic_digest(*sorted(permitted_fields)),
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_EXPORT_APPROVED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return ExportRequestResult(request=updated, event=event, audit_event=audit_event)


def deny_data_export(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    export_id: UUID,
    reason: ReasonCoded,
) -> ExportRequestResult:
    """Refuse an export as a governed, recorded decision."""
    export_request = _load_export(stores, export_id, context.require_scope())
    guard = _guard(
        stores,
        command="deny_data_export",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), reason.reason_code),
        target_scope=export_request.scope.organization_scope,
        prior_actor_references=(export_request.requester_reference,),
    )
    if guard.replay is not None:
        return _replayed_export(stores, guard, "data_export.denied")

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(ExportState.DENIED, action="deny_data_export")
    stores.exports.save(updated)

    event = _event(
        guard,
        event_type="data_export.denied",
        aggregate_id=export_id,
        payload=privileged_events.export_decision_payload(
            export_id=export_id,
            approver_reference=None,
            reason_code=reason.reason_code,
            permitted_field_digest="",
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_EXPORT_DENIED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return ExportRequestResult(request=updated, event=event, audit_event=audit_event)


def generate_export_artifact(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    export_id: UUID,
    artifact_id: UUID,
    manifest: DatasetManifest,
    rows: Sequence[Mapping[str, str]],
    dlp_profile: DlpPolicyProfile,
    class_fields: frozenset[str],
    purpose_fields: frozenset[str],
    recipient_denied: frozenset[str] = frozenset(),
    revoked_source_references: frozenset[str] = frozenset(),
) -> ArtifactResult:
    """Build the artifact an approved export authorises.

    The field set is **selected**, never filtered after the fact
    (`permitted_field_set` then `build_artifact`): a row that is
    assembled whole and then stripped has existed whole, and something
    that has existed whole can leak whole. DLP transforms are applied to
    that selected projection.

    The artifact is explicitly **not authoritative**
    (`ExportArtifact.is_authoritative` returns `False` and cannot return
    anything else). An export is a copy taken under a purpose; the
    authoritative record stays where it lives."""
    export_request = _load_export(stores, export_id, context.require_scope())
    if export_request.approver_reference is None:
        raise ExportApprovalMissingError(
            f"export {export_id} has no recorded approver; generation requires approval"
        )
    if manifest.export_id != export_id:
        raise ExportManifestMissingError(
            f"manifest {manifest.manifest_id} does not belong to export {export_id}"
        )

    guard = _guard(
        stores,
        command="generate_export_artifact",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), str(artifact_id), manifest.digest()),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        stored_artifact = stores.artifacts.get(artifact_id)
        if stored_artifact is None:  # pragma: no cover - defensive
            _raise_not_found("export artifact", artifact_id)
            raise AssertionError  # pragma: no cover
        return ArtifactResult(
            artifact=stored_artifact,
            event=_rebuilt_artifact_event(stored_artifact, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    assert_source_records_current(
        revoked_references=revoked_source_references,
        requested_references=frozenset(i.record_reference for i in manifest.items),
    )
    permitted = permitted_field_set(
        export_request.requested_fields,
        class_fields=class_fields,
        purpose_fields=purpose_fields,
        recipient_denied=recipient_denied,
    )
    dlp_assessment = _require_dlp(stores, export_id)
    projection = apply_transforms(
        [{k: v for k, v in row.items() if k in permitted} for row in rows],
        transforms=dlp_assessment.required_transforms,
        suppressed_fields=dlp_profile.suppressed_fields,
        masked_fields=dlp_profile.masked_fields,
        pseudonymized_fields=dlp_profile.pseudonymized_fields,
    )
    artifact = build_artifact(
        export_request,
        projection,
        manifest=replace(manifest, permitted_fields=permitted),
        artifact_id=artifact_id,
        at=guard.now,
        policy=policy,
    )
    stores.artifacts.save(artifact)

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(
        ExportState.ARTIFACT_GENERATED, action="generate_export_artifact"
    )
    stores.exports.save(updated)

    event = _rebuilt_artifact_event(artifact, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_artifact",
                target_id=artifact_id,
                reason_code=RC_ARTIFACT_GENERATED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=artifact_id,
        clock=clock,
    )
    return ArtifactResult(artifact=artifact, event=event, audit_event=audit_event)


def _rebuilt_artifact_event(artifact: ExportArtifact, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="export_artifact.generated",
        aggregate_id=artifact.artifact_id,
        payload=privileged_events.artifact_generated_payload(
            artifact_id=artifact.artifact_id,
            export_id=artifact.export_id,
            manifest_digest=artifact.manifest.digest(),
            expires_at=artifact.expires_at.isoformat(),
            item_count=len(artifact.manifest.items),
        ),
    )


def deliver_export_artifact(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    artifact_id: UUID,
    reason: ReasonCoded,
) -> ArtifactResult:
    """Record delivery to the approved recipient.

    Delivery is recorded, not performed: the transfer channel and the
    external gateway are PACK-14's. What this command establishes is the
    governed fact that delivery happened, against which the recipient's
    obligations and the destruction attestation are later measured."""
    artifact, export_request = _load_artifact(stores, artifact_id, context.require_scope())
    guard = _guard(
        stores,
        command="deliver_export_artifact",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(artifact_id), reason.reason_code),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        return ArtifactResult(
            artifact=artifact,
            event=_rebuilt_delivery_event(artifact, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    artifact.verify_manifest()
    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(ExportState.DELIVERED, action="deliver_export_artifact")
    stores.exports.save(updated)

    event = _rebuilt_delivery_event(artifact, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_artifact",
                target_id=artifact_id,
                reason_code=RC_ARTIFACT_DELIVERED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=artifact_id,
        clock=clock,
    )
    return ArtifactResult(artifact=artifact, event=event, audit_event=audit_event)


def _rebuilt_delivery_event(artifact: ExportArtifact, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="export_artifact.delivered",
        aggregate_id=artifact.artifact_id,
        payload=privileged_events.artifact_generated_payload(
            artifact_id=artifact.artifact_id,
            export_id=artifact.export_id,
            manifest_digest=artifact.manifest.digest(),
            expires_at=artifact.expires_at.isoformat(),
            item_count=len(artifact.manifest.items),
        ),
    )


def access_export_artifact(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    artifact_id: UUID,
    access_id: UUID,
) -> ArtifactResult:
    """Record one access to a generated artifact (`P12-EXP-011`).

    `assert_accessible` checks revocation, expiry and the access count
    against the policy ceiling before the access is recorded, and the
    count is part of the artifact so the ceiling cannot be reset by
    clearing a log elsewhere."""
    artifact, export_request = _load_artifact(stores, artifact_id, context.require_scope())
    guard = _guard(
        stores,
        command="access_export_artifact",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(artifact_id), str(access_id)),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        return ArtifactResult(
            artifact=artifact,
            event=_rebuilt_access_event(artifact, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    artifact.assert_accessible(at=guard.now, policy=policy)
    updated_artifact = artifact.with_access()
    stores.artifacts.save(updated_artifact)
    stores.export_access.record(
        ExportAccessEvent(
            access_id=access_id,
            artifact_id=artifact_id,
            accessor_reference=guard.authority.actor_reference,
            accessed_at=guard.now,
        )
    )

    event = _rebuilt_access_event(updated_artifact, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_artifact",
                target_id=artifact_id,
                reason_code=RC_ARTIFACT_ACCESSED,
            ),
        ),
        aggregate_id=artifact_id,
        clock=clock,
    )
    return ArtifactResult(artifact=updated_artifact, event=event, audit_event=audit_event)


def _rebuilt_access_event(artifact: ExportArtifact, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="export_artifact.accessed",
        aggregate_id=artifact.artifact_id,
        payload=privileged_events.artifact_access_payload(
            artifact_id=artifact.artifact_id,
            accessor_reference=guard.authority.actor_reference,
            access_count=artifact.access_count,
            accessed_at=guard.now.isoformat(),
        ),
    )


def expire_export_artifact(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    artifact_id: UUID,
    reason: ReasonCoded,
) -> ArtifactResult:
    """Expire an artifact at the end of its access window."""
    artifact, export_request = _load_artifact(stores, artifact_id, context.require_scope())
    guard = _guard(
        stores,
        command="expire_export_artifact",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(artifact_id), reason.reason_code),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        return ArtifactResult(
            artifact=artifact,
            event=_rebuilt_expiry_event(artifact, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(ExportState.EXPIRED, action="expire_export_artifact")
    stores.exports.save(updated)

    event = _rebuilt_expiry_event(artifact, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_artifact",
                target_id=artifact_id,
                reason_code=RC_ARTIFACT_EXPIRED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=artifact_id,
        clock=clock,
    )
    return ArtifactResult(artifact=artifact, event=event, audit_event=audit_event)


def _rebuilt_expiry_event(artifact: ExportArtifact, guard: _CommandGuard) -> EventEnvelope:
    return _event(
        guard,
        event_type="export_artifact.expired",
        aggregate_id=artifact.artifact_id,
        payload=privileged_events.artifact_generated_payload(
            artifact_id=artifact.artifact_id,
            export_id=artifact.export_id,
            manifest_digest=artifact.manifest.digest(),
            expires_at=artifact.expires_at.isoformat(),
            item_count=len(artifact.manifest.items),
        ),
    )


def revoke_data_export(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    export_id: UUID,
    artifact_id: UUID | None,
    reason: ReasonCoded,
) -> ExportRequestResult:
    """Withdraw an export authorization (`P12-EXP-013`).

    Revocation blocks further platform-mediated access to the artifact.
    It does **not** delete a copy already delivered, and nothing in this
    command, its event or its audit row says otherwise. Claiming
    retrieval of a delivered copy would be a claim this platform cannot
    make good on; the honest control is the recipient obligation and the
    destruction attestation, and both are recorded as what they are."""
    export_request = _load_export(stores, export_id, context.require_scope())
    guard = _guard(
        stores,
        command="revoke_data_export",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), reason.reason_code),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        return _replayed_export(stores, guard, "data_export.revoked")

    if artifact_id is not None:
        artifact = stores.artifacts.get(artifact_id)
        if artifact is not None:
            stores.artifacts.save(artifact.with_revocation())

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(ExportState.REVOKED, action="revoke_data_export")
    stores.exports.save(updated)

    event = _event(
        guard,
        event_type="data_export.revoked",
        aggregate_id=export_id,
        payload=privileged_events.export_revoked_payload(
            export_id=export_id,
            revoking_authority=str(guard.authority.authority_id),
            reason_code=reason.reason_code,
        ),
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_EXPORT_REVOKED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return ExportRequestResult(request=updated, event=event, audit_event=audit_event)


def attest_export_destruction(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    export_id: UUID,
    attestation_id: UUID,
    attesting_party: str,
    attestation_reference: str,
) -> AttestationResult:
    """Record a recipient's attestation that a delivered copy was
    destroyed (`P12-EXP-015`).

    An **attestation**, not a verified fact, and the naming is the
    control: this platform cannot observe a third party's storage, and a
    field called `destroyed` would assert something nobody checked."""
    export_request = _load_export(stores, export_id, context.require_scope())
    guard = _guard(
        stores,
        command="attest_export_destruction",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(export_id), str(attestation_id), attesting_party),
        target_scope=export_request.scope.organization_scope,
    )
    if guard.replay is not None:
        stored_attestation = stores.attestations.get_for_export(export_id)
        if stored_attestation is None:  # pragma: no cover - defensive
            _raise_not_found("destruction attestation", attestation_id)
            raise AssertionError  # pragma: no cover
        return AttestationResult(
            attestation=stored_attestation,
            event=_rebuilt_attestation_event(stored_attestation, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    attestation = ExportDestructionAttestation(
        attestation_id=attestation_id,
        export_id=export_id,
        attesting_party=attesting_party,
        attested_at=guard.now,
        attestation_reference=attestation_reference,
    )
    stores.attestations.save(attestation)

    before_hash = _state_hash(export_request.to_state_payload())
    updated = export_request.with_state(
        ExportState.DESTRUCTION_ATTESTED, action="attest_export_destruction"
    )
    stores.exports.save(updated)

    event = _rebuilt_attestation_event(attestation, guard)
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="export_request",
                target_id=export_id,
                reason_code=RC_DESTRUCTION_ATTESTED,
                before_hash=before_hash,
                after_hash=_state_hash(updated.to_state_payload()),
            ),
        ),
        aggregate_id=export_id,
        clock=clock,
    )
    return AttestationResult(attestation=attestation, event=event, audit_event=audit_event)


def _rebuilt_attestation_event(
    attestation: ExportDestructionAttestation, guard: _CommandGuard
) -> EventEnvelope:
    return _event(
        guard,
        event_type="data_export.destruction_attested",
        aggregate_id=attestation.export_id,
        payload=privileged_events.destruction_attested_payload(
            export_id=attestation.export_id,
            attesting_party=attestation.attesting_party,
            attestation_reference=attestation.attestation_reference,
            attested_at=attestation.attested_at.isoformat(),
        ),
    )


def _replayed_export(
    stores: PrivilegedStores, guard: _CommandGuard, event_type: str
) -> ExportRequestResult:
    stored = stores.exports.get(guard.replay.aggregate_id) if guard.replay else None
    if stored is None:  # pragma: no cover - defensive
        _raise_not_found("export request", guard.event_id)
        raise AssertionError  # pragma: no cover
    if event_type == "data_export.requested":
        payload = privileged_events.export_requested_payload(
            export_id=stored.export_id,
            purpose=str(stored.purpose.purpose),
            domains=stored.scope.domains,
            record_classes=stored.scope.record_classes,
            recipient_category=str(stored.recipient.category),
            requested_format=stored.requested_format,
        )
    elif event_type == "data_export.revoked":
        payload = privileged_events.export_revoked_payload(
            export_id=stored.export_id,
            revoking_authority=str(guard.authority.authority_id),
            reason_code="",
        )
    else:
        payload = privileged_events.export_decision_payload(
            export_id=stored.export_id,
            approver_reference=stored.approver_reference,
            reason_code="",
            permitted_field_digest="",
        )
    return ExportRequestResult(
        request=stored,
        event=_event(guard, event_type=event_type, aggregate_id=stored.export_id, payload=payload),
        audit_event=_replayed_audit(stores, guard),
    )


# ---------------------------------------------------------------------------
# Commands: statistical disclosure control
# ---------------------------------------------------------------------------


def assess_disclosure_risk(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    policy: PrivilegedAccessPolicy,
    assessment_id: UUID,
    release_class: str,
    cohort_policy: CohortPolicy,
    cohorts: Sequence[CohortObservation],
    total_population: int,
    suppression: SuppressionDecision | None,
    release_history_reference: str,
    requester_reference: str,
) -> DisclosureAssessmentResult:
    """Assess the disclosure risk of a proposed release (`P12-SDC-001`).

    Four rule families run, never fewer than two
    (`CohortPolicy` refuses a policy with fewer): cohort threshold,
    complement protection, differencing across this requester's recent
    query digests, and cumulative release across the policy window. A
    single small-cell check is the rule everyone implements and the one
    that alone protects least - a complement of a suppressed cell, or the
    difference between two permitted releases, recovers exactly what the
    threshold was meant to withhold.

    The cumulative model is bounded, not open-ended (`OD-P12-08`): a
    window, a limit, and a history that must be **available**. If the
    release history cannot be read, `ReleaseHistory.assert_available`
    fails closed. An unbounded "all releases ever" model would be
    unimplementable and would therefore quietly become no model at all.

    Where the assessment requires suppression, a
    `disclosure_control.suppression_applied` event is emitted alongside
    the assessment; where the cumulative rule fails, a
    `cumulative_risk_flagged` event is emitted too. Both are governed
    facts in their own right."""
    guard = _guard(
        stores,
        command="assess_disclosure_risk",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(assessment_id), release_class),
        prior_actor_references=(requester_reference,),
    )
    if guard.replay is not None:
        stored = stores.disclosure_assessments.get(assessment_id)
        if stored is None:  # pragma: no cover - defensive
            _raise_not_found("disclosure risk assessment", assessment_id)
            raise AssertionError  # pragma: no cover
        return DisclosureAssessmentResult(
            assessment=stored,
            event=_rebuilt_disclosure_event(stored, guard),
            audit_event=_replayed_audit(stores, guard),
        )

    history = stores.release_history.window(
        scope=guard.scope,
        start=guard.now - policy.cumulative_release_window,
        end=guard.now,
    )
    history.assert_available()
    suppressed_keys = suppression.suppressed_cohorts if suppression else frozenset()
    rules: tuple[DisclosureRule, ...] = (
        evaluate_cohort_threshold(cohorts, cohort_policy),
        evaluate_complement_protection(
            cohorts,
            total=total_population,
            cohort_policy=cohort_policy,
            suppressed=suppressed_keys,
        ),
        evaluate_differencing(
            similar_query_digests=stores.query_audit.similar_digests(
                scope=guard.scope,
                requester_reference=requester_reference,
                digest_prefix=deterministic_digest(release_class)[:8],
            ),
            policy=policy,
        ),
        evaluate_cumulative(
            cohorts=cohorts,
            release_class=release_class,
            history=history,
            policy=policy,
        ),
    )
    assessment = DisclosureRiskAssessment(
        assessment_id=assessment_id,
        organization_scope=guard.scope,
        release_class=release_class,
        assessed_at=guard.now,
        reviewer_reference=guard.authority.actor_reference,
        rules=rules,
        suppression=suppression,
        release_history_reference=release_history_reference,
        policy_version=cohort_policy.policy_version,
    )
    stores.disclosure_assessments.save(assessment)
    assert_suppression_applied(cohorts, cohort_policy=cohort_policy, suppression=suppression)

    event = _rebuilt_disclosure_event(assessment, guard)
    emissions = [
        _Emission(
            event=event,
            target_type="disclosure_assessment",
            target_id=assessment_id,
            reason_code=RC_DISCLOSURE_ASSESSED,
            after_hash=_state_hash(assessment.to_state_payload()),
        )
    ]
    if suppression is not None:
        emissions.append(
            _Emission(
                event=_event(
                    guard,
                    event_type="disclosure_control.suppression_applied",
                    aggregate_id=assessment_id,
                    payload=privileged_events.suppression_applied_payload(
                        decision_id=suppression.decision_id,
                        suppressed_count=len(suppression.suppressed_cohorts),
                        rule_reference=suppression.rule_reference,
                    ),
                ),
                target_type="disclosure_assessment",
                target_id=assessment_id,
                reason_code=RC_DISCLOSURE_SUPPRESSED,
            )
        )
    cumulative = next((r for r in rules if str(r.family) == "cumulative"), None)
    if cumulative is not None and not cumulative.passed:
        emissions.append(
            _Emission(
                event=_event(
                    guard,
                    event_type="disclosure_control.cumulative_risk_flagged",
                    aggregate_id=assessment_id,
                    payload=privileged_events.cumulative_risk_payload(
                        assessment_id=assessment_id,
                        release_history_reference=release_history_reference,
                        rule_reference=cumulative.detail_reference,
                    ),
                ),
                target_type="disclosure_assessment",
                target_id=assessment_id,
                reason_code=RC_DISCLOSURE_CUMULATIVE_FLAGGED,
            )
        )

    audit_event = _finish(stores, guard, emissions, aggregate_id=assessment_id, clock=clock)
    return DisclosureAssessmentResult(assessment=assessment, event=event, audit_event=audit_event)


def _rebuilt_disclosure_event(
    assessment: DisclosureRiskAssessment, guard: _CommandGuard
) -> EventEnvelope:
    return _event(
        guard,
        event_type="disclosure_control.risk_assessed",
        aggregate_id=assessment.assessment_id,
        payload=privileged_events.disclosure_assessed_payload(
            assessment_id=assessment.assessment_id,
            release_class=assessment.release_class,
            outcome="passed" if assessment.passed else "failed",
            rule_families=tuple(str(r.family) for r in assessment.rules),
            policy_version=assessment.policy_version,
        ),
    )


def request_disclosure_exception(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    exception_id: UUID,
    release_class: str,
    justification_reference: str,
) -> DisclosureExceptionResult:
    """Ask for a bounded exception to a disclosure rule
    (`P12-SDC-008`)."""
    guard = _guard(
        stores,
        command="request_disclosure_exception",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(exception_id), release_class),
    )
    exception_request = DisclosureExceptionRequest(
        exception_id=exception_id,
        release_class=release_class,
        requester_reference=guard.authority.actor_reference,
        justification_reference=justification_reference,
        requested_at=guard.now,
    )
    event = _event(
        guard,
        event_type="disclosure_control.exception_requested",
        aggregate_id=exception_id,
        payload=privileged_events.disclosure_exception_payload(
            exception_id=exception_id,
            reviewer_reference="",
            approved=False,
            reason_code=RC_DISCLOSURE_EXCEPTION_REQUESTED,
        ),
    )
    if guard.replay is not None:
        return DisclosureExceptionResult(
            request=exception_request,
            decision=None,
            event=event,
            audit_event=_replayed_audit(stores, guard),
        )

    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="disclosure_assessment",
                target_id=exception_id,
                reason_code=RC_DISCLOSURE_EXCEPTION_REQUESTED,
            ),
        ),
        aggregate_id=exception_id,
        clock=clock,
    )
    return DisclosureExceptionResult(
        request=exception_request, decision=None, event=event, audit_event=audit_event
    )


def decide_disclosure_exception(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    exception_request: DisclosureExceptionRequest,
    decision_id: UUID,
    approved: bool,
    valid_until: datetime,
    reason: ReasonCoded,
    bounded_conditions: frozenset[str] = frozenset(),
    assessment_id: UUID | None = None,
    cohort_policy: CohortPolicy | None = None,
) -> DisclosureExceptionResult:
    """Decide a disclosure exception - bounded, expiring, reviewed.

    The requester may not decide their own exception
    (`P12-SDC-006`), the decision carries an expiry it cannot be built
    without, and where an assessment and cohort policy are supplied the
    decision is immediately tested through `assert_release_permitted`, so
    an approval that would still not permit the release fails here rather
    than at release time."""
    guard = _guard(
        stores,
        command="decide_disclosure_exception",
        context=context,
        port=port,
        clock=clock,
        request_parts=(str(exception_request.exception_id), str(decision_id), str(approved)),
        prior_actor_references=(exception_request.requester_reference,),
    )
    decision = DisclosureExceptionDecision(
        decision_id=decision_id,
        exception_id=exception_request.exception_id,
        reviewer_reference=guard.authority.actor_reference,
        approved=approved,
        decided_at=guard.now,
        valid_until=valid_until,
        reason=reason,
        bounded_conditions=bounded_conditions,
    )
    event_type = (
        "disclosure_control.exception_approved"
        if approved
        else "disclosure_control.exception_denied"
    )
    event = _event(
        guard,
        event_type=event_type,
        aggregate_id=exception_request.exception_id,
        payload=privileged_events.disclosure_exception_payload(
            exception_id=exception_request.exception_id,
            reviewer_reference=guard.authority.actor_reference,
            approved=approved,
            reason_code=reason.reason_code,
        ),
    )
    if guard.replay is not None:
        return DisclosureExceptionResult(
            request=exception_request,
            decision=decision,
            event=event,
            audit_event=_replayed_audit(stores, guard),
        )

    if approved and assessment_id is not None and cohort_policy is not None:
        assessment = stores.disclosure_assessments.get(assessment_id)
        if assessment is None:
            _raise_not_found("disclosure risk assessment", assessment_id)
            raise AssertionError  # pragma: no cover
        assert_release_permitted(
            assessment,
            cohort_policy=cohort_policy,
            exception=decision,
            exception_request=exception_request,
            at=guard.now,
        )

    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="disclosure_assessment",
                target_id=exception_request.exception_id,
                reason_code=RC_DISCLOSURE_EXCEPTION_DECIDED,
            ),
        ),
        aggregate_id=exception_request.exception_id,
        clock=clock,
    )
    return DisclosureExceptionResult(
        request=exception_request, decision=decision, event=event, audit_event=audit_event
    )


def observe_governed_publication(
    stores: PrivilegedStores,
    *,
    context: RequestContext,
    port: AuthorizationPort,
    clock: Clock,
    observation_id: UUID,
    publication_reference: str,
    certification_reference: str,
    publication_decision_reference: str,
    release_class: str,
    cohort_keys: frozenset[str],
    cohort_dimensions: frozenset[str],
) -> PublicationObservationResult:
    """Record that a governed publication happened **elsewhere**
    (`P12-VOTE-005`).

    PACK-12 does not certify a result, does not decide closure and does
    not publish. This command records three references and no content,
    and it exists so the cumulative-release model can count a publication
    it did not make. An event of this type is never evidence that PACK-12
    released anything."""
    guard = _guard(
        stores,
        command="observe_governed_publication",
        context=context,
        port=port,
        clock=clock,
        request_parts=(publication_reference, certification_reference),
    )
    event = _event(
        guard,
        event_type="disclosure_control.governed_publication_observed",
        aggregate_id=observation_id,
        payload=privileged_events.governed_publication_observed_payload(
            publication_reference=publication_reference,
            certification_reference=certification_reference,
            publication_decision_reference=publication_decision_reference,
        ),
    )
    if guard.replay is not None:
        return PublicationObservationResult(
            publication_reference=publication_reference,
            event=event,
            audit_event=_replayed_audit(stores, guard),
        )

    stores.release_history.record(
        ReleaseHistoryEntry(
            release_id=observation_id,
            organization_scope=guard.scope,
            release_class=release_class,
            cohort_dimensions=cohort_dimensions,
            cohort_keys=cohort_keys,
            released_at=guard.now,
            release_reference=publication_reference,
        )
    )
    audit_event = _finish(
        stores,
        guard,
        (
            _Emission(
                event=event,
                target_type="disclosure_assessment",
                target_id=observation_id,
                reason_code=RC_PUBLICATION_OBSERVED,
            ),
        ),
        aggregate_id=observation_id,
        clock=clock,
    )
    return PublicationObservationResult(
        publication_reference=publication_reference,
        event=event,
        audit_event=audit_event,
    )

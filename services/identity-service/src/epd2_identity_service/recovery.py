"""Account recovery - where strong authentication is actually defeated.

Every control in this module answers a specific attack:

- **Old credentials and all sessions are revoked *before* completion.** A
  recovery that leaves the attacker logged in has recovered nothing, so
  `complete_recovery` refuses without both revocation facts recorded.
- **No reviewer approves their own case.** Insider reset and support
  impersonation are first-class threats, and `record_decision` refuses
  when the reviewer initiated the case or is its subject.
- **High-assurance recovery requires dual control, cooling-off and
  out-of-band notification - all three**, not a choice among them: each
  closes a different attack (collusion, speed, and the legitimate holder
  not knowing).
- **A recently changed contact may not be the channel.**
  Contact-change-then-recover is a two-step takeover.
- **No security questions and no publicly discoverable facts.** For
  candidates and office-holders the answers are campaign material.

The assurance rule is the one the architecture correction restated
(OD-P14-10). Recovery necessarily uses *different* evidence from the
credential that was lost - demanding the same evidence would mean
demanding the lost credential. So the rule is about **resulting
confidence**: it must be equivalent, or the shortfall must carry an
explicit, reason-coded risk acceptance by a named authority. Without one,
recovery silently becomes the account's real assurance level.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.assurance import assurance_rank
from epd2_identity_service.domain import AuthenticationAssuranceLevel
from epd2_identity_service.exceptions import (
    AlternateVerificationFailedError,
    ForbiddenRecoveryTransitionError,
    RecoveryAlreadyCompletedError,
    RecoveryContactRecentlyChangedError,
    RecoveryCoolingOffActiveError,
    RecoveryCredentialsNotRevokedError,
    RecoveryDualControlRequiredError,
    RecoveryElevationRefusedError,
    RecoveryEvidenceMissingError,
    RecoveryRiskAcceptanceRequiredError,
    RecoveryRiskTooHighError,
    RecoverySelfApprovalRefusedError,
    UnknownRecoveryStatedReasonError,
    UnknownRecoveryStateError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    ScopedIdentityReference,
    require_timezone,
)


class RecoveryState(StrEnum):
    """The governed workflow, exactly as the task enumerates it."""

    REQUESTED = "requested"
    ASSESSING = "assessing"
    EVIDENCE_PENDING = "evidence_pending"
    COOLING_OFF = "cooling_off"
    APPROVED = "approved"
    REJECTED = "rejected"
    CREDENTIAL_REPLACEMENT_PENDING = "credential_replacement_pending"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


def parse_recovery_state(value: str) -> RecoveryState:
    try:
        return RecoveryState(value)
    except ValueError as exc:
        raise UnknownRecoveryStateError(f"unknown recovery state: {value!r}") from exc


_ALLOWED_RECOVERY_TRANSITIONS: frozenset[tuple[RecoveryState, RecoveryState]] = frozenset(
    {
        (RecoveryState.REQUESTED, RecoveryState.ASSESSING),
        (RecoveryState.REQUESTED, RecoveryState.CANCELLED),
        (RecoveryState.ASSESSING, RecoveryState.EVIDENCE_PENDING),
        (RecoveryState.ASSESSING, RecoveryState.COOLING_OFF),
        (RecoveryState.ASSESSING, RecoveryState.REJECTED),
        (RecoveryState.ASSESSING, RecoveryState.CANCELLED),
        (RecoveryState.EVIDENCE_PENDING, RecoveryState.ASSESSING),
        (RecoveryState.EVIDENCE_PENDING, RecoveryState.REJECTED),
        (RecoveryState.EVIDENCE_PENDING, RecoveryState.CANCELLED),
        (RecoveryState.COOLING_OFF, RecoveryState.APPROVED),
        (RecoveryState.COOLING_OFF, RecoveryState.REJECTED),
        (RecoveryState.COOLING_OFF, RecoveryState.CANCELLED),
        (RecoveryState.COOLING_OFF, RecoveryState.DISPUTED),
        (RecoveryState.APPROVED, RecoveryState.CREDENTIAL_REPLACEMENT_PENDING),
        (RecoveryState.APPROVED, RecoveryState.DISPUTED),
        (RecoveryState.CREDENTIAL_REPLACEMENT_PENDING, RecoveryState.COMPLETED),
        (RecoveryState.CREDENTIAL_REPLACEMENT_PENDING, RecoveryState.DISPUTED),
        (RecoveryState.COMPLETED, RecoveryState.DISPUTED),
        (RecoveryState.REJECTED, RecoveryState.DISPUTED),
    }
)


class StatedRecoveryReason(StrEnum):
    """What the person says happened. Free text may accompany it and is
    never the reason code."""

    DEVICE_LOST = "device_lost"
    DEVICE_STOLEN = "device_stolen"
    CREDENTIAL_LOST = "credential_lost"
    CHANNEL_LOST = "channel_lost"
    OTHER = "other"


def parse_stated_reason(value: str) -> StatedRecoveryReason:
    try:
        return StatedRecoveryReason(value)
    except ValueError as exc:
        raise UnknownRecoveryStatedReasonError(
            f"unknown stated recovery reason: {value!r}"
        ) from exc


class RecoveryRiskClassification(StrEnum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    REFUSED = "refused"


#: The fraud indicators the recovery control matrix §3 names. Each raises
#: the required assurance, extends cooling-off or routes to manual review
#: - and each is named, so a denial can be explained.
FRAUD_INDICATORS: frozenset[str] = frozenset(
    {
        "new_device_new_location_immediate_credential_change",
        "requested_within_contact_change_notification_window",
        "repeated_partial_recoveries",
        "account_holds_privileged_grant",
        "requested_during_active_ballot_window",
        "assisted_recovery_helper_is_requester",
    }
)


@dataclass(frozen=True, slots=True)
class RecoveryEvidenceReference:
    """A PACK-11 bundle reference. Never the evidence content.

    Immutable by construction: there is no method that changes a field,
    and a correction is a new reference rather than an edit - the pattern
    PACK-11 established for governed documents.
    """

    evidence_reference_id: UUID
    bundle_reference: str
    evidence_class: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, "recorded_at")
        if not self.bundle_reference:
            raise RecoveryEvidenceMissingError("an evidence reference names a PACK-11 bundle")


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    """Named signals, never a bare score."""

    assessed_at: datetime
    classification: RecoveryRiskClassification
    named_signals: tuple[str, ...]
    required_assurance: AuthenticationAssuranceLevel
    cooling_off: timedelta
    dual_control_required: bool

    def __post_init__(self) -> None:
        require_timezone(self.assessed_at, "assessed_at")
        if self.classification is not RecoveryRiskClassification.LOW and not self.named_signals:
            raise ValueError("a non-low classification names its signals")
        if self.dual_control_required and self.cooling_off <= timedelta(0):
            raise ValueError(
                "high-assurance recovery requires dual control AND a cooling-off period"
            )


@dataclass(frozen=True, slots=True)
class RecoveryRiskAcceptance:
    """An explicit, reason-coded acceptance of a confidence shortfall by a
    named authority (OD-P14-10)."""

    authority_reference: str
    reason_code: str
    accepted_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.accepted_at, "accepted_at")
        if not self.authority_reference or not self.reason_code:
            raise RecoveryRiskAcceptanceRequiredError(
                "a risk acceptance names an authority and carries a registered reason code"
            )


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    """Who decided, with what evidence, and with which second approver."""

    decided_at: datetime
    reviewer_reference: ScopedIdentityReference
    approved: bool
    reason_code: str
    second_approver_reference: ScopedIdentityReference | None
    grant_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, "decided_at")
        if not self.reason_code:
            raise ValueError("a recovery decision carries a registered reason code")
        if not self.grant_reference:
            raise ValueError("a recovery decision names the PACK-12 grant it acted under")


@dataclass(frozen=True, slots=True)
class RecoveryDispute:
    dispute_id: UUID
    raised_at: datetime
    reason_code: str
    appeal_path_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.raised_at, "raised_at")


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    """The case.

    `emergency` matters at the end rather than at the start: emergency
    recovery restores access and does **not** immediately authorize
    high-risk actions - elevated capability returns only once the normal
    assurance path is satisfied.
    """

    recovery_id: UUID
    account_id: AccountId
    requester_reference: ScopedIdentityReference
    state: RecoveryState
    stated_reason: StatedRecoveryReason
    entry_channel_class: str
    requested_at: datetime
    assisted_by: ScopedIdentityReference | None = None
    emergency: bool = False
    assessment: RecoveryAssessment | None = None
    cooling_off_ends_at: datetime | None = None
    evidence: tuple[RecoveryEvidenceReference, ...] = ()
    decision: RecoveryDecision | None = None
    risk_acceptance: RecoveryRiskAcceptance | None = None
    credentials_revoked: bool = False
    sessions_revoked: bool = False
    out_of_band_notified: bool = False
    dispute: RecoveryDispute | None = None
    replacement_assurance: AuthenticationAssuranceLevel | None = None
    version: int = 1

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, "requested_at")
        if self.cooling_off_ends_at is not None:
            require_timezone(self.cooling_off_ends_at, "cooling_off_ends_at")

    def transitioned(self, target: RecoveryState) -> RecoveryRequest:
        if (self.state, target) not in _ALLOWED_RECOVERY_TRANSITIONS:
            raise ForbiddenRecoveryTransitionError(
                f"recovery transition {self.state.value!r} -> {target.value!r} is not allowed"
            )
        return replace(self, state=target, version=self.version + 1)


def open_recovery(
    *,
    recovery_id: UUID,
    account_id: AccountId,
    requester_reference: ScopedIdentityReference,
    stated_reason: StatedRecoveryReason,
    entry_channel_class: str,
    entry_channel_changed_at: datetime | None,
    requested_at: datetime,
    contact_protective_window: timedelta,
    assisted_by: ScopedIdentityReference | None = None,
    emergency: bool = False,
) -> RecoveryRequest:
    """Open a case, refusing a channel that was changed too recently.

    This is the first control and the cheapest one: an attacker who has
    just changed the address cannot immediately use it to recover.
    """
    moment = require_timezone(requested_at, "requested_at")
    if entry_channel_changed_at is not None:
        changed = require_timezone(entry_channel_changed_at, "entry_channel_changed_at")
        if moment < changed + contact_protective_window:
            raise RecoveryContactRecentlyChangedError(
                "the offered channel was changed too recently to rely on for recovery"
            )
    return RecoveryRequest(
        recovery_id=recovery_id,
        account_id=account_id,
        requester_reference=requester_reference,
        state=RecoveryState.REQUESTED,
        stated_reason=stated_reason,
        entry_channel_class=entry_channel_class,
        requested_at=moment,
        assisted_by=assisted_by,
        emergency=emergency,
    )


def record_assessment(
    request: RecoveryRequest, *, assessment: RecoveryAssessment
) -> RecoveryRequest:
    """Record the risk assessment and enter the next state.

    A `REFUSED` classification ends the case with
    `RECOVERY_RISK_TOO_HIGH` rather than silently continuing at a higher
    bar, because a refusal a person is never told about is a refusal they
    cannot appeal.
    """
    assessing = request.transitioned(RecoveryState.ASSESSING)
    if assessment.classification is RecoveryRiskClassification.REFUSED:
        raise RecoveryRiskTooHighError(
            f"the risk assessment refused this recovery on: {', '.join(assessment.named_signals)}"
        )
    with_assessment = replace(assessing, assessment=assessment)
    if assessment.cooling_off > timedelta(0):
        cooling = with_assessment.transitioned(RecoveryState.COOLING_OFF)
        return replace(cooling, cooling_off_ends_at=assessment.assessed_at + assessment.cooling_off)
    return with_assessment.transitioned(RecoveryState.EVIDENCE_PENDING)


def attach_evidence(
    request: RecoveryRequest, *, evidence: RecoveryEvidenceReference
) -> RecoveryRequest:
    return replace(request, evidence=(*request.evidence, evidence), version=request.version + 1)


def verify_alternate_method(
    request: RecoveryRequest, *, method_independent_of_lost_credential: bool, verified: bool
) -> RecoveryRequest:
    """The alternate verification must be **independent** of what was
    lost.

    Verifying with the credential the person says they lost proves
    nothing about them and everything about whoever has it.
    """
    if not method_independent_of_lost_credential:
        raise AlternateVerificationFailedError(
            "the verification method must be independent of the credential that was lost"
        )
    if not verified:
        raise AlternateVerificationFailedError("the independent verification method failed")
    return replace(request, version=request.version + 1)


def record_decision(
    request: RecoveryRequest,
    *,
    decision: RecoveryDecision,
    now: datetime,
) -> RecoveryRequest:
    """Approve or reject, under separation of duties and dual control.

    Three refusals in order: cooling-off not elapsed, self-approval, dual
    control missing. Self-approval is checked against both the initiator
    and the subject, because a reviewer recovering their own account and
    a reviewer approving a case they opened are the same failure wearing
    two hats.
    """
    moment = require_timezone(now, "now")
    if request.state is RecoveryState.COMPLETED:
        raise RecoveryAlreadyCompletedError("this recovery case is already complete")
    if request.cooling_off_ends_at is not None and moment < request.cooling_off_ends_at:
        raise RecoveryCoolingOffActiveError("the cooling-off window has not elapsed")
    if decision.reviewer_reference == request.requester_reference:
        raise RecoverySelfApprovalRefusedError(
            "the reviewer initiated this case and may not decide it"
        )
    if request.assisted_by is not None and decision.reviewer_reference == request.assisted_by:
        raise RecoverySelfApprovalRefusedError(
            "the reviewer assisted this request and may not decide it"
        )
    assessment = request.assessment
    if (
        decision.approved
        and assessment is not None
        and assessment.dual_control_required
        and decision.second_approver_reference is None
    ):
        raise RecoveryDualControlRequiredError("high-assurance recovery requires a second approver")
    if decision.second_approver_reference == decision.reviewer_reference:
        raise RecoveryDualControlRequiredError(
            "the second approver must be a different person from the reviewer"
        )
    target = RecoveryState.APPROVED if decision.approved else RecoveryState.REJECTED
    return replace(request.transitioned(target), decision=decision)


def begin_credential_replacement(
    request: RecoveryRequest,
    *,
    credentials_revoked: bool,
    sessions_revoked: bool,
) -> RecoveryRequest:
    """Revocation happens **here**, before replacement, never after."""
    if not credentials_revoked or not sessions_revoked:
        raise RecoveryCredentialsNotRevokedError(
            "old credentials and every session are revoked before credential replacement begins"
        )
    return replace(
        request.transitioned(RecoveryState.CREDENTIAL_REPLACEMENT_PENDING),
        credentials_revoked=True,
        sessions_revoked=True,
    )


def complete_recovery(
    request: RecoveryRequest,
    *,
    replacement_assurance: AuthenticationAssuranceLevel,
    replaced_assurance: AuthenticationAssuranceLevel,
    out_of_band_notified: bool,
    risk_acceptance: RecoveryRiskAcceptance | None,
) -> RecoveryRequest:
    """Complete, enforcing the resulting-confidence rule.

    If the replacement credential's assurance is below what it replaces,
    completion requires an explicit reason-coded risk acceptance by a
    named authority. Without that, the account's real assurance level
    silently becomes whatever recovery happens to grant - which is the
    failure OD-P14-10's restatement was written to prevent.
    """
    if not request.credentials_revoked or not request.sessions_revoked:
        raise RecoveryCredentialsNotRevokedError(
            "completion is refused until old credentials and sessions are revoked"
        )
    if not out_of_band_notified:
        raise RecoveryEvidenceMissingError(
            "out-of-band notification to every verified channel is part of completion"
        )
    if not request.evidence:
        raise RecoveryEvidenceMissingError(
            "a completed recovery carries at least one immutable evidence reference"
        )
    if assurance_rank(replacement_assurance) < assurance_rank(replaced_assurance) and (
        risk_acceptance is None
    ):
        raise RecoveryRiskAcceptanceRequiredError(
            f"the resulting confidence ({replacement_assurance.value}) is below what it "
            f"replaces ({replaced_assurance.value}); an explicit reason-coded risk "
            "acceptance by a named authority is required"
        )
    return replace(
        request.transitioned(RecoveryState.COMPLETED),
        replacement_assurance=replacement_assurance,
        out_of_band_notified=True,
        risk_acceptance=risk_acceptance,
    )


def assert_emergency_recovery_cannot_elevate(
    request: RecoveryRequest, *, required_assurance: AuthenticationAssuranceLevel
) -> None:
    """Emergency recovery restores access; it does not confer authority.

    A high-risk action attempted straight after an emergency recovery is
    refused until the normal assurance path has been satisfied - which
    is what stops emergency recovery from becoming the fast route to a
    privileged act.
    """
    if not request.emergency:
        return
    if request.state is not RecoveryState.COMPLETED:
        return
    if required_assurance is AuthenticationAssuranceLevel.HIGH:
        raise RecoveryElevationRefusedError(
            "emergency recovery restores access and does not immediately authorize "
            "high-risk actions"
        )


def raise_dispute(request: RecoveryRequest, *, dispute: RecoveryDispute) -> RecoveryRequest:
    """ "I did not request this" must lead somewhere."""
    return replace(request.transitioned(RecoveryState.DISPUTED), dispute=dispute)

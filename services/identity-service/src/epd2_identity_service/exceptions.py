"""Identity Service exceptions, tied to stable reason codes."""

from __future__ import annotations


class UnknownVerificationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class ForbiddenVerificationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class UnknownIdentityRecordError(ValueError):
    """Raised for a plain lookup miss (no `IdentityRecord` exists for the
    given `identity_record_id`) - distinct from `IDENTITY_NOT_VERIFIED`,
    which describes a record that exists but has not passed verification
    (see ADR-004)."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- PACK-07 additions (canon 19d.2 / 19d.8, canon-0.6.0) -------------------
# Reuses the same generic `VALIDATION_UNKNOWN_STATUS` code
# `UnknownVerificationStatusError` already uses, mirroring
# `UnknownModerationDecisionTypeError`'s precedent for a non-status enum
# that still needs CT-00-02 fail-closed parsing — no new reason code is
# registered for either of these.


class UnknownIdentityAssuranceLevelError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAuthenticationAssuranceLevelError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAuthenticationContextError(ValueError):
    """Plain lookup miss - no `AuthenticationContext` exists for the
    given `authentication_context_id`."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- PACK-14 additions ------------------------------------------------------
#
# Identity, Authentication & Account Security (ADR-079 through ADR-088).
# One class per registered reason code, no domain knowledge, in the same
# shape PACK-13's `data-plane-service` exceptions module established: the
# class names what was refused, the `reason_code` attribute is the
# registered string, and `contracts/reason-codes/pack-14.yml` is the single
# source of truth both are checked against by
# `tests/contract/test_reason_codes_registry.py`.
#
# **There is no generic `AuthenticationError` and no generic `AUTH_ERROR`.**
# PACK-13's `P13-RSN-002` applied to a domain where it matters more: in an
# account-takeover investigation the difference between 'wrong credential'
# and 'credential revoked' is the whole investigation, so they are two
# classes carrying two codes and neither may be widened to cover the other.


# --- Credential registry and passkeys ---------------------------------------


class InvalidCredentialError(ValueError):
    """The presented credential did not verify. Deliberately distinct from
    CREDENTIAL_REVOKED and CREDENTIAL_EXPIRED: in a takeover investigation
    the difference between 'wrong secret' and 'revoked credential' is the
    whole investigation."""

    reason_code = "CREDENTIAL_INVALID"


class CredentialRevokedError(ValueError):
    """The credential exists and has been revoked. It can never verify again; a
    retry is pointless and the correct next step is enrolling a new one."""

    reason_code = "CREDENTIAL_REVOKED"


class CredentialExpiredError(ValueError):
    """The credential exists and is past its validity window."""

    reason_code = "CREDENTIAL_EXPIRED"


class CredentialAlreadyEnrolledError(ValueError):
    """A credential with this reference is already enrolled for the account.
    Re-enrolling would create two records for one authenticator and make
    revocation ambiguous."""

    reason_code = "CREDENTIAL_ALREADY_ENROLLED"


class LastRemainingCredentialError(ValueError):
    """Removal refused: it is the only credential on the account and no
    recovery path exists. Removing it would lock the holder out with no
    governed way back in."""

    reason_code = "CREDENTIAL_LAST_REMAINING"


class PasskeyVerificationFailedError(ValueError):
    """WebAuthn assertion verification failed in the verification adapter.
    Distinct from PASSKEY_ORIGIN_MISMATCH and
    PASSKEY_SIGN_COUNTER_REGRESSION, which name specific structural failures
    an operator must respond to differently."""

    reason_code = "PASSKEY_VERIFICATION_FAILED"


class PasskeyOriginMismatchError(ValueError):
    """The assertion was produced for a different origin than the one the
    ceremony was bound to. This is the phishing signature, not a generic
    verification failure."""

    reason_code = "PASSKEY_ORIGIN_MISMATCH"


class PasskeyChallengeExpiredError(ValueError):
    """The registration or authentication challenge was presented after its
    expiry. Challenges are single-use and short-lived by construction."""

    reason_code = "PASSKEY_CHALLENGE_EXPIRED"


class PasskeySignCounterRegressionError(ValueError):
    """The authenticator reported a signature counter lower than or equal to
    the stored one where the authenticator supports counters. This is the
    cloned-authenticator signal and is treated as a security event, not a
    retryable error."""

    reason_code = "PASSKEY_SIGN_COUNTER_REGRESSION"


class MalformedAuthenticatorResponseError(ValueError):
    """The authenticator response could not be parsed into the fields the
    verification adapter requires. Refused before any verification is
    attempted, so a malformed input never reaches the crypto boundary."""

    reason_code = "PASSKEY_MALFORMED_RESPONSE"


class PasswordLoginDisabledError(ValueError):
    """Password login is disabled for this scope or this account by governed
    configuration (ADR-081, specification section 5.2). The account has
    another path; this one is closed by decision, not by fault."""

    reason_code = "PASSWORD_LOGIN_DISABLED"


class PasswordOnlyAccountRefusedError(ValueError):
    """Creating a new password-only account is refused. A password is a
    fallback for someone who already has one, never the default path for a
    new account (specification section 5.2)."""

    reason_code = "PASSWORD_ONLY_ACCOUNT_REFUSED"


class PasswordPolicyNotMetError(ValueError):
    """The proposed password does not satisfy the governed policy. Never
    reveals which rule failed in a public response."""

    reason_code = "PASSWORD_POLICY_NOT_MET"


class BreachedPasswordRefusedError(ValueError):
    """The breached-password checking boundary reported the proposed password
    as known-compromised. Refused at enrollment, not at login, so the
    refusal discloses nothing about an existing account."""

    reason_code = "PASSWORD_BREACHED"


class SecurityQuestionRefusedError(ValueError):
    """A security question was offered as a credential or as recovery evidence.
    Security questions are prohibited outright: for candidates and office-
    holders the answers are campaign material."""

    reason_code = "SECURITY_QUESTION_REFUSED"


# --- Multi-factor -----------------------------------------------------------


class MfaRequiredError(ValueError):
    """The action requires a second factor that was not presented. Password
    authentication always reaches this code when no factor accompanies it."""

    reason_code = "MFA_REQUIRED"


class MfaFailedError(ValueError):
    """The second factor was presented and did not verify."""

    reason_code = "MFA_FAILED"


class MfaFactorNotEnrolledError(ValueError):
    """No factor of the required class is enrolled on the account."""

    reason_code = "MFA_FACTOR_NOT_ENROLLED"


class MfaFactorRevokedError(ValueError):
    """The factor exists and has been revoked."""

    reason_code = "MFA_FACTOR_REVOKED"


class MfaFactorAlreadyEnrolledError(ValueError):
    """A factor of this class is already enrolled and confirmed; a second
    enrollment of the same class would make removal ambiguous."""

    reason_code = "MFA_FACTOR_ALREADY_ENROLLED"


class MfaFactorNotConfirmedError(ValueError):
    """The factor was enrolled but never confirmed, so it cannot be used to
    authenticate. An unconfirmed factor is a claim, not a credential."""

    reason_code = "MFA_FACTOR_NOT_CONFIRMED"


class RecoveryCodeInvalidError(ValueError):
    """The presented recovery code does not belong to the account's current
    set."""

    reason_code = "RECOVERY_CODE_INVALID"


class RecoveryCodeAlreadyUsedError(ValueError):
    """The recovery code belongs to the set and has already been consumed.
    Recovery codes are single-use; a second presentation is a replay."""

    reason_code = "RECOVERY_CODE_ALREADY_USED"


class RecoveryCodeSetExhaustedError(ValueError):
    """Every code in the set has been consumed. The next step is reissuing the
    set under step-up, not retrying."""

    reason_code = "RECOVERY_CODE_SET_EXHAUSTED"


class SmsOtpNotAnAuthenticationFactorError(ValueError):
    """SMS OTP was offered as a login method or as a step-up factor. It is
    neither, and it carries no assurance level at all (OD-P14-09). It
    verifies a phone channel and contributes a low-weight recovery signal;
    an attacker who takes over the number gains a verified channel and no
    authentication."""

    reason_code = "SMS_OTP_NOT_AN_AUTHENTICATION_FACTOR"


# --- Assurance and step-up --------------------------------------------------


class AssuranceInsufficientError(ValueError):
    """The session's authentication assurance is below what the action
    requires. Evaluated fail-closed as a conjunction per canon 19d.8; no
    'or' condition can rescue it."""

    reason_code = "ASSURANCE_INSUFFICIENT"


class AssuranceStaleError(ValueError):
    """Assurance was sufficient but is outside the freshness window for this
    action class. The level is right and the age is wrong, which is a
    different remedy from raising the level."""

    reason_code = "ASSURANCE_STALE"


class StepUpRequiredError(ValueError):
    """A step-up is required for this action and has not been performed."""

    reason_code = "STEP_UP_REQUIRED"


class StepUpExpiredError(ValueError):
    """The step-up was performed and its window has elapsed."""

    reason_code = "STEP_UP_EXPIRED"


class StepUpObjectChangedError(ValueError):
    """The object changed after confirmation, so the approval is void
    (ADR-082). A step-up obtained against version n does not authorise
    version n+1; this is the rule that stops an approval being harvested for
    one thing and spent on another."""

    reason_code = "STEP_UP_OBJECT_CHANGED"


class StepUpBindingMismatchError(ValueError):
    """The step-up presented was bound to a different actor, session, action
    type or resource than the one being attempted. Distinct from
    STEP_UP_OBJECT_CHANGED, which is the same resource at a later version."""

    reason_code = "STEP_UP_BINDING_MISMATCH"


class StepUpCancelledError(ValueError):
    """The user cancelled the step-up. Recorded distinctly so a cancelled
    confirmation is never read as a failed one."""

    reason_code = "STEP_UP_CANCELLED"


class StepUpAlreadyConsumedError(ValueError):
    """The step-up confirmation was already spent on an action. A confirmation
    authorises one act, not a session of them."""

    reason_code = "STEP_UP_ALREADY_CONSUMED"


class StepUpMethodNotEligibleError(ValueError):
    """The method offered is marked step-up ineligible in the authentication
    method matrix and can never satisfy a step-up requirement, whatever the
    session already holds."""

    reason_code = "STEP_UP_METHOD_NOT_ELIGIBLE"


# --- Session security -------------------------------------------------------


class SessionExpiredError(ValueError):
    """The idle or the absolute deadline was reached. Both are mandatory; no
    session exists without them."""

    reason_code = "SESSION_EXPIRED"


class SessionRevokedError(ValueError):
    """The session was revoked and cannot refresh. A revoked session that could
    silently regenerate would make revocation cosmetic."""

    reason_code = "SESSION_REVOKED"


class SessionReplayDetectedError(ValueError):
    """A rotated refresh token was presented a second time. The whole token
    family is revoked and a security event is raised: either the holder or
    an attacker has a stale copy, and neither may continue."""

    reason_code = "SESSION_REPLAY_DETECTED"


class SessionScopeMismatchError(ValueError):
    """The session is not scoped to this workspace. Sessions are minted per
    origin and never span a risk boundary."""

    reason_code = "SESSION_SCOPE_MISMATCH"


class SessionOriginMismatchError(ValueError):
    """The session was presented from an origin it is not bound to."""

    reason_code = "SESSION_ORIGIN_MISMATCH"


class SessionQuarantinedError(ValueError):
    """The session is quarantined pending a security response. It is neither
    active nor revoked, and the difference matters to the holder."""

    reason_code = "SESSION_QUARANTINED"


class CsrfTokenInvalidError(ValueError):
    """A state-changing request arrived without a valid CSRF token."""

    reason_code = "CSRF_TOKEN_INVALID"


class SessionIdentifierInUrlError(ValueError):
    """A session identifier was placed in a URL or a redirect target. Refused
    structurally: URLs end up in logs, referrers and shoulder views."""

    reason_code = "SESSION_IDENTIFIER_IN_URL"


# --- Account lifecycle ------------------------------------------------------


class AccountLockedError(ValueError):
    """An AccountLock is in force. A lock is temporary, automatic and self-
    clearing, and it is deliberately not an AccountStatus (OD-P14-01) - the
    account is still whatever status it was."""

    reason_code = "ACCOUNT_LOCKED"


class AccountRestrictedError(ValueError):
    """An AccountRestriction with a named authority is in force."""

    reason_code = "ACCOUNT_RESTRICTED"


class AccountQuarantinedError(ValueError):
    """A security-class AccountRestriction (security quarantine) is in force.
    Represented as a restriction rather than a status because it has an
    authority and a review obligation."""

    reason_code = "ACCOUNT_QUARANTINED"


class AccountClosedError(ValueError):
    """The account is closed. Closure is terminal."""

    reason_code = "ACCOUNT_CLOSED"


class AccountNotActivatedError(ValueError):
    """The account is still pending; contact verification has not completed."""

    reason_code = "ACCOUNT_NOT_ACTIVATED"


class ClosureAlreadyRequestedError(ValueError):
    """An AccountClosureRequest is already open for this account."""

    reason_code = "ACCOUNT_CLOSURE_ALREADY_REQUESTED"


class ClosureNotRequestedError(ValueError):
    """No open AccountClosureRequest exists to cancel or complete."""

    reason_code = "ACCOUNT_CLOSURE_NOT_REQUESTED"


class AnonymizationInProgressError(ValueError):
    """An anonymization run is already in progress for this account; a second
    run would race the first over the same records."""

    reason_code = "ACCOUNT_ANONYMIZATION_IN_PROGRESS"


class AnonymizationNotStartedError(ValueError):
    """Completion was requested for an anonymization that was never begun."""

    reason_code = "ACCOUNT_ANONYMIZATION_NOT_STARTED"


# --- Account recovery -------------------------------------------------------


class RecoveryRequiredError(ValueError):
    """Authentication cannot proceed with what the account holds; the governed
    recovery workflow is the path."""

    reason_code = "RECOVERY_REQUIRED"


class RecoveryRiskTooHighError(ValueError):
    """The risk assessment refused the recovery on named, explainable signals.
    No opaque score is ever the sole basis."""

    reason_code = "RECOVERY_RISK_TOO_HIGH"


class RecoveryCoolingOffActiveError(ValueError):
    """The cooling-off window has not elapsed. The window exists so the
    legitimate holder has time to stop a fraudulent recovery."""

    reason_code = "RECOVERY_COOLING_OFF_ACTIVE"


class AlternateVerificationFailedError(ValueError):
    """The independent verification method - independent of the credential that
    was lost - failed."""

    reason_code = "ALTERNATE_VERIFICATION_FAILED"


class RecoveryContactRecentlyChangedError(ValueError):
    """The channel offered for recovery was changed too recently to rely on.
    Contact-change takeover is a first-class threat."""

    reason_code = "RECOVERY_CONTACT_RECENTLY_CHANGED"


class RecoverySelfApprovalRefusedError(ValueError):
    """The reviewer initiated the case or is its subject. Insider reset and
    support impersonation are first-class threats and this is their
    structural control."""

    reason_code = "RECOVERY_SELF_APPROVAL_REFUSED"


class RecoveryDualControlRequiredError(ValueError):
    """High-assurance recovery requires a second approver, and this decision
    carried one approver only."""

    reason_code = "RECOVERY_DUAL_CONTROL_REQUIRED"


class RecoveryEvidenceMissingError(ValueError):
    """The case carries no evidence reference, so a disputed recovery could not
    be answered from a record."""

    reason_code = "RECOVERY_EVIDENCE_MISSING"


class RecoveryAlreadyCompletedError(ValueError):
    """The recovery case has already reached completion; it is not a reusable
    authorisation."""

    reason_code = "RECOVERY_ALREADY_COMPLETED"


class RecoveryRiskAcceptanceRequiredError(ValueError):
    """The resulting confidence is below the assurance the recovery replaces,
    and no explicit reason-coded risk acceptance by a named authority was
    recorded (specification section 12.1). Without it the recovery path
    silently becomes the account's real assurance level."""

    reason_code = "RECOVERY_RISK_ACCEPTANCE_REQUIRED"


class RecoveryElevationRefusedError(ValueError):
    """Emergency recovery restored access and a high-risk action was attempted
    immediately afterwards. Elevated capability returns only once the normal
    assurance path is satisfied."""

    reason_code = "RECOVERY_ELEVATION_REFUSED"


class RecoveryCredentialsNotRevokedError(ValueError):
    """Completion was attempted before the old credentials and sessions were
    revoked. A recovery that leaves the attacker logged in has recovered
    nothing, so the order is enforced rather than documented."""

    reason_code = "RECOVERY_CREDENTIALS_NOT_REVOKED"


# --- Contact handles --------------------------------------------------------


class ContactNotVerifiedError(ValueError):
    """The channel has not completed verification."""

    reason_code = "CONTACT_NOT_VERIFIED"


class ContactRecentlyChangedError(ValueError):
    """The action falls within the protective window after a contact change."""

    reason_code = "CONTACT_RECENTLY_CHANGED"


class ContactAlreadyInUseError(ValueError):
    """The channel is already attached within its uniqueness scope. Never
    disclosed to an unauthenticated caller, because that would be an
    account-existence oracle."""

    reason_code = "CONTACT_ALREADY_IN_USE"


class ContactReuseBlockedError(ValueError):
    """The governed reuse policy refuses this channel - typically a handle
    released by a closed account within the protective window, where reuse
    would let a later holder inherit another person's history."""

    reason_code = "CONTACT_REUSE_BLOCKED"


class ContactNotNormalizableError(ValueError):
    """The value could not be normalized into the canonical form the uniqueness
    scope compares. Fail-closed: an unnormalizable value is never stored raw
    and compared later."""

    reason_code = "CONTACT_NOT_NORMALIZABLE"


class ContactAutoMergeRefusedError(ValueError):
    """Two accounts were about to be merged because they share a contact value.
    Refused unconditionally (ADR-080): a shared family address is not
    evidence of one person, and duplicate handling is a reviewed decision."""

    reason_code = "CONTACT_AUTO_MERGE_REFUSED"


class LastVerifiedChannelError(ValueError):
    """Removal refused: it is the only verified channel and out-of-band
    notification would have nowhere to go."""

    reason_code = "CONTACT_LAST_VERIFIED_CHANNEL"


class NotificationDeliveryFailedError(ValueError):
    """A required notification could not be handed to the delivery outbox. A
    security-relevant operation that depends on notification does not
    silently complete."""

    reason_code = "NOTIFICATION_DELIVERY_FAILED"


# --- Account linking and duplicates -----------------------------------------


class DuplicateAccountSuspectedError(ValueError):
    """Routed to review. Never an automatic merge, and never a response that
    discloses to the caller that another account exists."""

    reason_code = "DUPLICATE_ACCOUNT_SUSPECTED"


class AccountLinkingDeniedError(ValueError):
    """Linking refused by policy or by the governed review."""

    reason_code = "ACCOUNT_LINKING_DENIED"


class AccountLinkingProofMissingError(ValueError):
    """Control of both sides was not proven. Linking is user-initiated and
    proof-of-control-bound; never inferred from a shared attribute."""

    reason_code = "ACCOUNT_LINKING_PROOF_MISSING"


class AccountLinkingConflictError(ValueError):
    """The target is already linked to a different account, or the link would
    create a cycle. Resolved by review, never by reassignment."""

    reason_code = "ACCOUNT_LINKING_CONFLICT"


# --- Identity proofing ------------------------------------------------------


class IdentityProofingInsufficientError(ValueError):
    """The identity assurance established by proofing is below what the action
    requires. Distinct from ASSURANCE_INSUFFICIENT, which is about the
    session: canon 19d.8 keeps the two concepts unmixed."""

    reason_code = "IDENTITY_PROOFING_INSUFFICIENT"


class IdentityAssertionExpiredError(ValueError):
    """The identity assertion is outside its freshness window."""

    reason_code = "IDENTITY_ASSERTION_EXPIRED"


class IdentityProofingInconclusiveError(ValueError):
    """Neither verified nor rejected. Manual review follows; there is no
    default verdict."""

    reason_code = "IDENTITY_PROOFING_INCONCLUSIVE"


class ProofingDoesNotApproveMembershipError(ValueError):
    """A membership approval was inferred from a proofing decision. Refused:
    canon 19d.9 stage B is a separate human decision and no path around it
    exists."""

    reason_code = "PROOFING_DOES_NOT_APPROVE_MEMBERSHIP"


# --- External identity providers --------------------------------------------


class ExternalProviderUnavailableError(ValueError):
    """The adapter could not reach the provider. The account has a local path;
    the outage is recorded rather than routed around."""

    reason_code = "EXTERNAL_PROVIDER_UNAVAILABLE"


class ExternalAssertionInvalidError(ValueError):
    """Issuer, audience, signature, nonce or issued-at validation failed on the
    external assertion."""

    reason_code = "EXTERNAL_ASSERTION_INVALID"


class ExternalAssertionReplayedError(ValueError):
    """The assertion's identifier or nonce has been seen before. Recorded
    distinctly from a validation failure because a replay is an attack and a
    malformed assertion is usually a bug."""

    reason_code = "EXTERNAL_ASSERTION_REPLAYED"


class ExternalSubjectNotLinkedError(ValueError):
    """The provider subject is not linked to any account, and no account is
    created or matched implicitly. A provider subject is never a global user
    ID (ADR-079)."""

    reason_code = "EXTERNAL_SUBJECT_NOT_LINKED"


# --- Cross-origin authentication bootstrap ----------------------------------


class BootstrapInvalidError(ValueError):
    """The workspace authorization response failed validation for a reason
    other than audience, expiry, nonce, redirect URI or reuse - each of
    which has its own code."""

    reason_code = "BOOTSTRAP_INVALID"


class BootstrapAudienceMismatchError(ValueError):
    """The authorization response was presented to an audience other than the
    workspace it names. No token is reusable across origins."""

    reason_code = "BOOTSTRAP_AUDIENCE_MISMATCH"


class BootstrapAlreadyUsedError(ValueError):
    """The authorization response is single-use and was already redeemed. It is
    worthless the moment after it is used, and that is the property that
    distinguishes this ceremony from SSO."""

    reason_code = "BOOTSTRAP_ALREADY_USED"


class BootstrapExpiredError(ValueError):
    """The authorization response was presented after its short expiry."""

    reason_code = "BOOTSTRAP_EXPIRED"


class BootstrapNonceMismatchError(ValueError):
    """The nonce in the response does not match the one the workspace issued
    with its request."""

    reason_code = "BOOTSTRAP_NONCE_MISMATCH"


class RedirectUriNotAllowlistedError(ValueError):
    """The redirect URI is not on the workspace's registered allowlist. Open-
    redirect abuse is a first-class threat and the allowlist is exact-match,
    never prefix-match."""

    reason_code = "BOOTSTRAP_REDIRECT_URI_INVALID"


class BootstrapProofVerificationFailedError(ValueError):
    """The PKCE-equivalent proof did not verify against the challenge recorded
    with the request."""

    reason_code = "BOOTSTRAP_PROOF_VERIFICATION_FAILED"


class BootstrapReplayDetectedError(ValueError):
    """A redeemed authorization response was presented again. Distinct from
    BOOTSTRAP_ALREADY_USED in that the second presentation came from a
    different audience or after the first was already recorded as spent,
    which is an attack signal rather than a client bug."""

    reason_code = "BOOTSTRAP_REPLAY_DETECTED"


class CrossWorkspaceHandoffInvalidError(ValueError):
    """The handoff artifact is expired, addressed to the wrong audience, or
    scoped to a different purpose."""

    reason_code = "CROSS_WORKSPACE_HANDOFF_INVALID"


# --- WS-03 voting handoff boundary ------------------------------------------


class VotingHandoffInvalidError(ValueError):
    """The voting handoff artifact did not verify. Deliberately uniform: the
    refusal discloses nothing about which property failed to a caller
    outside the issuing boundary."""

    reason_code = "VOTING_HANDOFF_INVALID"


class VotingHandoffAlreadyUsedError(ValueError):
    """A single-use artifact was presented a second time."""

    reason_code = "VOTING_HANDOFF_ALREADY_USED"


class VotingHandoffExpiredError(ValueError):
    """The artifact was presented after its short expiry, checked at
    redemption."""

    reason_code = "VOTING_HANDOFF_EXPIRED"


class VotingHandoffAudienceMismatchError(ValueError):
    """The artifact was presented to an audience other than the WS-03 origin it
    was bound to."""

    reason_code = "VOTING_HANDOFF_AUDIENCE_MISMATCH"


class VotingHandoffPurposeMismatchError(ValueError):
    """The artifact was presented for a voting context other than the one it is
    bound to. One artifact, one voting context, no transfer."""

    reason_code = "VOTING_HANDOFF_PURPOSE_MISMATCH"


class VotingHandoffReverseResolutionRefusedError(ValueError):
    """A caller asked which account obtained a redeemed artifact. Refused
    structurally: neither the artifact nor the issuance and redemption
    records, jointly or separately, permit that resolution (ADR-088). The
    refusal exists as a code so the attempt is auditable."""

    reason_code = "VOTING_HANDOFF_REVERSE_RESOLUTION_REFUSED"


# --- Scoped identity mappings -----------------------------------------------


class IdentityMappingPurposeMismatchError(PermissionError):
    """The mapping was resolved for a purpose other than the one it was created
    for. A mapping without an enforced purpose is a general-purpose mapping,
    which is the global identifier this architecture exists to prevent."""

    reason_code = "IDENTITY_MAPPING_PURPOSE_MISMATCH"


class IdentityMappingScopeMismatchError(PermissionError):
    """The mapping was resolved outside its organizational scope. FIR-INV-013's
    Bund/Land/Kreis isolation applies to mappings too."""

    reason_code = "IDENTITY_MAPPING_SCOPE_MISMATCH"


class IdentityMappingExpiredError(ValueError):
    """The mapping is past its expiry. A mapping that never expires becomes the
    global identifier by longevity."""

    reason_code = "IDENTITY_MAPPING_EXPIRED"


class IdentityMappingNotPermittedError(PermissionError):
    """The caller's access policy does not permit resolving this mapping. A
    mapping boundary is a governed operation, not a table anyone may join."""

    reason_code = "IDENTITY_MAPPING_NOT_PERMITTED"


class UnrestrictedMappingLookupRefusedError(PermissionError):
    """An enumeration across mappings was attempted without a purpose and a
    scope. There is no 'list all mappings' operation, because such an
    operation would be the correlation surface the mapping boundary exists
    to deny."""

    reason_code = "UNRESTRICTED_MAPPING_LOOKUP_REFUSED"


class GlobalIdentifierRefusedError(PermissionError):
    """A raw account, person, membership or provider-subject identifier was
    about to cross a boundary that admits only a purpose-scoped actor
    reference (FIR-INV-001, ADR-079). This is the code that makes the
    absence of a global user ID structural rather than aspirational."""

    reason_code = "GLOBAL_IDENTIFIER_REFUSED"


# --- Privileged identity administration -------------------------------------


class PrivilegedApprovalMissingError(PermissionError):
    """The required PACK-12 grant or approval is absent, expired or scoped to a
    different purpose."""

    reason_code = "PRIVILEGED_APPROVAL_MISSING"


class ManualReviewRequiredError(ValueError):
    """The decision is routed to a human. A first-class outcome, never a silent
    approval or a silent denial."""

    reason_code = "MANUAL_REVIEW_REQUIRED"


class SeparationOfDutiesViolatedError(PermissionError):
    """The actor may not perform this act given another role they hold on the
    same case."""

    reason_code = "SEPARATION_OF_DUTIES_VIOLATED"


class SupportActionNotPermittedError(PermissionError):
    """A Support Agent attempted an act reserved to another role - changing an
    account owner, completing a recovery alone, or reading identity content.
    Support impersonation is a first-class threat."""

    reason_code = "SUPPORT_ACTION_NOT_PERMITTED"


class BreakGlassJustificationMissingError(PermissionError):
    """Break-glass was invoked without the justification and second actor
    PACK-12 requires. Emergencies are exactly where controls get skipped, so
    this one is enforced rather than trusted."""

    reason_code = "BREAK_GLASS_JUSTIFICATION_MISSING"


class SystemAdminIdentityAccessRefusedError(PermissionError):
    """A System Admin role attempted to read identity content. Operating the
    system is not reading the people in it (ADR-087)."""

    reason_code = "SYSTEM_ADMIN_IDENTITY_ACCESS_REFUSED"


# --- Security controls ------------------------------------------------------


class RateLimitExceededError(ValueError):
    """The governed rate limit for this operation and subject was exceeded."""

    reason_code = "RATE_LIMIT_EXCEEDED"


class AuthenticationThrottledError(ValueError):
    """Repeated authentication failures have throttled this subject. Distinct
    from ACCOUNT_LOCKED: throttling is per attempt source and clears with
    time; a lock is a record on the account."""

    reason_code = "AUTHENTICATION_THROTTLED"


class ChallengeExpiredError(ValueError):
    """The challenge was presented after its expiry."""

    reason_code = "CHALLENGE_EXPIRED"


class NonceAlreadyUsedError(ValueError):
    """The nonce has already been consumed. Nonces are single-use across the
    whole replay-prevention store, not per ceremony."""

    reason_code = "NONCE_ALREADY_USED"


class OriginNotAllowedError(ValueError):
    """The request origin is not one of the ten declared workspace origins."""

    reason_code = "ORIGIN_NOT_ALLOWED"


class SecretInPayloadRefusedError(ValueError):
    """A payload, audit record or metric label was about to carry secret
    material - a password, an OTP, a recovery code, a private key, a full
    WebAuthn assertion or a raw contact value. Refused at construction, so
    the prohibition is a code path rather than a review note."""

    reason_code = "SECRET_IN_PAYLOAD_REFUSED"


class AuditUnavailableError(ValueError):
    """The audit path is unavailable, so a consequential operation refuses.
    There is no unlogged privileged act."""

    reason_code = "AUDIT_UNAVAILABLE"


# --- Concurrency and idempotency --------------------------------------------


class ResourceVersionStaleError(ValueError):
    """The expected resource version does not match the stored one. PACK-13's
    ADR-077 discipline applied to identity aggregates."""

    reason_code = "RESOURCE_VERSION_STALE"


class IdempotencyKeyReusedError(ValueError):
    """The idempotency key was seen before with a different request body.
    Returning the first result would answer a question that was not asked;
    refusing is the only safe option."""

    reason_code = "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"


# --- Governed configuration and retention -----------------------------------


class ConfigurationRelaxationNotGovernedError(ValueError):
    """A timeout or freshness value was relaxed without an authority, a reason
    code and an audit record. Stricter is free; relaxing is a governed
    change (specification section 8.1)."""

    reason_code = "CONFIGURATION_RELAXATION_NOT_GOVERNED"


class ConfigurationDeadlineRemovalRefusedError(ValueError):
    """A configuration attempted to remove a deadline. No configuration may;
    the schema admits no unlimited value and there is no infinite session."""

    reason_code = "CONFIGURATION_DEADLINE_REMOVAL_REFUSED"


class RetentionScheduleUnconfirmedError(ValueError):
    """A destructive disposition was requested against a record class whose
    retention duration is still the provisional schedule pending OD-P14-07's
    legal confirmation. The provisional schedule governs storage; it does
    not authorise destruction."""

    reason_code = "RETENTION_SCHEDULE_UNCONFIRMED"


# --- Fail-closed parse failures, on codes earlier packs already own ---------
#
# CT-00-02 requires every enum parse to fail closed. PACK-07 set the
# precedent for this service with `UnknownIdentityAssuranceLevelError`:
# a parse failure is a validation failure, and putting each of the thirty
# below on its own new code would fill the registry with entries that tell
# an operator nothing an existing code does not already say.


class UnknownOrganizationLevelError(ValueError):
    """Fail-closed parse failure: an organization level outside `FIR-INV-013`'s
    four values."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownIdentityMappingPurposeError(ValueError):
    """Fail-closed parse failure: a mapping purpose outside the registered set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownIdentityMappingStatusError(ValueError):
    """Fail-closed parse failure: an identity-mapping status outside the known
    set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAccountLockCauseError(ValueError):
    """Fail-closed parse failure: an `AccountLock` cause outside the registered
    set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAccountRestrictionClassError(ValueError):
    """Fail-closed parse failure: an `AccountRestriction` class outside the
    known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownClosureRequestStateError(ValueError):
    """Fail-closed parse failure: an `AccountClosureRequest` state outside the
    known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownContactChannelClassError(ValueError):
    """Fail-closed parse failure: a contact channel class other than email or
    phone."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownContactStatusError(ValueError):
    """Fail-closed parse failure: a contact status outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownCredentialTypeError(ValueError):
    """Fail-closed parse failure: a credential type outside the registered set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownCredentialStatusError(ValueError):
    """Fail-closed parse failure: a credential status outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownMfaFactorClassError(ValueError):
    """Fail-closed parse failure: an MFA factor class outside the registered
    set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownMfaFactorStatusError(ValueError):
    """Fail-closed parse failure: an MFA factor status outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAuthenticationMethodError(ValueError):
    """Fail-closed parse failure: an authentication method outside the method
    matrix."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownSessionStatusError(ValueError):
    """Fail-closed parse failure: a session status outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownSessionRiskLevelError(ValueError):
    """Fail-closed parse failure: a session risk level outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownRiskSignalCategoryError(ValueError):
    """Fail-closed parse failure: a risk signal category outside the registered
    set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownStepUpActionClassError(ValueError):
    """Fail-closed parse failure: an action class outside the assurance action
    map."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownStepUpStatusError(ValueError):
    """Fail-closed parse failure: a step-up status outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownRecoveryStateError(ValueError):
    """Fail-closed parse failure: a recovery state outside the governed
    workflow."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownRecoveryStatedReasonError(ValueError):
    """Fail-closed parse failure: a stated recovery reason outside the
    enumerated set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownProofingMethodError(ValueError):
    """Fail-closed parse failure: a proofing method outside the proofing
    matrix."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownProofingStateError(ValueError):
    """Fail-closed parse failure: a proofing case state outside the known set."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownWorkspaceError(ValueError):
    """Fail-closed parse failure: a workspace outside FRONT-00's ten declared
    workspaces."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownPrivilegedRoleError(ValueError):
    """Fail-closed parse failure: an identity-administration role outside
    ADR-087's six."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownNotificationClassError(ValueError):
    """Fail-closed parse failure: a notification class outside `FIR-
    DELIVERY-001`'s four."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownRetentionClassError(ValueError):
    """Fail-closed parse failure: a retention class outside the privacy and
    retention matrix."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownFormIdError(ValueError):
    """Fail-closed parse failure: a form ID outside the PACK-14 form inventory."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAccountSecurityEventTypeError(ValueError):
    """Fail-closed parse failure: an event type outside the PACK-14 event
    catalog."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnsupportedAccountSecurityEventVersionError(ValueError):
    """Fail-closed parse failure: an unsupported event major version."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


# --- Forbidden transitions (CT-00-03) ---------------------------------------


class ForbiddenAccountLifecycleTransitionError(ValueError):
    """The requested account registry record state transition is not in the
    allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenContactTransitionError(ValueError):
    """The requested account contact state transition is not in the allowed
    set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenCredentialTransitionError(ValueError):
    """The requested credential state transition is not in the allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenMfaFactorTransitionError(ValueError):
    """The requested MFA factor state transition is not in the allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenSessionTransitionError(ValueError):
    """The requested session record state transition is not in the allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenRecoveryTransitionError(ValueError):
    """The requested recovery case state transition is not in the allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenProofingTransitionError(ValueError):
    """The requested identity proofing case state transition is not in the
    allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenClosureRequestTransitionError(ValueError):
    """The requested account closure request state transition is not in the
    allowed set."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


# --- Plain lookup misses ----------------------------------------------------
#
# A lookup miss is deliberately NOT the same as a state refusal: no
# `UnknownCredentialError` is ever raised where `CREDENTIAL_REVOKED` is the
# truth, because collapsing the two is how a revoked credential comes to
# look like a typo in an incident review.


class UnknownAccountRegistryRecordError(ValueError):
    """No account registry record exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAccountContactError(ValueError):
    """No account contact exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownCredentialError(ValueError):
    """No credential exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownMfaFactorError(ValueError):
    """No MFA factor exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownRecoveryCodeSetError(ValueError):
    """No recovery code set exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownSessionRecordError(ValueError):
    """No session record exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownStepUpChallengeError(ValueError):
    """No step-up challenge exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownRecoveryCaseError(ValueError):
    """No recovery case exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownIdentityProofingCaseError(ValueError):
    """No identity proofing case exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownIdentityMappingError(ValueError):
    """No identity mapping exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownBootstrapRequestError(ValueError):
    """No authentication bootstrap request exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownVotingHandoffArtifactError(ValueError):
    """No voting handoff artifact exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAccountLinkRequestError(ValueError):
    """No account link request exists for the given identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownExternalIdentityProviderError(ValueError):
    """No external identity provider registration exists for the given
    identifier."""

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- Permission ------------------------------------------------------------


class IdentityAdministrationPermissionDeniedError(PermissionError):
    """The actor lacks the permission this identity-administration operation
    requires. PACK-02's own code, unchanged - PACK-14 adds no second
    permission vocabulary."""

    reason_code = "PERMISSION_DENIED"


class UnknownAccountStatusValueError(ValueError):
    """Fail-closed parse failure: an account status outside canon 7.2's
    six values. The registry's copy of the enum lives in
    `accounts.AccountRegistryStatus`; ownership stays with
    `account-service`."""

    reason_code = "VALIDATION_UNKNOWN_STATUS"


class RecordUnderLegalHoldError(ValueError):
    """A destructive disposition was attempted against a record under a
    legal hold, or one whose hold state could not be determined.
    PACK-09's own code, unchanged; an unknown hold state fails closed."""

    reason_code = "RECORD_UNDER_LEGAL_HOLD"


# --- PACK-14 correction round: reference persistence and the runnable ------
# service boundary.
#
# Added by the correction that replaced the metadata-only persistence
# layer with real migration artefacts and durable adapters, replaced the
# permissive breached-password default with a fail-closed one, and added
# the runnable request/response adapter. Same rule as the section above:
# one class per registered reason code, and no generic error.


class MigrationNotAppliedError(ValueError):
    """The database is missing a declared migration, or a declared
    migration has no artefact on disk."""

    reason_code = "PERSISTENCE_MIGRATION_NOT_APPLIED"


class MigrationChecksumMismatchError(ValueError):
    """An applied migration's artefact changed after it was applied. An
    applied migration is never edited in place."""

    reason_code = "PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH"


class MigrationOutOfOrderError(ValueError):
    """The migration sequence is not contiguous, or the database records
    a migration this repository no longer declares."""

    reason_code = "PERSISTENCE_MIGRATION_OUT_OF_ORDER"


class UnsupportedPersistedTypeError(ValueError):
    """No encoding or decoding is defined for this field type. Raw
    `bytes` reach this deliberately: no key, salt or seed is ever
    persisted by this package."""

    reason_code = "PERSISTENCE_TYPE_UNSUPPORTED"


class PersistedRecordNotFoundError(ValueError):
    """A write targeted a row that does not exist. Distinct from a plain
    read miss, which is `VALIDATION_RECORD_NOT_FOUND`."""

    reason_code = "PERSISTENCE_RECORD_NOT_FOUND"


class BreachCheckUnavailableError(ValueError):
    """No breached-password checker is bound, so no password may be
    enrolled or replaced. A checker that silently reports nothing as
    breached is not a check."""

    reason_code = "BREACH_CHECK_UNAVAILABLE"


class ApiRequestMalformedError(ValueError):
    """The request could not be parsed into the operation's declared
    fields."""

    reason_code = "API_REQUEST_MALFORMED"


class UnknownApiOperationError(ValueError):
    """No endpoint is registered for the requested operation."""

    reason_code = "API_OPERATION_UNKNOWN"


class IdempotencyKeyRequiredError(ValueError):
    """A consequential operation was called without an idempotency key."""

    reason_code = "API_IDEMPOTENCY_KEY_REQUIRED"


class ResourceVersionRequiredError(ValueError):
    """A consequential operation was called without the expected
    resource version, so there is no optimistic-concurrency check."""

    reason_code = "API_RESOURCE_VERSION_REQUIRED"


class SessionContextRequiredError(PermissionError):
    """The operation requires an authenticated session context and none
    was presented. Distinct from `ASSURANCE_INSUFFICIENT`, which is a
    context that exists and is not strong enough."""

    reason_code = "API_SESSION_CONTEXT_REQUIRED"

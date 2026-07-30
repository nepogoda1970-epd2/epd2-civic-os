"""Authentication assurance: the method matrix, the caps, and the
fail-closed conjunction.

PACK-14 **reuses canon's four-value scale** (`none`, `low`,
`substantial`, `high`) rather than inventing an AAL-0…AAL-3 vocabulary of
its own. The informal AAL names are a reading aid in the documents and
appear nowhere in this code, which is the single largest reason the canon
assessment concludes no amendment is required.

Three rules from the authentication method matrix are enforced here and
nowhere else, so they cannot be forgotten at a call site:

1. **A method's assurance class is a ceiling, not a floor.** Risk signals
   lower the effective assurance of a session; nothing raises it above
   the ceiling of the method that produced it.
2. **A cap is not raised by combining two capped methods.** Two
   `substantial` paths do not add up to a `high` one - the rule that
   stops "password + synced passkey" being sold as phishing-resistant.
3. **SMS OTP appears in no row.** It carries no assurance level at all
   and cannot raise a session to any of them (OD-P14-09).

Evaluation follows canon 19d.8 exactly: every applicable condition must
hold **simultaneously**, no "or" is permitted, and a missing, expired or
unresolvable authentication context is a refusal rather than a default
allow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from epd2_identity_service.configuration import ActionClass, IdentityConfiguration
from epd2_identity_service.credentials import CredentialBinding
from epd2_identity_service.domain import (
    _ASSURANCE_ORDER,
    AuthenticationAssuranceLevel,
    IdentityAssuranceLevel,
)
from epd2_identity_service.exceptions import (
    AssuranceInsufficientError,
    AssuranceStaleError,
    IdentityProofingInsufficientError,
    StepUpMethodNotEligibleError,
    UnknownAuthenticationMethodError,
)
from epd2_identity_service.identifiers import require_timezone


class AuthenticationMethod(StrEnum):
    """Every method the authentication method matrix names.

    `SMS_OTP` is present as a member **only** so that a request naming it
    parses into something this module can refuse precisely, in
    `assurance_ceiling`. It has no assurance row, is not step-up
    eligible, and `PERMITS_LOGIN` excludes it.
    """

    PASSKEY_DEVICE_BOUND = "passkey_device_bound"
    PASSKEY_SYNCED = "passkey_synced"
    HARDWARE_SECURITY_KEY = "hardware_security_key"
    PASSWORD_WITH_MFA = "password_with_mfa"
    MAGIC_LINK = "magic_link"
    EMAIL_OTP = "email_otp"
    SMS_OTP = "sms_otp"
    RECOVERY_CODE = "recovery_code"
    VERIFIED_DEVICE_ASSISTED = "verified_device_assisted"
    FEDERATED_PROVIDER = "federated_provider"
    EID_MEDIATED = "eid_mediated"
    IN_PERSON_ASSISTED = "in_person_assisted"


def parse_authentication_method(value: str) -> AuthenticationMethod:
    try:
        return AuthenticationMethod(value)
    except ValueError as exc:
        raise UnknownAuthenticationMethodError(f"unknown authentication method: {value!r}") from exc


#: The assurance **ceiling** each method can reach. `SMS_OTP` maps to
#: `NONE`, which is the literal content of OD-P14-09: it authenticates
#: nothing. `PASSWORD_WITH_MFA` and `PASSKEY_SYNCED` cap at `substantial`
#: and never reach `high`, whatever they are combined with.
METHOD_ASSURANCE_CEILING: dict[AuthenticationMethod, AuthenticationAssuranceLevel] = {
    AuthenticationMethod.PASSKEY_DEVICE_BOUND: AuthenticationAssuranceLevel.HIGH,
    AuthenticationMethod.PASSKEY_SYNCED: AuthenticationAssuranceLevel.SUBSTANTIAL,
    AuthenticationMethod.HARDWARE_SECURITY_KEY: AuthenticationAssuranceLevel.HIGH,
    AuthenticationMethod.PASSWORD_WITH_MFA: AuthenticationAssuranceLevel.SUBSTANTIAL,
    AuthenticationMethod.MAGIC_LINK: AuthenticationAssuranceLevel.LOW,
    AuthenticationMethod.EMAIL_OTP: AuthenticationAssuranceLevel.LOW,
    AuthenticationMethod.SMS_OTP: AuthenticationAssuranceLevel.NONE,
    AuthenticationMethod.RECOVERY_CODE: AuthenticationAssuranceLevel.SUBSTANTIAL,
    AuthenticationMethod.VERIFIED_DEVICE_ASSISTED: AuthenticationAssuranceLevel.SUBSTANTIAL,
    AuthenticationMethod.FEDERATED_PROVIDER: AuthenticationAssuranceLevel.SUBSTANTIAL,
    AuthenticationMethod.EID_MEDIATED: AuthenticationAssuranceLevel.HIGH,
    AuthenticationMethod.IN_PERSON_ASSISTED: AuthenticationAssuranceLevel.SUBSTANTIAL,
}

#: Methods that may begin a login ceremony at all. SMS OTP is absent, and
#: so is `RECOVERY_CODE`: a recovery code is recovery entry, not login.
PERMITS_LOGIN: frozenset[AuthenticationMethod] = frozenset(
    {
        AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        AuthenticationMethod.PASSKEY_SYNCED,
        AuthenticationMethod.HARDWARE_SECURITY_KEY,
        AuthenticationMethod.PASSWORD_WITH_MFA,
        AuthenticationMethod.MAGIC_LINK,
        AuthenticationMethod.VERIFIED_DEVICE_ASSISTED,
        AuthenticationMethod.FEDERATED_PROVIDER,
        AuthenticationMethod.EID_MEDIATED,
    }
)

#: Methods that may satisfy a step-up requirement. A method absent here
#: can never satisfy one, whatever the session already holds - matrix
#: rule 4.
STEP_UP_ELIGIBLE: frozenset[AuthenticationMethod] = frozenset(
    {
        AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        AuthenticationMethod.PASSKEY_SYNCED,
        AuthenticationMethod.HARDWARE_SECURITY_KEY,
        AuthenticationMethod.PASSWORD_WITH_MFA,
        AuthenticationMethod.VERIFIED_DEVICE_ASSISTED,
        AuthenticationMethod.EID_MEDIATED,
    }
)

#: Methods that are phishing-resistant. Recorded because the threat model
#: distinguishes them and because "partial" is not a value a decision can
#: be made from.
PHISHING_RESISTANT: frozenset[AuthenticationMethod] = frozenset(
    {
        AuthenticationMethod.PASSKEY_DEVICE_BOUND,
        AuthenticationMethod.PASSKEY_SYNCED,
        AuthenticationMethod.HARDWARE_SECURITY_KEY,
        AuthenticationMethod.EID_MEDIATED,
    }
)


def assurance_rank(level: AuthenticationAssuranceLevel | IdentityAssuranceLevel) -> int:
    """The canonical ordering, read from `domain`'s single table.

    Deliberately not redefined here: `domain._ASSURANCE_ORDER` is already
    the copy `tests/repository/test_pack07_duplicated_logic_parity.py`
    keeps in step with `eligibility-service`, and a second copy in this
    module would be a third thing to keep in step.
    """
    return _ASSURANCE_ORDER[level.value]


def assurance_ceiling(method: AuthenticationMethod) -> AuthenticationAssuranceLevel:
    return METHOD_ASSURANCE_CEILING[method]


def assurance_for_passkey(binding: CredentialBinding) -> AuthenticationAssuranceLevel:
    """OD-P14-08, as a function.

    A synced passkey reaches at most `substantial`; `high` requires a
    device-bound credential. The syncing cloud account is part of a
    synced credential's trust chain, and that account is not this
    system's to assess.
    """
    if binding is CredentialBinding.DEVICE_BOUND:
        return AuthenticationAssuranceLevel.HIGH
    return AuthenticationAssuranceLevel.SUBSTANTIAL


def combine_methods(
    methods: tuple[AuthenticationMethod, ...],
) -> AuthenticationAssuranceLevel:
    """Rule 2: the result is the **maximum ceiling**, never a sum.

    Two `substantial` methods produce `substantial`. There is no
    arithmetic here and no bonus for breadth, because the property `high`
    denotes - phishing resistance with device binding - is not something
    two phishable factors jointly acquire.
    """
    if not methods:
        return AuthenticationAssuranceLevel.NONE
    best = max(methods, key=lambda method: assurance_rank(assurance_ceiling(method)))
    return assurance_ceiling(best)


class RiskState(StrEnum):
    """The session's current risk classification. Explainable, never an
    opaque score alone (specification §13)."""

    NORMAL = "normal"
    ELEVATED = "elevated"
    SUSPICIOUS = "suspicious"


def apply_risk_downgrade(
    level: AuthenticationAssuranceLevel, risk: RiskState
) -> AuthenticationAssuranceLevel:
    """Rule 1: risk lowers effective assurance and never raises it.

    A downgrade does **not** destroy the session. It leaves a session
    that can still do what it satisfies and cannot do what it does not,
    which is the whole point of assurance being per action rather than
    per login.
    """
    if risk is RiskState.NORMAL:
        return level
    if risk is RiskState.ELEVATED:
        return (
            AuthenticationAssuranceLevel.SUBSTANTIAL
            if level is AuthenticationAssuranceLevel.HIGH
            else level
        )
    return AuthenticationAssuranceLevel.LOW if assurance_rank(level) > 1 else level


@dataclass(frozen=True, slots=True)
class AssuranceEvidence:
    """What the assurance decision rests on.

    Named signals rather than a bare score: `PACK-14-SESSION-SECURITY-
    MATRIX.md` §3 requires that no opaque risk score is ever the sole
    basis for a consequential denial, and a structure with nowhere to put
    a bare score is the enforcement of that.
    """

    methods: tuple[AuthenticationMethod, ...]
    credential_binding: CredentialBinding
    risk_state: RiskState
    named_signals: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.risk_state is not RiskState.NORMAL and not self.named_signals:
            raise ValueError(
                "a non-normal risk state must name its signals; "
                "an unexplained score is not evidence"
            )


@dataclass(frozen=True, slots=True)
class AuthenticationAssurance:
    """The effective assurance of a session at a moment, and how it got
    there."""

    achieved_level: AuthenticationAssuranceLevel
    effective_level: AuthenticationAssuranceLevel
    authenticated_at: datetime
    evidence: AssuranceEvidence

    def __post_init__(self) -> None:
        require_timezone(self.authenticated_at, "authenticated_at")
        if assurance_rank(self.effective_level) > assurance_rank(self.achieved_level):
            raise ValueError("effective assurance may never exceed what was achieved")


def evaluate_assurance(
    *,
    evidence: AssuranceEvidence,
    authenticated_at: datetime,
) -> AuthenticationAssurance:
    achieved = combine_methods(evidence.methods)
    if (
        AuthenticationMethod.PASSKEY_DEVICE_BOUND in evidence.methods
        or AuthenticationMethod.PASSKEY_SYNCED in evidence.methods
    ):
        achieved = min(
            achieved,
            assurance_for_passkey(evidence.credential_binding),
            key=assurance_rank,
        )
    return AuthenticationAssurance(
        achieved_level=achieved,
        effective_level=apply_risk_downgrade(achieved, evidence.risk_state),
        authenticated_at=require_timezone(authenticated_at, "authenticated_at"),
        evidence=evidence,
    )


@dataclass(frozen=True, slots=True)
class AssuranceRequirement:
    """What an action requires. All conditions, simultaneously.

    `required_identity_assurance` is separate from
    `required_authentication_assurance` and neither substitutes for the
    other: canon 19d.8's five never-interchangeable concepts, of which
    these are two.
    """

    action_class: ActionClass
    required_authentication_assurance: AuthenticationAssuranceLevel
    required_identity_assurance: IdentityAssuranceLevel
    step_up_required: bool

    def freshness_window(self, configuration: IdentityConfiguration) -> timedelta:
        return configuration.freshness_window(self.action_class)


def assert_method_step_up_eligible(method: AuthenticationMethod) -> None:
    if method not in STEP_UP_ELIGIBLE:
        raise StepUpMethodNotEligibleError(
            f"{method.value} is not eligible for step-up and can never satisfy one"
        )


def evaluate_requirement(
    *,
    assurance: AuthenticationAssurance | None,
    identity_assurance: IdentityAssuranceLevel | None,
    requirement: AssuranceRequirement,
    configuration: IdentityConfiguration,
    now: datetime,
) -> None:
    """Canon 19d.8's fail-closed conjunction.

    Four conditions, all of which must hold at once: an authentication
    context exists; its effective assurance meets the requirement; that
    assurance is inside the action's freshness window; and the identity
    assurance meets its own separate requirement. No "or" is permitted,
    and a missing or unresolvable context is a refusal - never a default
    allow.

    The order of the checks is chosen so the reason code a caller
    receives is the one that tells them what to do: raise the level, wait
    and re-authenticate, or complete proofing.
    """
    if assurance is None:
        raise AssuranceInsufficientError("no authentication context is resolvable for this session")
    if assurance_rank(assurance.effective_level) < assurance_rank(
        requirement.required_authentication_assurance
    ):
        raise AssuranceInsufficientError(
            f"this action requires {requirement.required_authentication_assurance.value} "
            f"and the session holds {assurance.effective_level.value}"
        )
    window = requirement.freshness_window(configuration)
    if require_timezone(now, "now") - assurance.authenticated_at > window:
        raise AssuranceStaleError(
            f"assurance is outside the {window} freshness window for "
            f"{requirement.action_class.value}"
        )
    if requirement.required_identity_assurance is not IdentityAssuranceLevel.NONE and (
        identity_assurance is None
        or assurance_rank(identity_assurance)
        < assurance_rank(requirement.required_identity_assurance)
    ):
        raise IdentityProofingInsufficientError(
            f"this action requires identity assurance "
            f"{requirement.required_identity_assurance.value}"
        )


#: The action map from `PACK-14-ASSURANCE-LEVEL-MATRIX.md` §2, as data.
#: A named action resolves to exactly one requirement here rather than to
#: a literal at a call site, so the matrix and the code cannot disagree.
ACTION_REQUIREMENTS: dict[str, AssuranceRequirement] = {
    "read_own_dashboard": AssuranceRequirement(
        action_class=ActionClass.ORDINARY_READ,
        required_authentication_assurance=AuthenticationAssuranceLevel.LOW,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=False,
    ),
    "read_own_security_settings": AssuranceRequirement(
        action_class=ActionClass.SECURITY_SETTINGS_READ,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=False,
    ),
    "change_contact": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "add_passkey": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "remove_passkey": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.HIGH,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "enroll_or_remove_mfa_factor": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "issue_recovery_codes": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "submit_official_form": AssuranceRequirement(
        action_class=ActionClass.OFFICIAL_SUBMISSION,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "revoke_all_sessions": AssuranceRequirement(
        action_class=ActionClass.SECURITY_OR_CONTACT_CHANGE,
        required_authentication_assurance=AuthenticationAssuranceLevel.SUBSTANTIAL,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "request_account_closure": AssuranceRequirement(
        action_class=ActionClass.CONSEQUENTIAL_ACTION,
        required_authentication_assurance=AuthenticationAssuranceLevel.HIGH,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "privileged_identity_action": AssuranceRequirement(
        action_class=ActionClass.CONSEQUENTIAL_ACTION,
        required_authentication_assurance=AuthenticationAssuranceLevel.HIGH,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
    "voting_handoff": AssuranceRequirement(
        action_class=ActionClass.CONSEQUENTIAL_ACTION,
        required_authentication_assurance=AuthenticationAssuranceLevel.HIGH,
        required_identity_assurance=IdentityAssuranceLevel.NONE,
        step_up_required=True,
    ),
}

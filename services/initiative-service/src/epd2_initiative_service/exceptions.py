"""Initiative Service exceptions, tied to stable reason codes.

Every exception carries a class-level `reason_code` string attribute
(the same convention `epd2_credential_service.exceptions` and
`epd2_eligibility_service.exceptions` use). Reason codes reused verbatim
from canon section 24 or from PACK-02 precedent are noted as such;
additive, service-owned codes are noted as new.
"""

from __future__ import annotations

# --- Unknown enum value (CT-00-02), one class per owned status enum,
# all sharing the same reason_code string as PACK-02's own precedent
# (ADR-004: the reason_code classifies the *kind* of failure, the
# exception class identifies *which* entity's enum was misused). ---


class UnknownInitiativeStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownSupportStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownAmendmentStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


class UnknownSourceVerificationStatusError(ValueError):
    reason_code = "VALIDATION_UNKNOWN_STATUS"


# --- Forbidden state transition (CT-00-03). ---


class ForbiddenInitiativeTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenSupportTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenAmendmentTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


class ForbiddenSourceVerificationTransitionError(ValueError):
    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


# --- Plain lookup miss (distinct from an unknown-enum-value failure on a
# record that does exist - see ADR-004). ---


class UnknownInitiativeError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownInitiativeVersionError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownSupportRecordError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownAmendmentError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownSourceRecordError(ValueError):
    reason_code = "VALIDATION_RECORD_NOT_FOUND"


class UnknownEligibilityDecisionReferenceError(ValueError):
    """Raised when `add_support` is given an `eligibility_decision_id`
    that `epd2_eligibility_service.application.get_eligibility_decision`
    cannot resolve. Distinct from that service's own internal "unknown
    rule" error (`epd2_eligibility_service.exceptions.
    UnknownEligibilityRuleError`) - this describes *this* service's
    failure to resolve a required upstream reference, per the ADR-008
    read-only boundary, not a failure inside eligibility-service itself.
    """

    reason_code = "VALIDATION_RECORD_NOT_FOUND"


# --- Duplicate-creation conflicts (CT-00-04 analogue for issuance/
# creation, one additive code per entity, mirroring
# `CredentialIssuanceConflictError`/`CREDENTIAL_DUPLICATE_ISSUANCE_CONFLICT`
# and `RuleVersionFrozenError`/`ELIGIBILITY_RULE_VERSION_FROZEN`). Each
# fires only when the *same* caller-supplied id is resubmitted with
# genuinely different content - a true retry (identical content) is
# idempotent and never raises. ---


class InitiativeCreationConflictError(ValueError):
    reason_code = "INITIATIVE_DUPLICATE_CREATION_CONFLICT"


class InitiativeVersionFrozenError(ValueError):
    """Raised when a caller attempts to re-submit an existing
    `(initiative_id, version_number)` with different content. Canon
    section 11.2: "Опубликованная версия не изменяется" (a published
    version never changes) - the same rule-freeze shape as
    `epd2_eligibility_service.exceptions.RuleVersionFrozenError`, applied
    to `InitiativeVersion`."""

    reason_code = "INITIATIVE_VERSION_FROZEN"


class SupportRecordCreationConflictError(ValueError):
    reason_code = "SUPPORT_RECORD_DUPLICATE_CREATION_CONFLICT"


class AmendmentCreationConflictError(ValueError):
    reason_code = "AMENDMENT_DUPLICATE_CREATION_CONFLICT"


class SourceRecordCreationConflictError(ValueError):
    reason_code = "SOURCE_RECORD_DUPLICATE_CREATION_CONFLICT"


# --- Canon section 24 codes, reused verbatim (not invented here). ---


class DuplicateSupportError(ValueError):
    """Canon section 11.3: "Один участник не может иметь более одной
    активной поддержки одной инициативы" (one participant may have at
    most one *active* `SupportRecord` per initiative). Reuses canon
    section 24's own `DUPLICATE_SUPPORT` reason code verbatim - this is
    not a new, service-invented code."""

    reason_code = "DUPLICATE_SUPPORT"


# --- Additive, service-owned codes for outcomes distinct from a plain
# forbidden transition. ---


class AmendmentTargetSupersededError(ValueError):
    """Not raised as a hard block today - `supersede_amendment` always
    succeeds structurally (the transition is allowed) - but gives
    `application.supersede_amendment`'s audit `reason_code`
    (`AMENDMENT_TARGET_SUPERSEDED`) a matching domain-exception class,
    for a caller that wants to catch/reuse this specific outcome (e.g. a
    future guard that refuses further discussion once an amendment's
    `target_version_id` is no longer the initiative's current version),
    mirroring how `DuplicateSupportError` pairs a reason code with a
    class before every call site necessarily raises it."""

    reason_code = "AMENDMENT_TARGET_SUPERSEDED"


class InitiativeHasNoVersionError(ValueError):
    """Raised by `submit_initiative` when `Initiative.current_version_id`
    is still `None` - canon requires *some* version to exist before an
    initiative can move past `draft` (there would be nothing to review),
    but assigns no field to record this rule directly; this is this
    service's own, additive completion of that gap (see README.md)."""

    reason_code = "INITIATIVE_HAS_NO_VERSION"


class InitiativeNotAcceptingSupportError(ValueError):
    """Raised by `add_support` when `Initiative.status !=
    support_collection` - canon 11.3 places `SupportRecord` creation in
    the context of the support-collection status (canon section 11.1's
    `support_collection`); this is this
    service's own, additive completion of that gap (canon lists the
    `support_collection` status but does not spell out that support may
    ONLY be added in it - the least surprising reading, and the only one
    consistent with `support_collection -> qualified`/`-> rejected` being
    meaningful outcomes of a bounded collection window)."""

    reason_code = "INITIATIVE_NOT_ACCEPTING_SUPPORT"

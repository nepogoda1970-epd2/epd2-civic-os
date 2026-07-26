"""Data protection governance and the DPIA activation gate.

Framework 0.8.1 AGR-12 (*Critical*) records that the baseline had no
controller/processor map, no purpose/basis model, no DSAR path, no DPIA
and no transfer assessment, and assigns the fix to PACK-09. Section 13.1
makes "Processing Registry, purpose / legal basis, controller / processor
mapping, DPIA gate и data-subject-request interfaces" an acceptance
criterion.

## What a "gate" means here

The DPIA gate is a *contract-level control*, not a compliance claim.
PACK-09 does not assess risk, does not decide whether a DPIA is legally
required under Art. 35 GDPR, and does not certify that an approved DPIA
is adequate. What it does is make the following impossible to skip
silently:

- a processing activity classified as high-risk cannot be **activated**
  while its DPIA is missing, draft, under review, rejected or expired;
- the party who **approves** the DPIA cannot be the party who **runs**
  the processing;
- activation is its own recorded, versioned decision with an authority
  and a reason code, not a status flip.

Framework section 9 is explicit that architectural presence or a PASS
does not activate anything legally: "юридическая активация оформляется
отдельным versioned ActivationDecision". `ProcessingActivationDecision`
below is the PACK-09-scoped instance of exactly that pattern — it
activates a processing activity *within this system*, and asserts nothing
about legal authorization to run it.

## DPO independence

Framework AGR-12 and the institutional role matrix (section 10) put the
DPO in the "independent / control" column against a Data Owner and a
Processor Manager in the operational column. `assert_dpo_independence`
enforces the separation structurally: the reviewer reference must differ
from both the controller and the process owner. It is a separation of
duties check, in the same family as PACK-05's two-actor approval, not a
judgement about anyone's competence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_compliance_service.exceptions import (
    DPIANotApprovedError,
    DPIARequiredError,
    DPOIndependenceRequiredError,
    ProcessingActivationBlockedError,
)


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


# ===========================================================================
# Risk classification and the DPIA-required determination
# ===========================================================================


class ProcessingRiskClass(StrEnum):
    """The recorded risk classification of a processing activity.

    A *recorded* classification, made by a human and stored, not a score
    this system computes. `SPECIAL_CATEGORY` is separate from `HIGH`
    because Framework section 13.1 requires special-category processing
    to carry an explicit classification of its own rather than being
    folded into a generic high-risk bucket."""

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    SPECIAL_CATEGORY = "special_category"


#: Risk classes whose activation requires an approved DPIA. Special
#: category is included unconditionally: Framework 13.1 treats it as its
#: own class precisely so it cannot be waved through as "standard".
DPIA_REQUIRING_RISK_CLASSES: frozenset[ProcessingRiskClass] = frozenset(
    {ProcessingRiskClass.HIGH, ProcessingRiskClass.SPECIAL_CATEGORY}
)


class DPIAStatus(StrEnum):
    """Lifecycle of a data protection impact assessment.

    `EXPIRED` is a real state rather than an absence, so an assessment
    that has aged out blocks activation with `DPIA_NOT_APPROVED` and a
    clear message, instead of silently continuing to authorize."""

    NOT_REQUIRED = "not_required"
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


#: The only status that permits activation of DPIA-requiring processing.
_ACTIVATING_DPIA_STATES: frozenset[DPIAStatus] = frozenset({DPIAStatus.APPROVED})

_ALLOWED_DPIA_TRANSITIONS: frozenset[tuple[DPIAStatus, DPIAStatus]] = frozenset(
    {
        (DPIAStatus.DRAFT, DPIAStatus.UNDER_REVIEW),
        (DPIAStatus.UNDER_REVIEW, DPIAStatus.APPROVED),
        (DPIAStatus.UNDER_REVIEW, DPIAStatus.REJECTED),
        (DPIAStatus.UNDER_REVIEW, DPIAStatus.DRAFT),
        (DPIAStatus.REJECTED, DPIAStatus.DRAFT),
        (DPIAStatus.APPROVED, DPIAStatus.EXPIRED),
        (DPIAStatus.EXPIRED, DPIAStatus.DRAFT),
    }
)


@dataclass(frozen=True, slots=True)
class DPIARequirementDetermination:
    """The recorded decision whether a processing activity needs a DPIA.

    Separate from the DPIA itself because "we assessed this and concluded
    none is needed" is a governance artefact in its own right, and one
    that a supervisory review will ask to see. Recording it also means the
    absence of a DPIA is never ambiguous between "not required" and "not
    done"."""

    determination_id: UUID
    activity_id: UUID
    organization_id: UUID
    risk_class: ProcessingRiskClass
    dpia_required: bool
    determined_at: datetime
    determined_by_party_reference: UUID
    basis_reference: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.determined_at, "determined_at")
        if self.risk_class in DPIA_REQUIRING_RISK_CLASSES and not self.dpia_required:
            raise DPIARequiredError(
                f"a {self.risk_class.value} processing activity cannot be determined to need no "
                "DPIA; the risk classification and the determination must agree"
            )


@dataclass(frozen=True, slots=True)
class DataProtectionImpactAssessment:
    """A DPIA attached to one processing activity.

    `reviewer_party_reference` is the independent reviewer (the DPO
    role); `approval_reference` points at the approval artefact. Neither
    is permitted to be the process owner or the controller — see
    `assert_dpo_independence`, which every state change routes through."""

    dpia_id: UUID
    activity_id: UUID
    organization_id: UUID
    status: DPIAStatus
    risk_class: ProcessingRiskClass
    reviewer_party_reference: UUID
    created_at: datetime
    updated_at: datetime
    approval_reference: str | None = None
    approved_at: datetime | None = None
    valid_until: datetime | None = None
    outcome_reason_code: str | None = None
    dpia_version: int = 1

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")
        _require_aware(self.updated_at, "updated_at")
        for name, value in (
            ("approved_at", self.approved_at),
            ("valid_until", self.valid_until),
        ):
            if value is not None:
                _require_aware(value, name)
        if self.dpia_version < 1:
            raise ValueError("dpia_version must be a positive integer")
        if self.status is DPIAStatus.APPROVED:
            if self.approved_at is None:
                raise ValueError("an approved DPIA must record when it was approved")
            if not self.approval_reference:
                raise ValueError("an approved DPIA must reference its approval artefact")
        if self.status is DPIAStatus.REJECTED and not self.outcome_reason_code:
            raise ValueError("a rejected DPIA must carry the reason code explaining it")

    def is_activating_at(self, at: datetime) -> bool:
        """Whether this DPIA currently permits activation.

        Checks validity as well as status: an approved DPIA past its
        `valid_until` does not activate anything, which is the practical
        meaning of `EXPIRED` even before anyone transitions it."""
        _require_aware(at, "at")
        if self.status not in _ACTIVATING_DPIA_STATES:
            return False
        return self.valid_until is None or at < self.valid_until

    def with_status(
        self,
        target: DPIAStatus,
        at: datetime,
        *,
        approval_reference: str | None = None,
        outcome_reason_code: str | None = None,
        valid_until: datetime | None = None,
    ) -> DataProtectionImpactAssessment:
        if (self.status, target) not in _ALLOWED_DPIA_TRANSITIONS:
            raise DPIANotApprovedError(
                f"invalid DPIA transition {self.status.value} -> {target.value}"
            )
        _require_aware(at, "at")
        return replace(
            self,
            status=target,
            updated_at=at,
            approved_at=at if target is DPIAStatus.APPROVED else self.approved_at,
            approval_reference=(
                approval_reference if target is DPIAStatus.APPROVED else self.approval_reference
            ),
            valid_until=valid_until if valid_until is not None else self.valid_until,
            outcome_reason_code=(
                outcome_reason_code if outcome_reason_code else self.outcome_reason_code
            ),
            dpia_version=self.dpia_version + 1,
        )


def assert_dpo_independence(
    *,
    reviewer_party_reference: UUID,
    controller_reference: UUID,
    process_owner_authority_reference: UUID,
) -> None:
    """Raise `DPO_INDEPENDENCE_REQUIRED` if the reviewer is also the
    controller or the operational process owner.

    Framework section 10's role matrix puts the DPO in the independent /
    control column against the operational Data Owner and Processor
    Manager; AGR-12 names DPO independence explicitly. This is the same
    shape of separation-of-duties check PACK-05 applies to two-actor
    approval, and it compares *references*, not role names — a party who
    happens to hold both roles fails it, which is the point."""
    if reviewer_party_reference == controller_reference:
        raise DPOIndependenceRequiredError(
            "the DPIA reviewer may not also be the controller of the processing it assesses"
        )
    if reviewer_party_reference == process_owner_authority_reference:
        raise DPOIndependenceRequiredError(
            "the DPIA reviewer may not also be the operational process owner; a DPO does not "
            "self-approve operational processing"
        )


# ===========================================================================
# The activation gate
# ===========================================================================


class ProcessingActivationState(StrEnum):
    NOT_ACTIVATED = "not_activated"
    ACTIVATED = "activated"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class ProcessingActivationDecision:
    """The governed decision that activated (or refused to activate) a
    processing activity.

    Its own object rather than a status field, so the *decision* — who,
    when, on what basis, referencing which DPIA — survives independently
    of the activity's current state. Framework section 9: activation is a
    separate versioned decision carrying process, jurisdiction, legal
    basis, approved rules, effective dates, accountable authority,
    security evidence, fallback and revocation conditions. PACK-09
    implements the system-level subset of that shape and claims nothing
    about legal activation."""

    activation_decision_id: UUID
    activity_id: UUID
    organization_id: UUID
    state: ProcessingActivationState
    decided_at: datetime
    decided_by_authority_reference: UUID
    reason_code: str
    dpia_id: UUID | None = None
    effective_from: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_aware(self.decided_at, "decided_at")
        _require_text(self.reason_code, "reason_code")
        for name, value in (
            ("effective_from", self.effective_from),
            ("revoked_at", self.revoked_at),
        ):
            if value is not None:
                _require_aware(value, name)
        if self.state is ProcessingActivationState.ACTIVATED and self.effective_from is None:
            raise ValueError("an activation decision must record when activation takes effect")


def assert_activation_permitted(
    *,
    risk_class: ProcessingRiskClass,
    requirement: DPIARequirementDetermination | None,
    dpia: DataProtectionImpactAssessment | None,
    at: datetime,
) -> None:
    """The DPIA gate. Raise unless this processing may be activated.

    Refusal order, each with its own code so the caller knows what to fix:

    1. no requirement determination at all -> `DPIA_REQUIRED`. Fail
       closed: an activity nobody has classified is not activated on the
       assumption that it is low-risk.
    2. the determination says a DPIA is required and none exists ->
       `DPIA_REQUIRED`.
    3. a DPIA exists but is not approved-and-valid at `at` ->
       `DPIA_NOT_APPROVED`. Draft, under review, rejected, expired and
       approved-but-lapsed all land here, and the message says which.
    4. the DPIA belongs to a different activity ->
       `PROCESSING_ACTIVATION_BLOCKED`.

    A `LOW`/`STANDARD` activity with a recorded determination saying no
    DPIA is required passes — the gate is not a blanket requirement, it
    is a requirement that the question was answered and the answer
    honoured."""
    _require_aware(at, "at")
    if requirement is None:
        raise DPIARequiredError(
            "no DPIA-requirement determination exists for this processing activity; activation "
            "is refused rather than assuming low risk"
        )
    dpia_needed = requirement.dpia_required or risk_class in DPIA_REQUIRING_RISK_CLASSES
    if not dpia_needed:
        return
    if dpia is None:
        raise DPIARequiredError(
            f"processing classified {risk_class.value} requires a DPIA and none is recorded"
        )
    if dpia.activity_id != requirement.activity_id:
        raise ProcessingActivationBlockedError(
            "the supplied DPIA belongs to a different processing activity"
        )
    if not dpia.is_activating_at(at):
        raise DPIANotApprovedError(
            f"DPIA {dpia.dpia_id} is {dpia.status.value} and does not permit activation"
        )


# ===========================================================================
# Transfers and consent withdrawal
# ===========================================================================


class TransferMechanism(StrEnum):
    """The recorded basis for a transfer outside the primary scope.

    A *managed classification field*, exactly like `LegalBasis`: choosing
    a value records what the organization documented, and asserts nothing
    about whether that mechanism is valid, sufficient or correctly
    applied."""

    NO_TRANSFER = "no_transfer"
    ADEQUACY_DECISION = "adequacy_decision"
    STANDARD_CONTRACTUAL_CLAUSES = "standard_contractual_clauses"
    BINDING_CORPORATE_RULES = "binding_corporate_rules"
    DEROGATION = "derogation"
    OTHER_DOCUMENTED = "other_documented"


@dataclass(frozen=True, slots=True)
class TransferAssessment:
    """A recorded assessment of a data transfer attached to a processing
    activity. PACK-09 records the mechanism, the recipient *category* and
    the assessment reference — never a recipient's identity."""

    assessment_id: UUID
    activity_id: UUID
    organization_id: UUID
    mechanism: TransferMechanism
    recipient_category: str
    assessed_at: datetime
    assessed_by_party_reference: UUID
    assessment_reference: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.assessed_at, "assessed_at")
        _require_text(self.recipient_category, "recipient_category")


@dataclass(frozen=True, slots=True)
class ConsentWithdrawalRecord:
    """A recorded withdrawal of consent for one processing activity.

    Framework-aligned and deliberately narrow: withdrawal is recorded and
    it stops consent-based processing, but it does **not** automatically
    destroy anything. Where a lawful retention obligation or an active
    Legal Hold applies, the record survives the withdrawal — the
    retention and hold machinery in `domain.py` is unaffected by this
    object, and that is intentional rather than an omission."""

    withdrawal_id: UUID
    activity_id: UUID
    organization_id: UUID
    withdrawn_at: datetime
    subject_party_reference: UUID
    affects_records_of_class: str
    retention_obligation_persists: bool = True

    def __post_init__(self) -> None:
        _require_aware(self.withdrawn_at, "withdrawn_at")
        _require_text(self.affects_records_of_class, "affects_records_of_class")

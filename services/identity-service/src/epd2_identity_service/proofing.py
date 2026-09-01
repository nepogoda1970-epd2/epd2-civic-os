"""The identity proofing boundary - and what it deliberately is not.

It is **not a general person database**. A `person_record_id` is optional,
most accounts never acquire one, and no domain joins to it. Evidence uses
PACK-11's bundles by reference; the document content never enters an
event, a log or a record here.

Three separations are normative (ADR-086) and are enforced by this module
refusing to produce the fourth thing from the first three:

```text
authentication ≠ identity proofing ≠ membership eligibility ≠ authorization
```

Identity proofing does not approve membership - canon 19d.9 stage B is a
separate human decision and `refuse_membership_inference()` exists so a
caller who tries to short-circuit it gets a reason-coded refusal.

Canon 19d.2's prohibition is carried unchanged: verification through any
`identity_scheme` is never equivalent to, and never implies, a particular
citizenship. `identity_assurance_level` is computed solely from the fact
and quality of identity verification.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.domain import IdentityAssuranceLevel
from epd2_identity_service.exceptions import (
    ForbiddenProofingTransitionError,
    IdentityProofingInconclusiveError,
    IdentityProofingInsufficientError,
    ProofingDoesNotApproveMembershipError,
    UnknownProofingMethodError,
    UnknownProofingStateError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    PersonRecordId,
    require_timezone,
)


class IdentityProofingMethod(StrEnum):
    """The eight method classes from the identity proofing matrix."""

    SELF_ASSERTED = "self_asserted"
    EMAIL_VERIFIED = "email_verified"
    PHONE_VERIFIED = "phone_verified"
    DOCUMENT_ASSISTED = "document_assisted"
    ORGANIZATIONAL_ATTESTATION = "organizational_attestation"
    IN_PERSON = "in_person"
    EID = "eid"
    MANUALLY_REVIEWED = "manually_reviewed"


def parse_proofing_method(value: str) -> IdentityProofingMethod:
    try:
        return IdentityProofingMethod(value)
    except ValueError as exc:
        raise UnknownProofingMethodError(f"unknown identity proofing method: {value!r}") from exc


#: The **ceiling** each method reaches on canon 19d.2's scale, from the
#: proofing matrix §1. Email and phone verification map to `none`, which
#: is the honest answer: proving control of a channel proves reachability
#: and says nothing about who a person is.
METHOD_ASSURANCE_CEILING: dict[IdentityProofingMethod, IdentityAssuranceLevel] = {
    IdentityProofingMethod.SELF_ASSERTED: IdentityAssuranceLevel.NONE,
    IdentityProofingMethod.EMAIL_VERIFIED: IdentityAssuranceLevel.NONE,
    IdentityProofingMethod.PHONE_VERIFIED: IdentityAssuranceLevel.NONE,
    IdentityProofingMethod.DOCUMENT_ASSISTED: IdentityAssuranceLevel.SUBSTANTIAL,
    IdentityProofingMethod.ORGANIZATIONAL_ATTESTATION: IdentityAssuranceLevel.SUBSTANTIAL,
    IdentityProofingMethod.IN_PERSON: IdentityAssuranceLevel.HIGH,
    IdentityProofingMethod.EID: IdentityAssuranceLevel.HIGH,
    IdentityProofingMethod.MANUALLY_REVIEWED: IdentityAssuranceLevel.HIGH,
}

#: Methods whose outcome is decided by a person, not by an adapter.
REQUIRES_MANUAL_REVIEW: frozenset[IdentityProofingMethod] = frozenset(
    {
        IdentityProofingMethod.DOCUMENT_ASSISTED,
        IdentityProofingMethod.ORGANIZATIONAL_ATTESTATION,
        IdentityProofingMethod.IN_PERSON,
        IdentityProofingMethod.MANUALLY_REVIEWED,
    }
)


class ProofingState(StrEnum):
    STARTED = "started"
    EVIDENCE_RECEIVED = "evidence_received"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    VERIFIED = "verified"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


def parse_proofing_state(value: str) -> ProofingState:
    try:
        return ProofingState(value)
    except ValueError as exc:
        raise UnknownProofingStateError(f"unknown proofing state: {value!r}") from exc


_ALLOWED_PROOFING_TRANSITIONS: frozenset[tuple[ProofingState, ProofingState]] = frozenset(
    {
        (ProofingState.STARTED, ProofingState.EVIDENCE_RECEIVED),
        (ProofingState.STARTED, ProofingState.WITHDRAWN),
        (ProofingState.EVIDENCE_RECEIVED, ProofingState.VERIFIED),
        (ProofingState.EVIDENCE_RECEIVED, ProofingState.REJECTED),
        (ProofingState.EVIDENCE_RECEIVED, ProofingState.MANUAL_REVIEW_REQUIRED),
        (ProofingState.EVIDENCE_RECEIVED, ProofingState.WITHDRAWN),
        (ProofingState.MANUAL_REVIEW_REQUIRED, ProofingState.VERIFIED),
        (ProofingState.MANUAL_REVIEW_REQUIRED, ProofingState.REJECTED),
    }
)


@dataclass(frozen=True, slots=True)
class IdentityEvidenceReference:
    """A PACK-11 bundle reference. **Never** the document content."""

    evidence_reference_id: UUID
    bundle_reference: str
    evidence_class: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, "recorded_at")
        if not self.bundle_reference:
            raise ValueError("an identity evidence reference names a PACK-11 bundle")


@dataclass(frozen=True, slots=True)
class IdentityAssertion:
    """An assertion about a claimed identity, with a freshness window.

    `attributes_released` is a tuple of **attribute names**, not values:
    what crosses this boundary is the fact that a name and a date of
    birth were verified, following ADR-027's established
    derived-boolean pattern, and the raw attributes stay inside.
    """

    assertion_id: UUID
    method: IdentityProofingMethod
    issued_at: datetime
    expires_at: datetime
    attributes_released: tuple[str, ...]
    issuer_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.issued_at, "issued_at")
        require_timezone(self.expires_at, "expires_at")
        if self.expires_at <= self.issued_at:
            raise ValueError("an assertion must expire after it was issued")

    def assert_fresh(self, now: datetime) -> None:
        if require_timezone(now, "now") >= self.expires_at:
            from epd2_identity_service.exceptions import IdentityAssertionExpiredError

            raise IdentityAssertionExpiredError(
                "the identity assertion is outside its freshness window"
            )


@dataclass(frozen=True, slots=True)
class IdentityProofingDecision:
    decided_at: datetime
    verified: bool
    achieved_assurance: IdentityAssuranceLevel
    deciding_authority: str
    reason_code: str

    def __post_init__(self) -> None:
        require_timezone(self.decided_at, "decided_at")
        if not self.deciding_authority:
            raise ValueError("a proofing decision names its deciding authority")
        if not self.reason_code:
            raise ValueError("a proofing decision carries a registered reason code")


@dataclass(frozen=True, slots=True)
class IdentityProofingCase:
    """One proofing case.

    A correction is a **new case**, never a rewrite of this one - the
    pattern PACK-11 established for governed documents, applied here so a
    changed verdict leaves both verdicts visible.
    """

    case_id: UUID
    account_id: AccountId
    person_record_id: PersonRecordId | None
    method: IdentityProofingMethod
    requested_assurance: IdentityAssuranceLevel
    state: ProofingState
    started_at: datetime
    evidence: tuple[IdentityEvidenceReference, ...] = ()
    assertion: IdentityAssertion | None = None
    decision: IdentityProofingDecision | None = None
    version: int = 1

    def __post_init__(self) -> None:
        require_timezone(self.started_at, "started_at")

    def transitioned(self, target: ProofingState) -> IdentityProofingCase:
        if (self.state, target) not in _ALLOWED_PROOFING_TRANSITIONS:
            raise ForbiddenProofingTransitionError(
                f"proofing transition {self.state.value!r} -> {target.value!r} is not allowed"
            )
        return replace(self, state=target, version=self.version + 1)


def start_case(
    *,
    case_id: UUID,
    account_id: AccountId,
    method: IdentityProofingMethod,
    requested_assurance: IdentityAssuranceLevel,
    started_at: datetime,
    person_record_id: PersonRecordId | None = None,
) -> IdentityProofingCase:
    """Start a case, refusing a method that cannot reach the ask.

    Refusing up front rather than at decision time is deliberate: asking
    someone to submit an identity document for a method whose ceiling is
    below what the action needs wastes their evidence and their time.
    """
    ceiling = METHOD_ASSURANCE_CEILING[method]
    from epd2_identity_service.assurance import assurance_rank

    if assurance_rank(ceiling) < assurance_rank(requested_assurance):
        raise IdentityProofingInsufficientError(
            f"{method.value} reaches at most {ceiling.value} and cannot establish "
            f"{requested_assurance.value}"
        )
    return IdentityProofingCase(
        case_id=case_id,
        account_id=account_id,
        person_record_id=person_record_id,
        method=method,
        requested_assurance=requested_assurance,
        state=ProofingState.STARTED,
        started_at=require_timezone(started_at, "started_at"),
    )


def attach_evidence(
    case: IdentityProofingCase, *, evidence: IdentityEvidenceReference
) -> IdentityProofingCase:
    received = (
        case.transitioned(ProofingState.EVIDENCE_RECEIVED)
        if case.state is ProofingState.STARTED
        else case
    )
    return replace(received, evidence=(*received.evidence, evidence))


def record_decision(
    case: IdentityProofingCase,
    *,
    decision: IdentityProofingDecision,
) -> IdentityProofingCase:
    """Decide, with `inconclusive` as a first-class outcome.

    A method that requires manual review cannot be decided
    automatically, and an inconclusive outcome routes to review rather
    than defaulting to either verdict. "Neither verified nor rejected" is
    a real state and pretending otherwise is how a default verdict gets
    invented.
    """
    if case.method in REQUIRES_MANUAL_REVIEW and case.state is not (
        ProofingState.MANUAL_REVIEW_REQUIRED
    ):
        raise IdentityProofingInconclusiveError(
            f"{case.method.value} is decided by a reviewer; route the case to manual review first"
        )
    ceiling = METHOD_ASSURANCE_CEILING[case.method]
    from epd2_identity_service.assurance import assurance_rank

    if decision.verified and assurance_rank(decision.achieved_assurance) > assurance_rank(ceiling):
        raise IdentityProofingInsufficientError(
            f"{case.method.value} cannot establish {decision.achieved_assurance.value}"
        )
    target = ProofingState.VERIFIED if decision.verified else ProofingState.REJECTED
    return replace(case.transitioned(target), decision=decision)


def route_to_manual_review(case: IdentityProofingCase) -> IdentityProofingCase:
    return case.transitioned(ProofingState.MANUAL_REVIEW_REQUIRED)


def refuse_membership_inference(case: IdentityProofingCase) -> None:
    """ADR-086, as a call site. Always raises.

    Any code path that is about to derive a membership approval from a
    proofing verdict calls this. Canon 19d.9's stage B is a human
    decision, and a system that can infer it does not have a two-stage
    admission however its documents describe it.
    """
    raise ProofingDoesNotApproveMembershipError(
        f"proofing case {case.case_id} establishes identity assurance and approves no membership; "
        "canon 19d.9 stage B is a separate human decision"
    )


def refuse_citizenship_inference(scheme: str) -> None:
    """Canon 19d.2's prohibition, as a call site. Always raises."""
    raise IdentityProofingInsufficientError(
        f"verification through {scheme!r} is never equivalent to, and never implies, "
        "a particular citizenship"
    )

"""Official notice and legally effective notice (Framework 0.8.1 AGR-08).

This module exists to hold one trust boundary open:

    delivery / read telemetry  ≠  legally effective notice

Framework 0.8.1 states it three times — hard invariant 39 ("delivery /
read telemetry не устанавливает legally effective notice"), hard
invariant 40 ("legal notice требует authorized object, valid method,
proof и governed effect decision"), and AGR-08, which classes the
conflation as *Critical* and assigns the fix to PACK-09 with PACK-22
consuming it. Section 13.1 makes it an acceptance criterion, and section
13.3 acceptance gate 5 makes it testable: "notice delivery и legal effect
невозможно слить одним статусом".

## The three-layer model

1. **Notice** — `OfficialNotice`. The authorized object: who issued it,
   to which party, of what kind, by which permitted methods. Issuing it
   starts nothing.
2. **Service** — `ServiceAttempt`. One attempt to serve it by one
   method, carrying *telemetry*: a transport outcome and optionally a
   read signal. Any number of these may exist. None of them creates
   legal effect.
3. **Effect** — `NoticeEffectDecision`. A governed determination, by an
   authorized notice authority, that service is proven under a named
   rule. This, and only this, can start a procedural deadline, and it
   can do so exactly once.

A single status field spanning these layers would make the confusion
Framework AGR-08 names *unrepresentable-free*: `delivered` would sit on
the same axis as `effective`, and somewhere downstream a comparison would
treat one as the other. Three types with no shared status enum makes that
mistake a type error instead of a judgement call.

## What is deliberately not here

No inbox, no email/SMS/post gateway, no `Message`, no `Thread`, no group
chat, no role-address messaging, no communication UI (explicit scope
exclusion; Framework 13.2 and section 8's PACK-22 entry). `ServiceAttempt`
records *that* a channel reported an outcome and what that outcome was;
it does not implement the channel. PACK-22 will implement channels and
feed telemetry in — and Framework hard invariant 57 forbids it from
minting legal effect on a provider's say-so: "external-provider status не
создаёт internal legal effect без validation / reconciliation".
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_compliance_service.exceptions import (
    DeadlineTriggerInvalidError,
    DuplicateLegalEffectPreventedError,
    NoticeEffectAlreadyEstablishedError,
    NoticeEffectUndeterminedError,
    NoticeMethodInvalidError,
    ServiceNotProvenError,
)
from epd2_compliance_service.references import NoticeProofPackageRef


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


# ===========================================================================
# Layer 1 — the authorized object
# ===========================================================================


class NoticeKind(StrEnum):
    """What the notice is.

    Each kind has different service requirements in real procedural law;
    modelling the kind explicitly is what lets a deemed-service rule be
    selected and recorded rather than assumed."""

    CASE_OPENED = "case_opened"
    HEARING_SUMMONS = "hearing_summons"
    SUBMISSION_REQUEST = "submission_request"
    DECISION_SERVICE = "decision_service"
    INTERIM_MEASURE_SERVICE = "interim_measure_service"
    DEADLINE_NOTIFICATION = "deadline_notification"
    PROCEDURAL_ORDER = "procedural_order"


class ServiceMethod(StrEnum):
    """How service may be attempted.

    A closed list, because "was this an authorized method" has to be
    answerable deterministically. Each `OfficialNotice` carries the subset
    it authorizes; an attempt by any other method is refused with
    `NOTICE_METHOD_INVALID` before any telemetry is even considered."""

    REGISTERED_POST = "registered_post"
    POSTAL = "postal"
    ELECTRONIC_PORTAL = "electronic_portal"
    ELECTRONIC_MAIL = "electronic_mail"
    PERSONAL_SERVICE = "personal_service"
    PUBLIC_POSTING = "public_posting"


@dataclass(frozen=True, slots=True)
class OfficialNotice:
    """A notice issued by an authorized authority to a case party.

    Issuing a notice has no procedural consequence by itself. It creates
    the object that service may later be attempted on, and that a notice
    authority may later determine to have taken effect.

    `recipient_party_reference` is a per-case handle. There is no address
    field, no email field and no phone field here — the *channel*
    coordinates belong to PACK-22, and PACK-09 deliberately cannot hold
    them (Framework hard invariant 1 and AGR-28's communication identity
    minimization)."""

    notice_id: UUID
    case_id: UUID
    organization_id: UUID
    notice_kind: NoticeKind
    issuing_authority_reference: UUID
    recipient_party_reference: UUID
    authorized_methods: frozenset[ServiceMethod]
    issued_at: datetime
    content_reference: str
    recipient_is_authorized_service_recipient: bool = True

    def __post_init__(self) -> None:
        _require_aware(self.issued_at, "issued_at")
        _require_text(self.content_reference, "content_reference")
        if not self.authorized_methods:
            raise NoticeMethodInvalidError(
                "an official notice must authorize at least one service method"
            )

    def assert_method_authorized(self, method: ServiceMethod) -> None:
        if method not in self.authorized_methods:
            raise NoticeMethodInvalidError(
                f"{method.value} is not an authorized service method for notice {self.notice_id}"
            )


# ===========================================================================
# Layer 2 — service attempts and their telemetry
# ===========================================================================


class DeliveryTelemetryStatus(StrEnum):
    """What the transport reported.

    Note what these values are *not*: none of them is `effective`,
    `served` or `notified`. They describe a transport outcome and nothing
    more. `UNKNOWN` is a first-class value rather than an absence, because
    "the provider never told us" is a state the system must be able to
    hold and fail closed on, not a gap it fills with an optimistic
    default."""

    UNKNOWN = "unknown"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    REFUSED = "refused"
    UNDELIVERABLE = "undeliverable"


class ReadTelemetryStatus(StrEnum):
    """Whether the recipient's client reported a read.

    Framework hard invariant 39 covers read telemetry explicitly and for
    good reason: a read receipt is trivially forgeable, frequently absent
    for legitimate recipients, and produced by software the issuing
    organization does not control. It is an input, never a conclusion."""

    UNKNOWN = "unknown"
    NOT_READ = "not_read"
    READ_REPORTED = "read_reported"
    ACKNOWLEDGED_BY_RECIPIENT = "acknowledged_by_recipient"


@dataclass(frozen=True, slots=True)
class ServiceAttempt:
    """One recorded attempt to serve a notice.

    Carries the method used, when it was attempted, and whatever the
    transport and the recipient's client reported. `provider_reference`
    identifies the external gateway that reported it — Framework hard
    invariant 58: provider IDs are not a global person key, and this one
    identifies a *provider*, not a recipient.

    `is_reconciled` implements Framework hard invariant 57: a provider's
    success signal is not trusted until the organization has validated
    and reconciled it. An unreconciled attempt cannot support a proven
    service determination no matter how positive its telemetry is."""

    attempt_id: UUID
    notice_id: UUID
    case_id: UUID
    organization_id: UUID
    method: ServiceMethod
    attempted_at: datetime
    delivery_status: DeliveryTelemetryStatus
    read_status: ReadTelemetryStatus = ReadTelemetryStatus.UNKNOWN
    provider_reference: str = ""
    is_reconciled: bool = False
    proof_package_reference: NoticeProofPackageRef | None = None
    failure_reason_code: str | None = None
    supersedes_attempt_id: UUID | None = None

    def __post_init__(self) -> None:
        _require_aware(self.attempted_at, "attempted_at")
        if self.supersedes_attempt_id == self.attempt_id:
            raise ValueError("a service attempt cannot supersede itself")

    @property
    def is_failed(self) -> bool:
        return self.delivery_status in {
            DeliveryTelemetryStatus.BOUNCED,
            DeliveryTelemetryStatus.UNDELIVERABLE,
        }

    @property
    def telemetry_is_unknown(self) -> bool:
        return self.delivery_status is DeliveryTelemetryStatus.UNKNOWN

    def reconcile(self, *, proof_package_reference: NoticeProofPackageRef) -> ServiceAttempt:
        """Mark this attempt validated and reconciled against a proof
        package.

        This is the step Framework hard invariant 57 requires between a
        provider reporting success and the organization treating it as
        anything. Reconciliation is not itself legal effect — it only
        makes the attempt *usable as evidence* by a notice authority."""
        return replace(self, is_reconciled=True, proof_package_reference=proof_package_reference)


# ===========================================================================
# Layer 3 — the governed legal-effect determination
# ===========================================================================


class DeemedServiceRule(StrEnum):
    """Which rule the authority invoked to conclude service is proven.

    Recorded rather than implied, because "why is this deemed served"
    must be answerable years later. PACK-09 does not encode any specific
    statute's parameters: which rule applies, and after how many days, is
    configuration and legal review (Framework section 9 — legal
    activation is a separate versioned decision this repository does not
    grant)."""

    ACTUAL_RECEIPT_PROVEN = "actual_receipt_proven"
    REGISTERED_POST_PRESUMPTION = "registered_post_presumption"
    PORTAL_AVAILABILITY_PRESUMPTION = "portal_availability_presumption"
    PUBLIC_POSTING_PERIOD = "public_posting_period"
    RECIPIENT_ACKNOWLEDGEMENT = "recipient_acknowledgement"


class NoticeEffectOutcome(StrEnum):
    """The determination's outcome.

    `UNDETERMINED` exists so a notice authority can record "I looked and
    could not establish this" as a durable fact rather than leaving a
    silence that a later reader might mistake for "not yet examined"."""

    EFFECTIVE = "effective"
    NOT_EFFECTIVE = "not_effective"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True, slots=True)
class NoticeEffectDecision:
    """The governed determination that a notice took legal effect.

    The only object in this repository that may start a procedural
    deadline. Four things are structural:

    1. **A human authority decides.** `decided_by_authority_reference`
       is mandatory; there is no automatic path from telemetry to this
       object (Framework hard invariant 69: AI does not decide notice
       effect).
    2. **The supporting attempts are named.** `supporting_attempt_ids`
       records exactly which attempts the authority relied on, so the
       determination is auditable against its evidence rather than
       free-floating.
    3. **The rule is named.** `deemed_service_rule` plus
       `rule_reference` say under what the conclusion was reached.
    4. **`effective_at` is set only when the outcome is `effective`.**
       A non-effective determination cannot carry an effective instant,
       which is what stops a downstream reader from picking up a
       timestamp and treating it as a trigger."""

    effect_id: UUID
    notice_id: UUID
    case_id: UUID
    organization_id: UUID
    outcome: NoticeEffectOutcome
    decided_at: datetime
    decided_by_authority_reference: UUID
    deemed_service_rule: DeemedServiceRule
    supporting_attempt_ids: tuple[UUID, ...]
    rule_reference: str
    effective_at: datetime | None = None
    reason_code: str | None = None
    proof_package_reference: NoticeProofPackageRef | None = None

    def __post_init__(self) -> None:
        _require_aware(self.decided_at, "decided_at")
        _require_text(self.rule_reference, "rule_reference")
        if self.outcome is NoticeEffectOutcome.EFFECTIVE:
            if self.effective_at is None:
                raise ServiceNotProvenError(
                    "an effective notice determination must record when it took effect"
                )
            _require_aware(self.effective_at, "effective_at")
            if not self.supporting_attempt_ids:
                raise ServiceNotProvenError(
                    "an effective notice determination must name the service attempts it relies on"
                )
        elif self.effective_at is not None:
            raise ValueError(
                "only an effective determination may carry effective_at; a non-effective one "
                "must not, so it can never be mistaken for a deadline trigger"
            )
        if self.outcome is not NoticeEffectOutcome.EFFECTIVE and not self.reason_code:
            raise ValueError(
                "a non-effective notice determination must carry the reason code explaining it"
            )

    @property
    def establishes_legal_effect(self) -> bool:
        return self.outcome is NoticeEffectOutcome.EFFECTIVE


def determine_notice_effect(
    *,
    effect_id: UUID,
    notice: OfficialNotice,
    attempts: tuple[ServiceAttempt, ...],
    deemed_service_rule: DeemedServiceRule,
    rule_reference: str,
    decided_at: datetime,
    decided_by_authority_reference: UUID,
    effective_at: datetime,
    existing_effect: NoticeEffectDecision | None = None,
) -> NoticeEffectDecision:
    """Determine whether a notice took legal effect. The one place that
    conversion is allowed to happen.

    Refusal order, each with its own code:

    1. an effect already exists and establishes legal effect ->
       `NOTICE_EFFECT_ALREADY_ESTABLISHED`. Legal effect is created
       exactly once (Framework hard invariant 59). An identical replay is
       handled idempotently by the application layer *above* this
       function and never reaches it.
    2. no attempts at all -> `SERVICE_NOT_PROVEN`. Issuing a notice is
       not serving it.
    3. every attempt used an unauthorized method ->
       `NOTICE_METHOD_INVALID`.
    4. no attempt is both *reconciled* and positive, and no permitted
       presumption applies -> `SERVICE_NOT_PROVEN`. This is the check
       that makes `delivered` telemetry insufficient on its own: a
       delivered-but-unreconciled attempt supports nothing (hard
       invariant 57).
    5. the only usable attempts carry unknown telemetry ->
       `NOTICE_EFFECT_UNDETERMINED`, fail closed.

    One case is deliberately NOT a refusal: when every authorized attempt
    positively *failed*, this returns a recorded `NOT_EFFECTIVE`
    determination rather than raising. That is a finding about the
    evidence, and the parties are entitled to see and challenge it; an
    exception would leave no record at all. It establishes no legal
    effect and starts no deadline.

    Read telemetry is never sufficient by itself. `READ_REPORTED` on an
    otherwise-unproven attempt does not move any of these checks;
    `ACKNOWLEDGED_BY_RECIPIENT` does, but only under the
    `RECIPIENT_ACKNOWLEDGEMENT` rule, which an authority must select
    explicitly."""
    _require_aware(decided_at, "decided_at")
    _require_aware(effective_at, "effective_at")

    if existing_effect is not None and existing_effect.establishes_legal_effect:
        raise NoticeEffectAlreadyEstablishedError(
            f"notice {notice.notice_id} already took legal effect at "
            f"{existing_effect.effective_at.isoformat() if existing_effect.effective_at else '?'}"
        )

    relevant = tuple(attempt for attempt in attempts if attempt.notice_id == notice.notice_id)
    if not relevant:
        raise ServiceNotProvenError(
            f"no service attempt exists for notice {notice.notice_id}; issuing a notice is not "
            "serving it"
        )

    authorized = tuple(
        attempt for attempt in relevant if attempt.method in notice.authorized_methods
    )
    if not authorized:
        raise NoticeMethodInvalidError(
            f"every service attempt for notice {notice.notice_id} used an unauthorized method"
        )

    usable = tuple(attempt for attempt in authorized if not attempt.is_failed)
    if not usable:
        # Every authorized attempt positively failed. That is a *finding*,
        # not an error: the authority determined, on the evidence, that
        # the notice did not take effect. Recording it as a governed
        # `NOT_EFFECTIVE` decision - rather than raising - is what gives
        # the parties something to see and to challenge, and is what makes
        # `notice_effect.determined` with outcome `not_effective` a
        # reachable state rather than a documented fiction. It starts no
        # deadline: `establishes_legal_effect` is false and `effective_at`
        # stays null.
        return NoticeEffectDecision(
            effect_id=effect_id,
            notice_id=notice.notice_id,
            case_id=notice.case_id,
            organization_id=notice.organization_id,
            outcome=NoticeEffectOutcome.NOT_EFFECTIVE,
            decided_at=decided_at,
            decided_by_authority_reference=decided_by_authority_reference,
            deemed_service_rule=deemed_service_rule,
            supporting_attempt_ids=(),
            rule_reference=rule_reference,
            effective_at=None,
            reason_code=ServiceNotProvenError.reason_code,
        )

    if all(attempt.telemetry_is_unknown for attempt in usable):
        raise NoticeEffectUndeterminedError(
            f"service state for notice {notice.notice_id} could not be established; refusing to "
            "determine legal effect"
        )

    supporting = tuple(
        attempt.attempt_id for attempt in usable if _supports(attempt, deemed_service_rule)
    )
    if not supporting:
        raise ServiceNotProvenError(
            f"no reconciled service attempt for notice {notice.notice_id} supports the "
            f"{deemed_service_rule.value} rule; delivery or read telemetry alone is not proof "
            "of service"
        )

    return NoticeEffectDecision(
        effect_id=effect_id,
        notice_id=notice.notice_id,
        case_id=notice.case_id,
        organization_id=notice.organization_id,
        outcome=NoticeEffectOutcome.EFFECTIVE,
        decided_at=decided_at,
        decided_by_authority_reference=decided_by_authority_reference,
        deemed_service_rule=deemed_service_rule,
        supporting_attempt_ids=supporting,
        rule_reference=rule_reference,
        effective_at=effective_at,
    )


def _supports(attempt: ServiceAttempt, rule: DeemedServiceRule) -> bool:
    """Whether one attempt can support one deemed-service rule.

    Reconciliation is required for every rule without exception
    (Framework hard invariant 57). Beyond that, each rule names the
    telemetry it needs — and no rule is satisfied by
    `DeliveryTelemetryStatus.DELIVERED` alone *plus* a read receipt,
    because that combination is exactly the conflation AGR-08 forbids."""
    if not attempt.is_reconciled:
        return False
    if rule is DeemedServiceRule.ACTUAL_RECEIPT_PROVEN:
        return attempt.delivery_status is DeliveryTelemetryStatus.DELIVERED
    if rule is DeemedServiceRule.RECIPIENT_ACKNOWLEDGEMENT:
        return attempt.read_status is ReadTelemetryStatus.ACKNOWLEDGED_BY_RECIPIENT
    if rule is DeemedServiceRule.REGISTERED_POST_PRESUMPTION:
        return attempt.method is ServiceMethod.REGISTERED_POST and attempt.delivery_status in {
            DeliveryTelemetryStatus.DELIVERED,
            DeliveryTelemetryStatus.DISPATCHED,
        }
    if rule is DeemedServiceRule.PORTAL_AVAILABILITY_PRESUMPTION:
        return (
            attempt.method is ServiceMethod.ELECTRONIC_PORTAL
            and attempt.delivery_status is DeliveryTelemetryStatus.DELIVERED
        )
    if rule is DeemedServiceRule.PUBLIC_POSTING_PERIOD:
        return attempt.method is ServiceMethod.PUBLIC_POSTING
    return False


# ===========================================================================
# The bridge to procedural deadlines
# ===========================================================================


class TriggerSource(StrEnum):
    """What started a procedural deadline.

    `DELIVERY_TELEMETRY` and `READ_TELEMETRY` are listed *so they can be
    rejected by name*. A caller that tries to start a procedural deadline
    from either gets `DEADLINE_TRIGGER_INVALID` and a message saying
    which one it used, rather than a generic validation failure that
    leaves the architectural rule implicit."""

    NOTICE_EFFECT_DECISION = "notice_effect_decision"
    GOVERNED_DECISION = "governed_decision"
    FILING_RECEIPT = "filing_receipt"
    STATUTORY_DATE = "statutory_date"
    DELIVERY_TELEMETRY = "delivery_telemetry"
    READ_TELEMETRY = "read_telemetry"


#: The only sources that may start a procedural deadline.
GOVERNED_TRIGGER_SOURCES: frozenset[TriggerSource] = frozenset(
    {
        TriggerSource.NOTICE_EFFECT_DECISION,
        TriggerSource.GOVERNED_DECISION,
        TriggerSource.FILING_RECEIPT,
        TriggerSource.STATUTORY_DATE,
    }
)


@dataclass(frozen=True, slots=True)
class DeadlineTrigger:
    """The recorded fact that one governed source started one deadline.

    Create-once per `(deadline_id)`: the store refuses a second, and the
    application layer refuses a second trigger for the same notice
    effect. Together those give Framework hard invariant 59 — retry or
    replay never repeats a consequential legal effect — a place to be
    enforced rather than a rule to remember."""

    trigger_id: UUID
    deadline_id: UUID
    case_id: UUID
    organization_id: UUID
    source: TriggerSource
    triggered_at: datetime
    notice_effect_id: UUID | None = None
    source_reference: str = ""

    def __post_init__(self) -> None:
        _require_aware(self.triggered_at, "triggered_at")
        if self.source not in GOVERNED_TRIGGER_SOURCES:
            # Reason-coded and enforced in the constructor, not only in
            # `assert_trigger_is_governed`: a future command that builds a
            # trigger directly and hands it to the store must hit the same
            # refusal, or the guard is only as good as the last caller who
            # remembered it (Framework hard invariant 39).
            raise DeadlineTriggerInvalidError(
                f"{self.source.value} is not a governed deadline trigger source; delivery and "
                "read telemetry never start a procedural deadline"
            )
        if self.source is TriggerSource.NOTICE_EFFECT_DECISION and self.notice_effect_id is None:
            raise DeadlineTriggerInvalidError(
                "a notice-effect trigger must name the NoticeEffectDecision that produced it"
            )


def assert_trigger_is_governed(
    source: TriggerSource, *, effect: NoticeEffectDecision | None, case_id: UUID
) -> None:
    """Raise `DEADLINE_TRIGGER_INVALID` unless this source may start a
    procedural deadline for this case.

    Checks, in order: the source is governed at all; a notice-effect
    trigger actually carries an effect; that effect established legal
    effect rather than merely existing; and the effect belongs to this
    case. The third check is the one that catches the most plausible
    mistake — passing an `UNDETERMINED` or `NOT_EFFECTIVE` determination
    because it is "the notice effect object"."""
    if source not in GOVERNED_TRIGGER_SOURCES:
        raise DeadlineTriggerInvalidError(
            f"{source.value} may not start a procedural deadline: delivery and read telemetry "
            "are inputs to a notice-effect determination, never triggers themselves"
        )
    if source is not TriggerSource.NOTICE_EFFECT_DECISION:
        return
    if effect is None:
        raise DeadlineTriggerInvalidError(
            "a notice-effect trigger requires the NoticeEffectDecision it derives from"
        )
    if not effect.establishes_legal_effect:
        raise DeadlineTriggerInvalidError(
            f"notice effect {effect.effect_id} is {effect.outcome.value}; only an effective "
            "determination starts a procedural deadline"
        )
    if effect.case_id != case_id:
        raise DeadlineTriggerInvalidError("the supplied notice effect belongs to a different case")


def assert_no_duplicate_legal_effect(
    *, existing_triggers: tuple[DeadlineTrigger, ...], notice_effect_id: UUID
) -> None:
    """Raise if this notice effect has already started a deadline.

    One governed determination, one legal effect (Framework hard
    invariant 59). A caller retrying after a timeout gets the recorded
    outcome from the application layer; a caller genuinely trying to
    start a second deadline from the same effect gets this."""
    for trigger in existing_triggers:
        if trigger.notice_effect_id == notice_effect_id:
            raise DuplicateLegalEffectPreventedError(
                f"notice effect {notice_effect_id} has already triggered deadline "
                f"{trigger.deadline_id}; one governed determination produces one legal effect"
            )

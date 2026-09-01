"""Domain tests for the official-notice trust boundary (Architecture &
Domain Framework 0.8.1 section 13.2, hard invariants 39, 40, 57 and 59).

The boundary this module tests is the one the Framework treats as the
single most load-bearing separation in PACK-09:

1. `OfficialNotice` - an authorized object exists. Nothing is served.
2. `ServiceAttempt` - provider telemetry. Still not a legal effect.
3. `NoticeEffectDecision` - a governed determination. The ONLY thing that
   can start a procedural deadline.

Every test below exists because collapsing any two of those three layers
produces a system that starts legal deadlines on a mail provider's
say-so.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from epd2_compliance_service.exceptions import (
    DeadlineTriggerInvalidError,
    DuplicateLegalEffectPreventedError,
    NoticeEffectAlreadyEstablishedError,
    NoticeEffectUndeterminedError,
    NoticeMethodInvalidError,
    ServiceNotProvenError,
)
from epd2_compliance_service.notices import (
    GOVERNED_TRIGGER_SOURCES,
    DeadlineTrigger,
    DeemedServiceRule,
    DeliveryTelemetryStatus,
    NoticeEffectDecision,
    NoticeEffectOutcome,
    NoticeKind,
    OfficialNotice,
    ReadTelemetryStatus,
    ServiceAttempt,
    ServiceMethod,
    TriggerSource,
    assert_no_duplicate_legal_effect,
    assert_trigger_is_governed,
    determine_notice_effect,
)
from epd2_compliance_service.references import NoticeProofPackageRef

T0 = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
T1 = T0 + timedelta(days=3)
T2 = T0 + timedelta(days=14)

ORG = uuid4()
CASE_ID = uuid4()
NOTICE_ID = uuid4()
AUTHORITY = uuid4()
RECIPIENT = uuid4()


def _proof() -> NoticeProofPackageRef:
    return NoticeProofPackageRef(id=uuid4(), organization_id=ORG)


def _notice(**overrides: object) -> OfficialNotice:
    base = {
        "notice_id": NOTICE_ID,
        "case_id": CASE_ID,
        "organization_id": ORG,
        "notice_kind": NoticeKind.HEARING_SUMMONS,
        "issuing_authority_reference": AUTHORITY,
        "recipient_party_reference": RECIPIENT,
        "authorized_methods": frozenset({ServiceMethod.REGISTERED_POST}),
        "issued_at": T0,
        "content_reference": "pack-11:notice:1",
    }
    base.update(overrides)
    return OfficialNotice(**base)  # type: ignore[arg-type]


def _attempt(
    *,
    method: ServiceMethod = ServiceMethod.REGISTERED_POST,
    delivery: DeliveryTelemetryStatus = DeliveryTelemetryStatus.DELIVERED,
    read: ReadTelemetryStatus = ReadTelemetryStatus.UNKNOWN,
    reconciled: bool = True,
) -> ServiceAttempt:
    attempt = ServiceAttempt(
        attempt_id=uuid4(),
        notice_id=NOTICE_ID,
        case_id=CASE_ID,
        organization_id=ORG,
        method=method,
        attempted_at=T0 + timedelta(hours=6),
        delivery_status=delivery,
        read_status=read,
        provider_reference="provider:1",
    )
    return attempt.reconcile(proof_package_reference=_proof()) if reconciled else attempt


def _determine(
    *,
    notice: OfficialNotice | None = None,
    attempts: tuple[ServiceAttempt, ...] = (),
    rule: DeemedServiceRule = DeemedServiceRule.REGISTERED_POST_PRESUMPTION,
    existing: NoticeEffectDecision | None = None,
) -> NoticeEffectDecision:
    return determine_notice_effect(
        effect_id=uuid4(),
        notice=notice or _notice(),
        attempts=attempts,
        deemed_service_rule=rule,
        rule_reference="rules:service:s.5",
        decided_at=T1,
        decided_by_authority_reference=AUTHORITY,
        effective_at=T1,
        existing_effect=existing,
    )


# ===========================================================================
# Layer 1: issuing a notice starts nothing
# ===========================================================================


def test_issuing_a_notice_establishes_no_legal_effect() -> None:
    """The `OfficialNotice` type has no field, method or property that
    could express legal effect. It is not that the value is false - the
    concept is absent from the layer entirely."""
    notice = _notice()
    assert not hasattr(notice, "establishes_legal_effect")
    assert not hasattr(notice, "served_at")
    assert not hasattr(notice, "effective_at")


def test_an_unauthorized_service_method_is_refused_by_the_notice_itself() -> None:
    notice = _notice(authorized_methods=frozenset({ServiceMethod.REGISTERED_POST}))
    notice.assert_method_authorized(ServiceMethod.REGISTERED_POST)
    with pytest.raises(NoticeMethodInvalidError) as excinfo:
        notice.assert_method_authorized(ServiceMethod.ELECTRONIC_MAIL)
    assert excinfo.value.reason_code == "NOTICE_METHOD_INVALID"


def test_a_notice_must_authorize_at_least_one_method() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _notice(authorized_methods=frozenset())


# ===========================================================================
# Layer 2: telemetry is not legal effect (hard invariants 39 and 57)
# ===========================================================================


def test_delivery_telemetry_alone_does_not_establish_legal_effect() -> None:
    """The headline invariant. A provider reporting 'delivered' on an
    UNRECONCILED attempt proves nothing, and the refusal is
    `SERVICE_NOT_PROVEN` - a named refusal, not a silent false."""
    with pytest.raises(ServiceNotProvenError) as excinfo:
        _determine(attempts=(_attempt(reconciled=False),))
    assert excinfo.value.reason_code == "SERVICE_NOT_PROVEN"


def test_read_telemetry_alone_does_not_establish_legal_effect_either() -> None:
    with pytest.raises(ServiceNotProvenError):
        _determine(
            attempts=(
                _attempt(
                    delivery=DeliveryTelemetryStatus.DISPATCHED,
                    read=ReadTelemetryStatus.READ_REPORTED,
                    reconciled=False,
                ),
            )
        )


def test_reconciliation_is_what_turns_telemetry_into_usable_evidence() -> None:
    """Framework hard invariant 57: provider status is not internal legal
    effect *without validation and reconciliation*. Same telemetry, two
    outcomes, and the only difference is the proof package."""
    unreconciled = _attempt(reconciled=False)
    assert unreconciled.is_reconciled is False
    with pytest.raises(ServiceNotProvenError):
        _determine(attempts=(unreconciled,))

    reconciled = unreconciled.reconcile(proof_package_reference=_proof())
    assert reconciled.is_reconciled is True
    effect = _determine(attempts=(reconciled,))
    assert effect.outcome is NoticeEffectOutcome.EFFECTIVE


def test_issuing_a_notice_without_any_attempt_is_not_service() -> None:
    with pytest.raises(ServiceNotProvenError, match="no service attempt"):
        _determine(attempts=())


def test_every_attempt_over_an_unauthorized_method_yields_a_method_refusal() -> None:
    """A distinct code from `SERVICE_NOT_PROVEN`: the problem is not
    insufficient evidence, it is that the channel was never authorized."""
    with pytest.raises(NoticeMethodInvalidError):
        _determine(attempts=(_attempt(method=ServiceMethod.ELECTRONIC_MAIL),))


def test_all_attempts_failed_produces_a_not_effective_determination() -> None:
    """A recorded, governed 'not effective' - not an exception. The
    authority decided, on the evidence, that service did not take effect,
    and that decision is itself part of the record."""
    failed = _attempt(delivery=DeliveryTelemetryStatus.UNDELIVERABLE)
    effect = _determine(attempts=(failed,))
    assert effect.outcome is NoticeEffectOutcome.NOT_EFFECTIVE
    assert effect.establishes_legal_effect is False
    assert effect.effective_at is None
    assert effect.reason_code == "SERVICE_NOT_PROVEN"
    assert effect.supporting_attempt_ids == ()


def test_entirely_unknown_telemetry_fails_closed_as_undetermined() -> None:
    """Fail-closed: 'we do not know' is neither effective nor not
    effective, and it starts nothing."""
    unknown = _attempt(delivery=DeliveryTelemetryStatus.UNKNOWN, read=ReadTelemetryStatus.UNKNOWN)
    with pytest.raises(NoticeEffectUndeterminedError) as excinfo:
        _determine(attempts=(unknown,))
    assert excinfo.value.reason_code == "NOTICE_EFFECT_UNDETERMINED"


def test_the_telemetry_enums_are_named_telemetry_on_purpose() -> None:
    """A reviewer reading `attempt.delivery_status: DeliveryTelemetryStatus`
    is told by the type name that this is a provider's claim. Naming is
    not a substitute for a guard, but it is the first line of one."""
    assert DeliveryTelemetryStatus.__name__.endswith("TelemetryStatus")
    assert ReadTelemetryStatus.__name__.endswith("TelemetryStatus")


# ===========================================================================
# Layer 3: the governed determination (hard invariants 40 and 59)
# ===========================================================================


def test_an_effective_determination_names_its_rule_and_its_evidence() -> None:
    attempt = _attempt()
    effect = _determine(attempts=(attempt,))
    assert effect.establishes_legal_effect is True
    assert effect.deemed_service_rule is DeemedServiceRule.REGISTERED_POST_PRESUMPTION
    assert effect.rule_reference == "rules:service:s.5"
    assert effect.supporting_attempt_ids == (attempt.attempt_id,)
    assert effect.effective_at == T1


def test_an_effective_determination_requires_an_effective_instant() -> None:
    """Reason-coded, not a bare `ValueError`: an effective determination
    with no effective instant is a governance defect a party could be
    misled by, so it refuses with `SERVICE_NOT_PROVEN`."""
    with pytest.raises(ServiceNotProvenError, match="when it took effect"):
        NoticeEffectDecision(
            effect_id=uuid4(),
            notice_id=NOTICE_ID,
            case_id=CASE_ID,
            organization_id=ORG,
            outcome=NoticeEffectOutcome.EFFECTIVE,
            decided_at=T1,
            decided_by_authority_reference=AUTHORITY,
            deemed_service_rule=DeemedServiceRule.ACTUAL_RECEIPT_PROVEN,
            supporting_attempt_ids=(uuid4(),),
            rule_reference="rules:service:s.1",
            effective_at=None,
        )


def test_legal_effect_is_established_exactly_once() -> None:
    """Framework hard invariant 59. A second determination against a
    notice that already has an establishing one is refused by name."""
    established = _determine(attempts=(_attempt(),))
    with pytest.raises(NoticeEffectAlreadyEstablishedError) as excinfo:
        _determine(attempts=(_attempt(),), existing=established)
    assert excinfo.value.reason_code == "NOTICE_EFFECT_ALREADY_ESTABLISHED"


def test_a_previous_not_effective_determination_does_not_block_a_later_one() -> None:
    """Only an *establishing* effect is once-only. A refused
    determination can be revisited when better evidence arrives - which is
    the whole reason the two are distinguished."""
    not_effective = _determine(attempts=(_attempt(delivery=DeliveryTelemetryStatus.UNDELIVERABLE),))
    assert not_effective.establishes_legal_effect is False
    later = _determine(attempts=(_attempt(),), existing=not_effective)
    assert later.establishes_legal_effect is True


def test_a_refused_delivery_is_not_treated_as_a_delivery_failure() -> None:
    """`REFUSED` is a recipient *act*, not a transport failure, and in
    several jurisdictions refusing service constitutes service. PACK-09
    therefore does not classify it as failed - but it also does not
    presume it effective: no deemed-service rule currently accepts it on
    its own, so the determination falls to `SERVICE_NOT_PROVEN` until an
    authority selects a rule that covers refusal. Fail-closed on a
    genuinely contested legal question is the right default; silently
    picking either answer would not be."""
    assert _attempt(delivery=DeliveryTelemetryStatus.REFUSED).is_failed is False
    with pytest.raises(ServiceNotProvenError):
        _determine(attempts=(_attempt(delivery=DeliveryTelemetryStatus.REFUSED),))


def test_the_deemed_service_rules_each_require_supporting_evidence() -> None:
    """Actual receipt needs an acknowledgement; the registered-post
    presumption needs a delivered registered-post attempt. A rule cannot
    be satisfied by an attempt that has nothing to do with it."""
    acknowledged = _attempt(read=ReadTelemetryStatus.ACKNOWLEDGED_BY_RECIPIENT)
    effect = _determine(attempts=(acknowledged,), rule=DeemedServiceRule.ACTUAL_RECEIPT_PROVEN)
    assert effect.establishes_legal_effect is True

    merely_dispatched = _attempt(delivery=DeliveryTelemetryStatus.DISPATCHED)
    with pytest.raises(ServiceNotProvenError):
        _determine(attempts=(merely_dispatched,), rule=DeemedServiceRule.ACTUAL_RECEIPT_PROVEN)


# ===========================================================================
# Deadline triggers (hard invariants 39 and 59)
# ===========================================================================


def test_telemetry_can_never_be_a_governed_deadline_trigger() -> None:
    """The two telemetry sources exist in `TriggerSource` precisely so the
    refusal can be asserted *by name* rather than being an omission
    somebody could quietly re-add."""
    assert TriggerSource.DELIVERY_TELEMETRY not in GOVERNED_TRIGGER_SOURCES
    assert TriggerSource.READ_TELEMETRY not in GOVERNED_TRIGGER_SOURCES

    for source in (TriggerSource.DELIVERY_TELEMETRY, TriggerSource.READ_TELEMETRY):
        with pytest.raises(DeadlineTriggerInvalidError) as excinfo:
            assert_trigger_is_governed(source, effect=None, case_id=CASE_ID)
        assert excinfo.value.reason_code == "DEADLINE_TRIGGER_INVALID"


def test_a_notice_effect_trigger_requires_an_effect_that_actually_establishes() -> None:
    not_effective = _determine(attempts=(_attempt(delivery=DeliveryTelemetryStatus.BOUNCED),))
    with pytest.raises(DeadlineTriggerInvalidError):
        assert_trigger_is_governed(
            TriggerSource.NOTICE_EFFECT_DECISION, effect=None, case_id=CASE_ID
        )
    with pytest.raises(DeadlineTriggerInvalidError):
        assert_trigger_is_governed(
            TriggerSource.NOTICE_EFFECT_DECISION, effect=not_effective, case_id=CASE_ID
        )

    effective = _determine(attempts=(_attempt(),))
    assert_trigger_is_governed(
        TriggerSource.NOTICE_EFFECT_DECISION, effect=effective, case_id=CASE_ID
    )


def test_an_effect_from_another_case_cannot_trigger_this_case_s_deadline() -> None:
    effective = _determine(attempts=(_attempt(),))
    foreign = replace(effective, case_id=uuid4())
    with pytest.raises(DeadlineTriggerInvalidError):
        assert_trigger_is_governed(
            TriggerSource.NOTICE_EFFECT_DECISION, effect=foreign, case_id=CASE_ID
        )


def test_the_same_notice_effect_cannot_start_two_deadlines() -> None:
    """Framework hard invariant 59: retry and replay do not repeat a
    consequential legal effect."""
    effect_id = uuid4()
    existing = (
        DeadlineTrigger(
            trigger_id=uuid4(),
            deadline_id=uuid4(),
            case_id=CASE_ID,
            organization_id=ORG,
            source=TriggerSource.NOTICE_EFFECT_DECISION,
            triggered_at=T1,
            notice_effect_id=effect_id,
        ),
    )
    assert_no_duplicate_legal_effect(existing_triggers=existing, notice_effect_id=uuid4())
    with pytest.raises(DuplicateLegalEffectPreventedError) as excinfo:
        assert_no_duplicate_legal_effect(existing_triggers=existing, notice_effect_id=effect_id)
    assert excinfo.value.reason_code == "DUPLICATE_LEGAL_EFFECT_PREVENTED"


def test_a_notice_effect_trigger_must_carry_its_effect_id() -> None:
    with pytest.raises(DeadlineTriggerInvalidError) as excinfo:
        DeadlineTrigger(
            trigger_id=uuid4(),
            deadline_id=uuid4(),
            case_id=CASE_ID,
            organization_id=ORG,
            source=TriggerSource.NOTICE_EFFECT_DECISION,
            triggered_at=T1,
            notice_effect_id=None,
        )
    assert excinfo.value.reason_code == "DEADLINE_TRIGGER_INVALID"


def test_a_deadline_trigger_cannot_be_constructed_from_telemetry_at_all() -> None:
    """Not merely refused by the command - refused by the aggregate, so a
    future command cannot construct one and store it directly."""
    for source in (TriggerSource.DELIVERY_TELEMETRY, TriggerSource.READ_TELEMETRY):
        with pytest.raises(DeadlineTriggerInvalidError):
            DeadlineTrigger(
                trigger_id=uuid4(),
                deadline_id=uuid4(),
                case_id=CASE_ID,
                organization_id=ORG,
                source=source,
                triggered_at=T1,
            )

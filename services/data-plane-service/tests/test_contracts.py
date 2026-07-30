"""API and event contract evolution (PACK-13 §15, §16, §17; ADR-074).

No silent semantic change, no field reused for a new meaning, no reason
code whose meaning changes, no field removed before consumer migration,
no hidden privilege expansion — and, on the event side, no historical
event rewritten, no unknown enum defaulted, and no upcaster that invents
a legal fact.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from _data_plane_builders import NOW, OWNER_DOMAIN, actor, evidence, uid

from epd2_data_plane_service.contracts import (
    CONTRACT_CHANGE_SEQUENCE,
    NOT_DETERMINED,
    ApiContract,
    ApiDeprecation,
    ApiMigrationPlan,
    ApiVersion,
    BreakingChangeRecord,
    ConsumerCompatibilityStatus,
    ConsumerReadinessState,
    ContractChangeStage,
    EventCompatibilityAssessment,
    EventConsumerVersionSupport,
    EventContractVersion,
    EventUpcasterReference,
    UpcastOutcome,
    reject_flag_bypassing_gate,
    reject_hidden_privilege_expansion,
    require_consumers_migrated,
    resolve_unknown_enum_value,
)
from epd2_data_plane_service.exceptions import (
    BreakingChangeNotApprovedError,
    ConsumerNotReadyError,
    ConsumerNotRegisteredError,
    DeprecationWindowIncompleteError,
    EventVersionUnsupportedError,
    SemanticReviewRequiredError,
)
from epd2_data_plane_service.registry import CompatibilityMode


def _plan(*, rollback: bool = True) -> ApiMigrationPlan:
    return ApiMigrationPlan(
        plan_id=uid(9100),
        contract_id=uid(9101),
        from_version_id=uid(9102),
        to_version_id=uid(9103),
        steps=("announce", "coexist", "migrate", "retire"),
        evidence=evidence(),
        rollback_available=rollback,
        forward_fix_only=not rollback,
    )


def _breaking(**overrides: Any) -> BreakingChangeRecord:
    defaults: dict[str, Any] = {
        "change_id": uid(9200),
        "explicit_reason": "the field's meaning changed",
        "owner": OWNER_DOMAIN,
        "impact_summary": "two registered consumers must migrate",
        "affected_domains": ("membership-service", "finance-service"),
        "migration_plan": _plan(),
        "rollback_statement": "rehearsed against reference fixtures",
        "data_migration_reference": uid(9201),
        "event_replay_impact": "no historical event is rewritten",
        "api_coexistence_ends_at": NOW + timedelta(days=90),
        "deadline_at": NOW + timedelta(days=120),
        "approval_by": actor(2),
        "proposed_by": actor(1),
        "evidence": evidence(),
        "final_retirement_decision": "retire after consumer migration is demonstrated",
    }
    defaults.update(overrides)
    return BreakingChangeRecord(**defaults)


# ---------------------------------------------------------------------------
# API evolution
# ---------------------------------------------------------------------------


def test_endpoint_identity_is_stable_and_carried_across_versions() -> None:
    contract = ApiContract(
        contract_id=uid(9101), endpoint_identity="/memberships", owner=OWNER_DOMAIN
    )
    assert contract.endpoint_identity == "/memberships"


def test_a_retired_field_name_stays_retired() -> None:
    """`P13-API-006`: a new meaning takes a new name."""
    contract = ApiContract(
        contract_id=uid(9101),
        endpoint_identity="/memberships",
        owner=OWNER_DOMAIN,
        retired_field_names=frozenset({"status_code"}),
    )
    with pytest.raises(SemanticReviewRequiredError, match="never"):
        contract.reject_field_reuse(["status_code", "state"])


def test_an_unretired_field_name_may_be_introduced() -> None:
    ApiContract(
        contract_id=uid(9101),
        endpoint_identity="/memberships",
        owner=OWNER_DOMAIN,
        retired_field_names=frozenset({"status_code"}),
    ).reject_field_reuse(["state"])


def test_there_is_no_latest_alias_that_moves_under_a_caller() -> None:
    """`P13-API-011`."""
    with pytest.raises(ValueError, match="silently moves"):
        ApiVersion(
            version_id=uid(9102),
            contract_id=uid(9101),
            version_label="v1",
            request_schema_version_id=uid(1),
            response_schema_version_id=uid(2),
            published_at=NOW,
            is_latest_alias=True,
        )


def test_a_contract_change_widening_privilege_requires_pack_12_authority() -> None:
    """`P13-API-008`: whatever its shape."""
    version = ApiVersion(
        version_id=uid(9102),
        contract_id=uid(9101),
        version_label="v2",
        request_schema_version_id=uid(1),
        response_schema_version_id=uid(2),
        published_at=NOW,
        widens_privilege=True,
    )
    with pytest.raises(BreakingChangeNotApprovedError, match="privileged change"):
        reject_hidden_privilege_expansion(version, privileged_grant_present=False)
    reject_hidden_privilege_expansion(version, privileged_grant_present=True)


def test_retirement_before_the_coexistence_window_is_refused() -> None:
    deprecation = ApiDeprecation(
        version_id=uid(9102),
        announced_at=NOW,
        coexistence_ends_at=NOW + timedelta(days=90),
        replacement_version_id=uid(9103),
        reason_code="DEPRECATION_WINDOW_INCOMPLETE",
    )
    with pytest.raises(DeprecationWindowIncompleteError):
        deprecation.require_window_elapsed(NOW + timedelta(days=1))
    deprecation.require_window_elapsed(NOW + timedelta(days=91))


def test_an_unregistered_consumer_receives_no_compatibility_protection() -> None:
    """`P13-REG-009`: a stated consequence, not a discovered one."""
    statuses = [
        ConsumerCompatibilityStatus(
            consumer_id=uid(1),
            consumer_name="unregistered-reader",
            target_version_id=uid(9103),
            state=ConsumerReadinessState.UNREGISTERED,
            observed_at=NOW,
        )
    ]
    with pytest.raises(ConsumerNotRegisteredError):
        require_consumers_migrated(statuses, context="field removal")


def test_no_field_is_removed_before_consumer_migration() -> None:
    statuses = [
        ConsumerCompatibilityStatus(
            consumer_id=uid(1),
            consumer_name="lagging",
            target_version_id=uid(9103),
            state=ConsumerReadinessState.IN_PROGRESS,
            observed_at=NOW,
        )
    ]
    with pytest.raises(ConsumerNotReadyError):
        require_consumers_migrated(statuses, context="field removal")


def test_fully_migrated_consumers_admit_removal() -> None:
    require_consumers_migrated(
        [
            ConsumerCompatibilityStatus(
                consumer_id=uid(1),
                consumer_name="ready",
                target_version_id=uid(9103),
                state=ConsumerReadinessState.MIGRATED,
                observed_at=NOW,
            )
        ],
        context="field removal",
    )


def test_a_consumer_status_carries_no_request_payload() -> None:
    """`P13-API-013`: which consumers use which version, never what they
    sent."""
    status = ConsumerCompatibilityStatus(
        consumer_id=uid(1),
        consumer_name="c",
        target_version_id=uid(2),
        state=ConsumerReadinessState.MIGRATED,
        observed_at=NOW,
    )
    for forbidden in ("payload", "request", "body", "sample"):
        assert forbidden not in status.__slots__


def test_a_migration_plan_is_rollback_capable_or_forward_fix_only() -> None:
    """`P13-API-014`."""
    with pytest.raises(ValueError, match="not both"):
        ApiMigrationPlan(
            plan_id=uid(9100),
            contract_id=uid(9101),
            from_version_id=uid(1),
            to_version_id=uid(2),
            steps=("a",),
            evidence=evidence(),
            rollback_available=True,
            forward_fix_only=True,
        )
    with pytest.raises(ValueError, match="forward-fix-only"):
        ApiMigrationPlan(
            plan_id=uid(9100),
            contract_id=uid(9101),
            from_version_id=uid(1),
            to_version_id=uid(2),
            steps=("a",),
            evidence=evidence(),
            rollback_available=False,
            forward_fix_only=False,
        )


def test_a_forward_fix_only_plan_is_an_honest_declaration() -> None:
    assert _plan(rollback=False).forward_fix_only


# ---------------------------------------------------------------------------
# Contract change governance
# ---------------------------------------------------------------------------


def test_the_governance_sequence_has_its_eleven_stages_in_order() -> None:
    assert len(CONTRACT_CHANGE_SEQUENCE) == 11
    assert CONTRACT_CHANGE_SEQUENCE[0] is ContractChangeStage.PROPOSED
    assert CONTRACT_CHANGE_SEQUENCE[-1] is ContractChangeStage.RETIREMENT


def test_a_complete_breaking_change_record_constructs() -> None:
    assert _breaking().change_id == uid(9200)


def test_a_breaking_change_missing_a_mandatory_field_is_not_approvable() -> None:
    """`P13-GOV-002`."""
    for field in (
        "explicit_reason",
        "impact_summary",
        "rollback_statement",
        "event_replay_impact",
        "final_retirement_decision",
    ):
        with pytest.raises(BreakingChangeNotApprovedError):
            _breaking(**{field: ""})


def test_a_breaking_change_with_no_affected_domains_is_not_approvable() -> None:
    with pytest.raises(BreakingChangeNotApprovedError, match="unanswered question"):
        _breaking(affected_domains=())


def test_the_approver_of_a_breaking_change_is_not_its_proposer() -> None:
    """`P13-GOV-005`."""
    with pytest.raises(BreakingChangeNotApprovedError, match="separated"):
        _breaking(approval_by=actor(1), proposed_by=actor(1))


def test_a_feature_flag_cannot_stand_in_for_an_approval() -> None:
    """`P13-GOV-004`, FIR-INV-006: a gate a flag can skip was never a
    gate."""
    with pytest.raises(BreakingChangeNotApprovedError, match="cannot stand in"):
        reject_flag_bypassing_gate(
            flag_name="new_membership_shape", change_approved=False, gate_name="compatibility"
        )


def test_a_flag_may_control_rollout_of_an_approved_change() -> None:
    reject_flag_bypassing_gate(
        flag_name="new_membership_shape", change_approved=True, gate_name="compatibility"
    )


def test_no_flag_at_all_is_unaffected() -> None:
    reject_flag_bypassing_gate(flag_name=None, change_approved=False, gate_name="compatibility")


# ---------------------------------------------------------------------------
# Event evolution
# ---------------------------------------------------------------------------


def test_envelope_payload_and_schema_versions_are_three_distinct_fields() -> None:
    """`P13-EVO-002`."""
    version = EventContractVersion(
        event_family="membership.recorded",
        envelope_version="1.0",
        payload_version="3",
        schema_version_id=uid(9300),
        semantic_version="2.1.0",
    )
    assert version.envelope_version != version.payload_version
    assert version.schema_version_id != uid(0)


def test_an_envelope_version_follows_the_canons_form() -> None:
    with pytest.raises(ValueError, match="major"):
        EventContractVersion(
            event_family="m",
            envelope_version="1",
            payload_version="1",
            schema_version_id=uid(1),
            semantic_version="1.0.0",
        )


def test_a_consumer_declares_the_versions_it_supports() -> None:
    """`P13-EVO-005`."""
    support = EventConsumerVersionSupport(
        consumer_name="transparency-projection",
        consumer_domain=OWNER_DOMAIN,
        event_family="membership.recorded",
        supported_payload_versions=frozenset({"1", "2"}),
    )
    support.require_supported("2")
    with pytest.raises(EventVersionUnsupportedError, match="fails closed"):
        support.require_supported("3")


def test_a_consumer_cannot_declare_a_best_effort_partial_parse() -> None:
    """`P13-EVO-006`."""
    with pytest.raises(ValueError, match="partial parse"):
        EventConsumerVersionSupport(
            consumer_name="c",
            consumer_domain=OWNER_DOMAIN,
            event_family="f",
            supported_payload_versions=frozenset({"1"}),
            fails_closed_on_unsupported=False,
        )


def test_a_consumer_declares_at_least_one_version() -> None:
    with pytest.raises(ValueError, match="at least one"):
        EventConsumerVersionSupport(
            consumer_name="c",
            consumer_domain=OWNER_DOMAIN,
            event_family="f",
            supported_payload_versions=frozenset(),
        )


def _upcaster(required: tuple[str, ...] = ()) -> EventUpcasterReference:
    return EventUpcasterReference(
        upcaster_id=uid(9400),
        event_family="membership.recorded",
        from_payload_version="1",
        to_payload_version="2",
        transform=lambda payload: {**payload, "renamed": payload.get("old_name", "")},
        required_target_fields=required,
    )


def test_an_upcaster_is_deterministic_over_recorded_historical_payloads() -> None:
    """`P13-EVO-007`."""
    samples = [{"old_name": "a"}, {"old_name": "b"}, {}]
    assert _upcaster().assert_deterministic(samples)


def test_an_upcaster_restructures_what_the_original_provably_implied() -> None:
    result = _upcaster().upcast({"old_name": "a"})
    assert result.outcome is UpcastOutcome.TRANSFORMED
    assert result.payload["renamed"] == "a"


def test_an_upcaster_invents_no_legal_fact() -> None:
    """`P13-EVO-008`: an explicit not-determined value, never a plausible
    default."""
    result = _upcaster(required=("consent_reference",)).upcast({"old_name": "a"})
    assert result.outcome is UpcastOutcome.NOT_DETERMINED_RECORDED
    assert result.payload["consent_reference"] == NOT_DETERMINED
    assert result.undetermined_fields == ("consent_reference",)
    assert result.reason_code == "SEMANTIC_REVIEW_REQUIRED"


def test_an_unknown_enum_value_is_surfaced_rather_than_defaulted() -> None:
    """`P13-EVO-012`: defaulting an unknown status to 'normal' is how a
    novel failure becomes invisible."""
    known = frozenset({"active", "suspended"})
    assert resolve_unknown_enum_value("active", known_values=known, context="status") == "active"
    unknown = resolve_unknown_enum_value("lapsed", known_values=known, context="status")
    assert unknown.startswith(NOT_DETERMINED)
    assert "lapsed" in unknown


def test_an_event_assessment_asserts_historical_interpretability() -> None:
    """`P13-EVO-003`, `P13-EVO-004`: a historical event is never
    rewritten, and a new schema does not change the meaning of an old
    one."""
    assessment = EventCompatibilityAssessment(
        assessment_id=uid(9500),
        event_family="membership.recorded",
        from_payload_version="1",
        to_payload_version="2",
        verdict=CompatibilityMode.BACKWARD,
        historical_events_remain_interpretable=True,
        upcaster=_upcaster(),
    )
    assert assessment.verdict is CompatibilityMode.BACKWARD


def test_an_assessment_that_cannot_assert_interpretability_is_incomplete() -> None:
    with pytest.raises(SemanticReviewRequiredError, match="never rewritten"):
        EventCompatibilityAssessment(
            assessment_id=uid(9500),
            event_family="membership.recorded",
            from_payload_version="1",
            to_payload_version="2",
            verdict=CompatibilityMode.BREAKING,
            historical_events_remain_interpretable=False,
        )

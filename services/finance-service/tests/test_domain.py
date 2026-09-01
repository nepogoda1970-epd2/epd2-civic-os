"""Tests for `epd2_finance_service.domain` - money, determinism, scope,
identity minimisation and the recorded reason.

This module also carries the `ФИН` coverage register for the whole
finance suite: `FIN_INVARIANT_COVERAGE` maps each of canon 19f.13's
forty-five hard invariants either to the test function that proves it or
to an explicit statement of why this round has no executable test for it.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_finance_service.domain import (
    CURRENCY_SCALE,
    GOVERNED_CURRENCIES,
    PROHIBITED_IDENTITY_KEYS,
    AuthorityReference,
    ConflictDeclaration,
    EvidenceKind,
    EvidenceReference,
    FinancePartyHandle,
    HandlePurpose,
    Money,
    OrganizationalScopeRef,
    PolicyBinding,
    Provenance,
    ProvenanceKind,
    ReasonCoded,
    RequestContext,
    RetentionBinding,
    RoundingRule,
    deterministic_digest,
    reject_identity_payload_keys,
    require_timezone,
    sum_money,
)
from epd2_finance_service.exceptions import (
    AccountingPeriodUndeterminedError,
    CurrencyUnsupportedError,
    EvidenceReferenceMissingError,
    ForbiddenIdentityLinkageError,
    MonetaryAmountInvalidError,
    OrganizationScopeMismatchError,
    OrganizationScopeUndeterminedError,
    PartyHandlePurposeMismatchError,
)

_NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def _scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


def _ungoverned_currency_amount(minor_units: int) -> Money:
    """A `Money` carrying a currency the active policy does not govern.

    The constructor refuses an ungoverned currency outright, so the only
    way to reach the cross-currency arithmetic guard at all is to build a
    governed amount and overwrite the field afterwards - which is exactly
    the state that guard exists to refuse (`ФИН-09`)."""
    amount = Money(minor_units, "EUR")
    object.__setattr__(amount, "currency", "CHF")
    return amount


# =============================================================================
# The ФИН coverage register (canon 19f.13)
# =============================================================================

#: Prefix marking an invariant this round proves by argument rather than by
#: an executable test. The text after it is the honest reason.
NOT_EXECUTABLE = "NOT COVERED BY AN EXECUTABLE TEST: "

#: Each of canon 19f.13's forty-five hard invariants mapped to the test
#: function that proves it, or to a `NOT_EXECUTABLE` explanation.
FIN_INVARIANT_COVERAGE: dict[str, str] = {
    "ФИН-01": "test_no_dataclass_field_in_the_finance_package_is_a_prohibited_identity_key",
    "ФИН-02": "test_an_event_payload_carrying_a_prohibited_identity_key_is_refused",
    "ФИН-03": "test_a_scoped_list_never_returns_another_scopes_record",
    "ФИН-04": "test_an_undetermined_organizational_scope_denies_before_any_other_check",
    "ФИН-05": "test_a_posted_journal_entry_is_content_immutable",
    "ФИН-06": "test_correction_by_reversal_produces_a_reversal_and_leaves_the_original_readable",
    "ФИН-07": "test_a_posted_entry_balances_per_currency",
    "ФИН-08": "test_a_float_monetary_amount_is_refused",
    "ФИН-09": "test_cross_currency_arithmetic_refuses",
    "ФИН-10": "test_posting_into_a_closed_period_is_refused_by_the_command",
    "ФИН-11": "test_reopening_without_dual_control_refuses",
    "ФИН-12": "test_a_budget_summary_projection_has_no_field_for_an_actual_amount",
    "ФИН-13": "test_a_reclassification_that_would_drop_an_obligation_refuses",
    "ФИН-14": "test_split_contributions_inside_one_policy_window_aggregate",
    "ФИН-15": "test_a_related_party_group_reference_changes_the_aggregation_snapshot",
    "ФИН-16": "test_an_anonymous_or_unestablished_contribution_source_refuses",
    "ФИН-17": "test_rejection_return_and_escalation_leave_the_receipt_byte_identical",
    "ФИН-18": "test_an_in_kind_contribution_without_a_valuation_basis_refuses",
    "ФИН-19": "test_sponsorship_approval_without_counter_performance_or_policy_refuses",
    "ФИН-20": "test_a_pack_35_lobbying_subject_refuses",
    "ФИН-21": "test_a_payload_asserting_something_about_a_document_refuses",
    "ФИН-22": "test_a_legal_hold_reference_caches_no_active_flag",
    "ФИН-23": "test_a_classified_transaction_binds_the_policy_version_that_classified_it",
    "ФИН-24": "test_a_frozen_snapshot_cannot_be_replaced",
    "ФИН-25": "test_an_amended_successor_supersedes_a_predecessor_that_stays_readable",
    "ФИН-26": "test_submission_does_not_imply_acknowledgement_nor_acknowledgement_acceptance",
    "ФИН-27": "test_acceptance_from_delivery_telemetry_refuses",
    "ФИН-28": "test_publication_requires_a_separate_authorisation",
    "ФИН-29": "test_the_auditor_fails_the_independence_check_against_a_preparer_or_approver",
    "ФИН-30": "test_the_incompatibility_matrix_refuses_each_canon_listed_pair",
    "ФИН-31": "test_a_claimant_may_not_review_approve_authorise_or_execute_their_own_claim",
    "ФИН-32": "test_an_undeclared_conflict_fails_closed",
    "ФИН-33": "test_preparation_approval_signing_submission_and_publication_are_distinct_acts",
    "ФИН-34": "test_every_projection_is_non_authoritative",
    "ФИН-35": "test_a_small_cell_refuses",
    "ФИН-36": "test_a_forbidden_inbound_reference_kind_refuses",
    "ФИН-37": "test_an_authority_scoped_to_another_organization_may_not_act_in_this_one",
    "ФИН-38": "test_an_imported_transaction_without_a_batch_reference_refuses",
    "ФИН-39": "test_a_naive_datetime_refuses_with_the_accounting_period_undetermined_code",
    "ФИН-40": "test_every_listed_refusal_carries_a_registered_reason_code",
    "ФИН-41": "test_an_unresolvable_authority_refuses_with_the_authority_missing_code",
    "ФИН-42": "test_no_function_in_the_package_accepts_a_bypass_flag_parameter",
    "ФИН-43": (
        NOT_EXECUTABLE + "a disclaimer rule. The invariant says no claim of legal compliance, "
        "authority acceptance or operational readiness follows from the canon "
        "section. There is no code path that could assert or deny it: it "
        "constrains what humans may say about this system, and the package "
        "records it in the `epd2_finance_service` package docstring."
    ),
    "ФИН-44": "test_the_finance_package_imports_no_other_service_package",
    "ФИН-45": "test_a_role_name_alone_is_not_proof_of_authority",
}

#: The canonical register: `ФИН-01` through `ФИН-45`, no more and no fewer.
ALL_FIN_INVARIANTS: tuple[str, ...] = tuple(f"ФИН-{number:02d}" for number in range(1, 46))


def _test_function_names() -> frozenset[str]:
    """Every `def test_*` in this committed suite, read off the source."""
    names: set[str] = set()
    for path in sorted(Path(__file__).parent.glob("test_*.py")):
        names.update(re.findall(r"^def (test_\w+)\(", path.read_text(encoding="utf-8"), re.M))
    return frozenset(names)


def test_every_hard_finance_invariant_appears_in_the_coverage_register() -> None:
    assert set(FIN_INVARIANT_COVERAGE) == set(ALL_FIN_INVARIANTS)


def test_every_claimed_coverage_names_a_test_function_that_exists() -> None:
    available = _test_function_names()
    claimed = {
        invariant: value
        for invariant, value in FIN_INVARIANT_COVERAGE.items()
        if not value.startswith(NOT_EXECUTABLE)
    }
    missing = {invariant: value for invariant, value in claimed.items() if value not in available}
    assert missing == {}


def test_every_uncovered_invariant_states_why_rather_than_being_omitted() -> None:
    uncovered = [
        value for value in FIN_INVARIANT_COVERAGE.values() if value.startswith(NOT_EXECUTABLE)
    ]
    assert uncovered, "the register must name uncovered invariants explicitly, not silently"
    for statement in uncovered:
        assert len(statement) > len(NOT_EXECUTABLE) + 40


# =============================================================================
# Money: integer minor units and nothing else (`ФИН-08`)
# =============================================================================


def test_money_carries_integer_minor_units_with_an_explicit_currency_and_scale() -> None:
    amount = Money(12_345, "EUR")
    assert amount.minor_units == 12_345
    assert amount.currency == "EUR"
    assert amount.scale == CURRENCY_SCALE["EUR"]
    assert amount.rounding is RoundingRule.EXACT


def test_a_float_monetary_amount_is_refused() -> None:
    with pytest.raises(MonetaryAmountInvalidError) as excinfo:
        Money(123.45, "EUR")  # type: ignore[arg-type]
    assert excinfo.value.reason_code == "FINANCE_MONETARY_AMOUNT_INVALID"


def test_a_bool_is_not_an_int_for_a_monetary_amount() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        Money(True, "EUR")


def test_a_decimal_string_amount_is_refused() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        Money("123.45", "EUR")  # type: ignore[arg-type]


def test_a_monetary_payload_carries_no_floating_point_value() -> None:
    payload = Money(-2_500, "EUR").to_payload()
    assert payload == {
        "minor_units": -2_500,
        "currency": "EUR",
        "scale": 2,
        "rounding": "exact",
    }
    assert not any(isinstance(value, float) for value in payload.values())


# =============================================================================
# Currency (`ФИН-09`)
# =============================================================================


def test_cross_currency_arithmetic_refuses() -> None:
    with pytest.raises(CurrencyUnsupportedError) as excinfo:
        Money(1_000, "EUR") + _ungoverned_currency_amount(1_000)
    assert excinfo.value.reason_code == "FINANCE_CURRENCY_UNSUPPORTED"


def test_cross_currency_subtraction_refuses_too() -> None:
    with pytest.raises(CurrencyUnsupportedError):
        Money(1_000, "EUR") - _ungoverned_currency_amount(400)


def test_an_ungoverned_currency_refuses() -> None:
    assert "USD" not in GOVERNED_CURRENCIES
    with pytest.raises(CurrencyUnsupportedError) as excinfo:
        Money(1_000, "USD")
    assert excinfo.value.reason_code == "FINANCE_CURRENCY_UNSUPPORTED"


def test_a_lower_case_currency_code_refuses() -> None:
    with pytest.raises(CurrencyUnsupportedError):
        Money(1_000, "eur")


def test_a_wrong_scale_refuses() -> None:
    with pytest.raises(MonetaryAmountInvalidError) as excinfo:
        Money(1_000, "EUR", 3)
    assert excinfo.value.reason_code == "FINANCE_MONETARY_AMOUNT_INVALID"


def test_sum_money_never_nets_across_currencies() -> None:
    amounts = (Money(1_000, "EUR"), _ungoverned_currency_amount(700), Money(500, "EUR"))
    assert sum_money(amounts) == {"EUR": 1_500, "CHF": 700}


def test_same_currency_arithmetic_stays_exact() -> None:
    assert (Money(1_000, "EUR") + Money(2_345, "EUR")).minor_units == 3_345
    assert (Money(1_000, "EUR") - Money(2_345, "EUR")).minor_units == -1_345
    assert Money(1_000, "EUR").negated() == Money(-1_000, "EUR")


def test_a_zero_value_posting_is_refused_where_a_non_zero_amount_is_required() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        Money(0, "EUR").assert_non_zero(context="posting")
    assert Money(0, "EUR").is_zero is True
    assert Money(1, "EUR").is_positive is True


# =============================================================================
# Time (`ФИН-39`)
# =============================================================================


def test_a_naive_datetime_refuses_with_the_accounting_period_undetermined_code() -> None:
    with pytest.raises(AccountingPeriodUndeterminedError) as excinfo:
        require_timezone(datetime(2026, 3, 1, 12, 0), context="test")
    assert excinfo.value.reason_code == "FINANCE_ACCOUNTING_PERIOD_UNDETERMINED"


def test_a_timezone_explicit_datetime_passes_unchanged() -> None:
    assert require_timezone(_NOW, context="test") == _NOW


def test_a_retention_binding_refuses_a_naive_bound_at() -> None:
    with pytest.raises(AccountingPeriodUndeterminedError):
        RetentionBinding(record_class_reference="finance.record.v1", bound_at=datetime(2026, 3, 1))


def test_a_retention_binding_refuses_an_empty_record_class_reference() -> None:
    with pytest.raises(EvidenceReferenceMissingError):
        RetentionBinding(record_class_reference="   ", bound_at=_NOW)


# =============================================================================
# Determinism (`ФИН-24`)
# =============================================================================


def test_the_content_digest_is_stable_across_calls_and_sensitive_to_input() -> None:
    assert deterministic_digest("a", "b") == deterministic_digest("a", "b")
    assert deterministic_digest("a", "b") != deterministic_digest("b", "a")


# =============================================================================
# Organizational scope (`ФИН-03`, `ФИН-04`)
# =============================================================================


def test_an_undetermined_scope_denies_rather_than_defaulting() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError) as excinfo:
        _scope().assert_matches(None)
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_UNDETERMINED"


def test_a_foreign_scope_raises_the_mismatch_code() -> None:
    with pytest.raises(OrganizationScopeMismatchError) as excinfo:
        _scope().assert_matches(_scope())
    assert excinfo.value.reason_code == "ORGANIZATION_SCOPE_MISMATCH"


def test_a_request_context_without_a_scope_denies_on_require_scope() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError):
        RequestContext(scope=None).require_scope()


def test_an_empty_scope_kind_is_refused() -> None:
    with pytest.raises(OrganizationScopeUndeterminedError):
        OrganizationalScopeRef(organization_id=uuid4(), scope_kind="  ")


# =============================================================================
# Identity minimisation (`ФИН-01`, `ФИН-02`)
# =============================================================================


def test_a_prohibited_identity_key_is_rejected_at_the_top_level() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError) as excinfo:
        reject_identity_payload_keys({"user_id": "u-1"}, context="test")
    assert excinfo.value.reason_code == "FINANCE_FORBIDDEN_IDENTITY_LINKAGE"


def test_a_prohibited_identity_key_nested_one_level_down_is_rejected_too() -> None:
    payload: dict[str, object] = {"outer": [{"inner": {"ballot_id": "b-1"}}]}
    with pytest.raises(ForbiddenIdentityLinkageError):
        reject_identity_payload_keys(payload, context="test")


def test_the_prohibited_key_check_is_case_insensitive() -> None:
    with pytest.raises(ForbiddenIdentityLinkageError):
        reject_identity_payload_keys({"Person_ID": "p-1"}, context="test")


def test_the_prohibited_key_register_covers_the_shapes_the_canon_names() -> None:
    for key in ("user_id", "person_id", "member_id", "ballot_id", "vote_id", "credential_id"):
        assert key in PROHIBITED_IDENTITY_KEYS


def test_a_party_handle_is_usable_only_for_the_purpose_it_was_minted_for() -> None:
    perimeter = _scope()
    handle = FinancePartyHandle(
        handle_id=uuid4(), purpose=HandlePurpose.CONTRIBUTION, perimeter=perimeter
    )
    handle.assert_usable_for(HandlePurpose.CONTRIBUTION, perimeter)
    with pytest.raises(PartyHandlePurposeMismatchError) as excinfo:
        handle.assert_usable_for(HandlePurpose.SPONSORSHIP, perimeter)
    assert excinfo.value.reason_code == "FINANCE_PARTY_HANDLE_PURPOSE_MISMATCH"


def test_a_party_handle_reference_discloses_only_the_purpose_and_the_minted_id() -> None:
    handle_id = uuid4()
    handle = FinancePartyHandle(
        handle_id=handle_id, purpose=HandlePurpose.SPONSORSHIP, perimeter=_scope()
    )
    assert handle.as_reference() == f"fph:sponsorship:{handle_id}"


# =============================================================================
# The recorded reason and the presented authority (`ФИН-40`, `ФИН-45`)
# =============================================================================


def test_a_reason_code_must_be_a_non_empty_upper_case_code() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        ReasonCoded(reason_code="finance_routine_act", authority_reference="board-1")
    with pytest.raises(MonetaryAmountInvalidError):
        ReasonCoded(reason_code="  ", authority_reference="board-1")


def test_a_reason_requires_the_authority_that_invoked_it() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        ReasonCoded(reason_code="FINANCE_ROUTINE_ACT", authority_reference="  ")


def test_an_authority_reference_never_puts_the_actor_on_the_wire() -> None:
    authority = AuthorityReference(
        authority_id=uuid4(),
        role_code="finance_administrator",
        scope=_scope(),
        actor_reference="actor-admin",
    )
    payload = authority.to_payload()
    assert payload["role_code"] == "finance_administrator"
    assert set(payload) == {"authority_id", "role_code", "actor_reference"}


def test_an_authority_requires_a_non_empty_role_code() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        AuthorityReference(authority_id=uuid4(), role_code="  ", scope=_scope())


def test_a_conflict_declaration_distinguishes_undeclared_from_none() -> None:
    undeclared = ConflictDeclaration(state=ConflictDeclaration.UNDECLARED, declared_by="a")
    declared = ConflictDeclaration(state=ConflictDeclaration.NONE, declared_by="a")
    blocking = ConflictDeclaration(state=ConflictDeclaration.BLOCKING, declared_by="a")
    assert undeclared.is_undeclared is True
    assert declared.is_undeclared is False
    assert blocking.is_blocking is True


# =============================================================================
# Provenance, evidence and policy bindings (`ФИН-21`, `ФИН-23`, `ФИН-38`)
# =============================================================================


def test_provenance_requires_a_source_system_and_a_recording_authority() -> None:
    with pytest.raises(MonetaryAmountInvalidError):
        Provenance(
            kind=ProvenanceKind.IMPORTED, source_system_reference="  ", recorded_by_authority="t"
        )
    with pytest.raises(MonetaryAmountInvalidError):
        Provenance(
            kind=ProvenanceKind.IMPORTED, source_system_reference="bank", recorded_by_authority=" "
        )


def test_an_evidence_reference_asserts_nothing_about_the_document() -> None:
    reference = EvidenceReference(
        kind=EvidenceKind.RECEIPT, external_reference="doc-1", scope=_scope()
    )
    assert reference.owner == "pack-11-documents"
    assert set(reference.to_payload()) == {"kind", "owner", "external_reference"}


def test_an_empty_evidence_reference_refuses() -> None:
    with pytest.raises(EvidenceReferenceMissingError):
        EvidenceReference(kind=EvidenceKind.INVOICE, external_reference="  ", scope=_scope())


def test_a_policy_binding_records_the_exact_version_a_decision_used() -> None:
    binding = PolicyBinding(
        policy_kind="income_classification",
        policy_id="income",
        policy_version="2026.1",
        effective_from=date(2026, 1, 1),
    )
    assert binding.to_payload()["policy_version"] == "2026.1"
    assert binding.to_payload()["effective_from"] == "2026-01-01"

"""Concurrency: expected version, conflicts, approvals, transactions
(PACK-13 §6, §7; ADR-077).

The four assertions this file exists for: an expected version that
matches proceeds; a stale one conflicts with a reason code; no path
produces a silent overwrite; and an approval bound to a version that has
since moved is refused rather than applied.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from _data_plane_builders import (
    NOW,
    OTHER_DOMAIN,
    actor,
    aggregate,
    boundary,
    unit_reference,
    version,
)

from epd2_data_plane_service.concurrency import (
    ConcurrencyPolicy,
    ExpectedVersion,
    ExpectedVersionKind,
    OrganizationScopeAssertion,
    TransactionBoundary,
    evaluate_expected_version,
)
from epd2_data_plane_service.domain import ApprovalReference, OrganizationScopeReference
from epd2_data_plane_service.exceptions import (
    ConcurrencyApprovalOnChangedVersionError,
    ConcurrencyAuthorityLapsedError,
    ConcurrencyLastWriteWinsProhibitedError,
    ConcurrencyStaleAggregateVersionError,
    CrossDomainDirectAccessDeniedError,
)


def test_expected_version_match_proceeds_and_increments_by_one() -> None:
    current = version(3)
    next_version = ConcurrencyPolicy.require_proceed(current, ExpectedVersion.exact(3))
    assert next_version.version == 4


def test_stale_expected_version_conflicts_with_its_own_reason_code() -> None:
    current = version(5)
    decision = evaluate_expected_version(current, ExpectedVersion.exact(3))
    assert not decision.proceeds
    assert decision.conflict is not None
    assert decision.conflict.reason_code == "CONCURRENCY_STALE_AGGREGATE_VERSION"
    assert decision.conflict.actual_version == 5
    assert decision.conflict.retry_admissible is True


def test_stale_expected_version_raises_rather_than_overwriting() -> None:
    with pytest.raises(ConcurrencyStaleAggregateVersionError):
        ConcurrencyPolicy.require_proceed(version(5), ExpectedVersion.exact(3))


def test_must_not_exist_and_any_existing_are_distinct_assertions() -> None:
    """`P13-CC-009`: collapsing them makes a create-if-absent silently
    overwrite an existing record."""
    absent = version(0)
    present = version(2)

    assert evaluate_expected_version(absent, ExpectedVersion.must_not_exist()).proceeds
    assert not evaluate_expected_version(present, ExpectedVersion.must_not_exist()).proceeds
    assert evaluate_expected_version(present, ExpectedVersion.any_existing()).proceeds
    assert not evaluate_expected_version(absent, ExpectedVersion.any_existing()).proceeds


def test_create_conflict_is_not_retry_admissible() -> None:
    """Retrying the same create against an existing record can never
    succeed, which is a different fact from a stale version."""
    decision = evaluate_expected_version(version(2), ExpectedVersion.must_not_exist())
    assert decision.conflict is not None
    assert decision.conflict.retry_admissible is False


def test_expected_version_exact_requires_a_version() -> None:
    with pytest.raises(ValueError, match="requires a version"):
        ExpectedVersion(kind=ExpectedVersionKind.EXACT)


def test_expected_version_any_must_not_carry_a_version() -> None:
    with pytest.raises(ValueError, match="must not carry a version"):
        ExpectedVersion(kind=ExpectedVersionKind.ANY_EXISTING, version=3)


def test_last_write_wins_is_refused_for_a_consequential_record() -> None:
    with pytest.raises(ConcurrencyLastWriteWinsProhibitedError):
        ConcurrencyPolicy.reject_last_write_wins(consequential=True, context="finance posting")


def test_last_write_wins_is_admissible_only_where_the_class_says_so() -> None:
    ConcurrencyPolicy.reject_last_write_wins(consequential=False, context="cache hint")


def test_approval_against_a_moved_version_is_returned_for_a_fresh_decision() -> None:
    approval = ApprovalReference(
        approval_id=aggregate().aggregate_id,
        approver=actor(),
        approved_object_version=4,
        decided_at=NOW,
    )
    with pytest.raises(ConcurrencyApprovalOnChangedVersionError):
        ConcurrencyPolicy.require_approval_still_current(approval, version(5))


def test_approval_against_the_same_version_is_accepted() -> None:
    approval = ApprovalReference(
        approval_id=aggregate().aggregate_id,
        approver=actor(),
        approved_object_version=5,
        decided_at=NOW,
    )
    ConcurrencyPolicy.require_approval_still_current(approval, version(5))


def test_authority_is_rechecked_at_execution_not_only_at_construction() -> None:
    with pytest.raises(ConcurrencyAuthorityLapsedError):
        ConcurrencyPolicy.require_authority_effective_at_execution(
            authority_expires_at=NOW,
            executing_at=NOW + timedelta(seconds=1),
            context="migration execution",
        )


def test_authority_still_effective_at_execution_passes() -> None:
    ConcurrencyPolicy.require_authority_effective_at_execution(
        authority_expires_at=NOW + timedelta(hours=1),
        executing_at=NOW,
        context="migration execution",
    )


def test_transaction_boundary_cannot_permit_an_external_effect() -> None:
    """`P13-TX-004` as a constructor refusal rather than a comment."""
    with pytest.raises(ValueError, match="no external side effect"):
        TransactionBoundary(
            owning_domain=boundary().owning_domain,
            schema_name="membership_schema",
            permits_external_effect=True,
        )


def test_unit_of_work_refuses_a_write_to_another_domains_aggregate() -> None:
    unit = unit_reference()
    with pytest.raises(CrossDomainDirectAccessDeniedError):
        unit.assert_same_domain(aggregate(domain=OTHER_DOMAIN))


def test_unit_of_work_accepts_its_own_domains_aggregate() -> None:
    unit_reference().assert_same_domain(aggregate())


def test_scope_assertion_records_a_checkable_fact() -> None:
    assertion = OrganizationScopeAssertion(
        asserted_at_boundary="migration_verification",
        scope=OrganizationScopeReference(
            organization_id=aggregate().aggregate_id,
            scope_kind=unit_reference().scope.scope_kind,
        ),
        record_count=17,
    )
    assert assertion.record_count == 17


def test_aggregate_version_rejects_a_negative_version() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        version(-1)


def test_version_zero_means_does_not_exist() -> None:
    assert version(0).exists is False
    assert version(1).exists is True

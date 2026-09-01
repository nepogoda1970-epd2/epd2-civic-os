"""Tests for epd2_eligibility_service.domain."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from epd2_eligibility_service.domain import (
    EligibilityDecisionValue,
    EligibilitySnapshot,
    compute_snapshot_digest,
    parse_decision_value,
)
from epd2_eligibility_service.exceptions import UnknownEligibilityDecisionValueError


def test_parse_decision_value_accepts_known_values() -> None:
    assert parse_decision_value("eligible") == EligibilityDecisionValue.ELIGIBLE


def test_parse_decision_value_rejects_unknown_value() -> None:
    """CT-00-02: unknown status/value is never accepted."""
    with pytest.raises(UnknownEligibilityDecisionValueError):
        parse_decision_value("super_eligible")


def test_snapshot_digest_is_order_independent() -> None:
    ids = (uuid4(), uuid4(), uuid4())
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    a = compute_snapshot_digest(
        eligibility_rule_id=uuid4(),
        rule_version=1,
        created_at=created_at,
        eligible_decision_ids=ids,
    )
    rule_id = uuid4()
    b1 = compute_snapshot_digest(
        eligibility_rule_id=rule_id,
        rule_version=1,
        created_at=created_at,
        eligible_decision_ids=ids,
    )
    b2 = compute_snapshot_digest(
        eligibility_rule_id=rule_id,
        rule_version=1,
        created_at=created_at,
        eligible_decision_ids=tuple(reversed(ids)),
    )
    assert b1 == b2
    assert isinstance(a, str)
    assert len(a) == 64


def test_snapshot_rejects_mismatched_eligible_count() -> None:
    with pytest.raises(ValueError, match="eligible_count"):
        EligibilitySnapshot(
            eligibility_snapshot_id=uuid4(),
            eligibility_rule_id=uuid4(),
            rule_version=1,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            eligible_decision_ids=(uuid4(), uuid4()),
            eligible_count=1,
            digest="a" * 64,
        )


def test_eligibility_service_has_no_import_dependency_on_identity_service() -> None:
    """Structural boundary check: this package must not *import*
    epd2_identity_service/epd2_account_service (README.md's boundary
    note). Checks actual import statements, not arbitrary text - the
    docstrings in this package legitimately mention those names in
    prose."""
    import ast

    import epd2_eligibility_service.application as application_module
    import epd2_eligibility_service.domain as domain_module

    forbidden = {"epd2_identity_service", "epd2_account_service"}
    for module in (domain_module, application_module):
        source_file = module.__file__
        assert source_file is not None
        with open(source_file, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        assert not (imported_roots & forbidden), (
            f"{source_file} imports {imported_roots & forbidden}"
        )

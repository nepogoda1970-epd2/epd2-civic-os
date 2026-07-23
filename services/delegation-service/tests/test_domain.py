"""Tests for epd2_delegation_service.domain.

Covers every `ALLOWED_TRANSITIONS` pair (plus at least one forbidden
transition) for `Delegation`'s status machine, canon section 16.1's
prohibitions #1 ("self-delegation") and #3 ("hidden indefinite
delegation") as structural `__post_init__` checks, the
`FORBIDDEN_FIELD_NAMES` identity-separation guarantee on both `Delegation`
and `DelegationSnapshot`, and the `DelegationSnapshot` hash helpers'
determinism/order-independence.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_delegation_service.domain import (
    ALLOWED_TRANSITIONS,
    BLOCKING_SCOPE_STATUSES,
    FORBIDDEN_FIELD_NAMES,
    Delegation,
    DelegationSnapshot,
    DelegationStatus,
    compute_delegation_snapshot_hash,
    compute_delegation_snapshot_input_hash,
    parse_delegation_status,
)
from epd2_delegation_service.exceptions import (
    ForbiddenDelegationTransitionError,
    SelfDelegationError,
    UnknownDelegationStatusError,
)

_VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)
_VALID_UNTIL = datetime(2026, 6, 1, tzinfo=UTC)


def _make_delegation(**overrides: object) -> Delegation:
    defaults: dict[str, object] = {
        "delegation_id": uuid4(),
        "delegator_actor_id": uuid4(),
        "delegate_actor_id": uuid4(),
        "scope_type": "ballot",
        "scope_id": uuid4(),
        "valid_from": _VALID_FROM,
        "valid_until": _VALID_UNTIL,
        "revocation_status": "none",
        "status": DelegationStatus.DRAFT,
    }
    defaults.update(overrides)
    return Delegation(**defaults)  # type: ignore[arg-type]


def _make_snapshot(**overrides: object) -> DelegationSnapshot:
    defaults: dict[str, object] = {
        "delegation_snapshot_id": uuid4(),
        "ballot_id": uuid4(),
        "policy_version": 1,
        "created_at": datetime(2026, 1, 2, tzinfo=UTC),
        "input_hash": "a" * 64,
        "resolved_weights": {},
        "cycle_records": (),
        "snapshot_hash": "b" * 64,
    }
    defaults.update(overrides)
    return DelegationSnapshot(**defaults)  # type: ignore[arg-type]


# --- Delegation status machine ----------------------------------------------


def test_parse_delegation_status_accepts_known_values() -> None:
    assert parse_delegation_status("active") == DelegationStatus.ACTIVE


def test_parse_delegation_status_rejects_unknown_value() -> None:
    with pytest.raises(UnknownDelegationStatusError):
        parse_delegation_status("super_active")


@pytest.mark.parametrize("current,target", sorted(ALLOWED_TRANSITIONS))
def test_every_allowed_delegation_transition_succeeds(
    current: DelegationStatus, target: DelegationStatus
) -> None:
    delegation = _make_delegation(status=current)
    updated = delegation.with_status(target)
    assert updated.status == target


def test_delegation_revoked_is_terminal() -> None:
    delegation = _make_delegation(status=DelegationStatus.REVOKED)
    with pytest.raises(ForbiddenDelegationTransitionError):
        delegation.with_status(DelegationStatus.ACTIVE)


def test_delegation_forbidden_transition_draft_to_revoked() -> None:
    delegation = _make_delegation(status=DelegationStatus.DRAFT)
    with pytest.raises(ForbiddenDelegationTransitionError):
        delegation.with_status(DelegationStatus.REVOKED)


def test_delegation_invalid_is_terminal() -> None:
    delegation = _make_delegation(status=DelegationStatus.INVALID)
    with pytest.raises(ForbiddenDelegationTransitionError):
        delegation.with_status(DelegationStatus.DRAFT)


def test_blocking_scope_statuses_are_draft_and_active() -> None:
    """Documented choice (README.md): a `draft` already reserves its scope
    triple, not just `active`."""
    assert {DelegationStatus.DRAFT, DelegationStatus.ACTIVE} == BLOCKING_SCOPE_STATUSES


# --- Prohibition #1: self-delegation ----------------------------------------


def test_self_delegation_is_rejected_structurally() -> None:
    """Canon section 16.1 prohibition #1 ("самоделегирование")."""
    actor_id = uuid4()
    with pytest.raises(SelfDelegationError):
        _make_delegation(delegator_actor_id=actor_id, delegate_actor_id=actor_id)


# --- Prohibition #3: hidden indefinite delegation ---------------------------


def test_valid_until_none_is_an_explicit_choice_and_is_accepted() -> None:
    """An explicit `None` (indefinite delegation) is accepted - it is only
    ever rejected if it is set to a nonsensical (non-future) instant."""
    delegation = _make_delegation(valid_until=None)
    assert delegation.valid_until is None


def test_valid_until_must_be_strictly_after_valid_from() -> None:
    with pytest.raises(ValueError, match="valid_until"):
        _make_delegation(valid_from=_VALID_UNTIL, valid_until=_VALID_FROM)


def test_valid_until_equal_to_valid_from_is_rejected() -> None:
    with pytest.raises(ValueError, match="valid_until"):
        _make_delegation(valid_from=_VALID_FROM, valid_until=_VALID_FROM)


def test_delegation_requires_timezone_aware_valid_from() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_delegation(valid_from=datetime(2026, 1, 1))


def test_delegation_requires_timezone_aware_valid_until() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_delegation(valid_until=datetime(2026, 6, 1))


def test_delegation_rejects_empty_scope_type() -> None:
    with pytest.raises(ValueError, match="scope_type"):
        _make_delegation(scope_type="")


# --- Identity-separation ------------------------------------------------------


def test_delegation_has_no_forbidden_identity_field() -> None:
    field_names = set(Delegation.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)
    assert "account_id" not in field_names
    assert "identity_record_id" not in field_names
    assert "person_id" not in field_names


def test_delegation_snapshot_has_no_forbidden_identity_field() -> None:
    field_names = set(DelegationSnapshot.__dataclass_fields__)
    assert not (field_names & FORBIDDEN_FIELD_NAMES)


def test_no_code_path_imports_voting_service_or_pack_02(tmp_path: Path) -> None:
    """Structural boundary check (ADR-008): this package imports neither
    `epd2_voting_service` (PACK-03<->PACK-03 forbidden) nor any PACK-02
    service package."""
    import epd2_delegation_service

    package_dir = Path(inspect.getfile(epd2_delegation_service)).parent
    forbidden_modules = {
        "epd2_voting_service",
        "epd2_account_service",
        "epd2_identity_service",
        "epd2_eligibility_service",
        "epd2_credential_service",
    }

    for py_file in package_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden_modules, (
                        f"{py_file.name} imports forbidden module {alias.name!r}"
                    )
            elif isinstance(node, ast.ImportFrom):
                assert node.module is not None
                assert node.module.split(".")[0] not in forbidden_modules, (
                    f"{py_file.name} imports from forbidden module {node.module!r}"
                )


# --- DelegationSnapshot -------------------------------------------------------


def test_snapshot_requires_timezone_aware_created_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _make_snapshot(created_at=datetime(2026, 1, 1))


def test_snapshot_rejects_non_positive_weight() -> None:
    with pytest.raises(ValueError, match="resolved_weights"):
        _make_snapshot(resolved_weights={uuid4(): 0})


def test_snapshot_rejects_policy_version_below_one() -> None:
    with pytest.raises(ValueError, match="policy_version"):
        _make_snapshot(policy_version=0)


def test_compute_delegation_snapshot_input_hash_is_deterministic() -> None:
    kwargs = dict(
        ballot_id=uuid4(),
        policy_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        delegator_actor_ids=frozenset({uuid4(), uuid4()}),
        direct_voters=frozenset(),
    )
    a = compute_delegation_snapshot_input_hash(**kwargs)  # type: ignore[arg-type]
    b = compute_delegation_snapshot_input_hash(**kwargs)  # type: ignore[arg-type]
    assert a == b
    assert len(a) == 64


def test_compute_delegation_snapshot_input_hash_is_order_independent() -> None:
    ids = (uuid4(), uuid4(), uuid4())
    ballot_id = uuid4()
    scope_id = uuid4()
    a = compute_delegation_snapshot_input_hash(
        ballot_id=ballot_id,
        policy_version=1,
        scope_type="ballot",
        scope_id=scope_id,
        delegator_actor_ids=frozenset(ids),
        direct_voters=frozenset(),
    )
    b = compute_delegation_snapshot_input_hash(
        ballot_id=ballot_id,
        policy_version=1,
        scope_type="ballot",
        scope_id=scope_id,
        delegator_actor_ids=frozenset(reversed(ids)),
        direct_voters=frozenset(),
    )
    assert a == b


def test_compute_delegation_snapshot_input_hash_changes_with_direct_voters() -> None:
    delegator = uuid4()
    common = dict(
        ballot_id=uuid4(),
        policy_version=1,
        scope_type="ballot",
        scope_id=uuid4(),
        delegator_actor_ids=frozenset({delegator}),
    )
    a = compute_delegation_snapshot_input_hash(direct_voters=frozenset(), **common)  # type: ignore[arg-type]
    b = compute_delegation_snapshot_input_hash(direct_voters=frozenset({delegator}), **common)  # type: ignore[arg-type]
    assert a != b


def test_compute_delegation_snapshot_hash_changes_with_resolved_weights() -> None:
    delegate = uuid4()
    a = compute_delegation_snapshot_hash(input_hash="a" * 64, resolved_weights={}, cycle_records=())
    b = compute_delegation_snapshot_hash(
        input_hash="a" * 64, resolved_weights={delegate: 1}, cycle_records=()
    )
    assert a != b


def test_compute_delegation_snapshot_hash_is_independent_of_cycle_record_order() -> None:
    a = compute_delegation_snapshot_hash(
        input_hash="a" * 64, resolved_weights={}, cycle_records=("x", "y")
    )
    b = compute_delegation_snapshot_hash(
        input_hash="a" * 64, resolved_weights={}, cycle_records=("y", "x")
    )
    assert a == b


def test_close_time_after_open_time_smoke() -> None:
    delegation = _make_delegation()
    assert delegation.valid_until is not None
    assert delegation.valid_until > delegation.valid_from
    assert delegation.valid_until - delegation.valid_from == timedelta(days=151)

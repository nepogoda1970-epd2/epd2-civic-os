"""PACK-15 voting context registry persistence.

The registry is the one store both sides read, so what it *cannot* hold
is the interesting part: no participant, no assertion, no credential, no
ballot, no turnout figure. A registry row is administrative configuration,
and that is why an eligibility-side read of it creates no edge ADR-089
forbids.

The other property under test is version immutability. A frozen rule set
is only frozen if the row recording it cannot be edited after activation;
otherwise the version someone voted under can change underneath them.
"""

from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_core.sqlite_migrations import (
    foreign_keys,
    load_artefacts,
    table_columns,
    table_names,
)
from epd2_governance_service.voting_context_sql_storage import (
    MIGRATIONS_DIR,
    PACK15_GOVERNANCE_MIGRATIONS,
    SqlVotingContextStore,
    open_voting_context_registry,
)
from epd2_governance_service.voting_contexts import (
    DisclosureControlProfile,
    VotingContext,
    VotingContextStatus,
    VotingType,
    VotingWindow,
)

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)

#: No registry column may name any of these. A registry that could hold
#: one of them would make "read the registry" a way to learn a fact about
#: a person.
FORBIDDEN_REGISTRY_COLUMNS = frozenset(
    {
        "participant_reference",
        "account_id",
        "person_id",
        "membership_id",
        "case_id",
        "assertion_id",
        "nonce",
        "voting_credential_id",
        "credential_id",
        "redemption_reference",
        "ballot_id",
        "vote_content",
        "turnout",
        "votes_cast",
    }
)


@pytest.fixture
def registry() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_voting_context_registry(Path(directory) / "registry.db", applied_at=NOW)
        try:
            yield connection
        finally:
            connection.close()


def _context(
    *,
    version: int = 1,
    status: VotingContextStatus = VotingContextStatus.DRAFT,
    reference: str = "vc-1",
) -> VotingContext:
    window = VotingWindow(starts_at=NOW + timedelta(days=1), ends_at=NOW + timedelta(days=3))
    issuance = VotingWindow(starts_at=NOW, ends_at=NOW + timedelta(days=2))
    return VotingContext(
        voting_context_id=uuid4(),
        voting_context_reference=reference,
        version=version,
        voting_type=VotingType.INTERNAL_PARTY_VOTE,
        organizational_scope="DE-BE",
        status=status,
        voting_window=window,
        credential_issuance_window=issuance,
        revocation_cutoff=window.starts_at,
        eligibility_rule_set_reference="rs-1",
        eligibility_rule_set_version="1.0.0",
        required_assurance="substantial",
        participation_class="full_member",
        privacy_profile="standard",
        audit_profile="standard",
        disclosure_control=DisclosureControlProfile(),
        eligible_population=400,
    )


# =============================================================================
# 1. What the registry cannot hold
# =============================================================================


def test_the_registry_holds_exactly_one_table(registry: sqlite3.Connection) -> None:
    assert set(table_names(registry)) - {"schema_migration"} == {"voting_context"}


def test_no_registry_column_names_a_participant_or_a_ballot(
    registry: sqlite3.Connection,
) -> None:
    columns = set(table_columns(registry, "voting_context"))
    offending = sorted(columns & FORBIDDEN_REGISTRY_COLUMNS)
    assert not offending, f"the registry carries: {offending}"


def test_the_registry_has_no_foreign_key_at_all(registry: sqlite3.Connection) -> None:
    """A key out of the registry is a read edge into whatever it points
    at, which is how a configuration store quietly becomes a join path."""
    for table in table_names(registry):
        assert foreign_keys(registry, table) == ()


def test_the_disclosure_floor_is_a_database_constraint(registry: sqlite3.Connection) -> None:
    """The floor of five is refused below by the CHECK, not only by the
    dataclass - an operator editing the row directly hits it too."""
    with pytest.raises(sqlite3.IntegrityError):
        registry.execute(
            "INSERT INTO voting_context (voting_context_reference, version, voting_context_id, "
            "voting_type, organizational_scope, status, voting_window_start, voting_window_end, "
            "issuance_window_start, issuance_window_end, revocation_cutoff, rule_set_reference, "
            "rule_set_version, required_assurance, participation_class, privacy_profile, "
            "audit_profile, disclosure_minimum_cell, small_electorate, "
            "per_scope_metrics_permitted, eligible_population, document) "
            "VALUES ('vc-x', 1, 'id', 'internal_party_vote', 'DE-BE', 'draft', 'a', 'z', 'a', 'y', "
            "'a', 'rs', '1', 'substantial', 'full_member', 'standard', 'standard', 4, 0, 1, "
            "10, '{}')"
        )


# =============================================================================
# 2. Round-trip and versioning
# =============================================================================


def test_a_context_round_trips(registry: sqlite3.Connection) -> None:
    store = SqlVotingContextStore(registry)
    context = _context()
    store.save(context)
    assert store.get("vc-1", 1) == context


def test_an_activated_context_round_trips_with_its_snapshot(
    registry: sqlite3.Connection,
) -> None:
    store = SqlVotingContextStore(registry)
    activated = _context(status=VotingContextStatus.CONFIGURED).activate(
        now=NOW, approver="ops", second_approver="governance"
    )
    store.save(activated)
    stored = store.get("vc-1", 1)
    assert stored == activated
    assert stored is not None
    assert stored.activation_snapshot is not None
    assert stored.activation_snapshot.snapshot_digest == (
        activated.activation_snapshot.snapshot_digest  # type: ignore[union-attr]
    )


def test_versions_are_separate_rows_and_the_latest_is_the_highest(
    registry: sqlite3.Connection,
) -> None:
    store = SqlVotingContextStore(registry)
    store.save(_context(version=1))
    store.save(_context(version=2))
    store.save(_context(version=3))
    assert tuple(item.version for item in store.versions("vc-1")) == (1, 2, 3)
    latest = store.latest("vc-1")
    assert latest is not None and latest.version == 3


def test_an_activated_version_is_not_editable_in_place(registry: sqlite3.Connection) -> None:
    """A change after activation is a new version, never an overwrite.

    `save` only updates a row whose activation snapshot is still null, so
    a second write against an activated version leaves the frozen
    parameters exactly where they were.
    """
    store = SqlVotingContextStore(registry)
    activated = _context(status=VotingContextStatus.CONFIGURED).activate(
        now=NOW, approver="ops", second_approver="governance"
    )
    store.save(activated)

    drifted = VotingContext(
        voting_context_id=activated.voting_context_id,
        voting_context_reference=activated.voting_context_reference,
        version=activated.version,
        voting_type=activated.voting_type,
        organizational_scope="DE-BY",
        status=VotingContextStatus.ISSUANCE_OPEN,
        voting_window=activated.voting_window,
        credential_issuance_window=activated.credential_issuance_window,
        revocation_cutoff=activated.revocation_cutoff,
        eligibility_rule_set_reference=activated.eligibility_rule_set_reference,
        eligibility_rule_set_version="9.9.9",
        required_assurance=activated.required_assurance,
        participation_class=activated.participation_class,
        privacy_profile=activated.privacy_profile,
        audit_profile=activated.audit_profile,
        disclosure_control=activated.disclosure_control,
        eligible_population=activated.eligible_population,
        activation_snapshot=activated.activation_snapshot,
    )
    store.save(drifted)

    stored = store.get("vc-1", 1)
    assert stored is not None
    assert stored.organizational_scope == "DE-BE"
    assert stored.eligibility_rule_set_version == "1.0.0"
    assert stored.status is VotingContextStatus.ACTIVE


def test_a_draft_version_may_still_be_corrected_in_place(registry: sqlite3.Connection) -> None:
    """Before activation nothing is frozen, so editing a draft is
    ordinary work rather than a violation."""
    store = SqlVotingContextStore(registry)
    draft = _context()
    store.save(draft)
    store.save(_context(status=VotingContextStatus.ACTIVE))
    stored = store.get("vc-1", 1)
    assert stored is not None
    assert stored.status is VotingContextStatus.ACTIVE


def test_two_contexts_do_not_collide_on_version_number(registry: sqlite3.Connection) -> None:
    store = SqlVotingContextStore(registry)
    store.save(_context(reference="vc-1"))
    store.save(_context(reference="vc-2"))
    assert store.get("vc-1", 1) is not None
    assert store.get("vc-2", 1) is not None
    assert store.latest("vc-3") is None


# =============================================================================
# 3. Migrations
# =============================================================================


def test_every_declared_migration_has_a_file() -> None:
    assert load_artefacts(PACK15_GOVERNANCE_MIGRATIONS, MIGRATIONS_DIR)


def test_applying_the_migrations_twice_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "registry.db"
        first = open_voting_context_registry(path, applied_at=NOW)
        before = table_names(first)
        first.close()
        second = open_voting_context_registry(path, applied_at=NOW)
        try:
            assert table_names(second) == before
            row = second.execute("SELECT COUNT(*) AS n FROM schema_migration").fetchone()
            assert row["n"] == len(PACK15_GOVERNANCE_MIGRATIONS)
        finally:
            second.close()

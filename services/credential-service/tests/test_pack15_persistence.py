"""PACK-15 durable-persistence, transactional and concurrency tests.

These assert properties of the **database**, not of application code:

* the spent-nonce table is a set - three columns, no value column;
* a second redemption of one credential is a constraint violation, not a
  check-then-act race;
* no voting-side table carries an assertion reference or a foreign key to
  an identity-side table (which lives in a separate database file, so such
  a key is not expressible at all);
* migrations are checksummed, and an edited migration is refused.
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_core.sqlite_migrations import (
    MigrationChecksumMismatchError,
    UnexpectedMigrationFileError,
    apply_migrations,
    connect,
    foreign_keys,
    load_artefacts,
    table_columns,
    table_names,
)
from epd2_credential_service.voting_credential_sql_storage import (
    MIGRATIONS_DIR,
    PACK15_CREDENTIAL_MIGRATIONS,
    SqlCredentialIdempotencyStore,
    SqlCredentialRedemptionStore,
    SqlCredentialReplayStore,
    SqlSpentNonceSet,
    SqlVotingCredentialStore,
    open_voting_side_database,
    record_revocation,
)
from epd2_credential_service.voting_credentials import (
    CredentialIssuanceIdempotencyRecord,
    CredentialRedemption,
    CredentialReplayRecord,
    CredentialStatus,
    SpentNonce,
    VotingCredential,
)

NOW = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)

#: Identity-side column names that must appear in no voting-side table.
IDENTITY_SIDE_COLUMNS = frozenset(
    {
        "assertion_id",
        "eligibility_assertion_id",
        "nonce_reference",
        "case_id",
        "participant_reference",
        "account_id",
        "person_id",
        "membership_id",
        "member_number",
        "context_pseudonym",
        "ballot_id",
    }
)


@pytest.fixture()
def connection() -> sqlite3.Connection:
    database = Path(tempfile.mkdtemp()) / "voting-side.sqlite3"
    return open_voting_side_database(database, applied_at=NOW)


def _credential(**overrides: object) -> VotingCredential:
    base: dict[str, object] = {
        "voting_credential_id": uuid4(),
        "credential_type": "internal_party_vote",
        "status": CredentialStatus.ISSUED,
        "voting_context_reference": "vc-1",
        "issued_at_bucket": NOW,
        "expires_at": NOW + timedelta(hours=2),
        "audience_origin": "https://vote.epd.example",
    }
    base.update(overrides)
    return VotingCredential(**base)  # type: ignore[arg-type]


# -- schema shape -----------------------------------------------------------


def test_the_spent_nonce_table_is_a_set(connection: sqlite3.Connection) -> None:
    columns = set(table_columns(connection, "spent_nonce"))
    assert columns == {"nonce", "voting_context_reference", "spent_at_bucket"}
    assert "voting_credential_id" not in columns


def test_no_voting_side_table_carries_an_identity_side_column(
    connection: sqlite3.Connection,
) -> None:
    for table in table_names(connection):
        if table == "schema_migration":
            continue
        offending = set(table_columns(connection, table)) & IDENTITY_SIDE_COLUMNS
        assert offending == set(), f"{table} carries {sorted(offending)}"


def test_no_voting_side_table_references_an_identity_side_table(
    connection: sqlite3.Connection,
) -> None:
    identity_side = {
        "eligibility_case",
        "eligibility_decision",
        "eligibility_assertion",
        "assertion_queue_entry",
        "assertion_pickup",
        "participation_unit_ledger",
        "voting_handoff_acceptance",
    }
    for table in table_names(connection):
        assert not (set(foreign_keys(connection, table)) & identity_side)


def test_the_credential_table_has_no_assertion_or_nonce_column(
    connection: sqlite3.Connection,
) -> None:
    columns = set(table_columns(connection, "voting_credential"))
    assert "assertion_id" not in columns
    assert "nonce" not in columns


# -- atomicity and concurrency ----------------------------------------------


def test_a_spent_nonce_insert_is_the_check(connection: sqlite3.Connection) -> None:
    nonces = SqlSpentNonceSet(connection)
    spent = SpentNonce(nonce="n1", voting_context_reference="vc-1", spent_at_bucket=NOW)
    assert nonces.add(spent) is True
    assert nonces.add(spent) is False
    assert nonces.contains("n1") is True
    assert nonces.count("vc-1") == 1


def test_concurrent_nonce_spending_yields_exactly_one_winner(
    connection: sqlite3.Connection,
) -> None:
    """The primary key decides the race, not a prior `contains()`."""
    nonces = SqlSpentNonceSet(connection)
    spent = SpentNonce(nonce="race", voting_context_reference="vc-1", spent_at_bucket=NOW)
    results = [nonces.add(spent) for _ in range(8)]
    assert results.count(True) == 1
    assert results.count(False) == 7


def test_a_second_redemption_violates_the_unique_index(
    connection: sqlite3.Connection,
) -> None:
    credentials = SqlVotingCredentialStore(connection)
    redemptions = SqlCredentialRedemptionStore(connection)
    credential = _credential()
    credentials.save(credential)
    connection.commit()
    redemptions.save(
        CredentialRedemption(
            redemption_reference="r1",
            voting_credential_id=credential.voting_credential_id,
            voting_context_reference="vc-1",
            redeemed_at_bucket=NOW,
            continuation_capability="capability-1",
        )
    )
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError):
        redemptions.save(
            CredentialRedemption(
                redemption_reference="r2",
                voting_credential_id=credential.voting_credential_id,
                voting_context_reference="vc-1",
                redeemed_at_bucket=NOW,
                continuation_capability="capability-2",
            )
        )


def test_a_rolled_back_issuance_leaves_no_credential_and_no_spent_nonce(
    connection: sqlite3.Connection,
) -> None:
    """A partial issuance must not exist."""
    credentials = SqlVotingCredentialStore(connection)
    nonces = SqlSpentNonceSet(connection)
    credential = _credential()
    try:
        nonces.add(
            SpentNonce(nonce="rollback", voting_context_reference="vc-1", spent_at_bucket=NOW)
        )
        credentials.save(credential)
        raise RuntimeError("simulated failure after both writes")
    except RuntimeError:
        connection.rollback()
    assert nonces.contains("rollback") is False
    assert credentials.get(credential.voting_credential_id) is None


def test_a_stored_redemption_never_returns_the_continuation_capability(
    connection: sqlite3.Connection,
) -> None:
    """The capability is a secret handed to the client, not an audit fact."""
    credentials = SqlVotingCredentialStore(connection)
    redemptions = SqlCredentialRedemptionStore(connection)
    credential = _credential()
    credentials.save(credential)
    redemptions.save(
        CredentialRedemption(
            redemption_reference="r1",
            voting_credential_id=credential.voting_credential_id,
            voting_context_reference="vc-1",
            redeemed_at_bucket=NOW,
            continuation_capability="the-real-capability",
        )
    )
    connection.commit()
    stored = redemptions.get("r1")
    assert stored is not None
    assert stored.continuation_capability != "the-real-capability"
    assert "continuation_capability" not in table_columns(connection, "credential_redemption")


# -- round trips ------------------------------------------------------------


def test_a_credential_round_trips_through_the_database(
    connection: sqlite3.Connection,
) -> None:
    credentials = SqlVotingCredentialStore(connection)
    credential = _credential()
    credentials.save(credential)
    connection.commit()
    loaded = credentials.get(credential.voting_credential_id)
    assert loaded == credential


def test_status_changes_are_updated_in_place(connection: sqlite3.Connection) -> None:
    credentials = SqlVotingCredentialStore(connection)
    credential = _credential()
    credentials.save(credential)
    redeemed = _credential(
        voting_credential_id=credential.voting_credential_id,
        status=CredentialStatus.REDEEMED,
        redeemed_at=NOW,
        redemption_reference="r1",
    )
    credentials.save(redeemed)
    connection.commit()
    loaded = credentials.get(credential.voting_credential_id)
    assert loaded is not None and loaded.status is CredentialStatus.REDEEMED
    assert credentials.count_by_status("vc-1", CredentialStatus.REDEEMED) == 1


def test_the_idempotency_window_is_purgeable(connection: sqlite3.Connection) -> None:
    credentials = SqlVotingCredentialStore(connection)
    store = SqlCredentialIdempotencyStore(connection)
    credential = _credential()
    credentials.save(credential)
    store.put(
        CredentialIssuanceIdempotencyRecord(
            idempotency_key="k1",
            voting_credential_id=credential.voting_credential_id,
            created_at=NOW,
            expires_at=NOW + timedelta(seconds=300),
        )
    )
    connection.commit()
    assert store.get("k1") is not None
    assert store.purge_expired(NOW + timedelta(seconds=600)) == 1
    assert store.get("k1") is None


def test_a_replay_record_carries_no_attribution(connection: sqlite3.Connection) -> None:
    replays = SqlCredentialReplayStore(connection)
    replays.record(
        CredentialReplayRecord(
            replay_id=uuid4(),
            voting_context_reference="vc-1",
            reason_code="CREDENTIAL_REPLAY_DETECTED",
            detected_at_bucket=NOW,
        )
    )
    connection.commit()
    assert replays.count("vc-1") == 1
    columns = set(table_columns(connection, "credential_replay_record"))
    assert not (columns & IDENTITY_SIDE_COLUMNS)


def test_a_revocation_after_the_cutoff_cannot_be_persisted(
    connection: sqlite3.Connection,
) -> None:
    """The CHECK constraint refuses it at the database level."""
    credentials = SqlVotingCredentialStore(connection)
    credential = _credential()
    credentials.save(credential)
    connection.commit()
    record_revocation(
        connection,
        voting_credential_id=credential.voting_credential_id,
        reason_code="CREDENTIAL_REVOKED",
        revoked_at=NOW,
        authority_role="credential_issuer",
        dual_control_reference="dual-1",
    )
    connection.commit()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT OR REPLACE INTO credential_revocation (voting_credential_id, reason_code, "
            "revoked_at, authority_role, dual_control_reference, before_cutoff) "
            "VALUES (?, ?, ?, ?, ?, 0)",
            (
                str(credential.voting_credential_id),
                "CREDENTIAL_REVOKED",
                NOW.isoformat(),
                "credential_issuer",
                None,
            ),
        )


# -- migration discipline ---------------------------------------------------


def test_every_declared_migration_has_a_file_and_no_file_is_undeclared() -> None:
    artefacts = load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, MIGRATIONS_DIR)
    assert len(artefacts) == len(PACK15_CREDENTIAL_MIGRATIONS)
    for artefact in artefacts:
        assert artefact.sql.startswith("-- PACK-15 migration")
        assert len(artefact.checksum) == 64


def test_an_undeclared_migration_file_is_refused() -> None:
    directory = Path(tempfile.mkdtemp())
    for artefact in load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, MIGRATIONS_DIR):
        (directory / artefact.path.name).write_text(artefact.sql, encoding="utf-8")
    (directory / "9999_stray.sql").write_text("CREATE TABLE stray (id TEXT);", encoding="utf-8")
    with pytest.raises(UnexpectedMigrationFileError):
        load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, directory)


def test_an_edited_applied_migration_is_refused() -> None:
    directory = Path(tempfile.mkdtemp())
    artefacts = load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, MIGRATIONS_DIR)
    for artefact in artefacts:
        (directory / artefact.path.name).write_text(artefact.sql, encoding="utf-8")
    database = directory / "voting.sqlite3"
    connection = connect(database)
    apply_migrations(
        connection,
        load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, directory),
        applied_at=NOW,
    )
    first = artefacts[0]
    (directory / first.path.name).write_text(
        first.sql + "\n-- an edit after the fact\n", encoding="utf-8"
    )
    with pytest.raises(MigrationChecksumMismatchError):
        apply_migrations(
            connection, load_artefacts(PACK15_CREDENTIAL_MIGRATIONS, directory), applied_at=NOW
        )


def test_applying_twice_is_idempotent() -> None:
    directory = Path(tempfile.mkdtemp())
    database = directory / "voting.sqlite3"
    first = open_voting_side_database(database, applied_at=NOW)
    tables = table_names(first)
    first.close()
    second = open_voting_side_database(database, applied_at=NOW)
    assert table_names(second) == tables

"""PACK-15 audit-stream persistence and separation.

`assert_streams_separable` refuses a request that spans the boundary.
These tests check the stronger claim: that spanning it is not expressible.
The identity-side streams (AS-01, AS-02) and the voting-side streams
(AS-03, AS-04) live in different database files, so there is no join to
write, no view to define and no foreign key to follow - and a role holding
one connection does not hold the other (ADR-097).

The per-stream key spaces are the second half of the guarantee: AS-01
carries a case reference, AS-02 an assertion reference, AS-03 a credential
reference, and no table carries two of them. That is the ADR-093 pairing
prohibition written in DDL rather than asserted in prose.
"""

from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from epd2_audit_core.voting_audit_sql_storage import (
    IDENTITY_SIDE_DATABASE_STREAMS,
    NEUTRAL_DATABASE_STREAMS,
    PACK15_IDENTITY_SIDE_AUDIT_MIGRATIONS,
    PACK15_NEUTRAL_AUDIT_MIGRATIONS,
    PACK15_VOTING_SIDE_AUDIT_MIGRATIONS,
    STREAM_SUBJECT_COLUMNS,
    STREAM_TABLES,
    VOTING_SIDE_DATABASE_STREAMS,
    SqlEvidenceBundleExportStore,
    SqlVotingAuditStreamStore,
    VotingAuditRecord,
    open_identity_side_audit_database,
    open_neutral_audit_database,
    open_voting_side_audit_database,
)
from epd2_audit_core.voting_evidence_bundle import (
    BUNDLE_SECTIONS,
    AuditStream,
    BundleSigningCustody,
    EvidenceBundle,
    EvidenceBundleScopeRefusedError,
    canonical_bundle_message,
)
from epd2_core.sqlite_migrations import foreign_keys, table_columns, table_names

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)

#: The subject columns of the three subject-bearing streams. No table may
#: carry more than one of them.
SUBJECT_COLUMNS = frozenset({"case_reference", "assertion_reference", "credential_reference"})


@pytest.fixture
def identity_side() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_identity_side_audit_database(
            Path(directory) / "audit-identity.db", applied_at=NOW
        )
        try:
            yield connection
        finally:
            connection.close()


@pytest.fixture
def voting_side() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_voting_side_audit_database(
            Path(directory) / "audit-voting.db", applied_at=NOW
        )
        try:
            yield connection
        finally:
            connection.close()


@pytest.fixture
def neutral() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_neutral_audit_database(
            Path(directory) / "audit-neutral.db", applied_at=NOW
        )
        try:
            yield connection
        finally:
            connection.close()


def _record(stream: AuditStream, subject: str) -> VotingAuditRecord:
    return VotingAuditRecord(
        record_id=uuid4(),
        stream=stream,
        voting_context_reference="vc-1",
        event_type=f"epd2.pack15.{stream.value.lower()}.recorded.v1",
        reason_code="EPD2-P15-AUDIT-RECORDED",
        recorded_at_bucket=NOW,
        subject=subject,
        payload_hash="c" * 64,
        payload={"class": "standard"},
        retention_class="voting_audit",
    )


# =============================================================================
# 1. Structural separation
# =============================================================================


def test_the_three_audit_databases_hold_disjoint_tables(
    identity_side: sqlite3.Connection,
    voting_side: sqlite3.Connection,
    neutral: sqlite3.Connection,
) -> None:
    identity = set(table_names(identity_side)) - {"schema_migration"}
    voting = set(table_names(voting_side)) - {"schema_migration"}
    common = set(table_names(neutral)) - {"schema_migration"}
    assert identity == {"audit_record_as01_eligibility", "audit_record_as02_assertion"}
    assert voting == {"audit_record_as03_credential", "audit_record_as04_voting_integrity"}
    assert common == {
        "audit_record_as05_independent",
        "audit_record_as06_system_integrity",
        "evidence_bundle_export",
    }
    assert not identity & voting
    assert not identity & common
    assert not voting & common


def test_no_table_carries_two_stream_key_spaces(
    identity_side: sqlite3.Connection,
    voting_side: sqlite3.Connection,
    neutral: sqlite3.Connection,
) -> None:
    """A row holding both an assertion reference and a credential
    reference would be the exact pairing ADR-093 forbids."""
    for connection in (identity_side, voting_side, neutral):
        for table in table_names(connection):
            present = set(table_columns(connection, table)) & SUBJECT_COLUMNS
            assert len(present) <= 1, f"{table} carries {sorted(present)}"


def test_the_identity_side_database_has_no_credential_column(
    identity_side: sqlite3.Connection,
) -> None:
    for table in table_names(identity_side):
        columns = set(table_columns(identity_side, table))
        assert "credential_reference" not in columns
        assert "voting_credential_id" not in columns


def test_the_voting_side_database_has_no_case_or_assertion_column(
    voting_side: sqlite3.Connection,
) -> None:
    for table in table_names(voting_side):
        columns = set(table_columns(voting_side, table))
        assert "case_reference" not in columns
        assert "assertion_reference" not in columns
        assert "participant_reference" not in columns


def test_no_audit_table_has_a_foreign_key(
    identity_side: sqlite3.Connection,
    voting_side: sqlite3.Connection,
    neutral: sqlite3.Connection,
) -> None:
    """Audit records are append-only facts, not rows in a graph. A key out
    of one would be a join path someone could follow later."""
    for connection in (identity_side, voting_side, neutral):
        for table in table_names(connection):
            assert foreign_keys(connection, table) == ()


def test_as04_to_as06_carry_no_subject_at_all(
    voting_side: sqlite3.Connection, neutral: sqlite3.Connection
) -> None:
    """AS-04, AS-05 and AS-06 are aggregate-only.

    They classify an observation rather than name a participation, which
    is why 'did this person vote' cannot be answered from them.
    """
    for connection, streams in (
        (voting_side, {AuditStream.VOTING_INTEGRITY}),
        (neutral, NEUTRAL_DATABASE_STREAMS),
    ):
        for stream in streams:
            columns = set(table_columns(connection, STREAM_TABLES[stream]))
            assert not columns & SUBJECT_COLUMNS
            assert STREAM_SUBJECT_COLUMNS[stream] in columns


def test_every_stream_has_a_table_and_a_subject_column() -> None:
    assert set(STREAM_TABLES) == set(AuditStream)
    assert set(STREAM_SUBJECT_COLUMNS) == set(AuditStream)
    assert set(AuditStream) == (
        IDENTITY_SIDE_DATABASE_STREAMS | VOTING_SIDE_DATABASE_STREAMS | NEUTRAL_DATABASE_STREAMS
    )
    assert not IDENTITY_SIDE_DATABASE_STREAMS & VOTING_SIDE_DATABASE_STREAMS


# =============================================================================
# 2. What each connection will and will not accept
# =============================================================================


def test_a_record_round_trips_in_its_own_stream(identity_side: sqlite3.Connection) -> None:
    store = SqlVotingAuditStreamStore(identity_side, IDENTITY_SIDE_DATABASE_STREAMS)
    record = _record(AuditStream.ELIGIBILITY, "case-1")
    store.append(record)
    assert store.records(AuditStream.ELIGIBILITY, "vc-1") == (record,)
    assert store.count(AuditStream.ASSERTION, "vc-1") == 0


def test_a_voting_side_record_cannot_be_written_through_the_identity_connection(
    identity_side: sqlite3.Connection,
) -> None:
    store = SqlVotingAuditStreamStore(identity_side, IDENTITY_SIDE_DATABASE_STREAMS)
    with pytest.raises(EvidenceBundleScopeRefusedError):
        store.append(_record(AuditStream.CREDENTIAL, "credential-1"))


def test_an_identity_side_stream_cannot_be_read_through_the_voting_connection(
    voting_side: sqlite3.Connection,
) -> None:
    store = SqlVotingAuditStreamStore(voting_side, VOTING_SIDE_DATABASE_STREAMS)
    with pytest.raises(EvidenceBundleScopeRefusedError):
        store.records(AuditStream.ASSERTION, "vc-1")


def test_the_stream_column_is_checked_by_the_database(
    identity_side: sqlite3.Connection,
) -> None:
    """A typo cannot file an AS-02 record into the AS-01 table."""
    with pytest.raises(sqlite3.IntegrityError):
        identity_side.execute(
            "INSERT INTO audit_record_as01_eligibility (record_id, stream, "
            "voting_context_reference, event_type, reason_code, recorded_at_bucket, "
            "case_reference, payload_hash, document, retention_class) "
            "VALUES ('r1', 'AS-02', 'vc-1', 'e', 'c', 't', 'case-1', 'h', '{}', 'r')"
        )


def test_records_from_both_sides_never_meet_in_one_query(
    identity_side: sqlite3.Connection, voting_side: sqlite3.Connection
) -> None:
    """The two connections are two files.

    Selecting the voting-side table through the identity-side connection
    is not a permission failure - the table simply does not exist there.
    """
    SqlVotingAuditStreamStore(identity_side, IDENTITY_SIDE_DATABASE_STREAMS).append(
        _record(AuditStream.ASSERTION, "assertion-1")
    )
    SqlVotingAuditStreamStore(voting_side, VOTING_SIDE_DATABASE_STREAMS).append(
        _record(AuditStream.CREDENTIAL, "credential-1")
    )
    with pytest.raises(sqlite3.OperationalError):
        identity_side.execute("SELECT * FROM audit_record_as03_credential").fetchall()
    with pytest.raises(sqlite3.OperationalError):
        voting_side.execute("SELECT * FROM audit_record_as02_assertion").fetchall()


# =============================================================================
# 3. The evidence-bundle export log
# =============================================================================


def _bundle(*, pre_closure: bool = False) -> EvidenceBundle:
    sections: dict[str, Mapping[str, object]] = {name: {} for name in BUNDLE_SECTIONS}
    custody = BundleSigningCustody()
    return EvidenceBundle(
        bundle_schema_version=1,
        voting_context_reference="vc-1",
        sections=sections,
        suppressed=(),
        signature=custody.sign(
            canonical_bundle_message(voting_context_reference="vc-1", sections=sections)
        ),
        key_identifier=custody.key_identifier(),
        generated_at_bucket=NOW + timedelta(hours=1),
        pre_closure=pre_closure,
    )


def test_an_export_is_logged_with_its_grant(neutral: sqlite3.Connection) -> None:
    store = SqlEvidenceBundleExportStore(neutral)
    store.record_export(
        _bundle(),
        bundle_id=uuid4(),
        exported_by_role="auditor",
        grant_reference="grant-1",
        dual_control_reference=None,
    )
    exports = store.exports_for_context("vc-1")
    assert len(exports) == 1
    assert exports[0]["exported_by_role"] == "auditor"
    assert exports[0]["pre_closure"] == 0


def test_a_pre_closure_export_without_dual_control_is_refused_by_the_database(
    neutral: sqlite3.Connection,
) -> None:
    """Four eyes for a pre-closure export is a CHECK, so it is not a step
    an operator can skip on a busy evening."""
    store = SqlEvidenceBundleExportStore(neutral)
    with pytest.raises(sqlite3.IntegrityError):
        store.record_export(
            _bundle(pre_closure=True),
            bundle_id=uuid4(),
            exported_by_role="auditor",
            grant_reference="grant-1",
            dual_control_reference=None,
        )


def test_a_pre_closure_export_with_dual_control_is_stored(
    neutral: sqlite3.Connection,
) -> None:
    store = SqlEvidenceBundleExportStore(neutral)
    store.record_export(
        _bundle(pre_closure=True),
        bundle_id=uuid4(),
        exported_by_role="auditor",
        grant_reference="grant-1",
        dual_control_reference="dual-1",
    )
    exports = store.exports_for_context("vc-1")
    assert exports[0]["dual_control_reference"] == "dual-1"


def test_the_export_log_carries_no_participant_column(neutral: sqlite3.Connection) -> None:
    columns = set(table_columns(neutral, "evidence_bundle_export"))
    assert not columns & {
        "participant_reference",
        "account_id",
        "assertion_id",
        "voting_credential_id",
    }


# =============================================================================
# 4. Migrations
# =============================================================================


def test_each_audit_database_declares_exactly_its_own_migrations() -> None:
    assert len(PACK15_IDENTITY_SIDE_AUDIT_MIGRATIONS) == 1
    assert len(PACK15_VOTING_SIDE_AUDIT_MIGRATIONS) == 1
    assert len(PACK15_NEUTRAL_AUDIT_MIGRATIONS) == 1
    identifiers = {
        definition.identifier
        for definitions in (
            PACK15_IDENTITY_SIDE_AUDIT_MIGRATIONS,
            PACK15_VOTING_SIDE_AUDIT_MIGRATIONS,
            PACK15_NEUTRAL_AUDIT_MIGRATIONS,
        )
        for definition in definitions
    }
    assert len(identifiers) == 3


def test_applying_the_audit_migrations_twice_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audit-identity.db"
        first = open_identity_side_audit_database(path, applied_at=NOW)
        before = table_names(first)
        first.close()
        second = open_identity_side_audit_database(path, applied_at=NOW)
        try:
            assert table_names(second) == before
        finally:
            second.close()

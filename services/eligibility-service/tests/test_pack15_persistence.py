"""PACK-15 identity-side durable persistence.

What these tests are for: the unlinkability guarantee of ADR-093 is a
claim about *storage*, and a claim about storage that is only checked in
application code is a claim an operator with a SQL prompt can ignore.
Everything below is asserted against a real migrated SQLite schema.

Three groups:

1. **Separation.** The eligibility database and the Assertion Issuer
   database are separate files; neither carries a credential reference,
   and no foreign key crosses between them - which is not a discipline
   here, it is a syntactic impossibility.
2. **Exactly-once.** The participation-unit claim and the one-time pickup
   are decided by the database, so a concurrent second attempt loses on a
   constraint rather than on a read that raced.
3. **Migrations.** Declared, present, checksummed and idempotent.
"""

from __future__ import annotations

import sqlite3
import tempfile
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from epd2_core.sqlite_migrations import (
    MigrationChecksumMismatchError,
    UnexpectedMigrationFileError,
    apply_migrations,
    foreign_keys,
    load_artefacts,
    table_columns,
    table_names,
)
from epd2_eligibility_service.voting_attributes import AttributeKind, ScopedAttribute
from epd2_eligibility_service.voting_eligibility import (
    AssertionPickup,
    AssertionQueueEntry,
    AssertionStatus,
    EligibilityAssertion,
    EligibilityCase,
    EligibilityCriterion,
    EligibilityDecision,
    EligibilityDecisionReason,
    EligibilityDecisionStatus,
    EligibilityEvidenceReference,
    EligibilityRuleSetReference,
    ParticipationUnitLedgerEntry,
)
from epd2_eligibility_service.voting_handoff import HandoffAcceptance
from epd2_eligibility_service.voting_timing import CohortSizeClass
from epd2_eligibility_service.voting_trust_sql_storage import (
    ASSERTION_ISSUER_MIGRATIONS_DIR,
    ELIGIBILITY_MIGRATIONS_DIR,
    PACK15_ASSERTION_ISSUER_MIGRATIONS,
    PACK15_ELIGIBILITY_MIGRATIONS,
    SqlAssertionIssuerStore,
    SqlEligibilityCaseStore,
    SqlHandoffAcceptanceStore,
    SqlParticipationUnitLedger,
    StorageBoundaryViolationError,
    assert_storage_boundaries_are_separate,
    open_assertion_issuer_database,
    open_eligibility_database,
)

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)

#: Columns that identify a person, or a case that identifies a person.
#: None of them may appear in the Assertion Issuer database.
IDENTIFYING_COLUMNS = frozenset(
    {
        "participant_reference",
        "case_id",
        "account_id",
        "person_id",
        "membership_id",
        "communication_persona_id",
    }
)

#: Columns that belong to the voting side. None of them may appear in
#: either identity-side database, under any table.
VOTING_SIDE_COLUMNS = frozenset(
    {
        "voting_credential_id",
        "credential_id",
        "credential_reference",
        "redemption_reference",
        "ballot_id",
        "vote_content",
    }
)


@pytest.fixture
def eligibility_db() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_eligibility_database(Path(directory) / "eligibility.db", applied_at=NOW)
        try:
            yield connection
        finally:
            connection.close()


@pytest.fixture
def issuer_db() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as directory:
        connection = open_assertion_issuer_database(Path(directory) / "issuer.db", applied_at=NOW)
        try:
            yield connection
        finally:
            connection.close()


def _case(case_id: UUID | None = None) -> EligibilityCase:
    return EligibilityCase(
        case_id=case_id or uuid4(),
        voting_context_reference="vc-1",
        participant_reference="participant-1",
        participation_class="full_member",
        requested_at=NOW,
        status=EligibilityDecisionStatus.REQUESTED,
        scoped_attributes=(
            ScopedAttribute(
                name="membership_active",
                kind=AttributeKind.PREDICATE,
                predicate_value=True,
                source_owner="membership-service",
                source_version="2026-07-01",
            ),
        ),
        evidence=(
            EligibilityEvidenceReference(
                evidence_reference="doc-1",
                evidence_class="membership_record",
                referenced_at=NOW,
            ),
        ),
        assisted_by=None,
    )


def _decision(case_id: UUID) -> EligibilityDecision:
    return EligibilityDecision(
        decision_id=uuid4(),
        case_id=case_id,
        voting_context_reference="vc-1",
        status=EligibilityDecisionStatus.APPROVED,
        rule_set=EligibilityRuleSetReference(
            rule_set_id="rs-1",
            rule_set_version="1.0.0",
            declared_attribute_names=frozenset({"membership_active"}),
            criteria=(EligibilityCriterion.MEMBERSHIP_STATUS,),
        ),
        source_versions={"membership-service": "2026-07-01"},
        reasons=(
            EligibilityDecisionReason(
                reason_code="EPD2-P15-ELIG-APPROVED",
                criterion=EligibilityCriterion.MEMBERSHIP_STATUS,
                note="",
            ),
        ),
        eligibility_class="standard",
        organizational_scope="DE-BE",
        required_assurance_satisfied=True,
        decided_at=NOW,
        valid_until=NOW + timedelta(days=7),
    )


def _assertion(status: AssertionStatus = AssertionStatus.MINTED) -> EligibilityAssertion:
    return EligibilityAssertion(
        assertion_id=uuid4(),
        voting_context_reference="vc-1",
        eligibility_result="approved",
        eligibility_class="standard",
        organizational_scope="DE-BE",
        required_assurance_satisfied=True,
        issued_at_bucket=NOW,
        expires_at=NOW + timedelta(hours=6),
        audience="voting-credential-issuer",
        purpose="voting_credential_issuance",
        nonce="nonce-" + uuid4().hex,
        status=status,
        integrity_metadata={
            "algorithm": "hmac-sha256",
            "key_identifier": "test-assertion-key-v1",
            "signature": "a" * 64,
        },
    )


# =============================================================================
# 1. Separation
# =============================================================================


def test_the_two_identity_side_databases_hold_disjoint_tables(
    eligibility_db: sqlite3.Connection, issuer_db: sqlite3.Connection
) -> None:
    eligibility_tables = set(table_names(eligibility_db)) - {"schema_migration"}
    issuer_tables = set(table_names(issuer_db)) - {"schema_migration"}
    assert eligibility_tables == {
        "eligibility_case",
        "eligibility_decision",
        "participation_unit_ledger",
    }
    assert issuer_tables == {
        "eligibility_assertion",
        "assertion_queue_entry",
        "assertion_pickup",
        "voting_handoff_acceptance",
    }
    assert not eligibility_tables & issuer_tables


def test_the_issuer_database_carries_no_identifying_column(
    issuer_db: sqlite3.Connection,
) -> None:
    """The issuer consumes a five-field minimized decision.

    If it could store who the decision was about, the boundary would be a
    naming convention rather than an architecture.
    """
    for table in table_names(issuer_db):
        columns = set(table_columns(issuer_db, table))
        offending = sorted(columns & IDENTIFYING_COLUMNS)
        assert not offending, f"{table} carries identifying columns: {offending}"


def test_neither_identity_side_database_carries_a_voting_side_column(
    eligibility_db: sqlite3.Connection, issuer_db: sqlite3.Connection
) -> None:
    for connection in (eligibility_db, issuer_db):
        for table in table_names(connection):
            columns = set(table_columns(connection, table))
            offending = sorted(columns & VOTING_SIDE_COLUMNS)
            assert not offending, f"{table} carries voting-side columns: {offending}"


def test_no_foreign_key_leaves_its_own_database(
    eligibility_db: sqlite3.Connection, issuer_db: sqlite3.Connection
) -> None:
    """`person -> assertion` has no edge to walk.

    Every foreign key must point at a table in the same file; a key into
    the other file cannot even be declared, and this asserts that none was
    smuggled in by name.
    """
    for connection in (eligibility_db, issuer_db):
        local = set(table_names(connection))
        for table in local:
            for referenced in foreign_keys(connection, table):
                assert referenced in local, (
                    f"{table} references {referenced}, which is not in this database"
                )


def test_the_participation_ledger_records_that_and_never_which(
    eligibility_db: sqlite3.Connection,
) -> None:
    columns = set(table_columns(eligibility_db, "participation_unit_ledger"))
    assert columns == {
        "voting_context_reference",
        "participation_unit_key",
        "assertion_minted",
        "minted_at",
    }
    assert "assertion_id" not in columns


def test_the_two_stores_may_not_share_a_database() -> None:
    with pytest.raises(StorageBoundaryViolationError):
        assert_storage_boundaries_are_separate("/tmp/one.db", "/tmp/one.db")
    with pytest.raises(StorageBoundaryViolationError):
        assert_storage_boundaries_are_separate("/tmp/one.db", "/tmp/./one.db")
    assert_storage_boundaries_are_separate("/tmp/one.db", "/tmp/two.db")


# =============================================================================
# 2. Round-trips and exactly-once
# =============================================================================


def test_a_case_and_its_decisions_round_trip(eligibility_db: sqlite3.Connection) -> None:
    store = SqlEligibilityCaseStore(eligibility_db)
    case = _case()
    store.save_case(case)
    assert store.get_case(case.case_id) == case

    decision = _decision(case.case_id)
    store.save_decision(decision)
    assert store.get_decision(decision.decision_id) == decision
    assert store.decisions_for_case(case.case_id) == (decision,)


def test_a_case_status_change_is_updated_in_place(eligibility_db: sqlite3.Connection) -> None:
    store = SqlEligibilityCaseStore(eligibility_db)
    case = _case()
    store.save_case(case)
    store.save_case(
        EligibilityCase(
            case_id=case.case_id,
            voting_context_reference=case.voting_context_reference,
            participant_reference=case.participant_reference,
            participation_class=case.participation_class,
            requested_at=case.requested_at,
            status=EligibilityDecisionStatus.APPROVED,
            scoped_attributes=case.scoped_attributes,
            evidence=case.evidence,
        )
    )
    stored = store.get_case(case.case_id)
    assert stored is not None
    assert stored.status is EligibilityDecisionStatus.APPROVED
    row = eligibility_db.execute("SELECT COUNT(*) AS n FROM eligibility_case").fetchone()
    assert row["n"] == 1


def test_a_participation_unit_can_be_claimed_exactly_once(
    eligibility_db: sqlite3.Connection,
) -> None:
    ledger = SqlParticipationUnitLedger(eligibility_db)
    entry = ParticipationUnitLedgerEntry(
        voting_context_reference="vc-1",
        participation_unit_key="unit-1",
        assertion_minted=True,
        minted_at=NOW,
    )
    assert ledger.claim(entry) is True
    assert ledger.claim(entry) is False
    assert ledger.count_minted("vc-1") == 1
    assert ledger.get("vc-1", "unit-1") == entry


def test_concurrent_claims_of_one_participation_unit_produce_one_winner() -> None:
    """Eight threads, one participation unit, one assertion.

    Each thread opens its own connection, so this is a real database race
    rather than a serialized one.
    """
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "eligibility.db"
        setup = open_eligibility_database(path, applied_at=NOW)
        setup.close()

        entry = ParticipationUnitLedgerEntry(
            voting_context_reference="vc-1",
            participation_unit_key="unit-1",
            assertion_minted=True,
            minted_at=NOW,
        )
        results: list[bool] = []
        lock = threading.Lock()
        barrier = threading.Barrier(8)

        def attempt() -> None:
            connection = sqlite3.connect(path, timeout=10.0)
            connection.row_factory = sqlite3.Row
            try:
                barrier.wait()
                try:
                    claimed = SqlParticipationUnitLedger(connection).claim(entry)
                    connection.commit()
                except sqlite3.OperationalError:  # pragma: no cover - lock contention
                    connection.rollback()
                    claimed = False
                with lock:
                    results.append(claimed)
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert results.count(True) == 1, results
        verify = open_eligibility_database(path, applied_at=NOW)
        try:
            assert SqlParticipationUnitLedger(verify).count_minted("vc-1") == 1
        finally:
            verify.close()


def test_an_assertion_and_its_queue_entry_round_trip(issuer_db: sqlite3.Connection) -> None:
    store = SqlAssertionIssuerStore(issuer_db)
    assertion = _assertion()
    store.save_assertion(assertion)
    stored = store.get_assertion(assertion.assertion_id)
    assert stored == assertion
    assert stored is not None
    assert stored.integrity_metadata["key_identifier"] == "test-assertion-key-v1"

    entry = AssertionQueueEntry(
        assertion_id=assertion.assertion_id,
        voting_context_reference="vc-1",
        batch_reference="batch-1",
        enqueued_at=NOW,
        release_not_before=NOW + timedelta(seconds=30),
        cohort_wait_deadline=NOW + timedelta(seconds=3600),
        cohort_size_class=CohortSizeClass.ABOVE_MINIMUM,
    )
    store.save_queue_entry(entry)
    assert store.get_queue_entry(assertion.assertion_id) == entry
    assert store.pending_batch("batch-1") == (entry,)

    released = AssertionQueueEntry(
        assertion_id=entry.assertion_id,
        voting_context_reference=entry.voting_context_reference,
        batch_reference=entry.batch_reference,
        enqueued_at=entry.enqueued_at,
        release_not_before=entry.release_not_before,
        cohort_wait_deadline=entry.cohort_wait_deadline,
        released_at=NOW + timedelta(seconds=120),
        cohort_size_class=entry.cohort_size_class,
    )
    store.save_queue_entry(released)
    assert store.pending_batch("batch-1") == ()


def test_an_assertion_nonce_is_unique(issuer_db: sqlite3.Connection) -> None:
    """Two assertions sharing a nonce would let one credential be issued
    for two participations, or two for one."""
    store = SqlAssertionIssuerStore(issuer_db)
    first = _assertion()
    store.save_assertion(first)
    duplicate = EligibilityAssertion(
        assertion_id=uuid4(),
        voting_context_reference=first.voting_context_reference,
        eligibility_result=first.eligibility_result,
        eligibility_class=first.eligibility_class,
        organizational_scope=first.organizational_scope,
        required_assurance_satisfied=first.required_assurance_satisfied,
        issued_at_bucket=first.issued_at_bucket,
        expires_at=first.expires_at,
        audience=first.audience,
        purpose=first.purpose,
        nonce=first.nonce,
        status=first.status,
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.save_assertion(duplicate)


def test_a_pickup_is_consumable_exactly_once(issuer_db: sqlite3.Connection) -> None:
    store = SqlAssertionIssuerStore(issuer_db)
    assertion = _assertion()
    store.save_assertion(assertion)
    pickup = AssertionPickup(
        pickup_id=uuid4(),
        assertion_id=assertion.assertion_id,
        voting_context_reference="vc-1",
        handoff_artifact_digest="d" * 64,
        audience_origin="https://vote.example",
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    store.save_pickup(pickup)
    assert store.get_pickup_by_digest("d" * 64) == pickup
    assert store.consume_pickup(pickup.pickup_id, consumed_at=NOW) is True
    assert store.consume_pickup(pickup.pickup_id, consumed_at=NOW) is False
    consumed = store.get_pickup_by_digest("d" * 64)
    assert consumed is not None and consumed.consumed


def test_a_second_pickup_for_one_handoff_digest_is_refused(
    issuer_db: sqlite3.Connection,
) -> None:
    store = SqlAssertionIssuerStore(issuer_db)
    first = _assertion()
    second = _assertion()
    store.save_assertion(first)
    store.save_assertion(second)
    digest = "e" * 64
    store.save_pickup(
        AssertionPickup(
            pickup_id=uuid4(),
            assertion_id=first.assertion_id,
            voting_context_reference="vc-1",
            handoff_artifact_digest=digest,
            audience_origin="https://vote.example",
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
        )
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.save_pickup(
            AssertionPickup(
                pickup_id=uuid4(),
                assertion_id=second.assertion_id,
                voting_context_reference="vc-1",
                handoff_artifact_digest=digest,
                audience_origin="https://vote.example",
                created_at=NOW,
                expires_at=NOW + timedelta(minutes=10),
            )
        )


def test_a_handoff_artifact_is_accepted_exactly_once(issuer_db: sqlite3.Connection) -> None:
    store = SqlHandoffAcceptanceStore(issuer_db)
    acceptance = HandoffAcceptance(
        acceptance_id=uuid4(),
        artifact_digest="f" * 64,
        voting_context_reference="vc-1",
        audience="voting-credential-issuer",
        origin="https://mitwirkung.example",
        accepted_at=NOW,
    )
    assert store.accept_once(acceptance) is True
    assert store.accept_once(acceptance) is False
    assert store.get("f" * 64) == acceptance


def test_an_acceptance_record_carries_no_account_or_session(
    issuer_db: sqlite3.Connection,
) -> None:
    columns = set(table_columns(issuer_db, "voting_handoff_acceptance"))
    assert not columns & {"account_id", "session_id", "device_id", "participant_reference"}


def test_a_rolled_back_issuance_leaves_no_assertion_and_no_queue_entry(
    issuer_db: sqlite3.Connection,
) -> None:
    """Minting and enqueueing are one unit of work.

    A half-applied issuance is an assertion that exists but will never be
    released - a participant permanently unable to vote, with no record
    saying why.
    """
    store = SqlAssertionIssuerStore(issuer_db)
    assertion = _assertion()
    try:
        store.save_assertion(assertion)
        store.save_queue_entry(
            AssertionQueueEntry(
                assertion_id=assertion.assertion_id,
                voting_context_reference="vc-1",
                batch_reference="batch-1",
                enqueued_at=NOW,
                release_not_before=NOW + timedelta(seconds=30),
                cohort_wait_deadline=NOW + timedelta(seconds=3600),
            )
        )
        raise RuntimeError("release scheduling failed")
    except RuntimeError:
        issuer_db.rollback()

    assert store.get_assertion(assertion.assertion_id) is None
    assert store.get_queue_entry(assertion.assertion_id) is None


def test_a_queue_entry_without_its_assertion_is_refused(issuer_db: sqlite3.Connection) -> None:
    store = SqlAssertionIssuerStore(issuer_db)
    with pytest.raises(sqlite3.IntegrityError):
        store.save_queue_entry(
            AssertionQueueEntry(
                assertion_id=uuid4(),
                voting_context_reference="vc-1",
                batch_reference="batch-1",
                enqueued_at=NOW,
                release_not_before=NOW + timedelta(seconds=30),
                cohort_wait_deadline=NOW + timedelta(seconds=3600),
            )
        )
        issuer_db.commit()


# =============================================================================
# 3. Migrations
# =============================================================================


def test_every_declared_migration_has_a_file() -> None:
    assert load_artefacts(PACK15_ELIGIBILITY_MIGRATIONS, ELIGIBILITY_MIGRATIONS_DIR)
    assert load_artefacts(PACK15_ASSERTION_ISSUER_MIGRATIONS, ASSERTION_ISSUER_MIGRATIONS_DIR)


def test_an_undeclared_migration_file_is_refused() -> None:
    """A file nobody declared is a schema change nobody reviewed."""
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        for definition in PACK15_ELIGIBILITY_MIGRATIONS:
            (target / definition.filename()).write_text(
                (ELIGIBILITY_MIGRATIONS_DIR / definition.filename()).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        (target / "0099_undeclared.sql").write_text("CREATE TABLE x (y TEXT);", encoding="utf-8")
        with pytest.raises(UnexpectedMigrationFileError):
            load_artefacts(PACK15_ELIGIBILITY_MIGRATIONS, target)


def test_an_edited_applied_migration_is_refused() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        for definition in PACK15_ELIGIBILITY_MIGRATIONS:
            (target / definition.filename()).write_text(
                (ELIGIBILITY_MIGRATIONS_DIR / definition.filename()).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        connection = sqlite3.connect(target / "eligibility.db")
        connection.row_factory = sqlite3.Row
        try:
            apply_migrations(
                connection, load_artefacts(PACK15_ELIGIBILITY_MIGRATIONS, target), applied_at=NOW
            )
            first = PACK15_ELIGIBILITY_MIGRATIONS[0].filename()
            (target / first).write_text(
                (target / first).read_text(encoding="utf-8") + "\n-- edited\n", encoding="utf-8"
            )
            with pytest.raises(MigrationChecksumMismatchError):
                apply_migrations(
                    connection,
                    load_artefacts(PACK15_ELIGIBILITY_MIGRATIONS, target),
                    applied_at=NOW,
                )
        finally:
            connection.close()


def test_applying_the_migrations_twice_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "issuer.db"
        first = open_assertion_issuer_database(path, applied_at=NOW)
        before = table_names(first)
        first.close()
        second = open_assertion_issuer_database(path, applied_at=NOW)
        try:
            assert table_names(second) == before
            row = second.execute("SELECT COUNT(*) AS n FROM schema_migration").fetchone()
            assert row["n"] == len(PACK15_ASSERTION_ISSUER_MIGRATIONS)
        finally:
            second.close()

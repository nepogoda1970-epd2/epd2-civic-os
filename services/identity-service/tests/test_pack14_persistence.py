"""PACK-14 durable persistence tests.

The eight properties the correction round exists to prove, plus the
migration discipline they rest on. Every test here runs against the
**reference persistence adapters**, not the in-memory ones - several of
them restart the application against a file-backed database, which is the
only way to tell a real store from a dictionary.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from _pack14_builders import (
    NOW,
    SALT,
    account_id,
    assurance,
    credential_metadata,
    device,
    new_credential_id,
    new_session_id,
    reference,
    scope,
)

from epd2_core.clock import FixedClock
from epd2_identity_service.account_security_storage import (
    InMemoryAccountRegistryStore,
    InMemoryReplayPreventionStore,
)
from epd2_identity_service.accounts import AccountRegistryStatus, create_account_record
from epd2_identity_service.assurance import AuthenticationMethod
from epd2_identity_service.codecs import decode_dataclass, encode_dataclass
from epd2_identity_service.configuration import default_configuration
from epd2_identity_service.contacts import ContactChannelClass
from epd2_identity_service.credentials import CredentialType
from epd2_identity_service.exceptions import (
    MigrationChecksumMismatchError,
    MigrationNotAppliedError,
    ResourceVersionStaleError,
    UnsupportedPersistedTypeError,
    VotingHandoffAlreadyUsedError,
)
from epd2_identity_service.identifiers import AccountId
from epd2_identity_service.migration_runner import (
    MIGRATIONS_DIR,
    apply_migrations,
    connect,
    load_artefacts,
    open_migrated,
    statements,
    verify_migrations,
)
from epd2_identity_service.persistence import PACK14_MIGRATIONS, MigrationKind
from epd2_identity_service.runtime import IdentityRuntime, build_identity_service
from epd2_identity_service.secret_storage import DeterministicSecureRandom
from epd2_identity_service.sessions import SessionRecord, SessionStatus
from epd2_identity_service.sql_storage import (
    SqlAccountRegistryStore,
    SqlReplayPreventionStore,
    UnitOfWork,
)
from epd2_identity_service.voting_handoff import (
    VotingHandoffRequest,
    issue_voting_handoff,
    redeem_voting_handoff,
)
from epd2_identity_service.workspaces import WorkspaceId, workspace_origin

CLOCK = FixedClock(NOW)


def _runtime(database: str = ":memory:") -> IdentityRuntime:
    return build_identity_service(
        clock=CLOCK,
        derivation_salt=SALT,
        database=database,
        random=DeterministicSecureRandom(),
    )


# --- migrations -------------------------------------------------------------


def test_every_declared_migration_has_an_artefact_and_the_reverse() -> None:
    artefacts = load_artefacts()
    assert len(artefacts) == len(PACK14_MIGRATIONS)
    for artefact in artefacts:
        assert artefact.path.is_file()
        assert artefact.sql.strip()
        assert artefact.definition.kind is MigrationKind.EXPAND


def test_applying_the_migrations_creates_the_schema_and_is_idempotent() -> None:
    connection = connect(":memory:")
    applied = apply_migrations(connection, applied_at=NOW)
    assert len(applied) == len(PACK14_MIGRATIONS)
    # A second run applies nothing: that is what "idempotent migration"
    # means operationally.
    assert apply_migrations(connection, applied_at=NOW) == ()
    verify_migrations(connection)


def test_the_schema_carries_the_declared_constraints_and_expiry_indexes() -> None:
    connection = open_migrated(":memory:", applied_at=NOW)
    names = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    }
    for constraint in (
        "uq_contact_scope_digest",
        "uq_passkey_credential_reference",
        "uq_open_closure_request",
        "uq_bootstrap_response_digest",
        "uq_voting_handoff_digest",
        "uq_nonce_record",
        "uq_identity_mapping_purpose_scope_source",
    ):
        assert constraint in names, constraint
    for index in (
        "ix_session_absolute_deadline",
        "ix_bootstrap_response_expires_at",
        "ix_voting_handoff_expires_at",
        "ix_replay_nonce_expires_at",
        "ix_identity_mapping_expires_at",
    ):
        assert index in names, index


def test_an_edited_applied_migration_is_refused_by_the_compatibility_check() -> None:
    """ADR-075's rule, enforced: an applied migration is never edited in
    place, and the checksum is how that becomes detectable."""
    connection = open_migrated(":memory:", applied_at=NOW)
    connection.execute(
        "UPDATE schema_migration SET checksum = ? WHERE identifier = ?",
        ("0" * 64, PACK14_MIGRATIONS[0].identifier),
    )
    with pytest.raises(MigrationChecksumMismatchError):
        verify_migrations(connection)


def test_an_unapplied_migration_is_refused(tmp_path: Path) -> None:
    connection = connect(":memory:")
    with pytest.raises(MigrationNotAppliedError):
        verify_migrations(connection)


def test_an_artefact_with_no_declaration_is_refused(tmp_path: Path) -> None:
    for artefact in load_artefacts():
        (tmp_path / artefact.path.name).write_text(artefact.sql, encoding="utf-8")
    (tmp_path / "0099_undeclared.sql").write_text("CREATE TABLE x (a TEXT);\n", encoding="utf-8")
    with pytest.raises(MigrationNotAppliedError):
        load_artefacts(tmp_path)


def test_the_statement_splitter_produces_executable_statements() -> None:
    sql = (MIGRATIONS_DIR / "0010_replay_prevention.sql").read_text(encoding="utf-8")
    parts = statements(sql)
    assert parts
    assert all(part.rstrip().endswith(";") for part in parts)


# --- state survives a restart -----------------------------------------------


def test_account_contact_and_credential_state_survive_recreating_the_application(
    tmp_path: Path,
) -> None:
    """The test a dictionary cannot pass.

    A whole new application object, a whole new connection, against the
    same file - and the account, its verified contact and its credential
    are all still there.
    """
    database = str(tmp_path / "identity.sqlite3")
    account = account_id()
    first = _runtime(database)
    first.service.create_account(
        account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4()
    )
    contact = first.service.add_contact(
        contact_id=uuid4(),
        account_id=account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="anna@epd.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    first.service.verify_contact(
        contact_id=contact.contact_id, correlation_id=uuid4(), event_id=uuid4()
    )
    first.service.activate_account(
        account_id=account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
    )
    first.service.enroll_credential(
        credential_id=new_credential_id(),
        account_id=account,
        credential_type=CredentialType.PASSKEY,
        metadata=credential_metadata(),
        correlation_id=uuid4(),
        event_id=uuid4(),
        requires_confirmation=False,
    )
    first.connection.close()

    second = _runtime(database)
    record = second.service.account_store.get(account)
    assert record is not None
    assert record.account_status is AccountRegistryStatus.ACTIVE
    assert record.version == 2
    contacts = second.service.contact_store.for_account(account)
    assert len(contacts) == 1
    assert contacts[0].is_verified()
    assert contacts[0].masked_value == "a***@e***.example"
    credentials = second.service.credential_store.for_account(account)
    assert len(credentials) == 1
    assert credentials[0].metadata.nickname == "Diensthandy"
    second.connection.close()


def test_a_session_survives_a_restart_with_both_deadlines_intact(tmp_path: Path) -> None:
    database = str(tmp_path / "identity.sqlite3")
    account = account_id()
    first = _runtime(database)
    _activate(first, account)
    session, _refresh, _csrf = first.service.issue_session(
        session_id=new_session_id(),
        account_id=account,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
        credential_binding="device_bound",
        device=device(),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    first.connection.close()

    second = _runtime(database)
    restored = second.service.session_store.get(session.session_id)
    assert restored is not None
    assert restored.idle_deadline == session.idle_deadline
    assert restored.absolute_deadline == session.absolute_deadline
    assert restored.idle_deadline.tzinfo is not None
    assert restored.status is SessionStatus.ACTIVE
    second.connection.close()


def _activate(runtime: IdentityRuntime, account: AccountId) -> None:
    runtime.service.create_account(
        account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4()
    )
    contact = runtime.service.add_contact(
        contact_id=uuid4(),
        account_id=account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="anna@epd.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    runtime.service.verify_contact(
        contact_id=contact.contact_id, correlation_id=uuid4(), event_id=uuid4()
    )
    runtime.service.activate_account(
        account_id=account, expected_version=1, correlation_id=uuid4(), event_id=uuid4()
    )


# --- replay protection across a restart -------------------------------------


def test_voting_handoff_replay_protection_survives_a_restart(tmp_path: Path) -> None:
    """The property an in-process set cannot have.

    A single-use artifact that becomes replayable after a restart is not
    single-use; it is single-use per process, which is not a security
    property anyone can rely on.
    """
    database = str(tmp_path / "identity.sqlite3")
    context = uuid4()
    first = _runtime(database)
    artifact, issuance = issue_voting_handoff(
        VotingHandoffRequest(
            request_id=uuid4(),
            voting_context_id=context,
            audience_origin=workspace_origin(WorkspaceId.VOTING_CLIENT),
            requested_at=NOW,
        ),
        artifact_id=uuid4(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    first.service.voting_handoff_store.save_issuance(issuance)
    spent, redemption = redeem_voting_handoff(
        issuance,
        presented_value=artifact.value,
        presenting_origin=artifact.audience_origin,
        voting_context_id=context,
        redemption_id=uuid4(),
        now=NOW,
    )
    first.service.voting_handoff_store.save_issuance(spent)
    first.service.voting_handoff_store.save_redemption(redemption)
    first.connection.close()

    second = _runtime(database)
    stored = second.service.voting_handoff_store.get_issuance(artifact.artifact_id)
    assert stored is not None
    assert stored.is_spent()
    with pytest.raises(VotingHandoffAlreadyUsedError):
        redeem_voting_handoff(
            stored,
            presented_value=artifact.value,
            presenting_origin=artifact.audience_origin,
            voting_context_id=context,
            redemption_id=uuid4(),
            now=NOW,
        )
    second.connection.close()


def test_nonce_and_idempotency_records_survive_a_restart(tmp_path: Path) -> None:
    from epd2_identity_service.persistence import IdempotencyRecord, ReplayNonceRecord
    from epd2_identity_service.secret_storage import hash_token

    database = str(tmp_path / "identity.sqlite3")
    first = _runtime(database)
    first.service.replay_store.record_nonce(
        ReplayNonceRecord(
            nonce_digest=hash_token("nonce-1"),
            purpose="bootstrap",
            consumed_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
        )
    )
    first.service.replay_store.record_idempotency(
        IdempotencyRecord(
            idempotency_key="k1",
            request_digest="a" * 64,
            operation="account.create",
            recorded_at=NOW,
        )
    )
    first.service.replay_store.record_assertion_id("assertion-1")
    first.connection.close()

    second = _runtime(database)
    assert hash_token("nonce-1").digest in second.service.replay_store.seen_nonce_digests()
    stored = second.service.replay_store.get_idempotency("k1")
    assert stored is not None
    assert stored.operation == "account.create"
    assert "assertion-1" in second.service.replay_store.seen_assertion_ids()
    second.connection.close()


def test_bootstrap_single_use_survives_a_restart(tmp_path: Path) -> None:
    from epd2_identity_service.bootstrap import (
        BootstrapProofMethod,
        create_bootstrap_request,
        issue_bootstrap_response,
        redeem_bootstrap_response,
    )
    from epd2_identity_service.domain import AuthenticationAssuranceLevel
    from epd2_identity_service.exceptions import BootstrapAlreadyUsedError
    from epd2_identity_service.identifiers import MappingPurpose

    database = str(tmp_path / "identity.sqlite3")
    redirect = f"{workspace_origin(WorkspaceId.MEMBER_APPLICATION)}/cb"
    first = _runtime(database)
    request = create_bootstrap_request(
        request_id=uuid4(),
        workspace=WorkspaceId.MEMBER_APPLICATION,
        redirect_uri=redirect,
        redirect_allowlist=frozenset({redirect}),
        proof_challenge="digest",
        proof_method=BootstrapProofMethod.S256,
        created_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    first.service.bootstrap_store.save_request(request)
    response, value = issue_bootstrap_response(
        request,
        response_id=uuid4(),
        actor_reference=reference(account_id(), purpose=MappingPurpose.SESSION),
        achieved_assurance=AuthenticationAssuranceLevel.HIGH,
        issued_at=NOW,
        lifetime=timedelta(minutes=2),
        random=DeterministicSecureRandom(seed="r"),
    )
    spent, redemption = redeem_bootstrap_response(
        response,
        presented_value=value,
        presenting_workspace=request.workspace,
        presenting_origin=request.audience_origin,
        presented_nonce=request.nonce,
        redemption_id=uuid4(),
        now=NOW,
    )
    first.service.bootstrap_store.save_response(spent)
    first.service.bootstrap_store.save_redemption(redemption)
    first.connection.close()

    second = _runtime(database)
    stored = second.service.bootstrap_store.get_response(response.response_id)
    assert stored is not None and stored.is_spent()
    prior = second.service.bootstrap_store.redemption_for(response.response_id)
    assert prior is not None
    with pytest.raises(BootstrapAlreadyUsedError):
        redeem_bootstrap_response(
            stored,
            presented_value=value,
            presenting_workspace=request.workspace,
            presenting_origin=request.audience_origin,
            presented_nonce=request.nonce,
            redemption_id=uuid4(),
            now=NOW,
        )
    second.connection.close()


# --- transactions and concurrency -------------------------------------------


def test_a_failed_transaction_leaves_no_partial_account_or_credential_state(
    tmp_path: Path,
) -> None:
    database = str(tmp_path / "identity.sqlite3")
    runtime = _runtime(database)
    account = account_id()
    with pytest.raises(RuntimeError, match="deliberate"), runtime.service.transaction():
        runtime.service.create_account(
            account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4()
        )
        runtime.service.add_contact(
            contact_id=uuid4(),
            account_id=account,
            channel_class=ContactChannelClass.EMAIL,
            raw_value="anna@epd.example",
            correlation_id=uuid4(),
            event_id=uuid4(),
        )
        raise RuntimeError("deliberate failure half-way through the request")
    assert runtime.service.account_store.get(account) is None
    assert runtime.service.contact_store.for_account(account) == ()
    runtime.connection.close()


def test_a_stale_write_is_refused_by_the_optimistic_concurrency_check() -> None:
    connection = open_migrated(":memory:", applied_at=NOW)
    store = SqlAccountRegistryStore(connection)
    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    store.save(record)
    moved_on = record.with_status(AccountRegistryStatus.ACTIVE)
    store.save(moved_on)
    # A second writer holding the version-1 read now tries to advance it
    # to version 2 as well. The row is already at 2.
    stale = record.with_status(AccountRegistryStatus.CLOSED)
    with pytest.raises(ResourceVersionStaleError):
        store.save(stale)
    connection.close()


def test_the_database_enforces_contact_uniqueness_within_a_scope() -> None:
    runtime = _runtime()
    account = account_id()
    other = account_id("44444444-4444-4444-8444-444444444444")
    for candidate in (account, other):
        runtime.service.create_account(
            account_id=candidate, scope=scope(), correlation_id=uuid4(), event_id=uuid4()
        )
    runtime.service.add_contact(
        contact_id=uuid4(),
        account_id=account,
        channel_class=ContactChannelClass.EMAIL,
        raw_value="familie@epd.example",
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    # The application layer refuses first; if it ever stopped, the unique
    # index would still refuse. Both are asserted, because a constraint
    # nobody tests is a constraint that gets dropped in a later migration.
    from epd2_identity_service.exceptions import ContactAlreadyInUseError

    with pytest.raises(ContactAlreadyInUseError):
        runtime.service.add_contact(
            contact_id=uuid4(),
            account_id=other,
            channel_class=ContactChannelClass.EMAIL,
            raw_value="familie@epd.example",
            correlation_id=uuid4(),
            event_id=uuid4(),
        )
    with pytest.raises(sqlite3.IntegrityError):
        runtime.connection.execute(
            "INSERT INTO account_contact"
            " (contact_id, account_id, channel_class, normalized_digest, masked_value, status,"
            "  scope_level, scope_unit_id, added_at, retention_class, legal_hold, version,"
            "  document)"
            " SELECT ?, ?, channel_class, normalized_digest, masked_value, status,"
            "  scope_level, scope_unit_id, added_at, retention_class, legal_hold, version, document"
            " FROM account_contact LIMIT 1",
            (str(uuid4()), str(other)),
        )
    runtime.connection.close()


def test_the_unit_of_work_nests_without_committing_early() -> None:
    connection = open_migrated(":memory:", applied_at=NOW)
    unit = UnitOfWork(connection=connection)
    store = SqlAccountRegistryStore(connection)
    record = create_account_record(account_id=account_id(), scope=scope(), created_at=NOW)
    with pytest.raises(RuntimeError), unit():
        with unit():
            store.save(record)
        raise RuntimeError("outer failure after an inner block completed")
    assert store.get(record.account_id) is None
    connection.close()


# --- serialization ----------------------------------------------------------


def test_the_codec_round_trips_a_session_including_its_typed_identifiers() -> None:
    from epd2_identity_service.sessions import SessionScope, issue_session

    session, _refresh, _csrf = issue_session(
        session_id=new_session_id(),
        account_id=account_id(),
        actor_reference=reference(account_id()),
        scope=SessionScope(
            workspace=WorkspaceId.MEMBER_APPLICATION,
            origin=workspace_origin(WorkspaceId.MEMBER_APPLICATION),
            capabilities=frozenset({"member-shell"}),
        ),
        assurance=assurance(),
        device=device(),
        issued_at=NOW,
        configuration=default_configuration(),
        random=DeterministicSecureRandom(),
    )
    restored = decode_dataclass(SessionRecord, encode_dataclass(session))
    assert restored == session
    assert restored.issued_at.tzinfo is not None


def test_the_codec_refuses_raw_bytes_and_naive_datetimes() -> None:
    with pytest.raises(UnsupportedPersistedTypeError):
        encode_dataclass(_WithBytes(payload=b"secret"))
    with pytest.raises(UnsupportedPersistedTypeError):
        encode_dataclass(_WithNaive(moment=datetime(2026, 7, 30)))


from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True, slots=True)
class _WithBytes:
    payload: bytes


@dataclass(frozen=True, slots=True)
class _WithNaive:
    moment: datetime


def test_no_stored_document_contains_a_secret_or_a_raw_contact(tmp_path: Path) -> None:
    """A sweep over every row the reference path writes.

    Cheaper than reasoning about thirty aggregates one at a time, and it
    catches the case a per-aggregate assertion would miss: a nested field
    that acquired a secret through a type change.
    """
    database = str(tmp_path / "identity.sqlite3")
    runtime = _runtime(database)
    account = account_id()
    _activate(runtime, account)
    runtime.service.issue_session(
        session_id=new_session_id(),
        account_id=account,
        workspace=WorkspaceId.MEMBER_APPLICATION,
        methods=(AuthenticationMethod.PASSKEY_DEVICE_BOUND,),
        credential_binding="device_bound",
        device=device(),
        correlation_id=uuid4(),
        event_id=uuid4(),
    )
    forbidden = ("anna@epd.example", "hunter2", "BEGIN PRIVATE KEY")
    tables = [
        row["name"]
        for row in runtime.connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    ]
    for table in tables:
        rows = runtime.connection.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            blob = " ".join(str(value) for value in tuple(row))
            for secret in forbidden:
                assert secret not in blob, f"{table} carries {secret!r}"
    runtime.connection.close()


# --- the default binding ----------------------------------------------------


def test_the_runtime_binds_sql_stores_and_not_the_in_memory_ones() -> None:
    runtime = _runtime()
    assert isinstance(runtime.service.account_store, SqlAccountRegistryStore)
    assert isinstance(runtime.service.replay_store, SqlReplayPreventionStore)
    assert not isinstance(runtime.service.account_store, InMemoryAccountRegistryStore)
    assert not isinstance(runtime.service.replay_store, InMemoryReplayPreventionStore)
    assert runtime.service.unit_of_work is not None
    runtime.connection.close()


def test_the_runtime_binds_the_refusing_security_ports_by_default() -> None:
    from epd2_identity_service.exceptions import (
        BreachCheckUnavailableError,
        PasskeyVerificationFailedError,
    )
    from epd2_identity_service.secret_storage import (
        UnavailablePasswordHasher,
        UnboundBreachedPasswordChecker,
    )

    runtime = _runtime()
    assert isinstance(runtime.service.breach_checker, UnboundBreachedPasswordChecker)
    assert isinstance(runtime.service.password_hasher, UnavailablePasswordHasher)
    with pytest.raises(BreachCheckUnavailableError):
        runtime.service.breach_checker.is_breached("anything")
    with pytest.raises(PasskeyVerificationFailedError):
        runtime.service.webauthn_verifier.verify_registration(
            None,  # type: ignore[arg-type]
            challenge=None,  # type: ignore[arg-type]
        )
    runtime.connection.close()


def test_the_clock_is_still_the_only_source_of_time_in_a_stored_row(tmp_path: Path) -> None:
    database = str(tmp_path / "identity.sqlite3")
    runtime = _runtime(database)
    account = account_id()
    runtime.service.create_account(
        account_id=account, scope=scope(), correlation_id=uuid4(), event_id=uuid4()
    )
    row = runtime.connection.execute(
        "SELECT created_at FROM account_registry_record WHERE account_id = ?", (str(account),)
    ).fetchone()
    assert datetime.fromisoformat(row["created_at"]) == NOW
    assert NOW.tzinfo is UTC
    runtime.connection.close()

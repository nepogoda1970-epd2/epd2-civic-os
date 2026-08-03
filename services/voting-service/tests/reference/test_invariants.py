"""Invariant, logging, audit, schema and boundary tests.

Covers PACK-16D §44 (no intermediate tally), §45 (feature-flag
restrictions), §46 (logging restrictions), §47 (audit evidence), §50
(schema registry) and the §36 independent-implementation boundary.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

import epd2_voting_service.reference as reference_package
from epd2_voting_service.reference.audit import (
    AuditFieldRejected,
    AuditLog,
    AuditRecordType,
)
from epd2_voting_service.reference.casting.transactions import submit_cast_ballot
from epd2_voting_service.reference.crypto.randomness import (
    TEST_PROFILE_ENV,
    DeterministicSourceForbiddenError,
    select_source,
)
from epd2_voting_service.reference.election_record.builder import (
    IntermediateTallyProhibitedError,
    open_tally,
)
from epd2_voting_service.reference.invariants import (
    IMMUTABLE_INVARIANTS,
    PERMITTED_FLAGS,
    FeatureFlags,
    UnknownFeatureFlagError,
    UnsafeFeatureFlagError,
    enforce_startup_invariants,
)
from epd2_voting_service.reference.logging_boundary import (
    ALLOWED_FIELDS,
    FORBIDDEN_LOG_FIELDS,
    ForbiddenLogFieldError,
    ReferenceLogger,
    scan_mapping,
)
from epd2_voting_service.reference.publication.bulletin_board import (
    PRE_CLOSURE_ENTRY_TYPES,
    EntryType,
    PreClosurePublicationError,
)
from epd2_voting_service.reference.publication.outbox import FORBIDDEN_OUTBOX_FIELDS
from epd2_voting_service.reference.schemas import (
    REGISTRY_VERSION,
    SCHEMA_REGISTRY,
    UnknownSchemaError,
    get_schema,
)
from epd2_voting_service.reference.testing.fixtures import fixture_a
from epd2_voting_service.reference.testing.scenarios import make_ballot

REFERENCE_ROOT = pathlib.Path(reference_package.__file__).parent


# -- §44 no intermediate tally -------------------------------------------


def test_tally_construction_is_unavailable_before_closure() -> None:
    with pytest.raises(IntermediateTallyProhibitedError):
        open_tally(board_closed=False)
    open_tally(board_closed=True)  # no exception


def test_pre_closure_entry_types_exclude_every_result_artifact() -> None:
    post_closure_only = set(EntryType) - PRE_CLOSURE_ENTRY_TYPES
    assert EntryType.TALLY_ARTIFACT in post_closure_only
    assert EntryType.SEALED_BATCH_OPENING in post_closure_only
    assert EntryType.BATCH_RECONCILIATION_RECORD in post_closure_only
    assert EntryType.BALLOT_ACCEPTED in post_closure_only
    assert EntryType.BALLOT_SPOILED in post_closure_only


@pytest.mark.parametrize(
    "entry_type",
    sorted(set(EntryType) - PRE_CLOSURE_ENTRY_TYPES - {EntryType.ELECTION_CLOSED}),
)
def test_every_post_closure_entry_type_is_refused_before_closure(
    entry_type: EntryType,
) -> None:
    fixture = fixture_a()
    with pytest.raises(PreClosurePublicationError):
        fixture.board.append(entry_type, b"payload")


def test_turnout_and_accepted_enumeration_are_not_exported_pre_closure() -> None:
    """Nothing the board exports before closure counts accepted ballots."""
    fixture = fixture_a()
    for index in range(3):
        envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, f"inv-{index}".encode())
        submit_cast_ballot(
            fixture.store,
            fixture.runtime,
            fixture.capabilities[index],
            envelope,
            f"k{index}",
        )
    fixture.board.append(EntryType.ELECTION_MANIFEST, b"m")
    fixture.board.publish_checkpoint()

    exported = fixture.board.export_entries()
    assert all(entry_type != "ballot_accepted" for _, entry_type, _ in exported)
    # the exported payloads carry no ballot id at all
    for ballot_id in fixture.store.accepted_ballots:
        assert all(ballot_id.encode() not in payload for _, _, payload in exported)


def test_no_feature_flag_can_reach_the_tally_gate() -> None:
    """`open_tally` takes a bool, not a flag lookup. Assert its shape."""
    import inspect

    signature = inspect.signature(open_tally)
    assert list(signature.parameters) == ["board_closed"]
    source = inspect.getsource(open_tally)
    assert "flag" not in source.lower()
    assert "getenv" not in source and "environ" not in source


# -- §45 feature-flag restrictions ---------------------------------------


def test_permitted_flags_load() -> None:
    flags = enforce_startup_invariants({"reference_api_enabled": True})
    assert flags.get("reference_api_enabled") is True
    assert flags.get("verbose_verification_output") is False


@pytest.mark.parametrize("invariant", sorted(IMMUTABLE_INVARIANTS))
def test_unsafe_flag_override_fails_startup(invariant: str) -> None:
    for name in (invariant, f"disable_{invariant}", f"{invariant}_off", invariant.upper()):
        with pytest.raises(UnsafeFeatureFlagError):
            enforce_startup_invariants({name: False})


def test_unknown_flag_fails_startup_rather_than_being_ignored() -> None:
    with pytest.raises(UnknownFeatureFlagError):
        enforce_startup_invariants({"skip_proof_check_fast_path": True})


def test_permitted_flags_and_invariants_do_not_overlap() -> None:
    for flag in PERMITTED_FLAGS:
        for invariant in IMMUTABLE_INVARIANTS:
            assert invariant not in flag


def test_feature_flags_are_immutable_after_load() -> None:
    flags = enforce_startup_invariants({"reference_api_enabled": True})
    with pytest.raises((AttributeError, TypeError)):
        flags.values = ()  # type: ignore[misc]
    assert isinstance(flags, FeatureFlags)


# -- §46 logging restrictions --------------------------------------------


def test_allowed_and_forbidden_log_fields_are_disjoint() -> None:
    assert not (ALLOWED_FIELDS & FORBIDDEN_LOG_FIELDS)


@pytest.mark.parametrize("field", sorted(FORBIDDEN_LOG_FIELDS))
def test_forbidden_log_field_fails_the_test_sink(field: str) -> None:
    logger = ReferenceLogger(component="voting.reference")
    with pytest.raises(ForbiddenLogFieldError):
        logger.emit("acceptance.committed", **{field: "value"})
    assert logger.records == [], "a rejected record was still written"


def test_allowed_log_fields_are_accepted() -> None:
    logger = ReferenceLogger(component="voting.reference")
    record = logger.emit(
        "acceptance.committed",
        election_context_id="fixture-a",
        coarse_time_bucket="w0",
        outcome="accepted",
        internal_transaction_id="tx-1",
    )
    assert record.reason_code == "acceptance.committed"
    assert dict(record.fields).keys() == {
        "election_context_id",
        "coarse_time_bucket",
        "outcome",
        "internal_transaction_id",
    }


def test_an_undeclared_field_is_refused_even_if_it_looks_harmless() -> None:
    logger = ReferenceLogger(component="voting.reference")
    with pytest.raises(ForbiddenLogFieldError, match="allow-list"):
        logger.emit("acceptance.committed", ballot_count=3)


def test_free_text_reason_codes_are_refused() -> None:
    logger = ReferenceLogger(component="voting.reference")
    with pytest.raises(ForbiddenLogFieldError, match="catalogue reason code"):
        logger.emit("voter cap-1 cast ballot abc")


def test_event_payloads_carry_no_forbidden_field() -> None:
    """§42's leakage expectation, applied to every persisted outbox row."""
    fixture = fixture_a()
    envelope, _ = make_ballot(fixture, {"c1": ("opt-1",)}, b"inv-event")
    submit_cast_ballot(fixture.store, fixture.runtime, fixture.capabilities[0], envelope, "k1")
    for row in fixture.store.outbox.rows:
        payload = {name: getattr(row, name) for name in row.__dataclass_fields__}
        assert scan_mapping(payload) == ()
        assert not (set(payload) & FORBIDDEN_OUTBOX_FIELDS)


# -- §47 audit evidence --------------------------------------------------


def test_audit_log_is_tamper_evident() -> None:
    log = AuditLog()
    for record_type in AuditRecordType:
        log.append(
            record_type,
            reason_code="acceptance.committed",
            election_context_id="fixture-a",
            coarse_time_bucket="w0",
            outcome="ok",
        )
    assert len(log.records) == 10
    assert log.verify_chain() is True

    tampered = log.records[3]
    log.records[3] = type(tampered)(
        sequence=tampered.sequence,
        record_type=tampered.record_type,
        reason_code="acceptance.rejected",
        election_context_id=tampered.election_context_id,
        coarse_time_bucket=tampered.coarse_time_bucket,
        outcome=tampered.outcome,
        previous_hash=tampered.previous_hash,
    )
    assert log.verify_chain() is False


def test_audit_records_reject_extra_fields() -> None:
    log = AuditLog()
    with pytest.raises(AuditFieldRejected):
        log.append(
            AuditRecordType.ATOMIC_ACCEPTANCE,
            reason_code="acceptance.committed",
            election_context_id="fixture-a",
            coarse_time_bucket="w0",
            outcome="ok",
            capability_reference="cap-1",
        )
    assert log.records == []


def test_audit_log_is_not_a_capability_to_ballot_map() -> None:
    log = AuditLog()
    record = log.append(
        AuditRecordType.ATOMIC_ACCEPTANCE,
        reason_code="acceptance.committed",
        election_context_id="fixture-a",
        coarse_time_bucket="w0",
        outcome="ok",
    )
    fields = set(record.__slots__)
    assert not (fields & {"capability_reference", "ballot_id", "voter_id", "identity"})


# -- §50 schema registry -------------------------------------------------


def test_every_required_schema_is_registered() -> None:
    required = {
        "parameter_set",
        "election_context",
        "manifest",
        "encrypted_ballot",
        "spoiled_ballot",
        "receipt",
        "batch_commitment",
        "batch_opening",
        "reconciliation_record",
        "board_entry",
        "checkpoint",
        "election_record",
        "verification_result",
    }
    assert required <= set(SCHEMA_REGISTRY)
    assert REGISTRY_VERSION == "EPD2-SCHEMA-1"


def test_every_schema_is_versioned_and_pins_its_encoding() -> None:
    for name, descriptor in SCHEMA_REGISTRY.items():
        assert descriptor.version, name
        assert descriptor.encoding_version == "EPD2-ENC-1", name
        assert descriptor.critical_fields, name


def test_migration_is_never_silent() -> None:
    with pytest.raises(UnknownSchemaError, match="never silent"):
        get_schema("receipt", "2.0.0")
    with pytest.raises(UnknownSchemaError):
        get_schema("no_such_schema")


# -- §15 test RNG cannot reach production --------------------------------


def test_test_rng_cannot_be_selected_in_production_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TEST_PROFILE_ENV, "1")
    # even with the test flag set, the production selector refuses
    assert select_source("production").is_deterministic is False
    for profile in ("test", "deterministic", "TEST", "prod"):
        with pytest.raises(DeterministicSourceForbiddenError):
            select_source(profile)


# -- §36 independent implementation boundary ------------------------------


def test_verifier_imports_no_identity_credential_or_capability_module() -> None:
    """The verifier must be runnable from public artefacts alone."""
    forbidden_modules = {
        "epd2_voting_service.reference.casting.store",
        "epd2_voting_service.reference.casting.continuation",
        "epd2_voting_service.reference.casting.transactions",
        "epd2_voting_service.reference.casting.idempotency",
        "epd2_voting_service.reference.api",
    }
    verification_dir = REFERENCE_ROOT / "verification"
    offenders: list[str] = []
    for path in sorted(verification_dir.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in forbidden_modules:
                offenders.append(f"{path.name}:{node.lineno} {node.module}")
            if isinstance(node, ast.Import):
                offenders.extend(
                    f"{path.name}:{node.lineno} {alias.name}"
                    for alias in node.names
                    if alias.name in forbidden_modules
                )
    assert offenders == [], f"verifier reaches into private state: {offenders}"


def test_verifier_names_no_capability_or_identity_symbol() -> None:
    verification_dir = REFERENCE_ROOT / "verification"
    banned = ("capability_reference", "credential_id", "voter_id", "continuation_capability")
    for path in sorted(verification_dir.rglob("*.py")):
        text = path.read_text()
        for name in banned:
            assert name not in text, f"{path.name} names {name}"


def test_no_production_module_reads_the_test_profile_environment() -> None:
    offenders: list[str] = []
    for path in sorted(REFERENCE_ROOT.rglob("*.py")):
        relative = path.relative_to(REFERENCE_ROOT)
        if relative.parts[0] in {"testing", "crypto"}:
            continue
        text = path.read_text()
        if TEST_PROFILE_ENV in text or "os.environ" in text:
            offenders.append(str(relative))
    assert offenders == [], f"production modules read the test profile flag: {offenders}"

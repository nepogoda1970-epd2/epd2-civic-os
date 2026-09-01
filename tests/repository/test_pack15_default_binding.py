"""The PACK-15 in-memory adapters are not the default runtime binding.

PACK-14's correction round established the rule and
`test_pack14_default_binding.py` enforces it there. PACK-15 adds two more
composition roots - one per side of the trust boundary - and the same
rule has to hold for both, or the architecture's central claim ("these are
two storage boundaries") reduces to "these are two dictionaries in one
process".

Four things are checked:

1. Neither composition root names an in-memory adapter.
2. A built runtime holds an `Sql*` adapter on every store port, checked by
   walking the runtime's fields rather than trusting the factory's source.
3. The identity side's two connections are two databases, and the
   factory refuses to be pointed at one.
4. The signing custody and the assertion verifier default to refusing, so
   an unconfigured deployment fails at the first call.

Must be run from the repository root, with PYTHONPATH covering the
services' `src/` directories (per `LOCAL_VERIFICATION.md`).
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

import pytest

import epd2_credential_service.voting_credential_storage as credential_memory
import epd2_eligibility_service.voting_trust_storage as eligibility_memory
from epd2_credential_service.voting_credential_application import AssertionVerifier
from epd2_credential_service.voting_credential_runtime import build_voting_credential_service
from epd2_eligibility_service.voting_assertion_issuer import FutureKeyServiceCustody
from epd2_eligibility_service.voting_trust_exceptions import SystemDependencyUnavailableError
from epd2_eligibility_service.voting_trust_runtime import build_voting_trust_runtime
from epd2_eligibility_service.voting_trust_sql_storage import StorageBoundaryViolationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ELIGIBILITY_RUNTIME_SOURCE = (
    REPO_ROOT
    / "services"
    / "eligibility-service"
    / "src"
    / "epd2_eligibility_service"
    / "voting_trust_runtime.py"
)
CREDENTIAL_RUNTIME_SOURCE = (
    REPO_ROOT
    / "services"
    / "credential-service"
    / "src"
    / "epd2_credential_service"
    / "voting_credential_runtime.py"
)

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)

#: One entry per store field of `VotingTrustRuntime`. A port added
#: without a durable adapter shows up here as a missing key rather than as
#: a silent in-memory default.
IDENTITY_SIDE_STORE_FIELDS: dict[str, str] = {
    "case_store": "SqlEligibilityCaseStore",
    "participation_ledger": "SqlParticipationUnitLedger",
    "assertion_store": "SqlAssertionIssuerStore",
    "handoff_store": "SqlHandoffAcceptanceStore",
}

VOTING_SIDE_STORE_FIELDS: dict[str, str] = {
    "credentials": "SqlVotingCredentialStore",
    "spent_nonces": "SqlSpentNonceSet",
    "idempotency": "SqlCredentialIdempotencyStore",
    "redemptions": "SqlCredentialRedemptionStore",
    "replays": "SqlCredentialReplayStore",
}


def _in_memory_names(module: object) -> set[str]:
    return {
        name
        for name in vars(module)
        if name.startswith("InMemory") and isinstance(getattr(module, name), type)
    }


def _verifier() -> AssertionVerifier:
    return AssertionVerifier(
        verify=lambda message, signature: False,
        expected_audience="voting-credential-issuer",
    )


# =============================================================================
# 1. What the composition roots name
# =============================================================================


@pytest.mark.parametrize(
    "source_path",
    [ELIGIBILITY_RUNTIME_SOURCE, CREDENTIAL_RUNTIME_SOURCE],
)
def test_no_pack15_composition_root_names_an_in_memory_adapter(source_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")
    named = set(re.findall(r"\bInMemory[A-Za-z0-9_]*", source))
    assert not named, f"{source_path.name} binds in-memory adapters: {sorted(named)}"


def test_every_pack15_in_memory_adapter_lives_outside_the_composition_roots() -> None:
    """The test adapters exist; they are simply not what a runtime picks."""
    adapters = _in_memory_names(eligibility_memory) | _in_memory_names(credential_memory)
    assert len(adapters) >= 8, "the PACK-15 test adapters were removed rather than demoted"
    for source_path in (ELIGIBILITY_RUNTIME_SOURCE, CREDENTIAL_RUNTIME_SOURCE):
        source = source_path.read_text(encoding="utf-8")
        for adapter in adapters:
            assert adapter not in source, f"{adapter} is bound by {source_path.name}"


def test_each_pack15_sql_adapter_has_an_in_memory_counterpart() -> None:
    """An SQL adapter with no test double makes unit tests reach for a
    database; a test double with no SQL adapter is an aggregate that never
    became durable."""
    import epd2_credential_service.voting_credential_sql_storage as credential_sql
    import epd2_eligibility_service.voting_trust_sql_storage as eligibility_sql

    for sql_module, memory_module in (
        (eligibility_sql, eligibility_memory),
        (credential_sql, credential_memory),
    ):
        sql_names = {
            name.removeprefix("Sql")
            for name in vars(sql_module)
            if name.startswith("Sql") and isinstance(getattr(sql_module, name), type)
        }
        memory_names = {name.removeprefix("InMemory") for name in _in_memory_names(memory_module)}
        missing = sorted(sql_names - memory_names)
        assert not missing, f"SQL adapters with no test counterpart: {missing}"


# =============================================================================
# 2. What a built runtime actually holds
# =============================================================================


def test_the_identity_side_runtime_holds_a_sql_adapter_on_every_store_port() -> None:
    with tempfile.TemporaryDirectory() as directory:
        runtime = build_voting_trust_runtime(
            applied_at=NOW,
            audience="voting-credential-issuer",
            eligibility_database=str(Path(directory) / "eligibility.db"),
            assertion_issuer_database=str(Path(directory) / "issuer.db"),
        )
        try:
            bound = {field.name for field in fields(runtime)}
            missing = set(IDENTITY_SIDE_STORE_FIELDS) - bound
            assert not missing, f"declared store ports that no longer exist: {sorted(missing)}"
            for field_name, expected in IDENTITY_SIDE_STORE_FIELDS.items():
                adapter = getattr(runtime, field_name)
                assert type(adapter).__name__ == expected, (
                    f"{field_name} is bound to {type(adapter).__name__}, not {expected}"
                )
        finally:
            runtime.close()


def test_the_voting_side_runtime_holds_a_sql_adapter_on_every_store_port() -> None:
    runtime = build_voting_credential_service(
        applied_at=NOW,
        verifier=_verifier(),
        allowed_origins=("https://vote.example",),
    )
    try:
        for field_name, expected in VOTING_SIDE_STORE_FIELDS.items():
            adapter = getattr(runtime.service, field_name)
            assert type(adapter).__name__ == expected, (
                f"{field_name} is bound to {type(adapter).__name__}, not {expected}"
            )
    finally:
        runtime.close()


def test_no_field_of_a_built_runtime_is_an_in_memory_adapter() -> None:
    """Walks the runtime rather than the factory's source, so a binding
    made through a default argument is caught too."""
    eligibility_adapters = tuple(
        getattr(eligibility_memory, name) for name in _in_memory_names(eligibility_memory)
    )
    credential_adapters = tuple(
        getattr(credential_memory, name) for name in _in_memory_names(credential_memory)
    )
    with tempfile.TemporaryDirectory() as directory:
        identity = build_voting_trust_runtime(
            applied_at=NOW,
            audience="voting-credential-issuer",
            eligibility_database=str(Path(directory) / "eligibility.db"),
            assertion_issuer_database=str(Path(directory) / "issuer.db"),
        )
        try:
            for field in fields(identity):
                assert not isinstance(getattr(identity, field.name), eligibility_adapters)
        finally:
            identity.close()

    voting = build_voting_credential_service(
        applied_at=NOW,
        verifier=_verifier(),
        allowed_origins=("https://vote.example",),
    )
    try:
        for field in fields(voting.service):
            assert not isinstance(getattr(voting.service, field.name), credential_adapters)
    finally:
        voting.close()


# =============================================================================
# 3. Two boundaries, two databases
# =============================================================================


def test_the_identity_side_runtime_opens_two_separate_databases() -> None:
    with tempfile.TemporaryDirectory() as directory:
        runtime = build_voting_trust_runtime(
            applied_at=NOW,
            audience="voting-credential-issuer",
            eligibility_database=str(Path(directory) / "eligibility.db"),
            assertion_issuer_database=str(Path(directory) / "issuer.db"),
        )
        try:
            assert runtime.eligibility_connection is not runtime.assertion_issuer_connection
            eligibility_tables = {
                row[0]
                for row in runtime.eligibility_connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            issuer_tables = {
                row[0]
                for row in runtime.assertion_issuer_connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            assert "eligibility_case" in eligibility_tables
            assert "eligibility_case" not in issuer_tables
            assert "eligibility_assertion" in issuer_tables
            assert "eligibility_assertion" not in eligibility_tables
        finally:
            runtime.close()


def test_pointing_both_identity_side_stores_at_one_database_is_refused() -> None:
    with tempfile.TemporaryDirectory() as directory:
        shared = str(Path(directory) / "one.db")
        with pytest.raises(StorageBoundaryViolationError):
            build_voting_trust_runtime(
                applied_at=NOW,
                audience="voting-credential-issuer",
                eligibility_database=shared,
                assertion_issuer_database=shared,
            )


def test_the_identity_side_factory_has_no_default_database_at_all() -> None:
    """Naming both databases is required, not defaulted.

    A default would have to be either one shared database - which
    collapses the boundary - or a pair of names the caller never chose,
    which is a deployment shape arrived at by omission.
    """
    import inspect

    signature = inspect.signature(build_voting_trust_runtime)
    for name in ("eligibility_database", "assertion_issuer_database"):
        assert signature.parameters[name].default is inspect.Parameter.empty


# =============================================================================
# 4. The security ports refuse by default
# =============================================================================


def test_the_assertion_signing_custody_defaults_to_an_adapter_that_refuses() -> None:
    with tempfile.TemporaryDirectory() as directory:
        runtime = build_voting_trust_runtime(
            applied_at=NOW,
            audience="voting-credential-issuer",
            eligibility_database=str(Path(directory) / "eligibility.db"),
            assertion_issuer_database=str(Path(directory) / "issuer.db"),
        )
        try:
            assert isinstance(runtime.issuer.custody, FutureKeyServiceCustody)
            with pytest.raises(SystemDependencyUnavailableError):
                runtime.issuer.custody.key_identifier()
        finally:
            runtime.close()


def test_the_voting_side_factory_has_no_default_verifier() -> None:
    """There is no fallback verifier that accepts.

    The alternative to "a deployment must bind a verifier" is "an
    unconfigured deployment issues credentials against unverified
    assertions", which is not a degraded mode but the absence of the trust
    boundary.
    """
    import inspect

    signature = inspect.signature(build_voting_credential_service)
    assert signature.parameters["verifier"].default is inspect.Parameter.empty

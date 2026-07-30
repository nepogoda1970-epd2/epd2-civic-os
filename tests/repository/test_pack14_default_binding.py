"""The in-memory adapters are not the default runtime binding.

The correction round's premise was that PACK-14 shipped with nothing but
in-memory storage. The adapters still exist - they are the cheapest way
to unit-test a domain rule - but they are now **test** adapters, and the
difference between "test adapter" and "default adapter" is exactly one
composition root. This file is what keeps that difference real:

1. `epd2_identity_service.runtime` names no in-memory adapter except the
   audit store, which is a documented deployment binding because
   `audit-core` owns durable audit persistence.
2. A runtime built by `build_identity_service` holds SQL adapters on
   every store port, checked by walking the service's actual fields
   rather than by trusting the factory's source.
3. Every in-memory adapter still satisfies the protocol its SQL
   counterpart does, so the test adapters remain usable *as* test
   adapters and do not quietly rot.
4. The security ports default to adapters that refuse.

Must be run from the repository root (with PYTHONPATH covering the
services' `src/` directories, per `LOCAL_VERIFICATION.md`).
"""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

import epd2_identity_service.account_security_storage as in_memory_storage
import epd2_identity_service.runtime as runtime_module
import epd2_identity_service.sql_storage as sql_storage
from epd2_identity_service.passkeys import UnboundWebAuthnVerifier
from epd2_identity_service.runtime import build_identity_service
from epd2_identity_service.secret_storage import (
    UnavailablePasswordHasher,
    UnboundBreachedPasswordChecker,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME_SOURCE = (
    REPO_ROOT / "services" / "identity-service" / "src" / "epd2_identity_service" / "runtime.py"
)

#: The one in-memory adapter the composition root may name, and the
#: reason it may. `epd2_audit_core` owns durable audit persistence;
#: PACK-14 appends through its governed ingestion contract and does not
#: get to bind that service's storage on its behalf. `runtime.py` records
#: the same reason in prose next to the binding.
PERMITTED_IN_MEMORY_BINDING = "InMemoryAuditEventStore"

#: The store ports whose default binding must be durable. One name per
#: constructor argument of `AccountSecurityService`, so a port added
#: without a durable adapter shows up here as a missing key rather than
#: as a silent in-memory default.
DURABLE_STORE_FIELDS: dict[str, str] = {
    "account_store": "SqlAccountRegistryStore",
    "contact_store": "SqlAccountContactStore",
    "credential_store": "SqlCredentialStore",
    "authentication_store": "SqlAuthenticationStore",
    "session_store": "SqlSessionStore",
    "recovery_store": "SqlRecoveryStore",
    "proofing_store": "SqlIdentityProofingStore",
    "bootstrap_store": "SqlBootstrapStore",
    "voting_handoff_store": "SqlVotingHandoffStore",
    "mapping_store": "SqlIdentityMappingStore",
    "replay_store": "SqlReplayPreventionStore",
}

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
SALT = b"pack-14-default-binding-test-salt"


def _clock() -> object:
    class _FixedClock:
        def now(self) -> datetime:
            return NOW

    return _FixedClock()


def _in_memory_adapter_names() -> set[str]:
    return {
        name
        for name in vars(in_memory_storage)
        if name.startswith("InMemory") and isinstance(getattr(in_memory_storage, name), type)
    }


# =============================================================================
# 1. The composition root's source
# =============================================================================


def test_the_composition_root_names_no_in_memory_store_adapter() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    named = set(re.findall(r"\bInMemory[A-Za-z0-9_]*", source))
    assert named <= {PERMITTED_IN_MEMORY_BINDING}, (
        f"the runtime composition root binds in-memory adapters: "
        f"{sorted(named - {PERMITTED_IN_MEMORY_BINDING})}"
    )


def test_the_permitted_in_memory_binding_is_documented_where_it_is_made() -> None:
    """A permitted exception with no recorded reason becomes an
    unexamined default the next time someone reads the file."""
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    assert "audit-core" in source
    assert "AUDIT_STORE_IS_A_DEPLOYMENT_BINDING" in source


def test_every_in_memory_adapter_lives_outside_the_composition_root() -> None:
    """The adapters exist; they are simply not what the runtime picks."""
    adapters = _in_memory_adapter_names()
    assert len(adapters) >= 11, "the test adapters were removed rather than demoted"
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    for adapter in adapters:
        assert adapter not in source, f"{adapter} is bound by the composition root"


# =============================================================================
# 2. What a built runtime actually holds
# =============================================================================


def test_a_built_runtime_holds_a_sql_adapter_on_every_store_port() -> None:
    runtime = build_identity_service(clock=_clock(), derivation_salt=SALT)  # type: ignore[arg-type]
    try:
        bound = {field.name for field in fields(runtime.service)}
        missing = set(DURABLE_STORE_FIELDS) - bound
        assert not missing, f"declared store ports that no longer exist: {sorted(missing)}"
        for field_name, expected in DURABLE_STORE_FIELDS.items():
            adapter = getattr(runtime.service, field_name)
            assert type(adapter).__name__ == expected, (
                f"{field_name} is bound to {type(adapter).__name__}, not {expected}"
            )
    finally:
        runtime.connection.close()


def test_no_field_of_a_built_runtime_is_an_in_memory_store_adapter() -> None:
    """Walks the service rather than the factory's source, so a binding
    added through a default argument is caught too."""
    adapters = tuple(getattr(in_memory_storage, name) for name in _in_memory_adapter_names())
    runtime = build_identity_service(clock=_clock(), derivation_salt=SALT)  # type: ignore[arg-type]
    try:
        for field in fields(runtime.service):
            value = getattr(runtime.service, field.name)
            assert not isinstance(value, adapters), (
                f"{field.name} is bound to the test adapter {type(value).__name__}"
            )
    finally:
        runtime.connection.close()


def test_a_built_runtime_carries_a_unit_of_work() -> None:
    """Transaction boundaries are part of the default binding, not an
    opt-in a caller has to remember."""
    runtime = build_identity_service(clock=_clock(), derivation_salt=SALT)  # type: ignore[arg-type]
    try:
        assert isinstance(runtime.service.unit_of_work, sql_storage.UnitOfWork)
    finally:
        runtime.connection.close()


# =============================================================================
# 3. The test adapters still satisfy the protocols
# =============================================================================


def test_each_sql_adapter_has_an_in_memory_counterpart_and_the_reverse() -> None:
    """Drift in either direction is a problem: an SQL adapter with no
    test double makes unit tests reach for the database, and a test
    double with no SQL adapter is an aggregate that never became
    durable."""
    sql_names = {
        name.removeprefix("Sql")
        for name in vars(sql_storage)
        if name.startswith("Sql") and isinstance(getattr(sql_storage, name), type)
    }
    memory_names = {name.removeprefix("InMemory") for name in _in_memory_adapter_names()}
    assert sql_names <= memory_names, (
        f"SQL adapters with no test counterpart: {sorted(sql_names - memory_names)}"
    )


# =============================================================================
# 4. The security ports refuse by default
# =============================================================================


def test_the_security_ports_default_to_adapters_that_refuse() -> None:
    runtime = build_identity_service(clock=_clock(), derivation_salt=SALT)  # type: ignore[arg-type]
    try:
        assert isinstance(runtime.service.breach_checker, UnboundBreachedPasswordChecker)
        assert isinstance(runtime.service.password_hasher, UnavailablePasswordHasher)
        assert isinstance(runtime.service.webauthn_verifier, UnboundWebAuthnVerifier)
    finally:
        runtime.connection.close()


def test_the_module_exports_a_single_composition_root() -> None:
    """Two factories become two sets of defaults, and the second one is
    always the one nobody audits."""
    factories = [
        name
        for name, value in vars(runtime_module).items()
        if callable(value)
        and getattr(value, "__module__", None) == runtime_module.__name__
        and not name.startswith("_")
        and not isinstance(value, type)
    ]
    assert factories == ["build_identity_service"]

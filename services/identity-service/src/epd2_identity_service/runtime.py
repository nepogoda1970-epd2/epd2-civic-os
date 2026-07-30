"""The runtime composition root.

One function, and it is the answer to "what does this service actually
run with". `build_identity_service` binds the **durable** adapters from
`sql_storage`, opens the connection through the migration runner so the
schema is applied and verified before anything reads it, and binds the
fail-closed security ports.

**The in-memory adapters are not the default runtime binding.** They
remain in `account_security_storage` as explicit test adapters, and
`tests/repository/test_pack14_default_binding.py` asserts that this
module names none of them.

What a deployment still has to bind is unchanged and is not hidden by
this factory: a WebAuthn verifier, a memory-hard password hasher, a
breached-password checker and an assertion signature verifier all default
to adapters that **refuse**, so an unconfigured deployment fails at the
first attempt rather than after an incident.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from epd2_audit_core.storage import AuditEventStore, InMemoryAuditEventStore
from epd2_core.clock import Clock
from epd2_identity_service.account_security_application import (
    AccountSecurityService,
    NotificationOutbox,
)
from epd2_identity_service.migration_runner import open_migrated
from epd2_identity_service.observability import MetricsRecorder
from epd2_identity_service.passkeys import UnboundWebAuthnVerifier, WebAuthnVerifier
from epd2_identity_service.secret_storage import (
    BreachedPasswordChecker,
    PasswordHasher,
    SecureRandom,
    SystemSecureRandom,
    TotpVerifier,
    UnavailablePasswordHasher,
    UnboundBreachedPasswordChecker,
)
from epd2_identity_service.service_api import IdentityServiceApi
from epd2_identity_service.sql_storage import (
    SqlAccountContactStore,
    SqlAccountRegistryStore,
    SqlAuthenticationStore,
    SqlBootstrapStore,
    SqlCredentialStore,
    SqlIdentityMappingStore,
    SqlIdentityProofingStore,
    SqlRecoveryStore,
    SqlReplayPreventionStore,
    SqlSessionStore,
    SqlVotingHandoffStore,
    UnitOfWork,
)


@dataclass(frozen=True, slots=True)
class IdentityRuntime:
    """Everything a caller needs, and the connection it all shares."""

    connection: sqlite3.Connection
    service: AccountSecurityService
    api: IdentityServiceApi


def build_identity_service(
    *,
    clock: Clock,
    derivation_salt: bytes,
    database: str = ":memory:",
    applied_at: datetime | None = None,
    audit_store: AuditEventStore | None = None,
    random: SecureRandom | None = None,
    password_hasher: PasswordHasher | None = None,
    breach_checker: BreachedPasswordChecker | None = None,
    totp_verifier: TotpVerifier | None = None,
    webauthn_verifier: WebAuthnVerifier | None = None,
) -> IdentityRuntime:
    """Build the service on the durable reference persistence path.

    `database=":memory:"` is a **SQLite** in-memory database, not the
    in-memory *adapters*: the migrations run against it, the constraints
    and indexes exist, and every write goes through the same SQL the
    file-backed path uses. Passing a filename is what makes state survive
    a restart, and that is exactly what
    `test_pack14_persistence.py` does.
    """
    connection = open_migrated(database, applied_at=applied_at or clock.now())
    unit_of_work = UnitOfWork(connection=connection)
    service = AccountSecurityService(
        account_store=SqlAccountRegistryStore(connection),
        contact_store=SqlAccountContactStore(connection),
        credential_store=SqlCredentialStore(connection),
        authentication_store=SqlAuthenticationStore(connection),
        session_store=SqlSessionStore(connection),
        recovery_store=SqlRecoveryStore(connection),
        proofing_store=SqlIdentityProofingStore(connection),
        bootstrap_store=SqlBootstrapStore(connection),
        voting_handoff_store=SqlVotingHandoffStore(connection),
        mapping_store=SqlIdentityMappingStore(connection),
        replay_store=SqlReplayPreventionStore(connection),
        audit_store=audit_store if audit_store is not None else InMemoryAuditEventStore(),
        clock=clock,
        derivation_salt=derivation_salt,
        random=random if random is not None else SystemSecureRandom(),
        # Every security port below defaults to the adapter that refuses.
        password_hasher=(
            password_hasher if password_hasher is not None else UnavailablePasswordHasher()
        ),
        breach_checker=(
            breach_checker if breach_checker is not None else UnboundBreachedPasswordChecker()
        ),
        totp_verifier=totp_verifier,  # type: ignore[arg-type]
        webauthn_verifier=(
            webauthn_verifier if webauthn_verifier is not None else UnboundWebAuthnVerifier()
        ),
        outbox=NotificationOutbox(),
        metrics=MetricsRecorder(),
        unit_of_work=unit_of_work,
    )
    return IdentityRuntime(connection=connection, service=service, api=IdentityServiceApi(service))


#: The audit store is the one port this factory still binds in memory,
#: and it is recorded here rather than glossed: `audit-core` owns durable
#: audit persistence, PACK-14 appends through its governed ingestion
#: contract, and binding a durable audit adapter is that service's round
#: to do. A deployment passes its own `audit_store` in the meantime.
AUDIT_STORE_IS_A_DEPLOYMENT_BINDING = True

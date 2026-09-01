"""The PACK-15 voting-side composition root.

`build_voting_credential_service` binds the **durable** adapters from
`voting_credential_sql_storage`, opens the voting-side database through
the migration runner, and returns the issuer service.

**The in-memory adapters are not the default runtime binding.** They stay
in `voting_credential_storage` as explicit test adapters, and
`tests/repository/test_pack15_default_binding.py` asserts this module
names none of them.

The assertion verifier is a required argument with no default. There is
no fallback verifier that accepts, because the alternative to "a
deployment must bind a verifier" is "an unconfigured deployment issues
credentials against unverified assertions", and the second is not a
degraded mode - it is the absence of the trust boundary.

This factory opens exactly one connection, and it is a **different
database file** from either identity-side database. That is what makes a
foreign key from a credential to an assertion inexpressible rather than
merely unwritten (ADR-093).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from epd2_credential_service.voting_credential_application import (
    DEFAULT_IDEMPOTENCY_WINDOW_SECONDS,
    AssertionVerifier,
    VotingCredentialIssuerService,
)
from epd2_credential_service.voting_credential_sql_storage import (
    SqlCredentialIdempotencyStore,
    SqlCredentialRedemptionStore,
    SqlCredentialReplayStore,
    SqlSpentNonceSet,
    SqlVotingCredentialStore,
    open_voting_side_database,
)


@dataclass(frozen=True, slots=True)
class VotingCredentialRuntime:
    connection: sqlite3.Connection
    service: VotingCredentialIssuerService

    def close(self) -> None:
        self.connection.close()


def build_voting_credential_service(
    *,
    applied_at: datetime,
    verifier: AssertionVerifier,
    allowed_origins: tuple[str, ...],
    database: str = ":memory:",
    idempotency_window_seconds: int = DEFAULT_IDEMPOTENCY_WINDOW_SECONDS,
) -> VotingCredentialRuntime:
    """Build the voting side on the durable reference persistence path.

    `database=":memory:"` is a **SQLite** in-memory database, not the
    in-memory *adapters*: the migrations run against it, so the spent-nonce
    primary key and the redemption unique index exist and every write goes
    through the same SQL the file-backed path uses.
    """
    connection = open_voting_side_database(database, applied_at=applied_at)
    service = VotingCredentialIssuerService(
        credentials=SqlVotingCredentialStore(connection),
        spent_nonces=SqlSpentNonceSet(connection),
        idempotency=SqlCredentialIdempotencyStore(connection),
        redemptions=SqlCredentialRedemptionStore(connection),
        replays=SqlCredentialReplayStore(connection),
        verifier=verifier,
        allowed_origins=allowed_origins,
        idempotency_window_seconds=idempotency_window_seconds,
    )
    return VotingCredentialRuntime(connection=connection, service=service)

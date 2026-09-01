"""The PACK-15 identity-side composition root.

One function, and it is the answer to "what does the eligibility side
actually run with". `build_voting_trust_runtime` binds the **durable**
adapters from `voting_trust_sql_storage`, opens each database through the
migration runner so the schema is applied and verified before anything
reads it, and binds the signing custody fail-closed.

**The in-memory adapters are not the default runtime binding.** They
remain in `voting_trust_storage` as explicit test adapters, and
`tests/repository/test_pack15_default_binding.py` asserts that this
module names none of them.

Two connections, never one. The eligibility database and the Assertion
Issuer database are opened separately and handed to separate stores, so
this factory cannot produce a runtime in which one transaction spans both
(`OD-P15-01`). `assert_storage_boundaries_are_separate` refuses a
deployment that points them at the same file.

Key custody defaults to `FutureKeyServiceCustody`, whose every method
raises: an unconfigured deployment fails at the first mint rather than
signing real assertions with a default key.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from epd2_eligibility_service.voting_assertion_issuer import (
    AssertionIssuer,
    AssertionSigningKeyCustody,
    FutureKeyServiceCustody,
    SecureRandom,
    SystemSecureRandom,
)
from epd2_eligibility_service.voting_timing import IssuanceTimingProfile
from epd2_eligibility_service.voting_trust_sql_storage import (
    SqlAssertionIssuerStore,
    SqlEligibilityCaseStore,
    SqlHandoffAcceptanceStore,
    SqlParticipationUnitLedger,
    assert_storage_boundaries_are_separate,
    open_assertion_issuer_database,
    open_eligibility_database,
)


@dataclass(frozen=True, slots=True)
class VotingTrustRuntime:
    """Everything the identity side needs, and the two connections it uses.

    The connections are separate fields rather than one, because a single
    field would be an invitation to open one transaction across both
    boundaries.
    """

    eligibility_connection: sqlite3.Connection
    assertion_issuer_connection: sqlite3.Connection
    case_store: SqlEligibilityCaseStore
    participation_ledger: SqlParticipationUnitLedger
    assertion_store: SqlAssertionIssuerStore
    handoff_store: SqlHandoffAcceptanceStore
    issuer: AssertionIssuer

    def close(self) -> None:
        self.eligibility_connection.close()
        self.assertion_issuer_connection.close()


def build_voting_trust_runtime(
    *,
    applied_at: datetime,
    audience: str,
    eligibility_database: str,
    assertion_issuer_database: str,
    profile: IssuanceTimingProfile | None = None,
    custody: AssertionSigningKeyCustody | None = None,
    random: SecureRandom | None = None,
) -> VotingTrustRuntime:
    """Build the identity side on the durable reference persistence path.

    Both databases are **required arguments with no defaults**, unlike the
    PACK-14 factory's `database=":memory:"`. A default here would have to
    be either one shared database - which collapses the boundary this
    round exists to create - or a pair of names a caller never chose,
    which is a deployment shape arrived at by omission. Naming them is
    cheap; a test passes two temporary paths, and
    `services/eligibility-service/tests/test_pack15_persistence.py` does.
    """
    assert_storage_boundaries_are_separate(eligibility_database, assertion_issuer_database)
    eligibility_connection = open_eligibility_database(eligibility_database, applied_at=applied_at)
    assertion_issuer_connection = open_assertion_issuer_database(
        assertion_issuer_database, applied_at=applied_at
    )
    return VotingTrustRuntime(
        eligibility_connection=eligibility_connection,
        assertion_issuer_connection=assertion_issuer_connection,
        case_store=SqlEligibilityCaseStore(eligibility_connection),
        participation_ledger=SqlParticipationUnitLedger(eligibility_connection),
        assertion_store=SqlAssertionIssuerStore(assertion_issuer_connection),
        handoff_store=SqlHandoffAcceptanceStore(assertion_issuer_connection),
        issuer=AssertionIssuer(
            # Fail-closed: an unbound key service refuses every call.
            custody=custody if custody is not None else FutureKeyServiceCustody(),
            random=random if random is not None else SystemSecureRandom(),
            profile=profile if profile is not None else IssuanceTimingProfile(),
            audience=audience,
        ),
    )

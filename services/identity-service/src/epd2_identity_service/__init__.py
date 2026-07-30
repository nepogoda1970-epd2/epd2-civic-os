"""EPD2 Civic OS Identity Service.

Owns canon 7.3's `IdentityRecord` (PACK-02), canon 19d.2's additive
identity attributes and canon 19d.8's `AuthenticationContext` (PACK-07),
and - from PACK-14 - the Account Registry, Credential Registry,
Authentication, Session Security, Recovery coordination and
Identity-Proofing-reference contexts (ADR-079 through ADR-088).

**PACK-14 IMPLEMENTATION CANDIDATE. NOT PASS. NOT PRODUCTION READY. NOT
LEGALLY ACTIVATED.**

## The PACK-14 module map, in dependency order

Each module imports only from those above it.

- `exceptions` - one class per registered reason code, no domain
  knowledge. **No generic `AUTH_ERROR` and none may be added.**
- `identifiers` - the five identifier spaces as distinct types, the
  purpose-scoped reference derivation, and the payload-key prohibition
  every event and audit record passes through.
- `secret_storage` - the ports for password hashing, TOTP, secure random
  and breach checking, plus token hashing at rest. **No cryptographic
  primitive is implemented here.**
- `configuration` - the governed timeouts and freshness windows, with the
  rules that stricter is free and relaxing is governed.
- `workspaces` - the ten workspaces from the server side, and WS-03's
  structural refusal of an ordinary session.
- `accounts` - lifecycle without extending the canonical status enum:
  `AccountLock`, `AccountRestriction`, `AccountClosureRequest`.
- `contacts` - mutable attributes, never identifiers; no auto-merge.
- `credentials`, `passkeys`, `passwords`, `mfa` - the credential
  registry, the WebAuthn **boundary**, the fenced password fallback, and
  the factor classes with `sms_otp` deliberately absent.
- `assurance` - canon's four-value scale reused, the method ceilings, and
  the fail-closed conjunction.
- `sessions`, `stepup` - the session aggregate with two mandatory
  deadlines, and confirmations bound to an action and an object version.
- `bootstrap`, `voting_handoff` - the per-workspace ceremony that is not
  SSO, and the identity-free artifact that is WS-03's only entry.
- `recovery`, `proofing`, `providers`, `linking` - the governed recovery
  workflow, the proofing boundary, the provider adapter contract, and the
  four merges that never happen.
- `administration` - PACK-12's model applied here; no new privileged
  mechanism, no universal identity console.
- `authentication`, `observability`, `forms`, `persistence` - attempt and
  risk records with enumeration resistance, privacy-preserving metrics,
  governed forms and content, and the persistence contract.
- `account_security_events`, `account_security_storage`,
  `account_security_application`, `api` - fifty-nine events on PACK-13's
  unchanged envelope, the storage **ports** and their test adapters, the
  governed commands, and the API catalogue of forty-two operations.
- `codecs`, `migration_runner`, `sql_storage`, `service_api`, `runtime` -
  the **reference persistence path** and the **runnable reference
  boundary**. Ten SQL artefacts in `../migrations/`, applied in order in
  a transaction with a recorded checksum; eleven durable adapters; a
  `UnitOfWork`; an optimistic-concurrency guard; a transport-agnostic
  request/response adapter for twelve of the forty-two operations; and
  one composition root that binds all of it.

  **The in-memory adapters in `account_security_storage` are test
  adapters, not the default runtime binding.** `runtime` names none of
  them, and `tests/repository/test_pack14_default_binding.py` asserts it.

## What this service is not

It integrates **no production IAM, no eID scheme, no email provider and
no SMS provider**. It implements **no WebAuthn cryptography and no
password hashing algorithm** - both are ports, and the default binding
for each refuses, as do the breached-password and assertion-signature
ports. **No password may be enrolled or replaced while no breach checker
is bound.**

It deploys **no production database**. The persistence path is a
*reference* path on SQLite through the standard library: real migrations,
real constraints, real transactions, no replication, no backup, no
failover, no claim of operational durability. It exposes **no HTTP
surface and no production gateway**; `service_api` is transport-agnostic
and binding it to a transport is a deployment's job.

It builds **no Voting Client**: eligibility assertion,
voting credential issuance, ballot casting, verification and tally are
PACK-15/16, and PACK-14 defines only the boundary the handoff artifact
crosses. It creates **no global user ID**, no parallel authentication
service, no second privileged model and no second evidence store.

## No claim of production readiness or legal validity

Nothing here establishes that an identity has been verified in law, that
a session is operationally safe at scale, or that any retention duration
is lawful - `OD-P14-07` is open. See
`docs/packs/PACK-14/PACK-14-OPEN-ITEMS.md`.
"""

from __future__ import annotations

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

#: The truthful status of the six contexts this service implements for
#: PACK-14: the governed workflows, the refusal surface and the boundary
#: guarantees are real and tested; no production identity infrastructure
#: exists behind them.
IDENTITY_CONTEXT_IMPLEMENTATION_STATUS = "reference_implementation"

#: The FIR entries this package fully implements. Empty by design: every
#: entry the PACK-14 FIR Coverage Matrix touches is foundation-only,
#: contract-only, or a recorded dependency on a provider, a legal
#: confirmation or a later pack - and a contract is not an
#: implementation.
IMPLEMENTED_FIR_ENTRIES: tuple[str, ...] = ()

#: PACK-14's own roadmap entry is a **candidate** until an external
#: pipeline says otherwise. Recorded so a test can assert it.
CANDIDATE_FIR_ENTRIES: tuple[str, ...] = ("FIR-ROADMAP-004",)

__all__ = [
    "CANDIDATE_FIR_ENTRIES",
    "CANON_VERSION",
    "IDENTITY_CONTEXT_IMPLEMENTATION_STATUS",
    "IMPLEMENTED_FIR_ENTRIES",
    "REPOSITORY_VERSION",
]

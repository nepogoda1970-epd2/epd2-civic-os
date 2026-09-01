"""Secret material: where it may live, and what this package refuses to
invent.

Two prohibitions from the implementation task shape this whole module and
are worth stating where a contributor will read them:

- **No placeholder security behaviour.** Nothing here pretends to be a
  password hash, a KDF or a signature verifier. Every genuinely
  cryptographic operation is a **port** - a `Protocol` a deployment
  satisfies with a real, audited library - and the in-memory reference
  adapters below are explicit, self-declaring test doubles that refuse to
  be mistaken for production ones.
- **No home-made production cryptography.** This package computes SHA-256
  digests for token-hashing-at-rest and for reference derivation, which
  are ordinary hashing rather than an invented primitive, and it computes
  nothing else. There is no bespoke KDF, no bespoke MAC and no bespoke
  signature scheme anywhere in `identity-service`.

What that leaves is the part this pack *can* honestly own: the rule that
a secret is never stored in a recoverable form, never appears in an
event, an audit record, a metric label or a log line, and is compared in
constant time when it is compared at all.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets as stdlib_secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from epd2_identity_service.exceptions import (
    BreachCheckUnavailableError,
    SecretInPayloadRefusedError,
)

#: Length of the opaque values this package mints (bootstrap responses,
#: voting handoff artifacts, verification codes, session tokens). 32
#: bytes of `secrets.token_bytes` entropy, rendered URL-safe.
OPAQUE_VALUE_BYTES = 32


class SecureRandom(Protocol):
    """The secure-random port.

    A port rather than a direct call so a deterministic test provider can
    be substituted without any production code path acquiring a "test
    mode" branch - a branch that, once it exists, is one configuration
    mistake away from being taken in production.
    """

    def token(self, byte_length: int = OPAQUE_VALUE_BYTES) -> str: ...

    def bytes(self, byte_length: int) -> bytes: ...


class SystemSecureRandom:
    """The real adapter: the standard library's CSPRNG, unmodified."""

    def token(self, byte_length: int = OPAQUE_VALUE_BYTES) -> str:
        return stdlib_secrets.token_urlsafe(byte_length)

    def bytes(self, byte_length: int) -> bytes:
        return stdlib_secrets.token_bytes(byte_length)


class DeterministicSecureRandom:
    """A **test double**, not a random source.

    Named so no reader mistakes it for one, and deliberately not
    importable through a flag on `SystemSecureRandom`. It emits a
    counter-derived value so a test can assert on an exact artifact
    without any production adapter learning to be predictable.
    """

    def __init__(self, seed: str = "pack-14-test") -> None:
        self._seed = seed
        self._counter = 0

    def token(self, byte_length: int = OPAQUE_VALUE_BYTES) -> str:
        return self.bytes(byte_length).hex()

    def bytes(self, byte_length: int) -> bytes:
        self._counter += 1
        material = b""
        block = 0
        while len(material) < byte_length:
            digest = hashlib.sha256(f"{self._seed}:{self._counter}:{block}".encode()).digest()
            material += digest
            block += 1
        return material[:byte_length]


class PasswordHasher(Protocol):
    """The password-hashing port.

    A deployment binds this to a modern memory-hard algorithm - Argon2id
    or scrypt with governed parameters. **This package does not implement
    one**, because a hand-rolled password hash is precisely the
    "placeholder security behaviour" the task forbids, and a placeholder
    that verifies correctly in tests is the most dangerous kind.
    """

    #: A short, stable label recorded on the credential so an operator can
    #: tell which algorithm a stored hash was produced by, and so a
    #: rehash-on-login policy can act on it. Never the parameters, never
    #: the salt, never the hash.
    algorithm_label: str

    def hash(self, password: str) -> str: ...

    def verify(self, password: str, stored_hash: str) -> bool: ...

    def needs_rehash(self, stored_hash: str) -> bool: ...


class UnavailablePasswordHasher:
    """The default binding: refuses.

    A deployment that has not bound a real memory-hard hasher cannot
    store or verify a password at all. This is the fail-closed choice: the
    alternative - a "simple" fallback hasher - would silently become the
    production one somewhere.
    """

    algorithm_label = "unbound"

    def hash(self, password: str) -> str:
        raise SecretInPayloadRefusedError(
            "no password hasher is bound; bind a memory-hard hasher (Argon2id or scrypt) "
            "before enabling password fallback"
        )

    def verify(self, password: str, stored_hash: str) -> bool:
        raise SecretInPayloadRefusedError("no password hasher is bound")

    def needs_rehash(self, stored_hash: str) -> bool:
        raise SecretInPayloadRefusedError("no password hasher is bound")


class BreachedPasswordChecker(Protocol):
    """The breached-password checking boundary.

    A boundary, not an implementation: no corpus ships with this
    repository and no network call is made from it. `is_breached` is
    consulted at **enrollment and at change**, never at login, so a
    refusal never becomes an oracle about an existing account.
    """

    def is_breached(self, password: str) -> bool: ...


class UnboundBreachedPasswordChecker:
    """The default binding: **refuses**.

    This replaces an earlier permissive default that reported nothing as
    breached. That default was wrong in the direction a security default
    must never be wrong: a deployment that had not bound a checker would
    have discovered it after a credential-stuffing incident rather than
    at enrollment.

    So: **no checker means no password enrollment and no password
    change.** `is_breached` raises `BREACH_CHECK_UNAVAILABLE` rather than
    returning either boolean, because both booleans are lies - `False`
    claims a check that did not happen, and `True` would refuse every
    password for the wrong reason.

    Authentication against an **already stored** hash is a separate
    question, governed by `PasswordDegradedModeDecision` below.
    """

    def is_breached(self, password: str) -> bool:
        raise BreachCheckUnavailableError(
            "no breached-password checker is bound; password enrollment and password "
            "replacement refuse until one is"
        )


class DeterministicBreachedPasswordChecker:
    """A **test double**, and it says so in its name.

    It reports exactly the passwords it was constructed with as breached
    and nothing else. It exists so the enrollment and change paths can be
    tested on both branches without a corpus, and it is never the
    production default - `UnboundBreachedPasswordChecker` is.
    """

    def __init__(self, breached: frozenset[str] = frozenset()) -> None:
        self._breached = breached

    def is_breached(self, password: str) -> bool:
        return password in self._breached


@dataclass(frozen=True, slots=True)
class PasswordDegradedModeDecision:
    """The one governed exception, and its shape.

    When no breach checker is bound, an existing password holder can
    still be locked out of an account they legitimately own. Whether to
    let them authenticate against a hash that was stored **before** the
    checker went unbound is a governance decision, not a code default -
    so it is a value a deployment constructs, with an authority and a
    registered reason code, exactly like a configuration relaxation.

    It permits **authentication only**. There is no field that could
    permit enrollment or replacement, which is the whole point:
    `allows_authentication` is the only boolean here.
    """

    authority_reference: str
    reason_code: str
    decided_at: datetime
    allows_authentication: bool

    def __post_init__(self) -> None:
        if not self.authority_reference or not self.reason_code:
            raise BreachCheckUnavailableError(
                "a degraded-mode decision names an authority and carries a reason code"
            )
        if self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware")


def assert_breach_check_available(checker: BreachedPasswordChecker, password: str) -> bool:
    """Run the check, and let its refusal through.

    A thin wrapper, so every enrollment and change path calls the same
    thing and none of them is tempted to wrap the refusal in a
    `try: ... except: pass`.
    """
    return checker.is_breached(password)


class TotpVerifier(Protocol):
    """The TOTP port. RFC 6238 is a standard with audited
    implementations; this package binds one rather than writing one."""

    def provisioning_secret(self, random: SecureRandom) -> str: ...

    def verify(self, secret: str, presented_code: str, *, unix_time: int) -> bool: ...


class DeterministicTotpVerifier:
    """A **test double** for the TOTP port.

    It accepts exactly the code its own `expected_code` produces for the
    given secret and time step. It is not RFC 6238 and does not claim to
    be; it exists so the enrollment, confirmation, use and revocation
    workflows around a TOTP factor can be tested end to end without a
    real authenticator app, and so that no production path ever needs a
    test branch.
    """

    STEP_SECONDS = 30

    def provisioning_secret(self, random: SecureRandom) -> str:
        return random.token(20)

    def expected_code(self, secret: str, *, unix_time: int) -> str:
        step = unix_time // self.STEP_SECONDS
        digest = hashlib.sha256(f"{secret}:{step}".encode()).digest()
        return f"{int.from_bytes(digest[:4], 'big') % 1_000_000:06d}"

    def verify(self, secret: str, presented_code: str, *, unix_time: int) -> bool:
        return constant_time_equals(presented_code, self.expected_code(secret, unix_time=unix_time))


@dataclass(frozen=True, slots=True)
class HashedSecret:
    """A secret at rest.

    Only ever the digest and the algorithm label. There is no field that
    could hold the value, so no serialization of this dataclass can leak
    one - the same structural argument `Account` uses to prove it carries
    no identity data.
    """

    digest: str
    algorithm: str

    def __post_init__(self) -> None:
        if len(self.digest) != 64:
            raise ValueError("digest must be a 64-character hex SHA-256 digest")

    def matches(self, presented: str) -> bool:
        return constant_time_equals(self.digest, hash_token(presented).digest)


def hash_token(value: str) -> HashedSecret:
    """Token hashing at rest.

    Used for the single-use, high-entropy values this package mints:
    bootstrap authorization responses, voting handoff artifacts,
    verification codes, recovery codes and refresh tokens. A plain
    SHA-256 is correct here and a memory-hard KDF is not - these values
    carry 256 bits of CSPRNG entropy, so there is no guessing attack for
    a slow hash to slow down, and the property that matters is that a
    database read yields nothing presentable.

    Passwords are the opposite case and go through `PasswordHasher`.
    """
    if not value:
        raise SecretInPayloadRefusedError("refusing to hash an empty secret")
    return HashedSecret(
        digest=hashlib.sha256(value.encode("utf-8")).hexdigest(), algorithm="sha-256"
    )


def constant_time_equals(left: str, right: str) -> bool:
    """Compare two secret-derived strings without leaking their common
    prefix length through timing."""
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def derivation_salt(random: SecureRandom) -> bytes:
    """Mint a per-deployment salt for `derive_scoped_reference`.

    Held in the deployment's secret store and never written to a record,
    an event or a log: without it a scoped reference would be computable
    by anyone holding an `account_id`, which would make the mapping
    boundary decorative.
    """
    return random.bytes(32)

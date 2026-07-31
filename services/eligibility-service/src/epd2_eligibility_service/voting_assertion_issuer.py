"""The Eligibility Assertion Issuer's signing boundary (`OD-P15-01`).

A separately bounded module with its own storage boundary, its own signing
key custody and its own service credential. It consumes **only** a
minimized eligibility decision (`MinimizedDecisionInput` below) and is
structurally unable to read an account, person-record or membership store:
this module imports no other service's package, and the only input type it
accepts carries none of those fields.

**Reference cryptography only.** The integrity protection is an HMAC over
the canonical assertion payload with a key held behind
`AssertionSigningKeyCustody`. That is a *reference* implementation with
test keys and an explicit boundary for a future HSM/KMS binding
(`FutureKeyServiceCustody` refuses, so a deployment that has not bound a
real key service fails closed rather than signing with a default). **No
production cryptographic readiness is claimed.**
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from epd2_eligibility_service.voting_eligibility import (
    ASSERTION_PURPOSE,
    ASSERTION_RESULT_APPROVED,
    AssertionPickup,
    AssertionQueueEntry,
    AssertionStatus,
    EligibilityAssertion,
    EligibilityDecision,
)
from epd2_eligibility_service.voting_timing import (
    CohortSizeClass,
    IssuanceTimingProfile,
    classify_cohort_size,
    coarsen,
)
from epd2_eligibility_service.voting_trust_exceptions import (
    AssertionPickupAlreadyUsedError,
    AssertionPickupExpiredError,
    AssertionReleasePendingError,
    SystemDependencyUnavailableError,
)

#: Nonce entropy in bytes. A nonce is random and non-derived: deriving it
#: from participant data would recreate the assertion-to-credential map
#: without storing it (ADR-091).
NONCE_ENTROPY_BYTES = 32

#: The signing algorithm identifier carried in integrity metadata.
ASSERTION_INTEGRITY_ALGORITHM = "hmac-sha256-reference"


@dataclass(frozen=True, slots=True)
class MinimizedDecisionInput:
    """The **only** input shape the Assertion Issuer accepts.

    Five fields. There is no field here for a participant, a case, a
    criterion input, a reason history or an evidence reference, so the
    issuer cannot receive one even if a caller wanted to send it.
    """

    voting_context_reference: str
    eligibility_result: str
    eligibility_class: str
    organizational_scope: str
    required_assurance_satisfied: bool

    def __post_init__(self) -> None:
        if self.eligibility_result != ASSERTION_RESULT_APPROVED:
            raise ValueError("only an approved decision reaches the assertion issuer")
        if not self.voting_context_reference or not self.eligibility_class:
            raise ValueError("a minimized decision names its context and class")

    @classmethod
    def from_decision(cls, decision: EligibilityDecision) -> MinimizedDecisionInput:
        """Project a decision down to the five crossing-relevant facts."""
        return cls(
            voting_context_reference=decision.voting_context_reference,
            eligibility_result=ASSERTION_RESULT_APPROVED,
            eligibility_class=decision.eligibility_class,
            organizational_scope=decision.organizational_scope,
            required_assurance_satisfied=decision.required_assurance_satisfied,
        )


class SecureRandom(Protocol):
    def token_hex(self, nbytes: int) -> str: ...


class SystemSecureRandom:
    def token_hex(self, nbytes: int) -> str:
        return secrets.token_hex(nbytes)


class AssertionSigningKeyCustody(Protocol):
    """Custody of the assertion signing key.

    Deliberately a port: the key is not a module constant, and the
    eligibility decision store has no way to reach it.
    """

    def key_identifier(self) -> str: ...

    def sign(self, message: bytes) -> str: ...

    def verify(self, message: bytes, signature: str) -> bool: ...


class TestKeyCustody:
    """A test-key custody. **Never valid in a non-test trust store.**

    The key identifier is prefixed `test-` and
    `assert_production_custody` refuses it, so a deployment cannot sign
    real assertions with a test key by omission.
    """

    def __init__(self, secret: bytes = b"pack15-reference-test-key") -> None:
        self._secret = secret

    def key_identifier(self) -> str:
        return "test-assertion-signing-key-v1"

    def sign(self, message: bytes) -> str:
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def verify(self, message: bytes, signature: str) -> bool:
        return hmac.compare_digest(self.sign(message), signature)


class FutureKeyServiceCustody:
    """The HSM/KMS boundary, unbound in this round.

    Every method refuses. A deployment that has not bound a real key
    service therefore fails closed rather than falling back to a default
    key.
    """

    def key_identifier(self) -> str:
        raise SystemDependencyUnavailableError(
            "no key service is bound; PACK-15 integrates no HSM or KMS"
        )

    def sign(self, message: bytes) -> str:
        raise SystemDependencyUnavailableError(
            "no key service is bound; PACK-15 integrates no HSM or KMS"
        )

    def verify(self, message: bytes, signature: str) -> bool:
        raise SystemDependencyUnavailableError(
            "no key service is bound; PACK-15 integrates no HSM or KMS"
        )


def assert_production_custody(custody: AssertionSigningKeyCustody) -> None:
    """Refuse a test key outside a test trust store."""
    if custody.key_identifier().startswith("test-"):
        raise SystemDependencyUnavailableError(
            "a test signing key is structurally invalid outside a test trust store"
        )


def canonical_assertion_message(payload: Mapping[str, object]) -> bytes:
    """Deterministic bytes over the twelve-field crossing payload."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True, slots=True)
class AssertionIssuer:
    """Mints, queues, releases and serves the minimized assertion."""

    custody: AssertionSigningKeyCustody
    random: SecureRandom
    profile: IssuanceTimingProfile
    audience: str

    def mint(
        self,
        *,
        assertion_id: UUID,
        decision: MinimizedDecisionInput,
        now: datetime,
        expires_at: datetime,
        eligible_population: int,
    ) -> EligibilityAssertion:
        """Mint an assertion in status `minted`. Minting is not release."""
        granularity = self.profile.effective_timestamp_granularity(eligible_population)
        assertion = EligibilityAssertion(
            assertion_id=assertion_id,
            voting_context_reference=decision.voting_context_reference,
            eligibility_result=ASSERTION_RESULT_APPROVED,
            eligibility_class=decision.eligibility_class,
            organizational_scope=decision.organizational_scope,
            required_assurance_satisfied=decision.required_assurance_satisfied,
            issued_at_bucket=coarsen(now, granularity),
            expires_at=coarsen(expires_at, granularity) + timedelta(seconds=granularity),
            audience=self.audience,
            purpose=ASSERTION_PURPOSE,
            nonce=self.random.token_hex(NONCE_ENTROPY_BYTES),
            status=AssertionStatus.MINTED,
        )
        return self._with_integrity(assertion)

    def _with_integrity(self, assertion: EligibilityAssertion) -> EligibilityAssertion:
        signature = self.custody.sign(canonical_assertion_message(assertion.wire_payload()))
        return EligibilityAssertion(
            assertion_id=assertion.assertion_id,
            voting_context_reference=assertion.voting_context_reference,
            eligibility_result=assertion.eligibility_result,
            eligibility_class=assertion.eligibility_class,
            organizational_scope=assertion.organizational_scope,
            required_assurance_satisfied=assertion.required_assurance_satisfied,
            issued_at_bucket=assertion.issued_at_bucket,
            expires_at=assertion.expires_at,
            audience=assertion.audience,
            purpose=assertion.purpose,
            nonce=assertion.nonce,
            status=assertion.status,
            integrity_metadata={
                "algorithm": ASSERTION_INTEGRITY_ALGORITHM,
                "key_identifier": self.custody.key_identifier(),
                "signature": signature,
            },
        )

    def verify_integrity(self, assertion: EligibilityAssertion) -> bool:
        signature = assertion.integrity_metadata.get("signature", "")
        if not signature:
            return False
        probe = EligibilityAssertion(
            assertion_id=assertion.assertion_id,
            voting_context_reference=assertion.voting_context_reference,
            eligibility_result=assertion.eligibility_result,
            eligibility_class=assertion.eligibility_class,
            organizational_scope=assertion.organizational_scope,
            required_assurance_satisfied=assertion.required_assurance_satisfied,
            issued_at_bucket=assertion.issued_at_bucket,
            expires_at=assertion.expires_at,
            audience=assertion.audience,
            purpose=assertion.purpose,
            nonce=assertion.nonce,
            status=assertion.status,
        )
        return self.custody.verify(canonical_assertion_message(probe.wire_payload()), signature)

    # -- queued release ---------------------------------------------------

    def enqueue(
        self,
        assertion: EligibilityAssertion,
        *,
        batch_reference: str,
        now: datetime,
        jitter_fraction: float,
    ) -> AssertionQueueEntry:
        """Place a minted assertion in the queue with a randomized release.

        `jitter_fraction` is supplied by the caller (an injectable source)
        so that tests are deterministic. It is clamped to `[0, 1]`; the
        release offset is uniform over the governed delay window and is
        never a fixed offset.
        """
        if not 0.0 <= jitter_fraction <= 1.0:
            raise ValueError("jitter_fraction is a fraction of the release window")
        span = self.profile.release_delay_max_seconds - self.profile.release_delay_min_seconds
        offset = self.profile.release_delay_min_seconds + int(span * jitter_fraction)
        interval_end = now + timedelta(seconds=self.profile.batch_interval_seconds)
        return AssertionQueueEntry(
            assertion_id=assertion.assertion_id,
            voting_context_reference=assertion.voting_context_reference,
            batch_reference=batch_reference,
            enqueued_at=now,
            release_not_before=interval_end + timedelta(seconds=offset),
            cohort_wait_deadline=now + timedelta(seconds=self.profile.cohort_wait_max_seconds),
        )

    def release_decision(
        self,
        entry: AssertionQueueEntry,
        *,
        cohort_size: int,
        now: datetime,
        eligible_population: int,
    ) -> tuple[bool, CohortSizeClass, bool]:
        """Decide whether a queued assertion may be released now.

        Returns `(release_now, cohort_class, below_minimum)`.

        * A batch below the minimum cohort is **never released early** -
          a cohort of one waits.
        * At `cohort_wait_deadline` it is released **anyway**, with the
          cohort class recorded. Access is never denied for want of a
          cohort.
        """
        minimum = self.profile.effective_minimum_cohort(eligible_population)
        cohort_class = classify_cohort_size(cohort_size, minimum)
        if now < entry.release_not_before:
            return (False, cohort_class, cohort_size < minimum)
        if cohort_size >= minimum:
            return (True, cohort_class, False)
        if now >= entry.cohort_wait_deadline:
            return (True, cohort_class, True)
        return (False, cohort_class, True)

    def assert_released(self, entry: AssertionQueueEntry) -> None:
        if entry.released_at is None:
            raise AssertionReleasePendingError(
                "the assertion's governed release schedule has not yet elapsed"
            )

    # -- one-time pickup --------------------------------------------------

    def consume_pickup(self, pickup: AssertionPickup, *, now: datetime) -> AssertionPickup:
        """Consume a one-time pickup, or refuse."""
        if pickup.consumed:
            raise AssertionPickupAlreadyUsedError(
                "the one-time assertion pickup has already been consumed"
            )
        if now >= pickup.expires_at:
            raise AssertionPickupExpiredError("the one-time assertion pickup has expired")
        return AssertionPickup(
            pickup_id=pickup.pickup_id,
            assertion_id=pickup.assertion_id,
            voting_context_reference=pickup.voting_context_reference,
            handoff_artifact_digest=pickup.handoff_artifact_digest,
            audience_origin=pickup.audience_origin,
            created_at=pickup.created_at,
            expires_at=pickup.expires_at,
            consumed_at=now,
        )

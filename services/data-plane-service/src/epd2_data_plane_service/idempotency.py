"""Idempotency and deduplication (PACK-13 §11; ADR-077).

Idempotency is required across every operation class §11's
`P13-IDEM-001` enumerates. This module models the key, its scope, the
record, the decision and the two guards — and it refuses in four places
where a plausible-looking implementation would silently do the wrong
thing:

- **A key is scoped to a domain and an operation.** Never global, because
  a global key space lets one domain's retry collide with another's
  (`P13-IDEM-002`).
- **A key is never a global user identifier and never derived from one.**
  That would turn a key space into a correlation space and defeat
  FIR-INV-001 (`P13-IDEM-003`).
- **Reuse with a different payload is a conflict, not a replay**
  (`P13-IDEM-004`).
- **Expiry never silently admits a duplicate of a consequential
  action.** Where it could, the operation carries a second, permanent
  guard tied to the *business fact* rather than to the request
  (`P13-IDEM-006`). The idempotency record is an optimisation; the guard
  is the control.

The record stores a **request digest, not the request** (`P13-IDEM-008`),
and the stored first result is likewise a reference rather than a
payload: replaying returns what the first execution produced without
re-performing the effect (`P13-IDEM-005`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_data_plane_service.domain import (
    GLOBAL_IDENTITY_KEYS,
    OrganizationScopeReference,
    request_digest,
    require_timezone,
)
from epd2_data_plane_service.exceptions import (
    IdempotencyGlobalIdentifierProhibitedError,
    IdempotencyKeyReusedWithDifferentPayloadError,
    IdempotencyKeyScopeInvalidError,
    IdempotencyRecordExpiredError,
)


class OperationClass(StrEnum):
    """The operation classes §11 requires idempotency for.

    Each class states, through `CONSEQUENTIAL_OPERATION_CLASSES` below,
    whether an expired idempotency record could admit a duplicate with a
    real-world consequence. That is what decides whether a permanent
    business-fact guard is mandatory."""

    COMMAND = "command"
    EVENT_CONSUMER = "event_consumer"
    EXTERNAL_CALLBACK = "external_provider_callback"
    EXPORT_GENERATION = "export_generation"
    DOCUMENT_RENDITION = "document_rendition"
    FINANCE_IMPORT = "finance_import"
    DEADLINE_JOB = "deadline_job"
    NOTIFICATION_DISPATCH = "notification_dispatch"
    SCHEMA_PUBLICATION = "schema_publication"
    MIGRATION_EXECUTION = "migration_execution"


#: The operation classes whose duplicate has a consequence that outlives
#: the idempotency window — a financial posting, an export artifact, a
#: schema publication, a migration. For these, `IdempotencyPolicy`
#: requires a `BusinessFactGuard` and refuses without one (ADR-077).
CONSEQUENTIAL_OPERATION_CLASSES: frozenset[OperationClass] = frozenset(
    {
        OperationClass.EXPORT_GENERATION,
        OperationClass.DOCUMENT_RENDITION,
        OperationClass.FINANCE_IMPORT,
        OperationClass.SCHEMA_PUBLICATION,
        OperationClass.MIGRATION_EXECUTION,
    }
)


@dataclass(frozen=True, slots=True)
class IdempotencyScope:
    """The domain plus operation a key is valid within.

    Both fields are required and neither may be empty: a key with no
    operation is a key that a second operation in the same domain can
    collide with."""

    domain_name: str
    operation_name: str
    operation_class: OperationClass
    organization_scope: OrganizationScopeReference | None = None

    def __post_init__(self) -> None:
        if not self.domain_name or not self.operation_name:
            raise IdempotencyKeyScopeInvalidError(
                "an idempotency scope requires both a domain and an operation; a key that "
                "is global across the system lets one domain's retry collide with another's"
            )

    @property
    def qualified_name(self) -> str:
        return f"{self.domain_name}:{self.operation_name}"

    @property
    def consequential(self) -> bool:
        return self.operation_class in CONSEQUENTIAL_OPERATION_CLASSES


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """A scoped idempotency key.

    `key_value` is the caller's own opaque token. It is validated on
    construction against `GLOBAL_IDENTITY_KEYS`-shaped material, because
    the most convenient key a caller has to hand is often exactly the
    identifier that must never become one."""

    scope: IdempotencyScope
    key_value: str

    def __post_init__(self) -> None:
        if not self.key_value:
            raise IdempotencyKeyScopeInvalidError("an idempotency key must not be empty")
        reject_identity_derived_key(self.key_value, scope=self.scope)

    @property
    def qualified_key(self) -> str:
        """The full key space entry: scope, then value. Two domains using
        the same `key_value` produce two different qualified keys."""
        return f"{self.scope.qualified_name}:{self.key_value}"

    @property
    def digest(self) -> str:
        return request_digest(self.qualified_key)


def reject_identity_derived_key(key_value: str, *, scope: IdempotencyScope) -> None:
    """Refuse a key that is, or is trivially derived from, a global
    person identifier (`P13-IDEM-003`).

    The check is structural and deliberately conservative: it matches a
    key value that *is* one of the forbidden field names, or that is
    prefixed by one, which is the shape a caller reaches for when
    building a key out of the identifier they already have. It cannot
    detect an opaque hash of a person identifier — that residual is
    recorded in the known-limitations document rather than papered
    over."""
    lowered = key_value.lower()
    for forbidden in GLOBAL_IDENTITY_KEYS:
        if lowered == forbidden or lowered.startswith(f"{forbidden}:"):
            raise IdempotencyGlobalIdentifierProhibitedError(
                f"idempotency key for {scope.qualified_name} derives from {forbidden!r}; "
                f"a key space built on a person identifier is a correlation space"
            )


class IdempotencyOutcome(StrEnum):
    FIRST_EXECUTION = "first_execution"
    REPLAY = "replay"
    CONFLICT = "conflict"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """One stored idempotency record.

    Holds a **request digest**, never the request (`P13-IDEM-008`), and a
    **result reference**, never the result payload: replay must be able
    to answer "what did the first execution produce" without the record
    becoming a second copy of the data."""

    key: IdempotencyKey
    request_digest: str
    result_reference: UUID
    recorded_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, field="IdempotencyRecord.recorded_at")
        require_timezone(self.expires_at, field="IdempotencyRecord.expires_at")
        if self.expires_at <= self.recorded_at:
            raise ValueError("IdempotencyRecord.expires_at must be after recorded_at")

    def is_expired_at(self, moment: datetime) -> bool:
        require_timezone(moment, field="moment")
        return moment >= self.expires_at


@dataclass(frozen=True, slots=True)
class IdempotencyDecision:
    """What the caller should do with this request."""

    outcome: IdempotencyOutcome
    record: IdempotencyRecord | None = None
    reason_code: str | None = None

    @property
    def should_execute(self) -> bool:
        return self.outcome is IdempotencyOutcome.FIRST_EXECUTION


@dataclass(frozen=True, slots=True)
class DeduplicationRecord:
    """Consumer-side deduplication, keyed on the **event ID plus the
    consumer's own scope** (`P13-IDEM-009`).

    Two consumers of the same event are two independent effects, each
    deduplicated once. A deduplication table keyed on event ID alone
    would make the second consumer's first delivery look like a
    duplicate of the first consumer's."""

    consumer_name: str
    consumer_domain: str
    event_id: UUID
    first_seen_at: datetime
    observation_count: int = 1

    def __post_init__(self) -> None:
        require_timezone(self.first_seen_at, field="DeduplicationRecord.first_seen_at")
        if not self.consumer_name or not self.consumer_domain:
            raise IdempotencyKeyScopeInvalidError(
                "a deduplication record is keyed on the event ID *and* the consumer's own "
                "scope; a consumer with no scope shares a key space with every other"
            )
        if self.observation_count < 1:
            raise ValueError("observation_count must be at least 1")

    @property
    def dedup_key(self) -> str:
        return f"{self.consumer_domain}:{self.consumer_name}:{self.event_id}"

    def observed_again(self) -> DeduplicationRecord:
        """Count the duplicate. Duplicates are normal and expected under
        at-least-once delivery, and counting them is how an operator sees
        a redelivery storm rather than guessing at one."""
        return DeduplicationRecord(
            consumer_name=self.consumer_name,
            consumer_domain=self.consumer_domain,
            event_id=self.event_id,
            first_seen_at=self.first_seen_at,
            observation_count=self.observation_count + 1,
        )


@dataclass(frozen=True, slots=True)
class BusinessFactGuard:
    """The permanent guard that survives idempotency-record expiry.

    Tied to the **business fact** — a unique posting, a single artifact
    per approval, a digest uniqueness in the registry, an applied-state
    check for a migration — rather than to the request. Where a
    consequential operation carries no guard, `IdempotencyPolicy` refuses
    to evaluate at all rather than accepting an unguarded duplicate
    (`P13-IDEM-006`)."""

    guard_name: str
    fact_key: str

    def __post_init__(self) -> None:
        if not self.guard_name or not self.fact_key:
            raise ValueError("a BusinessFactGuard requires both a name and a fact key")


def compute_request_digest(payload: Mapping[str, object]) -> str:
    """Canonicalize and digest a request payload.

    Uses the repository's existing canonical JSON so that two
    independently-constructed representations of the same logical request
    produce the same digest, and a reordered dictionary is not a
    different request."""
    return request_digest(canonical_dumps(payload))


class IdempotencyPolicy:
    """The idempotency decision function and its two guards."""

    @staticmethod
    def evaluate(
        *,
        key: IdempotencyKey,
        incoming_digest: str,
        existing: IdempotencyRecord | None,
        now: datetime,
        guard: BusinessFactGuard | None = None,
        guarded_fact_already_exists: bool = False,
    ) -> IdempotencyDecision:
        """Decide what to do with an incoming request.

        Four outcomes, and the order they are checked in is load-bearing:

        1. **Conflict first.** Same key, different payload is a conflict
           whether or not the record has expired — treating it as a
           replay would return the wrong first result (`P13-IDEM-004`).
        2. **Expiry second**, and only for a *matching* payload. An
           expired record for a consequential operation consults the
           permanent guard; an expired record for a non-consequential one
           simply admits a fresh execution.
        3. **Replay third**, returning the recorded result reference
           without re-performing the effect (`P13-IDEM-005`).
        4. **First execution** otherwise.
        """
        require_timezone(now, field="now")
        if key.scope.consequential and guard is None:
            raise IdempotencyRecordExpiredError(
                f"{key.scope.qualified_name} is a consequential operation class and "
                f"requires a permanent business-fact guard in addition to its idempotency "
                f"record; the record is an optimisation, the guard is the control"
            )
        if existing is None:
            if guarded_fact_already_exists:
                return IdempotencyDecision(
                    outcome=IdempotencyOutcome.CONFLICT,
                    reason_code="IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD",
                )
            return IdempotencyDecision(outcome=IdempotencyOutcome.FIRST_EXECUTION)
        if existing.request_digest != incoming_digest:
            return IdempotencyDecision(
                outcome=IdempotencyOutcome.CONFLICT,
                record=existing,
                reason_code="IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD",
            )
        if existing.is_expired_at(now):
            if key.scope.consequential and guarded_fact_already_exists:
                return IdempotencyDecision(
                    outcome=IdempotencyOutcome.EXPIRED,
                    record=existing,
                    reason_code="IDEMPOTENCY_RECORD_EXPIRED",
                )
            return IdempotencyDecision(outcome=IdempotencyOutcome.FIRST_EXECUTION, record=existing)
        return IdempotencyDecision(outcome=IdempotencyOutcome.REPLAY, record=existing)

    @staticmethod
    def require_no_conflict(decision: IdempotencyDecision, *, context: str) -> None:
        """Turn a conflict decision into the registered refusal."""
        if decision.outcome is IdempotencyOutcome.CONFLICT:
            raise IdempotencyKeyReusedWithDifferentPayloadError(
                f"{context}: the same idempotency key was presented with different content; "
                f"this is a conflict, never a replay"
            )
        if decision.outcome is IdempotencyOutcome.EXPIRED:
            raise IdempotencyRecordExpiredError(
                f"{context}: the idempotency window closed and the permanent business-fact "
                f"guard reports the consequential effect already exists; a silent duplicate "
                f"is refused"
            )

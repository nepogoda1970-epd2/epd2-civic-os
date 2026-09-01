"""Persistence contracts: migrations, constraints, retention and replay
records.

**No production database is deployed by this round**, and none is
simulated. What exists here is the persistence *contract* PACK-13's
ADR-075 discipline expects of any domain that will one day be deployed on
the production data plane: an ordered, reversible-or-explicitly-not
migration list, the unique constraints and expiry indexes the domain
depends on for correctness rather than for speed, the retention binding
per record class, and the replay-prevention records single-use artifacts
need.

Two of those are load-bearing rather than descriptive:

- **The unique constraints are correctness.** Contact uniqueness within a
  scope, one active credential per reference, one open closure request
  per account - each is a rule this package enforces in memory and would
  lose to a concurrent writer without the constraint.
- **The expiry indexes are a privacy control.** The retention matrix
  requires handoff issuance records to be deleted early *and as a set*;
  without an index on expiry that deletion becomes a table scan somebody
  eventually stops running.

`OD-P14-07` is open, and the durations below are the **provisional safe
schedules** from `PACK-14-PRIVACY-RETENTION-MATRIX.md`. The behaviour
around them is not provisional: deletion under a legal hold refuses, an
unknown hold state fails closed, evidence survives closure, and a
destructive disposition against an unconfirmed schedule is refused with
`RETENTION_SCHEDULE_UNCONFIRMED`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from epd2_identity_service.exceptions import (
    IdempotencyKeyReusedError,
    NonceAlreadyUsedError,
    RetentionScheduleUnconfirmedError,
    UnknownRetentionClassError,
)
from epd2_identity_service.identifiers import require_timezone
from epd2_identity_service.secret_storage import HashedSecret


class MigrationKind(StrEnum):
    """PACK-13's expand/contract vocabulary, reused rather than
    reinvented."""

    EXPAND = "expand"
    BACKFILL = "backfill"
    CONTRACT = "contract"


@dataclass(frozen=True, slots=True)
class MigrationDefinition:
    """One ordered, named migration step.

    `reversible` is a claim the definition makes about itself and the
    migration report repeats: a `CONTRACT` step that drops a column is
    honestly irreversible, and saying so is more useful than a rollback
    plan that would not work.
    """

    identifier: str
    sequence: int
    kind: MigrationKind
    summary: str
    reversible: bool

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("migration sequence numbers start at 1")
        if not self.summary:
            raise ValueError("a migration definition summarises what it does")


#: The PACK-14 migration list. Expand-only: this round adds tables and
#: indexes and drops nothing, so every step is reversible and the
#: contract phase is empty. That is the honest state of a first
#: implementation round, not a deferral.
PACK14_MIGRATIONS: tuple[MigrationDefinition, ...] = (
    MigrationDefinition(
        identifier="p14-001-account-registry",
        sequence=1,
        kind=MigrationKind.EXPAND,
        summary="Account registry records, locks, restrictions and closure requests.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-002-account-contacts",
        sequence=2,
        kind=MigrationKind.EXPAND,
        summary="Account contacts, holding normalized digests and masked values only.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-003-credential-registry",
        sequence=3,
        kind=MigrationKind.EXPAND,
        summary="Credentials, passkey records, MFA factors and recovery code sets.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-004-sessions",
        sequence=4,
        kind=MigrationKind.EXPAND,
        summary="Session records, refresh-token families and device references.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-005-step-up",
        sequence=5,
        kind=MigrationKind.EXPAND,
        summary="Step-up challenges and results, bound to action and object version.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-006-recovery",
        sequence=6,
        kind=MigrationKind.EXPAND,
        summary="Recovery cases, assessments, evidence references, decisions and disputes.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-007-proofing",
        sequence=7,
        kind=MigrationKind.EXPAND,
        summary="Identity proofing cases and their PACK-11 evidence references.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-008-bootstrap-and-handoff",
        sequence=8,
        kind=MigrationKind.EXPAND,
        summary="Bootstrap requests and responses, redemptions, voting handoff issuances.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-009-identity-mappings",
        sequence=9,
        kind=MigrationKind.EXPAND,
        summary="Governed identity mappings with purpose, scope, policy and expiry.",
        reversible=True,
    ),
    MigrationDefinition(
        identifier="p14-010-replay-prevention",
        sequence=10,
        kind=MigrationKind.EXPAND,
        summary="Nonce and idempotency records with expiry indexes.",
        reversible=True,
    ),
)


@dataclass(frozen=True, slots=True)
class UniqueConstraint:
    """A uniqueness rule this domain depends on for correctness."""

    name: str
    table: str
    columns: tuple[str, ...]
    rationale: str


PACK14_UNIQUE_CONSTRAINTS: tuple[UniqueConstraint, ...] = (
    UniqueConstraint(
        name="uq_contact_scope_digest",
        table="account_contact",
        columns=("channel_class", "scope_level", "scope_unit_id", "normalized_digest"),
        rationale=(
            "Contact uniqueness is scoped, never global: a global constraint would make "
            "the address a cross-scope join key."
        ),
    ),
    UniqueConstraint(
        name="uq_passkey_credential_reference",
        table="passkey_credential",
        columns=("credential_reference",),
        rationale="One authenticator credential reference maps to one record, so revocation "
        "is unambiguous.",
    ),
    UniqueConstraint(
        name="uq_open_closure_request",
        table="account_closure_request",
        columns=("account_id",),
        rationale="At most one open closure request per account; enforced partially on the "
        "open states.",
    ),
    UniqueConstraint(
        name="uq_bootstrap_response_digest",
        table="bootstrap_response",
        columns=("value_digest",),
        rationale="Single-use is meaningless if two rows can hold the same value.",
    ),
    UniqueConstraint(
        name="uq_voting_handoff_digest",
        table="voting_handoff_issuance",
        columns=("value_digest",),
        rationale="Same reason, and the property WS-03's isolation rests on.",
    ),
    UniqueConstraint(
        name="uq_nonce_record",
        table="replay_nonce",
        columns=("nonce_digest",),
        rationale="Nonces are single-use across the whole store, not per ceremony.",
    ),
    UniqueConstraint(
        name="uq_identity_mapping_purpose_scope_source",
        table="identity_mapping",
        columns=("purpose", "scope_level", "scope_unit_id", "source_reference"),
        rationale="One purpose-scoped correlation per source; no second mapping to shadow it.",
    ),
)


@dataclass(frozen=True, slots=True)
class ExpiryIndex:
    """An index on an expiry column, present for privacy rather than for
    speed: the disposal job that keeps a retention promise has to be
    cheap enough that it keeps running."""

    name: str
    table: str
    column: str
    rationale: str


PACK14_EXPIRY_INDEXES: tuple[ExpiryIndex, ...] = (
    ExpiryIndex(
        name="ix_session_absolute_deadline",
        table="session_record",
        column="absolute_deadline",
        rationale="Expired sessions are disposed of, and no session is exempt.",
    ),
    ExpiryIndex(
        name="ix_bootstrap_response_expires_at",
        table="bootstrap_response",
        column="expires_at",
        rationale="Short-lived by design; a stale row is a redeemable artifact.",
    ),
    ExpiryIndex(
        name="ix_voting_handoff_expires_at",
        table="voting_handoff_issuance",
        column="expires_at",
        rationale=(
            "Deleted early AND as a set: deleting one side of a pair can make the "
            "surviving side identifying."
        ),
    ),
    ExpiryIndex(
        name="ix_replay_nonce_expires_at",
        table="replay_nonce",
        column="expires_at",
        rationale="A replay-prevention store that grows without bound stops being queried.",
    ),
    ExpiryIndex(
        name="ix_identity_mapping_expires_at",
        table="identity_mapping",
        column="expires_at",
        rationale="A mapping that never expires becomes the global identifier by longevity.",
    ),
)


@dataclass(frozen=True, slots=True)
class RetentionBinding:
    """One record class, its provisional duration and its hold
    behaviour."""

    record_class: str
    provisional_duration: timedelta | None
    legal_hold_applies: bool
    #: `False` for every class until `OD-P14-07`'s legal confirmation.
    #: Read by `assert_disposition_permitted`, which is what makes the
    #: open decision a refusal rather than a footnote.
    duration_confirmed: bool
    deletion_effect: str


#: The provisional schedules from `PACK-14-PRIVACY-RETENTION-MATRIX.md`
#: §1. `provisional_duration=None` means "life of the record plus a
#: statutory period" - a duration that is not a fixed interval and that
#: PACK-09 owns.
PACK14_RETENTION: dict[str, RetentionBinding] = {
    "account_record": RetentionBinding(
        record_class="account_record",
        provisional_duration=None,
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="anonymized, not erased, where obligations remain",
    ),
    "contact_history": RetentionBinding(
        record_class="contact_history",
        provisional_duration=timedelta(days=730),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="tokenized reference retained; raw value removed",
    ),
    "credential_metadata": RetentionBinding(
        record_class="credential_metadata",
        provisional_duration=timedelta(days=365),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="metadata retained; no key material ever existed here",
    ),
    "authentication_attempts": RetentionBinding(
        record_class="authentication_attempts",
        provisional_duration=timedelta(days=90),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="aggregated then removed",
    ),
    "session_history": RetentionBinding(
        record_class="session_history",
        provisional_duration=timedelta(days=365),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="removed",
    ),
    "suspicious_activity": RetentionBinding(
        record_class="suspicious_activity",
        provisional_duration=timedelta(days=730),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="retained where a case is open",
    ),
    "recovery_evidence": RetentionBinding(
        record_class="recovery_evidence",
        provisional_duration=timedelta(days=2192),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="never deleted while a dispute or hold is open",
    ),
    "proofing_evidence": RetentionBinding(
        record_class="proofing_evidence",
        provisional_duration=None,
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="governed disposition only, with PACK-09 authorization",
    ),
    "privileged_action": RetentionBinding(
        record_class="privileged_action",
        provisional_duration=timedelta(days=3653),
        legal_hold_applies=True,
        duration_confirmed=False,
        deletion_effect="never deleted while an oversight obligation exists",
    ),
    "voting_handoff_issuance": RetentionBinding(
        record_class="voting_handoff_issuance",
        provisional_duration=timedelta(hours=1),
        legal_hold_applies=False,
        duration_confirmed=False,
        deletion_effect="deleted early AND as a set, creating no correlation",
    ),
}


def retention_binding(record_class: str) -> RetentionBinding:
    try:
        return PACK14_RETENTION[record_class]
    except KeyError as exc:
        raise UnknownRetentionClassError(f"unknown retention class: {record_class!r}") from exc


def assert_disposition_permitted(
    record_class: str,
    *,
    legal_hold_state: bool | None,
    dispute_open: bool,
) -> None:
    """The four deletion constraints, in one place.

    `legal_hold_state=None` means the hold state could not be
    determined, and that **fails closed** - an unknown hold is treated as
    a hold, because the alternative is deleting evidence during an
    investigation nobody could see.

    The schedule check is last and refuses every destructive disposition
    while `OD-P14-07` is open. The provisional schedule governs how long
    records are kept; it does not authorise destroying them.
    """
    binding = retention_binding(record_class)
    if binding.legal_hold_applies and legal_hold_state is not False:
        from epd2_identity_service.exceptions import RecordUnderLegalHoldError

        raise RecordUnderLegalHoldError(
            "the record is under a legal hold, or its hold state is unknown"
        )
    if dispute_open:
        from epd2_identity_service.exceptions import RecordUnderLegalHoldError

        raise RecordUnderLegalHoldError("an open dispute preserves this record")
    if not binding.duration_confirmed:
        raise RetentionScheduleUnconfirmedError(
            f"the retention duration for {record_class!r} awaits OD-P14-07's legal "
            "confirmation; the provisional schedule governs storage, not destruction"
        )


@dataclass(frozen=True, slots=True)
class ReplayNonceRecord:
    """A consumed nonce, with an expiry so the store stays bounded."""

    nonce_digest: HashedSecret
    purpose: str
    consumed_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.consumed_at, "consumed_at")
        require_timezone(self.expires_at, "expires_at")


def assert_nonce_unused(nonce: str, *, seen: frozenset[str]) -> None:
    from epd2_identity_service.secret_storage import hash_token

    if hash_token(nonce).digest in seen:
        raise NonceAlreadyUsedError("this nonce has already been consumed")


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """PACK-13's ADR-077 idempotency discipline, applied here.

    The request digest is stored alongside the key so a key reused with a
    *different* body is refused rather than answered with the first
    result - answering would be replying to a question nobody asked.
    """

    idempotency_key: str
    request_digest: str
    operation: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.recorded_at, "recorded_at")


def assert_idempotent(
    record: IdempotencyRecord | None, *, idempotency_key: str, request_digest: str, operation: str
) -> bool:
    """Return `True` when this is a genuine replay of the same request.

    Three outcomes, not two: new request (`False`), identical replay
    (`True`), and same key with a different body (refusal).
    """
    if record is None:
        return False
    if record.operation != operation or record.request_digest != request_digest:
        raise IdempotencyKeyReusedError(
            f"idempotency key {idempotency_key!r} was used before with a different request"
        )
    return True

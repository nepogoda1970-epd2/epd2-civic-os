"""Contact handles - mutable attributes, never identifiers.

Email and phone may change, may be reused only under a governed policy,
and require verification. The rules below exist because their opposites
are the ordinary way an account is taken over:

- **A change notifies both the old and the new channel.** Notifying only
  the new one is how a takeover goes unnoticed.
- **A recently changed contact may not be the sole basis for recovery.**
  Change the address, then "recover" the account, is a two-step takeover
  the protective window breaks.
- **No account is ever auto-merged by a matching contact value.** A
  shared family address is not evidence of one person (ADR-080).
- **The raw value never reaches an ordinary audit log or event.** What
  travels is the channel class and a tokenized reference; the masked form
  exists for showing a person which of their addresses is meant, and
  nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.exceptions import (
    ContactAlreadyInUseError,
    ContactAutoMergeRefusedError,
    ContactNotNormalizableError,
    ContactNotVerifiedError,
    ContactRecentlyChangedError,
    ContactReuseBlockedError,
    ForbiddenContactTransitionError,
    LastVerifiedChannelError,
    UnknownContactChannelClassError,
    UnknownContactStatusError,
)
from epd2_identity_service.identifiers import AccountId, OrganizationScope, require_timezone
from epd2_identity_service.secret_storage import HashedSecret, hash_token


class ContactChannelClass(StrEnum):
    """Two channel classes, and no more.

    There is deliberately no `sms` class distinct from `phone`: SMS is a
    delivery mechanism over the phone channel, and giving it its own
    class would invite treating it as an authentication factor, which it
    is not (OD-P14-09).
    """

    EMAIL = "email"
    PHONE = "phone"


def parse_channel_class(value: str) -> ContactChannelClass:
    try:
        return ContactChannelClass(value)
    except ValueError as exc:
        raise UnknownContactChannelClassError(f"unknown contact channel class: {value!r}") from exc


class ContactStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFICATION_PENDING = "verification_pending"
    VERIFIED = "verified"
    REPLACED = "replaced"
    REMOVED = "removed"


def parse_contact_status(value: str) -> ContactStatus:
    try:
        return ContactStatus(value)
    except ValueError as exc:
        raise UnknownContactStatusError(f"unknown contact status: {value!r}") from exc


_ALLOWED_CONTACT_TRANSITIONS: frozenset[tuple[ContactStatus, ContactStatus]] = frozenset(
    {
        (ContactStatus.UNVERIFIED, ContactStatus.VERIFICATION_PENDING),
        (ContactStatus.UNVERIFIED, ContactStatus.REMOVED),
        (ContactStatus.VERIFICATION_PENDING, ContactStatus.VERIFIED),
        (ContactStatus.VERIFICATION_PENDING, ContactStatus.UNVERIFIED),
        (ContactStatus.VERIFICATION_PENDING, ContactStatus.REMOVED),
        (ContactStatus.VERIFIED, ContactStatus.REPLACED),
        (ContactStatus.VERIFIED, ContactStatus.REMOVED),
    }
)


def normalize_email(value: str) -> str:
    """Normalize an email address for uniqueness comparison.

    Deliberately conservative: trim, lower-case, and require exactly one
    `@` with a non-empty local part and a dotted domain. It does **not**
    strip dots or `+tags` from the local part, because those are
    provider-specific conventions and treating `a.b@` and `ab@` as one
    address would silently merge two people at two providers that do not
    agree.
    """
    candidate = value.strip().lower()
    if candidate.count("@") != 1:
        raise ContactNotNormalizableError("an email address contains exactly one '@'")
    local, _, domain = candidate.partition("@")
    if (
        not local
        or not domain
        or "." not in domain
        or domain.startswith(".")
        or domain.endswith(".")
    ):
        raise ContactNotNormalizableError(f"not a normalizable email address: {value!r}")
    if any(character.isspace() for character in candidate):
        raise ContactNotNormalizableError("an email address contains no whitespace")
    return candidate


def normalize_phone(value: str) -> str:
    """Normalize a phone number to E.164-shaped digits.

    Requires a leading `+` and 8 to 15 digits. National formats are
    refused rather than guessed at: guessing a country code is guessing
    which person a number belongs to.
    """
    candidate = "".join(character for character in value.strip() if not character.isspace())
    candidate = candidate.replace("-", "").replace("(", "").replace(")", "").replace("/", "")
    if not candidate.startswith("+"):
        raise ContactNotNormalizableError("a phone number must be given in +E.164 form")
    digits = candidate[1:]
    if not digits.isdigit() or not 8 <= len(digits) <= 15:
        raise ContactNotNormalizableError(f"not a normalizable phone number: {value!r}")
    return f"+{digits}"


def normalize_contact(channel_class: ContactChannelClass, value: str) -> str:
    if channel_class is ContactChannelClass.EMAIL:
        return normalize_email(value)
    return normalize_phone(value)


def mask_contact(channel_class: ContactChannelClass, normalized_value: str) -> str:
    """The masked form, for showing a person which channel is meant.

    Enough to recognise, not enough to disclose: `a***@e***.example` and
    `+49*******89`. Used in a UI and in a notification, never in an audit
    payload - a masked value is still a value.
    """
    if channel_class is ContactChannelClass.EMAIL:
        local, _, domain = normalized_value.partition("@")
        domain_head, _, domain_tail = domain.partition(".")
        return f"{local[:1]}***@{domain_head[:1]}***.{domain_tail}"
    return f"{normalized_value[:3]}{'*' * max(0, len(normalized_value) - 5)}{normalized_value[-2:]}"


@dataclass(frozen=True, slots=True)
class ContactUniquenessScope:
    """Where a contact value must be unique.

    Uniqueness is scoped, not global: the same address may legitimately
    appear in two organizational scopes, and a global uniqueness rule
    would turn the address into the cross-scope join key `FIR-INV-013`
    forbids.
    """

    channel_class: ContactChannelClass
    scope: OrganizationScope

    def matches(self, other: ContactUniquenessScope) -> bool:
        return self.channel_class is other.channel_class and self.scope.matches(other.scope)


@dataclass(frozen=True, slots=True)
class AccountContact:
    """A contact handle attached to an account.

    The normalized value is stored **hashed** (`normalized_digest`) for
    uniqueness comparison, alongside the masked form for display. The raw
    value lives only in the delivery boundary that has to send to it, and
    this dataclass has no field that could hold it.
    """

    contact_id: UUID
    account_id: AccountId
    channel_class: ContactChannelClass
    normalized_digest: HashedSecret
    masked_value: str
    status: ContactStatus
    uniqueness_scope: ContactUniquenessScope
    added_at: datetime
    verified_at: datetime | None
    changed_at: datetime | None
    retention_class: str
    version: int

    def __post_init__(self) -> None:
        require_timezone(self.added_at, "added_at")
        if self.verified_at is not None:
            require_timezone(self.verified_at, "verified_at")
        if self.changed_at is not None:
            require_timezone(self.changed_at, "changed_at")
        if not self.retention_class:
            raise ValueError("every contact record carries a retention class")

    def is_verified(self) -> bool:
        return self.status is ContactStatus.VERIFIED

    def transitioned(self, target: ContactStatus, *, at: datetime) -> AccountContact:
        if (self.status, target) not in _ALLOWED_CONTACT_TRANSITIONS:
            raise ForbiddenContactTransitionError(
                f"contact transition {self.status.value!r} -> {target.value!r} is not allowed"
            )
        verified_at = self.verified_at
        if target is ContactStatus.VERIFIED:
            verified_at = require_timezone(at, "at")
        return replace(self, status=target, verified_at=verified_at, version=self.version + 1)

    def matches_value(self, channel_class: ContactChannelClass, raw_value: str) -> bool:
        if channel_class is not self.channel_class:
            return False
        return self.normalized_digest.matches(normalize_contact(channel_class, raw_value))


def build_contact(
    *,
    contact_id: UUID,
    account_id: AccountId,
    channel_class: ContactChannelClass,
    raw_value: str,
    scope: OrganizationScope,
    added_at: datetime,
    retention_class: str = "contact_history",
) -> AccountContact:
    normalized = normalize_contact(channel_class, raw_value)
    return AccountContact(
        contact_id=contact_id,
        account_id=account_id,
        channel_class=channel_class,
        normalized_digest=hash_token(normalized),
        masked_value=mask_contact(channel_class, normalized),
        status=ContactStatus.UNVERIFIED,
        uniqueness_scope=ContactUniquenessScope(channel_class=channel_class, scope=scope),
        added_at=require_timezone(added_at, "added_at"),
        verified_at=None,
        changed_at=None,
        retention_class=retention_class,
        version=1,
    )


def assert_unique_within_scope(
    candidate: AccountContact, existing: tuple[AccountContact, ...]
) -> None:
    """Uniqueness, and the refusal that must never become a merge.

    If the value already exists on **another** account, the answer is
    `CONTACT_ALREADY_IN_USE` and - separately and emphatically - never a
    merge of the two accounts (`ContactAutoMergeRefusedError` exists so
    that a caller who tries to build one gets a refusal with its own
    code, rather than this function quietly doing it).
    """
    for other in existing:
        if other.status in (ContactStatus.REMOVED, ContactStatus.REPLACED):
            continue
        if not other.uniqueness_scope.matches(candidate.uniqueness_scope):
            continue
        if other.normalized_digest.digest != candidate.normalized_digest.digest:
            continue
        if other.account_id == candidate.account_id:
            return
        raise ContactAlreadyInUseError(
            "the channel is already attached to an account within this uniqueness scope"
        )


def refuse_auto_merge(left_account: AccountId, right_account: AccountId) -> None:
    """ADR-080, as a call site.

    Any code path that finds two accounts sharing a contact value calls
    this instead of merging. It always raises when the accounts differ,
    which is the only behaviour that makes "no automatic merge" a
    property of the system rather than a paragraph about it.
    """
    if left_account != right_account:
        raise ContactAutoMergeRefusedError(
            "two accounts sharing a contact value are never merged automatically; "
            "duplicate handling is a reviewed decision"
        )


def assert_reuse_permitted(
    *,
    candidate: AccountContact,
    released_handles: tuple[tuple[HashedSecret, datetime], ...],
    now: datetime,
    reuse_embargo: timedelta,
) -> None:
    """A handle released by a closed account may not be reused
    immediately.

    Otherwise a later holder inherits the previous holder's recovery
    paths and notification history - the "reuse or correlation
    vulnerability" the retention matrix forbids deletion from creating.
    """
    for digest, released_at in released_handles:
        if digest.digest != candidate.normalized_digest.digest:
            continue
        if (
            require_timezone(now, "now")
            < require_timezone(released_at, "released_at") + reuse_embargo
        ):
            raise ContactReuseBlockedError(
                "this channel was released by a closed account too recently to be reused"
            )


def assert_not_recently_changed(
    contact: AccountContact, *, now: datetime, protective_window: timedelta
) -> None:
    """The protective window after a contact change.

    Raised as `CONTACT_RECENTLY_CHANGED` for ordinary operations; the
    recovery workflow raises its own `RECOVERY_CONTACT_RECENTLY_CHANGED`
    instead, because the remedy differs - wait, versus use a different
    channel.
    """
    if contact.changed_at is None:
        return
    if require_timezone(now, "now") < contact.changed_at + protective_window:
        raise ContactRecentlyChangedError("this channel was changed inside the protective window")


def assert_verified(contact: AccountContact) -> None:
    if not contact.is_verified():
        raise ContactNotVerifiedError("the channel has not completed verification")


def assert_not_last_verified_channel(
    contact: AccountContact, all_contacts: tuple[AccountContact, ...]
) -> None:
    """Out-of-band notification needs somewhere to go.

    Removing the last verified channel would leave the account with no
    way to be told that it is being taken over, which is the one message
    that must always arrive.
    """
    remaining = [
        other
        for other in all_contacts
        if other.contact_id != contact.contact_id and other.is_verified()
    ]
    if contact.is_verified() and not remaining:
        raise LastVerifiedChannelError(
            "this is the only verified channel; out-of-band notification would have nowhere to go"
        )

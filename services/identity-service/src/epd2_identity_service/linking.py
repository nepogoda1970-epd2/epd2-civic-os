"""Account linking, and the four merges that never happen.

Linking is **user-initiated only**, step-up protected, and requires proof
of control of **both** sides. Four things are refused outright:

1. merge by email;
2. merge by name or date of birth;
3. automatic provider-based merge;
4. silent reassignment of a link to a different account.

Each has its own call site here rather than a shared "merge refused",
because a future reader needs to see that the specific convenience they
are reaching for was considered and rejected.

Duplicate detection is a **review**, not an answer. Crucially, a
duplicate response never discloses to the caller that another account
exists: `DUPLICATE_ACCOUNT_SUSPECTED` is routed to a reviewer, and what
the caller sees is the same uniform response any other outcome produces.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_identity_service.contacts import refuse_auto_merge
from epd2_identity_service.exceptions import (
    AccountLinkingConflictError,
    AccountLinkingDeniedError,
    AccountLinkingProofMissingError,
    ContactAutoMergeRefusedError,
    DuplicateAccountSuspectedError,
    UnknownAccountLinkRequestError,
)
from epd2_identity_service.identifiers import (
    AccountId,
    ScopedIdentityReference,
    require_timezone,
)
from epd2_identity_service.providers import ProviderSubjectReference
from epd2_identity_service.stepup import StepUpResult


class LinkKind(StrEnum):
    EXTERNAL_PROVIDER = "external_provider"
    SECOND_ACCOUNT = "second_account"


class LinkState(StrEnum):
    REQUESTED = "requested"
    PROOF_PENDING = "proof_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNLINKED = "unlinked"


@dataclass(frozen=True, slots=True)
class ProofOfControl:
    """Evidence that the requester controls the side being linked.

    `established_at` and `method` are both required: a proof without a
    method is an assertion, and a proof without a time cannot be aged
    out.
    """

    method: str
    established_at: datetime

    def __post_init__(self) -> None:
        require_timezone(self.established_at, "established_at")
        if not self.method:
            raise AccountLinkingProofMissingError("a proof of control names its method")


@dataclass(frozen=True, slots=True)
class AccountLinkRequest:
    """A user-initiated link.

    `initiator_reference` is mandatory and is the account holder's own
    scoped reference - there is no field for an administrator, because an
    administrator-initiated link is not a thing this module supports.
    """

    link_request_id: UUID
    account_id: AccountId
    initiator_reference: ScopedIdentityReference
    kind: LinkKind
    state: LinkState
    requested_at: datetime
    subject_reference: ProviderSubjectReference | None = None
    counterpart_account_id: AccountId | None = None
    proof_this_side: ProofOfControl | None = None
    proof_other_side: ProofOfControl | None = None
    decided_at: datetime | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.requested_at, "requested_at")
        if self.decided_at is not None:
            require_timezone(self.decided_at, "decided_at")
        if self.kind is LinkKind.EXTERNAL_PROVIDER and self.subject_reference is None:
            raise UnknownAccountLinkRequestError(
                "an external-provider link names the provider subject reference"
            )
        if self.kind is LinkKind.SECOND_ACCOUNT and self.counterpart_account_id is None:
            raise UnknownAccountLinkRequestError("a second-account link names the counterpart")


def request_link(
    *,
    link_request_id: UUID,
    account_id: AccountId,
    initiator_reference: ScopedIdentityReference,
    kind: LinkKind,
    requested_at: datetime,
    subject_reference: ProviderSubjectReference | None = None,
    counterpart_account_id: AccountId | None = None,
) -> AccountLinkRequest:
    return AccountLinkRequest(
        link_request_id=link_request_id,
        account_id=account_id,
        initiator_reference=initiator_reference,
        kind=kind,
        state=LinkState.PROOF_PENDING,
        requested_at=require_timezone(requested_at, "requested_at"),
        subject_reference=subject_reference,
        counterpart_account_id=counterpart_account_id,
    )


def record_proof(
    request: AccountLinkRequest,
    *,
    this_side: ProofOfControl | None = None,
    other_side: ProofOfControl | None = None,
) -> AccountLinkRequest:
    return replace(
        request,
        proof_this_side=this_side or request.proof_this_side,
        proof_other_side=other_side or request.proof_other_side,
    )


def approve_link(
    request: AccountLinkRequest,
    *,
    step_up: StepUpResult,
    existing_links: tuple[AccountLinkRequest, ...],
    approved_at: datetime,
) -> AccountLinkRequest:
    """Approve, with both proofs, a step-up, and no conflict.

    The step-up is passed as a value rather than a boolean so it cannot
    be satisfied by a caller writing `True` - the object either exists,
    is bound and is unspent, or the call does not happen.
    """
    if request.proof_this_side is None or request.proof_other_side is None:
        raise AccountLinkingProofMissingError(
            "control of both sides must be proven before a link is approved"
        )
    if step_up.binding.action_code != "link_account":
        raise AccountLinkingDeniedError("the presented step-up is not bound to account linking")
    for other in existing_links:
        if other.state is not LinkState.APPROVED:
            continue
        if (
            request.kind is LinkKind.EXTERNAL_PROVIDER
            and other.subject_reference == request.subject_reference
            and other.account_id != request.account_id
        ):
            raise AccountLinkingConflictError(
                "this provider subject is already linked to a different account"
            )
        if (
            request.kind is LinkKind.SECOND_ACCOUNT
            and other.counterpart_account_id == request.counterpart_account_id
            and other.account_id != request.account_id
        ):
            raise AccountLinkingConflictError("this counterpart is already linked elsewhere")
    return replace(
        request,
        state=LinkState.APPROVED,
        decided_at=require_timezone(approved_at, "approved_at"),
    )


def reject_link(
    request: AccountLinkRequest, *, reason_code: str, decided_at: datetime
) -> AccountLinkRequest:
    return replace(
        request,
        state=LinkState.REJECTED,
        reason_code=reason_code,
        decided_at=require_timezone(decided_at, "decided_at"),
    )


def unlink(request: AccountLinkRequest, *, unlinked_at: datetime) -> AccountLinkRequest:
    """Unlinking is always available to the holder.

    A link the holder cannot undo is a link that becomes permanent by
    inconvenience, and permanence is what turns a link into an identity.
    """
    return replace(
        request, state=LinkState.UNLINKED, decided_at=require_timezone(unlinked_at, "unlinked_at")
    )


def refuse_merge_by_contact(left: AccountId, right: AccountId) -> None:
    """Refusal 1. Always raises.

    Delegates to the contacts module's own refusal first, so both entry
    points produce the same reason code, then raises unconditionally -
    `refuse_auto_merge` returns quietly when the two identifiers are the
    same account, and "they were the same account all along" is not a
    reason to perform a merge.
    """
    refuse_auto_merge(left, right)
    raise ContactAutoMergeRefusedError("accounts are never merged by a matching contact value")


def refuse_merge_by_personal_attributes(attribute_names: tuple[str, ...]) -> None:
    """Refusal 2. Always raises.

    Name and date of birth collide constantly in a population of any
    size, and a merge on them is a merge of two people.
    """
    raise AccountLinkingDeniedError(
        f"accounts are never merged on personal attributes ({', '.join(attribute_names)}); "
        "linking requires proof of control of both sides"
    )


def refuse_automatic_provider_merge(reference: ProviderSubjectReference) -> None:
    """Refusal 3. Always raises."""
    raise AccountLinkingDeniedError(
        f"a subject claim from {reference.issuer!r} never merges two accounts automatically; "
        "linking is user-initiated and step-up protected"
    )


def refuse_silent_reassignment(request: AccountLinkRequest) -> None:
    """Refusal 4. Always raises.

    Moving an existing link to a different account without the holder's
    involvement is a takeover that leaves the audit trail looking like
    housekeeping.
    """
    raise AccountLinkingConflictError(
        f"link {request.link_request_id} is never silently reassigned to another account"
    )


def route_duplicate_to_review(
    *, candidate_account_id: AccountId, named_signals: tuple[str, ...]
) -> None:
    """Duplicate handling: a reviewed decision, and a silent response.

    This raises `DUPLICATE_ACCOUNT_SUSPECTED` for the **internal** path.
    The public response is the uniform one from `authentication.py`,
    because telling a caller "an account like this already exists" is an
    account-existence oracle wearing a helpful tone.
    """
    raise DuplicateAccountSuspectedError(
        f"account {candidate_account_id} routed to duplicate review on: {', '.join(named_signals)}"
    )

"""PACK-15 Voting Context Registry (VC-01).

The definition of a vote as an **administrative object**: windows, scope,
rule-set version, assurance, revocation cutoff, privacy/audit/disclosure
profiles and the issuance timing profile. It is owned by
`governance-service` and deliberately not by `voting-service`:
`voting-service` owns `Ballot`, `VoteEnvelope` and `VoteReceipt`, and the
registry is read by the eligibility side, which must have no read edge to
anything that holds a cast ballot.

This module holds **no participant data of any kind** - no case, no
assertion, no credential, no ballot, no tally - and has no field through
which one could arrive.

Activation freezes the context: after `activate()` the critical parameters
are captured in an immutable `ActivationSnapshot`, and changing one
requires a new version or a governed suspension/re-activation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class VotingContextError(ValueError):
    """Base class; never raised directly."""


class VotingContextNotActiveError(VotingContextError):
    reason_code = "VOTING_CONTEXT_NOT_ACTIVE"


class VotingContextScopeMismatchError(VotingContextError):
    reason_code = "VOTING_CONTEXT_SCOPE_MISMATCH"


class VotingContextConfigurationInvalidError(VotingContextError):
    reason_code = "VOTING_CONTEXT_CONFIGURATION_INVALID"


class VotingContextSuspendedError(VotingContextError):
    reason_code = "VOTING_CONTEXT_SUSPENDED"


class VotingContextClosedError(VotingContextError):
    reason_code = "VOTING_CONTEXT_CLOSED"


class UnknownVotingContextError(VotingContextError):
    reason_code = "VOTING_CONTEXT_NOT_FOUND"


class DualControlRequiredError(VotingContextError):
    reason_code = "DUAL_CONTROL_REQUIRED"


class VotingType(StrEnum):
    """Seven types, **not** interchangeable in their rules."""

    INTERNAL_PARTY_VOTE = "internal_party_vote"
    PROGRAMME_VOTE = "programme_vote"
    ORGANIZATIONAL_ELECTION = "organizational_election"
    CANDIDATE_NOMINATION = "candidate_nomination"
    ASSEMBLY_DECISION = "assembly_decision"
    ADVISORY_CONSULTATION = "advisory_consultation"
    #: Profile only. Not activated, not permitted, not claimed.
    PUBLIC_ELECTION_PROFILE = "public_election_profile"


#: The public-election profile exists so the architecture does not
#: foreclose one. Activating it is refused here, structurally.
ACTIVATION_PROHIBITED_TYPES: frozenset[VotingType] = frozenset({VotingType.PUBLIC_ELECTION_PROFILE})

#: Revocation-cutoff maxima per type (specification section 14.1). The
#: cutoff bounds the window in which participation can be removed at all.
CUTOFF_AT_VOTING_WINDOW_OPEN: frozenset[VotingType] = frozenset(
    {VotingType.ORGANIZATIONAL_ELECTION, VotingType.CANDIDATE_NOMINATION}
)


class VotingContextStatus(StrEnum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    ACTIVE = "active"
    ISSUANCE_OPEN = "issuance_open"
    ISSUANCE_CLOSED = "issuance_closed"
    VOTING_OPEN = "voting_open"
    VOTING_CLOSED = "voting_closed"
    TALLIED = "tallied"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


CONTEXT_TRANSITIONS: Mapping[VotingContextStatus, frozenset[VotingContextStatus]] = {
    VotingContextStatus.DRAFT: frozenset(
        {VotingContextStatus.CONFIGURED, VotingContextStatus.CANCELLED}
    ),
    VotingContextStatus.CONFIGURED: frozenset(
        {VotingContextStatus.ACTIVE, VotingContextStatus.CANCELLED}
    ),
    VotingContextStatus.ACTIVE: frozenset(
        {
            VotingContextStatus.ISSUANCE_OPEN,
            VotingContextStatus.SUSPENDED,
            VotingContextStatus.CANCELLED,
        }
    ),
    VotingContextStatus.ISSUANCE_OPEN: frozenset(
        {
            VotingContextStatus.ISSUANCE_CLOSED,
            VotingContextStatus.SUSPENDED,
            VotingContextStatus.CANCELLED,
        }
    ),
    VotingContextStatus.ISSUANCE_CLOSED: frozenset(
        {VotingContextStatus.VOTING_OPEN, VotingContextStatus.SUSPENDED}
    ),
    VotingContextStatus.VOTING_OPEN: frozenset(
        {VotingContextStatus.VOTING_CLOSED, VotingContextStatus.SUSPENDED}
    ),
    VotingContextStatus.VOTING_CLOSED: frozenset({VotingContextStatus.TALLIED}),
    VotingContextStatus.TALLIED: frozenset({VotingContextStatus.ARCHIVED}),
    VotingContextStatus.SUSPENDED: frozenset(
        {VotingContextStatus.ACTIVE, VotingContextStatus.CANCELLED}
    ),
    VotingContextStatus.ARCHIVED: frozenset(),
    VotingContextStatus.CANCELLED: frozenset(),
}

#: Statuses in which credential issuance may occur.
ISSUANCE_STATUSES: frozenset[VotingContextStatus] = frozenset({VotingContextStatus.ISSUANCE_OPEN})

#: Statuses after which outcome-bearing evidence may be exported.
CLOSED_STATUSES: frozenset[VotingContextStatus] = frozenset(
    {VotingContextStatus.VOTING_CLOSED, VotingContextStatus.TALLIED, VotingContextStatus.ARCHIVED}
)


@dataclass(frozen=True, slots=True)
class VotingWindow:
    starts_at: datetime
    ends_at: datetime

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise VotingContextConfigurationInvalidError("timestamps are timezone-aware")
        if self.ends_at <= self.starts_at:
            raise VotingContextConfigurationInvalidError("a window ends after it starts")

    def contains(self, moment: datetime) -> bool:
        return self.starts_at <= moment < self.ends_at


@dataclass(frozen=True, slots=True)
class DisclosureControlProfile:
    """Minimum cell size and the small-electorate flag.

    `minimum_cell` is a floor of 5 and is never lowered per context - a
    small electorate raises it, never lowers it.
    """

    minimum_cell: int = 5
    small_electorate: bool = False
    per_scope_metrics_permitted: bool = True

    def __post_init__(self) -> None:
        if self.minimum_cell < 5:
            raise VotingContextConfigurationInvalidError(
                "the disclosure minimum cell size has a floor of 5"
            )
        if self.small_electorate and self.per_scope_metrics_permitted:
            raise VotingContextConfigurationInvalidError(
                "a small electorate publishes no per-scope operational metric at all"
            )


@dataclass(frozen=True, slots=True)
class ActivationSnapshot:
    """The immutable capture taken at activation.

    Its digest is what makes "the critical parameters were frozen" a
    checkable claim rather than an assurance.
    """

    snapshot_digest: str
    captured_at: datetime
    parameters: Mapping[str, str]

    def __post_init__(self) -> None:
        if len(self.snapshot_digest) != 64:
            raise VotingContextConfigurationInvalidError("an activation snapshot carries a digest")


def compute_snapshot_digest(parameters: Mapping[str, str]) -> str:
    return hashlib.sha256(
        json.dumps(dict(parameters), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class VotingContext:
    """The administrative definition of one vote."""

    voting_context_id: UUID
    voting_context_reference: str
    version: int
    voting_type: VotingType
    organizational_scope: str
    status: VotingContextStatus
    voting_window: VotingWindow
    credential_issuance_window: VotingWindow
    revocation_cutoff: datetime
    eligibility_rule_set_reference: str
    eligibility_rule_set_version: str
    required_assurance: str
    participation_class: str
    privacy_profile: str
    audit_profile: str
    disclosure_control: DisclosureControlProfile
    eligible_population: int
    activation_snapshot: ActivationSnapshot | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise VotingContextConfigurationInvalidError("a context version starts at 1")
        if not self.voting_context_reference:
            raise VotingContextConfigurationInvalidError("a context names its reference")
        if self.credential_issuance_window.ends_at > self.voting_window.ends_at:
            raise VotingContextConfigurationInvalidError(
                "the issuance window closes no later than the voting window"
            )
        self._assert_cutoff_maximum()

    def _assert_cutoff_maximum(self) -> None:
        if self.voting_type in CUTOFF_AT_VOTING_WINDOW_OPEN:
            maximum = self.voting_window.starts_at
        else:
            maximum = self.credential_issuance_window.ends_at
        if self.revocation_cutoff > maximum:
            raise VotingContextConfigurationInvalidError(
                f"the revocation cutoff for {self.voting_type.value} may not be later than "
                f"{maximum.isoformat()}"
            )

    # -- state -------------------------------------------------------------

    def critical_parameters(self) -> dict[str, str]:
        """The parameters frozen at activation."""
        return {
            "voting_context_reference": self.voting_context_reference,
            "version": str(self.version),
            "voting_type": self.voting_type.value,
            "organizational_scope": self.organizational_scope,
            "voting_window_start": self.voting_window.starts_at.isoformat(),
            "voting_window_end": self.voting_window.ends_at.isoformat(),
            "issuance_window_start": self.credential_issuance_window.starts_at.isoformat(),
            "issuance_window_end": self.credential_issuance_window.ends_at.isoformat(),
            "revocation_cutoff": self.revocation_cutoff.isoformat(),
            "rule_set_reference": self.eligibility_rule_set_reference,
            "rule_set_version": self.eligibility_rule_set_version,
            "required_assurance": self.required_assurance,
            "participation_class": self.participation_class,
            "privacy_profile": self.privacy_profile,
            "audit_profile": self.audit_profile,
            "disclosure_minimum_cell": str(self.disclosure_control.minimum_cell),
        }

    def activate(self, *, now: datetime, approver: str, second_approver: str) -> VotingContext:
        """Activate under dual control, capturing the immutable snapshot."""
        if self.voting_type in ACTIVATION_PROHIBITED_TYPES:
            raise VotingContextConfigurationInvalidError(
                "the public-election profile is not activated, not permitted and not claimed"
            )
        if self.status is not VotingContextStatus.CONFIGURED:
            raise VotingContextNotActiveError(
                f"a context is activated from `configured`, not from {self.status.value!r}"
            )
        if not approver or not second_approver or approver == second_approver:
            raise DualControlRequiredError("activation requires two distinct authorized approvers")
        parameters = self.critical_parameters()
        snapshot = ActivationSnapshot(
            snapshot_digest=compute_snapshot_digest(parameters),
            captured_at=now,
            parameters=parameters,
        )
        return replace(self, status=VotingContextStatus.ACTIVE, activation_snapshot=snapshot)

    def transition(self, target: VotingContextStatus) -> VotingContext:
        if target not in CONTEXT_TRANSITIONS[self.status]:
            raise VotingContextNotActiveError(
                f"{self.status.value} -> {target.value} is not a permitted transition"
            )
        return replace(self, status=target)

    def new_version_with(self, **changes: object) -> VotingContext:
        """Change a critical parameter by producing a **new version**.

        An activated context is frozen: this is the only way to change one,
        and the new version starts at `draft` so it must be configured and
        dual-control activated again.
        """
        if self.activation_snapshot is None:
            raise VotingContextConfigurationInvalidError(
                "an unactivated context is edited in place, not re-versioned"
            )
        return replace(
            self,
            version=self.version + 1,
            status=VotingContextStatus.DRAFT,
            activation_snapshot=None,
            **changes,  # type: ignore[arg-type]
        )

    def assert_snapshot_intact(self) -> None:
        """Refuse a context whose frozen parameters have drifted."""
        if self.activation_snapshot is None:
            return
        current = compute_snapshot_digest(self.critical_parameters())
        if current != self.activation_snapshot.snapshot_digest:
            raise VotingContextConfigurationInvalidError(
                "the activated context's critical parameters have changed without a new version"
            )

    def assert_issuance_permitted(self, now: datetime) -> None:
        if self.status is VotingContextStatus.SUSPENDED:
            raise VotingContextSuspendedError("the voting context is suspended")
        if self.status in {VotingContextStatus.CANCELLED, VotingContextStatus.ARCHIVED}:
            raise VotingContextClosedError("the voting context is closed")
        if self.status not in ISSUANCE_STATUSES:
            raise VotingContextNotActiveError("the voting context is not open for issuance")
        if not self.credential_issuance_window.contains(now):
            raise VotingContextNotActiveError("the credential issuance window is not open")
        self.assert_snapshot_intact()

    def assert_scope(self, organizational_scope: str) -> None:
        if organizational_scope != self.organizational_scope:
            raise VotingContextScopeMismatchError(
                "the organizational scope does not match the voting context"
            )

    @property
    def closed_for_outcome_evidence(self) -> bool:
        return self.status in CLOSED_STATUSES


class VotingContextStore(Protocol):
    def save(self, context: VotingContext) -> None: ...

    def get(self, voting_context_reference: str, version: int) -> VotingContext | None: ...

    def latest(self, voting_context_reference: str) -> VotingContext | None: ...

    def versions(self, voting_context_reference: str) -> Sequence[VotingContext]: ...


class InMemoryVotingContextStore:
    def __init__(self) -> None:
        self._contexts: dict[tuple[str, int], VotingContext] = {}

    def save(self, context: VotingContext) -> None:
        self._contexts[(context.voting_context_reference, context.version)] = context

    def get(self, voting_context_reference: str, version: int) -> VotingContext | None:
        return self._contexts.get((voting_context_reference, version))

    def latest(self, voting_context_reference: str) -> VotingContext | None:
        matching = self.versions(voting_context_reference)
        return matching[-1] if matching else None

    def versions(self, voting_context_reference: str) -> Sequence[VotingContext]:
        return tuple(
            context
            for (reference, _), context in sorted(self._contexts.items())
            if reference == voting_context_reference
        )


#: Fields no voting-context record may ever carry.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "membership_id",
        "member_number",
        "participant_reference",
        "assertion_id",
        "voting_credential_id",
        "ballot_id",
        "turnout",
        "vote_totals",
    }
)


def assert_no_participant_data(payload: Mapping[str, object]) -> None:
    offending = sorted(set(payload) & FORBIDDEN_FIELD_NAMES)
    if offending:
        raise VotingContextConfigurationInvalidError(
            "a voting context carries no participant or outcome data: " + ", ".join(offending)
        )

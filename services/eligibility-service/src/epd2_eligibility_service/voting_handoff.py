"""PACK-14 handoff acceptance and the one-time WS-03 pickup (VC-05).

The ordinary workspace transmits **only** PACK-14's opaque, single-use,
audience- and context-bound `VotingHandoffArtifact` (ADR-088). This module
accepts it on the PACK-15 side and serves the one-time assertion pickup to
the isolated voting origin.

What an acceptance record holds is deliberately almost nothing: the
artifact's digest, the voting context, the audience and origin it was bound
to, and when it was consumed. It holds **no account reference and no
session**, so nothing here permits reverse identity resolution - which is
the property ADR-088 handed to this round to preserve.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from epd2_eligibility_service.voting_trust_exceptions import (
    HandoffAlreadyUsedError,
    HandoffAudienceMismatchError,
    HandoffExpiredError,
    HandoffInvalidError,
    HandoffOriginMismatchError,
)

#: Fields a handoff artifact may never carry (ADR-088, restated so this
#: side refuses them rather than trusting the issuing side).
HANDOFF_FORBIDDEN_FIELDS: frozenset[str] = frozenset(
    {
        "account_id",
        "person_id",
        "person_record_id",
        "membership_id",
        "member_number",
        "communication_persona_id",
        "email",
        "phone",
        "session_id",
        "device_id",
    }
)


def artifact_digest(artifact_value: str) -> str:
    """A digest of the opaque artifact, used as its one-time key.

    The artifact value itself is never stored: an acceptance record that
    held it would be a replayable secret at rest.
    """
    if not artifact_value:
        raise HandoffInvalidError("an empty handoff artifact never verifies")
    return hashlib.sha256(artifact_value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class VotingHandoffArtifact:
    """The inbound view of PACK-14's outbound artifact.

    Opaque `value`, plus the bindings this side must check before reading
    anything else.
    """

    value: str
    voting_context_reference: str
    audience: str
    origin: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.value:
            raise HandoffInvalidError("a handoff artifact carries an opaque value")
        if self.expires_at.tzinfo is None:
            raise HandoffInvalidError("timestamps are timezone-aware at this boundary")


@dataclass(frozen=True, slots=True)
class HandoffAcceptance:
    """The record of one accepted, single-use handoff.

    Carries no account, no session and nothing from which one could be
    derived.
    """

    acceptance_id: UUID
    artifact_digest: str
    voting_context_reference: str
    audience: str
    origin: str
    accepted_at: datetime
    consumed_at: datetime | None = None

    def __post_init__(self) -> None:
        if len(self.artifact_digest) != 64:
            raise HandoffInvalidError("an acceptance stores the artifact digest, never its value")
        if self.accepted_at.tzinfo is None:
            raise HandoffInvalidError("timestamps are timezone-aware")

    @property
    def consumed(self) -> bool:
        return self.consumed_at is not None


@dataclass(frozen=True, slots=True)
class HandoffBinding:
    """The bindings this boundary enforces, as governed configuration."""

    expected_audience: str
    allowed_origins: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.expected_audience:
            raise ValueError("a handoff binding names its audience")
        if not self.allowed_origins:
            raise ValueError("a handoff binding names at least one allowed origin")


def verify_handoff(
    artifact: VotingHandoffArtifact,
    *,
    binding: HandoffBinding,
    voting_context_reference: str,
    now: datetime,
    previous: HandoffAcceptance | None,
) -> str:
    """Verify a handoff artifact and return its digest.

    Order matters: **origin and audience are checked before anything
    else is read**, so a misdirected artifact is refused without its
    contents being processed at all.
    """
    if artifact.origin not in binding.allowed_origins:
        raise HandoffOriginMismatchError(
            "the handoff artifact was presented from an origin it is not bound to"
        )
    if not hmac.compare_digest(artifact.audience, binding.expected_audience):
        raise HandoffAudienceMismatchError(
            "the handoff artifact was presented to an audience it is not bound to"
        )
    if artifact.voting_context_reference != voting_context_reference:
        raise HandoffInvalidError("the handoff artifact belongs to a different voting context")
    if now >= artifact.expires_at:
        raise HandoffExpiredError("the handoff artifact has expired")
    digest = artifact_digest(artifact.value)
    if previous is not None:
        raise HandoffAlreadyUsedError(
            "a handoff artifact is single-use; a second presentation is refused"
        )
    return digest


def assert_handoff_payload_minimal(payload: dict[str, object]) -> None:
    """Refuse a handoff payload carrying an identity field."""
    offending = sorted(set(payload) & HANDOFF_FORBIDDEN_FIELDS)
    if offending:
        raise HandoffInvalidError(
            "a handoff artifact may not carry identity fields: " + ", ".join(offending)
        )

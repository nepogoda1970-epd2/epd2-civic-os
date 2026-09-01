"""Privileged session evidence - references, not an archive (ADR-068).

A grant answers "who was allowed to do what". Session evidence answers
"what did they actually do", and it is the only thing an independent
reviewer has to review.

The design constraint that shapes every field: evidence detailed enough
to review is, by construction, a record of what sensitive material
someone looked at. Stored naively it becomes a second copy of the
platform's most sensitive content, held in the one subsystem that is
deliberately hardest to delete from. So:

- **References, never copies** (`P12-SES-003`). `accessed_resources`
  holds pointers; `operation_summaries` holds a governed summary per
  operation, not the operation's input or output.
- **No secrets** (`P12-SES-002`). `reject_prohibited_payload_keys` runs
  over every summary at construction, so a builder that reaches for a
  token fails closed rather than sealing it into the chain.
- **Sealed once, then immutable** (`P12-SES-004`). After `seal`, the
  object exposes no mutating method; `SealedPrivilegedSession` is a
  distinct type, so "can I still append to this?" is answered by the
  type system rather than by a flag.

The chaining rule reuses PACK-02's exactly -
`sha256(canonical_dumps(fields) + previous_hash)` - so one verification
procedure covers the audit chain, PACK-11's document versions and these
sessions (`P12-SES-005`).

**Tamper evidence, not tamper resistance** (`P12-SES-007`). A sealed
session is detectably altered, not unalterable. An actor with sufficient
infrastructure access can rewrite and recompute, because there is no
external anchor. Nothing in this module may be described otherwise.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from epd2_core.canonical_json import canonical_dumps
from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
    PurposeBinding,
    reject_prohibited_payload_keys,
    require_text,
    require_timezone,
)
from epd2_privileged_access_service.exceptions import (
    ForbiddenTransitionError,
    SessionEvidenceIncompleteError,
    UnknownStatusError,
)

GENESIS_PREVIOUS_HASH = "0" * 64


class SessionState(StrEnum):
    STARTED = "started"
    ENDED = "ended"
    SEALED = "sealed"
    REVIEWED = "reviewed"


@dataclass(frozen=True, slots=True)
class OperationSummary:
    """One governed operation, summarised.

    `summary_reference` is a pointer at a governed summary, not the
    summary text: deciding what is reviewable without being a content
    copy is a design obligation the reviewer's own surface carries, and
    embedding prose here would smuggle content into the chain."""

    sequence: int
    occurred_at: datetime
    operation: str
    resource_domain: str
    resource_reference: str | None
    outcome: str
    summary_reference: str

    def __post_init__(self) -> None:
        require_timezone(self.occurred_at, context="OperationSummary.occurred_at")
        require_text(self.operation, "operation")
        require_text(self.resource_domain, "resource_domain")
        require_text(self.summary_reference, "summary_reference")
        if self.sequence < 1:
            raise SessionEvidenceIncompleteError("sequence must be a positive integer")
        if self.outcome not in {"succeeded", "refused", "failed"}:
            raise UnknownStatusError(f"unknown operation outcome {self.outcome!r}")
        reject_prohibited_payload_keys(self.to_payload(), context="OperationSummary")

    def to_payload(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "occurred_at": self.occurred_at.isoformat(),
            "operation": self.operation,
            "resource_domain": self.resource_domain,
            "resource_reference": self.resource_reference,
            "outcome": self.outcome,
            "summary_reference": self.summary_reference,
        }


@dataclass(frozen=True, slots=True)
class PrivilegedSession:
    """An open privileged session.

    The eighteen mandatory fields of `P12-SES-001`. Fields that are
    genuinely optional at start time (`ended_at`, the integrity
    reference) become mandatory at seal time, which is what `seal`
    enforces."""

    session_id: UUID
    actor_reference: str
    effective_role: str
    grant_reference: UUID
    purpose: PurposeBinding
    target_system: str
    target_domain: str
    organization_scope: OrganizationalScopeRef
    permitted_operations: frozenset[str]
    started_at: datetime
    approval_references: tuple[str, ...] = ()
    break_glass_marker: bool = False
    state: SessionState = SessionState.STARTED
    ended_at: datetime | None = None
    operation_summaries: tuple[OperationSummary, ...] = ()
    accessed_resources: tuple[str, ...] = ()
    search_actions: tuple[UUID, ...] = ()
    export_actions: tuple[UUID, ...] = ()
    evidence_bundle_reference: str | None = None
    review_status: str = "pending"
    previous_hash: str = GENESIS_PREVIOUS_HASH

    def __post_init__(self) -> None:
        require_text(self.actor_reference, "actor_reference")
        require_text(self.effective_role, "effective_role")
        require_text(self.target_system, "target_system")
        require_text(self.target_domain, "target_domain")
        require_timezone(self.started_at, context="PrivilegedSession.started_at")
        if not self.permitted_operations:
            raise SessionEvidenceIncompleteError(
                "a session must record the operations it was permitted"
            )
        if self.ended_at is not None:
            require_timezone(self.ended_at, context="PrivilegedSession.ended_at")
            if self.ended_at < self.started_at:
                raise SessionEvidenceIncompleteError("ended_at must not precede started_at")
        if len(self.previous_hash) != 64:
            raise SessionEvidenceIncompleteError("previous_hash must be a 64-character digest")

    # -- accumulation ------------------------------------------------------

    def with_operation(self, summary: OperationSummary) -> PrivilegedSession:
        if self.state is not SessionState.STARTED:
            raise ForbiddenTransitionError(
                "operations may only be recorded on a session that is still started"
            )
        return replace(self, operation_summaries=(*self.operation_summaries, summary))

    def with_accessed_resource(self, reference: str) -> PrivilegedSession:
        require_text(reference, "resource reference")
        if reference in self.accessed_resources:
            return self
        return replace(self, accessed_resources=(*self.accessed_resources, reference))

    def with_search_action(self, query_id: UUID) -> PrivilegedSession:
        return replace(self, search_actions=(*self.search_actions, query_id))

    def with_export_action(self, export_id: UUID) -> PrivilegedSession:
        return replace(self, export_actions=(*self.export_actions, export_id))

    def end(self, at: datetime) -> PrivilegedSession:
        require_timezone(at, context="PrivilegedSession.end")
        if self.state is not SessionState.STARTED:
            raise ForbiddenTransitionError(f"a session in state {self.state.value} cannot be ended")
        if at < self.started_at:
            raise SessionEvidenceIncompleteError("end instant must not precede the start")
        return replace(self, state=SessionState.ENDED, ended_at=at)

    # -- sealing -----------------------------------------------------------

    def hashable_fields(self) -> dict[str, object]:
        """Every field that participates in the integrity hash.

        Covers the whole record deliberately: a snapshot that is only
        nearly complete leaves the omitted fields outside the
        tamper-evidence hash and signals nothing about the gap."""
        return {
            "session_id": str(self.session_id),
            "actor_reference": self.actor_reference,
            "effective_role": self.effective_role,
            "grant_reference": str(self.grant_reference),
            "purpose": self.purpose.to_payload(),
            "target_system": self.target_system,
            "target_domain": self.target_domain,
            "organization_scope": self.organization_scope.to_payload(),
            "permitted_operations": sorted(self.permitted_operations),
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "approval_references": list(self.approval_references),
            "break_glass_marker": self.break_glass_marker,
            "operation_summaries": [s.to_payload() for s in self.operation_summaries],
            "accessed_resources": list(self.accessed_resources),
            "search_actions": [str(q) for q in self.search_actions],
            "export_actions": [str(e) for e in self.export_actions],
            "evidence_bundle_reference": self.evidence_bundle_reference,
            "review_status": self.review_status,
        }

    def seal(self, *, evidence_bundle_reference: str) -> SealedPrivilegedSession:
        """Seal the session with a tamper-evident integrity reference.

        Refuses a session that is not ended, or that lacks any mandatory
        evidence field (`P12-SES-001`). The evidence bundle reference is
        PACK-11's; PACK-12 defines no parallel evidence store
        (`P12-SES-005`)."""
        if self.state is not SessionState.ENDED:
            raise ForbiddenTransitionError("only an ended session can be sealed")
        if self.ended_at is None:  # pragma: no cover - guarded by `end`
            raise SessionEvidenceIncompleteError("a sealed session must record its end instant")
        require_text(evidence_bundle_reference, "evidence_bundle_reference")
        payload = self.hashable_fields()
        payload["evidence_bundle_reference"] = evidence_bundle_reference
        reject_prohibited_payload_keys(payload, context="PrivilegedSession.seal")
        integrity = compute_session_hash(payload, self.previous_hash)
        return SealedPrivilegedSession(
            session_id=self.session_id,
            organization_scope=self.organization_scope,
            sealed_payload=payload,
            evidence_bundle_reference=evidence_bundle_reference,
            previous_hash=self.previous_hash,
            integrity_reference=integrity,
            sealed_at=self.ended_at,
        )


def compute_session_hash(payload: dict[str, object], previous_hash: str) -> str:
    """`sha256(canonical_dumps(payload) + previous_hash)`.

    The same rule PACK-02's audit chain and PACK-11's document versions
    use, so one verification procedure covers all three."""
    serialized = canonical_dumps(payload)
    return hashlib.sha256((serialized + previous_hash).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SealedPrivilegedSession:
    """A sealed session. A distinct type, deliberately.

    There is no `with_operation`, no `end`, no `replace`-friendly
    mutator and no setter: after sealing, the only operations are reading
    and verifying (`P12-SES-004`, `P12-SES-006`). An
    `audit_custodian` and an `independent_privileged_access_reviewer`
    can both read this; neither can alter it, because there is nothing
    to call."""

    session_id: UUID
    organization_scope: OrganizationalScopeRef
    sealed_payload: dict[str, object]
    evidence_bundle_reference: str
    previous_hash: str
    integrity_reference: str
    sealed_at: datetime
    review_status: str = "pending"
    review_reference: str | None = None

    def __post_init__(self) -> None:
        require_timezone(self.sealed_at, context="SealedPrivilegedSession.sealed_at")
        if len(self.integrity_reference) != 64:
            raise SessionEvidenceIncompleteError("integrity_reference must be a sha256 digest")

    def verify(self) -> bool:
        """Whether the sealed payload still hashes to its recorded
        integrity reference.

        Tamper **evidence**: this detects alteration. It does not prevent
        it, and an actor able to rewrite both the payload and the digest
        is not detected by this method (`P12-SES-007`)."""
        return compute_session_hash(self.sealed_payload, self.previous_hash) == (
            self.integrity_reference
        )

    def with_review(self, *, reference: str, status: str) -> SealedPrivilegedSession:
        """Attach a review outcome.

        This is not a mutation of the sealed evidence: `sealed_payload`,
        `previous_hash` and `integrity_reference` are untouched, and
        `verify()` still returns what it returned before. Review status
        lives outside the hash precisely so that reviewing does not
        require breaking the seal."""
        if status not in {"pending", "accepted", "findings_raised"}:
            raise UnknownStatusError(f"unknown session review status {status!r}")
        return replace(self, review_status=status, review_reference=require_text(reference, "ref"))

    def to_state_payload(self) -> dict[str, object]:
        return {
            "session_id": str(self.session_id),
            "organization_scope": self.organization_scope.to_payload(),
            "evidence_bundle_reference": self.evidence_bundle_reference,
            "previous_hash": self.previous_hash,
            "integrity_reference": self.integrity_reference,
            "sealed_at": self.sealed_at.isoformat(),
            "review_status": self.review_status,
            "review_reference": self.review_reference,
        }


def verify_session_chain(sessions: tuple[SealedPrivilegedSession, ...]) -> tuple[bool, int | None]:
    """Verify a chain of sealed sessions.

    Returns `(ok, first_broken_index)`. Linkage is checked as well as
    each link's own digest, because a chain whose individual entries
    verify but whose links do not is a chain somebody re-cut."""
    previous = GENESIS_PREVIOUS_HASH
    for index, session in enumerate(sessions):
        if session.previous_hash != previous:
            return False, index
        if not session.verify():
            return False, index
        previous = session.integrity_reference
    return True, None

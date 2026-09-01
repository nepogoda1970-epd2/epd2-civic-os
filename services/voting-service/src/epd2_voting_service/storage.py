"""Storage protocols and in-memory reference adapters for Voting
Service's four owned entities.

`_BallotRecord` mirrors `epd2_credential_service.storage._CredentialRecord`'s
pattern: it carries two internal-only bookkeeping fields alongside the
public `Ballot`, neither ever exposed by any public method except their
own narrow, internal-lookup accessors -

- `created_by_actor_id` - the actor who created the ballot (ADR-009 item
  7 / INV-08: `approve_ballot_configuration` must reject the same actor
  approving their own ballot). Not a canon `Ballot` field - internal
  bookkeeping only, documented the same way credential-service documents
  `issuance_reference`.
- `frozen_eligibility_snapshot_digest` - the real `EligibilitySnapshot.digest`
  this ballot's `configuration_hash` was computed against at freeze time
  (`submit_ballot_for_configuration_review`), used later by `cast_vote` to
  cross-check a presented credential's own `eligibility_snapshot_digest`
  against the exact snapshot this ballot froze to. Also not a canon
  `Ballot` field.

`InMemoryBallotStore.save` is where CT-00-10's rule-freeze guarantee is
structurally enforced, reusing exactly the pattern
`InMemoryEligibilityRuleStore.save` established for `EligibilityRule`
immutability: once a stored ballot's own status has left `draft`, any
attempt to persist different `configuration_fields(...)` content raises
`BallotConfigurationLockedError` rather than silently overwriting it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol
from uuid import UUID

from epd2_voting_service.domain import (
    Ballot,
    BallotOption,
    BallotStatus,
    VoteEnvelope,
    VoteEnvelopeStatus,
    VoteReceipt,
    configuration_fields,
)
from epd2_voting_service.exceptions import (
    BallotConfigurationLockedError,
    BallotCreationConflictError,
    UnknownBallotError,
    UnknownVoteEnvelopeError,
    VoteEnvelopeCreationConflictError,
    VoteReceiptCreationConflictError,
)


@dataclass(frozen=True, slots=True)
class _BallotRecord:
    public: Ballot
    created_by_actor_id: UUID
    frozen_eligibility_snapshot_digest: str | None


class BallotStore(Protocol):
    def create(self, ballot: Ballot, *, created_by_actor_id: UUID) -> Ballot:
        """Create a new ballot (must be `status == draft`). If
        `ballot.ballot_id` already exists with identical public content,
        returns the existing public ballot (idempotent). If it exists
        with different content, raises `BallotCreationConflictError`."""
        ...

    def save(self, ballot: Ballot) -> Ballot:
        """Persist an update to an already-created ballot. Once the
        *currently stored* ballot's status has left `draft`,
        `configuration_fields(...)` (the `configuration_hash`-covered
        fields, using the effective challenge window) must be unchanged
        from what is already stored, or `BallotConfigurationLockedError`
        is raised (CT-00-10). `status` itself, and `configuration_hash`
        (set exactly once, in the same call that leaves `draft`), are not
        subject to this check. Raises `UnknownBallotError` if no ballot
        with this id was ever `create`d."""
        ...

    def get(self, ballot_id: UUID) -> Ballot | None: ...

    def created_by_actor_id_for(self, ballot_id: UUID) -> UUID | None:
        """Internal-only lookup, used solely for the ADR-009 item 7
        second-actor approval check - never exposed outside this
        service."""
        ...

    def frozen_eligibility_snapshot_digest_for(self, ballot_id: UUID) -> str | None:
        """Internal-only lookup of the `EligibilitySnapshot.digest` this
        ballot's configuration was frozen against, set once by
        `set_frozen_eligibility_snapshot_digest` - never exposed outside
        this service."""
        ...

    def set_frozen_eligibility_snapshot_digest(self, ballot_id: UUID, digest: str) -> None:
        """Record the `EligibilitySnapshot.digest` a ballot's
        configuration was frozen against. Called exactly once, by
        `application.submit_ballot_for_configuration_review`."""
        ...


class InMemoryBallotStore:
    def __init__(self) -> None:
        self._records: dict[UUID, _BallotRecord] = {}

    def create(self, ballot: Ballot, *, created_by_actor_id: UUID) -> Ballot:
        existing = self._records.get(ballot.ballot_id)
        if existing is not None:
            if existing.public == ballot and existing.created_by_actor_id == created_by_actor_id:
                return existing.public
            raise BallotCreationConflictError(
                f"ballot_id {ballot.ballot_id} already created with different content"
            )
        self._records[ballot.ballot_id] = _BallotRecord(
            public=ballot,
            created_by_actor_id=created_by_actor_id,
            frozen_eligibility_snapshot_digest=None,
        )
        return ballot

    def save(self, ballot: Ballot) -> Ballot:
        existing = self._records.get(ballot.ballot_id)
        if existing is None:
            raise UnknownBallotError(f"unknown ballot_id: {ballot.ballot_id}")
        if existing.public.status != BallotStatus.DRAFT and configuration_fields(
            existing.public
        ) != configuration_fields(ballot):
            raise BallotConfigurationLockedError(
                f"ballot {ballot.ballot_id} configuration is frozen "
                f"(status {existing.public.status.value!r}) and cannot be mutated"
            )
        self._records[ballot.ballot_id] = replace(existing, public=ballot)
        return ballot

    def get(self, ballot_id: UUID) -> Ballot | None:
        record = self._records.get(ballot_id)
        return record.public if record is not None else None

    def created_by_actor_id_for(self, ballot_id: UUID) -> UUID | None:
        record = self._records.get(ballot_id)
        return record.created_by_actor_id if record is not None else None

    def frozen_eligibility_snapshot_digest_for(self, ballot_id: UUID) -> str | None:
        record = self._records.get(ballot_id)
        return record.frozen_eligibility_snapshot_digest if record is not None else None

    def set_frozen_eligibility_snapshot_digest(self, ballot_id: UUID, digest: str) -> None:
        existing = self._records.get(ballot_id)
        if existing is None:
            raise UnknownBallotError(f"unknown ballot_id: {ballot_id}")
        self._records[ballot_id] = replace(existing, frozen_eligibility_snapshot_digest=digest)


class BallotOptionStore(Protocol):
    def add(self, option: BallotOption) -> BallotOption:
        """Add a new option (idempotent by `ballot_option_id`, same
        conflict-or-idempotent shape as `BallotStore.create`)."""
        ...

    def save(self, option: BallotOption) -> BallotOption:
        """Persist an update to an already-added option (e.g. its
        `active -> locked` transition in `open_ballot`)."""
        ...

    def get(self, ballot_option_id: UUID) -> BallotOption | None: ...

    def list_for_ballot(self, ballot_id: UUID) -> tuple[BallotOption, ...]: ...


class InMemoryBallotOptionStore:
    def __init__(self) -> None:
        self._options: dict[UUID, BallotOption] = {}

    def add(self, option: BallotOption) -> BallotOption:
        existing = self._options.get(option.ballot_option_id)
        if existing is not None:
            if existing == option:
                return existing
            raise BallotCreationConflictError(
                f"ballot_option_id {option.ballot_option_id} already added with different content"
            )
        self._options[option.ballot_option_id] = option
        return option

    def save(self, option: BallotOption) -> BallotOption:
        self._options[option.ballot_option_id] = option
        return option

    def get(self, ballot_option_id: UUID) -> BallotOption | None:
        return self._options.get(ballot_option_id)

    def list_for_ballot(self, ballot_id: UUID) -> tuple[BallotOption, ...]:
        return tuple(o for o in self._options.values() if o.ballot_id == ballot_id)


class VoteEnvelopeStore(Protocol):
    def create(self, envelope: VoteEnvelope) -> VoteEnvelope:
        """Idempotent create by `vote_envelope_id`: if it already exists
        with identical content, returns the existing record (CT-00-04
        replay of `cast_vote` is a no-op); if it exists with different
        content, raises `VoteEnvelopeCreationConflictError`. Used only
        for a brand-new envelope's very first persist - never for a
        later status transition (see `save`)."""
        ...

    def save(self, envelope: VoteEnvelope) -> VoteEnvelope:
        """Persist an update to an already-`create`d envelope (e.g. its
        `received -> validated`/`rejected` or `validated -> superseded`/
        `included` transition). Unlike `create`, this unconditionally
        overwrites - callers only ever pass a status-derived successor
        from `VoteEnvelope.with_status`, which itself enforces the
        transition table, so there is nothing left here to conflict-
        check. Raises `UnknownVoteEnvelopeError` if no envelope with this
        id was ever `create`d."""
        ...

    def get(self, vote_envelope_id: UUID) -> VoteEnvelope | None: ...

    def find_validated_for_credential(
        self, ballot_id: UUID, credential_proof: UUID
    ) -> VoteEnvelope | None:
        """The current `validated` envelope, if any, for this
        `(ballot_id, credential_proof)` pair - the "previous valid
        envelope" ADR-009 items 1-2 require `cast_vote` to supersede when
        the same credential casts a new vote. At most one such envelope
        can exist at a time by construction (every `cast_vote` call that
        finds one immediately supersedes it before/while saving the new
        one)."""
        ...

    def list_for_ballot(self, ballot_id: UUID) -> tuple[VoteEnvelope, ...]: ...


class InMemoryVoteEnvelopeStore:
    def __init__(self) -> None:
        self._envelopes: dict[UUID, VoteEnvelope] = {}

    def create(self, envelope: VoteEnvelope) -> VoteEnvelope:
        existing = self._envelopes.get(envelope.vote_envelope_id)
        if existing is not None:
            if existing == envelope:
                return existing
            raise VoteEnvelopeCreationConflictError(
                f"vote_envelope_id {envelope.vote_envelope_id} already exists with "
                "different content"
            )
        self._envelopes[envelope.vote_envelope_id] = envelope
        return envelope

    def save(self, envelope: VoteEnvelope) -> VoteEnvelope:
        if envelope.vote_envelope_id not in self._envelopes:
            raise UnknownVoteEnvelopeError(f"unknown vote_envelope_id: {envelope.vote_envelope_id}")
        self._envelopes[envelope.vote_envelope_id] = envelope
        return envelope

    def get(self, vote_envelope_id: UUID) -> VoteEnvelope | None:
        return self._envelopes.get(vote_envelope_id)

    def find_validated_for_credential(
        self, ballot_id: UUID, credential_proof: UUID
    ) -> VoteEnvelope | None:
        for envelope in self._envelopes.values():
            if (
                envelope.ballot_id == ballot_id
                and envelope.credential_proof == credential_proof
                and envelope.validation_status == VoteEnvelopeStatus.VALIDATED
            ):
                return envelope
        return None

    def list_for_ballot(self, ballot_id: UUID) -> tuple[VoteEnvelope, ...]:
        return tuple(e for e in self._envelopes.values() if e.ballot_id == ballot_id)


class VoteReceiptStore(Protocol):
    def save(self, receipt: VoteReceipt) -> VoteReceipt:
        """Idempotent create-or-update by `receipt_id`, same conflict-or-
        idempotent shape as `VoteEnvelopeStore.save`."""
        ...

    def get(self, receipt_id: UUID) -> VoteReceipt | None: ...

    def find_for_vote_envelope(self, vote_envelope_id: UUID) -> VoteReceipt | None: ...


class InMemoryVoteReceiptStore:
    def __init__(self) -> None:
        self._receipts: dict[UUID, VoteReceipt] = {}

    def save(self, receipt: VoteReceipt) -> VoteReceipt:
        existing = self._receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing == receipt:
                return existing
            raise VoteReceiptCreationConflictError(
                f"receipt_id {receipt.receipt_id} already exists with different content"
            )
        self._receipts[receipt.receipt_id] = receipt
        return receipt

    def get(self, receipt_id: UUID) -> VoteReceipt | None:
        return self._receipts.get(receipt_id)

    def find_for_vote_envelope(self, vote_envelope_id: UUID) -> VoteReceipt | None:
        for receipt in self._receipts.values():
            if receipt.vote_envelope_reference == vote_envelope_id:
                return receipt
        return None

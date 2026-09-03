"""CTRL-05 governed evidence sources and integrity verification.

CTRL-05 reads evidence; it never writes to the planes it reviews. Each source
adapter wraps exactly one accepted control plane and exposes a **read-only**
projection of that plane's own append-only evidence:

* `Ctrl02EvidenceSource` — `RegionalOperationsService.events` (intervention,
  privileged/JIT and break-glass acts);
* `Ctrl03EvidenceSource` — `CredentialLifecycleService.events` (credential,
  trust and key lifecycle acts);
* `Ctrl04EvidenceSource` — the Operations Console `EvidenceJournal` plus its
  composed `epd2.ctrl04.evidence.v1` action records.

Two properties are structural rather than promised:

**No write path.** A source adapter holds its plane behind a projection that
exposes only reading methods. There is no method on any adapter that mutates,
deletes or re-orders source evidence, and none that dispatches an operational
action. The absence is asserted behaviourally by the CTRL-05 gates, not only
by inspection.

**Independent integrity.** Each adapter re-derives the source record's own hash
using that plane's own algorithm from the record's own fields, and re-walks the
chain. A rewritten, re-ordered, truncated or unhashed record is reported as a
typed `IntegrityVerification` state — never silently as healthy evidence, and
never as an empty result.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from epd2_control_plane_service.domain import VOTING_DOMAIN_FORBIDDEN_FIELDS
from epd2_control_plane_service.operations_adapters import redact_metadata, scrub_text
from epd2_core.canonical_json import canonical_dumps

__all__ = [
    "PERSON_IDENTIFIER_FIELDS",
    "VOTING_OBJECT_CLASSES",
    "Ctrl02EvidenceSource",
    "Ctrl03EvidenceSource",
    "Ctrl04EvidenceSource",
    "EvidenceDomain",
    "EvidenceEnvelope",
    "EvidencePlane",
    "EvidenceReference",
    "EvidenceSource",
    "IntegrityState",
    "IntegrityVerification",
    "SourceUnavailable",
    "envelope_digest",
]


class EvidencePlane(StrEnum):
    CTRL02 = "CTRL-02"
    CTRL03 = "CTRL-03"
    CTRL04 = "CTRL-04"


class EvidenceDomain(StrEnum):
    GENERAL = "GENERAL"
    VOTING = "VOTING"


class IntegrityState(StrEnum):
    """Outcome of independently re-deriving a source record's integrity."""

    VERIFIED = "VERIFIED"
    HASH_MISMATCH = "HASH_MISMATCH"
    CHAIN_BROKEN = "CHAIN_BROKEN"
    SEQUENCE_BROKEN = "SEQUENCE_BROKEN"
    METADATA_MISSING = "METADATA_MISSING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    UNKNOWN_SCHEMA = "UNKNOWN_SCHEMA"


#: Verification outcomes that mean the record may be relied on as evidence.
TRUSTWORTHY_STATES = frozenset({IntegrityState.VERIFIED})

#: Field names that would create a cross-domain universal person index if they
#: were ever carried into an oversight envelope, correlation graph or export.
#: The voting-domain set is inherited from the accepted CTRL-01 domain model;
#: the rest are the generic person identifiers oversight must not accumulate.
PERSON_IDENTIFIER_FIELDS = frozenset(VOTING_DOMAIN_FORBIDDEN_FIELDS) | frozenset(
    {
        "person_id",
        "person_reference",
        "member_id",
        "member_number",
        "membership_id",
        "national_id",
        "tax_id",
        "social_security_number",
        "passport_number",
        "date_of_birth",
        "home_address",
        "email",
        "email_address",
        "phone",
        "phone_number",
        "universal_subject_id",
        "global_person_key",
    }
)


class SourceUnavailable(Exception):
    """A source plane could not be read. Never converted into empty evidence."""

    def __init__(self, plane: EvidencePlane, detail: str) -> None:
        super().__init__(f"{plane.value}: {detail}")
        self.plane = plane
        self.detail = detail


@dataclass(frozen=True, slots=True)
class IntegrityVerification:
    """Independently derived integrity status of one source record."""

    state: IntegrityState
    algorithm: str
    recorded_hash: str | None
    recomputed_hash: str | None
    previous_hash: str | None
    expected_previous_hash: str | None
    sequence: int | None
    detail: str = ""

    @property
    def trustworthy(self) -> bool:
        return self.state in TRUSTWORTHY_STATES


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Exact, immutable identity of one source record.

    A finding, attestation or export always names this reference, never a
    mutable projection of it. `content_digest` binds the exact normalized
    content the reviewer saw, so a later divergence is detectable.
    """

    plane: EvidencePlane
    stream_id: str
    event_id: str
    sequence: int
    event_hash: str
    content_digest: str

    @property
    def key(self) -> str:
        return f"{self.plane.value}:{self.stream_id}:{self.event_id}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "plane": self.plane.value,
            "stream_id": self.stream_id,
            "event_id": self.event_id,
            "sequence": self.sequence,
            "event_hash": self.event_hash,
            "content_digest": self.content_digest,
            "key": self.key,
        }


@dataclass(frozen=True, slots=True)
class EvidenceEnvelope:
    """A normalized, redacted, integrity-checked oversight view of one record.

    The envelope is a projection: it carries no authority to change anything,
    and its `attributes` have already been redacted and scrubbed at the source
    boundary so that no raw secret can reach a reviewer, an export or the
    oversight journal.
    """

    reference: EvidenceReference
    domain: EvidenceDomain
    scope_key: str
    occurred_at: str
    actor_ref: str
    authority_ref: str
    action_code: str
    object_ref: str
    result: str
    reason_code: str
    correlation_ref: str
    approval_refs: tuple[str, ...]
    attributes: Mapping[str, str]
    redacted_fields: tuple[str, ...]
    integrity: IntegrityVerification

    def as_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference.as_dict(),
            "domain": self.domain.value,
            "scope": self.scope_key,
            "occurred_at": self.occurred_at,
            "actor_ref": self.actor_ref,
            "authority_ref": self.authority_ref,
            "action_code": self.action_code,
            "object_ref": self.object_ref,
            "result": self.result,
            "reason_code": self.reason_code,
            "correlation_ref": self.correlation_ref,
            "approval_refs": list(self.approval_refs),
            "attributes": dict(self.attributes),
            "redacted_fields": list(self.redacted_fields),
            "integrity": {
                "state": self.integrity.state.value,
                "algorithm": self.integrity.algorithm,
                "recorded_hash": self.integrity.recorded_hash,
                "recomputed_hash": self.integrity.recomputed_hash,
                "sequence": self.integrity.sequence,
                "detail": self.integrity.detail,
                "trustworthy": self.integrity.trustworthy,
            },
        }


def envelope_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_dumps(dict(payload)).encode()).hexdigest()


def _screen_person_identifiers(attributes: Mapping[str, Any], where: str) -> None:
    """Refuse any attribute that would introduce a universal person index.

    This runs at the source boundary: an identifier that never enters an
    envelope cannot enter a correlation graph, an export or the journal.
    """
    for key in attributes:
        if key.lower() in PERSON_IDENTIFIER_FIELDS:
            raise SourceUnavailable(
                EvidencePlane.CTRL04,
                f"{where}: attribute {key!r} would create a cross-domain person identifier",
            )


def _safe_attributes(raw: Mapping[str, Any], where: str) -> tuple[dict[str, str], tuple[str, ...]]:
    _screen_person_identifiers(raw, where)
    clean, redacted = redact_metadata(raw)
    return {k: scrub_text(v) for k, v in clean.items()}, tuple(redacted)


#: CTRL-03 object classes that are voting-domain by construction.
VOTING_OBJECT_CLASSES: frozenset[str] = frozenset({"VOTING_KEY_REFERENCE"})


def _domain_of(voting_refs: frozenset[str], *candidates: Any) -> EvidenceDomain:
    """Classify one record's domain from the facts its own plane recorded.

    A record is voting-domain when it names an object the owning plane has
    declared to be voting-domain, or when its object class is voting-domain by
    construction. Nothing here infers the domain from a name.
    """
    for candidate in candidates:
        if candidate is None:
            continue
        value = str(candidate)
        if value in voting_refs or value in VOTING_OBJECT_CLASSES:
            return EvidenceDomain.VOTING
    return EvidenceDomain.GENERAL


def _read_events(service: Any, plane: EvidencePlane, detail: str) -> Sequence[Any]:
    """Read a plane's own append-only event sequence, whether it is exposed as
    a property or as a method. Nothing here can write to the plane."""
    try:
        accessor = service.events
        events = accessor() if callable(accessor) else accessor
        return tuple(events)
    except SourceUnavailable:
        raise
    except Exception as exc:
        raise SourceUnavailable(plane, f"{type(exc).__name__}") from exc


class EvidenceSource(Protocol):
    """Read-only projection of one accepted control plane's evidence."""

    plane: EvidencePlane
    available: bool

    def stream_id(self) -> str: ...

    def envelopes(self) -> tuple[EvidenceEnvelope, ...]: ...


@dataclass(slots=True)
class _ChainWalk:
    """State carried while re-walking one source chain."""

    previous_hash: str = "GENESIS"
    expected_sequence: int = 1
    broken: bool = False


class _HashChainSource:
    """Shared re-derivation for the CTRL-02/CTRL-03 payload-hash chains.

    Both planes hash a canonical JSON payload that includes the previous hash
    and the sequence. CTRL-05 rebuilds that payload from the record's own
    fields and compares; it never asks the plane whether it is intact.
    """

    plane: EvidencePlane
    algorithm = "sha256(json.dumps(payload,sort_keys,separators))"

    def _verify(
        self, payload: Mapping[str, Any], recorded_hash: str, walk: _ChainWalk, sequence: int
    ) -> IntegrityVerification:
        encoded = json.dumps(dict(payload), sort_keys=True, default=str, separators=(",", ":"))
        recomputed = hashlib.sha256(encoded.encode()).hexdigest()
        recorded_previous = str(payload.get("previous_hash", ""))
        if not recorded_hash or not recorded_previous:
            walk.broken = True
            return IntegrityVerification(
                IntegrityState.METADATA_MISSING,
                self.algorithm,
                recorded_hash or None,
                recomputed,
                recorded_previous or None,
                walk.previous_hash,
                sequence,
                "record carries no hash or no chain link",
            )
        if sequence != walk.expected_sequence:
            walk.broken = True
            return IntegrityVerification(
                IntegrityState.SEQUENCE_BROKEN,
                self.algorithm,
                recorded_hash,
                recomputed,
                recorded_previous,
                walk.previous_hash,
                sequence,
                f"expected sequence {walk.expected_sequence}",
            )
        if recorded_previous != walk.previous_hash:
            walk.broken = True
            return IntegrityVerification(
                IntegrityState.CHAIN_BROKEN,
                self.algorithm,
                recorded_hash,
                recomputed,
                recorded_previous,
                walk.previous_hash,
                sequence,
                "previous-hash link does not match the preceding record",
            )
        if recomputed != recorded_hash:
            walk.broken = True
            return IntegrityVerification(
                IntegrityState.HASH_MISMATCH,
                self.algorithm,
                recorded_hash,
                recomputed,
                recorded_previous,
                walk.previous_hash,
                sequence,
                "record content does not reproduce its recorded hash",
            )
        walk.previous_hash = recorded_hash
        walk.expected_sequence = sequence + 1
        return IntegrityVerification(
            IntegrityState.VERIFIED,
            self.algorithm,
            recorded_hash,
            recomputed,
            recorded_previous,
            recorded_previous,
            sequence,
        )


class Ctrl02EvidenceSource(_HashChainSource):
    """Read-only projection of CTRL-02 regional intervention evidence."""

    plane = EvidencePlane.CTRL02

    def __init__(
        self,
        service: Any,
        stream: str = "ctrl02-regional-operations",
        voting_domain_refs: Iterable[str] = (),
    ) -> None:
        self._service = service
        self._stream = stream
        #: The governed set of object references that belong to the voting
        #: domain. It is *declared* by the plane that owns the fact, never
        #: guessed from a name: an envelope is voting-domain only if its own
        #: plane says so, and CTRL-05 then refuses to show it at all.
        self._voting_refs = frozenset(voting_domain_refs)
        self.available = True

    def stream_id(self) -> str:
        return self._stream

    def _events(self) -> Sequence[Any]:
        if not self.available:
            raise SourceUnavailable(self.plane, "regional operations evidence is unavailable")
        return _read_events(self._service, self.plane, "regional operations")

    def envelopes(self) -> tuple[EvidenceEnvelope, ...]:
        walk = _ChainWalk()
        out: list[EvidenceEnvelope] = []
        for event in self._events():
            payload = {
                "sequence": event.sequence,
                "actor_id": event.actor_id,
                "authority_basis": event.authority_basis,
                "action": event.action,
                "target": event.target,
                "scope": event.scope,
                "occurred_at": event.occurred_at,
                "result": event.result,
                "reason": event.reason,
                "approval_refs": tuple(event.approval_refs),
                "prior_state_ref": event.prior_state_ref,
                "new_state_ref": event.new_state_ref,
                "correlation_ref": event.correlation_ref,
                "previous_hash": event.previous_hash,
            }
            integrity = self._verify(payload, event.event_hash, walk, event.sequence)
            attributes, redacted = _safe_attributes(
                {
                    "prior_state_ref": event.prior_state_ref,
                    "new_state_ref": event.new_state_ref,
                    "reason": event.reason,
                },
                "CTRL-02 evidence",
            )
            reference = EvidenceReference(
                self.plane,
                self._stream,
                event.event_id,
                event.sequence,
                event.event_hash,
                envelope_digest(payload),
            )
            out.append(
                EvidenceEnvelope(
                    reference=reference,
                    domain=_domain_of(self._voting_refs, event.target, event.scope),
                    scope_key=event.scope,
                    occurred_at=event.occurred_at,
                    actor_ref=event.actor_id,
                    authority_ref=event.authority_basis,
                    action_code=event.action,
                    object_ref=event.target,
                    result=event.result,
                    reason_code=event.reason,
                    correlation_ref=event.correlation_ref,
                    approval_refs=tuple(event.approval_refs),
                    attributes=attributes,
                    redacted_fields=redacted,
                    integrity=integrity,
                )
            )
        return tuple(out)


class Ctrl03EvidenceSource(_HashChainSource):
    """Read-only projection of CTRL-03 credential/trust/key lifecycle evidence."""

    plane = EvidencePlane.CTRL03

    def __init__(
        self,
        service: Any,
        stream: str = "ctrl03-credential-lifecycle",
        voting_domain_refs: Iterable[str] = (),
    ) -> None:
        self._service = service
        self._stream = stream
        self._voting_refs = frozenset(voting_domain_refs)
        self.available = True

    def stream_id(self) -> str:
        return self._stream

    def _events(self) -> Sequence[Any]:
        if not self.available:
            raise SourceUnavailable(self.plane, "credential lifecycle evidence is unavailable")
        return _read_events(self._service, self.plane, "credential lifecycle")

    def envelopes(self) -> tuple[EvidenceEnvelope, ...]:
        walk = _ChainWalk()
        out: list[EvidenceEnvelope] = []
        for event in self._events():
            payload = {
                "sequence": event.sequence,
                "actor_id": event.actor_id,
                "authority_basis": event.authority_basis,
                "object_class": event.object_class,
                "target_ref": event.target_ref,
                "action": event.action,
                "prior_state": event.prior_state,
                "new_state": event.new_state,
                "occurred_at": event.occurred_at,
                "result": event.result,
                "reason": event.reason,
                "approval_refs": tuple(event.approval_refs),
                "provider_ref": event.provider_ref,
                "trust_version": event.trust_version,
                "evidence_correlation": event.evidence_correlation,
                "previous_hash": event.previous_hash,
            }
            integrity = self._verify(payload, event.event_hash, walk, event.sequence)
            # Credential/key lifecycle metadata is reference-only by CTRL-03
            # contract; CTRL-05 redacts again at its own boundary rather than
            # trusting the upstream classification.
            attributes, redacted = _safe_attributes(
                {
                    "object_class": event.object_class,
                    "prior_state": event.prior_state,
                    "new_state": event.new_state,
                    "provider_ref": event.provider_ref or "NONE",
                    "trust_version": event.trust_version,
                    "reason": event.reason,
                },
                "CTRL-03 evidence",
            )
            reference = EvidenceReference(
                self.plane,
                self._stream,
                event.event_id,
                event.sequence,
                event.event_hash,
                envelope_digest(payload),
            )
            out.append(
                EvidenceEnvelope(
                    reference=reference,
                    domain=_domain_of(
                        self._voting_refs,
                        event.target_ref,
                        getattr(event, "object_class", None),
                    ),
                    scope_key=str(getattr(event, "scope", "")) or "UNSCOPED",
                    occurred_at=event.occurred_at,
                    actor_ref=event.actor_id,
                    authority_ref=event.authority_basis,
                    action_code=event.action,
                    object_ref=event.target_ref,
                    result=event.result,
                    reason_code=event.reason,
                    correlation_ref=event.evidence_correlation,
                    approval_refs=tuple(event.approval_refs),
                    attributes=attributes,
                    redacted_fields=redacted,
                    integrity=integrity,
                )
            )
        return tuple(out)


class Ctrl04EvidenceSource:
    """Read-only projection of the CTRL-04 Operations Console journal.

    The adapter holds the console service but exposes only reading methods.
    It re-derives each record's hash through the accepted CTRL-01 journal
    algorithm (`ControlEvidenceEvent.compute_hash`) rather than asking the
    journal to verify itself, and it re-walks the chain independently.
    """

    plane = EvidencePlane.CTRL04
    algorithm = "sha256(canonical_json(hashable)+previous_hash)"

    def __init__(
        self,
        service: Any,
        stream: str = "ctrl04-operations-console",
        voting_domain_refs: Iterable[str] = (),
    ) -> None:
        self._service = service
        self._stream = stream
        self._voting_refs = frozenset(voting_domain_refs)
        self.available = True

    def stream_id(self) -> str:
        return self._stream

    def _records(self) -> Sequence[Any]:
        if not self.available:
            raise SourceUnavailable(self.plane, "operations console evidence is unavailable")
        try:
            return tuple(self._service.journal.records())
        except Exception as exc:
            raise SourceUnavailable(self.plane, f"{type(exc).__name__}") from exc

    def action_record(self, action_id: str) -> dict[str, Any] | None:
        """The composed `epd2.ctrl04.evidence.v1` record, redacted again here."""
        if not self.available:
            raise SourceUnavailable(self.plane, "operations console evidence is unavailable")
        try:
            record = self._service.evidence_record(action_id)
        except Exception:
            return None
        text = scrub_text(json.dumps(record))
        loaded: dict[str, Any] = json.loads(text)
        return loaded

    def envelopes(self) -> tuple[EvidenceEnvelope, ...]:
        previous = "0" * 64
        expected_sequence = 1
        out: list[EvidenceEnvelope] = []
        for record in self._records():
            recomputed = record.compute_hash()
            if not record.event_hash:
                integrity = IntegrityVerification(
                    IntegrityState.METADATA_MISSING,
                    self.algorithm,
                    None,
                    recomputed,
                    record.previous_event_hash,
                    previous,
                    record.sequence,
                    "journal record carries no hash",
                )
            elif record.sequence != expected_sequence:
                integrity = IntegrityVerification(
                    IntegrityState.SEQUENCE_BROKEN,
                    self.algorithm,
                    record.event_hash,
                    recomputed,
                    record.previous_event_hash,
                    previous,
                    record.sequence,
                    f"expected sequence {expected_sequence}",
                )
            elif record.previous_event_hash != previous:
                integrity = IntegrityVerification(
                    IntegrityState.CHAIN_BROKEN,
                    self.algorithm,
                    record.event_hash,
                    recomputed,
                    record.previous_event_hash,
                    previous,
                    record.sequence,
                    "previous-hash link does not match the preceding record",
                )
            elif recomputed != record.event_hash:
                integrity = IntegrityVerification(
                    IntegrityState.HASH_MISMATCH,
                    self.algorithm,
                    record.event_hash,
                    recomputed,
                    record.previous_event_hash,
                    previous,
                    record.sequence,
                    "record content does not reproduce its recorded hash",
                )
            else:
                integrity = IntegrityVerification(
                    IntegrityState.VERIFIED,
                    self.algorithm,
                    record.event_hash,
                    recomputed,
                    record.previous_event_hash,
                    previous,
                    record.sequence,
                )
                previous = record.event_hash
                expected_sequence = record.sequence + 1
            attributes, redacted = _safe_attributes(dict(record.attributes), "CTRL-04 evidence")
            reference = EvidenceReference(
                self.plane,
                self._stream,
                f"ctrl04-event-{record.sequence:08d}",
                record.sequence,
                record.event_hash,
                envelope_digest(record.hashable()),
            )
            out.append(
                EvidenceEnvelope(
                    reference=reference,
                    domain=_domain_of(self._voting_refs, record.object_ref),
                    scope_key=record.scope_key,
                    occurred_at=record.occurred_at.isoformat(),
                    actor_ref=record.actor_ref,
                    authority_ref=record.authority_basis,
                    action_code=record.action_id,
                    object_ref=record.object_ref,
                    result=record.result,
                    reason_code=record.reason_code,
                    correlation_ref=record.correlation_ref,
                    approval_refs=tuple(record.approval_refs),
                    attributes=attributes,
                    redacted_fields=redacted,
                    integrity=integrity,
                )
            )
        return tuple(out)


@dataclass(frozen=True, slots=True)
class VotingVerificationReference:
    """The only voting-domain surface CTRL-05 may name.

    It is a governed *verification interface* reference: a public bulletin or
    verifier endpoint identity and its published digest. It carries no
    voting-internal identity, no ballot, no member reference and no control
    path — and CTRL-05 offers no method that reaches inside the voting domain.
    """

    interface_id: str
    published_digest: str
    verification_status: str
    published_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "interface_id": self.interface_id,
            "published_digest": self.published_digest,
            "verification_status": self.verification_status,
            "published_at": self.published_at,
            "voting_internal_access": "NONE",
            "control_path": "NONE",
        }


class VotingVerificationSource:
    """External, reference-only voting verification status.

    Registration screens every field: anything resembling a persistent member
    or person identifier is refused at the boundary, so the oversight console
    cannot come to hold one even if an upstream system offered it.
    """

    plane = EvidencePlane.CTRL04  # not an oversight evidence plane; reference only

    def __init__(self) -> None:
        self.available = True
        self._references: dict[str, VotingVerificationReference] = {}

    def register(self, reference: VotingVerificationReference) -> None:
        payload = reference.as_dict()
        for key, value in payload.items():
            if key.lower() in PERSON_IDENTIFIER_FIELDS:
                raise SourceUnavailable(
                    EvidencePlane.CTRL04, f"voting reference field {key!r} is forbidden"
                )
            if isinstance(value, str) and any(
                marker in value.lower() for marker in ("voter_id", "member_id", "person_id")
            ):
                raise SourceUnavailable(
                    EvidencePlane.CTRL04, "voting reference value carries an identity reference"
                )
        self._references[reference.interface_id] = reference

    def references(self) -> tuple[VotingVerificationReference, ...]:
        if not self.available:
            raise SourceUnavailable(EvidencePlane.CTRL04, "voting verification interface offline")
        return tuple(self._references.values())


def collect(
    sources: Iterable[EvidenceSource],
) -> tuple[tuple[EvidenceEnvelope, ...], dict[str, str]]:
    """Read every source, recording unavailability rather than hiding it.

    Returns the envelopes that could be read and a map of plane to failure
    reason for those that could not. An unavailable plane is never reported as
    an empty result set.
    """
    envelopes: list[EvidenceEnvelope] = []
    unavailable: dict[str, str] = {}
    for source in sources:
        try:
            envelopes.extend(source.envelopes())
        except SourceUnavailable as exc:
            unavailable[source.plane.value] = exc.detail
    return tuple(envelopes), unavailable

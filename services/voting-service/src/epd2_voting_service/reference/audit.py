"""Reference audit evidence (PACK-16D §47).

Audit evidence is a hash-chained append-only sequence. Each record carries
a class, a reason code, a coarse time bucket and an election context — and
nothing that could join a capability to a ballot. The chain makes silent
deletion detectable; it does not make deletion impossible, and it is not a
substitute for the bulletin board.

The record type list is closed. Adding a class means adding a decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h
from epd2_voting_service.reference.logging_boundary import FORBIDDEN_LOG_FIELDS


class AuditRecordType(StrEnum):
    PARAMETER_VALIDATION = "parameter_validation"
    PROOF_VALIDATION = "proof_validation"
    ATOMIC_ACCEPTANCE = "atomic_acceptance"
    ATOMIC_CHALLENGE = "atomic_challenge"
    RESERVATION = "reservation"
    PUBLICATION_OBLIGATION = "publication_obligation"
    BOARD_APPEND = "board_append"
    CHECKPOINT = "checkpoint"
    CLOSURE = "closure"
    VERIFICATION = "verification"


class AuditFieldRejected(RuntimeError):
    """An audit record carried a field that would breach privacy."""

    reason_code = "AUDIT_FIELD_REJECTED"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    sequence: int
    record_type: AuditRecordType
    reason_code: str
    election_context_id: str
    coarse_time_bucket: str
    outcome: str
    previous_hash: bytes

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("sequence", encode_uint(self.sequence, 8)),
                ("record_type", encode_text(self.record_type.value)),
                ("reason_code", encode_text(self.reason_code)),
                ("election_context_id", encode_text(self.election_context_id)),
                ("coarse_time_bucket", encode_text(self.coarse_time_bucket)),
                ("outcome", encode_text(self.outcome)),
                ("previous_hash", encode_bytes(self.previous_hash)),
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.AUDIT_RECORD, [self.canonical_bytes()])


@dataclass
class AuditLog:
    """Tamper-evident, privacy-minimised, append-only.

    Role restriction and retention are governance properties enforced
    outside this class; they are named in the PACK-16D logging and audit
    boundary document and are **not** implemented here.
    """

    records: list[AuditRecord] = field(default_factory=list)

    def append(
        self,
        record_type: AuditRecordType,
        *,
        reason_code: str,
        election_context_id: str,
        coarse_time_bucket: str,
        outcome: str,
        **rejected: object,
    ) -> AuditRecord:
        if rejected:
            offending = sorted(rejected)
            forbidden = [n for n in offending if n.lower() in FORBIDDEN_LOG_FIELDS]
            raise AuditFieldRejected(
                f"audit records accept no additional fields; got {offending} "
                f"(forbidden: {forbidden})"
            )
        previous = self.records[-1].digest() if self.records else b"\x00" * 32
        record = AuditRecord(
            sequence=len(self.records),
            record_type=record_type,
            reason_code=reason_code,
            election_context_id=election_context_id,
            coarse_time_bucket=coarse_time_bucket,
            outcome=outcome,
            previous_hash=previous,
        )
        self.records.append(record)
        return record

    def verify_chain(self) -> bool:
        previous = b"\x00" * 32
        for index, record in enumerate(self.records):
            if record.sequence != index or record.previous_hash != previous:
                return False
            previous = record.digest()
        return True

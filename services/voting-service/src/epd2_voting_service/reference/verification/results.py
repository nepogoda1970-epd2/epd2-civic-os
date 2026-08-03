"""Machine-readable verification outcomes and stable exit codes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class VerificationResultCode(StrEnum):
    VERIFIED = "VERIFIED"
    VERIFIED_WITH_WARNINGS = "VERIFIED_WITH_WARNINGS"
    INCOMPLETE_RECORD = "INCOMPLETE_RECORD"
    UNSUPPORTED_PROFILE = "UNSUPPORTED_PROFILE"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_CANONICAL_ENCODING = "INVALID_CANONICAL_ENCODING"
    INVALID_MANIFEST = "INVALID_MANIFEST"
    INVALID_PARAMETER_SET = "INVALID_PARAMETER_SET"
    INVALID_CEREMONY = "INVALID_CEREMONY"
    INVALID_BALLOT_PROOF = "INVALID_BALLOT_PROOF"
    INVALID_CHALLENGE_OPENING = "INVALID_CHALLENGE_OPENING"
    BOARD_INCONSISTENCY = "BOARD_INCONSISTENCY"
    BATCH_ROOT_MISMATCH = "BATCH_ROOT_MISMATCH"
    BATCH_RECONCILIATION_FAILED = "BATCH_RECONCILIATION_FAILED"
    BATCH_INCLUSION_FAILED = "BATCH_INCLUSION_FAILED"
    BATCH_CONSISTENCY_FAILED = "BATCH_CONSISTENCY_FAILED"
    BOARD_SIGNATURE_MISSING = "BOARD_SIGNATURE_MISSING"
    BOARD_SIGNER_UNKNOWN = "BOARD_SIGNER_UNKNOWN"
    BOARD_SIGNER_UNAUTHORIZED = "BOARD_SIGNER_UNAUTHORIZED"
    BOARD_SIGNATURE_INVALID = "BOARD_SIGNATURE_INVALID"
    BOARD_SIGNATURE_CONTEXT_MISMATCH = "BOARD_SIGNATURE_CONTEXT_MISMATCH"
    INVALID_CEREMONY_TRANSCRIPT = "INVALID_CEREMONY_TRANSCRIPT"
    GUARDIAN_QUORUM_MISMATCH = "GUARDIAN_QUORUM_MISMATCH"
    INVALID_DECRYPTION_SHARE = "INVALID_DECRYPTION_SHARE"
    TALLY_MISMATCH = "TALLY_MISMATCH"
    ARCHIVE_CORRUPTION = "ARCHIVE_CORRUPTION"


#: Stable, documented exit codes. Never renumbered.
EXIT_CODES: dict[VerificationResultCode, int] = {
    VerificationResultCode.VERIFIED: 0,
    VerificationResultCode.VERIFIED_WITH_WARNINGS: 1,
    VerificationResultCode.INCOMPLETE_RECORD: 10,
    VerificationResultCode.UNSUPPORTED_PROFILE: 11,
    VerificationResultCode.INVALID_SCHEMA: 12,
    VerificationResultCode.INVALID_CANONICAL_ENCODING: 13,
    VerificationResultCode.INVALID_MANIFEST: 20,
    VerificationResultCode.INVALID_PARAMETER_SET: 21,
    VerificationResultCode.INVALID_CEREMONY: 22,
    VerificationResultCode.INVALID_BALLOT_PROOF: 30,
    VerificationResultCode.INVALID_CHALLENGE_OPENING: 31,
    VerificationResultCode.BOARD_INCONSISTENCY: 40,
    VerificationResultCode.BATCH_ROOT_MISMATCH: 41,
    VerificationResultCode.BATCH_RECONCILIATION_FAILED: 42,
    VerificationResultCode.BATCH_INCLUSION_FAILED: 43,
    VerificationResultCode.BATCH_CONSISTENCY_FAILED: 44,
    VerificationResultCode.BOARD_SIGNATURE_MISSING: 45,
    VerificationResultCode.BOARD_SIGNER_UNKNOWN: 46,
    VerificationResultCode.BOARD_SIGNER_UNAUTHORIZED: 47,
    VerificationResultCode.BOARD_SIGNATURE_INVALID: 48,
    VerificationResultCode.BOARD_SIGNATURE_CONTEXT_MISMATCH: 49,
    VerificationResultCode.INVALID_CEREMONY_TRANSCRIPT: 23,
    VerificationResultCode.GUARDIAN_QUORUM_MISMATCH: 24,
    VerificationResultCode.INVALID_DECRYPTION_SHARE: 50,
    VerificationResultCode.TALLY_MISMATCH: 51,
    VerificationResultCode.ARCHIVE_CORRUPTION: 60,
}

#: What a `VERIFIED` result did **not** check. Printed every time (`IV-11`).
NOT_CHECKED: tuple[str, ...] = (
    "that a device encrypted the choice its voter intended",
    "that every published ballot came from a distinct real entitlement",
    "that nobody was coerced",
    "that no eligible person was prevented from voting",
    "that guardian key shares were handled correctly after the ceremony",
    "that the parameters are appropriate - VO-08 is OPEN",
    "the per-capability entitlement bound, which is Auditor-restricted evidence",
    "that the authorised signer set itself is the right one - the verifier "
    "checks a checkpoint against the signer registry it was given, and cannot "
    "tell you that registry was authorised by the Election Board",
    "that the board showed the same checkpoints to everyone - a valid "
    "signature proves who issued a checkpoint, never that no other view "
    "exists; cross-mirror comparison remains unimplemented",
)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    code: VerificationResultCode
    detail: str = ""
    checks_run: tuple[str, ...] = field(default=())
    warnings: tuple[str, ...] = field(default=())

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.code]

    @property
    def not_checked(self) -> tuple[str, ...]:
        return NOT_CHECKED

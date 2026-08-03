"""Central domain-separation registry (PACK-16B `DS-*`, PACK-16D §13).

Every hash and HMAC input in the reference implementation is prefixed with
exactly one label drawn from this registry. Ad-hoc string literals in
cryptographic code are prohibited: `require_label` is the only way to
obtain a label, and it raises on anything not registered here.
"""

from __future__ import annotations

from enum import StrEnum


class DomainLabel(StrEnum):
    """Stable, versioned, unique domain-separation labels.

    The value is the wire label. Values are **append-only**: changing one
    changes every digest derived under it and is a new profile version,
    not an edit.
    """

    PARAMETER_SET = "EPD2/v1/parameter_set"
    ELECTION_CONTEXT = "EPD2/v1/election_context"
    MANIFEST = "EPD2/v1/manifest"
    GUARDIAN_COMMITMENT = "EPD2/v1/guardian_commitment"
    GUARDIAN_PROOF = "EPD2/v1/guardian_proof"
    JOINT_PUBLIC_KEY = "EPD2/v1/joint_public_key"
    BALLOT_NONCE = "EPD2/v1/ballot_nonce"
    SELECTION_ENCRYPTION = "EPD2/v1/selection_encryption"
    SELECTION_PROOF = "EPD2/v1/selection_proof"
    CONTEST_PROOF = "EPD2/v1/contest_proof"
    BALLOT_HASH = "EPD2/v1/ballot_hash"
    CONFIRMATION_CODE = "EPD2/v1/confirmation_code"
    CHALLENGE_OPENING = "EPD2/v1/challenge_opening"
    CAST_BALLOT = "EPD2/v1/cast_ballot"
    SPOILED_BALLOT = "EPD2/v1/spoiled_ballot"
    BATCH_LEAF = "EPD2/v1/batch_leaf"
    BATCH_COVER_LEAF = "EPD2/v1/batch_cover_leaf"
    BATCH_ROOT = "EPD2/v1/batch_root"
    BOARD_ENTRY = "EPD2/v1/board_entry"
    BOARD_CHECKPOINT = "EPD2/v1/board_checkpoint"
    ELECTION_RECORD = "EPD2/v1/election_record"
    DECRYPTION_SHARE = "EPD2/v1/decryption_share"
    TALLY = "EPD2/v1/tally"
    VERIFICATION_RESULT = "EPD2/v1/verification_result"
    AUDIT_RECORD = "EPD2/v1/audit_record"
    CEREMONY_TRANSCRIPT = "EPD2/v1/ceremony_transcript"
    BOARD_SIGNATURE = "EPD2/v1/board_signature"


REGISTRY_VERSION = "EPD2-DS-1"

#: Labels that are registered but have **no call site** in this round.
#:
#: A registry that lists a label nothing uses is making a claim it does not
#: back, so the unused ones are named here and asserted by test rather than
#: left for a reader to discover. ``BATCH_COVER_LEAF`` is unused by design:
#: a cover leaf is uniform random bytes and is never hashed, so there is
#: nothing for the label to separate. The other eight are reserved for
#: artefacts this round does not hash under their own label.
#:
#: This set shrank by two in the correction round: ``GUARDIAN_COMMITMENT``
#: and ``GUARDIAN_PROOF`` acquired real call sites when the threshold
#: ceremony arrived, and a label that is in use must not stay on a list of
#: labels that are not.
RESERVED_WITHOUT_CALL_SITE: frozenset[str] = frozenset(
    {
        DomainLabel.BALLOT_NONCE.value,
        DomainLabel.CHALLENGE_OPENING.value,
        DomainLabel.BATCH_COVER_LEAF.value,
        DomainLabel.ELECTION_CONTEXT.value,
        DomainLabel.JOINT_PUBLIC_KEY.value,
        DomainLabel.SELECTION_ENCRYPTION.value,
        DomainLabel.CAST_BALLOT.value,
        DomainLabel.SPOILED_BALLOT.value,
        DomainLabel.VERIFICATION_RESULT.value,
    }
)

_ALL: frozenset[str] = frozenset(label.value for label in DomainLabel)


class UnregisteredDomainLabelError(ValueError):
    """An ad-hoc domain label was used. Prohibited by PACK-16D §13."""

    reason_code = "VALIDATION_FORBIDDEN_TRANSITION"


def require_label(label: str | DomainLabel) -> str:
    """Return the wire form of a registered label, or fail closed."""
    value = label.value if isinstance(label, DomainLabel) else label
    if value not in _ALL:
        raise UnregisteredDomainLabelError(
            f"domain label {value!r} is not in the PACK-16D domain-separation registry"
        )
    return value


def all_labels() -> tuple[str, ...]:
    """Every registered label, in declaration order."""
    return tuple(label.value for label in DomainLabel)

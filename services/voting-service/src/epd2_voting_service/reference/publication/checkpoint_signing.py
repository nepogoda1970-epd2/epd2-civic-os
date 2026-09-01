"""Checkpoint signature profile and signer trust model.

The first PACK-16D candidate signed checkpoints with a symmetric HMAC key
and the verifier never checked the result, because a third party does not
hold that key. A signature nobody can verify is not authenticity; it is
decoration. This module replaces it.

**Profile.** Ed25519 (RFC 8032, PureEdDSA over edwards25519 with SHA-512),
supplied by a **vetted library** through `crypto.signature_provider` — not
implemented here. Public keys are the standard 32-byte raw encoding,
signatures the standard 64 bytes; both lengths are checked exactly, so a
near-miss is a malformed input rather than an alternative encoding. The
provider rejects a non-canonical scalar, so a signature is not malleable
into a different encoding of itself.

An earlier candidate implemented the curve arithmetic in this repository
and an audit failed it. The replacement is not a smaller version of the
same idea: there is **no fallback**. If the provider is absent the import
raises and the process does not start, because the machine without the
dependency is precisely the machine you would least want running
hand-rolled cryptography.

**Trust anchor.** A verifier must not accept a key that arrives inside the
artefact it is checking, because then anyone can mint their own board. The
authorised signer set is therefore part of the **election context**, fixed
before the first checkpoint, and the checkpoint carries only a *key
identifier* that must resolve inside that set. `SignerRegistry` is that
set; `verify_checkpoint` refuses an identifier it cannot resolve, and there
is no path that reads a key out of the checkpoint being verified.

**What a valid signature does and does not prove.** It proves the named
authorised signer issued this checkpoint. It does **not** prove the board
showed the same checkpoint to everyone: two correctly signed checkpoints
can still conflict, and detecting that is what the consistency proof and
mirror comparison are for. The two properties are kept apart deliberately
here and in the verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from epd2_voting_service.reference.crypto import signature_provider
from epd2_voting_service.reference.crypto.domain_separation import DomainLabel
from epd2_voting_service.reference.crypto.encoding import (
    encode_bytes,
    encode_struct,
    encode_text,
    encode_uint,
)
from epd2_voting_service.reference.crypto.hashing import ZERO_KEY, h

#: Bound into every signed payload, so a signature made under one profile
#: cannot be replayed as one made under another.
CHECKPOINT_SCHEMA_VERSION: str = "EPD2-CHECKPOINT-2"
SIGNATURE_PROFILE: str = signature_provider.SIGNATURE_PROFILE


class CheckpointSignatureOutcome(StrEnum):
    """Machine-readable outcomes. Every failure is one of these."""

    VALID = "BOARD_SIGNATURE_VALID"
    MISSING = "BOARD_SIGNATURE_MISSING"
    SIGNER_UNKNOWN = "BOARD_SIGNER_UNKNOWN"
    SIGNER_UNAUTHORIZED = "BOARD_SIGNER_UNAUTHORIZED"
    INVALID = "BOARD_SIGNATURE_INVALID"
    CONTEXT_MISMATCH = "BOARD_SIGNATURE_CONTEXT_MISMATCH"


class CheckpointSigningError(RuntimeError):
    reason_code = "BOARD_SIGNATURE_INVALID"


@dataclass(frozen=True, slots=True)
class SignerRecord:
    """One authorised board signer, as declared in the election context."""

    signing_key_id: str
    public_key: bytes
    board_id: str
    election_context_id: str
    key_version: int = 1
    #: Inclusive checkpoint-sequence window this key may sign in. A key
    #: rotation is expressed by ending one window and beginning the next,
    #: both declared in advance rather than announced by the key itself.
    active_from_sequence: int = 0
    active_to_sequence: int | None = None
    superseded_by: str | None = None

    def is_active_at(self, checkpoint_sequence: int) -> bool:
        if checkpoint_sequence < self.active_from_sequence:
            return False
        if self.active_to_sequence is None:
            return True
        return checkpoint_sequence <= self.active_to_sequence

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("signing_key_id", encode_text(self.signing_key_id)),
                ("public_key", encode_bytes(self.public_key)),
                ("board_id", encode_text(self.board_id)),
                ("election_context_id", encode_text(self.election_context_id)),
                ("key_version", encode_uint(self.key_version, 4)),
                ("active_from_sequence", encode_uint(self.active_from_sequence, 8)),
                (
                    "active_to_sequence",
                    encode_uint(
                        self.active_to_sequence + 1 if self.active_to_sequence is not None else 0,
                        8,
                    ),
                ),
                ("superseded_by", encode_text(self.superseded_by or "")),
            ]
        )


@dataclass(frozen=True, slots=True)
class SignerRegistry:
    """The trust anchor: who may sign this election's board, declared up front.

    A verifier is given this registry alongside the export. It is *not*
    read out of the checkpoints, and no method here can add a signer.
    """

    election_context_id: str
    board_id: str
    signers: tuple[SignerRecord, ...]

    def resolve(self, signing_key_id: str) -> SignerRecord | None:
        for record in self.signers:
            if record.signing_key_id == signing_key_id:
                return record
        return None

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("election_context_id", encode_text(self.election_context_id)),
                ("board_id", encode_text(self.board_id)),
                *[
                    (f"signer_{index}", record.canonical_bytes())
                    for index, record in enumerate(self.signers)
                ],
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.BOARD_SIGNATURE, [self.canonical_bytes()])


@dataclass(frozen=True, slots=True)
class CheckpointPayload:
    """Exactly what a signature covers. Nothing outside this is bound."""

    protocol_profile_id: str
    election_context_id: str
    board_id: str
    checkpoint_sequence: int
    tree_size: int
    root: bytes
    previous_checkpoint_hash: bytes
    publication_phase: str
    signing_key_id: str
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def canonical_bytes(self) -> bytes:
        """Canonical binary tuple encoding — never non-canonical JSON.

        Every field a replay could vary is inside: the profile, the
        election, the board, the sequence, the size, the root, the chain
        link, the phase, the schema and the key id.
        """
        return encode_struct(
            [
                ("schema_version", encode_text(self.schema_version)),
                ("protocol_profile_id", encode_text(self.protocol_profile_id)),
                ("election_context_id", encode_text(self.election_context_id)),
                ("board_id", encode_text(self.board_id)),
                ("checkpoint_sequence", encode_uint(self.checkpoint_sequence, 8)),
                ("tree_size", encode_uint(self.tree_size, 8)),
                ("root", encode_bytes(self.root)),
                ("previous_checkpoint_hash", encode_bytes(self.previous_checkpoint_hash)),
                ("publication_phase", encode_text(self.publication_phase)),
                ("signing_key_id", encode_text(self.signing_key_id)),
            ]
        )

    def signing_input(self) -> bytes:
        """Domain-separated signing input.

        The label prevents a signature over some other EPD2 structure from
        ever being presented as a checkpoint signature.
        """
        return h(ZERO_KEY, DomainLabel.BOARD_CHECKPOINT, [self.canonical_bytes()])


def sign_checkpoint(payload: CheckpointPayload, signing_seed: bytes) -> bytes:
    """Produce a checkpoint signature. The key is TEST-ONLY in fixtures."""
    if len(signing_seed) != signature_provider.PRIVATE_KEY_BYTES:
        raise CheckpointSigningError(
            f"signing key must be {signature_provider.PRIVATE_KEY_BYTES} bytes"
        )
    return signature_provider.PROVIDER.sign_checkpoint(signing_seed, payload.signing_input())


def verify_checkpoint(
    payload: CheckpointPayload,
    signature: bytes,
    registry: SignerRegistry,
) -> tuple[CheckpointSignatureOutcome, str]:
    """Verify a checkpoint signature against the declared signer set.

    Fail-closed on every defect, with a distinct outcome for each so that a
    reader can tell "nobody signed this" from "the wrong person signed it"
    from "the bytes were altered".
    """
    if not signature:
        return (
            CheckpointSignatureOutcome.MISSING,
            f"checkpoint {payload.checkpoint_sequence} carries no signature",
        )
    if payload.schema_version != CHECKPOINT_SCHEMA_VERSION:
        return (
            CheckpointSignatureOutcome.CONTEXT_MISMATCH,
            f"checkpoint schema {payload.schema_version!r} is not {CHECKPOINT_SCHEMA_VERSION!r}",
        )
    if payload.election_context_id != registry.election_context_id:
        return (
            CheckpointSignatureOutcome.CONTEXT_MISMATCH,
            "checkpoint names a different election than the signer registry",
        )
    if payload.board_id != registry.board_id:
        return (
            CheckpointSignatureOutcome.CONTEXT_MISMATCH,
            "checkpoint names a different board than the signer registry",
        )
    record = registry.resolve(payload.signing_key_id)
    if record is None:
        return (
            CheckpointSignatureOutcome.SIGNER_UNKNOWN,
            f"signing key {payload.signing_key_id!r} is not in the declared signer "
            "set; a key carried by the artefact it signs is never a trust anchor",
        )
    if (
        record.election_context_id != payload.election_context_id
        or record.board_id != payload.board_id
    ):
        return (
            CheckpointSignatureOutcome.SIGNER_UNAUTHORIZED,
            f"signing key {payload.signing_key_id!r} is not authorised for this election and board",
        )
    if not record.is_active_at(payload.checkpoint_sequence):
        return (
            CheckpointSignatureOutcome.SIGNER_UNAUTHORIZED,
            f"signing key {payload.signing_key_id!r} is outside its declared "
            f"activation window at checkpoint {payload.checkpoint_sequence}",
        )
    if not signature_provider.PROVIDER.verify_checkpoint(
        record.public_key, payload.signing_input(), signature
    ):
        return (
            CheckpointSignatureOutcome.INVALID,
            f"signature on checkpoint {payload.checkpoint_sequence} does not verify",
        )
    return CheckpointSignatureOutcome.VALID, ""

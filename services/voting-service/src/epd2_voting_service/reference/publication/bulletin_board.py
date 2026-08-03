"""Append-only bulletin board with chained signed checkpoints."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
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
from epd2_voting_service.reference.crypto.merkle import consistency_proof, inclusion_proof
from epd2_voting_service.reference.crypto.merkle import root as merkle_root
from epd2_voting_service.reference.hooks import FaultHook, trip
from epd2_voting_service.reference.publication.checkpoint_signing import (
    CHECKPOINT_SCHEMA_VERSION,
    CheckpointPayload,
    SignerRecord,
    SignerRegistry,
    sign_checkpoint,
)


class EntryType(StrEnum):
    ELECTION_MANIFEST = "election_manifest"
    PARAMETER_SET = "parameter_set"
    JOINT_PUBLIC_KEY = "joint_public_key"
    SEALED_BATCH_COMMITMENT = "sealed_batch_commitment"
    SEALED_BATCH_OPENING = "sealed_batch_opening"
    BATCH_RECONCILIATION_RECORD = "batch_reconciliation_record"
    BALLOT_ACCEPTED = "ballot_accepted"
    BALLOT_SPOILED = "ballot_spoiled"
    ELECTION_CLOSED = "election_closed"
    TALLY_ARTIFACT = "tally_artifact"
    INCIDENT_NOTICE = "incident_notice"
    BOARD_CHECKPOINT = "board_checkpoint"


PRE_CLOSURE_ENTRY_TYPES: frozenset[EntryType] = frozenset(
    {
        EntryType.ELECTION_MANIFEST,
        EntryType.PARAMETER_SET,
        EntryType.JOINT_PUBLIC_KEY,
        EntryType.SEALED_BATCH_COMMITMENT,
        EntryType.INCIDENT_NOTICE,
        EntryType.BOARD_CHECKPOINT,
    }
)


class BoardIntegrityError(RuntimeError):
    reason_code = "BULLETIN_BOARD_BATCH_ROOT_MISMATCH"


class PreClosurePublicationError(RuntimeError):
    reason_code = "PUBLICATION_UNSCHEDULED_BATCH_PROHIBITED"


@dataclass(frozen=True, slots=True)
class BoardEntry:
    sequence: int
    entry_type: EntryType
    payload: bytes

    def canonical_bytes(self) -> bytes:
        return encode_struct(
            [
                ("sequence", encode_uint(self.sequence, 8)),
                ("entry_type", encode_text(self.entry_type.value)),
                ("payload", encode_bytes(self.payload)),
            ]
        )

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.BOARD_ENTRY, [self.canonical_bytes()])


@dataclass(frozen=True, slots=True)
class Checkpoint:
    checkpoint_sequence: int
    tree_size: int
    root: bytes
    previous_checkpoint_hash: bytes
    signature: bytes
    signing_key_id: str = ""
    board_id: str = ""
    election_context_id: str = ""
    protocol_profile_id: str = ""
    publication_phase: str = "open"
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def payload(self) -> CheckpointPayload:
        """The exact structure the signature covers."""
        return CheckpointPayload(
            protocol_profile_id=self.protocol_profile_id,
            election_context_id=self.election_context_id,
            board_id=self.board_id,
            checkpoint_sequence=self.checkpoint_sequence,
            tree_size=self.tree_size,
            root=self.root,
            previous_checkpoint_hash=self.previous_checkpoint_hash,
            publication_phase=self.publication_phase,
            signing_key_id=self.signing_key_id,
            schema_version=self.schema_version,
        )

    def canonical_bytes(self) -> bytes:
        return self.payload().canonical_bytes()

    def digest(self) -> bytes:
        return h(ZERO_KEY, DomainLabel.BOARD_CHECKPOINT, [self.canonical_bytes()])


@dataclass
class BulletinBoard:
    """Reference append-only board.

    A single list is *not* the append-only guarantee: the guarantee is that
    every published checkpoint is chained, signed and independently
    re-derivable from the exported entries, which is what
    `verification.verifier` actually checks.
    """

    election_context_id: str
    #: TEST-ONLY Ed25519 seed in fixtures. A production board holds this in
    #: a key store this reference implementation does not model.
    signing_key: bytes
    board_id: str = "board-1"
    signing_key_id: str = "board-signing-key-1"
    protocol_profile_id: str = "EPD2-CRYPTO-1"
    entries: list[BoardEntry] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    closed: bool = False

    def signer_record(self) -> SignerRecord:
        """This board's own entry in a signer registry."""
        return SignerRecord(
            signing_key_id=self.signing_key_id,
            public_key=signature_provider.PROVIDER.generate_test_keypair(self._seed())[1],
            board_id=self.board_id,
            election_context_id=self.election_context_id,
        )

    def signer_registry(self) -> SignerRegistry:
        return SignerRegistry(
            election_context_id=self.election_context_id,
            board_id=self.board_id,
            signers=(self.signer_record(),),
        )

    def _seed(self) -> bytes:
        """Derive a 32-byte **TEST-ONLY** Ed25519 private key from `signing_key`.

        Fixtures pass a short human-readable string; a production board
        holds a real key in a key store this reference implementation does
        not model (`OD-P16D-11`). Hashing here keeps the fixture ergonomics
        without letting a short string become a short key — a 32-byte value
        is used as-is, anything else is stretched by SHA-256.
        """
        if len(self.signing_key) == signature_provider.PRIVATE_KEY_BYTES:
            return self.signing_key
        return hashlib.sha256(self.signing_key).digest()

    def append(
        self,
        entry_type: EntryType,
        payload: bytes,
        *,
        fault_hook: FaultHook | None = None,
    ) -> BoardEntry:
        if not self.closed and entry_type not in PRE_CLOSURE_ENTRY_TYPES:
            raise PreClosurePublicationError(
                f"{entry_type.value} may not be published before closure"
            )
        entry = BoardEntry(len(self.entries), entry_type, payload)
        self.entries.append(entry)
        trip(fault_hook, "after_board_append")
        return entry

    def close(self, payload: bytes = b"") -> BoardEntry:
        entry = BoardEntry(len(self.entries), EntryType.ELECTION_CLOSED, payload)
        self.entries.append(entry)
        self.closed = True
        return entry

    def root(self) -> bytes:
        return merkle_root([e.digest() for e in self.entries])

    def publish_checkpoint(self, *, fault_hook: FaultHook | None = None) -> Checkpoint:
        trip(fault_hook, "before_checkpoint_signing")
        previous = self.checkpoints[-1].digest() if self.checkpoints else b"\x00" * 32
        unsigned = Checkpoint(
            checkpoint_sequence=len(self.checkpoints),
            tree_size=len(self.entries),
            root=self.root(),
            previous_checkpoint_hash=previous,
            signature=b"",
            signing_key_id=self.signing_key_id,
            board_id=self.board_id,
            election_context_id=self.election_context_id,
            protocol_profile_id=self.protocol_profile_id,
            publication_phase="closed" if self.closed else "open",
        )
        signature = sign_checkpoint(unsigned.payload(), self._seed())
        checkpoint = Checkpoint(
            checkpoint_sequence=unsigned.checkpoint_sequence,
            tree_size=unsigned.tree_size,
            root=unsigned.root,
            previous_checkpoint_hash=unsigned.previous_checkpoint_hash,
            signature=signature,
            signing_key_id=unsigned.signing_key_id,
            board_id=unsigned.board_id,
            election_context_id=unsigned.election_context_id,
            protocol_profile_id=unsigned.protocol_profile_id,
            publication_phase=unsigned.publication_phase,
        )
        self.checkpoints.append(checkpoint)
        return checkpoint

    def inclusion_proof(self, sequence: int) -> list[tuple[str, bytes]]:
        if not 0 <= sequence < len(self.entries):
            raise BoardIntegrityError("entry sequence out of range")
        return inclusion_proof([e.digest() for e in self.entries], sequence)

    def consistency_proof(self, old_tree_size: int) -> list[bytes]:
        """Prove the tree of ``old_tree_size`` entries is a prefix of this one."""
        if not 0 < old_tree_size <= len(self.entries):
            raise BoardIntegrityError(
                f"old tree size {old_tree_size} is not in (0, {len(self.entries)}]"
            )
        return consistency_proof([e.digest() for e in self.entries], old_tree_size)

    def root_at(self, tree_size: int) -> bytes:
        """The root the board would have published at ``tree_size`` entries."""
        if not 0 <= tree_size <= len(self.entries):
            raise BoardIntegrityError("tree size out of range")
        return merkle_root([e.digest() for e in self.entries[:tree_size]])

    def export_entries(self) -> list[tuple[int, str, bytes]]:
        """Bytes only. The verifier never touches this object's internals."""
        return [(e.sequence, e.entry_type.value, e.payload) for e in self.entries]

    def export_checkpoints(self) -> list[tuple[int, int, bytes, bytes, bytes]]:
        """Legacy five-tuple view, kept so existing callers still work."""
        return [
            (c.checkpoint_sequence, c.tree_size, c.root, c.previous_checkpoint_hash, c.signature)
            for c in self.checkpoints
        ]

    def export_signed_checkpoints(self) -> list[Checkpoint]:
        """Full checkpoints, which is what signature verification needs."""
        return list(self.checkpoints)

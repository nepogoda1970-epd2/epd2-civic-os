"""Checkpoint authenticity (correction §9, §10, §20; final correction §5, §33).

Two properties are kept apart throughout, because conflating them is the
mistake the previous correction existed to fix:

* a **valid signature** proves the named authorised signer issued the
  checkpoint;
* it proves **nothing** about whether the board showed the same checkpoint
  to everyone. Two correctly signed checkpoints can still conflict, and the
  last tests here demonstrate exactly that.

**The signature primitive is no longer ours.** The previous candidate
implemented Ed25519 in this repository and an audit failed it. The active
path is now `crypto.signature_provider`, a thin port over a vetted library.
The tests below therefore changed character: they no longer probe curve
arithmetic we wrote, they check that the port is wired up, canonical,
fail-closed, and conformant to RFC 8032's published vectors.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

from epd2_voting_service.reference.crypto.signature_provider import (
    PROVIDER,
    CheckpointSignatureProvider,
    CryptographyEd25519Provider,
    SignatureFormatError,
)
from epd2_voting_service.reference.publication.bulletin_board import (
    BulletinBoard,
    Checkpoint,
    EntryType,
)
from epd2_voting_service.reference.publication.checkpoint_signing import (
    CHECKPOINT_SCHEMA_VERSION,
    CheckpointPayload,
    CheckpointSignatureOutcome,
    CheckpointSigningError,
    SignerRecord,
    SignerRegistry,
    sign_checkpoint,
    verify_checkpoint,
)
from epd2_voting_service.reference.testing.fixtures import fixture_a
from epd2_voting_service.reference.verification.results import VerificationResultCode
from epd2_voting_service.reference.verification.verifier import (
    BoardExport,
    board_export_from,
    verify_board,
)

REFERENCE_ROOT = pathlib.Path(__file__).resolve().parents[2] / "src/epd2_voting_service/reference"
CLI_ORACLE = pathlib.Path(__file__).resolve().parent / "crossimpl/openssl_cli_ed25519_oracle.py"

#: RFC 8032 §7.1. Reproduced from the RFC itself, three of its vectors:
#: the empty message, a one-byte message and a longer one. Each entry is
#: (secret key, public key, message, signature), all lower-case hex.
RFC_8032_VECTORS: list[tuple[str, str, str, str]] = [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8"
        "821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "72",
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085a"
        "c1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
    (
        "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
        "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
        "af82",
        "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff"
        "9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a",
    ),
]


def _board(
    election_context_id: str = "ctx-a",
    signing_key: bytes = b"TEST-ONLY-board-seed",
    board_id: str = "board-1",
) -> BulletinBoard:
    board = BulletinBoard(
        election_context_id=election_context_id,
        signing_key=signing_key,
        board_id=board_id,
    )
    board.append(EntryType.ELECTION_MANIFEST, b"manifest")
    board.append(EntryType.PARAMETER_SET, b"parameters")
    return board


# -- the provider: is it the vetted one, and is the old one gone? --------


def test_vetted_ed25519_provider_is_active() -> None:
    """The active provider is the library port, not anything we wrote."""
    assert isinstance(PROVIDER, CryptographyEd25519Provider)
    assert isinstance(PROVIDER, CheckpointSignatureProvider)
    assert PROVIDER.backend.startswith("cryptography")
    assert PROVIDER.profile == "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"
    # The provider module must be the one the publication layer signs with.
    from epd2_voting_service.reference.publication import checkpoint_signing

    assert PROVIDER.profile == checkpoint_signing.SIGNATURE_PROFILE


def test_handwritten_ed25519_not_imported() -> None:
    """No module in the reference package imports or defines curve arithmetic.

    Asserted structurally with `ast` rather than by grepping for a name,
    because the failure this guards against is somebody re-adding the
    implementation under a different filename.
    """
    assert not (REFERENCE_ROOT / "crypto/ed25519.py").exists(), (
        "the hand-written Ed25519 module is back; the audit removed it for a reason"
    )

    banned_names = {"ed25519", "edwards25519", "_recover_x", "_decompress", "_compress"}
    offenders: list[str] = []
    for path in sorted(REFERENCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # `from cryptography...ed25519 import ...` is the vetted
                # library and is the one form allowed, in one module only.
                if node.module.endswith(".ed25519") and not node.module.startswith("cryptography."):
                    offenders.append(f"{path.name}: from {node.module}")
                if node.module.startswith("cryptography.") and path.name != "signature_provider.py":
                    offenders.append(f"{path.name}: imports cryptography outside the provider")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[-1] in banned_names:
                        offenders.append(f"{path.name}: import {alias.name}")
            if isinstance(node, ast.FunctionDef) and node.name in banned_names:
                offenders.append(f"{path.name}: def {node.name}")
    assert offenders == [], offenders


def test_missing_provider_fails_closed() -> None:
    """With `cryptography` unavailable, importing the provider must raise.

    Run in a subprocess with the module blocked, because the property is
    about import-time behaviour and cannot be observed in a process that has
    already imported it successfully. What must **not** happen is a silent
    fallback to a hand-written implementation.
    """
    probe = (
        "import epd2_voting_service.reference.crypto.signature_provider as p\n"
        "print('OK' if p.PROVIDER.backend.startswith('cryptography') else 'WRONG')\n"
    )
    blocked = (
        "import sys\n"
        "class Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] == 'cryptography':\n"
        "            raise ImportError('blocked for the test')\n"
        "        return None\n"
        "sys.meta_path.insert(0, Block())\n"
        "for mod in [m for m in sys.modules if m.split('.')[0] == 'cryptography']:\n"
        "    del sys.modules[mod]\n"
        "try:\n"
        "    import epd2_voting_service.reference.crypto.signature_provider  # noqa: F401\n"
        "except Exception as exc:\n"
        "    print(type(exc).__name__)\n"
        "else:\n"
        "    print('IMPORTED-ANYWAY')\n"
    )
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    # Control: without the blocker the same subprocess must import fine.
    # Without this, a subprocess that could never import `cryptography`
    # anyway would make the real assertion pass for the wrong reason.
    control = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True, text=True, timeout=300, check=False, env=env,
    )  # fmt: skip
    assert control.stdout.strip() == "OK", (
        "the control run could not import the provider at all, so this test "
        f"proves nothing about the fallback: {control.stderr[-400:]}"
    )

    completed = subprocess.run(
        [sys.executable, "-c", blocked],
        capture_output=True, text=True, timeout=300, check=False, env=env,
    )  # fmt: skip
    out = completed.stdout.strip()
    assert out != "IMPORTED-ANYWAY", (
        "the provider imported with `cryptography` blocked, which means a fallback exists"
    )
    assert out in {"SignatureProviderUnavailableError", "ImportError", "ModuleNotFoundError"}, (
        f"unexpected failure mode: {out!r} / {completed.stderr[-400:]}"
    )


# -- RFC 8032 conformance ------------------------------------------------


@pytest.mark.parametrize(("index", "vector"), list(enumerate(RFC_8032_VECTORS)))
def test_rfc8032_vectors(index: int, vector: tuple[str, str, str, str]) -> None:
    """RFC 8032 §7.1 — primary-source conformance for the signature scheme.

    Three vectors: TEST 1 (empty message), TEST 2 (one byte), TEST 3 (two
    bytes). The RFC publishes more; these three are reproduced with their
    provenance rather than a bulk copy of the corpus.
    """
    secret_hex, public_hex, message_hex, signature_hex = vector
    secret = bytes.fromhex(secret_hex)
    message = bytes.fromhex(message_hex)

    private_bytes, public_bytes = PROVIDER.generate_test_keypair(secret)
    assert private_bytes == secret
    assert public_bytes.hex() == public_hex, f"RFC 8032 vector {index + 1}: public key"
    assert PROVIDER.sign_checkpoint(secret, message).hex() == signature_hex, (
        f"RFC 8032 vector {index + 1}: signature"
    )
    assert PROVIDER.verify_checkpoint(
        bytes.fromhex(public_hex), message, bytes.fromhex(signature_hex)
    )


def test_rfc8032_vector_1() -> None:
    """Named separately because the correction task names it."""
    secret, public, message, signature = RFC_8032_VECTORS[0]
    assert PROVIDER.generate_test_keypair(bytes.fromhex(secret))[1].hex() == public
    produced = PROVIDER.sign_checkpoint(bytes.fromhex(secret), bytes.fromhex(message))
    assert produced.hex() == signature


def test_rfc8032_vector_2() -> None:
    secret, public, message, signature = RFC_8032_VECTORS[1]
    assert PROVIDER.generate_test_keypair(bytes.fromhex(secret))[1].hex() == public
    produced = PROVIDER.sign_checkpoint(bytes.fromhex(secret), bytes.fromhex(message))
    assert produced.hex() == signature


def test_openssl_cli_independently_verifies_rfc_vectors() -> None:
    """Independent oracle: the OpenSSL **binary**, out-of-process.

    Not the same artefact as the linked library the provider uses, though
    it shares an upstream — a limitation the conformance report states
    rather than glosses. If the binary is absent the test **fails**: a
    silently skipped oracle is how a round ends up claiming conformance it
    never measured.
    """
    assert shutil.which("openssl") is not None, (
        "the `openssl` binary is absent, so the independent CLI oracle could "
        "not run; record this as missing evidence rather than as a pass"
    )

    cases = {}
    for index, (_secret, public, message, signature) in enumerate(RFC_8032_VECTORS):
        cases[f"rfc8032-{index + 1}-valid"] = {
            "public_key": public,
            "message": message,
            "signature": signature,
            "expected": "accepted",
        }
        # The same signature under a flipped message byte must be refused.
        mutated = bytes.fromhex(message) + b"\x01"
        cases[f"rfc8032-{index + 1}-mutated-message"] = {
            "public_key": public,
            "message": mutated.hex(),
            "signature": signature,
            "expected": "rejected",
        }

    with tempfile.TemporaryDirectory() as work:
        case_file = pathlib.Path(work) / "cases.json"
        case_file.write_text(json.dumps({"cases": cases}), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(CLI_ORACLE), str(case_file)],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    assert completed.returncode == 0, completed.stderr
    verdict = json.loads(completed.stdout)
    assert verdict["backend"].startswith("OpenSSL"), verdict["backend"]

    disagreements = [
        f"{name}: expected {r['expected']}, got {r['actual']} ({r['detail'][:80]})"
        for name, r in verdict["cases"].items()
        if not r["match"]
    ]
    assert disagreements == [], disagreements
    # At least the non-empty vectors must have genuinely run, not skipped.
    ran = [r for r in verdict["cases"].values() if not r["skipped"]]
    assert len(ran) >= 4, f"too few CLI comparisons actually executed: {len(ran)}"


# -- canonical encodings and fail-closed inputs --------------------------


def test_invalid_signature_rejected() -> None:
    _secret, public, message, signature = RFC_8032_VECTORS[1]
    raw = bytearray(bytes.fromhex(signature))
    raw[0] ^= 0x01
    assert not PROVIDER.verify_checkpoint(bytes.fromhex(public), bytes.fromhex(message), bytes(raw))


def test_wrong_public_key_rejected() -> None:
    _s, _public, message, signature = RFC_8032_VECTORS[1]
    other = RFC_8032_VECTORS[2][1]
    assert not PROVIDER.verify_checkpoint(
        bytes.fromhex(other), bytes.fromhex(message), bytes.fromhex(signature)
    )


def test_wrong_message_rejected() -> None:
    _s, public, _message, signature = RFC_8032_VECTORS[1]
    assert not PROVIDER.verify_checkpoint(
        bytes.fromhex(public), b"a different message", bytes.fromhex(signature)
    )


def test_noncanonical_key_length_rejected() -> None:
    """A 31- or 33-byte key is malformed, not an alternative encoding."""
    _s, public, message, signature = RFC_8032_VECTORS[1]
    for wrong in (bytes.fromhex(public)[:-1], bytes.fromhex(public) + b"\x00", b"", b"\x00" * 64):
        assert not PROVIDER.verify_checkpoint(
            wrong, bytes.fromhex(message), bytes.fromhex(signature)
        )
    with pytest.raises(SignatureFormatError):
        PROVIDER.load_public_key(bytes.fromhex(public)[:-1])
    with pytest.raises(SignatureFormatError):
        PROVIDER.load_public_key("not bytes")  # type: ignore[arg-type]


def test_noncanonical_signature_length_rejected() -> None:
    _s, public, message, signature = RFC_8032_VECTORS[1]
    raw = bytes.fromhex(signature)
    for wrong in (raw[:-1], raw + b"\x00", b"", raw[:32]):
        assert not PROVIDER.verify_checkpoint(bytes.fromhex(public), bytes.fromhex(message), wrong)
    with pytest.raises(SignatureFormatError):
        PROVIDER.signature_bytes(raw[:-1])


def test_provider_rejects_a_wrong_length_private_key() -> None:
    with pytest.raises(SignatureFormatError):
        PROVIDER.generate_test_keypair(b"short")
    with pytest.raises(SignatureFormatError):
        PROVIDER.sign_checkpoint(b"short", b"message")


def test_public_key_round_trips_through_the_canonical_form() -> None:
    _s, public, _m, _sig = RFC_8032_VECTORS[1]
    loaded = PROVIDER.load_public_key(bytes.fromhex(public))
    assert PROVIDER.public_key_bytes(loaded).hex() == public
    with pytest.raises(SignatureFormatError):
        PROVIDER.public_key_bytes(object())


def test_a_seed_of_the_wrong_length_is_refused() -> None:
    with pytest.raises(SignatureFormatError):
        PROVIDER.generate_test_keypair(b"short")
    with pytest.raises(CheckpointSigningError):
        sign_checkpoint(
            CheckpointPayload(
                protocol_profile_id="EPD2-CRYPTO-1",
                election_context_id="ctx",
                board_id="board-1",
                checkpoint_sequence=0,
                tree_size=1,
                root=b"\x00" * 32,
                previous_checkpoint_hash=b"\x00" * 32,
                publication_phase="open",
                signing_key_id="k",
            ),
            b"too short",
        )


# -- checkpoint signing and verification ---------------------------------


def test_valid_checkpoint_signature() -> None:
    board = _board()
    checkpoint = board.publish_checkpoint()
    outcome, detail = verify_checkpoint(
        checkpoint.payload(), checkpoint.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.VALID, detail
    assert checkpoint.signing_key_id == board.signing_key_id
    assert checkpoint.schema_version == CHECKPOINT_SCHEMA_VERSION


def test_missing_checkpoint_signature_rejected() -> None:
    board = _board()
    checkpoint = board.publish_checkpoint()
    unsigned = dataclasses.replace(checkpoint, signature=b"")
    outcome, detail = verify_checkpoint(
        unsigned.payload(), unsigned.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.MISSING
    assert "no signature" in detail


def test_unknown_signer_rejected() -> None:
    """A key that is not in the declared set is never a trust anchor."""
    board = _board()
    checkpoint = board.publish_checkpoint()
    stranger = dataclasses.replace(checkpoint, signing_key_id="some-other-key")
    outcome, detail = verify_checkpoint(
        stranger.payload(), stranger.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.SIGNER_UNKNOWN
    assert "not in the declared signer set" in detail


def test_unauthorized_signer_rejected() -> None:
    """A real key, correctly used, but authorised for a different board."""
    board = _board()
    checkpoint = board.publish_checkpoint()
    registry = SignerRegistry(
        election_context_id=board.election_context_id,
        board_id=board.board_id,
        signers=(dataclasses.replace(board.signer_record(), board_id="another-board"),),
    )
    outcome, detail = verify_checkpoint(checkpoint.payload(), checkpoint.signature, registry)
    assert outcome is CheckpointSignatureOutcome.SIGNER_UNAUTHORIZED
    assert "not authorised" in detail


def test_signer_outside_its_activation_window_rejected() -> None:
    """Key rotation: a superseded key may not sign a later checkpoint."""
    board = _board()
    first = board.publish_checkpoint()
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"b")
    second = board.publish_checkpoint()
    rotated = SignerRegistry(
        election_context_id=board.election_context_id,
        board_id=board.board_id,
        signers=(
            dataclasses.replace(
                board.signer_record(),
                active_from_sequence=0,
                active_to_sequence=0,
                superseded_by="board-signing-key-2",
            ),
        ),
    )
    assert (
        verify_checkpoint(first.payload(), first.signature, rotated)[0]
        is CheckpointSignatureOutcome.VALID
    )
    outcome, detail = verify_checkpoint(second.payload(), second.signature, rotated)
    assert outcome is CheckpointSignatureOutcome.SIGNER_UNAUTHORIZED
    assert "activation window" in detail


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("root", b"\xff" * 32),
        ("checkpoint_sequence", 41),
        ("tree_size", 999),
        ("previous_checkpoint_hash", b"\xaa" * 32),
        ("publication_phase", "closed"),
    ],
)
def test_altered_checkpoint_rejected(field: str, value: object) -> None:
    board = _board()
    checkpoint = board.publish_checkpoint()
    altered = dataclasses.replace(checkpoint, **{field: value})  # type: ignore[arg-type]
    outcome, _ = verify_checkpoint(altered.payload(), altered.signature, board.signer_registry())
    assert outcome is CheckpointSignatureOutcome.INVALID


# The three cases below are already covered by the parametrisation above.
# They exist under their own names because the correction task names them
# individually, and a requirement that can only be found by reading a
# parameter list is a requirement a reviewer will miss. Each asserts the
# same property the parametrised case does, on the field it is named for.


def _altered(field: str, value: object) -> CheckpointSignatureOutcome:
    board = _board()
    checkpoint = board.publish_checkpoint()
    altered = dataclasses.replace(checkpoint, **{field: value})  # type: ignore[arg-type]
    outcome, _ = verify_checkpoint(altered.payload(), altered.signature, board.signer_registry())
    return outcome


def test_altered_root_rejected() -> None:
    """A different root under the same signature is not the same checkpoint."""
    assert _altered("root", b"\xff" * 32) is CheckpointSignatureOutcome.INVALID


def test_altered_sequence_rejected() -> None:
    """Replaying a checkpoint at another sequence number does not verify."""
    assert _altered("checkpoint_sequence", 41) is CheckpointSignatureOutcome.INVALID


def test_altered_tree_size_rejected() -> None:
    """Claiming a different number of entries does not verify."""
    assert _altered("tree_size", 999) is CheckpointSignatureOutcome.INVALID


def test_wrong_election_signature_rejected() -> None:
    """A signature from another election does not transfer."""
    board = _board(election_context_id="ctx-a")
    other = _board(election_context_id="ctx-b")
    checkpoint = other.publish_checkpoint()
    outcome, detail = verify_checkpoint(
        checkpoint.payload(), checkpoint.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.CONTEXT_MISMATCH
    assert "different election" in detail


def test_wrong_board_signature_rejected() -> None:
    board = _board()
    other = BulletinBoard(
        election_context_id=board.election_context_id,
        signing_key=b"TEST-ONLY-board-seed",
        board_id="board-2",
    )
    other.append(EntryType.ELECTION_MANIFEST, b"manifest")
    other.append(EntryType.PARAMETER_SET, b"parameters")
    checkpoint = other.publish_checkpoint()
    outcome, detail = verify_checkpoint(
        checkpoint.payload(), checkpoint.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.CONTEXT_MISMATCH
    assert "different board" in detail


def test_signature_replay_rejected() -> None:
    """A signature lifted from checkpoint 0 does not validate checkpoint 1."""
    board = _board()
    first = board.publish_checkpoint()
    board.append(EntryType.SEALED_BATCH_COMMITMENT, b"b")
    second = board.publish_checkpoint()
    replayed = dataclasses.replace(second, signature=first.signature)
    outcome, _ = verify_checkpoint(replayed.payload(), replayed.signature, board.signer_registry())
    assert outcome is CheckpointSignatureOutcome.INVALID


def test_schema_version_is_bound() -> None:
    board = _board()
    checkpoint = board.publish_checkpoint()
    downgraded = dataclasses.replace(checkpoint, schema_version="EPD2-CHECKPOINT-1")
    outcome, detail = verify_checkpoint(
        downgraded.payload(), downgraded.signature, board.signer_registry()
    )
    assert outcome is CheckpointSignatureOutcome.CONTEXT_MISMATCH
    assert "schema" in detail


def test_the_payload_binds_every_field_the_specification_lists() -> None:
    payload = CheckpointPayload(
        protocol_profile_id="EPD2-CRYPTO-1",
        election_context_id="ctx",
        board_id="board-1",
        checkpoint_sequence=3,
        tree_size=9,
        root=b"\x01" * 32,
        previous_checkpoint_hash=b"\x02" * 32,
        publication_phase="open",
        signing_key_id="key-1",
    )
    encoded = payload.canonical_bytes()
    for name in (
        b"schema_version",
        b"protocol_profile_id",
        b"election_context_id",
        b"board_id",
        b"checkpoint_sequence",
        b"tree_size",
        b"root",
        b"previous_checkpoint_hash",
        b"publication_phase",
        b"signing_key_id",
    ):
        assert name in encoded
    # canonical binary, never JSON
    assert not encoded.lstrip().startswith(b"{")
    assert payload.signing_input() != encoded


# -- verifier integration ------------------------------------------------


def test_verifier_checks_signatures_and_says_so() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    result = verify_board(board_export_from(board))
    assert result.code is VerificationResultCode.VERIFIED
    assert "board.checkpoint_signatures" in result.checks_run


def test_verifier_reports_a_forged_signature_distinctly() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    export = board_export_from(board)
    forged = dataclasses.replace(export.signed_checkpoints[0], signature=b"\x00" * 64)
    broken = dataclasses.replace(export, signed_checkpoints=(forged,))
    result = verify_board(broken)
    assert result.code is VerificationResultCode.BOARD_SIGNATURE_INVALID
    assert result.exit_code == 48


def test_verifier_reports_an_unknown_signer_distinctly() -> None:
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    export = board_export_from(board)
    stranger = dataclasses.replace(export.signed_checkpoints[0], signing_key_id="nobody")
    result = verify_board(dataclasses.replace(export, signed_checkpoints=(stranger,)))
    assert result.code is VerificationResultCode.BOARD_SIGNER_UNKNOWN
    assert result.exit_code == 46


def test_an_export_without_signed_checkpoints_is_incomplete() -> None:
    """Losing the signed view must not degrade to a weaker check."""
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    board.publish_checkpoint()
    stripped = BoardExport(
        entries=tuple(board.export_entries()),
        checkpoints=tuple(board.export_checkpoints()),
    )
    result = verify_board(stripped)
    assert result.code is VerificationResultCode.INCOMPLETE_RECORD
    assert "signed checkpoints" in result.detail


# -- authenticity is not consistency -------------------------------------


def test_conflicting_signed_checkpoints_detected() -> None:
    """Two *validly signed* checkpoints at one sequence is equivocation.

    This is the case a signature check alone cannot catch, and the reason
    §10 keeps the two properties apart. Both signatures here are genuine.
    """
    fixture = fixture_a()
    board = fixture.board
    board.append(EntryType.ELECTION_MANIFEST, b"m")
    honest = board.publish_checkpoint()

    # The same authorised signer signs a different root at the same
    # sequence — a split view, correctly signed.
    conflicting_payload = dataclasses.replace(honest, root=b"\x5a" * 32).payload()
    conflicting = dataclasses.replace(
        honest,
        root=b"\x5a" * 32,
        signature=sign_checkpoint(conflicting_payload, hashlib.sha256(board.signing_key).digest()),
    )
    registry = board.signer_registry()
    assert (
        verify_checkpoint(honest.payload(), honest.signature, registry)[0]
        is CheckpointSignatureOutcome.VALID
    )
    assert (
        verify_checkpoint(conflicting.payload(), conflicting.signature, registry)[0]
        is CheckpointSignatureOutcome.VALID
    ), "both signatures must be genuine for this test to mean anything"

    export = BoardExport(
        entries=tuple(board.export_entries()),
        checkpoints=tuple(board.export_checkpoints()),
        signed_checkpoints=(honest, conflicting),
        signer_registry=registry,
    )
    result = verify_board(export)
    assert result.code is VerificationResultCode.BOARD_INCONSISTENCY
    assert "equivocated" in result.detail


def test_a_valid_signature_is_not_evidence_of_a_single_view() -> None:
    """The claim this module must never make, asserted as documentation."""
    from epd2_voting_service.reference.verification.results import NOT_CHECKED

    assert any("same checkpoints to everyone" in line for line in NOT_CHECKED)
    assert any("authorised signer set itself" in line for line in NOT_CHECKED)


def test_a_signer_registry_is_never_read_from_the_checkpoint() -> None:
    """Structural: no code path takes a key out of the artefact it checks."""
    import inspect

    from epd2_voting_service.reference.publication import checkpoint_signing

    source = inspect.getsource(checkpoint_signing.verify_checkpoint)
    assert "registry.resolve" in source
    assert "payload.public_key" not in source
    assert not hasattr(CheckpointPayload, "public_key")
    assert "public_key" not in CheckpointPayload.__slots__


def test_signer_record_round_trips_through_canonical_bytes() -> None:
    record = SignerRecord(
        signing_key_id="k",
        public_key=b"\x01" * 32,
        board_id="b",
        election_context_id="e",
    )
    assert record.canonical_bytes() == record.canonical_bytes()
    registry = SignerRegistry(election_context_id="e", board_id="b", signers=(record,))
    assert len(registry.digest()) == 32
    assert registry.resolve("k") is record
    assert registry.resolve("nope") is None


def test_checkpoint_type_is_the_one_the_board_publishes() -> None:
    board = _board()
    checkpoint = board.publish_checkpoint()
    assert isinstance(checkpoint, Checkpoint)
    assert checkpoint.digest() == checkpoint.digest()

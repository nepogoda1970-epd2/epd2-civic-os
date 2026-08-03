"""Checkpoint signature provider — a vetted library, behind one narrow port.

**Why this module replaced a working implementation.** The previous
candidate carried a from-scratch Ed25519: Edwards-curve point arithmetic,
point compression, scalar multiplication, private-key expansion, signing
and verification, all written here. It followed RFC 8032, it agreed with
OpenSSL on every vector it was given, and an independent audit still failed
it — correctly. Agreement on the vectors you thought to write is not the
property that matters for a low-level cryptographic primitive. What matters
is the vulnerability class you did not think of: a missing subgroup check,
a branch that leaks a key bit, a malleable encoding accepted on some input
nobody tried. Those are found by years of adversarial attention paid to one
widely deployed implementation, and they cannot be found by the author of a
fresh one.

So the arithmetic is gone. This module is a **port**, not an
implementation: it defines what the publication layer needs from a
signature scheme and adapts a vetted library to it.

**There is no fallback, deliberately.** If `cryptography` is missing, the
import below raises and the process does not start. A
`try: import cryptography / except: use our own curve code` would silently
reinstate exactly what the audit removed, on whichever machine happened to
lack the dependency — and that machine is the one you would least want
running hand-rolled crypto. Failing closed is the whole point.

**What the provider does not decide.** It answers "is this signature valid
for this key over these bytes". It has no opinion on *whose* key that is.
Signer authorisation lives in `SignerRegistry` and the election context,
where it can be reasoned about; a provider that also decided trust would be
two mechanisms wearing one name.
"""

from __future__ import annotations

from typing import Final, Protocol, runtime_checkable

#: Raw canonical sizes. Ed25519 has exactly one wire form for each of
#: these, so a length that is not exactly right is a malformed input rather
#: than an alternative encoding, and is refused as such.
PUBLIC_KEY_BYTES: Final[int] = 32
SIGNATURE_BYTES: Final[int] = 64
PRIVATE_KEY_BYTES: Final[int] = 32

#: Recorded wherever a signature is published, so a verifier can tell which
#: scheme produced the bytes it is holding.
SIGNATURE_PROFILE: Final[str] = "Ed25519 (RFC 8032, PureEdDSA, SHA-512)"


class SignatureProviderUnavailableError(RuntimeError):
    """No vetted signature provider is installed. **Never fall back.**"""

    reason_code = "SIGNATURE_PROVIDER_UNAVAILABLE"


class SignatureFormatError(ValueError):
    """A key or signature was not in the canonical raw form."""

    reason_code = "BOARD_SIGNATURE_INVALID"


try:  # pragma: no cover - import-time environment check
    from cryptography.hazmat.primitives import serialization as _serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey as _Ed25519PrivateKey,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey as _Ed25519PublicKey,
    )
except ImportError as exc:  # pragma: no cover - exercised out-of-process
    raise SignatureProviderUnavailableError(
        "the vetted Ed25519 provider (`cryptography`) is not installed. "
        "EPD2 does not fall back to a hand-written implementation: install "
        "the declared dependency or do not start."
    ) from exc


@runtime_checkable
class CheckpointSignatureProvider(Protocol):
    """What the publication layer needs, and nothing more.

    Six operations. A provider that needed a seventh would be doing
    something the publication layer should not be delegating.
    """

    #: Human-readable scheme identifier, published alongside signatures.
    profile: str

    def generate_test_keypair(self, seed: bytes) -> tuple[bytes, bytes]:
        """Derive a **TEST-ONLY** keypair deterministically from `seed`.

        Deterministic key generation is what makes fixtures reproducible.
        It is also exactly what a production key must never be, which is
        why the method says so in its name rather than in a comment.
        """
        ...

    def load_public_key(self, raw: bytes) -> object: ...

    def sign_checkpoint(self, private_key_bytes: bytes, message: bytes) -> bytes: ...

    def verify_checkpoint(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        """Verify. Returns `False` on any defect; never raises on bad input."""
        ...

    def public_key_bytes(self, public_key: object) -> bytes: ...

    def signature_bytes(self, signature: bytes) -> bytes: ...


class CryptographyEd25519Provider:
    """Ed25519 via `cryptography`, which is OpenSSL underneath.

    Every method below is argument validation and canonical encoding around
    a library call. If a future reader finds curve arithmetic here again,
    that is the defect this module exists to prevent.
    """

    profile: str = SIGNATURE_PROFILE
    #: Named so a report can state what was used without importing it.
    backend: str = "cryptography (OpenSSL Ed25519)"

    # -- construction ----------------------------------------------------

    def generate_test_keypair(self, seed: bytes) -> tuple[bytes, bytes]:
        """`(private_key_bytes, public_key_bytes)` — TEST-ONLY.

        Ed25519 private keys *are* 32 uniform bytes, so a deterministic
        fixture seed is a usable private key directly. Production keys must
        come from the OS CSPRNG through a key-management process this
        reference implementation does not have (`OD-P16D-11`).
        """
        if not isinstance(seed, bytes | bytearray):
            raise SignatureFormatError("seed must be bytes")
        if len(seed) != PRIVATE_KEY_BYTES:
            raise SignatureFormatError(
                f"seed must be exactly {PRIVATE_KEY_BYTES} bytes, got {len(seed)}"
            )
        private = _Ed25519PrivateKey.from_private_bytes(bytes(seed))
        return bytes(seed), self.public_key_bytes(private.public_key())

    def load_public_key(self, raw: bytes) -> _Ed25519PublicKey:
        """Parse a raw 32-byte public key. Strict: no PEM, no DER, no base64.

        Accepting several encodings would mean two byte strings could name
        the same key, and a registry keyed on bytes would then have two
        entries for one signer.
        """
        if not isinstance(raw, bytes | bytearray):
            raise SignatureFormatError("public key must be bytes")
        if len(raw) != PUBLIC_KEY_BYTES:
            raise SignatureFormatError(
                f"public key must be exactly {PUBLIC_KEY_BYTES} raw bytes, got {len(raw)}"
            )
        try:
            return _Ed25519PublicKey.from_public_bytes(bytes(raw))
        except Exception as exc:  # library raises several distinct types here
            raise SignatureFormatError(f"not a valid Ed25519 public key: {exc}") from exc

    # -- signing and verification ---------------------------------------

    def sign_checkpoint(self, private_key_bytes: bytes, message: bytes) -> bytes:
        if not isinstance(private_key_bytes, bytes | bytearray):
            raise SignatureFormatError("private key must be bytes")
        if len(private_key_bytes) != PRIVATE_KEY_BYTES:
            raise SignatureFormatError(
                f"private key must be exactly {PRIVATE_KEY_BYTES} bytes, "
                f"got {len(private_key_bytes)}"
            )
        if not isinstance(message, bytes | bytearray):
            raise SignatureFormatError("message must be bytes")
        private = _Ed25519PrivateKey.from_private_bytes(bytes(private_key_bytes))
        return self.signature_bytes(private.sign(bytes(message)))

    def verify_checkpoint(self, public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
        """Fail closed on **every** defect, and say nothing about which one.

        A malformed key, a malformed signature and a genuine mismatch all
        return `False` here. The distinction a reader needs — unknown
        signer, unauthorised signer, altered bytes — is drawn by
        `verify_checkpoint` in `publication.checkpoint_signing`, which has
        the registry to draw it with. Making that distinction *here* would
        mean the primitive layer reporting on trust.
        """
        if not isinstance(public_key_bytes, bytes | bytearray):
            return False
        if not isinstance(signature, bytes | bytearray):
            return False
        if not isinstance(message, bytes | bytearray):
            return False
        if len(public_key_bytes) != PUBLIC_KEY_BYTES:
            return False
        if len(signature) != SIGNATURE_BYTES:
            return False
        try:
            public = _Ed25519PublicKey.from_public_bytes(bytes(public_key_bytes))
            public.verify(bytes(signature), bytes(message))
        except Exception:  # InvalidSignature and parse errors alike
            return False
        return True

    # -- canonical encodings --------------------------------------------

    def public_key_bytes(self, public_key: object) -> bytes:
        """Raw 32-byte encoding — the only form this repository publishes."""
        if not isinstance(public_key, _Ed25519PublicKey):
            raise SignatureFormatError("not an Ed25519 public key object")
        raw = public_key.public_bytes(
            encoding=_serialization.Encoding.Raw,
            format=_serialization.PublicFormat.Raw,
        )
        if len(raw) != PUBLIC_KEY_BYTES:  # pragma: no cover - library invariant
            raise SignatureFormatError("provider returned a non-canonical public key length")
        return raw

    def signature_bytes(self, signature: bytes) -> bytes:
        """Assert the canonical 64-byte signature length and return it."""
        if not isinstance(signature, bytes | bytearray):
            raise SignatureFormatError("signature must be bytes")
        if len(signature) != SIGNATURE_BYTES:
            raise SignatureFormatError(
                f"signature must be exactly {SIGNATURE_BYTES} bytes, got {len(signature)}"
            )
        return bytes(signature)


#: The single active provider. There is exactly one, and no selection
#: mechanism: a provider chosen by configuration is a provider an operator
#: can get wrong.
PROVIDER: Final[CryptographyEd25519Provider] = CryptographyEd25519Provider()


def active_provider() -> CryptographyEd25519Provider:
    """The active provider, for callers that prefer a function to a global."""
    return PROVIDER

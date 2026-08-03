"""Canonical encoding for every cryptographic artefact (PACK-16D §12).

The reference implementation uses a **canonical binary tuple encoding**
rather than "JSON that happens to look stable". Ordinary JSON is not
canonical: key order, integer/float ambiguity, unicode escaping and
whitespace are all under-specified, and two conforming encoders can
produce different bytes for the same value. Hashes and signatures are
computed over *these* bytes and over nothing else.

Grammar (all lengths big-endian):

    UINT(n, width)  ->  width bytes, big-endian, fixed width, no
                        leading-zero stripping and no short forms
    BYTES(b)        ->  UINT(len(b), 4) || b
    TEXT(s)         ->  BYTES(NFC(s).encode("utf-8"))
    SEQ(items)      ->  UINT(len(items), 4) || concat(encode(item))
    FIELD(name, v)  ->  TEXT(name) || encode(v)
    STRUCT(fields)  ->  UINT(len(fields), 4) || concat(FIELD(...)) in
                        **declaration order**, never sorted, never a map

Maps are prohibited outright: a struct is an ordered field list, so there
is no key-ordering question to get wrong.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence

ENCODING_VERSION = "EPD2-ENC-1"

MAX_BYTES_LEN = 1 << 24
MAX_SEQ_LEN = 1 << 20
MAX_TEXT_LEN = 1 << 16


class CanonicalEncodingError(ValueError):
    """Input cannot be encoded canonically, or decoded bytes are not canonical."""

    reason_code = "INVALID_CANONICAL_ENCODING"


def encode_uint(value: int, width: int) -> bytes:
    """Fixed-width big-endian unsigned integer."""
    if value < 0:
        raise CanonicalEncodingError("negative integer is not canonically encodable")
    try:
        return value.to_bytes(width, "big")
    except OverflowError as exc:  # pragma: no cover - exercised via encode_group_element
        raise CanonicalEncodingError(f"integer does not fit in {width} bytes") from exc


def decode_uint(raw: bytes, width: int) -> int:
    """Inverse of :func:`encode_uint`, rejecting any non-canonical width."""
    if len(raw) != width:
        raise CanonicalEncodingError(f"expected exactly {width} bytes, got {len(raw)}")
    return int.from_bytes(raw, "big")


def encode_bytes(raw: bytes) -> bytes:
    if len(raw) > MAX_BYTES_LEN:
        raise CanonicalEncodingError("byte string exceeds the canonical length limit")
    return encode_uint(len(raw), 4) + raw


def normalize_text(text: str) -> str:
    """NFC is the single permitted normalisation form."""
    return unicodedata.normalize("NFC", text)


def encode_text(text: str) -> bytes:
    if len(text) > MAX_TEXT_LEN:
        raise CanonicalEncodingError("text exceeds the canonical length limit")
    return encode_bytes(normalize_text(text).encode("utf-8"))


def encode_seq(items: Sequence[bytes]) -> bytes:
    """`UINT(len, 4) || BYTES(item)...` — every item length-prefixed.

    Each item carries its own length. Concatenating the items raw, which
    an earlier version did, makes the encoding ambiguous: `[b"ab", b"c"]`
    and `[b"a", b"bc"]` both flatten to the same bytes, so two different
    sequences share a digest. The independent cross-implementation
    verifier was written from the documented grammar rather than from this
    function and disagreed with it, which is how the defect surfaced.
    """
    if len(items) > MAX_SEQ_LEN:
        raise CanonicalEncodingError("sequence exceeds the canonical length limit")
    return encode_uint(len(items), 4) + b"".join(encode_bytes(item) for item in items)


def encode_struct(fields: Sequence[tuple[str, bytes]]) -> bytes:
    """Ordered field list. Declaration order is normative; never sorted.

    Field values are length-prefixed for the same reason sequence items
    are: a raw value makes the boundary between one field and the next
    depend on the reader's schema rather than on the bytes.
    """
    seen: set[str] = set()
    out = [encode_uint(len(fields), 4)]
    for name, value in fields:
        if name in seen:
            raise CanonicalEncodingError(f"duplicate field {name!r} in canonical struct")
        seen.add(name)
        out.append(encode_text(name))
        out.append(encode_bytes(value))
    return b"".join(out)


def encode_group_element(value: int, modulus_bytes: int) -> bytes:
    """A group element is always the full fixed width of the modulus."""
    return encode_uint(value, modulus_bytes)


def encode_scalar(value: int, order_bytes: int) -> bytes:
    """A scalar is always the full fixed width of the subgroup order."""
    return encode_uint(value, order_bytes)


def encode_bool(value: bool) -> bytes:
    return b"\x01" if value else b"\x00"

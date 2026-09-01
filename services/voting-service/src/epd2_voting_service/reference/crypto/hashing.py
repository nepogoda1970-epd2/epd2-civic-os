"""Domain-separated hashing profile (PACK-16B, PACK-16D §14).

`H` is HMAC-SHA-256 exactly as PACK-16B fixed it. Every call site supplies
a registered domain label (`domain_separation`), a key, and a canonically
encoded input tuple (`encoding`). There is no unkeyed convenience wrapper:
an unkeyed digest is expressed as a keyed one under the zero key, so that
no call site can accidentally reuse a hash context across artefact kinds.
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence

from epd2_voting_service.reference.crypto.domain_separation import DomainLabel, require_label
from epd2_voting_service.reference.crypto.encoding import encode_seq, encode_text

HASH_PROFILE = "HMAC-SHA-256"
DIGEST_BYTES = 32
ZERO_KEY = b"\x00" * DIGEST_BYTES


def h(key: bytes, label: str | DomainLabel, parts: Sequence[bytes]) -> bytes:
    """Keyed, domain-separated hash. Output is the full 32 bytes.

    Truncation is not offered: PACK-16D §14 requires a truncation rule per
    use, and the reference implementation's rule is "never truncate".
    """
    payload = encode_text(require_label(label)) + encode_seq(list(parts))
    return hmac.new(key, payload, hashlib.sha256).digest()


def h_int(key: bytes, label: str | DomainLabel, parts: Sequence[bytes]) -> int:
    """The digest read as a big-endian integer."""
    return int.from_bytes(h(key, label, parts), "big")


def h_q(key: bytes, label: str | DomainLabel, parts: Sequence[bytes], q: int) -> int:
    """`H_q(...) = H(...) mod q`, the challenge-derivation form."""
    return h_int(key, label, parts) % q

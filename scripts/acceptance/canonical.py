"""Deterministic canonical serialization and hashing primitives.

The execution manifest and every machine-readable evidence document the
harness emits use exactly one serialization: UTF-8, sorted keys, no
insignificant whitespace, ``\\n`` line terminator, ASCII-escaped. Two runs
that observed the same facts therefore produce byte-identical documents, and
a document's integrity digest is recomputable by any independent reviewer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_HASH_FIELD = "manifest_sha256"


def canonical_json_bytes(document: Any) -> bytes:
    """Serialize ``document`` deterministically."""
    text = json.dumps(document, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def document_digest(document: dict[str, Any]) -> str:
    """Digest of a document with its own integrity field excluded.

    The digest is computed over the canonical serialization of the document
    with ``manifest_sha256`` removed, so the stored digest never has to be
    part of its own preimage.
    """
    stripped = {key: value for key, value in document.items() if key != MANIFEST_HASH_FIELD}
    return sha256_bytes(canonical_json_bytes(stripped))


def seal_document(document: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``document`` carrying its own integrity digest."""
    sealed = dict(document)
    sealed[MANIFEST_HASH_FIELD] = document_digest(document)
    return sealed


def verify_sealed_document(document: dict[str, Any]) -> bool:
    """True when the document's stored integrity digest matches its content."""
    stored = document.get(MANIFEST_HASH_FIELD)
    if not isinstance(stored, str):
        return False
    return stored == document_digest(document)


def write_canonical_json(path: Path, document: Any) -> str:
    """Write ``document`` canonically; return the SHA-256 of the bytes written."""
    data = canonical_json_bytes(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha256_bytes(data)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

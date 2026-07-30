"""Format-specific canonicalization and the content digest
(PACK-13 §13; `P13-REG-005`, `P13-REG-005a`, `P13-REG-005b`; ADR-073).

This module exists to keep one sentence honest:

> Content that is identical after the registry's format-specific
> canonicalization produces the same content digest. **Digest equality
> does not itself define schema-version identity.**

Two consequences shape the code:

1. **There is no universal format abstraction** (`P13-FMT-002`). Each
   format has its own canonicalizer with its own *enumerated* set of
   removed serialization differences, recorded in
   `REMOVED_DIFFERENCES` and asserted by tests. A layer that pretended
   OpenAPI and SQL migration metadata were the same kind of object would
   produce compatibility answers that are wrong in both.
2. **Canonicalization is not a semantic normalizer** (`P13-REG-005a`).
   It removes key ordering and insignificant whitespace and nothing
   else. Two documents with different digests may still mean the same
   thing, and this module does not adjudicate that
   (`P13-REG-005b`).

`SchemaFormat.SQL_MIGRATION_METADATA` is included because the registry
records migration metadata as a schema-shaped artifact — but its
"canonical form" is the migration ID, the statement digest and the
ordering position, and its compatibility answer comes from §18's
migration-control checks, **not** from a schema differ (`P13-FMT-003`'s
table).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from epd2_core.canonical_json import canonical_dumps
from epd2_data_plane_service.domain import content_digest


class SchemaFormat(StrEnum):
    """The formats the registry supports (`P13-FMT-001`).

    Protobuf and Avro are admissible as a future-compatible extension
    where justified, and are deliberately absent here rather than
    stubbed: a member with no canonicalizer would be a format the
    registry claims to support and cannot digest."""

    JSON_SCHEMA = "json_schema"
    OPENAPI = "openapi"
    ASYNCAPI = "asyncapi"
    SQL_MIGRATION_METADATA = "sql_migration_metadata"


#: The *enumerated* serialization differences each format's
#: canonicalization removes (`P13-REG-005a`). Recorded as data so the
#: claim is checkable, and so that widening it is a visible change rather
#: than a quiet one inside a function body.
REMOVED_DIFFERENCES: Mapping[SchemaFormat, tuple[str, ...]] = {
    SchemaFormat.JSON_SCHEMA: (
        "object key ordering",
        "insignificant whitespace",
        "non-ASCII escaping form",
    ),
    SchemaFormat.OPENAPI: (
        "object key ordering",
        "insignificant whitespace",
        "non-ASCII escaping form",
        "YAML-to-JSON projection of an equivalent document",
    ),
    SchemaFormat.ASYNCAPI: (
        "object key ordering",
        "insignificant whitespace",
        "non-ASCII escaping form",
        "YAML-to-JSON projection of an equivalent document",
    ),
    SchemaFormat.SQL_MIGRATION_METADATA: (
        "surrounding whitespace of the recorded statement digest",
    ),
}

#: What canonicalization explicitly does **not** do, for every format.
#: Stated as data for the same reason: a future contributor reading only
#: the code should not have to infer the limit from its absence.
NOT_NORMALIZED: tuple[str, ...] = (
    "semantic equivalence of differently-expressed constraints",
    "field renaming, however obviously synonymous",
    "default values expressed as an explicit value versus an omission",
    "enumeration ordering where the format assigns it meaning",
    "any difference the format itself treats as significant",
)


@dataclass(frozen=True, slots=True)
class CanonicalContent:
    """The canonical form of one schema document, plus its digest.

    Carries the format so that a digest can never be compared across
    formats by accident: two artifacts in different formats are two
    artifacts, whatever their bytes."""

    schema_format: SchemaFormat
    canonical_text: str
    digest: str

    def __post_init__(self) -> None:
        if not self.canonical_text:
            raise ValueError("canonical_text must not be empty")
        if len(self.digest) != 64:
            raise ValueError("digest must be a SHA-256 hex digest")


class UnsupportedSchemaFormatError(ValueError):
    """A format with no registered canonicalizer was presented.

    A distinct type rather than a generic `ValueError` so the registry
    can refuse the publication rather than silently digesting bytes with
    a canonicalizer that does not understand them."""


def _canonicalize_structured(document: Mapping[str, Any]) -> str:
    """Canonical JSON for a structured document.

    Delegates to the repository's existing `canonical_dumps`, which sorts
    keys, uses fixed separators and escapes non-ASCII, so two
    independently-built representations of the same document are
    byte-identical. This is the whole of the normalization for
    structured formats — no key renaming, no default expansion, no
    `$ref` resolution."""
    return canonical_dumps(document)


def _canonicalize_sql_migration_metadata(document: Mapping[str, Any]) -> str:
    """Canonical form for SQL migration metadata.

    Not a schema canonicalization at all: the metadata's identity is the
    migration ID, the statement digest and the ordering position, and
    those three are projected into a fixed, ordered form. The statements
    themselves are **not** normalized — an SQL normalizer that decided
    two statements were equivalent would be exactly the semantic claim
    `P13-REG-005b` forbids."""
    required = ("migration_id", "statement_digest", "ordering_position")
    missing = [field for field in required if field not in document]
    if missing:
        raise UnsupportedSchemaFormatError(
            f"SQL migration metadata requires {list(required)}; missing: {missing}"
        )
    projection = {
        "migration_id": str(document["migration_id"]).strip(),
        "ordering_position": int(document["ordering_position"]),
        "statement_digest": str(document["statement_digest"]).strip(),
    }
    return json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonicalize(schema_format: SchemaFormat, document: Mapping[str, Any]) -> CanonicalContent:
    """Produce the canonical form and digest of `document`.

    Dispatch is explicit per format, not table-driven over a shared
    "structured document" abstraction, because the SQL case genuinely is
    a different kind of object and hiding that behind one branch is how
    `P13-FMT-002` gets violated by a refactor."""
    if schema_format is SchemaFormat.SQL_MIGRATION_METADATA:
        canonical_text = _canonicalize_sql_migration_metadata(document)
    elif schema_format in (
        SchemaFormat.JSON_SCHEMA,
        SchemaFormat.OPENAPI,
        SchemaFormat.ASYNCAPI,
    ):
        canonical_text = _canonicalize_structured(document)
    else:  # pragma: no cover - StrEnum is closed; kept as a fail-closed default
        raise UnsupportedSchemaFormatError(
            f"no canonicalizer is registered for {schema_format!r}; publication is refused "
            f"rather than digested by a canonicalizer that does not understand the format"
        )
    return CanonicalContent(
        schema_format=schema_format,
        canonical_text=canonical_text,
        digest=content_digest(canonical_text),
    )


def digests_match(left: CanonicalContent, right: CanonicalContent) -> bool:
    """Whether two canonical contents are byte-identical after their own
    format's canonicalization.

    Named `digests_match` rather than `is_same_schema` deliberately. The
    answer to this function is a narrow content fact; whether two
    documents are the same *schema version* is a governance fact decided
    by a publication decision (`P13-REG-005c`), and no caller should be
    able to confuse the two by reading a method name."""
    if left.schema_format is not right.schema_format:
        return False
    return left.digest == right.digest


def validate_examples(
    document: Mapping[str, Any], examples: Sequence[Mapping[str, Any]]
) -> tuple[bool, tuple[str, ...]]:
    """Validate a JSON-Schema-shaped document's own example fixtures.

    Returns `(all_valid, failure_messages)` rather than raising, so the
    registry can attach the validation result to the publication decision
    (`P13-REG-008` requires the result to be *recorded*, not merely
    acted upon).

    Uses the repository's existing minimal validator, which supports a
    deliberately small JSON Schema subset. Where a schema uses a keyword
    the validator does not implement, the keyword is ignored rather than
    silently treated as satisfied — the same honest limitation
    `epd2_core.minimal_json_schema` documents for itself, restated here
    because a registry that over-claimed its validation would be worse
    than one that under-claimed it."""
    from epd2_core.minimal_json_schema import SchemaValidationError, validate

    failures: list[str] = []
    for index, example in enumerate(examples):
        try:
            validate(example, dict(document))
        except SchemaValidationError as exc:
            failures.append(f"example #{index}: {exc}")
    return (not failures, tuple(failures))

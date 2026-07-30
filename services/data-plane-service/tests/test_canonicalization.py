"""Format-specific canonicalization and the content digest
(PACK-13 §13; `P13-REG-005`).

The one sentence this file exists to keep honest: content identical after
the registry's format-specific canonicalization produces the same content
digest, and **digest equality does not itself define schema-version
identity**.
"""

from __future__ import annotations

import pytest
from _data_plane_builders import BASE_EXAMPLE, BASE_SCHEMA

from epd2_data_plane_service.canonicalization import (
    NOT_NORMALIZED,
    REMOVED_DIFFERENCES,
    SchemaFormat,
    UnsupportedSchemaFormatError,
    canonicalize,
    digests_match,
    validate_examples,
)


def test_key_ordering_does_not_change_the_digest() -> None:
    left = canonicalize(SchemaFormat.JSON_SCHEMA, {"a": 1, "b": 2})
    right = canonicalize(SchemaFormat.JSON_SCHEMA, {"b": 2, "a": 1})
    assert left.digest == right.digest
    assert digests_match(left, right)


def test_a_different_value_changes_the_digest() -> None:
    left = canonicalize(SchemaFormat.JSON_SCHEMA, {"a": 1})
    right = canonicalize(SchemaFormat.JSON_SCHEMA, {"a": 2})
    assert not digests_match(left, right)


def test_a_digest_is_never_compared_across_formats() -> None:
    """Two artifacts in different formats are two artifacts, whatever
    their bytes (`P13-FMT-002`)."""
    document = {"a": 1}
    json_schema = canonicalize(SchemaFormat.JSON_SCHEMA, document)
    openapi = canonicalize(SchemaFormat.OPENAPI, document)
    assert json_schema.digest == openapi.digest
    assert not digests_match(json_schema, openapi)


def test_canonicalization_is_deterministic_across_calls() -> None:
    first = canonicalize(SchemaFormat.JSON_SCHEMA, BASE_SCHEMA)
    second = canonicalize(SchemaFormat.JSON_SCHEMA, BASE_SCHEMA)
    assert first.canonical_text == second.canonical_text
    assert first.digest == second.digest


def test_sql_migration_metadata_has_its_own_canonical_form() -> None:
    """Its identity is the migration ID, the statement digest and the
    ordering position — not a schema diff (`P13-FMT-003`)."""
    content = canonicalize(
        SchemaFormat.SQL_MIGRATION_METADATA,
        {
            "migration_id": " 0001_add_scope ",
            "statement_digest": " abc ",
            "ordering_position": 1,
        },
    )
    assert "0001_add_scope" in content.canonical_text
    assert "  " not in content.canonical_text


def test_sql_migration_metadata_requires_its_three_fields() -> None:
    with pytest.raises(UnsupportedSchemaFormatError, match="migration_id"):
        canonicalize(SchemaFormat.SQL_MIGRATION_METADATA, {"migration_id": "x"})


def test_sql_statements_are_not_normalized() -> None:
    """An SQL normalizer deciding two statements are equivalent would be
    exactly the semantic claim `P13-REG-005b` forbids."""
    left = canonicalize(
        SchemaFormat.SQL_MIGRATION_METADATA,
        {"migration_id": "m", "statement_digest": "d1", "ordering_position": 1},
    )
    right = canonicalize(
        SchemaFormat.SQL_MIGRATION_METADATA,
        {"migration_id": "m", "statement_digest": "d2", "ordering_position": 1},
    )
    assert left.digest != right.digest


def test_every_format_enumerates_what_its_canonicalization_removes() -> None:
    """`P13-REG-005a`: the enumerated set is recorded per format, so
    widening it is a visible change."""
    for schema_format in SchemaFormat:
        assert schema_format in REMOVED_DIFFERENCES
        assert REMOVED_DIFFERENCES[schema_format]


def test_what_canonicalization_does_not_do_is_stated_as_data() -> None:
    assert "semantic equivalence of differently-expressed constraints" in NOT_NORMALIZED
    assert "field renaming, however obviously synonymous" in NOT_NORMALIZED


def test_valid_examples_validate() -> None:
    valid, failures = validate_examples(BASE_SCHEMA, [BASE_EXAMPLE])
    assert valid
    assert failures == ()


def test_an_invalid_example_is_reported_rather_than_raised() -> None:
    """`P13-REG-008` requires the result to be *recorded*, not merely
    acted upon."""
    valid, failures = validate_examples(BASE_SCHEMA, [{"membership_id": "not-a-uuid"}])
    assert not valid
    assert failures
    assert "example #0" in failures[0]


def test_a_canonical_content_requires_a_sha256_digest() -> None:
    from epd2_data_plane_service.canonicalization import CanonicalContent

    with pytest.raises(ValueError, match="SHA-256"):
        CanonicalContent(
            schema_format=SchemaFormat.JSON_SCHEMA, canonical_text="{}", digest="short"
        )


def test_an_empty_canonical_text_is_refused() -> None:
    from epd2_data_plane_service.canonicalization import CanonicalContent

    with pytest.raises(ValueError, match="must not be empty"):
        CanonicalContent(schema_format=SchemaFormat.JSON_SCHEMA, canonical_text="", digest="a" * 64)


def test_the_supported_formats_are_the_four_with_canonicalizers() -> None:
    """Protobuf and Avro are admissible as a future extension and are
    deliberately absent rather than stubbed: a member with no
    canonicalizer would be a format the registry claims to support and
    cannot digest."""
    assert {f.value for f in SchemaFormat} == {
        "json_schema",
        "openapi",
        "asyncapi",
        "sql_migration_metadata",
    }

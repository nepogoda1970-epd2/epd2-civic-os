"""Versioned schema registry (PACK-16D §50).

Every artefact that crosses a trust boundary has a named, versioned schema
with an explicit field list. Fields are split into *critical* and
*optional*: an unknown critical field is a hard rejection, because a
receiver that ignores a field it does not understand is a receiver that can
be told something it will not act on. An unknown field that is not declared
optional is also rejected — the registry has no "ignore the rest" mode.

Field *order* is normative and matches the canonical encoding, because the
canonical encoding never sorts (see ``crypto.encoding``). Changing an order
is a breaking change, not a formatting change.

There is deliberately no migration machinery here. Silent migration is
prohibited by §50; a schema change is a decision, and the registry can only
say whether a document matches a declared version.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from epd2_voting_service.reference.crypto.encoding import ENCODING_VERSION

REGISTRY_VERSION = "EPD2-SCHEMA-1"


class SchemaError(ValueError):
    reason_code = "INVALID_SCHEMA"


class UnknownSchemaError(SchemaError):
    reason_code = "UNSUPPORTED_PROFILE"


class UnknownCriticalFieldError(SchemaError):
    """An unrecognised field. Never ignored, never reinterpreted."""

    reason_code = "INVALID_SCHEMA"


class MissingCriticalFieldError(SchemaError):
    reason_code = "INVALID_SCHEMA"


@dataclass(frozen=True, slots=True)
class SchemaDescriptor:
    name: str
    version: str
    critical_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    #: Which earlier versions a consumer of this version may also read.
    backward_compatible_with: tuple[str, ...] = ()
    encoding_version: str = ENCODING_VERSION

    def validate(self, document: Mapping[str, object]) -> None:
        present = set(document)
        declared = set(self.critical_fields) | set(self.optional_fields)
        unknown = sorted(present - declared)
        if unknown:
            raise UnknownCriticalFieldError(
                f"{self.name}@{self.version}: unknown field(s) {unknown} — "
                "an unknown field is rejected, never ignored"
            )
        missing = sorted(set(self.critical_fields) - present)
        if missing:
            raise MissingCriticalFieldError(
                f"{self.name}@{self.version}: missing critical field(s) {missing}"
            )


def _s(
    name: str,
    critical: tuple[str, ...],
    optional: tuple[str, ...] = (),
) -> SchemaDescriptor:
    return SchemaDescriptor(
        name=name, version="1.0.0", critical_fields=critical, optional_fields=optional
    )


SCHEMA_REGISTRY: dict[str, SchemaDescriptor] = {
    d.name: d
    for d in (
        _s(
            "parameter_set",
            ("parameter_set_id", "profile_version", "p", "q", "g"),
            ("provenance", "production_use_permitted"),
        ),
        _s(
            "election_context",
            ("election_context_id", "manifest_digest", "parameter_set_id", "base_hash"),
        ),
        _s("manifest", ("election_context_id", "ballot_styles")),
        _s(
            "encrypted_ballot",
            (
                "ballot_id",
                "election_context_id",
                "ballot_style_id",
                "parameter_set_id",
                "manifest_digest",
                "contests",
            ),
        ),
        _s("spoiled_ballot", ("ballot_id", "nonces", "plaintexts")),
        _s(
            "receipt",
            ("ballot_id", "confirmation_code", "batch_window_id", "counted"),
            ("publication_obligation_id",),
        ),
        _s(
            "batch_commitment",
            (
                "election_context_id",
                "batch_sequence",
                "batch_window_id",
                "fixed_capacity_profile_id",
                "capacity",
                "commitment_root",
            ),
        ),
        _s("batch_opening", ("batch_sequence", "leaves", "openings")),
        _s(
            "reconciliation_record",
            ("accepted_cast", "public_challenged_spoiled", "cover", "E", "K", "A"),
        ),
        _s("board_entry", ("sequence", "entry_type", "payload")),
        _s(
            "checkpoint",
            ("checkpoint_sequence", "tree_size", "root", "previous_checkpoint_hash", "signature"),
        ),
        _s(
            "election_record",
            (
                "manifest",
                "params",
                "joint_public_key",
                "base_hash",
                "sealed_batches",
                "batch_openings",
                "accepted_ballots",
                "spoiled_ballots",
                "reconciliation",
                "tallies",
            ),
            ("shares", "ceremony", "threshold_shares"),
        ),
        _s(
            "verification_result",
            ("code", "exit_code", "checks_run", "not_checked"),
            ("detail", "warnings"),
        ),
    )
}


def get_schema(name: str, version: str = "1.0.0") -> SchemaDescriptor:
    descriptor = SCHEMA_REGISTRY.get(name)
    if descriptor is None:
        raise UnknownSchemaError(f"no schema named {name!r} in {REGISTRY_VERSION}")
    if version != descriptor.version and version not in descriptor.backward_compatible_with:
        raise UnknownSchemaError(
            f"{name}: version {version!r} is not {descriptor.version!r} and is not "
            "declared backward compatible; migration is never silent"
        )
    return descriptor


def validate_document(name: str, document: Mapping[str, object], version: str = "1.0.0") -> None:
    get_schema(name, version).validate(document)

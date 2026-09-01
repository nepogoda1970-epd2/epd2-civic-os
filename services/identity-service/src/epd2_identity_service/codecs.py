"""Safe serialization for the PACK-14 aggregates.

Persistence needs to turn frozen dataclasses into rows and back. Doing
that by hand for thirty aggregates would be thirty opportunities to drop
a field, and a dropped field in an identity aggregate is a security
control that silently stops being loaded.

So the codec is **driven by the dataclass's own type hints**. Encoding
walks the declared fields; decoding reconstructs from the same
declaration. A field added to an aggregate is persisted the moment it is
declared, and a field whose type the codec does not understand is a
loud `UnsupportedPersistedTypeError` rather than a silent `str()`.

Three rules this module exists to keep:

- **Typed identifiers survive the round trip.** `AccountId`,
  `CredentialId` and `SessionId` are `NewType`s over `UUID`; the codec
  resolves the supertype on the way out and re-applies the `NewType` on
  the way in, so a decoded aggregate type-checks exactly like a
  constructed one.
- **Timezone-aware timestamps stay timezone-aware.** Every `datetime`
  is stored as an ISO-8601 string with its offset. A naive datetime read
  back from a database would silently break every deadline calculation
  in `sessions` and `stepup`.
- **No secret is encodable.** The aggregates hold `HashedSecret`
  digests, never values, and `encode_value` refuses `bytes` outright -
  the one Python type a raw key or salt would arrive as.
"""

from __future__ import annotations

import types
import typing
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, TypeVar, get_args, get_origin
from uuid import UUID

from epd2_identity_service.exceptions import UnsupportedPersistedTypeError

T = TypeVar("T")

#: Resolved once per dataclass, because `get_type_hints` is expensive and
#: every aggregate is decoded on every read.
_HINT_CACHE: dict[type, dict[str, Any]] = {}


def _hints(cls: type) -> dict[str, Any]:
    cached = _HINT_CACHE.get(cls)
    if cached is None:
        module = __import__(cls.__module__, fromlist=["*"])
        cached = typing.get_type_hints(cls, vars(module))
        _HINT_CACHE[cls] = cached
    return cached


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """Return `(inner, optional)` for `X | None`, else `(annotation, False)`."""
    origin = get_origin(annotation)
    if origin is types.UnionType or origin is typing.Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0], True
        raise UnsupportedPersistedTypeError(
            f"only `X | None` unions are persistable, not {annotation!r}"
        )
    return annotation, False


def _resolve_newtype(annotation: Any) -> Any:
    """`AccountId` -> `UUID`. A `NewType` erases at runtime, so the codec
    persists its supertype and re-applies the alias on decode."""
    supertype = getattr(annotation, "__supertype__", None)
    return supertype if supertype is not None else annotation


def encode_value(value: Any) -> Any:
    """Encode one value into JSON-compatible data.

    `bytes` is refused deliberately: it is the shape a raw key, salt or
    seed would arrive in, and none of those belongs in a persisted
    aggregate. Every secret this package holds is already a
    `HashedSecret`, which encodes as its digest and its algorithm label.
    """
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, bytes | bytearray | memoryview):
        raise UnsupportedPersistedTypeError(
            "raw bytes are never persisted by this package; secrets are held as digests"
        )
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise UnsupportedPersistedTypeError("a naive datetime is never persisted")
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if is_dataclass(value) and not isinstance(value, type):
        return encode_dataclass(value)
    if isinstance(value, frozenset | set):
        return sorted(encode_value(item) for item in value)
    if isinstance(value, tuple | list):
        return [encode_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): encode_value(item) for key, item in value.items()}
    raise UnsupportedPersistedTypeError(f"no encoding is defined for {type(value)!r}")


def encode_dataclass(instance: Any) -> dict[str, Any]:
    return {field.name: encode_value(getattr(instance, field.name)) for field in fields(instance)}


def decode_value(annotation: Any, raw: Any) -> Any:
    """Decode one value back into the type the dataclass declares."""
    annotation, optional = _unwrap_optional(annotation)
    if raw is None:
        if not optional:
            raise UnsupportedPersistedTypeError(
                f"a stored null cannot be decoded into non-optional {annotation!r}"
            )
        return None
    annotation = _resolve_newtype(annotation)

    origin = get_origin(annotation)
    if origin in (tuple, list):
        (item_type, *rest) = get_args(annotation) or (Any,)
        if rest and rest != [Ellipsis]:
            raise UnsupportedPersistedTypeError(
                f"only homogeneous tuples are persistable, not {annotation!r}"
            )
        decoded = [decode_value(item_type, item) for item in raw]
        return tuple(decoded) if origin is tuple else decoded
    if origin in (frozenset, set):
        (item_type,) = get_args(annotation) or (Any,)
        decoded_items = {decode_value(item_type, item) for item in raw}
        return frozenset(decoded_items) if origin is frozenset else decoded_items
    if origin is dict:
        key_type, item_type = get_args(annotation) or (str, Any)
        return {
            decode_value(key_type, key): decode_value(item_type, item) for key, item in raw.items()
        }

    if isinstance(annotation, type):
        if issubclass(annotation, StrEnum):
            return annotation(raw)
        if issubclass(annotation, bool):
            return bool(raw)
        if issubclass(annotation, UUID):
            return UUID(raw)
        if issubclass(annotation, datetime):
            moment = datetime.fromisoformat(raw)
            if moment.tzinfo is None:
                raise UnsupportedPersistedTypeError("a stored timestamp lost its offset")
            return moment
        if issubclass(annotation, timedelta):
            return timedelta(seconds=raw)
        if is_dataclass(annotation):
            return decode_dataclass(annotation, raw)
        if issubclass(annotation, int | str):
            return annotation(raw)
    if annotation is Any:
        return raw
    raise UnsupportedPersistedTypeError(f"no decoding is defined for {annotation!r}")


def decode_dataclass(cls: type[T], raw: dict[str, Any]) -> T:  # noqa: UP047 - PEP 695 generics are not parsed by the pinned mypy
    hints = _hints(cls)
    kwargs: dict[str, Any] = {}
    for field in fields(cls):  # type: ignore[arg-type]
        if field.name not in raw:
            raise UnsupportedPersistedTypeError(
                f"stored {cls.__name__} row is missing field {field.name!r}; "
                "a migration is required before it can be read"
            )
        kwargs[field.name] = decode_value(hints[field.name], raw[field.name])
    return cls(**kwargs)


def identifier_text(value: UUID | str) -> str:
    """The canonical column form of a typed identifier.

    A single helper so every table stores the same textual form: a UUID
    is lower-case hyphenated, an opaque reference is itself. Two
    spellings of one identifier in two tables is a join that silently
    returns nothing.
    """
    return str(value)

"""Minimal canonical identifier helpers.

Per docs/canonical/TZ-00-domain-event-canon.md, section 6 ("Canonical
identifiers"): every object receives a global identifier in UUID format,
and an identifier must not encode meaning. This module only provides
generation and validation of such identifiers - it does not attach them to
any domain entity.
"""

from uuid import UUID, uuid4


def generate_uuid() -> UUID:
    """Generate a new random (UUID4) canonical identifier.

    Accepts no external parameters, so no meaning can be encoded into the
    identifier by a caller.
    """
    return uuid4()


def is_valid_uuid(value: str) -> bool:
    """Return True if `value` is a syntactically valid UUID string.

    Never raises for an invalid or empty string; only accepts a string
    argument.
    """
    if not isinstance(value, str) or not value:
        return False
    try:
        UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True

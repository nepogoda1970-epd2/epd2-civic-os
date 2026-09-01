"""EPD2 Civic OS shared Python infrastructure package.

This package intentionally contains no business logic — only
infrastructure-level version constants, canonical identifier helpers, the
canonical event envelope, a dependency-injected clock, canonical JSON
serialization, a reason-code registry loader, and a minimal JSON Schema
validator, shared across future EPD2 Civic OS services. See
CLAUDE-PACK-02 section 4.2 for what is and is not allowed in this package.
"""

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

__all__ = ["CANON_VERSION", "REPOSITORY_VERSION"]

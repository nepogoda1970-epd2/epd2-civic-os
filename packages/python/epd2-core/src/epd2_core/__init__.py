"""EPD2 Civic OS shared Python infrastructure package.

This package intentionally contains no business logic — only
infrastructure-level version constants and canonical identifier helpers,
shared across future EPD2 Civic OS services.
"""

from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION

__all__ = ["CANON_VERSION", "REPOSITORY_VERSION"]

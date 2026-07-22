"""Canon and repository version constants.

CANON_VERSION must stay in sync with:
- docs/canonical/canon-version.json (`canon_version`)
- packages/typescript/epd2-types/src/version.ts (`CANON_VERSION`)

REPOSITORY_VERSION must stay in sync with:
- packages/typescript/epd2-types/src/version.ts (`REPOSITORY_VERSION`)
- the latest entry in CHANGELOG.md

Consistency across all of the above is enforced by
scripts/verify_versions.py.
"""

CANON_VERSION = "0.1.0"
REPOSITORY_VERSION = "0.2.0"

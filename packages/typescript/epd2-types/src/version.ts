/**
 * Canon and repository version constants.
 *
 * CANON_VERSION must stay in sync with:
 * - docs/canonical/canon-version.json (`canon_version`)
 * - packages/python/epd2-core/src/epd2_core/version.py (`CANON_VERSION`)
 *
 * REPOSITORY_VERSION must stay in sync with:
 * - packages/python/epd2-core/src/epd2_core/version.py (`REPOSITORY_VERSION`)
 * - the latest entry in CHANGELOG.md
 *
 * Consistency across all of the above is enforced by
 * scripts/verify_versions.py.
 */

export const CANON_VERSION = "0.4.0";
export const REPOSITORY_VERSION = "0.5.0";

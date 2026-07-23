from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION


def test_canon_version_is_semver_like_string() -> None:
    assert isinstance(CANON_VERSION, str)
    parts = CANON_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_repository_version_is_semver_like_string() -> None:
    assert isinstance(REPOSITORY_VERSION, str)
    parts = REPOSITORY_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_current_versions_match_expected_skeleton_version() -> None:
    # CANON_VERSION moved 0.1.0 -> 0.2.0 per ADR-010 (accepted with
    # amendment): Ballot.challenge_window_hours and
    # ResultPublication.challenge_deadline_at, a backward-compatible
    # (minor) canon addition per canon section 25. CANON_VERSION is
    # unchanged by CLAUDE-PACK-03 (no further canon edit was made).
    # CANON_VERSION moved 0.2.0 -> 0.3.0 per ADR-013 (accepted with
    # amendments): new canon section 19a (Transparency Context) defining
    # PublicLedgerEntry, AuditExportPackage, DisclosurePolicy,
    # LobbyLogEntry, a new section 20.14 event catalog, and four new
    # section 22 ownership-matrix rows - a backward-compatible (minor)
    # canon addition per canon section 25. That earlier round was a
    # canon-only change for CLAUDE-PACK-04 governance; no
    # transparency-service code existed yet, so REPOSITORY_VERSION stayed
    # unchanged at the time.
    # REPOSITORY_VERSION moved 0.2.0 -> 0.3.0 for CLAUDE-PACK-03
    # (Participation and Decision Kernel): six new services, no canon
    # change of its own.
    # REPOSITORY_VERSION moved 0.3.0 -> 0.4.0 for CLAUDE-PACK-04
    # (Transparency Context): implements transparency-service
    # (PublicLedgerEntry/AuditExportPackage/DisclosurePolicy/
    # LobbyLogEntry) against the already-accepted canon 0.3.0 text and
    # ADR-011 through ADR-015 - no further canon edit was made, so
    # CANON_VERSION is unchanged.
    assert CANON_VERSION == "0.3.0"
    assert REPOSITORY_VERSION == "0.4.0"

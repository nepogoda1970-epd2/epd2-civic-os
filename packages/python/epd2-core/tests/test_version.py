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
    # CANON_VERSION moved 0.3.0 -> 0.4.0 per ADR-018 and ADR-020
    # (both accepted with amendments): new canon section 19b (Governance
    # Context) defining GovernancePolicy, GovernanceDecision,
    # TechnicalChallenge, and integrating the already-existing
    # RoleAssignment (8.4); a new section 20.15 event catalog; three new
    # section 22 ownership-matrix rows; and the reworded/extended section
    # 23 forbidden-link entries (AdministratorRole generalized to any
    # RoleAssignment role_code) - a backward-compatible (minor) canon
    # addition per canon section 25. This round was a canon-only change
    # for CLAUDE-PACK-05 governance; no governance-service code existed
    # yet, so REPOSITORY_VERSION was unchanged at the time.
    # REPOSITORY_VERSION moved 0.4.0 -> 0.5.0 for CLAUDE-PACK-05
    # (Governance Context): implements governance-service
    # (RoleAssignment/GovernancePolicy/GovernanceDecision/
    # TechnicalChallenge) against the already-accepted canon 0.4.0 text
    # and ADR-016 through ADR-020 - no further canon edit was made, so
    # CANON_VERSION is unchanged at that point.
    # CANON_VERSION moved 0.4.0 -> 0.5.0 per ADR-023 and ADR-025 (both
    # accepted with amendments): new canon section 19c (AI Processing
    # Context, an extension of the already-existing section 17) adding
    # AIProcessingRecord.processing_status (six values, no stored
    # superseded), supersedes_ai_processing_record_id (a unified,
    # derived-at-read-time supersession mechanism covering both a
    # superseded processing run and a superseded review outcome), the
    # canonical embedded redaction_manifest value object (nine sub-fields),
    # the disclosure-lifecycle fields plus the derived DisclosureStatus
    # read model, and AIDisclosurePackage as a contract/value object (not
    # a canonical system-of-record entity); a corrected/expanded section
    # 20.12 AI event catalog (ai.output.corrected -> ai.output_corrected,
    # plus six new events); and new section 23 forbidden-link entries - a
    # backward-compatible (minor) canon addition per canon section 25.
    # This round is a canon-only change for CLAUDE-PACK-06 governance; no
    # ai-processing-service code exists yet, so REPOSITORY_VERSION is
    # unchanged at 0.5.0 (both versions now coincidentally match, as they
    # did transiently around PACK-04/PACK-05, but remain tracked
    # independently).
    # REPOSITORY_VERSION moved 0.5.0 -> 0.6.0 for CLAUDE-PACK-06 (AI
    # Processing Context): implements ai-processing-service
    # (AIProcessingRecord/RedactionManifest/AIDisclosurePackage) against
    # the already-accepted canon 0.5.0 text and ADR-021 through ADR-025 -
    # no further canon edit was made, so CANON_VERSION is unchanged at
    # 0.5.0.
    assert CANON_VERSION == "0.5.0"
    assert REPOSITORY_VERSION == "0.6.0"

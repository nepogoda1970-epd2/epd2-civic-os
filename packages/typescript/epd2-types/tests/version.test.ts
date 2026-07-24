import assert from "node:assert/strict";
import { test } from "node:test";

import { CANON_VERSION, REPOSITORY_VERSION } from "../src/version.js";

test("CANON_VERSION is a semver-like string", () => {
  assert.equal(typeof CANON_VERSION, "string");
  const parts = CANON_VERSION.split(".");
  assert.equal(parts.length, 3);
  for (const part of parts) {
    assert.ok(/^\d+$/.test(part), `expected numeric segment, got "${part}"`);
  }
});

test("REPOSITORY_VERSION is a semver-like string", () => {
  assert.equal(typeof REPOSITORY_VERSION, "string");
  const parts = REPOSITORY_VERSION.split(".");
  assert.equal(parts.length, 3);
  for (const part of parts) {
    assert.ok(/^\d+$/.test(part), `expected numeric segment, got "${part}"`);
  }
});

test("current versions match the expected skeleton version", () => {
  // CANON_VERSION moved 0.1.0 -> 0.2.0 per ADR-010 (accepted with
  // amendment): Ballot.challenge_window_hours and
  // ResultPublication.challenge_deadline_at, a backward-compatible
  // (minor) canon addition per canon section 25. CANON_VERSION is
  // unchanged by CLAUDE-PACK-03 (no further canon edit was made).
  // CANON_VERSION moved 0.2.0 -> 0.3.0 per ADR-013 (accepted with
  // amendments): new canon section 19a (Transparency Context) defining
  // PublicLedgerEntry, AuditExportPackage, DisclosurePolicy,
  // LobbyLogEntry, a new section 20.14 event catalog, and four new
  // section 22 ownership-matrix rows - a backward-compatible (minor)
  // canon addition per canon section 25. That earlier round was a
  // canon-only change for CLAUDE-PACK-04 governance; no
  // transparency-service code existed yet, so REPOSITORY_VERSION stayed
  // unchanged at the time.
  // REPOSITORY_VERSION moved 0.2.0 -> 0.3.0 for CLAUDE-PACK-03
  // (Participation and Decision Kernel): six new services, no canon
  // change of its own.
  // REPOSITORY_VERSION moved 0.3.0 -> 0.4.0 for CLAUDE-PACK-04
  // (Transparency Context): implements transparency-service
  // (PublicLedgerEntry/AuditExportPackage/DisclosurePolicy/
  // LobbyLogEntry) against the already-accepted canon 0.3.0 text and
  // ADR-011 through ADR-015 - no further canon edit was made, so
  // CANON_VERSION is unchanged.
  // CANON_VERSION moved 0.3.0 -> 0.4.0 per ADR-018 and ADR-020 (both
  // accepted with amendments): new canon section 19b (Governance
  // Context) defining GovernancePolicy, GovernanceDecision,
  // TechnicalChallenge, and integrating the already-existing
  // RoleAssignment (8.4); a new section 20.15 event catalog; three new
  // section 22 ownership-matrix rows; and the reworded/extended section
  // 23 forbidden-link entries (AdministratorRole generalized to any
  // RoleAssignment role_code) - a backward-compatible (minor) canon
  // addition per canon section 25. This round was a canon-only change
  // for CLAUDE-PACK-05 governance; no governance-service code existed
  // yet, so REPOSITORY_VERSION was unchanged at the time.
  // REPOSITORY_VERSION moved 0.4.0 -> 0.5.0 for CLAUDE-PACK-05
  // (Governance Context): implements governance-service
  // (RoleAssignment/GovernancePolicy/GovernanceDecision/
  // TechnicalChallenge) against the already-accepted canon 0.4.0 text
  // and ADR-016 through ADR-020 - no further canon edit was made, so
  // CANON_VERSION is unchanged.
  assert.equal(CANON_VERSION, "0.4.0");
  assert.equal(REPOSITORY_VERSION, "0.5.0");
});

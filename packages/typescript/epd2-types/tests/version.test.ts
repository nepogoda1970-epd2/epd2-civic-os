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
  // REPOSITORY_VERSION moved 0.2.0 -> 0.3.0 for CLAUDE-PACK-03
  // (Participation and Decision Kernel): six new services, no canon
  // change of its own.
  assert.equal(CANON_VERSION, "0.2.0");
  assert.equal(REPOSITORY_VERSION, "0.3.0");
});

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
  assert.equal(CANON_VERSION, "0.1.0");
  assert.equal(REPOSITORY_VERSION, "0.2.0");
});

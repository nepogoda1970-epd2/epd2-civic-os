import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

// PACK-08 frontend vertical slice smoke tests — same dependency-free,
// source-reading style as tests/smoke.test.ts: no running server or React
// test renderer is available in this sandbox, so these tests read the page
// source directly rather than render it.

const here = dirname(fileURLToPath(import.meta.url));
const appDir = join(here, "..", "app", "organizations");

function read(relativePath: string): string {
  return readFileSync(join(appDir, relativePath), "utf-8");
}

test("organization browser page has the required German-authoritative heading", () => {
  const source = read("page.tsx");
  assert.match(source, /LABELS\.organizationsHeading/);
  assert.match(source, /<h1>/);
});

test("organization browser page does not call any backend or render a <form>", () => {
  for (const file of [
    "page.tsx",
    "[id]/page.tsx",
    "dev-authorization-console/page.tsx",
  ]) {
    const source = read(file);
    assert.doesNotMatch(source, /fetch\(/, `${file} must not call fetch()`);
    assert.doesNotMatch(source, /<form/i, `${file} must not render a <form>`);
  }
});

test("organization detail page renders relations, authorities, and an as-of selector", () => {
  const source = read("[id]/page.tsx");
  assert.match(source, /LABELS\.relationsHeading/);
  assert.match(source, /LABELS\.authoritiesHeading/);
  assert.match(source, /AsOfSelector/);
});

test("as-of selector resolves historical status from static sample data only, no API", () => {
  const source = read("AsOfSelector.tsx");
  assert.match(source, /"use client"/);
  assert.doesNotMatch(source, /fetch\(/);
});

test("dev authorization console is clearly labeled development-only and not wired to a backend", () => {
  const source = read("dev-authorization-console/page.tsx");
  assert.match(source, /LABELS\.devConsoleBanner/);
  assert.match(source, /checkSampleRegionalScopeAccess/);
  assert.doesNotMatch(source, /fetch\(/);
});

test("authorization check defaults to deny when no sample grant matches", async () => {
  const { checkSampleRegionalScopeAccess } =
    await import("../app/organizations/authorization.ts");
  const result = checkSampleRegionalScopeAccess({
    subjectReference: "does-not-exist",
    scopeType: "organization_scope",
    scopeReference: "00000000-0000-0000-0000-000000000001",
    actionCode: "administer_organization",
    asOf: new Date().toISOString(),
  });
  assert.equal(result.allowed, false);
  assert.equal(result.reasonCode, "CROSS_SCOPE_ACCESS_DENIED");
  assert.equal(result.mode, null);
});

test("authorization check allows a subject with a matching, currently-valid sample grant", async () => {
  const { checkSampleRegionalScopeAccess } =
    await import("../app/organizations/authorization.ts");
  const result = checkSampleRegionalScopeAccess({
    subjectReference: "30000000-0000-0000-0000-000000000001",
    scopeType: "organization_scope",
    scopeReference: "00000000-0000-0000-0000-000000000002",
    actionCode: "view_organizational_relation",
    asOf: "2026-07-25T00:00:00.000Z",
  });
  assert.equal(result.allowed, true);
  assert.equal(result.mode, "exact_scope");
});

test("authorization check denies a matching subject/scope/action outside the grant's validity window", async () => {
  const { checkSampleRegionalScopeAccess } =
    await import("../app/organizations/authorization.ts");
  const result = checkSampleRegionalScopeAccess({
    subjectReference: "30000000-0000-0000-0000-000000000004",
    scopeType: "organization_scope",
    scopeReference: "00000000-0000-0000-0000-000000000003",
    actionCode: "view_organizational_relation",
    asOf: "2027-01-01T00:00:00.000Z",
  });
  assert.equal(result.allowed, false);
});

test("statusAsOf resolves the status in effect at a historical date, not just the current one", async () => {
  const { statusAsOf } = await import("../app/organizations/data.ts");
  const history = [
    { status: "draft" as const, effective_from: "2024-02-15T00:00:00+00:00" },
    { status: "active" as const, effective_from: "2024-03-01T00:00:00+00:00" },
    {
      status: "restricted" as const,
      effective_from: "2026-05-01T00:00:00+00:00",
    },
  ];
  assert.equal(
    statusAsOf({ status_history: history }, "2024-03-15T00:00:00+00:00"),
    "active",
  );
  assert.equal(
    statusAsOf({ status_history: history }, "2024-02-20T00:00:00+00:00"),
    "draft",
  );
  assert.equal(
    statusAsOf({ status_history: history }, "2026-06-01T00:00:00+00:00"),
    "restricted",
  );
});

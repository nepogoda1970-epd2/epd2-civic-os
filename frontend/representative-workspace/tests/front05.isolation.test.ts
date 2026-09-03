import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

import {
  BROWSER_STORAGE_KINDS,
  PERMITTED_REQUEST_ORIGIN_CLASSES,
  WS04_BOUNDARY,
  WS04_DATA_CLASSES,
  WS04_ORIGIN,
  WS04_ROUTE_PREFIX,
  WS04_STORAGE_POLICY,
  WS04_WORKSPACE_ID,
  requestOriginClassPermitted,
  storageAllowed,
} from "../policies/workspace";
import {
  CONFIDENTIAL_FIELD_NAMES,
  ConfidentialityError,
  ERROR_REPORTING,
  FORBIDDEN_CORRELATION_IDENTIFIERS,
  SEARCH_POLICY,
  TELEMETRY_ALLOWED_FIELDS,
  TELEMETRY_FORBIDDEN_CONTENT,
  TELEMETRY_PLATFORM_CONNECTED,
  assertNoConfidentialContent,
  findConfidentialFields,
  findForbiddenCorrelationIdentifiers,
  searchScopePermitted,
  telemetryFieldPermitted,
  validateTelemetryEvent,
} from "../policies/confidentiality";

const HERE = resolve(import.meta.dirname, "..");

/* ------------------------------------------------------------------- workspace */

test("the workspace identity matches the accepted architecture record", () => {
  assert.equal(WS04_WORKSPACE_ID, "WS-04");
  assert.equal(WS04_ORIGIN, "https://represent.epd.example");
  assert.equal(WS04_ROUTE_PREFIX, "/representative");
  assert.equal(WS04_BOUNDARY.separateOrigin, true);
  assert.equal(WS04_BOUNDARY.votingDomainAccess, false);
  assert.equal(WS04_BOUNDARY.universalAdminMode, false);
  assert.deepEqual(
    [...WS04_DATA_CLASSES],
    ["MANDATE_INTERNAL", "CASE_CONFIDENTIAL", "PUBLIC_APPROVED"],
  );
});

test("every route in the app tree lives under the WS-04 prefix", () => {
  const routes = routeInventory();
  assert.ok(
    routes.length >= 8,
    `expected the full route set, got ${routes.length}`,
  );
  for (const route of routes) {
    assert.ok(
      route === "/" || route.startsWith(WS04_ROUTE_PREFIX),
      `route outside the WS-04 prefix: ${route}`,
    );
  }
});

/* --------------------------------------------------------------------- storage */

test("only the declared UI-preference purposes may use storage", () => {
  for (const kind of BROWSER_STORAGE_KINDS) {
    for (const purpose of WS04_STORAGE_POLICY.permittedPurposes) {
      const allowed = storageAllowed(kind, purpose);
      assert.equal(
        allowed,
        kind === "cookie" || kind === "localStorage",
        `${kind}/${purpose}`,
      );
    }
    // Any purpose outside the closed list is refused for every kind.
    for (const purpose of [
      "case_payload",
      "case_body",
      "correspondence",
      "draft",
      "analytics",
      "",
    ]) {
      assert.equal(storageAllowed(kind, purpose), false, `${kind}/${purpose}`);
    }
  }
});

test("no source file writes to a browser store", () => {
  const offenders: string[] = [];
  const patterns = [
    /\blocalStorage\s*\.\s*setItem/,
    /\bsessionStorage\s*\.\s*setItem/,
    /\bindexedDB\s*\.\s*open/,
    /\bdocument\s*\.\s*cookie\s*=/,
    /\bcaches\s*\.\s*open/,
    /navigator\s*\.\s*serviceWorker\s*\.\s*register/,
  ];
  for (const file of sourceFiles()) {
    const text = readFileSync(file, "utf8");
    for (const pattern of patterns) {
      if (pattern.test(text)) offenders.push(`${file}: ${pattern}`);
    }
  }
  assert.deepEqual(offenders, []);
});

test("this package registers no service worker and opens no cache", () => {
  // The policy record *declares* a service-worker position; that is a
  // declaration, not a registration, so it is the one permitted mention.
  assert.equal(WS04_STORAGE_POLICY.serviceWorkerRegisteredByThisPackage, false);
  const offenders: string[] = [];
  for (const file of sourceFiles()) {
    const text = readFileSync(file, "utf8");
    if (/serviceWorker\s*\.\s*register/.test(text)) offenders.push(file);
    if (/\bcaches\b/.test(text)) offenders.push(file);
    if (/serviceWorker/.test(text) && !file.endsWith("policies/workspace.ts")) {
      offenders.push(file);
    }
  }
  assert.deepEqual(offenders, []);
});

/* ------------------------------------------------------------- confidentiality */

test("confidential field names are detected wherever they appear", () => {
  for (const name of CONFIDENTIAL_FIELD_NAMES) {
    const payload = { outer: { [name]: "x" } };
    assert.ok(
      findConfidentialFields(payload).length > 0,
      `${name} not detected`,
    );
  }
});

test("a confidential payload is refused, not silently stripped", () => {
  assert.throws(
    () => assertNoConfidentialContent({ caseBody: "text" }, "telemetry"),
    ConfidentialityError,
  );
  // The safe payload passes through unchanged, by identity.
  const safe = { route: "/representative/desk" };
  assert.equal(assertNoConfidentialContent(safe, "telemetry"), safe);
});

test("forbidden correlation identifiers are detected", () => {
  for (const name of FORBIDDEN_CORRELATION_IDENTIFIERS) {
    assert.ok(
      findForbiddenCorrelationIdentifiers({ [name]: 1 }).length > 0,
      `${name} not detected`,
    );
  }
});

test("the confidentiality walker survives a cyclic payload", () => {
  const cyclic: Record<string, unknown> = { a: 1 };
  cyclic.self = cyclic;
  assert.deepEqual(findConfidentialFields(cyclic), []);
});

/* ------------------------------------------------------------------ telemetry */

test("no telemetry platform is connected and the allowlist is closed", () => {
  assert.equal(TELEMETRY_PLATFORM_CONNECTED, false);
  for (const field of TELEMETRY_ALLOWED_FIELDS) {
    assert.equal(telemetryFieldPermitted(field), true, field);
  }
  for (const field of TELEMETRY_FORBIDDEN_CONTENT) {
    assert.equal(telemetryFieldPermitted(field), false, field);
  }
});

test("telemetry fails closed while no platform is connected", () => {
  // Even an event built entirely from allowlisted fields is refused, because
  // the first condition is that a platform exists to receive it. That ordering
  // is the point: the allowlist is the second line, not the first.
  assert.equal(
    validateTelemetryEvent({ route_id: "representative.desk" }),
    false,
  );
  assert.equal(
    validateTelemetryEvent({ route_id: "representative.desk", case_body: "x" }),
    false,
  );
  assert.equal(validateTelemetryEvent({ subject: "Anliegen" }), false);
  assert.equal(validateTelemetryEvent(null), false);
  assert.equal(validateTelemetryEvent([]), false);
});

test("the allowlist would still exclude case content if a platform arrived", () => {
  // Exercised independently of the platform flag, so the constraint is proven
  // now rather than assumed to hold when the flag flips.
  const permitted = (event: Record<string, unknown>) =>
    Object.keys(event).every(telemetryFieldPermitted);
  assert.equal(permitted({ route_id: "x", locale: "de" }), true);
  assert.equal(permitted({ route_id: "x", case_body: "text" }), false);
  for (const field of TELEMETRY_FORBIDDEN_CONTENT) {
    assert.equal(permitted({ [field]: "x" }), false, field);
  }
});

test("error reporting is disabled and carries nothing sensitive", () => {
  assert.equal(ERROR_REPORTING.enabled, false);
  assert.equal(ERROR_REPORTING.carriesCaseContent, false);
  assert.equal(ERROR_REPORTING.carriesIdentity, false);
  assert.equal(ERROR_REPORTING.carriesCorrelationHandle, false);
  assert.equal(ERROR_REPORTING.carriesStackTraceToUser, false);
});

/* --------------------------------------------------------------------- search */

test("an unscoped or wildcard search scope is refused", () => {
  assert.equal(SEARCH_POLICY.crossMandateSearch, false);
  assert.equal(SEARCH_POLICY.personSearch, false);
  assert.equal(SEARCH_POLICY.enumerationPermitted, false);
  for (const scope of [null, "", "all", "*", "global"]) {
    assert.equal(searchScopePermitted(scope), false, String(scope));
  }
  assert.equal(searchScopePermitted("MANDAT-0001"), true);
});

/* ----------------------------------------------------------- request boundary */

test("only the declared request origin classes are permitted", () => {
  for (const value of PERMITTED_REQUEST_ORIGIN_CLASSES) {
    assert.equal(requestOriginClassPermitted(value), true, value);
  }
  for (const value of [
    "member_workspace",
    "voting_client",
    "third_party",
    "",
  ]) {
    assert.equal(requestOriginClassPermitted(value), false, value);
  }
});

test("no source file imports across the workspace package boundary", () => {
  const offenders: string[] = [];
  for (const file of sourceFiles()) {
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(/from\s+"([^"]+)"/g)) {
      const specifier = match[1];
      if (
        specifier.includes("web-shell") ||
        specifier.includes("voting-client") ||
        specifier.includes("../../../..//")
      ) {
        offenders.push(`${file}: ${specifier}`);
      }
    }
  }
  assert.deepEqual(offenders, []);
});

/* --------------------------------------------------------------------- helpers */

function sourceFiles(): string[] {
  const roots = [
    "app",
    "components",
    "content",
    "domain",
    "policies",
    "runtime",
  ];
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (/\.tsx?$/.test(entry)) out.push(full);
    }
  };
  for (const root of roots) walk(resolve(HERE, root));
  return out;
}

export function routeInventory(): string[] {
  const appDir = resolve(HERE, "app");
  const routes: string[] = [];
  const walk = (dir: string, prefix: string) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        walk(full, `${prefix}/${entry}`);
      } else if (entry === "page.tsx") {
        routes.push(prefix === "" ? "/" : prefix);
      }
    }
  };
  walk(appDir, "");
  return routes.sort();
}

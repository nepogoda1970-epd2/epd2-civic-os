import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  BROWSER_PERSISTENCE_KINDS,
  PERMITTED_REQUEST_ORIGIN_CLASSES,
  WS03_ISOLATION,
  WS03_ORIGIN,
  WS03_ROUTE_PREFIX,
  WS03_WORKSPACE_ID,
  requestOriginClassPermitted,
  storageAllowed,
} from "../policies/isolation";
import {
  FORBIDDEN_IDENTITY_FIELDS,
  ForbiddenIdentityError,
  assertNoIdentity,
  findForbiddenIdentityFields,
} from "../policies/identity";
import {
  PROHIBITED_TALLY_QUANTITIES,
  findProhibitedTallyQuantities,
  intermediateTallyAvailableFor,
} from "../policies/tally";
import {
  WS03_ERROR_REPORTING,
  telemetryPermitted,
  validateTelemetryEvent,
} from "../policies/telemetry";
import {
  SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES,
  SUPPORT_OPERATOR_PERMITTED_CAPABILITIES,
  mayChangeBallotSelections,
  mayConfirmConsequentialAction,
  mayViewBallotSelections,
  supportOperatorMay,
} from "../policies/supportRole";

const HERE = resolve(import.meta.dirname, "..");

function read(relative: string): string {
  return readFileSync(resolve(HERE, relative), "utf8");
}

const PRODUCTION_SOURCES = [
  "app/layout.tsx",
  "app/page.tsx",
  "app/not-found.tsx",
  "app/vote/layout.tsx",
  "app/vote/credential/page.tsx",
  "app/vote/ballot/page.tsx",
  "app/vote/review/page.tsx",
  "app/vote/receipt/page.tsx",
  "components/shell.tsx",
  "components/primitives.tsx",
  "components/assistance.tsx",
  "components/JourneyProvider.tsx",
  "components/CredentialSurface.tsx",
  "components/BallotSurface.tsx",
  "components/ReviewSurface.tsx",
  "components/ReceiptSurface.tsx",
  "domain/types.ts",
  "domain/handoff.ts",
  "domain/ballot.ts",
  "domain/receipt.ts",
  "domain/stateMachine.ts",
  "domain/capabilities.ts",
  "runtime/ports.ts",
  "runtime/unavailable.ts",
  "runtime/productionRuntime.ts",
  "runtime/compose.ts",
  "runtime/fixtureAbsent.ts",
  "policies/isolation.ts",
  "policies/identity.ts",
  "policies/telemetry.ts",
  "policies/tally.ts",
  "policies/supportRole.ts",
  "policies/visualBaseline.ts",
  "content/de.ts",
  "content/en.ts",
];

test("the workspace identity is exactly WS-03 on its own origin", () => {
  assert.equal(WS03_WORKSPACE_ID, "WS-03");
  assert.equal(WS03_ORIGIN, "https://vote.epd.example");
  assert.equal(WS03_ROUTE_PREFIX, "/vote");
});

test("the isolation posture keeps every accepted PACK-15 value", () => {
  assert.equal(WS03_ISOLATION.separateOrigin, true);
  assert.equal(WS03_ISOLATION.sharedCookies, false);
  assert.equal(WS03_ISOLATION.sharedLocalStorage, false);
  assert.equal(WS03_ISOLATION.sharedSessionStorage, false);
  assert.equal(WS03_ISOLATION.sharedIndexedDb, false);
  assert.equal(WS03_ISOLATION.sharedCacheStorage, false);
  assert.equal(WS03_ISOLATION.sharedServiceWorker, false);
  assert.equal(WS03_ISOLATION.ownServiceWorker, false);
  assert.equal(WS03_ISOLATION.identitySession, false);
  assert.equal(WS03_ISOLATION.memberSessionAccepted, false);
  assert.equal(WS03_ISOLATION.memberWorkspaceShell, false);
  assert.equal(WS03_ISOLATION.analytics, "none");
  assert.equal(WS03_ISOLATION.fingerprinting, false);
  assert.equal(WS03_ISOLATION.sharedTelemetry, false);
  assert.equal(WS03_ISOLATION.sharedErrorReportingIdentity, false);
  assert.equal(WS03_ISOLATION.thirdPartyScripts, "none");
  assert.equal(WS03_ISOLATION.thirdPartyFonts, "none");
  assert.equal(WS03_ISOLATION.referrerPolicy, "no-referrer");
  assert.equal(WS03_ISOLATION.cachePolicy, "no-store");
  assert.equal(WS03_ISOLATION.frameAncestors, "none");
  assert.equal(WS03_ISOLATION.persistentMemberIdentifier, false);
  assert.equal(WS03_ISOLATION.persistentVotingIdentifier, false);
  assert.equal(WS03_ISOLATION.credentialMaterialPersisted, false);
  assert.equal(WS03_ISOLATION.ballotStatePersisted, false);
  assert.equal(WS03_ISOLATION.intermediateTally, false);
  assert.equal(WS03_ISOLATION.s2sCredentialInBrowser, false);
  assert.equal(WS03_ISOLATION.reverseIdentityBridge, false);
});

test("no browser persistence kind is permitted, including unknown ones", () => {
  for (const kind of BROWSER_PERSISTENCE_KINDS) {
    assert.equal(storageAllowed(kind), false, kind);
  }
  assert.equal(storageAllowed("some-future-store"), false);
});

test("only same-origin document and static asset requests are permitted", () => {
  assert.deepEqual(
    [...PERMITTED_REQUEST_ORIGIN_CLASSES],
    ["ws03-same-origin-document", "ws03-same-origin-static-asset"],
  );
  assert.equal(requestOriginClassPermitted("third-party-script"), false);
  assert.equal(requestOriginClassPermitted("analytics-beacon"), false);
});

test("no production source touches browser persistence or measurement", () => {
  // The policy modules are allowed to *name* these mechanisms — naming them is
  // their job. What no source may do is *use* one, so the patterns below match
  // a call or a property access rather than a mention.
  for (const relative of PRODUCTION_SOURCES) {
    const source = read(relative);
    assert.doesNotMatch(source, /(^|[^.\w])localStorage\s*[.[]/m, relative);
    assert.doesNotMatch(source, /(^|[^.\w])sessionStorage\s*[.[]/m, relative);
    assert.doesNotMatch(source, /(^|[^.\w])indexedDB\s*[.[]/m, relative);
    assert.doesNotMatch(source, /document\s*\.\s*cookie/, relative);
    assert.doesNotMatch(source, /(^|[^.\w])caches\s*\./m, relative);
    assert.doesNotMatch(source, /navigator\s*\.\s*serviceWorker/, relative);
    assert.doesNotMatch(source, /navigator\s*\.\s*sendBeacon/, relative);
    assert.doesNotMatch(
      source,
      /gtag|googletagmanager|mixpanel|segment\.io|plausible|matomo/i,
      relative,
    );
  }
});

test("no production source makes a network call", () => {
  // Every WS-03 network capability is blocked, so a request anywhere in the
  // production tree would be a route this stage was not permitted to invent.
  for (const relative of PRODUCTION_SOURCES) {
    const source = read(relative);
    assert.doesNotMatch(source, /(^|[^.\w])fetch\s*\(/m, relative);
    assert.doesNotMatch(source, /XMLHttpRequest/, relative);
    assert.doesNotMatch(source, /new\s+WebSocket/, relative);
    assert.doesNotMatch(source, /new\s+EventSource/, relative);
  }
});

test("no production source carries service-to-service authority", () => {
  for (const relative of PRODUCTION_SOURCES) {
    const source = read(relative);
    // An actual header assignment, not the word in a comment or a policy field.
    assert.doesNotMatch(
      source,
      /["']?[Aa]uthorization["']?\s*:\s*[`"']/,
      relative,
    );
    assert.doesNotMatch(source, /client_secret\s*[:=]/i, relative);
    assert.doesNotMatch(source, /private_?[Kk]ey\s*[:=]\s*[`"']/, relative);
    assert.doesNotMatch(source, /BEGIN [A-Z ]*PRIVATE KEY/, relative);
    assert.doesNotMatch(source, /credentials\s*:\s*["']include["']/, relative);
  }
  // The one place API-03 may be named is the production adapter, which records
  // that no browser-side S2S authority exists at all.
  const adapter = read("runtime/productionRuntime.ts");
  assert.match(adapter, /s2sBearerCredential: false/);
  assert.match(adapter, /mtlsClientSecret: false/);
  assert.match(adapter, /servicePrivateKey: false/);
  assert.match(adapter, /memberSessionCookie: false/);
});

test("no production source imports the Member Workspace", () => {
  const importPattern =
    /from\s+["'][^"']*(web-shell|MemberWorkspace|WorkspaceShell)/;
  for (const relative of PRODUCTION_SOURCES) {
    assert.doesNotMatch(read(relative), importPattern, relative);
  }
});

test("production code does not import governed fixture data", () => {
  const staticImport = /^import[\s\S]*?from\s+["'][^"']*governedTestRuntime/m;
  for (const relative of PRODUCTION_SOURCES) {
    assert.doesNotMatch(read(relative), staticImport, relative);
  }
  // compose.ts reaches it only through a dynamic import behind the flag, and
  // next.config.ts replaces the module entirely unless the flag is set.
  const compose = read("runtime/compose.ts");
  assert.match(compose, /await import\("\.\/governedTestRuntime"\)/);
  assert.match(
    compose,
    /process\.env\.NEXT_PUBLIC_FRONT04_GOVERNED_TEST === "1"/,
  );
  const config = read("next.config.ts");
  assert.match(config, /NormalModuleReplacementPlugin/);
  assert.match(config, /fixtureAbsent\.ts/);
});

test("the forbidden identity vocabulary is enforced by a detector", () => {
  assert.ok(FORBIDDEN_IDENTITY_FIELDS.includes("member_id"));
  assert.ok(FORBIDDEN_IDENTITY_FIELDS.includes("account_reference"));
  assert.ok(FORBIDDEN_IDENTITY_FIELDS.includes("session_reference"));
  assert.deepEqual(
    findForbiddenIdentityFields({ a: { b: [{ member_id: 1 }] } }),
    ["member_id"],
  );
  assert.deepEqual(findForbiddenIdentityFields({ ok: true }), []);
  assert.throws(
    () => assertNoIdentity({ person_id: "x" }),
    ForbiddenIdentityError,
  );
  // The detector survives a cycle rather than hanging on one.
  const cyclic: Record<string, unknown> = { safe: 1 };
  cyclic.self = cyclic;
  assert.deepEqual(findForbiddenIdentityFields(cyclic), []);
});

test("intermediate tally quantities are refused for every role", () => {
  assert.ok(PROHIBITED_TALLY_QUANTITIES.includes("turnout"));
  assert.ok(PROHIBITED_TALLY_QUANTITIES.includes("accepted_ballot_count"));
  assert.ok(PROHIBITED_TALLY_QUANTITIES.includes("remaining_cast_entitlement"));
  assert.deepEqual(findProhibitedTallyQuantities({ x: { turnout: 3 } }), [
    "turnout",
  ]);
  for (const role of [
    "eligible_voter",
    "accessibility_support_operator",
    "admin",
    "root",
  ]) {
    assert.equal(intermediateTallyAvailableFor(role), false, role);
  }
});

test("telemetry and error reporting are off, not merely minimised", () => {
  assert.equal(telemetryPermitted(), false);
  assert.equal(validateTelemetryEvent({ event: "render" }), false);
  assert.equal(WS03_ERROR_REPORTING.enabled, false);
  assert.equal(WS03_ERROR_REPORTING.carriesIdentity, false);
  assert.equal(WS03_ERROR_REPORTING.carriesBallotMaterial, false);
  assert.equal(WS03_ERROR_REPORTING.carriesCorrelationHandle, false);
});

test("the support operator cannot become a second voter", () => {
  assert.equal(
    mayViewBallotSelections("accessibility_support_operator"),
    false,
  );
  assert.equal(
    mayChangeBallotSelections("accessibility_support_operator"),
    false,
  );
  assert.equal(
    mayConfirmConsequentialAction("accessibility_support_operator"),
    false,
  );
  assert.equal(mayViewBallotSelections("eligible_voter"), true);
  for (const capability of SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES) {
    assert.equal(supportOperatorMay(capability), false, capability);
  }
  for (const capability of SUPPORT_OPERATOR_PERMITTED_CAPABILITIES) {
    assert.equal(supportOperatorMay(capability), true, capability);
  }
  assert.equal(supportOperatorMay("invented_capability"), false);
});

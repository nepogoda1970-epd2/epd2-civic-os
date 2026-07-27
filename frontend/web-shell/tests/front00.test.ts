import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { ROUTES } from "../foundation/routes.ts";
import {
  MOBILE_CAPABILITIES,
  MOBILE_CLIENT_CHANNEL,
  MOBILE_DELIVERY_SEQUENCE,
  MOBILE_PUSH_POLICY,
  MOBILE_RETURN_STATUSES,
  MOBILE_SECURITY_PROFILE,
  MOBILE_SHARED_RUNTIME_STATE_PROHIBITED,
  MOBILE_VOTING_HANDOFF,
} from "../foundation/mobile-application-profile.ts";
import { storageAllowed } from "../foundation/storage-policy.ts";
import { validateTelemetryEvent } from "../foundation/telemetry-policy.ts";
import { PRESENTATION_STATES } from "../foundation/types.ts";
import { WORKSPACES } from "../foundation/workspaces.ts";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const read = (path: string) => readFileSync(join(root, path), "utf8");

test("declares exactly ten separate workspaces", () => {
  assert.equal(WORKSPACES.length, 10);
  assert.equal(new Set(WORKSPACES.map((workspace) => workspace.id)).size, 10);
  assert.equal(
    new Set(WORKSPACES.map((workspace) => workspace.originPlaceholder)).size,
    10,
  );
  assert.ok(
    WORKSPACES.every((workspace) => workspace.sessionSharing === "forbidden"),
  );
});

test("Voting Client policy forbids analytics and all browser storage", () => {
  const voting = WORKSPACES.find((workspace) => workspace.id === "WS-03");
  assert.equal(voting?.analytics, "none");
  assert.equal(voting?.browserStorage, "none");
  for (const kind of [
    "cookie",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "cacheStorage",
    "serviceWorker",
  ] as const) {
    assert.equal(storageAllowed("WS-03", kind, "technical-cache"), false);
  }
});

test("telemetry fails closed for Voting Client and sensitive identifiers", () => {
  assert.equal(validateTelemetryEvent("WS-03", { event: "render" }), false);
  assert.equal(
    validateTelemetryEvent("WS-01", { event: "render", globalUserId: "x" }),
    false,
  );
  assert.equal(validateTelemetryEvent("WS-01", { event: "render" }), true);
});

test("mandatory state catalogue is complete", () => {
  assert.equal(PRESENTATION_STATES.length, 19);
  for (const required of [
    "authority_missing",
    "scope_unresolved",
    "not_legally_activated",
    "requires_dual_control",
  ]) {
    assert.ok(
      PRESENTATION_STATES.includes(
        required as (typeof PRESENTATION_STATES)[number],
      ),
    );
  }
});

test("representative routes have explicit ownership, activation and backend dependency", () => {
  assert.equal(ROUTES.length, 5);
  for (const route of ROUTES) {
    assert.match(route.workspaceId, /^WS-\d{2}$/);
    assert.ok(route.status);
    assert.ok(route.backendDependency);
  }
});

test("shell and components include accessibility primitives", () => {
  const source = read("components/foundation.tsx");
  assert.match(source, /skip-link/);
  assert.match(source, /aria-label="Hauptnavigation"/);
  assert.match(source, /id="main-content"/);
  assert.match(source, /role="alert"/);
  assert.match(source, /aria-live/);
  assert.match(source, /aria-current/);
});

test("dialog uses native modal semantics and labelled heading", () => {
  const source = read("components/DialogExample.tsx");
  assert.match(source, /<dialog/);
  assert.match(source, /aria-labelledby="dialog-title"/);
  assert.match(source, /showModal/);
  assert.match(source, /onCancel/);
});

test("foundation does not claim PASS, production readiness or legal activation", () => {
  for (const path of [
    "foundation/workspaces.ts",
    "foundation/routes.ts",
    "components/foundation.tsx",
    "app/foundation/page.tsx",
    "app/foundation/examples/[kind]/page.tsx",
  ]) {
    const source = read(path);
    assert.doesNotMatch(
      source,
      /\bproduction-ready\b|\blegally activated\b|\bFINAL PASS\b/i,
    );
  }
});

test("FRONT-00 contains no API integration or global identity storage", () => {
  const sources = [
    read("foundation/storage-policy.ts"),
    read("foundation/telemetry-policy.ts"),
    read("app/foundation/examples/[kind]/page.tsx"),
  ].join("\n");
  assert.doesNotMatch(sources, /fetch\(|axios|globalIdentity|sharedSession/);
});

test("Mobile App is a client channel and does not change workspace or origin counts", () => {
  assert.equal(MOBILE_CLIENT_CHANNEL, "epd2-mobile-app");
  assert.equal(WORKSPACES.length, 10);
  assert.equal(
    new Set(WORKSPACES.map(({ originPlaceholder }) => originPlaceholder)).size,
    10,
  );
  assert.ok(WORKSPACES.every(({ id }) => !id.toLowerCase().includes("mobile")));
});

test("Mobile App capability scope is limited and privileged capabilities are prohibited", () => {
  const permitted = MOBILE_CAPABILITIES.filter(({ allowed }) => allowed);
  assert.ok(
    permitted.every(({ workspaceScope }) =>
      workspaceScope.every(
        (workspace) => workspace === "WS-02" || workspace === "WS-05",
      ),
    ),
  );
  assert.deepEqual(
    permitted
      .filter(({ workspaceScope }) => workspaceScope.includes("WS-05"))
      .map(({ capability }) => capability),
    ["citizen-office-request-status"],
  );
  for (const capability of [
    "representative-workspace",
    "institutional-administration",
    "employee-compliance-legal",
    "finance-workspace",
    "independent-oversight",
    "publication-administration",
    "privileged-administration",
    "certification",
    "tally-administration",
    "legal-decisions",
    "security-administration",
    "universal-admin",
  ]) {
    assert.equal(
      MOBILE_CAPABILITIES.find((entry) => entry.capability === capability)
        ?.allowed,
      false,
    );
  }
});

test("citizen-office request status is WS-05 and activation-gated by PACK-33", () => {
  const requestStatus = MOBILE_CAPABILITIES.find(
    ({ capability }) => capability === "citizen-office-request-status",
  );
  assert.deepEqual(requestStatus?.workspaceScope, ["WS-05"]);
  assert.equal(requestStatus?.dependentPack, "PACK-33");
  assert.notEqual(requestStatus?.dependentPack, "PACK-29");
});

test("Mobile voting requires isolated system-browser handoff", () => {
  assert.equal(MOBILE_VOTING_HANDOFF.votingInsideApp, false);
  assert.equal(MOBILE_VOTING_HANDOFF.embeddedWebView, "prohibited");
  assert.equal(MOBILE_VOTING_HANDOFF.userAgent, "system-browser-required");
  assert.equal(MOBILE_VOTING_HANDOFF.memberSessionTransfer, "prohibited");
  assert.equal(
    MOBILE_VOTING_HANDOFF.persistentMemberIdentifierTransfer,
    "prohibited",
  );
  assert.equal(MOBILE_VOTING_HANDOFF.sharedCookies, false);
  assert.equal(MOBILE_VOTING_HANDOFF.sharedLocalStorage, false);
  assert.equal(MOBILE_VOTING_HANDOFF.sharedIndexedDB, false);
  assert.equal(MOBILE_VOTING_HANDOFF.sharedAnalytics, false);
  assert.equal(MOBILE_VOTING_HANDOFF.sharedIdentitySession, false);
  assert.deepEqual(MOBILE_RETURN_STATUSES, [
    "completed",
    "cancelled",
    "expired",
    "failed",
  ]);
  assert.equal(MOBILE_VOTING_HANDOFF.return.containsBallotReference, false);
  assert.equal(MOBILE_VOTING_HANDOFF.return.containsVoteContent, false);
});

test("Mobile offline, push and production activation policies fail closed", () => {
  assert.equal(
    MOBILE_SECURITY_PROFILE.offlineConsequentialActions,
    "prohibited",
  );
  assert.equal(MOBILE_SECURITY_PROFILE.offlineCache.votingData, "prohibited");
  assert.equal(MOBILE_PUSH_POLICY.providerTrustedStorage, false);
  assert.equal(MOBILE_PUSH_POLICY.payload, "minimal-routing-and-status-only");
  assert.equal(MOBILE_SECURITY_PROFILE.productionImplemented, false);
  assert.ok(
    MOBILE_CAPABILITIES.every(
      ({ activationStatus }) =>
        activationStatus === "inactive-pending-pack-and-security-gates",
    ),
  );
  assert.deepEqual(MOBILE_DELIVERY_SEQUENCE, [
    "responsive-ws-02-web",
    "pwa-non-critical-capabilities-only",
    "native-app-after-api-and-security-stabilization",
  ]);
  assert.ok(
    MOBILE_SHARED_RUNTIME_STATE_PROHIBITED.includes("voting-credentials"),
  );
});

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import type { StorageKind } from "../foundation/storage-policy.ts";
import { storageAllowed } from "../foundation/storage-policy.ts";
import { validateTelemetryEvent } from "../foundation/telemetry-policy.ts";
import {
  ALLOWED_WS03_ORIGINS,
  PARTICIPATION_STATES,
  PROHIBITED_DELIVERY_CHANNELS,
  PROHIBITED_IDENTITY_SIDE_STATES,
  VOTING_ORIGIN_ISOLATION,
  credentialDeliveryPermitted,
  participationStateVisibleToIdentitySide,
} from "../foundation/voting-trust-policy.ts";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const read = (path: string) => readFileSync(join(root, path), "utf8");

const STORAGE_KINDS: readonly StorageKind[] = [
  "cookie",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "cacheStorage",
  "serviceWorker",
];

const RENDITION_SOURCES = [
  "components/voting-trust.tsx",
  "app/mitwirkung/abstimmungen/page.tsx",
  "app/vote/page.tsx",
];

test("voting-origin states are never visible on the identity side", () => {
  assert.ok(PROHIBITED_IDENTITY_SIDE_STATES.length > 0);
  for (const state of PROHIBITED_IDENTITY_SIDE_STATES) {
    assert.equal(participationStateVisibleToIdentitySide(state), false, state);
  }
  assert.equal(
    participationStateVisibleToIdentitySide("eligibility_confirmed"),
    true,
  );
  assert.equal(participationStateVisibleToIdentitySide("anything-else"), false);
});

test("the declared participation states contain no casting state", () => {
  for (const state of PARTICIPATION_STATES) {
    assert.ok(
      !PROHIBITED_IDENTITY_SIDE_STATES.includes(state.id),
      `prohibited state declared: ${state.id}`,
    );
    assert.ok(state.labelDe.length > 0);
    assert.ok(state.markerKind.length > 0);
  }
  assert.equal(
    new Set(PARTICIPATION_STATES.map((state) => state.id)).size,
    PARTICIPATION_STATES.length,
  );
});

test("access is deliverable only inside the isolated voting origin", () => {
  for (const channel of PROHIBITED_DELIVERY_CHANNELS) {
    assert.equal(credentialDeliveryPermitted(channel), false, channel);
  }
  assert.equal(credentialDeliveryPermitted("isolated_ws03_origin"), true);
  assert.equal(credentialDeliveryPermitted("assistant_hand_over"), false);
  assert.equal(credentialDeliveryPermitted(""), false);
  assert.deepEqual(ALLOWED_WS03_ORIGINS, ["https://vote.epd.example"]);
});

test("voting origin shares nothing with the identity origin", () => {
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedCookies, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedLocalStorage, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedSessionStorage, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedIndexedDb, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedServiceWorker, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.identitySession, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.analytics, "none");
  assert.equal(VOTING_ORIGIN_ISOLATION.fingerprinting, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedTelemetry, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.sharedErrorReportingIdentity, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.thirdPartyScripts, "none");
  assert.equal(VOTING_ORIGIN_ISOLATION.referrerPolicy, "no-referrer");
  assert.equal(VOTING_ORIGIN_ISOLATION.cachePolicy, "no-store");
  assert.equal(VOTING_ORIGIN_ISOLATION.frameAncestors, "none");
  assert.equal(VOTING_ORIGIN_ISOLATION.persistentMemberIdentifier, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.credentialMaterialPersisted, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.returnCarriesIdentityToken, false);
  assert.equal(VOTING_ORIGIN_ISOLATION.returnCarriesVotingIdentifier, false);
});

test("WS-03 permits no browser storage and no telemetry", () => {
  for (const kind of STORAGE_KINDS) {
    assert.equal(storageAllowed("WS-03", kind, "technical-cache"), false, kind);
  }
  assert.equal(validateTelemetryEvent("WS-03", { event: "render" }), false);
});

test("PACK-15 renditions carry no data access and no casting language", () => {
  for (const path of RENDITION_SOURCES) {
    const source = read(path);
    assert.doesNotMatch(source, /fetch\(/, path);
    assert.doesNotMatch(source, /localStorage/, path);
    assert.doesNotMatch(source, /sessionStorage/, path);
    assert.doesNotMatch(source, /indexedDB/, path);
    assert.doesNotMatch(source, /analytics/, path);
    for (const phrase of [
      "Sie haben abgestimmt",
      "Ihre Stimme wurde abgegeben",
      "Ballot status",
    ]) {
      assert.ok(!source.includes(phrase), `${path} contains "${phrase}"`);
    }
  }
});

test("the isolated voting origin does not use the member workspace shell", () => {
  const source = read("app/vote/page.tsx");
  assert.ok(!source.includes("WorkspaceShell"));
  assert.ok(source.includes("IsolatedVotingShell"));
});

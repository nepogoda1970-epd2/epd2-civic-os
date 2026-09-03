import assert from "node:assert/strict";
import test from "node:test";

import {
  ACCEPTED_IDENTITY_SIDE_ROUTE,
  ACCEPTED_LINEAGE,
  BROWSER_AUTHORITY,
  SPECIFICATION_ONLY_OPERATIONS,
  SPECIFICATION_SOURCE,
  createProductionRuntime,
} from "../runtime/productionRuntime";
import {
  PRODUCTION_REFUSALS,
  refusal,
  unavailable,
} from "../runtime/unavailable";
import { createGovernedTestRuntime } from "../runtime/governedTestRuntime";
import { createGovernedTestRuntime as absent } from "../runtime/fixtureAbsent";
import type { VotingContext } from "../domain/types";

const CONTEXT: VotingContext = {
  votingContextId: "ctx",
  audienceOrigin: "https://vote.epd.example",
  purpose: "voting_entry",
  expiresAt: "2026-09-01T12:02:00.000Z",
  role: "eligible_voter",
};

test("the adapter is pinned to the exact accepted lineage", () => {
  assert.equal(
    ACCEPTED_LINEAGE.api02C13Sha256,
    "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9",
  );
  assert.equal(ACCEPTED_LINEAGE.api02C13AcceptanceRun, 33497989489);
  assert.equal(ACCEPTED_LINEAGE.api02C13AcceptanceJob, 99824485228);
  assert.equal(
    ACCEPTED_LINEAGE.front03C1Sha256,
    "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26",
  );
  assert.equal(ACCEPTED_LINEAGE.front03C1AcceptanceRun, 33528038712);
  assert.equal(
    ACCEPTED_LINEAGE.front02C21Sha256,
    "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179",
  );
  assert.equal(
    ACCEPTED_LINEAGE.enteringCanonicalMain,
    "c333b9dd12e0c13dd402222cc958d95e779b8488",
  );
});

test("the one accepted voting route is recorded as not callable from WS-03", () => {
  assert.equal(ACCEPTED_IDENTITY_SIDE_ROUTE.method, "POST");
  assert.equal(
    ACCEPTED_IDENTITY_SIDE_ROUTE.path,
    "/api/v1/identity/voting-handoff",
  );
  assert.equal(ACCEPTED_IDENTITY_SIDE_ROUTE.callableFromWs03, false);
  assert.equal(ACCEPTED_IDENTITY_SIDE_ROUTE.ingressClass, "MEMBER");
});

test("the specification-only operations are named and are not treated as runtime", () => {
  assert.equal(SPECIFICATION_ONLY_OPERATIONS.length, 10);
  for (const operation of SPECIFICATION_ONLY_OPERATIONS) {
    assert.match(operation, /^(GET|POST) \/elections\//);
  }
  assert.match(SPECIFICATION_SOURCE, /PACK-16C-API-CATALOG\.md/);
  assert.match(SPECIFICATION_SOURCE, /no endpoint is implemented/);
});

test("the browser holds no service-to-service authority of any kind", () => {
  for (const [name, held] of Object.entries(BROWSER_AUTHORITY)) {
    assert.equal(held, false, name);
  }
});

test("every production port returns a controlled unavailability", async () => {
  const runtime = createProductionRuntime();
  assert.equal(runtime.profile, "production");
  const results = [
    await runtime.handoff.consume({}),
    await runtime.electionManifest.read(CONTEXT),
    await runtime.ballotStyle.read(CONTEXT),
    await runtime.crypto.prepareEnvelope(CONTEXT, {
      ballotStyleId: "",
      selections: [],
    }),
    await runtime.submission.submit(CONTEXT, "final_cast", "token"),
    await runtime.submission.status(CONTEXT, "token"),
    await runtime.receipt.readReceipt("ABCDEFGH"),
    await runtime.receipt.confirmRecordedAsCast("ABCDEFGH"),
  ];
  for (const result of results) {
    assert.equal(result.ok, false);
    if (result.ok) continue;
    assert.match(result.error.reasonCode, /^WS03_/);
    assert.ok(result.error.safeMessage.length > 10);
    assert.ok(result.error.nextSafeAction.length > 10);
    assert.ok(
      ["committed", "not_committed", "unknown"].includes(
        result.error.commitKnowledge,
      ),
    );
  }
});

test("a submission refusal never claims something was committed", async () => {
  const runtime = createProductionRuntime();
  const submitted = await runtime.submission.submit(CONTEXT, "final_cast", "t");
  assert.equal(submitted.ok, false);
  if (submitted.ok) return;
  assert.equal(submitted.error.commitKnowledge, "not_committed");
  assert.equal(submitted.error.entitlementKnownIntact, true);
  assert.match(
    submitted.error.safeMessage,
    /nichts abgegeben und nichts gezählt/,
  );
});

test("a status refusal is honest that the outcome is unknown", async () => {
  const runtime = createProductionRuntime();
  const status = await runtime.submission.status(CONTEXT, "t");
  assert.equal(status.ok, false);
  if (status.ok) return;
  assert.equal(status.error.commitKnowledge, "unknown");
  assert.equal(status.error.entitlementKnownIntact, false);
});

test("every production refusal names its exact missing dependency", () => {
  const codes = Object.values(PRODUCTION_REFUSALS).map((r) => r.reasonCode);
  assert.equal(new Set(codes).size, codes.length);
  for (const code of codes) {
    assert.match(code, /^WS03_[A-Z_]+$/);
  }
  assert.ok(codes.includes("WS03_BALLOT_CRYPTO_RUNTIME_BLOCKED"));
  assert.ok(codes.includes("WS03_BALLOT_SUBMISSION_CONTRACT_NOT_ACCEPTED"));
});

test("a refusal is frozen so a caller cannot soften it", () => {
  const value = refusal(PRODUCTION_REFUSALS.crypto);
  assert.equal(Object.isFrozen(value), true);
  const before = value.safeMessage;
  try {
    (value as { safeMessage: string }).safeMessage = "Alles in Ordnung";
  } catch {
    // Strict mode throws; sloppy mode ignores. Either way the value must hold.
  }
  assert.equal(value.safeMessage, before);
  const wrapped = unavailable<never>(PRODUCTION_REFUSALS.crypto);
  assert.equal(wrapped.ok, false);
});

test("the governed test profile supplies presentation only, never an outcome", async () => {
  const runtime = createGovernedTestRuntime();
  assert.equal(runtime.profile, "governed_test");
  const context = await runtime.handoff.consume(null);
  assert.equal(context.ok, true);
  if (!context.ok) return;
  const manifest = await runtime.electionManifest.read(context.value);
  assert.equal(manifest.ok, true);
  if (!manifest.ok) return;
  assert.equal(manifest.value.activationStatus, "PROTOTYPE_NOT_ACTIVATED");
  const style = await runtime.ballotStyle.read(context.value);
  assert.equal(style.ok, true);

  // Crypto, submission and receipt remain blocked in the test profile too: a
  // fixture may furnish a page, never a cryptographic operation or a result.
  for (const result of [
    await runtime.crypto.prepareEnvelope(context.value, {
      ballotStyleId: "",
      selections: [],
    }),
    await runtime.submission.submit(context.value, "final_cast", "t"),
    await runtime.submission.status(context.value, "t"),
    await runtime.receipt.readReceipt("ABCDEFGH"),
    await runtime.receipt.confirmRecordedAsCast("ABCDEFGH"),
  ]) {
    assert.equal(result.ok, false);
  }
});

test("the fixture-absent stub throws rather than degrading to something usable", () => {
  assert.throws(() => absent(), /WS03_FIXTURE_ABSENT_IN_PRODUCTION/);
});

test("the fixture election context carries no identity or tally material", async () => {
  const runtime = createGovernedTestRuntime();
  const context = await runtime.handoff.consume(null);
  assert.equal(context.ok, true);
  if (!context.ok) return;
  const style = await runtime.ballotStyle.read(context.value);
  assert.equal(style.ok, true);
  if (!style.ok) return;
  const serialised = JSON.stringify(style.value);
  for (const forbidden of ["member_id", "account_id", "turnout", "count"]) {
    assert.ok(!serialised.includes(forbidden), forbidden);
  }
});

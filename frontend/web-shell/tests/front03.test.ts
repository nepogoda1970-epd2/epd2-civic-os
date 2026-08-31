import assert from "node:assert/strict";
import test from "node:test";
import {
  createFixtureRuntime,
  createProductionRuntime,
  storagePolicy,
  telemetryAllowed,
} from "../member/runtime";

test("Applicant principal stays Applicant", async () => {
  const r = await createFixtureRuntime("applicant").principal.resolve();
  assert.equal(r.ok && r.value.actor, "applicant");
});
test("unauthorized scope is refused safely", async () => {
  const r =
    await createFixtureRuntime("member").organizationScope.reauthorize(
      "secret",
    );
  assert.equal(r.ok, false);
  if (!r.ok) assert.equal(r.error.safeMessage, "Zugriff nicht möglich.");
});
test("VotingHandoff has no persistent identity", async () => {
  const r = await createFixtureRuntime("member").votingHandoff.create();
  assert.equal(r.ok, false);
  assert.doesNotMatch(
    JSON.stringify(r),
    /memberId|accountId|personId|session/i,
  );
});
test("browser storage excludes bearer authority", () => {
  assert.deepEqual(storagePolicy, {
    bearerInLocalStorage: false,
    bearerInSessionStorage: false,
    bearerInIndexedDB: false,
    protectedOfflineCache: false,
    crossWorkspaceBridge: false,
  });
});
test("telemetry allowlist excludes protected identifiers", () => {
  assert.equal(
    telemetryAllowed.some((x) =>
      /member|applicant|email|phone|token|session|continuation/i.test(x),
    ),
    false,
  );
});
test("initiative success exists only after port commit", async () => {
  const r = await createFixtureRuntime("member").initiatives.commit("bund", {
    title: "T",
    summary: "S",
    clientRequestRef: "r",
    expectedVersion: "1",
  });
  assert.equal(r.ok && r.value.state, "committed");
});
test("scope authorization returns context version", async () => {
  const r =
    await createFixtureRuntime("member").organizationScope.reauthorize(
      "berlin",
    );
  assert.equal(r.ok && r.value.contextVersion, "fixture-berlin");
});
test("authorized scope catalogue comes from OrganizationScopePort", async () => {
  const r =
    await createFixtureRuntime("member").organizationScope.listAuthorized();
  assert.equal(r.ok, true);
  if (r.ok)
    assert.deepEqual(
      r.value.map((x) => x.label),
      ["Bund", "Landesverband Berlin", "Regional-/Ortsverband Berlin-Mitte"],
    );
});
test("scope-specific MemberCore projections change after reauthorization", async () => {
  const runtime = createFixtureRuntime("member");
  const a = await runtime.memberCore.read("bund");
  const b = await runtime.memberCore.read("berlin");
  assert.equal(
    a.ok && b.ok && a.value.organization !== b.value.organization,
    true,
  );
});
test("production runtime cannot activate fixture data", async () => {
  const runtime = createProductionRuntime();
  assert.equal(runtime.profile, "production");
  assert.equal((await runtime.memberCore.read("bund")).ok, false);
  assert.equal((await runtime.organizationScope.listAuthorized()).ok, false);
  assert.equal((await runtime.votingHandoff.create()).ok, false);
});

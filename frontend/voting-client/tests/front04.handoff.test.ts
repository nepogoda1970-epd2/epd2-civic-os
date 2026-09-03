import assert from "node:assert/strict";
import test from "node:test";

import {
  FORBIDDEN_HANDOFF_CHANNELS,
  HANDOFF_REFUSAL_CODES,
  VOTING_AUDIENCE_ORIGIN,
  VOTING_ENTRY_PURPOSE,
  handoffChannelPermitted,
  pageLocalDigest,
  urlCarriesHandoffChannelViolation,
  verifyHandoff,
} from "../domain/handoff";

const NOW = new Date("2026-09-01T12:00:00.000Z");
const CONTEXT_ID = "ctx-0001";

function binding(overrides: Partial<Parameters<typeof verifyHandoff>[1]> = {}) {
  return {
    expectedAudience: VOTING_AUDIENCE_ORIGIN,
    allowedOrigins: [VOTING_AUDIENCE_ORIGIN],
    expectedVotingContextId: CONTEXT_ID,
    now: NOW,
    consumedDigests: new Set<string>(),
    ...overrides,
  };
}

function artifact(overrides: Record<string, unknown> = {}) {
  return {
    artifact: "opaque-value-0001",
    audienceOrigin: VOTING_AUDIENCE_ORIGIN,
    purpose: VOTING_ENTRY_PURPOSE,
    votingContextId: CONTEXT_ID,
    expiresAt: "2026-09-01T12:02:00.000Z",
    ...overrides,
  };
}

test("a valid handoff yields a voting context carrying no identity", () => {
  const result = verifyHandoff(artifact(), binding(), VOTING_AUDIENCE_ORIGIN);
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.equal(result.context.votingContextId, CONTEXT_ID);
  assert.equal(result.context.purpose, "voting_entry");
  assert.equal(result.context.role, "eligible_voter");
  assert.deepEqual(Object.keys(result.context).sort(), [
    "audienceOrigin",
    "expiresAt",
    "purpose",
    "role",
    "votingContextId",
  ]);
});

test("an expired handoff is refused", () => {
  const result = verifyHandoff(
    artifact({ expiresAt: "2026-09-01T11:59:59.000Z" }),
    binding(),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_EXPIRED");
  assert.equal(result.refusal.commitKnowledge, "not_committed");
});

test("expiry is inclusive: a handoff expiring exactly now is refused", () => {
  const result = verifyHandoff(
    artifact({ expiresAt: NOW.toISOString() }),
    binding(),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
});

test("an already consumed handoff is refused as replay", () => {
  const value = artifact();
  const result = verifyHandoff(
    value,
    binding({ consumedDigests: new Set([pageLocalDigest(value.artifact)]) }),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_ALREADY_USED");
  assert.equal(result.refusal.entitlementKnownIntact, false);
});

test("a wrong audience is refused", () => {
  const result = verifyHandoff(
    artifact({ audienceOrigin: "https://mitglieder.epd.example" }),
    binding(),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_AUDIENCE_MISMATCH");
});

test("a wrong presenting origin is refused before the audience is read", () => {
  // The artifact below has BOTH a wrong presenting origin and a wrong purpose.
  // Origin must win, which is what proves the ordering.
  const result = verifyHandoff(
    artifact({ purpose: "something_else" }),
    binding(),
    "https://mitglieder.epd.example",
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_ORIGIN_MISMATCH");
});

test("a wrong purpose is refused", () => {
  const result = verifyHandoff(
    artifact({ purpose: "password_reset" }),
    binding(),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_PURPOSE_MISMATCH");
});

test("a wrong voting context is refused", () => {
  const result = verifyHandoff(
    artifact({ votingContextId: "ctx-9999" }),
    binding(),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_CONTEXT_MISMATCH");
});

test("a malformed handoff is refused with the same generic invalid code", () => {
  for (const value of [
    null,
    undefined,
    42,
    "string",
    [],
    {},
    { artifact: "" },
  ]) {
    const result = verifyHandoff(value, binding(), VOTING_AUDIENCE_ORIGIN);
    assert.equal(result.ok, false);
    if (result.ok) continue;
    assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_INVALID");
  }
});

test("a handoff carrying persistent identity is refused outright", () => {
  for (const field of [
    "member_id",
    "account_id",
    "person_id",
    "session_reference",
  ]) {
    const result = verifyHandoff(
      artifact({ [field]: "anything" }),
      binding(),
      VOTING_AUDIENCE_ORIGIN,
    );
    assert.equal(result.ok, false, field);
    if (result.ok) continue;
    assert.equal(result.refusal.reasonCode, "VOTING_HANDOFF_IDENTITY_PRESENT");
  }
});

test("an unknown artifact and a wrong value produce the same refusal", () => {
  const unknown = verifyHandoff(
    artifact({ artifact: "never-issued" }),
    binding({ expectedVotingContextId: "ctx-other" }),
    VOTING_AUDIENCE_ORIGIN,
  );
  const wrong = verifyHandoff(
    artifact({ artifact: "wrong-value" }),
    binding({ expectedVotingContextId: "ctx-other" }),
    VOTING_AUDIENCE_ORIGIN,
  );
  assert.equal(unknown.ok, false);
  assert.equal(wrong.ok, false);
  if (unknown.ok || wrong.ok) return;
  assert.equal(unknown.refusal.reasonCode, wrong.refusal.reasonCode);
  assert.equal(unknown.refusal.safeMessage, wrong.refusal.safeMessage);
});

test("every refusal renders the same non-disclosing message", () => {
  const messages = new Set<string>();
  for (const [override, origin] of [
    [{ purpose: "x" }, VOTING_AUDIENCE_ORIGIN],
    [{ audienceOrigin: "https://elsewhere.example" }, VOTING_AUDIENCE_ORIGIN],
    [{ votingContextId: "other" }, VOTING_AUDIENCE_ORIGIN],
    [{}, "https://elsewhere.example"],
  ] as const) {
    const result = verifyHandoff(artifact(override), binding(), origin);
    if (!result.ok) messages.add(result.refusal.safeMessage);
  }
  assert.equal(messages.size, 1);
});

test("no handoff channel is permitted while no accepted contract exists", () => {
  for (const channel of FORBIDDEN_HANDOFF_CHANNELS) {
    assert.equal(handoffChannelPermitted(channel), false, channel);
  }
  assert.equal(handoffChannelPermitted("anything_else"), false);
});

test("a handoff value in the query string or fragment is a channel violation", () => {
  assert.equal(
    urlCarriesHandoffChannelViolation("/vote/credential?handoff=abc"),
    true,
  );
  assert.equal(
    urlCarriesHandoffChannelViolation("/vote/credential?token=abc"),
    true,
  );
  assert.equal(
    urlCarriesHandoffChannelViolation("/vote/credential#artifact=abc"),
    true,
  );
  assert.equal(
    urlCarriesHandoffChannelViolation("/vote/credential#credential"),
    true,
  );
  assert.equal(urlCarriesHandoffChannelViolation("/vote/credential"), false);
  assert.equal(
    urlCarriesHandoffChannelViolation("/vote/credential?lang=en"),
    false,
  );
});

test("the refusal vocabulary is closed", () => {
  assert.equal(HANDOFF_REFUSAL_CODES.length, 9);
  assert.equal(new Set(HANDOFF_REFUSAL_CODES).size, 9);
});

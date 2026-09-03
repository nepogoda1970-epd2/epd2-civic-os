import assert from "node:assert/strict";
import test from "node:test";

import {
  authorityUsable,
  bindScope,
  mayReadAcrossMandates,
  resolvedMandateIds,
  scopeIsSingular,
  searchRequestAdmissible,
} from "../domain/scope";
import {
  ANONYMOUS_SESSION,
  applySessionEvent,
  interruptionFor,
  mustClearLoadedContent,
  nextSessionState,
  type SessionEvent,
} from "../domain/session";
import { SESSION_STATES, sessionPermitsWork } from "../domain/types";
import type { MandateScope, MandateSession } from "../domain/types";

const SCOPE_A: MandateScope = Object.freeze({
  mandateId: "MANDAT-A",
  organizationId: "ORG-A",
  label: "Mandat A",
  level: "test",
  authorityActive: true,
});

const SCOPE_B: MandateScope = Object.freeze({
  ...SCOPE_A,
  mandateId: "MANDAT-B",
  organizationId: "ORG-B",
  label: "Mandat B",
});

const SESSION_A: MandateSession = Object.freeze({
  state: "authenticated",
  role: "representative",
  assurance: "standard",
  scope: SCOPE_A,
  displayName: "Test",
  conflictRestricted: false,
});

/* ----------------------------------------------------------------- scope binding */

test("binding succeeds only for the session's own mandate", () => {
  assert.equal(bindScope(SESSION_A, "MANDAT-A", {}).ok, true);
  assert.equal(bindScope(SESSION_A, null, {}).ok, true);
  assert.equal(bindScope(SESSION_A, "MANDAT-B", {}).ok, false);
});

test("the wrong-mandate refusal is non-disclosing", () => {
  const wrong = bindScope(SESSION_A, "MANDAT-B", {});
  assert.equal(wrong.ok, false);
  if (wrong.ok) return;
  assert.equal(wrong.error.nonDisclosing, true);
  assert.equal(wrong.error.kind, "scope_mismatch");
  // The refusal names no mandate, no case and no resource.
  assert.ok(!wrong.error.safeMessage.includes("MANDAT-B"));
  assert.ok(!wrong.error.safeMessage.includes("MANDAT-A"));
});

test("a session without scope binds nothing", () => {
  const anonymous = bindScope(ANONYMOUS_SESSION, "MANDAT-A", {});
  assert.equal(anonymous.ok, false);
  assert.deepEqual(resolvedMandateIds(ANONYMOUS_SESSION), []);
});

test("exactly one mandate is ever resolved", () => {
  assert.deepEqual(resolvedMandateIds(SESSION_A), ["MANDAT-A"]);
  assert.equal(scopeIsSingular(SESSION_A), true);
  assert.equal(scopeIsSingular(ANONYMOUS_SESSION), true);
});

test("cross-mandate reading is a total refusal", () => {
  assert.equal(mayReadAcrossMandates(SESSION_A), false);
  assert.equal(mayReadAcrossMandates(ANONYMOUS_SESSION), false);
});

test("a search is admissible only when scoped to the session's mandate", () => {
  assert.equal(
    searchRequestAdmissible({ session: SESSION_A, scopeMandateId: "MANDAT-A" }),
    true,
  );
  assert.equal(
    searchRequestAdmissible({ session: SESSION_A, scopeMandateId: "MANDAT-B" }),
    false,
  );
  assert.equal(
    searchRequestAdmissible({ session: SESSION_A, scopeMandateId: null }),
    false,
  );
  assert.equal(
    searchRequestAdmissible({
      session: ANONYMOUS_SESSION,
      scopeMandateId: "MANDAT-A",
    }),
    false,
  );
});

test("authority must be active for the scope to be usable", () => {
  assert.equal(authorityUsable(SCOPE_A), true);
  assert.equal(authorityUsable({ ...SCOPE_A, authorityActive: false }), false);
  assert.equal(authorityUsable(null), false);
});

/* --------------------------------------------------------------- session states */

test("no event returns a terminal negative state to a working state", () => {
  const negative = [
    "expired",
    "revoked",
    "scope_changed",
    "authority_suspended",
    "authority_expired",
  ] as const;
  const events: SessionEvent["type"][] = [
    "session_established",
    "step_up_completed",
    "step_up_demanded",
    "session_expired",
    "session_revoked",
    "scope_changed",
    "authority_suspended",
    "authority_expired",
    "signed_out",
  ];
  for (const state of negative) {
    for (const type of events) {
      const next = nextSessionState(state, { type } as SessionEvent);
      if (next === null) continue;
      assert.ok(
        !sessionPermitsWork(next),
        `${state} + ${type} reached the working state ${next}`,
      );
    }
  }
});

test("an anonymous session cannot step up into work", () => {
  for (const type of [
    "step_up_completed",
    "step_up_demanded",
    "scope_changed",
  ] as const) {
    assert.equal(nextSessionState("anonymous", { type }), null, type);
  }
});

test("expiry and revocation clear the scope and the role", () => {
  for (const type of ["session_expired", "session_revoked"] as const) {
    const after = applySessionEvent(SESSION_A, { type });
    assert.equal(after.scope, null, type);
    assert.equal(after.role, null, type);
    assert.equal(after.assurance, "none", type);
    assert.equal(after.displayName, null, type);
  }
});

test("every non-working state has a defined interruption", () => {
  for (const state of SESSION_STATES) {
    const interruption = interruptionFor(state);
    if (sessionPermitsWork(state)) {
      assert.equal(interruption, null, state);
      continue;
    }
    if (state === "anonymous" || state === "step_up_required") continue;
    assert.ok(interruption !== null, `${state} has no interruption`);
    assert.ok(interruption.refusal.safeMessage.length > 0, state);
    assert.ok(interruption.refusal.nextSafeAction.length > 0, state);
  }
});

test("a revoked session is the only one that discards the draft outright", () => {
  assert.equal(
    interruptionFor("expired")?.draftDisposition,
    "retained_in_memory",
  );
  assert.equal(interruptionFor("revoked")?.draftDisposition, "discarded");
  assert.equal(interruptionFor("scope_changed")?.draftDisposition, "discarded");
});

test("a scope change forces previously loaded content to be cleared", () => {
  assert.equal(mustClearLoadedContent(SCOPE_A, SCOPE_B), true);
  assert.equal(mustClearLoadedContent(SCOPE_A, null), true);
  assert.equal(mustClearLoadedContent(SCOPE_A, SCOPE_A), false);
  assert.equal(mustClearLoadedContent(null, SCOPE_A), false);
});

test("commit knowledge is never invented on an interruption", () => {
  assert.equal(interruptionFor("expired")?.refusal.committed, "not_committed");
  // A revocation mid-flight genuinely cannot know, and says so.
  assert.equal(interruptionFor("revoked")?.refusal.committed, "unknown");
});

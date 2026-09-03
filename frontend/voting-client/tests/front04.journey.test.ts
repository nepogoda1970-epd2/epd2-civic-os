import assert from "node:assert/strict";
import test from "node:test";

import {
  PROHIBITED_PREMATURE_SUCCESS_PHRASES,
  STATES_PERMITTING_CAST_SUCCESS_LANGUAGE,
  TERMINAL_STATES,
  canTransition,
  castSuccessLanguagePermitted,
  isTerminal,
  permittedEvents,
  submissionPermittedFrom,
  transition,
} from "../domain/stateMachine";
import {
  COMMITTED_STATES,
  JOURNEY_STATES,
  commitKnowledge,
  submissionClassCreatesNetworkArtefact,
} from "../domain/types";
import {
  blankContestIds,
  BALLOT_STATE_PERSISTENCE,
  ballotStyleAcceptable,
  clearContest,
  contestValidity,
  emptyDraft,
  readyForReview,
  selectionFor,
  toggleOption,
} from "../domain/ballot";
import {
  BALLOT_CRYPTO_RUNTIME,
  WS03_CAPABILITIES,
  capability,
  capabilityExecutable,
  capabilityStatus,
} from "../domain/capabilities";
import type { BallotStyle } from "../domain/types";

const STYLE: BallotStyle = {
  ballotStyleId: "style-1",
  schemaVersion: "test-1",
  contests: [
    {
      contestId: "single",
      title: "Frage 1",
      instruction: "Eine Auswahl",
      selectionLimit: 1,
      options: [
        { optionId: "a", label: "A" },
        { optionId: "b", label: "B" },
      ],
    },
    {
      contestId: "multi",
      title: "Frage 2",
      instruction: "Zwei Auswahlen",
      selectionLimit: 2,
      options: [
        { optionId: "x", label: "X" },
        { optionId: "y", label: "Y" },
        { optionId: "z", label: "Z" },
      ],
    },
  ],
};

test("every journey state is reachable in the vocabulary and has a commit answer", () => {
  assert.equal(JOURNEY_STATES.length, 12);
  for (const state of JOURNEY_STATES) {
    const knowledge = commitKnowledge(state);
    assert.ok(
      ["committed", "not_committed", "unknown"].includes(knowledge),
      state,
    );
  }
});

test("a timeout leads to uncertainty, never to success and never to failure", () => {
  assert.equal(
    transition("submitted", { type: "submission_timed_out" }),
    "submission_uncertain",
  );
  assert.equal(commitKnowledge("submission_uncertain"), "unknown");
  assert.equal(
    canTransition("submission_uncertain", "submission_timed_out"),
    false,
  );
});

test("no client-side event can reach an accepted state", () => {
  const clientEvents = [
    "submission_started",
    "submission_timed_out",
    "selection_changed",
    "review_opened",
    "ballot_opened",
    "handoff_accepted",
    "cancelled",
  ] as const;
  for (const state of JOURNEY_STATES) {
    if ((COMMITTED_STATES as readonly string[]).includes(state)) continue;
    for (const event of clientEvents) {
      const next = transition(state, { type: event });
      assert.ok(
        !(COMMITTED_STATES as readonly string[]).includes(next),
        `${state} + ${event} reached ${next}`,
      );
    }
  }
  // Only an authoritative acceptance does.
  assert.equal(
    transition("submitted", { type: "authoritative_acceptance" }),
    "accepted",
  );
  assert.equal(
    transition("submission_uncertain", { type: "authoritative_acceptance" }),
    "accepted",
  );
});

test("review must precede submission", () => {
  assert.equal(submissionPermittedFrom("reviewed"), true);
  for (const state of JOURNEY_STATES) {
    if (state === "reviewed") continue;
    assert.equal(submissionPermittedFrom(state), false, state);
  }
});

test("an impermissible event leaves the state unchanged rather than throwing", () => {
  assert.equal(
    transition("prepared", { type: "authoritative_acceptance" }),
    "prepared",
  );
  assert.equal(
    transition("accepted", { type: "submission_started" }),
    "accepted",
  );
});

test("a second submission event from a submitted state does not advance", () => {
  assert.equal(
    transition("submitted", { type: "submission_started" }),
    "submitted",
  );
});

test("terminal states accept nothing", () => {
  for (const state of TERMINAL_STATES) {
    assert.equal(isTerminal(state), true, state);
    assert.deepEqual(permittedEvents(state), [], state);
  }
});

test("cast success language is permitted only after authoritative acceptance", () => {
  for (const state of JOURNEY_STATES) {
    const permitted = castSuccessLanguagePermitted(state);
    assert.equal(
      permitted,
      (STATES_PERMITTING_CAST_SUCCESS_LANGUAGE as readonly string[]).includes(
        state,
      ),
      state,
    );
  }
  assert.equal(castSuccessLanguagePermitted("submitted"), false);
  assert.equal(castSuccessLanguagePermitted("submission_uncertain"), false);
  assert.ok(
    PROHIBITED_PREMATURE_SUCCESS_PHRASES.includes("Sie haben abgestimmt"),
  );
  assert.ok(
    PROHIBITED_PREMATURE_SUCCESS_PHRASES.includes("Stimme erfolgreich"),
  );
});

test("a local diagnostic challenge creates no network artefact", () => {
  assert.equal(
    submissionClassCreatesNetworkArtefact("local_diagnostic_challenge"),
    false,
  );
  assert.equal(submissionClassCreatesNetworkArtefact("final_cast"), true);
  assert.equal(
    submissionClassCreatesNetworkArtefact("public_evidentiary_challenge"),
    true,
  );
});

test("ballot state is declared ephemeral in every direction", () => {
  for (const [target, allowed] of Object.entries(BALLOT_STATE_PERSISTENCE)) {
    assert.equal(allowed, false, target);
  }
});

test("a single-selection contest replaces rather than accumulates", () => {
  let draft = emptyDraft(STYLE);
  draft = toggleOption(STYLE, draft, "single", "a");
  draft = toggleOption(STYLE, draft, "single", "b");
  assert.deepEqual(selectionFor(draft, "single").optionIds, ["b"]);
});

test("a multi-selection contest refuses to exceed its limit", () => {
  let draft = emptyDraft(STYLE);
  draft = toggleOption(STYLE, draft, "multi", "x");
  draft = toggleOption(STYLE, draft, "multi", "y");
  draft = toggleOption(STYLE, draft, "multi", "z");
  assert.deepEqual(selectionFor(draft, "multi").optionIds, ["x", "y"]);
  assert.equal(contestValidity(STYLE, draft, "multi").kind, "within_limit");
});

test("toggling removes and clearing empties", () => {
  let draft = emptyDraft(STYLE);
  draft = toggleOption(STYLE, draft, "multi", "x");
  draft = toggleOption(STYLE, draft, "multi", "x");
  assert.deepEqual(selectionFor(draft, "multi").optionIds, []);
  draft = toggleOption(STYLE, draft, "multi", "y");
  draft = clearContest(draft, "multi");
  assert.deepEqual(selectionFor(draft, "multi").optionIds, []);
});

test("an unknown contest or option changes nothing", () => {
  const draft = emptyDraft(STYLE);
  assert.deepEqual(toggleOption(STYLE, draft, "nope", "a"), draft);
  assert.deepEqual(toggleOption(STYLE, draft, "single", "nope"), draft);
});

test("abstention is a permitted outcome", () => {
  const draft = emptyDraft(STYLE);
  assert.equal(readyForReview(STYLE, draft), true);
  assert.deepEqual(blankContestIds(STYLE, draft), ["single", "multi"]);
});

test("a ballot style carrying identity or tally material is refused", () => {
  assert.equal(ballotStyleAcceptable(STYLE), true);
  assert.equal(ballotStyleAcceptable({ ...STYLE, member_id: "x" }), false);
  assert.equal(ballotStyleAcceptable({ ...STYLE, turnout: 12 }), false);
});

test("every WS-03 network capability is blocked at this baseline", () => {
  const networkCapabilities = [
    "handoff_consumption",
    "election_context",
    "ballot_style",
    "public_election_parameters",
    "public_joint_key",
    "capability_probe",
    "ballot_crypto",
    "ballot_submission",
    "submission_recovery",
    "local_diagnostic_challenge",
    "public_evidentiary_challenge",
    "receipt_verification",
    "recorded_as_cast_verification",
  ] as const;
  for (const id of networkCapabilities) {
    assert.equal(capabilityExecutable(id), false, id);
    assert.match(capabilityStatus(id), /^(BLOCKED_|LIMITED)/, id);
  }
  assert.equal(BALLOT_CRYPTO_RUNTIME, "BLOCKED");
  assert.equal(capabilityStatus("ballot_crypto"), "BLOCKED_CRYPTO");
});

test("every capability names an owner and a reason", () => {
  for (const record of WS03_CAPABILITIES) {
    assert.ok(record.owner.length > 0, record.id);
    assert.ok(record.reason.length > 20, record.id);
    assert.ok(record.frontendBehaviour.length > 20, record.id);
  }
  assert.throws(() => capability("nonexistent" as never));
});

test("only client-local capabilities are available", () => {
  const available = WS03_CAPABILITIES.filter(
    (record) => record.status === "AVAILABLE_ACCEPTED_RUNTIME",
  ).map((record) => record.id);
  assert.deepEqual(available.sort(), [
    "accessibility_assistance",
    "governed_fallback",
  ]);
});

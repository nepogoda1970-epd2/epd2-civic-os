/**
 * Governed test profile.
 *
 * This module exists so the complete user journey — rendering a ballot,
 * keyboard operation, review, cancellation, the consequential boundary and
 * every failure surface — can be exercised by real browser tests.  It is not a
 * backend and it never pretends to be one.
 *
 * What it supplies is presentation material only: an election context that
 * declares itself not activated, and a ballot style.  What it deliberately
 * does NOT supply is a cast, a receipt, an encryption or a success.  Those
 * remain blocked in this profile exactly as they are in production, because
 * the dependency that blocks them is the absence of a governed cryptographic
 * implementation and of an accepted submission contract — and a fixture cannot
 * substitute for either without becoming the fake the stage contract forbids.
 *
 * `FIXTURE_MARKER` is a unique string.  The production build is scanned for it
 * and must not contain it.
 */

import type {
  BallotStyle,
  ElectionContext,
  Receipt,
  Result,
} from "../domain/types";
import { PRODUCTION_REFUSALS, unavailable } from "./unavailable";
import type { VotingRuntime } from "./ports";

export const FIXTURE_MARKER = "EPD2_FRONT04_GOVERNED_TEST_FIXTURE_MARKER";

export const FIXTURE_ELECTION: ElectionContext = Object.freeze({
  electionContextReference: "PROTOTYP-KONTEXT-0001",
  title: "Beispielabstimmung (Prototyp, nicht aktiviert)",
  activationStatus: "PROTOTYPE_NOT_ACTIVATED",
});

export const FIXTURE_BALLOT_STYLE: BallotStyle = Object.freeze({
  ballotStyleId: "PROTOTYP-STIMMZETTEL-0001",
  schemaVersion: "front04-fixture-1",
  contests: Object.freeze([
    Object.freeze({
      contestId: "contest-1",
      title: "Beispielfrage 1",
      instruction: "Wählen Sie höchstens eine Antwort.",
      selectionLimit: 1,
      options: Object.freeze([
        Object.freeze({
          optionId: "c1-a",
          label: "Antwortmöglichkeit A",
          description: "Beispieltext ohne inhaltliche Bedeutung.",
        }),
        Object.freeze({
          optionId: "c1-b",
          label: "Antwortmöglichkeit B",
          description: "Beispieltext ohne inhaltliche Bedeutung.",
        }),
        Object.freeze({
          optionId: "c1-c",
          label: "Antwortmöglichkeit C",
          description: "Beispieltext ohne inhaltliche Bedeutung.",
        }),
      ]),
    }),
    Object.freeze({
      contestId: "contest-2",
      title: "Beispielfrage 2",
      instruction: "Wählen Sie höchstens zwei Antworten.",
      selectionLimit: 2,
      options: Object.freeze([
        Object.freeze({ optionId: "c2-a", label: "Vorschlag Alpha" }),
        Object.freeze({ optionId: "c2-b", label: "Vorschlag Beta" }),
        Object.freeze({ optionId: "c2-c", label: "Vorschlag Gamma" }),
        Object.freeze({ optionId: "c2-d", label: "Vorschlag Delta" }),
      ]),
    }),
  ]),
});

export const FIXTURE_VOTING_CONTEXT_ID = "PROTOTYP-VOTING-CONTEXT-0001";

export function createGovernedTestRuntime(): VotingRuntime {
  return Object.freeze({
    profile: "governed_test" as const,
    handoff: Object.freeze({
      async consume() {
        return {
          ok: true as const,
          value: {
            votingContextId: FIXTURE_VOTING_CONTEXT_ID,
            audienceOrigin: "https://vote.epd.example",
            purpose: "voting_entry" as const,
            expiresAt: new Date(Date.now() + 120_000).toISOString(),
            role: "eligible_voter" as const,
          },
        };
      },
    }),
    electionManifest: Object.freeze({
      async read() {
        return { ok: true as const, value: FIXTURE_ELECTION };
      },
    }),
    ballotStyle: Object.freeze({
      async read() {
        return { ok: true as const, value: FIXTURE_BALLOT_STYLE };
      },
    }),
    // Blocked in this profile too.  A fixture may furnish a page; it may not
    // furnish a cryptographic operation or an acceptance.
    crypto: Object.freeze({
      async prepareEnvelope(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.crypto);
      },
    }),
    submission: Object.freeze({
      async submit(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.submission);
      },
      async status(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.submissionStatus);
      },
    }),
    receipt: Object.freeze({
      async readReceipt(): Promise<Result<Receipt>> {
        return unavailable<Receipt>(PRODUCTION_REFUSALS.receipt);
      },
      async confirmRecordedAsCast(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.recordedAsCast);
      },
    }),
  });
}

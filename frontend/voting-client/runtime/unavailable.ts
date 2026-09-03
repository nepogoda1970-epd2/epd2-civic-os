/**
 * Controlled unavailability.
 *
 * Every refusal a port can return is built here, so each one carries the same
 * four things the voter needs: what happened, whether anything was committed,
 * whether their entitlement is known to be intact, and what can safely be done
 * next.  A port cannot invent a cheerier refusal, because it has no other way
 * to construct one.
 */

import type { CommitKnowledge, Result, SafeRefusal } from "../domain/types";

export type UnavailabilityInput = {
  readonly reasonCode: string;
  readonly safeMessage: string;
  readonly commitKnowledge: CommitKnowledge;
  readonly entitlementKnownIntact: boolean;
  readonly nextSafeAction: string;
  readonly kind?: SafeRefusal["kind"];
};

export function refusal(input: UnavailabilityInput): SafeRefusal {
  return Object.freeze({
    kind: input.kind ?? "blocked",
    reasonCode: input.reasonCode,
    safeMessage: input.safeMessage,
    commitKnowledge: input.commitKnowledge,
    entitlementKnownIntact: input.entitlementKnownIntact,
    nextSafeAction: input.nextSafeAction,
  });
}

export function unavailable<T>(input: UnavailabilityInput): Result<T> {
  return { ok: false, error: refusal(input) };
}

const RETURN_AND_RESTART =
  "Kehren Sie in den Mitgliederbereich zurück und starten Sie den Vorgang erneut.";
const CONTACT_GOVERNED_CHANNEL =
  "Wenden Sie sich an die zuständige Stelle über den angegebenen Ersatzweg.";

/** The refusals the production adapter uses.  Each names its exact dependency. */
export const PRODUCTION_REFUSALS = Object.freeze({
  handoffChannel: {
    reasonCode: "WS03_HANDOFF_CHANNEL_NOT_ACCEPTED",
    safeMessage:
      "Für die Übernahme der Stimmberechtigung ist derzeit kein freigegebener Übergabeweg verfügbar.",
    commitKnowledge: "not_committed" as CommitKnowledge,
    entitlementKnownIntact: true,
    nextSafeAction: RETURN_AND_RESTART,
  },
  electionContext: {
    reasonCode: "WS03_ELECTION_CONTEXT_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Es ist derzeit keine Abstimmung abrufbar.",
    commitKnowledge: "not_committed" as CommitKnowledge,
    entitlementKnownIntact: true,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  ballotStyle: {
    reasonCode: "WS03_BALLOT_STYLE_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Es kann derzeit kein Stimmzettel angezeigt werden.",
    commitKnowledge: "not_committed" as CommitKnowledge,
    entitlementKnownIntact: true,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  crypto: {
    reasonCode: "WS03_BALLOT_CRYPTO_RUNTIME_BLOCKED",
    safeMessage:
      "Die kryptografische Vorbereitung der Stimme ist nicht verfügbar. Es wurde nichts abgegeben.",
    commitKnowledge: "not_committed" as CommitKnowledge,
    entitlementKnownIntact: true,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  submission: {
    reasonCode: "WS03_BALLOT_SUBMISSION_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Die Stimmabgabe ist nicht verfügbar. Es wurde nichts abgegeben und nichts gezählt.",
    commitKnowledge: "not_committed" as CommitKnowledge,
    entitlementKnownIntact: true,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  submissionStatus: {
    reasonCode: "WS03_SUBMISSION_STATUS_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Der Stand einer Übermittlung kann derzeit nicht abgefragt werden.",
    commitKnowledge: "unknown" as CommitKnowledge,
    entitlementKnownIntact: false,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  receipt: {
    reasonCode: "WS03_RECEIPT_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Es kann derzeit kein Nachweis abgerufen werden.",
    commitKnowledge: "unknown" as CommitKnowledge,
    entitlementKnownIntact: false,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
  recordedAsCast: {
    reasonCode: "WS03_RECORDED_AS_CAST_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Die Prüfung der Veröffentlichung ist derzeit nicht verfügbar.",
    commitKnowledge: "unknown" as CommitKnowledge,
    entitlementKnownIntact: false,
    nextSafeAction: CONTACT_GOVERNED_CHANNEL,
  },
} as const);

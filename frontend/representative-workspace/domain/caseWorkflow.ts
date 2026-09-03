/**
 * Case intake and triage.
 *
 * Two properties matter more than the transition table itself:
 *
 *  1. Every transition is server-authoritative. This module computes what a
 *     transition *would* be and what preconditions it carries; it never decides
 *     that one occurred. `clientMayDecide` is asserted false for case state.
 *  2. Every attempt has three outcomes, not two. The uncertain outcome — the
 *     request was sent and the answer never arrived — is a first-class result,
 *     because treating it as failure invites a duplicate mutation.
 */

import { clientMayDecide } from "../policies/boundaries";
import type {
  ActionDescriptor,
  CaseState,
  CaseSummary,
  SafeRefusal,
} from "./types";

export type CaseEvent =
  | { readonly type: "assign" }
  | { readonly type: "triage" }
  | { readonly type: "await_response" }
  | { readonly type: "record_response" }
  | { readonly type: "close" }
  | { readonly type: "archive" }
  | { readonly type: "reopen" };

const TRANSITIONS: Readonly<
  Record<CaseState, Partial<Record<CaseEvent["type"], CaseState>>>
> = Object.freeze({
  new: { assign: "assigned" },
  assigned: { triage: "triaged", close: "closed" },
  triaged: {
    await_response: "awaiting_response",
    record_response: "triaged",
    close: "closed",
  },
  awaiting_response: { record_response: "triaged", close: "closed" },
  closed: { archive: "archived", reopen: "assigned" },
  archived: {},
  /**
   * `unavailable` is not a case state on the server. It is what this client
   * shows when it cannot know the state, and no event moves out of it: the only
   * exit is a successful read, which is a new observation rather than a
   * transition.
   */
  unavailable: {},
});

export function proposedCaseState(
  state: CaseState,
  event: CaseEvent,
): CaseState | null {
  const next = TRANSITIONS[state][event.type];
  return next === undefined ? null : next;
}

/** The client proposes; it does not decide. Total function, always false. */
export function clientMayCommitCaseTransition(): false {
  return clientMayDecide("case_state");
}

/**
 * The precondition a transition must carry. Absence of a version token is
 * itself a blocking condition: an unconditional mutation would silently
 * overwrite a concurrent change by a colleague on the same desk.
 */
export type TransitionPrecondition = {
  readonly requiresVersion: true;
  readonly version: string | null;
  readonly admissible: boolean;
};

export function preconditionFor(
  caseVersion: string | null,
): TransitionPrecondition {
  return {
    requiresVersion: true,
    version: caseVersion,
    admissible: caseVersion !== null && caseVersion.length > 0,
  };
}

/** The three outcomes of an attempted transition. */
export type TransitionOutcome =
  | { readonly kind: "not_attempted"; readonly refusal: SafeRefusal }
  | { readonly kind: "refused"; readonly refusal: SafeRefusal }
  | { readonly kind: "uncertain"; readonly refusal: SafeRefusal };

export const STALE_CASE: SafeRefusal = Object.freeze({
  kind: "conflict_stale",
  reasonCode: "WS04-CASE-409",
  safeMessage:
    "Der Vorgang wurde zwischenzeitlich von anderer Stelle geändert.",
  committed: "not_committed",
  nextSafeAction:
    "Aktuellen Stand laden und die Änderung erneut prüfen. Ihre Eingabe bleibt erhalten.",
  nonDisclosing: false,
});

export const UNCERTAIN_CASE: SafeRefusal = Object.freeze({
  kind: "unavailable",
  reasonCode: "WS04-CASE-UNCERTAIN",
  safeMessage: "Es ist nicht feststellbar, ob die Änderung übernommen wurde.",
  committed: "unknown",
  nextSafeAction:
    "Nicht erneut absenden. Zuerst den aktuellen Stand des Vorgangs prüfen.",
  nonDisclosing: false,
});

/**
 * The uncertain outcome deliberately offers no retry. Automatic retry of a
 * state transition whose result is unknown is how a case gets closed twice.
 */
export function retryOfferedFor(outcome: TransitionOutcome): boolean {
  return (
    outcome.kind === "refused" && outcome.refusal.kind !== "conflict_stale"
  );
}

/**
 * The action register for the desk. `capability` points into
 * `domain/capabilities.ts`; the interface must consult that register before
 * treating any of these as executable, and at this baseline none is.
 */
export const CASE_ACTIONS: readonly ActionDescriptor[] = Object.freeze([
  {
    actionId: "case.assign",
    label: "Vorgang zuweisen",
    required: "mandate_staff_assigned",
    impact: "low",
    capability: "case_assignment",
  },
  {
    actionId: "case.triage",
    label: "Vorgang einordnen",
    required: "mandate_staff_assigned",
    impact: "low",
    capability: "case_triage_transition",
  },
  {
    actionId: "case.record_response",
    label: "Antwort dokumentieren",
    required: "mandate_staff_assigned",
    impact: "high",
    capability: "case_response_record",
  },
  {
    actionId: "case.close",
    label: "Vorgang abschließen",
    required: "mandate_representative",
    impact: "consequential",
    capability: "case_triage_transition",
  },
]);

/**
 * A list projection safe to render. Confidential fields never reach the list
 * surface at all: the summary type carries no body text by construction, so a
 * list view cannot leak case content even if a future adapter over-fetches.
 */
export function listProjection(
  cases: readonly CaseSummary[],
): readonly CaseSummary[] {
  return cases.map((c) =>
    Object.freeze({
      caseId: c.caseId,
      reference: c.reference,
      subject: c.conflictRestricted ? "Zugriff eingeschränkt" : c.subject,
      state: c.state,
      receivedAt: c.receivedAt,
      mandateId: c.mandateId,
      assigneeLabel: c.assigneeLabel,
      conflictRestricted: c.conflictRestricted,
    }),
  );
}

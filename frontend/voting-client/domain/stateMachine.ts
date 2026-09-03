/**
 * The consequential-cast state machine.
 *
 * The point of this module is that success cannot be reached by a transition
 * the client makes on its own.  `accepted` is reachable only from an
 * authoritative acceptance, and the transition table says so: there is no edge
 * from `submitted` or `submission_uncertain` to `accepted` that a timeout, a
 * retry or a render can take.
 */

import type { JourneyState } from "./types";

export type JourneyEvent =
  | { readonly type: "handoff_accepted" }
  | { readonly type: "ballot_opened" }
  | { readonly type: "selection_changed" }
  | { readonly type: "review_opened" }
  | { readonly type: "review_returned" }
  | { readonly type: "submission_started" }
  | { readonly type: "submission_timed_out" }
  | { readonly type: "authoritative_acceptance" }
  | { readonly type: "authoritative_refusal" }
  | { readonly type: "receipt_obtained" }
  | { readonly type: "verification_confirmed" }
  | { readonly type: "cancelled" }
  | { readonly type: "context_expired" }
  | { readonly type: "failed" };

const TRANSITIONS: Readonly<
  Record<
    JourneyState,
    Readonly<Partial<Record<JourneyEvent["type"], JourneyState>>>
  >
> = Object.freeze({
  not_started: {
    handoff_accepted: "credential_accepted",
    failed: "failed",
    context_expired: "expired",
    cancelled: "cancelled",
  },
  credential_accepted: {
    ballot_opened: "prepared",
    cancelled: "cancelled",
    context_expired: "expired",
    failed: "failed",
  },
  prepared: {
    selection_changed: "prepared",
    review_opened: "reviewed",
    cancelled: "cancelled",
    context_expired: "expired",
    failed: "failed",
  },
  reviewed: {
    review_returned: "prepared",
    selection_changed: "prepared",
    submission_started: "submitted",
    cancelled: "cancelled",
    context_expired: "expired",
    failed: "failed",
  },
  submitted: {
    // A timeout moves to uncertainty, never to success and never to failure.
    submission_timed_out: "submission_uncertain",
    authoritative_acceptance: "accepted",
    authoritative_refusal: "failed",
    failed: "failed",
  },
  submission_uncertain: {
    // The only way out is an authoritative answer obtained by a status check.
    authoritative_acceptance: "accepted",
    authoritative_refusal: "failed",
    failed: "failed",
  },
  accepted: {
    receipt_obtained: "receipt_available",
    failed: "failed",
  },
  receipt_available: {
    verification_confirmed: "verified",
    failed: "failed",
  },
  verified: {},
  failed: {},
  cancelled: {},
  expired: {},
});

export const TERMINAL_STATES = Object.freeze([
  "verified",
  "failed",
  "cancelled",
  "expired",
] as const);

export function isTerminal(state: JourneyState): boolean {
  return (TERMINAL_STATES as readonly string[]).includes(state);
}

export function permittedEvents(state: JourneyState): JourneyEvent["type"][] {
  return Object.keys(TRANSITIONS[state]) as JourneyEvent["type"][];
}

export function canTransition(
  state: JourneyState,
  event: JourneyEvent["type"],
): boolean {
  return TRANSITIONS[state][event] !== undefined;
}

/**
 * Apply an event.  An event that is not permitted from the current state
 * leaves the state unchanged: the machine refuses rather than throwing, so a
 * double-click or a replayed action cannot advance the journey.
 */
export function transition(
  state: JourneyState,
  event: JourneyEvent,
): JourneyState {
  return TRANSITIONS[state][event.type] ?? state;
}

/**
 * Review must precede submission.  Stated separately from the table because a
 * gate reads it and because it is the invariant most worth naming.
 */
export function submissionPermittedFrom(state: JourneyState): boolean {
  return canTransition(state, "submission_started");
}

/**
 * The set of states in which the interface may use completed-cast language.
 * Everything else must use language that does not claim a vote was recorded.
 */
export const STATES_PERMITTING_CAST_SUCCESS_LANGUAGE = Object.freeze([
  "accepted",
  "receipt_available",
  "verified",
] as const);

export function castSuccessLanguagePermitted(state: JourneyState): boolean {
  return (
    STATES_PERMITTING_CAST_SUCCESS_LANGUAGE as readonly string[]
  ).includes(state);
}

/**
 * Phrases that may never appear before an authoritative acceptance.  The
 * browser tests scan the rendered page for these in every state that is not in
 * `STATES_PERMITTING_CAST_SUCCESS_LANGUAGE`.
 */
export const PROHIBITED_PREMATURE_SUCCESS_PHRASES = Object.freeze([
  "Sie haben abgestimmt",
  "Ihre Stimme wurde abgegeben",
  "Ihre Stimme wurde gezählt",
  "Sie haben teilgenommen",
  "Stimme erfolgreich",
  "Stimmabgabe erfolgreich",
  "Erfolgreich abgestimmt",
] as const);

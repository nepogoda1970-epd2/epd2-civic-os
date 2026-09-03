/**
 * The WS-04 session model.
 *
 * WS-04 differs from WS-03 in holding a persistent identity session, so the
 * interesting behaviour is in the states where that session stops being
 * sufficient: expiry, revocation, scope change, and authority ending part-way
 * through a task. Each of those has a defined, non-destructive resolution.
 */

import type { AssuranceLevel } from "../policies/authority";
import type {
  MandateScope,
  MandateSession,
  SafeRefusal,
  SessionState,
} from "./types";
import { sessionPermitsWork } from "./types";

export const ANONYMOUS_SESSION: MandateSession = Object.freeze({
  state: "anonymous",
  role: null,
  assurance: "none",
  scope: null,
  displayName: null,
  conflictRestricted: false,
});

export type SessionEvent =
  | { readonly type: "session_established" }
  | { readonly type: "step_up_completed" }
  | { readonly type: "step_up_demanded" }
  | { readonly type: "session_expired" }
  | { readonly type: "session_revoked" }
  | { readonly type: "scope_changed" }
  | { readonly type: "authority_suspended" }
  | { readonly type: "authority_expired" }
  | { readonly type: "signed_out" };

/**
 * The transition table. Two invariants hold and are asserted by tests:
 *
 *  1. No client-side event moves a session from a terminal negative state back
 *     into a working state. Recovery is always a fresh server-issued session.
 *  2. `session_established` and `step_up_completed` are recorded as *observed*
 *     server outcomes, never as decisions this client makes.
 */
const TRANSITIONS: Readonly<
  Record<SessionState, Partial<Record<SessionEvent["type"], SessionState>>>
> = Object.freeze({
  anonymous: {
    session_established: "authenticated",
  },
  authenticated: {
    step_up_completed: "stepped_up",
    step_up_demanded: "step_up_required",
    session_expired: "expired",
    session_revoked: "revoked",
    scope_changed: "scope_changed",
    authority_suspended: "authority_suspended",
    authority_expired: "authority_expired",
    signed_out: "anonymous",
  },
  stepped_up: {
    step_up_demanded: "step_up_required",
    session_expired: "expired",
    session_revoked: "revoked",
    scope_changed: "scope_changed",
    authority_suspended: "authority_suspended",
    authority_expired: "authority_expired",
    signed_out: "anonymous",
  },
  step_up_required: {
    step_up_completed: "stepped_up",
    session_expired: "expired",
    session_revoked: "revoked",
    signed_out: "anonymous",
  },
  expired: { signed_out: "anonymous" },
  revoked: { signed_out: "anonymous" },
  scope_changed: { signed_out: "anonymous" },
  authority_suspended: { signed_out: "anonymous" },
  authority_expired: { signed_out: "anonymous" },
});

export function nextSessionState(
  state: SessionState,
  event: SessionEvent,
): SessionState | null {
  const row = TRANSITIONS[state];
  const next = row[event.type];
  return next === undefined ? null : next;
}

export function applySessionEvent(
  session: MandateSession,
  event: SessionEvent,
): MandateSession {
  const next = nextSessionState(session.state, event);
  if (next === null) return session;
  const clears =
    next === "expired" ||
    next === "revoked" ||
    next === "anonymous" ||
    next === "scope_changed";
  return Object.freeze({
    state: next,
    role: clears ? null : session.role,
    assurance: assuranceFor(next, session.assurance),
    scope: clears ? null : session.scope,
    displayName: clears ? null : session.displayName,
    conflictRestricted: session.conflictRestricted,
  });
}

function assuranceFor(
  state: SessionState,
  previous: AssuranceLevel,
): AssuranceLevel {
  if (state === "stepped_up") return "stepped_up";
  if (state === "authenticated")
    return previous === "none" ? "standard" : previous;
  if (state === "step_up_required") return "standard";
  return "none";
}

/**
 * What the interface must do when a session stops permitting work. The rule is
 * that unsaved local composition is never silently discarded and never
 * silently submitted: the user is told exactly what state their work is in.
 */
export type SessionInterruption = {
  readonly state: SessionState;
  readonly refusal: SafeRefusal;
  readonly draftDisposition: "retained_in_memory" | "discarded";
};

const INTERRUPTIONS: Readonly<
  Partial<Record<SessionState, SessionInterruption>>
> = Object.freeze({
  expired: {
    state: "expired",
    refusal: {
      kind: "unauthenticated",
      reasonCode: "WS04-SESSION-001",
      safeMessage: "Ihre Sitzung ist abgelaufen.",
      committed: "not_committed",
      nextSafeAction:
        "Neu anmelden. Ihr nicht abgesendeter Entwurf bleibt in diesem Fenster erhalten.",
      nonDisclosing: false,
    },
    draftDisposition: "retained_in_memory",
  },
  revoked: {
    state: "revoked",
    refusal: {
      kind: "authority_revoked",
      reasonCode: "WS04-SESSION-002",
      safeMessage: "Ihre Sitzung wurde beendet.",
      committed: "unknown",
      nextSafeAction: "Wenden Sie sich an die zuständige Stelle.",
      nonDisclosing: false,
    },
    draftDisposition: "discarded",
  },
  scope_changed: {
    state: "scope_changed",
    refusal: {
      kind: "scope_mismatch",
      reasonCode: "WS04-SESSION-003",
      safeMessage: "Ihr Mandatsbezug hat sich geändert.",
      committed: "not_committed",
      nextSafeAction:
        "Neu anmelden. Inhalte des vorherigen Mandats werden nicht weiter angezeigt.",
      nonDisclosing: false,
    },
    draftDisposition: "discarded",
  },
  authority_suspended: {
    state: "authority_suspended",
    refusal: {
      kind: "authority_revoked",
      reasonCode: "WS04-SESSION-004",
      safeMessage: "Ihre Mandatsbefugnis ist derzeit ausgesetzt.",
      committed: "not_committed",
      nextSafeAction: "Lesezugriff bleibt bestehen, Handlungen sind gesperrt.",
      nonDisclosing: false,
    },
    draftDisposition: "retained_in_memory",
  },
  authority_expired: {
    state: "authority_expired",
    refusal: {
      kind: "authority_expired",
      reasonCode: "WS04-SESSION-005",
      safeMessage: "Ihre Mandatsperiode ist beendet.",
      committed: "not_committed",
      nextSafeAction:
        "Es sind keine Handlungen mehr möglich. Laufende Vorgänge liegen bei der zuständigen Stelle.",
      nonDisclosing: false,
    },
    draftDisposition: "retained_in_memory",
  },
});

export function interruptionFor(
  state: SessionState,
): SessionInterruption | null {
  if (sessionPermitsWork(state)) return null;
  return INTERRUPTIONS[state] ?? null;
}

/**
 * A scope change must not leave the previous mandate's content on screen. The
 * caller is required to consult this before rendering anything it had already
 * loaded.
 */
export function mustClearLoadedContent(
  previous: MandateScope | null,
  next: MandateScope | null,
): boolean {
  if (previous === null) return false;
  if (next === null) return true;
  return previous.mandateId !== next.mandateId;
}

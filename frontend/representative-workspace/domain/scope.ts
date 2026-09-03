/**
 * Mandate scope binding.
 *
 * The prohibition this module implements is structural rather than procedural:
 * a cross-mandate request must have no expressible form. Every protected read
 * or action carries exactly one `MandateScope`, resolved from the session; a
 * request that carries none, or that names a mandate other than the session's,
 * is refused here before any port is reached.
 *
 * This is presentation-side defence in depth. It is never a substitute for the
 * server-side scope decision, which does not exist yet — see
 * `domain/capabilities.ts`, `mandate_scope_resolution`.
 */

import { crossMandateAccessAvailableFor } from "../policies/authority";
import { SEARCH_POLICY } from "../policies/confidentiality";
import type {
  MandateScope,
  MandateSession,
  Result,
  SafeRefusal,
} from "./types";

/**
 * A request that has been proved to name exactly one mandate. The brand cannot
 * be produced anywhere but `bindScope`, so an unbound identifier cannot be
 * passed where a bound one is required.
 */
export type ScopeBound<T> = {
  readonly __scopeBound: unique symbol;
  readonly mandateId: string;
  readonly value: T;
};

const SCOPE_MISMATCH: SafeRefusal = Object.freeze({
  kind: "scope_mismatch",
  reasonCode: "WS04-SCOPE-001",
  safeMessage:
    "Dieser Vorgang gehört nicht zu Ihrem Mandat oder existiert nicht.",
  committed: "not_committed",
  nextSafeAction: "Zur Mandatsübersicht zurückkehren.",
  nonDisclosing: true,
});

const NO_SCOPE: SafeRefusal = Object.freeze({
  kind: "scope_mismatch",
  reasonCode: "WS04-SCOPE-002",
  safeMessage: "Für diese Sitzung ist kein Mandat aufgelöst.",
  committed: "not_committed",
  nextSafeAction: "Anmeldung mit Mandatsbezug erneut beginnen.",
  nonDisclosing: false,
});

/**
 * The single entry point through which an identifier becomes usable. The
 * refusal is identical for "outside your mandate" and "does not exist", so
 * membership of another mandate's case set cannot be probed.
 */
export function bindScope<T>(
  session: MandateSession,
  requestedMandateId: string | null,
  value: T,
): Result<ScopeBound<T>> {
  const scope = session.scope;
  if (scope === null) {
    return { ok: false, error: NO_SCOPE };
  }
  if (requestedMandateId !== null && requestedMandateId !== scope.mandateId) {
    return { ok: false, error: SCOPE_MISMATCH };
  }
  return {
    ok: true,
    value: {
      mandateId: scope.mandateId,
      value,
    } as ScopeBound<T>,
  };
}

/**
 * Scope is a single value. There is deliberately no function that returns a
 * list of mandates a session may act in, and no sentinel meaning "all".
 */
export function resolvedMandateIds(session: MandateSession): readonly string[] {
  return session.scope === null ? [] : [session.scope.mandateId];
}

export function scopeIsSingular(session: MandateSession): boolean {
  return resolvedMandateIds(session).length <= 1;
}

/** Total function. Cross-mandate access is unavailable for every role. */
export function mayReadAcrossMandates(session: MandateSession): false {
  if (session.role !== null) {
    void crossMandateAccessAvailableFor(session.role);
  }
  return false;
}

/**
 * A search request is admissible only if it is scoped to the session's single
 * mandate. An unscoped search has no admissible form.
 */
export function searchRequestAdmissible(input: {
  readonly session: MandateSession;
  readonly scopeMandateId: string | null;
}): boolean {
  if (!SEARCH_POLICY.requiresServerAuthorization) return false;
  if (!SEARCH_POLICY.requiresExplicitScope) return false;
  if (input.scopeMandateId === null) return false;
  const ids = resolvedMandateIds(input.session);
  return ids.length === 1 && ids[0] === input.scopeMandateId;
}

export function authorityUsable(scope: MandateScope | null): boolean {
  return scope !== null && scope.authorityActive;
}

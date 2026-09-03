/**
 * Conflict of interest restrictions.
 *
 * A restriction limits what a representative may see and do. The rules that
 * make it meaningful rather than decorative:
 *
 *  1. A subject may never clear a restriction over themselves.
 *  2. Unknown is not cleared. If the restriction register cannot be read, the
 *     workspace restricts rather than permits.
 *  3. A restriction hides content non-disclosingly, so that its existence does
 *     not itself reveal which case a representative is conflicted on.
 */

import {
  conflictOfficerMay,
  maySelfClearConflict,
  type Ws04Role,
} from "../policies/authority";
import type {
  ActionDescriptor,
  ConflictRestriction,
  MandateSession,
  SafeRefusal,
} from "./types";

export type RestrictionKnowledge =
  | {
      readonly known: true;
      readonly restrictions: readonly ConflictRestriction[];
    }
  | { readonly known: false; readonly reason: string };

/**
 * Fail-closed. An unreadable register yields "restricted", not "unrestricted".
 * This is the behaviour at the current baseline, because the register is
 * `BLOCKED_BY_DEPENDENCY`.
 */
export function restrictedFor(
  knowledge: RestrictionKnowledge,
  scopeLabel: string,
): boolean {
  if (!knowledge.known) return true;
  return knowledge.restrictions.some(
    (r) => r.active && r.scopeLabel === scopeLabel,
  );
}

export function anyRestrictionActive(knowledge: RestrictionKnowledge): boolean {
  if (!knowledge.known) return true;
  return knowledge.restrictions.some((r) => r.active);
}

/** Total function. Neither role nor circumstance makes this true. */
export function mayClearOwnRestriction(role: Ws04Role): false {
  return maySelfClearConflict(role);
}

/**
 * What a conflict officer may do. The officer is a narrow secondary role, not
 * a representative administrator: it may act on the conflict record and may
 * not read case content.
 */
export function officerMay(capability: string): boolean {
  return conflictOfficerMay(capability);
}

export const RESTRICTED_REFUSAL: SafeRefusal = Object.freeze({
  kind: "conflict_restricted",
  reasonCode: "WS04-CONFLICT-001",
  safeMessage: "Für diesen Bereich besteht eine Zugriffsbeschränkung.",
  committed: "not_committed",
  nextSafeAction:
    "Die zuständige Stelle für Interessenkonflikte entscheidet über die Beschränkung.",
  /**
   * Non-disclosing: the message is identical whether the item exists, lies
   * outside scope, or is restricted, so the restriction does not point at the
   * conflicted subject matter.
   */
  nonDisclosing: true,
});

export const UNKNOWN_RESTRICTION_REFUSAL: SafeRefusal = Object.freeze({
  kind: "conflict_restricted",
  reasonCode: "WS04-CONFLICT-002",
  safeMessage: "Zugriffsbeschränkungen können derzeit nicht geprüft werden.",
  committed: "not_committed",
  nextSafeAction:
    "Bis zur Prüfbarkeit bleibt der Zugriff gesperrt. Der geregelte Weg bleibt offen.",
  nonDisclosing: false,
});

export function refusalFor(knowledge: RestrictionKnowledge): SafeRefusal {
  return knowledge.known ? RESTRICTED_REFUSAL : UNKNOWN_RESTRICTION_REFUSAL;
}

/**
 * A restricted session may still see that a restriction exists over its own
 * mandate — otherwise the workspace would appear simply broken — but never the
 * reason, and never the protected content.
 */
export function restrictionNotice(session: MandateSession): string | null {
  if (!session.conflictRestricted) return null;
  return "Für Teile Ihres Mandats besteht eine Zugriffsbeschränkung. Die Begründung liegt bei der zuständigen Stelle.";
}

export const CONFLICT_ACTIONS: readonly ActionDescriptor[] = Object.freeze([
  {
    actionId: "conflict.view_register_entry",
    label: "Eintrag im Konfliktregister ansehen",
    required: "conflict_officer",
    impact: "read",
    capability: "conflict_restriction_read",
  },
  {
    actionId: "conflict.record_assessment_proposal",
    label: "Bewertungsvorschlag erfassen",
    required: "conflict_officer",
    impact: "high",
    capability: "conflict_restriction_change",
  },
  {
    actionId: "conflict.request_recusal_review",
    label: "Befangenheitsprüfung anfordern",
    required: "conflict_officer",
    impact: "high",
    capability: "conflict_restriction_change",
  },
]);

/**
 * No descriptor exists for clearing one's own restriction, and the test suite
 * asserts that none can appear.
 */
export const FORBIDDEN_CONFLICT_ACTION_IDS = Object.freeze([
  "conflict.clear_own",
  "conflict.remove_own_flag",
  "conflict.self_clear",
  "conflict.override",
] as const);

export function conflictRegisterClean(): boolean {
  const ids = CONFLICT_ACTIONS.map((a) => a.actionId);
  return !FORBIDDEN_CONFLICT_ACTION_IDS.some((f) => ids.includes(f));
}

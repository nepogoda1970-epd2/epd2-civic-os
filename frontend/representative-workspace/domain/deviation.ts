/**
 * Deviation records.
 *
 * A deviation is a representative's stated divergence from a governed
 * democratic decision. The invariants that keep it honest:
 *
 *  1. A deviation references a decision; it never modifies one. There is no
 *     code path from this module to a decision's state.
 *  2. A deviation is a record with provenance and a version, not a free-text
 *     note. Superseding is explicit, so the history stays legible.
 *  3. Recording a deviation is not publishing it. Publication is a separate
 *     proposal that the publication authority decides.
 */

import { clientMayDecide } from "../policies/boundaries";
import type {
  ActionDescriptor,
  DeviationRecord,
  Result,
  SafeRefusal,
} from "./types";

export type DeviationDraft = {
  readonly issue: string;
  readonly representativePosition: string;
  readonly referencedDecision: string | null;
  readonly explanation: string;
  readonly supersedes: string | null;
};

export const DEVIATION_LIMITS = Object.freeze({
  issueMaxLength: 200,
  positionMaxLength: 2000,
  explanationMinLength: 40,
  explanationMaxLength: 8000,
});

const INVALID: (code: string, message: string) => SafeRefusal = (
  code,
  message,
) =>
  Object.freeze({
    kind: "forbidden",
    reasonCode: code,
    safeMessage: message,
    committed: "not_committed",
    nextSafeAction: "Eingabe ergänzen und erneut prüfen.",
    nonDisclosing: false,
  });

/**
 * Local shape validation only. A local pass is not an acceptance: the server
 * validates independently, and this function's success says nothing about
 * whether the record can be stored.
 */
export function validateDeviationDraft(
  draft: DeviationDraft,
): Result<DeviationDraft> {
  if (draft.issue.trim().length === 0) {
    return {
      ok: false,
      error: INVALID("WS04-DEV-001", "Das Thema fehlt."),
    };
  }
  if (draft.issue.length > DEVIATION_LIMITS.issueMaxLength) {
    return {
      ok: false,
      error: INVALID("WS04-DEV-002", "Das Thema ist zu lang."),
    };
  }
  if (draft.referencedDecision === null) {
    return {
      ok: false,
      error: INVALID(
        "WS04-DEV-003",
        "Eine Abweichung muss sich auf eine Entscheidung beziehen.",
      ),
    };
  }
  if (draft.explanation.trim().length < DEVIATION_LIMITS.explanationMinLength) {
    return {
      ok: false,
      error: INVALID(
        "WS04-DEV-004",
        "Die Begründung ist zu kurz. Eine Abweichung ist ohne Begründung nicht nachvollziehbar.",
      ),
    };
  }
  if (draft.explanation.length > DEVIATION_LIMITS.explanationMaxLength) {
    return {
      ok: false,
      error: INVALID("WS04-DEV-005", "Die Begründung ist zu lang."),
    };
  }
  return { ok: true, value: draft };
}

/**
 * The referenced decision cannot be resolved at this baseline, so a reference
 * is carried as unverified text and displayed as such. The workspace never
 * claims a reference is valid.
 */
export const DECISION_REFERENCE_UNVERIFIED =
  "Bezug ungeprüft: die Entscheidung kann derzeit nicht aufgelöst werden." as const;

export function referenceVerified(record: DeviationRecord): boolean {
  void record;
  return false;
}

/** Total function. A deviation never alters the decision it references. */
export function deviationAltersDecision(): false {
  void clientMayDecide("governed_decision");
  return false;
}

/**
 * Superseding preserves the earlier record. The interface must render both,
 * because a deviation history that quietly rewrites itself is worse than none.
 */
export function supersedes(
  earlier: DeviationRecord,
  later: DeviationRecord,
): boolean {
  return later.supersedes === earlier.deviationId;
}

export const DEVIATION_ACTIONS: readonly ActionDescriptor[] = Object.freeze([
  {
    actionId: "deviation.record",
    label: "Abweichung erfassen",
    required: "mandate_representative",
    impact: "consequential",
    capability: "deviation_record_write",
  },
  {
    actionId: "deviation.supersede",
    label: "Abweichung ersetzen",
    required: "mandate_representative",
    impact: "consequential",
    capability: "deviation_record_write",
  },
]);

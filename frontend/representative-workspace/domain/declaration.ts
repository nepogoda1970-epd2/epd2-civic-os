/**
 * Declarations: meetings, interest declarations, disclosures.
 *
 * These are compliance obligations. The rule that governs every line here is
 * that this workspace must never state or imply that an obligation has been
 * met. It can accept a composition, it can report that transmission is
 * blocked, and it must say plainly that the obligation therefore remains open.
 */

import type {
  ActionDescriptor,
  DeclarationKind,
  DeclarationRecord,
  Result,
  SafeRefusal,
} from "./types";

export type DeclarationDraft = {
  readonly kind: DeclarationKind;
  readonly subject: string;
  readonly occurredAt: string;
  readonly counterparty: string;
  readonly summary: string;
};

export const DECLARATION_LIMITS = Object.freeze({
  subjectMaxLength: 200,
  counterpartyMaxLength: 200,
  summaryMaxLength: 4000,
});

function invalid(code: string, message: string): SafeRefusal {
  return Object.freeze({
    kind: "forbidden",
    reasonCode: code,
    safeMessage: message,
    committed: "not_committed",
    nextSafeAction: "Angaben ergänzen.",
    nonDisclosing: false,
  });
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function validateDeclarationDraft(
  draft: DeclarationDraft,
): Result<DeclarationDraft> {
  if (draft.subject.trim().length === 0) {
    return {
      ok: false,
      error: invalid("WS04-DECL-001", "Der Gegenstand fehlt."),
    };
  }
  if (draft.subject.length > DECLARATION_LIMITS.subjectMaxLength) {
    return {
      ok: false,
      error: invalid("WS04-DECL-002", "Der Gegenstand ist zu lang."),
    };
  }
  if (!ISO_DATE.test(draft.occurredAt)) {
    return {
      ok: false,
      error: invalid("WS04-DECL-003", "Das Datum ist unvollständig."),
    };
  }
  if (draft.kind === "meeting" && draft.counterparty.trim().length === 0) {
    return {
      ok: false,
      error: invalid(
        "WS04-DECL-004",
        "Ein Treffen ist ohne Gegenüber nicht dokumentierbar.",
      ),
    };
  }
  if (draft.summary.length > DECLARATION_LIMITS.summaryMaxLength) {
    return {
      ok: false,
      error: invalid("WS04-DECL-005", "Die Zusammenfassung ist zu lang."),
    };
  }
  return { ok: true, value: draft };
}

/**
 * The statement the interface is required to display when submission is
 * blocked. It is deliberately blunt: an unsubmitted declaration leaves a legal
 * obligation open, and the representative has to know that.
 */
export const OBLIGATION_REMAINS_OPEN =
  "Diese Erklärung wurde nicht übermittelt. Die Meldepflicht bleibt offen und ist auf dem geregelten Weg zu erfüllen." as const;

/** Total function at this baseline: nothing here discharges an obligation. */
export function obligationDischarged(record: DeclarationRecord): boolean {
  return record.state === "accepted" && record.submittedAt !== null;
}

export function submissionBlockedRefusal(): SafeRefusal {
  return Object.freeze({
    kind: "blocked",
    reasonCode: "WS04-DECL-BLOCKED",
    safeMessage: "Erklärungen können derzeit nicht übermittelt werden.",
    committed: "not_committed",
    nextSafeAction: OBLIGATION_REMAINS_OPEN,
    nonDisclosing: false,
  });
}

export const DECLARATION_ACTIONS: readonly ActionDescriptor[] = Object.freeze([
  {
    actionId: "declaration.submit",
    label: "Erklärung übermitteln",
    required: "mandate_representative",
    impact: "consequential",
    capability: "declaration_submission",
  },
]);

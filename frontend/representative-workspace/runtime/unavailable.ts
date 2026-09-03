/**
 * Controlled unavailability.
 *
 * Every refusal a port can return is constructed here, so each one carries the
 * four things the operator needs: what happened, whether anything was
 * committed, what may safely be done next, and whether the message must avoid
 * disclosing existence. A port has no other way to build a refusal, so it
 * cannot invent a cheerier one.
 *
 * The refusal catalogue below names, for each port, the exact missing
 * dependency recorded in `domain/capabilities.ts`. That coupling is asserted by
 * the validator: a refusal may not claim a dependency the register does not
 * record.
 */

import type { Result, SafeRefusal } from "../domain/types";

export type UnavailabilityInput = {
  readonly reasonCode: string;
  readonly safeMessage: string;
  readonly committed: SafeRefusal["committed"];
  readonly nextSafeAction: string;
  readonly kind?: SafeRefusal["kind"];
  readonly nonDisclosing?: boolean;
};

export function refusal(input: UnavailabilityInput): SafeRefusal {
  return Object.freeze({
    kind: input.kind ?? "blocked",
    reasonCode: input.reasonCode,
    safeMessage: input.safeMessage,
    committed: input.committed,
    nextSafeAction: input.nextSafeAction,
    nonDisclosing: input.nonDisclosing ?? false,
  });
}

export function unavailable<T>(input: UnavailabilityInput): Result<T> {
  return { ok: false, error: refusal(input) };
}

const GOVERNED_PATH =
  "Der geregelte Weg über die zuständige Stelle bleibt offen.";
const RESTART_SESSION =
  "Melden Sie sich erneut an. Nicht abgesendete Eingaben bleiben in diesem Fenster erhalten.";

/**
 * The production refusals. Every one of these corresponds to a capability whose
 * status is BLOCKED_BY_DEPENDENCY, and the `capability` field is the join key
 * the validator checks.
 */
export const PRODUCTION_REFUSALS = Object.freeze({
  session: {
    capability: "mandate_session_establishment",
    reasonCode: "WS04_MANDATE_SESSION_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Eine mandatsgebundene Anmeldung ist derzeit nicht möglich. Es existiert keine freigegebene Laufzeit dafür.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  scope: {
    capability: "mandate_scope_resolution",
    reasonCode: "WS04_MANDATE_REGISTER_NOT_ACCEPTED",
    safeMessage: "Ihr Mandatsbezug kann derzeit nicht aufgelöst werden.",
    committed: "not_committed" as const,
    nextSafeAction: RESTART_SESSION,
    kind: "unavailable" as const,
  },
  stepUp: {
    capability: "step_up_authentication",
    reasonCode: "WS04_STEP_UP_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Die zusätzliche Authentisierung ist derzeit nicht verfügbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "step_up_required" as const,
  },
  caseList: {
    capability: "case_intake_list",
    reasonCode: "WS04_CASE_INTAKE_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Die Vorgangsliste ist derzeit nicht abrufbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  caseDetail: {
    capability: "case_detail_read",
    reasonCode: "WS04_CASE_DETAIL_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Dieser Vorgang ist derzeit nicht abrufbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
    /** Identical wording to the scope refusal, by design. */
    nonDisclosing: true,
  },
  caseMutation: {
    capability: "case_triage_transition",
    reasonCode: "WS04_CASE_TRANSITION_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Änderungen an Vorgängen können derzeit nicht gespeichert werden. Es wurde nichts geändert.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
  },
  caseSearch: {
    capability: "case_scoped_search",
    reasonCode: "WS04_SCOPED_SEARCH_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Die Suche ist derzeit nicht verfügbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  position: {
    capability: "position_draft_read",
    reasonCode: "WS04_POSITION_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Positionen sind derzeit nicht abrufbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  positionWrite: {
    capability: "position_draft_write",
    reasonCode: "WS04_POSITION_PERSISTENCE_NOT_ACCEPTED",
    safeMessage:
      "Entwürfe können derzeit nicht gespeichert werden. Ihr Text bleibt nur in diesem Fenster erhalten.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
  },
  deviation: {
    capability: "deviation_record_write",
    reasonCode: "WS04_DEVIATION_CONTRACT_NOT_ACCEPTED",
    safeMessage:
      "Abweichungen können derzeit nicht erfasst werden. Es wurde nichts aufgezeichnet.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
  },
  decisionReference: {
    capability: "deviation_decision_reference",
    reasonCode: "WS04_DECISION_RESOLUTION_NOT_ACCEPTED",
    safeMessage:
      "Der Bezug auf die Entscheidung kann derzeit nicht geprüft werden.",
    committed: "not_committed" as const,
    nextSafeAction:
      "Die Angabe wird ungeprüft übernommen und ist als ungeprüft gekennzeichnet.",
    kind: "unavailable" as const,
  },
  declaration: {
    capability: "declaration_submission",
    reasonCode: "WS04_DECLARATION_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Erklärungen können derzeit nicht übermittelt werden.",
    committed: "not_committed" as const,
    nextSafeAction:
      "Die Meldepflicht bleibt offen und ist auf dem geregelten Weg zu erfüllen.",
  },
  publicationProposal: {
    capability: "publication_proposal_submission",
    reasonCode: "WS04_PUBLICATION_PROPOSAL_MODEL_ABSENT",
    safeMessage:
      "Vorschläge zur Veröffentlichung können derzeit nicht eingereicht werden.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
  },
  publicationState: {
    capability: "publication_state_observation",
    reasonCode: "WS04_PUBLICATION_STATE_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Der Veröffentlichungsstand ist derzeit nicht feststellbar.",
    committed: "unknown" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  conflict: {
    capability: "conflict_restriction_read",
    reasonCode: "WS04_CONFLICT_REGISTER_NOT_ACCEPTED",
    safeMessage: "Zugriffsbeschränkungen können derzeit nicht geprüft werden.",
    committed: "not_committed" as const,
    nextSafeAction:
      "Bis zur Prüfbarkeit bleibt der Zugriff gesperrt. " + GOVERNED_PATH,
    kind: "conflict_restricted" as const,
  },
  registry: {
    capability: "registry_read_reference",
    reasonCode: "WS04_REGISTRY_READ_CONTRACT_NOT_ACCEPTED",
    safeMessage: "Registerangaben sind derzeit nicht abrufbar.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  eligibility: {
    capability: "eligibility_status_display",
    reasonCode: "WS04_ELIGIBILITY_STATUS_NOT_AVAILABLE",
    safeMessage:
      "Ein Berechtigungsstatus liegt nicht vor. Dieser Arbeitsbereich entscheidet darüber nicht.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
  audit: {
    capability: "audit_trail_read",
    reasonCode: "WS04_CONTROL_PLANE_NOT_STARTED",
    safeMessage:
      "Ein Prüfpfad ist nicht abrufbar. Es existiert keine freigegebene Kontrollebene.",
    committed: "not_committed" as const,
    nextSafeAction: GOVERNED_PATH,
    kind: "unavailable" as const,
  },
} as const);

export type ProductionRefusalKey = keyof typeof PRODUCTION_REFUSALS;

export function productionRefusal(key: ProductionRefusalKey): SafeRefusal {
  return refusal(PRODUCTION_REFUSALS[key]);
}

export function productionUnavailable<T>(key: ProductionRefusalKey): Result<T> {
  return { ok: false, error: productionRefusal(key) };
}

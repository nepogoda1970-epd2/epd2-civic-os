/**
 * English translation layer.
 *
 * Present so DE/EN readiness is preserved.  It carries text and nothing else:
 * no route, no context, no eligibility, no ballot semantics and no cast
 * semantics is reachable from this module, and no language preference is
 * stored anywhere in this workspace.
 */

export const CONTENT_VERSION_EN = "F04-EN-1.0.0";

export const WS03_CONTENT_EN = Object.freeze({
  workspace: "Voting area",
  credentialTitle: "Take up voting entitlement",
  ballotTitle: "Ballot",
  reviewTitle: "Check your vote",
  receiptTitle: "Verify your submission",
  languageChangesNothing:
    "Changing the interface language changes no route authority, no election context, no eligibility, no ballot semantics, no legal effect and no cast semantics.",
} as const);

/**
 * The German page titles are authoritative. This mapping exists so a
 * translation cannot silently become the canonical label.
 */
export const AUTHORITATIVE_DE_TITLES = Object.freeze({
  "/vote/credential": "Stimmberechtigung übernehmen",
  "/vote/ballot": "Stimmzettel",
  "/vote/review": "Stimme prüfen",
  "/vote/receipt": "Stimmabgabe verifizieren",
} as const);

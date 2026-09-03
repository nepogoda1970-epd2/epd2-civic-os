/**
 * English translation layer.
 *
 * It exists to prove a property rather than to serve users: switching language
 * changes no route authority, no mandate scope, no authorization outcome, no
 * case state and no publication state. `policies/language.ts` states that as
 * `localeAffects(): false`, a test exercises both locales against the same
 * decisions, and this file is deliberately partial — only the strings the
 * language test needs are translated, so nothing here can drift into being a
 * second, subtly different specification of the interface.
 */

export const CONTENT_VERSION_EN = "F05-EN-1.0.0";

export const WS04_CONTENT_EN = Object.freeze({
  workspace: "Mandate workspace",
  boundaryNotice:
    "Separate workspace for mandate work. There is no system-wide administrative access and no access to the voting domain.",
  candidateNotice:
    "Prototype under construction. This interface is not accepted, not certified and not legally activated. No real cases are processed.",
  publicationNotApproval:
    "Publication proposal. This is not a publication and not an approval.",
  obligationOpen:
    "This declaration was not transmitted. The reporting obligation remains open.",
  singleMandateOnly:
    "This workspace shows data for exactly one mandate. A cross-mandate view does not exist.",
} as const);

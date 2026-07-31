/**
 * PACK-15 — voting trust boundary policy (identity side and voting origin).
 *
 * Pure data and predicates. No React, no network access, no browser API.
 * The single purpose of this module is to make the separation between the
 * identity domain (WS-02) and the voting origin (WS-03) checkable by a
 * test rather than by review comment.
 *
 * Source of truth: docs/packs/PACK-15/PACK-15-RENDITION-SPECIFICATION.md
 * (§4, §7.1, §7.2) and docs/packs/PACK-15/PACK-15-CONTENT-CATALOGUE-DE.md
 * (§12). NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
 */

export type ParticipationStateId =
  | "eligibility_pending"
  | "eligibility_confirmed"
  | "review_required"
  | "eligibility_denied"
  | "access_queued"
  | "access_available"
  | "access_expired"
  | "dispute_open";

/**
 * Non-colour state carrier. `FIR-UX-009` requires the marker to be a shape
 * or a symbol, never a colour and never a colour alone.
 */
export type ParticipationMarkerKind =
  | "dot"
  | "clock"
  | "check"
  | "crossed"
  | "key"
  | "expired";

export type ParticipationState = Readonly<{
  id: ParticipationStateId;
  labelDe: string;
  markerKind: ParticipationMarkerKind;
  actions: readonly string[];
}>;

/**
 * The complete set of participation states the identity side may ever
 * display. There is deliberately no "voted" state and none may be added:
 * the participant's identity-side view ends at „Zugang verfügbar".
 */
export const PARTICIPATION_STATES: readonly ParticipationState[] = [
  {
    id: "eligibility_pending",
    labelDe: "Antrag eingegangen",
    markerKind: "dot",
    actions: ["withdraw_request"],
  },
  {
    id: "eligibility_confirmed",
    labelDe: "Teilnahmeberechtigt",
    markerKind: "check",
    actions: ["retrieve_access"],
  },
  {
    id: "review_required",
    labelDe: "In Prüfung",
    markerKind: "clock",
    actions: ["submit_evidence"],
  },
  {
    id: "eligibility_denied",
    labelDe: "Nicht teilnahmeberechtigt",
    markerKind: "crossed",
    actions: ["view_reason", "open_dispute"],
  },
  {
    id: "access_queued",
    labelDe: "Zugang wird vorbereitet",
    markerKind: "clock",
    actions: [],
  },
  {
    id: "access_available",
    labelDe: "Zugang verfügbar",
    markerKind: "key",
    actions: ["enter_voting_area"],
  },
  {
    id: "access_expired",
    labelDe: "Zugang abgelaufen",
    markerKind: "expired",
    actions: ["report_access_problem"],
  },
  {
    id: "dispute_open",
    labelDe: "Widerspruch in Bearbeitung",
    markerKind: "clock",
    actions: ["view_dispute", "withdraw_dispute"],
  },
] as const;

/**
 * States that belong exclusively to the voting origin. The identity domain
 * must never receive, store, infer or render any of these: each of them
 * would be an individual participation status, and an individual
 * participation status is the link between a person and a ballot that this
 * architecture exists to prevent.
 */
export const PROHIBITED_IDENTITY_SIDE_STATES: readonly string[] = [
  "redeemed",
  "voted",
  "ballot_cast",
  "ballot_accepted",
  "participation_confirmed",
] as const;

/**
 * Channels over which voting access may never be delivered. A credential
 * that can be forwarded, stored or shown could also be taken or coerced
 * (PACK-15-CONTENT-CATALOGUE-DE.md §12.7).
 */
export const PROHIBITED_DELIVERY_CHANNELS: readonly string[] = [
  "email",
  "sms",
  "push_notification",
  "clipboard",
  "url_query",
  "url_fragment",
  "downloadable_file",
  "print_or_pdf",
  "operator_screen",
  "logs",
  "analytics",
  "error_reporting",
  "shared_browser_storage",
] as const;

/**
 * The only permitted delivery channel: the credential is minted inside the
 * isolated voting origin and redeemed there immediately, in one pass.
 */
export const PERMITTED_DELIVERY_CHANNEL = "isolated_ws03_origin" as const;

/** Voting origins the identity side is allowed to hand off to. */
export const ALLOWED_WS03_ORIGINS: readonly string[] = [
  "https://vote.epd.example",
] as const;

/**
 * Everything the voting origin must not share with the identity origin.
 * Every field is stated as a prohibition so that a regression is a failing
 * assertion rather than a missing one.
 */
export const VOTING_ORIGIN_ISOLATION = {
  sharedCookies: false,
  sharedLocalStorage: false,
  sharedSessionStorage: false,
  sharedIndexedDb: false,
  sharedServiceWorker: false,
  identitySession: false,
  analytics: "none",
  fingerprinting: false,
  sharedTelemetry: false,
  sharedErrorReportingIdentity: false,
  thirdPartyScripts: "none",
  referrerPolicy: "no-referrer",
  cachePolicy: "no-store",
  frameAncestors: "none",
  persistentMemberIdentifier: false,
  credentialMaterialPersisted: false,
  returnCarriesIdentityToken: false,
  returnCarriesVotingIdentifier: false,
} as const;

export type VotingOriginIsolation = typeof VOTING_ORIGIN_ISOLATION;

/** Fails closed: only the isolated voting origin is a permitted channel. */
export function credentialDeliveryPermitted(channel: string): boolean {
  if (PROHIBITED_DELIVERY_CHANNELS.includes(channel)) return false;
  return channel === PERMITTED_DELIVERY_CHANNEL;
}

/**
 * Fails closed: a state is visible on the identity side only when it is one
 * of the declared participation states and not one of the prohibited
 * voting-origin states.
 */
export function participationStateVisibleToIdentitySide(
  state: string,
): boolean {
  if (PROHIBITED_IDENTITY_SIDE_STATES.includes(state)) return false;
  return PARTICIPATION_STATES.some((entry) => entry.id === state);
}

/** Lookup helper used by the rendition layer; throws on unknown states. */
export function participationStateById(
  id: ParticipationStateId,
): ParticipationState {
  const state = PARTICIPATION_STATES.find((entry) => entry.id === id);
  if (!state) throw new Error(`Unknown participation state: ${id}`);
  return state;
}

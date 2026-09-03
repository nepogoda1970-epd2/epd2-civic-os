/**
 * WS-04 workspace identity and trust boundary.
 *
 * Every value here is taken from an accepted record rather than invented:
 * `services/identity-service/src/epd2_identity_service/workspaces.py` (the
 * server-side workspace policy), `frontend/web-shell/foundation/workspaces.ts`
 * (the accepted frontend policy) and
 * `docs/packs/PACK-14/PACK-14-CROSS-WORKSPACE-SESSION-MATRIX.md` row WS-04.
 *
 * One value is deliberately NOT copied. The accepted frontend policy records
 * `routePrefix: "/Mandate Holder"` — a display name in a URL field, containing
 * a space and capitals, which cannot be a route prefix. The target frontend
 * architecture and the FRONT-05 working contract both say `/representative`.
 * This package uses `/representative`, does not modify the accepted record, and
 * carries the conflict as an open reconciliation item for governance. See
 * `docs/frontend/FRONT-05-WS04-SOURCE-RECONCILIATION.md`.
 */

export const WS04_WORKSPACE_ID = "WS-04" as const;
export const WS04_CANONICAL_NAME = "Mandate Holder Workspace" as const;
export const WS04_ORIGIN = "https://represent.epd.example" as const;
export const WS04_ROUTE_PREFIX = "/representative" as const;

/** The accepted record's value, quoted so the conflict is visible in code. */
export const WS04_ACCEPTED_ROUTE_PREFIX_LITERAL = "/Mandate Holder" as const;
export const WS04_ROUTE_PREFIX_RECONCILIATION =
  "OPEN_GOVERNANCE_ITEM: accepted frontend policy records a display name in the route-prefix field" as const;

/** Data classes this workspace handles, from the accepted workspace policy. */
export const WS04_DATA_CLASSES = Object.freeze([
  "MANDATE_INTERNAL",
  "CASE_CONFIDENTIAL",
  "PUBLIC_APPROVED",
] as const);

export type Ws04DataClass = (typeof WS04_DATA_CLASSES)[number];

/**
 * The trust boundary. `bootstrap: full` and `issuesIdentitySession: true` come
 * from the accepted server-side policy: unlike WS-03, this workspace does hold
 * an identity session. That makes the isolation rules different in kind — the
 * question is not "no identity at all" but "no authority beyond this mandate".
 */
export const WS04_BOUNDARY = Object.freeze({
  separateOrigin: true,
  bootstrap: "full",
  issuesIdentitySession: true,
  riskTier: 2,
  cookiesHostOnlyOnly: true,
  parentDomainCookie: false,
  crossWorkspaceCookieDomain: false,
  sharedSessionProvider: false,
  sharedStorageAdapter: false,
  sharedPrivilegedStorageBridge: false,
  browserStorageAsIdentity: false,
  uncontrolledCrossOriginPostMessage: false,
  crossOriginAnalyticsIdentity: false,
  crossWorkspaceCorrelationIdentifier: false,
  votingDomainAccess: false,
  mobileClientSurface: false,
  universalAdminMode: false,
  reauthenticateWhenCrossingFromLowerTier: true,
} as const);

/**
 * Browser storage. The accepted policy says `preferences-only`, so this
 * workspace may keep a UI preference — and nothing else. The sensitivity of its
 * data classes means every case-bearing value is refused regardless of the
 * preference allowance.
 */
export const WS04_STORAGE_POLICY = Object.freeze({
  tier: "preferences-only",
  permittedPurposes: Object.freeze(["ui-preference"] as const),
  forbiddenPurposes: Object.freeze([
    "case-content",
    "case-identifier",
    "correspondence",
    "declaration-content",
    "position-draft",
    "deviation-draft",
    "attachment",
    "identity",
    "session",
    "credential",
    "secret",
    "authority-decision",
    "conflict-status",
    "voting-linked-identifier",
  ] as const),
  indexedDb: false,
  cacheStorageForSensitiveResponses: false,
  serviceWorker: "own-origin-only-when-approved",
  serviceWorkerRegisteredByThisPackage: false,
} as const);

export const BROWSER_STORAGE_KINDS = Object.freeze([
  "cookie",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "cacheStorage",
  "serviceWorker",
] as const);

export type BrowserStorageKind = (typeof BROWSER_STORAGE_KINDS)[number];

/**
 * Total function. An unknown purpose is refused rather than defaulted, and the
 * only permitted combination is a UI preference in a cookie or localStorage.
 */
export function storageAllowed(kind: string, purpose: string): boolean {
  const permitted = WS04_STORAGE_POLICY.permittedPurposes as readonly string[];
  if (!permitted.includes(purpose)) return false;
  return kind === "cookie" || kind === "localStorage";
}

/** Outbound request classes this frontend may originate. */
export const PERMITTED_REQUEST_ORIGIN_CLASSES = Object.freeze([
  "ws04-same-origin-document",
  "ws04-same-origin-static-asset",
] as const);

export function requestOriginClassPermitted(value: string): boolean {
  return (PERMITTED_REQUEST_ORIGIN_CLASSES as readonly string[]).includes(
    value,
  );
}

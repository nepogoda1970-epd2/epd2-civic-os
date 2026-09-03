/**
 * WS-03 isolation invariants.
 *
 * These values are the frontend-side restatement of the accepted PACK-15
 * browser baseline that FRONT-03 C1 carried, tightened where FRONT-04 chooses
 * the stricter reading.  Nothing here is configuration: the fields are frozen
 * and the tests assert their exact values, so weakening the boundary requires
 * changing a value that a gate reads.
 */

export const WS03_WORKSPACE_ID = "WS-03" as const;
export const WS03_ORIGIN = "https://vote.epd.example" as const;
export const WS03_ROUTE_PREFIX = "/vote" as const;

/**
 * The exact isolation posture of this workspace.  FRONT-03 C1 proved cookies,
 * localStorage, sessionStorage and same-origin-only requests at runtime on
 * `/vote`; IndexedDB, CacheStorage and Service Worker were policy-only there.
 * FRONT-04 keeps every value and adds runtime proof for the remainder.
 */
export const WS03_ISOLATION = Object.freeze({
  separateOrigin: true,
  sharedCookies: false,
  sharedLocalStorage: false,
  sharedSessionStorage: false,
  sharedIndexedDb: false,
  sharedCacheStorage: false,
  sharedServiceWorker: false,
  ownServiceWorker: false,
  identitySession: false,
  memberSessionAccepted: false,
  memberWorkspaceShell: false,
  analytics: "none",
  fingerprinting: false,
  sharedTelemetry: false,
  sharedErrorReportingIdentity: false,
  thirdPartyScripts: "none",
  thirdPartyFonts: "none",
  crossOriginSdkIdentifier: false,
  referrerPolicy: "no-referrer",
  cachePolicy: "no-store",
  frameAncestors: "none",
  persistentMemberIdentifier: false,
  persistentVotingIdentifier: false,
  credentialMaterialPersisted: false,
  ballotStatePersisted: false,
  handoffInQueryString: false,
  handoffInFragment: false,
  handoffInBrowserStorage: false,
  handoffInPageTitle: false,
  handoffInLogCorrelation: false,
  reverseIdentityBridge: false,
  intermediateTally: false,
  s2sCredentialInBrowser: false,
} as const);

/**
 * Every browser persistence mechanism this workspace may reach, and the single
 * permitted answer for each.  `storageAllowed` is total: an unknown kind is
 * refused rather than defaulted.
 */
export const BROWSER_PERSISTENCE_KINDS = Object.freeze([
  "cookie",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "cacheStorage",
  "serviceWorker",
  "webSql",
  "fileSystem",
] as const);

export type BrowserPersistenceKind = (typeof BROWSER_PERSISTENCE_KINDS)[number];

export function storageAllowed(kind: string): false {
  void kind;
  return false;
}

/**
 * Outbound request classes this frontend is permitted to originate.  The list
 * is empty of third-party classes by construction; see
 * `docs/frontend/FRONT-04-NETWORK-UNLINKABILITY-BOUNDARY.md`.
 */
export const PERMITTED_REQUEST_ORIGIN_CLASSES = Object.freeze([
  "ws03-same-origin-document",
  "ws03-same-origin-static-asset",
] as const);

export function requestOriginClassPermitted(value: string): boolean {
  return (PERMITTED_REQUEST_ORIGIN_CLASSES as readonly string[]).includes(
    value,
  );
}

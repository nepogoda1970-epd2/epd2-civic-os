import type { WorkspaceId } from "./types";

export const MOBILE_PROFILE_ID = "EPD2-MOBILE-APPLICATION-PROFILE-0.8.2";
export const MOBILE_CLIENT_CHANNEL = "epd2-mobile-app";

export const MOBILE_RETURN_STATUSES = [
  "completed",
  "cancelled",
  "expired",
  "failed",
] as const;

export type MobileReturnStatus = (typeof MOBILE_RETURN_STATUSES)[number];
export type MobileCapabilityPolicy = Readonly<{
  profileId: typeof MOBILE_PROFILE_ID;
  clientChannel: typeof MOBILE_CLIENT_CHANNEL;
  workspaceScope: readonly WorkspaceId[];
  capability: string;
  allowed: boolean;
  sessionModel: "app-session-only" | "separate-voting-session" | "none";
  storagePolicy: string;
  handoffPolicy: string;
  offlinePolicy: "read-only-non-sensitive" | "prohibited";
  notificationPolicy: "neutral-minimal-routing-only";
  securityGate: string;
  dependentPack: string;
  activationStatus: "inactive-pending-pack-and-security-gates";
}>;

const allowed = (
  capability: string,
  workspaceScope: readonly WorkspaceId[],
  dependentPack: string,
): MobileCapabilityPolicy => ({
  profileId: MOBILE_PROFILE_ID,
  clientChannel: MOBILE_CLIENT_CHANNEL,
  workspaceScope,
  capability,
  allowed: true,
  sessionModel: "app-session-only",
  storagePolicy: "minimal-secure-session-artifacts-only",
  handoffPolicy: "no-authority-transfer",
  offlinePolicy: "read-only-non-sensitive",
  notificationPolicy: "neutral-minimal-routing-only",
  securityGate: "api-and-mobile-security-profile-stable",
  dependentPack,
  activationStatus: "inactive-pending-pack-and-security-gates",
});

const prohibited = (
  capability: string,
  workspaceScope: readonly WorkspaceId[],
): MobileCapabilityPolicy => ({
  profileId: MOBILE_PROFILE_ID,
  clientChannel: MOBILE_CLIENT_CHANNEL,
  workspaceScope,
  capability,
  allowed: false,
  sessionModel: "none",
  storagePolicy: "prohibited",
  handoffPolicy: "prohibited",
  offlinePolicy: "prohibited",
  notificationPolicy: "neutral-minimal-routing-only",
  securityGate: "not-activatable-in-mobile-app",
  dependentPack: "not-applicable",
  activationStatus: "inactive-pending-pack-and-security-gates",
});

export const MOBILE_CAPABILITIES: readonly MobileCapabilityPolicy[] = [
  ...[
    "member-profile",
    "initiatives",
    "deliberation",
    "delegation",
    "programme-participation",
    "neutral-notifications",
    "protected-messages",
    "candidacy",
    "assemblies",
    "user-facing-appeals",
  ].map((capability) => allowed(capability, ["WS-02"], "relevant-domain-PACK")),
  allowed("citizen-office-request-status", ["WS-05"], "PACK-33"),
  prohibited("representative-workspace", ["WS-04"]),
  prohibited("institutional-administration", ["WS-06"]),
  prohibited("employee-compliance-legal", ["WS-07"]),
  prohibited("finance-workspace", ["WS-08"]),
  prohibited("independent-oversight", ["WS-09"]),
  prohibited("publication-administration", ["WS-10"]),
  prohibited("privileged-administration", ["WS-06"]),
  prohibited("certification", ["WS-06", "WS-09"]),
  prohibited("tally-administration", ["WS-03", "WS-06"]),
  prohibited("legal-decisions", ["WS-07"]),
  prohibited("security-administration", ["WS-06"]),
  prohibited("universal-admin", ["WS-06"]),
] as const;

export const MOBILE_VOTING_HANDOFF = {
  votingInsideApp: false,
  embeddedWebView: "prohibited",
  userAgent: "system-browser-required",
  targetWorkspace: "WS-03",
  sessionModel: "separate-voting-session",
  memberSessionTransfer: "prohibited",
  persistentMemberIdentifierTransfer: "prohibited",
  sharedCookies: false,
  sharedLocalStorage: false,
  sharedIndexedDB: false,
  sharedAnalytics: false,
  sharedIdentitySession: false,
  artifact: {
    oneTime: true,
    shortLived: true,
    purposeScoped: true,
    boundToOneVotingEvent: true,
    containsUserSelection: false,
  },
  return: {
    statuses: MOBILE_RETURN_STATUSES,
    signedOrOneTime: true,
    containsBallotReference: false,
    containsVoteContent: false,
  },
  clearVotingContextAfter: ["completion", "cancellation"],
  correlationMetadata: "minimized",
  intermediateTally: "unavailable",
  analytics: "prohibited",
  fingerprinting: "prohibited",
} as const;

export const MOBILE_PUSH_POLICY = {
  providerTrustedStorage: false,
  payload: "minimal-routing-and-status-only",
  fullContentRetrieval: "authenticated-server-retrieval-required",
  prohibitedContent: [
    "political-preference",
    "voting-content",
    "legal-case-text",
    "sensitive-membership-data",
  ],
} as const;

export const MOBILE_SECURITY_PROFILE = {
  productionImplemented: false,
  secureStorage: "minimal-session-artifacts-only",
  plaintextHighAssuranceTokens: "prohibited",
  biometricUnlock: "does-not-replace-server-authentication",
  remoteLogout: "required-before-activation",
  deviceSessionInventory: "required-before-activation",
  deviceRevocation: "required-before-activation",
  deepLinkValidation: "server-required",
  offlineConsequentialActions: "prohibited",
  offlineCache: {
    votingData: "prohibited",
    privilegedData: "prohibited",
    sensitiveLegalData: "prohibited",
  },
  separatelyGoverned: ["clipboard", "screenshots", "os-sharing"],
  analytics: { politicalPreference: "prohibited" },
  crashLogs: {
    pii: "prohibited",
    tokens: "prohibited",
    ballotData: "prohibited",
    legalContent: "prohibited",
  },
} as const;

export const MOBILE_DELIVERY_SEQUENCE = [
  "responsive-ws-02-web",
  "pwa-non-critical-capabilities-only",
  "native-app-after-api-and-security-stabilization",
] as const;

export const MOBILE_SHARED_SOURCE_ALLOWED = [
  "design-tokens",
  "schemas",
  "generated-api-types",
  "accessibility-patterns",
  "non-authoritative-ui-components",
] as const;

export const MOBILE_SHARED_RUNTIME_STATE_PROHIBITED = [
  "cookies",
  "browser-storage",
  "authority-state",
  "privileged-sessions",
  "voting-credentials",
] as const;

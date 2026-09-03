import type {
  CapabilityStatus,
  MemberRuntime,
  MemberSummary,
  MembershipRecord,
  PortFailure,
  Result,
  Scope,
} from "./types";

/**
 * FRONT-03 C1 binds only to routes present in the independently accepted
 * API-02 C13 route register.  The browser never receives or constructs a
 * bearer value: authority remains in the HttpOnly same-origin session cookie.
 */
export const acceptedApi02C13 = Object.freeze({
  candidate:
    "EPD2_API02_AUTHENTICATION_AND_AUTHORIZATION_RUNTIME_CANDIDATE_0.1_C13.zip",
  sha256: "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9",
  acceptanceRun: "33497989489",
  routes: Object.freeze({
    accountMe: "/api/v1/account/me",
    membershipMe: "/api/v1/membership/me",
    securityState: "/api/v1/identity/security-state",
    sessions: "/api/v1/identity/sessions",
    credentials: "/api/v1/identity/credentials",
    stepUpChallenge: "/api/v1/identity/step-up/challenge",
    stepUpCompletion: "/api/v1/identity/step-up/completion",
    passkeyChallenge: "/api/v1/identity/credentials/passkey/challenge",
    passkeyCompletion: "/api/v1/identity/credentials/passkey",
    votingHandoff: "/api/v1/identity/voting-handoff",
  }),
});

type AccountView = {
  account_status: string;
  membership_state: string;
};
type MembershipView = {
  organization_id: string;
  membership_state: string;
  is_governed_membership: boolean;
  latest_application_status: string | null;
};
type SecurityStateView = {
  account_status: string;
  activated: boolean;
  credential_count: number;
  credential_types: string[];
  factor_classes: string[];
  active_session_count: number;
  lock_in_force: boolean;
  restriction_in_force: boolean;
  closure_requested: boolean;
};
type SessionView = {
  workspace: string;
  assurance: string;
  status: string;
  current: boolean;
};
type CredentialView = {
  credential_type: string;
  nickname: string;
  binding: string;
  status: string;
};

const failure = (
  kind: PortFailure["kind"],
  safeMessage = "Die zuständige Laufzeit ist noch nicht verfügbar.",
): Result<never> => ({ ok: false, error: { kind, safeMessage } });

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

async function requestJson<T>(
  path: string,
  signal?: AbortSignal,
): Promise<Result<T>> {
  try {
    const response = await fetch(path, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: { accept: "application/json" },
      signal,
    });
    if (response.status === 401 || response.status === 403)
      return failure("forbidden", "Zugriff nicht möglich.");
    if (!response.ok) return failure("unavailable");
    return { ok: true, value: (await response.json()) as T };
  } catch {
    return failure("unavailable");
  }
}

function validAccount(value: unknown): value is AccountView {
  return (
    isRecord(value) &&
    typeof value.account_status === "string" &&
    typeof value.membership_state === "string"
  );
}

function validMembership(value: unknown): value is MembershipView {
  return (
    isRecord(value) &&
    typeof value.organization_id === "string" &&
    value.organization_id.length > 0 &&
    typeof value.membership_state === "string" &&
    typeof value.is_governed_membership === "boolean" &&
    (value.latest_application_status === null ||
      typeof value.latest_application_status === "string")
  );
}

async function readIdentityContext(
  signal?: AbortSignal,
): Promise<Result<{ account: AccountView; membership: MembershipView }>> {
  const [account, membership] = await Promise.all([
    requestJson<unknown>(acceptedApi02C13.routes.accountMe, signal),
    requestJson<unknown>(acceptedApi02C13.routes.membershipMe, signal),
  ]);
  if (!account.ok) return account;
  if (!membership.ok) return membership;
  if (!validAccount(account.value) || !validMembership(membership.value))
    return failure(
      "unknown",
      "Die Laufzeitantwort konnte nicht sicher eingeordnet werden.",
    );
  return {
    ok: true,
    value: { account: account.value, membership: membership.value },
  };
}

function requireGovernedMember(
  membership: MembershipView,
  targetScope?: string,
): Result<MembershipView> {
  if (!membership.is_governed_membership)
    return failure(
      "forbidden",
      "Mitgliedschaft ist nicht autoritativ aktiviert.",
    );
  if (targetScope !== undefined && targetScope !== membership.organization_id)
    return failure("forbidden", "Zugriff nicht möglich.");
  return { ok: true, value: membership };
}

function currentScope(membership: MembershipView): Scope {
  return {
    ref: membership.organization_id,
    label: "Aktueller autorisierter Organisationskontext",
    authorized: true,
  };
}

function memberSummary(membership: MembershipView): MemberSummary {
  return {
    status: membership.membership_state,
    organization: "Aktueller autorisierter Organisationskontext",
    tasks: [],
    deadlines: [],
    messages: [],
    capabilities: {
      initiatives: "LIMITED",
      deliberation: "LIMITED",
      delegation: "BLOCKED",
    },
    voting: "BLOCKED",
  };
}

function membershipRecord(membership: MembershipView): MembershipRecord {
  return {
    status: membership.membership_state,
    affiliation: "Aktueller autorisierter Organisationskontext",
    version: "API-02 C13 accepted contract",
    provenance: "GET /api/v1/membership/me",
    history: [],
    correctionState: "BLOCKED",
    decisionState: membership.is_governed_membership
      ? "authoritativ aktiviert"
      : "nicht autoritativ aktiviert",
    documentState: "nicht in FRONT-03 dupliziert",
  };
}

function validSecurityState(value: unknown): value is SecurityStateView {
  if (!isRecord(value)) return false;
  return (
    typeof value.account_status === "string" &&
    typeof value.activated === "boolean" &&
    typeof value.credential_count === "number" &&
    Array.isArray(value.credential_types) &&
    value.credential_types.every((x) => typeof x === "string") &&
    Array.isArray(value.factor_classes) &&
    value.factor_classes.every((x) => typeof x === "string") &&
    typeof value.active_session_count === "number" &&
    typeof value.lock_in_force === "boolean" &&
    typeof value.restriction_in_force === "boolean" &&
    typeof value.closure_requested === "boolean"
  );
}

function validSessions(value: unknown): value is { sessions: SessionView[] } {
  if (!isRecord(value) || !Array.isArray(value.sessions)) return false;
  return value.sessions.every(
    (row) =>
      isRecord(row) &&
      typeof row.workspace === "string" &&
      typeof row.assurance === "string" &&
      typeof row.status === "string" &&
      typeof row.current === "boolean",
  );
}

function validCredentials(
  value: unknown,
): value is { credentials: CredentialView[] } {
  if (!isRecord(value) || !Array.isArray(value.credentials)) return false;
  return value.credentials.every(
    (row) =>
      isRecord(row) &&
      typeof row.credential_type === "string" &&
      typeof row.nickname === "string" &&
      typeof row.binding === "string" &&
      typeof row.status === "string",
  );
}

export function createApi02C13Runtime(): MemberRuntime {
  const unavailable = async <T>(): Promise<Result<T>> => failure("unavailable");
  return Object.freeze({
    profile: "production" as const,
    principal: {
      async resolve() {
        const context = await readIdentityContext();
        if (!context.ok) return context;
        const { account, membership } = context.value;
        if (
          ["closed", "suspended"].includes(account.account_status.toLowerCase())
        )
          return failure(
            "forbidden",
            "Das Konto ist für diesen Bereich nicht freigegeben.",
          );
        const actor = membership.is_governed_membership
          ? "member"
          : "applicant";
        return {
          ok: true as const,
          value: {
            actor,
            displayName:
              actor === "member" ? "Mitgliedskonto" : "Antragstellerkonto",
            scopeRef:
              actor === "member" ? membership.organization_id : undefined,
            assurance: "standard" as const,
          },
        };
      },
    },
    applicantCase: { readOwnCase: unavailable },
    memberCore: {
      async read(scopeRef: string, signal?: AbortSignal) {
        const context = await readIdentityContext(signal);
        if (!context.ok) return context;
        const member = requireGovernedMember(
          context.value.membership,
          scopeRef,
        );
        return member.ok
          ? { ok: true as const, value: memberSummary(member.value) }
          : member;
      },
    },
    membership: {
      async read(scopeRef: string, signal?: AbortSignal) {
        const context = await readIdentityContext(signal);
        if (!context.ok) return context;
        const member = requireGovernedMember(
          context.value.membership,
          scopeRef,
        );
        return member.ok
          ? { ok: true as const, value: membershipRecord(member.value) }
          : member;
      },
    },
    // These bounded-context operations are deliberately not inferred from API-02.
    initiatives: { list: unavailable, commit: unavailable },
    deliberation: { list: unavailable },
    delegation: { status: unavailable },
    organizationScope: {
      async listAuthorized() {
        const context = await readIdentityContext();
        if (!context.ok) return context;
        const member = requireGovernedMember(context.value.membership);
        return member.ok
          ? { ok: true as const, value: [currentScope(member.value)] }
          : member;
      },
      async reauthorize(targetRef: string, signal?: AbortSignal) {
        // API-02 C13 exposes the current authorized organization context but no
        // route that changes it.  Reauthorization therefore re-reads authority
        // and succeeds only for that exact current context; it never switches.
        const context = await readIdentityContext(signal);
        if (!context.ok) return context;
        const member = requireGovernedMember(
          context.value.membership,
          targetRef,
        );
        return member.ok
          ? {
              ok: true as const,
              value: {
                scopeRef: member.value.organization_id,
                contextVersion: `api02-c13:${member.value.organization_id}`,
              },
            }
          : member;
      },
    },
    sessionAssurance: {
      async read() {
        const [security, sessions, credentials] = await Promise.all([
          requestJson<unknown>(acceptedApi02C13.routes.securityState),
          requestJson<unknown>(acceptedApi02C13.routes.sessions),
          requestJson<unknown>(acceptedApi02C13.routes.credentials),
        ]);
        if (!security.ok) return security;
        if (!sessions.ok) return sessions;
        if (!credentials.ok) return credentials;
        if (
          !validSecurityState(security.value) ||
          !validSessions(sessions.value) ||
          !validCredentials(credentials.value)
        )
          return failure(
            "unknown",
            "Die Laufzeitantwort konnte nicht sicher eingeordnet werden.",
          );
        const current = sessions.value.sessions.find((row) => row.current);
        const sessionLabels = sessions.value.sessions.map(
          (row) =>
            `${row.current ? "Aktuelle" : "Weitere"} Sitzung · ${row.assurance} · ${row.status}`,
        );
        const credentialLabels = credentials.value.credentials.map(
          (row) => `${row.credential_type} · ${row.nickname} · ${row.status}`,
        );
        const recovery: CapabilityStatus = "BLOCKED";
        return {
          ok: true as const,
          value: {
            assurance: current?.assurance ?? "nicht bestimmt",
            sessions: sessionLabels,
            passkeys: credentialLabels,
            recovery,
          },
        };
      },
    },
    // The accepted C13 handoff requires a voting-context id, object version,
    // idempotency key and bound high-assurance step-up.  FRONT-03's parameterless
    // port cannot safely manufacture any of them, so this stays fail-closed.
    votingHandoff: { create: unavailable },
    supportHelp: {
      async read() {
        return {
          ok: true as const,
          value: {
            status: "LIMITED" as CapabilityStatus,
            offline: "Mitgliederstelle schriftlich kontaktieren.",
          },
        };
      },
    },
  });
}

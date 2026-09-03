import { createApi02C13Runtime } from "./api02Runtime";
import type {
  ActorMode,
  ApplicantCase,
  CapabilityStatus,
  DeliberationItem,
  DelegationStatus,
  Initiative,
  InitiativeDraft,
  InitiativeReceipt,
  MemberRuntime,
  MemberSummary,
  MembershipRecord,
  Result,
  Scope,
} from "./types";

const unavailable = <T>(): Result<T> => ({
  ok: false,
  error: {
    kind: "unavailable",
    safeMessage: "Die zuständige Laufzeit ist noch nicht verfügbar.",
  },
});
const fixtureScopes: Scope[] = [
  { ref: "bund", label: "Bund", level: "Bund", authorized: true },
  {
    ref: "berlin",
    label: "Landesverband Berlin",
    level: "Land",
    authorized: true,
  },
  {
    ref: "berlin-mitte",
    label: "Regional-/Ortsverband Berlin-Mitte",
    level: "Ort",
    authorized: true,
  },
];
const scopedLabel = (scopeRef: string) =>
  fixtureScopes.find((scope) => scope.ref === scopeRef)?.label ?? scopeRef;

export function createFixtureRuntime(
  actor: Exclude<ActorMode, "anonymous">,
): MemberRuntime {
  return Object.freeze({
    profile: "fixture" as const,
    principal: {
      async resolve() {
        return {
          ok: true as const,
          value: {
            actor,
            displayName: actor === "member" ? "Anna Beispiel" : "Alex Beispiel",
            scopeRef: actor === "member" ? "bund" : undefined,
            assurance: "standard" as const,
          },
        };
      },
    },
    applicantCase: {
      async readOwnCase(): Promise<Result<ApplicantCase>> {
        if (actor !== "applicant") return unavailable();
        return {
          ok: true,
          value: {
            reference: "ANTRAG-2026-0142",
            submittedAt: "24.08.2026, 10:14",
            status: "In Prüfung",
            unit: "Mitgliederaufnahme Bund",
            stage: "Unterlagenprüfung",
            deadline: "12.09.2026",
            documents: [
              "Aufnahmeantrag — eingegangen",
              "Identitätsnachweis — geprüft",
            ],
            timeline: [
              { at: "24.08.2026", label: "Antrag eingereicht" },
              { at: "27.08.2026", label: "Prüfung begonnen" },
            ],
            notice:
              "Für Ihren Antrag ist derzeit keine Ergänzung erforderlich.",
          },
        };
      },
    },
    memberCore: {
      async read(
        scopeRef: string,
        signal?: AbortSignal,
      ): Promise<Result<MemberSummary>> {
        if (actor !== "member" || signal?.aborted) return unavailable();
        return {
          ok: true,
          value: {
            status: "Aktiv",
            organization: scopedLabel(scopeRef),
            tasks: [
              `Profilangaben prüfen · ${scopedLabel(scopeRef)}`,
              `Initiative weiterbearbeiten · ${scopedLabel(scopeRef)}`,
            ],
            deadlines: [`12.09.2026 · Rückmeldung · ${scopedLabel(scopeRef)}`],
            messages: [
              `Neue Mitteilung zur Programmwerkstatt · ${scopedLabel(scopeRef)}`,
            ],
            capabilities: {
              initiatives: "AVAILABLE",
              deliberation: "AVAILABLE",
              delegation: "BLOCKED",
            },
            voting: "BLOCKED",
          },
        };
      },
    },
    membership: {
      async read(
        scopeRef: string,
        signal?: AbortSignal,
      ): Promise<Result<MembershipRecord>> {
        if (actor !== "member" || signal?.aborted) return unavailable();
        return {
          ok: true,
          value: {
            status: "Aktiv",
            affiliation: scopedLabel(scopeRef),
            version: `v3-${scopeRef}`,
            provenance: "Authoritative Membership Projection",
            history: [
              "Aufnahme bestätigt",
              `Zuordnung autorisiert · ${scopedLabel(scopeRef)}`,
            ],
            correctionState: "LIMITED",
            decisionState: "Aufnahmeentscheidung bestätigt",
            documentState: "Mitgliedschaftsnachweis verfügbar",
          },
        };
      },
    },
    initiatives: {
      async list(
        scopeRef: string,
        signal?: AbortSignal,
      ): Promise<Result<Initiative[]>> {
        if (actor !== "member" || signal?.aborted) return unavailable();
        return {
          ok: true,
          value: [
            {
              ref: `INI-${scopeRef}-44`,
              title: `Offene kommunale Daten · ${scopedLabel(scopeRef)}`,
              state: "Beratung",
              scopeRef,
            },
          ],
        };
      },
      async commit(
        scopeRef: string,
        draft: InitiativeDraft,
      ): Promise<Result<InitiativeReceipt>> {
        if (actor !== "member" || !scopeRef || !draft.title || !draft.summary)
          return unavailable();
        return {
          ok: true,
          value: {
            receiptRef: `RCPT-${scopeRef}-2026-0081`,
            committedAt: new Date(0).toISOString(),
            state: "committed",
          },
        };
      },
    },
    deliberation: {
      async list(
        scopeRef: string,
        signal?: AbortSignal,
      ): Promise<Result<DeliberationItem[]>> {
        if (actor !== "member" || signal?.aborted) return unavailable();
        return {
          ok: true,
          value: [
            {
              title: `Offene kommunale Daten · ${scopedLabel(scopeRef)}`,
              provenance: "Deliberation Projection",
              version: `v4-${scopeRef}`,
            },
          ],
        };
      },
    },
    delegation: {
      async status(
        scopeRef: string,
        signal?: AbortSignal,
      ): Promise<Result<DelegationStatus>> {
        if (actor !== "member" || signal?.aborted) return unavailable();
        return {
          ok: true,
          value: {
            activation: "BLOCKED",
            reason: `Kein akzeptierter Laufzeitvertrag für Delegationen · ${scopedLabel(scopeRef)}.`,
          },
        };
      },
    },
    organizationScope: {
      async listAuthorized(): Promise<Result<Scope[]>> {
        if (actor !== "member") return unavailable();
        return { ok: true, value: fixtureScopes };
      },
      async reauthorize(targetRef: string, signal?: AbortSignal) {
        if (actor !== "member" || signal?.aborted) return unavailable<never>();
        return fixtureScopes.some((scope) => scope.ref === targetRef)
          ? {
              ok: true as const,
              value: {
                scopeRef: targetRef,
                contextVersion: `fixture-${targetRef}`,
              },
            }
          : {
              ok: false as const,
              error: {
                kind: "forbidden" as const,
                safeMessage: "Zugriff nicht möglich.",
              },
            };
      },
    },
    sessionAssurance: {
      async read() {
        return actor === "member"
          ? {
              ok: true as const,
              value: {
                assurance: "standard",
                sessions: ["Aktuelle Sitzung"],
                passkeys: [],
                recovery: "BLOCKED" as CapabilityStatus,
              },
            }
          : unavailable<never>();
      },
    },
    votingHandoff: {
      async create() {
        return unavailable<never>();
      },
    },
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

export function createProductionRuntime(): MemberRuntime {
  return createApi02C13Runtime();
}

export function composeMemberRuntime(
  profile: "fixture" | "production",
  actor: Exclude<ActorMode, "anonymous">,
): MemberRuntime {
  return profile === "fixture"
    ? createFixtureRuntime(actor)
    : createProductionRuntime();
}
export const storagePolicy = Object.freeze({
  bearerInLocalStorage: false,
  bearerInSessionStorage: false,
  bearerInIndexedDB: false,
  protectedOfflineCache: false,
  crossWorkspaceBridge: false,
});
export const telemetryAllowed = Object.freeze([
  "route_id",
  "capability_status",
  "safe_reason_code",
  "viewport_class",
]);

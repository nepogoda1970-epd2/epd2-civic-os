import type {
  InitiativeDraft,
  PrincipalPort,
  Result,
  SessionAssurancePort,
} from "./types";

const unavailable = <T>(): Result<T> => ({
  ok: false,
  error: {
    kind: "unavailable",
    safeMessage: "Die zuständige Laufzeit ist noch nicht verfügbar.",
  },
});
export class Api02UnavailableAdapter
  implements PrincipalPort, SessionAssurancePort
{
  async resolve() {
    return unavailable<never>();
  }
  async read() {
    return unavailable<never>();
  }
}

// This adapter is imported only by development/test composition. Production composition never falls back to it.
export class Front03FixtureAdapter {
  constructor(private actor: "applicant" | "member" = "member") {}
  async resolve() {
    return {
      ok: true as const,
      value: {
        actor: this.actor,
        displayName:
          this.actor === "member" ? "Anna Beispiel" : "Alex Beispiel",
        scopeRef: this.actor === "member" ? "bund" : undefined,
        assurance: "standard" as const,
      },
    };
  }
  async readOwnCase() {
    return {
      ok: true as const,
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
        notice: "Für Ihren Antrag ist derzeit keine Ergänzung erforderlich.",
      },
    };
  }
  async read(scopeRef: string) {
    return {
      ok: true as const,
      value: {
        status: "Aktiv",
        tasks: ["Profilangaben prüfen", "Initiative weiterbearbeiten"],
        deadlines: ["12.09.2026 · Rückmeldung"],
        messages: ["Neue Mitteilung zur Programmwerkstatt"],
        voting: "BLOCKED" as const,
        scopeRef,
      },
    };
  }
  async list(scopeRef: string) {
    return {
      ok: true as const,
      value: [
        {
          ref: "INI-44",
          title: "Offene kommunale Daten",
          state: "Beratung",
          scopeRef,
        },
      ],
    };
  }
  async commit(scopeRef: string, draft: InitiativeDraft) {
    void scopeRef;
    void draft;
    return {
      ok: true as const,
      value: {
        receiptRef: "RCPT-2026-0081",
        committedAt: new Date(0).toISOString(),
        state: "committed" as const,
      },
    };
  }
  async status(scopeRef: string) {
    void scopeRef;
    return {
      ok: true as const,
      value: {
        activation: "BLOCKED" as const,
        reason: "Kein akzeptierter Laufzeitvertrag für Delegationen.",
      },
    };
  }
  async listAuthorized() {
    return {
      ok: true as const,
      value: [
        {
          ref: "bund",
          label: "Bund",
          level: "Bund" as const,
          authorized: true,
        },
        {
          ref: "berlin",
          label: "Landesverband Berlin",
          level: "Land" as const,
          authorized: true,
        },
        {
          ref: "berlin-mitte",
          label: "Regional-/Ortsverband Berlin-Mitte",
          level: "Ort" as const,
          authorized: true,
        },
      ],
    };
  }
  async reauthorize(targetRef: string) {
    return ["bund", "berlin", "berlin-mitte"].includes(targetRef)
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
  }
  async create() {
    return {
      ok: false as const,
      error: {
        kind: "unavailable" as const,
        safeMessage:
          "Voting-Handoff ist bis zum akzeptierten Vertrag blockiert.",
      },
    };
  }
}

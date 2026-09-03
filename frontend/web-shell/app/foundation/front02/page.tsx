import {
  Button,
  Notice,
  PageHeader,
  StatePanel,
  WorkspaceShell,
} from "../../../components/foundation";
import { WORKSPACES } from "../../../foundation/workspaces";

const states = [
  [
    "not_found",
    "404 · Nicht gefunden",
    "Die angeforderte öffentliche Projektion existiert nicht.",
  ],
  [
    "forbidden",
    "403 · Kein Zugriff",
    "Diese Ansicht bleibt in ihrem zuständigen Workspace.",
  ],
  [
    "auth_required",
    "Anmeldung erforderlich",
    "Kein Login wird hier erzeugt; der Handoff wäre ausdrücklich und zweckgebunden.",
  ],
  [
    "session_expired",
    "Sitzung abgelaufen",
    "Eine neue, getrennte Sitzung wäre erforderlich.",
  ],
  ["loading", "Lädt", "Der Zustand enthält keinen Erfolgshinweis."],
  ["empty", "Keine Einträge", "Es werden keine Inhalte erfunden."],
  [
    "validation",
    "Eingabe prüfen",
    "Die beispielhafte Eingabe erfüllt eine Regel nicht.",
  ],
  [
    "stale_conflict",
    "Veraltete Fassung / Konflikt",
    "Version und Korrektur müssen geprüft werden.",
  ],
  [
    "duplicate",
    "Doppelter Vorgang",
    "Der Vorgang wurde nicht erneut ausgelöst.",
  ],
  [
    "dependency_unavailable",
    "Abhängigkeit nicht verfügbar",
    "Ein geregelter Offline-Kanal wird genannt.",
  ],
  [
    "partial_outage",
    "Teilausfall",
    "Nur freigegebene Teilinformationen bleiben sichtbar.",
  ],
  ["maintenance", "Wartung", "Keine verdeckte Ausführung während der Wartung."],
  ["upload_failed", "Upload fehlgeschlagen", "Keine Datei wurde übernommen."],
  [
    "submission_interrupted",
    "Übermittlung unterbrochen",
    "Es gibt keine Quittung und keine stillschweigende Speicherung.",
  ],
  [
    "read_only",
    "Nur lesbar",
    "Bearbeitung ist in diesem Fixture absichtlich deaktiviert.",
  ],
  [
    "retry",
    "Erneut versuchen",
    "Wiederholung bleibt eine explizite Nutzeraktion.",
  ],
  [
    "offline_channel",
    "Offline-Kanal",
    "Kontaktweg: zuständige Stelle, mit Vorgangsreferenz.",
  ],
  [
    "completed",
    "Abgeschlossen",
    "Illustrativer Abschluss, nicht als rechtliche Wirkung.",
  ],
  [
    "receipt_evidence",
    "Quittung / Nachweis",
    "Beispielhafte Referenz: FRONT02-FIXTURE-001.",
  ],
] as const;

export default function Front02FoundationPage() {
  return (
    <WorkspaceShell workspaceId="WS-01">
      <PageHeader
        title="FRONT-02 state and shell catalogue"
        description="Read-only C2 fixtures; no session, protected record or consequential mutation is created."
      />
      <section className="section-block" aria-labelledby="front02-states">
        <h2 id="front02-states">Systemzustände und Folgen</h2>
        <div className="grid">
          {states.map(([state, title, text]) => (
            <StatePanel
              key={state}
              state={
                state === "forbidden"
                  ? "forbidden"
                  : state === "loading"
                    ? "loading"
                    : state === "empty"
                      ? "empty"
                      : state === "read_only"
                        ? "not_available"
                        : "error"
              }
              title={title}
            >
              <p data-front02-state={state}>{text}</p>
              {["retry", "offline_channel"].includes(state) ? (
                <Button disabled>
                  {state === "retry" ? "Erneut versuchen" : "Kontaktweg öffnen"}
                </Button>
              ) : null}
            </StatePanel>
          ))}
        </div>
      </section>
      <section className="section-block" aria-labelledby="front02-shells">
        <h2 id="front02-shells">Getrennte Workspace-Schalen</h2>
        <div className="grid">
          {WORKSPACES.map((workspace) => (
            <article
              className="card"
              data-front02-workspace={workspace.id}
              key={workspace.id}
            >
              <h3>
                {workspace.id} · {workspace.name}
              </h3>
              <p>
                Shell: {workspace.shell}; Navigation:{" "}
                {workspace.navigationSource}; Session sharing:{" "}
                {workspace.sessionSharing}.
              </p>
              <Notice kind="information" title="Fixture-Grenze">
                {workspace.sensitivity}. Aktivierung: {workspace.activation}.
                Keine gemeinsame Anmeldung oder universelle Arbeitsfläche.
              </Notice>
            </article>
          ))}
        </div>
      </section>
    </WorkspaceShell>
  );
}

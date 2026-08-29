import Link from "next/link";

import {
  Card,
  MetadataList,
  Notice,
  PageHeader,
  RestrictedContentNotice,
  StaleDataWarning,
  WorkspaceShell,
} from "./foundation";
import { workspaceById } from "../foundation/workspaces";
import type { WorkspaceId } from "../foundation/types";

export function WorkspaceAcceptancePage({
  workspaceId,
}: {
  workspaceId: WorkspaceId;
}) {
  const workspace = workspaceById(workspaceId);
  return (
    <WorkspaceShell workspaceId={workspaceId}>
      <PageHeader
        title={`${workspace.id} · ${workspace.name}`}
        description="FRONT-02 Shell-Nachweis. Keine Fachfunktion ist dadurch aktiviert oder autorisiert."
      />
      <Notice kind="authority" title="Autorität bleibt am Ziel-Origin">
        Diese Shell teilt weder Sitzung noch Browser-Speicher noch Berechtigungen
        mit einem anderen Workspace. Eine spätere Fachfunktion muss am Ziel-Origin
        neu autorisieren.
      </Notice>
      <Card title="Scope und Laufzeitgrenze">
        <MetadataList
          items={[
            { term: "Origin", description: workspace.originPlaceholder },
            { term: "Route", description: workspace.routePrefix },
            { term: "Aktivierung", description: workspace.activation },
            { term: "Browser-Speicher", description: workspace.browserStorage },
            { term: "Analytics", description: workspace.analytics },
            { term: "Sitzung", description: "Keine gemeinsame Sitzung" },
          ]}
        />
      </Card>
      {workspaceId === "WS-02" ? (
        <StaleDataWarning>
          Ein Wechsel des Organisations-Scope muss inkompatiblen Kontext verwerfen
          und am Ziel neu autorisieren.
        </StaleDataWarning>
      ) : null}
      {workspaceId === "WS-03" ? (
        <RestrictedContentNotice>
          Kein Stimmzettel, keine Identitätssitzung, kein shared storage und keine
          Analytics. Nur zweckgebundener Handoff ist zulässig.
        </RestrictedContentNotice>
      ) : null}
      {workspaceId === "WS-06" ? (
        <RestrictedContentNotice>
          Kein Universal-Admin. Privilegierte Aktionen benötigen rollen- und
          scope-spezifische Autorisierung sowie vorgesehene
          dual-control/break-glass Regeln.
        </RestrictedContentNotice>
      ) : null}
      {workspaceId === "WS-10" ? (
        <Notice kind="info" title="Publikationsprojektion">
          WS-10 zeigt ausschließlich freigegebene öffentliche Renditionen mit
          Herkunft, Version, Korrektur- und Ersetzungszustand.
        </Notice>
      ) : null}
      <p>
        <Link href="/foundation/workspaces">Zur Workspace-Übersicht</Link>
      </p>
    </WorkspaceShell>
  );
}

export type Front02SystemState =
  | "denied"
  | "error"
  | "recovery"
  | "translation-fallback";

export function SystemStateAcceptancePage({
  state,
}: {
  state: Front02SystemState;
}) {
  const copy = {
    denied: {
      title: "Zugriff nicht verfügbar",
      description:
        "Die Oberfläche bestätigt keine Existenz eines geschützten Datensatzes.",
      body: "Für diesen Bereich ist eine erneute, scope-spezifische Autorisierung am zuständigen Origin erforderlich.",
    },
    error: {
      title: "Abhängigkeit vorübergehend nicht verfügbar",
      description: "Es wurde keine autoritative Änderung bestätigt.",
      body: "Der Zustand bleibt unverändert. Ein sicherer erneuter Versuch ist möglich, sobald die Abhängigkeit wieder verfügbar ist.",
    },
    recovery: {
      title: "Sichere Wiederaufnahme",
      description:
        "Unterbrochene Aktionen werden nicht als abgeschlossen dargestellt.",
      body: "Prüfen Sie den letzten bestätigten Stand und wiederholen Sie nur die zulässige Aktion. Ein Receipt erscheint erst nach bestätigtem Backend-Commit.",
    },
    "translation-fallback": {
      title: "English translation unavailable",
      description:
        "The current approved English rendition is unavailable or out of date.",
      body: "Die aktuelle deutsche Fassung bleibt maßgeblich. German authoritative source remains available; no stale English text is presented as current authority.",
    },
  } as const;
  const item = copy[state];
  return (
    <WorkspaceShell workspaceId="WS-01">
      <PageHeader title={item.title} description={item.description} />
      <Notice
        kind={state === "error" ? "warning" : "info"}
        title="FRONT-02 Systemzustand"
      >
        {item.body}
      </Notice>
      <p>
        <Link href="/hilfe">Hilfe öffnen</Link>
      </p>
    </WorkspaceShell>
  );
}

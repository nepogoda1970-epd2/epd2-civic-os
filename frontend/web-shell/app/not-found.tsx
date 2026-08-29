import Link from "next/link";

import { Notice, PageHeader, WorkspaceShell } from "../components/foundation";

export default function NotFound() {
  return (
    <WorkspaceShell workspaceId="WS-01">
      <PageHeader
        title="Seite nicht gefunden"
        description="Die angeforderte öffentliche Seite ist nicht verfügbar."
      />
      <Notice kind="info" title="Keine Datensatzaussage">
        Dieser 404-Zustand bestätigt nicht, ob ein geschützter Datensatz existiert.
      </Notice>
      <p>
        <Link href="/">Zur Startseite</Link> · <Link href="/hilfe">Hilfe</Link>
      </p>
    </WorkspaceShell>
  );
}

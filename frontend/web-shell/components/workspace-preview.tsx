import {
  Card,
  MetadataList,
  Notice,
  PageHeader,
  WorkspaceShell,
} from "./foundation";
import { WORKSPACES } from "../foundation/workspaces";

export function WorkspacePreviews() {
  return (
    <>
      <PageHeader
        description="Wiederverwendbare Shell-Varianten; keine dieser Ansichten ist ein authentifizierter Workspace oder implementiert Fachautorität."
        title="Zehn getrennte Workspace-Shells"
      />
      <Notice kind="authority" title="Getrennte Origins und Sitzungen">
        Gemeinsame Komponenten bedeuten keine gemeinsame Laufzeit. Jede Shell
        ist an ihren eigenen Origin, ihre eigene Re-Autorisierung und ihre
        eigene Speicherregel gebunden.
      </Notice>
      <div className="grid">
        {WORKSPACES.map((workspace) => (
          <Card key={workspace.id} title={`${workspace.id} · ${workspace.name}`}>
            <MetadataList
              items={[
                { term: "Origin", description: workspace.originPlaceholder },
                { term: "Status", description: workspace.activation },
                { term: "Speicher", description: workspace.browserStorage },
                { term: "Sitzung", description: "Keine gemeinsame Sitzung" },
              ]}
            />
            <p>{workspace.capabilities.join(" · ")}</p>
          </Card>
        ))}
      </div>
    </>
  );
}

export function WorkspacePreviewPage() {
  return (
    <WorkspaceShell workspaceId="WS-01">
      <WorkspacePreviews />
    </WorkspaceShell>
  );
}

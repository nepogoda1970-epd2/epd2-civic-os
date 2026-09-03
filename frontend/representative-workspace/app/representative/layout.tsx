import { IsolatedRepresentativeShell } from "../../components/shell";
import { WorkspaceProvider } from "../../components/WorkspaceProvider";

/**
 * The `/representative` layout holds the workspace provider, so a client-side
 * step between sections keeps the resolved session and scope in memory while a
 * reload or a direct visit resolves them again from the runtime. Nothing is
 * written to any persistent store to achieve that.
 */
export default function RepresentativeLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <WorkspaceProvider>
      <IsolatedRepresentativeShell breadcrumbLabel="Mandatsarbeit">
        {children}
      </IsolatedRepresentativeShell>
    </WorkspaceProvider>
  );
}

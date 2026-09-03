import type { ReactNode } from "react";

import { WS03_CONTENT } from "../content/de";
import { WS03_WORKSPACE_ID } from "../policies/isolation";

/**
 * The isolated WS-03 shell.
 *
 * There is no navigation into the Member Workspace, no account menu, no
 * organisation switcher, no identity indicator and no measurement.  The only
 * navigation this shell offers is the skip link, because every other movement
 * through the journey is a consequential decision that belongs on the page.
 */
export function IsolatedVotingShell({
  children,
  breadcrumbLabel,
}: {
  children: ReactNode;
  breadcrumbLabel: string;
}) {
  return (
    <div className="voting-shell" data-workspace={WS03_WORKSPACE_ID}>
      <a className="skip-link" href="#main">
        Zum Inhalt springen
      </a>
      <p className="candidate-banner">
        <strong>Prototyp</strong>
        <span>{WS03_CONTENT.candidateNotice}</span>
      </p>
      <header className="voting-header">
        <span className="voting-wordmark">EPD²</span>
        <p>{WS03_CONTENT.boundaryNotice}</p>
      </header>
      <main className="voting-main" id="main" tabIndex={-1}>
        <p className="informational" data-breadcrumb>
          {WS03_CONTENT.workspace} — {breadcrumbLabel}
        </p>
        {children}
      </main>
      <footer className="voting-footer">
        <span>{WS03_CONTENT.noTally}</span>
        <span>{WS03_CONTENT.fallback.body}</span>
      </footer>
    </div>
  );
}

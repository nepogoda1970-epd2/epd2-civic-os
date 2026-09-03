"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { WS04_CONTENT } from "../content/de";
import { WS04_ROUTE_PREFIX, WS04_WORKSPACE_ID } from "../policies/workspace";

/**
 * The isolated WS-04 shell.
 *
 * Navigation exists here, unlike in WS-03, and the distinction matters: every
 * destination is a section of the *same* mandate. There is no link into the
 * Member Workspace, no organisation switcher, no mandate switcher, and no
 * administrative menu — the absence of a mandate switcher is what makes
 * "exactly one scope" visible rather than merely asserted in code.
 *
 * The identity indicator shows a display name and nothing else. No account
 * reference, no member number and no person identifier reaches this shell,
 * because `MandateSession` does not carry one.
 */

const SECTIONS = [
  { href: `${WS04_ROUTE_PREFIX}`, label: WS04_CONTENT.nav.home },
  { href: `${WS04_ROUTE_PREFIX}/desk`, label: WS04_CONTENT.nav.desk },
  { href: `${WS04_ROUTE_PREFIX}/positions`, label: WS04_CONTENT.nav.positions },
  {
    href: `${WS04_ROUTE_PREFIX}/deviations`,
    label: WS04_CONTENT.nav.deviations,
  },
  {
    href: `${WS04_ROUTE_PREFIX}/declarations`,
    label: WS04_CONTENT.nav.declarations,
  },
  {
    href: `${WS04_ROUTE_PREFIX}/publication`,
    label: WS04_CONTENT.nav.publication,
  },
  { href: `${WS04_ROUTE_PREFIX}/conflicts`, label: WS04_CONTENT.nav.conflicts },
] as const;

export function WorkspaceNav() {
  const pathname = usePathname();
  return (
    <nav className="workspace-nav" aria-label={WS04_CONTENT.nav.label}>
      <h2>{WS04_CONTENT.nav.label}</h2>
      <ul>
        {SECTIONS.map((section) => {
          const current =
            section.href === WS04_ROUTE_PREFIX
              ? pathname === WS04_ROUTE_PREFIX
              : pathname.startsWith(section.href);
          return (
            <li key={section.href}>
              <Link
                href={section.href}
                aria-current={current ? "page" : undefined}
              >
                {section.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function IsolatedRepresentativeShell({
  children,
  breadcrumbLabel,
  displayName,
}: {
  children: ReactNode;
  breadcrumbLabel: string;
  displayName?: string | null;
}) {
  return (
    <div className="workspace-shell" data-workspace={WS04_WORKSPACE_ID}>
      <a className="skip-link" href="#main">
        Zum Inhalt springen
      </a>
      <p className="candidate-banner">
        <strong>Prototyp</strong>
        <span>{WS04_CONTENT.candidateNotice}</span>
      </p>
      <header className="workspace-header">
        <span className="workspace-wordmark">EPD²</span>
        <p>{WS04_CONTENT.boundaryNotice}</p>
        <p data-identity>{displayName ?? WS04_CONTENT.auth.signedOut}</p>
      </header>
      <main className="workspace-main" id="main" tabIndex={-1}>
        <p className="informational" data-breadcrumb>
          {WS04_CONTENT.workspace} — {breadcrumbLabel}
        </p>
        <div className="workspace-layout">
          <WorkspaceNav />
          <div>{children}</div>
        </div>
      </main>
      <footer className="workspace-footer">
        <span>{WS04_CONTENT.votingBoundary.body}</span>
        <span>{WS04_CONTENT.states.notAudited}</span>
      </footer>
    </div>
  );
}

import type { Metadata } from "next";

import "./workspace.css";

/**
 * The isolated WS-04 root layout.
 *
 * Differences from the Member Workspace root layout, each recorded in
 * docs/frontend/FRONT-05-PACK15-MIGRATION-MATRIX.csv:
 *
 *  - no inline locale script. The web-shell layout reads `location.search` to
 *    set `lang`. Here German is authoritative and `lang` is static, so no
 *    script reads the URL on an origin that renders confidential material.
 *  - no shared shell, no account menu, no organisation switcher and no
 *    identity provider imported from the Member Workspace.
 *  - a title that never varies with the operator's state, so no case
 *    reference, subject line or mandate identifier can reach the page title,
 *    the browser history or the referrer.
 */

export const metadata: Metadata = {
  title: "Mandatsbereich — EPD²",
  description:
    "Getrennter Arbeitsbereich für Mandatsarbeit. Kein systemweiter Verwaltungszugriff, keine Auswertung von Fallinhalten.",
  referrer: "no-referrer",
  robots: { index: false, follow: false },
};

export default function RepresentativeRootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}

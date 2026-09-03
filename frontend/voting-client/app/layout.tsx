import type { Metadata } from "next";

import "./voting.css";

/**
 * The isolated WS-03 root layout.
 *
 * Three deliberate differences from the Member Workspace root layout, each
 * recorded in docs/frontend/FRONT-04-PACK15-MIGRATION-MATRIX.csv:
 *
 *  - no inline locale script.  The web-shell layout reads `location.search` to
 *    set `lang`.  On the voting origin that is script execution reading the URL,
 *    and a language value in the query string is a browser-visible parameter on
 *    a surface whose entire point is that nothing in its URL carries meaning.
 *    German is authoritative here and `lang` is static.
 *  - no shared shell, navigation, account menu or identity provider.
 *  - a title that never varies with the voter's state, so no handoff value,
 *    context, code or selection can reach the page title or the referrer.
 */

export const metadata: Metadata = {
  title: "Abstimmungsbereich — EPD²",
  description:
    "Getrennter Abstimmungsbereich ohne Angaben zur Person und ohne Erhebung von Nutzungsdaten.",
  referrer: "no-referrer",
  robots: { index: false, follow: false },
};

export default function VotingRootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}

import Link from "next/link";

import { WS04_CONTENT } from "../content/de";
import { WS04_ORIGIN, WS04_ROUTE_PREFIX } from "../policies/workspace";

/**
 * Rendered per request.
 *
 * This is not a performance choice, it is what makes the Content-Security-Policy
 * in `middleware.ts` work at all. The policy carries a per-request nonce, and a
 * statically prerendered page carries script tags stamped at build time — so the
 * nonce in the header can never match the markup, every script is blocked, and
 * the page renders as inert server output with no hydration. The failure is
 * silent: the markup looks complete and only the interaction is dead, which is
 * how it survived a first pass here.
 *
 * Per-request rendering is also the semantically correct answer: every surface
 * is mandate-scoped and served `no-store`, so there is nothing a shared
 * prerender could legitimately be reused for.
 */
export const dynamic = "force-dynamic";

/**
 * The origin root.
 *
 * It is an entry notice rather than a redirect: a silent redirect would hide
 * from the operator that they have crossed onto a separate origin with a
 * separate session, and that crossing is the isolation boundary.
 */
export default function OriginRoot() {
  return (
    <div className="workspace-shell">
      <a className="skip-link" href="#main">
        Zum Inhalt springen
      </a>
      <p className="candidate-banner">
        <strong>Prototyp</strong>
        <span>{WS04_CONTENT.candidateNotice}</span>
      </p>
      <main className="workspace-main" id="main" tabIndex={-1}>
        <div className="page-header">
          <h1>{WS04_CONTENT.workspace}</h1>
          <p>{WS04_CONTENT.boundaryNotice}</p>
        </div>
        <p className="informational">{WS04_ORIGIN}</p>
        <p>
          <Link className="button button--primary" href={WS04_ROUTE_PREFIX}>
            {WS04_CONTENT.nav.home}
          </Link>
        </p>
      </main>
    </div>
  );
}

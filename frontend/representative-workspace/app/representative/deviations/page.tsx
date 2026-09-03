import { DeviationSurface } from "../../../components/DeviationSurface";

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

export default function DeviationsPage() {
  return <DeviationSurface />;
}

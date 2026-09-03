"use client";

import { WS04_CONTENT } from "../content/de";
import { formatGovernedInstant } from "../policies/dateTime";
import { useWorkspace } from "./WorkspaceProvider";

/**
 * The scope banner.
 *
 * It is rendered on every protected surface and never collapses, because the
 * single-mandate boundary is the property an operator most needs to be able to
 * see at a glance. When no scope is resolved it says so rather than falling
 * back to a blank, which would read as "no restriction" instead of "unknown".
 */
export function ScopeBanner() {
  const { scope } = useWorkspace();
  return (
    <dl className="scope-banner" data-scope-banner>
      <div>
        <dt>{WS04_CONTENT.scope.label}</dt>
        <dd data-mandate-label>
          {scope === null ? WS04_CONTENT.scope.none : scope.label}
        </dd>
      </div>
      <div>
        <dt>Befugnis</dt>
        <dd data-authority-state>
          {scope !== null && scope.authorityActive
            ? WS04_CONTENT.scope.authorityActive
            : WS04_CONTENT.scope.authorityInactive}
          {scope?.authorityExpiresAt
            ? ` — bis ${formatGovernedInstant(scope.authorityExpiresAt)}`
            : ""}
        </dd>
      </div>
      <div>
        <dt className="visually-hidden">Hinweis</dt>
        <dd>{WS04_CONTENT.scope.singleOnly}</dd>
      </div>
    </dl>
  );
}

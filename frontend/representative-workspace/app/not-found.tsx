import { WS04_CONTENT } from "../content/de";

/**
 * The not-found page.
 *
 * Its wording matches the scope-mismatch refusal exactly. A distinguishable
 * "no such page" versus "not your mandate" would let a direct URL walk map
 * another mandate's caseload, so the two are the same message by design.
 */
export default function NotFound() {
  return (
    <div className="workspace-shell">
      <main className="workspace-main" id="main" tabIndex={-1}>
        <div className="page-header">
          <h1>Nicht verfügbar</h1>
          <p>
            Dieser Vorgang gehört nicht zu Ihrem Mandat oder existiert nicht.
          </p>
        </div>
        <p className="informational">{WS04_CONTENT.fallback.body}</p>
      </main>
    </div>
  );
}

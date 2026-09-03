import { IsolatedVotingShell } from "../components/shell";
import { GovernedFallback, Notice } from "../components/primitives";

export const metadata = { title: "Abstimmungsbereich — EPD²" };

/**
 * A path this origin does not own.  The response says only that, and in
 * particular never says whether a protected ballot or election context exists.
 */
export default function NotFound() {
  return (
    <IsolatedVotingShell breadcrumbLabel="Nicht verfügbar">
      <div className="page-header">
        <h1>Seite nicht verfügbar</h1>
      </div>
      <Notice kind="warning" title="Kein Zugriff" role="alert">
        <p>
          Diese Adresse gehört nicht zu diesem Bereich. Es wurde nichts
          abgegeben und nichts gezählt.
        </p>
        <p>
          <a className="button button--secondary" href="/vote/credential">
            Zum Einstieg
          </a>
        </p>
      </Notice>
      <GovernedFallback />
    </IsolatedVotingShell>
  );
}

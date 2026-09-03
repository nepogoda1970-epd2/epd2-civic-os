import { IsolatedVotingShell } from "../components/shell";
import { GovernedFallback, Notice } from "../components/primitives";
import { WS03_CONTENT } from "../content/de";

export const metadata = { title: "Abstimmungsbereich — EPD²" };

/**
 * The origin root.  It is not a landing page and it grants nothing: it names
 * the boundary and points at the one entry the journey has.  There is no
 * redirect, because a redirect from here would be movement the voter did not
 * choose on an origin whose whole purpose is that nothing happens implicitly.
 */
export default function VotingOriginRoot() {
  return (
    <IsolatedVotingShell breadcrumbLabel="Übersicht">
      <div className="page-header">
        <h1>{WS03_CONTENT.workspace}</h1>
        <p>{WS03_CONTENT.boundaryNotice}</p>
      </div>
      <Notice kind="information" title="Einstieg">
        <p>
          Der Vorgang beginnt mit der Übernahme einer einmaligen,
          zweckgebundenen Stimmberechtigung aus dem Mitgliederbereich.
        </p>
        <p>
          <a className="button button--secondary" href="/vote/credential">
            {WS03_CONTENT.credential.title}
          </a>
        </p>
      </Notice>
      <GovernedFallback />
    </IsolatedVotingShell>
  );
}

import Link from "next/link";

import type { PublicFixtureDetail } from "../public/front02-fixtures";

export function PublicFixtureDetailView({
  detail,
}: {
  detail: PublicFixtureDetail;
}) {
  return (
    <main
      className="public-shell"
      data-front02-detail={detail.family}
      data-workspace="WS-01"
    >
      <section className="public-hero">
        <p className="public-eyebrow">
          Illustrative public fixture · not authoritative
        </p>
        <h1>{detail.title}</h1>
        <p className="public-lead">{detail.summary}</p>
      </section>
      <section className="public-content">
        <article className="public-section">
          <h2>Publikationskontext</h2>
          <dl className="fixture-metadata">
            <div>
              <dt>Datum</dt>
              <dd>{detail.date}</dd>
            </div>
            <div>
              <dt>Kategorie</dt>
              <dd>{detail.category}</dd>
            </div>
            <div>
              <dt>Herausgeber</dt>
              <dd>{detail.issuer}</dd>
            </div>
            <div>
              <dt>Korrekturstand</dt>
              <dd>{detail.correction}</dd>
            </div>
            <div>
              <dt>Provenienz</dt>
              <dd>{detail.provenance}</dd>
            </div>
          </dl>
        </article>
        {detail.family === "regionen" ? (
          <nav aria-label="Regional navigation" className="regional-nav">
            <Link href="/aktuelles">Aktuelles</Link>
            <Link href="/termine">Termine</Link>
            <Link href="/personen">Personen</Link>
            <Link href="/wahlen">Wahlen</Link>
          </nav>
        ) : null}
        <p className="public-note">
          Diese Darstellung führt keine Anmeldung, keine Mutation und keine
          geschützte Suche aus.
        </p>
      </section>
    </main>
  );
}

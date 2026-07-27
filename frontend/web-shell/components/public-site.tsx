import Link from "next/link";

import type { PublicPage } from "../public/content";
import { reviewed, topNavigation } from "../public/content";
import { statusLabels } from "../public/status";

const lifecycle = [
  "Entwurf",
  "automatisierte Formal- und Risikoprüfung",
  "Zulässigkeitsentscheidung",
  "Veröffentlichung",
  "Unterstützungsphase",
  "Beratung",
  "Qualifikation",
  "Rechts- und Fachprüfung",
  "Änderungen",
  "Abstimmungsreife",
  "Abstimmung",
  "angenommen oder archiviert",
  "Umsetzung und Fortschritt",
];

const programStates = [
  ["empty", "Noch keine gemeinsame Position beschlossen"],
  ["in_formation", "Positionen werden vorbereitet"],
  ["partially_formed", "Teilbereiche sind gebildet"],
  ["formed", "Beschlossene Position vorhanden"],
  ["under_revision", "Erneute Beratung läuft"],
  ["conflict_detected", "Widerspruch muss geklärt werden"],
  ["superseded", "Durch neuere Fassung ersetzt"],
] as const;

export function CapabilityStatusBanner({ page }: { page: PublicPage }) {
  return (
    <section
      aria-label="Reifegrad dieser Fähigkeit"
      className={`capability-banner capability-banner--${page.status}`}
      data-capability-status={page.status}
      data-dependent-pack={page.pack}
      data-workspace="WS-01"
    >
      <div>
        <span className="capability-banner__label">Aktueller Status</span>
        <strong>{statusLabels[page.status]}</strong>
      </div>
      <dl>
        <div>
          <dt>Verantwortlicher PACK</dt>
          <dd>{page.pack}</dd>
        </div>
        <div>
          <dt>Aktivierung</dt>
          <dd>{page.prerequisites}</dd>
        </div>
        <div>
          <dt>Zuletzt geprüft</dt>
          <dd>{reviewed}</dd>
        </div>
      </dl>
      <Link href="/status">Statussystem verstehen</Link>
    </section>
  );
}

function PublicHeader() {
  return (
    <>
      <a className="skip-link" href="#main">
        Zum Inhalt springen
      </a>
      <div className="candidate-banner" role="status">
        <strong>FRONT-01 Implementation Candidate</strong>
        <span>Keine produktive oder rechtlich aktivierte Plattform</span>
      </div>
      <header className="public-header">
        <Link aria-label="EPD² Startseite" className="logo" href="/">
          EPD²
        </Link>
        <nav aria-label="Hauptnavigation">
          {topNavigation.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
    </>
  );
}

function PublicFooter() {
  return (
    <footer className="public-footer">
      <div>
        <strong>EPD²</strong>
        <p>
          Politisches Projekt · Beteiligungsplattform · Civic-OS-Architektur
        </p>
      </div>
      <nav aria-label="Fußnavigation">
        <Link href="/datenschutz">Datenschutz</Link>
        <Link href="/barrierefreiheit">Barrierefreiheit</Link>
        <Link href="/kontakt">Kontakt</Link>
        <Link href="/impressum">Impressum</Link>
      </nav>
    </footer>
  );
}

function ProgramSkeleton() {
  return (
    <section className="public-section" aria-labelledby="program-skeleton">
      <p className="section-kicker">Read-only Prototyp</p>
      <h2 id="program-skeleton">Offenes Programmskelett</h2>
      <div className="program-grid">
        {programStates.map(([state, description], index) => (
          <article
            className="program-card"
            data-program-state={state}
            key={state}
          >
            <span>{String(index + 1).padStart(2, "0")}</span>
            <h3>{state.replaceAll("_", " ")}</h3>
            <p>{description}</p>
          </article>
        ))}
      </div>
      <p className="public-note">
        Keine Eingabe, Unterstützung, Begutachtung, Abstimmung oder
        Programmbearbeitung ist auf dieser Seite möglich.
      </p>
    </section>
  );
}

function InitiativeLifecycle() {
  return (
    <section className="public-section" aria-labelledby="initiative-lifecycle">
      <p className="section-kicker">Künftiger Lifecycle</p>
      <h2 id="initiative-lifecycle">Vom Entwurf zum Fortschrittsnachweis</h2>
      <ol className="lifecycle">
        {lifecycle.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <div className="guardrail-grid">
        <article>
          <h3>KI ist advisory</h3>
          <p>
            Sie markiert Fragen und Risiken, entscheidet aber nicht endgültig.
          </p>
        </article>
        <article>
          <h3>Prüfung folgt der Version</h3>
          <p>Rechts- und Fachgutachten sind an die exakte Fassung gebunden.</p>
        </article>
        <article>
          <h3>Archive bleiben sichtbar</h3>
          <p>
            Abgelehnte oder abgelaufene Initiativen werden nachvollziehbar
            archiviert.
          </p>
        </article>
      </div>
    </section>
  );
}

function VotingBoundary() {
  const rules = [
    "eigener Origin für WS-03",
    "keine gemeinsamen Cookies",
    "kein gemeinsamer localStorage oder IndexedDB",
    "keine gemeinsame Identity Session",
    "keine Analytics und kein Fingerprinting",
    "einmaliger, zweckgebundener Handoff",
    "keine dauerhafte Mitgliedskennung",
    "keine Stimmzetteldaten im Rückweg",
    "keine Zwischenauszählung",
    "mobil ausschließlich im Systembrowser",
  ];
  return (
    <section
      className="public-section boundary-section"
      aria-labelledby="voting-boundary"
    >
      <p className="section-kicker">NOT ACTIVATED</p>
      <h2 id="voting-boundary">Voting Client Isolation</h2>
      <ul className="boundary-list">
        {rules.map((rule) => (
          <li key={rule}>{rule}</li>
        ))}
      </ul>
      <p className="public-note">
        Erfordert PACK-15, PACK-16, PACK-17 sowie Rechts-, Sicherheits- und
        Infrastrukturfreigaben. Es gibt hier keinen Stimmzettel.
      </p>
    </section>
  );
}

function TransparencyFlow() {
  return (
    <section className="public-section" aria-labelledby="publication-flow">
      <p className="section-kicker">Governed publication</p>
      <h2 id="publication-flow">Von der Quelle zur öffentlichen Projektion</h2>
      <ol
        aria-label="Schritte der kontrollierten Veröffentlichung"
        className="publication-flow"
        tabIndex={0}
      >
        {[
          "Autoritative Quelle",
          "Prüfung",
          "Schwärzung",
          "Freigabe",
          "Publikationsprojektion",
          "Korrektur oder Ersetzung",
        ].map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <article className="sample-card">
        <strong>Illustrative example — not operational data</strong>
        <p>
          Beispieldatensatz: freigegebene Zusammenfassung, Version 2, ersetzt
          Version 1.
        </p>
      </article>
    </section>
  );
}

function Boards() {
  const initiativeStatuses = [
    "accepted",
    "awaiting_assignment",
    "planned",
    "in_progress",
    "partially_completed",
    "blocked",
    "delayed",
    "completed",
    "verified",
    "closed",
    "not_implemented",
  ];
  return (
    <section className="public-section" aria-labelledby="boards">
      <p className="section-kicker">Read-only Erklärung</p>
      <h2 id="boards">Öffentliche Fortschrittsboards</h2>
      <div className="board-grid">
        <article>
          <h3>Accepted Initiatives Board</h3>
          <p>
            Verantwortung, Maßnahmen, Termine, Hindernisse, Nachweise und
            Historie.
          </p>
          <div className="tag-cloud">
            {initiativeStatuses.map((status) => (
              <span key={status}>{status}</span>
            ))}
          </div>
        </article>
        <article>
          <h3>Program Progress Board</h3>
          <p>
            Programmzusage, politische Aktivitäten, Fortschritt, Nachweise und
            Abweichungen zwischen Programm und tatsächlichem Handeln.
          </p>
        </article>
      </div>
    </section>
  );
}

function KindSpecific({ kind }: Pick<PublicPage, "kind">) {
  if (kind === "program" || kind === "program-section")
    return <ProgramSkeleton />;
  if (kind === "initiative") return <InitiativeLifecycle />;
  if (kind === "voting") return <VotingBoundary />;
  if (kind === "transparency") return <TransparencyFlow />;
  if (kind === "boards") return <Boards />;
  return null;
}

export function PublicPageView({ page }: { page: PublicPage }) {
  return (
    <div className="public-shell" data-page-id={page.id} data-workspace="WS-01">
      <PublicHeader />
      <main id="main" tabIndex={-1}>
        <section className="public-hero">
          <p className="public-eyebrow">{page.eyebrow}</p>
          <h1>{page.title}</h1>
          <p className="public-lead">{page.lead}</p>
          {page.kind === "home" ? (
            <div className="hero-actions">
              <Link className="button button--primary" href="/programm">
                Programm verstehen
              </Link>
              <Link className="button button--secondary" href="/status">
                Entwicklungsstand
              </Link>
            </div>
          ) : null}
        </section>
        <CapabilityStatusBanner page={page} />
        <div className="public-content">
          {page.sections.map((section) => (
            <section className="public-section" key={section.title}>
              <h2>{section.title}</h2>
              <p>{section.text}</p>
              {section.items ? (
                <ul>
                  {section.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </section>
          ))}
          <KindSpecific kind={page.kind} />
          {page.kind === "home" ? (
            <section
              className="capability-index"
              aria-labelledby="capability-index"
            >
              <p className="section-kicker">So funktioniert es</p>
              <h2 id="capability-index">
                Künftige Fähigkeiten, klar gekennzeichnet
              </h2>
              <div>
                {[
                  ["/initiativen", "Initiativen"],
                  ["/beratung", "Beratung"],
                  ["/abstimmungen", "Abstimmungen"],
                  ["/buergerbuero", "Bürgerbüro"],
                  ["/abgeordnetentisch", "Abgeordnetentisch"],
                  ["/finanzen", "Finanzen"],
                  ["/fortschritt", "Fortschritt"],
                ].map(([href, label]) => (
                  <Link href={href} key={href}>
                    {label}
                    <span>Konzept ansehen →</span>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}

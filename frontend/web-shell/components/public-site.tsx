"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MouseEvent } from "react";

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

type Locale = "de" | "en";

function PublicHeader({
  locale,
  setLocale,
}: {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}) {
  return (
    <>
      <a className="skip-link" href="#main">
        Zum Inhalt springen
      </a>
      <div className="candidate-banner" role="status">
        <strong>FRONT-02 C2 Correction Candidate</strong>
        <span>
          {locale === "en"
            ? "No production-ready or legally activated platform"
            : "Keine produktive oder rechtlich aktivierte Plattform"}
        </span>
      </div>
      <header className="public-header">
        <div className="public-brand">
          <Link aria-label="EPD² Startseite" className="logo" href="/">
            EPD²
          </Link>
          <span className="public-logo-subtitle visually-hidden">
            Erste Partei Direkte Demokratie
          </span>
        </div>
        <nav aria-label="Hauptnavigation">
          {topNavigation.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div
          aria-label="Sprache / language"
          className="language-selector"
          role="group"
        >
          <button
            aria-pressed={locale === "de"}
            onClick={() => setLocale("de")}
            type="button"
          >
            DE
          </button>
          <span aria-hidden="true">|</span>
          <button
            aria-pressed={locale === "en"}
            onClick={() => setLocale("en")}
            type="button"
          >
            EN
          </button>
        </div>
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
  const [locale, setLocale] = useState<Locale>(() =>
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("lang") === "en"
      ? "en"
      : "de",
  );
  useEffect(() => {
    const selected =
      new URLSearchParams(window.location.search).get("lang") === "en"
        ? "en"
        : "de";
    setLocale(selected);
    document.documentElement.lang = selected;
  }, []);
  const english = locale === "en" && page.en;
  const visiblePage = english ? { ...page, ...page.en } : page;
  const fallback = locale === "en" && !page.en;
  const preserveLocale = (event: MouseEvent<HTMLDivElement>) => {
    if (locale !== "en") return;
    const anchor = (event.target as HTMLElement).closest(
      "a[href]",
    ) as HTMLAnchorElement | null;
    if (
      !anchor ||
      anchor.target ||
      !anchor.getAttribute("href")?.startsWith("/")
    )
      return;
    const url = new URL(anchor.href, window.location.origin);
    if (url.searchParams.get("lang") === "en") return;
    event.preventDefault();
    url.searchParams.set("lang", "en");
    window.location.assign(`${url.pathname}${url.search}${url.hash}`);
  };
  return (
    <div
      className="public-shell"
      data-page-id={page.id}
      data-workspace="WS-01"
      onClickCapture={preserveLocale}
    >
      <PublicHeader
        locale={locale}
        setLocale={(next) => {
          const query = next === "en" ? "?lang=en" : "";
          window.history.replaceState(
            null,
            "",
            `${window.location.pathname}${query}`,
          );
          document.documentElement.lang = next;
          setLocale(next);
        }}
      />
      <main id="main" tabIndex={-1}>
        {fallback ? (
          <section className="locale-fallback" lang="en">
            <strong>English rendition unavailable.</strong> The current
            authoritative content is available in German below.
          </section>
        ) : null}
        <section className="public-hero" lang={fallback ? "de" : undefined}>
          <p className="public-eyebrow">{visiblePage.eyebrow}</p>
          <h1>{visiblePage.title}</h1>
          <p className="public-lead">{visiblePage.lead}</p>
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
        <div lang={fallback ? "de" : undefined}>
          <CapabilityStatusBanner page={page} />
        </div>
        <div className="public-content" lang={fallback ? "de" : undefined}>
          {visiblePage.sections.map((section) => (
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

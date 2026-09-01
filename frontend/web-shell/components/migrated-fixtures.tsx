import Link from "next/link";
import type { ReactNode } from "react";

import {
  BackLink,
  Button,
  CandidateBanner,
  LinkButton,
  Notice,
  SearchField,
  StatusBadge,
} from "./foundation";

const publicNavigation = [
  "Über uns",
  "Programm",
  "Programmwerkstatt",
  "Struktur",
  "Mitmachen",
  "Transparenz",
  "Aktuelles",
] as const;

const internalNavigation = [
  "Dashboard",
  "Programmwerkstatt",
  "Meine Vorschläge",
  "Meine Stimmen & Delegation",
  "Kommunikation",
  "Organisation ⭐",
  "Versammlungen & Termine",
  "Schwarzes Brett",
  "Vertrauensarchitektur",
  "Delegation & Reputation",
  "Profil / Einstellungen",
] as const;

function PublicHeader({ current }: { current?: string }) {
  return (
    <header className="fixture-header">
      <Link className="logo" href="/foundation/examples/public">
        EPD²
      </Link>
      <nav aria-label="Hauptnavigation" className="fixture-public-nav">
        {publicNavigation.map((item) => (
          <a
            aria-current={item === current ? "page" : undefined}
            href="#"
            key={item}
          >
            {item}
          </a>
        ))}
      </nav>
      <LinkButton href="#" variant="primary">
        Mitglied werden
      </LinkButton>
    </header>
  );
}

function PublicFooter({ login = false }: { login?: boolean }) {
  const links = [
    "Impressum",
    "Datenschutz",
    "Nutzungsbedingungen",
    "Satzung",
    "eID-Verifizierung",
    ...(login ? ["Bürgerannahme", "Bürger-Login"] : []),
    "Kontakt",
  ];
  return (
    <footer className="fixture-footer">
      <p>© 2026 EPD² — Digitale Demokratie für Deutschland</p>
      <nav aria-label="Fußnavigation">
        {links.map((item) => (
          <a href="#" key={item}>
            {item}
          </a>
        ))}
      </nav>
    </footer>
  );
}

function FixtureFrame({
  source,
  children,
}: {
  source: string;
  children: ReactNode;
}) {
  return (
    <div className="migrated-fixture">
      <a className="skip-link" href="#fixture-main">
        Zum Inhalt springen
      </a>
      <CandidateBanner source={source} />
      {children}
    </div>
  );
}

function FixtureCard({
  title,
  children,
  number,
}: {
  title: string;
  children: ReactNode;
  number?: string;
}) {
  return (
    <section className="fixture-card">
      {number ? <div className="fixture-number">{number}</div> : null}
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export function PublicHomeFixture() {
  return (
    <FixtureFrame source="index.html">
      <PublicHeader />
      <main id="fixture-main" tabIndex={-1}>
        <section className="fixture-home-hero">
          <div>
            <p className="fixture-kicker">
              Digitale Demokratie für Deutschland
            </p>
            <h1>EPD² bringt politische Entscheidung zurück zu den Bürgern.</h1>
            <p className="fixture-lead">
              EPD² verbindet offene Programmarbeit, verifizierte Beteiligung,
              digitale Abstimmungen und transparente Dokumentation zu einer
              neuen politischen Infrastruktur.
            </p>
            <div className="fixture-actions">
              <LinkButton href="#" variant="primary">
                Programm mitgestalten
              </LinkButton>
              <LinkButton href="#">Mitglied werden</LinkButton>
              <LinkButton href="#">Bürgerbereich</LinkButton>
            </div>
            <p className="fixture-small">
              eID-Verifizierung geplant · Programmwerkstatt ·
              Transparenz-Zentrum · Bürgerbereich im Aufbau
            </p>
          </div>
        </section>
        <section className="fixture-section fixture-section--soft">
          <div className="fixture-content">
            <h2>Worum es geht</h2>
            <p className="fixture-intro">
              EPD² ist keine fertige Programmschrift von oben, sondern eine
              politische Plattform: Bürger bringen Probleme ein, Vorschläge
              werden strukturiert, diskutiert, geprüft und von verifizierten
              Mitgliedern demokratisch entschieden.
            </p>
            <div className="fixture-grid">
              <FixtureCard title="Programm">
                <p>
                  Die politischen Schwerpunkte entstehen offen, nachvollziehbar
                  und entwicklungsfähig.
                </p>
              </FixtureCard>
              <FixtureCard title="Programmwerkstatt">
                <p>
                  Vorschläge einreichen, strukturieren, diskutieren und zur
                  Entscheidung bringen.
                </p>
              </FixtureCard>
              <FixtureCard title="Transparenz">
                <p>
                  Finanzen, Entscheidungen, Protokolle und Beteiligung
                  nachvollziehbar dokumentieren.
                </p>
              </FixtureCard>
            </div>
          </div>
        </section>
        <section className="fixture-section">
          <div className="fixture-content">
            <h2>Drei Wege, sofort einzusteigen</h2>
            <div className="fixture-grid">
              <FixtureCard number="01" title="Problem einreichen">
                <p>
                  Ein konkretes gesellschaftliches Problem beschreiben und in
                  die Programmwerkstatt einbringen.
                </p>
              </FixtureCard>
              <FixtureCard number="02" title="Mitglied werden">
                <p>
                  Mitgliedschaft vorbereiten und die spätere verifizierte
                  Beteiligung ermöglichen.
                </p>
              </FixtureCard>
              <FixtureCard number="03" title="Bürgerbereich">
                <p>
                  Der persönliche Bereich für Vorschläge, Abstimmungen und
                  Delegationen befindet sich im Aufbau.
                </p>
              </FixtureCard>
            </div>
          </div>
        </section>
        <section className="fixture-section fixture-section--soft">
          <div className="fixture-content fixture-two-column">
            <div>
              <h2>Bürgerbereich im Aufbau</h2>
              <p className="fixture-intro">
                Der Login zum persönlichen Kabinett ist geplant. Dort sollen
                Mitglieder künftig Vorschläge verwalten, Abstimmungen verfolgen,
                Stimmen delegieren und ihre regionale Beteiligung einsehen
                können.
              </p>
              <p>
                Bis zur technischen Freischaltung führt der öffentliche Einstieg
                über Mitgliedschaft, Kontakt und Programmwerkstatt.
              </p>
            </div>
            <FixtureCard title="Geplante Funktionen">
              <ul>
                <li>Profil und Mitgliedsstatus</li>
                <li>Eigene Vorschläge</li>
                <li>Abstimmungen und Delegationen</li>
                <li>Kommunikation mit Gremien</li>
                <li>Transparente Beteiligungshistorie</li>
              </ul>
            </FixtureCard>
          </div>
        </section>
        <section className="fixture-section fixture-cta">
          <h2>EPD² mit aufbauen</h2>
          <p>
            Der Aufbau beginnt mit Menschen, die Struktur, Programm, Technik und
            Vertrauen gemeinsam entwickeln wollen.
          </p>
          <LinkButton href="#" variant="primary">
            Jetzt mitmachen
          </LinkButton>
        </section>
      </main>
      <PublicFooter />
    </FixtureFrame>
  );
}

function InternalHeader() {
  return (
    <header className="fixture-header fixture-internal-header">
      <div className="fixture-brand">
        <Link className="logo" href="#">
          EPD²
        </Link>
        <span>Intern</span>
      </div>
      <div className="fixture-identity">
        <span className="fixture-live">● Systemstatus Fixture</span>
        <StatusBadge state="prototype">eID-verifiziert (Beispiel)</StatusBadge>
        <div className="fixture-identity-copy">
          <strong>Bürger-ID #48291</strong>
          <small>Statische Beispieldaten</small>
        </div>
        <span className="fixture-avatar" aria-hidden="true">
          #48291
        </span>
      </div>
    </header>
  );
}

function InternalFrame({
  current,
  children,
  source,
}: {
  current: string;
  children: ReactNode;
  source: string;
}) {
  return (
    <FixtureFrame source={source}>
      <InternalHeader />
      <div className="fixture-internal-layout">
        <aside className="fixture-sidebar">
          <nav aria-label="Interne Navigation">
            {internalNavigation.map((item) => (
              <a
                aria-current={item === current ? "page" : undefined}
                href="#"
                key={item}
              >
                {item}
              </a>
            ))}
          </nav>
        </aside>
        <main className="fixture-internal-main" id="fixture-main" tabIndex={-1}>
          {children}
        </main>
      </div>
      <PublicFooter />
    </FixtureFrame>
  );
}

const dashboardCards = [
  [
    "Meine Organisation",
    "Landesverband Berlin|Regionalverband Steglitz-Zehlendorf|Ortsverband Steglitz-Süd",
    "Ansprechpartner ansehen",
  ],
  [
    "Vorstand kontaktieren",
    "Ortsvorstand Steglitz-Süd|Regionalvorstand Steglitz-Zehlendorf|Landesvorstand Berlin",
    "",
  ],
  [
    "Meine Mandatsträger",
    "Bezirksverordneter — Steglitz-Zehlendorf|Landesliste Berlin — Kandidat 2027",
    "Nachricht senden",
  ],
  [
    "Nächste Termine",
    "Ortsgruppentreffen — 12. Juni 2026 · 19:00 Uhr|Landesversammlung — 05. Juli 2026 · Berlin",
    "Alle Termine anzeigen",
  ],
  [
    "Regionale Initiativen",
    "Schulwegsicherheit Steglitz — Diskussion offen|Digitale Bürgerdienste Berlin — KI-Strukturierung läuft",
    "Initiativen öffnen",
  ],
  [
    "Parteiversammlungen",
    "Teilnahme an digitalen Parteiversammlungen mit Tagesordnung, Anträgen, Diskussion, Abstimmung und Protokoll.|Nächste Online-Versammlung — Heute · 20:00 Uhr",
    "Zu den Versammlungen",
  ],
  [
    "Abgeordnetentisch",
    "Parlamentarische Schnittstelle: Arbeitsdokumente, Wochenplan, Beteiligung, Abstimmungsverhalten und öffentliche Begründungen bei Abweichungen.|Vertrauensindikator Berlin — 82 % Vertrauen · 11 % Beobachtung · 7 % Klärungsbedarf",
    "Abgeordnetentisch öffnen",
  ],
  [
    "Aktuelle Abstimmungen",
    "Bahn-Reform — endet in 3 Tagen · Ergebnisanzeige nur statische Quelle|Digitale Verwaltung Berlin — Vorprüfung aktiv",
    "Abstimmungen öffnen",
  ],
] as const;

export function DashboardFixture() {
  return (
    <InternalFrame current="Dashboard" source="intern/dashboard.html">
      <h1>Guten Abend, Bürger #48291</h1>
      <p className="fixture-muted">
        Ihr persönlicher Überblick über Mitgliedschaft, Region und Beteiligung.
      </p>
      <Notice kind="authority" title="Statische Candidate-Fixture">
        <p>
          Identität, Status, Termine und Kennzahlen sind unveränderte
          Layout-Beispiele aus der Quelle. Es findet keine Authentifizierung
          oder Datenabfrage statt.
        </p>
      </Notice>
      <section className="fixture-profile" aria-labelledby="member-number">
        <div className="fixture-profile-head">
          <div>
            <span>Mitgliedsnummer</span>
            <strong id="member-number">EPD-2026-0048291</strong>
          </div>
          <StatusBadge state="prototype">eID-verifiziert (Fixture)</StatusBadge>
        </div>
        <dl className="fixture-profile-meta">
          <div>
            <dt>Landesverband</dt>
            <dd>Berlin</dd>
          </div>
          <div>
            <dt>Regionalverband</dt>
            <dd>Steglitz-Zehlendorf</dd>
          </div>
          <div>
            <dt>Ortsverband</dt>
            <dd>Steglitz-Süd</dd>
          </div>
          <div>
            <dt>Wahlkreis</dt>
            <dd>Berlin-Steglitz-Zehlendorf</dd>
          </div>
        </dl>
      </section>
      <div className="fixture-dashboard-grid">
        {dashboardCards.map(([title, content, action]) => (
          <FixtureCard key={title} title={title}>
            <div className="fixture-soft-list">
              {content.split("|").map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
            {action ? (
              <LinkButton
                href="#"
                variant={
                  title === "Parteiversammlungen" ||
                  title === "Aktuelle Abstimmungen"
                    ? "primary"
                    : "secondary"
                }
              >
                {action}
              </LinkButton>
            ) : null}
          </FixtureCard>
        ))}
      </div>
    </InternalFrame>
  );
}

export function CommunicationFixture() {
  return (
    <InternalFrame current="Kommunikation" source="intern/kommunikation.html">
      <h1>Kommunikation</h1>
      <p className="fixture-muted">
        Sichere und protokollierte Kommunikation innerhalb der EPD²
      </p>
      <Notice kind="legal" title="Nicht aktiviert">
        <p>
          Diese Migration zeigt ausschließlich die Quellkomposition. Nachrichten
          werden weder geladen noch gesendet oder gespeichert.
        </p>
      </Notice>
      <nav aria-label="Kommunikationsbereiche" className="fixture-tabs">
        <a aria-current="page" href="#">
          Direktnachrichten
        </a>
        <a href="#">Gruppen & Channels</a>
        <a href="#">KI-Unterstützung</a>
      </nav>
      <div className="fixture-communication-grid">
        <section aria-label="Dialogliste">
          <SearchField
            id="conversation-search"
            label="Dialoge suchen"
            placeholder="Suchen..."
          />
          <div className="fixture-message-item fixture-message-item--current">
            <strong>Bahn-Reform Arbeitsgruppe</strong>
            <small>4 neue Nachrichten (Fixture)</small>
          </div>
          <div className="fixture-message-item">
            <strong>Mitglied #18420</strong>
            <small>Verfassungsbeirat</small>
          </div>
          <div className="fixture-message-item">
            <strong>KI-Unterstützung</strong>
            <small>Neue Analyse verfügbar (Fixture)</small>
          </div>
        </section>
        <section aria-labelledby="conversation-title">
          <div className="fixture-conversation-head">
            <strong id="conversation-title">Bahn-Reform Arbeitsgruppe</strong>
            <StatusBadge state="prototype">
              Verschlüsselung nicht verbunden
            </StatusBadge>
          </div>
          <div className="fixture-chat">
            <p className="fixture-chat-date">
              Heute, 11:32 Uhr — statischer Inhalt
            </p>
            <article className="fixture-bubble">
              <strong>Mitglied #18420</strong>
              <p>
                Ich schlage vor, den Fokus stärker auf die regionale
                Infrastruktur zu legen.
              </p>
            </article>
            <article className="fixture-bubble">
              <strong>Bürger #48291</strong>
              <p>Das würde besser zur Dezentralisierungsstrategie passen.</p>
            </article>
            <article className="fixture-bubble">
              <strong>Mitglied #18420</strong>
              <p>Sollten wir das in den nächsten Vorschlag einbauen?</p>
              <small>Bearbeitet von KI-Unterstützung markiert</small>
            </article>
          </div>
          <div className="fixture-compose">
            <label className="visually-hidden" htmlFor="message">
              Nachricht schreiben
            </label>
            <input disabled id="message" placeholder="Nachricht schreiben..." />
            <Button disabled>Nicht verbunden</Button>
          </div>
          <p className="fixture-small fixture-centered">
            Keine Kommunikations-, Moderations- oder Protokollfunktion ist
            aktiviert.
          </p>
        </section>
      </div>
    </InternalFrame>
  );
}

export function LoginFixture() {
  return (
    <FixtureFrame source="buerger-login.html">
      <PublicHeader />
      <main className="fixture-login-main" id="fixture-main" tabIndex={-1}>
        <section>
          <p className="fixture-kicker">Geschützter Mitgliederbereich</p>
          <h1>EPD² — Bürger-Login</h1>
          <p className="fixture-lead">
            Der Bürger-Login ist der Zugang zum persönlichen
            EPD²-Mitgliederbereich. Nach Freischaltung des Mitgliedskontos
            erfolgt der normale Zugang mit E-Mail oder Mitgliedsnummer, Passwort
            und zusätzlicher Sicherheitsbestätigung.
          </p>
          <Notice title="Erst Verifizierung, dann Konto">
            <p>
              Ein Mitgliedskonto wird nicht nur durch eine E-Mail-Adresse
              eröffnet. Die Freischaltung erfolgt nach Mitgliedsantrag und
              Identitätsprüfung — aktuell über manuelle Prüfung, später
              zusätzlich über eID-Verifizierung.
            </p>
          </Notice>
          <div className="fixture-grid fixture-login-cards">
            <FixtureCard title="Normaler Login">
              <p>
                E-Mail oder Mitgliedsnummer, Passwort und 2-Faktor-Bestätigung.
              </p>
            </FixtureCard>
            <FixtureCard title="Sensible Vorgänge">
              <p>
                Für Abstimmungen, digitale Versammlungen und Kandidaturen kann
                eine erneute Identitätsbestätigung erforderlich sein.
              </p>
            </FixtureCard>
            <FixtureCard title="Online-Versammlungen">
              <p>
                Nach dem Login führt der Bereich „Versammlungen“ zu
                Tagesordnung, Anträgen, Diskussion, Abstimmung und Protokoll.
              </p>
            </FixtureCard>
          </div>
        </section>
        <section
          className="fixture-login-panel"
          aria-labelledby="login-heading"
        >
          <h2 id="login-heading">Einloggen</h2>
          <p>
            Visuelle Candidate-Fixture. Keine echte Authentifizierung oder
            Übermittlung.
          </p>
          <form onSubmit={undefined}>
            <label htmlFor="login">E-Mail oder Mitgliedsnummer</label>
            <input
              disabled
              id="login"
              placeholder="name@example.de oder EPD-2026-…"
            />
            <label htmlFor="password">Passwort</label>
            <input
              disabled
              id="password"
              placeholder="••••••••"
              type="password"
            />
            <label htmlFor="code">2-Faktor-Code</label>
            <input
              disabled
              id="code"
              placeholder="6-stelliger Code"
              inputMode="numeric"
            />
            <Button disabled type="submit">
              Nicht verbunden
            </Button>
          </form>
          <div className="fixture-form-actions">
            <LinkButton href="#">Mitgliedskonto aktivieren</LinkButton>
            <LinkButton href="#">Noch kein Mitglied?</LinkButton>
            <LinkButton href="#">Passwort-Hilfe</LinkButton>
          </div>
        </section>
      </main>
      <PublicFooter login />
    </FixtureFrame>
  );
}

export function AbstimmungenFixture() {
  return (
    <FixtureFrame source="struktur/abstimmungen.html">
      <PublicHeader current="Struktur" />
      <main className="fixture-vote-info" id="fixture-main" tabIndex={-1}>
        <h1>Parteitage & Abstimmungen</h1>
        <p className="fixture-lead">
          Parteitage, Mitgliederentscheidungen und Abstimmungen werden als
          zentrale Elemente demokratischer Willensbildung verstanden.
        </p>
        <Notice kind="legal" title="Keine Abstimmungsfunktion">
          <p>
            Diese Seite ist eine visuelle Candidate-Fixture. Sie aktiviert weder
            Teilnahme, Stimmabgabe noch Ergebnisermittlung.
          </p>
        </Notice>
        <section
          className="fixture-vote-callout"
          aria-label="Geplanter Beteiligungsrahmen"
        >
          <p>
            EPD² will physische, hybride und digitale Beteiligungsformen
            rechtssicher miteinander verbinden.
          </p>
          <p>
            Konkrete Termine, Verfahren und Abstimmungsergebnisse werden
            veröffentlicht, sobald die entsprechenden Strukturen aktiv sind.
          </p>
        </section>
        <BackLink href="/foundation">Zurück zur Struktur</BackLink>
      </main>
      <PublicFooter />
    </FixtureFrame>
  );
}

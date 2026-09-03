import type { CapabilityStatus } from "./status";

export type PublicPage = {
  id: string;
  path: string;
  title: string;
  eyebrow: string;
  lead: string;
  status: CapabilityStatus;
  pack: string;
  prerequisites: string;
  kind:
    | "standard"
    | "home"
    | "program"
    | "program-section"
    | "initiative"
    | "voting"
    | "finance"
    | "citizen-office"
    | "representatives"
    | "transparency"
    | "technology"
    | "boards"
    | "status";
  sections: readonly {
    title: string;
    text: string;
    items?: readonly string[];
  }[];
  en?: {
    title: string;
    eyebrow: string;
    lead: string;
    sections: readonly {
      title: string;
      text: string;
      items?: readonly string[];
    }[];
  };
};

const reviewed = "27.07.2026";
export { reviewed };

export const publicPages: readonly PublicPage[] = [
  {
    id: "FRONT01-PAGE-001",
    path: "/",
    title: "Politische Beteiligung, nachvollziehbar aufgebaut",
    eyebrow: "EPD² · Partei, Plattform und Civic OS",
    lead: "EPD² ist ein politisches und zivilgesellschaftliches Aufbauprojekt. Die Partei gibt den demokratischen Rahmen, die Plattform organisiert Beteiligung und das Civic OS beschreibt die dafür entwickelte Softwarearchitektur.",
    status: "foundation_available",
    pack: "FRONT-00 / PACK-01–09",
    prerequisites:
      "Fachliche Workspaces, Rechtsprüfung und Produktionsfreigaben",
    kind: "home",
    sections: [
      {
        title: "Was heute belastbar ist",
        text: "Die gemeinsame Frontend-Grundlage und die Backend-Pakete PACK-01 bis PACK-09 haben den finalen Prüfstatus erreicht. Diese Website ist die erste öffentliche Migration auf dieser Grundlage.",
        items: [
          "ein gemeinsames, barrierearm ausgerichtetes Designsystem",
          "zehn getrennte Workspaces und zehn getrennte Origins als Zielarchitektur",
          "Versionen, Zuständigkeiten und Aktivierungsvoraussetzungen sichtbar machen",
        ],
      },
      {
        title: "Was noch nicht aktiviert ist",
        text: "Produktive Abstimmungen, bindende eID-Nutzung, Finanzabläufe und institutionelle Fallbearbeitung sind nicht aktiviert. Beschreibungen dieser Bereiche sind Konzepte, Spezifikationen oder öffentliche Prototypen.",
      },
      {
        title: "Wie Beteiligung wachsen soll",
        text: "Beteiligung soll von verständlicher Information über Initiativen und Beratung bis zu überprüfbaren Entscheidungen reichen. Politische und rechtliche Wirkung entsteht nie automatisch durch eine Oberfläche, KI oder eID.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-002",
    path: "/ueber-uns",
    title: "Über EPD²",
    eyebrow: "Organisation und Vorhaben",
    lead: "EPD² verbindet politische Organisation, offene Programmbildung und eine getrennte, überprüfbare digitale Infrastruktur.",
    status: "informational",
    pack: "PACK-08 / PACK-18",
    prerequisites: "Freigegebene Organisationsdarstellung",
    kind: "standard",
    sections: [
      {
        title: "Drei Ebenen, klare Aufgaben",
        text: "Die Partei trifft politische Entscheidungen im Rahmen von Recht und Satzung. Die Plattform ermöglicht Beteiligung. Das Civic OS ist die technische Architektur – es ersetzt weder politische Verantwortung noch Rechtsprüfung.",
      },
      {
        title: "Der aktuelle Aufbau",
        text: "Der öffentliche Auftritt wird schrittweise migriert. Funktionsbeschreibungen sind mit ihrem Reifegrad gekennzeichnet und dürfen nicht als laufender Dienst verstanden werden.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-003",
    path: "/ziele",
    title: "Ziele",
    eyebrow: "Demokratische Wirkung braucht nachvollziehbare Verfahren",
    lead: "EPD² will Beteiligung verständlicher, institutionelle Verantwortung sichtbarer und politische Arbeit überprüfbarer machen.",
    status: "informational",
    pack: "PACK-18",
    prerequisites: "Politische Beschlussfassung zu einzelnen Zielen",
    kind: "standard",
    sections: [
      {
        title: "Beteiligung mit Grenzen",
        text: "Offenheit bedeutet nicht Beliebigkeit. Zuständigkeit, Datenschutz, freies Mandat, Rechtsschutz und sichere Abstimmungsgrenzen bleiben verbindliche Leitplanken.",
      },
      {
        title: "Fortschritt statt Versprechen",
        text: "Angenommene Entscheidungen und Programmpositionen sollen später mit Verantwortlichen, Fristen, Nachweisen, Hindernissen und Änderungshistorie verfolgt werden.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-004",
    path: "/grundsaetze",
    title: "Grundsätze und Grenzen",
    eyebrow: "Politischer Ausgangspunkt",
    lead: "Ein kurzes Grundsatzprogramm bildet den erkennbaren politischen Rahmen. Offene Programmbildung ergänzt diesen Rahmen, ersetzt ihn aber nicht.",
    status: "informational",
    pack: "PACK-18 / PACK-32",
    prerequisites: "Formelle Annahme der jeweiligen Programmfassung",
    kind: "standard",
    sections: [
      {
        title: "Demokratische Verantwortung",
        text: "KI bleibt beratend. Entscheidungen werden von zuständigen Menschen und Organen getroffen. Das freie Mandat wird nicht durch Bindungswerte, automatische Sanktionen oder Abwahlmechaniken ersetzt.",
      },
      {
        title: "Nachvollziehbarkeit",
        text: "Quellen, Beratungsstände, Gutachten und Beschlüsse sollen an exakte Versionen gebunden sein. Wesentliche Änderungen lösen eine erneute Prüfung aus.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-005",
    path: "/programm",
    title: "Das offene Programm",
    eyebrow: "Öffentliche Lesefassung · noch kein PACK-32 Workflow",
    lead: "Das Programm soll aus einem stabilen Grundsatzrahmen und schrittweise gebildeten thematischen Positionen bestehen. Leere Bereiche werden sichtbar bleiben.",
    status: "prototype",
    pack: "PACK-32",
    prerequisites: "PACK-32, FRONT-04/FRONT-10 und formelle Annahme",
    kind: "program",
    sections: [
      {
        title: "Warum ein offenes Gerüst?",
        text: "Pflichtthemen verschwinden nicht, nur weil noch keine gemeinsame Position beschlossen wurde. Freie Themenblöcke können später nach einem geregelten Verfahren ergänzt werden.",
      },
      {
        title: "Trennung der Fassungen",
        text: "Arbeitsstände, angenommene Positionen und offiziell verabschiedete Programmversionen sind getrennt. Offizielle Versionen bleiben unveränderlich; spätere Änderungen erzeugen eine neue Version.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-006",
    path: "/programm/struktur",
    title: "Programmstruktur",
    eyebrow: "Read-only Programmskelett",
    lead: "Sieben kontrollierte Zustände zeigen ehrlich, ob ein Themenbereich leer, in Bildung, teilweise oder vollständig gebildet, in Überarbeitung, konfliktbehaftet oder ersetzt ist.",
    status: "prototype",
    pack: "PACK-32",
    prerequisites: "Operativer Program Formation Lifecycle",
    kind: "program",
    sections: [
      {
        title: "Pflichtthemen",
        text: "Demokratie und Staat, Wirtschaft und Arbeit, Soziales, Klima, Bildung, Europa und Außenpolitik bleiben als dauerhafte Orientierung sichtbar.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-007",
    path: "/programm/status",
    title: "Programmstatus",
    eyebrow: "Reifegrad statt Vollständigkeitsbehauptung",
    lead: "Noch nicht beschlossene Positionen werden nicht durch redaktionelle Platzhalter als Parteilinie ausgegeben.",
    status: "not_activated",
    pack: "PACK-32",
    prerequisites: "Beschlussfähiger Lifecycle und Publikationsfreigabe",
    kind: "program-section",
    sections: [
      {
        title: "Aktueller Hinweis",
        text: "Diese Ansicht demonstriert die spätere Statuslogik. Sie nimmt keine Vorschläge an und ändert kein Programm.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-008",
    path: "/mitmachen",
    title: "Mitmachen",
    eyebrow: "Öffentliche Beteiligungswege",
    lead: "Du kannst das Projekt verfolgen, Rückmeldungen geben und dich über künftige Beteiligungswege informieren. Ein Mitgliederkonto wird hier nicht bereitgestellt.",
    status: "informational",
    pack: "PACK-18",
    prerequisites:
      "Getrennte Aktivierung künftiger Mitgliederfunktionen in WS-02",
    kind: "standard",
    sections: [
      {
        title: "Heute möglich",
        text: "Öffentliche Informationen lesen, Kontakt aufnehmen und den Entwicklungsstand nachvollziehen.",
      },
      {
        title: "Später in getrennten Workspaces",
        text: "Mitgliedsbezogene Beteiligung, Bürgeranliegen und Abstimmungen erhalten eigene Origins und zweckgebundene Sitzungen.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-009",
    path: "/mitgliedschaft",
    title: "Mitgliedschaft",
    eyebrow: "Information · kein Online-Beitritt",
    lead: "Diese Seite erklärt den vorgesehenen Weg zur Mitgliedschaft. Sie enthält weder Kontoeröffnung noch eID- oder Zahlungsablauf.",
    status: "planned",
    pack: "PACK-18 / WS-02",
    prerequisites:
      "Mitgliedschaftsprozess, Datenschutzinformation und rechtliche Freigabe",
    kind: "standard",
    sections: [
      {
        title: "Getrennter Mitgliederbereich",
        text: "Ein späterer Login ist ein ausdrücklicher Handoff zu WS-02. Es gibt keine globale Sitzung und keine automatische Berechtigung für andere Workspaces.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-010",
    path: "/organisation",
    title: "Organisation",
    eyebrow: "Partei und Plattform",
    lead: "Aufgaben, Zuständigkeiten und regionale Ebenen sollen nachvollziehbar dargestellt werden, ohne eine noch nicht freigegebene Amtsbesetzung zu behaupten.",
    status: "informational",
    pack: "PACK-08 / PACK-28",
    prerequisites: "Freigegebene öffentliche Organisationsprojektion",
    kind: "standard",
    sections: [
      {
        title: "Bund, Land und Kreis",
        text: "Die Datenarchitektur trennt Organisationsbereiche von Beginn an. Öffentliche Angaben stammen später nur aus freigegebenen Projektionen.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-011",
    path: "/struktur",
    title: "Struktur und Regionen",
    eyebrow: "Organisationsmodell",
    lead: "EPD² ist mit getrennten Zuständigkeitsbereichen für Bund, Länder und Kreise entworfen.",
    status: "specified",
    pack: "PACK-08 / PACK-28",
    prerequisites: "Autoritative Organisationsdaten und Publikationsprüfung",
    kind: "standard",
    sections: [
      {
        title: "Keine globale Organisationsrolle",
        text: "Berechtigungen sind an Rolle, Organisation und konkreten Datensatz gebunden. Ein Universal-Admin ist ausgeschlossen.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-012",
    path: "/transparenz",
    title: "Transparenz durch freigegebene Projektionen",
    eyebrow: "Zielmodell · keine operativen Logs",
    lead: "Öffentliche Transparenz liest nicht direkt aus geschützten Arbeits- oder Quelldatenbanken.",
    status: "specified",
    pack: "PACK-28 / WS-10",
    prerequisites: "Review, Schwärzung, Freigabe und Publikationsdienst",
    kind: "transparency",
    sections: [
      {
        title: "Kontrollierter Veröffentlichungsweg",
        text: "Autoritative Quelle, Prüfung, Schwärzung, Freigabe, öffentliche Projektion und eine nachvollziehbare Korrektur- oder Ersetzungshistorie bleiben getrennte Schritte.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-013",
    path: "/technologie",
    title: "Technologie mit überprüfbaren Grenzen",
    eyebrow: "Architektur · keine Sicherheitsgarantie",
    lead: "Das Civic OS setzt auf Zweckbindung, getrennte Vertrauensgrenzen und versionierte Verträge. Architektur allein beweist keine Produktions- oder Rechtssicherheit.",
    status: "implemented_reference",
    pack: "PACK-01–09 / FRONT-00",
    prerequisites:
      "Je Fähigkeit eigene Security-, Legal- und Infrastruktur-Gates",
    kind: "technology",
    sections: [
      {
        title: "Zehn Workspaces, zehn Origins",
        text: "Öffentliche Website, Mitgliederanwendung, Voting Client und institutionelle Arbeitsbereiche werden nicht zu einer universellen Anwendung zusammengezogen.",
      },
      {
        title: "KI bleibt beratend",
        text: "KI kann Zusammenfassungen, Widersprüche, Risiken und offene Fragen sichtbar machen. Sie trifft keine endgültige politische oder rechtliche Entscheidung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-014",
    path: "/sicherheit",
    title: "Sicherheit ist ein Freigabeprozess",
    eyebrow: "Threat Models, Tests und unabhängige Prüfung",
    lead: "Sicherheitsbehauptungen gelten nur für den belegten Umfang. Noch nicht aktivierte Fähigkeiten werden nicht als sicher oder einsatzbereit bezeichnet.",
    status: "production_blocked",
    pack: "PACK-15–17",
    prerequisites:
      "Implementierung, unabhängige Verifikation und Betriebsfreigabe",
    kind: "technology",
    sections: [
      {
        title: "Keine Abkürzung durch Kryptografie",
        text: "Kryptografie kann Teil eines überprüfbaren Systems sein, garantiert aber weder demokratische Legitimität noch rechtliche Wirksamkeit.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-015",
    path: "/datenschutz",
    title: "Datenschutz und Zweckbindung",
    eyebrow: "Öffentliche Information",
    lead: "Diese Website vermeidet Tracking, Fingerprinting und workspaceübergreifende Identifikatoren.",
    status: "informational",
    pack: "PACK-09 / PACK-18",
    prerequisites: "Zweckspezifische Hinweise vor jedem künftigen Formular",
    kind: "standard",
    sections: [
      {
        title: "Künftige Formulare",
        text: "Jeder spätere Dienst benötigt eigene Angaben zu Zweck, Rechtsgrundlage, Empfängern, Aufbewahrung, Rechten und automatisierter oder KI-gestützter Verarbeitung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-016",
    path: "/barrierefreiheit",
    title: "Barrierefreiheit",
    eyebrow: "Definition of Done",
    lead: "Semantische Struktur, Tastaturbedienung, sichtbarer Fokus, reduzierte Bewegung und verständliche Statusangaben werden von Beginn an geprüft.",
    status: "foundation_available",
    pack: "FRONT-00 / FRONT-01",
    prerequisites:
      "Fortlaufende Tests und Prüfung mit realen Nutzerinnen und Nutzern",
    kind: "standard",
    sections: [
      {
        title: "Kein Zertifizierungsversprechen",
        text: "Die Umsetzung orientiert sich an WCAG 2.1 AA und wird automatisiert geprüft. Damit wird keine vollständige WCAG-Zertifizierung behauptet.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-017",
    path: "/kontakt",
    title: "Kontakt",
    eyebrow: "Allgemeiner öffentlicher Kontakt",
    lead: "Für allgemeine Fragen kann der veröffentlichte Organisationskontakt genutzt werden. Diese Seite ist kein Bürgerbüro und kein rechtlicher Zustellkanal.",
    status: "informational",
    pack: "PACK-18",
    prerequisites: "Gesonderte Hinweise für künftige zweckspezifische Kanäle",
    kind: "standard",
    sections: [
      {
        title: "Keine automatische Rechtswirkung",
        text: "Versand, Eingang oder Lesebestätigung einer Nachricht begründen nicht automatisch eine rechtliche Wirkung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-018",
    path: "/impressum",
    title: "Impressum",
    eyebrow: "Anbieterkennzeichnung",
    lead: "EPD Plattform e.V., VR 42522 B, Sitz Berlin. Die vollständigen freigegebenen Kontaktangaben sind vor öffentlicher Bereitstellung organisatorisch zu bestätigen.",
    status: "informational",
    pack: "PACK-09",
    prerequisites:
      "Juristische und redaktionelle Freigabe der aktuellen Pflichtangaben",
    kind: "standard",
    sections: [
      {
        title: "Hinweis",
        text: "Der technische Candidate ist keine öffentliche Inbetriebnahme und ersetzt keine Prüfung der Pflichtangaben.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-019",
    path: "/initiativen",
    title: "Von der Initiative zur überprüfbaren Umsetzung",
    eyebrow: "Erklärmodell · Workflow nicht aktiviert",
    lead: "Der künftige Lebenszyklus trennt Entwurf, Prüfung, Beratung, Abstimmungsreife, Entscheidung und Fortschrittskontrolle.",
    status: "specified",
    pack: "PACK-03 / PACK-32",
    prerequisites: "Fachliche Frontends, Rechtsprüfung und Aktivierung",
    kind: "initiative",
    sections: [
      {
        title: "Beratung vor Wirkung",
        text: "Automatisierte Prüfungen markieren formale und Risikofragen. Die endgültige Zulässigkeits- oder Ablehnungsentscheidung bleibt bei der zuständigen menschlichen Stelle.",
      },
      {
        title: "Versionsgebundene Gutachten",
        text: "Rechtliche und fachliche Stellungnahmen beziehen sich auf eine exakte Fassung. Materielle Änderungen erfordern eine erneute Prüfung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-020",
    path: "/beratung",
    title: "Öffentliche Beratung",
    eyebrow: "Deliberation-Konzept",
    lead: "Argumente, Quellen, Änderungen und Gegenpositionen sollen nachvollziehbar zusammengeführt werden, ohne Widerspruch unsichtbar zu machen.",
    status: "specified",
    pack: "PACK-03",
    prerequisites: "Moderation, Schutzkonzept und fachlicher Workspace",
    kind: "initiative",
    sections: [
      {
        title: "Ein-Klick-KI-Analyse",
        text: "Geplant ist eine snapshotgebundene Analyse mit Zusammenfassung, Pro und Contra, Widersprüchen, offenen Fragen, Quellen, Version und Hinweis auf mögliche Veraltung. Sie bleibt beratend und anfechtbar.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-021",
    path: "/abstimmungen",
    title: "Abstimmungen in einer getrennten Vertrauensgrenze",
    eyebrow: "WS-03 · nicht aktiviert",
    lead: "Die öffentliche Seite erklärt das Zielmodell. Sie enthält keinen Stimmzettel und überträgt keine Stimme.",
    status: "not_activated",
    pack: "PACK-15 / PACK-16 / PACK-17",
    prerequisites:
      "Rechts-, Sicherheits-, Infrastruktur- und Autoritätsfreigaben",
    kind: "voting",
    sections: [
      {
        title: "Getrennter Voting Client",
        text: "Eigener Origin, keine gemeinsamen Cookies, kein gemeinsamer LocalStorage oder IndexedDB, keine gemeinsame Identitätssitzung, keine Analytics und kein Fingerprinting.",
      },
      {
        title: "Minimierter Handoff",
        text: "Ein einmaliges, zweckgebundenes Übergabeartefakt enthält keine dauerhafte Mitgliedskennung. Der Rückweg enthält keine Stimmzetteldaten; Zwischenauszählungen sind ausgeschlossen.",
      },
      {
        title: "Mobil",
        text: "Eine mobile Anwendung öffnet den Voting Client im Systembrowser, niemals in einer eingebetteten WebView.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-022",
    path: "/ki-assistenz",
    title: "KI als beratendes Werkzeug",
    eyebrow: "Kein automatischer politischer Entscheider",
    lead: "KI-Unterstützung soll Material strukturieren und Risiken sichtbar machen. Sie entscheidet weder über politische Annahme noch über rechtliche Zulässigkeit.",
    status: "specified",
    pack: "PACK-18 / PACK-32",
    prerequisites: "Snapshot-, Quellen-, Offenlegungs- und Anfechtungsregeln",
    kind: "initiative",
    sections: [
      {
        title: "Nachprüfbarer Umfang",
        text: "Jede Analyse nennt Datenstand, erfasste Quellen und Grenzen. Änderungen am Gegenstand können die Analyse veralten lassen.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-023",
    path: "/buergerbuero",
    title: "Künftiges Bürgerbüro",
    eyebrow: "WS-05 · No-Wrong-Door Caseflow geplant",
    lead: "Bürgeranliegen sollen später über ein eigenes Portal angenommen, begründet weitergeleitet und mit datensparsamen Statusinformationen versehen werden.",
    status: "planned",
    pack: "PACK-33",
    prerequisites:
      "PACK-23 und PACK-29 über die PACK-33 Abhängigkeitskette; WS-05 Implementierung",
    kind: "citizen-office",
    sections: [
      {
        title: "Geplanter Fallweg",
        text: "Eingangsbestätigung, zuständige Stelle, Routinggrund, Übergabeverlauf, Frist- oder Eskalationshinweise und Datenschutzklasse werden getrennt modelliert.",
      },
      {
        title: "Heute nicht verfügbar",
        text: "Es gibt keinen aktiven Antrag, Fallstatus, SLA und keine Zusage rechtlicher Wirkung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-024",
    path: "/abgeordnetentisch",
    title: "Offener Abgeordnetentisch",
    eyebrow: "Öffentliche Erklärung · geschütztes Fallbüro bleibt getrennt",
    lead: "Der öffentliche Bereich soll später bereinigte Informationen über parlamentarische Arbeit zeigen. Bürgerinnen und Bürger greifen nicht direkt auf WS-04 zu.",
    status: "planned",
    pack: "PACK-29",
    prerequisites: "WS-04, WS-05 und freigegebene WS-10 Projektionen",
    kind: "representatives",
    sections: [
      {
        title: "Freies Mandat",
        text: "Öffentliche Rückmeldungen oder aggregierte Indikatoren sind nicht bindend. Sie lösen keine automatische Sanktion, Abberufung oder Mandatsentziehung aus.",
      },
      {
        title: "Veröffentlichung statt Aktenzugriff",
        text: "Korrespondenz und Fallarbeit bleiben geschützt. Öffentlich erscheinen nur geprüfte, minimierte und freigegebene Zusammenfassungen.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-025",
    path: "/finanzen",
    title: "Finanztransparenz – Zielbild",
    eyebrow: "PACK-10 Spezifikation · kein aktiver Finanzdienst",
    lead: "Vorgesehen sind ein Party-Finance Ledger, Beiträge, Sponsoring, Rechenschaftsbericht, unabhängige Finanzprüfung und öffentliche Projektionen.",
    status: "specified",
    pack: "PACK-10",
    prerequisites:
      "Runtime-Implementierung, Finanzprüfung und Publikationsfreigabe",
    kind: "finance",
    sections: [
      {
        title: "Derzeit nicht aktiv",
        text: "finance-service ist nicht aktiv. Es gibt kein öffentliches Live-Ledger und auf dieser Seite keinen Spenden-, Zahlungs- oder Meldeablauf.",
      },
      {
        title: "Spätere Veröffentlichung",
        text: "Öffentliche Daten kommen aus kontrollierten Publikationsprojektionen. Veröffentlichung bedeutet nicht automatisch externe rechtliche Anerkennung.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-026",
    path: "/versammlungen",
    title: "Versammlungen und Online-Teilnahme",
    eyebrow: "Konzept · nicht rechtlich aktiviert",
    lead: "Ein künftiger Ablauf trennt Einberufung, Anwesenheit, Quorum, Rederecht, Anträge, Abstimmungsberechtigung und Protokoll.",
    status: "legally_blocked",
    pack: "PACK-21",
    prerequisites:
      "Rechts- und Sicherheitsaktivierung; zuständige Satzungsgrundlage",
    kind: "standard",
    sections: [
      {
        title: "Keine Gleichsetzung",
        text: "Technische Anwesenheit beweist weder Quorum noch Stimmberechtigung. Eine Online-Oberfläche macht eine Versammlung nicht automatisch rechtlich wirksam.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-027",
    path: "/kandidatur",
    title: "Kandidatur und Nominierung",
    eyebrow: "Erklärmodell",
    lead: "Interesse, Bewerbung, Nominierung, Eignungsprüfung, Zulassung, Wahlzulassung, Ablehnung, Rechtsbehelf und Rücknahme sind getrennte Schritte.",
    status: "planned",
    pack: "PACK-20",
    prerequisites:
      "Zuständiges Verfahren, Fristen, Datenschutz und Rechtsprüfung",
    kind: "standard",
    sections: [
      {
        title: "Keine öffentliche Bewerbung",
        text: "Diese Seite erhebt keine Kandidaturdaten und zeigt keine vermeintlich autoritative Kandidatenliste.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-028",
    path: "/compliance",
    title: "Compliance und Rechtsprozesse",
    eyebrow: "PACK-09 Backend PASS · WS-07 Oberfläche fehlt",
    lead: "PACK-09 stellt geprüfte Backend-Grundlagen bereit. Eine öffentliche Seite ist jedoch kein aktiver Compliance-Fall, kein Legal Hold und kein Zustellworkflow.",
    status: "foundation_available",
    pack: "PACK-09 / WS-07",
    prerequisites:
      "WS-07 Implementierung, Rollenmodell und rechtliche Aktivierung",
    kind: "standard",
    sections: [
      {
        title: "Aktueller Stand",
        text: "PACK-09 ist FINAL PASS. Die fehlende Fachoberfläche wird dadurch nicht vorgetäuscht oder ersetzt.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-029",
    path: "/rechtsgovernance",
    title: "Rechts- und Verfassungsgovernance",
    eyebrow: "Institutionelles Zielbild",
    lead: "Unabhängigkeit, Bestellung, Befangenheit, Zuständigkeit und Wirkung von Stellungnahmen müssen vor Aktivierung eindeutig geregelt sein.",
    status: "planned",
    pack: "PACK-31",
    prerequisites:
      "Rechtliche Prüfung und formelle institutionelle Einrichtung",
    kind: "standard",
    sections: [
      {
        title: "Beratung und Bindung",
        text: "Eine Stellungnahme ist nur dann bindend, wenn eine gültige Rechts- oder Satzungsgrundlage dies ausdrücklich vorsieht. Bis dahin wird keine solche Wirkung behauptet.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-030",
    path: "/fortschritt",
    title: "Entscheidungen und Programmfortschritt",
    eyebrow: "Öffentliche Board-Prototypen · read-only",
    lead: "Zwei künftige Boards sollen angenommene Initiativen und politische Programmzusagen anhand von Verantwortung, Fristen, Nachweisen und Abweichungen verfolgen.",
    status: "planned",
    pack: "PACK-32 / PACK-33",
    prerequisites:
      "Autoritative Quellen, fachliche Workspaces und Publikationsprojektionen",
    kind: "boards",
    sections: [
      {
        title: "Accepted Initiatives Board",
        text: "Geplant sind angenommene Entscheidung, verantwortliches Organ, Maßnahmenplan, Meilensteine, Fristen, Status, Ergebnisse, Verzögerungen, Hindernisse, Nachweise, letzte Aktualisierung und öffentliche Änderungshistorie.",
      },
      {
        title: "Program Progress Board",
        text: "Programmzusage, verantwortliches politisches Organ, verbundene Initiativen, gesetzgeberische oder öffentliche Aktivitäten, Fortschritt, Hindernisse, Nachweise und Abweichungen zwischen Programm und Handeln sollen nachvollziehbar werden.",
      },
    ],
  },
  {
    id: "FRONT01-PAGE-031",
    path: "/status",
    title: "Reifegrad und Roadmap",
    eyebrow: "Was vorhanden ist – und was nicht",
    lead: "Jede Fähigkeit erhält einen kontrollierten Status. Ein bestandener Architektur- oder Backend-PACK aktiviert nicht automatisch einen öffentlichen Dienst.",
    status: "informational",
    pack: "FRONT-01",
    prerequisites: "Evidenz je Fähigkeit",
    kind: "status",
    sections: [
      {
        title: "Bestätigte Grundlage",
        text: "FRONT-00 FOUNDATION 0.1.6 ist FINAL PASS. PACK-01 bis PACK-09 sind FINAL PASS. Repository 0.9.0 und Canon 0.7.0 bleiben unverändert.",
      },
      {
        title: "Roadmap",
        text: "PACK-10 befindet sich auf Spezifikations-/Canon-Stufe. PACK-19 bis PACK-35 und Domains 51–58 sind geplant oder vorgeschlagen, soweit keine gesonderte Implementierung belegt ist.",
      },
    ],
  },
];

const front02PublicPages: readonly PublicPage[] = [
  {
    id: "FRONT02-PAGE-001",
    path: "/aktuelles",
    title: "Aktuelles",
    eyebrow: "Freigegebene öffentliche Mitteilungen",
    lead: "Veröffentlichungen erscheinen hier erst nach der zuständigen Freigabe.",
    status: "planned",
    pack: "PACK-28 / WS-10",
    prerequisites: "Freigegebene Publikationsprojektion",
    kind: "standard",
    sections: [
      {
        title: "Illustrative öffentliche Mitteilung",
        text: "31. August 2026 · Information · Herausgegeben von der Redaktion. Beispielhafte, nicht autoritative Fixture mit Version 1.0 und sichtbarem Korrekturweg.",
      },
      {
        title: "Weitere Mitteilungen",
        text: "Die Liste ist begrenzt und paginiert. Nicht freigegebene Inhalte werden nicht dargestellt.",
      },
    ],
    en: {
      title: "News",
      eyebrow: "Approved public notices",
      lead: "Publications appear here only after responsible approval.",
      sections: [
        {
          title: "Illustrative public notice",
          text: "31 August 2026 · Information · Issued by the editorial role. This is a non-authoritative fixture, version 1.0, with a visible correction path.",
        },
        {
          title: "Further notices",
          text: "The list is bounded and paginated. Unapproved content is not displayed.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-002",
    path: "/presse",
    title: "Presse",
    eyebrow: "Pressezentrum · freigegebene Renditionen",
    lead: "Pressemitteilungen und Stellungnahmen werden versioniert veröffentlicht.",
    status: "planned",
    pack: "PACK-28 / WS-10",
    prerequisites: "Freigegebene Publikationsprojektion",
    kind: "standard",
    sections: [
      {
        title: "Illustrative Pressemitteilung",
        text: "31. August 2026 · Pressestelle · Version 1.0. Medienkontakt und freigegebener Download werden als Muster dargestellt.",
      },
      {
        title: "Korrekturen",
        text: "Eine spätere Ersetzung bleibt mit der ursprünglichen Rendition verknüpft.",
      },
    ],
    en: {
      title: "Press",
      eyebrow: "Press centre · approved renditions",
      lead: "Press releases and statements are published with versions.",
      sections: [
        {
          title: "Illustrative press release",
          text: "31 August 2026 · Press office · Version 1.0. Media contact and an approved download are shown as a fixture.",
        },
        {
          title: "Corrections",
          text: "A later replacement remains linked to the original rendition.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-003",
    path: "/termine",
    title: "Termine",
    eyebrow: "Öffentliche Veranstaltungen",
    lead: "Nur freigegebene öffentliche Termine gehören in diese Ansicht.",
    status: "planned",
    pack: "PACK-21 / PACK-28",
    prerequisites: "Freigegebene Veranstaltungsprojektion",
    kind: "standard",
    sections: [
      {
        title: "Illustrativer Termin",
        text: "12. September 2026 · Berlin · Öffentliche Informationsveranstaltung. Dies ist keine Anmeldung, Versammlung oder Abstimmung.",
      },
      {
        title: "Filter und Seiten",
        text: "Zeit, Ort und Thema werden später als begrenzte öffentliche Filter angeboten.",
      },
    ],
    en: {
      title: "Events",
      eyebrow: "Public events",
      lead: "Only approved public events belong on this view.",
      sections: [
        {
          title: "Illustrative event",
          text: "12 September 2026 · Berlin · Public information event. This is not registration, an assembly or a vote.",
        },
        {
          title: "Filters and pages",
          text: "Time, location and topic will later be available as bounded public filters.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-004",
    path: "/regionen",
    title: "Regionen",
    eyebrow: "Eine EPD²-Plattform · organisationsbezogen",
    lead: "Regionale Informationen werden im gemeinsamen Auftritt dargestellt, nicht als lokale Mini-Sites.",
    status: "specified",
    pack: "PACK-08 / PACK-28",
    prerequisites: "Freigegebene Organisationsprojektionen",
    kind: "standard",
    sections: [
      {
        title: "Region finden",
        text: "Illustrative Suche nach einem freigegebenen öffentlichen Organisationsbereich. Sie erstellt weder Mitgliedschaft noch Berechtigung.",
      },
      {
        title: "Landesverband Berlin",
        text: "Illustrative öffentliche Projektion mit Übersicht, Aktuelles, Termine, Initiativen, Personen, Wahlen, Dokumente & Transparenz und Kontakt.",
      },
    ],
    en: {
      title: "Regions",
      eyebrow: "One EPD² platform · organization-scoped",
      lead: "Regional information is presented in the common platform, not as local mini-sites.",
      sections: [
        {
          title: "Find a region",
          text: "Illustrative search for an approved public organization scope. It creates neither membership nor authority.",
        },
        {
          title: "Berlin regional association",
          text: "Illustrative public projection with overview, news, events, initiatives, people, elections, documents & transparency and contact.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-005",
    path: "/personen",
    title: "Personen",
    eyebrow: "Öffentliche Rollen und Mandate",
    lead: "Dies ist keine Mitgliederdatenbank und kein universelles Personenprofil.",
    status: "planned",
    pack: "PACK-28 / WS-10",
    prerequisites: "Freigegebene öffentliche Personenrenditionen",
    kind: "standard",
    sections: [
      {
        title: "Illustrative öffentliche Rolle",
        text: "Eine später freigegebene Persona zeigt nur die veröffentlichte Rolle, ihre Quelle und Version – keine Mitgliederdaten.",
      },
    ],
    en: {
      title: "People",
      eyebrow: "Public roles and mandates",
      lead: "This is not a membership directory or universal person profile.",
      sections: [
        {
          title: "Illustrative public role",
          text: "A future approved persona displays only the published role, its source and version – never membership data.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-006",
    path: "/wahlen",
    title: "Wahlen",
    eyebrow: "Öffentliche Information · keine Stimmabgabe",
    lead: "Diese Seite informiert. Die geheime Stimmabgabe bleibt ausschließlich im isolierten WS-03.",
    status: "not_activated",
    pack: "PACK-15 / PACK-16 / PACK-17",
    prerequisites:
      "Rechts-, Sicherheits-, Infrastruktur- und Kryptografie-Freigaben",
    kind: "voting",
    sections: [
      {
        title: "Illustrative Wahlinformation",
        text: "Eine zukünftige öffentliche Kampagnen- oder Wahlinformation ist keine Wahlurne und prüft keine Stimmberechtigung.",
      },
    ],
    en: {
      title: "Elections",
      eyebrow: "Public information · no ballot casting",
      lead: "This page informs. Secret ballot casting remains exclusively in isolated WS-03.",
      sections: [
        {
          title: "Illustrative election information",
          text: "A future public campaign or election notice is not a ballot box and does not check voting eligibility.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-007",
    path: "/hilfe",
    title: "Hilfe",
    eyebrow: "Unterstützung in Ebenen",
    lead: "Hilfe beginnt mit verständlicher Information und führt bei geschützten Vorgängen zum zuständigen Workspace.",
    status: "informational",
    pack: "FRONT-02 / PACK-18",
    prerequisites: "Versionierte Hilfeinhalte und Kontaktwege",
    kind: "standard",
    sections: [
      {
        title: "Öffentliche Hilfe",
        text: "Status, Grenzen und sichere nächste Schritte werden erklärt.",
      },
      {
        title: "Menschliche Unterstützung",
        text: "Ein Chatbot ist nicht der einzige Hilfsweg. Für nicht verfügbare Funktionen wird ein Kontakt- oder geregelter Offline-Weg genannt.",
      },
    ],
    en: {
      title: "Help",
      eyebrow: "Layered assistance",
      lead: "Help begins with clear information and directs protected matters to their owning workspace.",
      sections: [
        {
          title: "Public help",
          text: "Status, limits and safe next steps are explained.",
        },
        {
          title: "Human support",
          text: "A chatbot is not the only help channel. Unavailable functions name contact or a governed offline route.",
        },
      ],
    },
  },
  {
    id: "FRONT02-PAGE-008",
    path: "/suche",
    title: "Suche",
    eyebrow: "Nur freigegebene öffentliche Inhalte",
    lead: "Die öffentliche Suche ist begrenzt: Findbar ist nur, was für denselben öffentlichen Nutzer geöffnet werden darf.",
    status: "planned",
    pack: "PACK-12 / PACK-13 / WS-10",
    prerequisites: "Freigegebener öffentlicher Index",
    kind: "standard",
    sections: [
      {
        title: "Öffentlicher Fixture-Index",
        text: "Aktuelles, Presse und Termine sind illustrative, offene Treffer. Ein geschützter Testdatensatz ist absichtlich nicht auffindbar.",
      },
      {
        title: "Keine Ergebnisse",
        text: "Unbekannte Eingaben werden nicht zu erfundenen öffentlichen Datensätzen.",
      },
    ],
    en: {
      title: "Search",
      eyebrow: "Approved public content only",
      lead: "Public search is bounded: only content openable by the same public user is findable.",
      sections: [
        {
          title: "Public fixture index",
          text: "News, press and events are illustrative open results. A protected test record is intentionally not findable.",
        },
        {
          title: "No results",
          text: "Unknown input is not turned into invented public records.",
        },
      ],
    },
  },
];

export const allPublicPages: readonly PublicPage[] = [
  ...publicPages,
  ...front02PublicPages,
];

export const publicPageByPath = new Map(
  allPublicPages.map((page) => [page.path, page]),
);

export const topNavigation = [
  { href: "/ueber-uns", label: "Über uns" },
  { href: "/ziele", label: "Ziele" },
  { href: "/programm", label: "Programm" },
  { href: "/mitmachen", label: "Mitmachen" },
  { href: "/organisation", label: "Organisation" },
  { href: "/transparenz", label: "Transparenz" },
  { href: "/technologie", label: "Technologie" },
  { href: "/status", label: "Status" },
] as const;

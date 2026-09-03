export type PublicFixtureDetail = {
  path: string;
  family:
    "aktuelles" | "presse" | "termine" | "regionen" | "personen" | "wahlen";
  title: string;
  summary: string;
  date: string;
  category: string;
  issuer: string;
  correction: string;
  provenance: string;
};

/** Deliberately small, non-authoritative public projections for FRONT-02 tests. */
export const publicFixtureDetails: readonly PublicFixtureDetail[] = [
  {
    path: "/aktuelles/aufbau",
    family: "aktuelles",
    title: "Aufbau der öffentlichen Projektion",
    summary:
      "Illustrative Meldung über die nachvollziehbare Veröffentlichung von Projektständen.",
    date: "2026-08-30",
    category: "Projektstand",
    issuer: "EPD² Redaktion (Fixture)",
    correction: "Version 1 · Korrekturen werden sichtbar ersetzt",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
  {
    path: "/presse/stellungnahme",
    family: "presse",
    title: "Stellungnahme zum transparenten Aufbau",
    summary:
      "Illustrative Presseinformation ohne politische oder rechtliche Bindung.",
    date: "2026-08-30",
    category: "Presseinformation",
    issuer: "EPD² Presse (Fixture)",
    correction: "Version 1 · keine Freigabe behauptet",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
  {
    path: "/termine/berlin",
    family: "termine",
    title: "Offener Informationsabend Berlin",
    summary:
      "Illustrativer Termin; keine Anmeldung, keine Kontoerstellung und keine Berechtigungsprüfung.",
    date: "2026-09-15",
    category: "Termin",
    issuer: "Region Berlin (Fixture)",
    correction: "Version 1 · Änderungen werden nachvollziehbar markiert",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
  {
    path: "/regionen/berlin",
    family: "regionen",
    title: "Region Berlin",
    summary:
      "Illustrative regionale öffentliche Projektion innerhalb der gemeinsamen Plattform.",
    date: "2026-08-30",
    category: "Regionale Übersicht",
    issuer: "Region Berlin (Fixture)",
    correction: "Version 1 · Rollen und Inhalte vorbehaltlich Freigabe",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
  {
    path: "/personen/sprecherin",
    family: "personen",
    title: "Öffentliche Sprecherinnenrolle",
    summary:
      "Illustrative Rolle, keine Mitgliedsakte und kein universelles Personenprofil.",
    date: "2026-08-30",
    category: "Öffentliche Rolle",
    issuer: "Organisation (Fixture)",
    correction: "Version 1 · Rollenstand mit Quelle",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
  {
    path: "/wahlen/bundestag",
    family: "wahlen",
    title: "Wahlinformation Bundestag",
    summary:
      "Illustrative öffentliche Information. Keine Stimmabgabe oder Berechtigungsprüfung.",
    date: "2026-08-30",
    category: "Wahlinformation",
    issuer: "Wahlredaktion (Fixture)",
    correction: "Version 1 · kein aktivierter Wahlprozess",
    provenance: "Fixturequelle FRONT-02 · nicht autoritativ",
  },
];

export const publicFixtureByPath = new Map(
  publicFixtureDetails.map((detail) => [detail.path, detail]),
);

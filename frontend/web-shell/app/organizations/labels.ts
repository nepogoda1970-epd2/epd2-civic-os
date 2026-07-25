/**
 * German-authoritative / English-informational label pairs for the PACK-08
 * frontend vertical slice.
 *
 * German is the authoritative text throughout this vertical slice; English
 * is present only as an informational gloss (rendered smaller, marked with
 * `lang="en"`, never the sole text for any label). Every user-facing label
 * used by app/organizations/* is defined here in one place so the
 * German/English pairing stays consistent and easy to audit.
 */

export interface Bilingual {
  de: string;
  en: string;
}

export const LABELS = {
  organizationsHeading: { de: "Organisationen", en: "Organizations" },
  organizationsIntro: {
    de: "Nur lesende Übersicht auf Basis statischer Beispieldaten — keine echte Backend-Anbindung.",
    en: "Read-only overview backed by static sample data — no real backend connection.",
  },
  name: { de: "Name", en: "Name" },
  legalOperator: { de: "Rechtsträger", en: "Legal operator" },
  organizationType: { de: "Organisationstyp", en: "Organization type" },
  status: { de: "Status", en: "Status" },
  effectiveFrom: { de: "Gültig ab", en: "Effective from" },
  effectiveUntil: { de: "Gültig bis", en: "Effective until" },
  dissolvedAt: { de: "Aufgelöst am", en: "Dissolved at" },
  parentOrganization: {
    de: "Übergeordnete Organisation",
    en: "Parent organization",
  },
  successor: { de: "Rechtsnachfolger", en: "Successor" },
  details: { de: "Details", en: "Details" },
  asOfSelectorLabel: {
    de: "Stichtag (aktuell oder historisch)",
    en: "As-of date (current or historical)",
  },
  asOfSelectorHint: {
    de: "Wählen Sie einen Zeitpunkt, um den zu diesem Zeitpunkt gültigen Status zu sehen.",
    en: "Choose a point in time to see the status that was in effect then.",
  },
  currentStatusAsOf: {
    de: "Status zum gewählten Stichtag",
    en: "Status as of selected date",
  },
  relationsHeading: {
    de: "Organisationsbeziehungen",
    en: "Organizational relations",
  },
  relationsIntro: {
    de: "Typisierte Beziehungen (Hierarchie, Kontinuität, Kooperation) laut Kanon 19e.7.",
    en: "Typed relations (hierarchy, continuity, cooperation) per canon 19e.7.",
  },
  relationType: { de: "Beziehungstyp", en: "Relation type" },
  relationCategory: { de: "Kategorie", en: "Category" },
  source: { de: "Quelle", en: "Source" },
  target: { de: "Ziel", en: "Target" },
  validFrom: { de: "Gültig ab", en: "Valid from" },
  validUntil: { de: "Gültig bis", en: "Valid until" },
  noRelations: {
    de: "Keine Beziehungen vorhanden.",
    en: "No relations present.",
  },
  authoritiesHeading: {
    de: "Institutionelle Befugnisse",
    en: "Institutional authority assignments",
  },
  authoritiesIntro: {
    de: "Nur explizit zugewiesene Rollen laut Kanon 19e.15/19e.16 — keine abgeleiteten Befugnisse.",
    en: "Only explicitly assigned roles per canon 19e.15/19e.16 — no inferred authority.",
  },
  roleCode: { de: "Rolle", en: "Role" },
  subject: {
    de: "Zugewiesene Person (Referenz)",
    en: "Assigned subject (reference)",
  },
  proceduralAuthority: { de: "Verfahrensbefugnis", en: "Procedural authority" },
  dataAccess: { de: "Datenzugriff", en: "Data access" },
  yes: { de: "Ja", en: "Yes" },
  no: { de: "Nein", en: "No" },
  noAuthorities: {
    de: "Keine institutionellen Befugnisse in diesem Geltungsbereich.",
    en: "No institutional authority assignments in this scope.",
  },
  devConsoleHeading: {
    de: "Entwicklungs- und Testkonsole: Regionale Zugriffsprüfung",
    en: "Development test console: regional scope access check",
  },
  devConsoleBanner: {
    de: "Nur zu Entwicklungs- und Testzwecken. Keine echte Autorisierungsentscheidung, keine Backend-Anbindung, ausschließlich statische Beispieldaten.",
    en: "Development and testing use only. Not a real authorization decision, no backend connection, static sample data only.",
  },
  devConsoleIntro: {
    de: "Simuliert die Standard-verweigern-Logik aus Kanon 19e.12 anhand fest hinterlegter Beispiel-Berechtigungen.",
    en: "Simulates the default-deny logic from canon 19e.12 against fixed sample grants.",
  },
  subjectLabel: {
    de: "Handelnde Person (Beispiel-Referenz)",
    en: "Acting subject (sample reference)",
  },
  scopeLabel: {
    de: "Geltungsbereich (Organisation)",
    en: "Scope (organization)",
  },
  actionLabel: { de: "Aktion", en: "Action" },
  asOfLabel: { de: "Stichtag", en: "As-of date" },
  runCheck: { de: "Prüfung ausführen", en: "Run check" },
  resultAllowed: { de: "Zugriff erlaubt", en: "Access allowed" },
  resultDenied: { de: "Zugriff verweigert", en: "Access denied" },
  reasonCode: { de: "Begründungscode", en: "Reason code" },
  accessMode: { de: "Zugriffsmodus", en: "Access mode" },
  backToList: { de: "Zurück zur Übersicht", en: "Back to overview" },
  skipToMain: { de: "Zum Hauptinhalt springen", en: "Skip to main content" },
} as const satisfies Record<string, Bilingual>;

export const STATUS_LABELS: Record<string, Bilingual> = {
  draft: { de: "Entwurf", en: "Draft" },
  active: { de: "Aktiv", en: "Active" },
  restricted: { de: "Eingeschränkt", en: "Restricted" },
  archived: { de: "Archiviert", en: "Archived" },
};

export const RELATION_TYPE_LABELS: Record<string, Bilingual> = {
  parent_of: { de: "übergeordnet von", en: "parent of" },
  subordinate_to: { de: "untergeordnet gegenüber", en: "subordinate to" },
  affiliated_with: { de: "assoziiert mit", en: "affiliated with" },
  successor_of: { de: "Rechtsnachfolger von", en: "successor of" },
  merged_into: { de: "fusioniert in", en: "merged into" },
  split_from: { de: "abgespalten von", en: "split from" },
  temporary_supervision_by: {
    de: "zeitweise beaufsichtigt durch",
    en: "temporary supervision by",
  },
  operates_within: { de: "tätig innerhalb von", en: "operates within" },
  participates_in: { de: "beteiligt an", en: "participates in" },
};

export const RELATION_CATEGORY_LABELS: Record<string, Bilingual> = {
  hierarchy: { de: "Hierarchie", en: "hierarchy" },
  continuity: { de: "Kontinuität", en: "continuity" },
  cooperation: { de: "Kooperation", en: "cooperation" },
};

export const ROLE_LABELS: Record<string, Bilingual> = {
  dpo: { de: "Datenschutzbeauftragte:r", en: "Data Protection Officer" },
  election_board_member: {
    de: "Wahlvorstandsmitglied",
    en: "Election board member",
  },
  election_officer: { de: "Wahlleiter:in", en: "Election officer" },
  independent_auditor: {
    de: "Unabhängige:r Prüfer:in",
    en: "Independent auditor",
  },
  finance_auditor: { de: "Finanzprüfer:in", en: "Finance auditor" },
  party_arbitrator: { de: "Parteischiedsrichter:in", en: "Party arbitrator" },
  organizational_administrator: {
    de: "Organisationsverwalter:in",
    en: "Organizational administrator",
  },
};

export const ACCESS_MODE_LABELS: Record<string, Bilingual> = {
  exact_scope: { de: "exakter Geltungsbereich", en: "exact scope" },
  ancestor_scope: {
    de: "übergeordneter Geltungsbereich",
    en: "ancestor scope",
  },
  descendant_scope: {
    de: "untergeordneter Geltungsbereich",
    en: "descendant scope",
  },
  delegated_cross_scope: {
    de: "delegierter bereichsübergreifender Zugriff",
    en: "delegated cross-scope",
  },
  temporary_supervision: {
    de: "zeitweise Aufsicht",
    en: "temporary supervision",
  },
  institutional_oversight_without_data_access: {
    de: "institutionelle Aufsicht ohne Datenzugriff",
    en: "institutional oversight without data access",
  },
};

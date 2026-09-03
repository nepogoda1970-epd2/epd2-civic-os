/**
 * German is the authoritative interface terminology for WS-03.
 *
 * The four canonical page titles are exact and are asserted by tests.  English
 * is a translation layer only: changing language changes no route authority, no
 * election context, no eligibility, no ballot semantics, no legal effect and no
 * cast semantics, and no language preference is persisted anywhere.
 */

export const CONTENT_VERSION = "F04-DE-1.0.0";

export const WS03_CONTENT = Object.freeze({
  workspace: "Abstimmungsbereich",
  boundaryNotice:
    "Sie befinden sich in einem getrennten Bereich. Es besteht hier keine Anmeldung und keine Verbindung zu Ihrem Mitgliedskonto.",
  candidateNotice:
    "Prototyp im Aufbau. Diese Oberfläche ist nicht freigegeben, nicht zertifiziert und rechtlich nicht aktiviert. Es findet keine gültige Abstimmung statt.",

  credential: Object.freeze({
    title: "Stimmberechtigung übernehmen",
    lead: "Hier wird eine einmalige, zweckgebundene Übergabe aus dem Mitgliederbereich entgegengenommen. Es werden keine Angaben zu Ihrer Person übernommen.",
    whatHappens: "Was hier geschieht",
    whatHappensBody:
      "Die Übergabe gilt einmalig, nur für diesen Bereich und nur für kurze Zeit. Sie erzeugt keine Anmeldung, keinen wiederverwendbaren Zugang und keine Kennung, die Sie später wiedererkennbar macht.",
    unavailableTitle: "Übernahme derzeit nicht möglich",
    channelViolationTitle: "Ungültiger Übergabeweg",
    channelViolationBody:
      "Ein Zugangswert darf nicht über die Adresszeile übergeben werden. Der Wert wurde nicht verwendet, nicht gespeichert und nicht weitergegeben.",
    noContextTitle: "Keine gültige Stimmberechtigung",
    noContextBody:
      "Für diesen Bereich liegt keine gültige, zweckgebundene Übergabe vor. Ein direkter Aufruf begründet keine Berechtigung.",
  }),

  ballot: Object.freeze({
    title: "Stimmzettel",
    lead: "Markieren Sie Ihre Auswahl. Ihre Auswahl bleibt bis zur Prüfung nur in diesem Fenster und wird nicht gespeichert.",
    selectionKept:
      "Ihre Auswahl wird nicht dauerhaft gespeichert. Wenn Sie die Seite neu laden, beginnen Sie erneut.",
    limitOne: "Höchstens eine Auswahl",
    limitMany: "Höchstens {n} Auswahlmöglichkeiten",
    selectedCount: "Ausgewählt: {n} von höchstens {limit}",
    clearContest: "Auswahl in dieser Frage zurücksetzen",
    blankAllowed:
      "Sie können eine Frage auch unbeantwortet lassen. Das ist eine zulässige Entscheidung.",
    toReview: "Auswahl prüfen",
    unavailableTitle: "Kein Stimmzettel verfügbar",
  }),

  review: Object.freeze({
    title: "Stimme prüfen",
    lead: "Prüfen Sie Ihre Auswahl. Es wurde noch nichts abgegeben und noch nichts gezählt.",
    yourSelection: "Ihre Auswahl",
    blank: "Keine Auswahl",
    back: "Zurück zum Stimmzettel",
    cancel: "Vorgang abbrechen",
    consequential: "Verbindlicher Schritt",
    consequentialBody:
      "Die endgültige Abgabe ist nicht umkehrbar. Sie können bis dahin zurückgehen oder abbrechen.",
    castAction: "Stimme endgültig abgeben",
    localCheckAction: "Auswahl auf diesem Gerät prüfen",
    localCheckExplanation:
      "Eine Prüfung auf diesem Gerät sendet nichts, veröffentlicht nichts und verbraucht Ihre Stimmberechtigung nicht. Sie ist beliebig oft möglich.",
    publicChallengeAction: "Öffentlichen Prüfnachweis erzeugen",
    publicChallengeExplanation:
      "Ein öffentlicher Prüfnachweis wird veröffentlicht und ausdrücklich nicht gezählt. Er ist einmal möglich und schließt eine spätere endgültige Abgabe nicht aus.",
    exclusive:
      "Endgültige Abgabe und öffentlicher Prüfnachweis sind unterschiedliche Vorgänge mit unterschiedlichen Folgen.",
    cancelledTitle: "Vorgang abgebrochen",
    cancelledBody:
      "Es wurde nichts abgegeben und nichts gezählt. Ihre Stimmberechtigung ist unverändert.",
  }),

  receipt: Object.freeze({
    title: "Stimmabgabe verifizieren",
    lead: "Hier kann geprüft werden, ob ein Nachweis in der Veröffentlichung erfasst ist. Der Nachweis zeigt niemals Ihre Auswahl.",
    codeLabel: "Nachweiscode",
    codeHint:
      "Der Code wird in Gruppen dargestellt. Groß- und Kleinschreibung spielt keine Rolle.",
    codeInvalid: "Der eingegebene Nachweiscode hat nicht die erwartete Form.",
    check: "Veröffentlichung prüfen",
    neverShows: "Was ein Nachweis nicht enthält",
    neverShowsBody:
      "Ein Nachweis enthält weder Ihre Auswahl noch Angaben zu Ihrer Person, weder einen Platz in einer Reihenfolge noch eine Anzahl.",
    doNotShare:
      "Ein Nachweis belegt keine Auswahl. Bewahren Sie ihn für sich; eine Weitergabe ist nicht vorgesehen und nicht erforderlich.",
    unavailableTitle: "Prüfung derzeit nicht verfügbar",
    notFoundTitle: "Kein Eintrag zu diesem Code",
  }),

  states: Object.freeze({
    loading: "Wird geladen",
    committedYes: "Es wurde etwas verbindlich erfasst.",
    committedNo: "Es wurde nichts abgegeben und nichts gezählt.",
    committedUnknown:
      "Ob etwas erfasst wurde, ist derzeit nicht feststellbar. Es wird nichts erneut gesendet.",
    entitlementIntact:
      "Ihre Stimmberechtigung gilt nach derzeitigem Stand weiter.",
    entitlementUnknown:
      "Ob Ihre Stimmberechtigung weiter gilt, ist derzeit nicht feststellbar.",
    nextStep: "Nächster sicherer Schritt",
    uncertainTitle: "Übermittlung ohne Rückmeldung",
    uncertainBody:
      "Die Übermittlung wurde begonnen, eine Rückmeldung liegt nicht vor. Es wird nichts automatisch erneut gesendet.",
  }),

  assistance: Object.freeze({
    title: "Unterstützung",
    modeLabel: "Unterstützungsmodus",
    modeOn: "Unterstützungsmodus aktiv",
    modeOff: "Unterstützungsmodus aus",
    boundary:
      "Unterstützung erklärt den Aufbau und die Bedienung der Seite. Eine unterstützende Person kann Ihre Auswahl weder sehen noch treffen, weder ändern noch bestätigen.",
    keyboard:
      "Alle Schritte sind vollständig mit der Tastatur bedienbar. Mit der Tabulatortaste wechseln Sie zwischen den Bedienelementen, mit der Leertaste treffen Sie eine Auswahl.",
  }),

  fallback: Object.freeze({
    title: "Ersatzweg",
    body: "Wenn dieser Weg nicht zur Verfügung steht, wenden Sie sich schriftlich an die zuständige Stelle. Der Ersatzweg ist unabhängig von dieser Oberfläche.",
  }),

  noTally:
    "In diesem Bereich werden keine Zwischenstände, keine Verteilungen und keine Beteiligungszahlen dargestellt.",
} as const);

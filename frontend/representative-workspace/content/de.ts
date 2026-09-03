/**
 * German is the authoritative interface terminology for WS-04.
 *
 * English is a translation layer only: changing language changes no route
 * authority, no mandate scope, no authorization outcome, no case state, no
 * publication state and no legal effect. `policies/language.ts` asserts that,
 * and no language preference reaches any persistent store beyond the declared
 * UI-preference purpose.
 *
 * Two tone rules govern every string here, and both come from what this
 * workspace is:
 *
 *  1. Nothing may read as an accomplished act. A composition that could not be
 *     transmitted is described as not transmitted, and where an obligation
 *     remains open the text says so plainly.
 *  2. A refusal about a protected resource must read identically whether the
 *     resource is absent, out of scope, or restricted.
 */

export const CONTENT_VERSION = "F05-DE-1.0.0";

export const WS04_CONTENT = Object.freeze({
  workspace: "Mandatsbereich",
  boundaryNotice:
    "Getrennter Arbeitsbereich für Mandatsarbeit. Es besteht kein systemweiter Verwaltungszugriff und kein Zugang zum Abstimmungsbereich.",
  candidateNotice:
    "Prototyp im Aufbau. Diese Oberfläche ist nicht freigegeben, nicht zertifiziert und rechtlich nicht aktiviert. Es werden keine echten Vorgänge bearbeitet.",
  noRuntimeNotice:
    "Für diesen Arbeitsbereich existiert derzeit keine freigegebene Laufzeit. Alle Netzfunktionen sind gesperrt; die Oberfläche zeigt den sicheren Zustand.",

  nav: Object.freeze({
    label: "Bereiche des Mandats",
    home: "Übersicht",
    desk: "Bürgeranliegen",
    positions: "Positionen",
    deviations: "Abweichungen",
    declarations: "Erklärungen",
    publication: "Veröffentlichungsvorschläge",
    conflicts: "Zugriffsbeschränkungen",
  }),

  scope: Object.freeze({
    label: "Mandatsbezug",
    none: "Kein Mandat aufgelöst",
    singleOnly:
      "Dieser Arbeitsbereich zeigt ausschließlich Daten genau eines Mandats. Eine mandatsübergreifende Ansicht ist nicht vorgesehen.",
    authorityActive: "Befugnis aktiv",
    authorityInactive: "Befugnis nicht aktiv",
  }),

  home: Object.freeze({
    title: "Übersicht",
    lead: "Dieser Bereich zeigt nur, was für Ihr Mandat freigegeben und belegbar ist. Nicht verfügbare Funktionen werden als nicht verfügbar dargestellt und nicht simuliert.",
    identity: "Mandat",
    actionable: "Offene Punkte",
    queueSummary: "Bürgeranliegen",
    pendingDeclarations: "Offene Erklärungen",
    pendingWork: "Positionen und Abweichungen",
    proposals: "Veröffentlichungsvorschläge",
    alerts: "Hinweise, die Handlung erfordern",
    nothingActionable:
      "Es sind keine belegbaren offenen Punkte abrufbar, weil die zugehörigen Dienste nicht verfügbar sind. Das ist keine Aussage darüber, dass nichts offen ist.",
    capabilitySummary:
      "Von {total} Funktionen dieses Arbeitsbereichs sind {blocked} durch fehlende Abhängigkeiten gesperrt und {executable} ohne Netzabhängigkeit nutzbar.",
  }),

  desk: Object.freeze({
    title: "Bürgeranliegen",
    lead: "Eingang und Einordnung von Anliegen, die diesem Mandat zugeordnet sind.",
    states: Object.freeze({
      new: "neu",
      assigned: "zugewiesen",
      triaged: "eingeordnet",
      awaiting_response: "wartet auf Rückmeldung",
      closed: "abgeschlossen",
      archived: "archiviert",
      unavailable: "nicht feststellbar",
    }),
    columnReference: "Zeichen",
    columnSubject: "Gegenstand",
    columnState: "Stand",
    columnReceived: "Eingang",
    columnAssignee: "Bearbeitung",
    unassigned: "nicht zugewiesen",
    restricted: "Zugriff eingeschränkt",
    empty:
      "Es kann keine Liste angezeigt werden. Eine leere Liste würde behaupten, dass keine Anliegen vorliegen.",
    unavailableTitle: "Vorgangsliste nicht abrufbar",
    detailTitle: "Vorgang",
    detailUnavailableTitle: "Vorgang nicht abrufbar",
    resolving: "Vorgang wird geprüft.",
    confidentialNotice:
      "Inhalte von Anliegen sind vertraulich. Sie werden nicht im Browser gespeichert, nicht in der Adresszeile geführt und nicht ausgewertet.",
    transitionBlocked:
      "Änderungen am Stand eines Vorgangs sind derzeit nicht möglich. Es wurde nichts geändert.",
    uncertainTitle: "Ergebnis nicht feststellbar",
    versionLabel: "Fassung",
    provenanceLabel: "Herkunft",
  }),

  positions: Object.freeze({
    title: "Positionen",
    lead: "Positionen des Mandats. Ein Entwurf ist keine Veröffentlichung.",
    states: Object.freeze({
      draft: "Entwurf",
      submitted_internal: "intern eingereicht",
      proposed_for_publication: "zur Veröffentlichung vorgeschlagen",
      public_approved_rendition: "freigegebene öffentliche Fassung",
      superseded: "ersetzt",
    }),
    draftNotSaved:
      "Dieser Entwurf wird nicht gespeichert. Er besteht nur in diesem Fenster und geht beim Neuladen verloren.",
    unavailableTitle: "Positionen nicht abrufbar",
    saveBlocked: "Entwürfe können derzeit nicht gespeichert werden.",
  }),

  deviations: Object.freeze({
    title: "Abweichungen",
    lead: "Erfasste Abweichungen von einer demokratisch getroffenen Entscheidung, mit Begründung und Herkunft.",
    issue: "Thema",
    position: "Standpunkt",
    referencedDecision: "Bezug zur Entscheidung",
    explanation: "Begründung",
    doesNotAlter:
      "Eine erfasste Abweichung ändert die referenzierte Entscheidung nicht. Sie dokumentiert einen Unterschied.",
    referenceUnverified:
      "Bezug ungeprüft: die Entscheidung kann derzeit nicht aufgelöst werden.",
    unavailableTitle: "Abweichungen nicht abrufbar",
    recordBlocked:
      "Abweichungen können derzeit nicht erfasst werden. Es wurde nichts aufgezeichnet.",
    supersededBy: "ersetzt durch",
  }),

  declarations: Object.freeze({
    title: "Erklärungen",
    lead: "Termine, Interessenerklärungen und Offenlegungen.",
    kinds: Object.freeze({
      meeting: "Termin",
      declaration: "Erklärung",
      disclosure: "Offenlegung",
    }),
    subject: "Gegenstand",
    occurredAt: "Datum",
    counterparty: "Gegenüber",
    summary: "Zusammenfassung",
    obligationOpen:
      "Diese Erklärung wurde nicht übermittelt. Die Meldepflicht bleibt offen und ist auf dem geregelten Weg zu erfüllen.",
    unavailableTitle: "Erklärungen nicht abrufbar",
    submitBlocked: "Erklärungen können derzeit nicht übermittelt werden.",
  }),

  publication: Object.freeze({
    title: "Veröffentlichungsvorschläge",
    lead: "Dieser Arbeitsbereich kann eine Fassung zur Veröffentlichung vorschlagen. Über die Freigabe entscheidet die Veröffentlichungsstelle.",
    notAnApproval:
      "Vorschlag zur Veröffentlichung. Dies ist keine Veröffentlichung und keine Freigabe.",
    states: Object.freeze({
      draft: "Entwurf, nicht eingereicht",
      proposal_submitted: "Vorschlag eingereicht, nicht freigegeben",
      returned_for_correction: "Zur Überarbeitung zurückgegeben",
      approved_by_publication_authority:
        "Von der Veröffentlichungsstelle freigegeben",
      rejected: "Abgelehnt",
      superseded: "Ersetzt",
    }),
    decidedBy: "Entscheidende Stelle",
    stateUnknown:
      "Der Veröffentlichungsstand ist derzeit nicht feststellbar und wird nicht angenommen.",
    unavailableTitle: "Vorschläge nicht abrufbar",
    proposeBlocked:
      "Vorschläge zur Veröffentlichung können derzeit nicht eingereicht werden.",
    separationNotice:
      "Eine Freigabe ist in diesem Arbeitsbereich nicht vorgesehen und technisch nicht erreichbar.",
  }),

  conflicts: Object.freeze({
    title: "Zugriffsbeschränkungen",
    lead: "Beschränkungen wegen möglicher Interessenkonflikte werden von der zuständigen Stelle festgelegt.",
    noSelfClear:
      "Eine Beschränkung über die eigene Person kann in diesem Arbeitsbereich nicht aufgehoben werden.",
    unknownIsRestricted:
      "Solange Beschränkungen nicht prüfbar sind, bleibt der Zugriff gesperrt. Unbekannt bedeutet nicht aufgehoben.",
    unavailableTitle: "Beschränkungen nicht prüfbar",
    activeLabel: "aktiv",
    scopeLabel: "Betroffener Bereich",
  }),

  auth: Object.freeze({
    signedOut: "Nicht angemeldet",
    stepUpRequired: "Zusätzliche Authentisierung erforderlich",
    stepUpBody:
      "Für diesen Vorgang ist eine zusätzliche Authentisierung erforderlich. Sie ist derzeit nicht verfügbar.",
    sessionExpired: "Ihre Sitzung ist abgelaufen.",
    sessionRevoked: "Ihre Sitzung wurde beendet.",
    scopeChanged: "Ihr Mandatsbezug hat sich geändert.",
    authoritySuspended: "Ihre Mandatsbefugnis ist derzeit ausgesetzt.",
    authorityExpired: "Ihre Mandatsperiode ist beendet.",
    notPermitted: "Für diese Handlung fehlt die erforderliche Befugnis.",
    revalidationNotice:
      "Die Befugnis wird beim Absenden erneut serverseitig geprüft. Eine hier sichtbare Schaltfläche ist keine Berechtigung.",
  }),

  states: Object.freeze({
    committedYes: "Die Änderung wurde übernommen.",
    committedNo: "Es wurde nichts geändert.",
    committedUnknown: "Es ist nicht feststellbar, ob etwas geändert wurde.",
    commitStatus: "Stand der Änderung",
    nextStep: "Nächster sicherer Schritt",
    dependency: "Fehlende Abhängigkeit",
    notAudited:
      "Handlungen in diesem Arbeitsbereich werden derzeit von keiner freigegebenen Kontrollebene protokolliert.",
  }),

  search: Object.freeze({
    label: "Suche im Mandat",
    scopeNotice:
      "Die Suche gilt ausschließlich innerhalb Ihres Mandats. Eine mandatsübergreifende Suche ist nicht vorgesehen.",
    unavailable: "Die Suche ist derzeit nicht verfügbar.",
  }),

  fallback: Object.freeze({
    title: "Geregelter Weg",
    body: "Solange digitale Wege gesperrt sind, bleibt der geregelte Weg über die zuständige Stelle offen. Kein Anliegen entfällt dadurch, dass die Software unfertig ist.",
  }),

  degraded: Object.freeze({
    title: "Eingeschränkter Betrieb",
    intakePaused:
      "Der Eingang von Anliegen ist ausgesetzt. Bereits freigegebene öffentliche Positionen bleiben abrufbar.",
  }),

  votingBoundary: Object.freeze({
    title: "Kein Zugang zum Abstimmungsbereich",
    body: "Aus diesem Arbeitsbereich besteht kein Zugang zu Stimmzetteln, Stimmen, Zwischenständen oder Nachweisen. Diese Trennung ist Teil des Wahlgeheimnisses.",
  }),
} as const);

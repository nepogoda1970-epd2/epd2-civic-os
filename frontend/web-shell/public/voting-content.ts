/**
 * PACK-15 — authoritative German content for the voting trust boundary.
 *
 * German is the authoritative language for this content (content version
 * `P15-DE-1.0.0`). The sentences below are taken from
 * docs/packs/PACK-15/PACK-15-CONTENT-CATALOGUE-DE.md — §2, §4, §5, §6, §7,
 * §10 and the architecture-correction texts in §12. Where the catalogue
 * carries a runtime placeholder (`{context_name}`, `{expiry}`), the fixed
 * wording below states the same rule without the placeholder, because this
 * surface renders static sample data and never a resolved value.
 *
 * Two rules govern every text here: no text confirms, denies or implies a
 * ballot choice or an individual act of casting, and every refusal names a
 * reason, the responsible body and the next possible step.
 */

import type { ParticipationStateId } from "../foundation/voting-trust-policy";

export type ParticipationStateText = Readonly<{
  title: string;
  body: string;
  nextStep: string;
  note?: string;
}>;

export type NotOfferedRow = Readonly<{
  expectation: string;
  text: string;
}>;

const STATE_TEXTS = {
  eligibility_pending: {
    title: "Antrag eingegangen",
    body: "Ihr Antrag wurde aufgenommen. Sie erhalten eine Mitteilung, sobald die Prüfung abgeschlossen ist.",
    nextStep:
      "Sie müssen nichts weiter tun. Solange nicht entschieden wurde, können Sie den Antrag zurückziehen.",
  },
  eligibility_confirmed: {
    title: "Teilnahmeberechtigt",
    body: "Sie sind für diese Abstimmung teilnahmeberechtigt. Der Zugang zur Abstimmung kann innerhalb des Ausgabezeitraums abgerufen werden. Der Zugang wird nur einmal ausgegeben.",
    nextStep:
      "Teilnahmeberechtigt zu sein bedeutet noch nicht, Zugang zu haben. Der Zugang wird gesondert ausgegeben.",
  },
  review_required: {
    title: "In Prüfung",
    body: "Ihr Antrag wird durch eine zuständige Person geprüft. Dies ist keine Ablehnung. Sie erhalten eine Mitteilung, sobald entschieden wurde. Wird eine Prüfung nicht rechtzeitig abgeschlossen, wird der Vorgang eskaliert und nicht automatisch entschieden.",
    nextStep:
      "Reichen Sie die angeforderten Unterlagen ein. Es werden nur die Unterlagen erhoben, die für die genannte Regel erforderlich sind.",
  },
  eligibility_denied: {
    title: "Nicht teilnahmeberechtigt",
    body: "Ihr Antrag wurde abgelehnt. Die Mitteilung nennt Ihnen die geprüfte Regel und die zuständige Stelle.",
    nextStep:
      "Sie können gegen diese Entscheidung Widerspruch einlegen. Die Mitteilung nennt Ihnen die zuständige Stelle und die Frist.",
  },
  access_queued: {
    title: "Zugang wird vorbereitet",
    body: "Ihre Teilnahmeberechtigung wurde bestätigt. Der Zugang zur Abstimmung wird jetzt vorbereitet und in Kürze freigegeben. Sie erhalten eine Nachricht, sobald er verfügbar ist.",
    note: "Zugänge werden bewusst gesammelt und zeitlich versetzt freigegeben. Dadurch lässt sich aus dem Zeitpunkt nicht ableiten, wer einen Zugang erhalten hat. Diese Wartezeit ist kein Fehler und kein Rückstand.",
    nextStep:
      "Sie müssen nichts weiter tun. Eine Position in einer Warteschlange und eine verbleibende Wartezeit werden bewusst nicht angezeigt.",
  },
  access_available: {
    title: "Zugang verfügbar",
    body: "Ihr Zugang zur Abstimmung ist jetzt verfügbar. Sie können den Abstimmungsbereich innerhalb des genannten Zeitraums betreten.",
    nextStep:
      "Der Zugang gilt für eine Abstimmung und kann nur einmal verwendet werden.",
  },
  access_expired: {
    title: "Zugang abgelaufen",
    body: "Der Ausgabezeitraum für diese Abstimmung ist beendet. Ein abgelaufener Zugang wurde nicht verbraucht.",
    nextStep:
      "Melden Sie den Vorgang über „Problem mit dem Zugang melden“. Solange die Widerrufsfrist läuft, kann ein bestehender Zugang widerrufen und ein neuer ausgestellt werden.",
  },
  dispute_open: {
    title: "Widerspruch in Bearbeitung",
    body: "Ihr Widerspruch wurde aufgenommen. Die Prüfung erfolgt durch eine Stelle, die an der ursprünglichen Entscheidung nicht beteiligt war.",
    nextStep:
      "Sie erhalten die Entscheidung innerhalb der in der Mitteilung genannten Frist.",
  },
} as const satisfies Record<ParticipationStateId, ParticipationStateText>;

const NOT_OFFERED = [
  {
    expectation: "Zugang zusenden lassen",
    text: "Der Zugang wird ausschließlich im Abstimmungsbereich erstellt und dort sofort verwendet. Ein Versand ist nicht vorgesehen und wäre ein Sicherheitsrisiko.",
  },
  {
    expectation: "Zugang für später aufbewahren",
    text: "Der Zugang wird nicht gespeichert und nicht angezeigt. Erstellung und Verwendung erfolgen in einem Durchgang.",
  },
  {
    expectation: "Status „hat teilgenommen“ abrufen",
    text: "Ob eine bestimmte Person teilgenommen hat, wird nicht gespeichert und kann nicht abgefragt werden — weder durch Sie noch durch die Administration.",
  },
  {
    expectation: "Zwischenzahlen zur Beteiligung",
    text: "Vor dem Abschluss werden keine Beteiligungszahlen veröffentlicht, auch nicht als Fortschrittsanzeige.",
  },
] as const satisfies readonly NotOfferedRow[];

export const VOTING_CONTENT = {
  contentVersion: "P15-DE-1.0.0",

  contextSummary: {
    heading: "Teilnahme an Abstimmungen",
    intro:
      "Für jede Abstimmung wird gesondert geprüft, wer teilnahmeberechtigt ist. Die Prüfung erfolgt nach den Regeln, die für diese Abstimmung vor Beginn festgelegt und veröffentlicht wurden. Eine Prüfung ist keine Stimmabgabe.",
    separationNote:
      "Ihre Anmeldung, Ihre Mitgliedschaft und Ihre Teilnahmeberechtigung sind drei verschiedene Dinge. Aus der Teilnahmeberechtigung folgt kein Zugang zur Abstimmung — dieser wird erst in einem eigenen Schritt ausgegeben.",
    cardTitle: "Abstimmung",
    labels: {
      contextName: "Abstimmung",
      votingType: "Art der Abstimmung",
      scope: "Geltungsbereich",
      window: "Abstimmungszeitraum",
    },
  },

  markerLabels: {
    dot: "Markierung: Punkt",
    clock: "Markierung: Uhr",
    check: "Markierung: Haken",
    crossed: "Markierung: durchgestrichen",
    key: "Markierung: Schlüssel",
    expired: "Markierung: abgelaufen",
  },

  actionLabels: {
    withdraw_request: "Antrag zurückziehen",
    submit_evidence: "Nachweise einreichen",
    retrieve_access: "Zugang abrufen",
    view_reason: "Begründung ansehen",
    open_dispute: "Widerspruch einlegen",
    enter_voting_area: "Zum Abstimmungsbereich",
    report_access_problem: "Problem mit dem Zugang melden",
    view_dispute: "Widerspruch ansehen",
    withdraw_dispute: "Widerspruch zurückziehen",
  },

  noActionAvailable:
    "Keine Handlung erforderlich. Sie erhalten eine Nachricht, sobald sich etwas ändert.",

  actionsHeading: "Mögliche Schritte",

  states: STATE_TEXTS,

  accessAvailability: {
    heading: "Zugang zur Abstimmung",
    windowLabel: "Zugang abrufbar bis",
    noCountdownNote:
      "Fristen werden genannt. Eine laufende Uhr, ein Zähler oder eine geschätzte Wartezeit werden bewusst nicht dargestellt.",
  },

  departure: {
    title: "Sie verlassen jetzt den Mitgliederbereich",
    body: "Im Abstimmungsbereich werden keine Angaben zu Ihrer Person geführt. Es werden dort keine Nutzungsdaten erhoben und keine Verbindung zu Ihrem Konto hergestellt.",
    deliveryNote:
      "Der Zugang wird ausschließlich innerhalb des Abstimmungsbereichs erstellt und dort sofort verwendet. Er wird Ihnen nicht per E-Mail, SMS oder Datei zugesendet, nicht angezeigt und nicht zum Kopieren bereitgestellt. Niemand — auch keine unterstützende oder administrative Person — kann ihn einsehen.",
    declarationLabel: "Erklärung",
    declaration:
      "Mir ist bekannt, dass ich den Abstimmungsbereich jetzt betrete und der Vorgang dort in einem Durchgang abgeschlossen wird.",
    continueLabel: "Fortfahren",
    cancelLabel: "Abbrechen",
    continueHref: "/vote",
    cancelHref: "/mitwirkung/abstimmungen",
  },

  arrival: {
    title: "Sie befinden sich im Abstimmungsbereich",
    body: "Im Abstimmungsbereich werden keine Angaben zu Ihrer Person geführt und keine Nutzungsdaten erhoben.",
  },

  waiting: {
    title: "Zugang wird erstellt",
    body: "Einen Moment bitte. Der Zugang wird erstellt und anschließend sofort eingelöst.",
    note: "Auch dieser kurze Zeitversatz ist Teil des Verfahrens.",
  },

  redeemed: {
    title: "Zugang eingelöst",
    body: "Sie können jetzt an der Abstimmung teilnehmen. Ab hier besteht keine Verbindung mehr zu Ihrem Konto.",
    transition:
      "Der Stimmzettel und die Stimmabgabe sind in diesem Stand noch nicht enthalten. Sie werden in PACK-16 spezifiziert und hier bewusst nicht dargestellt.",
  },

  abort: {
    title: "Vorgang nicht abgeschlossen",
    body: "Der Vorgang wurde nicht abgeschlossen. Wurde bereits ein Zugang erstellt, kann er nicht erneut ausgegeben werden.",
    nextStep:
      "Melden Sie das Problem über „Problem mit dem Zugang melden“. Solange die Widerrufsfrist läuft, kann ein bestehender Zugang widerrufen und ein neuer ausgestellt werden.",
  },

  deliveryRefusal: {
    title: "Zustellung auf einem anderen Weg",
    text: "Der Zugang kann nicht per E-Mail, SMS, Datei, Ausdruck oder über eine andere Person zugestellt werden. Das ist keine technische Einschränkung, sondern Teil des Schutzes: Ein Zugang, den man weitergeben, speichern oder vorzeigen kann, könnte auch abgenommen oder erzwungen werden.",
  },

  smallElectorate: {
    title: "Hinweis zur kleinen Wählerschaft",
    text: "An dieser Abstimmung nehmen nur wenige Personen teil. Bei sehr kleinen Gruppen lässt sich die Teilnahme durch technische Maßnahmen nicht vollständig unkenntlich machen — wer die Gruppe kennt, kann Rückschlüsse ziehen. Das Verfahren wurde entsprechend angepasst: längere Ausgabezeiträume, gröbere Zeitangaben und keine Zwischenzahlen.",
  },

  dispute: {
    title: "Widerspruch einlegen",
    text: "Sie können gegen eine Entscheidung zur Teilnahmeberechtigung oder gegen einen Widerruf des Zugangs Widerspruch einlegen. Die Prüfung erfolgt durch eine Stelle, die an der ursprünglichen Entscheidung nicht beteiligt war.",
    note: "Für den Widerspruch ist keine Angabe zu Ihrer Stimmabgabe erforderlich, und eine solche Angabe wird auch nicht entgegengenommen. Die prüfende Stelle erhält keinen Zugriff auf Stimmen.",
    linkLabel: "Widerspruch einlegen",
    href: "/mitwirkung/abstimmungen/widerspruch",
    activationNote:
      "Der Vorgang ist in diesem Stand beschrieben, aber noch nicht aktiviert.",
  },

  assistance: {
    title: "Unterstützung bei der Teilnahme",
    text: "Wenn Sie bei der Teilnahme Unterstützung benötigen, können Sie diese hier anfordern — technisch, sprachlich, vor Ort oder wegen einer Beeinträchtigung. Sie müssen dabei keine Angaben zu Ihrer Gesundheit machen.",
    limits:
      "Eine unterstützende Person darf Ihnen helfen, die Teilnahmeberechtigung prüfen zu lassen, den Zugang abzurufen und den Abstimmungsbereich zu erreichen. Sie darf nicht an Ihrer Stelle handeln, Ihren Zugang behalten oder Ihre Stimmabgabe einsehen oder beeinflussen.",
    linkLabel: "Unterstützung anfordern",
    href: "/mitwirkung/abstimmungen/unterstuetzung",
    activationNote:
      "Der Vorgang ist in diesem Stand beschrieben, aber noch nicht aktiviert.",
  },

  notOfferedHeading: "Was das System bewusst nicht anbietet",

  notOffered: NOT_OFFERED,
} as const;

export type VotingContent = typeof VOTING_CONTENT;

# PACK-14 — Content Catalogue (Deutsch)

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Required by `FIR-FORM-002` and `FIR-FORM-004`. **These are real texts, not
placeholders.** Every entry carries an owner, a content version, an
effective date and the form version it belongs to, per `FIR-FORM-004`.

| Property               | Value                                                                    |
| ---------------------- | ------------------------------------------------------------------------ |
| Owner                  | Account Registry / Authentication (per section)                          |
| Content version        | `P14-DE-1.0.0`                                                           |
| Effective from         | On acceptance of the PACK-14 implementation round — **not yet in force** |
| Authoritative language | Deutsch                                                                  |
| Form version binding   | `F-P14-01` … `F-P14-15`, version 1                                       |

Translations must not silently alter legal or procedural meaning
(`FIR-FORM-004`). Where an English gloss appears below it is
documentation, never the authoritative text.

---

## 1. Registrierung (`F-P14-01`)

**Titel:** Konto erstellen

**Einleitung:** Mit einem Konto können Sie sich anmelden und Ihre
Sicherheitseinstellungen verwalten. Ein Konto ist keine Mitgliedschaft.
Über die Aufnahme in die Partei wird in einem eigenen Verfahren
entschieden.

**Feldbeschriftungen**

- E-Mail-Adresse
- Sprache
- Bevorzugtes Anmeldeverfahren

**Hilfetext (E-Mail):** Ihre E-Mail-Adresse dient der Kontaktaufnahme und
der Bestätigung. Sie ist nicht Ihre Kontonummer und kann später geändert
werden.

**Erklärungen**

- Ich habe die Nutzungsbedingungen in der Fassung {terms_version} gelesen
  und akzeptiere sie.
- Ich habe die Datenschutzhinweise zur Kenntnis genommen.

**Bestätigung:** Ihr Konto wurde angelegt. Bitte bestätigen Sie Ihre
E-Mail-Adresse, um es zu aktivieren.

**Fehlermeldungen**

- Bitte geben Sie eine gültige E-Mail-Adresse ein.
- Bitte akzeptieren Sie die Nutzungsbedingungen, um fortzufahren.
- Wenn zu dieser Adresse ein Konto besteht, erhalten Sie eine Nachricht.
  _(Antwort ist bewusst identisch für bestehende und nicht bestehende
  Konten — Kontenaufzählung wird dadurch verhindert.)_

## 2. E-Mail-Bestätigung (`F-P14-02`)

**Titel:** E-Mail-Adresse bestätigen

**Text:** Wir haben Ihnen einen Bestätigungscode an {channel} gesendet. Der
Code ist {validity} gültig und kann nur einmal verwendet werden.

**Fehlermeldungen**

- Der Code ist nicht korrekt. Bitte prüfen Sie Ihre Eingabe.
- Der Code ist abgelaufen. Bitte fordern Sie einen neuen Code an.
- Zu viele Versuche. Bitte warten Sie {cooldown}, bevor Sie es erneut
  versuchen.

## 3. Passkey einrichten (`F-P14-04`)

**Titel:** Passkey einrichten

**Einleitung:** Ein Passkey ist das sicherste Anmeldeverfahren. Er ist an
diese Website gebunden und kann auf einer gefälschten Seite nicht
verwendet werden.

**Hilfetext:** Richten Sie nach Möglichkeit **mehr als einen** Passkey ein.
Geht ein Gerät verloren, können Sie sich dann weiterhin anmelden.

**Feldbeschriftung:** Name für dieses Gerät

**Hilfetext (Name):** Ein Name, an dem Sie das Gerät später wiedererkennen,
zum Beispiel „Diensthandy" oder „Laptop zu Hause".

**Hinweis bei synchronisiertem Passkey:** Dieser Passkey wird über Ihr
Geräte-Konto synchronisiert. Er schützt zuverlässig vor gefälschten
Anmeldeseiten. Für besonders kritische Handlungen kann zusätzlich ein
gerätegebundener Passkey oder ein Sicherheitsschlüssel verlangt werden.

**Bestätigung:** Der Passkey „{nickname}" wurde eingerichtet. Wir haben
Sie darüber an alle bestätigten Kontaktwege benachrichtigt.

## 4. Passkey entfernen (`F-P14-05`)

**Titel:** Passkey entfernen

**Warnung:** Wenn Sie diesen Passkey entfernen, können Sie sich mit diesem
Gerät nicht mehr anmelden. Diese Handlung wird an alle bestätigten
Kontaktwege gemeldet.

**Erklärung:** Mir ist bekannt, dass ich mich mit diesem Gerät danach nicht
mehr anmelden kann.

**Ablehnung (letzter Zugang):** Dies ist Ihr einziges Anmeldeverfahren. Es
kann nicht entfernt werden, solange kein zweiter Zugang oder ein
eingerichteter Wiederherstellungsweg besteht. Richten Sie zuerst einen
weiteren Passkey oder Wiederherstellungscodes ein.

## 5. Zwei-Faktor-Verfahren (`F-P14-06`, `F-P14-07`)

**Titel:** Zwei-Faktor-Verfahren einrichten

**Einleitung:** Ein zweiter Faktor schützt Ihr Konto zusätzlich. Verfahren
per E-Mail oder SMS bieten dabei den geringsten Schutz und reichen für
besonders kritische Handlungen nicht aus.

**Warnung beim Entfernen:** Nach dem Entfernen sinkt das Schutzniveau Ihres
Kontos. Bestimmte Handlungen sind dann nicht mehr möglich, bis Sie ein
gleichwertiges Verfahren einrichten.

**Erklärung:** Mir ist bekannt, dass das Schutzniveau meines Kontos dadurch
sinkt.

## 6. Wiederherstellungscodes (`F-P14-08`)

**Titel:** Wiederherstellungscodes erzeugen

**Text:** Diese Codes werden **nur einmal** angezeigt. Bewahren Sie sie an
einem sicheren Ort auf, getrennt von Ihren Geräten. Jeder Code kann genau
einmal verwendet werden.

**Erklärung:** Ich habe die Codes gespeichert.

## 7. Kontowiederherstellung (`F-P14-09`)

**Titel:** Zugang zum Konto wiederherstellen

**Einleitung:** Wenn Sie sich nicht mehr anmelden können, prüfen wir Ihren
Antrag in einem geregelten Verfahren. Zum Schutz vor Kontoübernahmen kann
dies einige Zeit dauern und zusätzliche Nachweise erfordern.

**Hinweis:** Aus Sicherheitsgründen stellen wir keine Fragen zu
persönlichen Angaben, die öffentlich bekannt sein können.

**Feldbeschriftungen**

- Erreichbarer Kontaktweg
- Grund des Antrags
- Unterstützt durch (falls zutreffend)

**Fehlermeldung (kürzlich geänderter Kontaktweg):** Dieser Kontaktweg wurde
vor Kurzem geändert und kann derzeit nicht als alleiniger Nachweis dienen.
Bitte wählen Sie einen anderen Weg oder wenden Sie sich an die
Unterstützung.

**Wartezeit:** Ihr Antrag wird geprüft. Aus Sicherheitsgründen gilt eine
Wartezeit bis {cooling_off_end}. In dieser Zeit informieren wir alle
bestätigten Kontaktwege. Waren Sie das nicht, können Sie den Vorgang
sofort stoppen.

**Abschluss:** Ihr Zugang wurde wiederhergestellt. Alle bisherigen
Anmeldeverfahren und alle aktiven Sitzungen wurden beendet.

**Ablehnung:** Der Antrag konnte nicht bewilligt werden ({reason_code}).
Sie können Widerspruch einlegen; die Wege dazu finden Sie in dieser
Mitteilung.

## 8. Verdächtige Anmeldung (`F-P14-10`)

**Titel:** Ungewöhnliche Anmeldung festgestellt

**Text:** Am {occurred_at} wurde eine Anmeldung von einem uns unbekannten
Gerät festgestellt.

**Auswahl**

- Das war ich.
- **Das war ich nicht.**

**Nach „Das war ich nicht":** Wir haben alle aktiven Sitzungen beendet.
Bitte richten Sie umgehend ein neues Anmeldeverfahren ein. Wir haben einen
Sicherheitsvorgang eröffnet.

## 9. Kontaktdaten ändern (`F-P14-11`)

**Titel:** Kontaktdaten ändern

**Hinweis:** Wir benachrichtigen sowohl den bisherigen als auch den neuen
Kontaktweg. So bemerken Sie eine unberechtigte Änderung.

**Bestätigung:** Ihr Kontaktweg wurde geändert. Für einen begrenzten
Zeitraum kann der neue Weg nicht als alleiniger Nachweis für eine
Kontowiederherstellung dienen.

## 10. Aktive Sitzungen (`F-P14-12`)

**Titel:** Aktive Sitzungen und Geräte

**Text:** Hier sehen Sie, wo Sie derzeit angemeldet sind. Sie können
einzelne Sitzungen oder alle Sitzungen beenden.

**Bestätigung:** {count} Sitzungen wurden beendet. Eine beendete Sitzung
kann nicht fortgesetzt werden.

## 11. Konto schließen (`F-P14-13`)

**Titel:** Konto schließen

**Warnung:** Das Schließen des Kontos beendet **nicht** Ihre Mitgliedschaft.
Ein Austritt aus der Partei ist ein eigenes Verfahren.

**Hinweis zur Aufbewahrung:** Bestimmte Aufzeichnungen müssen wir aus
rechtlichen Gründen weiter aufbewahren. Sie werden nicht gelöscht, auch
wenn das Konto geschlossen ist.

**Erklärungen**

- Mir ist bekannt, dass das Schließen des Kontos keine Beendigung der
  Mitgliedschaft ist.
- Mir ist bekannt, dass bestimmte Aufzeichnungen aufbewahrt werden.

**Wartezeit:** Ihr Antrag wurde aufgenommen. Bis {cooling_off_end} können
Sie ihn widerrufen.

## 12. Identitätsprüfung (`F-P14-14`)

**Titel:** Identität nachweisen

**Einleitung:** Für bestimmte Verfahren ist ein Identitätsnachweis
erforderlich. Wir erheben dabei nur, was für den angegebenen Zweck
notwendig ist.

**Hinweis:** Ein Identitätsnachweis ist **keine** Aussage über Ihre
Staatsangehörigkeit und **keine** Entscheidung über eine Mitgliedschaft.

**Erklärung:** Ich willige ein, dass die eingereichten Nachweise
ausschließlich zum Zweck {purpose} geprüft und nach den geltenden Fristen
aufbewahrt werden.

**Ergebnis (offen):** Ihre Angaben konnten nicht abschließend geprüft
werden. Der Vorgang wurde zur manuellen Prüfung weitergeleitet.

## 13. Privilegierte Wiederherstellung (`F-P14-15`)

**Titel:** Wiederherstellung genehmigen

**Hinweis für Prüfende:** Sie dürfen einen Vorgang nicht genehmigen, den
Sie selbst eingeleitet haben oder der Sie selbst betrifft. Jede
Entscheidung wird mit Begründungscode und Nachweis aufgezeichnet.

**Ablehnung bei Selbstgenehmigung:** Diese Entscheidung ist nicht zulässig,
da Sie den Vorgang eingeleitet haben oder betroffen sind.

## 14. Einreichungsbestätigung — allgemeiner Aufbau

**Titel:** Einreichungsbestätigung

Enthält: Formular-Kennung und -Version, Vorgangsnummer, Datum und Uhrzeit,
einreichende Stelle in zulässiger Form, organisatorischer Geltungsbereich,
Verzeichnis der Anlagen, ausdrücklich bestätigte Erklärungen,
Integritätsnachweis, Einreichungsweg sowie den nächsten Verfahrensschritt
mit geltenden Fristen.

**Schlusssatz:** Diese Bestätigung dokumentiert den Eingang. Sie ist keine
Entscheidung in der Sache.

## 15. Wiederkehrende Bausteine

| Baustein                         | Text                                                                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Zusätzliche Bestätigung nötig    | Für diesen Schritt ist eine erneute Bestätigung Ihrer Identität erforderlich.                                                               |
| Bestätigung abgelaufen           | Ihre Bestätigung ist abgelaufen. Bitte bestätigen Sie erneut.                                                                               |
| Vorgang geändert                 | Der Vorgang hat sich geändert, nachdem Sie ihn bestätigt haben. Bitte prüfen Sie die Änderung und bestätigen Sie erneut.                    |
| Nicht ausreichendes Schutzniveau | Für diese Handlung ist ein höheres Schutzniveau erforderlich.                                                                               |
| Sitzung abgelaufen               | Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.                                                                               |
| Sitzung beendet                  | Diese Sitzung wurde beendet und kann nicht fortgesetzt werden.                                                                              |
| Dienst nicht erreichbar          | Der Dienst ist derzeit nicht erreichbar. Aus Sicherheitsgründen wird diese Handlung nicht ausgeführt. Bitte versuchen Sie es später erneut. |
| Konto gesperrt                   | Ihr Konto ist derzeit gesperrt ({reason_code}). Die Mitteilung nennt Ihnen die zuständige Stelle und den Weg zum Widerspruch.               |

**Grundsatz für alle Texte:** Jede Ablehnung nennt einen Grund, die
zuständige Stelle und den nächsten möglichen Schritt. Eine Ablehnung ohne
Weg nach vorn ist in diesem System kein zulässiger Text.

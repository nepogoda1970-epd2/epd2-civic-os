# PACK-15 — Content Catalogue (Deutsch)

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Required by `FIR-FORM-002` and `FIR-FORM-004`. **These are real texts, not
placeholders.**

| Property               | Value                                                                           |
| ---------------------- | ------------------------------------------------------------------------------- |
| Owner                  | Eligibility Service / Credential Issuer / Election administration (per section) |
| Content version        | `P15-DE-1.0.0`                                                                  |
| Effective from         | On acceptance of the PACK-15 implementation round — **not yet in force**        |
| Authoritative language | Deutsch                                                                         |
| Form version binding   | `F-P15-01` … `F-P15-09`, version 1                                              |

Translations must not silently alter legal or procedural meaning
(`FIR-FORM-004`). Where an English gloss appears below it is
documentation, never the authoritative text.

**Two rules govern every text in this catalogue.** First: no text
confirms, denies or implies a ballot choice or an individual act of
casting. Second: every refusal names a reason, the responsible body and
the next possible step — a refusal without a way forward is not a
permissible text in this system.

---

## 1. Stimmberechtigung beantragen (`F-P15-01`)

**Titel:** Teilnahme prüfen lassen

**Einleitung:** Für jede Abstimmung wird gesondert geprüft, wer
teilnahmeberechtigt ist. Die Prüfung erfolgt nach den Regeln, die für
diese Abstimmung vor Beginn festgelegt und veröffentlicht wurden. Eine
Prüfung ist keine Stimmabgabe.

**Hinweis zur Trennung:** Ihre Anmeldung, Ihre Mitgliedschaft und Ihre
Teilnahmeberechtigung sind drei verschiedene Dinge. Aus der
Teilnahmeberechtigung folgt kein Zugang zur Abstimmung — dieser wird erst
in einem eigenen Schritt ausgegeben.

**Feldbeschriftungen**

- Abstimmung
- Art der Teilnahme
- Unterstützt durch (falls zutreffend)
- Bevorzugter Benachrichtigungsweg

**Erklärung:** Meine Angaben sind vollständig und richtig.

**Erklärung (Interessenkonflikt, falls verlangt):** Mir ist bekannt, dass
ich einen Interessenkonflikt anzeigen muss, und ich habe dies getan,
soweit ein solcher besteht.

**Bestätigung:** Ihr Antrag wurde aufgenommen. Sie erhalten eine
Mitteilung, sobald die Prüfung abgeschlossen ist.

**Fehlermeldungen**

- Diese Abstimmung ist derzeit nicht geöffnet.
- Diese Abstimmung gehört nicht zu Ihrem Bereich.
- Für diese Abstimmung liegt bereits ein Antrag von Ihnen vor.

## 2. Ergebnis der Prüfung

**Bewilligt:** Sie sind für die Abstimmung „{context_name}"
teilnahmeberechtigt. Der Zugang zur Abstimmung kann ab {issuance_start}
und bis {issuance_end} abgerufen werden. Der Zugang wird nur einmal
ausgegeben.

**Abgelehnt:** Ihr Antrag wurde abgelehnt ({reason_code}). Die Mitteilung
nennt Ihnen die geprüfte Regel und die zuständige Stelle. Sie können gegen
diese Entscheidung Widerspruch einlegen; die Frist beträgt
{objection_period}.

**Prüfung durch eine Person erforderlich:** Ihr Antrag wird durch eine
zuständige Person geprüft. **Dies ist keine Ablehnung.** Sie erhalten eine
Mitteilung, sobald entschieden wurde. Wird eine Prüfung nicht rechtzeitig
abgeschlossen, wird der Vorgang eskaliert und nicht automatisch
entschieden.

**Nachweise fehlen:** Für die Prüfung fehlen noch Nachweise
({reason_code}). Bitte reichen Sie die genannten Unterlagen ein.

**Angaben veraltet:** Die zugrunde liegenden Angaben sind nicht aktuell
genug für diese Abstimmung. Wir prüfen erneut, sobald aktuelle Angaben
vorliegen. Sie müssen nichts weiter tun.

**Schutzniveau nicht ausreichend:** Für diese Abstimmung ist ein höheres
Schutzniveau Ihrer Anmeldung erforderlich. Richten Sie ein sichereres
Anmeldeverfahren ein und stellen Sie den Antrag danach erneut.

**Entscheidung abgelaufen:** Die Entscheidung ist abgelaufen, weil der
Ausgabezeitraum endete. Eine erneute Prüfung ist innerhalb des
Ausgabezeitraums möglich.

## 3. Nachweise einreichen (`F-P15-02`)

**Titel:** Nachweise einreichen

**Einleitung:** Reichen Sie hier die Unterlagen ein, die für die Prüfung
Ihrer Teilnahmeberechtigung angefordert wurden. Es werden nur die
Unterlagen erhoben, die für die genannte Regel erforderlich sind.

**Erklärung:** Ich willige ein, dass die eingereichten Nachweise
ausschließlich zur Prüfung meiner Teilnahmeberechtigung für die Abstimmung
„{context_name}" verwendet und nach den geltenden Fristen aufbewahrt
werden.

**Hinweis:** Die Unterlagen verlassen den Prüfvorgang nicht. Sie werden
insbesondere **nicht** an den Abstimmungsbereich übermittelt.

## 4. Zugang zur Abstimmung abrufen (`F-P15-04`)

**Titel:** Zugang zur Abstimmung abrufen

**Einleitung:** Sie erhalten jetzt einen einmaligen Zugang zur Abstimmung
„{context_name}". Der Zugang gilt nur für diese Abstimmung, ist nur
einmal verwendbar und läuft am {expiry} ab.

**Wichtiger Hinweis:** Der Zugang enthält keine Angaben zu Ihrer Person.
Er kann dem Abstimmungsbereich nicht zeigen, wer Sie sind, und er kann
später nicht mit Ihrer Stimme in Verbindung gebracht werden. Deshalb kann
ein einmal eingelöster Zugang auch nicht zurückgenommen werden.

**Warnung:** Geben Sie diesen Zugang an niemanden weiter. Wer ihn besitzt,
kann ihn einlösen. Wir können nicht feststellen, wer ihn eingelöst hat.

**Bestätigung:** Der Zugang wurde ausgegeben. Sie wechseln jetzt in den
Abstimmungsbereich. Dort werden Sie nicht mehr namentlich geführt.

**Fehlermeldungen**

- Der Ausgabezeitraum für diese Abstimmung ist beendet.
- Dieser Nachweis der Teilnahmeberechtigung ist abgelaufen.
- Dieser Nachweis wurde bereits verwendet. Ein zweiter Zugang wird nicht
  ausgegeben.
- Dieser Nachweis gehört zu einer anderen Abstimmung.
- Für diese Abstimmung wurde Ihnen bereits ein Zugang ausgegeben.

## 5. Zugang verloren, nicht erhalten oder abgelaufen (`F-P15-05`)

**Titel:** Problem mit dem Zugang melden

**Einleitung:** Melden Sie hier, wenn Sie den Zugang nicht erhalten haben,
ihn verloren haben oder er abgelaufen ist. Was möglich ist, hängt davon
ab, ob der Zugang bereits eingelöst wurde und ob die Frist für Widerrufe
noch läuft.

**Auswahl**

- Ich habe den Zugang nicht erhalten.
- Ich habe den Zugang verloren.
- Der Zugang ist ungenutzt abgelaufen.
- Ich vermute, dass der Zugang missbraucht wurde.

**Möglich (vor Ablauf der Widerrufsfrist):** Wir können den bisherigen
Zugang widerrufen und Ihnen einen neuen ausstellen. Der bisherige Zugang
wird dabei ungültig.

**Nicht möglich (nach Einlösung):** Ein bereits eingelöster Zugang kann
nicht widerrufen und nicht ersetzt werden. Das liegt nicht an einer
fehlenden Funktion, sondern am Aufbau des Verfahrens: Damit niemand
nachvollziehen kann, wie Sie abgestimmt haben, besteht keine Verbindung
zwischen Ihrem Zugang und einer abgegebenen Stimme. Ohne diese Verbindung
kann eine Stimme weder gefunden noch geändert werden — auch nicht durch
die Administration.

**Nicht möglich (nach Ablauf der Widerrufsfrist):** Für diese Abstimmung
ist die Frist für Widerrufe am {revocation_cutoff} abgelaufen. Eine
erneute Ausgabe ist nicht mehr möglich. Sie können den Vorgang prüfen
lassen; die Wege dazu finden Sie in dieser Mitteilung.

**Bei vermutetem Missbrauch:** Wir nehmen Ihre Meldung auf und prüfen den
Vorgang auf Hinweise auf einen Missbrauch. Sollte sich ein Fehler des
Verfahrens bestätigen, wird über Maßnahmen für die gesamte Abstimmung
entschieden — nicht über einzelne Stimmen.

## 6. Widerspruch (`F-P15-03`, `F-P15-06`)

**Titel:** Widerspruch einlegen

**Einleitung:** Sie können gegen eine Entscheidung zur
Teilnahmeberechtigung oder gegen einen Widerruf des Zugangs Widerspruch
einlegen. Die Prüfung erfolgt durch eine Stelle, die an der ursprünglichen
Entscheidung nicht beteiligt war.

**Hinweis:** Für den Widerspruch ist **keine Angabe zu Ihrer Stimmabgabe
erforderlich**, und eine solche Angabe wird auch nicht entgegengenommen.
Die prüfende Stelle erhält keinen Zugriff auf Stimmen.

**Feldbeschriftungen**

- Betroffene Entscheidung
- Grund des Widerspruchs
- Begründung
- Gewünschtes Ergebnis

**Bestätigung:** Ihr Widerspruch wurde aufgenommen. Sie erhalten die
Entscheidung bis spätestens {deadline}.

**Entscheidung — stattgegeben:** Ihrem Widerspruch wurde stattgegeben. Die
Entscheidung wurde aufgehoben und der Vorgang neu geprüft.

**Entscheidung — teilweise stattgegeben:** Ihrem Widerspruch wurde
teilweise stattgegeben ({reason_code}). Die Mitteilung nennt Ihnen, was
geändert wurde und was nicht.

**Entscheidung — zurückgewiesen:** Ihr Widerspruch wurde zurückgewiesen
({reason_code}). Die Mitteilung nennt Ihnen die geprüfte Regel, die
zuständige Stelle und die weiteren Möglichkeiten.

**Grenze der Abhilfe:** Wenn eine Abstimmung bereits läuft oder
abgeschlossen ist, kann ein Widerspruch nicht zu einer nachträglichen
Änderung einzelner Stimmen führen. Möglich sind Maßnahmen, die die gesamte
Abstimmung betreffen — etwa eine Verlängerung, eine Aussetzung oder eine
Wiederholung. Über solche Maßnahmen entscheidet das dafür zuständige
Gremium.

## 7. Unterstützung (`F-P15-07`, `F-P15-08`)

**Titel:** Unterstützung bei der Teilnahme

**Einleitung:** Wenn Sie bei der Teilnahme Unterstützung benötigen, können
Sie diese hier anfordern — technisch, sprachlich, vor Ort oder wegen einer
Beeinträchtigung. Sie müssen dabei keine Angaben zu Ihrer Gesundheit
machen.

**Grenzen der Unterstützung — verbindlich:** Eine unterstützende Person
darf Ihnen helfen, die Teilnahmeberechtigung prüfen zu lassen, den Zugang
abzurufen und den Abstimmungsbereich zu erreichen. Sie darf **nicht** an
Ihrer Stelle handeln, Ihren Zugang behalten oder Ihre Stimmabgabe
einsehen oder beeinflussen.

**Erklärungen der unterstützenden Person**

- Ich habe im Auftrag und in Anwesenheit der antragstellenden Person
  gehandelt.
- Ich habe keinen Zugang zurückbehalten.
- Ich habe die Stimmabgabe weder eingesehen noch beeinflusst.

**Nachweis:** Über jede unterstützte Handlung wird ein Nachweis erstellt,
der die unterstützende Person namentlich nennt. Sie erhalten diesen
Nachweis.

## 8. Unabhängige Prüfung (`F-P15-09`)

**Titel:** Unabhängige Prüfung beantragen

**Einleitung:** Sie können eine unabhängige Prüfung der Durchführung einer
Abstimmung beantragen. Geprüft werden der ordnungsgemäße Ablauf, die
Einhaltung der Trennung der Zuständigkeiten und die Übereinstimmung der
Anzahlen — **nicht** einzelne Stimmen und nicht, wer teilgenommen hat.

**Hinweis:** Die prüfende Stelle arbeitet mit Nachweisbündeln, die keine
personenbezogenen Verbindungen enthalten. Sie erhält keinen Zugriff auf
Stimmen und keine Möglichkeit, Personen und Stimmen einander zuzuordnen.

## 9. Störungen und Ausfälle

| Situation                           | Text                                                                                                                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Quelle nicht erreichbar             | Die Prüfung ist derzeit nicht möglich, weil erforderliche Angaben nicht abgerufen werden können. Aus Sicherheitsgründen wird nicht vorläufig entschieden. Wir versuchen es erneut. |
| Ausgabe verzögert                   | Die Ausgabe des Zugangs ist derzeit verzögert. Ihr Nachweis der Teilnahmeberechtigung bleibt gültig; er wurde noch nicht verbraucht.                                               |
| Einlösung nicht bestätigt           | Die Einlösung konnte nicht bestätigt werden. Bitte versuchen Sie es erneut. Es kann dabei kein zweiter Zugang entstehen.                                                           |
| Prüfung nicht möglich               | Eine erforderliche Sicherheitsprüfung ist derzeit nicht möglich. Aus Sicherheitsgründen wird kein Zugang ausgegeben.                                                               |
| Abstimmungsbereich nicht erreichbar | Der Abstimmungsbereich ist derzeit nicht erreichbar. Bitte versuchen Sie es später erneut. Sollte die Störung längere Zeit andauern, wird über eine Verlängerung entschieden.      |
| Zeitprüfung fehlgeschlagen          | Der Vorgang konnte nicht ausgeführt werden, weil die Zeitprüfung fehlgeschlagen ist. Bitte versuchen Sie es später erneut.                                                         |
| Nachweisführung nicht möglich       | Aus Sicherheitsgründen wird diese Handlung nicht ausgeführt, solange sie nicht nachweisbar aufgezeichnet werden kann.                                                              |
| Prüfung durch Person ausstehend     | Ihr Vorgang wartet auf die Prüfung durch eine zuständige Person. Der Vorgang wird nicht automatisch entschieden.                                                                   |

## 10. Wiederkehrende Bausteine

| Baustein                          | Text                                                                                                                                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Trennung Anmeldung / Berechtigung | Angemeldet zu sein bedeutet nicht, teilnahmeberechtigt zu sein. Beides wird getrennt geprüft.                                                  |
| Trennung Berechtigung / Zugang    | Teilnahmeberechtigt zu sein bedeutet noch nicht, Zugang zu haben. Der Zugang wird gesondert ausgegeben.                                        |
| Einmaligkeit                      | Der Zugang gilt für eine Abstimmung und kann nur einmal verwendet werden.                                                                      |
| Keine Zuordnung                   | Es besteht keine Verbindung zwischen Ihrer Person und Ihrer Stimme. Diese Verbindung wird nicht gespeichert und kann nicht hergestellt werden. |
| Keine Zwischenergebnisse          | Vor dem offiziellen Abschluss werden keine Zwischenstände, Teilergebnisse oder Beteiligungszahlen veröffentlicht.                              |
| Kein Nachweis der Stimmabgabe     | Das System kann und darf nicht bestätigen, ob eine bestimmte Person abgestimmt hat. Ein solcher Nachweis wird nicht ausgestellt.               |
| Widerspruch                       | Gegen jede Entscheidung können Sie Widerspruch einlegen. Die Mitteilung nennt Ihnen die zuständige Stelle und die Frist.                       |
| Erklärung zum Widerruf            | Ein Widerruf ist nur möglich, solange der Zugang nicht eingelöst wurde und die Widerrufsfrist nicht abgelaufen ist.                            |
| Verlassen des Mitgliederbereichs  | Sie verlassen jetzt den Mitgliederbereich. Im Abstimmungsbereich werden keine Angaben zu Ihrer Person geführt und keine Nutzungsdaten erhoben. |

## 11. Was das System bewusst nicht anbietet

Diese Texte erscheinen dort, wo Mitglieder eine Funktion erwarten, die es
aus Gründen des Verfahrens nicht gibt. Sie erklären den Grund, statt eine
Lücke zu lassen.

| Erwartete Funktion             | Text                                                                                                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Nachweis „Ich habe abgestimmt" | Ein solcher Nachweis wird nicht ausgestellt. Er würde eine Verbindung zwischen Person und Stimme voraussetzen, die es nicht gibt — und er könnte gegen Sie verwendet werden, etwa um Druck auf Ihre Teilnahme auszuüben. |
| Stimme zurückziehen            | Eine abgegebene Stimme kann nicht zurückgezogen werden. Sie ist keiner Person zugeordnet und kann deshalb nicht aufgefunden werden.                                                                                      |
| Teilnehmerliste einsehen       | Eine Liste der Teilnehmenden wird nicht geführt und nicht veröffentlicht.                                                                                                                                                |
| Zwischenstand ansehen          | Zwischenstände gibt es nicht. Das Ergebnis wird nach dem Abschluss durch die zuständige Stelle festgestellt und veröffentlicht.                                                                                          |
| Zugang übertragen              | Der Zugang kann nicht übertragen werden. Er ist an eine Abstimmung gebunden und nur einmal verwendbar.                                                                                                                   |

---

**Grundsatz für alle Texte:** Jede Ablehnung nennt einen Grund, die
zuständige Stelle und den nächsten möglichen Schritt. Jede Grenze des
Verfahrens wird erklärt, nicht verschwiegen. Kein Text bestätigt, verneint
oder legt nahe, wie eine Person abgestimmt hat.

---

## 12. Texte der Architekturkorrektur (2026-07-31)

Ergänzt Abschnitte 1–11. Inhaltsversion bleibt `P15-DE-1.0.0`.

### 12.1 Zugang wird vorbereitet (Warteschlange)

**Titel:** Zugang wird vorbereitet

**Text:** Ihre Teilnahmeberechtigung wurde bestätigt. Der Zugang zur
Abstimmung wird jetzt vorbereitet und in Kürze freigegeben. Sie erhalten
eine Nachricht, sobald er verfügbar ist.

**Hinweis (verbindlich, erklärt das Verfahren):** Zugänge werden bewusst
gesammelt und zeitlich versetzt freigegeben. Dadurch lässt sich aus dem
Zeitpunkt nicht ableiten, wer einen Zugang erhalten hat. Diese Wartezeit
ist kein Fehler und kein Rückstand.

**Bewusst nicht angezeigt:** eine Position in einer Warteschlange, eine
verbleibende Wartezeit oder ein Zähler. Beides würde Rückschlüsse auf die
Zahl der Teilnehmenden erlauben und unnötigen Druck erzeugen.

### 12.2 Zugang verfügbar

**Titel:** Zugang verfügbar

**Text:** Ihr Zugang zur Abstimmung „{context_name}" ist jetzt verfügbar.
Sie können den Abstimmungsbereich bis {expiry} betreten.

**Schaltfläche:** Zum Abstimmungsbereich

### 12.3 Verlassen des Mitgliederbereichs

**Titel:** Sie verlassen jetzt den Mitgliederbereich

**Text:** Im Abstimmungsbereich werden keine Angaben zu Ihrer Person
geführt. Es werden dort keine Nutzungsdaten erhoben und keine Verbindung zu
Ihrem Konto hergestellt.

**Hinweis:** Der Zugang wird ausschließlich innerhalb des
Abstimmungsbereichs erstellt und dort sofort verwendet. Er wird Ihnen
nicht per E-Mail, SMS oder Datei zugesendet, nicht angezeigt und nicht zum
Kopieren bereitgestellt. Niemand — auch keine unterstützende oder
administrative Person — kann ihn einsehen.

**Erklärung:** Mir ist bekannt, dass ich den Abstimmungsbereich jetzt
betrete und der Vorgang dort in einem Durchgang abgeschlossen wird.

**Schaltflächen:** Fortfahren · Abbrechen

### 12.4 Zugang wird erstellt (im Abstimmungsbereich)

**Titel:** Zugang wird erstellt

**Text:** Einen Moment bitte. Der Zugang wird erstellt und anschließend
sofort eingelöst.

**Hinweis:** Auch dieser kurze Zeitversatz ist Teil des Verfahrens.

### 12.5 Zugang eingelöst

**Titel:** Zugang eingelöst

**Text:** Sie können jetzt an der Abstimmung teilnehmen. Ab hier besteht
keine Verbindung mehr zu Ihrem Konto.

### 12.6 Abbruch im Abstimmungsbereich

**Titel:** Vorgang nicht abgeschlossen

**Text:** Der Vorgang wurde nicht abgeschlossen. Wurde bereits ein Zugang
erstellt, kann er nicht erneut ausgegeben werden.

**Nächster Schritt:** Melden Sie das Problem über „Problem mit dem Zugang
melden". Solange die Widerrufsfrist läuft, kann ein bestehender Zugang
widerrufen und ein neuer ausgestellt werden.

### 12.7 Ablehnung eines anderen Zustellwegs

**Text:** Der Zugang kann nicht per E-Mail, SMS, Datei, Ausdruck oder über
eine andere Person zugestellt werden. Das ist keine technische
Einschränkung, sondern Teil des Schutzes: Ein Zugang, den man weitergeben,
speichern oder vorzeigen kann, könnte auch abgenommen oder erzwungen
werden.

### 12.8 Kleine Wählerschaft — Hinweis

**Text:** An dieser Abstimmung nehmen nur wenige Personen teil. Bei sehr
kleinen Gruppen lässt sich die Teilnahme durch technische Maßnahmen nicht
vollständig unkenntlich machen — wer die Gruppe kennt, kann Rückschlüsse
ziehen. Das Verfahren wurde entsprechend angepasst: längere
Ausgabezeiträume, gröbere Zeitangaben und keine Zwischenzahlen.

### 12.9 Ergänzung zu Abschnitt 11 — was das System weiterhin nicht anbietet

| Erwartete Funktion                | Text                                                                                                                                                      |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Zugang zusenden lassen            | Der Zugang wird ausschließlich im Abstimmungsbereich erstellt und dort sofort verwendet. Ein Versand ist nicht vorgesehen und wäre ein Sicherheitsrisiko. |
| Zugang für später aufbewahren     | Der Zugang wird nicht gespeichert und nicht angezeigt. Erstellung und Verwendung erfolgen in einem Durchgang.                                             |
| Status „hat teilgenommen" abrufen | Ob eine bestimmte Person teilgenommen hat, wird nicht gespeichert und kann nicht abgefragt werden — weder durch Sie noch durch die Administration.        |
| Zwischenzahlen zur Beteiligung    | Vor dem Abschluss werden keine Beteiligungszahlen veröffentlicht, auch nicht als Fortschrittsanzeige.                                                     |

**Grundsatz, unverändert:** Jede Ablehnung nennt einen Grund, die zuständige
Stelle und den nächsten möglichen Schritt. Kein Text bestätigt, verneint
oder legt nahe, ob oder wie eine Person abgestimmt hat.

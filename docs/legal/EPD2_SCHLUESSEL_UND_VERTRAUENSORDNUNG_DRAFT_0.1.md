# EPD² Schlüssel- und Vertrauensordnung (SVO) — Diskussionsentwurf 0.1

**Status:** DRAFT / NOT ADOPTED / NOT LEGALLY ACTIVATED  
**Date:** 2026-08-28  
**Purpose:** Legal-organizational rules for cryptographic trust, key custody, bounded delegation, blocking, revocation, recovery and independent evidence control.  
**Technical boundary:** Concrete provider names, HSM/KMS coordinates, key IDs, recovery shares, secret material and operational credentials are excluded from this document.

## § 1 Zweck und Grundprinzipien

(1) Diese Ordnung konkretisiert die Satzung in Bezug auf die mehrstufige kryptographische Vertrauensarchitektur, die Verwahrung kritischer Schlüssel, die technische Delegation an Bundes- und Gebietsverbände, die Sperrung und den Widerruf technischer Zugänge, die Wiederherstellung nach Sicherheitsvorfällen sowie die unabhängige Nachweisführung.

(2) Technische Schlüssel, Zertifikate, Sitzungen, Authentisierungsmittel und sonstige technische Berechtigungen begründen weder ein Parteiamt noch eine politische, organisatorische, finanzielle, mitgliedschaftsbezogene oder wahlbezogene Zuständigkeit.

(3) Politische oder organisatorische Zuständigkeiten entstehen ausschließlich aus Gesetz, Satzung, wirksam erlassenen Ordnungen sowie ordnungsgemäßen Wahlen, Bestellungen oder Beschlüssen des zuständigen Parteiorgans.

(4) Es gilt das Trennungsprinzip:

```text
politische Zuständigkeit
!= OrganizationalAuthority
!= technische Sitzung
!= Zugangsschlüssel
!= Schlüsselverwahrung
!= Security Authority
!= Voting Authority
```

## § 2 Drei Vertrauensebenen

(1) Die allgemeine EPD²-Vertrauensarchitektur besteht mindestens aus drei getrennten Vertrauensebenen.

### Ebene 1 — Zentraler Vertrauensanker / Root Trust

Der zentrale Vertrauensanker bildet den höchsten generischen kryptographischen Vertrauensanker der Plattform.

Er darf:
- nachgeordnete Plattform-Vertrauensanker bestätigen;
- im geregelten Wiederherstellungs- oder Rotationsverfahren neue nachgeordnete Vertrauensanker autorisieren.

Er darf nicht:
- für gewöhnliche Benutzeranmeldungen verwendet werden;
- tägliche regionale oder föderale Verwaltungsaktionen signieren;
- an Bundes-, Landes-, Kreis-, Bezirks- oder Ortsstrukturen übertragen werden;
- einer einzelnen natürlichen Person oder einem einzelnen Parteiorgan allein zur Verfügung stehen.

### Ebene 2 — Plattform-Vertrauensanker / Platform Intermediate

Der Plattform-Vertrauensanker ist vom Root Trust getrennt und erhält einen eigenen privaten Schlüssel.

Er darf ausschließlich nach Maßgabe dieser Ordnung und der technischen Sicherheitsrichtlinien:
- Bund- oder zweckgebundene Issuer bestätigen;
- regionale Issuer bestätigen;
- Rotationen und Widerrufe in seinem Zuständigkeitsbereich technisch abbilden.

Der private Root-Schlüssel wird hierfür nicht übertragen.

### Ebene 3 — Bund- und Regional-Issuer

Der Bundesverband und berechtigte Gebietsverbände erhalten ausschließlich eigene, voneinander getrennte technische Issuer-Schlüssel.

Jeder Issuer ist sachlich, räumlich, organisatorisch und zeitlich beschränkt.

Ein regionaler Issuer darf insbesondere nicht:
- Rechte für einen anderen Landesverband ausstellen;
- Bundeszuständigkeiten erzeugen;
- Root- oder Platform-Intermediate-Rechte erzeugen;
- Voting Authority erzeugen;
- seinen eigenen Delegationsrahmen erweitern.

## § 3 Nichtübertragung von Master- und Issuer-Schlüsseln

(1) Private Schlüssel einer übergeordneten Vertrauensebene werden nicht an eine nachgeordnete Vertrauensebene weitergegeben.

(2) Ein nachgeordneter Vertrauensbereich erhält ausschließlich einen eigenen privaten Schlüssel und den erforderlichen Nachweis seiner begrenzten Vertrauensstellung.

(3) Die Kompromittierung eines regionalen Issuer-Schlüssels darf nicht zur Kompromittierung des Root Trust, des Platform Intermediate oder anderer Regionen führen.

(4) Schlüsselmaterial darf nicht als allgemein zugängliche Datei, insbesondere nicht als ungeschützte PEM-Datei oder vergleichbarer Klartext-Export, bereitgestellt werden, soweit die maßgebliche technische Schlüsselklasse Non-Exportability verlangt.

## § 4 Schlüsselverwahrung und Mehrpersonenprinzip

(1) Besonders kritische Schlüsselklassen unterliegen einem Mehrpersonen- bzw. Schwellenverfahren (`m-of-n`).

(2) Das konkrete Schwellenverhältnis wird je Schlüsselklasse durch die technische Sicherheits- und Schlüsselrichtlinie festgelegt. Diese Ordnung schreibt kein einheitliches `3-of-5` für sämtliche Schlüsselklassen vor.

(3) Keine einzelne Person darf allein Erzeugung, Aktivierung, Wiederherstellung, Rotation oder endgültige Aufhebung eines zentralen Vertrauensankers bewirken.

(4) Schlüsselverwahrer (Key Custodians) üben ausschließlich die ihnen technisch und organisatorisch zugewiesene Verwahrungsfunktion aus. Die Funktion begründet kein Parteiamt und keine politische Entscheidungsbefugnis.

(5) Ein Parteiamt, insbesondere ein Vorsitzenden-, Vorstands- oder Schatzmeisteramt, vermittelt seinerseits keinen unmittelbaren Zugriff auf zentrale oder regionale private Schlüssel.

(6) Bestellung, Wechsel und Abberufung von Key Custodians sind so zu regeln, dass weder ein einzelnes Parteiorgan noch ein einzelner technischer Betreiber sämtliche Verwahrer in einem unkontrollierten Vorgang ersetzen kann. Staffelung, Unvereinbarkeiten, unabhängige Bestätigung und unveränderbare Nachweisführung sind vorzusehen.

## § 5 Bindung technischer Zugänge an OrganizationalAuthority

(1) Für politische oder organisatorische Funktionen ist `OrganizationalAuthority` der maßgebliche digitale Nachweis der bestehenden Zuständigkeit.

(2) `OrganizationalAuthority` muss auf die konkrete Wahl, Bestellung oder Entscheidung, die maßgebliche Satzungs- oder Ordnungsgrundlage, den zuständigen organisatorischen Bereich, den Geltungszeitraum und die zulässigen Fähigkeiten zurückführbar sein.

(3) Kryptographisch signierte Laufzeitnachweise sind nur kurzlebige technische Ableitungen aus einer bestehenden OrganizationalAuthority. Sie schaffen keine eigenständige Zuständigkeit.

(4) Eine technisch gültige Signatur genügt nicht, wenn die zugrunde liegende OrganizationalAuthority suspendiert, widerrufen, abgelaufen oder für die konkrete Handlung nicht zuständig ist.

(5) Die Wiederherstellung eines Authentisierungsmittels oder einer technischen Sitzung stellt eine suspendierte oder entzogene OrganizationalAuthority nicht wieder her.

## § 6 Technischer Quarantäne- und Sicherheitszugriff

(1) Bei einer konkreten Sicherheitsgefährdung dürfen hierzu ausdrücklich ermächtigte Security-Funktionen unverzüglich technische Sicherungsmaßnahmen treffen.

(2) Zulässige technische Maßnahmen umfassen insbesondere:
- Quarantäne einer Sitzung;
- Widerruf oder Sperrung eines kompromittierten Authentisierungsmittels;
- Beendigung eines privilegierten technischen Zugangs;
- Sperrung eines kompromittierten Service-Zugangs;
- Isolation eines kompromittierten Workloads;
- technische Eindämmung eines kompromittierten kryptographischen Schlüssels.

(3) Security-Funktionen dürfen aufgrund dieser technischen Befugnis nicht:
- ein Parteiamt entziehen;
- eine Person in ein Parteiamt einsetzen;
- eine politische oder organisatorische Zuständigkeit neu schaffen;
- eine suspendierte OrganizationalAuthority eigenmächtig wiederherstellen;
- einen Gebietsverband politisch übernehmen;
- die Governance des Voting Trust Domain verändern.

(4) Eine technische Quarantäne ist von einer politischen oder organisatorischen Suspendierung strikt zu trennen.

## § 7 Politische und organisatorische Suspendierung

(1) Die Suspendierung, Entziehung oder Wiederherstellung einer politischen oder organisatorischen Zuständigkeit richtet sich ausschließlich nach Gesetz, Satzung, der Organisations-, Zuständigkeits- und Kompetenzordnung und den Entscheidungen der jeweils zuständigen Parteiorgane.

(2) Technische Systeme vollziehen eine wirksame Suspendierung oder Entziehung, begründen sie aber nicht selbst.

(3) Maßnahmen gegen Gebietsverbände richten sich zusätzlich nach den satzungsmäßigen Regeln über Aufsicht und Eingriffe.

(4) Eine Maßnahme gegen einen Gebietsverband überträgt dessen Schlüssel, Datenzugriffe, Haushaltsbefugnisse oder sonstigen Verwaltungsrechte nicht automatisch auf den übergeordneten Gebietsverband.

## § 8 Widerruf, Rotation und Kompromittierung

(1) Jede Schlüsselklasse besitzt einen geregelten Lebenszyklus mit mindestens den Zuständen Erzeugung, Bereitstellung, Aktiv, Nur-Verifikation, Kompromittiert, Widerrufen, Außer Betrieb und Vernichtet oder gleichwertigen Zuständen.

(2) Kompromittierte, widerrufene, außer Betrieb genommene oder vernichtete Schlüssel dürfen unter derselben Schlüsselidentität nicht erneut für aktive Signatur oder Ausgabe verwendet werden.

(3) Bei Kompromittierung eines regionalen Issuers ist mindestens vorzusehen:

```text
Containment
-> Widerruf des kompromittierten Issuers
-> Ausstellung eines neuen regionalen Issuers
-> neue Schlüsselidentität
-> kontrollierte Erneuerung nachgeordneter Laufzeitschlüssel
-> Audit und Nachprüfung
```

(4) Bei Kompromittierung des Platform Intermediate ist eine kontrollierte Neu-Ausstellung der betroffenen Bund- und Regional-Issuer vorzusehen.

(5) Bei Kompromittierung des Root Trust ist ein vollständiges Root-Recovery- und Trust-Rebuild-Verfahren nach § 9 durchzuführen.

## § 9 Wiederherstellung und Verlust des Quorums

(1) Für den Verlust des erforderlichen Key-Custodian-Quorums, die Kompromittierung zentraler Vertrauensanker und andere systemische Vertrauensstörungen ist ein gesondertes Recovery-Verfahren vorzuhalten.

(2) Das Recovery-Verfahren trennt zwingend:
- rechtliche bzw. Governance-Autorisierung;
- Recovery Custody;
- technische Durchführung;
- unabhängige Nachprüfung.

(3) Eine einzelne Person oder ein einzelnes Parteiorgan darf einen zentralen Vertrauensanker nicht allein wiederherstellen.

(4) Nach Verwendung eines besonders geschützten Recovery-Verfahrens sind die hiervon betroffenen Schlüssel und Recovery-Materialien nach Maßgabe der Sicherheitsrichtlinie zu rotieren oder neu zu erzeugen.

(5) Parteischiedsgerichte können im Rahmen ihrer gesetzlichen und satzungsmäßigen Zuständigkeit Entscheidungen über Streitigkeiten, Rechtsbehelfe oder die Zulässigkeit einer Governance-Maßnahme treffen. Sie verwahren keine zentralen privaten Schlüssel und betreiben weder HSM/KMS noch technische Systemadministration.

## § 10 Regionale Betriebsfähigkeit bei zentraler Störung

(1) Der zentrale Root Trust darf nicht der technische Hot Path jeder gewöhnlichen regionalen Handlung sein.

(2) Ein berechtigter Gebietsverband darf innerhalb eines zuvor wirksam begrenzten und technisch nachweisbaren Delegationsrahmens vorübergehend weiterarbeiten, wenn die Verbindung zur zentralen Vertrauensinfrastruktur gestört ist.

(3) Die zulässige autonome Betriebsdauer, Freshness-Grenzen, RTO, RPO und Revoke-/Recovery-Ziele werden in INFRA/OPS technisch festgelegt und getestet. Ohne eine solche Festlegung darf keine unbegrenzte regionale Offline-Autonomie angenommen werden.

(4) Während einer zentralen Störung darf keine Erhöhung des regionalen Delegationsrahmens, keine Root- oder Bund-Eskalation und keine Erweiterung auf andere Regionen erfolgen.

## § 11 Unveränderbare Nachweisführung

(1) Schlüssel- und Vertrauensereignisse, insbesondere Erzeugung, Aktivierung, Delegation, Rotation, Widerruf, Quarantäne, Recovery und Änderungen des Verwahrer-Quorums, sind unveränderbar und nachvollziehbar zu protokollieren.

(2) Die Nachweisführung ist technisch so auszugestalten, dass nachträgliches Löschen oder Umschreiben historischer Sicherheits- und Governance-Ereignisse durch Identity-, Security-, Platform- oder politische Administratoren ausgeschlossen ist.

(3) Die technische Zielarchitektur umfasst append-only bzw. WORM-Speicherung, kryptographische Verkettung und einen unabhängigen externen Zeit- oder Integritätsanker oder eine gleichwertige unabhängige Absicherung.

(4) Berechtigte unabhängige Prüffunktionen und Parteischiedsgerichte erhalten im Rahmen ihrer Zuständigkeit lesenden Zugriff auf die für Prüfung oder Verfahren erforderlichen Nachweise, soweit Datenschutz, Wahlgeheimnis und sonstige gesetzliche Geheimhaltungspflichten gewahrt bleiben.

## § 12 Voting Trust Domain

(1) Wahl- und Abstimmungsschlüssel des geschützten Voting Trust Domain sind von der allgemeinen Trust-Hierarchie dieser Ordnung getrennt.

(2) Weder Root Trust, Platform Intermediate, Bund Issuer noch Regional Issuer begründen aus sich heraus Voting Authority oder Zugriff auf geheime Stimmabgaben.

(3) Einzelheiten des Voting Trust Domain richten sich nach der hierfür geltenden Wahl-, Abstimmungs- und Sicherheitsordnung sowie den einschlägigen technischen Governance-Regeln.

## § 13 Technische Konkretisierung und Geheimhaltung

(1) Kryptographische Algorithmen, Schlüsselformate, Cryptoperioden, Provider-Anforderungen und technische Protokolle werden in den jeweils geltenden technischen Sicherheits- und Trust-Profilen festgelegt.

(2) Diese technischen Profile dürfen die in Satzung und dieser Ordnung festgelegte Zuständigkeits- und Trennungsstruktur nicht abschwächen.

(3) Nicht in öffentlich zugängliche Parteidokumente aufzunehmen sind insbesondere:
- private Schlüssel oder Recovery Shares;
- konkrete HSM/KMS-Zugangsdaten und geheime Endpunkte;
- produktive Key IDs, soweit deren Veröffentlichung nicht ausdrücklich technisch vorgesehen ist;
- operative Notfallzugänge;
- Secret-Manager-Inhalte;
- persönliche Sicherheitsmerkmale der Custodians.

## § 14 Inkrafttreten

(1) Dieser Diskussionsentwurf entfaltet keine Rechtswirkung.

(2) Eine Schlüssel- und Vertrauensordnung tritt erst nach rechtlicher Prüfung und ordnungsgemäßem Beschluss des nach der Satzung zuständigen Parteiorgans in Kraft.

(3) Technische Umsetzung oder Erprobung vor Inkrafttreten begründet keine satzungsrechtliche Zuständigkeit.

# PACK-16A — German Legal and Governance Boundary

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

> **This document is a technical architecture assessment of a legal
> landscape. It is not legal advice, it is not a legal opinion, and it does
> not constitute a legal assessment.** Every mode below carries
> `LEGAL ASSESSMENT REQUIRED`. Nothing here authorises anything.

---

## 1. The separation this document exists to hold

```text
TECHNICAL CAPABILITY   ≠   LEGAL PERMISSIBILITY
```

The selected ballot model can express a nomination ballot. German law
decides whether it may be used for one, and for statutory nominations it
currently does not. Conflating the two is the single most likely way for
this project to cause real harm — a nomination conducted electronically
where the law requires paper risks *Zurückweisung des Wahlvorschlags*,
which disenfranchises the entire body it was meant to serve.

Permitted formulations throughout this pack:

```text
TECHNICAL ARCHITECTURE ONLY
LEGAL ASSESSMENT REQUIRED
NOT LEGALLY ACTIVATED
ELECTION-SPECIFIC AUTHORIZATION REQUIRED
```

Prohibited, absolutely, without a separate cited proof:

```text
LEGAL COMPLIANT · BVerfG COMPLIANT · APPROVED FOR PUBLIC ELECTIONS
BSI CERTIFIED · LEGALLY READY
```

---

## 2. BVerfG, 2 BvC 3/07 — the constitutional frame

**Bundesverfassungsgericht, Zweiter Senat, judgment of 3 March 2009, 2 BvC
3/07 and 2 BvC 4/07 (joined), BVerfGE 123, 39** `[E-41]`.

### 2.1 The two Leitsätze

**Leitsatz 1:**

> *"Der Grundsatz der Öffentlichkeit der Wahl aus Art. 38 in Verbindung mit
> Art. 20 Abs. 1 und Abs. 2 GG gebietet, dass alle wesentlichen Schritte der
> Wahl öffentlicher Überprüfbarkeit unterliegen, soweit nicht andere
> verfassungsrechtliche Belange eine Ausnahme rechtfertigen."*

Official English: *"The principle of public elections following from Art. 38
in conjunction with Art. 20(1) and (2) of the Basic Law requires that all
key steps of an election be subject to public scrutiny, insofar as other
constitutional interests do not justify an exception from such scrutiny."*

**Leitsatz 2 — the operative sentence:**

> *"Beim Einsatz elektronischer Wahlgeräte müssen die wesentlichen Schritte
> der Wahlhandlung und der Ergebnisermittlung vom Bürger zuverlässig und
> ohne besondere Sachkenntnis überprüft werden können."*

Official English: *"When electronic voting machines are used, it must be
possible for citizens to reliably scrutinise the key steps of the polling
process and the determination of the result without any specialist
knowledge."*

### 2.2 What the Court did **not** decide

**It did not prohibit electronic voting.** Four independent confirmations:

- Rn. 121: *"The legislator is not precluded from using electronic voting
  machines for elections, provided that the constitutionally required
  possibility of reliable scrutiny is guaranteed."* German, from the press
  release: *"Der Gesetzgeber ist nicht gehindert, bei den Wahlen
  elektronische Wahlgeräte einzusetzen, wenn die verfassungsrechtlich
  gebotene Möglichkeit einer zuverlässigen Richtigkeitskontrolle gesichert
  ist."*
- Rn. 115–116: how to secure transparency is the legislator's to design;
  the Court reviews only the outer limits.
- The **Tenor** struck the *Bundeswahlgeräteverordnung* for failing to
  secure verifiability; the enabling statute § 35 BWG was *"verfassungs-
  rechtlich zwar nicht zu beanstanden"*.
- Case commentary records that the judgment *"stellt keine grundsätzliche
  Absage an die Verwendung von Wahlcomputern dar"*.

**It also did not decide anything about cryptographic verifiability.** The
case concerned electronic recording devices. Any statement that a
cryptographic protocol is or is not BVerfG-compliant is an **extrapolation**
`[E-41]`, and this pack does not make one.

### 2.3 The four elements of the standard

| Element                    | Meaning                                                                 |
| -------------------------- | ------------------------------------------------------------------------- |
| **wesentliche Schritte**   | Both the *Wahlhandlung* and the *Ergebnisermittlung*, not one of them    |
| **vom Bürger**             | By the ordinary citizen — not by an expert body, not by a certifier      |
| **zuverlässig**            | Reliably, not in principle                                              |
| **ohne besondere Sachkenntnis** | Without specialist knowledge                                       |

Rn. 109 states it directly: *"All citizens must be able to reliably verify
and understand the key steps of the election without specialist technical
knowledge."*

### 2.4 Why this is the crux for cryptographic verifiability

The Court foreclosed the two obvious workarounds:

- **Rn. 123:** *"Restrictions of the ability of the public to scrutinise
  elections cannot be compensated by model devices being checked."*
  → Device certification does not substitute for citizen-scrutinisable
  steps.
- **Rn. 124:** *"Other comprehensive technical and organisational measures
  on their own are not suitable to compensate for a lack of possibilities to
  scrutinise the electoral process."*
  → Audits, ISMS and Common Criteria do not either.
- **Rn. 120:** *"Votes may not be stored exclusively in electronic form
  after they have been cast."* — the de-facto paper-record requirement for
  the devices at issue.
- **Rn. 125:** for computer-based voting machines *"no conflicting
  constitutional principles are ascertainable that could justify
  far-reaching restrictions on the principle of public elections"* — the
  secrecy of the ballot does not excuse opacity.

**The honest architectural reading, marked as inference:** a verification
act consisting of "check this ciphertext against the bulletin board" or
"verify this zero-knowledge proof" sits badly with *ohne besondere
Sachkenntnis*, because the citizen's confidence rests on a mathematical
claim she cannot herself evaluate. Whether **any** cryptographic scheme can
satisfy Rn. 109 is unresolved in German constitutional doctrine.

**This is precisely the design pressure Selene articulates from the
cryptographic side** — *"many voters may not really understand the purpose
of the encrypted ballot"* `[E-38]` — and it is the reason Selene is recorded
as **REQUIRES FURTHER RESEARCH** rather than dismissed: tracker-based
verifiability is materially closer to the German standard than
ciphertext-based verifiability. `OD-P16A-10` carries it.

---

## 3. BSI — what exists, and what conspicuously does not

| Item                                                                                                    | Status                                                                                 |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **BSI-CC-PP-0037-2008** — *Basissatz von Sicherheitsanforderungen an Online-Wahlprodukte*, v1.0, EAL2+  | **ARCHIVED** — *"ein archiviertes Schutzprofil, welches nicht mehr grundsätzlich für Produktzertifizierungen zu Verfügung steht"* `[E-53]` |
| **BSI-CC-PP-0121-2024** — *Protection Profile for E-Voting Systems for **non-political** Elections*, v1.0, EAL4+ ALC_FLR.2, CC:2022 R1, certified 20 Feb 2024, valid to 19 Feb 2034 | **CURRENT** `[E-53]` |
| **BSI TR-03169** — *IT-sicherheitstechnische Anforderungen zur Durchführung von **nicht-politischen** Online-Wahlen und -Abstimmungen* | Current; scope explicitly non-political `[E-54]` |
| **BSI**, *Ende-zu-Ende Verifizierbare Onlinewahlen: Handlungsleitfaden für Wahlorganisatoren*, 25 Apr 2025 | Published `[E-54]` |
| **BSI TR-02102-1** — *Kryptographische Verfahren: Empfehlungen und Schlüssellängen*, version **2026-01**, 23 Jan 2026 | Current; the parameter reference for PACK-16B `[E-52]` |

**Two facts matter more than the list.**

**First: citing PP-0037 as the current German protection profile is an
error.** It is archived and superseded. Any prior EPD² material doing so
should be corrected; none in this baseline does.

**Second, and structurally decisive: the entire current German technical
framework for online voting is scoped to non-political elections by
construction.** BSI's own portal states the scope as *"Bei der Durchführung
von **nicht-politischen** Abstimmungen und Wahlen"* `[E-54]`. PP-0121 and
TR-03169 both carry *nicht-politisch* in their titles. **There is no German
technical baseline for political online elections, and the exclusion is
deliberate, tracking the constitutional constraint.**

For EPD² this cuts both ways. The framework that exists — PP-0121,
TR-03169, and the E2E-verifiability guidance, which explicitly includes
*"Ende-zu-Ende-Verifizierbarkeit"* and addresses coercion resistance
`[E-54]` — **is exactly the framework covering internal party votes**, which
is the only class this architecture is aimed at. And the framework that
does not exist marks the boundary this architecture may not cross.

**`BSI CERTIFIED` is a prohibited claim.** Nothing is certified; no
certification has been sought; and PP-0121 governs a class of election, not
this system.

---

## 4. Party law — where binding electronic voting is and is not permitted

### 4.1 § 15 Abs. 2a PartG — the enabling provision

Parteiengesetz as amended by the 11. PartGÄndG of 27 February 2024
(BGBl. 2024 I Nr. 70), in force 5 March 2024 `[E-49]`:

> *"Der Vorstand kann entscheiden,
> 1. dass die Stimmabgabe unter Wahrung der Rechte aller Stimmberechtigten
> **bei Beschlussfassungen und Wahlen** ganz oder teilweise im Wege der
> **elektronischen Kommunikation** erfolgen kann, wenn dabei die
> **Sicherheit, auch mit Blick auf den Schutz personenbezogener Daten, auf
> dem Stand der Technik** gewährleistet ist, und
> 2. welche Kommunikationsmittel dabei eingesetzt werden.
> Dies gilt nicht, soweit die Satzung etwas anderes bestimmt."*

**Binding electronic votes are permitted for internal party matters** —
*Beschlussfassungen* (resolutions) **and** *Wahlen*, which by § 15 Abs. 2
includes *Vorstandswahlen*. Conditions: a *Vorstand* decision; the rights of
all entitled voters preserved; security **auf dem Stand der Technik**
including data protection; and the *Satzung* may exclude it.

§ 15 Abs. 2 continues to require **secrecy** for board elections, so the
electronic channel must implement a genuine secret ballot.

§ 9 Abs. 1 PartG now permits *Präsenz*, **virtuelle** and two forms of
**hybride** party congresses `[E-49]`.

**"Stand der Technik" is the load-bearing undefined term.** It is where BSI
TR-03169, PP-0121 and TR-02102-1 become the de facto benchmarks. **No
source states that mapping**, and it is recorded as an inference and as
`OD-P16A-11`.

### 4.2 The constitutional objection that accompanied the enabling provision

§ 15 Abs. 2a was enacted **over a published expert constitutional
objection**, and it has not been tested at the BVerfG. Prof. Dr. Sophie
Schönberger (PRuF, HHU Düsseldorf), Stellungnahme of 20 November 2023,
Ausschussdrucksache 20(4)340-A, assessed the provision as
*"verfassungsrechtlich als auch verfassungspolitisch höchst problematisch"*,
with the core objection `[E-55]`:

> *"bei elektronischen Abstimmungssystemen **ohne Kenntnis und Verständnis
> des verwandten Algorithmus** die konkrete Abstimmungssituation **nicht
> nachvollzogen** werden kann."*

**That is the BVerfG Rn. 109 argument transposed into party law, verbatim
in substance.** Its architectural consequence is not defensive but
directive: **a system that can demonstrate lay-comprehensible verifiability
answers the strongest published objection to its own legal basis.** This is
a design constraint, not a compliance box, and it is why
`PACK-16A-ACCESSIBILITY-REQUIREMENTS.md` §4 treats plain-language
verification as a protocol-level requirement rather than a frontend concern.

### 4.3 Candidate nomination — the hard boundary

§ 17 PartG:

> *"Die Aufstellung von Bewerbern für Wahlen zu Volksvertretungen muss in
> **geheimer Abstimmung** erfolgen. Die Aufstellung regeln **die Wahlgesetze
> und die Satzungen der Parteien**."* `[E-50]`

**Sentence 2 delegates outward to the Wahlgesetze**, so PartG permissions do
not override BWahlG requirements. The operative guidance is the
Bundeswahlleiterin's *Leitfaden Aufstellungsversammlung*, Stand September
2024, for the 2025 Bundestag election `[E-51]`:

> *"Eine solche Versammlung setzt nach herrschender Meinung die
> **gleichzeitige körperliche Anwesenheit** der stimmberechtigten Personen
> **an einem Ort** voraus."*

> *"**Elektronische Verfahren können nur zur Vorermittlung, Sammlung und
> Vorauswahl der Bewerbungen benutzt werden**, also nur im Vorfeld und als
> Vorverfahren zur eigentlichen, **schriftlichen mit Stimmzetteln und
> geheim** durchzuführenden Abstimmung."*

> *"Die Gelegenheit, sich **nur digital** vorzustellen, **genügt danach
> nicht**."*

> *"Der Grundsatz der **Öffentlichkeit der Wahl** gebietet, dass alle
> wesentlichen Schritte der Wahl öffentlicher Überprüfbarkeit unterliegen."*
> — the BVerfG Leitsatz imported directly into operative electoral guidance.

> *"Der Grundsatz der geheimen Wahl erfordert eine Abstimmung von
> **mindestens drei Personen**."*

Cited provisions: § 21 Abs. 3 BWahlG, § 27 Abs. 5 BWahlG, § 17 PartG.

**A correction to a common belief, recorded because getting it wrong is
costly:** the current rule is **not** "digital nomination with subsequent
postal or in-person confirmation". That confirmation model was the
**temporary COVID-era construction** (draft § 52 Abs. 4 BWahlG excluding the
*Schlussabstimmung* from electronic procedure) `[E-51]`. Under the 2025
guidance the position is **stricter**: the assembly itself must be a
physical *Präsenzversammlung* with written secret paper ballots, and no
Briefwahl alternative is offered for the *Schlussabstimmung*.

**Marked as inference:** the restriction rests on *herrschende Meinung* plus
Bundeswahlleiterin guidance interpreting § 21 BWahlG rather than on an
explicit statutory prohibition, which makes it legislatively movable. It is
nonetheless the operative rule, and deviation risks *Zurückweisung des
Wahlvorschlags*.

### 4.4 The verified boundary

| Domain                                                             | Binding online vote? | Basis                                                                                     |
| ------------------------------------------------------------------ | -------------------- | ------------------------------------------------------------------------------------------- |
| **Parteitagsbeschlüsse** (party resolutions)                       | **YES**              | § 15 Abs. 2a Nr. 1 PartG; § 9 Abs. 1 PartG `[E-49]`                                        |
| **Vorstandswahlen** (internal board elections)                     | **YES**, must be *geheim* | § 15 Abs. 2a + § 15 Abs. 2 PartG `[E-49]`                                            |
| **Aufstellung von Wahlbewerbern** (Bundestag, Landtag)             | **NO**               | § 17 PartG → § 21 Abs. 3 / § 27 Abs. 5 BWahlG; h.M. and Bundeswahlleiterin guidance `[E-50]`, `[E-51]` |
| **Public political elections** (Kommunal, Land, Bund, Referendum)  | **NO**               | No legal basis; BVerfG standard unmet; no BSI framework `[E-41]`, `[E-54]`                 |

### 4.5 Vereinsrecht baseline

The **VMVDigG** (*Gesetz zur Ermöglichung hybrider und virtueller
Mitgliederversammlungen im Vereinsrecht*), in force 21 March 2023, amended
§ 32 BGB to make hybrid and virtual member assemblies permanently available
for associations generally `[E-49]`. Parties are *Vereine* under § 2 PartG,
so § 32 BGB is the residual baseline where PartG is silent — an inference,
marked as such.

---

## 5. The nine legal modes

| Mode | Class                                          | Technical suitability                       | Required legal basis                              | Secrecy level              | Public scrutiny required           | Accessibility           | Auditability            | Remote-voting implications                   | Unresolved legal questions                                                       | Activation authority                | **Default state**            |
| ---- | ---------------------------------------------- | ------------------------------------------- | -------------------------------------------------- | -------------------------- | ---------------------------------- | ----------------------- | ----------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------- | ---------------------------- |
| **A** | Internal **non-binding** party consultation   | **Suitable** — `EPD2-HOM-1`                 | Satzung; Vorstand decision                          | Secret recommended         | Internal; result published          | Full                    | Full from the record    | Lowest stakes; coercion risk still real      | Whether *advisory_consultation* may extend beyond members (PACK-15 `OD-P15-08`)   | Election Board                      | **not activated**            |
| **B** | Internal **binding** party vote (Beschluss)   | **Suitable** — `EPD2-HOM-1`                 | **§ 15 Abs. 2a Nr. 1 PartG** + Satzung + Vorstand   | Secret where required       | Internal + auditor                  | Full                    | Full                    | Coercion mitigation limited to §5 of the coercion boundary | What *"Stand der Technik"* requires; untested at the BVerfG `[E-55]`  | Legal Activation Authority + Board  | **not activated**            |
| **C** | Candidate and nomination procedure            | **Suitable for internal pre-selection only** | § 17 PartG → BWahlG                                 | **Secret, statutory**       | **Öffentlichkeitsgrundsatz applies** | Full                    | Full                    | **Statutory nomination requires physical presence and paper** `[E-51]` | Whether the h.M. is legislatively movable                | **prohibited for statutory nomination** | **PROHIBITED**          |
| **D** | Internal organizational election (Vorstand)   | **Suitable** — `EPD2-HOM-1`                 | **§ 15 Abs. 2a + § 15 Abs. 2 PartG**                | **Secret, mandatory**       | Internal + auditor                  | Full                    | Full                    | Small bodies: §6 of the profile matrix        | Same as B; plus small-electorate secrecy in practice                              | Legal Activation Authority + Board  | **not activated**            |
| **E** | Non-political online election (Verein, Gremium) | **Suitable** — `EPD2-HOM-1`               | § 32 BGB / Satzung; **BSI PP-0121 / TR-03169 are the applicable benchmarks** `[E-53]`, `[E-54]` | Per Satzung | Per Satzung        | Full                    | Full                    | The class BSI's framework actually addresses  | Whether certification is expected in practice                                     | Election Board                      | **not activated**            |
| **F** | **Municipal political election**              | **not assessed as permissible**             | Kommunalwahlrecht — none permits it                 | Constitutional              | **Öffentlichkeitsgrundsatz**        | Statutory               | Statutory               | —                                             | Everything                                                                        | **none exists**                     | **PROHIBITED BY DEFAULT**    |
| **G** | **Land election**                             | **not assessed as permissible**             | Landeswahlrecht — none permits it                   | Constitutional              | **Öffentlichkeitsgrundsatz**        | Statutory               | Statutory               | —                                             | Everything                                                                        | **none exists**                     | **PROHIBITED BY DEFAULT**    |
| **H** | **Bundestag election**                        | **not assessed as permissible**             | BWahlG — does not permit it                         | Constitutional              | **BVerfG Leitsatz 1 and 2**         | Statutory               | Statutory               | —                                             | Whether Rn. 109 can ever be met cryptographically `[E-41]`                        | **none exists**                     | **PROHIBITED BY DEFAULT**    |
| **I** | **Referendum / constitutional vote**          | **not assessed as permissible**             | None at federal level                               | Constitutional              | **Öffentlichkeitsgrundsatz**        | Statutory               | Statutory               | —                                             | Everything                                                                        | **none exists**                     | **PROHIBITED BY DEFAULT**    |

```text
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT
```

Modes **F, G, H and I** are prohibited by default and may not be activated
by any configuration. A context declaring one is refused at configuration
time with `VOTING_CONTEXT_LEGAL_BASIS_MISSING`. **Removing that prohibition
is a Canon-level governance act, not a setting.**

Mode **C** is prohibited **for statutory nomination**; the internal
pre-selection use in the same row is permitted, and the two must be
distinguishable in configuration rather than by convention.

---

## 6. Council of Europe CM/Rec(2017)5

Adopted 14 June 2017 at the 1289th meeting of the Ministers' Deputies;
replaces Rec(2004)11. **Soft law — a Recommendation, not binding** — and
the reference standard cited by ODIHR and the Venice Commission `[E-56]`.

| Standard | Text                                                                                                                                | EPD² posture                                                                       |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **1**    | *"The voter interface of an e-voting system shall be easy to understand and use by all voters."*                                     | **specified** — accessibility requirements §2; aligns with *ohne besondere Sachkenntnis* |
| **2**    | Persons with disabilities and special needs vote independently                                                                       | **specified** — accessibility requirements §3                                       |
| **3**    | *"Unless channels of remote e-voting are universally accessible, they shall be only an additional and optional means of voting."*    | **adopted** — electronic voting is an additional channel, never the sole one        |
| **10**   | *"The voter's intention shall not be affected by the voting system, or by any undue influence."*                                     | **bounded** — coercion boundary §1; unmitigated cases named                         |
| **15**   | Voter can verify intention is accurately represented and the sealed vote entered the box unaltered                                   | **specified** — challenge/spoil + confirmation code                                 |
| **17**   | *"sound evidence that each authentic vote is accurately included"*                                                                   | **specified** — published record + independent verifier                             |
| **18**   | *"sound evidence that only eligible voters' votes have been included"*                                                               | **partially** — supplied by PACK-15 plus the aggregate count check `[E-06]`; **not** ballot-level eligibility verifiability |
| **19**   | Secrecy at all stages                                                                                                                | **specified**, bounded by §3.4 of the ballot model                                   |
| **23**   | *"An e-voting system shall not provide the voter with proof of the content of the vote cast for use by third parties."*              | **specified** — `BM-03`                                                             |
| **24**   | No disclosure of vote counts before the ballot box closes                                                                            | **specified** — `ADR-094`, `BM-21`                                                  |
| **25**   | *"E-voting shall ensure that the secrecy of previous choices recorded and erased by the voter before issuing his or her final vote is respected."* | **not applicable** — no revoting; and `SU-04` binds any future profile |
| **26**   | Counting must not permit reconstructing a link between the unsealed vote and the voter                                               | **specified** — no individual ballot is decrypted                                   |
| **27**   | *"Member States that introduce e-voting shall do so in a gradual and progressive manner."*                                           | **adopted** — the PACK-16A…D sequencing is this principle applied                   |
| **30**   | *"Any observer shall be able to observe the count of the votes."*                                                                    | **specified** — `RS-02`, `BB-36`; the CoE analogue of the Öffentlichkeitsgrundsatz  |
| **31**   | Transparency in all aspects                                                                                                          | **specified** — publication requirements throughout                                 |

**Standard 18 is the honest gap.** Ballot-level eligibility verifiability
would require a link between eligibility and the ballot, which is exactly
what this architecture forbids. What EPD² can offer is the check
ElectionGuard names: that the number of ballots cast does not exceed the
number of participants entitled `[E-06]`. That is weaker than Standard 18
as written, and saying so is preferable to claiming the standard is met.

---

## 7. Comparative note — the frameworks that do exist

Germany has no binding technical framework for political online elections.
Two comparators are recorded so that "ready" cannot be defined downwards:

- **Switzerland, OEV/VEleS (SR 161.116)** — complete and individual
  verifiability, control components with diverse design and independent
  operation, independent examination commissioned by the Federal
  Chancellery, source-code publication, and **a symbolic and a cryptographic
  proof of protocol compliance** `[E-45]`. EPD² does not meet the last of
  these and **does not claim to** (`RR-09`).
- **Estonia** — the largest deployment, and per ODIHR's June 2025 Opinion
  **still without a statutory definition of individual or universal
  verifiability** `[E-40]`. Deployment scale is not a compliance argument.

---

## 8. The governance gate

**No election profile may be enabled for any context without all ten of the
following.** Each is a document or an act, produced by a named party, and
absence of any one is a refusal rather than a risk acceptance.

| # | Gate item                                | Produced by                       | Evidence                                          |
| - | ---------------------------------------- | --------------------------------- | ------------------------------------------------- |
| 1 | **Legal basis**                          | Legal Activation Authority        | Written basis citing the provision relied on      |
| 2 | **Election-specific authorization**      | Legal Activation Authority + Board| Recorded decision, per context, published         |
| 3 | **Approved election profile**            | Election Board                    | Manifest with profile, contests and counting rule |
| 4 | **Independent security assessment**      | External party                    | Report, published or summarised publicly          |
| 5 | **Accessibility assessment**             | External or qualified internal    | Report against `FIR-INV-012`                      |
| 6 | **Operational readiness evidence**       | Election Officer                  | Readiness record including mirror availability    |
| 7 | **Approved key ceremony**                | Ceremony Coordinator + Trustees   | Published ceremony record and public key evidence |
| 8 | **Incident and recovery plan**           | Incident Commander + Board        | Plan naming abort, annul and re-run authorities   |
| 9 | **Public-verifiability plan**            | Election Board                    | Named mirrors, named independent verifier (`BM-28`) |
| 10| **Data-protection assessment**           | DPO                               | DPIA covering the context class                   |

### 8.1 Permitted outcomes of the gate

```text
ACTIVATE for this context
ACTIVATE with named conditions
DEFER pending a named gate item
REFUSE — and hold the vote by another means
```

**The fourth outcome is a normal result, not a failure.** For a context
with material coercion risk, a small electorate, or a legal basis that does
not clearly cover it, deciding to hold the vote on paper or in person is
the correct engineering answer as well as the correct legal one.
`RS-07` says the same thing about role separation.

### 8.2 What the gate may never be used to do

```text
It may not activate modes F, G, H or I.
It may not activate mode C for a statutory nomination.
It may not waive an inherited invariant.
It may not lower disclosure_min_cell.
It may not reduce k or n for a small electorate (TP-06).
It may not be delegated to an operator, a flag or a default.
```

---

## 9. Legal sources — pointer table

> **All PACK-16A Evidence IDs are canonically defined in
> `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md`.**

**This table is a pointer, not a registry.** It defines no identifier,
introduces no identifier, and carries no field the canonical registry does
not carry. Each entry below names the source in short form and directs the
reader to its single canonical definition — including the full source
title, issuing institution, version and date, source type, URL, relevant
section, property supported, scope of support, limitations and the list of
documents that cite it.

| ID     | Source, in short                                                                                              | Canonical definition                          |
| ------ | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `E-41` | BVerfG, Zweiter Senat, 3 March 2009, **2 BvC 3/07, 2 BvC 4/07**, BVerfGE 123, 39 — the *Wahlcomputer* judgment | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-49` | **Parteiengesetz** i.d.F. 11. PartGÄndG (in force 05.03.2024) — §§ 9, 15; and **VMVDigG** amending § 32 BGB    | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-50` | **§ 17 PartG**; **§ 21 Abs. 3 Satz 1 BWahlG**; **§ 27 Abs. 5 BWahlG**                                         | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-51` | **Die Bundeswahlleiterin**, *Leitfaden Aufstellungsversammlung*, Stand September 2024; Bundestag WD 3-3000-249/20 | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9  |
| `E-52` | **BSI TR-02102-1**, version **2026-01**, 23 January 2026                                                      | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-53` | **BSI-CC-PP-0037-2008** (archived) and **BSI-CC-PP-0121-2024** (current, non-political scope)                 | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-54` | **BSI TR-03169** and the BSI E2E-verifiability guidance of 25.04.2025; the BSI Online-Wahlen portal            | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-55` | **Schönberger**, *Stellungnahme*, 20.11.2023, Ausschussdrucksache **20(4)340-A**; BT-Drs. **20/9147**          | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |
| `E-56` | **Council of Europe CM/Rec(2017)5**, adopted 14 June 2017                                                     | `PACK-16A-PROTOCOL-EVIDENCE-MATRIX.md` §9     |

Also cited in this document and defined in the same canonical registry:
`E-06` (§3.1), `E-38` (§8), `E-40` (§6, Estonia), `E-45` (§7, Swiss
OEV/VEleS).

**UNVERIFIED items, recorded in the canonical entries and relied on
nowhere:** the verbatim German body text at the cited Randnummern
(paragraph attribution is confirmed by the official English translation and
by an independent Bundestag citation); the current text of § 32 BGB; the
version number of TR-03169; the scope of BSI-CC-PP-0122-2024; the enacted
text and expiry of the COVID-era § 52 BWahlG.

**TECHNICAL ARCHITECTURE ONLY. LEGAL ASSESSMENT REQUIRED. NOT LEGALLY
ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

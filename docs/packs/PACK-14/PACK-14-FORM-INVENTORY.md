# PACK-14 — Form Inventory

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Required by `FIR-FORM-002`. Fifteen forms and official documents, each with
a provisional form ID, a domain owner, an intended submitter, a receiving
authority, a basis, a confidentiality class, a signature or authentication
class, a workflow, a retention class and the responsible future pack.

Form IDs are **provisional** until the canonical forms framework
(`FIR-FORM-001`) exists and assigns them.

## 1. Inventory

| Form ID    | Name (DE)                                    | Submitter                  | Receiving authority     | Basis                             | Confidentiality | Auth class required     | Attachments       | Workflow                                           | Retention class     |
| ---------- | -------------------------------------------- | -------------------------- | ----------------------- | --------------------------------- | --------------- | ----------------------- | ----------------- | -------------------------------------------------- | ------------------- |
| `F-P14-01` | Kontoregistrierung                           | Any person                 | Account Registry        | Platform terms; `FIR-ROADMAP-004` | INTERNAL        | `none` → `low`          | none              | submit → verify contact → activate                 | account record      |
| `F-P14-02` | E-Mail-Bestätigung                           | Account holder             | Account Registry        | Platform terms                    | INTERNAL        | `low`                   | none              | request → confirm                                  | contact history     |
| `F-P14-03` | Telefonnummer-Bestätigung                    | Account holder             | Account Registry        | Platform terms                    | INTERNAL        | `low`                   | none              | request → confirm                                  | contact history     |
| `F-P14-04` | Passkey einrichten                           | Account holder             | Authentication          | ADR-081                           | INTERNAL        | `substantial` + step-up | none              | initiate → attest → name → confirm                 | credential metadata |
| `F-P14-05` | Passkey entfernen                            | Account holder             | Authentication          | ADR-081                           | INTERNAL        | `high` + step-up        | none              | select → confirm consequences → remove             | credential metadata |
| `F-P14-06` | Zwei-Faktor-Verfahren einrichten             | Account holder             | Authentication          | ADR-082                           | INTERNAL        | `substantial` + step-up | none              | choose → enroll → verify → confirm                 | credential metadata |
| `F-P14-07` | Zwei-Faktor-Verfahren entfernen              | Account holder             | Authentication          | ADR-082                           | INTERNAL        | `substantial` + step-up | none              | select → confirm downgrade → remove                | credential metadata |
| `F-P14-08` | Wiederherstellungscodes erzeugen             | Account holder             | Authentication          | ADR-085                           | CONFIDENTIAL    | `substantial` + step-up | none              | request → display once → confirm stored            | credential metadata |
| `F-P14-09` | Kontowiederherstellung beantragen            | Account holder or assisted | Recovery                | ADR-085                           | CONFIDENTIAL    | `none` (entry)          | optional evidence | request → assess → verify → cooling-off → complete | recovery evidence   |
| `F-P14-10` | Verdächtige Anmeldung bestätigen oder melden | Account holder             | Session Security        | ADR-083                           | INTERNAL        | `low`                   | none              | notify → confirm or report → response              | suspicious activity |
| `F-P14-11` | Kontaktdaten ändern                          | Account holder             | Account Registry        | ADR-084                           | INTERNAL        | `substantial` + step-up | none              | request → verify new → notify both → apply         | contact history     |
| `F-P14-12` | Aktive Sitzungen beenden                     | Account holder             | Session Security        | ADR-083                           | INTERNAL        | `substantial` + step-up | none              | list → select → confirm → revoke                   | session history     |
| `F-P14-13` | Konto schließen                              | Account holder             | Account Registry        | ADR-084                           | INTERNAL        | `high` + step-up        | none              | request → cooling-off → close → retain/anonymize   | account record      |
| `F-P14-14` | Identitätsprüfung einreichen                 | Account holder or assisted | Identity Proofing       | ADR-086; canon 19d.2              | **RESTRICTED**  | `substantial`           | identity evidence | submit → evidence → decide or review               | proofing evidence   |
| `F-P14-15` | Privilegierte Wiederherstellung genehmigen   | Recovery Reviewer          | Identity Administration | ADR-085, ADR-087                  | **RESTRICTED**  | `high` + PACK-12 grant  | case evidence     | assess → dual control → decide                     | privileged action   |

## 2. Official documents produced

| Document                                              | Produced by                                          | Class             | Immutable |
| ----------------------------------------------------- | ---------------------------------------------------- | ----------------- | --------- |
| Einreichungsbestätigung (submission receipt)          | Every form above                                     | official receipt  | yes       |
| Sicherheitsbenachrichtigung (security alert)          | `F-P14-04`, `05`, `06`, `07`, `09`, `10`, `11`, `12` | security alert    | yes       |
| Entscheidungsmitteilung (decision notice)             | `F-P14-09`, `13`, `14`, `15`                         | official decision | yes       |
| Wiederherstellungsnachweis (recovery evidence record) | `F-P14-09`                                           | evidence          | yes       |

## 3. Coverage statement

Every user-facing identity operation named in
`PACK-14-WORKFLOW-MATRIX.md` has a form here. **None is implemented.**
Paper equivalents for the assisted and offline channels are **deferred** to
`FIR-INCLUSION-001`'s own round and are named here rather than omitted.

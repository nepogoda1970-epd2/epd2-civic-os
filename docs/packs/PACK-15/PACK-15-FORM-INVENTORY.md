# PACK-15 — Form Inventory

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Required by `FIR-FORM-002`. Nine forms and official documents, each with a
provisional form ID, an owner, an intended submitter, a receiving
authority, a basis, a confidentiality class, an authentication class, a
workflow, a retention class and the boundary side it belongs to.

Form IDs are **provisional** until the canonical forms framework
(`FIR-FORM-001`) exists and assigns them.

---

## 1. Inventory

| Form ID    | Name (DE)                                                | Submitter                         | Receiving authority                     | Basis                        | Confidentiality  | Auth class required         | Attachments        | Workflow                                        | Retention class        | Side                 |
| ---------- | -------------------------------------------------------- | --------------------------------- | --------------------------------------- | ---------------------------- | ---------------- | --------------------------- | ------------------ | ----------------------------------------------- | ---------------------- | -------------------- |
| `F-P15-01` | Antrag auf Prüfung der Stimmberechtigung                 | Member; assisted helper           | Eligibility Service                     | `FIR-ROADMAP-005`; rule-set  | INTERNAL         | `substantial`               | none               | submit → evaluate → decide or review            | eligibility case       | identity             |
| `F-P15-02` | Nachweise zur Stimmberechtigung einreichen               | Member; assisted helper           | Eligibility Service                     | Rule-set; ADR-089            | **CONFIDENTIAL** | `substantial`               | evidence reference | submit → review → decide                        | eligibility evidence   | identity             |
| `F-P15-03` | Widerspruch gegen die Entscheidung zur Stimmberechtigung | Member                            | Dispute Reviewer                        | ADR-098                      | **CONFIDENTIAL** | `substantial`               | optional evidence  | submit → assign → decide → notify               | dispute case           | identity             |
| `F-P15-04` | Ausgabe des Stimmzugangs beantragen                      | Member                            | Credential Issuer                       | ADR-092                      | INTERNAL         | `substantial` + assertion   | none               | present assertion → validate → issue → deliver  | credential evidence    | voting               |
| `F-P15-05` | Verlorenen oder abgelaufenen Stimmzugang melden          | Member                            | Credential Issuer + Eligibility Officer | ADR-092, ADR-095             | **CONFIDENTIAL** | `substantial`               | none               | report → assess → revoke-then-reissue or refuse | credential evidence    | both, as two records |
| `F-P15-06` | Überprüfung eines Widerrufs beantragen                   | Member                            | Dispute Reviewer                        | ADR-095, ADR-098             | **CONFIDENTIAL** | `substantial`               | optional evidence  | submit → assign → decide → notify               | dispute case           | identity             |
| `F-P15-07` | Unterstützung bei der Teilnahme anfordern                | Member; representative on request | Inclusion support                       | `FIR-INCLUSION-001`          | INTERNAL         | `low` (entry)               | none               | request → arrange → confirm                     | assistance record      | identity             |
| `F-P15-08` | Protokoll einer unterstützten Ausgabe                    | Helper / operator                 | Credential Issuer                       | `FIR-INCLUSION-001`; ADR-092 | **RESTRICTED**   | `substantial` + attribution | none               | record → countersign → receipt                  | assisted-action record | voting               |
| `F-P15-09` | Antrag auf unabhängige Prüfung                           | Member; Governance                | Independent Auditor                     | `FIR-ROLE-003`; ADR-097      | **RESTRICTED**   | `substantial`               | case references    | submit → scope → review → report                | auditor evidence       | audit                |

**`F-P15-05` is the form that must not become a link.** It is deliberately
recorded as **two independent records** — an identity-side report and a
voting-side revocation — that share no key and are correlated only by the
governed reissue decision, which is itself recorded on both streams
without a common reference. An implementation that stores it as one case
spanning both sides has recreated the pairing through the support desk.

---

## 2. Official documents produced

| Document                                                                | Produced by                 | Class             | Immutable |
| ----------------------------------------------------------------------- | --------------------------- | ----------------- | --------- |
| Einreichungsbestätigung (submission receipt)                            | Every form above            | official receipt  | yes       |
| Entscheidungsmitteilung Stimmberechtigung (eligibility decision notice) | `F-P15-01`, `F-P15-02`      | official decision | yes       |
| Widerspruchsentscheidung (dispute decision)                             | `F-P15-03`, `F-P15-06`      | official decision | yes       |
| Ausgabebestätigung (issuance confirmation)                              | `F-P15-04`                  | official receipt  | yes       |
| Widerrufsmitteilung (revocation notice)                                 | `F-P15-05`, revocation acts | official notice   | yes       |
| Unterstützungsnachweis (assisted-action receipt)                        | `F-P15-07`, `F-P15-08`      | evidence          | yes       |
| Prüfbericht (independent audit report)                                  | `F-P15-09`                  | audit evidence    | yes       |

**No document above states, implies or can be used to infer a ballot
choice, a person-level casting act, or any pre-closure result.** The
issuance confirmation confirms an issuance; it does not confirm
participation.

---

## 3. Coverage statement

Every participant-facing operation named in
`PACK-15-WORKFLOW-MATRIX.md` has a form here. **None is implemented.**
Paper equivalents for the assisted and offline channels are **deferred** to
`FIR-INCLUSION-001`'s own round and are named here rather than omitted.

---

## 4. Forms deliberately not created

| Form that will be proposed                         | Why it does not exist                                                         |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| „Teilnahmebestätigung anfordern" (proof of voting) | It would be a person-level participation statement, and it would be coercible |
| „Stimme zurückziehen" (withdraw a cast ballot)     | Requires the person→ballot link; the remedy is at context level only          |
| „Stimmzugang übertragen" (transfer a credential)   | Transfer is not a supported operation                                         |
| „Teilnahmeliste einsehen" (view participants)      | An enumeration of participation                                               |

Each of these has a plausible member-service justification. Each is
refused, and the refusal is explained to the participant in
`PACK-15-CONTENT-CATALOGUE-DE.md` §11 rather than presented as a missing
feature.

# PACK-15 — Field Catalogue

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Fields, types, requiredness, dependencies and validation, per form.
Required by `FIR-FORM-002`. Validation messages are in
`PACK-15-CONTENT-CATALOGUE-DE.md`.

## Conventions

`R` required · `O` optional · `C` conditional (the condition is stated).

**No field in any form below is a global identifier, and no form collects
any attribute from the prohibited set** in
`PACK-15-ATTRIBUTE-MINIMIZATION-MATRIX.md` §1. In particular no form
collects a date of birth, an address, a member number or an account
identifier, and no form on the voting side collects anything about the
person at all.

---

## `F-P15-01` Antrag auf Prüfung der Stimmberechtigung

| Field                      | Type        | Req | Validation                                                       | Note                                                    |
| -------------------------- | ----------- | --- | ---------------------------------------------------------------- | ------------------------------------------------------- |
| `voting_context_reference` | reference   | R   | Must be an active context the participant may see                | The only context-identifying field                      |
| `participation_class`      | enum        | C   | Required where the context offers more than one                  | From the context's own taxonomy                         |
| `declaration_accuracy`     | declaration | R   | Explicitly checked; never pre-checked                            | „Meine Angaben sind vollständig und richtig."           |
| `conflict_declaration`     | declaration | C   | Required where the rule-set contains `EC-09`                     | A declaration, not an investigation                     |
| `assisted_by`              | reference   | C   | Required in the assisted path                                    | Helper attribution (`FIR-INCLUSION-001`)                |
| `preferred_channel`        | enum        | O   | From the participant's confirmed channels                        | For notifications only                                  |

## `F-P15-02` Nachweise zur Stimmberechtigung einreichen

| Field                  | Type        | Req | Validation                                        | Note                                                    |
| ---------------------- | ----------- | --- | ------------------------------------------------- | ------------------------------------------------------- |
| `case_reference`       | reference   | R   | An open eligibility case of the submitter          | —                                                       |
| `evidence_reference`   | reference   | R   | A PACK-11 governed document reference              | **Never the content, never in an event, never in a log**|
| `evidence_class`       | enum        | R   | From the rule-set's declared evidence classes      | —                                                       |
| `submitter_statement`  | text        | O   | Free text; never the reason code                   | Additional, never authoritative                         |
| `consent_declaration`  | declaration | R   | Purpose-limited and explicit                       | —                                                       |
| `assisted_by`          | reference   | C   | Assisted path                                      | —                                                       |

## `F-P15-03` Widerspruch gegen die Entscheidung zur Stimmberechtigung

| Field                    | Type        | Req | Validation                                                             | Note                                                |
| ------------------------ | ----------- | --- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| `decision_reference`     | reference   | R   | The participant's own decision                                          | —                                                   |
| `ground`                 | enum        | R   | From the twelve registered dispute grounds                              | Free text is additional, never the ground           |
| `statement`              | text        | R   | —                                                                       | —                                                   |
| `evidence_reference`     | reference   | O   | PACK-11 reference                                                       | —                                                   |
| `remedy_sought`          | enum        | R   | `re_evaluation`, `manual_review`, `scope_correction`, `window_extension`| **`ballot_correction` is deliberately absent**      |
| `assisted_by`            | reference   | C   | Assisted path                                                           | —                                                   |
| —                        | —           | —   | No field accepts ballot content, and none may be added                  | ADR-098                                             |

## `F-P15-04` Ausgabe des Stimmzugangs beantragen

| Field                      | Type        | Req | Validation                                                    | Note                                             |
| -------------------------- | ----------- | --- | ------------------------------------------------------------- | ------------------------------------------------ |
| `assertion`                | assertion   | R   | Verified, unexpired, unspent, audience- and context-bound     | The only participant-derived input               |
| `voting_context_reference` | reference   | R   | Must match the assertion's context                             | Mismatch is `CREDENTIAL_CONTEXT_MISMATCH`        |
| `idempotency_key`          | key         | R   | Derived from the assertion nonce, voting side only            | Never echoed to the identity side                |
| `delivery_target_class`    | enum        | R   | `isolated_client` — the only permitted value in this round    | `OD-P15-07` may add accessible fallbacks          |

**This form collects nothing about the person.** It is listed as a form
because it is a participant-initiated act with a receipt, not because it
has personal fields — and the fact that it has none is the property to
check in review.

## `F-P15-05` Verlorenen oder abgelaufenen Stimmzugang melden

| Field                      | Type        | Req | Validation                                                            | Note                                                       |
| -------------------------- | ----------- | --- | --------------------------------------------------------------------- | ---------------------------------------------------------- |
| `voting_context_reference` | reference   | R   | An active context                                                     | —                                                          |
| `report_class`             | enum        | R   | `not_received`, `lost`, `expired_unused`, `suspected_compromise`      | Each has a different remedy                                |
| `credential_reference`     | reference   | C   | Required for `lost` and `suspected_compromise`, **supplied by the holder** | The issuer cannot look it up any other way            |
| `statement`                | text        | O   | —                                                                     | —                                                          |
| `assisted_by`              | reference   | C   | Assisted path                                                         | —                                                          |
| —                          | —           | —   | Filed as **two records** on two streams with no shared key            | Form inventory §1                                          |

## `F-P15-06` Überprüfung eines Widerrufs beantragen

| Field                   | Type      | Req | Validation                                     | Note                                          |
| ----------------------- | --------- | --- | ---------------------------------------------- | --------------------------------------------- |
| `revocation_reference`  | reference | R   | Supplied by the holder                          | No search; no oracle                          |
| `ground`                | enum      | R   | From the registered grounds                     | —                                             |
| `statement`             | text      | R   | —                                               | —                                             |
| `evidence_reference`    | reference | O   | PACK-11 reference                               | —                                             |

## `F-P15-07` Unterstützung bei der Teilnahme anfordern

| Field                | Type        | Req | Validation                                                    | Note                                                          |
| -------------------- | ----------- | --- | ------------------------------------------------------------- | ------------------------------------------------------------- |
| `support_class`      | enum        | R   | `accessibility`, `in_person`, `offline`, `language`, `technical` | —                                                          |
| `context_reference`  | reference   | O   | Where the request concerns one context                        | —                                                             |
| `requirements`       | text        | O   | Described by the participant                                  | Not a diagnosis, not a health record                          |
| `contact_preference` | enum        | R   | From confirmed channels                                       | —                                                             |
| —                    | —           | —   | **No health data, no disability classification, is collected**| Support is arranged from a stated need, not from a category   |

## `F-P15-08` Protokoll einer unterstützten Ausgabe

| Field                       | Type        | Req | Validation                                                            | Note                                                    |
| --------------------------- | ----------- | --- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| `helper_reference`          | reference   | R   | The attributed helper or operator                                     | **Attribution is mandatory; impersonation is refused**  |
| `support_class`             | enum        | R   | As in `F-P15-07`                                                      | —                                                       |
| `context_reference`         | reference   | R   | —                                                                     | —                                                       |
| `participant_confirmation`  | declaration | R   | Confirmed by the participant, not by the helper                       | —                                                       |
| `no_retention_declaration`  | declaration | R   | „Ich habe keinen Zugang zurückbehalten."                              | The helper declares it; the receipt records it          |
| `no_influence_declaration`  | declaration | R   | „Ich habe die Stimmabgabe weder eingesehen noch beeinflusst."         | The hard limit of assistance                            |
| —                           | —           | —   | The receipt is immutable and is given to the participant              | `FIR-INCLUSION-001`                                     |

## `F-P15-09` Antrag auf unabhängige Prüfung

| Field                  | Type      | Req | Validation                                              | Note                                                       |
| ---------------------- | --------- | --- | ------------------------------------------------------- | ---------------------------------------------------------- |
| `context_reference`    | reference | R   | The context under review                                | —                                                          |
| `scope_class`          | enum      | R   | `integrity`, `separation`, `issuance_counts`, `process` | **`ballot_content` and `participation_list` are absent**   |
| `ground`               | text      | R   | —                                                       | —                                                          |
| `case_references`      | reference | O   | The requester's own cases, where relevant               | Only their own                                             |
| —                      | —         | —   | The auditor works from bundles; this form grants no raw stream access | `SD-10`                                      |

---

## Fields that must never appear in any PACK-15 form

| Field                                 | Why                                                              |
| ------------------------------------- | ---------------------------------------------------------------- |
| `account_id`, `person_record_id`      | `FIR-INV-001`                                                     |
| `membership_id`, `member_number`      | Prohibited set                                                    |
| `date_of_birth`, `address`, `name`    | A predicate or a scope match suffices                            |
| `email`, `phone` as an entered value  | Channels are selected from confirmed channels, never re-typed    |
| `ballot_choice`, `vote_content`       | Never, in any form, for any purpose, including disputes          |
| `has_voted`, `participation_confirmed`| A person-level participation statement                            |
| `assertion_id` on a voting-side form  | The pairing                                                       |
| `credential_id` on an identity-side form | The pairing, from the other direction                          |
| Any health or disability category     | Support is arranged from a stated need                            |

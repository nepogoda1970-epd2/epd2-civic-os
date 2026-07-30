# PACK-14 — Field Catalogue

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Fields, types, requiredness, dependencies and validation, per form.
Required by `FIR-FORM-002`. Validation messages are in
`PACK-14-CONTENT-CATALOGUE-DE.md`.

## Conventions

`R` required · `O` optional · `C` conditional (the condition is stated).
**No field in any form below is a global identifier**, and no form collects
a national ID except `F-P14-14`, where it is evidence held under PACK-11
and never a key.

## `F-P14-01` Kontoregistrierung

| Field                      | Type        | Req | Validation                                                     | Note                                       |
| -------------------------- | ----------- | --- | -------------------------------------------------------------- | ------------------------------------------ |
| `email`                    | email       | R   | RFC-conformant; normalized lower-case; uniqueness within scope | A contact attribute, never the account key |
| `locale`                   | enum        | R   | Supported locales                                              | Canon 7.2 field                            |
| `terms_version`            | version     | R   | Must be the current published version                          | Canon 7.2 field                            |
| `terms_accepted`           | declaration | R   | Must be explicitly checked; never pre-checked                  |                                            |
| `privacy_acknowledged`     | declaration | R   | Must be explicitly checked                                     |                                            |
| `preferred_authentication` | enum        | O   | `passkey` default                                              | Passkey-first                              |

## `F-P14-02` / `F-P14-03` Kontaktbestätigung

| Field               | Type   | Req | Validation                                               |
| ------------------- | ------ | --- | -------------------------------------------------------- |
| `channel_class`     | enum   | R   | `email` or `phone`                                       |
| `verification_code` | string | R   | Single use; time-limited; rate-limited; **never logged** |

## `F-P14-04` Passkey einrichten

| Field                    | Type      | Req         | Validation                               | Note                                                |
| ------------------------ | --------- | ----------- | ---------------------------------------- | --------------------------------------------------- |
| `credential_nickname`    | string    | R           | 1–64 chars; no personal data required    | The user must be able to recognise the device later |
| `authenticator_response` | WebAuthn  | R           | Origin, challenge and signature verified | **Never stored in full, never logged**              |
| `device_binding`         | enum      | R (derived) | `device_bound` or `synced`               | Recorded distinctly (ADR-081)                       |
| `backup_eligible`        | boolean   | R (derived) | From authenticator data                  |                                                     |
| `step_up_reference`      | reference | R           | Action- and version-bound, unexpired     |                                                     |

## `F-P14-05` Passkey entfernen

| Field                      | Type        | Req | Validation                                                                                        |
| -------------------------- | ----------- | --- | ------------------------------------------------------------------------------------------------- |
| `credential_reference`     | reference   | R   | Must belong to this account                                                                       |
| `consequence_acknowledged` | declaration | R   | Must be explicitly checked                                                                        |
| `step_up_reference`        | reference   | R   | Assurance `high`                                                                                  |
| —                          | —           | —   | Refused with `CREDENTIAL_LAST_REMAINING` if it is the only credential and no recovery path exists |

## `F-P14-06` / `F-P14-07` Zwei-Faktor-Verfahren

| Field                    | Type        | Req        | Validation                                                                                                                                  |
| ------------------------ | ----------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `factor_class`           | enum        | R          | `totp`, `security_key`, `recovery_code`, `email_otp`. **`sms_otp` is deliberately absent** — it is not an authentication factor (OD-P14-09) |
| `confirmation_value`     | string      | R (enroll) | Single use; **never logged**                                                                                                                |
| `downgrade_acknowledged` | declaration | R (remove) | States the resulting assurance in words                                                                                                     |
| `step_up_reference`      | reference   | R          |                                                                                                                                             |

## `F-P14-08` Wiederherstellungscodes

| Field                 | Type        | Req       | Validation                               |
| --------------------- | ----------- | --------- | ---------------------------------------- |
| `code_count`          | integer     | R (fixed) | Policy value                             |
| `stored_confirmation` | declaration | R         | The codes are shown once and never again |
| `step_up_reference`   | reference   | R         |                                          |

## `F-P14-09` Kontowiederherstellung beantragen

| Field                | Type      | Req | Validation                                                                 | Note                                                      |
| -------------------- | --------- | --- | -------------------------------------------------------------------------- | --------------------------------------------------------- |
| `account_reference`  | handle    | R   | A contact handle or an account-scoped reference                            | Responses are uniform to prevent enumeration (AC-P14-004) |
| `reachable_channel`  | enum      | R   | Must not be a channel changed inside the protective window                 | Else `RECOVERY_CONTACT_RECENTLY_CHANGED`                  |
| `stated_reason`      | enum      | R   | `device_lost`, `device_stolen`, `credential_lost`, `channel_lost`, `other` | Free text is additional, never the reason code            |
| `assisted_by`        | reference | C   | Required when submitted through an assisted channel                        | Helper attribution (`FIR-INCLUSION-001`)                  |
| `evidence_reference` | reference | O   | PACK-11 bundle reference                                                   | Never the evidence content                                |

## `F-P14-10` Verdächtige Anmeldung

| Field             | Type      | Req | Validation                                                          |
| ----------------- | --------- | --- | ------------------------------------------------------------------- |
| `event_reference` | reference | R   | The notified event                                                  |
| `response`        | enum      | R   | `was_me` or `was_not_me`                                            |
| —                 | —         | —   | `was_not_me` immediately revokes sessions and opens a security case |

## `F-P14-11` Kontaktdaten ändern

| Field               | Type        | Req | Validation                                                |
| ------------------- | ----------- | --- | --------------------------------------------------------- |
| `channel_class`     | enum        | R   | `email` or `phone`                                        |
| `new_value`         | email/phone | R   | Normalized; uniqueness scope; not blocked by reuse policy |
| `verification_code` | string      | R   | Sent to the **new** channel; single use                   |
| `step_up_reference` | reference   | R   |                                                           |
| —                   | —           | —   | Both old and new channels are notified on success         |

## `F-P14-12` Aktive Sitzungen beenden

| Field               | Type      | Req | Validation                 |
| ------------------- | --------- | --- | -------------------------- |
| `session_selection` | enum      | R   | `one`, `all_others`, `all` |
| `session_reference` | reference | C   | Required when `one`        |
| `step_up_reference` | reference | R   |                            |

## `F-P14-13` Konto schließen

| Field                            | Type        | Req | Validation                                                        |
| -------------------------------- | ----------- | --- | ----------------------------------------------------------------- |
| `closure_reason`                 | enum        | R   | Registered reasons                                                |
| `retention_acknowledged`         | declaration | R   | States plainly that some records are retained by law              |
| `membership_notice_acknowledged` | declaration | C   | Required when a membership exists: closure is **not** resignation |
| `step_up_reference`              | reference   | R   | Assurance `high`                                                  |

## `F-P14-14` Identitätsprüfung einreichen

| Field                 | Type        | Req | Validation                                   | Note                                                |
| --------------------- | ----------- | --- | -------------------------------------------- | --------------------------------------------------- |
| `proofing_method`     | enum        | R   | From the proofing matrix                     |                                                     |
| `declared_name`       | string      | R   |                                              | Held under PACK-11, never an integration key        |
| `date_of_birth`       | date        | C   | Required for document-assisted and in-person | Canon 19d.2 field                                   |
| `evidence_reference`  | reference   | R   | PACK-11 bundle                               | **Document content never enters an event or a log** |
| `consent_declaration` | declaration | R   | Purpose-limited, explicit                    |                                                     |
| `assisted_by`         | reference   | C   | Assisted channel                             |                                                     |

## `F-P14-15` Privilegierte Wiederherstellung genehmigen

| Field                | Type        | Req | Validation                                                                                         |
| -------------------- | ----------- | --- | -------------------------------------------------------------------------------------------------- |
| `case_reference`     | reference   | R   | The recovery case                                                                                  |
| `assessment_summary` | structured  | R   | Named signals, never a bare score                                                                  |
| `decision`           | enum        | R   | `approve`, `reject`, `escalate`                                                                    |
| `reason_code`        | reason code | R   | Registered; no free text as the reason                                                             |
| `grant_reference`    | reference   | R   | A current PACK-12 grant                                                                            |
| `second_approver`    | reference   | C   | Required by dual control for high-risk cases                                                       |
| —                    | —           | —   | Refused with `RECOVERY_SELF_APPROVAL_REFUSED` if the reviewer initiated the case or is its subject |

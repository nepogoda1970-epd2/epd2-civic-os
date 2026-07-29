# PACK-12 — FIR Coverage Matrix

Specification-only. No code. Not implemented.

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the _specification round_ that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.

**No FIR entry is marked `implemented` by this round, and none may be.**
A specification round produces requirements, not implementations. The
`PACK-12 treatment` column records what this round did with each entry;
the `Implementation-stage obligation` column records what the future
implementation round must do before any status change is even arguable.

Treatment values: **addressed** (the specification fully specifies how
the entry is met), **partially addressed** (specified in part, with the
remainder named), **deferred** (recorded as a dependency owned by a later
pack), **unchanged** (the entry is untouched by PACK-12).

---

## 1. Roadmap

| FIR               | Status before PACK-12 | PACK-12 treatment | Specification / ADR references               | Implementation-stage obligation                                                                                             | Reason for deferral |
| ----------------- | --------------------- | ----------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `FIR-ROADMAP-002` | `approved`            | addressed         | Whole package; spec §1–§17; ADR-061..ADR-068 | Build the three contexts; satisfy all 101 acceptance criteria; then propose a status change to `implemented` — never before | —                   |

`FIR-ROADMAP-002` MUST NOT move past `scheduled` or `under_review` on
the strength of this round.

---

## 2. Hard invariants

| FIR           | Status before | Treatment           | References                                                                  | Implementation-stage obligation                                                                | Reason for deferral                                                   |
| ------------- | ------------- | ------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `FIR-INV-006` | `approved`    | addressed           | `P12-BG-009`, `P12-BG-011`; ADR-063                                         | Prove structurally that no flag, mode or grant disables an invariant, audit or separation      | —                                                                     |
| `FIR-INV-007` | `approved`    | addressed           | §7, §9, §10; `P12-SRCH-*`, `P12-EXP-*`, `P12-DLP-*`; ADR-064, 066, 067      | Implement scoped access, reason codes, purpose, DLP, rate limits, approvals and audit evidence | —                                                                     |
| `FIR-INV-008` | `approved`    | addressed           | `P12-ROLE-008`, `P12-ROLE-014`, `P12-ROLE-015`; role matrix pair 1; ADR-061 | Enforce the preserved institutional pair at assignment and at the act                          | —                                                                     |
| `FIR-INV-009` | `approved`    | addressed           | §4, §5; `P12-PAM-*`, `P12-BG-*`; ADR-062, ADR-063                           | Implement the grant lifecycle, break-glass dual control and the notification obligation        | Notification **transport** deferred to PACK-17 / gateway              |
| `FIR-INV-011` | `approved`    | partially addressed | §11; `P12-SDC-*`; ADR-067                                                   | Implement cohort, suppression, complement, differencing and cumulative rules                   | Production analytics engine and release-history storage are PACK-13's |
| `FIR-INV-013` | `approved`    | addressed           | §12; `P12-ORG-003`..`008`; `P12-SRCH-010`                                   | Enforce organizational scope on every grant, query and export                                  | —                                                                     |
| `FIR-INV-014` | `approved`    | addressed           | `P12-ROLE-001`, `P12-ROLE-019`, `P12-ROLE-021`, `P12-FE-004`; ADR-061       | Structural test that no role set spans all domains and scopes; no universal console            | —                                                                     |
| `FIR-INV-015` | `approved`    | addressed           | §19; `P12-SES-007`, `P12-EXP-013`, `P12-DLP-004`                            | Forbidden-phrase scans; no production, legal or tamper-resistance claim in code, docs or UI    | —                                                                     |
| `FIR-INV-001` | `approved`    | unchanged           | Referenced only                                                             | PACK-12 mints no identifier; nothing to implement here                                         | —                                                                     |
| `FIR-INV-002` | `approved`    | unchanged           | `P12-VOTE-001`, `P12-VOTE-002`                                              | Structural absence of any voting reference type                                                | Owned by PACK-15/16                                                   |
| `FIR-INV-003` | `approved`    | unchanged           | `P12-VOTE-001`                                                              | As above                                                                                       | Owned by PACK-15/16                                                   |
| `FIR-INV-005` | `approved`    | unchanged           | `P12-VOTE-001` (intermediate tally absolutely excluded)                     | As above                                                                                       | Owned by PACK-15/16                                                   |
| `FIR-INV-010` | `approved`    | unchanged           | `P12-SES-005` reuses PACK-11 evidence bundles                               | Reuse, do not reimplement                                                                      | Implemented by PACK-11                                                |

---

## 3. Institutional roles

| FIR            | Status before                   | Treatment           | References                                              | Implementation-stage obligation                                                                                                | Reason for deferral                        |
| -------------- | ------------------------------- | ------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| `FIR-ROLE-001` | `approved`                      | partially addressed | `P12-ROLE-019`; role matrix §1.1                        | DPO must not be substitutable by any PACK-12 operational assignment; enforce at the act                                        | The DPO office itself is not PACK-12's     |
| `FIR-ROLE-003` | `approved`                      | partially addressed | `independent_privileged_access_reviewer`; `P12-PAM-008` | Give the independent auditor governed read access to grants, sessions and query/export audit without any operational privilege | The auditor office itself is not PACK-12's |
| `FIR-ROLE-005` | `approved`                      | unchanged           | Referenced only                                         | Election Administration Separation Matrix stays with the election domain                                                       | Owned elsewhere                            |
| `FIR-ROLE-006` | `implemented in reference form` | unchanged           | Referenced only                                         | Finance separation of duties stays PACK-10's                                                                                   | Implemented by PACK-10                     |

---

## 4. Data governance

| FIR            | Status before | Treatment           | References                                                         | Implementation-stage obligation                                                                   | Reason for deferral                                          |
| -------------- | ------------- | ------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `FIR-DATA-001` | `approved`    | partially addressed | `P12-CLS-001`..`005`; data matrix §2; `IndexPolicy`, `ExportScope` | Bind every index and export decision to the authoritative record class and processing purpose     | The catalog and processing registry themselves are PACK-09's |
| `FIR-DATA-002` | `approved`    | unchanged           | Referenced only                                                    | Deadline management stays PACK-09's                                                               | Owned elsewhere                                              |
| `FIR-DATA-003` | `approved`    | partially addressed | `P12-EXP-016`, `P12-EXP-017`, `P12-SRCH-013`; data matrix §8       | Observe hold state before every export and index-removal act; never treat a hold as authorization | Hold semantics remain PACK-09's; PACK-12 only observes       |

---

## 5. Frontend

| FIR             | Status before | Treatment           | References                 | Implementation-stage obligation                                                          | Reason for deferral                           |
| --------------- | ------------- | ------------------- | -------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------- |
| `FIR-FRONT-001` | `approved`    | partially addressed | `P12-FE-001`, `P12-FE-004` | Twelve administrative surfaces only; no universal console; workspace model stays FRONT's | Full workspace architecture is FRONT-PACK's   |
| `FIR-FRONT-002` | `approved`    | partially addressed | `P12-FE-003`, `P12-FE-006` | Reuse FRONT-00's storage and telemetry policies; no sensitive data in client telemetry   | Design system and navigation are FRONT-PACK's |
| `FIR-FRONT-003` | `approved`    | deferred            | `P12-FE-002`               | Privileged administration MUST NOT appear in the ordinary mobile app                     | Mobile app scope is its own future package    |

---

## 6. Security and operations — dependency only

| FIR           | Status before | Treatment | References                        | Implementation-stage obligation                                                         | Reason for deferral                                                |
| ------------- | ------------- | --------- | --------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `FIR-SEC-001` | `approved`    | deferred  | `P12-BG-006`..`008`; T-P12-20     | Emit the notification and escalation events the incident platform will consume          | Incident-response platform and out-of-band transport are PACK-17's |
| `FIR-SEC-003` | `approved`    | deferred  | `P12-EXP-014`; recipient profiles | Record transfer-channel restrictions and recipient obligations the gateway will enforce | External gateway security is PACK-14's                             |

---

## 7. Summary

| Treatment           | Count |
| ------------------- | ----- |
| addressed           | 9     |
| partially addressed | 8     |
| deferred            | 3     |
| unchanged           | 6     |
| **implemented**     | **0** |

Zero is the only correct value in the last row for a specification-only
round, and `AC-P12-101` makes it structurally testable: the
implementation round must be able to assert that this matrix contains no
`implemented` value.

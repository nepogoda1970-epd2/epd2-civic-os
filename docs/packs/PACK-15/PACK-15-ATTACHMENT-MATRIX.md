# PACK-15 — Attachment Matrix

**Round:** PACK-15 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.14.0` · **Canon version:** unchanged at `0.8.0`
**Baseline:** `EPD2_PACK-14_IDENTITY_AUTHENTICATION_ACCOUNT_SECURITY_0.14.0_FINAL_PASS.zip`
**Authoritative register:** `EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER_UPDATED_V6.md`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-31).**

Permitted and required attachments per form. Required by `FIR-FORM-002`.

---

## 1. Attachments by form

| Form                                      | Attachments permitted | Required | Types                                                       | Handling                                                  |
| ----------------------------------------- | --------------------- | -------- | ----------------------------------------------------------- | --------------------------------------------------------- |
| `F-P15-01` Prüfung beantragen             | **none**              | —        | —                                                           | The request itself needs no document                      |
| `F-P15-02` Nachweise einreichen           | **required**          | yes      | Membership, scope, role or status evidence per the rule-set | PACK-11 governed document; referenced, never inlined      |
| `F-P15-03` Widerspruch (Berechtigung)     | optional              | no       | Supporting evidence where the reviewer requests it          | PACK-11 reference                                         |
| `F-P15-04` Zugang abrufen                 | **none**              | —        | —                                                           | **Structurally none.** This form is on the voting side    |
| `F-P15-05` Problem mit dem Zugang         | **none**              | —        | —                                                           | A holder-supplied reference is a field, not an attachment |
| `F-P15-06` Widerruf überprüfen            | optional              | no       | Supporting evidence                                         | PACK-11 reference                                         |
| `F-P15-07` Unterstützung anfordern        | **none**              | —        | —                                                           | **No medical or disability documentation is accepted**    |
| `F-P15-08` Protokoll unterstützte Ausgabe | **none**              | —        | —                                                           | The receipt is generated, not uploaded                    |
| `F-P15-09` Unabhängige Prüfung            | case references only  | yes      | The requester's own case references                         | Referenced                                                |

**`F-P15-04` accepting no attachment is a structural property, not a
simplification.** An attachment surface on the voting side would be a
channel through which identity-bearing material could arrive, and the
absence of the surface is the control.

---

## 2. Handling rules

| Rule                                                                                        | Reason                                                                     |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| An attachment is stored as a PACK-11 governed document, never as a field value              | Evidence needs custody, versioning and retention a field does not have     |
| Events and logs carry the **reference**, never the content                                  | Audit minimization; ADR-091                                                |
| Evidence is readable only within its own eligibility or dispute case                        | Least privilege                                                            |
| **No evidence and no evidence reference crosses the trust boundary**                        | The voting side has no use for it and no right to see it                   |
| A denied case's evidence is retained per schedule, not deleted on denial                    | A denial may be disputed; destroyed evidence cannot answer the dispute     |
| No executable attachment type is accepted                                                   | Established by PACK-11 and the initiative pre-publication profile          |
| Virus and content scanning is a boundary requirement of the implementation round            | Named here rather than assumed                                             |
| Attachment metadata is minimized: no EXIF, no author, no device, no geolocation is retained | A photograph of a document carries a location and a camera unless stripped |
| Retention follows `PACK-15-PRIVACY-RETENTION-MATRIX.md`                                     | PACK-09 owns schedules                                                     |

---

## 3. What is deliberately not collected

Identity documents as a general eligibility input — proofing is PACK-14's
and its evidence stays there. Biometric material of any kind. Medical
certificates or disability classifications for the assistance path.
Membership cards or member numbers as images. Screenshots of a voting
client. Anything a participant might upload to "prove they voted", which
the system must refuse to accept as well as refuse to issue.

Each of these would create a store whose existence is a liability
disproportionate to the operation it serves, and the last one would create
a coercion instrument.

---

## 4. Attachment paths that must not exist

| Path                                                                         | Why                                                    |
| ---------------------------------------------------------------------------- | ------------------------------------------------------ |
| Uploading anything to the credential issuer                                  | An identity channel into the voting side               |
| Attaching an eligibility document to a dispute about a credential            | Carries identity-side evidence into a voting-side case |
| Attaching a credential value to any form                                     | A secret in a document store                           |
| Attaching a screenshot of the voting client to a dispute                     | May contain ballot content                             |
| An operator attaching evidence on a participant's behalf without attribution | Unattributed assisted action                           |

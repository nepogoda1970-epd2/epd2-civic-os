# PACK-14 — Attachment Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

Permitted and required attachments per form. Required by `FIR-FORM-002`.

## 1. Attachments by form

| Form                                 | Attachments permitted                            | Required | Types                                                       | Handling                                                                                          |
| ------------------------------------ | ------------------------------------------------ | -------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `F-P14-01` … `F-P14-08`              | **none**                                         | —        | —                                                           | These operations need no documents, and accepting them would create an unnecessary evidence store |
| `F-P14-09` Wiederherstellung         | optional                                         | no       | Supporting evidence where the reviewer requests it          | PACK-11 bundle; referenced, never inlined                                                         |
| `F-P14-10` Verdächtige Anmeldung     | **none**                                         | —        | —                                                           | —                                                                                                 |
| `F-P14-11` … `F-P14-13`              | **none**                                         | —        | —                                                           | —                                                                                                 |
| `F-P14-14` Identitätsprüfung         | **required** for document-assisted and in-person | yes      | Identity document image or scan; organizational attestation | PACK-11 governed document with custody chain; **RESTRICTED**                                      |
| `F-P14-15` Privilegierte Genehmigung | case evidence only                               | yes      | The case's own assessment record                            | Referenced                                                                                        |

## 2. Handling rules

| Rule                                                                                   | Reason                                                                      |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| An attachment is stored as a PACK-11 governed document, never as a field value         | Evidence needs custody, versioning and retention that a field does not have |
| Events and logs carry the **reference**, never the content                             | ADR-086; audit minimization                                                 |
| Identity documents are RESTRICTED and readable only within their proofing case         | Least privilege over the most sensitive data in the system                  |
| Retention follows the class in `PACK-14-PRIVACY-RETENTION-MATRIX.md`                   | PACK-09 owns schedules                                                      |
| A rejected proofing case's evidence is retained per schedule, not deleted on rejection | Rejection may be disputed; destroyed evidence cannot answer the dispute     |
| No executable attachment type is accepted                                              | Established by PACK-11 and the initiative pre-publication profile           |
| Virus and content scanning is a boundary requirement of the implementation round       | Named here rather than assumed                                              |

## 3. What is deliberately not collected

Passport or ID numbers as searchable fields; biometric templates; full
document text extracted into structured fields; any attachment on the
authentication and session forms. Each would create a store whose existence
is a liability disproportionate to the operation it serves.

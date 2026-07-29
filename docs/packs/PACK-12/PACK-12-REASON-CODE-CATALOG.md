# PACK-12 — Reason Code Catalog

Specification-only. **No `contracts/reason-codes/pack-12.yml` is created
by this round.** This catalogue is the proposed content of that file, to
be authored in the implementation round.

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

Companion to `PACK-12-SPECIFICATION.md` section 14.

---

## 1. Why four prefixes and not one code

`P12-RSN-002` forbids a single generic `FORBIDDEN`. The reason is
operational, not aesthetic: a refusal is the only thing an operator, an
auditor and an affected participant all see. A code that says only "no"
cannot distinguish "you asked for the wrong scope", "your grant expired",
"this field is not exportable" and "this would re-identify a cohort of
four" — four situations with four different correct responses.

Four prefixes, matching the four governed concerns:

| Prefix        | Concern                                               |
| ------------- | ----------------------------------------------------- |
| `PRIVILEGE_`  | Privileged administration, PAM, break-glass, sessions |
| `SEARCH_`     | Authorization-aware search and indexing               |
| `EXPORT_`     | Governed data export and DLP                          |
| `DISCLOSURE_` | Statistical disclosure control                        |

Codes reused verbatim from earlier packs are listed in section 6 and MUST
NOT be shadowed by a PACK-12 synonym (`P12-RSN-003`).

---

## 2. `PRIVILEGE_*` — 27 codes

| Code                                               | Meaning                                                                    |
| -------------------------------------------------- | -------------------------------------------------------------------------- |
| `PRIVILEGE_AUTHORITY_MISSING`                      | No active, scope-matching privileged authority exists for this operation   |
| `PRIVILEGE_SEPARATION_OF_DUTIES_CONFLICT`          | The act would place two separated duties with one subject                  |
| `PRIVILEGE_ROLE_COMBINATION_PROHIBITED`            | The subject holds a pair the incompatibility matrix forbids                |
| `PRIVILEGE_SELF_APPROVAL_PROHIBITED`               | Requester and approver are the same subject                                |
| `PRIVILEGE_INSUFFICIENT_APPROVER`                  | The presented approver lacks the role or rank the risk class requires      |
| `PRIVILEGE_APPROVER_COUNT_INSUFFICIENT`            | Fewer approvers than the risk class requires                               |
| `PRIVILEGE_SCOPE_MISMATCH`                         | The requested resource lies outside the grant's resource scope             |
| `PRIVILEGE_PURPOSE_MISMATCH`                       | The operation does not serve the grant's declared purpose                  |
| `PRIVILEGE_OPERATION_NOT_GRANTED`                  | The operation is outside the grant's operation set                         |
| `PRIVILEGE_ORGANIZATION_MISMATCH`                  | The grant belongs to a different organization                              |
| `PRIVILEGE_GRANT_EXPIRED`                          | The grant's end instant has passed                                         |
| `PRIVILEGE_GRANT_REVOKED`                          | The grant was withdrawn before expiry                                      |
| `PRIVILEGE_GRANT_NOT_ACTIVATED`                    | The grant is approved but not yet activated                                |
| `PRIVILEGE_GRANT_DORMANT`                          | The grant is unused past the dormancy interval and requires review         |
| `PRIVILEGE_STANDING_ACCESS_PROHIBITED`             | A permanent, unbounded grant was requested                                 |
| `PRIVILEGE_JUSTIFICATION_MISSING`                  | No written justification was supplied                                      |
| `PRIVILEGE_RISK_CLASSIFICATION_UNDETERMINED`       | The risk class could not be determined; fail closed                        |
| `PRIVILEGE_BREAK_GLASS_CONDITION_ABSENT`           | No documented emergency condition                                          |
| `PRIVILEGE_BREAK_GLASS_DUAL_CONTROL_MISSING`       | Activator and approver are the same, or the approver is absent             |
| `PRIVILEGE_BREAK_GLASS_NOTIFICATION_UNDELIVERED`   | Out-of-band notification could not be dispatched; escalate, do not proceed |
| `PRIVILEGE_BREAK_GLASS_SCOPE_TOO_BROAD`            | The requested emergency scope exceeds the narrow-scope requirement         |
| `PRIVILEGE_BREAK_GLASS_RENEWAL_REQUIRES_DECISION`  | Extension was attempted in place of a new dual-controlled decision         |
| `PRIVILEGE_SESSION_EVIDENCE_INCOMPLETE`            | A session cannot be sealed because required evidence fields are missing    |
| `PRIVILEGE_AUDIT_MUTATION_PROHIBITED`              | An attempt to modify or delete an audit record under custody               |
| `PRIVILEGE_ASSIGNMENT_NOT_GOVERNED`                | An operational assignment was asserted without governed authority          |
| `PRIVILEGE_ASSIGNMENT_NOT_EFFECTIVE_DATED`         | An operational assignment lacks scope, purpose or effective dating         |
| `PRIVILEGE_INSTITUTIONAL_AUTHORITY_NOT_EXTENDABLE` | An operational assignment was used to claim institutional authority        |

---

## 3. `SEARCH_*` — 14 codes

| Code                                         | Meaning                                                                     |
| -------------------------------------------- | --------------------------------------------------------------------------- |
| `SEARCH_SOURCE_AUTHORIZATION_DENIED`         | The requester could not open the source record directly                     |
| `SEARCH_SCOPE_UNDETERMINED`                  | No organization scope was resolvable; default deny                          |
| `SEARCH_ORGANIZATION_MISMATCH`               | The query reaches outside the requester's organizational scope              |
| `SEARCH_PURPOSE_MISMATCH`                    | The declared purpose does not admit this query                              |
| `SEARCH_MODE_NOT_PERMITTED`                  | The requested search mode is not available to this subject                  |
| `SEARCH_HIGHLY_CONFIDENTIAL_DOMAIN_EXCLUDED` | The target domain is excluded from the index by policy                      |
| `SEARCH_BALLOT_CONTENT_PROHIBITED`           | Ballot-level material may never be indexed or searched                      |
| `SEARCH_UNCERTIFIED_RESULT_PROHIBITED`       | Intermediate, partial or non-certified tally material may never be searched |
| `SEARCH_INDEX_AUTHORIZATION_STALE`           | The index view could not be reconciled with current source authorization    |
| `SEARCH_SNIPPET_SUPPRESSED`                  | A snippet was withheld because the source restriction forbids it            |
| `SEARCH_RESULT_SUPPRESSED`                   | Results exist but are not disclosable to this requester                     |
| `SEARCH_FACET_SUPPRESSED`                    | A facet or suggestion was withheld to avoid disclosing restricted values    |
| `SEARCH_CACHE_CONTEXT_MISMATCH`              | A cache entry did not match the effective authorization context             |
| `SEARCH_INDEX_POLICY_VIOLATION`              | An indexing attempt violates `IndexPolicy` or `IndexFieldPolicy`            |

`SEARCH_RESULT_SUPPRESSED` is deliberately indistinguishable, from the
requester's side, from "no results" (`P12-SRCH-007`). The code exists for
the audit trail, not for the response body.

---

## 4. `EXPORT_*` — 24 codes

| Code                                    | Meaning                                                                                                         |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `EXPORT_AUTHORITY_MISSING`              | No export authority for this record class in this scope                                                         |
| `EXPORT_DATA_OWNER_MISSING`             | No authoritative data owner could be resolved                                                                   |
| `EXPORT_APPROVAL_MISSING`               | No approval, or approval by an ineligible subject                                                               |
| `EXPORT_SELF_APPROVAL_PROHIBITED`       | The requester approved their own export                                                                         |
| `EXPORT_PURPOSE_MISSING`                | No declared purpose                                                                                             |
| `EXPORT_PURPOSE_MISMATCH`               | The requested data does not serve the declared purpose                                                          |
| `EXPORT_LEGAL_BASIS_MISSING`            | A basis reference is required for this class or recipient and is absent                                         |
| `EXPORT_ORGANIZATION_MISMATCH`          | Cross-organizational export without its own scope and basis                                                     |
| `EXPORT_RECIPIENT_NOT_AUTHORIZED`       | The recipient or recipient category may not receive this class                                                  |
| `EXPORT_RECIPIENT_OBLIGATION_MISSING`   | Required downstream obligations were not recorded                                                               |
| `EXPORT_TRANSFER_CHANNEL_PROHIBITED`    | The requested channel is not permitted for this class or recipient                                              |
| `EXPORT_FIELD_NOT_EXPORTABLE`           | A requested field is denied by field policy                                                                     |
| `EXPORT_BULK_EXTRACTION_NOT_AUTHORIZED` | Read permission was presented as bulk-export authority                                                          |
| `EXPORT_SEARCH_PERMISSION_INSUFFICIENT` | Search permission was presented as export authority                                                             |
| `EXPORT_ADMIN_PRIVILEGE_INSUFFICIENT`   | Administrative privilege was presented as export authority                                                      |
| `EXPORT_BALLOT_CONTENT_PROHIBITED`      | Ballot-level material may never be exported                                                                     |
| `EXPORT_UNCERTIFIED_RESULT_PROHIBITED`  | Intermediate, partial or non-certified tally material may never be exported                                     |
| `EXPORT_RESULT_PUBLICATION_NOT_OWNED`   | A certified result may be released only by the authoritative voting/result-certification domain, not by PACK-12 |
| `EXPORT_LEGAL_HOLD_NOT_AUTHORIZATION`   | A legal hold was presented as permission to export                                                              |
| `EXPORT_SOURCE_RECORD_REVOKED`          | A source record is revoked or deleted and may not enter a new export                                            |
| `EXPORT_MANIFEST_MISSING`               | No immutable manifest is bound to the artifact                                                                  |
| `EXPORT_MANIFEST_MISMATCH`              | The artifact does not match its manifest digest                                                                 |
| `EXPORT_ARTIFACT_EXPIRED`               | The artifact's expiry has passed                                                                                |
| `EXPORT_ARTIFACT_REVOKED`               | Authorization for the artifact was withdrawn                                                                    |

### 4.1 `EXPORT_DLP_*` — 8 codes

| Code                                  | Meaning                                                  |
| ------------------------------------- | -------------------------------------------------------- |
| `EXPORT_DLP_REVIEW_REQUIRED`          | Manual DLP review is required before a decision          |
| `EXPORT_DLP_ASSESSMENT_MISSING`       | No completed DLP assessment                              |
| `EXPORT_DLP_ASSESSMENT_INCOMPLETE`    | Detection could not complete; fail closed                |
| `EXPORT_DLP_FORBIDDEN_DATA_DETECTED`  | Forbidden data was found in the candidate set            |
| `EXPORT_DLP_SIZE_LIMIT_EXCEEDED`      | Export exceeds the permitted size                        |
| `EXPORT_DLP_FREQUENCY_LIMIT_EXCEEDED` | Export frequency exceeds the permitted rate              |
| `EXPORT_DLP_UNUSUAL_VOLUME_REVIEW`    | Volume anomaly requires review                           |
| `EXPORT_DLP_REPEATED_REQUEST_RISK`    | Repeated similar requests indicate an extraction pattern |

---

## 5. `DISCLOSURE_*` — 11 codes

| Code                                             | Meaning                                                                      |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| `DISCLOSURE_ASSESSMENT_MISSING`                  | No disclosure-risk assessment where one is required                          |
| `DISCLOSURE_THRESHOLD_FAILED`                    | A cohort is below the applicable threshold                                   |
| `DISCLOSURE_SUPPRESSION_REQUIRED`                | Release requires suppression that was not applied                            |
| `DISCLOSURE_COMPLEMENT_RECOVERABLE`              | A suppressed value is recoverable from totals or neighbours                  |
| `DISCLOSURE_REPEATED_QUERY_RISK`                 | Successive queries permit differencing                                       |
| `DISCLOSURE_CUMULATIVE_RELEASE_RISK`             | Individually permissible releases are jointly re-identifying                 |
| `DISCLOSURE_EXCEPTION_NOT_APPROVED`              | An override was applied without an approved exception                        |
| `DISCLOSURE_EXCEPTION_EXPIRED`                   | The approved exception's conditions no longer hold                           |
| `DISCLOSURE_PUBLICATION_AUTHORITY_MISSING`       | Raw-data access was presented as authority to publish                        |
| `DISCLOSURE_CLASSIFICATION_UNMAPPED`             | The source classification has no enforcement-tier mapping; fail closed       |
| `DISCLOSURE_CLASSIFICATION_DOWNGRADE_PROHIBITED` | An enforcement tier was used to lower an authoritative source classification |

---

## 6. Codes reused from earlier packs

Reused verbatim, never shadowed (`P12-RSN-003`):

| Code                                 | Owner   | Used by PACK-12 for                                       |
| ------------------------------------ | ------- | --------------------------------------------------------- |
| `PERMISSION_DENIED`                  | PACK-02 | Generic authorization refusal where no specific code fits |
| `VALIDATION_RECORD_NOT_FOUND`        | PACK-02 | Unknown grant, request or artifact identifier             |
| `OPTIMISTIC_CONCURRENCY_CONFLICT`    | PACK-02 | Stale expected version on a governed object               |
| `AUDIT_CHAIN_BROKEN`                 | PACK-02 | Chain verification failure during custody operations      |
| `ORGANIZATION_SCOPE_MISMATCH`        | PACK-08 | Cross-scope refusal                                       |
| `ORGANIZATION_SCOPE_UNDETERMINED`    | PACK-08 | Undeterminable scope; default deny                        |
| `CROSS_SCOPE_ACCESS_DENIED`          | PACK-08 | Cross-scope read without an access mode                   |
| `AUTHORITY_ROLE_INCOMPATIBLE`        | PACK-08 | Role pair violation at assignment time                    |
| `RECORD_UNDER_LEGAL_HOLD`            | PACK-09 | Disposal blocked by a hold                                |
| `LEGAL_HOLD_STATE_UNKNOWN`           | PACK-09 | Indeterminate hold; fail closed                           |
| `GOVERNED_RECORD_DELETION_FORBIDDEN` | PACK-09 | Deletion attempt on a governed record                     |
| `PUBLICATION_NOT_ALLOWED`            | PACK-04 | Publication without its own authorization                 |
| `DISCLOSURE_POLICY_VIOLATION`        | PACK-04 | Emission violating an applicable disclosure policy        |

---

## 7. Totals and registry obligations

| Group          | Codes  |
| -------------- | ------ |
| `PRIVILEGE_*`  | 24     |
| `SEARCH_*`     | 13     |
| `EXPORT_*`     | 30     |
| `DISCLOSURE_*` | 9      |
| Reused         | 13     |
| **Total**      | **89** |

At implementation time each entry MUST carry the seven fields
`epd2_core.reason_codes.ReasonCodeRegistry.load_from_yaml` requires:
`code`, `meaning`, `severity`, `description`, `retryable`, `owner`,
`introduced_in_version` — plus the `source` marker the PACK-08 through
PACK-11 registries use. A missing field makes the whole registry fail to
load, which is the intended behaviour.

Canon section 24 registers none of these codes today. Whether that
requires a canon amendment is answered in `PACK-12-CANON-ASSESSMENT.md`;
the short answer is no, and PACK-11's registry — which likewise contains
no `source: canon-0.8.0` entry — is the precedent.

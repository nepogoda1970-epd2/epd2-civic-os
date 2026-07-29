# PACK-12 — Event Catalog

Specification-only. No code, no schema file, no implementation.

> **Status note added by the PACK-12 implementation candidate round
> (2026-07-29).** The "specification-only / not implemented" statement
> above describes the *specification round* that produced this document
> and is preserved as the historical record. It is no longer the state of
> the repository: `services/privileged-access-service` now implements this
> specification as an **implementation candidate** at repository version
> `0.12.0`.
>
> **LOCAL VERIFICATION INCOMPLETE / EXTERNAL CI PENDING / NOT FINAL PASS.**
> Nothing here is claimed as verified, passed, or production-ready. See
> `docs/handover/PACK-12-IMPLEMENTATION-CANDIDATE-REPORT.md` section 5.


Companion to `PACK-12-SPECIFICATION.md` section 13.

---

## 1. Conventions

- The canonical envelope of canon section 21 is used unchanged. This
  catalogue proposes no envelope change, so `event_version` starts at
  `1.0` for every family (`P12-EVT-002`).
- Names carry the **aggregate prefix**, not a service prefix, following
  canon section 20 throughout: `privileged_access.requested`, never
  `pack12.privileged_access_requested` (`P12-EVT-004`).
- Six families, 44 event types.
- Every payload is subject to `P12-EVT-003`: no plaintext secret, no
  credential, no key material, no ballot content, no full sensitive
  payload.

### 1.1 Safe metadata on every event

| Field                | Note                                                      |
| -------------------- | --------------------------------------------------------- |
| `organization_scope` | Mandatory; an undeterminable scope denies before emission |
| `aggregate_id`       | Stable identifier of the affected object                  |
| `purpose_reference`  | Declared purpose, where the aggregate has one             |
| `reason_code`        | Registered code from `PACK-12-REASON-CODE-CATALOG.md`     |
| `policy_version`     | The policy version the decision was taken under           |
| `actor_reference`    | Opaque; never an identity attribute                       |

### 1.2 Forbidden in every payload

Plaintext credentials; private key material; session tokens; ballot
content, vote envelopes, intermediate and non-certified tally material,
delegation records; document bytes,
extracted text or renditions (PACK-11 owns those); full record payloads;
whistleblower identity; raw query text where it may embed personal data —
a query digest and a policy-classified query shape are emitted instead.

---

## 2. `privileged_access.*` — 11 types

| Event type                           | Emitted when                         | Key payload (beyond safe metadata)                             |
| ------------------------------------ | ------------------------------------ | -------------------------------------------------------------- |
| `privileged_access.requested`        | A request is submitted               | requested role, operations, data classes, duration, risk class |
| `privileged_access.approved`         | An approver approves                 | approver reference, SoD evaluation reference, effective window |
| `privileged_access.denied`           | An approver or the guard refuses     | reason code, failed check                                      |
| `privileged_access.activated`        | The grant becomes usable             | activation instant, re-evaluated SoD reference                 |
| `privileged_access.expired`          | The recorded end instant passes      | expiry instant                                                 |
| `privileged_access.revoked`          | A grant is withdrawn early           | revoking authority, reason code                                |
| `privileged_session.started`         | A session opens under a grant        | session id, grant reference, permitted operations              |
| `privileged_session.ended`           | A session closes                     | end instant, operation count                                   |
| `privileged_session.evidence_sealed` | Session evidence is sealed           | integrity reference, evidence bundle reference                 |
| `privileged_access.review_requested` | Periodic or post-access review opens | review kind, reviewer reference                                |
| `privileged_access.review_completed` | A review concludes                   | outcome, findings reference, reason code                       |

---

## 3. `break_glass.*` — 7 types

| Event type                                 | Emitted when                          | Key payload                                              |
| ------------------------------------------ | ------------------------------------- | -------------------------------------------------------- |
| `break_glass.requested`                    | Emergency access is requested         | emergency condition reference, requested scope, duration |
| `break_glass.approved`                     | The second control approves           | approver reference (distinct from activator)             |
| `break_glass.activated`                    | Emergency access becomes usable       | activation instant, narrow scope, hard expiry            |
| `break_glass.notification_dispatched`      | Out-of-band notification is sent      | recipient class, dispatch outcome, transport reference   |
| `break_glass.expired`                      | The hard expiry passes                | expiry instant                                           |
| `break_glass.revoked`                      | Emergency access is withdrawn early   | revoking authority, reason code                          |
| `break_glass.independent_review_completed` | Post-hoc independent review concludes | reviewer reference, outcome, findings reference          |

`break_glass.notification_dispatched` MUST be emitted whether the
dispatch succeeded or failed; a failed dispatch carries its failure
reason and escalation reference (`P12-BG-008`). The event MUST NOT be
suppressible by the activating actor (`P12-BG-007`).

---

## 4. `search_query.*` and `search_index.*` — 8 types

| Event type                                  | Emitted when                                | Key payload                                           |
| ------------------------------------------- | ------------------------------------------- | ----------------------------------------------------- |
| `search_query.submitted`                    | A query arrives                             | query digest, mode, scope, purpose                    |
| `search_query.authorized`                   | The query passes admission                  | resolved scope, applied restrictions                  |
| `search_query.denied`                       | The query is refused                        | reason code, failed check                             |
| `search_query.executed`                     | Results are returned                        | authorized result count, snippet policy applied       |
| `search_query.restricted_result_suppressed` | Results were withheld                       | suppression count band, suppression reason            |
| `search_index.policy_changed`               | `IndexPolicy` or `IndexFieldPolicy` changes | policy version before and after, authority reference  |
| `search_index.reindex_requested`            | A reindex is requested                      | scope, reason, requesting authority                   |
| `search_index.removal_evidenced`            | Records are removed from the index          | removal evidence reference, source decision reference |

`search_query.submitted` carries a **query digest**, not the raw query
string: a query can itself contain personal data, and an audit trail of
raw queries would be a second copy of exactly what the search rules
exist to protect.

`search_query.restricted_result_suppressed` carries a **count band**
rather than an exact count, because an exact suppression count is itself
a disclosure of how many restricted records matched
(`P12-SRCH-007`).

---

## 5. `data_export.*` and `export_artifact.*` — 11 types

| Event type                                    | Emitted when                               | Key payload                                                 |
| --------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------- |
| `data_export.requested`                       | An export request is submitted             | purpose, scope, record classes, recipient category, format  |
| `data_export.dlp_assessment_completed`        | DLP assessment concludes                   | assessment reference, findings summary, required transforms |
| `data_export.disclosure_assessment_completed` | Disclosure assessment concludes            | assessment reference, cohort outcome, cumulative outcome    |
| `data_export.approved`                        | An approver approves                       | approver reference, permitted field set digest              |
| `data_export.denied`                          | The request is refused                     | reason code, failed check                                   |
| `export_artifact.generated`                   | The artifact is produced                   | manifest digest, artifact reference, expiry                 |
| `export_artifact.delivered`                   | The artifact reaches the recipient channel | delivery reference, transfer channel                        |
| `export_artifact.accessed`                    | The artifact is opened or downloaded       | access instant, accessor reference, access count            |
| `data_export.revoked`                         | Authorization is withdrawn before expiry   | revoking authority, reason code                             |
| `export_artifact.expired`                     | The artifact expiry passes                 | expiry instant                                              |
| `data_export.destruction_attested`            | The recipient attests destruction          | attestation reference, attesting party, attested instant    |

`data_export.destruction_attested` records an **attestation**, which is a
statement by the recipient, not a verified fact. Nothing in this family
may be read as evidence that a copy outside the platform ceased to exist
(`P12-EXP-013`, `P12-DLP-004`).

---

## 6. `disclosure_control.*` — 7 types

| Event type                                   | Emitted when                           | Key payload                                       |
| -------------------------------------------- | -------------------------------------- | ------------------------------------------------- |
| `disclosure_control.risk_assessed`           | A disclosure-risk assessment completes | cohort sizes band, rule set version, outcome      |
| `disclosure_control.suppression_applied`     | Values are suppressed                  | suppression rule reference, suppressed cell count |
| `disclosure_control.exception_requested`     | An override is requested               | requested rule, justification reference           |
| `disclosure_control.exception_approved`      | A reviewer approves the override       | reviewer reference, bounded conditions            |
| `disclosure_control.exception_denied`        | A reviewer refuses                     | reason code                                       |
| `disclosure_control.cumulative_risk_flagged` | Cumulative release crosses a rule      | release history reference, rule reference         |

---

## 7. Ownership and consumption

| Family                 | Owner                      | Consumers                                          |
| ---------------------- | -------------------------- | -------------------------------------------------- |
| `privileged_access.*`  | PACK-12 privileged context | Audit core, oversight surfaces, PACK-17 incident   |
| `break_glass.*`        | PACK-12 privileged context | Audit core, PACK-17 incident, out-of-band gateway  |
| `search_*`             | PACK-12 search context     | Audit core, disclosure-control reviewer            |
| `data_export.*`        | PACK-12 export context     | Audit core, PACK-09 retention, disclosure reviewer |
| `disclosure_control.*` | PACK-12 export context     | Audit core, transparency surfaces                  |

Whether these are one service or three bounded contexts is
`OD-P12-04`, open. The event families are stable either way; the
catalogue deliberately does not assume the answer.

---

## 8. What this catalogue is not

It is a specification of names, payload obligations and prohibitions. It
is **not** a schema registry entry, a JSON Schema file, or an
implementation. No `contracts/events/*.schema.json` file is added by this
round. Schema authoring belongs to the implementation round and, for the
registry runtime, to PACK-13.

---

## 9. `disclosure_control.governed_publication_observed` — scope note

This event records that a governed publication occurred elsewhere. It
carries certification, publication-decision and rendition references and
**no result content**. PACK-12 does not certify, does not decide closure
and does not publish (`P12-VOTE-005`); it observes and audits the fact.
An event of this type is never evidence that PACK-12 released anything.

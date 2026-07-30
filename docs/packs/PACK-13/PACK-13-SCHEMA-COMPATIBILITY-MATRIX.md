# PACK-13 — Schema Compatibility Matrix

Specification-only. No code. Not implemented.

Companion to `PACK-13-SPECIFICATION.md` §12–§17,
`ADR-073-CANONICAL-SCHEMA-REGISTRY.md` and
`ADR-074-API-AND-EVENT-CONTRACT-EVOLUTION.md`.

---

## 1. The five modes

| Mode                                 | Meaning                       | Who is safe                      |
| ------------------------------------ | ----------------------------- | -------------------------------- |
| **backward compatible**              | New readers can read old data | Consumers upgrade first          |
| **forward compatible**               | Old readers can read new data | Producers upgrade first          |
| **full compatible**                  | Both directions hold          | Either order                     |
| **breaking**                         | Neither direction holds       | Nobody, without a migration plan |
| **unknown / manual review required** | The checker cannot decide     | Nobody, until a human decides    |

`P13-COMPAT-005` `unknown` is the **default** when the automated checker
does not produce a definite answer. It is never collapsed into
"probably backward compatible".

---

## 2. Change classification

`Auto` = the checker may classify it. `Review` = semantic review is
mandatory regardless of what the checker says.

| Change                                                 | Structural class       | Verdict                                        | Why                                                                                    |
| ------------------------------------------------------ | ---------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| Add optional field with no new obligation              | additive               | backward — **Auto**                            | Old readers ignore it                                                                  |
| Add optional field that carries meaning by its absence | additive               | **Review**                                     | The absent case previously meant something                                             |
| Add optional field creating a new consumer obligation  | additive               | **Review → likely breaking**                   | Consumers now must act on it                                                           |
| Add required field                                     | additive               | **breaking**                                   | Old producers become invalid                                                           |
| Remove field                                           | subtractive            | **breaking**                                   | A consumer reads it                                                                    |
| Rename field                                           | subtractive + additive | **breaking**                                   | It is a removal wearing a costume                                                      |
| Widen a type (int → long)                              | modify                 | forward-risk — **Review**                      | Old readers may truncate                                                               |
| Narrow a type                                          | modify                 | **breaking**                                   | Existing values stop fitting                                                           |
| Change type                                            | modify                 | **breaking**                                   | —                                                                                      |
| **Add enum value**                                     | additive               | **Review**                                     | Consumers may not handle it; `P13-EVO-012` forbids silent defaulting                   |
| **Change enum value meaning (same wire value)**        | invisible              | **breaking — always Review**                   | No differ can see it; every consumer is silently wrong                                 |
| Remove enum value                                      | subtractive            | **breaking**                                   | Historical data contains it                                                            |
| Tighten validation (pattern, min/max, required)        | modify                 | **breaking**                                   | Previously valid becomes invalid                                                       |
| Loosen validation                                      | modify                 | forward-risk — **Review**                      | Old readers may reject new values                                                      |
| Change a default                                       | modify                 | **breaking**                                   | The absent case now means something else                                               |
| **Change reason-code semantics**                       | invisible              | **breaking — always Review**                   | Auditors and operators read these; the wire value is unchanged                         |
| Add a reason code                                      | additive               | **Review**                                     | Consumers may fail closed on unknown codes — which is correct, and must be planned for |
| **Change event meaning without changing shape**        | invisible              | **breaking — always Review**                   | The whole historical record is reinterpreted                                           |
| **Change organization scope semantics**                | invisible              | **breaking — always Review**                   | An isolation boundary moved (`FIR-INV-013`)                                            |
| **Change identity linkage**                            | invisible              | **breaking — always Review + security review** | May defeat `FIR-INV-001` / `FIR-INV-002`                                               |
| **Change retention semantics**                         | invisible              | **breaking — always Review + legal review**    | A record's lawful lifetime changed                                                     |
| **Change authorization implication**                   | invisible              | **breaking — always Review + security review** | A field that gated access no longer does                                               |
| **Change legal effect**                                | invisible              | **breaking — always Review + legal review**    | No tool can see it; the consequence is external to the system                          |
| Change pagination contract                             | modify                 | **breaking**                                   | Callers page incorrectly                                                               |
| Change error contract                                  | modify                 | **breaking**                                   | Callers branch on it                                                                   |
| Change idempotency contract                            | modify                 | **breaking**                                   | Duplicate suppression changes                                                          |
| Reorder fields (JSON)                                  | cosmetic               | full — **Auto**                                | Order is not semantic in JSON                                                          |
| Reformat / reindent                                    | cosmetic               | full — **Auto**                                | `content_digest` is unchanged after format-specific canonicalization (`P13-REG-005`)   |
| Documentation-only change                              | cosmetic               | full — **Auto**                                | —                                                                                      |

`P13-COMPAT-006` Every row marked **invisible** shares one property: the
serialized bytes may be identical before and after. This is why §13's
compatibility checkers are declared necessary and not sufficient, and why
`P13-FMT-004` requires semantic assessment on every change.

---

## 3. Required review by change class

| Class                     | Owner sign-off | Security review          | Privacy review           | Legal review | Consumer readiness            |
| ------------------------- | -------------- | ------------------------ | ------------------------ | ------------ | ----------------------------- |
| Cosmetic                  | yes            | —                        | —                        | —            | —                             |
| Additive, no obligation   | yes            | —                        | —                        | —            | notify                        |
| Additive with obligation  | yes            | if authorization touched | if data category touched | —            | **required**                  |
| Enum extension            | yes            | —                        | —                        | —            | **required**                  |
| Breaking, structural      | yes            | —                        | —                        | —            | **required + migration plan** |
| Identity linkage          | yes            | **required**             | **required**             | —            | **required**                  |
| Retention semantics       | yes            | —                        | **required**             | **required** | **required**                  |
| Authorization implication | yes            | **required**             | —                        | —            | **required**                  |
| Legal effect              | yes            | **required**             | **required**             | **required** | **required**                  |

---

## 4. Per-format checker capability — stated honestly

| Format                 | Checker can decide                                                     | Checker cannot decide                                                     |
| ---------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| JSON Schema            | field presence, type, required, enum membership, validation tightening | any meaning change; obligation created by a new field                     |
| OpenAPI                | endpoint/parameter/response shape, status codes                        | semantics of a status code; authorization implication; pagination meaning |
| AsyncAPI               | channel and message shape                                              | event meaning; ordering-scope change                                      |
| SQL migration metadata | ordering, checksum, applied state                                      | whether a column drop loses a governed fact                               |
| protobuf/Avro (future) | the format's own compatibility rules                                   | all of the invisible classes above                                        |

`P13-COMPAT-007` No format's checker can decide any row marked
**invisible** in §2. The registry therefore records both the automated
verdict _and_ the human assessment, and they are separate fields — a
`CompatibilityAssessment` that carries only the tool's answer is
incomplete.

---

## 5. Coexistence and deprecation window classes

| Change class             | Minimum coexistence                                | Deprecation announcement                             | Retirement requires                                        |
| ------------------------ | -------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------- |
| Additive, no obligation  | none                                               | —                                                    | —                                                          |
| Additive with obligation | one consumer-migration cycle                       | yes                                                  | consumer readiness confirmed                               |
| Enum extension           | one consumer-migration cycle                       | yes                                                  | consumer readiness confirmed                               |
| Breaking, structural     | **two** cycles                                     | yes, dated                                           | **all** registered consumers migrated or explicitly waived |
| Invisible-class change   | **two** cycles + explicit consumer acknowledgement | yes, dated, with the semantic change stated in prose | acknowledgement from every registered consumer             |

## 6. Digest and version identity in the compatibility workflow

`P13-COMPAT-009` The compatibility workflow reads `content_digest` to
answer one question only: **is this byte-identical, after this format's
canonicalization, to something already registered?** It never infers
version identity, semantic equivalence or compatibility from digest
equality (`P13-REG-005`..`005g`).

| Situation                                       | Digest    | Version identity            | Outcome                                                                                                     |
| ----------------------------------------------- | --------- | --------------------------- | ----------------------------------------------------------------------------------------------------------- |
| New content, new version                        | new       | new `schema_version_id`     | normal path; compatibility assessed                                                                         |
| Reformatted, semantically unchanged             | **same**  | no new version needed       | cosmetic; no republication                                                                                  |
| Identical content, accidental republication     | same      | —                           | **blocked or reason-coded review** (`SCHEMA_DUPLICATE_CONTENT`, `SCHEMA_DUPLICATE_CONTENT_REVIEW_REQUIRED`) |
| Identical content, deliberate governed re-issue | same      | **new `schema_version_id`** | permitted **only** with `governance_justification` (`SCHEMA_IDENTICAL_CONTENT_REPUBLICATION_APPROVED`)      |
| Different content, same meaning                 | different | new version                 | the registry does **not** claim they are equivalent                                                         |

`P13-COMPAT-010` **Canonicalization is not a semantic normalizer.** Each
format's enumerated normalizations are recorded in specification §13; a
difference outside that enumeration produces a different digest, and the
registry draws no conclusion from that beyond "not byte-identical".

---

## 7. Coexistence and deprecation windows

`P13-COMPAT-008` The numeric window lengths are **open configuration
decisions** (OD-P13-03) and are not fixed by this specification. What is
fixed is that they exist, are per-class, and are enforced by the registry
rather than by memory.

# Document Service architecture

> PACK-11, `FIR-ROADMAP-001`. ADR-055 through ADR-060.
> Implementation status: `reference_implementation`.

## Position in the system

`document-service` is the eleventh service and a **leaf**: nothing imports
it, and it imports only `epd2-core` and `epd2-audit-core`.

```text
PACK-08 organization-service ──(typed scope references)──┐
PACK-09 compliance-service ───(record class, hold, ──────┤
                               destruction authorization) │
                                                          ▼
                                              PACK-11 document-service
                                                          │
                                   ┌──────────────────────┴───────────────┐
                                   │                                      │
                        canonical event stream                  published interface
                        (25 event types, 4 of                   (resolution, signature,
                         them publicly projectable)              admissibility, rendition)
```

Consumers do not import this service. They read the event stream, or they
ask through the published interface and get a reason-coded answer.

## The aggregates

| Aggregate               | Owns                                                                    |
| ----------------------- | ----------------------------------------------------------------------- |
| `GovernedDocument`      | The register entry: kind, sensitivity, custodian, review requirement, current version pointer, chain head, retention and hold bindings. |
| `DocumentVersion`       | One immutable statement of content at a moment, plus its place in the chain. |
| `ReviewRecord`          | One recorded review of one version. Append-only.                        |
| `ApprovalRecord`        | The act that turns a proposal into a record. One per version.           |
| `PublicationAuthorization` | The separate authority to publish. One per version.                  |
| `PublicationRendition`  | A citable published form. Several per version are legitimate.           |
| `SupersessionRecord`    | "Version N is no longer current; version M is."                         |
| `RevocationRecord`      | "This version no longer has effect." Never "this version is gone."      |
| `SignatureDetermination` | A recorded, version-bound signature determination.                     |
| `AdmissibilityDetermination` | A recorded, version- and procedure-bound admissibility determination. |
| `EvidenceRecord`        | A governed *use* of an exact version, with provenance and custody.      |
| `EvidenceBundle`        | An ordered, sealable, citable set of evidence.                          |

## The command frame

Every state-changing command routes through one private frame (`_guard`)
and one private tail (`_finish`). A guard a command can forget is a guard
that is not in force.

```text
_guard:  1. scope (undetermined denies, before any read or write)
         2. authority (resolved through the port; a role_code is not proof)
         3. role incompatibility, re-checked now + per-act separation
         4. conflict declaration (None and 'undeclared' both fail closed)
         5. idempotency (command store first, audit store as second defence)
         6. optimistic concurrency (after idempotency, so a true replay works)

command body: load chain → verify chain → transition → store

_finish: audit append → event publish → idempotency record
         (audit first: an event without an audit row is an unaccountable act)
```

## Why the chain is verified on every command

`_load_chain` re-verifies the whole version history before any governed act
on an existing document. That costs one hash recomputation per version and
buys the property `FIR-INV-010` states: a governed act recorded against a
history that no longer verifies would add a trustworthy-looking row to an
untrustworthy history.

## Storage

Six rules enforced by the store rather than by convention: no delete method
anywhere; scope-filtered multi-record queries; append-only versions with
head-linked appends; a content-addressed, write-once content store;
optimistic concurrency left to the application layer; and in-memory
adapters that are explicitly not a data plane.

## Read paths

There are exactly three, and content leaves through only one.

| Path                          | Carries                                                   |
| ----------------------------- | --------------------------------------------------------- |
| `read_document_content`       | The bytes. Authority-, profile-, independence- and integrity-checked. |
| `restricted_projection`       | Governance metadata. No content, no title, no finding text. |
| `build_public_projection`     | Publication facts. No content, no title, no sensitivity.   |

## Deferred to other packs

Production storage and the event bus (PACK-13); privileged, JIT and
break-glass access, controlled search and DLP (PACK-12); identity, keys and
external trust providers (PACK-14); retention schedules, legal-hold
decisions and destruction authorizations (PACK-09).

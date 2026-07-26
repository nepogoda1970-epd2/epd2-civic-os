# compliance-service

PACK-09's one wholly new service (ADR-038). Owner of records
classification and retention, controlled disposal and destruction
evidence, Legal Hold, the Data Catalog & Processing Registry, governed
procedural cases and deadlines, data-subject/legal requests, and party
arbitration/internal disputes.

## Modules

| Module           | Contents                                                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `domain.py`      | Immutable entities and their structural invariants (timezone-awareness, append-only deadline history, role separation, hold scoping) |
| `events.py`      | Eight canonical event builders plus the audit `*_full_state_payload` snapshots                                                       |
| `storage.py`     | Storage `Protocol`s and in-memory reference adapters (no delete method anywhere; create-once evidence)                               |
| `application.py` | Commands with scope guards, `event_id` idempotency, Audit Core append and reason-coded refusals                                      |
| `exceptions.py`  | One class per registered reason code (`contracts/reason-codes/pack-09.yml`)                                                          |

## Hard boundaries

No document-byte storage (PACK-11), no finance reporting or
Rechenschaftsbericht (PACK-10), no privileged/break-glass administration
or DLP (PACK-12), no production database, event bus or schema registry
(PACK-13), no real IAM/eID or credential issuance (PACK-14), no voting
threat model or cryptographic voting (PACK-15/16), no production incident
response (PACK-17), no user-facing application (PACK-18).

This service holds **no identity data**: a natural person appears only as
a per-case, randomly minted `CasePartyReference` (see
`domain.mint_case_party_reference`) or an opaque organizational authority
reference. Identity verification is recorded as a _status plus an opaque
reference_, never as an attribute, document or eID assertion.

It also holds **no link to voting**: nothing here references a `Ballot`,
`VoteEnvelope`, `Tally`, `ResultPublication` or `Delegation`, and the
package imports nothing from `epd2_voting_service`,
`epd2_tally_service` or `epd2_delegation_service`
(`tests/repository/test_service_boundaries.py`).

## No claim of legal compliance

This service provides a governed workflow, evidence references and
auditability. It does **not** determine, and makes no claim about,
whether any retention schedule, legal basis, deadline computation,
data-subject response or arbitration decision satisfies the GDPR, the
BDSG, the Parteiengesetz or any other law. `LegalBasis` is a _managed
classification field_, not a legal sufficiency assessment. Every legal
determination stays a human judgement made outside this system.

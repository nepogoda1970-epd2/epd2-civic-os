**Round:** PACK-14 — implementation candidate. **NOT PASS. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Repository version:** `0.14.0` · **Canon version:** unchanged at `0.8.0`
**External GitHub Actions has not run against this round.**

# PACK-14 — Privacy Verification

## 1. The data-minimization commitments, and where each is enforced

| Commitment                                                                                  | Enforcement                                                                                                    | Test                                                                         |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| No password, OTP, recovery code, private key or full WebAuthn assertion in any record class | No dataclass in the package has a field that could hold one; `PROHIBITED_SECRET_KEYS` refuses them in payloads | `test_no_secret_key_survives_payload_validation` (26 keys)                   |
| No identity document content outside its PACK-11 bundle                                     | Proofing holds `IdentityEvidenceReference` only                                                                | `test_a_proofing_event_carries_a_bundle_reference_and_no_attributes`         |
| Raw contact values replaced by tokenized references                                         | `AccountContact` stores a digest and a masked form                                                             | `test_a_contact_event_carries_a_tokenized_reference_and_no_address`          |
| No record class carries a cross-domain identifier                                           | `PROHIBITED_IDENTIFIER_KEYS`; `assert_reference_crosses_boundary`                                              | `test_every_identifier_space_except_the_scoped_one_is_refused_at_a_boundary` |
| Session activity recorded coarsely; no page-level tracking                                  | `SessionRecord.last_activity_at` is a single timestamp                                                         | field set                                                                    |
| Analytics carries no identity; WS-03 carries no analytics                                   | Metric label allowlist; WS-03 gets no session at all                                                           | `test_metric_labels_admit_no_per_person_dimension`                           |

## 2. Observability

`MetricLabels` admits eight label keys, every one an enum value or a
registered reason code. There is no `account`, no `subject` and no
`origin` label, because each would make the metric a per-person time
series. A labelled series below `MINIMUM_DISCLOSABLE_COUNT` (5) is
**withheld entirely** rather than rounded: a rounded low count still
tells a reader that the combination occurred at all, which for a rare
label set is the disclosure.

`redact()` walks nested mappings and sequences and **replaces** rather
than truncates — a truncated password is still a password prefix.

## 3. The identifier separation, in one paragraph

What leaves this service is a `ScopedIdentityReference`: a SHA-256 digest
over the purpose, the organizational scope, the domain owner, the
identifier space, the value and a per-deployment secret salt. Two
references derived for two purposes from the same account do not compare
equal, and neither can be reversed to the account without the governed
mapping. The salt requirement is enforced (`>= 32 bytes`) because a
reference anyone can recompute from an `account_id` is the `account_id`
with extra steps.

## 4. Retention

Ten record classes, each with a provisional duration, a legal-hold flag
and a stated deletion effect. The reference schema carries the metadata
these constraints operate on rather than leaving it to a future
deployment: every table whose class has a schedule carries its retention
class, and the hold and dispute columns
`assert_disposition_permitted` reads are columns, not attributes of an
in-process object. Ten **expiry indexes** exist in the applied schema, so
a disposal job is an indexed scan rather than a full table scan somebody
eventually stops running — `ix_voting_handoff_expires_at` is the one
worth naming, because constraint 3 below requires those records to be
removed early and as a set. **Every `duration_confirmed` flag is
`False`**, and a test asserts it — `OD-P14-07` is open and the
provisional schedule governs storage, not destruction.

The four deletion constraints from the retention matrix are enforced in
`assert_disposition_permitted`:

1. evidence required by a dispute, an oversight obligation or a hold is
   not destroyed;
2. an attempted deletion under hold refuses, and an **unknown hold state
   fails closed**;
3. voting-handoff records are deleted **as a set** (recorded in the
   binding's `deletion_effect`), because deleting one side of a pair can
   make the surviving side identifying;
4. contact-handle reuse is embargoed (`assert_reuse_permitted`) so a
   later holder cannot inherit another person's history.

## 5. Data subject rights

PACK-14 adds **no parallel mechanism and no new export surface**. Access,
correction, deletion, objection and export are governed by PACK-09 and
PACK-12, and the API catalogue contains no export operation — a test
asserts that. The runnable reference adapter routes twelve operations and
**none of them is an export, a listing across accounts, or a reverse
resolution**; `service_api.ROUTED_OPERATIONS` is a named constant, so
what is reachable can be read rather than inferred.

## 6. Minimization at rest, checked rather than asserted

The reference persistence path is where minimization either holds or
quietly stops holding, so it is tested at the row level rather than at
the type level.

- `codecs.encode_value` refuses `bytes` outright — the one Python type a
  raw key, salt or seed would arrive as — and refuses a naive datetime,
  because a timestamp that lost its offset breaks every deadline the
  privacy schedule depends on.
- A persistence test sweeps **every row of every one of the 29 tables**
  for a raw contact value or a secret and fails if it finds one. It is a
  sweep rather than a per-table assertion so that a table added by a
  future migration is covered the moment it exists.
- `ApiResponse.__post_init__` runs `assert_response_safe`, so a response
  carrying a prohibited identifier cannot be **constructed**, let alone
  returned. Two tests check the session inventory specifically, because a
  session list is the response most likely to acquire an identifier for
  convenience.
- `voting_handoff_issuance` has no account column of any kind, and the
  migration says a later one adding it would reverse ADR-088.

## 7. What this round does not establish

That any retention duration is lawful; that a deployed system's logs
carry no secret (this repository has no logging framework to verify);
that a real analytics pipeline honours the label allowlist. Each is a
deployment obligation, recorded in `PACK-14-OPEN-ITEMS.md`.

# API-05 developer report — WORKING 0.1 PRESEAL

## Result

`WORKING_PRESEAL_NOT_ACCEPTED`

The provider-neutral external integration boundary is implemented. It may not
be sealed because API-04 is not yet independently accepted in canonical
governance. No accepted API-04 SHA has been invented.

## Lineage

| Baseline | Identity | State |
| --- | --- | --- |
| DATA-06 | `8cba01997e4943f6d3c2b3fc1fe11e2c3527cd6c39123171a827fb8e3669cbf1` | accepted |
| API-01 C5 | `cea2fb0e23ee174e802ec1899cf62e570e5c8659a0f31c7e6c3c3955bffa3d27` | accepted |
| API-02 C13 | `9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9` | accepted |
| API-03 C5 | `5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55` | accepted |
| API-04 | `null` | not accepted; exact final predecessor remains blocked |

Working API-04 assumptions were taken from repository commit
`70bfbd7f1d50b43516da2d07275787e78cd23108`, snapshot workflow run
`33565519471`, artifact `9822942448`. This is not presented as an accepted
predecessor.

## Implemented boundary

- 11 typed provider classes; one executable synthetic/non-live email profile;
- four transport patterns: synchronous, callback, reconciliation, and the
  structural redirect/handoff policy model;
- one provider-bound callback route template;
- real separate-process TCP/HTTPS provider and callback harness;
- TLS certificate verification with temporary synthetic EC material;
- signed HMAC-SHA256 callback path, freshness, key/provider binding, rotation
  overlap, and validate-before-replay ordering;
- provider-scoped idempotency and replay singularity;
- PostgreSQL operational state, callback receipt, attempts, claims, and
  reconciliation records;
- explicit failure classes, bounded exponential backoff with jitter,
  Retry-After bounding, and circuit recovery probing;
- suspension and queued commit-time reauthorization;
- API-03 service-identity port and API-04 claim-publication port;
- outbound allowlist construction, recursive redaction, provider-local ID
  isolation, and non-authoritative `_CLAIMED` signals;
- 16 behavioral source mutations.

## Verification summary

The authoritative values are generated into
`validation/api05/validator_result.json` by `scripts/validate_api05.py`.
Developer PASS requires zero failed or blocked gates, including PostgreSQL 16.

## FIR disposition

**Implemented/advanced in API-05 scope:** `FIR-SEC-003`, `FIR-VENDOR-001`,
`FIR-VENDOR-002`, `FIR-VENDOR-003`, `FIR-VENDOR-004`, `FIR-VENDOR-005`,
`FIR-API-001`, `FIR-ID-001`, `FIR-AUTH-001`, `FIR-DATA-004`, `FIR-TEST-001`,
`FIR-TEST-002`, `FIR-EDGE-001`, `FIR-TIME-001`.

**Partially advanced only:** `FIR-REL-001`, `FIR-READY-001`,
`FIR-CRYPTO-001`, `FIR-SEC-SECRET-001`, `FIR-OPS-001`,
`FIR-INFRA-SOV-001`.

**Intentionally unchanged/deferred:** voting, BSI/CC readiness, commercial
provider selection, legal effect, production credential custody, HSM/KMS,
production deployment, capacity, incident operation, and final SEC.

**New FIR IDs:** none.

## Open gate

After API-04 acceptance: obtain exact accepted API-04 bytes/SHA/run/evidence,
mechanically reconcile interfaces, rerun every test and inherited regression,
then create the first `CANDIDATE_NOT_ACCEPTED` seal. Until then this work is
correctly PRESEAL and cannot be called API-05 accepted or closed.


# CTRL-03 Stage Contract

## Status

`CANDIDATE_NOT_ACCEPTED`. CTRL-02 authoritative predecessor reconciliation is complete; CTRL-03 remains unaccepted until independent governed acceptance of the exact candidate bytes.

## Scope

CTRL-03 governs credential, trust and key lifecycle intent, authorization, evidence and safe read models. It does not take custody of private keys, raw secrets, password equivalents, recovery material, provider tokens or voting keys.

The runtime separates human credentials, passkeys, recovery credentials, sessions, authority projections, service credentials, mTLS certificates, JWS signing keys, JWKS entries, encryption-key references, provider-secret references and external voting-key references.

## Control invariants

- Exact region and organization scope; no hierarchy-derived or cross-region authority.
- Request, approval, commit-time reauthorization, custody execution and independent review are distinct.
- High-impact actions require both Security and Trust Custodian approval classes.
- Provider, target, authority, trust-set and CTRL-02 revisions are rechecked at commit.
- Cryptoperiods and algorithm/profile pairs are explicit; PQ algorithms remain inactive.
- Rotation links old and new identities and bounds overlap to 24 hours.
- JIT secret access is reference-only, requires two distinct approval references and expires within 15 minutes.
- Break-glass authority expires within one hour and follows declare, approve, activate, contain, rotate/revoke, verify and review.
- Regional issuance never uses the root hot path for ordinary work.
- Recovery ceremonies cannot silently lower their threshold.
- Voting keys remain external references and never enter generic CTRL custody.
- Audit records are append-only, hash-linked and contain no secret payload.

## Predecessor identities

- CTRL-01: `ACCEPTED / CLOSED`; candidate SHA-256 `07134db175587a9aa441fe87a811c7cfca6cc8dfbd30006279dd0edb598783b5`, size `190099`.
- CTRL-02: `ACCEPTED / CLOSED`; authoritative candidate SHA-256 `f58bafe758f19c0b40d3a525d85d0315052c01bc9ed14eae9973079a4dfb993e`, size `16720456`, acceptance run `33690561259`, workflow head `a70e2bfef7a668ee5158475712827bbc50f6d5fd`.

## Acceptance boundary

Candidate validation may report `PASS` only after exact CTRL-02 authoritative identity reconciliation. The candidate must still never self-report CTRL-03 as accepted, production-ready, legally activated, BSI/CC certified or canonically sealed.

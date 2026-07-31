-- PACK-15 migration 0002 — expand — the spent-nonce SET
--
-- The load-bearing table of ADR-093. It is a **set**: the nonce is the
-- primary key and there is no value column. It answers "was this nonce
-- spent?" and can never answer "what did it produce?", because there is
-- nowhere in this table for that answer to live.
--
-- Adding a `voting_credential_id` column here would reconstruct
-- `person -> assertion -> credential` in one migration. That is why the
-- table has exactly three columns and a repository test asserts it.

CREATE TABLE spent_nonce (
    nonce                    TEXT NOT NULL PRIMARY KEY,
    voting_context_reference TEXT NOT NULL,
    spent_at_bucket          TEXT NOT NULL
);

CREATE INDEX ix_spent_nonce_context ON spent_nonce(voting_context_reference);

-- The bounded idempotency window. It is the ONLY place an issuance key
-- and a credential are ever associated, the association is explicit, and
-- `expires_at` is NOT NULL so it cannot become durable by omission.
CREATE TABLE credential_issuance_idempotency (
    idempotency_key      TEXT NOT NULL PRIMARY KEY,
    voting_credential_id TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    expires_at           TEXT NOT NULL,
    FOREIGN KEY (voting_credential_id) REFERENCES voting_credential(voting_credential_id),
    CHECK (expires_at > created_at)
);

CREATE INDEX ix_credential_idempotency_expiry ON credential_issuance_idempotency(expires_at);

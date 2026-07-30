-- PACK-14 migration 0010 — expand — replay prevention and idempotency
--
-- Every table here carries an expiry index, because a replay-prevention
-- store that grows without bound is a store somebody eventually stops
-- querying.

CREATE TABLE replay_nonce (
    nonce_digest  TEXT NOT NULL PRIMARY KEY,
    purpose       TEXT NOT NULL,
    consumed_at   TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    CHECK (length(nonce_digest) = 64)
);
CREATE UNIQUE INDEX uq_nonce_record ON replay_nonce(nonce_digest);
CREATE INDEX ix_replay_nonce_expires_at ON replay_nonce(expires_at);

CREATE TABLE idempotency_record (
    idempotency_key  TEXT NOT NULL PRIMARY KEY,
    operation        TEXT NOT NULL,
    request_digest   TEXT NOT NULL,
    recorded_at      TEXT NOT NULL,
    CHECK (length(request_digest) = 64)
);
CREATE INDEX ix_idempotency_record_recorded_at ON idempotency_record(recorded_at);

CREATE TABLE external_assertion_seen (
    assertion_id  TEXT NOT NULL PRIMARY KEY,
    seen_at       TEXT NOT NULL
);
CREATE INDEX ix_external_assertion_seen_at ON external_assertion_seen(seen_at);

CREATE TABLE authentication_attempt (
    attempt_id       TEXT NOT NULL PRIMARY KEY,
    workspace        TEXT NOT NULL,
    method_class     TEXT NOT NULL,
    outcome_kind     TEXT NOT NULL,
    reason_code      TEXT NOT NULL,
    attempted_at     TEXT NOT NULL,
    retention_class  TEXT NOT NULL DEFAULT 'authentication_attempts',
    document         TEXT NOT NULL
);
-- 90 days, provisionally: the shortest schedule in the retention matrix.
CREATE INDEX ix_authentication_attempt_attempted_at ON authentication_attempt(attempted_at);

CREATE TABLE authentication_challenge (
    challenge_id  TEXT NOT NULL PRIMARY KEY,
    workspace     TEXT NOT NULL,
    method        TEXT NOT NULL,
    issued_at     TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    consumed_at   TEXT,
    document      TEXT NOT NULL
);
CREATE INDEX ix_authentication_challenge_expires_at ON authentication_challenge(expires_at);

CREATE TABLE webauthn_challenge (
    challenge_id  TEXT NOT NULL PRIMARY KEY,
    account_id    TEXT NOT NULL,
    ceremony      TEXT NOT NULL,
    issued_at     TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    consumed_at   TEXT,
    document      TEXT NOT NULL,
    CHECK (ceremony IN ('registration','authentication'))
);
CREATE INDEX ix_webauthn_challenge_expires_at ON webauthn_challenge(expires_at);

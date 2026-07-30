-- PACK-14 migration 0008 — expand — bootstrap and voting handoff
--
-- Three single-use artifacts, three digest-unique tables. Single-use is
-- meaningless if two rows can hold the same value, so the uniqueness is
-- a constraint rather than a convention.
--
-- `voting_handoff_issuance` has NO account column, no session column and
-- no scoped-reference column. That absence is ADR-088's non-reversibility
-- property expressed as a schema, and a future migration that adds one
-- would be reversing the decision, not extending it.

CREATE TABLE bootstrap_request (
    request_id       TEXT NOT NULL PRIMARY KEY,
    workspace        TEXT NOT NULL,
    audience_origin  TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    expires_at       TEXT NOT NULL,
    document         TEXT NOT NULL
);
CREATE INDEX ix_bootstrap_request_expires_at ON bootstrap_request(expires_at);

CREATE TABLE bootstrap_response (
    response_id      TEXT NOT NULL PRIMARY KEY,
    request_id       TEXT NOT NULL REFERENCES bootstrap_request(request_id),
    workspace        TEXT NOT NULL,
    audience_origin  TEXT NOT NULL,
    value_digest     TEXT NOT NULL,
    issued_at        TEXT NOT NULL,
    expires_at       TEXT NOT NULL,
    redeemed_at      TEXT,
    document         TEXT NOT NULL,
    CHECK (length(value_digest) = 64)
);
CREATE UNIQUE INDEX uq_bootstrap_response_digest ON bootstrap_response(value_digest);
CREATE INDEX ix_bootstrap_response_expires_at ON bootstrap_response(expires_at);

CREATE TABLE bootstrap_redemption (
    response_id   TEXT NOT NULL PRIMARY KEY,
    redemption_id TEXT NOT NULL,
    workspace     TEXT NOT NULL,
    redeemed_at   TEXT NOT NULL,
    value_digest  TEXT NOT NULL,
    document      TEXT NOT NULL
);

CREATE TABLE voting_handoff_issuance (
    artifact_id        TEXT NOT NULL PRIMARY KEY,
    value_digest       TEXT NOT NULL,
    voting_context_id  TEXT NOT NULL,
    purpose            TEXT NOT NULL,
    audience_origin    TEXT NOT NULL,
    issued_at          TEXT NOT NULL,
    expires_at         TEXT NOT NULL,
    redeemed_at        TEXT,
    retention_class    TEXT NOT NULL DEFAULT 'voting_handoff_issuance',
    document           TEXT NOT NULL,
    CHECK (purpose = 'voting_entry'),
    CHECK (length(value_digest) = 64)
);
CREATE UNIQUE INDEX uq_voting_handoff_digest ON voting_handoff_issuance(value_digest);
-- Deleted early AND as a set: deleting one side of a pair can make the
-- surviving side identifying.
CREATE INDEX ix_voting_handoff_expires_at ON voting_handoff_issuance(expires_at);

CREATE TABLE voting_handoff_redemption (
    redemption_id      TEXT NOT NULL PRIMARY KEY,
    artifact_id        TEXT NOT NULL,
    voting_context_id  TEXT NOT NULL,
    redeemed_at        TEXT NOT NULL,
    document           TEXT NOT NULL
);

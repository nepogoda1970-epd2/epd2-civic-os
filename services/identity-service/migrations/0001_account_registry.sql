-- PACK-14 migration 0001 — expand — account registry
--
-- Accounts, technical locks, restrictions and closure requests. The
-- canonical status enum is NOT extended (OD-P14-01): `locked`,
-- `closure_pending` and `deleted_or_anonymized` are represented by the
-- three companion tables below, which is why they are three tables and
-- not three more values in `account_status`.

CREATE TABLE account_registry_record (
    account_id           TEXT    NOT NULL PRIMARY KEY,
    account_status       TEXT    NOT NULL,
    scope_level          TEXT    NOT NULL,
    scope_unit_id        TEXT    NOT NULL,
    created_at           TEXT    NOT NULL,
    activated_at         TEXT,
    anonymization_state  TEXT    NOT NULL,
    version              INTEGER NOT NULL,
    retention_class      TEXT    NOT NULL DEFAULT 'account_record',
    legal_hold           INTEGER NOT NULL DEFAULT 0,
    document             TEXT    NOT NULL,
    CHECK (account_status IN
        ('pending','active','restricted','suspended','recovery_pending','closed')),
    CHECK (version >= 1)
);

CREATE TABLE account_lock (
    lock_id          TEXT NOT NULL PRIMARY KEY,
    account_id       TEXT NOT NULL REFERENCES account_registry_record(account_id),
    cause            TEXT NOT NULL,
    reason_code      TEXT NOT NULL,
    locked_at        TEXT NOT NULL,
    expires_at       TEXT NOT NULL,
    released_at      TEXT,
    retention_class  TEXT NOT NULL DEFAULT 'suspicious_activity',
    legal_hold       INTEGER NOT NULL DEFAULT 0,
    document         TEXT NOT NULL
);
-- A lock without an expiry is a suspension wearing a lock's clothes.
CREATE INDEX ix_account_lock_expires_at ON account_lock(expires_at);
CREATE INDEX ix_account_lock_account ON account_lock(account_id);

CREATE TABLE account_restriction (
    restriction_id       TEXT NOT NULL PRIMARY KEY,
    account_id           TEXT NOT NULL REFERENCES account_registry_record(account_id),
    restriction_class    TEXT NOT NULL,
    authority_reference  TEXT NOT NULL,
    reason_code          TEXT NOT NULL,
    applied_at           TEXT NOT NULL,
    review_due_at        TEXT NOT NULL,
    expires_at           TEXT,
    lifted_at            TEXT,
    retention_class      TEXT NOT NULL DEFAULT 'suspicious_activity',
    legal_hold           INTEGER NOT NULL DEFAULT 0,
    document             TEXT NOT NULL,
    -- A restriction with no named authority is a lock, and locks live in
    -- their own table.
    CHECK (length(authority_reference) > 0)
);
CREATE INDEX ix_account_restriction_account ON account_restriction(account_id);

CREATE TABLE account_closure_request (
    closure_request_id  TEXT NOT NULL PRIMARY KEY,
    account_id          TEXT NOT NULL REFERENCES account_registry_record(account_id),
    state               TEXT NOT NULL,
    requested_at        TEXT NOT NULL,
    cooling_off_ends_at TEXT NOT NULL,
    resolved_at         TEXT,
    retention_class     TEXT NOT NULL DEFAULT 'account_record',
    legal_hold          INTEGER NOT NULL DEFAULT 0,
    document            TEXT NOT NULL,
    CHECK (state IN ('requested','cooling_off','cancelled','completed'))
);
-- At most one OPEN closure request per account. Partial, because a closed
-- account may legitimately carry several historical requests.
CREATE UNIQUE INDEX uq_open_closure_request
    ON account_closure_request(account_id)
    WHERE state IN ('requested','cooling_off');

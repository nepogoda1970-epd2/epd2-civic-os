-- PACK-14 migration 0004 — expand — session security
--
-- Both deadlines are NOT NULL. There is no nullable variant and no
-- sentinel meaning "unlimited": "no infinite session" is a schema
-- property here, not only a Python one.

CREATE TABLE session_record (
    session_id          TEXT    NOT NULL PRIMARY KEY,
    account_id          TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    workspace           TEXT    NOT NULL,
    origin              TEXT    NOT NULL,
    status              TEXT    NOT NULL,
    assurance           TEXT    NOT NULL,
    issued_at           TEXT    NOT NULL,
    last_activity_at    TEXT    NOT NULL,
    idle_deadline       TEXT    NOT NULL,
    absolute_deadline   TEXT    NOT NULL,
    refresh_family_id   TEXT    NOT NULL,
    retention_class     TEXT    NOT NULL DEFAULT 'session_history',
    legal_hold          INTEGER NOT NULL DEFAULT 0,
    document            TEXT    NOT NULL,
    CHECK (status IN ('active','idle','expired','revoked','quarantined')),
    CHECK (idle_deadline <= absolute_deadline)
);
CREATE INDEX ix_session_account ON session_record(account_id);
CREATE INDEX ix_session_refresh_family ON session_record(refresh_family_id);
-- Expired sessions are disposed of, and no session is exempt.
CREATE INDEX ix_session_absolute_deadline ON session_record(absolute_deadline);

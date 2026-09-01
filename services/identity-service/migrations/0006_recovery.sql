-- PACK-14 migration 0006 — expand — account recovery
--
-- Recovery evidence is the record class the retention matrix protects
-- most: never deleted while a dispute or a hold is open.

CREATE TABLE recovery_case (
    recovery_id           TEXT    NOT NULL PRIMARY KEY,
    account_id            TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    state                 TEXT    NOT NULL,
    requester_reference   TEXT    NOT NULL,
    requested_at          TEXT    NOT NULL,
    cooling_off_ends_at   TEXT,
    emergency             INTEGER NOT NULL DEFAULT 0,
    credentials_revoked   INTEGER NOT NULL DEFAULT 0,
    sessions_revoked      INTEGER NOT NULL DEFAULT 0,
    dispute_open          INTEGER NOT NULL DEFAULT 0,
    version               INTEGER NOT NULL,
    retention_class       TEXT    NOT NULL DEFAULT 'recovery_evidence',
    legal_hold            INTEGER NOT NULL DEFAULT 0,
    document              TEXT    NOT NULL
);
CREATE INDEX ix_recovery_case_account ON recovery_case(account_id);
-- At most one OPEN recovery case per account.
CREATE UNIQUE INDEX uq_open_recovery_case
    ON recovery_case(account_id)
    WHERE state NOT IN ('completed','rejected','cancelled');

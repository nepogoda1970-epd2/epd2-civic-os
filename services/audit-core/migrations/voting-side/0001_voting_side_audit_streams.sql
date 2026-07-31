-- PACK-15 migration 0001 (voting-side audit set) — expand
--
-- Streams AS-03 (credential) and AS-04 (voting integrity), applied to the
-- **voting-side audit database file**. Nothing here may carry a case
-- reference or an assertion reference, and nothing in the identity-side
-- set may carry a credential reference; the two sets are separate files,
-- so no query can span them and no foreign key between them exists.

CREATE TABLE audit_record_as03_credential (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    credential_reference     TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-03')
);

CREATE INDEX ix_as03_context
    ON audit_record_as03_credential(voting_context_reference);

-- AS-04 is aggregate-only: integrity observations about a context, never
-- about a participation. It has no subject column at all, which is why a
-- per-person "did they vote" question cannot be answered from it.
CREATE TABLE audit_record_as04_voting_integrity (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    observation_class        TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-04')
);

CREATE INDEX ix_as04_context
    ON audit_record_as04_voting_integrity(voting_context_reference);

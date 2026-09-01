-- PACK-15 migration 0001 (identity-side audit set) — expand
--
-- Streams AS-01 (eligibility) and AS-02 (assertion). One table per
-- stream, each with its own key space, applied to the **identity-side
-- audit database file**.
--
-- There is no unified table, no view and no foreign key spanning this set
-- and the voting-side set (AS-03, AS-04): those tables live in a
-- different database file, so the separation of ADR-097 is expressed as
-- the absence of a join path rather than as a policy on a shared table.
--
-- `stream` is CHECKed so a record cannot be written into the wrong stream
-- by a typo, and `tests/repository/test_pack15_audit_stream_separation.py`
-- asserts no table here carries a column from another stream's key space.

CREATE TABLE audit_record_as01_eligibility (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    case_reference           TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-01')
);

CREATE INDEX ix_as01_context
    ON audit_record_as01_eligibility(voting_context_reference);

-- AS-02 records the assertion lifecycle. It carries an assertion
-- reference and no case reference: an audit row holding both would
-- re-link the decision to the artifact that crossed the boundary.
CREATE TABLE audit_record_as02_assertion (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    assertion_reference      TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-02')
);

CREATE INDEX ix_as02_context
    ON audit_record_as02_assertion(voting_context_reference);

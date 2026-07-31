-- PACK-15 migration 0001 (neutral audit set) — expand
--
-- Streams AS-05 (independent observation) and AS-06 (system integrity),
-- plus the evidence-bundle export log. These belong to neither side, so
-- they get their own database file rather than being attached to one side
-- and quietly becoming a join path between the two.
--
-- No table here carries a case reference, an assertion reference or a
-- credential reference. AS-05 and AS-06 are context-scoped and
-- aggregate-only.

CREATE TABLE audit_record_as05_independent (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    observer_role            TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-05')
);

CREATE INDEX ix_as05_context
    ON audit_record_as05_independent(voting_context_reference);

CREATE TABLE audit_record_as06_system_integrity (
    record_id                TEXT NOT NULL PRIMARY KEY,
    stream                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    event_type               TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    recorded_at_bucket       TEXT NOT NULL,
    component                TEXT NOT NULL,
    payload_hash             TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL,
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (stream = 'AS-06')
);

CREATE INDEX ix_as06_context
    ON audit_record_as06_system_integrity(voting_context_reference);

-- The export log. `pre_closure = 1` is only storable with a dual-control
-- reference, so a pre-closure export without four eyes fails the CHECK
-- rather than an assertion someone can skip.
CREATE TABLE evidence_bundle_export (
    bundle_id                TEXT NOT NULL PRIMARY KEY,
    voting_context_reference TEXT NOT NULL,
    bundle_schema_version    INTEGER NOT NULL,
    key_identifier           TEXT NOT NULL,
    signature                TEXT NOT NULL,
    pre_closure              INTEGER NOT NULL,
    exported_by_role         TEXT NOT NULL,
    grant_reference          TEXT NOT NULL,
    dual_control_reference   TEXT,
    generated_at_bucket      TEXT NOT NULL,
    document                 TEXT NOT NULL,
    CHECK (bundle_schema_version >= 1),
    CHECK (pre_closure IN (0, 1)),
    CHECK (pre_closure = 0 OR dual_control_reference IS NOT NULL)
);

CREATE INDEX ix_evidence_bundle_context
    ON evidence_bundle_export(voting_context_reference);

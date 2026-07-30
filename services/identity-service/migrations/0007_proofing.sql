-- PACK-14 migration 0007 — expand — identity proofing references
--
-- Evidence stays in PACK-11. What is stored here is a bundle reference
-- and a decision; no document content has a column.

CREATE TABLE identity_proofing_case (
    case_id              TEXT    NOT NULL PRIMARY KEY,
    account_id           TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    person_record_id     TEXT,
    method               TEXT    NOT NULL,
    requested_assurance  TEXT    NOT NULL,
    state                TEXT    NOT NULL,
    started_at           TEXT    NOT NULL,
    version              INTEGER NOT NULL,
    retention_class      TEXT    NOT NULL DEFAULT 'proofing_evidence',
    legal_hold           INTEGER NOT NULL DEFAULT 0,
    document             TEXT    NOT NULL
);
CREATE INDEX ix_identity_proofing_case_account ON identity_proofing_case(account_id);

-- PACK-14 migration 0009 — expand — the governed mapping boundary
--
-- `expires_at` is NOT NULL. A mapping that never expires becomes the
-- global identifier by longevity, which is the failure mode that does
-- not look like a failure while it is happening.

CREATE TABLE identity_mapping (
    mapping_id        TEXT NOT NULL PRIMARY KEY,
    purpose           TEXT NOT NULL,
    scope_level       TEXT NOT NULL,
    scope_unit_id     TEXT NOT NULL,
    domain_owner      TEXT NOT NULL,
    source_reference  TEXT NOT NULL,
    status            TEXT NOT NULL,
    retention_class   TEXT NOT NULL,
    audit_reference   TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    expires_at        TEXT NOT NULL,
    legal_hold        INTEGER NOT NULL DEFAULT 0,
    document          TEXT NOT NULL,
    CHECK (length(audit_reference) > 0)
);
-- One purpose-scoped correlation per source; no second mapping to shadow
-- it.
CREATE UNIQUE INDEX uq_identity_mapping_purpose_scope_source
    ON identity_mapping(purpose, scope_level, scope_unit_id, source_reference);
CREATE INDEX ix_identity_mapping_expires_at ON identity_mapping(expires_at);

CREATE TABLE account_link_request (
    link_request_id  TEXT NOT NULL PRIMARY KEY,
    account_id       TEXT NOT NULL REFERENCES account_registry_record(account_id),
    kind             TEXT NOT NULL,
    state            TEXT NOT NULL,
    requested_at     TEXT NOT NULL,
    decided_at       TEXT,
    document         TEXT NOT NULL
);
CREATE INDEX ix_account_link_request_account ON account_link_request(account_id);

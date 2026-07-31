-- PACK-15 migration 0001 — expand — voting credentials
--
-- The voting-side store, in its own database file. Canon 10.1's forbidden
-- fields are structurally absent, and PACK-15 adds the two that make the
-- cut real: there is **no assertion_id column and no nonce column** here,
-- and no foreign key to any identity-side table, which are in separate
-- database files and therefore not referenceable at all.

CREATE TABLE voting_credential (
    voting_credential_id     TEXT NOT NULL PRIMARY KEY,
    credential_type          TEXT NOT NULL,
    status                   TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    issued_at_bucket         TEXT NOT NULL,
    expires_at               TEXT NOT NULL,
    redeemed_at              TEXT,
    revoked_at               TEXT,
    revocation_reason        TEXT,
    redemption_reference     TEXT,
    audience_origin          TEXT NOT NULL,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL DEFAULT 'credential_evidence',
    legal_hold               INTEGER NOT NULL DEFAULT 0,
    CHECK (expires_at > issued_at_bucket),
    CHECK (revoked_at IS NULL OR revocation_reason IS NOT NULL)
);

CREATE INDEX ix_voting_credential_context
    ON voting_credential(voting_context_reference, status);

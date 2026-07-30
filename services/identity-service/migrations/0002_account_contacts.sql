-- PACK-14 migration 0002 — expand — contact handles
--
-- Contacts are mutable attributes, never identifiers. The raw value has
-- no column: what is stored is a digest for uniqueness comparison and a
-- masked form for display.

CREATE TABLE account_contact (
    contact_id         TEXT    NOT NULL PRIMARY KEY,
    account_id         TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    channel_class      TEXT    NOT NULL,
    normalized_digest  TEXT    NOT NULL,
    masked_value       TEXT    NOT NULL,
    status             TEXT    NOT NULL,
    scope_level        TEXT    NOT NULL,
    scope_unit_id      TEXT    NOT NULL,
    added_at           TEXT    NOT NULL,
    verified_at        TEXT,
    changed_at         TEXT,
    retention_class    TEXT    NOT NULL,
    legal_hold         INTEGER NOT NULL DEFAULT 0,
    version            INTEGER NOT NULL,
    document           TEXT    NOT NULL,
    CHECK (channel_class IN ('email','phone')),
    CHECK (length(normalized_digest) = 64)
);

-- Uniqueness is SCOPED, never global: a global constraint would make the
-- address a cross-scope join key, which is what FIR-INV-013 forbids.
-- Partial, so a removed or replaced handle does not block the account
-- that legitimately holds it now.
CREATE UNIQUE INDEX uq_contact_scope_digest
    ON account_contact(channel_class, scope_level, scope_unit_id, normalized_digest)
    WHERE status NOT IN ('removed','replaced');

CREATE INDEX ix_account_contact_account ON account_contact(account_id);

-- Handles released by a closed account, so reuse can be embargoed. A
-- later holder must not inherit a former holder's recovery paths.
CREATE TABLE released_contact_handle (
    normalized_digest TEXT NOT NULL,
    channel_class     TEXT NOT NULL,
    released_at       TEXT NOT NULL,
    PRIMARY KEY (channel_class, normalized_digest)
);
CREATE INDEX ix_released_contact_handle_released_at ON released_contact_handle(released_at);

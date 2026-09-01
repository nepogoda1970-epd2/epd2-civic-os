-- PACK-14 migration 0003 — expand — credential registry
--
-- Metadata only. No password, no TOTP seed, no recovery-code value and
-- no WebAuthn private key has a column here, which is the structural
-- version of the retention matrix's "no key material ever existed here".

CREATE TABLE credential (
    credential_id    TEXT    NOT NULL PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    credential_type  TEXT    NOT NULL,
    status           TEXT    NOT NULL,
    created_at       TEXT    NOT NULL,
    last_used_at     TEXT,
    expires_at       TEXT,
    version          INTEGER NOT NULL,
    retention_class  TEXT    NOT NULL DEFAULT 'credential_metadata',
    legal_hold       INTEGER NOT NULL DEFAULT 0,
    document         TEXT    NOT NULL
);
CREATE INDEX ix_credential_account ON credential(account_id);

CREATE TABLE passkey_credential (
    credential_id         TEXT NOT NULL PRIMARY KEY,
    account_id            TEXT NOT NULL REFERENCES account_registry_record(account_id),
    credential_reference  TEXT NOT NULL,
    public_key            TEXT NOT NULL,
    sign_counter          INTEGER,
    binding               TEXT NOT NULL,
    relying_party_origin  TEXT NOT NULL,
    retention_class       TEXT NOT NULL DEFAULT 'credential_metadata',
    legal_hold            INTEGER NOT NULL DEFAULT 0,
    document              TEXT NOT NULL,
    CHECK (binding IN ('device_bound','synced','not_applicable'))
);
-- One authenticator credential reference maps to exactly one record, so
-- revocation is never ambiguous.
CREATE UNIQUE INDEX uq_passkey_credential_reference
    ON passkey_credential(credential_reference);

CREATE TABLE mfa_factor (
    factor_id        TEXT    NOT NULL PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    factor_class     TEXT    NOT NULL,
    status           TEXT    NOT NULL,
    enrolled_at      TEXT    NOT NULL,
    confirmed_at     TEXT,
    revoked_at       TEXT,
    retention_class  TEXT    NOT NULL DEFAULT 'credential_metadata',
    legal_hold       INTEGER NOT NULL DEFAULT 0,
    document         TEXT    NOT NULL,
    -- `sms_otp` is deliberately absent from this CHECK, as it is from
    -- `MfaFactorClass` (OD-P14-09). The database refuses it too.
    CHECK (factor_class IN ('totp','security_key','recovery_code','email_otp','provider_mfa'))
);
CREATE INDEX ix_mfa_factor_account ON mfa_factor(account_id);
-- One ACTIVE factor per class per account.
CREATE UNIQUE INDEX uq_active_mfa_factor_class
    ON mfa_factor(account_id, factor_class)
    WHERE status <> 'revoked';

CREATE TABLE recovery_code_set (
    set_id           TEXT    NOT NULL PRIMARY KEY,
    account_id       TEXT    NOT NULL REFERENCES account_registry_record(account_id),
    issued_at        TEXT    NOT NULL,
    revoked_at       TEXT,
    retention_class  TEXT    NOT NULL DEFAULT 'credential_metadata',
    legal_hold       INTEGER NOT NULL DEFAULT 0,
    document         TEXT    NOT NULL
);
CREATE INDEX ix_recovery_code_set_account ON recovery_code_set(account_id);

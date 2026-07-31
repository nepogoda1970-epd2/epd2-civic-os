-- PACK-15 migration 0003 — expand — redemption, replay and revocation
--
-- Redemption is atomic: the credential's status change and the redemption
-- row are written in one transaction, and the unique index on
-- `voting_credential_id` makes a second redemption a constraint
-- violation rather than a race.
--
-- The replay table carries no holder attribution of any kind, because no
-- holder is knowable on this side.

CREATE TABLE credential_redemption (
    redemption_reference     TEXT NOT NULL PRIMARY KEY,
    voting_credential_id     TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    redeemed_at_bucket       TEXT NOT NULL,
    FOREIGN KEY (voting_credential_id) REFERENCES voting_credential(voting_credential_id)
);

-- One redemption per credential, enforced by the database rather than by
-- a check-then-act in application code.
CREATE UNIQUE INDEX uq_credential_redemption_credential
    ON credential_redemption(voting_credential_id);

CREATE TABLE credential_replay_record (
    replay_id                TEXT NOT NULL PRIMARY KEY,
    voting_context_reference TEXT NOT NULL,
    reason_code              TEXT NOT NULL,
    detected_at_bucket       TEXT NOT NULL,
    timing_class             TEXT NOT NULL DEFAULT 'bucketed'
);

CREATE INDEX ix_credential_replay_context
    ON credential_replay_record(voting_context_reference);

CREATE TABLE credential_revocation (
    voting_credential_id  TEXT NOT NULL PRIMARY KEY,
    reason_code           TEXT NOT NULL,
    revoked_at            TEXT NOT NULL,
    authority_role        TEXT NOT NULL,
    dual_control_reference TEXT,
    before_cutoff         INTEGER NOT NULL,
    FOREIGN KEY (voting_credential_id) REFERENCES voting_credential(voting_credential_id),
    CHECK (before_cutoff = 1)
);

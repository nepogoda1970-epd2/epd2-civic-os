-- PACK-14 migration 0005 — expand — step-up
--
-- A confirmation is bound to an actor, a session, an action, a resource
-- AND a resource version. The binding columns are NOT NULL because an
-- optional binding column is an omitted one, and an omitted one is the
-- harvesting attack ADR-082 exists to prevent.

CREATE TABLE step_up_challenge (
    challenge_id       TEXT    NOT NULL PRIMARY KEY,
    actor_reference    TEXT    NOT NULL,
    session_id         TEXT    NOT NULL,
    action_code        TEXT    NOT NULL,
    resource_type      TEXT    NOT NULL,
    resource_id        TEXT    NOT NULL,
    resource_version   INTEGER NOT NULL,
    required_assurance TEXT    NOT NULL,
    status             TEXT    NOT NULL,
    issued_at          TEXT    NOT NULL,
    expires_at         TEXT    NOT NULL,
    document           TEXT    NOT NULL,
    CHECK (resource_version >= 0)
);
CREATE INDEX ix_step_up_challenge_expires_at ON step_up_challenge(expires_at);

CREATE TABLE step_up_result (
    challenge_id      TEXT    NOT NULL PRIMARY KEY,
    actor_reference   TEXT    NOT NULL,
    session_id        TEXT    NOT NULL,
    action_code       TEXT    NOT NULL,
    resource_id       TEXT    NOT NULL,
    resource_version  INTEGER NOT NULL,
    status            TEXT    NOT NULL,
    completed_at      TEXT    NOT NULL,
    expires_at        TEXT    NOT NULL,
    document          TEXT    NOT NULL
);
CREATE INDEX ix_step_up_result_expires_at ON step_up_result(expires_at);

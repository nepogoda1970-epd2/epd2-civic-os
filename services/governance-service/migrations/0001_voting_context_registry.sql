-- PACK-15 migration 0001 — expand — the voting context registry
--
-- The registry database holds administrative configuration only. It has
-- no column for a participant, an assertion, a credential, a ballot or a
-- turnout figure, and no foreign key to any store that does: the
-- eligibility side reads this registry, and a read edge from there to
-- anything holding a cast ballot is what ADR-089 forbids.
--
-- `activation_snapshot_digest` is what makes "the critical parameters
-- were frozen at activation" checkable rather than asserted.

CREATE TABLE voting_context (
    voting_context_reference     TEXT NOT NULL,
    version                      INTEGER NOT NULL,
    voting_context_id            TEXT NOT NULL,
    voting_type                  TEXT NOT NULL,
    organizational_scope         TEXT NOT NULL,
    status                       TEXT NOT NULL,
    voting_window_start          TEXT NOT NULL,
    voting_window_end            TEXT NOT NULL,
    issuance_window_start        TEXT NOT NULL,
    issuance_window_end          TEXT NOT NULL,
    revocation_cutoff            TEXT NOT NULL,
    rule_set_reference           TEXT NOT NULL,
    rule_set_version             TEXT NOT NULL,
    required_assurance           TEXT NOT NULL,
    participation_class          TEXT NOT NULL,
    privacy_profile              TEXT NOT NULL,
    audit_profile                TEXT NOT NULL,
    disclosure_minimum_cell      INTEGER NOT NULL,
    small_electorate             INTEGER NOT NULL,
    per_scope_metrics_permitted  INTEGER NOT NULL,
    eligible_population          INTEGER NOT NULL,
    activation_snapshot_digest   TEXT,
    activation_captured_at       TEXT,
    document                     TEXT NOT NULL,
    PRIMARY KEY (voting_context_reference, version),
    CHECK (version >= 1),
    CHECK (disclosure_minimum_cell >= 5),
    CHECK (issuance_window_end <= voting_window_end)
);

CREATE INDEX ix_voting_context_status ON voting_context(status);

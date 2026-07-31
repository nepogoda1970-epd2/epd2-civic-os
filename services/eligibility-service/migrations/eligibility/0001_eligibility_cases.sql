-- PACK-15 migration 0001 — expand — eligibility cases and decisions
--
-- The identity-side store. It is identified by design: the eligibility
-- side must know whose eligibility it is deciding, and identification
-- stops here (unlinkability matrix, transition 1).
--
-- There is deliberately **no column** for an assertion identifier, a
-- nonce, a credential or a ballot, and no foreign key to any table in the
-- assertion-issuer or voting-side databases — which are separate database
-- files, so such a key is not expressible.

CREATE TABLE eligibility_case (
    case_id                  TEXT NOT NULL PRIMARY KEY,
    voting_context_reference TEXT NOT NULL,
    participant_reference    TEXT NOT NULL,
    participation_class      TEXT NOT NULL,
    status                   TEXT NOT NULL,
    requested_at             TEXT NOT NULL,
    assisted_by              TEXT,
    document                 TEXT NOT NULL,
    retention_class          TEXT NOT NULL DEFAULT 'eligibility_case',
    legal_hold               INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX ix_eligibility_case_context ON eligibility_case(voting_context_reference);

CREATE TABLE eligibility_decision (
    decision_id                  TEXT NOT NULL PRIMARY KEY,
    case_id                      TEXT NOT NULL,
    voting_context_reference     TEXT NOT NULL,
    status                       TEXT NOT NULL,
    rule_set_reference           TEXT NOT NULL,
    rule_set_version             TEXT NOT NULL,
    eligibility_class            TEXT NOT NULL,
    organizational_scope         TEXT NOT NULL,
    required_assurance_satisfied INTEGER NOT NULL,
    decided_at                   TEXT NOT NULL,
    valid_until                  TEXT NOT NULL,
    reason_codes                 TEXT NOT NULL,
    source_versions              TEXT NOT NULL,
    document                     TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES eligibility_case(case_id),
    CHECK (valid_until > decided_at)
);

CREATE INDEX ix_eligibility_decision_case ON eligibility_decision(case_id);

-- One assertion per participation unit per voting context. It records
-- *that* an assertion was minted and never *which one*: there is no
-- assertion_id column here, and adding one would be the ADR-093 pairing.
CREATE TABLE participation_unit_ledger (
    voting_context_reference TEXT NOT NULL,
    participation_unit_key   TEXT NOT NULL,
    assertion_minted         INTEGER NOT NULL,
    minted_at                TEXT,
    PRIMARY KEY (voting_context_reference, participation_unit_key),
    CHECK (assertion_minted IN (0, 1)),
    CHECK (assertion_minted = 0 OR minted_at IS NOT NULL)
);

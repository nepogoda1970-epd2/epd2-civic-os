-- PACK-15 migration 0001 (assertion-issuer set) — expand
--
-- `OD-P15-01`: a separately bounded module with its own storage boundary.
-- This migration set is applied to its **own database file**, declared by
-- `PACK15_ASSERTION_ISSUER_MIGRATIONS`; it shares no schema, no
-- transaction and no connection with the `eligibility/` set, and its
-- tables carry **no participant reference and no case reference** — the
-- issuer consumes a five-field minimized decision and nothing else.
--
-- Because the two sets live in separate files, a foreign key from an
-- assertion back to a case is not expressible here, which is a stronger
-- guarantee than not writing one.

CREATE TABLE eligibility_assertion (
    assertion_id                 TEXT NOT NULL PRIMARY KEY,
    voting_context_reference     TEXT NOT NULL,
    eligibility_result           TEXT NOT NULL,
    eligibility_class            TEXT NOT NULL,
    organizational_scope         TEXT NOT NULL,
    required_assurance_satisfied INTEGER NOT NULL,
    issued_at_bucket             TEXT NOT NULL,
    expires_at                   TEXT NOT NULL,
    audience                     TEXT NOT NULL,
    purpose                      TEXT NOT NULL,
    nonce                        TEXT NOT NULL,
    status                       TEXT NOT NULL,
    integrity_algorithm          TEXT NOT NULL,
    integrity_key_identifier     TEXT NOT NULL,
    integrity_signature          TEXT NOT NULL,
    CHECK (eligibility_result = 'approved'),
    CHECK (purpose = 'voting_credential_issuance'),
    CHECK (expires_at > issued_at_bucket)
);

CREATE UNIQUE INDEX uq_eligibility_assertion_nonce ON eligibility_assertion(nonce);

CREATE TABLE assertion_queue_entry (
    assertion_id             TEXT NOT NULL PRIMARY KEY,
    voting_context_reference TEXT NOT NULL,
    batch_reference          TEXT NOT NULL,
    enqueued_at              TEXT NOT NULL,
    release_not_before       TEXT NOT NULL,
    cohort_wait_deadline     TEXT NOT NULL,
    released_at              TEXT,
    cohort_size_class        TEXT,
    below_minimum_cohort     INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (assertion_id) REFERENCES eligibility_assertion(assertion_id),
    CHECK (cohort_wait_deadline >= release_not_before)
);

CREATE INDEX ix_assertion_queue_batch ON assertion_queue_entry(batch_reference);

-- The one-time pickup. Keyed on the handoff artifact's digest, never on
-- the artifact value: a record holding the value would be a replayable
-- secret at rest.
CREATE TABLE assertion_pickup (
    pickup_id                TEXT NOT NULL PRIMARY KEY,
    assertion_id             TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    handoff_artifact_digest  TEXT NOT NULL,
    audience_origin          TEXT NOT NULL,
    created_at               TEXT NOT NULL,
    expires_at               TEXT NOT NULL,
    consumed_at              TEXT,
    FOREIGN KEY (assertion_id) REFERENCES eligibility_assertion(assertion_id),
    CHECK (length(handoff_artifact_digest) = 64),
    CHECK (expires_at > created_at)
);

CREATE UNIQUE INDEX uq_assertion_pickup_digest ON assertion_pickup(handoff_artifact_digest);

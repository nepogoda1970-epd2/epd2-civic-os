-- PACK-15 migration 0002 (assertion-issuer set) — expand
--
-- PACK-14 handoff acceptance. It belongs to the **issuer** database and
-- deliberately not to the eligibility database: an acceptance digest sits
-- beside `assertion_pickup`, and putting it beside `eligibility_case`
-- would create the case → digest → pickup → assertion path that ADR-093
-- forbids.
--
-- Carries no account, no session and nothing from which one could be
-- derived (ADR-088, preserved by ADR-090). The digest is the one-time
-- key; a second presentation collides on the primary key rather than
-- being re-served.

CREATE TABLE voting_handoff_acceptance (
    artifact_digest          TEXT NOT NULL PRIMARY KEY,
    acceptance_id            TEXT NOT NULL,
    voting_context_reference TEXT NOT NULL,
    audience                 TEXT NOT NULL,
    origin                   TEXT NOT NULL,
    accepted_at              TEXT NOT NULL,
    consumed_at              TEXT,
    CHECK (length(artifact_digest) = 64)
);

CREATE INDEX ix_handoff_acceptance_context
    ON voting_handoff_acceptance(voting_context_reference);

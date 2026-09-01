"""Voting Service. Owns `Ballot`, `BallotOption`, `VoteEnvelope`,
`VoteReceipt` (canon sections 15.1-15.4; ADR-005 consolidation of "Ballot
Definition Service", "Vote Casting Service", and "Receipt Service" into
one physical package). No identity linkage on `VoteEnvelope`/
`VoteReceipt` — see README.md.
"""

"""Moderation Service. Owns `ModerationCase`, `ModerationDecision`, `Appeal`
(canon section 14). Consolidates canon's "Moderation Service" and "Appeal
Service" into one package (ADR-005) — safe only because of the
application-layer appeal role-separation check (CT-00-06, see
`application.decide_appeal`)."""

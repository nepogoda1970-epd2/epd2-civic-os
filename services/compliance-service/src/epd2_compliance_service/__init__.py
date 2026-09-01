"""Compliance Service - PACK-09's one wholly new service (ADR-038).

Owns the Compliance, Records Governance & Legal Workflows context:
records classification and retention (`RetentionPolicy`,
`RetentionStartEvent`, `GovernedRecord`), controlled disposal
(`DisposalEligibility`, `DestructionAuthorization`,
`DestructionEvidence`), Legal Hold, the Data Catalog & Processing
Registry (`DataAsset`, `ProcessingActivity`), governed procedural cases
and deadlines (`ProceduralCase`, `DeadlineDefinition`,
`ProceduralDeadline`), data-subject/legal requests, and party
arbitration/internal disputes.

It references organization-service scopes by opaque UUID and owns no
identity, document bytes, finance ledger, ballot, vote or tally - see
ADR-038 for the boundary and `docs/packs/PACK-09-IMPLEMENTATION.md` for
what is deliberately deferred to PACK-10 through PACK-18.

This service makes **no claim of automatic legal compliance** with GDPR,
BDSG or German party law. It provides a governed workflow, evidence
references and auditability; whether a given retention schedule, legal
basis, deadline or decision satisfies the law remains a human legal
judgement made outside this system.
"""

from __future__ import annotations

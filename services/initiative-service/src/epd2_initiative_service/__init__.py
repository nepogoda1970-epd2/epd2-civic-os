"""Initiative Service. Owns `Initiative`, `InitiativeVersion`,
`SupportRecord`, `Amendment`, `SourceRecord` (canon sections 11-12; ADR-005
consolidation of "Initiative Service", "Amendment Service", and "Evidence
Service" into one physical package). See README.md for the consolidation
rationale, the PACK-02 dependencies, and this service's own hard rules
(AI cannot silently promote a source to `human_checked`; at most one
active `SupportRecord` per participant per initiative; a published
`InitiativeVersion` is immutable).
"""

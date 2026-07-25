"""Governance Service — canon section 19b (added by canon 0.4.0, ADR-018),
implemented per ADR-016 through ADR-020.

Owns `RoleAssignment` (canon 8.4, its first physical implementation),
`GovernancePolicy`, `GovernanceDecision`, and `TechnicalChallenge` (canon
19b.2-19b.4), plus the derived `FinalityStatus` read model (19b.3/19b.6).
"""

from __future__ import annotations

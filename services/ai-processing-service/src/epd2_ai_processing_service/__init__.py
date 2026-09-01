"""AI Processing Service — canon section 17.1 (original) extended by
canon section 19c (added by canon 0.5.0, ADR-023/ADR-025), implemented
per ADR-021 through ADR-025.

Owns `AIProcessingRecord` exclusively (canon 19c: "остаётся единственной
сущностью настоящего раздела"), plus the embedded, immutable
`RedactionManifest` value object, the `AIDisclosurePackage` contract/
value object (never persisted), and the derived `DisclosureStatus` read
model.
"""

from __future__ import annotations

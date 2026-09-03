# INFRA-03 C1 reconciliation

C1 derives from exact PRESEAL SHA-256 `30033863c854b34532b42a216bb275c691e57413053724f393b183ad814685fe` (16,176,926 bytes). The runtime design is unchanged. The obsolete API-06 blocker is released only by exact live verification of canonical API-06 acceptance; missing or changed governance remains fail-closed.

C1 uses the INFRA-03-owned G39/G40 seal semantics: deterministic safe archive hygiene and independent exact-same-byte replay. The legacy generic INFRA-01 package builder is not reused because it duplicates cumulative `FREEZE-INVENTORY.json` and `SHA256SUMS.txt` members on this PRESEAL. No INFRA-03 gate is waived.

The candidate does not self-accept. Whole-INFRA closure, production readiness, legal activation, final security acceptance, and BSI/Common Criteria/EAL4 certification are not asserted.

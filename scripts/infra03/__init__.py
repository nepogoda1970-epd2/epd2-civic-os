"""EPD2 INFRA-03 — Deployment Runtime, Environment Topology & Preview-Readiness
Foundation (working pre-seal implementation).

Stage self-state: ``PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED``. This package
consumes — never bypasses — the accepted INFRA-02 supply-chain guarantees:
immutable artifact digests, SBOM/provenance identity, promotion-by-digest and
release-integrity evidence.
"""

INFRA03_NAME = "EPD2-INFRA03-PREVIEW-RUNTIME"
INFRA03_VERSION = "0.1.0"

#: The exact accepted hard predecessor (INFRA-02 acceptance record on main).
PREDECESSOR = {
    "stage": "INFRA-02",
    "candidate": "EPD2_INFRA02_CI_CD_AND_SOFTWARE_SUPPLY_CHAIN_CANDIDATE_0.1.zip",
    "zip_sha256": "d91fa6db81126765c0e26bf285fff2f974464544b7fa6299b6d069a25d1ff72c",
    "size_bytes": 15980332,
    "authoritative_run": 33574647511,
    "freeze_tree_digest": "c169a2930ab50612076ab3f90468ff03f5ec19e2005c520765a4905e15c51f7d",
    "source_file_count": 1494,
    "archive_member_count": 1496,
    "acceptance_record": "docs/infra/INFRA-02/INFRA02_ACCEPTANCE_RECORD.json",
}

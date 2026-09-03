"""The governed INFRA-03 mutation catalog (assignment §60).

Thirty-six corruption classes, each mapped onto exactly one distinct
``I03_*`` detector code. The mutation suite
(``tests/repository/test_infra03_mutation_suite.py``) corrupts a
representative input per class and asserts the mapped detector fires; the
G38 gate requires every class detected and the mapping distinct.
"""

from __future__ import annotations

from scripts.infra03 import codes

#: mutation class -> the one detector code that must catch it.
MUTATION_DETECTORS: dict[str, str] = {
    "M01-mutable-latest-reference": codes.MUTABLE_ARTIFACT_REFERENCE,
    "M02-wrong-artifact-digest": codes.ARTIFACT_DIGEST_MISMATCH,
    "M03-local-rebuild-substitution": codes.LOCAL_REBUILD_SUBSTITUTION,
    "M04-provenance-handoff-bypass": codes.SUPPLY_CHAIN_HANDOFF_BYPASSED,
    "M05-undeclared-service": codes.UNDECLARED_SERVICE,
    "M06-public-admin-port": codes.ADMIN_ENDPOINT_PUBLIC,
    "M07-wrong-network-segment": codes.WRONG_NETWORK_SEGMENT,
    "M08-open-east-west-traffic": codes.UNDECLARED_FLOW,
    "M09-forwarded-header-spoof": codes.FORWARDED_HEADER_UNTRUSTED,
    "M10-plaintext-fallback": codes.PLAINTEXT_FALLBACK_FORBIDDEN,
    "M11-wrong-ca": codes.UNTRUSTED_CA,
    "M12-wrong-hostname": codes.HOSTNAME_MISMATCH,
    "M13-missing-client-cert": codes.CLIENT_CERT_MISSING,
    "M14-wrong-workload-cert": codes.WORKLOAD_IDENTITY_MISMATCH,
    "M15-universal-service-cert": codes.UNIVERSAL_SERVICE_CERT,
    "M16-secret-in-manifest": codes.SECRET_IN_MANIFEST,
    "M17-secret-in-logs": codes.SECRET_IN_LOGS,
    "M18-production-db-in-preview": codes.PRODUCTION_DB_IN_PREVIEW,
    "M19-sqlite-substitution": codes.NON_POSTGRES_SUBSTITUTION,
    "M20-readiness-always-true": codes.READINESS_ALWAYS_TRUE,
    "M21-sensitive-health-output": codes.SENSITIVE_HEALTH_OUTPUT,
    "M22-sleep-as-readiness": codes.SLEEP_BASED_READINESS,
    "M23-crashloop-marked-healthy": codes.CRASHLOOP_MARKED_HEALTHY,
    "M24-failed-deploy-marked-success": codes.FAILED_DEPLOY_MARKED_SUCCESS,
    "M25-partial-unsafe-exposure": codes.PARTIAL_UNSAFE_EXPOSURE,
    "M26-unsafe-rollback": codes.UNSAFE_ROLLBACK,
    "M27-duplicate-redeploy": codes.NON_IDEMPOTENT_REDEPLOY,
    "M28-drift-ignored": codes.DRIFT_IGNORED,
    "M29-undeclared-egress": codes.UNDECLARED_EGRESS,
    "M30-voting-person-id-leakage": codes.VOTING_PERSON_ID_LEAK,
    "M31-voting-global-correlation": codes.VOTING_GLOBAL_CORRELATION,
    "M32-shared-voting-observability": codes.SHARED_VOTING_OBSERVABILITY,
    "M33-stale-state-after-reset": codes.STALE_STATE_AFTER_RESET,
    "M34-ambiguous-destructive-target": codes.AMBIGUOUS_DESTRUCTIVE_TARGET,
    "M35-stale-infra02-predecessor": codes.STALE_PREDECESSOR,
    "M36-post-test-byte-mutation": codes.POST_TEST_BYTE_MUTATION,
}

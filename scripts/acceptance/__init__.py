"""EPD² INFRA-01 canonical CI acceptance harness.

One deterministic, fail-closed, evidence-producing acceptance system for the
repository. The harness is infrastructure: it executes and reconciles the
governed checks, binds every run to an exact candidate identity, proves that
tested bytes equal packaged bytes, and emits machine-readable evidence
sufficient for an independent governed acceptance decision.

The harness never decides business-domain acceptance by assertion, never
infers PASS from source inspection, and never represents a check that did not
execute as anything other than FAIL/BLOCKED.

Canonical entry point:

    uv run python -m scripts.acceptance run

Stage semantics, the machine-readable check registry, the execution-manifest
schema and the mutation coverage for the harness itself are governed by
INFRA-01 (see ``docs/infra/INFRA-01/``).

NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
"""

from __future__ import annotations

HARNESS_NAME = "EPD2-INFRA01-ACCEPTANCE-HARNESS"
HARNESS_VERSION = "0.1.0"

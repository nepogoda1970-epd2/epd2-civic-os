"""EPD2 CTRL-01 — Governed Control Plane & Authority Operations Foundation.

Stage mode: `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`. This package opens and
closes no canonical layer and makes no acceptance, production-readiness, legal
activation or certification claim.
"""

from __future__ import annotations

STAGE = "CTRL-01"
STAGE_MODE = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
SELF_STATE_ALLOWED = (
    "CTRL01_IMPLEMENTATION_COMPLETE",
    "LOCAL_VERIFICATION_PASS",
    "PRESEAL_READY",
    "NOT_ACCEPTED",
)

__all__ = ["SELF_STATE_ALLOWED", "STAGE", "STAGE_MODE"]

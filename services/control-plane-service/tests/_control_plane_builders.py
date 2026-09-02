"""Re-export of the packaged reference world, so tests and the CTRL-01
validator exercise exactly the same governed fixture."""

from __future__ import annotations

from epd2_control_plane_service.reference_world import (  # noqa: F401
    BUND,
    KREIS_BE,
    LAND_BE,
    LAND_BY,
    PLATFORM,
    PRINCIPALS,
    RULE,
    T0,
    World,
    _authority,
    build_world,
    run_governed_flow,
)

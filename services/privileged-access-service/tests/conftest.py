"""Pytest fixtures for the Privileged Access Service test suite.

Puts this directory on `sys.path` so the sibling `_privileged_builders`
module can be imported as a plain top-level module, without requiring
`__init__.py` files in the tests directory - the same precedent
`document-service`'s own conftest sets, and for the same reason: the
repository runs pytest with `--import-mode=importlib`, which resolves
same-named test files across services by full path but does not make
sibling helper modules importable on its own.

Two details here are deliberate and both were found the hard way.

**The helper's name is service-specific.** `document-service` already
contributes a top-level `_builders`, and a second module of that name on
`sys.path` does not shadow it loudly - it wins or loses by whichever
conftest imported first, and the loser's tests fail to collect with an
import error naming the wrong file. So this one is
`_privileged_builders`.

**The path is *appended*, not inserted at the front.** Prepending it puts
this directory ahead of every other service's tests directory, and
`document-service/tests/test_privacy_boundary.py` imports a sibling by
bare name (`from test_application import Flow`) - which
`--import-mode=importlib` resolves for *collection* but not for a plain
import statement. Prepending made that import resolve to **this**
service's `test_application.py` and broke thirteen PACK-11 tests that
pass in isolation. Appending leaves every earlier service's own directory
ahead of this one, so a bare sibling import still finds its own package.

The builders and test doubles live there; this module only wires them
into fixtures. Nothing here reads the system clock - `FixedClock` is
the only source of time in the suite, so a test that depends on an
interval says so by advancing it rather than by sleeping.
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parent))

import pytest
from _privileged_builders import (
    FixedClock,
    StubAuthorizationPort,
    StubSourceAuthorizationPort,
    build_stores,
)

from epd2_privileged_access_service.domain import (
    OrganizationalScopeRef,
)
from epd2_privileged_access_service.policy import (
    REFERENCE_POLICY,
    PrivilegedAccessPolicy,
)
from epd2_privileged_access_service.storage import PrivilegedStores


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


@pytest.fixture
def other_scope() -> OrganizationalScopeRef:
    return OrganizationalScopeRef(organization_id=uuid4())


@pytest.fixture
def policy() -> PrivilegedAccessPolicy:
    return REFERENCE_POLICY


@pytest.fixture
def port() -> StubAuthorizationPort:
    return StubAuthorizationPort()


@pytest.fixture
def source_port() -> StubSourceAuthorizationPort:
    return StubSourceAuthorizationPort()


@pytest.fixture
def stores() -> PrivilegedStores:
    return build_stores()

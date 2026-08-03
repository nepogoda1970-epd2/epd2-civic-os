"""PACK-16D reference implementation of the EPD2-HOM-1 voting protocol.

**REFERENCE IMPLEMENTATION CANDIDATE. NOT A PRODUCTION CRYPTOGRAPHIC
RELEASE. NOT CERTIFIED. NOT LEGALLY ACTIVATED. NOT READY FOR REAL
ELECTIONS.**

Every module under this package exists to make the PACK-16A/16B/16C
specifications executable and independently checkable. It is deliberately
written in the repository's existing Python stack with **no new
dependency of any kind** (see
`docs/packs/PACK-16/PACK-16D-LANGUAGE-AND-DEPENDENCY-ASSESSMENT.md`), and
it makes **no constant-time or side-channel claim** (see
`docs/packs/PACK-16/PACK-16D-SECURITY-AND-SIDE-CHANNEL-LIMITATIONS.md`).
"""

from __future__ import annotations

REFERENCE_IMPLEMENTATION_STATUS = "REFERENCE IMPLEMENTATION CANDIDATE - NOT PRODUCTION"

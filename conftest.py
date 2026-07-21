"""Root pytest conftest.

Ensures the repository root is importable so that top-level `scripts`
package (repository structure checks) can be imported by
`tests/repository/*.py` regardless of pytest's import mode. Tests are
expected to be run from the repository root.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# GitHub Actions: one-click repository verification

This workflow is pack-agnostic: run it whenever `uv.lock` / `package-lock.json`
need regenerating against the current `pyproject.toml` / `package.json` (for
example, after a new pack adds workspace members or dependencies), or
whenever you want a real-network confirmation of `make verify` on a fresh
checkout. It always verifies whatever pack(s) are implemented in the tree at
run time — see `docs/handover/` for the pack-specific report that applies to
a given run.

1. Upload the **contents of this folder** to the repository root (not the outer folder itself).
2. Open **Actions**.
3. Select **Verify and Package**.
4. Click **Run workflow** → **Run workflow**.
5. When finished, open the run and download the artifact named `epd2-civic-os-verification-result`.

The workflow creates `uv.lock`, `package-lock.json`, runs the full verification pipeline (`make verify`), and packages the result (`VERIFICATION-RESULT.md`, `VERIFICATION.log`, the full tree) whether verification passes or fails.

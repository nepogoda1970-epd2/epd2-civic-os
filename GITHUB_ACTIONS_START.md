# GitHub Actions: one-click PACK-01 verification

1. Upload the **contents of this folder** to the repository root (not the outer folder itself).
2. Open **Actions**.
3. Select **Verify and Package**.
4. Click **Run workflow** → **Run workflow**.
5. When finished, open the run and download the artifact named `epd2-civic-os-PACK-01-result`.

The workflow creates `uv.lock`, `package-lock.json`, runs the full verification pipeline, and packages the result whether verification passes or fails.

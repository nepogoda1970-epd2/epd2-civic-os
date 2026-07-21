# Repository Rules

## Structural rules enforced by `scripts/` and `tests/repository/`

- Required top-level files and directories must exist
  (`scripts/check_repository.py`, `tests/repository/test_required_files.py`).
- Forbidden files and directories must not exist — secrets, private keys,
  `node_modules/`, `.venv/`, `__pycache__/`, `.DS_Store`, real database
  files, archives with unknown contents
  (`scripts/check_forbidden_files.py`, `tests/repository/test_forbidden_paths.py`).
- Version numbers must be consistent across the Python package, the
  TypeScript package, `docs/canonical/canon-version.json`, and
  `CHANGELOG.md` (`scripts/verify_versions.py`,
  `tests/repository/test_version_consistency.py`).

## CODEOWNERS placeholders

`CODEOWNERS` currently uses placeholder GitHub team aliases
(`@EPD2-CANON-OWNER`, `@EPD2-ARCHITECTURE-OWNER`,
`@EPD2-INFRASTRUCTURE-OWNER`, `@EPD2-FRONTEND-OWNER`) because no GitHub
organization or team structure exists yet for this project. These
placeholders are **not** real GitHub usernames and will not resolve to any
account.

Once the GitHub organization and its teams are created, replace each
placeholder in `CODEOWNERS` with the corresponding real team alias (for
example `@epd2-plattform/canon-owners`). Until then, `CODEOWNERS` remains a
template and does not enforce actual review routing.

This is also tracked as an open question in
`docs/review/OPEN_QUESTIONS.md`.

.PHONY: setup format format-check lint typecheck test test-python test-typescript \
        test-frontend check-repository build-frontend verify clean

# --- make setup ---
# Installs Python dependencies via uv and Node dependencies via npm, using
# the committed lock files (uv.lock, package-lock.json). Requires no root
# privileges and does not modify global system configuration.
setup:
	uv sync --all-groups
	npm install

# --- make format ---
# Uses the Prettier version pinned in package-lock.json (via the root
# "format" script / `npm run`), never an ad hoc `npx --yes` download.
format:
	uv run ruff format .
	npm run format

# --- make format-check ---
format-check:
	uv run ruff format --check .
	npm run format:check

# --- make lint ---
lint:
	uv run ruff check .
	npm run lint --workspace=frontend/web-shell

# --- make typecheck ---
typecheck:
	uv run mypy .
	npm run typecheck --workspace=packages/typescript/epd2-types
	npm run typecheck --workspace=frontend/web-shell

# --- make test ---
test: test-python test-typescript test-frontend

test-python:
	uv run pytest

test-typescript:
	npm run test --workspace=packages/typescript/epd2-types

test-frontend:
	npm run test --workspace=frontend/web-shell

# --- make check-repository ---
check-repository:
	uv run python scripts/check_repository.py
	uv run python scripts/check_forbidden_files.py
	uv run python scripts/verify_versions.py

# --- make build-frontend ---
build-frontend:
	npm run build --workspace=frontend/web-shell

# --- make verify ---
# Runs the full sequential verification pipeline, as run in CI:
# 1. repository checks, 2. format check, 3. lint, 4. typecheck,
# 5. Python tests, 6. TypeScript tests, 7. frontend tests, 8. frontend build.
# Does not install or download anything itself — run `make setup` first.
# Fails on the first non-zero exit code.
verify: check-repository format-check lint typecheck test build-frontend

# --- make clean ---
clean:
	rm -rf .venv
	rm -rf packages/python/epd2-core/.pytest_cache packages/python/epd2-core/.mypy_cache
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -name "__pycache__" -not -path "*/node_modules/*" -type d -prune -exec rm -rf {} +
	rm -rf node_modules packages/typescript/epd2-types/node_modules frontend/web-shell/node_modules
	rm -rf frontend/web-shell/.next frontend/web-shell/out
	rm -rf packages/typescript/epd2-types/dist

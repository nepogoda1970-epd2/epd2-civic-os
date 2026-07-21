# Local Development

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- Node.js 22 LTS
- GNU Make

## Setup

```bash
make setup
```

This installs Python dependencies for the root workspace via `uv sync`, and
Node dependencies for the TypeScript package and the frontend. It does not
require root privileges and does not modify global system configuration.

## Everyday commands

```bash
make format         # Ruff format + Prettier
make lint           # Ruff lint + ESLint
make typecheck      # mypy + tsc
make test           # all tests (Python, TypeScript, frontend)
make check-repository  # structural repository checks
make verify         # full sequential verification, as run in CI
```

## Workspace layout

- `packages/python/epd2-core` — shared Python package (no business logic).
- `packages/typescript/epd2-types` — shared TypeScript package (no business
  logic).
- `frontend/web-shell` — minimal Next.js frontend skeleton.
- `services/` — placeholder for future business services (empty at this
  stage).
- `contracts/` — placeholder for future OpenAPI specs, event schemas, JSON
  schemas, and the documented reason codes list.

## Running a single package's tests

```bash
uv run --package epd2-core pytest packages/python/epd2-core/tests
```

```bash
npm --workspace packages/typescript/epd2-types test
```

```bash
npm --workspace frontend/web-shell test
```
